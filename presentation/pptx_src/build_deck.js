// Builds presentation/slides.pptx from the same content as presentation/slides.tex.
// Every number/citation here is copied from slides.tex (already verified against
// report/tables/*.tex and report/main.pdf) -- not retyped from memory.
//
//   node build_deck.js
//
// Style: "bold and modern" per the user's explicit direction (they rejected
// a first, plain-academic-styled pptx pass as too simple). Content-informed
// palette: deep slate navy (dominant) + a hazard-amber accent, evoking the
// AQI warning-system subject of the talk. Dark title/section-divider/closing
// slides sandwich light content slides. Icon badges (react-icons -> sharp,
// generate_icons.js) give a repeated visual motif across the agenda and each
// section divider. No accent lines/stripes anywhere (an explicit anti-pattern
// per the pptx skill) -- separation is by whitespace, card surfaces, and the
// one accent color, used sparingly.
//
// IMPORTANT pptxgenjs constraint (confirmed by direct testing, not documented
// in the skill): a run with options.bullet truthy always starts a NEW <a:p>,
// and any other run in what should be the same paragraph still gets its own
// (default, bullet-less) <a:pPr> emitted, which wins visually over the first
// run's bullet/indent. The only reliable bulleted paragraph is therefore ONE
// run. Every bulleted item below is a single plain string (or a single
// {t,bold,italic} object styling the WHOLE bullet) -- never an array of
// differently-styled runs.

const pptxgen = require("pptxgenjs");
const path = require("path");
const { execSync } = require("child_process");
const { applyTheme } = require("./apply_theme.js");

const ROOT = "/Users/jc/Desktop/PROJECT MTH5000";
const FIG = path.join(ROOT, "report/figures");
const EQ = path.join(ROOT, "presentation/pptx_src/eq");
const ICON = path.join(ROOT, "presentation/pptx_src/icons");
const OUT = path.join(ROOT, "presentation/slides.pptx");

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

const NAVY = "16343A"; // dominant: deep atmospheric teal-charcoal
const NAVY_DARKER = "0F2327";
const INK = "1C2B2C"; // body text on light slides (teal-tinted near-black)
const SLATE = "5C7678"; // muted secondary text
const CANVAS = "F1F4F4"; // light slide background (cool teal-gray, not cream)
const WHITE = "FFFFFF";
const AMBER = "E35D45"; // the one sharp accent, used sparingly: warm coral
const AMBER_LIGHT = "F0A999";
const TEAL = "3D6D72"; // supporting accent, only where a second tone is needed
const LINE = "DCE3E3"; // hairline on light surfaces

const THEME = {
  name: "MTH5000 Hazard Warning",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: NAVY,
    lt1: WHITE,
    dk2: SLATE,
    lt2: CANVAS,
    accent1: AMBER,
    accent2: TEAL,
    accent3: AMBER_LIGHT,
    accent4: "9FC7C9",
    accent5: NAVY_DARKER,
    accent6: "7A9496",
    hlink: AMBER,
    folHlink: AMBER,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

const FONT = "Calibri";
const PW = 13.333;
const PH = 7.5;
const MARGIN = 0.55;
const CONTENT_W = PW - 2 * MARGIN;
const EYEBROW_Y = 0.32;
const TITLE_Y = 0.62;
const TITLE_H = 0.72;
const BODY_Y = 1.5;
const BODY_H = 5.55;

function freshShadow(opts) {
  return Object.assign({ type: "outer", color: NAVY, opacity: 0.18, blur: 10, offset: 3, angle: 90 }, opts || {});
}

const SLIDE_NUM_LIGHT = {
  x: PW - 1.0,
  y: 7.1,
  w: 0.7,
  h: 0.3,
  fontFace: FONT,
  fontSize: 10.5,
  color: SLATE,
  align: "right",
};
const SLIDE_NUM_DARK = Object.assign({}, SLIDE_NUM_LIGHT, { color: "7E9A9C" });

// ---------------------------------------------------------------------------
// Slide masters
// ---------------------------------------------------------------------------

pres.defineSlideMaster({
  title: "TITLE_SLIDE",
  background: { color: NAVY },
  objects: [],
});

pres.defineSlideMaster({
  title: "DIVIDER",
  background: { color: NAVY },
  slideNumber: SLIDE_NUM_DARK,
  objects: [],
});

pres.defineSlideMaster({
  title: "AGENDA",
  background: { color: CANVAS },
  slideNumber: SLIDE_NUM_LIGHT,
  objects: [],
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: CANVAS },
  slideNumber: SLIDE_NUM_LIGHT,
  objects: [
    {
      placeholder: {
        options: {
          name: "title",
          type: "title",
          x: MARGIN,
          y: TITLE_Y,
          w: CONTENT_W,
          h: TITLE_H,
          fontFace: FONT,
          fontSize: 27,
          bold: true,
          color: NAVY,
          align: "left",
          valign: "top",
        },
        text: "",
      },
    },
    {
      placeholder: {
        options: {
          name: "body",
          type: "body",
          x: MARGIN,
          y: BODY_Y,
          w: CONTENT_W,
          h: BODY_H,
          fontFace: FONT,
          fontSize: 16.5,
          color: INK,
          valign: "top",
        },
        text: "",
      },
    },
  ],
});

pres.defineSlideMaster({
  title: "FREE",
  background: { color: CANVAS },
  slideNumber: SLIDE_NUM_LIGHT,
  objects: [
    {
      placeholder: {
        options: {
          name: "title",
          type: "title",
          x: MARGIN,
          y: TITLE_Y,
          w: CONTENT_W,
          h: TITLE_H,
          fontFace: FONT,
          fontSize: 25,
          bold: true,
          color: NAVY,
          align: "left",
          valign: "top",
        },
        text: "",
      },
    },
  ],
});

