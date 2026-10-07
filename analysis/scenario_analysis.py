#!/usr/bin/env python3
"""TRUCKLY — Deliverables 19 & 20: scenario analysis and sensitivity analysis.

Scenario analysis reuses the main experiment (12 scenarios x 100 days already
run). Sensitivity analysis re-runs the base scenario under perturbed parameters,
because fuel price and waiting cost change the COST MODEL rather than the
instance and therefore cannot be read off the existing results.
"""
from __future__ import annotations
import os, sys, json, copy
import numpy as np
import pandas as pd
import yaml

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
from src.network import RoadNetwork
from src.data_generator import InstanceGenerator
from src.domain import CostModel
from src.simulation import run_instance

TAB = os.path.join(HERE, "outputs", "tables")
RES = os.path.join(HERE, "outputs", "results")

LABELS = {
    "S0_base": "S0  Base case", "S1_low_avail": "S1  Low availability (2/truck)",
    "S2_mod_avail": "S2  Moderate availability (6/truck)",
    "S3_high_avail": "S3  High availability (15/truck)",
    "S4_strict_dl": "S4  Strict deadlines", "S5_relaxed_dl": "S5  Relaxed deadlines",
    "S6_low_util": "S6  Light shipments (low util)",
    "S7_high_util": "S7  Heavy shipments (high util)",
    "S8_small_trucks": "S8  Small-truck fleet", "S9_large_trucks": "S9  Large-truck fleet",
    "S10a_detour_15": "S10a Detour tolerance 15%", "S10b_detour_50": "S10b Detour tolerance 50%",
}


def summarise(K, scenario):
    d = K[K.scenario_id == scenario]
    piv = {p: d[d.policy == p].sort_values("instance_id").reset_index(drop=True)
           for p in d.policy.unique()}
    b0, b2, tr = piv["B0_empty"], piv["B2_greedy"], piv["TRUCKLY"]
    return dict(
        scenario=scenario, label=LABELS.get(scenario, scenario),
        density=round(float(tr.shipment_density.mean()), 2),
        B0_empty_km=round(float(b0.empty_km.mean())),
        B2_empty_km=round(float(b2.empty_km.mean())),
        TR_empty_km=round(float(tr.empty_km.mean())),
        empty_red_vs_B0_pct=round(100 * (b0.empty_km.mean() - tr.empty_km.mean())
                                  / b0.empty_km.mean(), 2),
        empty_red_vs_B2_pct=round(100 * (b2.empty_km.mean() - tr.empty_km.mean())
                                  / b2.empty_km.mean(), 2),
        net_cost_red_vs_B0_pct=round(100 * (b0.net_cost.mean() - tr.net_cost.mean())
                                     / b0.net_cost.mean(), 2),
        net_cost_red_vs_B2_pct=round(100 * (b2.net_cost.mean() - tr.net_cost.mean())
                                     / b2.net_cost.mean(), 2),
        fill_rate_TR_pct=round(float(tr.fill_rate_pct.mean()), 1),
        fill_rate_B2_pct=round(float(b2.fill_rate_pct.mean()), 1),
        util_gain_vs_B0_pp=round(float(tr.util_weight_pct.mean()
                                       - b0.util_weight_pct.mean()), 2),
        served_TR=round(float(tr.served.mean()), 2),
        served_B2=round(float(b2.served.mean()), 2),
        solve_ms=round(float(tr.solve_ms.mean()), 3))


