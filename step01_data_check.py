"""
MTH5000 - Step 1: data viability check and first look.

Run this before writing any modelling code. It answers three questions:
  1. Do I have a long enough continuous daily series to model?
  2. How much is missing, and is it scattered or one large hole?
  3. Are the weekly and annual cycles actually there, or am I assuming them?

Usage:
    python step01_data_check.py --csv data/delhi.csv --date-col date --value-col PM2.5

If you have no data yet, run with --demo to generate a synthetic series with
known structure. Useful for checking the script works before you fight with
real files.
"""

import argparse
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # write files, do not open windows
import matplotlib.pyplot as plt

# CPCB AQI category breakpoints for PM2.5 (ug/m3, 24h mean).
# "Very poor" starts at 121 and "severe" at 250. The threshold you choose for
# a warning is a decision, not a fact; justify it in the report.
HAZARD_THRESHOLD = 121.0


def load_series(csv_path, date_col, value_col):
    """Read a CSV into a clean daily series indexed by date."""
    df = pd.read_csv(csv_path)

    if date_col not in df.columns or value_col not in df.columns:
        sys.exit(f"Columns not found. Available columns: {list(df.columns)}")

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])

    # Non-numeric junk (blanks, 'NA', '-') becomes NaN rather than crashing.
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")

    # Several stations on the same day: average them into a city-level value.
    s = df.groupby(date_col)[value_col].mean().sort_index()

    # Reindex onto a complete daily calendar so gaps become explicit NaNs
    # rather than silently missing rows. This matters: a model that never
    # sees the gap will quietly treat two distant days as adjacent.
    full_index = pd.date_range(s.index.min(), s.index.max(), freq="D")
    return s.reindex(full_index)


