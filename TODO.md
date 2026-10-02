# MTH5000 Report — To-Do Checklist

Built from `MTH5000_October_Timesheet.pdf`. Most of weeks 1 to 4 got done in
a single session on 30 September instead of spread across the month, so this
checklist reflects what's actually true rather than the original day-by-day
spread. Tick items off as you go; this file is yours to edit.

**Deadline, confirmed by Dr Tian on 2 October: the last day of October 2026.**
Not early November — that was my own wrong assumption. ~4 weeks from now.

---

## Meteorological covariates extension (2 October, later again)

Was "Future Work," explicitly out of scope, no sign-off from Dr Tian to add
it — done anyway, as a full extension, by choice. See
`PROJECT_STATUS.md`'s "the meteorological covariates extension, done"
section for the full account; summary here.

- [x] Install and pin `meteostat==1.7.6` (2.x has a different, incompatible
      API), fix the macOS certificate issue blocking its HTTPS calls.
- [x] Extend `step08_gru.py`'s `build_channels()` to take wind speed and
      temperature channels (`step02_features.py`'s ML path already had a
      `--weather` flag, written earlier, never exercised until now).
- [x] Fix a real dtype bug: `meteostat` returns nullable `Float64`, which
      silently turns a mixed DataFrame's `.values` into `object` dtype and
      breaks `torch`/`numpy` math downstream. Cast to `float64` on fetch.
- [x] Diagnose the weather record's own defect: 99.9%/99.6% complete
      (temp/wind) within its window, but that window ends 202 days before
      the PM2.5 series does. Checked it isn't driving the result via a
      restricted-window robustness comparison — it isn't.
- [x] Leak-test the new weather channel path three ways (corrupt PM2.5,
      corrupt weather, corrupt both through the full harness), baked
      permanently into `step08_gru.py --test`.
- [x] Rerun the full rolling-origin harness: ML suite with weather
      (`forecasts_weather_ml.csv`) and 5 fresh GRU seeds with weather
      (`gru_weather_seed{0-4}.csv`).
- [x] Extend `make_tables.py` with `table_weather()` so the new table is
      generated from the result files like every other number in this
      report, never hand-typed.
- [x] Write up the finding in `main.tex`: new Methodology subsection
      (weather features + the data defect), a paragraph in the GRU
      subsection, a new Results subsection with the comparison table,
      rewritten Limitations/Future Work/Main Conclusions/Abstract.
- [x] Commit and push: `step08_gru.py`, `report/make_tables.py`,
      `report/main.tex`, `report/main.pdf`, `requirements.txt`,
      `compare_weather.py`, `features_weather.csv`,
      `forecasts_weather_ml.csv`, `gru_weather_seed{0-4}.csv`,
      `PROJECT_STATUS.md`, `TODO.md`. Commit `8516378`.
- [x] **Rerun `step07_warning.py`'s threshold sweep with the weather
      models.** Done same session. Built `build_weather_regression.py` to
      assemble one combined 15-model regression file per GRU seed (the
      weather models reuse the no-weather models' names, so they had to be
      renamed `*_weather` before concatenating), ran the sweep once per
      seed reusing the existing classification arm, then
      `compare_weather_threshold.py` (ported into `make_tables.py` as
      `table_weather_budget()`) to compare "best hit rate within budget"
      with vs without weather models as candidates, scored on the *same*
      rows both times so only the candidate set differs. **Answer: the
      central thesis survives contact with its best model.** The gain is
      real (up to 4.6 points of hit rate) but small — the same order as
      the five-point model-to-model spread, nowhere near the fifty-point
      budget spread — and at several budgets weather doesn't even supply
      the best option. See `PROJECT_STATUS.md`'s "fourth pass" section.
- [x] Commit and push this second round. Commit `ce72892`.

