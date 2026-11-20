"""Spike 50 (pre-registered in SPIKE_50_REPORT.md): graded consensus of minimum circuits.

  python -m experiments.spike50 tasks | occam CELL | nets CELL | analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
from scipy.stats import spearmanr

from cerp import kernel, netsolve
from experiments import spike36 as S36
from experiments import spike48 as S48

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike50_raw"
OUT = ROOT / "experiments" / "results" / "spike50.json"
CELLS = {"n8_s64": (8, 64), "n8_s96": (8, 96), "n10_s80": (10, 80)}
SEEDS, NS = 10, 20


def tasks(cell):
    cache = RAW / f"tasks_{cell}.json"
    if cache.exists():
        return [tuple(t) for t in json.loads(cache.read_text())]
    n, seen = CELLS[cell]; K = 1 << n; ci = list(CELLS).index(cell); rng = np.random.default_rng(5_050 + ci)
    out = [(f, S48.bits(np.isin(np.arange(K), rng.choice(K, seen, replace=False)))) for f in S48.gen_targets(n, 5_000 + ci)]
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def run_occam(cell):
    n, _ = CELLS[cell]; K = 1 << n; P = S36.pts(n); res = []
    ev = lambda a: np.array([kernel.evaluate(a, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)
    for ti, (f, care) in enumerate(tasks(cell)):
        r = netsolve.compile_partial(f, n, care, W=4, time_limit=60)
        if r["status"] != "sat":
            res.append({"cost": None}); continue
        fc = f & care; spec = netsolve.layered(n, [] if r["cost"] == 1 else [r["cost"] - 1])
        lab = np.array([(f >> x) & 1 for x in range(K)], bool); cm = np.array([(care >> x) & 1 for x in range(K)], bool)
        ones = np.zeros(K); good = 0
        for s in range(NS):
            st, a = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=3, rand_obj=s, workers=2)
            if a is None:
                continue
            y = ev(a)
            if (y == lab)[cm].all():
                ones += y; good += 1
        res.append({"cost": r["cost"], "samples": good, "p": (ones / max(good, 1)).round(4).tolist()})
        if ti % 25 == 0:
            print(cell, "task", ti, flush=True)
    (RAW / f"occam_{cell}.json").write_text(json.dumps(res))
    print("occam", cell, "compiled", float(np.mean([r["cost"] is not None for r in res])), "mean samples", float(np.mean([r.get("samples", 0) for r in res])), flush=True)


def run_nets(cell):
    n, _ = CELLS[cell]
    out, fit = S36.train(n, tasks(cell), "tanh", SEEDS, 8, 0.03, 0.5, 5_070 + list(CELLS).index(cell))
    np.savez_compressed(RAW / f"nets_{cell}.npz", out=np.packbits(out, axis=1), fit=fit)
    print("nets", cell, "fit", float(fit.mean()), flush=True)


def analyse():
    res = {"cells": {}}
    for cell, (n, seen) in CELLS.items():
        if not (RAW / f"occam_{cell}.json").exists() or not (RAW / f"nets_{cell}.npz").exists():
            continue
        K = 1 << n; TK = tasks(cell); occ = json.loads((RAW / f"occam_{cell}.json").read_text()); D = np.load(RAW / f"nets_{cell}.npz")
        out = np.unpackbits(D["out"], axis=1)[:, :K].astype(bool); fit = D["fit"]; Th = S36.ntk(n, "tanh")
        ag = agk = tot = 0; PP, QQ, split_mid, split_ext = [], [], [], []; bal_g, bal_k, bal_n, tr_all = [], [], [], []
        for i, ((f, c), o) in enumerate(zip(TK, occ)):
            if o["cost"] is None or o["samples"] == 0:
                continue
            h = np.array([not (c >> x) & 1 for x in range(K)]); p = np.array(o["p"])[h]; kp = S36.kpred(Th, n, f, c)[h]
            gp = np.where(p > 0.5, True, np.where(p < 0.5, False, kp)); tr = np.array([(f >> x) & 1 for x in range(K)], bool)[h]
            nets = [out[i * SEEDS + j][h] for j in range(SEEDS) if fit[i * SEEDS + j]]
            if not nets:
                continue
            Nn = np.array(nets); q = Nn.mean(0)
            ag += (Nn == gp).sum(); agk += (Nn == kp).sum(); tot += Nn.size
            mixed = (p > 0) & (p < 1); PP += p[mixed].tolist(); QQ += q[mixed].tolist()
            sq = np.minimum(q, 1 - q); split_mid += sq[(p >= 0.4) & (p <= 0.6)].tolist(); split_ext += sq[(p == 0) | (p == 1)].tolist()
            bal_g.append(gp); bal_k.append(kp); bal_n.append(Nn[0]); tr_all.append(tr)
        T = np.concatenate(tr_all)
        r = {"n": n, "seen": seen, "compiled": float(np.mean([o["cost"] is not None for o in occ])), "mean_samples": float(np.mean([o.get("samples", 0) for o in occ])),
             "fit": float(fit.mean()), "agree_graded": float(ag / tot), "agree_kernel": float(agk / tot), "n_mixed_inputs": len(PP),
             "rho": float(spearmanr(PP, QQ)[0]) if len(PP) > 2 else None,
             "split_seed_rate_mid": float(np.mean(split_mid)) if split_mid else None, "split_seed_rate_ext": float(np.mean(split_ext)) if split_ext else None,
             "n_mid": len(split_mid), "bal_graded": float(S36.bal(np.concatenate(bal_g), T)), "bal_kernel": float(S36.bal(np.concatenate(bal_k), T)),
             "bal_net_seed0": float(S36.bal(np.concatenate(bal_n), T))}
        r["guard_ok"] = bool(r["fit"] >= 0.90 and r["compiled"] >= 0.90 and len(PP) >= 500)
        res["cells"][cell] = r
        print(cell, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
    C = res["cells"]
    if len(C) == len(CELLS):
        ok = all(x["guard_ok"] for x in C.values()); nv = "NO VERDICT"
        a = [x["agree_graded"] for x in C.values()]; d = [x["agree_graded"] - x["agree_kernel"] for x in C.values()]
        rh = [x["rho"] for x in C.values()]; sp = [x["split_seed_rate_mid"] - x["split_seed_rate_ext"] for x in C.values()]
        res["H50.1"] = nv if not ok else "HELD" if min(a) >= 0.93 else "BROKEN" if min(a) < 0.88 else "NEITHER"
        res["H50.2"] = nv if not ok else "HELD" if min(d) >= 0.03 else "BROKEN" if min(d) <= 0 else "NEITHER"
        res["H50.3"] = nv if not ok else "HELD" if min(rh) >= 0.40 else "BROKEN" if min(rh) <= 0.10 else "NEITHER"
        res["H50.4"] = nv if not ok else "HELD" if min(sp) >= 0.10 else "BROKEN" if min(sp) <= 0 else "NEITHER"
        res["measured"] = {"agree_graded": dict(zip(C, a)), "graded_minus_kernel": dict(zip(C, d)), "rho": dict(zip(C, rh)), "split_mid_minus_ext": dict(zip(C, sp))}
        print({k: res[k] for k in ("H50.1", "H50.2", "H50.3", "H50.4")}, res["measured"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: [print(c, len(tasks(c))) for c in CELLS], "occam": lambda: run_occam(a[2]), "nets": lambda: run_nets(a[2]), "analyse": analyse}[a[1]]()
