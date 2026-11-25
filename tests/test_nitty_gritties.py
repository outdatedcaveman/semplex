"""Unit and verification tests for experiments/nitty_gritties_probe.py (HNG.1-HNG.4)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

import nitty_gritties_probe as ngp  # noqa: E402


def _reject_nonfinite(val: str) -> None:
    raise ValueError(f"Non-finite JSON constant not allowed: {val}")


def test_predictions_and_results_strict_json_consistency() -> None:
    pred_path = ROOT / "experiments" / "results" / "nitty_gritties_predictions.json"
    res_path = ROOT / "experiments" / "results" / "nitty_gritties_results.json"
    assert pred_path.is_file()
    assert res_path.is_file()

    preds = json.loads(pred_path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)
    results = json.loads(res_path.read_text(encoding="utf-8"), parse_constant=_reject_nonfinite)

    assert results["suite"] == preds["suite"] == "master_principle_nitty_gritties"
    hyps = results["hypotheses"]
    assert set(hyps.keys()) == {"HNG.1", "HNG.2", "HNG.3", "HNG.4"}

    expected_held = 0
    for key in ("HNG.1", "HNG.2", "HNG.3", "HNG.4"):
        h = hyps[key]
        assert h["hypothesis"] == key
        assert isinstance(h["checks"], dict) and len(h["checks"]) > 0
        expected_status = "HELD" if all(h["checks"].values()) else "BROKEN"
        assert h["status"] == expected_status
        if h["status"] == "HELD":
            expected_held += 1
    assert results["held_count"] == expected_held
    assert results["total_count"] == 4


def test_quantize_tensor_int3_symmetric_levels() -> None:
    rng = torch.Generator().manual_seed(42)
    w = torch.randn((8, 16), generator=rng, dtype=torch.float32)
    qw = ngp.quantize_tensor_int3(w)
    assert qw.shape == w.shape
    assert qw.dtype == w.dtype
    assert torch.isfinite(qw).all()

    amax = w.abs().amax(dim=1, keepdim=True).clamp(min=1e-8)
    scale = amax / 3.0
    levels = torch.round(qw / scale)
    assert torch.allclose(qw, levels * scale, atol=1e-5)
    assert (levels.abs() <= 3.0).all()

    w16 = w.half()
    qw16 = ngp.quantize_tensor_int3(w16)
    assert qw16.dtype == torch.float16
    assert torch.isfinite(qw16).all()


def test_cyclic_bispectrum_invariance_and_phase_separation() -> None:
    rng = np.random.default_rng(123)
    x = rng.normal(0.0, 1.0, size=16)
    b0 = ngp.cyclic_bispectrum(x)
    for shift in range(16):
        bs = ngp.cyclic_bispectrum(np.roll(x, shift))
        assert np.max(np.abs(bs - b0)) <= 1e-11

    t = 2.0 * math.pi * np.arange(16) / 16.0
    s_plus = np.cos(t) + np.cos(2.0 * t) + np.cos(3.0 * t)
    s_minus = np.cos(t) + np.cos(2.0 * t) + np.cos(3.0 * t + math.pi / 2.0)
    ps_diff = np.max(np.abs(np.abs(np.fft.fft(s_plus)) ** 2 - np.abs(np.fft.fft(s_minus)) ** 2))
    assert ps_diff <= 1e-11
    assert np.linalg.norm(ngp.cyclic_bispectrum(s_plus) - ngp.cyclic_bispectrum(s_minus)) > 1e-2


def test_deterministic_hng2_hng3_hng4_probes() -> None:
    preds = json.loads(
        (ROOT / "experiments" / "results" / "nitty_gritties_predictions.json").read_text(encoding="utf-8")
    )
    h2 = ngp.run_hng2_measurable_dobrushin(preds)
    h3 = ngp.run_hng3_cech_nerve_and_pou(preds)
    h4 = ngp.run_hng4_bispectrum_symmetrization(preds)

    assert h2["status"] == "HELD"
    assert h2["max_contraction_violation"] <= 1e-10
    assert h2["max_comp_violation"] <= 1e-10
    assert h2["max_horizon_violation"] <= 1e-10

    assert h3["status"] == "HELD"
    assert h3["split_descent_exact"] is True
    assert h3["pou_abs_err"] <= 1e-12
    assert h3["raw_overlap_err"] >= 0.5
    assert h3["c4_global_solutions"] == 0
    assert h3["c4_min_monodromy"] == 2

    assert h4["status"] == "HELD"
    assert h4["sym_orbit_variance_max"] <= 1e-12
    assert h4["sym_mse_ratio"] <= 0.85
