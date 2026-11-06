"""Spike 06: Lean-checked claims. Skipped unless CERP_LEAN points to Lean 4."""

import pytest

from cerp import kernel
from cerp.bdd import normal_form
from cerp.benchmarks import carry_prefix, carry_ripple
from cerp.demo import ALARM, SENSORS_AGREE
from cerp.ledger import Ledger, LedgerError, Method, Status, compare
from cerp.sat import prove_equivalence
from cerp.translate import bdd_to_expr

lean_bridge = pytest.importorskip("cerp.lean_bridge")
try:
    lean_bridge.lean_binary()
except lean_bridge.LeanUnavailable:
    pytest.skip("Lean 4 not available (set CERP_LEAN)", allow_module_level=True)

V = ["a", "b", "c", "d"]


def test_true_equivalence_is_proved_without_extra_axioms():
    r, _ = lean_bridge.prove_expr_claim(ALARM, bdd_to_expr(normal_form(ALARM, V)), V, name="t_eq")
    assert r.ok and set(r.axioms) <= {"propext", "Quot.sound", "Classical.choice"}


def test_task_equivalence_is_proved():
    proj = {"kind": "expr", "body": ["or", ["and", ["var", "a"], ["var", "c"]],
                                     ["and", ["var", "a"], ["var", "d"]]]}
    r, _ = lean_bridge.prove_expr_claim(ALARM, proj, V, care=SENSORS_AGREE, name="t_task")
    assert r.ok


def test_false_claim_is_rejected():
    bad = {"kind": "expr", "body": ["and", ["var", "a"], ["var", "c"]]}
    r, _ = lean_bridge.prove_expr_claim(ALARM, bad, V, name="t_bad")
    assert not r.ok and "sorryAx" in r.axioms


def test_rup_certificate_replayed_by_lean_kernel():
    (l, vs), (rr, _) = carry_ripple(2), carry_prefix(2)
    c = {"vars": vs, "left": l, "right": rr}
    _, F = kernel.miter_cnf(c)
    _, lemmas, _ = prove_equivalence(c)
    r, _ = lean_bridge.prove_cnf_unsat(F, lemmas, name="t_carry2")
    assert r.ok and "Lean.ofReduceBool" not in r.axioms
    bad, _ = lean_bridge.prove_cnf_unsat(F, lemmas[:-1], name="t_carry2_trunc")
    assert not bad.ok


def test_ledger_proof_assistant_warrant_is_strongest_and_names_its_bridge():
    L = Ledger()
    r, _ = lean_bridge.prove_expr_claim(ALARM, bdd_to_expr(normal_form(ALARM, V)), V, name="t_led")
    c = L.proof_assistant("alarm ≡ N(alarm)", r, category="canonicalization")
    assert c.status is Status.PROVED and c.warrant.basis == {Method.PROOF_ASSISTANT}
    v = kernel.check({"relation": "extensional", "vars": V, "left": ALARM,
                      "right": bdd_to_expr(normal_form(ALARM, V))})
    k = L.kernel_result("same, by Python kernel", v, category="canonicalization")
    # stronger method, but different trusted bases => the order says incomparable, honestly
    assert compare(c.warrant, k.warrant) == "incomparable"
    bad, _ = lean_bridge.prove_expr_claim(ALARM, {"kind": "expr", "body": ["var", "a"]}, V, name="t_led2")
    with pytest.raises(LedgerError):
        L.proof_assistant("false", bad, category="x")
