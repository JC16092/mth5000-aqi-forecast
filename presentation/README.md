# Oral presentation (MTH5000, first week of November)

Kept separate from `report/` but sharing everything else in this project:
the same `data/`, the same `step*.py` / `evaluation.py` / `significance.py`
scripts, the same figures, and the same
[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) changelog.

- **`slides_v2.pptx`** -- editable PowerPoint, **the current primary
  deliverable and the only deck that is up to date**. Built by
  `pptx_src/build_deck_v2.js`. This is the "threshold line" design (see
  below). Tracked, the same way `report/main.pdf` is.
- **`slides.tex`** / **`slides.pdf`** -- the original Beamer version.
  Tracked, but **stale**: it is at the pre-LSTM 31-slide state and still
  carries the "GRU chosen because fewer parameters" justification that
  the report has since retracted (see "Kept in sync with the report"
  below). Do not present from it without bringing it forward first.
- **`slides.pptx`** -- the earlier teal/coral deck, regenerable with
  `pptx_src/build_deck.js`. Deliberately **not** tracked: it is
  superseded and carries the same retracted justification, and its build
  script is committed, so there is nothing to preserve by committing the
  output. Likewise `slides_moda.pptx`, a watermarked export kept only as
  a local record of the connector attempt.

## Design

The user explicitly rejected a first pptx pass that carried over the
report's plain-academic style ("i dont like it its so simple looking") and
asked for something "bold and modern." A second pass built a navy/amber
palette on that direction; the user then asked to "change the theme," and
on being offered concrete alternatives picked deep teal + coral over navy/
amber. The deck now uses that content-informed palette -- deep atmospheric
teal-charcoal (`#16343A`, dominant) plus a warm coral accent (`#E35D45`),
still evoking the AQI warning-system subject rather than a generic blue,
just a cooler, less literally "hazard sign" reading than the amber
version -- with dark title/section-divider/closing slides sandwiching
light content slides, icon badges (one per chapter, via `react-icons` +
`sharp`) repeated across the agenda and each divider as the deck's one
visual motif, big stat callouts on the handful of slides carrying the
report's own headline numbers, and card-styled figures. No accent
lines/stripes anywhere (an explicit anti-pattern in the `pptx` skill's own
guidance) -- separation is by whitespace, card surfaces, and the one
accent color, used sparingly. Report figures (`report/figures/*.png`)
stay monochrome, reused as-is rather than recolored or rebuilt natively,
since traceability to the report's own output matters more than palette
consistency for the one element that *is* the evidence.

## The "threshold line" design (`build_deck_v2.js`)

