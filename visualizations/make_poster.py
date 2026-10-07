#!/usr/bin/env python3
"""TRUCKLY — Deliverable 6: the A3 statistical poster (PDF + PNG).

A3 portrait, 297 x 420 mm, designed to be read at print size.
Every graph carries a bordered HANDWRITTEN OBSERVATION box beneath it,
deliberately left EMPTY: the university requires the observations to be
handwritten, so no generated prose is placed in those boxes.
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "visualizations"))
from style import MUTED, GRID, BASELINE

FIG = os.path.join(HERE, "outputs", "figures")
TAB = os.path.join(HERE, "outputs", "tables")
OUT = os.path.join(HERE, "outputs", "poster")
os.makedirs(OUT, exist_ok=True)

A3_W, A3_H = 11.69, 16.54
PAGE, CARD = "#ffffff", "#fcfcfb"
NAVY, MID, PALE = "#0d366b", "#256abf", "#cde2fb"
INK, INK2 = "#0b0b0b", "#52514e"
WARN_BG, WARN_EC, WARN_INK = "#fdf6ef", "#eb6834", "#7a3a12"

F = json.load(open(os.path.join(TAB, "poster_findings.json")))
KPI = pd.read_csv(os.path.join(TAB, "kpi_results.csv"))
DESC = pd.read_csv(os.path.join(TAB, "descriptive_A_journey_level_BASELINE_B0.csv"))
SC = pd.read_csv(os.path.join(TAB, "scenario_analysis.csv"))

fig = plt.figure(figsize=(A3_W, A3_H), facecolor=PAGE)


def T(x, y, s, size=9, color=INK, weight="normal", ha="left", va="top"):
    fig.text(x, y, s, fontsize=size, color=color, fontweight=weight,
             ha=ha, va=va, zorder=10, linespacing=1.42)


def card(x, y, w, h, fc=CARD, ec=GRID, lw=1.0):
    fig.patches.append(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.006",
        transform=fig.transFigure, facecolor=fc, edgecolor=ec, linewidth=lw,
        zorder=-10, mutation_aspect=A3_W / A3_H))


def title(x, y, s, size=10.5, color=NAVY):
    T(x, y, s, size=size, color=color, weight="bold")


def image(path, x, y, w, h):
    ax = fig.add_axes([x, y, w, h], zorder=5)
    ax.imshow(mpimg.imread(path))
    ax.axis("off")
    ax.patch.set_alpha(0)


def obs_box(x, y, w, h):
    """Intentionally EMPTY — handwritten observations go here."""
    fig.patches.append(Rectangle((x, y), w, h, transform=fig.transFigure,
                                 facecolor="#ffffff", edgecolor=BASELINE,
                                 linewidth=1.2, linestyle=(0, (5, 3)), zorder=2))
    T(x + 0.007, y + h - 0.0035, "HANDWRITTEN OBSERVATION", size=6.2,
      color=MUTED, weight="bold")
    for i in range(1, 4):
        yy = y + h - 0.0105 - i * 0.0072
        if yy > y + 0.003:
            fig.lines.append(plt.Line2D([x + 0.010, x + w - 0.010], [yy, yy],
                                        transform=fig.transFigure,
                                        color="#edebe4", lw=0.6, zorder=3))


def table(x, y, w, h, cells, cols, widths, fs=6.5, first_left=True,
          bold_cols=()):
    ax = fig.add_axes([x, y, w, h], zorder=6)
    ax.axis("off"); ax.patch.set_alpha(0)
    tb = ax.table(cellText=cells, colLabels=cols, cellLoc="right",
                  colWidths=widths, loc="center")
    tb.auto_set_font_size(False); tb.set_fontsize(fs)
    nrow = len(cells) + 1
    for (r, c), cell in tb.get_celld().items():
        cell.set_height(1.0 / nrow)
        cell.set_edgecolor("#e9e8e4"); cell.set_linewidth(0.6)
        if r == 0:
            cell.set_text_props(weight="bold", color="#ffffff", ha="center")
            cell.set_facecolor(MID)
        else:
            cell.set_facecolor("#f4f4f1" if r % 2 == 0 else "#ffffff")
            if c in bold_cols:
                cell.set_text_props(weight="bold")
        if c == 0 and first_left:
            cell.set_text_props(ha="left")
    return tb


# =========================================================================
# HEADER
# =========================================================================
card(0.028, 0.928, 0.944, 0.062, fc=NAVY, ec=NAVY)
T(0.5, 0.983, "TRUCKLY", size=34, color="#ffffff", weight="bold", ha="center")
T(0.5, 0.955, "Statistical Analysis of Freight Truck Journey Optimisation",
  size=13.5, color=PALE, ha="center")
T(0.5, 0.940, "A simulation–optimisation study of empty return journeys on the "
              "Chennai · Bengaluru · Coimbatore freight corridor",
  size=8.6, color="#9ec5f4", ha="center")

# =========================================================================
# 1 / 2 / 3
# =========================================================================
Y, H = 0.836, 0.084
for i, (x, head, body) in enumerate([
    (0.028, "1 · PROBLEM STATEMENT",
     "A truck delivers Chennai → Bengaluru. With no return load it\n"
     "drives back EMPTY, or idles waiting for one. Both waste fuel,\n"
     "capacity, driver hours and money, and add avoidable vehicle-\n"
     "kilometres and CO₂.\n\n"
     "Under the baseline policy modelled here 100% of return\n"
     f"kilometres are empty: a mean of {F['graph1']['mean_km']:.0f} km per truck and\n"
     f"{F['graph1']['total_empty_km_per_day']:,.0f} km per 30-truck operating day."),
    (0.3453, "2 · OBJECTIVE",
     "RQ — Can intelligent freight matching and route optimisation\n"
     "reduce empty truck kilometres while keeping deliveries\n"
     "feasible and improving fleet efficiency?\n\n"
     "Formally a SELECTIVE Pickup-and-Delivery Problem with Time\n"
     "Windows: choose which loads to accept, assign them to trucks\n"
     "and route each truck — minimising cost subject to capacity,\n"
     "time windows, detour tolerance and driver-hours limits."),
    (0.6626, "3 · DATASET",
     "⚠  THE FREIGHT RECORDS ARE SIMULATED. They are NOT\n"
     "observations of real Indian freight.\n\n"
     "OBS   40 node coordinates, real (OpenStreetMap)\n"
     "SIM   18,000 shipments · 3,000 truck-journeys\n"
     "         100 simulated operating days × 30 trucks\n"
     "DRV   distances · fuel · cost · utilisation · CO₂\n"
     "ASM   circuity · speeds · fuel curve · tariffs · driver rules\n"
     "Seeded and reproducible: same seed ⇒ identical data."),
]):
    card(x, Y, 0.3094, H)
    title(x + 0.012, Y + H - 0.009, head, size=9.8)
    T(x + 0.012, Y + H - 0.024, body, size=7.3, color=INK2)

# =========================================================================
# 4 DESCRIPTIVE STATISTICS
# =========================================================================
Y, H = 0.728, 0.098
card(0.028, Y, 0.944, H)
title(0.040, Y + H - 0.009, "4 · DESCRIPTIVE STATISTICS", size=9.8)
T(0.285, Y + H - 0.0095,
  "baseline B0 (empty return)  ·  n = 3,000 truck-journeys  ·  scenario S0_base",
  size=7.0, color=MUTED)
keep = ["total_distance_km", "empty_distance_km", "fuel_litres", "fuel_cost_inr",
        "driving_time_hr", "duty_time_hr", "total_cost_inr", "co2_kg"]
d = DESC[DESC.Variable.isin(keep)].set_index("Variable").loc[keep].reset_index()
d = d[["Variable", "Unit", "Mean", "SD", "Min", "P10", "Q1 (P25)",
       "Median (P50)", "Q3 (P75)", "P90", "Max", "IQR"]]
cells = [[r[0].replace("_", " "), r[1]] + [f"{v:,.1f}" for v in r[2:]]
         for r in d.values]
table(0.038, Y + 0.006, 0.924, H - 0.026, cells,
      ["Variable", "Unit", "Mean", "SD", "Min", "P10", "Q1", "Median", "Q3",
       "P90", "Max", "IQR"],
      [0.155, 0.058] + [0.079] * 10, fs=6.8)

# =========================================================================
# 5 THE FIVE GRAPHS
# =========================================================================
title(0.028, 0.7235, "5 · STATISTICAL VISUALISATIONS", size=9.8)
T(0.295, 0.7225, "five required panels + one supplementary  ·  the observation box under "
                 "each panel is left blank for handwriting", size=6.9, color=MUTED)

GW, GH, OH, PAD = 0.4622, 0.1040, 0.0300, 0.0130
COLX = (0.028, 0.5098)
ROWY = (0.5455, 0.3825, 0.2195)
PANELH = GH + OH + 0.026     # 0.160

g1, g2, g3, g4, g5 = (F["graph1"], F["graph2"], F["graph3"], F["graph4"], F["graph5"])
n_out = sum(r["n_outliers"] for r in g2["by_type"])
top3 = ", ".join(f"{a}↔{b} ρ={r:+.2f}"
                 for a, b, r in g4["strongest_non_definitional"][:2])

PANELS = [
    (COLX[0], ROWY[0], "01_empty_distance_histogram.png",
     "G1 · HISTOGRAM — empty_distance_km",
     f"right-skewed (skew {g1['skew']:.2f}); mean {g1['mean_km']:.0f} km > median "
     f"{g1['median_km']:.0f} km; IQR {g1['iqr']:.0f} km;\ntop decile carries "
     f"{g1['pct_of_empty_km_in_top_decile']:.0f}% of all empty kilometres"),
    (COLX[1], ROWY[0], "02_fuel_cost_boxplot.png",
     "G2 · BOX PLOT — fuel_cost_inr by truck_type",
     f"within-class IQR (~₹{g2['within_class_iqr_mean']:,.0f}) EXCEEDS the between-class\n"
     f"median range (₹{g2['between_class_median_range']:,.0f}); {n_out} points beyond the 1.5×IQR fence"),
    (COLX[0], ROWY[1], "03_distance_vs_fuel.png",
     "G3 · SCATTER — distance vs fuel, coloured by payload",
     f"Pearson r = {g3['pearson_r']:.3f}, R² = {g3['r2']:.3f}, Spearman ρ = {g3['spearman']:.3f};\n"
     "relationship is PARTLY STRUCTURAL by construction — see caption"),
    (COLX[1], ROWY[1], "04_correlation_heatmap.png",
     "G4 · CORRELATION HEATMAP — Spearman ρ",
     f"strongest non-definitional pairs: {top3};\ndefinitional identities are masked, "
     "not reported as findings"),
    (COLX[0], ROWY[2], "05_utilisation_distribution.png",
     "G5 · DISTRIBUTION — utilisation_weight_pct",
     f"BIMODAL: {g5['pct_exactly_zero']:.0f}% exactly 0% (unmatched), median of matched "
     f"legs {g5['median_matched_pct']:.1f}%;\n{g5['pct_below_threshold']:.0f}% of legs below the "
     f"{g5['threshold']:.0f}% under-utilisation threshold"),
    (COLX[1], ROWY[2], "03b_payload_vs_fuel_per_km.png",
     "G3b · SUPPLEMENTARY — payload vs fuel intensity",
     f"dividing fuel by distance removes the trivial driver: r falls "
     f"{g3['pearson_r']:.2f} → {g3['g3b_pearson_r']:.2f},\nslope {g3['g3b_slope']:.4f} L/km per tonne carried"),
]
for x, y, img, head, finding in PANELS:
    card(x, y, GW, PANELH)
    title(x + 0.011, y + PANELH - 0.008, head, size=8.4)
    image(os.path.join(FIG, img), x + 0.009, y + OH + PAD, GW - 0.018, GH)
    T(x + 0.011, y + OH + PAD - 0.0015, "STATISTICAL FINDING:  " + finding,
      size=5.9, color=INK2)
    obs_box(x + 0.011, y + 0.005, GW - 0.022, OH - 0.006)

# =========================================================================
# 6 KEY FINDINGS  +  7 CONCLUSION
# =========================================================================
Y, H = 0.090, 0.120
card(0.028, Y, 0.615, H)
title(0.040, Y + H - 0.009, "6 · KEY FINDINGS — baseline vs TRUCKLY", size=9.8)
T(0.345, Y + H - 0.0095, "R = 100 paired days · common random numbers",
  size=6.8, color=MUTED)
show = ["Empty km", "Total km", "Fuel", "Net cost (cost - revenue)",
        "Weight utilisation", "Backhaul fill rate", "Shipments served",
        "On-time rate"]
k = KPI.set_index("KPI").loc[show].reset_index()
na = lambda v: "n/a" if (isinstance(v, float) and np.isnan(v)) or str(v) == "nan" else str(v)
cells = [[r[0].replace(" (cost - revenue)", " (net)"),
          f"{r[1]:,.1f}", f"{r[2]:,.1f}", f"{r[3]:,.1f}", na(r[4]), na(r[5])]
         for r in k[["KPI", "B0_empty", "B2_greedy", "TRUCKLY",
                     "Truckly vs B0", "Truckly vs B2"]].values]
table(0.038, Y + 0.006, 0.595, H - 0.026, cells,
      ["KPI", "B0 empty", "B2 greedy", "TRUCKLY", "vs B0", "vs B2"],
      [0.30, 0.145, 0.145, 0.145, 0.13, 0.13], fs=6.9, bold_cols=(4, 5))

card(0.6626, Y, 0.3094, H)
title(0.6746, Y + H - 0.009, "7 · CONCLUSION", size=9.8)
s0 = SC[SC.scenario == "S0_base"].iloc[0]
s1 = SC[SC.scenario == "S1_low_avail"].iloc[0]
s3 = SC[SC.scenario == "S3_high_avail"].iloc[0]
fuel_d = KPI.set_index("KPI").loc["Fuel", "Truckly vs B0"]
cost_d = KPI.set_index("KPI").loc["Total cost", "Truckly vs B0"]
T(0.6746, Y + H - 0.024,
  f"Optimised matching cut empty running by {s0.empty_red_vs_B0_pct:.1f}%\n"
  f"and net cost by {s0.net_cost_red_vs_B0_pct:.1f}% versus the empty-return\n"
  f"baseline, and beat a NAIVE GREEDY matcher by\n"
  f"{s0.empty_red_vs_B2_pct:.2f}% on empty km (Wilcoxon p<0.001, lower\n"
  f"in 69/100 days) and {s0.net_cost_red_vs_B2_pct:.1f}% on net cost.\n\n"
  f"The 60% aspiration was NOT reached on any metric.\n"
  f"The benefit is not a constant — it rises from\n"
  f"{s1.empty_red_vs_B0_pct:.0f}% at {s1.density:.0f} loads/truck to "
  f"{s3.empty_red_vs_B0_pct:.0f}% at {s3.density:.0f} loads/truck.\n\n"
  f"Fuel and gross cost ROSE ({fuel_d}, {cost_d}):\n"
  f"carrying freight burns more than running empty.\n"
  f"The gain is in NET cost and in utilisation.",
  size=7.0, color=INK2)

# =========================================================================
# 8 PROVENANCE & LIMITATIONS
# =========================================================================
Y, H = 0.010, 0.072
card(0.028, Y, 0.944, H, fc=WARN_BG, ec=WARN_EC, lw=1.4)
title(0.040, Y + H - 0.008, "8 · DATA PROVENANCE AND LIMITATIONS", size=9.8,
      color="#a8410f")
T(0.040, Y + H - 0.020,
  "OBS  observed / external — 40 node coordinates from OpenStreetMap / public gazetteer.\n"
  "SIM  simulated — ALL shipments, trucks, weights, time windows and journeys.\n"
  "DRV  derived — distances, fuel, cost, utilisation, CO₂ (from OBS + SIM + ASM).\n"
  "ASM  assumed — road circuity 1.18–1.35×, truck speeds, fuel curve, diesel ₹90/L,\n"
  "        tolls, wages, driver-hour rules, freight tariff, CO₂ factor 2.68 kg/L.\n"
  "        Every value is declared in config.yaml.", size=6.3, color=WARN_INK)
T(0.505, Y + H - 0.020,
  "LIMITATIONS\n"
  "•  No live routing engine was reachable from the build environment: road distance is\n"
  "    great-circle × a declared circuity factor, NOT traced road geometry.\n"
  "•  No real carrier freight records, no live traffic, no cancellations, no competing carriers.\n"
  "•  Single-leg return model; multi-day journey chains are out of scope.\n"
  "•  CO₂ is ESTIMATED from an assumed emission factor — it is not a measurement.\n"
  "•  Results are conditional on the generator: they describe the SIMULATED environment.",
  size=6.3, color=WARN_INK)

fig.savefig(os.path.join(OUT, "Truckly_A3_Statistical_Poster.pdf"),
            facecolor=PAGE, dpi=300)
fig.savefig(os.path.join(OUT, "Truckly_A3_Statistical_Poster.png"),
            facecolor=PAGE, dpi=160)
plt.close(fig)
print("poster written to", OUT)
