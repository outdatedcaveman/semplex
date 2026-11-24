"""Spike 61: data-driven lexical atoms shared across 14 models (sparse vs dense matching).
Rows read from published safetensors (cerp/hfrows.py); no model run. See SPIKE_61_REPORT.md."""
import itertools, json, os, sys
import numpy as np
from cerp import hfrows
from experiments.spike53 import MODELS

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike61_raw")
OUT = os.path.join(ROOT, "results", "spike61.json")
K, NNZ, REF = 256, 5, "openai-community/gpt2"


def single(tok, w):
    e = tok.encode(" " + w, add_special_tokens=False).ids
    return e[0] if len(e) == 1 else None


def shared_words():
    toks = {m: hfrows.tokenizer(m) for m in MODELS}
    words = open(os.path.join(ROOT, "data", "google-10000-english-no-swears.txt")).read().split()
    return [w for w in words if w.isalpha() and len(w) >= 2 and all(single(toks[m], w) is not None for m in MODELS)], toks


def run():
    os.makedirs(RAW, exist_ok=True)
    words, toks = shared_words()
    json.dump(words, open(os.path.join(RAW, "words.json"), "w"))
    for m in MODELS:
        p = os.path.join(RAW, m.replace("/", "__") + ".npz")
        if os.path.exists(p): continue
        e, _, _ = hfrows.matrices(m)
        X = hfrows.rows(m, e, [single(toks[m], w) for w in words])
        np.savez_compressed(p, X=X.astype(np.float32))
        print(m, X.shape, flush=True)


def decompose(X, seed=0):
    from sklearn.decomposition import MiniBatchDictionaryLearning, PCA
    from sklearn.linear_model import orthogonal_mp
    X = X - X.mean(0); X = X / np.linalg.norm(X, axis=1, keepdims=True)
    dl = MiniBatchDictionaryLearning(n_components=K, alpha=1.0, batch_size=256, max_iter=30, random_state=seed)
    dl.fit(X)
    D = dl.components_; D = D / np.linalg.norm(D, axis=1, keepdims=True)
    A = orthogonal_mp(D.T, X.T, n_nonzero_coefs=NNZ).T          # words x K
    P = PCA(n_components=K, random_state=seed).fit_transform(X)
    return A, P


def match(A, B):
    from scipy.optimize import linear_sum_assignment
    def z(M):
        M = M - M.mean(0); s = np.linalg.norm(M, axis=0); s[s == 0] = 1; return M / s
    C = np.abs(z(A).T @ z(B))
    r, c = linear_sum_assignment(-C)
    return C[r, c], c


def analyse():
    words = json.load(open(os.path.join(RAW, "words.json")))
    codes, pcs = {}, {}
    for m in MODELS:
        X = np.load(os.path.join(RAW, m.replace("/", "__") + ".npz"))["X"].astype(np.float64)
        codes[m], pcs[m] = decompose(X)
        print("decomposed", m, flush=True)
    pairs = list(itertools.combinations(MODELS, 2))
    res = []
    for a, b in pairs:
        sa, _ = match(codes[a], codes[b]); da, _ = match(pcs[a], pcs[b])
        res.append({"pair": [a, b], "sparse": float(sa.mean()), "dense": float(da.mean())})
    rng = np.random.default_rng(6100)
    a, b = MODELS[0], MODELS[1]
    null = float(match(codes[a], codes[b][rng.permutation(len(words))])[0].mean())
    # universal atoms of the reference model
    best = {}                     # ref atom -> list of (model, corr, matched atom)
    for m in MODELS:
        if m == REF: continue
        corr, col = match(codes[REF], codes[m])
        for k in range(K):
            best.setdefault(k, []).append((m, float(corr[k]), int(col[k])))
    universal = [k for k in range(K) if sum(c >= 0.5 for _, c, _ in best[k]) >= 10]
    A = codes[REF]
    atoms = []
    for k in universal:
        top = np.argsort(-np.abs(A[:, k]))[:10]
        atoms.append({"atom": k, "n_models_ge_0.5": sum(c >= 0.5 for _, c, _ in best[k]),
                      "median_corr": float(np.median([c for _, c, _ in best[k]])), "top_words": [words[i] for i in top],
                      "signs": [int(np.sign(A[i, k])) for i in top]})
    atoms.sort(key=lambda x: -x["median_corr"])
    f1 = float(np.mean([r["sparse"] - r["dense"] >= 0.05 for r in res]))
    f1b = float(np.mean([r["sparse"] <= r["dense"] for r in res]))
    frac_u = len(universal) / K
    v = {"H61.1": "HELD" if f1 >= 0.75 else "BROKEN" if f1b >= 0.5 else "NEITHER",
         "H61.2": "HELD" if frac_u >= 0.25 else "BROKEN" if frac_u < 0.05 else "NEITHER"}
    if len(words) < 2000:
        v = {k: "NO VERDICT" for k in v}
    formulas = {}
    for w in ["king", "queen", "water", "money", "love", "running", "happy", "january", "three", "red", "doctor", "fear", "justice", "dog", "computer"]:
        if w in words:
            i = words.index(w); nz = np.nonzero(A[i])[0]
            formulas[w] = sorted([(int(k), round(float(A[i, k]), 3), k in universal) for k in nz], key=lambda t: -abs(t[1]))
    out = {"verdicts": v, "n_words": len(words), "frac_pairs_sparse_beats_dense_by_0.05": f1, "frac_pairs_sparse_le_dense": f1b,
           "median_sparse": float(np.median([r["sparse"] for r in res])), "median_dense": float(np.median([r["dense"] for r in res])),
           "shuffle_null_sparse": null, "n_universal": len(universal), "frac_universal": frac_u,
           "universal_atoms": atoms, "reference_atom_matches": {str(k): best[k] for k in universal},
           "formulas": formulas, "pairs": res}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