The teal/coral palette above was still judged too plain ("still not
satisfied ... I want something unique that can impress my proffs"). The
redesign makes the cover carry data rather than decoration: 365 bars of
peak daily PM2.5 read straight from `data/delhi_clean.csv`, drawn on a
square-root scale, with the 121 ug/m3 health threshold as a live rule
running across them -- bars above it coral, below it teal. That same
skyline motif recurs, dimmed, on every section divider and on the closing
slide, so the deck's one ornament is the dataset itself.

Two things to know before editing it:

**The deck is typeset in Calibri, not Inter.** The design was drawn in
Inter, but Inter is not installed here and pptxgenjs cannot embed a font,
so naming it would have silently substituted something unpredictable on
the presentation-room machine. Calibri runs noticeably taller per line, so
**any text box whose height was computed for Inter will overflow** --
assume roughly 38px per line at `fontSize: PT(22)`, not the ~33px a
1.5 multiplier suggests. Six blocks had to be refitted for exactly this
reason. If you change any body copy, re-render and look at the slide.

**Backgrounds and the white logo are pre-rendered PNGs.** pptxgenjs has no
radial-gradient support and no image `tint`, so `pptx_src/gen_bg.py`
writes `bg/bg_cover.png` and `bg/bg_dark.png` with PIL, and recolours the
Monash logo white while preserving its alpha. Rerun it if the palette
changes; the deck will not regenerate them for you.

Coordinates are written in a 1920x1080 design space and converted at the
call site: `IN(px) = px / 144` for inches, `PT(px) = px / 2` for points.

### Kept in sync with the report

The report and the deck are built in separate chats against one shared
folder, so the deck can silently fall behind. It did once, when the
second-review pass added an LSTM, a GRU optimiser check, a small
transformer and a KAN-LSTM hybrid. Two lessons from catching up:

- **Re-derive from `report/tables/*.tex` and `report/main.tex`, not from
  a summary of what changed.** The summary of that pass was accurate but
  flattened the ten/eleven distinction above; reading the tables directly
  is what surfaced it.
- **A falsified justification is the dangerous kind of staleness**, worse
  than a stale number, because nothing about the slide looks wrong. The
  deck claimed the LSTM was ruled out for having too many parameters long
  after the project had fitted one and watched it win. Any slide that
  gives a *reason* for a modelling choice needs re-reading whenever the
  evidence for that choice changes, not just the slides carrying numbers.

### On the connectors (recorded so it isn't re-tried)

Both configured PowerPoint connectors were tried for this redesign before
building locally. **PowerPoint by Anthropic** exposes no parameter for
colour, font, shape, background or chart -- it builds correct plain decks
and structurally cannot express a visual design. **Moda** can, and the
design was in fact built there first, but its export stamps a `moda.app`
watermark on every slide on the free plan. Stripping that watermark, or
reassembling the deck from clean canvas screenshots to dodge the paid
export, were both declined -- the second would also have turned an
editable deck into pictures of a deck. The design was rebuilt locally
instead.

## Build

PowerPoint (primary):

```
cd pptx_src
npm install              # first time only
node generate_icons.js   # writes pptx_src/icons/*.png (only if they're missing or an icon changes)
python3 gen_bg.py        # writes pptx_src/bg/*.png (only if the palette changes)
node build_deck_v2.js    # writes ../slides_v2.pptx   <- current deliverable
node build_deck.js       # writes ../slides.pptx      <- superseded
```

Beamer (secondary):

```
tectonic slides.tex
```

## Status

`slides_v2.pptx` is filled in: title slide, agenda, and 25 content
slides covering all six chapters of `report/main.tex` (3 Introduction, 3
Literature Review, 6 Methodology, 5 Results, 4 Discussion, 2 Conclusion),
plus a section-divider slide before each chapter. 32 slides total.
(`slides.pptx` and `slides.tex` are at the earlier 31-slide state and
predate the LSTM work -- see the note below.)

**A counting trap worth knowing before editing any model count.** The
project fits **eleven** specifications, but the decision-threshold sweep
covers **ten** of them. The report is deliberately precise about which
number goes where, and the deck follows it: the Methodology agenda line
and chapter divider say eleven models, while the central-result slide and
the Q3 answer say ten specifications. They are not inconsistent and
should not be "fixed" to match each other. Every
number traces to the same table or script result the report uses (read
directly from `report/tables/*.tex`, never retyped from memory); every
citation was cross-checked against how it actually renders in
`report/main.pdf`, not against memory of the report's prose -- that check
caught three wrong citations (a reintroduced CART year, a fabricated
co-author, a wrong author count) before the deck was considered done.
Every figure is the report's own, reused directly rather than recomputed.
Validated (`scripts/office/validate.py`), content-checked (`markitdown`),
and visually QA'd page-by-page by rendering to images, not just by a
clean compile/validate log or an un-inspected "looks designed" assumption.

`pptx_src/eq/` holds the three equation images (ARIMA+Fourier, ridge
closed-form, the GRU's four gate equations), typeset from LaTeX
(`mathptmx`, matching the report's own math font) rather than built as
PowerPoint text, since PowerPoint has no native equation-typesetting good
enough to match the report. Their `.tex` sources are kept alongside the
`.png`s so they can be regenerated (`tectonic eq_*.tex && pdftoppm -png -r
400 eq_*.pdf eq_*`) if the underlying formulas ever change.

`pptx_src/icons/` holds the six chapter-badge PNGs (coral circle + white
Font Awesome icon) generated by `pptx_src/generate_icons.js`. Regenerate
them if an icon choice changes; they aren't hand-edited.

## Conventions carried over from `report/`

- No number goes on a slide typed by hand -- if it's a result, it traces to
  the same script/table the report uses.
- Figures are **not** duplicated into this folder. Both decks resolve
  `fig1_series.png` etc. straight from `../report/figures/`.

## Two pptxgenjs gotchas worth remembering

**Bulleted lines must be a single text run.** Confirmed by direct testing
(not documented in pptxgenjs's own docs): a run with `options.bullet` set
always starts a new `<a:p>`, and any other run sharing what should be the
same bulleted paragraph still gets its own default (bullet-less) `<a:pPr>`
emitted -- multiple `<a:pPr>` blocks end up inside one `<a:p>`, and the
bullet and hanging indent are lost in both LibreOffice and (per the
malformed-XML pattern this produces) likely PowerPoint too. `build_deck.js`
therefore builds every bulleted line as one run; a whole bullet may still
be bold or italic (`{t, bold}` / `{t, italic}` in `bulletParagraphs()`),
just never mixed with plain text in the same line.

**Don't pre-size a background card to a table's estimated height.** A
table's actual rendered row height depends on font metrics and whether any
cell wraps, neither easy to predict in advance -- an early version of the
"bold and modern" redesign drew a white rounded-rect card sized from a
guessed per-row height behind each table, and on two Results slides the
real table came out taller than the guess, so the card (and whatever sat
below it, positioned assuming the card's guessed bottom edge) visibly
overlapped the real table. Fixed by dropping the background card for
tables entirely -- the per-cell fill (`modernTable()`'s navy header / white
body) already gives a clean surface without needing a separate shape to
track its size -- and by giving `addTable`'s `colW` explicit values that
sum to its own `w` rather than leaving column widths to guesswork (a
mismatch there was silently letting one table render wider than the box
it was supposed to fit, the original source of the same visual collision).
Image cards don't have this problem: their size comes from the actual
image's pixel dimensions via PIL, not a row-count guess, so they stay
exact.
