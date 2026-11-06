import ast
import pathlib
import sys

import pytest

from cerp import kernel
from cerp.kernel import KernelError, Verdict

X = {"kind": "expr", "body": ["var", "x"]}
Y = {"kind": "expr", "body": ["var", "y"]}
X_AND_Y = {"kind": "expr", "body": ["and", ["var", "x"], ["var", "y"]]}
Y_AND_X = {"kind": "expr", "body": ["and", ["var", "y"], ["var", "x"]]}
X_OR_Y = {"kind": "expr", "body": ["or", ["var", "x"], ["var", "y"]]}


def test_equivalence_and_counterexample():
    ok = kernel.check({"relation": "extensional", "vars": ["x", "y"], "left": X_AND_Y, "right": Y_AND_X})
    assert ok.ok and ok.points_checked == 4
    bad = kernel.check({"relation": "extensional", "vars": ["x", "y"], "left": X_AND_Y, "right": X_OR_Y})
    assert not bad.ok
    cx = bad.counterexample
    assert kernel.evaluate(X_AND_Y, cx) != kernel.evaluate(X_OR_Y, cx)


def test_task_relation_only_checks_care_points():
    care = {"kind": "expr", "body": ["not", ["xor", ["var", "x"], ["var", "y"]]]}  # x == y
    v = kernel.check({"relation": "task", "vars": ["x", "y"], "left": X_AND_Y, "right": X_OR_Y, "care": care})
    assert v.ok and v.points_checked == 2
    v = kernel.check({"relation": "task", "vars": ["x", "y"], "left": X, "right": Y, "care": care})
    assert v.ok


def test_verdicts_cannot_be_forged():
    with pytest.raises(KernelError):
        Verdict(True, "extensional", ("x",), 2, None, kernel.KERNEL_VERSION)


@pytest.mark.parametrize("claim", [
    {"relation": "magic", "vars": ["x"], "left": X, "right": X},
    {"relation": "extensional", "vars": ["x", "x"], "left": X, "right": X},
    {"relation": "task", "vars": ["x"], "left": X, "right": X},  # missing care
    {"relation": "extensional", "vars": ["x"], "left": {"kind": "expr", "body": ["nand", X["body"], X["body"]]}, "right": X},
    {"relation": "extensional", "vars": [f"v{i}" for i in range(kernel.MAX_VARS + 1)], "left": X, "right": X},
])
def test_malformed_claims_raise_rather_than_verdict(claim):
    with pytest.raises(KernelError):
        kernel.check(claim)


def test_circuit_must_be_topologically_ordered():
    c = {"kind": "circuit", "body": {"inputs": ["x"], "output": "g1",
         "gates": [{"id": "g1", "op": "not", "in": ["g0"]}, {"id": "g0", "op": "not", "in": ["x"]}]}}
    with pytest.raises(KernelError):
        kernel.evaluate(c, {"x": 0})


def test_insufficiency_certificate():
    care = {"kind": "expr", "body": ["const", 1]}
    claim = {"vars": ["x", "y"], "f": X_AND_Y, "care": care, "subset": ["x"],
             "x": {"x": 1, "y": 0}, "y": {"x": 1, "y": 1}}
    assert kernel.check_insufficiency(claim).ok
    claim["y"] = {"x": 0, "y": 0}  # does not agree on subset {x}
    assert not kernel.check_insufficiency(claim).ok


def test_kernel_is_independent_of_the_rest_of_cerp():
    """The trusted base must not grow silently: stdlib imports only."""
    src = pathlib.Path(kernel.__file__).read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, "relative import in kernel"
            mod = node.module
        elif isinstance(node, ast.Import):
            mod = node.names[0].name
        else:
            continue
        root = mod.split(".")[0]
        assert root == "__future__" or root in sys.stdlib_module_names, f"non-stdlib import {mod}"
        assert root != "cerp"
