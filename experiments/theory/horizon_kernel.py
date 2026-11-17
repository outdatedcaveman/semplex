"""Exploratory (post hoc on Spike 69): does a discounted predictive kernel K_gamma = sum_t gamma^t E<o(gw),o(hw)>
(short effective horizon) predict the leading constituent in ties and in the Z7_02 exception?
Also reports the letter-walk spectrum |mu_hat(rho)| (largest singular value of the averaged letter operator
restricted to each isotypic component)."""
import json, os, sys
import numpy as np
import experiments.spike69 as S
from experiments.spike58 import comp

def kernel_gamma(name, gamma, T=60):
    G, L, out = S.spec(name); n = len(G); idx = {g: i for i, g in enumerate(G)}
    O = np.array([out(g) for g in G], float)
    pair = np.zeros((n * n, n * n))
    for g in G:
        for h in G:
            for a in L: pair[idx[g] * n + idx[h], idx[comp(g, a)] * n + idx[comp(h, a)]] += 1 / len(L)
    v = (O @ O.T).ravel(); K = np.zeros(n * n); w = 1.0
    for _ in range(T): v = pair @ v; w *= gamma; K += w * v
    K = K.reshape(n, n); return G, K - K.mean(0) - K.mean(1)[:, None] + K.mean()

def mu_spec(name, irs):
    G, L, out = S.spec(name); n = len(G); idx = {g: i for i, g in enumerate(G)}
    M = np.zeros((n, n))
    for g in G:
        for a in L: M[idx[g], idx[comp(g, a)]] += 1 / len(L)
    return {S.irrep_label(ir, k): float(np.linalg.norm(ir["P"] @ M @ ir["P"], 2)) for k, ir in enumerate(irs)}

if __name__ == "__main__":
    obs = json.load(open(os.path.join(S.ROOT, "results", "spike69.json")))["per_automaton"]
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else [n for n in S.AUTOMATA]
    res = {}
    for n in names:
        G, _, _ = S.predictive_kernel(n); irs = S.real_irreps(G); mu = mu_spec(n, irs)
        row = {"mu": mu, "observed": obs[n]["best_irreps"]}
        for gm in (0.3, 0.5, 0.7, 0.9, 0.97):
            _, K = kernel_gamma(n, gm); w = S.isotypic_weights(K, irs); row[f"top_{gm}"] = max(w, key=w.get)
        res[n] = row
        from collections import Counter
        print(n, "obs", Counter(row["observed"]).most_common(1), {k: round(v, 2) for k, v in mu.items()}, {g: row[f"top_{g}"] for g in (0.3, 0.5, 0.7, 0.9, 0.97)}, flush=True)
    json.dump(res, open(os.path.join(S.ROOT, "results", "theory_horizon_kernel.json"), "w"), indent=1)
