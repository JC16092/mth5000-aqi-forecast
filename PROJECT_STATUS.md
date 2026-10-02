# PROJECT STATUS: read this first

Handover note so a new conversation can pick up without re-reading everything.
For the schedule and the step by step plan, see `BLUEPRINT.md`, but note its
dates and structure are now superseded (see below).
Last updated: 2 October 2026, after a supervisor meeting that substantially
changed what the report needs to look like. See "Week 7, meeting with Dr Tian"
near the end. **Read that section before touching the report again.**

**Deadline, confirmed by Dr Tian: the last day of October 2026.** Not early
November as previously assumed. Call it four weeks from 2 October.

**The report's scope just grew substantially.** The 14-page draft is not close
to sufficient. Dr Tian's own worked example from a previous student is 71
pages. Do not resume writing without reading the new section below in full.

---

## Who and what

- **Student:** Jaykumar Vinodbhai Chauhan, ID 34710280
- **Degree:** Master of Mathematics, Monash University
- **Unit:** MTH5000, Masters Research Project (compulsory, 4th semester)
- **Supervisor:** Dr Tianhai Tian, School of Mathematics. He taught me MTH3230 (Time Series and Random Processes).
- **Time available:** roughly 9 to 10 weeks from mid-August 2026.
- **Constraints:** laptop only, no budget, no fieldwork, free data only.

## The approved project

**Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities.**

Dr Tian has approved this topic. Two earlier proposals were written and are now superseded (see below).

The idea: daily pollution data for one Indian city, most likely Delhi. Predict concentrations one to three days ahead, and predict whether a day will exceed a hazardous health threshold. Evaluate the models not just on average error but as a *warning system*, using hit rate and false alarm rate, because a model with good average error can still miss the extreme days that are the only ones anyone cares about.

**Three research questions:**

1. How accurately can concentrations be forecast 1 to 3 days ahead by machine learning, versus classical and naive benchmarks?
2. Is it better to forecast the concentration then apply a threshold, or to classify the exceedance event directly?
3. As a warning system, what hit rate and false alarm rate does each approach achieve, and how does the decision threshold trade them off?

**Supervisor's key steer:** he explicitly asked for machine learning rather than relying on ARIMA, and wants several methods tried. SARIMA is retained only as a benchmark, because ML results need a classical reference point to be interpretable.

