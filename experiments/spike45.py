"""Spike 45 (pre-registered in SPIKE_45_REPORT.md): the Occam pull on other target classes and on real data.

  python -m experiments.spike45 tasks
  python -m experiments.spike45 occam CELL
  python -m experiments.spike45 nets CELL
  python -m experiments.spike45 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve
from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike45_raw"
OUT = ROOT / "experiments" / "results" / "spike45.json"
n, K = 6, 64
SYN = ("cost4", "symmetric", "noisy", "dnf")
REAL = ("breast_cancer", "wine", "digits", "diabetes")
CELLS = SYN + REAL
P = S36.pts(n)


def bits(y):
    return sum(int(v) << x for x, v in enumerate(y))


def not_threshold(f):
    c = bounds.not_threshold_cert(n, f)
    return bool(c) and kernel_bounds.check_not_threshold(n, f, c["pos"], c["neg"]).ok


def balanced(y):
    return 0.25 * K <= y.sum() <= 0.75 * K


def gen_targets(cls, rng):
    """Yield (f_train_total, f_truth_total) candidates for a synthetic class."""
    while True:
        if cls == "cost4":
            W = rng.integers(-3, 4, (3, n)); b = rng.integers(-6, 7, 3); h = (P @ W.T + b >= 0).astype(int)
            y = (h @ rng.integers(-2, 3, 3) + int(rng.integers(-2, 3)) >= 0)
            if not balanced(y):
                continue
            f = bits(y)
            if netsolve.solve(f, n, netsolve.layered(n, []), W=4, time_limit=10)[0] == "sat":
                continue
            if netsolve.solve(f, n, netsolve.layered(n, [2]), W=4, time_limit=20)[0] != "unsat":
                continue
            yield f
        elif cls == "symmetric":
            g = rng.integers(0, 2, n + 1); y = g[P.sum(1)].astype(bool)
            if balanced(y) and not_threshold(bits(y)):
                yield bits(y)
        elif cls == "noisy":
            W = rng.integers(-3, 4, (2, n)); b = rng.integers(-6, 7, 2); h = (P @ W.T + b >= 0).astype(int)
            y = (h @ rng.integers(-2, 3, 2) + int(rng.integers(-2, 3)) >= 0)
            if balanced(y) and not_threshold(bits(y)):
                yield bits(y)
        elif cls == "dnf":
            y = np.zeros(K, bool)
            for _ in range(3):
                k = int(rng.integers(2, 4)); vars_ = rng.choice(n, k, replace=False); sg = rng.integers(0, 2, k)
                y |= (P[:, vars_] == sg).all(1)
            if balanced(y) and not_threshold(bits(y)):
                yield bits(y)


def real_function(name):
    from sklearn import datasets as D
    if name == "breast_cancer":
        d = D.load_breast_cancer(); X, y = d.data, (d.target == 0)
    elif name == "wine":
        d = D.load_wine(); X, y = d.data, (d.target == 1)
    elif name == "digits":
        d = D.load_digits(); X, y = d.data, (d.target >= 5)
    else:
        d = D.load_diabetes(); X, y = d.data, (d.target > np.median(d.target))
    sd = X.std(0); ok = sd > 0
    corr = np.zeros(X.shape[1]); corr[ok] = np.abs([np.corrcoef(X[:, j], y)[0, 1] for j in np.where(ok)[0]])
    top = np.argsort(-corr, kind="stable")[:n]
    B = (X[:, top] > np.median(X[:, top], 0)).astype(int); code = B @ (1 << np.arange(n))
    f = obs = 0; cells = {}
    for c, lab in zip(code, y):
        cells.setdefault(int(c), []).append(bool(lab))
    for c, labs in cells.items():
        pos = sum(labs)
        if 2 * pos == len(labs):
            continue
        obs |= 1 << c
        if 2 * pos > len(labs):
            f |= 1 << c
    return f, obs, [int(t) for t in top]


def tasks():
    """Each task: f_train (labels the learners see), f_truth, care (seen inputs), held (scored inputs)."""
    cache = RAW / "tasks.json"
    if cache.exists():
        return json.loads(cache.read_text())
    out = {}
    for ci, cls in enumerate(SYN):
        rng = np.random.default_rng(4_500 + ci); T, seen_f = [], set()
        for f in gen_targets(cls, rng):
            if f in seen_f and cls != "symmetric":
                continue
            seen_f.add(f)
            care_idx = rng.choice(K, 48, replace=False); care = bits(np.isin(np.arange(K), care_idx))
            ft = f
            if cls == "noisy":
                for x in rng.choice(care_idx, 5, replace=False):
                    ft ^= 1 << int(x)
            T.append({"f_train": ft, "f_truth": f, "care": care, "held": ((1 << K) - 1) & ~care})
            if len(T) == 100:
                break
        out[cls] = T; print(cls, len(T), flush=True)
    meta = {}
    for di, name in enumerate(REAL):
        f, obs, top = real_function(name); cells = [x for x in range(K) if (obs >> x) & 1]
        rng = np.random.default_rng(4_550 + di); T = []
        while len(T) < 40:
            k = int(round(0.75 * len(cells))); s = rng.choice(cells, k, replace=False)
            care = sum(1 << int(x) for x in s); held = obs & ~care
            lab = lambda m: {(f >> x) & 1 for x in range(K) if (m >> x) & 1}
            if len(lab(care)) < 2 or len(lab(held)) < 2:
                continue
            T.append({"f_train": f & obs, "f_truth": f & obs, "care": care, "held": held})
        out[name] = T
        meta[name] = {"observed_cells": len(cells), "features": top, "ones": sum((f >> x) & 1 for x in cells)}
        print(name, meta[name], flush=True)
    out["_meta"] = meta
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def compile_occam(f, care):
    fc = f & care; t0 = time.time(); spec = art = None; cost = None
    for k, widths in ((1, []), (3, [2]), (4, [3]), (5, [4]), (6, [5])):
        st, a = netsolve.solve(fc, n, netsolve.layered(n, widths), W=4, care=care, time_limit=10)
        if st == "sat":
            cost, spec, art = k, netsolve.layered(n, widths), a; break
    if cost is None:
        return {"cost": None, "seconds": time.time() - t0}
    preds, verified = [], True
    for s in range(3):
        st2, a2 = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=10, rand_obj=s)
        a2 = a2 if st2 == "sat" else art
        y = np.array([kernel.evaluate(a2, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)
        verified &= all(y[x] == bool((f >> x) & 1) for x in range(K) if (care >> x) & 1)
        preds.append(y.tolist())
    return {"cost": cost, "verified": bool(verified), "preds": preds, "seconds": time.time() - t0}


def run_occam(cell):
    res = [compile_occam(t["f_train"], t["care"]) for t in tasks()[cell]]
    (RAW / f"occam_{cell}.json").write_text(json.dumps(res))
    print("occam", cell, "compiled", float(np.mean([r["cost"] is not None for r in res])), flush=True)


def run_nets(cell):
    TK = [(t["f_train"], t["care"]) for t in tasks()[cell]]
    out, fit = S36.train(n, TK, "tanh", 10, 8, 0.03, 0.5, 4_570 + CELLS.index(cell))
    (RAW / f"nets_{cell}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": 10}))
    print("nets", cell, "fit", float(fit.mean()), flush=True)


def analyse():
    T = tasks(); Th = S36.ntk(n, "tanh"); res = {"cells": {}, "meta": T["_meta"]}
    for cell in CELLS:
        occ = json.loads((RAW / f"occam_{cell}.json").read_text()); d = json.loads((RAW / f"nets_{cell}.json").read_text())
        out = np.array(d["out"], bool); fit = np.array(d["fit"]); S = d["seeds"]
        a_o = a_k = tot = dis = side = 0; Pn, Pk, Po, Tr = [], [], [], []; costs = []
        for i, (t, o) in enumerate(zip(T[cell], occ)):
            if o["cost"] is None:
                continue
            costs.append(o["cost"])
            h = np.array([(t["held"] >> x) & 1 for x in range(K)], bool); tr = np.array([(t["f_truth"] >> x) & 1 for x in range(K)], bool)[h]
            op = (np.array(o["preds"], bool)[:, h].mean(0) > 0.5); kp = S36.kpred(Th, n, t["f_train"], t["care"])[h]
            for j in range(S):
                if not fit[i * S + j]:
                    continue
                nt = out[i * S + j][h]; a_o += (nt == op).sum(); a_k += (nt == kp).sum(); tot += len(nt)
                mk = nt != kp; dis += mk.sum(); side += (op == nt)[mk].sum()
                Pn.append(nt); Pk.append(kp); Po.append(op); Tr.append(tr)
        Pn, Pk, Po, Tr = (np.concatenate(v) for v in (Pn, Pk, Po, Tr))
        r = {"compiled": float(np.mean([o["cost"] is not None for o in occ])), "fit": float(fit.mean()), "n_disagreements": int(dis),
             "sides": float(side / dis) if dis else None, "agree_occam": float(a_o / tot), "agree_ntk": float(a_k / tot),
             "bal_net": float(S36.bal(Pn, Tr)), "bal_ntk": float(S36.bal(Pk, Tr)), "bal_occam": float(S36.bal(Po, Tr)),
             "mean_cost": float(np.mean(costs)), "verified": float(np.mean([o.get("verified", False) for o in occ if o["cost"] is not None]))}
        r["guard_ok"] = bool(r["compiled"] >= 0.70 and r["fit"] >= 0.90 and dis >= 200)
        bar = 0.65 if cell in SYN else 0.60
        r["sides_verdict"] = ("no verdict" if not r["guard_ok"] else "held" if r["sides"] >= bar else "broken" if r["sides"] <= 0.50 else "neither")
        res["cells"][cell] = r
        print(cell, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    C = res["cells"]

    def tally(cells, v):
        return sum(C[c]["sides_verdict"] == v for c in cells)
    res["H45.1"] = "HELD" if tally(SYN, "held") >= 3 else "BROKEN" if tally(SYN, "broken") >= 2 else "NEITHER"
    res["H45.2"] = "HELD" if tally(REAL, "held") >= 3 else "BROKEN" if tally(REAL, "broken") >= 2 else "NEITHER"
    d3 = [C[c]["agree_occam"] - C[c]["agree_ntk"] for c in CELLS if C[c]["guard_ok"]]
    res["H45.3"] = "HELD" if sum(x >= 0.02 for x in d3) >= 6 else "BROKEN" if sum(x <= 0 for x in d3) >= 4 else "NEITHER"
    d4 = [C[c]["bal_net"] - C[c]["bal_ntk"] for c in REAL if C[c]["guard_ok"]]
    res["H45.4"] = "HELD" if sum(x >= 0.01 for x in d4) >= 3 else "BROKEN" if sum(x <= 0 for x in d4) >= 3 else "NEITHER"
    res["d_agree"] = {c: C[c]["agree_occam"] - C[c]["agree_ntk"] for c in CELLS}
    res["d_bal_real"] = {c: C[c]["bal_net"] - C[c]["bal_ntk"] for c in REAL}
    OUT.write_text(json.dumps(res, indent=1)); print({k: res[k] for k in ("H45.1", "H45.2", "H45.3", "H45.4")})


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: tasks(), "occam": lambda: run_occam(a[2]), "nets": lambda: run_nets(a[2]), "analyse": analyse}[a[1]]()
