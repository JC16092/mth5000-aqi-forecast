// Oral presentation deck for MTH5000. Every number is read from the compiled report (report/main.pdf);
// nothing is recomputed here. Slide figures come from make_slide_figures.py; backup slides reuse the
// report's own figures, extracted from the PDF by ../extract_assets.sh.
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const SLIDES = path.join(__dirname, "..", "assets_slides");
const REPORT = path.join(__dirname, "..", "assets");
const OUT = path.join(__dirname, "..", "MTH5000_oral_presentation.pptx");

// ---------- design tokens: Monash blue, with the Okabe-Ito accents the report's figures use ----------
const C = {
  navy: "0B2545", blue: "006CAB", sky: "56B4E9", pale: "DCEAF5", bg: "F4F7FA", ink: "1B2733",
  grey: "5B6B7A", line: "D3DCE6", verm: "D55E00", orange: "E69F00", green: "009E73", white: "FFFFFF",
};
const FONT = "Calibri";
const W = 13.333, H = 7.5, MX = 0.6;

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.title = "Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities";
pptx.author = "Jaykumar Vinodbhai Chauhan";

// ---------- structure: section and minutes per slide (the single source of truth for the roadmap and the notes) ----------
const SECTIONS = ["Motivation", "Data", "Methods", "Results", "Discussion", "Conclusion"];
const SEC = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 5, 5, 5, 5];
const MINS = [0.5, 1.25, 1.25, 0.75, 0.5, 1.25, 1.5, 1, 0.5, 1.5, 1.5, 0.75, 1.25, 1.25, 1.25, 1, 1.75, 0.5, 1, 1, 1, 1.25, 0.5, 1.25, 1, 0.5, 0.5, 1.25, 1, 0.75, 1, 1.25, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
const NMAIN = SEC.length;
const TAKE = {}; // takeaway line per slide, for the cue card
const GUIDE = []; // collected as slides are built, written out as PRESENTER_GUIDE.md
const secMinutes = (k) => SEC.reduce((a, s, i) => a + (s === k ? MINS[i] : 0), 0);
let n = 0;

function notesFor(cue) {
  const m = MINS[n - 1];
  const head = n <= NMAIN ? `[Slide ${n} of ${NMAIN} | about ${m} min | running total ${MINS.slice(0, n).reduce((a, b) => a + b, 0)} min]` : `[Backup, not timed]`;
  const lines = [head];
  if (cue.say) lines.push("SAY: " + cue.say);
  if (cue.show) lines.push("POINT TO: " + cue.show);
  if (cue.ask) lines.push("IF ASKED: " + cue.ask);
  if (cue.next) lines.push("TRANSITION: " + cue.next);
  return lines.join("\n");
}

// ---------- helpers ----------
function base(title, cue) {
  const s = pptx.addSlide();
  n += 1;
  s.background = { color: C.bg };
  const k = n <= NMAIN ? SEC[n - 1] : -1;
  s.addText(k >= 0 ? SECTIONS[k].toUpperCase() : "BACKUP", {
    x: MX, y: 0.3, w: 6, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 3, margin: 0,
  });
  if (k >= 0) {
    // progress tracker: where this slide sits in the talk
    SECTIONS.forEach((_, i) => {
      s.addShape(pptx.ShapeType.roundRect, {
        x: W - MX - 3.5 + i * 0.6, y: 0.36, w: 0.5, h: 0.07, rectRadius: 0.03,
        fill: { color: i === k ? C.blue : i < k ? C.navy : C.line }, line: { color: C.bg, width: 0 },
      });
    });
  }
  s.addText(title, {
    x: MX, y: 0.62, w: W - 2 * MX, h: 1.0, fontFace: FONT, fontSize: 28, bold: true, color: C.navy, valign: "top", margin: 0,
  });
  s.addText("MTH5000  |  J. V. Chauhan  |  Supervisor: Dr T. Tian", {
    x: MX, y: H - 0.42, w: 7, h: 0.28, fontFace: FONT, fontSize: 10, color: C.grey, margin: 0,
  });
  s.addText(n <= NMAIN ? `${n} / ${NMAIN}` : `B${n - NMAIN}`, {
    x: W - MX - 1, y: H - 0.42, w: 1, h: 0.28, fontFace: FONT, fontSize: 10, color: C.grey, align: "right", margin: 0,
  });
  if (cue) s.addNotes(notesFor(cue));
  GUIDE.push({ n, title, cue: cue || {}, mins: MINS[n - 1] || 0 });
  return s;
}

function card(s, x, y, w, h, o = {}) {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08, fill: { color: o.fill || C.white }, line: { color: o.line || C.line, width: 0.75 },
    shadow: o.flat ? undefined : { type: "outer", color: "000000", opacity: 0.08, blur: 6, offset: 2, angle: 90 },
  });
}

// the one place a slide's conclusion is stated, in the same position on every results slide
function takeaway(s, text, y = 6.2) {
  TAKE[n] = text;
  s.addShape(pptx.ShapeType.rect, { x: MX, y, w: 1.5, h: 0.75, fill: { color: C.navy }, line: { color: C.navy, width: 0 } });
  s.addText("TAKEAWAY", { x: MX, y, w: 1.5, h: 0.75, fontFace: FONT, fontSize: 12, bold: true, color: C.white, align: "center", valign: "middle", charSpacing: 2, margin: 0 });
  s.addShape(pptx.ShapeType.rect, { x: MX + 1.5, y, w: W - 2 * MX - 1.5, h: 0.75, fill: { color: C.pale }, line: { color: C.pale, width: 0 } });
  s.addText(text, { x: MX + 1.7, y, w: W - 2 * MX - 1.9, h: 0.75, fontFace: FONT, fontSize: 15.5, color: C.navy, bold: true, valign: "middle", margin: 0 });
}

const ALT = {
  "series.png": "Daily PM2.5 at the Delhi monitor, 2016 to 2026, with days above the 121 threshold shaded; winter peaks, maximum 896 on 8 November 2017.",
  "cadence.png": "Line chart: the sensor produced 48 readings a day until 2024 and 24 a day after, against the fixed 24 the coverage statistic assumed.",
  "implausible.png": "Bar chart of implausible values per 1000 days by true coverage: 18.5, 14.9 and 15.2 below 90 percent coverage, 2.1 above.",
  "periodogram.png": "Periodogram: peaks only at the annual cycle and its harmonics, nothing at 7 days.",
  "acf.png": "Autocorrelation to lag 21: lags 7, 14 and 21 sit on the smooth decay, not above it.",
  "dow.png": "Day-of-week effect on concentration: every one of the seven intervals contains zero.",
  "annual.png": "Monthly median PM2.5 with interquartile band: high from November to January, lowest in the monsoon, crossing the 121 threshold in autumn and spring.",
  "rq1.png": "Plot of relative error for nine models at one, two and three days ahead: the three networks beat ARIMA only at one day, and every machine learning regressor trails ARIMA.",
  "seed_spread.png": "Bar chart of the spread across ten seeds for GRU, LSTM and transformer at each horizon, against a 0.004 noise floor; the GRU reaches 0.048 at three days.",
  "winter.png": "Observed PM2.5 over winter 2024 to 2025 with ARIMA and GRU one-day-ahead forecasts both following each episode.",
  "weather.png": "GRU ranges over ten seeds with and without weather at each horizon, against the ARIMA line; they separate only at one day.",
  "hero_1.png": "Hit rate rising with alarms raised per year for ARIMA alone.",
  "hero_2.png": "Hit rate against alarms per year for ARIMA, gradient boosting, persistence and climatology: the curves nearly coincide.",
  "hero_budget.png": "The same four curves with two annotations: moving the budget from 40 to 100 alarms changes hit rate by 50 points, while choosing among models at a fixed budget changes it by about 5.",
  "dial_vs_detector.png": "Two bar charts on one axis: swapping the model at 100 alarms a year gives hit rates 0.821 to 0.873, while turning the budget from 40 to 100 alarms gives 0.379 to 0.881.",
  "waffle.png": "Four grids of 100 dots: the best model catches 38, 57, 74 and 88 of every 100 hazardous days at 40, 60, 80 and 100 alarms a year.",
  "calendar.png": "Calendar heat map of the share of days above 121 by year and month: dark from October to February every year, almost clear from June to September.",
  "skyline.png": "The last 365 days of the dataset, one bar per day, hazardous days in vermillion.",
  "monash-logo.png": "Monash University logo",
  "fig5_1_sensitivity.png": "Report Figure 5.1: mean relative error for each of eleven GRU settings at three horizons.",
  "fig3_6_arima_stability.png": "Report Figure 3.6: ARIMA coefficients across 28 refits; the moving-average coefficient crosses the invertibility boundary at three.",
  "fig5_2_architectures.png": "Report Figure 5.2: bounded-check ranges for four architectures against ARIMA.",
  "fig4_4_arms.png": "Report Figure 4.4: hit-rate advantage of forecast-then-threshold over its matched classifier, by budget and horizon.",
};

async function figure(s, dir, file, x, y, maxW, maxH, o = {}) {
  const meta = await sharp(path.join(dir, file)).metadata();
  const r = Math.min(maxW / meta.width, maxH / meta.height);
  const w = meta.width * r, h = meta.height * r;
  const px = x + (maxW - w) / 2, py = y + (maxH - h) / 2;
  const pad = o.pad === undefined ? 0.12 : o.pad;
  if (!o.bare) card(s, px - pad, py - pad, w + 2 * pad, h + 2 * pad);
  s.addImage({ path: path.join(dir, file), x: px, y: py, w, h, altText: ALT[file] || file });
  return { x: px, y: py, w, h };
}

function caption(s, text, x, y, w, o = {}) {
  s.addText(text, { x, y, w, h: o.h || 0.4, fontFace: FONT, fontSize: 12, italic: true, color: C.grey, valign: "top", margin: 0 });
}

function bullets(s, items, x, y, w, h, o = {}) {
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    if (typeof it === "string") {
      runs.push({ text: it, options: { bullet: { indent: 18 }, breakLine: !last, paraSpaceAfter: o.gap || 9 } });
    } else {
      runs.push({ text: it[0], options: { bullet: { indent: 18 }, bold: true, color: C.navy } });
      runs.push({ text: it[1], options: { breakLine: !last, paraSpaceAfter: o.gap || 9 } });
    }
  });
  s.addText(runs, { x, y, w, h, fontFace: FONT, fontSize: o.fontSize || 18, color: C.ink, valign: "top", margin: 0, lineSpacingMultiple: 1.05 });
}

function stat(s, x, y, w, h, big, label, color, bigSize) {
  card(s, x, y, w, h);
  s.addText(big, { x: x + 0.15, y: y + 0.08, w: w - 0.3, h: h * 0.5, fontFace: FONT, fontSize: bigSize || (w > 3.4 ? 38 : 32), bold: true, color: color || C.blue, valign: "middle", margin: 0 });
  s.addText(label, { x: x + 0.15, y: y + h * 0.56, w: w - 0.3, h: h * 0.42, fontFace: FONT, fontSize: 13.5, color: C.grey, valign: "top", margin: 0 });
}

function table(s, rows, x, y, colW, rowH, o = {}) {
  const fs = o.fontSize || 14;
  const hl = new Set((o.hl || []).map(([r, c]) => `${r},${c}`));
  const bold = new Set(o.boldRows || []);
  const body = rows.map((row, r) => row.map((cell, c) => {
    const header = r === 0;
    const opt = {
      fontFace: FONT, fontSize: fs, color: header ? C.white : C.ink, bold: header || bold.has(r),
      fill: { color: header ? C.navy : hl.has(`${r},${c}`) ? C.pale : r % 2 ? C.white : "F9FBFD" },
      align: c === 0 || (o.leftCols || []).includes(c) ? "left" : "center", valign: "middle",
      border: [{ type: "none" }, { type: "none" }, { type: "solid", pt: 0.5, color: C.line }, { type: "none" }],
      margin: [0.02, 0.08, 0.02, 0.08],
    };
    if (hl.has(`${r},${c}`)) { opt.bold = true; opt.color = C.navy; }
    return { text: cell, options: opt };
  }));
  s.addTable(body, { x, y, w: colW.reduce((a, b) => a + b, 0), colW, rowH });
}

function eq(s, text, x, y, w, h, fs) {
  card(s, x, y, w, h, { flat: true });
  s.addText(text, { x: x + 0.1, y, w: w - 0.2, h, fontFace: "Cambria Math", fontSize: fs || 16, color: C.navy, align: "center", valign: "middle", margin: 0 });
}

