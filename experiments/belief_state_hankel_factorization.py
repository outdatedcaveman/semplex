"""Finite Z2 controlled-HMM: action-only prior vs observation-conditioned past.

The example separates the hidden physical state from the agent's information
state. With action-only histories, a uniform prior remains uniform under the
group action and the past Gramian vanishes. Once one-hot observations are
included, posterior beliefs become point masses, the past Gramian is nonzero,
and the history-future response matrix factors through posterior beliefs.
"""
from __future__ import annotations

import json
import numpy as np


def centered_projector(pi: np.ndarray) -> np.ndarray:
    w = np.sqrt(pi)
    one = w / np.linalg.norm(w)
    return np.eye(len(pi)) - np.outer(one, one)


def run():
    pi = np.array([0.5, 0.5])
    Dpi_inv_sqrt = np.diag(1.0 / np.sqrt(pi))
    Pperp = centered_projector(pi)

    # Z2 actions on two hidden states: identity and swap.
    I = np.eye(2)
    S = np.array([[0.0, 1.0], [1.0, 0.0]])
    actions = [I, S]

    # Action-only histories: every action preserves the uniform prior.
    prior_feature = np.sqrt(pi)
    B0 = np.outer(prior_feature, prior_feature)
    Wc_action = np.zeros((2, 2))
    B = B0.copy()
    for _ in range(1, 4):
        B = sum(T.T @ B @ T for T in actions) / len(actions)
        Wc_action += Pperp @ B @ Pperp
    Wc_action = 0.5 * (Wc_action + Wc_action.T)

    # Observation y reveals the current state exactly; posterior is delta_y.
    posteriors = np.eye(2)
    past_features = (Dpi_inv_sqrt @ (posteriors - pi[None, :]).T).T
    Wc_observed = past_features.T @ np.diag(pi) @ past_features
    Wc_observed = 0.5 * (Wc_observed + Wc_observed.T)

    # Future tests: observe now, then after each of the two group actions.
    # Rows index hidden states; columns index (action, observed symbol).
    O_future = np.array([
        [1.0, 0.0, 0.0, 1.0],
        [0.0, 1.0, 1.0, 0.0],
    ])
    # Uniform test weighting, centered on the prior.
    Wo = Pperp @ (O_future @ (0.5 * np.eye(4)) @ O_future.T) @ Pperp
    Wo = 0.5 * (Wo + Wo.T)

    # History-future Hankel matrix: H(h,tau)=P(tau|h)=mu_h^T f_tau.
    # Here the posterior map is the identity, so H = R O with R=I.
    R_posterior = posteriors
    H = R_posterior @ O_future

    # The standard balanced product using the actual observation-conditioned
    # past Gramian, versus the action-only uniform-prior past Gramian.
    def psd_sqrt(A):
        vals, vecs = np.linalg.eigh(0.5 * (A + A.T))
        return (vecs * np.sqrt(np.maximum(vals, 0.0))) @ vecs.T

    Wc_action_sqrt = psd_sqrt(Wc_action)
    Wc_observed_sqrt = psd_sqrt(Wc_observed)
    balanced_action = Wc_action_sqrt @ Wo @ Wc_action_sqrt
    balanced_observed = Wc_observed_sqrt @ Wo @ Wc_observed_sqrt

    # Histories are predictively distinct exactly when their response rows differ.
    action_only_profile = pi @ O_future
    action_only_response_profiles = np.stack([action_only_profile, action_only_profile])
    observed_response_profiles = H
    action_only_profile_classes = len({tuple(row) for row in action_only_response_profiles})
    observed_profile_classes = len({tuple(row) for row in observed_response_profiles})

    return {
        "system": "Z2 hidden state with deterministic identity/swap actions",
        "prior": pi.tolist(),
        "observation_model": "one-hot observation reveals current state",
        "action_only_past_gramian": Wc_action.tolist(),
        "observation_conditioned_past_gramian": Wc_observed.tolist(),
        "future_observability_gramian": Wo.tolist(),
        "history_future_response_matrix_H": H.tolist(),
        "factorization": {
            "R_posterior": R_posterior.tolist(),
            "O_future": O_future.tolist(),
            "H_equals_R_times_O": bool(np.allclose(H, R_posterior @ O_future)),
        },
        "balanced_products": {
            "action_only_prior": balanced_action.tolist(),
            "observation_conditioned": balanced_observed.tolist(),
        },
        "profile_class_counts": {
            "action_only_histories": action_only_profile_classes,
            "observation_histories": observed_profile_classes,
        },
        "assertions": {
            "action_only_prior_gramian_zero": bool(np.allclose(Wc_action, 0.0, atol=1e-12)),
            "posterior_gramian_is_centered_projector": bool(np.allclose(Wc_observed, Pperp)),
            "future_gramian_nonzero": bool(np.linalg.norm(Wo) > 1e-8),
            "H_factorizes_through_posterior": bool(np.allclose(H, R_posterior @ O_future)),
            "action_only_balanced_product_zero": bool(np.allclose(balanced_action, 0.0, atol=1e-12)),
            "observed_balanced_product_nonzero": bool(np.linalg.norm(balanced_observed) > 1e-8),
            "action_only_one_profile": action_only_profile_classes == 1,
            "observation_histories_two_profiles": observed_profile_classes == 2,
        },
        "interpretation": (
            "The same physical system has one predictive belief state for an agent "
            "with action-only access to a uniform hidden state, but two predictive "
            "states for an agent receiving a fully revealing observation. The past "
            "Gramian must be built from the agent's posterior histories."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
