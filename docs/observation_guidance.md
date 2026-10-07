# TRUCKLY — Observation Guidance for the Five Poster Graphs

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
n = 3,000. Mean 149.8 km, median 134.6 km,
SD 71.5 km, IQR 84-208 km
(= 124 km), P90 255 km, max 302 km,
skewness 0.499. The top decile of journeys carries
**18.8%** of all empty kilometres. The
fleet burns 4,495 empty km per operating day.

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
LCV_3T: median Rs 2,087 (IQR 1,934) · RIGID_9T: median Rs 2,807 (IQR 2,738) · RIGID_16T: median Rs 3,451 (IQR 3,271) · ARTIC_25T: median Rs 4,084 (IQR 3,619).
Mean within-class IQR is about **Rs 2,890**, which is
LARGER than the **Rs 1,997** spread between the
smallest and largest class medians.
0 points fall beyond the 1.5×IQR fence.

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
Pearson r = 0.882, R² = 0.778,
Spearman ρ = 0.903, slope 0.2576 L/km,
n = 3,000. So roughly 78% of the variation in fuel is
accounted for by distance, and about 22% is not.
The supplementary panel (G3b) plots fuel **per km** against payload: r drops to
0.372, R² = 0.138, slope
0.0123 L/km per tonne carried.

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
- Payload t·km ↔ Detour km: ρ = +0.73
- Weight util % ↔ Detour km: ρ = +0.68
- Weight util % ↔ Empty km: ρ = -0.61
- Loaded km ↔ Empty km: ρ = -0.58
- Payload t·km ↔ Empty km: ρ = -0.55

Near-zero pairs: Total cost ₹↔Waiting h ρ=+0.03, Waiting h↔Fuel L ρ=-0.01, Driving h↔Waiting h ρ=-0.01.

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
n = 3,000. The distribution is **bimodal**:
52.7% of return legs sit at exactly 0% (those trucks
were not matched and ran home empty), and the matched legs form a second mode
with a median of 14.2%. Overall median
0.0%, mean 9.1%, P90 29.8%,
max 97.8%. **87.5%** of all legs fall
below the 25% under-utilisation threshold.

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
