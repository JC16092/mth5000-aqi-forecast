// Builds presentation/slides_v2.pptx — the "threshold line" design, rebuilt
// locally so the file carries no third-party watermark and no rented dependency.
//
//   node build_deck_v2.js
//
// Design concept: the health threshold as a recurring coral rule, with the
// project's own real daily PM2.5 series spiking across it. Deep teal #16343A
// dominant, warm coral #E35D45 accent. Dark cover / dividers / hero / closing
// sandwich light content slides.
//
// Coordinates are ported from the 1920x1080 design at 144 px/in, so IN(px) and
// PT(px) below convert design pixels to pptxgenjs inches and points directly.
//
// Every number and citation is unchanged from the verified deck — see
// ../README.md. Bulleted lines are ONE text run each (a pptxgenjs run carrying
// options.bullet always opens a new paragraph; a second run in the same bullet
// silently loses the bullet and indent).

const pptxgen = require("pptxgenjs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = "/Users/jc/Desktop/PROJECT MTH5000";
const FIG = path.join(ROOT, "report/figures");
const EQ = path.join(ROOT, "presentation/pptx_src/eq");
const BG = path.join(ROOT, "presentation/pptx_src/bg");
const OUT = path.join(ROOT, "presentation/slides_v2.pptx");

const IN = (px) => px / 144;
const PT = (px) => px / 2;

const NAVY = "16343A";
const NAVY_DARK = "0E2125";
const GHOST = "1E4850";
const INK = "1C2B2C";
const SLATE = "5C7678";
const MUTED = "7E9A9C";
const PALE = "AFC6C8";
const CANVAS = "F1F4F4";
const WHITE = "FFFFFF";
const CORAL = "E35D45";
const CORAL_LT = "F0A999";
const TEAL_MID = "3D6D72";
const TEAL_DK = "2F5F67";
const LINE = "DCE3E3";
const CHIP = "E9EEEE";
const STEEL = "C7D3D3";

const F = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.theme = { headFontFace: F, bodyFontFace: F };

const shadow = () => ({ type: "outer", color: NAVY, opacity: 0.16, blur: 10, offset: 3, angle: 90 });

pres.defineSlideMaster({
  title: "LIGHT",
  background: { color: CANVAS },
  slideNumber: { x: IN(1740), y: IN(1012), w: IN(70), h: IN(30), fontFace: F, fontSize: 10.5, color: SLATE, align: "right" },
});
pres.defineSlideMaster({
  title: "DARK",
  background: { color: NAVY },
  slideNumber: { x: IN(1740), y: IN(1012), w: IN(70), h: IN(30), fontFace: F, fontSize: 10.5, color: "7E9A9C", align: "right" },
});

// --- helpers ---------------------------------------------------------------

function eyebrow(s, text, color) {
  s.addText(text, {
    x: IN(110), y: IN(84), w: IN(900), h: IN(34),
    fontFace: F, fontSize: PT(20), bold: true, color: color || CORAL, charSpacing: 1.6,
  });
}

function slideTitle(s, text, color) {
  s.addText(text, {
    x: IN(110), y: IN(120), w: IN(1620), h: IN(90),
    fontFace: F, fontSize: PT(58), bold: true, color: color || NAVY, valign: "top",
  });
}

function hairline(s, y, color) {
  s.addShape(pres.ShapeType.rect, {
    x: IN(110), y: IN(y), w: IN(1700), h: IN(2), fill: { color: color || LINE }, line: { type: "none" },
  });
}

function card(s, x, y, w, h, fill, withShadow) {
  const o = {
    x: IN(x), y: IN(y), w: IN(w), h: IN(h),
    rectRadius: 0.14, fill: { color: fill || WHITE }, line: { type: "none" },
  };
  if (withShadow !== false && (fill || WHITE) === WHITE) o.shadow = shadow();
  s.addShape(pres.ShapeType.roundRect, o);
}

function label(s, x, y, w, text, color) {
  s.addText(text, {
    x: IN(x), y: IN(y), w: IN(w), h: IN(32),
    fontFace: F, fontSize: PT(18), bold: true, color: color || CORAL, charSpacing: 1.4,
  });
}

function body(s, x, y, w, h, text, size, color, lh) {
  s.addText(text, {
    x: IN(x), y: IN(y), w: IN(w), h: IN(h),
    fontFace: F, fontSize: PT(size || 24), color: color || INK,
    lineSpacingMultiple: lh || 1.5, valign: "top",
  });
}

// One run per bullet — see the header note.
function bullets(s, items, x, y, w, h, size, color) {
  const runs = items.map((t) => ({
    text: t,
    options: {
      fontFace: F, fontSize: PT(size || 24), color: color || INK,
      bullet: { code: "25CF", indent: 16 },
      lineSpacingMultiple: 1.5, paraSpaceAfter: 12, breakLine: true,
    },
  }));
  s.addText(runs, { x: IN(x), y: IN(y), w: IN(w), h: IN(h), valign: "top" });
}

function pill(s, x, y, w, h, text, fill, color, size, bold) {
  s.addText(text, {
    shape: pres.ShapeType.roundRect, rectRadius: IN(h) / 2,
    x: IN(x), y: IN(y), w: IN(w), h: IN(h),
    fill: { color: fill }, line: { type: "none" },
    fontFace: F, fontSize: PT(size || 21), color: color || NAVY, bold: !!bold,
    align: "center", valign: "middle", margin: 0,
  });
}

function imgFit(file, maxWpx, maxHpx) {
  const out = execSync(`python3 -c "from PIL import Image; im=Image.open('${file}'); print(im.size[0], im.size[1])"`).toString().trim();
  const [pw, ph] = out.split(" ").map(Number);
  const a = pw / ph;
  let w = maxWpx, h = maxWpx / a;
  if (h > maxHpx) { h = maxHpx; w = maxHpx * a; }
  return { w, h };
}

function placeImg(s, file, cx, cy, maxW, maxH) {
  const { w, h } = imgFit(file, maxW, maxH);
  s.addImage({ path: file, x: IN(cx - w / 2), y: IN(cy - h / 2), w: IN(w), h: IN(h) });
}

// The project's own series: peak daily PM2.5 per ~18-day window, 2016-2026.
const SERIES = [274,283,342,297,218,126,169,161,700,167,124,106,52,104,138,695,896,505,383,298,176,132,802,286,70,397,103,780,153,184,430,620,320,363,304,510,135,157,227,301,463,83,50,68,75,55,265,525,243,335,368,221,194,152,92,61,65,93,66,61,42,46,68,82,193,549,299,349,423,258,229,145,112,173,70,46,51,41,74,158,409,301,369,278,274,118,136,121,118,161,79,63,46,45,52,70,97,379,229,223,299,449,176,117,103,129,91,58,40,34,47,52,72,137,358,345,233,343,460,375,227,97,217,87,155,99,116,80,58,31,50,47,81,194,385,665,373,332,264,231,146,100,96,117,211,74,70,54,33,42,45,44,58,202,326,236,384,285,368,189,108,86,81,108,80,60,54,64,40,51];
const CAP = 896, THR = 121;

function skyline(s, vals, baseY, maxH, hotOp, coolOp, gap) {
  const N = vals.length, bw = 1920 / N;
  vals.forEach((v, i) => {
    const h = Math.max(5, maxH * Math.sqrt(Math.min(v, CAP) / CAP));
    const hot = v > THR;
    s.addShape(pres.ShapeType.rect, {
      x: IN(i * bw), y: IN(baseY - h), w: IN(bw - (gap || 1.6)), h: IN(h),
      fill: { color: hot ? CORAL : TEAL_DK, transparency: Math.round((1 - (hot ? hotOp : coolOp)) * 100) },
      line: { type: "none" },
    });
  });
}

const CHAPTERS = [
  ["Introduction", "Why a forecast only helps if it arrives before the hazardous day — and the three questions that follow."],
  ["Literature Review", "Where these methods come from — and the one thing the Delhi literature never does."],
  ["Methodology", "The data and two real defects in it, twelve models, and one leakage-tested harness."],
  ["Results", "Three research questions answered — and the one that turns out to dominate the other two."],
  ["Discussion", "What the numbers mean, how large a difference really is, and where the limits sit."],
  ["Conclusion", "What was found, what it recommends, and what should be done next."],
];

function divider(idx, sliceStart) {
  const s = pres.addSlide({ masterName: "DARK" });
  s.background = { path: path.join(BG, "bg_dark.png") };
  const n = String(idx + 1).padStart(2, "0");
  s.addText(n, {
    x: IN(1180), y: IN(150), w: IN(700), h: IN(560),
    fontFace: F, fontSize: PT(400), bold: true, color: GHOST, align: "right", valign: "top",
  });
  skyline(s, SERIES.slice(sliceStart, sliceStart + 40), 1080, 130, 0.78, 0.5, 2.8);
  s.addShape(pres.ShapeType.rect, { x: 0, y: IN(1031), w: IN(1920), h: IN(2), fill: { color: CORAL_LT, transparency: 50 }, line: { type: "none" } });
  s.addText(`CHAPTER ${n} OF 06`, { x: IN(140), y: IN(398), w: IN(900), h: IN(36), fontFace: F, fontSize: PT(22), bold: true, color: CORAL, charSpacing: 1.8 });
  s.addText(CHAPTERS[idx][0], { x: IN(140), y: IN(440), w: IN(1000), h: IN(120), fontFace: F, fontSize: PT(92), bold: true, color: WHITE, valign: "top" });
  s.addText(CHAPTERS[idx][1], { x: IN(140), y: IN(580), w: IN(860), h: IN(100), fontFace: F, fontSize: PT(30), color: PALE, lineSpacingMultiple: 1.4, valign: "top" });
  for (let i = 0; i < 6; i++) {
    s.addShape(pres.ShapeType.roundRect, {
      x: IN(140 + i * 96), y: IN(700), w: IN(86), h: IN(7), rectRadius: 0.02,
      fill: { color: i === idx ? CORAL : TEAL_DK }, line: { type: "none" },
    });
  }
}

// ===========================================================================
// 1 — Cover
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.background = { path: path.join(BG, "bg_cover.png") };
  skyline(s, SERIES, 1080, 340, 0.96, 0.8, 1.6);
  s.addShape(pres.ShapeType.rect, { x: 0, y: IN(955), w: IN(1920), h: IN(2), fill: { color: CORAL_LT, transparency: 15 }, line: { type: "none" } });
  s.addText("121 µg/m³   ·   HEALTH THRESHOLD", {
    shape: pres.ShapeType.roundRect, rectRadius: IN(25),
    x: IN(120), y: IN(930), w: IN(452), h: IN(50),
    fill: { color: NAVY_DARK }, line: { color: CORAL, width: 1.5 },
    fontFace: F, fontSize: PT(21), bold: true, color: CORAL_LT, align: "center", valign: "middle", charSpacing: 1.2,
  });
  s.addImage({ path: path.join(BG, "monash-logo-white.png"), x: IN(1560), y: IN(96), w: IN(248), h: IN(72.5) });
  s.addText("MTH5000 · MASTERS RESEARCH PROJECT", { x: IN(120), y: IN(150), w: IN(900), h: IN(36), fontFace: F, fontSize: PT(23), bold: true, color: CORAL, charSpacing: 1.8 });
  s.addText("Forecasting Hazardous\nAir Quality Days", { x: IN(120), y: IN(206), w: IN(1340), h: IN(240), fontFace: F, fontSize: PT(104), bold: true, color: WHITE, lineSpacingMultiple: 1.02, valign: "top" });
  s.addText("Ten specifications at a Delhi monitor, one to three days ahead — and the alarm budget that outweighs every one of them.", { x: IN(120), y: IN(462), w: IN(1180), h: IN(100), fontFace: F, fontSize: PT(34), color: PALE, lineSpacingMultiple: 1.4, valign: "top" });
  s.addText("Jaykumar Vinodbhai Chauhan  ·  34710280", { x: IN(120), y: IN(600), w: IN(1200), h: IN(36), fontFace: F, fontSize: PT(26), bold: true, color: WHITE });
  s.addText("Supervisor: Dr Tianhai Tian  ·  School of Mathematics, Monash University", { x: IN(120), y: IN(640), w: IN(1200), h: IN(32), fontFace: F, fontSize: PT(23), color: MUTED });
  s.addText("Peak daily PM2.5 per ~18-day window, 2016–2026 · 3,093 usable days · square-root scale", { x: IN(820), y: IN(700), w: IN(980), h: IN(28), fontFace: F, fontSize: PT(19), color: "6E9093", align: "right" });
}

