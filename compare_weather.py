"""
Scratch script: does adding meteostat weather (wind speed, temperature) change
anything? Not part of the tracked pipeline that feeds the report's tables -
this is the exploratory comparison that decides whether the extension is worth
writing up, and if so, what numbers to quote.

    python compare_weather.py

Reads the already-existing baseline forecasts (forecasts_all.csv, gru_seed*.csv)
and the weather-enabled runs produced this session (forecasts_weather_ml.csv,
gru_weather_seed*.csv), scores both with the exact same evaluation.py machinery
and the exact same burn-in used everywhere else in this project, and prints a
side by side rMAE table per model and horizon.
"""
import glob

import pandas as pd

from step01_data_check import load_series
import evaluation as ev

BURN_IN = 1095
ML_MODELS = ["ridge", "random_forest", "random_forest_delta",
             "hist_gbm", "hist_gbm_delta"]


def score(path, scale, reference="naive_carry"):
    d = pd.read_csv(path, parse_dates=["origin"])
    return ev.regression_metrics(d, scale, reference=reference)


def gru_range(pattern, scale):
    files = sorted(glob.glob(pattern))
    if not files:
        return None, 0
    rows = {}
    for f in files:
        g = score(f, scale)
        rows[f] = g[g.model == "gru"].set_index("horizon")["rMAE"]
    return pd.DataFrame(rows), len(files)


def main():
    s = load_series("data/delhi_clean.csv", "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[BURN_IN]].values)

    base = score("forecasts_all.csv", scale)
    weather = score("forecasts_weather_ml.csv", scale)

    base_gru, n_base = gru_range("gru_seed*.csv", scale)
    weather_gru, n_weather = gru_range("gru_weather_seed*.csv", scale)

    print(f"{'Model':<24}{'h':>3}  {'rMAE (no weather)':>18}  "
          f"{'rMAE (with weather)':>20}  {'delta':>8}")
    print("-" * 80)
    for h in (1, 2, 3):
        for name in ML_MODELS:
            b = base[(base.model == name) & (base.horizon == h)]["rMAE"]
            w = weather[(weather.model == name) & (weather.horizon == h)]["rMAE"]
            if len(b) and len(w):
                bv, wv = float(b.iloc[0]), float(w.iloc[0])
                print(f"{name:<24}{h:>3}  {bv:>18.4f}  {wv:>20.4f}  {wv - bv:>+8.4f}")
        if base_gru is not None and weather_gru is not None:
            bv_lo, bv_hi = base_gru.loc[h].min(), base_gru.loc[h].max()
            wv_lo, wv_hi = weather_gru.loc[h].min(), weather_gru.loc[h].max()
            print(f"{'gru (' + str(n_base) + ' seeds)':<24}{h:>3}  "
                  f"{bv_lo:>8.4f}-{bv_hi:<8.4f}  "
                  f"{'gru (' + str(n_weather) + ' seeds)':<0}"
                  f"{wv_lo:>11.4f}-{wv_hi:<8.4f}")
        print()

    # Reference: ARIMA is unaffected by this extension by construction (its
    # exogenous terms must be known at the forecast horizon, which future
    # weather is not), so it is not re-run here. Quote it from the existing
    # baseline for context only.
    arima = base[(base.model == "arima_fourier")].set_index("horizon")["rMAE"]
    print("For context, ARIMA + Fourier (unaffected, not rerun):")
    print(arima.to_string())


if __name__ == "__main__":
    main()
