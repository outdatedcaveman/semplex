"""Spike 31 (pre-registered in SPIKE_31_REPORT.md): Walsh-degree spectral bias of the initial NTK.

  python -m experiments.spike31
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib

import numpy as np
from scipy.stats import spearmanr

from cerp import train
from experiments import spike14 as S14, spike29 as S29, spike30 as S30
from experiments.spike09 import tgt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike31.json"
XS = train.XS.astype(np.float64)
SUBSETS = [S for k in range(5) for S in itertools.combinations(range(4), k)]
CHI = np.array([[np.prod(XS[x, list(S)]) if S else 1.0 for x in range(16)] for S in SUBSETS])     # (16 chars, 16 points)
DEG = np.array([len(S) for S in SUBSETS])


def spectrum(K):
    M = CHI @ K @ CHI.T / 16                                   # Walsh-basis matrix (diagonal for distance kernels)
    off = (M ** 2).sum() - (np.diag(M) ** 2).sum()
    mu = np.array([np.diag(M)[DEG == k].mean() for k in range(5)])
    return mu, float(off / (M ** 2).sum())


def f1(mu):
    w = np.array([math.comb(4, k) * mu[k] for k in range(1, 5)])
    return float(w[0] / w.sum())


def kernel_from_mu(mu):
    return sum(mu[len(S)] * np.outer(CHI[i], CHI[i]) for i, S in enumerate(SUBSETS))


def kernel_acc(K, fs, care, T):
    right = n = 0
    for b in range(len(fs)):
        seen = np.nonzero(care[b])[0]; held = np.nonzero(~care[b])[0]
        p = S30.kernel_predict(K, seen, T[b].astype(float), 1e-3)
        right += int((p[held] == T[b, held]).sum()); n += len(held)
    return right / n


def main():
    tb, ex, els, iso = S14.setup()
    fs = np.array([e for _ in range(10) for e in els]); T = tgt(fs).astype(bool); care = S30.masks(len(fs))
    s30 = json.loads((ROOT / "experiments" / "results" / "spike30.json").read_text())["rows"]
    s29 = json.loads((ROOT / "experiments" / "results" / "spike29.json").read_text())["rows"]
    res = {"activations": {}, "synthetic": {}}
    offmax = 0.0
    for a in S29.ACTS:
        mu, off = spectrum(S30.ntk(a)); offmax = max(offmax, off)
        res["activations"][a] = {"mu": mu.tolist(), "F1": f1(mu), "offdiag_share": off, "lambda": s29[a]["lambda"],
                                 "kern_acc": s30[a]["kern_acc"], "net_acc": s29[a]["heldout_acc"]}
    E = np.zeros(5)                                            # target spectrum (energy per character, by degree)
    for e in els:
        y = np.array([1.0 if (e >> x) & 1 else -1.0 for x in range(16)])
        c = CHI @ y / 16; nc = (c[DEG > 0] ** 2).sum()
        for k in range(1, 5):
            E[k] += (c[DEG == k] ** 2).mean() / nc
    E /= len(els)
    res["target_energy_share_by_degree"] = [float(math.comb(4, k) * E[k]) for k in range(1, 5)]
    for r in (0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0):
        mu = np.array([1.0] + [r ** k for k in range(1, 5)])
        res["synthetic"][str(r)] = {"F1": f1(mu), "kern_acc": kernel_acc(kernel_from_mu(mu), fs, care, T)}
    mu_m = np.array([1.0] + list(E[1:] / E[1]))
    res["matched"] = {"mu": mu_m.tolist(), "F1": f1(mu_m), "kern_acc": kernel_acc(kernel_from_mu(mu_m), fs, care, T)}
    A = res["activations"]; ks = sorted(A)
    F = [A[k]["F1"] for k in ks]
    res["H31.1_max_offdiag_share"] = offmax
    res["H31.2_rho_F1_kernacc"] = float(spearmanr(F, [A[k]["kern_acc"] for k in ks]).correlation)
    res["H31.3_rho_F1_netacc"] = float(spearmanr(F, [A[k]["net_acc"] for k in ks]).correlation)
    un = [A[k]["F1"] for k in ks if A[k]["lambda"] <= 3]; ti = [A[k]["F1"] for k in ks if A[k]["lambda"] >= 7]
    res["H31.4_meanF1_untilted_minus_tilted"] = float(np.mean(un) - np.mean(ti))
    seq = [res["synthetic"][str(r)]["kern_acc"] for r in (0.3, 0.5, 0.7, 1.0, 1.5, 2.0)]
    res["H31.5_inversions_r_ge_0.3"] = int(sum(seq[i + 1] > seq[i] for i in range(len(seq) - 1)))
    res["H31.5_acc_r1_minus_r0.3"] = res["synthetic"]["1.0"]["kern_acc"] - res["synthetic"]["0.3"]["kern_acc"]
    best = max(A[k]["kern_acc"] for k in ks)
    res["H31.6_matched_minus_best_activation"] = res["matched"]["kern_acc"] - best
    OUT.write_text(json.dumps(res, indent=1))
    for k in sorted(ks, key=lambda k: -A[k]["F1"]):
        print(f"{k:10s} F1={A[k]['F1']:.3f} kern={A[k]['kern_acc']:.3f} net={A[k]['net_acc']:.3f} lam={A[k]['lambda']:.2f}")
    print("synthetic", {r: (round(v["F1"], 3), round(v["kern_acc"], 3)) for r, v in res["synthetic"].items()})
    print("matched", round(res["matched"]["F1"], 3), round(res["matched"]["kern_acc"], 3), "target share by degree", [round(x, 3) for x in res["target_energy_share_by_degree"]])
    print({k: v for k, v in res.items() if k.startswith("H31")})


if __name__ == "__main__":
    main()
