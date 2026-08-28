"""
MTH5000 - Step 3: the benchmarks the machine learning has to beat.

    python step03_benchmarks.py --csv data/delhi_clean.csv
    python step03_benchmarks.py --test

WHY THIS COMES BEFORE ANY MODEL

A mean absolute error of 40 means nothing on its own. It means something only
against what you would have got for free. Dr Tian asked for machine learning, and
the way to show machine learning earned its place is to publish the number that a
one line forecast achieves and then beat it. If the gradient boosting cannot beat
persistence at three days ahead, that is the finding, and it is a real one.

THE FOUR BENCHMARKS

  naive              tomorrow equals today. Textbook persistence. Undefined when
                     today is missing, which is honest but costs rows.
  naive_carry        tomorrow equals the last value actually observed. What an
                     operator would really do when a sensor is down. The gap
                     between this and naive is the price the missing days exact.
  seasonal_naive_7   tomorrow equals the same weekday a week ago. Included even
                     though we established there is no weekly cycle at this
                     station, because its failure is the quantitative evidence
                     for that claim rather than an assertion about a periodogram.
  climatology        the historical average for that day of the year, smoothed.
                     Carries no recent information at all. At three days ahead it
                     is often embarrassingly hard to beat, and a model that cannot
                     is a model that has learned only the season.

The climatology is fitted on training data alone and its smoothing window is
chosen on the validation block. Fitting it on everything would let the test
period's own weather set the average it is scored against.
"""

import argparse
import sys

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Need step01_data_check.py and evaluation.py beside this script. {e}")

HORIZONS = [1, 2, 3]
GAP_DAYS = 3          # blank days between blocks, so a target in one is never a feature in the next


# ----------------------------------------------------------------------------
# Splitting
# ----------------------------------------------------------------------------

def chronological_split(index, train_frac=0.65, val_frac=0.15, gap=GAP_DAYS):
    """Three contiguous blocks in time order, separated by blank days.

    The test block is 20 percent rather than 15 so that it spans two winters. A
    block covering one winter and two low seasons is not a fair sample of a series
    whose entire signal is seasonal, and the warning metrics computed on it would
    describe an unusually clean period rather than the climate the system would
    operate in.

    The gap matters more than it looks. A forecast issued on the last day of
    training has targets up to three days later, which land inside validation. If
    the blocks touch, those targets are both trained on and scored on. Three blank
    days at each boundary removes the overlap for horizons up to three.
    """
    n = len(index)
    i_tr = int(train_frac * n)
    i_va = int((train_frac + val_frac) * n)
    train = index[:i_tr - gap]
    val = index[i_tr:i_va - gap]
    test = index[i_va:]
    return train, val, test


# ----------------------------------------------------------------------------
# The benchmarks
# ----------------------------------------------------------------------------

def fit_climatology(train_series, window):
    """Mean concentration by day of year, smoothed circularly.

    Circular because 31 December and 1 January are one day apart, and a window
    that stops at the year boundary would put a discontinuity in the middle of
    the season this project is about.
    """
    s = train_series.dropna()
    by_doy = s.groupby(s.index.dayofyear).mean()
    by_doy = by_doy.reindex(range(1, 367))

    # Wrap the year three times, smooth, take the middle copy back.
    tripled = pd.concat([by_doy, by_doy, by_doy], ignore_index=True)
    smoothed = tripled.rolling(window, center=True, min_periods=1).mean()
    out = smoothed.iloc[366:732].values
    return pd.Series(out, index=range(1, 367)).ffill().bfill()


