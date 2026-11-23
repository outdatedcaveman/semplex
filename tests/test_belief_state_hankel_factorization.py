import numpy as np

from experiments.belief_state_hankel_factorization import run


def test_action_only_uniform_prior_has_zero_past_gramian():
    d = run()
    assert d["assertions"]["action_only_prior_gramian_zero"]


def test_observations_create_nonzero_posterior_gramian():
    d = run()
    assert d["assertions"]["posterior_gramian_is_centered_projector"]


def test_future_observability_gramian_is_nonzero():
    d = run()
    assert d["assertions"]["future_gramian_nonzero"]


def test_history_future_hankel_factorizes_through_posterior():
    d = run()
    assert d["assertions"]["H_factorizes_through_posterior"]


def test_action_only_and_observed_histories_have_different_semantic_quotients():
    d = run()
    assert d["assertions"]["action_only_one_profile"]
    assert d["assertions"]["observation_histories_two_profiles"]


def test_balanced_product_uses_observation_conditioned_past_information():
    d = run()
    assert d["assertions"]["action_only_balanced_product_zero"]
    assert d["assertions"]["observed_balanced_product_nonzero"]
