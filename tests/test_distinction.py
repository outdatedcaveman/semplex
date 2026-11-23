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
    resource_context_well_formed,
    resource_supports,
    ResourceMode,
    ResourceOccurrence,
    ResourceUse,
    ResourceProfile,
    merge_linear_occurrences,
    merge_persistent_occurrences,
    tarski_satisfaction_invariant,
    resource_profile_from_usage,
    resource_profile_fits_context,
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


def test_persistent_contraction_is_context_independent_for_multiple_demands():
    prefix = [ResourceOccurrence(20, "B", ResourceMode.LINEAR, (20,))]
    suffix = [ResourceOccurrence(21, "C", ResourceMode.LINEAR, (21,))]
    left = ResourceOccurrence(22, "A", ResourceMode.PERSISTENT, (22,))
    right = ResourceOccurrence(23, "A", ResourceMode.PERSISTENT, (23,))
    before = prefix + [left, right] + suffix
    after = prefix + [merge_persistent_occurrences(left, right)] + suffix
    for formula in ("A", "B", "C", "D"):
        for demand in range(7):
            assert resource_supports(before, formula, demand) == resource_supports(
                after, formula, demand
            )


def test_linear_contraction_loses_exactly_one_capacity_without_persistent_backup():
    contexts = [
        [],
        [ResourceOccurrence(30, "A", ResourceMode.LINEAR, (30,))],
        [ResourceOccurrence(31, "B", ResourceMode.LINEAR, (31,))],
        [ResourceOccurrence(32, "A", ResourceMode.LINEAR, (32,)),
         ResourceOccurrence(33, "C", ResourceMode.LINEAR, (33,))],
    ]
    for i, background in enumerate(contexts):
        left = ResourceOccurrence(100 + 2 * i, "A", ResourceMode.LINEAR, (100 + 2 * i,))
        right = ResourceOccurrence(101 + 2 * i, "A", ResourceMode.LINEAR, (101 + 2 * i,))
        merged = merge_linear_occurrences(left, right)
        before = background + [left, right]
        after = background + [merged]
        available_before = sum(
            item.formula == "A" and item.mode is ResourceMode.LINEAR for item in before
        )
        assert resource_supports(before, "A", available_before)
        assert not resource_supports(after, "A", available_before)


def test_duplicate_occurrence_tokens_are_rejected_as_malformed_contexts():
    occurrence = ResourceOccurrence(501, "A", ResourceMode.LINEAR, (501,))
    assert not resource_context_well_formed([occurrence, occurrence])
    try:
        resource_supports([occurrence, occurrence], "A", 2)
    except ValueError as error:
        assert "duplicate occurrence tokens" in str(error)
    else:
        raise AssertionError("duplicate token IDs must not count as two linear resources")


def test_contraction_rejects_two_references_to_the_same_occurrence_token():
    occurrence = ResourceOccurrence(502, "A", ResourceMode.PERSISTENT, (502,))
    for merge in (merge_persistent_occurrences, merge_linear_occurrences):
        try:
            merge(occurrence, occurrence)
        except ValueError as error:
            assert "same occurrence token" in str(error)
        else:
            raise AssertionError("a single occurrence token cannot be contracted with itself")


def test_c20_usage_adapter_preserves_token_identity_and_aggregates_formula_labels():
    context = [
        ResourceOccurrence(601, "A", ResourceMode.LINEAR, (601,)),
        ResourceOccurrence(602, "A", ResourceMode.LINEAR, (602,)),
        ResourceOccurrence(603, "B", ResourceMode.LINEAR, (603,)),
    ]
    profile = resource_profile_from_usage(
        context,
        token_to_variable={601: 0, 602: 1, 603: 2},
        formula_to_rank={"A": 1, "B": 2},
        context_ranks=(1, 1, 2),
        usage_vector=(1, 1, 1),
    )
    assert [(use.token, use.variable_index, use.count) for use in profile.uses] == [
        (601, 0, 1), (602, 1, 1), (603, 2, 1)
    ]
    assert profile.usage_for_formula("A") == 2
    assert profile.usage_for_formula("B") == 1
    assert profile.exactly_once
    assert profile.respects_linear_capacity
    assert resource_profile_fits_context(context, profile)


def test_c20_usage_adapter_is_natural_under_simultaneous_context_permutation():
    context = [
        ResourceOccurrence(601, "A", ResourceMode.LINEAR, (601,)),
        ResourceOccurrence(602, "A", ResourceMode.LINEAR, (602,)),
        ResourceOccurrence(603, "B", ResourceMode.LINEAR, (603,)),
    ]
    original = resource_profile_from_usage(
        context,
        token_to_variable={601: 0, 602: 1, 603: 2},
        formula_to_rank={"A": 1, "B": 2},
        context_ranks=(1, 1, 2),
        usage_vector=(1, 0, 1),
    )

    permuted_context = [context[2], context[0], context[1]]
    permuted = resource_profile_from_usage(
        permuted_context,
        token_to_variable={603: 0, 601: 1, 602: 2},
        formula_to_rank={"A": 1, "B": 2},
        context_ranks=(2, 1, 1),
        usage_vector=(1, 1, 0),
    )

    def by_token(profile):
        return {
            use.token: (use.formula, use.variable_index, use.count, use.origins)
            for use in profile.uses
        }

    original_by_token = by_token(original)
    permuted_by_token = by_token(permuted)
    assert {token: item[1] for token, item in original_by_token.items()} == {
        601: 0, 602: 1, 603: 2
    }
    assert {token: item[1] for token, item in permuted_by_token.items()} == {
        603: 0, 601: 1, 602: 2
    }
    assert {
        token: (formula, count, origins)
        for token, (formula, _index, count, origins) in original_by_token.items()
    } == {
        token: (formula, count, origins)
        for token, (formula, _index, count, origins) in permuted_by_token.items()
    }
    assert original.usage_for_formula("A") == permuted.usage_for_formula("A") == 1
    assert original.usage_for_formula("B") == permuted.usage_for_formula("B") == 1
    assert resource_profile_fits_context(context, original)
    assert resource_profile_fits_context(permuted_context, permuted)


