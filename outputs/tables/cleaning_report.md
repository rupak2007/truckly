# TRUCKLY — Data Cleaning & Validation Report

- journeys: **216,000 rows x 41 columns**
- shipments: **231,000 rows x 18 columns**
- instances: **1,200 rows x 13 columns**
- analysis frame written: `data/processed/truckly_clean.csv` (base scenario, 18,000 rows) and `truckly_clean.csv.gz` (all scenarios, 216,000 rows)

## 1. Validation checks

The `fires_on_corrupted_copy` column is the test of the test: a seeded
corrupted copy of the data is built and the same checks are re-run. A
check that does not fire there is not actually checking anything.

| check                                       |   violations | rule                                                                                                               | action_if_violated                                                     | fires_on_corrupted_copy   |
|:--------------------------------------------|-------------:|:-------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------|:--------------------------|
| C01_missing_values                          |            0 | no NaN in any journey or shipment column outside the declared nullable set ['match_score', 'matched_shipment_ids'] | flag row, do not drop; investigate generator branch                    | True                      |
| C01b_declared_nullable_only_where_unmatched |            0 | match_score is populated if and only if the truck was matched                                                      | score written for an unmatched truck -> bookkeeping fault              | True                      |
| C02_duplicate_keys                          |            0 | (scenario, instance, policy, truck) is unique in journeys                                                          | keep first, log the duplicate key                                      | True                      |
| C03_negative_quantities                     |            0 | distances, fuel, cost and times are non-negative                                                                   | quarantine row; a negative here is a code fault, not data noise        | True                      |
| C04_distance_identity                       |            0 | total_distance_km == loaded_distance_km + empty_distance_km                                                        | recompute from legs; never patch the aggregate                         | True                      |
| C05_cost_identity                           |            0 | total = variable + fixed; variable = fuel + driver + toll                                                          | recompute in CostModel; single source of truth                         | True                      |
| C06_utilisation_bounds                      |            0 | 0 <= utilisation <= 100 for both definitions                                                                       | >100% means payload exceeded capacity -> capacity constraint broken    | True                      |
| C07_capacity_respected                      |            0 | payload tonne-km never exceeds capacity tonne-km                                                                   | hard constraint violation; reject the route                            | True                      |
| C08_time_windows                            |            0 | delivery deadline is strictly after pickup ready time                                                              | regenerate the shipment; an inverted window is unservable              | True                      |
| C09_geographic_bounds                       |            0 | all coordinates inside the Indian bounding box (6-38N, 68-98E)                                                     | drop node from the network; a stray coordinate corrupts every matrix   | True                      |
| C10_od_distinct                             |            0 | shipment origin != destination                                                                                     | regenerate; a zero-length shipment is meaningless                      | True                      |
| C11_service_level_bounded                   |            0 | shipments served never exceeds shipments offered                                                                   | double-assignment bug in the optimiser                                 | True                      |
| C12_pairing_intact                          |            0 | every policy in an instance saw the same shipment pool (the paired-design precondition)                            | instance regenerated between policies -> pairing broken, analysis void | True                      |

**Result: 13/13 checks passed on the real data; 13/13 checks demonstrably fire on corrupted data.**

## 2. Data types

| column                   | dtype   |
|:-------------------------|:--------|
| total_distance_km        | float64 |
| loaded_distance_km       | float64 |
| empty_distance_km        | float64 |
| detour_distance_km       | float64 |
| payload_tonne_km         | float64 |
| capacity_tonne_km        | float64 |
| utilisation_weight_pct   | float64 |
| utilisation_distance_pct | float64 |
| driving_time_hr          | float64 |
| service_time_hr          | float64 |
| waiting_time_hr          | float64 |
| duty_time_hr             | float64 |
| fuel_litres              | float64 |
| fuel_cost_inr            | float64 |
| driver_cost_inr          | float64 |
| toll_cost_inr            | float64 |
| variable_cost_inr        | float64 |
| fixed_cost_inr           | float64 |
| total_cost_inr           | float64 |
| revenue_inr              | float64 |
| net_cost_inr             | float64 |
| co2_kg                   | float64 |
| avg_payload_tonnes       | float64 |
| n_shipments_matched      | int64   |
| late_deliveries          | int64   |
| lateness_minutes         | float64 |
| scenario_id              | str     |
| instance_id              | int64   |
| policy                   | str     |
| truck_id                 | str     |
| truck_type               | str     |
| truck_capacity_kg        | int64   |
| current_node             | str     |
| home_node                | str     |
| direct_return_km         | float64 |
| matched_shipment_ids     | str     |
| route_node_sequence      | str     |
| match_score              | float64 |
| unmatched_reason         | str     |
| solver_status            | str     |
| solve_time_ms            | float64 |

## 3. Numeric ranges

