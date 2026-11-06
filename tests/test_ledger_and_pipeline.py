import pytest

from cerp import kernel
from cerp.demo import ALARM, SENSORS_AGREE
from cerp.ledger import Ledger, LedgerError, Status
from cerp.pipeline import analyze, default_translators

X = {"kind": "expr", "body": ["var", "x"]}


# ---------------------------------------------------------------- ledger

def test_proof_status_requires_authentic_kernel_verdict():
    L = Ledger()
    with pytest.raises(LedgerError):
        L.kernel_result("x = x", {"ok": True}, category="t")
    v = kernel.check({"relation": "extensional", "vars": ["x"], "left": X, "right": X})
    assert L.kernel_result("x = x", v, category="t").status is Status.PROVED_IN_FRAGMENT


def test_derived_claims_are_capped_by_weakest_dependency():
    L = Ledger()
    v = kernel.check({"relation": "extensional", "vars": ["x"], "left": X, "right": X})
    p = L.kernel_result("p", v, category="t")
    e = L.empirical("e", protocol="toy", data=[1, 2], uncertainty="n=2, no CI")
    d = L.derived("p and e", depends_on=[p.id, e.id], rule="conjunction", category="t")
    assert d.status is Status.EMPIRICALLY_SUPPORTED
    c = L.conjecture("q", rationale="hunch", open_obligation="prove q")
    # a claim recorded as PROVED but resting on a conjecture is effectively a conjecture
    p2 = L.kernel_result("p2", v, category="t", depends_on=[c.id])
    assert p2.status is Status.PROVED_IN_FRAGMENT
    assert L.effective_status(p2.id) is Status.CONJECTURE


def test_empirical_claims_need_protocol_and_uncertainty():
    with pytest.raises(LedgerError):
        Ledger().empirical("it works", protocol="", data=[], uncertainty="")


# ---------------------------------------------------------------- pipeline

def test_demo_end_to_end():
    rep = analyze(ALARM, ["a", "b", "c", "d"], care=SENSORS_AGREE, name="alarm")
    assert rep["status"] == "OK"
    assert rep["sufficiency"]["minimal_sufficient_sets"] == [["a", "c", "d"], ["b", "c", "d"]]
    assert not rep["rejected"]
    L = rep["ledger"]
    improvements = [c for c in L.claims.values() if c.category == "improvement"]
    assert improvements and all("task fidelity" in c.statement for c in improvements)
    # enumeration completeness is honestly NOT proved
    assert any(c.status is Status.CONJECTURE and "minimal sufficient sets" in c.statement
               for c in L.claims.values())


def test_unsound_translator_is_caught_and_recorded():
    """Charter §12.1: counterexamples for intentionally unsound transformations."""
    def buggy(src, nf, vars):  # swaps AND and OR at the root
        b = src["body"]
        swap = {"and": "or", "or": "and"}
        return {"kind": "expr", "body": [swap.get(b[0], b[0])] + b[1:]}

    tr = default_translators()
    tr["buggy"] = buggy
    rep = analyze(ALARM, ["a", "b", "c", "d"], name="alarm", translators=tr)
    rej = [r for r in rep["rejected"] if r["translator"] == "buggy"]
    assert len(rej) == 1 and rej[0]["counterexample"]
    assert rep["ledger"].claims[rej[0]["claim"]].status is Status.REFUTED
    assert all(c["translator"] != "buggy" for c in rep["candidates"])


def test_crashing_translator_is_recorded_not_fatal():
    tr = default_translators()
    tr["crash"] = lambda *a: 1 / 0
    rep = analyze(ALARM, ["a", "b", "c", "d"], translators=tr)
    assert rep["status"] == "OK"
    assert any("crash" in c.statement and c.status is Status.HEURISTIC for c in rep["ledger"].claims.values())


@pytest.mark.parametrize("source,vars,why", [
    ({"kind": "turing_machine", "body": {}}, ["x"], "not an F0 artifact"),
    (X, [f"v{i}" for i in range(kernel.MAX_VARS + 1)], "exceeds"),
    ({"kind": "expr", "body": ["var", "z"]}, ["x"], "undeclared"),
])
def test_out_of_scope_returns_boundary_not_a_guess(source, vars, why):
    rep = analyze(source, vars)
    assert rep["status"] == "OUT-OF-SCOPE"
    (c,) = rep["ledger"].claims.values()
    assert c.status is Status.OUT_OF_SCOPE and why in c.statement


def test_task_front_never_worse_than_exact_front():
    """Because ≡_ext ⊆ ≡_T, exact realizations are task candidates too."""
    from cerp.resources import dominates
    from .conftest import random_exprs
    care = {"kind": "expr", "body": ["or", ["var", "a"], ["not", ["var", "c"]]]}
    for e in random_exprs(25, ["a", "b", "c", "d"], depth=4, seed=21):
        rep = analyze(e, ["a", "b", "c", "d"], care=care)
        for (sub, rel), ext_front in rep["pareto"].items():
            if rel != "extensional":
                continue
            task_front = rep["pareto"][(sub, "task")]
            for x in ext_front:
                assert not any(dominates(x["cost"], t["cost"]) for t in task_front)