// ===========================================================================
// 2 — Agenda
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "AGENDA");
  s.addText("What we'll cover", { x: IN(110), y: IN(136), w: IN(1200), h: IN(90), fontFace: F, fontSize: PT(62), bold: true, color: NAVY, valign: "top" });
  hairline(s, 258);
  const rows = [
    ["01", "Introduction", "Why this matters, and what three questions it answers", false],
    ["02", "Literature Review", "Classical, ML and deep learning methods, and the gap this fills", false],
    ["03", "Methodology", "Data, two real defects, twelve models, one evaluation harness", false],
    ["04", "Results", "Accuracy, weather, the two arms, and the decision threshold", true],
    ["05", "Discussion", "What the numbers mean, how large a difference is, and the limits", false],
    ["06", "Conclusion", "What was found, and what comes next", false],
  ];
  rows.forEach((r, i) => {
    const x = 110 + (i % 3) * 580;
    const y = 312 + Math.floor(i / 3) * 324;
    card(s, x, y, 540, 286, r[3] ? NAVY : WHITE);
    s.addText(r[0], { x: IN(x + 36), y: IN(y + 36), w: IN(120), h: IN(60), fontFace: F, fontSize: PT(44), bold: true, color: r[3] ? CORAL : CORAL_LT });
    s.addText(r[1], { x: IN(x + 36), y: IN(y + 102), w: IN(470), h: IN(44), fontFace: F, fontSize: PT(31), bold: true, color: r[3] ? WHITE : NAVY });
    s.addText(r[2], { x: IN(x + 36), y: IN(y + 150), w: IN(470), h: IN(110), fontFace: F, fontSize: PT(21), color: r[3] ? PALE : SLATE, lineSpacingMultiple: 1.45, valign: "top" });
  });
  s.addText("Results is where the central finding lands — the alarm budget, not the model.", { x: IN(110), y: IN(982), w: IN(1700), h: IN(30), fontFace: F, fontSize: PT(20), color: MUTED });
}

// 3 — Divider 01
divider(0, 0);

// ===========================================================================
// 4 — Motivation
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "INTRODUCTION");
  slideTitle(s, "Motivation");
  hairline(s, 232);
  bullets(s, [
    "PM2.5 in Indian cities regularly reaches hazardous levels; sustained exposure raises cardiopulmonary and all-cause mortality",
    "A forecast only helps if it arrives before the hazardous day — same-day warnings are of limited use",
    "Daily PM2.5 has exploitable structure: day-to-day persistence, a strong annual cycle, dependence on recent conditions",
    "My own motivation: growing up in India, seasonal smog was ordinary life, not an abstract statistic",
  ], 110, 296, 1020, 460, 27);

  card(s, 1230, 300, 580, 280, NAVY);
  label(s, 1278, 334, 490, "THE EVENT BEING FORECAST", CORAL_LT);
  s.addText("920 days", { x: IN(1278), y: IN(376), w: IN(490), h: IN(110), fontFace: F, fontSize: PT(90), bold: true, color: WHITE, valign: "top" });
  s.addText("above the 121 µg/m³ health threshold — 29.7% of the usable record.", { x: IN(1278), y: IN(486), w: IN(490), h: IN(84), fontFace: F, fontSize: PT(22), color: PALE, lineSpacingMultiple: 1.35, valign: "top" });

  card(s, 1230, 608, 580, 190);
  label(s, 1278, 642, 490, "RECORD LENGTH", SLATE);
  s.addText("3,093", { x: IN(1278), y: IN(680), w: IN(490), h: IN(76), fontFace: F, fontSize: PT(62), bold: true, color: NAVY, valign: "top" });
  s.addText("usable daily means, 2016–2026", { x: IN(1278), y: IN(754), w: IN(490), h: IN(34), fontFace: F, fontSize: PT(21), color: SLATE });

  s.addText("A forecast issued on the morning of a hazardous day cannot change anyone's behaviour — the lead time is the point.", { x: IN(110), y: IN(928), w: IN(1700), h: IN(34), fontFace: F, fontSize: PT(21), color: MUTED });
}

// ===========================================================================
// 5 — Research problem and significance
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "INTRODUCTION");
  slideTitle(s, "Research problem and significance");
  hairline(s, 232);
  const quads = [
    [110, 296, "THE GAP IN THE LITERATURE", "Existing ML studies of Indian air quality report average error only — not decomposed by the operating point a warning actually uses.", false],
    [980, 296, "WHY AVERAGE ERROR MISLEADS", "Good average error can still mean a poor warning system — and the reverse also holds.", false],
    [110, 628, "AN ASSUMPTION WORTH TESTING", "The approved proposal assumed a weekly cycle alongside the annual one. It is tested directly here, not carried over.", false],
    [980, 628, "SIGNIFICANCE", "If the decision threshold dominates the model, then the alarm budget is the more consequential design choice.", true],
  ];
  quads.forEach(([x, y, lab, txt, dark]) => {
    card(s, x, y, 830, 300, dark ? NAVY : WHITE);
    label(s, x + 46, y + 40, 740, lab, dark ? CORAL_LT : CORAL);
    body(s, x + 46, y + 88, 740, 180, txt, 26, dark ? WHITE : INK);
  });
}

