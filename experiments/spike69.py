"""Spike 69: formal test of the two-regime law C37 (structured predictive state -> its geometry;
degenerate predictive state -> architectural bias toward the minimal faithful irreducible), with
non-degeneracy computed and committed before training. Also probes the S4_6 anomaly.
Generic: any permutation group by generators (+ identity letter), any 0/1 output vector.
Irreducibles are computed numerically (isotypic projectors of the regular representation;
complex-conjugate pairs and quaternionic types merged into real irreducibles). See SPIKE_69_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp, inv, cyc, closure

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike69_raw")
OUT = os.path.join(ROOT, "results", "spike69.json")
PRED = os.path.join(ROOT, "results", "spike69_predictions.json")
SEEDS, STEPS, LEN, BATCH, HORIZON = 5, 6000, 30, 64, 30
TAU_STRUCT = 0.15          # structure threshold on tau (fixed with the predictions, before any run)
TIE = 1.5                  # a structured kernel has a unique prediction only if its top isotypic share is >= TIE x the second


def ident(n): return tuple(range(n))
def prod_perm(p, q): n = len(p); return tuple(list(p) + [n + x for x in q])

def q8():
    from experiments.spike66 import q8 as f
    return f()


def spec(name):
    """-> (G list, letters incl. identity, out: element -> tuple of 0/1)"""
    one = lambda n: (lambda x: (int(x == ident(n)),))
    sub = lambda n, S: (lambda x: (int(x[0] in S),))              # cyclic/abelian on points: x[0] = image of 0
    pair = lambda x: tuple(int({x[0], x[1]} == set(p)) for p in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
    pt = lambda n: (lambda x: tuple(int(x[0] == i) for i in range(n)))
    S4c = [cyc(4, [0, 1]), cyc(4, [0, 1, 2, 3])]
    A4g = [cyc(4, [0, 1, 2]), cyc(4, [0, 1], [2, 3])]
    D4g = [cyc(4, [0, 1, 2, 3]), cyc(4, [1, 3])]
    Z = lambda n: [cyc(n, list(range(n)))]
    V4g = [prod_perm(cyc(2, [0, 1]), ident(2)), prod_perm(ident(2), cyc(2, [0, 1]))]
    Z33 = [prod_perm(cyc(3, [0, 1, 2]), ident(3)), prod_perm(ident(3), cyc(3, [0, 1, 2]))]
    table = {
        # degenerate regime: identity readout
        "Z8_id": (Z(8), one(8)), "S3_id": ([cyc(3, [0, 1]), cyc(3, [0, 1, 2])], one(3)),
        "A4_id": (A4g, one(4)), "D4_id": (D4g, one(4)), "Q8_id": (None, one(8)),
        # structured regime: coset / subset readouts
        "D4_4": (D4g, pt(4)),
        "A4_6": (A4g, pair),
        "Z7_02": (Z(7), sub(7, {0, 2})),
        "Z9_013": (Z(9), sub(9, {0, 1, 3})),
        "Z8_014": (Z(8), sub(8, {0, 1, 4})),
        "Z4xZ2": (None, None), "V4_01": (V4g, None), "Z33_sub": (Z33, None),
        "Q8_sub": (None, None),
        # S4_6 anomaly variants
        "S4_6": (S4c, pair),
        "S4_6cox": ([cyc(4, [0, 1]), cyc(4, [1, 2]), cyc(4, [2, 3])], pair),
        "S4_6c3": ([cyc(4, [0, 1, 2]), cyc(4, [0, 1, 2, 3])], pair),
    }
    g, out = table[name]
    if name.startswith("Q8"):
        g = q8()
        if name == "Q8_sub": out = lambda x: (int(x[0] in {0, 2, 4}),)          # elements whose image of "1" is 1, i or j
    if name == "V4_01": out = lambda x: (int(x[0] == 0 and x[2] == 2), int(x[0] == 0))   # [g = e], [first factor trivial]
    if name == "Z33_sub": out = lambda x: (int((x[0], x[3]) in {(0, 3), (1, 3), (0, 4)}),)
    if name == "Z4xZ2":
        g = [prod_perm(cyc(4, [0, 1, 2, 3]), ident(2)), prod_perm(ident(4), cyc(2, [0, 1]))]
        out = lambda x: (int((x[0], x[4]) in {(0, 4), (1, 4), (0, 5)}),)
    n = len(g[0]); G = sorted(closure(g))
    return G, g + [ident(n)], out


STRUCT = ["D4_4", "A4_6", "Z7_02", "Z9_013", "Z8_014", "Z4xZ2", "V4_01", "Z33_sub", "Q8_sub"]
DEGEN = ["Z8_id", "S3_id", "A4_id", "D4_id", "Q8_id"]
ANOM = ["S4_6", "S4_6cox", "S4_6c3"]
AUTOMATA = DEGEN + STRUCT + ANOM


def minimal_classes(name):
    G, L, out = spec(name)
    cls = {s: out(s) for s in G}
    while True:
        sig = {s: (cls[s],) + tuple(cls[comp(s, a)] for a in L) for s in G}
        ids = {v: i for i, v in enumerate(sorted(set(sig.values()), key=str))}
        new = {s: ids[sig[s]] for s in G}
        if len(set(new.values())) == len(set(cls.values())): return new
        cls = new


def real_irreps(G):
    """Isotypic projectors of the right-regular representation for real irreducibles.
    Returns list of dicts {P (n x n), dim_real (trace), faithful, kernel_size}."""
    n = len(G); idx = {g: i for i, g in enumerate(G)}
    def R(a):
        M = np.zeros((n, n))
        for g in G: M[idx[g], idx[comp(g, a)]] = 1
        return M
    # conjugacy classes
    seen, classes = set(), []
    for g in G:
        if g in seen: continue
        c = {comp(comp(inv(x), g), x) for x in G}; seen |= c; classes.append(sorted(c))
    rng = np.random.default_rng(0)
    M = np.zeros((n, n))
    for c in classes:
        S = sum(R(a) for a in c); M += rng.normal() * (S + S.T)
    w, V = np.linalg.eigh(M)
    groups, cur = [], [0]
    for i in range(1, n):
        if abs(w[i] - w[cur[-1]]) < 1e-6 * max(1, abs(w).max()): cur.append(i)
        else: groups.append(cur); cur = [i]
    groups.append(cur)
    e = idx[ident(len(G[0]))]; out = []
    for gidx in groups:
        U = V[:, gidx]; P = U @ U.T
        row = P[e]; ker = int(np.sum(np.abs(row - row[e]) < 1e-8))
        if np.allclose(P, np.ones((n, n)) / n): continue          # trivial
        out.append({"P": P, "dim_real_sq": int(round(np.trace(P))), "faithful": ker == 1, "kernel_size": ker})
    return out


def irrep_label(ir, k):
    return f"r{k}_tr{ir['dim_real_sq']}_ker{ir['kernel_size']}"


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


def structure_index(Kc):
    """eta: off-diagonal spread / diagonal mean (reported only)."""
    n = len(Kc); iu = np.triu_indices(n, 1)
    return float(np.std(Kc[iu]) / np.mean(np.diag(Kc)))


def tau_index(Kc, irs):
    """tau: total-variation distance between the kernel's isotypic energy shares (renormalised over the
    invariant part) and the shares of the degenerate kernel (centring matrix, shares tr P_i / (n-1)).
    tau = 0 exactly for an identity-like predictive state."""
    n = len(Kc); w = np.array([np.sum((ir["P"] @ Kc @ ir["P"]) ** 2) for ir in irs]); inv_frac = float(w.sum() / np.sum(Kc * Kc))
    w = w / w.sum(); r = np.array([ir["dim_real_sq"] for ir in irs], float) / (n - 1)
    return float(0.5 * np.abs(w - r).sum()), inv_frac


def smoothness(ir, G, L):
    """mean over non-identity letters of P(e,a)/P(e,e): how slowly the constituent varies along one letter."""
    idx = {g: i for i, g in enumerate(G)}; e = idx[ident(len(G[0]))]
    return float(np.mean([ir["P"][e, idx[a]] / ir["P"][e, e] for a in L if a != ident(len(G[0]))]))


def scores(Gram, irs):
    from scipy.stats import spearmanr
    iu = np.triu_indices(len(Gram), 1)
    return {irrep_label(ir, k): float(spearmanr(Gram[iu], ir["P"][iu])[0]) for k, ir in enumerate(irs)}


def isotypic_weights(Kc, irs):
    """share of the kernel's Frobenius energy in each isotypic component (for invariant kernels this is exact)."""
    tot = np.sum(Kc * Kc)
    return {irrep_label(ir, k): float(np.sum((ir["P"] @ Kc @ ir["P"]) ** 2) / tot) for k, ir in enumerate(irs)}


