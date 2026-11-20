"""Spike 79: remaining loopholes of the Gibbs selection rule (C43), alpha/lambda FROZEN from Spike 77:
(A) unselected NON-ABELIAN automata (GRU+Adam); (B) other substrates: evolution strategies (no gradients) and a
transformer (no recurrence) on unselected cyclic automata; (C) the cost from first principles: the kinetic
(minimum-dissipation, straight-line) displacement cost E||rho(a)x - x||^2 over the representation's unit sphere
equals 2*c_rho exactly; registered against the alternative geodesic cost E[angle(x, rho(a)x)^2].
See SPIKE_79_REPORT.md."""
import json, os, sys, itertools
import numpy as np
from experiments.spike58 import comp, cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike77 as S77
import experiments.spike78 as S78

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike79_raw")
OUT = os.path.join(ROOT, "results", "spike79.json")
PRED = os.path.join(ROOT, "results", "spike79_predictions.json")
ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA

def ident(n): return tuple(range(n))
def dihed(m, kind):
    r = cyc(m, list(range(m))); f = tuple((-i) % m for i in range(m)); f2 = tuple((1 - i) % m for i in range(m))
    return [r, f] if kind == "rf" else [f, f2]
GROUPS = {
    "S3c": [cyc(3, [0, 1]), cyc(3, [0, 1, 2])], "S3t": [cyc(3, [0, 1]), cyc(3, [1, 2])],
    "D4rf": dihed(4, "rf"), "D4ff": dihed(4, "ff"), "D5rf": dihed(5, "rf"), "D5ff": dihed(5, "ff"), "D6rf": dihed(6, "rf"),
    "A4a": [cyc(4, [0, 1, 2]), cyc(4, [0, 1], [2, 3])], "A4b": [cyc(4, [0, 1, 2]), cyc(4, [1, 2, 3])],
    "S4c": [cyc(4, [0, 1]), cyc(4, [0, 1, 2, 3])], "S4x": [cyc(4, [0, 1]), cyc(4, [1, 2]), cyc(4, [2, 3])],
}
POOL = {}
for gname, g in GROUPS.items():
    n = len(g[0])
    POOL[f"{gname}_pt"] = (g, "pt")
    for S in itertools.combinations(range(1, n), 1): POOL[f"{gname}_sub0{S[0]}"] = (g, frozenset({0, S[0]}))
    if n >= 4:
        for S in itertools.combinations(range(1, n), 2): POOL[f"{gname}_sub0{S[0]}{S[1]}"] = (g, frozenset({0, *S}))
POOL["Q8_sub"] = (None, frozenset({0, 2, 4})); POOL["Q8_sub2"] = (None, frozenset({0, 2}))

def spec(name):
    g, S = POOL[name]
    if g is None:
        from experiments.spike66 import q8
        g = q8()
    n = len(g[0])
    out = (lambda x, n=n: tuple(int(x[0] == i) for i in range(n))) if S == "pt" else (lambda x, S=S: (int(x[0] in S),))
    return sorted(closure(g)), g + [ident(n)], out

def feats(name, specf=None):
    specf = specf or spec; G, L, out = specf(name)
    irs = S69.real_irreps(G); wt = S69.isotypic_weights(S78.wkernel(G, L, [1 / len(L)] * len(L), out), irs)
    idx = {g: i for i, g in enumerate(G)}; e = idx[ident(len(G[0]))]; N = len(G)
    nz = [a for a in L if a != ident(len(G[0]))]; rng = np.random.default_rng(0); F = {}
    for k, ir in enumerate(irs):
        lab = S69.irrep_label(ir, k)
        c = float(np.mean([1 - ir["P"][e, idx[a]] / ir["P"][e, e] for a in nz]))
        # geodesic alternative: mean squared angle between x and its image, x uniform on the isotypic unit sphere
        w, V = np.linalg.eigh(ir["P"]); U = V[:, w > 0.5]; geo = []
        for a in nz:
            Ra = np.zeros((N, N))
            for g in G: Ra[idx[g], idx[comp(g, a)]] = 1
            Rp = U.T @ Ra @ U; X = rng.normal(size=(400, U.shape[1])); X /= np.linalg.norm(X, axis=1, keepdims=True)
            geo.append(np.mean(np.arccos(np.clip(np.sum(X * (X @ Rp.T), 1), -1, 1)) ** 2))
        F[lab] = (max(wt[lab], 1e-6), c, float(np.mean(geo)))
    return F

def probs(F, a, lam, which=1):
    ks = list(F); s = np.array([a * np.log(F[k][0]) - lam * F[k][which] for k in ks]); p = np.exp(s - s.max()); return dict(zip(ks, p / p.sum()))

