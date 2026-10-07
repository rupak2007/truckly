"""
TRUCKLY — Stage C: global assignment via OR-Tools CP-SAT.

Model (see docs/methodology.md for the full statement):

    min  sum_{k,b} c_kb y_kb  +  sum_k c_k^empty z_k  +  sum_r pi_r u_r
    s.t. sum_b y_kb + z_k = 1                     for every truck k     (C1)
         sum_{k,b : r in b} y_kb + u_r = 1        for every request r   (C2)
         y, z, u in {0,1}

This is a set-partitioning problem with an outside option. It is solved to
PROVEN OPTIMALITY over the generated candidate set -- the solver status is
recorded on every journey row so the claim is checkable.
"""
from __future__ import annotations

import time
from ortools.sat.python import cp_model

SCALE = 100      # rupees -> paise, so the objective is integral


def solve_assignment(candidates, base_evals, trucks, shipments,
                     time_limit_s=10.0, n_workers=8):
    t0 = time.perf_counter()
    m = cp_model.CpModel()

    y = [m.NewBoolVar(f"y{i}") for i in range(len(candidates))]
    z = {t.truck_id: m.NewBoolVar(f"z_{t.truck_id}") for t in trucks}

    by_truck, by_ship = {}, {}
    for i, c in enumerate(candidates):
        by_truck.setdefault(c.truck.truck_id, []).append(i)
        for s in c.bundle:
            by_ship.setdefault(s.shipment_id, []).append(i)

    for t in trucks:                                             # (C1)
        m.Add(sum(y[i] for i in by_truck.get(t.truck_id, [])) + z[t.truck_id] == 1)
    for s in shipments:                                          # (C2)
        m.Add(sum(y[i] for i in by_ship.get(s.shipment_id, [])) <= 1)

    obj = []
    for i, c in enumerate(candidates):
        rev = sum(s.revenue_inr for s in c.bundle)
        obj.append(int(round((c.ev.obj_inr - rev) * SCALE)) * y[i])
    for t in trucks:
        obj.append(int(round(base_evals[t.truck_id].obj_inr * SCALE)) * z[t.truck_id])
    m.Minimize(sum(obj))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = int(n_workers)
    st = solver.Solve(m)

    status = {cp_model.OPTIMAL: "optimal", cp_model.FEASIBLE: "feasible",
              cp_model.INFEASIBLE: "infeasible",
              cp_model.MODEL_INVALID: "invalid",
              cp_model.UNKNOWN: "timeout"}.get(st, "unknown")

    chosen = []
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i, c in enumerate(candidates):
            if solver.Value(y[i]) == 1:
                chosen.append(c)
    ms = (time.perf_counter() - t0) * 1000.0
    return chosen, status, ms, (solver.ObjectiveValue() / SCALE
                                if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)


def perfect_information_bound(all_candidates, base_evals, trucks, shipments,
                              time_limit_s=30.0):
    """Offline optimum over the SAME candidate set -- used as the ceiling in the
    upper-bound analysis. Identical model; separated for clarity of intent."""
    return solve_assignment(all_candidates, base_evals, trucks, shipments,
                            time_limit_s)
