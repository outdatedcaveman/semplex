"""Spike 64: holonomy of Procrustes alignments between 14 models' lexicons (sheaf/frame obstruction).
Uses Spike 61's rows. See SPIKE_64_REPORT.md."""
import itertools, json, os, sys
import numpy as np
from experiments.spike53 import MODELS

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW61 = os.path.join(ROOT, "results", "spike61_raw")
OUT = os.path.join(ROOT, "results", "spike64.json")
D, SEED = 128, 6400


def load(m):
    X = np.load(os.path.join(RAW61, m.replace("/", "__") + ".npz"))["X"].astype(np.float64)
    X = X - X.mean(0); X = X / np.linalg.norm(X, axis=1, keepdims=True)
    U, s, Vt = np.linalg.svd(X, full_matrices=False)
    return U[:, :D] * s[:D]


def procrustes(A, B):
    U, _, Vt = np.linalg.svd(A.T @ B)
    return U @ Vt


def run():
    rng = np.random.default_rng(SEED)
    X = {m: load(m) for m in MODELS}
    n = next(iter(X.values())).shape[0]
    perm = rng.permutation(n); fit, test = perm[: int(0.8 * n)], perm[int(0.8 * n):]
    h1, h2 = fit[: len(fit) // 2], fit[len(fit) // 2:]
    R, delta, r2 = {}, {}, {}
    for a, b in itertools.permutations(MODELS, 2):
        R[a, b] = procrustes(X[a][fit], X[b][fit])
        r2[a, b] = float(1 - np.linalg.norm(X[a][test] @ R[a, b] - X[b][test]) ** 2 / np.linalg.norm(X[b][test]) ** 2)
        R1, R2 = procrustes(X[a][h1], X[b][h1]), procrustes(X[a][h2], X[b][h2])
        delta[a, b] = float(np.linalg.norm(R1 - R2) / np.sqrt(2 * D))
    tri = []
    for a, b, c in itertools.combinations(MODELS, 3):
        M = R[a, b] @ R[b, c] @ R[c, a]
        h = float(np.linalg.norm(M - np.eye(D)) / np.sqrt(2 * D))
        nu = float(np.sqrt(delta[a, b] ** 2 + delta[b, c] ** 2 + delta[c, a] ** 2))
        tri.append({"triangle": [a, b, c], "holonomy": h, "noise": nu, "ratio": h / nu,
                    "diag_low": float(np.mean(np.diag(M)[:16])), "diag_high": float(np.mean(np.diag(M)[-16:]))})
    f1 = float(np.mean([t["ratio"] >= 2 for t in tri])); f1b = float(np.mean([t["ratio"] <= 1.2 for t in tri]))
    med_r2 = float(np.median(list(r2.values())))
    v = {"H64.1": "HELD" if f1 >= 0.8 else "BROKEN" if f1b >= 0.5 else "NEITHER",
         "H64.2": "HELD" if med_r2 >= 0.30 else "BROKEN" if med_r2 < 0.10 else "NEITHER"}
    out = {"verdicts": v, "frac_ratio_ge_2": f1, "frac_ratio_le_1.2": f1b, "median_ratio": float(np.median([t["ratio"] for t in tri])),
           "median_holonomy": float(np.median([t["holonomy"] for t in tri])), "median_noise": float(np.median([t["noise"] for t in tri])),
           "median_heldout_r2": med_r2, "min_r2": float(min(r2.values())), "max_r2": float(max(r2.values())),
           "median_diag_low": float(np.median([t["diag_low"] for t in tri])), "median_diag_high": float(np.median([t["diag_high"] for t in tri])),
           "triangles": tri}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "triangles"}, indent=1))


if __name__ == "__main__":
    run()
