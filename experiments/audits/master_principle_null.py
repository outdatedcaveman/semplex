"""Audit (2026-11-25) of the Master Principle G(lambda) evidence (claims/PROPOSED.md section 11): how high is the
Gram-matrix cosine by chance, and can the tests tell the candidate operators apart?

For each of the 12 pre-registered monoids it reports cos(G, o o^T), cos(G, Wc + Wo), cos(G, Wo), and the median and
95th percentile of cos(G, X X^T) for random centred pi-weighted Grams (2,000 draws, 64-d Gaussian centroids). Reads only
experiments/results/master_principle_predictions.json. Run: python -m experiments.audits.master_principle_null
"""
import json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cos(A, B):
    A, B = np.asarray(A, float), np.asarray(B, float)
    return float((A * B).sum() / np.linalg.norm(A) / np.linalg.norm(B))


def main(draws=2000, seed=0):
    p = json.load(open(os.path.join(ROOT, "results", "master_principle_predictions.json")))
    rng = np.random.default_rng(seed); rows = []
    for M in p["monoids"]:
        m = M["m"]; W = np.sqrt(np.array(M["pi"])); one = W / np.linalg.norm(W); C = np.eye(m) - np.outer(one, one)
        G = np.array(M["G"]); o = np.array(M["o"]); O = np.outer(o, o) if o.ndim == 1 else o
        null = [cos(G, (X := C @ (W[:, None] * rng.normal(size=(m, 64)))) @ X.T) for _ in range(draws)]
        rows.append({"id": M["id"], "m": m, "cos_G_o": cos(G, O), "cos_G_WcWo": cos(G, M["WcWo_noheat"]),
                     "cos_G_Wo": cos(G, M["Wo"]), "null_median": float(np.median(null)), "null_p95": float(np.percentile(null, 95))})
    med = {k: float(np.median([r[k] for r in rows])) for k in rows[0] if k not in ("id", "m")}
    out = {"per_monoid": rows, "median": med}
    json.dump(out, open(os.path.join(ROOT, "results", "audit_master_principle_null.json"), "w"), indent=1)
    print(json.dumps(med, indent=1))


if __name__ == "__main__":
    main()
