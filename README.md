# Machine Learning for Forecasting Hazardous Air Quality Days in Indian Cities

MTH5000 Masters Research Project, Monash University.
Jaykumar Vinodbhai Chauhan (Student ID 34710280), Master of Mathematics.
Supervisor: Dr Tianhai Tian, School of Mathematics.

The full report is [`report/main.pdf`](report/main.pdf). This README covers the code only.

## What this project does

Forecasts daily PM2.5 one to three days ahead at a single Delhi monitor, and
evaluates every model not just on average error but as a hazard warning
system (hit rate, false alarm rate, and the alarm-budget trade-off). Three
research questions, answered in the report:

1. How accurately can concentrations be forecast 1–3 days ahead by machine
   learning, versus classical and naive benchmarks?
2. Is it better to forecast the concentration then threshold it, or to
   classify the exceedance event directly?
3. As a warning system, what hit rate and false alarm rate does each
   approach achieve, and how does the decision threshold trade them off?

The central finding: the alarm budget an operator accepts determines warning
performance far more than which model is used.

## Setup

Requires Python 3.13 specifically (not 3.14 — see the comment at the top of
`requirements.txt`).

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On macOS, `meteostat` (used for the weather extension) needs a one-time
certificate fix before its first live fetch:

```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

## Project layout

```
data/                       raw and cleaned PM2.5 series
step00_fetch_openaq.py      downloads the raw series from OpenAQ
step01_data_check.py        viability check: ADF test, periodogram, ACF/PACF
step01b_clean.py            reports and (when told) removes impossible values
step02_features.py          builds the supervised feature table (--weather for the weather extension)
evaluation.py                shared scoring module; every model is scored by this and nothing else
step03_benchmarks.py        persistence, seasonal-naive, climatology
step04_arima.py             ARIMA with annual Fourier terms (single-split benchmark)
step05_rolling.py           the rolling-origin evaluation harness
step06_ml.py                ridge, random forest, gradient boosting (level and change targets)
step07_warning.py           direct classification arm + the decision-threshold sweep
step08_gru.py               the recurrent network (--weather for the weather-augmented variant)
make_figures.py             every figure in the report, generated from the result files
build_weather_regression.py assembles the combined weather-vs-no-weather comparison files
compare_weather.py          console sanity check: weather vs. no-weather GRU accuracy
compare_weather_threshold.py console sanity check: does the weather accuracy gain survive the threshold sweep
report/
  main.tex                  the report source
  make_tables.py            every table in the report, generated from the result files
  refs.bib                  bibliography, CrossRef-verified
  figures/                  copied here automatically by make_tables.py
  main.pdf                  the compiled report
```

Every `stepXX_*.py` script takes `--test`, which runs that script's own
correctness checks (including a leakage test — corrupt the series from a
chosen date, rebuild, assert nothing before that date changed) and exits
without fitting anything. Run `python stepXX_name.py --test` for any of them
before trusting their output.

## Reproducing the whole project from the cleaned data

```bash
source .venv/bin/activate

# Features, with and without weather
python step02_features.py --csv data/delhi_clean.csv --value-col PM2.5 --fourier 4 --out features.csv
python step02_features.py --csv data/delhi_clean.csv --value-col PM2.5 --fourier 4 --weather --out features_weather.csv

# Benchmarks, ARIMA, the rolling-origin harness, the ML suite (with and without weather)
python step03_benchmarks.py --csv data/delhi_clean.csv --out forecasts_benchmarks.csv
python step04_arima.py --csv data/delhi_clean.csv --benchmarks forecasts_benchmarks.csv --out forecasts_classical.csv
python step05_rolling.py --csv data/delhi_clean.csv --window expanding --out forecasts_rolling.csv
python step06_ml.py --csv data/delhi_clean.csv --features features.csv --out forecasts_all.csv
python step06_ml.py --csv data/delhi_clean.csv --features features_weather.csv --no-arima --out forecasts_weather_ml.csv

# GRU, 10 seeds, base and weather (fast enough to run in parallel)
for N in 0 1 2 3 4 5 6 7 8 9; do
  python step08_gru.py --csv data/delhi_clean.csv --features features.csv --seed $N \
         --existing forecasts_all.csv --out gru_seed${N}.csv &
done
wait
for N in 0 1 2 3 4 5 6 7 8 9; do
  python step08_gru.py --csv data/delhi_clean.csv --features features_weather.csv --weather --seed $N \
         --existing forecasts_all.csv --out gru_weather_seed${N}.csv &
done
wait
cp gru_seed0.csv forecasts_with_gru.csv

# Direct classification arm, fit once
python step07_warning.py --csv data/delhi_clean.csv --features features.csv \
       --regression forecasts_all.csv --out-clf forecasts_classification.csv \
       --out-sweep /tmp/discard_sweep.csv

# Threshold sweeps: the main one, per-seed GRU range, and the weather comparison
python step07_warning.py --regression forecasts_with_gru.csv \
       --reuse-classification forecasts_classification.csv --out-sweep threshold_sweep.csv
for N in 0 1 2 3 4 5 6 7 8 9; do
  python step07_warning.py --regression gru_seed${N}.csv \
         --reuse-classification forecasts_classification.csv \
         --out-sweep threshold_sweep_gru_seed${N}.csv
done
python build_weather_regression.py
for N in 0 1 2 3 4 5 6 7 8 9; do
  python step07_warning.py --regression regression_weather_seed${N}.csv \
         --reuse-classification forecasts_classification.csv \
         --out-sweep threshold_sweep_weather_seed${N}.csv
done

# Every table and figure in the report, from the result files above
python report/make_tables.py
python make_figures.py

# The report itself
cd report && tectonic main.tex
```

No number in the report is typed by hand — every table is generated by
`report/make_tables.py` directly from these result files, and every figure
by `make_figures.py`. Rerunning the block above regenerates all of them.

To rebuild `data/delhi_clean.csv` itself from nothing, see the "Rebuild it
from nothing with" section of `PROJECT_STATUS.md`, which also has the full,
dated account of every decision made in this project, including several
genuine data defects found and fixed along the way (a clipped instrument
ceiling, a miscalculated coverage statistic, and a GRU reproducibility gap
discovered on a full pipeline rerun).

## Data

`data/delhi_clean.csv`: 3,093 usable daily PM2.5 means, 9 November 2016 to
27 August 2026, OpenAQ location 8118 (sensor 23534), supplied through the
AirNow network — not the Indian CPCB network, whose own stations return data
only from February 2025 through this endpoint. This limitation, and why the
station was chosen anyway, is discussed in the report's Limitations section.
`data/delhi.csv` is the raw download; `data/delhi_clean_nocap.csv` is the
cleaned series without the upper cleaning threshold, used for the
sensitivity check in Limitations.