pres.defineSlideMaster({
  title: "CLOSING",
  background: { color: NAVY },
  slideNumber: SLIDE_NUM_DARK,
  objects: [],
});

// ---------------------------------------------------------------------------
// Generic helpers
// ---------------------------------------------------------------------------

function eyebrow(slide, text) {
  slide.addText(text.toUpperCase(), {
    x: MARGIN,
    y: EYEBROW_Y,
    w: CONTENT_W,
    h: 0.3,
    fontFace: FONT,
    fontSize: 12,
    bold: true,
    color: AMBER,
    charSpacing: 1.5,
    align: "left",
  });
}

// Bulleted item: a plain string, or {t, bold, italic} to style the WHOLE
// line. Never an array of multiple runs -- see the file header note.
function bulletParagraphs(items, opts) {
  const o = Object.assign(
    {
      fontFace: FONT,
      fontSize: 16.5,
      color: INK,
      lineSpacingMultiple: 1.12,
      bullet: { code: "25CF", indent: 16, color: AMBER },
      paraSpaceAfter: 13,
    },
    opts || {}
  );
  return items.map((item) => {
    const isObj = typeof item === "object";
    return {
      text: isObj ? item.t : item,
      options: Object.assign({}, o, {
        bold: isObj ? !!item.bold : false,
        italic: isObj ? !!item.italic : false,
        breakLine: true,
      }),
    };
  });
}

function numberedParagraphs(items, opts) {
  const o = Object.assign(
    {
      fontFace: FONT,
      fontSize: 16.5,
      color: INK,
      lineSpacingMultiple: 1.12,
      paraSpaceAfter: 13,
    },
    opts || {}
  );
  return items.map((item, idx) => {
    const isObj = typeof item === "object";
    return {
      text: isObj ? item.t : item,
      options: Object.assign({}, o, {
        bold: isObj ? !!item.bold : false,
        italic: isObj ? !!item.italic : false,
        bullet: { numbered: true, startAt: idx + 1, color: AMBER },
        breakLine: true,
      }),
    };
  });
}

function addContentSlide(sectionTitle, chapterLabel, title, bullets, opts) {
  const slide = pres.addSlide({ masterName: "CONTENT", sectionTitle });
  eyebrow(slide, chapterLabel);
  slide.addText(title, { placeholder: "title" });
  slide.addText(bulletParagraphs(bullets, opts), { placeholder: "body" });
  return slide;
}

function addFreeSlide(sectionTitle, chapterLabel, title) {
  const slide = pres.addSlide({ masterName: "FREE", sectionTitle });
  eyebrow(slide, chapterLabel);
  slide.addText(title, { placeholder: "title" });
  return slide;
}

function fitImage(file, maxW, maxH) {
  const out = execSync(
    `python3 -c "from PIL import Image; im=Image.open('${file}'); print(im.size[0], im.size[1])"`
  )
    .toString()
    .trim();
  const [pw, ph] = out.split(" ").map(Number);
  const aspect = pw / ph;
  let w = maxW,
    h = maxW / aspect;
  if (h > maxH) {
    h = maxH;
    w = maxH * aspect;
  }
  return { w, h };
}

// White rounded card with a soft shadow behind a figure, so every reused
// report PNG (left monochrome, deliberately -- see README) sits on its own
// designed surface instead of floating bare on the canvas background.
function addImageCard(slide, file, cx, cy, maxW, maxH, pad) {
  const p = pad == null ? 0.22 : pad;
  const { w, h } = fitImage(file, maxW - 2 * p, maxH - 2 * p);
  const cardW = w + 2 * p;
  const cardH = h + 2 * p;
  const cardX = cx - cardW / 2;
  const cardY = cy - cardH / 2;
  slide.addShape(pres.ShapeType.roundRect, {
    x: cardX,
    y: cardY,
    w: cardW,
    h: cardH,
    rectRadius: 0.08,
    fill: { color: WHITE },
    line: { type: "none" },
    shadow: freshShadow(),
  });
  slide.addImage({ path: file, x: cx - w / 2, y: cy - h / 2, w, h });
  return { w: cardW, h: cardH };
}

// Booktabs-inspired table, restyled: dark header fill / white header text,
// white body rows, hairline row separators, the key row's values in bold
// amber rather than plain bold black.
function modernTable(slide, rows, opts) {
  const o = Object.assign(
    { x: MARGIN, y: 1.5, w: CONTENT_W, fontSize: 13.5, colW: null, align: "c" },
    opts || {}
  );
  const hair = { type: "solid", pt: 0.75, color: LINE };
  const none = { type: "none", pt: 0, color: WHITE };
  const nRows = rows.length;
  const data = rows.map((row, r) => {
    const isHeader = r === 0;
    const isLast = r === nRows - 1;
    return row.map((cell, c) => {
      const text = typeof cell === "string" ? cell : cell.t;
      const keyCell = typeof cell === "object" && cell.bold;
      return {
        text,
        options: {
          fontFace: FONT,
          fontSize: o.fontSize,
          color: isHeader ? WHITE : keyCell ? AMBER : INK,
          bold: isHeader || keyCell,
          fill: { color: isHeader ? NAVY : WHITE },
          align: c === 0 ? "l" : o.align,
          valign: "m",
          border: [isLast ? none : hair, none, none, none],
          margin: [5, 8, 5, 8],
        },
      };
    });
  });
  // No background card here: a table's actual rendered height is not
  // reliably predictable in advance (row wrapping, font metrics), so a
  // pre-sized card behind it risks mismatching the real table bounds and
  // colliding with whatever sits below -- confirmed by exactly that
  // collision during visual QA. Per-cell fill (navy header, white body)
  // already gives the table a clean, well-defined surface without needing
  // a separate shape to track its size.
  slide.addTable(data, { x: o.x, y: o.y, w: o.w, colW: o.colW, autoPage: false, fontFace: FONT });
}

