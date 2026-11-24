"""Spike 19 exploratory (post hoc, NOT pre-registered): is the stabilizer term needed once agreement and
solid angle are in the universal unit-weight law? Compare nested models on the held-out elements."""
import json, math
import numpy as np
from collections import defaultdict
from scipy.optimize import minimize
from experiments import spike14 as S14, spike19 as S

tb, ex, els, iso = S14.setup()
perm = np.random.default_rng(1901).permutation(len(els))
tr = [els[i] for i in perm[:64]]; te = [els[i] for i in perm[64:]]
feats, okey, osz = S.unit_features(els, iso)
tot = lambda c: {k: c[0].get(k, 0) + c[1].get(k, 0) for k in set(c[0]) | set(c[1])}
s14 = json.loads((S14.RAW / "A8.json").read_text())["counts"]; fresh = json.loads((S.RAW / "arm1.json").read_text())["counts"]
s14c = {e: tot(s14[str(e)]) for e in els}; fr = {e: tot(fresh[str(e)]) for e in els}
for name, mask in (("agree+omega", (0, 1, 1)), ("stab+agree", (1, 1, 0)), ("stab+omega", (1, 0, 1)), ("agree only", (0, 1, 0)), ("all three", (1, 1, 1))):
    m = np.array(mask, float)
    r = minimize(lambda p: -S.loglik(p * m, {e: s14c[e] for e in tr}, feats, iso), np.zeros(3), method="Nelder-Mead", options={"maxiter": 2000})
    p = r.x * m
    f = lambda e: {f"{x}-{y}": sum(p[0]*feats[e][t][0] + p[1]*feats[e][t][1] + p[2]*feats[e][t][2] for t in (x, y)) for x, y in iso[e]}
    def sc(data):
        g = n = 0.0
        for e in te:
            gb, N = S.gain_bits(f(e), data[e], iso[e])
            if gb is not None: g += gb; n += N
        return round(g / n, 3)
    print(name.ljust(12), "params", np.round(p, 3), "held-out S14", sc(s14c), "fresh", sc(fr))
