"""Spike 68: C34 in context: shape, common frame and raw axes across 5 small models,
with a tied-basis control (base vs instruct). See SPIKE_68_REPORT.md."""
import itertools, json, os, shutil, sys
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike68_raw")
OUT = os.path.join(ROOT, "results", "spike68.json")
CACHE = os.path.expanduser("~/.cache/semplex-s68")
MODELS = ["Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B-Instruct", "HuggingFaceTB/SmolLM2-360M", "EleutherAI/pythia-410m", "openai-community/gpt2"]
TIED = ("Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-0.5B-Instruct")
TPL = ["I saw a {w} yesterday.", "There is a {w} on the table.", "She talked about the {w}.", "A picture of a {w}.", "We need a {w} now."]


def concepts():
    from experiments.spike53 import fetch_meta, DATA
    from transformers import AutoTokenizer
    import pandas as pd
    fetch_meta()
    m = pd.read_csv(os.path.join(DATA, "concepts-metadata_things.tsv"), sep="\t")
    words = sorted({str(w) for w in m["Word"] if str(w).isalpha() and str(w).islower()})
    toks = [AutoTokenizer.from_pretrained(r, cache_dir=CACHE) for r in MODELS]
    ok = [w for w in words if all(len(t.encode(" " + w, add_special_tokens=False)) == 1 for t in toks)]
    return ok[:300]


def reps(repo, words):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    torch.set_num_threads(os.cpu_count())
    tok = AutoTokenizer.from_pretrained(repo, cache_dir=CACHE)
    model = AutoModelForCausalLM.from_pretrained(repo, cache_dir=CACHE, torch_dtype=torch.float32).eval()
    L = model.config.num_hidden_layers; layer = int(round(0.6 * L))
    tid = {w: tok.encode(" " + w, add_special_tokens=False)[0] for w in words}
    V = []
    with torch.no_grad():
        for w in words:
            acc = []
            for t in TPL:
                ids = tok(t.format(w=w), return_tensors="pt").input_ids
                pos = (ids[0] == tid[w]).nonzero()[0, 0]
                h = model(ids, output_hidden_states=True).hidden_states[layer][0, pos]
                acc.append(h.float().numpy())
            V.append(np.mean(acc, 0))
    return np.array(V), layer


def run():
    os.makedirs(RAW, exist_ok=True)
    wp = os.path.join(RAW, "words.json")
    if not os.path.exists(wp):
        json.dump(concepts(), open(wp, "w"))
    words = json.load(open(wp))
    for repo in MODELS:
        p = os.path.join(RAW, repo.replace("/", "__") + ".npz")
        if os.path.exists(p): continue
        V, layer = reps(repo, words)
        np.savez_compressed(p, V=V.astype(np.float32), layer=layer)
        shutil.rmtree(os.path.join(CACHE, "models--" + repo.replace("/", "--")), ignore_errors=True)
        print(repo, V.shape, "layer", layer, flush=True)


def prep(V):
    V = V - V.mean(0); return V / np.linalg.norm(V, axis=1, keepdims=True)


def cka(X, Y):
    X = X - X.mean(0); Y = Y - Y.mean(0)
    return float(np.linalg.norm(X.T @ Y) ** 2 / (np.linalg.norm(X.T @ X) * np.linalg.norm(Y.T @ Y)))


def axis_stat(X, Y):
    z = lambda M: (M - M.mean(0)) / (M.std(0) + 1e-12)
    C = np.abs(z(X).T @ z(Y)) / X.shape[0]
    return float(0.5 * (C.max(1).mean() + C.max(0).mean()))


def procrustes_r2(X, Y, rng, k=64):
    def pca(M):
        U, s, _ = np.linalg.svd(M - M.mean(0), full_matrices=False); return U[:, :k] * s[:k]
    A, B = pca(X), pca(Y); n = len(A); p = rng.permutation(n); f, t = p[: int(0.8 * n)], p[int(0.8 * n):]
    U, _, Vt = np.linalg.svd(A[f].T @ B[f]); R = U @ Vt
    return float(1 - np.linalg.norm(A[t] @ R - B[t]) ** 2 / np.linalg.norm(B[t] - B[t].mean(0)) ** 2)


def analyse():
    rng = np.random.default_rng(6800)
    V = {m: prep(np.load(os.path.join(RAW, m.replace("/", "__") + ".npz"))["V"].astype(np.float64)) for m in MODELS}
    res = []
    for a, b in itertools.combinations(MODELS, 2):
        obs = axis_stat(V[a], V[b]); sh = axis_stat(V[a], V[b][rng.permutation(len(V[b]))])
        res.append({"pair": [a, b], "tied": {a, b} == set(TIED), "cka": cka(V[a], V[b]),
                    "procrustes_r2": procrustes_r2(V[a], V[b], rng), "axis": obs, "axis_shuffled": sh, "axis_excess": obs - sh})
    un = [r for r in res if not r["tied"]]; tied = [r for r in res if r["tied"]][0]
    mc = float(np.median([r["cka"] for r in un])); mp = float(np.median([r["procrustes_r2"] for r in un]))
    ex = [r["axis_excess"] for r in un]
    v = {"H68.1": "HELD" if mc >= 0.5 else "BROKEN" if mc < 0.25 else "NEITHER",
         "H68.2": "HELD" if tied["axis_excess"] >= 3 * max(ex) else "BROKEN" if tied["axis_excess"] <= float(np.median(ex)) else "NEITHER",
         "H68.3": "HELD" if mp >= 0.3 else "BROKEN" if mp < 0.1 else "NEITHER"}
    out = {"verdicts": v, "median_cka_unrelated": mc, "median_procrustes_unrelated": mp, "tied": tied,
           "max_unrelated_axis_excess": float(max(ex)), "median_unrelated_axis_excess": float(np.median(ex)), "pairs": res,
           "n_words": len(json.load(open(os.path.join(RAW, "words.json"))))}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps({k: v for k, v in out.items() if k != "pairs"}, indent=1, default=str))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
