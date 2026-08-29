"""
MTH5000 - Step 8: the recurrent network, in the same harness.

    python step08_gru.py --test
    python step08_gru.py --csv data/delhi_clean.csv --features features.csv

WHY THIS EXISTS, GIVEN WHAT WEEK 5 SHOWED

The threshold sweep showed that every model already fitted lands within about five
points of hit rate at a fixed alarm budget, while the budget itself moves it by
fifty. So this network is not expected to change any conclusion. It is fitted
because the proposal named it, because the supervisor asked for machine learning
specifically, and because "we fitted a recurrent network and it did not beat
ARIMA" is a defensible sentence while "we did not fit one" is not.

WHAT IT SEES

A window of the last L days, each day carrying the logarithm of concentration, a
missingness flag, and the annual Fourier terms. This is a genuine sequence model
rather than a feed-forward network on lagged columns: the recurrence is the point,
and it is what the proposal promised.

THE IMPUTATION IT FORCES, WHICH IS ITSELF A RESULT

Every other model in this project handles missing days honestly. The state space
models skip the measurement update at a gap, and gradient boosting takes NaN
natively. A recurrent network can do neither: it must be handed a value at every
timestep. So gaps are filled by carrying the last observation forward, and a
separate channel tells the network which days were filled.

That is a real methodological cost of the method and it belongs in the discussion.
The architecture the supervisor asked for is the one architecture in the suite
that cannot represent "I do not know".

WHAT IS PREDICTED

The change in log concentration from the origin, with the origin value added back
afterwards. The same reframing helped the tree models in step 6, for the same
reason: it hands the network the persistence for free and asks it to model a
roughly stationary residual rather than to reproduce a level it cannot extrapolate.
"""

import argparse
import sys
import warnings

import numpy as np
import pandas as pd

try:
    from step01_data_check import load_series, HAZARD_THRESHOLD
    from step03_benchmarks import HORIZONS
    from step04_arima import fourier_terms
    from step05_rolling import Forecaster, Naive, Arima, Climatology, rolling_origin
    from step06_ml import load_features
    import evaluation as ev
except ImportError as e:
    sys.exit(f"Needs steps 1 to 6 and evaluation.py beside this script. {e}")

SEQ_LEN = 30


def build_channels(series, exog, seq_fourier=2):
    """One row per day: log value carried forward, a missing flag, Fourier terms."""
    log = np.log(series)
    filled = log.ffill()
    miss = series.isna().astype(float)
    cols = {"log": filled, "missing": miss}
    for k in range(1, seq_fourier + 1):
        cols[f"sin{k}"] = exog[f"ann_sin_{k}"].reindex(series.index)
        cols[f"cos{k}"] = exog[f"ann_cos_{k}"].reindex(series.index)
    ch = pd.DataFrame(cols, index=series.index)
    # A leading gap has nothing to carry forward. Back-filling only affects days
    # before the first observation, which no origin in this project reaches.
    return ch.bfill().fillna(0.0)


def make_sequences(channels, origins, seq_len=SEQ_LEN):
    """Stack the window ending at each origin. Nothing after the origin enters."""
    idx = channels.index
    pos = {d: i for i, d in enumerate(idx)}
    values = channels.values
    keep, out = [], []
    for t in origins:
        i = pos.get(t)
        if i is None or i + 1 < seq_len:
            continue
        out.append(values[i + 1 - seq_len: i + 1])
        keep.append(t)
    if not out:
        return np.empty((0, seq_len, values.shape[1])), pd.DatetimeIndex([])
    return np.stack(out), pd.DatetimeIndex(keep)


class GRUForecaster(Forecaster):
    """A small gated recurrent network, refitted on a slow cadence."""

    def __init__(self, series, channels, name="gru", seq_len=SEQ_LEN, hidden=24,
                 epochs=60, lr=0.01, min_train=600, patience=8, seed=0):
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
        self.models, self.scalers = {}, {}
        self.origin = None

    # -- the network itself, isolated so everything else is testable without torch
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
            # Early stopping on a chronological holdout inside the training
            # window, never on anything at or after the origin.
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
            y = target - anchor                      # change in log from the origin
            ok = np.isfinite(y)
            if ok.sum() < self.min_train:
                continue
            X, y = X[ok], y[ok]

            # Standardise using the training window only.
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

