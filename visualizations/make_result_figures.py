#!/usr/bin/env python3
"""TRUCKLY — result figures: baseline-vs-Truckly, scenario curve, sensitivity
tornado, failure taxonomy, route map, ML pruning curve."""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "visualizations"))
sys.path.insert(0, HERE)
from style import (SURFACE, INK, INK2, MUTED, GRID, BASELINE, BLUE, ORANGE,
                   AQUA, YELLOW, RED, VIOLET, MAGENTA, SEQ, POLICY_COLOR,
                   POLICY_LABEL, clean_axes, caption, save)

TAB = os.path.join(HERE, "outputs", "tables")
FIG = os.path.join(HERE, "outputs", "figures")
PROC = os.path.join(HERE, "data", "processed")
GEN = os.path.join(HERE, "data", "generated")
os.makedirs(FIG, exist_ok=True)

K = pd.read_csv(os.path.join(TAB, "instance_kpis.csv"))
BASE = K[K.scenario_id == "S0_base"]
ORDER = ["B0_empty", "B1_wait_6h", "B2_greedy", "TRUCKLY"]


# ---------------------------------------------------------------------------
def fig_baseline_vs_truckly():
    specs = [("Empty kilometres", "empty_km", "km/day"),
             ("Net cost (cost − revenue)", "net_cost", "₹/day"),
             ("Fuel consumed", "fuel_l", "L/day"),
             ("Weight utilisation", "util_weight_pct", "%")]
    fig, axes = plt.subplots(1, 4, figsize=(16.4, 4.5))
    fig.subplots_adjust(wspace=0.42)
    for ax, (title, col, unit) in zip(axes, specs):
        means = [BASE[BASE.policy == p][col].mean() for p in ORDER]
        cis = []
        for p in ORDER:
            v = BASE[BASE.policy == p][col].values
            cis.append(1.96 * v.std(ddof=1) / np.sqrt(len(v)))
        cols = [POLICY_COLOR[p] for p in ORDER]
        bars = ax.bar(range(4), means, color=cols, width=0.68,
                      edgecolor=SURFACE, linewidth=2.0)
        ax.errorbar(range(4), means, yerr=cis, fmt="none", ecolor=INK2,
                    elinewidth=1.4, capsize=4)
        for i, (b, m) in enumerate(zip(bars, means)):
            ax.text(i, m, f"{m:,.0f}" if abs(m) > 20 else f"{m:,.2f}",
                    ha="center", va="bottom", fontsize=9.5, color=INK,
                    fontweight="bold", zorder=8)
        ax.margins(y=0.16)
        ax.tick_params(axis="y", pad=1)
        ax.set_xticks(range(4), ["B0", "B1", "B2", "TRUCKLY"], fontsize=9.5)
        ax.set_title(title, fontsize=11.5)
        ax.set_ylabel(unit)
        clean_axes(ax)
    handles = [Line2D([], [], marker="s", ls="", ms=9, color=POLICY_COLOR[p],
                      label=POLICY_LABEL[p]) for p in ORDER]
    fig.legend(handles=handles, loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, -0.07), frameon=False)
    fig.suptitle("Baseline policies vs TRUCKLY — per simulated operating day "
                 "(mean ± 95% CI, R = 100 paired days)",
                 fontsize=13.5, fontweight="bold", y=1.04)
    caption(fig, "Common random numbers: all four policies saw the identical fleet, "
                 "shipment pool and per-arc fuel perturbation.", y=-0.14)
    save(fig, os.path.join(FIG, "06_baseline_vs_truckly.png"))


# ---------------------------------------------------------------------------
def fig_scenario_density():
    S = pd.read_csv(os.path.join(TAB, "scenario_analysis.csv"))
    d = S[S.scenario.isin(["S1_low_avail", "S2_mod_avail", "S3_high_avail"])] \
        .sort_values("density")
    sens = pd.read_csv(os.path.join(TAB, "sensitivity_analysis.csv"))
    sd = sens[sens.parameter == "shipment_density"].sort_values("value")

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(sd.value, sd.empty_red_vs_B0_pct, marker="o", color=BLUE,
            label="Empty-km reduction vs B0")
    ax.plot(sd.value, sd.net_cost_red_vs_B0_pct, marker="s", color=ORANGE,
            label="Net-cost reduction vs B0")
    for x, y in zip(sd.value, sd.empty_red_vs_B0_pct):
        ax.annotate(f"{y:.0f}%", (x, y), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=9, color=INK)
    ax.axhline(60, color=MUTED, ls=":", lw=1.6)
    ax.text(sd.value.max(), 60.8, "60% aspirational target (hypothesis, not a claim)",
            ha="right", va="bottom", fontsize=9, color=MUTED)
    ax.set_xlabel("Shipment density (open loads offered per available truck)")
    ax.set_ylabel("Reduction vs empty-return baseline (%)")
    ax.set_title("TRUCKLY's benefit is a function of freight-market thickness")
    ax.set_ylim(0, 68)
    ax.legend(loc="lower right")
    clean_axes(ax)
    caption(fig, "R = 40 simulated days per density level, base scenario otherwise "
                 "unchanged. This curve is the project's most robust result: it "
                 "replaces a single fragile point estimate with a functional "
                 "relationship.", y=-0.02)
    save(fig, os.path.join(FIG, "07_benefit_vs_shipment_density.png"))


