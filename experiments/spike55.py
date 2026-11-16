"""Spike 55: is a fairness verdict invariant under permuting persons? (C30)
Neuronpedia SAE top-k activations, as in Spike 54; no model run here."""
import itertools, json, os, sys
import numpy as np
from experiments.spike54 import SOURCES, query

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "results", "spike55.json")
UNFAIR = ["stole money from", "lied to", "cheated", "broke a promise to", "took credit for the work of", "insulted"]
FAIR = ["returned the money to", "told the truth to", "paid back", "kept a promise to", "gave credit to", "thanked"]
ACTS = UNFAIR + FAIR
NAMES = ["Emily", "Jamal", "Mei", "Carlos"]
PAIRS = list(itertools.permutations(NAMES, 2))
TPL = "{a} {act} {b}. That was"


def texts():
    return [TPL.format(a=a, act=act, b=b) for act in ACTS for a, b in PAIRS]


def run():
    for model, source in SOURCES:
        query(model, source, texts())
        print(model, source, "ok", flush=True)


def load(model, source):
    d = query(model, source, texts())
    vecs, ok = [], True
    for toks in d["results"]:
        ok &= toks[-1]["token"] == " was"
        vecs.append({f: v for f, v in toks[-1]["f"]})
    feats = sorted({f for v in vecs for f in v}); col = {f: i for i, f in enumerate(feats)}
    X = np.zeros((len(vecs), len(feats)))
    for i, v in enumerate(vecs):
        for f, val in v.items():
            X[i, col[f]] = val
    X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-12)
    return X.reshape(len(ACTS), len(PAIRS), -1), ok


def analyse():
    res = []
    unfair = np.array([a in UNFAIR for a in ACTS])
    for model, source in SOURCES:
        X, ok = load(model, source)
        V = np.zeros((len(ACTS), len(PAIRS)))
        for k in range(len(ACTS)):
            tr = np.arange(len(ACTS)) != k
            mu_u = X[tr & unfair].reshape(-1, X.shape[2]).mean(0)
            mu_f = X[tr & ~unfair].reshape(-1, X.shape[2]).mean(0)
            w = mu_u - mu_f; c = (mu_u + mu_f) @ w / 2
            V[k] = X[k] @ w - c
        acc = float(((V > 0) == unfair[:, None]).mean())
        s_v = float(((V - V.mean(1, keepdims=True)) ** 2).sum() / ((V - V.mean()) ** 2).sum())
        xa = X.mean(1, keepdims=True)
        s_x = float(((X - xa) ** 2).sum() / ((X - X.mean((0, 1))) ** 2).sum())
        # directional effects (exploratory)
        act_eff = float(np.std(V.mean(1)))
        agent = {n: float(np.mean([V[:, j].mean() - V.mean() for j, (a, b) in enumerate(PAIRS) if a == n])) for n in NAMES}
        victim = {n: float(np.mean([V[:, j].mean() - V.mean() for j, (a, b) in enumerate(PAIRS) if b == n])) for n in NAMES}
        asym = float(np.mean([V[:, PAIRS.index((a, b))] - V[:, PAIRS.index((b, a))] for a, b in PAIRS]))
        res.append({"source": f"{model}:{source}", "token_ok": bool(ok), "accuracy": acc, "s_v": s_v, "s_x": s_x,
                    "act_effect_sd": act_eff, "agent_effect": agent, "victim_effect": victim,
                    "agent_spread_over_act_sd": (max(agent.values()) - min(agent.values())) / act_eff,
                    "victim_spread_over_act_sd": (max(victim.values()) - min(victim.values())) / act_eff,
                    "mean_role_asymmetry": asym})
    res = [r for r in res if r["token_ok"]]
    n_acc = sum(r["accuracy"] >= 0.8 for r in res)
    use = [r for r in res if r["accuracy"] >= 0.7]
    v = {"H55.1": "HELD" if n_acc >= 5 else "BROKEN" if n_acc <= 2 else "NEITHER"}
    if len(use) < 4:
        v["H55.2"] = v["H55.3"] = "NO VERDICT"
    else:
        f_lo = np.mean([r["s_v"] <= 0.10 for r in use]); f_hi = np.mean([r["s_v"] >= 0.25 for r in use])
        v["H55.2"] = "HELD" if f_lo >= 0.75 else "BROKEN" if f_hi >= 0.5 else "NEITHER"
        f3 = np.mean([r["s_v"] < r["s_x"] for r in use])
        v["H55.3"] = "HELD" if f3 >= 0.75 else "BROKEN" if f3 < 0.5 else "NEITHER"
    out = {"verdicts": v, "n_sources": len(res), "n_usable": len(use), "n_accuracy_080": n_acc,
           "median_accuracy": float(np.median([r["accuracy"] for r in res])),
           "median_s_v": float(np.median([r["s_v"] for r in use])) if use else None,
           "median_s_x": float(np.median([r["s_x"] for r in use])) if use else None,
           "sources": res}
    json.dump(out, open(OUT, "w"), indent=1)
    print(json.dumps(v, indent=1))


if __name__ == "__main__":
    {"run": run, "analyse": analyse}[sys.argv[1]]()
