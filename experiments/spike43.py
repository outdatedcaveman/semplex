"""Spike 43 (pre-registered in SPIKE_43_REPORT.md): kernel-smoothed target first, Occam later? (H-J)

  python -m experiments.spike43 run A|G
  python -m experiments.spike43 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from experiments import spike36 as S36

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike43_raw"
OUT = ROOT / "experiments" / "results" / "spike43.json"
CK = (0, 1, 2, 3, 5, 10, 30, 100, 300, 1000, 3000)
n, ACT, SEEDS, M, SEED = 6, "tanh", 10, 8, 3_720


def train(opt):
    """Spike 36's `train`, step for step, with output checkpoints. opt = 'A' (AdamW, as Spike 36) or 'G' (plain GD)."""
    TK = S36.tasks(n); XS = (2 * S36.pts(n) - 1).astype(np.float32); K = 1 << n
    Y = np.array([[(f >> x) & 1 for x in range(K)] for f, _ in TK for _ in range(SEEDS)], dtype=np.float32)
    C = np.array([[(c >> x) & 1 for x in range(K)] for _, c in TK for _ in range(SEEDS)], dtype=np.float32)
    B = len(Y); rng = np.random.default_rng(SEED); lr = 0.03
    p = {"W1": rng.normal(0, 0.5, (B, M, n)).astype(np.float32), "b1": rng.normal(0, 0.5, (B, M)).astype(np.float32),
         "W2": rng.normal(0, 0.5, (B, M)).astype(np.float32), "b2": np.zeros(B, np.float32)}
    mo = {k: np.zeros_like(v) for k, v in p.items()}; ve = {k: np.zeros_like(x) for k, x in p.items()}

    def fwd():
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h, d = S36.phi(pre, ACT)
        return pre, h, d, np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]

    Z = {0: fwd()[3].copy()}
    for t in range(1, 3001):
        pre, h, d, z = fwd()
        dz = (1 / (1 + np.exp(-np.clip(z, -60, 60))) - Y) * C / C.sum(1, keepdims=True)
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * d
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            if opt == "A":
                mo[k] = 0.9 * mo[k] + 0.1 * g[k]; ve[k] = 0.999 * ve[k] + 0.001 * g[k] ** 2
                p[k] = p[k] - lr * (mo[k] / (1 - 0.9 ** t)) / (np.sqrt(ve[k] / (1 - 0.999 ** t)) + 1e-8) - lr * 0.03 * p[k]
            else:
                p[k] = p[k] - 2.0 * g[k]
        if t in CK:
            Z[t] = fwd()[3].copy()
    fit = (((Z[3000] >= 0) == Y.astype(bool)) | (C == 0)).all(1)
    return Z, fit


def run(opt):
    Z, fit = train(opt)
    RAW.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(RAW / f"arm_{opt}.npz", fit=fit, **{f"z{t}": Z[t].astype(np.float32) for t in CK})
    print("arm", opt, "fit", float(fit.mean()), flush=True)


def analyse():
    TK = S36.tasks(n); occ = json.loads((S36.RAW / "occam_n6.json").read_text()); Th = S36.ntk(n, ACT); K = 1 << n
    held = [np.array([not (c >> x) & 1 for x in range(K)]) for _, c in TK]
    truth = [np.array([(f >> x) & 1 for x in range(K)], bool) for f, _ in TK]
    kf, op, kr = [], [], []
    for (f, c), o, h in zip(TK, occ, held):
        seen = [x for x in range(K) if (c >> x) & 1]; y = np.array([(f >> x) & 1 for x in range(K)], float)
        kf.append((Th[:, seen] @ (y[seen] - 0.5) > 0)[h]); op.append((np.array(o["preds"], bool)[:, h].mean(0) > 0.5))
        kr.append(S36.kpred(Th, n, f, c)[h])
    res = {"checkpoints": list(CK)}
    for opt in ("A", "G"):
        f = RAW / f"arm_{opt}.npz"
        if not f.exists():
            continue
        D = np.load(f); fit = D["fit"]; cur = {}
        for t in CK:
            z, z0 = D[f"z{t}"], D["z0"]; AK = SO = SK = ACC = 0; nK = nC = nA = 0; P, T = [], []
            for i in range(len(TK)):
                conflict = op[i] != kf[i]
                for j in range(SEEDS):
                    b = i * SEEDS + j
                    if not fit[b]:
                        continue
                    dz = (z[b] - z0[b] > 0)[held[i]]; s = (z[b] >= 0)[held[i]]
                    AK += (dz == kf[i]).sum(); nK += len(dz)
                    SO += (dz == op[i])[conflict].sum(); nC += conflict.sum()
                    ACC += (s == op[i]).sum(); SK += (s == kr[i]).sum(); nA += len(s)
                    P.append(s); T.append(truth[i][held[i]])
            P, T = np.concatenate(P), np.concatenate(T)
            cur[str(t)] = {"A_K": AK / nK if t else None, "S": SO / nC if t else None, "agree_occam_sign_z": ACC / nA,
                           "agree_ridge_ntk_sign_z": SK / nA, "bal": float(S36.bal(P, T)), "n_conflict_points": int(nC)}
        res[opt] = {"fit": float(fit.mean()), "curve": cur}
        print(opt, "fit", round(float(fit.mean()), 4))
        for t in CK:
            print("  t", t, {k: (round(float(v), 3) if v is not None else None) for k, v in cur[str(t)].items()})
    if "A" in res:
        c = res["A"]["curve"]
        prev = json.loads((S36.RAW / "nets_n6_tanh.json").read_text())
        same = np.mean(np.array(prev["out"], bool) == (np.load(RAW / "arm_A.npz")["z3000"] >= 0))
        res["sanity_bits_equal_spike36"] = float(same)
        res["H43.1_A_K_1"] = c["1"]["A_K"]; res["H43.2_S_1"] = c["1"]["S"]; res["H43.3_S_3000_minus_S_1"] = c["3000"]["S"] - c["1"]["S"]
        res["first_t_S_ge_half"] = next((t for t in CK[1:] if c[str(t)]["S"] >= 0.5), None)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print({k: v for k, v in res.items() if k.startswith(("H43", "sanity", "first"))})


if __name__ == "__main__":
    a = sys.argv
    {"run": lambda: run(a[2]), "analyse": analyse}[a[1]]()
