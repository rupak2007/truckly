#!/usr/bin/env python3
"""TRUCKLY — generates every written deliverable from the ACTUAL results.

Nothing here is hand-typed prose with numbers in it. Every figure quoted is
read out of outputs/tables at build time, so the documents cannot drift away
from the experiment.
"""
from __future__ import annotations
import os, json
import numpy as np
import pandas as pd
import yaml

H = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(H, "outputs", "tables")
DOC = os.path.join(H, "docs")
os.makedirs(DOC, exist_ok=True)

cfg = yaml.safe_load(open(os.path.join(H, "config.yaml")))
F = json.load(open(os.path.join(TAB, "poster_findings.json")))
KPI = pd.read_csv(os.path.join(TAB, "kpi_results.csv")).set_index("KPI")
TGT = pd.read_csv(os.path.join(TAB, "target_60pct_analysis.csv"))
TST = pd.read_csv(os.path.join(TAB, "statistical_tests.csv"))
SC = pd.read_csv(os.path.join(TAB, "scenario_analysis.csv")).set_index("scenario")
TOR = pd.read_csv(os.path.join(TAB, "sensitivity_tornado.csv"))
FAIL = pd.read_csv(os.path.join(TAB, "failure_taxonomy.csv"))
VAL = pd.read_csv(os.path.join(TAB, "validation_checks.csv"))
ML = pd.read_csv(os.path.join(TAB, "ml_model_comparison.csv"))
MLP = pd.read_csv(os.path.join(TAB, "ml_pruning_curve.csv"))
DESC = pd.read_csv(os.path.join(TAB, "descriptive_A_journey_level_BASELINE_B0.csv"))
SENS = pd.read_csv(os.path.join(TAB, "sensitivity_analysis.csv"))

pr = TST.iloc[0]
s0, s1, s3 = SC.loc["S0_base"], SC.loc["S1_low_avail"], SC.loc["S3_high_avail"]
g1, g2, g3, g4, g5 = (F["graph1"], F["graph2"], F["graph3"], F["graph4"], F["graph5"])
mlbest = ML[ML.split == "test"].sort_values("pr_auc", ascending=False).iloc[0]
prune = MLP[MLP.threshold == 0.02].iloc[0]


def w(name, text, folder=DOC):
    open(os.path.join(folder, name), "w").write(text)
    print("  wrote", os.path.join(os.path.basename(folder), name))


