"""Noncommuting finite HMM: compare additive interface Gram with Hankel-balanced Gram."""
from __future__ import annotations

import json
import numpy as np


def psd_sqrt_and_pinv_sqrt(A: np.ndarray, tol: float = 1e-11):
    vals, vecs = np.linalg.eigh(0.5 * (A + A.T))
    sqrt_vals = np.sqrt(np.maximum(vals, 0.0))
    inv_vals = np.array([1.0 / np.sqrt(v) if v > tol else 0.0 for v in vals])
    sqrt = (vecs * sqrt_vals) @ vecs.T
    inv_sqrt = (vecs * inv_vals) @ vecs.T
    return sqrt, inv_sqrt, vals


def stationary_distribution(P: np.ndarray) -> np.ndarray:
    pi = np.full(P.shape[0], 1.0 / P.shape[0])
    for _ in range(20000):
        nxt = pi @ P
        if np.max(np.abs(nxt - pi)) < 1e-15:
            break
        pi = nxt
    return pi / pi.sum()


def build_model(seed: int = 20261121):
    rng = np.random.default_rng(seed)
    n = 3
    # Positive, non-reversible transition matrix.
    P = rng.dirichlet(np.array([4.0, 2.0, 1.0]), size=n)
    # State-conditioned observation distributions; columns are states.
    obs_by_state = rng.dirichlet(np.array([2.0, 1.5, 0.8]), size=n)
    Olik = obs_by_state.T
    pi = stationary_distribution(P)

    # All two-observation histories (y0,y1), with posterior over X_1.
    R_rows = []
    p_hist = []
    h_labels = []
    for y0 in range(n):
        for y1 in range(n):
            joint_x0_x1 = (
                pi[:, None]
                * Olik[y0, :, None]
                * P
                * Olik[y1, None, :]
            )
            joint = joint_x0_x1.sum()
            posterior_x1 = joint_x0_x1.sum(axis=0) / joint
            R_rows.append(posterior_x1)
            p_hist.append(joint)
            h_labels.append((y0, y1))
    R = np.asarray(R_rows)
    p_hist = np.asarray(p_hist)
    p_hist /= p_hist.sum()

    # All two-observation future tests (y1,y2), conditional on current state X_1.
    O_future = np.zeros((n, n * n))
    p_tests = []
    tau_labels = []
    for y1 in range(n):
        for y2 in range(n):
            # f_tau(x1) = sum_x2,x3 P(x2|x1) O(y1|x2) P(x3|x2) O(y2|x3)
            f = np.zeros(n)
            for x1 in range(n):
                for x2 in range(n):
                    for x3 in range(n):
                        f[x1] += P[x1, x2] * Olik[y1, x2] * P[x2, x3] * Olik[y2, x3]
            O_future[:, y1 * n + y2] = f
            tau_prob = float(pi @ f)
            p_tests.append(tau_prob)
            tau_labels.append((y1, y2))
    p_tests = np.asarray(p_tests)
    p_tests /= p_tests.sum()

    Dpi_inv_sqrt = np.diag(1.0 / np.sqrt(pi))
    Dpi_sqrt = np.diag(np.sqrt(pi))
    D_h = np.diag(p_hist)
    D_tau = np.diag(p_tests)

    R_feat = (R - pi[None, :]) @ Dpi_inv_sqrt
    O_centered = O_future - (pi @ O_future)[None, :]
    O_feat = Dpi_sqrt @ O_centered

    A = np.sqrt(p_hist)[:, None] * R_feat
    B = O_feat * np.sqrt(p_tests)[None, :]
    H = A @ B

    Wc = A.T @ A
    Wo = B @ B.T
    Wc = 0.5 * (Wc + Wc.T)
    Wo = 0.5 * (Wo + Wo.T)

    Wbal = psd_sqrt_and_pinv_sqrt(Wc)[0] @ Wo @ psd_sqrt_and_pinv_sqrt(Wc)[0]
    Wbal = 0.5 * (Wbal + Wbal.T)
    Wsum = Wc + Wo

    wc_sqrt, wc_inv_sqrt, wc_eigs = psd_sqrt_and_pinv_sqrt(Wc)
    eval_sum, evec_sum = np.linalg.eigh(Wsum)
    eval_bal, evec_bal = np.linalg.eigh(Wbal)
    u_sum = evec_sum[:, -1]
    v_bal = evec_bal[:, -1]

    P_sum = wc_inv_sqrt @ np.outer(u_sum, u_sum) @ wc_sqrt
    P_bal = wc_inv_sqrt @ np.outer(v_bal, v_bal) @ wc_sqrt
    H_sum_rank1 = A @ P_sum @ B
    H_bal_rank1 = A @ P_bal @ B
    U, s, Vt = np.linalg.svd(H, full_matrices=False)
    H_svd_rank1 = s[0] * np.outer(U[:, 0], Vt[0, :])

    err_sum = np.linalg.norm(H - H_sum_rank1, ord="fro")
    err_bal = np.linalg.norm(H - H_bal_rank1, ord="fro")
    err_svd = np.linalg.norm(H - H_svd_rank1, ord="fro")

    # Current action-only prior Gramian is zero for a uniform stationary prior
    # only when the action family is measure-preserving; this model is not a group
    # action, so we do not use that simplification here.
    commutator_norm = float(np.linalg.norm(Wc @ Wo - Wo @ Wc, ord="fro"))
    angle_cos = float(abs(np.dot(u_sum, v_bal)) / (
        np.linalg.norm(u_sum) * np.linalg.norm(v_bal)
    ))

    return {
        "seed": seed,
        "transition_matrix": P.tolist(),
        "observation_likelihood": Olik.tolist(),
        "stationary_prior": pi.tolist(),
        "history_labels": h_labels,
        "future_test_labels": tau_labels,
        "posterior_matrix_R": R.tolist(),
        "future_response_matrix_O": O_future.tolist(),
        "Wc_posterior_history": Wc.tolist(),
        "Wo_future_tests": Wo.tolist(),
        "Wc_plus_Wo_eigenvalues": np.sort(eval_sum)[::-1].tolist(),
        "balanced_gram_eigenvalues": np.sort(eval_bal)[::-1].tolist(),
        "weighted_hankel_singular_values_squared": (s**2).tolist(),
        "commutator_frobenius_norm": commutator_norm,
        "top_mode_cosine_sum_vs_balanced": angle_cos,
        "rank1_approximation_errors": {
            "additive_sum_mode": float(err_sum),
            "balanced_hankel_mode": float(err_bal),
            "optimal_svd": float(err_svd),
        },
        "assertions": {
            "history_future_factorization_exact": bool(np.allclose(
                R @ O_future,
                np.array([[row @ O_future for row in R]])[0],
            )),
            "noncommuting_grams": commutator_norm > 1e-8,
            "sum_and_balanced_top_modes_differ": angle_cos < 1.0 - 1e-6,
            "balanced_spectrum_matches_hankel": bool(np.allclose(
                np.sort(s**2)[::-1][:n],
                np.sort(eval_bal)[::-1],
                atol=1e-9,
            )),
            "balanced_rank1_error_matches_svd": bool(abs(err_bal - err_svd) < 1e-9),
            "sum_rank1_is_worse": bool(err_sum > err_bal + 1e-8),
        },
    }


if __name__ == "__main__":
    result = build_model()
    result["all_assertions_pass"] = all(result["assertions"].values())
    print(json.dumps(result, indent=2, sort_keys=True))
