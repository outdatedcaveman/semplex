"""Variational Master Principle & Non-Abelian Gauge-Ring Empirical Suite (`gemini/master-principle-variational`).

Companion to `MasterPrincipleVariational.lean` (26 Mathlib theorems) and
`MasterPrincipleGauge.lean` (16 Mathlib theorems).

Structure:
  0. `spike26_exact_check()`:
     - Exact rational Fraction checks on ChatGPT's Spike 26 `S_3` controlled HMM and a
       companion 5-class `D_4` controlled HMM.
     - Compares uniform syntactic weights `D_H` vs physical policy weights `P(h | pi_act)`.
     - Verifies centered `Wc_c + Wo_c` false-mode retention `(1, 2, 2)` vs exact centered
       Hankel rank `(0, 2, 0)` (and `(0, 4, 0)` on `D_4`), support-reduced Riccati realization
       `||(R_min X* R_min^T)^2 - H_c H_c^T||_F < 1e-12`, `GL(r)` covariance/invariance,
       stationary-prior `B=2` `rank(R)=1` collapse, and anti-identity `eta = 1/(n-1)`
       full-abstraction separation.
  1. Arm 1A (`12` fresh non-commuting monoids x `4` archs = `48` runs, `steps=2000`):
     - Tests derived primal Variational Master Operator `X_primal_var(lam) = (Wc^{-1} + lam L)^{-1} # Wo`
       against postulated heat-sandwiches `G_sum_heat(lam)`, `G_gm_heat(lam)`, dual `X_dual_var(lam)`,
       and static baselines in orthonormal `(m-1)`-dim `P_perp` coordinates, plus 41-point log-grid
       oracle ceilings and `eps_rel in {1e-6, 1e-4, 1e-2}` regularization sensitivity.
     - Tracks causal trajectory shifts on `rnn_mlp -> leaky_a025` and `rnn_mlp -> vel_warmup`.
  2. Arm 1B (`8` fresh HMMs [4 cyclic-group + 4 unbalanced non-reversible] x `2` archs = `16` runs):
     - Tests derived dual `X_dual_var(lam) = (Wc^{obs} + lam L)^{-1} # Wo^{obs}` vs `G_sum_heat`,
       `G_gm_heat`, `W_bal_dual`, `W_gm`, `W_sum`, `W_bal`, and `G_hist*(lam) = R X_dual(lam) R^T`.
  3. Arm 2A (Matched-Capacity Non-Abelian Gauge-Ring Benchmark: `3` groups x `4` models x `2` seeds = `24` runs):
     - `Z_3`, `S_3`, `D_4` with `L_train in {3, 4}` (holding out 25% of `L=4` + 100% OOD `L=5`).
     - Matched capacity (`16,000 +- 5%` params) across `local_edge_mlp`, `multiset_deepsets`,
       `ordered_gru`, and `gauge_equivariant_bilinear` (`MatProdNet` + soft orthogonal reg).
     - Evaluates held-out balanced accuracy (`bacc`), OOD `L=5` `bacc`, and exact `L=3` ANOVA
       decomposition of gauge-orbit collapse (`within_orbit_var / total_var`) and base-frame
       variance (`within_class_diff_hol_var / total_var`).
  4. Arm 2B (Dynamic Controlled `S_3` & `D_4` Gauge-Ring POMDPs: `2` groups x `3` regimes x `2` seeds = `12` runs):
     - Exact controlled POMDP trajectories in `(B=2, eta_inf)`, `(B=3, eta_inf)`, and `(B=3, eta_unif)`.
     - Measures `kl_gap`, `belief_r2`, `pca95_dim`, `eff_rank`, and unobservable state collapse ratio.
"""

from __future__ import annotations

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from fractions import Fraction as F
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
OUT = RESULTS / "master_principle_variational.json"
PRED = RESULTS / "master_principle_variational_predictions.json"

GAMMA_C = 0.6
GAMMA_O = 0.7
T_MON = 16
BURN_MON = 4
T_OP = 16
T_HMM = 12
BURN_HMM = 2
BATCH = 64

EPS_DEFAULT = 1e-4
EPS_SWEEP = (1e-6, 1e-4, 1e-2)
LAM_GRID = tuple([0.0] + [float(x) for x in np.geomspace(1e-2, 50.0, 40)])

ARM1A_ARCHS = ("gru_mlp", "rnn_mlp", "leaky_a025", "vel_warmup")
ARM1B_ARCHS = ("gru_mlp", "vel_warmup")
ARM2A_MODELS = ("local_edge_mlp", "multiset_deepsets", "ordered_gru", "gauge_equivariant_bilinear")


# ---------------------------------------------------------------------------
# Linear Algebra & SPD Variational Master Operator Utilities
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
    keep = vals > 0.5
    return vecs[:, keep]  # (m, r) orthonormal basis Q_perp


def spd_eigh_power(A: np.ndarray, power: float, floor: float = 1e-14) -> np.ndarray:
    vals, vecs = np.linalg.eigh(sym_mat(A))
    safe = np.maximum(vals, floor)
    return sym_mat((vecs * (safe ** power)) @ vecs.T)


def spd_geom_mean(P: np.ndarray, Q: np.ndarray, floor: float = 1e-14) -> np.ndarray:
    """Kubo-Ando geometric mean P # Q = P^{1/2} (P^{-1/2} Q P^{-1/2})^{1/2} P^{1/2}."""
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


class VariationalEvaluator:
    """Evaluates static, heat-sandwich, and variational geodesic operators in P_perp."""

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
        # Ensure Lkin PSD on reduced coordinates up to numerical floor
        ev_l, vec_l = np.linalg.eigh(self.Lk_q)
        self.Lk_q = sym_mat((vec_l * np.maximum(ev_l, 0.0)) @ vec_l.T)

        Wc_q = sym_mat(self.Q.T @ self.Wc @ self.Q)
        Wo_q = sym_mat(self.Q.T @ self.Wo @ self.Q)
        tr_c = max(float(np.trace(Wc_q)) / max(r, 1), 1e-12)
        tr_o = max(float(np.trace(Wo_q)) / max(r, 1), 1e-12)
        self.Wc_reg = sym_mat(Wc_q + (eps_rel * tr_c) * np.eye(r))
        self.Wo_reg = sym_mat(Wo_q + (1e-8 * tr_o) * np.eye(r))
        self.A_primal = sym_mat(np.linalg.inv(self.Wc_reg))
        self.A_dual = sym_mat(self.Wc_reg)

        # Static baselines in full space
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

    def eval_op(self, family: str, lam: float) -> np.ndarray:
        if family == "X_primal_var":
            Al = sym_mat(self.A_primal + lam * self.Lk_q)
            Al_inv = sym_mat(np.linalg.inv(Al))
            Xq = spd_geom_mean(Al_inv, self.Wo_reg)
            return self.lift(Xq)
        if family == "X_dual_var":
            Al = sym_mat(self.A_dual + lam * self.Lk_q)
            Al_inv = sym_mat(np.linalg.inv(Al))
            Xq = spd_geom_mean(Al_inv, self.Wo_reg)
            return self.lift(Xq)
        if family == "G_sum_heat":
            H = expm(-0.5 * lam * self.Lkin)
            return sym_perp(H @ self.static["W_sum"] @ H, self.Pperp)
        if family == "G_gm_heat":
            H = expm(-0.5 * lam * self.Lkin)
            return sym_perp(H @ self.static["W_gm"] @ H, self.Pperp)
        raise ValueError(f"Unknown operator family {family}")

    def check_variational_monotonicity(self, family: str = "X_primal_var") -> tuple[bool, bool]:
        """Check whether Tr(L_kin X*(lam)) and normalized kin(X*(lam)) decrease on lam >= 0."""
        lams = [0.0, 0.05, 0.2, 1.0, 4.0, 15.0, 50.0]
        raw_kins = []
        norm_kins = []
        for lv in lams:
            X = self.eval_op(family, lv)
            rk = float(np.trace(self.Lkin @ X))
            nk = dirichlet_kin_norm(X, self.Lkin)
            raw_kins.append(rk)
            norm_kins.append(nk)
        raw_mono = all(raw_kins[i + 1] <= raw_kins[i] + 1e-8 for i in range(len(lams) - 1))
        norm_mono = all(norm_kins[i + 1] <= norm_kins[i] + 1e-8 for i in range(len(lams) - 1))
        return raw_mono, norm_mono

    def invert_lambda(self, family: str, kin_obs: float, lo: float = -2.0, hi: float = 50.0) -> float:
        """Invert lambda matching kin_norm(Op(lam)) ~ kin_obs over lam in [lo, hi]."""
        if family in ("G_sum_heat", "G_gm_heat"):
            lo_use = -4.0
        else:
            # Ensure A + lam * Lk_q remains strictly PD on lower bound
            min_ratio = 0.0
            try:
                base_A = self.A_primal if family == "X_primal_var" else self.A_dual
                min_eig_A = float(np.linalg.eigvalsh(base_A).min())
                max_eig_L = float(np.linalg.eigvalsh(self.Lk_q).max())
                lo_use = max(-2.0, -0.8 * min_eig_A / max(max_eig_L, 1e-9))
            except np.linalg.LinAlgError:
                lo_use = 0.0

        grid = np.linspace(lo_use, hi, 35)
        vals = []
        for lv in grid:
            try:
                M = self.eval_op(family, float(lv))
                vals.append(dirichlet_kin_norm(M, self.Lkin))
            except np.linalg.LinAlgError:
                vals.append(float("nan"))

        # Check bracket around kin_obs
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

    def score_all(self, G_net: np.ndarray) -> dict:
        kin_obs = dirichlet_kin_norm(G_net, self.Lkin)
        scores = {}
        lams = {}
        for fam in ("X_primal_var", "X_dual_var", "G_sum_heat", "G_gm_heat"):
            lam = self.invert_lambda(fam, kin_obs)
            G_pred = self.eval_op(fam, lam)
            scores[fam] = cos_mat(G_net, G_pred)
            lams[fam] = float(lam)
            # Also 41-point oracle grid ceiling (pure operator geometry independent of lam inversion)
            best_c = -1.0
            best_l = 0.0
            for lg in LAM_GRID:
                c = cos_mat(G_net, self.eval_op(fam, lg))
                if c > best_c:
                    best_c = c
                    best_l = lg
            scores[f"{fam}_best"] = float(best_c)
            lams[f"{fam}_best"] = float(best_l)

        for st_name, mat in self.static.items():
            scores[st_name] = cos_mat(G_net, mat)
        return {"kin_norm": kin_obs, "scores": scores, "lams": lams}


