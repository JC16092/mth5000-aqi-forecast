# PROJECT STATUS: read this first

Handover note so a new conversation can pick up without re-reading everything.
For the schedule and the step by step plan, see `BLUEPRINT.md`.
Last updated: 20 August 2026. Weeks 1 and 2 both complete on day one.

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
| `software_setup_guide_aqi_forecast.md` | Data sources, packages, working order for this project |
| `data/delhi_clean.csv` | THE dataset. 3,093 usable days, 2016-11-09 to 2026-08-27. Built from `data/delhi.csv` by step 1b. |
| `data/delhi.csv` | Raw download, kept so the cleaning can be rerun with different thresholds. |
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

### Immediate next steps

Week 6: the recurrent network, then freeze. Given the finding above, the honest
expectation is that it changes nothing material, and the report should say so.
Do not let it eat more than three days. Then the sensitivity run without
`--max-value 1000`, and modelling stops on 30 September.

### Environment, settled

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
