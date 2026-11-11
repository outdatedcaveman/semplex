"""Learning rules other than backpropagation, on tiny networks (Spike 10b). UNTRUSTED.

Network: n inputs (as -1/+1) -> H tanh units -> 1 logit; full-batch updates on
the care points; Adam on whatever "gradient" the rule supplies.

Rules
  backprop   the true gradient
  frozen     first layer stays at its random initialization; only the output trains
  fa         feedback alignment: the error reaches the hidden layer through fixed
             random weights instead of the output weights
  local      a meta-learned combination of update terms that use NO downstream
             weights (no weight transport): only the unit's own input, activation
             and weights, plus the scalar output error broadcast to every unit.
             A reduced stand-in for the trace-monomial dictionaries of
             Perin, Anselmi & Deny (arXiv:2611.12248); it is NOT their method.

Local dictionary for the first-layer update of unit j (e = sigmoid(z) - target):
  0  -e * (1 - h_j^2) * x      error broadcast with the unit's own slope
  1  -e * h_j * x              error-modulated Hebbian (three-factor)
  2   h_j * x                  Hebbian
  3  -h_j^2 * w_j              Oja-style decay
  4  -w_j                      weight decay
"""

from __future__ import annotations

import itertools

import numpy as np

N_TERMS = 5


def inputs(n):
    X = np.array([[(i >> j) & 1 for j in range(n)] for i in range(1 << n)], dtype=np.float64)
    return 2 * X - 1


def init(B, H, n, rng, scale=0.5):
    return {"W1": rng.normal(0, scale, (B, H, n)), "b1": rng.normal(0, scale, (B, H)),
            "W2": rng.normal(0, scale, (B, H)), "b2": np.zeros(B)}


def forward(p, XS, hard=False):
    pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
    h = np.where(pre >= 0, 1.0, -1.0) if hard else np.tanh(pre)
    return pre, h, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]


def train(p, XS, targets, care, steps, rule="backprop", lr=0.03, wd=0.0, alpha=None, fb=None, state=None,
          on_step=None):
    if state is None:
        state = {"t": 0, "m": {k: np.zeros_like(v) for k, v in p.items()},
                 "v": {k: np.zeros_like(v) for k, v in p.items()}}
    ncare = care.sum(1, keepdims=True)
    for it in range(steps):
        pre, h, z = forward(p, XS)
        dz = (1 / (1 + np.exp(-np.clip(z, -60, 60))) - targets) * care / ncare            # (B, X)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        if rule == "backprop" or rule == "fa":
            back = p["W2"] if rule == "backprop" else fb
            dh = dz[:, :, None] * back[:, None, :] * (1 - h * h)
            g["W1"], g["b1"] = np.einsum("bxh,xn->bhn", dh, XS), dh.sum(1)
        elif rule == "frozen":
            g["W1"], g["b1"] = np.zeros_like(p["W1"]), np.zeros_like(p["b1"])
        elif rule == "local":
            a = alpha
            e = dz[:, :, None]                                                            # (B, X, 1)
            cm = (care / ncare)[:, :, None]
            d = a[0] * e * (1 - h * h) + a[1] * e * h - a[2] * h * cm                      # per (b, x, unit)
            hsq = np.einsum("bxh,bx->bh", h * h, care / ncare)                             # mean h^2
            g["W1"] = np.einsum("bxh,xn->bhn", d, XS) + (a[3] * hsq + a[4])[:, :, None] * p["W1"]
            g["b1"] = d.sum(1) + (a[3] * hsq + a[4]) * p["b1"]
        else:
            raise ValueError(rule)
        state["t"] += 1
        t = state["t"]
        for k in p:
            state["m"][k] = 0.9 * state["m"][k] + 0.1 * g[k]
            state["v"][k] = 0.999 * state["v"][k] + 0.001 * g[k] ** 2
            mh, vh = state["m"][k] / (1 - 0.9 ** t), state["v"][k] / (1 - 0.999 ** t)
            p[k] = p[k] - lr * mh / (np.sqrt(vh) + 1e-8) - lr * wd * p[k]
        if on_step is not None:
            on_step(t, p)
    return p, state


def loss(p, XS, targets, care):
    _, _, z = forward(p, XS)
    z = np.clip(z, -60, 60)
    l = np.log1p(np.exp(-z)) * targets + np.log1p(np.exp(z)) * (1 - targets)
    return (l * care).sum(1) / care.sum(1)


def bits(mat01):
    k = mat01.shape[-1]
    if k <= 62:
        return (mat01.astype(np.int64) * (1 << np.arange(k)).astype(np.int64)).sum(-1)
    return np.array([sum(1 << i for i in np.nonzero(r)[0].tolist()) for r in mat01.reshape(-1, k)],
                    dtype=object).reshape(mat01.shape[:-1])


def read(p, XS):
    pre, _, z = forward(p, XS)
    return bits(z >= 0), bits(np.transpose(pre >= 0, (0, 2, 1)))


def effective_width(units, g, npts, kmax=6):
    full = (1 << npts) - 1
    uniq = sorted({min(int(u), full ^ int(u)) for u in units} - {0})
    if g in (0, full):
        return 0
    gb = [(int(g) >> x) & 1 for x in range(npts)]
    ub = [[(u >> x) & 1 for x in range(npts)] for u in uniq]
    for k in range(1, min(kmax, len(uniq)) + 1):
        for s in itertools.combinations(range(len(uniq)), k):
            seen, ok = {}, True
            for x in range(npts):
                cell = tuple(ub[i][x] for i in s)
                if seen.setdefault(cell, gb[x]) != gb[x]:
                    ok = False
                    break
            if ok:
                return k
    return kmax + 1


def meta_learn_local(XS, targets, care, H, rng, pop=12, gens=25, steps=800, sigma=0.5):
    """Evolution strategy over the 5 coefficients: minimize mean final loss."""
    n = XS.shape[1]
    mean = np.array([1.0, 0.0, 0.0, 0.0, 0.0])           # start from plain error broadcast
    history = []

    def score(a, seed):
        r = np.random.default_rng(seed)
        p = init(len(targets), H, n, r)
        p, _ = train(p, XS, targets, care, steps, rule="local", alpha=a)
        l = loss(p, XS, targets, care)
        return float(np.mean(np.where(np.isfinite(l), np.minimum(l, 5.0), 5.0)))

    best, best_s = mean.copy(), score(mean, 0)
    for g in range(gens):
        cands = [mean + sigma * rng.normal(size=N_TERMS) for _ in range(pop)]
        scores = [score(c, g + 1) for c in cands]
        order = np.argsort(scores)
        elite = [cands[i] for i in order[: pop // 4]]
        mean = np.mean(elite, axis=0)
        if scores[order[0]] < best_s:
            best, best_s = cands[order[0]].copy(), scores[order[0]]
        sigma *= 0.93
        history.append(round(float(scores[order[0]]), 4))
    return best, best_s, history
