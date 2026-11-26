"""Unit tests for Spike 99 candidate-agreement audit, nulls, Gram stats, and verdict rules."""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from experiments import spike99 as S99
from experiments.audits import spike99_candidate_audit as AUDIT


def test_pairwise_cosine_and_canonical_isomorphism() -> None:
    # Two relabeled isomorphic 4-state automata must yield identical canonical signatures.
    D1 = np.array([[1, 2, 3, 0], [0, 0, 2, 3]], dtype=int)
    O1 = np.array([0, 0, 1, 1], dtype=int)
    # Permute states (0->2, 1->3, 2->0, 3->1) and swap letters 0<->1
    perm = [2, 3, 0, 1]
    inv = [0] * 4
    for i, p in enumerate(perm):
        inv[p] = i
    D2 = np.array(
        [
            [perm[int(D1[1, inv[q]])] for q in range(4)],
            [perm[int(D1[0, inv[q]])] for q in range(4)],
        ],
        dtype=int,
    )
    O2 = np.array([O1[inv[q]] for q in range(4)], dtype=int)
    assert AUDIT.canonical_aut_sig(D1, O1, 0) == AUDIT.canonical_aut_sig(D2, O2, perm[0])

    # Changing output breaks isomorphism
    O3 = np.array([0, 1, 1, 1], dtype=int)
    assert AUDIT.canonical_aut_sig(D1, O1, 0) != AUDIT.canonical_aut_sig(D1, O3, 0)


def test_null_a_b_c_properties_and_upper_tail_p() -> None:
    pi = np.array([0.15, 0.25, 0.35, 0.25], dtype=float)
    W, one, Q0 = AUDIT.centred_subspace_basis(pi)
    Pperp = np.eye(4) - np.outer(one, one)

    rng = np.random.default_rng(7)
    Z = rng.normal(size=(4, 16))
    X = Pperp @ (W[:, None] * Z)
    A = X @ X.T
    T_raw = rng.normal(size=(4, 4))
    T = Pperp @ (0.5 * (T_raw + T_raw.T)) @ Pperp

    na = AUDIT.null_a_gaussian_draws(T, pi, hidden_dim=64, draws=200, seed=1)
    nb, diag = AUDIT.null_b_rotation_draws(A, T, pi, draws=200, seed=2, return_diagnostics=True)
    nc = AUDIT.null_c_diagonal_draws(A, T, pi, draws=200, seed=3)
    assert na.shape == (200,)
    assert nb.shape == (200,)
    assert nc.shape == (200,)
    assert diag["max_eig_err"] < 1e-8
    assert diag["min_rot_eig"] >= -1e-8
    assert np.all((na >= -1.0 - 1e-9) & (na <= 1.0 + 1e-9))
    assert np.all((nb >= -1.0 - 1e-9) & (nb <= 1.0 + 1e-9))
    assert np.all((nc >= -1.0 - 1e-9) & (nc <= 1.0 + 1e-9))

    # Empirical upper-tail p = (1 + #{null >= obs}) / (B + 1)
    vals = np.array([0.1, 0.3, 0.5, 0.8])
    assert abs(AUDIT.empirical_upper_p(vals, 0.9) - 1.0 / 5.0) < 1e-12
    assert abs(AUDIT.empirical_upper_p(vals, 0.5) - 3.0 / 5.0) < 1e-12


def test_learned_gram_stats_and_split_half() -> None:
    pi = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    rng = np.random.default_rng(42)
    B, T = 40, 20
    ST = rng.integers(0, 4, size=(B, T))
    # Pure state-clustered embeddings with small isotropic noise
    centers = np.eye(4, 8) * 3.0
    H = centers[ST] + 0.05 * rng.normal(size=(B, T, 8))
    stats = S99.compute_learned_gram_and_stats(H, ST, pi, burn=5)
    assert stats is not None
    assert stats["r2_state"] > 0.95
    assert stats["split_half_cos"] is not None and stats["split_half_cos"] > 0.99
    assert stats["min_state_sep"] > 3.5