// Big bold stat with a small label underneath -- used sparingly, only for
// the handful of numbers the report itself treats as headline findings.
function addStat(slide, cx, y, value, label, opts) {
  const o = Object.assign({ w: 3.1, valueColor: NAVY, valueSize: 54, labelColor: SLATE }, opts || {});
  slide.addText(value, {
    x: cx - o.w / 2,
    y,
    w: o.w,
    h: 0.95,
    fontFace: FONT,
    fontSize: o.valueSize,
    bold: true,
    color: o.valueColor,
    align: "center",
    valign: "bottom",
  });
  slide.addText(label, {
    x: cx - o.w / 2,
    y: y + 0.95,
    w: o.w,
    h: 0.55,
    fontFace: FONT,
    fontSize: 13,
    color: o.labelColor,
    align: "center",
    valign: "top",
    lineSpacingMultiple: 1.1,
  });
}

const CHAPTERS = [
  { key: "introduction", title: "Introduction", desc: "Why this matters, and what three questions it answers" },
  { key: "literature", title: "Literature Review", desc: "Classical, ML and deep learning methods, and the gap this fills" },
  { key: "methodology", title: "Methodology", desc: "Data, two real defects, ten models, one evaluation harness" },
  { key: "results", title: "Results", desc: "Accuracy, weather, the two arms, and the decision threshold" },
  { key: "discussion", title: "Discussion", desc: "What the numbers mean, how large a difference is, and the limits" },
  { key: "conclusion", title: "Conclusion", desc: "What was found, and what comes next" },
];

function addDividerSlide(sectionTitle, idx) {
  const slide = pres.addSlide({ masterName: "DIVIDER", sectionTitle });
  const ch = CHAPTERS[idx];
  const badgeSize = 1.7;
  slide.addImage({
    path: path.join(ICON, `${ch.key}.png`),
    x: MARGIN,
    y: 2.35,
    w: badgeSize,
    h: badgeSize,
  });
  slide.addText(`CHAPTER ${idx + 1} OF 6`, {
    x: MARGIN + badgeSize + 0.45,
    y: 2.55,
    w: 8,
    h: 0.4,
    fontFace: FONT,
    fontSize: 14,
    bold: true,
    color: AMBER,
    charSpacing: 1.5,
  });
  slide.addText(ch.title, {
    x: MARGIN + badgeSize + 0.45,
    y: 2.9,
    w: 9.5,
    h: 1.1,
    fontFace: FONT,
    fontSize: 40,
    bold: true,
    color: WHITE,
  });
  // Progress dots
  const dotR = 0.065;
  const gap = 0.3;
  const startX = MARGIN + badgeSize + 0.45;
  const dotY = 4.05;
  CHAPTERS.forEach((_, i) => {
    slide.addShape(pres.ShapeType.ellipse, {
      x: startX + i * gap,
      y: dotY,
      w: dotR * 2,
      h: dotR * 2,
      fill: { color: i === idx ? AMBER : "28474C" },
      line: { type: "none" },
    });
  });
  return slide;
}

// ---------------------------------------------------------------------------
// Title slide
// ---------------------------------------------------------------------------

{
  const slide = pres.addSlide({ masterName: "TITLE_SLIDE" });
  const logoW = 1.55,
    logoH = logoW * (943 / 1118);
  const cardW = logoW + 0.7,
    cardH = logoH + 0.5;
  slide.addShape(pres.ShapeType.roundRect, {
    x: (PW - cardW) / 2,
    y: 0.55,
    w: cardW,
    h: cardH,
    rectRadius: 0.1,
    fill: { color: WHITE },
    line: { type: "none" },
    shadow: freshShadow({ opacity: 0.3, blur: 14 }),
  });
  slide.addImage({
    path: path.join(FIG, "monash-logo-stacked.png"),
    x: (PW - logoW) / 2,
    y: 0.55 + (cardH - logoH) / 2,
    w: logoW,
    h: logoH,
  });

  slide.addText("MACHINE LEARNING FOR HAZARDOUS AIR QUALITY WARNING", {
    x: 1,
    y: 0.55 + cardH + 0.35,
    w: PW - 2,
    h: 0.4,
    fontFace: FONT,
    fontSize: 13,
    bold: true,
    color: AMBER,
    align: "center",
    charSpacing: 1.5,
  });
  slide.addText("Forecasting Hazardous Air Quality\nDays in Indian Cities", {
    x: 1,
    y: 0.55 + cardH + 0.75,
    w: PW - 2,
    h: 1.5,
    fontFace: FONT,
    fontSize: 34,
    bold: true,
    color: WHITE,
    align: "center",
    valign: "top",
    lineSpacingMultiple: 1.05,
  });
  slide.addText(
    [
      { text: "Jaykumar Vinodbhai Chauhan", options: { breakLine: true, fontSize: 18, color: WHITE } },
      { text: "Student ID: 34710280  ·  Supervisor: Dr Tianhai Tian", options: { breakLine: true, fontSize: 14, color: "B9D1D1" } },
    ],
    {
      x: 1,
      y: 5.3,
      w: PW - 2,
      h: 1.0,
      fontFace: FONT,
      align: "center",
      valign: "top",
      lineSpacingMultiple: 1.35,
    }
  );
  slide.addText("School of Mathematics, Monash University  ·  MTH5000 Masters Research Project  ·  November 2026", {
    x: 1,
    y: 6.85,
    w: PW - 2,
    h: 0.4,
    fontFace: FONT,
    fontSize: 11.5,
    color: "6E9093",
    align: "center",
  });
}

