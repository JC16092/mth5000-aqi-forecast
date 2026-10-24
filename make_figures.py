"""Figures for the supervision brief.

House style: serif, Liberation Serif metric-compatible with Times so the
figures sit consistently beside Times body text, no chartjunk. Colour is
used where it carries information (distinguishing series, flagging a
specific point) and skipped where position alone already does the job.
Every figure carries one argument; anything that does not serve that
argument is left out.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf
from scipy import stats

import evaluation as ev
from step01_data_check import load_series
from step07_warning import operating_point_at_alarms

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 8.5,
    "axes.linewidth": 0.6,
    "axes.edgecolor": "0.3",
    "axes.labelsize": 8.5,
    "axes.titlesize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "xtick.color": "0.3", "ytick.color": "0.3",
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
})

THRESHOLD = 121.0
RAW = "data/delhi.csv"
CLEAN = "data/delhi_clean.csv"
W = 6.3

# Monash blue (#006CAB, sampled directly from figures/monash-logo.svg),
# extended to a full categorical set with the Okabe-Ito colour-blind-safe
# palette (Monash's own blue stands in almost exactly for Okabe-Ito's
# "blue"), so multi-series figures stay distinguishable without relying on
# colour alone -- line style or marker shape still carries the same
# distinction wherever there is more than one series.
BLUE = "#006CAB"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
SKYBLUE = "#56B4E9"
FLAG = VERMILLION  # the one colour used, throughout, to mark a called-out point


def strip(ax, left=True):
    """Recessive axes: keep only what carries information."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if not left:
        ax.spines["left"].set_visible(False)
    ax.tick_params(length=3)


def load(path):
    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date")
    full = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    return df.set_index("date").reindex(full)


