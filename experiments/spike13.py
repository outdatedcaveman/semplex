"""Spike 13: GD done properly, and a discriminating test of abductive candidates A1, A2, A4.

  python -m experiments.spike13 calibrate        GD learning rate on 16 elements NOT among Spike 12's 48
  python -m experiments.spike13 run ENV ...      main environments (raw counts to results/spike13_raw/)
  python -m experiments.spike13 analyse

Pre-registered in experiments/SPIKE_13_REPORT.md; candidates in charter/ABDUCTION.md.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

from cerp import atlas, mechvol, train, unitgeom
from experiments import spike12 as S12
from experiments.spike09 import tgt, wstar_table

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike13_raw"
CAL = ROOT / "experiments" / "results" / "spike13_calibration.json"
STEPS = 10_000
LR_GRID = (0.3, 1.0, 3.0, 10.0)
SHRINK = 0.03 * 0.03            # AdamW's per-step weight-decay shrink (lr * wd); GD uses wd = SHRINK / lr


def gd_lr():
    return json.loads(CAL.read_text())["chosen_lr"]


def envs():
    lr = gd_lr()
    return {
        "A8-10k": dict(H=8, scale=0.5, opt="adamw", lr=0.03, steps=STEPS),
        "G8-s0.1": dict(H=8, scale=0.1, opt="gd", lr=lr, steps=STEPS, wd=SHRINK / lr),
        "G8-s0.5": dict(H=8, scale=0.5, opt="gd", lr=lr, steps=STEPS, wd=SHRINK / lr),
        "G8-s2": dict(H=8, scale=2.0, opt="gd", lr=lr, steps=STEPS, wd=SHRINK / lr),
        "G128-s0.5": dict(H=128, scale=0.5, opt="gd", lr=lr, steps=STEPS, wd=SHRINK / lr),
    }


def calibrate():
    tb = atlas.build_all(4)[4]
    wstar, _ = wstar_table(tb)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    pool = sorted(set(e for e in ex if wstar[e] == 2 and tb.hi[e] == 3) - set(S12.elements()[1]))
    cal = sorted(int(x) for x in np.random.default_rng(1300).choice(pool, 16, replace=False))
    fs = np.array(cal * 10)
    out = {"elements": cal, "steps": STEPS, "fit_by_lr": {}}
    for lr in LR_GRID:
        p = train.init(len(fs), 8, np.random.default_rng(1301), scale=0.5, dtype=np.float32)
        p, _ = train.train(p, tgt(fs), np.ones((len(fs), 16)), STEPS, lr=lr, wd=SHRINK / lr, opt="gd")
        g, _, _ = train.read_circuits(p)
        out["fit_by_lr"][str(lr)] = float((g == fs).mean())
        print(lr, out["fit_by_lr"][str(lr)], flush=True)
    best = max(out["fit_by_lr"].values())
    out["chosen_lr"] = min(float(k) for k, v in out["fit_by_lr"].items() if v == best)   # tie -> smaller lr
    CAL.write_text(json.dumps(out, indent=1))
    print("chosen", out["chosen_lr"])


def predictors(iso, g, omega, floor, geom, tstar):
    pc = lambda t: bin(t).count("1")
    agree = lambda t: max(16 - pc(t ^ g), pc(t ^ g))
    out = {}
    for a, b in iso:
        out[f"{a}-{b}"] = {
            "S_vol": math.log(omega.get(a, floor) * omega.get(b, floor)),
            "S_imb": abs(pc(a) - 8) + abs(pc(b) - 8),
            "S_agree": max(agree(a), agree(b)),
            "S_m2": math.log(geom[a]["m2"]) + math.log(geom[b]["m2"]),
            "S_minf": math.log(geom[a]["minf"]) + math.log(geom[b]["minf"]),
            "S_int": -(geom[a]["int"] + geom[b]["int"]),
            "has_tstar": float(a in tstar or b in tstar),
        }
    return out


def analyse():
    tb, els, iso = S12.elements()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    geom = unitgeom.table(tb.ltf)
    full = 0xFFFF
    pc = lambda t: bin(t).count("1")
    data = {p.stem: json.loads(p.read_text()) for p in sorted(RAW.glob("*.json"))}
    data.update({f"S12:{p.stem}": json.loads(p.read_text()) for p in sorted(S12.RAW.glob("*.json"))})
    res = {"envs": {n: {k: d[k] for k in d if k not in ("counts", "elements")} for n, d in data.items()}}
    pred, tstars = {}, {}
    for e in els:
        ag = {b: max(16 - pc(b ^ e), pc(b ^ e)) for b in geom}
        m = max(ag.values())
        tstars[e] = {b for b, a in ag.items() if a == m}
        pred[e] = predictors(iso[e], e, omega, 0.5 / ns, geom, tstars[e])
    names = ("S_vol", "S_imb", "S_agree", "S_m2", "S_minf", "S_int")
    for r in ("R1", "R2"):
        sp, a1 = {}, {}
        for n, d in data.items():
            row = {}
            for s in names:
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
            # A1: share of credited runs whose core contains t*, vs share of isomers containing t*
            obs, base, w = 0.0, 0.0, 0.0
            for e in els:
                c = d["counts"][r][str(e)]
                tot = {k: c[0].get(k, 0) + c[1].get(k, 0) for k in pred[e]}
                n_e = sum(tot.values())
                if n_e == 0:
                    continue
                obs += sum(v * pred[e][k]["has_tstar"] for k, v in tot.items())
                base += n_e * np.mean([pred[e][k]["has_tstar"] for k in pred[e]])
                w += n_e
            a1[n] = {"share_with_tstar": obs / w, "isomer_baseline": base / w, "ratio": obs / base if base else None}
        res[f"median_within_element_spearman_{r}"] = sp
        res[f"A1_tstar_{r}"] = a1
    # invariance: GD vs Adam at matched steps, and GD init scales
    inv = {}
    for a, b in (("A8-10k", "G8-s0.5"), ("S12:W8", "A8-10k"), ("G8-s0.5", "G128-s0.5"),
                 ("G8-s0.1", "G8-s2"), ("G8-s0.5", "G8-s2"), ("G8-s0.1", "G8-s0.5")):
        if a in data and b in data:
            inv[f"{a}|{b}"] = invariance(data[a], data[b], els, "R2")
    res["invariance_R2"] = inv
    (ROOT / "experiments" / "results" / "spike13.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "envs"}, indent=1))
    print(json.dumps({n: {k: v for k, v in e.items() if k in ("fit", "r2_mean_prefix_length", "r2_prefix_not_minimal")}
                      for n, e in res["envs"].items()}, indent=1))


def invariance(da, db, els, r):
    num, den, ne = [], [], 0
    for e in els:
        ca, cb = da["counts"][r][str(e)], db["counts"][r][str(e)]
        bt = [S12.js(ca[0], cb[0]), S12.js(ca[1], cb[1])]
        wt = [S12.js(*ca), S12.js(*cb)]
        if None in bt or None in wt:
            continue
        ne += 1
        num.append(np.mean(bt)); den.append(np.mean(wt))
    return {"elements": ne, "ratio": float(np.mean(num) / np.mean(den)) if den else None}


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "calibrate":
        calibrate()
    elif cmd == "run":
        E = envs()
        for n in sys.argv[2:]:
            S12.run_env(n, envs=E, raw=RAW, seed_base=13_000)
    else:
        analyse()
