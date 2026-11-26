"""Spike 99: Discriminating test of the two-sided Gramian (W_c + W_o) on irreversible automata.

Implements all pre-registered design & statistical rules (Work Order 2026-11-25 G-A +
ChatGPT independent review requirements 1-11):
  - Candidate target: A = W_c + W_o (unsmoothed two-sided Gramian).
  - Competitors B: W_o alone, G(lambda_0) with heat, output Gram o o^T, predictive-kernel top mode k1_top.
  - Eligibility: fresh irreversible automata from Spike 81's pool (excluding all prior uses
    and isomorphic duplicates, min(pi) > 1e-4) satisfying max_B cos(W_c + W_o, B) <= 0.80.
    If fewer than 20 qualify, DO NOT relax the threshold: report UNDERPOWERED / NO VERDICT.
  - Learners: primary GRU + 3-layer tanh MLP readout (5 seeds), secondary GRU + linear readout
    (5 seeds), identical budgets, plus untrained-GRU step-0 control; no best-seed selection.
  - Learned Gram: mu_s = E[h_t | s_t = s] on held-out trajectories, sqrt(pi)-weighted and centered,
    with within-state variance, between-state separation, R^2_state, and split-half stability.
  - Nulls (10,000 draws each, upper-tail p = (1 + #{null >= obs}) / (B + 1)):
      Null A: Gaussian stationary-weighted using actual GRU hidden_dim.
      Null B: spectrum-preserving random orthogonal rotations Q A Q^T in centred subspace.
      Null C: spectrum-matched diagonal baseline in centred subspace (secondary).
  - Aggregate inference: 10,000-rep hierarchical bootstrap (automata, then seeds) and
    Holm-Bonferroni corrected pairwise tests at alpha = 0.05.

Usage:
  python -m experiments.spike99 predict
  python -m experiments.spike99 run
  python -m experiments.spike99 analyse
"""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import json
import os
import pathlib
import subprocess
import sys
import time
from typing import Callable

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
from scipy.stats import wilcoxon

from experiments import master_principle as MP
from experiments import spike81 as S81
from experiments.audits import spike99_candidate_audit as AUDIT

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results"
RAW = RESULTS / "spike99_raw"
PRED_PATH = RESULTS / "spike99_predictions.json"
LOCK_PATH = RESULTS / "spike99_selection_lock.json"
OUT_PATH = RESULTS / "spike99.json"

TARGET_KEY = "WcWo"
COMPETITOR_KEYS = AUDIT.COMPETITORS_4
ALL_CAND_KEYS = AUDIT.CANDIDATES_5

MAX_COMP_THRESHOLD = 0.80
MIN_ELIGIBLE_AUTOMATA = 20
TARGET_N_AUTOMATA = 20

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


def available_ram_gb() -> float | None:
    """Return available physical RAM in GiB on Windows (or /proc/meminfo on POSIX)."""
    try:
        if os.name == "nt":
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return float(stat.ullAvailPhys / (1024.0 ** 3))
        elif pathlib.Path("/proc/meminfo").exists():
            for line in pathlib.Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemAvailable:"):
                    kb = float(line.split()[1])
                    return kb / (1024.0 ** 2)
    except Exception:
        return None
    return None


def make_gru_model(arch: str, L: int, k_out: int = 1, hidden_dim: int = HIDDEN_DIM):
    """Build GRU + nonlinear MLP (primary) or GRU + linear readout (secondary) with hidden_dim."""
    import torch

    nn = torch.nn
    if arch not in ("gru_mlp", "gru_lin"):
        raise ValueError(f"Unsupported arch: {arch}")

    class Spike99GRU(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.hidden_dim = hidden_dim
            self.e = nn.Embedding(L, EMB_DIM)
            self.r = nn.GRU(EMB_DIM, hidden_dim, batch_first=True)
            if arch == "gru_lin":
                self.h = nn.Linear(hidden_dim, k_out)
            else:
                self.h = nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.Tanh(),
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.Tanh(),
                    nn.Linear(hidden_dim, k_out),
                )

        def hidden(self, X: torch.Tensor) -> torch.Tensor:
            return self.r(self.e(X))[0]

        def forward(self, X: torch.Tensor) -> torch.Tensor:
            return self.h(self.hidden(X))

    return Spike99GRU()


def compute_learned_gram_and_stats(
    H: np.ndarray,
    ST: np.ndarray,
    pi: np.ndarray,
    burn: int = BURN,
) -> dict | None:
    """Compute mu_s = E[h_t | s_t = s], centered sqrt(pi) Gram, and geometry diagnostics."""
    H_post = np.asarray(H[:, burn:], dtype=float)
    ST_post = np.asarray(ST[:, burn:], dtype=int)
    d_hid = H_post.shape[-1]
    flatH = H_post.reshape(-1, d_hid)
    flatL = ST_post.ravel()
    m = len(pi)

    counts = np.bincount(flatL, minlength=m)
    if (counts == 0).any():
        return None

    Ce = np.stack([flatH[flatL == s].mean(axis=0) for s in range(m)])
    # Within-state variance (pi-weighted across states and empirical pooled)
    per_state_var = np.array([float(np.mean(np.sum((flatH[flatL == s] - Ce[s]) ** 2, axis=1))) for s in range(m)])
    var_within_pi = float(np.sum(pi * per_state_var))
    var_within_emp = float(np.mean(np.sum((flatH - Ce[flatL]) ** 2, axis=1)))

    # Centered sqrt(pi)-weighted state Gram: G_learned = X_perp @ X_perp.T
    W, one, _ = AUDIT.centred_subspace_basis(pi)
    mu_bar = (pi[:, None] * Ce).sum(axis=0)
    diffs = Ce - mu_bar
    var_between_pi = float(np.sum(pi[:, None] * (diffs ** 2)))
    X = W[:, None] * diffs
    centring_err = float(np.linalg.norm(one @ X))
    if centring_err >= 1e-8:
        raise AssertionError(f"Centring invariant violated: ||1_pi^T X||_2 = {centring_err:.2e}")
    X_perp = X - np.outer(one, one @ X)
    G_learned = 0.5 * ((X_perp @ X_perp.T) + (X_perp @ X_perp.T).T)
    if float(np.linalg.norm(G_learned)) < 1e-12:
        return None

    # Minimum pairwise centroid separation across distinct states
    pair_dists = [
        float(np.linalg.norm(Ce[i] - Ce[j]))
        for i in range(m)
        for j in range(i + 1, m)
    ]
    min_sep = float(min(pair_dists)) if pair_dists else 0.0
    r2_state = float(var_between_pi / max(var_between_pi + var_within_pi, 1e-12))

    # Split-half held-out stability across first vs second half of trajectories
    half = H_post.shape[0] // 2
    split_half_cos = None
    if half >= 1:
        def _half_gram(Hh: np.ndarray, Sh: np.ndarray) -> np.ndarray | None:
            fh = Hh.reshape(-1, d_hid)
            fs = Sh.ravel()
            if any(not (fs == s).any() for s in range(m)):
                return None
            ch = np.stack([fh[fs == s].mean(axis=0) for s in range(m)])
            mh = (pi[:, None] * ch).sum(axis=0)
            xh = W[:, None] * (ch - mh)
            xp = xh - np.outer(one, one @ xh)
            return 0.5 * ((xp @ xp.T) + (xp @ xp.T).T)

        G1 = _half_gram(H_post[:half], ST_post[:half])
        G2 = _half_gram(H_post[half:], ST_post[half:])
        if G1 is not None and G2 is not None:
            split_half_cos = AUDIT.cos_mat(G1, G2)

    return {
        "hidden_dim": int(d_hid),
        "Ce": Ce,
        "G_learned": G_learned,
        "var_within_pi": var_within_pi,
        "var_within_emp": var_within_emp,
        "var_between_pi": var_between_pi,
        "min_state_sep": min_sep,
        "r2_state": r2_state,
        "split_half_cos": split_half_cos,
    }


