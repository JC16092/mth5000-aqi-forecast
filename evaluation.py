"""
MTH5000 - shared evaluation. Imported by steps 3 onward.

Every model in the project is scored by this module and by nothing else. That is
the point of it. If SARIMA were scored by one piece of code and gradient boosting
by another, any difference between them could be a difference in the scoring
rather than in the models, and the comparison that the whole project rests on
would be worthless.

THE FORECAST TABLE

Everything flows through one long table with five columns:

    origin      the date the forecast was issued, the last day whose value was known
    horizon     1, 2 or 3 days ahead
    model       name of the method
    y_pred      the forecast
    y_true      what actually happened

Every metric, table and figure in the report is a groupby on this object. It is
written to disk so that week 5 can compute warning system performance without
refitting anything.

TWO DEFINITIONS THAT ARE EASY TO CONFUSE

False alarm RATE is FP / (FP + TN), the share of quiet days that raised an alarm.
False alarm RATIO is FP / (TP + FP), the share of alarms that were wrong.
Meteorology uses both and they answer different questions. Both are reported
here, named in full, because using one and calling it the other is a classic way
to make a warning system look better than it is.

THE DECISION THRESHOLD IS NOT THE EVENT THRESHOLD

The event is fixed: a day is hazardous if the observed value exceeds the health
threshold. The decision is free: you may raise an alarm at any predicted value
you choose. Setting the decision threshold below the event threshold buys hit
rate at the cost of false alarms. Sweeping it is what produces the curve that
answers Research Question 3, so the two are kept as separate arguments
throughout and never collapsed into one number.
"""

import sys

import numpy as np
import pandas as pd

FORECAST_COLUMNS = ["origin", "horizon", "model", "y_pred", "y_true"]


# ----------------------------------------------------------------------------
# Assembling and guarding the forecast table
# ----------------------------------------------------------------------------

def new_forecasts():
    return pd.DataFrame(columns=FORECAST_COLUMNS)


def check_forecasts(df):
    missing = [c for c in FORECAST_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"Forecast table is missing columns: {missing}")
    if df["horizon"].isna().any():
        sys.exit("Forecast table has a null horizon.")
    dup = df.duplicated(["origin", "horizon", "model"]).sum()
    if dup:
        sys.exit(f"Forecast table has {dup} duplicated (origin, horizon, model) rows.")
    return df


def restrict_to_common(df, verbose=True):
    """Keep only the origins every model can forecast, so the comparison is fair.

    Models fail on different days. Persistence needs yesterday, the seasonal
    benchmark needs the same weekday a week earlier, and a machine learning model
    needs a complete feature row. If each is scored on whatever days it happens to
    manage, a model that quietly declines the hardest days looks better than one
    that attempts them. Scoring every model on the intersection removes that
    advantage. Report how many rows it costs.
    """
    ok = df.dropna(subset=["y_pred", "y_true"])
    n_models = df["model"].nunique()
    counts = ok.groupby(["origin", "horizon"])["model"].nunique()
    keep = counts[counts == n_models].index
    out = ok.set_index(["origin", "horizon"]).loc[keep].reset_index()

    if verbose:
        lost = len(ok) - len(out)
        print(f"  Common rows: {len(out)} kept, {lost} dropped so that all "
              f"{n_models} models are scored on identical days.")
    return out


# ----------------------------------------------------------------------------
# Regression metrics
# ----------------------------------------------------------------------------

def mase_scale(train_values):
    """Denominator for MASE: mean absolute one step change in the training data.

    Hyndman's scaling. It makes the error scale free and interpretable: a MASE
    below 1 beats the one step naive forecast, above 1 loses to it. Computed on
    training data only, so the scale itself cannot carry information from the
    test period.
    """
    v = pd.Series(train_values).dropna().values
    if len(v) < 2:
        raise ValueError("Need at least two training points for the MASE scale.")
    return float(np.mean(np.abs(np.diff(v))))


