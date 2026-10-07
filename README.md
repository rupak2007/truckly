# TRUCKLY — Optimising Freight Trucks' Journeys

A **simulation–optimisation decision-support system** for backhaul freight
matching, with a controlled four-policy experiment, statistical validation,
scenario and sensitivity analysis, a failure taxonomy, an honest ML extension,
a working demo and an A3 statistical poster.

> ⚠️ **The freight records in this project are SIMULATED.** Only the 40 node
> coordinates are real. No result here is an observation of Indian road freight.

## Headline results

| | vs B0 (empty return) | vs B2 (naive greedy) |
|---|---|---|
| Empty kilometres | **−24.7%** | **−1.01%** |
| Net cost (cost − revenue) | **−18.6%** | **−2.1%** |
| Loads served | +15.9/day | **+11.7%** |
| Weight utilisation | +6.81 pp | +0.47 pp |
| Fuel | **+9.1% (INCREASE)** | +0.5% |

Primary endpoint: mean paired difference **34.6 empty km/day**
(95% bootstrap CI [25.0, 44.3], Wilcoxon p =
1.5e-09, lower in 69/100
paired days).

**The 60% aspirational target was not reached on any metric**, and the benefit
is not constant — it rises from 10% at 2
open loads per truck to 44% at 15.

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

Master seed `20260816` in `config.yaml`. Every instance is a
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