def test_c20_usage_adapter_distinguishes_weakening_from_duplication():
    context = [
        ResourceOccurrence(611, "A", ResourceMode.LINEAR, (611,)),
        ResourceOccurrence(612, "A", ResourceMode.LINEAR, (612,)),
        ResourceOccurrence(613, "B", ResourceMode.LINEAR, (613,)),
    ]
    mapping = {611: 0, 612: 1, 613: 2}
    ranks = {"A": 1, "B": 2}
    weakened = resource_profile_from_usage(context, mapping, ranks, (1, 1, 2), (1, 0, 1))
    assert weakened.unused_tokens == (612,)
    assert weakened.duplicated_tokens == ()
    assert not weakened.exactly_once
    assert weakened.respects_linear_capacity
    assert resource_profile_fits_context(context, weakened)

    duplicated = resource_profile_from_usage(context, mapping, ranks, (1, 1, 2), (2, 0, 1))
    assert duplicated.duplicated_tokens == (611,)
    assert duplicated.unused_tokens == (612,)
    assert not duplicated.respects_linear_capacity
    # Aggregate A-demand still equals aggregate A-capacity; token-level accounting
    # correctly catches the duplication hidden by that aggregate.
    assert duplicated.usage_for_formula("A") == 2
    assert not resource_profile_fits_context(context, duplicated)


def test_c20_usage_adapter_rejects_noninjective_or_incomplete_token_maps():
    context = [
        ResourceOccurrence(621, "A", ResourceMode.LINEAR, (621,)),
        ResourceOccurrence(622, "B", ResourceMode.LINEAR, (622,)),
    ]
    args = (context, {"A": 1, "B": 2}, (1, 2), (1, 1))
    try:
        resource_profile_from_usage(context, {621: 0, 622: 0}, *args[1:])
    except ValueError as error:
        assert "distinct variables" in str(error)
    else:
        raise AssertionError("two resource tokens cannot map to one C-20 variable")
    try:
        resource_profile_from_usage(context, {621: 0}, *args[1:])
    except ValueError as error:
        assert "cover exactly" in str(error)
    else:
        raise AssertionError("the adapter must map every resource token")


def test_c20_usage_adapter_rejects_rank_mismatch_and_persistent_contexts():
    linear = [ResourceOccurrence(631, "A", ResourceMode.LINEAR, (631,))]
    try:
        resource_profile_from_usage(linear, {631: 0}, {"A": 1}, (2,), (1,))
    except ValueError as error:
        assert "disagrees" in str(error)
    else:
        raise AssertionError("the formula-to-rank map must match the C-20 context")

    persistent = [ResourceOccurrence(632, "A", ResourceMode.PERSISTENT, (632,))]
    try:
        resource_profile_from_usage(persistent, {632: 0}, {"A": 1}, (1,), (2,))
    except ValueError as error:
        assert "all-linear" in str(error)
    else:
        raise AssertionError("persistent resources need a separate C-20 interpretation")


def test_resource_profile_fits_context_rejects_noncanonical_positions_and_forged_provenance():
    context = [
        ResourceOccurrence(651, "A", ResourceMode.LINEAR, (651,)),
        ResourceOccurrence(652, "B", ResourceMode.LINEAR, (652,)),
    ]
    noncontiguous = ResourceProfile((
        ResourceUse(651, "A", 0, 1, (651,)),
        ResourceUse(652, "B", 2, 1, (652,)),
    ))
    try:
        resource_profile_fits_context(context, noncontiguous)
    except ValueError as error:
        assert "biject" in str(error)
    else:
        raise AssertionError("profile variable indices must cover every C-20 position")

    forged_provenance = ResourceProfile((
        ResourceUse(651, "A", 0, 1, (999,)),
        ResourceUse(652, "B", 1, 1, (652,)),
    ))
    try:
        resource_profile_fits_context(context, forged_provenance)
    except ValueError as error:
        assert "provenance" in str(error)
    else:
        raise AssertionError("the adapter must not accept forged provenance trails")


def test_c20_usage_adapter_rejects_negative_usage_counts():
    context = [ResourceOccurrence(641, "A", ResourceMode.LINEAR, (641,))]
    invalid_profile = ResourceProfile((ResourceUse(641, "A", 0, -1, (641,)),))
    assert not invalid_profile.respects_linear_capacity
    try:
        resource_profile_from_usage(context, {641: 0}, {"A": 1}, (1,), (-1,))
    except ValueError as error:
        assert "nonnegative integers" in str(error)
    else:
        raise AssertionError("usage vectors are natural-number valued")
