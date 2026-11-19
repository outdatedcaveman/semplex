"""Spike 81: the selection rule beyond groups. For an arbitrary deterministic automaton (random transition maps,
including non-invertible ones: resets, merges), on its minimal states Q with visit distribution pi:
  modes v_i   = eigenvectors of the pi-weighted, centred predictive kernel K on Q;
  value e_i   = eigenvalue share of K;
  cost c_i    = (1/2) * mean_a E_pi[(v_i(delta_a q) - v_i(q))^2] / E_pi[v_i^2]   (kinetic displacement of the mode
                under each letter; for group automata and isotypic v this equals the c_rho used in Spikes 77-80).
Rule (alpha, lambda frozen from Spike 77): P(mode i) ∝ e_i^alpha * exp(-lambda c_i). Learned 'leader' = the mode best
aligned with the top eigenvector of the learned pi-weighted centroid Gram. See SPIKE_81_REPORT.md."""
import json, os, sys
import numpy as np
import experiments.spike77 as S77

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike81_raw")
OUT = os.path.join(ROOT, "results", "spike81.json")
PRED = os.path.join(ROOT, "results", "spike81_predictions.json")
ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA
SEEDS, LEN, T_H = 3, 30, 30


def random_automaton(rng, n, k_letters, kind):
    """transition table d[a][q] and binary output o[q]; kind: 'perm' (all letters bijective), 'mixed' (one letter a
    reset or merge), 'free' (arbitrary maps)."""
    d = []
    for a in range(k_letters):
        if kind == "perm" or (kind == "mixed" and a > 0): d.append(rng.permutation(n))
        elif kind == "mixed": m = rng.integers(0, n, size=n); m[rng.integers(n)] = m[0]; d.append(m)
        else: d.append(rng.integers(0, n, size=n))
    o = rng.integers(0, 2, size=n)
    return np.array(d), o


def minimize(d, o, start=0):
    """reachable states from start, then Moore minimisation; returns (D, O, start) on minimal states"""
    k, n = d.shape; reach = {start}; fr = [start]
    while fr:
        q = fr.pop()
        for a in range(k):
            if d[a][q] not in reach: reach.add(int(d[a][q])); fr.append(int(d[a][q]))
    R = sorted(reach); cls = {q: int(o[q]) for q in R}
    while True:
        sig = {q: (cls[q],) + tuple(cls[int(d[a][q])] for a in range(k)) for q in R}
        ids = {s: i for i, s in enumerate(sorted(set(sig.values())))}; new = {q: ids[sig[q]] for q in R}
        if len(set(new.values())) == len(set(cls.values())): cls = new; break
        cls = new
    m = len(set(cls.values())); D = np.zeros((k, m), int); O = np.zeros(m, int)
    for q in R:
        O[cls[q]] = o[q]
        for a in range(k): D[a][cls[q]] = cls[int(d[a][q])]
    return D, O, cls[start]


def visit_dist(D, s0, letters_p, T=LEN, burn=5):
    k, m = D.shape; p = np.zeros(m); p[s0] = 1; acc = np.zeros(m)
    for t in range(T):
        q = np.zeros(m)
        for a in range(k): np.add.at(q, D[a], p * letters_p[a])
        p = q
        if t >= burn: acc += p
    return acc / acc.sum()


