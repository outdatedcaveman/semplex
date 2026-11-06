"""Resource vectors and Pareto ranking (charter Layer I).

Costs are compared only within a shared cost model (same keys). Comparing
gate counts with DFA states requires a declared common machine model,
which F0 does not yet have -- so we report per-substrate fronts.
"""

from __future__ import annotations


def dominates(a: dict, b: dict) -> bool:
    """a <= b on every coordinate and < on at least one (lower is better)."""
    if a.keys() != b.keys():
        raise ValueError("incommensurable cost vectors: %s vs %s" % (sorted(a), sorted(b)))
    return all(a[k] <= b[k] for k in a) and any(a[k] < b[k] for k in a)


def pareto_front(items: list, key=lambda x: x["cost"]) -> list:
    return [x for x in items if not any(dominates(key(y), key(x)) for y in items if y is not x)]
