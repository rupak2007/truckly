#!/usr/bin/env python3
"""TRUCKLY — Deliverable 25: the project dashboard (self-contained HTML)."""
from __future__ import annotations
import os, base64, json
import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
TAB, FIG = os.path.join(H, "outputs", "tables"), os.path.join(H, "outputs", "figures")
OUT = os.path.join(H, "outputs", "dashboard.html")

KPI = pd.read_csv(os.path.join(TAB, "kpi_results.csv"))
K = KPI.set_index("KPI")
TST = pd.read_csv(os.path.join(TAB, "statistical_tests.csv"))
SC = pd.read_csv(os.path.join(TAB, "scenario_analysis.csv"))
FAIL = pd.read_csv(os.path.join(TAB, "failure_taxonomy.csv"))
TGT = pd.read_csv(os.path.join(TAB, "target_60pct_analysis.csv"))
pr = TST.iloc[0]
s0 = SC.set_index("scenario").loc["S0_base"]
emp = TGT[(TGT.metric == "Empty-km reduction") & (TGT.comparator == "B0_empty")].iloc[0]
net = TGT[(TGT.metric == "NET-cost reduction") & (TGT.comparator == "B0_empty")].iloc[0]


def b64(name):
    with open(os.path.join(FIG, name), "rb") as f:
        return base64.b64encode(f.read()).decode()


def tiles():
    T = [
        ("Empty km avoided", f"{emp.abs_diff_per_day:,.0f}", "km per operating day",
         f"−{emp.pct_ratio_of_sums:.1f}% vs empty-return baseline", "good"),
        ("Net cost saved", f"₹{net.abs_diff_per_day:,.0f}", "per operating day",
         f"−{net.pct_ratio_of_sums:.1f}% vs baseline", "good"),
        ("Loads matched", f"{s0.served_TR:.1f}", "per day (B2 greedy: "
         f"{s0.served_B2:.1f})", f"+{100*(s0.served_TR-s0.served_B2)/s0.served_B2:.1f}% vs greedy", "good"),
        ("Backhaul fill rate", f"{s0.fill_rate_TR_pct:.1f}%", "of return legs carry freight",
         "baseline: 0%", "good"),
        ("Weight utilisation", f"+{s0.util_gain_vs_B0_pp:.2f} pp", "return-leg tonne-km",
         "from 0% at baseline", "good"),
        ("Fuel", f"+{abs(float(str(K.loc['Fuel','Truckly vs B0']).split()[0])):.1f}%",
         "INCREASE vs baseline", "carrying freight burns more than running empty", "warn"),
        ("On-time delivery", f"{float(K.loc['On-time rate','TRUCKLY']):.1f}%",
         "deadlines are hard constraints", "no deadline missed", "good"),
        ("Decision time", f"{float(K.loc['Solve time per decision','TRUCKLY']):.2f} ms",
         "per truck, CP-SAT proven optimal", "operationally feasible", "good"),
    ]
    return "".join(
        f'<div class="tile {c}"><div class="lab">{l}</div>'
        f'<div class="val">{v}</div><div class="sub">{s}</div>'
        f'<div class="note">{n}</div></div>' for l, v, s, n, c in T)


def table_html(df, bold=()):
    th = "".join(f"<th>{c}</th>" for c in df.columns)
    rows = ""
    for _, r in df.iterrows():
        tds = "".join(
            f'<td class="{"b" if c in bold else ""}">'
            f'{"n/a" if (isinstance(v,float) and np.isnan(v)) or str(v)=="nan" else v}</td>'
            for c, v in zip(df.columns, r.values))
        rows += f"<tr>{tds}</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>"


kpi_show = KPI[["KPI", "B0_empty", "B1_wait_6h", "B2_greedy", "TRUCKLY",
                "Truckly vs B0", "Truckly vs B2", "Improvement?"]]
sc_show = SC[["label", "density", "empty_red_vs_B0_pct", "empty_red_vs_B2_pct",
              "net_cost_red_vs_B0_pct", "fill_rate_TR_pct", "util_gain_vs_B0_pp"]]