// ===========================================================================
// 6 — Objectives and research questions
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "INTRODUCTION");
  slideTitle(s, "Objectives and research questions");
  hairline(s, 232);
  s.addText("OBJECTIVES", { x: IN(110), y: IN(286), w: IN(800), h: IN(34), fontFace: F, fontSize: PT(21), bold: true, color: SLATE, charSpacing: 1.6 });
  const objs = [
    "Evaluate classical, ML and deep learning models 1–3 days ahead, under a leakage-tested protocol",
    "Compare forecast-then-threshold against direct classification",
    "Quantify skill as a warning system under a varying threshold",
  ];
  objs.forEach((t, i) => {
    const y = 334 + i * 140;
    pill(s, 110, y, 52, 52, String(i + 1), "CDDBDB", NAVY, 24, true);
    body(s, 186, y + 4, 700, 100, t, 25, INK, 1.4);
  });
  s.addShape(pres.ShapeType.rect, { x: IN(950), y: IN(286), w: IN(2), h: IN(474), fill: { color: LINE }, line: { type: "none" } });
  s.addText("RESEARCH QUESTIONS", { x: IN(1010), y: IN(286), w: IN(800), h: IN(34), fontFace: F, fontSize: PT(21), bold: true, color: SLATE, charSpacing: 1.6 });
  const rqs = [
    ["Q1", "How accurately can PM2.5 be forecast 1–3 days ahead?", false],
    ["Q2", "Threshold a forecast, or classify the exceedance directly?", false],
    ["Q3", "What hit rate / false alarm rate trade-off does each give?", true],
  ];
  rqs.forEach(([tag, t, hot], i) => {
    const y = 334 + i * 140;
    pill(s, 1010, y, 52, 52, tag, hot ? CORAL : "CDDBDB", hot ? WHITE : NAVY, 20, true);
    s.addText(t, { x: IN(1086), y: IN(y + 4), w: IN(700), h: IN(100), fontFace: F, fontSize: PT(25), bold: !!hot, color: hot ? NAVY : INK, lineSpacingMultiple: 1.4, valign: "top" });
  });
  card(s, 110, 846, 1700, 124, NAVY);
  s.addText("Q3's answer turns out to dominate Q1 and Q2 — and the report is organised around that.", { x: IN(170), y: IN(846), w: IN(1580), h: IN(124), fontFace: F, fontSize: PT(30), color: WHITE, align: "center", valign: "middle" });
}

// 7 — Divider 02
divider(1, 20);

// ===========================================================================
// 8 — Classical and machine learning methods
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "LITERATURE REVIEW");
  slideTitle(s, "Classical and machine learning methods");
  hairline(s, 232);
  const blocks = [
    [290, "ARIMA (BOX–JENKINS)", "Differenced series, own past values and errors; order chosen by an AIC grid (Hyndman & Khandakar, 2008); Fourier terms carry complex seasonality (De Livera et al., 2011)."],
    [494, "THE MACHINE LEARNING LINEAGE", "Ridge (Hoerl & Kennard, 1970); random forest = bagging (Breiman, 1996) + trees (Breiman et al., 2017) + decorrelation (Breiman, 2001); gradient boosting, additive and stagewise (Friedman, 2001)."],
    [698, "COMPETITION EVIDENCE", "Flexible learners need not beat ARIMA on short series (M3/M4: Makridakis et al., 2018/2020); an LSTM lost to ARIMA head-to-head (Siami-Namini et al., 2018) — but gradient boosting won M5, where genuine exogenous structure existed (Makridakis et al., 2022)."],
  ];
  blocks.forEach(([y, lab, txt], i) => {
    label(s, 110, y, 1050, lab);
    body(s, 110, y + 40, 1050, 140, txt, 24);
    if (i < 2) s.addShape(pres.ShapeType.rect, { x: IN(110), y: IN(y + 172), w: IN(1050), h: IN(2), fill: { color: LINE }, line: { type: "none" } });
  });
  card(s, 1250, 290, 560, 350, NAVY);
  label(s, 1298, 330, 470, "TAKEAWAY", CORAL_LT);
  body(s, 1298, 376, 470, 230, "The deciding factor is exploitable structure, not “ML vs. classical” in the abstract — and this project's single series sits closer to M4 than M5.", 26, WHITE);
  card(s, 1250, 672, 560, 266);
  label(s, 1298, 712, 470, "AND HOW IT IS TESTED", SLATE);
  body(s, 1298, 758, 470, 160, "A single train-test split understates variability (Tashman, 2000; Hewamalage et al., 2023) — the motivation for rolling-origin evaluation.", 23);
}

// ===========================================================================
// 9 — Deep learning: why a GRU
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "LITERATURE REVIEW");
  slideTitle(s, "Deep learning: narrowing to a GRU");
  s.addText("Each ruled out a priori for a stated reason — then the two closest were fitted in full, and both beat the GRU.", { x: IN(1180), y: IN(140), w: IN(630), h: IN(60), fontFace: F, fontSize: PT(23), color: SLATE, align: "right", lineSpacingMultiple: 1.35, valign: "top" });
  hairline(s, 232);
  const rows = [
    ["MLP", "No sense of sequence order — needs the same hand-built lag table the regression and tree models already use (Hornik et al., 1989)"],
    ["CNN", "Fixed receptive field, ill-suited to an annual cycle already handed to every model as Fourier terms (LeCun et al., 1998)"],
    ["Transformer / TFT", "Large parameter counts, tuned for datasets orders of magnitude bigger than ~3,000 observations (Lim et al., 2021) — fitted in full after Dr Tian challenged that premise, and it beats the GRU", true],
    ["Plain RNN", "Vanishing and exploding gradients over long sequences (Bengio et al., 1994)"],
    ["LSTM", "Fixes that with 3 gates and a memory cell — more parameters than this dataset needs (Hochreiter & Schmidhuber, 1997) — fitted in full on Dr Tian's advice, and it wins too", true],
  ];
  rows.forEach(([name, why, tested], i) => {
    const y = 286 + i * 106;
    card(s, 110, y, 1700, 92, WHITE, false);
    // a priori screen vs. what was actually fitted afterwards — not the same verdict
    pill(s, 140, y + 24, 44, 44, tested ? "→" : "✕", tested ? "F7DAD3" : "E6EBEB", tested ? CORAL : "8FA3A4", 22, true);
    s.addText(name, { x: IN(212), y: IN(y), w: IN(300), h: IN(92), fontFace: F, fontSize: PT(27), bold: true, color: NAVY, valign: "middle" });
    s.addText(why, { x: IN(520), y: IN(y), w: IN(1250), h: IN(92), fontFace: F, fontSize: PT(23), color: SLATE, valign: "middle" });
  });
  card(s, 110, 816, 1700, 108, NAVY);
  pill(s, 140, 848, 44, 44, "✓", CORAL, WHITE, 22, true);
  s.addText("GRU", { x: IN(212), y: IN(816), w: IN(300), h: IN(108), fontFace: F, fontSize: PT(29), bold: true, color: WHITE, valign: "middle" });
  s.addText("2 gates, no memory cell, same gradient-flow property, smaller parameter count (Cho et al., 2014). Chapter 4 tests both size arguments directly — and supports neither.", { x: IN(520), y: IN(816), w: IN(1250), h: IN(108), fontFace: F, fontSize: PT(22), color: "C9DCDC", valign: "middle" });
}

// ===========================================================================
// 10 — Delhi air quality and the research gap
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "LITERATURE REVIEW");
  slideTitle(s, "Delhi air quality, and the research gap");
  hairline(s, 232);
  const quads = [
    [110, 288, "WHERE DELHI'S POLLUTION COMES FROM", "Traffic, industry and seasonal stubble burning (Guttikunda et al., 2014; Cusworth et al., 2018; Jethva et al., 2019)."],
    [980, 288, "PRIOR DELHI PM2.5 ML STUDIES", "Masood & Ahmad (2020) and Singh & Srivastava (2025) score accuracy only — none evaluates forecasts as a warning system with an explicit alarm budget."],
    [110, 560, "FORECAST VERIFICATION", "Match measures to the decision (Jolliffe & Stephenson, 2012); CSI (Schaefer, 1990); plain accuracy misleads on imbalanced events (He & Garcia, 2009; Saito & Rehmsmeier, 2015)."],
    [980, 560, "DATA QUALITY", "The literature on negative readings (Jiang et al., 2023) and on missingness mirrors the two defects found in this project's own source data."],
  ];
  quads.forEach(([x, y, lab, txt]) => {
    card(s, x, y, 830, 248);
    label(s, x + 46, y + 36, 740, lab);
    body(s, x + 46, y + 80, 740, 150, txt, 24);
  });
  card(s, 110, 846, 1700, 124, NAVY);
  s.addText("THE GAP", { x: IN(166), y: IN(872), w: IN(300), h: IN(30), fontFace: F, fontSize: PT(19), bold: true, color: CORAL_LT, charSpacing: 1.4 });
  s.addText("Evaluate the comparison against an explicit alarm budget — Chapter 4 shows it changes which model wins.", { x: IN(166), y: IN(900), w: IN(1580), h: IN(50), fontFace: F, fontSize: PT(28), color: WHITE, valign: "top" });
}

// 11 — Divider 03
divider(2, 40);

