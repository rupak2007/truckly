#!/usr/bin/env python3
"""TRUCKLY — Deliverable 4: descriptive statistics."""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(HERE, "outputs", "tables")
PROC = os.path.join(HERE, "data", "processed")
GEN = os.path.join(HERE, "data", "generated")
os.makedirs(TAB, exist_ok=True)

JOURNEY_VARS = [
    ("total_distance_km", "km"), ("empty_distance_km", "km"),
    ("loaded_distance_km", "km"), ("detour_distance_km", "km"),
    ("fuel_litres", "L"), ("fuel_cost_inr", "INR"),
    ("waiting_time_hr", "hours"), ("driving_time_hr", "hours"),
    ("duty_time_hr", "hours"), ("utilisation_weight_pct", "%"),
    ("utilisation_distance_pct", "%"), ("total_cost_inr", "INR"),
    ("net_cost_inr", "INR"), ("co2_kg", "kg"),
]
SHIPMENT_VARS = [
    ("shipment_weight_kg", "kg"), ("shipment_volume_m3", "m3"),
    ("direct_distance_km", "km"), ("revenue_inr", "INR"),
]


def describe(df, cols, unit_map):
    rows = []
    for c, u in cols:
        v = pd.to_numeric(df[c], errors="coerce").dropna()
        if v.empty:
            continue
        q1, q3 = v.quantile(.25), v.quantile(.75)
        rows.append({
            "Variable": c, "Unit": u, "n": len(v),
            "Mean": v.mean(), "SD": v.std(ddof=1), "Min": v.min(),
            "P10": v.quantile(.10), "Q1 (P25)": q1, "Median (P50)": v.median(),
            "Q3 (P75)": q3, "P90": v.quantile(.90), "Max": v.max(),
            "IQR": q3 - q1, "Skew": v.skew(),
        })
    return pd.DataFrame(rows)


def main():
    clean = pd.read_csv(os.path.join(PROC, "truckly_clean.csv"))     # S0_base
    ships = pd.read_csv(os.path.join(GEN, "truckly_shipments.csv"))  # S0_base
    base = clean[clean.policy == "B0_empty"]

    blocks = {
        "A_journey_level_BASELINE_B0": describe(base, JOURNEY_VARS, None),
        "B_shipment_level": describe(ships, SHIPMENT_VARS, None),
        "C_journey_level_TRUCKLY": describe(
            clean[clean.policy == "TRUCKLY"], JOURNEY_VARS, None),
    }
    for k, v in blocks.items():
        v.round(3).to_csv(os.path.join(TAB, f"descriptive_{k}.csv"), index=False)

    # policy comparison at journey level
    pol = (clean.groupby("policy")
           .agg(n=("total_distance_km", "size"),
                mean_total_km=("total_distance_km", "mean"),
                mean_empty_km=("empty_distance_km", "mean"),
                mean_fuel_l=("fuel_litres", "mean"),
                mean_cost=("total_cost_inr", "mean"),
                mean_net_cost=("net_cost_inr", "mean"),
                mean_wait_hr=("waiting_time_hr", "mean"),
                mean_util_w=("utilisation_weight_pct", "mean"),
                fill_rate_pct=("is_matched", lambda x: 100 * x.mean()))
           .round(2))
    pol.to_csv(os.path.join(TAB, "descriptive_by_policy.csv"))

    fmt = lambda d: d.round(2).to_markdown(index=False)
    L = ["# TRUCKLY — Descriptive Statistics", "",
         "Scenario **S0_base**, 100 simulated operating days, 30 trucks per day.",
         "",
         "> Two units of analysis are present, so the table is split into blocks",
         "> with their own `n`. Block A/C are per truck-journey; Block B is per",
         "> shipment. A single table with one `n` would be wrong.", "",
         "## Block A — Journey level, BASELINE B0 (empty return)", "",
         "This block characterises **the problem**: what the fleet looks like",
         "under current practice.", "", fmt(blocks["A_journey_level_BASELINE_B0"]),
         "", "## Block B — Shipment level (the open freight pool)", "",
         fmt(blocks["B_shipment_level"]), "",
         "## Block C — Journey level, TRUCKLY", "",
         fmt(blocks["C_journey_level_TRUCKLY"]), "",
         "## Block D — Journey means by policy", "",
         pol.to_markdown(), "",
         "*Provenance: journey and shipment records are SIM (simulated); node",
         "coordinates are OBS; distances are DRV from an ASM circuity model;",
         "costs are DRV from ASM unit prices. See docs/data_dictionary.md.*", ""]
    open(os.path.join(TAB, "descriptive_statistics.md"), "w").write("\n".join(L))

    pd.set_option("display.width", 250)
    print(blocks["A_journey_level_BASELINE_B0"].round(2).to_string(index=False))
    print()
    print(blocks["B_shipment_level"].round(2).to_string(index=False))
    print()
    print(pol.to_string())


if __name__ == "__main__":
    main()
