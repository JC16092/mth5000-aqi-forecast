"""
MTH5000 - Diebold-Mariano test for equal predictive accuracy.

Section 5.2 of the report bounds "how large is a real difference between
models" empirically, by rerunning the identical pipeline and measuring how
much a score moves for reasons that have nothing to do with which model is
better. That is a measured tolerance, not a test. This module asks the same
question properly: a null hypothesis, a sampling distribution, and a
p-value, following Diebold and Mariano (1995), with the small-sample
correction of Harvey, Leybourne and Newbold (1997) referred to a t
distribution rather than DM's own asymptotic normal.
"""

import os

import numpy as np
import pandas as pd
from scipy import stats


def dm_test(e1, e2, h, loss="absolute"):
    """Diebold-Mariano test of equal predictive accuracy between two models.

    e1, e2 are forecast errors (y_true - y_pred) from models 1 and 2, the
    same length and in the same origin order: this function does not align
    them itself, since silently reordering one series relative to the other
    would corrupt the test without raising an error. h is the forecast
    horizon, which sets how many lags of the loss differential's own
    autocorrelation enter its long-run variance: an optimally fitted h-step
    forecast has errors that are at most an MA(h-1) process, so lags 1 to
    h-1 carry genuine serial correlation that a plain variance estimate
    would ignore and that would make the test overconfident. loss="absolute"
    matches this report's headline rMAE measure; "squared" is supported for
    comparison.

    Returns the mean loss differential, the DM statistic, its
    Harvey-Leybourne-Newbold (1997) small-sample correction, and the
    two-sided p-value of that correction against t(n-1).
    """
    e1 = np.asarray(e1, dtype=float)
    e2 = np.asarray(e2, dtype=float)
    if e1.shape != e2.shape:
        raise ValueError("e1 and e2 must be the same length, paired by origin.")
    n = len(e1)
    if n <= 2 * h:
        raise ValueError(f"too few paired origins ({n}) for horizon {h}.")

    if loss == "absolute":
        d = np.abs(e1) - np.abs(e2)
    elif loss == "squared":
        d = e1 ** 2 - e2 ** 2
    else:
        raise ValueError(f"unknown loss {loss!r}")

    dbar = d.mean()
    var_d = np.mean((d - dbar) ** 2)
    for k in range(1, h):
        # Divide by n throughout, not n-k: the standard convention for this
        # estimator (Diebold & Mariano 1995), which keeps the implied long
        # run variance estimate non-negative in a way dividing each lag by
        # its own, shrinking overlap count would not guarantee.
        var_d += 2 * np.sum((d[k:] - dbar) * (d[:-k] - dbar)) / n

    if var_d <= 0:
        # Two forecasts with an identical loss on every origin: no evidence
        # of a difference, which is the dbar == 0 case this degenerates to
        # in practice (a nonzero constant differential with zero variance
        # does not occur in this project's data and is not handled as a
        # signed-infinite limit here).
        dm = dm_hln = 0.0
        pvalue = 1.0
        return {"n": n, "dbar": dbar, "dm": dm, "dm_hln": dm_hln, "pvalue": pvalue}

    dm = dbar / np.sqrt(var_d / n)
    correction = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_hln = dm * correction
    pvalue = 2 * (1 - stats.t.cdf(np.abs(dm_hln), df=n - 1))
    return {"n": n, "dbar": dbar, "dm": dm, "dm_hln": dm_hln, "pvalue": pvalue}


def paired_errors(df, model_a, model_b, horizon):
    """Forecast errors for two models at one horizon, paired by origin.

    Raises rather than silently truncating if the two models were not
    scored on exactly the same days, since that mismatch is exactly the
    kind of thing that would corrupt the test without ever raising an
    error on its own.
    """
    a = df[(df.model == model_a) & (df.horizon == horizon)][["origin", "y_true", "y_pred"]]
    b = df[(df.model == model_b) & (df.horizon == horizon)][["origin", "y_pred"]]
    m = a.merge(b, on="origin", suffixes=("_a", "_b"), how="inner")
    if len(m) != len(a) or len(m) != len(b):
        raise ValueError(
            f"origins did not match between {model_a!r} and {model_b!r} at "
            f"h={horizon}: {len(a)} vs {len(b)} vs {len(m)} common")
    m = m.sort_values("origin")
    e_a = (m["y_true"] - m["y_pred_a"]).values
    e_b = (m["y_true"] - m["y_pred_b"]).values
    return e_a, e_b


def dm_over_seeds(seed_paths, seed_model, other_model, horizon, loss="absolute"):
    """Run the DM test once per GRU seed file against a fixed competitor.

    Returns one row per seed file, so the result can be reported as a
    range, the same convention Table 4.1 already uses for every other
    number that depends on the network's random initialisation.
    """
    rows = []
    for f in seed_paths:
        df = pd.read_csv(f, parse_dates=["origin"])
        e_seed, e_other = paired_errors(df, seed_model, other_model, horizon)
        r = dm_test(e_seed, e_other, h=horizon, loss=loss)
        r["seed_file"] = os.path.basename(f)
        rows.append(r)
    return pd.DataFrame(rows)