**Model suite:** naive and seasonal-naive benchmarks, SARIMA benchmark, penalised linear regression, random forest, histogram-based gradient boosting (scikit-learn's HistGradientBoosting, see the environment note below), LSTM or GRU. A Kolmogorov-Arnold Network is a stretch goal, chosen because Dr Tian published a KAN paper in November 2025.

## Current file map

**Current and in use:**

| File | What it is |
|---|---|
| `project_proposal_aqi_forecast.pdf` | THE approved proposal. ML version. Use this one. |
| `PROJECT_LOGBOOK.pdf` | The full teaching record. Every concept, every step, every mistake, written for someone starting from zero. Built by `build_logbook.py`. Read Part V. |
| `supervisor_meeting_3_prep.pdf` | The six page document to hand Tian: provenance, methods, results, code walkthrough. Built by `build_meeting_brief.py`. |
| `supervisor_meeting_3_agenda.pdf` | The eighteen questions to ask Tian, with answer lines. Built by `build_meeting_agenda.py`. |
| `report/main.tex` | The report. Compiles to 14 pages. **Every section is now written**, including Abstract, Introduction, Literature, Discussion, Limitations and Conclusion. Only optional polish remains (see "Week 7" below). |
| `report/refs.bib` | Bibliography, 7 CrossRef-verified entries. `tectonic main.tex` runs bibtex automatically; no separate step needed. |
| `software_setup_guide_aqi_forecast.md` | Data sources, packages, working order for this project |
| `data/delhi_clean.csv` | THE dataset. 3,093 usable days, 2016-11-09 to 2026-08-27. Built from `data/delhi.csv` by step 1b. |
| `data/delhi.csv` | Raw download, kept so the cleaning can be rerun with different thresholds. |
| `step08_gru.py` | Gated recurrent network in the same harness. Takes `--seed`; report a range, not a point. |
| `forecasts_with_gru.csv` | All ten models by three horizons. The final RQ1 table. |
| `step07_warning.py` | Direct classification arm plus the decision threshold sweep. RQ2 and RQ3. |
| `threshold_sweep.csv` | Every model at every decision threshold. The source of the main figure. |
| `step06_ml.py` | Ridge, random forest and histogram gradient boosting as Forecaster subclasses, level and change targets. |
| `forecasts_all.csv` | 9 models by 3 horizons over 2,303 origins. **The RQ1 result.** |
| `step05_rolling.py` | The rolling origin harness. Every model plugs into one loop; the loop carries the leakage test. |
| `forecasts_rolling.csv` | 2,303 origins over 6.8 years, 6 models by 3 horizons. **These are the reportable numbers.** |
| `evaluation.py` | Shared scoring. Steps 3 onward import it so every model is scored by identical code. |
| `step03_benchmarks.py` | Naive, carried-forward naive, seasonal naive and climatology. |
| `step04_arima.py` | ARIMA with Fourier exog on log concentration, plus a no-Fourier ablation. |
| `forecasts_classical.csv` | Long forecast table, 7 models by 3 horizons on the test block. |
| `step01b_clean.py` | Working script: reports impossible values with context, applies coverage and plausibility rules only when told. |
| `step00_fetch_openaq.py` | Working script: finds Delhi stations, downloads the daily PM2.5 series from OpenAQ v3, S3 archive fallback. Parsing tested against fixtures and a stubbed API. Not yet run against the live API. |
| `step01_data_check.py` | Working script: data viability check, ADF test, periodogram, plots. Tested. |
| `step02_features.py` | Working script: builds the supervised feature table. Imports the loader from step 1. Has a built-in leakage test. Tested on demo and messy CSVs. |
| `BLUEPRINT.md` | Week by week plan from 20 August to submission on 22 October 2026. Data acquisition commands, decision gates, risk triggers. Read it after this file. |
| `PROJECT_STATUS.md` | This file |

**Superseded, keep for reference but do not use:**

| File | Why superseded |
|---|---|
| `project_proposal_draft.pdf` | The EKC economics proposal. Rejected as too economics-heavy. |
| `project_proposal.pdf` | Older duplicate of the EKC proposal. Should be deleted. |
| `project_proposal_kalman.pdf` | Alternative topic, not chosen |
| `software_setup_guide.md` | Setup guide for the EKC project, not this one |
| `reference_sources_and_links.md` | EKC references |
| `supervisor_meeting_prep.md`, `meeting_prep_tianhai_tian.pdf`, `supervisor_meeting_2_prep.pdf` | Meeting prep, already used |
| `about_me_pitch_*.md`, `followup_email_template.md`, `coursework_summary_for_prof.*` | Earlier admin, done |

## Where I am right now

**The data exists.** Environment built, station chosen, series downloaded, cleaned
and ready. Day one of nine weeks finished the whole of week one.

### The dataset

`data/delhi_clean.csv`. OpenAQ location **8118**, sensor **23534**, named
"New Delhi", provider **AirNow**. 3,093 usable days from 2016-11-09 to
2026-08-27, 9.8 years, longest gap 34 days, mean 102.7, median 71.7, max 896.0,
920 days above 121, which is 29.7 percent.

Rebuild it from nothing with:

```bash
export OPENAQ_KEY="..."
python step00_fetch_openaq.py --location-id 8118 --from 2016-11-09 --out data/delhi.csv
python step01b_clean.py --csv data/delhi.csv --apply --min-value 0 \
       --min-coverage 50 --max-value 1000 --out data/delhi_clean.csv
```

### Why station 8118, and what it costs

Compared five candidates on coverage rather than on span. The finding that
decided it: **every CPCB station returns data only from 2025-02-19**, about
eighteen months, even though the OpenAQ location metadata advertises
`datetimeFirst` of 2016-02-05. Four independent stations sharing an identical
cutoff is a systematic limit on what the measurements endpoint serves, not a
coincidence. Station 8118 is on a different provider and returns the full 9.8
years.

The cost of that choice, and it must be stated plainly in the data section:
8118 is an AirNow feed, almost certainly the US diplomatic post monitor, not the
Indian official network. So the project forecasts at one well-characterised
reference site in Delhi, which is common in this literature, and cites OpenAQ
and the US Department of State rather than CPCB. Confirm the owner and licence
from the location metadata before writing that section, and tell Dr Tian rather
than letting him find it.

Whether the S3 archive holds the full CPCB record is untested and worth an hour
in week 6. If it does, a CPCB station becomes a robustness check.

### The coverage bug, which is a real finding

OpenAQ computes `percentComplete` as observations divided by an `expectedCount`
of 24, assuming hourly reporting. **This sensor reported half-hourly from 2016
to 2024 and hourly from 2025.** The visible symptom is `percentComplete` above
100, which is impossible. The damaging one is invisible: a day holding 24 of a
real 48 readings scores as fully complete, so a mean built from half a day of a
polluted afternoon enters the series as a genuine daily mean. Days at 50 to 75
percent true coverage were about nine times more likely to exceed 500 than days
above 90 percent. That is where every impossible value came from.

Both `step00_fetch_openaq.py` and `step01b_clean.py` now take the cadence from
the data, using the 90th percentile of observation counts within each year, which
follows the 2025 change automatically. Do not reintroduce a hard-coded 24.

### Cleaning decisions, and how to defend each

282 days removed of 3,375.

- `--min-value 0`, 5 days. Negative mass is impossible. Needs no defence.
- `--min-coverage 50`, 270 days. Against the true cadence. Fifty rather than 75
  because the longest gap is the binding constraint: at 60 percent and above it
  jumps to 69 days, past the point where seasonal fits distort, and at 90 percent
  a 185 day hole appears. Fifty keeps the worst gap at 34.
- `--max-value 1000`, 7 days. **This is the weakest link and a judgement, not a
  fact.** Justified on seasonality: 1990 appeared three times, identical, at the
  maximum, which is a clip ceiling rather than a measurement, and one of them was
  2 September, in the monsoon, between neighbours of 42 and 178. Plan a
  sensitivity run in week 5 with no `--max-value` and show the conclusions hold.
  That converts the weakest assumption into a reported robustness check.

The exceedance rate barely moved across every candidate rule, 30.0 down to 27.0.
The coverage filter is not eating the events, which it easily could have been.
Say so in the report.

### The weekly cycle does not exist here. Settled, with evidence.

Tested three ways on the cleaned series, all agreeing.

1. Periodogram: dominant periods 357.9, 178.9, 188.4, 397.7, 325.4, 60.7 days.
   The annual cycle and its harmonics. Nothing near 7.
2. ACF of the deseasonalised log series: lag 7 is 0.173, but lag 6 is 0.179 and
   lag 8 is 0.153. Lag 7 sits on the decay curve, not above it. Same at 14 and 21.
   That is persistence, not periodicity.
3. Day of week on the same residuals: Mon +2.0%, Tue +3.1%, Wed +1.6%, Thu -0.3%,
   Fri -2.2%, Sat -0.9%, Sun -3.3%. Spread 6.5%. ANOVA F = 1.13, p = 0.34.
   Kruskal-Wallis p = 0.77.

**Consequence: ARIMA with annual Fourier exog, no weekly seasonal order.** The
two-seasonal-period problem does not arise. Do not add a weekly seasonal term out
of habit. `dow` and `is_weekend` stay in the feature table because their
unimportance is itself a reportable result, but expect nothing from them.

The physical reading, worth giving Dr Tian: a weekly cycle in urban PM2.5 is a
traffic signature, and 8118 is a diplomatic enclave monitor, not a roadside site.
Its absence is coherent, not missing.

### Two things that follow

**Work in logs.** Annual Fourier terms on log PM2.5 give R-squared 0.693, far
better than on the raw scale, because the series is strongly right skewed.
Back-transforming a log-scale mean forecast gives a median, not a mean; say which
one you report.

**Fourier order K = 4.** BIC keeps improving to K = 6, but BIC assumes
independent errors and these residuals are heavily autocorrelated, so the
effective sample size is far below 3,093 and BIC over-selects. K = 4 takes the
clear gain from K = 3 and stays parsimonious. Treat the order as a tuning
parameter under the rolling-origin harness in week 3 rather than trusting an
in-sample criterion.

### The feature table

`features.csv`, built 20 August from `data/delhi_clean.csv` with `--fourier 4`.
3,355 rows, 39 feature columns, 6 target columns. Leakage checks passed. Class
balance 29.7 percent at h=1, 2 and 3. Suggested chronological split: train to
2023-11-17, validation to 2025-04-05, test from 2025-04-06.

### Week 2, complete

**The split had to be changed before any result was trustworthy.** The first
attempt used the last 15 percent as test, which happened to cover one winter and
two low seasons: exceedance rate 17.8 percent against 30.8 in training, and half
the volatility. Every model scored beautifully for reasons unrelated to the
models. The test block is now the last 20 percent, spanning two winters, at 25.1
against 33.6 percent. `step03_benchmarks.py` prints the character of all three
blocks on every run so this cannot hide again.

**rMAE was added alongside MASE.** MASE divides by the training period's
volatility, so on a calmer test period every model's MASE falls including the
naive forecast's, which reads as though persistence beats persistence. rMAE
divides by the naive forecast's error on identical rows, so naive is exactly
1.000 and everything else is directly interpretable. Read rMAE first.

**Results on the test block, 2024-09-11 to 2026-08-27.** rMAE, lower is better.

| Model | h=1 | h=2 | h=3 |
|---|---|---|---|
| ARIMA(1,1,1) + Fourier, median | **0.903** | **0.850** | **0.798** |
| ARIMA(1,1,1) + Fourier, mean | 0.921 | 0.856 | 0.817 |
| ARIMA(1,1,1), no Fourier | 0.948 | 0.916 | 0.901 |
| naive and naive carried forward | 1.000 | 1.000 | 1.000 |
| climatology | 1.394 | 1.075 | 0.956 |
| seasonal naive, lag 7 | 1.711 | 1.325 | 1.187 |

Four things in that table are worth reporting rather than just recording.

1. ARIMA beats persistence at every horizon and its margin grows with horizon,
   from 10 percent at one day to 20 percent at three. Persistence degrades faster
   than the model does.
2. **The Fourier terms earn their place, and increasingly so with horizon:** 4.5
   points of rMAE at h=1, 6.6 at h=2, 10 at h=3. Recent information decays and
   seasonal information does not, which is exactly the expected mechanism. Keep
   the ablation in the report; it turns a design choice into evidence.
3. **The back-transform behaves as theory says.** The median variant wins on MAE
   at every horizon and the mean variant wins on RMSE at every horizon. That is
   not a contradiction, it is the definition of the two quantities, and it is a
   cheap demonstration that the log scale was handled deliberately.
4. Seasonal naive is the worst benchmark everywhere, rMAE 1.19 to 1.71. A
   benchmark that assumes a weekly cycle loses to one that assumes nothing.
   Quantitative support for the finding above.

**A tension to raise with Dr Tian.** The order search chose d = 1 by a clear AIC
margin, 1892.5 against 1912.1 for the best d = 0 specification, even though the
ADF test rejects a unit root. ADF has low power on a strongly seasonal series,
and the two disagree. Worth a sentence in the report rather than quietly
following whichever one suits.

**As a warning system, the numbers are sobering.** At h=1 persistence achieves a
hit rate of 0.860 at 89 alarms per year; ARIMA with Fourier reaches 0.902 at 96;
climatology reaches 0.970 at 115. A system raising an alarm on a quarter to a
third of all days is not obviously useful, and no amount of model accuracy fixes
that. It is fixed by moving the decision threshold, which is the sweep in week 5.

**A trend that affects the week 3 design.** Day-to-day volatility has fallen
steadily: mean absolute daily change was 38.9 in 2017 and 15.8 so far in 2026,
with the annual mean drifting down too. An expanding training window therefore
keeps feeding the model an era that no longer resembles the present. Test a fixed
width rolling window against the expanding one in step 5 rather than assuming.

### Week 3, complete. The harness exists and these are now the real numbers.

2,303 origins from 2019-11-09 to 2026-08-24, spanning 6.8 years, three year
burn-in, parameters re-estimated every 90 days, state advanced daily in between.

**The single split was flattering ARIMA.** rMAE at h=1 was 0.903 on the single
block and is 0.940 under rolling origin; at h=3 it was 0.798 and is 0.836. The
honest numbers are worse, which is the entire reason for building the harness.
Report the rolling numbers and mention the single split only to show why it was
abandoned.

| Model | h=1 | h=2 | h=3 |
|---|---|---|---|
| ARIMA + Fourier, mean back-transform | **0.939** | 0.875 | 0.837 |
| ARIMA + Fourier, median back-transform | 0.940 | **0.873** | **0.836** |
| ARIMA, no Fourier | 0.973 | 0.915 | 0.894 |
| naive carried forward | 1.000 | 1.000 | 1.000 |
| climatology | 1.417 | 1.054 | 0.948 |
| seasonal naive, lag 7 | 1.736 | 1.286 | 1.157 |

**The leakage test is inside the harness and runs before any forecast is
produced.** It corrupts the series from a cut date, reruns every model through
the same loop, and asserts that no forecast issued before the cut changed. It
passes with the ARIMA in the loop, which is the case that matters, because a
model carrying filter state across origins is the one that could plausibly leak.

**Expanding window against a three year rolling window: no material difference
for ARIMA**, 0.940 against 0.946 at h=1 and 0.836 against 0.841 at h=3. So the
declining volatility does not justify a shorter window, and expanding is kept
because it is simpler and uses more data. That question is now answered rather
than assumed.

**But it matters a great deal for climatology**, which improves from 1.417 to
1.341 at h=1 and from 0.948 to 0.897 at h=3, with its bias falling from +11.1 to
+4.7. The reason is worth a paragraph in the report: ARIMA differences the series,
d = 1, so a slow downward drift in the level cancels out. Climatology is a pure
level estimate with no differencing, so a decade of higher concentrations biases
it upward and a shorter window tracks the decline. The drift hurts exactly the
model that cannot absorb it.

**The back-transform choice is a warning system decision, not a cosmetic one.**
The median variant under-forecasts by 6.4 at h=1 and 9.5 at h=3, because the
median of a right skewed distribution sits below its mean. The bias corrected
mean variant is unbiased, +1.3 at every horizon. On MAE they are indistinguishable
and the median wins by 0.001; on RMSE the mean wins clearly, 36.28 against 37.56
at h=1. As a warning system the mean variant catches more: hit rate 0.932 against
0.900 at h=1, at the cost of 116 alarms per year against 107. **Take this to Dr
Tian.** A systematic tendency to under-forecast is exactly the wrong failure mode
for a hazard warning, and the choice between the two back-transforms should be
made on that argument rather than on a decimal place of MAE.

**ARIMA with Fourier has the best CSI at every horizon**, 0.790 at h=1 against
0.776 for persistence and 0.732 for climatology. Climatology still has the
highest raw hit rate, 0.937, but buys it with 126 alarms per year.

### Week 4, complete. Research Question 1 has an answer, and it is a negative one.

rMAE under rolling origin, 2,303 origins. Lower is better; 1.000 is persistence.

| Model | h=1 | h=2 | h=3 |
|---|---|---|---|
| **ARIMA + Fourier** | **0.940** | **0.883** | **0.832** |
| random forest, change target | 0.962 | 0.918 | 0.898 |
| random forest, level target | 0.985 | 0.929 | 0.882 |
| gradient boosting, change target | 0.978 | 0.937 | 0.881 |
| gradient boosting, level target | 1.007 | 0.943 | 0.886 |
| ridge | 0.997 | 0.952 | 0.897 |
| naive carried forward | 1.000 | 1.000 | 1.000 |
| climatology | 1.415 | 1.060 | 0.947 |
| seasonal naive | 1.759 | 1.325 | 1.168 |

**The classical model beats every machine learning model at every horizon.** Dr
Tian asked for machine learning, so this needs to be delivered as a finding with
its reasons rather than as a disappointment. The likely mechanism: on a strongly
persistent series the optimal forecast is close to a smooth function of the recent
past, which ARIMA represents exactly and a tree can only approximate in steps,
and three thousand daily observations is a small sample for a flexible learner.
This is the outcome the forecasting competition literature would predict.

**The first version of this result was wrong and had to be corrected.** With
fixed hyperparameters, gradient boosting scored 1.152 at h=1, worse than
persistence, which would have been a striking claim. A check on validation showed
the configuration was overfitting: 400 iterations over 31 leaf nodes gave 1.085,
four leaf nodes over 200 iterations gave 0.970. Capacity is now chosen at every
refit from a small explicit grid, scored on the last fifth of the training window
held out in time order. Gradient boosting improved from 1.152 to 1.007 at h=1 and
from 1.011 to 0.886 at h=3. **The conclusion survived the correction, which is
what makes it reportable.** Put this episode in the report: a negative result
about a model class is only worth stating once you have shown it is not a
negative result about your own hyperparameters.

**Modelling the change rather than the level helps the tree models**, from 0.985
to 0.962 for the random forest at h=1 and from 1.007 to 0.978 for gradient
boosting. Trees cannot extrapolate beyond the targets they were trained on and
this series drifts downward; handing them the persistence for free and asking
them to model a roughly stationary residual removes that handicap. Report both
forms.

**The one leakage trap specific to supervised learning**, and it is now handled
and tested: at origin t the label on feature row t' is the value at t' + h, so
the training set ends at **t minus h**, not t. A separate model per horizon is
required by that arithmetic. The error would have been three rows per refit and
completely invisible in the output.

**As a warning system the ranking reverses.** At h=1 gradient boosting reaches a
hit rate of 0.948 and CSI 0.800 against ARIMA at 0.906 and 0.798, because ARIMA's
median back-transform biases it low by 6.4 and the tree models are close to
unbiased. So the best model on average error is not the best warning system. That
tension is the substance of Research Question 2 and should not be resolved by
picking whichever number flatters.

### Week 5, complete. And it produced the finding the report should be built on.

**RQ3 first, because it reframes everything else.** Sweeping the decision
threshold while holding the event fixed at 121 gives, at h = 1:

| Alarm budget per year | Best hit rate available |
|---|---|
| 40 | 0.377 |
| 60 | 0.567 |
| 80 | 0.727 |
| 100 | 0.873 |

Now compare that against what the choice of model buys. At a fixed budget of 60
alarms per year, h = 1: ARIMA 0.567, gradient boosting 0.573, logistic 0.571,
persistence 0.558, climatology 0.521. At h = 3: ARIMA 0.533, gradient boosting
0.535, classifier 0.539, persistence 0.524, **climatology 0.537**.

**The spread across models is about five points of hit rate. The spread across
alarm budgets is fifty.** At three days ahead, climatology, which knows nothing
whatever about recent conditions, matches the best model to within four
thousandths. The operational question is which alarm budget can be justified, and
the modelling question is close to a rounding error beside it.

This is the argument the project exists to make and it should be the spine of the
report. Everything in weeks 2 to 4 becomes supporting evidence for it rather than
the point. `fig5_warning.png` shows it: the curves very nearly coincide.

**RQ2: neither arm dominates.** Forecast then threshold wins at some horizon and
budget combinations, direct classification at others, and no pattern in the
winners survives inspection. Given that, prefer the forecast then threshold arm
on grounds other than accuracy: it yields a concentration, which can be
rethresholded for any policy without refitting, while a classifier is welded to
the threshold it was trained on. Say that explicitly rather than presenting a
coin flip as a result.

**A caution to state in the report.** These hit rates are lower than the earlier
tables suggest because those used a decision threshold equal to the event
threshold, which raises about 100 alarms a year. Any headline number must state
the alarm budget it was obtained under. A hit rate quoted without its false alarm
cost is not a result.

### A reproducibility defect found and fixed on 29 August

Running the identical pipeline on two machines gave individual gradient boosting
forecasts differing by up to **85 micrograms per cubic metre**. Two causes
compounded. Scikit-learn's histogram gradient boosting parallelises with OpenMP,
so floating point summation order depends on the machine's thread count and a
fixed `random_state` is not enough for bit reproducibility. Those small
differences then flipped which configuration the capacity search selected at some
refits, turning a rounding difference into a different fitted model.

Both are now fixed in `step06_ml.py` and `step07_warning.py`: threads are pinned
to one inside every tuned fit and prediction, and the search only abandons an
incumbent configuration when a later one beats it by more than half a percent, so
noise cannot decide the choice.

**The conclusions were never at risk.** Aggregated over 2,303 origins the two
machines agreed to within **0.0039** of relative mean absolute error on every one
of the 27 model and horizon cells, and no ordering changed except among the
near-tied tree models. ARIMA, ridge, climatology, persistence and seasonal naive
were bit identical.

**But state that number in the report, because it is part of the argument.** The
machine to machine numerical noise of 0.004 is the same order as the gap between
adjacent machine learning models in the results table, for instance gradient
boosting at 0.978 against random forest at 0.985. When switching computers moves
a model as much as switching models does, the claim that the model choice matters
little is not rhetoric.

The final reported numbers should come from a rerun under the fixed code at the
freeze point, not from the current CSVs.

### Week 6, complete. The recurrent network changed the answer to RQ1.

**It should not have been skipped, and I advised skipping it.** On the strength of
the threshold result I recommended dropping it as unlikely to matter. That was
wrong and the record should say so: it is the best model at one day ahead.

rMAE. **Final, from five seeds run on 29 August.**

| Model | h=1 | h=2 | h=3 |
|---|---|---|---|
| GRU, range over 5 seeds | **0.915 to 0.935** | 0.885 to 0.898 | 0.832 to 0.879 |
| ARIMA + Fourier | 0.940 | **0.883** | **0.8318** |
| random forest, change target | 0.962 | 0.918 | 0.898 |
| gradient boosting, change target | 0.978 | 0.937 | 0.881 |
| ridge | 0.997 | 0.952 | 0.897 |
| persistence | 1.000 | 1.000 | 1.000 |

Seed by seed, so the claim is exact:

| | seed 0 | seed 1 | seed 2 | seed 3 | seed 4 | ARIMA |
|---|---|---|---|---|---|---|
| h=1 | 0.9177 | 0.9241 | 0.9347 | 0.9154 | 0.9212 | 0.9401 |
| h=2 | 0.8924 | 0.8981 | 0.8853 | 0.8855 | 0.8926 | 0.8827 |
| h=3 | 0.8792 | 0.8568 | 0.8401 | 0.8592 | 0.8321 | 0.8318 |

**h=1: the network beats ARIMA in 5 of 5 seeds.** Robust, report it as a win.
**h=2: ARIMA beats the network in 5 of 5**, by 0.003 against the best seed.
**h=3: ARIMA beats the network in 5 of 5, but by 0.0003 against seed 4.** That is
a tie. Do not claim a win for either at three days; say they are indistinguishable
and give both numbers.

**The corrected answer to RQ1.** At one day ahead the recurrent network beats
ARIMA under every seed tried. At two and three days ARIMA beats it under every
seed. So machine learning wins at the shortest horizon and the classical model
wins as the horizon lengthens, which is a more interesting result than either
clean sweep and is consistent with the mechanism: the network exploits short range
nonlinear structure, while at longer horizons the seasonal component dominates and
the Fourier terms carry it more cleanly.

**Report the network as a range, never as a point.** The spread across seeds is
0.019 at h=1, 0.013 at h=2 and 0.047 at h=3. At three days that spread exceeds the
gap between the network and five of the other models. A single seed neural network
number is not a result, and stating one would be the same error as the gradient
boosting hyperparameters in week 4. Run five seeds for the final table.

**A methodological cost worth a paragraph.** Every other model in the suite handles
missing days honestly: the state space models skip the measurement update at a gap,
gradient boosting takes NaN natively. A recurrent network can do neither, since it
must be handed a value at every timestep. Gaps are therefore carried forward with a
separate missingness channel. The one architecture the supervisor asked for is the
one architecture in the suite that cannot represent "I do not know".

**None of this disturbs the week 5 finding.** The spread across all ten models at a
fixed alarm budget remains far smaller than the spread across budgets.

### Week 7, after a stall. Resumed 30 September, report drafted to completion.

Work stopped for about three and a half weeks after week 6 (last activity
around 4 September). Resumed 30 September. Two gaps were found and fixed
before writing continued, then the whole remaining report was drafted in one
session.

**Gap found: the GRU was missing from Table 4 and the decision-threshold
figure's source data.** `step07_warning.py` was still reading
`forecasts_all.csv`, which predates the GRU, even though `make_tables.py`'s
`table_budget()` already had `"gru"` first in its row list. Rerun as:

```bash
python step07_warning.py --regression forecasts_with_gru.csv \
       --reuse-classification forecasts_classification.csv \
       --out-sweep threshold_sweep.csv
```

The GRU lands at 0.371 / 0.554 / 0.721 / 0.873 hit rate across the 40 to 100
alarm budgets at h=1, inside the same narrow band as every other model. This
strengthens the week 5 finding rather than complicating it. Figure 5 was left
alone; it deliberately caps itself at four curves for legibility, by its own
comment, so the GRU's absence there is not a bug.

**The `--max-value 1000` sensitivity run was done.** Rebuilt the cleaning
without the cap (`data/delhi_clean_nocap.csv`, 3,100 days and 927 exceedances
against 3,093 and 920 with the cap) and reran the full ML suite on it
(`forecasts_all_nocap.csv`). ARIMA is essentially untouched: 0.935 against
0.940 at h=1, 0.829 against 0.832 at h=3, because working in logs and
differencing absorbs the clipped-ceiling contamination. The machine learning
models are not protected the same way: ridge moves from a near tie with
persistence to a clear loss at h=1 (0.997 to 1.118), and gradient boosting on
the level target moves from a narrow win to a loss at h=3 (0.883 to 1.006).
**RQ1's finding that ARIMA beats every ML model at every horizon strengthens
rather than merely survives**, because the models it beat most narrowly are
exactly the ones most exposed to the uncleaned tail. This is now written up
in the Limitations section, with these exact numbers.

**Everything else in the report was then written and compiled:**

- Discussion §6.1 (the operational-question argument) and the remaining four
  Limitations paragraphs (single station, single city, small hyperparameter
  grids, no meteorological covariates).
- The Conclusion.
- The personal motivation paragraph, pulled from the approved proposal into
  the Introduction, in the same position it held there.
- The Literature review, all four areas from the old TODO, each anchored to
  a CrossRef-verified citation: Masood & Ahmad (2020) and Singh & Srivastava
  (2025) for Delhi/India ML forecasting; Makridakis et al. (2020, the M4
  competition) for ML-vs-classical on limited data; Jolliffe & Stephenson
  (2012) for warning-system verification; Jiang et al. (2023) for
  negative/invalid monitor readings, the direct counterpart to this
  project's own clipped-ceiling finding. Breiman (2001) and Bergmeir &
  Benítez (2012) were also cited in Methodology, reused from the proposal's
  own indicative references.
- The Abstract, written last, leading with the alarm-budget finding rather
  than which model won, ~230 words.

**I have not read the four new Literature citations full-text**, only
verified via CrossRef that they exist and match their titles. Read them
yourself before treating the Literature section as final; this project holds
everything else to a higher verification bar than that.

**A second gap found and fixed after first calling this "done": Table 4's
GRU row was silently seed-0-only.** `forecasts_with_gru.csv` turned out to be
seed 0 exclusively (checked by comparing `y_pred` against each
`gru_seed{0..4}.csv` directly), so the earlier fix that put GRU into Table 4
had quietly broken this project's own rule of never reporting the network as
a single-seed point, the same rule Table 3 follows correctly. Fixed by
rerunning `step07_warning.py` once per seed
(`threshold_sweep_gru_seed{0..4}.csv`) and extending `table_budget()` in
`make_tables.py` to report GRU as a min-max range there too, mirroring
`table_accuracy()`. Spread across seeds is small, 0.006 to 0.014 in hit rate,
so this reinforces the central finding rather than complicating it. The top
"Best hit rate" summary rows in Table 4 still derive from seed 0 alone, a
roughly 0.002 difference from the true 5-seed best, which is below this
project's own established noise floor and was left as is, flagged rather
than silently decided. **Lesson for next time: "done" needs an actual audit,
not just a compile-and-look check** — this was found only because it was
directly challenged.

**A full audit pass followed, checking every hand-typed number in main.tex
against its source rather than trusting a clean compile.** Two more real
errors found and fixed:

- The coverage-defect sentence in Data was internally inconsistent: "1,085
  of 3,199 observed days" mixed a numerator computed over all 3,467 raw
  rows (including the 268 with no value at all) with a denominator that
  excluded those 268. Fixed to state the correct population (3,467) and
  what 268 actually is.
- The Fourier-ablation claim in Results ("4.5 points at h=1, 10 at h=3")
  traced to a stale week 2 single-split run. `forecasts_all.csv` doesn't
  even carry a no-Fourier ARIMA variant any more. Reran `step05_rolling.py`
  fresh: the real current figure is 3.3 points at h=1, 5.8 at h=3, same
  story, about half the claimed size.

Confirmed correct on direct recomputation, no changes needed: Table 1 and
Table 2 (byte-identical dataset on a fresh rerun); the periodogram's six
dominant periods; ACF at lags 6/7/8; the day-of-week ANOVA (F=1.13, p=0.34,
a hardcoded plot label that happened to still be right) and Kruskal-Wallis
(p=0.77); the Fourier R-squared of 0.69; and the GRU seed-spread figures.

Also fixed a long-standing overfull hbox present since the very first
compile (Table 3 needed `footnotesize`, same as Table 4). The report now
compiles with zero warnings for the first time.

**What is actually left:**

1. Read the four new Literature citations and confirm the characterisation
   of each is fair.
2. A full read-through of `report/main.tex` end to end, since it was written
   across sessions spanning weeks; check the voice is consistent.
3. Optional: expand Results §5.2 ("Two arms of the same question") with more
   classifier detail, from `threshold_sweep.csv`. Not a gap, just thinner
   than the rest of Results.
4. Decide when to send the complete draft to Dr Tian. Given the runway to
   early November, sending it now rather than polishing alone longer is
   probably worth more.

Everything above is committed to git. `PROJECT_STATUS.md` and
`supervisor_meeting_3_prep.pdf` still carry an older uncommitted edit from
before this session; not touched.

### Week 7, meeting with Dr Tian, 2 October. Everything below supersedes
### the writing plan above. Read this in full before writing anything.

Sent the progress report, the draft, and the code/data walkthrough on 30
September. Met in person on 2 October. The outcome changes the report's
required depth substantially, not just its content.

**1. The deadline is the last day of October 2026, confirmed directly.** Not
"early November" as this document assumed after the 30 September session. That
assumption was mine, not his, and it was wrong. Roughly four weeks from today.

**2. References: at least four full pages.** The current bibliography has
seven entries on about a third of a page. This is roughly an order of
magnitude short. Every one of the additional entries still needs CrossRef
verification before use; this is a large literature-search task, not a
formatting one, and it cannot be fabricated to hit a page count.

**3. The main instruction, repeated twice: focus on Methodology.** He named
two method families explicitly and wants them treated as the two pillars of
the section, not folded together as the current draft does:

- **(i) Machine learning** — ridge regression, random forest, gradient
  boosting, and the ARIMA classical benchmark arguably belongs in conversation
  with this group too, since it is the comparison point.
- **(ii) Deep learning** — the GRU.

For each of the two, he wants: the general features and theoretical
properties of the method family, and then specifically how this project
implemented it. Two passes, not one: what the method is, then what we did
with it.

**4. This is a mathematics degree, and the report must read like one.** Full
mathematical detail: algorithms, derivations, formulas, worked notation, not
prose summaries of what a model does. The current draft has almost none of
this; it describes models in words (for example, "ARIMA with annual Fourier
terms, fitted on the logarithm of concentration") without ever writing the
actual equations. This has to change throughout Methodology at minimum:
ridge regression's penalised least squares objective, the random forest
splitting criterion, gradient boosting's additive functional-gradient-descent
formulation, ARIMA's difference and AR/MA polynomial form with the Fourier
exogenous terms written out, and the GRU's full gate equations (reset gate,
update gate, candidate state, state update). The log/exp back-transform
mean-vs-median relationship already in the draft is the right level of
mathematical detail; the rest of Methodology needs to match it.

**5. A worked example was shown**, a previous student's report, 71 pages. Its
index (saved as reference) has a six-chapter structure: Introduction,
Literature Review (which has its own dedicated subsections per method family,
mirroring point 3), Methodology (same per-model subsections again, this time
implementation-focused — this double treatment, theory in Lit Review,
implementation in Methodology, is the pattern to copy), Results and Analysis,
Discussion, Conclusion, each as its own chapter with its own numbered
subsections, plus separate List of Figures and List of Tables pages. This was
shown as a calibration point for depth and structure, not necessarily a
template to copy chapter-for-chapter — judgement is needed on how much of the
formal six-chapter split to adopt versus how much to achieve by expanding the
existing seven-section report.

**What this means practically.** The 14-page draft was evaluated as a
complete, correctly-argued, but far too short treatment of a mathematics
capstone. The content is not wrong; it is insufficiently deep in exactly the
place (Methodology) that counts for the most marks, and insufficiently
supported by literature. Expanding Methodology with full mathematical
treatment of both method families, expanding Literature Review to carry
theoretical background on each method family (not just the four areas already
written), and growing References to four-plus real pages is the priority,
roughly in that order, within the four weeks available.

### Same day, later: the restructure done. Report is now 32 pages.

Chose, with the user, to adopt the full six-chapter thesis structure rather
than expand within the old seven-section shape. Converted
`\documentclass{article}` to `report`, added Abstract / Table of Contents /
List of Figures / List of Tables as roman-numbered front matter, and split
into Introduction, Literature Review, Methodology, Results and Analysis,
Discussion, Conclusion as proper chapters. All of the 30 September content is
preserved; nothing was cut.

**Introduction** expanded to six subsections: Background, Problem,
Objectives, Questions, Significance, Structure of the Report.

**Literature Review** gained two new theory sections, mirroring the
Methodology split: "Classical and Machine Learning Methods for Time Series
Forecasting" and "Deep Learning Methods for Time Series Forecasting" (the
latter with its own Recurrent Neural Networks / vanishing-gradient
subsection and a Gated Recurrent Unit subsection). Four new citations, all
CrossRef-verified: Hoerl & Kennard (1970, ridge regression), Friedman (2001,
gradient boosting), Cho et al. (2014, the GRU itself), Hochreiter &
Schmidhuber (1997, LSTM, cited for the vanishing-gradient problem it
addressed). Bibliography is now 11 entries, roughly one page — the 4-page
target is still open, see below.

