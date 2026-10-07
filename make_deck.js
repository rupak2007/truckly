// TRUCKLY — Deliverable 27: final project presentation (16 slides)
const pptx = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

const H = __dirname;
const FIG = path.join(H, "outputs", "figures");
const T = JSON.parse(fs.readFileSync(path.join(H, "outputs", "tables", "deck_numbers.json")));

const NAVY = "0D366B", BLUE = "2A78D6", ICE = "CADCFC", ORANGE = "EB6834";
const INK = "0B0B0B", INK2 = "52514E", MUTED = "898781", PAPER = "FFFFFF",
      SOFT = "F4F6FA";
const HEAD = "Cambria", BODY = "Calibri";

const p = new pptx();
p.layout = "LAYOUT_WIDE";              // 13.333 x 7.5
p.author = "TRUCKLY";
p.title = "TRUCKLY — Optimising Freight Trucks' Journeys";

const img = (n) => path.join(FIG, n);

function dark(s) { s.background = { color: NAVY }; }
function light(s) { s.background = { color: PAPER }; }

function title(s, txt, sub, onDark) {
  s.addText(txt, { x: 0.62, y: 0.42, w: 12.1, h: 0.78, fontSize: 38, bold: true,
    fontFace: HEAD, color: onDark ? PAPER : NAVY, margin: 0 });
  if (sub) s.addText(sub, { x: 0.62, y: 1.22, w: 12.1, h: 0.42, fontSize: 15,
    fontFace: BODY, color: onDark ? ICE : INK2, margin: 0 });
}

function num(s, n, x, y) {
  s.addShape(p.ShapeType.ellipse, { x, y, w: 0.46, h: 0.46, fill: { color: ORANGE } });
  s.addText(String(n), { x, y, w: 0.46, h: 0.46, fontSize: 15, bold: true,
    color: PAPER, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
}

function card(s, x, y, w, h, fill) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.1,
    fill: { color: fill || SOFT },
    shadow: { type: "outer", angle: 90, blur: 8, offset: 1, opacity: 0.10, color: "000000" } });
}

function stat(s, x, y, w, value, label, note, color) {
  card(s, x, y, w, 1.62);
  s.addText(value, { x: x + 0.22, y: y + 0.16, w: w - 0.44, h: 0.7, fontSize: 40,
    bold: true, color: color || BLUE, fontFace: HEAD, margin: 0 });
  s.addText(label, { x: x + 0.22, y: y + 0.88, w: w - 0.44, h: 0.3, fontSize: 13.5,
    bold: true, color: INK, fontFace: BODY, margin: 0 });
  s.addText(note, { x: x + 0.22, y: y + 1.16, w: w - 0.44, h: 0.38, fontSize: 11,
    color: MUTED, fontFace: BODY, margin: 0 });
}

function bullets(s, items, x, y, w, size, color) {
  s.addText(items.map((t, i) => ({ text: t, options: {
    bullet: { indent: 14 }, breakLine: i !== items.length - 1 } })),
    { x, y, w, h: 0.4 * items.length + 0.3, fontSize: size || 14,
      color: color || INK2, fontFace: BODY, paraSpaceAfter: 8, margin: 0 });
}

function footer(s, txt) {
  s.addText(txt, { x: 0.62, y: 6.82, w: 12.1, h: 0.3, fontSize: 9.5,
    color: MUTED, fontFace: BODY, margin: 0 });
}

// ---------------------------------------------------------------- 1 TITLE
let s = p.addSlide(); dark(s);
s.addText("TRUCKLY", { x: 0.9, y: 2.05, w: 11.5, h: 1.35, fontSize: 76, bold: true,
  color: PAPER, fontFace: HEAD, charSpacing: 1, margin: 0 });
s.addText("Optimising Freight Trucks' Journeys", { x: 0.95, y: 3.35, w: 11.5,
  h: 0.6, fontSize: 26, color: ICE, fontFace: HEAD, margin: 0 });
s.addText("A simulation–optimisation study of empty return journeys on the South-India freight corridor",
  { x: 0.95, y: 4.0, w: 11.5, h: 0.4, fontSize: 14, color: "9EC5F4", fontFace: BODY, margin: 0 });