def modes(D, O, pi, letters_p):
    k, m = D.shape
    # predictive kernel: K(q,r) = sum_t E_w [o(q w) o(r w)] for random words of length t (uniform letters)
    Pq = [np.eye(m)[D[a]] for a in range(k)]                      # Pq[a][q] = one-hot of delta_a(q)
    M = sum(w * P for w, P in zip(letters_p, Pq))                  # Markov operator on states (row q -> next-state dist)
    pair = np.zeros((m * m, m * m))
    for a in range(k):
        for q in range(m):
            for r in range(m): pair[q * m + r, D[a][q] * m + D[a][r]] += letters_p[a]
    v = np.outer(O, O).astype(float).ravel(); K = np.zeros(m * m)
    for _ in range(T_H): v = pair @ v; K += v
    K = K.reshape(m, m)
    W = np.diag(np.sqrt(pi)); one = np.sqrt(pi)[:, None]; C = np.eye(m) - one @ one.T          # pi-centring in sqrt-space
    Kw = C @ W @ K @ W @ C; ev, EV = np.linalg.eigh(Kw); order = np.argsort(-ev); ev, EV = ev[order], EV[:, order]
    keep = ev > 1e-9 * max(ev.max(), 1e-12); ev, EV = ev[keep], EV[:, keep]
    share = ev / ev.sum(); V = EV / np.sqrt(pi)[:, None]             # back to functions on states (pi-orthonormal)
    out = []
    for i in range(V.shape[1]):
        vi = V[:, i]; den = np.sum(pi * vi ** 2)
        c = 0.5 * np.mean([np.sum(pi * (vi[D[a]] - vi) ** 2) / den for a in range(k)])
        out.append({"value": float(share[i]), "cost": float(c), "v": vi.tolist()})
    return out


def predict_rule(ms, a=ALPHA, lam=LAMBDA):
    s = np.array([a * np.log(max(x["value"], 1e-6)) - lam * x["cost"] for x in ms]); p = np.exp(s - s.max()); return (p / p.sum()).tolist()


def build_pool():
    rng = np.random.default_rng(81); pool = []
    while len(pool) < 600:
        n = int(rng.integers(5, 10)); k = int(rng.integers(2, 4)); kind = ["perm", "mixed", "free"][len(pool) % 3]
        d, o = random_automaton(rng, n, k, kind); D, O, s0 = minimize(d, o)
        if D.shape[1] < 4 or O.min() == O.max(): continue
        pool.append({"kind": kind, "D": D.tolist(), "O": O.tolist(), "s0": int(s0)})
    return pool


def predict():
    pool = build_pool(); rows = []
    for i, A in enumerate(pool):
        D, O = np.array(A["D"]), np.array(A["O"]); k = D.shape[0]; lp = np.ones(k + 1) / (k + 1)   # + identity letter
        Dl = np.vstack([D, np.arange(D.shape[1])[None]])
        pi = visit_dist(Dl, A["s0"], lp); ms = modes(Dl, O, pi, lp)
        if len(ms) < 2: continue
        pg = predict_rule(ms); pe = predict_rule(ms, 1.0, 0.0); ps = predict_rule(ms, 0.0, 3.0)
        rows.append({"id": i, **A, "pi": pi.tolist(), "modes": ms, "gibbs": pg, "energy": pe, "smooth": ps,
                     "argmax": {"gibbs": int(np.argmax(pg)), "energy": int(np.argmax(pe)), "smooth": int(np.argmax(ps))}})
    rng = np.random.default_rng(810)
    disc = [r for r in rows if r["argmax"]["gibbs"] != r["argmax"]["energy"]]
    rand = [rows[j] for j in rng.choice(len(rows), size=12, replace=False)]
    dsel = [disc[j] for j in rng.choice(len(disc), size=min(12, len(disc)), replace=False)] if disc else []
    P = {"alpha": ALPHA, "lambda": LAMBDA, "random": rand, "discriminating": dsel, "n_pool": len(rows), "n_disc": len(disc)}
    json.dump(P, open(PRED, "w"))
    from collections import Counter
    print("pool", len(rows), "discriminating", len(disc), "kinds random", Counter(r["kind"] for r in rand), "kinds disc", Counter(r["kind"] for r in dsel))