# =====================================================================
# 1. DATA DICTIONARY
# =====================================================================
ROWS = [
    ("truckly_nodes.csv", "node_id", "Network node identifier", "str", "—", "OBS", "CHN", "Primary key for every location"),
    ("truckly_nodes.csv", "name", "Place name", "str", "—", "OBS", "Chennai", "Human-readable label on maps and in the demo"),
    ("truckly_nodes.csv", "lat / lon", "Coordinates", "float", "degrees", "OBS", "13.0827 / 80.2707", "Real coordinates from OpenStreetMap / public gazetteer; the basis of every distance"),
    ("truckly_nodes.csv", "node_role", "hub / industrial / customer / port", "str", "—", "ASM", "hub", "Shapes the demand-weighting of the gravity model"),
    ("truckly_nodes.csv", "demand_weight_out / _in", "Relative propensity to originate / receive freight", "float", "—", "ASM", "1.00", "Gravity-model mass terms; encode corridor asymmetry"),
    ("truckly_nodes.csv", "region_class", "source or sink region", "str", "—", "ASM", "source", "Determines headhaul vs backhaul direction"),
    ("truckly_shipments.csv", "shipment_id", "Shipment identifier", "str", "—", "SIM", "S0007_042", "Primary key"),
    ("truckly_shipments.csv", "origin_node_id / dest_node_id", "Pickup / delivery node", "str", "—", "SIM", "CHN / BLR", "Drawn from the gravity OD model over real nodes"),
    ("truckly_shipments.csv", "pickup_lat/lon, delivery_lat/lon", "Denormalised coordinates", "float", "degrees", "OBS", "13.0827", "Convenience for mapping without a join"),
    ("truckly_shipments.csv", "shipment_weight_kg", "Gross weight", "float", "kg", "SIM", "2,327.8", "Binds the weight-capacity constraint; lognormal by design"),
    ("truckly_shipments.csv", "shipment_volume_m3", "Cubic volume", "float", "m³", "SIM", "9.43", "Second capacity dimension — catches cube-out on light freight"),
    ("truckly_shipments.csv", "pickup_ready_time_hr", "Earliest pickup", "float", "hours from t0", "SIM", "6.42", "Time-window lower bound; source of waiting time"),
    ("truckly_shipments.csv", "delivery_deadline_hr", "Latest delivery", "float", "hours from t0", "SIM", "17.10", "Time-window upper bound; hard constraint"),
    ("truckly_shipments.csv", "service_time_pickup_min / _delivery_min", "Loading / unloading time", "float", "minutes", "SIM", "45.0 / 40.0", "Consumes duty time and affects feasibility"),
    ("truckly_shipments.csv", "direct_distance_km / direct_duration_min", "Origin→destination road distance / duration", "float", "km / min", "DRV", "342.4 / 373.5", "Loaded-leg length; input to revenue and to the score"),
    ("truckly_shipments.csv", "revenue_inr", "Freight tariff earned if served", "float", "INR", "SIM/ASM", "5,980", "The PRIZE in the prize-collecting objective"),
    ("truckly_trucks.csv", "truck_id", "Truck identifier", "str", "—", "SIM", "T0007_015", "Primary key"),
    ("truckly_trucks.csv", "truck_type", "Vehicle class", "str", "—", "SIM", "RIGID_16T", "Selects capacity and the fuel curve"),
    ("truckly_trucks.csv", "truck_capacity_kg / _m3", "Payload / deck capacity", "float", "kg / m³", "ASM", "16,000 / 52", "Hard capacity constraints"),
    ("truckly_trucks.csv", "base_fuel_l_per_100km", "Unladen consumption β₀", "float", "L/100km", "ASM", "26.0", "Intercept of the fuel model"),
    ("truckly_trucks.csv", "load_fuel_coeff", "Marginal consumption per tonne β₁", "float", "L/100km/t", "ASM", "0.72", "Makes an empty km cheaper than a loaded one but not free"),
    ("truckly_trucks.csv", "truck_current_node", "Where the truck became free", "str", "—", "SIM", "BLR", "Route origin"),
    ("truckly_trucks.csv", "home_node", "Where it must return to", "str", "—", "SIM", "CHN", "Route terminus"),
    ("truckly_trucks.csv", "available_from_hr", "When the truck becomes free", "float", "hours from t0", "SIM", "10.4", "Decision epoch"),
    ("truckly_trucks.csv", "must_return_by_hr", "Latest acceptable arrival home", "float", "hours from t0", "SIM", "19.8", "Duty-time budget"),
    ("truckly_trucks.csv", "driving_hours_used", "Hours already driven this shift", "float", "hours", "SIM", "3.1", "Reduces the remaining legal driving budget"),
    ("truckly_trucks.csv", "direct_return_km / _min", "Empty return distance / duration", "float", "km / min", "DRV", "342.4 / 373.5", "The B0 baseline, and the base of the detour budget"),
    ("journeys", "policy", "B0_empty / B1_wait_* / B2_greedy / TRUCKLY", "str", "—", "OPT", "TRUCKLY", "Row dimension that makes the design paired and long-format"),
    ("journeys", "matched_shipment_ids", "Accepted requests", "str", "—", "OPT", "S0007_042", "Empty when the truck ran home empty"),
    ("journeys", "route_node_sequence", "Ordered node visits", "str", "—", "OPT", "BLR>HSR>CHN>CHN", "Executed route"),
    ("journeys", "total_distance_km", "Distance over the whole route", "float", "km", "DRV", "398.2", "Denominator of distance utilisation"),
    ("journeys", "loaded_distance_km", "Distance on arcs with payload > 0", "float", "km", "DRV", "342.4", "Productive distance"),
    ("journeys", "empty_distance_km", "total − loaded", "float", "km", "DRV", "55.8", "**PRIMARY KPI**"),
    ("journeys", "detour_distance_km", "total − direct return", "float", "km", "DRV", "55.8", "What the operator actually feels; bounded by the detour budget"),
    ("journeys", "payload_tonne_km", "Σ (payload × arc length)", "float", "t·km", "DRV", "5,412", "Freight productivity numerator"),
    ("journeys", "capacity_tonne_km", "Σ (capacity × arc length)", "float", "t·km", "DRV", "6,371", "Utilisation denominator"),
    ("journeys", "utilisation_weight_pct", "payload_t·km ÷ capacity_t·km × 100", "float", "%", "DRV", "8.2", "Preferred utilisation definition (return leg only)"),
    ("journeys", "utilisation_distance_pct", "loaded_km ÷ total_km × 100", "float", "%", "DRV", "29.6", "Answers a different question; reported alongside, never instead"),
    ("journeys", "driving_time_hr / service_time_hr / waiting_time_hr", "Time components", "float", "hours", "DRV", "6.5 / 1.4 / 0.2", "Driver-hours constraints and the waiting-cost term"),
    ("journeys", "duty_time_hr", "driving + service + waiting", "float", "hours", "DRV", "8.1", "Bound by max_duty_hours"),
    ("journeys", "fuel_litres", "Load-dependent, noise-perturbed consumption", "float", "L", "DRV", "112.4", "See §5.7 of the methodology"),
    ("journeys", "fuel_cost_inr / driver_cost_inr / toll_cost_inr", "Cost components", "float", "INR", "DRV", "10,116", "Sum to variable_cost_inr"),
    ("journeys", "variable_cost_inr / fixed_cost_inr / total_cost_inr", "Cost roll-up", "float", "INR", "DRV", "13,400", "total = variable + fixed"),
    ("journeys", "revenue_inr", "Tariff earned on matched loads", "float", "INR", "DRV", "5,980", "Zero for an empty return"),
    ("journeys", "net_cost_inr", "total_cost − revenue", "float", "INR", "DRV", "7,420", "The business-relevant cost figure"),
    ("journeys", "co2_kg", "fuel × emission factor", "float", "kg", "DRV", "301.2", "**ESTIMATED**, never observed"),
    ("journeys", "avg_payload_tonnes", "payload_t·km ÷ loaded_km", "float", "t", "DRV", "2.3", "Colour variable for poster Graph 3"),
    ("journeys", "match_score", "Explainable score S(k,b)", "float", "—", "OPT", "+1.280", "Diagnostic + user-facing explanation; NaN when unmatched"),
    ("journeys", "unmatched_reason", "Why the truck ran empty", "str", "—", "OPT", "detour_exceeded", "**Drives the failure taxonomy**"),
    ("journeys", "solver_status / solve_time_ms", "CP-SAT status and runtime", "str / float", "— / ms", "OPT", "optimal / 0.58", "Evidence for the operational-feasibility claim"),
    ("candidates", "selected_by_optimiser", "Did CP-SAT choose this pair", "int", "0/1", "OPT", "1", "**ML target variable**"),
    ("candidates", "competing_trucks", "How many trucks this bundle is feasible for", "int", "—", "DRV", "4", "Global-competition feature — the non-circular signal"),
    ("candidates", "cost_rank_within_truck", "Rank of c_kb among this truck's candidates", "int", "—", "DRV", "1", "Relative-quality feature"),
    ("candidates", "bearing_deviation_deg", "Angle between shipment and return direction", "float", "degrees", "DRV", "12.4", "Geometric alignment feature"),
    ("instances", "n_shipments_offered", "Open loads in the pool that day", "int", "—", "SIM", "180", "Service-level denominator; identical across policies by construction"),
    ("instances", "seed / config_hash", "Reproducibility manifest", "int / str", "—", "SIM", "…", "Same seed ⇒ byte-identical instance"),
]
dd = pd.DataFrame(ROWS, columns=["Table", "Column", "Meaning", "Type", "Unit",
                                 "Provenance", "Example", "Why it is needed"])
