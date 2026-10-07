# TRUCKLY
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

Across **100 paired simulated operating days** of a 30-truck
fleet on a 40-node South-India network, under common random numbers, Truckly
reduced empty vehicle-kilometres by **24.7%** and net
cost by **18.6%** relative to an empty-return baseline,
and raised return-leg weight utilisation by
**6.81 percentage points**
from zero. Against a **naive greedy matcher** — the honest competitor — the
margin was much smaller but statistically reliable: **1.01%**
fewer empty kilometres (mean paired difference 34.6 km/day, 95%
bootstrap CI [25.0, 44.3], Wilcoxon p = 1.5e-09,
lower in 69/100 days) and
**2.1%** lower net cost while serving
**11.7% more loads**.

**The 60% aspirational target was not reached on any metric.** Two results run
against the intuitive story and are reported as found: fuel consumption and
gross operating cost *increased* (-9.1 % and
-7.4 % versus B0), because carrying freight burns
more than running empty — the gain is in *net* cost and in utilisation, not in
fuel. And the benefit is not a constant: it rises from
**10.0%** at 2 open loads per truck to
**44.3%** at 15, making shipment density
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
**4,495 empty kilometres per operating day** —
a mean of 150 km per truck, with the worst decile of journeys
carrying 19% of the total. Every one of
those kilometres consumes diesel, driver hours, vehicle life and road capacity
while producing nothing.

The distribution matters as much as the total. Because empty distance is
**right-skewed** (skewness 0.50; mean 150 km >
median 135 km), the waste is concentrated: a matching system
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
Stage A  candidate generation   feasible (truck, bundle) pairs, bundles <= 2
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
| Distance / duration | **DRV + ASM** | great-circle × declared circuity (1.18–1.35×); **no live routing engine was reachable** — see `docs/limitations.md` §1 |
| Shipments | **SIM** | 18,000 in the base scenario (231,000 across all 12 scenarios) |
| Trucks | **SIM** | 3,000 truck-journeys in the base scenario, 4 vehicle classes |
| Journeys | **OPT/DRV** | 216,000 rows = 12 scenarios × 100 days × 30 trucks × 6 policies |
| Candidates | **OPT** | 24,764 (truck, bundle) pairs with features and the optimiser's choice |
| Cost parameters | **ASM** | diesel ₹90.0/L, wage ₹130.0/h, toll ₹1.6/km, tariff ₹20.0/km + ₹3.0/t·km |

Shipment origin–destination pairs are drawn from a **gravity (spatial-interaction)
model**, `P(o→d) ∝ w_o·w_d / dist^1.8`, with an
asymmetric split (0.62 headhaul) so
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

**Result: 13/13 checks pass on the real data, and
13/13 demonstrably fire on the corrupted copy.**

| check                                       |   violations | fires_on_corrupted_copy   |
|:--------------------------------------------|-------------:|:--------------------------|
| C01_missing_values                          |            0 | True                      |
| C01b_declared_nullable_only_where_unmatched |            0 | True                      |
| C02_duplicate_keys                          |            0 | True                      |
| C03_negative_quantities                     |            0 | True                      |
| C04_distance_identity                       |            0 | True                      |
| C05_cost_identity                           |            0 | True                      |
| C06_utilisation_bounds                      |            0 | True                      |
| C07_capacity_respected                      |            0 | True                      |
| C08_time_windows                            |            0 | True                      |
| C09_geographic_bounds                       |            0 | True                      |
| C10_od_distinct                             |            0 | True                      |
| C11_service_level_bounded                   |            0 | True                      |
| C12_pairing_intact                          |            0 | True                      |

**No rows were dropped, no values imputed, no outliers winsorised.** The
1.5×IQR rule is a display convention, not a validity test — a long empty return
is unusual, not erroneous, and it is exactly the phenomenon the project exists
to study. Full transformation log in `outputs/tables/cleaning_report.md`.

---

## 12. Exploratory Data Analysis

Baseline B0, scenario S0_base, n = 3,000 truck-journeys.

