"""Unit tests for Spike 99 candidate-agreement audit, nulls, Gram stats, and verdict rules."""

from __future__ import annotations

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
        observed_T=0.60,
        reps=50,
    )
    assert agg["reps"] == 50
    assert agg["p_aggregate"] <= 0.05


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
    assert rep_full["n_present"] == 200 and rep_full["n_missing"] == 0

    incomplete = full_grid[:-3]
    with pytest.raises(AssertionError, match="Missing 3 records"):
        S99.validate_and_complete_seed_grid(incomplete, selected_ids, strict_complete=True)

    comp_inc, rep_inc = S99.validate_and_complete_seed_grid(incomplete, selected_ids, strict_complete=False)
    assert len(comp_inc) == 200
    assert rep_inc["n_present"] == 197 and rep_inc["n_missing"] == 3
    missing_recs = [r for r in comp_inc if r.get("missing_record")]
    assert len(missing_recs) == 3
    assert all((not r["fit_ok"]) and (r["trained"]["G_learned"] is None) and (not r["trained"]["eval"]["gram_valid"]) for r in missing_recs)

    # Extra record outside frozen selected_ids or duplicate record must fail.
    with pytest.raises(AssertionError, match="Unexpected run record"):
        S99.validate_and_complete_seed_grid(incomplete + [{**full_grid[0], "id": 999}], selected_ids)
    with pytest.raises(AssertionError, match="Duplicate run record"):
        S99.validate_and_complete_seed_grid(full_grid + [full_grid[0]], selected_ids)


def test_null_b_psd_rejection_and_haar_orthogonal_properties() -> None:
    pi = np.array([0.2, 0.25, 0.25, 0.3], dtype=float)
    _, one, Q0 = AUDIT.centred_subspace_basis(pi)
    Pperp = np.eye(4) - np.outer(one, one)
    # Construct indefinite symmetric matrix in im(P_perp) with negative eigenvalue -0.5.
    A_neg = Q0 @ np.diag([2.0, 0.5, -0.5]) @ Q0.T
    T = Pperp @ np.diag([1.0, 0.5, 0.2, 0.1]) @ Pperp
    with pytest.raises(AssertionError, match="PSD"):
        AUDIT.null_b_rotation_draws(A_neg, T, pi, draws=20, seed=1)

    A_psd = Q0 @ np.diag([2.0, 0.5, 0.0]) @ Q0.T
    nb, diag = AUDIT.null_b_rotation_draws(A_psd, T, pi, draws=100, seed=2, return_diagnostics=True)
    assert nb.shape == (100,)
    assert diag["orig_min_eig"] >= -1e-8
    assert diag["min_rot_eig"] >= -1e-8

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
