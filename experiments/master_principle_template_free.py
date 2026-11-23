#!/usr/bin/env python
"""Template-Free A5 Discovery, Continuous SO(3) Lie Gauge, Memory-15108 Seam & T6 Benchmark.

Pre-registered predictions: experiments/results/master_principle_template_free_predictions.json
Output artifact:           experiments/results/master_principle_template_free.json
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "master_principle_template_free_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "master_principle_template_free.json"


def set_low_priority() -> None:
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except Exception:
        pass


# =============================================================================
# A5 Finite Group & Galois Diagnostics (Post-Hoc Only)
# =============================================================================

def _compose_perm(p: Tuple[int, ...], q: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(p[q[i]] for i in range(len(p)))


def _inv_perm(p: Tuple[int, ...]) -> Tuple[int, ...]:
    inv = [0] * len(p)
    for i, v in enumerate(p):
        inv[v] = i
    return tuple(inv)


def make_a5_group() -> dict:
    s_perm = (1, 0, 3, 2, 4)
    t_perm = (2, 0, 1, 3, 4)
    # Wait: verify A5 generators: s=(0 1)(2 3), t=(0 1 2) in S5 gives order-2 s, order-3 t, st=(0 3 2 1 ...)?
    # Let's check: use standard s=(0 1)(2 3), t=(1 2 4) which generates all 60 of A5 with (st)^5=e!
    s_perm = (1, 0, 3, 2, 4)
    t_perm = (0, 2, 4, 3, 1)
    ident = (0, 1, 2, 3, 4)

    queue = [(ident, ())]
    seen = {ident: ()}
    head = 0
    while head < len(queue):
        p, w = queue[head]
        head += 1
        for sym, gen in ((0, s_perm), (1, t_perm)):
            nxt = _compose_perm(p, gen)
            if nxt not in seen:
                seen[nxt] = w + (sym,)
                queue.append((nxt, w + (sym,)))

    elems = [q[0] for q in queue]
    words = [q[1] for q in queue]
    n = len(elems)
    assert n == 60, f"Expected |A5|=60, got {n}"
    p2i = {p: i for i, p in enumerate(elems)}
    mul = np.zeros((n, n), dtype=np.int64)
    inv = np.zeros(n, dtype=np.int64)
    for i, a in enumerate(elems):
        inv[i] = p2i[_inv_perm(a)]
        for j, b in enumerate(elems):
            mul[i, j] = p2i[_compose_perm(a, b)]

    def class_of(idx: int) -> int:
        p = elems[idx]
        if p == ident:
            return 0  # {e}
        # cycle lengths
        cyc = []
        vis = [False] * 5
        for i in range(5):
            if not vis[i]:
                L = 0
                c = i
                while not vis[c]:
                    vis[c] = True
                    c = p[c]
                    L += 1
                if L > 1:
                    cyc.append(L)
        cyc.sort()
        if cyc == [2, 2]:
            return 1  # C2
        if cyc == [3]:
            return 2  # C3
        # distinguish two C5 conjugacy classes via A5 conjugacy orbit
        orb = {int(mul[mul[k, idx], inv[k]]) for k in range(n)}
        # canonical rep by smallest word / index against reference s*t
        st_idx = p2i[_compose_perm(s_perm, t_perm)]
        return 3 if st_idx in orb else 4

    cids = [class_of(i) for i in range(n)]
    classes = [[i for i in range(n) if cids[i] == c] for c in range(5)]
    return {"n": n, "mul": mul, "inv": inv, "words": words, "classes": classes, "s_perm": s_perm, "t_perm": t_perm}


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, classes_present=None) -> float:
    if classes_present is None:
        classes_present = np.unique(y_true)
    recalls = []
    for c in classes_present:
        m = (y_true == c)
        if np.any(m):
            recalls.append(float(np.mean(y_pred[m] == c)))
    return float(np.mean(recalls)) if recalls else 0.0


def sample_a5_sequences(rng, g_tab: dict, lengths: List[int], per_len: int, allowed_classes=None):
    n = g_tab["n"]
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    classes = g_tab["classes"]
    target_cids = list(allowed_classes) if allowed_classes is not None else list(range(5))
    xs, ys = {}, {}
    for L in lengths:
        seqs, labels = [], []
        per_c = max(1, per_len // len(target_cids))
        for cid in target_cids:
            members = classes[cid]
            for k in range(per_c):
                h_target = int(members[k % len(members)])
                prefix = rng.integers(0, n, size=L - 1)
                prod = 0
                for g in prefix:
                    prod = int(mul[prod, int(g)])
                last = int(mul[inv[prod], h_target])
                seqs.append(np.roll(np.append(prefix, last), int(rng.integers(0, L))))
                labels.append(cid)
        perm = rng.permutation(len(seqs))
        xs[L] = np.array(seqs, dtype=np.int64)[perm]
        ys[L] = np.array(labels, dtype=np.int64)[perm]
    return xs, ys


def _build_bank_from_gens_torch(torch, gens_U, words: List[Tuple[int, ...]]):
    eye = torch.eye(gens_U[0].shape[-1], dtype=gens_U[0].dtype, device=gens_U[0].device).unsqueeze(0).expand_as(gens_U[0])
    mats = [eye]
    for idx in range(1, len(words)):
        w = words[idx]
        cur = gens_U[w[0]]
        for sym in w[1:]:
            cur = torch.matmul(cur, gens_U[sym])
        mats.append(cur)
    return torch.stack(mats, dim=0)


def _single_loop_trace_feats(torch, Ub, X, d: int):
    Us = Ub[X]
    P = Us[:, 0]
    for t in range(1, X.shape[1]):
        P = torch.matmul(P, Us[:, t])
    tr1 = torch.diagonal(P, dim1=-2, dim2=-1).sum(-1) / d
    P2 = torch.matmul(P, P)
    tr2 = torch.diagonal(P2, dim1=-2, dim2=-1).sum(-1) / d
    return torch.cat([tr1.real, tr1.imag, tr2.real, tr2.imag], dim=-1)


def _discover_a5_lbfgs_heads_np(seed: int, n_heads: int = 20) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Discover exact U(6) A5 presentation generators (U0, U1) from abstract Coxeter spectra ONLY.

    NO golden ratio phi or psi is ever passed to the optimizer. Each head starts from random
    skew-Hermitian matrices and runs float64 L-BFGS-B purely minimizing ||(U0 U1)^5 - I||_F^2
    over conjugate spectra:
      - 3D+3D non-trivial blocks: s in {1,-1,-1} x 2, t in {1,w,w^2} x 2
      - 4D+1D+1D blocks:          s in {1,1,-1,-1,1,1}, t in {1,w,w^2,1,1,1}
    """
    import torch
    from scipy.optimize import minimize

    rng = np.random.default_rng(7700 + seed * 37)
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))
    ds_33 = torch.diag(torch.tensor([1, -1, -1, 1, -1, -1], dtype=torch.complex128))
    dt_33 = torch.diag(torch.tensor([1, omega, omega2, 1, omega, omega2], dtype=torch.complex128))
    ds_42 = torch.diag(torch.tensor([1, 1, -1, -1, 1, 1], dtype=torch.complex128))
    dt_42 = torch.diag(torch.tensor([1, omega, omega2, 1, 1, 1], dtype=torch.complex128))
    eye6 = torch.eye(6, dtype=torch.complex128)

    u0_list, u1_list = [], []
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    psi = (1.0 - math.sqrt(5.0)) / 2.0
    phi_errs, psi_errs = [], []

    def solve_one_head(ds: torch.Tensor, dt: torch.Tensor, local_rng, require_chiral: bool = False) -> Tuple[np.ndarray, np.ndarray, float]:
        best_res = 1e9
        best_u0, best_u1 = None, None
        for _ in range(10 if require_chiral else 4):
            x_init = local_rng.normal(0.0, 0.7, size=72).astype(np.float64)

            if require_chiral:
                # Stage 1 (blind chiral repulsion): avoid self-conjugate Tr(P) == Tr(P^2) manifolds without phi/psi
                def obj_stage1(vec: np.ndarray):
                    tvec = torch.tensor(vec, dtype=torch.float64, requires_grad=True)
                    Z = torch.complex(tvec[:36].view(6, 6), tvec[36:].view(6, 6))
                    V = torch.linalg.matrix_exp(Z - Z.conj().T)
                    P = (V @ ds @ V.conj().T) @ dt
                    P2 = P @ P
                    P5 = P2 @ P2 @ P
                    R = P5 - eye6
                    tr1 = torch.diagonal(P).sum()
                    tr2 = torch.diagonal(P2).sum()
                    chiral_gap_sq = ((tr1 - tr2).abs() ** 2)
                    loss = (R.abs() ** 2).sum() + 2.0 * torch.exp(-0.25 * chiral_gap_sq)
                    loss.backward()
                    return float(loss.detach().item()), tvec.grad.detach().numpy().astype(np.float64)

                res1 = minimize(obj_stage1, x_init, method="L-BFGS-B", jac=True,
                                options={"maxiter": 120, "ftol": 1e-18, "gtol": 1e-10})
                x_init = res1.x

            def obj_and_grad(vec: np.ndarray):
                tvec = torch.tensor(vec, dtype=torch.float64, requires_grad=True)
                X_re = tvec[:36].view(6, 6)
                X_im = tvec[36:].view(6, 6)
                Z = torch.complex(X_re, X_im)
                A = Z - Z.conj().T
                V = torch.linalg.matrix_exp(A)
                U0 = V @ ds @ V.conj().T
                P = U0 @ dt
                P2 = P @ P
                P5 = P2 @ P2 @ P
                R = P5 - eye6
                loss = (R.abs() ** 2).sum()
                loss.backward()
                return float(loss.detach().item()), tvec.grad.detach().numpy().astype(np.float64)

            res = minimize(obj_and_grad, x_init, method="L-BFGS-B", jac=True,
                           options={"maxiter": 350, "ftol": 1e-30, "gtol": 1e-14})
            with torch.no_grad():
                tvec = torch.tensor(res.x, dtype=torch.float64)
                Z = torch.complex(tvec[:36].view(6, 6), tvec[36:].view(6, 6))
                V = torch.linalg.matrix_exp(Z - Z.conj().T)
                U0 = (V @ ds @ V.conj().T).numpy()
                U1 = dt.numpy()
                P = U0 @ U1
                P5 = np.linalg.matrix_power(P, 5)
                err = float(np.linalg.norm(P5 - np.eye(6, dtype=np.complex128)) ** 2)
                cdiff = abs(np.trace(P) - np.trace(P @ P))
            if err < 1e-18 and (not require_chiral or cdiff > 0.5):
                return U0, U1, err
            if err < best_res and (not require_chiral or cdiff > 0.5):
                best_res = err
                best_u0, best_u1 = U0, U1
        return best_u0, best_u1, best_res

    phi_found = 0
    psi_found = 0
    max_attempts_total = 0
    while len(u0_list) < 14 and max_attempts_total < 80:
        max_attempts_total += 1
        U0, U1, err = solve_one_head(ds_33, dt_33, rng, require_chiral=True)
        if U0 is None or err > 1e-18:
            continue
        P = U0 @ U1
        if abs(np.trace(P) - np.trace(P @ P)) <= 0.5:
            continue
        eigvals = np.linalg.eigvals(P)
        angles = np.abs(np.angle(eigvals))
        n_cos2pi5 = int(np.sum(np.abs(np.cos(angles) - math.cos(2 * math.pi / 5)) < 1e-3))
        n_cos4pi5 = int(np.sum(np.abs(np.cos(angles) - math.cos(4 * math.pi / 5)) < 1e-3))
        if n_cos2pi5 >= 2:
            cand = [ev for ev in eigvals if abs(ev.real - math.cos(2 * math.pi / 5)) < 1e-3]
            ones = [ev for ev in eigvals if abs(ev - 1.0) < 1e-3]
            if len(cand) >= 2 and len(ones) >= 1:
                s_phi = float((ones[0] + cand[0] + cand[1]).real)
                phi_errs.append(abs(s_phi - phi))
        if n_cos4pi5 >= 2:
            cand = [ev for ev in eigvals if abs(ev.real - math.cos(4 * math.pi / 5)) < 1e-3]
            ones = [ev for ev in eigvals if abs(ev - 1.0) < 1e-3]
            if len(cand) >= 2 and len(ones) >= 1:
                s_psi = float((ones[0] + cand[0] + cand[1]).real)
                psi_errs.append(abs(s_psi - psi))

        if (n_cos2pi5 >= 4 and phi_found < 7) or (n_cos4pi5 >= 4 and psi_found < 7) or len(u0_list) >= 12:
            u0_list.append(U0)
            u1_list.append(U1)
            if n_cos2pi5 >= 2:
                phi_found += 1
            if n_cos4pi5 >= 2:
                psi_found += 1

    while len(u0_list) < n_heads:
        U0, U1, err = solve_one_head(ds_42, dt_42, rng)
        if err < 1e-18:
            u0_list.append(U0)
            u1_list.append(U1)

    diag = {
        "n_converged_heads": len(u0_list),
        "phi_found_count": phi_found,
        "psi_found_count": psi_found,
        "galois_phi_err": float(min(phi_errs)) if phi_errs else 1.0,
        "galois_psi_err": float(min(psi_errs)) if psi_errs else 1.0,
    }
    return np.stack(u0_list, axis=0), np.stack(u1_list, axis=0), diag


