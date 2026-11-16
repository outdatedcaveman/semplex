"""Spike 57: closure (C32) and economy (C31) laws on automata built from Krohn-Rhodes parts.
GRUs trained on outputs only; hidden-state geometry compared with predictions."""
import itertools, json, os, sys, time
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike57_raw")
OUT = os.path.join(ROOT, "results", "spike57.json")
SEEDS = 5
HID, LEN, STEPS, BATCH, LR = 32, 30, 3000, 64, 0.003


# ---------------------------------------------------------------- automata
def make(name):
    """returns (states list, letters list, step(state, letter) -> state, out(state) -> tuple, start)"""
    if name in ("Z5", "Z7"):
        n = int(name[1:])
        return list(range(n)), ["inc", "noop"], (lambda s, a: (s + 1) % n if a == "inc" else s), (lambda s: (int(s == 0),)), 0
    if name == "RESET3":
        return [0, 1, 2], ["r0", "r1", "r2", "noop"], (lambda s, a: int(a[1]) if a != "noop" else s), (lambda s: (int(s == 0), int(s == 1))), 0
    if name == "S3":
        P = list(itertools.permutations(range(3)))
        def st(p, a):
            q = (p[1], p[0], p[2]) if a == "swap" else (p[1], p[2], p[0])
            return q
        return P, ["swap", "cycle"], st, (lambda p: (int(p == (0, 1, 2)),)), (0, 1, 2)
    if name in ("PROD", "CASC"):
        S = [(m, c) for m in (0, 1) for c in range(3)]
        def st(s, a):
            m, c = s
            if a == "set0": return (0, c)
            if a == "set1": return (1, c)
            if a == "t":
                d = 1 if (name == "PROD" or m == 0) else -1
                return (m, (c + d) % 3)
            return s
        return S, ["set0", "set1", "t", "noop"], st, (lambda s: (int(s[1] == 0), s[0])), (0, 0)
    raise KeyError(name)

AUTOMATA = ["Z5", "Z7", "RESET3", "S3", "PROD", "CASC"]


def minimal_classes(name):
    """Moore minimization: map each reachable state to its minimal-state class id"""
    S, L, st, out, s0 = make(name)
    reach, frontier = {s0}, [s0]
    while frontier:
        s = frontier.pop()
        for a in L:
            t = st(s, a)
            if t not in reach:
                reach.add(t); frontier.append(t)
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
    Y = np.zeros((B, T, len(out(s0))), np.float32)
    ST = []
    for b in range(B):
        s, row = s0, []
        for t in range(T):
            s = st(s, L[X[b, t]]); Y[b, t] = out(s); row.append(s)
        ST.append(row)
    return X, Y, ST


