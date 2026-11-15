"""Spike 06: Lean-checked claims. Skipped unless CERP_LEAN points to Lean 4."""

import pytest

from cerp import kernel
from cerp.bdd import normal_form
from cerp.benchmarks import carry_prefix, carry_ripple
from cerp.demo import ALARM, SENSORS_AGREE
from cerp.ledger import Ledger, LedgerError, Method, Status, compare
from cerp.sat import prove_equivalence
from cerp.translate import bdd_to_expr

# Seconds allowed per Lean file. Bounds.lean takes about 170 s on a fast host and about 600 s on a
# memory-constrained one; raise SEMPLEX_LEAN_TIMEOUT there instead of editing this test.
import os as _os
LEAN_FILE_TIMEOUT = float(_os.environ.get("SEMPLEX_LEAN_TIMEOUT", "600"))

lean_bridge = pytest.importorskip("cerp.lean_bridge")
pytestmark = [pytest.mark.lean, pytest.mark.slow]
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


def test_proof_files_compile_and_use_only_standard_axioms(tmp_path):
    """Cerp.lean and Theory.lean keep checking; every audited theorem uses at most
    propext / Quot.sound / Classical.choice."""
    import re
    import subprocess
    lean = lean_bridge.lean_binary()
    d = lean_bridge.LEAN_DIR
    for f in ("Cerp", "Theory", "Bounds"):
        r = subprocess.run([lean, f"--root={d}", "-o", str(tmp_path / f"{f}.olean"), str(d / f"{f}.lean")],
                           cwd=d, capture_output=True, text=True, timeout=LEAN_FILE_TIMEOUT)
        assert r.returncode == 0, r.stdout + r.stderr
    for audit in ("Audit.lean", "AuditTheory.lean", "AuditBounds.lean"):
        r = subprocess.run([lean, str(d / audit)], cwd=d, capture_output=True, text=True, timeout=LEAN_FILE_TIMEOUT,
                           env={**__import__("os").environ, "LEAN_PATH": str(tmp_path)})
        assert r.returncode == 0, r.stdout + r.stderr
        for m in re.finditer(r"depends on axioms: \[([^\]]*)\]", r.stdout):
            assert set(a.strip() for a in m.group(1).split(",")) <= {"propext", "Quot.sound", "Classical.choice"}
        assert "sorryAx" not in r.stdout


def test_tseitin_miter_equiv_proved_by_lean_kernel():
    vs = ["a", "b"]
    e1 = {"kind": "expr", "body": ["and", ["var", "a"], ["var", "b"]]}
    e2 = {"kind": "expr", "body": ["not", ["or", ["not", ["var", "a"]], ["not", ["var", "b"]]]]}
    _, lemmas, _ = prove_equivalence({"vars": vs, "left": e1, "right": e2})
    r, _ = lean_bridge.verify_expr_equiv_tseitin(e1, e2, vs, lemmas, name="t_tseitin_demorgan")
    assert r.ok and set(r.axioms) <= {"propext", "Quot.sound", "Classical.choice"}


def test_lrat_miter_equiv_and_ur_compiler_certify_lean():
    from cerp import sat, ur_compiler
    vs = ["a", "b", "c"]
    e1 = {"kind": "expr", "body": ["xor", ["var", "a"], ["xor", ["var", "b"], ["var", "c"]]]}
    e2 = {"kind": "expr", "body": ["xor", ["xor", ["var", "a"], ["var", "b"]], ["var", "c"]]}
    status, lrat_steps, _ = sat.prove_equivalence_lrat({"vars": vs, "left": e1, "right": e2})
    assert status == "unsat"
    r, _ = lean_bridge.verify_expr_equiv_lrat(e1, e2, vs, lrat_steps, name="t_lrat_xor")
    assert r.ok and set(r.axioms) <= {"propext", "Quot.sound", "Classical.choice"}

    out = ur_compiler.compile_unified({
        "kind": "f0",
        "vars": vs,
        "fn": lambda env: env["a"] ^ env["b"] ^ env["c"],
        "name": "xor3_cert",
        "certify_lean": True,
    })
    assert out["validation_errors"] == []
    assert out["lean_cert"] is not None and out["lean_cert"]["ok"] is True
    assert out["lean_cert"].get("net_ok") is True


