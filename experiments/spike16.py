"""Spike 16: is symmetry inheritance just the kernel limit? Does generalization track the symmetry deficit?
Does stabilizer symmetrization help exactly where the theory says?  Pre-registered in SPIKE_16_REPORT.md.

  python -m experiments.spike16 run CELL ...
  python -m experiments.spike16 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import sys

import numpy as np

from cerp import atlas, train
from experiments import spike15 as S15
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike16_raw"
CELLS = {k: S15.CELLS[k] for k in ("tanh-W8-adam", "relu-W8-adam", "tanh-W8-gd", "tanh-W64-adam")}
FULL = 0xFFFF
B4 = atlas.transforms(4)                                # (perm, neg, idx): (T e)(x) = e(idx[x])


# ------------------------------------------------------------------ kernel limit (part 1)

def ntk(act, rng, units=200_000, scale=0.5):
    """Monte Carlo NTK of a one-hidden-layer net (first layer and output layer trained), inputs in {-1,+1}."""
    Z = np.hstack([train.XS, np.ones((16, 1))])                       # (16, 5)
    K = np.zeros((16, 16))
    done = 0
    while done < units:
        m = min(50_000, units - done)
        wb = rng.normal(0, scale, (m, 5))
        pre = Z @ wb.T                                                 # (16, m)
        if act == "relu":
            phi, dphi = np.maximum(pre, 0), (pre > 0).astype(float)
        else:
            phi = np.tanh(pre); dphi = 1 - phi ** 2
        a2 = scale ** 2                                                # E[W2^2]
        K += phi @ phi.T + a2 * (dphi @ dphi.T) * (Z @ Z.T)
        done += m
    return K / units


def kernel_completion(K, f, care):
    c = [x for x in range(16) if (care >> x) & 1]
    y = np.array([1.0 if (f >> x) & 1 else -1.0 for x in c])
    alpha = np.linalg.solve(K[np.ix_(c, c)] + 1e-8 * np.eye(len(c)), y)
    pred = K[:, c] @ alpha
    return sum(1 << x for x in range(16) if pred[x] >= 0)


# ------------------------------------------------------------------ stabilizer of labelled data (parts 2, 3)

def data_stabilizer(f, care):
    """All input permutations/negations mapping the labelled set to itself with labels preserved."""
    G = []
    for perm, neg, idx in B4:
        ok = True
        for x in range(16):
            if (care >> x) & 1:
                y = int(idx[x])
                if not (care >> y) & 1 or ((f >> y) & 1) != ((f >> x) & 1):
                    ok = False
                    break
        if ok:
            G.append(idx)
    return G


def orbits_of(G):
    seen, out = set(), []
    for x in range(16):
        if x in seen:
            continue
        orb = {int(idx[x]) for idx in G}
        seen |= orb
        out.append(sorted(orb))
    return out


def make_planted():
    tb = atlas.build_all(4)[4]
    rnd = random.Random(1601)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    tasks = []
    while len(tasks) < 600:
        f = rnd.choice(ex)
        # random member of the class, so tasks are not aligned with the exhibit's coordinates
        _, _, idx = rnd.choice(B4)
        f = atlas.apply_T(f, idx, False, 4)
        care = sum(1 << x for x in rnd.sample(range(16), 8))
        G = data_stabilizer(f, care)
        if len(G) < 2:
            continue
        orbs = orbits_of(G)
        free_orbs = [o for o in orbs if not any((care >> x) & 1 for x in o)]
        inv = S15.invariant(f, orbs)
        tasks.append({"f": int(f), "care": int(care), "G": len(G), "invariant": bool(inv)})
    return tasks


# ------------------------------------------------------------------ runs

def run(cell):
    cfg = CELLS[cell]
    armB = S15.make_tasks()
    planted = make_planted()
    fs = np.array([t["f"] for t in armB] * 5 + [t["f"] for t in planted] * 3)
    cs = np.array([t["care"] for t in armB] * 5 + [t["care"] for t in planted] * 3)
    p = train.init(len(fs), cfg["H"], np.random.default_rng(16_000 + list(CELLS).index(cell)), dtype=np.float32)
    p, _ = train.train(p, tgt(fs), tgt(cs), cfg["steps"], lr=cfg["lr"], wd=cfg["wd"], opt=cfg["opt"], act=cfg["act"])
    _, _, z = train.forward(p, act=cfg["act"])
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{cell}.json").write_text(json.dumps({"cell": cell, "n_armB": len(armB) * 5, "logits": z.astype(float).round(4).tolist()}))
    print(cell, "done", flush=True)


def analyse():
    tb = atlas.build_all(4)[4]
    armB = S15.make_tasks()
    planted = make_planted()
    rng = np.random.default_rng(1602)
    kern = {a: ntk(a, rng) for a in ("tanh", "relu")}
    res = {"planted_tasks": len(planted), "planted_invariant_share": float(np.mean([t["invariant"] for t in planted]))}
    for f in sorted(RAW.glob("*.json")):
        d = json.loads(f.read_text())
        cell = d["cell"]; cfg = CELLS[cell]
        Z = np.array(d["logits"]); nB = d["n_armB"]
        g = ((Z >= 0).astype(np.int64) * (1 << np.arange(16))).sum(1)
        K = kern[cfg["act"]]
        # part 1: kernel vs learned on arm-B tasks
        n_inv = same_K_given_inv = n_scored = kern_inv = kern_cheap = 0
        for i in range(nB):
            t = armB[i % len(armB)]
            h = int(g[i]); care, fv = t["care"], t["f"]
            if (h & care) != (fv & care):
                continue
            comps = [fv & care]
            for x in range(16):
                if not (care >> x) & 1:
                    comps += [c | (1 << x) for c in comps]
            comps = np.array(comps); cost = tb.hi[comps]
            if tb.hi[h] != cost.min():
                continue
            orbs = S15.point_orbits(S15.GROUPS[t["group"]])
            cheap = comps[cost == cost.min()]
            q = np.mean([S15.invariant(int(c), orbs) for c in cheap])
            if q in (0.0, 1.0):
                continue
            hk = kernel_completion(K, fv, care)
            n_scored += 1
            kern_inv += S15.invariant(hk, orbs)
            kern_cheap += tb.hi[hk] == cost.min()
            if S15.invariant(h, orbs):
                n_inv += 1
                same_K_given_inv += h == hk
        part1 = {"runs": n_scored, "kernel_completion_invariant": kern_inv / n_scored,
                 "kernel_completion_cheapest": kern_cheap / n_scored,
                 "P_learned_equals_kernel_given_learned_invariant": same_K_given_inv / max(n_inv, 1)}
        # parts 2 and 3: planted targets
        acc = {True: [], False: []}; acc_sym = {True: [], False: []}
        err_break = err_keep = n_break = n_keep = 0
        for j, t in enumerate(planted * 3):
            i = nB + j
            fv, care = t["f"], t["care"]
            free = [x for x in range(16) if not (care >> x) & 1]
            G = data_stabilizer(fv, care)
            zz = Z[i]
            zs = np.mean([zz[np.array(idx)] for idx in G], axis=0)                # orbit-averaged logits
            hv = [(zz[x] >= 0) == bool((fv >> x) & 1) for x in free]
            hs = [(zs[x] >= 0) == bool((fv >> x) & 1) for x in free]
            acc[t["invariant"]].append(np.mean(hv)); acc_sym[t["invariant"]].append(np.mean(hs))
            for o in orbits_of(G):
                fo = [x for x in o if not (care >> x) & 1]
                if not fo:
                    continue
                breaks = len({(fv >> x) & 1 for x in o}) > 1
                e = sum(not ((zz[x] >= 0) == bool((fv >> x) & 1)) for x in fo)
                if breaks:
                    err_break += e; n_break += len(fo)
                else:
                    err_keep += e; n_keep += len(fo)
        cost_inv = float(np.mean([tb.hi[t["f"]] for t in planted if t["invariant"]]))
        cost_non = float(np.mean([tb.hi[t["f"]] for t in planted if not t["invariant"]]))
        part2 = {"heldout_acc_target_invariant": float(np.mean(acc[True])), "heldout_acc_target_breaks": float(np.mean(acc[False])),
                 "mean_cost_invariant_targets": cost_inv, "mean_cost_breaking_targets": cost_non,
                 "error_rate_on_orbits_where_target_breaks": err_break / max(n_break, 1),
                 "error_rate_on_orbits_where_target_keeps": err_keep / max(n_keep, 1)}
        part3 = {"symmetrization_gain_target_invariant": float(np.mean(acc_sym[True]) - np.mean(acc[True])),
                 "symmetrization_gain_target_breaks": float(np.mean(acc_sym[False]) - np.mean(acc[False]))}
        res[cell] = {"part1_kernel": part1, "part2_deficit": part2, "part3_method": part3}
    (ROOT / "experiments" / "results" / "spike16.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        for c in sys.argv[2:]:
            run(c)
    else:
        analyse()
