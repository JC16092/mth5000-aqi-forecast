# Oral presentation, fresh build (MTH5000, first week of November)

A clean-slate deck built from `report/main.pdf` (77 pages, 14 tables, 13 figures, after Dr Tian's review).
It reuses nothing from `presentation/`, which still holds the earlier 33-slide deck and was left untouched
(see "Open question").

| File | What it is |
|---|---|
| `MTH5000_oral_presentation.pptx` | The deck: 29 talk slides plus 9 backup slides (B1 to B9). |
| `MTH5000_oral_presentation.pdf` | A LibreOffice export, as a fallback if PowerPoint is unavailable in the room. Rendered with Carlito in place of Calibri, so check line breaks if you regenerate it. |
| `PRESENTER_GUIDE.md` | Timing checkpoints, delivery advice, and every slide's cues. Generated from the same source as the speaker notes. |

## How the deck is built to be presented

- **One message per slide**, stated as the slide title and again in a consistent "TAKEAWAY" bar. Detail
  lives in the speaker notes and in the backups, not on the slide.
- **A spine**: the alarm budget moves hit rate by about 50 points, the model by about 5. The title slide
  states it, the roadmap asks the audience to hold it in mind, the results earn it, the discussion defends
  it, the conclusion repeats it.
- **Navigation**: a roadmap slide with minutes per section, and a six-segment progress tracker on every slide.
- **Slide-grade figures**, drawn at the size they are shown so a 14 pt label is a 14 pt label. They are drawn
  from the report's own data and palette. Three are drawn rather than quoted: Table 4.1 as a dot plot, the
  ten-seed spreads, and the central budget curves (the curves reproduce Table 4.7 exactly; the script prints
  the check).
- **Consistent identity system**: Monash blue, navy for ARIMA, vermillion only for a called-out point, as in
  the report.
- **Speaker notes are cues, not scripts**: SAY, POINT TO, IF ASKED, TRANSITION, with a running clock.
- **Rehearsal and defence material**: a Q&A cue sheet (B8, B9) for the questions an examiner is likely to
  ask, including the one a sharp examiner will ask about the central result (a bigger budget raises the hit
  rate by construction, so the finding is the size of the two effects, not that one exists).

## Timing

The 29 talk slides total **32.5 minutes**, inside the 30 to 40 minute slot. If questions are taken inside
the slot, `PRESENTER_GUIDE.md` names what to cut first.

## Provenance

- Every number is read from the compiled report. After the last build, every numeric token in the slides and
  notes was checked against the report text. Not found verbatim: `3,579` (the report prints `3579`), `4,000`
  (the report writes "four thousand"), and the section minutes on the roadmap (the talk's own timing).
- Derived, not quoted: "5 of 5 ML regressors behind ARIMA at every horizon" (read off Table 4.1 row by row);
  the ten-seed spreads (high minus low from Table 4.1); the shaded better arm on the RQ2 slide (computed from
  Table 4.6, ties unshaded).
- Backup slides B2 to B6 reuse the report's own tables and figures.

## Build

```
./extract_assets.sh                                   # report figures and logos from report/main.pdf into assets/
python src/make_slide_figures.py                      # slide figures into assets_slides/ (needs the report's Python environment)
cd src && npm install && node build_deck.js           # writes the .pptx and PRESENTER_GUIDE.md
soffice --headless --convert-to pdf --outdir .. ../MTH5000_oral_presentation.pptx   # optional PDF fallback
```

PNGs are gitignored, as for `report/figures/`, so the two asset folders are rebuilt rather than committed.
The deck is typeset in Calibri. Coordinates in `build_deck.js` are inches on a 13.333 by 7.5 slide; the
per-slide minutes are the `MINS` array at the top.

## Open question

`presentation/` was described as cleared for a fresh start, but on `main` it still holds the earlier deck
(`slides_v2.pptx`, the Beamer files, `pptx_src/`, `README.md`). It was left alone. Delete it once this deck
is the one you are keeping.
