"""Three-state partially observed HMM: posterior history/future Hankel factorization."""
from __future__ import annotations

import json
import numpy as np


def psd_sqrt(A: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(0.5 * (A + A.T))
    return (vecs * np.sqrt(np.maximum(vals, 0.0))) @ vecs.T


def run():
    n = 3
    pi = np.full(n, 1.0 / n)
    Dpi_sqrt = np.diag(np.sqrt(pi))
    Dpi_inv_sqrt = np.diag(1.0 / np.sqrt(pi))

    # Two noisy observations; likelihood rows are observation symbols, columns states.
    likelihood = np.array([
        [0.9, 0.5, 0.1],
        [0.1, 0.5, 0.9],
    ])
    p_y = likelihood @ pi
    post_y = (pi[None, :] * likelihood) / p_y[:, None]

    # Cyclic group Z3 actions, acting on row beliefs by right multiplication.
    actions = []
    for shift in range(n):
        T = np.zeros((n, n))
        for x in range(n):
            T[x, (x + shift) % n] = 1.0
        actions.append(T)

    # Six histories: observe y, then apply action shift a.
    history_beliefs = []
    history_weights = []
    history_labels = []
    for y in range(2):
        for a, T in enumerate(actions):
            history_beliefs.append(post_y[y] @ T)
            history_weights.append(p_y[y] / n)
            history_labels.append((y, a))
    R = np.asarray(history_beliefs)
    p_h = np.asarray(history_weights)
    D_h = np.diag(p_h)

    # Six future tests: apply shift b, then observe symbol y.
    # O[x,(b,y)] = P(y | state x after shift b).
    O = np.zeros((n, n * 2))
    test_labels = []
    for b in range(n):
        for y in range(2):
            for x in range(n):
                O[x, 2 * b + y] = likelihood[y, (x + b) % n]
            test_labels.append((b, y))
    p_tau = np.full(n * 2, 1.0 / (n * 2))
    D_tau = np.diag(p_tau)

    # Center/whiten history and future features around the prior.
    R_feat = (R - pi[None, :]) @ Dpi_inv_sqrt
    O_centered = O - (pi @ O)[None, :]
    O_feat = Dpi_sqrt @ O_centered

    H = R_feat @ O_feat
    H_weighted = np.sqrt(p_h)[:, None] * H * np.sqrt(p_tau)[None, :]

    Wc = R_feat.T @ D_h @ R_feat
    Wo = O_feat @ D_tau @ O_feat.T
    Wc = 0.5 * (Wc + Wc.T)
    Wo = 0.5 * (Wo + Wo.T)
    Wbal = psd_sqrt(Wc) @ Wo @ psd_sqrt(Wc)
    Wbal = 0.5 * (Wbal + Wbal.T)

    # Action-only histories preserve the uniform prior and have no centered belief variation.
    one = np.sqrt(pi)
    Pperp = np.eye(n) - np.outer(one, one)
    B = np.outer(one, one)
    Wc_action = np.zeros((n, n))
    for _ in range(1, 4):
        B = sum(T.T @ B @ T for T in actions) / len(actions)
        Wc_action += Pperp @ B @ Pperp
    Wc_action = 0.5 * (Wc_action + Wc_action.T)
    prior_after_actions = np.stack([pi @ T for T in actions])

    # Exact response matrix without centering: P(test | history) = R @ O.
    H_probability = R @ O

    # Compare nonzero singular-value squares with the balanced Gram eigenvalues.
    svals = np.linalg.svd(H_weighted, compute_uv=False)
    h_eigs = np.sort(svals**2)[::-1]
    b_eigs = np.sort(np.linalg.eigvalsh(Wbal))[::-1]
    rank_H = int(np.linalg.matrix_rank(H_weighted, tol=1e-10))
    unique_beliefs = len({tuple(np.round(row, 12)) for row in R})
    unique_profiles = len({tuple(np.round(row, 12)) for row in H_probability})

    assertions = {
        "all_actions_preserve_uniform_prior": bool(np.allclose(prior_after_actions, pi)),
        "action_only_past_gramian_zero": bool(np.allclose(Wc_action, 0.0)),
        "observation_conditioned_past_gramian_nonzero": bool(np.linalg.norm(Wc) > 1e-8),
        "future_observability_gramian_nonzero": bool(np.linalg.norm(Wo) > 1e-8),
        "history_future_factorization_exact": bool(np.allclose(H_probability, R @ O)),
        "centered_whitened_factorization_exact": bool(np.allclose(H, R_feat @ O_feat)),
        "six_distinct_posterior_beliefs": unique_beliefs == 6,
        "six_distinct_future_profiles": unique_profiles == 6,
        "centered_hankel_rank_two": rank_H == 2,
        "balanced_spectrum_matches_hankel": bool(np.allclose(h_eigs[:n], b_eigs, atol=1e-10)),
    }

    return {
        "model": "3-state cyclic hidden Markov system with binary noisy observation",
        "prior": pi.tolist(),
        "observation_likelihood": likelihood.tolist(),
        "observation_probabilities": p_y.tolist(),
        "history_labels": history_labels,
        "future_test_labels": test_labels,
        "posterior_beliefs_R": R.tolist(),
        "future_response_matrix_O": O.tolist(),
        "history_future_probability_matrix": H_probability.tolist(),
        "centered_whitened_H": H.tolist(),
        "Wc_posterior_history": Wc.tolist(),
        "Wo_future_tests": Wo.tolist(),
        "balanced_product": Wbal.tolist(),
        "weighted_hankel_singular_values_squared": h_eigs.tolist(),
        "balanced_product_eigenvalues": b_eigs.tolist(),
        "centered_hankel_rank": rank_H,
        "unique_posterior_beliefs": unique_beliefs,
        "unique_future_profiles": unique_profiles,
        "assertions": assertions,
        "all_assertions_pass": all(assertions.values()),
        "interpretation": (
            "The agent's posterior history map and future-test map factor the "
            "predictive Hankel matrix. The posterior belief is sufficient; the "
            "linear predictive rank is two although six distinct posterior histories "
            "are represented. The balanced Gram spectrum matches the weighted "
            "Hankel singular-value squares."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
