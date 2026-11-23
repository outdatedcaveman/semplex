from experiments.character_hott_gauge_bridge import (
    action_groupoid_functor_checks,
    action_groupoid_functor_preserves_composition,
    action_groupoid_functor_preserves_identity,
    bouquet_two_loop_counterexample,
    centralizer_size,
    d4_character_table,
    s3_character_table,
)
from experiments.finite_group_gauge_orbits import d4_group, s3_group


def test_irreducible_s3_characters_separate_conjugacy_classes():
    table = s3_character_table()
    assert table.row_orthogonality_holds()
    assert table.separates((0, 1, 2))
    assert table.separating_subsets() == ((2,),)
    assert table.pair_coverage()[(0, 1)] == (1, 2)
    assert table.pair_coverage()[(0, 2)] == (2,)
    assert table.pair_coverage()[(1, 2)] == (1, 2)


def test_irreducible_d4_characters_separate_conjugacy_classes():
    table = d4_character_table()
    assert table.row_orthogonality_holds()
    assert table.separates((0, 1, 2, 3, 4))
    assert table.separating_subsets() == (
        (1, 2, 4), (1, 3, 4), (2, 3, 4)
    )
    assert table.minimum_weighted_subset((1, 2, 3, 4, 5)) == (10, 3, (1, 2, 4))


def test_character_budget_can_block_full_abstraction():
    table = d4_character_table()
    assert table.minimum_weighted_subset((1, 2, 3, 4, 5), budget=6) is None
    assert table.minimum_weighted_subset((1, 2, 3, 4, 5), budget=10) is not None


def test_action_groupoid_equivalence_on_s3_exhaustively():
    result = action_groupoid_functor_checks(s3_group(), exhaustive=True)
    assert result["fully_faithful"]
    assert result["pairs_checked"] == 216 ** 2
    assert result["essentially_surjective"]
    assert result["set_truncation_classes"] == 3


def test_action_groupoid_equivalence_on_d4_exhaustively():
    result = action_groupoid_functor_checks(d4_group(), exhaustive=True)
    assert result["fully_faithful"]
    assert result["pairs_checked"] == 512 ** 2
    assert result["essentially_surjective"]
    assert result["set_truncation_classes"] == 5


def test_gauge_stabilizers_are_holonomy_centralizers():
    s3, d4 = s3_group(), d4_group()
    assert sorted(centralizer_size(s3, h) for h in s3.elements) == [2, 2, 2, 3, 3, 6]
    assert sorted(centralizer_size(d4, h) for h in d4.elements) == [4, 4, 4, 4, 4, 4, 8, 8]


def test_holonomy_functor_preserves_identity_and_composition():
    assert action_groupoid_functor_preserves_identity(s3_group())
    assert action_groupoid_functor_preserves_composition(s3_group())
    assert action_groupoid_functor_preserves_identity(d4_group())
    assert action_groupoid_functor_preserves_composition(d4_group())


def test_two_loop_bouquet_requires_simultaneous_conjugation():
    witness = bouquet_two_loop_counterexample(s3_group())
    assert witness["componentwise_classes_match"]
    assert not witness["simultaneous_conjugate"]
    assert witness["product_left"] != witness["product_right"]