def evaluate_learned_gram(
    G_learned: np.ndarray,
    cand_mats: dict[str, np.ndarray],
    pi: np.ndarray,
    hidden_dim: int,
    draws: int = NULL_DRAWS,
    seed: int = 0,
) -> dict:
    """Score one learned Gram against all 5 candidates and Nulls A, B, C."""
    cosines = {k: AUDIT.cos_mat(G_learned, cand_mats[k]) for k in ALL_CAND_KEYS}
    obs_target = cosines[TARGET_KEY]
    max_comp = max(cosines[c] for c in COMPETITOR_KEYS)
    margin_D = float(obs_target - max_comp)

    null_a = AUDIT.null_a_gaussian_draws(cand_mats[TARGET_KEY], pi, hidden_dim=hidden_dim, draws=draws, seed=seed)
    null_b, null_b_diag = AUDIT.null_b_rotation_draws(
        G_learned, cand_mats[TARGET_KEY], pi, draws=draws, seed=seed + 100, return_diagnostics=True
    )
    null_c = AUDIT.null_c_diagonal_draws(G_learned, cand_mats[TARGET_KEY], pi, draws=draws, seed=seed + 200)

    return {
        "gram_valid": True,
        "cosines": cosines,
        "target_cos": obs_target,
        "max_competitor_cos": max_comp,
        "margin_D": margin_D,
        "null_A": {
            "median": float(np.median(null_a)),
            "p95": float(np.percentile(null_a, 95)),
            "p_upper": AUDIT.empirical_upper_p(null_a, obs_target),
        },
        "null_B": {
            "median": float(np.median(null_b)),
            "p95": float(np.percentile(null_b, 95)),
            "p_upper": AUDIT.empirical_upper_p(null_b, obs_target),
            "max_eig_err": null_b_diag["max_eig_err"],
            "min_rot_eig": null_b_diag["min_rot_eig"],
            "orig_min_eig": null_b_diag["orig_min_eig"],
            "psd_tol": null_b_diag["psd_tol"],
        },
        "null_C": {
            "median": float(np.median(null_c)),
            "p95": float(np.percentile(null_c, 95)),
            "p_upper": AUDIT.empirical_upper_p(null_c, obs_target),
        },
    }


def failed_seed_eval_stub() -> dict:
    """Explicit failed/degenerate seed entry kept in the primary intention-to-train analysis."""
    return {
        "gram_valid": False,
        "fit_ok": False,
        "cosines": {k: 0.0 for k in ALL_CAND_KEYS},
        "target_cos": 0.0,
        "max_competitor_cos": 0.0,
        "margin_D": 0.0,
        "null_A": {"median": 0.0, "p95": 1.0, "p_upper": 1.0},
        "null_B": {
            "median": 0.0,
            "p95": 1.0,
            "p_upper": 1.0,
            "max_eig_err": 0.0,
            "min_rot_eig": 0.0,
            "orig_min_eig": 0.0,
            "psd_tol": 0.0,
        },
        "null_C": {"median": 0.0, "p95": 1.0, "p_upper": 1.0},
    }


def normalize_seed_eval(seed_eval: dict | None, fit_ok: bool | None = None) -> dict:
    """Single canonical normalizer for every seed evaluation (missing/invalid -> failed stub)."""
    if not isinstance(seed_eval, dict) or not bool(seed_eval.get("gram_valid", True)):
        return failed_seed_eval_stub()
    cos = seed_eval.get("cosines")
    if not isinstance(cos, dict) or not all(k in cos for k in ALL_CAND_KEYS):
        return failed_seed_eval_stub()
    parsed_cos: dict[str, float] = {}
    for k in ALL_CAND_KEYS:
        try:
            v = float(cos[k])
        except (TypeError, ValueError):
            return failed_seed_eval_stub()
        if not np.isfinite(v):
            return failed_seed_eval_stub()
        parsed_cos[k] = v

    parsed_nulls: dict[str, dict] = {}
    for nk in ("null_A", "null_B", "null_C"):
        nd = seed_eval.get(nk)
        if not isinstance(nd, dict) or "p95" not in nd or "p_upper" not in nd:
            return failed_seed_eval_stub()
        try:
            p95 = float(nd["p95"])
            pu = float(nd["p_upper"])
            med = float(nd.get("median", 0.0))
        except (TypeError, ValueError):
            return failed_seed_eval_stub()
        if not (np.isfinite(p95) and np.isfinite(pu) and np.isfinite(med)):
            return failed_seed_eval_stub()
        parsed_nulls[nk] = {**nd, "median": med, "p95": p95, "p_upper": pu}

    eff_fit = bool(seed_eval.get("fit_ok", True)) if fit_ok is None else bool(fit_ok)
    obs_target = parsed_cos[TARGET_KEY]
    max_comp = max(parsed_cos[c] for c in COMPETITOR_KEYS)
    return {
        "gram_valid": True,
        "fit_ok": eff_fit,
        "cosines": parsed_cos,
        "target_cos": obs_target,
        "max_competitor_cos": max_comp,
        "margin_D": float(obs_target - max_comp),
        "null_A": parsed_nulls["null_A"],
        "null_B": parsed_nulls["null_B"],
        "null_C": parsed_nulls["null_C"],
    }


def _is_valid_finite_psd_gram(G_raw) -> tuple[bool, np.ndarray | None]:
    """Validate learned Gram matrix shape, finiteness, non-zero norm, and PSD tolerance."""
    if G_raw is None:
        return False, None
    try:
        arr = np.asarray(G_raw, dtype=float)
    except (TypeError, ValueError):
        return False, None
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1] or arr.shape[0] == 0:
        return False, None
    if not np.all(np.isfinite(arr)):
        return False, None
    sym = 0.5 * (arr + arr.T)
    if float(np.linalg.norm(sym)) < 1e-12:
        return False, None
    eigs = np.linalg.eigvalsh(sym)
    scale = max(float(np.max(np.abs(eigs))), 1e-12)
    if float(np.min(eigs)) < -1e-8 * scale:
        return False, None
    return True, arr