# ---------------------------------------------------------------------------
def fig_tornado():
    T = pd.read_csv(os.path.join(TAB, "sensitivity_tornado.csv"))
    T = T.sort_values("empty_swing_pp")
    base = pd.read_csv(os.path.join(TAB, "sensitivity_analysis.csv"))
    centre = float(base[base.is_base].empty_red_vs_B0_pct.mean())
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    y = np.arange(len(T))
    ax.barh(y, T.max_empty_red - centre, left=centre, color=BLUE, height=0.6,
            edgecolor=SURFACE, linewidth=2.0, label="upper end of tested range")
    ax.barh(y, T.min_empty_red - centre, left=centre, color=ORANGE, height=0.6,
            edgecolor=SURFACE, linewidth=2.0, label="lower end of tested range")
    ax.axvline(centre, color=INK, lw=1.8)
    ax.set_yticks(y, [p.replace("_", " ") for p in T.parameter])
    span = T.max_empty_red.max() - T.min_empty_red.min()
    ax.set_xlim(T.min_empty_red.min() - 0.16 * span,
                T.max_empty_red.max() + 0.14 * span)
    for i, (lo, hi) in enumerate(zip(T.min_empty_red, T.max_empty_red)):
        ax.text(hi + 0.35, i, f"{hi:.1f}", va="center", fontsize=8.8, color=INK2)
        ax.text(lo - 0.35, i, f"{lo:.1f}", va="center", ha="right", fontsize=8.8,
                color=INK2)
    ax.set_xlabel("Empty-km reduction vs B0 (%)")
    ax.set_title("Sensitivity tornado — what actually moves the result")
    ax.legend(loc="lower right")
    clean_axes(ax)
    caption(fig, f"Base case marked by the vertical line ({centre:.1f}%). "
                 "One-factor-at-a-time, R = 40 days per point. Shipment density and "
                 "deadline tightness dominate; fuel price and wages barely move the "
                 "empty-km result at all (they move cost, not routing).", y=-0.02)
    save(fig, os.path.join(FIG, "08_sensitivity_tornado.png"))


# ---------------------------------------------------------------------------
def fig_failure():
    F = pd.read_csv(os.path.join(TAB, "failure_taxonomy_by_scenario.csv"))
    order = ["S1_low_avail", "S0_base", "S3_high_avail", "S4_strict_dl",
             "S5_relaxed_dl", "S10a_detour_15", "S10b_detour_50"]
    F = F[F.scenario_id.isin(order)]
    reasons = ["matched", "detour_exceeded", "lost_to_competing_truck",
               "deadline_infeasible", "capacity", "volume", "driver_hours",
               "return_window", "no_shipment_in_pool"]
    reasons = [r for r in reasons if r in F.unmatched_reason.unique()]
    cmap = {"matched": AQUA, "detour_exceeded": ORANGE,
            "lost_to_competing_truck": VIOLET, "deadline_infeasible": MAGENTA,
            "capacity": YELLOW, "volume": SEQ[2], "driver_hours": RED,
            "return_window": SEQ[5], "no_shipment_in_pool": MUTED}
    P = F.pivot(index="scenario_id", columns="unmatched_reason",
                values="pct").reindex(order).fillna(0)
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    left = np.zeros(len(P))
    for r in reasons:
        v = P[r].values if r in P.columns else np.zeros(len(P))
        ax.barh(range(len(P)), v, left=left, color=cmap[r], height=0.66,
                edgecolor=SURFACE, linewidth=2.0,
                label=r.replace("_", " "))
        for i, (x, w) in enumerate(zip(left, v)):
            if w > 5:
                ax.text(x + w / 2, i, f"{w:.0f}%", ha="center", va="center",
                        fontsize=8.8, color="white" if r != "capacity" else INK,
                        fontweight="bold")
        left += v
    ax.set_yticks(range(len(P)), P.index)
    ax.set_xlabel("Share of truck return legs (%)")
    ax.set_title("TRUCKLY failure taxonomy — why a truck still went home empty")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=4)
    ax.set_xlim(0, 100)
    clean_axes(ax)
    caption(fig, "Read the non-'matched' segments: they are the improvement backlog. "
                 "Detour tolerance is the dominant binding constraint in every "
                 "scenario, which says geography — not capacity or deadlines — is "
                 "what limits backhaul matching here.", y=-0.30)
    save(fig, os.path.join(FIG, "09_failure_taxonomy.png"))


