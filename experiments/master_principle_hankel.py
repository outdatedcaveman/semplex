"""Master Principle Hankel & Non-Commuting Interface Experiment (`gemini/master-principle-hankel`):

Empirical companion to `MasterPrincipleHankel.lean` investigating two core open questions
identified in `MASTER_PRINCIPLE_SYNTHESIS_2026-11-21.md`:
  Arm 1 (Non-Commuting Monoids + Contractive SSM):
    Compare 7 candidate operators (`W_sum = W_c + W_o`, `W_bal = W_c^{1/2} W_o W_c^{1/2}`,
    `W_gm = W_c # W_o`, `W_bal_dual`, `W_c`, `W_o`, `o`), each evaluated at its exact FD
    zero-cosine `lam_kin`, across 12 fresh strongly non-commuting irreversible monoids on
    `gru_mlp`, `rnn_mlp`, `lru_lo_mlp` (rho=0.50), and `lru_hi_mlp` (rho=0.85), plus
    step-0 `W_c(rho^2)` verification.
  Arm 2 (Partially Observed Controlled HMMs):
    4 reversible cyclic-group HMMs (`W_c^{action} = 0` identically, generalizing Spikes 23-24)
    + 4 non-reversible non-commuting HMMs across `gru_mlp` and `rnn_mlp`, verifying near-Bayes
    filtering (`kl_gap`), linear belief recovery (`belief_r2`), Hankel rank compression
    (`pca95_dim` vs `n_distinct_beliefs` vs `m-1`), and learned state/history-kernel alignment
    with `W_sum^{obs}` vs `W_bal^{obs}` vs `W_gm^{obs}` vs `W_bal_dual^{obs}` vs `W_o`.
"""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
from scipy.linalg import expm

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import spike81 as S81

RESULTS = ROOT / "experiments" / "results"
RAW = RESULTS / "master_principle_hankel_raw"
OUT = RESULTS / "master_principle_hankel.json"
PRED = RESULTS / "master_principle_hankel_predictions.json"

GAMMA_C = 0.6
GAMMA_O = 0.7
T_MON = 16
BURN_MON = 4
T_OP = 16
T_HMM = 12
BURN_HMM = 2
BATCH = 64

OPS_ORDER = ("W_sum", "W_bal", "W_gm", "W_bal_dual", "W_c", "W_o", "o")
GAMMA_SWEEP = (0.10, 0.25, 0.40, 0.55, 0.7225, 0.85)


def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def sym_perp(M: np.ndarray, Pperp: np.ndarray) -> np.ndarray:
    S = 0.5 * (M + M.T)
    return 0.5 * ((Pperp @ S @ Pperp) + (Pperp @ S @ Pperp).T)


def psd_powers(A: np.ndarray, rel_tol: float = 1e-4):
    vals, vecs = np.linalg.eigh(0.5 * (A + A.T))
    top = float(max(vals.max(), 1e-12))
    thr = rel_tol * top
    sqrt_v = np.sqrt(np.maximum(vals, 0.0))
    inv_sqrt_v = np.where(vals > thr, 1.0 / np.sqrt(np.maximum(vals, 1e-15)), 0.0)
    sqrt_A = (vecs * sqrt_v) @ vecs.T
    pinv_sqrt_A = (vecs * inv_sqrt_v) @ vecs.T
    return 0.5 * (sqrt_A + sqrt_A.T), 0.5 * (pinv_sqrt_A + pinv_sqrt_A.T)


def build_candidate_ops(Wc: np.ndarray, Wo: np.ndarray, o_gram: np.ndarray, Pperp: np.ndarray) -> dict[str, np.ndarray]:
    Wc_s = sym_perp(Wc, Pperp)
    Wo_s = sym_perp(Wo, Pperp)
    wc_h, wc_ih = psd_powers(Wc_s, rel_tol=1e-4)
    wbal = sym_perp(wc_h @ Wo_s @ wc_h, Pperp)
    # Kubo-Ando geometric mean Wc # Wo on Wc's active support
    inner_gm = 0.5 * (wc_ih @ Wo_s @ wc_ih + (wc_ih @ Wo_s @ wc_ih).T)
    inner_gm_h, _ = psd_powers(inner_gm, rel_tol=1e-6)
    wgm = sym_perp(wc_h @ inner_gm_h @ wc_h, Pperp)
    # Balanced-coordinate pullback T^T T = Wc^{+1/2} (Wc^{1/2} Wo Wc^{1/2})^{1/2} Wc^{+1/2}
    wbal_h, _ = psd_powers(wbal, rel_tol=1e-6)
    wbal_dual = sym_perp(wc_ih @ wbal_h @ wc_ih, Pperp)
    return {
        "W_sum": sym_perp(Wc_s + Wo_s, Pperp),
        "W_bal": wbal,
        "W_gm": wgm,
        "W_bal_dual": wbal_dual,
        "W_c": Wc_s,
        "W_o": Wo_s,
        "o": sym_perp(o_gram, Pperp),
    }


def monoid_base_operators(
    Dl: np.ndarray,
    O: np.ndarray,
    pi: np.ndarray,
    gc: float = GAMMA_C,
    go: float = GAMMA_O,
    T: int = T_OP,
) -> dict:
    L, m = Dl.shape
    O = np.asarray(O, float)
    if O.ndim == 1:
        O = O[:, None]
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)

    Ts = []
    for a in range(L):
        Pa = np.zeros((m, m))
        for q in range(m):
            Pa[q, Dl[a, q]] = 1.0
        Ts.append((W[:, None] * Pa) / W[None, :])

    Lkin = np.zeros((m, m))
    for Ta in Ts:
        diff = Ta - np.eye(m)
        Lkin += diff.T @ diff
    Lkin = 0.5 / L * sym_perp(Lkin, Pperp)

    mu_o = (pi[:, None] * O).sum(0, keepdims=True)
    Oc = O - mu_o
    sd = np.sqrt((pi[:, None] * (Oc ** 2)).sum(0, keepdims=True))
    Os = Oc / np.maximum(sd, 1e-12)
    F = W[:, None] * Os
    At = F @ F.T
    o_gram = sym_perp(At, Pperp)

    Wo = np.zeros((m, m))
    g = 1.0
    for _ in range(T):
        Wo += g * At
        At_next = np.zeros((m, m))
        for Ta in Ts:
            At_next += Ta @ At @ Ta.T
        At = At_next / L
        g *= go
    Wo = sym_perp(Wo, Pperp)

    Bt = np.outer(one, one)
    Wc = np.zeros((m, m))
    Wc_zero_lag = np.zeros((m, m))
    g = gc
    gz = 1.0
    for _ in range(1, T):
        Bt_next = np.zeros((m, m))
        for Ta in Ts:
            Bt_next += Ta.T @ Bt @ Ta
        Bt = Bt_next / L
        centered = Pperp @ Bt @ Pperp
        Wc += g * centered
        Wc_zero_lag += gz * centered
        g *= gc
        gz *= gc
    Wc = sym_perp(Wc, Pperp)
    Wc_zero_lag = sym_perp(Wc_zero_lag, Pperp)

    return {
        "Pperp": Pperp,
        "Lkin": Lkin,
        "Wc": Wc,
        "Wc_zero_lag": Wc_zero_lag,
        "Wo": Wo,
        "o": o_gram,
        "cands": build_candidate_ops(Wc, Wo, o_gram, Pperp),
    }


