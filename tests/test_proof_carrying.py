"""Spike 03: RUP-certified equivalence beyond the exhaustive wall."""

import random

import pytest

from cerp import kernel
from cerp.benchmarks import carry_prefix, carry_ripple, less_than_borrow, less_than_msb
from cerp.kernel import KernelError
from cerp.ledger import Ledger, Method, Status
from cerp.sat import prove_equivalence


def claim_for(left, right):
    (l, vs), (r, _) = left, right
    return {"vars": vs, "left": l, "right": r}


def test_certifies_equivalence_at_n64():
    c = claim_for(less_than_msb(32), less_than_borrow(32))
    status, cert, _ = prove_equivalence(c)
    assert status == "unsat"
    v = kernel.check_rup({**c, "certificate": cert})
    assert v.ok and v.relation == "rup" and len(v.vars) == 64


def test_non_equivalence_gives_checkable_counterexample_at_n64():
    c = claim_for(carry_ripple(32), carry_prefix(32, bug=True))
    status, x, _ = prove_equivalence(c)
    assert status == "sat"
    assert kernel.check_counterexample({**c, "x": x}).ok
    flipped = dict(x)
    flipped["a0"] ^= 1
    # a wrong witness is rejected (unless it happens to be another counterexample)
    v = kernel.check_counterexample({**c, "x": flipped})
    from cerp.substrates import evaluate
    assert v.ok == (evaluate(c["left"], flipped) != evaluate(c["right"], flipped))


@pytest.fixture(scope="module")
def certified():
    c = claim_for(carry_ripple(8), carry_prefix(8))
    status, cert, _ = prove_equivalence(c)
    assert status == "unsat" and len(cert) > 3
    return c, cert


def test_truncated_certificate_rejected(certified):
    c, cert = certified
    assert not kernel.check_rup({**c, "certificate": cert[:-1]}).ok      # no empty clause
    assert not kernel.check_rup({**c, "certificate": [[]]}).ok           # bare claim of UNSAT


def test_corrupted_lemma_rejected(certified):
    c, cert = certified
    rng = random.Random(0)
    n, _ = kernel.miter_cnf(c)
    rejected = 0
    for _ in range(20):
        bad = [list(l) for l in cert]
        i = rng.randrange(len(bad) - 1)
        bad[i] = [rng.choice([-1, 1]) * rng.randint(1, n)]  # an arbitrary unit "lemma"
        rejected += not kernel.check_rup({**c, "certificate": bad}).ok
    assert rejected >= 15  # a random unit is occasionally RUP-implied; most are not


def test_certificate_cannot_be_reused_for_a_false_claim(certified):
    """The kernel builds the formula from the claim, so a valid certificate
    for one claim does not certify a different (false) one."""
    c, cert = certified
    bad_claim = claim_for(carry_ripple(8), carry_prefix(8, bug=True))
    try:
        accepted = kernel.check_rup({**bad_claim, "certificate": cert}).ok
    except KernelError:  # literal numbering does not even fit the other formula
        accepted = False
    assert not accepted
    # same-size false claim: swap one input in an otherwise identical miter
    (r, vs) = carry_prefix(8)
    swapped = {"kind": "circuit", "body": dict(r["body"], inputs=list(r["body"]["inputs"]))}
    g = [dict(x) for x in swapped["body"]["gates"]]
    for x in g:
        x["in"] = ["b0" if i == "a0" else "a0" if i == "b0" else "a1" if i == "a2" else i for i in x["in"]]
    swapped["body"]["gates"] = g
    false_claim = {"vars": c["vars"], "left": c["left"], "right": swapped}
    assert prove_equivalence(false_claim)[0] == "sat"
    assert not kernel.check_rup({**false_claim, "certificate": cert}).ok


def test_out_of_range_literals_are_malformed(certified):
    c, _ = certified
    with pytest.raises(KernelError):
        kernel.check_rup({**c, "certificate": [[10**9], []]})


def test_ledger_records_rup_as_kernel_checked(certified):
    c, cert = certified
    L = Ledger()
    cl = L.kernel_result("ripple ≡ prefix (8-bit carry)", kernel.check_rup({**c, "certificate": cert}),
                         category="translation")
    assert cl.status is Status.PROVED_IN_FRAGMENT
    assert cl.warrant.basis == {Method.KERNEL_CHECKED}
    assert any("RUP" in a for a in cl.assumptions)


def test_task_relation_via_care_set():
    """x0 & x1 vs x0 differ only when x1 = 0; equal on care = x1."""
    vs = ["x0", "x1"] + [f"p{i}" for i in range(30)]
    left = {"kind": "expr", "body": ["and", ["var", "x0"], ["var", "x1"]]}
    right = {"kind": "expr", "body": ["var", "x0"]}
    care = {"kind": "expr", "body": ["var", "x1"]}
    c = {"vars": vs, "left": left, "right": right, "care": care}
    status, cert, _ = prove_equivalence(c)
    assert status == "unsat" and kernel.check_rup({**c, "certificate": cert}).ok
    status, x, _ = prove_equivalence({"vars": vs, "left": left, "right": right})
    assert status == "sat" and x["x1"] == 0
