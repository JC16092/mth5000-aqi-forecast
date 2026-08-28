# Software and data setup: AQI forecasting project

For the proposal "Forecasting Hazardous Air Quality Days in Indian Cities". Everything is free, runs on a laptop, and needs no fieldwork. Outputs are a written report, static figures, and reproducible code. No app or website.

## Before anything else: the viability check

Do this in your first sitting, before committing to the topic.

Pull daily PM2.5 for your intended city and date range, plot it, and count the missing days. You are looking for a long enough continuous run (several years) with gaps that are scattered rather than one huge hole. If a station is badly incomplete, try another station in the same city. Twenty minutes here decides whether the project is viable, and it is the single most useful thing you can do early.

---

## Data

### Primary: OpenAQ

Free, research-oriented, holds historical Indian station data including many Delhi monitors. This is the source you cite.

- Platform: https://openaq.org
- API docs: https://docs.openaq.org (free API key, register on the site)
- Bulk archive on AWS S3: linked from the docs, better if you want several years at once without rate limits

### Official: CPCB

The government source. Accurate but awkward: daily AQI bulletins are published as PDFs, so a multi-year series means scraping and parsing hundreds of documents.

- Daily bulletins: https://cpcb.nic.in/AQI_Bulletin.php
- Real-time feed via data.gov.in: https://www.data.gov.in/resource/real-time-air-quality-index-various-locations (current readings only, not historical)

Treat CPCB as a cross-check on a sample of dates rather than your main pipeline.

### Prototyping shortcut

There are well-known CPCB-derived city-wise daily CSVs on Kaggle covering roughly 2015 to 2020. Search "Air Quality Data in India".

Use one of these in week one to get the entire analysis working end to end on clean data, then swap in properly sourced OpenAQ data for the results you actually report. Prototyping on the convenient file is sensible; citing Kaggle in the report is not. Cite OpenAQ or CPCB.

### Meteorology (optional extension only)

The `meteostat` package is by far the easiest route, wrapping NOAA and GHCN station data:

```python
from meteostat import Daily, Point
delhi = Point(28.61, 77.21)
met = Daily(delhi, start, end).fetch()
```

ERA5 reanalysis via the Copernicus Climate Data Store is more rigorous but considerably more work. Only go there if the project is running ahead of schedule.

---

## Software

Python throughout. One reason above all: `statsmodels` covers every method in the proposal in a single library, and its state-space framework handles missing observations natively by skipping the measurement update at gaps. That is exactly the argument Section 3 of the proposal makes, so the tool matches the methodology rather than working around it.

```bash
pip install pandas numpy statsmodels matplotlib scipy pmdarima scikit-learn meteostat
```

| Tool | Purpose | Proposal step |
|---|---|---|
| `statsmodels.tsa.stattools.adfuller` | Augmented Dickey-Fuller test | Step 1 |
| `statsmodels.graphics.tsaplots.plot_acf`, `plot_pacf` | ACF and PACF | Step 1 |
| `scipy.signal.periodogram`, `welch` | Spectral density, identifying cycles | Step 1 |
| `statsmodels.tsa.statespace.SARIMAX` | Seasonal ARIMA, Kalman-based, accepts NaN | Step 3 |
| `pmdarima.auto_arima` | Automated order search as a starting point | Step 3 |
| `statsmodels.tsa.statespace.UnobservedComponents` | Structural level, seasonal, irregular model | Step 4 |
| `statsmodels.stats.diagnostic.acorr_ljungbox` | Residual autocorrelation test | Step 3 |
| `sklearn.metrics.confusion_matrix` | Hits, misses, false alarms | Step 5 |

R is a viable alternative (`forecast`, `fable`, `KFAS`, `tseries`) but you would spread the same work across more packages for no gain.

---

## One genuine modelling decision to make early

Daily pollution data has two seasonal periods: roughly 7 days (weekly, from traffic and industry) and roughly 365 days (annual, from meteorology and seasonal burning). SARIMA handles one seasonal period, not two.

The two standard fixes:

1. Model the weekly cycle as the SARIMA seasonal component, and capture the annual cycle with Fourier terms passed in as exogenous regressors (`exog` in SARIMAX).
2. Use the structural model, where several seasonal components can sit side by side in the state vector.

This is a real modelling choice rather than a mechanical step, and it is a good thing to raise with Dr Tian. Option 2 also strengthens the case for the state-space half of the project.

---

## Figures to produce

1. The full daily series, with hazardous-threshold episodes shaded.
2. Periodogram or smoothed spectral density, showing the weekly and annual peaks explicitly.
3. ACF and PACF before and after differencing.
4. Forecast against actuals over the test period, with prediction intervals, at each horizon.
5. Structural decomposition: estimated level, seasonal and irregular components separately.
6. Warning-system performance: hit rate against false alarm rate as the decision threshold varies.

Figure 6 is the one that carries the argument. Everything before it is standard; that plot is what makes the project about a decision rather than about a model fit.

---

## Suggested working order

1. Viability check (above). Do not skip.
2. Load a prototype CSV, get a clean daily series with a proper date index, handle duplicates and obvious sensor errors.
3. Exploratory analysis: plot, ADF test, ACF/PACF, periodogram. Confirm the weekly and annual cycles exist before assuming them.
4. Fit SARIMA. Start with `auto_arima` to get a sensible baseline, then refine by hand from the ACF/PACF evidence and justify your final choice.
5. Fit the structural state-space model. Compare its decomposition against what you saw in step 3.
6. Build the rolling-origin evaluation. This is fiddly code; write it carefully and test it on a short window first.
7. Convert forecasts to warnings, build the contingency tables, sweep the threshold.
8. Swap the prototype data for properly sourced OpenAQ data and rerun. If the pipeline is written cleanly this should be a one-line change.

Step 6 is where most of the real programming effort lives. Rolling-origin forecasting means refitting or updating the model at each step and forecasting forward, which is easy to get subtly wrong in ways that leak future information into past forecasts. Guard against that explicitly.

---

## Scale

Roughly 2,000 to 3,000 daily observations for one city over several years. Everything fits in memory and runs in seconds. No GPU, no cloud, no paid software, no registration beyond a free OpenAQ key.

## Version control

Use git from the start, even working alone. A private GitHub repository is free, and being able to undo a bad afternoon is worth the five minutes of setup.
