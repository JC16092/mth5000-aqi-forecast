// Oral presentation deck for MTH5000, built from report/main.pdf.
// Every number below is read from the compiled report (table or sentence cited in the notes);
// nothing is recomputed here. Figures are extracted from the report PDF, not redrawn.
const path = require("path");
const pptxgen = require("pptxgenjs");
const sharp = require("sharp");

const ASSETS = path.join(__dirname, "..", "assets");
const OUT = path.join(__dirname, "..", "MTH5000_oral_presentation.pptx");

// ---------- palette (Monash blue + the Okabe-Ito accents the report's figures use) ----------
const C = {
  navy: "0B2545",
  blue: "006CAB",
  pale: "DCEAF5",
  bg: "F4F7FA",
  ink: "1B2733",
  grey: "5B6B7A",
  line: "D3DCE6",
  verm: "D55E00", // the report's one "called-out" colour
  orange: "E69F00",
  green: "009E73",
  white: "FFFFFF",
};
const FONT = "Calibri";
const W = 13.333,
  H = 7.5,
  MX = 0.6;

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.title = "Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities";
pptx.author = "Jaykumar Vinodbhai Chauhan";

let n = 0;
// Minutes budgeted per slide, in order. Main talk is the first 28 entries; backups carry 0.
const MINS = [0.75, 1.5, 1.25, 1.25, 1.5, 1, 1.5, 1.5, 0.75, 1.5, 1.5, 1.25, 1.25, 1.5, 0.75, 1.25, 1.25, 1.25, 1.5, 1, 1.25, 1.75, 1, 1.25, 1.25, 1.25, 1.25, 0, 0, 0, 0, 0, 0];
const cumMins = (k) => MINS.slice(0, k).reduce((a, b) => a + b, 0);
function timedNotes(notes) {
  const body = (notes || "").replace(/^\[[^\]]*\]\s*/, "");
  const m = MINS[n - 1] || 0;
  const head = m ? `[Slide ${n} | about ${m} min | running total ${cumMins(n)} min] ` : `[Slide ${n} | backup, not timed] `;
  return head + body;
}
const SECTIONS = {
  intro: "Motivation",
  data: "Data",
  methods: "Methods",
  results: "Results",
  discuss: "Discussion",
  concl: "Conclusion",
  backup: "Backup",
};

// ---------- helpers ----------
function base(section, title, notes) {
  const s = pptx.addSlide();
  n += 1;
  s.background = { color: C.bg };
  if (section) {
    s.addText(SECTIONS[section].toUpperCase(), {
      x: MX, y: 0.3, w: 6, h: 0.3, fontFace: FONT, fontSize: 11, bold: true,
      color: C.blue, charSpacing: 3, margin: 0,
    });
  }
  s.addText(title, {
    x: MX, y: 0.58, w: W - 2 * MX, h: 0.95, fontFace: FONT, fontSize: 27,
    bold: true, color: C.navy, valign: "top", margin: 0,
  });
  s.addText("MTH5000  |  J. V. Chauhan  |  Supervisor: Dr T. Tian", {
    x: MX, y: H - 0.42, w: 7, h: 0.28, fontFace: FONT, fontSize: 10, color: C.grey, margin: 0,
  });
  s.addText(String(n), {
    x: W - MX - 1, y: H - 0.42, w: 1, h: 0.28, fontFace: FONT, fontSize: 10,
    color: C.grey, align: "right", margin: 0,
  });
  if (notes) s.addNotes(timedNotes(notes));
  return s;
}

function card(s, x, y, w, h, opts = {}) {
  s.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || C.line, width: 0.75 },
    shadow: opts.noShadow ? undefined : { type: "outer", color: "000000", opacity: 0.08, blur: 6, offset: 2, angle: 90 },
  });
}

async function fitImage(s, file, x, y, maxW, maxH, opts = {}) {
  const meta = await sharp(path.join(ASSETS, file)).metadata();
  const r = Math.min(maxW / meta.width, maxH / meta.height);
  const w = meta.width * r,
    h = meta.height * r;
  const px = x + (maxW - w) / 2,
    py = y + (maxH - h) / 2;
  const pad = opts.pad === undefined ? 0.12 : opts.pad;
  if (!opts.bare) card(s, px - pad, py - pad, w + 2 * pad, h + 2 * pad);
  s.addImage({ path: path.join(ASSETS, file), x: px, y: py, w, h });
  return { x: px, y: py, w, h, pad };
}

function caption(s, text, x, y, w) {
  s.addText(text, {
    x, y, w, h: 0.5, fontFace: FONT, fontSize: 11.5, italic: true, color: C.grey,
    valign: "top", margin: 0,
  });
}

function bullets(s, items, x, y, w, h, opts = {}) {
  const fs = opts.fontSize || 17;
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    if (typeof it === "string") {
      runs.push({ text: it, options: { bullet: { indent: 18 }, breakLine: !last, paraSpaceAfter: 7 } });
    } else {
      // [bold lead, rest]
      runs.push({ text: it[0], options: { bullet: { indent: 18 }, bold: true, color: C.navy } });
      runs.push({ text: it[1], options: { breakLine: !last, paraSpaceAfter: 7 } });
    }
  });
  s.addText(runs, {
    x, y, w, h, fontFace: FONT, fontSize: fs, color: C.ink, valign: "top",
    margin: 0, lineSpacingMultiple: 1.05,
  });
}

function stat(s, x, y, w, h, big, label, color, bigSize) {
  card(s, x, y, w, h);
  s.addText(big, {
    x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h * 0.52, fontFace: FONT,
    fontSize: bigSize || opts_bigsize(w), bold: true, color: color || C.blue, valign: "middle", margin: 0,
  });
  s.addText(label, {
    x: x + 0.15, y: y + h * 0.58, w: w - 0.3, h: h * 0.38, fontFace: FONT,
    fontSize: 13, color: C.grey, valign: "top", margin: 0,
  });
}
function opts_bigsize(w) {
  return w > 3.4 ? 38 : 32;
}

// table: rows = array of arrays of strings; opts.hl = {r,c} cells to highlight; opts.boldRows
function table(s, rows, x, y, colW, rowH, opts = {}) {
  const fs = opts.fontSize || 13;
  const hl = new Set((opts.hl || []).map(([r, c]) => `${r},${c}`));
  const bold = new Set(opts.boldRows || []);
  const body = rows.map((row, r) =>
    row.map((cell, c) => {
      const header = r === 0;
      const o = {
        fontFace: FONT, fontSize: fs, color: header ? C.white : C.ink, bold: header || bold.has(r),
        fill: { color: header ? C.navy : hl.has(`${r},${c}`) ? C.pale : r % 2 ? C.white : "F9FBFD" },
        align: c === 0 || (opts.leftCols || []).includes(c) ? "left" : "center", valign: "middle",
        border: [
          { type: "none" }, { type: "none" },
          { type: "solid", pt: 0.5, color: C.line }, { type: "none" },
        ],
        margin: [0.02, 0.08, 0.02, 0.08],
      };
      if (hl.has(`${r},${c}`)) { o.bold = true; o.color = C.navy; }
      return { text: cell, options: o };
    })
  );
  s.addTable(body, { x, y, w: colW.reduce((a, b) => a + b, 0), colW, rowH });
}

function eq(s, text, x, y, w, h, fs) {
  card(s, x, y, w, h, { fill: C.white, noShadow: true });
  s.addText(text, {
    x: x + 0.1, y, w: w - 0.2, h, fontFace: "Cambria Math", fontSize: fs || 16,
    color: C.navy, align: "center", valign: "middle", margin: 0,
  });
}

