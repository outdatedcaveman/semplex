from fractions import Fraction as F
from itertools import product

from experiments import nonabelian_causal_realization as m


def test_s3_has_three_expected_conjugacy_classes():
    assert [len(c) for c in m.CLASS_SETS] == [1, 3, 2]
    assert len(set(m.CLASS_SETS)) == 3
    assert len(m.GROUP) == 6


def test_nonabelian_holonomy_is_gauge_covariant():
    for connection in product(m.GROUP, repeat=3):
        for gauge in product(m.GROUP, repeat=3):
            transformed = m.gauge_transform(connection, gauge)
            expected = m.compose(
                m.compose(gauge[0], m.holonomy(connection)),
                m.inverse(gauge[0]),
            )
            assert m.holonomy(transformed) == expected


def test_connection_gauge_orbits_are_exactly_conjugacy_classes():
    result = m.orbit_partition()
    assert result["connection_count"] == 216
    assert result["gauge_transformation_count"] == 216
    assert result["orbit_count"] == 3
    assert result["orbit_sizes_by_class"] == {
        "identity": 36,
        "transposition": 108,
        "3-cycle": 72,
    }
    assert sum(r["size"] for r in result["orbits"]) == 216


def test_local_edge_conjugacy_multiset_loses_order_sensitive_holonomy():
    witness = m.find_local_order_collision()
    assert witness["same_local_conjugacy_multiset"]
    assert witness["first_holonomy_class"] != witness["second_holonomy_class"]
    assert "not gauge-invariant" in witness["warning"]
    baseline = m.representation_baseline_summary()
    assert baseline["ordered_group_holonomy_states"] == 6
    assert baseline["gauge_invariant_holonomy_classes"] == 3
    assert baseline["frame_redundancy_factor"] == 2


def test_controlled_class_dynamics_are_noncommuting_invertible_kernels():
    for transition in m.TRANSITIONS.values():
        assert all(sum(row, F(0)) == 1 for row in transition)
        assert m.det3(transition) != 0
    assert m.det3(m.P_WAIT) == F(3, 8)
    assert m.det3(m.P_PROBE) == F(1, 4)
    assert m.matmul(m.P_WAIT, m.P_PROBE) != m.matmul(m.P_PROBE, m.P_WAIT)


def test_group_level_markov_lift_is_conjugation_equivariant_and_stochastic():
    assert m.check_group_lift_equivariance()
    assert m.check_group_lift_row_stochastic()


def test_hankel_factorization_is_exact_below_probe_budget():
    result = m.hankel_factorization(2, F(1, 6))
    assert result["history_count"] == 13
    assert result["test_count"] == 13
    assert result["factorization_exact"]
    assert result["rank_O"] == 1
    assert result["rank_H"] == 1
    assert not result["full_abstraction_on_simplex"]
    # Every affordable future response is independent of the current hidden class.
    assert all(len(set(col)) == 1 for col in zip(*result["O"]))


def test_probe_budget_makes_posterior_fully_abstract_at_nonuniform_noise():
    result = m.hankel_factorization(3, F(1, 6))
    assert result["history_count"] == 43
    assert result["test_count"] == 43
    assert result["factorization_exact"]
    assert (result["rank_R"], result["rank_O"], result["rank_H"]) == (3, 3, 3)
    assert result["full_abstraction_on_simplex"]


def test_weighted_past_future_gramians_recover_hankel_rank():
    informative = m.hankel_factorization(3, F(1, 6))
    below_threshold = m.hankel_factorization(2, F(1, 6))
    assert (informative["rank_Wc"], informative["rank_Wo"], informative["rank_WcWo"]) == (3, 3, 3)
    assert informative["rank_WcWo"] == informative["rank_H"]
    assert (below_threshold["rank_Wc"], below_threshold["rank_Wo"], below_threshold["rank_WcWo"]) == (2, 1, 1)
    assert below_threshold["rank_WcWo"] == below_threshold["rank_H"]


def test_uniform_observation_channel_destroys_full_abstraction_at_every_budget():
    for budget in (0, 1, 2, 3, 4):
        result = m.hankel_factorization(budget, F(1, 3))
        assert result["factorization_exact"]
        assert result["rank_O"] == 1
        assert result["rank_H"] == 1
        assert not result["full_abstraction_on_simplex"]


def test_exact_noise_threshold_matches_the_determinant_theorem():
    for eta in (F(0), F(1, 6), F(1, 4), F(1, 3), F(1, 2)):
        channel = [
            [F(1) - 2 * eta if i == j else eta for j in range(3)]
            for i in range(3)
        ]
        result = m.hankel_factorization(3, eta)
        expected_rank = 1 if eta == F(1, 3) else 3
        assert m.det3(channel) == (1 - 3 * eta) ** 2
        assert result["rank_O"] == expected_rank
        assert result["full_abstraction_on_simplex"] == (eta != F(1, 3))


def test_hankel_rows_are_exact_future_response_profiles_of_posteriors():
    result = m.hankel_factorization(3, F(1, 6))
    for i, posterior in enumerate(result["R"]):
        for j, likelihood in enumerate(zip(*result["O"])):
            expected = sum((posterior[k] * likelihood[k] for k in range(3)), F(0))
            assert result["H"][i][j] == expected


def test_dynamic_belief_state_is_a_sufficient_predictive_state():
    eta = F(1, 6)
    histories = m.history_rows(3, eta)
    tests = m.future_columns(3, eta)
    prior = [F(1, 3)] * 3
    for history in histories:
        belief = history["posterior"]
        alpha = list(prior)
        for action, outcome in zip(history["actions"], history["observations"]):
            alpha = m.row_mul(alpha, m.joint_matrix(action, outcome, eta))
        history_mass = sum(alpha, F(0))
        for test in tests:
            predicted = sum(
                (belief[i] * test["likelihood"][i] for i in range(3)),
                F(0),
            )
            direct = list(alpha)
            for action, outcome in zip(test["actions"], test["observations"]):
                direct = m.row_mul(direct, m.joint_matrix(action, outcome, eta))
            direct_probability = sum(direct, F(0)) / history_mass
            assert predicted == direct_probability
            assert F(0) <= predicted <= F(1)
    assert len(histories) == 43
    assert len(tests) == 43


def test_budget_two_posterior_rank_is_prior_drift_not_observation_learning():
    uniform = m.hankel_factorization(2, F(1, 6))
    stationary_prior = m.stationary_wait_prior()
    assert m.row_mul(stationary_prior, m.P_WAIT) == stationary_prior
    stationary = m.hankel_factorization(2, F(1, 6), prior=stationary_prior)
    assert uniform["rank_R"] == 2
    assert stationary["rank_R"] == 1
    assert stationary["rank_O"] == 1
    assert stationary["rank_H"] == 1


def test_centered_gram_sum_is_not_the_centered_hankel_operator():
    b2 = m.centered_diagnostics(m.hankel_factorization(2, F(1, 6)))
    b3 = m.centered_diagnostics(m.hankel_factorization(3, F(1, 6)))
    b3_uniform = m.centered_diagnostics(m.hankel_factorization(3, F(1, 3)))
    assert (b2["rank_centered_H"], b3["rank_centered_H"], b3_uniform["rank_centered_H"]) == (0, 2, 0)
    assert (b2["rank_centered_Wc_plus_Wo"], b3["rank_centered_Wc_plus_Wo"], b3_uniform["rank_centered_Wc_plus_Wo"]) == (1, 2, 2)
    assert all(x["centered_H_equals_factorization"] for x in (b2, b3, b3_uniform))
