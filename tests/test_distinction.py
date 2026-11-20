"""Adversarial finite tests for Spike 17's distinction-calculus examples."""
from cerp.distinction import (
    existential_import,
    factor_through,
    binary_partition_profile,
    dyadic_half_molarity_of,
    dyadic_molarity_equivalent,
    glue_module_profiles,
    restrict_module_a,
    restrict_module_b,
    is_congruence,
    is_equivalence,
    linear_contraction_counterexample,
    persistent_contraction,
    preserves_through,
    run_demonstrator,
    tarski_satisfaction_invariant,
)


def test_factorization_criterion_and_tarski_unused_assignment_coordinates():
    assignments = [(x, y) for x in (False, True) for y in (False, True)]
    projection, q_x, q_y = lambda a: a[0], lambda a: a[0], lambda a: a[1]
    assert preserves_through(projection, q_x, assignments)
    assert factor_through(projection, q_x, assignments) == {False: False, True: True}
    assert not preserves_through(projection, q_y, assignments)
    assert factor_through(projection, q_y, assignments) is None


def test_tarski_satisfaction_invariance_checks_free_variable_agreement():
    s, s2 = {"x": 1, "y": 0}, {"x": 1, "y": 9}
    assert tarski_satisfaction_invariant(s, s2, {"x"}, lambda e: e["x"] == 1)


def test_quotient_equivalence_and_congruence_are_distinct_obligations():
    domain = (0, 1, 2, 3)
    parity = lambda x, y: x % 2 == y % 2
    assert is_equivalence(domain, parity)
    assert is_congruence(domain, parity, lambda x, y: (x + y) % 4, 2)
    assert not is_congruence(domain, parity, lambda x: 0 if x == 0 else 1, 1)
    assert not is_congruence(domain, parity, lambda _x: 9, 1)


def test_linear_contraction_fails_without_duplicability_permission():
    assert not linear_contraction_counterexample(background=0, demand=2)
    assert persistent_contraction(background=0, demand=2)


def test_existential_import_depends_on_nonempty_domain_semantics():
    assert existential_import((0, 1), lambda _x: True)
    assert not existential_import((), lambda _x: True)


def test_generator_domains_are_not_accidentally_consumed():
    assert existential_import((x for x in (0, 1)), lambda _x: True)


def test_four_fragments_report_only_what_they_actually_model():
    result = run_demonstrator()
    assert result["classical_fol"]["tarski_assignment_invariance_instance"]
    assert result["linear_resource_fragment"]["linear_contraction_fails_for_two_token_demand"]
    assert result["linear_resource_fragment"]["persistent_permission_allows_reuse"]
    assert "compiled_and_axiom_audited_in_CI" in result["dependent_type_theory"]["status"]
    assert result["contextual_indexed_observations"]["identity_in_M1"]
    assert not result["contextual_indexed_observations"]["identity_in_M2"]



def test_module_overlap_gluing_is_iff_compatible_and_unique():
    local_a, local_b = (True, False), (False, False)
    global_profile = glue_module_profiles(local_a, local_b)
    assert global_profile == (True, False, False)
    assert restrict_module_a(global_profile) == local_a
    assert restrict_module_b(global_profile) == local_b
    assert glue_module_profiles((True, False), (False, True)) is None



def test_synesism_dyadic_partition_conserves_value_without_identity():
    parent = (0, 1, 0)
    children = (1, 2, 1)
    child = (1, 1, 1)
    assert dyadic_molarity_equivalent(parent, children)
    assert dyadic_half_molarity_of(child, parent)
    assert parent != children
    assert dyadic_molarity_equivalent(
        (2, 3, 4), binary_partition_profile((2, 3, 4))
    )


def test_occurrence_sensitive_linear_contraction_loses_capacity():
    from cerp.distinction import (
        ResourceMode, ResourceOccurrence, merge_linear_occurrences, resource_supports,
    )
    left = ResourceOccurrence(1, "A", ResourceMode.LINEAR, (1,))
    right = ResourceOccurrence(2, "A", ResourceMode.LINEAR, (2,))
    assert left.token != right.token
    assert resource_supports([left, right], "A", 2)
    merged = merge_linear_occurrences(left, right)
    assert merged.origins == (1, 2)
    assert not resource_supports([merged], "A", 2)


def test_persistent_contraction_preserves_support_and_provenance():
    from cerp.distinction import (
        ResourceMode, ResourceOccurrence, merge_persistent_occurrences, resource_supports,
    )
    left = ResourceOccurrence(11, "A", ResourceMode.PERSISTENT, (11,))
    right = ResourceOccurrence(12, "A", ResourceMode.PERSISTENT, (12,))
    merged = merge_persistent_occurrences(left, right)
    assert merged.origins == (11, 12)
    background = [ResourceOccurrence(13, "B", ResourceMode.LINEAR, (13,))]
    before = background + [left, right]
    after = background + [merged]
    for formula in ("A", "B", "C"):
        for demand in range(5):
            assert resource_supports(before, formula, demand) == resource_supports(
                after, formula, demand
            )
