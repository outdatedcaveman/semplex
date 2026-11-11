"""Spike 10b: systematic local learning rules."""

import numpy as np
import pytest

from cerp import localrules as L

jax = pytest.importorskip("jax")
import jax.numpy as jnp  # noqa: E402


def test_dictionary_sizes_and_closure():
    sizes = {P: [len(L.enumerate_monomials(P, K)) for K in (2, 3, 4)] for P in "ABC"}
    assert sizes == {"A": [2, 3, 11], "B": [2, 5, 16], "C": [3, 8, 30]}
    for P, Q in (("A", "B"), ("B", "C")):                       # more observational power, larger dictionary
        a = {m["label"] for m in L.enumerate_monomials(P, 4)}
        b = {m["label"] for m in L.enumerate_monomials(Q, 4)}
        assert a < b
    labels = [m["label"] for m in L.enumerate_monomials("C", 4)]
    assert len(set(labels)) == len(labels)
    for m in L.enumerate_monomials("C", 4):                     # every index contracted exactly twice
        s = "".join(m["subs"])
        assert all(s.count(ch) == 2 for ch in set(s))


def test_backprop_is_one_monomial_of_power_C():
    """The gradient of  E * (V . Y)  w.r.t. the first layer is the backpropagated gradient."""
    monos = L.enumerate_monomials("C", 3)
    i = [m["label"] for m in monos].index("Y[a]*E*V[a]")
    tr = L.make_trainer(monos, 4)
    rng = np.random.default_rng(0)
    X = jnp.asarray(L.inputs_aug(4))
    W = jnp.asarray(rng.normal(0, 0.5, (8, 5)).astype(np.float32))
    v = jnp.asarray(rng.normal(0, 0.5, 8).astype(np.float32))
    e = jnp.asarray(rng.normal(0, 0.5, 16).astype(np.float32))
    care = jnp.ones(16)
    g = tr["grad_local"](W, X, care, e, v, jnp.zeros(len(monos)).at[i].set(1.0))
    y = jnp.tanh(X @ W.T)
    bp = ((e[:, None] * v[None, :] * (1 - y * y)).T @ X) / 16
    assert np.allclose(np.asarray(g), np.asarray(bp), atol=1e-5)
    assert "Y[a]*E*V[a]" not in [m["label"] for m in L.enumerate_monomials("B", 4)]


def test_power_A_rules_are_task_blind():
    """A rule that observes only its own layer learns the same first layer for every task."""
    monos = L.enumerate_monomials("A", 4)
    tr = L.make_trainer(monos, 4)
    rng = np.random.default_rng(1)
    coef = jnp.asarray(rng.normal(0, 0.01, len(monos)).astype(np.float32))
    st = tuple(map(jnp.asarray, L.init_states(6, 8, 4, np.random.default_rng(3))))
    X = jnp.asarray(L.inputs_aug(4))
    T1 = rng.integers(0, 2, (6, 16)).astype(np.float32)
    C = np.ones_like(T1)
    run = tr["run"](40)
    w_a = np.asarray(run(coef, st, X, T1, C)[0])
    w_b = np.asarray(run(coef, st, X, 1 - T1, C)[0])
    assert np.array_equal(w_a, w_b)
    monos_b = L.enumerate_monomials("B", 4)                      # with the error visible, it is not
    trb = L.make_trainer(monos_b, 4)
    cb = jnp.asarray(rng.normal(0, 0.01, len(monos_b)).astype(np.float32))
    rb = trb["run"](40)
    assert not np.array_equal(np.asarray(rb(cb, st, X, T1, C)[0]), np.asarray(rb(cb, st, X, 1 - T1, C)[0]))


def test_search_keeps_a_working_rule_working():
    """Sanity gate from Spike 10c: started from backpropagation, the search must not destroy it."""
    monos = L.enumerate_monomials("C", 3, "O")
    labels = [m["label"] for m in monos]
    tr = L.make_trainer(monos, 4)
    rng = np.random.default_rng(1)
    X = jnp.asarray(L.inputs_aug(4))
    fs = [0x6666, 0x8888, 0x6996, 0x0FF0, 0x8000, 0x7888] * 4
    T = np.array([[(f >> x) & 1 for x in range(16)] for f in fs], dtype=np.float32)
    C = np.ones_like(T)
    units = L.natural_units(monos, tr, X, 8, 4, rng)
    warm = np.zeros(len(monos), dtype=np.float32)
    warm[labels.index("Y[a]*E*V[a]")] = 1.0                      # backpropagation in natural units
    a, hist = L.cem_search(tr, units, X, T, C, 8, 4, rng, gens=4, pop=8, elite=3, start=warm)
    assert hist[-1][1] >= 0.9                                     # fit rate of the incumbent
    assert a[labels.index("Y[a]*E*V[a]")] > 0.3