function writeGuide() {
  const fs = require("fs");
  const main = GUIDE.filter((g) => g.n <= NMAIN);
  let cum = 0;
  const rows = [];
  const checkpoints = [];
  main.forEach((g, i) => {
    cum += g.mins;
    rows.push(`| ${g.n} | ${g.title} | ${g.mins} | ${cum} |`);
    if (i === main.length - 1 || SEC[i + 1] !== SEC[i]) checkpoints.push(`- End of **${SECTIONS[SEC[i]]}** (slide ${g.n}): ${cum} min on the clock.`);
  });
  const md = [
    "# Presenter guide",
    "",
    "Generated by `src/build_deck.js` from the same cues as the speaker notes, so the two cannot drift apart.",
    `Talk length: **${cum} minutes** across ${NMAIN} slides, which leaves room inside a 30 to 40 minute slot.`,
    "",
    "## Time checkpoints (glance at the clock here)",
    "",
    ...checkpoints,
    "",
    "If you are more than two minutes over at the end of Methods, cut slide 12 (model suite), slide 23 (weather through the threshold) and slide 30 (limitations, say two sentences) rather than rushing the results.",
    "",
    "## How to deliver it",
    "",
    "- One message per slide: say the takeaway bar aloud, in your own words, before you leave the slide.",
    "- The talk has one spine: *the alarm budget moves the hit rate by about 50 points, the model by about 5.* Every section either sets it up (data, methods), earns it (RQ1 to RQ3) or defends it (robustness, limits).",
    "- Look at the audience on the headline numbers, and at the slide only to point.",
    "- Never read the notes: they are cues. Rehearse three times aloud with a timer, once with the backup questions B8 and B9.",
    "- Hard questions are welcome: state the limit before they do. The report already does, and the slides say so.",
    "",
    "## Before the day (yours to do)",
    "",
    "- [ ] Open the .pptx in PowerPoint (not just a viewer) and flip through once: check line breaks, since this deck was checked with a stand-in for Calibri.",
    "- [ ] Send the deck to Dr Tian a week ahead and ask for one round of feedback; he responded quickly to the report.",
    "- [ ] Check the oral's marking rubric. If it weights clarity, timing or questions, re-balance: the talk is built to give clarity and a defensible Q&A.",
    "- [ ] Rehearse aloud with a timer, three times; once for someone outside mathematics. The test: can they say the main finding back in one sentence (the dial matters more than the detector)?",
    "- [ ] Put the PDF on a USB stick and in the cloud as a fallback; check the room's screen ratio (the deck is 16:9).",
    "- [ ] Know slides 4, 25 and 28 cold: they carry the idea in one picture, what a budget means, and the central result.",
    "",
    "## One-page cue card (say the takeaway in your own words, then move on)",
    "",
    "| Slide | Title | Takeaway |",
    "|---|---|---|",
    ...main.map((g) => `| ${g.n} | ${g.title} | ${TAKE[g.n] || (g.cue.say || "").split(". ")[0] + "."} |`),
    "",
    "## Timing table",
    "",
    "| Slide | Title | Minutes | Running total |",
    "|---|---|---|---|",
    ...rows,
    "",
    "## Cues, slide by slide",
    "",
    ...GUIDE.flatMap((g) => {
      const label = g.n <= NMAIN ? `### ${g.n}. ${g.title}` : `### B${g.n - NMAIN}. ${g.title}`;
      const lines = [label, ""];
      if (g.cue.say) lines.push(`- **Say:** ${g.cue.say}`);
      if (g.cue.show) lines.push(`- **Point to:** ${g.cue.show}`);
      if (g.cue.ask) lines.push(`- **If asked:** ${g.cue.ask}`);
      if (g.cue.next) lines.push(`- **Transition:** ${g.cue.next}`);
      lines.push("");
      return lines;
    }),
  ].join("\n");
  fs.writeFileSync(path.join(__dirname, "..", "PRESENTER_GUIDE.md"), md);
}

