"""Spike 58: closure (probe form), causal power by interchange intervention, economy as
characters of the minimal faithful irreducible, loop topology, construction cost.
GRUs trained on automata outputs only. See SPIKE_58_REPORT.md."""
import itertools, json, math, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike58_raw")
OUT = os.path.join(ROOT, "results", "spike58.json")
SEEDS = 5
HID, EMB, LEN, STEPS, BATCH, LR = 64, 16, 30, 8000, 64, 0.003
AUTOMATA = ["Z5", "Z7", "RESET3", "S3", "A4", "A5", "PROD", "CASC"]
GROUPS = ["Z5", "Z7", "S3", "A4", "A5"]
PHI = (1 + 5 ** 0.5) / 2


# ---------------------------------------------------------------- permutations
def comp(g, p):            # (g ∘ p)(i) = g[p[i]]
    return tuple(g[i] for i in p)


def inv(g):
    r = [0] * len(g)
    for i, x in enumerate(g):
        r[x] = i
    return tuple(r)


def cyc(n, *cycles):
    p = list(range(n))
    for c in cycles:
        for a, b in zip(c, c[1:] + c[:1]):
            p[a] = b
    return tuple(p)


def closure(gens):
    n = len(gens[0]); e = tuple(range(n)); G = {e}; fr = [e]
    while fr:
        g = fr.pop()
        for p in gens:
            h = comp(g, p)
            if h not in G:
                G.add(h); fr.append(h)
    return sorted(G)


PERM_GENS = {"S3": [cyc(3, [0, 1]), cyc(3, [0, 1, 2])],
             "A4": [cyc(4, [0, 1, 2]), cyc(4, [0, 1], [2, 3])],
             "A5": [cyc(5, [0, 1, 2]), cyc(5, [0, 1, 2, 3, 4])]}


def make(name):
    """(states, letters, step, out, start)"""
    if name in ("Z5", "Z7"):
        n = int(name[1:])
        return list(range(n)), ["inc", "noop"], (lambda s, a: (s + 1) % n if a == "inc" else s), (lambda s: (int(s == 0),)), 0
    if name == "RESET3":
        return [0, 1, 2], ["r0", "r1", "r2", "noop"], (lambda s, a: int(a[1]) if a != "noop" else s), (lambda s: (int(s == 0), int(s == 1))), 0
    if name in PERM_GENS:
        gens = PERM_GENS[name]; n = len(gens[0])
        return closure(gens), list(range(len(gens))), (lambda g, a: comp(g, gens[a])), (lambda g: tuple(int(g[0] == j) for j in range(n))), tuple(range(n))
    if name in ("PROD", "CASC"):
        S = [(m, c) for m in (0, 1) for c in range(3)]
        def st(s, a):
            m, c = s
            if a == "set0": return (0, c)
            if a == "set1": return (1, c)
            if a == "t": return (m, (c + (1 if (name == "PROD" or m == 0) else -1)) % 3)
            return s
        return S, ["set0", "set1", "t", "noop"], st, (lambda s: (int(s[1] == 0), s[0])), (0, 0)
    raise KeyError(name)


def minimal_classes(name):
    S, L, st, out, s0 = make(name)
    reach, fr = {s0}, [s0]
    while fr:
        s = fr.pop()
        for a in L:
            t = st(s, a)
            if t not in reach:
                reach.add(t); fr.append(t)
    cls = {s: out(s) for s in reach}
    while True:
        sig = {s: (cls[s],) + tuple(cls[st(s, a)] for a in L) for s in reach}
        ids = {v: i for i, v in enumerate(sorted(set(sig.values()), key=str))}
        new = {s: ids[sig[s]] for s in reach}
        if len(set(new.values())) == len(set(cls.values())):
            return {s: new[s] for s in reach}
        cls = new


def sample(name, B, T, rng):
    S, L, st, out, s0 = make(name)
    X = rng.integers(0, len(L), size=(B, T))
    Y = np.zeros((B, T, len(out(s0))), np.float32); ST = []
    for b in range(B):
        s, row = s0, []
        for t in range(T):
            s = st(s, L[X[b, t]]); Y[b, t] = out(s); row.append(s)
        ST.append(row)
    return X, Y, ST


