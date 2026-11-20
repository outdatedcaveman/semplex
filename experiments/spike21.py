"""Spike 21 (pre-registered in SPIKE_21_REPORT.md): unit-level law over training; credit-ratchet ablation.

  python -m experiments.spike21 run VARIANT       tanh-adamw | tanh-gd | tanh-gd-dem | relu-adamw
  python -m experiments.spike21 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize

from cerp import loglin, mechvol, train
from experiments import spike14 as S14
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike21_raw"
OUT = ROOT / "experiments" / "results" / "spike21.json"
CH = (0, 10, 30, 100, 300, 1000, 3000)
VARIANTS = {"tanh-adamw": dict(act="tanh", opt="adamw", lr=0.03, wd=0.03, dem=False),
            "tanh-gd": dict(act="tanh", opt="gd", lr=0.3, wd=0.003, dem=False),
            "tanh-gd-dem": dict(act="tanh", opt="gd", lr=0.3, wd=0.003, dem=True),
            "relu-adamw": dict(act="relu", opt="adamw", lr=0.03, wd=0.03, dem=False)}


def step_loop(p, T, steps, cfg, state):
    XS = train.XS.astype(np.float32)
    for _ in range(steps):
        pre, h, z = train.forward(p, act=cfg["act"])
        dz = (1 / (1 + np.exp(-z)) - T) / 16
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dact = (pre > 0).astype(np.float32) if cfg["act"] == "relu" else (1 - h * h)
        dh = dz[:, :, None] * p["W2"][:, None, :] * dact
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS)
        g["b1"] = dh.sum(1)
        if cfg["dem"]:
            s = 1.0 / (np.abs(p["W2"]) + 0.05)
            g["W1"] = g["W1"] * s[:, :, None]; g["b1"] = g["b1"] * s
        state["t"] += 1
        t = state["t"]
        for k in p:
            if cfg["opt"] == "gd":
                p[k] = p[k] - cfg["lr"] * g[k] - cfg["lr"] * cfg["wd"] * p[k]
            else:
                state["m"][k] = 0.9 * state["m"][k] + 0.1 * g[k]
                state["v"][k] = 0.999 * state["v"][k] + 0.001 * g[k] ** 2
                mh, vh = state["m"][k] / (1 - 0.9 ** t), state["v"][k] / (1 - 0.999 ** t)
                p[k] = p[k] - cfg["lr"] * mh / (np.sqrt(vh) + 1e-8) - cfg["lr"] * cfg["wd"] * p[k]
    return p


def run(name):
    cfg = VARIANTS[name]
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(21_000 + list(VARIANTS).index(name)), dtype=np.float32)
    T = tgt(fs).astype(np.float32)
    state = {"t": 0, "m": {k: np.zeros_like(v) for k, v in p.items()}, "v": {k: np.zeros_like(v) for k, v in p.items()}}
    done, units_at = 0, {}
    for cp in CH:
        if cp > done:
            p = step_loop(p, T, cp - done, cfg, state); done = cp
        _, _, units = train.read_circuits(p, act=cfg["act"])
        cnt = {str(e): defaultdict(int) for e in els}
        for b in range(len(fs)):
            for u in mechvol.canon(units[b]):
                if int(u) != 0:
                    cnt[str(int(fs[b]))][str(int(u))] += 1
        units_at[str(cp)] = cnt
    g, _, _ = train.read_circuits(p, act=cfg["act"])
    out = {"variant": name, **cfg, "fit": float((g == fs).mean()), "units_at": units_at}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(out))
    print(name, "fit", out["fit"], flush=True)


def mutual_info(t, g):
    n = np.zeros((2, 2))
    for x in range(16):
        n[(t >> x) & 1, (g >> x) & 1] += 1
    p = n / 16; pt = p.sum(1); pg = p.sum(0)
    return float(sum(p[i, j] * math.log2(p[i, j] / (pt[i] * pg[j])) for i in range(2) for j in range(2) if p[i, j] > 0))


def analyse():
    tb, ex, els, iso = S14.setup()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    units = sorted(u for u in omega if u != 0)
    lom = np.array([math.log(omega[u]) for u in units])
    MI = {e: np.array([mutual_info(u, e) for u in units]) for e in els}
    idx = {u: i for i, u in enumerate(units)}
    res = {}
    for f in sorted(RAW.glob("*.json")):
        d = json.loads(f.read_text())
        row = {"fit": d["fit"], "by_step": {}}
        for cp, cnt in d["units_at"].items():
            C = {e: np.zeros(len(units)) for e in els}
            for e in els:
                for u, n in cnt[str(e)].items():
                    if int(u) in idx:
                        C[e][idx[int(u)]] += n

            def nll(pr):
                gam, lam = pr
                tot = 0.0
                for e in els:
                    s = gam * lom + lam * MI[e]; m = s.max(); lZ = m + math.log(np.exp(s - m).sum())
                    tot -= float(C[e] @ (s - lZ))
                return tot
            r = minimize(nll, np.array([1.0, 0.0]), method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-2, "maxiter": 600})
            th, f = loglin.fit([(C[e], np.stack([lom, MI[e]], 1)) for e in els], 2)
            row["by_step"][cp] = {"gamma": float(th[0]), "lambda_MI": float(th[1]),
                                  "nelder_mead_first_analysis": {"gamma": float(r.x[0]), "lambda_MI": float(r.x[1]), "nll": float(r.fun)}, "nll": float(f)}
        res[d["variant"]] = row
        print(d["variant"], row, flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        analyse()