def make_demo_series(n_years=6, seed=0):
    """Synthetic daily series with known weekly and annual structure."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=365 * n_years, freq="D")
    t = np.arange(len(idx))

    annual = 60 * np.cos(2 * np.pi * (t - 15) / 365.25)   # winter peak
    weekly = 8 * np.sin(2 * np.pi * t / 7)
    level = 90 + 0.004 * t
    noise = rng.normal(0, 18, len(idx))

    values = np.clip(level + annual + weekly + noise, 5, None)
    s = pd.Series(values, index=idx)

    # Knock out ~4% of days to imitate instrument downtime.
    drop = rng.choice(len(s), size=int(0.04 * len(s)), replace=False)
    s.iloc[drop] = np.nan
    return s


def report_coverage(s):
    """Print the coverage facts that decide whether the project is viable."""
    n_total = len(s)
    n_obs = int(s.notna().sum())
    n_missing = n_total - n_obs

    # Longest unbroken run of NaNs: one long outage is far worse than
    # the same number of days scattered about.
    is_na = s.isna().values
    longest_gap, run = 0, 0
    for flag in is_na:
        run = run + 1 if flag else 0
        longest_gap = max(longest_gap, run)

    print("\n" + "=" * 58)
    print("COVERAGE")
    print("=" * 58)
    print(f"  Date range        : {s.index.min().date()} to {s.index.max().date()}")
    print(f"  Calendar days     : {n_total}")
    print(f"  Observed          : {n_obs}  ({100 * n_obs / n_total:.1f}%)")
    print(f"  Missing           : {n_missing}  ({100 * n_missing / n_total:.1f}%)")
    print(f"  Longest gap       : {longest_gap} consecutive days")
    print(f"  Years of data     : {n_total / 365.25:.1f}")

    print("\n  Verdict:")
    if n_total / 365.25 < 3:
        print("  - Under 3 years. The annual cycle will be poorly estimated.")
    if n_missing / n_total > 0.20:
        print("  - Over 20% missing. Try a different station.")
    if longest_gap > 60:
        print(f"  - A {longest_gap}-day hole will distort the seasonal fit.")
    if n_total / 365.25 >= 3 and n_missing / n_total <= 0.20 and longest_gap <= 60:
        print("  - Usable. Proceed.")

    print("\n" + "=" * 58)
    print("DISTRIBUTION")
    print("=" * 58)
    print(s.describe().round(1).to_string())

    exceed = (s > HAZARD_THRESHOLD).sum()
    print(f"\n  Days above {HAZARD_THRESHOLD:.0f}: {exceed} "
          f"({100 * exceed / n_obs:.1f}% of observed days)")
    print("  These are the events the warning system has to catch.")
    if exceed < 100:
        print("  Note: few exceedances means wide uncertainty on hit rates.")


def report_structure(s):
    """Stationarity test and dominant periodicities."""
    from statsmodels.tsa.stattools import adfuller

    clean = s.dropna()

    # statsmodels is changing adfuller to return a result object rather than a
    # tuple. Handle both so this does not break on a future version.
    res = adfuller(clean, autolag="AIC")
    if isinstance(res, tuple):
        stat, pval, _, _, crit = res[0], res[1], res[2], res[3], res[4]
    else:
        stat, pval, crit = res.stat, res.pvalue, res.critical_values
    print("\n" + "=" * 58)
    print("STATIONARITY (Augmented Dickey-Fuller)")
    print("=" * 58)
    print(f"  Test statistic : {stat:.3f}")
    print(f"  p-value        : {pval:.4f}")
    print(f"  5% critical    : {crit['5%']:.3f}")
    print("  ->", "rejects a unit root (stationary)" if pval < 0.05
          else "cannot reject a unit root (differencing likely needed)")

    # Periodogram on the mean-removed series. Interpolation here is only for
    # the spectral estimate, which cannot handle gaps; the modelling later
    # uses the state-space formulation and does not interpolate.
    from scipy.signal import periodogram
    filled = s.interpolate(limit_direction="both")
    freqs, power = periodogram(filled - filled.mean(), fs=1.0)

    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

    keep = (periods >= 2) & (periods <= 400)
    top = np.argsort(power[keep])[::-1][:6]

    print("\n" + "=" * 58)
    print("DOMINANT PERIODS (from the periodogram)")
    print("=" * 58)
    for rank, i in enumerate(top, 1):
        p = periods[keep][i]
        print(f"  {rank}. {p:8.1f} days")
    print("\n  Look for peaks near 7 (weekly) and near 365 (annual).")
    print("  If both are present, SARIMA alone cannot take both seasonal")
    print("  periods, which is the modelling decision to settle with Dr Tian.")


def make_plots(s, out_prefix="step01"):
    """Three diagnostic figures."""
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf

    # 1. The series, with hazardous days marked.
    fig, ax = plt.subplots(figsize=(13, 4.5))
    ax.plot(s.index, s.values, lw=0.6, color="0.3")
    ax.axhline(HAZARD_THRESHOLD, color="firebrick", ls="--", lw=1,
               label=f"hazard threshold ({HAZARD_THRESHOLD:.0f})")
    above = s > HAZARD_THRESHOLD
    ax.scatter(s.index[above], s[above], s=4, color="firebrick", zorder=3)
    ax.set_title("Daily concentration, with threshold exceedances marked")
    ax.set_ylabel("PM2.5")
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(f"{out_prefix}_series.png", dpi=150)
    plt.close(fig)

    # 2. ACF and PACF.
    clean = s.dropna()
    fig, axes = plt.subplots(1, 2, figsize=(13, 4))
    plot_acf(clean, lags=60, ax=axes[0])
    axes[0].set_title("ACF (60 lags: look for a spike at 7)")
    plot_pacf(clean, lags=60, ax=axes[1], method="ywm")
    axes[1].set_title("PACF")
    fig.tight_layout()
    fig.savefig(f"{out_prefix}_acf_pacf.png", dpi=150)
    plt.close(fig)

    # 3. Monthly profile: the annual cycle made visible.
    fig, ax = plt.subplots(figsize=(8, 4))
    by_month = s.groupby(s.index.month).mean()
    ax.bar(by_month.index, by_month.values, color="0.4")
    ax.axhline(HAZARD_THRESHOLD, color="firebrick", ls="--", lw=1)
    ax.set_xticks(range(1, 13))
    ax.set_xlabel("month")
    ax.set_ylabel("mean PM2.5")
    ax.set_title("Mean concentration by month")
    fig.tight_layout()
    fig.savefig(f"{out_prefix}_monthly.png", dpi=150)
    plt.close(fig)

    print("\n  Wrote: "
          f"{out_prefix}_series.png, {out_prefix}_acf_pacf.png, "
          f"{out_prefix}_monthly.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--date-col", default="date")
    ap.add_argument("--value-col", default="PM2.5")
    ap.add_argument("--demo", action="store_true",
                    help="use a synthetic series instead of a file")
    args = ap.parse_args()

    if args.demo:
        print("Using synthetic demo data (no real file loaded).")
        s = make_demo_series()
    elif args.csv:
        s = load_series(args.csv, args.date_col, args.value_col)
    else:
        sys.exit("Give --csv PATH or --demo. See --help.")

    report_coverage(s)
    report_structure(s)
    make_plots(s)

    print("\nNext: if coverage passed, move to differencing and SARIMA.\n")


if __name__ == "__main__":
    main()
