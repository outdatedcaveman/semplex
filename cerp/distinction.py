"""Finite reference models for Spike 17.

These are executable examples and countermodels, not substitutes for the Lean
proof development or complete implementations of the compared logics.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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



class ResourceMode(str, Enum):
    LINEAR = "linear"
    PERSISTENT = "persistent"


@dataclass(frozen=True)
class ResourceOccurrence:
    """One assumption/evidence occurrence, distinct from its proposition label."""
    token: int
    formula: Hashable
    mode: ResourceMode
    origins: tuple[int, ...]


def resource_context_well_formed(context: Sequence[ResourceOccurrence]) -> bool:
    """A linear resource occurrence token may appear only once in a context."""
    tokens = [occurrence.token for occurrence in context]
    return len(tokens) == len(set(tokens))


def resource_supports(
    context: Sequence[ResourceOccurrence], formula: Hashable, demand: int
) -> bool:
    """Persistent occurrences are reusable; linear occurrences count individually."""
    if demand < 0:
        raise ValueError("resource demand must be nonnegative")
    if not resource_context_well_formed(context):
        raise ValueError("resource context contains duplicate occurrence tokens")
    return any(
        item.formula == formula and item.mode is ResourceMode.PERSISTENT
        for item in context
    ) or sum(
        item.formula == formula and item.mode is ResourceMode.LINEAR
        for item in context
    ) >= demand


@dataclass(frozen=True)
class ResourceUse:
    """Usage of one Semplex occurrence after mapping it to one C-20 variable slot."""
    token: int
    formula: Hashable
    variable_index: int
    count: int
    origins: tuple[int, ...]


@dataclass(frozen=True)
class ResourceProfile:
    """C-20 stored-use vector re-indexed by Semplex occurrence token."""
    uses: tuple[ResourceUse, ...]

    def usage_for_formula(self, formula: Hashable) -> int:
        return sum(use.count for use in self.uses if use.formula == formula)

    @property
    def unused_tokens(self) -> tuple[int, ...]:
        return tuple(use.token for use in self.uses if use.count == 0)

    @property
    def duplicated_tokens(self) -> tuple[int, ...]:
        return tuple(use.token for use in self.uses if use.count > 1)

    @property
    def respects_linear_capacity(self) -> bool:
        """Each mapped linear occurrence is used at most once."""
        return all(0 <= use.count <= 1 for use in self.uses)

    @property
    def exactly_once(self) -> bool:
        """Every mapped linear occurrence is used exactly once (no weakening)."""
        return all(use.count == 1 for use in self.uses)


def resource_profile_from_usage(
    context: Sequence[ResourceOccurrence],
    token_to_variable: Mapping[int, int],
    formula_to_rank: Mapping[Hashable, int],
    context_ranks: Sequence[int],
    usage_vector: Sequence[int],
) -> ResourceProfile:
    """Adapt a C-20 Usage vector to Semplex tokens, for all-linear contexts only.

    C-20 Usage coordinates count stored term occurrences, one coordinate per
    variable slot. The Agda bridge serializes the snoc context newest-first
    (de Bruijn order); callers must align context_ranks and usage_vector in that
    same order, or provide the explicit token_to_variable bijection accordingly.
    This adapter preserves token identity and aggregates by formula label
    without identifying distinct occurrences. Persistent resources are
    deliberately rejected: C-20's current LCtx/Usage fragment has no
    exponential or reusable-context interpretation.
    """
    occurrences = tuple(context)
    if not resource_context_well_formed(occurrences):
        raise ValueError("resource context contains duplicate occurrence tokens")
    if any(item.mode is not ResourceMode.LINEAR for item in occurrences):
        raise ValueError("C-20 adapter currently supports all-linear contexts only")
    if len(context_ranks) != len(usage_vector):
        raise ValueError("context rank vector and usage vector must have equal length")
    if set(token_to_variable) != {item.token for item in occurrences}:
        raise ValueError("token-to-variable map must cover exactly the context tokens")
    positions = tuple(token_to_variable[item.token] for item in occurrences)
    if any(not isinstance(position, int) or isinstance(position, bool) for position in positions):
        raise ValueError("variable positions must be integers")
    if len(set(positions)) != len(positions):
        raise ValueError("distinct resource tokens must map to distinct variables")
    if set(positions) != set(range(len(usage_vector))):
        raise ValueError("token-to-variable map must biject onto the usage-vector positions")
    if any(not isinstance(rank, int) or isinstance(rank, bool) or rank < 0 for rank in context_ranks):
        raise ValueError("C-20 context ranks must be nonnegative integers")
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 0 for count in usage_vector):
        raise ValueError("usage counts must be nonnegative integers")

    uses: list[ResourceUse] = []
    for item in occurrences:
        if item.formula not in formula_to_rank:
            raise ValueError(f"missing C-20 rank for formula label {item.formula!r}")
        rank = formula_to_rank[item.formula]
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 0:
            raise ValueError("formula ranks must be nonnegative integers")
        index = token_to_variable[item.token]
        if context_ranks[index] != rank:
            raise ValueError("formula-to-rank map disagrees with the C-20 context at a token position")
        uses.append(ResourceUse(
            token=item.token,
            formula=item.formula,
            variable_index=index,
            count=usage_vector[index],
            origins=item.origins,
        ))
    return ResourceProfile(tuple(uses))


def resource_profile_fits_context(
    context: Sequence[ResourceOccurrence], profile: ResourceProfile
) -> bool:
    """Check per-token linearity and aggregate demand against an all-linear context."""
    occurrences = tuple(context)
    if not resource_context_well_formed(occurrences):
        raise ValueError("resource context contains duplicate occurrence tokens")
    if any(item.mode is not ResourceMode.LINEAR for item in occurrences):
        raise ValueError("profile/context capacity check currently supports all-linear contexts only")
    profile_tokens = [use.token for use in profile.uses]
    if len(profile_tokens) != len(set(profile_tokens)):
        raise ValueError("resource profile contains duplicate occurrence tokens")
    if set(item.token for item in occurrences) != set(profile_tokens):
        raise ValueError("profile tokens must match the context tokens exactly")
    by_token = {item.token: item for item in occurrences}
    if any(by_token[use.token].formula != use.formula for use in profile.uses):
        raise ValueError("profile formula labels must match their source occurrences")
    if any(
        not isinstance(use.count, int) or isinstance(use.count, bool) or use.count < 0
        for use in profile.uses
    ):
        raise ValueError("profile usage counts must be nonnegative integers")
    if any(
        not isinstance(use.variable_index, int) or isinstance(use.variable_index, bool)
        or use.variable_index < 0
        for use in profile.uses
    ):
        raise ValueError("profile variable indices must be nonnegative integers")
    variable_positions = {use.variable_index for use in profile.uses}
    if len(variable_positions) != len(profile.uses):
        raise ValueError("distinct resource tokens must retain distinct variable positions")
    if variable_positions != set(range(len(profile.uses))):
        raise ValueError("profile variable indices must biject onto the context positions")
    if any(by_token[use.token].origins != use.origins for use in profile.uses):
        raise ValueError("profile provenance must match its source occurrences")
    if not profile.respects_linear_capacity:
        return False
    labels = {item.formula for item in occurrences}
    return all(
        profile.usage_for_formula(label)
        <= sum(item.formula == label and item.mode is ResourceMode.LINEAR for item in occurrences)
        for label in labels
    )


def merge_persistent_occurrences(
    left: ResourceOccurrence, right: ResourceOccurrence
) -> ResourceOccurrence:
    """Contract two persistent occurrences while retaining both provenance trails."""
    if left.token == right.token:
        raise ValueError("cannot contract two references to the same occurrence token")
    if left.formula != right.formula:
        raise ValueError("only occurrences of the same formula can be contracted")
    if left.mode is not ResourceMode.PERSISTENT or right.mode is not ResourceMode.PERSISTENT:
        raise ValueError("only persistent occurrences admit this contraction")
    return ResourceOccurrence(
        token=left.token,
        formula=left.formula,
        mode=ResourceMode.PERSISTENT,
        origins=left.origins + right.origins,
    )


def merge_linear_occurrences(
    left: ResourceOccurrence, right: ResourceOccurrence
) -> ResourceOccurrence:
    """A deliberately unsafe merge, included to exhibit lost linear capacity."""
    if left.token == right.token:
        raise ValueError("cannot contract two references to the same occurrence token")
    if left.formula != right.formula:
        raise ValueError("only occurrences of the same formula can be merged")
    if left.mode is not ResourceMode.LINEAR or right.mode is not ResourceMode.LINEAR:
        raise ValueError("this counterexample requires two linear occurrences")
    return ResourceOccurrence(
        token=left.token,
        formula=left.formula,
        mode=ResourceMode.LINEAR,
        origins=left.origins + right.origins,
    )


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
            "occurrence_sensitive_persistent_contraction": (
                resource_supports(
                    [ResourceOccurrence(1, "A", ResourceMode.PERSISTENT, (1,)),
                     ResourceOccurrence(2, "A", ResourceMode.PERSISTENT, (2,))],
                    "A", 7
                )
                == resource_supports(
                    [merge_persistent_occurrences(
                        ResourceOccurrence(1, "A", ResourceMode.PERSISTENT, (1,)),
                        ResourceOccurrence(2, "A", ResourceMode.PERSISTENT, (2,))
                    )],
                    "A", 7
                )
            ),
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