def minimal_faithful(irs):
    f = [(ir["dim_real_sq"], irrep_label(ir, k)) for k, ir in enumerate(irs) if ir["faithful"]]
    if not f: return []
    d = min(x for x, _ in f); return [l for x, l in f if x == d]


def predict():
    res = {}
    for name in AUTOMATA:
        G, Kc, O0c = predictive_kernel(name); irs = real_irreps(G); cls = minimal_classes(name)
        _, L, _ = spec(name)
        eta = structure_index(Kc); tau, invf = tau_index(Kc, irs); sc = scores(Kc, irs); wt = isotypic_weights(Kc, irs)
        best_sc = max(sc, key=sc.get); srt = sorted(wt, key=wt.get, reverse=True); best_w = srt[0]
        regime = "structured" if tau >= TAU_STRUCT else "degenerate"
        tie = wt[srt[0]] < TIE * wt[srt[1]]
        mf = minimal_faithful(irs); sm = {irrep_label(ir, k): smoothness(ir, G, L) for k, ir in enumerate(irs)}
        mf_smooth = max(mf, key=sm.get) if mf else None
        info = {irrep_label(ir, k): {"tr": ir["dim_real_sq"], "kernel": ir["kernel_size"], "faithful": ir["faithful"], "smooth": sm[irrep_label(ir, k)]} for k, ir in enumerate(irs)}
        if regime == "degenerate": kind, pred = "degenerate", mf
        elif not tie: kind, pred = "unique", [best_w]
        else:
            top = [l for l in srt if wt[l] >= wt[srt[0]] / TIE]
            kind, pred = "tie", top
        res[name] = {"order": len(G), "minimal_states": len(set(cls.values())), "eta": eta, "tau": tau, "invariant_fraction": invf,
                     "regime": regime, "kind": kind, "irreps": info,
                     "kernel_spearman": sc, "kernel_isotypic_weight": wt, "best_by_spearman": best_sc, "best_by_weight": best_w,
                     "minimal_faithful": mf, "smoothest_minimal_faithful": mf_smooth, "prediction": pred}
        if kind == "tie":
            res[name]["tie_faithful_rule"] = [l for l in pred if info[l]["faithful"]]
            dmin = min(info[l]["tr"] for l in pred); res[name]["tie_lowdim_rule"] = [l for l in pred if info[l]["tr"] == dmin]
        print(f"{name:9s} |G|={len(G):3d} min={len(set(cls.values())):3d} eta={eta:.3f} tau={tau:.3f} inv={invf:.2f} {kind:10s} pred={pred} mf={mf} smooth_mf={mf_smooth}")
        print("          ", {k: (round(wt[k], 3), info[k]["tr"], info[k]["kernel"], round(sm[k], 2)) for k in wt})
        print("          weights", {k: round(v, 3) for k, v in wt.items()})
    json.dump(res, open(PRED, "w"), indent=1)


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
    lab = np.array([[idx[s] for s in row] for row in ST])[:, 5:]; d = H.shape[2]
    flatH, flatL = H[:, 5:].reshape(-1, d), lab.ravel()
    mlab = np.array([cls[G[i]] for i in flatL])
    clf = LogisticRegression(max_iter=3000).fit(flatH[:5000], mlab[:5000]); r["probe_macro"] = float(clf.score(flatH[5000:], mlab[5000:]))
    r["n_macro"] = len(set(cls.values())); r["elements_seen"] = int(len(set(flatL.tolist())))
    Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))]); Ce = Ce - Ce.mean(0); Ce = Ce / np.linalg.norm(Ce, axis=1, keepdims=True)
    Ge = Ce @ Ce.T; iu = np.triu_indices(len(G), 1)
    _, Kc, O0c = predictive_kernel(name)
    r["rho_predictive"] = float(spearmanr(Ge[iu], Kc[iu])[0])
    r["rho_onestep"] = float(spearmanr(Ge[iu], O0c[iu])[0])
    irs = real_irreps(G); r["irrep_scores"] = scores(Ge, irs)
    r["best_irrep"] = max(r["irrep_scores"], key=r["irrep_scores"].get)
    return r


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    names = AUTOMATA if which is None else which.split(",")
    for name in names:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{name}_{i}.json")
            if os.path.exists(p): continue
            r = run_one(name, 6900 + 10 * AUTOMATA.index(name) + i)
            json.dump(r, open(p, "w"), indent=1)
            print(name, i, {kk: (round(v, 3) if isinstance(v, float) else v) for kk, v in r.items() if kk != "irrep_scores"}, flush=True)