def norm_dirichlet_theoretical(Lkin: np.ndarray, Wsrc: np.ndarray, lam: float) -> float:
    E = expm(-lam * Lkin)
    M = E @ Wsrc
    den = float(np.trace(M))
    if den <= 1e-15:
        return 0.0
    return float(np.trace(Lkin @ M) / den)


def invert_lambda_from_kin(
    Lkin: np.ndarray, Wsrc: np.ndarray, kin_obs: float, lo: float = -4.0, hi: float = 12.0
) -> float:
    if float(np.linalg.norm(Wsrc)) < 1e-12:
        return 0.0
    k_lo = norm_dirichlet_theoretical(Lkin, Wsrc, lo)
    k_hi = norm_dirichlet_theoretical(Lkin, Wsrc, hi)
    if kin_obs >= k_lo:
        return lo
    if kin_obs <= k_hi:
        return hi
    a, b = lo, hi
    for _ in range(50):
        mid = 0.5 * (a + b)
        if norm_dirichlet_theoretical(Lkin, Wsrc, mid) > kin_obs:
            a = mid
        else:
            b = mid
    return 0.5 * (a + b)


def eval_G_at(Lkin: np.ndarray, Wsrc: np.ndarray, Pperp: np.ndarray, lam: float) -> np.ndarray:
    H = expm(-0.5 * lam * Lkin)
    return sym_perp(H @ Wsrc @ H, Pperp)


def dirichlet_kin_norm(G: np.ndarray, Lkin: np.ndarray) -> float:
    den = float(np.trace(G))
    if den <= 1e-12:
        return 0.0
    return float(np.trace(Lkin @ G) / den)


def commutator_ratio(A: np.ndarray, B: np.ndarray) -> float:
    denom = float(np.linalg.norm(A) * np.linalg.norm(B))
    if denom < 1e-12:
        return 0.0
    return float(np.linalg.norm(A @ B - B @ A) / denom)


def stationary_distribution(P: np.ndarray) -> np.ndarray:
    pi = np.full(P.shape[0], 1.0 / P.shape[0])
    for _ in range(20000):
        nxt = pi @ P
        if np.max(np.abs(nxt - pi)) < 1e-14:
            pi = nxt
            break
        pi = nxt
    return pi / pi.sum()


def compute_hmm_operators(P_actions: np.ndarray, Olik: np.ndarray, pi: np.ndarray, rng: np.random.Generator) -> dict:
    """Compute exact observation-conditioned Wc^{obs}, Wc^{action}, Wo^{future}, L_kin, and H = R_feat @ O_feat."""
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)
    Dpi_inv_h = np.diag(1.0 / np.sqrt(pi))
    Dpi_h = np.diag(np.sqrt(pi))

    # L_kin and action-only Wc^{action} in L^2(pi) for mixture transition actions P_a
    # Adjoint on L^2(pi): T_a[q, r] = sqrt(pi[q]) * P_a[q, r] / sqrt(pi[r])
    Ts = [((W[:, None] * P_actions[a]) / W[None, :]) for a in range(L)]
    Lkin = np.zeros((m, m))
    for Ta in Ts:
        diff = Ta - np.eye(m)
        Lkin += diff.T @ diff
    Lkin = 0.5 / L * sym_perp(Lkin, Pperp)

    Bt = np.outer(one, one)
    Wc_action = np.zeros((m, m))
    g = GAMMA_C
    for _ in range(1, T_HMM):
        Bt_next = np.zeros((m, m))
        for Ta in Ts:
            Bt_next += Ta.T @ Bt @ Ta
        Bt = Bt_next / L
        Wc_action += g * (Pperp @ Bt @ Pperp)
        g *= GAMMA_C
    Wc_action = sym_perp(Wc_action, Pperp)

    # Exact Monte-Carlo sample of action-observation histories -> posteriors mu_h
    n_traj = 400
    mu_list = []
    for _ in range(n_traj):
        x = int(rng.choice(m, p=pi))
        bel = pi.copy()
        for t in range(T_HMM):
            y = int(rng.choice(n_obs, p=Olik[:, x]))
            lik = Olik[y]
            bel = bel * lik
            bel = bel / max(float(bel.sum()), 1e-15)
            if t >= BURN_HMM:
                mu_list.append(bel.copy())
            a = int(rng.integers(L))
            x = int(rng.choice(m, p=P_actions[a, x]))
            bel = bel @ P_actions[a]
            bel = bel / max(float(bel.sum()), 1e-15)
    R_raw = np.asarray(mu_list, dtype=float)  # (N_hist, m)
    N_hist = R_raw.shape[0]
    R_feat = ((R_raw - pi[None, :]) @ Dpi_inv_h) / math.sqrt(N_hist)
    Wc_obs = sym_perp(R_feat.T @ R_feat, Pperp)

    # Exact multi-step discounted future-test vectors f_tau(x) for horizons k = 1, 2, 3
    cols = []
    weights = []
    # Current state vector is ones; backward operator step (a, y): P_a @ diag(Olik[y]) @ v
    horizon = 3 if (L ** 3) * (n_obs ** 3) <= 256 else 2
    vecs = [np.ones(m, dtype=float)]
    g = 1.0
    for _k in range(1, horizon + 1):
        nxt = []
        for v in vecs:
            for a in range(L):
                for y in range(n_obs):
                    nxt.append(P_actions[a] @ (Olik[y] * v))
        vecs = nxt
        w_per = g / (L ** _k)
        for v in vecs:
            cols.append(v)
            weights.append(w_per)
        g *= GAMMA_O
    O_fut = np.column_stack(cols)  # (m, N_test)
    w_arr = np.asarray(weights, dtype=float)
    O_cent = O_fut - (pi @ O_fut)[None, :]
    O_feat = Dpi_h @ O_cent * np.sqrt(w_arr)[None, :]
    Wo_obs = sym_perp(O_feat @ O_feat.T, Pperp)

    # Exact Hankel factorization H = R_feat @ O_feat
    H = R_feat @ O_feat
    _, s_h, _ = np.linalg.svd(H, full_matrices=False)
    cands = build_candidate_ops(Wc_obs, Wo_obs, Wo_obs, Pperp)
    eigs_bal = np.sort(np.linalg.eigvalsh(cands["W_bal"]))[::-1]
    top_k = min(m, len(s_h))
    hankel_err = float(np.max(np.abs(np.sort(s_h ** 2)[::-1][:top_k] - eigs_bal[:top_k])))
    trace_err = float(abs(float(np.trace(H.T @ H)) - float(np.trace(Wc_obs @ Wo_obs))))
    assert hankel_err < 1e-8, f"Balanced vs Hankel SVD mismatch: {hankel_err}"
    assert trace_err < 1e-8, f"Trace H^T H vs Tr(Wc Wo) mismatch: {trace_err}"

    # Check finite posterior multiplicity vs rank
    n_distinct_beliefs = int(len({tuple(np.round(r, 3).tolist()) for r in R_raw}))

    return {
        "Pperp": Pperp,
        "Lkin": Lkin,
        "Wc_action": Wc_action,
        "Wc_obs": Wc_obs,
        "Wo_obs": Wo_obs,
        "cands": cands,
        "W_action_sum": sym_perp(Wc_action + Wo_obs, Pperp),
        "comm_ratio_obs": commutator_ratio(Wc_obs, Wo_obs),
        "hankel_svd_match_err": hankel_err,
        "n_distinct_beliefs": n_distinct_beliefs,
        "sample_beliefs": R_raw[:384],
        "R_feat_sample": ((R_raw[:384] - pi[None, :]) @ Dpi_inv_h),
    }


