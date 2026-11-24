"""Spike 47 (pre-registered in SPIKE_47_REPORT.md): constrained collapse onto a minimum circuit's cells.

  python -m experiments.spike47 run
  python -m experiments.spike47 analyse
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

from cerp import orbits

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "experiments" / "results" / "spike47_raw"
OUT = ROOT / "experiments" / "results" / "spike47.json"
G9 = ROOT / "experiments" / "results" / "g9_orbits.json"
n, K, M, SEEDS, SEED = 4, 16, 8, 10, 4_700
CK = (30, 100, 300, 1000, 3000)
P = np.array([[(x >> i) & 1 for i in range(n)] for x in range(K)])
XS = (2 * P - 1).astype(np.float32)
FULL = (1 << K) - 1


def targets():
    d = json.loads(G9.read_text())["dims"]["4"]["classes"]
    return [c for c in d if c["cost"] == 3]


def unoriented_ltfs():
    """Non-constant 4-input threshold functions, one per complement pair, as 0/1 arrays over the 16 inputs."""
    _, tabs = orbits.ltfs_with_bound(n, 3)
    reps = sorted({min(t, FULL ^ t) for t in tabs if t not in (0, FULL)})
    return reps, np.array([[(t >> x) & 1 for x in range(K)] for t in reps], dtype=np.float64)


def min_circuits(f, reps, G):
    """Pairs (i < j) of unoriented LTFs whose cell pattern determines f through a 2-input threshold gate."""
    fv = np.array([(f >> x) & 1 for x in range(K)])
    out = []
    Gi = G.astype(int)
    for i in range(len(reps)):
        gi = Gi[i]
        for j in range(i + 1, len(reps)):
            cell = 2 * gi + Gi[j]; val = {}
            ok = True
            for c, v in zip(cell, fv):
                if val.setdefault(int(c), int(v)) != int(v):
                    ok = False; break
            if not ok:
                continue
            # realizable by a threshold gate on (g_i, g_j): some completion of the 2-bit table is not XOR/XNOR
            good = False
            for fill in range(16):
                tb = [val.get(c, (fill >> c) & 1) for c in range(4)]
                if tb not in ([0, 1, 1, 0], [1, 0, 0, 1]):
                    good = True; break
            if good:
                out.append((i, j))
    return out


def run():
    T = targets(); B = len(T) * SEEDS
    Y = np.array([[(t["rep"] >> x) & 1 for x in range(K)] for t in T for _ in range(SEEDS)], dtype=np.float32)
    rng = np.random.default_rng(SEED); lr = 0.03
    p = {"W1": rng.normal(0, 0.5, (B, M, n)).astype(np.float32), "b1": rng.normal(0, 0.5, (B, M)).astype(np.float32),
         "W2": rng.normal(0, 0.5, (B, M)).astype(np.float32), "b2": np.zeros(B, np.float32)}
    mo = {k: np.zeros_like(v) for k, v in p.items()}; ve = {k: np.zeros_like(v) for k, v in p.items()}
    snap = {}
    for t in range(1, 3001):
        pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
        h = np.tanh(pre); z = np.einsum("bxh,bh->bx", h, p["W2"]) + p["b2"][:, None]
        dz = (1 / (1 + np.exp(-np.clip(z, -60, 60))) - Y) / K
        g = {"W2": np.einsum("bx,bxh->bh", dz, h), "b2": dz.sum(1)}
        dh = dz[:, :, None] * p["W2"][:, None, :] * (1 - h * h)
        g["W1"] = np.einsum("bxh,xn->bhn", dh, XS); g["b1"] = dh.sum(1)
        for k in p:
            mo[k] = 0.9 * mo[k] + 0.1 * g[k]; ve[k] = 0.999 * ve[k] + 0.001 * g[k] ** 2
            p[k] = p[k] - lr * (mo[k] / (1 - 0.9 ** t)) / (np.sqrt(ve[k] / (1 - 0.999 ** t)) + 1e-8) - lr * 0.03 * p[k]
        if t in CK:
            for k in p:
                snap[f"{k}_{t}"] = p[k].copy()
    pre = np.einsum("bhn,xn->bxh", p["W1"], XS) + p["b1"][:, None, :]
    out = (np.einsum("bxh,bh->bx", np.tanh(pre), p["W2"]) + p["b2"][:, None]) >= 0
    fit = (out == Y.astype(bool)).all(1)
    RAW.mkdir(parents=True, exist_ok=True); np.savez_compressed(RAW / "nets.npz", fit=fit, **snap)
    print("fit", float(fit.mean()), flush=True)


def reps_at(D, t, b, weighted=True):
    h = np.tanh(XS @ D[f"W1_{t}"][b].T + D[f"b1_{t}"][b]).astype(np.float64)
    return h * D[f"W2_{t}"][b].astype(np.float64) if weighted else h


def cr_pairs(Z, G, N11, sub=None):
    """Variance of Z explained by the cell partition of each pair of rows of G. Returns a (len, len) matrix,
    or a vector for the listed pairs `sub`."""
    Zc = Z - Z.mean(0); tot = (Zc ** 2).sum()
    A = G @ Zc; S = Zc.sum(0)                                   # S is 0 after centring; kept for clarity
    n1 = G.sum(1)
    if sub is not None:
        I, J = sub[:, 0], sub[:, 1]
        Bij = np.einsum("px,px,xk->pk", G[I], G[J], Zc); n11 = N11[I, J]; Ai, Aj = A[I], A[J]; ni, nj = n1[I], n1[J]
    else:
        Bij = np.einsum("ix,jx,xk->ijk", G, G, Zc); n11 = N11; Ai, Aj = A[:, None, :], A[None, :, :]; ni, nj = n1[:, None], n1[None, :]
    cells = ((Bij, n11), (Ai - Bij, ni - n11), (Aj - Bij, nj - n11), (S - Ai - Aj + Bij, K - ni - nj + n11))
    ex = 0
    for s, c in cells:
        ex = ex + np.where(c > 0, (s ** 2).sum(-1) / np.maximum(c, 1), 0.0)
    return ex / tot if tot > 0 else ex * 0


def analyse():
    T = targets(); reps, G = unoriented_ltfs(); N11 = G @ G.T; L = len(reps)
    D = np.load(RAW / "nets.npz"); fit = D["fit"]
    mc = [min_circuits(t["rep"], reps, G) for t in T]
    mism = [(t["rep_hex"], len(c), t["num_circuits"]) for t, c in zip(T, mc) if len(c) != t["num_circuits"]]
    iu = np.triu_indices(L, 1)
    res = {"n_targets": len(T), "n_unoriented_ltfs": L, "n_pairs": int(len(iu[0])), "fit": float(fit.mean()),
           "enumeration_mismatches": mism[:10], "n_mismatch": len(mism),
           "chance_top_is_min": float(np.mean([len(c) for c in mc]) / len(iu[0]))}
    rows = []
    for i, t in enumerate(T):
        sub = np.array(mc[i]); keyset = {a * L + b for a, b in mc[i]}
        for s in range(SEEDS):
            b = i * SEEDS + s
            if not fit[b]:
                continue
            r = {"target": t["rep_hex"], "one_orbit": t["num_orbits"] == 1}
            for tt in CK:
                r[f"cr_min_{tt}"] = float(cr_pairs(reps_at(D, tt, b), G, N11, sub).max())
            Z = reps_at(D, 3000, b); allcr = cr_pairs(Z, G, N11)[iu]; top = int(np.argmax(allcr))
            r["cr_best"] = float(allcr[top]); r["top_is_min"] = bool(int(iu[0][top]) * L + int(iu[1][top]) in keyset)
            r["rank_of_best_min"] = int((allcr > r["cr_min_3000"] + 1e-12).sum()) + 1
            fv = np.array([[(t["rep"] >> x) & 1 for x in range(K)]], dtype=np.float64)
            Zc = Z - Z.mean(0); m1 = fv[0] == 1
            r["cr_class"] = float((((Zc[m1].sum(0)) ** 2).sum() / m1.sum() + ((Zc[~m1].sum(0)) ** 2).sum() / (~m1).sum()) / (Zc ** 2).sum())
            Hh = reps_at(D, 3000, b, weighted=False); hcr = cr_pairs(Hh, G, N11)[iu]
            r["raw_cr_min"] = float(cr_pairs(Hh, G, N11, sub).max()); r["raw_top_is_min"] = bool(int(iu[0][int(np.argmax(hcr))]) * L + int(iu[1][int(np.argmax(hcr))]) in keyset)
            rows.append(r)
        if i % 16 == 0:
            print("target", i, flush=True)
    (RAW / "rows.json").write_text(json.dumps(rows))
    a = lambda k: np.array([r[k] for r in rows], dtype=float)
    res.update({"n_nets": len(rows), "frac_cr_min_ge_0.90": float((a("cr_min_3000") >= 0.90).mean()), "frac_top_is_min": float(a("top_is_min").mean()),
                "median_cr_min": {str(t): float(np.median(a(f"cr_min_{t}"))) for t in CK}, "median_cr_best": float(np.median(a("cr_best"))),
                "median_cr_class": float(np.median(a("cr_class"))), "median_rank_of_best_min": float(np.median(a("rank_of_best_min"))),
                "frac_rank_le_10": float((a("rank_of_best_min") <= 10).mean()),
                "raw": {"frac_cr_min_ge_0.90": float((a("raw_cr_min") >= 0.90).mean()), "frac_top_is_min": float(a("raw_top_is_min").mean()), "median_cr_min": float(np.median(a("raw_cr_min")))},
                "by_orbits": {k: {"n": int(m.sum()), "median_cr_min": float(np.median(a("cr_min_3000")[m])), "frac_top_is_min": float(a("top_is_min")[m].mean())}
                              for k, m in (("one_orbit", a("one_orbit") == 1), ("several_orbits", a("one_orbit") == 0))}})
    ok = res["fit"] >= 0.90 and res["n_mismatch"] == 0
    d3 = res["median_cr_min"]["3000"] - res["median_cr_min"]["100"]
    res["H47.1"] = "NO VERDICT" if not ok else "HELD" if res["frac_cr_min_ge_0.90"] >= 0.70 else "BROKEN" if res["frac_cr_min_ge_0.90"] < 0.40 else "NEITHER"
    res["H47.2"] = "NO VERDICT" if not ok else "HELD" if res["frac_top_is_min"] >= 0.60 else "BROKEN" if res["frac_top_is_min"] < 0.30 else "NEITHER"
    res["H47.3"] = "NO VERDICT" if not ok else "HELD" if d3 >= 0.10 else "BROKEN" if d3 <= 0.02 else "NEITHER"
    res["H47.3_measured"] = d3
    OUT.write_text(json.dumps(res, indent=1)); print(json.dumps({k: v for k, v in res.items() if k != "enumeration_mismatches"}, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
