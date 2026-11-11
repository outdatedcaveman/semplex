"""Spike 09: reading circuits off trained networks."""

import numpy as np

from cerp import train


def test_determination_and_effective_width():
    v = lambda j: sum(1 << x for x in range(16) if (x >> j) & 1)
    a, b, c = v(0), v(1), v(2)
    assert train.determines([a, b], a ^ b) and not train.determines([a], a ^ b)
    k, iso = train.effective_width([a, b, c, 0xFFFF ^ a], a ^ b)       # c is irrelevant; ~a duplicates a
    assert k == 2 and set(iso) == {min(a, 0xFFFF ^ a), min(b, 0xFFFF ^ b)}
    assert train.effective_width([a], a & b) == (None, None)            # one unit cannot determine AND
    assert train.effective_width([a], 0) == (0, ())


def test_training_fits_xor_and_the_hard_version_agrees():
    v = lambda j: sum(1 << x for x in range(16) if (x >> j) & 1)
    f = v(0) ^ v(1)
    rng = np.random.default_rng(0)
    B = 16
    p = train.init(B, 8, rng)
    T = np.array([[(f >> x) & 1 for x in range(16)]] * B, dtype=float)
    p, _ = train.train(p, T, np.ones_like(T), 1500, wd=0.03)
    g, faithful, units = train.read_circuits(p)
    assert (g == f).mean() >= 0.9
    for i in np.nonzero(g == f)[0]:
        k, _ = train.effective_width(units[i], f)
        assert k is not None and k >= 2                                  # XOR needs two threshold functions


def test_care_mask_leaves_dont_cares_free():
    rng = np.random.default_rng(1)
    p = train.init(8, 8, rng)
    f, care = 0b0110100110010110, 0x00FF
    T = np.array([[(f >> x) & 1 for x in range(16)]] * 8, dtype=float)
    C = np.array([[(care >> x) & 1 for x in range(16)]] * 8, dtype=float)
    p, _ = train.train(p, T, C, 1500)
    g, _, _ = train.read_circuits(p)
    assert ((g & care) == (f & care)).mean() >= 0.75