def predict():
    # --- Arm 1: 12 fresh strongly non-commuting monoids ---
    rng_mon = np.random.default_rng(2026112201)
    cands_mon = []
    seen_sigs = set()
    for _ in range(500):
        d, o = S81.random_automaton(rng_mon, 8, 3, "free")
        D, O, s0 = S81.minimize(d, o, start=0)
        if D.shape[1] < 6 or O.min() == O.max():
            continue
        sig = (tuple(map(tuple, D.tolist())), tuple(O.tolist()), int(s0))
        if sig in seen_sigs:
            continue
        seen_sigs.add(sig)
        Dl = np.vstack([D, np.arange(D.shape[1])[None]])
        k = Dl.shape[0]
        pi = S81.visit_dist(Dl, s0, np.ones(k) / k, T=T_MON, burn=BURN_MON)
        if (pi <= 1e-3).any():
            continue
        ops = monoid_base_operators(Dl, O, pi, gc=GAMMA_C, go=GAMMA_O, T=T_OP)
        Wc, Wo, o_gr, Pperp, Lkin = ops["Wc"], ops["Wo"], ops["o"], ops["Pperp"], ops["Lkin"]
        if np.linalg.norm(Wc) < 1e-2 or np.linalg.norm(Wo) < 1e-2:
            continue
        cr = commutator_ratio(Wc, Wo)
        if cr < 0.12:
            continue
        G_sum_0 = eval_G_at(Lkin, ops["cands"]["W_sum"], Pperp, 1.0)
        G_bal_0 = eval_G_at(Lkin, ops["cands"]["W_bal"], Pperp, 1.0)
        G_gm_0 = eval_G_at(Lkin, ops["cands"]["W_gm"], Pperp, 1.0)
        if cos_mat(G_sum_0, o_gr) >= 0.90:
            continue
        sep = 1.0 - min(cos_mat(G_sum_0, G_bal_0), cos_mat(G_sum_0, G_gm_0))
        row = {
            "id": len(cands_mon),
            "D": D.tolist(),
            "Dl": Dl.tolist(),
            "out": O.tolist(),
            "s0": int(s0),
            "m": int(Dl.shape[1]),
            "L": int(k),
            "pi": pi.tolist(),
            "comm_ratio": cr,
            "sep_sum_vs_bal_gm": float(sep),
            "Lkin": Lkin.tolist(),
            "Pperp": Pperp.tolist(),
            "Wc": Wc.tolist(),
            "Wc_zero_lag": ops["Wc_zero_lag"].tolist(),
            "Wo": Wo.tolist(),
            "o": o_gr.tolist(),
        }
        for op_name in OPS_ORDER:
            row[op_name] = ops["cands"][op_name].tolist()
        for gc_s in GAMMA_SWEEP:
            ops_g = monoid_base_operators(Dl, O, pi, gc=gc_s, go=GAMMA_O, T=T_OP)
            row[f"Wc_gc_{gc_s:.4f}"] = ops_g["Wc"].tolist()
            row[f"Wc_zl_gc_{gc_s:.4f}"] = ops_g["Wc_zero_lag"].tolist()
            row[f"Wsum_gc_{gc_s:.4f}"] = ops_g["cands"]["W_sum"].tolist()
        cands_mon.append(row)

    assert len(cands_mon) >= 12, f"Only found {len(cands_mon)} strongly non-commuting monoids out of 500!"
    cands_mon.sort(key=lambda r: -r["sep_sum_vs_bal_gm"])
    picked_mon = cands_mon[:12]
    for idx, r in enumerate(picked_mon):
        r["name"] = f"NCM_{idx:02d}"

    # --- Arm 2: 8 fresh partially-observed controlled HMMs ---
    hmm_items = []
    rng_hmm = np.random.default_rng(2026112202)

    # 4 reversible cyclic-group HMMs (Wc_action == 0 identically)
    cyc_configs = [
        ("hmm_Z4", 4, np.array([[0.90, 0.72, 0.28, 0.10], [0.10, 0.28, 0.72, 0.90]], float)),
        ("hmm_Z5", 5, np.array([[0.92, 0.75, 0.50, 0.25, 0.08], [0.08, 0.25, 0.50, 0.75, 0.92]], float)),
        ("hmm_Z6", 6, np.array([[0.90, 0.80, 0.60, 0.35, 0.20, 0.10], [0.10, 0.20, 0.40, 0.65, 0.80, 0.90]], float)),
        ("hmm_Z7", 7, np.array([[0.92, 0.82, 0.68, 0.50, 0.32, 0.18, 0.08], [0.08, 0.18, 0.32, 0.50, 0.68, 0.82, 0.92]], float)),
    ]
    for nm, m, Olik in cyc_configs:
        assert np.allclose(Olik.sum(0), 1.0)
        P_actions = np.zeros((2, m, m), dtype=float)
        step2 = 2 if m >= 5 else (m - 1)
        for x in range(m):
            P_actions[0, x, (x + 1) % m] = 1.0
            P_actions[1, x, (x + step2) % m] = 1.0
        pi = np.ones(m) / m
        h_ops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        assert float(np.linalg.norm(h_ops["Wc_action"])) < 1e-10, f"{nm}: expected Wc_action==0"
        row = {
            "name": nm,
            "family": "cyclic_group_hmm",
            "m": m,
            "L": 2,
            "n_obs": int(Olik.shape[0]),
            "P_actions": P_actions.tolist(),
            "Olik": Olik.tolist(),
            "pi": pi.tolist(),
            "Pperp": h_ops["Pperp"].tolist(),
            "Lkin": h_ops["Lkin"].tolist(),
            "Wc_action": h_ops["Wc_action"].tolist(),
            "Wc_obs": h_ops["Wc_obs"].tolist(),
            "Wo_obs": h_ops["Wo_obs"].tolist(),
            "W_action_sum": h_ops["W_action_sum"].tolist(),
            "comm_ratio_obs": h_ops["comm_ratio_obs"],
            "hankel_svd_match_err": h_ops["hankel_svd_match_err"],
            "n_distinct_beliefs": h_ops["n_distinct_beliefs"],
        }
        for op_name in OPS_ORDER:
            row[op_name] = h_ops["cands"][op_name].tolist()
        hmm_items.append(row)

    # 4 non-reversible strongly non-commuting controlled HMMs
    nr_count = 0
    while nr_count < 4:
        m = [4, 5, 5, 6][nr_count]
        n_obs = [2, 2, 3, 2][nr_count]
        P_actions = np.zeros((2, m, m), dtype=float)
        alpha_p = np.linspace(4.0, 0.8, m)
        for a in range(2):
            for x in range(m):
                P_actions[a, x] = rng_hmm.dirichlet(np.roll(alpha_p, x + 2 * a))
        Olik = rng_hmm.dirichlet(np.full(n_obs, 0.9), size=m).T
        Olik = np.clip(Olik, 0.05, 0.95)
        Olik = Olik / Olik.sum(axis=0, keepdims=True)
        P_mix = 0.5 * (P_actions[0] + P_actions[1])
        pi = stationary_distribution(P_mix)
        if pi.min() < 0.05:
            continue
        h_ops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        if h_ops["comm_ratio_obs"] < 0.10 or np.linalg.norm(h_ops["Wc_obs"]) < 1e-2 or np.linalg.norm(h_ops["Wo_obs"]) < 1e-2:
            continue
        nm = f"hmm_nr_{nr_count}"
        row = {
            "name": nm,
            "family": "nonrev_hmm",
            "m": m,
            "L": 2,
            "n_obs": n_obs,
            "P_actions": P_actions.tolist(),
            "Olik": Olik.tolist(),
            "pi": pi.tolist(),
            "Pperp": h_ops["Pperp"].tolist(),
            "Lkin": h_ops["Lkin"].tolist(),
            "Wc_action": h_ops["Wc_action"].tolist(),
            "Wc_obs": h_ops["Wc_obs"].tolist(),
            "Wo_obs": h_ops["Wo_obs"].tolist(),
            "W_action_sum": h_ops["W_action_sum"].tolist(),
            "comm_ratio_obs": h_ops["comm_ratio_obs"],
            "hankel_svd_match_err": h_ops["hankel_svd_match_err"],
            "n_distinct_beliefs": h_ops["n_distinct_beliefs"],
        }
        for op_name in OPS_ORDER:
            row[op_name] = h_ops["cands"][op_name].tolist()
        hmm_items.append(row)
        nr_count += 1

    out = {
        "constants": {
            "gamma_c": GAMMA_C,
            "gamma_o": GAMMA_O,
            "T_mon": T_MON,
            "burn_mon": BURN_MON,
            "T_op": T_OP,
            "T_hmm": T_HMM,
            "burn_hmm": BURN_HMM,
            "ops_order": list(OPS_ORDER),
            "gamma_sweep": list(GAMMA_SWEEP),
        },
        "n_candidates_mon": len(cands_mon),
        "monoids": picked_mon,
        "hmms": hmm_items,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(out))
    print(
        f"Monoids: {len(cands_mon)}/{500} qualified; picked 12 "
        f"(comm=[{min(r['comm_ratio'] for r in picked_mon):.3f}, {max(r['comm_ratio'] for r in picked_mon):.3f}], "
        f"sep=[{min(r['sep_sum_vs_bal_gm'] for r in picked_mon):.3f}, {max(r['sep_sum_vs_bal_gm'] for r in picked_mon):.3f}])"
    )
    print(
        f"HMMs: {len(hmm_items)} ready "
        f"(nr_comm={[round(r['comm_ratio_obs'], 3) for r in hmm_items if r['family']=='nonrev_hmm']}, "
        f"max_hankel_err={max(r['hankel_svd_match_err'] for r in hmm_items):.2e})"
    )


