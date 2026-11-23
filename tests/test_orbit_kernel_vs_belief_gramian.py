import numpy as np

from experiments.orbit_kernel_vs_belief_gramian import (
    arbitrary_readout_kernel,
    master_operators_z2,
)


def test_uniform_prior_past_gramian_vanishes_for_z2_bijections():
    d = master_operators_z2()
    assert np.allclose(d["Wc"], 0.0, atol=1e-12)


def test_future_observability_and_orbit_kernel_are_nonzero():
    d = master_operators_z2()
    assert np.linalg.norm(d["Wo"]) > 1e-8
    assert np.array_equal(d["K_orbit"], np.eye(2))


def test_balanced_product_using_current_past_gramian_collapses():
    d = master_operators_z2()
    assert np.allclose(d["G_balanced_from_current_Wc"], 0.0, atol=1e-12)
    assert np.linalg.norm(d["K_orbit"]) > 0


def test_centered_state_reachability_baseline_recovers_future_gramian():
    d = master_operators_z2()
    assert np.allclose(d["G_balanced_from_state_Wc"], d["Wo"], atol=1e-12)


def test_heat_sandwich_retains_nonzero_semantic_direction():
    d = master_operators_z2()
    assert np.linalg.norm(d["G_sum"]) > 1e-8
    assert np.linalg.matrix_rank(d["G_sum"], tol=1e-10) == 1


def test_orbit_kernel_is_psd_for_arbitrary_vector_readout():
    rng = np.random.default_rng(20261121)
    readout = rng.normal(size=(2, 5))
    K = arbitrary_readout_kernel(readout)
    assert np.linalg.eigvalsh(K).min() >= -1e-10


def test_z2_orbit_kernel_is_group_circulant_for_arbitrary_readout():
    rng = np.random.default_rng(20261121)
    K = arbitrary_readout_kernel(rng.normal(size=(2, 4)))
    assert np.allclose(K[0, 0], K[1, 1])
    assert np.allclose(K[0, 1], K[1, 0])


def test_sum_and_balanced_product_can_select_opposite_modes():
    Wc = np.diag([100.0, 60.0])
    Wo = np.diag([1.0, 40.0])
    Wsum = Wc + Wo
    Wbal = np.sqrt(Wc) @ Wo @ np.sqrt(Wc)
    assert np.argmax(np.diag(Wsum)) == 0
    assert np.argmax(np.diag(Wbal)) == 1
    assert np.allclose(np.diag(Wsum), [101.0, 100.0])
    assert np.allclose(np.diag(Wbal), [100.0, 2400.0])


def test_kinematic_dirichlet_cost_is_not_entropy_production():
    d = master_operators_z2()
    assert abs(d["entropy_production"]) < 1e-12
    assert np.linalg.norm(d["Lkin"]) > 1e-8
