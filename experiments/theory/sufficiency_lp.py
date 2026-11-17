"""C31''' check: for each readout, which sets of irreducible constituents are (i) faithful and
(ii) sufficient for a threshold readout of every output coset? Features of state g in irrep rho are
the isotypic projection P_rho e_g of the regular-representation basis vector (matrix coefficients)."""
import itertools, json, os, numpy as np
from scipy.optimize import linprog
import experiments.spike60 as S
from experiments.spike58 import comp, inv

def iso_features(G, chi):
    n = len(G); idx = {g: i for i, g in enumerate(G)}
    d = chi(G[0])
    P = np.zeros((n, n))                       # P = (d/|G|) sum_x chi(x) L(x)  (left regular)
    for x in G:
        c = chi(x)
        if c == 0: continue
        for g in G: P[idx[comp(x, g)], idx[g]] += d / n * c
    U, s, _ = np.linalg.svd(P); r = int((s > 1e-8).sum())
    return (U[:, :r].T @ P).T                  # n x r coordinates of P e_g

def separable(F, y):
    """exists w,b: (2y-1)(Fw+b) >= 1"""
    n, m = F.shape; s = 2 * y - 1
    A = -(s[:, None] * np.c_[F, np.ones(n)]); b = -np.ones(n)
    res = linprog(np.zeros(m + 1), A_ub=A, b_ub=b, bounds=[(None, None)] * (m + 1), method="highs")
    return res.status == 0

def faithful(G, chis):
    e = G[0]
    ker = [x for x in G if all(abs(chi(x) - chi(e)) < 1e-9 for chi in chis)]
    return len(ker) == 1

if __name__ == "__main__":
    out = {}
    for name in S.AUTOMATA:
        G, H, cos, lab = S.setup(name); tab, mf = S.irreps(name)
        feats = {k: iso_features(G, f) for k, f in tab}
        rows = {}
        for r in range(1, len(tab) + 1):
            for sub in itertools.combinations([k for k, _ in tab], r):
                F = np.concatenate([feats[k] for k in sub], 1)
                sep = all(separable(F, np.array([lab[g] == c for g in G], float)) for c in range(len(cos)))
                fa = faithful(G, [f for k, f in tab if k in sub])
                dim = sum(int(round(tab[[k for k, _ in tab].index(k)][1](G[0]))) for k in sub)
                rows["+".join(sub)] = {"faithful": fa, "readout_separable": sep, "dim": dim}
        ok = [k for k, v in rows.items() if v["faithful"] and v["readout_separable"]]
        best = min(ok, key=lambda k: rows[k]["dim"]) if ok else None
        out[name] = {"candidates": rows, "C31'''_prediction_any_irreps": best,
                     "minimal_ok_all": sorted([k for k in ok if rows[k]["dim"] == rows[best]["dim"]]) if best else []}
        print(name, "→", out[name]["minimal_ok_all"], {k: v for k, v in rows.items() if "+" not in k})
    json.dump(out, open(os.path.join(S.ROOT, "results", "theory_sufficiency_lp.json"), "w"), indent=1)