def fast_sample_monoid(Dl: np.ndarray, O: np.ndarray, s0: int, B: int, T: int, rng: np.random.Generator):
    import torch
    L = Dl.shape[0]
    X = rng.integers(0, L, size=(B, T))
    ST = np.empty((B, T), dtype=np.int64)
    q = np.full(B, s0, dtype=np.int64)
    for t in range(T):
        q = Dl[X[:, t], q]
        ST[:, t] = q
    O_mat = O[:, None] if O.ndim == 1 else O
    Y = O_mat[ST].astype(np.float32)
    return torch.from_numpy(X).long(), torch.from_numpy(Y), ST


def make_monoid_model(arch: str, L: int, k_out: int):
    import torch
    import torch.nn as nn

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    if arch == "gru_mlp":
        class M(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(L, 64)
                self.rnn = nn.GRU(64, 64, batch_first=True)
                self.head = mlp_head()
            def hidden(self, X):
                return self.rnn(self.emb(X))[0]
            def forward(self, X):
                return self.head(self.hidden(X))
        return M()
    if arch == "rnn_mlp":
        class M(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(L, 64)
                self.rnn = nn.RNN(64, 64, batch_first=True, nonlinearity="tanh")
                self.head = mlp_head()
            def hidden(self, X):
                return self.rnn(self.emb(X))[0]
            def forward(self, X):
                return self.head(self.hidden(X))
        return M()
    if arch in ("lru_lo_mlp", "lru_hi_mlp"):
        rho = 0.50 if arch == "lru_lo_mlp" else 0.85
        class LRU(nn.Module):
            def __init__(self, r: float):
                super().__init__()
                self.rho = float(r)
                self.emb = nn.Embedding(L, 64)
                self.head = mlp_head()
            def hidden(self, X):
                u = self.emb(X)  # (B, T, 64)
                B, T, D = u.shape
                h = torch.zeros(B, D, dtype=u.dtype, device=u.device)
                hs = []
                for t in range(T):
                    h = self.rho * h + u[:, t, :]
                    hs.append(h)
                return torch.stack(hs, dim=1)
            def forward(self, X):
                return self.head(self.hidden(X))
        return LRU(rho)
    raise ValueError(f"Unknown monoid arch {arch}")


def extract_monoid_gram(H_np: np.ndarray, ST: np.ndarray, pi: np.ndarray, m: int, Lkin: np.ndarray, Pperp: np.ndarray):
    flat_h = H_np[:, BURN_MON:].reshape(-1, H_np.shape[-1])
    flat_q = ST[:, BURN_MON:].ravel()
    Ce = np.stack([
        flat_h[flat_q == q].mean(0) if (flat_q == q).any() else np.zeros(flat_h.shape[1])
        for q in range(m)
    ])
    mu = (pi[:, None] * Ce).sum(0, keepdims=True)
    Cc = Ce - mu
    W = np.sqrt(pi)[:, None]
    G_net = sym_perp((W * Cc) @ (W * Cc).T, Pperp)
    kin = dirichlet_kin_norm(G_net, Lkin)
    return G_net, kin


def train_monoid_task(job: tuple[dict, str]) -> dict:
    import torch
    import torch.nn.functional as F
    torch.set_num_threads(1)

    A, arch = job
    name = A["name"]
    Dl = np.array(A["Dl"], dtype=np.int64)
    O = np.array(A["out"], dtype=np.float32)
    pi = np.array(A["pi"], dtype=float)
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    L, m = Dl.shape

    seed = 20261122 + (sum(ord(c) for c in f"{name}:{arch}") * 131 + hash((name, arch)) % 100000) % 1000000
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_monoid_model(arch, L, 1)
    # Deterministic eval stream
    X_eval, Y_eval, ST_eval = fast_sample_monoid(Dl, O, A["s0"], 400, T_MON, np.random.default_rng(seed + 10**6))

    step0_info = {}
    if arch in ("lru_lo_mlp", "lru_hi_mlp"):
        rho = 0.50 if arch == "lru_lo_mlp" else 0.85
        # Single-init step 0 Gram + 16-draw isotropic average
        with torch.no_grad():
            H0 = mdl.hidden(X_eval).numpy()
        G0_run, _ = extract_monoid_gram(H0, ST_eval, pi, m, Lkin, Pperp)
        G0_iso = np.zeros((m, m))
        with torch.no_grad():
            orig_w = mdl.emb.weight.data.clone()
            for j in range(16):
                g_rng = torch.Generator().manual_seed(seed + 5000 + j)
                mdl.emb.weight.data.normal_(0.0, 1.0 / math.sqrt(64), generator=g_rng)
                Hj = mdl.hidden(X_eval).numpy()
                Gj, _ = extract_monoid_gram(Hj, ST_eval, pi, m, Lkin, Pperp)
                tr = float(np.trace(Gj))
                if tr > 1e-12:
                    G0_iso += Gj / tr
            mdl.emb.weight.data.copy_(orig_w)
        step0_info = {
            "rho": rho,
            "gamma_c_theo": rho * rho,
            "step0_cos_vs_gc_run": {
                f"{gc_s:.4f}": cos_mat(G0_run, np.array(A[f"Wc_zl_gc_{gc_s:.4f}"], dtype=float))
                for gc_s in GAMMA_SWEEP
            },
            "step0_cos_vs_gc_iso": {
                f"{gc_s:.4f}": cos_mat(G0_iso, np.array(A[f"Wc_zl_gc_{gc_s:.4f}"], dtype=float))
                for gc_s in GAMMA_SWEEP
            },
        }

    opt = torch.optim.Adam(mdl.parameters(), lr=3e-3)
    steps = 1200
    t0 = time.time()
    for _ in range(steps):
        X, Y, _ = fast_sample_monoid(Dl, O, A["s0"], BATCH, T_MON, rng)
        loss = F.binary_cross_entropy_with_logits(mdl(X)[:, BURN_MON:], Y[:, BURN_MON:])
        opt.zero_grad()
        loss.backward()
        opt.step()

    with torch.no_grad():
        logits = mdl(X_eval)[:, BURN_MON:]
        fit = float(((logits > 0).float() == Y_eval[:, BURN_MON:]).float().mean())
        H = mdl.hidden(X_eval).numpy()

    G_net, kin = extract_monoid_gram(H, ST_eval, pi, m, Lkin, Pperp)
    scores = {}
    lams = {}
    for op_name in OPS_ORDER:
        Wsrc = np.array(A[op_name], dtype=float)
        lam_op = invert_lambda_from_kin(Lkin, Wsrc, kin)
        G_pred = eval_G_at(Lkin, Wsrc, Pperp, lam_op)
        scores[op_name] = cos_mat(G_net, G_pred)
        lams[op_name] = float(lam_op)

    best_gc = None
    gc_cos = {}
    if arch in ("lru_lo_mlp", "lru_hi_mlp"):
        for gc_s in GAMMA_SWEEP:
            Wsrc = np.array(A[f"Wsum_gc_{gc_s:.4f}"], dtype=float)
            lam_g = invert_lambda_from_kin(Lkin, Wsrc, kin)
            c_g = cos_mat(G_net, eval_G_at(Lkin, Wsrc, Pperp, lam_g))
            gc_cos[f"{gc_s:.4f}"] = c_g
        best_gc = float(max(GAMMA_SWEEP, key=lambda g: gc_cos[f"{g:.4f}"]))

    res = {
        "arm": "monoid",
        "name": name,
        "arch": arch,
        "fit": fit,
        "kin_norm": kin,
        "scores": scores,
        "lams": lams,
        "elapsed_s": float(time.time() - t0),
    }
    if step0_info:
        res["step0"] = step0_info
        res["post_gc_cos"] = gc_cos
        res["best_gc_post"] = best_gc

    p = RAW / f"monoid_{name}_{arch}.json"
    p.write_text(json.dumps(res))
    return res


def sample_hmm_batch(P_actions: np.ndarray, Olik: np.ndarray, pi: np.ndarray, B: int, T: int, rng: np.random.Generator):
    """Sample (inputs_one_hot, targets_y_next, exact_posteriors_mu, bayes_y_next_probs)."""
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]
    P_mix = P_actions.mean(axis=0)
    emit_from_cur = P_mix @ Olik.T  # (m, n_obs): P(y_{t+1} | X_t)

    IN = np.zeros((B, T, L + n_obs), dtype=np.float32)
    TG = np.zeros((B, T), dtype=np.int64)
    MU = np.zeros((B, T, m), dtype=np.float32)
    BAYES = np.zeros((B, T, n_obs), dtype=np.float32)

    x = rng.choice(m, size=B, p=pi)
    bel = np.broadcast_to(pi, (B, m)).copy()
    prev_a = np.full(B, -1, dtype=np.int64)

    for t in range(T):
        # Emission y_t | x_t
        probs_y = Olik[:, x].T  # (B, n_obs)
        u = rng.random(B)
        cdf = np.cumsum(probs_y, axis=1)
        y = np.argmax(cdf >= u[:, None], axis=1)

        # Bayes update at step t given y_t
        bel = bel * Olik[y]  # (B, m)
        bel = bel / np.maximum(bel.sum(axis=1, keepdims=True), 1e-15)
        MU[:, t, :] = bel.astype(np.float32)
        BAYES[:, t, :] = (bel @ emit_from_cur).astype(np.float32)

        # Input token at t: [prev_a one-hot (or zero at t=0), y_t one-hot]
        if t > 0:
            IN[np.arange(B), t, prev_a] = 1.0
        IN[np.arange(B), t, L + y] = 1.0

        # Random action a_t -> x_{t+1} -> y_{t+1}
        a = rng.integers(0, L, size=B)
        probs_x = P_actions[a, x]  # (B, m)
        u_x = rng.random(B)
        x_nxt = np.argmax(np.cumsum(probs_x, axis=1) >= u_x[:, None], axis=1)

        probs_ynxt = Olik[:, x_nxt].T
        u_yn = rng.random(B)
        y_nxt = np.argmax(np.cumsum(probs_ynxt, axis=1) >= u_yn[:, None], axis=1)
        TG[:, t] = y_nxt

        # Transition belief for step t+1 using a_t
        bel = np.einsum("bm,bmn->bn", bel, P_actions[a])
        bel = bel / np.maximum(bel.sum(axis=1, keepdims=True), 1e-15)
        x = x_nxt
        prev_a = a

    return IN, TG, MU, BAYES


def make_hmm_model(arch: str, in_dim: int, n_obs: int):
    import torch.nn as nn

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, n_obs))

    if arch == "gru_mlp":
        class M(nn.Module):
            def __init__(self):
                super().__init__()
                self.in_proj = nn.Linear(in_dim, 64)
                self.rnn = nn.GRU(64, 64, batch_first=True)
                self.head = mlp_head()
            def hidden(self, x):
                return self.rnn(self.in_proj(x))[0]
            def forward(self, x):
                return self.head(self.hidden(x))
        return M()
    if arch == "rnn_mlp":
        class M(nn.Module):
            def __init__(self):
                super().__init__()
                self.in_proj = nn.Linear(in_dim, 64)
                self.rnn = nn.RNN(64, 64, batch_first=True, nonlinearity="tanh")
                self.head = mlp_head()
            def hidden(self, x):
                return self.rnn(self.in_proj(x))[0]
            def forward(self, x):
                return self.head(self.hidden(x))
        return M()
    raise ValueError(f"Unknown hmm arch {arch}")


