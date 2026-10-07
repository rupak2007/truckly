# TRUCKLY — Pre-registered analysis plan

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
