# MTH5000 BLUEPRINT: what happens, in what order, from now to submission

Jaykumar Vinodbhai Chauhan, 34710280. Master of Mathematics, Monash University.
Supervisor: Dr Tianhai Tian, School of Mathematics.
Project: Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities.

Written 20 August 2026. Nine weeks counted from today.

**Submission: Thursday 22 October 2026.** Confirm this against the unit guide in
week 1 and correct this file if it is wrong. Every date below moves with it.

The plan front-loads deliberately. The core project is finished at the end of
week 6, which leaves three weeks of slack. That is not padding. Two of those
weeks are writing and one is the buffer that absorbs whatever goes wrong,
because something will.

| Week | Dates | Objective | Gate at the end |
|---|---|---|---|
| 1 | Thu 20 Aug to Wed 26 Aug | Data in hand, viability settled | DONE 20 August. Dataset, cleaning and feature table all complete |
| 2 | Thu 27 Aug to Wed 2 Sep | Benchmarks and ARIMA | Naive, seasonal naive and ARIMA with Fourier exog scored on a fixed test split |
| 3 | Thu 3 Sep to Wed 9 Sep | Rolling-origin evaluation harness | Benchmarks rerun under rolling origin, numbers agree |
| 4 | Thu 10 Sep to Wed 16 Sep | Machine learning suite, regression arm | Ridge, random forest, gradient boosting scored at h=1,2,3 |
| 5 | Thu 17 Sep to Wed 23 Sep | Classification arm and the warning system | RQ2 and RQ3 answered, figure 6 exists |
| 6 | Thu 24 Sep to Wed 30 Sep | Neural network, final data swap, freeze | All results final, no more modelling |
| 7 | Thu 1 Oct to Wed 7 Oct | Write the first full draft | Complete draft to Dr Tian |
| 8 | Thu 8 Oct to Wed 14 Oct | Revise on his feedback | Second draft, all figures final |
| 9 | Thu 15 Oct to Wed 21 Oct | Polish, buffer, submit | Submitted, ideally Monday 19 October |

Aim to submit on **Monday 19 October**, three days early. Treat 22 October as
the hard wall, not the target.

---

# Before anything else: the setup checklist

Half a day, week 1. Do all of it before touching data.

**Accounts.** Two, both free, both take five minutes.

1. OpenAQ API key. Register at https://explore.openaq.org/register, then take
   the key from https://explore.openaq.org/account. It is passed in an
   `X-API-Key` header. Treat it like a password: put it in an environment
   variable, never in a file you commit.
2. Kaggle account, for the prototyping CSV only. You will not cite it.

**No AWS account is needed.** The OpenAQ bulk archive is a public S3 bucket
that reads without credentials. I verified the listing works anonymously while
writing this.

**Environment.**

```bash
mkdir -p ~/mth5000 && cd ~/mth5000
git init
python3 -m venv .venv && source .venv/bin/activate
pip install pandas numpy statsmodels matplotlib scipy scikit-learn \
            pmdarima meteostat requests
pip install awscli                      # only for the bulk archive route
pip freeze > requirements.txt
printf '.venv/\ndata/\n*.csv\n.env\n__pycache__/\n' > .gitignore
git add -A && git commit -m "Environment and step 1 and 2 scripts"
```

Put `step01_data_check.py` and `step02_features.py` in this folder. Commit at
the end of every working session, with a message saying what changed. When
something breaks in week 5, `git log` is how you find the afternoon it broke.

**Store the key outside the repo.**

```bash
echo 'export OPENAQ_KEY="paste-your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

# Week 1: get the data. Nothing else matters this week.

Everything downstream is written and tested. Real data is the only thing
standing between you and a running project, so this week has one job.

## Step 1.1: find the Delhi stations, and how far back each one goes

OpenAQ v3 is the source you cite. Find the monitoring locations within 25 km of
central Delhi that measure PM2.5. Parameter id 2 is pm25.

```bash
curl -s -H "X-API-Key: $OPENAQ_KEY" \
  "https://api.openaq.org/v3/locations?coordinates=28.6139,77.2090&radius=25000&parameters_id=2&limit=100" \
  > delhi_locations.json
