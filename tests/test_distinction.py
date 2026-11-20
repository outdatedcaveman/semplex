"""Adversarial finite tests for Spike 17's distinction calculus demonstrator."""
from cerp.distinction import (exponential_contraction, factor_through, is_congruence,
    is_equivalence, linear_contraction_counterexample, preserves_through,
    run_demonstrator, tarski_satisfaction_invariant)

def test_factorization_criterion_and_tarski_unused_assignment_coordinates():
    assignments = [(x, y) for x in (False, True) for y in (False, True)]
    projection, q_x, q_y = lambda a: a[0], lambda a: a[0], lambda a: a[1]
    assert preserves_through(projection, q_x, assignments)
    assert factor_through(projection, q_x, assignments) == {False: False, True: True}
    assert not preserves_through(projection, q_y, assignments)
    assert factor_through(projection, q_y, assignments) is None

def test_tarski_satisfaction_invariance_requires_agreement_on_free_variables():
    s, s2 = {"x": 1, "y": 0}, {"x": 1, "y": 9}
    assert tarski_satisfaction_invariant(s, s2, {"x"}, lambda e: e["x"] == 1)

def test_quotient_equivalence_and_congruence_are_distinct_obligations():
    domain = (0, 1, 2, 3)
    parity = lambda x, y: x % 2 == y % 2
    assert is_equivalence(domain, parity)
    assert is_congruence(domain, parity, lambda x, y: (x + y) % 4, 2)
    assert not is_congruence(domain, parity, lambda x: 0 if x == 0 else 1, 1)

def test_linear_contraction_fails_without_duplicability_permission():
    assert not linear_contraction_counterexample(background=0, demand=2)
    assert exponential_contraction(background=0, demand=2)

def test_four_systems_demonstrator_exhibits_contextual_identity():
    result = run_demonstrator()
    assert result["classical_fol"]["tarski_assignment_invariance_for_FV_x"]
    assert result["linear_logic"]["linear_contraction_is_not_sound_for_two_token_demand"]
    assert result["dependent_type_theory"]["identity_is_a_typed_path_with_reflexivity_and_transport"]
    assert result["contextual_fibrational"]["identity_in_M1"]
    assert not result["contextual_fibrational"]["identity_in_M2"]
