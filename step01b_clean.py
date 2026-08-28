"""
MTH5000 - Step 1b: inspect and clean physically impossible values.

Sits between the download and the feature table. It exists because step 1 on the
real series reported a minimum of -7.3 and a maximum of 1990, and neither is a
possible 24-hour mean PM2.5 concentration. Left in place, a single value of 1990
distorts every mean, every rolling statistic and every model fit near it.

    python step01b_clean.py --csv data/delhi.csv                 # report only
    python step01b_clean.py --csv data/delhi.csv --apply --out data/delhi_clean.csv

BY DEFAULT THIS SCRIPT CHANGES NOTHING. It prints what it found and what each
rule would remove. You choose the thresholds, and you defend them in the report.
That is deliberate: where the line sits between instrument noise and a real
extreme is a judgement about the instrument and the site, and it belongs to you
and Dr Tian, not to a default buried in a script.

THE TWO PROBLEMS, AND HOW TO THINK ABOUT THEM

Negative values. Mass concentration cannot be negative. Small negatives are
ordinary noise around the detection limit on reference monitors and appear in
raw output routinely. Large negatives are faults. Both are unusable as
concentrations, so both become NaN, and NaN is already what the rest of the
pipeline expects. Note in the report how many there were and how large.

High values. Harder, because Delhi genuinely does record extraordinary days, and
the extreme days are the entire point of this project. Deleting a real 900 to
protect yourself from a fake 1990 would remove exactly the events the warning
system exists to catch. So this script does not guess. It shows you each extreme
day with how many hours went into it and what the neighbouring days looked like,
because a real episode builds and decays over several days while an artifact
stands alone. Judge them, then set --max-value if you decide one is warranted.
"""

import argparse
import sys

import numpy as np
import pandas as pd


def load(csv_path):
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if "PM2.5" not in df.columns:
        sys.exit(f"No PM2.5 column. Found: {list(df.columns)}")
    df = df.sort_values("date").reset_index(drop=True)
    return add_true_coverage(df)


def add_true_coverage(df):
    """Recompute coverage against the sensor's actual reporting cadence.

    OpenAQ reports percentComplete as observedCount divided by an expectedCount
    of 24, assuming hourly reporting. This sensor reported half-hourly from 2016
    to 2024 and hourly from 2025, so for eight of the ten years the denominator
    is half what it should be. The visible symptom is percentComplete above 100,
    which is impossible and is the tell that the denominator is wrong. The
    invisible symptom is far worse: a day with 24 readings out of a real 48
    scores as fully complete, and a daily mean built from half a day of a
    polluted afternoon then enters the series as though it were a real daily
    mean. That is where the impossible extremes come from.

    The fix is to take the cadence from the data itself. The 90th percentile of
    observation counts within a year is a robust estimate of what a full day
    looks like for that year, and it tracks the 2025 switch automatically
    instead of needing to be told about it.
    """
    if "n_obs" not in df.columns:
        df["true_cov"] = np.nan
        return df
    year = df["date"].dt.year
    cadence = year.map(df.groupby(year)["n_obs"].quantile(0.9).round())
    df["cadence"] = cadence
    df["true_cov"] = 100.0 * df["n_obs"] / cadence
    return df


def neighbour_context(df, i, k=3):
    """Values on the k days either side, for judging whether a spike is real."""
    lo, hi = max(0, i - k), min(len(df), i + k + 1)
    out = []
    for j in range(lo, hi):
        v = df["PM2.5"].iloc[j]
        mark = ">" if j == i else " "
        out.append(f"{mark}{df['date'].iloc[j].date()} {('%8.1f' % v) if pd.notna(v) else '     NaN'}")
    return out