```

Then read off, for each location, the `id`, the `name`, and `datetimeFirst` and
`datetimeLast`. Those two fields are the whole decision: they tell you the span
of record before you download a single measurement.

```python
import json
rows = json.load(open("delhi_locations.json"))["results"]
for r in sorted(rows, key=lambda r: r["datetimeFirst"]["utc"]):
    print(r["id"], r["datetimeFirst"]["utc"][:10], r["datetimeLast"]["utc"][:10], r["name"])
```

You want a station with at least four years and preferably six, still reporting
now. Write down the two or three best candidate ids. Delhi has many CPCB
monitors feeding OpenAQ, so you should have real choice.

The 25 km radius is the API maximum. If you want a wider net, use `bbox`
instead, or repeat the query around a second centre point.

## Step 1.2: pull the daily series

The v3 API aggregates to daily for you, which saves you writing that code.
First get the pm25 sensor id for your chosen location:

```bash
curl -s -H "X-API-Key: $OPENAQ_KEY" \
  "https://api.openaq.org/v3/locations/LOCATION_ID/sensors"
```

Then pull daily values, paginating until you have the full span:

```bash
curl -s -H "X-API-Key: $OPENAQ_KEY" \
  "https://api.openaq.org/v3/sensors/SENSOR_ID/days?date_from=2018-01-01&date_to=2026-08-20&limit=1000&page=1"
```

Rate limits are 60 requests per minute and 2,000 per hour, so a few thousand
days is nothing. Do not hammer it in a loop without a small sleep; repeatedly
blowing the limit can get a key banned.

**If the API truncates the history**, and it may, since OpenAQ has previously
capped how far back the live API serves, use the bulk archive instead. It is a
public S3 bucket, it needs no AWS account, and it holds the complete record:

```bash
aws s3 cp --no-sign-request --recursive --region us-east-1 \
  s3://openaq-data-archive/records/csv.gz/locationid=LOCATION_ID/year=2020/ data/
