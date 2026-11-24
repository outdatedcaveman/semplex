"""Fast unit, differential, and strict-JSON checks for Quantitative Gauge Stability (HQS.1-HQS.5)."""
from __future__ import annotations

import itertools
import json
import math
import re
from pathlib import Path

import numpy as np

from experiments import quantitative_gauge_stability_probe as probe

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "quantitative_gauge_stability_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "quantitative_gauge_stability_results.json"


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


def _assert_group_axioms(table: list[list[int]]) -> None:
    n = len(table)
    # Identity at index 0
    for x in range(n):
        assert table[0][x] == x
        assert table[x][0] == x
    # Closure + Associativity + Inverses
    for x in range(n):
        inv_hits = [y for y in range(n) if table[x][y] == 0 and table[y][x] == 0]
        assert len(inv_hits) == 1
        for y in range(n):
            assert 0 <= table[x][y] < n
            for z in range(n):
                assert table[table[x][y]][z] == table[x][table[y][z]]


def test_obstruction_and_stability_formal_files_present_and_sorry_free():
    required = [
        ROOT / "proofs" / "lean" / "ObstructionExactSequence.lean",
        ROOT / "proofs" / "lean" / "AuditObstructionExactSequence.lean",
        ROOT / "proofs" / "cubical" / "src" / "Semplex" / "Cubical" / "FiberObstructionSequence.agda",
        ROOT / "proofs" / "lean-mathlib" / "QuantitativeGaugeStability.lean",
        ROOT / "proofs" / "lean-mathlib" / "AuditQuantitativeGaugeStability.lean",
    ]
    for path in required:
        assert path.exists(), f"Missing formal artifact: {path}"
        text = path.read_text(encoding="utf-8")
        stripped = re.sub(r"/-[\s\S]*?-/", "", text)
        stripped = re.sub(r"\{-[\s\S]*?-\}", "", stripped)
        stripped = re.sub(r"--.*$", "", stripped, flags=re.MULTILINE)
        assert re.search(r"\bsorry\b", stripped) is None, f"Found sorry in {path}"
        assert re.search(r"\badmit\b", stripped) is None, f"Found admit in {path}"
        assert "{!!" not in stripped and "{!" not in stripped, f"Found Agda hole in {path}"

    core_audit = (ROOT / "proofs" / "lean" / "AuditObstructionExactSequence.lean").read_text(
        encoding="utf-8"
    )
    assert core_audit.count("#print axioms") == 22

    mathlib_audit = (
        ROOT / "proofs" / "lean-mathlib" / "AuditQuantitativeGaugeStability.lean"
    ).read_text(encoding="utf-8")
    assert mathlib_audit.count("#print axioms") == 17


def test_q8_vs_c2cubed_tables_monolith_and_non_dirac_hmm_invariance():
    q8_names, q8_table = probe.build_q8_table()
    c2_names, c2_table = probe.build_c2cubed_table()
    _assert_group_axioms(q8_table)
    _assert_group_axioms(c2_table)

    # Q8 is strictly nonabelian (i*j = k != -k = j*i), C2^3 is abelian
    i_idx, j_idx = q8_names.index("i"), q8_names.index("j")
    assert q8_table[i_idx][j_idx] != q8_table[j_idx][i_idx]
    assert all(c2_table[a][b] == c2_table[b][a] for a in range(8) for b in range(8))

    # Subgroup intersections match HQS.1 theorem (Q8 monolith {1, -1} vs C2^3 trivial {000})
    q8_subs = probe.proper_nontrivial_subgroups(q8_table)
    c2_subs = probe.proper_nontrivial_subgroups(c2_table)
    assert len(q8_subs) == 4
    assert len(c2_subs) == 14

    q8_inter = set(range(8))
    for sg in q8_subs:
        q8_inter &= set(sg)
    assert [q8_names[idx] for idx in sorted(q8_inter)] == ["1", "-1"]

    c2_inter = set(range(8))
    for sg in c2_subs:
        c2_inter &= set(sg)
    assert [c2_names[idx] for idx in sorted(c2_inter)] == ["000"]

    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))["predictions"]
    hqs1 = probe.run_hqs1_monolith_hmm(preds)
    assert hqs1["verdict"] == "HELD"
    assert hqs1["q8_max_row_prob"] < 1.0
    assert hqs1["c2cubed_max_row_prob"] < 1.0
    assert hqs1["q8_profile_tv_max"] <= 1e-12
    assert hqs1["c2cubed_profile_tv_max"] <= 1e-12


