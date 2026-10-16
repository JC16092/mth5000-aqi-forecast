"""
MTH5000 - GRU optimizer and learning-rate sensitivity check.

A follow-up to Dr Tian's 15 October email: "GRU is not always good,
depending on the choice of optimizer, learning rate, activation function
and the steps of data for prediction." The hidden-size/sequence-length
half of that was already checked (gru_hyperparam_sensitivity.py). This
checks the other half that is actually tunable for a GRU: optimizer
choice and learning rate. ("Activation function" is not a free parameter
here -- a GRU's gates are fixed sigmoid/tanh by the architecture's own
equations, already given in full in Methodology, not a configurable
choice the way a plain feed-forward layer's activation is.)

Same bounded design as the existing hyperparameter check, for the same
reason: single split, fit once on train, score once on validation
(step03_benchmarks.chronological_split), three seeds (0-2), base GRU
only, hidden and seq_len held at the report's defaults. This is a
sensitivity check, not a replacement for Table 4.1.

GRUForecaster's optimizer is a hardcoded torch.optim.Adam inside
_fit_one. Rather than edit step08_gru.py, this subclasses it the same
way arima_coefficient_stability.py subclassed Arima: the pipeline script
that produces the report's real numbers stays untouched, and the
subclass exists only here.

    python gru_optimizer_sensitivity.py
"""

import sys
import time
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series
    from step03_benchmarks import chronological_split, HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Naive, rolling_origin
    from step08_gru import build_channels, GRUForecaster, SEQ_LEN, make_sequences
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4, 5, 8 and evaluation.py beside this script. {e}")

SEEDS = [0, 1, 2]
DEFAULT_HIDDEN = 24
DEFAULT_LR = 0.01
LR_GRID = [0.003, 0.03]          # optimizer held at Adam (the default)
OPTIMIZER_GRID = ["sgd", "rmsprop"]  # lr held at the report's default


class ConfigurableGRU(GRUForecaster):
    """Identical to GRUForecaster, except _fit_one takes its optimizer
    class from self.optimizer_name instead of hardcoding Adam."""

    def __init__(self, *args, optimizer_name="adam", **kwargs):
        super().__init__(*args, **kwargs)
        self.optimizer_name = optimizer_name

    def _fit_one(self, X, y):
        import torch
        torch.manual_seed(self.seed)
        torch.set_num_threads(1)

        n_val = max(30, int(0.15 * len(y)))
        Xtr, ytr = X[:-n_val], y[:-n_val]
        Xva, yva = X[-n_val:], y[-n_val:]

        class Net(torch.nn.Module):
            def __init__(self, n_feat, hidden):
                super().__init__()
                self.gru = torch.nn.GRU(n_feat, hidden, batch_first=True)
                self.out = torch.nn.Linear(hidden, 1)

            def forward(self, x):
                h, _ = self.gru(x)
                return self.out(h[:, -1])

        net = Net(X.shape[2], self.hidden)
        if self.optimizer_name == "sgd":
            opt = torch.optim.SGD(net.parameters(), lr=self.lr, momentum=0.9)
        elif self.optimizer_name == "rmsprop":
            opt = torch.optim.RMSprop(net.parameters(), lr=self.lr)
        else:
            opt = torch.optim.Adam(net.parameters(), lr=self.lr)
        loss_fn = torch.nn.L1Loss()

        Xtr_t = torch.tensor(Xtr, dtype=torch.float32)
        ytr_t = torch.tensor(ytr, dtype=torch.float32).view(-1, 1)
        Xva_t = torch.tensor(Xva, dtype=torch.float32)
        yva_t = torch.tensor(yva, dtype=torch.float32).view(-1, 1)

        best_state, best_loss, since = None, np.inf, 0
        for _ in range(self.epochs):
            net.train()
            perm = torch.randperm(len(ytr_t))
            for i in range(0, len(perm), 128):
                b = perm[i:i + 128]
                opt.zero_grad()
                loss_fn(net(Xtr_t[b]), ytr_t[b]).backward()
                opt.step()
            net.eval()
            with torch.no_grad():
                v = float(loss_fn(net(Xva_t), yva_t))
            if v < best_loss - 1e-5:
                best_loss, since = v, 0
                best_state = {k: t.clone() for k, t in net.state_dict().items()}
            else:
                since += 1
                if since >= self.patience:
                    break
        if best_state is not None:
            net.load_state_dict(best_state)
        net.eval()
        return net


def run_one(series, channels, exog, train_idx, val_idx, optimizer_name, lr, seed):
    first, last = train_idx[-1], val_idx[-1]
    models = [Naive(),
              ConfigurableGRU(series, channels, name="gru", hidden=DEFAULT_HIDDEN,
                              seq_len=SEQ_LEN, lr=lr, optimizer_name=optimizer_name,
                              seed=seed)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
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
    print("  Single split, fit once on train, scored once on val -- the same "
          "bounded design as the hidden-size/seq-len check. hidden=24, "
          "seq_len=30 held fixed; only optimizer and learning rate vary.\n")

    combos = ([("adam", DEFAULT_LR, "default")]
             + [("adam", lr, "lr") for lr in LR_GRID]
             + [(opt, DEFAULT_LR, "optimizer") for opt in OPTIMIZER_GRID])

    rows = []
    t0 = time.time()
    for optimizer_name, lr, sweep in combos:
        for seed in SEEDS:
            m = run_one(s, channels, exog, train_idx, val_idx, optimizer_name, lr, seed)
            for h in HORIZONS:
                if h in m.index:
                    rows.append({"sweep": sweep, "optimizer": optimizer_name, "lr": lr,
                                 "seed": seed, "horizon": h,
                                 "rMAE": float(m.loc[h, "rMAE"]),
                                 "MAE": float(m.loc[h, "MAE"]),
                                 "n": int(m.loc[h, "n"])})
            print(f"  optimizer={optimizer_name:<8} lr={lr:<6} seed={seed}  "
                  f"({time.time() - t0:6.1f}s elapsed)")
            sys.stdout.flush()

    out = pd.DataFrame(rows)
    out.to_csv("gru_optimizer_sensitivity.csv", index=False)
    print(f"\n  Wrote gru_optimizer_sensitivity.csv ({len(out)} rows).")

    print("\n" + "=" * 72)
    print("SUMMARY: mean rMAE across seeds 0-2, by horizon")
    print("=" * 72)
    summary = (out.groupby(["sweep", "optimizer", "lr", "horizon"])["rMAE"]
               .agg(["mean", "min", "max"]).reset_index()
               .sort_values(["horizon", "sweep", "optimizer", "lr"]))
    for h in HORIZONS:
        print(f"\n  h={h}")
        for _, r in summary[summary["horizon"] == h].iterrows():
            print(f"    optimizer={r['optimizer']:<8} lr={r['lr']:<6}  "
                  f"({r['sweep']:<9})  mean {r['mean']:.4f}  "
                  f"range [{r['min']:.4f}, {r['max']:.4f}]")

    default_mean = (out[out.sweep == "default"].groupby("horizon")["rMAE"].mean())
    print("\n  Default (Adam, lr=0.01) mean rMAE: "
          + ", ".join(f"h={h} {default_mean.get(h, float('nan')):.4f}" for h in HORIZONS))
    print("  Compare every other row above against this one.")


if __name__ == "__main__":
    main()