def test_verdict_rules_underpowered_held_broken_neither_and_holm() -> None:
    # Underpowered (< 20) must never relax and must return NO VERDICT / UNDERPOWERED.
    up = S99.evaluate_aggregate_verdict([], [], n_eligible=0)
    assert up["status"] == "UNDERPOWERED"
    assert up["verdict"] == "NO VERDICT"

    # Synthetic HELD case (20 automata, strong positive margin D = 0.20, null B p = 0.001)
    def make_aut(target_cos: float, comp_cos: float, null_p95: float, null_b_p: float):
        seed_evals = [
            {
                "target_cos": target_cos,
                "cosines": {"WcWo": target_cos, "Wo": comp_cos, "G": comp_cos, "o": comp_cos, "k1_top": comp_cos},
                "max_competitor_cos": comp_cos,
                "margin_D": target_cos - comp_cos,
                "null_A": {"median": 0.4, "p95": null_p95, "p_upper": 0.001},
                "null_B": {"median": 0.4, "p95": null_p95, "p_upper": null_b_p},
                "null_C": {"median": 0.4, "p95": null_p95, "p_upper": 0.001},
            }
            for _ in range(5)
        ]
        return S99.evaluate_automaton_held(seed_evals), seed_evals

    held_pairs = [make_aut(0.90, 0.70, 0.75, 0.001) for _ in range(20)]
    res_held = S99.evaluate_aggregate_verdict(
        [a for a, _ in held_pairs],
        [se for _, se in held_pairs],
        n_eligible=20,
        bootstrap_reps=500,
        aggregate_null_b={"p_aggregate": 0.001, "T_observed": 0.20, "reps": 500},
    )
    assert res_held["verdict"] == "HELD"
    assert res_held["n_held"] == 20
    assert all(v["reject_at_alpha"] for v in res_held["holm_pairwise"].values())

    # CI lower bound < 0.05 (e.g. 0.02..0.10) must NOT receive HELD under Commit-2 Section 8.F
    borderline_pairs = [make_aut(0.85, 0.83, 0.75, 0.001) for _ in range(10)] + [
        make_aut(0.85, 0.75, 0.75, 0.001) for _ in range(10)
    ]
    res_borderline = S99.evaluate_aggregate_verdict(
        [a for a, _ in borderline_pairs],
        [se for _, se in borderline_pairs],
        n_eligible=20,
        bootstrap_reps=500,
        aggregate_null_b={"p_aggregate": 0.001, "T_observed": 0.06, "reps": 500},
    )
    assert res_borderline["verdict"] != "HELD"

    # Intention-to-train fit failure: if only 3/5 seeds pass fit guard, individual HELD must fail
    aut_low_fit = S99.evaluate_automaton_held(held_pairs[0][1], fit_flags=[True, True, True, False, False])
    assert aut_low_fit["held"] is False
    # Individual Null B: if only 3/5 seeds have p_B <= 0.05, individual HELD must fail
    mixed_b = held_pairs[0][1][:3] + [
        {**held_pairs[0][1][0], "null_B": {"median": 0.4, "p95": 0.75, "p_upper": 0.20}},
        {**held_pairs[0][1][0], "null_B": {"median": 0.4, "p95": 0.75, "p_upper": 0.20}},
    ]
    assert S99.evaluate_automaton_held(mixed_b)["held"] is False

    # Synthetic BROKEN case (competitor beats target, CI upper < 0.05)
    broken_pairs = [make_aut(0.60, 0.75, 0.78, 0.40) for _ in range(20)]
    res_broken = S99.evaluate_aggregate_verdict(
        [a for a, _ in broken_pairs],
        [se for _, se in broken_pairs],
        n_eligible=20,
        bootstrap_reps=500,
    )
    assert res_broken["verdict"] == "BROKEN"

    # Synthetic NEITHER case (margin = 0.07 > 0.05 but only 10/20 HELD while aggregate null passes)
    neither_pairs = [make_aut(0.88, 0.80, 0.78, 0.01) for _ in range(10)] + [
        make_aut(0.82, 0.75, 0.80, 0.01) for _ in range(10)
    ]
    res_neither = S99.evaluate_aggregate_verdict(
        [a for a, _ in neither_pairs],
        [se for _, se in neither_pairs],
        n_eligible=20,
        bootstrap_reps=500,
    )
    assert res_neither["verdict"] == "NEITHER"


