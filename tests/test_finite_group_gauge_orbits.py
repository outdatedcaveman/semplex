from fractions import Fraction as F

from experiments import finite_group_gauge_orbits as g


def test_group_axioms_for_s3_and_d4():
    assert g.group_axioms_hold(g.s3_group())
    assert g.group_axioms_hold(g.d4_group())


def test_holonomy_gauge_covariance_for_s3_and_d4():
    assert g.holonomy_is_gauge_covariant(g.s3_group())
    assert g.holonomy_is_gauge_covariant(g.d4_group())


def test_generic_gauge_ring_orbits_for_s3():
    result = g.gauge_ring_orbits(g.s3_group())
    assert result["group_order"] == 6
    assert result["connection_count"] == 216
    assert result["conjugacy_class_count"] == 3
    assert sorted(row["orbit_size"] for row in result["orbits"]) == [36, 72, 108]


def test_generic_gauge_ring_orbits_for_dihedral_d4():
    result = g.gauge_ring_orbits(g.d4_group())
    assert result["group_order"] == 8
    assert result["connection_count"] == 512
    assert result["gauge_transformation_count"] == 512
    assert result["conjugacy_class_count"] == 5
    assert sorted(row["conjugacy_class_size"] for row in result["orbits"]) == [1, 1, 2, 2, 2]
    assert sorted(row["orbit_size"] for row in result["orbits"]) == [64, 64, 128, 128, 128]


def test_class_markov_lift_is_gauge_equivariant_for_d4():
    group = g.d4_group()
    n = len(g.conjugacy_classes(group))
    transition = tuple(
        tuple(F(3, 4) if i == j else F(1, 4) if j == (i + 1) % n else F(0)
              for j in range(n))
        for i in range(n)
    )
    lifted = g.lift_class_kernel(group, transition)
    assert g.lifted_kernel_is_stochastic(group, lifted)
    assert g.lifted_kernel_is_conjugation_equivariant(group, lifted)


def test_general_symmetric_channel_determinant_for_three_and_five_sectors():
    for n, eta in ((3, F(1, 6)), (5, F(1, 10)), (5, F(1, 5)), (5, F(1, 4))):
        channel = g.symmetric_observation_channel(n, eta)
        assert all(sum(row, F(0)) == 1 for row in channel)
        assert g.determinant(channel) == g.symmetric_channel_determinant(n, eta)
    assert g.symmetric_channel_determinant(5, F(1, 10)) == F(1, 16)
    assert g.symmetric_channel_determinant(5, F(1, 5)) == 0
    anti_identity = g.symmetric_observation_channel(5, F(1, 4))
    assert all(sum(row, F(0)) == 1 for row in anti_identity)
    assert all(anti_identity[i][i] == 0 for i in range(5))
    assert g.determinant(anti_identity) == F(1, 256)
    assert g.probe_separates_beliefs(5, F(1, 4), F(1, 16))


def test_generalized_probe_separates_beliefs_iff_both_factors_are_invertible():
    assert g.probe_separates_beliefs(5, F(1, 10), F(1, 16))
    assert not g.probe_separates_beliefs(5, F(1, 5), F(1, 16))
    assert not g.probe_separates_beliefs(5, F(1, 10), F(0))


def test_class_kernel_lift_is_not_unique_and_erases_intra_class_state():
    group = g.d4_group()
    classes = g.conjugacy_classes(group)
    n = len(classes)
    transition = tuple(
        tuple(F(3, 4) if i == j else F(1, 4) if j == (i + 1) % n else F(0)
              for j in range(n))
        for i in range(n)
    )
    lifted = g.lift_class_kernel(group, transition)
    identity = g.identity_group_kernel(group)
    assert g.lifted_kernel_is_conjugation_equivariant(group, lifted)
    assert g.group_kernel_is_conjugation_equivariant(group, identity)
    assert g.group_kernel_is_lumpable_over_classes(group, identity)
    assert g.group_kernel_is_lumpable_over_classes(group, lifted)
    # Identity preserves the exact group element; the uniform lift sends all
    # members of a source conjugacy class to identical next-state distributions.
    assert identity != lifted
    index = {x: i for i, x in enumerate(group.elements)}
    transposition_class = next(c for c in classes if len(c) == 2)
    a, b = tuple(transposition_class)
    assert identity[index[a]] != identity[index[b]]
    assert lifted[index[a]] == lifted[index[b]]