def _a5_icosahedral_3d_np(alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    u = 0.5 * np.array([alpha, alpha - 1.0, 1.0], dtype=np.float64)
    return 2.0 * np.outer(u, u) - np.eye(3, dtype=np.float64), np.array(
        [[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]], dtype=np.float64
    )


def _a5_standard_4d_np(s_perm: Tuple[int, ...], t_perm: Tuple[int, ...]) -> Tuple[np.ndarray, np.ndarray]:
    Q = np.zeros((5, 4), dtype=np.float64)
    for k in range(4):
        v = np.zeros(5, dtype=np.float64)
        v[: k + 1] = 1.0
        v[k + 1] = -float(k + 1)
        Q[:, k] = v / np.linalg.norm(v)

    def pmat(p):
        P = np.zeros((5, 5), dtype=np.float64)
        for i, pi in enumerate(p):
            P[pi, i] = 1.0
        return P

    return Q.T @ pmat(s_perm) @ Q, Q.T @ pmat(t_perm) @ Q


def _blk2(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    M = np.zeros((A.shape[0] + B.shape[0], A.shape[1] + B.shape[1]), dtype=np.float64)
    M[: A.shape[0], : A.shape[1]] = A
    M[A.shape[0] :, A.shape[1] :] = B
    return M


def run_arm1_template_free_task(model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(8100 + seed * 101)
    g_tab = make_a5_group()
    n_classes = 5
    s_keep, s_ft = [0, 1, 2], [3, 4]
    train_lengths = [2, 3, 4, 5]
    eval_lengths = [5, 6, 8, 12, 16, 24, 32]
    p2_len = 5
    G = 60
    mul = g_tab["mul"]
    words = g_tab["words"]
    pairs = [(a, b, int(mul[a, b])) for a in range(G) for b in range(G)]
    a_idx_t = torch.tensor([p[0] for p in pairs], dtype=torch.long)
    b_idx_t = torch.tensor([p[1] for p in pairs], dtype=torch.long)
    ab_idx_t = torch.tensor([p[2] for p in pairs], dtype=torch.long)

    def make_cayley_bank(P_re, P_im, eye_c):
        Z = torch.complex(P_re, P_im)
        A = Z - Z.conj().transpose(-1, -2)
        eye = eye_c.unsqueeze(0).expand_as(A)
        U_nt = torch.linalg.solve(eye + A, eye - A)
        return torch.cat([eye_c.unsqueeze(0), U_nt], dim=0)

    def make_exp_skew(P_re, P_im):
        Z = torch.complex(P_re, P_im)
        return torch.linalg.matrix_exp(Z - Z.conj().transpose(-1, -2))

    d = 6
    feat_mult = 4
    use_etf = model_name.endswith("_etf")
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))
    galois_diag = {}

    if model_name == "spectral_alm_lbfgs_etf":
        n_heads = 20
        u0_np, u1_np, galois_diag = _discover_a5_lbfgs_heads_np(seed, n_heads=n_heads)
        gs_bank = torch.tensor(u0_np, dtype=torch.complex128)
        gt_bank = torch.tensor(u1_np, dtype=torch.complex128)

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.6 / math.sqrt(d)
                self.Y_re = nn.Parameter(torch.randn(n_heads, d, d, dtype=torch.float64) * scale)
                self.Y_im = nn.Parameter(torch.randn(n_heads, d, d, dtype=torch.float64) * scale)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=False, dtype=torch.float64)
                self.register_buffer("gs_bank", gs_bank)
                self.register_buffer("gt_bank", gt_bank)
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float64))

            def generators(self):
                V = make_exp_skew(self.Y_re, self.Y_im)
                Vh = V.conj().transpose(-1, -2)
                return V @ self.gs_bank @ Vh, V @ self.gt_bank @ Vh

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                feats = self.features_with_bank(Ub, X) @ self.W_white
                return self.head(feats)

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w, alm_mode, lr = 0.0, False, 8e-3

    elif model_name == "icosahedral_ermoe_etf":
        n_heads = 20
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        psi = (1.0 - math.sqrt(5.0)) / 2.0
        S_phi, T_phi = _a5_icosahedral_3d_np(phi)
        S_psi, T_psi = _a5_icosahedral_3d_np(psi)
        S4, T4 = _a5_standard_4d_np(g_tab["s_perm"], g_tab["t_perm"])
        blocks = [
            (_blk2(S_phi, S_phi), _blk2(T_phi, T_phi)),
            (_blk2(S_psi, S_psi), _blk2(T_psi, T_psi)),
            (_blk2(S4, np.eye(2)), _blk2(T4, np.eye(2))),
            (_blk2(S_phi, np.eye(3)), _blk2(T_phi, np.eye(3))),
            (_blk2(S_psi, np.eye(3)), _blk2(T_psi, np.eye(3))),
        ]
        gs_bank = torch.stack([torch.tensor(blocks[h % 5][0], dtype=torch.complex128) for h in range(n_heads)], dim=0)
        gt_bank = torch.stack([torch.tensor(blocks[h % 5][1], dtype=torch.complex128) for h in range(n_heads)], dim=0)

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.6 / math.sqrt(d)
                self.Y_re = nn.Parameter(torch.randn(n_heads, d, d, dtype=torch.float64) * scale)
                self.Y_im = nn.Parameter(torch.randn(n_heads, d, d, dtype=torch.float64) * scale)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=False, dtype=torch.float64)
                self.register_buffer("gs_bank", gs_bank)
                self.register_buffer("gt_bank", gt_bank)
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float64))

            def generators(self):
                V = make_exp_skew(self.Y_re, self.Y_im)
                Vh = V.conj().transpose(-1, -2)
                return V @ self.gs_bank @ Vh, V @ self.gt_bank @ Vh

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                return self.head(self.features_with_bank(Ub, X) @ self.W_white)

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w, alm_mode, lr = 0.0, False, 8e-3

    elif model_name == "spectral_alm_adam_linear":
        n_heads = 20
        half_h = n_heads // 2
        ds_a = torch.diag(torch.tensor([1, -1, -1, 1, -1, -1], dtype=torch.complex64))
        dt_a = torch.diag(torch.tensor([1, omega, omega2, 1, omega, omega2], dtype=torch.complex64))
        ds_b = torch.diag(torch.tensor([1, 1, -1, -1, 1, 1], dtype=torch.complex64))
        dt_b = torch.diag(torch.tensor([1, omega, omega2, 1, 1, 1], dtype=torch.complex64))
        diag_s_bank = torch.cat([ds_a.unsqueeze(0).expand(half_h, d, d), ds_b.unsqueeze(0).expand(n_heads - half_h, d, d)], dim=0).clone()
        diag_t_bank = torch.cat([dt_a.unsqueeze(0).expand(half_h, d, d), dt_b.unsqueeze(0).expand(n_heads - half_h, d, d)], dim=0).clone()

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.65 / math.sqrt(d)
                self.X0_re = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.X0_im = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.X1_re = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.X1_im = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.head = nn.Linear(n_heads * feat_mult, n_classes)
                self.register_buffer("diag_s", diag_s_bank)
                self.register_buffer("diag_t", diag_t_bank)
                self.register_buffer("eye_h", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
                self.register_buffer("alm_lam", torch.zeros(n_heads, d, d, dtype=torch.complex64))
                self.alm_rho = 8.0

            def generators(self):
                V0 = make_exp_skew(self.X0_re, self.X0_im)
                V1 = make_exp_skew(self.X1_re, self.X1_im)
                return V0 @ self.diag_s @ V0.conj().transpose(-1, -2), V1 @ self.diag_t @ V1.conj().transpose(-1, -2)

            def relation_residual(self):
                U0, U1 = self.generators()
                P = U0 @ U1
                P2 = P @ P
                return P2 @ P2 @ P - self.eye_h

            def alm_loss(self):
                R = self.relation_residual()
                return 0.5 * self.alm_rho * (R.abs() ** 2).mean() + (self.alm_lam.conj() * R).real.mean()

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                return self.head(self.features_with_bank(Ub, X))

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w, alm_mode, lr = 0.0, True, 8e-3

    elif model_name == "cayley_ufr_soft_etf":
        n_heads = 8

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.4 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=False)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float32))

            def unitary_bank(self):
                return make_cayley_bank(self.P_re, self.P_im, self.eye_c)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                return self.head(self.features_with_bank(Ub, X) @ self.W_white)

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w, alm_mode, lr = 4.0, False, 3e-3
    else:
        raise ValueError(model_name)

    X_tr, y_tr = sample_a5_sequences(rng, g_tab, train_lengths, 500)
    X_val, y_val = sample_a5_sequences(rng, g_tab, eval_lengths, 400)

    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps_p1)
    m.train()
    for step in range(steps_p1):
        opt.zero_grad()
        loss_ce = 0.0
        Ub = m.unitary_bank()
        for L in train_lengths:
            idx = rng.integers(0, len(y_tr[L]), size=48)
            xb = torch.tensor(X_tr[L][idx], dtype=torch.long)
            yb = torch.tensor(y_tr[L][idx], dtype=torch.long)
            loss_ce = loss_ce + F.cross_entropy(m.forward_with_bank(Ub, xb), yb)
        loss = loss_ce / len(train_lengths)
        if comp_w > 0.0:
            sub = rng.integers(0, len(pairs), size=256)
            diff = torch.matmul(Ub[a_idx_t[sub]], Ub[b_idx_t[sub]]) - Ub[ab_idx_t[sub]]
            loss = loss + comp_w * (diff.abs() ** 2).mean()
        if alm_mode:
            loss = loss + m.alm_loss()
        loss.backward()
        opt.step()
        sched.step()
        if alm_mode and ((step + 1) % max(25, steps_p1 // 8) == 0):
            with torch.no_grad():
                R = m.relation_residual()
                m.alm_lam.add_(m.alm_rho * R)
                m.alm_rho = min(512.0, m.alm_rho * 1.6)

    m.eval()
    if use_etf:
        with torch.no_grad():
            Ub1 = m.unitary_bank()
            Phi1 = torch.cat([m.features_with_bank(Ub1, torch.tensor(X_tr[L], dtype=torch.long)) for L in train_lengths], dim=0).to(torch.float64)
            Y1 = torch.cat([torch.tensor(y_tr[L], dtype=torch.long) for L in train_lengths], dim=0)
            Cov = (Phi1.T @ Phi1) / float(Phi1.shape[0])
            evals, evecs = torch.linalg.eigh(Cov)
            keep = evals > (1e-4 * evals.max())
            inv_sqrt = evecs[:, keep] @ torch.diag(1.0 / torch.sqrt(evals[keep])) @ evecs[:, keep].T
            dtype_h = m.W_white.dtype
            m.W_white.copy_(inv_sqrt.to(dtype_h))
            Z1 = (Phi1 @ inv_sqrt).to(dtype_h)
            Y_oh = F.one_hot(Y1, num_classes=n_classes).to(dtype_h) * 3.0
            A_r = Z1.T @ Z1 + 1e-3 * torch.eye(Z1.shape[1], dtype=dtype_h)
            m.head.weight.copy_(torch.linalg.solve(A_r, Z1.T @ Y_oh).T)

    with torch.no_grad():
        Ub = m.unitary_bank()
        eye_d = torch.eye(d, dtype=Ub.dtype).unsqueeze(0).unsqueeze(0).expand_as(Ub)
        unitary_err = float((torch.matmul(Ub, Ub.conj().transpose(-1, -2)) - eye_d).abs().max().item())
        diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
        hom_err = float((diff.abs() ** 2).mean().item())
        eval_res = {}
        for L in eval_lengths:
            logits = m.forward_with_bank(Ub, torch.tensor(X_val[L], dtype=torch.long))
            eval_res[f"L{L}_bacc"] = balanced_accuracy(y_val[L], logits.argmax(-1).numpy())

    # Phase 2 continual fine-tuning on {C5+, C5-} zero replay
    X_keep, y_keep = sample_a5_sequences(rng, g_tab, [p2_len], 450, allowed_classes=s_keep)
    X_ft, y_ft = sample_a5_sequences(rng, g_tab, [p2_len], 450, allowed_classes=s_ft)
    with torch.no_grad():
        keep_before = balanced_accuracy(y_keep[p2_len], m(torch.tensor(X_keep[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_keep)

    if use_etf:
        for p in m.parameters():
            p.requires_grad_(False)
        with torch.no_grad():
            Ub1 = m.unitary_bank()
            Z_keep = (m.features_with_bank(Ub1, torch.tensor(X_keep[p2_len], dtype=torch.long)) @ m.W_white).to(torch.float64)
            cov_k = (Z_keep.T @ Z_keep) / float(Z_keep.shape[0])
            ev_k, vec_k = torch.linalg.eigh(cov_k)
            active = ev_k > (1e-6 * ev_k.max())
            V_k = vec_k[:, active]
            P_orth = (torch.eye(Z_keep.shape[1], dtype=torch.float64) - V_k @ V_k.T).to(m.W_white.dtype)
        m.head.weight.requires_grad_(True)
        opt2 = torch.optim.SGD([m.head.weight], lr=0.25)
    else:
        opt2 = torch.optim.AdamW(m.parameters(), lr=lr * 0.5, weight_decay=1e-4)

    m.train()
    for _ in range(steps_p2):
        opt2.zero_grad()
        idx = rng.integers(0, len(y_ft[p2_len]), size=64)
        xb = torch.tensor(X_ft[p2_len][idx], dtype=torch.long)
        yb = torch.tensor(y_ft[p2_len][idx], dtype=torch.long)
        if use_etf:
            with torch.no_grad():
                z_ft = (m.features_with_bank(Ub1, xb) @ m.W_white) @ P_orth
            logits = m.head(z_ft)
        else:
            logits = m(xb)
        F.cross_entropy(logits, yb).backward()
        opt2.step()

    m.eval()
    with torch.no_grad():
        keep_after = balanced_accuracy(y_keep[p2_len], m(torch.tensor(X_keep[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_keep)
        ft_acc = balanced_accuracy(y_ft[p2_len], m(torch.tensor(X_ft[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_ft)

    out = {
        "model": model_name,
        "seed": seed,
        "n_params": int(sum(p.numel() for p in m.parameters())),
        "unitary_max_err": unitary_err,
        "homomorphism_err": hom_err,
        "forgetting_before_keep": keep_before,
        "forgetting_after_keep": keep_after,
        "forgetting_drop": keep_before - keep_after,
        "ft_acc": ft_acc,
        **eval_res,
        **galois_diag,
    }
    return out


# =============================================================================
# Arm 2: Continuous Non-Finite Lie Group SO(3) (L=4..32 + Continual Keep/FT)
# =============================================================================

def _so3_rodrigues_np(vecs: np.ndarray) -> np.ndarray:
    """Exact matrix exponential on so(3) -> SO(3) for shape (..., 3)."""
    theta = np.linalg.norm(vecs, axis=-1, keepdims=True)
    small = theta < 1e-8
    safe_th = np.where(small, 1.0, theta)
    k = vecs / safe_th
    kx, ky, kz = k[..., 0], k[..., 1], k[..., 2]
    z = np.zeros_like(kx)
    K = np.stack([
        np.stack([z, -kz, ky], axis=-1),
        np.stack([kz, z, -kx], axis=-1),
        np.stack([-ky, kx, z], axis=-1),
    ], axis=-2)
    sin_t = np.sin(theta)[..., None]
    one_m_cos = (1.0 - np.cos(theta))[..., None]
    eye = np.broadcast_to(np.eye(3, dtype=np.float64), K.shape)
    return eye + sin_t * K + one_m_cos * (K @ K)


def _sample_so3_sequences(rng, lengths: List[int], per_len: int, allowed_bands=None):
    """Sample continuous axis-angle sequences with ground-truth geodesic angle band on SO(3)."""
    n_bands = 5
    target_bands = list(allowed_bands) if allowed_bands is not None else list(range(n_bands))
    band_edges = np.linspace(0.0, math.pi + 1e-9, n_bands + 1)
    xs, y_band, y_cos = {}, {}, {}

    for L in lengths:
        seqs, bands, cosines = [], [], []
        per_b = max(1, per_len // len(target_bands))
        for bid in target_bands:
            lo, hi = band_edges[bid], band_edges[bid + 1] - 1e-6
            for _ in range(per_b):
                th_target = float(rng.uniform(lo, hi))
                u = rng.normal(size=3)
                u /= np.linalg.norm(u)
                R_target = _so3_rodrigues_np(u * th_target)

                # Random prefix of continuous small increments
                pref = rng.normal(0.0, 0.7, size=(L - 1, 3))
                R_pref = np.eye(3, dtype=np.float64)
                for step_r in _so3_rodrigues_np(pref):
                    R_pref = R_pref @ step_r
                R_last = R_pref.T @ R_target
                # Extract log(R_last) as final axis-angle vector
                cos_l = np.clip((np.trace(R_last) - 1.0) / 2.0, -1.0, 1.0)
                th_l = math.acos(cos_l)
                if th_l < 1e-6:
                    w_last = np.zeros(3, dtype=np.float64)
                elif abs(th_l - math.pi) < 1e-3:
                    eigvals, eigvecs = np.linalg.eigh(R_last)
                    axis = eigvecs[:, int(np.argmax(eigvals.real))]
                    w_last = axis * th_l
                else:
                    skew = (R_last - R_last.T) / (2.0 * math.sin(th_l))
                    w_last = np.array([skew[2, 1], skew[0, 2], skew[1, 0]], dtype=np.float64) * th_l
                full_seq = np.vstack([pref, w_last[None, :]])
                seqs.append(full_seq.astype(np.float32))
                bands.append(bid)
                cosines.append(math.cos(th_target))
        perm = rng.permutation(len(seqs))
        xs[L] = np.stack(seqs, axis=0)[perm]
        y_band[L] = np.array(bands, dtype=np.int64)[perm]
        y_cos[L] = np.array(cosines, dtype=np.float32)[perm]
    return xs, y_band, y_cos


def run_arm2_so3_task(model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(9200 + seed * 101)
    train_lengths = [2, 3, 4, 5]
    eval_lengths = [5, 8, 16, 24, 32]
    p2_len = 5
    s_keep, s_ft = [0, 1, 2], [3, 4]
    n_bands = 5

    X_tr, yb_tr, yc_tr = _sample_so3_sequences(rng, train_lengths, 400)
    X_val, yb_val, yc_val = _sample_so3_sequences(rng, eval_lengths, 350)

    def hat_3d(vecs):
        # vecs: (B, L, 3) -> (B, L, 3, 3) skew-symmetric in float64
        z = torch.zeros_like(vecs[..., 0])
        vx, vy, vz = vecs[..., 0], vecs[..., 1], vecs[..., 2]
        r0 = torch.stack([z, -vz, vy], dim=-1)
        r1 = torch.stack([vz, z, -vx], dim=-1)
        r2 = torch.stack([-vy, vx, z], dim=-1)
        return torch.stack([r0, r1, r2], dim=-2)

    use_etf = (model_name == "so3_gauge_ermoe_etf")

    if model_name == "so3_gauge_ermoe_etf":
        n_experts = 8
        n_rbf = 24
        n_band_feats = n_rbf + 2

        class SO3Model(nn.Module):
            def __init__(self):
                super().__init__()
                # Per-expert so(3) gauge conjugation frame V_e = exp(0.5*(A_e - A_e^T))
                # plus learned radial Lie-algebra scale alpha (initialized away from 1.0 -> learns BCH scale!)
                self.A_gauge = nn.Parameter(torch.randn(n_experts, 3, 3, dtype=torch.float64) * 0.5)
                self.alpha = nn.Parameter(torch.tensor([0.85], dtype=torch.float64))
                feat_dim = n_experts * n_band_feats
                self.head = nn.Linear(feat_dim, n_bands, bias=False, dtype=torch.float64)
                self.reg = nn.Linear(feat_dim, 1, bias=False, dtype=torch.float64)
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float64))
                self.register_buffer("rbf_centers", torch.linspace(-1.0, 1.0, n_rbf, dtype=torch.float64))

            def _product_and_cos(self, X):
                x64 = X.to(torch.float64)
                K = hat_3d(self.alpha * x64)
                R_step = torch.linalg.matrix_exp(K)  # (B, L, 3, 3)
                A_sk = 0.5 * (self.A_gauge - self.A_gauge.transpose(-1, -2))
                V = torch.linalg.matrix_exp(A_sk)  # (E, 3, 3)
                P = torch.eye(3, dtype=torch.float64).view(1, 3, 3).expand(X.shape[0], 3, 3).clone()
                for t in range(X.shape[1]):
                    P = P @ R_step[:, t]
                Pg = torch.einsum("eij,bjk,elk->beil", V, P, V)
                tr1 = torch.diagonal(Pg, dim1=-2, dim2=-1).sum(-1) / 3.0  # (B, E)
                cos_e = (3.0 * tr1 - 1.0) / 2.0
                return cos_e

            def extract_feats(self, X):
                cos_e = self._product_and_cos(X)  # (B, E)
                sigma = 0.08
                diff = cos_e.unsqueeze(-1) - self.rbf_centers.view(1, 1, n_rbf)
                rbf = torch.exp(-0.5 * (diff / sigma) ** 2)
                feats = torch.cat([rbf, cos_e.unsqueeze(-1), torch.ones_like(cos_e.unsqueeze(-1))], dim=-1)
                return feats.reshape(X.shape[0], -1)

            def forward_cls(self, X):
                return self.head(self.extract_feats(X) @ self.W_white)

            def forward_cos(self, X):
                return self.reg(self.extract_feats(X) @ self.W_white).squeeze(-1)

        m = SO3Model()
        lr = 3e-2

    elif model_name == "cayley_ufr_soft":
        class SoftLieModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.lin_map = nn.Linear(3, 9)
                self.head = nn.Linear(12, n_bands)
                self.reg = nn.Linear(12, 1)

            def extract_feats(self, X):
                M = torch.eye(3, dtype=torch.float32).unsqueeze(0).expand(X.shape[0], 3, 3).clone()
                I3 = torch.eye(3, dtype=torch.float32).view(1, 1, 3, 3)
                S = self.lin_map(X).view(X.shape[0], X.shape[1], 3, 3)
                # Soft unconstrained Cayley-like step without true skew constraint
                R_step = I3 + 0.5 * S
                for t in range(X.shape[1]):
                    M = M @ R_step[:, t]
                tr1 = torch.diagonal(M, dim1=-2, dim2=-1).sum(-1, keepdim=True) / 3.0
                return torch.cat([M.reshape(X.shape[0], 9), tr1, tr1 ** 2, torch.ones_like(tr1)], dim=-1)

            def forward_cls(self, X):
                return self.head(self.extract_feats(X))

            def forward_cos(self, X):
                return self.reg(self.extract_feats(X)).squeeze(-1)

        m = SoftLieModel()
        lr = 5e-3

    elif model_name == "mlp_sequence":
        class MLPSeq(nn.Module):
            def __init__(self):
                super().__init__()
                self.enc = nn.Sequential(nn.Linear(3, 48), nn.Tanh(), nn.Linear(48, 48), nn.Tanh())
                self.gru = nn.GRU(48, 48, batch_first=True)
                self.head = nn.Linear(48, n_bands)
                self.reg = nn.Linear(48, 1)

            def extract_feats(self, X):
                h, _ = self.gru(self.enc(X))
                return h[:, -1, :]

            def forward_cls(self, X):
                return self.head(self.extract_feats(X))

            def forward_cos(self, X):
                return self.reg(self.extract_feats(X)).squeeze(-1)

        m = MLPSeq()
        lr = 5e-3
    else:
        raise ValueError(model_name)

    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps_p1)
    m.train()
    for step in range(steps_p1):
        opt.zero_grad()
        loss = 0.0
        for L in train_lengths:
            idx = rng.integers(0, len(yb_tr[L]), size=48)
            xb = torch.tensor(X_tr[L][idx])
            yb = torch.tensor(yb_tr[L][idx], dtype=torch.long)
            yc = torch.tensor(yc_tr[L][idx], dtype=torch.float64 if use_etf else torch.float32)
            loss = loss + F.cross_entropy(m.forward_cls(xb), yb) + 5.0 * F.mse_loss(m.forward_cos(xb), yc)
            if use_etf:
                loss = loss + 5.0 * F.mse_loss(m._product_and_cos(xb).mean(dim=-1), yc)
        (loss / len(train_lengths)).backward()
        opt.step()
        sched.step()

    m.eval()
    if use_etf:
        with torch.no_grad():
            Phi1 = torch.cat([m.extract_feats(torch.tensor(X_tr[L])) for L in train_lengths], dim=0).to(torch.float64)
            Y1 = torch.cat([torch.tensor(yb_tr[L], dtype=torch.long) for L in train_lengths], dim=0)
            Yc1 = torch.cat([torch.tensor(yc_tr[L], dtype=torch.float64) for L in train_lengths], dim=0)
            Cov = (Phi1.T @ Phi1) / float(Phi1.shape[0])
            evals, evecs = torch.linalg.eigh(Cov)
            keep = evals > (1e-10 * evals.max())
            inv_sqrt = evecs[:, keep] @ torch.diag(1.0 / torch.sqrt(evals[keep])) @ evecs[:, keep].T
            m.W_white.copy_(inv_sqrt)
            Z1 = Phi1 @ inv_sqrt
            A_r = Z1.T @ Z1 + 1e-6 * torch.eye(Z1.shape[1], dtype=torch.float64)
            Y_oh = F.one_hot(Y1, num_classes=n_bands).to(torch.float64) * 3.0
            m.head.weight.copy_(torch.linalg.solve(A_r, Z1.T @ Y_oh).T)
            m.reg.weight.copy_(torch.linalg.solve(A_r, Z1.T @ Yc1.unsqueeze(-1)).T)

    eval_res = {}
    with torch.no_grad():
        for L in eval_lengths:
            xb = torch.tensor(X_val[L])
            pred = m.forward_cls(xb).argmax(-1).numpy()
            eval_res[f"L{L}_bacc"] = balanced_accuracy(yb_val[L], pred)
            if L == 32:
                pred_c = m.forward_cos(xb).numpy()
                var = float(np.var(yc_val[L]))
                eval_res["R2_cos"] = float(1.0 - np.mean((pred_c - yc_val[L]) ** 2) / max(1e-12, var))

    # Continual Keep {0,1,2} -> FT {3,4} zero replay
    Xk, yk, _ = _sample_so3_sequences(rng, [p2_len], 360, allowed_bands=s_keep)
    Xf, yf, _ = _sample_so3_sequences(rng, [p2_len], 360, allowed_bands=s_ft)
    with torch.no_grad():
        keep_before = balanced_accuracy(yk[p2_len], m.forward_cls(torch.tensor(Xk[p2_len])).argmax(-1).numpy(), s_keep)

    if use_etf:
        for p in m.parameters():
            p.requires_grad_(False)
        with torch.no_grad():
            Zk = m.extract_feats(torch.tensor(Xk[p2_len])) @ m.W_white
            cov_k = (Zk.T @ Zk) / float(Zk.shape[0])
            ev_k, vec_k = torch.linalg.eigh(cov_k)
            active = ev_k > (1e-6 * ev_k.max())
            V_k = vec_k[:, active]
            P_orth = torch.eye(Zk.shape[1], dtype=torch.float64) - V_k @ V_k.T
        m.head.weight.requires_grad_(True)
        opt2 = torch.optim.SGD([m.head.weight], lr=0.25)
    else:
        opt2 = torch.optim.AdamW(m.parameters(), lr=lr * 0.5, weight_decay=1e-4)

    m.train()
    for _ in range(steps_p2):
        opt2.zero_grad()
        idx = rng.integers(0, len(yf[p2_len]), size=64)
        xb = torch.tensor(Xf[p2_len][idx])
        yb = torch.tensor(yf[p2_len][idx], dtype=torch.long)
        if use_etf:
            with torch.no_grad():
                zf = (m.extract_feats(xb) @ m.W_white) @ P_orth
            logits = m.head(zf)
        else:
            logits = m.forward_cls(xb)
        F.cross_entropy(logits, yb).backward()
        opt2.step()

    m.eval()
    with torch.no_grad():
        keep_after = balanced_accuracy(yk[p2_len], m.forward_cls(torch.tensor(Xk[p2_len])).argmax(-1).numpy(), s_keep)
        ft_acc = balanced_accuracy(yf[p2_len], m.forward_cls(torch.tensor(Xf[p2_len])).argmax(-1).numpy(), s_ft)

    return {
        "model": model_name,
        "seed": seed,
        "n_params": int(sum(p.numel() for p in m.parameters())),
        "forgetting_before_keep": keep_before,
        "forgetting_after_keep": keep_after,
        "forgetting_drop": keep_before - keep_after,
        "ft_acc": ft_acc,
        **eval_res,
    }


# =============================================================================
# Arm 3: Memory-15108 Algebraic Closure Seam & T6 Finite-Sample Concentration
# =============================================================================

def run_arm3_closure_and_t6(n_trials: int = 2000) -> dict:
    # Part A: S3 permutation Koopman matrices on 6 states
    def mul_s3(i, j):
        perms = [(0, 1, 2), (1, 0, 2), (2, 1, 0), (0, 2, 1), (1, 2, 0), (2, 0, 1)]
        p2i = {p: k for k, p in enumerate(perms)}
        return p2i[tuple(perms[i][perms[j][x]] for x in range(3))]

    U_ops = []
    for a in range(6):
        U = np.zeros((6, 6), dtype=np.float64)
        for x in range(6):
            U[x, mul_s3(a, x)] = 1.0
        U_ops.append(U)

    # Commuting invariant conjugacy algebra (3 classes: {0}, {1,2,3}, {4,5}) -> 6x3 indicator basis
    classes = [[0], [1, 2, 3], [4, 5]]
    Q_conj = np.zeros((6, 3), dtype=np.float64)
    for c_id, cl in enumerate(classes):
        v = np.zeros(6, dtype=np.float64)
        v[cl] = 1.0
        Q_conj[:, c_id] = v / np.linalg.norm(v)
    P_conj = Q_conj @ Q_conj.T
    # Right-conjugation-invariant class observable algebra IS right-action invariant? Wait: left-multiplication moves conjugacy classes!
    # For LEFT multiplication U_a f(x) = f(a x): right-regular orbits / constant subspace span{1}, OR full conjugacy under adj: U_a := Ad_a (x -> a x a^{-1})!
    Ad_ops = []
    inv_idx = [next(k for k in range(6) if mul_s3(x, k) == 0) for x in range(6)]
    for a in range(6):
        Ad = np.zeros((6, 6), dtype=np.float64)
        for x in range(6):
            Ad[x, mul_s3(mul_s3(a, x), inv_idx[a])] = 1.0
        Ad_ops.append(Ad)

    comm_defect_exact = float(max(np.linalg.norm(Ad @ P_conj - P_conj @ Ad) for Ad in Ad_ops))
    # Broken: eigenspace of non-invariant G_broken = diag(0, 1, 2, 0, 1, 2) projected to classes 0 vs rest
    v_broken = np.array([1.0, 1.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    v_broken /= np.linalg.norm(v_broken)
    P_broken = np.outer(v_broken, v_broken)
    broken_comm_defect = float(max(np.linalg.norm(Ad @ P_broken - P_broken @ Ad) for Ad in Ad_ops))
    # Quotient leakage on class partition for P_broken (non-conjugacy-invariant): distance of (f * f) / Ad-evolved states
    f_odd = np.array([0.0, 1.0, -1.0, 0.0, 0.0, 0.0], dtype=np.float64)  # swaps under transpositions (1<->2) -> span{f_odd} can be T-invariant for swap (1<->2) yet f_odd^2 leaves span{f_odd}!
    P_odd = np.outer(f_odd, f_odd) / np.dot(f_odd, f_odd)
    f_sq = f_odd ** 2
    alg_escape_defect = float(np.linalg.norm(f_sq - P_odd @ f_sq))

    # Part B: T6 Chebyshev concentration on 3:1 binary noisy POMDP (p=0.75 vs q=0.25, half-gap delta=0.25)
    rng = np.random.default_rng(42026)
    delta = 0.25
    budgets = [10, 25, 50, 100, 250, 500]
    t6_curve = []
    violations = 0
    for N in budgets:
        # True bit drawn equally from {0, 1}; bit=1 gives prob 0.75 of 1, bit=0 gives prob 0.25 of 1
        y = rng.integers(0, 2, size=n_trials)
        p = np.where(y == 1, 0.75, 0.25)
        cnts = rng.binomial(N, p)
        phat = cnts / float(N)
        pred = (phat >= 0.5).astype(np.int64)
        emp_err = float(np.mean(pred != y))
        cheb_bound = float(1.0 / (4.0 * N * (delta ** 2)))
        if emp_err > cheb_bound + 1e-12:
            violations += 1
        t6_curve.append({"N": N, "empirical_err": emp_err, "chebyshev_bound": cheb_bound})

    return {
        "commuting_defect": comm_defect_exact,
        "broken_defect": max(broken_comm_defect, alg_escape_defect),
        "broken_comm_defect": broken_comm_defect,
        "alg_escape_defect": alg_escape_defect,
        "t6_chebyshev_violations": violations,
        "t6_curve": t6_curve,
    }


def _agg_mean(rows: List[dict]) -> dict:
    keys = [k for k in rows[0] if isinstance(rows[0][k], (int, float)) and k != "seed"]
    out = {}
    for k in keys:
        vals = [r[k] for r in rows if k in r]
        if vals:
            out[k] = float(np.mean(vals))
    if "galois_phi_err" in rows[0]:
        out["galois_phi_err"] = float(min(r["galois_phi_err"] for r in rows))
        out["galois_psi_err"] = float(min(r["galois_psi_err"] for r in rows))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    set_low_priority()
    t0 = time.time()

    if args.smoke:
        seeds = [0]
        a5_p1, a5_p2 = 120, 60
        so3_p1, so3_p2 = 150, 80
        t6_trials = 500
    else:
        seeds = [0, 1, 2]
        a5_p1, a5_p2 = 240, 120
        so3_p1, so3_p2 = 260, 120
        t6_trials = 2000

    a5_models = ["spectral_alm_lbfgs_etf", "spectral_alm_adam_linear", "icosahedral_ermoe_etf", "cayley_ufr_soft_etf"]
    so3_models = ["so3_gauge_ermoe_etf", "cayley_ufr_soft", "mlp_sequence"]

    a5_jobs = [(mn, sd, a5_p1, a5_p2) for mn in a5_models for sd in seeds]
    so3_jobs = [(mn, sd, so3_p1, so3_p2) for mn in so3_models for sd in seeds]

    arm1_raw, arm2_raw = {}, {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs1 = {ex.submit(run_arm1_template_free_task, *job): job for job in a5_jobs}
        futs2 = {ex.submit(run_arm2_so3_task, *job): job for job in so3_jobs}
        for f in concurrent.futures.as_completed(futs1):
            r = f.result()
            arm1_raw.setdefault(r["model"], []).append(r)
        for f in concurrent.futures.as_completed(futs2):
            r = f.result()
            arm2_raw.setdefault(r["model"], []).append(r)

    arm1 = {m: _agg_mean(arm1_raw[m]) for m in a5_models}
    arm2 = {m: _agg_mean(arm2_raw[m]) for m in so3_models}
    arm3 = run_arm3_closure_and_t6(n_trials=t6_trials)

    lbfgs = arm1["spectral_alm_lbfgs_etf"]
    adam_lin = arm1["spectral_alm_adam_linear"]
    ico = arm1["icosahedral_ermoe_etf"]
    so3_etf = arm2["so3_gauge_ermoe_etf"]
    so3_cay = arm2["cayley_ufr_soft"]
    so3_mlp = arm2["mlp_sequence"]

    min_lbfgs_bacc = min(lbfgs[f"L{L}_bacc"] for L in (5, 6, 8, 12, 16, 24, 32))
    htf1 = (
        lbfgs["homomorphism_err"] < 1e-10
        and min_lbfgs_bacc >= 0.999
        and lbfgs["galois_phi_err"] < 1e-5
        and lbfgs["galois_psi_err"] < 1e-5
    )
    htf2 = (
        lbfgs["forgetting_after_keep"] >= 0.99
        and lbfgs["forgetting_drop"] <= 0.01
        and (lbfgs["forgetting_after_keep"] - adam_lin["forgetting_after_keep"]) >= 0.50
        and abs(lbfgs["forgetting_after_keep"] - ico["forgetting_after_keep"]) <= 0.01
    )
    htf3 = (
        so3_etf["L32_bacc"] >= 0.99
        and so3_etf["R2_cos"] >= 0.999
        and so3_etf["forgetting_after_keep"] >= 0.99
        and (so3_etf["L32_bacc"] - max(so3_cay["L32_bacc"], so3_mlp["L32_bacc"])) >= 0.30
        and (so3_etf["forgetting_after_keep"] - max(so3_cay["forgetting_after_keep"], so3_mlp["forgetting_after_keep"])) >= 0.30
    )
    n250_err = next(row["empirical_err"] for row in arm3["t6_curve"] if row["N"] == 250)
    htf4 = (
        arm3["commuting_defect"] < 1e-12
        and arm3["broken_defect"] > 0.05
        and arm3["t6_chebyshev_violations"] == 0
        and n250_err <= 0.01
    )

    result = {
        "mode": "smoke" if args.smoke else "full",
        "elapsed_s": round(time.time() - t0, 2),
        "total_runs": len(a5_jobs) + len(so3_jobs) + 1,
        "verdicts": {
            "HTF.1": "HELD" if htf1 else "BROKEN",
            "HTF.2": "HELD" if htf2 else "BROKEN",
            "HTF.3": "HELD" if htf3 else "BROKEN",
            "HTF.4": "HELD" if htf4 else "BROKEN",
        },
        "Arm1_TemplateFree_A5": arm1,
        "Arm2_Continuous_SO3": arm2,
        "Arm3_Closure_T6": arm3,
    }
    if not args.smoke:
        OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
