"""Unit tests for Spike 99 candidate-agreement audit, nulls, Gram stats, and verdict rules."""

from __future__ import annotations

import numpy as np

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
    target = Pperp @ np.diag([2.0, 0.5, -0.5, -1.0]) @ Pperp
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