// ===========================================================================
// 12 — The data and two defects
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "The data — and two defects in it");
  hairline(s, 232);
  const tiles = [
    [110, "PERIOD", "2016–2026", false],
    [542, "USABLE DAYS", "3,093 (86.4%)", false],
    [974, "LONGEST GAP", "34 days", false],
    [1406, "ABOVE THRESHOLD", "920 (29.7%)", true],
  ];
  tiles.forEach(([x, lab, val, dark]) => {
    card(s, x, 272, x === 1406 ? 404 : 402, 118, dark ? NAVY : WHITE, false);
    s.addText(lab, { x: IN(x + 32), y: IN(294), w: IN(340), h: IN(28), fontFace: F, fontSize: PT(17), bold: true, color: dark ? CORAL_LT : SLATE, charSpacing: 1.2 });
    s.addText(val, { x: IN(x + 32), y: IN(322), w: IN(340), h: IN(52), fontFace: F, fontSize: PT(34), bold: true, color: dark ? WHITE : NAVY, valign: "top" });
  });
  body(s, 110, 424, 1700, 80, "OpenAQ. Every CPCB station returns only ~18 months; only location 8118 (AirNow, a US diplomatic post) has the full decade — selected, with that limitation stated plainly.", 24);

  card(s, 110, 518, 900, 208);
  pill(s, 152, 552, 48, 48, "01", CORAL, WHITE, 19, true);
  s.addText("Clipped instrument ceiling", { x: IN(222), y: IN(552), w: IN(740), h: IN(40), fontFace: F, fontSize: PT(26), bold: true, color: NAVY });
  body(s, 222, 596, 740, 110, "1990 µg/m³ repeats identically on three unrelated dates — an instrument ceiling, not a reading.", 23, SLATE);

  card(s, 110, 750, 900, 226);
  pill(s, 152, 784, 48, 48, "02", CORAL, WHITE, 19, true);
  s.addText("Wrong coverage denominator", { x: IN(222), y: IN(784), w: IN(740), h: IN(40), fontFace: F, fontSize: PT(26), bold: true, color: NAVY });
  body(s, 222, 828, 740, 130, "It assumed 24 hourly readings; the sensor was half-hourly 2016–2024. Recomputed: 1,085 of 3,467 days fall below 75% true coverage, against 268 with no value at all.", 23, SLATE);

  card(s, 1050, 518, 760, 458);
  label(s, 1086, 552, 688, "THE COVERAGE DEFECT, DIAGNOSED", SLATE);
  placeImg(s, path.join(FIG, "fig2_coverage.png"), 1430, 736, 688, 300);
  s.addText("Cadence taken from the data each year (solid) against the assumed 24 (dashed), and implausible values by true coverage.", { x: IN(1086), y: IN(904), w: IN(688), h: IN(60), fontFace: F, fontSize: PT(19), color: MUTED, lineSpacingMultiple: 1.35, valign: "top" });
}

// ===========================================================================
// 13 — Seasonality
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "Seasonality: tested, not assumed");
  hairline(s, 232);
  body(s, 110, 258, 800, 70, "The approved proposal assumed a weekly cycle alongside the annual one. It was tested directly, three independent ways.", 23, SLATE, 1.4);
  const tests = [
    [344, "PERIODOGRAM", "Dominant periods near 358, 179 and 61 days — the annual cycle and its harmonics. Nothing near 7."],
    [520, "AUTOCORRELATION", "Lag 7 is 0.173 and lag 6 is 0.179 — sitting on the decay curve, not above it."],
    [696, "DAY OF WEEK", "ANOVA p = 0.34; Kruskal-Wallis p = 0.77. No day differs from the rest."],
  ];
  tests.forEach(([y, lab, txt]) => {
    card(s, 110, y, 800, 152);
    label(s, 152, y + 30, 700, lab);
    body(s, 152, y + 64, 700, 80, txt, 23, INK, 1.4);
  });
  card(s, 950, 344, 860, 504);
  label(s, 988, 382, 784, "LAGS 7, 14 AND 21 SIT ON THE DECAY", SLATE);
  placeImg(s, path.join(FIG, "fig3_weekly.png"), 1380, 610, 784, 380);
  card(s, 110, 876, 1700, 100, NAVY);
  s.addText("No weekly cycle at this station — consistent with a diplomatic enclave rather than a roadside site. ARIMA therefore carries annual Fourier terms only.", { x: IN(166), y: IN(876), w: IN(1590), h: IN(100), fontFace: F, fontSize: PT(26), color: WHITE, valign: "middle" });
}

// ===========================================================================
// 14 — Features and weather covariates
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "Features and weather covariates");
  hairline(s, 232);
  card(s, 110, 282, 1080, 400);
  label(s, 152, 314, 990, "ONE ROW PER FORECAST ORIGIN t — USING ONLY DATA UP TO DAY t");
  const chips = [
    [152, 356, 250, "Lags 0, 1, 2, 3, 7"], [418, 356, 250, "First differences"], [684, 356, 340, "Rolling mean / SD / max"],
    [152, 424, 300, "Windows 3, 7, 14, 30 d"], [468, 424, 330, "Anomaly vs 30-day norm"], [814, 424, 300, "Exceedance frequency"],
    [152, 492, 360, "Days since last exceedance"], [528, 492, 230, "Calendar terms"], [774, 492, 310, "4 annual Fourier pairs"],
    [152, 560, 290, "3 missingness flags"],
  ];
  chips.forEach(([x, y, w, t]) => pill(s, x, y, w, 52, t, CHIP, NAVY, 21));
  s.addText("Missing values are never imputed — the two recurrent networks are the only exception.", { x: IN(152), y: IN(628), w: IN(990), h: IN(40), fontFace: F, fontSize: PT(22), color: SLATE });

  card(s, 1230, 282, 580, 430, NAVY);
  label(s, 1278, 314, 490, "WEATHER (METEOSTAT)", CORAL_LT);
  bullets(s, [
    "Temperature, wind speed, pressure, precipitation",
    "Each at its own value, a one-day lag, and a 3-day rolling mean",
    "Only observations up to day t — never a forecast",
  ], 1278, 358, 490, 340, 23, WHITE);

  card(s, 110, 716, 1700, 260);
  pill(s, 152, 752, 48, 48, "03", CORAL, WHITE, 19, true);
  s.addText("A third data defect — in the weather record itself", { x: IN(222), y: IN(752), w: IN(1500), h: IN(40), fontFace: F, fontSize: PT(26), bold: true, color: NAVY });
  body(s, 222, 800, 1500, 150, "The archive ends 202 days before the PM2.5 series does: a hard cutoff, not scattered gaps. Precipitation is only 54% complete and is excluded from the recurrent network for that reason. The comparison is therefore checked twice — over every origin, and restricted to origins inside the fully observed window.", 24, SLATE);
}

// ===========================================================================
// 15 — Classical benchmark and ML regressors
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "Classical benchmark and ML regressors");
  hairline(s, 232);
  card(s, 110, 282, 1700, 268);
  label(s, 156, 314, 1600, "ARIMA(1,1,1) WITH FOUR ANNUAL FOURIER PAIRS — ORDER CHOSEN BY AIC (1892.5)");
  placeImg(s, path.join(EQ, "eq_arima-1.png"), 960, 423, 1320, 122);
  s.addText("Fitted on log(PM2.5) — φ₁ = 0.581, θ₁ = −0.987, both inside the stationarity and invertibility boundaries.", { x: IN(156), y: IN(498), w: IN(1600), h: IN(40), fontFace: F, fontSize: PT(22), color: SLATE, align: "center" });
  s.addText("THREE MACHINE LEARNING REGRESSORS — EACH FITTED TO LEVEL AND TO CHANGE FROM ORIGIN", { x: IN(110), y: IN(586), w: IN(1700), h: IN(34), fontFace: F, fontSize: PT(21), bold: true, color: SLATE, charSpacing: 1.4 });
  const models = [
    [110, "Ridge", "β = (XᵀX + λI)⁻¹Xᵀy", "A closed-form solution — the penalty keeps it stable when lagged and rolling features are collinear, as they necessarily are."],
    [690, "Random forest", "bagging + random features", "Bagged trees plus a random feature subset at each split, which decorrelates the trees and lowers the variance floor averaging alone cannot reach."],
    [1270, "Gradient boosting", "additive, stagewise", "Each round's tree corrects the ensemble's residual. The histogram implementation accepts missing values natively — no imputation step."],
  ];
  models.forEach(([x, name, formula, txt]) => {
    card(s, x, 636, 540, 340);
    s.addText(name, { x: IN(x + 46), y: IN(672), w: IN(450), h: IN(44), fontFace: F, fontSize: PT(28), bold: true, color: NAVY });
    s.addText(formula, { x: IN(x + 46), y: IN(718), w: IN(450), h: IN(40), fontFace: F, fontSize: PT(23), bold: true, color: CORAL });
    body(s, x + 46, 766, 450, 180, txt, 23, SLATE);
  });
}

