"""
MTH5000 - ARIMA coefficient stability across the rolling-origin harness.

A follow-up to a PhD-scholar review finding: the AR(1)/MA(1) coefficients
and AIC gap reported in Methodology (phi_1=0.581, theta_1=-0.987, chosen
order (1,1,1) against a runner-up at AIC 1893.6) come from a single
one-time fit in step04_arima.py's original single-split pipeline, not from
the rolling-origin harness that actually produces Table 4.1's numbers.
That harness (step06_ml.py, via the Arima class and rolling_origin shared
with every other model) re-estimates ARIMA's coefficients every 90 days
across roughly seven years of expanding-window refits, at a fixed order,
(1,1,1), chosen once and never re-searched at any later refit.

This script subclasses Arima to record phi_1, theta_1, sigma2 and AIC at
every one of those refits, run under the exact configuration that produced
forecasts_all.csv (burn-in 1095, expanding window, refit every 90 days,
order (1,1,1)), and reports whether the single reported snapshot is
representative of the whole evaluation or whether it drifts.

    python arima_coefficient_stability.py
"""

import sys

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series
    from step03_benchmarks import HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Arima, rolling_origin
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4 and 5 beside this script. {e}")


class LoggingArima(Arima):
    """Identical to Arima, but records phi_1, theta_1, sigma2 and AIC at
    every refit rather than only exposing the final filter state."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = []

    def start(self, y_hist, exog_hist):
        super().start(y_hist, exog_hist)
        p = self.res.params
        self.log.append({
            "refit_origin": y_hist.index[-1],
            "n_train": int(y_hist.dropna().shape[0]),
            "phi_1": float(p.get("ar.L1", np.nan)),
            "theta_1": float(p.get("ma.L1", np.nan)),
            "sigma2": float(p.get("sigma2", np.nan)),
            "aic": float(self.res.aic),
            "converged": bool(self.res.mle_retvals.get("converged", True)),
        })


def main():
    s = load_series("data/delhi_clean.csv", "date", "PM2.5")
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=4)

    burn_in = 1095
    first = s.index[burn_in]
    last = s.index[-max(HORIZONS) - 1]

    model = LoggingArima(order=(1, 1, 1), name="arima_fourier", use_exog=True)
    print(f"  origins {first.date()} to {last.date()}")
    print("  expanding window, refit every 90 days, order (1,1,1) fixed throughout")
    print("  (the exact configuration behind forecasts_all.csv / Table 4.1)\n")
    rolling_origin(s, exog, [model], first, last, window="expanding",
                   refit_every=90, verbose=True)

    log = pd.DataFrame(model.log)
    log.to_csv("arima_coefficient_stability.csv", index=False)

    print(f"\n  {len(log)} refits recorded.\n")
    print(log[["refit_origin", "n_train", "phi_1", "theta_1", "aic",
              "converged"]].to_string(index=False))

    print("\n" + "=" * 72)
    print("STABILITY SUMMARY")
    print("=" * 72)
    print(f"  phi_1:   min {log.phi_1.min():.4f}  max {log.phi_1.max():.4f}  "
          f"range {log.phi_1.max() - log.phi_1.min():.4f}")
    print(f"  theta_1: min {log.theta_1.min():.4f}  max {log.theta_1.max():.4f}  "
          f"range {log.theta_1.max() - log.theta_1.min():.4f}")
    print(f"  converged at every refit: {bool(log.converged.all())}")
    print(f"  closest |theta_1| ever gets to the invertibility boundary (1.0): "
          f"{(1 - log.theta_1.abs()).min():.4f}")
    print(f"  did any refit's theta_1 cross outside (-1, 1)? "
          f"{bool((log.theta_1.abs() >= 1.0).any())}")

    first_row = log.iloc[0]
    print(f"\n  First refit (closest to the originally-reported single fit): "
          f"phi_1={first_row.phi_1:.4f}, theta_1={first_row.theta_1:.4f}")
    print(f"  Report currently states: phi_1=0.581, theta_1=-0.987")


if __name__ == "__main__":
    main()
