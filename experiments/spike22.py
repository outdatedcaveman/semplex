"""Spike 22 (pre-registered in SPIKE_22_REPORT.md): leaky ReLU and unit movement vs the information tilt (C10).

  python -m experiments.spike22 run VARIANT     relu | leaky0.01 | leaky0.1 | leaky0.3 | tanh
  python -m experiments.spike22 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr

from cerp import mechvol, train
from experiments import spike14 as S14
from experiments.spike09 import tgt
from experiments.spike21 import mutual_info

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike22_raw"
OUT = ROOT / "experiments" / "results" / "spike22.json"
FULL = 0xFFFF
VARIANTS = {"relu": 0.0, "leaky0.01": 0.01, "leaky0.1": 0.1, "leaky0.3": 0.3, "tanh": None}


def fwd(p, alpha):
    pre = np.einsum("bhn,xn->bxh", p["W1"], train.XS.astype(np.float32)) + p["b1"][:, None, :]
    if alpha is None:
        h = np.tanh(pre); d = 1 - h * h
    else:
        h = np.where(pre > 0, pre, alpha * pre); d = np.where(pre > 0, 1.0, alpha).astype(np.float32)
    return pre, h, d, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]


def canon_units(pre):
    u = train.bits(np.transpose(pre >= 0, (0, 2, 1)))
    return np.minimum(u, FULL ^ u)


def counts(units, fs, els):
    cnt = {str(e): defaultdict(int) for e in els}
    for b in range(len(fs)):
        for u in units[b]:
            if int(u) != 0:
                cnt[str(int(fs[b]))][str(int(u))] += 1
    return cnt


def run(name):
    alpha = VARIANTS[name]
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(22_000 + list(VARIANTS).index(name)), dtype=np.float32)
    T = tgt(fs).astype(np.float32)
    XS = train.XS.astype(np.float32)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}
    u0 = canon_units(fwd(p, alpha)[0])
    for t in range(1, 3001):
        pre, h, d, z = fwd(p, alpha)
        dz = (1 / (1 + np.exp(-z)) - T) / 16
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) - 0.03 * 0.03 * p[k]
    pre, _, _, z = fwd(p, alpha)
    u1 = canon_units(pre)
    gfun = train.bits(z >= 0)
    out = {"variant": name, "alpha": alpha, "fit": float((gfun == fs).mean()), "movement": float((u0 != u1).mean()),
           "units_at": {"0": counts(u0, fs, els), "3000": counts(u1, fs, els)}}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{name}.json").write_text(json.dumps(out))
    print(name, "fit", out["fit"], "movement", out["movement"], flush=True)


def fit_law(cnt, els, idx, lom, MI):
    C = {e: np.zeros(len(lom)) for e in els}
    for e in els:
        for u, n in cnt[str(e)].items():
            if int(u) in idx:
                C[e][idx[int(u)]] += n

    def nll(pr):
        tot = 0.0
        for e in els:
            s = pr[0] * lom + pr[1] * MI[e]; mx = s.max(); lZ = mx + math.log(np.exp(s - mx).sum())
            tot -= float(C[e] @ (s - lZ))
        return tot
    r = minimize(nll, np.array([1.0, 0.0]), method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-2, "maxiter": 600})
    return {"gamma": float(r.x[0]), "lambda_MI": float(r.x[1])}


def analyse():
    tb, ex, els, iso = S14.setup()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    units = sorted(u for u in omega if u != 0)
    lom = np.array([math.log(omega[u]) for u in units])
    MI = {e: np.array([mutual_info(u, e) for u in units]) for e in els}
    idx = {u: i for i, u in enumerate(units)}
    res = {}
    for name in VARIANTS:
        f = RAW / f"{name}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        res[name] = {"alpha": d["alpha"], "fit": d["fit"], "movement": d["movement"],
                     **{f"step{cp}": fit_law(d["units_at"][cp], els, idx, lom, MI) for cp in ("0", "3000")}}
        print(name, res[name], flush=True)
    mv = [res[k]["movement"] for k in res]; lam = [res[k]["step3000"]["lambda_MI"] for k in res]
    res["spearman_movement_lambda"] = float(spearmanr(mv, lam).correlation)
    print("spearman", res["spearman_movement_lambda"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
