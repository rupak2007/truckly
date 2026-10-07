#!/usr/bin/env python3
"""TRUCKLY — Deliverable 5: the five poster figures (+ one supplementary).

Every figure is generated from data/processed/truckly_clean.csv, so each can be
regenerated without re-running the experiment.
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from scipy import stats

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "visualizations"))
from style import (SURFACE, INK, INK2, MUTED, GRID, BASELINE, BLUE, ORANGE,
                   AQUA, YELLOW, RED, VIOLET, SEQ, clean_axes, fd_bins,
                   caption, save)

PROC = os.path.join(HERE, "data", "processed")
FIG = os.path.join(HERE, "outputs", "figures")
TAB = os.path.join(HERE, "outputs", "tables")
os.makedirs(FIG, exist_ok=True)
FINDINGS = {}

df = pd.read_csv(os.path.join(PROC, "truckly_clean.csv"))
B0 = df[df.policy == "B0_empty"].copy()
TR = df[df.policy == "TRUCKLY"].copy()
UNDER = 25.0


# ===========================================================================
def graph1():
    v = B0.empty_distance_km.values
    n, h = fd_bins(v)
    mean, med = v.mean(), np.median(v)
    q1, q3 = np.percentile(v, [25, 75])
    p90 = np.percentile(v, 90)
    top_decile_share = 100 * v[v >= p90].sum() / v.sum()

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.hist(v, bins=n, color=BLUE, edgecolor=SURFACE, linewidth=0.6, alpha=0.95)
    ax.axvspan(q1, q3, color=BLUE, alpha=0.10, zorder=0)
    ax.axvline(med, color=INK, lw=2.0, label=f"Median  {med:,.0f} km")
    ax.axvline(mean, color=ORANGE, lw=2.0, ls="--", label=f"Mean  {mean:,.0f} km")
    ax.set_xlabel("Empty return distance per truck-journey (km)")
    ax.set_ylabel("Number of truck-journeys")
    ax.set_title("Distribution of empty return distance — baseline B0")
    ax.legend(loc="upper right")
    ax.text(0.985, 0.60, f"IQR shaded\n{q1:,.0f} – {q3:,.0f} km",
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            color=INK2)
    clean_axes(ax)
    caption(fig, f"n = {len(v):,} truck-journeys, 100 simulated operating days. "
                 f"Freedman–Diaconis bin width = {h:.1f} km ({n} bins). "
                 "SIMULATED freight on real node coordinates.", y=-0.02)
    save(fig, os.path.join(FIG, "01_empty_distance_histogram.png"))
    FINDINGS["graph1"] = dict(
        n=int(len(v)), mean_km=round(mean, 1), median_km=round(med, 1),
        sd_km=round(v.std(ddof=1), 1), q1=round(q1, 1), q3=round(q3, 1),
        iqr=round(q3 - q1, 1), p90=round(p90, 1), max_km=round(v.max(), 1),
        skew=round(stats.skew(v), 3),
        pct_of_empty_km_in_top_decile=round(top_decile_share, 1),
        total_empty_km_per_day=round(v.sum() / B0.instance_id.nunique(), 0))


# ===========================================================================
def graph2():
    order = ["LCV_3T", "RIGID_9T", "RIGID_16T", "ARTIC_25T"]
    data = [B0[B0.truck_type == t].fuel_cost_inr.values for t in order]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    bp = ax.boxplot(data, tick_labels=[t.replace("_", " ") for t in order],
                    patch_artist=True, widths=0.55, showfliers=True,
                    medianprops=dict(color=INK, lw=2.0),
                    whiskerprops=dict(color=BASELINE, lw=1.2),
                    capprops=dict(color=BASELINE, lw=1.2),
                    flierprops=dict(marker="o", markersize=3.2,
                                    markerfacecolor=MUTED,
                                    markeredgecolor="none", alpha=0.45))
    for patch, c in zip(bp["boxes"], [SEQ[1], SEQ[2], SEQ[3], SEQ[5]]):
        patch.set_facecolor(c)
        patch.set_edgecolor(SURFACE)
        patch.set_linewidth(2.0)
    stat_rows = []
    for i, t in enumerate(order):
        v = data[i]
        q1, q3 = np.percentile(v, [25, 75])
        iqr = q3 - q1
        nout = int(((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)).sum())
        # direct label (relief rule: these fills are below 3:1 on the surface)
        ax.text(i + 1, np.median(v), f"{np.median(v):,.0f}", ha="center",
                va="bottom", fontsize=9, color=INK, fontweight="bold")
        stat_rows.append(dict(truck_type=t, n=len(v), median=round(np.median(v)),
                              Q1=round(q1), Q3=round(q3), IQR=round(iqr),
                              n_outliers=nout,
                              pct_outliers=round(100 * nout / len(v), 1)))
    ax.set_ylabel("Fuel cost per journey (₹)")
    ax.set_xlabel("Vehicle class")
    ax.set_title("Fuel cost by vehicle class — baseline B0")
    clean_axes(ax)
    caption(fig, f"n = {len(B0):,} truck-journeys. Box = Q1–Q3, whiskers = "
                 "1.5×IQR, points beyond = unusual, NOT erroneous. "
                 "Medians labelled directly.", y=-0.02)
    save(fig, os.path.join(FIG, "02_fuel_cost_boxplot.png"))
    FINDINGS["graph2"] = dict(by_type=stat_rows,
                              within_class_iqr_mean=round(
                                  np.mean([r["IQR"] for r in stat_rows])),
                              between_class_median_range=round(
                                  max(r["median"] for r in stat_rows)
                                  - min(r["median"] for r in stat_rows)))


# ===========================================================================
def graph3():
    d = TR.copy()
    x, y, c = d.total_distance_km.values, d.fuel_litres.values, d.avg_payload_tonnes.values
    r_p, _ = stats.pearsonr(x, y)
    r_s, _ = stats.spearmanr(x, y)
    slope, icept, rval, _, _ = stats.linregress(x, y)

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    sc = ax.scatter(x, y, c=c, cmap="viridis", s=13, alpha=0.72,
                    linewidths=0.4, edgecolors=SURFACE)
    xs = np.linspace(x.min(), x.max(), 100)
    ax.plot(xs, icept + slope * xs, color=INK, lw=2.0, zorder=5)
    cb = fig.colorbar(sc, ax=ax, pad=0.015)
    cb.set_label("Mean payload over loaded arcs (t)", color=INK2, fontsize=9.5)
    cb.outline.set_visible(False)
    ax.set_xlabel("Total journey distance (km)")
    ax.set_ylabel("Fuel consumed (L)")
    ax.set_title("Distance vs fuel, coloured by payload — TRUCKLY journeys")
    ax.text(0.025, 0.965, f"Pearson r = {r_p:.3f}\nR² = {rval**2:.3f}\n"
                          f"Spearman ρ = {r_s:.3f}",
            transform=ax.transAxes, va="top", ha="left", fontsize=9.5,
            color=INK, bbox=dict(fc=SURFACE, ec=GRID, boxstyle="round,pad=0.4"))
    clean_axes(ax)
    caption(fig,
            "STRUCTURAL-DEPENDENCE NOTE: fuel is simulated from a load-dependent "
            "consumption model with stochastic perturbation, so the distance–fuel "
            "association is PARTLY STRUCTURAL BY CONSTRUCTION. r and R² are "
            "descriptive; no confidence band or p-value is shown because "
            "truck-journeys within a simulated day are not independent.", y=-0.02)
    save(fig, os.path.join(FIG, "03_distance_vs_fuel.png"))

    # ---- 3b: the stronger panel ------------------------------------------
    d2 = TR[TR.avg_payload_tonnes > 0].copy()
    x2 = d2.avg_payload_tonnes.values
    y2 = (d2.fuel_litres / d2.total_distance_km).values
    r2p, _ = stats.pearsonr(x2, y2)
    s2, i2, r2v, _, _ = stats.linregress(x2, y2)
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.scatter(x2, y2, s=13, alpha=0.55, color=BLUE, linewidths=0.4,
               edgecolors=SURFACE)
    xs = np.linspace(x2.min(), x2.max(), 100)
    ax.plot(xs, i2 + s2 * xs, color=ORANGE, lw=2.2)
    ax.set_xlabel("Mean payload over loaded arcs (tonnes)")
    ax.set_ylabel("Fuel intensity (L per km)")
    ax.set_title("Payload vs fuel intensity — distance removed as a driver")
    ax.text(0.025, 0.965, f"Pearson r = {r2p:.3f}\nR² = {r2v**2:.3f}\n"
                          f"slope = {s2:.4f} L/km per tonne",
            transform=ax.transAxes, va="top", ha="left", fontsize=9.5, color=INK,
            bbox=dict(fc=SURFACE, ec=GRID, boxstyle="round,pad=0.4"))
    clean_axes(ax)
    caption(fig, f"n = {len(d2):,} loaded TRUCKLY journeys. Dividing fuel by "
                 "distance removes the trivial driver; what remains is the "
                 "load-and-conditions effect. Descriptive only.", y=-0.02)
    save(fig, os.path.join(FIG, "03b_payload_vs_fuel_per_km.png"))
    FINDINGS["graph3"] = dict(pearson_r=round(r_p, 3), r2=round(rval ** 2, 3),
                              spearman=round(r_s, 3), n=int(len(d)),
                              slope_l_per_km=round(slope, 4),
                              g3b_pearson_r=round(r2p, 3),
                              g3b_r2=round(r2v ** 2, 3),
                              g3b_slope=round(s2, 4), g3b_n=int(len(d2)))


# ===========================================================================
def graph4():
    cols = ["empty_distance_km", "loaded_distance_km", "detour_distance_km",
            "payload_tonne_km", "fuel_litres", "waiting_time_hr",
            "total_cost_inr", "utilisation_weight_pct", "driving_time_hr"]
    nice = ["Empty km", "Loaded km", "Detour km", "Payload t·km", "Fuel L",
            "Waiting h", "Total cost ₹", "Weight util %", "Driving h"]
    d = TR[cols]
    C = d.corr(method="spearman")

    # DEFINITIONAL pairs — related by an identity, not a finding
    defn = {("loaded_distance_km", "payload_tonne_km"),
            ("loaded_distance_km", "utilisation_weight_pct"),
            ("payload_tonne_km", "utilisation_weight_pct"),
            ("fuel_litres", "total_cost_inr"),
            ("empty_distance_km", "driving_time_hr"),
            ("loaded_distance_km", "driving_time_hr"),
            ("detour_distance_km", "loaded_distance_km"),
            ("driving_time_hr", "fuel_litres"),
            ("driving_time_hr", "total_cost_inr")}
    mask_def = np.zeros_like(C.values, dtype=bool)
    for a, b in defn:
        i, jx = cols.index(a), cols.index(b)
        mask_def[i, jx] = mask_def[jx, i] = True
    upper = np.triu(np.ones_like(C.values, dtype=bool), k=0)  # incl. diagonal

    fig, ax = plt.subplots(figsize=(7.6, 6.2))
    M = np.ma.array(C.values, mask=upper | mask_def)
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(cols)), nice, rotation=45, ha="right")
    ax.set_yticks(range(len(cols)), nice)
    for i in range(len(cols)):
        for jx in range(len(cols)):
            if upper[i, jx]:
                continue
            if mask_def[i, jx]:
                ax.add_patch(plt.Rectangle((jx - .5, i - .5), 1, 1,
                                           facecolor=GRID, edgecolor=SURFACE,
                                           lw=1.5))
                ax.text(jx, i, "def.", ha="center", va="center", fontsize=7.5,
                        color=MUTED)
            else:
                val = C.values[i, jx]
                ax.text(jx, i, f"{val:.2f}", ha="center", va="center",
                        fontsize=8.4,
                        color="white" if abs(val) > 0.55 else INK)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(False)
    ax.set_title("Spearman rank correlation — TRUCKLY journeys", pad=18)
    cb = fig.colorbar(im, ax=ax, shrink=0.75, pad=0.02)
    cb.set_label("Spearman ρ", color=INK2, fontsize=9.5)
    cb.outline.set_visible(False)
    ax.legend(handles=[Patch(facecolor=GRID, edgecolor=SURFACE,
                             label="grey  =  definitional identity, masked")],
              loc="lower left", bbox_to_anchor=(0.30, 0.86), frameon=False)
    caption(fig, f"n = {len(d):,} truck-journeys. Spearman chosen over Pearson "
                 "because several variables are right-skewed. Cells linked by an "
                 "arithmetic identity are masked — they are properties of the "
                 "definitions, not findings. Descriptive only; no p-values, "
                 "because journeys within a day are not independent.", y=-0.045)
    save(fig, os.path.join(FIG, "04_correlation_heatmap.png"))

    tri = []
    for i in range(len(cols)):
        for jx in range(i):
            if not mask_def[i, jx]:
                tri.append((nice[i], nice[jx], round(C.values[i, jx], 3)))
    tri.sort(key=lambda t: -abs(t[2]))
    FINDINGS["graph4"] = dict(n=int(len(d)), strongest_non_definitional=tri[:6],
                              weakest=tri[-3:])
    pd.DataFrame(tri, columns=["var_a", "var_b", "spearman_rho"]).to_csv(
        os.path.join(TAB, "correlation_non_definitional.csv"), index=False)


# ===========================================================================
def graph5():
    v = TR.utilisation_weight_pct.values
    vb = TR[TR.is_matched == 1].utilisation_weight_pct.values
    below = 100 * (v < UNDER).mean()
    zero = 100 * (v <= 1e-9).mean()

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    n, h = fd_bins(v[v > 0])
    ax.hist(v, bins=np.linspace(0, max(v.max(), 1), 46), density=True,
            color=BLUE, alpha=0.85, edgecolor=SURFACE, linewidth=0.6)
    kd = stats.gaussian_kde(vb, bw_method=0.28)
    xs = np.linspace(0, vb.max(), 300)
    ax.plot(xs, kd(xs) * (len(vb) / len(v)), color=ORANGE, lw=2.2,
            label="KDE, matched journeys only")
    ax.axvspan(0, UNDER, color=RED, alpha=0.07, zorder=0)
    ax.axvline(np.median(v), color=INK, lw=2.0,
               label=f"Median  {np.median(v):.1f} %")
    ax.set_xlabel("Weight utilisation of the return journey (%)")
    ax.set_ylabel("Density")
    ax.set_title("Return-leg capacity utilisation — TRUCKLY")
    ax.annotate(f"{below:.0f}% of journeys below {UNDER:.0f}%\n"
                f"(of which {zero:.0f} pp are exactly 0 — unmatched)",
                xy=(UNDER, ax.get_ylim()[1] * 0.55),
                xytext=(UNDER + 6, ax.get_ylim()[1] * 0.72),
                fontsize=9.2, color=INK,
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.2))
    ax.legend(loc="upper right")
    clean_axes(ax)
    caption(fig, f"n = {len(v):,} truck-journeys. Utilisation = payload-tonne-km "
                 "÷ capacity-tonne-km over the RETURN LEG ONLY (the outbound leg "
                 "is outside the model), so values are not round-trip figures. "
                 "Volume is ignored by this metric.", y=-0.02)
    save(fig, os.path.join(FIG, "05_utilisation_distribution.png"))
    FINDINGS["graph5"] = dict(
        n=int(len(v)), median_pct=round(float(np.median(v)), 2),
        mean_pct=round(float(v.mean()), 2),
        pct_below_threshold=round(below, 1), pct_exactly_zero=round(zero, 1),
        median_matched_pct=round(float(np.median(vb)), 2),
        p90=round(float(np.percentile(v, 90)), 2), max_pct=round(float(v.max()), 2),
        threshold=UNDER)


if __name__ == "__main__":
    graph1(); graph2(); graph3(); graph4(); graph5()
    json.dump(FINDINGS, open(os.path.join(TAB, "poster_findings.json"), "w"),
              indent=2)
    print("\nFINDINGS\n", json.dumps(FINDINGS, indent=2)[:2600])
