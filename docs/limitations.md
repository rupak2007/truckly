# TRUCKLY — Limitations

Ordered by how much they threaten the conclusions. Nothing here is hidden in a
footnote; the first three are severe enough that the headline results must
always be quoted with them.

## 1. No live routing engine was reachable — road distance is modelled, not measured

The build environment had no network route to a routing service (a connection
attempt to the OSRM demo server returned no HTTP status at all). Rather than
fabricate road distances and label them observed, distance is computed as

    road_km = great_circle_km x circuity_factor

with circuity declared in `config.yaml` as 1.35x
below 50 km, 1.25x for 50-200 km and
1.18x above 200 km, and truck speeds of
38.0-55.0 km/h.
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

Diesel at Rs 90.0/L, driver wage Rs
130.0/h, toll Rs 1.6/km,
freight tariff Rs 20.0/km + Rs
3.0/t-km, and an empty-running management
penalty of Rs 6.0/km are all **ASM**.
The sensitivity analysis sweeps each; the tornado shows fuel price and wages
barely move the empty-km result (they move cost, not routing), while the tariff
strongly moves the net-cost result.

## 4. Single-leg model

Only the return leg is simulated. The outbound leg that put the truck where it
is, and any onward multi-day chain, are out of scope. Trucks whose direct
return exceeds 6.5 h of driving are
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
capped at bundles of size <= 2. A
monolithic model could in principle find solutions this decomposition misses.

## 7. CO2 is estimated, not measured

Emissions are `fuel_litres x 2.68` kg/L,
an **ASM** factor. Before submission this should be replaced with a cited
factor from a national inventory (e.g. DESNZ/Defra or US EPA) and the citation
recorded. No CO2 number in this project is an observation.

## 8. No live traffic, cancellations, breakdowns or rejections

Travel times are free-flow. Shipments never cancel, trucks never break down,
shippers never reject a carrier. Each of these would reduce realised benefit.

## 9. Driver rules are declared, not statutory

`max_driving_hours = 10.0`,
`max_duty_hours = 13.0`,
break after 5.0 h are **ASM**. They are
plausible, and they are enforced as hard constraints, but they were not taken
from a cited statutory instrument.

## 10. Statistical significance is cheap here

R is under our control. Simulating more days makes any non-zero difference
"significant". That is why the confidence interval and the effect size, not the
p-value, are reported as the result — and why only ONE confirmatory test is
run, with everything else explicitly descriptive.
