"""Fast unit, structural, and strict-JSON tests for Master Principle Final Synthesis (HFS.1-HFS.3)."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np

from experiments import master_principle_final_synthesis_probe as probe

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "master_principle_final_synthesis_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "master_principle_final_synthesis_results.json"


def _strict_parse_constant(tok: str) -> float:
    raise ValueError(f"Non-standard JSON numeric constant disallowed: {tok!r}")


def _assert_all_finite(obj: object, path: str = "root") -> None:
    if isinstance(obj, float):
        assert math.isfinite(obj), f"Non-finite float at {path}: {obj!r}"
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _assert_all_finite(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, v in enumerate(obj):
            _assert_all_finite(v, f"{path}[{idx}]")


def test_final_closure_formal_artifacts_present_sorry_postulate_and_hole_free() -> None:
    agda_path = ROOT / "proofs" / "cubical" / "src" / "Semplex" / "Cubical" / "SemanticUnivalence.agda"
    core_lean = ROOT / "proofs" / "lean" / "ContextualRingDescent.lean"
    core_audit = ROOT / "proofs" / "lean" / "AuditContextualRingDescent.lean"
    math_lean = ROOT / "proofs" / "lean-mathlib" / "MasterPrincipleUniversalClosure.lean"
    math_audit = ROOT / "proofs" / "lean-mathlib" / "AuditMasterPrincipleUniversalClosure.lean"

    for path in (agda_path, core_lean, core_audit, math_lean, math_audit):
        assert path.exists(), f"Missing formal artifact: {path}"
        text = path.read_text(encoding="utf-8")
        stripped = re.sub(r"/-[\s\S]*?-/", "", text)
        stripped = re.sub(r"\{-[\s\S]*?-\}", "", stripped)
        stripped = re.sub(r"--.*$", "", stripped, flags=re.MULTILINE)
        assert re.search(r"\bsorry\b", stripped) is None, f"Found sorry in {path}"
        assert re.search(r"\badmit\b", stripped) is None, f"Found admit in {path}"
        assert "{!!" not in stripped and "{!" not in stripped, f"Found Agda hole in {path}"

    agda_stripped = re.sub(r"\{-[\s\S]*?-\}", "", agda_path.read_text(encoding="utf-8"))
    agda_stripped = re.sub(r"--.*$", "", agda_stripped, flags=re.MULTILINE)
    assert re.search(r"\bpostulate\b", agda_stripped) is None

    assert core_audit.read_text(encoding="utf-8").count("#print axioms") == 23
    assert math_audit.read_text(encoding="utf-8").count("#print axioms") == 12


def test_predictions_and_results_strict_json_and_verdicts() -> None:
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    res_doc = json.loads(OUT_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    _assert_all_finite(preds, "predictions")
    _assert_all_finite(res_doc, "results")

    assert res_doc["summary"] == {"HFS.1": "BROKEN", "HFS.2": "HELD", "HFS.3": "HELD"}

    r1 = res_doc["results"]["HFS.1"]
    p1 = preds["HFS.1"]
    assert r1["n_cal_pairs"] == p1["num_cal"] == 10
    assert r1["n_eval_pairs"] == p1["num_eval"] == 24
    expected_hfs1 = (
        r1["fp32_eval_acc"] >= p1["fp32_eval_acc_min"]
        and r1["all_int3_flip_rate"] >= p1["all_int3_flip_rate_min"]
        and r1["spearman_gamma_vs_margin_shift"] >= p1["spearman_gamma_vs_margin_shift_min"]
        and r1["spearman_gamma_vs_flip"] >= p1["spearman_gamma_vs_flip_min"]
        and r1["protection_flip_reduction"] >= p1["protection_flip_reduction_min"]
    )
    assert expected_hfs1 is False
    assert r1["verdict"] == "BROKEN"
    # Verify exact scientific breakdown: rank correlations & flip trigger passed, baseline acc & 1.5x reduction failed
    assert r1["all_int3_flip_rate"] >= p1["all_int3_flip_rate_min"]
    assert r1["spearman_gamma_vs_margin_shift"] >= p1["spearman_gamma_vs_margin_shift_min"]
    assert r1["spearman_gamma_vs_flip"] >= p1["spearman_gamma_vs_flip_min"]
    assert r1["spearman_gamma_vs_flip"] > r1["spearman_frob_vs_flip"]
    assert r1["fp32_eval_acc"] < p1["fp32_eval_acc_min"]
    assert r1["protection_flip_reduction"] < p1["protection_flip_reduction_min"]

    r2 = res_doc["results"]["HFS.2"]
    p2 = preds["HFS.2"]
    assert r2["num_chains"] == p2["num_chains"] == 10
    assert r2["horizon"] == p2["horizon"] == 15
    assert r2["max_violation"] <= p2["max_violation_le"]
    assert r2["max_t15_contraction_vs_linear_ratio"] <= p2["max_t15_contraction_vs_linear_ratio_le"]
    assert r2["verdict"] == "HELD"

    r3 = res_doc["results"]["HFS.3"]
    assert r3["verdict"] == "HELD"


def test_hfs2_dobrushin_tv_contraction_unit() -> None:
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    out = probe.run_hfs2_dobrushin_markov(preds)
    assert out["verdict"] == "HELD"
    assert out["max_violation"] <= 1e-12
    assert len(out["chains"]) == 10

    # Adversarial finite-state TV metric axioms and Dobrushin step check
    mu = np.array([0.7, 0.2, 0.05, 0.05], dtype=np.float64)
    nu = np.array([0.1, 0.1, 0.5, 0.3], dtype=np.float64)
    xi = np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float64)
    assert probe.tv_dist(mu, mu) == 0.0
    assert abs(probe.tv_dist(mu, nu) - probe.tv_dist(nu, mu)) < 1e-15
    assert probe.tv_dist(mu, xi) <= probe.tv_dist(mu, nu) + probe.tv_dist(nu, xi) + 1e-15

    P = np.array(
        [
            [0.6, 0.2, 0.1, 0.1],
            [0.5, 0.3, 0.1, 0.1],
            [0.1, 0.1, 0.5, 0.3],
            [0.1, 0.1, 0.4, 0.4],
        ],
        dtype=np.float64,
    )
    alpha = probe.dobrushin_coeff(P)
    assert probe.tv_dist(mu @ P, nu @ P) <= alpha * probe.tv_dist(mu, nu) + 1e-15


def test_hfs3_contextual_ring_descent_witness_unit() -> None:
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    out = probe.run_hfs3_contextual_ring_descent(preds)
    assert out["verdict"] == "HELD"
    assert out["sparse_abc_sequences_checked"] == 126
    assert out["sparse_abc_violations"] == 0
    assert out["sparse_abc_direct_ac_adjacent"] is False
    assert out["sparse_abc_connected"] is True
    assert out["holonomy_strict_sections"] == 1
    assert out["holonomy_groupoid_sections"] == 2
    assert out["holonomy_groupoid_aut_closed"] is True
    assert out["holonomy_coset0_edge_sections"] == 2
    assert out["holonomy_coset0_global_sections"] == 0
    assert out["holonomy_coset0_min_monodromy"] == 2
    assert out["hallucination_internally_iso"] is True
    assert out["hallucination_grounded"] is False
    assert out["grounded_grounded"] is True
