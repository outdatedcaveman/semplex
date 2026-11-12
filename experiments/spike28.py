"""Spike 28 (pre-registered in SPIKE_28_REPORT.md): indicator-alignment R² as predictor of the information tilt (C13).

  python -m experiments.spike28 run ACT      erf | signsqrt | tanh02 | tanh05 | clip2 | bentid | clip4 | silu | gelu
  python -m experiments.spike28 analyse
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
RAW = ROOT / "experiments" / "results" / "spike28_raw"
OUT = ROOT / "experiments" / "results" / "spike28.json"
ACTS = ("erf", "signsqrt", "tanh02", "tanh05", "clip2", "bentid", "clip4", "silu", "gelu")
R2 = {"erf": 0.882, "signsqrt": 0.848, "tanh02": 0.818, "tanh05": 0.767, "clip2": 0.631, "bentid": 0.600,
      "clip4": 0.497, "silu": 0.459, "gelu": 0.450}                      # fixed before any run
GROUP = {a: ("high" if r >= 0.75 else "low" if r <= 0.52 else "middle") for a, r in R2.items()}


def phi(pre, act):
    from scipy.special import erf
    sg = lambda z: 1 / (1 + np.exp(-z))
    if act == "erf":
        return erf(pre), (2 / np.sqrt(np.pi)) * np.exp(-pre * pre)
    if act == "signsqrt":
        a = np.abs(pre); return np.sign(pre) * np.sqrt(a), 0.5 / np.sqrt(a + 1e-4)
    if act in ("tanh02", "tanh05"):
        c = 0.2 if act == "tanh02" else 0.5; h = np.tanh(pre); return h + c * pre, 1 - h * h + c
    if act in ("clip2", "clip4"):
        c = 2.0 if act == "clip2" else 4.0; return np.clip(pre, 0, c), ((pre > 0) & (pre < c)).astype(np.float32)
    if act == "bentid":
        r = np.sqrt(pre * pre + 1); return (r - 1) / 2 + pre, pre / (2 * r) + 1
    if act == "silu":
        s = sg(pre); return pre * s, s * (1 + pre * (1 - s))
    if act == "gelu":
        cdf = 0.5 * (1 + erf(pre / np.sqrt(2))); pdf = np.exp(-pre * pre / 2) / np.sqrt(2 * np.pi); return pre * cdf, cdf + pre * pdf
    raise ValueError(act)


def run(act):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(40) for e in els])
    p = train.init(len(fs), 8, np.random.default_rng(28_000 + ACTS.index(act)), dtype=np.float32)
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
            res[a] = {"R2": R2[a], "group": GROUP[a], "fit": d["fit"], "step3000": S22.fit_law(d["units_at"]["3000"], els, idx, lom, MI)}
            print(a, res[a], flush=True)
    from scipy.stats import spearmanr
    ks = [a for a in ACTS if a in res]
    res["spearman_R2_lambda"] = float(spearmanr([R2[a] for a in ks], [res[a]["step3000"]["lambda_MI"] for a in ks]).correlation)
    print("spearman", res["spearman_R2_lambda"])
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
