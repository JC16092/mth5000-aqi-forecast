# MTH5000 Report — To-Do Checklist

Built from `MTH5000_October_Timesheet.pdf`. Most of weeks 1 to 4 got done in
a single session on 30 September instead of spread across the month, so this
checklist reflects what's actually true rather than the original day-by-day
spread. Tick items off as you go; this file is yours to edit.

**Deadline, confirmed by Dr Tian on 2 October: the last day of October 2026.**
Not early November — that was my own wrong assumption. ~4 weeks from now.

---

## Supersedes everything below: post-meeting pivot (2 October)

Dr Tian reviewed the 14-page draft. Verdict: correct but far too short for a
24-point mathematics capstone, specifically in Methodology. See
`PROJECT_STATUS.md`'s "Week 7, meeting with Dr Tian" section for the full
account. The checklist below this point (reading citations, proofreading,
the classifier-detail expansion) is now secondary to this:

- [x] **References: grow from 7 entries (~1/3 page) to at least 4 full pages.**
      Done: 40 entries, exactly 4 pages (pages 35-38 of 38). Every one found
      by real CrossRef search and DOI-verified before citing — this caught
      two wrong guessed DOIs that resolved to unrelated papers (Guttikunda
      et al. and Miller 1984) before they were used, and one candidate
      (Chung et al.'s GRU-vs-LSTM workshop paper) was dropped for having no
      real Crossref DOI. See PROJECT_STATUS.md's "References grown from 11
      to 40 entries" section for exactly where each new citation was woven
      into the prose.
- [x] **Methodology: split explicitly into (i) Machine learning and
      (ii) Deep learning**, each covering the method family's general
      features/theory, then specifically how this project implemented it.
      Done same day as the meeting — see the checked items below.
- [x] **Add full mathematical detail throughout Methodology**: ridge
      regression's objective, the random forest splitting criterion,
      gradient boosting's functional gradient descent, ARIMA's AR/MA/I
      polynomial form with the Fourier terms written out, the GRU's full
      gate equations. Done same day — see below. Literature-lineage
      citations (bagging, CART, AdaBoost, XGBoost, backprop,
      vanishing-gradient) added to these same equations in the 2 October
      references session.
- [x] **Expand Literature Review** to also carry theoretical background on
      ML and deep learning as method families (mirrors the Methodology
      split above), not just the four application-area citations already
      there. Done same day — see below. Further deepened in the references
      session with the bagging/CART/AdaBoost lineage, the M3/M4/M5
      forecasting-competition thread, and the forecast-evaluation-
      methodology citations (Tashman, Hyndman & Koehler, Hewamalage et al.).
- [x] Decide how much of the previous student's 6-chapter, 71-page structure
      to adopt — **decided: adopt it fully.**
- [x] **Restructure into the six-chapter thesis format.** `report` class,
      Abstract/TOC/List of Figures/List of Tables as roman-numbered front
      matter, six proper chapters. Report is now 32 pages (was 14). Compiles
      clean, pushed to GitHub (`e90d941`).
- [x] **Split Methodology into Machine Learning Methods and Deep Learning
      Methods sections**, each with full math: ARIMA (AR/I/MA form + Fourier
      terms + log/exp back-transform derivation), ridge regression
      (objective + closed form), random forest (ensemble + splitting
      criterion), gradient boosting (stagewise update + functional gradient),
      GRU (all four gate equations), all checked against the actual
      implementation (`step08_gru.py`) before writing, not assumed.
- [x] **Add theory sections to Literature Review** mirroring the Methodology
      split, with 4 new CrossRef-verified citations: Hoerl & Kennard 1970
      (ridge), Friedman 2001 (gradient boosting), Cho et al. 2014 (the GRU),
      Hochreiter & Schmidhuber 1997 (LSTM / vanishing gradient).
- [x] **References: still only 11 entries (~1 page), not 4+.** Done, see
      above — 40 entries, 4 pages, ARIMA/Box-Jenkins and the boosting
      lineage both now cited, plus a forecast-evaluation-methodology thread
      and a health/India-context thread that weren't in the original plan.
- [x] Read the 4 Delhi/ML-vs-classical citations full-text. Full text
      proper wasn't obtainable through any legitimate route (paywalls and
      bot walls on every host tried), but abstract-level reading caught a
      real overclaim: Singh & Srivastava's "evaluation around health risk"
      was fixed to describe their health-risk assessment and their ML
      forecasting comparison as the two separate analyses they actually
      are. See PROJECT_STATUS.md for the full account.
- [ ] Consider adding "Chapter Summary" subsections to Discussion and
      Conclusion to match the convention Results already uses. Lower
      priority, cosmetic.
- [ ] A full read-through of all the new Methodology/Literature content for
      voice, since it was written in one sitting rather than slowly.

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
- [x] Full read-through of `report/main.tex` end to end (written across
      several sessions spanning weeks — check the voice is consistent and
      nothing repeats). Voice holds up throughout, including today's
      citation-dense additions. One real bug found: the Rolling-Origin
      Evaluation section had the single-split and rolling-origin rMAE
      numbers (0.903 and 0.940) transposed. Fixed.
- [x] Fix anything found in the read-through; confirm tables/figures still
      match after the sensitivity rerun. The transposed-numbers bug above
      was the one thing found and it's fixed; tables/figures unaffected
      since they're generated from the result files, not hand-typed.
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
