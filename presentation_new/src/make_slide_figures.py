"""Slide figures for the oral presentation.

A slide figure is not a paper figure: it is drawn at the size it is shown (so a 14 pt label is a 14 pt label
on the projector), carries one argument, and is stripped of everything that does not serve it. These are
drawn from the same data files and the same palette as the report's figures; where a figure plots numbers
that the report publishes in a table, the table is the source and the figure says so below.

Run from anywhere:   python presentation_new/src/make_slide_figures.py
Needs matplotlib, numpy, pandas, scipy, statsmodels (the report's own requirements).
Writes PNGs with transparent backgrounds to presentation_new/assets_slides/.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm
from matplotlib.ticker import MultipleLocator, PercentFormatter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "presentation_new", "assets_slides")
os.makedirs(OUT, exist_ok=True)

THRESHOLD = 121.0
# Deck palette. Monash blue and the Okabe-Ito accents are the report's; vermillion marks a called-out point only.
NAVY, BLUE, SKY = "#0B2545", "#006CAB", "#56B4E9"
ORANGE, GREEN, VERM = "#E69F00", "#009E73", "#D55E00"
INK, GREY, LIGHT = "#1B2733", "#5B6B7A", "#B9C4CF"

fam = "Carlito" if any(f.name == "Carlito" for f in fm.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({
    "font.family": fam, "font.size": 14, "text.color": INK,
    "axes.labelsize": 14, "axes.labelcolor": INK, "axes.edgecolor": GREY, "axes.linewidth": 1.0,
    "xtick.labelsize": 13, "ytick.labelsize": 13, "xtick.color": GREY, "ytick.color": GREY,
    "legend.fontsize": 13, "legend.frameon": False,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 250, "savefig.transparent": True, "savefig.bbox": "tight", "savefig.pad_inches": 0.04,
})


def load_clean():
    df = pd.read_csv(os.path.join(ROOT, "data", "delhi_clean.csv"), parse_dates=["date"]).sort_values("date")
    full = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    return df.set_index("date").reindex(full)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name))
    plt.close(fig)
    print("wrote", name)


def deseasonalise(clean, K=4):
    import statsmodels.api as sm
    y = np.log(clean["PM2.5"])
    doy = y.index.dayofyear.values.astype(float)
    X = [np.ones(len(y))]
    for k in range(1, K + 1):
        X += [np.sin(2 * np.pi * k * doy / 365.25), np.cos(2 * np.pi * k * doy / 365.25)]
    X = np.column_stack(X)
    m = y.notna().values
    fit = sm.OLS(y.values[m], X[m]).fit()
    r = pd.Series(np.nan, index=y.index)
    r[m] = fit.resid
    return r


# ------------------------------------------------------------------ the data
def fig_series(clean):
    s = clean["PM2.5"]
    fig, ax = plt.subplots(figsize=(12.1, 3.0))
    ax.fill_between(s.index, THRESHOLD, s.where(s > THRESHOLD), color=VERM, alpha=0.30, linewidth=0)
    ax.plot(s.index, s.values, lw=0.7, color=BLUE)
    ax.axhline(THRESHOLD, color=INK, ls=(0, (5, 3)), lw=1.2, label=f"hazard threshold, {THRESHOLD:.0f}")
    i = s.idxmax()
    ax.plot([i], [s.max()], "o", ms=7, mfc="white", mec=VERM, mew=2)
    ax.annotate(f"{s.max():.0f} on {i.date()}", xy=(i, s.max()), xytext=(14, -2), textcoords="offset points",
                fontsize=13, va="center")
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_ylim(0, 950)
    ax.legend(loc="upper right", handlelength=2.6)
    save(fig, "series.png")


def fig_cadence():
    """Panel for the coverage defect: readings per day the sensor really produces, against the fixed 24."""
    yrs = np.arange(2016.85, 2026.7, 0.05)
    true = np.where(yrs < 2025.0, 48, 24)
    fig, ax = plt.subplots(figsize=(6.0, 2.35))
    ax.plot(yrs, true, color=BLUE, lw=3, label="actual cadence (half-hourly, then hourly)")
    ax.axhline(24, color=VERM, ls=(0, (5, 3)), lw=2.2)
    ax.text(2016.9, 19, "assumed by the coverage statistic: 24", color=VERM, fontsize=13, va="top")
    ax.text(2016.9, 51, "readings per day the sensor produces", color=BLUE, fontsize=13, va="bottom")
    ax.set_ylim(0, 62)
    ax.set_xlim(2016.8, 2026.8)
    ax.set_yticks([0, 24, 48])
    ax.xaxis.set_major_locator(MultipleLocator(2))
    save(fig, "cadence.png")


def fig_implausible():
    """Report Figure 3.1(b): implausible values (days above 500) per 1000 observed days, by true coverage."""
    labels = ["0 to 50%", "50 to 75%", "75 to 90%", "over 90%"]
    rate = [18.5, 14.9, 15.2, 2.1]
    n = [270, 806, 395, 1904]
    fig, ax = plt.subplots(figsize=(5.85, 2.35))
    y = np.arange(4)[::-1]
    ax.barh(y, rate, color=[VERM, VERM, VERM, LIGHT], height=0.66)
    for yi, r, nn in zip(y, rate, n):
        ax.text(r + 0.4, yi, f"{r}", va="center", fontsize=13.5, fontweight="bold")
        ax.text(r + 3.4, yi, f"n = {nn:,}", va="center", fontsize=11.5, color=GREY)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 26)
    ax.set_xlabel("days above 500, per 1000 observed", fontsize=13)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "implausible.png")


def fig_periodogram():
    from scipy.signal import periodogram
    s = load_clean()["PM2.5"]
    filled = s.interpolate(limit_direction="both")
    freqs, power = periodogram(filled - filled.mean(), fs=1.0)
    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)
    keep = (periods >= 2) & (periods <= 400)
    periods, power = periods[keep], power[keep]
    top = np.argsort(power)[::-1][:6]
    fig, ax = plt.subplots(figsize=(4.2, 2.7))
    ax.plot(periods, power, color=BLUE, lw=1.1)
    ax.plot(periods[top], power[top], "o", ms=7, mfc="white", mec=VERM, mew=2)
    ax.axvline(7, color=INK, ls=(0, (1, 1.5)), lw=1.5)
    ax.text(8, power.max() * 0.93, "7 days", fontsize=14, fontweight="bold", va="top")
    ax.set_xscale("log")
    ax.set_xlim(2, 560)
    ax.set_xticks([10, 100])
    ax.set_xticklabels(["10", "100"])
    ax.set_xlabel("period (days)")
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    save(fig, "periodogram.png")


def fig_acf(clean):
    from statsmodels.tsa.stattools import acf
    r = deseasonalise(clean)
    rr = r.interpolate(limit=3).dropna()
    a = acf(rr, nlags=21, fft=True)
    band = 1.96 / np.sqrt(len(rr))
    lags = np.arange(1, 22)
    fig, ax = plt.subplots(figsize=(4.2, 2.7))
    ax.axhspan(-band, band, color=BLUE, alpha=0.14)
    weekly = np.isin(lags, [7, 14, 21])
    ax.vlines(lags, 0, a[1:22], color=BLUE, alpha=0.5, lw=1.6)
    ax.plot(lags[~weekly], a[1:22][~weekly], "o", ms=5, color=BLUE)
    ax.plot(lags[weekly], a[1:22][weekly], "o", ms=9, mfc="white", mec=VERM, mew=2.2)
    ax.text(7.4, a[7] + 0.09, "7", fontsize=14, fontweight="bold", ha="center")
    ax.set_xlabel("lag (days)")
    ax.set_ylabel("autocorrelation")
    ax.xaxis.set_major_locator(MultipleLocator(7))
    ax.set_ylim(-0.05, 0.7)
    save(fig, "acf.png")


def fig_dow(clean):
    r = deseasonalise(clean)
    d = pd.DataFrame({"r": r, "dow": r.index.dayofweek}).dropna()
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    m, lo, hi = [], [], []
    for i in range(7):
        g = d[d.dow == i]["r"]
        h = 1.96 * g.std(ddof=1) / np.sqrt(len(g))
        m.append(100 * (np.exp(g.mean()) - 1))
        lo.append(100 * (np.exp(g.mean() - h) - 1))
        hi.append(100 * (np.exp(g.mean() + h) - 1))
    y = np.arange(7)[::-1]
    fig, ax = plt.subplots(figsize=(4.2, 2.7))
    ax.axvline(0, color=GREY, lw=1)
    ax.hlines(y, lo, hi, color=BLUE, alpha=0.6, lw=2.2)
    ax.plot(m, y, "o", ms=7, color=BLUE)
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.set_xlabel("effect on concentration (%)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    save(fig, "dow.png")


def fig_annual(clean):
    s = clean["PM2.5"].dropna()
    g = s.groupby(s.index.month)
    med, q1, q3 = g.median(), g.quantile(0.25), g.quantile(0.75)
    months = np.arange(1, 13)
    fig, ax = plt.subplots(figsize=(5.4, 3.7))
    ax.fill_between(months, q1, q3, color=BLUE, alpha=0.18, linewidth=0)
    ax.plot(months, med, color=BLUE, lw=2.8)
    ax.plot(months, med, "o", ms=7, color=BLUE)
    ax.axhline(THRESHOLD, color=INK, ls=(0, (5, 3)), lw=1.2)
    ax.text(6.5, THRESHOLD + 12, "hazard threshold", fontsize=13, ha="center")
    ax.set_xticks(months)
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.set_xlim(0.6, 12.4)
    ax.set_ylim(0, None)
    save(fig, "annual.png")


# ------------------------------------------------------------------ the results
def fig_rq1():
    """Report Table 4.1, drawn. Networks are ranges over ten seeds; everything else is one fit."""
    rows = [  # label, (lo, hi) for h = 1, 2, 3, style
        ("GRU", [(0.910, 0.939), (0.878, 0.906), (0.831, 0.879)], "net", BLUE),
        ("LSTM", [(0.913, 0.932), (0.874, 0.892), (0.824, 0.847)], "net", ORANGE),
        ("Transformer", [(0.914, 0.925), (0.870, 0.893), (0.825, 0.842)], "net", GREEN),
        ("ARIMA + Fourier", [(0.940, 0.940), (0.883, 0.883), (0.832, 0.832)], "arima", NAVY),
        ("Gradient boosting, change", [(0.983,) * 2, (0.937,) * 2, (0.878,) * 2], "ml", GREY),
        ("Random forest, change", [(0.968,) * 2, (0.919,) * 2, (0.897,) * 2], "ml", GREY),
        ("Gradient boosting, level", [(1.008,) * 2, (0.945,) * 2, (0.885,) * 2], "ml", GREY),
        ("Random forest, level", [(0.988,) * 2, (0.934,) * 2, (0.879,) * 2], "ml", GREY),
        ("Ridge", [(0.997,) * 2, (0.952,) * 2, (0.897,) * 2], "ml", GREY),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12.1, 4.15), sharey=True, sharex=True,
                             gridspec_kw={"wspace": 0.07})
    y = np.arange(len(rows))[::-1]
    for h, ax in enumerate(axes):
        ax.axvline(1.0, color=GREY, lw=1.4, ls=(0, (4, 3)))
        ax.text(1.0, len(rows) - 0.25, "persistence", ha="center", va="bottom", fontsize=12, color=GREY)
        for yi, (name, rng, kind, col) in zip(y, rows):
            lo, hi = rng[h]
            if kind == "net":
                ax.plot([lo, hi], [yi, yi], color=col, lw=9, solid_capstyle="round")
            elif kind == "arima":
                ax.plot([lo], [yi], "D", ms=11, color=col)
                ax.text(lo + 0.011, yi, f"{lo:.3f}", ha="left", va="center", fontsize=13, fontweight="bold", color=col)
            else:
                ax.plot([lo], [yi], "o", ms=9, color=col)
        ax.set_title(f"{h + 1} day{'s' if h else ''} ahead", fontsize=15, fontweight="bold", loc="left", pad=16)
        ax.set_xlim(0.80, 1.035)
        ax.set_xticks([0.8, 0.9, 1.0])
        ax.set_xlabel("rMAE (lower is better)", fontsize=13)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_ylim(-0.7, len(rows) + 0.15)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([r[0] for r in rows], fontsize=13.5)
    for lab, r in zip(axes[0].get_yticklabels(), rows):
        lab.set_color(r[3] if r[2] != "ml" else INK)
        lab.set_fontweight("bold" if r[2] != "ml" else "normal")
    save(fig, "rq1.png")


def fig_seed_spread():
    """Width of each network's ten-seed range, from Table 4.1 (high minus low), against the 0.004 machine floor."""
    spread = {"GRU": [0.939 - 0.910, 0.906 - 0.878, 0.879 - 0.831],
              "LSTM": [0.932 - 0.913, 0.892 - 0.874, 0.847 - 0.824],
              "Transformer": [0.925 - 0.914, 0.893 - 0.870, 0.842 - 0.825]}
    cols = {"GRU": BLUE, "LSTM": ORANGE, "Transformer": GREEN}
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    w = 0.26
    x = np.arange(3)
    for i, (k, v) in enumerate(spread.items()):
        bars = ax.bar(x + (i - 1) * w, v, w * 0.92, color=cols[k], label=k)
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 0.0012, f"{val:.3f}", ha="center", fontsize=11.5)
    ax.axhline(0.004, color=VERM, lw=2.2, ls=(0, (5, 3)), label="0.004: tree models, two machines")
    ax.set_xticks(x)
    ax.set_xticklabels(["1 day ahead", "2 days", "3 days"])
    ax.set_ylabel("spread of ten seeds (rMAE)")
    ax.set_ylim(0, 0.072)
    ax.legend(loc="upper left", ncol=2, columnspacing=1.2, handlelength=1.4, fontsize=12.5)
    save(fig, "seed_spread.png")