**Methodology is the chapter that actually changed shape.** It now has an
explicit "Machine Learning Methods" section and a "Deep Learning Methods"
section, each covering the method's general form before this project's
specific configuration, per Dr Tian's repeated instruction. Full math added
throughout, checked against the actual implementation before writing (not
generic textbook description):

- ARIMA: the AR/I/MA backshift-polynomial form, specialised to the actual
  $(1,1,1)$ order with the four annual Fourier pairs written out as the
  exogenous term, and the log-normal median/mean back-transform as a
  derivation.
- Ridge regression: the penalised least-squares objective and its
  closed-form solution.
- Random forest: the bagged-ensemble averaging formula and the
  squared-error splitting criterion.
- Gradient boosting: the stagewise additive update and the
  functional-gradient-descent residual, including why it reduces to the
  ordinary residual under squared-error loss.
- The GRU: all four gate equations (update, reset, candidate state, state
  update), followed by the specific architecture actually fitted — confirmed
  directly against `step08_gru.py` rather than assumed: single `nn.GRU`
  layer, 24 hidden units, Adam optimiser, L1 (MAE) loss, early stopping on
  the last 15% of each training window as a chronological holdout.

Moved Reproducibility to the end of Methodology (it belongs with the methods
it describes, not dangling after the Conclusion).