# ---------------------------------------------------------------------------
# Exact Finite Groups & Spike 26 Exact Matrix Check
# ---------------------------------------------------------------------------

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
        # Conjugacy classes
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


def make_z3_group() -> FiniteGroup:
    return FiniteGroup("Z3", (0, 1, 2), 0, lambda a, b: (a + b) % 3, lambda a: (-a) % 3)


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


def controlled_pomdp_spec(group_name: str) -> dict:
    """Exact rational specifications for Spike 26 S_3 and companion 5-class D_4 controlled HMMs."""
    if group_name == "S3":
        P_wait = (
            (F(3, 4), F(1, 4), F(0)),
            (F(1, 8), F(3, 4), F(1, 8)),
            (F(0), F(1, 4), F(3, 4)),
        )
        P_probe = (
            (F(1, 2), F(1, 2), F(0)),
            (F(0), F(1, 2), F(1, 2)),
            (F(1, 4), F(0), F(3, 4)),
        )
        eta_inf, eta_unif, eta_anti = F(1, 6), F(1, 3), F(1, 2)
        prior_stat = (F(1, 4), F(1, 2), F(1, 4))
    elif group_name == "D4":
        # Non-doubly-stochastic invertible P_wait + asymmetric invertible P_probe on 5 classes
        P_wait = (
            (F(3, 4), F(1, 4), F(0), F(0), F(0)),
            (F(1, 8), F(3, 4), F(1, 8), F(0), F(0)),
            (F(0), F(1, 8), F(3, 4), F(1, 8), F(0)),
            (F(0), F(0), F(1, 8), F(3, 4), F(1, 8)),
            (F(0), F(0), F(0), F(1, 4), F(3, 4)),
        )
        P_probe = (
            (F(5, 8), F(3, 8), F(0), F(0), F(0)),
            (F(0), F(5, 8), F(3, 8), F(0), F(0)),
            (F(0), F(0), F(5, 8), F(3, 8), F(0)),
            (F(0), F(0), F(0), F(5, 8), F(3, 8)),
            (F(3, 8), F(0), F(0), F(0), F(5, 8)),
        )
        eta_inf, eta_unif, eta_anti = F(1, 10), F(1, 5), F(1, 4)
        prior_stat = (F(1, 8), F(1, 4), F(1, 4), F(1, 4), F(1, 8))
    else:
        raise ValueError(group_name)
    return {
        "n_cls": len(P_wait),
        "costs": {"wait": 1, "probe": 3},
        "P": {"wait": P_wait, "probe": P_probe},
        "eta_inf": eta_inf,
        "eta_unif": eta_unif,
        "eta_anti": eta_anti,
        "prior_stat": prior_stat,
    }


def _rational_hankel_exact(spec: dict, budget: int, eta: F, prior: tuple[F, ...]):
    n = spec["n_cls"]
    actions = ("wait", "probe")
    costs = spec["costs"]

    def k_prob(action: str, x: int, y: int) -> F:
        if action == "wait":
            return F(1, n)
        return F(1) - (n - 1) * eta if x == y else eta

    def joint(action: str, y: int):
        P = spec["P"][action]
        return [[P[i][j] * k_prob(action, j, y) for j in range(n)] for i in range(n)]

    words = [()]
    for length in range(1, budget + 1):
        for w in product(actions, repeat=length):
            if sum(costs[a] for a in w) <= budget:
                words.append(w)
    # Count word lengths <= budget -> equal probability per affordable word type, or uniform 1/2 per action step
    # Compute BOTH: syntactic uniform over realized sequences, AND physical policy probability P(h | pi_act)
    n_words = len(words)
    histories_post = []
    histories_prob = []
    for w in words:
        for ys in product(range(n), repeat=len(w)):
            alpha = list(prior)
            for a, y in zip(w, ys):
                M = joint(a, y)
                alpha = [sum(alpha[i] * M[i][j] for i in range(n)) for j in range(n)]
            mass = sum(alpha)
            if mass > 0:
                histories_post.append([x / mass for x in alpha])
                histories_prob.append(mass / n_words)

    tests_lik = []
    tests_prob = []
    for w in words:
        for ys in product(range(n), repeat=len(w)):
            lik = [F(1)] * n
            for a, y in reversed(list(zip(w, ys))):
                M = joint(a, y)
                lik = [sum(M[i][j] * lik[j] for j in range(n)) for i in range(n)]
            tests_lik.append(lik)
            tests_prob.append(F(1, n_words))

    R = np.array([[float(x) for x in r] for r in histories_post], dtype=float)
    O = np.array([[float(tests_lik[t][i]) for t in range(len(tests_lik))] for i in range(n)], dtype=float)
    p_h = np.array([float(x) for x in histories_prob], dtype=float)
    p_h = p_h / p_h.sum()
    p_t = np.array([float(x) for x in tests_prob], dtype=float)
    p_t = p_t / p_t.sum()
    return R, O, p_h, p_t


def spike26_exact_check() -> dict:
    """Exact verification of centered Wc+Wo vs Hankel rank, uniform vs policy weights,
    support-reduced Riccati realization, GL(r) invariance, stationary prior, and eta anti-identity."""
    out = {}
    for gname in ("S3", "D4"):
        spec = controlled_pomdp_spec(gname)
        n = spec["n_cls"]
        prior_u = tuple([F(1, n)] * n)
        regimes = [
            ("B2_inf", 2, spec["eta_inf"], prior_u),
            ("B3_inf", 3, spec["eta_inf"], prior_u),
            ("B3_unif", 3, spec["eta_unif"], prior_u),
            ("B3_anti", 3, spec["eta_anti"], prior_u),
            ("B2_stat", 2, spec["eta_inf"], spec["prior_stat"]),
        ]
        res_g = {}
        for rname, B, eta, prior in regimes:
            R, O, p_h, p_t = _rational_hankel_exact(spec, B, eta, prior)
            rank_R = int(np.linalg.matrix_rank(R, tol=1e-10))
            rank_O = int(np.linalg.matrix_rank(O, tol=1e-10))
            H_unif = (R @ O) / math.sqrt(len(R) * O.shape[1])
            rank_H = int(np.linalg.matrix_rank(H_unif, tol=1e-10))

            by_weight = {}
            for wtag, d_h, d_t in [
                ("uniform_syntactic", np.full(len(R), 1.0 / len(R)), np.full(O.shape[1], 1.0 / O.shape[1])),
                ("policy_prob", p_h, p_t),
            ]:
                sw_h = np.sqrt(d_h)
                sw_t = np.sqrt(d_t)
                Rw = sw_h[:, None] * R
                Ow = O * sw_t[None, :]
                Hw = Rw @ Ow
                # Center w.r.t. stationary/mean posterior weighted by d_h (eliminating trivial constant future mode)
                one_h = sw_h / np.linalg.norm(sw_h)
                P_h_perp = np.eye(len(R)) - np.outer(one_h, one_h)
                Rw_c = P_h_perp @ Rw
                # Subtract weighted mean future row in weighted space: center rows of Rw -> Hw_c = Rw_c @ Ow
                Hw_c = Rw_c @ Ow
                Wc_c = sym_mat(Rw_c.T @ Rw_c)
                # Center O wrt mean state vector under prior? Better: state-projection onto range of Wc_c + P_s_perp
                mu_row = (d_h @ R)
                mu_row = mu_row / np.linalg.norm(mu_row)
                P_s_perp = np.eye(n) - np.ones((n, n)) / n
                Wc_s = sym_mat(P_s_perp @ (Rw.T @ Rw) @ P_s_perp)
                Wo_s = sym_mat(P_s_perp @ (Ow @ Ow.T) @ P_s_perp)
                rk_Wc_s = int(np.linalg.matrix_rank(Wc_s, tol=1e-10))
                rk_Wo_s = int(np.linalg.matrix_rank(Wo_s, tol=1e-10))
                rk_sum_s = int(np.linalg.matrix_rank(Wc_s + Wo_s, tol=1e-10))
                rk_Hc = int(np.linalg.matrix_rank(Hw_c, tol=1e-10))

                ric_err = None
                gl_cov_err = None
                gl_inv_err = None
                zero_collapse = None
                if rk_Hc == 0:
                    zero_collapse = bool(float(np.linalg.norm(Hw_c)) < 1e-12)
                else:
                    # Trim to minimal r = rk_Hc support via thin SVD on Hw_c:
                    U_h, s_h, Vt_h = np.linalg.svd(Hw_c, full_matrices=False)
                    keep = s_h > 1e-10 * s_h[0]
                    r_dim = int(np.sum(keep))
                    R_min = U_h[:, keep] * np.sqrt(s_h[keep])[None, :]
                    O_min = (np.sqrt(s_h[keep])[:, None]) * Vt_h[keep, :]
                    Wc_m = sym_mat(R_min.T @ R_min)
                    Wo_m = sym_mat(O_min @ O_min.T)
                    X_m = spd_geom_mean(np.linalg.inv(Wc_m), Wo_m)
                    G_hist = R_min @ X_m @ R_min.T
                    ric_err = float(np.linalg.norm(G_hist @ G_hist - Hw_c @ Hw_c.T))

                    # Check GL(r_dim) covariance & history invariance
                    rng_gl = np.random.default_rng(77 + r_dim)
                    S = rng_gl.standard_normal((r_dim, r_dim)) + 2.0 * np.eye(r_dim)
                    Sinv = np.linalg.inv(S)
                    Rp, Op = R_min @ Sinv, S @ O_min
                    X_p = spd_geom_mean(np.linalg.inv(sym_mat(Rp.T @ Rp)), sym_mat(Op @ Op.T))
                    gl_cov_err = float(np.linalg.norm(X_p - S @ X_m @ S.T))
                    gl_inv_err = float(np.linalg.norm(Rp @ X_p @ Rp.T - G_hist))

                by_weight[wtag] = {
                    "rank_Wc_c": rk_Wc_s,
                    "rank_Wo_c": rk_Wo_s,
                    "rank_Wc_c_plus_Wo_c": rk_sum_s,
                    "rank_Hc": rk_Hc,
                    "riccati_history_sq_err": ric_err,
                    "gl_cov_err": gl_cov_err,
                    "gl_inv_err": gl_inv_err,
                    "zero_hankel_verified": zero_collapse,
                }

            res_g[rname] = {
                "n_histories": int(len(R)),
                "n_tests": int(O.shape[1]),
                "rank_R": rank_R,
                "rank_O": rank_O,
                "rank_H": rank_H,
                "weights": by_weight,
            }
        out[gname] = res_g
    return out


