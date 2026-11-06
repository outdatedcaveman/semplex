"""epsilon-sufficiency from data: the noisy counterpart of Spike 01's Layer H.

Task: predict `target` from `features` under 0-1 loss. With plug-in
(empirical) Bayes risk R(S) for feature subset S, call S
epsilon-sufficient iff R(S) <= R(all features) + epsilon. Plug-in risk is
monotone non-increasing in S (refining a partition cannot raise empirical
0-1 Bayes risk), so minimal epsilon-sufficient sets are well defined.

Used to test Spike 01's conjecture P006: "substitutable variables signal
redundant measurement channels of a shared latent quantity".
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations


def plugin_risk(counts: Counter, observables, features, target) -> float:
    ti = observables.index(target)
    fi = [observables.index(f) for f in features]
    tab = defaultdict(lambda: [0, 0])
    n = 0
    for cell, k in counts.items():
        tab[tuple(cell[i] for i in fi)][cell[ti]] += k
        n += k
    return 1 - sum(max(v) for v in tab.values()) / n


def minimal_eps_sufficient(counts, observables, features, target, eps):
    full = plugin_risk(counts, observables, features, target)
    found = []
    for k in range(len(features) + 1):
        for s in combinations(features, k):
            if any(set(f) <= set(s) for f in found):
                continue
            if plugin_risk(counts, observables, s, target) <= full + eps:
                found.append(s)
    sets = [frozenset(s) for s in found]
    nec = frozenset.intersection(*sets) if sets else frozenset()
    used = frozenset().union(*sets) if sets else frozenset()
    return {"sets": [sorted(s) for s in sets], "substitutable": sorted(used - nec),
            "risks": {",".join(s) or "∅": round(plugin_risk(counts, observables, s, target), 4)
                      for k in range(len(features) + 1) for s in combinations(features, k)}}