def predict():
    P77 = json.load(open(S77.PRED)); P78 = json.load(open(S78.PRED))
    pool = sorted(n for n in POOL if n != "S3c_pt")          # S3_pt (same construction) was run in Spike 77
    rng = np.random.default_rng(79); sample = sorted(rng.choice(pool, size=10, replace=False).tolist())
    rows = {}
    for n in sample:
        F = feats(n); pg = probs(F, ALPHA, LAMBDA); pe = probs(F, P77["energy_alpha"], 0.0); ps = probs(F, 0.0, P77["smooth_lambda"])
        rows[n] = {"F": F, "gibbs": pg, "energy": pe, "smooth": ps, "argmax": {m: max(d, key=d.get) for m, d in (("gibbs", pg), ("energy", pe), ("smooth", ps))}}
    cyc6 = P78["sample"][:6]; crow = {}
    for n in cyc6:
        F = feats(n, S77.spec); pg = probs(F, ALPHA, LAMBDA); pe = probs(F, P77["energy_alpha"], 0.0); ps = probs(F, 0.0, P77["smooth_lambda"])
        crow[n] = {"F": F, "gibbs": pg, "energy": pe, "smooth": ps, "argmax": {m: max(d, key=d.get) for m, d in (("gibbs", pg), ("energy", pe), ("smooth", ps))}}
    # (C) refit both cost forms on the calibration data (Spikes 71, 73-76) for the cost comparison
    import experiments.theory.exchange_rate as XR
    from scipy.optimize import minimize
    P = {"alpha": ALPHA, "lambda": LAMBDA, "energy_alpha": P77["energy_alpha"], "smooth_lambda": P77["smooth_lambda"],
         "sample": sample, "rows": rows, "cyc6": cyc6, "crows": crow}
    json.dump(P, open(PRED, "w"), indent=1)
    for n in sample: print(n, rows[n]["argmax"], round(max(rows[n]["gibbs"].values()), 2))
    for n in cyc6: print(n, crow[n]["argmax"])

def train(name, learner, seed, specf):
    import torch
    from experiments.spike60 import build
    nn = torch.nn
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = specf(name); idx = {g: i for i, g in enumerate(G)}; e = ident(len(G[0])); k = len(out(e))
    def sample(B, T, r):
        X = r.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, k), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            s = e
            for t in range(T): s = comp(s, L[X[b, t]]); Y[b, t] = out(s); ST[b, t] = idx[s]
        return X, Y, ST
    if learner == "es":
        from torch.nn.utils import parameters_to_vector, vector_to_parameters
        m = build("gru", len(L), k); th = parameters_to_vector(m.parameters()).detach().clone(); mo = torch.zeros_like(th); vv = torch.zeros_like(th)
        def lv(v, X, Y):
            vector_to_parameters(v, m.parameters())
            with torch.no_grad(): return float(nn.functional.binary_cross_entropy_with_logits(m(X), Y))
        for it in range(1, 4001):
            Xn, Yn, _ = sample(32, 20, rng); X, Y = torch.tensor(Xn), torch.tensor(Yn)
            eps = torch.randn(32, th.numel()); eps = torch.cat([eps, -eps]); f = torch.tensor([lv(th + 0.05 * e_, X, Y) for e_ in eps])
            w = torch.argsort(torch.argsort(f)).float() / (len(f) - 1) - 0.5; gr = (w[:, None] * eps).sum(0) / (len(f) * 0.05)
            mo = 0.9 * mo + 0.1 * gr; vv = 0.999 * vv + 0.001 * gr * gr; th = th - 0.03 * (mo / (1 - 0.9 ** it)) / (torch.sqrt(vv / (1 - 0.999 ** it)) + 1e-8)
        vector_to_parameters(th, m.parameters())
    else:
        m = build("gru" if learner == "gru" else "tf", len(L), k)
        opt = torch.optim.Adam(m.parameters(), lr=0.003 if learner == "gru" else 0.001); sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 6000)
        for _ in range(6000):
            X, Y, _ = sample(64, 30, rng)
            loss = nn.functional.binary_cross_entropy_with_logits(m(torch.tensor(X)), torch.tensor(Y)); opt.zero_grad(); loss.backward(); opt.step(); sch.step()
    m.eval()
    with torch.no_grad():
        flen = 100 if learner != "tf" else 30
        X, Y, _ = sample(500, flen, np.random.default_rng(seed + 10**6)); fit = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, 30, np.random.default_rng(seed + 2 * 10**6)); H = m.hidden(torch.tensor(X)).numpy()
    irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, kk) for kk, ir in enumerate(irs)]; d = H.shape[-1]
    flatH, flatL = H[:, 5:].reshape(-1, d), ST[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == j].mean(0) if (flatL == j).any() else np.zeros(d) for j in range(len(G))])
    C1 = Ce - Ce.mean(0); C1 = C1 / np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
    s1 = S71.shares(C1, irs)
    return {"fit": fit, "leader": labels[int(np.argmax(s1))]}

