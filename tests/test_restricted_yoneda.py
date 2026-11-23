from experiments.restricted_yoneda_probe_benchmark import (
    diagnostics,
    parallel_pair,
    walking_arrow,
    discrete_pair,
    budget_frontier,
)


def test_restricted_yoneda_can_be_fully_faithful_on_a_proper_probe_subcategory():
    c = walking_arrow()
    result = diagnostics(c, ("1",))
    assert result["object_separating"]
    assert result["fully_faithful"]
    assert result["faithfulness_defect"] == 0
    assert result["fullness_defect"] == 0


def test_object_separation_does_not_imply_full_faithfulness():
    c = parallel_pair()
    result = diagnostics(c, ("A",))
    assert result["object_separating"]
    assert not result["fully_faithful"]
    assert result["faithfulness_defect"] == 0
    assert result["fullness_defect"] == 4


def test_restricted_probe_can_lose_distinct_morphisms():
    c = parallel_pair()
    result = diagnostics(c, ("B",))
    assert result["object_separating"]
    assert not result["fully_faithful"]
    assert result["faithfulness_defect"] == 1


def test_all_objects_recover_full_yoneda_on_finite_parallel_pair():
    c = parallel_pair()
    result = diagnostics(c, ("A", "B"))
    assert result["fully_faithful"]
    assert result["faithfulness_defect"] == 0
    assert result["fullness_defect"] == 0


def test_discrete_pair_exhibits_extra_natural_transformation():
    c = discrete_pair()
    result = diagnostics(c, ("A",))
    assert result["object_separating"]
    assert result["fullness_defect"] == 1
    assert not result["fully_faithful"]


def test_minimum_probe_cost_for_parallel_pair_is_four():
    c = parallel_pair()
    frontier = budget_frontier(c, {"A": 1, "B": 3})
    feasible = [r["cost"] for r in frontier if r["fully_faithful"]]
    assert feasible == [4]


def test_probe_naturality_not_just_componentwise_functions():
    # For the walking arrow, probing at object 0 alone sees both objects
    # as singleton sets. The arrow 0->1 in the probe category is required
    # to enforce naturality and recover the original category.
    c = walking_arrow()
    weak = diagnostics(c, ("0",))
    strong = diagnostics(c, ("1",))
    assert not weak["object_separating"]
    assert strong["fully_faithful"]