def train_hmm_task(job: tuple[dict, str]) -> dict:
    import torch
    import torch.nn.functional as F
    torch.set_num_threads(1)

    A, arch = job
    name = A["name"]
    P_actions = np.array(A["P_actions"], dtype=float)
    Olik = np.array(A["Olik"], dtype=float)
    pi = np.array(A["pi"], dtype=float)
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]

    seed = 20261123 + (sum(ord(c) for c in f"{name}:{arch}") * 137 + hash((name, arch)) % 100000) % 1000000
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_hmm_model(arch, L + n_obs, n_obs)
    opt = torch.optim.Adam(mdl.parameters(), lr=3e-3)
    t0 = time.time()
    steps = 1500
    for _ in range(steps):
        IN, TG, _, _ = sample_hmm_batch(P_actions, Olik, pi, BATCH, T_HMM, rng)
        logits = mdl(torch.from_numpy(IN))[:, BURN_HMM:]
        tgt = torch.from_numpy(TG)[:, BURN_HMM:]
        loss = F.cross_entropy(logits.reshape(-1, n_obs), tgt.reshape(-1))
        opt.zero_grad()
        loss.backward()
        opt.step()

    # Deterministic eval stream (400 trajectories -> 4000 post-burn belief states)
    eval_rng = np.random.default_rng(seed + 10**6)
    IN_ev, TG_ev, MU_ev, BAYES_ev = sample_hmm_batch(P_actions, Olik, pi, 400, T_HMM, eval_rng)
    with torch.no_grad():
        x_ev = torch.from_numpy(IN_ev)
        H_ev = mdl.hidden(x_ev).numpy()
        logits_ev = mdl(x_ev)[:, BURN_HMM:]
        ce_model = float(F.cross_entropy(logits_ev.reshape(-1, n_obs), torch.from_numpy(TG_ev)[:, BURN_HMM:].reshape(-1)))

    # Exact Bayes-optimal KL / CE on same trajectories
    p_bayes = np.clip(BAYES_ev[:, BURN_HMM:].reshape(-1, n_obs), 1e-12, 1.0)
    p_mod = np.exp(logits_ev.numpy() - logits_ev.numpy().max(axis=-1, keepdims=True))
    p_mod = p_mod / p_mod.sum(axis=-1, keepdims=True)
    p_mod = np.clip(p_mod.reshape(-1, n_obs), 1e-12, 1.0)
    kl_gap = float(np.mean(np.sum(p_bayes * (np.log(p_bayes) - np.log(p_mod)), axis=1)))
    ce_bayes = float(-np.mean(np.log(p_bayes[np.arange(len(p_bayes)), TG_ev[:, BURN_HMM:].ravel()])))

    # Linear belief decoding R^2 (train/test split across trajectories)
    H_tr = H_ev[:200, BURN_HMM:].reshape(-1, 64)
    H_te = H_ev[200:, BURN_HMM:].reshape(-1, 64)
    M_tr = MU_ev[:200, BURN_HMM:].reshape(-1, m)
    M_te = MU_ev[200:, BURN_HMM:].reshape(-1, m)
    # Add bias column to decode mu from h
    H_tr_b = np.column_stack([H_tr, np.ones(len(H_tr))])
    H_te_b = np.column_stack([H_te, np.ones(len(H_te))])
    coef, _, _, _ = np.linalg.lstsq(H_tr_b, M_tr, rcond=1e-5)
    M_pred = H_te_b @ coef
    ss_res = float(np.sum((M_te - M_pred) ** 2))
    ss_tot = float(np.sum((M_te - M_te.mean(axis=0, keepdims=True)) ** 2))
    belief_r2 = float(1.0 - ss_res / max(ss_tot, 1e-12))

    # Effective PCA 95% dimension of hidden states
    Hc = H_te - H_te.mean(axis=0, keepdims=True)
    _, s_pca, _ = np.linalg.svd(Hc, full_matrices=False)
    ev_pca = (s_pca ** 2) / max(float(np.sum(s_pca ** 2)), 1e-12)
    pca95_dim = int(np.searchsorted(np.cumsum(ev_pca), 0.95) + 1)

    # State-space basis V via ridge regression M -> H (H ≈ M V)
    M_all = np.concatenate([M_tr, M_te], axis=0)
    H_all = np.concatenate([H_tr, H_te], axis=0)
    V = np.linalg.solve(M_all.T @ M_all + 1e-6 * np.eye(m), M_all.T @ H_all)  # (m, 64)
    Dpi_h = np.diag(np.sqrt(pi))
    G_net_state = sym_perp(Dpi_h @ (V @ V.T) @ Dpi_h, Pperp)

    # Direct history-space centered kernel on 384 held-out histories
    H_sub = H_te[:384] - H_te[:384].mean(axis=0, keepdims=True)
    K_net = 0.5 * (H_sub @ H_sub.T + H_sub @ H_sub.T)
    Dpi_inv_h = np.diag(1.0 / np.sqrt(pi))
    R_sub = (M_te[:384] - pi[None, :]) @ Dpi_inv_h

    kin = dirichlet_kin_norm(G_net_state, Lkin)
    state_scores = {}
    hist_scores = {}
    lams = {}
    for op_name in OPS_ORDER:
        Wsrc = np.array(A[op_name], dtype=float)
        lam_op = invert_lambda_from_kin(Lkin, Wsrc, kin)
        G_pred = eval_G_at(Lkin, Wsrc, Pperp, lam_op)
        K_pred = R_sub @ G_pred @ R_sub.T
        state_scores[op_name] = cos_mat(G_net_state, G_pred)
        hist_scores[op_name] = cos_mat(K_net, K_pred)
        lams[op_name] = float(lam_op)

    W_act_sum = np.array(A["W_action_sum"], dtype=float)
    lam_act = invert_lambda_from_kin(Lkin, W_act_sum, kin)
    G_act_sum = eval_G_at(Lkin, W_act_sum, Pperp, lam_act)
    state_scores["W_action_sum"] = cos_mat(G_net_state, G_act_sum)
    hist_scores["W_action_sum"] = cos_mat(K_net, R_sub @ G_act_sum @ R_sub.T)

    res = {
        "arm": "hmm",
        "name": name,
        "family": A["family"],
        "arch": arch,
        "m": m,
        "kl_gap": kl_gap,
        "ce_model": ce_model,
        "ce_bayes": ce_bayes,
        "belief_r2": belief_r2,
        "pca95_dim": pca95_dim,
        "n_distinct_beliefs": int(len({tuple(np.round(r, 3).tolist()) for r in M_te[:384]})),
        "kin_norm": kin,
        "state_scores": state_scores,
        "hist_scores": hist_scores,
        "lams": lams,
        "elapsed_s": float(time.time() - t0),
    }
    p = RAW / f"hmm_{name}_{arch}.json"
    p.write_text(json.dumps(res))
    return res


