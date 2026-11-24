"""Finite test of executable-arrow sieves and resource-budget truncation."""
from __future__ import annotations


class ChainProbeCategory:
    objects = ("Q", "P", "X")
    arrows = ("iQ", "iP", "iX", "u", "g", "h")
    source = {"iQ": "Q", "iP": "P", "iX": "X", "u": "Q", "g": "P", "h": "Q"}
    target = {"iQ": "Q", "iP": "P", "iX": "X", "u": "P", "g": "X", "h": "X"}
    composition = {
        ("iQ", "iQ"): "iQ", ("iP", "iP"): "iP", ("iX", "iX"): "iX",
        ("u", "iQ"): "u", ("iP", "u"): "u",
        ("g", "iP"): "g", ("iX", "g"): "g",
        ("h", "iQ"): "h", ("iX", "h"): "h",
        ("g", "u"): "h",
    }

    def compose(self, after: str, before: str) -> str:
        assert self.target[before] == self.source[after]
        return self.composition[(after, before)]

    def validate(self):
        for f in self.arrows:
            assert self.compose(self.identity(self.target[f]), f) == f
            assert self.compose(f, self.identity(self.source[f])) == f
        for f in self.arrows:
            for g in self.arrows:
                if self.target[f] != self.source[g]:
                    continue
                for h in self.arrows:
                    if self.target[g] == self.source[h]:
                        assert self.compose(h, self.compose(g, f)) == self.compose(self.compose(h, g), f)

    def identity(self, obj: str) -> str:
        return {"Q": "iQ", "P": "iP", "X": "iX"}[obj]


def arrows_into(c: ChainProbeCategory, target: str):
    return tuple(a for a in c.arrows if c.target[a] == target)


def raw_budget_family(c: ChainProbeCategory, target: str, costs: dict[str, int], budget: int):
    return {a for a in arrows_into(c, target) if a in costs and costs[a] <= budget}


def sieve_closure(c: ChainProbeCategory, target: str, family: set[str]):
    """Smallest sieve containing family: all precomposites by arrows into each source."""
    closure = set(family)
    changed = True
    while changed:
        changed = False
        for f in tuple(closure):
            src = c.source[f]
            for u in c.arrows:
                if c.target[u] == src:
                    composite = c.compose(f, u)
                    if composite not in closure:
                        closure.add(composite)
                        changed = True
    assert all(c.target[a] == target for a in closure)
    return closure


def is_sieve(c: ChainProbeCategory, target: str, family: set[str]) -> bool:
    for f in family:
        if c.target[f] != target:
            return False
        for u in c.arrows:
            if c.target[u] == c.source[f] and c.compose(f, u) not in family:
                return False
    return True


def closure_cost(family: set[str], costs: dict[str, int]) -> int:
    if not family:
        return 0
    missing = family - costs.keys()
    if missing:
        raise ValueError(f"missing implementation costs for arrows: {sorted(missing)}")
    return max(costs[a] for a in family)


def run():
    c = ChainProbeCategory()
    c.validate()
    costs = {"g": 1, "h": 3}
    rows = []
    for budget in range(4):
        raw = raw_budget_family(c, "X", costs, budget)
        closed = sieve_closure(c, "X", raw)
        rows.append({
            "budget": budget,
            "raw_executable_arrows": sorted(raw),
            "raw_is_sieve": is_sieve(c, "X", raw),
            "sieve_closure": sorted(closed),
            "closure_is_sieve": is_sieve(c, "X", closed),
            "closure_cost": closure_cost(closed, costs),
            "closure_fits_budget": closure_cost(closed, costs) <= budget,
        })
    return {
        "category": "Q --u--> P --g--> X, with h = g∘u : Q-->X",
        "arrow_costs": costs,
        "interpretation": "budget sublevels of arrow costs need not be sieves; sieve closure may introduce over-budget arrows",
        "rows": rows,
        "key_implication": "A resource-bounded family of physically executable arrows is not automatically a subpresheaf of a representable. Refinement closure must be physically justified or explicitly costed.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