| Variable                 | Unit   |    n |    Mean |      SD |     Min |     P10 |   Q1 (P25) |   Median (P50) |   Q3 (P75) |     P90 |      Max |     IQR |   Skew |
|:-------------------------|:-------|-----:|--------:|--------:|--------:|--------:|-----------:|---------------:|-----------:|--------:|---------:|--------:|-------:|
| total_distance_km        | km     | 3000 |  149.84 |   71.48 |   60.22 |   65.23 |      84.22 |         134.58 |     208.12 |  255.24 |   302.01 |  123.9  |   0.5  |
| empty_distance_km        | km     | 3000 |  149.84 |   71.48 |   60.22 |   65.23 |      84.22 |         134.58 |     208.12 |  255.24 |   302.01 |  123.9  |   0.5  |
| loaded_distance_km       | km     | 3000 |    0    |    0    |    0    |    0    |       0    |           0    |       0    |    0    |     0    |    0    |   0    |
| detour_distance_km       | km     | 3000 |    0    |    0    |    0    |    0    |       0    |           0    |       0    |    0    |     0    |    0    |   0    |
| fuel_litres              | L      | 3000 |   38.16 |   20.67 |    8.62 |   15.75 |      21.2  |          33.45 |      51.61 |   69    |   116.43 |   30.41 |   0.84 |
| fuel_cost_inr            | INR    | 3000 | 3434.47 | 1860.4  |  775.43 | 1417.32 |    1907.55 |        3010.72 |    4644.5  | 6210.4  | 10479.1  | 2736.94 |   0.84 |
| waiting_time_hr          | hours  | 3000 |    0    |    0    |    0    |    0    |       0    |           0    |       0    |    0    |     0    |    0    |   0    |
| driving_time_hr          | hours  | 3000 |    2.94 |    1.24 |    1.25 |    1.36 |       1.76 |           2.8  |       4.03 |    4.64 |     5.49 |    2.27 |   0.28 |
| duty_time_hr             | hours  | 3000 |    2.94 |    1.24 |    1.25 |    1.36 |       1.76 |           2.8  |       4.03 |    4.64 |     5.49 |    2.27 |   0.28 |
| utilisation_weight_pct   | %      | 3000 |    0    |    0    |    0    |    0    |       0    |           0    |       0    |    0    |     0    |    0    |   0    |
| utilisation_distance_pct | %      | 3000 |    0    |    0    |    0    |    0    |       0    |           0    |       0    |    0    |     0    |    0    |   0    |
| total_cost_inr           | INR    | 3000 | 6556.85 | 2105.75 | 3555.02 | 4218.63 |    4784.95 |        6094.46 |    7981.1  | 9696.22 | 14176.1  | 3196.15 |   0.76 |
| net_cost_inr             | INR    | 3000 | 6556.85 | 2105.75 | 3555.02 | 4218.63 |    4784.95 |        6094.46 |    7981.1  | 9696.22 | 14176.1  | 3196.15 |   0.76 |
| co2_kg                   | kg     | 3000 |  102.27 |   55.4  |   23.09 |   42.2  |      56.8  |          89.65 |     138.3  |  184.93 |   312.04 |   81.5  |   0.84 |

Shipment level, n = 18,000:

| Variable           | Unit   |     n |    Mean |      SD |     Min |     P10 |   Q1 (P25) |   Median (P50) |   Q3 (P75) |     P90 |      Max |     IQR |   Skew |
|:-------------------|:-------|------:|--------:|--------:|--------:|--------:|-----------:|---------------:|-----------:|--------:|---------:|--------:|-------:|
| shipment_weight_kg | kg     | 18000 | 2831    | 1919.85 |  200    | 1061.4  |    1535.18 |        2327.8  |    3553.32 | 5180.99 | 19907.6  | 2018.15 |   2.12 |
| shipment_volume_m3 | m3     | 18000 |   12.72 |   11.21 |    0.65 |    3.8  |       5.78 |           9.43 |      15.71 |   25.14 |   147.19 |    9.92 |   3.12 |
| direct_distance_km | km     | 18000 |  119.28 |   76.06 |   40.34 |   45.38 |      55.33 |          96.79 |     161.75 |  244.97 |   302.01 |  106.42 |   0.86 |
| revenue_inr        | INR    | 18000 | 3997.28 | 2311.63 | 1450.33 | 1811.2  |    2145.46 |        3208.65 |    5344.96 | 7440.13 | 18378.2  | 3199.5  |   1.23 |

---

## 13. Statistical Analysis (the five poster panels)

| Panel | Measured result |
|---|---|
| **G1** histogram of empty distance | right-skewed, skew **0.50**; mean 149.8 km > median 134.6 km; IQR 124 km; top decile carries **18.8%** of all empty km |
| **G2** fuel cost by vehicle class | mean within-class IQR ≈ ₹2,890 **exceeds** the between-class median range of ₹1,997 — usage matters more than vehicle choice |
| **G3** distance vs fuel | r = 0.882, R² = 0.778; **partly structural by construction**. Supplementary panel (fuel/km vs payload): r = 0.372, slope 0.0123 L/km per tonne |
| **G4** Spearman heatmap | strongest non-definitional: Payload t·km↔Detour km ρ=+0.73; Weight util %↔Detour km ρ=+0.68; Weight util %↔Empty km ρ=-0.61. Definitional identities masked |
| **G5** utilisation density | **bimodal** — 52.7% at exactly 0%, matched legs median 14.2%; 87.5% below the 25% threshold |

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

    min  Σ_{k,b} (c_kb − rev_b)·y_kb  +  Σ_k c_k^empty·z_k
    s.t. Σ_b y_kb + z_k = 1              ∀ truck k          (C1)
         Σ_{k,b: r∈b} y_kb ≤ 1          ∀ request r        (C2)
         y, z ∈ {0,1}