| column                   |       min |       max |   n_missing |
|:-------------------------|----------:|----------:|------------:|
| total_distance_km        |    60.221 |   401.656 |           0 |
| loaded_distance_km       |     0     |   357.58  |           0 |
| empty_distance_km        |     0     |   330.762 |           0 |
| detour_distance_km       |     0     |   121.099 |           0 |
| payload_tonne_km         |     0     |  3943.85  |           0 |
| capacity_tonne_km        |   180.662 | 10033.7   |           0 |
| utilisation_weight_pct   |     0     |    99.84  |           0 |
| utilisation_distance_pct |     0     |   100     |           0 |
| driving_time_hr          |     1.255 |     8.076 |           0 |
| service_time_hr          |     0     |     3.797 |           0 |
| waiting_time_hr          |     0     |     4.462 |           0 |
| duty_time_hr             |     1.255 |    10.555 |           0 |
| fuel_litres              |     8.616 |   140.736 |           0 |
| fuel_cost_inr            |   775.426 | 12666.2   |           0 |
| driver_cost_inr          |   163.098 |  1372.16  |           0 |
| toll_cost_inr            |    96.353 |   642.649 |           0 |
| variable_cost_inr        |  1055.03  | 14442.3   |           0 |
| fixed_cost_inr           |  2500     |  2500     |           0 |
| total_cost_inr           |  3555.03  | 16942.3   |           0 |
| revenue_inr              |     0     | 21042.7   |           0 |
| net_cost_inr             | -7674.69  | 14468.3   |           0 |
| co2_kg                   |    23.09  |   377.172 |           0 |
| avg_payload_tonnes       |     0     |    17.966 |           0 |
| n_shipments_matched      |     0     |     2     |           0 |
| late_deliveries          |     0     |     0     |           0 |
| lateness_minutes         |     0     |     0     |           0 |
| instance_id              |     0     |    99     |           0 |
| truck_capacity_kg        |  3000     | 25000     |           0 |
| direct_return_km         |    60.221 |   302.008 |           0 |
| match_score              |    -0.525 |     1.881 |      181793 |
| solve_time_ms            |     0.003 |    32.648 |           0 |

## 4. Outlier analysis (1.5 x IQR convention)

**No row is deleted.** The 1.5xIQR rule is a display convention, not a
test of validity: a long empty return is unusual, not erroneous, and it is
exactly the observation the project exists to study. Deleting the tail
would remove the phenomenon.

| column                 |      Q1 |      Q3 |     IQR |   lower_fence |   upper_fence |   n_beyond_fence |   pct_beyond_fence |
|:-----------------------|--------:|--------:|--------:|--------------:|--------------:|-----------------:|-------------------:|
| total_distance_km      |   96.57 |  219.64 |  123.07 |        -88.03 |        404.24 |                0 |               0    |
| empty_distance_km      |   63.87 |  177.83 |  113.96 |       -107.08 |        348.77 |                0 |               0    |
| fuel_litres            |   23.18 |   54.83 |   31.64 |        -24.28 |        102.29 |             2593 |               1.2  |
| fuel_cost_inr          | 2086.54 | 4934.52 | 2847.97 |      -2185.42 |       9206.48 |             2593 |               1.2  |
| waiting_time_hr        |    0    |    0    |    0    |          0    |          0    |            22617 |              10.47 |
| total_cost_inr         | 5101.51 | 8405.63 | 3304.12 |        145.33 |      13361.8  |             2100 |               0.97 |
| utilisation_weight_pct |    0    |    8.03 |    8.03 |        -12.05 |         20.08 |            23621 |              10.94 |
| driving_time_hr        |    2.04 |    4.13 |    2.09 |         -1.09 |          7.27 |              511 |               0.24 |

## 5. Transformations applied (every one, explicitly)

| # | Transformation | Reason | Rows affected |
|---|---|---|---|
| 1 | Left-join instance metadata onto journeys | brings `n_shipments_offered`, `shipment_density`, seed and config hash to the analysis grain | all |
| 2 | Derived `is_matched` | binary backhaul fill indicator | all |
| 3 | Derived `empty_share_pct` | scale-free empty-running measure | all |
| 4 | Derived `cost_per_tonne_km`, `tonne_km_per_litre` | standard freight productivity metrics; undefined (NaN) where no freight was carried | 130,575 set to NaN by design |
| 5 | Derived `fuel_l_per_km` | removes distance as the trivial driver for Graph 3b | all |
| 6 | Derived `policy_family` | grouping key for the B1 wait variants | all |
| 7 | **No rows dropped, no values imputed, no outliers winsorised** | nothing in the validation suite justified it | 0 |

## 6. What was NOT done, and why

- **No imputation.** There are no missing values; imputing would invent data.
- **No outlier removal.** See section 4.
- **No winsorising or log-transform of the stored data.** Transformations belong in the analysis step, not in the stored dataset, so every figure can be traced back to raw quantities.
- **No de-duplication.** No duplicates exist; the check is retained because a future change to the seeding scheme could introduce them silently.
