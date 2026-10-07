"""
TRUCKLY — experiment engine.

Runs every policy on the SAME generated instance with the SAME common random
numbers, and emits three long-format tables:

    journeys    one row per (instance, policy, truck)
    candidates  one row per (instance, truck, bundle) feasible pair   [TRUCKLY]
    instances   one row per (scenario, replication)

Long format with a `policy` column -- not wide baseline_*/optimized_* pairs --
is what makes the paired analysis a one-line groupby and what lets a fourth or
fifth policy be added without touching the schema.
"""
from __future__ import annotations

import time
import numpy as np
import pandas as pd

from .feasibility import empty_return
from .matching import generate_candidates, add_competition_features
from .optimizer import solve_assignment
from .baselines import policy_B0, policy_B1, policy_B2, _journey_from


# ---------------------------------------------------------------------------
def policy_TRUCKLY(trucks, shipments, net, cost, eps, params, cfg,
                   max_bundle=None, return_candidates=False):
    """Stage A-E: candidates -> hard constraints -> CP-SAT -> exact routing."""
    mb = max_bundle if max_bundle is not None else params.get("max_bundle_size", 2)
    t0 = time.perf_counter()
    cands, base, rejects = generate_candidates(
        trucks, shipments, net, cost, eps, params, cfg,
        max_bundle=mb, collect_rejects=return_candidates)
    add_competition_features(cands, shipments)
    gen_ms = (time.perf_counter() - t0) * 1000.0

    chosen, status, solve_ms, obj = solve_assignment(
        cands, base, trucks, shipments)

    sel = {c.truck.truck_id: c for c in chosen}
    selected_ids = {id(c) for c in chosen}
    per_truck_ms = (gen_ms + solve_ms) / max(len(trucks), 1)

    # why did an unmatched truck go empty?
    had_cand = {}
    reject_reason = {}
    for c in cands:
        had_cand[c.truck.truck_id] = True
    for tid, _b, reason, _stage in rejects:
        reject_reason.setdefault(tid, {})
        reject_reason[tid][reason] = reject_reason[tid].get(reason, 0) + 1

    out = []
    for tr in trucks:
        if tr.truck_id in sel:
            c = sel[tr.truck_id]
            j = _journey_from(c.ev, tr, "TRUCKLY",
                              [s.shipment_id for s in c.bundle], "matched",
                              score=c.score, ms=per_truck_ms)
        else:
            b0 = base[tr.truck_id]
            if had_cand.get(tr.truck_id):
                reason = "lost_to_competing_truck"
            else:
                rr = reject_reason.get(tr.truck_id)
                reason = max(rr, key=rr.get) if rr else "no_shipment_in_pool"
            j = _journey_from(b0, tr, "TRUCKLY", [], reason, ms=per_truck_ms)
        j.solver_status = status
        out.append(j)

    meta = dict(solver_status=status, solve_ms=solve_ms, gen_ms=gen_ms,
                n_candidates=len(cands), objective=obj)
    if return_candidates:
        rows = []
        for c in cands:
            r = dict(truck_id=c.truck.truck_id,
                     bundle=",".join(s.shipment_id for s in c.bundle),
                     selected_by_optimiser=int(id(c) in selected_ids))
            r.update(c.features)
            rows.append(r)
        meta["candidate_rows"] = rows
        meta["reject_rows"] = [dict(truck_id=t, bundle=",".join(b),
                                    filter_stage_failed=r, stage=st)
                               for t, b, r, st in rejects]
    return out, meta


# ---------------------------------------------------------------------------
POLICY_FNS = {
    "B0_empty":    lambda **kw: policy_B0(kw["trucks"], kw["shipments"], kw["net"],
                                          kw["cost"], kw["eps"], kw["params"], kw["cfg"]),
    "B1_wait_2h":  lambda **kw: policy_B1(kw["trucks"], kw["shipments"], kw["net"],
                                          kw["cost"], kw["eps"], kw["params"], kw["cfg"], 2.0),
    "B1_wait_6h":  lambda **kw: policy_B1(kw["trucks"], kw["shipments"], kw["net"],
                                          kw["cost"], kw["eps"], kw["params"], kw["cfg"], 6.0),
    "B1_wait_12h": lambda **kw: policy_B1(kw["trucks"], kw["shipments"], kw["net"],
                                          kw["cost"], kw["eps"], kw["params"], kw["cfg"], 12.0),
    "B2_greedy":   lambda **kw: policy_B2(kw["trucks"], kw["shipments"], kw["net"],
                                          kw["cost"], kw["eps"], kw["params"], kw["cfg"],
                                          seed=kw["seed"]),
    "TRUCKLY":     lambda **kw: policy_TRUCKLY(kw["trucks"], kw["shipments"], kw["net"],
                                               kw["cost"], kw["eps"], kw["params"], kw["cfg"],
                                               return_candidates=kw.get("collect_cands", False)),
}


def run_instance(inst, net, cost, cfg, policies, collect_cands=False):
    trucks, ships, eps = inst["trucks"], inst["shipments"], inst["eps"]
    params = inst["params"]
    kw = dict(trucks=trucks, shipments=ships, net=net, cost=cost, eps=eps,
              params=params, cfg=cfg, seed=inst["seed"] % (2**31),
              collect_cands=collect_cands)

    truck_by_id = {t.truck_id: t for t in trucks}
    rev_by_id = {s.shipment_id: s.revenue_inr for s in ships}
    jrows, crows = [], []
    metas = {}
    for pol in policies:
        js, meta = POLICY_FNS[pol](**kw)
        metas[pol] = meta
        for j in js:
            tr = truck_by_id[j.truck_id]
            rec = cost.summarise(j, tr, revenue=sum(rev_by_id[m] for m in j.matched))
            rec.update(dict(
                scenario_id=inst["scenario_id"], instance_id=inst["instance_id"],
                policy=pol, truck_id=j.truck_id, truck_type=tr.truck_type,
                truck_capacity_kg=tr.capacity_kg,
                current_node=tr.current_node, home_node=tr.home_node,
                direct_return_km=tr.direct_return_km,
                matched_shipment_ids="|".join(j.matched),
                route_node_sequence=">".join(j.route),
                match_score=j.match_score, unmatched_reason=j.unmatched_reason,
                solver_status=getattr(j, "solver_status", None) or "not_applicable",
                solve_time_ms=j.solve_ms,
            ))
            jrows.append(rec)
        if pol == "TRUCKLY" and collect_cands and "candidate_rows" in meta:
            for r in meta["candidate_rows"]:
                r.update(scenario_id=inst["scenario_id"],
                         instance_id=inst["instance_id"], policy="TRUCKLY")
                crows.append(r)

    irow = dict(scenario_id=inst["scenario_id"], instance_id=inst["instance_id"],
                seed=inst["seed"], n_trucks=len(trucks),
                n_shipments_offered=len(ships),
                shipment_density=len(ships) / max(len(trucks), 1),
                detour_tolerance=params["detour_tolerance"],
                deadline_slack_factor=params["deadline_slack_factor"],
                diesel_price=cost.diesel,
                truckly_solver_status=metas.get("TRUCKLY", {}).get("solver_status", "not_applicable"),
                truckly_n_candidates=metas.get("TRUCKLY", {}).get("n_candidates", 0),
                truckly_solve_ms=metas.get("TRUCKLY", {}).get("solve_ms", 0.0))
    return jrows, crows, irow
