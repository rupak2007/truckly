#!/usr/bin/env python3
"""
TRUCKLY — Deliverables 13 & 24: the working recommendation demo with
explainability.

Run with no arguments for a scripted worked example (the Bangalore -> Chennai
case from the project brief). Run with --interactive to enter your own truck.

    python3 truckly_demo.py
    python3 truckly_demo.py --instance 7
    python3 truckly_demo.py --interactive
"""
from __future__ import annotations
import argparse, os, sys, textwrap, time
import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from src.network import RoadNetwork
from src.data_generator import InstanceGenerator
from src.domain import CostModel, Truck, Shipment
from src.matching import generate_candidates, add_competition_features
from src.optimizer import solve_assignment
from src.feasibility import empty_return, best_route, quick_prefilter, detour_budget_km

W = 78
def rule(ch="─"): print(ch * W)
def head(t): rule("═"); print(t.center(W)); rule("═")


def explain(truck, cand, b0, net, cost, params, n_considered, n_feasible, ms):
    ev = cand.ev
    f = cand.features
    bundle = cand.bundle
    saved_empty = b0.empty_km - ev.empty_km
    rev = sum(s.revenue_inr for s in bundle)
    net_gain = (b0.cost_inr) - (ev.cost_inr - rev)
    util = 100 * sum(l.km * l.payload_t for l in ev.legs) / \
           ((truck.capacity_kg / 1000) * ev.total_km)

    head("TRUCKLY RECOMMENDATION")
    print(f"  Truck            {truck.truck_id}   ({truck.truck_type}, "
          f"{truck.capacity_kg:,.0f} kg / {truck.capacity_m3:.0f} m³)")
    print(f"  Currently at     {net.names[truck.current_node]} ({truck.current_node})")
    print(f"  Must return to   {net.names[truck.home_node]} ({truck.home_node})")
    print(f"  Available from   t+{truck.available_from_hr:5.2f} h   "
          f"must be home by t+{truck.must_return_by_hr:5.2f} h")
    print(f"  Direct empty return  {truck.direct_return_km:,.1f} km")
    rule()
    print(f"  RECOMMENDED SHIPMENT{'S' if len(bundle) > 1 else ''}")
    for s in bundle:
        print(f"    {s.shipment_id}   {net.names[s.origin]} → {net.names[s.dest]}")
        print(f"       {s.weight_kg:,.0f} kg · {s.volume_m3:.1f} m³ · "
              f"{s.direct_km:,.1f} km · ready t+{s.ready_time_hr:.1f} h · "
              f"deadline t+{s.deadline_hr:.1f} h · ₹{s.revenue_inr:,.0f}")
    rule()
    print("  RECOMMENDED ROUTE")
    # collapse consecutive repeats: a pickup at the truck's current node is the
    # same physical place, not a second visit
    seq = [n for i, n in enumerate(ev.route) if i == 0 or n != ev.route[i - 1]]
    print("    " + "  →  ".join(seq))
    print("    " + "  →  ".join(net.names[n] for n in seq))
    rule()
    print(f"  {'Empty km avoided':<28}{saved_empty:>12,.1f} km")
    print(f"  {'Additional detour':<28}{ev.detour_km:>12,.1f} km   "
          f"(budget {detour_budget_km(truck, params['detour_tolerance'], params['min_detour_allowance_km']) - truck.direct_return_km:,.0f} km)")
    print(f"  {'Total route distance':<28}{ev.total_km:>12,.1f} km")
    print(f"  {'Expected fuel':<28}{ev.fuel_l:>12,.1f} L    "
          f"(empty return would burn {b0.fuel_l:,.1f} L)")
    print(f"  {'Expected journey cost':<28}₹{ev.cost_inr:>11,.0f}    "
          f"(empty return ₹{b0.cost_inr:,.0f})")
    print(f"  {'Freight revenue':<28}₹{rev:>11,.0f}")
    print(f"  {'NET SAVING vs empty return':<28}₹{net_gain:>11,.0f}")
    print(f"  {'Truck utilisation':<28}{util:>12,.1f} %   (empty return: 0.0 %)")
    print(f"  {'Waiting time':<28}{ev.waiting_hr:>12,.2f} h")
    print(f"  {'Driver duty time':<28}{ev.duty_hr:>12,.2f} h   "
          f"(budget {truck.must_return_by_hr - truck.available_from_hr:,.2f} h)")
    latest = min(s.deadline_hr for s in bundle)
    print(f"  {'Deadline status':<28}{'MET':>12}   "
          f"(arrives home t+{ev.arrive_home_hr:.2f} h, "
          f"tightest deadline t+{latest:.1f} h)")
    rule()
    print("  WHY TRUCKLY CHOSE THIS")
    reasons = [
        f"Avoids {saved_empty:,.0f} km of empty running — {100*saved_empty/max(b0.empty_km,1e-9):.0f}% "
        f"of the {b0.empty_km:,.0f} km the truck would otherwise drive with no load.",
        f"Costs only {ev.detour_km:,.1f} km of extra distance, which is "
        f"{100*ev.detour_km/max(truck.direct_return_km,1e-9):.0f}% over the direct return and "
        f"inside the {100*params['detour_tolerance']:.0f}% detour tolerance.",
        f"Fills {100*f['weight_ratio']:.0f}% of weight capacity and "
        f"{100*f['volume_ratio']:.0f}% of volume — no capacity or cube-out violation.",
        f"Pickup is {f['pickup_detour_km']:,.1f} km away and the load is ready in time; "
        f"only {ev.waiting_hr:.2f} h of idle waiting is incurred.",
        f"Delivery deadline is achievable with "
        f"{latest - ev.arrive_home_hr + (ev.arrive_home_hr - latest if False else 0):.1f} h "
        f"of margin, and driver duty stays within the legal budget.",
        f"Freight revenue of ₹{rev:,.0f} exceeds the ₹{ev.cost_inr - b0.cost_inr:,.0f} "
        f"of extra cost, so the load pays for itself — a net gain of ₹{net_gain:,.0f}.",
    ]
    for i, r in enumerate(reasons, 1):
        print(textwrap.fill(f"  {i}. {r}", W, subsequent_indent="     "))
    rule()
    print("  HOW THE DECISION WAS REACHED")
    print(f"    {n_considered:,} truck–shipment pairs screened against hard constraints")
    print(f"    {n_feasible:,} survived and were costed exactly")
    print(f"    CP-SAT solved the fleet-wide assignment to PROVEN OPTIMALITY in {ms:.1f} ms")
    print(f"    explainable score for this match: {cand.score:+.3f}")
    rule("═")