A **prize-collecting set-packing problem with an outside option**, solved by
OR-Tools CP-SAT to **proven optimality** over the generated candidate set
(solver status recorded on every row: 100% `optimal`). Routes are found by
exact enumeration of all (2k)!/2^k precedence-valid orderings, so the route for
any accepted bundle is provably optimal too.

Mean decision time: **0.58 ms per truck**.

---

## 16. Baseline Policies

Journey-level means, scenario S0_base:

| policy      |    n |   mean_total_km |   mean_empty_km |   mean_fuel_l |   mean_cost |   mean_net_cost |   mean_wait_hr |   mean_util_w |   fill_rate_pct |
|:------------|-----:|----------------:|----------------:|--------------:|------------:|----------------:|---------------:|--------------:|----------------:|
| B0_empty    | 3000 |          149.84 |          149.84 |         38.16 |     6556.85 |         6556.85 |           0    |          0    |            0    |
| B1_wait_12h | 3000 |          161.29 |          117.84 |         41.85 |     7054.49 |         5562.63 |           0.1  |          7.68 |           47.63 |
| B1_wait_2h  | 3000 |          161.18 |          118.42 |         41.81 |     7046.5  |         5578.54 |           0.08 |          7.49 |           46.77 |
| B1_wait_6h  | 3000 |          161.29 |          117.84 |         41.85 |     7054.49 |         5562.63 |           0.1  |          7.68 |           47.63 |
| B2_greedy   | 3000 |          159.38 |          113.92 |         41.45 |     7016.22 |         5453.99 |           0.16 |          8.63 |           47.43 |
| TRUCKLY     | 3000 |          160.02 |          112.77 |         41.64 |     7045.06 |         5339.11 |           0.14 |          9.1  |           47.33 |

---

## 17. Experimental Design

- **R = 100 simulated operating days** per scenario, 12 scenarios.
- **Common random numbers**: the per-arc fuel perturbation is fixed per
  (instance, arc), so any policy traversing that arc gets the same perturbation.
  The comparison is therefore paired.
- **Unit of inference = the operating day**, not the truck. Trucks within a day
  compete for the same pool and are not independent.
- Analysis plan pre-registered in `docs/pre_registration.md`.

---

## 18. Results

| KPI                       | Unit   |   B0_empty |   B1_wait_2h |   B1_wait_6h |   B1_wait_12h |   B2_greedy |    TRUCKLY | Truckly vs B0   | Truckly vs B2   | Better when   | Improvement?   |
|:--------------------------|:-------|-----------:|-------------:|-------------:|--------------:|------------:|-----------:|:----------------|:----------------|:--------------|:---------------|
| Total km                  | km     |    4495    |     4836     |     4839     |      4839     |    4781     |   4801     | -6.8 %          | -0.4 %          | lower         | NO             |
| Empty km                  | km     |    4495    |     3553     |     3535     |      3535     |    3418     |   3383     | +24.7 %         | +1.0 %          | lower         | yes            |
| Empty km share            | %      |     100    |       73.5   |       73     |        73     |      71.5   |     70.4   | -29.60 pp       | -1.10 pp        | lower         | yes            |
| Loaded km                 | km     |       0    |     1283     |     1303     |      1303     |    1364     |   1418     | nan             | +4.0 %          | higher        | --             |
| Fuel                      | L      |    1144.8  |     1254.4   |     1255.4   |      1255.4   |    1243.4   |   1249.2   | -9.1 %          | -0.5 %          | lower         | NO             |
| Fuel cost                 | INR    |  103034    |   112897     |   112983     |    112983     |  111902     | 112424     | -9.1 %          | -0.5 %          | lower         | NO             |
| Waiting time              | h      |       0    |        2.37  |        3.05  |         3.05  |       4.69  |      4.27  | nan             | +9.0 %          | lower         | --             |
| Driver duty time          | h      |      88.3  |      121.2   |      122.4   |       122.4   |     122.6   |    125     | -41.6 %         | -2.0 %          | lower         | NO             |
| Weight utilisation        | %      |       0    |        5.65  |        5.73  |         5.73  |       6.34  |      6.81  | nan             | +0.47 pp        | higher        | --             |
| Distance utilisation      | %      |       0    |       26.5   |       27     |        27     |      28.5   |     29.6   | nan             | +1.10 pp        | higher        | --             |
| Backhaul fill rate        | %      |       0    |       46.8   |       47.6   |        47.6   |      47.4   |     47.3   | nan             | -0.10 pp        | higher        | --             |
| Total cost                | INR    |  196706    |   211395     |   211635     |    211635     |  210487     | 211352     | -7.4 %          | -0.4 %          | lower         | NO             |
| Freight revenue           | INR    |       0    |    44039     |    44756     |     44756     |   46867     |  51179     | nan             | +9.2 %          | higher        | --             |
| Net cost (cost - revenue) | INR    |  196706    |   167356     |   166879     |    166879     |  163620     | 160173     | +18.6 %         | +2.1 %          | lower         | yes            |
| Shipments served          | count  |       0    |       14.03  |       14.29  |        14.29  |      14.23  |     15.89  | nan             | +11.7 %         | higher        | --             |
| On-time rate              | %      |     100    |      100     |      100     |       100     |     100     |    100     | +0.00 pp        | +0.00 pp        | higher        | NO             |
| Tonne-km per litre        | t.km/L |       0    |        2.643 |        2.682 |         2.682 |       2.959 |      3.175 | nan             | +7.3 %          | higher        | --             |
| CO2 estimate              | kg     |    3068    |     3362     |     3364     |      3364     |    3332     |   3348     | -9.1 %          | -0.5 %          | lower         | NO             |
| Solve time per decision   | ms     |       0.01 |        0.15  |        0.14  |         0.14  |       0.2   |      0.58  | nan             | nan             | lower         | --             |