def test_holm_bonferroni_monotonic() -> None:
    h = S99.holm_bonferroni({"a": 0.005, "b": 0.015, "c": 0.04, "d": 0.20}, alpha=0.05)
    assert h["a"]["reject_at_alpha"] is True
    assert h["b"]["reject_at_alpha"] is True
    assert h["c"]["reject_at_alpha"] is False
    assert h["d"]["reject_at_alpha"] is False

    # Step-down stopping: if rank 1 fails (0.02 > 0.05/3), rank 2 (0.022 <= 0.05/2) must NOT reject.
    h2 = S99.holm_bonferroni({"a": 0.005, "b": 0.020, "c": 0.022, "d": 0.20}, alpha=0.05)
    assert h2["a"]["reject_at_alpha"] is True
    assert h2["b"]["reject_at_alpha"] is False
    assert h2["c"]["reject_at_alpha"] is False


def test_stratified_selection_and_aggregate_null_b() -> None:
    eligible = [{"id": i, "kind": "free" if i % 2 == 0 else "mixed", "m": 5 + (i % 3)} for i in range(30)]
    sel1, unsel1 = S99.select_stratified_20(eligible, seed=20261125)
    sel2, unsel2 = S99.select_stratified_20(eligible, seed=20261125)
    assert len(sel1) == 20
    assert len(unsel1) == 10
    assert [r["id"] for r in sel1] == [r["id"] for r in sel2]
    assert set(r["id"] for r in sel1).isdisjoint(set(unsel1))

    # Aggregate Null B test preserves hierarchy & detects strong planted alignment
    rng = np.random.default_rng(123)
    pi = np.array([0.2, 0.25, 0.25, 0.3], dtype=float)
    _, _, Q0 = AUDIT.centred_subspace_basis(pi)
    Pperp = Q0 @ Q0.T
    target = Pperp @ np.diag([2.0, 0.8, 0.3, 0.1]) @ Pperp
    cands = {"WcWo": target}
    for j, k in enumerate(S99.COMPETITOR_KEYS):
        M = rng.normal(size=(4, 4))
        M = Pperp @ (0.5 * (M + M.T)) @ Pperp
        cands[k] = M
    agg = S99.aggregate_null_b_test(
        [[target.copy() for _ in range(5)] for _ in range(3)],
        [cands for _ in range(3)],
        [pi for _ in range(3)],
        observed_T=None,
        reps=50,
    )
    assert agg["reps"] == 50
    assert agg["p_aggregate"] <= 0.05
    assert agg["psd_diagnostics"]["orig_min_eig"] >= -1e-8
    assert agg["psd_diagnostics"]["min_rot_eig"] >= -1e-8
    assert agg["psd_diagnostics"]["max_eig_err"] < 1e-7
    with pytest.raises(AssertionError, match="Supplied observed_T"):
        S99.aggregate_null_b_test(
            [[target.copy() for _ in range(5)] for _ in range(3)],
            [cands for _ in range(3)],
            [pi for _ in range(3)],
            observed_T=agg["T_observed"] + 0.25,
            reps=10,
        )