// ---------------------------------------------------------------------------
// Agenda
// ---------------------------------------------------------------------------

{
  const slide = pres.addSlide({ masterName: "AGENDA" });
  slide.addText("What We'll Cover", {
    x: MARGIN,
    y: 0.55,
    w: CONTENT_W,
    h: 0.8,
    fontFace: FONT,
    fontSize: 32,
    bold: true,
    color: NAVY,
  });
  const rowH = 0.98;
  const startY = 1.75;
  const badgeSize = 0.62;
  CHAPTERS.forEach((ch, i) => {
    const y = startY + i * rowH;
    slide.addImage({ path: path.join(ICON, `${ch.key}.png`), x: MARGIN, y: y + 0.05, w: badgeSize, h: badgeSize });
    slide.addText(`0${i + 1}`, {
      x: MARGIN + badgeSize + 0.25,
      y: y,
      w: 0.7,
      h: rowH - 0.1,
      fontFace: FONT,
      fontSize: 20,
      bold: true,
      color: AMBER_LIGHT,
      valign: "m",
    });
    slide.addText(ch.title, {
      x: MARGIN + badgeSize + 0.95,
      y: y,
      w: 4.0,
      h: rowH - 0.1,
      fontFace: FONT,
      fontSize: 18,
      bold: true,
      color: NAVY,
      valign: "m",
    });
    slide.addText(ch.desc, {
      x: MARGIN + badgeSize + 5.1,
      y: y,
      w: CONTENT_W - (badgeSize + 5.1),
      h: rowH - 0.1,
      fontFace: FONT,
      fontSize: 13.5,
      color: SLATE,
      valign: "m",
    });
    if (i < CHAPTERS.length - 1) {
      slide.addShape(pres.ShapeType.line, {
        x: MARGIN,
        y: y + rowH - 0.08,
        w: CONTENT_W,
        h: 0,
        line: { color: LINE, width: 0.75 },
      });
    }
  });
}

// ---------------------------------------------------------------------------
// 1. Introduction
// ---------------------------------------------------------------------------
pres.addSection({ title: "Introduction" });
addDividerSlide("Introduction", 0);

addContentSlide("Introduction", "Introduction", "Motivation", [
  "PM2.5 in Indian cities regularly reaches hazardous levels; sustained exposure raises cardiopulmonary and all-cause mortality",
  "A forecast only helps if it arrives before the hazardous day – same-day warnings are of limited use",
  "Daily PM2.5 has exploitable structure: day-to-day persistence, a strong annual cycle, dependence on recent conditions",
  "My own motivation: growing up in India, seasonal smog was ordinary life, not an abstract statistic",
]);

addContentSlide("Introduction", "Introduction", "Research Problem and Significance", [
  "Existing ML studies of Indian air quality report average error only – not decomposed by the operating point a warning uses",
  "Good average error can still mean a poor warning system, and the reverse also holds",
  "The approved proposal assumed a weekly cycle alongside the annual one – tested directly here, not carried over",
  "Significance: if the decision threshold dominates the model, the alarm budget is the more consequential design choice",
]);

{
  const slide = addFreeSlide("Introduction", "Introduction", "Objectives and Research Questions");
  slide.addText("OBJECTIVES", {
    x: MARGIN,
    y: 1.45,
    w: CONTENT_W,
    h: 0.35,
    fontFace: FONT,
    fontSize: 13,
    bold: true,
    color: AMBER,
    charSpacing: 1.2,
  });
  slide.addText(
    numberedParagraphs(
      [
        "Evaluate classical, ML and deep learning models 1–3 days ahead, under a leakage-tested protocol",
        "Compare forecast-then-threshold against direct classification",
        "Quantify skill as a warning system under a varying threshold",
      ],
      { fontSize: 15.5 }
    ),
    { x: MARGIN + 0.15, y: 1.85, w: CONTENT_W - 0.3, h: 1.8 }
  );
  slide.addText("RESEARCH QUESTIONS", {
    x: MARGIN,
    y: 3.65,
    w: CONTENT_W,
    h: 0.35,
    fontFace: FONT,
    fontSize: 13,
    bold: true,
    color: AMBER,
    charSpacing: 1.2,
  });
  slide.addText(
    numberedParagraphs(
      [
        "How accurately can PM2.5 be forecast 1–3 days ahead?",
        "Threshold a forecast, or classify the exceedance directly?",
        "What hit rate / false alarm rate trade-off does each give?",
      ],
      { fontSize: 15.5 }
    ),
    { x: MARGIN + 0.15, y: 4.05, w: CONTENT_W - 0.3, h: 1.8 }
  );
  slide.addShape(pres.ShapeType.roundRect, {
    x: MARGIN,
    y: 6.05,
    w: CONTENT_W,
    h: 0.75,
    rectRadius: 0.08,
    fill: { color: NAVY },
    line: { type: "none" },
  });
  slide.addText("Q3's answer turns out to dominate Q1 and Q2.", {
    x: MARGIN,
    y: 6.05,
    w: CONTENT_W,
    h: 0.75,
    fontFace: FONT,
    fontSize: 16,
    italic: true,
    color: WHITE,
    align: "center",
    valign: "m",
  });
}

