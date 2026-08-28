"""
MTH5000 - Step 2: build the supervised feature table.

Turns one daily concentration series into a rectangular table that every model
in the proposal can consume: penalised linear regression, random forest,
gradient boosting, and the recurrent networks. SARIMA does not need this table,
it takes the raw series, but it is evaluated on exactly the same rows so the
comparison is fair.

    python step02_features.py --demo
    python step02_features.py --csv delhi.csv --value-col PM2.5 --out features.csv

THE ROW CONVENTION, which every other script depends on:

    A row indexed by date t is one forecast origin. Every feature in that row
    is computed from observations up to and INCLUDING day t, which is what a
    forecaster standing at the end of day t actually knows. The targets in that
    row are the values on days t+1, t+2 and t+3, which that forecaster does not
    know. So lag_0 is day t itself, and a rolling window labelled 7 covers days
    t-6 to t inclusive.

    This is the single place leakage can enter the project. If you add a
    feature, it must be a function of days <= t only, and you must extend
    test_no_leakage() below to cover it.

Missing values are left as NaN on purpose. Gradient boosting handles them
natively, and the state-space models handle gaps by skipping the measurement
update. Nothing is imputed here. Three flag columns record where the gaps are
so a model can use missingness as information rather than being confused by it.
Use --dropna for models that cannot take NaN, but read the row count it prints
before trusting the result.
"""

import argparse
import sys

import numpy as np
import pandas as pd

# Reuse the loader and the demo generator from step 1 so the two scripts can
# never disagree about how a CSV becomes a series.
try:
    from step01_data_check import load_series, make_demo_series, HAZARD_THRESHOLD
except ImportError:
    sys.exit("step01_data_check.py must sit in the same folder as this script.")

LAGS = [0, 1, 2, 3, 7]
ROLL_WINDOWS = [3, 7, 14, 30]
HORIZONS = [1, 2, 3]


# ----------------------------------------------------------------------------
# Features
# ----------------------------------------------------------------------------

def add_lag_features(feats, s):
    """Past values. lag_0 is day t, which is known at the forecast origin."""
    for k in LAGS:
        feats[f"lag_{k}"] = s.shift(k)

    # Short-term change. Direction of travel matters more than level when the
    # question is whether tomorrow crosses a threshold.
    feats["diff_1"] = s.shift(0) - s.shift(1)
    feats["diff_2"] = s.shift(0) - s.shift(2)
    feats["diff_7"] = s.shift(0) - s.shift(7)
    return feats


