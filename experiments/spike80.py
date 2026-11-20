"""Spike 80: three targeted tests of the Gibbs selection rule (C43).
(a) cost form: kinetic (chord^2, = 2c) vs geodesic (angle^2) on two-letter cyclic automata chosen so the two forms
    predict different leaders; both forms calibrated beforehand on Spikes 77-79 GRU runs;
(b) gradient-free learner at convergence: evolution strategies with 12,000 iterations on small automata, frozen rule;
(c) non-abelian automata where the frozen rule and energy-only disagree, sampled at random from that subpopulation.
See SPIKE_80_REPORT.md."""
import json, os, sys, itertools, glob
import numpy as np
from scipy.optimize import minimize
from experiments.spike58 import comp, cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike77 as S77
import experiments.spike79 as S79

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike80_raw")
OUT = os.path.join(ROOT, "results", "spike80.json")
PRED = os.path.join(ROOT, "results", "spike80_predictions.json")
ALPHA, LAMBDA = S77.ALPHA, S77.LAMBDA

def ident(n): return tuple(range(n))
def zstep(n, s): return tuple((i + s) % n for i in range(n))
def dihed(m, kind):
    r = cyc(m, list(range(m))); f = tuple((-i) % m for i in range(m)); f2 = tuple((1 - i) % m for i in range(m)); r2 = tuple((i + 2) % m for i in range(m))
    return {"rf": [r, f], "ff": [f, f2], "r2f": [r2, f]}[kind]

