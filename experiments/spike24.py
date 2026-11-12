"""Spike 24 (pre-registered in SPIKE_24_REPORT.md): oddness vs saturation as the source of the information tilt.

  python -m experiments.spike24 run ACT      tanh | hardtanh | softsign | arcsinh | sigmoid | cliprelu
  python -m experiments.spike24 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

from cerp import mechvol, train
from experiments import spike14 as S14
from experiments import spike22 as S22
from experiments.spike09 import tgt
from experiments.spike21 import mutual_info

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike24_raw"
OUT = ROOT / "experiments" / "results" / "spike24.json"
ACTS = ("tanh", "hardtanh", "softsign", "arcsinh", "sigmoid", "cliprelu")
ODD = {"tanh": True, "hardtanh": True, "softsign": True, "arcsinh": True, "sigmoid": False, "cliprelu": False, "relu": False}
SAT = {"tanh": True, "hardtanh": True, "softsign": True, "arcsinh": False, "sigmoid": True, "cliprelu": True, "relu": False}


def phi(pre, act):
    """(h, dh/dpre)"""
    if act == "tanh":
        h = np.tanh(pre); return h, 1 - h * h
    if act == "hardtanh":
        return np.clip(pre, -1, 1), (np.abs(pre) < 1).astype(np.float32)
    if act == "softsign":
        a = 1 + np.abs(pre); return pre / a, 1 / (a * a)
    if act == "arcsinh":
        return np.arcsinh(pre), 1 / np.sqrt(1 + pre * pre)
    if act == "sigmoid":
        h = 1 / (1 + np.exp(-pre)); return h, h * (1 - h)
    if act == "cliprelu":
        return np.clip(pre, 0, 1), ((pre > 0) & (pre < 1)).astype(np.float32)
    raise ValueError(act)


def run(act):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(24_000 + ACTS.index(act)), dtype=np.float32)
    T = tgt(fs).astype(np.float32)
    XS = train.XS.astype(np.float32)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}

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
    files = [RAW / f"{a}.json" for a in ACTS] + [S22.RAW / "relu.json"]
    for f in files:
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        name = d["variant"]
        res[name] = {"odd": ODD[name], "saturating": SAT[name], "fit": d["fit"],
                     "step3000": S22.fit_law(d["units_at"]["3000"], els, idx, lom, MI)}
        print(name, res[name], flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
