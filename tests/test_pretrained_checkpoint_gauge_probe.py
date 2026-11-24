"""Unit, schema, and exact algebraic checks for Step 2-5 Grand Closure deliverables."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "pretrained_checkpoint_gauge_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "pretrained_checkpoint_gauge_results.json"


def test_continuum_bridge_and_cubical_files_present_and_sorry_free():
    required = [
        ROOT / "proofs" / "lean" / "CausalCovarianceGroupoidBridge.lean",
        ROOT / "proofs" / "lean" / "AuditCausalCovarianceGroupoidBridge.lean",
        ROOT / "proofs" / "lean-mathlib" / "ContinuumKernelCovariance.lean",
        ROOT / "proofs" / "lean-mathlib" / "AuditContinuumKernelCovariance.lean",
        ROOT / "proofs" / "cubical" / "src" / "Semplex" / "Cubical" / "InductiveHigherHorn.agda",
    ]
    for path in required:
        assert path.exists(), f"Missing formal artifact: {path}"
        text = path.read_text(encoding="utf-8")
        assert "sorry" not in text.lower(), f"Found sorry in {path}"
        assert "{!!" not in text and "{!" not in text, f"Found Agda hole in {path}"

    bridge_audit = (ROOT / "proofs" / "lean" / "AuditCausalCovarianceGroupoidBridge.lean").read_text(
        encoding="utf-8"
    )
    assert bridge_audit.count("#print axioms") == 17

    mathlib_audit = (ROOT / "proofs" / "lean-mathlib" / "AuditContinuumKernelCovariance.lean").read_text(
        encoding="utf-8"
    )
    assert mathlib_audit.count("#print axioms") == 19


def test_polish_r2_diffeomorphism_exact_rational_jacobian_and_inverse():
    """Exact Fraction check of phi(x1, x2) = (x1 + (7/20)*x2^3, x2) & det(Dphi) = 1."""
    alpha = Fraction(7, 20)

    def phi(x1: Fraction, x2: Fraction) -> tuple[Fraction, Fraction]:
        return (x1 + alpha * (x2 ** 3), x2)

    def phi_inv(y1: Fraction, y2: Fraction) -> tuple[Fraction, Fraction]:
        return (y1 - alpha * (y2 ** 3), y2)

    for n1 in range(-2, 3):
        for n2 in range(-2, 3):
            x1 = Fraction(n1, 3)
            x2 = Fraction(n2, 2)
            y1, y2 = phi(x1, x2)
            rx1, rx2 = phi_inv(y1, y2)
            assert (rx1, rx2) == (x1, x2)
            # Upper triangular Jacobian [[1, 3*alpha*x2^2], [0, 1]] has determinant exactly 1
            j11, j12, j21, j22 = Fraction(1), 3 * alpha * (x2 ** 2), Fraction(0), Fraction(1)
            det = j11 * j22 - j12 * j21
            assert det == Fraction(1)


def test_pretrained_checkpoint_probe_schema_and_honest_verdicts():
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))
    res = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    assert res["experiment"] == preds["experiment"]
    for hk in ("HP.1", "HP.2", "HP.3", "HP.4", "HP.5"):
        assert hk in preds["hypotheses"]
        assert hk in res["verdicts"]
        assert res["verdicts"][hk] in ("HELD", "BROKEN", "NEITHER")
        assert hk in res["results"]

    # Check exact structural invariants recorded regardless of model-scale threshold verdicts
    assert res["results"]["HP.1"]["temp_recal_flips"] == 0
    assert res["results"]["HP.2"]["temp_recal_flips"] == 0
    assert res["results"]["HP.3"]["frozen_taskA_drop"] == 0.0
    assert res["results"]["HP.3"]["prop2_pyth_rel_err"] < 1e-12
    assert res["results"]["HP.3"]["prop2_orth_cos_abs"] < 1e-12
    assert res["results"]["HP.4"]["frozen_taskA_drop"] == 0.0
    assert res["results"]["HP.4"]["prop2_pyth_rel_err"] < 1e-12
    assert res["results"]["HP.4"]["prop2_orth_cos_abs"] < 1e-12
    assert res["verdicts"]["HP.4"] == "HELD"
    assert res["verdicts"]["HP.5"] == "HELD"