s.addShape(p.ShapeType.roundRect, { x: 0.95, y: 4.75, w: 5.5, h: 0.55, rectRadius: 0.1,
  fill: { color: "12233D" } });
s.addText("Selective PDPTW  ·  CP-SAT  ·  100 paired simulated days",
  { x: 1.15, y: 4.75, w: 5.2, h: 0.55, fontSize: 12, color: ICE, fontFace: BODY,
    valign: "middle", margin: 0 });
s.addNotes("Truckly is a decision-support system for backhaul freight matching. Everything in this deck comes from a controlled four-policy experiment on simulated data with real geography.");

// ---------------------------------------------------------------- 2 PROBLEM
s = p.addSlide(); light(s);
title(s, "The problem", "A delivered truck has to get home — and usually gets there empty");
card(s, 0.62, 2.0, 6.0, 3.9);
s.addText("Chennai", { x: 0.95, y: 2.35, w: 2.2, h: 0.4, fontSize: 17, bold: true,
  color: INK, fontFace: BODY, margin: 0 });
s.addText("↓   loaded  ·  342 km", { x: 1.05, y: 2.8, w: 4.2, h: 0.35, fontSize: 13,
  color: BLUE, fontFace: BODY, margin: 0 });
s.addText("Bengaluru", { x: 0.95, y: 3.2, w: 2.6, h: 0.4, fontSize: 17, bold: true,
  color: INK, fontFace: BODY, margin: 0 });
s.addText("↓   EMPTY  ·  342 km  ·  ₹9,000 of nothing", { x: 1.05, y: 3.65, w: 5.0,
  h: 0.35, fontSize: 13, bold: true, color: ORANGE, fontFace: BODY, margin: 0 });
s.addText("Chennai", { x: 0.95, y: 4.05, w: 2.2, h: 0.4, fontSize: 17, bold: true,
  color: INK, fontFace: BODY, margin: 0 });
s.addText("The alternative — waiting in Bengaluru for a load — swaps wasted distance for wasted time and lost fleet availability. Neither is good.",
  { x: 0.95, y: 4.7, w: 5.4, h: 0.9, fontSize: 12.5, color: INK2, fontFace: BODY, margin: 0 });
stat(s, 6.95, 2.0, 2.85, T.empty_per_day.toLocaleString(), "empty km per day",
  "30-truck fleet, baseline policy", ORANGE);
stat(s, 10.05, 2.0, 2.85, "100%", "of return km are empty", "under current practice", ORANGE);
stat(s, 6.95, 3.85, 5.95, T.top_decile + "%", "of all empty km sit in the worst 10% of journeys",
  "the waste is concentrated — you don't have to match everything", BLUE);
footer(s, "Baseline B0, scenario S0_base, 100 simulated operating days · simulated freight on real node coordinates");
s.addNotes("The key statistical point is the last card: empty distance is right-skewed, so a minority of journeys carry most of the waste. That is good news for a matching system.");

// ---------------------------------------------------------------- 3 WHY IT MATTERS
s = p.addSlide(); light(s);
title(s, "Why empty return trips matter", "Four costs, all of them avoidable in principle");
const why = [["Fuel", "an empty truck still burns 60–80% of laden consumption"],
             ["Driver time", "paid hours producing no freight movement"],
             ["Fleet availability", "the asset is unavailable while it repositions"],
             ["Emissions", "vehicle-kilometres with zero transport output"]];
why.forEach((wv, i) => {
  const x = 0.62 + (i % 2) * 6.3, y = 2.1 + Math.floor(i / 2) * 2.05;
  card(s, x, y, 6.0, 1.75);
  num(s, i + 1, x + 0.28, y + 0.28);
  s.addText(wv[0], { x: x + 0.92, y: y + 0.26, w: 4.8, h: 0.4, fontSize: 18, bold: true,
    color: NAVY, fontFace: HEAD, margin: 0 });
  s.addText(wv[1], { x: x + 0.92, y: y + 0.72, w: 4.9, h: 0.8, fontSize: 13,
    color: INK2, fontFace: BODY, margin: 0 });
});
footer(s, "Each of these is measured separately in the experiment — no composite 'overall savings' figure is ever computed.");

