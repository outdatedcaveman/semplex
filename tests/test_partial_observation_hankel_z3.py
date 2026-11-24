import numpy as np

from experiments.partial_observation_hankel_z3 import run


def test_all_z3_hankel_assertions_pass():
    d = run()
    assert d["all_assertions_pass"], d["assertions"]


def test_observation_histories_produce_six_distinct_beliefs():
    d = run()
    assert d["unique_posterior_beliefs"] == 6
    assert d["unique_future_profiles"] == 6


def test_linear_predictive_rank_is_two():
    d = run()
    assert d["centered_hankel_rank"] == 2


def test_balanced_product_spectrum_matches_weighted_hankel():
    d = run()
    h = np.asarray(d["weighted_hankel_singular_values_squared"])
    b = np.asarray(d["balanced_product_eigenvalues"])
    assert np.allclose(h[: len(b)], b, atol=1e-10)
    assert np.allclose(h[len(b) :], 0.0, atol=1e-10)