POOL = {}
for n in (7, 9, 11):                                   # (a) two-letter cyclic: +a, +b
    for a, b in itertools.combinations(range(1, n // 2 + 1), 2):
        for S in itertools.combinations(range(1, n), 2):
            POOL[f"T{n}_{a}{b}_{''.join(f'{x:x}' for x in (0,) + S)}"] = ([zstep(n, a), zstep(n, b)], frozenset((0,) + S))
for m in (5, 6, 7, 8):                                  # (c) non-abelian pool
    for kind in ("rf", "ff", "r2f"):
        if kind == "r2f" and m % 2 == 0: continue
        g = dihed(m, kind); POOL[f"N_D{m}{kind}_pt"] = (g, "pt")
        for S in itertools.combinations(range(1, m), 1): POOL[f"N_D{m}{kind}_s0{S[0]}"] = (g, frozenset({0, S[0]}))
        for S in itertools.combinations(range(1, m), 2): POOL[f"N_D{m}{kind}_s0{S[0]}{S[1]}"] = (g, frozenset({0, *S}))
for gname, g in S79.GROUPS.items():
    if gname.startswith("D"): continue
    n = len(g[0])
    for S in itertools.combinations(range(1, n), 2): POOL[f"N_{gname}_s0{S[0]}{S[1]}"] = (g, frozenset({0, *S}))
ES_AUT = ["Z7_s1_015", "Z7_s3_023", "Z8_s3_015"]          # Spike 77 automata (rule-discriminating), small groups

def spec(name):
    if name in ES_AUT: return S77.spec(name)
    g, S = POOL[name]; n = len(g[0])
    out = (lambda x, n=n: tuple(int(x[0] == i) for i in range(n))) if S == "pt" else (lambda x, S=S: (int(x[0] in S),))
    return sorted(closure(g)), g + [ident(n)], out

def feats(name, specf=None):
    S79_spec = S79.spec
    return S79.feats(name, specf or spec)

def probs(F, a, lam, which=1): return S79.probs(F, a, lam, which)

def calibrate():
    """fit (alpha, lambda) for chord (index 1) and geodesic (index 2) on fitted GRU runs of Spikes 77-79 (default condition)"""
    cases = []
    for f in glob.glob(os.path.join(ROOT, "results", "spike77_raw", "*_n0.0_*.json")):
        r = json.load(open(f))
        if r["fit"] >= 0.99: cases.append((S77.spec, r["automaton"], r["leader"]))
    for f in glob.glob(os.path.join(ROOT, "results", "spike78_raw", "*_gru_adam_[0-9].json")):
        r = json.load(open(f))
        if r["fit"] >= 0.99 and r["freq"] is None: cases.append((S77.spec, r["automaton"], r["leader"]))
    for f in glob.glob(os.path.join(ROOT, "results", "spike79_raw", "gru_*.json")):
        r = json.load(open(f))
        if r["fit"] >= 0.99: cases.append((S79.spec, r["automaton"], r["leader"]))
    Fc = {}
    for sp, n, _ in cases:
        if n not in Fc: Fc[n] = S79.feats(n, sp)
    out = {}
    for which, nm in ((1, "chord"), (2, "geodesic")):
        f = lambda pp: -sum(np.log(probs(Fc[n], pp[0], pp[1], which)[l] + 1e-12) for _, n, l in cases)
        x = minimize(f, [ALPHA, LAMBDA], method="Nelder-Mead").x; out[nm] = {"alpha": float(x[0]), "lambda": float(x[1]), "nll": float(f(x))}
    out["n_cases"] = len(cases); return out

def predict():
    cal = calibrate(); print("calibration", cal)
    P77 = json.load(open(S77.PRED))
    rows_a, rows_c = {}, {}
    for name in POOL:
        F = feats(name)
        if name.startswith("T"):
            pc = probs(F, cal["chord"]["alpha"], cal["chord"]["lambda"], 1); pg = probs(F, cal["geodesic"]["alpha"], cal["geodesic"]["lambda"], 2)
            mc, mg = max(pc, key=pc.get), max(pg, key=pg.get)
            # confidence threshold lowered from 0.6 to 0.45 before any run (0 candidates at 0.6)
            if mc != mg and pc[mc] >= 0.45 and pg[mg] >= 0.45: rows_a[name] = {"chord": pc, "geodesic": pg, "argmax": {"chord": mc, "geodesic": mg}}
        else:
            pgb = probs(F, ALPHA, LAMBDA); pe = probs(F, P77["energy_alpha"], 0.0); ps = probs(F, 0.0, P77["smooth_lambda"])
            mg, me = max(pgb, key=pgb.get), max(pe, key=pe.get)
            if mg != me: rows_c[name] = {"gibbs": pgb, "energy": pe, "smooth": ps, "argmax": {"gibbs": mg, "energy": me, "smooth": max(ps, key=ps.get)}}
    rng = np.random.default_rng(80)
    A = sorted(rng.choice(sorted(rows_a), size=min(8, len(rows_a)), replace=False).tolist()) if rows_a else []
    C = sorted(rng.choice(sorted(rows_c), size=min(8, len(rows_c)), replace=False).tolist()) if rows_c else []
    es = {}
    for n in ES_AUT:
        F = feats(n); es[n] = {"gibbs": probs(F, ALPHA, LAMBDA), "energy": probs(F, P77["energy_alpha"], 0.0), "smooth": probs(F, 0.0, P77["smooth_lambda"])}
        es[n]["argmax"] = {m: max(es[n][m], key=es[n][m].get) for m in ("gibbs", "energy", "smooth")}
    P = {"calibration": cal, "A": A, "rows_a": {n: rows_a[n] for n in A}, "n_a_candidates": len(rows_a),
         "C": C, "rows_c": {n: rows_c[n] for n in C}, "n_c_candidates": len(rows_c), "ES": ES_AUT, "rows_es": es}
    json.dump(P, open(PRED, "w"), indent=1)
    print("A", len(rows_a), [(n, rows_a[n]["argmax"]) for n in A]); print("C", len(rows_c), [(n, rows_c[n]["argmax"]) for n in C]); print("ES", {n: es[n]["argmax"] for n in ES_AUT})

def es_train(name, seed, iters=12000):
    import torch
    from torch.nn.utils import parameters_to_vector, vector_to_parameters
    from experiments.spike60 import build
    nn = torch.nn
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    G, L, out = spec(name); idx = {g: i for i, g in enumerate(G)}; e = ident(len(G[0])); k = len(out(e))
    def sample(B, T, r):
        X = r.integers(0, len(L), size=(B, T)); Y = np.zeros((B, T, k), np.float32); ST = np.zeros((B, T), int)
        for b in range(B):
            s = e
            for t in range(T): s = comp(s, L[X[b, t]]); Y[b, t] = out(s); ST[b, t] = idx[s]
        return X, Y, ST
    m = build("gru", len(L), k); th = parameters_to_vector(m.parameters()).detach().clone(); mo = torch.zeros_like(th); vv = torch.zeros_like(th)
    def lv(v, X, Y):
        vector_to_parameters(v, m.parameters())
        with torch.no_grad(): return float(nn.functional.binary_cross_entropy_with_logits(m(X), Y))
    for it in range(1, iters + 1):
        Xn, Yn, _ = sample(32, 30, rng); X, Y = torch.tensor(Xn), torch.tensor(Yn)
        eps = torch.randn(32, th.numel()); eps = torch.cat([eps, -eps]); f = torch.tensor([lv(th + 0.03 * e_, X, Y) for e_ in eps])
        w = torch.argsort(torch.argsort(f)).float() / (len(f) - 1) - 0.5; gr = (w[:, None] * eps).sum(0) / (len(f) * 0.03)
        lr = 0.03 * 0.5 * (1 + np.cos(np.pi * it / iters))
        mo = 0.9 * mo + 0.1 * gr; vv = 0.999 * vv + 0.001 * gr * gr; th = th - lr * (mo / (1 - 0.9 ** it)) / (torch.sqrt(vv / (1 - 0.999 ** it)) + 1e-8)
    vector_to_parameters(th, m.parameters()); m.eval()
    with torch.no_grad():
        X, Y, _ = sample(500, 100, np.random.default_rng(seed + 10**6)); fit = float(((m(torch.tensor(X)) > 0).float() == torch.tensor(Y)).float().mean())
        X, Y, ST = sample(400, 30, np.random.default_rng(seed + 2 * 10**6)); H = m.hidden(torch.tensor(X)).numpy()
    irs = S69.real_irreps(G); labels = [S69.irrep_label(ir, kk) for kk, ir in enumerate(irs)]
    flatH, flatL = H[:, 5:].reshape(-1, 64), ST[:, 5:].ravel()
    Ce = np.stack([flatH[flatL == j].mean(0) for j in range(len(G))]); C1 = Ce - Ce.mean(0); C1 /= np.maximum(np.linalg.norm(C1, axis=1, keepdims=True), 1e-12)
    return {"fit": fit, "leader": labels[int(np.argmax(S71.shares(C1, irs)))]}

def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED))
    jobs = [("a", n) for n in P["A"]] + [("c", n) for n in P["C"]] + [("es", n) for n in P["ES"]]
    if which: jobs = [j for j in jobs if j[0] in which.split(",")]
    for arm, name in jobs:
        for i in range(5 if arm == "a" else 3):
            pth = os.path.join(RAW, f"{arm}_{name}_{i}.json")
            if os.path.exists(pth): continue
            seed = 8000 + 1000 * ["a", "c", "es"].index(arm) + 10 * (P["A"] + P["C"] + P["ES"]).index(name) + i
            if arm == "es": r = es_train(name, seed)
            else: r = S79.train(name, "gru", seed, spec)
            r.update({"arm": arm, "automaton": name, "seed": seed}); json.dump(r, open(pth, "w")); print(arm, name, i, round(r["fit"], 3), r["leader"], flush=True)

