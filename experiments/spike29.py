"""Spike 29 (pre-registered in SPIKE_29_REPORT.md): trained-scale indicator alignment; tilt vs generalization.

  python -m experiments.spike29 run ACT
  python -m experiments.spike29 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
from scipy.stats import spearmanr

from cerp import train
from experiments import spike14 as S14
from experiments import spike24 as S24, spike27 as S27, spike28 as S28
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike29_raw"
OUT = ROOT / "experiments" / "results" / "spike29.json"
BASE = json.loads((ROOT / "experiments" / "results" / "spike29_baseline.json").read_text())
ACTS = sorted(BASE["lambda"])


def phi(pre, act):
    if act in S24.ACTS:
        return S24.phi(pre, act)
    if act in ("abs", "relu2", "ssq", "softplus", "elu"):
        return S27.phi(pre, act)
    if act in S28.ACTS:
        return S28.phi(pre, act)
    a = {"relu": 0.0, "leaky0.01": 0.01, "leaky0.1": 0.1, "leaky0.3": 0.3}[act]
    return np.where(pre > 0, pre, a * pre), np.where(pre > 0, 1.0, a).astype(np.float32)


def train_nets(act, fs, care, seed):
    p = train.init(len(fs), 8, np.random.default_rng(seed), dtype=np.float32)
    T = tgt(fs).astype(np.float32); C = care.astype(np.float32); XS = train.XS.astype(np.float32)
    m = {k: np.zeros_like(v) for k, v in p.items()}; v = {k: np.zeros_like(x) for k, x in p.items()}

    def fwd():
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = phi(pre, act)
        return pre, h, d, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
    for t in range(1, 3001):
        pre, h, d, z = fwd()
        dz = (1 / (1 + np.exp(-z)) - T) * C / C.sum(1, keepdims=True)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) - 0.03 * 0.03 * p[k]
    pre, h, _, z = fwd()
    return pre, h, (z >= 0)


def run(act):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els])
    T = tgt(fs).astype(bool)
    i = ACTS.index(act)
    pre, h, _ = train_nets(act, fs, np.ones((len(fs), 16)), 29_000 + i)              # arm A
    ind = (pre > 0).astype(np.float64).ravel(); hv = h.astype(np.float64).ravel()
    r2 = float(np.corrcoef(hv, ind)[0, 1] ** 2)
    rng = np.random.default_rng(29_999)                                              # same holdouts for every activation
    care = np.ones((len(fs), 16), dtype=bool)
    for b in range(len(fs)):
        care[b, rng.choice(16, 4, replace=False)] = False
    _, _, out = train_nets(act, fs, care, 29_500 + i)                                # arm B
    fit = (out == T)[care].reshape(len(fs), 12).all(1)
    held = (out == T)[~care].reshape(len(fs), 4).mean(1)
    res = {"act": act, "R2_trained": r2, "pre_std": float(pre.std()), "armB_fit_rate": float(fit.mean()),
           "heldout_acc": float(held[fit].mean()), "heldout_acc_all": float(held.mean())}
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{act}.json").write_text(json.dumps(res))
    print(res, flush=True)


def analyse():
    rows = {a: json.loads((RAW / f"{a}.json").read_text()) for a in ACTS if (RAW / f"{a}.json").exists()}
    lam = BASE["lambda"]; ks = sorted(rows)
    res = {"n": len(ks), "rows": {k: {**rows[k], "lambda": lam[k], "R2_fixed": BASE["R2_fixed"][k]} for k in ks}}
    res["rho_R2_trained_lambda"] = float(spearmanr([rows[k]["R2_trained"] for k in ks], [lam[k] for k in ks]).correlation)
    res["rho_R2_fixed_lambda"] = float(spearmanr([BASE["R2_fixed"][k] for k in ks], [lam[k] for k in ks]).correlation)
    res["rho_lambda_heldout"] = float(spearmanr([lam[k] for k in ks], [rows[k]["heldout_acc"] for k in ks]).correlation)
    hi = [rows[k]["heldout_acc"] for k in ks if lam[k] >= 7]; lo = [rows[k]["heldout_acc"] for k in ks if lam[k] <= 3]
    res["heldout_tilted_minus_untilted"] = float(np.mean(hi) - np.mean(lo)); res["n_tilted"] = len(hi); res["n_untilted"] = len(lo)
    if "clip2" in rows and "bentid" in rows:
        res["middle_order_correct"] = rows["clip2"]["R2_trained"] > rows["bentid"]["R2_trained"]
    OUT.write_text(json.dumps(res, indent=1))
    for k in ks:
        r = res["rows"][k]; print(f"{k:10s} lam={r['lambda']:6.2f} R2f={r['R2_fixed']:.3f} R2t={r['R2_trained']:.3f} held={r['heldout_acc']:.3f} fitB={r['armB_fit_rate']:.3f}")
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
