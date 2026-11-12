"""Spike 25 (pre-registered in SPIKE_25_REPORT.md): less strict certified symmetry propagation.

  python -m experiments.spike25 run
"""

from __future__ import annotations

import json
import math
import pathlib
from collections import defaultdict

import numpy as np

from experiments import spike18 as S18

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike25.json"


def poisson_binomial_upper(ps, k):
    """P(#successes >= k) for independent Bernoulli(ps)."""
    dp = np.zeros(len(ps) + 1); dp[0] = 1.0
    for p in ps:
        dp[1:] = dp[1:] * (1 - p) + dp[:-1] * p; dp[0] *= (1 - p)
    return float(dp[k:].sum())


def propagate(pts, y, lab, acc_imgs):
    parent = list(range(len(pts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for img in acc_imgs:
        for i in range(len(pts)):
            if img[i] >= 0:
                a, b = find(i), find(int(img[i]))
                if a != b:
                    parent[a] = b
    orbs = defaultdict(list)
    for i in range(len(pts)):
        orbs[find(i)].append(i)
    lab2, y2 = lab.copy(), y.copy()
    for o in orbs.values():
        ls = {int(y[i]) for i in o if lab[i]}
        if len(ls) > 1:
            return lab.copy(), y.copy(), True
        if len(ls) == 1:
            v = ls.pop()
            for i in o:
                if not lab[i]:
                    lab2[i] = True; y2[i] = v
    return lab2, y2, False


def csp(pts, y, lab, cands, pred, variant):
    index = {pt: i for i, pt in enumerate(pts)}
    dist = lambda a, b: sum(u != v for u, v in zip(pts[a], pts[b]))
    obs = np.where(lab, y.astype(bool), pred)
    L = np.nonzero(lab)[0]
    rng = np.random.default_rng(2500)
    agree, cnt = defaultdict(int), defaultdict(int)
    if variant == "V1":
        for ii in range(len(L)):
            for jj in range(ii + 1, len(L)):
                a, b = L[ii], L[jj]; dd = dist(a, b); cnt[dd] += 1; agree[dd] += int(y[a] == y[b])
    else:
        for a in L:                                   # labelled point vs every other point
            for b in range(len(pts)):
                if b != a and (not lab[b] or b > a):
                    dd = dist(a, b); cnt[dd] += 1; agree[dd] += int(obs[a] == obs[b])
    p0 = {dd: agree[dd] / cnt[dd] for dd in cnt}
    tests = []
    for kind, fn in cands:
        img = np.array([index.get(fn(pt), -1) for pt in pts])
        if variant == "V1":
            pairs = [(i, int(img[i])) for i in range(len(pts)) if img[i] >= 0 and img[i] != i and lab[i] and lab[img[i]]]
            if not pairs or not all(y[a] == y[b] for a, b in pairs):
                tests.append((kind, img, 1.0)); continue
            tests.append((kind, img, math.exp(sum(math.log(p0.get(dist(a, b), 1.0)) for a, b in pairs))))
        else:
            pairs = [(i, int(img[i])) for i in range(len(pts)) if img[i] >= 0 and img[i] != i and (lab[i] or lab[img[i]])]
            if not pairs:
                tests.append((kind, img, 1.0)); continue
            k = sum(int(obs[a] == obs[b]) for a, b in pairs)
            tests.append((kind, img, poisson_binomial_upper([p0.get(dist(a, b), 1.0) for a, b in pairs], k)))
    m = len(tests)
    if variant == "V1":
        order = sorted(range(m), key=lambda i: tests[i][2])
        kmax = max([r + 1 for r, i in enumerate(order) if tests[i][2] <= 0.05 * (r + 1) / m], default=0)
        acc = [tests[i] for i in order[:kmax]]
    else:
        acc = [t for t in tests if t[2] < 0.001 / m]
    lab2, y2, void = propagate(pts, y, lab, [img for _, img, _ in acc])
    return lab2, y2, [k for k, _, _ in acc], void


def run():
    import torch
    torch.set_num_threads(4)
    ttt_pts, ttt_y, ttt_doms = S18.tictactoe()
    mk_pts, mk_ys, mk_doms = S18.monk()
    jobs = [("tic-tac-toe", ttt_pts, ttt_y, ttt_doms, S18.candidates_ttt(), (0.1, 0.2, 0.3))]
    for name, yy in mk_ys.items():
        jobs.append((name, mk_pts, yy, mk_doms, S18.candidates_monk(mk_doms), (0.15, 0.3)))
    out = {}
    for name, pts, y, doms, cands, fracs in jobs:
        X = S18.onehot(pts, doms)
        for frac in fracs:
            rnd = np.random.default_rng(1802)                     # same splits as Spikes 18-19
            labs = []
            for s in range(10):
                lab = np.zeros(len(pts), dtype=bool); lab[rnd.choice(len(pts), int(round(frac * len(pts))), replace=False)] = True
                labs.append(lab)
            base = S18.train_mlp(X, np.array([y for _ in labs], float), np.array(labs, float), seed=1803)
            row = {"acc_base": [float((base[s][~labs[s]] == y[~labs[s]].astype(bool)).mean()) for s in range(10)]}
            for variant in ("V1", "V2"):
                res = [csp(pts, y, labs[s], cands, base[s], variant) for s in range(10)]
                pred = S18.train_mlp(X, np.array([r[1] for r in res], float), np.array([r[0] for r in res], float), seed=1803)
                row[variant] = {"acc": [float((pred[s][~labs[s]] == y[~labs[s]].astype(bool)).mean()) for s in range(10)],
                                "accepted": [r[2] for r in res], "void": [r[3] for r in res],
                                "labelled_after": [int(r[0].sum()) for r in res]}
                acc = row[variant]["accepted"]
                row[variant]["summary"] = {"gain": float(np.mean(row[variant]["acc"]) - np.mean(row["acc_base"])),
                                           "runs_with_decoy": sum("decoy" in a for a in acc), "runs_with_sym": sum("sym" in a for a in acc),
                                           "voided": sum(row[variant]["void"])}
                print(name, frac, variant, round(float(np.mean(row["acc_base"])), 3), row[variant]["summary"], flush=True)
            out[f"{name}@{frac}"] = row
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    run()
