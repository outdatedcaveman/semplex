"""Exact Z2 audit: orbit-response kernel vs uniform-prior past Gramian.

This tests whether the current Wc is the reachability factor of the
G18-style group orbit kernel. It is not: for a uniform prior under a
measure-preserving group action, Wc=0, while the one-hot orbit kernel
is nonzero. The current Wc is a prior/belief-sensitivity Gramian.
"""
from __future__ import annotations

import json
import numpy as np


def centered_projector(pi: np.ndarray) -> np.ndarray:
    w = np.sqrt(pi)
    one = w / np.linalg.norm(w)
    return np.eye(len(pi)) - np.outer(one, one)


def master_operators_z2(gamma_o: float = 0.8, horizon: int = 3, lam: float = 0.7):
    # Z2 acts on its two states by identity and swap.
    I = np.eye(2)
    S = np.array([[0.0, 1.0], [1.0, 0.0]])
    Ts = [I, S]
    pi = np.array([0.5, 0.5])
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = centered_projector(pi)

    # The current past/belief Gramian starts from the uniform prior rank-one form.
    Bt = np.outer(one, one)
    Wc = np.zeros((2, 2))
    gc = 0.8
    g = gc
    for _ in range(1, horizon):
        Bt = sum(T.T @ Bt @ T for T in Ts) / len(Ts)
        Wc += g * (Pperp @ Bt @ Pperp)
        g *= gc
    Wc = 0.5 * (Wc + Wc.T)

    # One-hot state readout, standardized exactly as in master_principle.py.
    O = np.eye(2)
    mu = (pi[:, None] * O).sum(0, keepdims=True)
    Oc = O - mu
    sd = np.sqrt((pi[:, None] * Oc**2).sum(0, keepdims=True))
    Os = Oc / np.maximum(sd, 1e-12)
    F = W[:, None] * Os
    At = F @ F.T
    Wo = np.zeros((2, 2))
    g = 1.0
    for _ in range(horizon):
        Wo += g * At
        At = sum(T @ At @ T.T for T in Ts) / len(Ts)
        g *= gamma_o
    Wo = Pperp @ (0.5 * (Wo + Wo.T)) @ Pperp

    # Dirichlet kinetic operator from the same two action matrices.
    Lkin = np.zeros((2, 2))
    for T in Ts:
        D = T - I
        Lkin += D.T @ D
    Lkin = 0.5 / len(Ts) * (Pperp @ Lkin @ Pperp)
    Lkin = 0.5 * (Lkin + Lkin.T)

    # The uniform random mixture of identity and swap is reversible:
    # detailed balance holds, so its stationary entropy production is zero.
    Pmix = 0.5 * (I + S)
    entropy_production = 0.0
    for i in range(2):
        for j in range(2):
            flow_ij = pi[i] * Pmix[i, j]
            flow_ji = pi[j] * Pmix[j, i]
            if flow_ij > 0 and flow_ji > 0:
                entropy_production += flow_ij * np.log(flow_ij / flow_ji)

    # Heat sandwich. On the centered one-dimensional subspace this scales Wo.
    evals, evecs = np.linalg.eigh(Lkin)
    H = (evecs * np.exp(-0.5 * lam * evals)) @ evecs.T
    G_sum = H @ (Wc + Wo) @ H
    G_sum = Pperp @ (0.5 * (G_sum + G_sum.T)) @ Pperp

    # Standard balanced-Gram candidate built from the current Wc and Wo.
    ec, vc = np.linalg.eigh(Wc)
    Wc_sqrt = (vc * np.sqrt(np.maximum(ec, 0.0))) @ vc.T
    G_balanced = Wc_sqrt @ Wo @ Wc_sqrt
    G_balanced = 0.5 * (G_balanced + G_balanced.T)

    # Alternative state-reachability baseline: all centered state directions
    # are admissible as initial perturbations.
    Wc_state = Pperp
    G_balanced_state = Wc_state @ Wo @ Wc_state

    # G18-style orbit kernel K(g,h)=E_w <o(gw),o(hw)> for one-hot readout.
    # Group elements and states are both encoded by {0,1}, multiplication is XOR.
    K_orbit = np.zeros((2, 2))
    for g in range(2):
        for h in range(2):
            K_orbit[g, h] = np.mean([
                float(np.dot(O[g ^ w], O[h ^ w])) for w in range(2)
            ])
    K_centered = Pperp @ K_orbit @ Pperp

    return {
        "pi": pi,
        "Pperp": Pperp,
        "Wc": Wc,
        "Wo": Wo,
        "Lkin": Lkin,
        "reversible_mixture": Pmix,
        "entropy_production": entropy_production,
        "G_sum": G_sum,
        "G_balanced_from_current_Wc": G_balanced,
        "Wc_state_baseline": Wc_state,
        "G_balanced_from_state_Wc": G_balanced_state,
        "K_orbit": K_orbit,
        "K_centered": K_centered,
    }


