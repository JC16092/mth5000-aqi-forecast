# Oral presentation (MTH5000, first week of November)

Beamer slide deck, kept separate from `report/` but sharing everything else
in this project: the same `data/`, the same `step*.py` / `evaluation.py` /
`significance.py` scripts, the same figures, and the same
[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md) changelog.

## Build

```
tectonic slides.tex
```

## Status

`slides.tex` is filled in: title slide, outline, and 24 content frames
covering all six chapters of `report/main.tex` (3 Introduction, 3
Literature Review, 6 Methodology, 5 Results, 3 Discussion, 2 Conclusion),
plus the per-section outline frames `\AtBeginSection` inserts
automatically. 31 pages total. Every number traces to the same table or
script result the report uses (read directly from `report/tables/*.tex`,
never retyped from memory); every figure is the report's own, reused via
`\graphicspath` below. Compiles clean with `tectonic`; verified
page-by-page by rendering to PNG, not just by a clean compile log.

## Conventions carried over from `report/`

- No number goes on a slide typed by hand -- if it's a result, it traces to
  the same script/table the report uses.
- No colour, no decorative theme -- plain academic style, matching the
  report.
- Figures are **not** duplicated into this folder. `slides.tex` sets
  `\graphicspath` to `../report/figures/` and `../`, so
  `\includegraphics{fig1_series}` or `\includegraphics{monash-logo-stacked}`
  resolve straight to the existing files. Add a presentation-only figure
  under `presentation/figures/` only if one is actually needed.
