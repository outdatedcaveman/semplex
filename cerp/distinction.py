"""Finite reference model for controlled distinction loss (Spike 17).

This module is deliberately a finite demonstrator, not a replacement for the
proof-assistant development. It makes the semantic side conditions executable
and provides adversarial counterexamples for the four comparison fragments.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Hashable, Iterable, Mapping, Sequence, TypeVar
X = TypeVar("X", bound=Hashable)
Y = TypeVar("Y", bound=Hashable)
A = TypeVar("A", bound=Hashable)

def preserves_through(transform: Callable[[X], Y], observable: Callable[[X], A], domain: Iterable[X]) -> bool:
    """Whether observable factors through transform on a finite domain."""
    xs = tuple(domain)
    return all(observable(x) == observable(y) for x in xs for y in xs if transform(x) == transform(y))

def factor_through(transform: Callable[[X], Y], observable: Callable[[X], A], domain: Iterable[X]) -> dict[Y, A] | None:
    """Construct the induced observable on the image, or return None."""
    induced: dict[Y, A] = {}
    for x in domain:
        key, value = transform(x), observable(x)
        if key in induced and induced[key] != value:
            return None
        induced[key] = value
    return induced

def is_equivalence(domain: Sequence[X], relation: Callable[[X, X], bool]) -> bool:
    return (all(relation(x, x) for x in domain)
        and all(relation(x, y) == relation(y, x) for x in domain for y in domain)
        and all(not (relation(x, y) and relation(y, z)) or relation(x, z) for x in domain for y in domain for z in domain))

def is_congruence(domain: Sequence[X], relation: Callable[[X, X], bool], operation: Callable[..., X], arity: int) -> bool:
    """Finite congruence test for an n-ary operation."""
    import itertools
    tuples = list(itertools.product(domain, repeat=arity))
    for left in tuples:
        for right in tuples:
            if all(relation(a, b) for a, b in zip(left, right)):
                if not relation(operation(*left), operation(*right)):
                    return False
    return True

def resource_entails(available: int, required: int) -> bool:
    """Tiny resource semantics: a context supplies at least its demand."""
    return available >= required

def linear_contraction_counterexample(background: int = 0, demand: int = 2) -> bool:
    """True iff contraction preserves this particular entailment."""
    premise = resource_entails(background + 2, demand)
    conclusion = resource_entails(background + 1, demand)
    return (not premise) or conclusion

def exponential_contraction(background: int = 0, demand: int = 2) -> bool:
    """An unrestricted token can be copied arbitrarily often in this model."""
    return resource_entails(background + demand, demand)

@dataclass(frozen=True)
class Module:
    """A module is a declared family of observables, not a subjective whim."""
    name: str
    observables: tuple[Callable[[X], Hashable], ...]
    def indistinguishable(self, x: X, y: X) -> bool:
        return all(obs(x) == obs(y) for obs in self.observables)

@dataclass(frozen=True)
class ContextualIdentity:
    """Identity is indexed by a module/context and its protected interface."""
    left: X
    right: X
    module: str
    holds: bool

def contextual_identity(x: X, y: X, module: Module) -> ContextualIdentity:
    return ContextualIdentity(x, y, module.name, module.indistinguishable(x, y))

def tarski_assignment_equivalence(assignment: Mapping[str, Hashable], other: Mapping[str, Hashable], free_variables: Iterable[str]) -> bool:
    """The assignment relation relevant to one formula's free variables."""
    return all(assignment[v] == other[v] for v in free_variables)

def tarski_satisfaction_invariant(assignment: Mapping[str, Hashable], other: Mapping[str, Hashable], free_variables: Iterable[str], satisfaction: Callable[[Mapping[str, Hashable]], A]) -> bool:
    """Finite instance of satisfaction depending only on FV(phi)."""
    if not tarski_assignment_equivalence(assignment, other, free_variables):
        raise ValueError("assignments do not agree on the formula's free variables")
    return satisfaction(assignment) == satisfaction(other)

def run_demonstrator() -> dict[str, object]:
    """Return deterministic results for the four comparison fragments."""
    assignments = [(x, y) for x in (False, True) for y in (False, True)]
    project_x = lambda a: a[0]
    formula_x = lambda a: a[0]
    formula_y = lambda a: a[1]
    parity = lambda x, y: x % 2 == y % 2
    add_mod4 = lambda x, y: (x + y) % 4
    noncongruent_unary = lambda x: 0 if x == 0 else 1
    finite = (0, 1, 2, 3)
    s, s_prime = {"x": 1, "y": 0}, {"x": 1, "y": 1}
    tarski = tarski_satisfaction_invariant(s, s_prime, {"x"}, lambda env: env["x"] == 1)
    m1 = Module("M1", (lambda z: z[0],))
    m2 = Module("M2", (lambda z: z[0], lambda z: z[1]))
    pair_a, pair_b = (0, 0), (0, 1)
    return {
        "classical_fol": {
            "tarski_assignment_invariance_for_FV_x": tarski,
            "quotient_by_unused_variable_preserves_phi_x": preserves_through(project_x, formula_x, assignments),
            "same_quotient_does_not_preserve_phi_y": not preserves_through(project_x, formula_y, assignments)},
        "linear_logic": {
            "linear_contraction_is_not_sound_for_two_token_demand": not linear_contraction_counterexample(),
            "unrestricted_exponential_token_is_duplicable": exponential_contraction()},
        "dependent_type_theory": {
            "identity_is_a_typed_path_with_reflexivity_and_transport": True,
            "note": "Lean Eq is the proof-assistant identity type; this records the formal fragment to be checked in Distinction.lean, not a Python proof."},
        "contextual_fibrational": {
            "identity_in_M1": contextual_identity(pair_a, pair_b, m1).holds,
            "identity_in_M2": contextual_identity(pair_a, pair_b, m2).holds,
            "identity_is_context_indexed": True},
        "quotient_theory": {
            "parity_is_equivalence": is_equivalence(finite, parity),
            "addition_mod_4_descends_to_parity_quotient": is_congruence(finite, parity, add_mod4, 2),
            "chosen_unary_operation_fails_congruence": not is_congruence(finite, parity, noncongruent_unary, 1)}}

if __name__ == "__main__":
    import json
    print(json.dumps(run_demonstrator(), indent=2, sort_keys=True))
