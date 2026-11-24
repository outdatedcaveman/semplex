"""Spike 60: readout-induced permutation representation (C31') vs minimal faithful (C31),
GRU and constant-depth transformer, A5 and S4 with two readouts each. See SPIKE_60_REPORT.md."""
import json, math, os, sys
import numpy as np
from experiments.spike58 import comp, inv, cyc, closure, char_table as char58

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike60_raw")
OUT = os.path.join(ROOT, "results", "spike60.json")
SEEDS, LEN, BATCH, STEPS = 5, 30, 64, 6000
AUTOMATA = ["A5_5", "A5_6", "S4_4", "S4_6"]
GENS = {"A5": [cyc(5, [0, 1, 2]), cyc(5, [0, 1, 2, 3, 4])], "S4": [cyc(4, [0, 1]), cyc(4, [0, 1, 2, 3])]}


def subgroup(name):
    g, k = name.split("_")
    G = closure(GENS[g])
    if name == "A5_5" or name == "S4_4":
        return [x for x in G if x[0] == 0]
    if name == "A5_6":
        c = cyc(5, [0, 1, 2, 3, 4]); C = {tuple(range(5))}; y = tuple(range(5))
        for _ in range(5):
            y = comp(y, c); C.add(y)
        return [x for x in G if {comp(comp(x, z), inv(x)) for z in C} == C]
    if name == "S4_6":
        return [x for x in G if {x[0], x[1]} == {0, 1}]


def setup(name):
    """group elements, letters, left-coset labels"""
    G = closure(GENS[name.split("_")[0]]); H = subgroup(name)
    cos = sorted({tuple(sorted(comp(g, h) for h in H)) for g in G})
    lab = {g: cos.index(tuple(sorted(comp(g, h) for h in H))) for g in G}
    return G, H, cos, lab


def make(name):
    G, H, cos, lab = setup(name); gens = GENS[name.split("_")[0]]; k = len(cos)
    return G, list(range(len(gens))), (lambda g, a: comp(g, gens[a])), (lambda g: tuple(int(lab[g] == j) for j in range(k))), G[0] if G[0] == tuple(range(len(G[0]))) else tuple(range(len(G[0])))


def minimal_size(name):
    S, L, st, out, s0 = make(name)
    reach, fr = {s0}, [s0]
    while fr:
        s = fr.pop()
        for a in L:
            t = st(s, a)
            if t not in reach: reach.add(t); fr.append(t)
    cls = {s: out(s) for s in reach}
    while True:
        sig = {s: (cls[s],) + tuple(cls[st(s, a)] for a in L) for s in reach}
        ids = {v: i for i, v in enumerate(sorted(set(sig.values()), key=str))}
        new = {s: ids[sig[s]] for s in reach}
        if len(set(new.values())) == len(set(cls.values())):
            return len(set(new.values()))
        cls = new


def perm_char(name):
    G, H, cos, lab = setup(name)
    cs = [set(c) for c in cos]
    return lambda x: sum(1 for c in cs if {comp(x, y) for y in c} == c)


def irreps(name):
    """(table [(label, chi)], minimal-faithful labels)"""
    g = name.split("_")[0]
    if g == "A5":
        tab, _, _ = char58("A5")
        return tab, {"chi3", "chi3'"}
    def ct(x):
        n, seen, out = 4, set(), []
        for i in range(n):
            if i in seen: continue
            j, L = i, 0
            while j not in seen: seen.add(j); j = x[j]; L += 1
            out.append(L)
        return tuple(sorted(out, reverse=True))
    vals = {"sign": {(1, 1, 1, 1): 1, (2, 1, 1): -1, (2, 2): 1, (3, 1): 1, (4,): -1},
            "chi2": {(1, 1, 1, 1): 2, (2, 1, 1): 0, (2, 2): 2, (3, 1): -1, (4,): 0},
            "std": {(1, 1, 1, 1): 3, (2, 1, 1): 1, (2, 2): -1, (3, 1): 0, (4,): -1},
            "std_sign": {(1, 1, 1, 1): 3, (2, 1, 1): -1, (2, 2): -1, (3, 1): 0, (4,): 1}}
    return [(k, (lambda x, v=v: v[ct(x)])) for k, v in vals.items()], {"std", "std_sign"}


def sample(name, B, T, rng):
    S, L, st, out, s0 = make(name)
    X = rng.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, len(out(s0))), np.float32); ST = []
    for b in range(B):
        s, row = s0, []
        for t in range(T):
            s = st(s, L[X[b, t]]); Y[b, t] = out(s); row.append(s)
        ST.append(row)
    return X, Y, ST