def report(df, top_n=12, spike_window=7):
    v = df["PM2.5"]
    n_obs = df["n_obs"] if "n_obs" in df.columns else pd.Series(np.nan, index=df.index)
    cov = df["true_cov"] if "true_cov" in df.columns else pd.Series(np.nan, index=df.index)

    if "cadence" in df.columns:
        print("\n" + "=" * 70)
        print("REPORTING CADENCE, TAKEN FROM THE DATA")
        print("=" * 70)
        cad = df.groupby(df["date"].dt.year)["cadence"].first()
        print("  year  readings per full day")
        for y, c in cad.items():
            print(f"  {y}   {c:.0f}")
        print("\n  Coverage below is computed against these, not against the")
        print("  API's assumption of 24. Where they differ, the API's own")
        print("  percentComplete is wrong and too generous.")
        for lo, hi in [(0, 25), (25, 50), (50, 75), (75, 90), (90, 1000)]:
            n = int(((cov >= lo) & (cov < hi)).sum())
            print(f"    true coverage {lo:>3} to {hi:<4}%: {n:>5} days")

    print("\n" + "=" * 70)
    print("PHYSICALLY IMPOSSIBLE: NEGATIVE VALUES")
    print("=" * 70)
    neg = df[v < 0]
    if neg.empty:
        print("  None.")
    else:
        print(f"  {len(neg)} days ({100 * len(neg) / v.notna().sum():.2f}% of observed)")
        print(f"  Range: {neg['PM2.5'].min():.1f} to {neg['PM2.5'].max():.1f}")
        print(f"\n  {'date':12} {'value':>8} {'obs':>5} {'cov%':>6}")
        for _, r in neg.sort_values("PM2.5").head(20).iterrows():
            h, c = r.get("n_obs", np.nan), r.get("true_cov", np.nan)
            print(f"  {str(r['date'].date()):12} {r['PM2.5']:8.1f} "
                  f"{('%5.0f' % h) if pd.notna(h) else '    ?'} "
                  f"{('%6.1f' % c) if pd.notna(c) else '     ?'}")
        if len(neg) > 20:
            print(f"  ... and {len(neg) - 20} more")
        print("\n  All of these become NaN. They are not concentrations.")

    print("\n" + "=" * 70)
    print("EXACT ZEROS")
    print("=" * 70)
    z = df[v == 0]
    print(f"  {len(z)} days. A 24-hour mean of exactly zero in Delhi is not")
    print("  credible either; treat these as instrument output, not measurement.")

    print("\n" + "=" * 70)
    print(f"LARGEST {top_n} VALUES, WITH CONTEXT")
    print("=" * 70)
    print("  A real episode builds and decays over several days. An artifact")
    print("  stands alone between ordinary neighbours. Look at the shape, and at")
    print("  how many hours went into the daily mean.\n")

    # Ratio to the local median, excluding the day itself, as an isolation score.
    med = v.rolling(spike_window, center=True, min_periods=3).median()
    ratio = v / med

    idx = v.nlargest(top_n).index
    for i in idx:
        h, c = n_obs.iloc[i], cov.iloc[i]
        print(f"  {df['date'].iloc[i].date()}  value {v.iloc[i]:7.1f}  "
              f"obs {('%2.0f' % h) if pd.notna(h) else ' ?'}  "
              f"cov {('%5.1f' % c) if pd.notna(c) else '    ?'}%  "
              f"local median {med.iloc[i]:6.1f}  ratio {ratio.iloc[i]:5.1f}")
        print("      " + " | ".join(neighbour_context(df, i, k=2)))
        print()

    print("  A ratio near 1 to 3 with high neighbours is a real episode.")
    print("  A ratio above roughly 8 with ordinary neighbours, especially on")
    print("  few hours, is an artifact.")

    print("\n" + "=" * 70)
    print("DISTRIBUTION OF THE UPPER TAIL")
    print("=" * 70)
    for q in [0.99, 0.995, 0.999, 1.0]:
        print(f"  {q * 100:6.1f} percentile : {v.quantile(q):8.1f}")
    for cut in [500, 750, 1000, 1500]:
        n = int((v > cut).sum())
        print(f"  days above {cut:5d} : {n}")