// ---------------------------------------------------------------------------
// 2. Literature Review
// ---------------------------------------------------------------------------
pres.addSection({ title: "Literature Review" });
addDividerSlide("Literature Review", 1);

addContentSlide(
  "Literature Review",
  "Literature Review",
  "Classical and Machine Learning Methods",
  [
    "ARIMA (Box–Jenkins): differenced series, own past values/errors; order by an AIC grid (Hyndman & Khandakar, 2008); Fourier terms for complex seasonality (De Livera et al., 2011)",
    "ML lineage: ridge (Hoerl & Kennard, 1970); random forest = bagging (Breiman, 1996) + trees (Breiman et al., 2017) + decorrelation (Breiman, 2001); gradient boosting, additive and stagewise (Friedman, 2001)",
    "Competition evidence: flexible learners need not beat ARIMA on short series (M3/M4: Makridakis et al., 2018/2020); an LSTM lost to ARIMA head-to-head (Siami-Namini et al., 2018) – but gradient boosting won M5, where genuine exogenous structure existed (Makridakis et al., 2022)",
    "Takeaway: the deciding factor is exploitable structure, not “ML vs. classical” in the abstract – this project's single series sits closer to M4 than M5",
    "A single train-test split understates variability (Tashman, 2000; Hewamalage et al., 2023) – the motivation for rolling-origin evaluation",
  ],
  { fontSize: 14.5 }
);

addContentSlide(
  "Literature Review",
  "Literature Review",
  "Deep Learning: Why a GRU",
  [
    "MLP (Hornik et al., 1989): no sense of sequence order – needs the same hand-built lag table as the regression and tree models",
    "CNN (LeCun et al., 1998): fixed receptive field, ill-suited to an annual cycle already handed to every model as Fourier terms",
    "Transformer / TFT (Lim et al., 2021): large parameter counts tuned for datasets orders of magnitude bigger than ~3,000 observations",
    "Plain RNN: vanishing/exploding gradients over long sequences (Bengio et al., 1994)",
    "LSTM fixes this with 3 gates and a memory cell – more parameters than this dataset needs (Hochreiter & Schmidhuber, 1997)",
    "GRU (Cho et al., 2014): 2 gates, no memory cell, same gradient-flow property, smaller parameter count – the assumptions that best match this project's data",
  ],
  { fontSize: 14.5 }
);

addContentSlide(
  "Literature Review",
  "Literature Review",
  "Delhi Air Quality and the Research Gap",
  [
    "Delhi's emissions: traffic, industry, seasonal stubble burning (Guttikunda et al., 2014; Cusworth et al., 2018; Jethva et al., 2019)",
    "Prior Delhi PM2.5 ML studies (Masood & Ahmad, 2020; Singh & Srivastava, 2025) score accuracy only – none evaluates forecasts as a warning system with an explicit alarm budget",
    "Verification framework (Jolliffe & Stephenson, 2012): match measures to the decision – CSI (Schaefer, 1990); plain accuracy misleads on imbalanced events (He & Garcia, 2009; Saito & Rehmsmeier, 2015)",
    "Data quality literature on negative readings (Jiang et al., 2023) and missingness mirrors the two defects found here",
    "The gap: evaluate against an explicit alarm budget – Chapter 4 shows this changes which model wins",
  ],
  { fontSize: 15.5 }
);

// ---------------------------------------------------------------------------
// 3. Methodology
// ---------------------------------------------------------------------------
pres.addSection({ title: "Methodology" });
addDividerSlide("Methodology", 2);

{
  const slide = addFreeSlide("Methodology", "Methodology", "Data and Two Defects in the Source");
  const leftW = 7.3;
  slide.addText(
    bulletParagraphs(
      [
        "OpenAQ. Every CPCB station returns only ~18 months; only location 8118 (AirNow, a US diplomatic post) has the full decade – selected, with the limitation stated plainly",
        "Clipped ceiling: 1990 µg/m³ repeats identically on 3 unrelated dates – an instrument ceiling, not a reading",
        "Wrong coverage denominator: assumed 24 hourly readings, sensor was half-hourly 2016–2024. Recomputed: 1,085 of 3,467 days are below 75% true coverage, vs. 268 with no value at all",
      ],
      { fontSize: 14.5 }
    ),
    { x: MARGIN, y: 1.5, w: leftW, h: 5.4 }
  );
  const rightX = MARGIN + leftW + 0.3;
  const rightW = PW - MARGIN - rightX;
  const stats = [
    ["Period", "2016–2026"],
    ["Usable days", "3,093 (86.4%)"],
    ["Longest gap", "34 days"],
    ["Days above threshold", "920 (29.7%)"],
  ];
  let sy = 1.5;
  stats.forEach(([k, v]) => {
    slide.addText(k.toUpperCase(), {
      x: rightX,
      y: sy,
      w: rightW,
      h: 0.28,
      fontFace: FONT,
      fontSize: 10.5,
      bold: true,
      color: SLATE,
      charSpacing: 1,
    });
    slide.addText(v, {
      x: rightX,
      y: sy + 0.26,
      w: rightW,
      h: 0.4,
      fontFace: FONT,
      fontSize: 19,
      bold: true,
      color: NAVY,
    });
    sy += 0.78;
  });
  addImageCard(slide, path.join(FIG, "fig2_coverage.png"), rightX + rightW / 2, 5.6, rightW, 2.1);
}

