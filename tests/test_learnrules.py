"""Spike 10b: learning rules and general-n circuit read-out."""

import numpy as np
import pytest

from cerp import learnrules as lr


@pytest.mark.slow
def test_rules_fit_xor_except_frozen_is_weaker():
    XS = lr.inputs(4)
    f = sum(1 << x for x in range(16) if ((x >> 0) ^ (x >> 1)) & 1)
    T = np.array([[(f >> x) & 1 for x in range(16)]] * 32, dtype=float)
    C = np.ones_like(T)
    fit = {}
    for rule in ("backprop", "fa", "local", "frozen"):
        rng = np.random.default_rng(0)
        p = lr.init(32, 8, 4, rng)
        p, _ = lr.train(p, XS, T, C, 1500, rule=rule, alpha=np.array([1.0, 0, 0, 0, 0]),
                        fb=rng.normal(0, 0.5, (32, 8)))
        g, units = lr.read(p, XS)
        fit[rule] = float((g == f).mean())
        if rule == "frozen":
            p0 = lr.init(32, 8, 4, np.random.default_rng(0))
            assert np.array_equal(p["W1"], p0["W1"])                     # first layer really is frozen
    assert fit["backprop"] > 0.9 and fit["fa"] > 0.8 and fit["local"] > 0.8


def test_local_rule_does_not_route_error_through_output_weights():
    """With all output weights at zero, backpropagation sends no signal to the first
    layer; the local rule still updates it (the error is broadcast, not transported)."""
    XS = lr.inputs(4)
    T = np.array([[x & 1 for x in range(16)]] * 4, dtype=float)
    C = np.ones_like(T)
    moved = {}
    for rule in ("backprop", "local"):
        p = lr.init(4, 8, 4, np.random.default_rng(1))
        p["W2"] = np.zeros_like(p["W2"])
        before = p["W1"].copy()
        p, _ = lr.train(p, XS, T, C, 1, rule=rule, alpha=np.array([1.0, 0, 0, 0, 0]))
        moved[rule] = float(np.abs(p["W1"] - before).max())
    assert moved["backprop"] == 0.0 and moved["local"] > 0.0


def test_effective_width_general_n():
    v = lambda j: sum(1 << x for x in range(64) if (x >> j) & 1)
    a, b, c = v(0), v(1), v(2)
    assert lr.effective_width([a, b, c], a ^ b, 64) == 2
    assert lr.effective_width([a, c], a ^ b, 64, kmax=4) == 5              # cannot be determined: kmax + 1
    assert lr.effective_width([a], 0, 64) == 0
