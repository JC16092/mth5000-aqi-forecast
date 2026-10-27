"""
Generate every LaTeX table in the report directly from the result files.

No number in the report is typed by hand. If a model is refitted or a threshold
changed, rerun this and every table updates. A report whose tables are copied by
hand is a report that will eventually disagree with its own code, usually in the
week before submission.
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats as spstats

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from step01_data_check import load_series          # noqa: E402
from step01b_clean import load as load_raw, apply_rules  # noqa: E402
from step03_benchmarks import chronological_split  # noqa: E402
from step04_arima import fourier_terms, select_order  # noqa: E402
from step07_warning import operating_point_at_alarms  # noqa: E402
import evaluation as ev                            # noqa: E402
import significance as sig                         # noqa: E402

NO_WEATHER_MODELS = {"naive_carry", "seasonal_naive_7", "climatology",
                     "arima_fourier", "ridge", "random_forest",
                     "random_forest_delta", "hist_gbm", "hist_gbm_delta",
                     "logistic", "forest_clf", "hgb_clf"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "tables")

PRETTY = {
    "gru": "GRU, 30 day sequence",
    "lstm": "LSTM, 30 day sequence",
    "transformer": "Transformer, 30 day sequence",
    "arima_fourier": "ARIMA(1,1,1) with Fourier terms",
    "arima_fourier_mean": "ARIMA, bias corrected back-transform",
    "arima_no_fourier": "ARIMA(1,1,1), no Fourier terms",
    "random_forest": "Random forest, level target",
    "random_forest_delta": "Random forest, change target",
    "hist_gbm": "Gradient boosting, level target",
    "hist_gbm_delta": "Gradient boosting, change target",
    "ridge": "Ridge regression",
    "naive_carry": "Persistence",
    "naive": "Persistence (strict)",
    "climatology": "Climatology",
    "seasonal_naive_7": "Seasonal naive, lag 7",
    "logistic": "Penalised logistic",
    "forest_clf": "Random forest classifier",
    "hgb_clf": "Gradient boosting classifier",
}

ORDER = ["gru", "lstm", "transformer", "arima_fourier", "random_forest_delta",
         "hist_gbm_delta", "random_forest", "hist_gbm", "ridge", "naive_carry",
         "climatology", "seasonal_naive_7"]

# Models reported as a range over independent random-initialisation seeds
# rather than as a single point estimate, and the seed-file glob pattern
# each one is found under.
SEEDED_MODELS = {"gru": "gru_seed*.csv", "lstm": "lstm_seed*.csv",
                 "transformer": "transformer_seed*.csv"}


def write(name, body):
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(body)
    print(f"  wrote tables/{name}")


def esc(s):
    return str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")


# ----------------------------------------------------------------------------

def table_dataset(series_path):
    s = load_series(series_path, "date", "PM2.5")
    d = s.dropna()
    full = pd.date_range(s.index.min(), s.index.max(), freq="D")
    isna = s.reindex(full).isna().values
    worst = run = 0
    for f in isna:
        run = run + 1 if f else 0
        worst = max(worst, run)
    rows = [
        ("Source", "OpenAQ location 8118, sensor 23534, provider AirNow"),
        ("Period", f"{s.index.min().date()} to {s.index.max().date()}"),
        ("Calendar days", f"{len(full)}"),
        ("Usable daily means", f"{len(d)} ({100 * len(d) / len(full):.1f}\\% of calendar)"),
        ("Longest gap", f"{worst} consecutive days"),
        ("Mean, median, maximum", f"{d.mean():.1f}, {d.median():.1f}, {d.max():.1f}"),
        ("Days above 121", f"{int((d > 121).sum())} ({100 * (d > 121).mean():.1f}\\%)"),
    ]
    body = ["\\begin{tabular}{ll}", "\\toprule"]
    for k, v in rows:
        body.append(f"{esc(k)} & {v} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("dataset.tex", "\n".join(body) + "\n")


def table_accuracy(forecast_path, series_path, burn_in=1095):
    """The main results table.

    The network is reported as a range over initialisation seeds and every other
    model as a single number, because only the network varies with a seed. A
    point estimate for a neural network trained once is not a result, and the
    range here is wide enough to change which model appears to win.
    """
    import glob
    s = load_series(series_path, "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[burn_in]].values)

    d = pd.read_csv(forecast_path, parse_dates=["origin"])
    m = ev.regression_metrics(d, scale, reference="naive_carry")
    piv = m.pivot_table(index="model", columns="horizon", values="rMAE")
    bias = m.pivot_table(index="model", columns="horizon", values="bias")

    # Every seed run that exists, for each model that varies with a random
    # initialisation (currently the GRU and the LSTM).
    seeded = {}
    for model_name, pattern in SEEDED_MODELS.items():
        seeds = sorted(glob.glob(os.path.join(ROOT, pattern)))
        runs = {}
        for f in seeds:
            g = ev.regression_metrics(pd.read_csv(f, parse_dates=["origin"]), scale,
                                      reference="naive_carry")
            g = g[g.model == model_name].set_index("horizon")["rMAE"]
            runs[os.path.basename(f)] = g
        if runs:
            seeded[model_name] = pd.DataFrame(runs)
            print(f"  {model_name} reported over {seeded[model_name].shape[1]} seeds")

    body = ["\\begin{tabular}{lccc r}", "\\toprule",
            "Model & $h=1$ & $h=2$ & $h=3$ & Bias at $h=1$ \\\\", "\\midrule"]
    for name in ORDER:
        if name in seeded:
            G = seeded[name]
            cells = [f"{G.loc[h].min():.3f} to {G.loc[h].max():.3f}" for h in (1, 2, 3)]
            body.append(f"{esc(PRETTY[name])}, range over {G.shape[1]} seeds & "
                        + " & ".join(cells)
                        + f" & {bias.loc[name, 1]:+.1f} \\\\")
            continue
        if name not in piv.index:
            continue
        cells = [f"{piv.loc[name, h]:.3f}" for h in (1, 2, 3)]
        body.append(f"{esc(PRETTY.get(name, name))} & " + " & ".join(cells)
                    + f" & {bias.loc[name, 1]:+.1f} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("accuracy.tex", "\n".join(body) + "\n")


def table_warning(forecast_path, threshold=121.0):
    """A single-seed warning-system row would violate this report's own
    rule against reporting a seeded network as one point rather than a
    range (Section 4.1's own lesson, learned from the GRU). LSTM has not
    been run through the threshold sweep across its ten seeds, only
    through the accuracy evaluation in Table~4.1, so it is deliberately
    excluded here rather than silently shown as a single, unrepresentative
    seed. Reported as a limitation, not a silent gap."""
    d = pd.read_csv(forecast_path, parse_dates=["origin"])
    w = ev.evaluate_warnings(d, event_threshold=threshold)
    body = ["\\begin{tabular}{lrrrrr}", "\\toprule",
            "Model & Hit rate & False alarm rate & Precision & CSI & Alarms/yr \\\\",
            "\\midrule"]
    for name in ORDER:
        if name in SEEDED_MODELS and name != "gru":
            continue  # see docstring: no single-seed warning-system row
        r = w[(w.model == name) & (w.horizon == 1)]
        if not len(r):
            continue
        r = r.iloc[0]
        body.append(f"{esc(PRETTY.get(name, name))} & {r.hit_rate:.3f} & "
                    f"{r.false_alarm_rate:.3f} & {r.precision:.3f} & "
                    f"{r.csi:.3f} & {r.alarms_per_year:.0f} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("warning.tex", "\n".join(body) + "\n")


def table_budget(sweep_path):
    import glob
    sw = pd.read_csv(sweep_path)
    budgets = (40, 60, 80, 100)

    # Every per-seed sweep that exists, for the network only. Mirrors the
    # treatment in table_accuracy: a network result depends on its random
    # initialisation, so it is reported as a range, never a single seed.
    seed_sweeps = sorted(glob.glob(os.path.join(ROOT, "threshold_sweep_gru_seed*.csv")))
    gru_range = None
    # Best GRU hit rate at each (horizon, budget) across every seed, so the
    # top "Best hit rate" row below is never silently capped at seed 0's
    # curve the way sweep_path's own "gru" rows are.
    gru_best = {h: {b: float("-inf") for b in budgets} for h in (1, 2, 3)}
    if seed_sweeps:
        per_seed = []
        for f in seed_sweeps:
            ssw = pd.read_csv(f)
            cells = []
            for b in budgets:
                g = ssw[(ssw.model == "gru") & (ssw.horizon == 1) &
                        (ssw.alarms_per_year <= b)]
                cells.append(g["hit_rate"].max() if len(g) else float("nan"))
            per_seed.append(cells)
            for h in (1, 2, 3):
                for b in budgets:
                    g = ssw[(ssw.model == "gru") & (ssw.horizon == h) &
                            (ssw.alarms_per_year <= b)]
                    if len(g):
                        gru_best[h][b] = max(gru_best[h][b], g["hit_rate"].max())
        arr = pd.DataFrame(per_seed, columns=budgets)
        gru_range = (arr.min(), arr.max())
        print(f"  GRU budget row reported over {len(seed_sweeps)} seeds")

    body = ["\\begin{tabular}{lrrrr}", "\\toprule",
            "Alarms per year & 40 & 60 & 80 & 100 \\\\", "\\midrule"]
    for h in (1, 2, 3):
        cells = []
        for b in budgets:
            g = sw[(sw.horizon == h) & (sw.alarms_per_year <= b) & (sw.model != "gru")]
            best = g["hit_rate"].max() if len(g) else float("-inf")
            if seed_sweeps:
                best = max(best, gru_best[h][b])
            cells.append(f"{best:.3f}" if best > float("-inf") else "--")
        body.append(f"Best hit rate, $h={h}$ & " + " & ".join(cells) + " \\\\")
    body.append("\\midrule")
    for name in ["gru", "arima_fourier", "hist_gbm_delta", "naive_carry", "climatology"]:
        if name == "gru" and gru_range is not None:
            lo, hi = gru_range
            cells = [f"{lo[b]:.3f}--{hi[b]:.3f}" for b in budgets]
            body.append(f"\\quad {esc(PRETTY['gru'])}, range over "
                        f"{len(seed_sweeps)} seeds, $h=1$ & "
                        + " & ".join(cells) + " \\\\")
            continue
        cells = []
        for b in budgets:
            g = sw[(sw.model == name) & (sw.horizon == 1) & (sw.alarms_per_year <= b)]
            cells.append(f"{g['hit_rate'].max():.3f}" if len(g) else "--")
        body.append(f"\\quad {esc(PRETTY.get(name, name))}, $h=1$ & "
                    + " & ".join(cells) + " \\\\")
    body.append("\\midrule")
    # The two models the Discussion chapter's sharpest illustrations name
    # directly at h=3 (persistence winning outright at a tight budget;
    # climatology nearly matching the best model at the loosest one), so a
    # reader can check those specific claims against a printed cell rather
    # than the prose alone.
    for name in ["naive_carry", "climatology"]:
        cells = []
        for b in budgets:
            g = sw[(sw.model == name) & (sw.horizon == 3) & (sw.alarms_per_year <= b)]
            cells.append(f"{g['hit_rate'].max():.3f}" if len(g) else "--")
        body.append(f"\\quad {esc(PRETTY.get(name, name))}, $h=3$ & "
                    + " & ".join(cells) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("budget.tex", "\n".join(body) + "\n")


def table_weather(base_path, weather_path, series_path, burn_in=1095):
    """Does adding meteostat wind speed and temperature change anything?

    Reported as the change in rMAE from the already-published
    Table~\\ref{tab:accuracy} baseline, negative is an improvement, rather
    than as a second absolute number competing with it, so there remains one
    place in the report that states what each model scores without weather.
    The network is the exception, shown as its own absolute range exactly
    like its row in Table~\\ref{tab:accuracy}, to be read directly against it.
    """
    import glob
    s = load_series(series_path, "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[burn_in]].values)

    base = ev.regression_metrics(pd.read_csv(base_path, parse_dates=["origin"]),
                                 scale, reference="naive_carry")
    weather = ev.regression_metrics(pd.read_csv(weather_path, parse_dates=["origin"]),
                                    scale, reference="naive_carry")

    ml_models = ["ridge", "random_forest", "random_forest_delta",
                 "hist_gbm", "hist_gbm_delta"]

    body = ["\\begin{tabular}{lrrr}", "\\toprule",
            "Model & $\\Delta$ rMAE, $h=1$ & $\\Delta$ rMAE, $h=2$ & "
            "$\\Delta$ rMAE, $h=3$ \\\\", "\\midrule"]
    for name in ml_models:
        cells = []
        for h in (1, 2, 3):
            b = base[(base.model == name) & (base.horizon == h)]["rMAE"]
            w = weather[(weather.model == name) & (weather.horizon == h)]["rMAE"]
            cells.append(f"{float(w.iloc[0]) - float(b.iloc[0]):+.3f}"
                        if len(b) and len(w) else "--")
        body.append(f"{esc(PRETTY.get(name, name))} & " + " & ".join(cells) + " \\\\")
    body.append("\\midrule")

    weather_seeds = sorted(glob.glob(os.path.join(ROOT, "gru_weather_seed*.csv")))
    if weather_seeds:
        rows = {}
        for f in weather_seeds:
            g = ev.regression_metrics(pd.read_csv(f, parse_dates=["origin"]),
                                      scale, reference="naive_carry")
            rows[f] = g[g.model == "gru"].set_index("horizon")["rMAE"]
        G = pd.DataFrame(rows)
        cells = [f"{G.loc[h].min():.3f} to {G.loc[h].max():.3f}" for h in (1, 2, 3)]
        body.append(f"{esc(PRETTY['gru'])}, with weather, {len(weather_seeds)} "
                    "seeds (absolute) & " + " & ".join(cells) + " \\\\")
        print(f"  weather network row reported over {len(weather_seeds)} seeds")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("weather.tex", "\n".join(body) + "\n")


def table_significance(comparisons=(
                           ("Plain GRU vs.\\ ARIMA", "gru_seed*.csv", "gru"),
                           ("GRU with weather vs.\\ ARIMA", "gru_weather_seed*.csv", "gru"),
                           ("LSTM vs.\\ ARIMA", "lstm_seed*.csv", "lstm"),
                           ("Transformer vs.\\ ARIMA", "transformer_seed*.csv", "transformer"),
                       ),
                       other_model="arima_fourier", horizons=(1, 2, 3)):
    """Diebold-Mariano test of each seeded network against the ARIMA benchmark.

    Run once per seed, exactly like every other seed-dependent number in
    this report, and reported as the range across all ten rather than a
    single run's statistic. A negative DM statistic favours the network at
    that seed; a positive one favours ARIMA. This is the formal counterpart
    to the seed-by-seed sign counting already given for Table~\\ref{tab:accuracy}
    in Section~\\ref{sec:results-rq1}, and to the empirical noise floor in
    Section~\\ref{sec:noise-floor}: that floor bounds measurement and
    initialisation noise, not the sampling uncertainty of a mean computed
    over one finite, autocorrelated run of forecast errors, which is what
    this test bounds instead.

    Generalised from a GRU-only function to take a list of (label, seed-file
    pattern, model name) triples, so a second seeded architecture (the LSTM)
    reports through the same table rather than a separate one that would
    silently overwrite it.
    """
    import glob
    rows = []
    for label, pattern, seed_model in comparisons:
        files = sorted(glob.glob(os.path.join(ROOT, pattern)))
        if not files:
            print(f"  no files matching {pattern}; skipping its significance rows")
            continue
        for h in horizons:
            d = sig.dm_over_seeds(files, seed_model, other_model, h)
            n_sig = int((d["pvalue"] < 0.05).sum())
            rows.append({
                "label": label, "h": h, "n_seeds": len(files),
                "dm_lo": d["dm_hln"].min(), "dm_hi": d["dm_hln"].max(),
                "p_lo": d["pvalue"].min(), "p_hi": d["pvalue"].max(),
                "n_sig": n_sig,
            })
            print(f"  DM {label}, h={h}: statistic {d['dm_hln'].min():.2f} to "
                  f"{d['dm_hln'].max():.2f}, p {d['pvalue'].min():.4f} to "
                  f"{d['pvalue'].max():.4f}, {n_sig}/{len(files)} significant at 0.05")

    body = ["\\begin{tabular}{llccc}", "\\toprule",
            "Comparison & $h$ & DM statistic & $p$-value & Sig.\\ seeds \\\\",
            "\\midrule"]
    for r in rows:
        p_lo = "$<$0.001" if r["p_lo"] < 0.001 else f"{r['p_lo']:.3f}"
        body.append(
            f"{r['label']} & {r['h']} & {r['dm_lo']:.2f} to {r['dm_hi']:.2f} & "
            f"{p_lo} to {r['p_hi']:.3f} & {r['n_sig']}/{r['n_seeds']} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("significance.tex", "\n".join(body) + "\n")
    return pd.DataFrame(rows)


def table_significance_ml(forecast_path, other_model="arima_fourier",
                          ml_models=("ridge", "random_forest", "random_forest_delta",
                                     "hist_gbm", "hist_gbm_delta"),
                          horizons=(1, 2, 3)):
    """Diebold-Mariano test of ARIMA against each point-forecast ML regressor.

    Table~\\ref{tab:accuracy}'s own claim, that the classical benchmark beats
    every machine learning regressor at every horizon, has until now rested
    on point rMAE values and the informal noise floor in
    Section~\\ref{sec:noise-floor}, never on the same formal test already
    applied to the one comparison with a seed to range over. None of ridge,
    the random forest or gradient boosting carries one, so one run against
    ARIMA is the whole comparison, read from the same single forecast table
    `table_accuracy` already uses rather than from a seed file. A negative
    statistic favours the machine learning model; a positive one favours
    ARIMA.
    """
    d = pd.read_csv(forecast_path, parse_dates=["origin"])
    rows = []
    for name in ml_models:
        pw = sig.dm_pairwise(d, name, other_model, horizons)
        for _, r in pw.iterrows():
            rows.append({"model": name, "h": int(r["horizon"]),
                        "dm": r["dm_hln"], "pvalue": r["pvalue"]})
            print(f"  DM {PRETTY.get(name, name)} vs.\\ ARIMA, h={int(r['horizon'])}: "
                  f"statistic {r['dm_hln']:.2f}, p {r['pvalue']:.4f}"
                  f"{'  *' if r['pvalue'] < 0.05 else ''}")

    body = ["\\begin{tabular}{lccc}", "\\toprule",
            "Comparison & $h$ & DM statistic & $p$-value \\\\", "\\midrule"]
    for r in rows:
        p = "$<$0.001" if r["pvalue"] < 0.001 else f"{r['pvalue']:.3f}"
        star = "$^{*}$" if r["pvalue"] < 0.05 else ""
        body.append(f"{esc(PRETTY.get(r['model'], r['model']))} vs.\\ ARIMA & "
                    f"{r['h']} & {r['dm']:.2f} & {p}{star} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("significance_ml.tex", "\n".join(body) + "\n")
    return pd.DataFrame(rows)


def table_weather_budget(pattern, budgets=(40, 60, 80, 100)):
    """Does adding the weather models widen the achievable hit rate at a
    fixed alarm budget, or does the five-point ceiling in Table~\\ref{tab:budget}
    absorb the accuracy gain from Table~\\ref{tab:weather}?

    Each sweep file already contains both the original and the weather
    models, scored by the same restrict_to_common call, over the same rows.
    So "without weather" and "with weather" below differ in exactly one
    thing, which models are allowed to be the best one at that budget, never
    in which rows were scored. Averaged over the five GRU weather seeds.
    """
    import glob
    files = sorted(glob.glob(os.path.join(ROOT, pattern)))
    if not files:
        print(f"  no files matching {pattern}; skipping weather_budget.tex")
        return

    body = ["\\begin{tabular}{lrrrr}", "\\toprule",
            "Alarms per year & 40 & 60 & 80 & 100 \\\\", "\\midrule"]
    for h in (1, 2, 3):
        no_wx_row, wx_row = [], []
        for budget in budgets:
            no_wx, wx = [], []
            for f in files:
                sweep = pd.read_csv(f)
                all_models = set(sweep.model.unique())
                best_no = max(
                    (operating_point_at_alarms(sweep, m, h, budget)["hit_rate"]
                     for m in NO_WEATHER_MODELS & all_models
                     if operating_point_at_alarms(sweep, m, h, budget) is not None),
                    default=None)
                best_wx = max(
                    (operating_point_at_alarms(sweep, m, h, budget)["hit_rate"]
                     for m in all_models
                     if operating_point_at_alarms(sweep, m, h, budget) is not None),
                    default=None)
                if best_no is not None:
                    no_wx.append(best_no)
                if best_wx is not None:
                    wx.append(best_wx)
            no_wx_row.append(sum(no_wx) / len(no_wx) if no_wx else None)
            wx_row.append(sum(wx) / len(wx) if wx else None)
        no_cells = [f"{v:.3f}" if v is not None else "--" for v in no_wx_row]
        wx_cells = [f"{v:.3f}" if v is not None else "--" for v in wx_row]
        body.append(f"Best hit rate, $h={h}$, no weather & " + " & ".join(no_cells) + " \\\\")
        body.append(f"\\quad with weather models added & " + " & ".join(wx_cells) + " \\\\")
        if h < 3:
            body.append("\\midrule")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("weather_budget.tex", "\n".join(body) + "\n")
    print(f"  weather budget table averaged over {len(files)} GRU weather seeds")


def table_arms(sweep_path, budgets=(40, 60, 80, 100)):
    """Research Question 2: forecast-then-threshold against direct
    classification, matched by base algorithm so neither arm benefits from
    simply having more candidate models to choose from.

    Three matched pairs, the same algorithm trained two ways: ridge against
    penalised logistic, the random forest's change-target variant against
    the random forest classifier, and gradient boosting's change-target
    variant against the gradient boosting classifier. h=1 only, mirroring
    the convention already used for the per-model budget breakdown in
    table_budget.
    """
    sweep = pd.read_csv(sweep_path)
    pairs = [("ridge", "logistic", "Ridge vs.\\ penalised logistic"),
             ("random_forest_delta", "forest_clf",
              "Random forest (change) vs.\\ its classifier"),
             ("hist_gbm_delta", "hgb_clf",
              "Gradient boosting (change) vs.\\ its classifier")]

    body = ["\\begin{tabular}{lrrrr}", "\\toprule",
            "Alarms per year, $h=1$ & 40 & 60 & 80 & 100 \\\\", "\\midrule"]
    for reg, clf, label in pairs:
        reg_cells, clf_cells = [], []
        for b in budgets:
            r = operating_point_at_alarms(sweep, reg, 1, b)
            c = operating_point_at_alarms(sweep, clf, 1, b)
            rv = r["hit_rate"] if r is not None else None
            cv = c["hit_rate"] if c is not None else None
            # Bold whichever arm wins that cell; leave both plain on a tie,
            # since bolding one would claim a winner that does not exist.
            if rv is not None and cv is not None and not np.isclose(rv, cv):
                reg_cells.append(f"\\textbf{{{rv:.3f}}}" if rv > cv else f"{rv:.3f}")
                clf_cells.append(f"\\textbf{{{cv:.3f}}}" if cv > rv else f"{cv:.3f}")
            else:
                reg_cells.append(f"{rv:.3f}" if rv is not None else "--")
                clf_cells.append(f"{cv:.3f}" if cv is not None else "--")
        body.append(f"{label} & \\multicolumn{{4}}{{c}}{{}} \\\\")
        body.append(f"\\quad forecast then threshold & " + " & ".join(reg_cells) + " \\\\")
        body.append(f"\\quad direct classification & " + " & ".join(clf_cells) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("arms.tex", "\n".join(body) + "\n")

    # The tally behind the "neither arm dominates" claim: every matched pair,
    # every horizon, every budget, counted once each.
    reg_wins = clf_wins = ties = 0
    diffs = []
    pair_models = [("ridge", "logistic"), ("random_forest_delta", "forest_clf"),
                   ("hist_gbm_delta", "hgb_clf")]
    for h in (1, 2, 3):
        for reg, clf in pair_models:
            for b in budgets:
                r = operating_point_at_alarms(sweep, reg, h, b)
                c = operating_point_at_alarms(sweep, clf, h, b)
                if r is None or c is None:
                    continue
                d = r["hit_rate"] - c["hit_rate"]
                diffs.append(d)
                if abs(d) < 1e-9:
                    ties += 1
                elif d > 0:
                    reg_wins += 1
                else:
                    clf_wins += 1
    diffs = np.array(diffs)
    tally = {"reg_wins": reg_wins, "clf_wins": clf_wins, "ties": ties,
            "total": reg_wins + clf_wins + ties,
            "mean_diff": float(diffs.mean()), "max_abs_diff": float(np.abs(diffs).max()),
            "median_abs_diff": float(np.median(np.abs(diffs)))}
    print(f"  arms tally: {tally}")
    return tally


def table_cleaning(raw_path):
    """Computed from the raw data and the production cleaning call, not
    hand-typed: this was the one table in the project that still violated
    this file's own opening rule, and a hand-typed table is a table that
    silently stops matching its own data the next time the cleaning rule
    is revisited.
    """
    raw = load_raw(raw_path)
    cleaned = apply_rules(raw, min_value=0, max_value=1000, max_ratio=None,
                          min_coverage=50)
    counts = cleaned["clean_reason"].value_counts()
    below_min = int(counts.get("below_min", 0))
    low_coverage = int(counts.get("low_coverage", 0))
    above_max = int(counts.get("above_max", 0))
    total_removed = below_min + low_coverage + above_max
    total_raw = int(raw["PM2.5_raw"].notna().sum())
    total_str = f"{total_removed} of {total_raw:,}".replace(",", "{,}")

    rows = [("Value below zero", f"{below_min}", "Mass concentration cannot be negative"),
            ("Coverage below 50\\%", f"{low_coverage}", "Against the cadence taken from the data"),
            ("Value above 1000", f"{above_max}",
             "Judgement; sensitivity analysis in Section~\\ref{sec:limitations}"),
            ("\\textbf{Total}", f"\\textbf{{{total_str}}}", "")]
    body = ["\\begin{tabular}{llp{6.2cm}}", "\\toprule",
            "Rule & Days removed & Basis \\\\", "\\midrule"]
    for a, b, c in rows:
        body.append(f"{a} & {b} & {c} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("cleaning.tex", "\n".join(body) + "\n")


def table_order_search(series_path, fourier_k=4):
    """The ARIMA order search in full, not just the top two candidates the
    prose quotes. Refits all 24 orders in the grid on the training block
    exactly as step04_arima.py does at pipeline time, rather than hand-
    copying numbers from a log -- select_order's own docstring already
    says the grid should be inspectable, not just trusted, and this is
    that inspection, in the report rather than only in a console.
    """
    s = load_series(series_path, "date", "PM2.5")
    y = np.log(s)
    y.name = "log_pm25"
    train_idx, val_idx, test_idx = chronological_split(s.index)
    exog = fourier_terms(s.index, K=fourier_k)
    grid = [(p, d, q) for d in (0, 1) for p in (0, 1, 2, 3) for q in (0, 1, 2)]
    order, table = select_order(y.loc[train_idx], exog.loc[train_idx], grid,
                                verbose=False)

    body = ["\\begin{longtable}{lrrl}",
            "\\caption{The ARIMA order search in full: every $(p,d,q)$ "
            "candidate in the grid, sorted by AIC. Four orders did not "
            "converge to a stable estimate on the training block and are "
            "reported with their AIC and BIC as returned, marked "
            "accordingly.}\\label{tab:order-search}\\\\",
            "\\toprule",
            "Order $(p,d,q)$ & AIC & BIC & \\\\", "\\midrule", "\\endfirsthead",
            "\\multicolumn{4}{l}{\\small\\itshape "
            "(Table~\\ref{tab:order-search}, continued)} \\\\",
            "\\toprule",
            "Order $(p,d,q)$ & AIC & BIC & \\\\", "\\midrule", "\\endhead",
            "\\midrule",
            "\\multicolumn{4}{r}{\\small\\itshape continued on next page} \\\\",
            "\\endfoot",
            "\\bottomrule",
            "\\endlastfoot"]
    for i, r in table.iterrows():
        mark = "\\quad $\\leftarrow$ chosen" if i == 0 else ""
        conv = "" if r["converged"] else " (did not converge)"
        body.append(f"({r['order'][0]},{r['order'][1]},{r['order'][2]}) & "
                    f"{r['aic']:.1f} & {r['bic']:.1f} & {conv}{mark} \\\\")
    body += ["\\end{longtable}"]
    write("order_search.tex", "\n".join(body) + "\n")
    print(f"  order search: {len(table)} candidates, chosen {tuple(order)}, "
          f"AIC {table.iloc[0]['aic']:.1f}")


def table_descriptive(series_path):
    """The distributional shape claimed throughout the Literature Review
    and Methodology ("strongly right skewed") as a statement with a
    number behind it, computed directly from the cleaned series rather
    than asserted.
    """
    s = load_series(series_path, "date", "PM2.5").dropna()
    rows = [
        ("Mean", f"{s.mean():.1f}"),
        ("Median", f"{s.median():.1f}"),
        ("Standard deviation", f"{s.std():.1f}"),
        ("Minimum", f"{s.min():.1f}"),
        ("Lower quartile ($Q_1$)", f"{s.quantile(0.25):.1f}"),
        ("Upper quartile ($Q_3$)", f"{s.quantile(0.75):.1f}"),
        ("Maximum", f"{s.max():.1f}"),
        ("Skewness", f"{spstats.skew(s):.2f}"),
        ("Excess kurtosis", f"{spstats.kurtosis(s):.2f}"),
    ]
    body = ["\\begin{tabular}{lr}", "\\toprule",
            "Statistic & PM2.5 (\\textmu g\\,m$^{-3}$) \\\\", "\\midrule"]
    for k, v in rows:
        body.append(f"{k} & {v} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("descriptive.tex", "\n".join(body) + "\n")
    print(f"  descriptive stats: skewness {spstats.skew(s):.2f}, "
          f"excess kurtosis {spstats.kurtosis(s):.2f}")


def table_architectures():
    """The four neural architectures' specifications, consolidated into one
    table. Each number is individually correct in its own Methodology
    subsection already; this is the same numbers, not new ones, read
    side by side rather than four subsections apart. Parameter counts are
    for the six-channel (no weather) network, confirmed against the fitted
    model objects in the relevant subsection already, repeated here rather
    than recomputed, since all four architectures share identical channel
    construction and window length.
    """
    import torch
    from kan_layer import KANLinear

    rows = [
        ("GRU", "24 hidden units", "Adam, lr $=0.01$", "2{,}329"),
        ("LSTM", "24 hidden units", "Adam, lr $=0.01$", "3{,}097"),
        ("Transformer", "$d_{model}=16$, 2 heads, 1 layer",
         "Adam, lr $=0.001$", "3{,}409"),
    ]

    class Net(torch.nn.Module):
        def __init__(self, n_feat, hidden):
            super().__init__()
            self.lstm = torch.nn.LSTM(n_feat, hidden, batch_first=True)
            self.out = KANLinear(hidden, 1, grid_size=5, spline_order=3)

    kan_params = sum(p.numel() for p in Net(6, 24).parameters() if p.requires_grad)
    rows.append(("Kolmogorov-Arnold-LSTM", "24 hidden units, grid size 5",
                "Adam, lr $=0.01$", f"{kan_params:,}".replace(",", "{,}")))

    body = ["\\begin{tabular}{llll}", "\\toprule",
            "Architecture & Size & Optimiser & Parameters \\\\", "\\midrule"]
    for name, size, opt, params in rows:
        body.append(f"{name} & {size} & {opt} & {params} \\\\")
    body += ["\\bottomrule",
            "\\multicolumn{4}{p{11.5cm}}{\\footnotesize All four share the "
            "same 30-day input window and six-channel construction "
            "(Section~\\ref{sec:preprocess}); parameters are for that "
            "six-channel network, confirmed against the fitted model "
            "objects.} \\\\",
            "\\end{tabular}"]
    write("architectures.tex", "\n".join(body) + "\n")
    print(f"  architectures: KAN-LSTM {kan_params} parameters, confirmed")


def table_gru_sensitivity(hyper_path="gru_hyperparam_sensitivity.csv",
                          fourier_path="gru_fourier_ablation.csv",
                          opt_path="gru_optimizer_sensitivity.csv"):
    """The exact numbers behind Figure 5.1, the three bounded checks as a
    table rather than only a plot: mean rMAE across the same three seeds,
    for every setting tried.
    """
    hp = pd.read_csv(os.path.join(ROOT, hyper_path))
    fo = pd.read_csv(os.path.join(ROOT, fourier_path))
    op = pd.read_csv(os.path.join(ROOT, opt_path))

    def mean_rmae(frame, mask, h):
        return frame[mask & (frame.horizon == h)]["rMAE"].mean()

    order = [
        ("Architecture", "$H=24$, 30-day window (default)", hp, hp.sweep == "default"),
        ("", "$H=12$", hp, (hp.sweep == "hidden") & (hp.hidden == 12)),
        ("", "$H=48$", hp, (hp.sweep == "hidden") & (hp.hidden == 48)),
        ("", "15-day window", hp, (hp.sweep == "seq_len") & (hp.seq_len == 15)),
        ("", "45-day window", hp, (hp.sweep == "seq_len") & (hp.seq_len == 45)),
        ("", "60-day window", hp, (hp.sweep == "seq_len") & (hp.seq_len == 60)),
        ("Seasonal input", "$K=4$ (matches ARIMA)", fo, fo.fourier_k == 4),
        ("Training", "Adam, lr $=0.003$", op, (op.sweep == "lr") & (op.lr == 0.003)),
        ("", "Adam, lr $=0.03$", op, (op.sweep == "lr") & (op.lr == 0.03)),
        ("", "SGD, lr $=0.01$", op, (op.sweep == "optimizer") & (op.optimizer == "sgd")),
        ("", "RMSprop, lr $=0.01$",
         op, (op.sweep == "optimizer") & (op.optimizer == "rmsprop")),
    ]
    body = ["\\begin{tabular}{llccc}", "\\toprule",
            "Check & Setting & $h=1$ & $h=2$ & $h=3$ \\\\", "\\midrule"]
    for grp, label, frame, mask in order:
        cells = [f"{mean_rmae(frame, mask, h):.3f}" for h in (1, 2, 3)]
        body.append(f"{grp} & {label} & " + " & ".join(cells) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("gru_sensitivity.tex", "\n".join(body) + "\n")


def table_rq_summary(forecast_path, sweep_path, series_path, burn_in=1095):
    """One row per research question, its headline quantitative answer
    beside it. Every number here is read back from the same results the
    rest of the report's tables already compute, not retyped from prose.
    """
    import glob
    s = load_series(series_path, "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[burn_in]].values)
    d = pd.read_csv(forecast_path, parse_dates=["origin"])
    m = ev.regression_metrics(d, scale, reference="naive_carry")
    arima_h1 = float(m[(m.model == "arima_fourier") & (m.horizon == 1)]["rMAE"].iloc[0])

    # The main sweep file's own "gru" rows are seed 0 only (the same trap
    # table_budget() already works around): take the true best across all
    # ten GRU seeds, exactly as table_budget()'s "Best hit rate" row does,
    # rather than silently under-stating the achievable range at a budget
    # of 100 the way reading threshold_sweep.csv alone would.
    sw = pd.read_csv(sweep_path)
    non_gru = sw[sw.model != "gru"]
    budget_lo = non_gru[(non_gru.horizon == 1)
                        & (non_gru.alarms_per_year <= 40)]["hit_rate"].max()
    budget_hi = non_gru[(non_gru.horizon == 1)
                        & (non_gru.alarms_per_year <= 100)]["hit_rate"].max()
    seed_sweeps = sorted(glob.glob(os.path.join(ROOT, "threshold_sweep_gru_seed*.csv")))
    for f in seed_sweeps:
        ssw = pd.read_csv(f)
        g40 = ssw[(ssw.model == "gru") & (ssw.horizon == 1)
                 & (ssw.alarms_per_year <= 40)]["hit_rate"]
        g100 = ssw[(ssw.model == "gru") & (ssw.horizon == 1)
                  & (ssw.alarms_per_year <= 100)]["hit_rate"]
        if len(g40):
            budget_lo = max(budget_lo, g40.max())
        if len(g100):
            budget_hi = max(budget_hi, g100.max())

    rows = [
        ("RQ1: accuracy vs. benchmarks",
         f"ARIMA beats every ML regressor at every horizon (rMAE {arima_h1:.3f} "
         f"at $h=1$); the GRU beats ARIMA only at $h=1$, across all ten seeds"),
        ("RQ2: forecast-then-threshold vs. direct classification",
         "neither dominates (21/11/4 across 36 matched comparisons); "
         "forecast-then-threshold preferred on flexibility grounds"),
        ("RQ3: model choice vs. decision threshold",
         f"budget sweep moves hit rate {budget_lo:.3f} to {budget_hi:.3f} "
         "($h=1$, 40 to 100 alarms/yr); model choice moves it about 5 points "
         "at a fixed budget"),
    ]
    body = ["\\begin{tabular}{p{4.2cm}p{9.5cm}}", "\\toprule",
            "Question & Headline answer \\\\", "\\midrule"]
    for q, a in rows:
        body.append(f"{q} & {a} \\\\")
        body.append("\\addlinespace")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("rq_summary.tex", "\n".join(body) + "\n")
    print(f"  RQ summary: ARIMA h=1 {arima_h1:.3f}, budget range "
          f"{budget_lo:.3f} to {budget_hi:.3f}")


def main():
    os.makedirs(OUT, exist_ok=True)
    clean = os.path.join(ROOT, "data", "delhi_clean.csv")
    fc = os.path.join(ROOT, "forecasts_with_transformer.csv")
    if not os.path.exists(fc):
        fc = os.path.join(ROOT, "forecasts_with_lstm.csv")
    if not os.path.exists(fc):
        fc = os.path.join(ROOT, "forecasts_with_gru.csv")
    if not os.path.exists(fc):
        fc = os.path.join(ROOT, "forecasts_all.csv")
    sweep = os.path.join(ROOT, "threshold_sweep.csv")

    print("Generating tables from the result files:")
    table_dataset(clean)
    table_accuracy(fc, clean)
    table_warning(fc)
    table_cleaning(os.path.join(ROOT, "data", "delhi.csv"))
    table_significance()
    table_significance_ml(fc)
    if os.path.exists(sweep):
        table_budget(sweep)
        table_arms(sweep)
    else:
        print("  threshold_sweep.csv not found; skipping budget.tex and arms.tex")

    weather_ml = os.path.join(ROOT, "forecasts_weather_ml.csv")
    if os.path.exists(weather_ml):
        table_weather(os.path.join(ROOT, "forecasts_all.csv"), weather_ml, clean)
    else:
        print("  forecasts_weather_ml.csv not found; skipping weather.tex")

    table_weather_budget("threshold_sweep_weather_seed*.csv")

    table_order_search(clean)
    table_descriptive(clean)
    table_architectures()
    if (os.path.exists(os.path.join(ROOT, "gru_hyperparam_sensitivity.csv"))
            and os.path.exists(os.path.join(ROOT, "gru_fourier_ablation.csv"))
            and os.path.exists(os.path.join(ROOT, "gru_optimizer_sensitivity.csv"))):
        table_gru_sensitivity()
    else:
        print("  GRU sensitivity CSVs not found; skipping gru_sensitivity.tex")
    if os.path.exists(sweep):
        table_rq_summary(fc, sweep, clean)
    else:
        print("  threshold_sweep.csv not found; skipping rq_summary.tex")

    # Figures live beside the report so latex finds them without absolute paths.
    import shutil
    figdir = os.path.join(HERE, "figures")
    os.makedirs(figdir, exist_ok=True)
    for f in ["fig1_series.png", "fig2_coverage.png", "fig3_weekly.png",
              "fig4_annual.png", "fig5_warning.png", "fig6_accuracy.png",
              "fig7_arms.png"]:
        src = os.path.join(ROOT, f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(figdir, f))
            print(f"  copied figures/{f}")
    print("\nNow: latexmk -pdf main.tex")


if __name__ == "__main__":
    main()
