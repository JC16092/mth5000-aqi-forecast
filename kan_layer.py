"""
A compact Kolmogorov-Arnold Network linear layer, in the "efficient-kan"
style: a learnable function per input-output edge, represented as a
base path (SiLU) plus a B-spline correction on a fixed grid, rather than
the original KAN paper's own slower sparse-grid-extension implementation
(the pip-installable `pykan` package). This project has no prior KAN
code and Dr Tian stated directly he has no experience with the method
either, so this is built from the published construction and checked
against first principles below, not copied from an unverified source.

Per-edge function: phi(x) = w_base * silu(x) + w_spline . B(x), where
B(x) is the vector of B-spline basis values at x on a fixed grid, order
`k` (cubic by default, matching the original KAN paper). A KANLinear
layer sums these edge functions over all input dimensions for each
output dimension, which is what makes it a *linear layer replacement*:
same (in_features, out_features) shape contract as torch.nn.Linear, a
different function living on each edge instead of a fixed weight.

    python kan_layer.py          # runs the self-test
"""

import torch
import torch.nn as nn


class KANLinear(nn.Module):
    def __init__(self, in_features, out_features, grid_size=5, spline_order=3,
                 grid_range=(-2.0, 2.0)):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.grid_size = grid_size
        self.spline_order = spline_order

        h = (grid_range[1] - grid_range[0]) / grid_size
        # Extend the grid by spline_order knots on each side, required by
        # the Cox-de Boor recursion to define a basis function all the way
        # to the domain's own edges.
        grid = (torch.arange(-spline_order, grid_size + spline_order + 1) * h
               + grid_range[0])
        self.register_buffer("grid", grid.expand(in_features, -1).contiguous())

        self.base_weight = nn.Parameter(torch.empty(out_features, in_features))
        self.spline_weight = nn.Parameter(
            torch.empty(out_features, in_features, grid_size + spline_order))

        nn.init.kaiming_uniform_(self.base_weight, a=5 ** 0.5)
        with torch.no_grad():
            noise = (torch.rand(grid_size + 1, in_features, out_features) - 0.5) * 0.1
            # _curve_to_coeff already returns (out_features, in_features,
            # basis), the exact shape spline_weight needs -- no further
            # permute here.
            self.spline_weight.data.copy_(
                self._curve_to_coeff(self.grid.T[spline_order:-spline_order], noise))

    def _b_splines(self, x):
        """x: (batch, in_features). Returns (batch, in_features,
        grid_size + spline_order) B-spline basis values via the standard
        Cox-de Boor recursion, order spline_order, on self.grid."""
        grid = self.grid  # (in_features, grid_size + 2*spline_order + 1)
        x = x.unsqueeze(-1)
        bases = ((x >= grid[:, :-1]) & (x < grid[:, 1:])).to(x.dtype)
        for p in range(1, self.spline_order + 1):
            left = (x - grid[:, :-(p + 1)]) / (grid[:, p:-1] - grid[:, :-(p + 1)])
            right = (grid[:, p + 1:] - x) / (grid[:, p + 1:] - grid[:, 1:-p])
            bases = left * bases[:, :, :-1] + right * bases[:, :, 1:]
        return bases  # (batch, in_features, grid_size + spline_order)

    def _curve_to_coeff(self, x, y):
        """Least-squares fit of spline coefficients to (x, y) samples,
        used only to initialise spline_weight away from exactly zero.
        x: (samples, in_features). y: (samples, in_features, out_features)."""
        A = self._b_splines(x).transpose(0, 1)          # (in, samples, basis)
        Bt = y.transpose(0, 1)                          # (in, samples, out)
        sol = torch.linalg.lstsq(A, Bt).solution         # (in, basis, out)
        return sol.permute(2, 0, 1)                      # (out, in, basis)

    def forward(self, x):
        base = torch.nn.functional.linear(torch.nn.functional.silu(x), self.base_weight)
        bs = self._b_splines(x)                          # (batch, in, basis)
        spline = torch.einsum("bik,oik->bo", bs, self.spline_weight)
        return base + spline


def _self_test():
    torch.manual_seed(0)
    layer = KANLinear(4, 3)
    x = torch.randn(16, 4)
    y = layer(x)
    assert y.shape == (16, 3), f"bad output shape {y.shape}"
    assert torch.isfinite(y).all(), "non-finite output from a fresh layer"

    # Gradients must reach both the base and the spline path, or the
    # spline half of the layer is dead weight contributing nothing.
    target = torch.randn(16, 3)
    loss = torch.nn.functional.mse_loss(y, target)
    loss.backward()
    assert layer.base_weight.grad is not None and layer.base_weight.grad.abs().sum() > 0, \
        "no gradient reached base_weight"
    assert layer.spline_weight.grad is not None and layer.spline_weight.grad.abs().sum() > 0, \
        "no gradient reached spline_weight"

    # A few optimisation steps on a deliberately nonlinear target should
    # reduce the loss; this is the actual thing a KAN layer is for.
    layer2 = KANLinear(1, 1, grid_size=8)
    opt = torch.optim.Adam(layer2.parameters(), lr=0.05)
    xs = torch.linspace(-1.5, 1.5, 200).unsqueeze(1)
    ys = torch.sin(3 * xs)
    losses = []
    for _ in range(300):
        opt.zero_grad()
        pred = layer2(xs)
        l = torch.nn.functional.mse_loss(pred, ys)
        l.backward()
        opt.step()
        losses.append(l.item())
    assert losses[-1] < losses[0] * 0.1, (
        f"a single KAN edge did not learn sin(3x): {losses[0]:.4f} -> {losses[-1]:.4f}")

    print("  KANLinear self-test: PASSED")
    print(f"    sin(3x) fit: loss {losses[0]:.4f} -> {losses[-1]:.4f} over 300 steps")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if _self_test() else 1)
