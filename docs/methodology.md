# TRUCKLY — Methodology

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

    P(o -> d)  proportional to  w_o * w_d / dist(o,d)^beta,   beta = 1.8

This matters substantively, not cosmetically. Uniform OD sampling over 40 nodes
spreads freight across 1,560 lanes, no corridor ever concentrates, and backhaul
matching becomes impossible for reasons that are an artefact of the sampler
rather than a property of freight. The gravity model concentrates flow onto
short and medium lanes between high-weight nodes, which is what real road
freight does.

Demand is **asymmetric**: a fraction 0.62
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
tonne, rho_a a per-arc road-difficulty index, gamma = 6.0,
and eps a lognormal perturbation with sigma = 0.085
representing driver behaviour, weather and vehicle condition.

The load term is not decoration. A distance-only fuel model would make an empty
kilometre and a loaded kilometre cost the same, and the entire economic premise
of backhaul matching would collapse.

## 5. Optimisation

**Master problem** — prize-collecting set packing with an outside option:

    min  sum_{k,b} (c_kb - rev_b) y_kb  +  sum_k c_k^empty z_k
    s.t. sum_b y_kb + z_k = 1              for every truck k        (C1)
         sum_{k,b : r in b} y_kb <= 1     for every request r      (C2)
         y, z in {0,1}

where `c_kb` is the journey objective for truck k serving bundle b and `rev_b`
is the freight revenue of the bundle. Solved with **OR-Tools CP-SAT** to proven
optimality over the generated candidate set; the solver status is recorded on
every journey row so the claim is checkable.

The journey objective adds a **managerial empty-running penalty** of
Rs 6.0/km to accounting cost. It is
applied identically to every policy, and reported money figures exclude it, so
the rupee columns stay real. The cost-component ablation reports results with
this term set to zero.

**Routing sub-problem** — for a bundle of k requests there are (2k)!/2^k
precedence-valid orderings (2 for k=1, 6 for k=2, 90 for k=3). All are
enumerated exactly, so the route for any accepted bundle is **provably optimal**
and faster than invoking a routing solver. Constraints enforced along the route:
time propagation, waiting at pickups before the ready time, weight and volume
capacity on every arc, hard delivery deadlines, a detour budget of
`max(theta * d_ret, 60.0 km)`,
remaining legal driving hours, total duty hours, and a mandatory break after
5.0 h of driving.

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
