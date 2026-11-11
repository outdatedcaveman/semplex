"""Weight-space geometry of a tiny architecture (Spike 08b, step 4). UNTRUSTED.

Architecture: n binary inputs -> h step neurons -> 1 step output, every
weight and bias an integer in [-W, W]; a neuron fires iff w.x + b >= 0.
The full weight grid is enumerated (the "genotype space"); each point maps
to the Boolean function it computes (the "phenotype").

Reported structure:
  volume      how many weight settings realize each function / each element
  components  is an element's region connected under single-weight +-1 moves?
  borders     which elements touch, and how far apart (Hamming) touching functions are
"""

from __future__ import annotations

import itertools

import numpy as np


def phenotype_grid(n, h, W):
    R = 2 * W + 1
    vals = np.arange(-W, W + 1)
    X = np.array([[(i >> j) & 1 for j in range(n)] for i in range(1 << n)])
    # every setting of one hidden neuron: (R^(n+1), 2^n) activations
    params = np.array(list(itertools.product(vals, repeat=n + 1)))
    act = ((params[:, :n] @ X.T + params[:, n:]) >= 0).astype(np.int8)          # (K, 2^n)
    K = len(params)
    out_params = np.array(list(itertools.product(vals, repeat=h + 1)))          # (R^(h+1), h+1)
    ph = np.zeros((K,) * h + (len(out_params),), dtype=np.int64)
    for x in range(1 << n):
        pre = np.zeros((K,) * h + (len(out_params),), dtype=np.int16)
        for k in range(h):
            shape = [1] * (h + 1)
            shape[k] = K
            a = act[:, x].reshape(shape)
            shape2 = [1] * (h + 1)
            shape2[h] = len(out_params)
            pre = pre + a * out_params[:, k].reshape(shape2)
        shape2 = [1] * (h + 1)
        shape2[h] = len(out_params)
        pre = pre + out_params[:, h].reshape(shape2)
        ph |= (pre >= 0).astype(np.int64) << x
    P = h * (n + 1) + h + 1
    return ph.reshape((R,) * P)


def components(ph, max_iter=10_000):
    """Connected components of equal-phenotype regions under +-1 moves on one axis."""
    lab = np.arange(ph.size, dtype=np.int64).reshape(ph.shape)
    for it in range(max_iter):
        before = lab.copy()
        for ax in range(ph.ndim):
            a = [slice(None)] * ph.ndim
            b = [slice(None)] * ph.ndim
            a[ax], b[ax] = slice(0, -1), slice(1, None)
            a, b = tuple(a), tuple(b)
            same = ph[a] == ph[b]
            m = np.minimum(lab[a], lab[b])
            lab[a] = np.where(same, m, lab[a])
            lab[b] = np.where(same, m, lab[b])
        if np.array_equal(before, lab):
            break
    roots = np.unique(lab)
    return {int(f): int(c) for f, c in zip(*np.unique(ph.reshape(-1)[roots], return_counts=True))}, it + 1


def borders(ph, n):
    """Counts of adjacent weight settings with different functions, by Hamming distance."""
    ham = {}
    pairs = {}
    for ax in range(ph.ndim):
        a = [slice(None)] * ph.ndim
        b = [slice(None)] * ph.ndim
        a[ax], b[ax] = slice(0, -1), slice(1, None)
        x, y = ph[tuple(a)].reshape(-1), ph[tuple(b)].reshape(-1)
        d = x != y
        x, y = x[d], y[d]
        key = np.minimum(x, y) * (1 << (1 << n)) + np.maximum(x, y)
        for k, c in zip(*np.unique(key, return_counts=True)):
            pairs[int(k)] = pairs.get(int(k), 0) + int(c)
    for k, c in pairs.items():
        u, v = divmod(k, 1 << (1 << n))
        hd = bin(u ^ v).count("1")
        ham[hd] = ham.get(hd, 0) + c
    return ham, pairs


def analyse(n, h, W, canon=None, cost=None):
    ph = phenotype_grid(n, h, W)
    fs, counts = np.unique(ph, return_counts=True)
    vol = {int(f): int(c) for f, c in zip(fs, counts)}
    comp, iters = components(ph)
    ham, pairs = borders(ph, n)
    out = {"n": n, "hidden": h, "W": W, "weight_settings": int(ph.size), "functions_realized": len(vol),
           "functions_with_disconnected_region": sum(1 for c in comp.values() if c > 1),
           "max_components_of_one_function": max(comp.values()), "propagation_rounds": iters,
           "border_pairs_by_hamming_distance": {int(k): v for k, v in sorted(ham.items())},
           "distinct_touching_function_pairs": len(pairs)}
    if canon is not None:
        cv, cc = {}, {}
        for f, v in vol.items():
            c = int(canon[f])
            cv[c] = cv.get(c, 0) + v
        out["elements_realized"] = len(cv)
        out["volume_by_element"] = {str(k): v for k, v in sorted(cv.items(), key=lambda kv: -kv[1])}
        if cost is not None:
            byc = {}
            for c, v in cv.items():
                byc.setdefault(int(cost[c]), []).append(v)
            out["volume_share_by_min_neurons"] = {k: round(sum(v) / ph.size, 4) for k, v in sorted(byc.items())}
            out["mean_volume_per_function_by_min_neurons"] = {}
            for k in sorted(byc):
                fl = [v for f, v in vol.items() if int(cost[f]) == k]
                out["mean_volume_per_function_by_min_neurons"][k] = round(sum(fl) / len(fl), 1)
    return out
