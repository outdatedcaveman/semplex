from experiments.costed_executable_sieves import ChainProbeCategory
from experiments.semiotic_threshold_sieve_counterexample import threshold_family
from experiments.costed_executable_sieves import is_sieve, sieve_closure


WEIGHTS = {"iQ": 1.0, "iP": 1.0, "iX": 1.0, "u": 0.5, "g": 0.9, "h": 0.45}


def test_multiplicative_confidence_composition():
    assert WEIGHTS["h"] == WEIGHTS["g"] * WEIGHTS["u"]


def test_high_threshold_confidence_set_is_not_a_sieve():
    c = ChainProbeCategory()
    family = threshold_family(c, "X", WEIGHTS, 0.8)
    # The identity has confidence 1 and is included, but its sieve closure
    # must contain every arrow into X, including the low-confidence h.
    assert family == {"g", "iX"}
    assert not is_sieve(c, "X", family)


def test_sieve_closure_adds_low_confidence_composite():
    c = ChainProbeCategory()
    family = threshold_family(c, "X", WEIGHTS, 0.8)
    closure = sieve_closure(c, "X", family)
    assert closure == {"g", "h", "iX"}
    assert "h" in closure - family


def test_low_enough_threshold_gives_the_maximal_sieve_in_this_example():
    c = ChainProbeCategory()
    family = threshold_family(c, "X", WEIGHTS, 0.45)
    assert family == {"g", "h", "iX"}
    assert is_sieve(c, "X", family)