def regression_metrics(df, scale, reference="naive"):
    """MAE, RMSE, MASE, relative MAE and bias, per model and horizon.

    Two scale free numbers are reported and they answer different questions.

    MASE divides by the mean absolute one step change in the TRAINING data. That
    is the standard definition and it keeps the scale free of the test period,
    but it becomes hard to read when the test period is calmer than the training
    period: every model's MASE falls, including the naive forecast's, and a
    reader who expects naive to score 1.0 will be misled.

    rMAE divides by the naive forecast's MAE on exactly the same rows. It answers
    the question the project actually asks, which is whether a model beats
    persistence here, and it is immune to a change in volatility between periods.
    Below 1 beats the reference; above 1 loses to it.
    """
    rows = []
    for (model, h), g in df.groupby(["model", "horizon"]):
        e = g["y_pred"].values - g["y_true"].values
        rows.append({
            "model": model, "horizon": int(h), "n": len(g),
            "MAE": np.mean(np.abs(e)),
            "RMSE": np.sqrt(np.mean(e ** 2)),
            "MASE": np.mean(np.abs(e)) / scale,
            "bias": np.mean(e),
        })
    out = pd.DataFrame(rows)

    ref = out[out["model"] == reference].set_index("horizon")["MAE"]
    if len(ref):
        out["rMAE"] = [r["MAE"] / ref.get(r["horizon"], np.nan) for _, r in out.iterrows()]
    else:
        out["rMAE"] = np.nan

    out = out.sort_values(["horizon", "MAE"])
    return out.reset_index(drop=True)


# ----------------------------------------------------------------------------
# Warning system metrics
# ----------------------------------------------------------------------------

def contingency(pred_alarm, true_event):
    pred_alarm = np.asarray(pred_alarm, dtype=bool)
    true_event = np.asarray(true_event, dtype=bool)
    return {
        "hits": int(np.sum(pred_alarm & true_event)),
        "misses": int(np.sum(~pred_alarm & true_event)),
        "false_alarms": int(np.sum(pred_alarm & ~true_event)),
        "correct_negatives": int(np.sum(~pred_alarm & ~true_event)),
    }


def warning_metrics(c, n_days=None):
    """Turn a contingency table into the numbers an operator cares about."""
    h, m, f, n = c["hits"], c["misses"], c["false_alarms"], c["correct_negatives"]
    total = h + m + f + n

    hit_rate = h / (h + m) if (h + m) else np.nan            # recall, POD
    far_rate = f / (f + n) if (f + n) else np.nan            # POFD
    far_ratio = f / (h + f) if (h + f) else np.nan           # 1 - precision
    precision = h / (h + f) if (h + f) else np.nan
    csi = h / (h + f + m) if (h + f + m) else np.nan         # critical success index
    pss = hit_rate - far_rate                                # Peirce skill score

    years = (n_days if n_days else total) / 365.25
    out = dict(c)
    out.update({
        "hit_rate": hit_rate,
        "false_alarm_rate": far_rate,
        "false_alarm_ratio": far_ratio,
        "precision": precision,
        "csi": csi,
        "peirce": pss,
        "alarms_per_year": (h + f) / years if years else np.nan,
        "events_per_year": (h + m) / years if years else np.nan,
    })
    return out


def evaluate_warnings(df, event_threshold, decision_threshold=None):
    """Warning performance per model and horizon at one decision threshold."""
    if decision_threshold is None:
        decision_threshold = event_threshold
    rows = []
    for (model, h), g in df.groupby(["model", "horizon"]):
        c = contingency(g["y_pred"].values > decision_threshold,
                        g["y_true"].values > event_threshold)
        r = warning_metrics(c, n_days=len(g))
        r.update({"model": model, "horizon": int(h),
                  "decision_threshold": decision_threshold})
        rows.append(r)
    cols = ["model", "horizon", "decision_threshold", "hits", "misses",
            "false_alarms", "correct_negatives", "hit_rate", "false_alarm_rate",
            "false_alarm_ratio", "precision", "csi", "peirce", "alarms_per_year"]
    return pd.DataFrame(rows)[cols].sort_values(["horizon", "model"]).reset_index(drop=True)