// ===========================================================================
// 16 — The gated recurrent unit
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "The three deep learning models");
  hairline(s, 232);
  card(s, 110, 282, 840, 440);
  label(s, 156, 314, 760, "TWO GATES, NO SEPARATE MEMORY CELL");
  placeImg(s, path.join(EQ, "eq_gru-1.png"), 530, 494, 688, 272);
  s.addText("hₜ is a convex combination, not a product of nonlinear transforms — so gradients survive many timesteps.", { x: IN(156), y: IN(644), w: IN(760), h: IN(72), fontFace: F, fontSize: PT(20), color: MUTED, lineSpacingMultiple: 1.3, valign: "top", margin: 0 });
  card(s, 990, 282, 820, 440);
  label(s, 1036, 314, 740, "THREE ARCHITECTURES, ONE PROTOCOL");
  const archs = [
    ["GRU", "2 gates, no separate memory cell — 2,329 parameters", 352, NAVY],
    ["LSTM", "3 gates and an explicit cell state — 3,097 parameters", 444, NAVY],
    ["Transformer", "Self-attention in place of recurrence: d_model = 16, 2 heads, 1 encoder layer — 3,409, the largest of the three", 536, CORAL],
  ];
  archs.forEach(([name, detail, y, c]) => {
    s.addText(name, { x: IN(1036), y: IN(y), w: IN(740), h: IN(34), fontFace: F, fontSize: PT(26), bold: true, color: c, margin: 0, valign: "middle" });
    s.addText(detail, { x: IN(1036), y: IN(y + 34), w: IN(740), h: IN(58), fontFace: F, fontSize: PT(20), color: SLATE, lineSpacingMultiple: 1.25, valign: "top", margin: 0 });
  });
  s.addShape(pres.ShapeType.rect, { x: IN(1036), y: IN(636), w: IN(728), h: IN(2), fill: { color: "E6EBEB" }, line: { type: "none" } });
  s.addText("Same 6 channels, same 30-day window, same target, same optimiser, same ten seeds. Only the architecture differs.", { x: IN(1036), y: IN(652), w: IN(740), h: IN(64), fontFace: F, fontSize: PT(21), color: SLATE, lineSpacingMultiple: 1.3, valign: "top", margin: 0 });
  card(s, 110, 754, 1700, 222, NAVY);
  s.addText("10", { x: IN(166), y: IN(786), w: IN(340), h: IN(110), fontFace: F, fontSize: PT(92), bold: true, color: CORAL, valign: "top" });
  s.addText("RANDOM SEEDS", { x: IN(166), y: IN(894), w: IN(340), h: IN(34), fontFace: F, fontSize: PT(21), bold: true, color: CORAL_LT, charSpacing: 1.4 });
  body(s, 560, 798, 1190, 150, "The three models whose results depend on a random initialisation. Every number for them is reported as a range across ten runs, never a single favourable one — and the GRU's training is not even bit-reproducible at a fixed seed.", 25, WHITE);
}

// ===========================================================================
// 17 — Rolling-origin evaluation and measures
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "METHODOLOGY");
  slideTitle(s, "Rolling-origin evaluation and measures");
  hairline(s, 232);
  const tiles = [[110, "FORECAST ORIGINS", "2,303"], [542, "SPAN", "6.8 years"], [974, "REFIT CADENCE", "90 days"], [1406, "NETWORK REFIT", "180 days"]];
  tiles.forEach(([x, lab, val]) => {
    card(s, x, 272, x === 1406 ? 404 : 402, 118, WHITE, false);
    s.addText(lab, { x: IN(x + 32), y: IN(294), w: IN(340), h: IN(28), fontFace: F, fontSize: PT(17), bold: true, color: SLATE, charSpacing: 1.2 });
    s.addText(val, { x: IN(x + 32), y: IN(322), w: IN(340), h: IN(52), fontFace: F, fontSize: PT(34), bold: true, color: NAVY, valign: "top" });
  });
  card(s, 110, 420, 1700, 166, NAVY);
  s.addText("THE GOVERNING INVARIANT", { x: IN(166), y: IN(450), w: IN(500), h: IN(30), fontFace: F, fontSize: PT(19), bold: true, color: CORAL_LT, charSpacing: 1.4 });
  body(s, 166, 488, 1590, 90, "At origin t a model may use observations up to and including day t and nothing else — enforced by construction, and verified by corrupting the series from a chosen date and requiring that no earlier forecast changes.", 26, WHITE, 1.4);
  const meas = [
    [110, "ACCURACY", "rMAE against persistence", "1.000 is persistence; below one beats it. MASE reported alongside, and never averaged across horizons — skill decays with horizon and concealing that would defeat the purpose."],
    [690, "AS A WARNING SYSTEM", "Hit rate and false alarm rate", "With precision, the critical success index, and alarms raised per year. Plain accuracy is never reported: on a minority class it rewards never raising an alarm at all."],
    [1270, "SIGNIFICANCE", "Diebold-Mariano test", "With the Harvey-Leybourne-Newbold small-sample correction. Run each network against ARIMA once per seed, and ARIMA against every machine learning regressor."],
  ];
  meas.forEach(([x, lab, head, txt]) => {
    card(s, x, 626, 540, 350);
    label(s, x + 46, 662, 450, lab);
    s.addText(head, { x: IN(x + 46), y: IN(704), w: IN(450), h: IN(44), fontFace: F, fontSize: PT(25), bold: true, color: NAVY });
    body(s, x + 46, 750, 450, 200, txt, 22, SLATE);
  });
}

// 18 — Divider 04
divider(3, 80);

// ===========================================================================
// 19 — Forecast accuracy (RQ1)
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "RESULTS · RQ1");
  slideTitle(s, "Forecast accuracy");
  hairline(s, 232);
  card(s, 110, 272, 1700, 408);
  label(s, 150, 300, 900, "RELATIVE MAE AT ONE DAY AHEAD — LOWER IS BETTER");
  [589, 872, 1155, 1720].forEach((x) =>
    s.addShape(pres.ShapeType.rect, { x: IN(x), y: IN(318), w: IN(2), h: IN(294), fill: { color: "EDF1F1" }, line: { type: "none" } }));
  s.addShape(pres.ShapeType.rect, { x: IN(1437), y: IN(312), w: IN(2), h: IN(304), fill: { color: "B9C6C6" }, line: { type: "none" } });
  const dots = [
    ["Transformer, 10 seeds", 951, 326, 62],
    ["LSTM, 10 seeds", 946, 357, 107],
    ["GRU, 10 seeds", 929, 388, 164],
    ["ARIMA + Fourier", 1098, 419, 0],
    ["Random forest (change)", 1257, 450, 0],
    ["Gradient boosting (change)", 1341, 481, 0],
    ["Random forest (level)", 1370, 512, 0],
    ["Ridge regression", 1420, 543, 0],
    ["Persistence", 1437, 574, 0],
    ["Gradient boosting (level)", 1483, 605, 0],
  ];
  dots.forEach(([name, cx, y, barW]) => {
    const isRange = barW > 0;
    s.addText(name, { x: IN(150), y: IN(y), w: IN(250), h: IN(26), fontFace: F, fontSize: PT(19), bold: isRange, color: isRange ? NAVY : SLATE, align: "right", valign: "middle", margin: 0 });
    if (isRange) {
      s.addShape(pres.ShapeType.roundRect, { x: IN(cx), y: IN(y + 6), w: IN(barW), h: IN(14), rectRadius: 0.05, fill: { color: CORAL }, line: { type: "none" } });
    } else {
      s.addShape(pres.ShapeType.ellipse, { x: IN(cx - 8), y: IN(y + 5), w: IN(16), h: IN(16), fill: { color: name === "Persistence" ? "8FA3A4" : NAVY }, line: { type: "none" } });
    }
  });
  [[529, "0.85"], [812, "0.90"], [1095, "0.95"], [1377, "1.00"], [1660, "1.05"]].forEach(([x, t]) =>
    s.addText(t, { x: IN(x), y: IN(630), w: IN(120), h: IN(28), fontFace: F, fontSize: PT(18), bold: t === "1.00", color: t === "1.00" ? SLATE : "8FA3A4", align: "center" }));
  s.addText("persistence", { x: IN(1310), y: IN(654), w: IN(260), h: IN(26), fontFace: F, fontSize: PT(17), color: "8FA3A4", align: "center" });

  s.addTable([
    [{ text: "Model", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "h = 1", options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center" } },
     { text: "h = 2", options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center" } },
     { text: "h = 3", options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center" } }],
    ["Transformer, range over 10 seeds", "0.914–0.925", "0.870–0.893", "0.825–0.842"],
    ["LSTM, range over 10 seeds", "0.913–0.932", "0.874–0.892", "0.824–0.847"],
    ["GRU, range over 10 seeds", "0.910–0.939", "0.878–0.906", "0.831–0.879"],
    ["ARIMA(1,1,1) + Fourier", "0.940", "0.883", "0.832"],
    ["Best ML regressor (GBM, change)", "0.983", "0.937", "0.878"],
    ["Persistence", "1.000", "1.000", "1.000"],
  ], {
    x: IN(110), y: IN(696), w: IN(1080), colW: [IN(432), IN(216), IN(216), IN(216)],
    rowH: IN(40), fontFace: F, fontSize: PT(19), color: INK, fill: { color: WHITE },
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: LINE }, { type: "none" }],
    align: "center", valign: "middle", margin: [4, 10, 4, 10],
  });

  card(s, 1230, 696, 580, 280, NAVY);
  s.addText("15 / 15", { x: IN(1278), y: IN(718), w: IN(490), h: IN(100), fontFace: F, fontSize: PT(84), bold: true, color: CORAL, valign: "top" });
  body(s, 1278, 820, 490, 140, "Diebold-Mariano pairings favour ARIMA over every machine learning regressor, at every horizon. Fourteen reach p < 0.05. The three networks are the exception, and only at one day ahead.", 22, WHITE, 1.35);
}

// ===========================================================================
// 20 — Does weather change the answer?
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "RESULTS");
  slideTitle(s, "Does weather change the answer?");
  hairline(s, 232);
  card(s, 110, 272, 1080, 440);
  label(s, 152, 300, 1000, "CHANGE IN rMAE FROM ADDING WEATHER — NEGATIVE IS AN IMPROVEMENT");
  const cats = ["Ridge", "RF level", "RF change", "GBM level", "GBM change"];
  s.addChart(pres.ChartType.bar, [
    { name: "h=1", labels: cats, values: [-0.031, 0.002, -0.003, -0.082, -0.073] },
    { name: "h=2", labels: cats, values: [-0.005, -0.006, -0.001, -0.020, -0.047] },
    { name: "h=3", labels: cats, values: [0.023, 0.053, 0.022, -0.029, 0.006] },
  ], {
    x: IN(150), y: IN(344), w: IN(1000), h: IN(344),
    barDir: "col", chartColors: [NAVY, TEAL_MID, CORAL],
    showLegend: true, legendPos: "b", legendFontFace: F, legendFontSize: 10,
    catAxisLabelFontFace: F, catAxisLabelFontSize: 10, catAxisLabelColor: SLATE,
    valAxisLabelFontFace: F, valAxisLabelFontSize: 10, valAxisLabelColor: SLATE,
    valGridLine: { color: "EDF1F1", size: 1 }, catGridLine: { style: "none" },
    valAxisMajorUnit: 0.05,
  });
  card(s, 1230, 272, 580, 464, NAVY);
  label(s, 1278, 304, 490, "THE GRU WITH WEATHER, VS ARIMA", CORAL_LT);
  const hs = [
    ["h = 1", "Wins clearly — 7 of 10 seeds now significant, up from 4 of 10.", 338, WHITE],
    ["h = 2", "A genuine three-way split: 3 clear wins, 6 ties, 1 loss.", 476, WHITE],
    ["h = 3", "More often a loss than a win — 5 of 10.", 614, CORAL],
  ];
  hs.forEach(([h, t, y, c], i) => {
    s.addText(h, { x: IN(1278), y: IN(y), w: IN(140), h: IN(42), fontFace: F, fontSize: PT(34), bold: true, color: c, margin: 0, valign: "middle" });
    s.addText(t, { x: IN(1278), y: IN(y + 48), w: IN(490), h: IN(80), fontFace: F, fontSize: PT(22), color: PALE, lineSpacingMultiple: 1.25, valign: "top", margin: 0 });
  });
  card(s, 110, 744, 830, 232);
  label(s, 156, 780, 740, "WHAT SURFACED IT");
  body(s, 156, 822, 740, 130, "Doubling the seed count from five to ten. Under the first five seeds alone, h = 2 and h = 3 had both looked like wins for the network.", 24);
  card(s, 980, 744, 830, 232);
  label(s, 1026, 780, 740, "CARRIED THROUGH THE THRESHOLD");
  body(s, 1026, 822, 740, 130, "At most 1.2 points of extra hit rate at any budget — a materially more accurate forecaster still does not escape the alarm-budget ceiling.", 24);
}

