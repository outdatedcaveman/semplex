"""Spike 32 (pre-registered in SPIKE_32_REPORT.md): exact init-prior Bayesian posterior vs trained nets and NTK.

  python -m experiments.spike32 run ACT
  python -m experiments.spike32 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
from scipy.stats import spearmanr

from cerp import train
from experiments import spike14 as S14, spike29 as S29, spike30 as S30
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike32_raw"
OUT = ROOT / "experiments" / "results" / "spike32.json"
XS = train.XS.astype(np.float32)
POW = (1 << np.arange(16)).astype(np.int64)


def freq_table(act, total=16_000_000, chunk=500_000, seed=32_000):
    rng = np.random.default_rng(seed + S29.ACTS.index(act))
    freq = np.zeros(1 << 16, dtype=np.int64)
    for _ in range(total // chunk):
        W1 = rng.normal(0, 0.5, (chunk, 8, 4)).astype(np.float32); b1 = rng.normal(0, 0.5, (chunk, 8)).astype(np.float32)
        W2 = rng.normal(0, 0.5, (chunk, 8)).astype(np.float32)
        pre = np.einsum("bhn,xn->bxh", W1, XS) + b1[:, None, :]
        h, _ = S29.phi(pre, act)
        z = np.einsum("bxh,bh->bx", h, W2)                      # b2 = 0 at init
        code = ((z >= 0).astype(np.int64) * POW).sum(1)
        freq += np.bincount(code, minlength=1 << 16)
    return freq


def predict(freq, seen, held, y):
    base = sum(int(y[x]) << x for x in seen)
    comps = []
    for m in range(16):
        code = base
        for j, x in enumerate(held):
            if (m >> j) & 1:
                code |= 1 << x
        comps.append((code, freq[code] + 0.5))
    w = np.array([c[1] for c in comps]); w = w / w.sum()
    if np.allclose(w, w[0]):
        return np.full(len(held), y[seen].mean() > 0.5)
    return np.array([sum(wi for (code, _), wi in zip(comps, w) if (code >> x) & 1) > 0.5 for x in held])


def run(act):
    freq = freq_table(act)
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els]); T = tgt(fs).astype(bool); care = S30.masks(len(fs))
    post = [predict(freq, np.nonzero(care[b])[0], np.nonzero(~care[b])[0], T[b]).tolist() for b in range(len(fs))]
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{act}.json").write_text(json.dumps({"act": act, "post": post, "distinct_functions": int((freq > 0).sum())}))
    print(act, "done; distinct functions sampled", int((freq > 0).sum()), flush=True)


def bal(p, t):
    return 0.5 * ((p & t).sum() / t.sum() + ((~p) & (~t)).sum() / (~t).sum())


def analyse():
    R = {}; dis_n = dis_post_net = 0
    for a in S29.ACTS:
        d30 = json.loads((S30.RAW / f"{a}.json").read_text()); d32 = json.loads((RAW / f"{a}.json").read_text())
        fit = np.array(d30["fit"])
        net, ker, tru = (np.array(d30[k])[fit] for k in ("net", "kern", "truth")); post = np.array(d32["post"])[fit]
        dis = net != ker; dis_n += int(dis.sum()); dis_post_net += int((post == net)[dis].sum())
        R[a] = {"lambda": S29.BASE["lambda"][a], "agree_post": float((post == net).mean()), "agree_kern": float((ker == net).mean()),
                "bal_post": float(bal(post, tru)), "bal_kern": float(bal(ker, tru)), "bal_net": float(bal(net, tru)),
                "acc_post": float((post == tru).mean()), "acc_net": float((net == tru).mean()), "distinct": d32["distinct_functions"]}
    ks = sorted(R); g = lambda f: [R[k][f] for k in ks]
    res = {"rows": R,
           "H32.1_mean_agree_post": float(np.mean(g("agree_post"))), "mean_agree_kern": float(np.mean(g("agree_kern"))),
           "H32.2_rho_balpost_balnet": float(spearmanr(g("bal_post"), g("bal_net")).correlation),
           "rho_balkern_balnet": float(spearmanr(g("bal_kern"), g("bal_net")).correlation),
           "H32.3_post_sides_with_net_on_net_kernel_disagreements": dis_post_net / dis_n, "pooled_disagreements": dis_n,
           "H32.4_n_post_ge_net": int(sum(R[k]["bal_post"] >= R[k]["bal_net"] for k in ks))}
    OUT.write_text(json.dumps(res, indent=1))
    for k in ks:
        r = R[k]; print(f"{k:10s} agreeP={r['agree_post']:.3f} agreeK={r['agree_kern']:.3f} balP={r['bal_post']:.3f} balK={r['bal_kern']:.3f} balN={r['bal_net']:.3f}")
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