### 60% target analysis

| metric                                               | comparator   |   comparator_total |   truckly_total |   abs_diff_per_day | abs_diff_ci            |   pct_ratio_of_sums |   pct_mean_of_per_instance | pct_estimator_unstable   | reaches_60pct_target   |
|:-----------------------------------------------------|:-------------|-------------------:|----------------:|-------------------:|:-----------------------|--------------------:|---------------------------:|:-------------------------|:-----------------------|
| Empty-km reduction                                   | B0_empty     |            4495.3  |         3383.1  |            1112.2  | [1051.49, 1175.05]     |               24.74 |                      24.82 | False                    | False                  |
| Fuel reduction                                       | B0_empty     |            1144.8  |         1249.2  |            -104.34 | [-110.08, -98.72]      |               -9.11 |                      -9.15 | False                    | False                  |
| Total-cost reduction                                 | B0_empty     |          196706    |       211352    |          -14646.1  | [-15340.34, -13959.88] |               -7.45 |                      -7.45 | False                    | False                  |
| NET-cost reduction                                   | B0_empty     |          196706    |       160173    |           36532.4  | [34624.61, 38484.10]   |               18.57 |                      18.59 | False                    | False                  |
| Waiting-time reduction                               | B1_wait_6h   |               3    |            4.3  |              -1.22 | [-1.53, -0.90]         |              -39.86 |                    -138.06 | True                     | False                  |
| Empty-km reduction                                   | B2_greedy    |            3417.7  |         3383.1  |              34.58 | [25.28, 44.64]         |                1.01 |                       1.02 | False                    | False                  |
| NET-cost reduction                                   | B2_greedy    |          163620    |       160173    |            3446.59 | [2982.30, 3921.22]     |                2.11 |                       2.15 | False                    | False                  |
| Weight-utilisation improvement (percentage POINTS)   | B0_empty     |               0    |            6.81 |               6.81 | [6.43, 7.19]           |              nan    |                     nan    | False                    | False                  |
| Weight-utilisation improvement (percentage POINTS)   | B2_greedy    |               6.34 |            6.81 |               0.47 | [0.36, 0.58]           |              nan    |                     nan    | False                    | False                  |
| Distance-utilisation improvement (percentage POINTS) | B0_empty     |               0    |           29.56 |              29.56 | [28.23, 30.91]         |              nan    |                     nan    | False                    | False                  |

**The 60% aspiration was not reached on any metric.** It was stated in advance
as a hypothesis, and it is reported against as found.

### The results that run against the story

- **Fuel rose 9.1%** and gross cost rose
  7.4% versus B0.
  Carrying freight burns more diesel than running empty. This is not a defect in
  the system; it is what the physics requires, and any project reporting fuel
  savings proportional to empty-km savings has mis-modelled it.
- **Total distance rose 6.8%**,
  because serving extra loads requires repositioning. The right measure is
  *empty* km, not total km.
- **Waiting time rose**, not fell, versus B1. Truckly is willing to wait when
  waiting pays. B1's wait caps (2/6/12 h) turned out to be **non-binding** in
  this environment — all three variants produce nearly identical results, which
  is itself a finding.

---

## 19. Statistical Validation

**Primary endpoint (pre-specified): empty-km reduction, TRUCKLY vs B2_greedy.**

- n = 100 paired operating days
- Mean paired difference **34.6 km/day**, 95% bootstrap CI
  **[25.0, 44.3]**
- Hodges–Lehmann estimate **29.4 km**
- Rank-biserial correlation **0.738**
- Wilcoxon signed-rank **p = 1.46e-09**
- TRUCKLY lower in **69/100** days

