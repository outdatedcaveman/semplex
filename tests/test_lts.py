"""Spike 05: fragment F1 -- stateful systems; equivalence is protocol-indexed."""

import ast
import pathlib
import random

from cerp import kernel_lts as K
from cerp.lts import (bisim_quotient, bisimulation, deterministic, lts, random_lts,
                      trace_equivalence)

P = lts("p0", [("p0", "a", "p1"), ("p1", "b", "p2"), ("p1", "c", "p3")])                  # a.(b+c)
Q = lts("q0", [("q0", "a", "q1"), ("q0", "a", "q2"), ("q1", "b", "q3"), ("q2", "c", "q4")])  # a.b + a.c
TEST = lts("t0", [("t0", "a", "t1"), ("t1", "b", "t2"), ("t2", "ok", "t2")])                # wants a then b
SYNC = {"a", "b", "c"}


def test_classic_pair_trace_equal_but_not_bisimilar_with_certificates():
    st, pairs = trace_equivalence(P, Q)
    assert st == "equivalent" and K.check_trace_cert(P, Q, pairs).ok
    st, pairs = trace_equivalence(P, Q, completed=True)
    assert st == "equivalent" and K.check_trace_cert(P, Q, pairs, completed=True).ok
    st, phi = bisimulation(P, Q)
    assert st == "not-bisimilar" and K.check_distinguishing_formula(P, Q, phi).ok


def test_the_difference_is_observable_in_a_context():
    """Trace-equivalent systems differ in deadlock once composed with a test:
    I/O-style or trace semantics is not preserved by this context."""
    assert not K.check_context_deadlock(P, TEST, SYNC).ok
    assert K.check_context_deadlock(Q, TEST, SYNC).ok


def test_bisimilar_systems_agree_in_every_context_tried():
    rng = random.Random(3)
    for _ in range(150):
        A = random_lts(rng, 3)
        B = bisim_quotient(A)
        st, R = bisimulation(A, B)
        assert st == "bisimilar" and K.check_bisimulation(A, B, R).ok
        T = random_lts(rng, 2, p=0.5)
        assert K.check_context_deadlock(A, T, {"a", "b"}).ok == K.check_context_deadlock(B, T, {"a", "b"}).ok


def test_hierarchy_bisim_implies_completed_implies_trace_and_all_certified():
    rng = random.Random(0)
    for _ in range(300):
        A, B = random_lts(rng, rng.randint(2, 3)), random_lts(rng, rng.randint(2, 3))
        bs, bc = bisimulation(A, B)
        cs, cc = trace_equivalence(A, B, completed=True)[:2]
        ts, tc = trace_equivalence(A, B)[:2]
        if bs == "bisimilar":
            assert cs == "equivalent" and K.check_bisimulation(A, B, bc).ok
        else:
            assert K.check_distinguishing_formula(A, B, bc).ok
        if cs == "equivalent":
            assert ts == "equivalent" and K.check_trace_cert(A, B, cc, completed=True).ok
        else:
            r = trace_equivalence(A, B, completed=True)
            X, Y = (A, B) if r[2] == "P" else (B, A)
            assert K.check_trace_witness(X, Y, r[1], completed=r[3] == "completed").ok
        if ts == "equivalent":
            assert K.check_trace_cert(A, B, tc).ok
        else:
            _, w, side, _ = trace_equivalence(A, B)
            X, Y = (A, B) if side == "P" else (B, A)
            assert K.check_trace_witness(X, Y, w).ok


def test_for_deterministic_systems_the_hierarchy_collapses():
    rng = random.Random(1)
    for _ in range(300):
        A, B = random_lts(rng, 3, det=True), random_lts(rng, 3, det=True)
        assert deterministic(A) and deterministic(B)
        assert (trace_equivalence(A, B)[0] == "equivalent") == (bisimulation(A, B)[0] == "bisimilar")


def test_quotient_is_idempotent_and_minimal():
    rng = random.Random(2)
    for _ in range(100):
        A = random_lts(rng, 4)
        q1 = bisim_quotient(A)
        q2 = bisim_quotient(q1)
        assert len(q2["body"]["states"]) == len(q1["body"]["states"])
        assert bisimulation(q1, q2)[0] == "bisimilar"


def test_forged_certificates_rejected():
    st, pairs = trace_equivalence(P, Q)
    assert not K.check_bisimulation(P, Q, [("p0", "q0"), ("p1", "q1"), ("p1", "q2")]).ok
    assert not K.check_distinguishing_formula(P, Q, ["dia", "a", ["tt"]]).ok   # both satisfy it
    assert not K.check_trace_cert(P, Q, pairs[:1]).ok                          # not closed
    assert not K.check_trace_witness(P, Q, ["a", "b"]).ok                      # both have ab


def test_kernel_lts_is_independent():
    src = pathlib.Path(K.__file__).read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.level:
            assert node.module == "kernel", f"kernel_lts may import only the core kernel: {node.module}"