def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED))
    jobs = [(n, "gru", spec) for n in P["sample"]] + [(n, l, S77.spec) for l in ("tf", "es") for n in P["cyc6"]]
    if which: jobs = [j for j in jobs if j[1] in which.split(",")]
    for name, learner, sp in jobs:
        for i in range(3):
            tag = f"{learner}_{name}_{i}"; pth = os.path.join(RAW, tag + ".json")
            if os.path.exists(pth): continue
            seed = 7900 + 1000 * ["gru", "tf", "es"].index(learner) + 10 * (P["sample"] + P["cyc6"]).index(name) + i
            r = train(name, learner, seed, sp); r.update({"automaton": name, "learner": learner, "seed": seed})
            json.dump(r, open(pth, "w")); print(tag, round(r["fit"], 3), r["leader"], flush=True)

def analyse():
    from scipy.optimize import minimize
    P = json.load(open(PRED)); runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    rowsof = lambda r: P["rows"][r["automaton"]] if r["learner"] == "gru" else P["crows"][r["automaton"]]
    fit = [r for r in runs if r["fit"] >= 0.99]
    det = {}
    for l in ("gru", "tf", "es"):
        rs = [r for r in fit if r["learner"] == l]
        det[l] = {"n_runs": len(rs), "n_automata": len({r["automaton"] for r in rs}),
                  "acc": float(np.mean([r["leader"] == rowsof(r)["argmax"]["gibbs"] for r in rs])) if rs else None,
                  "nll": {m: float(-sum(np.log(rowsof(r)[m][r["leader"]] + 1e-12) for r in rs)) for m in ("gibbs", "energy", "smooth")} if rs else None}
    g = det["gru"]; v = {}
    v["H79.1"] = "NO VERDICT" if g["n_automata"] < 5 else ("HELD" if g["acc"] >= 0.75 and g["nll"]["gibbs"] < min(g["nll"]["energy"], g["nll"]["smooth"]) else "BROKEN" if g["acc"] < 0.5 else "NEITHER")
    for l, hid in (("es", "H79.2"), ("tf", "H79.3")):
        d = det[l]
        v[hid] = "NO VERDICT" if d["n_automata"] < 4 else ("HELD" if d["nll"]["gibbs"] < min(d["nll"]["energy"], d["nll"]["smooth"]) else "BROKEN")
    # H79.4 cost form: refit (alpha, lambda) for chord (index 1) and geodesic (index 2) on all fitted Spike 79 runs, leave-one-automaton-out
    allr = fit; names = sorted({(r["learner"], r["automaton"]) for r in allr}); res = {}
    for which in (1, 2):
        tot = 0.0
        for nm in names:
            tr = [r for r in allr if (r["learner"], r["automaton"]) != nm]; te = [r for r in allr if (r["learner"], r["automaton"]) == nm]
            f = lambda pp: -sum(np.log(probs({k: tuple(v_) for k, v_ in rowsof(r)["F"].items()}, pp[0], pp[1], which)[r["leader"]] + 1e-12) for r in tr)
            x = minimize(f, [ALPHA, LAMBDA], method="Nelder-Mead").x
            tot += -sum(np.log(probs({k: tuple(v_) for k, v_ in rowsof(r)["F"].items()}, x[0], x[1], which)[r["leader"]] + 1e-12) for r in te)
        res[{1: "chord", 2: "geodesic"}[which]] = float(tot)
    v["H79.4"] = "NO VERDICT" if len(names) < 6 else ("HELD" if res["chord"] < res["geodesic"] else "BROKEN")
    per = {}
    for r in runs: per.setdefault(f"{r['learner']}/{r['automaton']}", []).append((r["leader"], round(r["fit"], 3)))
    out = {"verdicts": v, "learners": det, "cost_loo_nll": res, "per": per,
           "pred": {**{f"gru/{n}": P["rows"][n]["argmax"] for n in P["sample"]}, **{f"cyc/{n}": P["crows"][n]["argmax"] for n in P["cyc6"]}}}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps(v, indent=1)); print(json.dumps(det, indent=1)); print(res)
    for k, x in per.items(): print(k, x)

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
