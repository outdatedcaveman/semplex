"""Spike 49 (pre-registered in SPIKE_49_REPORT.md): do nets realize the consensus of minimum circuits?

  python -m experiments.spike49 tasks
  python -m experiments.spike49 forced CELL
  python -m experiments.spike49 nets CELL
  python -m experiments.spike49 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from cerp import kernel, netsolve
from experiments import spike36 as S36
from experiments import spike48 as S48

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike49_raw"
OUT = ROOT / "experiments" / "results" / "spike49.json"
CELLS = {"n8_s48": (8, 48, 10), "n8_s96": (8, 96, 10), "n8_s144": (8, 144, 10), "n10_s80": (10, 80, 5)}
NQ = 120


def tasks(cell):
    cache = RAW / f"tasks_{cell}.json"
    if cache.exists():
        return [tuple(t) for t in json.loads(cache.read_text())]
    n, seen, _ = CELLS[cell]; K = 1 << n; ci = list(CELLS).index(cell); rng = np.random.default_rng(4_950 + ci)
    out = [(f, S48.bits(np.isin(np.arange(K), rng.choice(K, seen, replace=False)))) for f in S48.gen_targets(n, 4_900 + ci)]
    RAW.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(out))
    return out


def ev(art, P, xs):
    n = P.shape[1]
    return np.array([kernel.evaluate(art, {f"x{i}": int(P[x, i]) for i in range(n)}) for x in xs], dtype=bool)


def run_forced(cell):
    n, seen, _ = CELLS[cell]; K = 1 << n; P = S36.pts(n); ci = list(CELLS).index(cell); rng = np.random.default_rng(4_990 + ci); res = []
    for ti, (f, care) in enumerate(tasks(cell)):
        held = [x for x in range(K) if not (care >> x) & 1]; q = sorted(int(x) for x in rng.choice(held, min(NQ, len(held)), replace=False))   # n8_s144 has only 112 held-out inputs
        r = netsolve.compile_partial(f, n, care, W=4, time_limit=60)
        if r["status"] != "sat":
            res.append({"cost": None, "q": q}); continue
        fc = f & care; spec = netsolve.layered(n, [] if r["cost"] == 1 else [r["cost"] - 1]); S = []
        seen_x = [x for x in range(K) if (care >> x) & 1]
        for s in range(5):
            st, a = netsolve.solve(fc, n, spec, W=4, care=care, time_limit=3, rand_obj=s, workers=1)
            a = a if a is not None else r["artifact"]
            if not (ev(a, P, seen_x) == np.array([bool((f >> x) & 1) for x in seen_x])).all():
                a = r["artifact"]
            S.append(ev(a, P, q))
        S = np.array(S); m = S.mean(0); status = []; maj = (m > 0.5)
        for j, x in enumerate(q):
            if 0 < m[j] < 1:
                status.append("unforced"); continue
            v = bool(S[0, j]); f2 = (fc | (1 << x)) if not v else (fc & ~(1 << x))      # demand the opposite value at x
            st, _ = netsolve.solve(f2, n, spec, W=4, care=care | (1 << x), time_limit=5, workers=1)
            status.append("forced" if st == "unsat" else "unforced" if st == "sat" else "unknown")
        res.append({"cost": r["cost"], "certified": bool(r["certified_minimal"]), "q": q, "maj": maj.astype(int).tolist(), "status": status})
        if ti % 20 == 0:
            print(cell, "task", ti, flush=True)
    (RAW / f"forced_{cell}.json").write_text(json.dumps(res))
    st = [s for r in res if r["cost"] is not None for s in r["status"]]
    print("forced", cell, {k: round(st.count(k) / len(st), 3) for k in ("forced", "unforced", "unknown")}, flush=True)


def run_nets(cell):
    n, _, seeds = CELLS[cell]
    out, fit = S36.train(n, tasks(cell), "tanh", seeds, 8, 0.03, 0.5, 4_970 + list(CELLS).index(cell))
    np.savez_compressed(RAW / f"nets_{cell}.npz", out=np.packbits(out, axis=1), fit=fit)
    print("nets", cell, "fit", float(fit.mean()), flush=True)


def analyse():
    res = {"cells": {}}
    for cell, (n, seen, SE) in CELLS.items():
        if not (RAW / f"forced_{cell}.json").exists() or not (RAW / f"nets_{cell}.npz").exists():
            continue
        K = 1 << n; TK = tasks(cell); FR = json.loads((RAW / f"forced_{cell}.json").read_text()); D = np.load(RAW / f"nets_{cell}.npz")
        out = np.unpackbits(D["out"], axis=1)[:, :K].astype(bool); fit = D["fit"]; Th = S36.ntk(n, "tanh")
        c = dict(nf=0, adh=0, kadh=0, dis=0, side=0, nu=0, maj=0, truth_f=0, net_truth_u=0)
        st_all = []; costs = []
        for i, ((f, care), r) in enumerate(zip(TK, FR)):
            if r["cost"] is None:
                continue
            costs.append(r["cost"]); q = np.array(r["q"]); st = np.array(r["status"]); maj = np.array(r["maj"], bool); st_all += r["status"]
            kp = S36.kpred(Th, n, f, care)[q]; tr = np.array([(f >> int(x)) & 1 for x in q], bool); F = st == "forced"; U = st == "unforced"
            c["truth_f"] += (maj == tr)[F].sum() * 1
            for j in range(SE):
                if not fit[i * SE + j]:
                    continue
                nt = out[i * SE + j][q]
                c["nf"] += F.sum(); c["adh"] += (nt == maj)[F].sum(); c["kadh"] += (kp == maj)[F].sum()
                mk = (nt != kp) & F; c["dis"] += mk.sum(); c["side"] += (nt == maj)[mk].sum()
                c["nu"] += U.sum(); c["maj"] += (nt == maj)[U].sum(); c["net_truth_u"] += (nt == tr)[U].sum()
        nq = len(st_all)
        r = {"n": n, "seen": seen, "compiled": float(np.mean([x["cost"] is not None for x in FR])), "fit": float(fit.mean()),
             "frac_forced": st_all.count("forced") / nq, "frac_unforced": st_all.count("unforced") / nq, "frac_unknown": st_all.count("unknown") / nq,
             "cost_hist": {str(k): costs.count(k) for k in sorted(set(costs))}, "n_forced_pairs": int(c["nf"]),
             "adherence": float(c["adh"] / c["nf"]), "kernel_adherence": float(c["kadh"] / c["nf"]),
             "sides_forced": float(c["side"] / c["dis"]) if c["dis"] else None, "n_forced_departures": int(c["dis"]),
             "majority_agreement": float(c["maj"] / c["nu"]) if c["nu"] else None,
             "forced_value_is_true_label": float(c["truth_f"] / max(1, st_all.count("forced"))),
             "net_accuracy_on_unforced": float(c["net_truth_u"] / c["nu"]) if c["nu"] else None}
        r["guard_ok"] = bool(r["fit"] >= 0.90 and r["compiled"] >= 0.90 and r["frac_unknown"] <= 0.10 and c["nf"] >= 2000)
        res["cells"][cell] = r
        print(cell, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
    C = res["cells"]
    if len(C) == len(CELLS):
        ok = all(x["guard_ok"] for x in C.values()); A = [x["adherence"] for x in C.values()]; SF = [x["sides_forced"] for x in C.values()]
        D4 = [x["adherence"] - x["kernel_adherence"] for x in C.values()]; nv = "NO VERDICT"
        res["H49.1"] = nv if not ok else "HELD" if min(A) >= 0.95 else "BROKEN" if min(A) < 0.90 else "NEITHER"
        res["H49.2"] = nv if not ok else "HELD" if max(A) - min(A) <= 0.04 else "BROKEN" if max(A) - min(A) > 0.08 else "NEITHER"
        res["H49.3"] = nv if not ok else "HELD" if min(SF) >= 0.80 else "BROKEN" if min(SF) < 0.65 else "NEITHER"
        res["H49.4"] = nv if not ok else "HELD" if min(D4) >= 0.05 else "BROKEN" if min(D4) <= 0 else "NEITHER"
        res["measured"] = {"adherence_min": min(A), "adherence_range": max(A) - min(A), "sides_forced_min": min(SF), "adherence_minus_kernel_min": min(D4)}
        print({k: res[k] for k in ("H49.1", "H49.2", "H49.3", "H49.4")}, res["measured"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    a = sys.argv
    {"tasks": lambda: [print(c, len(tasks(c))) for c in CELLS], "forced": lambda: run_forced(a[2]), "nets": lambda: run_nets(a[2]), "analyse": analyse}[a[1]]()
