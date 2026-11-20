"""Spike 17 exploratory (post hoc, NOT pre-registered): is the unit-level Curie bias the pull toward the
target's Chow direction? Unit mass vs (a) stabilizer size, (b) cosine of the unit's l2-max-margin weight
vector with the target's Chow vector.  python -m experiments.spike17_explore"""
import json, math
import numpy as np
from collections import defaultdict
from scipy.optimize import minimize, linprog
from cerp import atlas, mechvol, train
from experiments import spike14 as S14

Z = np.hstack([train.XS, np.ones((16, 1))])


def theta(t):
    y = np.array([1.0 if (t >> x) & 1 else -1.0 for x in range(16)]); A = y[:, None] * Z
    r = linprog(np.zeros(5), A_ub=-A, b_ub=-np.ones(16), bounds=[(None, None)] * 5, method="highs")
    r = minimize(lambda th: th @ th, r.x, jac=lambda th: 2 * th, method="SLSQP",
                 constraints=[{"type": "ineq", "fun": lambda th: A @ th - 1, "jac": lambda th: A}])
    return r.x


tb, ex, els, iso = S14.setup(); T = atlas.transforms(4)
cache = {}
for env in ("A8", "G8", "A128"):
    d = json.loads((S14.RAW / f"{env}.json").read_text())
    r_stab, r_cos, r_part = [], [], []
    for e in els:
        G = S14.stab_group(e, T)
        chow = Z.T @ np.array([1.0 if (e >> x) & 1 else -1.0 for x in range(16)])
        c = d["counts"][str(e)]
        m = defaultdict(float)
        for k in set(c[0]) | set(c[1]):
            a, b = map(int, k.split("-")); v = c[0].get(k, 0) + c[1].get(k, 0)
            m[a] += v; m[b] += v
        units = sorted({t for p in iso[e] for t in p})
        if sum(m.values()) == 0: continue
        y = np.array([m[t] for t in units])
        stab = np.array([sum(S14.act(t, idx) == t for idx in G) for t in units], float)
        cs = []
        for t in units:
            if t not in cache: cache[t] = theta(t)
            th = cache[t]; cs.append(abs(th @ chow) / (np.linalg.norm(th) * np.linalg.norm(chow) + 1e-12))
        cs = np.array(cs)
        r_stab.append(mechvol._spearman(y, stab)); r_cos.append(mechvol._spearman(y, cs))
        r_part.append(mechvol._spearman(stab, cs))
    f = lambda v: round(float(np.nanmedian(v)), 2)
    print(env, "rho(unit mass, stabilizer size)", f(r_stab), "| rho(unit mass, |cos(theta, Chow)|)", f(r_cos),
          "| rho(stabilizer, cos)", f(r_part))