def dm_pairwise(df, model_a, model_b, horizons, loss="absolute"):
    """Run the DM test at each horizon for two models that carry no seed.

    dm_over_seeds exists only because the recurrent network's forecast
    depends on a random initialisation; ARIMA, ridge, the random forest and
    gradient boosting do not, so one run against one competitor is the
    whole comparison, read from the same single forecast table as every
    other number in Table~\\ref{tab:accuracy} rather than from a seed file.
    Returns one row per horizon.
    """
    rows = []
    for h in horizons:
        e_a, e_b = paired_errors(df, model_a, model_b, h)
        r = dm_test(e_a, e_b, h=h, loss=loss)
        r["horizon"] = h
        rows.append(r)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def test_significance(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    rng = np.random.default_rng(0)
    n = 500

    # Identical forecasts must score a DM statistic of exactly zero.
    e = rng.normal(0, 10, n)
    r = dm_test(e, e.copy(), h=1)
    check(abs(r["dm"]) < 1e-10, "identical errors must give DM = 0")
    check(r["pvalue"] > 0.99, "identical errors must give p close to 1")

    # A model with inflated errors must be detected with high power at h=1.
    e_good = rng.normal(0, 5, n)
    e_bad = e_good + rng.normal(0, 40, n)
    r = dm_test(e_bad, e_good, h=1)
    check(r["dm"] > 0, "the worse model named first should give a positive statistic")
    check(r["pvalue"] < 0.01, "a large, obvious accuracy gap should be detected")

    # The test is symmetric in which model is named first.
    r2 = dm_test(e_good, e_bad, h=1)
    check(np.isclose(r["dm"], -r2["dm"]), "swapping models must flip the sign of DM")
    check(np.isclose(r["pvalue"], r2["pvalue"]), "swapping models must not change the p-value")

    # At h=1 the HLN-corrected statistic is an exact algebraic identity with
    # the textbook paired t-test: the two variance estimators differ only by
    # the population-to-sample (n to n-1) factor that the HLN correction
    # happens to supply exactly when h=1. This checks the implementation
    # against scipy's independent computation, not against another line of
    # the same formula.
    t_ref, p_ref = stats.ttest_rel(np.abs(e_bad), np.abs(e_good))
    check(np.isclose(r["dm_hln"], t_ref),
          "HLN-corrected DM at h=1 must equal the standard paired t-statistic")
    check(np.isclose(r["pvalue"], p_ref),
          "its p-value must equal the standard paired t-test's p-value")

    # A genuinely autocorrelated loss differential must be treated
    # differently at h=3 than at h=1: the extra lag terms are not a no-op.
    phi = 0.7
    d_auto = np.zeros(n)
    innov = rng.normal(0, 1, n)
    for t in range(1, n):
        d_auto[t] = phi * d_auto[t - 1] + innov[t]
    e1_auto = 50.0 + d_auto   # kept positive so |e1| - |e2| = d_auto exactly
    e2_auto = np.full(n, 50.0)
    dm_h1 = dm_test(e1_auto, e2_auto, h=1)["dm"]
    dm_h3 = dm_test(e1_auto, e2_auto, h=3)["dm"]
    check(not np.isclose(dm_h1, dm_h3, rtol=1e-3),
          "the h=3 autocovariance correction must change the statistic when "
          "the loss differential is genuinely autocorrelated")

    # Too few origins for the requested horizon must be refused.
    try:
        dm_test(np.array([1.0, 2.0]), np.array([1.0, 1.0]), h=5)
        check(False, "too few origins for the horizon should raise")
    except ValueError:
        pass

    # paired_errors must refuse mismatched origins rather than truncate.
    a = pd.DataFrame({"origin": pd.to_datetime(["2024-01-01", "2024-01-02"]),
                      "horizon": [1, 1], "model": ["a", "a"],
                      "y_pred": [1.0, 2.0], "y_true": [1.0, 2.0]})
    b = pd.DataFrame({"origin": pd.to_datetime(["2024-01-01"]),
                      "horizon": [1], "model": ["b"],
                      "y_pred": [1.0], "y_true": [1.0]})
    try:
        paired_errors(pd.concat([a, b], ignore_index=True), "a", "b", 1)
        check(False, "mismatched origins between models should raise")
    except ValueError:
        pass

    # dm_pairwise must agree exactly with calling paired_errors and dm_test
    # by hand: it is a loop over horizons, nothing more, and should not
    # silently compute anything differently. paired_errors reads y_true
    # from model_a's rows only, since in real use it is the same observed
    # outcome for every model being compared; y_true is held at zero here
    # (shared by construction) and y_pred set to minus the desired error,
    # so y_true - y_pred reproduces e_bad/e_good/e1_auto/e2_auto exactly.
    origins = pd.date_range("2024-01-01", periods=n, freq="D")
    zeros = np.zeros(n)
    toy = pd.concat([
        pd.DataFrame({"origin": origins, "horizon": 1, "model": "x",
                      "y_pred": -e_bad, "y_true": zeros}),
        pd.DataFrame({"origin": origins, "horizon": 1, "model": "y",
                      "y_pred": -e_good, "y_true": zeros}),
        pd.DataFrame({"origin": origins, "horizon": 3, "model": "x",
                      "y_pred": -e1_auto, "y_true": zeros}),
        pd.DataFrame({"origin": origins, "horizon": 3, "model": "y",
                      "y_pred": -e2_auto, "y_true": zeros}),
    ], ignore_index=True)
    pw = dm_pairwise(toy, "x", "y", horizons=(1, 3)).set_index("horizon")
    check(np.isclose(pw.loc[1, "dm_hln"], r["dm_hln"]),
          "dm_pairwise at h=1 must match a direct dm_test call")
    check(np.isclose(pw.loc[3, "dm_hln"], dm_test(e1_auto, e2_auto, h=3)["dm_hln"]),
          "dm_pairwise at h=3 must match a direct dm_test call")

    if verbose:
        print("  Significance checks:", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if test_significance() else 1)
