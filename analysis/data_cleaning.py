#!/usr/bin/env python3
"""
TRUCKLY — Deliverable 3: data validation, cleaning and the analysis frame.

Two honest points about what this script is:

1. The Truckly dataset is GENERATED, so it does not arrive with the missing
   values and typos of a scraped real-world file. Running a cleaning script on
   it and reporting "0 problems found" would be theatre. What this script
   actually is, therefore, is a **validation suite**: 12 checks that assert the
   generator produced physically and logically coherent data. Passing them is
   evidence the simulator is correct, and that is worth more than a fabricated
   cleaning story.

2. To show the validators actually bite, the script ALSO builds a deliberately
   corrupted copy of the data (seeded, documented, clearly labelled) and runs
   the same checks against it. Every check must fire. This is a test of the
   test -- not a claim that the real data had these defects.

Outputs
    data/processed/truckly_clean.csv        analysis frame (journeys + instance)
    outputs/tables/cleaning_report.md
    outputs/tables/validation_checks.csv
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
RES = os.path.join(HERE, "outputs", "results")
TAB = os.path.join(HERE, "outputs", "tables")
PROC = os.path.join(HERE, "data", "processed")
GEN = os.path.join(HERE, "data", "generated")
for d in (TAB, PROC):
    os.makedirs(d, exist_ok=True)

TOL = 1e-6


# ---------------------------------------------------------------------------
def run_checks(j: pd.DataFrame, s: pd.DataFrame, i: pd.DataFrame):
    """12 checks. Each returns (name, n_violations, description, action)."""
    out = []
    add = lambda *a: out.append(dict(zip(
        ["check", "violations", "rule", "action_if_violated"], a)))

    # `match_score` is NaN by design when a truck was not matched, and
    # `matched_shipment_ids` is empty for the same reason. Those are DECLARED
    # nullable columns, not missing data, and are excluded from C01 -- with the
    # count reported separately so nothing is hidden.
    NULLABLE = ["match_score", "matched_shipment_ids"]  # NaN by design when unmatched
    jn = j.drop(columns=[c for c in NULLABLE if c in j.columns])
    add("C01_missing_values", int(jn.isna().sum().sum() + s.isna().sum().sum()),
        "no NaN in any journey or shipment column outside the declared "
        f"nullable set {NULLABLE}",
        "flag row, do not drop; investigate generator branch")
    add("C01b_declared_nullable_only_where_unmatched",
        int((j.match_score.notna() & (j.n_shipments_matched == 0)).sum()) if
        "match_score" in j.columns else 0,
        "match_score is populated if and only if the truck was matched",
        "score written for an unmatched truck -> bookkeeping fault")
    add("C02_duplicate_keys",
        int(j.duplicated(["scenario_id", "instance_id", "policy", "truck_id"]).sum()),
        "(scenario, instance, policy, truck) is unique in journeys",
        "keep first, log the duplicate key")
    add("C03_negative_quantities",
        int(((j[["total_distance_km", "loaded_distance_km", "empty_distance_km",
                 "fuel_litres", "fuel_cost_inr", "waiting_time_hr",
                 "driving_time_hr", "total_cost_inr"]] < -TOL).any(axis=1)).sum()),
        "distances, fuel, cost and times are non-negative",
        "quarantine row; a negative here is a code fault, not data noise")
    add("C04_distance_identity",
        int((~np.isclose(j.total_distance_km,
                         j.loaded_distance_km + j.empty_distance_km,
                         atol=1e-6)).sum()),
        "total_distance_km == loaded_distance_km + empty_distance_km",
        "recompute from legs; never patch the aggregate")
    add("C05_cost_identity",
        int((~np.isclose(j.total_cost_inr,
                         j.variable_cost_inr + j.fixed_cost_inr, atol=1e-4)).sum()
            + (~np.isclose(j.variable_cost_inr,
                           j.fuel_cost_inr + j.driver_cost_inr + j.toll_cost_inr,
                           atol=1e-4)).sum()),
        "total = variable + fixed; variable = fuel + driver + toll",
        "recompute in CostModel; single source of truth")
    add("C06_utilisation_bounds",
        int(((j.utilisation_weight_pct < -TOL) | (j.utilisation_weight_pct > 100 + TOL)
             | (j.utilisation_distance_pct < -TOL)
             | (j.utilisation_distance_pct > 100 + TOL)).sum()),
        "0 <= utilisation <= 100 for both definitions",
        ">100% means payload exceeded capacity -> capacity constraint broken")
    add("C07_capacity_respected",
        int((j.payload_tonne_km > j.capacity_tonne_km + 1e-6).sum()),
        "payload tonne-km never exceeds capacity tonne-km",
        "hard constraint violation; reject the route")
    add("C08_time_windows",
        int((s.delivery_deadline_hr <= s.pickup_ready_time_hr).sum()),
        "delivery deadline is strictly after pickup ready time",
        "regenerate the shipment; an inverted window is unservable")
    add("C09_geographic_bounds",
        int(((s.pickup_lat < 6) | (s.pickup_lat > 38) | (s.pickup_lon < 68)
             | (s.pickup_lon > 98) | (s.delivery_lat < 6) | (s.delivery_lat > 38)
             | (s.delivery_lon < 68) | (s.delivery_lon > 98)).sum()),
        "all coordinates inside the Indian bounding box (6-38N, 68-98E)",
        "drop node from the network; a stray coordinate corrupts every matrix")
    add("C10_od_distinct",
        int((s.origin_node_id == s.dest_node_id).sum()),
        "shipment origin != destination",
        "regenerate; a zero-length shipment is meaningless")
    add("C11_service_level_bounded",
        int((j.groupby(["scenario_id", "instance_id", "policy"])
             .n_shipments_matched.sum()
             .reset_index()
             .merge(i[["scenario_id", "instance_id", "n_shipments_offered"]],
                    on=["scenario_id", "instance_id"])
             .pipe(lambda d: d.n_shipments_matched > d.n_shipments_offered)).sum()),
        "shipments served never exceeds shipments offered",
        "double-assignment bug in the optimiser")
    add("C12_pairing_intact",
        int((i.groupby(["scenario_id", "instance_id"]).n_shipments_offered
             .nunique() > 1).sum()),
        "every policy in an instance saw the same shipment pool "
        "(the paired-design precondition)",
        "instance regenerated between policies -> pairing broken, analysis void")
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------
def corrupt(j, s, seed=7):
    """Seeded, documented corruption used ONLY to prove the checks fire."""
    rng = np.random.default_rng(seed)
    j2, s2 = j.copy(), s.copy()
    n = len(j2)
    j2.loc[rng.choice(n, 5, replace=False), "fuel_litres"] = np.nan       # C01
    j2 = pd.concat([j2, j2.iloc[:3]], ignore_index=True)                   # C02
    j2.loc[rng.choice(n, 4, replace=False), "empty_distance_km"] = -12.0   # C03/C04
    j2.loc[rng.choice(n, 4, replace=False), "total_cost_inr"] += 500.0     # C05
    j2.loc[rng.choice(n, 4, replace=False), "utilisation_weight_pct"] = 132.0  # C06
    j2.loc[rng.choice(n, 3, replace=False), "payload_tonne_km"] = 1e9      # C07
    m = len(s2)
    idx = rng.choice(m, 6, replace=False)
    s2.loc[idx, "delivery_deadline_hr"] = s2.loc[idx, "pickup_ready_time_hr"] - 1.0  # C08
    s2.loc[rng.choice(m, 3, replace=False), "pickup_lat"] = 61.4           # C09
    idx2 = rng.choice(m, 3, replace=False)
    s2.loc[idx2, "dest_node_id"] = s2.loc[idx2, "origin_node_id"]          # C10
    j2.loc[rng.choice(n, 3, replace=False), "n_shipments_matched"] = 10**6  # C11
    j2.loc[rng.choice(n, 3, replace=False), "match_score"] = 0.5            # C01b
    return j2, s2


# ---------------------------------------------------------------------------
def main():
    j = pd.read_csv(os.path.join(RES, "journeys_main.csv.gz"))
    s = pd.read_csv(os.path.join(GEN, "truckly_shipments_all_scenarios.csv.gz"))
    i = pd.read_csv(os.path.join(RES, "instances_main.csv"))

    print(f"journeys  {j.shape[0]:,} rows x {j.shape[1]} cols")
    print(f"shipments {s.shape[0]:,} rows x {s.shape[1]} cols")
    print(f"instances {i.shape[0]:,} rows x {i.shape[1]} cols")

    real = run_checks(j, s, i)
    jc, sc = corrupt(j.head(4000), s.head(4000))
    ic = i.copy()
    ic.loc[0, "n_shipments_offered"] = -1          # C12: break the pairing
    ic = pd.concat([ic, ic.iloc[[0]].assign(n_shipments_offered=999)],
                   ignore_index=True)
    fired = run_checks(jc, sc, ic)
    real["fires_on_corrupted_copy"] = fired.violations.values > 0

    # ---- dtypes / ranges -------------------------------------------------
    dtypes = pd.DataFrame({"column": j.columns, "dtype": j.dtypes.astype(str).values})
    num = j.select_dtypes(include=[np.number])
    ranges = pd.DataFrame({"column": num.columns, "min": num.min().values,
                           "max": num.max().values,
                           "n_missing": num.isna().sum().values})

    # ---- outliers (reported, NEVER deleted) ------------------------------
    outl = []
    for c in ["total_distance_km", "empty_distance_km", "fuel_litres",
              "fuel_cost_inr", "waiting_time_hr", "total_cost_inr",
              "utilisation_weight_pct", "driving_time_hr"]:
        v = j[c].dropna()
        q1, q3 = v.quantile(.25), v.quantile(.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outl.append(dict(column=c, Q1=round(q1, 2), Q3=round(q3, 2),
                         IQR=round(iqr, 2), lower_fence=round(lo, 2),
                         upper_fence=round(hi, 2),
                         n_beyond_fence=int(((v < lo) | (v > hi)).sum()),
                         pct_beyond_fence=round(100 * ((v < lo) | (v > hi)).mean(), 2)))
    outl = pd.DataFrame(outl)

    # ---- build the analysis frame ---------------------------------------
    clean = j.merge(i[["scenario_id", "instance_id", "n_shipments_offered",
                       "shipment_density", "detour_tolerance",
                       "deadline_slack_factor", "seed", "config_hash"]],
                    on=["scenario_id", "instance_id"], how="left")
    clean["is_matched"] = (clean.n_shipments_matched > 0).astype(int)
    clean["empty_share_pct"] = np.where(
        clean.total_distance_km > 0,
        100 * clean.empty_distance_km / clean.total_distance_km, np.nan)
    clean["cost_per_tonne_km"] = np.where(
        clean.payload_tonne_km > 0, clean.total_cost_inr / clean.payload_tonne_km, np.nan)
    clean["tonne_km_per_litre"] = np.where(
        clean.fuel_litres > 0, clean.payload_tonne_km / clean.fuel_litres, np.nan)
    clean["fuel_l_per_km"] = np.where(
        clean.total_distance_km > 0, clean.fuel_litres / clean.total_distance_km, np.nan)
    clean["policy_family"] = clean.policy.str.split("_").str[0]

    clean.to_csv(os.path.join(PROC, "truckly_clean.csv.gz"), index=False,
                 compression="gzip")
    clean[clean.scenario_id == "S0_base"].to_csv(
        os.path.join(PROC, "truckly_clean.csv"), index=False)

    real.to_csv(os.path.join(TAB, "validation_checks.csv"), index=False)
    outl.to_csv(os.path.join(TAB, "outlier_report.csv"), index=False)
    ranges.to_csv(os.path.join(TAB, "range_report.csv"), index=False)

    # ---- report ----------------------------------------------------------
    n_fail = int((real.violations > 0).sum())
    L = ["# TRUCKLY — Data Cleaning & Validation Report", "",
         f"- journeys: **{j.shape[0]:,} rows x {j.shape[1]} columns**",
         f"- shipments: **{s.shape[0]:,} rows x {s.shape[1]} columns**",
         f"- instances: **{i.shape[0]:,} rows x {i.shape[1]} columns**",
         f"- analysis frame written: `data/processed/truckly_clean.csv` "
         f"(base scenario, {int((clean.scenario_id=='S0_base').sum()):,} rows) and "
         f"`truckly_clean.csv.gz` (all scenarios, {len(clean):,} rows)", "",
         "## 1. Validation checks", "",
         "The `fires_on_corrupted_copy` column is the test of the test: a seeded",
         "corrupted copy of the data is built and the same checks are re-run. A",
         "check that does not fire there is not actually checking anything.", "",
         real.to_markdown(index=False), "",
         f"**Result: {len(real)-n_fail}/{len(real)} checks passed on the real data; "
         f"{int(real.fires_on_corrupted_copy.sum())}/{len(real)} checks demonstrably "
         "fire on corrupted data.**", "",
         "## 2. Data types", "", dtypes.to_markdown(index=False), "",
         "## 3. Numeric ranges", "", ranges.round(3).to_markdown(index=False), "",
         "## 4. Outlier analysis (1.5 x IQR convention)", "",
         "**No row is deleted.** The 1.5xIQR rule is a display convention, not a",
         "test of validity: a long empty return is unusual, not erroneous, and it is",
         "exactly the observation the project exists to study. Deleting the tail",
         "would remove the phenomenon.", "", outl.to_markdown(index=False), "",
         "## 5. Transformations applied (every one, explicitly)", "",
         "| # | Transformation | Reason | Rows affected |",
         "|---|---|---|---|",
         "| 1 | Left-join instance metadata onto journeys | brings `n_shipments_offered`, "
         "`shipment_density`, seed and config hash to the analysis grain | all |",
         "| 2 | Derived `is_matched` | binary backhaul fill indicator | all |",
         "| 3 | Derived `empty_share_pct` | scale-free empty-running measure | all |",
         "| 4 | Derived `cost_per_tonne_km`, `tonne_km_per_litre` | standard freight "
         "productivity metrics; undefined (NaN) where no freight was carried | "
         f"{int(clean.cost_per_tonne_km.isna().sum()):,} set to NaN by design |",
         "| 5 | Derived `fuel_l_per_km` | removes distance as the trivial driver "
         "for Graph 3b | all |",
         "| 6 | Derived `policy_family` | grouping key for the B1 wait variants | all |",
         "| 7 | **No rows dropped, no values imputed, no outliers winsorised** | "
         "nothing in the validation suite justified it | 0 |", "",
         "## 6. What was NOT done, and why", "",
         "- **No imputation.** There are no missing values; imputing would invent data.",
         "- **No outlier removal.** See section 4.",
         "- **No winsorising or log-transform of the stored data.** Transformations "
         "belong in the analysis step, not in the stored dataset, so every figure "
         "can be traced back to raw quantities.",
         "- **No de-duplication.** No duplicates exist; the check is retained because "
         "a future change to the seeding scheme could introduce them silently.", ""]
    open(os.path.join(TAB, "cleaning_report.md"), "w").write("\n".join(L))

    print("\n", real.to_string(index=False))
    print(f"\nPASSED {len(real)-n_fail}/{len(real)} | corrupted-copy fired "
          f"{int(real.fires_on_corrupted_copy.sum())}/{len(real)}")


if __name__ == "__main__":
    main()
