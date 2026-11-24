"""Exact finite benchmark for resource-bounded restricted Yoneda probes.

This is a finite-category computation, not an implementation of arbitrary
infinity-categories. It compares:
  (i) object separation by restricted representable profiles;
  (ii) full faithfulness of the restricted Yoneda functor;
  (iii) the cost frontier for probe families.

No external dependencies are required.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Callable, Iterable


@dataclass(frozen=True)
class FiniteCategory:
    objects: tuple[str, ...]
    arrows: tuple[str, ...]
    source: dict[str, str]
    target: dict[str, str]
    identity: dict[str, str]
    composition: dict[tuple[str, str], str]  # (g, f) means g after f

    def hom(self, a: str, b: str) -> tuple[str, ...]:
        return tuple(x for x in self.arrows if self.source[x] == a and self.target[x] == b)

    def compose(self, g: str, f: str) -> str:
        assert self.target[f] == self.source[g], (g, f)
        return self.composition[(g, f)]

    def validate(self) -> None:
        for x in self.objects:
            i = self.identity[x]
            assert self.source[i] == x == self.target[i]
        for f in self.arrows:
            assert self.compose(self.identity[self.target[f]], f) == f
            assert self.compose(f, self.identity[self.source[f]]) == f
        for f in self.arrows:
            for g in self.arrows:
                if self.target[f] != self.source[g]:
                    continue
                for h in self.arrows:
                    if self.target[g] == self.source[h]:
                        assert self.compose(h, self.compose(g, f)) == self.compose(self.compose(h, g), f)


def make_category(objects, arrows, source, target, identity, composition):
    c = FiniteCategory(tuple(objects), tuple(arrows), source, target, identity, composition)
    c.validate()
    return c


def walking_arrow() -> FiniteCategory:
    return make_category(
        ("0", "1"), ("i0", "i1", "u"),
        {"i0": "0", "i1": "1", "u": "0"},
        {"i0": "0", "i1": "1", "u": "1"},
        {"0": "i0", "1": "i1"},
        {("i0", "i0"): "i0", ("i1", "i1"): "i1",
         ("u", "i0"): "u", ("i1", "u"): "u"},
    )


def parallel_pair() -> FiniteCategory:
    return make_category(
        ("A", "B"), ("iA", "iB", "f", "g"),
        {"iA": "A", "iB": "B", "f": "A", "g": "A"},
        {"iA": "A", "iB": "B", "f": "B", "g": "B"},
        {"A": "iA", "B": "iB"},
        {
            ("iA", "iA"): "iA", ("iB", "iB"): "iB",
            ("f", "iA"): "f", ("g", "iA"): "g",
            ("iB", "f"): "f", ("iB", "g"): "g",
        },
    )


def discrete_pair() -> FiniteCategory:
    return make_category(
        ("A", "B"), ("iA", "iB"),
        {"iA": "A", "iB": "B"}, {"iA": "A", "iB": "B"},
        {"A": "iA", "B": "iB"},
        {("iA", "iA"): "iA", ("iB", "iB"): "iB"},
    )


def probe_arrows(c: FiniteCategory, probes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(a for a in c.arrows if c.source[a] in probes and c.target[a] in probes)


def profile(c: FiniteCategory, probes: tuple[str, ...], x: str) -> dict[str, tuple[str, ...]]:
    return {p: c.hom(p, x) for p in probes}


def restrictions(c: FiniteCategory, probes: tuple[str, ...], x: str):
    """For each u:q->p in the probe category, return precomposition Hom(p,x)->Hom(q,x)."""
    out = {}
    for u in probe_arrows(c, probes):
        q, p = c.source[u], c.target[u]
        out[u] = {f: c.compose(f, u) for f in c.hom(p, x)}
    return out


def all_functions(domain: tuple[str, ...], codomain: tuple[str, ...]):
    if not domain:
        yield {}
        return
    if not codomain:
        return
    for values in product(codomain, repeat=len(domain)):
        yield dict(zip(domain, values))


def natural_transformations(
    c: FiniteCategory, probes: tuple[str, ...], x: str, y: str
) -> tuple[dict[str, dict[str, str]], ...]:
    """Enumerate Nat(Hom(P,-)(x), Hom(P,-)(y)) exactly."""
    px, py = profile(c, probes, x), profile(c, probes, y)
    choices = [tuple(all_functions(px[p], py[p])) for p in probes]
    if any(not z for z in choices):
        return ()
    rx, ry = restrictions(c, probes, x), restrictions(c, probes, y)
    result = []
    for family in product(*choices):
        eta = dict(zip(probes, family))
        valid = True
        for u in probe_arrows(c, probes):
            q, p = c.source[u], c.target[u]
            for f in px[p]:
                left = ry[u][eta[p][f]]
                right = eta[q][rx[u][f]]
                if left != right:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            result.append(eta)
    return tuple(result)


def induced_transformation(c, probes, arrow):
    """The natural transformation induced by postcomposition with arrow X->Y."""
    x, y = c.source[arrow], c.target[arrow]
    return {
        p: {f: c.compose(arrow, f) for f in c.hom(p, x)}
        for p in probes
    }


def hom_to_nat_image(c, probes, x, y):
    image = {
        tuple((p, tuple(sorted(induced_transformation(c, probes, h)[p].items()))) for p in probes)
        for h in c.hom(x, y)
    }
    return image


def transformation_key(probes, eta):
    return tuple((p, tuple(sorted(eta[p].items()))) for p in probes)


def profile_isomorphic(c, probes, x, y) -> bool:
    """Whether the two restricted presheaves are naturally isomorphic."""
    nxy = natural_transformations(c, probes, x, y)
    nyx = natural_transformations(c, probes, y, x)
    for fwd in nxy:
        for back in nyx:
            good = True
            for p in probes:
                for a in profile(c, probes, x)[p]:
                    if back[p].get(fwd[p][a]) != a:
                        good = False
                        break
                for b in profile(c, probes, y)[p]:
                    if fwd[p].get(back[p][b]) != b:
                        good = False
                        break
            if good:
                return True
    return False


def diagnostics(c: FiniteCategory, probes: tuple[str, ...]) -> dict:
    separated_pairs = []
    unresolved_pairs = []
    for i, x in enumerate(c.objects):
        for y in c.objects[i + 1:]:
            (unresolved_pairs if profile_isomorphic(c, probes, x, y) else separated_pairs).append((x, y))

    faithfulness_defect = 0
    fullness_defect = 0
    pair_rows = []
    for x in c.objects:
        for y in c.objects:
            hom_size = len(c.hom(x, y))
            nat = natural_transformations(c, probes, x, y)
            image_size = len(hom_to_nat_image(c, probes, x, y))
            fdef = hom_size - image_size
            pdef = len(nat) - image_size
            faithfulness_defect += fdef
            fullness_defect += pdef
            pair_rows.append({
                "source": x, "target": y,
                "hom_size": hom_size, "nat_size": len(nat),
                "image_size": image_size,
                "faithfulness_defect": fdef,
                "fullness_defect": pdef,
            })
    return {
        "probes": list(probes),
        "object_separating": not unresolved_pairs,
        "separated_pairs": [list(p) for p in separated_pairs],
        "unresolved_pairs": [list(p) for p in unresolved_pairs],
        "faithfulness_defect": faithfulness_defect,
        "fullness_defect": fullness_defect,
        "fully_faithful": faithfulness_defect == 0 and fullness_defect == 0,
        "hom_vs_nat": pair_rows,
    }


def budget_frontier(c: FiniteCategory, costs: dict[str, int]) -> list[dict]:
    rows = []
    for k in range(len(c.objects) + 1):
        for subset in combinations(c.objects, k):
            cost = sum(costs[p] for p in subset)
            d = diagnostics(c, subset)
            rows.append({"cost": cost, **d})
    rows.sort(key=lambda r: (r["cost"], len(r["probes"]), r["probes"]))
    return rows


def run() -> dict:
    walk = walking_arrow()
    pp = parallel_pair()
    disc = discrete_pair()
    results = {
        "scope": "finite ordinary categories; set-valued restricted Yoneda profiles",
        "definitions": {
            "profile": "N_P(X)(p) = Hom_C(p,X), contravariant in p",
            "full_faithfulness": "canonical Hom_C(X,Y) -> Nat(N_P(X),N_P(Y)) is bijective for every X,Y",
            "object_separation": "no two distinct objects have naturally isomorphic restricted profiles",
            "defect": "separate counts of lost morphisms (faithfulness) and extra natural transformations (fullness)",
        },
        "walking_arrow": {
            "costs": {"0": 1, "1": 3},
            "frontier": budget_frontier(walk, {"0": 1, "1": 3}),
        },
        "parallel_pair": {
            "costs": {"A": 1, "B": 3},
            "frontier": budget_frontier(pp, {"A": 1, "B": 3}),
            "one_probe_A": diagnostics(pp, ("A",)),
            "all_probes": diagnostics(pp, ("A", "B")),
        },
        "discrete_pair": {
            "one_probe_A": diagnostics(disc, ("A",)),
        },
    }
    return results


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
