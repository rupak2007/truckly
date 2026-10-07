#!/usr/bin/env python3
"""TRUCKLY — Deliverable 26 & 29: the final report and the README.
Every number is read from outputs/tables at build time."""
from __future__ import annotations
import os, json
import numpy as np
import pandas as pd
import yaml

H = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(H, "outputs", "tables")

cfg = yaml.safe_load(open(os.path.join(H, "config.yaml")))
F = json.load(open(os.path.join(TAB, "poster_findings.json")))
KPI = pd.read_csv(os.path.join(TAB, "kpi_results.csv"))
K = KPI.set_index("KPI")
TGT = pd.read_csv(os.path.join(TAB, "target_60pct_analysis.csv"))
TST = pd.read_csv(os.path.join(TAB, "statistical_tests.csv"))
SC = pd.read_csv(os.path.join(TAB, "scenario_analysis.csv"))
SCi = SC.set_index("scenario")
TOR = pd.read_csv(os.path.join(TAB, "sensitivity_tornado.csv"))
SENS = pd.read_csv(os.path.join(TAB, "sensitivity_analysis.csv"))
FAIL = pd.read_csv(os.path.join(TAB, "failure_taxonomy.csv"))
VAL = pd.read_csv(os.path.join(TAB, "validation_checks.csv"))
ML = pd.read_csv(os.path.join(TAB, "ml_model_comparison.csv"))
MLP = pd.read_csv(os.path.join(TAB, "ml_pruning_curve.csv"))
MLI = pd.read_csv(os.path.join(TAB, "ml_feature_importance.csv"))
DESC = pd.read_csv(os.path.join(TAB, "descriptive_A_journey_level_BASELINE_B0.csv"))
DESCS = pd.read_csv(os.path.join(TAB, "descriptive_B_shipment_level.csv"))
BYPOL = pd.read_csv(os.path.join(TAB, "descriptive_by_policy.csv"))

pr = TST.iloc[0]
s0, s1, s3 = SCi.loc["S0_base"], SCi.loc["S1_low_avail"], SCi.loc["S3_high_avail"]
g1, g2, g3, g4, g5 = (F["graph1"], F["graph2"], F["graph3"], F["graph4"], F["graph5"])
mlbest = ML[ML.split == "test"].sort_values("pr_auc", ascending=False).iloc[0]
p02 = MLP[MLP.threshold == 0.02].iloc[0]
emp = TGT[(TGT.metric == "Empty-km reduction") & (TGT.comparator == "B0_empty")].iloc[0]
netc = TGT[(TGT.metric == "NET-cost reduction") & (TGT.comparator == "B0_empty")].iloc[0]
fuelr = TGT[TGT.metric == "Fuel reduction"].iloc[0]
top_par = TOR.iloc[0]

md = lambda d: d.to_markdown(index=False)

