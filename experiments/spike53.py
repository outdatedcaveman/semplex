"""Spike 53: symmetry group -> geometry (C29) in open-model weights and THINGS-fMRI.

See experiments/SPIKE_53_REPORT.md. Model weights are read row by row from the
published safetensors files (cerp/hfrows.py); no model is run. Brain data are
the THINGS-fMRI single-trial betas (figshare 10.25452/figshare.plus.20492835).
Downloaded files are data only: CSV, TSV, JSON headers, HDF5 arrays.
"""
import io, json, os, sys, time, urllib.request, zipfile
import numpy as np

from cerp import hfrows

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "spike53.json")
RAW = os.path.join(ROOT, "results", "spike53_raw")
DATA = os.environ.get("SPIKE53_DATA", os.path.expanduser("~/.cache/semplex-things"))
ZIP = "https://ndownloader.figshare.com/files/43635873"
CAT27 = "https://osf.io/download/5mvxh/"
CONCEPTS = "https://osf.io/download/um6a9/"

MODELS = ["openai-community/gpt2", "EleutherAI/pythia-410m", "EleutherAI/pythia-6.9b",
          "Qwen/Qwen2.5-0.5B", "Qwen/Qwen2.5-7B", "mistralai/Mistral-7B-v0.1",
          "allenai/OLMo-2-1124-7B", "HuggingFaceTB/SmolLM2-360M", "tiiuae/falcon-7b",
          "microsoft/phi-2", "bigscience/bloom-560m", "stabilityai/stablelm-2-1_6b",
          "01-ai/Yi-6B", "internlm/internlm2_5-7b"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
FAMILIES = {"weekdays": DAYS, "months": MONTHS, "month_abbr": [m[:3] for m in MONTHS]}
PRODUCTS = {"month_x_form": (MONTHS, [m[:3] for m in MONTHS]),
            "weekday_x_form": (DAYS, [d[:3] for d in DAYS])}
ROIS = ["lLOC", "rLOC", "IT", "lFFA", "rFFA", "lPPA", "rPPA", "lEBA", "rEBA", "lOFA", "rOFA"]
NC_MIN = 10.0
SEED = 5300
N_PERM_FAM, N_PERM_HIER = 10000, 2000


# ---------------------------------------------------------------- statistics
def gram(X):
    X = X - X.mean(0)
    X = X / np.linalg.norm(X, axis=1, keepdims=True)
    return X @ X.T


def orbit_r2(G, orbit):
    """share of off-diagonal variance of G explained by averaging over orbits
    (orbit[i, j] = integer orbit id of the pair)"""
    n = len(G)
    iu = np.triu_indices(n, 1)
    g, o = G[iu], orbit[iu]
    k = o.max() + 1
    s = np.bincount(o, g, k)
    c = np.bincount(o, minlength=k)
    gh = (s / np.maximum(c, 1))[o]
    tot = ((g - g.mean()) ** 2).sum()
    return 1 - ((g - gh) ** 2).sum() / tot


def cyc_orbit(n):
    i = np.arange(n)
    d = np.abs(i[:, None] - i[None, :])
    return np.minimum(d, n - d)


def block_orbit(lab):
    m = lab.max() + 1
    a, b = np.minimum(lab[:, None], lab[None, :]), np.maximum(lab[:, None], lab[None, :])
    return a * m + b


def perm_p(G, orbit_fn, labels, n_perm, rng):
    obs = orbit_r2(G, orbit_fn(labels))
    ge = 0
    for _ in range(n_perm):
        ge += orbit_r2(G, orbit_fn(rng.permutation(labels))) >= obs - 1e-12
    return obs, (1 + ge) / (1 + n_perm)


def cyc_from_perm(perm):
    """cyclic orbit matrix after relabelling: member i sits at position perm[i]"""
    n = len(perm)
    d = np.abs(perm[:, None] - perm[None, :])
    return np.minimum(d, n - d)


def fourier(G):
    n = len(G)
    D = cyc_orbit(n)
    c = np.array([G[D == k].mean() for k in range(n // 2 + 1)])
    lam = [sum(c[min(k, n - k)] * np.cos(2 * np.pi * m * k / n) for k in range(n)) for m in range(1, n // 2 + 1)]
    return [float(x) for x in lam]


def cyc_test(X, rng, n_perm=N_PERM_FAM):
    G = gram(X)
    r2, p = perm_p(G, cyc_from_perm, np.arange(len(G)), n_perm, rng)
    lam = fourier(G)
    return {"r2": float(r2), "p": float(p), "lambda": lam, "circle": int(np.argmax(lam)) == 0}


def mantel(A, B, rng, n_perm):
    n = len(A)
    iu = np.triu_indices(n, 1)
    rank = lambda v: np.argsort(np.argsort(v)).astype(float)
    a = rank(A[iu]); a = (a - a.mean()) / a.std()
    RB = np.zeros((n, n)); RB[iu] = rank(B[iu]); RB = RB + RB.T
    def rho(P):
        b = RB[np.ix_(P, P)][iu]; b = (b - b.mean()) / b.std()
        return float((a * b).mean())
    obs = rho(np.arange(n))
    ge = sum(rho(rng.permutation(n)) >= obs - 1e-12 for _ in range(n_perm))
    return obs, (1 + ge) / (1 + n_perm)


def block_project(G, lab):
    n = len(G)
    o = block_orbit(lab)
    iu = np.triu_indices(n, 1)
    k = o.max() + 1
    s = np.bincount(o[iu], G[iu], k); c = np.bincount(o[iu], minlength=k)
    H = (s / np.maximum(c, 1))[o]
    np.fill_diagonal(H, np.diag(G))
    return H


# ---------------------------------------------------------------- weights
def single_ids(tok, words):
    ids = []
    for w in words:
        e = tok.encode(" " + w, add_special_tokens=False).ids
        if len(e) != 1:
            return None
        ids.append(e[0])
    return ids


def model_matrices(repo):
    e, u, h = hfrows.matrices(repo)
    out = [("in", e)]
    if u and u != e:
        out.append(("out", u))
    return out


# ---------------------------------------------------------------- brain
class _HTTP(io.RawIOBase):
    def __init__(s, u):
        s.u = u
        r = urllib.request.urlopen(urllib.request.Request(u, headers={"Range": "bytes=0-0"}))
        s.n = int(r.headers["Content-Range"].split("/")[1]); s.p = 0
    def seekable(s): return True
    def readable(s): return True
    def tell(s): return s.p
    def seek(s, o, w=0):
        s.p = {0: o, 1: s.p + o, 2: s.n + o}[w]; return s.p
    def readinto(s, b):
        k = len(b)
        if k == 0 or s.p >= s.n:
            return 0
        e = min(s.n, s.p + k) - 1
        for t in range(6):
            try:
                d = urllib.request.urlopen(urllib.request.Request(s.u, headers={"Range": f"bytes={s.p}-{e}"}), timeout=300).read()
                if len(d) == e - s.p + 1:
                    break
            except Exception:
                if t == 5:
                    raise
            time.sleep(5 * (t + 1))
        b[:len(d)] = d; s.p += len(d); return len(d)


def fetch_meta():
    os.makedirs(DATA, exist_ok=True)
    for name, url in [("category27_manual.tsv", CAT27), ("concepts-metadata_things.tsv", CONCEPTS)]:
        p = os.path.join(DATA, name)
        if not os.path.exists(p):
            open(p, "wb").write(urllib.request.urlopen(url).read())


TAIL = 2568          # bytes after the response array (sub-01 HDF5 metadata, measured)
N_TRIALS = 9840


def fetch_brain(s):
    """One streaming pass over sub-s's ResponseData.h5 inside the zip: keep only
    the rows of the selected voxels; the 15 GB file is never written to disk.
    Layout (read from sub-01's HDF5 metadata, pandas fixed format): block0_values
    is a contiguous row-major float32 array (voxels x 9840 trials), rows in
    voxel_id order, ending TAIL bytes before end of file."""
    import pandas as pd
    fetch_meta()
    out = os.path.join(DATA, f"sub-{s}_concepts.npz")
    if os.path.exists(out):
        return
    z = zipfile.ZipFile(io.BufferedReader(_HTTP(ZIP), 64 << 20))
    for k in ["StimulusMetadata", "VoxelMetadata"]:
        p = os.path.join(DATA, f"sub-{s}_{k}.csv")
        if not os.path.exists(p):
            open(p, "wb").write(z.read(f"betas_csv/sub-{s}_{k}.csv"))
    vox = pd.read_csv(os.path.join(DATA, f"sub-{s}_VoxelMetadata.csv"))
    stim = pd.read_csv(os.path.join(DATA, f"sub-{s}_StimulusMetadata.csv"))
    assert (vox["voxel_id"].to_numpy() == np.arange(len(vox))).all()
    assert (stim["trial_id"].to_numpy() == np.arange(N_TRIALS)).all()
    keep = (vox[ROIS].sum(axis=1) > 0) & (vox["nc_testset"] > NC_MIN)
    vid = vox.loc[keep, "voxel_id"].to_numpy()
    info = z.getinfo(f"betas_csv/sub-{s}_ResponseData.h5")
    RB = N_TRIALS * 4
    off = info.file_size - TAIL - len(vox) * RB
    starts = off + vid * RB
    buf = bytearray(len(vid) * RB)
    pos = 0
    with z.open(info) as src:
        while True:
            b = src.read(64 << 20)
            if not b:
                break
            lo, hi = pos, pos + len(b)
            i0 = max(0, np.searchsorted(starts, lo - RB, "right"))
            i1 = np.searchsorted(starts, hi, "left")
            for j in range(i0, i1):
                a0, a1 = max(lo, starts[j]), min(hi, starts[j] + RB)
                if a0 < a1:
                    buf[j * RB + a0 - starts[j]: j * RB + a1 - starts[j]] = b[a0 - lo: a1 - lo]
            pos = hi
    R = np.frombuffer(bytes(buf), np.float32).reshape(len(vid), N_TRIALS).T.copy()   # trials x voxels
    check = alignment_check(R, stim)
    tr = (stim["trial_type"] == "train").to_numpy()
    T = R[tr]
    T = (T - T.mean(0)) / T.std(0)
    con = stim.loc[tr, "concept"].to_numpy()
    names = np.array(sorted(set(con)))
    M = np.stack([T[con == c].mean(0) for c in names])
    np.savez_compressed(out, names=names, patterns=M.astype(np.float32), voxel_ids=vid,
                        check=np.array([check["same"], check["diff"]]))
    print("sub", s, "voxels", len(vid), "concepts", len(names), "check", check, flush=True)


def alignment_check(R, stim):
    """guard: odd/even repeats of the same test image must correlate more than different images"""
    te = (stim["trial_type"] == "test").to_numpy()
    st = stim.loc[te, "stimulus"].to_numpy(); X = R[te]
    ims = sorted(set(st))
    odd = np.stack([X[st == m][0::2].mean(0) for m in ims]); even = np.stack([X[st == m][1::2].mean(0) for m in ims])
    z = lambda A: (A - A.mean(1, keepdims=True)) / A.std(1, keepdims=True)
    C = z(odd) @ z(even).T / X.shape[1]
    same = float(np.diag(C).mean()); diff = float(C[~np.eye(len(ims), dtype=bool)].mean())
    if not same > diff + 0.05:
        raise SystemExit(f"alignment check failed: same {same:.3f} diff {diff:.3f}")
    return {"same": same, "diff": diff}


def brain_concepts():
    import pandas as pd
    cat = pd.read_csv(os.path.join(DATA, "category27_manual.tsv"), sep="\t")
    meta = pd.read_csv(os.path.join(DATA, "concepts-metadata_things.tsv"), sep="\t")
    one = cat.sum(axis=1) == 1
    lab = cat.to_numpy().argmax(1)
    d = {u: (w, int(l)) for u, w, l, o in zip(meta["uniqueID"], meta["Word"], lab, one) if o}
    return d, list(cat.columns)


# ---------------------------------------------------------------- run
def run():
    rng = np.random.default_rng(SEED)
    res = {"families": [], "products": [], "hier_models": [], "hier_brain": [], "mantel": []}
    words, catnames = brain_concepts()
    subj = {}
    for s in ["01", "02", "03"]:
        p = os.path.join(DATA, f"sub-{s}_concepts.npz")
        if os.path.exists(p):
            z = np.load(p, allow_pickle=False)
            subj[s] = (list(z["names"]), z["patterns"])
    # brain hierarchy
    brainG = {}
    for s, (names, P) in subj.items():
        keep = [i for i, n in enumerate(names) if n in words]
        lab = np.array([words[names[i]][1] for i in keep])
        ok = np.isin(lab, [c for c in set(lab) if (lab == c).sum() >= 8])
        keep = [k for k, o in zip(keep, ok) if o]
        lab = lab[ok]
        _, lab = np.unique(lab, return_inverse=True)
        G = gram(P[keep])
        r2, p = perm_p(G, block_orbit, lab, N_PERM_HIER, rng)
        res["hier_brain"].append({"subject": s, "n": len(keep), "r2": float(r2), "p": float(p)})
        brainG[s] = ({names[k]: j for j, k in enumerate(keep)}, G, lab)
        print("brain", s, len(keep), round(r2, 4), p, flush=True)
    for repo in MODELS:
        tok = hfrows.tokenizer(repo)
        for side, tensor in model_matrices(repo):
            mid = f"{repo}:{side}"
            for fam, ws in FAMILIES.items():
                ids = single_ids(tok, ws)
                if ids is None:
                    continue
                X = hfrows.rows(repo, tensor, ids)
                r = cyc_test(X, rng); r.update(matrix=mid, family=fam)
                res["families"].append(r)
            for fam, (A, B) in PRODUCTS.items():
                ia, ib = single_ids(tok, A), single_ids(tok, B)
                if ia is None or ib is None:
                    continue
                X = np.stack([hfrows.rows(repo, tensor, ia), hfrows.rows(repo, tensor, ib)], 1)  # n x 2 x d
                X = X / np.linalg.norm(X, axis=2, keepdims=True)
                mu = X.mean((0, 1)); a = X.mean(1) - mu; b = X.mean(0) - mu
                r = X - mu - a[:, None] - b[None]
                share = float((r ** 2).sum() / ((X - mu) ** 2).sum())
                n, m = X.shape[:2]
                res["products"].append({"matrix": mid, "family": fam,
                                        "interaction": cyc_test(r[:, 0], rng),
                                        "additive": cyc_test(a, rng),
                                        "interaction_share": share,
                                        "null_share": (n - 1) * (m - 1) / (n * m - 1)})
            # hierarchy on concept words
            cw = {}
            for u, (w, l) in words.items():
                e = tok.encode(" " + str(w), add_special_tokens=False).ids
                if len(e) == 1:
                    cw[u] = e[0]
            us = [u for s_ in brainG.values() for u in s_[0]]
            us = sorted(set(us) & set(cw)) if brainG else sorted(cw)
            lab = np.array([words[u][1] for u in us])
            ok = np.isin(lab, [c for c in set(lab) if (lab == c).sum() >= 8])
            us = [u for u, o in zip(us, ok) if o]
            lab = np.unique(lab[ok], return_inverse=True)[1]
            V = hfrows.rows(repo, tensor, [cw[u] for u in us])
            Gm = gram(V)
            r2, p = perm_p(Gm, block_orbit, lab, N_PERM_HIER, rng)
            res["hier_models"].append({"matrix": mid, "n": len(us), "r2": float(r2), "p": float(p)})
            for s, (idx, Gb, labb) in brainG.items():
                com = [u for u in us if u in idx]
                if len(com) < 100:
                    res["mantel"].append({"matrix": mid, "subject": s, "n": len(com), "skipped": True}); continue
                ib = [idx[u] for u in com]; im = [us.index(u) for u in com]
                A = Gb[np.ix_(ib, ib)]; B = Gm[np.ix_(im, im)]
                l2 = np.unique(np.array([words[u][1] for u in com]), return_inverse=True)[1]
                full = mantel(A, B, rng, N_PERM_HIER)
                resid = mantel(A - block_project(A, l2), B - block_project(B, l2), rng, N_PERM_HIER)
                res["mantel"].append({"matrix": mid, "subject": s, "n": len(com),
                                      "full_rho": full[0], "full_p": full[1],
                                      "resid_rho": resid[0], "resid_p": resid[1]})
            print(mid, "done", flush=True)
    res["categories"] = catnames
    os.makedirs(RAW, exist_ok=True)
    json.dump(res, open(os.path.join(RAW, "run.json"), "w"), indent=1, default=float)


def verdict(x, held, broken):
    return "HELD" if held(x) else "BROKEN" if broken(x) else "NEITHER"


def analyse():
    res = json.load(open(os.path.join(RAW, "run.json")))
    F, P, HB, HM, MA = res["families"], res["products"], res["hier_brain"], res["hier_models"], res["mantel"]
    MA = [m for m in MA if not m.get("skipped")]
    out = {"n_cases": {"families": len(F), "products": len(P), "brain_subjects": len(HB),
                       "matrices": len(HM), "mantel_pairs": len(MA)}}
    v = {}
    frac = lambda xs: float(np.mean(xs)) if xs else None
    f1 = frac([c["p"] < 0.01 for c in F]); out["H53.1_frac_sig"] = f1
    v["H53.1"] = "NO VERDICT" if len(F) < 30 else verdict(f1, lambda x: x >= 0.75, lambda x: x < 0.5)
    f2 = frac([c["circle"] for c in F]); out["H53.2_frac_circle"] = f2
    v["H53.2"] = "NO VERDICT" if len(F) < 30 else verdict(f2, lambda x: x >= 0.75, lambda x: x < 0.5)
    f3 = frac([c["interaction"]["p"] < 0.01 for c in P]); out["H53.3_frac_sig"] = f3
    v["H53.3"] = "NO VERDICT" if len(P) < 15 else verdict(f3, lambda x: x >= 0.5, lambda x: x <= 0.2)
    if len(HB) < 2:
        v["H53.4"] = "NO VERDICT"
    else:
        v["H53.4"] = "HELD" if all(h["p"] < 0.001 for h in HB) else "BROKEN" if sum(h["p"] >= 0.01 for h in HB) >= 2 else "NEITHER"
    f5 = frac([h["p"] < 0.001 for h in HM]); out["H53.5_frac_sig"] = f5
    v["H53.5"] = verdict(f5, lambda x: x >= 0.75, lambda x: x < 0.5)
    if MA:
        f6 = frac([m["full_p"] < 0.01 and m["full_rho"] > 0 for m in MA]); out["H53.6a_frac_sig"] = f6
        v["H53.6a"] = verdict(f6, lambda x: x >= 0.75, lambda x: x < 0.5)
        ns = frac([m["resid_p"] >= 0.01 for m in MA]); sg = frac([m["resid_p"] < 0.01 and m["resid_rho"] > 0 for m in MA])
        out["H53.6b_frac_resid_nonsig"], out["H53.6b_frac_resid_sig"] = ns, sg
        v["H53.6b"] = "HELD" if ns >= 0.5 else "BROKEN" if sg >= 0.75 else "NEITHER"
        out["median_full_rho"] = float(np.median([m["full_rho"] for m in MA]))
        out["median_resid_rho"] = float(np.median([m["resid_rho"] for m in MA]))
    else:
        v["H53.6a"] = v["H53.6b"] = "NO VERDICT"
    out["verdicts"] = v
    # exploratory
    by = {}
    for c in F:
        by.setdefault(c["family"], []).append(c)
    out["by_family"] = {k: {"n": len(c), "frac_sig": frac([x["p"] < 0.01 for x in c]),
                            "frac_circle": frac([x["circle"] for x in c]),
                            "median_r2": float(np.median([x["r2"] for x in c]))} for k, c in by.items()}
    out["by_side"] = {s: {"families_frac_sig": frac([c["p"] < 0.01 for c in F if c["matrix"].endswith(":" + s)]),
                          "products_frac_sig": frac([c["interaction"]["p"] < 0.01 for c in P if c["matrix"].endswith(":" + s)])}
                      for s in ["in", "out"]}
    out["products_summary"] = {
        "median_interaction_share": float(np.median([c["interaction_share"] for c in P])) if P else None,
        "null_share": sorted(set(c["null_share"] for c in P)),
        "frac_additive_sig": frac([c["additive"]["p"] < 0.01 for c in P]),
        "median_interaction_r2": float(np.median([c["interaction"]["r2"] for c in P])) if P else None,
        "median_additive_r2": float(np.median([c["additive"]["r2"] for c in P])) if P else None}
    out["hier_brain"] = HB
    out["hier_models_median_r2"] = float(np.median([h["r2"] for h in HM]))
    json.dump(out, open(OUT, "w"), indent=1, default=float)
    print(json.dumps(out["verdicts"], indent=1))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "fetch-brain":
        fetch_brain(sys.argv[2])
    elif cmd == "run":
        run()
    elif cmd == "analyse":
        analyse()