// ---------------------------------------------------------------- 4 IDEA
s = p.addSlide(); dark(s);
title(s, "The Truckly idea", "Match the returning truck to a load that is already going that way", true);
s.addText("Instead of  Bengaluru → EMPTY → Chennai", { x: 0.62, y: 2.15, w: 12.1,
  h: 0.45, fontSize: 19, color: "9EC5F4", fontFace: BODY, margin: 0 });
s.addText("Truckly searches the open freight pool for a compatible load", { x: 0.62,
  y: 2.72, w: 12.1, h: 0.45, fontSize: 19, bold: true, color: PAPER, fontFace: BODY, margin: 0 });
const opts = [["Bengaluru → Chennai", "exact corridor match"],
              ["Hosur → Chennai", "small pickup detour"],
              ["Bengaluru → Krishnagiri → Chennai", "two-load bundle"]];
opts.forEach((o, i) => {
  const x = 0.62 + i * 4.15;
  s.addShape(p.ShapeType.roundRect, { x, y: 3.55, w: 3.85, h: 1.5, rectRadius: 0.1,
    fill: { color: "12233D" } });
  s.addText(o[0], { x: x + 0.25, y: 3.78, w: 3.4, h: 0.7, fontSize: 14, bold: true,
    color: PAPER, fontFace: BODY, margin: 0 });
  s.addText(o[1], { x: x + 0.25, y: 4.48, w: 3.4, h: 0.35, fontSize: 12, color: ICE,
    fontFace: BODY, margin: 0 });
});
s.addText("…then checks capacity, volume, pickup time, delivery deadline, detour budget and driver hours — and picks the assignment that maximises system value across the WHOLE fleet, not one truck at a time.",
  { x: 0.62, y: 5.35, w: 12.1, h: 0.9, fontSize: 13.5, color: ICE, fontFace: BODY, margin: 0 });
s.addNotes("The 'whole fleet, not one truck at a time' phrase is the difference between Truckly and the greedy baseline.");

// ---------------------------------------------------------------- 5 ARCHITECTURE
s = p.addSlide(); light(s);
title(s, "System architecture", "Five stages, each independently testable");
const stages = [["A", "Candidate generation", "feasible (truck, bundle) pairs from the open pool"],
                ["B", "Hard constraints", "capacity → volume → detour → time windows → driver hours"],
                ["C", "Global assignment", "CP-SAT prize-collecting set packing, proven optimal"],
                ["D", "Route optimisation", "exact enumeration of all precedence-valid orders"],
                ["E", "Recommendation", "match, route, costs and a plain-language explanation"]];