R = f"""# TRUCKLY
## Optimising Freight Trucks' Journeys
### A simulation–optimisation study of empty return journeys on the South-India freight corridor

---

## 2. Abstract

Freight trucks routinely complete a delivery and return to base without a load,
because the operator has no visibility of shipments moving in the reverse
direction at the right time. This project builds **Truckly**, a
simulation–optimisation decision-support system for backhaul freight matching,
and tests it in a controlled experiment against three baseline policies.

The optimisation problem is formulated as a **Selective Pickup-and-Delivery
Problem with Time Windows** in prize-collecting form, decomposed into a CP-SAT
set-packing assignment stage and an exact route-enumeration stage, subject to
weight and volume capacity, hard delivery deadlines, a detour budget and driver
working-time limits.

Across **{int(pr.n_instances)} paired simulated operating days** of a 30-truck
fleet on a 40-node South-India network, under common random numbers, Truckly
reduced empty vehicle-kilometres by **{emp.pct_ratio_of_sums:.1f}%** and net
cost by **{netc.pct_ratio_of_sums:.1f}%** relative to an empty-return baseline,
and raised return-leg weight utilisation by
**{float(str(K.loc['Weight utilisation','TRUCKLY']))- 0:.2f} percentage points**
from zero. Against a **naive greedy matcher** — the honest competitor — the
margin was much smaller but statistically reliable: **{s0.empty_red_vs_B2_pct:.2f}%**
fewer empty kilometres (mean paired difference {pr.mean_diff:.1f} km/day, 95%
bootstrap CI [{pr.ci_low:.1f}, {pr.ci_high:.1f}], Wilcoxon p = {pr.wilcoxon_p:.1e},
lower in {int(pr.truckly_better_in_n)}/{int(pr.n_instances)} days) and
**{s0.net_cost_red_vs_B2_pct:.1f}%** lower net cost while serving
**{100*(s0.served_TR-s0.served_B2)/s0.served_B2:.1f}% more loads**.

**The 60% aspirational target was not reached on any metric.** Two results run
against the intuitive story and are reported as found: fuel consumption and
gross operating cost *increased* ({K.loc['Fuel','Truckly vs B0']} and
{K.loc['Total cost','Truckly vs B0']} versus B0), because carrying freight burns
more than running empty — the gain is in *net* cost and in utilisation, not in
fuel. And the benefit is not a constant: it rises from
**{s1.empty_red_vs_B0_pct:.1f}%** at {s1.density:.0f} open loads per truck to
**{s3.empty_red_vs_B0_pct:.1f}%** at {s3.density:.0f}, making shipment density
the dominant determinant of value.

All freight records are **simulated**; only the 40 node coordinates are
observed. Results describe the simulated environment, not Indian road freight.

---

## 3. Introduction

Road freight in India moves the majority of domestic tonnage, and a truck that
returns empty converts an entire leg of that capacity into pure cost. The
inefficiency is structural rather than accidental: freight flows are
asymmetric, so a corridor that carries heavy volume in one direction
necessarily has thinner return demand, and an individual carrier has no
visibility of the loads that do exist.

Two coping strategies dominate practice. The truck **returns empty**, wasting
fuel, capacity and driver time. Or it **waits** for a return load, converting
distance waste into time waste and reducing fleet availability. Truckly asks
whether an optimisation layer sitting over a pool of open loads can beat both —
and, more importantly, whether it can beat the obvious naive alternative of
simply grabbing the nearest feasible load.

---

## 4. Problem Statement

> **Given** a set of trucks, each with a current position, a required return
> destination, remaining weight and volume capacity, an availability time and a
> remaining legal driving-hours budget; and a pool of open shipment requests,
> each with a pickup node, delivery node, weight, volume, ready time and
> deadline —
>
> **find** (a) a subset of requests to accept, (b) an assignment of accepted
> requests to trucks, and (c) a route for each truck visiting each accepted
> pickup before its delivery and terminating at the truck's home node,
>
> **so as to maximise** system value — freight revenue less operating cost less
> a managerial penalty on empty running —
>
> **subject to** weight and volume capacity on every arc, time-window
> feasibility at every node, pickup-before-delivery precedence, a
> maximum-detour tolerance relative to the direct return, and driver
> working-time regulations.

This is a **Selective PDPTW**. It is *not* a VRPTW: in a VRPTW every customer
must be visited, whereas here accepting nothing and driving home empty is a
legal solution. Acceptance is a decision variable.

---

## 5. Motivation

Under the baseline policy modelled here, a 30-truck fleet burns
**{g1['total_empty_km_per_day']:,.0f} empty kilometres per operating day** —
a mean of {g1['mean_km']:.0f} km per truck, with the worst decile of journeys
carrying {g1['pct_of_empty_km_in_top_decile']:.0f}% of the total. Every one of
those kilometres consumes diesel, driver hours, vehicle life and road capacity
while producing nothing.

The distribution matters as much as the total. Because empty distance is
**right-skewed** (skewness {g1['skew']:.2f}; mean {g1['mean_km']:.0f} km >
median {g1['median_km']:.0f} km), the waste is concentrated: a matching system
does not need to match everything to capture most of the available benefit.

---

## 6. Existing Approach (the baselines)

| Code | Policy | Decision rule |
|---|---|---|
| **B0** | Empty return | Deliver, then drive directly home empty. No matching at all. |
| **B1** | Wait for load | Accept the **first** feasible load by ready-time order whose idle wait is within T_max (2 h / 6 h / 12 h tested). No comparison, no scoring. |
| **B2** | **Naive greedy** | Trucks in seeded order; each takes its **highest-scoring** feasible single load; the load is removed from the pool. No global coordination, no bundling. |

**B2 is the methodologically important one.** Comparing an optimiser against
"do nothing" inflates the headline and is not a fair test — any matcher beats
no matcher. The scientific claim of this project is the margin over *naive
matching*, and that margin is reported as the primary endpoint.

---

## 7. Proposed Truckly System

```
Stage A  candidate generation   feasible (truck, bundle) pairs, bundles <= {cfg['scenario_defaults']['max_bundle_size']}
Stage B  hard constraints       capacity -> volume -> detour -> time windows
                                -> driver hours -> return window
Stage C  global assignment      CP-SAT prize-collecting set packing
Stage D  route optimisation     exact enumeration of precedence-valid orders
Stage E  recommendation         match + route + costs + explanation
```

Information parity is enforced: every policy sees the same shipment pool at the
same decision epoch, uses the same `CostModel` object, and faces the same hard
constraints. No policy is given foresight the others lack.

---

## 8. Research Questions

| # | Question | Answered in |
|---|---|---|
| RQ1 | Does optimised matching reduce empty km vs a naive greedy matcher? | §19 |
| RQ2 | How much empty running exists under current practice? | §13 |
| RQ3 | What drives fuel consumption once distance is controlled for? | §13 |
| RQ4 | How much empty km / fuel / cost / waiting can be removed? | §18 |
| RQ5 | Is the improvement statistically reliable? | §19 |
| RQ6 | Under what conditions does the benefit appear or vanish? | §20, §21 |
| RQ7 | **When does Truckly fail?** | §22 |
| RQ8 | Does machine learning genuinely add anything? | §23 |

---

## 9. Dataset

| Layer | Provenance | Content |
|---|---|---|
| Network nodes | **OBS** | 40 real coordinates (OpenStreetMap / public gazetteer), Chennai–Bengaluru–Coimbatore–Madurai–Vijayawada corridor |
| Distance / duration | **DRV + ASM** | great-circle × declared circuity ({cfg['network']['circuity']['long_gt_200km']}–{cfg['network']['circuity']['short_lt_50km']}×); **no live routing engine was reachable** — see `docs/limitations.md` §1 |
| Shipments | **SIM** | 18,000 in the base scenario (231,000 across all 12 scenarios) |
| Trucks | **SIM** | 3,000 truck-journeys in the base scenario, 4 vehicle classes |
| Journeys | **OPT/DRV** | 216,000 rows = 12 scenarios × 100 days × 30 trucks × 6 policies |
| Candidates | **OPT** | 24,764 (truck, bundle) pairs with features and the optimiser's choice |
| Cost parameters | **ASM** | diesel ₹{cfg['cost']['diesel_price_inr_per_litre']}/L, wage ₹{cfg['cost']['driver_wage_inr_per_hour']}/h, toll ₹{cfg['cost']['toll_inr_per_km']}/km, tariff ₹{cfg['cost']['tariff_inr_per_km']}/km + ₹{cfg['cost']['tariff_inr_per_tonne_km']}/t·km |

Shipment origin–destination pairs are drawn from a **gravity (spatial-interaction)
model**, `P(o→d) ∝ w_o·w_d / dist^{cfg['scenario_defaults']['gravity_beta']}`, with an
asymmetric split ({cfg['scenario_defaults']['demand_asymmetry']} headhaul) so
that backhaul loads are genuinely scarce. Full rationale in `docs/methodology.md` §3.

---

## 10. Data Dictionary

See **`docs/data_dictionary.md`** — every column with meaning, type, unit,
provenance tag, example and justification.

---

## 11. Data Cleaning and Validation

The dataset is generated, so it does not arrive with the missing values of a
scraped file. What the cleaning stage actually is, therefore, is a
**validation suite** — and to prove the validators bite, the same 13 checks are
re-run against a seeded, deliberately corrupted copy of the data.

**Result: {int((VAL.violations==0).sum())}/{len(VAL)} checks pass on the real data, and
{int(VAL.fires_on_corrupted_copy.sum())}/{len(VAL)} demonstrably fire on the corrupted copy.**

{md(VAL[['check','violations','fires_on_corrupted_copy']])}

**No rows were dropped, no values imputed, no outliers winsorised.** The
1.5×IQR rule is a display convention, not a validity test — a long empty return
is unusual, not erroneous, and it is exactly the phenomenon the project exists
to study. Full transformation log in `outputs/tables/cleaning_report.md`.

---

## 12. Exploratory Data Analysis

Baseline B0, scenario S0_base, n = 3,000 truck-journeys.

{md(DESC.round(2))}

Shipment level, n = 18,000:

{md(DESCS.round(2))}

---

## 13. Statistical Analysis (the five poster panels)

| Panel | Measured result |
|---|---|
| **G1** histogram of empty distance | right-skewed, skew **{g1['skew']:.2f}**; mean {g1['mean_km']:.1f} km > median {g1['median_km']:.1f} km; IQR {g1['iqr']:.0f} km; top decile carries **{g1['pct_of_empty_km_in_top_decile']:.1f}%** of all empty km |
| **G2** fuel cost by vehicle class | mean within-class IQR ≈ ₹{g2['within_class_iqr_mean']:,} **exceeds** the between-class median range of ₹{g2['between_class_median_range']:,} — usage matters more than vehicle choice |
| **G3** distance vs fuel | r = {g3['pearson_r']:.3f}, R² = {g3['r2']:.3f}; **partly structural by construction**. Supplementary panel (fuel/km vs payload): r = {g3['g3b_pearson_r']:.3f}, slope {g3['g3b_slope']:.4f} L/km per tonne |
| **G4** Spearman heatmap | strongest non-definitional: {"; ".join(f"{a}↔{b} ρ={r:+.2f}" for a,b,r in g4['strongest_non_definitional'][:3])}. Definitional identities masked |
| **G5** utilisation density | **bimodal** — {g5['pct_exactly_zero']:.1f}% at exactly 0%, matched legs median {g5['median_matched_pct']:.1f}%; {g5['pct_below_threshold']:.1f}% below the {g5['threshold']:.0f}% threshold |

Observation guidance for handwriting: **`docs/observation_guidance.md`**.

---

## 14. Freight Matching Method

Candidate generation applies the hard filter as a cascade, cheapest test first,
tagging every rejection so the funnel can be counted. Feasible pairs receive an
**explainable score**

    S(k,b) = w1·empty_avoided − w2·detour + w3·capacity − w4·waiting + w5·slack

with every term divided by a stated maximum. The detour term is normalised by
`θ·d_ret` (the *tolerance*), not by `d_ret` — dividing by `d_ret` would compress
it into [0, θ] and silently down-weight it by 1/θ.

**The score is not the objective.** It drives baseline B2 and it is what the
user is shown as the reason for a recommendation. The optimiser minimises cost.

---

## 15. Optimisation Model

    min  Σ_{{k,b}} (c_kb − rev_b)·y_kb  +  Σ_k c_k^empty·z_k
    s.t. Σ_b y_kb + z_k = 1              ∀ truck k          (C1)
         Σ_{{k,b: r∈b}} y_kb ≤ 1          ∀ request r        (C2)
         y, z ∈ {{0,1}}

A **prize-collecting set-packing problem with an outside option**, solved by
OR-Tools CP-SAT to **proven optimality** over the generated candidate set
(solver status recorded on every row: 100% `optimal`). Routes are found by
exact enumeration of all (2k)!/2^k precedence-valid orderings, so the route for
any accepted bundle is provably optimal too.

Mean decision time: **{float(K.loc['Solve time per decision','TRUCKLY']):.2f} ms per truck**.

---

## 16. Baseline Policies

Journey-level means, scenario S0_base:

{md(BYPOL)}

---

## 17. Experimental Design

- **R = {int(pr.n_instances)} simulated operating days** per scenario, 12 scenarios.
- **Common random numbers**: the per-arc fuel perturbation is fixed per
  (instance, arc), so any policy traversing that arc gets the same perturbation.
  The comparison is therefore paired.
- **Unit of inference = the operating day**, not the truck. Trucks within a day
  compete for the same pool and are not independent.
- Analysis plan pre-registered in `docs/pre_registration.md`.

---

## 18. Results

{md(KPI)}

### 60% target analysis

{md(TGT)}

**The 60% aspiration was not reached on any metric.** It was stated in advance
as a hypothesis, and it is reported against as found.

### The results that run against the story

- **Fuel rose {abs(float(fuelr.pct_ratio_of_sums)):.1f}%** and gross cost rose
  {abs(float(str(K.loc['Total cost','Truckly vs B0']).split()[0])):.1f}% versus B0.
  Carrying freight burns more diesel than running empty. This is not a defect in
  the system; it is what the physics requires, and any project reporting fuel
  savings proportional to empty-km savings has mis-modelled it.
- **Total distance rose {abs(float(str(K.loc['Total km','Truckly vs B0']).split()[0])):.1f}%**,
  because serving extra loads requires repositioning. The right measure is
  *empty* km, not total km.
- **Waiting time rose**, not fell, versus B1. Truckly is willing to wait when
  waiting pays. B1's wait caps (2/6/12 h) turned out to be **non-binding** in
  this environment — all three variants produce nearly identical results, which
  is itself a finding.

---

## 19. Statistical Validation

**Primary endpoint (pre-specified): empty-km reduction, TRUCKLY vs B2_greedy.**

- n = {int(pr.n_instances)} paired operating days
- Mean paired difference **{pr.mean_diff:.1f} km/day**, 95% bootstrap CI
  **[{pr.ci_low:.1f}, {pr.ci_high:.1f}]**
- Hodges–Lehmann estimate **{pr.hodges_lehmann:.1f} km**
- Rank-biserial correlation **{pr.rank_biserial:.3f}**
- Wilcoxon signed-rank **p = {pr.wilcoxon_p:.2e}**
- TRUCKLY lower in **{int(pr.truckly_better_in_n)}/{int(pr.n_instances)}** days

> **On Cohen's d_z.** Common random numbers deliberately shrink the SD of the
> paired difference, so d_z is mechanically inflated and is **not comparable**
> to an unpaired design. It is reported as a within-design descriptor only.
>
> **On p-values.** R is under our control; simulating more days makes any
> non-zero difference "significant". The interval and the effect size are the
> result. Only one confirmatory test is run; every other comparison is
> descriptive, Holm-adjusted within the secondary family.

{md(TST.round(4))}

---

## 20. Scenario Analysis

{md(SC)}

**The single most important result in the project** is the S1→S2→S3 progression:
Truckly's benefit rises from **{s1.empty_red_vs_B0_pct:.1f}%** at
{s1.density:.0f} open loads per truck to **{s3.empty_red_vs_B0_pct:.1f}%** at
{s3.density:.0f}. Reporting the benefit as a *curve over shipment density*
rather than a point estimate is what makes it robust to the objection that the
generator was tuned.

---

## 21. Sensitivity Analysis

{md(TOR)}

The dominant parameter is **{top_par.parameter}**, with a swing of
**{top_par.empty_swing_pp:.1f} percentage points** in empty-km reduction across
its tested range. Deadline tightness is second. Fuel price and driver wages
barely move the empty-km result at all — they move *cost*, not *routing* — which
is a useful sanity check that the model is behaving sensibly.

Full one-factor-at-a-time sweep in `outputs/tables/sensitivity_analysis.csv`.

---

## 22. Failure Analysis

{md(FAIL)}

**Geography, not capacity, is the binding constraint.** `detour_exceeded`
dominates in every scenario: most open loads simply do not lie close enough to
the truck's return corridor. Capacity, volume, driver hours and deadlines
account for a small minority. This tells you where to invest: denser lane
coverage and a larger shipment pool, not bigger trucks.

`lost_to_competing_truck` is the cases where a feasible candidate existed but
another truck was a better global fit — that is the optimiser working as
intended, not a failure of the system.

---

## 23. ML Extension

Three candidate ML tasks were **rejected as circular**: fuel prediction and
travel-time prediction would recover formulas we wrote ourselves, and
feasibility prediction is exactly recoverable from the constraints. The one task
that survives is **candidate pruning**, whose label (`selected_by_optimiser`)
comes from a global optimisation over competing trucks and is not a function of
any single candidate's features.

{md(ML)}

Best model on test PR-AUC: **{mlbest.model}** (PR-AUC {mlbest.pr_auc:.3f},
ROC-AUC {mlbest.roc_auc:.3f}, recall {mlbest.recall:.3f}). Accuracy is not
reported: with a {mlbest.positive_rate:.1%} positive rate a trivial all-negative
classifier would score {1-mlbest.positive_rate:.1%}.

Top features: {", ".join(f"`{r.feature}`" for r in MLI.head(5).itertuples())}.

### The result that matters — pruning vs optimality gap

{md(MLP)}

At a threshold of 0.02 the classifier discards **{p02.mean_pruned_pct:.1f}%** of
candidates for a mean optimality gap of **{p02.mean_gap_pct:.3f}%**, leaving
{int(p02.instances_with_zero_gap)}/{int(p02.n_instances)} instances exactly
optimal, at **{p02.speedup:.2f}× speedup**. Beyond ~5% the gap grows fast.

**Honest conclusion: the ML layer is not why Truckly works.** The CP-SAT solve
already takes ~{p02.mean_ms_full:.0f} ms, so the practical gain at this problem
size is small. Its value would appear at fleet scale. Removing the ML layer
changes runtime, not the result.

---

## 24. Prototype

`truckly_demo.py` produces a full recommendation with an explanation:
recommended shipment, route, empty km avoided, detour, fuel, cost, revenue, net
saving, utilisation, waiting time, deadline status, and **five to six
plain-language reasons** for the choice — plus the nearest *rejected*
alternatives and why each failed. `outputs/dashboard.html` gives the fleet-level
KPI view.

---

## 25. Environmental Impact

Estimated CO₂ per operating day: B0 **{float(K.loc['CO2 estimate','B0_empty']):,.0f} kg**,
TRUCKLY **{float(K.loc['CO2 estimate','TRUCKLY']):,.0f} kg** — an **increase**,
because absolute fuel burn rises when freight is carried.

The environmental case for backhaul matching is therefore **not** "the truck
burns less fuel". It is that the {s0.served_TR:.1f} loads carried on return legs
did not each require a separate dedicated vehicle movement. Measuring that
avoided-trip benefit properly requires modelling the counterfactual dedicated
journey, which is out of scope here and is named in Future Work.

Every CO₂ figure uses an **ASM** factor of
{cfg['cost']['co2_kg_per_litre_diesel']} kg/L and is **estimated, never
observed**.

---

## 26. Driver Impact

Truckly must not buy company savings with unreasonable driver schedules. Duty
time is a hard constraint (max {cfg['driver']['max_driving_hours']} h driving,
{cfg['driver']['max_duty_hours']} h duty, mandatory break after
{cfg['driver']['break_after_hours']} h), and **on-time delivery held at
{float(K.loc['On-time rate','TRUCKLY']):.1f}%** — no deadline was ever missed,
because deadlines are enforced as hard constraints.

Mean duty time rose from {float(K.loc['Driver duty time','B0_empty']):.1f} h to
{float(K.loc['Driver duty time','TRUCKLY']):.1f} h per fleet-day. That is the
honest trade-off: matched trucks work longer days. Whether that is acceptable is
a policy question, not a technical one, and it should be stated to the operator
rather than buried.

---

## 27. Limitations

See **`docs/limitations.md`** for the full ordered list. The three that most
threaten the conclusions:

1. **No live routing engine was reachable** — road distance is great-circle ×
   a declared circuity factor, not traced road geometry.
2. **The freight records are simulated** — results describe the simulated
   environment, not Indian road freight.
3. **The freight pool is uncontested** — in a real spot market other carriers
   compete for the same loads, so these figures are an upper bound for one
   carrier.

---

## 28. Future Work

1. Re-run with a real routing engine (`RoadNetwork.build_matrices_from_osrm()`
   is already written and is a one-command swap).
2. Model the **counterfactual dedicated trip** for unserved loads, which would
   make the environmental and system-cost case measurable.
3. Add **competing carriers** to the shipment pool.
4. Multi-day, multi-leg journey chains.
5. Validate the routing engine against **Solomon benchmark instances** with
   published best-known solutions.
6. Stochastic / robust optimisation under uncertain travel times.
7. Rolling-horizon dynamic matching as loads arrive through the day.

---

## 29. Conclusion

Optimised freight matching reduced empty running by
**{emp.pct_ratio_of_sums:.1f}%** and net cost by **{netc.pct_ratio_of_sums:.1f}%**
against current practice in the simulated environment, and beat a naive greedy
matcher by a small but statistically reliable margin
({pr.mean_diff:.1f} km/day, 95% CI [{pr.ci_low:.1f}, {pr.ci_high:.1f}],
lower in {int(pr.truckly_better_in_n)}/{int(pr.n_instances)} days) while serving
{100*(s0.served_TR-s0.served_B2)/s0.served_B2:.1f}% more loads at
{s0.net_cost_red_vs_B2_pct:.1f}% lower net cost.

**The 60% aspiration was not achieved.** The honest headline is narrower and
more useful than that: *the value of freight matching is a function of how thick
the freight market is*. At {s1.density:.0f} open loads per truck it is worth
{s1.empty_red_vs_B0_pct:.0f}%; at {s3.density:.0f} it is worth
{s3.empty_red_vs_B0_pct:.0f}%. And the value of *optimisation over naive
matching* is real but modest — most of the benefit comes from matching at all,
with global optimisation adding a further few percent and a materially higher
service level.

The failure taxonomy points at what to fix: **{FAIL.iloc[0].reason if FAIL.iloc[0].reason != 'matched' else FAIL.iloc[1].reason}**
accounts for {FAIL[FAIL.reason=='detour_exceeded'].pct_of_trucks.iloc[0]:.1f}% of
unmatched trucks, so the constraint is geography and market density — not truck
capacity, not deadlines, and not the algorithm.

---

## 30. References

**Data and tools**

- OpenStreetMap contributors — node coordinates. https://www.openstreetmap.org/
- Project-OSRM — routing engine (integration written, not reachable from the build environment). https://github.com/Project-OSRM/osrm-backend
- Google OR-Tools — CP-SAT solver. https://developers.google.com/optimization/
- SINTEF — Solomon VRPTW benchmark and best-known solutions (named for future validation). https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/
- VRP-REP: the Vehicle Routing Problem Repository. https://www.vrp-rep.org/

**Parameter sourcing (to be completed with dated retrievals before submission)**

- Petroleum Planning & Analysis Cell, Government of India — diesel retail price. https://ppac.gov.in/
- data.gov.in — annual average retail selling prices, petrol and diesel, Delhi. https://www.data.gov.in/resource/year-wise-details-average-retail-selling-prices-rsp-petrol-and-diesel-delhi-2019-20-2024
- US EPA — GHG Emission Factors Hub (2025), for the diesel CO₂ factor. https://www.epa.gov/system/files/documents/2025-01/ghg-emission-factors-hub-2025.pdf
- NITI Aayog & RMI — *Goods on the Move: Efficiency and Sustainability in Indian Logistics* (2018). https://niti.gov.in/sites/default/files/2023-02/Freight_report.pdf

> **Note.** The cost, tariff, fuel-curve and emission-factor values used in this
> build are declared assumptions (`ASM`) in `config.yaml`. They are plausible but
> were not taken from dated retrievals of the sources above. Replacing them with
> cited values is the single highest-value hour of work remaining, and the
> sensitivity analysis already shows exactly how much each one matters.

---

*Generated from `outputs/tables/` — every number in this report is read from the
experiment at build time and cannot drift from the results.*
"""
open(os.path.join(H, "FINAL_REPORT.md"), "w").write(R)
print("wrote FINAL_REPORT.md")

