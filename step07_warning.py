"""
MTH5000 - Step 7: the warning system. Research Questions 2 and 3.

    python step07_warning.py --test
    python step07_warning.py --csv data/delhi_clean.csv --features features.csv

RESEARCH QUESTION 2: TWO WAYS TO PREDICT AN EXCEEDANCE

  Arm A, forecast then threshold. Take the concentration forecasts already
  produced, and raise an alarm when the forecast exceeds a decision threshold.
  The model never knows the event exists.

  Arm B, direct classification. Train on the binary label itself and output a
  probability, then raise an alarm when the probability exceeds a decision
  threshold. The model optimises the thing you actually care about, at the cost
  of throwing away the magnitude.

Both arms come from the same feature table, run through the same rolling origin
harness, and are scored by the same code on the same days. That is the only way
the comparison answers anything.

RESEARCH QUESTION 3: THE DECISION THRESHOLD IS THE WHOLE ARGUMENT

Every result so far has quietly assumed you raise an alarm when the forecast
exceeds the health threshold. There is no reason to. The event is fixed by health
policy; the decision is yours. Lowering it catches more hazardous days and cries
wolf more often, and the shape of that trade is the finding.

The two arms are not comparable in threshold units, one is micrograms and the
other a probability, so they are compared where they are commensurable: the plane
of hit rate against false alarm rate. Each model traces a curve as its own
threshold sweeps, and the curves can be read against each other directly.

WHAT MAKES THIS DIFFERENT FROM AN ORDINARY ROC PLOT

Alarms per year is carried alongside, because a false alarm rate of 0.10 sounds
small and means roughly one wasted alarm every ten quiet days, which is the
number an operator actually lives with. A warning system is chosen by what it
costs to run, not by the area under a curve.
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step03_benchmarks import HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Naive, rolling_origin
    from step06_ml import SklearnForecaster, load_features, TunedRegressor
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1 to 6 and evaluation.py beside this script. {e}")

EXCEED_PREFIX = "exceed_h"


class ClassifierForecaster(SklearnForecaster):
    """Predicts the probability of exceedance rather than the concentration.

    y_pred in the forecast table is therefore a probability in [0, 1] while
    y_true stays a concentration, so the event can still be recomputed from the
    observation at scoring time and the two arms remain comparable.
    """

    def _training_rows(self, window_index, origin, h):
        cutoff = origin - pd.Timedelta(days=h)
        idx = window_index[window_index <= cutoff].intersection(self.features.index)
        if len(idx) == 0:
            return None, None
        block = self.features.loc[idx]
        target = block[f"{EXCEED_PREFIX}{h}"]
        keep = target.notna()
        if not self.handles_nan:
            keep &= block[self.feature_cols].notna().all(axis=1)
        if keep.sum() < self.min_train:
            return None, None
        y = target.loc[keep].astype(int)
        # Refuse a window that contains only one class: a classifier fitted on it
        # would be a constant, and a constant that happens to match the majority
        # looks like skill in every metric that ignores the minority.
        if y.nunique() < 2:
            return None, None
        return block.loc[keep, self.feature_cols], y

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
                out[h] = float(est.predict_proba(row.values)[0, 1])
        return out


class ProbaTuned(TunedRegressor):
    """Same in-window selection, scored by log loss instead of absolute error."""

    def fit(self, X, y):
        from sklearn.metrics import log_loss
        n = len(y)
        cut = int((1 - self.holdout) * n)
        best, best_score = None, np.inf
        if cut > 50 and n - cut > 30 and len(np.unique(y[:cut])) > 1:
            for cfg in self.grid:
                m = self.build(**cfg)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m.fit(X[:cut], y[:cut])
                    p = m.predict_proba(X[cut:])[:, 1]
                try:
                    score = log_loss(y[cut:], p, labels=[0, 1])
                except ValueError:
                    score = np.inf
                if score < best_score:
                    best, best_score = cfg, score
        if best is None:
            best = self.grid[0]
        self.chosen_ = best
        self.model_ = self.build(**best)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model_.fit(X, y)
        return self

    def predict_proba(self, X):
        return self.model_.predict_proba(X)


def make_logistic():
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    def build(**kw):
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, class_weight="balanced",
                                         **kw)),
        ])
    grid = [dict(C=0.05), dict(C=0.3), dict(C=1.0), dict(C=5.0)]
    return ProbaTuned(build, grid, name="logistic")


def make_forest_clf():
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import RandomForestClassifier

    def build(**kw):
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("model", RandomForestClassifier(n_estimators=200, n_jobs=-1,
                                             random_state=0,
                                             class_weight="balanced_subsample",
                                             **kw)),
        ])
    grid = [dict(min_samples_leaf=5, max_features=0.4),
            dict(min_samples_leaf=20, max_features=0.4),
            dict(min_samples_leaf=50, max_features=0.6)]
    return ProbaTuned(build, grid, name="forest_clf")


def make_hgb_clf():
    from sklearn.ensemble import HistGradientBoostingClassifier

    def build(**kw):
        return HistGradientBoostingClassifier(early_stopping=False,
                                              random_state=0,
                                              class_weight="balanced", **kw)
    grid = [dict(max_iter=200, learning_rate=0.05, max_leaf_nodes=4,
                 min_samples_leaf=60, l2_regularization=5.0),
            dict(max_iter=300, learning_rate=0.05, max_leaf_nodes=7,
                 min_samples_leaf=40, l2_regularization=1.0),
            dict(max_iter=150, learning_rate=0.03, max_leaf_nodes=7,
                 min_samples_leaf=60, l2_regularization=10.0)]
    return ProbaTuned(build, grid, name="hgb_clf")


# ----------------------------------------------------------------------------
# Sweeping
# ----------------------------------------------------------------------------

def sweep_model(df, event_threshold, thresholds):
    """(hit rate, false alarm rate, precision, alarms per year) along a sweep."""
    rows = []
    for (model, h), g in df.groupby(["model", "horizon"]):
        yp = g["y_pred"].values
        truth = g["y_true"].values > event_threshold
        years = len(g) / 365.25
        for d in thresholds:
            c = ev.contingency(yp > d, truth)
            m = ev.warning_metrics(c, n_days=len(g))
            rows.append({"model": model, "horizon": int(h), "threshold": d,
                         "hit_rate": m["hit_rate"],
                         "false_alarm_rate": m["false_alarm_rate"],
                         "precision": m["precision"],
                         "csi": m["csi"], "peirce": m["peirce"],
                         "alarms_per_year": (c["hits"] + c["false_alarms"]) / years})
    return pd.DataFrame(rows)


def sweep_both_arms(reg, clf, event_threshold):
    a = sweep_model(reg, event_threshold,
                    np.round(np.arange(20, 401, 2.5), 2)) if len(reg) else pd.DataFrame()
    b = sweep_model(clf, event_threshold,
                    np.round(np.arange(0.005, 1.0, 0.005), 4)) if len(clf) else pd.DataFrame()
    if len(a):
        a["arm"] = "forecast then threshold"
    if len(b):
        b["arm"] = "direct classification"
    return pd.concat([x for x in (a, b) if len(x)], ignore_index=True)


def operating_point_at_alarms(sweep, model, horizon, budget):
    """The best hit rate available within a budget of alarms per year.

    This is the question an operator asks. Not "what is the AUC", but "if I can
    justify raising N alarms a year, how many hazardous days do I catch".
    """
    g = sweep[(sweep.model == model) & (sweep.horizon == horizon) &
              (sweep.alarms_per_year <= budget)]
    if not len(g):
        return None
    return g.loc[g["hit_rate"].idxmax()]


# ----------------------------------------------------------------------------

def test_warning(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    n = 600
    rng = np.random.default_rng(0)
    truth = rng.gamma(2, 60, n)
    df = pd.DataFrame({
        "origin": pd.date_range("2020-01-01", periods=n, freq="D"),
        "horizon": 1, "model": "probe",
        "y_true": truth,
        "y_pred": np.clip(truth + rng.normal(0, 25, n), 1, None)})

    sw = sweep_model(df, 121.0, np.arange(20, 400, 5.0))
    sw = sw.sort_values("threshold")
    hr = sw["hit_rate"].values
    fa = sw["false_alarm_rate"].values
    check(all(hr[i] >= hr[i + 1] - 1e-12 for i in range(len(hr) - 1)),
          "hit rate must not increase as the decision threshold rises")
    check(all(fa[i] >= fa[i + 1] - 1e-12 for i in range(len(fa) - 1)),
          "false alarm rate must not increase as the decision threshold rises")
    check(np.nanmax(hr) > 0.95 and np.nanmin(hr) < 0.05,
          "the sweep does not span the full range of operating points")

    # Alarms per year must fall as the threshold rises.
    ap = sw["alarms_per_year"].values
    check(all(ap[i] >= ap[i + 1] - 1e-9 for i in range(len(ap) - 1)),
          "alarms per year must not increase as the threshold rises")

    # The alarm budget lookup must respect the budget.
    op = operating_point_at_alarms(sw, "probe", 1, 60.0)
    check(op is not None and op["alarms_per_year"] <= 60.0,
          "the operating point exceeded the alarm budget")

    # A perfect forecast should reach a hit rate of 1 with no false alarms.
    perfect = df.copy(); perfect["y_pred"] = perfect["y_true"]
    sp = sweep_model(perfect, 121.0, [121.0])
    check(abs(sp["hit_rate"].iloc[0] - 1.0) < 1e-12 and
          abs(sp["false_alarm_rate"].iloc[0]) < 1e-12,
          "a perfect forecast is not scoring perfectly")

    # A classifier training window with one class only must be refused.
    idx = pd.date_range("2020-01-01", periods=400, freq="D")
    f = pd.DataFrame({"lag_0": np.arange(400.0)}, index=idx)
    for h in HORIZONS:
        f[f"{EXCEED_PREFIX}{h}"] = 0          # never an exceedance
        f[f"target_h{h}"] = 1.0
    c = ClassifierForecaster("c", make_logistic, f, ["lag_0"], min_train=10)
    X, y = c._training_rows(idx, idx[300], 1)
    check(X is None, "a single class training window should be refused, not fitted")

    if verbose:
        print("  Warning system checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Warning system, RQ2 and RQ3.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--features", default="features.csv")
    ap.add_argument("--regression", default="forecasts_all.csv")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--refit-every", type=int, default=90)
    ap.add_argument("--burn-in", type=int, default=1095)
    ap.add_argument("--out-clf", default="forecasts_classification.csv")
    ap.add_argument("--out-sweep", default="threshold_sweep.csv")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if (ev.test_evaluation() and test_warning()) else 1)

    print("\nRunning checks before fitting anything.")
    if not (ev.test_evaluation() and test_warning()):
        sys.exit("Checks failed.")

    s = load_series(args.csv, "date", "PM2.5")
    feats, cols = load_features(args.features)
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=args.fourier)

    models = [
        ClassifierForecaster("logistic", make_logistic, feats, cols),
        ClassifierForecaster("forest_clf", make_forest_clf, feats, cols),
        ClassifierForecaster("hgb_clf", make_hgb_clf, feats, cols, handles_nan=True),
    ]
    first, last = s.index[args.burn_in], s.index[-max(HORIZONS) - 1]

    print("\n" + "=" * 72)
    print("ARM B: DIRECT CLASSIFICATION, ROLLING ORIGIN")
    print("=" * 72)
    print(f"  origins {first.date()} to {last.date()}, refit every {args.refit_every} days")
    clf = rolling_origin(s, exog, models, first, last, refit_every=args.refit_every)
    clf.to_csv(args.out_clf, index=False)
    print(f"  Wrote {args.out_clf} ({len(clf)} rows).")

    reg = pd.read_csv(args.regression, parse_dates=["origin"])

    # Restrict both arms to the days every model in both arms could forecast.
    both = pd.concat([reg, clf], ignore_index=True)
    common = ev.restrict_to_common(both)
    keys = set(zip(common["origin"], common["horizon"]))
    reg_c = reg[[k in keys for k in zip(reg["origin"], reg["horizon"])]]
    clf_c = clf[[k in keys for k in zip(clf["origin"], clf["horizon"])]]

    print("\n" + "=" * 72)
    print("THRESHOLD SWEEP")
    print("=" * 72)
    sweep = sweep_both_arms(reg_c, clf_c, args.threshold)
    sweep.to_csv(args.out_sweep, index=False)
    print(f"  Wrote {args.out_sweep} ({len(sweep)} rows).")

    for h in HORIZONS:
        print("\n" + "=" * 72)
        print(f"BEST HIT RATE WITHIN AN ALARM BUDGET, h = {h}")
        print("=" * 72)
        print(f"  {'budget/yr':>9}  {'model':<20} {'arm':<24} {'hit':>6} {'falarm':>7} {'prec':>6}")
        for budget in (40, 60, 80, 100):
            best, best_row = None, None
            for m in sweep["model"].unique():
                op = operating_point_at_alarms(sweep, m, h, budget)
                if op is not None and (best is None or op["hit_rate"] > best):
                    best, best_row = op["hit_rate"], op
            if best_row is not None:
                print(f"  {budget:>9}  {best_row['model']:<20} {best_row['arm']:<24} "
                      f"{best_row['hit_rate']:6.3f} {best_row['false_alarm_rate']:7.3f} "
                      f"{best_row['precision']:6.3f}")

    print("\n  The event stays fixed at the health threshold; only the decision moves.")
    print("  Report the curve, not a single operating point, and state the alarm")
    print("  budget any headline number was chosen under.\n")


if __name__ == "__main__":
    main()