> **On Cohen's d_z.** Common random numbers deliberately shrink the SD of the
> paired difference, so d_z is mechanically inflated and is **not comparable**
> to an unpaired design. It is reported as a within-design descriptor only.
>
> **On p-values.** R is under our control; simulating more days makes any
> non-zero difference "significant". The interval and the effect size are the
> result. Only one confirmatory test is run; every other comparison is
> descriptive, Holm-adjusted within the secondary family.

| comparison                               | kpi                  |   n_instances |   comparator_mean |   truckly_mean |   mean_diff |      ci_low |     ci_high |   hodges_lehmann |   pct_change |   cohens_dz |   rank_biserial |   wilcoxon_p |   truckly_better_in_n | direction        |   holm_adjusted_p | role                    |
|:-----------------------------------------|:---------------------|--------------:|------------------:|---------------:|------------:|------------:|------------:|-----------------:|-------------:|------------:|----------------:|-------------:|----------------------:|:-----------------|------------------:|:------------------------|
| TRUCKLY vs B2_greedy  [PRIMARY ENDPOINT] | Empty km             |           100 |         3417.7    |      3383.12   |     34.5799 |     24.9788 |     44.3475 |          29.397  |       1.0118 |      0.6903 |          0.7383 |       0      |                    69 | lower is better  |          nan      | PRIMARY                 |
| TRUCKLY vs B0_empty                      | Empty km             |           100 |         4495.32   |      3383.12   |   1112.2    |   1052.45   |   1172.45   |        1105.77   |      24.7413 |      3.5619 |          1      |       0      |                   100 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Total km             |           100 |         4495.32   |      4800.72   |   -305.407  |   -324.059  |   -287.272  |        -301.796  |      -6.7939 |     -3.2059 |          1      |       0      |                     0 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Fuel L               |           100 |         1144.82   |      1249.16   |   -104.336  |   -109.959  |    -98.6774 |        -103.595  |      -9.1137 |     -3.5928 |          1      |       0      |                     0 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Net cost INR         |           100 |       196706      |    160173      |  36532.4    |  34570.6    |  38450.2    |       36290.8    |      18.5721 |      3.6876 |          1      |       0      |                   100 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Total cost INR       |           100 |       196706      |    211352      | -14646.1    | -15337.8    | -13956      |      -14630.2    |      -7.4457 |     -4.1439 |          1      |       0      |                     0 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Waiting h            |           100 |            0      |         4.2654 |     -4.2654 |     -4.7685 |     -3.7858 |          -4.1095 |     nan      |     -1.6818 |          1      |       0      |                     0 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Shipments served     |           100 |            0      |        15.89   |    -15.89   |    -16.55   |    -15.23   |         -16      |     nan      |     -4.7331 |          1      |       0      |                   100 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | Weight utilisation % |           100 |            0      |         6.8077 |     -6.8077 |     -7.2041 |     -6.4298 |          -6.6864 |     nan      |     -3.4749 |          1      |       0      |                   100 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B0_empty                      | CO2 kg               |           100 |         3068.13   |      3347.75   |   -279.62   |   -294.845  |   -264.556  |        -277.635  |      -9.1137 |     -3.5928 |          1      |       0      |                     0 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Empty km             |           100 |         3535.24   |      3383.12   |    152.125  |    130.097  |    175.085  |         144.576  |       4.3031 |      1.3233 |          0.9959 |       0      |                    95 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Total km             |           100 |         4838.65   |      4800.72   |     37.9236 |     28.5417 |     47.4605 |          35.9432 |       0.7838 |      0.7858 |          0.7719 |       0      |                    78 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Fuel L               |           100 |         1255.37   |      1249.16   |      6.2099 |      3.5187 |      8.9649 |           6.2982 |       0.4947 |      0.4426 |          0.5002 |       0      |                    68 | lower is better  |            0.0001 | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Net cost INR         |           100 |       166879      |    160173      |   6705.64   |   5937.56   |   7486.93   |        6488.6    |       4.0183 |      1.7043 |          1      |       0      |                   100 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Total cost INR       |           100 |       211635      |    211352      |    282.959  |    -19.0283 |    587.482  |         284.333  |       0.1337 |      0.1794 |          0.2222 |       0.0537 |                    62 | lower is better  |            0.0537 | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Waiting h            |           100 |            3.0498 |         4.2654 |     -1.2156 |     -1.5434 |     -0.8982 |          -1.0606 |     -39.8587 |     -0.7402 |          0.786  |       0      |                    16 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Shipments served     |           100 |           14.29   |        15.89   |     -1.6    |     -1.86   |     -1.35   |          -1.5    |     -11.1966 |     -1.2069 |          0.9783 |       0      |                    80 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | Weight utilisation % |           100 |            5.7309 |         6.8077 |     -1.0768 |     -1.2452 |     -0.921  |          -0.9799 |     -18.7892 |     -1.2952 |          0.9952 |       0      |                    97 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B1_wait_6h                    | CO2 kg               |           100 |         3364.39   |      3347.75   |     16.6425 |      9.175  |     23.88   |          16.8791 |       0.4947 |      0.4426 |          0.5002 |       0      |                    68 | lower is better  |            0.0001 | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Total km             |           100 |         4781.26   |      4800.72   |    -19.4582 |    -27.4811 |    -11.1858 |         -18.0651 |      -0.407  |     -0.4666 |          0.5423 |       0      |                    22 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Fuel L               |           100 |         1243.35   |      1249.16   |     -5.8075 |     -8.3774 |     -3.3057 |          -5.2478 |      -0.4671 |     -0.4418 |          0.4948 |       0      |                    29 | lower is better  |            0.0001 | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Net cost INR         |           100 |       163620      |    160173      |   3446.59   |   2990.92   |   3926.69   |        3217.66   |       2.1065 |      1.4395 |          1      |       0      |                    96 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Total cost INR       |           100 |       210487      |    211352      |   -865.196  |  -1143.17   |   -582.403  |        -823.082  |      -0.411  |     -0.593  |          0.6405 |       0      |                    24 | lower is better  |            0      | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Waiting h            |           100 |            4.6905 |         4.2654 |      0.425  |      0.1821 |      0.6847 |           0.291  |       9.0617 |      0.3281 |          0.3431 |       0.0066 |                    50 | lower is better  |            0.0133 | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Shipments served     |           100 |           14.23   |        15.89   |     -1.66   |     -1.91   |     -1.41   |          -1.5    |     -11.6655 |     -1.3122 |          1      |       0      |                    82 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | Weight utilisation % |           100 |            6.3416 |         6.8077 |     -0.4662 |     -0.5817 |     -0.3651 |          -0.4038 |      -7.3507 |     -0.852  |          0.8823 |       0      |                    86 | higher is better |            0      | secondary (descriptive) |
| TRUCKLY vs B2_greedy                     | CO2 kg               |           100 |         3332.19   |      3347.75   |    -15.564  |    -22.4793 |     -8.7352 |         -14.0642 |      -0.4671 |     -0.4418 |          0.4948 |       0      |                    29 | lower is better  |            0.0001 | secondary (descriptive) |

