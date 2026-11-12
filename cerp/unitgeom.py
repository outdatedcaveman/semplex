"""Per-threshold-function geometry for Spike 13 (abductive candidates A2, A4). UNTRUSTED.

For each 4-input threshold function t, as computed by a unit reading inputs in
{-1,+1} with a bias, i.e. sign(theta . z) with z = (x_s, 1) in R^5:

  margin_l2(t)   = 1 / min ||theta||_2   s.t. y_x theta . z_x >= 1 for all 16 x
  margin_linf(t) = 1 / min ||theta||_inf s.t. the same
  int_cost(t)    = min sum|w_i| + |T| over integer (w, T) with
                   [w . x >= T] = t on x in {0,1}^4   (threshold-logic weight size)

A2 (optimizer-geometry margins) says GD favours large l2 margins and Adam
(close to sign descent) large l_inf margins. A4 says small integer cost wins
regardless of the optimizer.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import LinearConstraint, linprog, milp, minimize

from cerp import train

Z = np.hstack([train.XS, np.ones((16, 1))])                      # (16, 5), inputs in {-1,+1} plus bias
X01 = train.X                                                    # (16, 4)


def _labels(t):
    return np.array([1.0 if (t >> x) & 1 else -1.0 for x in range(16)])


def margin_linf(t):
    y = _labels(t)
    # variables theta (5), s ; minimise s ; -y z theta <= -1 ; theta_i - s <= 0 ; -theta_i - s <= 0
    A = [np.append(-y[x] * Z[x], 0.0) for x in range(16)]
    for i in range(5):
        e = np.zeros(6); e[i], e[5] = 1, -1; A.append(e)
        e = np.zeros(6); e[i], e[5] = -1, -1; A.append(e)
    b = [-1.0] * 16 + [0.0] * 10
    r = linprog(np.eye(6)[5], A_ub=np.array(A), b_ub=b, bounds=[(None, None)] * 6, method="highs")
    assert r.status == 0, t
    return 1.0 / r.x[5]


def margin_l2(t):
    y = _labels(t)
    A = y[:, None] * Z
    # feasible start from the l_inf solution scaled up
    x0 = np.linalg.lstsq(A, np.ones(16) * 2, rcond=None)[0]
    if (A @ x0).min() < 1:
        r = linprog(np.zeros(5), A_ub=-A, b_ub=-np.ones(16), bounds=[(None, None)] * 5, method="highs")
        x0 = r.x
    r = minimize(lambda th: th @ th, x0, jac=lambda th: 2 * th, method="SLSQP",
                 constraints=[{"type": "ineq", "fun": lambda th: A @ th - 1, "jac": lambda th: A}],
                 options={"ftol": 1e-12, "maxiter": 500})
    assert r.success and (A @ r.x).min() > 1 - 1e-6, t
    return 1.0 / np.sqrt(r.x @ r.x)


def int_cost(t):
    """Exact minimum of sum|w_i| + |T| by MILP (w = wp - wn, T = Tp - Tn)."""
    y = np.array([(t >> x) & 1 for x in range(16)])
    # variables: wp(4) wn(4) Tp Tn, all >= 0 integer
    rows, lo, hi = [], [], []
    for x in range(16):
        r = np.concatenate([X01[x], -X01[x], [-1, 1]])
        rows.append(r)
        if y[x]:
            lo.append(0); hi.append(np.inf)            # w.x - T >= 0
        else:
            lo.append(-np.inf); hi.append(-1)          # w.x - T <= -1
    res = milp(c=np.ones(10), constraints=LinearConstraint(np.array(rows), lo, hi),
               integrality=np.ones(10), bounds=(0, 64))
    assert res.status == 0, t
    return int(round(res.fun))


def table(ltf_bits):
    """Geometry for every canonical (up to complement) non-constant threshold function."""
    full = 0xFFFF
    out = {}
    for b in sorted({int(min(b, full ^ b)) for b in ltf_bits} - {0}):
        out[b] = {"m2": margin_l2(b), "minf": margin_linf(b),
                  "int": min(int_cost(b), int_cost(full ^ b))}
    return out