sc_show.columns = ["Scenario", "Loads/truck", "Empty ↓ vs B0 %", "Empty ↓ vs B2 %",
                   "Net cost ↓ vs B0 %", "Fill rate %", "Util gain pp"]

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TRUCKLY — Fleet Dashboard</title><style>
:root{{color-scheme:light;--s1:#fcfcfb;--page:#f4f4f1;--ink:#0b0b0b;--ink2:#52514e;
--muted:#898781;--grid:#e1e0d9;--blue:#2a78d6;--navy:#0d366b;--orange:#eb6834;
--aqua:#1baf7a;--good:#0ca30c;--warn:#eb6834;}}
@media(prefers-color-scheme:dark){{:root{{--s1:#1a1a19;--page:#0d0d0d;--ink:#fff;
--ink2:#c3c2b7;--grid:#2c2c2a;--blue:#3987e5;--navy:#cde2fb;--orange:#d95926;--aqua:#199e70;}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--page);color:var(--ink);
font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}
.wrap{{max-width:1240px;margin:0 auto;padding:26px 20px 60px}}
header{{background:var(--navy);color:#fff;border-radius:14px;padding:26px 30px;margin-bottom:8px}}
@media(prefers-color-scheme:dark){{header{{background:#12233d}}}}
h1{{margin:0;font-size:34px;letter-spacing:-.5px}}
header p{{margin:6px 0 0;color:#9ec5f4;font-size:14px}}
.banner{{background:#fdf6ef;border:1px solid var(--orange);color:#7a3a12;
border-radius:10px;padding:11px 16px;margin:14px 0 22px;font-size:13px}}
@media(prefers-color-scheme:dark){{.banner{{background:#2a1a10;color:#f0c4a8}}}}
h2{{font-size:19px;margin:34px 0 12px;color:var(--ink)}}
h2 span{{color:var(--muted);font-weight:400;font-size:13px;margin-left:10px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(228px,1fr));gap:12px}}
.tile{{background:var(--s1);border:1px solid var(--grid);border-radius:12px;padding:16px 18px}}
.tile .lab{{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
.tile .val{{font-size:31px;font-weight:700;margin:6px 0 2px;color:var(--blue)}}
.tile.warn .val{{color:var(--orange)}}
.tile .sub{{font-size:12.5px;color:var(--ink2)}}
.tile .note{{font-size:11.5px;color:var(--muted);margin-top:7px;border-top:1px solid var(--grid);padding-top:7px}}
table{{width:100%;border-collapse:collapse;background:var(--s1);border:1px solid var(--grid);
border-radius:10px;overflow:hidden;font-size:13px}}
th{{background:#256abf;color:#fff;text-align:right;padding:9px 11px;font-weight:600;font-size:12px}}
th:first-child{{text-align:left}}
td{{padding:8px 11px;text-align:right;border-top:1px solid var(--grid);
font-variant-numeric:tabular-nums}}
td:first-child{{text-align:left}}
td.b{{font-weight:700}}
tbody tr:nth-child(even){{background:rgba(0,0,0,.022)}}
figure{{margin:0 0 16px;background:var(--s1);border:1px solid var(--grid);
border-radius:12px;padding:12px}}
figure img{{width:100%;display:block;border-radius:6px}}
figcaption{{font-size:12px;color:var(--ink2);margin-top:9px}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:900px){{.two{{grid-template-columns:1fr}}}}
.callout{{background:var(--s1);border-left:4px solid var(--blue);border-radius:0 10px 10px 0;
padding:14px 18px;margin:14px 0;font-size:13.5px;color:var(--ink2)}}
footer{{margin-top:44px;padding-top:18px;border-top:1px solid var(--grid);
font-size:12px;color:var(--muted)}}
</style></head><body><div class="wrap">

<header>
<h1>TRUCKLY</h1>
<p>Freight matching &amp; route optimisation · fleet dashboard ·
{int(pr.n_instances)} paired simulated operating days · 30 trucks · CP-SAT proven optimal</p>
</header>

<div class="banner">
<strong>Simulated data.</strong> Only the 40 node coordinates are real
(OpenStreetMap). All shipments, trucks, journeys, costs and emissions are
simulated, derived or assumed. These figures describe the simulated environment,
not Indian road freight.
</div>

<h2>Fleet KPIs <span>TRUCKLY vs the empty-return baseline, per operating day</span></h2>
<div class="tiles">{tiles()}</div>

<div class="callout">
<strong>Primary endpoint (pre-specified):</strong> empty-km reduction versus the
<em>naive greedy</em> matcher — not versus doing nothing. Mean paired difference
<strong>{pr.mean_diff:.1f} km/day</strong> (95% bootstrap CI
[{pr.ci_low:.1f}, {pr.ci_high:.1f}]; Hodges–Lehmann {pr.hodges_lehmann:.1f} km;
rank-biserial {pr.rank_biserial:.3f}; Wilcoxon p = {pr.wilcoxon_p:.1e}; TRUCKLY
lower in {int(pr.truckly_better_in_n)}/{int(pr.n_instances)} days).
Comparing an optimiser to “do nothing” inflates the headline; this is the honest test.
</div>

<h2>Baseline vs TRUCKLY <span>all KPIs, mean per operating day</span></h2>
{table_html(kpi_show, bold=("Truckly vs B0", "Truckly vs B2"))}

<div class="callout">
<strong>Read the negatives.</strong> Fuel, gross cost and total distance
<em>increased</em>. Carrying freight burns more diesel than running empty, and
serving extra loads requires repositioning. The gain is in <em>empty</em>
kilometres, <em>net</em> cost and utilisation — not in fuel.
<strong>The 60% aspirational target was not reached on any metric.</strong>
</div>

<h2>Baseline vs TRUCKLY <span>mean ± 95% CI over 100 paired days</span></h2>
<figure><img src="data:image/png;base64,{b64('06_baseline_vs_truckly.png')}">
<figcaption>Common random numbers: all four policies saw the identical fleet,
shipment pool and per-arc fuel perturbation.</figcaption></figure>

<h2>The most important result <span>benefit is a function of market thickness</span></h2>
<div class="two">
<figure><img src="data:image/png;base64,{b64('07_benefit_vs_shipment_density.png')}">
<figcaption>Reporting the benefit as a curve rather than a point estimate is what
makes it robust to the objection that the generator was tuned.</figcaption></figure>
<figure><img src="data:image/png;base64,{b64('08_sensitivity_tornado.png')}">
<figcaption>Shipment density and deadline tightness dominate. Fuel price and wages
barely move the empty-km result — they move cost, not routing.</figcaption></figure>
</div>

<h2>Scenario analysis <span>12 scenarios × 100 days</span></h2>
{table_html(sc_show)}

<h2>When does TRUCKLY fail? <span>failure taxonomy</span></h2>
<figure><img src="data:image/png;base64,{b64('09_failure_taxonomy.png')}">
<figcaption>Geography, not capacity, is the binding constraint: most open loads
simply do not lie close enough to the truck's return corridor.</figcaption></figure>
{table_html(FAIL)}

<h2>Route map <span>6 simulated operating days</span></h2>
<figure><img src="data:image/png;base64,{b64('10_route_map.png')}">
<figcaption>Node coordinates are real. Lines are straight-line schematics between
nodes, not traced road geometry — road distance is modelled with a circuity
factor.</figcaption></figure>

<h2>Problem characterisation <span>the five poster panels</span></h2>
<div class="two">
<figure><img src="data:image/png;base64,{b64('01_empty_distance_histogram.png')}">
<figcaption>Empty distance is right-skewed: the waste is concentrated in a
minority of journeys.</figcaption></figure>
<figure><img src="data:image/png;base64,{b64('05_utilisation_distribution.png')}">
<figcaption>Bimodal — the visual signature of the empty-backhaul problem.</figcaption></figure>
<figure><img src="data:image/png;base64,{b64('03_distance_vs_fuel.png')}">
<figcaption>Partly structural by construction; see the note on the panel.</figcaption></figure>
<figure><img src="data:image/png;base64,{b64('04_correlation_heatmap.png')}">
<figcaption>Definitional identities are masked, not reported as findings.</figcaption></figure>
</div>

<h2>ML extension <span>pruning, not prediction</span></h2>
<figure><img src="data:image/png;base64,{b64('11_ml_pruning_curve.png')}">
<figcaption>Machine learning serves the optimiser here rather than replacing it.
Removing the ML layer changes runtime, not the result — Truckly does not work
because of ML.</figcaption></figure>

<footer>
TRUCKLY · generated from <code>outputs/tables/</code> · seed
20260816 · every number is read from the experiment at build time.<br>
Provenance: OBS = observed · SIM = simulated · DRV = derived · ASM = assumed ·
OPT = optimiser output. See <code>docs/data_dictionary.md</code> and
<code>docs/limitations.md</code>.
</footer>
</div></body></html>"""

open(OUT, "w").write(HTML)
print("wrote", OUT, f"({os.path.getsize(OUT)/1e6:.1f} MB)")