def fig_winter():
    fc = pd.read_csv(os.path.join(ROOT, "forecasts_with_transformer.csv"), parse_dates=["origin"])
    fc = fc[fc["horizon"] == 1].copy()
    fc["target"] = fc["origin"] + pd.Timedelta(days=1)

    def get(model):
        g = fc[fc["model"] == model].sort_values("target")
        g = g[(g["target"] >= "2024-11-01") & (g["target"] <= "2025-02-15")]
        return g.set_index("target")

    actual, arima, gru = get("arima_fourier")["y_true"], get("arima_fourier")["y_pred"], get("gru")["y_pred"]
    fig, ax = plt.subplots(figsize=(12.1, 3.5))
    ax.fill_between(actual.index, THRESHOLD, actual.where(actual > THRESHOLD), color=VERM, alpha=0.20, linewidth=0)
    ax.plot(actual.index, actual.values, color=INK, lw=2.4, label="observed")
    ax.plot(arima.index, arima.values, color=NAVY, lw=2.2, ls="--", label="ARIMA, 1 day ahead")
    ax.plot(gru.index, gru.values, color=BLUE, lw=2.2, ls=":", label="GRU, 1 day ahead (seed 0, illustration only)")
    ax.axhline(THRESHOLD, color=GREY, ls=(0, (1, 1.5)), lw=1.3, label=f"hazard threshold, {THRESHOLD:.0f}")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("PM2.5 (µg/m³)")
    ax.legend(loc="upper right", handlelength=2.6)
    save(fig, "winter.png")