// ===========================================================================
// 21 — Two arms of the same question (RQ2)
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "RESULTS · RQ2");
  slideTitle(s, "Two arms of the same question");
  hairline(s, 232);
  body(s, 110, 258, 1700, 44, "Forecast-then-threshold against direct classification, matched by base algorithm — 36 comparisons across 3 pairs, 3 horizons and 4 alarm budgets.", 23, SLATE, 1.3);
  s.addText("21  forecast-then-threshold", { shape: pres.ShapeType.rect, x: IN(110), y: IN(330), w: IN(991), h: IN(96), fill: { color: CORAL }, line: { type: "none" }, fontFace: F, fontSize: PT(26), bold: true, color: WHITE, align: "center", valign: "middle" });
  s.addText("11  classifier", { shape: pres.ShapeType.rect, x: IN(1101), y: IN(330), w: IN(519), h: IN(96), fill: { color: TEAL_MID }, line: { type: "none" }, fontFace: F, fontSize: PT(26), bold: true, color: WHITE, align: "center", valign: "middle" });
  s.addText("4  ties", { shape: pres.ShapeType.rect, x: IN(1620), y: IN(330), w: IN(190), h: IN(96), fill: { color: STEEL }, line: { type: "none" }, fontFace: F, fontSize: PT(23), bold: true, color: NAVY, align: "center", valign: "middle" });
  card(s, 110, 474, 880, 502);
  label(s, 156, 510, 790, "A REAL BUT MODEST EDGE");
  bullets(s, [
    "Median gap of 0.011 in hit rate, largest 0.056 — real, but modest",
    "The edge narrows as the budget loosens: 8 of 9 at a budget of 40, but the classifier overtakes it, 6 of 9, at 100",
    "Preferred anyway: a forecast can be rethresholded for any future health policy, while a classifier is welded to the threshold it was trained on",
  ], 156, 556, 790, 400, 24);
  card(s, 1030, 474, 780, 502);
  label(s, 1076, 510, 690, "HIT-RATE EDGE BY ALARM BUDGET", SLATE);
  placeImg(s, path.join(FIG, "fig7_arms.png"), 1420, 730, 688, 330);
  s.addText("Above zero, forecast-then-threshold wins; below it, the classifier does.", { x: IN(1076), y: IN(910), w: IN(690), h: IN(44), fontFace: F, fontSize: PT(19), color: MUTED, valign: "top" });
}

// ===========================================================================
// 22 — The decision threshold (RQ3) — hero
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.background = { path: path.join(BG, "bg_dark.png") };
  eyebrow(s, "RESULTS · RQ3 · THE CENTRAL RESULT");
  slideTitle(s, "The decision threshold", WHITE);
  s.addShape(pres.ShapeType.rect, { x: IN(110), y: IN(232), w: IN(1700), h: IN(2), fill: { color: TEAL_DK }, line: { type: "none" } });
  card(s, 110, 276, 1000, 560, WHITE, false);
  label(s, 152, 306, 920, "BEST ACHIEVABLE HIT RATE, BY ALARM BUDGET");
  const budgets = ["40", "60", "80", "100"];
  s.addChart(pres.ChartType.line, [
    { name: "h=1", labels: budgets, values: [0.379, 0.567, 0.735, 0.881] },
    { name: "h=2", labels: budgets, values: [0.366, 0.538, 0.700, 0.840] },
    { name: "h=3", labels: budgets, values: [0.359, 0.533, 0.685, 0.827] },
  ], {
    x: IN(150), y: IN(344), w: IN(920), h: IN(400),
    chartColors: [CORAL, TEAL_MID, "9FC7C9"], lineSize: 3, lineDataSymbolSize: 7,
    showLegend: true, legendPos: "b", legendFontFace: F, legendFontSize: 10,
    catAxisLabelFontFace: F, catAxisLabelFontSize: 11, catAxisLabelColor: SLATE,
    valAxisLabelFontFace: F, valAxisLabelFontSize: 11, valAxisLabelColor: SLATE,
    valAxisMinVal: 0, valAxisMaxVal: 1,
    valGridLine: { color: "EDF1F1", size: 1 }, catGridLine: { style: "none" },
  });
  s.addText("alarms permitted per year", { x: IN(152), y: IN(782), w: IN(920), h: IN(30), fontFace: F, fontSize: PT(19), color: MUTED, align: "center" });

  s.addText("MOVE THE BUDGET, 40 → 100", { x: IN(1170), y: IN(292), w: IN(640), h: IN(32), fontFace: F, fontSize: PT(20), bold: true, color: CORAL_LT, charSpacing: 1.6 });
  s.addText("50 pts", { x: IN(1170), y: IN(322), w: IN(640), h: IN(170), fontFace: F, fontSize: PT(150), bold: true, color: CORAL, valign: "top" });
  s.addText("of hit rate at one day ahead — 0.379 to 0.881.", { x: IN(1170), y: IN(496), w: IN(640), h: IN(60), fontFace: F, fontSize: PT(24), color: PALE, lineSpacingMultiple: 1.35, valign: "top" });
  s.addShape(pres.ShapeType.rect, { x: IN(1170), y: IN(596), w: IN(640), h: IN(2), fill: { color: TEAL_DK }, line: { type: "none" } });
  s.addText("SWITCH THE MODEL INSTEAD", { x: IN(1170), y: IN(628), w: IN(640), h: IN(32), fontFace: F, fontSize: PT(20), bold: true, color: MUTED, charSpacing: 1.6 });
  s.addText("~5 pts", { x: IN(1170), y: IN(660), w: IN(640), h: IN(62), fontFace: F, fontSize: PT(48), bold: true, color: WHITE, valign: "top" });
  s.addText("across all ten specifications, at a fixed budget.", { x: IN(1170), y: IN(726), w: IN(640), h: IN(56), fontFace: F, fontSize: PT(24), color: PALE, valign: "top" });
  body(s, 110, 886, 1700, 80, "At three days ahead and a budget of 40 alarms a year, plain persistence — carrying today's reading forward unchanged — is the single best model in the entire study, at 0.359.", 25, "C9DCDC", 1.4);
}

// 23 — Divider 05
divider(4, 120);

