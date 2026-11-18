"""Spike 75: are closure and the predictive-energy shape law substrate-independent? The same automata are learned by
(GRU) gradient-trained recurrent network; (SPEC) exact spectral learner: SVD of the Hankel matrix of future outputs
(predictive-state compression, no neurons, no gradients); (RES) fixed random echo-state reservoir with a trained
linear readout only (no adaptive state); (ES) recurrent network trained by evolution strategies (no gradients).
See SPIKE_75_REPORT.md."""
import json, os, sys
import numpy as np
from experiments.spike58 import comp, cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike75_raw")
OUT = os.path.join(ROOT, "results", "spike75.json")
PRED = os.path.join(ROOT, "results", "spike75_predictions.json")
SEEDS = {"GRU": 5, "SPEC": 3, "RES": 5, "ES": 3}
A4g = [cyc(4, [0, 1, 2]), cyc(4, [0, 1], [2, 3])]
S4g = [cyc(4, [0, 1]), cyc(4, [0, 1, 2, 3])]
Z6 = [tuple((i + 1) % 6 for i in range(6))]
Z9 = [tuple((i + 1) % 9 for i in range(9))]
PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
TABLE = {
    "Z6_mod3": (Z6, lambda x: (int(x[0] % 3 == 0),)),
    "A4_4": (A4g, lambda x: tuple(int(x[0] == i) for i in range(4))),
    "A4_6": (A4g, lambda x: tuple(int({x[0], x[1]} == set(p)) for p in PAIRS)),
    "S4_12": (S4g, S71.coset_out(S4g, [cyc(4, [0, 1])])),
    "Z9_s1_014": (Z9, lambda x: (int(x[0] in {0, 1, 4}),)),
}
NAMES = list(TABLE)
ES_NAMES = ["Z6_mod3", "A4_4", "A4_6"]


def spec(name):
    g, out = TABLE[name]; n = len(g[0])
    return sorted(closure(g)), g + [tuple(range(n))], out


def predict():
    S71.spec = spec; S71._patch(); P = {}
    for n in NAMES:
        G, Kc, _ = S69.predictive_kernel(n); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs)
        srt = sorted(wt, key=wt.get, reverse=True)
        P[n] = {"energy": srt[0] if wt[srt[0]] >= 1.5 * wt[srt[1]] else None, "shares": wt,
                "minimal_states": len(set(S71.minimal_states(n).values())) if hasattr(S71, "minimal_states") else None}
        print(n, P[n]["energy"], {k: round(v, 2) for k, v in wt.items()})
    json.dump(P, open(PRED, "w"), indent=1)


# ---------------------------------------------------------------- data
def sample(name, B, T, rng):
    G, L, out = spec(name); e = tuple(range(len(G[0]))); idx = {g: i for i, g in enumerate(G)}
    X = rng.integers(0, len(L), size=(B, T)); k = len(out(e)); Y = np.zeros((B, T, k), np.float32); ST = np.zeros((B, T), int)
    for b in range(B):
        s = e
        for t in range(T):
            s = comp(s, L[X[b, t]]); Y[b, t] = out(s); ST[b, t] = idx[s]
    return X, Y, ST


def acc_of(P, Y): return float(((P > 0.5) == (Y > 0.5)).mean())


# ---------------------------------------------------------------- substrates: each returns (H eval states B x T x d, fit accuracy)
def sub_gru(name, seed):
    import torch
    S71.spec = spec
    from experiments.spike60 import build
    torch.manual_seed(seed); rng = np.random.default_rng(seed); G, L, out = spec(name); k = len(out(tuple(range(len(G[0])))))
    m = build("gru", len(L), k); opt = torch.optim.Adam(m.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
    for _ in range(6000):
        X, Y, _ = sample(name, 64, 30, rng)
        loss = torch.nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y)); opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(name, 500, 100, np.random.default_rng(seed + 10**6)); fit = acc_of(torch.sigmoid(m(torch.tensor(X))).numpy(), Y)
        X, Y, ST = sample(name, 400, 30, np.random.default_rng(seed + 2 * 10**6)); H = m.hidden(torch.tensor(X)).numpy()
    return H, ST, fit


def sub_res(name, seed, N=200, rho=0.9):
    rng = np.random.default_rng(seed); G, L, out = spec(name); k = len(out(tuple(range(len(G[0])))))
    Win = rng.normal(0, 1, (len(L), N)); W = rng.normal(0, 1, (N, N)); W *= rho / max(abs(np.linalg.eigvals(W)))
    def run(X):
        H = np.zeros(X.shape + (N,)); h = np.zeros((X.shape[0], N))
        for t in range(X.shape[1]): h = np.tanh(h @ W.T + Win[X[:, t]]); H[:, t] = h
        return H
    X, Y, _ = sample(name, 400, 60, rng); Htr = run(X)[:, 10:].reshape(-1, N); Ytr = Y[:, 10:].reshape(-1, k)
    A = np.c_[Htr, np.ones(len(Htr))]; Wout = np.linalg.solve(A.T @ A + 1e-2 * np.eye(N + 1), A.T @ Ytr)
    X, Y, _ = sample(name, 500, 100, np.random.default_rng(seed + 10**6)); Hf = run(X)
    fit = acc_of(np.c_[Hf.reshape(-1, N), np.ones(Hf.shape[0] * Hf.shape[1])] @ Wout, Y.reshape(-1, k))
    X, Y, ST = sample(name, 400, 30, np.random.default_rng(seed + 2 * 10**6))
    return run(X), ST, fit


