"""Spike 08: periodic table of threshold circuits (n <= 3 here; n = 4 in the experiment)."""

import numpy as np
import pytest

from cerp import atlas, kernel
from cerp.kernel import KernelError


@pytest.fixture(scope="module")
def tables():
    return atlas.build_all(3)


def check(tables, m, f):
    art = atlas.artifact(tables, m, f)
    v = kernel.check({"relation": "extensional", "vars": atlas.names(m), "left": art,
                      "right": atlas.table_artifact(m, f)})
    return v.ok, art["body"]["layers"]


def test_threshold_function_counts_match_known_values(tables):
    assert [len(tables[m].ltf) for m in (1, 2, 3)] == [4, 14, 104]   # OEIS A000609
    assert [len(tables[m].exhibit) for m in (2, 3)] == [4, 14]        # NPN classes


def test_every_3_input_function_has_a_kernel_verified_net_of_the_stated_size(tables):
    tb = tables[3]
    for f in range(256):
        ok, layers = check(tables, 3, f)
        assert ok and sum(atlas.shape(layers)) == tb.hi[f]
    assert all(tb.exact(f) for f in range(256))


def test_known_landmarks(tables):
    tb = tables[3]
    v = lambda j: sum(1 << i for i in range(8) if (i >> j) & 1)
    a, b, c = v(0), v(1), v(2)
    assert tb.hi[(a & b) | (a & c) | (b & c)] == 1          # majority is one neuron
    assert tb.hi[a ^ b] == 3 and tables[2].hi[0b0110] == 3   # XOR needs 2 hidden + output
    assert tb.hi[a ^ b ^ c] == 4 and tb.depth[a ^ b ^ c] == 2
    assert 2 not in set(tb.hi.tolist())                      # no element has 2 neurons


def test_cost_is_a_class_invariant(tables):
    tb = tables[3]
    for c in tb.classes():
        members = np.nonzero(tb.canon == c)[0]
        assert len(set(tb.hi[members].tolist())) == 1


def test_first_layer_is_an_observational_power(tables):
    """Protocol-Frame link: neurons = (min determining width) + 1 for every
    non-threshold 3-input function."""
    tb = tables[3]
    for c in tb.classes():
        e = tb.exhibit[c]
        w, k = atlas.min_determining_layers(tb, e)
        if tb.hi[e] > 1:
            assert tb.hi[e] == w + 1 and k >= 1


def test_compiler_returns_verified_task_optimal_nets(tables):
    xor3 = sum(1 << i for i in range(8) if bin(i).count("1") % 2)
    care = sum(1 << i for i in range(8) if not (i >> 2) & 1)       # only inputs with x2 = 0
    r = atlas.compile_task(tables, 3, xor3, care)
    assert r["exact_neurons"] == 4 and r["neurons"] == 3 and r["optimal"]   # XOR2 suffices on the care set
    v = kernel.check({"relation": "task", "vars": atlas.names(3), "left": r["net"],
                      "right": atlas.table_artifact(3, xor3), "care": atlas.table_artifact(3, care)})
    assert v.ok
    full = atlas.compile_task(tables, 3, xor3, 255)
    assert full["neurons"] == 4 and full["function"] == xor3


def test_kernel_rejects_malformed_threshold_nets():
    bad = {"kind": "tnet", "body": {"inputs": ["x0"], "layers": [[{"w": [1], "t": 1}, {"w": [1], "t": 0}]]}}
    with pytest.raises(KernelError):
        kernel.evaluate(bad, {"x0": 1})
    frac = {"kind": "tnet", "body": {"inputs": ["x0"], "layers": [[{"w": [0.5], "t": 1}]]}}
    with pytest.raises(KernelError):
        kernel.evaluate(frac, {"x0": 1})