def fig_weather():
    """GRU ranges over ten seeds, plain against weather-augmented. Plain: Table 4.1. Weather: Table 4.4."""
    plain = [(0.910, 0.939), (0.878, 0.906), (0.831, 0.879)]
    wx = [(0.882, 0.926), (0.855, 0.887), (0.816, 0.873)]
    arima = [0.940, 0.883, 0.832]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.0), sharey=True, gridspec_kw={"wspace": 0.12})
    for h, ax in enumerate(axes):
        ax.plot(wx[h], [1, 1], color=BLUE, lw=11, solid_capstyle="round")
        ax.plot(plain[h], [0, 0], color=ORANGE, lw=11, solid_capstyle="round")
        ax.axvline(arima[h], color=NAVY, lw=2, ls=(0, (4, 2.5)))
        ax.text(arima[h], 1.62, " ARIMA", color=NAVY, ha="left", fontsize=12, fontweight="bold")
        ax.set_title(f"{h + 1} day{'s' if h else ''}", fontsize=14, fontweight="bold", loc="left")
        ax.set_ylim(-0.6, 1.95)
        ax.set_xlabel("rMAE", fontsize=13)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
    axes[0].set_yticks([0, 1])
    axes[0].set_yticklabels(["plain", "with\nweather"], fontsize=13)
    save(fig, "weather.png")