# ---------------------------------------------------------------------------
def sensitivity(cfg, net, gen, R=40):
    """One-factor-at-a-time around the base case."""
    GRID = [
        ("diesel_price_inr_per_litre", "cost", [70, 80, 90, 105, 120]),
        ("driver_wage_inr_per_hour", "cost", [90, 110, 130, 160, 200]),
        ("waiting_cost_multiplier", "cost", [0.0, 0.5, 1.0, 2.0, 3.0]),
        ("empty_km_penalty_inr_per_km", "cost", [0.0, 3.0, 6.0, 12.0, 20.0]),
        ("tariff_inr_per_km", "cost", [10.0, 15.0, 20.0, 28.0, 36.0]),
        ("detour_tolerance", "scenario_defaults", [0.15, 0.25, 0.35, 0.50, 0.70]),
        ("shipment_density", "scenario_defaults", [2.0, 4.0, 6.0, 10.0, 15.0]),
        ("deadline_slack_factor", "scenario_defaults", [1.15, 1.4, 1.8, 2.4, 3.2]),
        ("min_detour_allowance_km", "scenario_defaults", [20.0, 40.0, 60.0, 90.0, 120.0]),
    ]
    rows = []
    for param, section, values in GRID:
        for v in values:
            c = copy.deepcopy(cfg)
            c[section][param] = v
            n2 = RoadNetwork(c) if section == "network" else net
            cost2 = CostModel(c)
            gen2 = InstanceGenerator(c, n2)
            J, I = [], []
            for i in range(R):
                inst = gen2.generate("S0_base", i)
                jr, _, ir = run_instance(inst, n2, cost2, c,
                                         ["B0_empty", "B2_greedy", "TRUCKLY"])
                J.extend(jr); I.append(ir)
            dj = pd.DataFrame(J)
            g = (dj.groupby(["instance_id", "policy"])
                 .agg(empty=("empty_distance_km", "sum"),
                      net=("net_cost_inr", "sum"),
                      fuel=("fuel_litres", "sum"),
                      served=("n_shipments_matched", "sum"),
                      ptkm=("payload_tonne_km", "sum"),
                      ctkm=("capacity_tonne_km", "sum"))
                 .reset_index())
            m = g.groupby("policy").mean(numeric_only=True)
            util = lambda p: 100 * m.loc[p, "ptkm"] / m.loc[p, "ctkm"]
            rows.append(dict(
                parameter=param, value=v, is_base=(v == cfg[section][param]),
                empty_red_vs_B0_pct=round(100 * (m.loc["B0_empty", "empty"]
                                                 - m.loc["TRUCKLY", "empty"])
                                          / m.loc["B0_empty", "empty"], 2),
                empty_red_vs_B2_pct=round(100 * (m.loc["B2_greedy", "empty"]
                                                 - m.loc["TRUCKLY", "empty"])
                                          / m.loc["B2_greedy", "empty"], 2),
                net_cost_red_vs_B0_pct=round(100 * (m.loc["B0_empty", "net"]
                                                    - m.loc["TRUCKLY", "net"])
                                             / m.loc["B0_empty", "net"], 2),
                fuel_change_vs_B0_pct=round(100 * (m.loc["B0_empty", "fuel"]
                                                   - m.loc["TRUCKLY", "fuel"])
                                            / m.loc["B0_empty", "fuel"], 2),
                util_gain_pp=round(util("TRUCKLY") - util("B0_empty"), 2),
                served=round(m.loc["TRUCKLY", "served"], 2)))
        print(f"  swept {param}")
    return pd.DataFrame(rows)


def main():
    cfg = yaml.safe_load(open(os.path.join(HERE, "config.yaml")))
    K = pd.read_csv(os.path.join(TAB, "instance_kpis.csv"))
    S = pd.DataFrame([summarise(K, s) for s in cfg["scenarios"].keys()])
    S.to_csv(os.path.join(TAB, "scenario_analysis.csv"), index=False)

    net = RoadNetwork(cfg); gen = InstanceGenerator(cfg, net)
    SENS = sensitivity(cfg, net, gen, R=40)
    SENS.to_csv(os.path.join(TAB, "sensitivity_analysis.csv"), index=False)

    # tornado: swing in the primary KPI per parameter
    tor = (SENS.groupby("parameter")
           .agg(min_empty_red=("empty_red_vs_B0_pct", "min"),
                max_empty_red=("empty_red_vs_B0_pct", "max"),
                min_netcost_red=("net_cost_red_vs_B0_pct", "min"),
                max_netcost_red=("net_cost_red_vs_B0_pct", "max"))
           .assign(empty_swing_pp=lambda d: d.max_empty_red - d.min_empty_red,
                   netcost_swing_pp=lambda d: d.max_netcost_red - d.min_netcost_red)
           .sort_values("empty_swing_pp", ascending=False).round(2).reset_index())
    tor.to_csv(os.path.join(TAB, "sensitivity_tornado.csv"), index=False)

    L = ["# TRUCKLY — Scenario and Sensitivity Analysis", "",
         "## Deliverable 19 — Scenario analysis (12 scenarios x 100 days each)", "",
         S.to_markdown(index=False), "",
         "**The single most important row-to-row comparison is S1 -> S2 -> S3**",
         "(shipment density 2 -> 6 -> 15 open loads per available truck). Truckly's",
         "benefit is a FUNCTION of how thick the freight market is, not a constant.",
         "Reporting it as a curve rather than a point is what makes the result robust",
         "to the objection that the generator was tuned.", "",
         "## Deliverable 20 — Sensitivity analysis (one-factor-at-a-time, R = 40)", "",
         SENS.to_markdown(index=False), "",
         "### Tornado — which parameters move the result most", "",
         tor.to_markdown(index=False), "",
         f"The dominant parameter is **{tor.iloc[0].parameter}** "
         f"(swing of {tor.iloc[0].empty_swing_pp:.1f} percentage points in",
         "empty-km reduction across its tested range).", ""]
    open(os.path.join(TAB, "scenario_and_sensitivity.md"), "w").write("\n".join(L))

    pd.set_option("display.width", 260)
    print(S.to_string(index=False)); print()
    print(tor.to_string(index=False))


if __name__ == "__main__":
    main()
