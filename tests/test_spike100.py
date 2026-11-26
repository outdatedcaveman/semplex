"""Unit and provenance regression tests for Spike 100 (NO_id Option A & strengthened locks)."""

from __future__ import annotations

import json
import pathlib

import numpy as np
import pytest

from experiments import master_principle as MP
from experiments import spike100 as S100
from experiments.audits import spike99_candidate_audit as AUDIT


def _make_synthetic_no_id_pool(n: int = 24) -> list[dict]:
    rng = np.random.default_rng(10042)
    pool = []
    for idx in range(n):
        L = 3 + (idx % 3)
        m = 6 + (idx % 3)
        D = rng.integers(0, m, size=(L, m))
        # Ensure at least one non-bijective letter and full state reachability via last-letter cycle
        D[0, 1] = D[0, 0]
        D[-1] = np.array([(q + 1) % m for q in range(m)], dtype=int)
        O = np.array([i % 2 for i in range(m)], dtype=int)
        pool.append(
            {
                "id": 1000 + idx,
                "trial_idx": 1000 + idx,
                "L": L,
                "m": m,
                "s0": 0,
                "D": D.tolist(),
                "O": O.tolist(),
            }
        )
    return pool


def _synthetic_eval(D: np.ndarray, O: np.ndarray, pi: np.ndarray) -> tuple[dict, np.ndarray]:
    ops = MP.master_operators(D, O.astype(float), pi)
    cands = AUDIT.candidate_matrices_from_ops(ops)
    raw_g = 0.5 * (cands["WcWo"] + cands["WcWo"].T)
    ev, vecs = np.linalg.eigh(raw_g)
    G_learned = vecs @ np.diag(np.maximum(ev, 0.0)) @ vecs.T
    G_learned = 0.5 * (G_learned + G_learned.T)
    cosines = {k: float(AUDIT.cos_mat(G_learned, cands[k])) for k in S100.ALL_CAND_KEYS}
    target_cos = cosines[S100.TARGET_KEY]
    max_comp = max(cosines[c] for c in S100.COMPETITOR_KEYS)
    return (
        {
            "gram_valid": True,
            "fit_ok": True,
            "cosines": cosines,
            "target_cos": target_cos,
            "max_competitor_cos": max_comp,
            "margin_D": target_cos - max_comp,
            "null_A": {"median": 0.4, "p95": 0.72, "p_upper": 0.001},
            "null_B": {"median": 0.4, "p95": 0.72, "p_upper": 0.001},
            "null_C": {"median": 0.4, "p95": 0.72, "p_upper": 0.001},
        },
        G_learned,
    )


def test_no_id_search_determinism_and_k1_guards() -> None:
    r1 = S100.search_no_id_pool(n_trials=3, n_mut_steps=5, audit_out=None)
    r2 = S100.search_no_id_pool(n_trials=3, n_mut_steps=5, audit_out=None)
    assert r1["denominators"]["n_search_trials"] == 3
    assert len(r1["trial_logs"]) == 3
    assert r1["trial_logs"] == r2["trial_logs"]

    # Constant output must fail both non-const and k1 norm/eigengap gates.
    d_const = np.array([[1, 2, 3, 4, 5, 0], [0, 0, 2, 3, 4, 5], [1, 1, 2, 3, 4, 5]], dtype=int)
    ev_const = S100.evaluate_no_id_candidate(d_const, np.zeros(6, dtype=int))
    assert not ev_const["eligible"]
    assert "constant_output" in ev_const["reasons"]

    # L > 6 must be rejected by canonical_aut_sig_guarded.
    with pytest.raises(AssertionError, match="L <= 6"):
        S100.canonical_aut_sig_guarded(np.zeros((7, 6), dtype=int), np.array([0, 1, 0, 1, 0, 1]), 0)


def test_strict_non_bool_int_and_seed_provenance_validation() -> None:
    lock_info = {
        "selection_sha256": "a" * 64,
        "candidate_audit_commit_sha": "b" * 40,
    }
    aid = 1005
    s_idx = 2
    good = {
        "id": aid,
        "arch": "gru_mlp",
        "seed_idx": s_idx,
        "seed": S100.expected_train_seed("gru_mlp", aid, s_idx),
        "eval_seed": S100.expected_eval_seed(aid, s_idx),
        "selection_lock_sha256": lock_info["selection_sha256"],
        "candidate_audit_commit_sha": lock_info["candidate_audit_commit_sha"],
    }
    assert S100.validate_raw_record_provenance(good, lock_info, expected_key=("gru_mlp", aid, s_idx)) == (
        "gru_mlp",
        aid,
        s_idx,
    )

    # Reject bool, float, None, missing, or mismatched seed/eval_seed/id/seed_idx/arch.
    bad_cases = [
        {**good, "id": True},
        {**good, "seed_idx": False},
        {**good, "id": 1005.0},
        {**good, "seed": None},
        {**good, "seed": True},
        {**good, "eval_seed": float(good["eval_seed"])},
        {**good, "seed": good["seed"] + 1},
        {**good, "eval_seed": good["eval_seed"] + 1},
        {**good, "arch": "bad_arch"},
        {**good, "selection_lock_sha256": ""},
        {k: v for k, v in good.items() if k != "candidate_audit_commit_sha"},
    ]
    for bad in bad_cases:
        with pytest.raises(AssertionError):
            S100.validate_raw_record_provenance(bad, lock_info)


