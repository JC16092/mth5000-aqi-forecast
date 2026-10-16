"""
MTH5000 - bounded check: does a Transformer compete on this series?

A follow-up to Dr Tian's 15 October email: "if you hope to improve, you
may try LSTM if the data size is not large enough. If the size is large,
you may try the transformer." That is a conditional, not a flat
recommendation, and the condition for the transformer half does not
hold here: this series is about 3,093 daily observations, which is
small for a self-attention model, not large. Literature Review already
makes this exact argument for why a GRU was chosen over a transformer in
the first place (parameter count assumes a dataset orders of magnitude
bigger than this one). This script tests that argument directly rather
than leaving it as a citation-backed claim alone, at the risk the user
explicitly accepted.

BOUNDED BY DESIGN, not a Table-4.1-grade addition. Same single-split,
three-seed pattern already used for the hyperparameter and Fourier
checks: fit once on the training block, score once on validation
(step03_benchmarks.chronological_split), rather than the full ten-seed
rolling-origin harness. A small transformer encoder has more to tune
than a GRU or LSTM does (model width, number of layers, number of
heads, positional encoding), and committing to a full production
evaluation of an architecture this project expects to underperform,
for the reason already given above, is not a good use of the time
remaining before submission. If this bounded check shows something
surprising, it would be the trigger for a full evaluation, not this
script itself.

    python transformer_bounded_check.py
"""

import math
import sys
import time
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series
    from step03_benchmarks import chronological_split, HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Forecaster, Naive, rolling_origin
    from step08_gru import build_channels, make_sequences, SEQ_LEN
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4, 5, 8 and evaluation.py beside this script. {e}")

SEEDS = [0, 1, 2]


class TransformerForecaster(Forecaster):
    """A small transformer encoder over the same 30-day channel window
    the GRU and LSTM use. Sinusoidal positional encoding, since the
    model has no inherent sense of order the way a recurrent cell does.
    Output taken from the last position's representation, same
    convention as h[:, -1] in the recurrent models."""

    def __init__(self, series, channels, name="transformer", seq_len=SEQ_LEN,
                 d_model=16, nhead=2, layers=1, epochs=60, lr=0.001,
                 min_train=600, patience=8, seed=0):
        self.name = name
        self.series = series
        self.channels = channels
        self.seq_len = seq_len
        self.d_model = d_model
        self.nhead = nhead
        self.layers = layers
        self.epochs = epochs
        self.lr = lr
        self.min_train = min_train
        self.patience = patience
        self.seed = seed
        self.models, self.scalers = {}, {}
        self.origin = None

    def _fit_one(self, X, y):
        import torch
        torch.manual_seed(self.seed)
        torch.set_num_threads(1)

        n_val = max(30, int(0.15 * len(y)))
        Xtr, ytr = X[:-n_val], y[:-n_val]
        Xva, yva = X[-n_val:], y[-n_val:]

        seq_len, d_model = self.seq_len, self.d_model

        class Net(torch.nn.Module):
            def __init__(self, n_feat, d_model, nhead, layers, seq_len):
                super().__init__()
                self.proj = torch.nn.Linear(n_feat, d_model)
                pe = torch.zeros(seq_len, d_model)
                pos = torch.arange(0, seq_len).unsqueeze(1).float()
                div = torch.exp(torch.arange(0, d_model, 2).float()
                                * (-math.log(10000.0) / d_model))
                pe[:, 0::2] = torch.sin(pos * div)
                pe[:, 1::2] = torch.cos(pos * div[:pe[:, 1::2].shape[1]])
                self.register_buffer("pe", pe.unsqueeze(0))
                enc_layer = torch.nn.TransformerEncoderLayer(
                    d_model=d_model, nhead=nhead, dim_feedforward=4 * d_model,
                    batch_first=True)
                self.encoder = torch.nn.TransformerEncoder(enc_layer, num_layers=layers)
                self.out = torch.nn.Linear(d_model, 1)

            def forward(self, x):
                z = self.proj(x) + self.pe
                z = self.encoder(z)
                return self.out(z[:, -1])

        net = Net(X.shape[2], d_model, self.nhead, self.layers, seq_len)
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

    def start(self, y_hist, exog_hist):
        self.origin = y_hist.index[-1]
        self.models, self.scalers = {}, {}
        for h in HORIZONS:
            cutoff = self.origin - pd.Timedelta(days=h)
            train_days = y_hist.index[y_hist.index <= cutoff]
            X, days = make_sequences(self.channels, train_days, self.seq_len)
            if len(days) < self.min_train:
                continue
            target = np.log(self.series.reindex(days + pd.Timedelta(days=h)).values)
            anchor = self.channels.loc[days, "log"].values
            y = target - anchor
            ok = np.isfinite(y)
            if ok.sum() < self.min_train:
                continue
            X, y = X[ok], y[ok]
            mu = X.reshape(-1, X.shape[2]).mean(axis=0)
            sd = X.reshape(-1, X.shape[2]).std(axis=0)
            sd[sd < 1e-8] = 1.0
            self.scalers[h] = (mu, sd)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.models[h] = self._fit_one((X - mu) / sd, y)

    def update(self, day, y_value, exog_row):
        self.origin = day

    def predict(self, horizons, future_exog):
        import torch
        out = {}
        X, days = make_sequences(self.channels, [self.origin], self.seq_len)
        for h in horizons:
            net = self.models.get(h)
            if net is None or len(days) == 0:
                out[h] = np.nan
                continue
            mu, sd = self.scalers[h]
            with torch.no_grad():
                d = float(net(torch.tensor((X - mu) / sd, dtype=torch.float32))[0, 0])
            anchor = self.channels.loc[self.origin, "log"]
            out[h] = float(np.exp(anchor + d)) if np.isfinite(anchor) else np.nan
        return out


