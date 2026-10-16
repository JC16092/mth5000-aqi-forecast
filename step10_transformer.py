"""
MTH5000 - Step 10: the transformer, promoted from a bounded check to the
full treatment, after Dr Tian's reply to the second-review response PDF
(16 October): the small-data argument against it does not hold in his
view -- "the datasets (4000 daily data) is large enough for transformer
... it suggests using transformer if the sample size is above 200" -- so
"no worries about the results," but it should actually be tested rather
than argued around.

transformer_bounded_check.py already answered the single-split, 3-seed
question of whether a transformer is worth the full treatment at all, and
found it unexpectedly competitive with the GRU. This script does not
redesign that architecture; it takes the exact same TransformerForecaster
(d_model=16, 2 heads, 1 layer, sinusoidal positional encoding, lr=0.001)
through the identical full ten-seed rolling-origin harness the GRU and
LSTM already went through, which is the same lift step09_lstm.py was: new
pipeline step, same channels, same windowing, same leak test, same
early-stopped training loop, the recurrent cell (or here, the encoder)
swapped in.

    python step10_transformer.py --test
    python step10_transformer.py --csv data/delhi_clean.csv --seed 0 \
           --out transformer_seed0.csv
"""

import argparse
import math
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step03_benchmarks import HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Forecaster, Naive, rolling_origin
    from step08_gru import build_channels, make_sequences, SEQ_LEN
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1, 3, 4, 5, 8 and evaluation.py beside this script. {e}")


class TransformerForecaster(Forecaster):
    """Identical to the architecture in transformer_bounded_check.py: a
    small encoder-only transformer over the same 30 day channel window the
    GRU and LSTM use, sinusoidal positional encoding since the model has
    no inherent sense of order, output taken from the last position the
    same way h[:, -1] is read from the recurrent models. Not re-tuned here
    -- this script changes the evaluation, not the architecture."""

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


# ----------------------------------------------------------------------------

def test_transformer(verbose=True):
    """Same battery as test_lstm in step09_lstm.py: the one check that
    matters is a leak test through the full harness, since the channel and
    windowing code is already tested by step08_gru.py's own suite."""
    ok = True

    def check(cond, msg):
        nonlocal ok
        if not cond:
            print(f"  FAIL: {msg}")
            ok = False

    n = 900
    idx = pd.date_range("2019-01-01", periods=n, freq="D")
    rng = np.random.default_rng(0)
    t = np.arange(n)
    s = pd.Series(np.clip(80 + 40 * np.cos(2 * np.pi * (t - 15) / 365.25)
                          + rng.normal(0, 10, n), 5, None), index=idx, name="PM2.5")
    s.iloc[rng.choice(n, 40, replace=False)] = np.nan
    ext = idx.append(pd.date_range(idx[-1] + pd.Timedelta(days=1), periods=3, freq="D"))
    exog = fourier_terms(ext, K=2)
    ch = build_channels(s, exog)

    try:
        import torch  # noqa: F401
    except ImportError:
        if verbose:
            print("  torch not installed: transformer not exercised.")
        return ok

    def build(series_, channels_):
        return [Naive(), TransformerForecaster(series_, channels_, min_train=120,
                                               epochs=4, d_model=8, nhead=2, layers=1)]

    first, last = idx[700], idx[730]
    base = rolling_origin(s, exog, build(s, ch), first, last, refit_every=20, verbose=False)
    check(base[base.model == "transformer"]["y_pred"].notna().sum() > 0,
          "the transformer produced no forecasts through the harness")

    cutd = idx[715]
    s3 = s.copy(); s3.loc[cutd:] = s3.loc[cutd:] * 8 + 400
    ch3 = build_channels(s3, exog)
    after = rolling_origin(s3, exog, build(s3, ch3), first, last,
                           refit_every=20, verbose=False)
    key = ["origin", "horizon", "model"]
    a = base[base.origin < cutd].set_index(key)["y_pred"].sort_index()
    b = after[after.origin < cutd].set_index(key)["y_pred"].sort_index()
    check(a.index.equals(b.index), "the corrupted run produced a different set of rows")
    if a.index.equals(b.index):
        diff = ~np.isclose(a.values.astype(float), b.values.astype(float),
                           rtol=1e-6, atol=1e-6, equal_nan=True)
        bad = sorted(set(a.index[diff].get_level_values("model"))) if diff.any() else []
        check(not diff.any(),
              f"LEAK: {int(diff.sum())} forecasts before the cut changed. {bad}")

    if verbose:
        print("  Transformer checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(
        description="Transformer, rolling origin, same harness as the GRU and LSTM.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--features", default="features.csv")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--refit-every", type=int, default=180)
    ap.add_argument("--burn-in", type=int, default=1095)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--d-model", type=int, default=16)
    ap.add_argument("--nhead", type=int, default=2)
    ap.add_argument("--layers", type=int, default=1)
    ap.add_argument("--lr", type=float, default=0.001)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--existing", default="forecasts_with_lstm.csv")
    ap.add_argument("--out", default="forecasts_with_transformer.csv")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if (ev.test_evaluation() and test_transformer()) else 1)

    print("\nRunning checks before fitting anything.")
    if not (ev.test_evaluation() and test_transformer()):
        sys.exit("Checks failed.")

    s = load_series(args.csv, "date", "PM2.5")
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=args.fourier)
    ch = build_channels(s, exog, weather=None, seq_fourier=2)

    first, last = s.index[args.burn_in], s.index[-max(HORIZONS) - 1]
    models = [TransformerForecaster(s, ch, name="transformer", epochs=args.epochs,
                                    d_model=args.d_model, nhead=args.nhead,
                                    layers=args.layers, lr=args.lr, seed=args.seed)]

    print("\n" + "=" * 72)
    print("TRANSFORMER, ROLLING ORIGIN")
    print("=" * 72)
    print(f"  origins {first.date()} to {last.date()}, refit every {args.refit_every} days")
    print(f"  sequence length {SEQ_LEN} days, d_model {args.d_model}, "
          f"heads {args.nhead}, layers {args.layers}, seed {args.seed}")

    tr = rolling_origin(s, exog, models, first, last, refit_every=args.refit_every)

    existing = pd.read_csv(args.existing, parse_dates=["origin"])
    both = pd.concat([existing, tr], ignore_index=True)
    ev.check_forecasts(both)

    common = ev.restrict_to_common(both)
    scale = ev.mase_scale(s.loc[:first].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    ev.print_regression(metrics, title="FORECAST ACCURACY, ROLLING ORIGIN")

    common.to_csv(args.out, index=False)
    print(f"\n  Wrote {args.out} ({len(common)} rows, {common['model'].nunique()} models).")


if __name__ == "__main__":
    main()