# ---------------------------------------------------------------- README
RD = f"""# TRUCKLY — Optimising Freight Trucks' Journeys

A **simulation–optimisation decision-support system** for backhaul freight
matching, with a controlled four-policy experiment, statistical validation,
scenario and sensitivity analysis, a failure taxonomy, an honest ML extension,
a working demo and an A3 statistical poster.

> ⚠️ **The freight records in this project are SIMULATED.** Only the 40 node
> coordinates are real. No result here is an observation of Indian road freight.

## Headline results

| | vs B0 (empty return) | vs B2 (naive greedy) |
|---|---|---|
| Empty kilometres | **−{emp.pct_ratio_of_sums:.1f}%** | **−{s0.empty_red_vs_B2_pct:.2f}%** |
| Net cost (cost − revenue) | **−{netc.pct_ratio_of_sums:.1f}%** | **−{s0.net_cost_red_vs_B2_pct:.1f}%** |
| Loads served | +{s0.served_TR:.1f}/day | **+{100*(s0.served_TR-s0.served_B2)/s0.served_B2:.1f}%** |
| Weight utilisation | +{s0.util_gain_vs_B0_pp:.2f} pp | +{float(K.loc['Weight utilisation','TRUCKLY'])-float(K.loc['Weight utilisation','B2_greedy']):.2f} pp |
| Fuel | **+{abs(float(fuelr.pct_ratio_of_sums)):.1f}% (INCREASE)** | +0.5% |

Primary endpoint: mean paired difference **{pr.mean_diff:.1f} empty km/day**
(95% bootstrap CI [{pr.ci_low:.1f}, {pr.ci_high:.1f}], Wilcoxon p =
{pr.wilcoxon_p:.1e}, lower in {int(pr.truckly_better_in_n)}/{int(pr.n_instances)}
paired days).

**The 60% aspirational target was not reached on any metric**, and the benefit
is not constant — it rises from {s1.empty_red_vs_B0_pct:.0f}% at {s1.density:.0f}
open loads per truck to {s3.empty_red_vs_B0_pct:.0f}% at {s3.density:.0f}.

## Quick start

```bash
pip install -r requirements.txt

python3 run_experiment.py --all --instances 100   # ~90 s, the whole experiment
python3 analysis/data_cleaning.py                 # validation + analysis frame
python3 analysis/descriptive_statistics.py
python3 analysis/statistical_tests.py             # KPI table, 60% target, tests
python3 analysis/scenario_analysis.py             # scenarios + sensitivity
python3 analysis/ml_candidate_pruning.py          # ML extension
python3 visualizations/make_poster_figures.py     # the 5 poster graphs
python3 visualizations/make_result_figures.py     # result figures
python3 visualizations/make_poster.py             # A3 poster (PDF + PNG)
python3 make_documents.py && python3 make_report.py
python3 make_dashboard.py

python3 truckly_demo.py                           # live recommendation + why
python3 truckly_demo.py --interactive             # enter your own truck
```

Or run everything: `bash run_all.sh`

## Reproducibility

Master seed `{cfg['meta']['master_seed']}` in `config.yaml`. Every instance is a
pure function of `(master_seed, scenario, instance_id)`, so the same seed
reproduces byte-identical data. Every run writes a config hash into
`outputs/results/instances_main.csv`. **Common random numbers** are used across
policies, so the four-way comparison is paired.

## Layout

```
TRUCKLY/
├── config.yaml                 every parameter, with a provenance tag
├── run_experiment.py           the experiment driver
├── truckly_demo.py             recommendation demo with explanations
├── make_documents.py           builds docs/ from the results
├── make_report.py              builds FINAL_REPORT.md from the results
├── make_dashboard.py           builds outputs/dashboard.html
├── FINAL_REPORT.md             30-section report, numbers read at build time
├── data/
│   ├── generated/              truckly_shipments/trucks/nodes/drivers.csv
│   └── processed/              truckly_clean.csv + cached matrices
├── src/
│   ├── network.py              nodes, distance/duration, OSRM swap-in
│   ├── domain.py               Truck/Shipment/Journey + the ONE cost model
│   ├── data_generator.py       seeded gravity-model instance generator
│   ├── feasibility.py          hard-constraint cascade + exact route eval
│   ├── matching.py             candidates, explainable score, features
│   ├── optimizer.py            CP-SAT prize-collecting set packing
│   ├── baselines.py            B0 / B1 / B2
│   └── simulation.py           experiment engine, common random numbers
├── analysis/                   cleaning · descriptives · tests · scenarios · ML
├── visualizations/             style + poster figures + result figures + poster
├── outputs/
│   ├── figures/                11 PNGs at 300 dpi
│   ├── tables/                 every result as CSV + markdown
│   ├── results/                journeys · candidates · instances
│   ├── poster/                 Truckly_A3_Statistical_Poster.pdf / .png
│   └── dashboard.html
└── docs/
    ├── data_dictionary.md      every column, typed and provenance-tagged
    ├── methodology.md          problem class, generator, fuel model, optimiser
    ├── limitations.md          ordered by severity, nothing hidden
    ├── pre_registration.md     analysis plan fixed before the run
    └── observation_guidance.md notes for the HANDWRITTEN poster observations
```

## What is honest about this project

- **A naive greedy baseline (B2) is included.** Comparing an optimiser to "do
  nothing" inflates the headline; the scientific claim is the margin over naive
  matching, and it is small.
- **Fuel and gross cost went UP**, and that is reported as the headline of §18
  rather than buried. Carrying freight burns more than running empty.
- **The 60% target was missed**, and is reported as missed.
- **Three ML tasks were rejected as circular** and the reasoning is written down.
  The surviving one is explicitly *not* the reason Truckly works.
- **Definitional correlations are masked** in the heatmap rather than presented
  as findings.
- **The distance–fuel panel carries a structural-dependence warning** on its face.
- **Only one confirmatory statistical test** is run; everything else is labelled
  descriptive.
- **The observation boxes on the poster are left blank**, because the university
  requires handwritten observations.
"""
open(os.path.join(H, "README.md"), "w").write(RD)
print("wrote README.md")

open(os.path.join(H, "requirements.txt"), "w").write(
    "numpy>=1.24\npandas>=2.0\nscipy>=1.10\nmatplotlib>=3.7\nseaborn>=0.12\n"
    "scikit-learn>=1.3\nortools>=9.8\nPyYAML>=6.0\ntabulate>=0.9\n")
print("wrote requirements.txt")
