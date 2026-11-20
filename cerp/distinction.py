"""Finite reference models for Spike 17.

These are executable examples and countermodels, not substitutes for the Lean
proof development or complete implementations of the compared logics.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Hashable, Iterable, Mapping, Sequence, TypeVar

X = TypeVar("X", bound=Hashable)
Y = TypeVar("Y", bound=Hashable)
A = TypeVar("A", bound=Hashable)


def preserves_through(
    transform: Callable[[X], Y], observable: Callable[[X], A], domain: Iterable[X]
) -> bool:
    """Whether observable factors through transform on a finite domain."""
    xs = tuple(domain)
    return all(
        observable(x) == observable(y)
        for x in xs
        for y in xs
        if transform(x) == transform(y)
    )


def factor_through(
    transform: Callable[[X], Y], observable: Callable[[X], A], domain: Iterable[X]
) -> dict[Y, A] | None:
    """Construct the induced observable on the image, or return None."""
    induced: dict[Y, A] = {}
    for x in domain:
        key, value = transform(x), observable(x)
        if key in induced and induced[key] != value:
            return None
        induced[key] = value
    return induced


def is_equivalence(
    domain: Sequence[X], relation: Callable[[X, X], bool]
) -> bool:
    return (
        all(relation(x, x) for x in domain)
        and all(relation(x, y) == relation(y, x) for x in domain for y in domain)
        and all(
            not (relation(x, y) and relation(y, z)) or relation(x, z)
            for x in domain for y in domain for z in domain
        )
    )


def is_congruence(
    domain: Sequence[X],
    relation: Callable[[X, X], bool],
    operation: Callable[..., X],
    arity: int,
) -> bool:
    """Check closure and congruence for an n-ary operation on a finite carrier."""
    tuples = list(product(domain, repeat=arity))
    outputs = [operation(*args) for args in tuples]
    if any(output not in domain for output in outputs):
        return False
    for left in tuples:
        for right in tuples:
            if all(relation(a, b) for a, b in zip(left, right)):
                if not relation(operation(*left), operation(*right)):
                    return False
    return True


def resource_entails(
    linear_available: int, required: int, *, persistent: bool = False
) -> bool:
    """A tiny resource semantics: linear tokens count; persistent permission is reusable."""
    if linear_available < 0 or required < 0:
        raise ValueError("resource counts must be nonnegative")
    return persistent or required <= linear_available


def linear_contraction_counterexample(background: int = 0, demand: int = 2) -> bool:
    """Whether merging two linear occurrences preserves this resource entailment."""
    before = resource_entails(background + 2, demand)
    after = resource_entails(background + 1, demand)
    return (not before) or after


def persistent_contraction(background: int = 0, demand: int = 2) -> bool:
    """Whether one persistent occurrence can support repeated use after contraction."""
    return resource_entails(background + 1, demand, persistent=True)


@dataclass(frozen=True)
class Module:
    """A module is a declared family of observables."""
    name: str
    observables: tuple[Callable[[X], Hashable], ...]

    def indistinguishable(self, x: X, y: X) -> bool:
        return all(obs(x) == obs(y) for obs in self.observables)


@dataclass(frozen=True)
class ContextualIdentity:
    left: X
    right: X
    module: str
    holds: bool


def contextual_identity(x: X, y: X, module: Module) -> ContextualIdentity:
    return ContextualIdentity(x, y, module.name, module.indistinguishable(x, y))


def tarski_assignment_equivalence(
    assignment: Mapping[str, Hashable],
    other: Mapping[str, Hashable],
    free_variables: Iterable[str],
) -> bool:
    """The assignment relation relevant to one formula's free variables."""
    return all(assignment[v] == other[v] for v in free_variables)


def tarski_satisfaction_invariant(
    assignment: Mapping[str, Hashable],
    other: Mapping[str, Hashable],
    free_variables: Iterable[str],
    satisfaction: Callable[[Mapping[str, Hashable]], A],
) -> bool:
    """Check one satisfaction instance after verifying agreement on FV(phi)."""
    if not tarski_assignment_equivalence(assignment, other, free_variables):
        raise ValueError("assignments do not agree on the formula's free variables")
    return satisfaction(assignment) == satisfaction(other)


def forall(domain: Iterable[X], predicate: Callable[[X], bool]) -> bool:
    """Finite first-order universal quantifier; vacuously true on an empty domain."""
    return all(predicate(x) for x in domain)


def exists(domain: Iterable[X], predicate: Callable[[X], bool]) -> bool:
    """Finite first-order existential quantifier; false on an empty domain."""
    return any(predicate(x) for x in domain)


def existential_import(domain: Iterable[X], predicate: Callable[[X], bool]) -> bool:
    """Truth of (forall x P(x)) -> (exists x P(x)) in a finite model."""
    xs = tuple(domain)
    return (not forall(xs, predicate)) or exists(xs, predicate)



