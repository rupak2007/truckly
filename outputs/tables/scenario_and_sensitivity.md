# TRUCKLY — Scenario and Sensitivity Analysis

## Deliverable 19 — Scenario analysis (12 scenarios x 100 days each)

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

**The single most important row-to-row comparison is S1 -> S2 -> S3**
(shipment density 2 -> 6 -> 15 open loads per available truck). Truckly's
benefit is a FUNCTION of how thick the freight market is, not a constant.
Reporting it as a curve rather than a point is what makes the result robust
to the objection that the generator was tuned.

## Deliverable 20 — Sensitivity analysis (one-factor-at-a-time, R = 40)

| parameter                   |   value | is_base   |   empty_red_vs_B0_pct |   empty_red_vs_B2_pct |   net_cost_red_vs_B0_pct |   fuel_change_vs_B0_pct |   util_gain_pp |   served |
|:----------------------------|--------:|:----------|----------------------:|----------------------:|-------------------------:|------------------------:|---------------:|---------:|
| diesel_price_inr_per_litre  |   70    | False     |                 24.77 |                  1.39 |                    22.38 |                  -10.29 |           6.82 |    16.2  |
| diesel_price_inr_per_litre  |   80    | False     |                 24.79 |                  1.36 |                    20.36 |                  -10.13 |           6.81 |    16.1  |
| diesel_price_inr_per_litre  |   90    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| diesel_price_inr_per_litre  |  105    | False     |                 24.87 |                  1.41 |                    16.3  |                   -9.68 |           6.76 |    15.78 |
| diesel_price_inr_per_litre  |  120    | False     |                 24.72 |                  1.18 |                    14.41 |                   -9.1  |           6.7  |    15.38 |
| driver_wage_inr_per_hour    |   90    | False     |                 24.82 |                  1.4  |                    19.71 |                  -10.11 |           6.81 |    16.08 |
| driver_wage_inr_per_hour    |  110    | False     |                 24.82 |                  1.4  |                    19.14 |                  -10.11 |           6.81 |    16.08 |
| driver_wage_inr_per_hour    |  130    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| driver_wage_inr_per_hour    |  160    | False     |                 24.87 |                  1.44 |                    17.77 |                   -9.87 |           6.78 |    15.9  |
| driver_wage_inr_per_hour    |  200    | False     |                 24.87 |                  1.38 |                    16.73 |                   -9.7  |           6.77 |    15.75 |
| waiting_cost_multiplier     |    0    | False     |                 24.83 |                  1.41 |                    18.88 |                  -10.08 |           6.82 |    16.05 |
| waiting_cost_multiplier     |    0.5  | False     |                 24.83 |                  1.43 |                    18.73 |                  -10.08 |           6.81 |    16.05 |
| waiting_cost_multiplier     |    1    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| waiting_cost_multiplier     |    2    | False     |                 24.81 |                  1.36 |                    18.31 |                   -9.98 |           6.79 |    15.98 |
| waiting_cost_multiplier     |    3    | False     |                 24.74 |                  1.28 |                    18.06 |                   -9.96 |           6.77 |    15.95 |
| empty_km_penalty_inr_per_km |    0    | False     |                 24.67 |                  1.21 |                    18.59 |                   -9.99 |           6.82 |    16.08 |
| empty_km_penalty_inr_per_km |    3    | False     |                 24.77 |                  1.35 |                    18.59 |                  -10.03 |           6.8  |    16.05 |
| empty_km_penalty_inr_per_km |    6    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| empty_km_penalty_inr_per_km |   12    | False     |                 24.9  |                  1.46 |                    18.57 |                   -9.94 |           6.79 |    15.95 |
| empty_km_penalty_inr_per_km |   20    | False     |                 24.97 |                  1.51 |                    18.55 |                   -9.94 |           6.78 |    15.9  |
| tariff_inr_per_km           |   10    | False     |                 24.69 |                  1.17 |                    10.92 |                   -8.82 |           6.67 |    15.2  |
| tariff_inr_per_km           |   15    | False     |                 24.82 |                  1.3  |                    14.71 |                   -9.57 |           6.78 |    15.68 |
| tariff_inr_per_km           |   20    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| tariff_inr_per_km           |   28    | False     |                 24.75 |                  1.36 |                    24.86 |                  -10.29 |           6.81 |    16.2  |
| tariff_inr_per_km           |   36    | False     |                 24.7  |                  1.35 |                    31.17 |                  -10.62 |           6.82 |    16.35 |
| detour_tolerance            |    0.15 | False     |                 23.09 |                  1.43 |                    17.31 |                   -8.69 |           6.14 |    15.55 |
| detour_tolerance            |    0.25 | False     |                 23.43 |                  1.37 |                    17.56 |                   -8.89 |           6.22 |    15.68 |
| detour_tolerance            |    0.35 | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| detour_tolerance            |    0.5  | False     |                 25.98 |                  1.18 |                    19.51 |                  -11.74 |           7.32 |    16.75 |
| detour_tolerance            |    0.7  | False     |                 26.49 |                  1.19 |                    19.86 |                  -12.56 |           7.51 |    17.08 |
| shipment_density            |    2    | False     |                 10.44 |                  0.6  |                     7.48 |                   -4.6  |           2.87 |     6.9  |
| shipment_density            |    4    | False     |                 17.99 |                  1.22 |                    13.14 |                   -7.68 |           4.68 |    12.28 |
| shipment_density            |    6    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| shipment_density            |   10    | False     |                 34.45 |                  1.83 |                    26.67 |                  -11.96 |           9.36 |    21.15 |
| shipment_density            |   15    | False     |                 43.55 |                  2.34 |                    34.47 |                  -14.21 |          11.87 |    25.78 |
| deadline_slack_factor       |    1.15 | False     |                 16.63 |                  0.81 |                    13.02 |                   -7.52 |           4.96 |    13.82 |
| deadline_slack_factor       |    1.4  | False     |                 19.68 |                  0.96 |                    15.05 |                   -8.35 |           5.64 |    14.5  |
| deadline_slack_factor       |    1.8  | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| deadline_slack_factor       |    2.4  | False     |                 29.8  |                  1.4  |                    22.5  |                  -11.3  |           8.2  |    18.08 |
| deadline_slack_factor       |    3.2  | False     |                 35.5  |                  2.16 |                    27.83 |                  -13.13 |          10    |    21.55 |
| min_detour_allowance_km     |   20    | False     |                 23.93 |                  1    |                    17.49 |                   -8.05 |           6.32 |    13.85 |
| min_detour_allowance_km     |   40    | False     |                 24.26 |                  1.06 |                    17.79 |                   -8.51 |           6.43 |    14.52 |
| min_detour_allowance_km     |   60    | True      |                 24.84 |                  1.41 |                    18.58 |                  -10    |           6.8  |    16    |
| min_detour_allowance_km     |   90    | False     |                 25.61 |                  1.4  |                    19.37 |                  -11.75 |           7.26 |    17    |
| min_detour_allowance_km     |  120    | False     |                 26.73 |                  1.53 |                    20.09 |                  -13.42 |           7.63 |    17.5  |

### Tornado — which parameters move the result most

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

The dominant parameter is **shipment_density** (swing of 33.1 percentage points in
empty-km reduction across its tested range).
