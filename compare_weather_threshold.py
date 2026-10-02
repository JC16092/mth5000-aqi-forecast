"""
Scratch script: does adding weather models to the threshold sweep widen the
achievable hit rate at a fixed alarm budget?

Reads threshold_sweep_weather_seed{0..4}.csv, each of which already contains
both the original (no-weather) models and the weather models scored on the
SAME common-origin set (restrict_to_common ran once, over all 18 models
together). So the two "best hit rate at budget B" numbers below are computed
from the same rows; the only difference is whether weather models are
candidates. That is the fair, single-variable comparison, as distinct from
just comparing against the old threshold_sweep.csv, which was scored on a
different (larger) common set.

    python compare_weather_threshold.py
"""
import glob

import pandas as pd

from step07_warning import operating_point_at_alarms

NO_WEATHER_MODELS = {"naive_carry", "seasonal_naive_7", "climatology",
                     "arima_fourier", "ridge", "random_forest",
                     "random_forest_delta", "hist_gbm", "hist_gbm_delta",
                     "logistic", "forest_clf", "hgb_clf"}
BUDGETS = (40, 60, 80, 100)


def best_at_budget(sweep, horizon, budget, models):
    best = None
    for m in models:
        op = operating_point_at_alarms(sweep, m, horizon, budget)
        if op is not None and (best is None or op["hit_rate"] > best[0]):
            best = (op["hit_rate"], m)
    return best


def main():
    files = sorted(glob.glob("threshold_sweep_weather_seed*.csv"))
    for h in (1, 2, 3):
        print(f"=== h={h} ===")
        print(f"{'budget':>7}  {'no weather':>12}  {'with weather':>24}  {'delta':>7}")
        for budget in BUDGETS:
            no_wx_vals, wx_vals, wx_models = [], [], []
            for f in files:
                sweep = pd.read_csv(f)
                all_models = set(sweep.model.unique())
                nb = best_at_budget(sweep, h, budget, NO_WEATHER_MODELS & all_models)
                wb = best_at_budget(sweep, h, budget, all_models)
                if nb:
                    no_wx_vals.append(nb[0])
                if wb:
                    wx_vals.append(wb[0])
                    wx_models.append(wb[1])
            if no_wx_vals and wx_vals:
                nb_mean = sum(no_wx_vals) / len(no_wx_vals)
                wb_mean = sum(wx_vals) / len(wx_vals)
                print(f"{budget:>7}  {nb_mean:>12.3f}  {wb_mean:>24.3f}  "
                      f"{wb_mean - nb_mean:>+7.3f}   winners: {sorted(set(wx_models))}")
        print()


if __name__ == "__main__":
    main()