def fig_hero(step=3):
    """The central result. Hit rate against alarms per year at one day ahead, for four representative models,
    straight from threshold_sweep.csv. The curves nearly coincide; the budget axis does all the work.
    step 1: ARIMA alone; step 2: all four curves; step 3: with the two quantities the finding compares."""
    sw = pd.read_csv(os.path.join(ROOT, "threshold_sweep.csv"))
    show = [("climatology", "climatology", LIGHT, ":", 2.6), ("hist_gbm_delta", "gradient boosting", SKY, "--", 2.4),
            ("naive_carry", "persistence", GREY, "-.", 2.4), ("arima_fourier", "ARIMA + Fourier", NAVY, "-", 3.2)]
    fig, ax = plt.subplots(figsize=(7.7, 4.7))
    vals = {}
    grid = np.arange(1, 131)
    for key, label, col, ls, lw in show:
        if step == 1 and key != "arima_fourier":
            continue
        g = sw[(sw.model == key) & (sw.horizon == 1)].dropna(subset=["alarms_per_year", "hit_rate"])
        # the report's own definition (step07_warning.operating_point_at_alarms): best hit rate within a budget
        best = np.array([g[g.alarms_per_year <= b].hit_rate.max() if (g.alarms_per_year <= b).any() else np.nan for b in grid])
        ax.plot(grid, best, color=col, ls=ls, lw=lw, label=label)
        vals[key] = (best[39], best[99])
    print("best hit rate within 40 / 100 alarms per year:", {k: tuple(round(float(x), 3) for x in v) for k, v in vals.items()})
    if step == 3:
        for xb in (40, 100):
            ax.axvline(xb, color=LIGHT, lw=1.2, zorder=0)
        lo_pt, hi_pt = 0.379, 0.881  # Table 4.7: best model at 40 and at 100 alarms a year
        ax.plot([40], [lo_pt], "o", ms=9, color=VERM, zorder=6)
        ax.plot([100], [hi_pt], "o", ms=9, color=VERM, zorder=6)
        for yy, x1 in ((lo_pt, 40), (hi_pt, 100)):
            ax.plot([14, x1], [yy, yy], color=VERM, lw=1.2, ls=(0, (2, 3)), zorder=2)
        ax.annotate("", xy=(14, hi_pt), xytext=(14, lo_pt), arrowprops=dict(arrowstyle="<->", color=VERM, lw=2.6))
        ax.text(17, 0.63, "the dial: budget 40 to\n100 alarms a year:\n0.379 to 0.881\n(50 points)", color=VERM, fontsize=14,
                fontweight="bold", va="center")
        ax.plot([106, 106], [0.821, 0.881], color=BLUE, lw=3, solid_capstyle="butt")
        for yy in (0.821, 0.881):
            ax.plot([103.5, 108.5], [yy, yy], color=BLUE, lw=3)
        ax.text(111, 0.80, "the detector:\nmodel choice at a\nfixed budget:\n0.82 to 0.88\n(about 5 points)", color=BLUE, fontsize=14,
                fontweight="bold", va="top")
    ax.set_xlim(0, 150)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("alarms raised per year")
    ax.set_ylabel("hit rate (share of hazardous days caught)")
    ax.set_xticks([0, 40, 60, 80, 100, 120])
    ax.legend(loc="lower right", handlelength=2.6, bbox_to_anchor=(1.0, 0.04))
    save(fig, {1: "hero_1.png", 2: "hero_2.png", 3: "hero_budget.png"}[step])


