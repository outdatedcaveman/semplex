"""Spike 48 (pre-registered in SPIKE_48_REPORT.md): the Occam pull at n = 8 and n = 10.

  python -m experiments.spike48 tasks
  python -m experiments.spike48 occam CELL
  python -m experiments.spike48 nets CELL
  python -m experiments.spike48 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve
from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike48_raw"
OUT = ROOT / "experiments" / "results" / "spike48.json"
CELLS = {"n8_matched": (8, 64, 4_800, 4_801, 10), "n10_matched": (10, 80, 4_810, 4_811, 5), "n8_literal": (8, 192, 4_800, 4_802, 10)}
MATCHED = ("n8_matched", "n10_matched")


def bits(y):
    return sum(int(v) << x for x, v in enumerate(y))


def gen_targets(n, seed, count=100):
    P = S36.pts(n); K = 1 << n; rng = np.random.default_rng(seed); T = []
    while len(T) < count:
        W = rng.integers(-3, 4, (2, n)); b = rng.integers(-6, 7, 2); h = (P @ W.T + b >= 0).astype(int)
        y = (h @ rng.integers(-2, 3, 2) + int(rng.integers(-2, 3)) >= 0)
        if not 0.25 * K <= y.sum() <= 0.75 * K:
            continue
        f = bits(y); c = bounds.not_threshold_cert(n, f)
        if c and kernel_bounds.check_not_threshold(n, f, c["pos"], c["neg"]).ok and f not in T:
            T.append(f)
    return T


def tasks(cell):
    cache = RAW / f"tasks_{cell}.json"
    if cache.exists():
        return [tuple(t) for t in json.loads(cache.read_text())]
    n, seen, tseed, cseed, _ = CELLS[cell]; K = 1 << n; rng = np.random.default_rng(cseed)
    out = [(f, bits(np.isin(np.arange(K), rng.choice(K, seen, replace=False)))) for f in gen_targets(n, tseed)]
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def run_occam(cell):
    n = CELLS[cell][0]; K = 1 << n; P = S36.pts(n); res = []
    for f, care in tasks(cell):
        r = netsolve.compile_partial(f, n, care, W=4, time_limit=60)
        if r["status"] != "sat":
            res.append({"cost": None}); continue
        fc = f & care; spec = netsolve.layered(n, [] if r["cost"] == 1 else [r["cost"] - 1]); preds = []; verified = True
        for s in range(5):
            st, a = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=3, rand_obj=s)
            a = a if a is not None else r["artifact"]
            y = np.array([kernel.evaluate(a, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)
            ok = all(y[x] == bool((f >> x) & 1) for x in range(K) if (care >> x) & 1)
            if not ok:
                y = np.array([kernel.evaluate(r["artifact"], {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)
                ok = all(y[x] == bool((f >> x) & 1) for x in range(K) if (care >> x) & 1)
            verified &= ok; preds.append(np.packbits(y).tolist())
        res.append({"cost": r["cost"], "certified": bool(r["certified_minimal"]), "verified": bool(verified), "preds": preds, "seconds": r["seconds"]})
    (RAW / f"occam_{cell}.json").write_text(json.dumps(res))
    print("occam", cell, "compiled", float(np.mean([r["cost"] is not None for r in res])), "certified", float(np.mean([r.get("certified", False) for r in res])), flush=True)


def run_nets(cell):
    n, _, _, _, seeds = CELLS[cell]
    out, fit = S36.train(n, tasks(cell), "tanh", seeds, 8, 0.03, 0.5, 4_820 + list(CELLS).index(cell))
    np.savez_compressed(RAW / f"nets_{cell}.npz", out=np.packbits(out, axis=1), fit=fit)
    print("nets", cell, "fit", float(fit.mean()), flush=True)


def analyse():
    res = {"cells": {}}
    for cell, (n, seen, _, _, S) in CELLS.items():
        if not (RAW / f"occam_{cell}.json").exists() or not (RAW / f"nets_{cell}.npz").exists():
            continue
        K = 1 << n; TK = tasks(cell); occ = json.loads((RAW / f"occam_{cell}.json").read_text()); D = np.load(RAW / f"nets_{cell}.npz")
        out = np.unpackbits(D["out"], axis=1)[:, :K].astype(bool); fit = D["fit"]; Th = S36.ntk(n, "tanh")
        a_o = a_k = tot = dis = side = 0; Pn, Pk, Po, Tr = [], [], [], []
        for i, ((f, c), o) in enumerate(zip(TK, occ)):
            if o["cost"] is None:
                continue
            h = np.array([not (c >> x) & 1 for x in range(K)]); tr = np.array([(f >> x) & 1 for x in range(K)], bool)[h]
            op = np.unpackbits(np.array(o["preds"], dtype=np.uint8), axis=1)[:, :K].astype(bool)[:, h].mean(0) > 0.5
            kp = S36.kpred(Th, n, f, c)[h]
            for j in range(S):
                if not fit[i * S + j]:
                    continue
                nt = out[i * S + j][h]; a_o += (nt == op).sum(); a_k += (nt == kp).sum(); tot += len(nt)
                mk = nt != kp; dis += mk.sum(); side += (op == nt)[mk].sum()
                Pn.append(nt); Pk.append(kp); Po.append(op); Tr.append(tr)
        Pn, Pk, Po, Tr = (np.concatenate(v) for v in (Pn, Pk, Po, Tr))
        costs = [o["cost"] for o in occ if o["cost"] is not None]
        r = {"n": n, "seen": seen, "compiled": float(np.mean([o["cost"] is not None for o in occ])), "certified": float(np.mean([o.get("certified", False) for o in occ])),
             "verified": float(np.mean([o.get("verified", False) for o in occ])), "cost_hist": {str(k): costs.count(k) for k in sorted(set(costs))},
             "fit": float(fit.mean()), "n_disagreements": int(dis), "sides": float(side / dis) if dis else None,
             "agree_occam": float(a_o / tot), "agree_ntk": float(a_k / tot),
             "bal_net": float(S36.bal(Pn, Tr)), "bal_ntk": float(S36.bal(Pk, Tr)), "bal_occam": float(S36.bal(Po, Tr))}
        r["guard_ok"] = bool(r["fit"] >= 0.90 and r["compiled"] >= 0.90 and dis >= 500)
        res["cells"][cell] = r
        print(cell, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
    C = res["cells"]
    if all(c in C for c in MATCHED):
        ok = all(C[c]["guard_ok"] for c in MATCHED)
        s = [C[c]["sides"] for c in MATCHED]; d2 = [C[c]["agree_occam"] - C[c]["agree_ntk"] for c in MATCHED]; d3 = [C[c]["bal_net"] - C[c]["bal_ntk"] for c in MATCHED]
        v = lambda xs, hi, lo: "NO VERDICT" if not ok else "HELD" if all(x >= hi for x in xs) else "BROKEN" if any(x <= lo for x in xs) else "NEITHER"
        res["H48.1"] = v(s, 0.65, 0.50); res["H48.2"] = v(d2, 0.02, 0.0); res["H48.3"] = v(d3, 0.02, 0.0)
        res["measured"] = {"sides": dict(zip(MATCHED, s)), "agree_occam_minus_ntk": dict(zip(MATCHED, d2)), "bal_net_minus_ntk": dict(zip(MATCHED, d3))}
        print({k: res[k] for k in ("H48.1", "H48.2", "H48.3")}, res["measured"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: [print(c, len(tasks(c))) for c in CELLS], "occam": lambda: run_occam(a[2]), "nets": lambda: run_nets(a[2]), "analyse": analyse}[a[1]]()
