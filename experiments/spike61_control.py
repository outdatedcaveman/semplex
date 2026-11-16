"""Spike 61 exploratory control (after verdicts): rotation-invariant shared geometry (linear CKA)
between models on the same 6,163 words, and the distribution of the best per-atom matches (GPT-2 atoms)."""
import itertools, json, os
import numpy as np
from experiments.spike53 import MODELS
from experiments import spike61 as S

def load(m):
    X = np.load(os.path.join(S.RAW, m.replace("/", "__") + ".npz"))["X"].astype(np.float64)
    X = X - X.mean(0); return X / np.linalg.norm(X, axis=1, keepdims=True)

def cka(X, Y):
    X = X - X.mean(0); Y = Y - Y.mean(0)
    xy = np.linalg.norm(X.T @ Y) ** 2
    return float(xy / (np.linalg.norm(X.T @ X) * np.linalg.norm(Y.T @ Y)))

if __name__ == "__main__":
    Xs = {m: load(m) for m in MODELS}
    rng = np.random.default_rng(6101)
    pairs = list(itertools.combinations(MODELS, 2))
    ck = [cka(Xs[a], Xs[b]) for a, b in pairs]
    a, b = MODELS[0], MODELS[1]
    ck_null = cka(Xs[a], Xs[b][rng.permutation(len(Xs[b]))])
    A_ref, _ = S.decompose(Xs[S.REF] * 1.0)
    A_q, _ = S.decompose(Xs["Qwen/Qwen2.5-7B"] * 1.0)
    corr, _ = S.match(A_ref, A_q)
    out = {"cka_median": float(np.median(ck)), "cka_min": float(min(ck)), "cka_max": float(max(ck)), "cka_shuffle_null": ck_null,
           "gpt2_vs_qwen7b_atom_match": {"max": float(corr.max()), "p90": float(np.percentile(corr, 90)), "median": float(np.median(corr)),
                                         "n_ge_0.5": int((corr >= 0.5).sum()), "n_ge_0.3": int((corr >= 0.3).sum())}}
    json.dump(out, open(os.path.join(S.ROOT, "results", "spike61_control.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
