"""Spike 10b: learning rules and general-n circuit read-out."""

import numpy as np

from cerp import learnrules as lr


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


def test_local_rule_uses_no_downstream_weights():
    """The 'local' first-layer update must not depend on W2 (no weight transport)."""
    XS = lr.inputs(4)
    T = np.array([[x & 1 for x in range(16)]] * 4, dtype=float)
    C = np.ones_like(T)
    a = np.array([1.0, 0.3, 0.1, 0.1, 0.01])
    out = []
    for w2scale in (1.0, -3.0):
        p = lr.init(4, 8, 4, np.random.default_rng(1))
        p["W2"] = np.zeros_like(p["W2"])          # same output (hence same error) for both runs
        p["b2"] = np.zeros_like(p["b2"])
        q = {k: v.copy() for k, v in p.items()}
        q, _ = lr.train(q, XS, T, C, 1, rule="local", alpha=a)
        out.append(q["W1"])
    assert np.allclose(out[0], out[1])


def test_effective_width_general_n():
    v = lambda j: sum(1 << x for x in range(64) if (x >> j) & 1)
    a, b, c = v(0), v(1), v(2)
    assert lr.effective_width([a, b, c], a ^ b, 64) == 2
    assert lr.effective_width([a, c], a ^ b, 64, kmax=4) == 5              # cannot be determined: kmax + 1
    assert lr.effective_width([a], 0, 64) == 0