def fig_detector_vs_dial():
    """Same axis, two questions. Left: swap the model at a fixed budget (100 alarms a year, h = 1, Table 4.7).
    Right: turn the budget with the best model (Table 4.7, best model, h = 1)."""
    det = [("climatology", 0.821, LIGHT), ("gradient boosting", 0.854, SKY), ("ARIMA + Fourier", 0.867, NAVY), ("persistence", 0.873, GREY)]
    dial = [("40", 0.379), ("60", 0.567), ("80", 0.735), ("100", 0.881)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.1, 3.9), sharey=True, gridspec_kw={"wspace": 0.12, "width_ratios": [1, 1]})
    x = np.arange(len(det))
    a1.bar(x, [d[1] for d in det], 0.62, color=[d[2] for d in det])
    for xi, d in zip(x, det):
        a1.text(xi, d[1] + 0.015, f"{d[1]:.3f}", ha="center", fontsize=14, fontweight="bold")
    a1.set_xticks(x)
    a1.set_xticklabels([d[0].replace(" + Fourier", "\n+ Fourier").replace("gradient boosting", "gradient\nboosting") for d in det], fontsize=13)
    a1.set_title("THE DETECTOR: swap the model", loc="left", fontsize=15, fontweight="bold", color=BLUE, pad=34)
    a1.set_ylabel("hit rate (share of hazardous days caught)")
    a1.text(0.0, 1.04, "fixed budget: 100 alarms a year", fontsize=13, color=GREY, transform=a1.transAxes)
    x2 = np.arange(len(dial))
    a2.bar(x2, [d[1] for d in dial], 0.62, color=VERM)
    for xi, d in zip(x2, dial):
        a2.text(xi, d[1] + 0.015, f"{d[1]:.3f}", ha="center", fontsize=14, fontweight="bold", color=VERM)
    a2.set_xticks(x2)
    a2.set_xticklabels([d[0] for d in dial], fontsize=13)
    a2.set_xlabel("alarms a year", fontsize=13)
    a2.set_title("THE DIAL: turn the budget", loc="left", fontsize=15, fontweight="bold", color=VERM, pad=34)
    a2.text(0.0, 1.04, "best model at each setting", fontsize=13, color=GREY, transform=a2.transAxes)
    for a in (a1, a2):
        a.set_ylim(0, 1.0)
    a2.spines["left"].set_visible(False)
    a2.tick_params(axis="y", length=0)
    save(fig, "dial_vs_detector.png")