def test_statistical_identity_mixed_candidate_median_and_null_b_parity() -> None:
    # Distinct per-seed margin vs candidate-median D_a:
    # WcWo = [0.6]*5 -> med=0.6; Wo=[0.9,0.9,0.1,0.1,0.1] -> med=0.1; G=[0.1,0.1,0.1,0.9,0.9] -> med=0.1.
    # Median of seed margins = -0.30, whereas canonical D_a = 0.60 - 0.10 = +0.50.
    seed_evals_diff = [
        {
            "gram_valid": True,
            "target_cos": 0.60,
            "cosines": {"WcWo": 0.60, "Wo": wo, "G": g, "o": 0.10, "k1_top": 0.10},
            "max_competitor_cos": max(wo, g),
            "margin_D": 0.60 - max(wo, g),
            "null_A": {"median": 0.2, "p95": 0.4, "p_upper": 0.01},
            "null_B": {"median": 0.2, "p95": 0.4, "p_upper": 0.01},
            "null_C": {"median": 0.2, "p95": 0.4, "p_upper": 0.01},
        }
        for wo, g in [(0.9, 0.1), (0.9, 0.1), (0.1, 0.1), (0.1, 0.9), (0.1, 0.9)]
    ]
    summary = S99.evaluate_automaton_held(seed_evals_diff)
    assert abs(summary["margin_D"] - 0.50) < 1e-12
    boot = S99.hierarchical_bootstrap_ci(
        [np.vstack([S99.seed_eval_to_cos_row(r) for r in seed_evals_diff])], reps=40
    )
    assert abs(boot["observed_median_D"] - 0.50) < 1e-12

    # End-to-end PSD Gram matrices across 20 synthetic automata verify exact T identity
    # across evaluate_automaton_held, hierarchical_bootstrap_ci, and aggregate_null_b_test.
    pi = np.array([0.2, 0.25, 0.25, 0.3], dtype=float)
    _, _, Q0 = AUDIT.centred_subspace_basis(pi)
    v0, v1, v2 = Q0[:, 0], Q0[:, 1], Q0[:, 2]
    B0 = np.outer(v0, v0)
    B1 = np.outer(v1, v1)
    B2 = np.outer(v2, v2)
    B_neg = np.outer(v0 + v1, v0 + v1) * 0.5
    cands = {"WcWo": B0, "Wo": B1, "G": B2, "o": B_neg, "k1_top": B1 + 0.25 * B2}

    all_summaries = []
    all_seed_evals = []
    all_grams = []
    for a_idx in range(20):
        aut_grams = []
        aut_evals = []
        for s_idx in range(5):
            w0 = 1.0 + 0.1 * ((a_idx + s_idx) % 3)
            w1 = 0.2 if (s_idx < 3) else 0.7
            w2 = 0.6 if (s_idx < 2) else 0.1
            G = w0 * B0 + w1 * B1 + w2 * B2
            ev = S99.evaluate_learned_gram(G, cands, pi, hidden_dim=16, draws=40, seed=100 * a_idx + s_idx)
            aut_grams.append(G)
            aut_evals.append(ev)
        all_grams.append(aut_grams)
        all_seed_evals.append(aut_evals)
        all_summaries.append(S99.evaluate_automaton_held(aut_evals))

    obs_T = float(np.median([s["margin_D"] for s in all_summaries]))
    agg = S99.aggregate_null_b_test(
        all_grams,
        [cands for _ in range(20)],
        [pi for _ in range(20)],
        observed_T=None,
        reps=30,
        seed=777,
    )
    assert abs(agg["T_observed"] - obs_T) < 1e-12
    assert abs(agg["T_observed_from_grams"] - obs_T) < 1e-12
    verdict = S99.evaluate_aggregate_verdict(
        all_summaries, all_seed_evals, n_eligible=20, bootstrap_reps=100, aggregate_null_b=agg
    )
    assert abs(verdict["median_D"] - obs_T) < 1e-12

    # Mismatched T_observed must fail loudly rather than silently diverging.
    with pytest.raises(AssertionError, match="Statistic mismatch"):
        S99.evaluate_aggregate_verdict(
            all_summaries,
            all_seed_evals,
            n_eligible=20,
            bootstrap_reps=20,
            aggregate_null_b={**agg, "T_observed": obs_T + 0.25},
        )


