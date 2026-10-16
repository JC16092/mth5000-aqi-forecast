"""
MTH5000 - bounded check: a Kolmogorov-Arnold Network, as a KAN-LSTM
hybrid.

Dr Tian, 15 October: "I have no experience using the Kolmogorov-Arnold
network. It seems that standard KAN performs not very good for time
series, but the variant (such as the mixture with LSTM) performs
excellently." This builds exactly that hybrid: an LSTM backbone handles
the sequence (so the recurrence that already works for this series is
kept), and the final linear readout, torch.nn.Linear(hidden, 1) in
LSTMForecaster (step09_lstm.py), is replaced by a KANLinear layer
(kan_layer.py) -- a learnable function per edge instead of a fixed
weight, exactly the KAN construction, used here as a readout head
rather than throughout the network.

No established, maintained library exists for this the way torch.nn.LSTM
exists for the recurrent part, and Dr Tian stated directly he has no
experience with the method. Both of those are exactly why this is run
as a bounded, single-split, three-seed check (the same pattern already
used for the hyperparameter, Fourier, optimizer and transformer checks),
not committed to a full ten-seed Table 4.1 treatment before there is any
evidence it trains stably at all.

    python kan_lstm_bounded_check.py
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
    from step05_rolling import Forecaster, Naive, rolling_origin
    from step08_gru import build_channels, make_sequences, SEQ_LEN
    from kan_layer import KANLinear
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4, 5, 8, kan_layer.py and evaluation.py beside this script. {e}")

SEEDS = [0, 1, 2]


class KANLSTMForecaster(Forecaster):
    """LSTM backbone, KANLinear readout in place of the plain linear
    head every other recurrent model in this project uses."""

    def __init__(self, series, channels, name="kan_lstm", seq_len=SEQ_LEN, hidden=24,
                 epochs=60, lr=0.01, min_train=600, patience=8, seed=0,
                 kan_grid_size=5, kan_spline_order=3):
        self.name = name
        self.series = series
        self.channels = channels
        self.seq_len = seq_len
        self.hidden = hidden
        self.epochs = epochs
        self.lr = lr
        self.min_train = min_train
        self.patience = patience
        self.seed = seed
        self.kan_grid_size = kan_grid_size
        self.kan_spline_order = kan_spline_order
        self.models, self.scalers = {}, {}
        self.origin = None

    def _fit_one(self, X, y):
        import torch
        torch.manual_seed(self.seed)
        torch.set_num_threads(1)

        n_val = max(30, int(0.15 * len(y)))
        Xtr, ytr = X[:-n_val], y[:-n_val]
        Xva, yva = X[-n_val:], y[-n_val:]

        hidden = self.hidden
        grid_size, spline_order = self.kan_grid_size, self.kan_spline_order

        class Net(torch.nn.Module):
            def __init__(self, n_feat, hidden):
                super().__init__()
                self.lstm = torch.nn.LSTM(n_feat, hidden, batch_first=True)
                self.out = KANLinear(hidden, 1, grid_size=grid_size,
                                     spline_order=spline_order)

            def forward(self, x):
                h, _ = self.lstm(x)
                return self.out(h[:, -1])

        net = Net(X.shape[2], hidden)
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
                pred = net(Xtr_t[b])
                if not torch.isfinite(pred).all():
                    # A spline layer can diverge if the input leaves the
                    # fixed grid range; fail loudly rather than silently
                    # emit NaN forecasts the harness would mistake for
                    # missing data.
                    raise RuntimeError("KAN-LSTM produced a non-finite "
                                       "prediction during training")
                loss_fn(pred, ytr_t[b]).backward()
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
              KANLSTMForecaster(series, channels, name="kan_lstm", seed=seed)]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fc = rolling_origin(series, exog, models, first, last,
                            refit_every=10 ** 7, verbose=False)
    fc = fc[fc["origin"].isin(val_idx)]
    common = ev.restrict_to_common(fc, verbose=False)
    scale = ev.mase_scale(series.loc[train_idx].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    return metrics[metrics["model"] == "kan_lstm"].set_index("horizon")


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
    print("  Bounded check: single split, 3 seeds, LSTM backbone with a "
          "KANLinear readout in place of the usual linear head. Not a "
          "Table 4.1 candidate; this checks whether the hybrid trains "
          "stably and is competitive at all before any larger commitment.\n")

    rows, failures = [], []
    t0 = time.time()
    for seed in SEEDS:
        try:
            m = run_one(s, channels, exog, train_idx, val_idx, seed)
        except RuntimeError as e:
            print(f"  seed={seed}  FAILED: {e}")
            failures.append(seed)
            continue
        for h in HORIZONS:
            if h in m.index:
                rows.append({"seed": seed, "horizon": h,
                             "rMAE": float(m.loc[h, "rMAE"]),
                             "MAE": float(m.loc[h, "MAE"]),
                             "n": int(m.loc[h, "n"])})
        print(f"  seed={seed}  ({time.time() - t0:6.1f}s elapsed)")
        sys.stdout.flush()

    out = pd.DataFrame(rows)
    out.to_csv("kan_lstm_bounded_check.csv", index=False)
    print(f"\n  Wrote kan_lstm_bounded_check.csv ({len(out)} rows). "
          f"{len(failures)} of {len(SEEDS)} seeds failed to train stably.")

    if not out.empty:
        print("\n" + "=" * 72)
        print("SUMMARY: mean rMAE across seeds, by horizon (1.000 = naive)")
        print("=" * 72)
        summary = out.groupby("horizon")["rMAE"].agg(["mean", "min", "max", "count"])
        for h in HORIZONS:
            if h in summary.index:
                r = summary.loc[h]
                print(f"  h={h}  kan-lstm mean {r['mean']:.4f}  "
                      f"range [{r['min']:.4f}, {r['max']:.4f}]  "
                      f"({int(r['count'])} seeds)")


if __name__ == "__main__":
    main()