# ---------------------------------------------------------------- figure 1
def fig_series(clean):
    s = clean["PM2.5"]
    fig, ax = plt.subplots(figsize=(W, 2.5))

    ax.fill_between(s.index, THRESHOLD, s.where(s > THRESHOLD),
                    color=VERMILLION, alpha=0.25, linewidth=0, zorder=2)
    ax.plot(s.index, s.values, lw=0.35, color=BLUE, zorder=3)
    ax.axhline(THRESHOLD, color="black", ls=(0, (4, 3)), lw=0.8, zorder=4)

    i = s.idxmax()
    ax.plot([i], [s.max()], "o", ms=3.5, mfc="white", mec=FLAG, mew=1.0, zorder=5)
    ax.annotate(f"{s.max():.0f} on {i.date()}", xy=(i, s.max()),
                xytext=(12, -2), textcoords="offset points", fontsize=7.5, va="center")

    # Right hand end, where the series has run out and nothing is obscured.
    ax.text(s.index[-1], THRESHOLD + 18, f"hazard threshold, {THRESHOLD:.0f}",
            fontsize=7.5, va="bottom", ha="right")
    ax.set_ylabel("PM2.5 (µg per cubic metre)")
    ax.set_ylim(0, 950)
    strip(ax)
    fig.savefig("fig1_series.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def fig_coverage(raw):
    df = raw.dropna(subset=["n_obs"]).copy()
    df["year"] = df.index.year
    cad = df.groupby("year")["n_obs"].quantile(0.9).round()
    df["cadence"] = df["year"].map(cad)
    df["cov"] = 100 * df["n_obs"] / df["cadence"]

    fig, axes = plt.subplots(1, 2, figsize=(W, 2.75),
                             gridspec_kw={"width_ratios": [1.55, 1], "wspace": 0.45,
                                          "top": 0.80})

    ax = axes[0]
    ax.plot(df.index, df["n_obs"], ".", ms=0.9, color=SKYBLUE, zorder=2)
    ax.plot(df.index, df["cadence"], color=BLUE, lw=1.1, zorder=4)
    ax.axhline(24, color="black", ls=(0, (4, 3)), lw=0.8, zorder=3)
    # Both annotations sit in the empty band above the data rather than on top
    # of the scatter, which was unreadable in print.
    # Label each line at its right hand end, in clear space, rather than over
    # the scatter, which was unreadable in print.
    # Offset off the lines themselves, so neither label reads as a strikethrough.
    ax.text(df.index[-1], 19, "  assumed 24", fontsize=7.2, va="center", ha="left")
    ax.text(df.index[-1], 53, "  actual", fontsize=7.2, va="center", ha="left", color=BLUE)
    ax.text(df.index[40], 55, "readings contributing to each daily mean",
            fontsize=7.2, va="bottom")
    ax.set_ylabel("readings per day")
    ax.set_ylim(0, 62)
    ax.set_xlim(df.index[0], df.index[-1] + pd.Timedelta(days=650))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_title("(a) The cadence changed; the assumption did not", loc="left", pad=8)
    strip(ax)

    ax = axes[1]
    bands = [(0, 50), (50, 75), (75, 90), (90, 1000)]
    labels = ["0 to 50", "50 to 75", "75 to 90", "over 90"]
    rate, n = [], []
    for lo, hi in bands:
        sub = df[(df["cov"] >= lo) & (df["cov"] < hi)].dropna(subset=["PM2.5_raw"])
        n.append(len(sub))
        rate.append(1000 * (sub["PM2.5_raw"] > 500).sum() / max(len(sub), 1))
    y = np.arange(len(bands))[::-1]
    ax.barh(y, rate, height=0.55, color=VERMILLION, edgecolor="none")
    for yi, r, ni in zip(y, rate, n):
        ax.text(r + 0.5, yi, f"{r:.1f}   (n = {ni})", va="center", fontsize=7.2)
    ax.set_yticks(y); ax.set_yticklabels([f"{l}%" for l in labels])
    ax.set_xlabel("days above 500, per 1000 observed")
    ax.set_xlim(0, max(rate) * 1.55)
    ax.set_xticks([])
    ax.set_title("(b) Implausible values by true coverage\n      of the day",
                 loc="left", pad=8)
    strip(ax, left=False)
    ax.spines["bottom"].set_visible(False)
    fig.savefig("fig2_coverage.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 3
def deseasonalise(clean, K=4):
    y = np.log(clean["PM2.5"])
    doy = y.index.dayofyear.values.astype(float)
    X = [np.ones(len(y))]
    for k in range(1, K + 1):
        X.append(np.sin(2 * np.pi * k * doy / 365.25))
        X.append(np.cos(2 * np.pi * k * doy / 365.25))
    X = np.column_stack(X)
    m = y.notna().values
    fit = sm.OLS(y.values[m], X[m]).fit()
    r = pd.Series(np.nan, index=y.index)
    r[m] = fit.resid
    return r, fit.rsquared


def fig_weekly(clean):
    r, _ = deseasonalise(clean)
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.4),
                             gridspec_kw={"width_ratios": [1.35, 1]})

    ax = axes[0]
    rr = r.interpolate(limit=3).dropna()
    a = acf(rr, nlags=21, fft=True)
    band = 1.96 / np.sqrt(len(rr))
    lags = np.arange(1, 22)
    ax.axhspan(-band, band, color=BLUE, alpha=0.12, zorder=1)
    weekly = np.isin(lags, [7, 14, 21])
    ax.vlines(lags, 0, a[1:22], color=BLUE, alpha=0.5, lw=1.0, zorder=2)
    ax.plot(lags[~weekly], a[1:22][~weekly], "o", ms=3, color=BLUE, zorder=3)
    ax.plot(lags[weekly], a[1:22][weekly], "o", ms=5, mfc="white", mec=FLAG,
            mew=1.2, zorder=4)
    for L in (7, 14, 21):
        ax.annotate(str(L), xy=(L, a[L]), xytext=(0, 7), textcoords="offset points",
                    ha="center", fontsize=7.5)
    ax.axhline(0, color="0.3", lw=0.6)
    ax.set_xlabel("lag (days)")
    ax.set_ylabel("autocorrelation")
    ax.xaxis.set_major_locator(MultipleLocator(7))
    ax.set_title("(a) Lags 7, 14 and 21 sit on the decay, not above it", loc="left")
    strip(ax)

    ax = axes[1]
    d = pd.DataFrame({"r": r, "dow": r.index.dayofweek}).dropna()
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    means, los, his = [], [], []
    for i in range(7):
        g = d[d.dow == i]["r"]
        se = g.std(ddof=1) / np.sqrt(len(g))
        h = 1.96 * se
        means.append(100 * (np.exp(g.mean()) - 1))
        los.append(100 * (np.exp(g.mean() - h) - 1))
        his.append(100 * (np.exp(g.mean() + h) - 1))
    y = np.arange(7)[::-1]
    ax.axvline(0, color="0.3", lw=0.6, zorder=1)
    ax.hlines(y, los, his, color=BLUE, alpha=0.55, lw=1.2, zorder=2)
    ax.plot(means, y, "o", ms=3.5, color=BLUE, zorder=3)
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.set_xlabel("effect on concentration (%)")
    ax.set_title("(b) No day differs from the rest\n      (ANOVA p = 0.34)", loc="left")
    strip(ax)
    fig.savefig("fig3_weekly.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 4
def fig_annual(clean):
    s = clean["PM2.5"].dropna()
    g = s.groupby(s.index.month)
    med = g.median()
    q1, q3 = g.quantile(0.25), g.quantile(0.75)
    months = np.arange(1, 13)
    names = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

    fig, ax = plt.subplots(figsize=(W * 0.62, 2.15))
    ax.fill_between(months, q1, q3, color=BLUE, alpha=0.18, linewidth=0, zorder=2)
    ax.plot(months, med, color=BLUE, lw=1.3, zorder=4)
    ax.plot(months, med, "o", ms=3, color=BLUE, zorder=5)
    ax.axhline(THRESHOLD, color="black", ls=(0, (4, 3)), lw=0.8, zorder=3)
    # Placed in the summer trough, where the line has nothing under it.
    ax.text(6.5, THRESHOLD + 10, "hazard threshold", fontsize=7.2, ha="center")
    ax.set_xticks(months); ax.set_xticklabels(names)
    ax.set_ylabel("PM2.5 (µg per cubic metre)")
    ax.set_xlabel("month")
    ax.set_xlim(0.6, 12.4)
    ax.set_ylim(0, None)
    strip(ax)
    fig.savefig("fig4_annual.png")
    plt.close(fig)




# ---------------------------------------------------------------- figure 5
def fig_warning(sweep_path="threshold_sweep.csv"):
    """The figure the report is built around.

    Top row is the classical trade: hit rate against false alarm rate. Bottom row
    replaces the false alarm rate with alarms raised per year, which is the same
    information expressed in the units an operator actually budgets in. A false
    alarm rate of 0.10 sounds negligible and is roughly one wasted alarm every ten
    quiet days.

    Identity is carried by colour and line style together, redundantly, rather
    than colour alone. Four curves per panel is the limit at which that stays
    readable, so one representative of each family is shown.
    """
    sw = pd.read_csv(sweep_path)

    show = [
        ("arima_fourier", "ARIMA", "-", BLUE, 1.4),
        ("hist_gbm_delta", "gradient boosting", "--", ORANGE, 1.2),
        ("hgb_clf", "classifier", "-.", GREEN, 1.2),
        ("naive_carry", "persistence", ":", VERMILLION, 1.2),
    ]
    present = [x for x in show if x[0] in set(sw["model"])]

    fig, axes = plt.subplots(2, 3, figsize=(W, 4.4), sharey=True,
                             gridspec_kw={"hspace": 0.45, "wspace": 0.12})

    for col, h in enumerate([1, 2, 3]):
        for row, xcol in enumerate(["false_alarm_rate", "alarms_per_year"]):
            ax = axes[row, col]
            for name, label, ls, colr, lw in present:
                g = sw[(sw.model == name) & (sw.horizon == h)].sort_values("threshold")
                g = g.dropna(subset=[xcol, "hit_rate"])
                if not len(g):
                    continue
                ax.plot(g[xcol], g["hit_rate"], ls=ls, color=colr, lw=lw, zorder=3,
                        label=label if (row == 0 and col == 0) else None)
                # Direct labels were tried and abandoned: the curves converge at
                # the right hand edge, which is the finding, so labels placed
                # there collide. A legend in the first panel is the honest fix.
            if row == 0:
                ax.set_xlim(0, 0.15)
                ax.set_xlabel("false alarm rate")
                ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
            else:
                ax.set_xlim(0, 200)
                ax.set_xlabel("alarms per year")
                for b in (60, 120):
                    ax.axvline(b, color="0.85", lw=0.7, zorder=1)
                if col == 0:
                    ax.text(62, 0.06, "60", fontsize=6.5, color="0.5")
                    ax.text(122, 0.06, "120 alarms/yr", fontsize=6.5, color="0.5")
            ax.set_ylim(0, 1.02)
            if col == 0:
                ax.set_ylabel("hit rate")
            if row == 0 and col == 0:
                ax.legend(loc="lower right", fontsize=6.6, handlelength=2.4,
                          borderpad=0.2, labelspacing=0.25)
            strip(ax)

    fig.savefig("fig5_warning.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 6
def fig_accuracy(fc_path="forecasts_with_transformer.csv", series_path=CLEAN, burn_in=1095):
    """RQ1, the figure Table 3 never had. A Cleveland dot plot: one row per
    model, one panel per horizon, a dot at that model's rMAE relative to
    persistence (the dashed line at 1.0). All three seeded networks, the GRU,
    the LSTM and the transformer added after Dr Tian's suggestion, get a
    horizontal range bar instead of a dot, across all ten seeds each, the
    same distinction the report's own text insists on rather than a single
    favourable run.
    Climatology and the seasonal-naive benchmark are left off: both sit far
    outside this range at one day ahead and would compress the competitive
    cluster that is actually the point of the figure; their numbers are in
    Table 3, unchanged.
    """
    s = load_series(series_path, "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[burn_in]].values)

    fc = pd.read_csv(fc_path, parse_dates=["origin"])
    common = ev.restrict_to_common(fc)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")

    order = ["gru", "lstm", "transformer", "arima_fourier", "hist_gbm_delta",
             "random_forest_delta", "hist_gbm", "random_forest", "ridge", "naive_carry"]
    labels = {
        "gru": "GRU, range over 10 seeds", "lstm": "LSTM, range over 10 seeds",
        "transformer": "Transformer, range over 10 seeds",
        "arima_fourier": "ARIMA",
        "hist_gbm_delta": "gradient boosting, change",
        "random_forest_delta": "random forest, change",
        "hist_gbm": "gradient boosting, level",
        "random_forest": "random forest, level",
        "ridge": "ridge", "naive_carry": "persistence",
    }
    SEEDED = {"gru": "gru_seed*.csv", "lstm": "lstm_seed*.csv",
              "transformer": "transformer_seed*.csv"}

    import glob
    seeded_by_h = {}
    for model_name, pattern in SEEDED.items():
        seed_files = sorted(glob.glob(pattern))
        by_h = {h: [] for h in (1, 2, 3)}
        for f in seed_files:
            g = ev.restrict_to_common(pd.read_csv(f, parse_dates=["origin"]))
            gm = ev.regression_metrics(g, scale, reference="naive_carry")
            for h in (1, 2, 3):
                row = gm[(gm.model == model_name) & (gm.horizon == h)]
                if len(row):
                    by_h[h].append(float(row["rMAE"].iloc[0]))
        seeded_by_h[model_name] = by_h

    FAMILY = {"gru": VERMILLION, "lstm": VERMILLION, "transformer": VERMILLION,
              "arima_fourier": BLUE, "naive_carry": "0.3"}

    y = np.arange(len(order))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(W, 3.6), sharey=True,
                             gridspec_kw={"wspace": 0.08})

    for col, h in enumerate([1, 2, 3]):
        ax = axes[col]
        ax.axvline(1.0, color="0.75", lw=0.8, zorder=1)
        for yi, name in zip(y, order):
            colr = FAMILY.get(name, ORANGE)
            if name in seeded_by_h and seeded_by_h[name][h]:
                lo, hi = min(seeded_by_h[name][h]), max(seeded_by_h[name][h])
                ax.plot([lo, hi], [yi, yi], color=colr, lw=2.6, zorder=3,
                        solid_capstyle="round")
                continue
            row = metrics[(metrics.model == name) & (metrics.horizon == h)]
            if not len(row):
                continue
            v = float(row["rMAE"].iloc[0])
            ax.plot(v, yi, "o", ms=5, mfc=colr, mec="none", zorder=3)
        if col == 0:
            ax.set_yticks(y)
            ax.set_yticklabels([labels[n] for n in order], fontsize=7.3)
        ax.set_ylim(-0.8, len(order) - 0.2)
        ax.set_xlim(0.78, 1.04)
        ax.set_xlabel("rMAE")
        ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
        strip(ax, left=(col == 0))
        ax.tick_params(axis="y", length=0)

    fig.savefig("fig6_accuracy.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 7
def fig_arms(sweep_path="threshold_sweep.csv"):
    """RQ2, the figure Table 4 never had. Table 4 gives the matched-pairs
    comparison at one day ahead only; this gives it at every horizon, which
    is where the edge for forecast-then-threshold actually narrows and, at
    the loosest budget, reverses. One line per matched pair, the hit-rate
    advantage of forecasting-then-thresholding over its matched classifier;
    above the zero line it wins, below it the classifier does.
    """
    sw = pd.read_csv(sweep_path)
    budgets = (40, 60, 80, 100)
    pairs = [
        ("ridge", "logistic", "ridge vs. logistic", "-", BLUE),
        ("random_forest_delta", "forest_clf", "random forest vs. its classifier", "--", ORANGE),
        ("hist_gbm_delta", "hgb_clf", "gradient boosting vs. its classifier", ":", GREEN),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(W, 2.7), sharey=True,
                             gridspec_kw={"wspace": 0.1})

    for col, h in enumerate([1, 2, 3]):
        ax = axes[col]
        ax.axhline(0, color="0.75", lw=0.8, zorder=1)
        for reg, clf, label, ls, colr in pairs:
            diffs = []
            for b in budgets:
                r = operating_point_at_alarms(sw, reg, h, b)
                c = operating_point_at_alarms(sw, clf, h, b)
                d = ((r["hit_rate"] - c["hit_rate"])
                     if (r is not None and c is not None) else np.nan)
                diffs.append(d)
            ax.plot(budgets, diffs, ls, color=colr, lw=1.4, marker="o",
                    ms=3.3, mfc=colr, mec="none", zorder=3,
                    label=label if col == 0 else None)
        ax.set_xlim(35, 105)
        ax.set_xticks(budgets)
        ax.set_xlabel("alarms per year")
        ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
        if col == 0:
            ax.set_ylabel("hit-rate edge, forecast-\nthen-threshold minus classifier")
        ax.set_ylim(-0.1, 0.1)
        strip(ax, left=(col == 0))

    axes[0].legend(loc="lower left", fontsize=6.5, handlelength=2.6,
                   borderpad=0.2, labelspacing=0.3, frameon=False)
    fig.savefig("fig7_arms.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 8
def fig_predictions(fc_path="forecasts_with_transformer.csv",
                     start="2024-11-01", end="2025-02-15"):
    """What the one-day-ahead forecasts actually look like against the
    series they are predicting, over one representative winter window
    rather than the full 6.8 years, which would compress every episode
    into an unreadable smear. ARIMA is its usual rolling-origin fit; the
    GRU line is seed 0 alone, for illustration only, exactly the single-seed
    presentation the rest of this report deliberately avoids for any
    reported number.
    """
    fc = pd.read_csv(fc_path, parse_dates=["origin"])
    fc = fc[fc["horizon"] == 1].copy()
    fc["target"] = fc["origin"] + pd.Timedelta(days=1)

    def series_for(model):
        g = fc[fc["model"] == model].sort_values("target")
        g = g[(g["target"] >= start) & (g["target"] <= end)]
        return g.set_index("target")

    actual = series_for("arima_fourier")["y_true"]
    arima = series_for("arima_fourier")["y_pred"]
    gru = series_for("gru")["y_pred"]

    fig, ax = plt.subplots(figsize=(W, 2.6))
    ax.fill_between(actual.index, THRESHOLD, actual.where(actual > THRESHOLD),
                    color=VERMILLION, alpha=0.18, linewidth=0, zorder=1)
    ax.plot(actual.index, actual.values, color="0.15", lw=1.2, zorder=4,
            label="actual")
    ax.plot(arima.index, arima.values, color=BLUE, lw=1.1, ls="--", zorder=3,
            label="ARIMA, 1 day ahead")
    ax.plot(gru.index, gru.values, color=VERMILLION, lw=1.1, ls=":", zorder=3,
            label="GRU, 1 day ahead (seed 0, illustrative only)")
    ax.axhline(THRESHOLD, color="black", ls=(0, (1, 1)), lw=0.6, zorder=2)
    ax.text(actual.index[-1], THRESHOLD + 15, f"hazard threshold, {THRESHOLD:.0f}",
            fontsize=7.2, va="bottom", ha="right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("PM2.5 (µg per cubic metre)")
    ax.legend(loc="upper right", fontsize=7, handlelength=2.3, borderpad=0.2,
              labelspacing=0.25)
    strip(ax)
    fig.savefig("fig8_predictions.png")
    plt.close(fig)


# ---------------------------------------------------------------- figure 9
def fig_gru_sensitivity(hyper_path="gru_hyperparam_sensitivity.csv",
                         fourier_path="gru_fourier_ablation.csv",
                         opt_path="gru_optimizer_sensitivity.csv"):
    """The three bounded checks behind Section 5.3's claim that the GRU's
    three-day configuration is this report's least defensible: architecture
    (hidden size, window length), seasonal input (Fourier order) and
    training procedure (optimiser, learning rate), each varied one at a
    time around the fitted default and scored by the same three seeds. One
    row per setting, one panel per horizon, mean rMAE across the three
    seeds; the vertical line in each panel is the default configuration
    used everywhere else in this report. The point is not any single row:
    it is that the rows barely move at one day ahead and spread out at
    three.
    """
    hp = pd.read_csv(hyper_path)
    fo = pd.read_csv(fourier_path)
    op = pd.read_csv(opt_path)

    def mean_rmae(frame, mask, h):
        g = frame[mask & (frame.horizon == h)]
        return g["rMAE"].mean()

    order = [
        ("Architecture", "H=24, 30-day window (default)"),
        ("Architecture", "H=12"),
        ("Architecture", "H=48"),
        ("Architecture", "15-day window"),
        ("Architecture", "45-day window"),
        ("Architecture", "60-day window"),
        ("Seasonal input", "K=4 (matches ARIMA)"),
        ("Training", "Adam, lr=0.003"),
        ("Training", "Adam, lr=0.03"),
        ("Training", "SGD, lr=0.01"),
        ("Training", "RMSprop, lr=0.01"),
    ]
    masks = {
        "H=24, 30-day window (default)": (hp, hp.sweep == "default"),
        "H=12": (hp, (hp.sweep == "hidden") & (hp.hidden == 12)),
        "H=48": (hp, (hp.sweep == "hidden") & (hp.hidden == 48)),
        "15-day window": (hp, (hp.sweep == "seq_len") & (hp.seq_len == 15)),
        "45-day window": (hp, (hp.sweep == "seq_len") & (hp.seq_len == 45)),
        "60-day window": (hp, (hp.sweep == "seq_len") & (hp.seq_len == 60)),
        "K=4 (matches ARIMA)": (fo, fo.fourier_k == 4),
        "Adam, lr=0.003": (op, (op.sweep == "lr") & (op.lr == 0.003)),
        "Adam, lr=0.03": (op, (op.sweep == "lr") & (op.lr == 0.03)),
        "SGD, lr=0.01": (op, (op.sweep == "optimizer") & (op.optimizer == "sgd")),
        "RMSprop, lr=0.01": (op, (op.sweep == "optimizer") & (op.optimizer == "rmsprop")),
    }

    y_pos, labels, cur_group = [], [], None
    y = 0
    for grp, label in order:
        if cur_group is not None and grp != cur_group:
            y -= 1
        y_pos.append(y)
        labels.append(label)
        y -= 1
        cur_group = grp
    group_header_y = {"Architecture": y_pos[0] + 0.9,
                      "Seasonal input": y_pos[[g for g, _ in order].index("Seasonal input")] + 0.9,
                      "Training": y_pos[[g for g, _ in order].index("Training")] + 0.9}

    default_rmae = {h: mean_rmae(hp, hp.sweep == "default", h) for h in (1, 2, 3)}
    GROUP_COLOR = {"Architecture": BLUE, "Seasonal input": ORANGE, "Training": GREEN}

    fig, axes = plt.subplots(1, 3, figsize=(W, 3.9), sharey=True,
                             gridspec_kw={"wspace": 0.08})
    for col, h in enumerate([1, 2, 3]):
        ax = axes[col]
        ax.axvline(default_rmae[h], color="0.75", lw=0.9, zorder=1)
        for yi, (grp, label) in zip(y_pos, order):
            frame, mask = masks[label]
            v = mean_rmae(frame, mask, h)
            is_default = label.endswith("(default)")
            marker = "s" if is_default else "o"
            colr = "0.15" if is_default else GROUP_COLOR[grp]
            ax.plot(v, yi, marker, ms=4.2 if marker == "o" else 5,
                    mfc=colr, mec="none", zorder=3)
        if col == 0:
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=7.1)
            for grp_name, gy in group_header_y.items():
                ax.text(0.775, gy, grp_name, fontsize=6.8, style="italic",
                        color=GROUP_COLOR[grp_name], va="bottom")
        ax.set_ylim(min(y_pos) - 0.8, 1.9)
        ax.set_xlim(0.78, 1.00)
        ax.set_xlabel("rMAE")
        ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
        strip(ax, left=(col == 0))
        ax.tick_params(axis="y", length=0)

    fig.savefig("fig9_gru_sensitivity.png")
    plt.close(fig)


# --------------------------------------------------------------- figure 10
def fig_arima_stability(path="arima_coefficient_stability.csv"):
    """The refit-by-refit stability check behind Section 3.4.1's claim that
    a single reported coefficient pair describes the model this evaluation
    settles into for most of its span, not a property holding at every
    refit. Two panels, one per coefficient, against the 28 refit origins.
    The dashed line in panel (b) is the invertibility boundary; the three
    refits that cross it are marked open rather than filled.
    """
    df = pd.read_csv(path, parse_dates=["refit_origin"]).sort_values("refit_origin")
    crosses = df["theta_1"] < -1.0

    fig, axes = plt.subplots(1, 2, figsize=(W, 2.5),
                             gridspec_kw={"wspace": 0.3})

    ax = axes[0]
    ax.plot(df["refit_origin"], df["phi_1"], "-o", color=BLUE, lw=1.0,
            ms=2.8, mfc=BLUE, mec="none", zorder=3)
    ax.set_ylabel(r"$\hat\phi_1$")
    ax.set_title("(a) The AR coefficient", loc="left")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    strip(ax)

    ax = axes[1]
    ax.axhline(-1.0, color="black", ls=(0, (4, 3)), lw=0.8, zorder=2)
    ax.text(df["refit_origin"].iloc[0], -1.0 - 0.0025, "invertibility boundary",
            fontsize=7.2, va="top")
    ax.plot(df.loc[~crosses, "refit_origin"], df.loc[~crosses, "theta_1"],
            "o", ms=3.2, color=BLUE, mfc=BLUE, mec="none", zorder=3)
    ax.plot(df["refit_origin"], df["theta_1"], "-", color=BLUE, alpha=0.4, lw=0.8, zorder=2)
    ax.plot(df.loc[crosses, "refit_origin"], df.loc[crosses, "theta_1"],
            "o", ms=5, mfc="white", mec=FLAG, mew=1.2, zorder=4)
    ax.set_ylabel(r"$\hat\theta_1$")
    ax.set_title("(b) The MA coefficient: 3 of 28 refits cross the boundary",
                 loc="left")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    strip(ax)

    fig.savefig("fig10_arima_stability.png")
    plt.close(fig)


# --------------------------------------------------------------- figure 11
def fig_architecture_bounded():
    """The four architectures' single-split, three-seed bounded checks,
    together: GRU (the report's own default configuration), LSTM,
    transformer, and the Kolmogorov-Arnold-LSTM hybrid, each scored on the
    same held-out split and the same three seeds. The vertical line in
    each panel is ARIMA's rolling-origin rMAE from Table 4.1, included so
    the bounded checks can be read against the same reference the rest of
    the report uses, not only against each other.
    """
    gru = pd.read_csv("gru_hyperparam_sensitivity.csv")
    gru = gru[gru.sweep == "default"]
    lstm = pd.read_csv("lstm_bounded_check.csv")
    transformer = pd.read_csv("transformer_bounded_check.csv")
    kan = pd.read_csv("kan_lstm_bounded_check.csv")

    order = ["GRU (default)", "LSTM", "Transformer", "Kolmogorov-Arnold-LSTM"]
    frames = {"GRU (default)": gru, "LSTM": lstm, "Transformer": transformer,
              "Kolmogorov-Arnold-LSTM": kan}
    colors = {"GRU (default)": BLUE, "LSTM": ORANGE, "Transformer": GREEN,
              "Kolmogorov-Arnold-LSTM": VERMILLION}
    arima_rmae = {1: 0.940, 2: 0.883, 3: 0.832}

    y = np.arange(len(order))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(W, 2.3), sharey=True,
                             gridspec_kw={"wspace": 0.08})
    for col, h in enumerate([1, 2, 3]):
        ax = axes[col]
        ax.axvline(arima_rmae[h], color="0.75", lw=0.9, zorder=1,
                   label="ARIMA (Table 4.1)" if col == 0 else None)
        for yi, name in zip(y, order):
            g = frames[name]
            vals = g[g.horizon == h]["rMAE"]
            lo, hi = vals.min(), vals.max()
            ax.plot([lo, hi], [yi, yi], color=colors[name], lw=2.6, zorder=3,
                    solid_capstyle="round")
        if col == 0:
            ax.set_yticks(y)
            ax.set_yticklabels(order, fontsize=7.6)
        ax.set_ylim(-0.8, len(order) - 0.2)
        ax.set_xlim(0.78, 1.00)
        ax.set_xlabel("rMAE")
        ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
        strip(ax, left=(col == 0))
        ax.tick_params(axis="y", length=0)
    axes[0].legend(loc="lower right", fontsize=6.6, handlelength=1.8,
                   borderpad=0.2, labelspacing=0.25, frameon=False)

    fig.savefig("fig11_architecture_bounded.png")
    plt.close(fig)


# --------------------------------------------------------------- figure 12
def fig_weather_effect(scale_series=CLEAN, burn_in=1095):
    """The weather-covariate reversal behind Section 4.1.1: the GRU with
    and without wind speed and temperature, each as a range over ten
    seeds, by horizon. Table 4.4 reports this as numbers; this is the
    same comparison as two range bars per horizon rather than a column of
    text, so the width of each bar, not just its position, is visible.
    """
    import glob
    s = load_series(scale_series, "date", "PM2.5")
    scale = ev.mase_scale(s.loc[:s.index[burn_in]].values)

    def seed_rmae(pattern):
        by_h = {h: [] for h in (1, 2, 3)}
        for f in sorted(glob.glob(pattern)):
            g = ev.restrict_to_common(pd.read_csv(f, parse_dates=["origin"]))
            gm = ev.regression_metrics(g, scale, reference="naive_carry")
            for h in (1, 2, 3):
                row = gm[(gm.model == "gru") & (gm.horizon == h)]
                if len(row):
                    by_h[h].append(float(row["rMAE"].iloc[0]))
        return by_h

    plain = seed_rmae("gru_seed*.csv")
    weather = seed_rmae("gru_weather_seed*.csv")

    rows = [("with weather", weather, BLUE), ("plain", plain, ORANGE)]
    y = np.arange(len(rows))[::-1]
    fig, axes = plt.subplots(1, 3, figsize=(W, 1.75), sharey=True,
                             gridspec_kw={"wspace": 0.08})
    for col, h in enumerate([1, 2, 3]):
        ax = axes[col]
        for yi, (label, by_h, colr) in zip(y, rows):
            lo, hi = min(by_h[h]), max(by_h[h])
            ax.plot([lo, hi], [yi, yi], color=colr, lw=3.4, zorder=3,
                    solid_capstyle="round")
        if col == 0:
            ax.set_yticks(y)
            ax.set_yticklabels([r[0] for r in rows], fontsize=7.8)
        ax.set_ylim(-0.8, len(rows) - 0.2)
        ax.set_xlabel("rMAE")
        ax.set_title(f"{h} day{'s' if h > 1 else ''} ahead", loc="left")
        strip(ax, left=(col == 0))
        ax.tick_params(axis="y", length=0)

    fig.savefig("fig12_weather_effect.png")
    plt.close(fig)


# --------------------------------------------------------------- figure 13
def fig_periodogram(series_path=CLEAN):
    """The frequency-domain counterpart to Figure 3.3's time-domain test:
    the same periodogram Section 3.3.2 quotes six dominant periods from
    (357.9, 178.9, 188.4, 397.7, 325.4 and 60.7 days), computed the
    identical way, now actually plotted rather than only tabulated in
    prose. A weekly cycle would appear as a peak at 7 days; there is none.
    """
    from scipy.signal import periodogram
    s = load_series(series_path, "date", "PM2.5")
    filled = s.interpolate(limit_direction="both")
    freqs, power = periodogram(filled - filled.mean(), fs=1.0)
    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)
    keep = (periods >= 2) & (periods <= 400)
    periods, power = periods[keep], power[keep]
    top = np.argsort(power)[::-1][:6]

    fig, ax = plt.subplots(figsize=(W, 2.3))
    ax.plot(periods, power, color=BLUE, lw=0.6, zorder=2)
    ax.plot(periods[top], power[top], "o", ms=4, mfc="white", mec=FLAG,
            mew=1.2, zorder=4)
    ax.axvline(7, color="black", ls=(0, (1, 1)), lw=0.7, zorder=1)
    ax.text(7, power.max() * 1.02, "7 days",
            fontsize=7.2, ha="center", va="bottom")
    ax.set_xscale("log")
    ax.set_xlim(2, 430)
    ax.set_xlabel("period (days)")
    ax.set_ylabel("power")
    ax.set_yticks([])
    strip(ax, left=False)
    ax.spines["left"].set_visible(False)
    fig.savefig("fig13_periodogram.png")
    plt.close(fig)


if __name__ == "__main__":
    raw = load(RAW)
    clean = load(CLEAN)
    fig_series(clean)
    fig_coverage(raw)
    fig_weekly(clean)
    fig_annual(clean)
    try:
        fig_warning()
        print("wrote fig5_warning.png")
    except FileNotFoundError:
        print("threshold_sweep.csv not found; skipping figure 5")
    try:
        fig_accuracy()
        print("wrote fig6_accuracy.png")
    except FileNotFoundError:
        print("forecasts_with_gru.csv not found; skipping figure 6")
    try:
        fig_arms()
        print("wrote fig7_arms.png")
    except FileNotFoundError:
        print("threshold_sweep.csv not found; skipping figure 7")
    try:
        fig_predictions()
        print("wrote fig8_predictions.png")
    except FileNotFoundError:
        print("forecasts_with_transformer.csv not found; skipping figure 8")
    try:
        fig_gru_sensitivity()
        print("wrote fig9_gru_sensitivity.png")
    except FileNotFoundError:
        print("GRU sensitivity CSVs not found; skipping figure 9")
    try:
        fig_arima_stability()
        print("wrote fig10_arima_stability.png")
    except FileNotFoundError:
        print("arima_coefficient_stability.csv not found; skipping figure 10")
    try:
        fig_architecture_bounded()
        print("wrote fig11_architecture_bounded.png")
    except FileNotFoundError:
        print("bounded-check CSVs not found; skipping figure 11")
    try:
        fig_weather_effect()
        print("wrote fig12_weather_effect.png")
    except FileNotFoundError:
        print("weather seed CSVs not found; skipping figure 12")
    try:
        fig_periodogram()
        print("wrote fig13_periodogram.png")
    except FileNotFoundError:
        print("CLEAN series not found; skipping figure 13")
    _, r2 = deseasonalise(clean)
    print(f"annual Fourier K=4 on log PM2.5: R2 = {r2:.3f}")
    print("wrote fig1_series.png fig2_coverage.png fig3_weekly.png fig4_annual.png")
