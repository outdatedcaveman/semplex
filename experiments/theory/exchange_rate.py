"""Exploratory calibration (post hoc, before registering Spike 77): does a Gibbs-type selection rule
P(rho) ∝ e_rho^alpha * exp(-lambda * c_rho), with e = predictive-energy share and c = letter-action cost
(1 - mean P(e,a)/P(e,e) over non-identity letters), with ONE (alpha, lambda) per resource condition, fit the leaders
observed in Spikes 71, 73, 74, 75, 76? Leave-one-automaton-out log-likelihood vs pure-energy and pure-smoothness."""
import json, os, glob
import numpy as np
from scipy.optimize import minimize
import experiments.spike69 as S69, experiments.spike71 as S71, experiments.spike73 as S73, experiments.spike74 as S74, experiments.spike75 as S75, experiments.spike76 as S76
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

def feats(specf, name):
    S71.spec = specf; S71._patch()
    G, Kc, _ = S69.predictive_kernel(name); irs = S69.real_irreps(G); wt = S69.isotypic_weights(Kc, irs)
    L = specf(name)[1]; lab = [S69.irrep_label(ir, k) for k, ir in enumerate(irs)]
    return {l: (max(wt[l], 1e-6), 1 - S69.smoothness(ir, G, L)) for l, ir in zip(lab, irs)}

cases = []   # (condition, automaton, feats, observed leaders)
def add(cond, specf, name, leaders):
    if leaders: cases.append((cond, name, feats(specf, name), leaders))
r71 = json.load(open(os.path.join(R, "spike71.json")))["per_automaton"]
for n, p in r71.items():
    if not n.startswith("A5"): add("default", S71.spec if False else (lambda nm, t=S71.table(): (sorted(__import__('experiments.spike58', fromlist=['closure']).closure(t[nm][0])), t[nm][0] + [tuple(range(len(t[nm][0][0])))], t[nm][1])), n, p["final"])
for n, rs in json.load(open(os.path.join(R, "spike73.json")))["per"].items():
    if n in S73.CYC: add("default", S73.cyc_spec, n, [r["final_leader"] for r in rs if r.get("fit", 0) >= 0.99])
for n, x in json.load(open(os.path.join(R, "spike74.json")))["per"].items():
    add("default", S74.spec, n, [l for l, f in zip(x["final"], x["fits"]) if f >= 0.99])
for f in glob.glob(os.path.join(R, "spike75_raw", "GRU_*.json")):
    r = json.load(open(f))
    if r["fit"] >= 0.99: add("default", S75.spec, r["automaton"], [r["leader"]])
for f in glob.glob(os.path.join(R, "spike76_raw", "*.json")):
    r = json.load(open(f))
    if r["substrate"] != "GRU": continue
    cond = "default" if (r["width"] == 64 and r["eta"] == 0.0) else f"w{r['width']}_n{r['eta']}"
    lead = max(r["shares"], key=r["shares"].get); add(cond, S76.spec, r["automaton"], [lead])

def nll(params, cs):
    a, lam = params; tot = 0.0
    for _, _, F, obs in cs:
        ks = list(F); s = np.array([a * np.log(F[k][0]) - lam * F[k][1] for k in ks]); p = np.exp(s - s.max()); p /= p.sum()
        for o in obs:
            if o in ks: tot -= np.log(p[ks.index(o)] + 1e-12)
    return tot

out = {}
for cond in sorted({c[0] for c in cases}):
    cs = [c for c in cases if c[0] == cond]; nobs = sum(len(c[3]) for c in cs)
    fit = minimize(nll, [1.0, 1.0], args=(cs,), method="Nelder-Mead")
    e_only = minimize(lambda p: nll([p[0], 0.0], cs), [1.0], method="Nelder-Mead")
    s_only = minimize(lambda p: nll([0.0, p[0]], cs), [1.0], method="Nelder-Mead")
    # leave-one-automaton-out predictive log-lik (both params)
    names = sorted({c[1] for c in cs}); loo = 0.0; acc = []
    for nm in names:
        tr = [c for c in cs if c[1] != nm]; te = [c for c in cs if c[1] == nm]
        if not tr: continue
        f = minimize(nll, [1.0, 1.0], args=(tr,), method="Nelder-Mead"); loo += nll(f.x, te)
        for _, _, F, obs in te:
            ks = list(F); s = [f.x[0] * np.log(F[k][0]) - f.x[1] * F[k][1] for k in ks]; pred = ks[int(np.argmax(s))]
            acc += [o == pred for o in obs]
    out[cond] = {"n_automata": len(names), "n_obs": nobs, "alpha": float(fit.x[0]), "lambda": float(fit.x[1]),
                 "nll_both": float(fit.fun), "nll_energy_only": float(e_only.fun), "nll_smooth_only": float(s_only.fun),
                 "loo_nll": loo, "loo_argmax_acc": float(np.mean(acc)) if acc else None, "chance_nll": float(sum(len(c[3]) * np.log(len(c[2])) for c in cs))}
    print(cond, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out[cond].items()})
json.dump(out, open(os.path.join(R, "theory_exchange_rate.json"), "w"), indent=1)
