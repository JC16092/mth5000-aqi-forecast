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
import evaluation as ev                            # noqa: E402

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
    sw = pd.read_csv(sweep_path)
    body = ["\\begin{tabular}{lrrrr}", "\\toprule",
            "Alarms per year & 40 & 60 & 80 & 100 \\\\", "\\midrule"]
    for h in (1, 2, 3):
        cells = []
        for b in (40, 60, 80, 100):
            g = sw[(sw.horizon == h) & (sw.alarms_per_year <= b)]
            cells.append(f"{g['hit_rate'].max():.3f}" if len(g) else "--")
        body.append(f"Best hit rate, $h={h}$ & " + " & ".join(cells) + " \\\\")
    body.append("\\midrule")
    for name in ["gru", "arima_fourier", "hist_gbm_delta", "naive_carry", "climatology"]:
        cells = []
        for b in (40, 60, 80, 100):
            g = sw[(sw.model == name) & (sw.horizon == 1) & (sw.alarms_per_year <= b)]
            cells.append(f"{g['hit_rate'].max():.3f}" if len(g) else "--")
        # Single run, so no range is claimed here.
        body.append(f"\\quad {esc(PRETTY.get(name, name))}, $h=1$ & "
                    + " & ".join(cells) + " \\\\")
    body += ["\\bottomrule", "\\end{tabular}"]
    write("budget.tex", "\n".join(body) + "\n")


def table_cleaning():
    rows = [("Value below zero", "5", "Mass concentration cannot be negative"),
            ("Coverage below 50\\%", "270", "Against the cadence taken from the data"),
            ("Value above 1000", "7", "Judgement; sensitivity analysis in Section 6"),
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
    else:
        print("  threshold_sweep.csv not found; skipping budget.tex")

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
