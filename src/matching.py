"""
TRUCKLY — candidate generation, explainable scoring, and the `candidates` table.

The score is NOT the objective. The optimiser minimises cost in rupees. The
score exists for two reasons only:
  (1) it drives baseline B2 (naive greedy), and
  (2) it is what the user is shown as the explanation for a recommendation.
"""
from __future__ import annotations

from itertools import combinations
from typing import List
import numpy as np

from .feasibility import best_route, quick_prefilter, empty_return


def _norm(x, lo, hi):
    if hi - lo <= 1e-12:
        return 0.0
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0))


class Candidate:
    __slots__ = ("truck", "bundle", "ev", "score", "features")

    def __init__(self, truck, bundle, ev, score, features):
        self.truck = truck
        self.bundle = bundle
        self.ev = ev
        self.score = score
        self.features = features


def score_candidate(truck, bundle, ev, base_ev, net, theta, w, max_wait,
                    slack_ref):
    """Explainable score S(k,b) in roughly [-1.5, 2.4]. See docs/methodology.md.

    Every term is divided by a STATED maximum so the weights are comparable.
    Note the detour term is normalised by theta*d_ret (the tolerance), NOT by
    d_ret -- dividing by d_ret would compress the term into [0, theta] and
    silently down-weight it by 1/theta.
    """
    d_ret = max(truck.direct_return_km, 1e-6)
    empty_avoided = max(0.0, base_ev.empty_km - ev.empty_km)
    t_empty = _norm(empty_avoided / d_ret, 0.0, 1.0)
    t_detour = _norm(max(0.0, ev.detour_km) / max(theta * d_ret, 1e-6), 0.0, 1.0)
    load_kg = sum(s.weight_kg for s in bundle)
    t_cap = _norm(load_kg / truck.capacity_kg, 0.0, 1.0)
    t_wait = _norm(ev.waiting_hr / max(max_wait, 1e-6), 0.0, 1.0)
    slack = min((s.deadline_hr - s.ready_time_hr) for s in bundle) if bundle else 0.0
    t_slack = _norm(slack / max(slack_ref, 1e-6), 0.0, 1.0)

    s = (w["w1_empty_avoided"] * t_empty
         - w["w2_detour"] * t_detour
         + w["w3_capacity"] * t_cap
         - w["w4_waiting"] * t_wait
         + w["w5_slack"] * t_slack)
    parts = dict(empty=t_empty, detour=t_detour, capacity=t_cap,
                 waiting=t_wait, slack=t_slack, empty_km_avoided=empty_avoided)
    return float(s), parts


def generate_candidates(trucks, shipments, net, cost, eps, params, cfg,
                        max_bundle=2, collect_rejects=True):
    """Stage A + B: feasible (truck, bundle) pairs with features and scores."""
    theta = params["detour_tolerance"]
    mdk = params.get("min_detour_allowance_km", 0.0)
    drv = cfg["driver"]
    w = cfg["score_weights"]
    max_wait = params["max_wait_hours"]
    slack_ref = float(np.percentile(
        [s.deadline_hr - s.ready_time_hr for s in shipments], 95)) if shipments else 1.0

    base = {t.truck_id: empty_return(t, net, cost, eps, drv) for t in trucks}
    cands, rejects = [], []
    sidx = {s.shipment_id: s for s in shipments}

    for tr in trucks:
        b0 = base[tr.truck_id]
        singles_ok = []
        for sh in shipments:
            r = quick_prefilter(tr, sh, net, theta, mdk)
            if r is not None:
                if collect_rejects:
                    rejects.append((tr.truck_id, (sh.shipment_id,), r, "prefilter"))
                continue
            ev = best_route(tr, [sh], net, cost, eps, theta, drv, min_detour_km=mdk)
            if not ev.feasible:
                if collect_rejects:
                    rejects.append((tr.truck_id, (sh.shipment_id,), ev.reason, "route"))
                continue
            if ev.waiting_hr > max_wait + 1e-9:
                if collect_rejects:
                    rejects.append((tr.truck_id, (sh.shipment_id,), "return_window", "wait"))
                continue
            sc, parts = score_candidate(tr, [sh], ev, b0, net, theta, w,
                                        max_wait, slack_ref)
            cands.append(Candidate(tr, [sh], ev, sc,
                                   _features(tr, [sh], ev, b0, net, parts, sc)))
            singles_ok.append(sh)

        # pairs, built only from shipments that are individually feasible
        if max_bundle >= 2 and len(singles_ok) >= 2:
            cap = tr.capacity_kg
            for s1, s2 in combinations(singles_ok, 2):
                if s1.weight_kg + s2.weight_kg > cap:
                    continue
                if s1.volume_m3 + s2.volume_m3 > tr.capacity_m3:
                    continue
                ev = best_route(tr, [s1, s2], net, cost, eps, theta, drv, min_detour_km=mdk)
                if not ev.feasible or ev.waiting_hr > max_wait + 1e-9:
                    if collect_rejects:
                        rejects.append((tr.truck_id,
                                        (s1.shipment_id, s2.shipment_id),
                                        ev.reason, "route"))
                    continue
                sc, parts = score_candidate(tr, [s1, s2], ev, b0, net, theta, w,
                                            max_wait, slack_ref)
                cands.append(Candidate(tr, [s1, s2], ev, sc,
                                       _features(tr, [s1, s2], ev, b0, net, parts, sc)))
    return cands, base, rejects


def _features(tr, bundle, ev, b0, net, parts, score):
    load = sum(s.weight_kg for s in bundle)
    vol = sum(s.volume_m3 for s in bundle)
    first = bundle[0]
    brg_ship = net.brg(first.origin, first.dest)
    brg_ret = net.brg(tr.current_node, tr.home_node)
    dev = abs((brg_ship - brg_ret + 180.0) % 360.0 - 180.0)
    return dict(
        bundle_size=len(bundle),
        pickup_detour_km=net.d(tr.current_node, first.origin),
        delivery_detour_km=net.d(bundle[-1].dest, tr.home_node),
        empty_km_avoided=parts["empty_km_avoided"],
        total_detour_km=ev.detour_km,
        weight_ratio=load / tr.capacity_kg,
        volume_ratio=vol / tr.capacity_m3,
        deadline_slack_hr=min(s.deadline_hr - s.ready_time_hr for s in bundle),
        wait_before_pickup_hr=ev.waiting_hr,
        bearing_deviation_deg=dev,
        c_kb_inr=ev.cost_inr,
        obj_kb_inr=ev.obj_inr,
        cost_delta_vs_empty_inr=ev.cost_inr - b0.cost_inr,
        match_score=score,
    )


def add_competition_features(cands, shipments):
    """Global-context features: how contested is each shipment."""
    cnt = {}
    for c in cands:
        for s in c.bundle:
            cnt[s.shipment_id] = cnt.get(s.shipment_id, 0) + 1
    per_truck = {}
    for c in cands:
        per_truck.setdefault(c.truck.truck_id, []).append(c)
    for tid, lst in per_truck.items():
        for rank, c in enumerate(sorted(lst, key=lambda x: x.features["c_kb_inr"])):
            c.features["cost_rank_within_truck"] = rank + 1
        for c in lst:
            c.features["n_candidates_for_truck"] = len(lst)
    for c in cands:
        c.features["competing_trucks"] = max(
            cnt.get(s.shipment_id, 1) for s in c.bundle)
        c.features["local_shipment_density"] = len(shipments)
    return cands
