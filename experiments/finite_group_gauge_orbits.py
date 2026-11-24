"""Generic finite-group gauge-ring orbit and observation-rank theorems.

The functions operate on an explicitly supplied finite group. The S3 and D4
instances are small exact witnesses for the general formulas.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from itertools import permutations, product
import json
from pathlib import Path
from typing import Callable, Generic, TypeVar

E = TypeVar("E")


@dataclass(frozen=True)
class FiniteGroup(Generic[E]):
    elements: tuple[E, ...]
    identity: E
    multiply: Callable[[E, E], E]
    inverse: Callable[[E], E]


def conjugacy_class(group: FiniteGroup[E], x: E) -> frozenset[E]:
    return frozenset(
        group.multiply(group.multiply(g, x), group.inverse(g))
        for g in group.elements
    )


def holonomy(group: FiniteGroup[E], connection: tuple[E, E, E]) -> E:
    return group.multiply(
        connection[2],
        group.multiply(connection[1], connection[0]),
    )


def gauge_transform(
    group: FiniteGroup[E],
    connection: tuple[E, E, E],
    gauge: tuple[E, E, E],
) -> tuple[E, E, E]:
    return tuple(
        group.multiply(
            group.multiply(gauge[(i + 1) % 3], connection[i]),
            group.inverse(gauge[i]),
        )
        for i in range(3)
    )  # type: ignore[return-value]


def holonomy_is_gauge_covariant(group: FiniteGroup[E]) -> bool:
    for connection in product(group.elements, repeat=3):
        for gauge in product(group.elements, repeat=3):
            transformed = gauge_transform(group, connection, gauge)
            expected = group.multiply(
                group.multiply(gauge[0], holonomy(group, connection)),
                group.inverse(gauge[0]),
            )
            if holonomy(group, transformed) != expected:
                return False
    return True


def gauge_ring_orbits(group: FiniteGroup[E]) -> dict:
    configurations = set(product(group.elements, repeat=3))
    gauges = tuple(product(group.elements, repeat=3))
    unseen = set(configurations)
    orbits = []
    while unseen:
        representative = min(unseen, key=repr)
        orbit = {
            gauge_transform(group, representative, gauge)
            for gauge in gauges
        }
        if not orbit <= unseen:
            raise AssertionError("gauge transformations failed to partition configurations")
        unseen.difference_update(orbit)
        sector = conjugacy_class(group, holonomy(group, representative))
        expected_size = len(group.elements) ** 2 * len(sector)
        if len(orbit) != expected_size:
            raise AssertionError("orbit size disagrees with centralizer-stabilizer formula")
        orbits.append({
            "conjugacy_class_size": len(sector),
            "orbit_size": len(orbit),
        })
    orbits.sort(key=lambda row: (row["conjugacy_class_size"], row["orbit_size"]))
    return {
        "group_order": len(group.elements),
        "connection_count": len(configurations),
        "gauge_transformation_count": len(gauges),
        "conjugacy_class_count": len(orbits),
        "orbits": orbits,
        "orbit_size_formula": "|G|^2 * |[H]|",
    }


def s3_group() -> FiniteGroup[tuple[int, int, int]]:
    elements = tuple(permutations(range(3)))
    identity = (0, 1, 2)

    def multiply(p, q):
        return tuple(p[q[i]] for i in range(3))

    def inverse(p):
        return tuple(p.index(i) for i in range(3))

    return FiniteGroup(elements, identity, multiply, inverse)


def d4_group() -> FiniteGroup[tuple[int, int]]:
    # Elements r^k s^e with r^4=s^2=e and srs=r^{-1}.
    elements = tuple((k, e) for k in range(4) for e in range(2))
    identity = (0, 0)

    def multiply(a, b):
        return ((a[0] + (-1 if a[1] else 1) * b[0]) % 4, (a[1] + b[1]) % 2)

    def inverse(a):
        if a[1] == 0:
            return ((-a[0]) % 4, 0)
        return (a[0], 1)

    return FiniteGroup(elements, identity, multiply, inverse)


def conjugacy_classes(group: FiniteGroup[E]) -> tuple[frozenset[E], ...]:
    unseen = set(group.elements)
    classes = []
    while unseen:
        representative = min(unseen, key=repr)
        sector = conjugacy_class(group, representative)
        classes.append(sector)
        unseen.difference_update(sector)
    return tuple(sorted(classes, key=lambda c: (len(c), repr(sorted(c, key=repr)))))


def lift_class_kernel(group: FiniteGroup[E], transition):
    """Lift a Markov kernel on conjugacy classes uniformly to group elements."""
    classes = conjugacy_classes(group)
    if len(transition) != len(classes) or any(len(row) != len(classes) for row in transition):
        raise ValueError("class transition matrix has the wrong dimension")
    if any(F(x) < 0 for row in transition for x in row) or any(
        sum((F(x) for x in row), F(0)) != 1 for row in transition
    ):
        raise ValueError("class transition matrix must be row-stochastic")
    class_of = {g: i for i, sector in enumerate(classes) for g in sector}
    return [
        [
            F(transition[class_of[g]][class_of[gp]]) / len(classes[class_of[gp]])
            for gp in group.elements
        ]
        for g in group.elements
    ]


def identity_group_kernel(group: FiniteGroup[E]):
    index = {g: i for i, g in enumerate(group.elements)}
    return [
        [F(1) if i == j else F(0) for j in range(len(group.elements))]
        for i in range(len(group.elements))
    ]


def group_kernel_is_conjugation_equivariant(group: FiniteGroup[E], kernel) -> bool:
    index = {g: i for i, g in enumerate(group.elements)}
    for g in group.elements:
        for gp in group.elements:
            for k in group.elements:
                kgk = group.multiply(group.multiply(k, g), group.inverse(k))
                kgpk = group.multiply(group.multiply(k, gp), group.inverse(k))
                if kernel[index[g]][index[gp]] != kernel[index[kgk]][index[kgpk]]:
                    return False
    return True


def group_kernel_is_lumpable_over_classes(group: FiniteGroup[E], kernel) -> bool:
    classes = conjugacy_classes(group)
    index = {g: i for i, g in enumerate(group.elements)}
    for source_class in classes:
        representatives = list(source_class)
        reference = representatives[0]
        reference_sums = [
            sum((kernel[index[reference]][index[target]] for target in target_class), F(0))
            for target_class in classes
        ]
        for source in representatives[1:]:
            sums = [
                sum((kernel[index[source]][index[target]] for target in target_class), F(0))
                for target_class in classes
            ]
            if sums != reference_sums:
                return False
    return True


def lifted_kernel_is_stochastic(group: FiniteGroup[E], lifted) -> bool:
    return all(sum(row, F(0)) == 1 for row in lifted)


def lifted_kernel_is_conjugation_equivariant(group: FiniteGroup[E], lifted) -> bool:
    index = {g: i for i, g in enumerate(group.elements)}
    for g in group.elements:
        for gp in group.elements:
            for k in group.elements:
                kgk = group.multiply(group.multiply(k, g), group.inverse(k))
                kgpk = group.multiply(group.multiply(k, gp), group.inverse(k))
                if lifted[index[g]][index[gp]] != lifted[index[kgk]][index[kgpk]]:
                    return False
    return True


def determinant(matrix) -> F:
    n = len(matrix)
    if n == 0 or any(len(row) != n for row in matrix):
        raise ValueError("determinant requires a nonempty square matrix")
    if n == 1:
        return F(matrix[0][0])
    total = F(0)
    for j in range(n):
        minor = [list(row[:j]) + list(row[j + 1:]) for row in matrix[1:]]
        total += (-1 if j % 2 else 1) * F(matrix[0][j]) * determinant(minor)
    return total


def symmetric_observation_channel(n: int, eta: F) -> tuple[tuple[F, ...], ...]:
    if n < 2 or eta < 0 or eta > F(1, n - 1):
        raise ValueError("require n >= 2 and 0 <= eta <= 1/(n-1)")
    return tuple(
        tuple(F(1) - (n - 1) * eta if i == j else eta for j in range(n))
        for i in range(n)
    )


def symmetric_channel_determinant(n: int, eta: F) -> F:
    if n < 2 or eta < 0 or eta > F(1, n - 1):
        raise ValueError("require n >= 2 and 0 <= eta <= 1/(n-1)")
    return (F(1) - n * eta) ** (n - 1)


def probe_separates_beliefs(n: int, eta: F, transition_determinant: F) -> bool:
    """One-step map b -> b P K_eta is injective iff both factors are invertible.

    This is not a criterion for observability by a multi-step controlled test family;
    that general question is determined by the rank of the full future operator O_B.
    """
    return transition_determinant != 0 and symmetric_channel_determinant(n, eta) != 0


def group_axioms_hold(group: FiniteGroup[E]) -> bool:
    xs = group.elements
    for x in xs:
        if group.multiply(group.identity, x) != x or group.multiply(x, group.identity) != x:
            return False
        if group.multiply(x, group.inverse(x)) != group.identity:
            return False
        for y in xs:
            for z in xs:
                if group.multiply(group.multiply(x, y), z) != group.multiply(x, group.multiply(y, z)):
                    return False
    return True


def analyze() -> dict:
    groups = {"S3": s3_group(), "D4": d4_group()}
    group_results = {}
    for name, group in groups.items():
        classes = conjugacy_classes(group)
        group_results[name] = {
            "group_axioms": group_axioms_hold(group),
            "holonomy_gauge_covariant": holonomy_is_gauge_covariant(group),
            "conjugacy_class_sizes": sorted(len(c) for c in classes),
            "gauge_ring_orbits": gauge_ring_orbits(group),
        }

    d4 = groups["D4"]
    n = len(conjugacy_classes(d4))
    class_transition = tuple(
        tuple(F(3, 4) if i == j else F(1, 4) if j == (i + 1) % n else F(0)
              for j in range(n))
        for i in range(n)
    )
    lifted = lift_class_kernel(d4, class_transition)
    identity_kernel = identity_group_kernel(d4)
    channels = {}
    for size, eta in ((3, F(1, 6)), (5, F(1, 10)), (5, F(1, 5)), (5, F(1, 4))):
        channel = symmetric_observation_channel(size, eta)
        channels[f"n={size},eta={eta}"] = {
            "determinant": str(determinant(channel)),
            "formula": str(symmetric_channel_determinant(size, eta)),
            "separates_if_probe_transition_invertible": probe_separates_beliefs(size, eta, F(1)),
        }
    return {
        "generic_gauge_orbit_law": "For a connected three-cycle, gauge orbits of G^3 are classified by conjugacy classes of the ordered holonomy; orbit size = |G|^2 * |[H]|.",
        "groups": group_results,
        "D4_class_markov_lift": {
            "transition": [[str(x) for x in row] for row in class_transition],
            "row_stochastic": lifted_kernel_is_stochastic(d4, lifted),
            "conjugation_equivariant": lifted_kernel_is_conjugation_equivariant(d4, lifted),
            "lumpable_over_classes": group_kernel_is_lumpable_over_classes(d4, lifted),
        },
        "nonunique_group_level_lift": {
            "identity_kernel_is_conjugation_equivariant": group_kernel_is_conjugation_equivariant(d4, identity_kernel),
            "identity_kernel_is_lumpable_over_classes": group_kernel_is_lumpable_over_classes(d4, identity_kernel),
            "uniform_lift_is_lumpable_over_classes": group_kernel_is_lumpable_over_classes(d4, lifted),
            "identity_kernel_differs_from_uniform_lift": identity_kernel != lifted,
            "interpretation": "The uniform class lift erases within-class group-element state; identity is another equivariant and class-lumpable lift that preserves it.",
        },
        "symmetric_channel_generalization": {
            "matrix": "K_n(eta) = eta * 11^T + (1 - n*eta) * I",
            "determinant": "det K_n(eta) = (1 - n*eta)^(n-1)",
            "examples": channels,
        },
    }


if __name__ == "__main__":
    result = analyze()
    artifact = Path(__file__).resolve().parents[1] / "artifacts" / "finite-group-gauge-orbits-20261122.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps(result, indent=2) + chr(10), encoding="utf-8")
    print(json.dumps({
        "artifact": str(artifact),
        "groups": {
            name: {
                "conjugacy_class_sizes": row["conjugacy_class_sizes"],
                "orbit_sizes": [x["orbit_size"] for x in row["gauge_ring_orbits"]["orbits"]],
            }
            for name, row in result["groups"].items()
        },
        "D4_class_markov_lift": result["D4_class_markov_lift"],
        "symmetric_channel_generalization": result["symmetric_channel_generalization"],
    }, indent=2))