def sweep_threshold(df, event_threshold, decision_thresholds):
    """The curve behind Research Question 3.

    The event stays fixed; the decision moves. Lowering the decision threshold
    catches more events and raises more false alarms, and the shape of that
    trade is the result the project is actually about.
    """
    frames = [evaluate_warnings(df, event_threshold, d) for d in decision_thresholds]
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------

def print_regression(metrics, title="FORECAST ACCURACY"):
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)
    print(f"  {'horizon':>7}  {'model':<22} {'MAE':>7} {'RMSE':>7} {'rMAE':>6} "
          f"{'MASE':>6} {'bias':>7}")
    print("  " + "-" * 74)
    for h in sorted(metrics["horizon"].unique()):
        sub = metrics[metrics["horizon"] == h]
        for _, r in sub.iterrows():
            print(f"  {r['horizon']:>7}  {r['model']:<22} {r['MAE']:7.2f} "
                  f"{r['RMSE']:7.2f} {r['rMAE']:6.3f} {r['MASE']:6.3f} {r['bias']:+7.2f}")
        print("  " + "-" * 74)
    print("  rMAE is against the naive forecast on identical rows. Below 1 beats it.")
    print("  MASE uses the training period scale, so it also reflects any difference")
    print("  in volatility between training and test. Read rMAE first.")
    print("  Horizons are never averaged: skill decays with horizon and that is the point.")