def _run_job(kind_job):
    kind, job = kind_job
    if kind == "monoid":
        return train_monoid_task(job)
    return train_hmm_task(job)


def run():
    RAW.mkdir(parents=True, exist_ok=True)
    P = json.loads(PRED.read_text())
    jobs = []
    for A in P["monoids"]:
        for arch in ("gru_mlp", "rnn_mlp", "lru_lo_mlp", "lru_hi_mlp"):
            pth = RAW / f"monoid_{A['name']}_{arch}.json"
            if not pth.exists():
                jobs.append(("monoid", (A, arch)))
    for A in P["hmms"]:
        for arch in ("gru_mlp", "rnn_mlp"):
            pth = RAW / f"hmm_{A['name']}_{arch}.json"
            if not pth.exists():
                jobs.append(("hmm", (A, arch)))

    print(f"Pending jobs: {len(jobs)} (2 workers, threads=1)")
    t0 = time.time()
    if jobs:
        with ProcessPoolExecutor(max_workers=2) as ex:
            futs = [ex.submit(_run_job, j) for j in jobs]
            done = 0
            for fut in as_completed(futs):
                r = fut.result()
                done += 1
                if r["arm"] == "monoid":
                    print(f"[{done}/{len(jobs)}] monoid {r['name']} {r['arch']} fit={r['fit']:.3f} sum={r['scores']['W_sum']:.3f} bal={r['scores']['W_bal']:.3f} gm={r['scores']['W_gm']:.3f}", flush=True)
                else:
                    print(f"[{done}/{len(jobs)}] hmm {r['name']} {r['arch']} kl={r['kl_gap']:.4f} r2={r['belief_r2']:.3f} pca95={r['pca95_dim']} sum_h={r['hist_scores']['W_sum']:.3f} bal_h={r['hist_scores']['W_bal']:.3f}", flush=True)
    print(f"All runs finished in {time.time() - t0:.1f}s")


