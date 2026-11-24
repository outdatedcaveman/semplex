"""Resource-relative executable probe presheaves.

A wide free subcategory F indexes admissible, zero-cost refinements.
Cost-bounded arrows into a target form an F-sieve under subadditive costs,
even when they are not sieves in the full category C.
"""
from __future__ import annotations


class ResourceProbeCategory:
    objects = ("R", "Q", "P", "X", "Y")
    arrows = (
        "iR", "iQ", "iP", "iX", "iY",
        "v", "u", "w", "g", "h", "k", "t", "tg", "th", "tk",
    )
    source = {
        "iR": "R", "iQ": "Q", "iP": "P", "iX": "X", "iY": "Y",
        "v": "R", "u": "Q", "w": "R", "g": "P", "h": "Q", "k": "R",
        "t": "X", "tg": "P", "th": "Q", "tk": "R",
    }
    target = {
        "iR": "R", "iQ": "Q", "iP": "P", "iX": "X", "iY": "Y",
        "v": "Q", "u": "P", "w": "P", "g": "X", "h": "X", "k": "X",
        "t": "Y", "tg": "Y", "th": "Y", "tk": "Y",
    }
    composition = {
        ("iR", "iR"): "iR", ("iQ", "iQ"): "iQ",
        ("iP", "iP"): "iP", ("iX", "iX"): "iX", ("iY", "iY"): "iY",
        ("iQ", "v"): "v", ("v", "iR"): "v",
        ("u", "iQ"): "u", ("iP", "u"): "u",
        ("iP", "w"): "w", ("w", "iR"): "w",
        ("iX", "g"): "g", ("g", "iP"): "g",
        ("iX", "h"): "h", ("h", "iQ"): "h",
        ("iX", "k"): "k", ("k", "iR"): "k",
        ("iY", "t"): "t", ("t", "iX"): "t",
        ("iY", "tg"): "tg", ("tg", "iP"): "tg",
        ("iY", "th"): "th", ("th", "iQ"): "th",
        ("iY", "tk"): "tk", ("tk", "iR"): "tk",
        ("u", "v"): "w",
        ("g", "u"): "h",
        ("h", "v"): "k",
        ("g", "w"): "k",
        ("t", "g"): "tg",
        ("t", "h"): "th",
        ("t", "k"): "tk",
        ("tg", "u"): "th",
        ("tg", "w"): "tk",
        ("th", "v"): "tk",
    }
    costs = {
        "iR": 0, "iQ": 0, "iP": 0, "iX": 0, "iY": 0,
        "v": 2, "u": 0, "w": 2, "g": 1, "h": 1, "k": 3,
        "t": 2, "tg": 3, "th": 3, "tk": 5,
    }
    free = {"iR", "iQ", "iP", "iX", "iY", "u"}

    def compose(self, after: str, before: str) -> str:
        assert self.target[before] == self.source[after], (after, before)
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
        for after in self.arrows:
            for before in self.arrows:
                if self.target[before] == self.source[after]:
                    composite = self.compose(after, before)
                    assert self.costs[composite] <= self.costs[after] + self.costs[before]
        for a in self.free:
            for b in self.free:
                if self.target[b] == self.source[a]:
                    assert self.compose(a, b) in self.free

    def identity(self, obj: str) -> str:
        return {"R": "iR", "Q": "iQ", "P": "iP", "X": "iX", "Y": "iY"}[obj]


def arrows_into(c: ResourceProbeCategory, target: str):
    return tuple(a for a in c.arrows if c.target[a] == target)


def affordable(c: ResourceProbeCategory, target: str, budget: int):
    return {a for a in arrows_into(c, target) if c.costs[a] <= budget}


def is_relative_sieve(c: ResourceProbeCategory, target: str, family: set[str]):
    for f in family:
        if c.target[f] != target:
            return False
        for u in c.free:
            if c.target[u] == c.source[f] and c.compose(f, u) not in family:
                return False
    return True


def is_full_sieve(c: ResourceProbeCategory, target: str, family: set[str]):
    for f in family:
        if c.target[f] != target:
            return False
        for u in c.arrows:
            if c.target[u] == c.source[f] and c.compose(f, u) not in family:
                return False
    return True


def grade_shift(c: ResourceProbeCategory, arrow: str, source_family: set[str], target_budget: int):
    """Postcompose affordable probes with arrow and verify shifted affordability."""
    out = {}
    for f in source_family:
        composite = c.compose(arrow, f)
        assert c.costs[composite] <= c.costs[arrow] + c.costs[f]
        assert c.costs[composite] <= target_budget
        out[f] = composite
    return out


def run():
    c = ResourceProbeCategory()
    c.validate()
    rows = []
    for budget in (0, 1, 2, 3, 5):
        family = affordable(c, "X", budget)
        rows.append({
            "budget": budget,
            "arrows": sorted(family),
            "free_refinement_sieve": is_relative_sieve(c, "X", family),
            "full_category_sieve": is_full_sieve(c, "X", family),
        })
    source = affordable(c, "X", 1)
    shifted = grade_shift(c, "t", source, 3)
    return {
        "objects": list(c.objects),
        "free_arrows": sorted(c.free),
        "costs": c.costs,
        "composites": {"g∘u": "h", "u∘v": "w", "h∘v": "k", "g∘w": "k"},
        "budget_frontier": rows,
        "grade_shift": {
            "target_arrow": "t:X→Y",
            "target_arrow_cost": c.costs["t"],
            "source_budget": 1,
            "target_budget": 3,
            "induced_map": shifted,
            "naturality_relative_to_free_refinements": all(
                is_relative_sieve(c, "Y", affordable(c, "Y", 3)) for _ in (0,)
            ),
        },
        "interpretation": "budgeted probe families are sieves relative to zero-cost refinements, not necessarily relative to all paid transformations",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