---

## 20. Scenario Analysis

| scenario        | label                               |   density |   B0_empty_km |   B2_empty_km |   TR_empty_km |   empty_red_vs_B0_pct |   empty_red_vs_B2_pct |   net_cost_red_vs_B0_pct |   net_cost_red_vs_B2_pct |   fill_rate_TR_pct |   fill_rate_B2_pct |   util_gain_vs_B0_pp |   served_TR |   served_B2 |   solve_ms |
|:----------------|:------------------------------------|----------:|--------------:|--------------:|--------------:|----------------------:|----------------------:|-------------------------:|-------------------------:|-------------------:|-------------------:|---------------------:|------------:|------------:|-----------:|
| S0_base         | S0  Base case                       |         6 |          4495 |          3418 |          3383 |                 24.74 |                  1.01 |                    18.57 |                     2.11 |               47.3 |               47.4 |                 6.81 |       15.89 |       14.23 |      0.576 |
| S1_low_avail    | S1  Low availability (2/truck)      |         2 |          4454 |          4023 |          4008 |                 10.01 |                  0.37 |                     7.17 |                     0.46 |               22.5 |               22.3 |                 2.7  |        7    |        6.69 |      0.246 |
| S2_mod_avail    | S2  Moderate availability (6/truck) |         6 |          4520 |          3444 |          3405 |                 24.68 |                  1.14 |                    18.31 |                     2.1  |               47.5 |               47.4 |                 6.57 |       16.04 |       14.22 |      0.493 |
| S3_high_avail   | S3  High availability (15/truck)    |        15 |          4501 |          2583 |          2507 |                 44.3  |                  2.94 |                    34.47 |                     7.57 |               68.9 |               68.6 |                12    |       25.58 |       20.59 |      1.524 |
| S4_strict_dl    | S4  Strict deadlines                |         6 |          4492 |          3684 |          3654 |                 18.64 |                  0.81 |                    14.03 |                     1.51 |               43   |               42.7 |                 5.19 |       14.24 |       12.81 |      0.465 |
| S5_relaxed_dl   | S5  Relaxed deadlines               |         6 |          4426 |          2892 |          2837 |                 35.92 |                  1.92 |                    28.06 |                     5.68 |               59.2 |               59.1 |                10.32 |       21.58 |       17.72 |      0.801 |
| S6_low_util     | S6  Light shipments (low util)      |         6 |          4452 |          3322 |          3274 |                 26.46 |                  1.44 |                    17.59 |                     2.66 |               48.5 |               48.2 |                 3.72 |       16.71 |       14.46 |      0.566 |
| S7_high_util    | S7  Heavy shipments (high util)     |         6 |          4425 |          3512 |          3478 |                 21.4  |                  0.96 |                    18.25 |                     1.84 |               42.8 |               42.6 |                 9.69 |       14.02 |       12.77 |      0.451 |
| S8_small_trucks | S8  Small-truck fleet               |         6 |          4427 |          3395 |          3358 |                 24.16 |                  1.11 |                    19.51 |                     2.36 |               46.9 |               46.5 |                10.26 |       15.57 |       13.95 |      0.511 |
| S9_large_trucks | S9  Large-truck fleet               |         6 |          4493 |          3320 |          3284 |                 26.89 |                  1.06 |                    18.59 |                     2.45 |               49.4 |               49.1 |                 5.36 |       16.84 |       14.74 |      0.624 |
| S10a_detour_15  | S10a Detour tolerance 15%           |         6 |          4460 |          3433 |          3387 |                 24.06 |                  1.35 |                    17.66 |                     2.23 |               46.3 |               45.8 |                 6.15 |       15.67 |       13.75 |      0.544 |
| S10b_detour_50  | S10b Detour tolerance 50%           |         6 |          4463 |          3377 |          3339 |                 25.19 |                  1.11 |                    18.76 |                     2.16 |               49.1 |               49   |                 7.06 |       16.37 |       14.69 |      0.584 |

