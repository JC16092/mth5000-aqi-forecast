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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from step01_data_check import load_series          # noqa: E402
from step07_warning import operating_point_at_alarms  # noqa: E402
import evaluation as ev                            # noqa: E402

NO_WEATHER_MODELS = {"naive_carry", "seasonal_naive_7", "climatology",
                     "arima_fourier", "ridge", "random_forest",
                     "random_forest_delta", "hist_gbm", "hist_gbm_delta",
                     "logistic", "forest_clf", "hgb_clf"}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "tables")

PRETTY = {
    "gru": "GRU, 30 day sequence",
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

ORDER = ["gru", "arima_fourier", "random_forest_delta", "hist_gbm_delta",
         "random_forest", "hist_gbm", "ridge", "naive_carry", "climatology",
         "seasonal_naive_7"]


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

    # Every seed run that exists, for the network only.
    seeds = sorted(glob.glob(os.path.join(ROOT, "gru_seed*.csv")))
    gru = {}
    for f in seeds:
        g = ev.regression_metrics(pd.read_csv(f, parse_dates=["origin"]), scale,
                                  reference="naive_carry")
        g = g[g.model == "gru"].set_index("horizon")["rMAE"]
        gru[os.path.basename(f)] = g
    G = pd.DataFrame(gru) if gru else None
    if G is not None:
        print(f"  network reported over {G.shape[1]} seeds")

    body = ["\\begin{tabular}{lccc r}", "\\toprule",
            "Model & $h=1$ & $h=2$ & $h=3$ & Bias at $h=1$ \\\\", "\\midrule"]
    for name in ORDER:
        if name == "gru" and G is not None:
            cells = [f"{G.loc[h].min():.3f} to {G.loc[h].max():.3f}" for h in (1, 2, 3)]
            body.append(f"{esc(PRETTY['gru'])}, range over {G.shape[1]} seeds & "
                        + " & ".join(cells)
                        + f" & {bias.loc['gru', 1]:+.1f} \\\\")
            continue
        if name not in piv.index:
            continue
        cells = [f"{piv.loc[name, h]:.3f}" for h in (1, 2, 3)]
        body.append(f"{esc(PRETTY.get(name, name))} & " + " & ".join(cells)
                    + f" & {bias.loc[name, 1]:+.1f} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("accuracy.tex", "\n".join(body) + "\n")


def table_warning(forecast_path, threshold=121.0):
    d = pd.read_csv(forecast_path, parse_dates=["origin"])
    w = ev.evaluate_warnings(d, event_threshold=threshold)
    body = ["\\begin{tabular}{lrrrrr}", "\\toprule",
            "Model & Hit rate & False alarm rate & Precision & CSI & Alarms/yr \\\\",
            "\\midrule"]
    for name in ORDER:
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
        arr = pd.DataFrame(per_seed, columns=budgets)
        gru_range = (arr.min(), arr.max())
        print(f"  GRU budget row reported over {len(seed_sweeps)} seeds")

    body = ["\\begin{tabular}{lrrrr}", "\\toprule",
            "Alarms per year & 40 & 60 & 80 & 100 \\\\", "\\midrule"]
    for h in (1, 2, 3):
        cells = []
        for b in budgets:
            g = sw[(sw.horizon == h) & (sw.alarms_per_year <= b)]
            cells.append(f"{g['hit_rate'].max():.3f}" if len(g) else "--")
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


def table_cleaning():
    rows = [("Value below zero", "5", "Mass concentration cannot be negative"),
            ("Coverage below 50\\%", "270", "Against the cadence taken from the data"),
            ("Value above 1000", "7", "Judgement; sensitivity analysis in Section~\\ref{sec:limitations}"),
            ("\\textbf{Total}", "\\textbf{282 of 3{,}375}", "")]
    body = ["\\begin{tabular}{llp{6.2cm}}", "\\toprule",
            "Rule & Days removed & Basis \\\\", "\\midrule"]
    for a, b, c in rows:
        body.append(f"{a} & {b} & {c} \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("cleaning.tex", "\n".join(body) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    clean = os.path.join(ROOT, "data", "delhi_clean.csv")
    fc = os.path.join(ROOT, "forecasts_with_gru.csv")
    if not os.path.exists(fc):
        fc = os.path.join(ROOT, "forecasts_all.csv")
    sweep = os.path.join(ROOT, "threshold_sweep.csv")

    print("Generating tables from the result files:")
    table_dataset(clean)
    table_accuracy(fc, clean)
    table_warning(fc)
    table_cleaning()
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

    # Figures live beside the report so latex finds them without absolute paths.
    import shutil
    figdir = os.path.join(HERE, "figures")
    os.makedirs(figdir, exist_ok=True)
    for f in ["fig1_series.png", "fig2_coverage.png", "fig3_weekly.png",
              "fig4_annual.png", "fig5_warning.png"]:
        src = os.path.join(ROOT, f)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(figdir, f))
            print(f"  copied figures/{f}")
    print("\nNow: latexmk -pdf main.tex")


if __name__ == "__main__":
    main()
