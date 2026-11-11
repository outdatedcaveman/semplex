"""Spike 08b: certified lower bounds, general nets, solver cross-check, geometry, bit flips."""

import ast
import pathlib

import pytest

from cerp import atlas, bounds, geometry, kernel
from cerp import kernel_bounds as kb
from cerp.kernel import KernelError


@pytest.fixture(scope="module")
def tables():
    return atlas.build_all(3)


def test_not_threshold_certificate_and_forgeries():
    xor2 = 0b0110
    c = bounds.not_threshold_cert(2, xor2)
    assert kb.check_not_threshold(2, xor2, c["pos"], c["neg"]).ok          # 01 + 10 = 00 + 11
    assert not kb.check_not_threshold(2, xor2, [0, 3], [1, 2]).ok           # labels swapped
    assert not kb.check_not_threshold(2, xor2, [1, 1], [0, 3]).ok           # sums differ
    assert bounds.not_threshold_cert(2, 0b1000) is None                     # AND is a threshold function


def test_threshold_census_is_certified_for_3_inputs(tables):
    """Every 3-input function is either a kernel-checked single neuron or has a
    kernel-checked non-threshold certificate: exactly 104 threshold functions."""
    n_thr = 0
    for f in range(256):
        if f in tables[3].ltf:
            n_thr += 1
        else:
            c = bounds.not_threshold_cert(3, f)
            assert kb.check_not_threshold(3, f, c["pos"], c["neg"]).ok
    assert n_thr == 104


def test_four_neuron_lower_bound_certificate_for_parity(tables):
    par = sum(1 << i for i in range(8) if bin(i).count("1") % 2)
    for f in (par, 255 ^ par):
        c = bounds.not_two_halfspaces_cert(3, f)
        assert c and kb.check_not_two_halfspaces(3, f, c).ok
        assert not kb.check_not_two_halfspaces(3, f, c[:1]).ok              # too few bad sets: a colouring escapes


def test_no_false_lower_bound_certificates(tables):
    tb = tables[3]
    for c in tb.classes():
        e = tb.exhibit[c]
        if tb.hi[e] == 3:
            assert not (bounds.not_two_halfspaces_cert(3, e) and bounds.not_two_halfspaces_cert(3, 255 ^ e))


def test_kernel_bounds_rejects_malformed_and_is_independent():
    with pytest.raises(KernelError):
        kb.check_not_threshold(2, 0b0110, [7], [0])
    src = pathlib.Path(kb.__file__).read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.level:
            assert node.module == "kernel"


def test_general_net_artifact_skip_and_relu():
    V = ["x0", "x1"]
    xor_skip = {"kind": "dnet", "body": {"inputs": V, "neurons": [
        {"in": [0, 1], "w": [1, 1], "b": -2, "act": "step"},                 # AND
        {"in": [0, 1, 2], "w": [1, 1, -2], "b": -1, "act": "step"}]}}        # x0 + x1 - 2 AND >= 1
    xor_relu = {"kind": "dnet", "body": {"inputs": V, "neurons": [
        {"in": [0, 1], "w": [1, -1], "b": 0, "act": "relu"},
        {"in": [0, 1], "w": [-1, 1], "b": 0, "act": "relu"},
        {"in": [2, 3], "w": [1, 1], "b": -1, "act": "step"}]}}
    for art in (xor_skip, xor_relu):
        assert kernel.check({"relation": "extensional", "vars": V, "left": art,
                             "right": atlas.table_artifact(2, 0b0110)}).ok
    bad = {"kind": "dnet", "body": {"inputs": V, "neurons": [{"in": [5], "w": [1], "b": 0, "act": "step"}]}}
    with pytest.raises(KernelError):
        kernel.evaluate(bad, {"x0": 0, "x1": 0})


def test_solver_agrees_with_exact_table(tables):
    ns = pytest.importorskip("cerp.netsolve")
    tb = tables[3]
    for c in tb.classes():
        e, hi = tb.exhibit[c], int(tb.hi[tb.exhibit[c]])
        for w in (2, 3):
            st, art = ns.solve(e, 3, ns.layered(3, [w]), W=2, time_limit=30, workers=1)
            assert st == ("sat" if hi <= w + 1 else "unsat")
    par = sum(1 << i for i in range(8) if bin(i).count("1") % 2)
    st, art = ns.solve(par, 3, ns.chain(3, 2), W=2, workers=1)                # skip connections: 2 neurons
    assert st == "sat" and kernel.check({"relation": "extensional", "vars": atlas.names(3), "left": art,
                                         "right": atlas.table_artifact(3, par)}).ok


def test_one_bit_flip_construction(tables):
    for f in range(256):
        L = atlas.net_layers(tables, 3, f)
        for p in range(8):
            L2 = atlas.flip_bit_layers(L, 3, f, p)
            art = {"kind": "tnet", "body": {"inputs": atlas.names(3), "layers": L2}}
            assert kernel.check({"relation": "extensional", "vars": atlas.names(3), "left": art,
                                 "right": atlas.table_artifact(3, f ^ (1 << p))}).ok
            assert sum(map(len, L2)) == sum(map(len, L)) + (2 if len(L) == 1 else 1)


def test_weight_space_geometry_small(tables):
    r = geometry.analyse(2, 2, 1, tables[2].canon, tables[2].hi)
    assert r["weight_settings"] == 3 ** 9 and r["functions_realized"] == 16
    assert r["volume_share_by_min_neurons"][1] > 0.99                        # XOR is rare in weight space
    assert sum(r["border_pairs_by_hamming_distance"].values()) > 0
