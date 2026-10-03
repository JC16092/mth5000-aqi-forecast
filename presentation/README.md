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

`slides.tex` is a skeleton: title slide, outline, and one placeholder frame
per chapter of `report/main.tex` (Introduction, Literature Review,
Methodology, Results, Discussion, Conclusion). Each frame's italic note
names the report section(s) to pull from. No content, numbers, or figures
have been filled in yet.

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
