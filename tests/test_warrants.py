"""Spike 04: status as a structured warrant."""

import itertools
import random

from cerp import kernel
from cerp.ledger import Ledger, Method, Outcome, Status, Warrant, compare, method_geq, project

METHODS = list(Method)


def rand_warrant(rng):
    return Warrant(frozenset(rng.sample(METHODS, rng.randint(1, 3))),
                   frozenset(rng.sample(["k", "py", "hw", "stats"], rng.randint(0, 2))),
                   frozenset(rng.sample(["A1", "A2"], rng.randint(0, 1))))


def test_method_order_is_a_partial_order():
    for a in METHODS:
        assert method_geq(a, a)
    for a, b in itertools.permutations(METHODS, 2):
        assert not (method_geq(a, b) and method_geq(b, a))
    for a, b, c in itertools.product(METHODS, repeat=3):
        if method_geq(a, b) and method_geq(b, c):
            assert method_geq(a, c)


def test_kernel_and_empirical_are_incomparable():
    """The v0 chain ranked them; they differ in kind (Spike 01 F7)."""
    k = Warrant(frozenset({Method.KERNEL_CHECKED}))
    e = Warrant(frozenset({Method.EMPIRICAL}))
    assert compare(k, e) == "incomparable"
    assert compare(k.join(e), k) == "⪯" and compare(k.join(e), e) == "⪯"


def test_warrant_order_is_transitive_and_join_never_strengthens():
    rng = random.Random(0)
    ws = [rand_warrant(rng) for _ in range(120)]
    for a, b in itertools.combinations(ws, 2):
        j = a.join(b)
        assert a.stronger_or_equal(j) and b.stronger_or_equal(j)  # join is a lower bound
    for a, b, c in itertools.islice(itertools.permutations(ws[:25], 3), 6000):
        if a.stronger_or_equal(b) and b.stronger_or_equal(c):
            assert a.stronger_or_equal(c)


def test_conditions_and_trust_weaken():
    base = Warrant(frozenset({Method.KERNEL_CHECKED}), frozenset({"k"}))
    assert compare(base, Warrant(base.basis, base.trusted_base | {"extra"})) == "⪰"
    assert compare(base, Warrant(base.basis, base.trusted_base, frozenset({"A1"}))) == "⪰"


def test_formerly_unlabelable_outputs_now_have_honest_labels():
    L = Ledger()
    a = L.computed("all minimal sets are listed", algorithm="enum.py")
    w = L.witnessed("theta reproduces P within KL 1e-8", witness_check="float64 KL")
    cw = L.assumption("closed world", why="researcher choice")
    ans = L.derived("answer", depends_on=[cw.id], rule="survivors agree", category="t")
    assert a.status is Status.COMPUTED_UNCERTIFIED
    assert w.status is Status.WITNESSED
    assert L.effective_status(ans.id) is Status.CONJECTURE
    assert L.effective_warrant(ans.id).conditions == {cw.id}  # *which* premise, not just "weak"
    # a premise and an argued guess are both CONJECTURE-labelled but different warrants
    g = L.conjecture("guess", rationale="hunch", open_obligation="prove")
    assert compare(cw.warrant, g.warrant) == "incomparable"


def test_kernel_refutation_is_strong_not_weak():
    """v0 ranked REFUTED below HEURISTIC. A kernel-decided refutation is a
    strongly warranted negative claim: outcome and warrant are separate."""
    L = Ledger()
    x = {"kind": "expr", "body": ["var", "x"]}
    nx = {"kind": "expr", "body": ["not", ["var", "x"]]}
    v = kernel.check({"relation": "extensional", "vars": ["x"], "left": x, "right": nx})
    c = L.kernel_result("x ≡ ~x", v, category="t")
    assert c.outcome is Outcome.REFUTED and c.status is Status.REFUTED
    assert Method.KERNEL_CHECKED in c.warrant.basis


def test_projection_is_lossy():
    """Distinct, ordered warrants can share a label; the ledger keeps the difference."""
    e = Warrant(frozenset({Method.EMPIRICAL}))
    ek = Warrant(frozenset({Method.EMPIRICAL, Method.EXACT_UNCERTIFIED}))
    assert project(e, Outcome.ASSERTED) == project(ek, Outcome.ASSERTED) == Status.EMPIRICALLY_SUPPORTED
    assert compare(e, ek) == "⪰"