def analyse():
    P = json.load(open(PRED))
    runs = [json.load(open(os.path.join(RAW, f"{n}_{i}.json"))) for n in AUTOMATA for i in range(SEEDS)
            if os.path.exists(os.path.join(RAW, f"{n}_{i}.json"))]
    fit = [r for r in runs if r["fit"] >= 0.99]
    nfit = {n: sum(1 for r in fit if r["automaton"] == n) for n in AUTOMATA}
    ok = lambda r: nfit[r["automaton"]] >= 3
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    kind = lambda r: P[r["automaton"]]["kind"]
    st = [r for r in fit if ok(r) and P[r["automaton"]]["regime"] == "structured"]
    un = [r for r in st if kind(r) == "unique"]
    dg = [r for r in fit if ok(r) and kind(r) == "degenerate"]
    ti = [r for r in fit if ok(r) and kind(r) == "tie" and P[r["automaton"]]["tie_faithful_rule"]]
    f1 = frac([r["rho_predictive"] >= 0.6 for r in st])
    f2 = frac([r["rho_predictive"] > r["rho_onestep"] for r in st])
    f3 = frac([r["best_irrep"] in P[r["automaton"]]["prediction"] for r in un])
    f4 = frac([r["best_irrep"] in P[r["automaton"]]["minimal_faithful"] for r in dg])
    f5 = frac([r["best_irrep"] in P[r["automaton"]]["tie_faithful_rule"] for r in ti])
    f6 = frac([r["best_irrep"] in P[r["automaton"]]["tie_lowdim_rule"] for r in ti])
    dis = [r for r in un if P[r["automaton"]]["smoothest_minimal_faithful"] and P[r["automaton"]]["smoothest_minimal_faithful"] not in P[r["automaton"]]["prediction"]]
    f7 = frac([r["best_irrep"] in P[r["automaton"]]["prediction"] for r in dis])
    f7b = frac([r["best_irrep"] == P[r["automaton"]]["smoothest_minimal_faithful"] for r in dis])
    nauto = lambda rs: len({r["automaton"] for r in rs})
    v = {"H69.1": tri(f1, 0.8, 0.5) if nauto(st) >= 4 else "NO VERDICT",
         "H69.2": tri(f2, 0.8, 0.5) if nauto(st) >= 4 else "NO VERDICT",
         "H69.3": tri(f3, 0.8, 0.5) if nauto(un) >= 4 else "NO VERDICT",
         "H69.4": tri(f4, 0.8, 0.5) if nauto(dg) >= 3 else "NO VERDICT",
         "H69.5": tri(f5, 0.8, 0.5) if nauto(ti) >= 2 else "NO VERDICT",
         "H69.6": tri(f6, 0.8, 0.5) if nauto(ti) >= 2 else "NO VERDICT",
         "H69.7": ("NO VERDICT" if nauto(dis) < 2 else "HELD" if f7 >= 0.8 else "BROKEN" if f7b >= 0.5 else "NEITHER")}
    per = {}
    for n in AUTOMATA:
        rs = [r for r in fit if r["automaton"] == n]
        per[n] = {"fitted": len(rs), "kind": P[n]["kind"], "tau": P[n]["tau"], "prediction": P[n]["prediction"],
                  "best_irreps": [r["best_irrep"] for r in rs], "fits": [round(r["fit"], 3) for r in runs if r["automaton"] == n],
                  "median_rho_predictive": float(np.median([r["rho_predictive"] for r in rs])) if rs else None,
                  "median_rho_onestep": float(np.median([r["rho_onestep"] for r in rs])) if rs else None}
    out = {"verdicts": v, "H69_1_frac": f1, "H69_2_frac": f2, "H69_3_frac": f3, "H69_4_frac": f4, "H69_5_frac": f5, "H69_6_frac": f6, "H69_7_frac_law": f7, "H69_7_frac_bias": f7b, "H69_7_cases": sorted({r["automaton"] for r in dis}),
           "per_automaton": per, "runs": runs}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(per, indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[cmd]()