# ---------------------------------------------------------------- models
def build(arch, nL, k_out):
    import torch
    nn = torch.nn
    if arch == "gru":
        class M(nn.Module):
            def __init__(s):
                super().__init__(); s.e = nn.Embedding(nL, 16); s.r = nn.GRU(16, 64, batch_first=True); s.h = nn.Linear(64, k_out)
            def hidden(s, X, h0=None):
                return s.r(s.e(X), h0)[0]
            def forward(s, X):
                return s.h(s.hidden(X))
        return M()
    class T(nn.Module):
        def __init__(s):
            super().__init__(); s.e = nn.Embedding(nL, 64); s.p = nn.Embedding(LEN, 64)
            layer = nn.TransformerEncoderLayer(64, 4, 128, dropout=0.0, batch_first=True, norm_first=True)
            s.t = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False); s.n = nn.LayerNorm(64); s.h = nn.Linear(64, k_out)
        def hidden(s, X):
            Tn = X.shape[1]; mask = torch.triu(torch.full((Tn, Tn), float("-inf")), 1)
            z = s.e(X) + s.p(torch.arange(Tn))[None]
            return s.n(s.t(z, mask=mask, is_causal=True))
        def forward(s, X):
            return s.h(s.hidden(X))
    return T()


def run_one(name, arch, seed):
    import torch
    from sklearn.linear_model import LogisticRegression
    from scipy.stats import spearmanr
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    S, L, st, out, s0 = make(name); k_out = len(out(s0))
    m = build(arch, len(L), k_out)
    opt = (torch.optim.Adam if arch == "gru" else torch.optim.AdamW)(m.parameters(), lr=0.003 if arch == "gru" else 0.001)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    first99 = -1
    for step in range(STEPS):
        X, Y, _ = sample(name, BATCH, LEN, rng)
        logit = m(torch.tensor(X)); loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
        if first99 < 0 and step % 25 == 0 and float(((logit > 0).float() == torch.tensor(Y)).float().mean()) >= 0.99:
            first99 = step
    r = {"automaton": name, "arch": arch, "seed": seed, "first99": first99}
    m.eval()
    with torch.no_grad():
        flen = 100 if arch == "gru" else LEN
        X, Y, _ = sample(name, 500, flen, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(name, 400, LEN, np.random.default_rng(seed + 2 * 10**6))
        H = m.hidden(torch.tensor(X)).numpy()
    idx = {g: i for i, g in enumerate(S)}
    lab = np.array([[idx[s] for s in row] for row in ST])
    Hs, Ls = H[:, 5:], lab[:, 5:]; d = H.shape[2]
    clf = LogisticRegression(max_iter=3000).fit(Hs[:200].reshape(-1, d), Ls[:200].ravel())
    r["probe_acc"] = float(clf.score(Hs[200:].reshape(-1, d), Ls[200:].ravel()))
    if arch == "gru":
        pl = clf.predict(Hs.reshape(-1, d)).reshape(Ls.shape); Xs = X[:, 5:]; tot = good = 0
        for c in range(len(S)):
            for a in range(len(L)):
                msk = (pl[:, :-1] == c) & (Xs[:, 1:] == a); nx = pl[:, 1:][msk]
                if nx.size: tot += nx.size; good += np.bincount(nx).max()
        r["determinism"] = good / tot
        irng = np.random.default_rng(seed + 3 * 10**6)
        pool = [(b, t) for b in range(400) for t in range(5, 9)]          # suffix of 20 within length 30
        by = {}
        for b, t in pool: by.setdefault(ST[b][t], []).append((b, t))
        states = list(by); D, Sf, Tg = [], [], []
        for _ in range(2000):
            b, t = pool[irng.integers(len(pool))]; s = ST[b][t]; s2 = s
            while s2 == s: s2 = states[irng.integers(len(states))]
            db, dt = by[s2][irng.integers(len(by[s2]))]
            suf = X[b, t + 1:t + 21]; z, tg = s2, []
            for a in suf: z = st(z, L[a]); tg.append(out(z))
            D.append(H[db, dt]); Sf.append(suf); Tg.append(tg)
        with torch.no_grad():
            o = m.h(m.hidden(torch.tensor(np.stack(Sf)), torch.tensor(np.stack(D))[None])) > 0
        r["intervene"] = float((o.numpy() == np.array(Tg, dtype=bool)).all(axis=(1, 2)).mean())
    flatH, flatL = Hs.reshape(-1, d), Ls.ravel()
    present = [j for j in range(len(S)) if (flatL == j).any()]
    C = np.stack([flatH[flatL == j].mean(0) for j in present]); el = [S[j] for j in present]
    C = C - C.mean(0); C = C / np.linalg.norm(C, axis=1, keepdims=True); Gm = C @ C.T
    iu = np.triu_indices(len(el), 1)
    def score(f):
        K = np.array([[f(comp(inv(a), b)) for b in el] for a in el], float)
        return float(spearmanr(Gm[iu], K[iu])[0])
    pc = perm_char(name)
    r["rho_readout"] = score(lambda x: pc(x) - 1)
    tab, mf = irreps(name)
    r["irrep_scores"] = {k: score(f) for k, f in tab}
    r["rho_minfaith"] = max(r["irrep_scores"][k] for k in mf)
    r["best_irrep"] = max(r["irrep_scores"], key=r["irrep_scores"].get)
    r["n_states_seen"] = len(el)
    return r


def run(arch):
    import torch
    torch.set_num_threads(2)
    os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        assert minimal_size(name) == len(make(name)[0]), name
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{arch}_{name}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(name, arch, 6000 + 10 * AUTOMATA.index(name) + i + (500 if arch == "tf" else 0))
            json.dump(r, open(p, "w"), indent=1)
            print(arch, name, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ("fit", "first99", "probe_acc", "intervene", "rho_readout", "rho_minfaith", "best_irrep")}, flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f"{a}_{n}_{i}.json"))) for a in ("gru", "tf") for n in AUTOMATA for i in range(SEEDS)]
    for r in runs:
        r["fitted"] = r["fit"] >= 0.99
    G = {n: [r for r in runs if r["arch"] == "gru" and r["automaton"] == n and r["fitted"]] for n in AUTOMATA}
    ok = [n for n in AUTOMATA if len(G[n]) >= 3]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    v = {}
    disc = [r for n in ("A5_6", "S4_6") if n in ok for r in G[n]]
    f1 = frac([r["rho_readout"] > r["rho_minfaith"] for r in disc]); v["H60.1"] = tri(f1, 0.8, 0.5)
    a56 = G["A5_6"] if "A5_6" in ok else []
    f2 = frac([r["best_irrep"] == "chi5" for r in a56]); f2b = frac([r["best_irrep"] in ("chi3", "chi3'") for r in a56])
    v["H60.2"] = "NO VERDICT" if f2 is None else "HELD" if f2 >= 0.8 else "BROKEN" if f2b >= 0.5 else "NEITHER"
    allg = [r for n in ok for r in G[n]]
    f3 = frac([r["rho_readout"] >= 0.5 for r in allg]); v["H60.3"] = tri(f3, 0.8, 0.5)
    tdisc = [r for r in runs if r["arch"] == "tf" and r["fitted"] and r["automaton"] in ("A5_6", "S4_6")]
    f4 = frac([r["rho_readout"] > r["rho_minfaith"] for r in tdisc]) if len(tdisc) >= 3 else None
    v["H60.4"] = tri(f4, 0.8, 0.5)
    tf = lambda g: frac([r["fitted"] for r in runs if r["arch"] == "tf" and r["automaton"].startswith(g)])
    fs4, fa5 = tf("S4"), tf("A5")
    v["H60.5"] = "HELD" if fs4 >= 0.6 and fa5 <= 0.2 else "BROKEN" if fa5 >= fs4 else "NEITHER"
    f6 = frac([r["probe_acc"] >= 0.99 and r["determinism"] >= 0.99 and r["intervene"] >= 0.98 for r in allg]); v["H60.6"] = tri(f6, 0.8, 0.5)
    out = {"verdicts": v, "gru_fitted": {n: len(G[n]) for n in AUTOMATA},
           "tf_fitted": {n: sum(r["fitted"] for r in runs if r["arch"] == "tf" and r["automaton"] == n) for n in AUTOMATA},
           "H60_1_frac": f1, "H60_2_frac_chi5": f2, "H60_2_frac_chi3": f2b, "H60_3_frac": f3, "H60_4_frac": f4,
           "tf_fit_rate": {"S4": fs4, "A5": fa5}, "H60_6_frac": f6,
           "best_irrep": {f"{a}:{n}": [r["best_irrep"] for r in runs if r["arch"] == a and r["automaton"] == n and r["fitted"]] for a in ("gru", "tf") for n in AUTOMATA},
           "median_rho": {f"{a}:{n}": {"readout": float(np.median([r["rho_readout"] for r in rs])), "minfaith": float(np.median([r["rho_minfaith"] for r in rs]))}
                          for a in ("gru", "tf") for n in AUTOMATA for rs in [[r for r in runs if r["arch"] == a and r["automaton"] == n and r["fitted"]]] if rs},
           "first99_median": {f"{a}:{n}": float(np.median([r["first99"] if r["first99"] >= 0 else 1e9 for r in runs if r["arch"] == a and r["automaton"] == n])) for a in ("gru", "tf") for n in AUTOMATA},
           "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2])
    else:
        analyse()