def predict(series, origins, climatology):
    """Every benchmark's forecast for every origin and horizon, in long form."""
    carried = series.ffill()          # last observed value on or before each date
    rows = []

    for t in origins:
        for h in HORIZONS:
            target_date = t + pd.Timedelta(days=h)
            if target_date not in series.index:
                continue
            y_true = series.loc[target_date]

            lag7_date = target_date - pd.Timedelta(days=7)
            snaive = series.loc[lag7_date] if lag7_date in series.index else np.nan
            # lag7_date is at most t for h <= 7, so this uses nothing from the future.

            doy = target_date.dayofyear
            preds = {
                "naive": series.loc[t],
                "naive_carry": carried.loc[t],
                "seasonal_naive_7": snaive,
                "climatology": climatology.get(doy, np.nan),
            }
            for name, yp in preds.items():
                rows.append({"origin": t, "horizon": h, "model": name,
                             "y_pred": yp, "y_true": y_true})

    return pd.DataFrame(rows, columns=ev.FORECAST_COLUMNS)


def tune_climatology(series, train_idx, val_idx, windows=(1, 7, 15, 31, 61, 91)):
    """Choose the smoothing window on validation, never on test."""
    train = series.loc[train_idx]
    best, table = None, []
    for w in windows:
        clim = fit_climatology(train, w)
        f = predict(series, val_idx, clim)
        f = f[f["model"] == "climatology"].dropna(subset=["y_pred", "y_true"])
        mae = np.mean(np.abs(f["y_pred"] - f["y_true"]))
        table.append((w, mae, len(f)))
        if best is None or mae < best[1]:
            best = (w, mae)

    print("\n  Climatology smoothing window, chosen on validation:")
    for w, mae, n in table:
        mark = "  <- chosen" if w == best[0] else ""
        print(f"    window {w:>3} days: validation MAE {mae:7.2f}  (n={n}){mark}")
    return best[0]


# ----------------------------------------------------------------------------

def run(csv, date_col, value_col, threshold, out):
    s = load_series(csv, date_col, value_col)
    idx = s.index

    train_idx, val_idx, test_idx = chronological_split(idx)
    print("=" * 72)
    print("SPLIT (chronological, never shuffled)")
    print("=" * 72)
    print(f"  {'block':<6} {'from':10} {'to':10} {'n':>5} {'mean':>7} {'sd':>7} "
          f"{'mean|d|':>8} {'>thr':>6} {'winters':>8}")
    print("  " + "-" * 76)
    for name, block in [("train", train_idx), ("val", val_idx), ("test", test_idx)]:
        d = s.loc[block].dropna()
        winters = len(set((d.index + pd.Timedelta(days=61)).year[d.index.month.isin([11, 12, 1])]))
        print(f"  {name:<6} {block[0].date()} {block[-1].date()} {len(d):>5} "
              f"{d.mean():7.1f} {d.std():7.1f} {np.abs(np.diff(d.values)).mean():8.1f} "
              f"{100 * (d > threshold).mean():5.1f}% {winters:>8}")
    print("  " + "-" * 76)
    print("  Compare the blocks before reading any score. If the test block is")
    print("  calmer or cleaner than training, every model looks better than it is")
    print("  and the exceedance rate the warning metrics are computed against is")
    print("  not the rate the system would meet in operation.")
    print(f"  {GAP_DAYS} blank days between blocks, so a target in one block is")
    print("  never scored against a model that trained on it.")

    window = tune_climatology(s, train_idx, val_idx)
    clim = fit_climatology(s.loc[train_idx], window)

    fc = predict(s, test_idx, clim)
    ev.check_forecasts(fc)

    print("\n" + "=" * 72)
    print("SCORING")
    print("=" * 72)
    fc_common = ev.restrict_to_common(fc)

    scale = ev.mase_scale(s.loc[train_idx].values)
    print(f"  MASE scale, from training data only: {scale:.3f}")

    metrics = ev.regression_metrics(fc_common, scale)
    ev.print_regression(metrics)

    warn = ev.evaluate_warnings(fc_common, event_threshold=threshold)
    ev.print_warnings(warn, threshold)

    fc_common.to_csv(out, index=False)
    print(f"\n  Wrote {out} ({len(fc_common)} rows).")

    best = metrics.loc[metrics.groupby("horizon")["MAE"].idxmin()]
    print("\n" + "=" * 72)
    print("WHAT THE MACHINE LEARNING HAS TO BEAT")
    print("=" * 72)
    for _, r in best.iterrows():
        print(f"  h={int(r['horizon'])}: {r['model']:<20} MAE {r['MAE']:6.2f}  "
              f"MASE {r['MASE']:.3f}")
    print("\n  Any model that does not beat these at a given horizon has not earned")
    print("  its place in the report at that horizon. Say so if it does not.")
    return fc_common, metrics


