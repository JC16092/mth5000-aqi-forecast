"""
MTH5000 - does the GRU's smaller Fourier set explain its loss at h=2/h=3?

A follow-up to a specific finding from a PhD-scholar review: Results and
Discussion explain the GRU losing to ARIMA at two and three days ahead as
"ARIMA carries the seasonal cycle explicitly via Fourier terms, the GRU has
to learn it from a short window" -- but Methodology states the GRU also
receives explicit Fourier terms, just K=2 harmonics against ARIMA's K=4
(Section 3.4.1). The mechanism story may be imprecise: the real contrast
could be harmonic count, not presence versus absence of seasonal input.
This checks that directly by refitting the GRU with K=4, holding every
other setting (H=24, 30-day window) at the report's own defaults, and
comparing to a freshly refit K=2 baseline under identical code and data
rather than reusing an older run.

Bounded in the same way as the earlier hyperparameter check: fits once on
the original training/validation split rather than redoing the full
ten-seed rolling-origin evaluation, three seeds (0-2), base GRU only (no
weather). Nothing in Table 4.1 is changed on the strength of this; it is a
diagnostic, not a resubmission of the main result.

    python gru_fourier_ablation.py
"""

import sys
import time

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series
    from step03_benchmarks import chronological_split, HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Naive, rolling_origin
    from step08_gru import build_channels, GRUForecaster, SEQ_LEN
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4, 5, 8 and evaluation.py beside this script. {e}")

SEEDS = [0, 1, 2]


def run_one(series, channels, exog, train_idx, val_idx, seed):
    first, last = train_idx[-1], val_idx[-1]
    models = [Naive(),
              GRUForecaster(series, channels, name="gru", hidden=24,
                            seq_len=SEQ_LEN, seed=seed)]
    fc = rolling_origin(series, exog, models, first, last,
                        refit_every=10 ** 7, verbose=False)
    fc = fc[fc["origin"].isin(val_idx)]
    common = ev.restrict_to_common(fc, verbose=False)
    scale = ev.mase_scale(series.loc[train_idx].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    return metrics[metrics["model"] == "gru"].set_index("horizon")


def main():
    s = load_series("data/delhi_clean.csv", "date", "PM2.5")
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=4)

    train_idx, val_idx, test_idx = chronological_split(s.index)
    print(f"  train {train_idx[0].date()} to {train_idx[-1].date()} "
          f"({len(train_idx)} days)")
    print(f"  val   {val_idx[0].date()} to {val_idx[-1].date()} "
          f"({len(val_idx)} days)")
    print("  Single split, fit once on train, scored once on val -- the "
          "same bounded design as the earlier hyperparameter check, H=24 "
          "and the 30-day window held fixed at the report's defaults; only "
          "the Fourier harmonic count varies.\n")

    rows = []
    t0 = time.time()
    for k, label in [(2, "K=2 (report default)"), (4, "K=4 (matches ARIMA)")]:
        channels = build_channels(s, exog, weather=None, seq_fourier=k)
        for seed in SEEDS:
            m = run_one(s, channels, exog, train_idx, val_idx, seed)
            for h in HORIZONS:
                if h in m.index:
                    rows.append({"fourier_k": k, "label": label, "seed": seed,
                                 "horizon": h, "rMAE": float(m.loc[h, "rMAE"]),
                                 "MAE": float(m.loc[h, "MAE"]),
                                 "n": int(m.loc[h, "n"])})
            print(f"  K={k} seed={seed}  ({time.time() - t0:6.1f}s elapsed)")
            sys.stdout.flush()

    out = pd.DataFrame(rows)
    out.to_csv("gru_fourier_ablation.csv", index=False)
    print(f"\n  Wrote gru_fourier_ablation.csv ({len(out)} rows).")

    print("\n" + "=" * 72)
    print("SUMMARY: mean rMAE across seeds 0-2, by horizon")
    print("=" * 72)
    summary = (out.groupby(["fourier_k", "horizon"])["rMAE"]
              .agg(["mean", "min", "max"]).reset_index())
    for h in HORIZONS:
        print(f"\n  h={h}")
        sub = summary[summary.horizon == h].sort_values("fourier_k")
        for _, r in sub.iterrows():
            print(f"    K={int(r['fourier_k'])}  mean {r['mean']:.4f}  "
                  f"range [{r['min']:.4f}, {r['max']:.4f}]")
        k2 = sub[sub.fourier_k == 2]["mean"].iloc[0]
        k4 = sub[sub.fourier_k == 4]["mean"].iloc[0]
        print(f"    K=4 minus K=2: {k4 - k2:+.4f} ({(k4 - k2) * 100:+.2f} points "
              f"of relative error; negative means K=4 is better)")


if __name__ == "__main__":
    main()
