#!/usr/bin/env python3
"""
TRUCKLY — Deliverables 16, 17, 18, 21: KPI results, 60% target analysis,
statistical validation, and the failure taxonomy.

Unit of inference = the SIMULATED OPERATING DAY (instance), not the truck.
Trucks within a day compete for the same shipment pool and are therefore not
independent; using n = 3,000 trucks instead of n = 100 days would inflate every
test by a factor of 30 in effective sample size.

Pre-specified analysis (fixed before the run, see docs/pre_registration.md):
  primary endpoint : empty-kilometre reduction, TRUCKLY vs B2_greedy
  primary test     : Wilcoxon signed-rank on paired per-instance differences
  reporting order  : bootstrap CI -> Hodges-Lehmann -> effect size -> p-value
  everything else  : DESCRIPTIVE, reported with CIs, no significance claims
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(HERE, "data", "processed")
TAB = os.path.join(HERE, "outputs", "tables")
RES = os.path.join(HERE, "outputs", "results")
os.makedirs(TAB, exist_ok=True)

B = 10000
RNG = np.random.default_rng(20260816)
POLICY_ORDER = ["B0_empty", "B1_wait_2h", "B1_wait_6h", "B1_wait_12h",
                "B2_greedy", "TRUCKLY"]


# ---------------------------------------------------------------------------
def instance_kpis(df, inst):
    g = (df.groupby(["scenario_id", "instance_id", "policy"])
         .agg(total_km=("total_distance_km", "sum"),
              empty_km=("empty_distance_km", "sum"),
              loaded_km=("loaded_distance_km", "sum"),
              detour_km=("detour_distance_km", "sum"),
              fuel_l=("fuel_litres", "sum"),
              fuel_cost=("fuel_cost_inr", "sum"),
              waiting_hr=("waiting_time_hr", "sum"),
              duty_hr=("duty_time_hr", "sum"),
              driving_hr=("driving_time_hr", "sum"),
              total_cost=("total_cost_inr", "sum"),
              revenue=("revenue_inr", "sum"),
              net_cost=("net_cost_inr", "sum"),
              co2_kg=("co2_kg", "sum"),
              payload_tkm=("payload_tonne_km", "sum"),
              capacity_tkm=("capacity_tonne_km", "sum"),
              served=("n_shipments_matched", "sum"),
              late=("late_deliveries", "sum"),
              trucks=("truck_id", "size"),
              matched_trucks=("is_matched", "sum"),
              solve_ms=("solve_time_ms", "mean"))
         .reset_index())
    g = g.merge(inst[["scenario_id", "instance_id", "n_shipments_offered",
                      "shipment_density"]],
                on=["scenario_id", "instance_id"], how="left")
    g["empty_share_pct"] = 100 * g.empty_km / g.total_km
    g["util_weight_pct"] = 100 * g.payload_tkm / g.capacity_tkm
    g["util_distance_pct"] = 100 * g.loaded_km / g.total_km
    g["fill_rate_pct"] = 100 * g.matched_trucks / g.trucks
    g["service_pct"] = 100 * g.served / g.n_shipments_offered
    g["on_time_pct"] = np.where(g.served > 0, 100 * (1 - g.late / g.served), 100.0)
    g["tkm_per_litre"] = g.payload_tkm / g.fuel_l
    return g


def boot_ci(d, stat=np.mean, alpha=0.05):
    idx = RNG.integers(0, len(d), size=(B, len(d)))
    reps = stat(np.asarray(d)[idx], axis=1)
    return float(np.percentile(reps, 100 * alpha / 2)), \
           float(np.percentile(reps, 100 * (1 - alpha / 2)))


def hodges_lehmann(d):
    d = np.asarray(d)
    if len(d) > 400:
        d = RNG.choice(d, 400, replace=False)
    w = (d[:, None] + d[None, :]) / 2.0
    return float(np.median(w[np.triu_indices(len(d), 0)]))


def paired_compare(a, b, name, kpi, higher_is_better=False):
    """a = comparator, b = TRUCKLY. d = a - b (positive => TRUCKLY lower)."""
    d = np.asarray(a) - np.asarray(b)
    lo, hi = boot_ci(d)
    if np.allclose(d, 0):
        p, rbc = 1.0, 0.0
    else:
        try:
            W, p = stats.wilcoxon(a, b, zero_method="wilcox",
                                  alternative="two-sided")
            nz = int((d != 0).sum())
            rbc = float(1 - 2 * W / (nz * (nz + 1) / 2)) if nz else 0.0
        except ValueError:
            p, rbc = 1.0, 0.0
    sd = d.std(ddof=1)
    base = np.asarray(a)
    return dict(
        comparison=name, kpi=kpi, n_instances=len(d),
        comparator_mean=float(np.mean(a)), truckly_mean=float(np.mean(b)),
        mean_diff=float(d.mean()), ci_low=lo, ci_high=hi,
        hodges_lehmann=hodges_lehmann(d),
        pct_change=float(100 * d.mean() / np.mean(a)) if np.mean(a) != 0 else np.nan,
        cohens_dz=float(d.mean() / sd) if sd > 0 else np.nan,
        rank_biserial=rbc, wilcoxon_p=float(p),
        truckly_better_in_n=int((d > 0).sum() if not higher_is_better
                                else (d < 0).sum()),
        direction="lower is better" if not higher_is_better else "higher is better")


# ---------------------------------------------------------------------------
def main():
    df = pd.read_csv(os.path.join(PROC, "truckly_clean.csv.gz"))
    inst = pd.read_csv(os.path.join(RES, "instances_main.csv"))
    K = instance_kpis(df, inst)
    K.to_csv(os.path.join(TAB, "instance_kpis.csv"), index=False)

    base = K[K.scenario_id == "S0_base"]
    piv = {p: base[base.policy == p].sort_values("instance_id").reset_index(drop=True)
           for p in POLICY_ORDER}
    R = len(piv["TRUCKLY"])

    # ---------------- Deliverable 16: KPI table ---------------------------
    rows = []
    SPEC = [("Total km", "total_km", "km", 0), ("Empty km", "empty_km", "km", 0),
            ("Empty km share", "empty_share_pct", "%", 1),
            ("Loaded km", "loaded_km", "km", 0),
            ("Fuel", "fuel_l", "L", 1), ("Fuel cost", "fuel_cost", "INR", 0),
            ("Waiting time", "waiting_hr", "h", 2),
            ("Driver duty time", "duty_hr", "h", 1),
            ("Weight utilisation", "util_weight_pct", "%", 2),
            ("Distance utilisation", "util_distance_pct", "%", 1),
            ("Backhaul fill rate", "fill_rate_pct", "%", 1),
            ("Total cost", "total_cost", "INR", 0),
            ("Freight revenue", "revenue", "INR", 0),
            ("Net cost (cost - revenue)", "net_cost", "INR", 0),
            ("Shipments served", "served", "count", 2),
            ("On-time rate", "on_time_pct", "%", 1),
            ("Tonne-km per litre", "tkm_per_litre", "t.km/L", 3),
            ("CO2 estimate", "co2_kg", "kg", 0),
            ("Solve time per decision", "solve_ms", "ms", 2)]
    # which direction is an improvement, per KPI
    HIGHER_BETTER = {"Weight utilisation", "Distance utilisation",
                     "Backhaul fill rate", "Freight revenue",
                     "Shipments served", "On-time rate", "Tonne-km per litre",
                     "Loaded km"}
    NO_PCT = {"Solve time per decision"}   # comparator is ~0; a % is meaningless
    for label, col, unit, dp in SPEC:
        r = {"KPI": label, "Unit": unit}
        for p in POLICY_ORDER:
            r[p] = round(float(piv[p][col].mean()), dp)
        b0, b2, tr = r["B0_empty"], r["B2_greedy"], r["TRUCKLY"]
        pp = unit == "%"
        hb = label in HIGHER_BETTER

        def delta(ref):
            if label in NO_PCT or ref == 0:
                return "n/a"
            if pp:
                return f"{tr - ref:+.2f} pp"
            # always signed so that POSITIVE = improvement, whichever
            # direction that is for this KPI
            v = (tr - ref) / ref * 100 if hb else (ref - tr) / ref * 100
            return f"{v:+.1f} %"
        r["Truckly vs B0"] = delta(b0)
        r["Truckly vs B2"] = delta(b2)
        r["Better when"] = "higher" if hb else "lower"
        r["Improvement?"] = ("--" if label in NO_PCT or b0 == 0 else
                             ("yes" if ((tr > b0) if hb else (tr < b0)) else "NO"))
        rows.append(r)
    kpi = pd.DataFrame(rows)
    kpi.to_csv(os.path.join(TAB, "kpi_results.csv"), index=False)

    # ---------------- Deliverable 17: 60% target --------------------------
    tgt = []
    for label, col, comp in [("Empty-km reduction", "empty_km", "B0_empty"),
                             ("Fuel reduction", "fuel_l", "B0_empty"),
                             ("Total-cost reduction", "total_cost", "B0_empty"),
                             ("NET-cost reduction", "net_cost", "B0_empty"),
                             ("Waiting-time reduction", "waiting_hr", "B1_wait_6h"),
                             ("Empty-km reduction", "empty_km", "B2_greedy"),
                             ("NET-cost reduction", "net_cost", "B2_greedy")]:
        a = piv[comp][col].values
        b = piv["TRUCKLY"][col].values
        ratio_of_sums = 100 * (a.sum() - b.sum()) / a.sum() if a.sum() else np.nan
        per_inst = np.where(a != 0, 100 * (a - b) / np.where(a == 0, np.nan, a), np.nan)
        lo, hi = boot_ci(a - b)
        tgt.append(dict(metric=label, comparator=comp,
                        comparator_total=round(a.mean(), 1),
                        truckly_total=round(b.mean(), 1),
                        abs_diff_per_day=round((a - b).mean(), 2),
                        abs_diff_ci=f"[{lo:.2f}, {hi:.2f}]",
                        pct_ratio_of_sums=round(ratio_of_sums, 2),
                        pct_mean_of_per_instance=round(np.nanmean(per_inst), 2),
                        pct_estimator_unstable=bool(
                            abs(np.nanmean(per_inst) - ratio_of_sums) > 5),
                        reaches_60pct_target=bool(ratio_of_sums >= 60)))
    # utilisation improvement in percentage POINTS
    for label, col, comp in [("Weight-utilisation improvement", "util_weight_pct", "B0_empty"),
                             ("Weight-utilisation improvement", "util_weight_pct", "B2_greedy"),
                             ("Distance-utilisation improvement", "util_distance_pct", "B0_empty")]:
        a, b = piv[comp][col].values, piv["TRUCKLY"][col].values
        lo, hi = boot_ci(b - a)
        tgt.append(dict(metric=label + " (percentage POINTS)", comparator=comp,
                        comparator_total=round(a.mean(), 2),
                        truckly_total=round(b.mean(), 2),
                        abs_diff_per_day=round((b - a).mean(), 2),
                        abs_diff_ci=f"[{lo:.2f}, {hi:.2f}]",
                        pct_ratio_of_sums=np.nan,
                        pct_mean_of_per_instance=np.nan,
                        pct_estimator_unstable=False,
                        reaches_60pct_target=False))
    target = pd.DataFrame(tgt)
    target.to_csv(os.path.join(TAB, "target_60pct_analysis.csv"), index=False)

    # ---------------- Deliverable 18: statistical validation --------------
    tests = []
    PRIMARY = ("B2_greedy", "empty_km", "Empty km")
    tests.append(paired_compare(piv["B2_greedy"].empty_km, piv["TRUCKLY"].empty_km,
                                "TRUCKLY vs B2_greedy  [PRIMARY ENDPOINT]", "Empty km"))
    for comp in ["B0_empty", "B1_wait_6h", "B2_greedy"]:
        for col, nm, hib in [("empty_km", "Empty km", False),
                             ("total_km", "Total km", False),
                             ("fuel_l", "Fuel L", False),
                             ("net_cost", "Net cost INR", False),
                             ("total_cost", "Total cost INR", False),
                             ("waiting_hr", "Waiting h", False),
                             ("served", "Shipments served", True),
                             ("util_weight_pct", "Weight utilisation %", True),
                             ("co2_kg", "CO2 kg", False)]:
            if comp == "B2_greedy" and col == "empty_km":
                continue
            tests.append(paired_compare(piv[comp][col], piv["TRUCKLY"][col],
                                        f"TRUCKLY vs {comp}", nm, hib))
    T = pd.DataFrame(tests)
    # Holm-Bonferroni within the SECONDARY family only
    sec = T.index[1:]
    p = T.loc[sec, "wilcoxon_p"].values
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    T["holm_adjusted_p"] = np.nan
    T.loc[sec, "holm_adjusted_p"] = adj
    T["role"] = ["PRIMARY"] + ["secondary (descriptive)"] * (len(T) - 1)
    T.to_csv(os.path.join(TAB, "statistical_tests.csv"), index=False)

    # ---------------- Deliverable 21: failure taxonomy --------------------
    tr = df[(df.policy == "TRUCKLY") & (df.scenario_id == "S0_base")]
    fail = (tr.unmatched_reason.value_counts(normalize=True) * 100).round(2)
    failn = tr.unmatched_reason.value_counts()
    F = pd.DataFrame({"reason": failn.index, "n": failn.values,
                      "pct_of_trucks": fail.values})
    _c = (df[df.policy == "TRUCKLY"]
          .groupby(["scenario_id", "unmatched_reason"]).size().rename("n"))
    by_sc = (_c / _c.groupby(level=0).sum() * 100).rename("pct").reset_index()
    F.to_csv(os.path.join(TAB, "failure_taxonomy.csv"), index=False)
    by_sc.to_csv(os.path.join(TAB, "failure_taxonomy_by_scenario.csv"), index=False)

    # ---------------- markdown report -------------------------------------
    pr = T.iloc[0]
    L = ["# TRUCKLY — Results, 60% Target Analysis and Statistical Validation", "",
         f"Scenario **S0_base**. **R = {R} simulated operating days**, 30 trucks per day, "
         f"{int(piv['TRUCKLY'].n_shipments_offered.mean())} open loads per day.",
         "Common random numbers: every policy saw the identical fleet, shipment pool,",
         "network and per-arc fuel perturbation. The comparison is therefore PAIRED.", "",
         "## Deliverable 16 — KPI results", "",
         kpi.to_markdown(index=False), "",
         "> **Reading the delta columns.** For level variables the delta is a",
         "> **% reduction** (positive = TRUCKLY is lower). For variables already",
         "> expressed in % the delta is in **percentage points** (signed change).",
         "> Percentage deltas are always signed so that **positive = improvement**,",
         "> whichever direction that is for the KPI. `Better when` states that",
         "> `Improvement?` applies it, so no sign has to be interpreted by eye.",
         "> Solve time is marked `n/a` because the B0 comparator is effectively zero",
         "> and a percentage against it is meaningless.", "",
         "## Deliverable 17 — 60% target analysis", "",
         "The 60% figure was stated **before** the experiment as an aspirational",
         "hypothesis. Each metric is reported separately. **No composite 'overall",
         "savings' number is computed**, because averaging percentage reductions",
         "across differently-scaled quantities is not meaningful.", "",
         target.to_markdown(index=False), "",
         "> `pct_estimator_unstable = True` flags a metric where the ratio-of-sums",
         "> and the mean-of-per-instance-ratios disagree by more than 5 points. That",
         "> happens when the comparator is near zero in some days (waiting time is the",
         "> case here), which makes the percentage form unreliable. **Read the absolute",
         "> difference and its CI for those rows, not the percentage.**", "",
         "## Deliverable 18 — Statistical validation", "",
         "### Primary endpoint (pre-specified)", "",
         f"- **Empty-km reduction, TRUCKLY vs B2_greedy**, n = {int(pr.n_instances)} paired days",
         f"- Mean paired difference: **{pr.mean_diff:,.1f} km per operating day** "
         f"(95% bootstrap CI [{pr.ci_low:,.1f}, {pr.ci_high:,.1f}])",
         f"- Hodges-Lehmann estimate: **{pr.hodges_lehmann:,.1f} km**",
         f"- Rank-biserial correlation: **{pr.rank_biserial:.3f}**",
         f"- Wilcoxon signed-rank p = **{pr.wilcoxon_p:.2e}**",
         f"- TRUCKLY lower in **{int(pr.truckly_better_in_n)} / {int(pr.n_instances)}** days",
         "",
         "> **Note on Cohen's dz.** Common random numbers deliberately shrink the SD of",
         "> the paired difference, so dz is mechanically inflated relative to an unpaired",
         "> or non-CRN design and is NOT comparable across designs. It is reported as a",
         "> within-design descriptor only; the rank-biserial correlation and the raw",
         "> difference in km are the effect sizes to quote.", "",
         "### All comparisons", "",
         T.round(4).to_markdown(index=False), "",
         "> Only the first row is a confirmatory test. Everything below it is",
         "> **descriptive**, Holm-adjusted within the secondary family, and carries no",
         "> significance claim. With R controllable by simulating more days, any",
         "> non-zero difference can be made 'significant'; the CI and the effect size",
         "> are the result, not the p-value.", "",
         "## Deliverable 21 — Failure taxonomy (TRUCKLY, S0_base)", "",
         F.to_markdown(index=False), "",
         "This is the answer to *when does Truckly fail?* — and it is the most",
         "actionable table in the project.", ""]
    open(os.path.join(TAB, "results_and_validation.md"), "w").write("\n".join(L))

    pd.set_option("display.width", 260)
    print(kpi.to_string(index=False)); print()
    print(target.to_string(index=False)); print()
    print(T.head(3).round(4).to_string(index=False)); print()
    print(F.to_string(index=False))


if __name__ == "__main__":
    main()
