from experiments.resource_relative_probe_sieves import (
    ResourceProbeCategory,
    affordable,
    grade_shift,
    is_full_sieve,
    is_relative_sieve,
)


def test_category_laws_and_cost_subadditivity():
    ResourceProbeCategory().validate()


def test_budget_one_profiles_are_sieves_relative_to_free_refinements():
    c = ResourceProbeCategory()
    family = affordable(c, "X", 1)
    assert family == {"iX", "g", "h"}
    assert is_relative_sieve(c, "X", family)


def test_same_budget_profile_is_not_a_sieve_under_paid_refinements():
    c = ResourceProbeCategory()
    family = affordable(c, "X", 1)
    assert not is_full_sieve(c, "X", family)
    assert c.compose("h", "v") == "k"
    assert c.costs["k"] == 3


def test_budget_three_restores_full_sieve_closure():
    c = ResourceProbeCategory()
    family = affordable(c, "X", 3)
    assert family == {"iX", "g", "h", "k"}
    assert is_full_sieve(c, "X", family)


def test_costly_postcomposition_shifts_budget_grade():
    c = ResourceProbeCategory()
    source = affordable(c, "X", 1)
    shifted = grade_shift(c, "t", source, 3)
    assert shifted == {"iX": "t", "g": "tg", "h": "th"}
    assert set(shifted.values()) <= affordable(c, "Y", 3)


def test_grade_shift_is_natural_under_free_refinement():
    c = ResourceProbeCategory()
    source = affordable(c, "X", 1)
    t = "t"
    for f in source:
        for u in c.free:
            if c.target[u] == c.source[f]:
                left = c.compose(t, c.compose(f, u))
                right = c.compose(c.compose(t, f), u)
                assert left == right


def test_free_subcategory_is_wide_and_composition_closed():
    c = ResourceProbeCategory()
    assert {c.source[a] for a in c.free} | {c.target[a] for a in c.free} == set(c.objects)
    for a in c.free:
        for b in c.free:
            if c.target[b] == c.source[a]:
                assert c.compose(a, b) in c.free