{
  const slide = addFreeSlide("Methodology", "Methodology", "Seasonality: Testing, Not Assuming, a Weekly Cycle");
  const leftW = 7.1;
  slide.addText(
    bulletParagraphs(
      [
        "Proposal assumed a weekly cycle alongside the annual one – tested directly, three independent ways",
        "Periodogram: dominant periods near 358, 179, 61 days – the annual cycle and harmonics, nothing near 7",
        "ACF: lag 7 is 0.173, lag 6 is 0.179 – on the decay curve, not above it",
        "Day-of-week: ANOVA p=0.34; Kruskal-Wallis p=0.77",
        "No weekly cycle – consistent with a diplomatic enclave, not a roadside site. ARIMA carries annual Fourier terms only",
      ],
      { fontSize: 14.5 }
    ),
    { x: MARGIN, y: 1.5, w: leftW, h: 5.4 }
  );
  const rightX = MARGIN + leftW + 0.3;
  const rightW = PW - MARGIN - rightX;
  addImageCard(slide, path.join(FIG, "fig3_weekly.png"), rightX + rightW / 2, 4.3, rightW, 4.6);
}

addContentSlide("Methodology", "Methodology", "Features and Weather Covariates", [
  "One row per origin t, using only data up to day t: lags, rolling mean/SD/max, anomalies, exceedance frequency, calendar and annual Fourier terms, missingness flags",
  "Missing values are never imputed, except for the GRU, shown next",
  "Weather (meteostat): temperature, wind speed, pressure, precipitation, each with a lag and a 3-day rolling mean",
  "Third data defect: the weather archive ends 202 days before the PM2.5 series – a hard cutoff. Precipitation is only 54% complete and excluded from the GRU",
]);

{
  const slide = addFreeSlide("Methodology", "Methodology", "Classical Benchmark and Machine Learning Regressors");
  slide.addText(
    [
      { text: "ARIMA(1,1,1)", options: { bold: true } },
      { text: " with four pairs of annual Fourier terms, order by AIC (1892.5):" },
    ],
    { x: MARGIN, y: 1.5, w: CONTENT_W, h: 0.4, fontFace: FONT, fontSize: 15, color: INK }
  );
  slide.addShape(pres.ShapeType.roundRect, {
    x: MARGIN,
    y: 1.98,
    w: CONTENT_W,
    h: 1.0,
    rectRadius: 0.06,
    fill: { color: WHITE },
    line: { type: "none" },
    shadow: freshShadow(),
  });
  {
    const { w, h } = fitImage(path.join(EQ, "eq_arima-1.png"), 11.0, 0.7);
    slide.addImage({ path: path.join(EQ, "eq_arima-1.png"), x: PW / 2 - w / 2, y: 1.98 + (1.0 - h) / 2, w, h });
  }
  slide.addText("fitted on log(PM2.5); φ₁ = 0.581, θ₁ = −0.987.", {
    x: MARGIN,
    y: 3.1,
    w: CONTENT_W,
    h: 0.4,
    fontFace: FONT,
    fontSize: 14,
    color: SLATE,
  });
  slide.addText(
    [
      { text: "Three ML regressors", options: { bold: true } },
      { text: ", each fitted to level and change from origin:" },
    ],
    { x: MARGIN, y: 3.65, w: CONTENT_W, h: 0.4, fontFace: FONT, fontSize: 15, color: INK }
  );
  slide.addText(
    bulletParagraphs(
      [
        "Ridge: closed-form β̂ = (XᵀX + λI)⁻¹Xᵀy",
        "Random forest: bagged trees + random feature subset, which decorrelates trees and lowers the variance floor",
        "Gradient boosting: additive, tree per round corrects the residual; accepts missing values natively",
      ],
      { fontSize: 15 }
    ),
    { x: MARGIN, y: 4.1, w: CONTENT_W, h: 2.5 }
  );
}

{
  const slide = addFreeSlide("Methodology", "Methodology", "The Gated Recurrent Unit");
  const leftW = 5.9;
  slide.addShape(pres.ShapeType.roundRect, {
    x: MARGIN,
    y: 1.5,
    w: leftW,
    h: 4.4,
    rectRadius: 0.08,
    fill: { color: WHITE },
    line: { type: "none" },
    shadow: freshShadow(),
  });
  {
    const { w, h } = fitImage(path.join(EQ, "eq_gru-1.png"), leftW - 0.6, 4.4 - 0.6);
    slide.addImage({
      path: path.join(EQ, "eq_gru-1.png"),
      x: MARGIN + (leftW - w) / 2,
      y: 1.5 + (4.4 - h) / 2,
      w,
      h,
    });
  }
  const rightX = MARGIN + leftW + 0.4;
  const rightW = PW - MARGIN - rightX;
  slide.addText(
    bulletParagraphs(
      [
        "H=24 hidden units, 30-day window",
        "6 channels (10 with weather): log-concentration, missingness flag, Fourier pairs (K=2 vs. ARIMA's K=4)",
        "Gaps forward-filled, missingness flagged",
        "Adam, MAE loss, early stopping",
        "10 seeds – not bit-reproducible at a fixed seed; every result is a range",
      ],
      { fontSize: 14.5 }
    ),
    { x: rightX, y: 1.5, w: rightW, h: 5.4 }
  );
}

addContentSlide("Methodology", "Methodology", "Rolling-Origin Evaluation and Warning-System Measures", [
  "2,303 origins, Nov 2019–Aug 2026, refit every 90 days (180 for the GRU). At origin t, only data up to day t is used – enforced by construction, verified by a corruption test",
  "Accuracy: rMAE against persistence (1.000 = persistence) and MASE, per horizon",
  "Warning system: hit rate, false alarm rate, precision, CSI, alarms per year – plain accuracy is never reported",
  "Diebold-Mariano test (HLN small-sample correction): GRU vs. ARIMA per seed, and ARIMA vs. each ML regressor",
]);

