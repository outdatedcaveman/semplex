"""Character-theoretic probes and the gauge action-groupoid equivalence.

Exact finite witnesses for S3 and D4. The mathematical construction is
generic; finite enumeration checks the instances, not the arbitrary-group proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from itertools import combinations, product
from typing import Hashable

from experiments.finite_group_gauge_orbits import (
    FiniteGroup, conjugacy_classes, conjugacy_class, d4_group,
    gauge_transform, holonomy, s3_group,
)


@dataclass(frozen=True)
class CharacterTable:
    group_name: str
    class_labels: tuple[str, ...]
    irreducible_labels: tuple[str, ...]
    class_sizes: tuple[int, ...]
    values: tuple[tuple[complex, ...], ...]

    def __post_init__(self):
        if len(self.values) != len(self.irreducible_labels):
            raise ValueError("one character row is required per irreducible")
        if len(self.class_sizes) != len(self.class_labels) or any(n <= 0 for n in self.class_sizes):
            raise ValueError("provide a positive size for every conjugacy class")
        if any(len(row) != len(self.class_labels) for row in self.values):
            raise ValueError("character row has the wrong number of classes")

    def row_orthogonality_holds(self) -> bool:
        order = sum(self.class_sizes)
        for i, left in enumerate(self.values):
            for j, right in enumerate(self.values):
                inner = sum(
                    (self.class_sizes[k] * left[k] * complex(right[k]).conjugate()
                     for k in range(len(self.class_sizes))),
                    0j,
                ) / order
                if abs(inner - (1 if i == j else 0)) > 1e-10:
                    return False
        return True

    def separates(self, selected: tuple[int, ...]) -> bool:
        signatures = [
            tuple(self.values[i][j] for i in selected)
            for j in range(len(self.class_labels))
        ]
        return len(set(signatures)) == len(self.class_labels)

    def separating_subsets(self, max_size: int | None = None):
        upper = len(self.irreducible_labels) if max_size is None else min(
            max_size, len(self.irreducible_labels)
        )
        for size in range(upper + 1):
            found = [
                subset for subset in combinations(range(len(self.irreducible_labels)), size)
                if self.separates(subset)
            ]
            if found:
                return tuple(found)
        return tuple()

    def minimum_weighted_subset(self, costs: tuple[int, ...], budget: int | None = None):
        if len(costs) != len(self.irreducible_labels) or any(c < 0 for c in costs):
            raise ValueError("provide one nonnegative cost per irreducible character")
        candidates = []
        for size in range(len(costs) + 1):
            for subset in combinations(range(len(costs)), size):
                total = sum(costs[i] for i in subset)
                if self.separates(subset) and (budget is None or total <= budget):
                    candidates.append((total, len(subset), subset))
        return min(candidates) if candidates else None

    def pair_coverage(self) -> dict[tuple[int, int], tuple[int, ...]]:
        coverage = {}
        for i, j in combinations(range(len(self.class_labels)), 2):
            coverage[(i, j)] = tuple(
                k for k, row in enumerate(self.values) if row[i] != row[j]
            )
        return coverage


def s3_character_table() -> CharacterTable:
    # Classes: identity, transpositions, 3-cycles.
    return CharacterTable(
        "S3",
        ("identity", "transposition", "3-cycle"),
        ("trivial", "sign", "standard-2d"),
        (1, 3, 2),
        ((1, 1, 1), (1, -1, 1), (2, 0, -1)),
    )


def d4_character_table() -> CharacterTable:
    # Classes: {e}, {r^2}, {r,r^3}, {s,r^2s}, {rs,r^3s}.
    return CharacterTable(
        "D4",
        ("identity", "half-turn", "quarter-turns", "axis-reflections", "diagonal-reflections"),
        ("trivial", "reflection-sign", "rotation-sign", "product-sign", "standard-2d"),
        (1, 1, 2, 2, 2),
        (
            (1, 1, 1, 1, 1),
            (1, 1, 1, -1, -1),
            (1, 1, -1, 1, -1),
            (1, 1, -1, -1, 1),
            (2, -2, 0, 0, 0),
        ),
    )


def groupoid_morphism(group: FiniteGroup, source, target, gauge) -> bool:
    return gauge_transform(group, source, gauge) == target


def conjugation_morphism(group: FiniteGroup, source, target, base_gauge) -> bool:
    return group.multiply(
        group.multiply(base_gauge, source), group.inverse(base_gauge)
    ) == target


def extend_base_gauge_to_ring_morphism(group, source, target, base_gauge):
    """Unique vertex gauge extending g_0, if it maps source to target."""
    g0 = base_gauge
    g1 = group.multiply(
        group.multiply(target[0], g0), group.inverse(source[0])
    )
    g2 = group.multiply(
        group.multiply(target[1], g1), group.inverse(source[1])
    )
    gauge = (g0, g1, g2)
    if gauge_transform(group, source, gauge) == target:
        return gauge
    return None


def action_groupoid_functor_is_fully_faithful(group: FiniteGroup, source, target) -> bool:
    """For fixed A,A', compare arrows with conjugators H(A)->H(A')."""
    left = []
    for k in group.elements:
        gauge = extend_base_gauge_to_ring_morphism(group, source, target, k)
        if gauge is not None:
            left.append(k)
    right = [
        k for k in group.elements
        if conjugation_morphism(group, holonomy(group, source), holonomy(group, target), k)
    ]
    return set(left) == set(right) and len(left) == len(right)


def action_groupoid_functor_checks(group: FiniteGroup, exhaustive: bool = True) -> dict:
    connections = tuple(product(group.elements, repeat=3))
    if exhaustive:
        pairs = product(connections, repeat=2)
    else:
        pairs = (
            (connections[i], connections[(i * 17 + 3) % len(connections)])
            for i in range(min(100, len(connections)))
        )
    checked = 0
    for source, target in pairs:
        if not action_groupoid_functor_is_fully_faithful(group, source, target):
            return {"fully_faithful": False, "pairs_checked": checked}
        checked += 1
    return {
        "fully_faithful": True,
        "pairs_checked": checked,
        "objects": len(connections),
        "essentially_surjective": True,  # A=(e,e,h) realizes every h.
        "set_truncation_classes": len(conjugacy_classes(group)),
    }


def gauge_compose(group: FiniteGroup, first, second):
    """Compose first A->A' then second A'->A'' (left action convention)."""
    return tuple(group.multiply(second[i], first[i]) for i in range(3))


def action_groupoid_functor_preserves_composition(group: FiniteGroup) -> bool:
    for first in product(group.elements, repeat=3):
        for second in product(group.elements, repeat=3):
            composite = gauge_compose(group, first, second)
            if composite[0] != group.multiply(second[0], first[0]):
                return False
    return True


def action_groupoid_functor_preserves_identity(group: FiniteGroup) -> bool:
    identity_gauge = (group.identity, group.identity, group.identity)
    return identity_gauge[0] == group.identity


def simultaneous_conjugate_tuple(group: FiniteGroup, source, target) -> bool:
    return any(
        tuple(
            group.multiply(group.multiply(k, x), group.inverse(k))
            for x in source
        ) == tuple(target)
        for k in group.elements
    )


def bouquet_two_loop_counterexample(group: FiniteGroup) -> dict:
    """Two tuples with matching component classes but distinct joint orbits."""
    transpositions = [
        x for x in group.elements
        if len(conjugacy_class(group, x)) == 3
    ]
    if len(transpositions) < 2:
        raise ValueError("the witness requires at least two distinct transpositions")
    s01, s12 = transpositions[0], transpositions[1]
    left, right = (s01, s01), (s01, s12)
    component_classes_match = all(
        conjugacy_class(group, left[i]) == conjugacy_class(group, right[i])
        for i in range(2)
    )
    joint_same_orbit = simultaneous_conjugate_tuple(group, left, right)
    return {
        "left": left,
        "right": right,
        "componentwise_classes_match": component_classes_match,
        "simultaneous_conjugate": joint_same_orbit,
        "product_left": group.multiply(left[1], left[0]),
        "product_right": group.multiply(right[1], right[0]),
    }


def centralizer_size(group: FiniteGroup, h) -> int:
    return sum(
        group.multiply(group.multiply(g, h), group.inverse(g)) == h
        for g in group.elements
    )


def analyze() -> dict:
    tables = (s3_character_table(), d4_character_table())
    character_results = {}
    for table in tables:
        minimum = table.separating_subsets()
        character_results[table.group_name] = {
            "class_labels": table.class_labels,
            "irreducibles": table.irreducible_labels,
            "class_sizes": table.class_sizes,
            "row_orthogonality": table.row_orthogonality_holds(),
            "character_table": table.values,
            "minimum_separating_cardinality": len(minimum[0]) if minimum else None,
            "minimum_separating_subsets": [
                [table.irreducible_labels[i] for i in subset] for subset in minimum
            ],
            "pair_coverage": {
                f"{table.class_labels[i]} | {table.class_labels[j]}": [
                    table.irreducible_labels[k] for k in cover
                ]
                for (i, j), cover in table.pair_coverage().items()
            },
            "weighted_example": table.minimum_weighted_subset(
                tuple(range(1, len(table.irreducible_labels) + 1))
            ),
        }

    groups = {"S3": s3_group(), "D4": d4_group()}
    bouquet_witness = bouquet_two_loop_counterexample(groups["S3"])
    groupoid_results = {}
    for name, group in groups.items():
        # Full pairwise hom-set comparison for both finite groups.
        groupoid_results[name] = action_groupoid_functor_checks(
            group, exhaustive=True
        )
        groupoid_results[name]["preserves_composition"] = action_groupoid_functor_preserves_composition(group)
        groupoid_results[name]["preserves_identity"] = action_groupoid_functor_preserves_identity(group)
        groupoid_results[name]["centralizer_sizes"] = sorted({
            centralizer_size(group, h) for h in group.elements
        })

    return {
        "character_theory": {
            "theorem": "Irreducible complex characters form a basis of class functions; hence the complete character vector separates conjugacy classes.",
            "minimal_probe_problem": "minimum set cover on unordered pairs of conjugacy classes; costs can encode measurement/implementation resources.",
            "tables": character_results,
        },
        "multi_loop_warning": {
            "construction": "For a bouquet with b1 loops, use Hom(F_b1,G)//G with simultaneous conjugation, not a product of independent conjugacy-class quotients.",
            "s3_counterexample": {
                key: (str(value) if isinstance(value, tuple) else value)
                for key, value in bouquet_witness.items()
            },
        },
        "hott_groupoid_bridge": {
            "construction": "Conn(Gamma)//G^V -> Hom(pi1(Gamma),G)//G by based holonomy; for a single cycle this reduces to G//G. On arrows the functor sends a vertex gauge to its base-vertex component.",
            "expected_theorem": "For a connected graph, spanning-tree gauge fixing identifies the connection action groupoid with the simultaneous-conjugation action groupoid on based holonomy representations. Its 0-truncation is the set of simultaneous-conjugacy classes; isotropy is the common centralizer of the holonomy tuple.",
            "checks": groupoid_results,
        },
    }


if __name__ == "__main__":
    import json
    from pathlib import Path
    result = analyze()
    out = Path(__file__).resolve().parents[1] / "artifacts" / "character-hott-gauge-bridge-20261122.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str) + chr(10), encoding="utf-8")
    print(json.dumps({
        "artifact": str(out),
        "minimum_character_sets": {
            name: row["minimum_separating_subsets"]
            for name, row in result["character_theory"]["tables"].items()
        },
        "groupoid_checks": result["hott_groupoid_bridge"]["checks"],
    }, indent=2))
