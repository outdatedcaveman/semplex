from fractions import Fraction
from experiments.finite_holonomy_pomdp import (
    HolonomyPOMDP, all_connections, channel_determinant,
    exhaustive_gauge_audit, exhaustive_resource_audit, holonomy,
)

def test_z3_wilson_loop_is_gauge_invariant_and_classifies_orbits():
    assert exhaustive_gauge_audit() == {
        "connections": 27, "gauge_transformations": 27,
        "distinct_gauge_orbits": 3, "each_orbit_size": 9,
        "holonomy_gauge_invariant": True,
        "orbits_exactly_holonomy_classes": True,
    }

def test_local_responses_do_not_reveal_global_holonomy():
    model = HolonomyPOMDP()
    assert all(model.local_response(holonomy(a)) == 0 for a in all_connections())
    priors = [(Fraction(1), Fraction(0), Fraction(0)),
              (Fraction(0), Fraction(1), Fraction(0)),
              (Fraction(0), Fraction(0), Fraction(1))]
    for budget in (0, 1, 2):
        assert len({model.profile(p, budget) for p in priors}) == 1

def test_first_global_probe_splits_the_semantic_quotient_at_cost_three():
    model = HolonomyPOMDP()
    priors = [(Fraction(1), Fraction(0), Fraction(0)),
              (Fraction(0), Fraction(1), Fraction(0)),
              (Fraction(0), Fraction(0), Fraction(1))]
    assert len({model.profile(p, 2) for p in priors}) == 1
    assert len({model.profile(p, 3) for p in priors}) == 3

def test_noisy_channel_identifiability_has_exact_rank_threshold():
    assert channel_determinant(Fraction(0)) == 1
    assert channel_determinant(Fraction(1, 6)) == Fraction(1, 4)
    assert channel_determinant(Fraction(1, 3)) == 0
    model = HolonomyPOMDP(Fraction(1, 6))
    beliefs = [(Fraction(1), Fraction(0), Fraction(0)),
               (Fraction(0), Fraction(1), Fraction(0)),
               (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))]
    assert len({model.profile(b, 3) for b in beliefs}) == len(beliefs)

def test_uniform_noise_makes_all_beliefs_predictively_equivalent():
    model = HolonomyPOMDP(Fraction(1, 3))
    beliefs = [(Fraction(1), Fraction(0), Fraction(0)),
               (Fraction(0), Fraction(1), Fraction(0)),
               (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))]
    assert len({model.profile(b, 6) for b in beliefs}) == 1

def test_bayes_update_is_exact_and_predictively_sufficient():
    model = HolonomyPOMDP(Fraction(1, 6))
    prior = (Fraction(1, 2), Fraction(1, 3), Fraction(1, 6))
    posterior = model.posterior(prior, observation=1)
    assert sum(posterior) == 1
    assert posterior == (Fraction(1, 4), Fraction(2, 3), Fraction(1, 12))
    assert model.response_distribution(posterior) == tuple(
        model.sequence_distribution(prior, (1, y)) /
        model.sequence_distribution(prior, (1,)) for y in range(3)
    )

def test_repeated_observations_are_correlated_through_static_hidden_state():
    model = HolonomyPOMDP(Fraction(1, 6))
    prior = (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))
    joint = model.sequence_distribution(prior, (0, 0))
    marginal = model.sequence_distribution(prior, (0,))
    assert joint != marginal * marginal

def test_exhaustive_resource_audit():
    audit = exhaustive_resource_audit()
    assert audit["budgets_below_3_collapse_all_beliefs"]
    assert audit["budget_3_exact_loop_separates_beliefs"]
    assert audit["uniform_noise_erases_all_information"]


def test_primitive_control_walks_have_gauge_invariant_closed_responses():
    from itertools import product
    from experiments.finite_holonomy_pomdp import (
        execute_walk, winding_number, gauge_transform,
    )
    for a in all_connections():
        for g in all_connections():
            transformed = gauge_transform(a, g)
            for n in range(1, 7):
                for actions in product((-1, 1), repeat=n):
                    if sum(actions) % 3:
                        continue
                    vertex, phase = execute_walk(a, actions)
                    other_vertex, other_phase = execute_walk(transformed, actions)
                    assert vertex == other_vertex == 0
                    assert phase == other_phase
                    assert phase == (winding_number(actions) * holonomy(a)) % 3


def test_primitive_controls_require_three_steps_for_nontrivial_holonomy():
    from experiments.finite_holonomy_pomdp import closed_walks
    assert closed_walks(1) == ()
    assert set(closed_walks(2)) == {(-1, 1), (1, -1)}
    assert set(closed_walks(3)) == {(-1, 1), (1, -1), (-1, -1, -1), (1, 1, 1)}


def test_belief_is_a_sufficient_statistic_of_observation_history():
    model = HolonomyPOMDP(Fraction(1, 6))
    prior = (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))
    # The hidden sector is static, so order does not matter once counts agree.
    posterior_a = model.posterior_sequence(prior, (0, 1))
    posterior_b = model.posterior_sequence(prior, (1, 0))
    assert posterior_a == posterior_b
    # Histories with the same posterior have identical affordable responses.
    assert model.profile(posterior_a, 6) == model.profile(posterior_b, 6)
    # Different posterior states are separated by the affordable Wilson loop.
    other = model.posterior_sequence(prior, (0, 0))
    assert posterior_a != other
    assert model.profile(posterior_a, 3) != model.profile(other, 3)


def test_posterior_history_future_hankel_factorization_and_balanced_identity():
    from experiments.finite_holonomy_pomdp import posterior_hankel_diagnostics
    d = posterior_hankel_diagnostics(Fraction(1, 6))
    lam = Fraction(1, 2)
    p = tuple(tuple((Fraction(1) if i == j else Fraction(0)) - Fraction(1, 3)
                    for j in range(3)) for i in range(3))
    assert d["R"] == d["O"]
    assert d["H"] == tuple(
        tuple(sum(d["R"][i][k] * d["O"][k][j] for k in range(3))
              for j in range(3)) for i in range(3)
    )
    assert d["centered_H"] == tuple(
        tuple(lam**2 * p[i][j] for j in range(3)) for i in range(3)
    )
    assert d["Wc"] == d["Wo"]
    assert d["balanced_gram"] == tuple(
        tuple(lam**4 * p[i][j] for j in range(3)) for i in range(3)
    )


def test_hankel_rank_collapses_exactly_at_uniform_noise():
    from experiments.finite_holonomy_pomdp import posterior_hankel_diagnostics
    informative = posterior_hankel_diagnostics(Fraction(1, 6))
    erased = posterior_hankel_diagnostics(Fraction(1, 3))
    assert any(any(x != 0 for x in row) for row in informative["centered_H"])
    assert all(all(x == 0 for x in row) for row in erased["centered_H"])
