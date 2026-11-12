"""Spike 15: the definitive transfer test of the Curie principle (pre-registered in SPIKE_15_REPORT.md).

  python -m experiments.spike15 runA SHARD      modular addition p=61, 8 models per shard (shards 0..11)
  python -m experiments.spike15 runB CELL       symmetric partial Boolean tasks, one architecture cell
  python -m experiments.spike15 analyse
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import random
import sys
import time

import numpy as np

from cerp import atlas, train
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike15_raw"
P_TEST = 61


# ------------------------------------------------------------------ arm A: modular addition

def mult_group_classes(p):
    """Frequencies 1..(p-1)/2 as elements of Z_p^* / {+-1} (cyclic of order (p-1)/2), via a primitive root."""
    K = (p - 1) // 2
    g = next(r for r in range(2, p) if len({pow(r, e, p) for e in range(1, p)}) == p - 1)
    log = {}
    for e in range(p - 1):
        x = pow(g, e, p)
        k = min(x, p - x)
        log.setdefault(k, e % K)
    return K, log                                            # log[k] in Z_K: discrete log of k in the quotient


def subgroup_cosets(K, log):
    """For each divisor d of K with 1 < d < K: the cosets of the subgroup of order d (as lists of k)."""
    out = {}
    for d in range(2, K):
        if K % d:
            continue
        step = K // d                                        # subgroup of order d = multiples of step in Z_K
        cos = {}
        for k, e in log.items():
            cos.setdefault(e % step, []).append(k)
        out[d] = list(cos.values())
    return out


def coset_ratio(w, cosets):
    """Within-coset variance / total variance of the profile w (index k-1)."""
    tot = np.var(w) * len(w)
    if tot == 0:
        return float("nan")
    within = sum(np.var([w[k - 1] for k in c]) * len(c) for c in cosets)
    return within / tot


def percentile_vs_permutations(w, cosets, rng, n=2000):
    obs = coset_ratio(w, cosets)
    perm = np.array([coset_ratio(rng.permutation(w), cosets) for _ in range(n)])
    return float((perm < obs).mean() + 0.5 * (perm == obs).mean())


def runA(shard):
    import torch
    from cerp import modadd as M
    torch.set_num_threads(2)
    p, B = P_TEST, 8
    a, b, y = M.data(p)
    P = M.init(B, p, 128, seed=15_000 + shard, scale=0.5)
    t0 = time.time()
    M.train(P, a, b, y, 2000, lr=1e-2, wd=1.0)
    out = {"shard": shard, "acc": M.accuracy(P, p).tolist(), "spectrum": M.spectrum(P).tolist(),
           "seconds": round(time.time() - t0, 1)}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"A{shard}.json").write_text(json.dumps(out))
    print("A", shard, out["seconds"], "acc", np.round(out["acc"], 3).tolist(), flush=True)


# ------------------------------------------------------------------ arm B: symmetric partial tasks

def perm_transform(perm, neg=0):
    idx = np.array([sum((((i >> perm[j]) & 1) ^ ((neg >> j) & 1)) << j for j in range(4)) for i in range(16)])
    return idx


GROUPS = {   # generators as point maps on {0..15}; the group is what they generate
    "swap01": [perm_transform((1, 0, 2, 3))],
    "cyclic4": [perm_transform((1, 2, 3, 0))],
    "reverse": [perm_transform((3, 2, 1, 0))],
    "S4": [perm_transform((1, 0, 2, 3)), perm_transform((1, 2, 3, 0))],
    "global_negation": [perm_transform((0, 1, 2, 3), 0b1111)],
    "swap01_x_swap23": [perm_transform((1, 0, 2, 3)), perm_transform((0, 1, 3, 2))],
}
CELLS = {
    "tanh-W8-adam": dict(H=8, act="tanh", opt="adamw", lr=0.03, wd=0.03, steps=4000),
    "tanh-W64-adam": dict(H=64, act="tanh", opt="adamw", lr=0.03, wd=0.03, steps=4000),
    "relu-W8-adam": dict(H=8, act="relu", opt="adamw", lr=0.03, wd=0.03, steps=4000),
    "relu-W64-adam": dict(H=64, act="relu", opt="adamw", lr=0.03, wd=0.03, steps=4000),
    "tanh-W8-gd": dict(H=8, act="tanh", opt="gd", lr=0.3, wd=0.003, steps=10000),
    "relu-W8-gd": dict(H=8, act="relu", opt="gd", lr=0.3, wd=0.003, steps=10000),
}


def point_orbits(gens):
    seen, orbits = set(), []
    for x in range(16):
        if x in seen:
            continue
        orb, frontier = {x}, [x]
        while frontier:
            z = frontier.pop()
            for gidx in gens:
                w = int(np.nonzero(gidx == z)[0][0])          # preimage and image both stay in the orbit
                for u in (int(gidx[z]), w):
                    if u not in orb:
                        orb.add(u); frontier.append(u)
        seen |= orb
        orbits.append(sorted(orb))
    return orbits


def invariant(h, orbits):
    return all(len({(h >> x) & 1 for x in o}) == 1 for o in orbits)


def make_tasks():
    rnd = random.Random(1501)
    tasks = []
    for gname, gens in GROUPS.items():
        orbs = point_orbits(gens)
        for _ in range(40):
            for _try in range(1000):
                vals = [rnd.randint(0, 1) for _ in orbs]
                cared = [o for o in orbs if rnd.random() < 0.5]
                ncare = sum(len(o) for o in cared)
                if 4 <= ncare <= 12:
                    break
            f = sum(v << x for v, o in zip(vals, orbs) for x in o)
            care = sum(1 << x for o in cared for x in o)
            tasks.append({"group": gname, "f": f, "care": care})
    return tasks


def runB(cell):
    cfg = CELLS[cell]
    tasks = make_tasks()
    fs = np.array([t["f"] for t in tasks] * 5)
    cs = np.array([t["care"] for t in tasks] * 5)
    p = train.init(len(fs), cfg["H"], np.random.default_rng(15_100 + list(CELLS).index(cell)), dtype=np.float32)
    t0 = time.time()
    p, _ = train.train(p, tgt(fs), tgt(cs), cfg["steps"], lr=cfg["lr"], wd=cfg["wd"], opt=cfg["opt"], act=cfg["act"])
    g, _, _ = train.read_circuits(p, act=cfg["act"])
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"B_{cell}.json").write_text(json.dumps({"cell": cell, **cfg, "learned": g.tolist(),
                                                     "seconds": round(time.time() - t0, 1)}))
    print("B", cell, round(time.time() - t0, 1), flush=True)


# ------------------------------------------------------------------ analysis

def analyse():
    res = {"A": analyseA(), "B": analyseB()}
    (ROOT / "experiments" / "results" / "spike15.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def analyseA():
    K, log = mult_group_classes(P_TEST)
    cos = subgroup_cosets(K, log)
    rng = np.random.default_rng(1502)
    # calibration control: fixed random partitions of the K frequencies into blocks of the same sizes
    fake = {}
    for d, c in cos.items():
        ks = list(range(1, K + 1)); rng.shuffle(ks)
        fake[d] = [ks[i * d:(i + 1) * d] for i in range(K // d)]
    profiles, accs = [], []
    for f in sorted(RAW.glob("A*.json")):
        d = json.loads(f.read_text())
        profiles += d["spectrum"]; accs += d["acc"]
    W = np.array(profiles)
    W = W / W.sum(1, keepdims=True)
    out = {"models": len(W), "mean_acc": float(np.mean(accs)), "subgroups": {}, "fake_partitions": {}}
    from scipy.stats import ttest_1samp
    for name, part in (("subgroups", cos), ("fake_partitions", fake)):
        for d, c in part.items():
            pct = np.array([percentile_vs_permutations(w, c, rng) for w in W])
            t = ttest_1samp(pct, 0.5, alternative="less")
            out[name][str(d)] = {"mean_percentile": float(pct.mean()), "p_one_sided": float(t.pvalue)}
    mean_prof = W.mean(0)
    out["equivariance_mean_profile_cv"] = float(mean_prof.std() / mean_prof.mean())
    out["per_model_profile_cv_mean"] = float((W.std(1) / W.mean(1)).mean())
    return out


def analyseB():
    tb = atlas.build_all(4)[4]
    tasks = make_tasks()
    out = {}
    from math import comb
    for f in sorted(RAW.glob("B_*.json")):
        d = json.loads(f.read_text())
        g = d["learned"]
        stats = {k: [0, 0.0, 0, 0.0] for k in ("all",) + tuple(GROUPS)}  # n, sum expected, sum observed, variance
        fit = cheapest = 0
        for i, h in enumerate(g):
            t = tasks[i % len(tasks)]
            care, fv = t["care"], t["f"]
            if (h & care) != (fv & care):
                continue
            fit += 1
            comps = [fv & care]
            for x in range(16):
                if not (care >> x) & 1:
                    comps += [c | (1 << x) for c in comps]
            comps = np.array(comps)
            cost = tb.hi[comps]
            if tb.hi[h] != cost.min():
                continue
            cheapest += 1
            orbs = point_orbits(GROUPS[t["group"]])
            cheap = comps[cost == cost.min()]
            q = float(np.mean([invariant(int(c), orbs) for c in cheap]))
            if q in (0.0, 1.0):
                continue
            obs = invariant(int(h), orbs)
            for k in ("all", t["group"]):
                stats[k][0] += 1; stats[k][1] += q; stats[k][2] += obs; stats[k][3] += q * (1 - q)
        row = {"fit_rate": fit / len(g), "cheapest_rate_among_fit": cheapest / max(fit, 1)}
        from scipy.stats import norm
        for k, (n, e, o, v) in stats.items():
            if n:
                # observed invariant count vs a sum of independent Bernoulli(q) (Poisson-binomial), normal approx.
                # Runs on the same task are not independent, so z is optimistic; the per-task test is also reported.
                z = (o - e) / math.sqrt(v) if v > 0 else float("nan")
                row[k] = {"runs": n, "expected_invariant_share": e / n, "observed_invariant_share": o / n,
                          "z": z, "p_one_sided": float(norm.sf(z))}
        out[d["cell"]] = row
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "runA":
        for s in sys.argv[2:]:
            runA(int(s))
    elif cmd == "runB":
        for c in sys.argv[2:]:
            runB(c)
    else:
        analyse()