**The single most important result in the project** is the S1→S2→S3 progression:
Truckly's benefit rises from **10.0%** at
2 open loads per truck to **44.3%** at
15. Reporting the benefit as a *curve over shipment density*
rather than a point estimate is what makes it robust to the objection that the
generator was tuned.

---

## 21. Sensitivity Analysis

| parameter                   |   min_empty_red |   max_empty_red |   min_netcost_red |   max_netcost_red |   empty_swing_pp |   netcost_swing_pp |
|:----------------------------|----------------:|----------------:|------------------:|------------------:|-----------------:|-------------------:|
| shipment_density            |           10.44 |           43.55 |              7.48 |             34.47 |            33.11 |              26.99 |
| deadline_slack_factor       |           16.63 |           35.5  |             13.02 |             27.83 |            18.87 |              14.81 |
| detour_tolerance            |           23.09 |           26.49 |             17.31 |             19.86 |             3.4  |               2.55 |
| min_detour_allowance_km     |           23.93 |           26.73 |             17.49 |             20.09 |             2.8  |               2.6  |
| empty_km_penalty_inr_per_km |           24.67 |           24.97 |             18.55 |             18.59 |             0.3  |               0.04 |
| diesel_price_inr_per_litre  |           24.72 |           24.87 |             14.41 |             22.38 |             0.15 |               7.97 |
| tariff_inr_per_km           |           24.69 |           24.84 |             10.92 |             31.17 |             0.15 |              20.25 |
| waiting_cost_multiplier     |           24.74 |           24.84 |             18.06 |             18.88 |             0.1  |               0.82 |
| driver_wage_inr_per_hour    |           24.82 |           24.87 |             16.73 |             19.71 |             0.05 |               2.98 |

The dominant parameter is **shipment_density**, with a swing of
**33.1 percentage points** in empty-km reduction across
its tested range. Deadline tightness is second. Fuel price and driver wages
barely move the empty-km result at all — they move *cost*, not *routing* — which
is a useful sanity check that the model is behaving sensibly.

Full one-factor-at-a-time sweep in `outputs/tables/sensitivity_analysis.csv`.

---

## 22. Failure Analysis

| reason                  |    n |   pct_of_trucks |
|:------------------------|-----:|----------------:|
| detour_exceeded         | 1437 |           47.9  |
| matched                 | 1420 |           47.33 |
| lost_to_competing_truck |  143 |            4.77 |

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

| model              | split      |    n |   positive_rate |   threshold |   precision |   recall |     f1 |   roc_auc |   pr_auc |   brier |   tp |   fp |   fn |   tn |
|:-------------------|:-----------|-----:|----------------:|------------:|------------:|---------:|-------:|----------:|---------:|--------:|-----:|-----:|-----:|-----:|
| LogisticRegression | validation | 5072 |          0.2362 |         0.5 |      0.7465 |   0.5384 | 0.6256 |    0.8926 |   0.7157 |  0.1072 |  645 |  219 |  553 | 3655 |
| LogisticRegression | test       | 5048 |          0.2385 |         0.5 |      0.7265 |   0.5714 | 0.6397 |    0.8933 |   0.7251 |  0.1079 |  688 |  259 |  516 | 3585 |
| RandomForest       | validation | 5072 |          0.2362 |         0.5 |      0.8403 |   0.6194 | 0.7131 |    0.9281 |   0.8337 |  0.0866 |  742 |  141 |  456 | 3733 |
| RandomForest       | test       | 5048 |          0.2385 |         0.5 |      0.81   |   0.6055 | 0.693  |    0.9213 |   0.8142 |  0.0919 |  729 |  171 |  475 | 3673 |
| GradientBoosting   | validation | 5072 |          0.2362 |         0.5 |      0.823  |   0.6444 | 0.7228 |    0.9327 |   0.8456 |  0.0825 |  772 |  166 |  426 | 3708 |
| GradientBoosting   | test       | 5048 |          0.2385 |         0.5 |      0.7996 |   0.6728 | 0.7307 |    0.9281 |   0.8302 |  0.0873 |  810 |  203 |  394 | 3641 |

