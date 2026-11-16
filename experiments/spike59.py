"""Spike 59: semantic primes as elements of the lexicon (spanning and universality),
in 14 open models' embedding weights read row by row. See SPIKE_59_REPORT.md."""
import itertools, json, os, sys
import numpy as np
from cerp import hfrows
from experiments.spike53 import MODELS, model_matrices, fetch_meta, DATA

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike59_raw")
OUT = os.path.join(ROOT, "results", "spike59.json")
PRIMES = ("i you someone something thing people body kind part this same other one two some all much many little few "
          "good bad big small think know want feel see hear say words true do happen move be mine live die when time now "
          "before after long short moment where place here above below far near side inside touch not maybe can because if "
          "very more like way").split()
ABSTRACT = ("justice freedom anger fear love hate hope shame pride guilt joy grief envy trust idea belief promise lie truth "
            "gift friend enemy help harm power rule law right duty fault blame praise reason cause chance risk danger safety "
            "peace war beauty health wealth poverty success failure mistake secret memory dream plan choice goal need value "
            "price debt loss victory rest").split()
SEED, N_RAND, K, WIN = 5900, 20, 8, 100


def things_words():
    import pandas as pd
    fetch_meta()
    m = pd.read_csv(os.path.join(DATA, "concepts-metadata_things.tsv"), sep="\t")
    return sorted({str(w) for w in m["Word"] if str(w).isalpha() and str(w).islower()})


def single(tok, w):
    e = tok.encode(" " + w, add_special_tokens=False).ids
    return e[0] if len(e) == 1 else None


def build(repo, tok, rng):
    """ids for primes, targets, and matched random dictionaries"""
    pr = {w: single(tok, w) for w in PRIMES}; pr = {w: i for w, i in pr.items() if i is not None}
    excl = set(PRIMES) | set(ABSTRACT)
    conc = {w: single(tok, w) for w in things_words() if w not in excl}; conc = {w: i for w, i in conc.items() if i is not None}
    abst = {w: single(tok, w) for w in ABSTRACT}; abst = {w: i for w, i in abst.items() if i is not None}
    used = set(pr.values()) | set(conc.values()) | set(abst.values())
    words = open(os.path.join(ROOT, "data", "google-10000-english-no-swears.txt")).read().split()
    rank = {w: r for r, w in enumerate(words)}
    cand = []                                   # (rank, id) of single-token real words, not primes/targets
    for w in words:
        if w.isalpha() and len(w) >= 2 and w not in excl:
            i = single(tok, w)
            if i is not None and i not in used:
                cand.append((rank[w], i))
    cr = np.array([c[0] for c in cand]); ci = np.array([c[1] for c in cand])
    rands = []
    for _ in range(N_RAND):
        d = []
        for w, i in pr.items():
            r0 = rank[w]
            ok = np.nonzero((np.abs(cr - r0) <= WIN) & ~np.isin(ci, d))[0]
            d.append(int(ci[rng.choice(ok)]))
        rands.append(d)
    return pr, conc, abst, rands


def run():
    os.makedirs(RAW, exist_ok=True)
    rng = np.random.default_rng(SEED)
    for repo in MODELS:
        tok = hfrows.tokenizer(repo)
        pr, conc, abst, rands = build(repo, tok, rng)
        for side, tensor in model_matrices(repo):
            p = os.path.join(RAW, f"{repo.replace('/', '__')}__{side}.npz")
            if os.path.exists(p):
                continue
            ids = sorted(set(pr.values()) | set(conc.values()) | set(abst.values()) | {i for d in rands for i in d})
            M = hfrows.rows(repo, tensor, ids)
            np.savez_compressed(p, ids=np.array(ids), M=M.astype(np.float32),
                                primes=json.dumps(pr), conc=json.dumps(conc), abst=json.dumps(abst), rands=json.dumps(rands))
            print(repo, side, len(pr), len(conc), len(abst), flush=True)


def omp_r2(D, X, k):
    from sklearn.linear_model import OrthogonalMatchingPursuit
    om = OrthogonalMatchingPursuit(n_nonzero_coefs=min(k, D.shape[0]), fit_intercept=False)
    om.fit(D.T, X.T)
    coef = om.coef_.reshape(X.shape[0], -1)
    R = X - coef @ D
    return 1 - (R ** 2).sum(1) / (X ** 2).sum(1), coef


