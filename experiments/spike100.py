"""Spike 100: Discriminating test of (W_c + W_o) on operator-separable NO_id irreversible automata.

Follows: Spike 99 (experiments/SPIKE_99_REPORT.md, frozen at 22b0cf5 / PR #14 904b4a9).
Pre-registered design & statistical lock (Collab Thread 2, Rounds 3-7):
  - Automaton class: Option A NO_id (no stay-identity letter; Dl = D), L in {3, 4, 5},
    n_init in {7..12}, Moore-minimized m >= 6, non-constant binary O, >= 1 non-bijective letter.
  - Independent-trial search: N_TRIALS = 200 independent deterministic trials (seed
    100_500_000 + trial_idx), N_MUT_STEPS = 250 single-entry mutations per trial minimizing
    max_B cos(WcWo, B), emitting <= 1 best eligible candidate per trial, deduplicated once
    per winner via canonical_aut_sig_guarded (k <= 6), with full 200-trial rejection ledger.
  - Hard eligibility gates (never relaxed):
      1. Irreversible, minimal m >= 6, non-constant O
      2. Finite-horizon post-burn occupancy support min(pi_occ) >= 0.01 (T=30, burn=5 from s0)
      3. Non-degenerate predictive kernel ||K_1||_F >= 1e-3 and eigengap(K_1) >= 1e-3
      4. Candidate separation max_{B in {Wo, G(lam0), o, k1_top}} cos(WcWo, B) <= 0.80
  - Provenance & integrity lock:
      * Pre-write clean-tree check at start of predict() (git status --porcelain == "")
      * source_file_sha256s bound inside canonical_selection_lock_hash() and verified at run()/analyse()
      * Strict native int (type(v) is int) checks on id, seed_idx, seed, eval_seed and arch
        in validate_raw_record_provenance() on BOTH run() resume and analyse()
  - Statistical suite: identical to Spike 99 Section 8 (200-slot ITT grid, 10k Null A/B/C &
    aggregate Null B on T = median_a(D_a), 10k hierarchical bootstrap CI95_low >= 0.05, Holm-Bonferroni).

Usage:
  python -m experiments.spike100 predict
  python -m experiments.spike100 run
  python -m experiments.spike100 analyse
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import pathlib
import subprocess
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np

from experiments import master_principle as MP
from experiments import spike81 as S81
from experiments import spike84 as S84
from experiments import spike99 as S99
from experiments.audits import spike99_candidate_audit as AUDIT

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
RAW = RESULTS / "spike100_raw"
POOL_AUDIT_PATH = RESULTS / "spike100_pool_audit.json"
PRED_PATH = RESULTS / "spike100_predictions.json"
LOCK_PATH = RESULTS / "spike100_selection_lock.json"
OUT_PATH = RESULTS / "spike100.json"

TARGET_KEY = S99.TARGET_KEY
COMPETITOR_KEYS = S99.COMPETITOR_KEYS
ALL_CAND_KEYS = S99.ALL_CAND_KEYS

MAX_COMP_THRESHOLD = 0.80
MIN_PI_OCC = 0.01
MIN_K1_NORM = 1e-3
MIN_K1_EIGENGAP = 1e-3
MIN_ELIGIBLE_AUTOMATA = 20
TARGET_N_AUTOMATA = 20

N_TRIALS = 200
N_MUT_STEPS = 250
TRIAL_SEED_BASE = 100_500_000
SELECTION_SEED = 20261126
N_INIT_LOW = 7
N_INIT_HIGH = 12
L_MIN = 3
L_MAX = 5
M_MIN = 6
MUT_TRANSITION_PROB = 0.80

SEEDS_PER_ARM = 5
HIDDEN_DIM = 64
EMB_DIM = 16
BATCH = 64
SEQ_LEN = 30
BURN = 5
STEPS = 2000
LR = 0.004
FIT_GUARD = 0.99

NULL_DRAWS = 10000
BOOTSTRAP_REPS = 10000
MIN_FREE_RAM_GB = 1.0

SOURCE_DEPENDENCY_PATHS = (
    "experiments/spike100.py",
    "experiments/spike99.py",
    "experiments/master_principle.py",
    "experiments/spike81.py",
    "experiments/spike84.py",
    "experiments/audits/spike99_candidate_audit.py",
)


def _require_strict_int(val, name: str) -> int:
    """Require native Python int (rejecting bool, float, str, None)."""
    if type(val) is not int:
        raise AssertionError(f"{name} must be a strict int (got {type(val).__name__}: {val!r}).")
    return val


def expected_train_seed(arch: str, aid: int, seed_idx: int) -> int:
    """Frozen Spike 100 training RNG seed formula."""
    if arch not in ("gru_mlp", "gru_lin"):
        raise AssertionError(f"Unsupported arch: {arch!r}")
    aid_i = _require_strict_int(aid, "id")
    s_idx_i = _require_strict_int(seed_idx, "seed_idx")
    return 100_000 + (0 if arch == "gru_mlp" else 10_000) + 100 * aid_i + s_idx_i


def expected_eval_seed(aid: int, seed_idx: int) -> int:
    """Frozen Spike 100 evaluation RNG seed formula."""
    aid_i = _require_strict_int(aid, "id")
    s_idx_i = _require_strict_int(seed_idx, "seed_idx")
    return 100_000_000 + 100 * aid_i + s_idx_i


def canonical_aut_sig_guarded(D: np.ndarray, O: np.ndarray | list[int], s0: int) -> tuple:
    """Canonical automaton signature with explicit L <= 6 permutation-complexity guard."""
    D_arr = np.asarray(D, dtype=int)
    if D_arr.ndim != 2 or D_arr.shape[0] > 6:
        raise AssertionError(f"canonical_aut_sig_guarded requires L <= 6, got shape {D_arr.shape}.")
    return AUDIT.canonical_aut_sig(D_arr, O, int(s0))


def verify_clean_working_tree(root: pathlib.Path = ROOT) -> None:
    """Fail if git working tree has any modified or untracked files."""
    out = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
    if out:
        raise AssertionError(f"Dirty git working tree rejected for production selection lock:\n{out}")


def compute_source_file_sha256s(
    paths: tuple[str, ...] = SOURCE_DEPENDENCY_PATHS,
    root: pathlib.Path = ROOT,
) -> dict[str, str]:
    """Compute SHA-256 digests of all source code dependencies."""
    digests: dict[str, str] = {}
    for rel in sorted(paths):
        fp = root / rel
        if not fp.exists():
            raise AssertionError(f"Missing dependency source file for hash lock: {fp}")
        digests[rel] = hashlib.sha256(fp.read_bytes()).hexdigest()
    return digests


def no_id_stratification_metrics(
    D: np.ndarray,
    O: np.ndarray,
    pi_occ: np.ndarray,
    ops: dict,
    hs: dict,
    k1_norm: float,
    k1_eigengap: float,
) -> dict:
    """Compute structural, finite-horizon occupancy, spectral, and rank diagnostics on NO_id DFAs."""
    L, m = D.shape
    W = np.sqrt(pi_occ)
    one = W / np.linalg.norm(W)
    M = np.zeros((m, m), dtype=float)
    Ts = []
    for a in range(L):
        Pa = np.zeros((m, m), dtype=float)
        for q in range(m):
            Pa[q, D[a, q]] = 1.0
        M += Pa / L
        Ts.append((W[:, None] * Pa) / W[None, :])
    M_tilde = sum(Ts) / L
    eigs_M = np.linalg.eigvals(M)
    mags = np.sort(np.abs(eigs_M))[::-1]
    spectral_gap = float(1.0 - mags[1]) if len(mags) > 1 else 0.0
    stat_l1_defect = float(np.sum(np.abs(pi_occ @ M - pi_occ)))
    rev_defect = float(np.linalg.norm(M_tilde - M_tilde.T) / max(np.linalg.norm(M_tilde), 1e-12))

    Lkin = np.asarray(ops["Lkin"], dtype=float)
    lkin_sub = np.linalg.eigvalsh(Lkin)
    lkin_pos = lkin_sub[lkin_sub > 1e-10]
    dirichlet_gap = float(lkin_pos.min()) if len(lkin_pos) else 0.0

    pi_pos = pi_occ[pi_occ > 0.0]
    h_pi_bits = float(-np.sum(pi_pos * np.log2(pi_pos)))
    p1 = float(np.sum(pi_occ[np.asarray(O, int) == 1]))
    p0 = 1.0 - p1
    h_out_bits = float(sum(-p * math.log2(p) for p in (p0, p1) if p > 1e-12))
    im_fracs = [len(set(D[a].tolist())) / m for a in range(L)]
    n_nonbij = sum(len(set(D[a].tolist())) < m for a in range(L))

    def mat_rank(A: np.ndarray) -> int:
        s = np.linalg.svd(A, compute_uv=False)
        return int(np.sum(s > 1e-9 * max(float(s.max()), 1e-12)))

    return {
        "m": int(m),
        "L": int(L),
        "pi_min": float(pi_occ.min()),
        "pi_entropy_bits": h_pi_bits,
        "stat_l1_defect": stat_l1_defect,
        "markov_spectral_gap": spectral_gap,
        "dirichlet_gap": dirichlet_gap,
        "n_nonbij_letters": int(n_nonbij),
        "min_image_frac": float(min(im_fracs)),
        "rev_defect": rev_defect,
        "wc_over_wo": float(ops["wc_over_wo"]),
        "cos_Wc_Wo": AUDIT.cos_mat(ops["Wc"], ops["Wo"]),
        "k1_norm": float(k1_norm),
        "k1_eigengap": float(k1_eigengap),
        "rank_WcWo": mat_rank(ops["WcWo_noheat"]),
        "rank_Wo": mat_rank(ops["Wo"]),
        "rank_Wc": mat_rank(ops["Wc"]),
        "rank_G": mat_rank(ops["G"]),
        "rank_o": mat_rank(ops["o"]),
        "out_p1": p1,
        "out_entropy_bits": h_out_bits,
        "dimO": int(hs["dimO"]),
        "dimR": int(hs["dimR"]),
        "dimH": int(hs["dimH"]),
    }


def evaluate_no_id_candidate(
    d_raw: np.ndarray,
    o_raw: np.ndarray,
    s0_raw: int = 0,
    min_pi_occ: float = MIN_PI_OCC,
    min_k1_norm: float = MIN_K1_NORM,
    min_k1_eigengap: float = MIN_K1_EIGENGAP,
    max_comp_threshold: float = MAX_COMP_THRESHOLD,
    with_strat: bool = False,
) -> dict:
    """Minimize and evaluate a NO_id DFA against all Spike 100 eligibility gates."""
    D, O, s0 = S81.minimize(np.asarray(d_raw, dtype=int), np.asarray(o_raw, dtype=int), int(s0_raw))
    L, m = D.shape
    is_irrev = any(len(set(D[a].tolist())) < m for a in range(L))
    nonconst_o = bool(O.min() < O.max())
    m_ok = bool(m >= M_MIN)

    reasons: list[str] = []
    if not m_ok:
        reasons.append(f"minimal_states_lt_{M_MIN}")
    if not is_irrev:
        reasons.append("bijective_not_irreversible")
    if not nonconst_o:
        reasons.append("constant_output")

    pi_occ = S81.visit_dist(D, s0, np.ones(L) / L, T=SEQ_LEN, burn=BURN)
    pi_min = float(pi_occ.min())
    pi_ok = bool(pi_min >= min_pi_occ)
    if not pi_ok:
        reasons.append(f"low_pi_occ_lt_{min_pi_occ}")

    ops = None
    k1_norm = 0.0
    k1_eigengap = 0.0
    max_comp = 1.0
    pw_5 = None
    if m_ok and nonconst_o and (pi_occ > 1e-12).all():
        ops = MP.master_operators(D, O.astype(float), pi_occ)
        k1_sym = 0.5 * (ops["k1"] + ops["k1"].T)
        k1_norm = float(np.linalg.norm(k1_sym))
        k1_eigs = np.sort(np.linalg.eigvalsh(k1_sym))[::-1]
        k1_eigengap = float(k1_eigs[0] - k1_eigs[1]) if len(k1_eigs) >= 2 else float(k1_eigs[0])
        mats = AUDIT.candidate_matrices_from_ops(ops)
        pw_5 = AUDIT.pairwise_cosine_matrix(mats, ALL_CAND_KEYS)
        max_comp = float(max(pw_5[TARGET_KEY][c] for c in COMPETITOR_KEYS))

    if ops is None or k1_norm < min_k1_norm:
        reasons.append(f"k1_norm_lt_{min_k1_norm}")
    if ops is None or k1_eigengap < min_k1_eigengap:
        reasons.append(f"k1_eigengap_lt_{min_k1_eigengap}")
    if ops is None or max_comp > max_comp_threshold:
        reasons.append(f"max_comp_cos_gt_{max_comp_threshold:.2f}")

    # Lexicographic score for hill-climbing: first minimize hard non-sep failures, then pi deficit, then max_comp
    n_structural_fails = int(not m_ok) + int(not is_irrev) + int(not nonconst_o) + int(not pi_ok)
    n_k1_fails = int(ops is None or k1_norm < min_k1_norm) + int(ops is None or k1_eigengap < min_k1_eigengap)
    obj = (n_structural_fails + n_k1_fails, -min(pi_min, min_pi_occ), max_comp)
    eligible = len(reasons) == 0

    strat = None
    if with_strat and ops is not None:
        hs = S84.head_structure(D, O.astype(float), pi_occ)
        strat = no_id_stratification_metrics(D, O, pi_occ, ops, hs, k1_norm, k1_eigengap)

    return {
        "D": D,
        "O": O,
        "s0": int(s0),
        "L": int(L),
        "m": int(m),
        "pi_occ": pi_occ,
        "pi_min": pi_min,
        "k1_norm": k1_norm,
        "k1_eigengap": k1_eigengap,
        "max_competitor_cos": max_comp,
        "pairwise_5": pw_5,
        "reasons": reasons,
        "eligible": eligible,
        "obj": obj,
        "strat": strat,
    }


def search_no_id_pool(
    n_trials: int = N_TRIALS,
    n_mut_steps: int = N_MUT_STEPS,
    trial_seed_base: int = TRIAL_SEED_BASE,
    audit_out: pathlib.Path | None = POOL_AUDIT_PATH,
) -> dict:
    """Run independent-trial NO_id operator-separation search with full rejection audit."""
    trial_logs: list[dict] = []
    raw_winners: list[dict] = []
    seen_sigs: dict[tuple, int] = {}
    unique_eligible: list[dict] = []
    n_duplicates = 0

    for trial_idx in range(n_trials):
        rng = np.random.default_rng(trial_seed_base + trial_idx)
        n_init = int(rng.integers(N_INIT_LOW, N_INIT_HIGH + 1))
        L = int(rng.integers(L_MIN, L_MAX + 1))
        d = rng.integers(0, n_init, size=(L, n_init))
        o = rng.integers(0, 2, size=n_init)

        curr_ev = evaluate_no_id_candidate(d, o, s0_raw=0)
        init_summary = {
            "m": curr_ev["m"],
            "L": curr_ev["L"],
            "pi_min": curr_ev["pi_min"],
            "k1_norm": curr_ev["k1_norm"],
            "k1_eigengap": curr_ev["k1_eigengap"],
            "max_competitor_cos": curr_ev["max_competitor_cos"],
            "reasons": curr_ev["reasons"],
        }
        best_elig = None
        if curr_ev["eligible"]:
            best_elig = (d.copy(), o.copy(), curr_ev, 0)

        for step in range(1, n_mut_steps + 1):
            d_prop = d.copy()
            o_prop = o.copy()
            if float(rng.random()) < MUT_TRANSITION_PROB:
                a = int(rng.integers(0, L))
                q = int(rng.integers(0, n_init))
                v = int(rng.integers(0, n_init))
                d_prop[a, q] = v
            else:
                q = int(rng.integers(0, n_init))
                o_prop[q] = 1 - int(o_prop[q])
            prop_ev = evaluate_no_id_candidate(d_prop, o_prop, s0_raw=0)
            if prop_ev["obj"] <= curr_ev["obj"]:
                d, o, curr_ev = d_prop, o_prop, prop_ev
            if prop_ev["eligible"]:
                if best_elig is None or prop_ev["max_competitor_cos"] < best_elig[2]["max_competitor_cos"]:
                    best_elig = (d_prop.copy(), o_prop.copy(), prop_ev, step)

        dup_of = None
        winner_step = None
        if best_elig is not None:
            wd, wo, _, winner_step = best_elig
            full_ev = evaluate_no_id_candidate(wd, wo, s0_raw=0, with_strat=True)
            sig = canonical_aut_sig_guarded(full_ev["D"], full_ev["O"], full_ev["s0"])
            dup_of = seen_sigs.get(sig)
            if dup_of is None:
                seen_sigs[sig] = trial_idx
                entry = {
                    "id": int(trial_idx),
                    "trial_idx": int(trial_idx),
                    "winner_step": int(winner_step),
                    "L": int(full_ev["L"]),
                    "m": int(full_ev["m"]),
                    "s0": int(full_ev["s0"]),
                    "D": full_ev["D"].tolist(),
                    "O": full_ev["O"].tolist(),
                    "pi_occ": full_ev["pi_occ"].tolist(),
                    "pi_min": float(full_ev["pi_min"]),
                    "k1_norm": float(full_ev["k1_norm"]),
                    "k1_eigengap": float(full_ev["k1_eigengap"]),
                    "max_competitor_cos": float(full_ev["max_competitor_cos"]),
                    "pairwise_5": full_ev["pairwise_5"],
                    "strat": full_ev["strat"],
                    "canonical_sig": S99._to_json_sig(sig),
                }
                unique_eligible.append(entry)
            else:
                n_duplicates += 1
            raw_winners.append(
                {
                    "trial_idx": int(trial_idx),
                    "winner_step": int(winner_step),
                    "L": int(full_ev["L"]),
                    "m": int(full_ev["m"]),
                    "max_competitor_cos": float(full_ev["max_competitor_cos"]),
                    "duplicate_of_trial": dup_of,
                }
            )
            final_ev = full_ev
        else:
            final_ev = curr_ev

        trial_logs.append(
            {
                "trial_idx": int(trial_idx),
                "trial_seed": int(trial_seed_base + trial_idx),
                "n_init": int(n_init),
                "L_init": int(L),
                "eligible_found": best_elig is not None,
                "winner_step": winner_step,
                "duplicate_of_trial": dup_of,
                "initial": init_summary,
                "final_or_best": {
                    "m": int(final_ev["m"]),
                    "L": int(final_ev["L"]),
                    "pi_min": float(final_ev["pi_min"]),
                    "k1_norm": float(final_ev["k1_norm"]),
                    "k1_eigengap": float(final_ev["k1_eigengap"]),
                    "max_competitor_cos": float(final_ev["max_competitor_cos"]),
                    "reasons": final_ev["reasons"] + ([f"duplicate_of_{dup_of}"] if dup_of is not None else []),
                },
            }
        )

    audit_payload = {
        "spike": 100,
        "automaton_class": "NO_id",
        "search_params": {
            "n_trials": int(n_trials),
            "n_mut_steps": int(n_mut_steps),
            "trial_seed_base": int(trial_seed_base),
            "n_init_range": [N_INIT_LOW, N_INIT_HIGH],
            "L_range": [L_MIN, L_MAX],
            "m_min": M_MIN,
            "min_pi_occ": MIN_PI_OCC,
            "min_k1_norm": MIN_K1_NORM,
            "min_k1_eigengap": MIN_K1_EIGENGAP,
            "max_comp_threshold": MAX_COMP_THRESHOLD,
            "mut_transition_prob": MUT_TRANSITION_PROB,
        },
        "denominators": {
            "n_search_trials": int(n_trials),
            "n_trial_winners_eligible": len(raw_winners),
            "n_duplicates_removed": int(n_duplicates),
            "n_unique_eligible": len(unique_eligible),
        },
        "eligible_automata": unique_eligible,
        "trial_logs": trial_logs,
    }
    if audit_out is not None:
        audit_out.parent.mkdir(parents=True, exist_ok=True)
        audit_out.write_text(json.dumps(audit_payload, indent=1), encoding="utf-8", newline="\n")
    return audit_payload


def select_stratified_20_no_id(
    eligible: list[dict],
    seed: int = SELECTION_SEED,
) -> tuple[list[dict], list[int]]:
    """Deterministic stratified sampling of 20 automata over (L, m) strata."""
    rng = np.random.default_rng(seed)
    strata: dict[tuple[int, int], list[dict]] = {}
    for row in sorted(eligible, key=lambda r: int(r["id"])):
        strata.setdefault((int(row["L"]), int(row["m"])), []).append(row)
    for k in sorted(strata):
        perm = rng.permutation(len(strata[k]))
        strata[k] = [strata[k][int(i)] for i in perm]
    selected: list[dict] = []
    keys = sorted(strata)
    while len(selected) < TARGET_N_AUTOMATA and any(strata[k] for k in keys):
        for k in keys:
            if strata[k] and len(selected) < TARGET_N_AUTOMATA:
                selected.append(strata[k].pop(0))
    sel_ids = {int(r["id"]) for r in selected}
    unselected_ids = sorted(int(r["id"]) for r in eligible if int(r["id"]) not in sel_ids)
    return sorted(selected, key=lambda r: int(r["id"])), unselected_ids


def canonical_selection_lock_hash(lock_payload: dict) -> str:
    """Compute SHA-256 hash over immutable Spike 100 lock fields including source digests."""
    keys = (
        "spike",
        "status",
        "automaton_class",
        "candidate_audit_commit_sha",
        "source_file_sha256s",
        "selection_algorithm",
        "strata_keys",
        "selection_seed",
        "max_competitor_threshold",
        "min_eligible_required",
        "eligible_count",
        "eligible_strata_inputs",
        "selected_ids",
        "eligible_unselected_ids",
        "selected_signatures",
    )
    body = {k: lock_payload[k] for k in keys}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_selection_lock(
    eligible: list[dict],
    selected: list[dict],
    unselected_ids: list[int],
    status: str,
    commit_sha: str | None = None,
    selection_seed: int = SELECTION_SEED,
    source_file_sha256s: dict[str, str] | None = None,
) -> dict:
    """Build immutable cryptographic selection-lock payload bound to source file SHA-256 digests."""
    sha = commit_sha or S99._git_head_sha()
    src_hashes = source_file_sha256s if source_file_sha256s is not None else compute_source_file_sha256s()
    eligible_inputs = [
        {"id": int(r["id"]), "L": int(r["L"]), "m": int(r["m"])}
        for r in sorted(eligible, key=lambda x: int(x["id"]))
    ]
    selected_ids = [int(r["id"]) for r in selected]
    selected_sigs = []
    for r in selected:
        D = np.asarray(r["D"], dtype=int)
        O = np.asarray(r["O"], dtype=int)
        s0 = int(r["s0"])
        sig = canonical_aut_sig_guarded(D, O, s0)
        selected_sigs.append(
            {
                "id": int(r["id"]),
                "L": int(D.shape[0]),
                "m": int(D.shape[1]),
                "s0": s0,
                "D": D.tolist(),
                "O": O.tolist(),
                "canonical_sig": S99._to_json_sig(sig),
            }
        )
    lock_payload = {
        "spike": 100,
        "status": str(status),
        "automaton_class": "NO_id",
        "candidate_audit_commit_sha": sha,
        "source_file_sha256s": src_hashes,
        "selection_algorithm": "deterministic_stratified_round_robin_over_L_m_strata",
        "strata_keys": ["L", "m"],
        "selection_seed": int(selection_seed),
        "max_competitor_threshold": MAX_COMP_THRESHOLD,
        "min_eligible_required": MIN_ELIGIBLE_AUTOMATA,
        "eligible_count": len(eligible),
        "eligible_strata_inputs": eligible_inputs,
        "selected_ids": selected_ids,
        "eligible_unselected_ids": [int(x) for x in unselected_ids],
        "selected_signatures": selected_sigs,
    }
    lock_payload["selection_sha256"] = canonical_selection_lock_hash(lock_payload)
    return lock_payload


def verify_selection_lock(
    pred_payload: dict,
    lock_payload: dict,
    pool_map: dict[int, dict] | None = None,
    verify_source_hashes: bool = True,
) -> dict:
    """Verify selection lock SHA, dependency source digests, stratified replay, and canonical signatures."""
    expected_sha = canonical_selection_lock_hash(lock_payload)
    recorded_sha = str(lock_payload.get("selection_sha256", ""))
    if not recorded_sha or not hmac.compare_digest(expected_sha, recorded_sha):
        raise AssertionError(f"Selection lock SHA-256 mismatch: expected={expected_sha}, recorded={recorded_sha}")

    if verify_source_hashes:
        recorded_srcs = lock_payload.get("source_file_sha256s")
        live_srcs = compute_source_file_sha256s()
        if recorded_srcs != live_srcs:
            raise AssertionError("Source dependency SHA-256 digests disagree with selection lock.")

    status = str(lock_payload.get("status", ""))
    if str(pred_payload.get("status", "")) != status:
        raise AssertionError(f"Lock/prediction status mismatch: {status} vs {pred_payload.get('status')}")
    for field, exp in (
        ("selection_lock_sha256", recorded_sha),
        ("candidate_audit_commit_sha", str(lock_payload["candidate_audit_commit_sha"])),
    ):
        val = pred_payload.get(field)
        if not isinstance(val, str) or not val or not hmac.compare_digest(val, exp):
            raise AssertionError(f"Predictions file missing or mismatched {field}.")

    if status != "READY":
        return {
            "status": status,
            "selection_sha256": recorded_sha,
            "candidate_audit_commit_sha": str(lock_payload["candidate_audit_commit_sha"]),
            "selected_ids": [],
        }

    selected_ids = [_require_strict_int(x, "lock.selected_ids") for x in lock_payload.get("selected_ids", [])]
    if len(selected_ids) != TARGET_N_AUTOMATA or len(set(selected_ids)) != TARGET_N_AUTOMATA:
        raise AssertionError(f"Selection lock must contain {TARGET_N_AUTOMATA} unique IDs, got {selected_ids}")
    if [int(x) for x in pred_payload.get("selected_ids", [])] != selected_ids:
        raise AssertionError("Predictions selected_ids disagree with selection lock.")
    if [int(x["id"]) for x in pred_payload.get("selected_automata", [])] != selected_ids:
        raise AssertionError("Predictions selected_automata IDs disagree with selection lock.")
    if [int(x["id"]) for x in lock_payload.get("selected_signatures", [])] != selected_ids:
        raise AssertionError("Selection lock selected_signatures IDs disagree with selected_ids.")
    if int(pred_payload.get("selection_seed", -1)) != int(lock_payload["selection_seed"]):
        raise AssertionError("Selection seed mismatch between predictions and selection lock.")
    if int(pred_payload.get("n_eligible", -1)) != int(lock_payload["eligible_count"]):
        raise AssertionError("Eligible count mismatch between predictions and selection lock.")

    re_sel, re_unsel = select_stratified_20_no_id(
        lock_payload["eligible_strata_inputs"], seed=int(lock_payload["selection_seed"])
    )
    if [int(r["id"]) for r in re_sel] != selected_ids or re_unsel != lock_payload["eligible_unselected_ids"]:
        raise AssertionError("Deterministic stratified selection replay disagrees with selection lock.")

    for entry in lock_payload["selected_signatures"]:
        aid = _require_strict_int(entry["id"], "entry.id")
        D = np.asarray(entry["D"], dtype=int)
        O = np.asarray(entry["O"], dtype=int)
        s0 = _require_strict_int(entry["s0"], "entry.s0")
        if D.shape != (int(entry["L"]), int(entry["m"])):
            raise AssertionError(f"Shape mismatch in selection lock on id={aid}")
        rebuilt_sig = S99._to_json_sig(canonical_aut_sig_guarded(D, O, s0))
        if rebuilt_sig != entry["canonical_sig"]:
            raise AssertionError(f"Canonical automaton signature mismatch in selection lock on id={aid}")
        if pool_map is not None:
            if aid not in pool_map:
                raise AssertionError(f"Selected ID {aid} missing from supplied pool_map.")
            PA = pool_map[aid]
            pool_sig = S99._to_json_sig(canonical_aut_sig_guarded(np.asarray(PA["D"], int), PA["O"], int(PA["s0"])))
            if pool_sig != entry["canonical_sig"]:
                raise AssertionError(f"Canonical signature mismatch vs pool_map on id={aid}")

    return {
        "status": "READY",
        "selection_sha256": recorded_sha,
        "candidate_audit_commit_sha": str(lock_payload["candidate_audit_commit_sha"]),
        "selected_ids": selected_ids,
    }


def validate_raw_record_provenance(
    rec: dict,
    lock_info: dict,
    expected_key: tuple[str, int, int] | None = None,
    source_desc: str = "raw record",
) -> tuple[str, int, int]:
    """Strictly validate cryptographic provenance, arch, and exact non-bool int slot/seed fields."""
    if not isinstance(rec, dict):
        raise AssertionError(f"{source_desc}: raw training record must be a JSON object.")
    exp_lock_sha = str(lock_info.get("selection_sha256", ""))
    exp_audit_sha = str(lock_info.get("candidate_audit_commit_sha", ""))
    if not exp_lock_sha or not exp_audit_sha:
        raise AssertionError("Selection lock provenance metadata is incomplete.")
    for field, expected in (
        ("selection_lock_sha256", exp_lock_sha),
        ("candidate_audit_commit_sha", exp_audit_sha),
    ):
        val = rec.get(field)
        if not isinstance(val, str) or not val or not hmac.compare_digest(val, expected):
            raise AssertionError(f"{source_desc}: missing, empty, or mismatched {field}.")

    arch = rec.get("arch")
    if type(arch) is not str or arch not in ("gru_mlp", "gru_lin"):
        raise AssertionError(f"{source_desc}: invalid arch {arch!r}.")
    aid = _require_strict_int(rec.get("id"), f"{source_desc}.id")
    s_idx = _require_strict_int(rec.get("seed_idx"), f"{source_desc}.seed_idx")
    actual_key = (arch, aid, s_idx)
    if expected_key is not None and actual_key != expected_key:
        raise AssertionError(f"{source_desc}: slot mismatch {actual_key} != expected {expected_key}.")

    raw_seed = _require_strict_int(rec.get("seed"), f"{source_desc}.seed")
    raw_eval = _require_strict_int(rec.get("eval_seed"), f"{source_desc}.eval_seed")
    exp_seed = expected_train_seed(arch, aid, s_idx)
    exp_eval = expected_eval_seed(aid, s_idx)
    if raw_seed != exp_seed:
        raise AssertionError(f"{source_desc}: seed mismatch ({raw_seed} != {exp_seed}).")
    if raw_eval != exp_eval:
        raise AssertionError(f"{source_desc}: eval_seed mismatch ({raw_eval} != {exp_eval}).")
    return actual_key


def normalize_seed_run_record(rec: dict) -> dict:
    """Validate slot/seed strict ints and delegate Gram/eval normalization to canonical S99 normalizer."""
    out = dict(rec)
    arch = out.get("arch")
    if type(arch) is not str or arch not in ("gru_mlp", "gru_lin"):
        raise AssertionError(f"normalize_seed_run_record: invalid arch {arch!r}.")
    aid = _require_strict_int(out.get("id"), "record.id")
    s_idx = _require_strict_int(out.get("seed_idx"), "record.seed_idx")
    seed = _require_strict_int(out.get("seed"), "record.seed")
    eval_seed = _require_strict_int(out.get("eval_seed"), "record.eval_seed")
    if seed != expected_train_seed(arch, aid, s_idx):
        raise AssertionError(f"normalize_seed_run_record: seed mismatch ({seed}).")
    if eval_seed != expected_eval_seed(aid, s_idx):
        raise AssertionError(f"normalize_seed_run_record: eval_seed mismatch ({eval_seed}).")
    return S99.normalize_seed_run_record(out)


def make_missing_seed_record(arch: str, aid: int, seed_idx: int) -> dict:
    """Create canonical failed-run record for a missing Spike 100 seed grid slot."""
    return normalize_seed_run_record(
        {
            "id": _require_strict_int(aid, "aid"),
            "arch": arch,
            "seed_idx": _require_strict_int(seed_idx, "seed_idx"),
            "seed": expected_train_seed(arch, aid, seed_idx),
            "eval_seed": expected_eval_seed(aid, seed_idx),
            "hidden_dim": HIDDEN_DIM,
            "fit": 0.0,
            "fit_ok": False,
            "missing_record": True,
            "untrained_control": {"fit": 0.0, "stats": None, "eval": None},
            "trained": {"stats": None, "eval": S99.failed_seed_eval_stub(), "G_learned": None},
        }
    )


def validate_and_complete_seed_grid(
    runs: list[dict],
    selected_ids: list[int],
    seeds_per_arm: int = SEEDS_PER_ARM,
    strict_complete: bool = False,
    expected_n_automata: int = TARGET_N_AUTOMATA,
) -> tuple[list[dict], dict]:
    """Validate frozen (arch, id, seed_idx) grid with strict non-bool int keys and complete missing slots."""
    ordered_ids = sorted(_require_strict_int(x, "selected_ids") for x in selected_ids)
    if len(set(ordered_ids)) != len(ordered_ids):
        raise AssertionError(f"Duplicate IDs in selected_ids: {selected_ids}")
    if len(ordered_ids) != expected_n_automata:
        raise AssertionError(f"Expected {expected_n_automata} selected automata in grid, got {len(ordered_ids)}")
    expected_keys = {
        (arch, aid, s_idx)
        for arch in ("gru_mlp", "gru_lin")
        for aid in ordered_ids
        for s_idx in range(seeds_per_arm)
    }
    by_key: dict[tuple[str, int, int], dict] = {}
    for rec in runs:
        arch = rec.get("arch")
        if type(arch) is not str or arch not in ("gru_mlp", "gru_lin"):
            raise AssertionError(f"Invalid arch in grid record: {arch!r}")
        aid = _require_strict_int(rec.get("id"), "record.id")
        s_idx = _require_strict_int(rec.get("seed_idx"), "record.seed_idx")
        key = (arch, aid, s_idx)
        if key not in expected_keys:
            raise AssertionError(f"Unexpected run record outside frozen grid: {key}")
        if key in by_key:
            raise AssertionError(f"Duplicate run record in grid: {key}")
        by_key[key] = normalize_seed_run_record(rec)

    completed: list[dict] = []
    missing_keys: list[dict] = []
    for arch in ("gru_mlp", "gru_lin"):
        for aid in ordered_ids:
            for s_idx in range(seeds_per_arm):
                key = (arch, aid, s_idx)
                if key in by_key:
                    completed.append(by_key[key])
                else:
                    missing_keys.append({"arch": arch, "id": aid, "seed_idx": s_idx})
                    completed.append(make_missing_seed_record(arch, aid, s_idx))
    if strict_complete and missing_keys:
        raise AssertionError(f"Missing {len(missing_keys)} records from required seed grid: {missing_keys[:5]}")

    expected_total = 2 * expected_n_automata * seeds_per_arm
    if len(completed) != expected_total:
        raise AssertionError(f"Seed grid postcondition failed: expected {expected_total}, got {len(completed)}")

    return completed, {
        "n_expected": len(expected_keys),
        "n_completed_grid": len(completed),
        "n_present": len(by_key),
        "n_missing": len(missing_keys),
        "missing_records": missing_keys,
    }


def predict(
    out_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    pool_audit_path: pathlib.Path = POOL_AUDIT_PATH,
    audit: dict | None = None,
    commit_sha: str | None = None,
    require_clean_tree: bool = True,
) -> dict:
    """Verify clean tree BEFORE writing, search NO_id pool, and persist immutable selection lock."""
    if require_clean_tree:
        verify_clean_working_tree()
    src_hashes = compute_source_file_sha256s()
    if audit is None:
        audit = search_no_id_pool(audit_out=pool_audit_path)
    eligible = audit["eligible_automata"]

    if len(eligible) < MIN_ELIGIBLE_AUTOMATA:
        lock_payload = build_selection_lock(
            eligible=eligible,
            selected=[],
            unselected_ids=[],
            status="UNDERPOWERED",
            commit_sha=commit_sha,
            source_file_sha256s=src_hashes,
        )
        payload = {
            "spike": 100,
            "status": "UNDERPOWERED",
            "automaton_class": "NO_id",
            "denominators": audit["denominators"],
            "max_competitor_threshold": MAX_COMP_THRESHOLD,
            "min_eligible_required": MIN_ELIGIBLE_AUTOMATA,
            "n_eligible": len(eligible),
            "reason": (
                f"Only {len(eligible)}/{audit['denominators']['n_search_trials']} independent NO_id trials "
                f"yielded unique automata passing all hard gates (< {MIN_ELIGIBLE_AUTOMATA}). Threshold NOT relaxed."
            ),
            "selected_ids": [],
            "selected_automata": [],
            "selection_lock_file": str(lock_path.relative_to(ROOT)).replace("\\", "/") if lock_path.is_relative_to(ROOT) else str(lock_path),
            "selection_lock_sha256": lock_payload["selection_sha256"],
            "candidate_audit_commit_sha": lock_payload["candidate_audit_commit_sha"],
            "source_file_sha256s": src_hashes,
            "pool_audit_file": str(pool_audit_path.relative_to(ROOT)).replace("\\", "/") if pool_audit_path.is_relative_to(ROOT) else str(pool_audit_path),
        }
    else:
        selected, unselected_ids = select_stratified_20_no_id(eligible, seed=SELECTION_SEED)
        lock_payload = build_selection_lock(
            eligible=eligible,
            selected=selected,
            unselected_ids=unselected_ids,
            status="READY",
            commit_sha=commit_sha,
            source_file_sha256s=src_hashes,
        )
        payload = {
            "spike": 100,
            "status": "READY",
            "automaton_class": "NO_id",
            "denominators": audit["denominators"],
            "max_competitor_threshold": MAX_COMP_THRESHOLD,
            "min_eligible_required": MIN_ELIGIBLE_AUTOMATA,
            "selection_seed": SELECTION_SEED,
            "n_eligible": len(eligible),
            "selected_ids": [int(r["id"]) for r in selected],
            "eligible_unselected_ids": unselected_ids,
            "selected_automata": selected,
            "selection_lock_file": str(lock_path.relative_to(ROOT)).replace("\\", "/") if lock_path.is_relative_to(ROOT) else str(lock_path),
            "selection_lock_sha256": lock_payload["selection_sha256"],
            "candidate_audit_commit_sha": lock_payload["candidate_audit_commit_sha"],
            "source_file_sha256s": src_hashes,
            "pool_audit_file": str(pool_audit_path.relative_to(ROOT)).replace("\\", "/") if pool_audit_path.is_relative_to(ROOT) else str(pool_audit_path),
        }

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock_payload, indent=1), encoding="utf-8", newline="\n")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1), encoding="utf-8", newline="\n")
    print(
        f"Spike 100 predict: status={payload['status']}, "
        f"n_unique_eligible={payload['n_eligible']}, lock_sha={lock_payload['selection_sha256'][:12]}"
    )
    return payload


def _train_or_eval_one(
    A: dict,
    arch: str,
    seed_idx: int,
    steps: int = STEPS,
    draws: int = NULL_DRAWS,
    selection_lock_sha256: str | None = None,
    candidate_audit_commit_sha: str | None = None,
) -> dict:
    """Train one NO_id GRU arm (or step-0 untrained control) and evaluate learned Gram."""
    import torch

    nn = torch.nn
    Dl = np.asarray(A["D"], dtype=int)  # NO_id: no stay-identity letter appended
    O = np.asarray(A["O"], dtype=float)
    s0 = int(A["s0"])
    L = int(Dl.shape[0])
    aid = int(A["id"])
    pi_occ = S81.visit_dist(Dl, s0, np.ones(L) / L, T=SEQ_LEN, burn=BURN)
    ops = MP.master_operators(Dl, O, pi_occ)
    cand_mats = AUDIT.candidate_matrices_from_ops(ops)

    seed = expected_train_seed(arch, aid, seed_idx)
    eval_seed = expected_eval_seed(aid, seed_idx)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    mdl = S99.make_gru_model(arch, L=L, k_out=1, hidden_dim=HIDDEN_DIM)

    def _collect_eval(offset: int):
        with torch.no_grad():
            Xv, Yv, _ = MP.fast_sample(Dl, O, s0, 500, 100, np.random.default_rng(eval_seed + offset))
            fit = float(((mdl(Xv) > 0).float() == Yv).float().mean())
            Xh, _, ST = MP.fast_sample(Dl, O, s0, 400, SEQ_LEN, np.random.default_rng(eval_seed + offset + 1_000_000))
            H = mdl.hidden(Xh).numpy()
        return fit, H, ST

    mdl.eval()
    fit0, H0, ST0 = _collect_eval(500_000)
    stats0 = S99.compute_learned_gram_and_stats(H0, ST0, pi_occ, burn=BURN)
    eval0 = (
        S99.evaluate_learned_gram(stats0["G_learned"], cand_mats, pi_occ, hidden_dim=mdl.hidden_dim, draws=draws, seed=seed + 1)
        if stats0 is not None
        else None
    )

    mdl.train()
    opt = torch.optim.AdamW(mdl.parameters(), lr=LR, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)
    for _ in range(steps):
        X, Y, _ = MP.fast_sample(Dl, O, s0, BATCH, SEQ_LEN, rng)
        loss = nn.functional.binary_cross_entropy_with_logits(mdl(X), Y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        sch.step()

    mdl.eval()
    fit, H, ST = _collect_eval(1_000_000)
    stats = S99.compute_learned_gram_and_stats(H, ST, pi_occ, burn=BURN)
    eval_tr = (
        S99.evaluate_learned_gram(stats["G_learned"], cand_mats, pi_occ, hidden_dim=mdl.hidden_dim, draws=draws, seed=seed + 2)
        if stats is not None
        else None
    )
    fit_ok = bool(fit >= FIT_GUARD)
    raw_rec = {
        "id": aid,
        "arch": arch,
        "seed_idx": int(seed_idx),
        "seed": seed,
        "eval_seed": eval_seed,
        "hidden_dim": int(mdl.hidden_dim),
        "fit": fit,
        "fit_ok": fit_ok,
        "selection_lock_sha256": selection_lock_sha256,
        "candidate_audit_commit_sha": candidate_audit_commit_sha,
        "untrained_control": {
            "fit": fit0,
            "stats": {k: v for k, v in stats0.items() if k not in ("Ce", "G_learned")} if stats0 else None,
            "eval": eval0,
        },
        "trained": {
            "stats": {k: v for k, v in stats.items() if k not in ("Ce", "G_learned")} if stats else None,
            "eval": eval_tr,
            "G_learned": stats["G_learned"].tolist() if stats is not None else None,
        },
    }
    return normalize_seed_run_record(raw_rec)


def run(
    pred_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    raw_dir: pathlib.Path = RAW,
    pool_map: dict[int, dict] | None = None,
    verify_source_hashes: bool = True,
) -> dict | None:
    """Execute Spike 100 training ONLY if selection lock + source digests verify and N_elig >= 20."""
    import torch

    torch.set_num_threads(1)
    if not pred_path.exists() or not lock_path.exists():
        raise AssertionError(f"Missing pre-registered predictions or selection lock: {pred_path}, {lock_path}")
    P = json.loads(pred_path.read_text(encoding="utf-8"))
    L = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_info = verify_selection_lock(P, L, pool_map=pool_map, verify_source_hashes=verify_source_hashes)
    if P["status"] != "READY":
        print(
            f"Spike 100 run aborted cleanly: status={P['status']}, "
            f"n_eligible={P['n_eligible']} (< {MIN_ELIGIBLE_AUTOMATA}). No training executed."
        )
        return None
    selected = P["selected_automata"]

    free_gb = S99.available_ram_gb()
    if free_gb is not None and free_gb < MIN_FREE_RAM_GB:
        raise RuntimeError(f"Aborted: free RAM {free_gb:.2f} GB < {MIN_FREE_RAM_GB:.2f} GB floor.")

    raw_dir.mkdir(parents=True, exist_ok=True)
    for arch in ("gru_mlp", "gru_lin"):
        for item in selected:
            aid = int(item["id"])
            A = pool_map[aid] if pool_map is not None else item
            for s_idx in range(SEEDS_PER_ARM):
                pth = raw_dir / f"{arch}_{aid}_{s_idx}.json"
                if pth.exists():
                    existing = json.loads(pth.read_text(encoding="utf-8"))
                    validate_raw_record_provenance(
                        existing, lock_info, expected_key=(arch, aid, s_idx), source_desc=str(pth)
                    )
                    continue
                free_gb = S99.available_ram_gb()
                if free_gb is not None and free_gb < MIN_FREE_RAM_GB:
                    raise RuntimeError(f"Stopped mid-run: free RAM {free_gb:.2f} GB < {MIN_FREE_RAM_GB:.2f} GB floor.")
                t0 = time.perf_counter()
                rec = _train_or_eval_one(
                    A,
                    arch,
                    s_idx,
                    selection_lock_sha256=lock_info["selection_sha256"],
                    candidate_audit_commit_sha=lock_info["candidate_audit_commit_sha"],
                )
                rec["secs"] = round(time.perf_counter() - t0, 2)
                pth.write_text(json.dumps(rec, indent=1), encoding="utf-8", newline="\n")
    return lock_info


def analyse(
    out_path: pathlib.Path = OUT_PATH,
    pred_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    raw_dir: pathlib.Path = RAW,
    pool_map: dict[int, dict] | None = None,
    null_draws: int = NULL_DRAWS,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    verify_source_hashes: bool = True,
) -> dict:
    """Summarize Spike 100 outcome strictly under pre-registered criteria and full 200-run grid."""
    if not pred_path.exists() or not lock_path.exists():
        raise AssertionError(f"Missing predictions or selection lock: {pred_path}, {lock_path}")
    P = json.loads(pred_path.read_text(encoding="utf-8"))
    L = json.loads(lock_path.read_text(encoding="utf-8"))
    lock_info = verify_selection_lock(P, L, pool_map=pool_map, verify_source_hashes=verify_source_hashes)

    if P["status"] != "READY" or len(P.get("selected_automata", [])) < MIN_ELIGIBLE_AUTOMATA:
        summary = {
            "spike": 100,
            "status": "UNDERPOWERED",
            "verdict": "NO VERDICT",
            "reason": P["reason"],
            "denominators": P.get("denominators"),
            "n_eligible": P["n_eligible"],
            "n_training_runs_executed": 0,
            "selection_lock_sha256": lock_info["selection_sha256"],
            "candidate_audit_commit_sha": lock_info["candidate_audit_commit_sha"],
        }
        out_path.write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
        return summary

    selected = P["selected_automata"]
    by_aid = {int(r["id"]): (pool_map[int(r["id"])] if pool_map is not None else r) for r in selected}
    ordered_aids = sorted(by_aid)
    if len(ordered_aids) != TARGET_N_AUTOMATA:
        raise AssertionError(f"Expected {TARGET_N_AUTOMATA} selected IDs, got {len(ordered_aids)}")

    raw_runs = []
    for fp in sorted(raw_dir.glob("*.json")):
        rec = json.loads(fp.read_text(encoding="utf-8"))
        validate_raw_record_provenance(rec, lock_info, source_desc=str(fp))
        raw_runs.append(rec)

    runs, grid_report = validate_and_complete_seed_grid(
        raw_runs, ordered_aids, seeds_per_arm=SEEDS_PER_ARM, expected_n_automata=TARGET_N_AUTOMATA
    )

    arms_out = {}
    for arch in ("gru_mlp", "gru_lin"):
        arm_runs = [r for r in runs if r["arch"] == arch]
        itt_by_aut: dict[int, list[dict]] = {aid: [] for aid in ordered_aids}
        fit_by_aut: dict[int, list[bool]] = {aid: [] for aid in ordered_aids}
        grams_by_aut: dict[int, list[np.ndarray | None]] = {aid: [] for aid in ordered_aids}
        sec_by_aut: dict[int, list[dict]] = {}
        for r in sorted(arm_runs, key=lambda x: (int(x["id"]), int(x["seed_idx"]))):
            aid = int(r["id"])
            ev = r["trained"]["eval"]
            gl_arr = np.asarray(r["trained"]["G_learned"], dtype=float) if r["gram_valid"] else None
            itt_by_aut[aid].append(ev)
            fit_by_aut[aid].append(bool(r["fit_ok"]) and bool(r["gram_valid"]))
            grams_by_aut[aid].append(gl_arr)
            if r["fit_ok"] and r["gram_valid"]:
                sec_by_aut.setdefault(aid, []).append(ev)

        itt_summaries = [S99.evaluate_automaton_held(itt_by_aut[aid], fit_flags=fit_by_aut[aid]) for aid in ordered_aids]
        itt_seed_evals = [itt_by_aut[aid] for aid in ordered_aids]
        obs_T = float(np.median([a["margin_D"] for a in itt_summaries]))
        aut_cands = []
        aut_pis = []
        for aid in ordered_aids:
            A = by_aid[aid]
            Dl = np.asarray(A["D"], dtype=int)
            O = np.asarray(A["O"], dtype=float)
            pi_occ = S81.visit_dist(Dl, int(A["s0"]), np.ones(Dl.shape[0]) / Dl.shape[0], T=SEQ_LEN, burn=BURN)
            aut_pis.append(pi_occ)
            aut_cands.append(AUDIT.candidate_matrices_from_ops(MP.master_operators(Dl, O, pi_occ)))
        agg_null_b = S99.aggregate_null_b_test(
            [grams_by_aut[aid] for aid in ordered_aids],
            aut_cands,
            aut_pis,
            observed_T=obs_T,
            reps=null_draws,
        )
        itt_verdict = S99.evaluate_aggregate_verdict(
            itt_summaries,
            itt_seed_evals,
            n_eligible=len(selected),
            bootstrap_reps=bootstrap_reps,
            aggregate_null_b=agg_null_b,
        )
        sec_summaries = [S99.evaluate_automaton_held(sec_by_aut[aid]) for aid in sorted(sec_by_aut)]
        sec_seed_evals = [sec_by_aut[aid] for aid in sorted(sec_by_aut)]
        arms_out[arch] = {
            "primary_intention_to_train": itt_verdict,
            "secondary_fit_qualified": S99.evaluate_aggregate_verdict(
                sec_summaries,
                sec_seed_evals,
                n_eligible=len(selected),
                bootstrap_reps=bootstrap_reps,
            ),
            "n_total_runs": len(arm_runs),
            "n_fit_ok_runs": sum(1 for r in arm_runs if r["fit_ok"]),
            "n_gram_valid_runs": sum(1 for r in arm_runs if r["gram_valid"]),
        }

    out = {
        "spike": 100,
        "status": "COMPLETE",
        "automaton_class": "NO_id",
        "denominators": {
            **(P.get("denominators") or {}),
            "n_selected_for_training": len(ordered_aids),
            "n_runs_expected": grid_report["n_expected"],
            "n_runs_present": grid_report["n_present"],
            "n_runs_missing": grid_report["n_missing"],
        },
        "arms": arms_out,
        "n_runs": len(runs),
        "grid_report": grid_report,
        "selection_lock_sha256": lock_info["selection_sha256"],
        "candidate_audit_commit_sha": lock_info["candidate_audit_commit_sha"],
    }
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=2))
    return out


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "analyse"
    {"predict": predict, "run": run, "analyse": analyse}[cmd]()


if __name__ == "__main__":
    main()