```

One gzipped CSV per location per day, roughly 1.5 MB for a year at one station.
Loop over the years you need, then concatenate and aggregate the hourly rows to
daily means yourself. The path pattern is
`records/csv.gz/locationid={id}/year={yyyy}/month={mm}/location-{id}-{yyyymmdd}.csv.gz`.
Files appear 72 hours after the end of each day, so the last three days are
always absent. That is expected, not a fault.

## Step 1.3: the prototyping shortcut, in parallel

While you are working out the API, download the Kaggle CPCB-derived dataset
"Air Quality Data in India (2015 to 2020)" by Rohan Rao. Its `city_day.csv`
gives you a clean daily Delhi series immediately.

Use it to get the entire pipeline running end to end this week. Swap in the
OpenAQ data in week 6 for the results you report. **Do not cite Kaggle in the
report.** Cite OpenAQ, and CPCB as the underlying authority.

This parallel track is the single most important scheduling decision in the
plan. It means an API problem costs you accuracy of sourcing, not weeks of time.

## Step 1.4: run the viability check

```bash
python step01_data_check.py --csv data/delhi.csv --value-col PM2.5
```

Read the verdict block. You need three years minimum and want six, under 20
percent missing, and no gap longer than 60 days. If the station fails, go back
to your candidate list and try the next one. This is a twenty minute loop, so
try three stations before settling.

Look hard at the periodogram output. You are checking that peaks near 7 and near
365 days are actually there rather than assumed. If the weekly peak is weak,
that is a finding, and it changes what you tell Dr Tian in step 1.6.

## Step 1.5: build the feature table

```bash
python step02_features.py --test
python step02_features.py --csv data/delhi.csv --value-col PM2.5 --out features.csv
```

Record the class balance line it prints. If exceedances are under 5 percent of
days, say so in week 2's supervision meeting, because it widens every confidence
interval in the project and may argue for the lower threshold.

## Step 1.6: settle the threshold, and email Dr Tian

Two things need his input before week 2, and they fit in one short email.

**The threshold.** The scripts currently use 121 ug/m3, the CPCB PM2.5
breakpoint where the category becomes "very poor". "Severe" starts at 250.
Verify both numbers against the CPCB national AQI documentation directly, not
against a secondary source, and put the citation in your notes now while you are
looking at it. Then choose, and justify the choice in terms of what the warning
is for. A warning that fires on merely bad days is a different instrument from
one that fires on emergency days, and the class balance you measured in 1.5 is
part of that argument.

**The two seasonal periods, now answered.** This was going to be the question
for him. It has been settled empirically instead, which is better. The weekly
cycle does not exist at this station: no periodogram peak near 7, no bump at lags
7, 14 or 21 in the deseasonalised log ACF, and a day of week spread of 6.5
percent with ANOVA p = 0.34. Bring him the finding rather than the question, with
the physical reading that a weekly cycle is a traffic signature and station 8118
is a diplomatic enclave monitor rather than a roadside site. Ask instead whether
he wants the structural state-space model as a comparison, which is now a
question about method rather than about necessity.

**Gate for week 1:** a real CSV that passes the coverage check, a feature table
built from it, and an email sent. If Friday arrives and you have no usable
station, fall back to the Kaggle series as the primary data source for now and
keep hunting in the background. Do not let data acquisition eat week 2.

---

# Week 2: benchmarks and SARIMA

The point of this week is to establish the numbers the machine learning has to
beat. A machine learning result with no reference point is uninterpretable, and
Dr Tian will ask.

**Write `step03_benchmarks.py`.** Three models, in increasing order of effort:

1. Naive: the forecast for t+h is the value at t.
2. Seasonal naive: the forecast for t+h is the value at t+h-7.
3. Climatology: the forecast is the historical mean for that day of year,
   smoothed. This one is often embarrassingly hard to beat at h=3.

**Write `step04_arima.py`.** Note the name. It is ARIMA with annual Fourier
terms as `exog`, not SARIMA, because the weekly cycle was tested for on 20 August
and is not there. See PROJECT_STATUS.md for the evidence. Do not add a weekly
seasonal order out of habit; if you do, you are fitting a component the data says
does not exist and you will have to defend it.

Work on log PM2.5. The series is strongly right skewed and annual Fourier terms
explain 69 percent of the variance in logs against far less on the raw scale.
Back-transform for reporting, and remember that the naive back-transform of a
log-scale mean forecast is a median, not a mean, so state which one you report.

Start with `pmdarima.auto_arima` for a defensible starting order, then refine by
hand from the ACF and PACF evidence. The deseasonalised log ACF decays 0.65,
0.43, 0.31, 0.23, which points at AR(2) or AR(3). Justify the final order from
the diagnostics, not from "auto_arima chose it". Check residuals with
`acorr_ljungbox`.

Use a simple fixed chronological split this week: train on the first 70 percent,
test on the last 15 percent, hold the middle 15 percent out for validation.
Leave at least three days between blocks so a target inside one is never a
feature in the next. The proper rolling-origin evaluation comes in week 3; this
week is about getting models that run at all.

**Metrics from the start.** MAE, RMSE, and MASE scaled against the naive
forecast. Report all three at h=1, 2 and 3 separately. Never average across
horizons, because the whole point is that skill decays with horizon.

**Gate:** a table of five numbers per model per horizon, checked into git.

---

# Week 3: the rolling-origin harness

This is the most dangerous week in the project. Your own risk register says so.
It is also the week that makes the results defensible, so do not rush it.

**Write `step05_rolling.py`.** The design, spelled out so you can check it:

- Expanding window. Start with the first three years as training, forecast the
  next day, then move the origin forward and refit.
- Refit cadence: refitting SARIMA every single day is slow. Refit weekly and
  update the state in between. Say in the report exactly what you did.
- At every origin, the model may see rows strictly up to that origin date and
  nothing after. The feature table's row convention already guarantees this at
  the feature level; the harness must not undo it by fitting on the whole table.
- Store every forecast as a row: origin date, horizon, model, predicted value,
  actual value. One long dataframe. Every metric, table and figure in the report
  is then a groupby on that one object, computed once.

**Test it on a short window first.** Ten origins, printed, checked by hand
against dates you compute yourself. Then scale up.

**The leakage test you must run.** Take a model, train it under the harness, and
also train it on a series where all values after some cut date have been
replaced with nonsense. Forecasts issued before the cut must be identical. This
is the same trick `step02_features.py --test` uses on features, applied to the
whole pipeline. If it fails, you have a leak, and finding it now instead of in
week 8 is the difference between a correction and a disaster.

**Gate:** week 2's benchmark numbers, rerun under the harness, giving sane
results. They will be slightly worse than the fixed split. That is expected and
correct; if they are dramatically better, you have a leak.

---

# Week 4: the machine learning suite, regression arm

Now the harness exists, adding a model is cheap. That is the payoff for week 3.

Fit each of these to predict the concentration at h=1, 2, 3:

- Penalised linear regression, ridge and lasso. One-hot encode day of week and
  month for these, and standardise the features. Lasso coefficients are a free
  feature-importance story for the report.
- Random forest.
- Histogram-based gradient boosting, `sklearn.ensemble.HistGradientBoostingRegressor`.
  This is the model most likely to win. Settled on 20 August: LightGBM and
  XGBoost both need an OpenMP shared library that macOS does not ship, and
  acquiring it means installing Homebrew. Scikit-learn's implementation is the
  same algorithm family, modelled on LightGBM, already installed, and handles
  NaN natively. Write it up as histogram-based gradient boosting; the
  implementation is a footnote.

**Hyperparameters.** Tune on the validation block only, never on test, and use a
small explicit grid you can print in an appendix. Do not use randomised search
with a large budget; you cannot defend numbers you cannot reproduce.

**Handle the NaNs correctly per model.** HistGradientBoosting takes them natively.
Ridge, lasso and random forest do not, so use `--dropna` or impute inside a
scikit-learn pipeline fitted on training data only. Imputing on the full table
before splitting is leakage, and it is a classic way to lose marks.

**Expect gradient boosting to beat the neural network, and possibly to beat
everything.** On a few thousand daily observations this is the well-documented
outcome. It is a legitimate result, not a failure.

**Gate:** RQ1 answered. A table of MAE, RMSE and MASE for every model at every
horizon, plus the forecast-versus-actual figure.

---

# Week 5: the classification arm and the warning system

This week answers RQ2 and RQ3, and it is where the project stops being a
modelling exercise and becomes an argument.

**The two arms of RQ2.**

- Arm A, forecast then threshold: take week 4's regression forecasts and apply
  the threshold to the predicted concentration.
- Arm B, direct classification: train classifiers on the `exceed_h1` to
  `exceed_h3` columns. Same models, logistic regression with penalty, random
  forest, gradient boosting.

Both arms come from the same feature table and run through the same harness, so
the comparison is clean. That was the point of building one wide table.

**Class imbalance.** Use class weights or `scale_pos_weight`. Do not oversample
a time series naively; duplicating minority days breaks the temporal structure.
Report precision, recall and average precision, never plain accuracy.

**The warning system, which is RQ3.** For each arm and horizon, sweep the
decision threshold from 0 to 1 and compute at each point: hit rate (recall),
false alarm rate, precision, and the number of alarms per year. That last one is
the number an actual operator cares about, and almost no paper reports it.

**Figure 6 is the figure that carries the project.** Hit rate against false alarm
rate, one curve per model, one panel per horizon, with the operating points of
the naive benchmarks marked. Build it this week, not in week 7.

**Gate:** RQ2 and RQ3 answered, figure 6 drafted.

---

# Week 6: neural network, final data, freeze

**The LSTM or GRU.** One model, small, properly regularised. Sequence length 30
days, one or two layers, dropout, early stopping on the validation block. Do not
spend more than three days on it. If it underperforms gradient boosting, report
that honestly with the sample size as the explanation. That is the expected
outcome and a defensible finding.

**The KAN is a stretch goal.** Dr Tian published on Kolmogorov-Arnold Networks in
November 2025, so attempting it is a genuine courtesy to your supervisor and a
good talking point. Attempt it only if the LSTM is done by Wednesday of this
week. If you do attempt it, read his paper first and cite it.

**Swap the data.** If you have been prototyping on the Kaggle series, this is
when you rerun everything on the properly sourced OpenAQ data. If the pipeline
is clean this is a one-line change and an afternoon of compute. Verify that
conclusions are stable across the two sources. If they are not, that is itself
worth a paragraph.

**Freeze on Wednesday 30 September.** After that date, no new models, no new
features, no new tuning. Everything else is writing. Projects fail at this
transition far more often than they fail at the modelling.

---

# Weeks 7 and 8: writing

**Confirm the required length and structure from the unit guide.** I could not
retrieve the MTH5000 assessment breakdown, so check whether there is a
presentation component and what weight it carries, and put the answer at the top
of PROJECT_STATUS.md. Do this in week 1, not week 7.

Suggested structure, adjust to the unit's requirements:

| Section | Content | Rough share |
|---|---|---|
| Introduction | Delhi air quality, why hazardous days specifically, the warning framing | 10% |
| Literature | Air quality forecasting, ML in time series, warning system evaluation | 15% |
| Data | OpenAQ, station choice, coverage, missingness, the threshold decision | 10% |
| Methodology | Feature construction, every model, rolling origin, metrics | 25% |
| Results | RQ1, RQ2, RQ3 in order, tables and figures | 25% |
| Discussion | Why gradient boosting wins, what the false alarm rate means in practice | 10% |
| Conclusion | Limitations, one city, future work | 5% |

Write the methodology section first. It is the longest, it is the least
dependent on the results reading well, and you have already made every decision
in it. Introduction and literature go last.

**Every citation verified against CrossRef before it goes in.** Never infer a
reference. This is already your rule; the point is that week 7 is when it is
most tempting to break it.

Send the full draft to Dr Tian at the end of week 7. Give him a full week. Do not
send him a partial draft in week 6 and a different one in week 7; supervisors
review far better once, properly.

---

# Week 9: buffer and submit

Polish, final figure regeneration at publication resolution, reference check,
formatting against the style rules, and a full read-through on paper rather than
on screen.

Submit Monday 19 October. The remaining days are for the thing you have not
thought of yet.

---

# Supervision

Meet or email Dr Tian at these points, with a specific question each time:

- **End of week 1:** threshold choice, and the two seasonal periods question.
- **End of week 3:** show him the rolling-origin design before you build every
  model on top of it. A structural flaw found here costs a day; found in week 6
  it costs the project.
- **End of week 5:** show him figure 6. This is the intellectual core, and his
  reaction tells you what the discussion section needs to argue.
- **End of week 7:** the full draft.

Bring a one-page summary of results to each meeting. Never arrive with only
questions.

---

# Risk register, with triggers

| Risk | Trigger to watch for | What you do |
|---|---|---|
| No station with adequate coverage | Three stations fail the week 1 check | Use the Kaggle CPCB series as primary and say so explicitly in the data section. Widen to a second city only as a last resort. |
| OpenAQ API truncates history | The days endpoint returns only recent months | Switch to the S3 bulk archive. It is complete and needs no account. |
| Exceedances under 5 percent of days | The class balance line in step 2 | Lower the threshold to the "poor" breakpoint and report both, or frame the project around the lower threshold with the severe case as a sensitivity analysis. |
| Deep learning underperforms | Week 6 LSTM loses to gradient boosting | Report it. Cite the forecasting-competition literature. Protect the evaluation and this becomes a finding rather than a failure. |
| Leakage discovered late | Test-set results look implausibly good | Run the week 3 leakage test again after every pipeline change. Implausibly good is a symptom, not a success. |
| Time runs out | End of week 6 and modelling is not frozen | Cut the KAN, then the LSTM, then the structural model. Never cut the rolling-origin evaluation or figure 6. |

---

# What "done" looks like

- One city, one station, a daily PM2.5 series of at least four years from OpenAQ.
- Benchmarks, SARIMA, three machine learning regressors, three classifiers, one
  neural network, all evaluated under one rolling-origin harness.
- RQ1, RQ2 and RQ3 each answered with a table and a figure.
- Figure 6, hit rate against false alarm rate, with benchmark operating points.
- A report in the required format, every citation CrossRef-verified.
- A git repository that reruns the whole thing from raw data to figures.

The thing that makes this project good is not the model that wins. It is that
the evaluation is honest enough that whichever model wins, the answer means
something. Protect the evaluation above everything else.