// ---------------------------------------------------------------------------
// 4. Results
// ---------------------------------------------------------------------------
pres.addSection({ title: "Results" });
addDividerSlide("Results", 3);

{
  const slide = addFreeSlide("Results", "Results", "Forecast Accuracy (RQ1)");
  modernTable(
    slide,
    [
      ["Model", "h=1", "h=2", "h=3"],
      ["GRU, range over 10 seeds", "0.910–0.939", "0.878–0.906", "0.831–0.879"],
      [
        "ARIMA(1,1,1) + Fourier",
        { t: "0.940", bold: true },
        { t: "0.883", bold: true },
        { t: "0.832", bold: true },
      ],
      ["Best ML regressor (GBM, change)", "0.983", "0.937", "0.878"],
      ["Persistence", "1.000", "1.000", "1.000"],
    ],
    { y: 1.55, w: CONTENT_W, fontSize: 13, colW: [5.2, 2.344, 2.344, 2.345] }
  );
  addImageCard(slide, path.join(FIG, "fig6_accuracy.png"), PW / 2, 5.2, 6.6, 2.1);
  addStat(slide, PW - 1.55, 4.1, "15/15", "DM pairings favour\nARIMA over every ML\nregressor", { w: 2.4, valueSize: 32 });
  slide.addText(
    "GRU wins clearly at h=1; ARIMA wins or ties beyond it (h=3: 0.831 vs. 0.832).",
    { x: MARGIN, y: 6.75, w: CONTENT_W - 2.7, h: 0.6, fontFace: FONT, fontSize: 13, color: SLATE }
  );
}

addContentSlide("Results", "Results", "Does Weather Change the Answer?", [
  "Gradient boosting improves at every horizon (by 8.2 / 2.0 / 2.9 points of rMAE); the random forest worsens 5.3 points at h=3 – no single story for every model",
  "GRU + weather: wins clearly at h=1 (7/10 seeds now significant, up from 4/10); h=2 becomes a genuine 3-way split; h=3 is more often a loss than a win (5 of 10)",
  "Doubling the seed count (5→10) is what surfaced this – under five seeds alone, h=2 and h=3 had looked like wins",
  "Carried through the threshold: at most 1.2 points of extra hit rate at any budget – a materially more accurate forecaster still does not escape the alarm-budget ceiling",
]);

{
  const slide = addFreeSlide("Results", "Results", "Two Arms of the Same Question (RQ2)");
  const leftW = 6.5;
  addStat(slide, MARGIN + leftW / 2 - 1.0, 1.55, "21", "vs. 11 wins", { w: 1.7, valueSize: 46 });
  slide.addText("36 comparisons (3 pairs × 3 horizons × 4 budgets): forecast-then-threshold wins 21, classifier 11, 4 ties", {
    x: MARGIN + leftW / 2 + 0.75,
    y: 1.68,
    w: leftW / 2 - 0.3,
    h: 0.95,
    fontFace: FONT,
    fontSize: 12.5,
    color: SLATE,
    valign: "m",
  });
  slide.addText(
    bulletParagraphs(
      [
        "Forecast-then-threshold vs. direct classification, matched by base algorithm",
        "Median gap 0.011 hit rate, max 0.056 – real but modest",
        "Edge narrows as budget loosens: 8/9 at budget 40, but the classifier overtakes it (6/9) at budget 100",
        "Preferred anyway: a forecast can be rethresholded for any future policy; a classifier is welded to its training threshold",
      ],
      { fontSize: 14 }
    ),
    { x: MARGIN, y: 2.85, w: leftW, h: 4.0 }
  );
  const rightX = MARGIN + leftW + 0.3;
  const rightW = PW - MARGIN - rightX;
  addImageCard(slide, path.join(FIG, "fig7_arms.png"), rightX + rightW / 2, 4.3, rightW, 4.6);
}

{
  const slide = addFreeSlide("Results", "Results", "The Decision Threshold (RQ3) – the Central Result");
  addStat(slide, MARGIN + 1.5, 1.55, "50 pts", "hit rate moved by\nbudget 40→100 alarms/yr", {
    w: 2.9,
    valueSize: 44,
    valueColor: AMBER,
  });
  addStat(slide, MARGIN + 4.9, 1.55, "~5 pts", "hit rate moved by\nswitching the model", { w: 2.9, valueSize: 44 });
  modernTable(
    slide,
    [
      ["Alarms per year", "40", "60", "80", "100"],
      ["Best hit rate, h=1", "0.379", "0.567", "0.735", "0.881"],
      ["Best hit rate, h=2", "0.366", "0.538", "0.700", "0.840"],
      ["Best hit rate, h=3", "0.359", "0.533", "0.685", "0.827"],
    ],
    {
      x: MARGIN + 6.1,
      y: 1.55,
      w: PW - MARGIN - (MARGIN + 6.1),
      fontSize: 11.5,
      colW: [2.133, 1.0, 1.0, 1.0, 1.0],
    }
  );
  addImageCard(slide, path.join(FIG, "fig5_warning.png"), PW / 2, 5.25, 5.6, 3.0);
  slide.addText("At h=3, budget 40, plain persistence is the best model in the study.", {
    x: MARGIN,
    y: 6.95,
    w: CONTENT_W,
    h: 0.4,
    fontFace: FONT,
    fontSize: 13,
    color: SLATE,
    align: "center",
  });
}

// ---------------------------------------------------------------------------
// 5. Discussion
// ---------------------------------------------------------------------------
pres.addSection({ title: "Discussion" });
addDividerSlide("Discussion", 4);