// ===========================================================================
// 24 — The operational question dominates
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "DISCUSSION");
  slideTitle(s, "The operational question dominates");
  hairline(s, 232);
  card(s, 110, 276, 880, 408);
  label(s, 156, 310, 790, "THREE DAYS AHEAD, AT THE LOOSEST BUDGET");
  s.addText("Climatology — uses no recent information at all", { x: IN(156), y: IN(364), w: IN(790), h: IN(34), fontFace: F, fontSize: PT(22), color: SLATE });
  s.addShape(pres.ShapeType.roundRect, { x: IN(156), y: IN(404), w: IN(634), h: IN(46), rectRadius: 0.05, fill: { color: STEEL }, line: { type: "none" } });
  s.addText("0.816", { x: IN(806), y: IN(406), w: IN(140), h: IN(44), fontFace: F, fontSize: PT(30), bold: true, color: NAVY });
  s.addText("The best fitted model in the study", { x: IN(156), y: IN(484), w: IN(790), h: IN(34), fontFace: F, fontSize: PT(22), color: SLATE });
  s.addShape(pres.ShapeType.roundRect, { x: IN(156), y: IN(524), w: IN(643), h: IN(46), rectRadius: 0.05, fill: { color: CORAL }, line: { type: "none" } });
  s.addText("0.827", { x: IN(806), y: IN(526), w: IN(140), h: IN(44), fontFace: F, fontSize: PT(30), bold: true, color: NAVY });
  body(s, 156, 602, 790, 70, "A forecast using nothing but the calendar lands within roughly a hundredth of the best model fitted here.", 22, SLATE, 1.4);
  card(s, 1030, 276, 780, 408);
  label(s, 1076, 310, 690, "BUT NOT AN ARGUMENT AGAINST MODELLING");
  bullets(s, [
    "ARIMA and the GRU both earn real gains over persistence",
    "A better point forecast still narrows the range of thresholds worth considering",
    "The argument is about where the leverage sits, not whether to model at all",
  ], 1076, 364, 690, 300, 24);
  card(s, 110, 716, 1700, 260, NAVY);
  s.addText("THE RECOMMENDATION", { x: IN(166), y: IN(750), w: IN(500), h: IN(30), fontFace: F, fontSize: PT(19), bold: true, color: CORAL_LT, charSpacing: 1.6 });
  body(s, 166, 792, 1590, 160, "The alarm budget is the policy instrument; the forecasting model only supplies its input. Fix the budget with the health authority first — and treat the choice of model as a secondary refinement of a curve whose shape is already mostly set.", 30, WHITE, 1.45);
}

// ===========================================================================
// 25 — How large is a difference between models?
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "DISCUSSION");
  slideTitle(s, "How large is a difference between models?");
  hairline(s, 232);
  card(s, 110, 276, 1000, 446);
  label(s, 156, 310, 900, "MEASURED IN rMAE — ON THE SAME SCALE");
  s.addText("Gap between two models in the table (0.878 vs 0.879 at h = 3)", { x: IN(156), y: IN(362), w: IN(900), h: IN(34), fontFace: F, fontSize: PT(21), color: SLATE });
  s.addShape(pres.ShapeType.roundRect, { x: IN(156), y: IN(402), w: IN(18), h: IN(38), rectRadius: 0.04, fill: { color: NAVY }, line: { type: "none" } });
  s.addText("0.001", { x: IN(190), y: IN(404), w: IN(200), h: IN(36), fontFace: F, fontSize: PT(22), bold: true, color: NAVY });
  s.addText("Same pipeline, same seeds, two different machines", { x: IN(156), y: IN(470), w: IN(900), h: IN(34), fontFace: F, fontSize: PT(21), color: SLATE });
  s.addShape(pres.ShapeType.roundRect, { x: IN(156), y: IN(510), w: IN(72), h: IN(38), rectRadius: 0.04, fill: { color: SLATE }, line: { type: "none" } });
  s.addText("0.004", { x: IN(244), y: IN(512), w: IN(200), h: IN(36), fontFace: F, fontSize: PT(22), bold: true, color: NAVY });
  s.addText("The GRU, across ten random seeds", { x: IN(156), y: IN(578), w: IN(900), h: IN(34), fontFace: F, fontSize: PT(21), color: SLATE });
  s.addShape(pres.ShapeType.roundRect, { x: IN(660), y: IN(618), w: IN(360), h: IN(38), rectRadius: 0.04, fill: { color: CORAL }, line: { type: "none" } });
  s.addText("0.028 – 0.048", { x: IN(156), y: IN(620), w: IN(480), h: IN(36), fontFace: F, fontSize: PT(22), bold: true, color: CORAL });
  s.addText("Rerunning the identical command with the same seed moves it almost as much.", { x: IN(156), y: IN(676), w: IN(900), h: IN(34), fontFace: F, fontSize: PT(20), color: MUTED });

  card(s, 1150, 276, 660, 446, NAVY);
  label(s, 1196, 310, 570, "THE FORMAL TEST IS STRICTER STILL", CORAL_LT);
  s.addText("GRU seeds reaching p < 0.05 against ARIMA", { x: IN(1196), y: IN(356), w: IN(570), h: IN(34), fontFace: F, fontSize: PT(21), color: PALE });
  const dm = [["4/10", "at h = 1 — the noise floor credits 8 of 10", 412, CORAL], ["0/10", "at h = 2", 514, WHITE], ["1/10", "at h = 3 — and that one favours ARIMA", 616, WHITE]];
  dm.forEach(([n, t, y, c], i) => {
    s.addText(n, { x: IN(1196), y: IN(y), w: IN(170), h: IN(64), fontFace: F, fontSize: PT(52), bold: true, color: c, valign: "top" });
    s.addText(t, { x: IN(1380), y: IN(y + 14), w: IN(390), h: IN(60), fontFace: F, fontSize: PT(22), color: c === CORAL ? WHITE : PALE, valign: "top" });
    if (i < 2) s.addShape(pres.ShapeType.rect, { x: IN(1196), y: IN(y + 86), w: IN(566), h: IN(2), fill: { color: TEAL_DK }, line: { type: "none" } });
  });
  card(s, 110, 756, 1700, 220);
  label(s, 166, 790, 1580, "AND THOSE COUNTS ARE THEMSELVES SMALL SAMPLES");
  body(s, 166, 834, 1580, 120, "A 95% Wilson interval on “4 of 10” at one day ahead runs from 0.17 to 0.69. A different batch of ten seeds could plausibly have produced a noticeably different count without the underlying comparison having changed at all.", 26);
}

// ===========================================================================
// 26 — Limitations I
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "DISCUSSION");
  slideTitle(s, "Limitations I — scope and sensitivity");
  hairline(s, 232);
  const cards3 = [
    [110, "ONE STATION", "An AirNow diplomatic-post monitor, not the CPCB network. It was chosen because it is the only nearby monitor with a full decade of record — history bought at the cost of representativeness."],
    [690, "ONE CITY", "Delhi only. Nothing here should be read as a claim about any other station or city — sources, meteorology and the strength of the annual cycle all vary by region."],
    [1270, "HYPERPARAMETERS", "Tree models were tuned from a small explicit grid at every refit, not an exhaustive search — so their results are a lower bound on what those model classes could reach."],
  ];
  cards3.forEach(([x, lab, txt]) => {
    card(s, x, 282, 540, 330);
    label(s, x + 46, 316, 450, lab);
    body(s, x + 46, 360, 450, 220, txt, 23);
  });
  s.addText("CLEANING THRESHOLD, CHECKED DIRECTLY — rMAE WITH AND WITHOUT THE 1000 µg/m³ CAP", { x: IN(110), y: IN(650), w: IN(1080), h: IN(32), fontFace: F, fontSize: PT(18), bold: true, color: SLATE, charSpacing: 1.3 });
  s.addTable([
    [{ text: "Model", options: { bold: true, color: WHITE, fill: { color: NAVY } } },
     { text: "Reported (capped)", options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center" } },
     { text: "Uncapped", options: { bold: true, color: WHITE, fill: { color: NAVY }, align: "center" } }],
    ["ARIMA, h = 1", "0.940", "0.935"],
    ["Ridge, h = 1", "0.997", "1.118"],
    ["Gradient boosting (level), h = 3", "0.883", "1.006"],
  ], {
    x: IN(110), y: IN(696), w: IN(1080), colW: [IN(480), IN(300), IN(300)],
    rowH: IN(58), fontFace: F, fontSize: PT(22), color: INK, fill: { color: WHITE },
    border: [{ type: "none" }, { type: "none" }, { pt: 0.75, color: LINE }, { type: "none" }],
    align: "center", valign: "middle", margin: [4, 10, 4, 10],
  });
  card(s, 1230, 652, 580, 324, NAVY);
  label(s, 1278, 686, 490, "WHAT THAT MEANS", CORAL_LT);
  body(s, 1278, 732, 490, 220, "The central finding does not merely survive removing the threshold — it strengthens. The models ARIMA beat most narrowly are precisely the ones most exposed to the uncleaned tail.", 24, WHITE);
}