# ---------------------------------------------------------------------------
# Arm 1A & Arm 1B Builders and Trainers (Non-Commuting Monoids & HMMs)
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

    # Check exact Hankel realization (R X_dual R^T)^2 = H H^T on centered space
    H = R_feat @ O_feat
    ev = VariationalEvaluator(Wc_obs, Wo_obs, Lkin, Pperp, Wo_obs, eps_rel=1e-10)
    G_hist = R_feat @ ev.eval_op("X_dual_var", 0.0) @ R_feat.T
    hankel_real_err = float(np.linalg.norm(G_hist @ G_hist - H @ H.T))

    return {
        "Pperp": Pperp,
        "Lkin": Lkin,
        "Wc_obs": Wc_obs,
        "Wo_obs": Wo_obs,
        "comm_ratio_obs": commutator_ratio(Wc_obs, Wo_obs),
        "hankel_realization_err": hankel_real_err,
    }


def predict() -> dict:
    # 1. Exact Spike 26 & D_4 matrix verification
    s26 = spike26_exact_check()

    # 2. 12 fresh strongly non-commuting monoids (seed 2026112301)
    rng_mon = np.random.default_rng(2026112301)
    cands_mon = []
    seen = set()
    for _ in range(600):
        d, o = S81.random_automaton(rng_mon, 8, 2, "free")
        D, O, s0 = S81.minimize(d, o, start=0)
        if D.shape[1] < 6 or O.min() == O.max():
            continue
        sig = (tuple(map(tuple, D.tolist())), tuple(O.tolist()), int(s0))
        if sig in seen:
            continue
        seen.add(sig)
        Dl = np.vstack([D, np.arange(D.shape[1])[None]])
        k = Dl.shape[0]
        pi = S81.visit_dist(Dl, s0, np.ones(k) / k, T=T_MON, burn=BURN_MON)
        if (pi <= 1e-3).any():
            continue
        ops = monoid_base_operators(Dl, O, pi)
        Wc, Wo, Lkin, Pperp, o_gr = ops["Wc"], ops["Wo"], ops["Lkin"], ops["Pperp"], ops["o"]
        if np.linalg.norm(Wc) < 1e-2 or np.linalg.norm(Wo) < 1e-2:
            continue
        cr = commutator_ratio(Wc, Wo)
        if cr < 0.12:
            continue
        ev = VariationalEvaluator(Wc, Wo, Lkin, Pperp, o_gr, eps_rel=EPS_DEFAULT)
        G_sum_1 = ev.eval_op("G_sum_heat", 1.0)
        if cos_mat(G_sum_1, o_gr) >= 0.90:
            continue
        X_pr_1 = ev.eval_op("X_primal_var", 1.0)
        G_gm_1 = ev.eval_op("G_gm_heat", 1.0)
        raw_mono, norm_mono = ev.check_variational_monotonicity("X_primal_var")
        sep = 1.0 - min(cos_mat(X_pr_1, G_sum_1), cos_mat(X_pr_1, G_gm_1))
        cands_mon.append({
            "D": D.tolist(),
            "Dl": Dl.tolist(),
            "out": O.tolist(),
            "s0": int(s0),
            "m": int(Dl.shape[1]),
            "L": int(k),
            "pi": pi.tolist(),
            "comm_ratio": float(cr),
            "sep": float(sep),
            "raw_mono": bool(raw_mono),
            "norm_mono": bool(norm_mono),
            "Pperp": Pperp.tolist(),
            "Lkin": Lkin.tolist(),
            "Wc": Wc.tolist(),
            "Wo": Wo.tolist(),
            "o": o_gr.tolist(),
        })
    assert len(cands_mon) >= 12, f"Found only {len(cands_mon)} qualified monoids!"
    cands_mon.sort(key=lambda r: -r["sep"])
    picked_mon = cands_mon[:12]
    for i, r in enumerate(picked_mon):
        r["name"] = f"NCM_V{i:02d}"
        r["seed"] = 4200 + i

    # 3. 8 fresh HMMs (4 cyclic + 4 strongly unbalanced non-reversible, seed 2026112302)
    rng_hmm = np.random.default_rng(2026112302)
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
        assert np.allclose(Olik.sum(0), 1.0)
        P_actions = np.zeros((2, m, m), dtype=float)
        step2 = 2 if m >= 5 else 3
        for x in range(m):
            P_actions[0, x, (x + 1) % m] = 1.0
            P_actions[1, x, (x + step2) % m] = 1.0
        pi = np.ones(m) / m
        hops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        hmms.append({
            "name": nm,
            "seed": 4300 + idx,
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
        Olik = rng_hmm.dirichlet(np.full(n_obs, 0.85), size=m).T
        Olik = np.clip(Olik, 0.05, 0.95)
        Olik = Olik / Olik.sum(axis=0, keepdims=True)
        pi = stationary_distribution(0.5 * (P_actions[0] + P_actions[1]))
        if pi.min() < 0.04:
            continue
        hops = compute_hmm_operators(P_actions, Olik, pi, rng_hmm)
        if hops["comm_ratio_obs"] < 0.12 or np.linalg.norm(hops["Wc_obs"]) < 1e-2 or np.linalg.norm(hops["Wo_obs"]) < 1e-2:
            continue
        hmms.append({
            "name": f"hmm_nr_V{nr_cnt}",
            "seed": 4304 + nr_cnt,
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

    # 4. Compute theoretical unordered-multiset ceiling on L=4 for Z3, S3, D4 + collision pairs
    multiset_ceilings = {}
    for grp in (make_z3_group(), make_s3_group(), make_d4_group()):
        tab = grp.build_tables()
        G, mul, cls_of, n_cls = tab["G"], tab["mul"], tab["cls_of"], tab["n_cls"]
        rng_m = np.random.default_rng(4499 + G)
        samples = (
            np.array(list(product(range(G), repeat=4)), dtype=np.int64)
            if G ** 4 <= 4096
            else rng_m.integers(0, G, size=(4096, 4))
        )
        h = samples[:, 0]
        for t in range(1, 4):
            h = mul[samples[:, t], h]
        ys = cls_of[h]
        counts_by_ms: dict[tuple[int, ...], Counter] = {}
        rows_by_ms_cls: dict[tuple[int, ...], dict[int, list]] = {}
        for row, y in zip(samples.tolist(), ys.tolist()):
            ms = tuple(sorted(row))
            counts_by_ms.setdefault(ms, Counter())[y] += 1
            rows_by_ms_cls.setdefault(ms, {}).setdefault(int(y), []).append(row)
        preds_opt = np.array([counts_by_ms[tuple(sorted(row))].most_common(1)[0][0] for row in samples.tolist()])
        n_coll_pairs = sum(1 for d in rows_by_ms_cls.values() if len(d) > 1)
        multiset_ceilings[grp.name] = {
            "n_multisets_L4": len(counts_by_ms),
            "n_ambiguous_multisets_L4": n_coll_pairs,
            "bayes_optimal_acc_L4": float((preds_opt == ys).mean()),
            "bayes_optimal_bacc_L4": balanced_acc(preds_opt, ys, n_cls),
        }

    pred_data = {
        "spike26_exact_check": s26,
        "monoids": picked_mon,
        "hmms": hmms,
        "multiset_ceilings": multiset_ceilings,
    }
    PRED.parent.mkdir(parents=True, exist_ok=True)
    PRED.write_text(json.dumps(pred_data, indent=2), encoding="utf-8")
    return pred_data


# ---------------------------------------------------------------------------
# PyTorch Models & Training Loops (Arm 1A, Arm 1B, Arm 2A, Arm 2B)
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
    Y = O_mat[ST].astype(np.float32)
    return torch.from_numpy(X).long(), torch.from_numpy(Y), ST


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


def run_arm1a_task(A: dict, arch: str, raw_dir: pathlib.Path) -> dict:
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

    arch_offset = ARM1A_ARCHS.index(arch) * 1000
    seed = int(A["seed"]) + arch_offset
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    mdl = make_arm1a_model(arch, L, k_out)
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    steps = 2000
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=3e-4)
    use_vel = (arch == "vel_warmup")

    t0 = time.time()
    for step in range(steps):
        X, Y, _ = fast_sample_monoid(Dl, O, A["s0"], BATCH, T_MON, rng)
        H = mdl.hidden(X)
        logits = mdl.head(H)
        loss = nn.functional.binary_cross_entropy_with_logits(logits[:, BURN_MON:], Y[:, BURN_MON:])
        if use_vel and step >= 1000:
            mu = 0.05 if step >= 1500 else 0.05 * ((step - 1000) / 500.0)
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
    X_ev, Y_ev, ST_ev = fast_sample_monoid(Dl, O, A["s0"], 400, T_MON, np.random.default_rng(int(A["seed"]) + 900_000 + arch_offset))
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

    ev_def = VariationalEvaluator(Wc, Wo, Lkin, Pperp, o_gram, eps_rel=EPS_DEFAULT)
    scored = ev_def.score_all(G_net)

    eps_sens = {}
    for er in EPS_SWEEP:
        ev_e = VariationalEvaluator(Wc, Wo, Lkin, Pperp, o_gram, eps_rel=er)
        sc_e = ev_e.score_all(G_net)
        eps_sens[f"{er:.0e}"] = {
            "X_primal_var": sc_e["scores"]["X_primal_var"],
            "X_primal_var_best": sc_e["scores"]["X_primal_var_best"],
        }

    res = {
        "arm": "arm1a",
        "name": name,
        "arch": arch,
        "fit": fit,
        "G_net": G_net.tolist(),
        "eps_sensitivity": eps_sens,
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
        u = rng.random(B)
        y = np.argmax(np.cumsum(probs_y, axis=1) >= u[:, None], axis=1)

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


def run_arm1b_task(A: dict, arch: str, raw_dir: pathlib.Path) -> dict:
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
    steps = 1500
    use_vel = (arch == "vel_warmup")
    t0 = time.time()

    for step in range(steps):
        IN, TG, _, _ = sample_hmm_batch(P_actions, Olik, pi, BATCH, T_HMM, rng)
        H = mdl.hidden(torch.from_numpy(IN))
        logits = mdl.head(H)[:, BURN_HMM:]
        tgt = torch.from_numpy(TG)[:, BURN_HMM:]
        loss = F.cross_entropy(logits.reshape(-1, n_obs), tgt.reshape(-1))
        if use_vel and step >= 750:
            mu = 0.05 if step >= 1125 else 0.05 * ((step - 750) / 375.0)
            H_st = H[:, BURN_HMM:]
            dh = (H_st[:, 1:] - H_st[:, :-1]).pow(2).mean()
            var_h = (H_st - H_st.mean(dim=(0, 1), keepdim=True)).pow(2).mean().clamp_min(1e-4)
            loss = loss + mu * (dh / var_h)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()

    mdl.eval()
    IN_ev, TG_ev, MU_ev, BAYES_ev = sample_hmm_batch(
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
    ss_res = float(np.sum((M_te - M_pred) ** 2))
    ss_tot = float(np.sum((M_te - M_te.mean(axis=0, keepdims=True)) ** 2))
    belief_r2 = float(1.0 - ss_res / max(ss_tot, 1e-12))

    H_all = np.concatenate([H_tr, H_te], axis=0)
    M_all = np.concatenate([M_tr, M_te], axis=0)
    V = np.linalg.solve(M_all.T @ M_all + 1e-6 * np.eye(m), M_all.T @ H_all)
    Dpi_h = np.diag(np.sqrt(pi))
    G_net_state = sym_perp(Dpi_h @ (V @ V.T) @ Dpi_h, Pperp)

    H_sub = H_te[:384] - H_te[:384].mean(axis=0, keepdims=True)
    K_net = sym_mat(H_sub @ H_sub.T)
    Dpi_inv_h = np.diag(1.0 / np.sqrt(pi))
    R_sub = (M_te[:384] - pi[None, :]) @ Dpi_inv_h

    ev_hmm = VariationalEvaluator(Wc_obs, Wo_obs, Lkin, Pperp, Wo_obs, eps_rel=1e-5)
    kin_obs = dirichlet_kin_norm(G_net_state, Lkin)
    state_scores = {}
    hist_scores = {}
    lams = {}
    for fam in ("X_dual_var", "X_primal_var", "G_sum_heat", "G_gm_heat"):
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
        "G_net_state": G_net_state.tolist(),
        "state_scores": state_scores,
        "hist_scores": hist_scores,
        "lams": lams,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm1b_{name}_{arch}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def make_arm2a_model(model_name: str, G_size: int, n_cls: int):
    import torch
    import torch.nn as nn

    if model_name == "local_edge_mlp":
        class LocalEdgeMLP(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 64)
                self.net = nn.Sequential(nn.Linear(64, 96), nn.Tanh(), nn.Linear(96, 96), nn.Tanh())
                self.head = nn.Linear(96, n_cls)
            def extract(self, X):
                z = self.net(self.emb(X))
                pen = z.mean(dim=1)
                logits = self.head(z).mean(dim=1)
                return pen, pen, logits
            def forward(self, X):
                return self.head(self.net(self.emb(X))).mean(dim=1)
        m = LocalEdgeMLP()
    elif model_name == "multiset_deepsets":
        class MultisetDeepSets(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 64)
                self.phi = nn.Sequential(nn.Linear(64, 64), nn.Tanh())
                self.rho_trunk = nn.Sequential(nn.Linear(64, 92), nn.Tanh(), nn.Linear(92, 60), nn.Tanh())
                self.head = nn.Linear(60, n_cls)
            def extract(self, X):
                z = self.phi(self.emb(X)).mean(dim=1)
                pen = self.rho_trunk(z)
                return z, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = MultisetDeepSets()
    elif model_name == "ordered_gru":
        class OrderedGRU(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G_size, 32)
                self.rnn = nn.GRU(32, 54, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(54, 24), nn.Tanh())
                self.head = nn.Linear(24, n_cls)
            def extract(self, X):
                h_last = self.rnn(self.emb(X))[0][:, -1, :]
                pen = self.trunk(h_last)
                return h_last, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = OrderedGRU()
    elif model_name == "gauge_equivariant_bilinear":
        class GaugeEquivBilinear(nn.Module):
            def __init__(self, k: int = 8):
                super().__init__()
                self.k = k
                self.M = nn.Parameter(torch.randn(G_size, k, k) / math.sqrt(k))
                h2 = 112 if G_size < 8 else 110
                self.trunk = nn.Sequential(nn.Linear(6, 128), nn.Tanh(), nn.Linear(128, h2), nn.Tanh())
                self.head = nn.Linear(h2, n_cls)
                self.register_buffer("eye", torch.eye(k))
            def orth_reg(self):
                return ((torch.bmm(self.M.transpose(-1, -2), self.M) - self.eye.unsqueeze(0)) ** 2).mean()
            def extract(self, X):
                Ms = self.M[X]
                P = Ms[:, 0]
                for t in range(1, X.shape[1]):
                    P = torch.bmm(Ms[:, t], P)
                d = torch.arange(self.k, device=X.device)
                traces = []
                Pk = P
                for r in range(6):
                    if r > 0:
                        Pk = torch.bmm(Pk, P)
                    traces.append(Pk[:, d, d].sum(-1) / self.k)
                inv = torch.stack(traces, dim=-1)
                pen = self.trunk(inv)
                return inv, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = GaugeEquivBilinear()
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    assert 15200 <= n_params <= 16800, f"{model_name} G={G_size} params={n_params} outside 16,000 +- 5%"
    return m, n_params


def balanced_acc(preds: np.ndarray, targets: np.ndarray, n_cls: int) -> float:
    accs = []
    for c in range(n_cls):
        mask = (targets == c)
        if mask.any():
            accs.append(float((preds[mask] == targets[mask]).mean()))
    return float(np.mean(accs))


def gauge_orbit_anova(feats: np.ndarray, hols: np.ndarray, classes: np.ndarray) -> dict:
    """Exact variance decomposition across gauge orbits (classes) and ordered base-frame holonomies."""
    total_var = float(np.mean(np.sum((feats - feats.mean(axis=0, keepdims=True)) ** 2, axis=1)))
    if total_var < 1e-12:
        return {"within_orbit_ratio": 1.0, "base_frame_within_class_ratio": 0.0, "within_hol_ratio": 1.0}
    within_orbit = 0.0
    for c in np.unique(classes):
        m_c = (classes == c)
        fc = feats[m_c]
        within_orbit += float(np.sum((fc - fc.mean(axis=0, keepdims=True)) ** 2))
    within_orbit /= len(feats)

    within_hol = 0.0
    for h in np.unique(hols):
        m_h = (hols == h)
        fh = feats[m_h]
        within_hol += float(np.sum((fh - fh.mean(axis=0, keepdims=True)) ** 2))
    within_hol /= len(feats)

    base_frame_var = max(within_orbit - within_hol, 0.0)
    return {
        "within_orbit_ratio": float(within_orbit / total_var),
        "base_frame_within_class_ratio": float(base_frame_var / total_var),
        "within_hol_ratio": float(within_hol / total_var),
    }


def run_arm2a_task(group_name: str, model_name: str, seed: int, raw_dir: pathlib.Path) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)

    grp = {"Z3": make_z3_group(), "S3": make_s3_group(), "D4": make_d4_group()}[group_name]
    tab = grp.build_tables()
    G, mul, cls_of, n_cls = tab["G"], tab["mul"], tab["cls_of"], tab["n_cls"]

    def hol_and_cls(A: np.ndarray):
        h = A[:, 0]
        for t in range(1, A.shape[1]):
            h = mul[A[:, t], h]
        return h, cls_of[h]

    # Deterministic stratified train/held-out split on L=4
    split_rng = np.random.default_rng(44000 + G)
    X3_tr = np.array(list(product(range(G), repeat=3)), dtype=np.int64)
    _, Y3_tr = hol_and_cls(X3_tr)

    all4 = np.array(list(product(range(G), repeat=4)), dtype=np.int64)
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

    if G ** 5 <= 243:
        X5_ood = np.array(list(product(range(G), repeat=5)), dtype=np.int64)
    else:
        X5_ood = split_rng.integers(0, G, size=(1000, 5), dtype=np.int64)
    _, Y5_ood = hol_and_cls(X5_ood)

    # Exact non-Abelian unordered-multiset collision pairs from held-out / L=4 space
    by_ms_va: dict[tuple[int, ...], dict[int, list]] = {}
    for row, y in zip(X4_va.tolist(), Y4_va.tolist()):
        by_ms_va.setdefault(tuple(sorted(row)), {}).setdefault(int(y), []).append(row)
    coll_x1, coll_y1, coll_x2, coll_y2 = [], [], [], []
    for d in by_ms_va.values():
        keys = sorted(d.keys())
        if len(keys) >= 2:
            coll_x1.append(d[keys[0]][0])
            coll_y1.append(keys[0])
            coll_x2.append(d[keys[1]][0])
            coll_y2.append(keys[1])

    run_seed = seed + 100 * G + 10 * ARM2A_MODELS.index(model_name)
    torch.manual_seed(run_seed)
    rng = np.random.default_rng(run_seed)

    mdl, n_params = make_arm2a_model(model_name, G, n_cls)
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    steps = 1500
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=3e-4)

    t0 = time.time()
    for step in range(steps):
        if step % 2 == 0:
            idx = rng.integers(0, len(X3_tr), size=min(BATCH, len(X3_tr)))
            xb, yb = X3_tr[idx], Y3_tr[idx]
        else:
            idx = rng.integers(0, len(X4_tr), size=BATCH)
            xb, yb = X4_tr[idx], Y4_tr[idx]
        loss = F.cross_entropy(mdl(torch.from_numpy(xb)), torch.from_numpy(yb))
        if hasattr(mdl, "orth_reg"):
            loss = loss + 0.5 * mdl.orth_reg()
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()
        sch.step()

    mdl.eval()
    with torch.no_grad():
        log3 = mdl(torch.from_numpy(X3_tr))
        p3 = log3.argmax(-1).numpy()
        log4 = mdl(torch.from_numpy(X4_va))
        p4 = log4.argmax(-1).numpy()
        ce4 = float(F.cross_entropy(log4, torch.from_numpy(Y4_va)))
        log5 = mdl(torch.from_numpy(X5_ood))
        p5 = log5.argmax(-1).numpy()
        ce5 = float(F.cross_entropy(log5, torch.from_numpy(Y5_ood)))

        coll_pair_sep = None
        if coll_x1:
            cp1 = mdl(torch.from_numpy(np.array(coll_x1, dtype=np.int64))).argmax(-1).numpy()
            cp2 = mdl(torch.from_numpy(np.array(coll_x2, dtype=np.int64))).argmax(-1).numpy()
            coll_pair_sep = float(((cp1 == np.array(coll_y1)) & (cp2 == np.array(coll_y2))).mean())

        h_all, c_all = hol_and_cls(X3_tr)
        z_raw, pen_feats, _ = mdl.extract(torch.from_numpy(X3_tr))
        anova_raw = gauge_orbit_anova(z_raw.numpy(), h_all, c_all)
        anova_pen = gauge_orbit_anova(pen_feats.numpy(), h_all, c_all)

    res = {
        "arm": "arm2a",
        "group": group_name,
        "model": model_name,
        "seed": seed,
        "n_params": int(n_params),
        "n_cls": int(n_cls),
        "acc_L3_train": float((p3 == Y3_tr).mean()),
        "bacc_L3_train": balanced_acc(p3, Y3_tr, n_cls),
        "acc_L4_heldout": float((p4 == Y4_va).mean()),
        "bacc_L4_heldout": balanced_acc(p4, Y4_va, n_cls),
        "ce_L4_heldout": ce4,
        "acc_L5_ood": float((p5 == Y5_ood).mean()),
        "bacc_L5_ood": balanced_acc(p5, Y5_ood, n_cls),
        "ce_L5_ood": ce5,
        "collision_pair_sep": coll_pair_sep,
        "n_collision_pairs": len(coll_x1),
        "anova_raw": anova_raw,
        "anova_pen": anova_pen,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm2a_{group_name}_{model_name}_{seed}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def run_arm2b_task(group_name: str, regime: str, seed: int, raw_dir: pathlib.Path) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)

    spec = controlled_pomdp_spec(group_name)
    n = spec["n_cls"]
    P_wait = np.array([[float(x) for x in r] for r in spec["P"]["wait"]], dtype=float)
    P_probe = np.array([[float(x) for x in r] for r in spec["P"]["probe"]], dtype=float)
    P_actions = np.stack([P_wait, P_probe], axis=0)  # 0=wait, 1=probe
    p_probe = 0.0 if regime == "B2_inf" else 0.5
    eta = float(spec["eta_unif"] if regime == "B3_unif" else spec["eta_inf"])

    Olik = np.zeros((2, n, n), dtype=float)  # (a, y, x) = P(y | a, x)
    Olik[0] = 1.0 / n
    Olik[1] = eta
    np.fill_diagonal(Olik[1], 1.0 - (n - 1) * eta)

    pi = stationary_distribution((1.0 - p_probe) * P_wait + p_probe * P_probe)
    # Centering / Lkin for exact operator alignment check in B3_inf
    W = np.sqrt(pi)
    one = W / np.linalg.norm(W)
    Pperp = np.eye(n) - np.outer(one, one)
    Ts = [((W[:, None] * P_actions[a]) / W[None, :]) for a in range(2)]
    Lkin = np.zeros((n, n))
    for Ta in Ts:
        Lkin += (Ta - np.eye(n)).T @ (Ta - np.eye(n))
    Lkin = 0.5 / 2 * sym_perp(Lkin, Pperp)

    def sample_pomdp(B: int, T: int, rng_s: np.random.Generator):
        IN = np.zeros((B, T, 2 + n), dtype=np.float32)  # [prev_a (2), y_t (n)]
        QRY = np.zeros((B, T, 2), dtype=np.float32)       # next_a one-hot
        TG = np.zeros((B, T), dtype=np.int64)
        MU = np.zeros((B, T, n), dtype=np.float32)
        BAYES = np.zeros((B, T, n), dtype=np.float32)

        x = rng_s.choice(n, size=B, p=pi)
        bel = np.broadcast_to(pi, (B, n)).copy()
        prev_a = np.zeros(B, dtype=np.int64)  # wait at t=0 (wait emission uniform anyway)

        for t in range(T):
            probs_y = Olik[prev_a, :, x]  # (B, n)
            u = rng_s.random(B)
            y = np.argmax(np.cumsum(probs_y, axis=1) >= u[:, None], axis=1)
            lik_mat = Olik[prev_a, y, :]  # (B, n)
            bel = bel * lik_mat
            bel = bel / np.maximum(bel.sum(axis=1, keepdims=True), 1e-15)
            MU[:, t, :] = bel.astype(np.float32)

            if t > 0:
                IN[np.arange(B), t, prev_a] = 1.0
            IN[np.arange(B), t, 2 + y] = 1.0

            nxt_a = (rng_s.random(B) < p_probe).astype(np.int64)
            QRY[np.arange(B), t, nxt_a] = 1.0

            probs_x = P_actions[nxt_a, x]
            x_nxt = np.argmax(np.cumsum(probs_x, axis=1) >= rng_s.random(B)[:, None], axis=1)
            probs_yn = Olik[nxt_a, :, x_nxt]
            y_nxt = np.argmax(np.cumsum(probs_yn, axis=1) >= rng_s.random(B)[:, None], axis=1)
            TG[:, t] = y_nxt

            bel_pred = np.einsum("bm,bmn->bn", bel, P_actions[nxt_a])
            # Expected emission E[O_a | b] = bel_pred @ Olik[nxt_a].T
            p_y_nxt = np.einsum("bn,byn->by", bel_pred, Olik[nxt_a])
            BAYES[:, t, :] = p_y_nxt.astype(np.float32)

            bel = bel_pred
            x = x_nxt
            prev_a = nxt_a

        return IN, QRY, TG, MU, BAYES

    class POMDPGRU(nn.Module):
        def __init__(self):
            super().__init__()
            self.in_proj = nn.Linear(2 + n, 64)
            self.rnn = nn.GRU(64, 64, batch_first=True)
            self.head = nn.Sequential(nn.Linear(64 + 2, 64), nn.Tanh(), nn.Linear(64, 64), nn.Tanh(), nn.Linear(64, n))
        def hidden(self, x):
            return self.rnn(self.in_proj(x))[0]
        def forward(self, x, qry):
            h = self.hidden(x)
            return self.head(torch.cat([h, qry], dim=-1))

    r_idx = ["B2_inf", "B3_inf", "B3_unif"].index(regime)
    run_seed = seed + (100 if group_name == "D4" else 0) + 10 * r_idx
    torch.manual_seed(run_seed)
    rng = np.random.default_rng(run_seed)

    mdl = POMDPGRU()
    opt = torch.optim.AdamW(mdl.parameters(), lr=3e-3, weight_decay=0.0)
    T_PO, BURN_PO, steps = 14, 4, 1500
    t0 = time.time()

    for _ in range(steps):
        IN, QRY, TG, _, _ = sample_pomdp(BATCH, T_PO, rng)
        logits = mdl(torch.from_numpy(IN), torch.from_numpy(QRY))[:, BURN_PO:]
        tgt = torch.from_numpy(TG)[:, BURN_PO:]
        loss = F.cross_entropy(logits.reshape(-1, n), tgt.reshape(-1))
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(mdl.parameters(), 1.0)
        opt.step()

    mdl.eval()
    IN_ev, QRY_ev, _, MU_ev, BAYES_ev = sample_pomdp(400, T_PO, np.random.default_rng(run_seed + 50_000))
    with torch.no_grad():
        H_ev = mdl.hidden(torch.from_numpy(IN_ev)).numpy()
        logits_ev = mdl(torch.from_numpy(IN_ev), torch.from_numpy(QRY_ev))[:, BURN_PO:].numpy()

    p_bayes = np.clip(BAYES_ev[:, BURN_PO:].reshape(-1, n), 1e-12, 1.0)
    ex = np.exp(logits_ev - logits_ev.max(axis=-1, keepdims=True))
    p_mod = np.clip((ex / ex.sum(axis=-1, keepdims=True)).reshape(-1, n), 1e-12, 1.0)
    kl_gap = float(np.mean(np.sum(p_bayes * (np.log(p_bayes) - np.log(p_mod)), axis=1)))

    H_tr = H_ev[:200, BURN_PO:].reshape(-1, 64)
    H_te = H_ev[200:, BURN_PO:].reshape(-1, 64)
    M_tr = MU_ev[:200, BURN_PO:].reshape(-1, n)
    M_te = MU_ev[200:, BURN_PO:].reshape(-1, n)
    coef, _, _, _ = np.linalg.lstsq(np.column_stack([H_tr, np.ones(len(H_tr))]), M_tr, rcond=1e-5)
    M_pred = np.column_stack([H_te, np.ones(len(H_te))]) @ coef
    ss_res = float(np.sum((M_te - M_pred) ** 2))
    ss_tot = float(np.sum((M_te - M_te.mean(axis=0, keepdims=True)) ** 2))
    belief_r2 = float(1.0 - ss_res / max(ss_tot, 1e-12)) if ss_tot > 1e-12 else 0.0

    Hc = H_te - H_te.mean(axis=0, keepdims=True)
    _, s_pca, _ = np.linalg.svd(Hc, full_matrices=False)
    eig_h = (s_pca ** 2) / max(len(Hc), 1)
    total_var = float(np.sum(eig_h))
    ev_norm = eig_h / max(total_var, 1e-15)
    pca95_dim = int(np.searchsorted(np.cumsum(ev_norm), 0.95) + 1)
    eff_rank = float((np.sum(eig_h) ** 2) / max(float(np.sum(eig_h ** 2)), 1e-15)) if total_var > 1e-10 else 0.0

    res = {
        "arm": "arm2b",
        "group": group_name,
        "regime": regime,
        "seed": seed,
        "kl_gap": kl_gap,
        "belief_r2": belief_r2,
        "state_var_total": total_var,
        "pca95_dim": pca95_dim,
        "eff_rank": eff_rank,
        "elapsed_s": float(time.time() - t0),
    }
    (raw_dir / f"arm2b_{group_name}_{regime}_{seed}.json").write_text(json.dumps(res), encoding="utf-8")
    return res


def _dispatch(task):
    kind = task[0]
    if kind == "arm1a":
        return run_arm1a_task(task[1], task[2], pathlib.Path(task[3]))
    if kind == "arm1b":
        return run_arm1b_task(task[1], task[2], pathlib.Path(task[3]))
    if kind == "arm2a":
        return run_arm2a_task(task[1], task[2], task[3], pathlib.Path(task[4]))
    if kind == "arm2b":
        return run_arm2b_task(task[1], task[2], task[3], pathlib.Path(task[4]))
    raise ValueError(kind)


def run_all(pred_data: dict, raw_dir: pathlib.Path, workers: int) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for A in pred_data["monoids"]:
        for arch in ARM1A_ARCHS:
            if not (raw_dir / f"arm1a_{A['name']}_{arch}.json").exists():
                jobs.append(("arm1a", A, arch, str(raw_dir)))
    for A in pred_data["hmms"]:
        for arch in ARM1B_ARCHS:
            if not (raw_dir / f"arm1b_{A['name']}_{arch}.json").exists():
                jobs.append(("arm1b", A, arch, str(raw_dir)))
    for grp in ("Z3", "S3", "D4"):
        for mdl in ARM2A_MODELS:
            for sd in (4400, 4401):
                if not (raw_dir / f"arm2a_{grp}_{mdl}_{sd}.json").exists():
                    jobs.append(("arm2a", grp, mdl, sd, str(raw_dir)))
    for grp in ("S3", "D4"):
        for reg in ("B2_inf", "B3_inf", "B3_unif"):
            for sd in (4500, 4501):
                if not (raw_dir / f"arm2b_{grp}_{reg}_{sd}.json").exists():
                    jobs.append(("arm2b", grp, reg, sd, str(raw_dir)))

    print(f"Pending jobs: {len(jobs)} (workers={workers}, threads=1)", flush=True)
    if not jobs:
        return
    t0 = time.time()
    done = 0
    if workers <= 1:
        for j in jobs:
            r = _dispatch(j)
            done += 1
            _log_done(done, len(jobs), r)
    else:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(_dispatch, j) for j in jobs]
            for fut in as_completed(futs):
                r = fut.result()
                done += 1
                _log_done(done, len(jobs), r)
    print(f"All {done} runs finished in {time.time() - t0:.1f}s", flush=True)


def _log_done(done: int, total: int, r: dict) -> None:
    a = r["arm"]
    if a == "arm1a":
        s = r["scores"]
        print(f"[{done}/{total}] arm1a {r['name']} {r['arch']} fit={r['fit']:.3f} Xpr={s['X_primal_var']:.3f} Gsum={s['G_sum_heat']:.3f} Ggm={s['G_gm_heat']:.3f}", flush=True)
    elif a == "arm1b":
        ss, hs = r["state_scores"], r["hist_scores"]
        print(f"[{done}/{total}] arm1b {r['name']} {r['arch']} kl={r['kl_gap']:.4f} Xdu_h={hs['X_dual_var']:.3f} Gsum_h={hs['G_sum_heat']:.3f} Xdu_s={ss['X_dual_var']:.3f}", flush=True)
    elif a == "arm2a":
        print(f"[{done}/{total}] arm2a {r['group']} {r['model']} sd={r['seed']} bacc4={r['bacc_L4_heldout']:.3f} bacc5={r['bacc_L5_ood']:.3f} orb={r['anova_pen']['within_orbit_ratio']:.3f}", flush=True)
    elif a == "arm2b":
        print(f"[{done}/{total}] arm2b {r['group']} {r['regime']} sd={r['seed']} kl={r['kl_gap']:.4f} r2={r['belief_r2']:.3f} effr={r['eff_rank']:.2f} var={r['state_var_total']:.3f}", flush=True)


def analyse(pred_data: dict, raw_dir: pathlib.Path) -> dict:
    a1a = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("arm1a_*.json"))]
    a1b = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("arm1b_*.json"))]
    a2a = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("arm2a_*.json"))]
    a2b = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(raw_dir.glob("arm2b_*.json"))]
    assert len(a1a) == 48 and len(a1b) == 16 and len(a2a) == 24 and len(a2b) == 12, (
        f"Expected 48/16/24/12, got {len(a1a)}/{len(a1b)}/{len(a2a)}/{len(a2b)}"
    )

    # --- HVR.1: Primal Variational vs Heat-Sandwich on Monoids ---
    op_keys_1a = (
        "X_primal_var", "G_sum_heat", "G_gm_heat", "X_dual_var",
        "X_primal_var_best", "G_sum_heat_best", "G_gm_heat_best",
        "W_gm", "W_sum", "W_bal", "W_c", "W_o", "o",
    )
    a1a_summary = {}
    primal_beats_both = 0
    heat_beats_primal = 0
    for arch in ARM1A_ARCHS:
        rs = [r for r in a1a if r["arch"] == arch and r["fit"] >= 0.90]
        if len(rs) < 6:
            a1a_summary[arch] = {"n": len(rs), "underpowered": True}
            continue
        means = {k: float(np.mean([r["scores"][k] for r in rs])) for k in op_keys_1a}
        meds = {k: float(np.median([r["scores"][k] for r in rs])) for k in op_keys_1a}
        margin_m = means["X_primal_var"] - max(means["G_sum_heat"], means["G_gm_heat"])
        margin_med = meds["X_primal_var"] - max(meds["G_sum_heat"], meds["G_gm_heat"])
        if margin_m >= 0.01 and margin_med >= 0.01:
            primal_beats_both += 1
        elif means["X_primal_var"] < max(means["G_sum_heat"], means["G_gm_heat"]) and meds["X_primal_var"] < max(meds["G_sum_heat"], meds["G_gm_heat"]):
            heat_beats_primal += 1
        eps_means = {
            e: float(np.mean([r["eps_sensitivity"][e]["X_primal_var"] for r in rs]))
            for e in ("1e-06", "1e-04", "1e-02")
        }
        a1a_summary[arch] = {"n": len(rs), "mean_cos": means, "median_cos": meds, "eps_sensitivity_mean": eps_means}

    hvr1 = "HELD" if primal_beats_both >= 3 else ("BROKEN" if heat_beats_primal >= 3 else "NEITHER")

    # --- HVR.2: Dual Variational vs Heat-Sandwich on HMMs ---
    hmm_conv = [r for r in a1b if r["kl_gap"] <= 0.05]
    a1b_ops = ("X_dual_var", "X_primal_var", "G_sum_heat", "G_gm_heat", "W_bal_dual", "W_gm", "W_sum", "W_bal", "W_o")
    by_hmm_fam = {}
    for fam in ("cyclic_group_hmm", "nonrev_hmm", "all"):
        rs = [r for r in hmm_conv if (fam == "all" or r["family"] == fam)]
        by_hmm_fam[fam] = {
            "n": len(rs),
            "mean_kl_gap": float(np.mean([r["kl_gap"] for r in rs])) if rs else None,
            "mean_belief_r2": float(np.mean([r["belief_r2"] for r in rs])) if rs else None,
            "state_mean": {k: float(np.mean([r["state_scores"][k] for r in rs])) for k in a1b_ops} if rs else {},
            "hist_mean": {k: float(np.mean([r["hist_scores"][k] for r in rs])) for k in a1b_ops} if rs else {},
        }
    dual_wins_hmms = sum(
        1 for r in hmm_conv
        if r["hist_scores"]["X_dual_var"] > max(r["hist_scores"]["G_sum_heat"], r["hist_scores"]["G_gm_heat"], r["hist_scores"]["W_sum"])
        and r["state_scores"]["X_dual_var"] > max(r["state_scores"]["G_sum_heat"], r["state_scores"]["G_gm_heat"], r["state_scores"]["W_sum"])
    )
    heat_wins_hmms = sum(
        1 for r in hmm_conv
        if max(r["hist_scores"]["G_sum_heat"], r["hist_scores"]["G_gm_heat"]) > r["hist_scores"]["X_dual_var"]
        and max(r["state_scores"]["G_sum_heat"], r["state_scores"]["G_gm_heat"]) > r["state_scores"]["X_dual_var"]
    )
    # Also evaluate grouped by HMM instance (averaging across gru_mlp and vel_warmup)
    by_hmm_name = {}
    for hm in pred_data["hmms"]:
        hrs = [r for r in hmm_conv if r["name"] == hm["name"]]
        if hrs:
            by_hmm_name[hm["name"]] = {
                "dual_both": all(
                    r["hist_scores"]["X_dual_var"] > max(r["hist_scores"]["G_sum_heat"], r["hist_scores"]["G_gm_heat"], r["hist_scores"]["W_sum"])
                    and r["state_scores"]["X_dual_var"] > max(r["state_scores"]["G_sum_heat"], r["state_scores"]["G_gm_heat"], r["state_scores"]["W_sum"])
                    for r in hrs
                )
            }
    n_hmm_dual = sum(1 for v in by_hmm_name.values() if v["dual_both"])
    n_hmm_dual_runs = dual_wins_hmms
    hvr2 = (
        "HELD" if n_hmm_dual_runs >= 12
        else ("BROKEN" if heat_wins_hmms >= 12 else "NEITHER")
    )

    # --- HVR.3: Variational Causal Shift Under Interventions ---
    mon_by = {(r["name"], r["arch"]): r for r in a1a}
    causal_pairs = []
    for hm_mon in pred_data["monoids"]:
        base = mon_by[(hm_mon["name"], "rnn_mlp")]
        if base["fit"] < 0.90:
            continue
        Wc = np.array(hm_mon["Wc"], dtype=float)
        Wo = np.array(hm_mon["Wo"], dtype=float)
        Lkin = np.array(hm_mon["Lkin"], dtype=float)
        Pperp = np.array(hm_mon["Pperp"], dtype=float)
        o_gr = np.array(hm_mon["o"], dtype=float)
        ev = VariationalEvaluator(Wc, Wo, Lkin, Pperp, o_gr, eps_rel=EPS_DEFAULT)
        for iv in ("leaky_a025", "vel_warmup"):
            tgt = mon_by[(hm_mon["name"], iv)]
            if tgt["fit"] < 0.90:
                continue
            G_tgt = np.array(tgt["G_net"], dtype=float)
            lam_b = base["lams"]["X_primal_var"]
            lam_t = tgt["lams"]["X_primal_var"]
            c_at_t = cos_mat(G_tgt, ev.eval_op("X_primal_var", lam_t))
            c_at_b = cos_mat(G_tgt, ev.eval_op("X_primal_var", lam_b))
            causal_pairs.append({
                "name": hm_mon["name"],
                "arm": iv,
                "kin_drop": bool(tgt["kin_norm"] < base["kin_norm"] and lam_t > lam_b),
                "shift_var": bool(c_at_t > c_at_b),
                "delta_kin": float(tgt["kin_norm"] - base["kin_norm"]),
                "delta_cos_var": float(c_at_t - c_at_b),
            })
    # Also HMM causal shifts
    hmm_by = {(r["name"], r["arch"]): r for r in a1b}
    hmm_causal = []
    for hm in pred_data["hmms"]:
        rb = hmm_by[(hm["name"], "gru_mlp")]
        rt = hmm_by[(hm["name"], "vel_warmup")]
        if rb["kl_gap"] <= 0.05 and rt["kl_gap"] <= 0.05:
            ev_h = VariationalEvaluator(
                np.array(hm["Wc_obs"]), np.array(hm["Wo_obs"]), np.array(hm["Lkin"]),
                np.array(hm["Pperp"]), np.array(hm["Wo_obs"]), eps_rel=1e-5
            )
            Gt = np.array(rt["G_net_state"], dtype=float)
            c_t = cos_mat(Gt, ev_h.eval_op("X_dual_var", rt["lams"]["X_dual_var"]))
            c_b = cos_mat(Gt, ev_h.eval_op("X_dual_var", rb["lams"]["X_dual_var"]))
            hmm_causal.append({
                "name": hm["name"],
                "kin_drop": bool(rt["kin_norm"] < rb["kin_norm"] and rt["lams"]["X_dual_var"] > rb["lams"]["X_dual_var"]),
                "shift_var": bool(c_t > c_b),
                "delta_kin": float(rt["kin_norm"] - rb["kin_norm"]),
                "delta_cos_var": float(c_t - c_b),
            })
    all_causal = causal_pairs + hmm_causal
    n_kin = sum(1 for r in all_causal if r["kin_drop"])
    n_sh = sum(1 for r in all_causal if r["shift_var"])
    hvr3 = (
        "HELD" if (len(all_causal) >= 16 and n_kin >= 0.75 * len(all_causal) and n_sh >= 0.75 * len(all_causal))
        else ("BROKEN" if (n_kin <= 0.25 * len(all_causal) or n_sh <= 0.25 * len(all_causal)) else "NEITHER")
    )

    # --- HVR.4 & HVR.5: Matched-Capacity Gauge-Ring Showdown & Orbit Collapse ---
    a2a_tbl = {}
    for grp in ("Z3", "S3", "D4"):
        a2a_tbl[grp] = {}
        for mdl in ARM2A_MODELS:
            rs = [r for r in a2a if r["group"] == grp and r["model"] == mdl]
            a2a_tbl[grp][mdl] = {
                "n_params": rs[0]["n_params"],
                "bacc_L3_train": float(np.mean([r["bacc_L3_train"] for r in rs])),
                "bacc_L4_heldout": float(np.mean([r["bacc_L4_heldout"] for r in rs])),
                "bacc_L5_ood": float(np.mean([r["bacc_L5_ood"] for r in rs])),
                "acc_L4_heldout": float(np.mean([r["acc_L4_heldout"] for r in rs])),
                "acc_L5_ood": float(np.mean([r["acc_L5_ood"] for r in rs])),
                "ce_L4_heldout": float(np.mean([r["ce_L4_heldout"] for r in rs])),
                "collision_pair_sep": float(np.mean([r["collision_pair_sep"] for r in rs])) if rs[0]["collision_pair_sep"] is not None else None,
                "n_collision_pairs": int(rs[0]["n_collision_pairs"]),
                "orbit_collapse_raw": float(np.mean([r["anova_raw"]["within_orbit_ratio"] for r in rs])),
                "orbit_collapse_pen": float(np.mean([r["anova_pen"]["within_orbit_ratio"] for r in rs])),
                "base_frame_raw": float(np.mean([r["anova_raw"]["base_frame_within_class_ratio"] for r in rs])),
                "base_frame_pen": float(np.mean([r["anova_pen"]["base_frame_within_class_ratio"] for r in rs])),
            }

    c1 = (
        a2a_tbl["Z3"]["local_edge_mlp"]["bacc_L4_heldout"] <= 0.45
        and a2a_tbl["S3"]["local_edge_mlp"]["bacc_L4_heldout"] <= 0.45
        and a2a_tbl["D4"]["local_edge_mlp"]["bacc_L4_heldout"] <= 0.35
    )
    c2 = (
        a2a_tbl["Z3"]["multiset_deepsets"]["bacc_L4_heldout"] >= 0.90
        and a2a_tbl["S3"]["multiset_deepsets"]["collision_pair_sep"] == 0.0
        and a2a_tbl["D4"]["multiset_deepsets"]["collision_pair_sep"] == 0.0
        and a2a_tbl["S3"]["ordered_gru"]["collision_pair_sep"] >= 0.70
        and a2a_tbl["D4"]["ordered_gru"]["collision_pair_sep"] >= 0.70
        and (a2a_tbl["S3"]["ordered_gru"]["bacc_L4_heldout"] > a2a_tbl["S3"]["multiset_deepsets"]["bacc_L4_heldout"] + 0.05)
        and (a2a_tbl["D4"]["ordered_gru"]["bacc_L4_heldout"] > a2a_tbl["D4"]["multiset_deepsets"]["bacc_L4_heldout"] + 0.05)
    )
    c3 = (
        all(a2a_tbl[g]["ordered_gru"]["bacc_L4_heldout"] >= 0.85 for g in ("Z3", "S3", "D4"))
        and all(a2a_tbl[g]["ordered_gru"]["bacc_L5_ood"] >= 0.80 for g in ("Z3", "S3", "D4"))
    )
    ds_matches_gru = (
        (a2a_tbl["S3"]["multiset_deepsets"]["collision_pair_sep"] > 0.0)
        or (a2a_tbl["D4"]["multiset_deepsets"]["collision_pair_sep"] > 0.0)
        or (a2a_tbl["S3"]["ordered_gru"]["bacc_L4_heldout"] <= a2a_tbl["S3"]["multiset_deepsets"]["bacc_L4_heldout"] + 0.02
            and a2a_tbl["D4"]["ordered_gru"]["bacc_L4_heldout"] <= a2a_tbl["D4"]["multiset_deepsets"]["bacc_L4_heldout"] + 0.02)
    )
    if c1 and c2 and c3:
        hvr4 = "HELD"
    elif ds_matches_gru or a2a_tbl["Z3"]["ordered_gru"]["bacc_L4_heldout"] < 0.85:
        hvr4 = "BROKEN"
    else:
        hvr4 = "NEITHER"

    s3_gru_orb = a2a_tbl["S3"]["ordered_gru"]["orbit_collapse_pen"]
    d4_gru_orb = a2a_tbl["D4"]["ordered_gru"]["orbit_collapse_pen"]
    s3_ge_orb = a2a_tbl["S3"]["gauge_equivariant_bilinear"]["orbit_collapse_pen"]
    d4_ge_orb = a2a_tbl["D4"]["gauge_equivariant_bilinear"]["orbit_collapse_pen"]
    if min(s3_gru_orb, s3_ge_orb) <= 0.15 and min(d4_gru_orb, d4_ge_orb) <= 0.15 and s3_gru_orb <= 0.25 and d4_gru_orb <= 0.25:
        hvr5 = "HELD"
    elif s3_gru_orb > 0.50 and d4_gru_orb > 0.50:
        hvr5 = "BROKEN"
    else:
        hvr5 = "NEITHER"

    # --- HVR.6: Dynamic POMDP Phase Transition ---
    a2b_tbl = {}
    for grp in ("S3", "D4"):
        a2b_tbl[grp] = {}
        for reg in ("B2_inf", "B3_inf", "B3_unif"):
            rs = [r for r in a2b if r["group"] == grp and r["regime"] == reg]
            a2b_tbl[grp][reg] = {
                "kl_gap": float(np.mean([r["kl_gap"] for r in rs])),
                "belief_r2": float(np.mean([r["belief_r2"] for r in rs])),
                "pca95_dim": float(np.mean([r["pca95_dim"] for r in rs])),
                "eff_rank": float(np.mean([r["eff_rank"] for r in rs])),
                "state_var_total": float(np.mean([r["state_var_total"] for r in rs])),
            }
        v_full = max(a2b_tbl[grp]["B3_inf"]["state_var_total"], 1e-12)
        for reg in ("B2_inf", "B3_inf", "B3_unif"):
            a2b_tbl[grp][reg]["var_ratio_vs_full"] = float(a2b_tbl[grp][reg]["state_var_total"] / v_full)

    full_ok = all(
        a2b_tbl[g]["B3_inf"]["kl_gap"] <= 0.03 and a2b_tbl[g]["B3_inf"]["belief_r2"] >= 0.85
        for g in ("S3", "D4")
    )
    unobs_collapse = all(
        a2b_tbl[g][reg]["kl_gap"] <= 0.03
        and (a2b_tbl[g][reg]["var_ratio_vs_full"] <= 0.25 or a2b_tbl[g][reg]["eff_rank"] <= 0.5 * a2b_tbl[g]["B3_inf"]["eff_rank"] or a2b_tbl[g][reg]["belief_r2"] <= 0.30)
        for g in ("S3", "D4")
        for reg in ("B2_inf", "B3_unif")
    )
    if full_ok and unobs_collapse:
        hvr6 = "HELD"
    elif any(a2b_tbl[g]["B3_inf"]["belief_r2"] < 0.60 for g in ("S3", "D4")):
        hvr6 = "BROKEN"
    else:
        hvr6 = "NEITHER"

    out = {
        "verdicts": {
            "HVR.1": hvr1,
            "HVR.2": hvr2,
            "HVR.3": hvr3,
            "HVR.4": hvr4,
            "HVR.5": hvr5,
            "HVR.6": hvr6,
        },
        "spike26_exact_check": pred_data["spike26_exact_check"],
        "multiset_ceilings": pred_data["multiset_ceilings"],
        "arm1a_monoids": {
            "summary": a1a_summary,
            "monotonicity_checks": [
                {"name": m["name"], "raw_mono": m["raw_mono"], "norm_mono": m["norm_mono"], "comm_ratio": m["comm_ratio"]}
                for m in pred_data["monoids"]
            ],
        },
        "arm1b_hmms": {
            "summary": by_hmm_fam,
            "n_dual_wins_runs": n_hmm_dual_runs,
            "n_hmm_both_archs_dual": n_hmm_dual,
            "hankel_realization_max_err": float(max(h["hankel_realization_err"] for h in pred_data["hmms"])),
        },
        "arm1_causal_shifts": {
            "n_pairs": len(all_causal),
            "n_kin_drop": n_kin,
            "n_shift_var": n_sh,
            "monoid_pairs": causal_pairs,
            "hmm_pairs": hmm_causal,
        },
        "arm2a_gauge_ring": a2a_tbl,
        "arm2b_pomdp": a2b_tbl,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=str, default=str(RESULTS / "master_principle_variational_raw"))
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--skip-run", action="store_true")
    args = parser.parse_args()

    raw_dir = pathlib.Path(args.raw_dir)
    if PRED.exists():
        pred_data = json.loads(PRED.read_text(encoding="utf-8"))
    else:
        pred_data = predict()
    if not args.skip_run:
        run_all(pred_data, raw_dir, args.workers)
    summary = analyse(pred_data, raw_dir)
    print("FINAL VERDICTS:", json.dumps(summary["verdicts"], indent=2))


if __name__ == "__main__":
    main()
