"""Spike 27 (pre-registered in SPIKE_27_REPORT.md): positive homogeneity and the information tilt (C12).

  python -m experiments.spike27 run ACT      abs | relu2 | ssq | softplus | elu | relu-sphere
  python -m experiments.spike27 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

from cerp import mechvol, train
from experiments import spike14 as S14, spike22 as S22
from experiments.spike09 import tgt
from experiments.spike21 import mutual_info

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike27_raw"
OUT = ROOT / "experiments" / "results" / "spike27.json"
ACTS = ("abs", "relu2", "ssq", "softplus", "elu", "relu-sphere")
HOMOG = {"abs": True, "relu2": True, "ssq": True, "softplus": False, "elu": False, "relu-sphere": "relu, symmetry removed"}


def phi(pre, act):
    if act == "abs":
        return np.abs(pre), np.sign(pre)
    if act == "relu2":
        r = np.maximum(pre, 0); return r * r, 2 * r
    if act == "ssq":
        return pre * np.abs(pre), 2 * np.abs(pre)
    if act == "softplus":
        return np.logaddexp(0, pre), 1 / (1 + np.exp(-pre))
    if act == "elu":
        e = np.exp(np.minimum(pre, 0)); return np.where(pre > 0, pre, e - 1), np.where(pre > 0, 1.0, e).astype(np.float32)
    if act == "relu-sphere":
        return np.maximum(pre, 0), (pre > 0).astype(np.float32)
    raise ValueError(act)


def run(act):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(27_000 + ACTS.index(act)), dtype=np.float32)
    T = tgt(fs).astype(np.float32)
    XS = train.XS.astype(np.float32)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}
    norm0 = np.sqrt((p["W1"] ** 2).sum(2) + p["b1"] ** 2)

    def fwd():
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = phi(pre, act)
        return pre, h, d, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
    u0 = S22.canon_units(fwd()[0])
    for t in range(1, 3001):
        pre, h, d, z = fwd()
        dz = (1 / (1 + np.exp(-z)) - T) / 16
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) - 0.03 * 0.03 * p[k]
        if act == "relu-sphere":
            s = norm0 / (np.sqrt((p["W1"] ** 2).sum(2) + p["b1"] ** 2) + 1e-12)
            p["W1"] = p["W1"] * s[:, :, None]; p["b1"] = p["b1"] * s
    pre, _, _, z = fwd()
    u1 = S22.canon_units(pre)
    gfun = train.bits(z >= 0)
    out = {"variant": act, "fit": float((gfun == fs).mean()), "movement": float((u0 != u1).mean()),
           "units_at": {"0": S22.counts(u0, fs, els), "3000": S22.counts(u1, fs, els)}}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{act}.json").write_text(json.dumps(out))
    print(act, "fit", out["fit"], flush=True)


def analyse():
    tb, ex, els, iso = S14.setup()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    units = sorted(u for u in omega if u != 0)
    lom = np.array([math.log(omega[u]) for u in units])
    MI = {e: np.array([mutual_info(u, e) for u in units]) for e in els}
    idx = {u: i for i, u in enumerate(units)}
    res = {}
    for a in ACTS:
        f = RAW / f"{a}.json"
        if f.exists():
            d = json.loads(f.read_text())
            res[a] = {"homogeneous": HOMOG[a], "fit": d["fit"], "step3000": S22.fit_law(d["units_at"]["3000"], els, idx, lom, MI)}
            print(a, res[a], flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
