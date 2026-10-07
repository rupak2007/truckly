"""
TRUCKLY — hard-constraint feasibility filter and exact route evaluation.

The filter is a cascade, cheapest test first, and every rejection is tagged so
the funnel can be counted (this feeds the failure taxonomy).

Route evaluation is EXACT for bundles of size <= 3: with k requests there are
(2k)!/2^k precedence-valid orderings (2 for k=1, 6 for k=2, 90 for k=3), all
enumerable in microseconds. OR-Tools Routing (src/routing.py) is used for the
Solomon validation and for larger bundles; using exact enumeration in the hot
loop is both faster and provably optimal, and is documented as such.
"""
from __future__ import annotations

from itertools import permutations
from typing import List, Tuple
import numpy as np

from .domain import Truck, Shipment, Leg

REASONS = ["matched", "no_shipment_in_pool", "capacity", "volume",
           "deadline_infeasible", "detour_exceeded", "driver_hours",
           "return_window", "lost_to_competing_truck", "not_selected"]


# ---------------------------------------------------------------------------
def valid_orders(k: int) -> List[Tuple[int, ...]]:
    """All pickup-before-delivery orderings of k requests.

    Encoding: +i = pickup of request i, -(i+1) = delivery of request i.
    """
    toks = [i for i in range(k)] + [-(i + 1) for i in range(k)]
    out = []
    for perm in permutations(toks):
        seen = set()
        ok = True
        for t in perm:
            if t >= 0:
                seen.add(t)
            else:
                if (-t - 1) not in seen:
                    ok = False
                    break
        if ok:
            out.append(perm)
    return out


_ORDER_CACHE = {k: valid_orders(k) for k in (1, 2, 3)}


# ---------------------------------------------------------------------------
class RouteEval:
    __slots__ = ("feasible", "reason", "route", "legs", "waiting_hr",
                 "service_hr", "drive_hr", "duty_hr", "total_km", "empty_km",
                 "loaded_km", "detour_km", "fuel_l", "cost_inr", "obj_inr", "arrive_home_hr",
                 "lateness_min", "late_n")

    def __init__(self):
        self.feasible = False
        self.reason = "not_selected"
        self.route = []
        self.legs = []
        self.waiting_hr = 0.0
        self.service_hr = 0.0
        self.drive_hr = 0.0
        self.duty_hr = 0.0
        self.total_km = 0.0
        self.empty_km = 0.0
        self.loaded_km = 0.0
        self.detour_km = 0.0
        self.fuel_l = 0.0
        self.cost_inr = float("inf")
        self.obj_inr = float("inf")
        self.arrive_home_hr = 0.0
        self.lateness_min = 0.0
        self.late_n = 0


def detour_budget_km(truck, theta, min_abs_km=0.0):
    """Route-length ceiling. Operators think in percentages AND in absolute
    kilometres -- a 25% allowance on a 65 km return is 16 km, which no real
    dispatcher would treat as the limit of acceptable detour. The budget is
    therefore max(theta * d_ret, min_abs_km)."""
    return truck.direct_return_km + max(theta * truck.direct_return_km, min_abs_km)