def analyse():
    rng = np.random.default_rng(SEED + 1)
    mats, sel = [], {"conc": {}, "abst": {}}
    for repo in MODELS:
        tok = hfrows.tokenizer(repo)
        for side, _ in model_matrices(repo):
            z = np.load(os.path.join(RAW, f"{repo.replace('/', '__')}__{side}.npz"), allow_pickle=False)
            ids = list(z["ids"]); M = z["M"].astype(np.float64)
            M = M - M.mean(0); M = M / np.linalg.norm(M, axis=1, keepdims=True)
            row = {i: M[j] for j, i in enumerate(ids)}
            pr, conc, abst, rands = (json.loads(str(z[k])) for k in ("primes", "conc", "abst", "rands"))
            pw = list(pr); D = np.stack([row[pr[w]] for w in pw])
            m = {"matrix": f"{repo}:{side}", "n_primes": len(pr), "n_conc": len(conc), "n_abst": len(abst)}
            m["ok"] = len(pr) >= 50 and len(conc) >= 100 and len(abst) >= 40
            for key, T in (("conc", conc), ("abst", abst)):
                tw = sorted(T); X = np.stack([row[T[w]] for w in tw])
                r2p, coef = omp_r2(D, X, K)
                rr = [omp_r2(np.stack([row[i] for i in d]), X, K)[0].mean() for d in rands]
                m[key] = {"prime_r2": float(r2p.mean()), "rand_mean": float(np.mean(rr)), "rand_sd": float(np.std(rr)),
                          "p": float(np.mean([x >= r2p.mean() for x in rr])),
                          "below_median": bool(r2p.mean() < np.median(rr)),
                          "z": float((r2p.mean() - np.mean(rr)) / (np.std(rr) + 1e-12)),
                          "r2_by_k": {kk: float(omp_r2(D, X, kk)[0].mean()) for kk in (4, 16)}}
                if m["ok"]:
                    sel[key][m["matrix"]] = {w: frozenset(pw[j] for j in np.nonzero(coef[t])[0]) for t, w in enumerate(tw)}
            mats.append(m)
    ok = [m for m in mats if m["ok"]]
    v = {}
    for key, hid in (("conc", "H59.1"), ("abst", "H59.2")):
        f = np.mean([m[key]["p"] <= 0.05 for m in ok]); fb = np.mean([m[key]["below_median"] for m in ok])
        v[hid] = "HELD" if f >= 0.75 else "BROKEN" if fb >= 0.5 else "NEITHER"
    # universality: mean pairwise overlap of the k-prime sets (all sets have k atoms, so overlap and Jaccard are monotone)
    uni = {}
    for key in ("conc", "abst"):
        S = sel[key]; mk = list(S)
        words = sorted(set.intersection(*[set(S[x]) for x in mk])) if mk else []
        B = np.zeros((len(mk), len(words), len(PRIMES)))
        for a, x in enumerate(mk):
            for t, w in enumerate(words):
                for pname in S[x][w]:
                    B[a, t, PRIMES.index(pname)] = 1
        present = [np.nonzero(B[a].sum(0))[0] for a in range(len(mk))]
        def stat(Bx):
            Ssum = Bx.sum(0)
            pair_inter = ((Ssum ** 2).sum(1) - Bx.sum((0, 2))) / 2
            return float(pair_inter.mean() / (len(mk) * (len(mk) - 1) / 2))
        obs = stat(B); null = []
        for _ in range(1000):
            Bx = B.copy()
            for a in range(len(mk)):
                cols = present[a]; Bx[a][:, cols] = B[a][:, rng.permutation(cols)]
            null.append(stat(Bx))
        uni[key] = {"n_words": len(words), "obs_mean_overlap": obs, "null_mean": float(np.mean(null)), "null_max": float(np.max(null)),
                    "p": float((1 + sum(n >= obs for n in null)) / 1001)}
        cnt = B.sum((0, 1))
        uni[key]["top_primes"] = [(PRIMES[j], int(cnt[j])) for j in np.argsort(-cnt)[:15]]
    pc, pa = uni["conc"]["p"], uni["abst"]["p"]
    v["H59.3"] = "HELD" if pc < 0.001 and pa < 0.001 else "BROKEN" if pc >= 0.05 and pa >= 0.05 else "NEITHER"
    out = {"verdicts": v, "n_matrices": len(mats), "n_ok": len(ok),
           "frac_p05": {k: float(np.mean([m[k]["p"] <= 0.05 for m in ok])) for k in ("conc", "abst")},
           "frac_below_median": {k: float(np.mean([m[k]["below_median"] for m in ok])) for k in ("conc", "abst")},
           "median_z": {k: float(np.median([m[k]["z"] for m in ok])) for k in ("conc", "abst")},
           "universality": uni, "matrices": mats}
    json.dump(out, open(OUT, "w"), indent=1, default=lambda o: sorted(o) if isinstance(o, frozenset) else str(o))
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