# ---------------------------------------------------------------- characters
def char_table(name):
    """list of (label, function elem->real char value) for nontrivial real irreducibles, and the predicted labels"""
    if name in ("Z5", "Z7"):
        n = int(name[1:])
        tab = [(f"k={k}", (lambda d, k=k: math.cos(2 * math.pi * k * d / n))) for k in range(1, n // 2 + 1)]
        return tab, {"k=1"}, (lambda g, h: (h - g) % n)
    G = closure(PERM_GENS[name]); n = len(G[0])
    def cycle_type(g):
        seen, ct = set(), []
        for i in range(n):
            if i in seen: continue
            j, L = i, 0
            while j not in seen:
                seen.add(j); j = g[j]; L += 1
            ct.append(L)
        return tuple(sorted(ct, reverse=True))
    def conj_class_rep(x, rep):
        return any(comp(comp(a, rep), inv(a)) == x for a in G)
    diff = lambda g, h: comp(inv(g), h)
    if name == "S3":
        def key(x):
            return cycle_type(x)
        vals = {"sign": {(1, 1, 1): 1, (2, 1): -1, (3,): 1}, "std": {(1, 1, 1): 2, (2, 1): 0, (3,): -1}}
        tab = [(k, (lambda x, v=v: v[key(x)])) for k, v in vals.items()]
        return tab, {"std"}, diff
    if name == "A4":
        c = cyc(4, [0, 1, 2])
        def key(x):
            ct = cycle_type(x)
            if ct == (3, 1): return "3a" if conj_class_rep(x, c) else "3b"
            return ct
        vals = {"omega(real,2d)": {(1, 1, 1, 1): 2, (2, 2): 2, "3a": -1, "3b": -1},
                "chi3": {(1, 1, 1, 1): 3, (2, 2): -1, "3a": 0, "3b": 0}}
        tab = [(k, (lambda x, v=v: v[key(x)])) for k, v in vals.items()]
        return tab, {"chi3"}, diff
    if name == "A5":
        c = cyc(5, [0, 1, 2, 3, 4])
        def key(x):
            ct = cycle_type(x)
            if ct == (5,): return "5a" if conj_class_rep(x, c) else "5b"
            return ct
        e = (1, 1, 1, 1, 1)
        vals = {"chi3": {e: 3, (2, 2, 1): -1, (3, 1, 1): 0, "5a": PHI, "5b": 1 - PHI},
                "chi3'": {e: 3, (2, 2, 1): -1, (3, 1, 1): 0, "5a": 1 - PHI, "5b": PHI},
                "chi4": {e: 4, (2, 2, 1): 0, (3, 1, 1): 1, "5a": -1, "5b": -1},
                "chi5": {e: 5, (2, 2, 1): 1, (3, 1, 1): -1, "5a": 0, "5b": 0}}
        tab = [(k, (lambda x, v=v: v[key(x)])) for k, v in vals.items()]
        return tab, {"chi3", "chi3'"}, diff
    raise KeyError(name)


# ---------------------------------------------------------------- per-run
def run_one(name, seed):
    import torch
    from sklearn.linear_model import LogisticRegression
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    S, L, st, out, s0 = make(name)
    cls = minimal_classes(name); k_out = len(out(s0))
    emb = torch.nn.Embedding(len(L), EMB); gru = torch.nn.GRU(EMB, HID, batch_first=True); head = torch.nn.Linear(HID, k_out)
    opt = torch.optim.Adam(list(emb.parameters()) + list(gru.parameters()) + list(head.parameters()), lr=LR)
    first99 = -1
    for step in range(STEPS):
        X, Y, _ = sample(name, BATCH, LEN, rng)
        logit = head(gru(emb(torch.tensor(X)))[0])
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step()
        if first99 < 0 and step % 25 == 0:
            if float(((logit > 0).float() == torch.tensor(Y)).float().mean()) >= 0.99:
                first99 = step
    r = {"automaton": name, "seed": seed, "first99": first99}
    with torch.no_grad():
        X, Y, _ = sample(name, 500, 100, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((head(gru(emb(torch.tensor(X)))[0]) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(name, 400, 60, np.random.default_rng(seed + 2 * 10**6))
        H = gru(emb(torch.tensor(X)))[0].numpy()
    lab = np.array([[cls[s] for s in row] for row in ST]); k = len(set(cls.values()))
    Hs, Ls, Xs = H[:, 5:], lab[:, 5:], X[:, 5:]
    # probe closure
    half = 200
    clf = LogisticRegression(max_iter=3000).fit(Hs[:half].reshape(-1, HID), Ls[:half].ravel())
    r["probe_acc"] = float(clf.score(Hs[half:].reshape(-1, HID), Ls[half:].ravel()))
    pl = clf.predict(Hs.reshape(-1, HID)).reshape(Ls.shape)
    tot = good = 0
    for c in range(k):
        for a in range(len(L)):
            m = (pl[:, :-1] == c) & (Xs[:, 1:] == a); nx = pl[:, 1:][m]
            if nx.size: tot += nx.size; good += np.bincount(nx).max()
    r["determinism"] = good / tot
    # interchange interventions
    irng = np.random.default_rng(seed + 3 * 10**6)
    pool = [(b, t) for b in range(400) for t in range(10, 40)]
    by_state = {}
    for b, t in pool:
        by_state.setdefault(ST[b][t], []).append((b, t))
    states = list(by_state)
    succ = {"diff": [], "same": []}
    for kind in ("diff", "same"):
        B, D, Sfx, Target = [], [], [], []
        for _ in range(2000):
            b, t = pool[irng.integers(len(pool))]; s = ST[b][t]
            if kind == "diff":
                s2 = s
                while s2 == s:
                    s2 = states[irng.integers(len(states))]
            else:
                s2 = s
            db, dt = by_state[s2][irng.integers(len(by_state[s2]))]
            suffix = X[b, t + 1:t + 21]
            z, tgt = s2, []
            for a in suffix:
                z = st(z, L[a]); tgt.append(out(z))
            D.append(H[db, dt]); Sfx.append(suffix); Target.append(tgt)
        with torch.no_grad():
            h0 = torch.tensor(np.stack(D))[None]
            o = head(gru(emb(torch.tensor(np.stack(Sfx))), h0)[0]) > 0
        ok = (o.numpy() == np.array(Target, dtype=bool)).all(axis=(1, 2))
        r[f"intervene_{kind}"] = float(ok.mean())
    # centroids, characters, interaction, topology
    flatH, flatL = Hs.reshape(-1, HID), Ls.ravel()
    C = np.stack([flatH[flatL == j].mean(0) for j in range(k)])
    if name in GROUPS:
        inv_cls = {v: s for s, v in cls.items()}
        elems = [inv_cls[j] for j in range(k)]
        Cc = C - C.mean(0); Cc = Cc / np.linalg.norm(Cc, axis=1, keepdims=True); Gm = Cc @ Cc.T
        tab, pred, diff = char_table(name)
        iu = np.triu_indices(k, 1)
        from scipy.stats import spearmanr
        scores = {}
        for lbl, chi in tab:
            K = np.array([[chi(diff(elems[i], elems[j])) for j in range(k)] for i in range(k)])
            scores[lbl] = float(spearmanr(Gm[iu], K[iu])[0])
        r["char_scores"] = scores
        r["char_best"] = max(scores, key=scores.get)
        r["char_hit"] = r["char_best"] in pred
    if name in ("Z5", "Z7"):
        import ripser
        idx = np.random.default_rng(seed).choice(len(flatH), 1500, replace=False)
        dg = ripser.ripser(flatH[idx], maxdim=1)["dgms"][1]
        p = np.sort(dg[:, 1] - dg[:, 0])[::-1] if len(dg) else np.array([0.0])
        r["h1_top"] = float(p[0]); r["h1_second"] = float(p[1]) if len(p) > 1 else 0.0
        r["h1_ratio"] = float(p[0] / p[1]) if len(p) > 1 and p[1] > 0 else float("inf")
    if name in ("PROD", "CASC"):
        Xc = np.stack([[C[cls[(m, c)]] for c in range(3)] for m in (0, 1)])
        mu = Xc.mean((0, 1)); a_ = Xc.mean(1) - mu; b_ = Xc.mean(0) - mu
        rr = Xc - mu - a_[:, None] - b_[None]
        r["relative_interaction"] = float((rr ** 2).sum() / ((Xc - mu) ** 2).sum()) / 0.4
    return r


def run():
    import torch
    torch.set_num_threads(os.cpu_count())
    os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        cls = minimal_classes(name)
        assert len(set(cls.values())) == len(make(name)[0]), name
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p):
                continue
            r = run_one(name, 5800 + 10 * AUTOMATA.index(name) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {k: r[k] for k in ("fit", "first99", "probe_acc", "intervene_diff", "intervene_same")}, r.get("char_best"), flush=True)


def analyse():
    from scipy.stats import spearmanr
    runs = [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for n in AUTOMATA for i in range(SEEDS)]
    for r in runs:
        r["fitted"] = r["fit"] >= 0.99
    by = {n: [r for r in runs if r["automaton"] == n and r["fitted"]] for n in AUTOMATA}
    ok = [n for n in AUTOMATA if len(by[n]) >= 3]
    F = [r for n in ok for r in by[n]]
    frac = lambda xs: float(np.mean(xs)) if xs else None
    tri = lambda f, hi, lo: "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    v = {}
    f1 = frac([r["probe_acc"] >= 0.99 and r["determinism"] >= 0.99 for r in F]); v["H58.1"] = tri(f1, 0.8, 0.5)
    f2 = frac([r["intervene_diff"] >= 0.98 for r in F]); v["H58.2"] = tri(f2, 0.8, 0.5)
    f3 = frac([r["intervene_same"] >= 0.99 for r in F]); v["H58.3"] = tri(f3, 0.8, 0.5)
    gq = [n for n in GROUPS if n in ok]
    if len(gq) >= 3:
        f4 = frac([r["char_hit"] for n in gq for r in by[n]]); v["H58.4"] = tri(f4, 0.8, 0.5)
    else:
        f4 = None; v["H58.4"] = "NO VERDICT"
    zq = [n for n in ("Z5", "Z7") if n in ok]
    f5 = frac([r["h1_ratio"] >= 3 for n in zq for r in by[n]]) if zq else None
    v["H58.5"] = "NO VERDICT" if f5 is None else tri(f5, 0.8, 0.5)
    order = ["RESET3", "Z5", "Z7", "S3", "A4", "A5"]
    def med_cost(n):
        xs = [r["first99"] if r["first99"] >= 0 else float("inf") for r in runs if r["automaton"] == n]
        return float(np.median(xs))
    costs = {n: med_cost(n) for n in AUTOMATA}
    rho = float(spearmanr(list(range(len(order))), [costs[n] if np.isfinite(costs[n]) else 1e12 for n in order])[0])
    casc_gt = costs["CASC"] > costs["PROD"]
    v["H58.6"] = "HELD" if rho >= 0.9 and casc_gt else "BROKEN" if rho <= 0.5 else "NEITHER"
    out = {"verdicts": v, "n_runs": len(runs), "fitted_by_automaton": {n: len(by[n]) for n in AUTOMATA},
           "qualifying": ok, "H58_1_frac": f1, "H58_2_frac": f2, "H58_3_frac": f3, "H58_4_frac": f4, "H58_5_frac": f5,
           "cost_median_steps": costs, "cost_spearman": rho, "casc_gt_prod": casc_gt,
           "char_best_by_automaton": {n: [r.get("char_best") for r in by[n]] for n in GROUPS},
           "median_intervene_diff": {n: float(np.median([r["intervene_diff"] for r in by[n]])) if by[n] else None for n in AUTOMATA},
           "median_intervene_same": {n: float(np.median([r["intervene_same"] for r in by[n]])) if by[n] else None for n in AUTOMATA},
           "median_relative_interaction": {n: float(np.median([r["relative_interaction"] for r in by[n]])) if by[n] else None for n in ("PROD", "CASC")},
           "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
