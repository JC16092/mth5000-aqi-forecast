"""
MTH5000 - Step 6: the machine learning suite, inside the same harness.

    python step06_ml.py --test
    python step06_ml.py --csv data/delhi_clean.csv --features features.csv

THE LABEL AVAILABILITY TRAP

This is the one mistake that is specific to supervised learning under a rolling
origin, and it is invisible when you make it.

A row of the feature table dated t' carries a target equal to the concentration
on day t' + h. Standing at origin t, that label is only known if t' + h is less
than or equal to t. So the training set at origin t is not "every feature row up
to t"; it is every row up to **t minus h**. Using rows between t - h and t means
training on labels drawn from days the forecaster has not lived through yet.

The error is small in row count, three rows per refit at h = 3, and it is
completely undetectable in the output: nothing crashes, the numbers just improve.
A separate model is trained per horizon precisely so that this cutoff can differ
by horizon, which is what the arithmetic requires.

WHY PRECOMPUTED FEATURES ARE NOT THEMSELVES A LEAK

The feature table is built once, from the whole series, before the harness runs.
That is safe only because every feature in it is a function of days up to and
including its own row date, which `step02_features.py --test` asserts by
corrupting the future and demanding that earlier rows do not change. No feature
uses a global mean, a global scaling constant, or a value from a later row. If
that ever stops being true, this script becomes a leak and the harness will not
catch it, because the harness can only police what it is given.

PREDICTING THE LEVEL OR THE CHANGE

A tree ensemble outputs a piecewise constant function of its inputs. On a series
this persistent, the best forecast is close to yesterday's value plus a small
correction, and a linear model can represent that exactly while a tree can only
approximate it in steps. Worse, trees cannot extrapolate beyond the range of
targets they were trained on, and this series drifts downward across the decade.

So each tree model is fitted twice. Once on the level, which is the obvious thing
to do and the thing most people do. Once on the CHANGE, target minus the value at
the origin, with the origin value added back at prediction time. The second form
asks the tree to model a roughly stationary quantity and hands it the persistence
for free. If the difference between the two is large, that is a finding about how
these models should be applied to persistent series, and it belongs in the report.

REPRODUCIBILITY OF THE TREE MODELS

Running this on two different computers produced individual gradient boosting
forecasts differing by up to 85 micrograms per cubic metre. Two causes compounded.
Scikit-learn's histogram gradient boosting parallelises histogram construction
with OpenMP, and floating point summation order then depends on how many threads
the machine has, so a fixed random_state is not sufficient for bit reproducibility.
Those small differences then flipped which configuration the capacity search chose
at some refits, turning a rounding difference into a different model.

Both are addressed here. Thread counts are pinned to one inside every tuned fit
and prediction, and the search only abandons an earlier configuration for a later
one when the later one is better by more than a relative margin, so numerical
noise cannot decide the choice. Pinning threads roughly doubles the random forest
fitting time and costs the gradient boosting almost nothing.

The honest note for the report: aggregated over 2,303 origins the two machines
agreed to within 0.004 of relative mean absolute error on every model, and no
conclusion depended on the difference. But 0.004 is the same order as the gap
between adjacent machine learning models in the results table, which is itself
part of the finding rather than an embarrassment.

CAPACITY IS CHOSEN, NOT ASSUMED

The first run of this script reported that gradient boosting was worse than
persistence at one day ahead, which would have been a striking negative result.
It was wrong. A quick check on validation showed the configuration was
overfitting: 400 boosting iterations over 31 leaf nodes on roughly two thousand
rows gave rMAE 1.085, while four leaf nodes over 200 iterations gave 0.970. The
method was fine; the settings were not.

So the tree models now choose their capacity at every refit, from a small
explicit grid, scored on the last fifth of the training window held out
chronologically. That block sits before the origin, so nothing from the future
enters the choice, and the grid is small enough to print in an appendix. Refitting
on the full window follows once the winner is known.

The lesson is worth stating in the report: a negative result about a model class
is only worth reporting once you have shown it is not a negative result about
your own hyperparameters.

MISSING VALUES, PER MODEL

Gradient boosting takes NaN natively and gets the table as it is. Ridge and the
random forest cannot, so they sit behind an imputer that is fitted inside the
training window at each refit and never on the full table. Imputing before
splitting is a classic and quiet way to move information backwards in time.
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step04_arima import fourier_terms
    from step05_rolling import (Forecaster, Naive, SeasonalNaive, Climatology,
                                Arima, rolling_origin)
    from step03_benchmarks import HORIZONS
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1 to 5 and evaluation.py beside this script. {e}")


TARGET_PREFIX = "target_h"


def load_features(path):
    f = pd.read_csv(path, parse_dates=["date"]).set_index("date")
    feature_cols = [c for c in f.columns
                    if not c.startswith(("target_", "exceed_h"))]
    return f, feature_cols


class SklearnForecaster(Forecaster):
    """Any scikit-learn regressor, one model per horizon, refitted on demand."""

    def __init__(self, name, make_estimator, features, feature_cols,
                 handles_nan=False, min_train=400, target="level",
                 anchor="lag_0"):
        self.name = name
        self.make_estimator = make_estimator
        self.features = features
        self.feature_cols = feature_cols
        self.handles_nan = handles_nan
        self.min_train = min_train
        self.target = target          # "level" or "delta"
        self.anchor = anchor          # the column added back for "delta"
        self.models = {}
        self.origin = None

    def _training_rows(self, window_index, origin, h):
        """Rows whose label was already observable at the origin.

        The cutoff is origin minus h days. One day later and the label lies in
        the forecaster's future.
        """
        cutoff = origin - pd.Timedelta(days=h)
        idx = window_index[window_index <= cutoff]
        idx = idx.intersection(self.features.index)
        if len(idx) == 0:
            return None, None
        block = self.features.loc[idx]
        target = block[f"{TARGET_PREFIX}{h}"]
        if self.target == "delta":
            # Model the change from the origin value. Adding it back at
            # prediction time gives the level, so nothing about the target
            # definition changes for scoring.
            target = target - block[self.anchor]
        keep = target.notna()
        if not self.handles_nan:
            keep &= block[self.feature_cols].notna().all(axis=1)
        if keep.sum() < self.min_train:
            return None, None
        return block.loc[keep, self.feature_cols], target.loc[keep]

    def start(self, y_hist, exog_hist):
        self.origin = y_hist.index[-1]
        self.models = {}
        for h in HORIZONS:
            X, y = self._training_rows(y_hist.index, self.origin, h)
            if X is None:
                continue
            est = self.make_estimator()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                est.fit(X.values, y.values)
            self.models[h] = est

    def update(self, day, y_value, exog_row):
        # Parameters are held between refits, exactly as for the ARIMA. Only the
        # origin moves, which is what selects the feature row used at prediction.
        self.origin = day

    def predict(self, horizons, future_exog):
        out = {}
        for h in horizons:
            est = self.models.get(h)
            if est is None or self.origin not in self.features.index:
                out[h] = np.nan
                continue
            row = self.features.loc[[self.origin], self.feature_cols]
            if not self.handles_nan and row.isna().any().any():
                out[h] = np.nan
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pred = float(est.predict(row.values)[0])
            if self.target == "delta":
                base = self.features.loc[self.origin, self.anchor]
                pred = np.nan if pd.isna(base) else pred + base
            out[h] = pred
        return out


# ----------------------------------------------------------------------------
# The estimators
# ----------------------------------------------------------------------------

def _single_threaded():
    """Pin BLAS and OpenMP to one thread, so results do not depend on the machine."""
    try:
        from threadpoolctl import threadpool_limits
        return threadpool_limits(limits=1)
    except Exception:
        import contextlib
        return contextlib.nullcontext()


class TunedRegressor:
    """Pick a configuration on a chronological holdout inside the training window.

    Ordinary grid search with K fold cross validation would train on rows that
    come after the rows it scores, which is the wrong habit in a forecasting
    project even when it is confined to training data. This holds out the last
    fifth of the window in time order instead.
    """

    def __init__(self, build, grid, holdout=0.2, name="", margin=0.005):
        self.build = build
        self.grid = grid
        self.holdout = holdout
        self.name = name
        # A later configuration must beat the incumbent by more than this
        # relative margin to replace it. Without it, a difference of one part in
        # ten thousand, which is within the numerical noise between machines,
        # decides which model is fitted.
        self.margin = margin
        self.chosen_ = None
        self.model_ = None

    def fit(self, X, y):
        n = len(y)
        cut = int((1 - self.holdout) * n)
        best, best_mae = None, np.inf
        if cut > 50 and n - cut > 30:
            for cfg in self.grid:
                m = self.build(**cfg)
                with warnings.catch_warnings(), _single_threaded():
                    warnings.simplefilter("ignore")
                    m.fit(X[:cut], y[:cut])
                    mae = float(np.mean(np.abs(m.predict(X[cut:]) - y[cut:])))
                if mae < best_mae * (1.0 - self.margin):
                    best, best_mae = cfg, mae
                elif best is None:
                    best, best_mae = cfg, mae
        if best is None:
            best = self.grid[0]
        self.chosen_ = best
        self.model_ = self.build(**best)
        with warnings.catch_warnings(), _single_threaded():
            warnings.simplefilter("ignore")
            self.model_.fit(X, y)
        return self

    def predict(self, X):
        with _single_threaded():
            return self.model_.predict(X)


def make_ridge():
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import TimeSeriesSplit
    # TimeSeriesSplit rather than plain K fold: ordinary cross validation would
    # train on rows that come after the rows it validates on, which inside a
    # forecasting project is the wrong habit even where it is technically
    # confined to the training window.
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", RidgeCV(alphas=np.logspace(-2, 4, 25), cv=TimeSeriesSplit(n_splits=4))),
    ])


FOREST_GRID = [
    dict(min_samples_leaf=3, max_features=0.4),
    dict(min_samples_leaf=15, max_features=0.4),
    dict(min_samples_leaf=40, max_features=0.6),
]


def make_forest():
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import RandomForestRegressor

    def build_named(**kw):
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("model", RandomForestRegressor(n_estimators=200, n_jobs=-1,
                                            random_state=0, **kw)),
        ])

    return TunedRegressor(build_named, FOREST_GRID, name="random_forest")


HGB_GRID = [
    dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=4,
         min_samples_leaf=60, l2_regularization=5.0),
    dict(max_iter=150, learning_rate=0.03, max_leaf_nodes=7,
         min_samples_leaf=60, l2_regularization=10.0),
    dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=7,
         min_samples_leaf=40, l2_regularization=1.0),
    dict(max_iter=400, learning_rate=0.05, max_leaf_nodes=31,
         min_samples_leaf=20, l2_regularization=1.0),
]


def make_hgb():
    # Histogram based gradient boosting, scikit-learn's implementation of the
    # LightGBM family. Chosen over LightGBM because macOS ships no OpenMP
    # runtime and LightGBM could not be imported. Takes NaN natively, which is
    # why it alone sees the feature table unmodified. The last entry in the grid
    # is the configuration that overfitted on the first run; it is kept so the
    # search can still choose it if the data ever warrants it.
    from sklearn.ensemble import HistGradientBoostingRegressor

    def build(**kw):
        return HistGradientBoostingRegressor(early_stopping=False,
                                             random_state=0, **kw)

    return TunedRegressor(build, HGB_GRID, name="hist_gbm")


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def test_ml(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    # A feature table where the target is a clean function of a future value, so
    # any use of an unavailable label is immediately visible.
    idx = pd.date_range("2020-01-01", periods=900, freq="D")
    rng = np.random.default_rng(0)
    v = pd.Series(50 + 20 * np.sin(np.arange(900) / 30) + rng.normal(0, 3, 900), index=idx)
    f = pd.DataFrame({"lag_0": v, "lag_1": v.shift(1)}, index=idx)
    for h in HORIZONS:
        f[f"{TARGET_PREFIX}{h}"] = v.shift(-h)

    fc = SklearnForecaster("probe", make_ridge, f, ["lag_0", "lag_1"], min_train=50)

    # 1. The label cutoff must be origin minus h, exactly.
    origin = idx[500]
    for h in HORIZONS:
        X, y = fc._training_rows(idx[:501], origin, h)
        check(X.index.max() == origin - pd.Timedelta(days=h),
              f"h={h}: last training row is {X.index.max().date()}, "
              f"expected {(origin - pd.Timedelta(days=h)).date()}")
        # And that row's label must be a day the forecaster has already seen.
        check(X.index.max() + pd.Timedelta(days=h) <= origin,
              f"h={h}: training used a label from after the origin")

    # 2. Corrupting the series strictly after the origin must not change training.
    f2 = f.copy()
    after = f2.index > origin
    f2.loc[after, :] = f2.loc[after, :] * 99 + 1000
    fc2 = SklearnForecaster("probe", make_ridge, f2, ["lag_0", "lag_1"], min_train=50)
    for h in HORIZONS:
        Xa, ya = fc._training_rows(idx[:501], origin, h)
        Xb, yb = fc2._training_rows(idx[:501], origin, h)
        check(np.allclose(Xa.values, Xb.values, equal_nan=True) and
              np.allclose(ya.values, yb.values, equal_nan=True),
              f"h={h}: training data changed when the future was corrupted")

    # 3. The delta target must round trip exactly: modelling the change and
    #    adding the origin value back must recover the level.
    d = SklearnForecaster("d", make_ridge, f, ["lag_0", "lag_1"],
                          min_train=50, target="delta")
    for h in HORIZONS:
        Xl, yl = fc._training_rows(idx[:501], origin, h)
        Xd, yd = d._training_rows(idx[:501], origin, h)
        check(np.allclose(yl.values - f.loc[yl.index, "lag_0"].values, yd.values,
                          equal_nan=True),
              f"h={h}: the delta target is not target minus the anchor")
    d.start(v.loc[:origin], None)
    fc.start(v.loc[:origin], None)
    pl = fc.predict(HORIZONS, None)
    pd_ = d.predict(HORIZONS, None)
    check(all(np.isfinite(x) for x in pd_.values()),
          "the delta model produced no finite forecast")

    # 4. Too little history must decline to predict rather than guess.
    thin = SklearnForecaster("thin", make_ridge, f, ["lag_0", "lag_1"], min_train=10_000)
    thin.start(v.loc[:origin], None)
    check(all(np.isnan(x) for x in thin.predict(HORIZONS, None).values()),
          "a model with too little training data should return NaN, not a guess")

    # 5. End to end through the harness, including the corruption test that the
    #    harness itself applies to every model it is given.
    from step05_rolling import test_rolling
    ext = idx.append(pd.date_range(idx[-1] + pd.Timedelta(days=1), periods=3, freq="D"))
    exog = fourier_terms(ext, K=2)
    v.name = "PM2.5"

    def build():
        return [Naive(),
                SklearnForecaster("ridge", make_ridge, f, ["lag_0", "lag_1"], min_train=50)]

    base = rolling_origin(v, exog, build(), idx[600], idx[700], refit_every=30, verbose=False)
    check(base[base.model == "ridge"]["y_pred"].notna().sum() > 0,
          "the ridge produced no forecasts through the harness")

    cut = idx[650]
    poisoned = v.copy()
    poisoned.loc[cut:] = poisoned.loc[cut:] * 9 + 500
    fp = f.copy()
    bad = fp.index >= cut
    fp.loc[bad, :] = fp.loc[bad, :] * 9 + 500

    def build_p():
        return [Naive(),
                SklearnForecaster("ridge", make_ridge, fp, ["lag_0", "lag_1"], min_train=50)]

    after_run = rolling_origin(poisoned, exog, build_p(), idx[600], idx[700],
                               refit_every=30, verbose=False)
    key = ["origin", "horizon", "model"]
    a = base[base.origin < cut].set_index(key)["y_pred"].sort_index()
    b = after_run[after_run.origin < cut].set_index(key)["y_pred"].sort_index()
    check(a.index.equals(b.index), "the corrupted run produced a different set of rows")
    if a.index.equals(b.index):
        diff = ~np.isclose(a.values.astype(float), b.values.astype(float),
                           rtol=1e-8, atol=1e-8, equal_nan=True)
        offenders = sorted(set(a.index[diff].get_level_values("model"))) if diff.any() else []
        check(not diff.any(),
              f"LEAK: {int(diff.sum())} forecasts before the cut changed. {offenders}")

    if verbose:
        print("  Machine learning checks:", "PASSED" if ok else "FAILED")
    return ok


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Machine learning suite, rolling origin.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--features", default="features.csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--window", default="expanding")
    ap.add_argument("--refit-every", type=int, default=90)
    ap.add_argument("--burn-in", type=int, default=1095)
    ap.add_argument("--out", default="forecasts_all.csv")
    ap.add_argument("--no-arima", action="store_true",
                    help="skip the ARIMA, which is the slow one, for a quick look")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if (ev.test_evaluation() and test_ml()) else 1)

    print("\nRunning checks before fitting anything.")
    if not (ev.test_evaluation() and test_ml()):
        sys.exit("Checks failed. Nothing below them would be trustworthy.")

    s = load_series(args.csv, args.date_col, args.value_col)
    feats, feature_cols = load_features(args.features)
    print(f"\n  Feature table: {len(feats)} rows, {len(feature_cols)} feature columns.")

    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=args.fourier)

    models = [Naive(), SeasonalNaive(), Climatology(window=15)]
    if not args.no_arima:
        models += [Arima(order=(1, 1, 1), name="arima_fourier", use_exog=True)]
    models += [
        SklearnForecaster("ridge", make_ridge, feats, feature_cols),
        SklearnForecaster("random_forest", make_forest, feats, feature_cols),
        SklearnForecaster("hist_gbm", make_hgb, feats, feature_cols, handles_nan=True),
        SklearnForecaster("random_forest_delta", make_forest, feats, feature_cols,
                          target="delta"),
        SklearnForecaster("hist_gbm_delta", make_hgb, feats, feature_cols,
                          handles_nan=True, target="delta"),
    ]

    first = s.index[args.burn_in]
    last = s.index[-max(HORIZONS) - 1]
    window = args.window if args.window == "expanding" else int(args.window)

    print("\n" + "=" * 72)
    print("ROLLING ORIGIN, CLASSICAL AND MACHINE LEARNING TOGETHER")
    print("=" * 72)
    print(f"  origins      {first.date()} to {last.date()}")
    print(f"  window       {window}, refit every {args.refit_every} days")
    print(f"  models       {', '.join(m.name for m in models)}")
    print("\n  Running.")

    fc = rolling_origin(s, exog, models, first, last, window=window,
                        refit_every=args.refit_every)
    ev.check_forecasts(fc)

    print("\n" + "=" * 72)
    print("SCORING")
    print("=" * 72)
    common = ev.restrict_to_common(fc)
    print(f"  {common['origin'].nunique()} origins, "
          f"{common['origin'].min().date()} to {common['origin'].max().date()}")

    scale = ev.mase_scale(s.loc[:first].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    ev.print_regression(metrics, title="FORECAST ACCURACY, ROLLING ORIGIN")
    warn = ev.evaluate_warnings(common, event_threshold=args.threshold)
    ev.print_warnings(warn, args.threshold)

    common.to_csv(args.out, index=False)
    print(f"\n  Wrote {args.out} ({len(common)} rows, {common['model'].nunique()} models).")

    print("\n" + "=" * 72)
    print("RESEARCH QUESTION 1")
    print("=" * 72)
    for h in HORIZONS:
        sub = metrics[metrics.horizon == h].sort_values("rMAE")
        best = sub.iloc[0]
        ml = sub[sub.model.isin(["ridge", "random_forest", "hist_gbm"])]
        best_ml = ml.iloc[0] if len(ml) else None
        line = f"  h={h}: best overall {best['model']} at rMAE {best['rMAE']:.3f}"
        if best_ml is not None and best_ml["model"] != best["model"]:
            line += f"; best ML {best_ml['model']} at {best_ml['rMAE']:.3f}"
        print(line)
    print("\n  If the machine learning does not beat the classical benchmark, say so.")
    print("  A negative result from a sound evaluation is a result.\n")


if __name__ == "__main__":
    main()