Best model on test PR-AUC: **GradientBoosting** (PR-AUC 0.830,
ROC-AUC 0.928, recall 0.673). Accuracy is not
reported: with a 23.8% positive rate a trivial all-negative
classifier would score 76.2%.

Top features: `n_candidates_for_truck`, `competing_trucks`, `bundle_size`, `match_score`, `empty_km_avoided`.

### The result that matters — pruning vs optimality gap

|   threshold |   mean_pruned_pct |   mean_gap_pct |   worst_gap_pct |   instances_with_zero_gap |   mean_ms_full |   mean_ms_pruned |   n_instances |   speedup |
|------------:|------------------:|---------------:|----------------:|--------------------------:|---------------:|-----------------:|--------------:|----------:|
|        0    |            0      |         0      |          0      |                        20 |         8.0202 |           7.2298 |            20 |    1.1093 |
|        0.02 |           38.7638 |         0.0581 |          0.6693 |                        17 |         8.0202 |           6.0065 |            20 |    1.3353 |
|        0.05 |           54.4038 |         0.6786 |          4.8687 |                         7 |         8.0202 |           5.8933 |            20 |    1.3609 |
|        0.1  |           63.6069 |         2.5445 |          7.3593 |                         3 |         8.0202 |           5.1578 |            20 |    1.555  |
|        0.2  |           73.8218 |         7.8782 |         43.6223 |                         0 |         8.0202 |           5.0369 |            20 |    1.5923 |
|        0.3  |           79.2418 |        10.6522 |         43.7597 |                         0 |         8.0202 |           4.7216 |            20 |    1.6986 |
|        0.5  |           85.6062 |        20.7341 |         70.919  |                         0 |         8.0202 |           4.3243 |            20 |    1.8547 |
|        0.7  |           90.8877 |        32.3836 |         75.5467 |                         0 |         8.0202 |           4.1427 |            20 |    1.936  |

At a threshold of 0.02 the classifier discards **38.8%** of
candidates for a mean optimality gap of **0.058%**, leaving
17/20 instances exactly
optimal, at **1.34× speedup**. Beyond ~5% the gap grows fast.

**Honest conclusion: the ML layer is not why Truckly works.** The CP-SAT solve
already takes ~8 ms, so the practical gain at this problem
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

Estimated CO₂ per operating day: B0 **3,068 kg**,
TRUCKLY **3,348 kg** — an **increase**,
because absolute fuel burn rises when freight is carried.

The environmental case for backhaul matching is therefore **not** "the truck
burns less fuel". It is that the 15.9 loads carried on return legs
did not each require a separate dedicated vehicle movement. Measuring that
avoided-trip benefit properly requires modelling the counterfactual dedicated
journey, which is out of scope here and is named in Future Work.

Every CO₂ figure uses an **ASM** factor of
2.68 kg/L and is **estimated, never
observed**.

---

## 26. Driver Impact

Truckly must not buy company savings with unreasonable driver schedules. Duty
time is a hard constraint (max 10.0 h driving,
13.0 h duty, mandatory break after
5.0 h), and **on-time delivery held at
100.0%** — no deadline was ever missed,
because deadlines are enforced as hard constraints.

Mean duty time rose from 88.3 h to
125.0 h per fleet-day. That is the
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
**24.7%** and net cost by **18.6%**
against current practice in the simulated environment, and beat a naive greedy
matcher by a small but statistically reliable margin
(34.6 km/day, 95% CI [25.0, 44.3],
lower in 69/100 days) while serving
11.7% more loads at
2.1% lower net cost.

**The 60% aspiration was not achieved.** The honest headline is narrower and
more useful than that: *the value of freight matching is a function of how thick
the freight market is*. At 2 open loads per truck it is worth
10%; at 15 it is worth
44%. And the value of *optimisation over naive
matching* is real but modest — most of the benefit comes from matching at all,
with global optimisation adding a further few percent and a materially higher
service level.

The failure taxonomy points at what to fix: **detour_exceeded**
accounts for 47.9% of
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
