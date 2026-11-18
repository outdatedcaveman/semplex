"""Spike 77: prospective test of the Gibbs selection rule (C43; calibrated post hoc in experiments/theory/exchange_rate.py):
P(leader = rho) ∝ e_rho^ALPHA * exp(-LAMBDA * c_rho), e = predictive-energy share, c = letter-action cost
(1 - mean P(e,a)/P(e,e) over non-identity letters). ALPHA, LAMBDA frozen from the default-condition fit before any run.
Rivals: energy-only and smoothness-only rules with their own frozen fitted parameters. Pressure arm: state noise eta = 1.0
should raise the exchange rate lambda/alpha. See SPIKE_77_REPORT.md."""
import itertools, json, os, sys
import numpy as np
from experiments.spike58 import cyc, closure
import experiments.spike69 as S69
import experiments.spike71 as S71
import experiments.spike75 as S75
import experiments.spike76 as S76

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "results", "spike77_raw")
OUT = os.path.join(ROOT, "results", "spike77.json")
PRED = os.path.join(ROOT, "results", "spike77_predictions.json")
CAL = json.load(open(os.path.join(ROOT, "results", "theory_exchange_rate.json")))["default"]
ALPHA, LAMBDA = CAL["alpha"], CAL["lambda"]
SEEDS = 5

def zstep(n, s): return tuple((i + s) % n for i in range(n))
def dih(m): return [cyc(m, list(range(m))), tuple((-i) % m for i in range(m))]
A4g = [cyc(4, [0, 1, 2]), cyc(4, [0, 1], [2, 3])]
S3g = [cyc(3, [0, 1]), cyc(3, [0, 1, 2])]
POOL = {}
for n in (7, 8, 11, 12):
    for s in (1, 2, 3):
        if np.gcd(s, n) != 1: continue
        for S in itertools.combinations(range(1, n), 2):
            POOL[f"Z{n}_s{s}_{''.join(f'{x:x}' for x in (0,) + S)}"] = ([zstep(n, s)], frozenset((0,) + S))
for m in (5, 7):
    POOL[f"D{m}_pt"] = (dih(m), "pt"); POOL[f"D{m}_sub01"] = (dih(m), frozenset({0, 1}))
POOL["A4_sub012"] = (A4g, frozenset({0, 1})); POOL["S3_pt"] = (S3g, "pt")

def spec(name):
    g, S = POOL[name]; n = len(g[0])
    out = (lambda x, n=n: tuple(int(x[0] == i) for i in range(n))) if S == "pt" else (lambda x, S=S: (int(x[0] in S),))
    return sorted(closure(g)), g + [tuple(range(n))], out

def feats(name):
    S71.spec = spec; S71._patch()
    G, Kc, _ = S69.predictive_kernel(name); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs); L = spec(name)[1]
    return {S69.irrep_label(ir, k): (max(wt[S69.irrep_label(ir, k)], 1e-6), 1 - S69.smoothness(ir, G, L)) for k, ir in enumerate(irs)}

def probs(F, a, lam):
    ks = list(F); s = np.array([a * np.log(F[k][0]) - lam * F[k][1] for k in ks]); p = np.exp(s - s.max()); return dict(zip(ks, p / p.sum()))

USED = {"Z7_s1_01", "Z7_s2_01", "D5_pt", "D6_pt"}   # names already run in Spikes 69-76 (same construction)

def predict():
    from scipy.optimize import minimize
    # rival parameters frozen from the same calibration data
    import experiments.theory.exchange_rate as XR
    cs = [c for c in XR.cases if c[0] == "default"]
    ea = minimize(lambda p: XR.nll([p[0], 0.0], cs), [1.0], method="Nelder-Mead").x[0]
    sl = minimize(lambda p: XR.nll([0.0, p[0]], cs), [1.0], method="Nelder-Mead").x[0]
    rows = {}
    for name in POOL:
        if name in USED: continue
        F = feats(name); pg = probs(F, ALPHA, LAMBDA); pe = probs(F, ea, 0.0); ps = probs(F, 0.0, sl)
        mg, me, ms = max(pg, key=pg.get), max(pe, key=pe.get), max(ps, key=ps.get)
        rows[name] = {"gibbs": pg, "energy": pe, "smooth": ps, "argmax": {"gibbs": mg, "energy": me, "smooth": ms}, "pmax": pg[mg]}
    # choose automata: Gibbs disagrees with at least one rival, confident (pmax >= 0.6); balance types; at most 12
    cand = [n for n, r in rows.items() if r["pmax"] >= 0.6 and (r["argmax"]["gibbs"] != r["argmax"]["energy"] or r["argmax"]["gibbs"] != r["argmax"]["smooth"])]
    rng = np.random.default_rng(77); pick = []
    for prefix in ("Z7", "Z8", "Z11", "Z12", "D5", "D7", "A4", "S3"):
        grp = [n for n in cand if n.startswith(prefix + "_")]
        if grp: pick += list(rng.choice(grp, size=min(2, len(grp)), replace=False))
    P = {"alpha": ALPHA, "lambda": LAMBDA, "energy_alpha": float(ea), "smooth_lambda": float(sl), "automata": pick,
         "rows": {n: rows[n] for n in pick}, "n_pool": len(rows), "n_candidates": len(cand)}
    json.dump(P, open(PRED, "w"), indent=1)
    for n in pick: print(n, rows[n]["argmax"], round(rows[n]["pmax"], 2))
    print(len(pick), "automata;", len(cand), "candidates of", len(rows))

