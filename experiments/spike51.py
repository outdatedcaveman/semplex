"""Spike 51 (pre-registered in SPIKE_51_REPORT.md): the nets' consequence relation as logic.

  python -m experiments.spike51 run
  python -m experiments.spike51 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from cerp import atlas
from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike51_raw"
OUT = ROOT / "experiments" / "results" / "spike51.json"
G9 = ROOT / "experiments" / "results" / "g9_orbits.json"
n, K, SEEDS = 4, 16, 10


def base_tasks():
    reps = [c["rep"] for c in json.loads(G9.read_text())["dims"]["4"]["classes"] if c["cost"] == 3]
    rng = np.random.default_rng(5_100); T = []
    for f in reps:
        for _ in range(3):
            care = sum(1 << int(x) for x in rng.choice(K, 8, replace=False))
            T.append((f, care))
    return T


def train(TK, seed):
    out, fit = S36.train(n, TK, "tanh", SEEDS, 8, 0.03, 0.5, seed)
    return out.reshape(len(TK), SEEDS, K), fit.reshape(len(TK), SEEDS)


def votes(out, fit):
    """Share of fitted seeds outputting 1, per task and input (nan if no seed fit)."""
    w = fit[:, :, None].astype(float)
    return (out * w).sum(1) / np.maximum(w.sum(1), 1)


def ent(q, thr):
    """Entailed value per input: 1, 0, or -1 (none), for confidence threshold thr (share of seeds)."""
    e = np.full(q.shape, -1)
    e[q >= thr] = 1; e[q <= 1 - thr] = 0
    return e


def run():
    T = base_tasks(); RAW.mkdir(parents=True, exist_ok=True)
    out0, fit0 = train(T, 5_110); q0 = votes(out0, fit0); e0 = ent(q0, 0.9)
    rng = np.random.default_rng(5_101); lits = {"cm": [], "rm": [], "counter": []}
    for i, (f, care) in enumerate(T):
        unseen = [x for x in range(K) if not (care >> x) & 1]
        conf = [x for x in unseen if e0[i, x] >= 0]
        split = [x for x in unseen if 0.15 < q0[i, x] < 0.85]
        if conf:
            x = int(rng.choice(conf)); lits["cm"].append((i, x, int(e0[i, x])))
            x = int(rng.choice(conf)); lits["counter"].append((i, x, 1 - int(e0[i, x])))
        if split:
            x = int(rng.choice(split)); lits["rm"].append((i, x, int(rng.integers(0, 2))))
    res = {"q0": q0.tolist(), "fit0": fit0.tolist(), "tasks": T, "lits": lits, "q1": {}, "fit1": {}}
    for kind, L in lits.items():
        TK = []
        for i, x, v in L:
            f, care = T[i]
            TK.append(((f & ~(1 << x)) | (v << x), care | (1 << x)))
        o, ft = train(TK, 5_120 + ["cm", "rm", "counter"].index(kind))
        res["q1"][kind] = votes(o, ft).tolist(); res["fit1"][kind] = ft.tolist()
        print(kind, len(L), "fit", float(ft.mean()), flush=True)
    (RAW / "run.json").write_text(json.dumps(res))


def minimal_model():
    tb = atlas.build_all(4)[4]
    cost = np.array([int(tb.hi[f]) for f in range(1 << K)]); F = np.arange(1 << K)
    VAL = ((F[:, None] >> np.arange(K)[None, :]) & 1).astype(np.int8)

    def e(f, care, extra=None):
        m = np.ones(len(F), bool)
        for x in range(K):
            if (care >> x) & 1:
                m &= VAL[:, x] == ((f >> x) & 1)
        if extra is not None:
            m &= VAL[:, extra[0]] == extra[1]
        pm = m & (cost == cost[m].min()); v = VAL[pm]
        r = np.full(K, -1); same = (v == v[0]).all(0); r[same] = v[0][same]
        return r
    return e


def kernel_rel():
    Th = S36.ntk(n, "tanh")

    def e(f, care, extra=None):
        if extra is not None:
            f = (f & ~(1 << extra[0])) | (extra[1] << extra[0]); care |= 1 << extra[0]
        return S36.kpred(Th, n, f, care).astype(int)
    return e


def count(rel0, rel1, T, lits, kind):
    """rel0[i] and rel1[j]: entailed values (-1 = none) for task i and literal j of `kind`."""
    c = {"instances": 0, "violations": 0}
    for j, (i, x, v) in enumerate(lits):
        f, care = T[i]
        unseen = [b for b in range(K) if not (care >> b) & 1 and b != x]
        e0, e1 = rel0[i], rel1[j]
        for b in unseen:
            if kind == "cm" and e0[b] >= 0:
                c["instances"] += 1; c["violations"] += int(e1[b] != e0[b])
            if kind == "cut" and e1[b] >= 0:
                c["instances"] += 1; c["violations"] += int(e0[b] != e1[b])
            if kind in ("rm", "counter") and e0[b] >= 0:
                c["instances"] += 1; c["violations"] += int(e1[b] != e0[b])
    c["rate"] = c["violations"] / c["instances"] if c["instances"] else None
    return c


def analyse():
    R = json.loads((RAW / "run.json").read_text()); T = [tuple(t) for t in R["tasks"]]; lits = {k: [tuple(l) for l in v] for k, v in R["lits"].items()}
    q0 = np.array(R["q0"]); fit_all = np.mean(R["fit0"] + sum((R["fit1"][k] for k in R["fit1"]), []))
    out = {"fit": float(fit_all), "n_literals": {k: len(v) for k, v in lits.items()}}
    for name, thr in (("confident", 0.9), ("majority", 0.6)):
        e0 = ent(q0, thr); r = {}
        for kind in ("cm", "rm", "counter"):
            e1 = ent(np.array(R["q1"][kind]), thr)
            r[kind] = count(e0, e1, T, lits[kind], kind)
            if kind == "cm":
                r["cut"] = count(e0, e1, T, lits[kind], "cut")
        out[name] = r
    for name, mk in (("minimal_model", minimal_model), ("kernel", kernel_rel)):
        e = mk(); e0 = [e(f, c) for f, c in T]; r = {}
        own = {}
        for kind in ("cm", "counter"):
            L = []
            for i, x, v in lits[kind]:
                ev = e0[i][x]
                if ev < 0:
                    continue
                L.append((i, x, int(ev) if kind == "cm" else 1 - int(ev)))
            own[kind] = L
        # RM literals for these relations: inputs where the relation entails nothing, else not-¬a holds trivially when entailed value == v
        own["rm"] = [(i, x, v) for i, x, v in lits["rm"] if e0[i][x] != 1 - v]
        for kind, L in own.items():
            e1 = [e(T[i][0], T[i][1], (x, v)) for i, x, v in L]
            r[kind] = count(e0, e1, T, L, kind)
            if kind == "cm":
                r["cut"] = count(e0, e1, T, L, "cut")
        out[name] = r
    # Retraction overlap with the minimal-model relation, on the nets' counter literals
    mm = minimal_model(); e0n = ent(q0, 0.9); e1n = ent(np.array(R["q1"]["counter"]), 0.9)
    both = mm_only = net_only = 0
    for j, (i, x, v) in enumerate(lits["counter"]):
        f, care = T[i]; m0 = mm(f, care); m1 = mm(f, care, (x, v))
        for b in range(K):
            if (care >> b) & 1 or b == x or e0n[i][b] < 0 or m0[b] < 0:
                continue
            mr = m1[b] != m0[b]; nr = e1n[j][b] != e0n[i][b]
            both += mr and nr; mm_only += mr and not nr; net_only += nr and not mr
    out["retraction_overlap"] = {"both": both, "minimal_model_only": mm_only, "net_only": net_only,
                                 "recall_of_mm_retractions": both / max(1, both + mm_only), "precision": both / max(1, both + net_only)}
    C = out["confident"]; ok = out["fit"] >= 0.9 and all(C[k]["instances"] >= 300 for k in ("cm", "cut", "rm", "counter"))
    nv = "NO VERDICT"
    out["H51.1"] = nv if not ok else "HELD" if C["cm"]["rate"] <= 0.05 else "BROKEN" if C["cm"]["rate"] > 0.15 else "NEITHER"
    out["H51.2"] = nv if not ok else "HELD" if C["cut"]["rate"] <= 0.05 else "BROKEN" if C["cut"]["rate"] > 0.15 else "NEITHER"
    out["H51.3"] = nv if not ok else "HELD" if C["rm"]["rate"] <= 0.10 else "BROKEN" if C["rm"]["rate"] > 0.25 else "NEITHER"
    rr = C["counter"]["rate"]; rec = out["retraction_overlap"]["recall_of_mm_retractions"]
    out["H51.4"] = nv if not ok else "HELD" if (rr >= 0.10 and rec >= 0.5) else "BROKEN" if rr < 0.03 else "NEITHER"
    OUT.write_text(json.dumps(out, indent=1, default=int)); print(json.dumps(out, indent=1, default=int))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