**One real bug found and fixed in passing:** `make_tables.py`'s hardcoded
cleaning table had "sensitivity analysis in Section 6" baked in as a literal
string, which the restructure would have made wrong (that content is now in
Section 5.3). Replaced with a proper `\ref` to the Limitations section, so
it tracks automatically through any future restructuring instead of needing
to be remembered and hand-fixed again.

Compiles cleanly: zero undefined references, zero LaTeX warnings beyond one
cosmetic `xdvipdfmx` notice about a page-anchor name collision from the
roman/arabic numbering switch, which has no visible effect. Pushed to
`github.com/JC16092/mth5000-aqi-forecast` (commit `e90d941`).

### Week 7, same day, later still: References grown from 11 to 40 entries, 4 pages. Done.

The single largest open item from the meeting is now closed. Added 29 new
entries to `refs.bib` (11 to 40), every one found by a real CrossRef
bibliographic search and then verified by fetching its DOI record directly
from `api.crossref.org` and checking title/author/journal/year against what
was about to be cited, before writing a single word of prose against it.
This caught two near-misses that would otherwise have silently become
fabricated citations: a guessed DOI for the Guttikunda/Goel/Pant Delhi
emissions paper resolved to a completely unrelated satellite paper, and a
guessed DOI for the Miller 1984 log-transform bias paper resolved to an
unrelated "Comment" in the same journal issue. Both were re-found by title
search and the correct DOI substituted. One candidate (Chung et al.'s
empirical GRU-vs-LSTM comparison, an oft-cited NeurIPS workshop paper) was
dropped rather than cited, because it has no real Crossref-registered DOI
(workshop papers often don't) and this project holds citations to a higher
bar than "I'm fairly sure this is real."

The bibliography now compiles to exactly 4 pages (pages 35-38 of the 38-page
PDF), matching Dr Tian's "at least four full pages" instruction on the nose
rather than padding past it. Report grew from 32 to 38 pages overall. Zero
new LaTeX warnings, zero BibTeX warnings (every new entry has the fields it
needs), zero undefined references, zero overfull/underfull boxes. Not yet
committed or pushed to GitHub.

**Every new citation was woven into existing prose, not appended as a dangling
list** — each sits next to the specific equation, design choice, or claim it
supports:

- **Literature Review, classical/ML section**: Box & Jenkins for the ARIMA
  model itself (previously had no citation at all); De Livera, Hyndman &
  Snyder for the Fourier-terms-for-seasonality device; the bagging/CART/
  AdaBoost lineage underneath Breiman's random forest and Friedman's
  gradient boosting, plus XGBoost as the modern alternative implementation
  not used here; Zhang's hybrid ARIMA-ANN as the "why not combine them"
  counterpoint to this project's side-by-side comparison; Makridakis 2018
  (PLOS, the M3-era precursor to M4) and Makridakis 2022 (M5, where gradient
  boosting won decisively) bracketing the M4 finding with its precursor and
  its counterexample, reframed as "does the series offer exogenous/
  hierarchical structure to exploit" rather than "ML vs classical" in the
  abstract; Siami-Namini et al.'s direct ARIMA-vs-LSTM comparison; Tashman
  and Hewamalage et al. on single-split optimism (feeding directly into the
  rolling-origin justification); Hyndman & Koehler on MASE.
- **Literature Review, deep learning section**: Rumelhart/Hinton/Williams
  for backprop itself; Bengio/Simard/Frasconi for the actual original
  vanishing-gradient result (previously only Hochreiter & Schmidhuber was
  cited for this, which is really the LSTM solution, not the original
  problem statement); LeCun/Bengio/Hinton's Nature survey; Lim & Zohren's
  deep-learning-for-forecasting survey, which directly echoes this
  project's own "gain depends on whether there's structure to exploit"
  reading; Che et al. for the forward-fill-plus-missingness-indicator
  technique, which is exactly what `step08_gru.py` does and previously had
  no literature anchor.
- **Literature Review, verification section**: Schaefer for the CSI
  definition itself (reported in every results table, previously
  uncited); He & Garcia and Saito & Rehmsmeier for why plain accuracy and
  ROC are the wrong defaults on an imbalanced rare-event problem like this
  one.
- **Literature Review, Delhi section**: a new opening paragraph on
  Guttikunda/Goel/Pant (general Indian-city emission sources) and the
  satellite studies (Cusworth et al., Jethva et al.) that establish the
  stubble-burning mechanism Singh & Srivastava's paper assumes, stated
  explicitly as a limitation: this project infers the mechanism from
  seasonal structure in the series, it doesn't observe it directly the way
  the satellite studies do.
- **Introduction, Research Background**: Pope & Dockery and Chen & Hoek for
  the health-effects claim that was previously asserted with no citation at
  all ("regularly reaches concentrations classified as hazardous").
- **Methodology**: Box & Jenkins and De Livera et al. again at the actual
  ARIMA/Fourier equations (the "implementation" half of the double
  treatment Dr Tian asked for, mirroring the "theory" half in Lit Review);
  Miller 1984 attached directly to the log back-transform bias equation,
  which is the exact phenomenon his 1984 correction term addresses;
  bagging and CART cited at the random forest split criterion; AdaBoost and
  XGBoost cited at the gradient boosting update; backprop and the vanishing-
  gradient paper cited at the GRU's training description; Che et al. cited
  again at the GRU missingness-channel paragraph; Tashman and Hewamalage
  again at the rolling-origin design; Hyndman & Koehler, Schaefer, He &
  Garcia and Saito & Rehmsmeier at the Evaluation Measures section, each
  next to the specific measure they justify.
- **Data Quality section**: a new paragraph on Little & Rubin's missing-data
  framework (MCAR/MAR/MNAR), used to state explicitly which category this
  project is assuming when it carries short gaps forward rather than
  discarding them, a judgement that was previously made silently.
- **Research Gap and Chapter Summary**: lightly rewritten from "four bodies
  of literature" to "five" to reflect the new forecast-evaluation-
  methodology thread and the health/India-context thread, without
  rewriting the paragraph's actual argument.

### Same day, later again: the four Delhi/ML citations read, one real overclaim found and fixed, committed and pushed

Fetched the actual abstracts of all four 30-September Delhi/ML-vs-classical
citations (Masood & Ahmad 2020, Singh & Srivastava 2025, Makridakis et al.
2020/M4, Jiang et al. 2023) via the Semantic Scholar API after DOI
resolution to ScienceDirect/Springer/Taylor & Francis repeatedly hit bot
walls (Cloudflare CAPTCHA on PMC, a login redirect on Springer, a JS-only
shell on ScienceDirect, 403s on ResearchGate and Scribd). Full text proper
was not obtainable through any legitimate channel tried for any of the
four — Singh & Srivastava is genuinely paywalled with no open-access
version at all; the other three have "open access" PDF links on paper that
are themselves bot-gated. Abstract-level verification was still enough to
catch a real problem:

- **Singh & Srivastava 2025 was mischaracterised.** The report said their
  paper "frame[s] their evaluation around health risk rather than average
  error alone." Their actual abstract makes clear the paper does two
  separate things: a health-risk assessment of stubble-season PM2.5
  exposure using a dedicated risk model (AirQ+), and, separately, a
  comparison of three ML models (ANN, SVM-RBF, random forest) for PM2.5
  forecasting that is itself still scored by ordinary $R^2$/RMSE/MAE — the
  exact "average error alone" the sentence claimed they moved past. Fixed
  in `main.tex` to describe the two analyses as parallel rather than one
  nested in the other.
- **Masood & Ahmad 2020 was also loosely stated.** "Several regression
  models" was two (SVM and ANN), and — more substantively — their inputs
  are meteorological and pollutant covariates *at the forecast target day*,
  not the series' own lagged history, which is a different forecasting
  problem from this project's. Fixed to state both precisely, framed as a
  contrast with this project's own lagged-history-only setup rather than a
  throwaway correction.
- Masood & Ahmad, Jiang et al., and the M4 competition's abstracts all held
  up against what the report already claimed of them — no further changes.

**Full read-through of `report/main.tex`, start to end, done.** Surfaced
one more real error, unrelated to today's citation work and present since
at least the restructure: in the Rolling-Origin Evaluation section, the
sentence comparing the single-split and rolling-origin rMAE at h=1 had the
two numbers transposed, stating the ARIMA "scored 0.940 ... against 0.903
on the single block" when the true history (recorded correctly elsewhere
in this file) is the reverse — 0.903 on the single flattering split, 0.940
under the honest rolling-origin harness. Fixed. Otherwise the read-through
found the voice consistent throughout, including today's citation-dense
additions sitting comfortably against the older prose — no other changes
needed.