// ====================================================================================
async function build() {
  // ---------- 1. Title ----------
  {
    const s = pptx.addSlide();
    n += 1;
    s.background = { color: C.navy };
    s.addShape(pptx.ShapeType.rect, { x: 8.4, y: 0, w: W - 8.4, h: H, fill: { color: C.white }, line: { color: C.white } });
    s.addImage({ path: path.join(REPORT, "monash-logo.png"), x: 8.9, y: 0.55, w: 3.5, h: (3.5 * 430) / 1470, altText: ALT["monash-logo.png"] });
    s.addText("MTH5000 MASTERS RESEARCH PROJECT  |  ORAL PRESENTATION", { x: MX, y: 0.7, w: 7.4, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: "8FC3E8", charSpacing: 2, margin: 0 });
    s.addText("Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities", { x: MX, y: 1.3, w: 7.4, h: 2.4, fontFace: FONT, fontSize: 38, bold: true, color: C.white, valign: "top", margin: 0 });
    s.addText(
      [
        { text: "Jaykumar Vinodbhai Chauhan", options: { bold: true, breakLine: true } },
        { text: "Student ID 34710280  |  Master of Mathematics", options: { breakLine: true } },
        { text: "Supervisor: Dr Tianhai Tian", options: { breakLine: true } },
        { text: "School of Mathematics, Monash University  |  November 2026" },
      ],
      { x: MX, y: 3.85, w: 7.4, h: 1.5, fontFace: FONT, fontSize: 16, color: "C9DCEC", valign: "top", margin: 0, paraSpaceAfter: 4 }
    );
    s.addImage({ path: path.join(SLIDES, "skyline.png"), x: 0, y: 5.95, w: 8.4, h: 1.5, altText: ALT["skyline.png"] });
    s.addText("The last 365 days of the dataset: one bar a day, vermillion above the 121 threshold.", { x: MX, y: 5.5, w: 7.6, h: 0.3, fontFace: FONT, fontSize: 11.5, italic: true, color: "8FA6BD", margin: 0 });
    s.addText("THE FINDING IN TWO NUMBERS", { x: 8.9, y: 2.6, w: 3.9, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
    s.addText("0.379 to 0.881", { x: 8.9, y: 2.95, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 36, bold: true, color: C.verm, margin: 0 });
    s.addText("hit rate at one day ahead as the alarm budget moves from 40 to 100 alarms a year", { x: 8.9, y: 3.7, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 14, color: C.grey, valign: "top", margin: 0 });
    s.addText("about 5 points", { x: 8.9, y: 4.75, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 36, bold: true, color: C.blue, margin: 0 });
    s.addText("what changing the model moves it by, at a fixed budget", { x: 8.9, y: 5.5, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 14, color: C.grey, valign: "top", margin: 0 });
    TAKE[1] = "The dial matters more than the detector: the alarm budget moves the hit rate by about 50 points, the model by about 5.";
    GUIDE.push({ n, title: "Title", mins: MINS[0], cue: { say: "Good morning. The answer to build to: the number of alarms a health authority is willing to raise matters many times more than which model produces the forecast.", next: "First, why the question matters." } });
    s.addNotes(notesFor({
      say: "Good morning. I asked how well machine learning can forecast hazardous air quality days in Delhi. The answer I want to build to is on the right: the number of alarms a health authority is willing to raise matters many times more than which model produces the forecast.",
      show: "the strip along the bottom: the last year of the data, one bar a day. The orange days are the ones the project is about.",
      next: "First, why the question matters.",
    }));
  }

  // ---------- 2. Why it matters ----------
  {
    const s = base("A forecast is only useful if it arrives before the hazardous day does", {
      say: "Sustained PM2.5 exposure is linked to cardiopulmonary and all-cause mortality, so I forecast a health threshold, not a round number: 121 µg/m³, the CPCB 'Very Poor' boundary. At my monitor 29.7 percent of days exceed it. Existing Delhi machine learning studies report R squared, RMSE and MAE; neither evaluates a warning system. I grew up in India, so this is not an abstract statistic for me.",
      show: "the four stat cards, then the takeaway.",
      ask: "121 is the CPCB National Air Quality Index boundary of the category below 'Severe', for the 24-hour mean.",
      next: "That gap gives me three research questions.",
    });
    bullets(s, [
      ["Health basis. ", "PM2.5 exposure is linked to cardiopulmonary and all-cause mortality (Pope and Dockery 2006; Chen and Hoek 2020)."],
      ["The event. ", "A day above 121 µg/m³, the CPCB 'Very Poor' boundary."],
      ["The gap. ", "Two Delhi machine learning studies (Masood and Ahmad 2020; Singh and Srivastava 2025) report R², RMSE and MAE. Neither evaluates a warning system with an explicit alarm budget."],
    ], MX, 1.85, 7.2, 4.2, { fontSize: 20, gap: 14 });
    stat(s, 8.3, 1.85, 2.15, 1.75, "29.7%", "of days exceed 121 µg/m³ (920 of 3,093)", C.verm);
    stat(s, 10.6, 1.85, 2.15, 1.75, "9.8 yrs", "of daily data, Nov 2016 to Aug 2026");
    stat(s, 8.3, 3.8, 2.15, 1.75, "1 to 3", "days ahead: the forecast horizons");
    stat(s, 10.6, 3.8, 2.15, 1.75, "12", "model specifications compared");
    takeaway(s, "A model with good average error can still miss the extreme days that are the only ones anyone cares about.");
  }

  // ---------- 3. Research questions ----------
  {
    const s = base("Three research questions, and the third turned out to dominate the other two", {
      say: "One: how accurately can concentrations be forecast one to three days ahead by machine learning, against classical and naive benchmarks. Two: forecast the concentration then threshold it, or classify the exceedance directly. Three: as a warning system, what hit rate and false alarm rate does each approach achieve, and how does the decision threshold trade them off. The answers are on the cards; I will earn each one with evidence.",
      show: "the bold answer on each card, RQ3 in vermillion.",
      next: "First, one picture that holds the whole talk.",
    });
    const rq = [
      ["RQ1", "Accuracy", "How accurately can daily concentrations be forecast 1 to 3 days ahead by machine learning, against classical and naive benchmarks?", "The classical model (ARIMA) beats every ML regressor at every horizon. The deep networks beat it only at one day ahead."],
      ["RQ2", "Two arms", "Is it better to forecast the concentration and then threshold it, or to classify the exceedance event directly?", "Neither dominates: 21 / 11 / 4 across 36 matched comparisons. Forecast-then-threshold is preferred."],
      ["RQ3", "Warning system", "As a warning system, what hit rate and false alarm rate does each approach achieve, and how does the threshold trade them off?", "The alarm budget moves hit rate by 50 points. The model moves it by about 5."],
    ];
    const cw = 3.85, gap = 0.2;
    rq.forEach((r, i) => {
      const x = MX + i * (cw + gap);
      card(s, x, 1.8, cw, 4.2);
      s.addText(r[0], { x: x + 0.25, y: 1.92, w: 1.2, h: 0.5, fontFace: FONT, fontSize: 26, bold: true, color: i === 2 ? C.verm : C.blue, margin: 0 });
      s.addText(r[1].toUpperCase(), { x: x + 1.3, y: 1.97, w: cw - 1.5, h: 0.4, fontFace: FONT, fontSize: 11, bold: true, color: C.grey, charSpacing: 2, valign: "middle", margin: 0 });
      s.addText(r[2], { x: x + 0.25, y: 2.5, w: cw - 0.5, h: 1.5, fontFace: FONT, fontSize: 16, color: C.ink, valign: "top", margin: 0 });
      s.addShape(pptx.ShapeType.rect, { x: x + 0.25, y: 4.05, w: cw - 0.5, h: 0.02, fill: { color: C.line }, line: { color: C.line, width: 0 } });
      s.addText("HEADLINE ANSWER", { x: x + 0.25, y: 4.15, w: cw - 0.5, h: 0.3, fontFace: FONT, fontSize: 10.5, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      s.addText(r[3], { x: x + 0.25, y: 4.48, w: cw - 0.5, h: 1.45, fontFace: FONT, fontSize: 16.5, bold: true, color: C.navy, valign: "top", margin: 0 });
    });
    takeaway(s, "The third question turns out to dominate the other two, and the talk is organised around it.");
  }

  // ---------- 4. The idea in one picture ----------
  {
    const s = base("The idea in one picture: the detector matters little, the dial matters a lot", {
      say: "Think of a smoke alarm. There are two things you can change: which detector you buy, and how sensitive you set the dial. On the left I swap the forecasting model at a fixed budget of 100 alarms a year: hit rates 0.82 to 0.87. On the right I keep the best model and turn the dial from 40 to 100 alarms a year: 0.38 to 0.88. Same axis. The rest of the talk is the evidence for this picture, and the care taken not to fool myself.",
      show: "the left panel is almost flat; the right panel climbs. Same vertical scale.",
      ask: "Both panels are one day ahead, from Table 4.7. The left uses four representative models at 100 alarms (as in the report's Figure 4.5); the weak lag-7 seasonal-naive benchmark would be lower, 0.758. The right uses the best model at each budget.",
      next: "Here is the route to that evidence.",
    });
    await figure(s, SLIDES, "dial_vs_detector.png", MX, 1.75, W - 2 * MX, 3.65, { bare: true });
    caption(s, "Hit rate (the share of hazardous days caught) at one day ahead, Table 4.7. Four representative models; the weak lag-7 seasonal-naive benchmark would sit lower, at 0.758 (B8).", MX, 5.55, 11.5, { h: 0.5 });
    takeaway(s, "Like a smoke alarm: swapping the brand moves the hit rate from 0.82 to 0.87; turning the sensitivity dial moves it from 0.38 to 0.88.");
  }

  // ---------- 5. Roadmap ----------
  {
    const s = base("The route: from the data, through the models, to the alarm budget", {
      say: "Roughly seven minutes on the data and what was wrong with it, five on the models and how they are tested, eleven on results against the three questions, then limits and conclusions. Keep one question in mind: how much does the model matter, compared with the number of alarms you allow?",
      next: "Start with the data.",
    });
    const steps = [
      [1, "Data", "one station, two defects, no weekly cycle"],
      [2, "Methods", "twelve models, rolling-origin tests, warning measures"],
      [3, "Results", "RQ1 accuracy, RQ2 two arms, RQ3 the alarm budget"],
      [4, "Discussion", "robustness checks and limits"],
      [5, "Conclusion", "contributions and the recommendation"],
    ];
    const cw = 2.3, gap = 0.16;
    steps.forEach(([k, name, desc], i) => {
      const x = MX + i * (cw + gap);
      card(s, x, 1.95, cw, 3.4);
      s.addShape(pptx.ShapeType.ellipse, { x: x + 0.25, y: 2.15, w: 0.6, h: 0.6, fill: { color: k === 3 ? C.verm : C.blue }, line: { color: C.white, width: 0 } });
      s.addText(String(i + 1), { x: x + 0.25, y: 2.15, w: 0.6, h: 0.6, fontFace: FONT, fontSize: 20, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      s.addText(name, { x: x + 0.25, y: 2.95, w: cw - 0.4, h: 0.45, fontFace: FONT, fontSize: 20, bold: true, color: C.navy, margin: 0 });
      s.addText(`about ${secMinutes(k)} min`, { x: x + 0.25, y: 3.4, w: cw - 0.4, h: 0.3, fontFace: FONT, fontSize: 13, bold: true, color: k === 3 ? C.verm : C.blue, margin: 0 });
      s.addText(desc, { x: x + 0.25, y: 3.8, w: cw - 0.45, h: 1.4, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    });
    s.addText("How to read the colours:", { x: MX, y: 5.5, w: 2.4, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: C.grey, valign: "middle", margin: 0 });
    [[C.blue, "data and models"], [C.navy, "ARIMA, the benchmark"], [C.verm, "the number to remember"]].forEach(([col, lab], i) => {
      const x = MX + 2.5 + i * 3.1;
      s.addShape(pptx.ShapeType.roundRect, { x, y: 5.55, w: 0.45, h: 0.25, rectRadius: 0.05, fill: { color: col }, line: { color: col, width: 0 } });
      s.addText(lab, { x: x + 0.55, y: 5.5, w: 2.4, h: 0.35, fontFace: FONT, fontSize: 13, color: C.ink, valign: "middle", margin: 0 });
    });
    takeaway(s, "Hold one question in mind: how much does the model matter, compared with the number of alarms you allow?");
  }

  // ---------- 5. Data ----------
  {
    const s = base("One well-characterised Delhi monitor, nearly ten years of daily PM2.5", {
      say: "Data come from OpenAQ. I compared five stations within 25 km on coverage rather than nominal record length and found every CPCB station serves data only from 19 February 2025, about eighteen months, although the metadata advertises 2016. Only location 8118 returns the full record. The cost, stated plainly: it is an AirNow feed, almost certainly a US diplomatic post monitor, so every number describes one site, not Delhi.",
      show: "the table, then the cost box on the right.",
      ask: "Four independent stations sharing an identical cutoff points to a limit of the measurements endpoint, not coincidence.",
      next: "That series had two defects.",
    });
    table(s, [
      ["Quantity", "Value after cleaning"],
      ["Source", "OpenAQ location 8118, sensor 23534, AirNow"],
      ["Period", "2016-11-09 to 2026-08-27"],
      ["Calendar days", "3,579"],
      ["Usable daily means", "3,093 (86.4% of calendar)"],
      ["Longest gap", "34 consecutive days"],
      ["Mean, median, maximum", "102.7, 71.7, 896.0 µg/m³"],
      ["Days above 121", "920 (29.7%)"],
    ], MX, 1.85, [2.7, 3.75], 0.47, { fontSize: 15 });
    caption(s, "Report Table 3.1.", MX, 5.7, 6);
    card(s, 7.7, 1.85, 5.05, 3.95);
    s.addText("Why station 8118, and what it costs", { x: 7.95, y: 1.97, w: 4.6, h: 0.4, fontFace: FONT, fontSize: 18, bold: true, color: C.navy, margin: 0 });
    bullets(s, [
      "Five stations compared on coverage, not nominal record length.",
      "Every CPCB station serves data only from 19 Feb 2025 (about 18 months).",
      "Only 8118 returns the full record.",
      ["Cost: ", "an AirNow feed, almost certainly a US diplomatic post monitor. Results describe one site."],
    ], 7.95, 2.5, 4.6, 3.2, { fontSize: 16 });
    takeaway(s, "One reference site with a full decade of record: good for comparing methods, not a claim about all of Delhi.");
  }

  // ---------- 6. Two defects ----------
  {
    const s = base("Two defects in the source data were found and corrected before any model was fitted", {
      say: "First, impossible values: five negatives, and 1990 appearing three times identically, one on 2 September in the monsoon between neighbours of 42 and 178. That is a clipped instrument ceiling. Second, the coverage statistic divided observation count by 24, but the sensor was half-hourly until 2024, so half a day of a polluted afternoon was scored as a complete day. Days at 50 to 75 percent true coverage gave implausible values about seven times as often as days above 90. I took the cadence from the data instead.",
      show: "left: sensor cadence against the assumed 24. right: implausible rate by true coverage.",
      ask: "1,085 of 3,467 days fall below 75 percent true coverage, far more than the 268 with no value at all. 1000 is a judgement; sensitivity check in the robustness slide.",
      next: "With clean data, what does the series look like?",
    });
    s.addText("(a) What the sensor really reports", { x: MX, y: 1.6, w: 6.0, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0 });
    s.addText("(b) Implausible values, by true coverage", { x: 6.9, y: 1.6, w: 5.8, h: 0.3, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, margin: 0 });
    await figure(s, SLIDES, "cadence.png", MX, 2.1, 6.0, 2.4);
    await figure(s, SLIDES, "implausible.png", 6.9, 2.1, 5.85, 2.4);
    card(s, MX, 4.75, 6.0, 1.3);
    s.addText([{ text: "A clipped ceiling. ", options: { bold: true, color: C.verm } }, { text: "1990 appears three times identically, once on 2 September, in the monsoon, between days of 42 and 178. Five negatives too." }], { x: MX + 0.2, y: 4.75, w: 5.6, h: 1.3, fontFace: FONT, fontSize: 14.5, color: C.ink, valign: "middle", margin: 0 });
    card(s, 6.75, 4.75, 6.0, 1.3);
    s.addText([{ text: "A wrong denominator. ", options: { bold: true, color: C.verm } }, { text: "Completeness assumed 24 readings a day. 1,085 of 3,467 days are below 75% true coverage; only 268 have no value at all." }], { x: 6.95, y: 4.75, w: 5.6, h: 1.3, fontFace: FONT, fontSize: 14.5, color: C.ink, valign: "middle", margin: 0 });
    takeaway(s, "Rules: below 0 (5 days), coverage below 50% (270), above 1000 (7): 282 of 3,375 removed, and the exceedance rate moves only 30.0% to 27.0%.");
  }

  // ---------- 7. Series ----------
  {
    const s = base("Exceedances arrive as multi-day winter episodes, and that is the structure worth forecasting", {
      say: "The cleaned series, with days above the threshold shaded. They come in winter episodes, not isolated days, which is why persistence turns out to be a strong forecast. The distribution is strongly right skewed, skewness 2.17 and excess kurtosis 8.31, so every model is fitted to the logarithm; annual Fourier terms explain 69 percent of the variance of the log.",
      show: "the shaded episodes, then the four skew statistics.",
      next: "The same data as a calendar.",
    });
    const b = await figure(s, SLIDES, "series.png", MX, 1.85, W - 2 * MX, 2.85);
    caption(s, "The cleaned daily series (report Figure 3.2, redrawn); days above the hazard threshold are shaded. Maximum 896.0 on 2017-11-08.", MX, b.y + b.h + 0.18, 11);
    [["102.7", "mean µg/m³"], ["71.7", "median"], ["2.17", "skewness"], ["8.31", "excess kurtosis"]].forEach((t, i) => {
      const x = MX + i * 3.06;
      card(s, x, 5.25, 2.9, 0.85);
      s.addText(t[0], { x: x + 0.2, y: 5.25, w: 1.4, h: 0.85, fontFace: FONT, fontSize: 28, bold: true, color: C.blue, valign: "middle", margin: 0 });
      s.addText(t[1], { x: x + 1.55, y: 5.25, w: 1.35, h: 0.85, fontFace: FONT, fontSize: 14, color: C.grey, valign: "middle", margin: 0 });
    });
    takeaway(s, "Episodes make persistence a strong forecast, and the heavy right tail is why every model is fitted to log PM2.5.");
  }

  // ---------- 7b. Calendar ----------
  {
    const s = base("Every year, the same months: hazardous days gather from October to February", {
      say: "Another view of the same data. Each cell is a month; darker means more of its days were above 121. The pattern repeats every year: October to February is dark, June to September is almost clear. This regularity is the annual cycle the models carry, and it is why a calendar-only forecast, climatology, is a surprisingly strong baseline.",
      show: "the dark columns, then the pale monsoon months.",
      ask: "Months with fewer than 15 usable days are left blank. 2016 starts in November and 2026 ends in August.",
      next: "Is there any other seasonality, say weekly?",
    });
    await figure(s, SLIDES, "calendar.png", MX, 1.8, 7.6, 4.2);
    bullets(s, [
      ["Each cell is a month; ", "the darker, the larger the share of its days above 121."],
      ["The pattern repeats every year: ", "October to February is dark; the monsoon months are almost clear."],
      ["That regularity ", "is the annual cycle the models carry, and why a calendar-only forecast (climatology) is a strong baseline."],
    ], 8.5, 1.9, 4.25, 4.1, { fontSize: 17, gap: 12 });
    takeaway(s, "Hazard is seasonal and arrives in episodes, so the calendar alone is already a strong baseline that a model has to beat.");
  }

  // ---------- 8. No weekly cycle ----------
  {
    const s = base("An assumption from the approved proposal fails: there is no weekly cycle at this station", {
      say: "The proposal assumed a weekly cycle alongside the annual one and treated two seasonal periods as the central difficulty. I tested it three ways. The periodogram's dominant periods are the annual cycle and harmonics, nothing near seven days. The autocorrelation at lag 7 sits on the decay curve between lags 6 and 8. Day of week gives a 6.5 percent spread with p = 0.34 and a rank test p = 0.77. Three tests with different assumptions agreeing is what makes the absence convincing.",
      show: "7 days on the periodogram; the circled lags; zero inside every interval.",
      ask: "A weekly rhythm is a traffic signature; 8118 is in a diplomatic enclave, not roadside like ITO or Anand Vihar.",
      next: "So the annual cycle is the only seasonality to model.",
    });
    const cols = [
      ["Periodogram", "periodogram.png", "Dominant periods 357.9, 178.9, 188.4, 397.7, 325.4, 60.7 days. None near 7."],
      ["Autocorrelation", "acf.png", "Lag 7 = 0.173, between lag 6 (0.179) and lag 8 (0.153): on the decay, not above it."],
      ["Day of week", "dow.png", "6.5% spread. ANOVA F = 1.13, p = 0.34. Kruskal-Wallis p = 0.77."],
    ];
    for (let i = 0; i < 3; i++) {
      const x = MX + i * 4.1;
      card(s, x, 1.8, 3.95, 4.25);
      s.addText(cols[i][0], { x: x + 0.2, y: 1.88, w: 3.55, h: 0.35, fontFace: FONT, fontSize: 16, bold: true, color: C.blue, margin: 0 });
      await figure(s, SLIDES, cols[i][1], x + 0.1, 2.3, 3.75, 2.45, { bare: true });
      s.addText(cols[i][2], { x: x + 0.2, y: 4.85, w: 3.55, h: 1.1, fontFace: FONT, fontSize: 14.5, color: C.ink, valign: "top", margin: 0 });
    }
    takeaway(s, "Three independent tests agree: ARIMA carries the annual cycle only, with no weekly seasonal order.");
  }

  // ---------- 9. Annual cycle and ARIMA ----------
  {
    const s = base("The annual cycle is unmistakable, so ARIMA carries it with Fourier terms and no weekly order", {
      say: "The annual cycle is the opposite: high in winter, low in the monsoon, which is what makes the missing weekly cycle credible. The benchmark is ARIMA on the log series with four annual Fourier pairs as exogenous regressors. The order was chosen by AIC over a 24-candidate grid: (1,1,1) scores 1892.5, the next, (1,1,2), 1893.6, a gap of 1.1, too small to call, so parsimony decides. Fitted phi 0.581, theta minus 0.987, which is 0.013 inside the invertibility boundary.",
      show: "the equation: AR and MA part, then the Fourier sum.",
      ask: "In the rolling refits theta crosses the boundary at 3 of 28 refits, each with fewer than 1,700 training days; the optimiser is unconstrained so the forecast is still produced and scored. Backup B5.",
      next: "Around that benchmark, the model suite.",
    });
    await figure(s, SLIDES, "annual.png", MX, 1.85, 5.2, 3.95);
    caption(s, "Monthly median with interquartile range (report Figure 3.5, redrawn).", MX, 5.85, 5.2);
    eq(s, "(1 − ϕ₁B)(1 − B) yₜ = c + (1 + θ₁B) εₜ\n+ Σₖ₌₁⁴ [ αₖ sin(2πkt/365.25) + βₖ cos(2πkt/365.25) ]", 6.2, 1.85, 6.55, 1.2, 16);
    s.addText("yₜ = log(PM2.5), B is the backshift operator, K = 4 annual Fourier pairs.", { x: 6.2, y: 3.12, w: 6.55, h: 0.35, fontFace: FONT, fontSize: 12.5, italic: true, color: C.grey, margin: 0 });
    bullets(s, [
      ["Order by AIC ", "over a 24-candidate grid: (1,1,1) at 1892.5, next (1,1,2) at 1893.6."],
      ["Fitted: ", "ϕ₁ = 0.581 and θ₁ = −0.987, which is 0.013 inside the invertibility boundary."],
      ["Back-transform: ", "median exp(m); mean exp(m + s²/2). Both reported."],
    ], 6.2, 3.65, 6.55, 2.4, { fontSize: 16.5 });
    takeaway(s, "A simpler, better-identified specification: the data justified dropping the weekly term, and the Fourier terms carry the season.");
  }

  // ---------- 10. Model suite ----------
  {
    const s = base("Twelve specifications from three families, all scored by one protocol", {
      say: "Classical and naive: persistence, climatology, seasonal naive at lag 7, and ARIMA. Machine learning: ridge, random forest and histogram gradient boosting, the trees each on the level and on the change from the origin. Deep learning: a GRU, an LSTM and a transformer, each over ten seeds. Dr Tian asked for machine learning rather than relying on ARIMA, and several methods tried; ARIMA stays as the reference point.",
      ask: "A Kolmogorov-Arnold-LSTM hybrid, which Dr Tian named, was tried as a bounded check only.",
      next: "Two lines on the regressors, then the networks.",
    });
    const cols = [
      ["Classical and naive", C.grey, ["Persistence (repeat today)", "Climatology", "Seasonal naive, lag 7", "ARIMA(1,1,1) + annual Fourier terms"]],
      ["Machine learning", C.blue, ["Ridge regression", "Random forest: level and change", "Histogram gradient boosting: level and change"]],
      ["Deep learning, 10 seeds each", C.verm, ["GRU", "LSTM", "Transformer encoder", "Kolmogorov-Arnold-LSTM: bounded check only"]],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 4.1;
      card(s, x, 1.85, 3.95, 3.8);
      s.addShape(pptx.ShapeType.rect, { x, y: 1.85, w: 3.95, h: 0.65, fill: { color: c[1] }, line: { color: c[1], width: 0 } });
      s.addText(c[0], { x: x + 0.2, y: 1.85, w: 3.6, h: 0.65, fontFace: FONT, fontSize: 17, bold: true, color: C.white, valign: "middle", margin: 0 });
      bullets(s, c[2], x + 0.2, 2.75, 3.55, 2.9, { fontSize: 19, gap: 12 });
    });
    takeaway(s, "Fitted to log PM2.5, forecast at h = 1, 2, 3 days, refitted as the training window expands, scored on identical origins by identical code.");
  }

  // ---------- 11. ML regressors ----------
  {
    const s = base("Three regressors, each controlling variance by a different mechanism", {
      say: "Ridge shrinks coefficients and has a closed form: X transpose X plus lambda I is positive definite for any lambda above zero, so a unique solution exists even with collinear lags. A random forest averages B trees; the variance of the average is rho sigma squared plus one minus rho over B sigma squared. The second term vanishes as B grows, the first is a floor, and random feature subsets lower rho. Boosting fits each tree to the pseudo-residual, the negative gradient of the loss, which is descent in function space.",
      show: "the three formulas, left to right.",
      ask: "Trees were fitted to level and change because a tree cannot extrapolate beyond the targets it saw, and this series drifts across the decade. Missing values are never imputed; histogram boosting accepts them natively.",
      next: "Now the deep networks.",
    });
    const cols = [
      ["Ridge regression", "SHRINKAGE", "β̂ = (XᵀX + λI)⁻¹ Xᵀy", ["Closed form: unique for any λ > 0, even with collinear lags.", "λ by cross-validation at every refit."]],
      ["Random forest", "BAGGING", "Var f̂(x) = ρσ² + (1 − ρ)σ² / B", ["Average of B trees on bootstrap resamples.", "Random feature subsets lower ρ, the floor averaging cannot beat."]],
      ["Histogram gradient boosting", "ADDITIVE CORRECTION", "Fₘ = Fₘ₋₁ + ν hₘ", ["Each tree fits the pseudo-residual: descent in function space.", "Binned features accept missing values, so nothing is imputed."]],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 4.1;
      card(s, x, 1.85, 3.95, 4.15);
      s.addText(c[0], { x: x + 0.2, y: 1.95, w: 3.55, h: 0.4, fontFace: FONT, fontSize: 18, bold: true, color: C.navy, margin: 0 });
      s.addText(c[1], { x: x + 0.2, y: 2.35, w: 3.55, h: 0.3, fontFace: FONT, fontSize: 10.5, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      eq(s, c[2], x + 0.2, 2.75, 3.55, 0.85, 16);
      bullets(s, c[3], x + 0.2, 3.8, 3.55, 2.1, { fontSize: 17 });
    });
    takeaway(s, "Trees are fitted to both the level and the change from the origin, because a tree cannot extrapolate and this series drifts.");
  }

  // ---------- 12. Networks ----------
  {
    const s = base("Three networks under one protocol, so the comparison is the cell and nothing else", {
      say: "The GRU has two gates and no separate memory cell; the LSTM three gates and an explicit cell state; the transformer replaces recurrence with self-attention. All three read the same 30-day window of six channels and predict the change in log concentration, with Adam on absolute error and early stopping, over ten seeds. The LSTM and transformer were added only after Dr Tian's feedback challenged the GRU-over-LSTM and small-data arguments, so I tested them rather than assuming.",
      show: "the parameter column: 2,329, 3,097, 3,409, 3,288, confirmed by counting the fitted objects.",
      ask: "Recurrent nets need a value at every timestep, so gaps are forward-filled with a missingness flag; the transformer reuses that as an implementation choice, not a necessity.",
      next: "How do we score them without fooling ourselves?",
    });
    table(s, [
      ["Architecture", "Size", "Optimiser", "Parameters"],
      ["GRU", "24 hidden units", "Adam, lr = 0.01", "2,329"],
      ["LSTM", "24 hidden units", "Adam, lr = 0.01", "3,097"],
      ["Transformer", "d_model = 16, 2 heads, 1 layer", "Adam, lr = 0.001", "3,409"],
      ["Kolmogorov-Arnold-LSTM", "24 hidden units, grid size 5", "Adam, lr = 0.01", "3,288"],
    ], MX, 1.85, [2.7, 3.5, 2.2, 1.6], 0.6, { fontSize: 15 });
    caption(s, "Report Table 3.6. Parameters are for the six-channel network, confirmed against the fitted model objects.", MX, 4.95, 10);
    bullets(s, [
      ["Shared input: ", "last 30 days; log PM2.5, a missingness flag, two annual Fourier pairs."],
      ["Shared training: ", "target is the change in log concentration; Adam on absolute error; early stopping on the latest 15%."],
      ["Reported as a range ", "over ten seeds, never one favourable seed."],
    ], MX, 5.3, 10.0, 0.85, { fontSize: 14.5, gap: 3 });
    card(s, 10.65, 1.85, 2.1, 3.0, { fill: C.navy, flat: true });
    s.addText("Gates", { x: 10.8, y: 1.95, w: 1.8, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: "8FC3E8", margin: 0 });
    s.addText("GRU: 2\nLSTM: 3 + cell state\nTransformer: self-attention", { x: 10.8, y: 2.35, w: 1.85, h: 2.3, fontFace: FONT, fontSize: 14, color: C.white, valign: "top", margin: 0, paraSpaceAfter: 8 });
    takeaway(s, "Only the cell differs: gated recurrence, a memory cell, or attention. Each is reported as a ten-seed range.");
  }

  // ---------- 13. Rolling origin ----------
  {
    const s = base("Rolling-origin evaluation: 2,303 forecasts, none of which can see the future", {
      say: "Every model is scored at 2,303 origins over 6.8 years after a three-year burn-in, refitted every 90 days, the networks every 180. The invariant is that at origin t a model may use observations up to and including day t and nothing else. Nothing fails visibly when that breaks; the numbers just improve. So it is tested: corrupt the series from a chosen date, rerun, and require that no earlier forecast changes. A single split would have misled me: ARIMA scored 0.903 on one calm block and 0.940 under the rolling harness.",
      show: "the timeline, then 0.903 to 0.940.",
      ask: "The label on feature row t' is the value at t' + h, so the training set ends at t minus h; hence one model per horizon.",
      next: "Now the measures.",
    });
    const tx = MX, tw = W - 2 * MX, ty = 1.95, burn = (tw * 3) / 9.8;
    s.addShape(pptx.ShapeType.rect, { x: tx, y: ty, w: burn, h: 0.7, fill: { color: C.line }, line: { color: C.line, width: 0 } });
    s.addShape(pptx.ShapeType.rect, { x: tx + burn, y: ty, w: tw - burn, h: 0.7, fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
    s.addText("3-year burn-in", { x: tx, y: ty, w: burn, h: 0.7, fontFace: FONT, fontSize: 15, bold: true, color: C.navy, align: "center", valign: "middle", margin: 0 });
    s.addText("2,303 forecast origins over 6.8 years, refitted every 90 days (networks: 180)", { x: tx + burn, y: ty, w: tw - burn, h: 0.7, fontFace: FONT, fontSize: 15, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
    s.addText("Nov 2016", { x: tx, y: ty + 0.75, w: 2, h: 0.3, fontFace: FONT, fontSize: 12, color: C.grey, margin: 0 });
    s.addText("9 Nov 2019", { x: tx + burn - 0.6, y: ty + 0.75, w: 1.4, h: 0.3, fontFace: FONT, fontSize: 12, color: C.grey, margin: 0 });
    s.addText("24 Aug 2026", { x: tx + tw - 1.6, y: ty + 0.75, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 12, color: C.grey, align: "right", margin: 0 });
    bullets(s, [
      ["Invariant: ", "at origin t, observations up to and including day t, and nothing else."],
      ["Tested, not assumed: ", "corrupt the series from a chosen date, rerun, and require no earlier forecast to change."],
      ["One model per horizon: ", "the label on row t′ is the value at t′ + h, so training ends at t − h."],
    ], MX, 3.3, 7.1, 2.7, { fontSize: 17 });
    card(s, 8.2, 3.3, 4.55, 2.7);
    s.addText("Why not one train-test split?", { x: 8.4, y: 3.4, w: 4.15, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, margin: 0 });
    s.addText("0.903", { x: 8.4, y: 3.85, w: 1.9, h: 0.8, fontFace: FONT, fontSize: 38, bold: true, color: C.grey, valign: "middle", margin: 0 });
    s.addText("single block", { x: 8.4, y: 4.65, w: 1.9, h: 0.3, fontFace: FONT, fontSize: 13, color: C.grey, margin: 0 });
    s.addText("→", { x: 10.2, y: 3.85, w: 0.6, h: 0.8, fontFace: FONT, fontSize: 30, color: C.grey, align: "center", valign: "middle", margin: 0 });
    s.addText("0.940", { x: 10.8, y: 3.85, w: 1.9, h: 0.8, fontFace: FONT, fontSize: 38, bold: true, color: C.verm, valign: "middle", margin: 0 });
    s.addText("rolling origin", { x: 10.8, y: 4.65, w: 1.9, h: 0.3, fontFace: FONT, fontSize: 13, color: C.grey, margin: 0 });
    s.addText("ARIMA rMAE at one day. The single block was calmer and flattered every model.", { x: 8.4, y: 5.05, w: 4.15, h: 0.85, fontFace: FONT, fontSize: 14, color: C.ink, valign: "top", margin: 0 });
    takeaway(s, "The protocol is the credibility of every number that follows: leakage-tested, and one draw of history is never trusted.");
  }

  // ---------- 14. Measures ----------
  {
    const s = base("Scored as a warning system: an alarm budget in alarms per year, not just an error", {
      say: "Accuracy is relative MAE against persistence on identical rows, so 1.000 is persistence. I report it rather than MASE alone because MASE divides by the training period's volatility, so it can fall for every model on a calmer block. The warning measures come from one contingency table: hit rate, false alarm rate, and alarms per year, the unit an operator actually budgets in. I never report plain accuracy, because with hazardous days a minority a model that never alarms scores high.",
      show: "the four cards; then the takeaway.",
      ask: "Diebold-Mariano with the Harvey-Leybourne-Newbold small-sample correction and absolute-error loss, run once per seed.",
      next: "Now the results.",
    });
    const defs = [
      ["Accuracy", "rMAE = MAE(model) / MAE(persistence)", "1.000 is persistence; below 1 beats it. Per horizon, never averaged."],
      ["Hit rate", "TP / (TP + FN)", "The share of actual hazardous days the model catches."],
      ["False alarm rate", "FP / (FP + TN)", "False alarms divided by quiet days, not by alarms raised."],
      ["Alarms per year", "365.25 (TP + FP) / n", "The unit an operator budgets in."],
    ];
    defs.forEach((d, i) => {
      const x = MX + (i % 2) * 6.15, y = 1.8 + Math.floor(i / 2) * 2.05;
      card(s, x, y, 5.95, 1.9);
      s.addText(d[0].toUpperCase(), { x: x + 0.25, y: y + 0.12, w: 5.4, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      s.addText(d[1], { x: x + 0.25, y: y + 0.45, w: 5.4, h: 0.6, fontFace: "Cambria Math", fontSize: 19, bold: true, color: C.navy, margin: 0 });
      s.addText(d[2], { x: x + 0.25, y: y + 1.1, w: 5.4, h: 0.7, fontFace: FONT, fontSize: 15.5, color: C.ink, valign: "top", margin: 0 });
    });
    takeaway(s, "Plain accuracy is never reported: with hazardous days a minority, a model that never alarms scores high by construction.");
  }

  // ---------- 15. RQ1 ----------
  {
    const s = base("RQ1: the networks win only at one day ahead, and ARIMA beats every ML regressor", {
      say: "Table 4.1 drawn. Left to right, one, two and three days; rMAE, lower is better, persistence at 1.0. The three networks are bars because each is a range over ten seeds. At one day they run 0.910 to 0.939 against ARIMA at 0.940, so they win. At three days the best network seed, 0.831, and ARIMA, 0.832, are separated by a few parts in ten thousand: a tie. And all five machine learning regressors sit behind ARIMA at every horizon, which fits the M4 competition result that flexible learners do not reliably beat classical benchmarks on a few thousand observations.",
      show: "ARIMA diamond against the coloured bars, panel by panel.",
      ask: "The full Table 4.1 is backup B1.",
      next: "What do the forecasts actually look like?",
    });
    s.addText("rMAE: error compared with simply repeating yesterday's value (the dashed line at 1.0). Further left is better.", { x: MX, y: 1.62, w: 12, h: 0.3, fontFace: FONT, fontSize: 14, italic: true, color: C.grey, margin: 0 });
    await figure(s, SLIDES, "rq1.png", (W - 12.1) / 2, 1.95, 12.1, 3.8, { bare: true });
    caption(s, "Report Table 4.1 drawn: bars are ten-seed ranges; the diamond is ARIMA; dots are single fits. Climatology (1.415 at h = 1) and seasonal naive (1.759) are off this axis; see B1.", MX, 5.8, 12, { h: 0.3 });
    takeaway(s, "Networks: 0.910 to 0.939 vs ARIMA 0.940 at one day. At three days 0.831 vs 0.832 is a tie. Every ML regressor trails ARIMA throughout.");
  }

  // ---------- 16. Winter ----------
  {
    const s = base("Both models follow each winter episode; the networks' edge shows on the sharpest rises", {
      say: "One representative winter, November 2024 to February 2025. Both models track the shape of each episode, not only its level, and the gap between them is visible mainly on the sharpest rises, exactly where a short-range nonlinear model would earn an edge. The GRU line is seed 0 alone, for illustration only; every quantitative claim uses all ten.",
      next: "But a single seed can mislead, as the next slide shows.",
    });
    const b = await figure(s, SLIDES, "winter.png", MX, 1.85, W - 2 * MX, 3.6);
    caption(s, "One representative winter, November 2024 to February 2025 (report Figure 4.2, redrawn). The GRU line is seed 0 alone, for illustration only.", MX, b.y + b.h + 0.18, 11.5);
    takeaway(s, "The edge is a short-range one: the forecast tracks the shape of each episode, with the gap on the sharpest rises.");
  }

  // ---------- 17. Seeds ----------
  {
    const s = base("A network's result is a range, not a number, and the spread rivals the gaps between models", {
      say: "This is why I report ranges. The GRU's ten-seed spread is 0.029, 0.028 and 0.048 at the three horizons; at three days that is wider than the gap separating ARIMA from two other models, so a single seed could be reported as beating them or losing to them at the analyst's convenience. Even tree models moved by 0.004 between two machines. And rerunning the same seed on the same machine moved the GRU almost as much as a new seed, so I doubled the sample from five to ten.",
      show: "the dashed floor of 0.004 against the bars.",
      ask: "Thread-order floating point in the OpenMP-parallel gradient boosting explains the 0.004; for networks, training accumulates small floating-point differences.",
      next: "Then are the one-day wins statistically real?",
    });
    await figure(s, SLIDES, "seed_spread.png", MX, 1.85, 7.0, 4.15);
    bullets(s, [
      ["Spread of ten seeds: ", "GRU 0.029, 0.028, 0.048 at h = 1, 2, 3; wider than some gaps in the table."],
      ["Noise floor 0.004: ", "tree models moved this much between two machines."],
      ["Same seed, same machine ", "still moved the GRU nearly as much as a new seed."],
      ["So five seeds became ten.", ""],
    ], 8.0, 1.95, 4.75, 4.0, { fontSize: 17 });
    takeaway(s, "A single seed could be reported as beating or losing to a rival at the analyst's convenience: only ranges are honest.");
  }

  // ---------- 18. Significance ----------
  {
    const s = base("Formal tests are more conservative than counting seeds, and the picture holds", {
      say: "A Diebold-Mariano test against ARIMA for each seed. At one day the statistic favours the network in all ten seeds for the GRU but is significant in only four; five for the LSTM, seven for the transformer. At two and three days no network reaches significance, bar one GRU seed at three days, in ARIMA's favour. For the five ML regressors, all fifteen comparisons favour ARIMA and fourteen reach p below 0.05. A limitation I want to state myself: twenty-seven tests with no correction; after Bonferroni only six survive and none of the plain GRU, LSTM or transformer, so read beyond one day as suggestive.",
      show: "the shaded one-day column; then 6 of 27.",
      ask: "Wilson 95% interval for 4 of 10 is 0.17 to 0.69; bootstrapping the statistic for heavy tails was not done.",
      next: "Now two arguments I made and then tested.",
    });
    table(s, [
      ["Seeds with p < 0.05 vs ARIMA", "h = 1", "h = 2", "h = 3"],
      ["GRU", "4 / 10", "0 / 10", "1 / 10"],
      ["GRU with weather", "7 / 10", "0 / 10", "1 / 10"],
      ["LSTM", "5 / 10", "0 / 10", "0 / 10"],
      ["Transformer", "7 / 10", "0 / 10", "0 / 10"],
    ], MX, 1.85, [3.2, 1.1, 1.1, 1.1], 0.58, { fontSize: 15.5, hl: [[1, 1], [2, 1], [3, 1], [4, 1]] });
    caption(s, "Report Table 4.2. The one significant 3-day GRU seed (p = 0.0056) favours ARIMA.", MX, 4.85, 6.5);
    card(s, MX, 5.2, 6.5, 0.85, { fill: C.pale, flat: true });
    s.addText("Four of ten significant is a small-sample proportion: 95% Wilson interval 0.17 to 0.69.", { x: MX + 0.2, y: 5.2, w: 6.1, h: 0.85, fontFace: FONT, fontSize: 14.5, color: C.navy, valign: "middle", margin: 0 });
    stat(s, 7.7, 1.85, 2.45, 1.7, "14 of 15", "regressor tests favour ARIMA at p < 0.05", C.blue);
    stat(s, 10.3, 1.85, 2.45, 1.7, "6 of 27", "tests survive a Bonferroni correction", C.verm);
    card(s, 7.7, 3.75, 5.05, 2.3);
    s.addText("Read beyond one day as suggestive", { x: 7.9, y: 3.85, w: 4.65, h: 0.4, fontFace: FONT, fontSize: 16.5, bold: true, color: C.navy, margin: 0 });
    s.addText("Twenty-seven tests, no joint correction: about 1.4 false positives expected by chance. After Bonferroni, none of the plain GRU, LSTM or transformer survives.", { x: 7.9, y: 4.3, w: 4.65, h: 1.7, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    takeaway(s, "One-day wins are real but modest; beyond one day nothing is confirmed, and the report says so.");
  }

  // ---------- 19. Two tested arguments ----------
  {
    const s = base("Two reasons for ruling models out did not survive being tested", {
      say: "In the literature review I argued for the GRU on two grounds: fewer parameters, and too little data for a transformer. I tested both under the identical protocol, on Dr Tian's feedback. The LSTM beats the GRU at every horizon, by 0.005, 0.008 and 0.013, despite a third more parameters. Dr Tian said the series, counting every evaluation block, is some four thousand days, which clears the bar for a transformer. The ten-seed run bears him out: the transformer beats the GRU in eight of ten matched seeds at every horizon and has the strongest formal significance at one day. One caveat: its four settings were inherited, not tuned.",
      next: "Next: does adding weather change the answer?",
    });
    const cols = [
      ["Argument 1: fewer parameters favour the GRU", "LSTM beats GRU at every horizon", "by 0.005, 0.008, 0.013 rMAE", "3,097 parameters against 2,329, a third more. The smaller network is not winning because it is smaller."],
      ["Argument 2: too little data for a transformer", "Transformer beats GRU in 8 of 10 seeds", "at every horizon, and matches the LSTM", "Dr Tian's count of about 4,000 days clears the threshold. At one day it has the strongest formal result: 7 of 10 seeds significant."],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 6.15;
      card(s, x, 1.85, 5.95, 3.55);
      s.addText(c[0].toUpperCase(), { x: x + 0.25, y: 1.98, w: 5.45, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.grey, charSpacing: 1.5, margin: 0 });
      s.addText(c[1], { x: x + 0.25, y: 2.4, w: 5.45, h: 0.6, fontFace: FONT, fontSize: 22, bold: true, color: C.verm, margin: 0 });
      s.addText(c[2], { x: x + 0.25, y: 3.0, w: 5.45, h: 0.45, fontFace: FONT, fontSize: 17, bold: true, color: C.navy, margin: 0 });
      s.addText(c[3], { x: x + 0.25, y: 3.65, w: 5.45, h: 2.2, fontFace: FONT, fontSize: 20, color: C.ink, valign: "top", margin: 0 });
    });
    card(s, MX, 5.55, W - 2 * MX, 0.5, { fill: C.white, flat: true });
    s.addText("Caveat stated in the report: the transformer's four settings were inherited from a single-split check, not tuned. This is one configuration's result.", { x: MX + 0.2, y: 5.55, w: W - 2 * MX - 0.4, h: 0.5, fontFace: FONT, fontSize: 13.5, italic: true, color: C.grey, valign: "middle", margin: 0 });
    takeaway(s, "A defensible prior is not evidence: both arguments were tested directly, and neither is supported.");
  }

  // ---------- 20. Weather ----------
  {
    const s = base("Weather helps at one day ahead and leaves two and three days a tie", {
      say: "I added observed wind speed and temperature; a calm, stagnant air mass is the physical candidate that the calendar-only Fourier terms cannot represent. At one day the weather network separates cleanly from the plain one; at two and three the ranges overlap. Gradient boosting improves everywhere, the random forest gets worse at three days, so weather is not a free improvement. Important: under the first five seeds two and three days both looked like wins. Doubling the seeds overturned that.",
      show: "blue bars (with weather) against orange (plain), relative to the ARIMA line.",
      ask: "The weather record ends 202 days before the PM2.5 series; I repeated the comparison inside the fully observed window and the picture held.",
      next: "Does that accuracy gain matter once it meets the alarm budget?",
    });
    const b = await figure(s, SLIDES, "weather.png", MX, 1.9, 7.3, 3.1);
    caption(s, "GRU ranges over ten seeds. Plain from Table 4.1, with weather from Table 4.4. Dashed: ARIMA.", MX, b.y + b.h + 0.2, 7.3);
    table(s, [
      ["Change in rMAE", "h = 1", "h = 2", "h = 3"],
      ["Gradient boosting, level", "−0.082", "−0.020", "−0.029"],
      ["Gradient boosting, change", "−0.073", "−0.047", "+0.006"],
      ["Ridge", "−0.031", "−0.005", "+0.023"],
      ["Random forest, level", "+0.002", "−0.006", "+0.053"],
      ["Random forest, change", "−0.003", "−0.001", "+0.022"],
    ], 8.4, 1.9, [2.2, 0.7, 0.7, 0.7], 0.5, { fontSize: 13.5 });
    caption(s, "Report Table 4.4: change from adding weather. Negative is an improvement.", 8.4, 5.0, 4.3, { h: 0.5 });
    takeaway(s, "GRU with weather beats ARIMA at one day in all ten seeds. At two days: 3 win, 6 tie, 1 loses. At three: 3 win, 2 tie, 5 lose.");
  }

  // ---------- 21. Weather through the threshold ----------
  {
    const s = base("Carried through the decision threshold, a more accurate forecaster buys about one point of hit rate", {
      say: "The test that matters. I reran the threshold sweep with the weather models as extra candidates. Where they win, the gain is at most 1.2 points of hit rate; elsewhere they are not even the best option. Compare that with the fifty points the budget buys. A forecast that is 8 points more accurate in rMAE buys at most a little over a point.",
      show: "the shaded cells: the largest gains.",
      next: "Now the second research question.",
    });
    table(s, [
      ["Best hit rate, alarms per year", "40", "60", "80", "100"],
      ["h = 1, no weather", "0.401", "0.609", "0.787", "0.899"],
      ["h = 1, weather models added", "0.402", "0.609", "0.792", "0.909"],
      ["h = 2, no weather", "0.388", "0.597", "0.771", "0.900"],
      ["h = 2, weather models added", "0.400", "0.597", "0.771", "0.900"],
      ["h = 3, no weather", "0.383", "0.567", "0.756", "0.876"],
      ["h = 3, weather models added", "0.383", "0.577", "0.756", "0.876"],
    ], MX, 1.85, [3.7, 1.1, 1.1, 1.1, 1.1], 0.55, { fontSize: 15, hl: [[4, 1], [2, 4], [6, 2]] });
    caption(s, "Report Table 4.5: best hit rate within an alarm budget, averaged over the ten network seeds, on identical origins.", MX, 5.75, 8.2);
    stat(s, 9.3, 1.85, 3.45, 1.9, "≤ 1.2 points", "the largest hit-rate gain from adding weather models", C.verm, 30);
    stat(s, 9.3, 3.95, 3.45, 1.9, "8.2 points", "rMAE gain for gradient boosting at h = 1, which became at most a little over 1 point of hit rate", C.blue, 30);
    takeaway(s, "The ceiling is not the models being too inaccurate: it persists after a materially more accurate forecaster is added.");
  }

  // ---------- 22. RQ2 ----------
  {
    const s = base("RQ2: forecast-then-threshold has a real but modest edge over direct classification", {
      say: "To compare fairly I matched each classifier to the regressor built on the same algorithm, so the training objective is the only thing that varies. Across three pairs, three horizons and four budgets, 36 comparisons: forecast-then-threshold wins 21, classification 11, four ties. The median gap is 0.011 of hit rate, the largest 0.056. The edge shrinks as the budget loosens: 8 of 9 at a budget of 40, but classification wins 6 of 9 at 100. I prefer forecast-then-threshold also because it yields a concentration that can be rethresholded for any future health policy without refitting.",
      show: "shaded cells: the better arm in each column.",
      ask: "All three horizons are backup B6.",
      next: "Now the central result, RQ3, starting with what a budget means.",
    });
    const rows = [
      ["h = 1, alarms per year", "40", "60", "80", "100"],
      ["Ridge: forecast then threshold", "0.377", "0.554", "0.723", "0.850"],
      ["Ridge: penalised logistic", "0.356", "0.550", "0.721", "0.856"],
      ["Random forest (change): forecast", "0.367", "0.550", "0.729", "0.867"],
      ["Random forest: classifier", "0.331", "0.550", "0.719", "0.856"],
      ["Grad. boosting (change): forecast", "0.379", "0.554", "0.727", "0.854"],
      ["Grad. boosting: classifier", "0.323", "0.546", "0.727", "0.865"],
    ];
    const hl = [];
    [[1, 2], [3, 4], [5, 6]].forEach(([f, c]) => {
      for (let col = 1; col <= 4; col++) {
        const a = parseFloat(rows[f][col]), b = parseFloat(rows[c][col]);
        if (a > b) hl.push([f, col]); else if (b > a) hl.push([c, col]);
      }
    });
    table(s, rows, MX, 1.85, [3.8, 0.95, 0.95, 0.95, 0.95], 0.55, { fontSize: 15, hl });
    caption(s, "Report Table 4.6: matched by base algorithm, h = 1. Shaded: the better arm; exact ties unshaded.", MX, 5.75, 7.6);
    [["21", "forecast-then-threshold wins", C.blue], ["11", "direct classification wins", C.grey], ["4", "exact ties", C.grey]].forEach((t, i) => {
      const y = 1.85 + i * 1.35;
      card(s, 9.2, y, 3.55, 1.2);
      s.addText(t[0], { x: 9.4, y, w: 1.2, h: 1.2, fontFace: FONT, fontSize: 42, bold: true, color: t[2], valign: "middle", margin: 0 });
      s.addText(t[1], { x: 10.6, y, w: 2.05, h: 1.2, fontFace: FONT, fontSize: 15.5, color: C.ink, valign: "middle", margin: 0 });
    });
    s.addText("of 36 matched comparisons", { x: 9.2, y: 5.8, w: 3.55, h: 0.3, fontFace: FONT, fontSize: 12, italic: true, color: C.grey, margin: 0 });
    takeaway(s, "Median gap 0.011 of hit rate. Forecast-then-threshold wins 8 of 9 at a 40-alarm budget, but loses 6 of 9 at 100.");
  }

  // ---------- RQ3a. What a budget means ----------
  {
    const s = base("What an alarm budget means: of every 100 hazardous days, how many are caught", {
      say: "Translate the dial into something you can feel. Each grid is 100 hazardous days; orange dots are the ones the best model caught at one day ahead. At 40 alarms a year, one alarm about every nine days, it catches 38 of 100. At 100 alarms, one about every four days, it catches 88. Nothing changed except the dial. This is a policy choice about how many alarms the public will tolerate, not a modelling choice.",
      show: "left to right, the orange fills up.",
      ask: "Hit rates are Table 4.7, best model at one day ahead (0.379, 0.567, 0.735, 0.881), rounded to whole days out of 100. Alarms every N days is 365.25 divided by the budget.",
      next: "Now let me show how this comes out of the model comparison, step by step.",
    });
    await figure(s, SLIDES, "waffle.png", MX, 1.75, W - 2 * MX, 3.7, { bare: true });
    caption(s, "Best model at each budget, one day ahead (Table 4.7), rounded to whole days out of 100.", MX, 5.6, 11);
    takeaway(s, "From one alarm every nine days to one every four, the same model catches 88 of 100 hazardous days instead of 38: a policy choice, not a modelling one.");
  }

  // ---------- RQ3b. Hero, step 1 ----------
  {
    const s = base("RQ3, step 1: one model, and its hit rate rises as you allow more alarms", {
      say: "Now the chart the project is built around. Horizontal: alarms raised per year, the dial. Vertical: the share of hazardous days caught. This is one model, ARIMA. As the budget rises, so does the hit rate. That is true by construction, so on its own it proves nothing about models. The question is what happens when I change the model.",
      show: "the two axes, then the single navy curve.",
      next: "Add three very different models.",
    });
    await figure(s, SLIDES, "hero_1.png", MX, 1.78, 7.5, 4.3, { bare: true });
    bullets(s, [
      ["Horizontal: ", "alarms raised per year, the dial."],
      ["Vertical: ", "the share of hazardous days caught."],
      ["More alarms catch more days, ", "by construction, so this alone says nothing about models."],
    ], 8.4, 2.0, 4.35, 3.8, { fontSize: 18, gap: 14 });
    takeaway(s, "Allow more alarms and the same model catches more hazardous days: that is the dial.");
  }

  // ---------- RQ3c. Hero, step 2 ----------
  {
    const s = base("RQ3, step 2: add three very different models, and the curves nearly coincide", {
      say: "Now add gradient boosting, persistence, which just repeats yesterday, and climatology, which uses only the calendar. Four very different forecasters, one almost identical curve. I have not separated them for legibility, because the overlap is the finding.",
      show: "how closely the four lines lie on top of one another.",
      next: "Now quantify the two effects.",
    });
    await figure(s, SLIDES, "hero_2.png", MX, 1.78, 7.5, 4.3, { bare: true });
    bullets(s, [
      ["ARIMA, gradient boosting, ", "persistence (just repeat yesterday) and climatology (the calendar alone)."],
      ["Four very different forecasters, ", "almost one curve."],
      ["Deliberately not separated: ", "the overlap is the finding."],
    ], 8.4, 2.0, 4.35, 3.8, { fontSize: 18, gap: 14 });
    takeaway(s, "Swap the detector, and the curve barely moves.");
  }

  // ---------- RQ3d. Hero, step 3 ----------
  {
    const s = base("RQ3: moving the alarm budget changes the hit rate by fifty points, and changing the model by five", {
      say: "Now the two effects. Along the dial, from 40 to 100 alarms a year, the best hit rate goes from 0.379 to 0.881: fifty points. At a fixed 100 alarms, switching the model moves it from about 0.82 to 0.88: about five. At three days and 40 alarms a year, persistence, which just repeats yesterday, is the best model in the whole study, 0.359. At 100 alarms a climatological forecast comes within a hundredth of the best, 0.816 against 0.827.",
      show: "the vermillion arrow on the left, then the blue bracket at 100 alarms.",
      ask: "A bigger budget raising the hit rate is true by construction, which is exactly why every model comparison is made at a fixed budget. The finding is the size of the two effects, not that the first exists. How big is the model effect exactly? The report says about five points; recomputed from the sweep it averages 7 across all ten models (2 to 12 by horizon and budget) and 4 without the lag-7 benchmark. Full Table 4.7 is backup B7.",
      next: "Why this happens: episodes. Then what I checked, and what I cannot claim.",
    });
    await figure(s, SLIDES, "hero_budget.png", MX, 1.75, 7.5, 3.85, { bare: true });
    caption(s, "The bracket spans the four models shown. Across all ten models the spread averages 7 points (4 without the lag-7 benchmark): see B8.", MX, 5.68, 7.6, { h: 0.45 });
    stat(s, 8.4, 1.85, 4.35, 1.3, "50 points", "the dial: budget 40 to 100 alarms a year (h = 1)", C.verm, 34);
    stat(s, 8.4, 3.3, 4.35, 1.3, "about 5 points", "the detector: model choice at a fixed budget", C.blue, 34);
    card(s, 8.4, 4.75, 4.35, 1.35, { fill: C.pale, flat: true });
    s.addText("At h = 3 and 40 alarms a year, persistence (0.359) is the best model in the whole study.", { x: 8.55, y: 4.75, w: 4.05, h: 1.35, fontFace: FONT, fontSize: 15.5, color: C.navy, valign: "middle", margin: 0 });
    takeaway(s, "The dial matters more than the detector: the alarm budget is the policy instrument, and the model only supplies its input.");
  }

  // ---------- 24. Robustness ----------
  {
    const s = base("The central finding survives every check, and the checks changed what I can claim", {
      say: "The 1000 cleaning ceiling is a judgement, so I restored the seven removed days and refitted everything. ARIMA barely moves, 0.935 against 0.940, because logs and differencing absorb the contamination. The ML models are not protected: ridge goes from a near tie with persistence to a clear loss, 0.997 to 1.118. So RQ1 strengthens. The bounded checks on the GRU show its three-day configuration is the one I can least defend: a 45-day window, four Fourier harmonics, and SGD each improve it by two to four points. I did not rerun the full evaluation with those, so Table 4.1 is unchanged.",
      show: "the first and last rows.",
      next: "And the limits.",
    });
    table(s, [
      ["Check", "What changed", "Result"],
      ["Restore the 7 capped days", "Refit full harness on the uncapped series", "ARIMA 0.935 vs 0.940 (h = 1). Ridge 0.997 → 1.118. GB level 0.883 → 1.006 (h = 3)."],
      ["Weather coverage gap", "Restrict to origins inside the observed window", "One-day ordering survives; two- and three-day picture unchanged."],
      ["Seed count 5 → 10", "Doubled for every network", "Weather win at h = 2 and 3 did not survive."],
      ["GRU window and size (bounded)", "6 settings, 3 seeds, one split", "Default near best at h = 1, 2; worst of six at h = 3 (45-day window 2.2 points better)."],
      ["GRU Fourier pairs (bounded)", "2 pairs → 4, as in ARIMA", "h = 3 improves 3.96 points, enough to put the mean below ARIMA on this split."],
      ["GRU optimiser (bounded)", "Adam, RMSprop, SGD; lr ×/÷ 3", "h = 3: SGD with momentum about 2 points better (0.839 vs 0.858)."],
    ], MX, 1.8, [2.75, 3.3, 6.08], 0.62, { fontSize: 13.5, leftCols: [1, 2] });
    takeaway(s, "Bounded checks are single-split, three-seed: nothing in the ten-seed Table 4.1 was changed on their strength.");
  }

  // ---------- 25. Limitations ----------
  {
    const s = base("What the results do not show", {
      say: "Limits, stated plainly. One monitor in one city, a diplomatic enclave. Observed weather, not forecast weather, so an operational system might do better. The LSTM and transformer were not given weather or the threshold sweep. Tree grids were small, so ML results are a lower bound. The significance tests are uncorrected with best-seed selection. And network training is not bit-reproducible even at a fixed seed. None of these overturns the central finding.",
      ask: "Why none overturns it: the finding rests on several independent sources agreeing, not on one p-value.",
      next: "So what does the project contribute?",
    });
    const items = [
      ["One site, one city", "8118 is a diplomatic-enclave monitor. Nothing here is a claim about Delhi as a whole or about other cities."],
      ["Observed weather, not forecast", "A real system would use numerical weather prediction. Boundary layer height is not available from meteostat."],
      ["Scope boundaries", "LSTM and transformer: no weather channels, no threshold sweep. The KAN-LSTM is a bounded check only."],
      ["Small search spaces", "Tree grids were small, so ML results are a lower bound. The GRU's 3-day configuration is the one its own checks least defend."],
      ["Significance testing", "27 tests, no joint correction, best-seed selection, no bootstrap of the loss differential's heavy tails."],
      ["Not bit-reproducible", "Network training moves at a fixed seed; ten seeds reduce the problem but do not remove it."],
    ];
    items.forEach((it, i) => {
      const x = MX + (i % 3) * 4.1, y = 1.8 + Math.floor(i / 3) * 2.2;
      card(s, x, y, 3.95, 2.05);
      s.addText(it[0], { x: x + 0.2, y: y + 0.1, w: 3.55, h: 0.5, fontFace: FONT, fontSize: 16.5, bold: true, color: C.navy, valign: "top", margin: 0 });
      s.addText(it[1], { x: x + 0.2, y: y + 0.65, w: 3.55, h: 1.35, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    });
    takeaway(s, "None of these overturns the central finding: it rests on several independent sources agreeing, not on any single p-value.");
  }

  // ---------- 26. Contributions ----------
  {
    const s = base("What this project contributes", {
      say: "Four things. A warning-system evaluation with an explicit alarm budget, which the Delhi studies I found do not do. A leakage-tested rolling-origin comparison from classical to deep models, with the networks reported as ten-seed ranges. Two defects in the source monitor diagnosed and corrected. And three priors tested instead of assumed: no weekly cycle, the GRU over the LSTM, and the small-data argument against a transformer.",
      next: "Back to the three questions.",
    });
    const items = [
      ["1", "A warning-system evaluation", "Hit rate, false alarm rate and alarms per year under an explicit budget: the operating point the Delhi studies do not report."],
      ["2", "A leakage-tested comparison", "Twelve specifications, classical to deep, under rolling-origin evaluation, with networks as ten-seed ranges."],
      ["3", "Two data defects, diagnosed and fixed", "A clipped ceiling and a coverage statistic that assumed the wrong cadence, both corrected before modelling."],
      ["4", "Priors tested, not assumed", "No weekly cycle; the GRU is not better because it is smaller; the small-data case against a transformer fails."],
    ];
    items.forEach((it, i) => {
      const x = MX + (i % 2) * 6.15, y = 1.85 + Math.floor(i / 2) * 2.1;
      card(s, x, y, 5.95, 1.95);
      s.addShape(pptx.ShapeType.ellipse, { x: x + 0.25, y: y + 0.3, w: 0.65, h: 0.65, fill: { color: C.blue }, line: { color: C.white, width: 0 } });
      s.addText(it[0], { x: x + 0.25, y: y + 0.3, w: 0.65, h: 0.65, fontFace: FONT, fontSize: 22, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      s.addText(it[1], { x: x + 1.1, y: y + 0.15, w: 4.6, h: 0.5, fontFace: FONT, fontSize: 18, bold: true, color: C.navy, valign: "middle", margin: 0 });
      s.addText(it[2], { x: x + 1.1, y: y + 0.7, w: 4.6, h: 1.15, fontFace: FONT, fontSize: 16, color: C.ink, valign: "top", margin: 0 });
    });
    takeaway(s, "Applying a standard model suite to Delhi is not new; evaluating it as a warning system with a varying alarm budget is.");
  }

  // ---------- 27. Conclusions ----------
  {
    const s = base("Three questions asked, three answered", {
      say: "RQ1: ARIMA beats every ML regressor at every horizon, with a Diebold-Mariano test at each comparison; the networks beat it only at one day ahead, as ranges across ten seeds. RQ2: neither arm dominates, 21, 11 and 4; I prefer forecast-then-threshold because a concentration can be rethresholded. RQ3: the budget moves hit rate by fifty points, the model by about five. Dr Tian's instruction to try several methods rather than default to ARIMA was right: it is what makes the negative result at two and three days credible, and what surfaces the one-day result.",
      next: "What follows from that.",
    });
    const rows = [
      ["RQ1", "Accuracy vs benchmarks", "ARIMA beats every ML regressor at every horizon (rMAE 0.940 at h = 1). The GRU beats ARIMA only at h = 1, across all ten seeds. The LSTM and transformer follow the same pattern.", C.blue],
      ["RQ2", "Forecast then threshold, or classify?", "Neither dominates: 21 / 11 / 4 across 36 matched comparisons. Forecast-then-threshold is preferred, since a concentration can be rethresholded for any future policy.", C.blue],
      ["RQ3", "Model choice vs decision threshold", "The budget sweep moves hit rate from 0.379 to 0.881 (h = 1, 40 to 100 alarms a year). Model choice moves it about 5 points at a fixed budget.", C.verm],
    ];
    rows.forEach((r, i) => {
      const y = 1.8 + i * 1.45;
      card(s, MX, y, W - 2 * MX, 1.3);
      s.addText(r[0], { x: MX + 0.25, y, w: 1.0, h: 1.3, fontFace: FONT, fontSize: 30, bold: true, color: r[3], valign: "middle", margin: 0 });
      s.addText(r[1], { x: MX + 1.4, y: y + 0.1, w: 3.0, h: 1.1, fontFace: FONT, fontSize: 16.5, bold: true, color: C.navy, valign: "middle", margin: 0 });
      s.addText(r[2], { x: MX + 4.55, y: y + 0.05, w: W - 2 * MX - 4.8, h: 1.2, fontFace: FONT, fontSize: 15.5, color: C.ink, valign: "middle", margin: 0 });
    });
    takeaway(s, "Machine learning earns a real but narrow place; the dial (the alarm budget), not the detector (the model), decides how many hazardous days are caught.", 6.2);
  }

  // ---------- 28. Recommendation ----------
  {
    const s = base("Design the warning system around its alarm budget, and treat the model as a refinement", {
      say: "The recommendation: design a hazardous air quality warning system around the alarm budget its operator can justify, with the forecasting model a secondary refinement. Six extensions follow from the report: a real numerical weather forecast; boundary layer height from a reanalysis such as ERA5; the GRU with four Fourier harmonics under the full ten-seed evaluation; a second, independent station; completing the LSTM and transformer with weather and the threshold sweep; and a full ten-seed evaluation of the Kolmogorov-Arnold-LSTM. Thank you; I am happy to take questions.",
      next: "Questions.",
    });
    card(s, MX, 1.85, 5.1, 4.8, { fill: C.navy, flat: true });
    s.addText("RECOMMENDATION", { x: MX + 0.3, y: 2.05, w: 4.5, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: "8FC3E8", charSpacing: 2, margin: 0 });
    s.addText("Design a hazardous air quality warning system around the alarm budget its operator can justify, with the forecasting model a secondary refinement.", { x: MX + 0.3, y: 2.45, w: 4.5, h: 2.6, fontFace: FONT, fontSize: 22, bold: true, color: C.white, valign: "top", margin: 0 });
    s.addText("A model comparison that does not fix the alarm budget it was evaluated at has answered a question nobody who operates the system asked.", { x: MX + 0.3, y: 5.15, w: 4.5, h: 1.3, fontFace: FONT, fontSize: 14, italic: true, color: "C9DCEC", valign: "top", margin: 0 });
    s.addText("SIX EXTENSIONS", { x: 6.1, y: 1.85, w: 6, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
    [
      ["Forecast weather. ", "Numerical weather prediction in place of observed conditions."],
      ["Boundary layer height. ", "From a reanalysis such as ERA5."],
      ["Four harmonics for the GRU ", "under the full ten-seed evaluation."],
      ["A second station, ", "ideally inside the CPCB network."],
      ["Complete the LSTM and transformer: ", "weather channels and the threshold sweep."],
      ["Promote the KAN-LSTM ", "from a bounded check to ten seeds."],
    ].forEach((e, i) => {
      const y = 2.25 + i * 0.73;
      s.addShape(pptx.ShapeType.ellipse, { x: 6.1, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: C.blue }, line: { color: C.white, width: 0 } });
      s.addText(String(i + 1), { x: 6.1, y: y + 0.05, w: 0.5, h: 0.5, fontFace: FONT, fontSize: 15, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      s.addText([{ text: e[0], options: { bold: true, color: C.navy } }, { text: e[1] }], { x: 6.8, y, w: 5.95, h: 0.6, fontFace: FONT, fontSize: 15.5, color: C.ink, valign: "middle", margin: 0 });
    });
  }

  // ---------- 29. Questions ----------
  {
    const s = pptx.addSlide();
    n += 1;
    s.background = { color: C.navy };
    s.addText("Thank you. Questions?", { x: MX, y: 2.2, w: 9, h: 1.0, fontFace: FONT, fontSize: 48, bold: true, color: C.white, margin: 0 });
    s.addText("The alarm budget a decision maker accepts dominates the choice of model.", { x: MX, y: 3.4, w: 10, h: 0.8, fontFace: FONT, fontSize: 22, color: "8FC3E8", margin: 0 });
    s.addText("Code, data and report: github.com/JC16092/mth5000-aqi-forecast", { x: MX, y: 5.0, w: 9.5, h: 0.4, fontFace: FONT, fontSize: 16, color: "C9DCEC", margin: 0 });
    s.addText("Backup: B1 full Table 4.1, B2 ARIMA order search, B3 significance tables, B4 GRU sensitivity, B5 stability and architecture checks, B6 RQ2 at all horizons, B7 full Table 4.7, B8 to B9 likely questions, B10 plain-language glossary.", { x: MX, y: 5.5, w: 11.5, h: 0.8, fontFace: FONT, fontSize: 14, color: "8FA6BD", valign: "top", margin: 0 });
    GUIDE.push({ n, title: "Thank you. Questions?", mins: 0, cue: { say: "Thank you. Happy to take questions. Detailed tables are in backup B1 to B7; the questions to expect are B8 and B9." } });
    s.addNotes(notesFor({ say: "Thank you. Happy to take questions. If asked something detailed, the backup slides B1 to B7 hold the full tables; B8 and B9 hold the questions I expect; B10 is the glossary." }));
  }

  // ====================================================================== backups
  {
    const s = base("B1. Report Table 4.1 in full: rMAE against persistence", { say: "Full accuracy table. Networks are ranges over ten seeds; everything else is a single fit. Bias is at h = 1 and its units are µg/m³." });
    table(s, [
      ["Model", "h = 1", "h = 2", "h = 3", "Bias, h = 1"],
      ["GRU, 10 seeds", "0.910 to 0.939", "0.878 to 0.906", "0.831 to 0.879", "−2.8"],
      ["LSTM, 10 seeds", "0.913 to 0.932", "0.874 to 0.892", "0.824 to 0.847", "−2.4"],
      ["Transformer, 10 seeds", "0.914 to 0.925", "0.870 to 0.893", "0.825 to 0.842", "−2.8"],
      ["ARIMA(1,1,1) + Fourier", "0.940", "0.883", "0.832", "−6.4"],
      ["Random forest, change", "0.968", "0.919", "0.897", "+2.1"],
      ["Gradient boosting, change", "0.983", "0.937", "0.878", "+2.0"],
      ["Random forest, level", "0.988", "0.934", "0.879", "+4.1"],
      ["Gradient boosting, level", "1.008", "0.945", "0.885", "+4.0"],
      ["Ridge regression", "0.997", "0.952", "0.897", "+2.6"],
      ["Persistence", "1.000", "1.000", "1.000", "−0.1"],
      ["Climatology", "1.415", "1.060", "0.947", "+9.4"],
      ["Seasonal naive, lag 7", "1.759", "1.325", "1.168", "+0.1"],
    ], MX + 0.6, 1.7, [3.4, 1.9, 1.9, 1.9, 1.4], 0.37, { fontSize: 14, boldRows: [4], hl: [[4, 1], [4, 2], [4, 3]] });
    caption(s, "Over 2,303 origins. Lower is better; 1.000 is persistence.", MX + 0.6, 6.6, 9, { h: 0.3 });
  }
  {
    const s = base("B2. The ARIMA order search in full: all 24 candidates by AIC", { say: "Table 3.4. Four orders did not converge to a stable estimate on the training block and are marked. (1,1,1) is chosen; the next best is 1.1 AIC points behind." });
    const r = [
      ["(1,1,1)", "1892.5", "1955.8", "chosen"], ["(1,1,2)", "1893.6", "1962.6", ""], ["(2,1,1)", "1894.4", "1963.4", ""], ["(3,1,1)", "1895.8", "1970.5", ""],
      ["(2,1,2)", "1895.8", "1970.6", "no convergence"], ["(3,1,2)", "1897.7", "1978.2", ""], ["(1,0,2)", "1910.4", "1985.2", "no convergence"], ["(2,0,1)", "1912.0", "1986.7", "no convergence"],
      ["(1,0,1)", "1912.1", "1981.1", ""], ["(2,0,0)", "1914.7", "1983.7", ""], ["(3,0,1)", "1915.5", "1996.0", "no convergence"], ["(3,0,2)", "1919.9", "2006.1", ""],
      ["(1,0,0)", "1927.4", "1990.7", ""], ["(0,0,2)", "2009.2", "2078.2", ""], ["(0,1,2)", "2022.5", "2085.7", ""], ["(2,0,2)", "2100.0", "2180.5", "no convergence"],
      ["(3,0,0)", "2126.5", "2201.2", "no convergence"], ["(3,1,0)", "2153.8", "2222.8", "no convergence"], ["(0,0,1)", "2167.9", "2231.1", ""], ["(0,1,1)", "2177.9", "2235.4", ""],
      ["(2,1,0)", "2196.7", "2259.9", "no convergence"], ["(1,1,0)", "2265.2", "2322.7", ""], ["(0,1,0)", "2355.6", "2407.4", ""], ["(0,0,0)", "2734.0", "2791.5", ""],
    ];
    const hdr = ["(p,d,q)", "AIC", "BIC", "note"];
    table(s, [hdr, ...r.slice(0, 12)], MX, 1.7, [1.2, 1.0, 1.0, 2.6], 0.37, { fontSize: 13, hl: [[1, 0], [1, 1], [1, 2], [1, 3]] });
    table(s, [hdr, ...r.slice(12)], 6.9, 1.7, [1.2, 1.0, 1.0, 2.6], 0.37, { fontSize: 13 });
    caption(s, "Report Table 3.4, sorted by AIC.", MX, 6.5, 6);
  }
  {
    const s = base("B3. Diebold-Mariano tests against ARIMA", { say: "Tables 4.2 and 4.3. Negative statistic favours the network; for the regressor table a positive statistic favours ARIMA. All 15 regressor pairings favour ARIMA and 14 reach p below 0.05." });
    table(s, [
      ["Network vs. ARIMA", "h", "DM statistic", "p-value", "Sig. seeds"],
      ["Plain GRU", "1", "−3.08 to −0.10", "0.002 to 0.923", "4/10"],
      ["Plain GRU", "2", "−0.47 to 1.73", "0.083 to 0.992", "0/10"],
      ["Plain GRU", "3", "−0.05 to 2.77", "0.006 to 0.987", "1/10"],
      ["GRU with weather", "1", "−3.92 to −0.87", "<0.001 to 0.383", "7/10"],
      ["GRU with weather", "2", "−1.78 to 0.26", "0.075 to 0.942", "0/10"],
      ["GRU with weather", "3", "−0.83 to 1.97", "0.049 to 0.907", "1/10"],
      ["LSTM", "1", "−2.59 to −0.66", "0.010 to 0.511", "5/10"],
      ["LSTM", "2", "−0.65 to 0.83", "0.409 to 0.974", "0/10"],
      ["LSTM", "3", "−0.59 to 1.05", "0.292 to 0.995", "0/10"],
      ["Transformer", "1", "−2.74 to −1.39", "0.006 to 0.164", "7/10"],
      ["Transformer", "2", "−1.34 to 0.84", "0.181 to 0.995", "0/10"],
      ["Transformer", "3", "−0.63 to 0.73", "0.463 to 0.988", "0/10"],
    ], MX, 1.7, [1.9, 0.4, 1.6, 1.7, 0.9], 0.38, { fontSize: 12 });
    table(s, [
      ["ARIMA vs. regressor", "h = 1", "h = 2", "h = 3"],
      ["Ridge", "4.25 (<0.001)", "3.85 (<0.001)", "3.62 (<0.001)"],
      ["RF, level", "3.05 (0.002)", "2.43 (0.015)", "2.19 (0.029)"],
      ["RF, change", "1.99 (0.046)", "1.93 (0.054)", "3.53 (<0.001)"],
      ["GB, level", "3.92 (<0.001)", "2.65 (0.008)", "2.26 (0.024)"],
      ["GB, change", "3.00 (0.003)", "2.51 (0.012)", "1.96 (0.050)"],
    ], 7.5, 1.7, [1.65, 1.2, 1.2, 1.2], 0.5, { fontSize: 12, hl: [[3, 2]] });
    caption(s, "Report Tables 4.2 and 4.3. Cells show DM statistic (p-value). Shaded: the one non-significant regressor pairing, p = 0.054.", 7.5, 4.85, 5.25);
  }
  {
    const s = base("B4. GRU sensitivity: three bounded checks, three seeds, one split", { say: "Table 5.1 and Figure 5.1. Mean rMAE across the same three seeds. At one and two days the default sits near the best; at three days it is the worst of six architecture settings. Single split, three seeds: nothing in Table 4.1 changed on this basis." });
    table(s, [
      ["Check", "Setting", "h = 1", "h = 2", "h = 3"],
      ["Architecture", "H = 24, 30-day (default)", "0.914", "0.886", "0.858"],
      ["", "H = 12", "0.927", "0.899", "0.856"],
      ["", "H = 48", "0.924", "0.889", "0.850"],
      ["", "15-day window", "0.922", "0.919", "0.839"],
      ["", "45-day window", "0.912", "0.907", "0.836"],
      ["", "60-day window", "0.912", "0.931", "0.851"],
      ["Seasonal input", "K = 4 (matches ARIMA)", "0.913", "0.881", "0.819"],
      ["Training", "Adam, lr = 0.003", "0.913", "0.888", "0.864"],
      ["", "Adam, lr = 0.03", "0.933", "0.912", "0.905"],
      ["", "SGD, lr = 0.01", "0.930", "0.889", "0.839"],
      ["", "RMSprop, lr = 0.01", "0.923", "0.914", "0.882"],
    ], MX, 1.7, [1.55, 2.5, 0.8, 0.8, 0.8], 0.4, { fontSize: 13 });
    const b = await figure(s, REPORT, "fig5_1_sensitivity.png", 7.7, 1.7, 4.8, 4.4);
    caption(s, "Report Figure 5.1. The vertical line marks the default.", 7.7, b.y + b.h + 0.2, 5.05);
  }
  {
    const s = base("B5. ARIMA coefficient stability, and all four architectures' bounded checks", { say: "Figure 3.6: phi drifts upward; theta oscillates near the invertibility boundary and crosses it at three of 28 refits, each with fewer than 1,700 training days. The optimiser is unconstrained, so a forecast is still produced there. Figure 5.2: all four architectures' bounded checks; the KAN hybrid sits among the other three." });
    const a = await figure(s, REPORT, "fig3_6_arima_stability.png", MX, 1.8, 6.0, 4.0);
    caption(s, "Report Figure 3.6. The three open points cross the invertibility boundary.", MX, a.y + a.h + 0.2, 6.0);
    const b = await figure(s, REPORT, "fig5_2_architectures.png", 6.95, 1.8, 5.6, 4.0);
    caption(s, "Report Figure 5.2. Bounded checks, ranges over three seeds, against ARIMA's rolling-origin rMAE.", 6.95, b.y + b.h + 0.2, 5.8);
  }
  {
    const s = base("B6. RQ2 at all three horizons: the hit-rate advantage of forecast-then-threshold", { say: "Figure 4.4 extends Table 4.6 to all horizons. Above zero, forecast-then-threshold wins. It wins 8 of 12 matched comparisons at one day, 7 of 12 at two, 6 of 12 at three: an edge that narrows rather than changing hands." });
    const b = await figure(s, REPORT, "fig4_4_arms.png", MX, 1.8, W - 2 * MX, 3.7);
    caption(s, "Report Figure 4.4. One line per matched pair.", MX, b.y + b.h + 0.2, 11);
    takeaway(s, "Forecast-then-threshold wins 8 of 12 matched comparisons at one day, 7 of 12 at two and 6 of 12 at three: an edge that narrows.", 6.2);
  }
  {
    const s = base("B7. Report Table 4.7 in full: best hit rate within an alarm budget", { say: "The principal table. Persistence and climatology at h = 3 are the two models the discussion names, so those claims can be checked against a printed cell." });
    table(s, [
      ["Best hit rate, alarms per year", "40", "60", "80", "100"],
      ["Best model, h = 1", "0.379", "0.567", "0.735", "0.881"],
      ["Best model, h = 2", "0.366", "0.538", "0.700", "0.840"],
      ["Best model, h = 3", "0.359", "0.533", "0.685", "0.827"],
      ["GRU, 10 seeds, h = 1", "0.356–0.377", "0.546–0.565", "0.719–0.735", "0.863–0.881"],
      ["ARIMA, h = 1", "0.358", "0.567", "0.727", "0.867"],
      ["Gradient boosting (change), h = 1", "0.379", "0.554", "0.727", "0.854"],
      ["Persistence, h = 1", "0.371", "0.558", "0.723", "0.873"],
      ["Climatology, h = 1", "0.352", "0.521", "0.660", "0.821"],
      ["Persistence, h = 3", "0.359", "0.507", "0.668", "0.791"],
      ["Climatology, h = 3", "0.336", "0.510", "0.649", "0.816"],
    ], MX + 0.6, 1.75, [4.3, 1.5, 1.5, 1.5, 1.5], 0.42, { fontSize: 14, hl: [[1, 1], [1, 4], [3, 1], [9, 1]], boldRows: [1] });
    caption(s, "Report Table 4.7. The event is fixed at the health threshold; only the decision threshold varies.", MX + 0.6, 6.5, 11);
  }
  {
    const s = base("B8. Likely questions, 1 of 2: scope and framing", {
      say: "Cue sheet for questions. Answers are short on purpose; the evidence is in the report section named.",
    });
    const qa = [
      ["Why 121 µg/m³?", "The CPCB National Air Quality Index boundary of the category below 'Severe', for the 24-hour mean: a policy threshold, not a round number. Section 3.1."],
      ["One station: is it representative?", "No claim that it is. It is the only nearby monitor with a full decade; CPCB stations serve data only from 19 Feb 2025. A second station is future work. Section 5.3."],
      ["Isn't a higher hit rate at a bigger budget trivial?", "Yes, by construction, which is why every model comparison is made at a fixed budget. The finding is the size of the two effects, and that persistence is best at h = 3 and 40 alarms. Section 5.1."],
      ["How big is the model effect, exactly?", "The report says about five points. Recomputed from the sweep file: the spread across all ten models averages 7 points (2 to 12 by horizon and budget), 4 without the lag-7 benchmark, 3 for the fitted models alone. Against 50 for the budget, the conclusion stands."],
      ["Is the left panel of slide 4 cherry-picked?", "It shows four representative models, as the report's Figure 4.5 does. The lag-7 seasonal-naive benchmark would be lower (0.758 at 100 alarms, h = 1, from the sweep file); it is a deliberately weak reference."],
      ["Why does ARIMA beat the ML models?", "Consistent with M4: a few thousand observations and no exogenous structure favour a classical model. ML is also more exposed to the uncleaned tail: ridge 0.997 → 1.118. Sections 2.1, 5.3."],
    ];
    qa.forEach((q, i) => {
      const y = 1.6 + i * 0.9;
      card(s, MX, y, W - 2 * MX, 0.82);
      s.addText(q[0], { x: MX + 0.2, y, w: 3.5, h: 0.82, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, valign: "middle", margin: 0 });
      s.addText(q[1], { x: MX + 3.85, y, w: W - 2 * MX - 4.05, h: 0.82, fontFace: FONT, fontSize: 13, color: C.ink, valign: "middle", margin: 0 });
    });
  }
  {
    const s = base("B9. Likely questions, 2 of 2: evidence and method", {
      say: "Cue sheet for questions, continued.",
    });
    const qa = [
      ["Why rMAE rather than RMSE or MASE?", "rMAE divides by persistence on identical rows. MASE divides by training volatility, so it can fall for every model on a calm block. DM uses absolute loss to match. Section 3.6."],
      ["Are the network wins real?", "Numerically ahead in all ten seeds at h = 1; DM p < 0.05 in 4, 5 and 7 of ten (GRU, LSTM, transformer). None beyond one day. After Bonferroni across 27 tests none of the three survive: read as suggestive. Section 3.7."],
      ["Why ten seeds? Why not tune?", "The same seed on the same machine moved the GRU almost as much as a new seed, and five to ten overturned the weather result. The GRU was set by inspection; bounded checks say the 3-day setting is the weakest. Section 5.3."],
      ["How do you know there is no leakage?", "The invariant is tested: corrupt the series from a date, rerun, and no earlier forecast may change. One model per horizon fixes the label arithmetic. Section 3.5."],
      ["ARIMA's θ sits near the boundary?", "0.013 inside. It crosses at 3 of 28 refits, each with fewer than 1,700 training days; the optimiser is unconstrained and those forecasts are scored as usual. Section 3.3.1."],
      ["Would real weather forecasts help?", "Untested: only observed weather is used. Weather moved hit rate by at most 1.2 points. Boundary layer height from ERA5 is the stronger candidate. Sections 4.1.1, 6.2."],
    ];
    qa.forEach((q, i) => {
      const y = 1.6 + i * 0.9;
      card(s, MX, y, W - 2 * MX, 0.82);
      s.addText(q[0], { x: MX + 0.2, y, w: 3.5, h: 0.82, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, valign: "middle", margin: 0 });
      s.addText(q[1], { x: MX + 3.85, y, w: W - 2 * MX - 4.05, h: 0.82, fontFace: FONT, fontSize: 13, color: C.ink, valign: "middle", margin: 0 });
    });
  }
  {
    const s = base("B10. The words used in this talk, in plain language", { say: "Glossary. Useful if an audience member is outside statistics: every term the talk uses, in one line each." });
    table(s, [
      ["Term", "In plain words"],
      ["PM2.5", "Fine particles under 2.5 micrometres across, small enough to reach deep into the lungs."],
      ["Hazard threshold, 121 µg/m³", "A day above this is 'hazardous': the boundary of the 'Very Poor' category of India's air quality index."],
      ["Persistence", "The simplest forecast: tomorrow equals today."],
      ["ARIMA", "A classical time-series model: predicts from recent values and recent errors, with the season added."],
      ["Machine learning regressor", "A flexible model that learns from examples: ridge regression, random forest, gradient boosting."],
      ["Neural network (GRU, LSTM, transformer)", "A model that learns patterns from a window of the last 30 days."],
      ["rMAE", "Average error compared with persistence on the same days: 1.0 is persistence, below 1 is better."],
      ["Hit rate", "The share of hazardous days that were caught."],
      ["False alarm rate", "The share of quiet days that were wrongly flagged."],
      ["Alarm budget", "How many alarms are raised per year: the dial in the talk."],
      ["Seed", "The random starting point of a network's training; the talk reports ten, as a range."],
      ["Rolling origin", "Testing as if each forecast were made on its own day, using only the past."],
    ], MX, 1.65, [3.6, 8.5], 0.37, { fontSize: 13, leftCols: [1] });
  }

  writeGuide();
  await pptx.writeFile({ fileName: OUT });
  console.log("wrote", OUT, "slides:", n, "| talk minutes:", MINS.reduce((a, b) => a + b, 0));
}

build().catch((e) => { console.error(e); process.exit(1); });