def add_rolling_features(feats, s):
    """Level and volatility over recent windows, ending at day t inclusive.

    min_periods is set to roughly half the window so a single missing day does
    not blank out the whole column. That is a deliberate trade: the statistic is
    computed from fewer observations rather than discarded.
    """
    for w in ROLL_WINDOWS:
        r = s.rolling(window=w, min_periods=max(2, w // 2))
        feats[f"roll_mean_{w}"] = r.mean()
        feats[f"roll_std_{w}"] = r.std()
        feats[f"roll_max_{w}"] = r.max()

    # Where today sits relative to the recent norm. Scale-free, so it transfers
    # if the pipeline is later pointed at a different city.
    feats["anom_30"] = s - feats["roll_mean_30"]
    with np.errstate(divide="ignore", invalid="ignore"):
        feats["z_30"] = feats["anom_30"] / feats["roll_std_30"].replace(0, np.nan)
    return feats


def add_exceedance_history(feats, s, threshold):
    """How recently and how often the threshold has been breached.

    Exceedances cluster: Delhi's bad days arrive in multi-day episodes when the
    boundary layer collapses. Persistence of the event itself is a strong
    predictor of the event, and a plain concentration lag does not express it.
    """
    # Float rather than bool: a missing day is an unknown exceedance, not a
    # non-exceedance, and bool columns cannot hold NaN.
    above = (s > threshold).astype(float).mask(s.isna())

    for w in [7, 30]:
        feats[f"exceed_frac_{w}"] = above.rolling(w, min_periods=max(2, w // 2)).mean()

    # Days since the last exceedance at or before t, capped so the column does
    # not become a proxy for the calendar date.
    idx = np.arange(len(s))
    last_hit = np.where(above.values == 1, idx, np.nan)
    last_hit = pd.Series(last_hit, index=s.index).ffill()
    feats["days_since_exceed"] = np.minimum(idx - last_hit.values, 90)
    return feats


def add_calendar_features(feats, idx, n_fourier):
    """Deterministic time terms.

    Day of week and month are left as plain integers. Trees split on them
    happily; for penalised regression, one-hot encode them at model time rather
    than baking that choice in here.
    """
    feats["dow"] = idx.dayofweek
    feats["is_weekend"] = (idx.dayofweek >= 5).astype(int)
    feats["month"] = idx.month
    doy = idx.dayofyear.values.astype(float)

    # Fourier terms for the annual cycle. This is the fix discussed in the
    # setup guide: SARIMA takes one seasonal period, so the weekly cycle goes in
    # as the seasonal order and the annual cycle comes in here as exogenous
    # regressors. The ML models get the same terms so the comparison is like
    # for like.
    for k in range(1, n_fourier + 1):
        feats[f"ann_sin_{k}"] = np.sin(2 * np.pi * k * doy / 365.25)
        feats[f"ann_cos_{k}"] = np.cos(2 * np.pi * k * doy / 365.25)
    return feats


def add_missingness_flags(feats, s):
    """Gaps as information, since instrument downtime is not random."""
    isna = s.isna()
    feats["is_missing"] = isna.astype(int)
    # Cast before rolling: summing a boolean window is not supported on every
    # pandas version, and this script has to run on the laptop as well as here.
    feats["n_missing_7"] = isna.astype(float).rolling(7, min_periods=1).sum()

    idx = np.arange(len(s))
    last_obs = np.where(~isna.values, idx, np.nan)
    last_obs = pd.Series(last_obs, index=s.index).ffill()
    feats["days_since_obs"] = np.minimum(idx - last_obs.values, 30)
    return feats


def add_weather(feats, idx, lat, lon):
    """Optional meteostat merge. Off unless --weather is passed.

    Only weather OBSERVED up to day t is used. Real forecasting systems feed in
    numerical weather predictions for t+1 onward, which would very likely help,
    but that is a different and much stronger claim about what is knowable.
    Say so in the report rather than quietly using future weather.
    """
    try:
        from meteostat import Point, Daily
    except ImportError:
        print("  meteostat not installed. pip install meteostat. Skipping weather.")
        return feats

    point = Point(lat, lon)
    met = Daily(point, idx.min().to_pydatetime(), idx.max().to_pydatetime()).fetch()
    if met.empty:
        print("  meteostat returned nothing for that point and range. Skipping.")
        return feats

    met = met.reindex(idx)
    for col in ["tavg", "tmin", "tmax", "prcp", "wspd", "pres"]:
        if col not in met.columns:
            continue
        feats[f"wx_{col}"] = met[col]
        feats[f"wx_{col}_lag1"] = met[col].shift(1)
        feats[f"wx_{col}_mean3"] = met[col].rolling(3, min_periods=2).mean()

    print(f"  Weather merged: {sum(c.startswith('wx_') for c in feats.columns)} columns.")
    return feats


def add_targets(feats, s, threshold):
    """What we are trying to predict: the value h days after the origin.

    A negative shift looks backwards on the page and is the one line in this
    file worth staring at. s.shift(-1) at row t holds the value from row t+1,
    which is exactly the future value we want as the target.
    """
    for h in HORIZONS:
        future = s.shift(-h)
        feats[f"target_h{h}"] = future

        # Nullable integer, so an unknown future stays unknown instead of
        # collapsing to False. A NaN silently becoming a negative label would
        # bias every hit rate in the project downwards.
        feats[f"exceed_h{h}"] = (future > threshold).astype("float").where(future.notna()).astype("Int8")
    return feats


def build_features(s, threshold=None, n_fourier=3, weather=False,
                   lat=28.61, lon=77.21):
    """One daily series in, one supervised table out."""
    if threshold is None:
        threshold = HAZARD_THRESHOLD

    if not isinstance(s.index, pd.DatetimeIndex):
        raise TypeError("Series must have a DatetimeIndex.")

    # A complete daily calendar is what makes shift(k) mean "k days ago".
    # On a gappy index it would silently mean "k rows ago", which is a
    # different and wrong thing.
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    s = s.reindex(full)

    feats = pd.DataFrame(index=s.index)
    feats = add_lag_features(feats, s)
    feats = add_rolling_features(feats, s)
    feats = add_exceedance_history(feats, s, threshold)
    feats = add_calendar_features(feats, s.index, n_fourier)
    feats = add_missingness_flags(feats, s)
    if weather:
        feats = add_weather(feats, s.index, lat, lon)
    feats = add_targets(feats, s, threshold)

    feats.index.name = "date"
    return feats


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------

def test_no_leakage(threshold=None, verbose=True):
    """Prove that no feature at row t depends on any day after t.

    Method: build the table, then corrupt the series from a cut date onward and
    rebuild. Every feature row strictly before the cut must be bit-for-bit
    identical. If a shift is the wrong sign or a rolling window is not aligned
    to the right edge, this fails loudly.

    Run this again every time you add a feature. Rolling-origin evaluation is
    the flagged risk in the project, and this is the cheapest guard against it.
    """
    if threshold is None:
        threshold = HAZARD_THRESHOLD

    s = make_demo_series(n_years=4, seed=1)
    cut = s.index[600]

    a = build_features(s, threshold=threshold)
    corrupted = s.copy()
    corrupted.loc[cut:] = corrupted.loc[cut:] * 10 + 500
    b = build_features(corrupted, threshold=threshold)

    feature_cols = [c for c in a.columns
                    if not c.startswith(("target_", "exceed_h"))]
    before = a.index < cut
    ok = True
    for c in feature_cols:
        left, right = a.loc[before, c], b.loc[before, c]
        if not left.equals(right):
            n_bad = int((left.fillna(-999) != right.fillna(-999)).sum())
            print(f"  LEAK in '{c}': {n_bad} rows before the cut changed.")
            ok = False

    # Targets must be exactly the value h days later, checked by hand at a
    # date with no missing neighbours.
    probe = None
    for d in a.index[100:400]:
        window = s.loc[d:d + pd.Timedelta(days=3)]
        if window.notna().all() and len(window) == 4:
            probe = d
            break
    if probe is not None:
        for h in HORIZONS:
            expected = s.loc[probe + pd.Timedelta(days=h)]
            got = a.loc[probe, f"target_h{h}"]
            if not np.isclose(expected, got):
                print(f"  MISALIGNED target_h{h} at {probe.date()}: "
                      f"expected {expected:.3f}, got {got:.3f}")
                ok = False
        # lag_0 must be day t itself, lag_1 the day before.
        if not np.isclose(a.loc[probe, "lag_0"], s.loc[probe]):
            print("  lag_0 is not day t.")
            ok = False
        if not np.isclose(a.loc[probe, "lag_1"], s.loc[probe - pd.Timedelta(days=1)]):
            print("  lag_1 is not day t-1.")
            ok = False

    # A rolling mean labelled 7 must cover t-6 to t inclusive.
    if probe is not None:
        window = s.loc[probe - pd.Timedelta(days=6):probe]
        if window.notna().all():
            if not np.isclose(a.loc[probe, "roll_mean_7"], window.mean()):
                print("  roll_mean_7 is not aligned to the right edge.")
                ok = False

    if verbose:
        print("  Leakage checks:", "PASSED" if ok else "FAILED")
    return ok


def report_table(feats, threshold):
    """What the table looks like, and where the usable rows are."""
    print("\n" + "=" * 58)
    print("FEATURE TABLE")
    print("=" * 58)
    feature_cols = [c for c in feats.columns
                    if not c.startswith(("target_", "exceed_h"))]
    print(f"  Rows              : {len(feats)}")
    print(f"  Feature columns   : {len(feature_cols)}")
    print(f"  Target columns    : {len(feats.columns) - len(feature_cols)}")
    print(f"  Date range        : {feats.index.min().date()} to {feats.index.max().date()}")

    complete = feats[feature_cols].notna().all(axis=1).sum()
    print(f"  Rows with every feature present: {complete} "
          f"({100 * complete / len(feats):.1f}%)")

    print("\n  Most incomplete feature columns:")
    na = feats[feature_cols].isna().sum().sort_values(ascending=False)
    for c, n in na.head(5).items():
        print(f"    {c:<22} {n:>5} missing ({100 * n / len(feats):.1f}%)")

    print("\n" + "=" * 58)
    print(f"CLASS BALANCE (threshold {threshold:.0f})")
    print("=" * 58)
    for h in HORIZONS:
        col = feats[f"exceed_h{h}"].dropna()
        pos = int((col == 1).sum())
        print(f"  h={h}: {pos} exceedance days out of {len(col)} labelled "
              f"({100 * pos / len(col):.1f}%)")
    print("\n  This is the minority class the warning system has to catch.")
    print("  Use class weights and precision-recall curves, not accuracy.")

    # Chronological split only. Shuffling a time series is the classic way to
    # get an excellent score that means nothing.
    n = len(feats)
    i_tr, i_va = int(0.70 * n), int(0.85 * n)
    print("\n" + "=" * 58)
    print("SUGGESTED CHRONOLOGICAL SPLIT (never shuffle)")
    print("=" * 58)
    print(f"  Train : {feats.index[0].date()} to {feats.index[i_tr - 1].date()}  ({i_tr} rows)")
    print(f"  Val   : {feats.index[i_tr].date()} to {feats.index[i_va - 1].date()}  ({i_va - i_tr} rows)")
    print(f"  Test  : {feats.index[i_va].date()} to {feats.index[-1].date()}  ({n - i_va} rows)")
    print("\n  Leave a gap of at least 3 days between train and val, and between")
    print("  val and test, so a target inside one block is never a feature in")
    print("  the next. Step 3 does this properly with rolling origins.")


def main():
    ap = argparse.ArgumentParser(description="Build the MTH5000 feature table.")
    ap.add_argument("--csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--demo", action="store_true",
                    help="synthetic series from step 1, for testing the pipeline")
    ap.add_argument("--out", default="features.csv")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD,
                    help=f"hazard threshold in ug/m3 (default {HAZARD_THRESHOLD:.0f})")
    ap.add_argument("--fourier", type=int, default=3,
                    help="number of annual Fourier pairs (default 3)")
    ap.add_argument("--weather", action="store_true",
                    help="merge meteostat daily weather (needs network)")
    ap.add_argument("--lat", type=float, default=28.61, help="Delhi by default")
    ap.add_argument("--lon", type=float, default=77.21)
    ap.add_argument("--dropna", action="store_true",
                    help="keep only rows with every feature and every target present")
    ap.add_argument("--keep-incomplete-targets", action="store_true",
                    help="keep the final rows whose targets fall past the data")
    ap.add_argument("--test", action="store_true",
                    help="run the leakage checks and exit")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if test_no_leakage(args.threshold) else 1)

    if args.demo:
        print("Using synthetic demo data (no real file loaded).")
        s = make_demo_series()
    elif args.csv:
        s = load_series(args.csv, args.date_col, args.value_col)
    else:
        sys.exit("Give --csv PATH or --demo. See --help.")

    print("\nRunning leakage checks before building.")
    if not test_no_leakage(args.threshold):
        sys.exit("Leakage checks failed. Fix the features before trusting any result.")

    feats = build_features(s, threshold=args.threshold, n_fourier=args.fourier,
                           weather=args.weather, lat=args.lat, lon=args.lon)

    if not args.keep_incomplete_targets:
        # The last max(HORIZONS) rows have no future to predict.
        target_cols = [f"target_h{h}" for h in HORIZONS]
        feats = feats[feats[target_cols].notna().any(axis=1)]

    if args.dropna:
        before = len(feats)
        feats = feats.dropna()
        print(f"\n  --dropna: {before} rows in, {len(feats)} out "
              f"({100 * (before - len(feats)) / before:.1f}% discarded).")

    report_table(feats, args.threshold)

    feats.to_csv(args.out)
    print(f"\n  Wrote {args.out} ({len(feats)} rows, {len(feats.columns)} columns).")
    print("\nNext: SARIMA on the raw series as the benchmark, then the ML models")
    print("on this table, all scored on the same rows.\n")


if __name__ == "__main__":
    main()
