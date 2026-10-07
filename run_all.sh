#!/usr/bin/env bash
# TRUCKLY — full pipeline, from nothing to every deliverable. ~4 minutes.
set -e
cd "$(dirname "$0")"
echo "=== 1/9  experiment (12 scenarios x 100 days x 6 policies) ==="
python3 run_experiment.py --all --instances 100 --tag main
echo "=== 2/9  validation + analysis frame ==="
python3 analysis/data_cleaning.py
echo "=== 3/9  descriptive statistics ==="
python3 analysis/descriptive_statistics.py
echo "=== 4/9  KPI table, 60% target, statistical validation, failure taxonomy ==="
python3 analysis/statistical_tests.py
echo "=== 5/9  scenario + sensitivity analysis ==="
python3 analysis/scenario_analysis.py
echo "=== 6/9  ML extension ==="
python3 analysis/ml_candidate_pruning.py
echo "=== 7/9  figures + A3 poster ==="
python3 visualizations/make_poster_figures.py
python3 visualizations/make_result_figures.py
python3 visualizations/make_poster.py
echo "=== 8/9  documents, report, dashboard ==="
python3 make_documents.py
python3 make_report.py
python3 make_dashboard.py
echo "=== 9/9  demo ==="
python3 truckly_demo.py | head -50
echo; echo "DONE. See outputs/ and FINAL_REPORT.md"