w("data_dictionary.md",
  "# TRUCKLY — Data Dictionary\n\n"
  "## Provenance tags\n\n"
  "| Tag | Meaning |\n|---|---|\n"
  "| `OBS` | Observed / external real-world data |\n"
  "| `BEN` | Published benchmark instance |\n"
  "| `SIM` | Generated by the Truckly synthetic layer |\n"
  "| `DRV` | Derived deterministically from other columns |\n"
  "| `ASM` | Declared assumption, no external source obtained |\n"
  "| `OPT` | Produced by the optimiser or the simulation |\n\n"
  "> **The only `OBS` data in this project is the 40 node coordinates.** "
  "Everything describing freight is `SIM`, `DRV` or `ASM`. No row of this "
  "dataset is an observation of real Indian freight.\n\n"
  "## Columns\n\n" + dd.to_markdown(index=False) + "\n")

# =====================================================================
# 2. LIMITATIONS
# =====================================================================
w("limitations.md", f"""# TRUCKLY — Limitations

Ordered by how much they threaten the conclusions. Nothing here is hidden in a
footnote; the first three are severe enough that the headline results must
always be quoted with them.

## 1. No live routing engine was reachable — road distance is modelled, not measured

The build environment had no network route to a routing service (a connection
attempt to the OSRM demo server returned no HTTP status at all). Rather than
fabricate road distances and label them observed, distance is computed as

    road_km = great_circle_km x circuity_factor

with circuity declared in `config.yaml` as {cfg['network']['circuity']['short_lt_50km']}x
below 50 km, {cfg['network']['circuity']['mid_50_200km']}x for 50-200 km and
{cfg['network']['circuity']['long_gt_200km']}x above 200 km, and truck speeds of
{cfg['network']['speeds_kmh']['short_lt_50km']}-{cfg['network']['speeds_kmh']['long_gt_200km']} km/h.
These are **ASM**, not **OBS**.

*Consequence:* absolute kilometre and fuel figures are approximations. Relative
comparisons between policies are far more robust, because every policy uses the
same distance matrix — the error is common-mode and largely cancels in the
paired difference.

*Fix:* `RoadNetwork.build_matrices_from_osrm()` in `src/network.py` is a
drop-in replacement that writes the same cache files. Run it once where network
access exists; no other code changes.

## 2. The freight records are simulated

There are no real carrier records here. Shipments, trucks, weights, time
windows and journeys are all generated. The generator is calibrated to a
plausible structure (real geography, a gravity OD model, asymmetric
headhaul/backhaul demand, lognormal weights) but it is a *model*, and every
result is conditional on it.

*Mitigation:* the headline result is reported as a **curve over shipment
density** rather than a point estimate (§Scenario analysis), which is far
harder to dismiss as generator tuning. The dominant parameter is stated openly.

## 3. Results are conditional on the cost and tariff assumptions

Diesel at Rs {cfg['cost']['diesel_price_inr_per_litre']}/L, driver wage Rs
{cfg['cost']['driver_wage_inr_per_hour']}/h, toll Rs {cfg['cost']['toll_inr_per_km']}/km,
freight tariff Rs {cfg['cost']['tariff_inr_per_km']}/km + Rs
{cfg['cost']['tariff_inr_per_tonne_km']}/t-km, and an empty-running management
penalty of Rs {cfg['cost']['empty_km_penalty_inr_per_km']}/km are all **ASM**.
The sensitivity analysis sweeps each; the tornado shows fuel price and wages
barely move the empty-km result (they move cost, not routing), while the tariff
strongly moves the net-cost result.

## 4. Single-leg model

Only the return leg is simulated. The outbound leg that put the truck where it
is, and any onward multi-day chain, are out of scope. Trucks whose direct
return exceeds {0.65*cfg['driver']['max_driving_hours']:.1f} h of driving are
excluded by the generator because they could not complete the leg in one legal
day. **Utilisation figures are therefore return-leg utilisation, not round-trip
utilisation**, and are not comparable to industry round-trip statistics.

## 5. The freight pool is uncontested

Every open load is available to this fleet alone. In reality a spot market is
contested by many carriers, so the achievable match rate would be lower. This
is the single largest reason to treat the reported benefits as an upper bound
on what one carrier could capture.

## 6. Decomposition is a heuristic

Assignment (CP-SAT) and routing (exact enumeration over precedence-valid
orders) are solved in two stages. The assignment stage is solved to **proven
optimality over the generated candidate set** — but the candidate set itself is
capped at bundles of size <= {cfg['scenario_defaults']['max_bundle_size']}. A
monolithic model could in principle find solutions this decomposition misses.

## 7. CO2 is estimated, not measured

Emissions are `fuel_litres x {cfg['cost']['co2_kg_per_litre_diesel']}` kg/L,
an **ASM** factor. Before submission this should be replaced with a cited
factor from a national inventory (e.g. DESNZ/Defra or US EPA) and the citation
recorded. No CO2 number in this project is an observation.

## 8. No live traffic, cancellations, breakdowns or rejections

Travel times are free-flow. Shipments never cancel, trucks never break down,
shippers never reject a carrier. Each of these would reduce realised benefit.

## 9. Driver rules are declared, not statutory

`max_driving_hours = {cfg['driver']['max_driving_hours']}`,
`max_duty_hours = {cfg['driver']['max_duty_hours']}`,
break after {cfg['driver']['break_after_hours']} h are **ASM**. They are
plausible, and they are enforced as hard constraints, but they were not taken
from a cited statutory instrument.

## 10. Statistical significance is cheap here

R is under our control. Simulating more days makes any non-zero difference
"significant". That is why the confidence interval and the effect size, not the
p-value, are reported as the result — and why only ONE confirmatory test is
run, with everything else explicitly descriptive.
""")