# ----------------------------------------------------------------------------

def test_benchmarks(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    idx = pd.date_range("2020-01-01", periods=400, freq="D")
    s = pd.Series(np.arange(400, dtype=float), index=idx)

    clim = pd.Series(0.0, index=range(1, 367))
    origins = idx[300:310]
    f = predict(s, origins, clim)

    t = origins[0]
    got = f[(f.origin == t) & (f.horizon == 2)].set_index("model")["y_pred"]
    check(got["naive"] == s.loc[t], "naive should be the value at the origin")
    check(got["seasonal_naive_7"] == s.loc[t + pd.Timedelta(days=2 - 7)],
          "seasonal naive should be the target date minus seven days")
    truth = f[(f.origin == t) & (f.horizon == 2)]["y_true"].iloc[0]
    check(truth == s.loc[t + pd.Timedelta(days=2)], "y_true is misaligned")

    # No forecast may use anything after its own origin.
    corrupted = s.copy()
    corrupted.loc[origins[0] + pd.Timedelta(days=1):] = -999.0
    f2 = predict(corrupted, [origins[0]], clim)
    a = f[(f.origin == origins[0])].set_index(["model", "horizon"])["y_pred"]
    b = f2.set_index(["model", "horizon"])["y_pred"]
    check(a.equals(b), "a benchmark forecast changed when the future was corrupted")

    # naive_carry must bridge a gap that defeats plain naive.
    g = s.copy(); g.loc[idx[305]] = np.nan
    f3 = predict(g, [idx[305]], clim).set_index("model")
    check(pd.isna(f3.loc["naive", "y_pred"]).all(), "naive should be undefined on a missing day")
    check((f3.loc["naive_carry", "y_pred"] == s.loc[idx[304]]).all(),
          "naive_carry should carry the last observed value")

    # Climatology smoothing must wrap the year end.
    doy = pd.Series(np.where(np.arange(1, 367) <= 3, 100.0, 0.0), index=range(1, 367))
    fake = pd.Series(doy.reindex(pd.date_range("2021-01-01", periods=365, freq="D").dayofyear).values,
                     index=pd.date_range("2021-01-01", periods=365, freq="D"))
    c = fit_climatology(fake, window=7)
    check(c.loc[365] > 0, "the smoothing window did not wrap across the year boundary")

    # The split must leave a real gap.
    tr, va, te = chronological_split(idx)
    check((va[0] - tr[-1]).days > GAP_DAYS, "no gap between train and validation")
    check((te[0] - va[-1]).days > GAP_DAYS, "no gap between validation and test")
    check(tr[-1] < va[0] < te[0], "blocks are not in time order")

    if verbose:
        print("  Benchmark checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Benchmark forecasts for MTH5000.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--out", default="forecasts_benchmarks.csv")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        okA = ev.test_evaluation()
        okB = test_benchmarks()
        sys.exit(0 if (okA and okB) else 1)

    print("\nRunning checks before scoring anything.")
    if not (ev.test_evaluation() and test_benchmarks()):
        sys.exit("Checks failed. Do not trust any number below them.")

    run(args.csv, args.date_col, args.value_col, args.threshold, args.out)
    print("\nNext: step 4, ARIMA with annual Fourier terms as exog, on log PM2.5,")
    print("scored by this same module on these same rows.\n")


if __name__ == "__main__":
    main()
