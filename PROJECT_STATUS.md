# PROJECT STATUS: read this first

Handover note so a new conversation can pick up without re-reading everything.
For the schedule and the step by step plan, see `BLUEPRINT.md`.
Last updated: 20 August 2026, end of day one.

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

### Immediate next steps

Week 1 finished on 20 August, six days early. Set up git, then week 2:
benchmarks and ARIMA with Fourier exog, on log PM2.5.

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