def evaluate_order(truck: Truck, bundle: List[Shipment], order, net, cost,
                   eps, theta, drv_cfg, hard_windows=True,
                   min_detour_km=0.0) -> RouteEval:
    """Exact simulation of one candidate route. Returns cost = inf if infeasible."""
    ev = RouteEval()
    seq_nodes = [truck.current_node]
    kinds = []                       # (node, kind, shipment_index)
    for t in order:
        if t >= 0:
            seq_nodes.append(bundle[t].origin); kinds.append(("P", t))
        else:
            seq_nodes.append(bundle[-t - 1].dest); kinds.append(("D", -t - 1))
    seq_nodes.append(truck.home_node)

    payload_kg = 0.0
    payload_m3 = 0.0
    time_hr = truck.available_from_hr
    drive_hr = 0.0
    wait_hr = 0.0
    svc_hr = 0.0
    total_km = 0.0
    legs = []

    max_km = detour_budget_km(truck, theta, min_detour_km)
    rem_drive = drv_cfg["max_driving_hours"] - truck.driving_hours_used

    for i in range(len(seq_nodes) - 1):
        a, b = seq_nodes[i], seq_nodes[i + 1]
        km = net.d(a, b)
        mins = net.t(a, b)
        rfac = net.rf(a, b)
        e = float(eps[net.idx[a], net.idx[b]])
        pt = payload_kg / 1000.0
        fuel = cost.arc_fuel_litres(km, pt, truck.base_fuel, truck.load_coeff, rfac, e)
        legs.append(Leg(a, b, km, mins, pt, rfac, fuel))

        total_km += km
        drive_hr += mins / 60.0
        time_hr += mins / 60.0

        if total_km > max_km + 1e-9:
            ev.reason = "detour_exceeded"; return ev
        if drive_hr > rem_drive + 1e-9:
            ev.reason = "driver_hours"; return ev

        if i < len(kinds):
            kind, si = kinds[i]
            sh = bundle[si]
            if kind == "P":
                if time_hr < sh.ready_time_hr:
                    w = sh.ready_time_hr - time_hr
                    wait_hr += w
                    time_hr = sh.ready_time_hr
                payload_kg += sh.weight_kg
                payload_m3 += sh.volume_m3
                if payload_kg > truck.capacity_kg + 1e-6:
                    ev.reason = "capacity"; return ev
                if payload_m3 > truck.capacity_m3 + 1e-6:
                    ev.reason = "volume"; return ev
                time_hr += sh.service_pickup_min / 60.0
                svc_hr += sh.service_pickup_min / 60.0
            else:
                late = (time_hr - sh.deadline_hr) * 60.0
                if late > 1e-6:
                    if hard_windows:
                        ev.reason = "deadline_infeasible"; return ev
                    ev.lateness_min += late; ev.late_n += 1
                payload_kg -= sh.weight_kg
                payload_m3 -= sh.volume_m3
                time_hr += sh.service_delivery_min / 60.0
                svc_hr += sh.service_delivery_min / 60.0

    duty = drive_hr + svc_hr + wait_hr
    # mandatory break (R11): inserted as duty time when continuous driving
    # exceeds the limit
    if drive_hr > drv_cfg["break_after_hours"]:
        n_breaks = int(drive_hr // drv_cfg["break_after_hours"])
        duty += n_breaks * drv_cfg["break_duration_min"] / 60.0
        time_hr += n_breaks * drv_cfg["break_duration_min"] / 60.0

    if duty > (truck.must_return_by_hr - truck.available_from_hr) + 1e-9:
        ev.reason = "driver_hours"; return ev
    if time_hr > truck.must_return_by_hr + 1e-9:
        ev.reason = "return_window"; return ev

    loaded_km = sum(l.km for l in legs if l.payload_t > 1e-9)
    fuel_l = sum(l.fuel_l for l in legs)

    ev.feasible = True
    ev.reason = "matched"
    ev.route = seq_nodes
    ev.legs = legs
    ev.waiting_hr = wait_hr
    ev.service_hr = svc_hr
    ev.drive_hr = drive_hr
    ev.duty_hr = duty
    ev.total_km = total_km
    ev.loaded_km = loaded_km
    ev.empty_km = total_km - loaded_km
    ev.detour_km = total_km - truck.direct_return_km
    ev.fuel_l = fuel_l
    ev.arrive_home_hr = time_hr

    fuel_cost = fuel_l * cost.diesel
    driver_cost = (drive_hr + svc_hr) * cost.wage_hr \
                  + wait_hr * cost.wage_hr * cost.wait_mult
    toll = total_km * cost.toll_km
    ev.cost_inr = fuel_cost + driver_cost + toll + cost.fixed
    # Optimisation objective = accounting cost + managerial empty-running
    # penalty. Reported money figures use cost_inr; the optimiser uses obj_inr.
    ev.obj_inr = ev.cost_inr + cost.lambda_empty * ev.empty_km
    return ev


def best_route(truck, bundle, net, cost, eps, theta, drv_cfg,
               hard_windows=True, min_detour_km=0.0):
    """Exact optimal ordering for this (truck, bundle) pair."""
    k = len(bundle)
    orders = _ORDER_CACHE.get(k)
    if orders is None:
        orders = valid_orders(k)
    best = RouteEval()
    reasons = {}
    for o in orders:
        ev = evaluate_order(truck, bundle, o, net, cost, eps, theta,
                            drv_cfg, hard_windows, min_detour_km)
        if ev.feasible and ev.obj_inr < best.obj_inr:
            best = ev
        elif not ev.feasible:
            reasons[ev.reason] = reasons.get(ev.reason, 0) + 1
    if not best.feasible and reasons:
        best.reason = max(reasons, key=reasons.get)
    return best


def empty_return(truck, net, cost, eps, drv_cfg):
    """The outside option: drive home empty. Feasible by construction."""
    ev = evaluate_order(truck, [], (), net, cost, eps,
                        theta=10.0, drv_cfg=drv_cfg, hard_windows=True)
    if not ev.feasible:
        raise AssertionError(
            f"B0 infeasible for {truck.truck_id} ({ev.reason}): the generator "
            "must guarantee every truck can at least drive home empty.")
    return ev


# ---------------------------------------------------------------------------
def quick_prefilter(truck, sh, net, theta, min_detour_km=0.0):
    """Cheap tests, applied before any route evaluation. Returns reason or None."""
    if sh.weight_kg > truck.capacity_kg:
        return "capacity"
    if sh.volume_m3 > truck.capacity_m3:
        return "volume"
    # optimistic lower bound on route length
    lb = net.d(truck.current_node, sh.origin) + sh.direct_km + net.d(sh.dest, truck.home_node)
    if lb > detour_budget_km(truck, theta, min_detour_km) + 1e-9:
        return "detour_exceeded"
    return None
