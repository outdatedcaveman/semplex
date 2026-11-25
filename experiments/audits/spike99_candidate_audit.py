"""Spike 99 blocking candidate-agreement audit and Spike 81 pool eligibility census.

Implements ChatGPT independent review requirements (2026-11-25, PR #12 / Task 150):
  1. Full pairwise candidate cosine matrices among:
       - WcWo   : W_c + W_o (unsmoothed two-sided Gramian)
       - Wo     : W_o alone (forward observability Gramian)
       - G      : G(lambda_0) with kinetic heat kernel
       - o      : o o^T (instantaneous centered output Gram)
       - k1_top : k_{1,w} k_{1,w}^T (rank-1 outer product of predictive-kernel top mode)
     (plus k1_full = full t >= 1 predictive kernel as an auxiliary diagnostic).
  2. Multi-null evaluation on PR #12's 12 monoids (10,000 draws each, upper-tail
     empirical p = (1 + #{null >= obs}) / (B + 1)):
       - Null A: Gaussian stationary-weighted null using actual GRU hidden dim (64).
       - Null B: Spectrum-preserving random orthogonal rotations Q A Q^T in centred subspace.
       - Null C: Spectrum-matched diagonal baseline in centred subspace (secondary).
  3. Full eligibility and rejection audit across all 600 automata in Spike 81's pool:
       - Excludes every automaton already used across Spikes 81, 83, 84, 87 and
         master_principle{,_mech,_transformer,_tf_causal}.
       - Excludes isomorphic duplicates via canonical (D, O, s0) signature.
       - Filters to irreversible automata with stationary support min(pi) > 1e-4.
       - Eligibility bar (never relaxed): max_{B != WcWo} cos(WcWo, B) <= 0.80.
       - Stratifies all rejected/eligible fresh irreversible automata by #states,
         stationary entropy, spectral gap, irreversibility, Gramian ranks, and
         output complexity.

Run:
  python -m experiments.audits.spike99_candidate_audit
"""

from __future__ import annotations

import json
import math
import pathlib
from collections import Counter, deque
from itertools import permutations

import numpy as np

from experiments import master_principle as MP
from experiments import spike81 as S81
from experiments import spike84 as S84

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "experiments" / "results"
AUDIT_OUT = RESULTS / "spike99_candidate_audit.json"

CANDIDATES_5 = ("WcWo", "Wo", "G", "o", "k1_top")
COMPETITORS_4 = ("Wo", "G", "o", "k1_top")
CANDIDATES_DIAG = ("WcWo", "Wo", "G", "o", "k1_top", "k1_full")

PRIOR_POOL_PRED_FILES = (
    ("spike81", "spike81_predictions.json"),
    ("spike81_results", "spike81.json"),
    ("spike83", "spike83_predictions.json"),
    ("spike84", "spike84_predictions.json"),
    ("spike87", "spike87_predictions.json"),
    ("master_principle", "master_principle_predictions.json"),
    ("master_principle_mech", "master_principle_mech_predictions.json"),
    ("master_principle_transformer", "master_principle_transformer_predictions.json"),
    ("master_principle_tf_causal", "master_principle_tf_causal_predictions.json"),
)
PRIOR_POOL_RAW_DIRS = (
    ("spike81_raw", "spike81_raw"),
    ("spike84_raw", "spike84_raw"),
    ("spike87_raw", "spike87_raw"),
    ("master_principle_raw", "master_principle_raw"),
    ("master_principle_mech_raw", "master_principle_mech_raw"),
)


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    """Frobenius cosine similarity between two matrices."""
    A = np.asarray(A, dtype=float)
    B = np.asarray(B, dtype=float)
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def empirical_upper_p(null_vals: np.ndarray, obs: float) -> float:
    """Exact Monte Carlo upper-tail p-value: (1 + #{null >= obs}) / (B + 1)."""
    arr = np.asarray(null_vals, dtype=float)
    return float((1 + int(np.sum(arr >= obs))) / (len(arr) + 1))