def test_invalid_seed_parity_across_observed_bootstrap_and_null_b() -> None:
    pi = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
    _, _, Q0 = AUDIT.centred_subspace_basis(pi)
    B0 = np.outer(Q0[:, 0], Q0[:, 0])
    B1 = np.outer(Q0[:, 1], Q0[:, 1])
    B2 = np.outer(Q0[:, 2], Q0[:, 2])
    cands = {"WcWo": B0, "Wo": B1, "G": B2, "o": B1, "k1_top": B2}

    # 3 failed seeds out of 5 -> every candidate median is 0.0 -> D_a == 0.0 (not -1.0)
    stub = S99.failed_seed_eval_stub()
    assert stub["margin_D"] == 0.0
    valid_ev = S99.evaluate_learned_gram(B0, cands, pi, hidden_dim=8, draws=30, seed=11)
    tampered_invalid = {**valid_ev, "gram_valid": False}

    sum_stub = S99.evaluate_automaton_held([valid_ev, valid_ev, stub, stub, stub])
    sum_inv = S99.evaluate_automaton_held([valid_ev, valid_ev, tampered_invalid, stub, stub])
    assert sum_stub["margin_D"] == 0.0
    assert sum_inv["margin_D"] == 0.0
    assert sum_stub["held"] is False

    # Mix 2 valid + 1 None + 1 zero matrix + 1 NaN matrix -> Null B & bootstrap agree identically.
    aut_grams = [B0 + 0.2 * B1, B0 + 0.1 * B2, None, np.zeros((4, 4)), np.full((4, 4), np.nan)]
    aut_evals = [
        S99.evaluate_learned_gram(aut_grams[0], cands, pi, hidden_dim=8, draws=30, seed=1),
        S99.evaluate_learned_gram(aut_grams[1], cands, pi, hidden_dim=8, draws=30, seed=2),
        stub,
        stub,
        stub,
    ]
    aut_sum = S99.evaluate_automaton_held(aut_evals)
    boot = S99.hierarchical_bootstrap_ci([np.vstack([S99.seed_eval_to_cos_row(e) for e in aut_evals])], reps=25)
    agg = S99.aggregate_null_b_test([aut_grams], [cands], [pi], observed_T=None, reps=25, seed=55)
    assert abs(aut_sum["margin_D"] - boot["observed_median_D"]) < 1e-12
    assert abs(aut_sum["margin_D"] - agg["T_observed_from_grams"]) < 1e-12

    # Canonical normalizer forces BOTH gram_valid=False and fit_ok=False for missing, zero, NaN,
    # non-PSD, or incomplete-candidate-key runs, while preserving gram_valid=True, fit_ok=False
    # only when a valid finite PSD Gram exists despite accuracy < 0.99.
    valid_rec = {
        "id": 10,
        "arch": "gru_mlp",
        "seed_idx": 0,
        "fit": 0.995,
        "fit_ok": True,
        "trained": {"stats": {}, "eval": valid_ev, "G_learned": B0.tolist()},
    }
    norm_ok = S99.normalize_seed_run_record(valid_rec)
    assert norm_ok["gram_valid"] is True and norm_ok["fit_ok"] is True

    low_fit_rec = {**valid_rec, "fit": 0.85, "fit_ok": False}
    norm_low_fit = S99.normalize_seed_run_record(low_fit_rec)
    assert norm_low_fit["gram_valid"] is True and norm_low_fit["fit_ok"] is False

    incomplete_keys_ev = {**valid_ev, "cosines": {"WcWo": 0.9, "Wo": 0.1, "G": 0.1, "o": 0.1}}
    for bad_rec in [
        {**valid_rec, "missing_record": True},
        {**valid_rec, "trained": {"eval": valid_ev, "G_learned": None}},
        {**valid_rec, "trained": {"eval": valid_ev, "G_learned": np.zeros((4, 4)).tolist()}},
        {**valid_rec, "trained": {"eval": valid_ev, "G_learned": np.full((4, 4), np.nan).tolist()}},
        {**valid_rec, "trained": {"eval": valid_ev, "G_learned": (Q0 @ np.diag([2.0, -0.5, 0.1]) @ Q0.T).tolist()}},
        {**valid_rec, "trained": {"eval": incomplete_keys_ev, "G_learned": B0.tolist()}},
        {**valid_rec, "trained": {"eval": None, "G_learned": B0.tolist()}},
    ]:
        nr = S99.normalize_seed_run_record(bad_rec)
        assert nr["gram_valid"] is False and nr["fit_ok"] is False
        assert nr["trained"]["G_learned"] is None
        assert nr["trained"]["eval"]["gram_valid"] is False
        assert nr["trained"]["eval"]["fit_ok"] is False
        assert nr["trained"]["eval"]["margin_D"] == 0.0
        assert np.all(S99.seed_eval_to_cos_row(nr["trained"]["eval"]) == 0.0)