**Committed and pushed**, commit `70f2ded`: `refs.bib`, `main.tex`,
`PROJECT_STATUS.md`, `TODO.md`, and the rebuilt `main.pdf`. Left untouched
and unstaged, as out of scope for this session: `supervisor_meeting_3_prep.pdf`
(modified before this session, not by it) and a pile of untracked files
from earlier sessions (`PROJECT_LOGBOOK.pdf`, the three `MTH5000_*.pdf`
meeting documents, `build_logbook.py`, `build_meeting_agenda.py`,
`supervisor_meeting_3_agenda.pdf`, a `Claude outputs/` directory) plus the
usual LaTeX build byproducts (`main.aux`/`.blg`/`.fdb_latexmk`/`.fls`/`.log`/
`.out`, `report/tables/`, `.tmp` files) that this repo has never tracked.

### Same day, a third pass: the meteorological covariates extension, done

This was "Future Work" as of the previous pass, explicitly out of scope for
the submission and with no recorded sign-off from Dr Tian to add it. Decided,
with the user, to do it anyway as a full extension rather than a prototype.
**The finding changes the RQ1 story, not just a footnote.**

**What's new, mechanically.** `step02_features.py --weather` already existed
(written in an earlier session, never actually exercised) and merges six
`meteostat` variables (temperature, wind speed, pressure, precipitation,
each with a lag and a rolling mean) into the ML feature table; it needed
`meteostat` installed and a one-time macOS certificate fix
(`/Applications/Python 3.13/Install Certificates.command`) and pinning to
`meteostat==1.7.6` — the installed-by-default 2.1.5 has a completely
different API (`Daily` doesn't exist the way the code expects). `step08_gru.py`
did not have a weather path at all; added one: `build_channels()` now takes
an optional `weather` DataFrame and adds each column plus its own missing
flag, forward-filled exactly like the log-concentration channel, the same
construction `step02`'s version already used. One real bug on the way: the
weather columns come back from `meteostat` as pandas' nullable `Float64`,
which silently degrades a mixed-dtype DataFrame's `.values` to `object` and
breaks `torch`/`numpy` arithmetic downstream with a confusing error. Cast to
plain `float64` in `fetch_weather()` and it was a non-issue.

**A real, diagnosed data-quality defect, a third one for this project.**
The weather station record is 99.9%/99.6% complete (temperature/wind speed)
*within the window it covers*, but that window ends 202 days before the
PM2.5 series does — a reporting lag, not scattered gaps. Checked whether
this contaminates the finding below by also scoring the comparison
restricted to origins entirely inside the clean window: every result held.
Precipitation's own coverage (54%) was poor enough to drop it from the GRU
entirely; kept for the tree models, which take a sparse column natively.

**The finding.** Added two channels (wind speed, temperature) to the GRU and
all six `meteostat` variables to ridge/random forest/gradient boosting, reran
the full rolling-origin harness (ML suite: `forecasts_weather_ml.csv`; GRU:
5 fresh seeds, `gru_weather_seed{0-4}.csv`, in parallel, each finished in
under two minutes). Leak-tested three ways before trusting any of it
(corrupt PM2.5 after a cut, corrupt weather after a cut, corrupt both
through the full harness) — all pass, now permanently in `step08_gru.py
--test`.

Gradient boosting improves at every horizon (8.5/1.9/2.6 points of rMAE at
h=1/2/3). Ridge improves at h=1/2, worsens slightly at h=3. The random
forest is flat to worse, losing 5.0 points at h=3. The GRU is where it
matters most: it already beat ARIMA at h=1 only (the known result); with
weather it beats ARIMA under all 5 seeds at h=1, under 4 of 5 clearly at h=2
with the fifth a dead-heat tie (0.8825 vs 0.8827 — inside the report's own
documented 0.004 machine-noise floor, so reported as a tie, not a win), and
under 4 of 5 at h=3 (one outlier seed, 0.877, still loses to ARIMA's 0.832).
**h=2 was a clean ARIMA win before this; it no longer is.**

What this does *not* do: retest RQ3. The threshold sweep was not rerun with
any weather model, so whether the accuracy gain survives contact with an
alarm-budget constraint — given how compressed every model already was
there — is explicitly left open, in the report's own words, not quietly
skipped.

**Report changes**, all in `main.tex`, recompiled clean, 38 → 40 pages:
Methodology gained a "Weather Covariates" subsection (§3.3.4) carrying the
defect and the robustness check, and a paragraph in the GRU subsection;
Results gained a "Does Weather Change the Answer?" subsection with a new
table (`tables/weather.tex`, generated by a new `table_weather()` function
in `make_tables.py` — **no number in this section is hand-typed**, same
rule as everywhere else in the report); Limitations' old "no meteorological
covariate" paragraph was rewritten to state the three real boundaries
(observed weather only, no boundary layer height since `meteostat` doesn't
have it — contradicting what this file and the report both previously
assumed — and RQ3 not retested); Future Work rewritten around the four
things that are now the actual next steps; Main Conclusions and the
Abstract both updated to state the h=2 result changed. One pre-existing
inaccuracy fixed while writing this: a sentence claimed the weather-GRU
"beats ARIMA under every seed" at h=2, which the exact numbers don't
support once the noise floor is applied — corrected to the honest 4-clear-
plus-1-tie characterisation before it ever got committed.

### Same day, a fourth pass: the threshold sweep rerun with the weather models. RQ3 holds.

The natural next step flagged at the end of the previous pass, done the same
session. **This is the more important result of the two.**

**Mechanically.** `step07_warning.py`'s sweep needs one `--regression` file
containing every model to be compared; `forecasts_weather_ml.csv` and
`gru_weather_seed{0-4}.csv` reuse the *same* model names as the no-weather
baseline (`ridge`, `random_forest`, ...), which would collide on
`(origin, horizon, model)` if concatenated directly. Wrote
`build_weather_regression.py` to assemble one combined file per GRU seed —
the no-weather baseline unchanged, the five weather ML models renamed
`*_weather`, that seed's GRU renamed `gru_weather` — 15 models each,
`regression_weather_seed{0-4}.csv`. Ran `step07_warning.py` once per seed,
`--reuse-classification forecasts_classification.csv` so the direct
classification arm (unaffected by weather, not rebuilt) is only reused, not
refitted, the same pattern already established when GRU was first added.
18 models in total per sweep; `restrict_to_common` kept 20,610 of the
original rows. Produced `threshold_sweep_weather_seed{0-4}.csv`.

**The fair comparison, and why it needed its own script.** The naive thing,
comparing these new numbers against the old `threshold_sweep.csv`'s budget
table, would be comparing two different row samples, since adding 6 more
models to the common-origin intersection can only shrink it. Instead wrote
`compare_weather_threshold.py` (logic then ported into `make_tables.py` as
`table_weather_budget()`, so the report number is generated, not hand-typed)
to compute "best hit rate within budget B" **twice from the same sweep
file**: once restricted to only the original 12 models, once allowing all
18 — so the only variable between the two numbers is which models are
*candidates*, never which rows were scored.

**The finding: the gain is real but small, and the central thesis survives
being tested against its most accurate model.** At several budgets the
weather models don't even supply the best option (delta exactly zero: 40
and 60 alarms/yr at h=1, 60 and 80 at h=2). Where they do win, the best
improvement is 4.6 points of hit rate (h=3, budget 60); most wins are under
2 points. That's the same order as the five-point model-to-model spread
already established, not a new tier above it, and nowhere near the
fifty-point spread moving the budget itself buys. Gradient boosting's 8.5
points of accuracy gain (rMAE) at h=1 — a large number by this report's own
standards — buys at most a few points of hit rate once run through a
decision threshold. The alarm-budget-dominates finding was tested against
its own best shot at being wrong, and held.

**Report changes:** the "What this does not do is retest RQ3" paragraph in
§4.1.1 replaced with the actual retest, a new table (`tables/weather_budget.tex`,
Table 4.3) and its discussion; Limitations' three-boundaries paragraph
trimmed to two (RQ3 untested is no longer one of them) with a closing
sentence stating what was found instead; Future Work's "most immediate"
item (the threshold rerun) removed since it's done, the remaining two
weather items renumbered; Main Conclusions and the Results chapter summary
both updated to state the ceiling held. Recompiled clean, still 40 pages
(the new table fit without pushing the page count up).

**Not yet done at the time:** committing and pushing. Done in the next pass,
see below.

### Same day, a fifth pass: the Literature Review's deep learning landscape was too narrow

The user compared this report's Deep Learning Methods section in Chapter 2
against the 71-page reference report Dr Tian showed, and noticed a real
inconsistency: the reference report surveys MLP, CNN, LSTM, GRU and
Transformer as a family before narrowing down; this report only ever
covered the recurrent lineage (plain RNN to LSTM to GRU), never naming MLP,
CNN or Transformer at all. **This was an inconsistency with this report's
own established pattern, not a judgement call** — the Machine Learning
Methods literature already does the "name the siblings before choosing"
treatment (bagging and CART under random forest, AdaBoost under gradient
boosting, XGBoost as an unused alternative), and the deep learning side
should have matched it but didn't.

Fixed by adding a new first subsection, "The Deep Learning Landscape for
Time Series" (§2.3.1), before the existing RNN/vanishing-gradient
subsection, covering MLP (universal approximation
\citep{hornik1989universal}, the classic ANN-forecasting survey
\citep{zhang1998ann}), CNN (the foundational LeNet paper
\citep{lecun1998cnn}, a directly comparable seasonal-time-series-with-trends
application \citep{liu2020cnn}), and Transformer (the Temporal Fusion
Transformer \citep{lim2021tft} — note "Attention Is All You Need" itself
has no real Crossref DOI, NeurIPS doesn't register one, the search returned
obvious spam entries at a fake prefix; cited the TFT paper instead, which
describes the same self-attention mechanism in the course of applying it to
forecasting, rather than force an uncitable claim). Each architecture gets
a specific reason it was not chosen for this project — MLP needs the
sequence hand-engineered into lagged features already, a CNN's fixed
receptive field matters less here only because the Fourier terms already
carry the annual cycle, a Transformer's parameter count assumes a dataset
far larger than three thousand observations — so the GRU choice is now
justified against the whole field, not just against LSTM. References grew
from 40 to 45 entries; bibliography still lands on exactly 4 pages.
Recompiled clean, 40 pages (`mdls` count unchanged).

**The user also said explicitly: page count is not a constraint on this
report, up to 70 pages is fine.** Saved as a standing memory
([[feedback_mth5000_report_length]]) — stop treating page growth as a cost
when adding real content; Dr Tian's own calibration example was 71 pages.

**Committed and pushed, both this pass and the previous (threshold sweep)
pass together**, see below for the exact file list.

**What is still genuinely open, in priority order:**

1. Consider whether Results, Discussion, and Conclusion chapters would
   benefit from the same subsection granularity the reference report uses
   (cosmetic, low priority, unchanged from before).
2. Decide when to send the complete draft to Dr Tian, given roughly three
   and a half weeks of runway left to the 31 October deadline. Both weather
   passes and the literature-review fix are now complete; nothing currently
   known to be wrong or missing stands between this draft and sending it.
3. The 34 references added across the last two passes (29 + 5) are
   CrossRef-verified and spot-checked, not read full-text. Unchanged, still
   lower priority.

Positron as the editor, Python 3.13.15 in a `.venv` inside the project folder.
The system `python3` is a 3.14 alpha and must not be used. Activate with
`source .venv/bin/activate` from the project folder; the folder name contains a
space, so quote any absolute path.

## Data sources

- **OpenAQ** (primary, cite this): https://openaq.org, API docs at https://docs.openaq.org, free key required
- **CPCB daily bulletins** (official, PDFs, awkward to scrape): https://cpcb.nic.in/AQI_Bulletin.php
- **Kaggle CPCB-derived CSVs** (prototyping only, do not cite): search "Air Quality Data in India"
- **Weather:** the `meteostat` Python package, which wraps NOAA and GHCN station data

## Things already decided, do not relitigate

- Topic is settled. Dr Tian approved it. Stop second-guessing.
- Machine learning is the core approach, at his explicit request.
- SARIMA stays as a benchmark, not as the main method.
- One city, not many. Multi-city is future work.
- Deliverables are a report, figures and code. No app, no website, no dashboard.

## Known risks

- On a few thousand daily observations, deep learning may not beat gradient boosting or even SARIMA. This is well documented in forecasting competitions. A negative result is publishable *if* the evaluation is rigorous, so protect the evaluation above all.
- Rolling-origin evaluation is the fiddliest code in the project and the easiest place to accidentally leak future information into past forecasts. Write it carefully and test it on a short window first.
- Exceedance days are a minority class. Use precision-recall analysis and class weighting, not plain accuracy.
- Daily data has two seasonal periods, roughly 7 and roughly 365. SARIMA takes only one. Handle the annual cycle with Fourier terms as exogenous regressors. Worth confirming with Dr Tian.

## Style preferences for documents

- Plain academic formatting: Times serif, black only, no colour, no decorative rules.
- No em dashes anywhere.
- Title block carries full name, student ID, degree, unit code, supervisor, school.
- Every citation verified against CrossRef before use, never inferred.