// ====================================================================================
async function build() {
  // ---------- 1. Title ----------
  {
    const s = pptx.addSlide();
    n += 1;
    s.background = { color: C.navy };
    s.addShape(pptx.ShapeType.rect, { x: 8.4, y: 0, w: W - 8.4, h: H, fill: { color: C.white }, line: { color: C.white } });
    s.addImage({ path: path.join(ASSETS, "monash-logo.png"), x: 8.9, y: 0.55, w: 3.5, h: 3.5 * 430 / 1470 });
    s.addText("MTH5000 MASTERS RESEARCH PROJECT  |  ORAL PRESENTATION", {
      x: MX, y: 0.7, w: 7.4, h: 0.35, fontFace: FONT, fontSize: 12, bold: true, color: "8FC3E8", charSpacing: 2, margin: 0,
    });
    s.addText("Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities", {
      x: MX, y: 1.5, w: 7.4, h: 2.7, fontFace: FONT, fontSize: 38, bold: true, color: C.white, valign: "top", margin: 0,
    });
    s.addText(
      [
        { text: "Jaykumar Vinodbhai Chauhan", options: { bold: true, breakLine: true } },
        { text: "Student ID 34710280  |  Master of Mathematics", options: { breakLine: true } },
        { text: "Supervisor: Dr Tianhai Tian", options: { breakLine: true } },
        { text: "School of Mathematics, Monash University  |  November 2026" },
      ],
      { x: MX, y: 4.7, w: 7.4, h: 1.6, fontFace: FONT, fontSize: 16, color: "C9DCEC", valign: "top", margin: 0, paraSpaceAfter: 4 }
    );
    // headline numbers on the white panel
    s.addText("THE FINDING IN TWO NUMBERS", {
      x: 8.9, y: 2.6, w: 3.9, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0,
    });
    s.addText("0.379 to 0.881", {
      x: 8.9, y: 2.95, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 36, bold: true, color: C.verm, margin: 0,
    });
    s.addText("hit rate at one day ahead as the alarm budget moves from 40 to 100 alarms a year", {
      x: 8.9, y: 3.7, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 14, color: C.grey, valign: "top", margin: 0,
    });
    s.addText("about 5 points", {
      x: 8.9, y: 4.75, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 36, bold: true, color: C.blue, margin: 0,
    });
    s.addText("the most that changing the model moves it, at a fixed budget", {
      x: 8.9, y: 5.5, w: 3.9, h: 0.75, fontFace: FONT, fontSize: 14, color: C.grey, valign: "top", margin: 0,
    });
    s.addNotes(timedNotes(
      "Talking points, not a script: trim to the time budget on each slide. Good morning. My project asks how well machine learning can forecast hazardous air quality days in Delhi, and the answer I want to build to is on the right: the number of alarms a health authority is willing to raise matters about ten times more than which model produces the forecast. I will take you through the data, the models, the three research questions, and what I would and would not claim."
    ));
  }

  // ---------- 2. Why it matters ----------
  {
    const s = base(
      "intro",
      "A forecast is only useful if it arrives before the hazardous day does",
      "[0:45 to 3:00] Sustained PM2.5 exposure is linked to cardiopulmonary and all-cause mortality (Pope and Dockery 2006; Chen and Hoek 2020), which is why the event I forecast is a health threshold and not an arbitrary round number: 121 micrograms per cubic metre, the boundary of the CPCB National Air Quality Index 'Very Poor' category, 24-hour mean. At the Delhi monitor I use, 29.7 percent of days exceed it. The gap in the literature: Masood and Ahmad (2020) and Singh and Srivastava (2025) report R squared, RMSE and MAE. Neither evaluates forecasts as a warning system with an explicit alarm budget. That is the space this project occupies. Personal note: I grew up in India, so this is not an abstract statistic for me."
    );
    bullets(
      s,
      [
        ["Health basis. ", "PM2.5 exposure is linked to cardiopulmonary and all-cause mortality (Pope and Dockery 2006; Chen and Hoek 2020)."],
        ["The event. ", "A day above 121 µg/m³, the boundary of the CPCB National Air Quality Index 'Very Poor' category (24-hour mean)."],
        ["The gap. ", "Two prior Delhi machine learning studies (Masood and Ahmad 2020; Singh and Srivastava 2025) report R², RMSE and MAE. Neither evaluates forecasts as a warning system with an explicit alarm budget."],
        ["The risk. ", "A model with good average error can still miss the extreme days that are the only ones anyone cares about."],
      ],
      MX, 1.8, 7.1, 4.9, { fontSize: 20 }
    );
    stat(s, 8.2, 1.8, 2.2, 1.6, "29.7%", "of days exceed 121 µg/m³ (920 of 3,093)", C.verm);
    stat(s, 10.6, 1.8, 2.15, 1.6, "1 to 3", "days ahead: the forecast horizons");
    stat(s, 8.2, 3.65, 2.2, 1.6, "9.8 yrs", "of daily data, Nov 2016 to Aug 2026");
    stat(s, 10.6, 3.65, 2.15, 1.6, "12", "model specifications compared");
    card(s, 8.2, 5.5, 4.55, 1.05, { fill: C.pale, noShadow: true });
    s.addText("Exceedances are a minority class, so plain accuracy is never reported: a model that never alarms scores high by construction.", {
      x: 8.35, y: 5.5, w: 4.25, h: 1.05, fontFace: FONT, fontSize: 13, color: C.navy, valign: "middle", margin: 0,
    });
  }

  // ---------- 3. Research questions ----------
  {
    const s = base(
      "intro",
      "Three research questions, and the third turned out to dominate the other two",
      "[3:00 to 4:30] Three questions. One: how accurately can concentrations be forecast one to three days ahead by machine learning, against classical and naive benchmarks. Two: is it better to forecast the concentration and then threshold it, or to classify the exceedance directly. Three: considered as a warning system, what hit rate and false alarm rate does each approach achieve, and how does the decision threshold trade them off. The answers, from the report's Table 6.1, are on the cards. I will come back to each with the evidence."
    );
    const rq = [
      ["RQ1", "Accuracy", "How accurately can daily concentrations be forecast 1 to 3 days ahead by machine learning, relative to classical and naive benchmarks?", "ARIMA beats every ML regressor at every horizon (rMAE 0.940 at h = 1). The deep networks beat it only at h = 1."],
      ["RQ2", "Two arms", "Is it better to forecast the concentration and then threshold it, or to classify the exceedance event directly?", "Neither dominates: 21 / 11 / 4 across 36 matched comparisons. Forecast-then-threshold preferred on flexibility."],
      ["RQ3", "Warning system", "As a warning system, what hit rate and false alarm rate does each approach achieve, and how does the decision threshold trade them off?", "Budget sweep moves hit rate 0.379 to 0.881 (h = 1). Model choice moves it about 5 points."],
    ];
    const cw = 3.85, gap = 0.2;
    rq.forEach((r, i) => {
      const x = MX + i * (cw + gap);
      card(s, x, 1.8, cw, 4.85);
      s.addText(r[0], { x: x + 0.25, y: 1.95, w: 1.2, h: 0.5, fontFace: FONT, fontSize: 26, bold: true, color: i === 2 ? C.verm : C.blue, margin: 0 });
      s.addText(r[1].toUpperCase(), { x: x + 1.3, y: 2.0, w: cw - 1.5, h: 0.4, fontFace: FONT, fontSize: 11, bold: true, color: C.grey, charSpacing: 2, valign: "middle", margin: 0 });
      s.addText(r[2], { x: x + 0.25, y: 2.6, w: cw - 0.5, h: 1.45, fontFace: FONT, fontSize: 16.5, color: C.ink, valign: "top", margin: 0 });
      s.addShape(pptx.ShapeType.rect, { x: x + 0.25, y: 4.15, w: cw - 0.5, h: 0.02, fill: { color: C.line }, line: { color: C.line, width: 0 } });
      s.addText("HEADLINE ANSWER", { x: x + 0.25, y: 4.28, w: cw - 0.5, h: 0.3, fontFace: FONT, fontSize: 10.5, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      s.addText(r[3], { x: x + 0.25, y: 4.6, w: cw - 0.5, h: 1.9, fontFace: FONT, fontSize: 17, bold: true, color: C.navy, valign: "top", margin: 0 });
    });
  }

  // ---------- 4. Data and station ----------
  {
    const s = base(
      "data",
      "One well-characterised Delhi monitor, nearly ten years of daily PM2.5",
      "[4:30 to 6:00] Data come from OpenAQ. I compared five candidate stations within 25 km of central Delhi on coverage rather than nominal length of record, and found something unexpected: every CPCB station returns measurements only from 19 February 2025, about eighteen months, even though the metadata advertises 2016. Four independent stations sharing an identical cutoff is a systematic limit of the measurements endpoint. Only location 8118 returns the full record, so I used it. The cost, which I want to state plainly: 8118 is supplied through AirNow and is almost certainly a US diplomatic post monitor. So everything here describes one well-characterised point in Delhi, not the whole city."
    );
    table(
      s,
      [
        ["Analysis dataset after cleaning", ""],
        ["Source", "OpenAQ location 8118, sensor 23534, AirNow"],
        ["Period", "2016-11-09 to 2026-08-27"],
        ["Calendar days", "3,579"],
        ["Usable daily means", "3,093 (86.4% of calendar)"],
        ["Longest gap", "34 consecutive days"],
        ["Mean, median, maximum", "102.7, 71.7, 896.0 µg/m³"],
        ["Days above 121", "920 (29.7%)"],
      ],
      MX, 1.8, [2.7, 3.75], 0.5, { fontSize: 14 }
    );
    caption(s, "Report Table 3.1.", MX, 5.9, 6);
    card(s, 7.7, 1.8, 5.05, 4.0, { fill: C.white });
    s.addText("Why station 8118, and what it costs", { x: 7.95, y: 1.95, w: 4.6, h: 0.4, fontFace: FONT, fontSize: 17, bold: true, color: C.navy, margin: 0 });
    bullets(
      s,
      [
        "Five stations within 25 km compared on coverage, not nominal record length.",
        "Every CPCB station serves data only from 19 Feb 2025 (about 18 months), despite metadata saying 2016.",
        "Only 8118 returns the full record.",
        [ "Cost: ", "8118 is an AirNow feed, almost certainly a US diplomatic post monitor. Results describe one site, not Delhi as a whole." ],
      ],
      7.95, 2.45, 4.6, 3.3, { fontSize: 16 }
    );
  }

  // ---------- 5. Two defects ----------
  {
    const s = base(
      "data",
      "Two defects in the source data were found and corrected before any model was fitted",
      "[6:00 to 8:00] Two problems. First, physically impossible values: five negative concentrations, and a maximum of 1990 that appears three times identically on unrelated dates. That is a clipped instrument ceiling, not a measurement; one occurrence fell on 2 September, in the monsoon, between neighbours of 42 and 178. Second, and more damaging, a coverage statistic. OpenAQ divides observation count by an expected 24, assuming hourly reporting, but this sensor reported half-hourly from 2016 to 2024. So a day holding 24 of a genuine 48 readings is scored as fully complete, and half a day of a polluted afternoon enters the series as a daily mean. Days at 50 to 75 percent true coverage produced implausible values about seven times as often as days above 90 percent. Panel (a) shows the cadence change; panel (b) the rate of implausible values by true coverage. Correction: take the cadence from the data, 90th percentile of counts within each year. 1,085 of 3,467 days fall below 75 percent true coverage, far more than the 268 with no recorded value."
    );
    const b = await fitImage(s, "fig3_1_coverage.png", MX, 1.8, 7.4, 3.5);
    caption(s, "Figure 3.1. (a) readings per daily mean; the fixed denominator of 24 (dashed) against the cadence estimated from the data (solid). (b) implausible values by true coverage.", MX, b.y + b.h + 0.2, 7.4);
    card(s, 8.35, 1.65, 4.4, 2.1);
    s.addText("1. A clipped ceiling", { x: 8.55, y: 1.75, w: 4.0, h: 0.35, fontFace: FONT, fontSize: 16, bold: true, color: C.verm, margin: 0 });
    s.addText("1990 appears three times identically, one of them on 2 September, in the monsoon, between neighbours of 42 and 178. Five negative values as well.", { x: 8.55, y: 2.15, w: 4.0, h: 1.5, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    card(s, 8.35, 3.9, 4.4, 2.4);
    s.addText("2. A wrong coverage denominator", { x: 8.55, y: 4.0, w: 4.0, h: 0.35, fontFace: FONT, fontSize: 16, bold: true, color: C.verm, margin: 0 });
    s.addText("Completeness assumed 24 readings a day, but the sensor was half-hourly until 2024. A half-day of data counted as complete. Implausible values were about 7 times as frequent at 50 to 75% true coverage as above 90%.", { x: 8.55, y: 4.4, w: 4.0, h: 1.8, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    s.addText("Rules applied (Table 3.3): value below 0 removes 5 days; coverage below 50% removes 270; value above 1000 removes 7. Total 282 of 3,375. The exceedance rate moves only from 30.0 to 27.0% across every candidate coverage threshold, so the filter is not removing the events of interest.", {
      x: MX, y: 5.95, w: 7.4, h: 0.9, fontFace: FONT, fontSize: 13, color: C.ink, valign: "top", margin: 0,
    });
  }

  // ---------- 6. Series ----------
  {
    const s = base(
      "data",
      "Exceedances arrive as multi-day winter episodes, and that is the structure worth forecasting",
      "[8:00 to 9:30] The cleaned series. The shaded days exceed the threshold. They arrive as winter episodes, not isolated days. This matters twice: persistence turns out to be a strong forecast for exactly this reason, and it motivates evaluating as a warning system. The distribution is strongly right skewed, skewness 2.17, excess kurtosis 8.31, so every model is fitted to the logarithm of concentration. That also stops a model predicting a negative concentration. Annual Fourier terms alone explain 69 percent of the variance of the logarithm."
    );
    const b = await fitImage(s, "fig3_2_series.png", MX, 1.8, W - 2 * MX, 3.1);
    caption(s, "Figure 3.2. The cleaned daily series, with days exceeding the threshold shaded. Maximum 896.0 on 2017-11-08.", MX, b.y + b.h + 0.2, 9);
    const sx = 5.3, sw = 1.78, sg = 0.15, sy = 5.55;
    [
      ["102.7", "mean µg/m³"],
      ["71.7", "median"],
      ["2.17", "skewness"],
      ["8.31", "excess kurtosis"],
    ].forEach((t, i) => {
      const x = MX + i * (2.05 + 0.1);
      card(s, x, 5.45, 2.05, 1.35);
      s.addText(t[0], { x: x + 0.1, y: 5.5, w: 1.85, h: 0.7, fontFace: FONT, fontSize: 30, bold: true, color: C.blue, valign: "middle", margin: 0 });
      s.addText(t[1], { x: x + 0.1, y: 6.2, w: 1.85, h: 0.45, fontFace: FONT, fontSize: 12.5, color: C.grey, valign: "top", margin: 0 });
    });
    card(s, 9.1, 5.45, 3.65, 1.35, { fill: C.pale, noShadow: true });
    s.addText("Fitted in logarithms: right skew, and annual Fourier terms explain 69% of the log variance.", { x: 9.25, y: 5.45, w: 3.35, h: 1.35, fontFace: FONT, fontSize: 13.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 7. No weekly cycle ----------
  {
    const s = base(
      "data",
      "An assumption from the approved proposal fails: there is no weekly cycle at this station",
      "[9:30 to 11:30] The proposal assumed a weekly cycle alongside the annual one, and treated reconciling two seasonal periods as the central modelling difficulty. I tested it three ways, each asking a different question. Periodogram: dominant periods 357.9, 178.9, 188.4, 397.7, 325.4 and 60.7 days, the annual cycle and harmonics, nothing near seven. Autocorrelation of the deseasonalised log series: lag 7 is 0.173, but lag 6 is 0.179 and lag 8 is 0.153, so lag 7 sits on the decay curve, not above it. Day of week: spread of 6.5 percent, ANOVA F = 1.13, p = 0.34, Kruskal-Wallis p = 0.77. Three tests on different assumptions agreeing is what makes the absence convincing. Physical reading: a weekly rhythm is a traffic signature, and 8118 is in the diplomatic enclave, not at a roadside site. Consequence: ARIMA with annual Fourier terms and no weekly seasonal order."
    );
    const a = await fitImage(s, "fig3_3_periodogram.png", MX, 1.8, 5.9, 2.6);
    caption(s, "Figure 3.3. Periodogram: the six dominant periods are marked open. Seven days (dotted) sits on the noise floor.", MX, a.y + a.h + 0.2, 5.9);
    const b = await fitImage(s, "fig3_4_weekly.png", 6.9, 1.8, 5.85, 2.6);
    caption(s, "Figure 3.4. Lags 7, 14, 21 lie on the decay curve; every day-of-week interval contains zero.", 6.9, b.y + b.h + 0.2, 5.85);
    const t = [
      ["Periodogram", "Dominant periods 357.9, 178.9, 188.4, 397.7, 325.4, 60.7 days. Nothing near 7."],
      ["Autocorrelation", "Lag 7 = 0.173, lag 6 = 0.179, lag 8 = 0.153: on the decay curve, not above it."],
      ["Day of week", "6.5% spread. ANOVA F = 1.13, p = 0.34. Kruskal-Wallis p = 0.77."],
    ];
    t.forEach((r, i) => {
      const x = MX + i * 4.1;
      card(s, x, 5.3, 3.95, 1.5);
      s.addText(r[0], { x: x + 0.2, y: 5.36, w: 3.55, h: 0.35, fontFace: FONT, fontSize: 15, bold: true, color: C.blue, margin: 0 });
      s.addText(r[1], { x: x + 0.2, y: 5.72, w: 3.55, h: 1.05, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    });
  }

  // ---------- 8. Annual cycle and ARIMA ----------
  {
    const s = base(
      "methods",
      "The annual cycle is unmistakable, so ARIMA carries it with Fourier terms and no weekly order",
      "[11:30 to 13:30] The annual cycle by contrast is very strong: monthly median with the interquartile range shaded, high in winter, low in the monsoon. Its strength is what makes the absence of a weekly cycle credible rather than an artefact of a weak test. So the classical benchmark is ARIMA on the log series with four pairs of annual Fourier terms as exogenous regressors. The order was chosen by AIC over a 24-candidate grid. (1,1,1) scores 1892.5; the next candidate, (1,1,2), 1893.6, a gap of 1.1, too small to call decisively, so (1,1,1) is the more parsimonious reading. Fitted phi 0.581, theta minus 0.987. Theta sits only 0.013 inside the invertibility boundary, and in the rolling refits it crosses the boundary at 3 of 28 refits, each with fewer than 1,700 training days, which is Figure 3.6 on the next slide. The optimiser is not constrained, so a forecast is still produced there."
    );
    const a = await fitImage(s, "fig3_5_annual.png", MX, 1.8, 5.0, 3.6);
    caption(s, "Figure 3.5. Monthly median with interquartile range shaded.", MX, a.y + a.h + 0.2, 5.0);
    eq(s, "(1 − ϕ₁B)(1 − B) yₜ = c + (1 + θ₁B) εₜ\n+ Σₖ₌₁⁴ [ αₖ sin(2πkt/365.25) + βₖ cos(2πkt/365.25) ]", 6.0, 1.8, 6.75, 1.1, 15);
    s.addText("yₜ = log(PM2.5), B is the backshift operator, K = 4 annual Fourier pairs, no weekly seasonal order.", { x: 6.0, y: 3.0, w: 6.75, h: 0.4, fontFace: FONT, fontSize: 12.5, italic: true, color: C.grey, margin: 0 });
    bullets(
      s,
      [
        ["Order by AIC ", "over a 24-candidate (p, d, q) grid: (1,1,1) scores 1892.5, next (1,1,2) at 1893.6, a gap of 1.1."],
        ["Fitted: ", "ϕ₁ = 0.581 and θ₁ = −0.987, which is 0.013 inside the invertibility boundary."],
        ["Back-transform: ", "median = exp(m), mean = exp(m + s²/2). Both are reported as separate models."],
      ],
      6.0, 3.55, 6.75, 3.2, { fontSize: 16 }
    );
  }

  // ---------- 9. Model suite ----------
  {
    const s = base(
      "methods",
      "Twelve specifications from three families, all scored by one protocol",
      "[13:30 to 15:00] The suite. Classical and naive: persistence, climatology, seasonal naive at lag 7, and ARIMA with Fourier terms. Machine learning: ridge, random forest and histogram gradient boosting, the trees each fitted to both the level of log concentration and its change from the origin. Deep learning: a GRU, an LSTM and a transformer, each fitted over ten random seeds and reported as a range. The supervisor asked for machine learning rather than relying on ARIMA, and wanted several methods tried; ARIMA stays as the benchmark so ML results have a reference point. A Kolmogorov-Arnold-LSTM hybrid was also tried, but only as a bounded check. Every model is fitted to the log of concentration, and at origin t may use only observations up to day t."
    );
    const cols = [
      ["Classical and naive", C.grey, ["Persistence (repeat today)", "Climatology", "Seasonal naive, lag 7", "ARIMA(1,1,1) + annual Fourier terms"]],
      ["Machine learning", C.blue, ["Ridge regression", "Random forest: level and change target", "Histogram gradient boosting: level and change target"]],
      ["Deep learning (10 seeds each)", C.verm, ["GRU", "LSTM", "Transformer encoder", "Kolmogorov-Arnold-LSTM: bounded check only"]],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 4.1;
      card(s, x, 1.8, 3.95, 3.7);
      s.addShape(pptx.ShapeType.rect, { x, y: 1.8, w: 3.95, h: 0.62, fill: { color: c[1] }, line: { color: c[1], width: 0 } });
      s.addText(c[0], { x: x + 0.2, y: 1.8, w: 3.6, h: 0.62, fontFace: FONT, fontSize: 16, bold: true, color: C.white, valign: "middle", margin: 0 });
      bullets(s, c[2], x + 0.2, 2.65, 3.55, 2.8, { fontSize: 17 });
    });
    card(s, MX, 5.75, W - 2 * MX, 1.05, { fill: C.pale, noShadow: true });
    s.addText("Common to all: fitted to log PM2.5, forecast at horizons h = 1, 2, 3 days, refitted as the training window expands, scored on identical forecast origins by identical code.", {
      x: MX + 0.2, y: 5.75, w: W - 2 * MX - 0.4, h: 1.05, fontFace: FONT, fontSize: 15, color: C.navy, valign: "middle", margin: 0,
    });
  }

  // ---------- 10. ML regressors ----------
  {
    const s = base(
      "methods",
      "Three machine learning regressors, each controlling variance by a different mechanism",
      "[15:00 to 17:00] Three regressors, three bias-variance mechanisms. Ridge shrinks coefficients, and unlike the others it has a closed form: the penalised normal equations give beta hat equals X transpose X plus lambda I, inverted, times X transpose y. X transpose X plus lambda I is positive definite for any lambda above zero, so the solution exists and is unique even when the lagged features are collinear, which lagged and rolling-window features of one series necessarily are. The random forest averages B trees on bootstrap resamples with random feature subsets; the variance of an average is rho sigma squared plus one minus rho over B sigma squared. The second term vanishes as B grows, but the first is a floor, and random feature subsets are what lower rho. Gradient boosting fits additively: each tree is fitted to the pseudo-residual, the negative gradient of the loss at the current ensemble, which for squared error is the ordinary residual. The histogram version accepts missing values natively, consistent with never imputing. Trees were fitted to both the level and the change from the origin, because a tree cannot extrapolate beyond the targets it was trained on."
    );
    const cols = [
      ["Ridge regression", "shrinkage", "β̂ = (XᵀX + λI)⁻¹ Xᵀy", ["Closed form: XᵀX + λI is positive definite for any λ > 0, so a unique solution exists even with collinear lags.", "λ chosen by cross-validation at every refit."]],
      ["Random forest", "bagging", "Var f̂(x) = ρσ² + (1 − ρ)σ² / B", ["Average of B trees on bootstrap resamples.", "Random feature subsets at each split lower the correlation ρ, which is the floor averaging alone cannot beat."]],
      ["Histogram gradient boosting", "additive correction", "Fₘ = Fₘ₋₁ + ν hₘ,  rᵢₘ = −∂L/∂F", ["Each tree fits the pseudo-residual: gradient descent in function space.", "Binned features accept missing values natively, so nothing is imputed."]],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 4.1;
      card(s, x, 1.75, 3.95, 4.3);
      s.addText(c[0], { x: x + 0.2, y: 1.85, w: 3.55, h: 0.4, fontFace: FONT, fontSize: 17, bold: true, color: C.navy, margin: 0 });
      s.addText(c[1].toUpperCase(), { x: x + 0.2, y: 2.25, w: 3.55, h: 0.3, fontFace: FONT, fontSize: 10.5, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      eq(s, c[2], x + 0.2, 2.65, 3.55, 0.8, 14.5);
      bullets(s, c[3], x + 0.2, 3.65, 3.55, 2.35, { fontSize: 15 });
    });
    s.addText("Trees were fitted to both the level of log concentration and its change from the forecast origin: a tree cannot extrapolate beyond the targets it was trained on, and this series drifts across the decade.", {
      x: MX, y: 6.2, w: W - 2 * MX, h: 0.7, fontFace: FONT, fontSize: 13.5, italic: true, color: C.grey, valign: "top", margin: 0,
    });
  }

  // ---------- 11. Deep nets ----------
  {
    const s = base(
      "methods",
      "Three networks under one protocol, so the comparison is the cell and nothing else",
      "[17:00 to 19:30] The GRU has two gates and no separate memory cell; the LSTM has three gates and an explicit cell state; the transformer replaces recurrence with self-attention over the 30-day window. All three share the same six input channels, log concentration, a missingness flag and two annual Fourier pairs, the same 30-day window, the same target, change in log concentration from the origin, the same Adam optimiser minimising absolute error, early stopping on the most recent 15 percent of each training window, and ten random seeds each. Parameter counts, confirmed by counting the fitted objects: GRU 2,329, LSTM 3,097, transformer 3,409, and the KAN-LSTM 3,288. Two things to flag. One: a recurrent network needs a value at every timestep, so gaps are forward-filled with a missingness flag; the transformer reuses that construction as an implementation choice, not because attention requires it. Two: the LSTM and the transformer were added only after Dr Tian's feedback challenged the GRU-over-LSTM and small-data arguments. I tested those arguments rather than leaving them as assumptions."
    );
    table(
      s,
      [
        ["Architecture", "Size", "Optimiser", "Parameters"],
        ["GRU", "24 hidden units", "Adam, lr = 0.01", "2,329"],
        ["LSTM", "24 hidden units", "Adam, lr = 0.01", "3,097"],
        ["Transformer", "d_model = 16, 2 heads, 1 layer", "Adam, lr = 0.001", "3,409"],
        ["Kolmogorov-Arnold-LSTM", "24 hidden units, grid size 5", "Adam, lr = 0.01", "3,288"],
      ],
      MX, 1.8, [2.5, 3.4, 2.2, 1.6], 0.55, { fontSize: 14 }
    );
    caption(s, "Report Table 3.6. Parameters are for the six-channel network, confirmed against the fitted model objects.", MX, 4.65, 9.7);
    bullets(
      s,
      [
        ["Shared input: ", "last 30 days, six channels: log PM2.5, missingness flag, two annual Fourier pairs."],
        ["Shared training: ", "target is the change in log concentration; Adam on absolute error; early stopping on the latest 15% of each window."],
        ["Reported as a range ", "over ten random seeds, never a single favourable one."],
      ],
      MX, 5.2, 9.7, 1.7, { fontSize: 16 }
    );
    card(s, 10.65, 1.8, 2.1, 5.0, { fill: C.navy, noShadow: true });
    s.addText("Gates", { x: 10.8, y: 1.9, w: 1.8, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: "8FC3E8", margin: 0 });
    s.addText("GRU: 2, no cell state\nLSTM: 3, plus cell state\nTransformer: none, self-attention", { x: 10.8, y: 2.3, w: 1.85, h: 2.3, fontFace: FONT, fontSize: 13, color: C.white, valign: "top", margin: 0, paraSpaceAfter: 8 });
    s.addText("Missing input", { x: 10.8, y: 3.7, w: 1.8, h: 0.35, fontFace: FONT, fontSize: 13, bold: true, color: "8FC3E8", margin: 0 });
    s.addText("forward-fill plus a missingness flag, for all three", { x: 10.8, y: 4.1, w: 1.85, h: 1.7, fontFace: FONT, fontSize: 13, color: C.white, valign: "top", margin: 0 });
  }

  // ---------- 12. Rolling-origin ----------
  {
    const s = base(
      "methods",
      "Rolling-origin evaluation: 2,303 forecasts, none of which can see the future",
      "[19:30 to 21:30] This is the fiddliest part of the project and the easiest place to leak future information. Every model is evaluated at 2,303 origins from 9 November 2019 to 24 August 2026, 6.8 years, after a three-year burn-in. Parameters are re-estimated every 90 days, the networks every 180 because each refit trains from scratch. The governing invariant: at origin t a model may use observations up to and including day t and nothing else, not a scaling constant computed on the full series. Nothing fails visibly when it is broken; the numbers just improve. So the invariant is tested directly: corrupt the series from a chosen date, rerun, and require that no forecast issued before that date changes. A second trap specific to supervised learning: the label on feature row t' is the concentration at t' + h, so the training set ends at t minus h, which is why a separate model is fitted per horizon. And the motivating result: on a single test block ARIMA scored 0.903 at one day; under rolling origin the same model scores 0.940. The single block happened to be calmer than the training period and was flattering every model."
    );
    // timeline
    const tx = MX, tw = W - 2 * MX, ty = 2.0;
    const burn = tw * 3 / 9.8;
    s.addShape(pptx.ShapeType.rect, { x: tx, y: ty, w: burn, h: 0.7, fill: { color: C.line }, line: { color: C.line, width: 0 } });
    s.addShape(pptx.ShapeType.rect, { x: tx + burn, y: ty, w: tw - burn, h: 0.7, fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
    s.addText("3-year burn-in", { x: tx, y: ty, w: burn, h: 0.7, fontFace: FONT, fontSize: 14, bold: true, color: C.navy, align: "center", valign: "middle", margin: 0 });
    s.addText("2,303 forecast origins over 6.8 years, refitted every 90 days (networks: 180)", { x: tx + burn, y: ty, w: tw - burn, h: 0.7, fontFace: FONT, fontSize: 14, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
    s.addText("9 Nov 2016", { x: tx, y: ty + 0.75, w: 2, h: 0.3, fontFace: FONT, fontSize: 11.5, color: C.grey, margin: 0 });
    s.addText("9 Nov 2019", { x: tx + burn - 0.5, y: ty + 0.75, w: 1.4, h: 0.3, fontFace: FONT, fontSize: 11.5, color: C.grey, margin: 0 });
    s.addText("27 Aug 2026", { x: tx + tw - 1.6, y: ty + 0.75, w: 1.6, h: 0.3, fontFace: FONT, fontSize: 11.5, color: C.grey, align: "right", margin: 0 });
    bullets(
      s,
      [
        ["Invariant: ", "at origin t a model may use observations up to and including day t, and nothing else. No future values, no full-series scaling."],
        ["Tested, not assumed: ", "corrupt the series from a chosen date, rerun, and require that no earlier forecast changes."],
        ["Label arithmetic: ", "the label on row t′ is the value at t′ + h, so the training set ends at t − h. One model per horizon."],
      ],
      MX, 3.5, 7.0, 3.3, { fontSize: 16 }
    );
    card(s, 8.2, 3.5, 4.55, 3.2);
    s.addText("Why not one train-test split?", { x: 8.4, y: 3.6, w: 4.15, h: 0.4, fontFace: FONT, fontSize: 16, bold: true, color: C.navy, margin: 0 });
    s.addText("0.903", { x: 8.4, y: 4.1, w: 1.9, h: 0.8, fontFace: FONT, fontSize: 38, bold: true, color: C.grey, valign: "middle", margin: 0 });
    s.addText("single block", { x: 8.4, y: 4.9, w: 1.9, h: 0.3, fontFace: FONT, fontSize: 12.5, color: C.grey, margin: 0 });
    s.addText("→", { x: 10.2, y: 4.1, w: 0.6, h: 0.8, fontFace: FONT, fontSize: 30, color: C.grey, align: "center", valign: "middle", margin: 0 });
    s.addText("0.940", { x: 10.8, y: 4.1, w: 1.9, h: 0.8, fontFace: FONT, fontSize: 38, bold: true, color: C.verm, valign: "middle", margin: 0 });
    s.addText("rolling origin", { x: 10.8, y: 4.9, w: 1.9, h: 0.3, fontFace: FONT, fontSize: 12.5, color: C.grey, margin: 0 });
    s.addText("ARIMA rMAE at one day ahead. The single block was calmer than the training period and flattered every model.", { x: 8.4, y: 5.35, w: 4.15, h: 1.25, fontFace: FONT, fontSize: 13.5, color: C.ink, valign: "top", margin: 0 });
  }

  // ---------- 13. Measures ----------
  {
    const s = base(
      "methods",
      "Scored as a warning system: an alarm budget in alarms per year, not just an error",
      "[21:30 to 23:00] The headline accuracy measure is relative MAE against persistence, computed on identical rows, so 1.000 is persistence and lower is better. I report it rather than MASE alone because MASE divides by the training period's volatility, so on a calmer test period every model's MASE falls, including naive's. The warning measures come from one contingency table. An alarm is raised when the forecast exceeds a decision threshold; an event is a day above the health threshold. Hit rate is TP over TP plus FN. False alarm rate is FP over FP plus TN, false alarms divided by quiet days, not by alarms raised. Alarms per year is what an operator actually experiences: a false alarm rate of 0.10 sounds negligible and means roughly one wasted alarm every ten quiet days. I never report plain accuracy. Finally, the Diebold-Mariano test with the Harvey-Leybourne-Newbold small-sample correction and absolute-error loss, run once per seed."
    );
    const defs = [
      ["Accuracy", "rMAE = MAE(model) / MAE(persistence)", "1.000 is persistence; below 1 beats it. Identical rows, per horizon, never averaged."],
      ["Hit rate", "TP / (TP + FN)", "Share of actual hazardous days the model catches."],
      ["False alarm rate", "FP / (FP + TN)", "False alarms divided by quiet days, not by alarms raised."],
      ["Alarms per year", "365.25 (TP + FP) / n", "The unit an operator budgets in."],
    ];
    defs.forEach((d, i) => {
      const x = MX + (i % 2) * 6.15, y = 1.75 + Math.floor(i / 2) * 2.1;
      card(s, x, y, 5.95, 1.95);
      s.addText(d[0].toUpperCase(), { x: x + 0.25, y: y + 0.12, w: 5.4, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
      s.addText(d[1], { x: x + 0.25, y: y + 0.45, w: 5.4, h: 0.6, fontFace: "Cambria Math", fontSize: 18, bold: true, color: C.navy, margin: 0 });
      s.addText(d[2], { x: x + 0.25, y: y + 1.1, w: 5.4, h: 0.75, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    });
    card(s, MX, 5.95, W - 2 * MX, 0.9, { fill: C.pale, noShadow: true });
    s.addText("Significance: Diebold-Mariano test, absolute-error loss, Harvey et al. small-sample correction, run once per seed against the same ARIMA forecast. Plain classification accuracy is never reported: with hazardous days a minority, true negatives dominate it.", {
      x: MX + 0.2, y: 5.95, w: W - 2 * MX - 0.4, h: 0.9, fontFace: FONT, fontSize: 13, color: C.navy, valign: "middle", margin: 0,
    });
  }

  // ---------- 14. RQ1 table ----------
  {
    const s = base(
      "results",
      "RQ1: every machine learning regressor loses to ARIMA, at every horizon",
      "[23:00 to 25:00] Table 4.1, the central accuracy result. rMAE against persistence, lower is better. Read it in three bands. The three networks are ranges across ten seeds: at one day ahead they run 0.910 to 0.939 against ARIMA's 0.940, so they win, but at three days the best network seed, 0.831, and ARIMA's 0.832 are separated by a few parts in ten thousand, a tie, and the worst seed, 0.879, is clearly weaker. ARIMA beats all five machine learning rows at every horizon. Those five, ridge and the two tree models on each target, sit between 0.878 and 1.008. Climatology and seasonal naive are worse than persistence at one day, 1.415 and 1.759. The last column is bias at h = 1: ARIMA's median forecast under-forecasts, minus 6.4, as theory says a median of a right-skewed quantity should."
    );
    const rows = [
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
    ];
    table(s, rows, MX, 1.65, [2.9, 1.6, 1.6, 1.6, 1.3], 0.385, { fontSize: 13, hl: [[4, 1], [4, 2], [4, 3], [1, 1], [2, 1], [3, 1]], boldRows: [4] });
    caption(s, "Report Table 4.1: rMAE against persistence over 2,303 origins. Lower is better. Shaded: ARIMA and the networks' one-day range.", MX, 6.75, 9, 0.3);
    stat(s, 9.95, 1.65, 2.8, 1.5, "0.940", "ARIMA at h = 1. Networks: 0.910 to 0.939", C.blue);
    stat(s, 9.95, 3.3, 2.8, 1.5, "0.831 | 0.832", "best network seed vs ARIMA at h = 3: a tie", C.verm, 26);
    stat(s, 9.95, 4.95, 2.8, 1.5, "5 of 5", "ML regressors behind ARIMA at every horizon", C.blue);
  }

  // ---------- 15. What a forecast looks like ----------
  {
    const s = base(
      "results",
      "What the one-day-ahead forecasts look like against the series they predict",
      "Figure 4.2, one representative winter, November 2024 to February 2025, rather than the full 6.8 years, which would compress every episode into an unreadable smear. Solid black is the observed series; the dashed line is ARIMA one day ahead and the dotted line is the GRU, seed 0 alone, for illustration only: every quantitative GRU claim in the report ranges or averages over all ten seeds. Both models track the shape of each winter episode rather than only its level, and the gap between them is visible mainly on the sharpest rises, exactly where a short-range nonlinear model would be expected to earn whatever edge it has."
    );
    const b = await fitImage(s, "fig4_2_predictions.png", MX, 1.8, W - 2 * MX, 3.45);
    caption(s, "Figure 4.2. One representative winter (November 2024 to February 2025). The GRU line is seed 0 alone, for illustration only.", MX, b.y + b.h + 0.2, W - 2 * MX);
    card(s, MX, 6.1, W - 2 * MX, 0.75, { fill: C.pale, noShadow: true });
    s.addText("Both models track the shape of each episode, not only its level. The gap is visible mainly on the sharpest rises, where a short-range nonlinear model would be expected to earn its edge.", { x: MX + 0.2, y: 6.1, w: W - 2 * MX - 0.4, h: 0.75, fontFace: FONT, fontSize: 14.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 15. Seeds and noise floor ----------
  {
    const s = base(
      "results",
      "A network's result is a range, not a number, and the spread is as large as many of the gaps",
      "[25:00 to 27:00] Figure 4.1 is Table 4.1 as a dot plot. None of the three networks has a single dot, because each one's ten seeds are drawn as a range bar. That is the point of this slide. Across ten seeds the GRU's spread is 0.029 at one day, 0.028 at two, and 0.048 at three. At three days that spread is wider than the gap separating ARIMA from two other models in the table, so a single seed could have been reported as beating them or losing to them at the analyst's convenience. The tree models moved by up to 0.004 between two machines, because histogram gradient boosting parallelises with OpenMP and floating-point summation order depends on thread count. And the discovery that forced ten seeds instead of five: rerunning the identical GRU command with the same seed on the same machine moved its score by nearly as much as switching to a different seed. Network training is not bit-reproducible here."
    );
    const b = await fitImage(s, "fig4_1_accuracy.png", MX, 1.65, 7.6, 4.7);
    caption(s, "Figure 4.1. Table 4.1 as a dot plot; each network's ten seeds as a range bar. The vertical line at 1.000 is persistence.", MX, b.y + b.h + 0.22, 7.6);
    card(s, 8.6, 1.65, 4.15, 2.05);
    s.addText("GRU spread across ten seeds", { x: 8.8, y: 1.75, w: 3.75, h: 0.35, fontFace: FONT, fontSize: 15, bold: true, color: C.navy, margin: 0 });
    s.addText([
      { text: "0.029", options: { bold: true, color: C.verm, fontSize: 24 } },
      { text: "  h = 1      ", options: { color: C.grey, fontSize: 12.5 } },
      { text: "0.028", options: { bold: true, color: C.verm, fontSize: 24 } },
      { text: "  h = 2", options: { color: C.grey, fontSize: 12.5, breakLine: true } },
      { text: "0.048", options: { bold: true, color: C.verm, fontSize: 24 } },
      { text: "  h = 3: wider than the gap between ARIMA and two other models", options: { color: C.grey, fontSize: 12.5 } },
    ], { x: 8.8, y: 2.15, w: 3.75, h: 1.45, fontFace: FONT, valign: "top", margin: 0 });
    bullets(
      s,
      [
        ["Noise floor 0.004: ", "tree models moved this much between two machines (thread-order floating point)."],
        ["Same seed, same machine ", "still moved the GRU nearly as much as a new seed, so five seeds became ten."],
      ],
      8.6, 3.95, 4.15, 2.8, { fontSize: 14.5 }
    );
  }

  // ---------- 16. Significance ----------
  {
    const s = base(
      "results",
      "Formal tests are more conservative than counting seeds, and the picture holds",
      "[27:00 to 29:00] Diebold-Mariano tests against ARIMA, one per seed. Plain GRU at one day: the statistic favours the GRU in all ten seeds but reaches p below 0.05 in only four. At two days none of the ten reaches significance; at three, exactly one seed does, and in ARIMA's favour, p = 0.0056. The LSTM reaches significance in five of ten at one day, the transformer in seven of ten, the strongest of the three, and the weather-augmented GRU also seven. At two and three days, no network reaches significance for the LSTM or the transformer. The right-hand column is the same test for the five ML regressors against ARIMA: the statistic favours ARIMA in all fifteen model-horizon pairs and fourteen reach p below 0.05; the exception is the change-target random forest at two days, p = 0.054. And a limitation I want to be upfront about: this test is run twenty-seven times with no correction. Under a global null, roughly 1.4 false positives expected. After a Bonferroni correction only six survive, and none of the plain GRU's, the LSTM's or the transformer's best seeds. So every individual significance claim beyond one day ahead should be read as suggestive, not confirmed. The central qualitative claims rest on several independent sources agreeing, not a single p-value."
    );
    table(
      s,
      [
        ["Seeds with p < 0.05 vs ARIMA", "h = 1", "h = 2", "h = 3"],
        ["GRU", "4 / 10", "0 / 10", "1 / 10"],
        ["GRU with weather", "7 / 10", "0 / 10", "1 / 10"],
        ["LSTM", "5 / 10", "0 / 10", "0 / 10"],
        ["Transformer", "7 / 10", "0 / 10", "0 / 10"],
      ],
      MX, 1.75, [3.0, 1.1, 1.1, 1.1], 0.5, { fontSize: 14, hl: [[1, 1], [2, 1], [3, 1], [4, 1]] }
    );
    caption(s, "Report Table 4.2 (Diebold-Mariano, small-sample corrected). The one significant 3-day GRU seed, p = 0.0056, favours ARIMA.", MX, 4.35, 6.4);
    stat(s, 7.4, 1.75, 2.55, 1.6, "14 of 15", "regressor tests favour ARIMA at p < 0.05", C.blue);
    stat(s, 10.2, 1.75, 2.55, 1.6, "6 of 27", "tests survive a Bonferroni correction", C.verm);
    card(s, 7.4, 3.55, 5.35, 2.15);
    s.addText("Read beyond one day as suggestive", { x: 7.6, y: 3.65, w: 4.95, h: 0.35, fontFace: FONT, fontSize: 15, bold: true, color: C.navy, margin: 0 });
    s.addText("Twenty-seven tests are run with no correction, so about 1.4 false positives are expected by chance. After Bonferroni, none of the plain GRU's, LSTM's or transformer's best seeds survives.", { x: 7.6, y: 4.05, w: 4.95, h: 1.55, fontFace: FONT, fontSize: 13.5, color: C.ink, valign: "top", margin: 0 });
    card(s, MX, 4.95, 6.4, 1.75, { fill: C.pale, noShadow: true });
    s.addText("Four of ten seeds significant is itself a small-sample proportion: its 95% Wilson interval runs from 0.17 to 0.69. A different batch of ten could plausibly give a noticeably different count.", { x: MX + 0.2, y: 4.95, w: 6.0, h: 1.75, fontFace: FONT, fontSize: 13.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 17. Two arguments that did not survive ----------
  {
    const s = base(
      "results",
      "Two reasons for ruling models out did not survive being tested",
      "[29:00 to 31:00] This is the part of the project I am most careful about. Two a priori arguments were made in the literature review for preferring the GRU: it has fewer parameters, and a transformer needs more data than three thousand observations. Both were tested directly under the identical protocol, on Dr Tian's feedback, and neither is supported. The LSTM beats the GRU at every horizon, by 0.005, 0.008 and 0.013, despite carrying roughly a third more parameters, 3,097 against 2,329. So the smaller network is not winning because it is smaller. Dr Tian's second review raised the transformer conditionally, 'if the size is large'. I judged three thousand observations too few. His reply was that counting every evaluation block the series is some four thousand days long, which by his reading of the literature clears the threshold. The ten-seed run bears him out: the transformer beats the GRU in eight of ten matched seeds at every horizon, matches the LSTM, and has the strongest formal significance against ARIMA at one day. One honest caveat: the transformer's four settings were inherited from a single-split check and never tuned, so this is the result of one configuration, not evidence it is the best available."
    );
    const cols = [
      ["Argument 1: fewer parameters favour the GRU", "LSTM beats GRU at every horizon", "by 0.005, 0.008, 0.013 rMAE", "3,097 parameters against the GRU's 2,329, a third more. The smaller network is not winning because it is smaller."],
      ["Argument 2: too little data for a transformer", "Transformer beats GRU in 8 of 10 seeds", "at every horizon, and matches the LSTM", "Dr Tian's count of about 4,000 days clears the threshold. At h = 1 it has the strongest formal result of the three: 7 of 10 seeds significant."],
    ];
    cols.forEach((c, i) => {
      const x = MX + i * 6.15;
      card(s, x, 1.8, 5.95, 3.75);
      s.addText(c[0].toUpperCase(), { x: x + 0.25, y: 1.88, w: 5.45, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.grey, charSpacing: 1.5, margin: 0 });
      s.addText(c[1], { x: x + 0.25, y: 2.3, w: 5.45, h: 0.55, fontFace: FONT, fontSize: 22, bold: true, color: C.verm, margin: 0 });
      s.addText(c[2], { x: x + 0.25, y: 2.85, w: 5.45, h: 0.45, fontFace: FONT, fontSize: 17, bold: true, color: C.navy, margin: 0 });
      s.addText(c[3], { x: x + 0.25, y: 3.5, w: 5.45, h: 2.3, fontFace: FONT, fontSize: 18, color: C.ink, valign: "top", margin: 0 });
    });
    card(s, MX, 5.8, W - 2 * MX, 0.9, { fill: C.pale, noShadow: true });
    s.addText("Caveat stated in the report: the transformer's four settings were inherited from a single-split check, not tuned. This is one configuration's result.", {
      x: MX + 0.2, y: 5.8, w: W - 2 * MX - 0.4, h: 0.9, fontFace: FONT, fontSize: 15, color: C.navy, valign: "middle", margin: 0,
    });
  }

  // ---------- 18. Weather ----------
  {
    const s = base(
      "results",
      "Weather helps at one day ahead and leaves two and three days a tie",
      "[31:00 to 33:00] I added observed wind speed and temperature, the physical candidate being a calm, stagnant airmass, which the Fourier terms, knowing only the calendar, cannot represent. Figure 4.3: the weather-augmented GRU against the plain GRU, each as a range across ten seeds. At one day the bars separate cleanly; at two and three days they overlap substantially. The tree models respond unevenly, Table 4.4: gradient boosting on the level target improves by 8.2 points of relative error at one day, the random forest on the level target is 5.3 points worse at three days. Important methodological point: under the first five seeds, two and three days both looked like a win for the network, and that did not survive a second batch of five. Doubling the seed count is what surfaced it. A data-quality note: the weather record ends 202 days before the PM2.5 series does, so I repeated the comparison restricted to origins fully inside the observed weather window; the ordering at one day survived and so did the mixed picture beyond it."
    );
    const b = await fitImage(s, "fig4_3_weather.png", MX, 1.8, 7.0, 3.1);
    caption(s, "Figure 4.3. The GRU's range over ten seeds, plain against weather-augmented. The bars separate at h = 1 and overlap at h = 2 and 3.", MX, b.y + b.h + 0.2, 7.0);
    table(
      s,
      [
        ["Change in rMAE with weather", "h = 1", "h = 2", "h = 3"],
        ["Gradient boosting, level", "−0.082", "−0.020", "−0.029"],
        ["Gradient boosting, change", "−0.073", "−0.047", "+0.006"],
        ["Ridge", "−0.031", "−0.005", "+0.023"],
        ["Random forest, level", "+0.002", "−0.006", "+0.053"],
        ["Random forest, change", "−0.003", "−0.001", "+0.022"],
      ],
      7.95, 1.75, [2.55, 0.75, 0.75, 0.75], 0.45, { fontSize: 12.5 }
    );
    caption(s, "Report Table 4.4. Negative is an improvement.", 7.95, 4.5, 4.8);
    card(s, MX, 5.35, W - 2 * MX, 1.45, { fill: C.pale, noShadow: true });
    s.addText("GRU with weather beats ARIMA at h = 1 in all ten seeds (7 of 10 significant). At h = 2, three seeds win, six tie, one loses; at h = 3, three win, two tie, five lose. Under the first five seeds both horizons looked like wins: doubling the seed count is what overturned that. Result survives restriction to origins inside the fully observed weather window.", {
      x: MX + 0.2, y: 5.35, w: W - 2 * MX - 0.4, h: 1.45, fontFace: FONT, fontSize: 13.5, color: C.navy, valign: "middle", margin: 0,
    });
  }

  // ---------- 19. Weather through the threshold ----------
  {
    const s = base(
      "results",
      "Carried through the decision threshold, a more accurate forecaster buys about one point of hit rate",
      "[33:00 to 34:30] This is the test that matters for the central finding. I reran the threshold sweep with the weather models added as candidates at every alarm budget, scored on identical origins. Table 4.5: at several budgets the weather models do not even supply the best option, a delta of exactly zero. Where they do win, the improvement is at most 1.2 points of hit rate, at two days and a budget of 40, and one point or under elsewhere. Compare that with the five-point spread across models and the fifty-point range the budget itself buys. A materially more accurate point forecast, 8.2 points of relative error for gradient boosting at one day, translates into at most a little over a point of additional hit rate once run through a decision threshold. So the ceiling is not a property of the original models being insufficiently accurate; it persists even after a better forecaster is added."
    );
    table(
      s,
      [
        ["Best hit rate, alarms per year", "40", "60", "80", "100"],
        ["h = 1, no weather", "0.401", "0.609", "0.787", "0.899"],
        ["h = 1, weather models added", "0.402", "0.609", "0.792", "0.909"],
        ["h = 2, no weather", "0.388", "0.597", "0.771", "0.900"],
        ["h = 2, weather models added", "0.400", "0.597", "0.771", "0.900"],
        ["h = 3, no weather", "0.383", "0.567", "0.756", "0.876"],
        ["h = 3, weather models added", "0.383", "0.577", "0.756", "0.876"],
      ],
      MX, 1.8, [3.5, 1.1, 1.1, 1.1, 1.1], 0.5, { fontSize: 14, hl: [[4, 1], [2, 4], [6, 2]] }
    );
    caption(s, "Report Table 4.5: best achievable hit rate within an alarm budget, averaged over the ten network seeds, scored on identical origins.", MX, 5.4, 7.9);
    stat(s, 9.2, 1.8, 3.55, 1.7, "≤ 1.2 points", "largest hit-rate gain from adding weather models (h = 2, budget 40)", C.verm);
    stat(s, 9.2, 3.65, 3.55, 1.7, "8.2 points", "rMAE gain for gradient boosting at h = 1, which became at most a little over 1 point of hit rate", C.blue);
    card(s, MX, 5.95, W - 2 * MX, 0.85, { fill: C.pale, noShadow: true });
    s.addText("The ceiling is not the ten original models being too inaccurate: it persists after a materially more accurate forecaster is added.", { x: MX + 0.2, y: 5.95, w: W - 2 * MX - 0.4, h: 0.85, fontFace: FONT, fontSize: 14.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 21. RQ2 ----------
  {
    const s = base(
      "results",
      "RQ2: forecast-then-threshold has a real but modest edge over direct classification",
      "To compare the two arms fairly, I matched each classifier to the regressor built from the same underlying algorithm, ridge against penalised logistic, and the change-target random forest and gradient boosting against their own classifier counterparts, so the training objective is the only thing that varies. Comparing best models would be misleading: forecast-then-threshold has seven regressors to choose from, classification has three. Across three pairs, three horizons, four budgets, 36 comparisons: forecast-then-threshold wins 21, classification wins 11, four ties. The median difference is 0.011 in hit rate, the largest 0.056. The edge shrinks as the budget loosens: 8 of 9 at a budget of 40, 7 of 9 at 60, but classification wins 6 of 9 at 100. I prefer forecast-then-threshold also on grounds beyond the numbers: it produces a concentration that can be rethresholded for any future health policy without refitting; a classifier is welded to the threshold it was trained on. The full three-horizon picture is Figure 4.4 in the backup slides."
    );
    const rows = [
      ["h = 1, alarms per year", "40", "60", "80", "100"],
      ["Ridge: forecast then threshold", "0.377", "0.554", "0.723", "0.850"],
      ["Ridge: penalised logistic", "0.356", "0.550", "0.721", "0.856"],
      ["Random forest (change): forecast", "0.367", "0.550", "0.729", "0.867"],
      ["Random forest: classifier", "0.331", "0.550", "0.719", "0.856"],
      ["Grad. boosting (change): forecast", "0.379", "0.554", "0.727", "0.854"],
      ["Grad. boosting: classifier", "0.323", "0.546", "0.727", "0.865"],
    ];
    // shade the better arm in each column of each matched pair; exact ties stay unshaded
    const hl = [];
    [[1, 2], [3, 4], [5, 6]].forEach(([f, c]) => {
      for (let col = 1; col <= 4; col++) {
        const a1 = parseFloat(rows[f][col]), a2 = parseFloat(rows[c][col]);
        if (a1 > a2) hl.push([f, col]);
        else if (a2 > a1) hl.push([c, col]);
      }
    });
    table(s, rows, MX, 1.8, [3.7, 0.95, 0.95, 0.95, 0.95], 0.52, { fontSize: 14, hl });
    caption(s, "Report Table 4.6: forecast-then-threshold against direct classification, matched by base algorithm, h = 1. Shaded: the better arm in each column; exact ties unshaded.", MX, 5.55, 7.5);
    [["21", "forecast-then-threshold wins", C.blue], ["11", "direct classification wins", C.grey], ["4", "exact ties", C.grey]].forEach((t, i) => {
      const y = 1.8 + i * 1.3;
      card(s, 9.0, y, 3.75, 1.15);
      s.addText(t[0], { x: 9.2, y, w: 1.2, h: 1.15, fontFace: FONT, fontSize: 40, bold: true, color: t[2], valign: "middle", margin: 0 });
      s.addText(t[1], { x: 10.4, y, w: 2.25, h: 1.15, fontFace: FONT, fontSize: 15, color: C.ink, valign: "middle", margin: 0 });
    });
    s.addText("of 36 matched comparisons (3 pairs, 3 horizons, 4 budgets)", { x: 9.0, y: 5.6, w: 3.75, h: 0.3, fontFace: FONT, fontSize: 11, italic: true, color: C.grey, valign: "top", margin: 0 });
    card(s, MX, 6.1, W - 2 * MX, 0.75, { fill: C.pale, noShadow: true });
    s.addText("Median gap 0.011 of hit rate, largest 0.056. It wins 8 of 9 at a 40-alarm budget and 7 of 9 at 60, but loses 6 of 9 at 100.", { x: MX + 0.2, y: 6.1, w: W - 2 * MX - 0.4, h: 0.75, fontFace: FONT, fontSize: 14.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 21. RQ3 headline ----------
  {
    const s = base(
      "results",
      "RQ3: moving the alarm budget changes the hit rate by fifty points, and changing the model by five",
      "[36:00 to 38:00] This is the principal result of the project. Table 4.7: best hit rate available within a budget of alarms per year, event fixed at the health threshold, only the decision threshold varying. At one day ahead, moving the budget from 40 to 100 alarms a year changes the achievable hit rate from 0.379 to 0.881. Holding the budget fixed and changing the model instead moves it by around five points. Look at the rows at a fixed column, say 100 alarms: GRU 0.863 to 0.881, ARIMA 0.867, persistence 0.873, gradient boosting 0.854, climatology 0.821. Two individual comparisons make the point sharper. At three days ahead and a budget of 40 alarms a year, persistence, a forecast that just repeats yesterday's reading, is the single best model in the entire study, 0.359, ahead of every ML regressor, ARIMA, and every one of the GRU's ten seeds. And at the loosest budget, 100 alarms, three days ahead, a climatological forecast, using no recent information whatever, comes within a hundredth of the best fitted model, 0.816 against 0.827. Mechanism: exceedances arrive as multi-day episodes, so the most informative fact about whether day t + 3 is hazardous is often simply that day t already is."
    );
    table(
      s,
      [
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
      ],
      MX, 1.7, [3.45, 1.15, 1.15, 1.15, 1.15], 0.4, { fontSize: 12.5, hl: [[1, 1], [1, 4], [9, 1]], boldRows: [1] }
    );
    caption(s, "Report Table 4.7. Persistence and climatology at h = 3 are the two models the discussion names.", MX, 6.2, 8.1);
    stat(s, 9.2, 1.7, 3.55, 1.55, "50 points", "0.379 to 0.881: moving the budget, 40 to 100 alarms a year (h = 1)", C.verm);
    stat(s, 9.2, 3.4, 3.55, 1.55, "about 5 points", "changing the model at a fixed budget", C.blue);
    card(s, 9.2, 5.1, 3.55, 1.7, { fill: C.pale, noShadow: true });
    s.addText("At h = 3 and 40 alarms a year, persistence (0.359) is the best model in the whole study.", { x: 9.35, y: 5.1, w: 3.25, h: 1.7, fontFace: FONT, fontSize: 14, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 22. Trade-off curves ----------
  {
    const s = base(
      "results",
      "The trade-off curves very nearly coincide, and that is the finding",
      "[38:00 to 39:30] Figure 4.5 shows the same result as curves. Top row: hit rate against false alarm rate. Bottom row: hit rate against alarms raised per year, the unit an operator budgets in. The curves for ARIMA, gradient boosting, the classifier and persistence very nearly coincide, and I deliberately did not separate them for legibility, because the overlap is the finding. Reading across the bottom row, the vertical gridlines mark 60 and about 120 alarms a year. The practical recommendation that follows: treat the alarm budget as the primary subject of discussion with the health authority commissioning a system, and the forecasting model as a secondary refinement of a curve whose shape is mostly fixed by what every model shares, persistence from one day to the next and the annual cycle. This is not an argument against modelling: ARIMA and the networks earn real if modest gains over persistence in Table 4.1."
    );
    const b = await fitImage(s, "fig4_5_tradeoff.png", MX, 1.8, 7.4, 4.35);
    caption(s, "Figure 4.5. Top: hit rate against false alarm rate. Bottom: hit rate against alarms per year. The curves have deliberately not been separated.", MX, b.y + b.h + 0.15, 7.4);
    bullets(
      s,
      [
        ["Same curve, every model. ", "Each model sits on nearly the same trade-off curve at each horizon."],
        ["What differs is where you stand on it, ", "and that is the operator's decision: alarms per year."],
        ["Not anti-modelling. ", "ARIMA and the networks earn real, modest gains over persistence (Table 4.1). The leverage in the problem sits elsewhere."],
      ],
      8.4, 1.85, 4.35, 4.6, { fontSize: 16.5 }
    );
  }

  // ---------- 23. Robustness ----------
  {
    const s = base(
      "discuss",
      "The central finding survives every check, and the checks changed what I can claim about the models",
      "[39:30 to 41:30] Discussion: what I checked and what it did to the claims. The cleaning ceiling of 1000 is a judgement, so I restored the seven removed days, three of them the clipped 1990, and refit the whole rolling-origin harness. ARIMA barely moves, 0.935 against 0.940 at one day, because working in logs and differencing absorbs the contamination. The ML models are not protected: ridge goes from a near tie with persistence to a clear loss, 0.997 to 1.118, and gradient boosting on the level target from a narrow win to a loss at three days, 0.883 to 1.006. So the RQ1 finding that ARIMA beats every ML model strengthens rather than weakens. Second, bounded checks on the GRU's own configuration: at one and two days the default is at or near the best setting tried. At three days it is the worst of the six architecture settings, with a 45-day window 2.2 points better, SGD with momentum about 2 points better, and four Fourier harmonics instead of two 3.96 points better, enough on that split to put the network's mean below ARIMA's. That last one is the pointed one: my explanation that the network has to learn seasonality ARIMA is handed is not quite right, because it is handed a coarser version of the same signal. None of this was rerun under the full evaluation, so nothing in Table 4.1 changed."
    );
    table(
      s,
      [
        ["Check", "What changed", "Result"],
        ["Restore the 7 capped days", "Refit full harness on uncapped series", "ARIMA 0.935 vs 0.940 (h = 1). Ridge 0.997 → 1.118. GB level 0.883 → 1.006 (h = 3)."],
        ["Weather coverage gap", "Restrict to origins inside observed window", "One-day ordering survives; two- and three-day picture unchanged."],
        ["Seed count 5 → 10", "Doubled for every network", "Weather win at h = 2 and 3 did not survive."],
        ["GRU window, size (bounded)", "6 settings, 3 seeds, one split", "Default at or near best at h = 1, 2; worst of six at h = 3 (45-day window 2.2 points better)."],
        ["GRU Fourier pairs (bounded)", "2 pairs → 4 (matches ARIMA)", "h = 3 improves 3.96 points, enough to put the mean below ARIMA on this split."],
        ["GRU optimiser (bounded)", "Adam / RMSprop / SGD, lr ×/÷ 3", "h = 3: SGD with momentum about 2 points better (0.839 vs 0.858)."],
      ],
      MX, 1.75, [2.65, 3.2, 6.28], 0.62, { fontSize: 13, leftCols: [1, 2] }
    );
    card(s, MX, 6.15, W - 2 * MX, 0.7, { fill: C.pale, noShadow: true });
    s.addText("The bounded checks are single-split, three-seed: nothing in the ten-seed rolling-origin Table 4.1 was changed on their strength.", { x: MX + 0.2, y: 6.15, w: W - 2 * MX - 0.4, h: 0.7, fontFace: FONT, fontSize: 13.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 24. Limitations ----------
  {
    const s = base(
      "discuss",
      "What the results do not show",
      "[41:30 to 43:00] Limitations, stated plainly. One monitor, in one city: every number describes one point in Delhi, a diplomatic enclave, not the city, and not other cities. The cleaning ceiling is a judgement, though checked. Hyperparameter grids for the tree models were small, so the ML results are a lower bound on what those classes could achieve. The weather is observed, not forecast: a real early-warning system would feed in a numerical weather prediction, which is a stronger and untested claim; and boundary layer height, the variable most directly tied to the physical mechanism, is not available from meteostat. The LSTM and transformer were not carried through weather or the threshold sweep; given the central finding I have no particular reason to expect that to overturn it, but an expectation is not the same as the run. The KAN-LSTM is a bounded check only. And the significance tests: uncorrected, with best-seed selection a second undisclosed form of selection, and not checked by bootstrap for the heavy tails of PM2.5."
    );
    const items = [
      ["One site, one city", "8118 is a diplomatic-enclave monitor. Nothing here is a claim about Delhi as a whole or about other cities."],
      ["Observed weather, not forecast weather", "A real early-warning system would use numerical weather prediction. Boundary layer height is not available from meteostat."],
      ["Scope boundaries", "The LSTM and transformer were not given weather channels or the threshold sweep. The KAN-LSTM is a bounded check only."],
      ["Small search spaces", "Tree grids were small; the ML results are a lower bound. The GRU's 3-day configuration is the one its own checks least defend."],
      ["Significance testing", "27 tests, no joint correction, best-seed selection, and no bootstrap check of the heavy tails of the loss differential."],
      ["Not bit-reproducible", "Network training moves at a fixed seed; ten seeds reduce the problem but do not remove it."],
    ];
    items.forEach((it, i) => {
      const x = MX + (i % 3) * 4.1, y = 1.75 + Math.floor(i / 3) * 2.55;
      card(s, x, y, 3.95, 2.4);
      s.addText(it[0], { x: x + 0.2, y: y + 0.12, w: 3.55, h: 0.7, fontFace: FONT, fontSize: 16.5, bold: true, color: C.navy, valign: "top", margin: 0 });
      s.addText(it[1], { x: x + 0.2, y: y + 0.85, w: 3.55, h: 1.5, fontFace: FONT, fontSize: 15, color: C.ink, valign: "top", margin: 0 });
    });
  }

  // ---------- 25. Conclusions ----------
  {
    const s = base(
      "concl",
      "Three questions asked, three answered",
      "[43:00 to 45:30] Conclusions, from Table 6.1. RQ1: ARIMA beats every ML regressor at every horizon, rMAE 0.940 at one day, backed by a Diebold-Mariano test at every comparison. The deep networks beat it only at one day ahead, each reported as a range across ten seeds. RQ2: neither arm dominates; 21, 11 and 4 across 36 matched comparisons; I prefer forecast-then-threshold because a concentration can be rethresholded for any future policy. RQ3: moving the budget changes the hit rate by fifty points; changing the model by about five. Along the way: two real defects in the source data, a clipped ceiling and a miscalculated coverage statistic, found and corrected before any model was fitted, and an assumption from the approved proposal, a weekly cycle, tested directly and found false. The supervisor's instruction to try several methods rather than defaulting to ARIMA was the right one: it is what makes the negative result at two and three days credible, and what surfaces the one-day result a project restricted to classical methods would never have found."
    );
    const rows = [
      ["RQ1", "Accuracy vs benchmarks", "ARIMA beats every ML regressor at every horizon (rMAE 0.940 at h = 1). The GRU beats ARIMA only at h = 1, across all ten seeds. LSTM and transformer follow the same pattern.", C.blue],
      ["RQ2", "Forecast then threshold, or classify?", "Neither dominates: 21 / 11 / 4 across 36 matched comparisons. Forecast-then-threshold preferred: a concentration can be rethresholded for any future policy.", C.blue],
      ["RQ3", "Model choice vs decision threshold", "Budget sweep moves hit rate from 0.379 to 0.881 (h = 1, 40 to 100 alarms a year). Model choice moves it about 5 points at a fixed budget.", C.verm],
    ];
    rows.forEach((r, i) => {
      const y = 1.7 + i * 1.5;
      card(s, MX, y, W - 2 * MX, 1.35);
      s.addText(r[0], { x: MX + 0.25, y, w: 1.0, h: 1.35, fontFace: FONT, fontSize: 28, bold: true, color: r[3], valign: "middle", margin: 0 });
      s.addText(r[1], { x: MX + 1.4, y: y + 0.12, w: 3.0, h: 1.1, fontFace: FONT, fontSize: 15.5, bold: true, color: C.navy, valign: "middle", margin: 0 });
      s.addText(r[2], { x: MX + 4.55, y: y + 0.08, w: W - 2 * MX - 4.8, h: 1.2, fontFace: FONT, fontSize: 14.5, color: C.ink, valign: "middle", margin: 0 });
    });
    card(s, MX, 6.2, W - 2 * MX, 0.65, { fill: C.pale, noShadow: true });
    s.addText("Along the way: two source-data defects corrected before modelling, and a weekly-cycle assumption from the proposal tested and found false.", { x: MX + 0.2, y: 6.2, w: W - 2 * MX - 0.4, h: 0.65, fontFace: FONT, fontSize: 13.5, color: C.navy, valign: "middle", margin: 0 });
  }

  // ---------- 26. Recommendation and future work ----------
  {
    const s = base(
      "concl",
      "Design the warning system around its alarm budget, and treat the model as a refinement",
      "[45:30 to 47:30] The recommendation: a hazardous air quality warning system should be designed around the alarm budget its operator can justify, with the forecasting model treated as a secondary refinement. Six extensions follow from the report. One: a real numerical weather forecast in place of observed conditions. Two: boundary layer height from a reanalysis product such as ERA5, the variable most directly tied to the physical mechanism. Three: refit the recurrent network with four Fourier harmonics under the full ten-seed evaluation, which would settle whether the gap to ARIMA at two and three days is substantially a consequence of that one undocumented difference. Four: a second, independent station, ideally in the CPCB network once its record lengthens. Five: complete the LSTM's and transformer's treatment with weather and the threshold sweep. Six: a full ten-seed evaluation of the Kolmogorov-Arnold-LSTM hybrid. Then questions."
    );
    card(s, MX, 1.75, 5.1, 4.9, { fill: C.navy, noShadow: true });
    s.addText("RECOMMENDATION", { x: MX + 0.3, y: 1.95, w: 4.5, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: "8FC3E8", charSpacing: 2, margin: 0 });
    s.addText("A hazardous air quality warning system should be designed around the alarm budget its operator can justify, with the forecasting model treated as a secondary refinement.", {
      x: MX + 0.3, y: 2.35, w: 4.5, h: 2.7, fontFace: FONT, fontSize: 21, bold: true, color: C.white, valign: "top", margin: 0,
    });
    s.addText("A model comparison that does not fix the alarm budget it was evaluated at has answered a question nobody who operates the system asked.", {
      x: MX + 0.3, y: 5.15, w: 4.5, h: 1.3, fontFace: FONT, fontSize: 14, italic: true, color: "C9DCEC", valign: "top", margin: 0,
    });
    s.addText("SIX EXTENSIONS", { x: 6.1, y: 1.75, w: 6, h: 0.3, fontFace: FONT, fontSize: 11, bold: true, color: C.blue, charSpacing: 2, margin: 0 });
    const ext = [
      ["Forecast weather. ", "Numerical weather prediction instead of observed conditions."],
      ["Boundary layer height. ", "From a reanalysis product such as ERA5."],
      ["Four harmonics for the GRU ", "under the full ten-seed rolling-origin evaluation."],
      ["A second station, ", "ideally inside the CPCB network."],
      ["Complete the LSTM and transformer: ", "weather channels and the threshold sweep."],
      ["Promote the KAN-LSTM ", "from a bounded check to a ten-seed evaluation."],
    ];
    ext.forEach((e, i) => {
      const y = 2.15 + i * 0.75;
      s.addShape(pptx.ShapeType.ellipse, { x: 6.1, y: y + 0.05, w: 0.5, h: 0.5, fill: { color: C.blue }, line: { color: C.blue, width: 0 } });
      s.addText(String(i + 1), { x: 6.1, y: y + 0.05, w: 0.5, h: 0.5, fontFace: FONT, fontSize: 15, bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
      s.addText([{ text: e[0], options: { bold: true, color: C.navy } }, { text: e[1] }], { x: 6.8, y, w: 5.95, h: 0.6, fontFace: FONT, fontSize: 14.5, color: C.ink, valign: "middle", margin: 0 });
    });
  }

  // ---------- 27. Questions ----------
  {
    const s = pptx.addSlide();
    n += 1;
    s.background = { color: C.navy };
    s.addText("Thank you. Questions?", { x: MX, y: 2.2, w: 9, h: 1.0, fontFace: FONT, fontSize: 48, bold: true, color: C.white, margin: 0 });
    s.addText("The alarm budget a decision maker accepts dominates the choice of model.", { x: MX, y: 3.4, w: 9.5, h: 0.8, fontFace: FONT, fontSize: 22, color: "8FC3E8", margin: 0 });
    s.addText("Code, data and report: github.com/JC16092/mth5000-aqi-forecast", { x: MX, y: 5.0, w: 9.5, h: 0.4, fontFace: FONT, fontSize: 16, color: "C9DCEC", margin: 0 });
    s.addText("Backup slides follow: ARIMA order search, significance tables, GRU sensitivity, architecture checks.", { x: MX, y: 5.5, w: 10, h: 0.4, fontFace: FONT, fontSize: 14, color: "8FA6BD", margin: 0 });
    s.addNotes(timedNotes("Thank you. Happy to take questions. Backup slides: B1 ARIMA order search (Table 3.4), B2 Diebold-Mariano against ARIMA (Tables 4.2 and 4.3), B3 GRU sensitivity (Table 5.1 and Figure 5.1), B4 ARIMA coefficient stability (Figure 3.6) and architecture bounded checks (Figure 5.2), B5 RQ2 across all horizons (Figure 4.4)."));
  }

  // ---------- Backups ----------
  {
    const s = base("backup", "B1. The ARIMA order search in full: all 24 candidates by AIC",
      "Backup. Table 3.4. Four orders did not converge to a stable estimate on the training block and are marked. (1,1,1) is chosen; the next best, (1,1,2), is 1.1 AIC points behind, too small a gap to call decisively, which is why parsimony is the defensible reading. BIC is also given.");
    const r = [
      ["(1,1,1)", "1892.5", "1955.8", "chosen"], ["(1,1,2)", "1893.6", "1962.6", ""], ["(2,1,1)", "1894.4", "1963.4", ""], ["(3,1,1)", "1895.8", "1970.5", ""],
      ["(2,1,2)", "1895.8", "1970.6", "no convergence"], ["(3,1,2)", "1897.7", "1978.2", ""], ["(1,0,2)", "1910.4", "1985.2", "no convergence"], ["(2,0,1)", "1912.0", "1986.7", "no convergence"],
      ["(1,0,1)", "1912.1", "1981.1", ""], ["(2,0,0)", "1914.7", "1983.7", ""], ["(3,0,1)", "1915.5", "1996.0", "no convergence"], ["(3,0,2)", "1919.9", "2006.1", ""],
      ["(1,0,0)", "1927.4", "1990.7", ""], ["(0,0,2)", "2009.2", "2078.2", ""], ["(0,1,2)", "2022.5", "2085.7", ""], ["(2,0,2)", "2100.0", "2180.5", "no convergence"],
      ["(3,0,0)", "2126.5", "2201.2", "no convergence"], ["(3,1,0)", "2153.8", "2222.8", "no convergence"], ["(0,0,1)", "2167.9", "2231.1", ""], ["(0,1,1)", "2177.9", "2235.4", ""],
      ["(2,1,0)", "2196.7", "2259.9", "no convergence"], ["(1,1,0)", "2265.2", "2322.7", ""], ["(0,1,0)", "2355.6", "2407.4", ""], ["(0,0,0)", "2734.0", "2791.5", ""],
    ];
    const hdr = ["(p,d,q)", "AIC", "BIC", "note"];
    const left = [hdr, ...r.slice(0, 12)], right = [hdr, ...r.slice(12)];
    table(s, left, MX, 1.65, [1.2, 1.0, 1.0, 2.5], 0.355, { fontSize: 12, hl: [[1, 0], [1, 1], [1, 2], [1, 3]] });
    table(s, right, 6.8, 1.65, [1.2, 1.0, 1.0, 2.5], 0.355, { fontSize: 12 });
    caption(s, "Report Table 3.4, sorted by AIC.", MX, 6.45, 6);
  }
  {
    const s = base("backup", "B2. Diebold-Mariano tests against ARIMA",
      "Backup. Table 4.2 is the networks: ranges across ten seeds of the statistic and the p-value, and the count of seeds reaching p below 0.05. Negative statistic favours the network. Table 4.3 is the five ML regressors, one fit each: positive favours ARIMA, and the asterisk marks p below 0.05. All 15 favour ARIMA; 14 are significant.");
    table(
      s,
      [
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
      ],
      MX, 1.75, [1.9, 0.4, 1.6, 1.7, 0.9], 0.37, { fontSize: 11.5 }
    );
    table(
      s,
      [
        ["ARIMA vs. ML regressor", "h = 1", "h = 2", "h = 3"],
        ["Ridge", "4.25 (<0.001)", "3.85 (<0.001)", "3.62 (<0.001)"],
        ["RF, level", "3.05 (0.002)", "2.43 (0.015)", "2.19 (0.029)"],
        ["RF, change", "1.99 (0.046)", "1.93 (0.054)", "3.53 (<0.001)"],
        ["GB, level", "3.92 (<0.001)", "2.65 (0.008)", "2.26 (0.024)"],
        ["GB, change", "3.00 (0.003)", "2.51 (0.012)", "1.96 (0.050)"],
      ],
      7.5, 1.75, [1.65, 1.2, 1.2, 1.2], 0.5, { fontSize: 11, hl: [[3, 2]] }
    );
    caption(s, "Report Tables 4.2 and 4.3. Positive statistic favours ARIMA. All 15 regressor pairings favour ARIMA; 14 reach p < 0.05 (RF change, h = 2: p = 0.054, shaded). Cells show DM statistic (p-value).", 7.5, 4.85, 5.25);
  }
  {
    const s = base("backup", "B3. GRU sensitivity: three bounded checks, three seeds, one split",
      "Backup. Table 5.1 and Figure 5.1. Mean rMAE across the same three seeds for each setting. The vertical line in each panel of the figure marks the default. At one and two days the default sits near the best. At three days it spreads widely, and the default is the worst of the six architecture settings. Single-split, three-seed: nothing in Table 4.1 changed on this basis.");
    table(
      s,
      [
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
      ],
      MX, 1.65, [1.55, 2.5, 0.8, 0.8, 0.8], 0.4, { fontSize: 12 }
    );
    const b = await fitImage(s, "fig5_1_sensitivity.png", 7.7, 1.65, 5.05, 4.2);
    caption(s, "Figure 5.1. Mean rMAE across the same three seeds, one row per setting; the vertical line marks the default.", 7.7, b.y + b.h + 0.2, 5.05);
  }
  {
    const s = base("backup", "B4. ARIMA coefficient stability, and all four architectures' bounded checks",
      "Backup. Left, Figure 3.6: phi hat drifts upward over the evaluation span; theta hat oscillates close to the invertibility boundary and crosses it outright at three of 28 refits, each with fewer than 1,700 training days. The optimiser is not constrained, so a forecast is still produced and scored at those refits. Right, Figure 5.2: all four architectures' bounded checks together, each a range over the same three seeds, against ARIMA's rolling-origin rMAE for reference. The Kolmogorov-Arnold hybrid sits among the other three rather than apart from them.");
    const a = await fitImage(s, "fig3_6_arima_stability.png", MX, 1.8, 6.0, 4.0);
    caption(s, "Figure 3.6. Both coefficients across all 28 refits; the three open points cross the invertibility boundary.", MX, a.y + a.h + 0.2, 6.0);
    const b = await fitImage(s, "fig5_2_architectures.png", 6.95, 1.8, 5.8, 4.0);
    caption(s, "Figure 5.2. Bounded checks, ranges over three seeds, against ARIMA's rolling-origin rMAE.", 6.95, b.y + b.h + 0.2, 5.8);
  }

  {
    const s = base("backup", "B5. RQ2 at all three horizons: the hit-rate advantage of forecast-then-threshold",
      "Backup. Figure 4.4 extends Table 4.6 to all three horizons: the hit-rate advantage of forecast-then-threshold over its matched classifier, by alarm budget, one line per matched pair. Above the zero line forecast-then-threshold wins; below it the classifier does. The lines start mostly above zero at a budget of 40 and drift toward it, and below it, as the budget loosens and the horizon lengthens. Forecast-then-threshold wins 8 of 12 matched comparisons at one day ahead, 7 of 12 at two days and 6 of 12 at three.");
    const b = await fitImage(s, "fig4_4_arms.png", MX, 1.8, W - 2 * MX, 3.4);
    caption(s, "Figure 4.4. Above the zero line forecast-then-threshold wins; below it the classifier does. One line per matched pair.", MX, b.y + b.h + 0.2, W - 2 * MX);
    card(s, MX, 6.1, W - 2 * MX, 0.75, { fill: C.pale, noShadow: true });
    s.addText("Forecast-then-threshold wins 8 of 12 matched comparisons at one day ahead, 7 of 12 at two days and 6 of 12 at three: an edge that narrows rather than changing hands.", { x: MX + 0.2, y: 6.1, w: W - 2 * MX - 0.4, h: 0.75, fontFace: FONT, fontSize: 14.5, color: C.navy, valign: "middle", margin: 0 });
  }

  await pptx.writeFile({ fileName: OUT });
  console.log("wrote", OUT, "slides:", n);
}

build().catch((e) => {
  console.error(e);
  process.exit(1);
});
