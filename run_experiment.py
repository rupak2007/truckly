#!/usr/bin/env python3
"""
TRUCKLY — main experiment driver.

Runs every policy on every replication of every scenario under COMMON RANDOM
NUMBERS, and writes the three long-format tables plus the raw shipment/truck/
node/driver exports.

    python3 run_experiment.py --scenarios S0_base --instances 100
    python3 run_experiment.py --all
"""
from __future__ import annotations

import argparse
import json
import os
import time
import hashlib
import numpy as np
import pandas as pd
import yaml

from src.network import RoadNetwork, NODES_RAW, SOURCE_REGION
from src.data_generator import InstanceGenerator
from src.domain import CostModel
from src.simulation import run_instance

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "data", "generated")
PROC = os.path.join(HERE, "data", "processed")
RES = os.path.join(HERE, "outputs", "results")


def export_static(net, cfg):
    """nodes / drivers reference tables (they do not vary by instance)."""
    nodes = pd.DataFrame([{
        "node_id": n[0], "name": n[1], "lat": n[2], "lon": n[3],
        "node_role": n[4], "demand_weight_out": n[5], "demand_weight_in": n[6],
        "region_class": "source" if n[0] in SOURCE_REGION else "sink",
        "provenance_coords": "OBS", "provenance_weights": "ASM",
    } for n in NODES_RAW])
    nodes.to_csv(os.path.join(GEN, "truckly_nodes.csv"), index=False)

    d = cfg["driver"]
    drivers = pd.DataFrame([{
        "driver_rule": k, "value": v, "unit": u, "provenance": "ASM"
    } for k, v, u in [
        ("max_driving_hours", d["max_driving_hours"], "hours"),
        ("max_duty_hours", d["max_duty_hours"], "hours"),
        ("break_after_hours", d["break_after_hours"], "hours"),
        ("break_duration_min", d["break_duration_min"], "minutes"),
        ("wage_inr_per_hour", cfg["cost"]["driver_wage_inr_per_hour"], "INR/hour"),
    ]])
    drivers.to_csv(os.path.join(GEN, "truckly_drivers.csv"), index=False)
    net.save_cache(PROC)
    return nodes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", nargs="*", default=["S0_base"])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--instances", type=int, default=None)
    ap.add_argument("--tag", default="main")
    ap.add_argument("--no-candidates", action="store_true")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(os.path.join(HERE, "config.yaml")))
    for d in (GEN, PROC, RES):
        os.makedirs(d, exist_ok=True)

    net = RoadNetwork(cfg)
    cost = CostModel(cfg)
    gen = InstanceGenerator(cfg, net)
    export_static(net, cfg)

    scenarios = list(cfg["scenarios"].keys()) if a.all else a.scenarios
    R = a.instances or cfg["scenario_defaults"]["n_instances"]
    policies = cfg["experiment"]["policies"]

    cfg_hash = hashlib.sha256(
        json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:12]

    J, C, I, S, T = [], [], [], [], []
    t_start = time.perf_counter()
    for sc in scenarios:
        t0 = time.perf_counter()
        for iid in range(R):
            inst = gen.generate(sc, iid)
            collect = (not a.no_candidates) and sc in (
                "S0_base", "S1_low_avail", "S3_high_avail", "S5_relaxed_dl")
            jr, cr, ir = run_instance(inst, net, cost, cfg, policies,
                                      collect_cands=collect)
            ir["config_hash"] = cfg_hash
            J.extend(jr); C.extend(cr); I.append(ir)

            for s in inst["shipments"]:
                S.append(dict(scenario_id=sc, instance_id=iid,
                              shipment_id=s.shipment_id, origin_node_id=s.origin,
                              dest_node_id=s.dest,
                              pickup_lat=net.lat[net.idx[s.origin]],
                              pickup_lon=net.lon[net.idx[s.origin]],
                              delivery_lat=net.lat[net.idx[s.dest]],
                              delivery_lon=net.lon[net.idx[s.dest]],
                              shipment_weight_kg=s.weight_kg,
                              shipment_volume_m3=round(s.volume_m3, 3),
                              pickup_ready_time_hr=s.ready_time_hr,
                              delivery_deadline_hr=s.deadline_hr,
                              service_time_pickup_min=s.service_pickup_min,
                              service_time_delivery_min=s.service_delivery_min,
                              direct_distance_km=s.direct_km,
                              direct_duration_min=s.direct_min,
                              revenue_inr=s.revenue_inr))
            for t in inst["trucks"]:
                T.append(dict(scenario_id=sc, instance_id=iid,
                              truck_id=t.truck_id, truck_type=t.truck_type,
                              truck_capacity_kg=t.capacity_kg,
                              truck_capacity_m3=t.capacity_m3,
                              base_fuel_l_per_100km=t.base_fuel,
                              load_fuel_coeff=t.load_coeff,
                              truck_current_node=t.current_node,
                              truck_current_lat=net.lat[net.idx[t.current_node]],
                              truck_current_lon=net.lon[net.idx[t.current_node]],
                              home_node=t.home_node,
                              home_lat=net.lat[net.idx[t.home_node]],
                              home_lon=net.lon[net.idx[t.home_node]],
                              available_from_hr=round(t.available_from_hr, 3),
                              must_return_by_hr=round(t.must_return_by_hr, 3),
                              driving_hours_used=round(t.driving_hours_used, 3),
                              driver_id=t.driver_id,
                              direct_return_km=round(t.direct_return_km, 2),
                              direct_return_min=round(t.direct_return_min, 2)))
        print(f"  {sc:16s} R={R}  {time.perf_counter()-t0:6.1f}s")

    dj = pd.DataFrame(J); di = pd.DataFrame(I)
    ds = pd.DataFrame(S); dt = pd.DataFrame(T)
    dj.to_csv(os.path.join(RES, f"journeys_{a.tag}.csv.gz"), index=False,
              compression="gzip")
    dj[dj.scenario_id == "S0_base"].to_csv(
        os.path.join(RES, f"journeys_{a.tag}_S0_base.csv"), index=False)
    di.to_csv(os.path.join(RES, f"instances_{a.tag}.csv"), index=False)
    if C:
        pd.DataFrame(C).to_csv(os.path.join(RES, f"candidates_{a.tag}.csv"),
                               index=False)
    if a.tag == "main":
        # Headline deliverable files = the base scenario (readable size).
        # The full multi-scenario set is kept gzipped alongside.
        ds[ds.scenario_id == "S0_base"].to_csv(
            os.path.join(GEN, "truckly_shipments.csv"), index=False)
        dt[dt.scenario_id == "S0_base"].to_csv(
            os.path.join(GEN, "truckly_trucks.csv"), index=False)
        ds.to_csv(os.path.join(GEN, "truckly_shipments_all_scenarios.csv.gz"),
                  index=False, compression="gzip")
        dt.to_csv(os.path.join(GEN, "truckly_trucks_all_scenarios.csv.gz"),
                  index=False, compression="gzip")

    print(f"\nTOTAL {time.perf_counter()-t_start:.1f}s | journeys {len(dj):,} "
          f"| shipments {len(ds):,} | candidates {len(C):,}")
    print(dj.groupby("policy")[["empty_distance_km", "total_distance_km",
                                "fuel_litres", "total_cost_inr",
                                "utilisation_weight_pct", "waiting_time_hr",
                                "n_shipments_matched"]].mean().round(2))


if __name__ == "__main__":
    main()