def analyse():
    P = json.load(open(PRED)); runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    fit = [r for r in runs if r["fit"] >= 0.99]; v = {}; out = {}
    a = [r for r in fit if r["arm"] == "a"]
    if len({r["automaton"] for r in a}) >= 4:
        nc = -sum(np.log(P["rows_a"][r["automaton"]]["chord"][r["leader"]] + 1e-12) for r in a)
        ng = -sum(np.log(P["rows_a"][r["automaton"]]["geodesic"][r["leader"]] + 1e-12) for r in a)
        hc = float(np.mean([r["leader"] == P["rows_a"][r["automaton"]]["argmax"]["chord"] for r in a])); hg = float(np.mean([r["leader"] == P["rows_a"][r["automaton"]]["argmax"]["geodesic"] for r in a]))
        v["H80.1"] = "HELD" if nc < ng else "BROKEN"; out["a"] = {"nll_chord": nc, "nll_geodesic": ng, "acc_chord": hc, "acc_geodesic": hg}
    else: v["H80.1"] = "NO VERDICT"
    es = [r for r in fit if r["arm"] == "es"]
    if len({r["automaton"] for r in es}) >= 2:
        acc = float(np.mean([r["leader"] == P["rows_es"][r["automaton"]]["argmax"]["gibbs"] for r in es]))
        v["H80.2"] = "HELD" if acc >= 0.75 else "BROKEN" if acc < 0.5 else "NEITHER"; out["es"] = {"acc": acc, "n": len(es)}
    else: v["H80.2"] = "NO VERDICT"
    c = [r for r in fit if r["arm"] == "c"]
    if len({r["automaton"] for r in c}) >= 4:
        nll = {m: -sum(np.log(P["rows_c"][r["automaton"]][m][r["leader"]] + 1e-12) for r in c) for m in ("gibbs", "energy", "smooth")}
        acc = float(np.mean([r["leader"] == P["rows_c"][r["automaton"]]["argmax"]["gibbs"] for r in c]))
        v["H80.3"] = "HELD" if acc >= 0.7 and nll["gibbs"] < min(nll["energy"], nll["smooth"]) else "BROKEN" if acc < 0.5 else "NEITHER"; out["c"] = {"acc": acc, "nll": nll}
    else: v["H80.3"] = "NO VERDICT"
    per = {}
    for r in runs: per.setdefault(f"{r['arm']}/{r['automaton']}", []).append((r["leader"], round(r["fit"], 3)))
    out.update({"verdicts": v, "per": per})
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps({k: out[k] for k in out if k != "per"}, indent=1))
    for k, x in per.items(): print(k, x)

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