def sub_spec(name, seed, n_suffix=300, max_len=8):
    """Hankel matrix: rows = histories (eval strings at each step), columns = (suffix, output bit) future outputs.
    The learned state is the projection onto the nonzero right-singular subspace (exact rank)."""
    rng = np.random.default_rng(seed); G, L, out = spec(name); idx = {g: i for i, g in enumerate(G)}; e = tuple(range(len(G[0])))
    sufs = [rng.integers(0, len(L), size=rng.integers(1, max_len + 1)) for _ in range(n_suffix)]
    def fut(g):
        v = []
        for s in sufs:
            x = g
            for a in s: x = comp(x, L[a])
            v.extend(out(x))
        return np.array(v, float)
    F = np.stack([fut(g) for g in G])                       # future-output vector per state (exact)
    X, Y, ST = sample(name, 400, 30, np.random.default_rng(seed + 2 * 10**6))
    Hk = F[ST.ravel()]                                       # Hankel rows for the sampled histories
    Hc = Hk - Hk.mean(0); U, s, Vt = np.linalg.svd(Hc, full_matrices=False); r = int((s > 1e-6 * s[0]).sum())
    H = (Hc @ Vt[:r].T).reshape(ST.shape + (r,))
    return H, ST, 1.0


def sub_es(name, seed, iters=4000, pop=64, sigma=0.05, lr=0.03):
    import torch
    from torch.nn.utils import parameters_to_vector, vector_to_parameters
    from experiments.spike60 import build
    torch.manual_seed(seed); rng = np.random.default_rng(seed); G, L, out = spec(name); k = len(out(tuple(range(len(G[0])))))
    m = build("gru", len(L), k); theta = parameters_to_vector(m.parameters()).detach().clone()
    mom = torch.zeros_like(theta); vv = torch.zeros_like(theta)
    def loss_at(v, X, Y):
        vector_to_parameters(v, m.parameters())
        with torch.no_grad(): return float(torch.nn.functional.binary_cross_entropy_with_logits(m(X), Y))
    for it in range(1, iters + 1):
        Xn, Yn, _ = sample(name, 32, 20, rng); X, Y = torch.tensor(Xn), torch.tensor(Yn)
        eps = torch.randn(pop // 2, theta.numel()); eps = torch.cat([eps, -eps])
        f = torch.tensor([loss_at(theta + sigma * e_, X, Y) for e_ in eps])
        rk = torch.argsort(torch.argsort(f)).float(); w = (rk / (len(f) - 1) - 0.5)        # centred ranks
        g = (w[:, None] * eps).sum(0) / (len(f) * sigma)                                   # descent direction estimate (minimise loss)
        mom = 0.9 * mom + 0.1 * g; vv = 0.999 * vv + 0.001 * g * g
        theta = theta - lr * (mom / (1 - 0.9 ** it)) / (torch.sqrt(vv / (1 - 0.999 ** it)) + 1e-8)
    vector_to_parameters(theta, m.parameters())
    with torch.no_grad():
        X, Y, _ = sample(name, 500, 100, np.random.default_rng(seed + 10**6)); fit = acc_of(torch.sigmoid(m(torch.tensor(X))).numpy(), Y)
        X, Y, ST = sample(name, 400, 30, np.random.default_rng(seed + 2 * 10**6)); H = m.hidden(torch.tensor(X)).numpy()
    return H, ST, fit


SUBS = {"GRU": sub_gru, "RES": sub_res, "SPEC": sub_spec, "ES": sub_es}


def measure(name, H, ST):
    from sklearn.linear_model import LogisticRegression
    S71.spec = spec; S71._patch()
    G, L, out = spec(name); irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    flatH, flatL = H[:, 5:].reshape(-1, H.shape[-1]), ST[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))])
    C1 = Ce - Ce.mean(0); C1 = C1 / np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
    s1 = S71.shares(C1, irs)
    r = {"leader": labels[int(np.argmax(s1))], "shares": dict(zip(labels, s1.tolist()))}
    cls = S71.minimal_states(name); mlab = np.array([cls[G[i]] for i in flatL]); h = len(flatL) // 2
    r["probe_macro"] = float(LogisticRegression(max_iter=3000).fit(flatH[:h], mlab[:h]).score(flatH[h:], mlab[h:]))
    r["probe_element"] = float(LogisticRegression(max_iter=3000).fit(flatH[:h], flatL[:h]).score(flatH[h:], flatL[h:]))
    if name == "Z6_mod3":
        par = np.array([G[i][0] % 2 for i in flatL])
        r["probe_mod2"] = float(LogisticRegression(max_iter=3000).fit(flatH[:h], par[:h]).score(flatH[h:], par[h:]))
    return r


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True)
    jobs = [(s, n) for s in SUBS for n in (ES_NAMES if s == "ES" else NAMES)]
    if which: jobs = [j for j in jobs if j[0] in which.split(",")]
    for sub, name in jobs:
        for i in range(SEEDS[sub]):
            p = os.path.join(RAW, f"{sub}_{name}_{i}.json")
            if os.path.exists(p): continue
            seed = 7500 + 100 * list(SUBS).index(sub) + 10 * NAMES.index(name) + i
            H, ST, fit = SUBS[sub](name, seed); r = measure(name, H, ST); r.update({"substrate": sub, "automaton": name, "seed": seed, "fit": fit})
            json.dump(r, open(p, "w"), indent=1)
            print(sub, name, i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "shares"}, flush=True)


