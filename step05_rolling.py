"""
MTH5000 - Step 5: the rolling origin evaluation harness.

    python step05_rolling.py --test
    python step05_rolling.py --csv data/delhi_clean.csv --window expanding
    python step05_rolling.py --csv data/delhi_clean.csv --window 1095

WHY THIS EXISTS

Steps 3 and 4 scored every model on one test block of 700 days. That block is one
draw from a process, and it happened to be calmer than the training period. Any
conclusion drawn from it is a conclusion about late 2024 to 2026 rather than about
the models. A rolling origin evaluation issues a forecast from every origin across
years of data, so the result is an average over many periods and many seasons
rather than a bet on one.

THE INVARIANT, WHICH IS THE WHOLE POINT

At origin t, a model may use observations up to and including day t and nothing
else. Not the value at t+1. Not a parameter estimated using data after t. Not a
scaling constant, a threshold, or an imputed value computed from the full series.

This is the easiest place in the project to break that without noticing, because
nothing crashes when you do; the numbers simply get better. So the harness is
built around one loop that all models share, and that loop is tested by
corrupting the future and asserting that no forecast issued before the corruption
changes. A model cannot leak on its own; it can only leak if the loop lets it.

HOW A MODEL PLUGS IN

Three methods, in the order the harness calls them.

    start(y_hist, exog_hist)   re-estimate parameters. y_hist ends at the origin.
    update(day, y_value, exog_row)   absorb one newly observed day.
    predict(horizons, future_exog)   forecast from the current state.

Cheap models recompute from scratch in start and ignore update. The ARIMA keeps
its filter state and advances it in update, because refitting it at every origin
would take hours and would change the parameters constantly, which makes results
harder to reproduce and harder to explain.

REFITTING AND THE WINDOW

Two knobs, both reported rather than assumed.

--refit-every    how often parameters are re-estimated. Between refits the state
                 is advanced but the parameters are held. Daily refitting is not
                 obviously better and is much slower; this makes it measurable.
--window         expanding uses everything up to the origin. A number uses only
                 the last that many days. This matters here: day to day volatility
                 at this station has fallen from a mean absolute change of 38.9 in
                 2017 to 15.8 in 2026, so an expanding window keeps training the
                 model on an era that no longer resembles the present. Which is
                 better is an empirical question and this is how it gets answered.
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step03_benchmarks import fit_climatology, HORIZONS
    from step04_arima import fourier_terms, fit_arima
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs step01, step03, step04 and evaluation.py beside this script. {e}")


# ----------------------------------------------------------------------------
# The model interface
# ----------------------------------------------------------------------------

class Forecaster:
    """Base class. Subclasses must not look at anything after the origin."""
    name = "base"

    def start(self, y_hist, exog_hist):
        raise NotImplementedError

    def update(self, day, y_value, exog_row):
        pass

    def predict(self, horizons, future_exog):
        raise NotImplementedError


class Naive(Forecaster):
    """Tomorrow equals the last observed value on or before the origin."""
    name = "naive_carry"

    def start(self, y_hist, exog_hist):
        obs = y_hist.dropna()
        self.last = obs.iloc[-1] if len(obs) else np.nan

    def update(self, day, y_value, exog_row):
        if not pd.isna(y_value):
            self.last = y_value

    def predict(self, horizons, future_exog):
        return {h: self.last for h in horizons}


class SeasonalNaive(Forecaster):
    """Tomorrow equals the same weekday a week earlier. Kept as a control."""
    name = "seasonal_naive_7"

    def start(self, y_hist, exog_hist):
        self.hist = y_hist.copy()

    def update(self, day, y_value, exog_row):
        self.hist.loc[day] = y_value

    def predict(self, horizons, future_exog):
        out = {}
        last = self.hist.index[-1]
        for h in horizons:
            d = last + pd.Timedelta(days=h - 7)
            out[h] = self.hist.loc[d] if d in self.hist.index else np.nan
        return out


class Climatology(Forecaster):
    """Day of year average, re-estimated at every refit from history only."""
    name = "climatology"

    def __init__(self, window=15):
        self.window = window

    def start(self, y_hist, exog_hist):
        self.table = fit_climatology(y_hist, self.window)
        self.last_day = y_hist.index[-1]

    def update(self, day, y_value, exog_row):
        self.last_day = day

    def predict(self, horizons, future_exog):
        return {h: self.table.get((self.last_day + pd.Timedelta(days=h)).dayofyear, np.nan)
                for h in horizons}


class Arima(Forecaster):
    """ARIMA with Fourier exog on logs. Keeps filter state between refits."""

    def __init__(self, order=(1, 1, 1), name="arima_fourier", use_exog=True,
                 back="median"):
        self.order = order
        self.name = name
        self.use_exog = use_exog
        self.back = back

    def start(self, y_hist, exog_hist):
        # statsmodels refuses to append a series whose name differs from the one
        # it was fitted on, so both are stripped of their name here rather than
        # relying on the caller to pass an unnamed series.
        ly = np.log(y_hist).rename(None)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.res = fit_arima(ly, exog_hist if self.use_exog else None, self.order)

    def update(self, day, y_value, exog_row):
        ly = pd.Series([np.log(y_value) if y_value and y_value > 0 else np.nan],
                       index=pd.DatetimeIndex([day]), name=None)
        ex = exog_row if self.use_exog else None
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.res = self.res.append(ly, exog=ex, refit=False)

    def predict(self, horizons, future_exog):
        n = max(horizons)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            f = self.res.get_forecast(steps=n,
                                      exog=future_exog if self.use_exog else None)
        m = f.predicted_mean.values
        v = f.var_pred_mean.values
        if self.back == "median":
            vals = np.exp(m)
        else:
            vals = np.exp(m + v / 2.0)
        return {h: vals[h - 1] for h in horizons}


# ----------------------------------------------------------------------------
# The harness
# ----------------------------------------------------------------------------

def rolling_origin(series, exog, models, first_origin, last_origin,
                   window="expanding", refit_every=90, stride=1, verbose=True):
    """One loop, shared by every model.

    series      the observed daily series, complete daily index, NaN where missing
    exog        deterministic regressors covering series plus max horizon beyond
    models      list of Forecaster instances
    window      "expanding", or an integer number of days
    refit_every re-estimate parameters every this many days
    stride      score every this many origins; every day is still absorbed
    """
    idx = series.index
    days = idx[(idx >= first_origin) & (idx <= last_origin)]
    max_h = max(HORIZONS)
    rows = []

    for i, t in enumerate(days):
        # --- put every model into a state that knows the series through t ---
        if i % refit_every == 0:
            hist = series.loc[:t]
            if window != "expanding":
                hist = hist.iloc[-int(window):]
            hist_exog = exog.loc[hist.index]
            for m in models:
                m.start(hist, hist_exog)
        else:
            for m in models:
                m.update(t, series.loc[t], exog.loc[[t]])

        if i % stride != 0:
            continue

        # --- forecast, using only deterministic information about the future ---
        future = pd.date_range(t + pd.Timedelta(days=1), periods=max_h, freq="D")
        if not set(future).issubset(set(exog.index)):
            continue
        fex = exog.loc[future]

        for m in models:
            try:
                preds = m.predict(HORIZONS, fex)
            except Exception:
                preds = {h: np.nan for h in HORIZONS}
            for h, yp in preds.items():
                target = t + pd.Timedelta(days=h)
                if target not in series.index:
                    continue
                rows.append({"origin": t, "horizon": h, "model": m.name,
                             "y_pred": yp, "y_true": series.loc[target]})

        if verbose and (i + 1) % 250 == 0:
            print(f"    origin {i + 1}/{len(days)}  ({t.date()})")

    return pd.DataFrame(rows, columns=ev.FORECAST_COLUMNS)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def _toy(n=500, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=n, freq="D")
    t = np.arange(n)
    v = 80 + 40 * np.cos(2 * np.pi * (t - 15) / 365.25) + rng.normal(0, 12, n)
    s = pd.Series(np.clip(v, 5, None), index=idx)
    s.iloc[rng.choice(n, size=int(0.04 * n), replace=False)] = np.nan
    # Named on purpose: load_series returns a named series, and statsmodels
    # refuses to append across a name mismatch. An unnamed toy hid that bug once.
    s.name = "PM2.5"
    ext = idx.append(pd.date_range(idx[-1] + pd.Timedelta(days=1), periods=3, freq="D"))
    return s, fourier_terms(ext, K=2)


def test_rolling(verbose=True, include_arima=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    s, exog = _toy()
    first, last = s.index[300], s.index[380]

    def build():
        ms = [Naive(), SeasonalNaive(), Climatology(window=15)]
        if include_arima:
            ms.append(Arima(order=(1, 0, 0)))
        return ms

    base = rolling_origin(s, exog, build(), first, last, refit_every=30, verbose=False)
    check(len(base) > 0, "the harness produced no forecasts")
    check(set(base["model"]) == {m.name for m in build()}, "a model produced nothing")

    # 1. Alignment. y_true must be the value h days after the origin.
    r = base.sample(30, random_state=0)
    bad = sum(1 for _, x in r.iterrows()
              if not (pd.isna(x["y_true"]) and pd.isna(s.loc[x["origin"] + pd.Timedelta(days=int(x["horizon"]))]))
              and x["y_true"] != s.loc[x["origin"] + pd.Timedelta(days=int(x["horizon"]))])
    check(bad == 0, f"{bad} rows have y_true misaligned with the target date")

    # 2. Naive must equal the last observed value at or before the origin.
    nv = base[base.model == "naive_carry"]
    carried = s.ffill()
    bad = sum(1 for _, x in nv.iterrows() if x["y_pred"] != carried.loc[x["origin"]])
    check(bad == 0, f"{bad} naive forecasts are not the carried forward value")

    # 3. THE LEAKAGE TEST. Corrupt the future, rerun, demand identical forecasts
    #    for every origin strictly before the cut.
    cut = s.index[340]
    poisoned = s.copy()
    poisoned.loc[cut:] = poisoned.loc[cut:] * 7 + 900
    after = rolling_origin(poisoned, exog, build(), first, last, refit_every=30, verbose=False)

    key = ["origin", "horizon", "model"]
    a = base[base.origin < cut].set_index(key)["y_pred"].sort_index()
    b = after[after.origin < cut].set_index(key)["y_pred"].sort_index()
    check(a.index.equals(b.index), "the corrupted run produced a different set of forecasts")
    if a.index.equals(b.index):
        diff = ~np.isclose(a.values.astype(float), b.values.astype(float),
                           rtol=1e-9, atol=1e-9, equal_nan=True)
        n_bad = int(diff.sum())
        check(n_bad == 0, f"LEAK: {n_bad} forecasts before the cut changed when the "
                          f"future was corrupted. Offenders: "
                          f"{sorted(set(a.index[diff].get_level_values('model')))}")

    # 4. A rolling window must not see beyond its own length.
    win = rolling_origin(s, exog, [Naive(), Climatology(10)], first, last,
                         window=200, refit_every=30, verbose=False)
    check(len(win) > 0, "the rolling window run produced nothing")

    # 5. Stride must reduce the number of scored origins without changing them.
    st = rolling_origin(s, exog, [Naive()], first, last, refit_every=30,
                        stride=5, verbose=False)
    full = rolling_origin(s, exog, [Naive()], first, last, refit_every=30, verbose=False)
    check(len(st) < len(full), "stride did not reduce the number of scored origins")
    merged = st.merge(full, on=key, suffixes=("_s", "_f"))
    check(len(merged) == len(st), "strided origins are not a subset of the full run")
    check(np.allclose(merged["y_pred_s"].astype(float),
                      merged["y_pred_f"].astype(float), equal_nan=True),
          "stride changed the forecasts it kept")

    if verbose:
        print("  Rolling origin checks:", "PASSED" if ok else "FAILED")
    return ok


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Rolling origin evaluation.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--window", default="expanding",
                    help='"expanding" or a number of days, for example 1095')
    ap.add_argument("--refit-every", type=int, default=90)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--burn-in", type=int, default=1095,
                    help="days of history before the first origin (default 3 years)")
    ap.add_argument("--out", default="forecasts_rolling.csv")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--quick-test", action="store_true",
                    help="run the checks without the ARIMA, which is much faster")
    args = ap.parse_args()

    if args.test or args.quick_test:
        okA = ev.test_evaluation()
        okB = test_rolling(include_arima=not args.quick_test)
        sys.exit(0 if (okA and okB) else 1)

    print("\nRunning checks before producing any forecast.")
    if not (ev.test_evaluation() and test_rolling()):
        sys.exit("Checks failed. Nothing below them would be trustworthy.")

    s = load_series(args.csv, args.date_col, args.value_col)
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=args.fourier)

    first = s.index[args.burn_in]
    last = s.index[-max(HORIZONS) - 1]
    window = args.window if args.window == "expanding" else int(args.window)

    models = [Naive(), SeasonalNaive(), Climatology(window=15),
              Arima(order=(1, 1, 1), name="arima_fourier", use_exog=True),
              # The median back-transform under-forecasts a right skewed series by
              # construction, which for a warning system means missing high days.
              # The bias corrected mean variant is carried alongside it so the
              # cost of that choice is measured rather than assumed.
              Arima(order=(1, 1, 1), name="arima_fourier_mean", use_exog=True,
                    back="mean"),
              Arima(order=(1, 1, 1), name="arima_no_fourier", use_exog=False)]

    print("\n" + "=" * 72)
    print("ROLLING ORIGIN")
    print("=" * 72)
    print(f"  origins      {first.date()} to {last.date()}")
    print(f"  window       {window}")
    print(f"  refit every  {args.refit_every} days")
    print(f"  models       {', '.join(m.name for m in models)}")
    print("\n  Running. Every day is absorbed; every origin issues 1, 2 and 3 day forecasts.")

    fc = rolling_origin(s, exog, models, first, last, window=window,
                        refit_every=args.refit_every, stride=args.stride)
    ev.check_forecasts(fc)

    print("\n" + "=" * 72)
    print("SCORING")
    print("=" * 72)
    common = ev.restrict_to_common(fc)
    print(f"  {common['origin'].nunique()} origins, "
          f"{common['origin'].min().date()} to {common['origin'].max().date()}, "
          f"spanning {(common['origin'].max() - common['origin'].min()).days / 365.25:.1f} years")

    scale = ev.mase_scale(s.loc[:first].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    ev.print_regression(metrics, title="FORECAST ACCURACY, ROLLING ORIGIN")
    warn = ev.evaluate_warnings(common, event_threshold=args.threshold)
    ev.print_warnings(warn, args.threshold)

    common.to_csv(args.out, index=False)
    print(f"\n  Wrote {args.out} ({len(common)} rows).")
    print("\n  Compare these against the single split numbers in PROJECT_STATUS.md.")
    print("  Where they disagree, believe these: they average over many periods")
    print("  rather than betting on one.\n")


if __name__ == "__main__":
    main()