# =====================================================================
# 3. PRE-REGISTRATION
# =====================================================================
w("pre_registration.md", """# TRUCKLY — Pre-registered analysis plan

Fixed before the experiment was run. Committed so that the analysis cannot be
retro-fitted to the result.

## Hypotheses

- **H1 (primary).** Optimisation-based freight matching (TRUCKLY) reduces total
  empty vehicle-kilometres per operating day relative to a naive greedy matcher
  (B2), under identical instances and common random numbers.
- **H2.** TRUCKLY reduces empty km relative to the empty-return policy (B0).
- **H3.** TRUCKLY reduces net cost (journey cost minus freight revenue)
  relative to both B0 and B2.
- **H0 aspiration.** The 60% figure is an *a priori aspirational hypothesis*,
  stated in advance and reported against. It is not a claim, and the
  experimental design was not tuned toward it.

## Design

- Unit of inference: **the simulated operating day (instance)**, not the truck.
  Trucks within a day compete for the same shipment pool and are not
  independent.
- R = 100 instances per scenario.
- Variance reduction: **common random numbers** — every policy sees the same
  fleet, shipment pool, network and per-arc fuel perturbation.
- Information parity: all policies decide at the same epoch with the same
  visible pool. No policy is given foresight the others lack.
- Identical cost model object for every policy.

## Primary endpoint and test

- Endpoint: **total empty kilometres per operating day, TRUCKLY vs B2_greedy**,
  base scenario S0_base.
- Test: **Wilcoxon signed-rank** on the paired per-instance differences, chosen
  in advance because the KPI distributions are expected to be right-skewed and
  the signed-rank test is valid under both skew and approximate normality.
- Reporting order: bootstrap 95% CI on the mean difference (10,000 resamples)
  -> Hodges-Lehmann estimate -> rank-biserial effect size -> p-value LAST.

## Multiplicity

Only the primary endpoint is confirmatory. All other KPIs and all other
scenarios are **descriptive**, reported with confidence intervals, Holm-adjusted
within the secondary family, and carry no significance claim.

## Stated in advance: what would count as a negative result

- If TRUCKLY does not beat B2 on empty km, H1 is not supported, and that will
  be reported as the headline finding rather than replaced with a comparison
  against B0.
- Percentage reductions will be reported per KPI. **No composite "overall
  savings" number will be computed** under any circumstances.
- If fuel or gross cost increases, that will be reported as an increase.
""")