def apply_rules(df, min_value, max_value, max_ratio, drop_zeros=False,
                min_coverage=None, use_raw=True, spike_window=7):
    # Work from PM2.5_raw when it is there. The PM2.5 column was already
    # filtered during download using the API's wrong denominator, so starting
    # from it would bake that mistake in permanently.
    source = "PM2.5_raw" if (use_raw and "PM2.5_raw" in df.columns) else "PM2.5"
    v = df[source].copy()
    reason = pd.Series("", index=df.index)

    if min_coverage is not None and "true_cov" in df.columns:
        m = (df["true_cov"] < min_coverage) & v.notna()
        reason[m] = "low_coverage"
        v[m] = np.nan

    if min_value is not None:
        m = (v < min_value) & v.notna()
        reason[m] = "below_min"
        v[m] = np.nan

    # Zero is treated separately from negative on purpose. A negative is
    # arithmetically impossible; a zero is merely not credible for a 24-hour
    # mean in Delhi. Those are different claims, so they get different switches
    # and you can report them separately.
    if drop_zeros:
        m = (v == 0) & v.notna()
        reason[m] = "exact_zero"
        v[m] = np.nan

    if max_value is not None:
        m = (v > max_value) & v.notna()
        reason[m] = "above_max"
        v[m] = np.nan

    if max_ratio is not None:
        med = df[source].rolling(spike_window, center=True, min_periods=3).median()
        m = (df[source] / med > max_ratio) & v.notna()
        reason[m] = "isolated_spike"
        v[m] = np.nan

    out = df.copy()
    out["PM2.5"] = v
    out["clean_reason"] = reason
    return out


def summarise(before, after):
    src = "PM2.5_raw" if "PM2.5_raw" in before.columns else "PM2.5"
    b, a = before[src], after["PM2.5"]
    removed = int(b.notna().sum() - a.notna().sum())
    print("\n" + "=" * 70)
    print("APPLIED")
    print("=" * 70)
    print(f"  Observed before : {int(b.notna().sum())}")
    print(f"  Observed after  : {int(a.notna().sum())}")
    print(f"  Removed         : {removed}")
    if "clean_reason" in after.columns:
        counts = after["clean_reason"].value_counts()
        tallied = 0
        for k, n in counts.items():
            if k:
                print(f"    {k:16} {n}")
                tallied += n
        # Each rule claims only the days it actually removed, so this must add up.
        if tallied != removed:
            print(f"    WARNING: reasons total {tallied}, removed {removed}")
    print(f"\n  mean  {b.mean():8.1f}  ->  {a.mean():8.1f}")
    print(f"  std   {b.std():8.1f}  ->  {a.std():8.1f}")
    print(f"  max   {b.max():8.1f}  ->  {a.max():8.1f}")
    print(f"  min   {b.min():8.1f}  ->  {a.min():8.1f}")
    over_b = int((b > 121).sum())
    over_a = int((a > 121).sum())
    print(f"\n  Days above 121: {over_b} -> {over_a}")
    print("  If that number moved much, say so in the report. It is the")
    print("  event count every hit rate in the project is computed against.")