def test_specker_c4_triangle_local_sections_and_monodromy():
    preds = json.loads(PRED_PATH.read_text(encoding="utf-8"))["predictions"]
    hqs2 = probe.run_hqs2_specker_c4(preds)
    assert hqs2["verdict"] == "HELD"
    assert hqs2["unanchored_global_solutions"] == 2
    assert hqs2["coset0_each_edge_solutions"] == 2
    assert hqs2["coset0_global_solutions"] == 0
    assert hqs2["coset0_min_cycle_monodromy"] == 2
    assert hqs2["coset1_global_solutions"] == 2
    assert hqs2["coset1_trivial_monodromy_count"] == 8

    # Cross-check monodromy directly over all C2 transitions mod 4
    coset0_edges = [(a, b) for a, b in itertools.product((0, 2), repeat=2) if (a + b) % 4 == 2]
    assert set(coset0_edges) == {(0, 2), (2, 0)}
    for e01, e12, e20 in itertools.product(coset0_edges, repeat=3):
        mono = ((e12[0] - e01[1]) + (e20[0] - e12[1]) + (e01[0] - e20[1])) % 4
        assert mono != 0


def test_variable_jacobian_diffeomorphism_and_contraction_horizon():
    xs = np.array(
        [[-1.5, -0.8], [-0.4, 1.1], [0.0, 0.0], [0.9, -1.3], [1.7, 0.6]],
        dtype=np.float64,
    )
    ys = probe.phi_nonunit(xs)
    x_rec, det_j = probe.phi_nonunit_inv(ys)
    assert np.max(np.abs(x_rec - xs)) < 1e-12
    assert float(np.max(det_j) / np.min(det_j)) > 3.0

    # Central finite-difference Jacobian determinant matches analytical 0.6 * cosh(0.6 x1) * exp(0.35 x1)
    eps = 1e-6
    for row_idx in range(xs.shape[0]):
        x = xs[row_idx : row_idx + 1]
        dx1 = np.array([[eps, 0.0]])
        dx2 = np.array([[0.0, eps]])
        col1 = (probe.phi_nonunit(x + dx1) - probe.phi_nonunit(x - dx1))[0] / (2.0 * eps)
        col2 = (probe.phi_nonunit(x + dx2) - probe.phi_nonunit(x - dx2))[0] / (2.0 * eps)
        fd_det = float(col1[0] * col2[1] - col1[1] * col2[0])
        assert abs(fd_det - float(det_j[row_idx])) / abs(float(det_j[row_idx])) < 1e-6

    # Check contraction-horizon inequality Theorem across T = 1..12
    rho, d0, step_delta = 0.55, 0.40, 0.12
    mu1, mu2 = 0.0, d0
    for horizon in range(1, 13):
        mu1 = rho * mu1
        mu2 = rho * mu2 + step_delta
        d_t = abs(mu1 - mu2)
        geom_bound = (rho ** horizon) * d0 + step_delta * (1.0 - (rho ** horizon)) / (1.0 - rho)
        lin_bound = d0 + horizon * step_delta
        assert d_t <= geom_bound + 1e-12
        assert geom_bound <= lin_bound + 1e-12
        assert probe.gaussian_1d_tv(mu1, mu2, 1.0) <= probe.gaussian_1d_tv(0.0, geom_bound, 1.0) + 1e-12