def normalize_seed_run_record(rec: dict) -> dict:
    """Single canonical normalizer for every seed run record (missing/invalid/failed unified)."""
    out = dict(rec)
    trained = dict(out.get("trained") or {})
    if out.get("missing_record", False):
        out["gram_valid"] = False
        out["fit_ok"] = False
        out["fit"] = 0.0
        trained["eval"] = failed_seed_eval_stub()
        trained["G_learned"] = None
        out["trained"] = trained
        return out

    gram_ok, gl_arr = _is_valid_finite_psd_gram(trained.get("G_learned"))
    raw_fit_ok = out.get("fit_ok", None)
    try:
        fit_val = float(out.get("fit", 0.0))
    except (TypeError, ValueError):
        fit_val = 0.0
    fit_ok_flag = bool(raw_fit_ok) and bool(np.isfinite(fit_val)) if raw_fit_ok is not None else False
    ev_norm = normalize_seed_eval(trained.get("eval"), fit_ok=fit_ok_flag)

    if not gram_ok or not ev_norm["gram_valid"]:
        out["gram_valid"] = False
        out["fit_ok"] = False
        trained["eval"] = failed_seed_eval_stub()
        trained["G_learned"] = None
        out["trained"] = trained
        return out

    out["gram_valid"] = True
    out["fit"] = fit_val
    out["fit_ok"] = fit_ok_flag
    trained["eval"] = ev_norm
    trained["G_learned"] = gl_arr.tolist() if isinstance(trained.get("G_learned"), list) else gl_arr
    out["trained"] = trained
    return out


def seed_eval_to_cos_row(seed_eval: dict | None) -> np.ndarray:
    """Extract ordered (5,) candidate cosine row via canonical normalize_seed_eval."""
    ev = normalize_seed_eval(seed_eval)
    if not ev["gram_valid"]:
        return np.zeros(len(ALL_CAND_KEYS), dtype=float)
    return np.array([float(ev["cosines"][k]) for k in ALL_CAND_KEYS], dtype=float)


