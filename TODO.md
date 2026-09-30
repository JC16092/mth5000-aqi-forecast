# MTH5000 Report — To-Do Checklist

Built from `MTH5000_October_Timesheet.pdf`. Most of weeks 1 to 4 got done in
a single session on 30 September instead of spread across the month, so this
checklist reflects what's actually true rather than the original day-by-day
spread. Tick items off as you go; this file is yours to edit.

**Deadline: no longer fixed to 19–22 October. Runway to roughly the first
week of November 2026.**

---

## Found and fixed after first calling the report "done" (30 Sep, later same day)

- [x] Table 4's GRU row was silently seed-0-only (`forecasts_with_gru.csv` is
      exactly seed 0). Reran the threshold sweep across all 5 seeds and Table 4
      now reports GRU as a range, matching Table 3's own rule. Spread is small
      (0.006–0.014), reinforcing rather than complicating the main finding.
- [ ] **Not fixed, flagged instead:** Table 4's top "Best hit rate" summary
      rows still use seed 0's curve, about 0.002 off the true 5-seed best.
      Below this project's own noise floor; a judgement call, not an oversight.
- [x] Full audit of every hand-typed number in `main.tex` against its
      source. Found and fixed two real errors: the coverage-defect sentence
      in Data (wrong denominator, 1,085 was over 3,467 rows not 3,199), and
      the Fourier-ablation claim in Results (traced to a stale week-2 run;
      correct current figure is 3.3/5.8 points, not 4.5/10). Confirmed
      correct on recomputation: Tables 1–2, the periodogram, ACF lags 6/7/8,
      the day-of-week ANOVA/Kruskal-Wallis tests, the Fourier R² of 0.69,
      and the GRU seed-spread numbers. Also fixed a long-standing overfull
      hbox (Table 3 needed footnotesize). Report now compiles with zero
      warnings.

---

## Week 1 — sensitivity check and Discussion 6.1

- [x] Re-read PROJECT_STATUS.md and BLUEPRINT.md, confirm the venv still works
- [x] Sensitivity rerun without `--max-value 1000`
- [x] Compare sensitivity result against the reported numbers
- [x] Draft Discussion §6.1, the operational-question argument

## Week 2 — Limitations, Conclusion, literature area 1

- [x] Limitations: single station (diplomatic monitor, not CPCB)
- [x] Limitations: single city
- [x] Limitations: the 1000 cleaning threshold (uses the sensitivity numbers)
- [x] Limitations: small hyperparameter grids
- [x] Limitations: no meteorological covariates
- [x] Draft Conclusion
- [x] Revise Discussion + Conclusion together, recompile
- [x] Literature area 1: Delhi/India ML forecasting (Masood & Ahmad 2020,
      Singh & Srivastava 2025)

## Week 3 — literature review core

- [x] Literature area 2: ML vs classical on limited data (Makridakis et al.
      2020, the M4 competition)
- [x] Literature area 3: warning system verification (Jolliffe & Stephenson
      2012)
- [x] Literature area 4: negative/invalid monitor readings (Jiang et al. 2023)
- [x] Write the literature prose, all four areas
- [x] Bibliography (`refs.bib`) set up, bibtex compiling via tectonic
- [ ] **Read the four new citations yourself and confirm the
      characterisation of each is fair** — I only verified them via CrossRef
      (they're real, correctly cited), not full-text. This is the one
      Week 3 item still open.

## Week 4 — introduction, abstract, full pass

- [x] Personal motivation paragraph, pulled from the approved proposal into
      the Introduction
- [ ] Full read-through of `report/main.tex` end to end (written across
      several sessions spanning weeks — check the voice is consistent and
      nothing repeats)
- [ ] Fix anything found in the read-through; confirm tables/figures still
      match after the sensitivity rerun
- [x] Draft Abstract (leads with the alarm-budget finding, ~230 words)
- [ ] Full compile and proofread on paper, formatting against the style
      rules one more time

## Week 5 — final polish and margin

- [ ] Close out anything left from the proofread
- [ ] Send the complete draft to Dr Tian
- [ ] Buffer / incorporate any quick feedback
- [ ] Buffer / rest

## Optional, not a gap

- [ ] Expand Results §5.2 ("Two arms of the same question") with more
      classifier detail from `threshold_sweep.csv` — currently thinner than
      the rest of Results but not incomplete

---

## Status snapshot (30 September 2026)

`report/main.tex` compiles to 14 pages. Every section is written: Abstract,
Introduction, Literature, Data, Methodology, Results, Discussion,
Limitations, Conclusion, Reproducibility. Everything above is committed to
git. What's left is entirely your own review pass — reading citations,
proofreading, and deciding when to send it to Dr Tian — not more writing.