def test_gru(verbose=True):
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

    check(ch.notna().all().all(), "the channel table still contains NaN")
    check(set(ch.columns) == {"log", "missing", "sin1", "cos1", "sin2", "cos2"},
          f"unexpected channels: {list(ch.columns)}")
    check(abs(ch["missing"].sum() - 40) < 1e-9, "the missing flag lost some gaps")

    # A window must end at its origin and contain nothing after it.
    X, days = make_sequences(ch, idx[100:105])
    check(X.shape == (5, SEQ_LEN, 6), f"unexpected sequence shape {X.shape}")
    for j, d in enumerate(days):
        expected = ch.loc[d - pd.Timedelta(days=SEQ_LEN - 1): d].values
        check(np.allclose(X[j], expected), f"window for {d.date()} is misaligned")
        check(np.allclose(X[j][-1], ch.loc[d].values),
              f"window for {d.date()} does not end at the origin")

    # Corrupting the future must leave earlier windows untouched.
    cut = idx[300]
    s2 = s.copy(); s2.loc[cut:] = s2.loc[cut:] * 8 + 400
    ch2 = build_channels(s2, exog)
    Xa, _ = make_sequences(ch, idx[200:250])
    Xb, _ = make_sequences(ch2, idx[200:250])
    check(np.allclose(Xa, Xb), "a sequence changed when the future was corrupted")

    # The label cutoff must be the origin minus h.
    g = GRUForecaster(s, ch, min_train=100, epochs=3)
    origin = idx[600]
    for h in HORIZONS:
        cutoff = origin - pd.Timedelta(days=h)
        train_days = idx[idx <= origin]
        train_days = train_days[train_days <= cutoff]
        check(train_days.max() == cutoff,
              f"h={h}: training window ends at {train_days.max().date()}, "
              f"expected {cutoff.date()}")
        check(train_days.max() + pd.Timedelta(days=h) <= origin,
              f"h={h}: a training label lies after the origin")

    # End to end through the harness, with the same corruption test the harness
    # applies to every model.
    try:
        import torch  # noqa: F401
    except ImportError:
        if verbose:
            print("  torch not installed: sequence checks passed, network not exercised.")
        return ok

    def build(series_, channels_):
        return [Naive(), GRUForecaster(series_, channels_, min_train=120,
                                       epochs=4, hidden=8)]

    first, last = idx[700], idx[730]
    base = rolling_origin(s, exog, build(s, ch), first, last, refit_every=20, verbose=False)
    check(base[base.model == "gru"]["y_pred"].notna().sum() > 0,
          "the network produced no forecasts through the harness")

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
        print("  Recurrent network checks:", "PASSED" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Recurrent network, rolling origin.")
    ap.add_argument("--csv", default="data/delhi_clean.csv")
    ap.add_argument("--features", default="features.csv")
    ap.add_argument("--threshold", type=float, default=HAZARD_THRESHOLD)
    ap.add_argument("--fourier", type=int, default=4)
    ap.add_argument("--refit-every", type=int, default=180,
                    help="slower than the other models: each refit trains a network")
    ap.add_argument("--burn-in", type=int, default=1095)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--hidden", type=int, default=24)
    ap.add_argument("--seed", type=int, default=0,
                    help="network initialisation. Vary it: a single seed is not a result.")
    ap.add_argument("--existing", default="forecasts_all.csv")
    ap.add_argument("--out", default="forecasts_with_gru.csv")
    ap.add_argument("--test", action="store_true")
    args = ap.parse_args()

    if args.test:
        sys.exit(0 if (ev.test_evaluation() and test_gru()) else 1)

    print("\nRunning checks before fitting anything.")
    if not (ev.test_evaluation() and test_gru()):
        sys.exit("Checks failed.")

    s = load_series(args.csv, "date", "PM2.5")
    extended = s.index.append(pd.date_range(s.index[-1] + pd.Timedelta(days=1),
                                            periods=max(HORIZONS), freq="D"))
    exog = fourier_terms(extended, K=args.fourier)
    ch = build_channels(s, exog)

    first, last = s.index[args.burn_in], s.index[-max(HORIZONS) - 1]
    models = [GRUForecaster(s, ch, name="gru", epochs=args.epochs,
                            hidden=args.hidden, seed=args.seed)]

    print("\n" + "=" * 72)
    print("RECURRENT NETWORK, ROLLING ORIGIN")
    print("=" * 72)
    print(f"  origins {first.date()} to {last.date()}, refit every {args.refit_every} days")
    print(f"  sequence length {SEQ_LEN} days, hidden units {args.hidden}, "
          f"up to {args.epochs} epochs with early stopping")
    print("  Gaps are carried forward with a missingness channel: a recurrent")
    print("  network cannot skip a timestep the way the state space models can.")

    gru = rolling_origin(s, exog, models, first, last, refit_every=args.refit_every)

    existing = pd.read_csv(args.existing, parse_dates=["origin"])
    both = pd.concat([existing, gru], ignore_index=True)
    ev.check_forecasts(both)

    print("\n" + "=" * 72)
    print("SCORING AGAINST EVERY OTHER MODEL ON IDENTICAL DAYS")
    print("=" * 72)
    common = ev.restrict_to_common(both)
    scale = ev.mase_scale(s.loc[:first].values)
    metrics = ev.regression_metrics(common, scale, reference="naive_carry")
    ev.print_regression(metrics, title="FORECAST ACCURACY, ROLLING ORIGIN")
    warn = ev.evaluate_warnings(common, event_threshold=args.threshold)
    ev.print_warnings(warn, args.threshold)

    common.to_csv(args.out, index=False)
    print(f"\n  Wrote {args.out} ({len(common)} rows, {common['model'].nunique()} models).")

    for h in HORIZONS:
        sub = metrics[metrics.horizon == h].set_index("model")["rMAE"]
        if "gru" in sub.index:
            better = (sub < sub["gru"]).sum()
            print(f"  h={h}: the network places {better + 1} of {len(sub)} "
                  f"at rMAE {sub['gru']:.3f}")
    print("\n  Report where it placed, whether or not that is flattering.\n")


if __name__ == "__main__":
    main()