# ---------------------------------------------------------------- training
def train(name, seed):
    import torch
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    S, L, st, out, s0 = make(name)
    k_out = len(out(s0))
    emb = torch.nn.Embedding(len(L), 16); gru = torch.nn.GRU(16, HID, batch_first=True); head = torch.nn.Linear(HID, k_out)
    params = list(emb.parameters()) + list(gru.parameters()) + list(head.parameters())
    opt = torch.optim.Adam(params, lr=LR)
    first99 = None
    for step in range(STEPS):
        X, Y, _ = sample(name, BATCH, LEN, rng)
        h, _ = gru(emb(torch.tensor(X)))
        logit = head(h)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(logit, torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step()
        if first99 is None and step % 25 == 0:
            acc = float(((logit > 0).float() == torch.tensor(Y)).float().mean())
            if acc >= 0.99: first99 = step
    with torch.no_grad():
        X, Y, _ = sample(name, 500, 100, np.random.default_rng(seed + 10**6))
        h, _ = gru(emb(torch.tensor(X)))
        fit_acc = float(((head(h) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(name, 400, 60, np.random.default_rng(seed + 2 * 10**6))
        H, _ = gru(emb(torch.tensor(X)))
    H = H.numpy()[:, 5:]; X = X[:, 5:]; ST = [r[5:] for r in ST]
    return fit_acc, first99, H, X, ST


def run():
    os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        cls = minimal_classes(name)
        S = make(name)[0]
        assert len(set(cls.values())) == len(S), (name, len(set(cls.values())), len(S))
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.npz")
            if os.path.exists(p):
                continue
            fit, first99, H, X, ST = train(name, 5700 + 10 * AUTOMATA.index(name) + i)
            lab = np.array([[cls[s] for s in row] for row in ST])
            np.savez_compressed(p, H=H.astype(np.float32), X=X, lab=lab, fit=fit, first99=-1 if first99 is None else first99)
            print(name, i, "fit", round(fit, 4), "first99", first99, flush=True)


# ---------------------------------------------------------------- analysis
def ari(a, b):
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(a, b))


def analyse():
    from sklearn.cluster import KMeans
    res = []
    for name in AUTOMATA:
        S, L, st, out, s0 = make(name)
        cls = minimal_classes(name); inv = {v: k for k, v in cls.items()}
        k = len(S)
        for i in range(SEEDS):
            z = np.load(os.path.join(RAW, f"{name}_{i}.npz"))
            H, X, lab = z["H"], z["X"], z["lab"]
            r = {"automaton": name, "seed": i, "fit": float(z["fit"]), "first99": int(z["first99"])}
            r["fitted"] = r["fit"] >= 0.99
            flatH, flatL = H.reshape(-1, H.shape[2]), lab.ravel()
            km = KMeans(k, n_init=10, random_state=0).fit(flatH)
            cl = km.labels_.reshape(lab.shape)
            r["ari"] = ari(flatL, km.labels_)
            # macro determinism over (cluster, letter) -> next cluster
            tot = good = 0
            for c in range(k):
                for a in range(len(L)):
                    m = (cl[:, :-1] == c) & (X[:, 1:] == a)
                    nxt = cl[:, 1:][m]
                    if nxt.size:
                        tot += nxt.size; good += np.bincount(nxt).max()
            r["determinism"] = good / tot
            C = np.stack([flatH[flatL == j].mean(0) for j in range(k)])
            Cc = C - C.mean(0)
            sv = np.linalg.svd(Cc, compute_uv=False) ** 2
            r["top2_share"] = float(sv[:2].sum() / sv.sum())
            r["dim90"] = int(np.searchsorted(np.cumsum(sv) / sv.sum(), 0.90) + 1)
            if name in ("Z5", "Z7"):
                n = k
                U = np.linalg.svd(Cc, full_matrices=False)[2][:2]
                P = Cc @ U.T
                order = [cls[c] for c in range(n)]           # minimal class of counter value c
                th = np.arctan2(P[order, 1], P[order, 0])
                d = np.angle(np.exp(1j * (np.roll(th, -1) - th)))
                r["step_sd"] = float(np.std(d)); r["step_mean"] = float(np.mean(d))
                r["fourier_k"] = float(round(abs(np.mean(d)) * n / (2 * np.pi), 2))
            if name == "RESET3":
                D = [np.linalg.norm(C[a] - C[b]) for a, b in itertools.combinations(range(3), 2)]
                r["dist_cv"] = float(np.std(D) / np.mean(D))
            if name in ("PROD", "CASC"):
                Xc = np.stack([[C[cls[(m, c)]] for c in range(3)] for m in (0, 1)])   # 2 x 3 x d
                mu = Xc.mean((0, 1)); a_ = Xc.mean(1) - mu; b_ = Xc.mean(0) - mu
                rr = Xc - mu - a_[:, None] - b_[None]
                share = float((rr ** 2).sum() / ((Xc - mu) ** 2).sum())
                r["interaction_share"] = share; r["relative_interaction"] = share / 0.4
            res.append(r)
    fitted = [r for r in res if r["fitted"]]
    by = {n: [r for r in fitted if r["automaton"] == n] for n in AUTOMATA}
    ok = {n: len(by[n]) >= 3 for n in AUTOMATA}
    frac = lambda xs: float(np.mean(xs)) if xs else None
    v = {}
    f1 = frac([r["ari"] >= 0.95 and r["determinism"] >= 0.99 for r in fitted])
    v["H57.1"] = "HELD" if f1 >= 0.8 else "BROKEN" if f1 < 0.5 else "NEITHER"
    if ok["Z5"] and ok["Z7"]:
        f2 = frac([r["top2_share"] >= 0.8 and r["step_sd"] <= 0.35 for r in by["Z5"] + by["Z7"]])
        v["H57.2"] = "HELD" if f2 >= 0.8 else "BROKEN" if f2 < 0.5 else "NEITHER"
    else:
        f2 = None; v["H57.2"] = "NO VERDICT"
    f3 = frac([r["dist_cv"] <= 0.15 for r in by["RESET3"]]) if ok["RESET3"] else None
    v["H57.3"] = "NO VERDICT" if f3 is None else "HELD" if f3 >= 0.8 else "BROKEN" if f3 < 0.5 else "NEITHER"
    f4 = frac([r["top2_share"] >= 0.8 for r in by["S3"]]) if ok["S3"] else None
    v["H57.4"] = "NO VERDICT" if f4 is None else "HELD" if f4 >= 0.8 else "BROKEN" if f4 < 0.5 else "NEITHER"
    if ok["PROD"] and ok["CASC"]:
        fp = frac([r["relative_interaction"] <= 0.30 for r in by["PROD"]])
        fc = frac([r["relative_interaction"] >= 0.60 for r in by["CASC"]])
        mp = float(np.median([r["relative_interaction"] for r in by["PROD"]]))
        mc = float(np.median([r["relative_interaction"] for r in by["CASC"]]))
        v["H57.5"] = "HELD" if fp >= 0.8 and fc >= 0.8 else "BROKEN" if mc <= mp else "NEITHER"
    else:
        fp = fc = mp = mc = None; v["H57.5"] = "NO VERDICT"
    out = {"verdicts": v, "n_runs": len(res), "n_fitted": len(fitted),
           "fitted_by_automaton": {n: len(by[n]) for n in AUTOMATA},
           "H57.1_frac": f1, "H57.2_frac": f2, "H57.3_frac": f3, "H57.4_frac": f4,
           "H57.5": {"prod_frac_low": fp, "casc_frac_high": fc, "prod_median": mp, "casc_median": mc},
           "first99_median": {n: float(np.median([r["first99"] for r in by[n] if r["first99"] >= 0])) if any(r["first99"] >= 0 for r in by[n]) else None for n in AUTOMATA},
           "runs": res}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
