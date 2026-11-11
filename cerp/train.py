"""Train many tiny real-valued networks at once and read off their circuits (Spike 09). UNTRUSTED.

Network: 4 inputs -> H tanh units -> 1 logit, trained by full-batch AdamW on
binary cross-entropy over the task's care points.

Reading a circuit off a trained net. Each hidden unit induces a threshold
function of the inputs, [pre-activation >= 0]. The learned hidden layer is
then a set of "protocols" in the sense of THEORY.md, and we ask:
  g        the function the net computes on all 16 inputs (sign of the logit)
  faithful does the net still compute g when every tanh is replaced by a hard step?
  w_eff    the smallest number of learned units whose threshold functions
           DETERMINE g (minimum hitting set over the learned units)
  isomer   that minimal set, as threshold functions up to complement
w_eff is compared with w*(g), the minimum over ALL threshold functions.
"""

from __future__ import annotations

import itertools

import numpy as np

N = 4
X = np.array([[(i >> j) & 1 for j in range(N)] for i in range(1 << N)], dtype=np.float64)   # (16, 4)
XS = 2 * X - 1                                                                              # inputs as -1/+1
POW = (1 << np.arange(16)).astype(np.int64)


def init(B, H, rng, scale=0.5, out_scale=None, dtype=np.float64):
    """out_scale defaults to scale (Spike 09). Spike 12 uses scale * sqrt(8 / H) so the
    logit stays O(1) as width grows and width 8 reproduces Spike 09."""
    out_scale = scale if out_scale is None else out_scale
    p = {"W1": rng.normal(0, scale, (B, H, N)), "b1": rng.normal(0, scale, (B, H)),
         "W2": rng.normal(0, out_scale, (B, H)), "b2": np.zeros(B)}
    return {k: v.astype(dtype) for k, v in p.items()}


def forward(p, hard=False):
    pre = np.einsum("bhn,xn->bxh", p["W1"], XS.astype(p["W1"].dtype)) + p["b1"][:, None, :]                       # (B, 16, H)
    h = np.where(pre >= 0, 1.0, -1.0) if hard else np.tanh(pre)
    return pre, h, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]


def train(p, targets, care, steps, lr=0.03, wd=0.0, state=None, opt="adamw"):
    """targets, care: (B, 16) arrays of 0/1. Returns (params, adam state).
    opt="gd": plain full-batch gradient descent (no momentum), decoupled weight decay."""
    dt = p["W1"].dtype
    targets, care = targets.astype(dt), care.astype(dt)
    if state is None:
        state = {"t": 0, "m": {k: np.zeros_like(v) for k, v in p.items()},
                 "v": {k: np.zeros_like(v) for k, v in p.items()}}
    ncare = care.sum(1, keepdims=True)
    for _ in range(steps):
        pre, h, z = forward(p)
        dz = (1 / (1 + np.exp(-z)) - targets) * care / ncare                                # (B, 16)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * (1 - h * h)                             # (B, 16, H)
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS.astype(dt))
        g["b1"] = dh.sum(1)
        state["t"] += 1
        t = state["t"]
        if opt == "gd":
            for k in p:
                p[k] = p[k] - lr * g[k] - lr * wd * p[k]
            continue
        for k in p:
            state["m"][k] = 0.9 * state["m"][k] + 0.1 * g[k]
            state["v"][k] = 0.999 * state["v"][k] + 0.001 * g[k] ** 2
            mh, vh = state["m"][k] / (1 - 0.9 ** t), state["v"][k] / (1 - 0.999 ** t)
            p[k] = p[k] - lr * mh / (np.sqrt(vh) + 1e-8) - lr * wd * p[k]
    return p, state


def bits(mat01):
    return (mat01.astype(np.int64) * POW).sum(-1)


def read_circuits(p):
    """Per net: g, faithful, unit threshold functions (as 16-bit ints)."""
    pre, _, z = forward(p)
    g = bits(z >= 0)                                                                         # (B,)
    _, _, zh = forward(p, hard=True)
    faithful = bits(zh >= 0) == g
    units = bits(np.transpose(pre >= 0, (0, 2, 1)))                                          # (B, H)
    return g, faithful, units


def determines(unit_bits, g):
    """Do these threshold functions determine g? (g constant on every cell)"""
    seen = {}
    for x in range(16):
        cell = tuple((u >> x) & 1 for u in unit_bits)
        v = (g >> x) & 1
        if seen.setdefault(cell, v) != v:
            return False
    return True


def effective_width(units, g):
    """(w_eff, isomer) for one net; units is a list of 16-bit ints."""
    full = 0xFFFF
    uniq = sorted({min(int(u), full ^ int(u)) for u in units} - {0})                          # up to complement, drop constants
    if g in (0, full):
        return 0, ()
    for k in range(1, len(uniq) + 1):
        for s in itertools.combinations(uniq, k):
            if determines(s, g):
                return k, s
    return None, None