def run(which=None):
    import torch
    torch.set_num_threads(2); os.makedirs(RAW, exist_ok=True); P = json.load(open(PRED))
    S71.spec = spec; S75.spec = spec; S76.S75.spec = spec
    jobs = [(n, 0.0) for n in P["automata"]] + [(n, 1.0) for n in P["automata"][::2]]
    if which: jobs = [j for j in jobs if str(j[1]) in which.split(",")]
    for name, eta in jobs:
        for i in range(SEEDS if eta == 0.0 else 3):
            p = os.path.join(RAW, f"{name}_n{eta}_{i}.json")
            if os.path.exists(p): continue
            seed = 7700 + 10 * P["automata"].index(name) + i + (500 if eta else 0)
            if eta == 0.0:
                r = S71.run_one(name, seed); r.pop("traj", None); sh = None
                lead = r["final_leader"]; fit = r["fit"]
            else:
                rr = S76.run_gru(("N", name, 64, eta, "GRU"), seed); sh = rr["shares"]; lead = max(sh, key=sh.get); fit = rr["fit"]
            out = {"automaton": name, "eta": eta, "seed": seed, "fit": fit, "leader": lead}
            json.dump(out, open(p, "w")); print(name, eta, i, round(fit, 3), lead, flush=True)

def analyse():
    P = json.load(open(PRED)); runs = [json.load(open(os.path.join(RAW, f))) for f in sorted(os.listdir(RAW))]
    d = [r for r in runs if r["eta"] == 0.0 and r["fit"] >= 0.99]
    nll = {m: -sum(np.log(P["rows"][r["automaton"]][m][r["leader"]] + 1e-12) for r in d) for m in ("gibbs", "energy", "smooth")}
    acc = float(np.mean([r["leader"] == P["rows"][r["automaton"]]["argmax"]["gibbs"] for r in d])) if d else None
    nq = len({r["automaton"] for r in d})
    v = {}
    if nq >= 5:
        v["H77.1"] = "HELD" if nll["gibbs"] < min(nll["energy"], nll["smooth"]) else "BROKEN"
        v["H77.2"] = "HELD" if acc >= 0.75 else "BROKEN" if acc < 0.5 else "NEITHER"
    else: v["H77.1"] = v["H77.2"] = "NO VERDICT"
    # H77.3 pressure raises the exchange rate: refit (alpha, lambda) on eta = 1 runs (no fit guard) vs default runs of the same automata
    from scipy.optimize import minimize
    def fitc(rs):
        def f(pp):
            a, lam = pp; t = 0.0
            for r in rs:
                F = feats(r["automaton"]); pr = probs(F, a, lam); t -= np.log(pr[r["leader"]] + 1e-12)
            return t
        return minimize(f, [1.0, 1.0], method="Nelder-Mead").x
    hi = [r for r in runs if r["eta"] == 1.0]; base = [r for r in runs if r["eta"] == 0.0 and r["automaton"] in {x["automaton"] for x in hi}]
    if len(hi) >= 9 and base:
        a1, l1 = fitc(hi); a0, l0 = fitc(base); rate1 = l1 / max(abs(a1), 1e-6); rate0 = l0 / max(abs(a0), 1e-6)
        v["H77.3"] = "HELD" if rate1 > rate0 else "BROKEN"
    else: rate0 = rate1 = None; v["H77.3"] = "NO VERDICT"
    per = {n: {"pred": P["rows"][n]["argmax"], "default": [r["leader"] for r in runs if r["automaton"] == n and r["eta"] == 0.0],
               "fits": [round(r["fit"], 3) for r in runs if r["automaton"] == n and r["eta"] == 0.0],
               "eta1": [r["leader"] for r in runs if r["automaton"] == n and r["eta"] == 1.0]} for n in P["automata"]}
    out = {"verdicts": v, "nll": nll, "gibbs_argmax_acc": acc, "n_automata": nq, "rate_default": rate0, "rate_eta1": rate1, "per": per}
    json.dump(out, open(OUT, "w"), indent=1); print(json.dumps({k: out[k] for k in ("verdicts", "nll", "gibbs_argmax_acc", "rate_default", "rate_eta1")}, indent=1))
    for n, x in per.items(): print(n, x)

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "run": run(sys.argv[2] if len(sys.argv) > 2 else None)
    else: {"predict": predict, "analyse": analyse}[c]()