def train(A, seed):
    import torch
    from experiments.spike60 import build
    nn = torch.nn
    D, O = np.array(A["D"]), np.array(A["O"]); k, m = D.shape; Dl = np.vstack([D, np.arange(m)[None]]); L = k + 1
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    def sample(B, T, r):
        X = r.integers(0, L, size=(B, T)); Y = np.zeros((B, T, 1), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            q = A["s0"]
            for t in range(T): q = Dl[X[b, t]][q]; Y[b, t, 0] = O[q]; ST[b, t] = q
        return X, Y, ST
    mdl = build("gru", L, 1); opt = torch.optim.Adam(mdl.parameters(), lr=0.003); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
    for _ in range(6000):
        X, Y, _ = sample(64, LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(torch.tensor(X)), torch.tensor(Y)); opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((mdl(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, LEN, np.random.default_rng(seed + 2 * 10**6)); H = mdl.hidden(torch.tensor(X)).numpy()
    flatH, flatL = H[:, 5:].reshape(-1, 64), ST[:, 5:].ravel()
    pi = np.array(A["pi"]); Ce = np.stack([flatH[flatL == q].mean(0) if (flatL == q).any() else np.zeros(64) for q in range(m)])
    mu = (pi[:, None] * Ce).sum(0); Cc = Ce - mu
    # learned pi-weighted Gram's top eigenvector as a function on states
    G = (np.sqrt(pi)[:, None] * Cc) @ (np.sqrt(pi)[:, None] * Cc).T; ev, EV = np.linalg.eigh(G); u = EV[:, -1] / np.sqrt(pi)
    al = []
    for md in A["modes"]:
        v = np.array(md["v"]); al.append(abs(np.sum(pi * u * v)) / np.sqrt(np.sum(pi * u * u) * np.sum(pi * v * v)))
    return {"fit": fit, "leader": int(np.argmax(al)), "alignment": [float(x) for x in al], "top_eig_share": float(ev[-1] / max(ev.sum(), 1e-12))}


def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED))
    sets = [("rand", r) for r in P["random"]] + [("disc", r) for r in P["discriminating"]]
    if which: sets = [s for s in sets if s[0] in which.split(",")]
    for tag, A in sets:
        for i in range(SEEDS):
            pth = os.path.join(RAW, f"{tag}_{A['id']}_{i}.json")
            if os.path.exists(pth): continue
            r = train(A, 8100 + 10 * A["id"] + i); r.update({"set": tag, "id": A["id"], "kind": A["kind"]})
            json.dump(r, open(pth, "w")); print(tag, A["id"], A["kind"], i, round(r["fit"], 3), r["leader"], "pred", A["argmax"], flush=True)


def analyse():
    P = json.load(open(PRED)); byid = {r["id"]: r for r in P["random"] + P["discriminating"]}
    runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]; fit = [r for r in runs if r["fit"] >= 0.99]
    def score(rs):
        if not rs: return None
        nll = {m: float(-sum(np.log(byid[r["id"]][m][r["leader"]] + 1e-12) for r in rs)) for m in ("gibbs", "energy", "smooth")}
        acc = float(np.mean([r["leader"] == byid[r["id"]]["argmax"]["gibbs"] for r in rs]))
        return {"n": len(rs), "n_automata": len({r["id"] for r in rs}), "acc": acc, "nll": nll}
    s_r = score([r for r in fit if r["set"] == "rand"]); s_d = score([r for r in fit if r["set"] == "disc"])
    s_np = score([r for r in fit if r["kind"] != "perm"])
    tri = lambda s, hi: "NO VERDICT" if s is None or s["n_automata"] < 5 else ("HELD" if s["acc"] >= hi and s["nll"]["gibbs"] < min(s["nll"]["energy"], s["nll"]["smooth"]) else "BROKEN" if s["acc"] < 0.5 else "NEITHER")
    v = {"H81.1": tri(s_r, 0.6), "H81.2": tri(s_d, 0.6), "H81.3": tri(s_np, 0.6)}
    out = {"verdicts": v, "random": s_r, "discriminating": s_d, "non_permutation": s_np,
           "per": [{k: r[k] for k in ("set", "id", "kind", "fit", "leader")} | {"pred": byid[r["id"]]["argmax"]} for r in runs]}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps({k: out[k] for k in ("verdicts", "random", "discriminating", "non_permutation")}, indent=1))


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