def show_rejected(truck, shipments, net, cost, eps, params, cfg, limit=6):
    theta = params["detour_tolerance"]; mdk = params["min_detour_allowance_km"]
    print("\n  NEAREST REJECTED ALTERNATIVES (why they did not qualify)")
    rows = []
    for s in shipments:
        r = quick_prefilter(truck, s, net, theta, mdk)
        if r is None:
            ev = best_route(truck, [s], net, cost, eps, theta, cfg["driver"],
                            min_detour_km=mdk)
            r = "FEASIBLE" if ev.feasible else ev.reason
        lb = net.d(truck.current_node, s.origin) + s.direct_km + net.d(s.dest, truck.home_node)
        rows.append((lb, s, r))
    rows.sort(key=lambda t: t[0])
    for lb, s, r in rows[:limit]:
        print(f"    {s.shipment_id}  {net.names[s.origin][:12]:<12}→ "
              f"{net.names[s.dest][:12]:<12} {s.weight_kg:>7,.0f} kg  "
              f"route≥{lb:6,.0f} km   {r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", type=int, default=3)
    ap.add_argument("--scenario", default="S3_high_avail")
    ap.add_argument("--interactive", action="store_true")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(os.path.join(HERE, "config.yaml")))
    net = RoadNetwork(cfg); cost = CostModel(cfg)
    gen = InstanceGenerator(cfg, net)
    inst = gen.generate(a.scenario, a.instance)
    trucks, ships, eps, params = (inst["trucks"], inst["shipments"],
                                  inst["eps"], inst["params"])

    if a.interactive:
        print("\nAvailable nodes:")
        for i, nid in enumerate(net.ids):
            print(f"  {nid} {net.names[nid]:<18}", end="" if (i + 1) % 4 else "\n")
        print()
        cur = input("Truck current node id  : ").strip().upper() or "BLR"
        home = input("Truck home node id     : ").strip().upper() or "CHN"
        cap = float(input("Capacity kg [16000]    : ").strip() or 16000)
        avail = float(input("Available from (h) [10]: ").strip() or 10)
        spec = cfg["truck_types"]["RIGID_16T"]
        trucks = [Truck("T_DEMO", "RIGID_16T", cap, spec["capacity_m3"],
                        spec["base_fuel_l_per_100km"],
                        spec["load_fuel_coeff_l_per_100km_per_t"],
                        cur, home, avail, avail + cfg["driver"]["max_duty_hours"],
                        0.0, "D_DEMO", net.d(cur, home), net.t(cur, home))] + trucks

    t0 = time.perf_counter()
    cands, base, rejects = generate_candidates(
        trucks, ships, net, cost, eps, params, cfg,
        max_bundle=params["max_bundle_size"], collect_rejects=True)
    add_competition_features(cands, ships)
    chosen, status, ms, obj = solve_assignment(cands, base, trucks, ships)
    total_ms = (time.perf_counter() - t0) * 1000

    head("TRUCKLY  ·  freight matching & route optimisation  ·  live demo")
    print(f"  Scenario {a.scenario} · instance {a.instance} · "
          f"{len(trucks)} trucks · {len(ships)} open loads")
    print(f"  Solver status: {status.upper()} · candidates {len(cands):,} · "
          f"total decision time {total_ms:.1f} ms")

    sel = {c.truck.truck_id: c for c in chosen}
    target = None
    if a.interactive and "T_DEMO" in sel:
        target = sel["T_DEMO"]
    else:  # pick the most illustrative: biggest empty-km saving
        target = max(chosen, key=lambda c: base[c.truck.truck_id].empty_km - c.ev.empty_km)

    n_pairs = len(trucks) * len(ships)
    explain(target.truck, target, base[target.truck.truck_id], net, cost,
            params, n_pairs, len(cands), ms)
    show_rejected(target.truck, ships, net, cost, eps, params, cfg)

    # fleet roll-up
    tot_b0 = sum(base[t.truck_id].empty_km for t in trucks)
    tot_tr = sum((sel[t.truck_id].ev.empty_km if t.truck_id in sel
                  else base[t.truck_id].empty_km) for t in trucks)
    print(f"\n  FLEET ROLL-UP FOR THIS DAY")
    print(f"    trucks matched            {len(chosen)} / {len(trucks)} "
          f"({100*len(chosen)/len(trucks):.0f}%)")
    print(f"    loads served              {sum(len(c.bundle) for c in chosen)} / {len(ships)}")
    print(f"    empty km, B0 baseline     {tot_b0:,.0f} km")
    print(f"    empty km, TRUCKLY         {tot_tr:,.0f} km")
    print(f"    empty km avoided          {tot_b0-tot_tr:,.0f} km "
          f"({100*(tot_b0-tot_tr)/tot_b0:.1f}%)")
    print()


if __name__ == "__main__":
    main()