def run_one(series, channels, exog, train_idx, val_idx, seed):
    first, last = train_idx[-1], val_idx[-1]
    models = [Naive(),
              TransformerForecaster(series, channels, name="transformer", seed=seed)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fc = rolling_origin(series, exog, models, first, last,
                            refit_every=10 ** 7, verbose=False)
    fc = fc[fc["origin"].isin(val_idx)]
    common = ev.restrict_to_common(fc, verbose=False)
    scale = ev.mase_scale(series.loc[train_idx].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    return metrics[metrics["model"] == "transformer"].set_index("horizon")


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
    print("  Bounded check: single split, 3 seeds, small transformer encoder "
          "(d_model=16, 2 heads, 1 layer). Not a Table 4.1 candidate; this "
          "tests whether the small-data argument against a transformer, "
          "already made in Literature Review, actually holds here.\n")

    rows = []
    t0 = time.time()
    for seed in SEEDS:
        m = run_one(s, channels, exog, train_idx, val_idx, seed)
        for h in HORIZONS:
            if h in m.index:
                rows.append({"seed": seed, "horizon": h,
                             "rMAE": float(m.loc[h, "rMAE"]),
                             "MAE": float(m.loc[h, "MAE"]),
                             "n": int(m.loc[h, "n"])})
        print(f"  seed={seed}  ({time.time() - t0:6.1f}s elapsed)")
        sys.stdout.flush()

    out = pd.DataFrame(rows)
    out.to_csv("transformer_bounded_check.csv", index=False)
    print(f"\n  Wrote transformer_bounded_check.csv ({len(out)} rows).")

    print("\n" + "=" * 72)
    print("SUMMARY: mean rMAE across seeds 0-2, by horizon (ARIMA for reference)")
    print("=" * 72)
    summary = out.groupby("horizon")["rMAE"].agg(["mean", "min", "max"])
    for h in HORIZONS:
        if h in summary.index:
            r = summary.loc[h]
            print(f"  h={h}  transformer mean {r['mean']:.4f}  "
                  f"range [{r['min']:.4f}, {r['max']:.4f}]  (1.000 = naive)")


if __name__ == "__main__":
    main()
