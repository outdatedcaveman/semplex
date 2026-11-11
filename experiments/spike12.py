"""Spike 12: is the learned circuit invariant when the environment changes?

  python -m experiments.spike12 run W8 W32 ...   (writes results/spike12_raw/<ENV>.json)
  python -m experiments.spike12 analyse          (writes results/spike12.json)

Pre-registered in experiments/SPIKE_12_REPORT.md.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from collections import defaultdict

import numpy as np

from cerp import atlas, mechvol, train
from experiments.spike09 import tgt, wstar_table

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike12_raw"
STEPS, SEEDS, HALF = 3000, 40, 20
ENVS = {
    "W8": dict(H=8, scale=0.5, opt="adamw", lr=0.03),
    "W32": dict(H=32, scale=0.5, opt="adamw", lr=0.03),
    "W128": dict(H=128, scale=0.5, opt="adamw", lr=0.03),
    "W512": dict(H=512, scale=0.5, opt="adamw", lr=0.03),
    "W1024": dict(H=1024, scale=0.5, opt="adamw", lr=0.03),
    "W8-s0.1": dict(H=8, scale=0.1, opt="adamw", lr=0.03),
    "W8-s2": dict(H=8, scale=2.0, opt="adamw", lr=0.03),
    "W8-GD": dict(H=8, scale=0.5, opt="gd", lr=1.0),
}


def elements():
    tb = atlas.build_all(4)[4]
    wstar, _ = wstar_table(tb)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    els = [e for e in ex if wstar[e] == 2 and tb.hi[e] == 3]
    pidx = mechvol.PairIndex(tb.ltf)
    iso = {e: pidx.isomers(e) for e in els}
    order = sorted(els, key=lambda e: (len(iso[e]), e))
    rng = np.random.default_rng(1200)
    chosen = []
    for q in np.array_split(np.array(order), 4):                                  # stratified by isomer count
        chosen += sorted(int(x) for x in rng.choice(q, 12, replace=False))
    return tb, chosen, {e: iso[e] for e in chosen}


def r2_prefix(units, w2, g):
    """Shortest prefix of units ordered by |output weight| that determines g."""
    order = np.argsort(-np.abs(w2), kind="stable")
    codes = [0] * 16
    for k, u in enumerate(order, 1):
        u = int(units[u])
        codes = [(c << 1) | ((u >> x) & 1) for x, c in enumerate(codes)]
        seen, ok = {}, True
        for x in range(16):
            if seen.setdefault(codes[x], (g >> x) & 1) != (g >> x) & 1:
                ok = False
                break
        if ok:
            return [int(units[j]) for j in order[:k]]
    return None


def credit(unitset, isos):
    hit = [q for q in isos if q[0] in unitset and q[1] in unitset]
    return {f"{q[0]}-{q[1]}": 1 / len(hit) for q in hit}


def run_env(name):
    cfg = ENVS[name]
    tb, els, iso = elements()
    H = cfg["H"]
    fs = np.array([e for _ in range(SEEDS) for e in els])                         # seed-major: half = index // (len(els)*HALF)
    rng = np.random.default_rng(12_000 + list(ENVS).index(name))
    t0 = time.time()
    p = train.init(len(fs), H, rng, scale=cfg["scale"], out_scale=cfg["scale"] * math.sqrt(8 / H), dtype=np.float32)
    p, _ = train.train(p, tgt(fs), np.ones((len(fs), 16)), STEPS, lr=cfg["lr"], wd=0.03, opt=cfg["opt"])
    g, faithful, units = train.read_circuits(p)
    out = {"env": name, **cfg, "steps": STEPS, "elements": els, "nets": len(fs), "train_seconds": round(time.time() - t0, 1)}
    counts = {r: {str(e): [defaultdict(float), defaultdict(float)] for e in els} for r in ("R1", "R2")}
    fit = g == fs
    plen, nonmin = [], 0
    for b in np.nonzero(fit)[0]:
        e, half = int(fs[b]), int(b // (len(els) * HALF))
        cu = {int(x) for x in mechvol.canon(units[b])}
        for k, v in credit(cu, iso[e]).items():
            counts["R1"][str(e)][half][k] += v
        pre = r2_prefix(units[b], p["W2"][b], e)
        if pre is None:
            continue
        plen.append(len(pre))
        c2 = credit({int(x) for x in mechvol.canon(pre)}, iso[e])
        nonmin += not c2
        for k, v in c2.items():
            counts["R2"][str(e)][half][k] += v
    out.update({"fit": float(fit.mean()), "faithful_when_fit": float(faithful[fit].mean()),
                "r2_mean_prefix_length": float(np.mean(plen)) if plen else None,
                "r2_prefix_not_minimal": nonmin, "counts": counts})
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(out))
    print(name, {k: v for k, v in out.items() if k not in ("counts", "elements")}, flush=True)


# ------------------------------------------------------------------ analysis

def js(p, q):
    keys = set(p) | set(q)
    sp, sq = sum(p.values()), sum(q.values())
    if sp == 0 or sq == 0:
        return None
    d = 0.0
    for k in keys:
        a, b = p.get(k, 0) / sp, q.get(k, 0) / sq
        m = (a + b) / 2
        d += (a * math.log2(a / m) if a else 0) + (b * math.log2(b / m) if b else 0)
    return d / 2


def predictors(iso, g, omega, floor):
    pc = lambda t: bin(t).count("1")
    agree = lambda t: max(16 - pc(t ^ g), pc(t ^ g))
    out = {}
    for q in iso:
        a, b = q
        out[f"{a}-{b}"] = {"S_vol": math.log(omega.get(a, floor) * omega.get(b, floor)),
                           "S_imb": abs(pc(a) - 8) + abs(pc(b) - 8),
                           "S_agree": max(agree(a), agree(b))}
    return out


def analyse():
    data = {p.stem: json.loads(p.read_text()) for p in sorted(RAW.glob("*.json"))}
    tb, els, iso = elements()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    pred = {e: predictors(iso[e], e, omega, 0.5 / ns) for e in els}
    res = {"envs": {n: {k: d[k] for k in d if k not in ("counts", "elements")} for n, d in data.items()}}
    pairs = [("W8", "W32"), ("W32", "W128"), ("W128", "W512"), ("W512", "W1024"), ("W8", "W1024"),
             ("W8", "W8-GD"), ("W8", "W8-s0.1"), ("W8", "W8-s2"), ("W8-s0.1", "W8-s2")]
    for r in ("R1", "R2"):
        within = {}
        for n, d in data.items():
            v = [js(*d["counts"][r][str(e)]) for e in els]
            within[n] = [x for x in v]
        inv = {}
        for a, b in pairs:
            if a not in data or b not in data:
                continue
            num, den, modal, ne = [], [], [], 0
            for i, e in enumerate(els):
                ca, cb = data[a]["counts"][r][str(e)], data[b]["counts"][r][str(e)]
                bt = [js(ca[0], cb[0]), js(ca[1], cb[1])]
                wt = [within[a][i], within[b][i]]
                if None in bt or None in wt:
                    continue
                ne += 1
                num.append(np.mean(bt)); den.append(np.mean(wt))
                ta = {k: ca[0].get(k, 0) + ca[1].get(k, 0) for k in set(ca[0]) | set(ca[1])}
                tb_ = {k: cb[0].get(k, 0) + cb[1].get(k, 0) for k in set(cb[0]) | set(cb[1])}
                modal.append(max(ta, key=ta.get) == max(tb_, key=tb_.get))
            inv[f"{a}|{b}"] = {"elements": ne, "js_between": float(np.mean(num)) if num else None,
                               "js_within": float(np.mean(den)) if den else None,
                               "ratio": float(np.mean(num) / np.mean(den)) if den else None,
                               "modal_agreement": float(np.mean(modal)) if modal else None}
        res[f"invariance_{r}"] = inv
        sp = {}
        for n, d in data.items():
            row = {}
            for s in ("S_vol", "S_imb", "S_agree"):
                rhos = []
                for e in els:
                    c = d["counts"][r][str(e)]
                    tot = {k: c[0].get(k, 0) + c[1].get(k, 0) for k in pred[e]}
                    if sum(tot.values()) == 0:
                        continue
                    y = np.array([tot[k] for k in pred[e]]); x = np.array([pred[e][k][s] for k in pred[e]])
                    rhos.append(mechvol._spearman(y, x))
                row[s] = float(np.nanmedian(rhos)) if rhos else None
            sp[n] = row
        res[f"median_within_element_spearman_{r}"] = sp
    (ROOT / "experiments" / "results" / "spike12.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "envs"}, indent=1))
    print(json.dumps(res["envs"], indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        for n in sys.argv[2:]:
            run_env(n)
    else:
        analyse()
