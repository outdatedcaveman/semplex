"""Spike 33 (pre-registered in SPIKE_33_REPORT.md): feature learning vs information tilt as the source of the gain over the init-prior posterior.

  python -m experiments.spike33 run ACT ARM      ARM in C (deterministic rerun of Spike 29 arm B), D, G, A
  python -m experiments.spike33 analyse
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np
from scipy.stats import spearmanr

from cerp import mechvol, train
from experiments import spike14 as S14, spike22 as S22, spike29 as S29, spike30 as S30
from experiments.spike09 import tgt
from experiments.spike21 import mutual_info

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike33_raw"
OUT = ROOT / "experiments" / "results" / "spike33.json"
ACTS = ("tanh", "sigmoid", "erf", "relu", "gelu", "abs")
ARMS = ("D", "G", "A")
XS = train.XS.astype(np.float32)


def train_arm(act, fs, care, seed, arm):
    H = 64 if arm == "A" else 8
    out_scale = 0.5 * math.sqrt(8 / H)
    p = train.init(len(fs), H, np.random.default_rng(seed), out_scale=out_scale, dtype=np.float32)
    T = tgt(fs).astype(np.float32); C = care.astype(np.float32)
    trainable = ("W2", "b2") if arm == "A" else ("W1", "b1", "W2", "b2")
    m = {k: np.zeros_like(p[k]) for k in trainable}; v = {k: np.zeros_like(p[k]) for k in trainable}

    def fwd():
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = S29.phi(pre, act)
        return pre, h, d, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
    pre0 = fwd()[0]
    for t in range(1, 3001):
        pre, h, d, z = fwd()
        dz = (1 / (1 + np.exp(-z)) - T) * C / C.sum(1, keepdims=True)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        if arm != "A":
            dh = dz[:, :, None] * p["W2"][:, None, :] * d
            g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in trainable:
            if arm == "G":
                p[k] = p[k] - 0.3 * g[k] - 0.3 * 0.003 * p[k]
                continue
            m[k] = 0.9 * m[k] + 0.1 * g[k]; v[k] = 0.999 * v[k] + 0.001 * g[k] ** 2
            step = 0.03 * (m[k] / (1 - 0.9 ** t)) / (np.sqrt(v[k] / (1 - 0.999 ** t)) + 1e-8) + 0.03 * 0.03 * p[k]
            if arm == "D" and k in ("W1", "b1"):
                step = 0.1 * step
            p[k] = p[k] - step
    pre, _, _, z = fwd()
    return pre0, pre, z >= 0


def run(act, arm):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els]); T = tgt(fs).astype(bool); care = S30.masks(len(fs))
    seed = 29_500 + S29.ACTS.index(act) if arm == "C" else 33_000 + 10 * ACTS.index(act) + ARMS.index(arm)
    pre0, pre, out = train_arm(act, fs, care, seed, arm)
    u0, u1 = S22.canon_units(pre0), S22.canon_units(pre)
    fit = (out == T)[care].reshape(len(fs), 12).all(1)
    held = [out[b, ~care[b]].tolist() for b in range(len(fs))]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{act}_{arm}.json").write_text(json.dumps({"act": act, "arm": arm, "fit": fit.tolist(), "net": held,
                                                       "movement": float((u0 != u1).mean()), "units_3000": S22.counts(u1, fs, els)}))
    print(act, arm, "fit", float(fit.mean()), "movement", float((u0 != u1).mean()), flush=True)


def bal(p, t):
    return 0.5 * ((p & t).sum() / t.sum() + ((~p) & (~t)).sum() / (~t).sum())


def analyse():
    tb, ex, els, iso = S14.setup()
    omega, ns = mechvol.solid_angles(40_000_000, np.random.default_rng(1100))
    units = sorted(u for u in omega if u != 0); idx = {u: i for i, u in enumerate(units)}
    lom = np.array([math.log(omega[u]) for u in units]); MI = {e: np.array([mutual_info(u, e) for u in units]) for e in els}
    rows = {}; repro = {}
    for act in ACTS:
        d30 = json.loads((S30.RAW / f"{act}.json").read_text())
        post_all = np.array(json.loads((ROOT / "experiments" / "results" / "spike32_raw" / f"{act}.json").read_text())["post"])
        tru_all = np.array(d30["truth"])
        dC = json.loads((RAW / f"{act}_C.json").read_text())
        repro[act] = int((np.array(dC["net"]) != np.array(d30["net"])).sum())   # deviation: tolerate <= 0.1% of bits (float32 update order)
        if repro[act] > 5:
            raise SystemExit(f"arm C rerun differs from Spike 30 in {repro[act]} bits for {act}")
        cells = {}
        for arm in ("C",) + ARMS:
            d = json.loads((RAW / f"{act}_{arm}.json").read_text())
            cells[arm] = {"fit": d["fit"], "net": d["net"], "movement": d["movement"],
                          "lambda": S22.fit_law(d["units_3000"], els, idx, lom, MI)["lambda_MI"]}
        for arm, c in cells.items():
            fit = np.array(c["fit"]); net = np.array(c["net"])[fit]; tru = tru_all[fit]; post = post_all[fit]
            rows[f"{act}|{arm}"] = {"act": act, "arm": arm, "fit_rate": float(fit.mean()), "bal_net": float(bal(net, tru)),
                                    "bal_post": float(bal(post, tru)), "gain": float(bal(net, tru) - bal(post, tru)),
                                    "lambda": c["lambda"], "movement": c["movement"]}
    trained = [r for r in rows.values() if r["arm"] in ("C", "D", "G")]
    withmove = [r for r in trained if r["movement"] is not None]
    res = {"rows": rows, "armC_bits_differing_from_spike30": repro,
           "H33.1_mean_gain_A": float(np.mean([r["gain"] for r in rows.values() if r["arm"] == "A"])),
           "mean_gain_C": float(np.mean([r["gain"] for r in rows.values() if r["arm"] == "C"])),
           "H33.2_rho_lambda_gain": float(spearmanr([r["lambda"] for r in trained], [r["gain"] for r in trained]).correlation),
           "H33.3_rho_movement_gain": float(spearmanr([r["movement"] for r in withmove], [r["gain"] for r in withmove]).correlation) if len(withmove) > 2 else None,
           "H33.3_n_cells_with_movement": len(withmove)}
    gc = {r["act"]: r["gain"] for r in rows.values() if r["arm"] == "C"}
    res["H33.4_ratio_untilted_over_tilted"] = float(np.mean([gc[a] for a in ("relu", "gelu", "abs")]) / np.mean([gc[a] for a in ("tanh", "sigmoid", "erf")]))
    OUT.write_text(json.dumps(res, indent=1))
    for k, r in rows.items():
        mv = "" if r["movement"] is None else f" move={r['movement']:.3f}"
        print(f"{k:12s} fit={r['fit_rate']:.3f} lam={r['lambda']:6.2f} balN={r['bal_net']:.3f} balP={r['bal_post']:.3f} gain={r['gain']:+.3f}{mv}")
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    run(sys.argv[2], sys.argv[3]) if sys.argv[1] == "run" else analyse()
