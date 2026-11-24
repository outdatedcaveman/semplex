"""Spike 72: does the input encoding decide whether a recurrent network lifts to a cover?
Discrete: A5 read out through its 6 axes (cosets of D5), letters given one-hot, as 3x3 icosahedral rotations
(rho3), or as 5x5 matrices of the 6-axis representation minus trivial (rho5).
Continuous: unsigned axis tracking (Spike 70 task) with rotations given as omega (3), R (9) or D2(R) (25).
See SPIKE_72_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp, cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike72_raw")
OUT = os.path.join(ROOT, "results", "spike72.json")
PRED = os.path.join(ROOT, "results", "spike72_predictions.json")
SEEDS, STEPS, LEN, BATCH = 5, 6000, 30, 64
A5g = [cyc(5, [0, 1, 2]), cyc(5, [0, 1, 2, 3, 4])]
E5 = tuple(range(5))
DISC = ["ONEHOT", "RHO3", "RHO5"]
CONT = ["OMEGA", "D1", "D2"]


def rot(axis, ang):
    k = np.asarray(axis, float); k = k / np.linalg.norm(k)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K


def rho_map(Rx, Ry):
    M = {E5: np.eye(len(Rx))}; fr = [E5]
    while fr:
        g = fr.pop()
        for p, R in ((A5g[0], Rx), (A5g[1], Ry)):
            h = comp(g, p); Rh = M[g] @ R
            if h in M:
                if not np.allclose(M[h], Rh, atol=1e-6): return None
            else: M[h] = Rh; fr.append(h)
    return M if len(M) == 60 else None


def rho3():
    """3-dim icosahedral representation on our generators: rotation by 2pi/3 about z and 2pi/5 about an axis at
    angle theta from z, theta solved so that x∘y (order 5) maps to a rotation by 4pi/5 (found by search; verified)."""
    from scipy.optimize import brentq
    tr = 1 + 2 * np.cos(4 * np.pi / 5)
    f = lambda th: np.trace(rot([0, 0, 1], 2 * np.pi / 3) @ rot([np.sin(th), 0, np.cos(th)], 2 * np.pi / 5)) - tr
    th = brentq(f, 1.3, 1.45)
    M = rho_map(rot([0, 0, 1], 2 * np.pi / 3), rot([np.sin(th), 0, np.cos(th)], 2 * np.pi / 5))
    assert M is not None
    return M


def rho5():
    """6-axis permutation representation (left cosets of D5, permuted by left multiplication) minus trivial,
    in an orthonormal basis; as a right-action homomorphism g -> matrix of right multiplication."""
    G = sorted(closure(A5g)); H = closure([cyc(5, [0, 1, 2, 3, 4]), cyc(5, [1, 4], [2, 3])])
    cos = sorted({frozenset(comp(g, h) for h in H) for g in G}, key=lambda s: sorted(s))
    lab = {g: cos.index(frozenset(comp(g, h) for h in H)) for g in G}
    # right action of A5 on the 6 axes via the identification axis = point stabilised... use the permutation of
    # cosets of D5 induced on RIGHT cosets H g: (H g) a = H (g a)
    rc = sorted({frozenset(comp(h, g) for h in H) for g in G}, key=lambda s: sorted(s))
    rl = {g: rc.index(frozenset(comp(h, g) for h in H)) for g in G}
    def perm(a):
        P = np.zeros((6, 6))
        for g in G: P[rl[g], rl[comp(g, a)]] = 1
        return P
    Q, _ = np.linalg.qr(np.c_[np.ones(6) / np.sqrt(6), np.random.default_rng(0).normal(size=(6, 5))]); B = Q[:, 1:]
    M = rho_map(B.T @ perm(A5g[0]) @ B, B.T @ perm(A5g[1]) @ B)
    assert M is not None
    return M


def disc_spec():
    G = sorted(closure(A5g)); out = S71.coset_out(A5g, [cyc(5, [0, 1, 2, 3, 4]), cyc(5, [1, 4], [2, 3])])
    return G, A5g + [E5], out


def predict():
    G, L, out = disc_spec(); irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    idx = {g: i for i, g in enumerate(G)}; e = idx[E5]
    M3 = rho3(); chi3 = np.array([np.trace(M3[g]) for g in G])
    # which real irreducible does rho3 realise? compare its character with N*P(e,g)/n
    match = {l: float(np.corrcoef(chi3, len(G) * ir["P"][e])[0, 1]) for l, ir in zip(labels, irs)}
    r3 = max(match, key=match.get)
    M5 = rho5(); chi5 = np.array([np.trace(M5[g]) for g in G])
    m5 = {l: float(np.corrcoef(chi5, len(G) * ir["P"][e])[0, 1]) for l, ir in zip(labels, irs)}
    r5 = max(m5, key=m5.get)
    pred = {"rho3_label": r3, "rho3_match": match, "rho5_label": r5, "rho5_match": m5,
            "ONEHOT": r5, "RHO3": r3, "RHO5": r5,
            "note": "rho5 is the readout's own representation (6 axes minus trivial = chi5)."}
    print(json.dumps({k: v for k, v in pred.items() if "match" not in k}, indent=1))
    json.dump(pred, open(PRED, "w"), indent=1)


def run_disc(enc, seed):
    import torch
    nn = torch.nn
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = disc_spec(); idx = {g: i for i, g in enumerate(G)}; k_out = 6
    irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    if enc == "ONEHOT": feat = None
    else:
        M = rho3() if enc == "RHO3" else rho5()
        feat = torch.tensor(np.stack([M[a].ravel() for a in L]), dtype=torch.float32)
    class Net(nn.Module):
        def __init__(s):
            super().__init__()
            s.e = nn.Embedding(len(L), 16) if feat is None else nn.Linear(feat.shape[1], 16)
            s.r = nn.GRU(16, 64, batch_first=True); s.h = nn.Linear(64, k_out)
        def emb(s, X): return s.e(X) if feat is None else s.e(feat[X])
        def hidden(s, X): return s.r(s.emb(X))[0]
        def forward(s, X): return s.h(s.hidden(X))
    m = Net()
    def sample(B, T, r):
        X = r.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, k_out), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            s = E5
            for t in range(T):
                s = comp(s, L[X[b, t]]); Y[b, t] = out(s); ST[b, t] = idx[s]
        return X, Y, ST
    opt = torch.optim.Adam(m.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    for step in range(STEPS):
        X, Y, _ = sample(BATCH, LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y))
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    r = {"part": "disc", "enc": enc, "seed": seed}
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6))
        r["fit"] = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        Xe, Ye, STe = sample(400, LEN, np.random.default_rng(seed + 2 * 10**6))
        H = m.hidden(torch.tensor(Xe)).numpy()
    flatH, flatL = H[:, 5:].reshape(-1, 64), STe[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))])
    C1 = Ce - Ce.mean(0); C1 = C1 / np.linalg.norm(C1, axis=1, keepdims=True)
    R = flatH - Ce[flatL]; W = np.cov(R.T) + 1e-4 * np.eye(64); ev, EV = np.linalg.eigh(W); C2 = (Ce - Ce.mean(0)) @ EV @ np.diag(ev ** -0.5) @ EV.T
    s1, s2 = S71.shares(C1, irs), S71.shares(C2, irs)
    r["shares"] = dict(zip(labels, s1.tolist())); r["shares_white"] = dict(zip(labels, s2.tolist()))
    r["leader"] = labels[int(np.argmax(s1))]; r["leader_white"] = labels[int(np.argmax(s2))]
    return r


def D2(R):
    B = []
    for M in (np.diag([1, -1, 0]) / np.sqrt(2), np.diag([1, 1, -2]) / np.sqrt(6)):
        B.append(M)
    for i, j in ((0, 1), (0, 2), (1, 2)):
        M = np.zeros((3, 3)); M[i, j] = M[j, i] = 1 / np.sqrt(2); B.append(M)
    return np.array([[np.trace(Bk @ R @ Bl @ R.T) for Bl in B] for Bk in B])


def run_cont(enc, seed):
    import torch
    import experiments.spike70 as S70
    from experiments.spike65 import harmonics
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import balanced_accuracy_score
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    def feats(W):
        if enc == "OMEGA": return W
        Fs = np.zeros(W.shape[:2] + ((9,) if enc == "D1" else (25,)), np.float32)
        for b in range(W.shape[0]):
            for t in range(W.shape[1]):
                Rm = S70.rot(W[b, t]); Fs[b, t] = (Rm if enc == "D1" else D2(Rm)).ravel()
        return Fs
    din = {"OMEGA": 3, "D1": 9, "D2": 25}[enc]
    gru = torch.nn.GRU(din, 64, batch_first=True); head = torch.nn.Linear(64, 5)
    opt = torch.optim.Adam(list(gru.parameters()) + list(head.parameters()), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, STEPS)
    for step in range(STEPS):
        W, Y, _ = S70.sample("AXIS", 64, LEN, rng)
        loss = ((head(gru(torch.tensor(feats(W)))[0]) - torch.tensor(Y)) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    r = {"part": "cont", "enc": enc, "seed": seed}
    with torch.no_grad():
        W, Y, _ = S70.sample("AXIS", 500, LEN, np.random.default_rng(seed + 10**6))
        r["fit_r2"] = S70.r2(head(gru(torch.tensor(feats(W)))[0]).numpy(), Y)
        W, Y, U = S70.sample("AXIS", 500, S70.MLEN, np.random.default_rng(seed + 2 * 10**6))
        H = gru(torch.tensor(feats(W)))[0].numpy()
    Hs, Us = H[:, 5:].reshape(-1, 64), U[:, 5:].reshape(-1, 3); Hc = Hs - Hs.mean(0); tot = (Hc ** 2).sum()
    for l, F in harmonics(Us).items():
        F = F - F.mean(0); coef, *_ = np.linalg.lstsq(F, Hc, rcond=None); r[f"R2_l{l}"] = float(1 - ((Hc - F @ coef) ** 2).sum() / tot)
    msk = np.abs(Us[:, 2]) >= 0.3; Xs, ys = Hs[msk], (Us[msk, 2] > 0).astype(int); hl = len(ys) // 2
    clf = LogisticRegression(max_iter=3000, class_weight="balanced").fit(Xs[:hl], ys[:hl])
    r["sign_probe_balanced"] = float(balanced_accuracy_score(ys[hl:], clf.predict(Xs[hl:])))
    return r


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    jobs = [("disc", e) for e in DISC] + [("cont", e) for e in CONT]
    if which: jobs = [j for j in jobs if j[1] in which.split(",")]
    for part, enc in jobs:
        for i in range(SEEDS):
            p = os.path.join(RAW, f"{enc}_{i}.json")
            if os.path.exists(p): continue
            seed = 7200 + 10 * (DISC + CONT).index(enc) + i
            r = run_disc(enc, seed) if part == "disc" else run_cont(enc, seed)
            json.dump(r, open(p, "w"), indent=1)
            print(enc, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k not in ("shares", "shares_white")}, flush=True)


def analyse():
    P = json.load(open(PRED))
    runs = [json.load(open(os.path.join(RAW, f"{e}_{i}.json"))) for e in DISC + CONT for i in range(SEEDS) if os.path.exists(os.path.join(RAW, f"{e}_{i}.json"))]
    F = {e: [r for r in runs if r["enc"] == e and (r.get("fit", 0) >= 0.99 if e in DISC else r.get("fit_r2", 0) >= 0.9)] for e in DISC + CONT}
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    g = lambda e: len(F[e]) >= 3
    f1 = frac([r["leader"] == P["RHO3"] for r in F["RHO3"]]) if g("RHO3") else None
    f2 = frac([r["leader"] == P[r["enc"]] for e in ("ONEHOT", "RHO5") for r in F[e]]) if g("ONEHOT") and g("RHO5") else None
    om = np.median([r["R2_l1"] for r in F["OMEGA"]]) if F["OMEGA"] else None
    if g("D2") and om is not None:
        c3 = frac([r["R2_l1"] < 0.5 * om and r["sign_probe_balanced"] <= 0.75 for r in F["D2"]]); b3 = frac([r["sign_probe_balanced"] >= 0.95 for r in F["D2"]])
        v3 = "HELD" if c3 >= 0.8 else "BROKEN" if b3 >= 0.5 else "NEITHER"
    else: c3 = b3 = None; v3 = "NO VERDICT"
    f4 = frac([r["sign_probe_balanced"] >= 0.95 for r in F["D1"]]) if g("D1") else None
    fW = frac([r["leader_white"] == r["leader"] for e in DISC for r in F[e]])
    v = {"H72.1": tri(f1, 0.8, 0.5), "H72.2": tri(f2, 0.8, 0.5), "H72.3": v3, "H72.4": tri(f4, 0.8, 0.5)}
    summ = {e: [{k: (round(x, 3) if isinstance(x, float) else x) for k, x in r.items() if k not in ("shares", "shares_white")} for r in runs if r["enc"] == e] for e in DISC + CONT}
    out = {"verdicts": v, "frac": {"H72_1": f1, "H72_2": f2, "H72_3_held": c3, "H72_3_broken": b3, "H72_4": f4, "white_agree": fW,
           "omega_median_R2_l1": om}, "fitted": {e: len(F[e]) for e in F}, "runs": summ}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(out["frac"], indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
