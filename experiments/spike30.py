"""Spike 30 (pre-registered in SPIKE_30_REPORT.md): initial-NTK account of held-out generalization.

  python -m experiments.spike30 run ACT
  python -m experiments.spike30 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
from scipy.stats import spearmanr

from cerp import train
from experiments import spike14 as S14
from experiments import spike29 as S29
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike30_raw"
OUT = ROOT / "experiments" / "results" / "spike30.json"
XS = train.XS.astype(np.float64)                                    # (16, 4), ±1


def masks(n):
    rng = np.random.default_rng(29_999)                               # identical to Spike 29
    care = np.ones((n, 16), dtype=bool)
    for b in range(n):
        care[b, rng.choice(16, 4, replace=False)] = False
    return care


def ntk(act, n=400_000, seed=30_000):
    rng = np.random.default_rng(seed)
    w = rng.normal(0, 0.5, (n, 4)); b = rng.normal(0, 0.5, n)
    z = (XS @ w.T + b).astype(np.float32)                             # (16, n)
    h, d = S29.phi(z, act)
    h = h.astype(np.float64); d = d.astype(np.float64)
    nngp = h @ h.T / n; dd = d @ d.T / n
    return 8 * (nngp + 0.25 * dd * (XS @ XS.T + 1)) + 1


def kernel_predict(K, seen, y, eps):
    Kss = K[np.ix_(seen, seen)]
    reg = eps * np.trace(Kss) / len(seen)
    a = np.linalg.solve(Kss + reg * np.eye(len(seen)), y[seen] * 2.0 - 1)
    return K[:, seen] @ a > 0


def run(act):
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els])
    T = tgt(fs).astype(bool)
    care = masks(len(fs))
    i = S29.ACTS.index(act)
    _, _, out = S29.train_nets(act, fs, care, 29_500 + i)            # deterministic rerun of Spike 29 arm B
    fit = (out == T)[care].reshape(len(fs), 12).all(1)
    K = ntk(act)
    rows = {"fit": fit.tolist(), "net": [], "kern": [], "kern_loose": [], "nn1": [], "truth": []}
    for b in range(len(fs)):
        seen = np.nonzero(care[b])[0]; held = np.nonzero(~care[b])[0]
        kp = kernel_predict(K, seen, T[b].astype(float), 1e-3); kl = kernel_predict(K, seen, T[b].astype(float), 1e-1)
        nn = []
        for x in held:
            d = np.abs(XS[seen] - XS[x]).sum(1) / 2
            near = seen[d == d.min()]; v = T[b, near].mean()
            nn.append(bool(v > 0.5) if v != 0.5 else bool(T[b, seen].mean() >= 0.5))
        rows["net"].append(out[b, held].tolist()); rows["kern"].append(kp[held].tolist())
        rows["kern_loose"].append(kl[held].tolist()); rows["nn1"].append(nn); rows["truth"].append(T[b, held].tolist())
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{act}.json").write_text(json.dumps({"act": act, **rows}))
    print(act, "done", flush=True)


def analyse():
    lam = S29.BASE["lambda"]
    res = {"rows": {}}
    pooled_dis, pooled_kern_right = 0, 0
    for a in S29.ACTS:
        f = RAW / f"{a}.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        fit = np.array(d["fit"]); net, kern, kl, nn, tru = (np.array(d[k])[fit] for k in ("net", "kern", "kern_loose", "nn1", "truth"))
        dis = net != kern
        pooled_dis += int(dis.sum()); pooled_kern_right += int((kern == tru)[dis].sum())
        res["rows"][a] = {"lambda": lam[a], "net_acc": float((net == tru).mean()), "kern_acc": float((kern == tru).mean()),
                          "kern_loose_acc": float((kl == tru).mean()), "nn1_acc": float((nn == tru).mean()),
                          "agree": float((net == kern).mean()), "kern_right_when_disagree": float((kern == tru)[dis].mean()) if dis.any() else None}
    R = res["rows"]; ks = sorted(R)
    s29 = json.loads((ROOT / "experiments" / "results" / "spike29.json").read_text())["rows"]
    res["max_abs_diff_vs_spike29_heldout"] = float(max(abs(R[k]["net_acc"] - s29[k]["heldout_acc"]) for k in ks))
    res["H30.1_rho_kernacc_netacc"] = float(spearmanr([R[k]["kern_acc"] for k in ks], [R[k]["net_acc"] for k in ks]).correlation)
    res["H30.2_mean_agreement"] = float(np.mean([R[k]["agree"] for k in ks]))
    res["H30.3_rho_lambda_agreement"] = float(spearmanr([R[k]["lambda"] for k in ks], [R[k]["agree"] for k in ks]).correlation)
    res["H30.4_kernel_right_when_disagree_pooled"] = pooled_kern_right / pooled_dis if pooled_dis else None
    res["pooled_disagreements"] = pooled_dis
    res["rho_kernloose_netacc"] = float(spearmanr([R[k]["kern_loose_acc"] for k in ks], [R[k]["net_acc"] for k in ks]).correlation)
    OUT.write_text(json.dumps(res, indent=1))
    for k in ks:
        r = R[k]; print(f"{k:10s} lam={r['lambda']:6.2f} net={r['net_acc']:.3f} kern={r['kern_acc']:.3f} kloose={r['kern_loose_acc']:.3f} nn1={r['nn1_acc']:.3f} agree={r['agree']:.3f} kR|dis={r['kern_right_when_disagree']}")
    print({k: v for k, v in res.items() if k != "rows"})


if __name__ == "__main__":
    run(sys.argv[2]) if sys.argv[1] == "run" else analyse()