def test_quantitative_gauge_stability_results_strict_json_and_verdict_consistency():
    preds_doc = json.loads(PRED_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    res_doc = json.loads(OUT_PATH.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant)
    _assert_all_finite(preds_doc, "predictions")
    _assert_all_finite(res_doc, "results")

    assert res_doc["experiment"] == preds_doc["experiment"]
    preds = preds_doc["predictions"]
    results = res_doc["results"]
    summary = res_doc["summary"]

    for key in ("HQS.1", "HQS.2", "HQS.3", "HQS.4", "HQS.5"):
        assert key in preds
        assert key in results
        assert summary[key] in ("HELD", "BROKEN")
        assert results[key]["verdict"] == summary[key]

    # Exact consistency between stored fields and computed HELD/BROKEN verdicts
    p1, r1 = preds["HQS.1"], results["HQS.1"]
    assert r1["verdict"] == (
        "HELD"
        if (
            r1["c2cubed_max_row_prob"] < p1["c2cubed_max_row_prob_lt"]
            and r1["q8_max_row_prob"] < p1["q8_max_row_prob_lt"]
            and r1["c2cubed_profile_tv_max"] <= p1["c2cubed_profile_tv_max_le"]
            and r1["q8_profile_tv_max"] <= p1["q8_profile_tv_max_le"]
            and r1["c2cubed_anchors_needed"] == p1["c2cubed_anchors_needed_eq"]
            and r1["c2cubed_final_kernel_size"] == p1["c2cubed_final_kernel_size_eq"]
            and r1["q8_n_proper_nontrivial_subgroups"] == p1["q8_all_proper_subgroups_count_eq"]
            and r1["q8_all_proper_subgroups_kernel_size"] >= p1["q8_all_proper_subgroups_kernel_size_ge"]
        )
        else "BROKEN"
    )

    p2, r2 = preds["HQS.2"], results["HQS.2"]
    assert r2["verdict"] == (
        "HELD"
        if (
            r2["unanchored_global_solutions"] == p2["unanchored_global_solutions_eq"]
            and r2["coset0_each_edge_solutions"] >= p2["coset0_each_edge_solutions_ge"]
            and r2["coset0_global_solutions"] == p2["coset0_global_solutions_eq"]
            and r2["coset0_min_cycle_monodromy"] != p2["coset0_min_cycle_monodromy_ne"]
            and r2["coset1_global_solutions"] == p2["coset1_global_solutions_eq"]
        )
        else "BROKEN"
    )

    p3, r3 = preds["HQS.3"], results["HQS.3"]
    rho_g = r3["spearman_gamma_vs_flip"]
    assert r3["verdict"] == (
        "HELD"
        if (
            r3["fp32_eval_acc"] >= p3["fp32_eval_acc_min"]
            and r3["all_int4_flip_rate"] >= p3["all_int4_flip_rate_min"]
            and rho_g is not None
            and rho_g >= p3["spearman_gamma_vs_flip_min"]
            and r3["gamma_beats_raw_frob"]
            and r3["protection_flip_reduction"] >= p3["protection_flip_reduction_min"]
        )
        else "BROKEN"
    )

    p4, r4 = preds["HQS.4"], results["HQS.4"]
    assert r4["prop2_pyth_rel_err"] <= p4["prop2_pyth_rel_err_max"]
    assert r4["prop2_orth_cos_abs"] <= p4["prop2_orth_cos_abs_max"]
    assert r4["verdict"] == (
        "HELD"
        if (
            r4["fp32_taskA_acc"] >= p4["fp32_taskA_acc_min"]
            and r4["frozen_taskB_acc"] >= p4["frozen_taskB_acc_min"]
            and r4["matched_taskB_acc_gap"] <= p4["matched_taskB_acc_gap_max"]
            and r4["prop2_pyth_rel_err"] <= p4["prop2_pyth_rel_err_max"]
            and r4["prop2_orth_cos_abs"] <= p4["prop2_orth_cos_abs_max"]
            and r4["return_only_shorter_than_sft"]
            and r4["return_only_less_logit_drift_than_sft"]
        )
        else "BROKEN"
    )

    p5, r5 = preds["HQS.5"], results["HQS.5"]
    assert r5["verdict"] == (
        "HELD"
        if (
            r5["jacobian_ratio_max_min"] >= p5["jacobian_ratio_min"]
            and r5["jacobian_log_density_max_err"] <= p5["jacobian_log_density_max_err"]
            and r5["mc_energy_dist_err_max"] <= p5["mc_energy_dist_err_max"]
            and r5["all_horizon_tv_below_contraction_bound"]
            and r5["contraction_vs_linear_ratio_at_T8"] <= p5["contraction_vs_linear_ratio_max_at_T8"]
        )
        else "BROKEN"
    )