def analyse():
    P = json.loads(PRED.read_text())
    mon_runs = [json.loads(p.read_text()) for p in sorted(RAW.glob("monoid_*.json"))]
    hmm_runs = [json.loads(p.read_text()) for p in sorted(RAW.glob("hmm_*.json"))]
    assert len(mon_runs) == 48, f"Expected 48 monoid runs, got {len(mon_runs)}"
    assert len(hmm_runs) == 16, f"Expected 16 hmm runs, got {len(hmm_runs)}"

    # --- HHK.1: Contractive SSM Step-0 & Post-training shift ---
    lo_runs = [r for r in mon_runs if r["arch"] == "lru_lo_mlp"]
    hi_runs = [r for r in mon_runs if r["arch"] == "lru_hi_mlp"]
    lo_iso_match = sum(1 for r in lo_runs if r["step0"]["step0_cos_vs_gc_iso"]["0.2500"] > r["step0"]["step0_cos_vs_gc_iso"]["0.7225"])
    hi_iso_match = sum(1 for r in hi_runs if r["step0"]["step0_cos_vs_gc_iso"]["0.7225"] > r["step0"]["step0_cos_vs_gc_iso"]["0.2500"])
    lo_iso_mean = float(np.mean([r["step0"]["step0_cos_vs_gc_iso"]["0.2500"] for r in lo_runs]))
    hi_iso_mean = float(np.mean([r["step0"]["step0_cos_vs_gc_iso"]["0.7225"] for r in hi_runs]))
    hi_by_m = {r["name"]: r for r in hi_runs}
    paired_conv = [(r, hi_by_m[r["name"]]) for r in lo_runs if r["fit"] >= 0.90 and hi_by_m[r["name"]]["fit"] >= 0.90]
    post_shift = sum(1 for rl, rh in paired_conv if rh["best_gc_post"] > rl["best_gc_post"])
    if len(paired_conv) >= 6:
        hhk1 = "HELD" if (lo_iso_match >= 10 and hi_iso_match >= 10 and lo_iso_mean >= 0.90 and hi_iso_mean >= 0.90 and post_shift >= 0.75 * len(paired_conv)) else ("BROKEN" if (lo_iso_match < 6 or hi_iso_match < 6) else "NEITHER")
    else:
        hhk1 = "NEITHER" if (lo_iso_match >= 10 and hi_iso_match >= 10) else "BROKEN"

    # --- HHK.2: Non-Commuting Monoid Showdown ---
    by_arch = {}
    sum_wins_archs = 0
    bal_or_gm_beats_sum = 0
    for arch in ("gru_mlp", "rnn_mlp", "lru_lo_mlp", "lru_hi_mlp"):
        rs = [r for r in mon_runs if r["arch"] == arch and r["fit"] >= 0.90]
        if len(rs) < 6:
            by_arch[arch] = {"n": len(rs), "underpowered": True}
            continue
        means = {op: float(np.mean([r["scores"][op] for r in rs])) for op in OPS_ORDER}
        meds = {op: float(np.median([r["scores"][op] for r in rs])) for op in OPS_ORDER}
        win_mean = max(OPS_ORDER, key=lambda op: means[op])
        win_med = max(OPS_ORDER, key=lambda op: meds[op])
        if win_mean == "W_sum" and win_med == "W_sum":
            sum_wins_archs += 1
        if (means["W_bal"] > means["W_sum"] and meds["W_bal"] > meds["W_sum"]) or (means["W_gm"] > means["W_sum"] and meds["W_gm"] > meds["W_sum"]):
            bal_or_gm_beats_sum += 1
        by_arch[arch] = {"n": len(rs), "mean_cos": means, "median_cos": meds, "winner_mean": win_mean, "winner_median": win_med}
    if sum_wins_archs >= 3:
        hhk2 = "HELD"
    elif bal_or_gm_beats_sum >= 3:
        hhk2 = "BROKEN"
    else:
        hhk2 = "NEITHER"

    # --- HHK.3: Bayes Filtering & Belief Recovery ---
    n_bayes_ok = sum(1 for r in hmm_runs if r["kl_gap"] <= 0.03 and r["belief_r2"] >= 0.85)
    hhk3 = "HELD" if n_bayes_ok >= 12 else ("BROKEN" if n_bayes_ok < 8 else "NEITHER")

    # --- HHK.4: Reversible cyclic-group HMMs + Non-reversible HMMs ---
    cyc_conv = [r for r in hmm_runs if r["family"] == "cyclic_group_hmm" and r["kl_gap"] <= 0.05]
    cyc_beat_act = sum(
        1 for r in cyc_conv
        if r["hist_scores"]["W_sum"] > 0.50 and r["hist_scores"]["W_bal"] > 0.50 and r["hist_scores"]["W_gm"] > 0.50
        and r["state_scores"]["W_sum"] > 0.50 and r["state_scores"]["W_bal"] > 0.50
    )
    if len(cyc_conv) < 6:
        hhk4 = "NO VERDICT"
    elif cyc_beat_act >= len(cyc_conv) - 1 and cyc_beat_act >= 6:
        hhk4 = "HELD"
    elif cyc_beat_act == 0:
        hhk4 = "BROKEN"
    else:
        hhk4 = "NEITHER"

    hmm_summary = {}
    for fam in ("cyclic_group_hmm", "nonrev_hmm", "all"):
        rs = [r for r in hmm_runs if (fam == "all" or r["family"] == fam) and r["kl_gap"] <= 0.05]
        if rs:
            hmm_summary[fam] = {
                "n": len(rs),
                "mean_hist": {op: float(np.mean([r["hist_scores"][op] for r in rs])) for op in list(OPS_ORDER) + ["W_action_sum"]},
                "mean_state": {op: float(np.mean([r["state_scores"][op] for r in rs])) for op in list(OPS_ORDER) + ["W_action_sum"]},
                "mean_kl_gap": float(np.mean([r["kl_gap"] for r in rs])),
                "mean_belief_r2": float(np.mean([r["belief_r2"] for r in rs])),
            }

    # --- HHK.5: Hankel rank compression vs distinct posterior quotient ---
    hmm_conv = [r for r in hmm_runs if r["kl_gap"] <= 0.03]
    med_pca_ratio = float(np.median([r["pca95_dim"] / max(r["m"] - 1, 1) for r in hmm_conv])) if hmm_conv else 999.0
    all_compressed = all(r["pca95_dim"] <= r["m"] + 1 and r["pca95_dim"] < r["n_distinct_beliefs"] for r in hmm_conv)
    if len(hmm_conv) < 10:
        hhk5 = "NO VERDICT"
    elif all_compressed:
        hhk5 = "HELD"
    elif med_pca_ratio <= 1.5:
        hhk5 = "NEITHER"
    else:
        hhk5 = "BROKEN"

    verdicts = {"HHK.1": hhk1, "HHK.2": hhk2, "HHK.3": hhk3, "HHK.4": hhk4, "HHK.5": hhk5}
    out = {
        "verdicts": verdicts,
        "hhk1_ssm": {
            "lo_iso_match_12": lo_iso_match,
            "hi_iso_match_12": hi_iso_match,
            "lo_iso_mean_cos": lo_iso_mean,
            "hi_iso_mean_cos": hi_iso_mean,
            "paired_converged": len(paired_conv),
            "post_shift_hi_gt_lo": post_shift,
        },
        "hhk2_monoid_showdown": by_arch,
        "hhk3_hmm_bayes": {"n_ok_16": n_bayes_ok, "summary": hmm_summary},
        "hhk4_cyclic_recovery": {"cyc_conv": len(cyc_conv), "cyc_beat_action_only": cyc_beat_act},
        "hhk5_hankel_compression": {
            "n_conv": len(hmm_conv),
            "all_compressed": all_compressed,
            "med_pca_over_m_minus_1": med_pca_ratio,
            "per_run": [
                {"name": r["name"], "arch": r["arch"], "m": r["m"], "pca95_dim": r["pca95_dim"], "n_distinct_beliefs": r["n_distinct_beliefs"]}
                for r in hmm_runs
            ],
        },
    }
    OUT.write_text(json.dumps(out, indent=2))
    print("VERDICTS:", json.dumps(verdicts))
    print(json.dumps({k: out[k] for k in ("hhk1_ssm", "hhk2_monoid_showdown", "hhk4_cyclic_recovery")}, indent=2))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "predict":
        predict()
    elif cmd == "run":
        run()
    elif cmd == "analyse":
        analyse()
    else:
        raise ValueError(f"Unknown command {cmd}")
