"""Spike 66: formally pre-registered test of the predictive-state law on new groups (extension pairs,
p-primary readout, the S4_6 anomaly). Generic harness: group by generators (+ identity letter),
arbitrary 0/1 output vector. See SPIKE_66_REPORT.md."""
import json, math, os, sys
import numpy as np
from experiments.spike58 import comp, inv, cyc, closure

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike66_raw")
OUT = os.path.join(ROOT, "results", "spike66.json")
PRED = os.path.join(ROOT, "results", "spike66_predictions.json")
SEEDS, STEPS, LEN, BATCH, HORIZON = 3, 6000, 30, 64, 30


def prod_perm(p, q):  # direct product acting on disjoint points
    n = len(p); return tuple(list(p) + [n + x for x in q])

def ident(n): return tuple(range(n))

# Q8 as a regular permutation group on its 8 elements, from quaternion multiplication
def q8():
    names = ["1", "-1", "i", "-i", "j", "-j", "k", "-k"]
    tab = {("i", "j"): "k", ("j", "k"): "i", ("k", "i"): "j", ("j", "i"): "-k", ("k", "j"): "-i", ("i", "k"): "-j"}
    def mul(a, b):
        sa = a.startswith("-"); sb = b.startswith("-"); a0 = a.lstrip("-"); b0 = b.lstrip("-"); s = sa ^ sb
        if a0 == "1": r = b0
        elif b0 == "1": r = a0
        elif a0 == b0: r = "1"; s = not s
        else:
            r = tab[(a0, b0)]
            if r.startswith("-"): r = r[1:]; s = not s
        if r == "1" and s: return "-1"
        if r == "1": return "1"
        return ("-" if s else "") + r
    gen = lambda x: tuple(names.index(mul(y, x)) for y in names)   # right multiplication
    return [gen("i"), gen("j")]


