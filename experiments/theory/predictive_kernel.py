"""Exact predictive-state kernel for the Spike 60 automata (no training).
K_T(g,h) = sum_{t=1..T} E_w[<o(g w), o(h w)>], w a uniform random word of length t.
For a uniformly mixing walk, E_w <o(gw),o(hw)> -> |H| chi_perm(g^-1 h)/|G| = chi_perm(g^-1 h)/[G:H]:
the predictive geometry is the readout permutation character (derivation in FOUNDATIONS §11.4)."""
import json, os, numpy as np
from scipy.stats import spearmanr
import experiments.spike60 as S
from experiments.spike58 import comp, inv

def kernel(name, T=30):
    G, H, cos, lab = S.setup(name); gens = S.GENS[name.split("_")[0]]; n = len(G)
    idx = {g: i for i, g in enumerate(G)}
    O = np.zeros((n, len(cos)))
    for g in G: O[idx[g], lab[g]] = 1
    pair = np.zeros((n * n, n * n))
    for g in G:
        for h in G:
            for a in gens: pair[idx[g] * n + idx[h], idx[comp(g, a)] * n + idx[comp(h, a)]] += 1 / len(gens)
    v = (O @ O.T).ravel(); K = np.zeros(n * n)
    for _ in range(T): v = pair @ v; K += v
    K = K.reshape(n, n); return K - K.mean(0) - K.mean(1)[:, None] + K.mean(), G

if __name__ == "__main__":
    out = {}
    for name in S.AUTOMATA:
        Kc, G = kernel(name); iu = np.triu_indices(len(G), 1)
        pc = S.perm_char(name); tab, _ = S.irreps(name)
        ker = lambda f: np.array([[f(comp(inv(a), b)) for b in G] for a in G], float)
        sc = {k: float(spearmanr(Kc[iu], ker(f)[iu])[0]) for k, f in tab}
        sc["readout_perm_minus_1"] = float(spearmanr(Kc[iu], ker(lambda x: pc(x) - 1)[iu])[0])
        out[name] = sc
    json.dump(out, open(os.path.join(S.ROOT, "results", "theory_predictive_kernel.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
