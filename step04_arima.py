"""
MTH5000 - Step 4: the classical benchmark. ARIMA with annual Fourier terms.

    python step04_arima.py --csv data/delhi_clean.csv
    python step04_arima.py --test

WHY ARIMA AND NOT SARIMA

The proposal and the setup guide both assume a weekly cycle, which would force a
seasonal order and raise the two seasonal period problem. That was tested on 20
August and the weekly cycle is not there: no periodogram peak near 7, lag 7 of
the deseasonalised autocorrelation sitting on the decay curve rather than above
it, and a day of week effect indistinguishable from noise. The benchmark in step
3 that assumes a weekly cycle is also the worst of the four. So there is no
weekly seasonal order here. The annual cycle is carried by Fourier terms as
exogenous regressors, which is the standard treatment for a period too long for
a seasonal ARIMA to estimate.

WHY LOGS

Concentration is strongly right skewed, and annual Fourier terms explain 69
percent of the variance of the logarithm against far less on the raw scale.
Fitting in logs also stops the model predicting negative concentrations.

Back-transforming is not innocent. If log y is normal with mean m and variance s
squared, then exp(m) is the MEDIAN of y and exp(m + s squared over 2) is its
MEAN. Both are produced here as separate named models, because a report that
back-transforms without saying which one it is reporting has quietly changed the
quantity being forecast. The median minimises absolute error and the mean
minimises squared error, so expect the median variant to win on MAE and the mean
variant to win on RMSE. That is not a contradiction, it is the definition.

WHY THE MISSING DAYS ARE NOT FILLED IN

SARIMAX is a state space model fitted by the Kalman filter. At a missing
observation it simply skips the measurement update and carries the state forward
through the transition. The gap costs precision, which is correct, rather than
being papered over with an interpolated value that the model would then treat as
data. This is the argument Section 3 of the proposal makes for the tooling, and
it is the reason no imputation appears anywhere in this project.

WHY THE PARAMETERS ARE NOT REFITTED EVERY DAY

Refitting at each of several hundred origins would take a long time and change
the parameters constantly, which makes the results harder to interpret and
harder to reproduce. Instead the model is estimated once on the training block,
and then the filter is advanced one observation at a time through validation and
test with the parameters held fixed. Each forecast still uses only observations
up to its own origin, which is the property that matters. Whether periodic
refitting improves matters is a question for the rolling origin harness in step
5, where it can be answered rather than assumed.
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step03_benchmarks import chronological_split, HORIZONS
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs step01_data_check.py, step03_benchmarks.py and evaluation.py. {e}")


def fourier_terms(index, K=4, period=365.25):
    """Deterministic annual terms, computable for any date including the future."""
    doy = index.dayofyear.values.astype(float)
    cols = {}
    for k in range(1, K + 1):
        cols[f"ann_sin_{k}"] = np.sin(2 * np.pi * k * doy / period)
        cols[f"ann_cos_{k}"] = np.cos(2 * np.pi * k * doy / period)
    return pd.DataFrame(cols, index=index)


def fit_arima(y, exog, order):
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = SARIMAX(y, exog=exog if exog is not None else None, order=order,
                        trend="c" if order[1] == 0 else "n",
                        enforce_stationarity=False, enforce_invertibility=False)
        return model.fit(disp=False)


def select_order(y_train, exog_train, grid, verbose=True):
    """A small explicit grid, scored by AIC on the training block only.

    Deliberately not pmdarima's automatic search. A short grid that fits in an
    appendix is defensible in a viva; "the software chose it" is not. The grid is
    printed in full so the choice can be inspected rather than trusted.
    """
    rows = []
    for order in grid:
        try:
            res = fit_arima(y_train, exog_train, order)
            rows.append({"order": order, "aic": res.aic, "bic": res.bic,
                         "converged": bool(res.mle_retvals.get("converged", True))})
        except Exception as e:
            rows.append({"order": order, "aic": np.inf, "bic": np.inf,
                         "converged": False, "error": str(e)[:40]})

    table = pd.DataFrame(rows).sort_values("aic").reset_index(drop=True)
    if verbose:
        print("\n  Order search on the training block, by AIC:")
        for _, r in table.head(10).iterrows():
            mark = "  <- chosen" if r.name == 0 else ""
            print(f"    ARIMA{r['order']}  AIC {r['aic']:10.1f}  BIC {r['bic']:10.1f}"
                  f"{'' if r['converged'] else '  (did not converge)'}{mark}")
    best = table.iloc[0]["order"]
    return best, table


def walk_forward(y, exog, order, train_idx, forecast_idx, label=""):
    """Estimate once on training, then advance the filter one day at a time.

    `exog` must be indexed over y's dates PLUS the horizon beyond the last one,
    because the final origin forecasts past the end of the data. Pass None for a
    model with no exogenous terms. Returns a dict keyed by (origin, horizon)
    holding the mean and variance of the forecast on the log scale.
    """
    def ex(idx):
        return None if exog is None else exog.loc[idx]

    res = fit_arima(y.loc[train_idx], ex(train_idx), order)
    sigma2 = float(res.params.get("sigma2", np.nan))

    out = {}
    cursor = train_idx[-1]
    all_idx = y.index

    # Everything after training, advanced one observation at a time.
    remaining = all_idx[all_idx > cursor]
    max_h = max(HORIZONS)
    want = set(forecast_idx)

    for i, day in enumerate(remaining):
        if cursor in want:
            future = all_idx[all_idx.get_loc(cursor) + 1: all_idx.get_loc(cursor) + 1 + max_h]
            if len(future) == max_h:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    f = res.get_forecast(steps=max_h, exog=ex(future))
                mean = f.predicted_mean.values
                var = f.var_pred_mean.values
                for h in HORIZONS:
                    out[(cursor, h)] = (mean[h - 1], var[h - 1])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = res.append(y.loc[[day]], exog=ex([day]), refit=False)
        cursor = day

        if label and (i + 1) % 200 == 0:
            print(f"    {label}: advanced {i + 1}/{len(remaining)} days")

    # The final origin, once every observation has been absorbed.
    if cursor in want:
        future = pd.date_range(cursor + pd.Timedelta(days=1), periods=max_h, freq="D")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f = res.get_forecast(steps=max_h, exog=ex(future))
        for h in HORIZONS:
            out[(cursor, h)] = (f.predicted_mean.values[h - 1], f.var_pred_mean.values[h - 1])

    return out, sigma2


def to_forecast_rows(preds, series, name, back="median"):
    """Back-transform from logs and assemble the long forecast table."""
    rows = []
    for (origin, h), (m, v) in preds.items():
        target = origin + pd.Timedelta(days=h)
        if target not in series.index:
            continue
        if back == "median":
            yp = np.exp(m)
        elif back == "mean":
            yp = np.exp(m + v / 2.0)
        else:
            raise ValueError(back)
        rows.append({"origin": origin, "horizon": h, "model": name,
                     "y_pred": yp, "y_true": series.loc[target]})
    return pd.DataFrame(rows, columns=ev.FORECAST_COLUMNS)


# ----------------------------------------------------------------------------

def run(csv, date_col, value_col, threshold, fourier_k, out, bench_path):
    s = load_series(csv, date_col, value_col)
    y = np.log(s)
    y.name = "log_pm25"
    # Extend past the last observation so the final origin can still forecast.
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=fourier_k)

    train_idx, val_idx, test_idx = chronological_split(s.index)
    print("=" * 72)
    print("ARIMA WITH ANNUAL FOURIER TERMS, ON LOG CONCENTRATION")
    print("=" * 72)
    print(f"  train {train_idx[0].date()} to {train_idx[-1].date()}, "
          f"{int(y.loc[train_idx].notna().sum())} observed")
    print(f"  test  {test_idx[0].date()} to {test_idx[-1].date()}, "
          f"{int(y.loc[test_idx].notna().sum())} observed")
    print(f"  {fourier_k} Fourier pairs. No weekly seasonal order: see the module docstring.")

    grid = [(p, d, q) for d in (0, 1) for p in (0, 1, 2, 3) for q in (0, 1, 2)]
    order, table = select_order(y.loc[train_idx], exog.loc[train_idx], grid)
    print(f"\n  Selected ARIMA{order}.")

    print("\n  Advancing the filter through validation and test, parameters fixed.")
    preds, sigma2 = walk_forward(y, exog, order, train_idx, test_idx, label="arima")
    print(f"    residual variance on the log scale: {sigma2:.4f}")

    fc = pd.concat([
        to_forecast_rows(preds, s, "arima_fourier", back="median"),
        to_forecast_rows(preds, s, "arima_fourier_mean", back="mean"),
    ], ignore_index=True)

    # An ablation: the same order with the seasonal information removed entirely.
    # If the Fourier terms are doing nothing, this will match, and the report
    # should say so rather than presenting them as though they earned their place.
    print("\n  Ablation: the same order with no Fourier terms at all.")
    preds_nf, _ = walk_forward(y, None, order, train_idx, test_idx)
    fc = pd.concat([fc, to_forecast_rows(preds_nf, s, "arima_no_fourier", back="median")],
                   ignore_index=True)

    bench = pd.read_csv(bench_path, parse_dates=["origin"])
    both = pd.concat([bench, fc], ignore_index=True)
    ev.check_forecasts(both)

    print("\n" + "=" * 72)
    print("SCORING, AGAINST THE STEP 3 BENCHMARKS ON IDENTICAL ROWS")
    print("=" * 72)
    common = ev.restrict_to_common(both)
    scale = ev.mase_scale(s.loc[train_idx].values)
    metrics = ev.regression_metrics(common, scale)
    ev.print_regression(metrics)
    warn = ev.evaluate_warnings(common, event_threshold=threshold)
    ev.print_warnings(warn, threshold)

    common.to_csv(out, index=False)
    print(f"\n  Wrote {out} ({len(common)} rows, {common['model'].nunique()} models).")
    return metrics


# ----------------------------------------------------------------------------

def test_arima(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    idx = pd.date_range("2020-01-01", periods=40, freq="D")
    F = fourier_terms(idx, K=2)
    check(F.shape == (40, 4), f"expected 4 Fourier columns, got {F.shape}")
    check(np.allclose(F["ann_sin_1"] ** 2 + F["ann_cos_1"] ** 2, 1.0),
          "the first Fourier pair is not on the unit circle")

    # A year apart must give almost identical terms.
    a = fourier_terms(pd.DatetimeIndex(["2021-03-01"]), K=3).values
    b = fourier_terms(pd.DatetimeIndex(["2022-03-01"]), K=3).values
    check(np.abs(a - b).max() < 0.06, "annual terms are not periodic across years")

    # Back-transform: the mean variant must exceed the median variant, always.
    preds = {(pd.Timestamp("2024-01-05"), 1): (np.log(100.0), 0.25)}
    s = pd.Series([50.0] * 10, index=pd.date_range("2024-01-01", periods=10, freq="D"))
    med = to_forecast_rows(preds, s, "m", back="median")["y_pred"].iloc[0]
    mn = to_forecast_rows(preds, s, "m", back="mean")["y_pred"].iloc[0]
    check(abs(med - 100.0) < 1e-9, "median back-transform should be exp of the log mean")
    check(abs(mn - 100.0 * np.exp(0.125)) < 1e-9, "mean back-transform is wrong")
    check(mn > med, "the mean back-transform must exceed the median")

    # y_true must come from the target date, not the origin.
    s2 = pd.Series(np.arange(10, dtype=float),
                   index=pd.date_range("2024-01-01", periods=10, freq="D"))
    r = to_forecast_rows({(pd.Timestamp("2024-01-03"), 2): (0.0, 0.0)}, s2, "m")
    check(r["y_true"].iloc[0] == s2.loc[pd.Timestamp("2024-01-05")],
          "y_true is not taken from the target date")

    if verbose:
        print("  ARIMA checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="ARIMA benchmark with Fourier exog.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--benchmarks", default="forecasts_benchmarks.csv")
    ap.add_argument("--out", default="forecasts_classical.csv")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if (ev.test_evaluation() and test_arima()) else 1)

    print("\nRunning checks before fitting anything.")
    if not (ev.test_evaluation() and test_arima()):
        sys.exit("Checks failed.")

    run(args.csv, args.date_col, args.value_col, args.threshold,
        args.fourier, args.out, args.benchmarks)
    print("\nNext: step 5, the rolling origin harness. That is the fiddliest code")
    print("in the project and the one to write slowly.\n")


if __name__ == "__main__":
    main()
