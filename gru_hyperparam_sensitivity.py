"""
MTH5000 - GRU hyperparameter sensitivity check.

A follow-up to a specific finding from a PhD-scholar review of the report
(2026-10-03): every other model family gets an explicit account of how its
hyperparameters were chosen (ARIMA's order by an AIC grid search, ridge's
lambda by cross-validation at every refit, the tree models' capacity by a
small grid scored on a held-out slice), but the GRU's own architecture,
H=24 hidden units and a 30-day window, is a fixed constructor default in
step08_gru.py with no stated selection procedure. This script checks
whether that choice was lucky rather than arbitrary.

Deliberately bounded rather than a full redo of the ten-seed rolling-origin
evaluation: fits once on the training block and scores once on the
validation block (step03_benchmarks.chronological_split), the same
single-split pattern step04_arima.py originally used for its own order
search, rather than refitting every 90 days across 2,303 origins. Three
seeds per setting (0, 1, 2 -- a subset of the ten used everywhere else in
this report, not a new convention), varying hidden size and sequence length
one at a time around the report's own defaults. The base (no-weather) GRU
only: the architecture hyperparameters are not expected to interact with
the weather channels differently, and halving the scope keeps this a
bounded check rather than a second full study.

Scored by evaluation.py like every other number in this project, never by
a parallel metric computed here.

    python gru_hyperparam_sensitivity.py
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
DEFAULT_HIDDEN = 24
DEFAULT_SEQLEN = SEQ_LEN  # 30
HIDDEN_GRID = [12, 48]       # seq_len held at the report's default
SEQLEN_GRID = [15, 45, 60]  # hidden held at the report's default


def run_one(series, channels, exog, train_idx, val_idx, hidden, seq_len, seed):
    """Fit once on train_idx, score once on val_idx. No refitting in between."""
    first, last = train_idx[-1], val_idx[-1]
    models = [Naive(),
              GRUForecaster(series, channels, name="gru", hidden=hidden,
                            seq_len=seq_len, seed=seed)]
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
    channels = build_channels(s, exog, weather=None, seq_fourier=2)

    train_idx, val_idx, test_idx = chronological_split(s.index)
    print(f"  train {train_idx[0].date()} to {train_idx[-1].date()} "
          f"({len(train_idx)} days)")
    print(f"  val   {val_idx[0].date()} to {val_idx[-1].date()} "
          f"({len(val_idx)} days)")
    print("  Single split, fit once on train, scored once on val. Not the full "
          "rolling-origin harness: this is a bounded sensitivity check, not a "
          "replacement for Table 4.1.\n")

    combos = ([(DEFAULT_HIDDEN, DEFAULT_SEQLEN, "default")]
             + [(h, DEFAULT_SEQLEN, "hidden") for h in HIDDEN_GRID]
             + [(DEFAULT_HIDDEN, l, "seq_len") for l in SEQLEN_GRID])

    rows = []
    t0 = time.time()
    for hidden, seq_len, sweep in combos:
        for seed in SEEDS:
            m = run_one(s, channels, exog, train_idx, val_idx, hidden, seq_len, seed)
            for h in HORIZONS:
                if h in m.index:
                    rows.append({"sweep": sweep, "hidden": hidden, "seq_len": seq_len,
                                 "seed": seed, "horizon": h,
                                 "rMAE": float(m.loc[h, "rMAE"]),
                                 "MAE": float(m.loc[h, "MAE"]),
                                 "n": int(m.loc[h, "n"])})
            print(f"  hidden={hidden:>3} seq_len={seq_len:>3} seed={seed}  "
                  f"({time.time() - t0:6.1f}s elapsed)")
            sys.stdout.flush()

    out = pd.DataFrame(rows)
    out.to_csv("gru_hyperparam_sensitivity.csv", index=False)
    print(f"\n  Wrote gru_hyperparam_sensitivity.csv ({len(out)} rows).")

    print("\n" + "=" * 72)
    print("SUMMARY: mean rMAE across seeds 0-2, by horizon")
    print("=" * 72)
    summary = (out.groupby(["sweep", "hidden", "seq_len", "horizon"])["rMAE"]
               .agg(["mean", "min", "max"]).reset_index()
               .sort_values(["horizon", "sweep", "hidden", "seq_len"]))
    for h in HORIZONS:
        print(f"\n  h={h}")
        for _, r in summary[summary["horizon"] == h].iterrows():
            print(f"    hidden={int(r['hidden']):>3} seq_len={int(r['seq_len']):>3}  "
                  f"({r['sweep']:<8})  mean {r['mean']:.4f}  "
                  f"range [{r['min']:.4f}, {r['max']:.4f}]")

    default_mean = (out[out.sweep == "default"].groupby("horizon")["rMAE"].mean())
    print("\n  Default (hidden=24, seq_len=30) mean rMAE: "
          + ", ".join(f"h={h} {default_mean.get(h, float('nan')):.4f}" for h in HORIZONS))
    print("  Compare every other row above against this one.")


if __name__ == "__main__":
    main()