// ===========================================================================
// 27 — Limitations II
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "DISCUSSION");
  slideTitle(s, "Limitations II — the GRU and reproducibility");
  hairline(s, 232);
  const quads = [
    [110, 282, "ARCHITECTURE FIXED BY INSPECTION", "H = 24 and a 30-day window were set by inspection, with no search equivalent to the tree models' grid. A bounded check found a 45-day window scored 2.2 points better at h = 3 — untested at the full ten-seed scale, and nothing in the reported table was changed on the strength of it.", false],
    [980, 282, "THE FOURIER ABLATION", "Giving the network ARIMA's K = 4 harmonics instead of its own K = 2 helps at every horizon — substantially at h = 3, by 3.96 points. The network was already handed a seasonal signal; just a coarser one than assumed.", false],
    [110, 652, "NOT BIT-REPRODUCIBLE", "Rerunning the identical command with the same seed moved the network's score by nearly as much as switching to a genuinely different one. That is why the seed count was doubled from five to ten — and why even ten should be read as a reduction in the problem, not a solution to it.", true],
    [980, 652, "THE WEATHER EXTENSION IS NARROW", "Only observed weather enters the table, never a forecast — a real early-warning system would use a numerical weather prediction, which is a materially stronger claim. Boundary layer height, the variable most directly tied to the physical mechanism, is unavailable without a reanalysis product.", false],
  ];
  quads.forEach(([x, y, lab, txt, dark]) => {
    card(s, x, y, 830, y === 282 ? 330 : 324, dark ? NAVY : WHITE);
    label(s, x + 46, y + 34, 740, lab, dark ? CORAL_LT : CORAL);
    body(s, x + 46, y + 80, 740, 220, txt, 24, dark ? WHITE : INK);
  });
}

// ===========================================================================
// 28 — Limitations III: the four architectures the second review added
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "DISCUSSION");
  slideTitle(s, "Limitations III — what the supervisor reviews added");
  hairline(s, 232);
  const quads = [
    [110, 282, "OPTIMISER AND LEARNING RATE — BOUNDED CHECK", "Adam at 0.01 is at or near the best setting tried at one and two days. At three days SGD with momentum beats it by about two points, 0.839 against 0.858, with a tighter seed spread. Three separate bounded checks now agree that the three-day configuration is the one this project would least defend.", false],
    [980, 282, "THE LSTM AND TRANSFORMER SCOPE, STATED PLAINLY", "Both were held to the same ten-seed rolling-origin evaluation as the GRU for accuracy, and no further: no weather channels, no threshold sweep for either. Both appear in the accuracy and significance tables and nowhere in the warning-system tables. Not tested because the marginal evidence did not justify the compute, not because a result was avoided.", false],
    [110, 652, "THE TRANSFORMER, PROMOTED OUT OF THIS LIST", "It began here as a bounded check. Dr Tian challenged the small-data premise directly — some four thousand days clears the threshold he had seen cited — so it was given the full ten-seed treatment. It beats the GRU in 8 of 10 matched seeds at every horizon and carries the strongest formal result against ARIMA at one day ahead, 7 of 10 seeds.", true],
    [980, 652, "A KAN-LSTM HYBRID — THE ONE CHECK STILL BOUNDED", "Dr Tian named this combination directly. No maintained library exists, so the layer was built from the published construction and unit-tested alone first, recovering sin(3x) to 1e-4. All three seeds trained stably. Competitive with the other three: worst at one day, best at two.", false],
  ];
  quads.forEach(([x, y, lab, txt, dark]) => {
    card(s, x, y, 830, y === 282 ? 330 : 324, dark ? NAVY : WHITE);
    label(s, x + 46, y + 34, 740, lab, dark ? CORAL_LT : CORAL);
    body(s, x + 46, y + 80, 740, 222, txt, 22, dark ? WHITE : INK, 1.4);
  });
}

// 29 — Divider 06
divider(5, 60);

// ===========================================================================
// 29 — Three questions, three answers
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "CONCLUSION");
  slideTitle(s, "Three questions, three answers");
  hairline(s, 232);
  body(s, 110, 258, 1700, 44, "Hazardous PM2.5 forecast one to three days ahead at one Delhi monitor; two real data defects corrected first; the proposal's weekly-cycle assumption tested and rejected.", 23, SLATE, 1.3);
  const ans = [
    [110, "Q1", "Machine learning earns a narrow place", "ARIMA beats every ML regressor at every horizon, DM-backed. The three that win are the networks — GRU, LSTM and transformer — each clearly only at one day ahead, reported as a range over ten seeds. Both of the two added on review beat the GRU originally chosen.", false],
    [690, "Q2", "Threshold the forecast", "Forecast-then-threshold beats direct classification in 21 of 36 matched comparisons to 11, with 4 ties — real but modest. It is preferred anyway, because a forecast can be rethresholded for any future policy without refitting.", false],
    [1270, "Q3", "The budget beats the model", "Across ten specifications at a fixed alarm budget, the spread in hit rate is about five points. Moving the budget instead moves it about fifty. The decision maker's choice outweighs the modeller's.", true],
  ];
  ans.forEach(([x, tag, head, txt, dark]) => {
    card(s, x, 334, 540, 392, dark ? NAVY : WHITE);
    pill(s, x + 46, 370, 60, 44, tag, dark ? CORAL : "CDDBDB", dark ? WHITE : NAVY, 20, true);
    s.addText(head, { x: IN(x + 46), y: IN(430), w: IN(450), h: IN(70), fontFace: F, fontSize: PT(27), bold: true, color: dark ? WHITE : NAVY, valign: "top" });
    body(s, x + 46, 500, 450, 215, txt, 21, dark ? PALE : SLATE, 1.38);
  });
  card(s, 110, 770, 1700, 206);
  label(s, 166, 804, 1580, "ON THE METHOD ITSELF");
  body(s, 166, 848, 1580, 110, "Trying several methods rather than defaulting to ARIMA is what surfaced the one-day-ahead network win — and what makes the negative result at two and three days credible. Two rounds of supervisor review then added two more architectures, and both beat the one originally chosen.", 26);
}

// ===========================================================================
// 30 — Future work
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "LIGHT" });
  eyebrow(s, "CONCLUSION");
  slideTitle(s, "Future work");
  hairline(s, 232);
  // six extensions now, so three columns rather than two
  const fw = [
    [110, 286, "1", "A genuine weather forecast", "A numerical weather prediction for the days ahead, rather than the conditions already observed at the origin — the stronger claim for an operational system, and the one this project deliberately did not make."],
    [686, 286, "2", "Boundary layer height", "Unavailable from meteostat; it would need a reanalysis product such as ERA5. It is the variable most directly tied to the physical mechanism of an episode rather than a correlate of it."],
    [1262, 286, "3", "Refit the GRU with K = 4", "Four Fourier harmonics under the full ten-seed evaluation, not the single validation split used so far — to settle how much of the gap to ARIMA that one difference explains."],
    [110, 630, "4", "A second station", "Ideally one inside the CPCB network once its record lengthens — to test whether these findings are a property of Delhi air quality, or of this one diplomatic-enclave monitor."],
    [686, 630, "5", "Finish the LSTM and the transformer", "Fit each with the weather channels and carry each through the threshold sweep — the two steps taken for neither. The honest expectation is that this refines the central finding rather than overturning it."],
    [1262, 630, "6", "Evaluate the KAN-LSTM hybrid in full", "Ten seeds and rolling origins for the one architecture still on a bounded check — the same promotion the transformer was just given, after its own bounded check proved to be understating it."],
  ];
  fw.forEach(([x, y, n, head, txt]) => {
    card(s, x, y, 546, 316);
    pill(s, x + 38, y + 32, 48, 48, n, CORAL, WHITE, 23, true);
    s.addText(head, { x: IN(x + 100), y: IN(y + 30), w: IN(410), h: IN(80), fontFace: F, fontSize: PT(25), bold: true, color: NAVY, valign: "middle" });
    body(s, x + 38, y + 116, 470, 180, txt, 21, SLATE, 1.38);
  });
}

// ===========================================================================
// 31 — Closing
// ===========================================================================
{
  const s = pres.addSlide({ masterName: "DARK" });
  s.background = { path: path.join(BG, "bg_dark.png") };
  skyline(s, SERIES, 1080, 190, 0.55, 0.35, 1.6);
  s.addShape(pres.ShapeType.rect, { x: 0, y: IN(1009), w: IN(1920), h: IN(2), fill: { color: CORAL_LT, transparency: 50 }, line: { type: "none" } });
  s.addText("THE RECOMMENDATION", { x: IN(110), y: IN(250), w: IN(1200), h: IN(36), fontFace: F, fontSize: PT(22), bold: true, color: CORAL, charSpacing: 1.8 });
  s.addText("Design the warning system around the alarm budget it can justify — and treat the forecasting model as a secondary refinement.", { x: IN(110), y: IN(300), w: IN(1500), h: IN(300), fontFace: F, fontSize: PT(62), bold: true, color: WHITE, lineSpacingMultiple: 1.2, valign: "top" });
  s.addText("Questions?", { x: IN(110), y: IN(624), w: IN(1500), h: IN(150), fontFace: F, fontSize: PT(112), bold: true, color: WHITE, valign: "top" });
  s.addText("Jaykumar Vinodbhai Chauhan  ·  34710280", { x: IN(110), y: IN(806), w: IN(900), h: IN(34), fontFace: F, fontSize: PT(24), color: PALE });
  s.addText("Supervisor: Dr Tianhai Tian  ·  School of Mathematics, Monash University", { x: IN(110), y: IN(842), w: IN(900), h: IN(30), fontFace: F, fontSize: PT(21), color: "6E9093" });
  s.addImage({ path: path.join(BG, "monash-logo-white.png"), x: IN(1560), y: IN(790), w: IN(248), h: IN(72.5) });
}

pres.writeFile({ fileName: OUT }).then(() => console.log("Wrote", OUT));