def test_tnet_lean_exhaustive_and_lrat_equiv():
    from cerp import sat, ur_compiler
    vs = ["x0", "x1", "x2", "x3"]
    comp = ur_compiler.compile_profile_factored(vs, lambda e: e["x0"] ^ e["x1"] ^ e["x2"] ^ e["x3"])
    net = comp["threshold_net"]
    assert net is not None

    r_ex, _ = lean_bridge.verify_threshold_net_equiv(net, comp["expr"], vs, name="t_tnet_xor4_ex")
    assert r_ex.ok and set(r_ex.axioms) <= {"propext", "Quot.sound", "Classical.choice"}

    status, lrat_steps, _ = sat.prove_tnet_equivalence_lrat(net, comp["expr"], vs)
    assert status == "unsat"
    r_lrat, _ = lean_bridge.verify_threshold_net_equiv(net, comp["expr"], vs, lrat_steps=lrat_steps, name="t_tnet_xor4_lrat", native=False)
    assert r_lrat.ok and set(r_lrat.axioms) <= set(lean_bridge.ALLOWED_AXIOMS)

    bad_net = {"inputs": list(net["inputs"]), "nodes": [dict(nd) for nd in net["nodes"]], "output": net["output"]}
    bad_net["nodes"][-1]["t"] = int(bad_net["nodes"][-1]["t"]) + 10
    bad_status, bad_ce, _ = sat.prove_tnet_equivalence_lrat(bad_net, comp["expr"], vs)
    assert bad_status == "sat" and isinstance(bad_ce, dict)


def test_tnet_lean_n6_two_hidden_layer_kernel_decide():
    from cerp import sat

    vs = [f"x{i}" for i in range(6)]
    _not = lambda a: ["not", a]
    _and = lambda a, b: ["and", a, b]
    _or = lambda a, b: ["or", a, b]
    _xor = lambda a, b: ["xor", a, b]
    _iff = lambda a, b: _not(_xor(a, b))

    def _gt3(as_, bs_):
        eq0 = _iff(as_[0], bs_[0])
        eq1 = _iff(as_[1], bs_[1])
        return _or(
            _and(as_[0], _not(bs_[0])),
            _or(_and(eq0, _and(as_[1], _not(bs_[1]))), _and(eq0, _and(eq1, _and(as_[2], _not(bs_[2]))))),
        )

    a3 = [["var", "x0"], ["var", "x1"], ["var", "x2"]]
    b3 = [["var", "x3"], ["var", "x4"], ["var", "x5"]]
    expr = {"kind": "expr", "body": _xor(_gt3(a3, b3), _gt3(a3, [_not(x) for x in b3]))}
    net = {
        "inputs": vs,
        "nodes": [
            {"id": "h0", "in": vs, "w": [4, 2, 1, -4, -2, -1], "t": 1},
            {"id": "h1", "in": vs, "w": [4, 2, 1, 4, 2, 1], "t": 8},
            {"id": "g0", "in": ["h0", "h1"], "w": [1, 1], "t": 1},
            {"id": "g1", "in": ["h0", "h1"], "w": [1, 1], "t": 2},
            {"id": "out", "in": ["g0", "g1"], "w": [1, -1], "t": 1},
        ],
        "output": "out",
    }
    status, lrat_steps, _ = sat.prove_tnet_equivalence_lrat(net, expr, vs, pb=True)
    assert status == "unsat"
    r, _ = lean_bridge.verify_threshold_net_equiv(
        net, expr, vs, lrat_steps=lrat_steps, name="t_tnet_n6_2h_cmp_xor", native=False, pb=True
    )
    assert r.ok and set(r.axioms) <= set(lean_bridge.ALLOWED_AXIOMS)


def test_tnet_lean_n8_one_hidden_layer_kernel_decide():
    from cerp import sat

    vs = [f"x{i}" for i in range(8)]
    _iff = lambda a, b: ["not", ["xor", a, b]]
    expr = {
        "kind": "expr",
        "body": [
            "and",
            ["and", _iff(["var", "x0"], ["var", "x4"]), _iff(["var", "x1"], ["var", "x5"])],
            ["and", _iff(["var", "x2"], ["var", "x6"]), _iff(["var", "x3"], ["var", "x7"])],
        ],
    }
    net = {
        "inputs": vs,
        "nodes": [
            {"id": "h0", "in": vs, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 0},
            {"id": "h1", "in": vs, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 1},
            {"id": "out", "in": ["h0", "h1"], "w": [1, -1], "t": 1},
        ],
        "output": "out",
    }
    status, lrat_steps, _ = sat.prove_tnet_equivalence_lrat(net, expr, vs, pb=True)
    assert status == "unsat"
    r, _ = lean_bridge.verify_threshold_net_equiv(
        net, expr, vs, lrat_steps=lrat_steps, name="t_tnet_n8_1h_eq4", native=False, pb=True
    )
    assert r.ok and set(r.axioms) <= set(lean_bridge.ALLOWED_AXIOMS)
