"""Volume law for mechanisms (Spike 11). UNTRUSTED.

For a 4-input function g with minimum determining width 2, an *isomer* is an
unordered pair {t1, t2} of threshold functions (each up to complement) that
determines g. The volume predictor is

    V(I) = Omega(t1) * Omega(t2)

where Omega(t) is the probability that a hidden unit with isotropic Gaussian
(weights, bias), reading inputs in {-1, +1}, computes t or its complement.
Threshold functions are scale invariant, so Omega is a solid angle in R^5 and
the initialization scale does not matter.

Functions are 16-bit ints, bit x = value at input x (as in cerp/train.py).
"""

from __future__ import annotations

import math

import numpy as np

from cerp import train

FULL = 0xFFFF


def canon(u):
    u = np.asarray(u, dtype=np.int64)
    return np.minimum(u, FULL ^ u)


def solid_angles(samples, rng, chunk=1_000_000):
    """Monte Carlo Omega(t) for every threshold function t (canonical up to complement)."""
    counts = {}
    done = 0
    while done < samples:
        k = min(chunk, samples - done)
        wb = rng.normal(size=(k, 5))
        pre = wb[:, :4] @ train.XS.T + wb[:, 4:]
        u = canon(train.bits(pre >= 0))
        for v, c in zip(*np.unique(u, return_counts=True)):
            counts[int(v)] = counts.get(int(v), 0) + int(c)
        done += k
    return {k: v / samples for k, v in counts.items()}, samples


class PairIndex:
    """All unordered pairs of distinct non-constant canonical threshold functions."""

    def __init__(self, ltf_bits):
        H = sorted({int(min(b, FULL ^ b)) for b in ltf_bits} - {0})
        self.H = np.array(H, dtype=np.int64)
        i, j = np.triu_indices(len(H), 1)
        self.i, self.j = i, j
        hb = ((self.H[:, None] >> np.arange(16)) & 1).astype(np.int64)
        self.cells = hb[i] + 2 * hb[j]                                         # (P, 16) in 0..3
        self.onehot = (np.int64(1) << self.cells).astype(np.int8)               # bit per cell

    def isomers(self, g):
        """All pairs {t1, t2} determining g, as a list of (t1, t2) with t1 < t2."""
        gb = np.array([(g >> x) & 1 for x in range(16)], dtype=bool)
        m1 = np.bitwise_or.reduce(np.where(gb[None, :], self.onehot, 0), axis=1)
        m0 = np.bitwise_or.reduce(np.where(~gb[None, :], self.onehot, 0), axis=1)
        k = np.nonzero((m1 & m0) == 0)[0]
        return [(int(self.H[self.i[q]]), int(self.H[self.j[q]])) for q in k]


def minimal_pairs(units, g):
    """Every pair among the net's units (up to complement) that determines g."""
    u = sorted({int(x) for x in canon(units)} - {0})
    out = []
    for a in range(len(u)):
        for b in range(a + 1, len(u)):
            if train.determines((u[a], u[b]), g):
                out.append((u[a], u[b]))
    return out


def score(obs, pred):
    """obs: {isomer: weight} from runs; pred: {isomer: predicted probability} over ALL isomers.

    Returns gain over uniform in bits per run, Spearman rho over all isomers,
    whether the most-observed isomer is the predicted favourite, and the
    in-sample ceiling (gain of the empirical distribution itself)."""
    K = len(pred)
    n = sum(obs.values())
    if n == 0 or K < 2:
        return None
    gain = sum(w * math.log2(pred[i] * K) for i, w in obs.items()) / n
    ceiling = sum(w * math.log2(w / n * K) for i, w in obs.items()) / n
    keys = sorted(pred)
    o = np.array([obs.get(k, 0.0) for k in keys])
    p = np.array([pred[k] for k in keys])
    rho = _spearman(o, p)
    top = max(obs, key=obs.get) == max(pred, key=pred.get)
    return {"gain_bits": gain, "ceiling_bits": ceiling, "spearman": rho, "top1": bool(top), "isomers": K, "runs": n}


def _rank(a):
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[order] = np.arange(len(a))
    for v in np.unique(a):                                                       # average ties
        m = a == v
        r[m] = r[m].mean()
    return r


def _spearman(a, b):
    ra, rb = _rank(a), _rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])