stages.forEach((st, i) => {
  const y = 2.05 + i * 0.98;
  card(s, 0.62, y, 12.1, 0.84);
  s.addShape(p.ShapeType.ellipse, { x: 0.88, y: y + 0.17, w: 0.5, h: 0.5, fill: { color: NAVY } });
  s.addText(st[0], { x: 0.88, y: y + 0.17, w: 0.5, h: 0.5, fontSize: 16, bold: true,
    color: PAPER, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
  s.addText(st[1], { x: 1.6, y: y + 0.13, w: 3.5, h: 0.32, fontSize: 15, bold: true,
    color: NAVY, fontFace: BODY, margin: 0 });
  s.addText(st[2], { x: 1.6, y: y + 0.46, w: 10.8, h: 0.32, fontSize: 12.5,
    color: INK2, fontFace: BODY, margin: 0 });
});
footer(s, "Formally a Selective Pickup-and-Delivery Problem with Time Windows — NOT a classical VRPTW, because accepting nothing is a legal solution.");

// ---------------------------------------------------------------- 6 DATASET
s = p.addSlide(); light(s);
title(s, "Dataset", "Real geography, simulated freight — and the labels say so");
s.addShape(p.ShapeType.roundRect, { x: 0.62, y: 2.0, w: 12.1, h: 0.72, rectRadius: 0.1,
  fill: { color: "FDF6EF" } });
s.addText("⚠  The freight records are SIMULATED. Only the 40 node coordinates are observed. No result here is an observation of real Indian freight.",
  { x: 0.9, y: 2.0, w: 11.6, h: 0.72, fontSize: 13.5, bold: true, color: "A8410F",
    fontFace: BODY, valign: "middle", margin: 0 });
const prov = [["OBS", "40 node coordinates from OpenStreetMap", BLUE],
              ["SIM", T.n_ship.toLocaleString() + " shipments · " + T.n_journey.toLocaleString() + " truck-journeys", ORANGE],
              ["DRV", "distances, fuel, cost, utilisation, CO₂", "1BAF7A"],
              ["ASM", "circuity, speeds, fuel curve, tariffs, driver rules", MUTED]];
prov.forEach((pv, i) => {
  const y = 3.0 + i * 0.86;
  card(s, 0.62, y, 6.0, 0.72);
  s.addShape(p.ShapeType.roundRect, { x: 0.85, y: y + 0.13, w: 0.78, h: 0.46,
    rectRadius: 0.06, fill: { color: pv[2] } });
  s.addText(pv[0], { x: 0.85, y: y + 0.13, w: 0.78, h: 0.46, fontSize: 12, bold: true,
    color: PAPER, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
  s.addText(pv[1], { x: 1.78, y: y, w: 4.7, h: 0.72, fontSize: 12.5, color: INK2,
    fontFace: BODY, valign: "middle", margin: 0 });
});
s.addImage({ path: img("10_route_map.png"), x: 6.95, y: 2.95, w: 5.77, h: 2.84 });
footer(s, "Origin–destination demand follows a gravity model with asymmetric headhaul/backhaul split, so backhaul loads are genuinely scarce.");

// ---------------------------------------------------------------- 7 STATS
s = p.addSlide(); light(s);
title(s, "Statistical findings", "What the baseline data actually shows");
s.addImage({ path: img("01_empty_distance_histogram.png"), x: 0.62, y: 1.95, w: 5.95, h: 3.8 });
s.addImage({ path: img("05_utilisation_distribution.png"), x: 6.78, y: 1.95, w: 5.95, h: 3.8 });
card(s, 0.62, 5.9, 5.95, 0.95);
s.addText("Right-skewed (skew " + T.skew + "): mean " + T.mean_km + " km > median " +
  T.median_km + " km. The worst decile carries " + T.top_decile + "% of all empty kilometres.",
  { x: 0.85, y: 5.9, w: 5.5, h: 0.95, fontSize: 12, color: INK2, fontFace: BODY,
    valign: "middle", margin: 0 });
card(s, 6.78, 5.9, 5.95, 0.95);
s.addText("Bimodal: " + T.pct_zero + "% of return legs sit at exactly 0% utilisation. That second peak IS the empty-backhaul problem, drawn.",
  { x: 7.01, y: 5.9, w: 5.5, h: 0.95, fontSize: 12, color: INK2, fontFace: BODY,
    valign: "middle", margin: 0 });
s.addNotes("Lead with the bimodality on the right — it is the visual signature of the problem and a much stronger observation than 'utilisation is low'.");

// ---------------------------------------------------------------- 8 BASELINES
s = p.addSlide(); light(s);
title(s, "The baselines", "Three of them — and the third is the one that matters");
const bl = [["B0", "Empty return", "Deliver, drive home empty. No matching at all.", MUTED],
            ["B1", "Wait for load", "Take the first feasible load by ready time, within a wait cap. No comparison.", MUTED],
            ["B2", "Naive greedy", "Trucks in seeded order; each grabs its best-scoring feasible load. No coordination, no bundling.", ORANGE]];
bl.forEach((b, i) => {
  const y = 2.1 + i * 1.35;
  card(s, 0.62, y, 12.1, 1.18, i === 2 ? "FDF6EF" : SOFT);
  s.addShape(p.ShapeType.roundRect, { x: 0.9, y: y + 0.3, w: 0.85, h: 0.58,
    rectRadius: 0.08, fill: { color: b[3] } });
  s.addText(b[0], { x: 0.9, y: y + 0.3, w: 0.85, h: 0.58, fontSize: 17, bold: true,
    color: PAPER, align: "center", valign: "middle", fontFace: BODY, margin: 0 });
  s.addText(b[1], { x: 1.95, y: y + 0.2, w: 3.2, h: 0.4, fontSize: 16, bold: true,
    color: NAVY, fontFace: BODY, margin: 0 });
  s.addText(b[2], { x: 1.95, y: y + 0.62, w: 10.4, h: 0.42, fontSize: 12.5,
    color: INK2, fontFace: BODY, margin: 0 });
});
card(s, 0.62, 6.15, 12.1, 0.78, "FDF6EF");
s.addText("Comparing an optimiser to “do nothing” inflates the headline — any matcher beats no matcher. The scientific claim of this project is the margin over B2.",
  { x: 0.9, y: 6.15, w: 11.6, h: 0.78, fontSize: 13, bold: true, color: "A8410F",
    fontFace: BODY, valign: "middle", margin: 0 });

// ---------------------------------------------------------------- 9 ALGORITHM
s = p.addSlide(); light(s);
title(s, "The Truckly algorithm", "Explainable score for ranking, exact optimisation for deciding");
card(s, 0.62, 2.0, 6.0, 4.3);
s.addText("Explainable score  S(k,b)", { x: 0.9, y: 2.22, w: 5.4, h: 0.4, fontSize: 17,
  bold: true, color: NAVY, fontFace: HEAD, margin: 0 });
bullets(s, ["+ empty kilometres avoided", "− detour incurred", "+ capacity filled",
  "− idle waiting time", "+ delivery deadline slack"], 1.0, 2.72, 5.2, 13.5);
s.addText("Every term divided by a stated maximum so the weights are comparable. Used to rank candidates and to explain the choice to the user.",
  { x: 0.9, y: 5.1, w: 5.4, h: 1.0, fontSize: 12, color: MUTED, fontFace: BODY, margin: 0 });
card(s, 6.95, 2.0, 5.77, 4.3, "12233D");
s.addText("Optimisation objective", { x: 7.23, y: 2.22, w: 5.2, h: 0.4, fontSize: 17,
  bold: true, color: PAPER, fontFace: HEAD, margin: 0 });
s.addText("min  Σ (c_kb − revenue_b)·y_kb  +  Σ c_empty·z_k\n\n" +
  "s.t.   Σ y_kb + z_k = 1        every truck\n" +
  "        Σ y_kb ≤ 1              every load\n\n" +
  "Prize-collecting set packing with an outside option.",
  { x: 7.23, y: 2.75, w: 5.2, h: 2.0, fontSize: 12.5, color: ICE,
    fontFace: "Courier New", margin: 0 });
s.addText("The score is NOT the objective. The optimiser minimises cost in rupees; the score exists to explain and to drive the greedy baseline.",
  { x: 7.23, y: 5.1, w: 5.2, h: 1.0, fontSize: 12, color: "9EC5F4", fontFace: BODY, margin: 0 });

// ---------------------------------------------------------------- 10 OPTIMISATION
s = p.addSlide(); light(s);
title(s, "Optimisation, and why it is checkable", "Provably optimal, and fast enough to run live");
stat(s, 0.62, 2.15, 3.85, "100%", "of solves returned OPTIMAL",
  "CP-SAT status recorded on every journey row", BLUE);
stat(s, 4.75, 2.15, 3.85, T.solve_ms + " ms", "mean decision time per truck",
  "operational feasibility is evidenced, not asserted", BLUE);
stat(s, 8.88, 2.15, 3.84, "exact", "route enumeration",
  "(2k)!/2^k precedence-valid orders — no heuristic", BLUE);
card(s, 0.62, 4.15, 12.1, 2.15);
s.addText("Two stages, deliberately separated", { x: 0.9, y: 4.35, w: 11.5, h: 0.4,
  fontSize: 16, bold: true, color: NAVY, fontFace: HEAD, margin: 0 });
bullets(s, [
  "Assignment — which truck takes which bundle: CP-SAT, solved to proven optimality over the generated candidate set",
  "Routing — in what order the stops are visited: 2 orders for one load, 6 for two, 90 for three; all enumerated exactly",
  "Honest caveat: the decomposition itself is a heuristic, and bundles are capped at two loads. A monolithic model could in principle find solutions this misses."],
  1.0, 4.82, 11.4, 13);

// ---------------------------------------------------------------- 11 DEMO
s = p.addSlide(); dark(s);
title(s, "Live demo", "One truck, one recommendation, six reasons", true);
card(s, 0.62, 2.0, 6.0, 4.5, "12233D");
s.addText("TRUCKLY RECOMMENDATION", { x: 0.9, y: 2.2, w: 5.4, h: 0.35, fontSize: 12,
  bold: true, color: ORANGE, fontFace: BODY, charSpacing: 1, margin: 0 });
s.addText("Truck T0003_015  ·  RIGID 16T\nTiruchirappalli → Hosur  ·  280 km direct empty return\n\n" +
  "MATCH  S0003_362\n1,834 kg · 280 km · Rs 7,733 revenue\n\n" +
  "Empty km avoided     280 km\nAdditional detour      0 km\nNet saving vs empty  Rs 7,184\nUtilisation           11.5 %\nDeadline              MET",
  { x: 0.9, y: 2.65, w: 5.4, h: 3.6, fontSize: 12.5, color: ICE, fontFace: "Courier New",
    lineSpacing: 17, margin: 0 });
card(s, 6.95, 2.0, 5.77, 4.5, "12233D");
s.addText("WHY TRUCKLY CHOSE THIS", { x: 7.23, y: 2.2, w: 5.2, h: 0.35, fontSize: 12,
  bold: true, color: ORANGE, fontFace: BODY, charSpacing: 1, margin: 0 });
bullets(s, [
  "Avoids 280 km of empty running — 100% of the empty leg",
  "Costs 0.0 km of extra distance, well inside the detour budget",
  "Fills 11% of weight and 10% of volume — no capacity breach",
  "Pickup is at the truck's current node; 0.00 h of idle waiting",
  "Deadline achievable with 3.5 h of margin; driver duty legal",
  "Revenue ₹7,733 exceeds ₹550 of extra cost — the load pays for itself"],
  7.3, 2.68, 5.1, 12.5, ICE);
footer(s, "13,500 truck–load pairs screened · 131 feasible · CP-SAT solved the fleet-wide assignment to proven optimality in 14 ms");

// ---------------------------------------------------------------- 12 RESULTS
s = p.addSlide(); light(s);
title(s, "Baseline vs TRUCKLY", "100 paired simulated days, common random numbers");
s.addImage({ path: img("06_baseline_vs_truckly.png"), x: 0.62, y: 1.82, w: 12.1, h: 3.32 });
stat(s, 0.62, 5.4, 3.85, "−" + T.empty_red + "%", "empty kilometres vs B0",
  "primary vs greedy: " + T.mean_diff + " km/day, p<0.001", BLUE);
stat(s, 4.75, 5.4, 3.85, "−" + T.net_red + "%", "net cost vs B0",
  "−" + T.net_red_b2 + "% vs the naive greedy matcher", BLUE);
stat(s, 8.88, 5.4, 3.84, "+" + T.fuel_up + "%", "FUEL — an increase",
  "carrying freight burns more than running empty", ORANGE);
s.addNotes("Do not skip the third card. Reporting the fuel increase is the point at which this stops being a sales deck and becomes a study.");

// ---------------------------------------------------------------- 13 SCENARIOS
s = p.addSlide(); light(s);
title(s, "The most important result", "The benefit is not a constant — it depends on how thick the freight market is");
s.addImage({ path: img("07_benefit_vs_shipment_density.png"), x: 0.62, y: 1.95, w: 6.4, h: 3.75 });
s.addImage({ path: img("08_sensitivity_tornado.png"), x: 7.2, y: 1.95, w: 5.52, h: 3.75 });
card(s, 0.62, 5.85, 12.1, 1.0);
s.addText("At " + T.dens_lo + " open loads per truck Truckly is worth " + T.red_lo +
  "%; at " + T.dens_hi + " it is worth " + T.red_hi +
  "%. Shipment density and deadline tightness dominate; fuel price and wages barely move the routing result at all.",
  { x: 0.9, y: 5.85, w: 11.6, h: 1.0, fontSize: 13, color: INK2, fontFace: BODY,
    valign: "middle", margin: 0 });

// ---------------------------------------------------------------- 14 FAILURE + ML
s = p.addSlide(); light(s);
title(s, "When does Truckly fail? And does ML help?", "Both answers are more useful than a success story");
s.addImage({ path: img("09_failure_taxonomy.png"), x: 0.62, y: 1.95, w: 6.3, h: 3.4 });
s.addImage({ path: img("11_ml_pruning_curve.png"), x: 7.1, y: 1.95, w: 5.62, h: 3.4 });
card(s, 0.62, 5.5, 6.3, 1.35);
s.addText("Geography, not capacity, is the binding constraint. " + T.fail_detour +
  "% of unmatched trucks fail on detour — the loads simply aren't near the return corridor.",
  { x: 0.85, y: 5.5, w: 5.85, h: 1.35, fontSize: 12, color: INK2, fontFace: BODY,
    valign: "middle", margin: 0 });
card(s, 7.1, 5.5, 5.62, 1.35, "FDF6EF");
s.addText("ML prunes " + T.prune_pct + "% of candidates for a " + T.prune_gap +
  "% optimality gap. Useful — but Truckly does not work BECAUSE of ML. Removing it changes runtime, not the result.",
  { x: 7.33, y: 5.5, w: 5.16, h: 1.35, fontSize: 12, color: "A8410F", fontFace: BODY,
    valign: "middle", margin: 0 });

// ---------------------------------------------------------------- 15 LIMITATIONS
s = p.addSlide(); light(s);
title(s, "Limitations", "Ordered by how much they threaten the conclusions");
const lim = [["1", "No live routing engine was reachable", "Road distance is great-circle × a declared circuity factor, not traced road geometry. The OSRM swap-in is written and is a one-command change."],
             ["2", "The freight records are simulated", "Results describe the simulated environment, not Indian road freight. Only the 40 node coordinates are observed."],
             ["3", "The freight pool is uncontested", "No competing carriers. These figures are an upper bound on what one carrier could capture."],
             ["4", "Single-leg model", "Only the return leg is simulated, so utilisation figures are return-leg, not round-trip."],
             ["5", "Significance is cheap here", "R is under our control. The confidence interval and effect size are the result — not the p-value."]];
lim.forEach((l, i) => {
  const y = 1.98 + i * 1.02;
  card(s, 0.62, y, 12.1, 0.88);
  num(s, l[0], 0.88, y + 0.21);
  s.addText(l[1], { x: 1.6, y: y + 0.13, w: 4.3, h: 0.32, fontSize: 14, bold: true,
    color: NAVY, fontFace: BODY, margin: 0 });
  s.addText(l[2], { x: 1.6, y: y + 0.47, w: 10.8, h: 0.34, fontSize: 11.5,
    color: INK2, fontFace: BODY, margin: 0 });
});

// ---------------------------------------------------------------- 16 CONCLUSION
s = p.addSlide(); dark(s);
title(s, "Conclusion", "What the evidence actually supports", true);
s.addText("Intelligent freight matching reduced empty running by " + T.empty_red +
  "% and net cost by " + T.net_red + "% against current practice, and beat a naive greedy matcher by a small but statistically reliable margin.",
  { x: 0.62, y: 2.1, w: 12.1, h: 0.9, fontSize: 17, color: PAPER, fontFace: BODY, margin: 0 });
const cc = [["60% target", "NOT reached on any metric", ORANGE],
            ["Primary endpoint", T.mean_diff + " km/day vs greedy\n95% CI [" + T.ci_lo + ", " + T.ci_hi + "]", ICE],
            ["Real driver of value", "market thickness:\n" + T.red_lo + "% → " + T.red_hi + "% as loads/truck rises", ICE]];
cc.forEach((c, i) => {
  const x = 0.62 + i * 4.15;
  s.addShape(p.ShapeType.roundRect, { x, y: 3.25, w: 3.85, h: 1.9, rectRadius: 0.1,
    fill: { color: "12233D" } });
  s.addText(c[0], { x: x + 0.25, y: 3.45, w: 3.4, h: 0.35, fontSize: 12, bold: true,
    color: ORANGE, fontFace: BODY, charSpacing: 0.6, margin: 0 });
  s.addText(c[1], { x: x + 0.25, y: 3.9, w: 3.4, h: 1.1, fontSize: 15, bold: true,
    color: c[2], fontFace: BODY, valign: "top", margin: 0 });
});
s.addText("The honest headline is narrower than the aspiration, and more useful: most of the benefit comes from matching at all, and global optimisation adds a further few percent plus a materially higher service level. The constraint to attack next is geography and market density — not truck capacity, not deadlines, and not the algorithm.",
  { x: 0.62, y: 5.45, w: 12.1, h: 1.2, fontSize: 13, color: "9EC5F4", fontFace: BODY, margin: 0 });

p.writeFile({ fileName: path.join(H, "outputs", "TRUCKLY_Presentation.pptx") })
  .then(f => console.log("wrote", f));
