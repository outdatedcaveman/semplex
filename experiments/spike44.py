"""Spike 44 (pre-registered in SPIKE_44_REPORT.md): does depth raise Occam agreement? (H-K)

  python -m experiments.spike44 run N        N = 5 | 6: three-layer [5, 5] tanh nets
  python -m experiments.spike44 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike44_raw"
OUT = ROOT / "experiments" / "results" / "spike44.json"
H1 = H2 = 5
SEEDS = 10


def init(rng, B, n):
    return {"W1": rng.normal(0, 0.5, (B, H1, n)), "b1": rng.normal(0, 0.5, (B, H1)),
            "W2": rng.normal(0, 0.5, (B, H2, H1)), "b2": rng.normal(0, 0.5, (B, H2)),
            "w3": rng.normal(0, 0.5, (B, H2)), "b3": np.zeros(B)}


def forward(p, XS):
    h1 = np.tanh(np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :])
    h2 = np.tanh(np.einsum("bgh,bxh->bxg", p["W2"], h1) + p["b2"][:, None, :])
    return h1, h2, np.einsum("bxg,bg->bx", h2, p["w3"]) + p["b3"][:, None]


def run(n):
    TK = S36.tasks(n); XS = (2 * S36.pts(n) - 1).astype(np.float32); K = 1 << n
    Y = np.array([[(f >> x) & 1 for x in range(K)] for f, _ in TK for _ in range(SEEDS)], dtype=np.float32)
    C = np.array([[(c >> x) & 1 for x in range(K)] for _, c in TK for _ in range(SEEDS)], dtype=np.float32)
    B = len(Y); rng = np.random.default_rng(4_400 + n); lr = 0.03
    p = {k: v.astype(np.float32) for k, v in init(rng, B, n).items()}
    mo = {k: np.zeros_like(v) for k, v in p.items()}; ve = {k: np.zeros_like(v) for k, v in p.items()}
    for t in range(1, 3001):
        h1, h2, z = forward(p, XS)
        dz = (1 / (1 + np.exp(-np.clip(z, -60, 60))) - Y) * C / C.sum(1, keepdims=True)
        d2 = dz[:, :, None] * p["w3"][:, None, :] * (1 - h2 * h2)
        d1 = np.einsum("bxg,bgh->bxh", d2, p["W2"]) * (1 - h1 * h1)
        g = {"w3": np.einsum("bx,bxg->bg", dz, h2), "b3": dz.sum(1),
             "W2": np.einsum("bxg,bxh->bgh", d2, h1), "b2": d2.sum(1),
             "W1": np.einsum("bxh,xn->bhn", d1, XS), "b1": d1.sum(1)}
        for k in p:
            mo[k] = 0.9 * mo[k] + 0.1 * g[k]; ve[k] = 0.999 * ve[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - lr * (mo[k] / (1 - 0.9 ** t)) / (np.sqrt(ve[k] / (1 - 0.999 ** t)) + 1e-8) - lr * 0.03 * p[k]
    out = forward(p, XS)[2] >= 0
    fit = ((out == Y.astype(bool)) | (C == 0)).all(1)
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"L3_n{n}.json").write_text(json.dumps({"out": out.astype(int).tolist(), "fit": fit.tolist(), "seeds": SEEDS}))
    print("L3 n", n, "fit", float(fit.mean()), flush=True)


def ntk_empirical(n, depth, samples=4_000, seed=4_450, chunk=500):
    """Mean of J Jᵀ over random inits, in closed form per net (tanh)."""
    XS = (2 * S36.pts(n) - 1).astype(np.float64); G0 = XS @ XS.T + 1; rng = np.random.default_rng(seed + depth)
    Ksum = np.zeros((1 << n, 1 << n))
    for _ in range(samples // chunk):
        if depth == 3:
            p = init(rng, chunk, n); h1, h2, _ = forward(p, XS)
            d2 = p["w3"][:, None, :] * (1 - h2 * h2); d1 = np.einsum("bxg,bgh->bxh", d2, p["W2"]) * (1 - h1 * h1)
            Ksum += (np.einsum("bxg,byg->xy", h2, h2) + chunk
                     + (np.einsum("bxg,byg->bxy", d2, d2) * np.einsum("bxh,byh->bxy", h1, h1)).sum(0) + np.einsum("bxg,byg->xy", d2, d2)
                     + np.einsum("bxh,byh->xy", d1, d1) * G0)
        else:
            W = rng.normal(0, 0.5, (chunk, 8, n)); b = rng.normal(0, 0.5, (chunk, 8)); w2 = rng.normal(0, 0.5, (chunk, 8))
            h = np.tanh(np.einsum("bhn,xn->bxh", W, XS) + b[:, None, :]); d = w2[:, None, :] * (1 - h * h)
            Ksum += np.einsum("bxh,byh->xy", h, h) + chunk + np.einsum("bxh,byh->xy", d, d) * G0
    return Ksum / samples


def analyse():
    res = {}
    for n in (5, 6):
        TK = S36.tasks(n); occ = json.loads((S36.RAW / f"occam_n{n}.json").read_text())
        K2, K3 = ntk_empirical(n, 2), ntk_empirical(n, 3); Ka = S36.ntk(n, "tanh")
        corr = float(np.corrcoef(K2.ravel(), Ka.ravel())[0, 1])
        L2 = json.loads((S36.RAW / f"nets_n{n}_tanh.json").read_text()); L3 = json.loads((RAW / f"L3_n{n}.json").read_text())
        r2 = S36.compare(n, TK, occ, np.array(L2["out"], bool), np.array(L2["fit"]), L2["seeds"], K2)
        r3 = S36.compare(n, TK, occ, np.array(L3["out"], bool), np.array(L3["fit"]), L3["seeds"], K3)
        r2a = S36.compare(n, TK, occ, np.array(L2["out"], bool), np.array(L2["fit"]), L2["seeds"], Ka)
        r2["fit"] = float(np.mean(L2["fit"])); r3["fit"] = float(np.mean(L3["fit"]))
        res[f"n{n}"] = {"L2": r2, "L3": r3, "L2_analytic_kernel": r2a, "corr_L2_empirical_vs_analytic_kernel": corr,
                        "d_agree_occam": r3["agree_occam"] - r2["agree_occam"],
                        "d_sides": r3["occam_sides_with_net_where_net_ne_ntk"] - r2["occam_sides_with_net_where_net_ne_ntk"],
                        "d_bal": r3["bal_net"] - r2["bal_net"]}
        print(n, json.dumps({k: (round(v, 4) if isinstance(v, float) else {a: round(float(b), 4) for a, b in v.items() if b is not None})
                             for k, v in res[f"n{n}"].items()}), flush=True)
    OUT.write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    a = sys.argv
    {"run": lambda: run(int(a[2])), "analyse": analyse}[a[1]]()