def test_rules(verbose=True):
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    idx = pd.date_range("2024-01-01", periods=15, freq="D")
    vals = [50, 55, 60, -7.3, 58, 62, 1990.0, 61, 59, 0.0, 57, 300, 320, 310, 55]
    df = pd.DataFrame({"date": idx, "PM2.5": vals, "n_obs": [24] * 15})

    out = apply_rules(df, min_value=0.0, max_value=None, max_ratio=None)
    check(pd.isna(out["PM2.5"].iloc[3]), "negative value was not removed")
    check(out["clean_reason"].iloc[3] == "below_min", "reason not recorded")
    check(out["PM2.5"].iloc[6] == 1990.0, "max_value None must remove nothing")
    check(out["PM2.5"].iloc[9] == 0.0,
          "a zero must survive min_value 0.0; it needs --drop-zeros, which is a "
          "separate judgement from a negative")

    out = apply_rules(df, min_value=0.0, max_value=None, max_ratio=None, drop_zeros=True)
    check(pd.isna(out["PM2.5"].iloc[9]), "--drop-zeros did not remove the zero")
    check(out["clean_reason"].iloc[9] == "exact_zero", "zero reason not recorded")

    out = apply_rules(df, min_value=0.0, max_value=1000.0, max_ratio=None)
    check(pd.isna(out["PM2.5"].iloc[6]), "1990 should be removed by max_value 1000")

    # The isolated spike must go, the genuine three day episode must survive.
    out = apply_rules(df, min_value=None, max_value=None, max_ratio=8.0)
    check(pd.isna(out["PM2.5"].iloc[6]), "isolated 1990 spike was not caught by ratio")
    check(out["PM2.5"].iloc[12] == 320.0,
          "a real multi-day episode was wrongly removed by the ratio rule")

    # Nothing at all when no rule is given.
    out = apply_rules(df, None, None, None)
    check(out["PM2.5"].equals(df["PM2.5"]), "default run must change nothing")

    # Cadence detection and the coverage rule.
    idx2 = pd.date_range("2019-01-01", periods=8, freq="D")
    d2 = pd.DataFrame({
        "date": idx2,
        "PM2.5":     [100, 900, 110, 120, 130, 140, 150, 160],
        "PM2.5_raw": [100, 900, 110, 120, 130, 140, 150, 160],
        # a half-hourly sensor: a full day is 48, so 24 is only half a day
        "n_obs":     [ 48,  24,  48,  47,  46,  48,  48,  12],
    })
    d2 = add_true_coverage(d2)
    check(d2["cadence"].iloc[0] == 48, f"cadence should be 48, got {d2['cadence'].iloc[0]}")
    check(abs(d2["true_cov"].iloc[1] - 50.0) < 1e-6,
          "24 of 48 readings must score 50 percent, not 100")

    out = apply_rules(d2, None, None, None, min_coverage=75.0)
    check(pd.isna(out["PM2.5"].iloc[1]),
          "the half covered day producing 900 was not removed by the coverage rule")
    check(pd.isna(out["PM2.5"].iloc[7]), "the 12 reading day was not removed")
    check(out["PM2.5"].iloc[0] == 100, "a fully covered day was wrongly removed")
    check(out["clean_reason"].iloc[1] == "low_coverage", "coverage reason not recorded")

    # Must work from PM2.5_raw, not from an already filtered PM2.5 column.
    d3 = d2.copy()
    d3["PM2.5"] = [np.nan] * 8          # as if the download had blanked everything
    out = apply_rules(d3, None, None, None, min_coverage=0.0)
    check(out["PM2.5"].notna().sum() == 8,
          "apply_rules must start from PM2.5_raw, not from the filtered column")

    if verbose:
        print("  Cleaning rule checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Inspect and clean impossible values.")
    ap.add_argument("--csv", default="data/delhi.csv")
    ap.add_argument("--out", default="data/delhi_clean.csv")
    ap.add_argument("--apply", action="store_true", help="write a cleaned file")
    ap.add_argument("--min-value", type=float, default=0.0,
                    help="values below this become NaN (default 0.0)")
    ap.add_argument("--max-value", type=float, default=None,
                    help="values above this become NaN (default: no upper cut)")
    ap.add_argument("--max-ratio", type=float, default=None,
                    help="remove days more than this many times the local median")
    ap.add_argument("--drop-zeros", action="store_true",
                    help="also remove exact zeros, a separate call from negatives")
    ap.add_argument("--min-coverage", type=float, default=None,
                    help="minimum percent of the day observed, against the true "
                         "cadence taken from the data, not the API's assumption")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if test_rules() else 1)

    df = load(args.csv)
    report(df)

    if not args.apply:
        print("\n" + "=" * 70)
        print("NOTHING WAS CHANGED")
        print("=" * 70)
        print("  This was a report. When you have decided the thresholds:")
        print(f"    python step01b_clean.py --csv {args.csv} --apply \\")
        print(f"           --min-value 0 --max-value NNN --min-coverage NN \\")
        print(f"           --out {args.out}")
        return

    cleaned = apply_rules(df, args.min_value, args.max_value, args.max_ratio,
                          drop_zeros=args.drop_zeros, min_coverage=args.min_coverage)
    summarise(df, cleaned)
    cleaned.to_csv(args.out, index=False)
    print(f"\n  Wrote {args.out}")
    print("\nNext:")
    print(f"    python step01_data_check.py --csv {args.out} --value-col PM2.5")
    print("    then step02_features.py on the same file.\n")


if __name__ == "__main__":
    main()
