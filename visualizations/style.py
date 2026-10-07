"""TRUCKLY — shared chart style.

Palette taken from the validated reference instance and re-checked with the
data-viz validator for the four categorical slots actually used here:
  blue #2a78d6, orange #eb6834, aqua #1baf7a, yellow #eda100
  -> lightness band PASS, chroma floor PASS,
     CVD separation PASS (worst adjacent dE 9.1, protan),
     normal-vision floor PASS (worst adjacent dE 22.9).
Aqua and yellow fall below 3:1 contrast on the light surface, so the relief
rule applies: every chart that uses them ships visible direct labels.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK2      = "#52514e"
MUTED     = "#898781"
GRID      = "#e1e0d9"
BASELINE  = "#c3c2b7"

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET, RED = "#e87ba4", "#008300", "#4a3aa7", "#e34948"

# colour follows the ENTITY, never its rank
POLICY_COLOR = {
    "B0_empty":   ORANGE,
    "B1_wait_2h": YELLOW, "B1_wait_6h": YELLOW, "B1_wait_12h": YELLOW,
    "B2_greedy":  AQUA,
    "TRUCKLY":    BLUE,
}
POLICY_LABEL = {
    "B0_empty": "B0  Empty return", "B1_wait_2h": "B1  Wait 2 h",
    "B1_wait_6h": "B1  Wait 6 h", "B1_wait_12h": "B1  Wait 12 h",
    "B2_greedy": "B2  Naive greedy", "TRUCKLY": "TRUCKLY",
}
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

BASE_RC = {
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": ["DejaVu Sans"], "font.size": 10.5,
    "axes.edgecolor": BASELINE, "axes.linewidth": 1.0,
    "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 13, "axes.titleweight": "bold",
    "axes.labelsize": 10.5, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "legend.frameon": False, "legend.fontsize": 9.5,
    "lines.linewidth": 2.0, "lines.markersize": 8,
}
plt.rcParams.update(BASE_RC)


def clean_axes(ax, keep_left=True):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    if keep_left:
        ax.spines["left"].set_color(BASELINE)
    else:
        ax.spines["left"].set_visible(False)
    return ax


def fd_bins(v):
    """Freedman-Diaconis bin width -> number of bins. Returns (nbins, width)."""
    v = np.asarray(v)
    q1, q3 = np.percentile(v, [25, 75])
    iqr = q3 - q1
    h = 2.0 * iqr * len(v) ** (-1 / 3)
    if h <= 0:
        return 30, (v.max() - v.min()) / 30
    n = int(np.ceil((v.max() - v.min()) / h))
    return max(8, min(n, 80)), h


def caption(fig, text, y=-0.10):
    """Footnote below the axes. Negative y keeps it clear of the x-label."""
    fig.text(0.012, y, text, ha="left", va="top", fontsize=8.0,
             color=MUTED, wrap=True, transform=fig.transFigure)


def save(fig, path, dpi=300):
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    print("  wrote", path)
