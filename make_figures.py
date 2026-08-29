"""Figures for the supervision brief.

House style: serif, black and grey only, no colour, no chartjunk. Liberation
Serif is metric compatible with Times, so the figures sit consistently beside
Times body text. Every figure carries one argument; anything that does not serve
that argument is left out.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf
from scipy import stats

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
                    color="0.55", linewidth=0, zorder=2)
    ax.plot(s.index, s.values, lw=0.35, color="0.25", zorder=3)
    ax.axhline(THRESHOLD, color="black", ls=(0, (4, 3)), lw=0.8, zorder=4)

    i = s.idxmax()
    ax.plot([i], [s.max()], "o", ms=3.5, mfc="white", mec="black", mew=0.8, zorder=5)
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

    fig, axes = plt.subplots(1, 2, figsize=(W, 2.4),
                             gridspec_kw={"width_ratios": [1.55, 1], "wspace": 0.42})

    ax = axes[0]
    ax.plot(df.index, df["n_obs"], ".", ms=0.9, color="0.5", zorder=2)
    ax.plot(df.index, df["cadence"], color="black", lw=1.0, zorder=4)
    ax.axhline(24, color="black", ls=(0, (4, 3)), lw=0.8, zorder=3)
    ax.text(df.index[40], 20.5, "denominator OpenAQ assumes (24)", fontsize=7.2, va="top")
    ax.text(df.index[40], 51.0, "readings in a full day, taken from the data",
            fontsize=7.2, va="bottom")
    ax.set_ylabel("readings per day")
    ax.set_ylim(0, 56)
    ax.set_title("(a) The cadence changed; the assumption did not", loc="left")
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
    ax.barh(y, rate, height=0.55, color="0.45", edgecolor="none")
    for yi, r, ni in zip(y, rate, n):
        ax.text(r + 0.5, yi, f"{r:.1f}   (n = {ni})", va="center", fontsize=7.2)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel("days above 500, per 1000 observed")
    ax.set_xlim(0, max(rate) * 1.55)
    ax.set_xticks([])
    ax.set_title("(b) Impossible values cluster where\n      true coverage is poor", loc="left")
    ax.text(-0.02, 1.0, "true coverage (%)", transform=ax.transAxes, fontsize=7.6,
            ha="right", va="bottom", color="0.3")
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
    ax.axhspan(-band, band, color="0.88", zorder=1)
    weekly = np.isin(lags, [7, 14, 21])
    ax.vlines(lags, 0, a[1:22], color="0.45", lw=1.0, zorder=2)
    ax.plot(lags[~weekly], a[1:22][~weekly], "o", ms=3, color="0.35", zorder=3)
    ax.plot(lags[weekly], a[1:22][weekly], "o", ms=5, mfc="white", mec="black",
            mew=1.0, zorder=4)
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
    ax.hlines(y, los, his, color="0.55", lw=1.0, zorder=2)
    ax.plot(means, y, "o", ms=3.5, color="black", zorder=3)
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
    ax.fill_between(months, q1, q3, color="0.85", linewidth=0, zorder=2)
    ax.plot(months, med, color="black", lw=1.2, zorder=4)
    ax.plot(months, med, "o", ms=3, color="black", zorder=5)
    ax.axhline(THRESHOLD, color="black", ls=(0, (4, 3)), lw=0.8, zorder=3)
    ax.text(1.1, THRESHOLD + 8, "hazard threshold", fontsize=7.2)
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

    Monochrome, so identity is carried by line style and a direct label at the end
    of each curve rather than by colour. Four curves per panel is the limit at
    which that stays readable, so one representative of each family is shown.
    """
    sw = pd.read_csv(sweep_path)

    show = [
        ("arima_fourier", "ARIMA", "-", "black", 1.3),
        ("hist_gbm_delta", "gradient boosting", "--", "0.35", 1.1),
        ("hgb_clf", "classifier", "-.", "0.5", 1.1),
        ("naive_carry", "persistence", ":", "0.6", 1.1),
    ]
    present = [x for x in show if x[0] in set(sw["model"])]

    fig, axes = plt.subplots(2, 3, figsize=(W, 4.4), sharey=True,
                             gridspec_kw={"hspace": 0.45, "wspace": 0.12,
                                          "right": 0.88})

    for col, h in enumerate([1, 2, 3]):
        for row, xcol in enumerate(["false_alarm_rate", "alarms_per_year"]):
            ax = axes[row, col]
            for name, label, ls, colr, lw in present:
                g = sw[(sw.model == name) & (sw.horizon == h)].sort_values("threshold")
                g = g.dropna(subset=[xcol, "hit_rate"])
                if not len(g):
                    continue
                ax.plot(g[xcol], g["hit_rate"], ls=ls, color=colr, lw=lw, zorder=3)
                if col == 2 and row == 0:
                    # Direct label on the curve at the right hand edge of the
                    # visible range, found by interpolation rather than by taking
                    # the last point, which lies outside the axis limits.
                    xs = g[xcol].values
                    ys = g["hit_rate"].values
                    order = np.argsort(xs)
                    yv = float(np.interp(0.135, xs[order], ys[order]))
                    ax.annotate(label, xy=(0.135, yv), xytext=(4, 0),
                                textcoords="offset points", fontsize=6.8,
                                va="center", color=colr)
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
            strip(ax)

    fig.savefig("fig5_warning.png")
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
    _, r2 = deseasonalise(clean)
    print(f"annual Fourier K=4 on log PM2.5: R2 = {r2:.3f}")
    print("wrote fig1_series.png fig2_coverage.png fig3_weekly.png fig4_annual.png")