def centred_subspace_basis(pi: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (W = sqrt(pi), one = W/||W||, Q0 with shape (m, m-1) spanning im(P_perp))."""
    pi = np.asarray(pi, dtype=float)
    m = len(pi)
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)
    evals, evecs = np.linalg.eigh(Pperp)
    # Keep the m - 1 unit-eigenvalue eigenvectors spanning im(P_perp).
    Q0 = evecs[:, evals > 0.5]
    return W, one, Q0


def null_a_gaussian_draws(
    target: np.ndarray,
    pi: np.ndarray,
    hidden_dim: int,
    draws: int = 10000,
    seed: int = 0,
) -> np.ndarray:
    """Null A: stationary-weighted centered Gaussian Grams using actual hidden_dim."""
    rng = np.random.default_rng(seed)
    m = len(pi)
    W, one, _ = centred_subspace_basis(pi)
    Pperp = np.eye(m) - np.outer(one, one)
    T_flat = np.asarray(target, dtype=float).ravel()
    T_norm = float(np.linalg.norm(T_flat))
    if T_norm < 1e-12:
        return np.zeros(draws, dtype=float)
    out = np.empty(draws, dtype=float)
    # Process in chunks to keep RAM tiny on 8 GB hosts.
    chunk = 500
    for start in range(0, draws, chunk):
        b = min(chunk, draws - start)
        Z = rng.normal(size=(b, m, hidden_dim))
        X = Pperp[None, :, :] @ (W[None, :, None] * Z)
        G_null = np.einsum("bmk,bnk->bmn", X, X)
        gn = np.linalg.norm(G_null.reshape(b, -1), axis=1)
        dots = G_null.reshape(b, -1) @ T_flat
        out[start : start + b] = np.where(gn > 1e-12, dots / (gn * T_norm), 0.0)
    return out


def _haar_orthogonal_batch(rng: np.random.Generator, d: int, b: int) -> np.ndarray:
    """Sample b Haar-distributed orthogonal matrices in O(d) via sign-corrected QR."""
    Z = rng.normal(size=(b, d, d))
    Q, R = np.linalg.qr(Z)
    diag = np.diagonal(R, axis1=1, axis2=2)
    signs = np.where(diag >= 0.0, 1.0, -1.0)
    return Q * signs[:, None, :]


def null_b_rotation_draws(
    source_gram: np.ndarray,
    target: np.ndarray,
    pi: np.ndarray,
    draws: int = 10000,
    seed: int = 1,
) -> np.ndarray:
    """Null B: spectrum-preserving random orientations Q A Q^T inside im(P_perp)."""
    rng = np.random.default_rng(seed)
    _, _, Q0 = centred_subspace_basis(pi)
    d = Q0.shape[1]
    A_sub = Q0.T @ (0.5 * (source_gram + source_gram.T)) @ Q0
    T_sub = Q0.T @ (0.5 * (target + target.T)) @ Q0
    na = float(np.linalg.norm(A_sub))
    nt = float(np.linalg.norm(T_sub))
    if na < 1e-12 or nt < 1e-12 or d == 0:
        return np.zeros(draws, dtype=float)
    out = np.empty(draws, dtype=float)
    chunk = 1000
    for start in range(0, draws, chunk):
        b = min(chunk, draws - start)
        U = _haar_orthogonal_batch(rng, d, b)
        rot = np.einsum("bij,jk,blk->bil", U, A_sub, U)
        dots = np.einsum("bij,ij->b", rot, T_sub)
        out[start : start + b] = dots / (na * nt)
    return out


def null_c_diagonal_draws(
    source_gram: np.ndarray,
    target: np.ndarray,
    pi: np.ndarray,
    draws: int = 10000,
    seed: int = 2,
) -> np.ndarray:
    """Null C (secondary): spectrum-matched diagonal matrices in random centred coordinates."""
    rng = np.random.default_rng(seed)
    _, _, Q0 = centred_subspace_basis(pi)
    d = Q0.shape[1]
    A_sub = Q0.T @ (0.5 * (source_gram + source_gram.T)) @ Q0
    T_sub = Q0.T @ (0.5 * (target + target.T)) @ Q0
    evals = np.linalg.eigvalsh(A_sub)
    na = float(np.linalg.norm(evals))
    nt = float(np.linalg.norm(T_sub))
    if na < 1e-12 or nt < 1e-12 or d == 0:
        return np.zeros(draws, dtype=float)
    t_diag = np.diag(T_sub)
    # Random permutations of eigenvalues along the canonical centred basis (diagonal in Q0 frame).
    out = np.empty(draws, dtype=float)
    for i in range(draws):
        perm = rng.permutation(d)
        out[i] = float(np.dot(evals[perm], t_diag) / (na * nt))
    return out


def canonical_aut_sig(D: np.ndarray, O: np.ndarray | list[int], s0: int) -> tuple:
    """Canonical automaton signature up to state isomorphism (BFS from s0) and letter permutation."""
    D_arr = np.asarray(D, dtype=int)
    O_arr = np.asarray(O, dtype=int)
    k, m = D_arr.shape
    best = None
    for lperm in permutations(range(k)):
        mapping = {int(s0): 0}
        order = [int(s0)]
        q = deque([int(s0)])
        while q:
            u = q.popleft()
            for a in lperm:
                v = int(D_arr[a, u])
                if v not in mapping:
                    mapping[v] = len(order)
                    order.append(v)
                    q.append(v)
        if len(order) < m:
            for u in range(m):
                if u not in mapping:
                    mapping[u] = len(order)
                    order.append(u)
        Dc = tuple(tuple(mapping[int(D_arr[a, u])] for u in order) for a in lperm)
        Oc = tuple(int(O_arr[u]) for u in order)
        sig = (m, k, Dc, Oc)
        if best is None or sig < best:
            best = sig
    return best


def collect_used_pool_ids(results_dir: pathlib.Path = RESULTS) -> dict[int, list[str]]:
    """Map every Spike-81 pool ID used in prior spikes/runs to its source artifact(s)."""
    used: dict[int, set[str]] = {}

    def record(obj, tag: str) -> None:
        if isinstance(obj, dict):
            for key in ("id", "aid"):
                if key in obj and isinstance(obj[key], int):
                    used.setdefault(obj[key], set()).add(tag)
            for v in obj.values():
                record(v, tag)
        elif isinstance(obj, list):
            for v in obj:
                record(v, tag)

    for tag, fn in PRIOR_POOL_PRED_FILES:
        fp = results_dir / fn
        if fp.exists():
            record(json.loads(fp.read_text(encoding="utf-8", errors="ignore")), tag)

    for tag, rd in PRIOR_POOL_RAW_DIRS:
        rp = results_dir / rd
        if rp.exists():
            for fp in rp.glob("*.json"):
                try:
                    d = json.loads(fp.read_text(encoding="utf-8", errors="ignore"))
                    for key in ("id", "aid"):
                        if key in d and isinstance(d[key], int):
                            used.setdefault(d[key], set()).add(tag)
                except Exception:
                    pass

    return {k: sorted(v) for k, v in sorted(used.items())}


def candidate_matrices_from_ops(ops: dict) -> dict[str, np.ndarray]:
    """Extract the 5 competing Gram matrices plus full k1 diagnostic matrix."""
    k1_w = np.asarray(ops["k1_w"], dtype=float)
    return {
        "WcWo": np.asarray(ops["WcWo_noheat"], dtype=float),
        "Wo": np.asarray(ops["Wo"], dtype=float),
        "G": np.asarray(ops["G"], dtype=float),
        "o": np.asarray(ops["o"], dtype=float),
        "k1_top": np.outer(k1_w, k1_w),
        "k1_full": np.asarray(ops["k1"], dtype=float),
    }


def pairwise_cosine_matrix(mats: dict[str, np.ndarray], keys: tuple[str, ...]) -> dict[str, dict[str, float]]:
    """Compute the symmetric pairwise cosine dictionary across candidate names."""
    return {a: {b: cos_mat(mats[a], mats[b]) for b in keys} for a in keys}


def automaton_stratification_metrics(
    Dl: np.ndarray, O: np.ndarray, pi: np.ndarray, ops: dict, hs: dict
) -> dict:
    """Compute structural, spectral, irreversibility, rank, and output complexity metrics."""
    L, m = Dl.shape
    D_act = Dl[:-1]  # Exclude the appended stay-identity letter when counting non-bijective action maps.
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)

    # Markov transition matrix M = (1/L) sum_a P_a
    M = np.zeros((m, m), dtype=float)
    Ts = []
    for a in range(L):
        Pa = np.zeros((m, m), dtype=float)
        for q in range(m):
            Pa[q, Dl[a, q]] = 1.0
        M += Pa / L
        Ts.append((W[:, None] * Pa) / W[None, :])
    M_tilde = sum(Ts) / L
    eigs_M = np.linalg.eigvals(M)
    mags = np.sort(np.abs(eigs_M))[::-1]
    spectral_gap = float(1.0 - mags[1]) if len(mags) > 1 else 0.0
    rev_defect = float(np.linalg.norm(M_tilde - M_tilde.T) / max(np.linalg.norm(M_tilde), 1e-12))

    Lkin = np.asarray(ops["Lkin"], dtype=float)
    lkin_sub = np.linalg.eigvalsh(Lkin)
    lkin_pos = lkin_sub[lkin_sub > 1e-10]
    dirichlet_gap = float(lkin_pos.min()) if len(lkin_pos) else 0.0

    # Stationary entropy (bits)
    pi_pos = pi[pi > 0.0]
    h_pi_bits = float(-np.sum(pi_pos * np.log2(pi_pos)))
    h_pi_norm = float(h_pi_bits / math.log2(m)) if m > 1 else 0.0

    # Output stationary entropy (bits) & kinetic sensitivity of o
    p1 = float(np.sum(pi[np.asarray(O, int) == 1]))
    p0 = 1.0 - p1
    h_out_bits = float(sum(-p * math.log2(p) for p in (p0, p1) if p > 1e-12))
    o_mat = np.asarray(ops["o"], dtype=float)
    o_kin = float(np.trace(o_mat @ Lkin) / max(np.trace(o_mat), 1e-12))

    # Irreversibility metrics on action letters (excluding appended identity)
    im_fracs = [len(set(D_act[a].tolist())) / m for a in range(D_act.shape[0])]
    n_nonbij = sum(len(set(D_act[a].tolist())) < m for a in range(D_act.shape[0]))

    def mat_rank(A: np.ndarray) -> int:
        s = np.linalg.svd(A, compute_uv=False)
        return int(np.sum(s > 1e-9 * max(float(s.max()), 1e-12)))

    return {
        "m": int(m),
        "L": int(L),
        "pi_min": float(pi.min()),
        "pi_entropy_bits": h_pi_bits,
        "pi_entropy_norm": h_pi_norm,
        "markov_spectral_gap": spectral_gap,
        "dirichlet_gap": dirichlet_gap,
        "n_nonbij_letters": int(n_nonbij),
        "min_image_frac": float(min(im_fracs)),
        "rev_defect": rev_defect,
        "wc_over_wo": float(ops["wc_over_wo"]),
        "cos_Wc_Wo": cos_mat(ops["Wc"], ops["Wo"]),
        "rank_WcWo": mat_rank(ops["WcWo_noheat"]),
        "rank_Wo": mat_rank(ops["Wo"]),
        "rank_Wc": mat_rank(ops["Wc"]),
        "rank_G": mat_rank(ops["G"]),
        "rank_o": mat_rank(o_mat),
        "rank_k1_full": mat_rank(ops["k1"]),
        "out_p1": p1,
        "out_entropy_bits": h_out_bits,
        "o_kin": o_kin,
        "dimO": int(hs["dimO"]),
        "dimR": int(hs["dimR"]),
        "dimH": int(hs["dimH"]),
    }


def audit_pr12_monoids(
    pred_path: pathlib.Path = RESULTS / "master_principle_predictions.json",
    hidden_dim: int = 64,
    draws: int = 10000,
) -> dict:
    """Compute the missing pairwise candidate cosines and multi-null distributions for PR #12."""
    p = json.loads(pred_path.read_text(encoding="utf-8"))
    per_monoid = []
    for idx, M in enumerate(p["monoids"]):
        pi = np.asarray(M["pi"], dtype=float)
        mats = candidate_matrices_from_ops(M)
        pw_5 = pairwise_cosine_matrix(mats, CANDIDATES_5)
        pw_diag = pairwise_cosine_matrix(mats, CANDIDATES_DIAG)
        G = mats["G"]
        WcWo = mats["WcWo"]
        # Null A (Gaussian stationary-weighted, actual GRU hidden_dim) against G and WcWo.
        null_a_G = null_a_gaussian_draws(G, pi, hidden_dim=hidden_dim, draws=draws, seed=1000 + idx)
        null_a_WcWo = null_a_gaussian_draws(WcWo, pi, hidden_dim=hidden_dim, draws=draws, seed=2000 + idx)
        # Note: per-seed G_learned is absent on master; Null B here measures spectrum-preserving
        # self-orientation cos(T, Q T Q^T) in the centred subspace as a structural null benchmark.
        null_b_G = null_b_rotation_draws(G, G, pi, draws=draws, seed=3000 + idx)
        null_b_WcWo = null_b_rotation_draws(WcWo, WcWo, pi, draws=draws, seed=4000 + idx)
        null_c_WcWo = null_c_diagonal_draws(WcWo, WcWo, pi, draws=draws, seed=5000 + idx)
        max_comp_wcwo = max(pw_5["WcWo"][c] for c in COMPETITORS_4)
        max_comp_no_g = max(pw_5["WcWo"][c] for c in ("Wo", "o", "k1_top"))
        per_monoid.append(
            {
                "id": int(M["id"]),
                "kind": M["kind"],
                "m": int(M["m"]),
                "pairwise_5": pw_5,
                "pairwise_diag": pw_diag,
                "max_competitor_cos_WcWo": float(max_comp_wcwo),
                "max_competitor_cos_WcWo_excl_G": float(max_comp_no_g),
                "cos_Wc_Wo": cos_mat(M["Wc"], M["Wo"]),
                "wc_over_wo": float(M["wc_over_wo"]),
                "null_A_G": {"median": float(np.median(null_a_G)), "p95": float(np.percentile(null_a_G, 95))},
                "null_A_WcWo": {"median": float(np.median(null_a_WcWo)), "p95": float(np.percentile(null_a_WcWo, 95))},
                "null_B_self_G": {"median": float(np.median(null_b_G)), "p95": float(np.percentile(null_b_G, 95))},
                "null_B_self_WcWo": {"median": float(np.median(null_b_WcWo)), "p95": float(np.percentile(null_b_WcWo, 95))},
                "null_C_self_WcWo": {"median": float(np.median(null_c_WcWo)), "p95": float(np.percentile(null_c_WcWo, 95))},
            }
        )

    med_pw = {
        a: {b: float(np.median([r["pairwise_diag"][a][b] for r in per_monoid])) for b in CANDIDATES_DIAG}
        for a in CANDIDATES_DIAG
    }
    min_pw = {
        a: {b: float(np.min([r["pairwise_diag"][a][b] for r in per_monoid])) for b in CANDIDATES_DIAG}
        for a in CANDIDATES_DIAG
    }
    max_pw = {
        a: {b: float(np.max([r["pairwise_diag"][a][b] for r in per_monoid])) for b in CANDIDATES_DIAG}
        for a in CANDIDATES_DIAG
    }
    return {
        "n_monoids": len(per_monoid),
        "hidden_dim": int(hidden_dim),
        "draws": int(draws),
        "per_monoid": per_monoid,
        "median_pairwise_diag": med_pw,
        "min_pairwise_diag": min_pw,
        "max_pairwise_diag": max_pw,
        "summary_nulls": {
            "null_A_G_median_of_medians": float(np.median([r["null_A_G"]["median"] for r in per_monoid])),
            "null_A_G_median_of_p95s": float(np.median([r["null_A_G"]["p95"] for r in per_monoid])),
            "null_A_WcWo_median_of_medians": float(np.median([r["null_A_WcWo"]["median"] for r in per_monoid])),
            "null_A_WcWo_median_of_p95s": float(np.median([r["null_A_WcWo"]["p95"] for r in per_monoid])),
            "null_B_self_WcWo_median_of_p95s": float(np.median([r["null_B_self_WcWo"]["p95"] for r in per_monoid])),
            "null_C_self_WcWo_median_of_p95s": float(np.median([r["null_C_self_WcWo"]["p95"] for r in per_monoid])),
        },
    }


def _stratify(rows: list[dict], key: str, bins: list[tuple[str, float, float]]) -> list[dict]:
    out = []
    for label, lo, hi in bins:
        sub = [r for r in rows if lo <= r["strat"][key] < hi]
        if not sub:
            continue
        out.append(
            {
                "bin": label,
                "count": len(sub),
                "n_eligible": sum(r["eligible"] for r in sub),
                "min_max_comp_cos": float(min(r["max_competitor_cos"] for r in sub)),
                "median_max_comp_cos": float(np.median([r["max_competitor_cos"] for r in sub])),
                "median_cos_WcWo_Wo": float(np.median([r["pairwise_5"]["WcWo"]["Wo"] for r in sub])),
                "median_wc_over_wo": float(np.median([r["strat"]["wc_over_wo"] for r in sub])),
            }
        )
    return out


def audit_spike81_pool(
    max_comp_threshold: float = 0.80,
    min_pi: float = 1e-4,
    results_dir: pathlib.Path = RESULTS,
) -> dict:
    """Audit all 600 automata in Spike 81's pool for Spike 99 eligibility and rejection reasons."""
    pool = S81.build_pool()
    used_map = collect_used_pool_ids(results_dir=results_dir)
    seen_sigs: dict[tuple, int] = {}

    records = []
    reason_counts = Counter()

    for i, A in enumerate(pool):
        D = np.asarray(A["D"], dtype=int)
        O = np.asarray(A["O"], dtype=float)
        m = int(D.shape[1])
        s0 = int(A["s0"])
        sig = canonical_aut_sig(D, A["O"], s0)
        dup_of = seen_sigs.get(sig)
        if dup_of is None:
            seen_sigs[sig] = i

        is_irrev = any(len(set(D[a].tolist())) < m for a in range(D.shape[0]))
        Dl = np.vstack([D, np.arange(m)[None]])
        L = int(Dl.shape[0])
        pi = S81.visit_dist(Dl, s0, np.ones(L) / L, T=30, burn=5)
        pi_ok = bool((pi > min_pi).all())

        ops = MP.master_operators(Dl, O, pi) if (pi > 1e-12).all() else None
        hs = S84.head_structure(Dl, O, pi) if (pi > 1e-12).all() else {"dimO": 0, "dimR": 0, "dimH": 0}
        if ops is not None:
            mats = candidate_matrices_from_ops(ops)
            pw_5 = pairwise_cosine_matrix(mats, CANDIDATES_5)
            pw_diag = pairwise_cosine_matrix(mats, CANDIDATES_DIAG)
            max_comp = float(max(pw_5["WcWo"][c] for c in COMPETITORS_4))
            max_comp_excl_g = float(max(pw_5["WcWo"][c] for c in ("Wo", "o", "k1_top")))
            strat = automaton_stratification_metrics(Dl, O, pi, ops, hs)
            # Diagnostic only (never used for eligibility): unit-normalized Wc/||Wc|| + Wo/||Wo||
            n_wc, n_wo = float(np.linalg.norm(ops["Wc"])), float(np.linalg.norm(ops["Wo"]))
            if n_wc > 1e-12 and n_wo > 1e-12:
                unit_sum = ops["Wc"] / n_wc + ops["Wo"] / n_wo
                unit_max = float(max(cos_mat(unit_sum, mats[c]) for c in COMPETITORS_4))
            else:
                unit_max = 1.0
        else:
            pw_5 = None
            pw_diag = None
            max_comp = None
            max_comp_excl_g = None
            strat = None
            unit_max = None

        reasons = []
        if i in used_map:
            reasons.append("used_in_prior_spike")
        if not is_irrev:
            reasons.append("bijective_not_irreversible")
        if dup_of is not None:
            reasons.append(f"isomorphic_duplicate_of_{dup_of}")
        if not pi_ok:
            reasons.append("low_stationary_mass_pi_le_1e-4")
        if max_comp is None or max_comp > max_comp_threshold:
            reasons.append(f"candidate_collinearity_max_cos_gt_{max_comp_threshold:.2f}")

        eligible = len(reasons) == 0
        if eligible:
            reason_counts["ELIGIBLE"] += 1
        else:
            for r in reasons:
                key = "isomorphic_duplicate" if r.startswith("isomorphic_duplicate") else r
                reason_counts[key] += 1

        records.append(
            {
                "id": int(i),
                "kind": A["kind"],
                "m": m,
                "L": L,
                "s0": s0,
                "eligible": eligible,
                "rejection_reasons": reasons,
                "used_sources": used_map.get(i, []),
                "is_irreversible": is_irrev,
                "isomorphic_duplicate_of": dup_of,
                "pi_ok": pi_ok,
                "max_competitor_cos": max_comp,
                "max_competitor_cos_excl_G": max_comp_excl_g,
                "diag_unit_norm_max_cos": unit_max,
                "pairwise_5": pw_5,
                "pairwise_diag": pw_diag,
                "strat": strat,
            }
        )

    fresh_irrev_ok = [
        r
        for r in records
        if not r["used_sources"] and r["is_irreversible"] and r["isomorphic_duplicate_of"] is None and r["pi_ok"]
    ]
    fresh_irrev_all = [
        r for r in records if not r["used_sources"] and r["is_irreversible"] and r["isomorphic_duplicate_of"] is None
    ]
    eligible_rows = [r for r in records if r["eligible"]]
    rejected_rows = [r for r in records if not r["eligible"]]

    stratifications = {}
    if fresh_irrev_ok:
        stratifications = {
            "n_states": _stratify(fresh_irrev_ok, "m", [(f"m={m}", m, m + 1) for m in range(4, 10)]),
            "stationary_entropy_bits": _stratify(
                fresh_irrev_ok,
                "pi_entropy_bits",
                [("[0, 1.5)", 0.0, 1.5), ("[1.5, 2.2)", 1.5, 2.2), ("[2.2, 2.8)", 2.2, 2.8), ("[2.8, inf)", 2.8, 99.0)],
            ),
            "markov_spectral_gap": _stratify(
                fresh_irrev_ok,
                "markov_spectral_gap",
                [("[0, 0.25)", 0.0, 0.25), ("[0.25, 0.50)", 0.25, 0.50), ("[0.50, 1.1)", 0.50, 1.1)],
            ),
            "irreversibility_wc_over_wo": _stratify(
                fresh_irrev_ok,
                "wc_over_wo",
                [("[0, 0.25)", 0.0, 0.25), ("[0.25, 0.50)", 0.25, 0.50), ("[0.50, 1.0)", 0.50, 1.0)],
            ),
            "gramian_rank_WcWo": _stratify(
                fresh_irrev_ok,
                "rank_WcWo",
                [(f"rank={rk}", rk, rk + 1) for rk in range(1, 10)],
            ),
            "output_complexity_entropy": _stratify(
                fresh_irrev_ok,
                "out_entropy_bits",
                [("[0, 0.5)", 0.0, 0.5), ("[0.5, 0.85)", 0.5, 0.85), ("[0.85, 1.01)", 0.85, 1.01)],
            ),
        }

    lowest_collinearity = sorted(fresh_irrev_ok, key=lambda r: r["max_competitor_cos"])[:20]
    return {
        "pool_size": len(pool),
        "max_comp_threshold": float(max_comp_threshold),
        "min_pi": float(min_pi),
        "n_used_excluded": len(used_map),
        "n_isomorphic_duplicates": sum(r["isomorphic_duplicate_of"] is not None for r in records),
        "n_fresh_irreversible_all": len(fresh_irrev_all),
        "n_fresh_irreversible_pi_ok": len(fresh_irrev_ok),
        "n_eligible": len(eligible_rows),
        "n_rejected": len(rejected_rows),
        "reason_counts": dict(reason_counts),
        "fresh_irrev_min_max_comp_cos": float(min(r["max_competitor_cos"] for r in fresh_irrev_ok)) if fresh_irrev_ok else None,
        "fresh_irrev_min_cos_WcWo_Wo": float(min(r["pairwise_5"]["WcWo"]["Wo"] for r in fresh_irrev_ok)) if fresh_irrev_ok else None,
        "fresh_irrev_min_max_comp_excl_G": float(min(r["max_competitor_cos_excl_G"] for r in fresh_irrev_ok)) if fresh_irrev_ok else None,
        "fresh_irrev_all_min_max_comp_cos": float(min(r["max_competitor_cos"] for r in fresh_irrev_all)) if fresh_irrev_all else None,
        "all_irrev_incl_used_min_max_comp_cos": float(
            min(r["max_competitor_cos"] for r in records if r["is_irreversible"] and r["max_competitor_cos"] is not None)
        ),
        "diag_fresh_unit_norm_le_080_count": sum(
            1 for r in fresh_irrev_ok if r["diag_unit_norm_max_cos"] is not None and r["diag_unit_norm_max_cos"] <= max_comp_threshold
        ),
        "stratifications": stratifications,
        "top20_lowest_collinearity_fresh": [
            {
                "id": r["id"],
                "kind": r["kind"],
                "m": r["m"],
                "L": r["L"],
                "max_competitor_cos": r["max_competitor_cos"],
                "max_competitor_cos_excl_G": r["max_competitor_cos_excl_G"],
                "cos_WcWo_Wo": r["pairwise_5"]["WcWo"]["Wo"],
                "cos_WcWo_G": r["pairwise_5"]["WcWo"]["G"],
                "cos_WcWo_o": r["pairwise_5"]["WcWo"]["o"],
                "cos_WcWo_k1_top": r["pairwise_5"]["WcWo"]["k1_top"],
                "wc_over_wo": r["strat"]["wc_over_wo"],
                "cos_Wc_Wo": r["strat"]["cos_Wc_Wo"],
            }
            for r in lowest_collinearity
        ],
        "eligible_automata": eligible_rows,
        "all_pool_records": records,
    }


def run_full_audit(draws: int = 10000, hidden_dim: int = 64, out_path: pathlib.Path = AUDIT_OUT) -> dict:
    pr12 = audit_pr12_monoids(hidden_dim=hidden_dim, draws=draws)
    pool_audit = audit_spike81_pool()
    payload = {
        "pr12_candidate_agreement_audit": pr12,
        "spike81_pool_audit": pool_audit,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return payload


def main() -> None:
    payload = run_full_audit()
    pr12 = payload["pr12_candidate_agreement_audit"]
    pool = payload["spike81_pool_audit"]
    print("=== PR #12 Median Pairwise Cosine Matrix ===")
    for a, row in pr12["median_pairwise_diag"].items():
        print(f"  {a:8s}: " + " ".join(f"{b}={v:.4f}" for b, v in row.items()))
    print("PR #12 null summary:", json.dumps(pr12["summary_nulls"], indent=2))
    print(
        f"Spike 81 pool audit: total={pool['pool_size']}, used_excluded={pool['n_used_excluded']}, "
        f"isomorphic_dups={pool['n_isomorphic_duplicates']}, fresh_irrev_pi_ok={pool['n_fresh_irreversible_pi_ok']}, "
        f"eligible={pool['n_eligible']}, min_max_comp_cos={pool['fresh_irrev_min_max_comp_cos']}"
    )


if __name__ == "__main__":
    main()