def compute_automaton_D_batch(cos_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Canonical automaton statistic D_a = median_s(cos_{a,s,target}) - max_c median_s(cos_{a,s,c})."""
    arr = np.asarray(cos_arr, dtype=float)
    if arr.ndim < 2 or arr.shape[-2] == 0 or arr.shape[-1] != len(ALL_CAND_KEYS):
        raise ValueError(f"Expected trailing shape (n_seeds>=1, {len(ALL_CAND_KEYS)}), got {arr.shape}")
    med_cands = np.median(arr, axis=-2)
    margin_D = med_cands[..., 0] - np.max(med_cands[..., 1:], axis=-1)
    return med_cands, margin_D


def compute_automaton_D_from_cos_matrix(cos_mat: np.ndarray) -> tuple[np.ndarray, float]:
    """Single-automaton wrapper around compute_automaton_D_batch returning (med_cands_5, D_a)."""
    arr = np.asarray(cos_mat, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D cos_mat of shape (n_seeds, {len(ALL_CAND_KEYS)}), got ndim={arr.ndim}")
    med_cands, margin_D = compute_automaton_D_batch(arr)
    return med_cands, float(margin_D)


def aggregate_null_b_test(
    per_automaton_seed_grams: list[list[np.ndarray | None]],
    per_automaton_cand_mats: list[dict[str, np.ndarray]],
    per_automaton_pis: list[np.ndarray],
    observed_T: float | None = None,
    reps: int = NULL_DRAWS,
    seed: int = 9950,
) -> dict:
    """10,000 aggregate Null B replicates of T = median_a(D_a), preserving automaton/seed hierarchy."""
    rng = np.random.default_rng(seed)
    n_aut = len(per_automaton_seed_grams)
    if n_aut == 0:
        return {
            "T_observed": None,
            "T_observed_from_grams": None,
            "p_aggregate": 1.0,
            "reps": 0,
            "psd_diagnostics": {"orig_min_eig": 0.0, "min_rot_eig": 0.0, "max_eig_err": 0.0},
        }
    T_null = np.empty(reps, dtype=float)
    # Precompute subspace bases and normalized target/competitor projections per automaton
    aut_pre = []
    obs_cos_mats = []
    global_orig_min_eig = float("inf")
    any_valid_gram = False
    for a_idx in range(n_aut):
        pi = per_automaton_pis[a_idx]
        _, _, Q0 = AUDIT.centred_subspace_basis(pi)
        d = Q0.shape[1]
        cands = per_automaton_cand_mats[a_idx]
        C_subs = {}
        for k in ALL_CAND_KEYS:
            Cs = Q0.T @ (0.5 * (cands[k] + cands[k].T)) @ Q0
            nc = float(np.linalg.norm(Cs))
            C_subs[k] = (Cs / nc) if nc >= 1e-12 else np.zeros_like(Cs)
        seed_subs = []
        n_seeds_a = len(per_automaton_seed_grams[a_idx])
        obs_rows = np.zeros((n_seeds_a, len(ALL_CAND_KEYS)), dtype=float)
        for s_idx, G in enumerate(per_automaton_seed_grams[a_idx]):
            if G is None:
                seed_subs.append(None)
                continue
            G_arr = np.asarray(G, dtype=float)
            if not np.all(np.isfinite(G_arr)) or float(np.linalg.norm(G_arr)) < 1e-12:
                seed_subs.append(None)
                continue
            Gs = 0.5 * (Q0.T @ G_arr @ Q0 + (Q0.T @ G_arr @ Q0).T)
            ng = float(np.linalg.norm(Gs))
            if ng < 1e-12:
                seed_subs.append(None)
                continue
            Gs_norm = Gs / ng
            orig_eigs = np.linalg.eigvalsh(Gs_norm)
            orig_min = float(np.min(orig_eigs))
            scale = max(float(np.max(np.abs(orig_eigs))), 1e-12)
            psd_tol = -1e-8 * scale
            if orig_min < psd_tol:
                raise AssertionError(
                    f"Aggregate Null B PSD check failed on automaton={a_idx}, seed={s_idx}: "
                    f"min_eig={orig_min:.2e} < {psd_tol:.2e}"
                )
            any_valid_gram = True
            global_orig_min_eig = min(global_orig_min_eig, orig_min)
            seed_subs.append((Gs_norm, orig_eigs, psd_tol))
            for k_idx, k_name in enumerate(ALL_CAND_KEYS):
                obs_rows[s_idx, k_idx] = float(np.sum(Gs_norm * C_subs[k_name]))
        obs_cos_mats.append(obs_rows)
        aut_pre.append((d, C_subs, seed_subs))

    obs_T_computed = float(np.median([compute_automaton_D_from_cos_matrix(m)[1] for m in obs_cos_mats]))
    if observed_T is not None and abs(float(observed_T) - obs_T_computed) >= 1e-12:
        raise AssertionError(
            f"Supplied observed_T={observed_T:.12g} does not match Gram-derived T={obs_T_computed:.12g}"
        )
    if observed_T is None:
        observed_T = obs_T_computed

    max_eig_err = 0.0
    global_min_rot_eig = float("inf")
    chunk = 500
    for start in range(0, reps, chunk):
        b = min(chunk, reps - start)
        D_mat = np.empty((b, n_aut), dtype=float)
        for a_idx, (d, C_subs, seed_subs) in enumerate(aut_pre):
            n_seeds = len(seed_subs)
            seed_cands = np.zeros((b, n_seeds, len(ALL_CAND_KEYS)), dtype=float)
            for s_idx, item in enumerate(seed_subs):
                if item is None:
                    continue
                Gs_norm, orig_eigs, psd_tol = item
                U = AUDIT._haar_orthogonal_batch(rng, d, b)
                rot = np.einsum("bij,jk,blk->bil", U, Gs_norm, U)
                rot_sym = 0.5 * (rot + np.swapaxes(rot, 1, 2))
                rot_eigs = np.linalg.eigvalsh(rot_sym)
                batch_err = float(np.max(np.abs(rot_eigs - orig_eigs[None, :])))
                batch_min_rot = float(np.min(rot_eigs))
                max_eig_err = max(max_eig_err, batch_err)
                global_min_rot_eig = min(global_min_rot_eig, batch_min_rot)
                if batch_err >= 1e-7:
                    raise AssertionError(
                        f"Aggregate Null B eigenvalue preservation failed: max_eig_err={batch_err:.2e}"
                    )
                if batch_min_rot < psd_tol:
                    raise AssertionError(
                        f"Aggregate Null B rotated PSD check failed: min_rot_eig={batch_min_rot:.2e} < {psd_tol:.2e}"
                    )
                for k_idx, k_name in enumerate(ALL_CAND_KEYS):
                    seed_cands[:, s_idx, k_idx] = np.einsum("bij,ij->b", rot_sym, C_subs[k_name])
            _, D_mat[:, a_idx] = compute_automaton_D_batch(seed_cands)
        T_null[start : start + b] = np.median(D_mat, axis=1)

    if not any_valid_gram:
        global_orig_min_eig = 0.0
        global_min_rot_eig = 0.0
    p_agg = float((1 + int(np.sum(T_null >= observed_T))) / (reps + 1))
    return {
        "T_observed": float(observed_T),
        "T_observed_from_grams": obs_T_computed,
        "T_null_median": float(np.median(T_null)),
        "T_null_p95": float(np.percentile(T_null, 95)),
        "p_aggregate": p_agg,
        "reps": int(reps),
        "psd_diagnostics": {
            "orig_min_eig": float(global_orig_min_eig),
            "min_rot_eig": float(global_min_rot_eig),
            "max_eig_err": float(max_eig_err),
        },
    }


def holm_bonferroni(p_values: dict[str, float], alpha: float = 0.05) -> dict[str, dict]:
    """Step-down Holm-Bonferroni correction across a dictionary of named p-values."""
    ordered = sorted(p_values.items(), key=lambda kv: kv[1])
    m = len(ordered)
    out = {}
    running_max = 0.0
    rejected_so_far = True
    for idx, (name, p) in enumerate(ordered):
        adj = min(1.0, (m - idx) * p)
        running_max = max(running_max, adj)
        threshold = alpha / (m - idx)
        if rejected_so_far and p <= threshold:
            reject = True
        else:
            reject = False
            rejected_so_far = False
        out[name] = {
            "raw_p": float(p),
            "holm_adj_p": float(running_max),
            "threshold": float(threshold),
            "reject_at_alpha": bool(reject),
        }
    return out


def hierarchical_bootstrap_ci(
    per_automaton_seed_cos: list[np.ndarray | list[list[float]]],
    reps: int = BOOTSTRAP_REPS,
    seed: int = 9900,
) -> dict:
    """Hierarchical bootstrap (automata, then seeds) recomputing canonical D_a per replicate."""
    rng = np.random.default_rng(seed)
    n_aut = len(per_automaton_seed_cos)
    if n_aut == 0:
        return {"observed_median_D": None, "ci95_low": None, "ci95_high": None, "reps": 0}
    arrs = [np.asarray(xs, dtype=float) for xs in per_automaton_seed_cos]
    obs_med = float(np.median([compute_automaton_D_from_cos_matrix(a)[1] for a in arrs]))
    boot = np.empty(reps, dtype=float)
    shapes = {a.shape for a in arrs}
    if len(shapes) == 1:
        stacked = np.stack(arrs, axis=0)  # (n_aut, n_seeds, 5)
        n_seeds = stacked.shape[1]
        chunk = 1000
        for start in range(0, reps, chunk):
            b = min(chunk, reps - start)
            aut_idx = rng.integers(0, n_aut, size=(b, n_aut))
            s_idx = rng.integers(0, n_seeds, size=(b, n_aut, n_seeds))
            sampled = stacked[aut_idx[:, :, None], s_idx]
            _, d_boot = compute_automaton_D_batch(sampled)
            boot[start : start + b] = np.median(d_boot, axis=1)
    else:
        for r in range(reps):
            aut_idx = rng.integers(0, n_aut, size=n_aut)
            aut_meds = np.empty(n_aut, dtype=float)
            for j, ai in enumerate(aut_idx):
                s_arr = arrs[ai]
                s_idx = rng.integers(0, len(s_arr), size=len(s_arr))
                _, d_val = compute_automaton_D_from_cos_matrix(s_arr[s_idx])
                aut_meds[j] = d_val
            boot[r] = float(np.median(aut_meds))
    return {
        "observed_median_D": obs_med,
        "ci95_low": float(np.percentile(boot, 2.5)),
        "ci95_high": float(np.percentile(boot, 97.5)),
        "reps": int(reps),
    }


def evaluate_automaton_held(seed_evals: list[dict], fit_flags: list[bool] | None = None) -> dict:
    """Apply Commit-2 Section 8 intention-to-train per-automaton HELD criterion across 5 seeds."""
    if not seed_evals:
        return {"held": False, "n_seeds": 0}
    norm_evals = [
        normalize_seed_eval(r, fit_ok=(None if fit_flags is None else bool(ok)))
        for r, ok in zip(seed_evals, fit_flags if fit_flags is not None else [True] * len(seed_evals))
    ]
    eff_fit = [bool(r["fit_ok"]) and bool(r["gram_valid"]) for r in norm_evals]

    cos_mat = np.vstack([seed_eval_to_cos_row(r) for r in norm_evals])
    med_arr, margin_D = compute_automaton_D_from_cos_matrix(cos_mat)
    med_cands = {k: float(med_arr[idx]) for idx, k in enumerate(ALL_CAND_KEYS)}
    med_target = med_cands[TARGET_KEY]

    null_a_p95 = float(np.median([r["null_A"]["p95"] for r in norm_evals]))
    n_above_p95 = sum(
        1 for i, r in enumerate(norm_evals) if r["gram_valid"] and cos_mat[i, 0] > r["null_A"]["p95"]
    )
    n_null_b_sig = sum(
        1 for r in norm_evals if r["gram_valid"] and r["null_B"]["p_upper"] <= 0.05
    )
    n_fit_ok = sum(1 for ok in eff_fit if ok)
    med_null_a_p = float(np.median([r["null_A"]["p_upper"] for r in norm_evals]))
    med_null_b_p = float(np.median([r["null_B"]["p_upper"] for r in norm_evals]))

    c1 = med_target > null_a_p95 + 0.05
    c2 = n_above_p95 >= 4
    c3 = margin_D >= 0.05
    c4 = n_null_b_sig >= 4
    c5 = n_fit_ok >= 4
    return {
        "held": bool(c1 and c2 and c3 and c4 and c5),
        "n_seeds": len(norm_evals),
        "n_fit_ok": int(n_fit_ok),
        "med_target_cos": med_target,
        "med_competitor_cos": {c: med_cands[c] for c in COMPETITOR_KEYS},
        "margin_D": margin_D,
        "null_a_p95": null_a_p95,
        "n_seeds_above_null_a_p95": int(n_above_p95),
        "n_seeds_null_b_p_le_005": int(n_null_b_sig),
        "med_null_a_p": med_null_a_p,
        "med_null_b_p": med_null_b_p,
        "criteria_met": {
            "gt_p95_plus_005": bool(c1),
            "ge_4_of_5_null_a": bool(c2),
            "beats_all_by_005": bool(c3),
            "ge_4_of_5_null_b": bool(c4),
            "ge_4_of_5_fit_ok": bool(c5),
        },
    }


def evaluate_aggregate_verdict(
    automaton_summaries: list[dict],
    per_automaton_seed_evals: list[list[dict]],
    n_eligible: int = TARGET_N_AUTOMATA,
    bootstrap_reps: int = BOOTSTRAP_REPS,
    aggregate_null_b: dict | None = None,
) -> dict:
    """Apply Commit-2 Section 8 aggregate HELD / BROKEN / NEITHER / UNDERPOWERED verdict."""
    if n_eligible < MIN_ELIGIBLE_AUTOMATA or len(automaton_summaries) < MIN_ELIGIBLE_AUTOMATA:
        return {
            "verdict": "NO VERDICT",
            "status": "UNDERPOWERED",
            "reason": f"Only {n_eligible} eligible automata (< {MIN_ELIGIBLE_AUTOMATA} required; threshold max_B <= {MAX_COMP_THRESHOLD:.2f} not relaxed).",
            "n_eligible": int(n_eligible),
            "n_evaluated": len(automaton_summaries),
        }

    n_held = sum(1 for a in automaton_summaries if a["held"])
    seed_cos_mats = [np.vstack([seed_eval_to_cos_row(r) for r in se]) for se in per_automaton_seed_evals]
    boot = hierarchical_bootstrap_ci(seed_cos_mats, reps=bootstrap_reps)
    obs_T_from_summaries = float(np.median([a["margin_D"] for a in automaton_summaries]))
    if abs(obs_T_from_summaries - float(boot["observed_median_D"])) >= 1e-12:
        raise AssertionError(
            f"Statistic mismatch between automaton_summaries T={obs_T_from_summaries:.12g} "
            f"and bootstrap observed_median_D={boot['observed_median_D']:.12g}"
        )
    if aggregate_null_b is not None and aggregate_null_b.get("T_observed") is not None:
        t_agg = float(aggregate_null_b["T_observed"])
        if abs(obs_T_from_summaries - t_agg) >= 1e-12:
            raise AssertionError(
                f"Statistic mismatch between automaton_summaries T={obs_T_from_summaries:.12g} "
                f"and aggregate_null_b T_observed={t_agg:.12g}"
            )
    med_null_a_p = float(np.median([a["med_null_a_p"] for a in automaton_summaries]))
    p_aggregate_null_b = float(aggregate_null_b["p_aggregate"]) if aggregate_null_b is not None else float(
        np.median([a["med_null_b_p"] for a in automaton_summaries])
    )

    # Paired Wilcoxon tests (WcWo vs each competitor) across automata with Holm-Bonferroni alpha=0.05
    target_vec = np.array([a["med_target_cos"] for a in automaton_summaries], dtype=float)
    raw_pvals = {}
    for comp in COMPETITOR_KEYS:
        comp_vec = np.array([a["med_competitor_cos"][comp] for a in automaton_summaries], dtype=float)
        diff = target_vec - comp_vec
        if np.allclose(diff, 0.0):
            raw_pvals[comp] = 1.0
        else:
            _, pv = wilcoxon(diff, alternative="greater")
            raw_pvals[comp] = float(pv)
    holm = holm_bonferroni(raw_pvals, alpha=0.05)

    held_count_bar = max(14, int(np.ceil(0.70 * len(automaton_summaries))))
    is_held = (
        n_held >= held_count_bar
        and boot["observed_median_D"] >= 0.05
        and boot["ci95_low"] >= 0.05
        and p_aggregate_null_b <= 0.05
    )
    fails_agg_null = (med_null_a_p > 0.05) or (p_aggregate_null_b > 0.05)
    is_broken = (boot["ci95_high"] < 0.05) or (n_held <= 6 and fails_agg_null)

    verdict = "HELD" if is_held else ("BROKEN" if is_broken else "NEITHER")
    return {
        "verdict": verdict,
        "status": "COMPLETE",
        "n_eligible": int(n_eligible),
        "n_evaluated": len(automaton_summaries),
        "n_held": int(n_held),
        "held_count_bar": int(held_count_bar),
        "median_D": boot["observed_median_D"],
        "ci95_low": boot["ci95_low"],
        "ci95_high": boot["ci95_high"],
        "med_null_a_p": med_null_a_p,
        "p_aggregate_null_b": p_aggregate_null_b,
        "aggregate_null_b": aggregate_null_b,
        "holm_pairwise": holm,
    }


def select_stratified_20(eligible: list[dict], seed: int = 20261125) -> tuple[list[dict], list[int]]:
    """Deterministic stratified sampling of exactly 20 automata over (kind, m) strata."""
    rng = np.random.default_rng(seed)
    strata: dict[tuple[str, int], list[dict]] = {}
    for row in sorted(eligible, key=lambda r: int(r["id"])):
        strata.setdefault((str(row["kind"]), int(row["m"])), []).append(row)
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


def _git_head_sha() -> str:
    """Return current HEAD commit SHA of the repository."""
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _to_json_sig(sig) -> list | int:
    """Convert nested tuple automaton canonical signature cleanly into JSON-safe nested lists."""
    if isinstance(sig, (tuple, list)):
        return [_to_json_sig(x) for x in sig]
    return int(sig)


def canonical_selection_lock_hash(lock_payload: dict) -> str:
    """Compute SHA-256 hash over the immutable fields of spike99_selection_lock.json."""
    keys = (
        "spike",
        "status",
        "candidate_audit_commit_sha",
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
    pool: list[dict] | None = None,
    commit_sha: str | None = None,
    selection_seed: int = 20261125,
) -> dict:
    """Build an immutable cryptographic selection-lock artifact with canonical automaton signatures."""
    sha = commit_sha or _git_head_sha()
    eligible_inputs = [
        {"id": int(r["id"]), "kind": str(r["kind"]), "m": int(r["m"])}
        for r in sorted(eligible, key=lambda x: int(x["id"]))
    ]
    selected_ids = [int(r["id"]) for r in selected]
    selected_sigs = []
    if selected:
        if pool is None:
            pool = S81.build_pool()
        for r in selected:
            aid = int(r["id"])
            A = pool[aid]
            D = np.asarray(A["D"], dtype=int)
            O = np.asarray(A["O"], dtype=int)
            s0 = int(A["s0"])
            sig = AUDIT.canonical_aut_sig(D, O, s0)
            selected_sigs.append(
                {
                    "id": aid,
                    "kind": str(A["kind"]),
                    "m": int(D.shape[1]),
                    "L": int(D.shape[0] + 1),
                    "s0": s0,
                    "canonical_sig": _to_json_sig(sig),
                }
            )
    lock_payload = {
        "spike": 99,
        "status": str(status),
        "candidate_audit_commit_sha": sha,
        "selection_algorithm": "deterministic_stratified_round_robin_over_shuffled_strata",
        "strata_keys": ["kind", "m"],
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


def verify_selection_lock(pred_payload: dict, lock_payload: dict, pool: list[dict] | None = None) -> dict:
    """Verify immutable selection lock against predictions file, canonical signatures, and rebuilt pool."""
    expected_sha = canonical_selection_lock_hash(lock_payload)
    recorded_sha = str(lock_payload.get("selection_sha256", ""))
    if not recorded_sha or not hmac.compare_digest(expected_sha, recorded_sha):
        raise AssertionError(
            f"Selection lock SHA-256 mismatch: expected={expected_sha}, recorded={recorded_sha}"
        )

    status = str(lock_payload.get("status", ""))
    if str(pred_payload.get("status", "")) != status:
        raise AssertionError(f"Lock/prediction status mismatch: {status} vs {pred_payload.get('status')}")
    if pred_payload.get("selection_lock_sha256") and not hmac.compare_digest(
        str(pred_payload["selection_lock_sha256"]), recorded_sha
    ):
        raise AssertionError("Predictions file selection_lock_sha256 disagrees with selection lock.")
    if pred_payload.get("candidate_audit_commit_sha") and (
        str(pred_payload["candidate_audit_commit_sha"]) != str(lock_payload["candidate_audit_commit_sha"])
    ):
        raise AssertionError("Predictions file candidate_audit_commit_sha disagrees with selection lock.")

    if status != "READY":
        return {
            "status": status,
            "selection_sha256": recorded_sha,
            "candidate_audit_commit_sha": str(lock_payload["candidate_audit_commit_sha"]),
            "selected_ids": [],
        }

    selected_ids = [int(x) for x in lock_payload.get("selected_ids", [])]
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
    if sorted(int(x) for x in pred_payload.get("eligible_unselected_ids", [])) != sorted(
        int(x) for x in lock_payload.get("eligible_unselected_ids", [])
    ):
        raise AssertionError("eligible_unselected_ids mismatch between predictions and selection lock.")

    re_sel, re_unsel = select_stratified_20(
        lock_payload["eligible_strata_inputs"], seed=int(lock_payload["selection_seed"])
    )
    if [int(r["id"]) for r in re_sel] != selected_ids or re_unsel != lock_payload["eligible_unselected_ids"]:
        raise AssertionError("Deterministic stratified selection replay disagrees with selection lock.")

    if pool is None:
        pool = S81.build_pool()
    for entry in lock_payload["selected_signatures"]:
        aid = int(entry["id"])
        if not (0 <= aid < len(pool)):
            raise AssertionError(f"Selected ID {aid} out of bounds for rebuilt pool size {len(pool)}")
        A = pool[aid]
        D = np.asarray(A["D"], dtype=int)
        O = np.asarray(A["O"], dtype=int)
        s0 = int(A["s0"])
        if str(A["kind"]) != str(entry["kind"]) or int(D.shape[1]) != int(entry["m"]) or s0 != int(entry["s0"]):
            raise AssertionError(f"Metadata mismatch vs rebuilt pool on automaton id={aid}")
        rebuilt_sig = _to_json_sig(AUDIT.canonical_aut_sig(D, O, s0))
        if rebuilt_sig != entry["canonical_sig"]:
            raise AssertionError(f"Canonical automaton signature mismatch vs rebuilt pool on id={aid}")

    return {
        "status": "READY",
        "selection_sha256": recorded_sha,
        "candidate_audit_commit_sha": str(lock_payload["candidate_audit_commit_sha"]),
        "selected_ids": selected_ids,
    }


def predict(
    out_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    audit: dict | None = None,
    pool: list[dict] | None = None,
    commit_sha: str | None = None,
) -> dict:
    """Run eligibility & candidate-agreement audit and lock Spike 99 predictions + selection lock."""
    if audit is None:
        audit = AUDIT.run_full_audit(draws=NULL_DRAWS, hidden_dim=HIDDEN_DIM)
    pool_audit = audit["spike81_pool_audit"]
    eligible = pool_audit["eligible_automata"]

    if len(eligible) < MIN_ELIGIBLE_AUTOMATA:
        lock_payload = build_selection_lock(
            eligible=eligible,
            selected=[],
            unselected_ids=[],
            status="UNDERPOWERED",
            pool=pool,
            commit_sha=commit_sha,
        )
        payload = {
            "spike": 99,
            "status": "UNDERPOWERED",
            "max_competitor_threshold": MAX_COMP_THRESHOLD,
            "min_eligible_required": MIN_ELIGIBLE_AUTOMATA,
            "n_eligible": len(eligible),
            "n_fresh_irreversible_pi_ok": pool_audit["n_fresh_irreversible_pi_ok"],
            "n_rejected": pool_audit["n_rejected"],
            "reason": (
                f"0/{pool_audit['n_fresh_irreversible_pi_ok']} fresh irreversible automata in Spike 81's pool "
                f"satisfy max_B cos(W_c + W_o, B) <= {MAX_COMP_THRESHOLD:.2f} "
                f"(observed minimum across fresh irreversible pool = {pool_audit['fresh_irrev_min_max_comp_cos']:.4f}). "
                "Per pre-registered rule, threshold is NOT relaxed."
            ),
            "selected_ids": [],
            "selected_automata": [],
            "selection_lock_file": str(lock_path.relative_to(ROOT)).replace("\\", "/") if lock_path.is_relative_to(ROOT) else str(lock_path),
            "selection_lock_sha256": lock_payload["selection_sha256"],
            "candidate_audit_commit_sha": lock_payload["candidate_audit_commit_sha"],
            "audit_file": str(AUDIT.AUDIT_OUT.relative_to(ROOT)).replace("\\", "/"),
        }
    else:
        selected, unselected_ids = select_stratified_20(eligible, seed=20261125)
        lock_payload = build_selection_lock(
            eligible=eligible,
            selected=selected,
            unselected_ids=unselected_ids,
            status="READY",
            pool=pool,
            commit_sha=commit_sha,
        )
        payload = {
            "spike": 99,
            "status": "READY",
            "max_competitor_threshold": MAX_COMP_THRESHOLD,
            "min_eligible_required": MIN_ELIGIBLE_AUTOMATA,
            "selection_seed": 20261125,
            "n_eligible": len(eligible),
            "selected_ids": [int(r["id"]) for r in selected],
            "eligible_unselected_ids": unselected_ids,
            "selected_automata": selected,
            "selection_lock_file": str(lock_path.relative_to(ROOT)).replace("\\", "/") if lock_path.is_relative_to(ROOT) else str(lock_path),
            "selection_lock_sha256": lock_payload["selection_sha256"],
            "candidate_audit_commit_sha": lock_payload["candidate_audit_commit_sha"],
            "audit_file": str(AUDIT.AUDIT_OUT.relative_to(ROOT)).replace("\\", "/"),
        }

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock_payload, indent=1), encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"Spike 99 predict: status={payload['status']}, n_eligible={payload['n_eligible']}, lock_sha={lock_payload['selection_sha256'][:12]}")
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
    """Train one GRU arm (or step-0 untrained control) and evaluate learned Gram."""
    import torch

    nn = torch.nn
    D = np.asarray(A["D"], dtype=int)
    O = np.asarray(A["O"], dtype=float)
    s0 = int(A["s0"])
    m = D.shape[1]
    Dl = np.vstack([D, np.arange(m)[None]])
    L = Dl.shape[0]
    pi = S81.visit_dist(Dl, s0, np.ones(L) / L, T=SEQ_LEN, burn=BURN)
    ops = MP.master_operators(Dl, O, pi)
    cand_mats = AUDIT.candidate_matrices_from_ops(ops)

    seed = 99_000 + (0 if arch == "gru_mlp" else 10_000) + 100 * int(A["id"]) + seed_idx
    eval_seed = 99_000_000 + 100 * int(A["id"]) + seed_idx
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    mdl = make_gru_model(arch, L=L, k_out=1, hidden_dim=HIDDEN_DIM)

    def _collect_eval(offset: int):
        with torch.no_grad():
            Xv, Yv, _ = MP.fast_sample(Dl, O, s0, 500, 100, np.random.default_rng(eval_seed + offset))
            fit = float(((mdl(Xv) > 0).float() == Yv).float().mean())
            Xh, _, ST = MP.fast_sample(Dl, O, s0, 400, SEQ_LEN, np.random.default_rng(eval_seed + offset + 1_000_000))
            H = mdl.hidden(Xh).numpy()
        return fit, H, ST

    # Untrained control (step 0 before any optimizer step)
    mdl.eval()
    fit0, H0, ST0 = _collect_eval(500_000)
    stats0 = compute_learned_gram_and_stats(H0, ST0, pi, burn=BURN)
    eval0 = (
        evaluate_learned_gram(stats0["G_learned"], cand_mats, pi, hidden_dim=mdl.hidden_dim, draws=draws, seed=seed + 1)
        if stats0 is not None
        else None
    )

    # Trained run
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
    stats = compute_learned_gram_and_stats(H, ST, pi, burn=BURN)
    eval_tr = (
        evaluate_learned_gram(stats["G_learned"], cand_mats, pi, hidden_dim=mdl.hidden_dim, draws=draws, seed=seed + 2)
        if stats is not None
        else None
    )
    fit_ok = bool(fit >= FIT_GUARD)
    raw_rec = {
        "id": int(A["id"]),
        "arch": arch,
        "seed_idx": int(seed_idx),
        "seed": int(seed),
        "eval_seed": int(eval_seed),
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


def make_missing_seed_record(arch: str, aid: int, seed_idx: int) -> dict:
    """Create canonical failed-run record for a missing seed grid slot via shared normalizer."""
    return normalize_seed_run_record(
        {
            "id": int(aid),
            "arch": str(arch),
            "seed_idx": int(seed_idx),
            "seed": 99_000 + (0 if arch == "gru_mlp" else 10_000) + 100 * int(aid) + int(seed_idx),
            "eval_seed": 99_000_000 + 100 * int(aid) + int(seed_idx),
            "hidden_dim": HIDDEN_DIM,
            "fit": 0.0,
            "fit_ok": False,
            "missing_record": True,
            "untrained_control": {"fit": 0.0, "stats": None, "eval": None},
            "trained": {"stats": None, "eval": failed_seed_eval_stub(), "G_learned": None},
        }
    )


def validate_and_complete_seed_grid(
    runs: list[dict],
    selected_ids: list[int],
    seeds_per_arm: int = SEEDS_PER_ARM,
    strict_complete: bool = False,
    expected_n_automata: int = TARGET_N_AUTOMATA,
) -> tuple[list[dict], dict]:
    """Validate frozen (arch, id, seed_idx) grid, normalize all runs, and enforce exact postcondition."""
    ordered_ids = sorted(int(x) for x in selected_ids)
    if len(set(ordered_ids)) != len(ordered_ids):
        raise AssertionError(f"Duplicate IDs in selected_ids: {selected_ids}")
    if len(ordered_ids) != expected_n_automata:
        raise AssertionError(
            f"Expected {expected_n_automata} selected automata in grid, got {len(ordered_ids)}"
        )
    expected_keys = {
        (arch, aid, s_idx)
        for arch in ("gru_mlp", "gru_lin")
        for aid in ordered_ids
        for s_idx in range(seeds_per_arm)
    }
    by_key: dict[tuple[str, int, int], dict] = {}
    for rec in runs:
        key = (str(rec["arch"]), int(rec["id"]), int(rec["seed_idx"]))
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

    report = {
        "n_expected": len(expected_keys),
        "n_completed_grid": len(completed),
        "n_present": len(by_key),
        "n_missing": len(missing_keys),
        "missing_records": missing_keys,
    }
    return completed, report


def _validated_ready_selection(P: dict) -> tuple[list[dict], list[int]]:
    """Verify frozen READY selection lock in spike99_predictions.json."""
    selected = P.get("selected_automata", [])
    selected_ids = [int(x) for x in P.get("selected_ids", [])]
    if (
        len(selected) < MIN_ELIGIBLE_AUTOMATA
        or len(selected) != TARGET_N_AUTOMATA
        or len(set(selected_ids)) != TARGET_N_AUTOMATA
        or selected_ids != [int(x["id"]) for x in selected]
    ):
        raise AssertionError(
            f"Invalid READY selection lock: n_selected={len(selected)}, selected_ids={selected_ids}"
        )
    return selected, selected_ids


def run(
    pred_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    raw_dir: pathlib.Path = RAW,
    pool: list[dict] | None = None,
) -> dict | None:
    """Execute Spike 99 training ONLY if pre-registered eligibility >= 20 AND selection lock verify."""
    import torch

    torch.set_num_threads(1)
    if not pred_path.exists():
        predict(out_path=pred_path, lock_path=lock_path, pool=pool)
    if not lock_path.exists():
        raise AssertionError(f"Missing immutable selection lock artifact: {lock_path}")
    P = json.loads(pred_path.read_text(encoding="utf-8"))
    L = json.loads(lock_path.read_text(encoding="utf-8"))
    if P["status"] != "READY":
        verify_selection_lock(P, L, pool=pool)
        print(
            f"Spike 99 run aborted cleanly: status={P['status']}, "
            f"n_eligible={P['n_eligible']} (< {MIN_ELIGIBLE_AUTOMATA}). No training executed."
        )
        return None
    if pool is None:
        pool = S81.build_pool()
    lock_info = verify_selection_lock(P, L, pool=pool)
    selected, _ = _validated_ready_selection(P)

    free_gb = available_ram_gb()
    if free_gb is not None and free_gb < MIN_FREE_RAM_GB:
        raise RuntimeError(f"Aborted: free RAM {free_gb:.2f} GB < {MIN_FREE_RAM_GB:.2f} GB floor.")

    raw_dir.mkdir(parents=True, exist_ok=True)
    for arch in ("gru_mlp", "gru_lin"):
        for item in selected:
            aid = int(item["id"])
            A = {"id": aid, **pool[aid]}
            for s_idx in range(SEEDS_PER_ARM):
                free_gb = available_ram_gb()
                if free_gb is not None and free_gb < MIN_FREE_RAM_GB:
                    raise RuntimeError(f"Stopped mid-run: free RAM {free_gb:.2f} GB < {MIN_FREE_RAM_GB:.2f} GB floor.")
                pth = raw_dir / f"{arch}_{aid}_{s_idx}.json"
                if pth.exists():
                    continue
                t0 = time.perf_counter()
                rec = _train_or_eval_one(
                    A,
                    arch,
                    s_idx,
                    selection_lock_sha256=lock_info["selection_sha256"],
                    candidate_audit_commit_sha=lock_info["candidate_audit_commit_sha"],
                )
                rec["secs"] = round(time.perf_counter() - t0, 2)
                pth.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return lock_info


def analyse(
    out_path: pathlib.Path = OUT_PATH,
    pred_path: pathlib.Path = PRED_PATH,
    lock_path: pathlib.Path = LOCK_PATH,
    raw_dir: pathlib.Path = RAW,
    pool: list[dict] | None = None,
    null_draws: int = NULL_DRAWS,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> dict:
    """Summarize Spike 99 outcome strictly under pre-registered criteria and full 200-run grid."""
    if not pred_path.exists():
        predict(out_path=pred_path, lock_path=lock_path, pool=pool)
    if not lock_path.exists():
        raise AssertionError(f"Missing immutable selection lock artifact: {lock_path}")
    P = json.loads(pred_path.read_text(encoding="utf-8"))
    L = json.loads(lock_path.read_text(encoding="utf-8"))
    audit = json.loads(AUDIT.AUDIT_OUT.read_text(encoding="utf-8")) if AUDIT.AUDIT_OUT.exists() else None

    if P["status"] != "READY" or len(P.get("selected_automata", [])) < MIN_ELIGIBLE_AUTOMATA:
        lock_info = verify_selection_lock(P, L, pool=pool)
        summary = {
            "spike": 99,
            "status": "UNDERPOWERED",
            "verdict": "NO VERDICT",
            "reason": P["reason"],
            "n_eligible": P["n_eligible"],
            "n_training_runs_executed": 0,
            "selection_lock_sha256": lock_info["selection_sha256"],
            "candidate_audit_commit_sha": lock_info["candidate_audit_commit_sha"],
            "pr12_candidate_agreement_summary": (
                audit["pr12_candidate_agreement_audit"]["median_pairwise_diag"] if audit else None
            ),
            "pr12_null_summary": (
                audit["pr12_candidate_agreement_audit"]["summary_nulls"] if audit else None
            ),
            "pool_audit_summary": (
                {
                    k: audit["spike81_pool_audit"][k]
                    for k in (
                        "pool_size",
                        "max_comp_threshold",
                        "n_used_excluded",
                        "n_isomorphic_duplicates",
                        "n_fresh_irreversible_all",
                        "n_fresh_irreversible_pi_ok",
                        "low_pi_threshold_effect",
                        "n_eligible",
                        "n_rejected",
                        "reason_counts",
                        "fresh_irrev_min_max_comp_cos",
                        "fresh_irrev_min_cos_WcWo_Wo",
                        "fresh_irrev_min_max_comp_excl_G",
                        "all_irrev_incl_used_min_max_comp_cos",
                        "diag_fresh_unit_norm_le_080_count",
                    )
                }
                if audit
                else None
            ),
        }
        out_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")
        print(json.dumps(summary, indent=2))
        return summary

    if pool is None:
        pool = S81.build_pool()
    lock_info = verify_selection_lock(P, L, pool=pool)
    selected, selected_ids = _validated_ready_selection(P)
    ordered_aids = sorted(selected_ids)
    if len(ordered_aids) != TARGET_N_AUTOMATA:
        raise AssertionError(f"Expected {TARGET_N_AUTOMATA} selected IDs, got {len(ordered_aids)}")

    raw_runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(raw_dir.glob("*.json")) if not f.name.endswith("_g.npy")]
    for rec in raw_runs:
        if rec.get("selection_lock_sha256") and rec["selection_lock_sha256"] != lock_info["selection_sha256"]:
            raise AssertionError("Raw training record carries a different selection_lock_sha256 than current lock.")
    runs, grid_report = validate_and_complete_seed_grid(
        raw_runs, ordered_aids, seeds_per_arm=SEEDS_PER_ARM, expected_n_automata=TARGET_N_AUTOMATA
    )
    if len(runs) != 2 * TARGET_N_AUTOMATA * SEEDS_PER_ARM:
        raise AssertionError(f"Expected 200 completed grid records, got {len(runs)}")

    arms_out = {}
    for arch in ("gru_mlp", "gru_lin"):
        arm_runs = [r for r in runs if r["arch"] == arch]
        if len(arm_runs) != TARGET_N_AUTOMATA * SEEDS_PER_ARM:
            raise AssertionError(f"Expected 100 records for arm={arch}, got {len(arm_runs)}")
        # Primary intention-to-train analysis: retain ALL 5 seeds per automaton on full 200-run grid.
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
        if len(itt_by_aut) != TARGET_N_AUTOMATA or any(len(itt_by_aut[aid]) != SEEDS_PER_ARM for aid in ordered_aids):
            raise AssertionError(f"Postcondition failed for arm={arch}: incomplete automaton/seed grid")
        itt_summaries = [
            evaluate_automaton_held(itt_by_aut[aid], fit_flags=fit_by_aut[aid])
            for aid in ordered_aids
        ]
        if len(itt_summaries) != TARGET_N_AUTOMATA:
            raise AssertionError(f"Expected {TARGET_N_AUTOMATA} ITT summaries, got {len(itt_summaries)}")
        itt_seed_evals = [itt_by_aut[aid] for aid in ordered_aids]
        obs_T = float(np.median([a["margin_D"] for a in itt_summaries]))
        aut_cands = []
        aut_pis = []
        for aid in ordered_aids:
            A = pool[aid]
            D = np.asarray(A["D"], dtype=int)
            O = np.asarray(A["O"], dtype=float)
            Dl = np.vstack([D, np.arange(D.shape[1])[None]])
            pi = S81.visit_dist(Dl, int(A["s0"]), np.ones(Dl.shape[0]) / Dl.shape[0], T=SEQ_LEN, burn=BURN)
            aut_pis.append(pi)
            aut_cands.append(AUDIT.candidate_matrices_from_ops(MP.master_operators(Dl, O, pi)))
        agg_null_b = aggregate_null_b_test(
            [grams_by_aut[aid] for aid in ordered_aids],
            aut_cands,
            aut_pis,
            observed_T=obs_T,
            reps=null_draws,
        )
        if abs(obs_T - float(agg_null_b["T_observed_from_grams"])) >= 1e-12:
            raise AssertionError(
                f"Statistic mismatch in analyse({arch}): obs_T={obs_T:.12g} vs "
                f"T_observed_from_grams={agg_null_b['T_observed_from_grams']:.12g}"
            )
        itt_verdict = evaluate_aggregate_verdict(
            itt_summaries,
            itt_seed_evals,
            n_eligible=len(selected),
            bootstrap_reps=bootstrap_reps,
            aggregate_null_b=agg_null_b,
        )
        sec_summaries = [evaluate_automaton_held(sec_by_aut[aid]) for aid in sorted(sec_by_aut)]
        sec_seed_evals = [sec_by_aut[aid] for aid in sorted(sec_by_aut)]
        arms_out[arch] = {
            "primary_intention_to_train": itt_verdict,
            "secondary_fit_qualified": evaluate_aggregate_verdict(
                sec_summaries,
                sec_seed_evals,
                n_eligible=len(selected),
                bootstrap_reps=bootstrap_reps,
            ),
            "n_total_runs": len(arm_runs),
            "n_fit_ok_runs": sum(1 for r in arm_runs if r["fit_ok"]),
        }

    out = {
        "spike": 99,
        "status": "COMPLETE",
        "arms": arms_out,
        "n_runs": len(runs),
        "grid_report": grid_report,
        "selection_lock_sha256": lock_info["selection_sha256"],
        "candidate_audit_commit_sha": lock_info["candidate_audit_commit_sha"],
    }
    out_path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return out


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "analyse"
    {"predict": predict, "run": run, "analyse": analyse}[cmd]()


if __name__ == "__main__":
    main()