def test_predict_clean_tree_source_hashes_and_run_resume_enforcement(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    syn_pool = _make_synthetic_no_id_pool(24)
    pool_map = {r["id"]: r for r in syn_pool}
    fake_audit = {
        "denominators": {
            "n_search_trials": 24,
            "n_trial_winners_eligible": 24,
            "n_duplicates_removed": 0,
            "n_unique_eligible": 24,
        },
        "eligible_automata": syn_pool,
        "trial_logs": [],
    }
    pred_p = tmp_path / "pred.json"
    lock_p = tmp_path / "lock.json"
    raw_dir = tmp_path / "raw"
    out_p = tmp_path / "out.json"
    audit_p = tmp_path / "audit.json"

    # Dirty tree must abort predict() BEFORE writing any files.
    monkeypatch.setattr(S100.subprocess, "check_output", lambda *a, **k: " M experiments/spike100.py\n")
    with pytest.raises(AssertionError, match="Dirty git working tree"):
        S100.predict(
            out_path=pred_p,
            lock_path=lock_p,
            pool_audit_path=audit_p,
            audit=fake_audit,
            commit_sha="deadbeef" * 5,
            require_clean_tree=True,
        )
    assert not pred_p.exists() and not lock_p.exists()

    # Clean tree writes lock + predictions cleanly.
    monkeypatch.setattr(S100.subprocess, "check_output", lambda *a, **k: "")
    pred = S100.predict(
        out_path=pred_p,
        lock_path=lock_p,
        pool_audit_path=audit_p,
        audit=fake_audit,
        commit_sha="deadbeef" * 5,
        require_clean_tree=True,
    )
    assert pred["status"] == "READY"
    assert len(pred["selected_ids"]) == 20
    lock_data = json.loads(lock_p.read_text(encoding="utf-8"))
    assert lock_data["source_file_sha256s"] == S100.compute_source_file_sha256s()

    # Tampered source digest must abort verify_selection_lock().
    tampered_lock = dict(
        lock_data,
        source_file_sha256s={**lock_data["source_file_sha256s"], "experiments/spike100.py": "0" * 64},
    )
    tampered_lock["selection_sha256"] = S100.canonical_selection_lock_hash(tampered_lock)
    pred_t = dict(pred, selection_lock_sha256=tampered_lock["selection_sha256"])
    with pytest.raises(AssertionError, match="Source dependency SHA-256"):
        S100.verify_selection_lock(pred_t, tampered_lock, pool_map=pool_map, verify_source_hashes=True)

    # Populate 198/200 raw records, leaving 2 missing slots handled by ITT grid completion.
    raw_dir.mkdir(parents=True, exist_ok=True)
    selected_ids = pred["selected_ids"]
    for arch in ("gru_mlp", "gru_lin"):
        for aid in selected_ids:
            A = pool_map[aid]
            D = np.asarray(A["D"], dtype=int)
            O = np.asarray(A["O"], dtype=int)
            pi_occ = S100.S81.visit_dist(
                D, int(A["s0"]), np.ones(D.shape[0]) / D.shape[0], T=S100.SEQ_LEN, burn=S100.BURN
            )
            ev, gl = _synthetic_eval(D, O, pi_occ)
            for s_idx in range(5):
                if arch == "gru_lin" and aid == selected_ids[-1] and s_idx >= 3:
                    continue
                rec = {
                    "id": aid,
                    "arch": arch,
                    "seed_idx": s_idx,
                    "seed": S100.expected_train_seed(arch, aid, s_idx),
                    "eval_seed": S100.expected_eval_seed(aid, s_idx),
                    "hidden_dim": 64,
                    "fit": 1.0,
                    "fit_ok": True,
                    "selection_lock_sha256": lock_data["selection_sha256"],
                    "candidate_audit_commit_sha": lock_data["candidate_audit_commit_sha"],
                    "trained": {"stats": {"r2_state": 0.99}, "eval": ev, "G_learned": gl.tolist()},
                }
                (raw_dir / f"{arch}_{aid}_{s_idx}.json").write_text(
                    json.dumps(S100.normalize_seed_run_record(rec)), encoding="utf-8"
                )

    res = S100.analyse(
        out_path=out_p,
        pred_path=pred_p,
        lock_path=lock_p,
        raw_dir=raw_dir,
        pool_map=pool_map,
        null_draws=20,
        bootstrap_reps=30,
        verify_source_hashes=True,
    )
    assert res["status"] == "COMPLETE"
    assert res["n_runs"] == 200
    assert res["denominators"]["n_runs_present"] == 198
    assert res["denominators"]["n_runs_missing"] == 2

    # run() resume must reject existing raw file with wrong seed even when hashes match.
    monkeypatch.setattr(S100.S99, "available_ram_gb", lambda: 4.0)
    bad_pth = raw_dir / f"gru_mlp_{selected_ids[0]}_0.json"
    bad_rec = json.loads(bad_pth.read_text(encoding="utf-8"))
    bad_rec["seed"] = bad_rec["seed"] + 999
    bad_pth.write_text(json.dumps(bad_rec), encoding="utf-8")
    with pytest.raises(AssertionError, match="seed mismatch"):
        S100.run(pred_path=pred_p, lock_path=lock_p, raw_dir=raw_dir, pool_map=pool_map, verify_source_hashes=True)