def analyse():
    P = json.load(open(PRED))
    runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    tri = lambda f, hi, lo: "NO VERDICT" if f is None else "HELD" if f >= hi else "BROKEN" if f < lo else "NEITHER"
    frac = lambda xs: float(np.mean(xs)) if xs else None
    adaptive_fit = lambda r: r["substrate"] == "SPEC" or (r["substrate"] in ("GRU", "ES") and r["fit"] >= 0.99)
    by = lambda s, n: [r for r in runs if r["substrate"] == s and r["automaton"] == n]
    # H75.1 closure discards the unobservable part in every ADAPTIVE substrate (Z6 read mod 3)
    z = {s: [r["probe_mod2"] for r in by(s, "Z6_mod3") if adaptive_fit(r)] for s in ("GRU", "SPEC", "ES")}
    med = {s: (float(np.median(v)) if len(v) >= 2 or (s == "SPEC" and v) else None) for s, v in z.items()}
    have = [s for s in med if med[s] is not None]
    v1 = "NO VERDICT" if len(have) < 2 else ("HELD" if all(med[s] <= 0.6 for s in have) else "BROKEN" if sum(med[s] >= 0.9 for s in have) >= 1 else "NEITHER")
    # H75.4 a non-adaptive substrate (fixed reservoir) does NOT contain the minimal automaton
    rp = [r["probe_macro"] for n in NAMES for r in by("RES", n)]
    f4 = frac([x <= 0.9 for x in rp]); v4 = "NO VERDICT" if f4 is None else ("HELD" if f4 >= 0.8 else "BROKEN" if f4 < 0.5 else "NEITHER")
    # H75.2 energy law across adaptive substrates (A4_6, S4_12)
    ad = [r for r in runs if r["automaton"] in ("A4_6", "S4_12") and r["substrate"] in ("GRU", "SPEC", "ES") and adaptive_fit(r) and P[r["automaton"]]["energy"]]
    f2 = frac([r["leader"] == P[r["automaton"]]["energy"] for r in ad])
    subs2 = {r["substrate"] for r in ad}
    v2 = tri(f2, 0.8, 0.5) if len(subs2) >= 2 else "NO VERDICT"
    # H75.3 readout-independence of the reservoir: same leader for A4_4 and A4_6 (same seeds' reservoirs)
    pairs = [(a, b) for a in by("RES", "A4_4") for b in by("RES", "A4_6") if a["seed"] % 10 == b["seed"] % 10]
    f3 = frac([a["leader"] == b["leader"] for a, b in pairs])
    gp = [(a, b) for a in by("GRU", "A4_4") for b in by("GRU", "A4_6") if a["seed"] % 10 == b["seed"] % 10 and adaptive_fit(a) and adaptive_fit(b)]
    f3g = frac([a["leader"] == b["leader"] for a, b in gp])
    v3 = "NO VERDICT" if f3 is None or f3g is None else ("HELD" if f3 >= 0.8 and f3g <= 0.2 else "BROKEN" if f3 <= f3g else "NEITHER")
    v = {"H75.1": v1, "H75.2": v2, "H75.3": v3, "H75.4": v4}
    table = {}
    for s in SUBS:
        for n in NAMES:
            rs = by(s, n)
            if rs: table[f"{s}/{n}"] = {"fit": [round(r["fit"], 3) for r in rs], "leader": [r["leader"] for r in rs],
                                        "probe_macro": [round(r["probe_macro"], 3) for r in rs], "probe_element": [round(r["probe_element"], 3) for r in rs],
                                        "probe_mod2": [round(r.get("probe_mod2", float("nan")), 3) for r in rs]}
    out = {"verdicts": v, "z6_median_mod2": med, "energy_frac": f2, "energy_substrates": sorted(subs2), "res_same_leader": f3, "gru_same_leader": f3g, "table": table}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps({k: out[k] for k in ("z6_median_mod2", "energy_frac", "res_same_leader", "gru_same_leader")}, indent=1))
    for k, x in table.items(): print(k, x)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
