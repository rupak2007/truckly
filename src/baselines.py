"""
TRUCKLY — the three baseline policies.

INFORMATION PARITY (this is the fairness rule the whole experiment rests on):
all four policies see the SAME shipment pool and the SAME network at the same
decision epoch. They differ ONLY in decision rule. No policy is given foresight
of shipments the others cannot see.

  B0  empty return   -- no matching at all
  B1  wait for load  -- time-priority rule: accept the FIRST feasible shipment
                        by ready-time order whose pre-departure idle wait is
                        within Tmax. No comparison, no scoring, no optimisation.
  B2  naive greedy   -- trucks in seeded order; each takes its highest-scoring
                        feasible single shipment; shipment removed from pool.
                        No global coordination, no bundling.
"""
from __future__ import annotations

import time
import numpy as np

from .feasibility import best_route, quick_prefilter, empty_return


def _journey_from(ev, truck, policy, matched, reason, score=float("nan"), ms=0.0):
    from .domain import Journey
    j = Journey(truck_id=truck.truck_id, policy=policy)
    j.matched = list(matched)
    j.legs = ev.legs
    j.route = ev.route
    j.waiting_hr = ev.waiting_hr
    j.service_hr = ev.service_hr
    j.late_deliveries = ev.late_n
    j.lateness_min = ev.lateness_min
    j.feasible = ev.feasible
    j.unmatched_reason = reason
    j.match_score = score
    j.solve_ms = ms
    return j


# ---------------------------------------------------------------------------
def policy_B0(trucks, shipments, net, cost, eps, params, cfg):
    drv = cfg["driver"]
    out = []
    for tr in trucks:
        t0 = time.perf_counter()
        ev = empty_return(tr, net, cost, eps, drv)
        out.append(_journey_from(ev, tr, "B0_empty", [], "policy_no_matching",
                                 ms=(time.perf_counter() - t0) * 1000.0))
    return out, {}


# ---------------------------------------------------------------------------
def policy_B1(trucks, shipments, net, cost, eps, params, cfg, t_max_hours):
    """Wait-for-load. Take the first thing that turns up, not the best thing."""
    theta = params["detour_tolerance"]
    mdk = params.get("min_detour_allowance_km", 0.0)
    drv = cfg["driver"]
    pool = sorted(shipments, key=lambda s: s.ready_time_hr)
    taken = set()
    out = []
    order = sorted(trucks, key=lambda t: t.available_from_hr)
    for tr in order:
        t0 = time.perf_counter()
        b0 = empty_return(tr, net, cost, eps, drv)
        picked, picked_ev, reason = None, None, "no_shipment_in_pool"
        for sh in pool:
            if sh.shipment_id in taken:
                continue
            r = quick_prefilter(tr, sh, net, theta, mdk)
            if r is not None:
                reason = r
                continue
            ev = best_route(tr, [sh], net, cost, eps, theta, drv, min_detour_km=mdk)
            if not ev.feasible:
                reason = ev.reason
                continue
            if ev.waiting_hr > t_max_hours + 1e-9:
                reason = "return_window"
                continue
            # identical economics to the CP-SAT objective: take the load only
            # if its revenue exceeds the incremental cost of collecting it
            if ev.obj_inr - sh.revenue_inr >= b0.obj_inr:
                reason = "not_economic"
                continue
            picked, picked_ev = sh, ev
            break
        ms = (time.perf_counter() - t0) * 1000.0
        if picked is None:
            out.append(_journey_from(b0, tr, f"B1_wait_{int(t_max_hours)}h", [],
                                     reason, ms=ms))
        else:
            taken.add(picked.shipment_id)
            out.append(_journey_from(picked_ev, tr, f"B1_wait_{int(t_max_hours)}h",
                                     [picked.shipment_id], "matched", ms=ms))
    return out, {}


# ---------------------------------------------------------------------------
def policy_B2(trucks, shipments, net, cost, eps, params, cfg, seed=0):
    """Naive greedy. First-come-first-served over a seeded truck order."""
    from .matching import score_candidate
    theta = params["detour_tolerance"]
    mdk = params.get("min_detour_allowance_km", 0.0)
    drv = cfg["driver"]
    w = cfg["score_weights"]
    max_wait = params["max_wait_hours"]
    slack_ref = float(np.percentile(
        [s.deadline_hr - s.ready_time_hr for s in shipments], 95)) if shipments else 1.0

    rng = np.random.default_rng(seed)
    order = list(trucks)
    rng.shuffle(order)

    available = {s.shipment_id: s for s in shipments}
    out = []
    for tr in order:
        t0 = time.perf_counter()
        b0 = empty_return(tr, net, cost, eps, drv)
        best, best_ev, best_sc = None, None, -np.inf
        reason = "no_shipment_in_pool"
        for sh in list(available.values()):
            r = quick_prefilter(tr, sh, net, theta, mdk)
            if r is not None:
                reason = r
                continue
            ev = best_route(tr, [sh], net, cost, eps, theta, drv, min_detour_km=mdk)
            if not ev.feasible:
                reason = ev.reason
                continue
            if ev.waiting_hr > max_wait + 1e-9:
                reason = "return_window"
                continue
            sc, _ = score_candidate(tr, [sh], ev, b0, net, theta, w,
                                    max_wait, slack_ref)
            if sc > best_sc:
                best, best_ev, best_sc = sh, ev, sc
        ms = (time.perf_counter() - t0) * 1000.0
        if best is None:
            out.append(_journey_from(b0, tr, "B2_greedy", [], reason, ms=ms))
        else:
            # greedy accepts only if the load pays for itself
            if best_ev.obj_inr - best.revenue_inr < b0.obj_inr:
                del available[best.shipment_id]
                out.append(_journey_from(best_ev, tr, "B2_greedy",
                                         [best.shipment_id], "matched",
                                         score=best_sc, ms=ms))
            else:
                out.append(_journey_from(b0, tr, "B2_greedy", [],
                                         "not_economic", ms=ms))
    by_id = {j.truck_id: j for j in out}
    return [by_id[t.truck_id] for t in trucks], {}