# =====================================================================
# 4. OBSERVATION GUIDANCE (Deliverable 28)
# =====================================================================
w("observation_guidance.md", f"""# TRUCKLY — Observation Guidance for the Five Poster Graphs

**Read this, look at the graph, then write the observation in your own words.**

These notes deliberately do **not** contain finished paragraphs for you to copy.
Your university requires the observations to be handwritten, and the point of
that requirement is that you understand what you are looking at. Each section
below gives you: what to look for, the statistical concept, the actual measured
result, and what you should be able to explain unaided.

---

## Graph 1 — Histogram of `empty_distance_km`

**What to look for**
Where the bulk of the bars sit; how far the right tail stretches; whether the
mean line sits to the right of the median line; how wide the shaded IQR band is.

**Statistical concept**
Distribution shape, central tendency vs dispersion, and **skewness diagnosed by
the mean-median gap**. When the mean exceeds the median, the distribution is
pulled right by a tail of large values.

**The actual result**
n = {g1['n']:,}. Mean {g1['mean_km']:.1f} km, median {g1['median_km']:.1f} km,
SD {g1['sd_km']:.1f} km, IQR {g1['q1']:.0f}-{g1['q3']:.0f} km
(= {g1['iqr']:.0f} km), P90 {g1['p90']:.0f} km, max {g1['max_km']:.0f} km,
skewness {g1['skew']:.3f}. The top decile of journeys carries
**{g1['pct_of_empty_km_in_top_decile']:.1f}%** of all empty kilometres. The
fleet burns {g1['total_empty_km_per_day']:,.0f} empty km per operating day.

**What you should be able to explain in your own words**
- Why mean > median tells you the distribution is right-skewed.
- Why a right-skewed distribution is operationally *good news* for a matching
  system: the empty kilometres are concentrated in a minority of journeys, so
  you do not need to match everything to capture most of the benefit.
- What the IQR band is actually showing (the middle half of journeys).

**Caveat you must state**
This distribution is a property of the simulated corridor and fleet. A different
geography or demand pattern would produce a different shape.

---

## Graph 2 — Box plot of `fuel_cost_inr` grouped by `truck_type`

**What to look for**
Whether the boxes overlap between vehicle classes; how tall each box is
(that is the IQR); whether any points sit beyond the whiskers.

**Statistical concept**
Quartiles, IQR as a **robust** measure of spread, the 1.5×IQR whisker
convention, and — the important one — **between-group variation vs
within-group variation**.

**The actual result**
{" · ".join(f"{r['truck_type']}: median Rs {r['median']:,} (IQR {r['IQR']:,})" for r in g2['by_type'])}.
Mean within-class IQR is about **Rs {g2['within_class_iqr_mean']:,}**, which is
LARGER than the **Rs {g2['between_class_median_range']:,}** spread between the
smallest and largest class medians.
{sum(r['n_outliers'] for r in g2['by_type'])} points fall beyond the 1.5×IQR fence.

**What you should be able to explain in your own words**
- The single most important reading: variation *within* a vehicle class exceeds
  variation *between* classes. So fuel cost is driven more by **how a vehicle is
  used** (distance, load, empty running) than by **which vehicle it is** — and
  that is precisely the argument for a matching system.
- What a box plot's five marks each represent.

**Caveat you must state**
The 1.5×IQR rule is a display convention, not a statistical test. A point beyond
the whisker is *unusual*, not *wrong*, and must never be called an error or
deleted.

---

## Graph 3 — Scatter of `total_distance_km` vs `fuel_litres`, coloured by payload

**What to look for**
How tightly points hug the fitted line; whether colour varies systematically
above vs below the line; whether the vertical spread grows with distance.

**Statistical concept**
Bivariate association, Pearson r vs Spearman ρ, **R² as the share of variance in
fuel explained by distance alone**, residual structure, and confounding.

**The actual result**
Pearson r = {g3['pearson_r']:.3f}, R² = {g3['r2']:.3f},
Spearman ρ = {g3['spearman']:.3f}, slope {g3['slope_l_per_km']:.4f} L/km,
n = {g3['n']:,}. So roughly {100*g3['r2']:.0f}% of the variation in fuel is
accounted for by distance, and about {100*(1-g3['r2']):.0f}% is not.
The supplementary panel (G3b) plots fuel **per km** against payload: r drops to
{g3['g3b_pearson_r']:.3f}, R² = {g3['g3b_r2']:.3f}, slope
{g3['g3b_slope']:.4f} L/km per tonne carried.

**What you should be able to explain in your own words**
- The two-part statement: **distance sets the level, payload sets the deviation.**
- Why the supplementary panel is the more informative one — dividing by distance
  removes the obvious driver and exposes the load effect.
- **The honesty point, which you must be able to defend out loud:** fuel in this
  dataset is *generated* from a load-dependent consumption model with random
  perturbation. The distance-fuel association is therefore **partly structural
  by construction**. The panel characterises the strength of that association
  and how much residual variation payload explains; it does not *discover* that
  distance drives fuel.

**Caveat you must state**
Association is not causation, and here the direction is known from the
generating model rather than inferred from the plot. No confidence band or
p-value is shown, because truck-journeys within one simulated day are not
independent observations.

---

## Graph 4 — Spearman correlation heatmap

**What to look for**
The strongest *non-grey* cells. Ignore the grey ones entirely — they are masked.

**Statistical concept**
Correlation matrices, **monotonic (Spearman) vs linear (Pearson) association**,
and the difference between a **definitional identity** and an empirical finding.

**The actual result** (strongest non-definitional pairs)
{chr(10).join(f"- {a} ↔ {b}: ρ = {r:+.2f}" for a, b, r in g4['strongest_non_definitional'][:5])}

Near-zero pairs: {", ".join(f"{a}↔{b} ρ={r:+.2f}" for a, b, r in g4['weakest'])}.

**What you should be able to explain in your own words**
- Why several cells are greyed out: `total = loaded + empty`,
  `fuel_cost = fuel × price`, and utilisation is a ratio of two other columns.
  Those correlations are properties of the arithmetic, not discoveries, and
  presenting them as findings would be an error.
- Why Spearman was chosen over Pearson here (the variables are skewed, and
  Spearman only assumes a monotonic relationship).
- What the negative utilisation↔empty-km correlation means physically.

**Caveat you must state**
Correlation here is pairwise and marginal — a strong pairwise correlation can
vanish once a third variable is controlled for. And none of these coefficients
establish a causal direction.

---

## Graph 5 — Distribution of `utilisation_weight_pct`

**What to look for**
**Count the peaks first.** Then the median line, then the size of the shaded
low-utilisation region.

**Statistical concept**
Probability density, **modality**, and percentile thresholds.

**The actual result**
n = {g5['n']:,}. The distribution is **bimodal**:
{g5['pct_exactly_zero']:.1f}% of return legs sit at exactly 0% (those trucks
were not matched and ran home empty), and the matched legs form a second mode
with a median of {g5['median_matched_pct']:.1f}%. Overall median
{g5['median_pct']:.1f}%, mean {g5['mean_pct']:.1f}%, P90 {g5['p90']:.1f}%,
max {g5['max_pct']:.1f}%. **{g5['pct_below_threshold']:.1f}%** of all legs fall
below the {g5['threshold']:.0f}% under-utilisation threshold.

**What you should be able to explain in your own words**
- Why bimodality is the *visual signature of the empty-backhaul problem* — it is
  a much more interesting observation than "utilisation is low", and you should
  lead with it.
- What the area under the low mode represents: the theoretical headroom a
  matching system is trying to capture.
- Why this is a useful sanity check on the later results.

**Caveats you must state**
- This is **return-leg** utilisation only. The outbound leg is outside the model,
  so these are not round-trip figures and must not be compared to industry
  round-trip statistics.
- Weight utilisation ignores volume. A truck at 40% of weight capacity may be at
  100% of volume ("cubed out"), so this panel *overstates* the spare capacity
  available for low-density freight.
""")