def print_warnings(w, event_threshold):
    print("\n" + "=" * 72)
    print(f"AS A WARNING SYSTEM (event: observed above {event_threshold:.0f})")
    print("=" * 72)
    print(f"  {'h':>2}  {'model':<22} {'hit':>6} {'falarm':>7} {'prec':>6} "
          f"{'CSI':>6} {'PSS':>6} {'alarms/yr':>9}")
    print("  " + "-" * 68)
    for h in sorted(w["horizon"].unique()):
        for _, r in w[w["horizon"] == h].iterrows():
            print(f"  {r['horizon']:>2}  {r['model']:<22} {r['hit_rate']:6.3f} "
                  f"{r['false_alarm_rate']:7.3f} {r['precision']:6.3f} "
                  f"{r['csi']:6.3f} {r['peirce']:6.3f} {r['alarms_per_year']:9.1f}")
        print("  " + "-" * 68)
    print("  hit    = hits / events. falarm = false alarms / quiet days.")
    print("  prec   = hits / alarms raised. CSI ignores correct negatives, which")
    print("           dominate and make plain accuracy meaningless here.")
    print("  PSS    = hit rate minus false alarm rate. Zero is no skill.")


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def test_evaluation(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    # MASE scale is the mean absolute first difference.
    check(abs(mase_scale([1, 2, 4, 7]) - 2.0) < 1e-12, "mase_scale is wrong")

    # A perfect forecast scores zero error and MASE zero.
    d = pd.DataFrame({
        "origin": pd.to_datetime(["2024-01-01"] * 3),
        "horizon": [1, 2, 3], "model": ["perfect"] * 3,
        "y_pred": [10.0, 20.0, 30.0], "y_true": [10.0, 20.0, 30.0]})
    m = regression_metrics(d, scale=5.0)
    check((m["MAE"] == 0).all() and (m["MASE"] == 0).all(), "perfect forecast is not scoring zero")

    # A forecast off by a constant: MAE equals that constant, MASE equals it over the scale.
    d2 = d.copy(); d2["y_pred"] = d2["y_true"] + 5.0; d2["model"] = "off_by_five"
    m2 = regression_metrics(d2, scale=10.0)
    check(np.allclose(m2["MAE"], 5.0), "MAE wrong on a constant offset")
    check(m2["rMAE"].isna().all(), "rMAE should be undefined when the reference is absent")
    check(np.allclose(m2["MASE"], 0.5), "MASE wrong on a constant offset")
    check(np.allclose(m2["bias"], 5.0), "bias should be signed and positive here")

    # rMAE must be exactly 1 for the reference model and scale correctly for others.
    ref = pd.DataFrame({"origin": pd.to_datetime(["2024-01-01"] * 4),
                        "horizon": [1, 1, 1, 1],
                        "model": ["naive", "naive", "other", "other"],
                        "y_pred": [0.0, 0.0, 5.0, 5.0],
                        "y_true": [10.0, 20.0, 10.0, 20.0]})
    mr = regression_metrics(ref, scale=1.0).set_index("model")
    check(abs(mr.loc["naive", "rMAE"] - 1.0) < 1e-12, "reference model rMAE must be 1")
    check(abs(mr.loc["other", "rMAE"] - (10.0 / 15.0)) < 1e-12, "rMAE arithmetic is wrong")

    # Contingency and the two false alarm definitions.
    c = contingency([True, True, False, False, True],
                    [True, False, True, False, False])
    check(c == {"hits": 1, "misses": 1, "false_alarms": 2, "correct_negatives": 1},
          f"contingency wrong: {c}")
    w = warning_metrics(c, n_days=5)
    check(abs(w["hit_rate"] - 0.5) < 1e-12, "hit rate wrong")
    check(abs(w["false_alarm_rate"] - 2 / 3) < 1e-12, "false alarm RATE wrong")
    check(abs(w["false_alarm_ratio"] - 2 / 3) < 1e-12, "false alarm RATIO wrong")
    check(abs(w["precision"] - 1 / 3) < 1e-12, "precision wrong")
    check(abs(w["csi"] - 1 / 4) < 1e-12, "CSI wrong")
    check(abs(w["peirce"] - (0.5 - 2 / 3)) < 1e-12, "Peirce skill score wrong")

    # Lowering the decision threshold must never lower the hit rate.
    rng = np.random.default_rng(0)
    n = 400
    truth = rng.gamma(2, 60, n)
    d3 = pd.DataFrame({
        "origin": pd.date_range("2020-01-01", periods=n, freq="D"),
        "horizon": 1, "model": "noisy",
        "y_true": truth,
        "y_pred": np.clip(truth + rng.normal(0, 30, n), 1, None)})
    sw = sweep_threshold(d3, 121.0, [60, 90, 121, 160, 220])
    hr = sw.sort_values("decision_threshold")["hit_rate"].values
    check(all(hr[i] >= hr[i + 1] - 1e-12 for i in range(len(hr) - 1)),
          "hit rate must be non increasing as the decision threshold rises")
    fa = sw.sort_values("decision_threshold")["false_alarm_rate"].values
    check(all(fa[i] >= fa[i + 1] - 1e-12 for i in range(len(fa) - 1)),
          "false alarm rate must be non increasing as the decision threshold rises")

    # The common row restriction must drop days a model could not forecast.
    a = pd.DataFrame({"origin": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                      "horizon": [1, 1], "model": ["a", "a"],
                      "y_pred": [1.0, 2.0], "y_true": [1.0, 2.0]})
    b = a.copy(); b["model"] = "b"; b.loc[0, "y_pred"] = np.nan
    both = pd.concat([a, b], ignore_index=True)
    common = restrict_to_common(both, verbose=False)
    check(len(common) == 2, f"expected 2 common rows, got {len(common)}")
    check(set(common["origin"].dt.day) == {2}, "kept the wrong day")

    # Duplicated keys must be refused rather than silently double counted.
    try:
        check_forecasts(pd.concat([a, a], ignore_index=True))
        check(False, "duplicated (origin, horizon, model) rows were not caught")
    except SystemExit:
        pass

    if verbose:
        print("  Evaluation checks:", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if test_evaluation() else 1)