def fig_waffle():
    """Of every 100 hazardous days, how many the best model catches at each budget (Table 4.7, best model, h = 1)."""
    opts = [(40, 0.379), (60, 0.567), (80, 0.735), (100, 0.881)]
    fig, axes = plt.subplots(1, 4, figsize=(12.1, 3.7), gridspec_kw={"wspace": 0.08})
    for ax, (b, hr) in zip(axes, opts):
        k = int(round(hr * 100 + 1e-9))
        for i in range(100):
            r, c = divmod(i, 10)
            ax.scatter(c, 9 - r, s=190, color=(VERM if i < k else "#E4EAF0"), edgecolors="none")
        ax.set_xlim(-0.8, 9.8)
        ax.set_ylim(-0.8, 9.8)
        ax.axis("off")
        ax.set_title(f"{b} alarms a year", fontsize=16, fontweight="bold", color=NAVY, pad=6)
        ax.text(4.5, -1.7, f"{k} of 100 caught", ha="center", fontsize=15, fontweight="bold", color=VERM)
        ax.text(4.5, -2.7, f"one alarm every {365.25 / b:.1f} days", ha="center", fontsize=13, color=GREY)
    save(fig, "waffle.png")


def fig_calendar(clean):
    s = clean["PM2.5"].dropna()
    df = pd.DataFrame({"v": s, "yr": s.index.year, "mo": s.index.month})
    g = df.groupby(["yr", "mo"])
    share = (g["v"].apply(lambda x: (x > THRESHOLD).mean())).unstack()
    count = g["v"].count().unstack()
    share = share.where(count >= 15)
    share = share.reindex(columns=range(1, 13))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("hz", ["#F3F7FB", "#F7D3B8", VERM])
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    im = ax.imshow(share.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(12))
    ax.set_xticklabels(list("JFMAMJJASOND"))
    ax.set_yticks(range(len(share.index)))
    ax.set_yticklabels(share.index)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("share of days above 121", fontsize=13)
    cb.outline.set_visible(False)
    save(fig, "calendar.png")


def fig_skyline(clean):
    """Cover motif: the last 365 days of the dataset itself, one bar per day, hazardous days in vermillion."""
    s = clean["PM2.5"].dropna().iloc[-365:]
    fig, ax = plt.subplots(figsize=(8.4, 1.5))
    cols = [VERM if v > THRESHOLD else SKY for v in s.values]
    ax.bar(np.arange(len(s)), np.minimum(s.values, 500), width=1.0, color=cols, alpha=0.95)
    ax.axhline(THRESHOLD, color="white", lw=1.2, ls=(0, (4, 3)))
    ax.set_xlim(-2, len(s) + 1)
    ax.axis("off")
    print("skyline covers", s.index[0].date(), "to", s.index[-1].date(), "| days above threshold:", int((s > THRESHOLD).sum()))
    save(fig, "skyline.png")


if __name__ == "__main__":
    clean = load_clean()
    fig_series(clean)
    fig_cadence()
    fig_implausible()
    fig_periodogram()
    fig_acf(clean)
    fig_dow(clean)
    fig_annual(clean)
    fig_rq1()
    fig_seed_spread()
    fig_winter()
    fig_weather()
    for k in (1, 2, 3):
        fig_hero(k)
    fig_detector_vs_dial()
    fig_waffle()
    fig_calendar(clean)
    fig_skyline(clean)
