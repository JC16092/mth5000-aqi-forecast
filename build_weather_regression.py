"""
Scratch script: assemble one combined regression file per GRU seed, so
step07_warning.py's threshold sweep can see the weather models side by side
with the existing non-weather ones under a single set of model names.

Needed because forecasts_weather_ml.csv reuses the same model names as
forecasts_all.csv (ridge, random_forest, hist_gbm, ...) for the weather
variants, which would collide on (origin, horizon, model) if concatenated
directly. Renamed here with a "_weather" suffix instead.

    python build_weather_regression.py

Writes regression_weather_seed{0..4}.csv, one per GRU weather seed, each
containing: every model in forecasts_all.csv unchanged (the no-weather
baseline, including ARIMA and benchmarks, as context), the five weather ML
models renamed *_weather, and that seed's GRU weather forecasts renamed
gru_weather.
"""
import glob

import pandas as pd

ML_WEATHER_MODELS = ["ridge", "random_forest", "random_forest_delta",
                     "hist_gbm", "hist_gbm_delta"]


def main():
    base = pd.read_csv("forecasts_all.csv", parse_dates=["origin"])

    weather_ml = pd.read_csv("forecasts_weather_ml.csv", parse_dates=["origin"])
    weather_ml = weather_ml[weather_ml.model.isin(ML_WEATHER_MODELS)].copy()
    weather_ml["model"] = weather_ml["model"] + "_weather"

    seeds = sorted(glob.glob("gru_weather_seed*.csv"))
    for f in seeds:
        n = f.replace("gru_weather_seed", "").replace(".csv", "")
        gru = pd.read_csv(f, parse_dates=["origin"])
        gru = gru[gru.model == "gru"].copy()
        gru["model"] = "gru_weather"

        combined = pd.concat([base, weather_ml, gru], ignore_index=True)
        dup = combined.duplicated(["origin", "horizon", "model"]).sum()
        if dup:
            raise SystemExit(f"{dup} duplicate (origin, horizon, model) rows "
                             f"building seed {n}; fix before sweeping.")
        out = f"regression_weather_seed{n}.csv"
        combined.to_csv(out, index=False)
        print(f"  wrote {out}: {combined['model'].nunique()} models, "
              f"{len(combined)} rows")


if __name__ == "__main__":
    main()