addContentSlide("Discussion", "Discussion", "The Operational Question Dominates the Modelling Question", [
  "Alarm budget moves the hit rate ~50 points; switching the model at fixed budget moves it ~5",
  "At h=3, loosest budget: climatology alone (0.816) comes within a hundredth of the best fitted model (0.827)",
  "Not an argument against modelling – ARIMA and the GRU both beat persistence, and a better forecast narrows the useful range of thresholds",
  "The leverage sits with the policy instrument, the alarm budget, not the model behind it. Recommendation: fix the budget with the health authority first; treat the model as a secondary refinement",
]);

addContentSlide("Discussion", "Discussion", "How Large Is a Difference Between Models?", [
  "Noise floor: identical pipeline, two machines, moves tree models up to 0.004; the GRU moves 0.028–0.048 across seeds – almost as much when the same seed is simply rerun",
  "Several table gaps sit at or below that floor (e.g. 0.878 vs. 0.879 at h=3) and cannot be confidently ordered",
  "Diebold-Mariano is more conservative still: only 4/10 GRU seeds reach p<0.05 at h=1 (the noise floor credits 8/10); 0/10 at h=2; 1/10 at h=3",
  "Those seed counts are themselves small-sample proportions: a 95% Wilson interval on “4 of 10” at h=1 runs 0.17 to 0.69",
]);

addContentSlide("Discussion", "Discussion", "Limitations I: Scope and Sensitivity", [
  "Single station, single city: an AirNow diplomatic-post monitor, not the CPCB network; Delhi only, chosen for data history",
  "Cleaning threshold (1000 µg/m³) checked directly: restoring capped days barely moves ARIMA (0.940→0.935 at h=1) but hurts the ML suite more (ridge: 0.997→1.118) – the central finding strengthens",
  "Tree hyperparameters from a small grid, not an exhaustive search – a lower bound on what those models could achieve",
]);

addContentSlide("Discussion", "Discussion", "Limitations II: The GRU and Reproducibility", [
  "GRU architecture (H=24, 30-day window) fixed by inspection – a bounded check found a 45-day window scored 2.2 points better at h=3, untested at full ten-seed scale",
  "Fourier ablation: giving the GRU ARIMA's K=4 harmonics helps at every horizon, substantially at h=3 (3.96 points) – the network already gets a seasonal signal, just a coarser one",
  "GRU training is not bit-reproducible at a fixed seed – why the seed count was doubled from 5 to 10",
  "Weather is observed only, never forecast; boundary layer height is unavailable without a reanalysis product",
]);

// ---------------------------------------------------------------------------
// 6. Conclusion
// ---------------------------------------------------------------------------
pres.addSection({ title: "Conclusion" });
addDividerSlide("Conclusion", 5);

addContentSlide(
  "Conclusion",
  "Conclusion",
  "Summary and Main Conclusions",
  [
    "Forecast hazardous PM2.5 1–3 days ahead at one Delhi monitor; two real data defects corrected; the weekly-cycle assumption tested and rejected",
    "Spread across models at fixed budget: ~5 points. Spread across budgets, model fixed: ~50 points",
    "ARIMA beats every ML regressor at every horizon (DM-backed); the GRU is the one model that wins, only at h=1, reported as a range over ten seeds",
    "Weather narrows h=1 further but leaves h=2/h=3 a tie or more-often-loss; its gain buys little once thresholded",
    "Forecast-then-threshold beats direct classification 21 of 36 – real but modest, preferred also for rethresholdability",
    "Trying several methods, not defaulting to ARIMA, is what surfaced the h=1 GRU win and made the negative result credible",
  ],
  { fontSize: 14.5 }
);

{
  const slide = addFreeSlide("Conclusion", "Conclusion", "Future Work");
  slide.addText(
    numberedParagraphs(
      [
        "A genuine weather forecast, not the conditions already observed at the forecast origin",
        "Boundary layer height via a reanalysis product (e.g. ERA5)",
        "Refit the GRU with four Fourier harmonics under the full ten-seed rolling-origin evaluation",
        "A second, independent station – ideally CPCB – once its record lengthens",
      ],
      { fontSize: 16 }
    ),
    { x: MARGIN + 0.15, y: 1.65, w: CONTENT_W - 0.3, h: 3.3 }
  );
  slide.addShape(pres.ShapeType.roundRect, {
    x: MARGIN,
    y: 5.5,
    w: CONTENT_W,
    h: 0.95,
    rectRadius: 0.08,
    fill: { color: NAVY },
    line: { type: "none" },
  });
  slide.addText(
    "Design the warning system around its alarm budget; treat the forecasting model as a secondary refinement.",
    {
      x: MARGIN + 0.3,
      y: 5.5,
      w: CONTENT_W - 0.6,
      h: 0.95,
      fontFace: FONT,
      fontSize: 15,
      italic: true,
      color: WHITE,
      align: "center",
      valign: "m",
    }
  );
}

{
  const slide = pres.addSlide({ masterName: "CLOSING" });
  const badgeSize = 1.3;
  slide.addImage({
    path: path.join(ICON, "introduction.png"),
    x: PW / 2 - badgeSize / 2,
    y: 2.3,
    w: badgeSize,
    h: badgeSize,
  });
  slide.addText("Questions?", {
    x: 1,
    y: 3.85,
    w: PW - 2,
    h: 1.0,
    fontFace: FONT,
    fontSize: 40,
    bold: true,
    color: WHITE,
    align: "center",
  });
}

// ---------------------------------------------------------------------------
pres.writeFile({ fileName: OUT }).then(async () => {
  await applyTheme(OUT, THEME);
  console.log("Wrote", OUT);
});