def test_seed_grid_validation_and_missing_seed_detection() -> None:
    selected_ids = list(range(10, 30))
    stub = S99.failed_seed_eval_stub()
    full_grid = [
        {
            "id": aid,
            "arch": arch,
            "seed_idx": s_idx,
            "seed": 1,
            "eval_seed": 2,
            "fit": 1.0,
            "fit_ok": True,
            "trained": {"stats": {}, "eval": stub, "G_learned": None},
        }
        for arch in ("gru_mlp", "gru_lin")
        for aid in selected_ids
        for s_idx in range(S99.SEEDS_PER_ARM)
    ]
    comp_full, rep_full = S99.validate_and_complete_seed_grid(full_grid, selected_ids)
    assert len(comp_full) == 200
    assert rep_full["n_present"] == 200 and rep_full["n_missing"] == 0 and rep_full["n_completed_grid"] == 200
    assert all((not r["gram_valid"]) and (not r["fit_ok"]) for r in comp_full)

    incomplete = full_grid[:-3]
    with pytest.raises(AssertionError, match="Missing 3 records"):
        S99.validate_and_complete_seed_grid(incomplete, selected_ids, strict_complete=True)

    comp_inc, rep_inc = S99.validate_and_complete_seed_grid(incomplete, selected_ids, strict_complete=False)
    assert len(comp_inc) == 200
    assert rep_inc["n_present"] == 197 and rep_inc["n_missing"] == 3
    missing_recs = [r for r in comp_inc if r.get("missing_record")]
    assert len(missing_recs) == 3
    assert all(
        (not r["gram_valid"])
        and (not r["fit_ok"])
        and (r["trained"]["G_learned"] is None)
        and (not r["trained"]["eval"]["gram_valid"])
        and (not r["trained"]["eval"]["fit_ok"])
        for r in missing_recs
    )

    # Extra record outside frozen selected_ids, wrong selected count, or duplicate record must fail.
    with pytest.raises(AssertionError, match="Unexpected run record"):
        S99.validate_and_complete_seed_grid(incomplete + [{**full_grid[0], "id": 999}], selected_ids)
    with pytest.raises(AssertionError, match="Duplicate run record"):
        S99.validate_and_complete_seed_grid(full_grid + [full_grid[0]], selected_ids)
    with pytest.raises(AssertionError, match="Expected 20 selected automata"):
        S99.validate_and_complete_seed_grid([], selected_ids[:19])


def test_null_b_psd_rejection_and_haar_orthogonal_properties() -> None:
    pi = np.array([0.2, 0.25, 0.25, 0.3], dtype=float)
    _, one, Q0 = AUDIT.centred_subspace_basis(pi)
    Pperp = np.eye(4) - np.outer(one, one)
    # Construct indefinite symmetric matrix in im(P_perp) with negative eigenvalue -0.5.
    A_neg = Q0 @ np.diag([2.0, 0.5, -0.5]) @ Q0.T
    T = Pperp @ np.diag([1.0, 0.5, 0.2, 0.1]) @ Pperp
    with pytest.raises(AssertionError, match="PSD"):
        AUDIT.null_b_rotation_draws(A_neg, T, pi, draws=20, seed=1)
    cands_neg = {k: T for k in S99.ALL_CAND_KEYS}
    with pytest.raises(AssertionError, match="Aggregate Null B PSD"):
        S99.aggregate_null_b_test([[A_neg]], [cands_neg], [pi], reps=10, seed=1)

    A_psd = Q0 @ np.diag([2.0, 0.5, 0.0]) @ Q0.T
    nb, diag = AUDIT.null_b_rotation_draws(A_psd, T, pi, draws=100, seed=2, return_diagnostics=True)
    assert nb.shape == (100,)
    assert diag["orig_min_eig"] >= -1e-8
    assert diag["min_rot_eig"] >= -1e-8
    assert "psd_tol" in diag

    # Verify _haar_orthogonal_batch yields O(d) orthogonality, |det|=1 sign mix, zero mean & 1/d variance.
    rng = np.random.default_rng(2026)
    d, b = 5, 2000
    U = AUDIT._haar_orthogonal_batch(rng, d, b)
    assert U.shape == (b, d, d)
    orth_err = np.max(np.abs(np.einsum("bij,bik->bjk", U, U) - np.eye(d)[None, :, :]))
    assert orth_err < 1e-10
    dets = np.linalg.det(U)
    assert np.max(np.abs(np.abs(dets) - 1.0)) < 1e-10
    pos_frac = float(np.mean(dets > 0.0))
    assert 0.40 < pos_frac < 0.60
    assert float(np.max(np.abs(np.mean(U, axis=0)))) < 0.08
    var_err = np.max(np.abs(np.mean(U ** 2, axis=0) - (1.0 / d)))
    assert float(var_err) < 0.04

    # Explicit zero-diagonal convention check: diag(R) == 0 maps to +1, never zeroing Q columns.
    class _ZeroNormal:
        def normal(self, size):
            return np.zeros(size, dtype=float)

    U_zero = AUDIT._haar_orthogonal_batch(_ZeroNormal(), d=4, b=3)
    assert np.allclose(U_zero, np.eye(4)[None, :, :])