def arbitrary_readout_kernel(readout: np.ndarray) -> np.ndarray:
    """Finite-group orbit Gram for arbitrary vector-valued readout on Z2."""
    K = np.zeros((2, 2))
    for g in range(2):
        for h in range(2):
            K[g, h] = np.mean([
                np.dot(readout[g ^ w], readout[h ^ w]) for w in range(2)
            ])
    return K


def run():
    d = master_operators_z2()
    rng = np.random.default_rng(20261121)
    O_rand = rng.normal(size=(2, 3))
    K_rand = arbitrary_readout_kernel(O_rand)

    # Exact diagonal example: the sum and balanced product can rank modes oppositely.
    Wc_demo = np.diag([100.0, 60.0])
    Wo_demo = np.diag([1.0, 40.0])
    Wsum_demo = Wc_demo + Wo_demo
    Wbal_demo = np.sqrt(Wc_demo) @ Wo_demo @ np.sqrt(Wc_demo)

    return {
        "group": "Z2 acting on itself by left translation",
        "readout": "one-hot state readout",
        "current_Wc_norm": float(np.linalg.norm(d["Wc"])),
        "Wo_norm": float(np.linalg.norm(d["Wo"])),
        "orbit_kernel": d["K_orbit"].tolist(),
        "centered_orbit_kernel": d["K_centered"].tolist(),
        "G_sum": d["G_sum"].tolist(),
        "balanced_product_using_current_Wc": d["G_balanced_from_current_Wc"].tolist(),
        "balanced_product_using_centered_state_baseline": d["G_balanced_from_state_Wc"].tolist(),
        "norms": {
            k: float(np.linalg.norm(d[k]))
            for k in ("Wc", "Wo", "Lkin", "G_sum", "G_balanced_from_current_Wc",
                      "G_balanced_from_state_Wc", "K_orbit", "K_centered")
        },
        "thermodynamic_cost_check": {
            "reversible_mixture": d["reversible_mixture"].tolist(),
            "stationary_entropy_production": float(d["entropy_production"]),
            "dirichlet_kinematic_norm": float(np.linalg.norm(d["Lkin"])),
        },
        "arbitrary_readout_example": {
            "readout": O_rand.tolist(),
            "orbit_kernel": K_rand.tolist(),
            "eigenvalues": np.linalg.eigvalsh(K_rand).tolist(),
            "minimum_eigenvalue": float(np.linalg.eigvalsh(K_rand).min()),
        },
        "sum_vs_balanced_product_diagonal_counterexample": {
            "Wc": Wc_demo.tolist(),
            "Wo": Wo_demo.tolist(),
            "sum_eigenvalues": np.linalg.eigvalsh(Wsum_demo).tolist(),
            "balanced_product_eigenvalues": np.linalg.eigvalsh(Wbal_demo).tolist(),
            "sum_top_mode": int(np.argmax(np.diag(Wsum_demo))),
            "balanced_product_top_mode": int(np.argmax(np.diag(Wbal_demo))),
            "selection_reverses": bool(np.argmax(np.diag(Wsum_demo)) != np.argmax(np.diag(Wbal_demo))),
        },
        "assertions": {
            "current_Wc_is_zero": bool(np.allclose(d["Wc"], 0.0, atol=1e-12)),
            "Wo_is_nonzero": bool(np.linalg.norm(d["Wo"]) > 1e-8),
            "orbit_kernel_is_identity": bool(np.allclose(d["K_orbit"], np.eye(2))),
            "current_balanced_product_is_zero": bool(np.allclose(d["G_balanced_from_current_Wc"], 0.0, atol=1e-12)),
            "state_baseline_product_recovers_Wo": bool(np.allclose(d["G_balanced_from_state_Wc"], d["Wo"])),
            "arbitrary_readout_kernel_psd": bool(np.linalg.eigvalsh(K_rand).min() >= -1e-10),
            "sum_vs_balanced_product_selection_reverses": bool(
                np.argmax(np.diag(Wsum_demo)) != np.argmax(np.diag(Wbal_demo))
            ),
            "reversible_dynamics_have_zero_entropy_production": bool(abs(d["entropy_production"]) < 1e-12),
            "reversible_dynamics_have_nonzero_kinematic_cost": bool(np.linalg.norm(d["Lkin"]) > 1e-8),
        },
        "interpretation": (
            "The implemented Wc measures changes of the uniform prior under past actions. "
            "It is not the state-orbit reachability Gramian for the G18 orbit kernel. "
            "The sum Wc+Wo remains nonzero; the balanced product Wc^(1/2)WoWc^(1/2) "
            "collapses to zero unless a different past-feature map is specified."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