def restrict_module_a(global_profile: tuple[bool, bool, bool]) -> tuple[bool, bool]:
    """Module A observes the first and overlap coordinates."""
    x, _y, z = global_profile
    return x, z


def restrict_module_b(global_profile: tuple[bool, bool, bool]) -> tuple[bool, bool]:
    """Module B observes the second and overlap coordinates."""
    _x, y, z = global_profile
    return y, z


def glue_module_profiles(
    module_a: tuple[bool, bool], module_b: tuple[bool, bool]
) -> tuple[bool, bool, bool] | None:
    """Glue local profiles iff their overlap coordinate agrees."""
    x, z_a = module_a
    y, z_b = module_b
    if z_a != z_b:
        return None
    return x, y, z_a



def dyadic_molarity_equivalent(
    left: tuple[int, int, int], right: tuple[int, int, int]
) -> bool:
    """Compare count / 2**order by cross multiplication; signature is structural."""
    left_order, left_count, _left_signature = left
    right_order, right_count, _right_signature = right
    return left_count * (2 ** right_order) == right_count * (2 ** left_order)


def dyadic_half_molarity_of(
    child: tuple[int, int, int], parent: tuple[int, int, int]
) -> bool:
    """Check whether child molarity is exactly half the parent's."""
    child_order, child_count, _ = child
    parent_order, parent_count, _ = parent
    return 2 * child_count * (2 ** parent_order) == parent_count * (2 ** child_order)


def binary_partition_profile(
    profile: tuple[int, int, int]
) -> tuple[int, int, int]:
    """Toy binary partition: order + 1, count doubled, new structural signature."""
    order, count, signature = profile
    return order + 1, 2 * count, signature + 1


def run_demonstrator() -> dict[str, object]:
    """Return finite examples; the DTT and fibration proofs live in Lean, not here."""
    assignments = [(x, y) for x in (False, True) for y in (False, True)]
    project_x = lambda a: a[0]
    formula_x = lambda a: a[0]
    formula_y = lambda a: a[1]
    parity = lambda x, y: x % 2 == y % 2
    add_mod4 = lambda x, y: (x + y) % 4
    noncongruent_unary = lambda x: 0 if x == 0 else 1
    finite = (0, 1, 2, 3)
    s, s_prime = {"x": 1, "y": 0}, {"x": 1, "y": 1}
    tarski = tarski_satisfaction_invariant(
        s, s_prime, {"x"}, lambda env: env["x"] == 1
    )
    m1 = Module("M1", (lambda z: z[0],))
    m2 = Module("M2", (lambda z: z[0], lambda z: z[1]))
    pair_a, pair_b = (0, 0), (0, 1)
    return {
        "classical_fol": {
            "tarski_assignment_invariance_instance": tarski,
            "quotient_by_unused_variable_preserves_phi_x": preserves_through(
                project_x, formula_x, assignments
            ),
            "same_quotient_does_not_preserve_phi_y": not preserves_through(
                project_x, formula_y, assignments
            ),
            "existential_import_nonempty_domain": existential_import(
                (0, 1), lambda _x: True
            ),
            "existential_import_empty_domain_fails": not existential_import(
                (), lambda _x: True
            ),
        },
        "linear_resource_fragment": {
            "linear_contraction_fails_for_two_token_demand": not linear_contraction_counterexample(),
            "persistent_permission_allows_reuse": persistent_contraction(),
        },
        "dependent_type_theory": {
            "status": "formal_fragment_in_Lean_source; compiled_and_axiom_audited_in_CI"
        },
        "contextual_indexed_observations": {
            "identity_in_M1": contextual_identity(pair_a, pair_b, m1).holds,
            "identity_in_M2": contextual_identity(pair_a, pair_b, m2).holds,
        },
        "synesism_dyadic_partition": {
            "parent_and_two_offspring_same_molarity": dyadic_molarity_equivalent((0, 1, 0), (1, 2, 1)),
            "each_child_half_parent_molarity": dyadic_half_molarity_of((1, 1, 1), (0, 1, 0)),
            "parent_and_offspring_configuration_differ": (0, 1, 0) != (1, 2, 1),
            "binary_partition_preserves_value": dyadic_molarity_equivalent((2, 3, 4), binary_partition_profile((2, 3, 4))),
        },
        "module_descent": {
            "compatible_profiles_glue_uniquely": glue_module_profiles((True, False), (False, False)) == (True, False, False),
            "incompatible_profiles_do_not_glue": glue_module_profiles((True, False), (False, True)) is None,
        },
        "quotient_theory": {
            "parity_is_equivalence": is_equivalence(finite, parity),
            "addition_mod_4_descends_to_parity_quotient": is_congruence(
                finite, parity, add_mod4, 2
            ),
            "chosen_unary_operation_fails_congruence": not is_congruence(
                finite, parity, noncongruent_unary, 1
            ),
        },
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_demonstrator(), indent=2, sort_keys=True))