# ---------------------------------------------------------------------------
def fig_map():
    nodes = pd.read_csv(os.path.join(GEN, "truckly_nodes.csv"))
    dfc = pd.read_csv(os.path.join(PROC, "truckly_clean.csv"))
    tr = dfc[(dfc.policy == "TRUCKLY") & (dfc.instance_id < 6)]
    b0 = dfc[(dfc.policy == "B0_empty") & (dfc.instance_id < 6)]
    xy = {r.node_id: (r.lon, r.lat) for r in nodes.itertuples()}

    fig, axes = plt.subplots(1, 2, figsize=(13.6, 7.0), sharex=True, sharey=True)
    for ax, (d, title, col) in zip(axes, [
            (b0, "B0 — every return leg runs empty", ORANGE),
            (tr, "TRUCKLY — matched legs carry freight", BLUE)]):
        for r in d.itertuples():
            seq = str(r.route_node_sequence).split(">")
            loaded = r.n_shipments_matched > 0
            pts = [xy[s] for s in seq if s in xy]
            if len(pts) < 2:
                continue
            xs, ys = zip(*pts)
            ax.plot(xs, ys, color=(BLUE if loaded else MUTED),
                    lw=1.5 if loaded else 0.8,
                    alpha=0.55 if loaded else 0.28, zorder=3 if loaded else 2)
        ax.scatter(nodes.lon, nodes.lat, s=26, color=INK, zorder=5,
                   edgecolors=SURFACE, linewidths=1.2)
        for r in nodes.itertuples():
            if r.node_role in ("hub", "port"):
                ax.annotate(r.name, (r.lon, r.lat), fontsize=10.5, color=INK,
                            fontweight="bold", xytext=(5, 4),
                            textcoords="offset points", zorder=6)
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("Longitude (°E)", fontsize=11)
        ax.tick_params(labelsize=10)
        ax.grid(alpha=0.35)
        clean_axes(ax)
    axes[0].set_ylabel("Latitude (°N)")
    axes[0].legend(handles=[
        Line2D([], [], color=BLUE, lw=2.4, label="leg carrying freight"),
        Line2D([], [], color=MUTED, lw=1.6, label="empty leg"),
        Line2D([], [], marker="o", ls="", color=INK, ms=6, label="network node")],
        loc="lower left", frameon=True, fontsize=10, facecolor=SURFACE,
        edgecolor=GRID, framealpha=0.95)
    fig.suptitle("Route map — 6 simulated operating days, South India corridor",
                 fontsize=15, fontweight="bold", y=0.98)
    fig.text(0.5, 0.925, "node coordinates are REAL (OpenStreetMap); lines are "
             "straight-line schematics, not traced road geometry",
             ha="center", fontsize=9.5, color=MUTED)
    fig.subplots_adjust(top=0.90, bottom=0.07)
    save(fig, os.path.join(FIG, "10_route_map.png"))


# ---------------------------------------------------------------------------
def fig_pruning():
    P = pd.read_csv(os.path.join(TAB, "ml_pruning_curve.csv"))
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(P.mean_pruned_pct, P.mean_gap_pct, marker="o", color=BLUE,
            label="mean optimality gap")
    ax.plot(P.mean_pruned_pct, P.worst_gap_pct, marker="^", color=ORANGE, ls="--",
            label="worst-case gap")
    for _, r in P.iterrows():
        if r.threshold in (0.02, 0.10, 0.30):
            ax.annotate(f"thr {r.threshold:.2f} · {r.speedup:.2f}× faster",
                        (r.mean_pruned_pct, r.mean_gap_pct),
                        textcoords="offset points", xytext=(-4, 22),
                        ha="right", fontsize=9, color=INK,
                        bbox=dict(fc=SURFACE, ec=GRID, boxstyle="round,pad=0.3"),
                        arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.9))
    ax.set_xlabel("Share of candidate (truck, bundle) pairs pruned by the classifier (%)")
    ax.set_ylabel("Loss in objective value vs full search (%)")
    ax.set_title("ML as a pruning heuristic — what it costs to search less")
    ax.legend(loc="upper left")
    clean_axes(ax)
    caption(fig, "CP-SAT re-solved from scratch at every threshold on 20 held-out "
                 "instances. The honest reading: ~39% of candidates can be discarded "
                 "for a mean gap of 0.06%, but the full solve already takes ~8 ms, so "
                 "the practical gain at this problem size is small. It would matter "
                 "at fleet scale.", y=-0.02)
    save(fig, os.path.join(FIG, "11_ml_pruning_curve.png"))


if __name__ == "__main__":
    fig_baseline_vs_truckly(); fig_scenario_density(); fig_tornado()
    fig_failure(); fig_map(); fig_pruning()
