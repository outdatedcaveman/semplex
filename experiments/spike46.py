"""Spike 46 (pre-registered in SPIKE_46_REPORT.md): the exact cost-error frontier under label noise.

  python -m experiments.spike46 tasks
  python -m experiments.spike46 frontier CELL
  python -m experiments.spike46 nets CELL
  python -m experiments.spike46 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

from cerp import bounds, kernel, kernel_bounds, netsolve
from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike46_raw"
RAW45 = ROOT / "experiments" / "results" / "spike45_raw"
OUT = ROOT / "experiments" / "results" / "spike46.json"
n, K = 6, 64
DOSES = (0, 2, 5, 8)
SYN = tuple(f"d{d}" for d in DOSES)
REAL = ("breast_cancer", "wine", "digits", "diabetes")
CELLS = SYN + REAL
LADDER = ((1, []), (3, [2]), (4, [3]), (5, [4]), (6, [5]))
P = S36.pts(n)


def bits(y):
    return sum(int(v) << x for x, v in enumerate(y))


def tasks():
    cache = RAW / "tasks.json"
    if cache.exists():
        return json.loads(cache.read_text())
    rng = np.random.default_rng(4_600); base = []
    while len(base) < 60:
        W = rng.integers(-3, 4, (2, n)); b = rng.integers(-6, 7, 2); h = (P @ W.T + b >= 0).astype(int)
        y = (h @ rng.integers(-2, 3, 2) + int(rng.integers(-2, 3)) >= 0)
        if not 0.25 * K <= y.sum() <= 0.75 * K:
            continue
        f = bits(y); c = bounds.not_threshold_cert(n, f)
        if not (c and kernel_bounds.check_not_threshold(n, f, c["pos"], c["neg"]).ok) or any(f == t[0] for t in base):
            continue
        care_idx = rng.choice(K, 48, replace=False); order = [int(x) for x in rng.choice(care_idx, 8, replace=False)]
        base.append((f, bits(np.isin(np.arange(K), care_idx)), order))
    out = {}
    for d in DOSES:
        T = []
        for f, care, order in base:
            ft = f
            for x in order[:d]:
                ft ^= 1 << x
            T.append({"f_train": ft, "f_truth": f, "care": care, "held": ((1 << K) - 1) & ~care})
        out[f"d{d}"] = T
    t45 = json.loads((RAW45 / "tasks.json").read_text())
    for name in REAL:
        out[name] = t45[name]
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def evaluate(art):
    return np.array([kernel.evaluate(art, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in range(K)], dtype=bool)


def frontier(f, care):
    fc = f & care; lab = np.array([(f >> x) & 1 for x in range(K)], bool); cm = np.array([(care >> x) & 1 for x in range(K)], bool)
    pts = []
    for k, widths in LADDER:
        spec = netsolve.layered(n, widths)
        st, art = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=20, min_errors=True)
        if art is None:
            pts.append({"cost": k, "errors": None, "optimal": False}); continue
        e = int((evaluate(art) != lab)[cm].sum()); preds = []
        for s in range(3):
            st2, a2 = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=3, rand_obj=s, max_errors=e)
            y = evaluate(a2 if a2 is not None else art)
            if int((y != lab)[cm].sum()) > e:
                y = evaluate(art)
            preds.append(y.tolist())
        pts.append({"cost": k, "errors": e, "optimal": st == "optimal", "preds": preds})
        if e == 0:
            break
    return pts


def run_frontier(cell):
    res = [frontier(t["f_train"], t["care"]) for t in tasks()[cell]]
    (RAW / f"frontier_{cell}.json").write_text(json.dumps(res))
    print("frontier", cell, "exact-fit found", float(np.mean([r[-1]["errors"] == 0 for r in res])), flush=True)


def run_nets(cell):
    TK = [(t["f_train"], t["care"]) for t in tasks()[cell]]
    out, fit = S36.train(n, TK, "tanh", 10, 8, 0.03, 0.5, 4_610 + SYN.index(cell))
    (RAW / f"nets_{cell}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": 10}))
    print("nets", cell, "fit", float(fit.mean()), flush=True)


def code_bits(k, e, m):
    h = k - 1
    circuit = 7 * math.log2(9) if h == 0 else h * 7 * math.log2(9) + (h + 1) * math.log2(9)
    return circuit + math.log2(math.comb(m, e)) + math.log2(m + 1)


def analyse():
    T = tasks(); Th = S36.ntk(n, "tanh"); res = {"cells": {}}
    for cell in CELLS:
        fr = json.loads((RAW / f"frontier_{cell}.json").read_text())
        d = json.loads(((RAW if cell in SYN else RAW45) / f"nets_{cell}.json").read_text())
        out = np.array(d["out"], bool); fit = np.array(d["fit"]); S = d["seeds"]
        names = ("exact", "simpler", "mdl", "ntk")
        agree = {a: 0 for a in names}; side = {a: 0 for a in names[:3]}; tot = dis = 0
        Pn, Tr = [], []; Pp = {a: [] for a in names}; land = {}; same = used = 0; opt = []; fpts = []
        for i, (t, pts) in enumerate(zip(T[cell], fr)):
            pts = [p for p in pts if p["errors"] is not None]
            if not pts or pts[-1]["errors"] != 0:
                continue
            used += 1; opt += [p["optimal"] for p in pts]; fpts.append([(p["cost"], p["errors"]) for p in pts])
            h = np.array([(t["held"] >> x) & 1 for x in range(K)], bool); m = bin(t["care"]).count("1")
            tr = np.array([(t["f_truth"] >> x) & 1 for x in range(K)], bool)[h]
            comp = [np.array(p["preds"], bool)[:, h].mean(0) > 0.5 for p in pts]
            j_mdl = int(np.argmin([code_bits(p["cost"], p["errors"], m) for p in pts]))
            pred = {"exact": comp[-1], "simpler": comp[-2] if len(pts) > 1 else comp[-1], "mdl": comp[j_mdl],
                    "ntk": S36.kpred(Th, n, t["f_train"], t["care"])[h]}
            same += len(pts) == 1
            for j in range(S):
                if not fit[i * S + j]:
                    continue
                nt = out[i * S + j][h]; tot += len(nt); mk = nt != pred["ntk"]; dis += mk.sum()
                for a in names:
                    agree[a] += (nt == pred[a]).sum(); Pp[a].append(pred[a])
                for a in names[:3]:
                    side[a] += (pred[a] == nt)[mk].sum()
                best = int(np.argmax([(nt == c).mean() for c in comp])); key = str(best - (len(pts) - 1))
                land[key] = land.get(key, 0) + 1
                Pn.append(nt); Tr.append(tr)
        Pn, Tr = np.concatenate(Pn), np.concatenate(Tr)
        r = {"tasks_used": used, "fit": float(fit.mean()), "frac_optimal": float(np.mean(opt)), "frac_simpler_is_exact": same / used,
             "n_disagreements": int(dis), "bal_net": float(S36.bal(Pn, Tr)),
             "landing_offset_from_exact": {k: v / sum(land.values()) for k, v in sorted(land.items())},
             "mean_exact_cost": float(np.mean([f[-1][0] for f in fpts])),
             "mean_errors_at_simpler": float(np.mean([f[-2][1] for f in fpts if len(f) > 1])) if any(len(f) > 1 for f in fpts) else None}
        for a in names:
            r[f"agree_{a}"] = float(agree[a] / tot); r[f"bal_{a}"] = float(S36.bal(np.concatenate(Pp[a]), Tr))
        for a in names[:3]:
            r[f"sides_{a}"] = float(side[a] / dis) if dis else None
        r["guard_ok"] = bool(r["fit"] >= 0.90 and r["frac_optimal"] >= 0.90 and r["frac_simpler_is_exact"] <= 0.5)
        res["cells"][cell] = r
        print(cell, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
    C = res["cells"]; ok = lambda c: C[c]["guard_ok"]
    d1 = C["d0"]["sides_exact"] - C["d8"]["sides_exact"]
    res["H46.1"] = "NO VERDICT" if not (ok("d0") and ok("d8")) else "HELD" if d1 >= 0.10 else "BROKEN" if d1 <= 0.02 else "NEITHER"
    x0 = C["d0"]["agree_simpler"] - C["d0"]["agree_exact"]; x8 = C["d8"]["agree_simpler"] - C["d8"]["agree_exact"]
    res["H46.2"] = "NO VERDICT" if not (ok("d0") and ok("d8")) else "BROKEN" if x8 <= 0 else "HELD" if (x0 <= -0.02 and x8 >= 0.02) else "NEITHER"
    d3 = [C[c]["agree_simpler"] - C[c]["agree_ntk"] for c in REAL if ok(c)]
    res["H46.3"] = "HELD" if sum(v > 0 for v in d3) >= 3 else "BROKEN" if sum(v <= 0 for v in d3) >= 3 else "NEITHER"
    d4 = [C[c]["bal_simpler"] - C[c]["bal_exact"] for c in ("d5", "d8")]
    res["H46.4"] = "NO VERDICT" if not (ok("d5") and ok("d8")) else "HELD" if all(v >= 0.02 for v in d4) else "BROKEN" if all(v <= 0 for v in d4) else "NEITHER"
    res["measured"] = {"H46.1_sides_exact_d0_minus_d8": d1, "H46.2_d0": x0, "H46.2_d8": x8,
                       "H46.3_agree_simpler_minus_ntk": {c: C[c]["agree_simpler"] - C[c]["agree_ntk"] for c in REAL},
                       "H46.4_bal_simpler_minus_exact": {"d5": d4[0], "d8": d4[1]}}
    OUT.write_text(json.dumps(res, indent=1)); print({k: res[k] for k in ("H46.1", "H46.2", "H46.3", "H46.4")}); print(res["measured"])


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: tasks(), "frontier": lambda: run_frontier(a[2]), "nets": lambda: run_nets(a[2]), "analyse": analyse}[a[1]]()
