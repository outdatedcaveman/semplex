"""Layer G: N(N(C)) = N(C) and N(C1) = N(C2) iff C1 ≡ C2, in fragment F0."""

import itertools

from cerp import kernel
from cerp.bdd import normal_form, task_normal_form
from cerp.substrates import semantics
from cerp.translate import bdd_to_circuit, bdd_to_expr

from .conftest import VARS4, VARS6, random_exprs


def test_idempotent(exprs6):
    for e in exprs6:
        nf = normal_form(e, VARS6)
        assert normal_form(nf, VARS6) == nf
        # also through another substrate and back
        assert normal_form(bdd_to_circuit(nf, VARS6), VARS6) == nf


def test_normal_form_decides_equivalence():
    # small vars -> many semantically equal pairs among random exprs
    es = random_exprs(120, ["a", "b", "c"], depth=4, seed=7)
    eq_pairs = 0
    for e1, e2 in itertools.combinations(es, 2):
        same_nf = normal_form(e1, ["a", "b", "c"]) == normal_form(e2, ["a", "b", "c"])
        v = kernel.check({"relation": "extensional", "vars": ["a", "b", "c"], "left": e1, "right": e2})
        assert same_nf == v.ok
        eq_pairs += v.ok
    assert eq_pairs > 50  # the test actually exercised the "iff" in both directions


def test_canonical_form_is_relative_to_variable_order():
    """Same function, two orders: two different canonical objects of different size."""
    f = {"kind": "expr", "body": ["or", ["or", ["and", ["var", "x1"], ["var", "y1"]],
                                               ["and", ["var", "x2"], ["var", "y2"]]],
                                        ["and", ["var", "x3"], ["var", "y3"]]]}
    good = normal_form(f, ["x1", "y1", "x2", "y2", "x3", "y3"])
    bad = normal_form(f, ["x1", "x2", "x3", "y1", "y2", "y3"])
    assert len(good["body"]["nodes"]) - 2 == 6
    assert len(bad["body"]["nodes"]) - 2 == 14
    v = kernel.check({"relation": "extensional", "vars": ["x1", "y1", "x2", "y2", "x3", "y3"],
                      "left": good, "right": bad})
    assert v.ok


def test_task_normal_form_decides_task_equivalence():
    care = {"kind": "expr", "body": ["or", ["var", "a"], ["var", "b"]]}
    es = random_exprs(60, VARS4, depth=4, seed=3)
    for e1, e2 in itertools.combinations(es, 2):
        same = task_normal_form(e1, care, VARS4) == task_normal_form(e2, care, VARS4)
        v = kernel.check({"relation": "task", "vars": VARS4, "left": e1, "right": e2, "care": care})
        assert same == v.ok


def test_bdd_to_expr_roundtrip_semantics(exprs6):
    for e in exprs6[:40]:
        nf = normal_form(e, VARS6)
        assert semantics(bdd_to_expr(nf), VARS6) == semantics(e, VARS6)
