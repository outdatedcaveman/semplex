"""Exponential Heat-Filtered Kubo-Ando vs Matrix-KL Free Energy &
Bidirectional/Non-Ambivalent/Multi-Loop Gauge Showdown (`gemini/master-principle-free-energy`).

Companion to `MasterPrincipleFreeEnergy.lean` and `MasterPrincipleBouquet.lean`.

Structure:
  1. Arm 1A (12 fresh non-commuting monoids x 4 archs = 48 runs, steps=2000):
     - Pits `G_gm_heat(lam) = exp(-lam L/2)(Wc#Wo)exp(-lam L/2)` against
       `X_kl_gm(lam) = exp(log(Wc#Wo) - lam L)`, `G_sum_heat`, `X_kl_sum`, and
       `X_primal_var` under (a) K_norm-matched lam, (b) leave-one-monoid-out CV lam,
       and (c) 41-point oracle grid.
     - Verifies heat-filtered Kubo-Ando Riccati residual, Golden-Thompson trace gap
       `Tr(G_gm_heat) - Tr(X_kl_gm) >= 0`, raw/normalized exponential kinetic monotonicity,
       and log-partition / KL-trace convexity across `12/12` monoids.
  2. Arm 1B (8 fresh HMMs [4 cyclic-group + 4 unbalanced non-reversible] x 2 archs = 16 runs):
     - Evaluates dual exponential `G_dual_heat(lam)` & `X_kl_dual(lam)` vs `W_bal_dual`,
       `X_dual_var`, `G_gm_heat`, `X_kl_gm`, and `G_sum_heat` on both state & history kernels.
  3. Arm 2A (Class-balanced `D_4` & Non-Ambivalent `A_4` gauge rings: 2 groups x 4 models x 2 seeds = 16 runs):
     - `L_train in {3, 4}` (25% disjoint held-out `L=4`, plus 100% OOD `L=5` & `L=6`),
       2,500 steps, class-balanced inverse-frequency loss weighting, matched `16k +- 5%` params.
     - Compares `multiset_deepsets`, `palindromic_gru` (ambivalent proxy: forward + reverse-inverse),
       `ordered_gru`, and Complex Unitary `cayley_unitary_equivariant` (`M(g) in U(d), M(e) = I`).
     - Specifically measures chiral separation `C_3^+ vs C_3^-` on `A_4`.
  4. Arm 2B (`b_1 = 2` Two-Loop `S_3` Bouquet: 4 models x 3 seeds = 12 runs):
     - 11 simultaneous `Ad(S_3)`-orbits vs 9 per-loop class pairs (`L=3`/loop train + 25% held-out
       + OOD `L=4`/loop), 2,500 steps, class-balanced over all 11 orbits, matched `16k +- 5%` params.
     - Compares `multiset_deepsets`, `per_loop_gauge_pooled_gru`, `joint_bouquet_gru` (measuring
       intermediate vs penultimate deferred base-frame collapse), and `cayley_unitary_bouquet`.
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import permutations, product
import json
import math
import pathlib
import sys
import time
from typing import Callable

import numpy as np
from scipy.linalg import expm

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import spike81 as S81

RESULTS = ROOT / "experiments" / "results"
OUT = RESULTS / "master_principle_free_energy.json"
PRED = RESULTS / "master_principle_free_energy_predictions.json"

GAMMA_C = 0.6
GAMMA_O = 0.7
T_MON = 16
BURN_MON = 4
T_OP = 16
T_HMM = 12
BURN_HMM = 2
BATCH = 64

EPS_DEFAULT = 1e-4
LAM_GRID = tuple([0.0] + [float(x) for x in np.geomspace(1e-2, 50.0, 40)])

ARM1A_ARCHS = ("gru_mlp", "rnn_mlp", "leaky_a025", "vel_warmup")
ARM1B_ARCHS = ("gru_mlp", "vel_warmup")
ARM2A_MODELS = ("multiset_deepsets", "palindromic_gru", "ordered_gru", "cayley_unitary_equivariant")
ARM2B_MODELS = ("multiset_deepsets", "per_loop_gauge_pooled_gru", "joint_bouquet_gru", "cayley_unitary_bouquet")


# ---------------------------------------------------------------------------
# Linear Algebra & Free-Energy Operator Utilities
# ---------------------------------------------------------------------------

def cos_mat(A: np.ndarray, B: np.ndarray) -> float:
    na = float(np.linalg.norm(A))
    nb = float(np.linalg.norm(B))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.sum(A * B) / (na * nb))


def sym_mat(M: np.ndarray) -> np.ndarray:
    return 0.5 * (M + M.T)


def sym_perp(M: np.ndarray, Pperp: np.ndarray) -> np.ndarray:
    S = sym_mat(M)
    return sym_mat(Pperp @ S @ Pperp)


def perp_basis(Pperp: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(sym_mat(Pperp))
    return vecs[:, vals > 0.5]


def spd_eigh_power(A: np.ndarray, power: float, floor: float = 1e-14) -> np.ndarray:
    vals, vecs = np.linalg.eigh(sym_mat(A))
    safe = np.maximum(vals, floor)
    return sym_mat((vecs * (safe ** power)) @ vecs.T)


def spd_logm(A: np.ndarray, floor: float = 1e-14) -> np.ndarray:
    vals, vecs = np.linalg.eigh(sym_mat(A))
    safe = np.maximum(vals, floor)
    return sym_mat((vecs * np.log(safe)) @ vecs.T)


def sym_expm(H: np.ndarray) -> np.ndarray:
    vals, vecs = np.linalg.eigh(sym_mat(H))
    vals = np.clip(vals, -45.0, 45.0)
    return sym_mat((vecs * np.exp(vals)) @ vecs.T)


def spd_geom_mean(P: np.ndarray, Q: np.ndarray, floor: float = 1e-14) -> np.ndarray:
    Ph = spd_eigh_power(P, 0.5, floor=floor)
    Pih = spd_eigh_power(P, -0.5, floor=floor)
    mid = sym_mat(Pih @ sym_mat(Q) @ Pih)
    mid_h = spd_eigh_power(mid, 0.5, floor=floor)
    return sym_mat(Ph @ mid_h @ Ph)


def psd_powers(A: np.ndarray, rel_tol: float = 1e-4) -> tuple[np.ndarray, np.ndarray]:
    vals, vecs = np.linalg.eigh(sym_mat(A))
    top = float(max(vals.max(), 1e-12))
    thr = rel_tol * top
    sqrt_v = np.sqrt(np.maximum(vals, 0.0))
    inv_sqrt_v = np.where(vals > thr, 1.0 / np.sqrt(np.maximum(vals, 1e-15)), 0.0)
    return sym_mat((vecs * sqrt_v) @ vecs.T), sym_mat((vecs * inv_sqrt_v) @ vecs.T)


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


class FreeEnergyEvaluator:
    """Evaluates heat-filtered Kubo-Ando vs Matrix-KL free-energy operators in P_perp."""

    def __init__(
        self,
        Wc: np.ndarray,
        Wo: np.ndarray,
        Lkin: np.ndarray,
        Pperp: np.ndarray,
        o_gram: np.ndarray,
        eps_rel: float = EPS_DEFAULT,
    ):
        self.Pperp = sym_mat(Pperp)
        self.Q = perp_basis(self.Pperp)
        self.Lkin = sym_perp(Lkin, self.Pperp)
        self.Wc = sym_perp(Wc, self.Pperp)
        self.Wo = sym_perp(Wo, self.Pperp)
        self.o_gram = sym_perp(o_gram, self.Pperp)

        r = self.Q.shape[1]
        self.Lk_q = sym_mat(self.Q.T @ self.Lkin @ self.Q)
        ev_l, vec_l = np.linalg.eigh(self.Lk_q)
        self.Lk_q = sym_mat((vec_l * np.maximum(ev_l, 0.0)) @ vec_l.T)

        Wc_q = sym_mat(self.Q.T @ self.Wc @ self.Q)
        Wo_q = sym_mat(self.Q.T @ self.Wo @ self.Q)
        tr_c = max(float(np.trace(Wc_q)) / max(r, 1), 1e-12)
        tr_o = max(float(np.trace(Wo_q)) / max(r, 1), 1e-12)
        self.Wc_reg = sym_mat(Wc_q + (eps_rel * tr_c) * np.eye(r))
        self.Wo_reg = sym_mat(Wo_q + (1e-8 * tr_o) * np.eye(r))
        self.Wc_reg_inv = sym_mat(np.linalg.inv(self.Wc_reg))

        self.W_sum_q = sym_mat(self.Wc_reg + self.Wo_reg)
        self.W_gm_q = spd_geom_mean(self.Wc_reg, self.Wo_reg)
        self.W_dual_q = spd_geom_mean(self.Wc_reg_inv, self.Wo_reg)

        self.log_Wgm_q = spd_logm(self.W_gm_q)
        self.log_Wsum_q = spd_logm(self.W_sum_q)
        self.log_Wdual_q = spd_logm(self.W_dual_q)

        # Static baselines
        wc_h, wc_ih = psd_powers(self.Wc, rel_tol=1e-4)
        wbal = sym_perp(wc_h @ self.Wo @ wc_h, self.Pperp)
        inner_gm = sym_mat(wc_ih @ self.Wo @ wc_ih)
        inner_gm_h, _ = psd_powers(inner_gm, rel_tol=1e-6)
        wgm = sym_perp(wc_h @ inner_gm_h @ wc_h, self.Pperp)
        wbal_h, _ = psd_powers(wbal, rel_tol=1e-6)
        wbal_dual = sym_perp(wc_ih @ wbal_h @ wc_ih, self.Pperp)

        self.static = {
            "W_sum": sym_perp(self.Wc + self.Wo, self.Pperp),
            "W_bal": wbal,
            "W_gm": wgm,
            "W_bal_dual": wbal_dual,
            "W_c": self.Wc,
            "W_o": self.Wo,
            "o": self.o_gram,
        }

    def lift(self, M_q: np.ndarray) -> np.ndarray:
        return sym_perp(self.Q @ M_q @ self.Q.T, self.Pperp)

    def eval_op_q(self, family: str, lam: float) -> np.ndarray:
        if family == "G_gm_heat":
            H = sym_expm(-0.5 * lam * self.Lk_q)
            return sym_mat(H @ self.W_gm_q @ H)
        if family == "X_kl_gm":
            return sym_expm(sym_mat(self.log_Wgm_q - lam * self.Lk_q))
        if family == "G_sum_heat":
            H = sym_expm(-0.5 * lam * self.Lk_q)
            return sym_mat(H @ self.W_sum_q @ H)
        if family == "X_kl_sum":
            return sym_expm(sym_mat(self.log_Wsum_q - lam * self.Lk_q))
        if family == "X_primal_var":
            Al = sym_mat(self.Wc_reg_inv + lam * self.Lk_q)
            return spd_geom_mean(sym_mat(np.linalg.inv(Al)), self.Wo_reg)
        if family == "G_dual_heat":
            H = sym_expm(-0.5 * lam * self.Lk_q)
            return sym_mat(H @ self.W_dual_q @ H)
        if family == "X_kl_dual":
            return sym_expm(sym_mat(self.log_Wdual_q - lam * self.Lk_q))
        if family == "X_dual_var":
            Al = sym_mat(self.Wc_reg + lam * self.Lk_q)
            return spd_geom_mean(sym_mat(np.linalg.inv(Al)), self.Wo_reg)
        raise ValueError(f"Unknown family {family}")

    def eval_op(self, family: str, lam: float) -> np.ndarray:
        return self.lift(self.eval_op_q(family, lam))

    def exact_law_checks(self) -> dict:
        lams = [0.0, 0.05, 0.2, 1.0, 4.0, 15.0, 50.0]
        gm_raw, gm_norm, gm_Z = [], [], []
        kl_raw, kl_Z = [], []
        gt_gaps = []
        ric_errs = []

        for lv in lams:
            Gq = self.eval_op_q("G_gm_heat", lv)
            Xq = self.eval_op_q("X_kl_gm", lv)
            gm_Z.append(float(np.trace(Gq)))
            gm_raw.append(float(np.trace(self.Lk_q @ Gq)))
            gm_norm.append(float(np.trace(self.Lk_q @ Gq) / max(np.trace(Gq), 1e-14)))
            kl_Z.append(float(np.trace(Xq)))
            kl_raw.append(float(np.trace(self.Lk_q @ Xq)))
            gt_gaps.append(float(np.trace(Gq) - np.trace(Xq)))

            # Heat-filtered Kubo-Ando Riccati residual
            H = sym_expm(-0.5 * lv * self.Lk_q)
            Hinv = sym_expm(0.5 * lv * self.Lk_q)
            A_l = Hinv @ self.Wc_reg_inv @ Hinv
            B_l = H @ self.Wo_reg @ H
            res_norm = float(np.linalg.norm(Gq @ A_l @ Gq - B_l) / max(np.linalg.norm(B_l), 1e-12))
            ric_errs.append(res_norm)

        gm_raw_mono = all(gm_raw[i + 1] <= gm_raw[i] + 1e-8 for i in range(len(lams) - 1))
        gm_norm_mono = all(gm_norm[i + 1] <= gm_norm[i] + 1e-8 for i in range(len(lams) - 1))
        kl_raw_mono = all(kl_raw[i + 1] <= kl_raw[i] + 1e-8 for i in range(len(lams) - 1))

        # Midpoint log-convexity of Z_gm(lam) and convexity of Z_kl(lam)
        gm_log_convex = True
        kl_trace_convex = True
        for i in range(len(lams) - 1):
            a, b = lams[i], lams[i + 1]
            mid = 0.5 * (a + b)
            zm = float(np.trace(self.eval_op_q("G_gm_heat", mid)))
            if zm * zm > gm_Z[i] * gm_Z[i + 1] + 1e-10:
                gm_log_convex = False
            zk_m = float(np.trace(self.eval_op_q("X_kl_gm", mid)))
            if zk_m > 0.5 * (kl_Z[i] + kl_Z[i + 1]) + 1e-10:
                kl_trace_convex = False

        comm_gm_L = commutator_ratio(self.W_gm_q, self.Lk_q)
        return {
            "gm_raw_mono": bool(gm_raw_mono),
            "gm_norm_mono": bool(gm_norm_mono),
            "gm_log_convex": bool(gm_log_convex),
            "kl_raw_mono": bool(kl_raw_mono),
            "kl_trace_convex": bool(kl_trace_convex),
            "gt_min_gap": float(min(gt_gaps)),
            "gt_gap_lam1": float(gt_gaps[3]),
            "gt_gap_lam4": float(gt_gaps[4]),
            "max_riccati_rel_err": float(max(ric_errs)),
            "comm_gm_L": float(comm_gm_L),
        }

    def invert_lambda(self, family: str, kin_obs: float, hi: float = 50.0) -> float:
        if family == "X_primal_var":
            min_eig_A = float(np.linalg.eigvalsh(self.Wc_reg_inv).min())
            max_eig_L = float(np.linalg.eigvalsh(self.Lk_q).max())
            lo_use = max(-2.0, -0.8 * min_eig_A / max(max_eig_L, 1e-9))
        elif family == "X_dual_var":
            min_eig_A = float(np.linalg.eigvalsh(self.Wc_reg).min())
            max_eig_L = float(np.linalg.eigvalsh(self.Lk_q).max())
            lo_use = max(-2.0, -0.8 * min_eig_A / max(max_eig_L, 1e-9))
        else:
            lo_use = -4.0

        grid = np.linspace(lo_use, hi, 35)
        vals = []
        for lv in grid:
            try:
                M = self.eval_op(family, float(lv))
                vals.append(dirichlet_kin_norm(M, self.Lkin))
            except np.linalg.LinAlgError:
                vals.append(float("nan"))

        best_i = int(np.nanargmin([abs(v - kin_obs) for v in vals]))
        a_l = float(grid[max(0, best_i - 1)])
        b_l = float(grid[min(len(grid) - 1, best_i + 1)])
        ka = vals[max(0, best_i - 1)]
        kb = vals[min(len(grid) - 1, best_i + 1)]
        if not (math.isnan(ka) or math.isnan(kb)) and (ka - kin_obs) * (kb - kin_obs) <= 0:
            desc = (ka >= kb)
            for _ in range(32):
                mid = 0.5 * (a_l + b_l)
                km = dirichlet_kin_norm(self.eval_op(family, mid), self.Lkin)
                if (km > kin_obs) == desc:
                    a_l = mid
                else:
                    b_l = mid
            return float(0.5 * (a_l + b_l))
        return float(grid[best_i])

    def score_arm1a(self, G_net: np.ndarray) -> dict:
        kin_obs = dirichlet_kin_norm(G_net, self.Lkin)
        scores, lams, curves = {}, {}, {}
        for fam in ("G_gm_heat", "X_kl_gm", "G_sum_heat", "X_kl_sum", "X_primal_var"):
            lam = self.invert_lambda(fam, kin_obs)
            scores[fam] = cos_mat(G_net, self.eval_op(fam, lam))
            lams[fam] = float(lam)
            grid_c = [cos_mat(G_net, self.eval_op(fam, lg)) for lg in LAM_GRID]
            bi = int(np.argmax(grid_c))
            scores[f"{fam}_best"] = float(grid_c[bi])
            lams[f"{fam}_best"] = float(LAM_GRID[bi])
            curves[fam] = grid_c
        for st_name, mat in self.static.items():
            scores[st_name] = cos_mat(G_net, mat)
        return {"kin_norm": kin_obs, "scores": scores, "lams": lams, "curves": curves}


# ---------------------------------------------------------------------------
# Pre-Registration Generator (12 Monoids + 8 HMMs + Finite Group Invariants)
# ---------------------------------------------------------------------------

def monoid_base_operators(Dl: np.ndarray, O: np.ndarray, pi: np.ndarray) -> dict:
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
    Fmat = W[:, None] * Os
    At = Fmat @ Fmat.T
    o_gram = sym_perp(At, Pperp)

    Wo = np.zeros((m, m))
    g = 1.0
    for _ in range(T_OP):
        Wo += g * At
        At_next = np.zeros((m, m))
        for Ta in Ts:
            At_next += Ta @ At @ Ta.T
        At = At_next / L
        g *= GAMMA_O
    Wo = sym_perp(Wo, Pperp)

    Bt = np.outer(one, one)
    Wc = np.zeros((m, m))
    g = GAMMA_C
    for _ in range(1, T_OP):
        Bt_next = np.zeros((m, m))
        for Ta in Ts:
            Bt_next += Ta.T @ Bt @ Ta
        Bt = Bt_next / L
        Wc += g * (Pperp @ Bt @ Pperp)
        g *= GAMMA_C
    Wc = sym_perp(Wc, Pperp)

    return {"Pperp": Pperp, "Lkin": Lkin, "Wc": Wc, "Wo": Wo, "o": o_gram}


def compute_hmm_operators(P_actions: np.ndarray, Olik: np.ndarray, pi: np.ndarray, rng: np.random.Generator) -> dict:
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(m) - np.outer(one, one)
    Dpi_inv_h = np.diag(1.0 / np.sqrt(pi))
    Dpi_h = np.diag(np.sqrt(pi))

    Ts = [((W[:, None] * P_actions[a]) / W[None, :]) for a in range(L)]
    Lkin = np.zeros((m, m))
    for Ta in Ts:
        diff = Ta - np.eye(m)
        Lkin += diff.T @ diff
    Lkin = 0.5 / L * sym_perp(Lkin, Pperp)

    mu_list = []
    for _ in range(400):
        x = int(rng.choice(m, p=pi))
        bel = pi.copy()
        for t in range(T_HMM):
            y = int(rng.choice(n_obs, p=Olik[:, x]))
            bel = bel * Olik[y]
            bel = bel / max(float(bel.sum()), 1e-15)
            if t >= BURN_HMM:
                mu_list.append(bel.copy())
            a = int(rng.integers(L))
            x = int(rng.choice(m, p=P_actions[a, x]))
            bel = bel @ P_actions[a]
            bel = bel / max(float(bel.sum()), 1e-15)
    R_raw = np.asarray(mu_list, dtype=float)
    N_hist = R_raw.shape[0]
    R_feat = ((R_raw - pi[None, :]) @ Dpi_inv_h) / math.sqrt(N_hist)
    Wc_obs = sym_perp(R_feat.T @ R_feat, Pperp)

    cols = []
    weights = []
    horizon = 3 if (L ** 3) * (n_obs ** 3) <= 256 else 2
    vecs = [np.ones(m, dtype=float)]
    g = 1.0
    for k in range(1, horizon + 1):
        nxt = []
        for v in vecs:
            for a in range(L):
                for y in range(n_obs):
                    nxt.append(P_actions[a] @ (Olik[y] * v))
        vecs = nxt
        w_per = g / (L ** k)
        for v in vecs:
            cols.append(v)
            weights.append(w_per)
        g *= GAMMA_O
    O_fut = np.column_stack(cols)
    w_arr = np.asarray(weights, dtype=float)
    O_cent = O_fut - (pi @ O_fut)[None, :]
    O_feat = Dpi_h @ O_cent * np.sqrt(w_arr)[None, :]
    Wo_obs = sym_perp(O_feat @ O_feat.T, Pperp)

    return {
        "Lkin": Lkin,
        "Pperp": Pperp,
        "Wc_obs": Wc_obs,
        "Wo_obs": Wo_obs,
        "comm_ratio_obs": commutator_ratio(Wc_obs, Wo_obs),
    }


@dataclass(frozen=True)
class FiniteGroup:
    name: str
    elements: tuple
    identity: object
    mul_fn: Callable[[object, object], object]
    inv_fn: Callable[[object], object]

    def build_tables(self):
        e2i = {e: i for i, e in enumerate(self.elements)}
        G = len(self.elements)
        mul = np.array([[e2i[self.mul_fn(a, b)] for b in self.elements] for a in self.elements], dtype=np.int64)
        inv = np.array([e2i[self.inv_fn(a)] for a in self.elements], dtype=np.int64)
        unseen = set(range(G))
        classes = []
        while unseen:
            rep = min(unseen)
            cset = sorted({int(mul[mul[k, rep], inv[k]]) for k in range(G)})
            classes.append(tuple(cset))
            unseen.difference_update(cset)
        classes.sort(key=lambda c: (len(c), c[0]))
        cls_of = np.zeros(G, dtype=np.int64)
        for ci, cset in enumerate(classes):
            for el in cset:
                cls_of[el] = ci
        return {
            "G": G,
            "id": e2i[self.identity],
            "mul": mul,
            "inv": inv,
            "classes": classes,
            "cls_of": cls_of,
            "n_cls": len(classes),
        }


def make_s3_group() -> FiniteGroup:
    elems = tuple(permutations(range(3)))
    return FiniteGroup(
        "S3",
        elems,
        (0, 1, 2),
        lambda p, q: tuple(p[q[i]] for i in range(3)),
        lambda p: tuple(p.index(i) for i in range(3)),
    )


def make_d4_group() -> FiniteGroup:
    elems = tuple((k, e) for k in range(4) for e in range(2))
    return FiniteGroup(
        "D4",
        elems,
        (0, 0),
        lambda a, b: ((a[0] + (-1 if a[1] else 1) * b[0]) % 4, (a[1] + b[1]) % 2),
        lambda a: ((-a[0]) % 4, 0) if a[1] == 0 else (a[0], 1),
    )


def make_a4_group() -> FiniteGroup:
    def is_even(p):
        invs = sum(1 for i in range(4) for j in range(i + 1, 4) if p[i] > p[j])
        return invs % 2 == 0
    elems = tuple(p for p in permutations(range(4)) if is_even(p))
    return FiniteGroup(
        "A4",
        elems,
        (0, 1, 2, 3),
        lambda p, q: tuple(p[q[i]] for i in range(4)),
        lambda p: tuple(p.index(i) for i in range(4)),
    )


def a4_chiral_classes(tab: dict) -> tuple[int, int]:
    """Identify the two mutually-inverse size-4 3-cycle classes C_3^+ and C_3^- in A_4."""
    inv = tab["inv"]
    cls_of = tab["cls_of"]
    size4 = [ci for ci, cset in enumerate(tab["classes"]) if len(cset) == 4]
    assert len(size4) == 2, f"Expected 2 size-4 classes in A4, got {tab['classes']}"
    c_plus, c_minus = size4[0], size4[1]
    assert int(cls_of[inv[tab["classes"][c_plus][0]]]) == c_minus
    return c_plus, c_minus


def s3_bouquet_tables():
    """Exact 11 simultaneous Ad(S_3)-orbits vs 9 per-loop class pairs on S_3 x S_3."""
    tab = make_s3_group().build_tables()
    G, mul, inv, cls_of = tab["G"], tab["mul"], tab["inv"], tab["cls_of"]
    unseen = set((h1, h2) for h1 in range(G) for h2 in range(G))
    orbits = []
    while unseen:
        rep = min(unseen)
        orb = sorted({(int(mul[mul[k, rep[0]], inv[k]]), int(mul[mul[k, rep[1]], inv[k]])) for k in range(G)})
        orbits.append(orb)
        unseen.difference_update(orb)
    orbits.sort(key=lambda o: (len(o), o[0]))
    orb_of = np.zeros((G, G), dtype=np.int64)
    for oi, orb in enumerate(orbits):
        for h1, h2 in orb:
            orb_of[h1, h2] = oi

    # Find exact split pairs for both tau-tau and c-c^-1
    tau_cls = [ci for ci, c in enumerate(tab["classes"]) if len(c) == 3][0]
    cyc_cls = [ci for ci, c in enumerate(tab["classes"]) if len(c) == 2][0]
    tau_orbs = [oi for oi, orb in enumerate(orbits)
                if cls_of[orb[0][0]] == tau_cls and cls_of[orb[0][1]] == tau_cls]
    cyc_orbs = [oi for oi, orb in enumerate(orbits)
                if cls_of[orb[0][0]] == cyc_cls and cls_of[orb[0][1]] == cyc_cls]
    assert len(orbits) == 11, f"Expected 11 S3 bouquet orbits, got {len(orbits)}"
    assert len(tau_orbs) == 2 and len(cyc_orbs) == 2
    return {
        **tab,
        "orbits": orbits,
        "orb_of": orb_of,
        "n_orbits": len(orbits),
        "tau_split_orbs": tau_orbs,
        "cyc_split_orbs": cyc_orbs,
    }


def balanced_acc(preds: np.ndarray, targets: np.ndarray, n_cls: int) -> float:
    accs = []
    for c in range(n_cls):
        mask = (targets == c)
        if mask.any():
            accs.append(float((preds[mask] == targets[mask]).mean()))
    return float(np.mean(accs))


def generate_predictions(force: bool = False) -> dict:
    if PRED.exists() and not force:
        return json.loads(PRED.read_text(encoding="utf-8"))

    # 1. 12 fresh non-commuting monoids (seed base 5100)
    rng_mon = np.random.default_rng(2026112401)
    cands_mon = []
    seen_specs = set()
    for _ in range(800):
        d, o = S81.random_automaton(rng_mon, 8, 2, "free")
        D, O, s0 = S81.minimize(d, o, start=0)
        if D.shape[1] < 6 or O.min() == O.max():
            continue
        sig = (tuple(map(tuple, D.tolist())), tuple(O.tolist()), int(s0))
        if sig in seen_specs:
            continue
        seen_specs.add(sig)
        Dl = np.vstack([D, np.arange(D.shape[1])[None]])
        k, m = Dl.shape
        pi = S81.visit_dist(Dl, s0, np.ones(k) / k, T=T_MON, burn=BURN_MON)
        if (pi <= 1e-3).any():
            continue
        ops = monoid_base_operators(Dl, O, pi)
        Wc, Wo, Lkin, Pperp, o_gr = ops["Wc"], ops["Wo"], ops["Lkin"], ops["Pperp"], ops["o"]
        if np.linalg.norm(Wc) < 1e-2 or np.linalg.norm(Wo) < 1e-2:
            continue
        comm_wc_wo = commutator_ratio(Wc, Wo)
        if comm_wc_wo < 0.12:
            continue
        ev = FreeEnergyEvaluator(Wc, Wo, Lkin, Pperp, o_gr, eps_rel=EPS_DEFAULT)
        laws = ev.exact_law_checks()
        if not (laws["gm_raw_mono"] and laws["gm_norm_mono"] and laws["gm_log_convex"] and
                laws["kl_raw_mono"] and laws["kl_trace_convex"]):
            continue
        if laws["comm_gm_L"] < 0.05 or laws["gt_gap_lam1"] <= 1e-6:
            continue
        sep = float(np.linalg.norm(ev.eval_op("G_gm_heat", 1.0) - ev.eval_op("X_kl_gm", 1.0)) /
                    max(float(np.linalg.norm(ev.eval_op("G_gm_heat", 1.0))), 1e-12))
        cands_mon.append({
            "D": D.tolist(),
            "Dl": Dl.tolist(),
            "out": O.tolist(),
            "s0": int(s0),
            "m": int(m),
            "L": int(k),
            "pi": pi.tolist(),
            "Pperp": Pperp.tolist(),
            "Lkin": Lkin.tolist(),
            "Wc": Wc.tolist(),
            "Wo": Wo.tolist(),
            "o": o_gr.tolist(),
            "comm_wc_wo": comm_wc_wo,
            "gm_kl_sep": sep,
            **laws,
        })
        if len(cands_mon) >= 28:
            break

    assert len(cands_mon) >= 12, f"Expected >=12 monoids, found {len(cands_mon)}"
    cands_mon.sort(key=lambda r: -r["gm_kl_sep"])
    picked_mon = cands_mon[:12]
    for idx, r in enumerate(picked_mon):
        r["name"] = f"NCM_FE{idx:02d}"
        r["seed"] = 5100 + idx

    # 2. 8 fresh HMMs (4 cyclic + 4 unbalanced non-reversible, seed 5200..5207)
    rng_hmm = np.random.default_rng(2026112402)
    hmms = []
    cyc_specs = [
        ("hmm_cyc_Z4", 4, np.array([[0.88, 0.70, 0.30, 0.12], [0.12, 0.30, 0.70, 0.88]], float)),
        ("hmm_cyc_Z5", 5, np.array([[0.90, 0.74, 0.48, 0.22, 0.10], [0.10, 0.26, 0.52, 0.78, 0.90]], float)),
        ("hmm_cyc_Z6", 6, np.array([[0.92, 0.78, 0.58, 0.38, 0.20, 0.08], [0.08, 0.22, 0.42, 0.62, 0.80, 0.92]], float)),
        ("hmm_cyc_Z7", 7, np.array([
            [0.80, 0.60, 0.40, 0.20, 0.10, 0.20, 0.50],
            [0.10, 0.25, 0.40, 0.55, 0.45, 0.30, 0.20],
            [0.10, 0.15, 0.20, 0.25, 0.45, 0.50, 0.30],
        ], float)),
    ]
    for idx, (nm, m, Olik) in enumerate(cyc_specs):
        P_actions = np.zeros((2, m, m), dtype=float)
        step2 = 2 if m >= 5 else 3
        for x in range(m):
            P_actions[0, x, (x + 1) % m] = 1.0
            P_actions[1, x, (x + step2) % m] = 1.0
        pi = np.ones(m) / m
        hops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        hmms.append({
            "name": nm,
            "seed": 5200 + idx,
            "family": "cyclic_group_hmm",
            "m": m,
            "L": 2,
            "n_obs": int(Olik.shape[0]),
            "P_actions": P_actions.tolist(),
            "Olik": Olik.tolist(),
            "pi": pi.tolist(),
            **{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in hops.items()},
        })

    nr_cnt = 0
    while nr_cnt < 4:
        m = [4, 5, 5, 6][nr_cnt]
        n_obs = [2, 2, 3, 2][nr_cnt]
        P_actions = np.zeros((2, m, m), dtype=float)
        alpha_p = np.linspace(4.5, 0.6, m)
        for a in range(2):
            for x in range(m):
                P_actions[a, x] = rng_hmm.dirichlet(np.roll(alpha_p, x + 2 * a))
        Olik = np.clip(rng_hmm.dirichlet(np.full(n_obs, 0.85), size=m).T, 0.05, 0.95)
        Olik /= Olik.sum(axis=0, keepdims=True)
        pi = stationary_distribution(0.5 * (P_actions[0] + P_actions[1]))
        if pi.min() < 0.04:
            continue
        hops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        if hops["comm_ratio_obs"] < 0.12 or np.linalg.norm(hops["Wc_obs"]) < 1e-2:
            continue
        hmms.append({
            "name": f"hmm_nr_V{nr_cnt}",
            "seed": 5204 + nr_cnt,
            "family": "nonrev_hmm",
            "m": m,
            "L": 2,
            "n_obs": n_obs,
            "P_actions": P_actions.tolist(),
            "Olik": Olik.tolist(),
            "pi": pi.tolist(),
            **{k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in hops.items()},
        })
        nr_cnt += 1

    # 3. Theoretical ceilings for D_4, A_4 (multiset & palindromic), and S_3 bouquet
    arm2a_ceilings = {}
    for grp in (make_d4_group(), make_a4_group()):
        tab = grp.build_tables()
        G, mul, inv, cls_of, n_cls = tab["G"], tab["mul"], tab["inv"], tab["cls_of"], tab["n_cls"]
        rng_m = np.random.default_rng(5499 + G)
        samples = (
            np.array(list(product(range(G), repeat=4)), dtype=np.int64)
            if G ** 4 <= 4096
            else rng_m.integers(0, G, size=(4096, 4))
        )
        h = samples[:, 0]
        for t in range(1, 4):
            h = mul[samples[:, t], h]
        ys = cls_of[h]
        ms_counts: dict[tuple[int, ...], Counter] = {}
        pal_counts: dict[tuple[int, ...], Counter] = {}
        for row, y in zip(samples.tolist(), ys.tolist()):
            ms = tuple(sorted(row))
            ms_counts.setdefault(ms, Counter())[y] += 1
            rev_inv = [int(inv[x]) for x in reversed(row)]
            pk = min(tuple(row), tuple(rev_inv))
            pal_counts.setdefault(pk, Counter())[y] += 1
        ms_preds = np.array([ms_counts[tuple(sorted(r))].most_common(1)[0][0] for r in samples.tolist()])
        pal_preds = np.array([
            pal_counts[min(tuple(r), tuple(int(inv[x]) for x in reversed(r)))].most_common(1)[0][0]
            for r in samples.tolist()
        ])
        arm2a_ceilings[grp.name] = {
            "G": G,
            "n_cls": n_cls,
            "class_sizes": [len(c) for c in tab["classes"]],
            "multiset_opt_bacc_L4": balanced_acc(ms_preds, ys, n_cls),
            "palindromic_opt_bacc_L4": balanced_acc(pal_preds, ys, n_cls),
        }

    bq = s3_bouquet_tables()
    G, mul, cls_of, orb_of, n_orb = bq["G"], bq["mul"], bq["cls_of"], bq["orb_of"], bq["n_orbits"]
    samples_b = np.array(list(product(range(G), repeat=6)), dtype=np.int64)
    h1 = mul[samples_b[:, 2], mul[samples_b[:, 1], samples_b[:, 0]]]
    h2 = mul[samples_b[:, 5], mul[samples_b[:, 4], samples_b[:, 3]]]
    yb = orb_of[h1, h2]
    per_loop_counts: dict[tuple[int, int], Counter] = {}
    for c1, c2, y in zip(cls_of[h1].tolist(), cls_of[h2].tolist(), yb.tolist()):
        per_loop_counts.setdefault((c1, c2), Counter())[y] += 1
    per_loop_preds = np.array([
        per_loop_counts[(int(c1), int(c2))].most_common(1)[0][0]
        for c1, c2 in zip(cls_of[h1].tolist(), cls_of[h2].tolist())
    ])
    bouquet_ceiling = {
        "n_joint_orbits": n_orb,
        "orbit_sizes": [len(o) for o in bq["orbits"]],
        "per_loop_class_pairs": 9,
        "per_loop_bayes_bacc": balanced_acc(per_loop_preds, yb, n_orb),
        "per_loop_bayes_acc": float((per_loop_preds == yb).mean()),
    }

    pre_reg = {
        "HFE.1": "Compare G_gm_heat(lam) vs X_kl_gm(lam) = exp(log(Wc#Wo)-lam L) across 48 Arm 1A runs (matched, LOOCV, oracle grid).",
        "HFE.2": "Test exponential duals G_dual_heat/X_kl_dual vs W_bal_dual & G_gm_heat across 16 Arm 1B HMM runs (state & history).",
        "HFE.3": "Verify rnn_mlp -> leaky_a025 & vel_warmup reduce kin_norm and raise inferred lam(G_gm_heat) & lam(X_kl_gm) monotonically.",
        "HFE.4": "Verify class-balanced D_4 & non-ambivalent A_4 separation: palindromic_gru fails C3+ vs C3- (<0.02), Complex Unitary Cayley succeeds + OOD L=5,6.",
        "HFE.5": "Verify b1=2 S_3 two-loop bouquet: per_loop_gauge_pooled_gru fails both split pairs (<0.02), joint/unitary succeed + deferred base-frame collapse.",
        "HFE.6": "Verify exact Riccati, Golden-Thompson gap >=0 (>0 when non-commuting), monotonicity, log-convexity, & U(d) unitarity <1e-5.",
    }

    data = {
        "pre_registration": pre_reg,
        "monoids": picked_mon,
        "hmms": hmms,
        "arm2a_ceilings": arm2a_ceilings,
        "bouquet_ceiling": bouquet_ceiling,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


# ---------------------------------------------------------------------------
# Arm 1A & 1B Training Runners
# ---------------------------------------------------------------------------

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
    return torch.from_numpy(X).long(), torch.from_numpy(O_mat[ST].astype(np.float32)), ST


def make_arm1a_model(arch: str, L: int, k_out: int):
    import torch
    import torch.nn as nn

    def mlp_head():
        return nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, k_out))

    if arch == "gru_mlp":
        class M(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(L, 16)
                self.rnn = nn.GRU(16, 64, batch_first=True)
                self.head = mlp_head()
            def hidden(self, X):
                return self.rnn(self.emb(X))[0]
            def forward(self, X):
                return self.head(self.hidden(X))
        return M()

    alpha = 0.25 if arch == "leaky_a025" else 1.0
    class LeakyRNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.alpha = float(alpha)
            self.emb = nn.Embedding(L, 16)
            self.cell = nn.RNNCell(16, 64, nonlinearity="tanh")
            nn.init.orthogonal_(self.cell.weight_hh)
            self.head = mlp_head()
        def hidden(self, X):
            u = self.emb(X)
            h = torch.zeros(X.shape[0], 64, dtype=u.dtype, device=u.device)
            hs = []
            a = self.alpha
            for t in range(X.shape[1]):
                h_c = self.cell(u[:, t], h)
                h = (1.0 - a) * h + a * h_c if a < 1.0 else h_c
                hs.append(h)
            return torch.stack(hs, dim=1)
        def forward(self, X):
            return self.head(self.hidden(X))
    return LeakyRNN()


def run_arm1a_task(A: dict, arch: str, raw_dir: pathlib.Path, steps: int = 2000) -> dict:
    import torch
    import torch.nn as nn
    torch.set_num_threads(1)

    name = A["name"]
    Dl = np.array(A["Dl"], dtype=np.int64)
    O = np.array(A["out"], dtype=np.float32)
    pi = np.array(A["pi"], dtype=float)
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    Wc = np.array(A["Wc"], dtype=float)
    Wo = np.array(A["Wo"], dtype=float)
    o_gram = np.array(A["o"], dtype=float)
    L, m = Dl.shape
    k_out = 1 if O.ndim == 1 else O.shape[1]

    arch_off = ARM1A_ARCHS.index(arch) * 1000
    seed = int(A["seed"]) + arch_off
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_arm1a_model(arch, L, k_out)
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=3e-4)
    use_vel = (arch == "vel_warmup")
    t0 = time.time()

    for step in range(steps):
        X, Y, _ = fast_sample_monoid(Dl, O, A["s0"], BATCH, T_MON, rng)
        H = mdl.hidden(X)
        logits = mdl.head(H)
        loss = nn.functional.binary_cross_entropy_with_logits(logits[:, BURN_MON:], Y[:, BURN_MON:])
        if use_vel and step >= steps // 2:
            half = steps // 2
            mu = 0.05 if step >= half + half // 2 else 0.05 * ((step - half) / max(half // 2, 1))
            H_st = H[:, BURN_MON:]
            dh = (H_st[:, 1:] - H_st[:, :-1]).pow(2).mean()
            var_h = (H_st - H_st.mean(dim=(0, 1), keepdim=True)).pow(2).mean().clamp_min(1e-4)
            loss = loss + mu * (dh / var_h)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    X_ev, Y_ev, ST_ev = fast_sample_monoid(Dl, O, A["s0"], 400, T_MON, np.random.default_rng(int(A["seed"]) + 900_000 + arch_off))
    with torch.no_grad():
        logits_ev = mdl(X_ev)[:, BURN_MON:]
        fit = float(((logits_ev > 0).float() == Y_ev[:, BURN_MON:]).float().mean())
        H_ev = mdl.hidden(X_ev).numpy()

    flat_h = H_ev[:, BURN_MON:].reshape(-1, 64)
    flat_q = ST_ev[:, BURN_MON:].ravel()
    Ce = np.stack([
        flat_h[flat_q == q].mean(0) if (flat_q == q).any() else np.zeros(64)
        for q in range(m)
    ])
    W_pi = np.sqrt(pi)[:, None]
    Cc = Ce - (pi[:, None] * Ce).sum(0, keepdims=True)
    G_net = sym_perp((W_pi * Cc) @ (W_pi * Cc).T, Pperp)

    ev_def = FreeEnergyEvaluator(Wc, Wo, Lkin, Pperp, o_gram, eps_rel=EPS_DEFAULT)
    scored = ev_def.score_arm1a(G_net)
    res = {
        "arm": "arm1a",
        "name": name,
        "arch": arch,
        "fit": fit,
        "G_net": G_net.tolist(),
        **scored,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm1a_{name}_{arch}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def sample_hmm_batch(P_actions: np.ndarray, Olik: np.ndarray, pi: np.ndarray, B: int, T: int, rng: np.random.Generator):
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]
    P_mix = P_actions.mean(axis=0)
    emit_from_cur = P_mix @ Olik.T
    IN = np.zeros((B, T, L + n_obs), dtype=np.float32)
    TG = np.zeros((B, T), dtype=np.int64)
    MU = np.zeros((B, T, m), dtype=np.float32)
    BAYES = np.zeros((B, T, n_obs), dtype=np.float32)

    x = rng.choice(m, size=B, p=pi)
    bel = np.broadcast_to(pi, (B, m)).copy()
    prev_a = np.full(B, -1, dtype=np.int64)
    for t in range(T):
        probs_y = Olik[:, x].T
        y = np.argmax(np.cumsum(probs_y, axis=1) >= rng.random(B)[:, None], axis=1)
        bel = bel * Olik[y]
        bel = bel / np.maximum(bel.sum(axis=1, keepdims=True), 1e-15)
        MU[:, t, :] = bel.astype(np.float32)
        BAYES[:, t, :] = (bel @ emit_from_cur).astype(np.float32)
        if t > 0:
            IN[np.arange(B), t, prev_a] = 1.0
        IN[np.arange(B), t, L + y] = 1.0
        a = rng.integers(0, L, size=B)
        probs_x = P_actions[a, x]
        x_nxt = np.argmax(np.cumsum(probs_x, axis=1) >= rng.random(B)[:, None], axis=1)
        probs_yn = Olik[:, x_nxt].T
        y_nxt = np.argmax(np.cumsum(probs_yn, axis=1) >= rng.random(B)[:, None], axis=1)
        TG[:, t] = y_nxt
        bel = np.einsum("bm,bmn->bn", bel, P_actions[a])
        bel = bel / np.maximum(bel.sum(axis=1, keepdims=True), 1e-15)
        x = x_nxt
        prev_a = a
    return IN, TG, MU, BAYES


def run_arm1b_task(A: dict, arch: str, raw_dir: pathlib.Path, steps: int = 1500) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)

    name = A["name"]
    P_actions = np.array(A["P_actions"], dtype=float)
    Olik = np.array(A["Olik"], dtype=float)
    pi = np.array(A["pi"], dtype=float)
    Lkin = np.array(A["Lkin"], dtype=float)
    Pperp = np.array(A["Pperp"], dtype=float)
    Wc_obs = np.array(A["Wc_obs"], dtype=float)
    Wo_obs = np.array(A["Wo_obs"], dtype=float)
    L, m, _ = P_actions.shape
    n_obs = Olik.shape[0]

    arch_off = ARM1B_ARCHS.index(arch) * 1000
    seed = int(A["seed"]) + arch_off
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    class HMMGRU(nn.Module):
        def __init__(self):
            super().__init__()
            self.in_proj = nn.Linear(L + n_obs, 64)
            self.rnn = nn.GRU(64, 64, batch_first=True)
            self.head = nn.Sequential(nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, n_obs))
        def hidden(self, x):
            return self.rnn(self.in_proj(x))[0]
        def forward(self, x):
            return self.head(self.hidden(x))

    mdl = HMMGRU()
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    use_vel = (arch == "vel_warmup")
    t0 = time.time()

    for step in range(steps):
        IN, TG, _, _ = sample_hmm_batch(P_actions, Olik, pi, BATCH, T_HMM, rng)
        H = mdl.hidden(torch.from_numpy(IN))
        logits = mdl.head(H)[:, BURN_HMM:]
        tgt = torch.from_numpy(TG)[:, BURN_HMM:]
        loss = F.cross_entropy(logits.reshape(-1, n_obs), tgt.reshape(-1))
        if use_vel and step >= steps // 2:
            half = steps // 2
            mu = 0.05 if step >= half + half // 2 else 0.05 * ((step - half) / max(half // 2, 1))
            H_st = H[:, BURN_HMM:]
            dh = (H_st[:, 1:] - H_st[:, :-1]).pow(2).mean()
            var_h = (H_st - H_st.mean(dim=(0, 1), keepdim=True)).pow(2).mean().clamp_min(1e-4)
            loss = loss + mu * (dh / var_h)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()

    mdl.eval()
    IN_ev, _, MU_ev, BAYES_ev = sample_hmm_batch(
        P_actions, Olik, pi, 400, T_HMM, np.random.default_rng(int(A["seed"]) + 900_000 + arch_off)
    )
    with torch.no_grad():
        x_ev = torch.from_numpy(IN_ev)
        H_ev = mdl.hidden(x_ev).numpy()
        logits_ev = mdl(x_ev)[:, BURN_HMM:].numpy()

    p_bayes = np.clip(BAYES_ev[:, BURN_HMM:].reshape(-1, n_obs), 1e-12, 1.0)
    ex = np.exp(logits_ev - logits_ev.max(axis=-1, keepdims=True))
    p_mod = np.clip((ex / ex.sum(axis=-1, keepdims=True)).reshape(-1, n_obs), 1e-12, 1.0)
    kl_gap = float(np.mean(np.sum(p_bayes * (np.log(p_bayes) - np.log(p_mod)), axis=1)))

    H_tr = H_ev[:200, BURN_HMM:].reshape(-1, 64)
    H_te = H_ev[200:, BURN_HMM:].reshape(-1, 64)
    M_tr = MU_ev[:200, BURN_HMM:].reshape(-1, m)
    M_te = MU_ev[200:, BURN_HMM:].reshape(-1, m)
    coef, _, _, _ = np.linalg.lstsq(np.column_stack([H_tr, np.ones(len(H_tr))]), M_tr, rcond=1e-5)
    M_pred = np.column_stack([H_te, np.ones(len(H_te))]) @ coef
    belief_r2 = float(1.0 - np.sum((M_te - M_pred) ** 2) / max(float(np.sum((M_te - M_te.mean(0, keepdims=True)) ** 2)), 1e-12))

    H_all = np.concatenate([H_tr, H_te], axis=0)
    M_all = np.concatenate([M_tr, M_te], axis=0)
    V = np.linalg.solve(M_all.T @ M_all + 1e-6 * np.eye(m), M_all.T @ H_all)
    Dpi_h = np.diag(np.sqrt(pi))
    G_net_state = sym_perp(Dpi_h @ (V @ V.T) @ Dpi_h, Pperp)

    H_sub = H_te[:384] - H_te[:384].mean(axis=0, keepdims=True)
    K_net = sym_mat(H_sub @ H_sub.T)
    Dpi_inv_h = np.diag(1.0 / np.sqrt(pi))
    R_sub = (M_te[:384] - pi[None, :]) @ Dpi_inv_h

    ev_hmm = FreeEnergyEvaluator(Wc_obs, Wo_obs, Lkin, Pperp, Wo_obs, eps_rel=1e-5)
    kin_obs = dirichlet_kin_norm(G_net_state, Lkin)
    state_scores, hist_scores, lams = {}, {}, {}
    for fam in ("G_dual_heat", "X_kl_dual", "X_dual_var", "G_gm_heat", "X_kl_gm", "G_sum_heat"):
        lam = ev_hmm.invert_lambda(fam, kin_obs)
        G_pred = ev_hmm.eval_op(fam, lam)
        state_scores[fam] = cos_mat(G_net_state, G_pred)
        hist_scores[fam] = cos_mat(K_net, sym_mat(R_sub @ G_pred @ R_sub.T))
        lams[fam] = float(lam)
    for st_name, mat in ev_hmm.static.items():
        state_scores[st_name] = cos_mat(G_net_state, mat)
        hist_scores[st_name] = cos_mat(K_net, sym_mat(R_sub @ mat @ R_sub.T))

    res = {
        "arm": "arm1b",
        "name": name,
        "family": A["family"],
        "arch": arch,
        "kl_gap": kl_gap,
        "belief_r2": belief_r2,
        "kin_norm": kin_obs,
        "state_scores": state_scores,
        "hist_scores": hist_scores,
        "lams": lams,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm1b_{name}_{arch}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


# ---------------------------------------------------------------------------
# Arm 2A & Arm 2B: Complex Unitary Cayley U(d) & Non-Abelian Bouquet Models
# ---------------------------------------------------------------------------

def gauge_orbit_anova(feats: np.ndarray, hols: np.ndarray, classes: np.ndarray) -> dict:
    total_var = float(np.mean(np.sum((feats - feats.mean(axis=0, keepdims=True)) ** 2, axis=1)))
    if total_var < 1e-12:
        return {"within_orbit_ratio": 1.0, "base_frame_within_class_ratio": 0.0, "within_hol_ratio": 1.0}
    within_orbit = 0.0
    for c in np.unique(classes):
        fc = feats[classes == c]
        within_orbit += float(np.sum((fc - fc.mean(axis=0, keepdims=True)) ** 2))
    within_orbit /= len(feats)

    within_hol = 0.0
    for h in np.unique(hols):
        fh = feats[hols == h]
        within_hol += float(np.sum((fh - fh.mean(axis=0, keepdims=True)) ** 2))
    within_hol /= len(feats)

    base_frame_var = max(within_orbit - within_hol, 0.0)
    return {
        "within_orbit_ratio": float(within_orbit / total_var),
        "base_frame_within_class_ratio": float(base_frame_var / total_var),
        "within_hol_ratio": float(within_hol / total_var),
    }


def make_cayley_unitary_mats(P_re, P_im, eye_c):
    """Exact U(d) Cayley transform with fixed M(e) = I_d for every non-identity generator."""
    import torch
    H_gen = 0.5 * (P_re + P_re.transpose(-1, -2)) + 1j * 0.5 * (P_im - P_im.transpose(-1, -2))
    A_p = eye_c + 1j * H_gen
    A_m = eye_c - 1j * H_gen
    U_non = torch.linalg.solve(A_p, A_m)
    U_id = eye_c.unsqueeze(0)
    return torch.cat([U_id, U_non], dim=0)  # (G, n_heads, d, d)


def reorder_id_first(tab: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, int]:
    """Permute group element indices so element 0 is identity e."""
    G = tab["G"]
    id_old = tab["id"]
    perm = [id_old] + [i for i in range(G) if i != id_old]
    inv_perm = np.zeros(G, dtype=np.int64)
    for new_i, old_i in enumerate(perm):
        inv_perm[old_i] = new_i
    mul_new = np.zeros((G, G), dtype=np.int64)
    inv_new = np.zeros(G, dtype=np.int64)
    cls_new = np.zeros(G, dtype=np.int64)
    for a in range(G):
        inv_new[a] = inv_perm[tab["inv"][perm[a]]]
        cls_new[a] = tab["cls_of"][perm[a]]
        for b in range(G):
            mul_new[a, b] = inv_perm[tab["mul"][perm[a], perm[b]]]
    return mul_new, inv_new, cls_new, G


def make_arm2a_model(model_name: str, G_size: int, n_cls: int, inv_table: np.ndarray):
    import torch
    import torch.nn as nn

    if model_name == "multiset_deepsets":
        h2 = 55 if G_size == 8 else 53
        class MultisetDeepSets(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 64)
                self.phi = nn.Sequential(nn.Linear(64, 64), nn.Tanh())
                self.rho = nn.Sequential(nn.Linear(64, 92), nn.Tanh(), nn.Linear(92, h2), nn.Tanh())
                self.head = nn.Linear(h2, n_cls)
            def extract(self, X):
                z = self.phi(self.emb(X)).mean(dim=1)
                pen = self.rho(z)
                return z, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = MultisetDeepSets()

    elif model_name == "palindromic_gru":
        class PalindromicGRU(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 32)
                self.rnn = nn.GRU(32, 54, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(54, 24), nn.Tanh())
                self.head = nn.Linear(24, n_cls)
                self.register_buffer("inv_idx", torch.from_numpy(inv_table).long())
            def extract(self, X):
                X_rev = torch.flip(self.inv_idx[X], dims=[1])
                hf = self.rnn(self.emb(X))[0][:, -1, :]
                hb = self.rnn(self.emb(X_rev))[0][:, -1, :]
                raw = 0.5 * (hf + hb)
                pen = 0.5 * (self.trunk(hf) + self.trunk(hb))
                logits = 0.5 * (self.head(self.trunk(hf)) + self.head(self.trunk(hb)))
                return raw, pen, logits
            def forward(self, X):
                return self.extract(X)[2]
        m = PalindromicGRU()

    elif model_name == "ordered_gru":
        class OrderedGRU(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 32)
                self.rnn = nn.GRU(32, 54, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(54, 24), nn.Tanh())
                self.head = nn.Linear(24, n_cls)
            def extract(self, X):
                raw = self.rnn(self.emb(X))[0][:, -1, :]
                pen = self.trunk(raw)
                return raw, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = OrderedGRU()

    elif model_name == "cayley_unitary_equivariant":
        n_heads, d = 4, 6
        h2 = 106 if G_size == 8 else 96
        class CayleyUnitaryNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads = n_heads
                self.d = d
                scale = 0.35 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G_size - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G_size - 1, n_heads, d, d) * scale)
                self.trunk = nn.Sequential(nn.Linear(n_heads * 8, 96), nn.Tanh(), nn.Linear(96, h2), nn.Tanh())
                self.head = nn.Linear(h2, n_cls)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley_unitary_mats(self.P_re, self.P_im, self.eye_c)
            def extract(self, X):
                U_bank = self.unitary_bank()
                Us = U_bank[X]  # (B, L, H, d, d)
                P = Us[:, 0]
                for t in range(1, X.shape[1]):
                    P = torch.matmul(Us[:, t], P)
                feats = []
                Pk = P
                for k in range(4):
                    if k > 0:
                        Pk = torch.matmul(Pk, P)
                    tr = torch.diagonal(Pk, dim1=-2, dim2=-1).sum(-1) / self.d
                    feats.append(tr.real)
                    feats.append(tr.imag)
                inv_f = torch.cat(feats, dim=-1)  # (B, n_heads * 8)
                pen = self.trunk(inv_f)
                return inv_f, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = CayleyUnitaryNet()
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    assert 15200 <= n_params <= 16800, f"Arm2A {model_name} G={G_size} params={n_params}"
    return m, n_params


def run_arm2a_task(group_name: str, model_name: str, seed: int, raw_dir: pathlib.Path, steps: int = 2500) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)

    tab_raw = {"D4": make_d4_group(), "A4": make_a4_group()}[group_name].build_tables()
    mul, inv, cls_of, G = reorder_id_first(tab_raw)
    n_cls = tab_raw["n_cls"]

    def hol_and_cls(A: np.ndarray):
        h = A[:, 0]
        for t in range(1, A.shape[1]):
            h = mul[A[:, t], h]
        return h, cls_of[h]

    split_rng = np.random.default_rng(54000 + G)
    X3_tr = np.array(list(product(range(G), repeat=3)), dtype=np.int64)
    _, Y3_tr = hol_and_cls(X3_tr)

    all4 = (
        np.array(list(product(range(G), repeat=4)), dtype=np.int64)
        if G ** 4 <= 4096
        else split_rng.integers(0, G, size=(4096, 4), dtype=np.int64)
    )
    _, Y4_all = hol_and_cls(all4)
    tr4, va4 = [], []
    for c in range(n_cls):
        idxs = np.where(Y4_all == c)[0]
        split_rng.shuffle(idxs)
        k_tr = int(0.75 * len(idxs))
        tr4.extend(idxs[:k_tr])
        va4.extend(idxs[k_tr:])
    X4_tr, Y4_tr = all4[tr4], Y4_all[tr4]
    X4_va, Y4_va = all4[va4], Y4_all[va4]

    X5_ood = split_rng.integers(0, G, size=(1200, 5), dtype=np.int64)
    _, Y5_ood = hol_and_cls(X5_ood)
    X6_ood = split_rng.integers(0, G, size=(1200, 6), dtype=np.int64)
    _, Y6_ood = hol_and_cls(X6_ood)

    # Multiset collision pairs on L=4 held-out + L=4 full
    by_ms_va: dict[tuple[int, ...], dict[int, list]] = {}
    for row, y in zip(all4.tolist(), Y4_all.tolist()):
        by_ms_va.setdefault(tuple(sorted(row)), {}).setdefault(int(y), []).append(row)
    coll_x1, coll_y1, coll_x2, coll_y2 = [], [], [], []
    for by_c in by_ms_va.values():
        if len(by_c) >= 2:
            cs = sorted(by_c.keys())
            coll_x1.append(by_c[cs[0]][0]); coll_y1.append(cs[0])
            coll_x2.append(by_c[cs[1]][0]); coll_y2.append(cs[1])
            if len(coll_x1) >= 64:
                break

    # Chiral pairs for A_4: exact inverse pair (r, r^{-rev}) switching C_3^+ and C_3^-
    chiral_x1, chiral_y1, chiral_x2, chiral_y2 = [], [], [], []
    if group_name == "A4":
        c_plus, c_minus = a4_chiral_classes(tab_raw)
        for row, y in zip(X4_va.tolist(), Y4_va.tolist()):
            if y == c_plus:
                rev_row = [int(inv[x]) for x in reversed(row)]
                chiral_x1.append(row); chiral_y1.append(int(c_plus))
                chiral_x2.append(rev_row); chiral_y2.append(int(c_minus))
                if len(chiral_x1) >= 64:
                    break

    # Class-balanced sampling tables for L=3 and L=4 training
    by_cls_3 = [np.where(Y3_tr == c)[0] for c in range(n_cls)]
    by_cls_4 = [np.where(Y4_tr == c)[0] for c in range(n_cls)]

    mdl_seed = seed * 100 + ARM2A_MODELS.index(model_name) * 10 + G
    torch.manual_seed(mdl_seed)
    rng = np.random.default_rng(mdl_seed)
    mdl, n_params = make_arm2a_model(model_name, G, n_cls, inv)
    opt = torch.optim.AdamW(mdl.parameters(), lr=2.5e-3, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=2e-4)
    t0 = time.time()

    per_cls = max(128 // n_cls, 16)
    for step in range(steps):
        use4 = (step % 2 == 1)
        Xsrc, Ysrc, bins = (X4_tr, Y4_tr, by_cls_4) if use4 else (X3_tr, Y3_tr, by_cls_3)
        pick = np.concatenate([rng.choice(b, size=per_cls, replace=True) for b in bins])
        rng.shuffle(pick)
        xb = torch.from_numpy(Xsrc[pick]).long()
        yb = torch.from_numpy(Ysrc[pick]).long()
        logits = mdl(xb)
        loss = F.cross_entropy(logits, yb)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    unitary_err = None
    with torch.no_grad():
        if hasattr(mdl, "unitary_bank"):
            U_b = mdl.unitary_bank()
            eye = mdl.eye_c.unsqueeze(0)
            uu = torch.matmul(U_b, U_b.conj().transpose(-1, -2))
            unitary_err = float(torch.max(torch.abs(uu - eye)).item())

        p4_va = mdl(torch.from_numpy(X4_va).long()).argmax(dim=-1).numpy()
        p5_ood = mdl(torch.from_numpy(X5_ood).long()).argmax(dim=-1).numpy()
        p6_ood = mdl(torch.from_numpy(X6_ood).long()).argmax(dim=-1).numpy()

        raw3, pen3, p3_logits = mdl.extract(torch.from_numpy(X3_tr).long())
        raw3_np, pen3_np = raw3.numpy(), pen3.numpy()
        p3_tr = p3_logits.argmax(dim=-1).numpy()
        H3, Y3 = hol_and_cls(X3_tr)

        coll_sep = 0.0
        if coll_x1:
            pc1 = mdl(torch.from_numpy(np.array(coll_x1)).long()).argmax(dim=-1).numpy()
            pc2 = mdl(torch.from_numpy(np.array(coll_x2)).long()).argmax(dim=-1).numpy()
            coll_sep = float(np.mean((pc1 == np.array(coll_y1)) & (pc2 == np.array(coll_y2))))

        chiral_sep = None
        if chiral_x1:
            pa1 = mdl(torch.from_numpy(np.array(chiral_x1)).long()).argmax(dim=-1).numpy()
            pa2 = mdl(torch.from_numpy(np.array(chiral_x2)).long()).argmax(dim=-1).numpy()
            chiral_sep = float(np.mean((pa1 == np.array(chiral_y1)) & (pa2 == np.array(chiral_y2))))

    res = {
        "arm": "arm2a",
        "group": group_name,
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "train_L3_bacc": balanced_acc(p3_tr, Y3, n_cls),
        "held_L4_acc": float((p4_va == Y4_va).mean()),
        "held_L4_bacc": balanced_acc(p4_va, Y4_va, n_cls),
        "ood_L5_acc": float((p5_ood == Y5_ood).mean()),
        "ood_L5_bacc": balanced_acc(p5_ood, Y5_ood, n_cls),
        "ood_L6_acc": float((p6_ood == Y6_ood).mean()),
        "ood_L6_bacc": balanced_acc(p6_ood, Y6_ood, n_cls),
        "collision_pair_sep": coll_sep,
        "chiral_pair_sep": chiral_sep,
        "anova_raw": gauge_orbit_anova(raw3_np, H3, Y3),
        "anova_pen": gauge_orbit_anova(pen3_np, H3, Y3),
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm2a_{group_name}_{model_name}_s{seed}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def make_arm2b_model(model_name: str, G_size: int, n_orbits: int, mul_table: np.ndarray, inv_table: np.ndarray):
    import torch
    import torch.nn as nn

    if model_name == "multiset_deepsets":
        class MultisetDeepSets(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 64)
                self.phi = nn.Sequential(nn.Linear(64, 64), nn.Tanh())
                self.rho = nn.Sequential(nn.Linear(64, 92), nn.Tanh(), nn.Linear(92, 53), nn.Tanh())
                self.head = nn.Linear(53, n_orbits)
            def extract(self, X):
                z = self.phi(self.emb(X)).mean(dim=1)
                pen = self.rho(z)
                return z, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = MultisetDeepSets()

    elif model_name == "per_loop_gauge_pooled_gru":
        # Independent basepoint conjugations k_r in S_3 on loop 1 and loop 2 -> purely G//G x G//G!
        conj_tbl = np.zeros((G_size, G_size), dtype=np.int64)
        for k in range(G_size):
            for x in range(G_size):
                conj_tbl[k, x] = mul_table[mul_table[k, x], inv_table[k]]

        class PerLoopGaugePooledGRU(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 32)
                self.rnn = nn.GRU(32, 48, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(96, 36), nn.Tanh())
                self.head = nn.Linear(36, n_orbits)
                self.register_buffer("conj_tbl", torch.from_numpy(conj_tbl).long())
            def extract(self, X):
                B, tot = X.shape
                Lloop = tot // 2
                X1, X2 = X[:, :Lloop], X[:, Lloop:]
                # (B, G, Lloop) -> batched forward in single GRU call
                C1 = self.conj_tbl[:, X1].permute(1, 0, 2).reshape(B * G_size, Lloop)
                C2 = self.conj_tbl[:, X2].permute(1, 0, 2).reshape(B * G_size, Lloop)
                h1 = self.rnn(self.emb(C1))[0][:, -1, :].reshape(B, G_size, 48).mean(dim=1)
                h2 = self.rnn(self.emb(C2))[0][:, -1, :].reshape(B, G_size, 48).mean(dim=1)
                cat = torch.cat([h1, h2], dim=-1)
                pen = self.trunk(cat)
                return cat, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = PerLoopGaugePooledGRU()

    elif model_name == "joint_bouquet_gru":
        class JointBouquetGRU(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 32)
                self.loop_emb = nn.Embedding(2, 32)
                self.rnn = nn.GRU(32, 54, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(54, 22), nn.Tanh())
                self.head = nn.Linear(22, n_orbits)
            def extract_full(self, X):
                B, tot = X.shape
                Lloop = tot // 2
                lidx = torch.cat([
                    torch.zeros(Lloop, dtype=torch.long, device=X.device),
                    torch.ones(Lloop, dtype=torch.long, device=X.device),
                ]).unsqueeze(0).expand(B, tot)
                inp = self.emb(X) + self.loop_emb(lidx)
                seq = self.rnn(inp)[0]
                h_mid = seq[:, Lloop - 1, :]
                h_last = seq[:, -1, :]
                pen = self.trunk(h_last)
                return h_mid, h_last, pen, self.head(pen)
            def forward(self, X):
                return self.extract_full(X)[3]
        m = JointBouquetGRU()

    elif model_name == "cayley_unitary_bouquet":
        n_heads, d = 4, 6
        class CayleyUnitaryBouquet(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads = n_heads
                self.d = d
                scale = 0.35 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G_size - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G_size - 1, n_heads, d, d) * scale)
                # 10 words x 2 (real, imag) x 4 heads = 80 invariants
                self.trunk = nn.Sequential(nn.Linear(80, 96), nn.Tanh(), nn.Linear(96, 62), nn.Tanh())
                self.head = nn.Linear(62, n_orbits)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley_unitary_mats(self.P_re, self.P_im, self.eye_c)
            def _prod(self, U_bank, X_sub):
                Us = U_bank[X_sub]
                P = Us[:, 0]
                for t in range(1, X_sub.shape[1]):
                    P = torch.matmul(Us[:, t], P)
                return P
            def extract(self, X):
                Lloop = X.shape[1] // 2
                U_bank = self.unitary_bank()
                H1 = self._prod(U_bank, X[:, :Lloop])
                H2 = self._prod(U_bank, X[:, Lloop:])
                H1d = H1.conj().transpose(-1, -2)
                H2d = H2.conj().transpose(-1, -2)
                H1_2 = torch.matmul(H1, H1)
                H2_2 = torch.matmul(H2, H2)
                words = [
                    H1, H2, H1_2, H2_2,
                    torch.matmul(H1, H2), torch.matmul(H1, H2d),
                    torch.matmul(H1_2, H2), torch.matmul(H1, H2_2),
                    torch.matmul(torch.matmul(H1, H2), torch.matmul(H1d, H2d)),
                    torch.matmul(torch.matmul(H1, H2), torch.matmul(H1, H2)),
                ]
                feats = []
                for W in words:
                    tr = torch.diagonal(W, dim1=-2, dim2=-1).sum(-1) / self.d
                    feats.append(tr.real)
                    feats.append(tr.imag)
                inv_f = torch.cat(feats, dim=-1)
                pen = self.trunk(inv_f)
                return inv_f, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = CayleyUnitaryBouquet()
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    assert 15200 <= n_params <= 16800, f"Arm2B {model_name} params={n_params}"
    return m, n_params


def run_arm2b_task(model_name: str, seed: int, raw_dir: pathlib.Path, steps: int = 2500) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)

    bq = s3_bouquet_tables()
    G, mul, inv, cls_of, orb_of = bq["G"], bq["mul"], bq["inv"], bq["cls_of"], bq["orb_of"]
    id_idx = bq["id"]
    n_orbits = bq["n_orbits"]

    def bouquet_hols_and_orb(X: np.ndarray):
        Lloop = X.shape[1] // 2
        h1 = X[:, 0]
        for t in range(1, Lloop):
            h1 = mul[X[:, t], h1]
        h2 = X[:, Lloop]
        for t in range(Lloop + 1, X.shape[1]):
            h2 = mul[X[:, t], h2]
        return h1, h2, orb_of[h1, h2], cls_of[h1]

    split_rng = np.random.default_rng(55000)
    # Stratified 75/25 disjoint split of L=3 per loop across all 11 simultaneous orbits
    all6 = np.array(list(product(range(G), repeat=6)), dtype=np.int64)
    H1_6, H2_6, Y6, C1_6 = bouquet_hols_and_orb(all6)
    tr_idx, va_idx = [], []
    for o in range(n_orbits):
        idxs = np.where(Y6 == o)[0]
        split_rng.shuffle(idxs)
        k_tr = int(0.75 * len(idxs))
        tr_idx.extend(idxs[:k_tr])
        va_idx.extend(idxs[k_tr:])
    X_tr, Y_tr = all6[tr_idx], Y6[tr_idx]
    X_va, Y_va = all6[va_idx], Y6[va_idx]
    H1_va, H2_va, C1_va = H1_6[va_idx], H2_6[va_idx], C1_6[va_idx]

    X_ood = split_rng.integers(0, G, size=(1500, 8), dtype=np.int64)
    _, _, Y_ood, _ = bouquet_hols_and_orb(X_ood)

    # Exact canonical split pairs across basepoint conjugations
    s01 = [i for i, e in enumerate(make_s3_group().elements) if e == (1, 0, 2)][0]
    s12 = [i for i, e in enumerate(make_s3_group().elements) if e == (0, 2, 1)][0]
    c3 = [i for i, e in enumerate(make_s3_group().elements) if e == (1, 2, 0)][0]
    c3i = int(inv[c3])

    def conj_pair_batch(a1: int, a2: int, b1: int, k0_rot: int, Lloop: int = 3):
        """Construct genuine gauge-varied split pairs where loop 2 of x2 is an exact
        per-loop uniform conjugation of loop 2 of x1 (so any purely per-loop
        conjugation-invariant representation maps x1 and x2 identically)."""
        x1s, x2s = [], []
        rng_p = np.random.default_rng(55100)
        for _ in range(48):
            k = int(rng_p.integers(0, G))
            g_int1 = rng_p.integers(0, G, size=Lloop - 1)
            g_int2 = rng_p.integers(0, G, size=Lloop - 1)
            def build_loop(h_val, gi):
                e0 = int(mul[int(gi[0]), int(mul[id_idx, int(inv[k])])])
                e1 = int(mul[int(gi[1]), int(mul[id_idx, int(inv[int(gi[0])])])])
                e2 = int(mul[k, int(mul[h_val, int(inv[int(gi[1])])])])
                return [e0, e1, e2]
            l1 = build_loop(a1, g_int1)
            l2_a = build_loop(a2, g_int2)
            # Conjugate every edge of loop 2 by k_rel = k * k0_rot * k^{-1}:
            # changes H_2 = k a2 k^{-1} -> k (k0_rot a2 k0_rot^{-1}) k^{-1} = k b2 k^{-1}!
            k_rel = int(mul[int(mul[k, k0_rot]), int(inv[k])])
            l2_b = [int(mul[int(mul[k_rel, e]), int(inv[k_rel])]) for e in l2_a]
            x1s.append(l1 + l2_a)
            x2s.append(l1 + l2_b)
        return np.array(x1s, dtype=np.int64), np.array(x2s, dtype=np.int64)

    # s01 -> c3 * s01 * c3^{-1} = s12; c3 -> s12 * c3 * s12^{-1} = c3^{-1}
    tau_x1, tau_x2 = conj_pair_batch(s01, s01, s01, c3)
    _, _, tau_y1, _ = bouquet_hols_and_orb(tau_x1)
    _, _, tau_y2, _ = bouquet_hols_and_orb(tau_x2)
    cyc_x1, cyc_x2 = conj_pair_batch(c3, c3, c3, s12)
    _, _, cyc_y1, _ = bouquet_hols_and_orb(cyc_x1)
    _, _, cyc_y2, _ = bouquet_hols_and_orb(cyc_x2)

    by_orb = [np.where(Y_tr == o)[0] for o in range(n_orbits)]
    mdl_seed = seed * 100 + ARM2B_MODELS.index(model_name) * 10 + 99
    torch.manual_seed(mdl_seed)
    rng = np.random.default_rng(mdl_seed)

    mdl, n_params = make_arm2b_model(model_name, G, n_orbits, mul, inv)
    opt = torch.optim.AdamW(mdl.parameters(), lr=2.5e-3, weight_decay=0.0)
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=2e-4)
    t0 = time.time()

    per_orb = max(132 // n_orbits, 12)
    for step in range(steps):
        pick = np.concatenate([rng.choice(b, size=per_orb, replace=True) for b in by_orb])
        rng.shuffle(pick)
        xb = torch.from_numpy(X_tr[pick]).long()
        yb = torch.from_numpy(Y_tr[pick]).long()
        logits = mdl(xb)
        loss = F.cross_entropy(logits, yb)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    unitary_err = None
    with torch.no_grad():
        if hasattr(mdl, "unitary_bank"):
            U_b = mdl.unitary_bank()
            eye = mdl.eye_c.unsqueeze(0)
            uu = torch.matmul(U_b, U_b.conj().transpose(-1, -2))
            unitary_err = float(torch.max(torch.abs(uu - eye)).item())

        p_va = mdl(torch.from_numpy(X_va).long()).argmax(dim=-1).numpy()
        p_ood = mdl(torch.from_numpy(X_ood).long()).argmax(dim=-1).numpy()
        pt1 = mdl(torch.from_numpy(tau_x1).long()).argmax(dim=-1).numpy()
        pt2 = mdl(torch.from_numpy(tau_x2).long()).argmax(dim=-1).numpy()
        tau_sep = float(np.mean((pt1 == tau_y1) & (pt2 == tau_y2)))
        pc1 = mdl(torch.from_numpy(cyc_x1).long()).argmax(dim=-1).numpy()
        pc2 = mdl(torch.from_numpy(cyc_x2).long()).argmax(dim=-1).numpy()
        cyc_sep = float(np.mean((pc1 == cyc_y1) & (pc2 == cyc_y2)))

        # Held-out orbit collapse diagnostics (plus deferred loop-1 variance for joint_bouquet_gru!)
        sub_n = min(len(X_va), 3000)
        X_sub = torch.from_numpy(X_va[:sub_n]).long()
        joint_pair_id = H1_va[:sub_n] * G + H2_va[:sub_n]
        anova_mid_cls1 = None
        if model_name == "joint_bouquet_gru":
            h_mid, h_last, pen, _ = mdl.extract_full(X_sub)
            anova_mid_cls1 = gauge_orbit_anova(h_mid.numpy(), H1_va[:sub_n], C1_va[:sub_n])
            anova_raw = gauge_orbit_anova(h_last.numpy(), joint_pair_id, Y_va[:sub_n])
            anova_pen = gauge_orbit_anova(pen.numpy(), joint_pair_id, Y_va[:sub_n])
        else:
            raw, pen, _ = mdl.extract(X_sub)
            anova_raw = gauge_orbit_anova(raw.numpy(), joint_pair_id, Y_va[:sub_n])
            anova_pen = gauge_orbit_anova(pen.numpy(), joint_pair_id, Y_va[:sub_n])

    res = {
        "arm": "arm2b",
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "held_acc": float((p_va == Y_va).mean()),
        "held_bacc": balanced_acc(p_va, Y_va, n_orbits),
        "ood_L4_acc": float((p_ood == Y_ood).mean()),
        "ood_L4_bacc": balanced_acc(p_ood, Y_ood, n_orbits),
        "tau_split_sep": tau_sep,
        "cyc_split_sep": cyc_sep,
        "anova_mid_cls1": anova_mid_cls1,
        "anova_raw": anova_raw,
        "anova_pen": anova_pen,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm2b_{model_name}_s{seed}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def _dispatch(task: tuple):
    kind = task[0]
    if kind == "arm1a":
        return run_arm1a_task(*task[1:])
    if kind == "arm1b":
        return run_arm1b_task(*task[1:])
    if kind == "arm2a":
        return run_arm2a_task(*task[1:])
    if kind == "arm2b":
        return run_arm2b_task(*task[1:])
    raise ValueError(kind)


# ---------------------------------------------------------------------------
# Summary Aggregation & Verdict Evaluation
# ---------------------------------------------------------------------------

def evaluate_summary(pred: dict, arm1a: list[dict], arm1b: list[dict], arm2a: list[dict], arm2b: list[dict], total_s: float) -> dict:
    # Arm 1A aggregation + Leave-One-Monoid-Out CV lambda evaluation
    a1a_summary = {}
    for arch in ARM1A_ARCHS:
        rows = [r for r in arm1a if r["arch"] == arch]
        fams = ("G_gm_heat", "X_kl_gm", "G_sum_heat", "X_kl_sum", "X_primal_var",
                "G_gm_heat_best", "X_kl_gm_best", "G_sum_heat_best", "X_kl_sum_best", "X_primal_var_best",
                "W_gm", "W_sum", "W_bal", "W_bal_dual")
        agg = {
            "n": len(rows),
            "n_fit_90": sum(1 for r in rows if r["fit"] >= 0.90),
            "mean_fit": float(np.mean([r["fit"] for r in rows])),
            "mean_kin_norm": float(np.mean([r["kin_norm"] for r in rows])),
        }
        for fm in fams:
            vals = [r["scores"][fm] for r in rows]
            agg[f"{fm}_mean"] = float(np.mean(vals))
            agg[f"{fm}_med"] = float(np.median(vals))
        # Leave-one-monoid-out CV over LAM_GRID
        if len(rows) >= 2:
            for fm in ("G_gm_heat", "X_kl_gm", "G_sum_heat", "X_kl_sum", "X_primal_var"):
                cv_vals = []
                mat_c = np.array([r["curves"][fm] for r in rows])  # (N, 41)
                for i in range(len(rows)):
                    mask = np.ones(len(rows), dtype=bool)
                    mask[i] = False
                    best_lg = int(np.argmax(mat_c[mask].mean(axis=0)))
                    cv_vals.append(float(mat_c[i, best_lg]))
                agg[f"{fm}_loocv_mean"] = float(np.mean(cv_vals))
                agg[f"{fm}_loocv_med"] = float(np.median(cv_vals))
        a1a_summary[arch] = agg

    # Paired trajectory checks (HFE.3)
    by1a = {(r["name"], r["arch"]): r for r in arm1a}
    paired_shifts = {}
    for target in ("leaky_a025", "vel_warmup"):
        kin_drop, gm_up, kl_up = 0, 0, 0
        dks, l_gm_base, l_gm_tgt, l_kl_base, l_kl_tgt = [], [], [], [], []
        for mon in pred["monoids"]:
            nm = mon["name"]
            rb, rt = by1a[(nm, "rnn_mlp")], by1a[(nm, target)]
            dks.append(rt["kin_norm"] - rb["kin_norm"])
            if rt["kin_norm"] < rb["kin_norm"]:
                kin_drop += 1
            lg_b, lg_t = rb["lams"]["G_gm_heat"], rt["lams"]["G_gm_heat"]
            lk_b, lk_t = rb["lams"]["X_kl_gm"], rt["lams"]["X_kl_gm"]
            l_gm_base.append(lg_b); l_gm_tgt.append(lg_t)
            l_kl_base.append(lk_b); l_kl_tgt.append(lk_t)
            if lg_t > lg_b:
                gm_up += 1
            if lk_t > lk_b:
                kl_up += 1
        paired_shifts[f"rnn_to_{target}"] = {
            "kin_drop_count": kin_drop,
            "mean_dkin": float(np.mean(dks)),
            "lam_gm_heat_up": gm_up,
            "lam_kl_gm_up": kl_up,
            "med_lam_gm_base": float(np.median(l_gm_base)),
            "med_lam_gm_tgt": float(np.median(l_gm_tgt)),
            "med_lam_kl_base": float(np.median(l_kl_base)),
            "med_lam_kl_tgt": float(np.median(l_kl_tgt)),
        }

    # Arm 1B aggregation
    a1b_summary = {}
    for arch in ARM1B_ARCHS:
        rows = [r for r in arm1b if r["arch"] == arch]
        fams = ("G_dual_heat", "X_kl_dual", "X_dual_var", "W_bal_dual", "G_gm_heat", "X_kl_gm", "G_sum_heat")
        by_fam = {}
        for fam_k in ("cyclic_group_hmm", "nonrev_hmm", "all"):
            sub = rows if fam_k == "all" else [r for r in rows if r["family"] == fam_k]
            by_fam[fam_k] = {
                "n": len(sub),
                "mean_kl": float(np.mean([r["kl_gap"] for r in sub])),
                "mean_r2": float(np.mean([r["belief_r2"] for r in sub])),
                "state": {fm: float(np.mean([r["state_scores"][fm] for r in sub])) for fm in fams},
                "hist": {fm: float(np.mean([r["hist_scores"][fm] for r in sub])) for fm in fams},
            }
        a1b_summary[arch] = by_fam

    # Count HMM runs where dual exponential (G_dual_heat or X_kl_dual) beats static W_bal_dual AND primal G_gm_heat
    dual_exp_both_wins = 0
    for r in arm1b:
        s_best_dual = max(r["state_scores"]["G_dual_heat"], r["state_scores"]["X_kl_dual"])
        h_best_dual = max(r["hist_scores"]["G_dual_heat"], r["hist_scores"]["X_kl_dual"])
        if (s_best_dual > max(r["state_scores"]["W_bal_dual"], r["state_scores"]["G_gm_heat"]) and
                h_best_dual > max(r["hist_scores"]["W_bal_dual"], r["hist_scores"]["G_gm_heat"])):
            dual_exp_both_wins += 1

    # Arm 2A aggregation
    a2a_summary = {}
    for grp in ("D4", "A4"):
        a2a_summary[grp] = {}
        for mdl in ARM2A_MODELS:
            sub = [r for r in arm2a if r["group"] == grp and r["model"] == mdl]
            a2a_summary[grp][mdl] = {
                "n": len(sub),
                "params": sub[0]["n_params"] if sub else None,
                "held_L4_acc_mean": float(np.mean([r["held_L4_acc"] for r in sub])),
                "held_L4_bacc_mean": float(np.mean([r["held_L4_bacc"] for r in sub])),
                "ood_L5_bacc_mean": float(np.mean([r["ood_L5_bacc"] for r in sub])),
                "ood_L6_bacc_mean": float(np.mean([r["ood_L6_bacc"] for r in sub])),
                "coll_sep_mean": float(np.mean([r["collision_pair_sep"] for r in sub])),
                "chiral_sep_mean": (float(np.mean([r["chiral_pair_sep"] for r in sub]))
                                    if sub and sub[0]["chiral_pair_sep"] is not None else None),
                "raw_within_orbit": float(np.mean([r["anova_raw"]["within_orbit_ratio"] for r in sub])),
                "pen_within_orbit": float(np.mean([r["anova_pen"]["within_orbit_ratio"] for r in sub])),
                "max_unitary_err": (max(r["unitary_max_err"] for r in sub)
                                    if sub and sub[0]["unitary_max_err"] is not None else None),
            }

    # Arm 2B aggregation
    a2b_summary = {}
    for mdl in ARM2B_MODELS:
        sub = [r for r in arm2b if r["model"] == mdl]
        a2b_summary[mdl] = {
            "n": len(sub),
            "params": sub[0]["n_params"] if sub else None,
            "held_acc_mean": float(np.mean([r["held_acc"] for r in sub])),
            "held_bacc_mean": float(np.mean([r["held_bacc"] for r in sub])),
            "ood_L4_bacc_mean": float(np.mean([r["ood_L4_bacc"] for r in sub])),
            "tau_split_sep_mean": float(np.mean([r["tau_split_sep"] for r in sub])),
            "cyc_split_sep_mean": float(np.mean([r["cyc_split_sep"] for r in sub])),
            "mid_cls1_within_orbit": (float(np.mean([r["anova_mid_cls1"]["within_orbit_ratio"] for r in sub]))
                                      if sub and sub[0]["anova_mid_cls1"] is not None else None),
            "raw_within_orbit": float(np.mean([r["anova_raw"]["within_orbit_ratio"] for r in sub])),
            "pen_within_orbit": float(np.mean([r["anova_pen"]["within_orbit_ratio"] for r in sub])),
            "max_unitary_err": (max(r["unitary_max_err"] for r in sub)
                                if sub and sub[0]["unitary_max_err"] is not None else None),
        }

    # Exact Verdicts HFE.1..HFE.6
    kl_wins_archs = sum(
        1 for arch in ARM1A_ARCHS
        if a1a_summary[arch]["X_kl_gm_mean"] >= a1a_summary[arch]["G_gm_heat_mean"] - 0.005
    )
    gm_beats_kl_archs = sum(
        1 for arch in ARM1A_ARCHS
        if a1a_summary[arch]["G_gm_heat_mean"] > a1a_summary[arch]["X_kl_gm_mean"] + 0.005
    )
    hfe1 = "HELD" if kl_wins_archs >= 3 else ("BROKEN" if gm_beats_kl_archs >= 3 else "NEITHER")

    hfe2 = "HELD" if dual_exp_both_wins >= 10 else ("BROKEN" if dual_exp_both_wins <= 2 else "NEITHER")

    l_sh = paired_shifts["rnn_to_leaky_a025"]
    v_sh = paired_shifts["rnn_to_vel_warmup"]
    hfe3 = (
        "HELD"
        if (l_sh["kin_drop_count"] >= 9 and v_sh["kin_drop_count"] >= 9 and
            l_sh["lam_gm_heat_up"] >= 9 and v_sh["lam_gm_heat_up"] >= 9 and
            l_sh["lam_kl_gm_up"] >= 9 and v_sh["lam_kl_gm_up"] >= 9)
        else ("BROKEN" if (l_sh["lam_gm_heat_up"] < 6 and v_sh["lam_gm_heat_up"] < 6) else "NEITHER")
    )

    pal_a4 = a2a_summary["A4"]["palindromic_gru"]
    cu_a4 = a2a_summary["A4"]["cayley_unitary_equivariant"]
    gru_a4 = a2a_summary["A4"]["ordered_gru"]
    cu_d4 = a2a_summary["D4"]["cayley_unitary_equivariant"]
    gru_d4 = a2a_summary["D4"]["ordered_gru"]
    if pal_a4["chiral_sep_mean"] is not None and pal_a4["chiral_sep_mean"] >= 0.05:
        hfe4 = "BROKEN"
    elif (max(cu_d4["held_L4_bacc_mean"], gru_d4["held_L4_bacc_mean"]) >= 0.85 and
          cu_a4["held_L4_bacc_mean"] >= 0.85 and cu_a4["chiral_sep_mean"] >= 0.70 and
          cu_a4["ood_L5_bacc_mean"] >= 0.70 and cu_a4["ood_L6_bacc_mean"] >= 0.70):
        hfe4 = "HELD"
    elif (pal_a4["chiral_sep_mean"] < 0.02 and
          max(cu_a4["chiral_sep_mean"], gru_a4["chiral_sep_mean"]) >= 0.60):
        hfe4 = "NEITHER"
    else:
        hfe4 = "BROKEN"

    plp = a2b_summary["per_loop_gauge_pooled_gru"]
    jbg = a2b_summary["joint_bouquet_gru"]
    cub = a2b_summary["cayley_unitary_bouquet"]
    split_broken_by_pool = (plp["tau_split_sep_mean"] > 0.02 or plp["cyc_split_sep_mean"] > 0.02)
    best_joint_tau = max(jbg["tau_split_sep_mean"], cub["tau_split_sep_mean"])
    best_joint_cyc = max(jbg["cyc_split_sep_mean"], cub["cyc_split_sep_mean"])
    best_joint_bacc = max(jbg["held_bacc_mean"], cub["held_bacc_mean"])
    deferred_drop = (jbg["mid_cls1_within_orbit"] - jbg["pen_within_orbit"]) if jbg["mid_cls1_within_orbit"] is not None else 0.0
    if split_broken_by_pool or max(best_joint_tau, best_joint_cyc) < 0.50:
        hfe5 = "BROKEN"
    elif best_joint_tau >= 0.70 and best_joint_cyc >= 0.70 and best_joint_bacc >= 0.85 and deferred_drop >= 0.15:
        hfe5 = "HELD"
    else:
        hfe5 = "NEITHER"

    mon_laws_ok = all(
        m["gm_raw_mono"] and m["gm_norm_mono"] and m["gm_log_convex"] and
        m["kl_raw_mono"] and m["kl_trace_convex"] and
        m["gt_min_gap"] >= -1e-10 and m["gt_gap_lam1"] > 1e-6 and m["max_riccati_rel_err"] < 1e-8
        for m in pred["monoids"]
    )
    unitary_errs = [v for d in (a2a_summary["D4"].values(), a2a_summary["A4"].values(), a2b_summary.values())
                    for item in d for v in [item.get("max_unitary_err")] if v is not None]
    hfe6 = "HELD" if (mon_laws_ok and all(e < 1e-5 for e in unitary_errs)) else "BROKEN"

    return {
        "verdicts": {
            "HFE.1": hfe1,
            "HFE.2": hfe2,
            "HFE.3": hfe3,
            "HFE.4": hfe4,
            "HFE.5": hfe5,
            "HFE.6": hfe6,
        },
        "total_runs": len(arm1a) + len(arm1b) + len(arm2a) + len(arm2b),
        "total_elapsed_s": float(total_s),
        "arm1a": a1a_summary,
        "paired_shifts": paired_shifts,
        "arm1b": a1b_summary,
        "arm1b_dual_exp_both_wins": dual_exp_both_wins,
        "arm2a": a2a_summary,
        "arm2a_ceilings": pred["arm2a_ceilings"],
        "arm2b": a2b_summary,
        "bouquet_ceiling": pred["bouquet_ceiling"],
        "monoid_law_audit": {
            "n_monoids_all_passed": sum(
                1 for m in pred["monoids"]
                if m["gm_raw_mono"] and m["gm_norm_mono"] and m["gm_log_convex"] and
                m["kl_raw_mono"] and m["kl_trace_convex"] and m["gt_min_gap"] >= -1e-10
            ),
            "gt_min_gap_overall": float(min(m["gt_min_gap"] for m in pred["monoids"])),
            "gt_gap_lam1_min": float(min(m["gt_gap_lam1"] for m in pred["monoids"])),
            "max_riccati_rel_err": float(max(m["max_riccati_rel_err"] for m in pred["monoids"])),
            "max_unitary_err": float(max(unitary_errs)) if unitary_errs else 0.0,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--raw-dir", type=str, default=None)
    args = parser.parse_args()

    t0 = time.time()
    pred = generate_predictions(force=False)

    if args.raw_dir:
        raw_dir = pathlib.Path(args.raw_dir)
    else:
        ts = time.strftime("%Y%m%d_%H%M%S")
        raw_dir = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "semplex_trash_oleans" / f"mp_free_energy_raw_{ts}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        print("=== SMOKE TEST ===")
        s_a1a = run_arm1a_task(pred["monoids"][0], "gru_mlp", raw_dir, steps=150)
        s_a1b = run_arm1b_task(pred["hmms"][0], "gru_mlp", raw_dir, steps=150)
        s_a2a_pal = run_arm2a_task("A4", "palindromic_gru", 1, raw_dir, steps=200)
        s_a2a_cu = run_arm2a_task("A4", "cayley_unitary_equivariant", 1, raw_dir, steps=200)
        s_a2b_pl = run_arm2b_task("per_loop_gauge_pooled_gru", 1, raw_dir, steps=200)
        s_a2b_cu = run_arm2b_task("cayley_unitary_bouquet", 1, raw_dir, steps=800)
        s_a2b_jg = run_arm2b_task("joint_bouquet_gru", 1, raw_dir, steps=800)
        print(json.dumps({
            "arm1a_fit": s_a1a["fit"],
            "arm1a_G_gm_heat": s_a1a["scores"]["G_gm_heat"],
            "arm1a_X_kl_gm": s_a1a["scores"]["X_kl_gm"],
            "arm1b_r2": s_a1b["belief_r2"],
            "a4_pal_chiral_sep": s_a2a_pal["chiral_pair_sep"],
            "a4_cu_chiral_sep": s_a2a_cu["chiral_pair_sep"],
            "a4_cu_unitary_err": s_a2a_cu["unitary_max_err"],
            "bouquet_pool_tau_cyc": (s_a2b_pl["tau_split_sep"], s_a2b_pl["cyc_split_sep"]),
            "bouquet_cu_bacc_tau_cyc": (s_a2b_cu["held_bacc"], s_a2b_cu["tau_split_sep"], s_a2b_cu["cyc_split_sep"]),
            "bouquet_jg_bacc_tau_cyc": (s_a2b_jg["held_bacc"], s_a2b_jg["tau_split_sep"], s_a2b_jg["cyc_split_sep"]),
            "bouquet_cu_elapsed_s": s_a2b_cu["elapsed_s"],
            "bouquet_jg_elapsed_s": s_a2b_jg["elapsed_s"],
            "bouquet_cu_unitary_err": s_a2b_cu["unitary_max_err"],
            "smoke_elapsed_s": round(time.time() - t0, 2),
        }, indent=2))
        assert s_a2a_pal["chiral_pair_sep"] == 0.0, "Palindromic GRU leaked chirality!"
        assert s_a2b_pl["tau_split_sep"] == 0.0 and s_a2b_pl["cyc_split_sep"] == 0.0, "Per-loop pooled GRU leaked joint split!"
        assert s_a2a_cu["unitary_max_err"] < 1e-5 and s_a2b_cu["unitary_max_err"] < 1e-5
        return

    tasks = []
    for A in pred["monoids"]:
        for arch in ARM1A_ARCHS:
            tasks.append(("arm1a", A, arch, raw_dir, 2000))
    for A in pred["hmms"]:
        for arch in ARM1B_ARCHS:
            tasks.append(("arm1b", A, arch, raw_dir, 1500))
    for grp in ("D4", "A4"):
        for mdl in ARM2A_MODELS:
            for sd in (1, 2):
                tasks.append(("arm2a", grp, mdl, sd, raw_dir, 2500))
    for mdl in ARM2B_MODELS:
        for sd in (1, 2, 3):
            tasks.append(("arm2b", mdl, sd, raw_dir, 2500))

    print(f"Dispatching {len(tasks)} runs across {args.workers} workers -> {raw_dir}")
    arm1a_res, arm1b_res, arm2a_res, arm2b_res = [], [], [], []
    done_cnt = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_dispatch, t): t for t in tasks}
        for fut in as_completed(futs):
            r = fut.result()
            done_cnt += 1
            if r["arm"] == "arm1a":
                arm1a_res.append(r)
            elif r["arm"] == "arm1b":
                arm1b_res.append(r)
            elif r["arm"] == "arm2a":
                arm2a_res.append(r)
            else:
                arm2b_res.append(r)
            if done_cnt % 10 == 0 or done_cnt == len(tasks):
                print(f"[{done_cnt}/{len(tasks)}] {r['arm']} done ({time.time() - t0:.1f}s)")

    summary = evaluate_summary(pred, arm1a_res, arm1b_res, arm2a_res, arm2b_res, time.time() - t0)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"COMPLETED {summary['total_runs']} runs in {summary['total_elapsed_s']:.1f}s")
    print("VERDICTS:", json.dumps(summary["verdicts"]))


if __name__ == "__main__":
    main()