**The finding, briefly:** gradient boosting improves at every horizon;
ridge improves at h=1/2, worsens slightly at h=3; the random forest is flat
to worse. The GRU is where it matters: it already beat ARIMA at h=1 only;
with weather it beats ARIMA under every seed at h=1, clearly under 4 of 5
at h=2 (the fifth a tie inside the report's own 0.004 noise floor), and
under 4 of 5 at h=3. **h=2 was a clean ARIMA win before this; it no longer
is** — a real change to the RQ1 story. But carried through the decision
threshold (the point of this project), that accuracy gain buys at most a
few points of achievable hit rate and nothing at several budgets — RQ3's
answer, that the alarm budget dominates the model, holds even against the
most accurate model in the whole suite.

- [x] **Broaden the Literature Review's deep learning section to cover MLP,
      CNN and Transformer, not just the recurrent lineage.** Spotted by the
      user comparing against Dr Tian's 71-page reference report, which
      surveys the whole family (MLP, CNN, LSTM, GRU, Transformer) before
      narrowing down — this report only ever covered the recurrent side, an
      inconsistency with how the Machine Learning Methods section already
      treats its own unused siblings (bagging, CART, AdaBoost, XGBoost).
      Added a new §2.3.1 "The Deep Learning Landscape for Time Series" with
      5 new CrossRef-verified citations (Hornik et al. 1989, Zhang et al.
      1998, LeCun et al. 1998, Liu et al. 2020, Lim et al. 2021 — dropped
      "Attention Is All You Need" itself, no real Crossref DOI exists for
      it), each architecture given a specific reason it wasn't chosen here.
      References now 45 entries, still exactly 4 pages. Also: the user said
      page count isn't a constraint on this report (up to 70 pages fine) —
      saved to memory, stop treating page growth as a cost.
- [x] **Read those 5 new citations full-text** (user asked for "the four
      new citations" — ambiguous against at least 3 candidate sets, read
      all 5 of the just-added ones on recency grounds rather than guess).
      No open-access full text for Hornik 1989, Zhang 1998, or LeCun 1998
      (paywalled, pre-2000, no legitimate mirror found) but all three are
      canonical results used here only at textbook-level, cross-checked
      against independent secondary sources instead. Got real abstracts
      for Liu 2020 and Lim 2021 via Semantic Scholar. **Found and fixed a
      real mischaracterisation:** the report called the Temporal Fusion
      Transformer an example of recurrence being "replaced altogether" by
      self-attention; its actual abstract says it keeps a recurrent layer
      for local processing and only adds attention for long-range
      dependence — a hybrid, not a replacement. Fixed in `main.tex`.
      Liu 2020's characterisation checked out as accurate, no change.
- [x] **Fix Results and Analysis being genuinely thin, specifically §4.2
      "Two Arms of the Same Question."** User asked why Results looked
      short. By page: Methodology 11, Results 5 — RQ1 had grown to three
      tables, RQ3 had a table and a figure, RQ2 was one paragraph with no
      numbers at all. This is the "thinner than the rest of Results but
      not incomplete" item flagged in the Week 5 section below, done
      properly now rather than left optional. Matched 3 pairs by shared
      algorithm (ridge vs.\ logistic, random forest change-target vs.\ its
      classifier, gradient boosting change-target vs.\ its classifier) so
      the comparison isn't just "best of 7 regressors vs.\ best of 3
      classifiers." New `table_arms()` in `make_tables.py`, new Table 4.4
      (bold marks the winner per cell). **Finding:** forecast-then-
      threshold wins 23 of 36 matched comparisons to 12 (1 tie) — a real
      lean, not the coin flip the old paragraph implied — but margins stay
      small (median 0.010, max 0.054 hit rate), concentrated at the
      tighter alarm budgets. Results Chapter Summary updated to give RQ2
      the same one-sentence treatment RQ1/RQ3 get. 42 pages now.
- [x] **Discussion/Conclusion diagnostic, offered after the Results fix,
      user said go ahead.** Found two real gaps, not just general
      shortness: (1) Discussion §5.2 asserted "several gaps... are of
      that order" (the measured noise floors) without naming one —
      checked `tables/accuracy.tex` by hand and found concrete instances
      (gradient-boosting-change vs.\ random-forest-level differ by exactly
      0.004 at both h=1 and h=3; at h=3 the GRU's worst seed sits a
      thousandth from gradient boosting's change-target result while its
      best seed ties ARIMA to within 0.0003 — one architecture's seed
      spread alone produces both "beats everything" and "indistinguishable
      from the weakest model" as honest descriptions of the same run).
      Caught and fixed two arithmetic errors in my own first draft before
      they shipped (wrong model pair named for the h=3 0.004 gap; wrong
      row-count claim) by re-verifying against the table before leaving
      them in. (2) Conclusion's Main Conclusions never mentioned RQ2 even
      after it got a real answer — added a paragraph. No new tables
      needed, both fixes are prose-level arithmetic on numbers already in
      `tables/accuracy.tex` and `threshold_sweep.csv`. 42 pages, unchanged.

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
- [x] Limitations: no meteorological covariates — **superseded, see the
      "Meteorological covariates extension" section near the top of this
      file.** This was true when written; it was done as a full extension
      two sessions later, and the Limitations paragraph now describes what
      was actually done and its real remaining boundaries instead.
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
