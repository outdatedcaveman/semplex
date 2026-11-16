"""Exhaustive check: is "forced by every minimum-cost consistent function" a rational consequence relation?

Data D = a partial labelling of the 2^n inputs (a set of literals x:=v). For each D, the models are the total
functions consistent with D; the preferred models are those of least minimum-circuit cost (atlas.hi).
D |~ (x:=v)  iff  every preferred model has f(x) = v.

Checked over every D (3^(2^n) of them) and every pair of literals on unlabelled inputs:
  Cautious Monotony   D|~a and D|~b            =>  D+a |~ b
  Cut                 D|~a and D+a|~b          =>  D |~ b
  Rational Monotony   D|~b and not D|~ not-a   =>  D+a |~ b
  Monotony (expected to FAIL: the relation is nonmonotonic)  D|~b  =>  D+a |~ b
"""
import itertools, json, sys
import numpy as np
from cerp import atlas

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
K = 1 << n
tb = atlas.build_all(n)[n]
cost = np.array([int(tb.hi[f]) for f in range(1 << K)])
F = np.arange(1 << K)
VAL = ((F[:, None] >> np.arange(K)[None, :]) & 1).astype(np.int8)          # VAL[f, x]

def preferred(D):
    """D: tuple over inputs of -1 (unlabelled), 0, 1."""
    m = np.ones(len(F), bool)
    for x, v in enumerate(D):
        if v >= 0:
            m &= VAL[:, x] == v
    if not m.any():
        return None
    c = cost[m].min()
    return m & (cost == c)

def forced(D):
    pm = preferred(D)
    v = VAL[pm]
    return {x: int(v[0, x]) for x in range(K) if D[x] < 0 and (v[:, x] == v[0, x]).all()}, pm

stats = dict(D=0, CM=[0, 0], Cut=[0, 0], RM=[0, 0], Mono=[0, 0])
cache = {}
def F_(D):
    if D not in cache:
        cache[D] = forced(D)[0]
    return cache[D]

for D in itertools.product((-1, 0, 1), repeat=K):
    stats["D"] += 1
    fD = F_(D)
    free = [x for x in range(K) if D[x] < 0]
    for xa in free:
        for va in (0, 1):
            Da = tuple(va if i == xa else D[i] for i in range(K)); fDa = F_(Da)
            a_forced = fD.get(xa) == va
            nota_forced = fD.get(xa) == 1 - va
            for xb in free:
                if xb == xa:
                    continue
                for vb in (0, 1):
                    b_D = fD.get(xb) == vb; b_Da = fDa.get(xb) == vb
                    if a_forced and b_D:
                        stats["CM"][0] += 1; stats["CM"][1] += (not b_Da)
                    if a_forced and b_Da:
                        stats["Cut"][0] += 1; stats["Cut"][1] += (not b_D)
                    if b_D and not nota_forced:
                        stats["RM"][0] += 1; stats["RM"][1] += (not b_Da)
                    if b_D:
                        stats["Mono"][0] += 1; stats["Mono"][1] += (not b_Da)
out = {k: (v if k == "D" else {"instances": v[0], "violations": v[1]}) for k, v in stats.items()}
print(json.dumps(out, indent=1))
json.dump(out, open(f"experiments/results/foundations_klm_n{n}.json", "w"), indent=1)