# =====================================================================
# 5. METHODOLOGY
# =====================================================================
w("methodology.md", f"""# TRUCKLY — Methodology

## 1. Problem class

Truckly is a **Selective Pickup-and-Delivery Problem with Time Windows
(S-PDPTW)**, solved in a prize-collecting form. It is NOT a classical VRPTW:
in a VRPTW every customer must be visited, whereas here *accepting nothing and
driving home empty is a legal solution*. Choosing which loads to serve is a
decision variable, which is what makes the problem selective.

## 2. Architecture

```
L0 config + seeds        config.yaml, run manifest, config hash
L1 data                  real node coordinates (OBS) + synthetic freight (SIM)
L2 network               distance & duration matrices (cached)
L3 domain                Truck / Shipment / Leg / Journey / CostModel
L4 feasibility filter    capacity -> volume -> detour -> time -> driver hours
L5 matching + scoring    candidate generation, explainable score
L6 optimisation          6a CP-SAT assignment · 6b exact route enumeration
L7 experiment engine     4 policies, common random numbers
L8 evaluation            KPI ledger, paired tests, scenarios, sensitivity
L9 presentation          poster, dashboard, demo
```

## 3. Instance generation

Origin-destination demand follows a **gravity (spatial-interaction) model**:

    P(o -> d)  proportional to  w_o * w_d / dist(o,d)^beta,   beta = {cfg['scenario_defaults']['gravity_beta']}

This matters substantively, not cosmetically. Uniform OD sampling over 40 nodes
spreads freight across 1,560 lanes, no corridor ever concentrates, and backhaul
matching becomes impossible for reasons that are an artefact of the sampler
rather than a property of freight. The gravity model concentrates flow onto
short and medium lanes between high-weight nodes, which is what real road
freight does.

Demand is **asymmetric**: a fraction {cfg['scenario_defaults']['demand_asymmetry']}
of loads run source->sink (headhaul, of no use to a returning truck) and the
remainder run sink->source (backhaul). Trucks are placed by simulating a
completed headhaul leg, so they stand at sink nodes needing to get home to
source nodes. If the pool were symmetric the problem would be trivial.

Driver headroom is generated **relative to the direct return**, so the
empty-return baseline B0 is feasible by construction for every truck. This is
asserted in code — a policy that cannot even drive home would make the
comparison meaningless.

## 4. Fuel model

    F_a = (d_a / 100) * (beta0 + beta1 * w_a + gamma * rho_a) * eps

with beta0 the unladen rate for the vehicle class, beta1 the marginal rate per
tonne, rho_a a per-arc road-difficulty index, gamma = {cfg['fuel_model']['road_factor_coeff_gamma']},
and eps a lognormal perturbation with sigma = {cfg['fuel_model']['noise_lognormal_sigma']}
representing driver behaviour, weather and vehicle condition.

The load term is not decoration. A distance-only fuel model would make an empty
kilometre and a loaded kilometre cost the same, and the entire economic premise
of backhaul matching would collapse.

## 5. Optimisation

**Master problem** — prize-collecting set packing with an outside option:

    min  sum_{{k,b}} (c_kb - rev_b) y_kb  +  sum_k c_k^empty z_k
    s.t. sum_b y_kb + z_k = 1              for every truck k        (C1)
         sum_{{k,b : r in b}} y_kb <= 1     for every request r      (C2)
         y, z in {{0,1}}

where `c_kb` is the journey objective for truck k serving bundle b and `rev_b`
is the freight revenue of the bundle. Solved with **OR-Tools CP-SAT** to proven
optimality over the generated candidate set; the solver status is recorded on
every journey row so the claim is checkable.

The journey objective adds a **managerial empty-running penalty** of
Rs {cfg['cost']['empty_km_penalty_inr_per_km']}/km to accounting cost. It is
applied identically to every policy, and reported money figures exclude it, so
the rupee columns stay real. The cost-component ablation reports results with
this term set to zero.

**Routing sub-problem** — for a bundle of k requests there are (2k)!/2^k
precedence-valid orderings (2 for k=1, 6 for k=2, 90 for k=3). All are
enumerated exactly, so the route for any accepted bundle is **provably optimal**
and faster than invoking a routing solver. Constraints enforced along the route:
time propagation, waiting at pickups before the ready time, weight and volume
capacity on every arc, hard delivery deadlines, a detour budget of
`max(theta * d_ret, {cfg['scenario_defaults']['min_detour_allowance_km']} km)`,
remaining legal driving hours, total duty hours, and a mandatory break after
{cfg['driver']['break_after_hours']} h of driving.

## 6. Explainable score

    S(k,b) = w1*empty_avoided - w2*detour + w3*capacity - w4*waiting + w5*slack

Every term is divided by a stated maximum so the weights are comparable. Note
the detour term is normalised by `theta * d_ret` — the *tolerance* — not by
`d_ret`; dividing by `d_ret` would compress the term into [0, theta] and
silently down-weight it by 1/theta.

**The score is not the objective.** The optimiser minimises cost in rupees. The
score exists to drive baseline B2 and to explain recommendations to the user.

## 7. Experimental design

Four policies on identical instances under **common random numbers**: the
per-arc fuel perturbation eps[a][b] is fixed for an (instance, arc) pair, so any
policy traversing that arc experiences the same perturbation. This makes the
comparison paired and sharply reduces the variance of the difference.

Unit of inference is the **simulated operating day**, not the truck. R = 100
days per scenario, 12 scenarios.
""")
print("docs done")
