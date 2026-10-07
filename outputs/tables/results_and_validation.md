# TRUCKLY — Results, 60% Target Analysis and Statistical Validation

Scenario **S0_base**. **R = 100 simulated operating days**, 30 trucks per day, 180 open loads per day.
Common random numbers: every policy saw the identical fleet, shipment pool,
network and per-arc fuel perturbation. The comparison is therefore PAIRED.

## Deliverable 16 — KPI results

| KPI                       | Unit   |   B0_empty |   B1_wait_2h |   B1_wait_6h |   B1_wait_12h |   B2_greedy |    TRUCKLY | Truckly vs B0   | Truckly vs B2   | Better when   | Improvement?   |
|:--------------------------|:-------|-----------:|-------------:|-------------:|--------------:|------------:|-----------:|:----------------|:----------------|:--------------|:---------------|
| Total km                  | km     |    4495    |     4836     |     4839     |      4839     |    4781     |   4801     | -6.8 %          | -0.4 %          | lower         | NO             |
| Empty km                  | km     |    4495    |     3553     |     3535     |      3535     |    3418     |   3383     | +24.7 %         | +1.0 %          | lower         | yes            |
| Empty km share            | %      |     100    |       73.5   |       73     |        73     |      71.5   |     70.4   | -29.60 pp       | -1.10 pp        | lower         | yes            |
| Loaded km                 | km     |       0    |     1283     |     1303     |      1303     |    1364     |   1418     | n/a             | +4.0 %          | higher        | --             |
| Fuel                      | L      |    1144.8  |     1254.4   |     1255.4   |      1255.4   |    1243.4   |   1249.2   | -9.1 %          | -0.5 %          | lower         | NO             |
| Fuel cost                 | INR    |  103034    |   112897     |   112983     |    112983     |  111902     | 112424     | -9.1 %          | -0.5 %          | lower         | NO             |
| Waiting time              | h      |       0    |        2.37  |        3.05  |         3.05  |       4.69  |      4.27  | n/a             | +9.0 %          | lower         | --             |
| Driver duty time          | h      |      88.3  |      121.2   |      122.4   |       122.4   |     122.6   |    125     | -41.6 %         | -2.0 %          | lower         | NO             |
| Weight utilisation        | %      |       0    |        5.65  |        5.73  |         5.73  |       6.34  |      6.81  | n/a             | +0.47 pp        | higher        | --             |
| Distance utilisation      | %      |       0    |       26.5   |       27     |        27     |      28.5   |     29.6   | n/a             | +1.10 pp        | higher        | --             |
| Backhaul fill rate        | %      |       0    |       46.8   |       47.6   |        47.6   |      47.4   |     47.3   | n/a             | -0.10 pp        | higher        | --             |
| Total cost                | INR    |  196706    |   211395     |   211635     |    211635     |  210487     | 211352     | -7.4 %          | -0.4 %          | lower         | NO             |
| Freight revenue           | INR    |       0    |    44039     |    44756     |     44756     |   46867     |  51179     | n/a             | +9.2 %          | higher        | --             |
| Net cost (cost - revenue) | INR    |  196706    |   167356     |   166879     |    166879     |  163620     | 160173     | +18.6 %         | +2.1 %          | lower         | yes            |
| Shipments served          | count  |       0    |       14.03  |       14.29  |        14.29  |      14.23  |     15.89  | n/a             | +11.7 %         | higher        | --             |
| On-time rate              | %      |     100    |      100     |      100     |       100     |     100     |    100     | +0.00 pp        | +0.00 pp        | higher        | NO             |
| Tonne-km per litre        | t.km/L |       0    |        2.643 |        2.682 |         2.682 |       2.959 |      3.175 | n/a             | +7.3 %          | higher        | --             |
| CO2 estimate              | kg     |    3068    |     3362     |     3364     |      3364     |    3332     |   3348     | -9.1 %          | -0.5 %          | lower         | NO             |
| Solve time per decision   | ms     |       0.01 |        0.15  |        0.14  |         0.14  |       0.2   |      0.58  | n/a             | n/a             | lower         | --             |

> **Reading the delta columns.** For level variables the delta is a
> **% reduction** (positive = TRUCKLY is lower). For variables already
> expressed in % the delta is in **percentage points** (signed change).
> Percentage deltas are always signed so that **positive = improvement**,
> whichever direction that is for the KPI. `Better when` states that
> `Improvement?` applies it, so no sign has to be interpreted by eye.
> Solve time is marked `n/a` because the B0 comparator is effectively zero
> and a percentage against it is meaningless.

## Deliverable 17 — 60% target analysis

The 60% figure was stated **before** the experiment as an aspirational
hypothesis. Each metric is reported separately. **No composite 'overall
savings' number is computed**, because averaging percentage reductions
across differently-scaled quantities is not meaningful.

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

> `pct_estimator_unstable = True` flags a metric where the ratio-of-sums
> and the mean-of-per-instance-ratios disagree by more than 5 points. That
> happens when the comparator is near zero in some days (waiting time is the
> case here), which makes the percentage form unreliable. **Read the absolute
> difference and its CI for those rows, not the percentage.**

## Deliverable 18 — Statistical validation

### Primary endpoint (pre-specified)

- **Empty-km reduction, TRUCKLY vs B2_greedy**, n = 100 paired days
- Mean paired difference: **34.6 km per operating day** (95% bootstrap CI [25.0, 44.3])
- Hodges-Lehmann estimate: **29.4 km**
- Rank-biserial correlation: **0.738**
- Wilcoxon signed-rank p = **1.46e-09**
- TRUCKLY lower in **69 / 100** days

> **Note on Cohen's dz.** Common random numbers deliberately shrink the SD of
> the paired difference, so dz is mechanically inflated relative to an unpaired
> or non-CRN design and is NOT comparable across designs. It is reported as a
> within-design descriptor only; the rank-biserial correlation and the raw
> difference in km are the effect sizes to quote.

### All comparisons

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

> Only the first row is a confirmatory test. Everything below it is
> **descriptive**, Holm-adjusted within the secondary family, and carries no
> significance claim. With R controllable by simulating more days, any
> non-zero difference can be made 'significant'; the CI and the effect size
> are the result, not the p-value.

## Deliverable 21 — Failure taxonomy (TRUCKLY, S0_base)

| reason                  |    n |   pct_of_trucks |
|:------------------------|-----:|----------------:|
| detour_exceeded         | 1437 |           47.9  |
| matched                 | 1420 |           47.33 |
| lost_to_competing_truck |  143 |            4.77 |

This is the answer to *when does Truckly fail?* — and it is the most
actionable table in the project.
