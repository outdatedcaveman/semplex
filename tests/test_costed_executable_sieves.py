from experiments.costed_executable_sieves import (
    ChainProbeCategory,
    closure_cost,
    is_sieve,
    raw_budget_family,
    sieve_closure,
)


def test_category_composition_is_associative_and_coherent():
    ChainProbeCategory().validate()


def test_budget_one_probe_family_is_not_a_sieve():
    c = ChainProbeCategory()
    costs = {"g": 1, "h": 3}
    raw = raw_budget_family(c, "X", costs, 1)
    assert raw == {"g"}
    assert not is_sieve(c, "X", raw)


def test_sieve_closure_adds_precomposition_arrow():
    c = ChainProbeCategory()
    closed = sieve_closure(c, "X", {"g"})
    assert closed == {"g", "h"}
    assert is_sieve(c, "X", closed)


def test_closure_can_exceed_the_physical_budget():
    c = ChainProbeCategory()
    costs = {"g": 1, "h": 3}
    raw = raw_budget_family(c, "X", costs, 1)
    closed = sieve_closure(c, "X", raw)
    assert closure_cost(closed, costs) == 3
    assert closure_cost(closed, costs) > 1


def test_budget_three_family_is_a_sieve_without_closure_inflation():
    c = ChainProbeCategory()
    costs = {"g": 1, "h": 3}
    raw = raw_budget_family(c, "X", costs, 3)
    assert raw == {"g", "h"}
    assert is_sieve(c, "X", raw)
    assert sieve_closure(c, "X", raw) == raw
