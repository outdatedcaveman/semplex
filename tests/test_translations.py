"""Layer J: untrusted translators, kernel-checked; two interpreters cross-checked."""

from cerp import kernel
from cerp.bdd import normal_form
from cerp.semantics import assignments
from cerp.substrates import evaluate
from cerp.translate import (bdd_to_circuit, bdd_to_dfa, bdd_to_expr, circuit_to_expr,
                            expr_to_circuit)

from .conftest import VARS6


def all_translations(e):
    nf = normal_form(e, VARS6)
    c = expr_to_circuit(e, VARS6)
    return {
        "expr->circuit": c,
        "circuit->expr": circuit_to_expr(c),
        "nf": nf,
        "nf->circuit": bdd_to_circuit(nf, VARS6),
        "nf->dfa": bdd_to_dfa(nf),
        "nf->expr": bdd_to_expr(nf),
    }


def test_every_translation_is_kernel_verified(exprs6):
    for e in exprs6:
        for name, art in all_translations(e).items():
            v = kernel.check({"relation": "extensional", "vars": VARS6, "left": e, "right": art})
            assert v.ok, (name, v.counterexample)


def test_main_interpreters_agree_with_kernel_interpreters(exprs6):
    """Two independent implementations of each substrate's semantics."""
    for e in exprs6[:50]:
        for art in all_translations(e).values():
            for env in assignments(VARS6):
                assert evaluate(art, env) == kernel.evaluate(art, env)


def test_composition_of_certified_steps():
    """Charter §7.3 in miniature: expr -> nf -> circuit -> expr, each step
    checked; the end-to-end claim is then checked directly as well. For
    the extensional relation on a fixed domain, transitivity makes the
    end-to-end check redundant -- we run it anyway as a guard."""
    e = {"kind": "expr", "body": ["ite", ["var", "a"], ["xor", ["var", "b"], ["var", "c"]], ["var", "d"]]}
    steps = [e]
    steps.append(normal_form(steps[-1], VARS6))
    steps.append(bdd_to_circuit(steps[-1], VARS6))
    steps.append(circuit_to_expr(steps[-1]))
    for a, b in zip(steps, steps[1:]):
        assert kernel.check({"relation": "extensional", "vars": VARS6, "left": a, "right": b}).ok
    assert kernel.check({"relation": "extensional", "vars": VARS6, "left": steps[0], "right": steps[-1]}).ok


def test_task_relation_does_not_compose_across_different_care_sets():
    """Counterexample: A ≡_T1 B and B ≡_T2 C does not give A ≡_T C for any
    useful T unless the care sets are related. Composition needs matching
    contracts (charter §7.3)."""
    V = ["x", "y"]
    A = {"kind": "expr", "body": ["const", 0]}
    B = {"kind": "expr", "body": ["var", "x"]}
    C = {"kind": "expr", "body": ["const", 1]}
    care1 = {"kind": "expr", "body": ["not", ["var", "x"]]}  # x = 0
    care2 = {"kind": "expr", "body": ["var", "x"]}           # x = 1
    assert kernel.check({"relation": "task", "vars": V, "left": A, "right": B, "care": care1}).ok
    assert kernel.check({"relation": "task", "vars": V, "left": B, "right": C, "care": care2}).ok
    for care in (care1, care2):
        assert not kernel.check({"relation": "task", "vars": V, "left": A, "right": C, "care": care}).ok