def test_selection_lock_tamper_rejection_and_200_grid_analyse(tmp_path: pathlib.Path) -> None:
    # Build a synthetic 24-automaton pool (4 states, 2 action symbols) where all 24 are eligible.
    syn_pool = []
    eligible = []
    rng = np.random.default_rng(42)
    for i in range(24):
        D = np.array([[1, 2, 3, 1], [(i + 1) % 4, (i + 2) % 4, 0, 2]], dtype=int)
        O = np.array([i % 2, 1, 0, (i + 1) % 2], dtype=int)
        kind = "free" if i % 2 == 0 else "mixed"
        syn_pool.append({"D": D, "O": O, "s0": 0, "kind": kind})
        eligible.append({"id": i, "kind": kind, "m": 4, "L": 3, "s0": 0})

    mock_audit = {
        "spike81_pool_audit": {
            "eligible_automata": eligible,
            "n_fresh_irreversible_pi_ok": 24,
            "n_rejected": 0,
            "fresh_irrev_min_max_comp_cos": 0.50,
        }
    }
    pred_p = tmp_path / "spike99_predictions.json"
    lock_p = tmp_path / "spike99_selection_lock.json"
    raw_dir = tmp_path / "spike99_raw"
    out_p = tmp_path / "spike99.json"

    pred = S99.predict(out_path=pred_p, lock_path=lock_p, audit=mock_audit, pool=syn_pool, commit_sha="deadbeef" * 5)
    assert pred["status"] == "READY"
    assert lock_p.exists()
    lock = json.loads(lock_p.read_text(encoding="utf-8"))
    info = S99.verify_selection_lock(pred, lock, pool=syn_pool)
    assert len(info["selected_ids"]) == 20
    assert info["candidate_audit_commit_sha"] == "deadbeef" * 5

    # Tamper tests must all abort cleanly.
    bad_hash_lock = {**lock, "selected_ids": list(reversed(lock["selected_ids"]))}
    with pytest.raises(AssertionError, match="SHA-256 mismatch"):
        S99.verify_selection_lock(pred, bad_hash_lock, pool=syn_pool)

    bad_pred = {**pred, "selected_ids": list(reversed(pred["selected_ids"]))}
    with pytest.raises(AssertionError, match="selected_ids disagree"):
        S99.verify_selection_lock(bad_pred, lock, pool=syn_pool)

    tampered_pool = [{**a, "O": np.array([1 - x for x in a["O"]])} if idx == lock["selected_ids"][0] else a for idx, a in enumerate(syn_pool)]
    with pytest.raises(AssertionError, match="signature mismatch"):
        S99.verify_selection_lock(pred, lock, pool=tampered_pool)

    # Deleting the lock file before training must fail loudly even if predictions exist.
    lock_p.unlink()
    with pytest.raises(AssertionError, match="Missing immutable selection lock"):
        S99.run(pred_path=pred_p, lock_path=lock_p, raw_dir=raw_dir, pool=syn_pool)
    lock_p.write_text(json.dumps(lock, indent=1), encoding="utf-8")

    # Populate 198 of 200 grid records (leaving 2 missing) and run end-to-end analyse().
    raw_dir.mkdir(parents=True, exist_ok=True)
    selected_ids = lock["selected_ids"]
    count = 0
    for arch in ("gru_mlp", "gru_lin"):
        for aid in selected_ids:
            A = syn_pool[aid]
            Dl = np.vstack([A["D"], np.arange(4)[None]])
            pi = S99.S81.visit_dist(Dl, 0, np.ones(3) / 3, T=S99.SEQ_LEN, burn=S99.BURN)
            cands = AUDIT.candidate_matrices_from_ops(S99.MP.master_operators(Dl, np.asarray(A["O"], dtype=float), pi))
            _, _, Q0 = AUDIT.centred_subspace_basis(pi)
            Pperp = Q0 @ Q0.T
            G_psd = Pperp @ np.diag([2.0, 1.0, 0.5, 0.2]) @ Pperp
            ev_good = S99.evaluate_learned_gram(G_psd, cands, pi, hidden_dim=8, draws=15, seed=aid + 1)
            for s_idx in range(S99.SEEDS_PER_ARM):
                count += 1
                if count > 198:
                    continue
                if count == 1:
                    rec = {
                        "id": aid,
                        "arch": arch,
                        "seed_idx": s_idx,
                        "fit": 0.90,
                        "fit_ok": False,
                        "selection_lock_sha256": info["selection_sha256"],
                        "candidate_audit_commit_sha": info["candidate_audit_commit_sha"],
                        "trained": {"stats": {}, "eval": ev_good, "G_learned": G_psd.tolist()},
                    }
                elif count == 2:
                    rec = {
                        "id": aid,
                        "arch": arch,
                        "seed_idx": s_idx,
                        "fit": 1.0,
                        "fit_ok": True,
                        "selection_lock_sha256": info["selection_sha256"],
                        "candidate_audit_commit_sha": info["candidate_audit_commit_sha"],
                        "trained": {"stats": None, "eval": None, "G_learned": None},
                    }
                else:
                    rec = {
                        "id": aid,
                        "arch": arch,
                        "seed_idx": s_idx,
                        "fit": 1.0,
                        "fit_ok": True,
                        "selection_lock_sha256": info["selection_sha256"],
                        "candidate_audit_commit_sha": info["candidate_audit_commit_sha"],
                        "trained": {"stats": {}, "eval": ev_good, "G_learned": G_psd.tolist()},
                    }
                (raw_dir / f"{arch}_{aid}_{s_idx}.json").write_text(
                    json.dumps(S99.normalize_seed_run_record(rec), indent=1), encoding="utf-8"
                )

    res = S99.analyse(
        out_path=out_p,
        pred_path=pred_p,
        lock_path=lock_p,
        raw_dir=raw_dir,
        pool=syn_pool,
        null_draws=20,
        bootstrap_reps=30,
    )
    assert res["status"] == "COMPLETE"
    assert res["n_runs"] == 200
    assert res["grid_report"]["n_expected"] == 200
    assert res["grid_report"]["n_present"] == 198
    assert res["grid_report"]["n_missing"] == 2
    assert res["selection_lock_sha256"] == info["selection_sha256"]
    assert res["candidate_audit_commit_sha"] == info["candidate_audit_commit_sha"]
    assert res["arms"]["gru_mlp"]["primary_intention_to_train"]["aggregate_null_b"]["psd_diagnostics"]["orig_min_eig"] >= -1e-8

    # Raw record from a different selection lock must abort analyse().
    wrong_pth = raw_dir / f"gru_mlp_{selected_ids[0]}_2.json"
    wrong_rec = json.loads(wrong_pth.read_text(encoding="utf-8"))
    wrong_rec["selection_lock_sha256"] = "0" * 64
    wrong_pth.write_text(json.dumps(wrong_rec), encoding="utf-8")
    with pytest.raises(AssertionError, match="selection_lock_sha256"):
        S99.analyse(
            out_path=out_p, pred_path=pred_p, lock_path=lock_p, raw_dir=raw_dir, pool=syn_pool, null_draws=10, bootstrap_reps=20
        )
