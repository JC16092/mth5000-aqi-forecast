# Oral presentation, fresh build (MTH5000, first week of November)

A clean-slate deck built directly from `report/main.pdf` (77 pages, 14 tables, 13 figures, after Dr Tian's
review). It does not reuse anything from `presentation/`, which holds the earlier 33-slide deck and is left
untouched (see "Open question" below).

- **`MTH5000_oral_presentation.pptx`** -- the deck. 28 slides for the talk plus 5 backup slides (B1 to B5).
- **`MTH5000_oral_presentation.pdf`** -- a LibreOffice export of the same deck, for use as a fallback if
  PowerPoint is unavailable in the room. It is rendered with Carlito in place of Calibri, so check line
  breaks if you regenerate it.

## Timing

Speaker notes on every slide start with a time budget and a running total, e.g.
`[Slide 14 | about 1.5 min | running total 18 min]`. The 28 talk slides come to **34 minutes**, inside the
30 to 40 minute slot. If questions are taken inside the slot rather than after it, the easiest cuts are
slide 9 (model suite), slide 20 (weather through the threshold) and slide 23 (trade-off curves). The notes
are talking points, not a script.

## Structure

| Slides | Section | Content |
|---|---|---|
| 1 to 3 | Motivation | Title, why it matters, the three research questions with their answers |
| 4 to 8 | Data | Station choice, the two data defects, the series, no weekly cycle, annual cycle and ARIMA |
| 9 to 13 | Methods | Model suite, ML regressors, the three networks, rolling-origin evaluation, measures |
| 14 to 23 | Results | RQ1 table, forecast figure, seed ranges, significance, the two tested arguments, weather, RQ2, RQ3, trade-off curves |
| 24 to 25 | Discussion | Robustness checks, limitations |
| 26 to 28 | Conclusion | Research-question answers, recommendation and future work, questions |
| B1 to B5 | Backup | ARIMA order search, Diebold-Mariano tables, GRU sensitivity, coefficient stability and architecture checks, RQ2 at all horizons |

## Provenance

- Every number is read from the compiled `report/main.pdf`, and each table slide names the report table it
  comes from. After the last build, every numeric token in the slides and notes was checked against the
  report text; the only two not found verbatim were `3,579` (the report prints `3579`) and `4,000` (the
  report writes "four thousand").
- Figures are the report's own, extracted from the PDF rather than redrawn, so they carry the report's
  recoloured palette. The deck palette (Monash blue `#006CAB`, navy, and the vermillion `#D55E00` used in
  the report for called-out points) follows them.
- The one derived claim is "5 of 5 ML regressors behind ARIMA at every horizon", read off Table 4.1 row by
  row. The RQ2 slide shades the better arm computed from the table values, with exact ties left unshaded.

## Build

```
./extract_assets.sh            # figures and logos from report/main.pdf into assets/ (PNGs are gitignored)
cd src && npm install          # first time only
node build_deck.js             # writes ../MTH5000_oral_presentation.pptx
soffice --headless --convert-to pdf --outdir .. ../MTH5000_oral_presentation.pptx   # optional PDF fallback
```

`assets/` is rebuilt byte-for-byte by `extract_assets.sh` (checked). The deck is typeset in Calibri.
Coordinates in `build_deck.js` are inches on a 13.333 by 7.5 slide; the per-slide time budget is the `MINS`
array at the top.

## Open question

`presentation/` was described as cleared for a fresh start, but on `main` it still contains the earlier deck
(`slides_v2.pptx`, Beamer `slides.tex`/`slides.pdf`, `pptx_src/`, `README.md`). It was left alone. Delete it
once this deck is the one you are keeping.
