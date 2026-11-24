"""Exact algebraic checks & schema verification for Master Principle Grand Closure."""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "master_principle_grand_closure_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "master_principle_grand_closure.json"


def test_grand_closure_formal_files_present_and_sorry_free():
    required = [
        ROOT / "proofs" / "lean" / "StochasticCausalCovariance.lean",
        ROOT / "proofs" / "lean" / "AuditStochasticCausalCovariance.lean",
        ROOT / "proofs" / "lean-mathlib" / "MasterPrincipleGrandClosure.lean",
        ROOT / "proofs" / "lean-mathlib" / "AuditMasterPrincipleGrandClosure.lean",
        ROOT / "proofs" / "cubical" / "src" / "Semplex" / "Cubical" / "HigherHornCoherence.agda",
    ]
    for path in required:
        assert path.exists(), f"Missing formal artifact: {path}"
        text = path.read_text(encoding="utf-8")
        assert "sorry" not in text.lower(), f"Found sorry in {path}"

    audit_text = (ROOT / "proofs" / "lean" / "AuditStochasticCausalCovariance.lean").read_text(
        encoding="utf-8"
    )
    assert audit_text.count("#print axioms") == 12

    mathlib_audit = (ROOT / "proofs" / "lean-mathlib" / "AuditMasterPrincipleGrandClosure.lean").read_text(
        encoding="utf-8"
    )
    assert mathlib_audit.count("#print axioms") == 28


def test_exact_n4_walsh_orthogonality_and_parity_kernel():
    """Exact integer check of n=4 Walsh orthogonality & extremal parity kernel."""
    n = 4
    N = 1 << n

    def pop_parity(bits: int) -> int:
        return -1 if (bits.bit_count() & 1) else 1

    # Character orthogonality across all 2^4 subsets
    for S in range(N):
        for T in range(N):
            inner = sum(pop_parity(x & S) * pop_parity(x & T) for x in range(N))
            assert inner == (N if S == T else 0)

    # Extremal even vs odd parity measures
    even_w = [1 if pop_parity(x) == 1 else 0 for x in range(N)]
    odd_w = [1 if pop_parity(x) == -1 else 0 for x in range(N)]
    for T in range(N - 1):
        hat_even = sum(even_w[x] * pop_parity(x & T) for x in range(N))
        hat_odd = sum(odd_w[x] * pop_parity(x & T) for x in range(N))
        assert hat_even == hat_odd
    full_mask = N - 1
    assert sum(even_w[x] * pop_parity(x & full_mask) for x in range(N)) == N // 2
    assert sum(odd_w[x] * pop_parity(x & full_mask) for x in range(N)) == -(N // 2)


def test_exact_zerovln_prop2_pythagorean_rational():
    """Exact Fraction verification of ZeroVLN Proposition 2 orthogonal decomposition."""
    g = [Fraction(2), Fraction(-3), Fraction(1), Fraction(4)]
    delta_sft = [Fraction(1, 2), Fraction(-1, 3), Fraction(3, 5), Fraction(1, 4)]
    g_norm2 = sum(gi * gi for gi in g)
    gain = sum(gi * di for gi, di in zip(g, delta_sft))
    delta_ret = [(gain / g_norm2) * gi for gi in g]
    w = [di - ri for di, ri in zip(delta_sft, delta_ret)]

    assert sum(gi * wi for gi, wi in zip(g, w)) == Fraction(0)
    lhs = sum(di * di for di in delta_sft)
    rhs = (gain * gain) / g_norm2 + sum(wi * wi for wi in w)
    assert lhs == rhs
    assert sum(ri * ri for ri in delta_ret) <= lhs


def test_rift_threshold_equivalence_exact():
    """Verify exact equivalence of RIFT rare-rule score vs prior-gap threshold."""
    n_h, n_l = 200, 2
    for tau in (0.0, 0.5, 1.0, 2.0):
        for E_l in (0.1, 1.5, 8.0):
            for E_h in (0.2, 6.0, 15.0):
                score_l = E_l - tau * math.log(n_l)
                score_h = E_h - tau * math.log(n_h)
                lhs = score_l < score_h
                rhs = (E_h - E_l) > tau * math.log(n_h / n_l)
                assert lhs == rhs


def test_grand_closure_results_schema_and_pre_registered_hypotheses():
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))
    res = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    assert res["experiment"] == preds["experiment"]
    assert res["seeds"] == preds["seeds"]
    for hk in ("HGC.1", "HGC.2", "HGC.3", "HGC.4", "HGC.5"):
        assert hk in preds["hypotheses"]
        assert hk in res["verdicts"]
    assert len(res["per_seed"]) == len(preds["seeds"])