def spec(name):
    """(generators incl. identity letter, output function on group elements given as tuples)"""
    if name == "Z4":   g = [cyc(4, [0, 1, 2, 3])]; out = lambda x: (int(x == ident(4)),)
    elif name == "V4": g = [prod_perm(cyc(2, [0, 1]), ident(2)), prod_perm(ident(2), cyc(2, [0, 1]))]; out = lambda x: (int(x == ident(4)),)
    elif name == "Z9": g = [cyc(9, list(range(9)))]; out = lambda x: (int(x == ident(9)),)
    elif name == "Z3xZ3": g = [prod_perm(cyc(3, [0, 1, 2]), ident(3)), prod_perm(ident(3), cyc(3, [0, 1, 2]))]; out = lambda x: (int(x == ident(6)),)
    elif name == "Q8": g = q8(); out = lambda x: (int(x == ident(8)),)
    elif name == "D4": g = [cyc(4, [0, 1, 2, 3]), cyc(4, [1, 3])]; out = lambda x: (int(x == ident(4)),)
    elif name == "Z6_mod3": g = [cyc(6, list(range(6)))]; out = lambda x: (int(x[0] % 3 == 0),)
    elif name == "S4_6": g = [cyc(4, [0, 1]), cyc(4, [0, 1, 2, 3])]; out = lambda x: tuple(int({x[0], x[1]} == set(pr)) for pr in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
    n = len(g[0]); letters = g + [ident(n)]
    G = closure(g)
    return G, letters, out

AUTOMATA = ["Z4", "V4", "Z9", "Z3xZ3", "Q8", "D4", "Z6_mod3", "S4_6"]


def minimal_classes(name):
    G, L, out = spec(name)
    cls = {s: out(s) for s in G}
    while True:
        sig = {s: (cls[s],) + tuple(cls[comp(s, a)] for a in L) for s in G}
        ids = {v: i for i, v in enumerate(sorted(set(sig.values()), key=str))}
        new = {s: ids[sig[s]] for s in G}
        if len(set(new.values())) == len(set(cls.values())): return new
        cls = new


def predictive_kernel(name, T=HORIZON):
    G, L, out = spec(name); n = len(G); idx = {g: i for i, g in enumerate(G)}
    O = np.array([out(g) for g in G], float)
    pair = np.zeros((n * n, n * n))
    for g in G:
        for h in G:
            for a in L: pair[idx[g] * n + idx[h], idx[comp(g, a)] * n + idx[comp(h, a)]] += 1 / len(L)
    v = (O @ O.T).ravel(); K = np.zeros(n * n)
    for _ in range(T): v = pair @ v; K += v
    K = K.reshape(n, n); Kc = K - K.mean(0) - K.mean(1)[:, None] + K.mean()
    O0 = O @ O.T; O0c = O0 - O0.mean(0) - O0.mean(1)[:, None] + O0.mean()
    return G, Kc, O0c


def predict():
    out = {}
    for name in AUTOMATA:
        cls = minimal_classes(name); G, Kc, O0c = predictive_kernel(name)
        out[name] = {"group_order": len(G), "minimal_states": len(set(cls.values()))}
        print(name, out[name])
    json.dump(out, open(PRED, "w"), indent=1)


def run_one(name, seed):
    import torch
    from sklearn.linear_model import LogisticRegression
    from scipy.stats import spearmanr
    from experiments.spike60 import build
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = spec(name); e = ident(len(G[0])); k_out = len(out(e))
    def sample(B, T, r):
        X = r.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, k_out), np.float32); ST = []
        for b in range(B):
            s, row = e, []
            for t in range(T):
                s = comp(s, L[X[b, t]]); Y[b, t] = out(s); row.append(s)
            ST.append(row)
        return X, Y, ST
    m = build("gru", len(L), k_out)
    opt = torch.optim.Adam(m.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    for step in range(STEPS):
        X, Y, _ = sample(BATCH, LEN, rng)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    r = {"automaton": name, "seed": seed}
    m.eval()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, LEN, np.random.default_rng(seed + 2 * 10**6))
        H = m.hidden(torch.tensor(X)).numpy()
    idx = {g: i for i, g in enumerate(G)}; cls = minimal_classes(name)
    lab = np.array([[idx[s] for s in row] for row in ST])[:, 5:]; Hs = H[:, 5:]; d = H.shape[2]
    flatH, flatL = Hs.reshape(-1, d), lab.ravel()
    # macrostate-level geometry: centroids per minimal class (equal to elements when the minimal automaton is the group)
    mlab = np.array([cls[G[i]] for i in flatL]); k = len(set(cls.values()))
    C = np.stack([flatH[mlab == j].mean(0) for j in range(k)]); C = C - C.mean(0); C = C / np.linalg.norm(C, axis=1, keepdims=True)
    Gm = C @ C.T
    _, Kc, O0c = predictive_kernel(name)
    # project kernels to minimal classes (average over elements in each class)
    M = np.zeros((len(G), k))
    for g in G: M[idx[g], cls[g]] = 1
    M = M / M.sum(0)
    Kq, Oq = M.T @ Kc @ M, M.T @ O0c @ M
    iu = np.triu_indices(k, 1)
    r["rho_predictive"] = float(spearmanr(Gm[iu], Kq[iu])[0]) if k > 2 else float("nan")
    r["rho_onestep"] = float(spearmanr(Gm[iu], Oq[iu])[0]) if k > 2 else float("nan")
    r["n_macro"] = k
    clf = LogisticRegression(max_iter=3000).fit(flatH[:5000], mlab[:5000]); r["probe_macro"] = float(clf.score(flatH[5000:], mlab[5000:]))
    if name == "Z6_mod3":
        par = np.array([G[i][0] % 2 for i in flatL])
        c2 = LogisticRegression(max_iter=3000).fit(flatH[:5000], par[:5000]); r["probe_mod2"] = float(c2.score(flatH[5000:], par[5000:]))
    if name == "S4_6":
        import experiments.spike60 as S60
        tab, _ = S60.irreps("S4_x")
        el = [G[j] for j in range(len(G))]
        Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))]); Ce = Ce - Ce.mean(0); Ce = Ce / np.linalg.norm(Ce, axis=1, keepdims=True)
        Ge = Ce @ Ce.T; iue = np.triu_indices(len(G), 1)
        r["irrep_scores"] = {kk: float(spearmanr(Ge[iue], np.array([[f(comp(inv(a), b)) for b in el] for a in el], float)[iue])[0]) for kk, f in tab}
        r["best_irrep"] = max(r["irrep_scores"], key=r["irrep_scores"].get)
    return r


def run():
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    for name in AUTOMATA:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(name, 6600 + 10 * AUTOMATA.index(name) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in r.items() if kk != "irrep_scores"}, flush=True)


def analyse():
    runs = [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for n in AUTOMATA for i in range(SEEDS)]
    fit = [r for r in runs if r["fit"] >= 0.99]
    law = [r for r in fit if r["n_macro"] > 2 and r["automaton"] != "S4_6"]
    f1 = float(np.mean([r["rho_predictive"] >= 0.6 for r in law])) if law else None
    f2 = float(np.mean([r["rho_predictive"] > r["rho_onestep"] for r in law])) if law else None
    z6 = [r for r in fit if r["automaton"] == "Z6_mod3"]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    v = {"H66.1": tri(f1, 0.8, 0.5), "H66.2": tri(f2, 0.8, 0.5)}
    if len(z6) >= 2:
        mm = float(np.median([r["probe_mod2"] for r in z6]))
        v["H66.3"] = "HELD" if mm <= 0.6 else "BROKEN" if mm >= 0.9 else "NEITHER"
    else:
        mm = None; v["H66.3"] = "NO VERDICT"
    s46 = [r.get("best_irrep") for r in fit if r["automaton"] == "S4_6"]
    out = {"verdicts": v, "H66_1_frac": f1, "H66_2_frac": f2, "z6_median_probe_mod2": mm, "S4_6_best_irrep": s46,
           "fitted": {n: sum(1 for r in fit if r["automaton"] == n) for n in AUTOMATA}, "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"predict": predict, "run": run, "analyse": analyse}[sys.argv[1]]()
