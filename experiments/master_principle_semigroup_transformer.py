#!/usr/bin/env python
"""Krohn-Rhodes Semigroup (A5 \\wr U2), Real Causal Transformer, & Continuous POMDP Showdown.

Pre-registered predictions:
  experiments/results/master_principle_semigroup_transformer_predictions.json
Output artifact:
  experiments/results/master_principle_semigroup_transformer.json
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[1]
PRED_PATH = ROOT / "experiments" / "results" / "master_principle_semigroup_transformer_predictions.json"
OUT_PATH = ROOT / "experiments" / "results" / "master_principle_semigroup_transformer.json"


def set_low_priority() -> None:
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    except Exception:
        pass


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, classes_present=None) -> float:
    if classes_present is None:
        classes_present = np.unique(y_true)
    recalls = []
    for c in classes_present:
        m = (y_true == c)
        if np.any(m):
            recalls.append(float(np.mean(y_pred[m] == c)))
    return float(np.mean(recalls)) if recalls else 0.0


# =============================================================================
# Finite Group A5 & Non-Invertible Wreath Semigroup A5 \wr U2
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
    n = len(elems)
    assert n == 60
    p2i = {p: i for i, p in enumerate(elems)}
    mul = np.zeros((n, n), dtype=np.int64)
    inv = np.zeros(n, dtype=np.int64)
    for i, a in enumerate(elems):
        inv[i] = p2i[_inv_perm(a)]
        for j, b in enumerate(elems):
            mul[i, j] = p2i[_compose_perm(a, b)]

    s_idx = p2i[s_perm]
    t_idx = p2i[t_perm]
    st_idx = p2i[_compose_perm(s_perm, t_perm)]
    # Mode-1 coupled A5 generators: conjugate pair (t*s*t^-1, s*t*s)
    s1_idx = int(mul[mul[t_idx, s_idx], inv[t_idx]])
    t1_idx = int(mul[mul[s_idx, t_idx], inv[s_idx]])

    def class_of(idx: int) -> int:
        p = elems[idx]
        if p == ident:
            return 0
        cyc = []
        vis = [False] * 5
        for i in range(5):
            if not vis[i]:
                L, c = 0, i
                while not vis[c]:
                    vis[c] = True
                    c = p[c]
                    L += 1
                if L > 1:
                    cyc.append(L)
        cyc.sort()
        if cyc == [2, 2]:
            return 1
        if cyc == [3]:
            return 2
        orb = {int(mul[mul[k, idx], inv[k]]) for k in range(n)}
        return 3 if st_idx in orb else 4

    cids = [class_of(i) for i in range(n)]
    return {
        "n": n,
        "mul": mul,
        "inv": inv,
        "cids": np.array(cids, dtype=np.int64),
        "s_idx": s_idx,
        "t_idx": t_idx,
        "s1_idx": s1_idx,
        "t1_idx": t1_idx,
    }


def eval_a5_u2_seq(seq: np.ndarray, g_tab: dict) -> int:
    """Tokens: 0=s_m, 1=t_m, 2=r0 (reset->(e,0)), 3=r1 (reset->(e,1)). Class in 0..9."""
    mul = g_tab["mul"]
    g = 0
    mode = 0
    s0, t0 = g_tab["s_idx"], g_tab["t_idx"]
    s1, t1 = g_tab["s1_idx"], g_tab["t1_idx"]
    for tok in seq:
        if tok == 2:
            g, mode = 0, 0
        elif tok == 3:
            g, mode = 0, 1
        elif tok == 0:
            gen = s1 if mode == 1 else s0
            g = int(mul[gen, g])
        else:
            gen = t1 if mode == 1 else t0
            g = int(mul[gen, g])
    return int(mode * 5 + g_tab["cids"][g])


def sample_a5_u2_dataset(
    rng: np.random.Generator,
    g_tab: dict,
    lengths: List[int],
    per_len: int,
    allowed_classes=None,
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """Sample balanced sequences covering 0, 1, or 2 resets + A5 composition suffixes."""
    target = list(allowed_classes) if allowed_classes is not None else list(range(10))
    target_set = set(target)
    xs, ys = {}, {}
    mul, inv = g_tab["mul"], g_tab["inv"]
    cids = g_tab["cids"]
    # Precompute short words in each conjugacy class for mode 0 and mode 1 so rare classes
    # (especially class 0/5 identity after group moves, and C2/C3/C5+/C5-) are well balanced.
    gens = {
        0: (g_tab["s_idx"], g_tab["t_idx"]),
        1: (g_tab["s1_idx"], g_tab["t1_idx"]),
    }

    for L in lengths:
        buckets: Dict[int, List[np.ndarray]] = {c: [] for c in target}
        per_c = max(4, per_len // len(target))
        attempts = 0
        while min(len(v) for v in buckets.values()) < per_c and attempts < per_c * 300:
            attempts += 1
            cid = target[attempts % len(target)]
            if len(buckets[cid]) >= per_c:
                continue
            want_mode = cid // 5
            want_a5 = cid % 5
            seq = np.zeros(L, dtype=np.int64)
            # Construct prefix with >=1 random reset in majority of cases so non-invertibility matters
            if L >= 5 and rng.random() < 0.85:
                rpos = int(rng.integers(0, L - 3))
                # Random prefix before reset
                for k in range(rpos):
                    seq[k] = int(rng.choice([0, 1, 2, 3], p=[0.42, 0.42, 0.08, 0.08]))
                seq[rpos] = 2 if want_mode == 0 else 3
                suffix_start = rpos + 1
                # Pick random tokens on suffix then adjust last few moves or sample
                cur_g = 0
                for k in range(suffix_start, L - 2):
                    tok = int(rng.integers(0, 2))
                    seq[k] = tok
                    cur_g = int(mul[gens[want_mode][tok], cur_g])
                # Solve last 2-6 moves to land cleanly inside want_a5
                # Search up to 64 short completions of length 2..min(5, L-suffix_start)
                tail_len = L - (L - 2)
                found = False
                for _ in range(48):
                    t0, t1 = int(rng.integers(0, 2)), int(rng.integers(0, 2))
                    g2 = int(mul[gens[want_mode][t1], int(mul[gens[want_mode][t0], cur_g])])
                    if int(cids[g2]) == want_a5:
                        seq[L - 2] = t0
                        seq[L - 1] = t1
                        found = True
                        break
                if not found:
                    # Resample short suffix until exact match
                    for _ in range(80):
                        sub = rng.integers(0, 2, size=L - suffix_start)
                        g_sub = 0
                        for tok in sub:
                            g_sub = int(mul[gens[want_mode][int(tok)], g_sub])
                        if int(cids[g_sub]) == want_a5:
                            seq[suffix_start:] = sub
                            found = True
                            break
                if not found:
                    continue
            else:
                if want_mode == 1 and L >= 2:
                    pos0 = int(rng.integers(0, L - 1))
                    seq[:pos0] = rng.integers(0, 2, size=pos0)
                    seq[pos0] = 3
                    sub = rng.integers(0, 2, size=L - pos0 - 1)
                    seq[pos0 + 1:] = sub
                else:
                    seq = rng.integers(0, 2, size=L)
                if eval_a5_u2_seq(seq, g_tab) != cid:
                    continue
            lbl = eval_a5_u2_seq(seq, g_tab)
            if lbl in target_set and len(buckets[lbl]) < per_c:
                buckets[lbl].append(seq)

        all_s, all_y = [], []
        for cid in target:
            for s in buckets[cid][:per_c]:
                all_s.append(s)
                all_y.append(cid)
        perm = rng.permutation(len(all_s))
        xs[L] = np.array(all_s, dtype=np.int64)[perm]
        ys[L] = np.array(all_y, dtype=np.int64)[perm]
    return xs, ys


def _discover_a5_lbfgs_heads_np(seed: int, n_heads: int = 12) -> Tuple[np.ndarray, np.ndarray, dict]:
    """Template-free U(6) A5 generator discovery using blind |Tr(P)-Tr(P^2)| repulsion."""
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
    errs = []

    def solve_one_head(ds: torch.Tensor, dt: torch.Tensor, require_chiral: bool = False):
        best_res = 1e9
        best_u0, best_u1 = None, None
        for _ in range(8 if require_chiral else 3):
            x_init = rng.normal(0.0, 0.7, size=72).astype(np.float64)
            if require_chiral:
                def obj1(vec: np.ndarray):
                    tvec = torch.tensor(vec, dtype=torch.float64, requires_grad=True)
                    Z = torch.complex(tvec[:36].view(6, 6), tvec[36:].view(6, 6))
                    V = torch.linalg.matrix_exp(Z - Z.conj().T)
                    P = (V @ ds @ V.conj().T) @ dt
                    P2 = P @ P
                    P5 = P2 @ P2 @ P
                    R = P5 - eye6
                    gap = (torch.diagonal(P).sum() - torch.diagonal(P2).sum()).abs() ** 2
                    loss = (R.abs() ** 2).sum() + 2.0 * torch.exp(-0.25 * gap)
                    loss.backward()
                    return float(loss.detach().item()), tvec.grad.detach().numpy().astype(np.float64)

                x_init = minimize(obj1, x_init, method="L-BFGS-B", jac=True,
                                  options={"maxiter": 110, "ftol": 1e-18, "gtol": 1e-10}).x

            def obj2(vec: np.ndarray):
                tvec = torch.tensor(vec, dtype=torch.float64, requires_grad=True)
                Z = torch.complex(tvec[:36].view(6, 6), tvec[36:].view(6, 6))
                V = torch.linalg.matrix_exp(Z - Z.conj().T)
                P = (V @ ds @ V.conj().T) @ dt
                P2 = P @ P
                R = (P2 @ P2 @ P) - eye6
                loss = (R.abs() ** 2).sum()
                loss.backward()
                return float(loss.detach().item()), tvec.grad.detach().numpy().astype(np.float64)

            res = minimize(obj2, x_init, method="L-BFGS-B", jac=True,
                           options={"maxiter": 300, "ftol": 1e-30, "gtol": 1e-14})
            with torch.no_grad():
                tvec = torch.tensor(res.x, dtype=torch.float64)
                Z = torch.complex(tvec[:36].view(6, 6), tvec[36:].view(6, 6))
                V = torch.linalg.matrix_exp(Z - Z.conj().T)
                U0 = (V @ ds @ V.conj().T).numpy()
                U1 = dt.numpy()
                P = U0 @ U1
                err = float(np.linalg.norm(np.linalg.matrix_power(P, 5) - np.eye(6)) ** 2)
                cdiff = abs(np.trace(P) - np.trace(P @ P))
            if err < 1e-18 and (not require_chiral or cdiff > 0.5):
                return U0, U1, err
            if err < best_res and (not require_chiral or cdiff > 0.5):
                best_res = err
                best_u0, best_u1 = U0, U1
        return best_u0, best_u1, best_res

    n_chiral = (2 * n_heads) // 3
    attempts = 0
    while len(u0_list) < n_chiral and attempts < 50:
        attempts += 1
        U0, U1, err = solve_one_head(ds_33, dt_33, require_chiral=True)
        if U0 is not None and err < 1e-18:
            u0_list.append(U0)
            u1_list.append(U1)
            errs.append(err)
    while len(u0_list) < n_heads:
        U0, U1, err = solve_one_head(ds_42, dt_42, require_chiral=False)
        if U0 is not None and err < 1e-18:
            u0_list.append(U0)
            u1_list.append(U1)
            errs.append(err)

    return np.stack(u0_list, axis=0), np.stack(u1_list, axis=0), {
        "a5_hom_err": float(np.mean(errs)),
        "n_heads": len(u0_list),
    }


def run_arm1_kr_task(model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(9100 + seed * 101)
    g_tab = make_a5_group()
    n_classes = 10
    s_keep, s_ft = [0, 1, 2, 3, 4, 5], [6, 7, 8, 9]
    train_lengths = [6, 8, 10]
    eval_lengths = [6, 12, 24, 48]
    p2_len = 8

    X_tr, y_tr = sample_a5_u2_dataset(rng, g_tab, train_lengths, 260)
    X_val, y_val = sample_a5_u2_dataset(rng, g_tab, eval_lengths, 220)
    use_etf = model_name.endswith("_etf")
    extra_diag: Dict[str, float] = {}

    if model_name == "kr_wreath_ermoe_etf":
        n_heads = 12
        d = 6
        u0_np, u1_np, a5_diag = _discover_a5_lbfgs_heads_np(seed, n_heads=n_heads)
        extra_diag.update(a5_diag)
        U_s0 = torch.tensor(u0_np, dtype=torch.complex128)
        U_t0 = torch.tensor(u1_np, dtype=torch.complex128)
        U_id = torch.eye(d, dtype=torch.complex128).unsqueeze(0).expand_as(U_s0).clone()
        U_t0h = U_t0.conj().transpose(-1, -2)
        U_s0h = U_s0.conj().transpose(-1, -2)
        U_s1 = U_t0 @ U_s0 @ U_t0h
        U_t1 = U_s0 @ U_t0 @ U_s0h
        cand_list = [U_s0, U_t0, U_s1, U_t1]  # 4 non-identity A5 unitary candidates

        class KRModel(nn.Module):
            def __init__(self):
                super().__init__()
                # Gauge-covariant symmetric initialization across all 4 tokens and initial mode p0
                self.reset_logit = nn.Parameter(torch.zeros(4, dtype=torch.float64))
                self.pi_logit = nn.Parameter(torch.randn(4, 2, dtype=torch.float64) * 0.25)
                self.p0_logit = nn.Parameter(torch.zeros(2, dtype=torch.float64))
                self.mode_head = nn.Linear(2, n_classes, bias=True, dtype=torch.float64)
                feat_dim = 2 * n_heads * 4 + 2  # ERMoE mode-routed trace features + mode prob
                self.head = nn.Linear(feat_dim, n_classes, bias=False, dtype=torch.float64)
                self.register_buffer("U_id", U_id)
                self.register_buffer("W_fiber", U_id.unsqueeze(0).unsqueeze(0).repeat(4, 2, 1, 1, 1).clone())
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float64))
                self.tau = 1.0

            def u2_operators(self):
                r = torch.sigmoid(self.reset_logit / self.tau)          # (4,), initially 0.50 uniformly
                pi = torch.softmax(self.pi_logit / self.tau, dim=-1)    # (4, 2)
                p0 = torch.softmax(self.p0_logit / self.tau, dim=-1)    # (2,)
                eye2 = torch.eye(2, dtype=torch.float64).unsqueeze(0).expand(4, 2, 2)
                reset_mat = pi.unsqueeze(-1).expand(4, 2, 2)
                M = (1.0 - r).view(4, 1, 1) * eye2 + r.view(4, 1, 1) * reset_mat
                stay = 1.0 - r  # exact det(M) = 1 - r
                return M, stay, p0

            def extract_feats_with_ops(self, X, M, stay, p0_vec, W_fiber):
                B, L = X.shape
                p = p0_vec.unsqueeze(0).expand(B, 2).clone()
                eye_b = self.U_id.unsqueeze(0).expand(B, n_heads, 6, 6).clone()
                P = eye_b.clone()
                for t in range(L):
                    tok = X[:, t]
                    s_t = stay[tok].view(B, 1, 1, 1)
                    W0 = W_fiber[tok, 0]
                    W1 = W_fiber[tok, 1]
                    p0 = p[:, 0].view(B, 1, 1, 1).to(torch.complex128)
                    p1 = p[:, 1].view(B, 1, 1, 1).to(torch.complex128)
                    U_step = p0 * W0 + p1 * W1
                    P = s_t * torch.matmul(U_step, P) + (1.0 - s_t) * eye_b
                    p = torch.bmm(M[tok], p.unsqueeze(-1)).squeeze(-1)
                tr1 = torch.diagonal(P, dim1=-2, dim2=-1).sum(-1) / 6.0
                tr2 = torch.diagonal(torch.matmul(P, P), dim1=-2, dim2=-1).sum(-1) / 6.0
                tr_vec = torch.cat([tr1.real, tr1.imag, tr2.real, tr2.imag], dim=-1)
                f0 = p[:, 0:1] * tr_vec
                f1 = p[:, 1:2] * tr_vec
                return torch.cat([f0, f1, p], dim=-1)

            def extract_feats(self, X):
                M, stay, p0_vec = self.u2_operators()
                return self.extract_feats_with_ops(X, M, stay, p0_vec, self.W_fiber)

            def forward_quotient(self, X):
                M, _, p0_vec = self.u2_operators()
                B, L = X.shape
                p = p0_vec.unsqueeze(0).expand(B, 2).clone()
                for t in range(L):
                    p = torch.bmm(M[X[:, t]], p.unsqueeze(-1)).squeeze(-1)
                return self.mode_head(p)

            def forward(self, X):
                return self.head(self.extract_feats(X) @ self.W_white)

        m = KRModel()
        lr = 0.12

    elif model_name == "unitary_only_ufr_etf":
        n_heads = 12
        d = 6
        u0_np, u1_np, _ = _discover_a5_lbfgs_heads_np(seed, n_heads=n_heads)
        U_s0 = torch.tensor(u0_np, dtype=torch.complex128)
        U_t0 = torch.tensor(u1_np, dtype=torch.complex128)
        U_id = torch.eye(d, dtype=torch.complex128).unsqueeze(0).expand_as(U_s0).clone()
        U_s1 = U_t0 @ U_s0 @ U_t0.conj().transpose(-1, -2)
        U_t1 = U_s0 @ U_t0 @ U_s0.conj().transpose(-1, -2)
        base = torch.stack([U_id, U_s0, U_t0, U_s1, U_t1], dim=0)

        class UnitaryOnly(nn.Module):
            def __init__(self):
                super().__init__()
                # Purely unitary multiplicative generator per token (structurally cannot reset det->0)
                self.Y_re = nn.Parameter(torch.randn(4, n_heads, d, d, dtype=torch.float64) * 0.25)
                self.Y_im = nn.Parameter(torch.randn(4, n_heads, d, d, dtype=torch.float64) * 0.25)
                feat_dim = n_heads * 4
                self.head = nn.Linear(feat_dim, n_classes, bias=False, dtype=torch.float64)
                self.register_buffer("base", base)
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float64))

            def unitary_ops(self):
                Z = torch.complex(self.Y_re, self.Y_im)
                V = torch.linalg.matrix_exp(Z - Z.conj().transpose(-1, -2))
                return V

            def extract_feats(self, X):
                V = self.unitary_ops()
                B, L = X.shape
                P = torch.eye(6, dtype=torch.complex128).view(1, 1, 6, 6).expand(B, n_heads, 6, 6).clone()
                for t in range(L):
                    P = torch.matmul(V[X[:, t]], P)
                tr1 = torch.diagonal(P, dim1=-2, dim2=-1).sum(-1) / 6.0
                tr2 = torch.diagonal(torch.matmul(P, P), dim1=-2, dim2=-1).sum(-1) / 6.0
                return torch.cat([tr1.real, tr1.imag, tr2.real, tr2.imag], dim=-1)

            def forward(self, X):
                return self.head(self.extract_feats(X) @ self.W_white)

        m = UnitaryOnly()
        lr = 0.03

    elif model_name == "causal_transformer":
        class CausalTx(nn.Module):
            def __init__(self):
                super().__init__()
                d_m = 64
                self.emb = nn.Embedding(4, d_m)
                self.pos = nn.Parameter(torch.randn(1, 64, d_m) * 0.02)
                layer = nn.TransformerEncoderLayer(
                    d_model=d_m, nhead=4, dim_feedforward=128, dropout=0.0, batch_first=True
                )
                self.enc = nn.TransformerEncoder(layer, num_layers=2)
                self.head = nn.Linear(d_m, n_classes)

            def forward(self, X):
                L = X.shape[1]
                h = self.emb(X) + self.pos[:, :L]
                mask = nn.Transformer.generate_square_subsequent_mask(L)
                out = self.enc(h, mask=mask, is_causal=True)
                return self.head(out[:, -1, :])

        m = CausalTx()
        lr = 4e-3

    elif model_name == "gru_baseline":
        class GRUBase(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(4, 32)
                self.gru = nn.GRU(32, 64, num_layers=2, batch_first=True)
                self.head = nn.Linear(64, n_classes)

            def forward(self, X):
                h, _ = self.gru(self.emb(X))
                return self.head(h[:, -1, :])

        m = GRUBase()
        lr = 5e-3
    else:
        raise ValueError(model_name)

    if model_name == "kr_wreath_ermoe_etf":
        # Stage 1: Gauge-covariant 4-restart U_2 quotient discovery strictly on X_tr
        q_steps = max(260, steps_p1)
        lr_q = 0.10
        best_q_loss = 1e18
        best_q_state = None
        for r_idx in range(4):
            with torch.no_grad():
                g_loc = torch.Generator()
                g_loc.manual_seed(seed * 1000 + r_idx + 17)
                m.reset_logit.fill_(-1.5)
                m.pi_logit.copy_(torch.randn(4, 2, generator=g_loc, dtype=torch.float64) * 0.5)
                m.p0_logit.copy_(torch.randn(2, generator=g_loc, dtype=torch.float64) * 0.5)
                m.mode_head.weight.copy_(torch.randn(n_classes, 2, generator=g_loc, dtype=torch.float64) * 0.25)
                m.mode_head.bias.zero_()
            opt_q = torch.optim.Adam([m.reset_logit, m.pi_logit, m.p0_logit] + list(m.mode_head.parameters()), lr=lr_q)
            m.train()
            for step in range(q_steps):
                m.tau = 1.0 if step < 120 else max(0.05, 1.0 - 0.95 * ((step - 120) / max(1, q_steps - 121)))
                opt_q.zero_grad()
                loss = 0.0
                for L in train_lengths:
                    idx = rng.integers(0, len(y_tr[L]), size=64)
                    xb = torch.tensor(X_tr[L][idx], dtype=torch.long)
                    yb = torch.tensor(y_tr[L][idx], dtype=torch.long)
                    loss = loss + F.cross_entropy(m.forward_quotient(xb), yb)
                (loss / len(train_lengths)).backward()
                opt_q.step()
            m.eval()
            m.tau = 0.05
            with torch.no_grad():
                q_loss = 0.0
                for L in train_lengths:
                    xb = torch.tensor(X_tr[L], dtype=torch.long)
                    yb = torch.tensor(y_tr[L], dtype=torch.long)
                    q_loss += float(F.cross_entropy(m.forward_quotient(xb), yb).item())
                q_loss /= float(len(train_lengths))
                if q_loss < best_q_loss:
                    best_q_loss = q_loss
                    best_q_state = (
                        m.reset_logit.detach().clone(),
                        m.pi_logit.detach().clone(),
                        m.p0_logit.detach().clone(),
                        m.mode_head.weight.detach().clone(),
                        m.mode_head.bias.detach().clone(),
                    )
        with torch.no_grad():
            m.reset_logit.copy_(best_q_state[0])
            m.pi_logit.copy_(best_q_state[1])
            m.p0_logit.copy_(best_q_state[2])
            m.mode_head.weight.copy_(best_q_state[3])
            m.mode_head.bias.copy_(best_q_state[4])
            M_disc, stay_disc, p0_disc = m.u2_operators()
            extra_diag["reset_contraction_err"] = float(
                max(abs(float(stay_disc[2].item())), abs(float(stay_disc[3].item())),
                    abs(1.0 - float(stay_disc[0].item())), abs(1.0 - float(stay_disc[1].item())))
            )
            extra_diag["det_r0"] = float(torch.linalg.det(M_disc[2]).item())
            extra_diag["det_r1"] = float(torch.linalg.det(M_disc[3]).item())
            extra_diag["det_s"] = float(torch.linalg.det(M_disc[0]).item())

            # Gauge-covariant mode indices determined solely from discovered p0_disc
            m0 = int(p0_disc.argmax().item())
            m1 = 1 - m0
            active_toks = [k for k in range(4) if float(stay_disc[k].item()) > 0.5]
            if len(active_toks) != 2:
                active_toks = sorted(range(4), key=lambda k: float(stay_disc[k].item()), reverse=True)[:2]
            tok_a, tok_b = active_toks[0], active_toks[1]

            X_all = torch.tensor(X_tr[train_lengths[-1]], dtype=torch.long)
            Y_all = torch.tensor(y_tr[train_lengths[-1]], dtype=torch.long)
            B_tr, L_tr = X_all.shape
            p_tr = p0_disc.unsqueeze(0).expand(B_tr, 2).clone()
            stay_mask_0 = torch.ones(B_tr, dtype=torch.bool)
            for t in range(L_tr):
                p_tr = torch.bmm(M_disc[X_all[:, t]], p_tr.unsqueeze(-1)).squeeze(-1)
                stay_mask_0 = stay_mask_0 & (p_tr[:, m0] > 0.8)
            mode1_mask = p_tr[:, m1] > 0.8

            def score_pair(W_trial, sub_mask):
                if int(sub_mask.sum().item()) < 20:
                    return 0.0
                F_sub = m.extract_feats_with_ops(X_all[sub_mask], M_disc, stay_disc, p0_disc, W_trial)
                Y_sub = Y_all[sub_mask]
                A_sub = F_sub.T @ F_sub + 1e-4 * torch.eye(F_sub.shape[1], dtype=torch.float64)
                Y_oh = F.one_hot(Y_sub, num_classes=n_classes).to(torch.float64)
                W_r = torch.linalg.solve(A_sub, F_sub.T @ Y_oh)
                pred = (F_sub @ W_r).argmax(-1)
                return float((pred == Y_sub).to(torch.float64).mean().item())

            # Stage 2A: Lift unitary generators for discovered initial mode m0
            W_best = m.W_fiber.clone()
            best_s0, best_p0 = -1.0, (0, 1)
            for i in range(len(cand_list)):
                for j in range(len(cand_list)):
                    if i == j:
                        continue
                    W_try = W_best.clone()
                    W_try[tok_a, m0] = cand_list[i]
                    W_try[tok_b, m0] = cand_list[j]
                    sc = score_pair(W_try, stay_mask_0)
                    if sc > best_s0:
                        best_s0, best_p0 = sc, (i, j)
            W_best[tok_a, m0] = cand_list[best_p0[0]]
            W_best[tok_b, m0] = cand_list[best_p0[1]]

            # Stage 2B: Lift unitary generators for discovered alternate mode m1
            best_s1, best_p1 = -1.0, (2, 3)
            for i in range(len(cand_list)):
                for j in range(len(cand_list)):
                    if i == j:
                        continue
                    W_try = W_best.clone()
                    W_try[tok_a, m1] = cand_list[i]
                    W_try[tok_b, m1] = cand_list[j]
                    sc = score_pair(W_try, mode1_mask)
                    if sc > best_s1:
                        best_s1, best_p1 = sc, (i, j)
            W_best[tok_a, m1] = cand_list[best_p1[0]]
            W_best[tok_b, m1] = cand_list[best_p1[1]]
            m.W_fiber.copy_(W_best)
            extra_diag["mode0_lift_acc"] = best_s0
            extra_diag["mode1_lift_acc"] = best_s1
    else:
        opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=steps_p1)
        m.train()
        for step in range(steps_p1):
            opt.zero_grad()
            loss = 0.0
            for L in train_lengths:
                idx = rng.integers(0, len(y_tr[L]), size=64)
                xb = torch.tensor(X_tr[L][idx], dtype=torch.long)
                yb = torch.tensor(y_tr[L][idx], dtype=torch.long)
                loss = loss + F.cross_entropy(m(xb), yb)
            (loss / len(train_lengths)).backward()
            opt.step()
            sched.step()
        m.eval()

    if use_etf:
        with torch.no_grad():
            Phi1 = torch.cat([m.extract_feats(torch.tensor(X_tr[L], dtype=torch.long)) for L in train_lengths], dim=0).to(torch.float64)
            Y1 = torch.cat([torch.tensor(y_tr[L], dtype=torch.long) for L in train_lengths], dim=0)
            Cov = (Phi1.T @ Phi1) / float(Phi1.shape[0])
            ev, vec = torch.linalg.eigh(Cov)
            keep = ev > (1e-10 * ev.max())
            inv_sqrt = vec[:, keep] @ torch.diag(1.0 / torch.sqrt(ev[keep])) @ vec[:, keep].T
            m.W_white.copy_(inv_sqrt)
            Z1 = Phi1 @ inv_sqrt
            A_r = Z1.T @ Z1 + 1e-6 * torch.eye(Z1.shape[1], dtype=torch.float64)
            Y_oh = F.one_hot(Y1, num_classes=n_classes).to(torch.float64) * 3.0
            m.head.weight.copy_(torch.linalg.solve(A_r, Z1.T @ Y_oh).T)

    eval_res = {}
    with torch.no_grad():
        for L in eval_lengths:
            xb = torch.tensor(X_val[L], dtype=torch.long)
            pred = m(xb).argmax(-1).numpy()
            eval_res[f"L{L}_bacc"] = balanced_accuracy(y_val[L], pred)

    # Zero-replay continual learning: Keep {0..5} -> FT {6..9}
    Xk, yk = sample_a5_u2_dataset(rng, g_tab, [p2_len], 420, allowed_classes=s_keep)
    Xf, yf = sample_a5_u2_dataset(rng, g_tab, [p2_len], 360, allowed_classes=s_ft)
    with torch.no_grad():
        keep_before = balanced_accuracy(yk[p2_len], m(torch.tensor(Xk[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_keep)

    if use_etf:
        for p in m.parameters():
            p.requires_grad_(False)
        with torch.no_grad():
            Zk = m.extract_feats(torch.tensor(Xk[p2_len], dtype=torch.long)) @ m.W_white
            cov_k = (Zk.T @ Zk) / float(Zk.shape[0])
            ev_k, vec_k = torch.linalg.eigh(cov_k)
            active = ev_k > (1e-6 * ev_k.max())
            V_k = vec_k[:, active]
            P_orth = torch.eye(Zk.shape[1], dtype=torch.float64) - V_k @ V_k.T
        m.head.weight.requires_grad_(True)
        opt2 = torch.optim.SGD([m.head.weight], lr=0.25)
    else:
        opt2 = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=1e-4)

    m.train()
    for _ in range(steps_p2):
        opt2.zero_grad()
        idx = rng.integers(0, len(yf[p2_len]), size=64)
        xb = torch.tensor(Xf[p2_len][idx], dtype=torch.long)
        yb = torch.tensor(yf[p2_len][idx], dtype=torch.long)
        if use_etf:
            with torch.no_grad():
                zf = (m.extract_feats(xb) @ m.W_white) @ P_orth
            logits = m.head(zf)
        else:
            logits = m(xb)
        F.cross_entropy(logits, yb).backward()
        opt2.step()

    m.eval()
    with torch.no_grad():
        keep_after = balanced_accuracy(yk[p2_len], m(torch.tensor(Xk[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_keep)
        ft_acc = balanced_accuracy(yf[p2_len], m(torch.tensor(Xf[p2_len], dtype=torch.long)).argmax(-1).numpy(), s_ft)

    return {
        "model": model_name,
        "seed": seed,
        "n_params": int(sum(p.numel() for p in m.parameters())),
        "forgetting_before_keep": keep_before,
        "forgetting_after_keep": keep_after,
        "forgetting_drop": keep_before - keep_after,
        "ft_acc": ft_acc,
        **eval_res,
        **extra_diag,
    }


# =============================================================================
# Arm 2: Real 2-Layer Causal Transformer on Non-Group Bounded-Dyck + Reset Language
# =============================================================================
# Vocab (11): 0='(', 1=')', 2='[', 3=']', 4='#' (reset), 5='a' (mode 0), 6='b' (mode 1),
#             7..10 = depth-typed payload tokens (d0..d3) matching current stack depth.
# State: (depth=min(len(stack), 3), mode in {0,1}) -> class = mode * 4 + depth in 0..7.

def _eval_dyck_reset_states(seq: List[int] | np.ndarray) -> List[int]:
    stack: List[int] = []
    mode = 0
    states = []
    for tok in seq:
        t = int(tok)
        if t == 0 or t == 2:
            if len(stack) < 3:
                stack.append(t)
        elif t == 1:
            if stack and stack[-1] == 0:
                stack.pop()
        elif t == 3:
            if stack and stack[-1] == 2:
                stack.pop()
        elif t == 4:
            stack.clear()
            mode = 0
        elif t == 5:
            mode = 0
        elif t == 6:
            mode = 1
        # Tokens 7..10 are depth-typed expression payloads leaving (stack, mode) unchanged.
        states.append(mode * 4 + min(len(stack), 3))
    return states


def _sample_dyck_reset_corpus(
    rng: np.random.Generator, n_seqs: int, seq_len: int = 16,
    target_classes: List[int] | None = None,
) -> Tuple[np.ndarray, np.ndarray]:
    xs, ys = [], []
    per_c = max(1, n_seqs // len(target_classes)) if target_classes else n_seqs
    buckets = {c: [] for c in (target_classes if target_classes else range(8))}

    def gen_one():
        stack: List[int] = []
        mode = 0
        seq: List[int] = []
        for pos in range(seq_len):
            d_cur = len(stack)
            w_push = [5, 4, 2, 0][d_cur]
            w_pop = [0, 2, 4, 6][d_cur]
            choices = [7 + d_cur] * 5
            if d_cur < 3 and w_push > 0:
                choices.extend(([0] if mode == 0 else [2]) * w_push)
            if stack and w_pop > 0:
                choices.extend(([1] if stack[-1] == 0 else [3]) * w_pop)
            choices.extend([5, 6, 4])
            tok = int(rng.choice(choices))
            seq.append(tok)
            if tok in (0, 2) and len(stack) < 3:
                stack.append(tok)
            elif tok == 1 and stack and stack[-1] == 0:
                stack.pop()
            elif tok == 3 and stack and stack[-1] == 2:
                stack.pop()
            elif tok == 4:
                stack.clear()
                mode = 0
            elif tok == 5:
                mode = 0
            elif tok == 6:
                mode = 1
        lbl = mode * 4 + min(len(stack), 3)
        return seq, lbl

    if target_classes is None:
        while len(xs) < n_seqs:
            seq, lbl = gen_one()
            xs.append(seq)
            ys.append(lbl)
    else:
        tset = set(target_classes)
        attempts = 0
        while min(len(v) for v in buckets.values()) < per_c and attempts < n_seqs * 60:
            attempts += 1
            seq, lbl = gen_one()
            if lbl in tset and len(buckets[lbl]) < per_c:
                buckets[lbl].append(seq)
        for c in target_classes:
            for seq in buckets[c]:
                xs.append(seq)
                ys.append(c)
        perm = rng.permutation(len(xs))
        return np.array(xs, dtype=np.int64)[perm], np.array(ys, dtype=np.int64)[perm]

    return np.array(xs, dtype=np.int64), np.array(ys, dtype=np.int64)


def run_arm2_transformer_task(seed: int, pretrain_steps: int, ft_steps: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(10200 + seed * 97)
    vocab_size = 11
    seq_len = 16
    d_m = 96

    class RealCausalTransformer(nn.Module):
        def __init__(self, n_out: int):
            super().__init__()
            self.emb = nn.Embedding(vocab_size, d_m)
            # Deterministic sinusoidal PE
            pe = torch.zeros(seq_len, d_m)
            pos = torch.arange(0, seq_len, dtype=torch.float32).unsqueeze(1)
            div = torch.exp(torch.arange(0, d_m, 2, dtype=torch.float32) * (-math.log(10000.0) / d_m))
            pe[:, 0::2] = torch.sin(pos * div)
            pe[:, 1::2] = torch.cos(pos * div)
            self.register_buffer("pe", pe.unsqueeze(0))
            layer = nn.TransformerEncoderLayer(
                d_model=d_m, nhead=4, dim_feedforward=192, dropout=0.0, batch_first=True
            )
            self.enc = nn.TransformerEncoder(layer, num_layers=2)
            self.lm_head = nn.Linear(d_m, vocab_size)
            self.cls_head = nn.Linear(d_m, n_out, bias=False)

        def encode(self, X):
            L = X.shape[1]
            h = self.emb(X) + self.pe[:, :L]
            mask = nn.Transformer.generate_square_subsequent_mask(L)
            return self.enc(h, mask=mask, is_causal=True)

    # -------------------------------------------------------------------------
    # Sub-Arm 2A: Unsupervised D-Optimal Epiplexity Data Selection (Zero Labels)
    # -------------------------------------------------------------------------
    X_unsup, _ = _sample_dyck_reset_corpus(rng, 2000, seq_len=seq_len)
    tx_unsup = RealCausalTransformer(8)
    opt_u = torch.optim.AdamW(tx_unsup.parameters(), lr=4e-3, weight_decay=1e-4)
    sched_u = torch.optim.lr_scheduler.CosineAnnealingLR(opt_u, T_max=pretrain_steps)
    tx_unsup.train()
    for step in range(pretrain_steps):
        opt_u.zero_grad()
        idx = rng.integers(0, len(X_unsup), size=64)
        xb = torch.tensor(X_unsup[idx], dtype=torch.long)
        H = tx_unsup.encode(xb)
        lm_logits = tx_unsup.lm_head(H[:, :-1, :])
        loss = F.cross_entropy(lm_logits.reshape(-1, vocab_size), xb[:, 1:].reshape(-1))
        loss.backward()
        opt_u.step()
        sched_u.step()

    tx_unsup.eval()
    # Long-tail imbalanced selection pool: Keep common (240 each for {0..3}), rare (12 each for {4..7})
    X_common, y_common = _sample_dyck_reset_corpus(rng, 960, seq_len=seq_len, target_classes=[0, 1, 2, 3])
    X_rare, y_rare = _sample_dyck_reset_corpus(rng, 48, seq_len=seq_len, target_classes=[4, 5, 6, 7])
    X_pool = np.concatenate([X_common, X_rare], axis=0)
    y_pool = np.concatenate([y_common, y_rare], axis=0)
    perm_p = rng.permutation(len(X_pool))
    X_pool, y_pool = X_pool[perm_p], y_pool[perm_p]
    X_test_b, y_test_b = _sample_dyck_reset_corpus(rng, 640, seq_len=seq_len, target_classes=list(range(8)))

    with torch.no_grad():
        H_pool = tx_unsup.encode(torch.tensor(X_pool, dtype=torch.long))[:, -1, :].numpy().astype(np.float64)
        H_test = tx_unsup.encode(torch.tensor(X_test_b, dtype=torch.long))[:, -1, :].numpy().astype(np.float64)
        # L2 normalize representations (no labels accessed!)
        Phi_pool = H_pool / (np.linalg.norm(H_pool, axis=-1, keepdims=True) + 1e-8)
        Phi_test = H_test / (np.linalg.norm(H_test, axis=-1, keepdims=True) + 1e-8)

    def eval_subset(indices: np.ndarray) -> Tuple[float, int]:
        Zp = Phi_pool[indices]
        yp = y_pool[indices]
        A = Zp.T @ Zp + 0.02 * np.eye(d_m)
        Yoh = np.eye(8, dtype=np.float64)[yp]
        W = np.linalg.solve(A, Zp.T @ Yoh)
        pred = (Phi_test @ W).argmax(axis=-1)
        return balanced_accuracy(y_test_b, pred, list(range(8))), int(len(np.unique(yp)))

    # Greedy D-optimal Sherman-Morrison selection (ZERO label access)
    max_B = 160
    lam = 0.05
    Sigma_inv = (1.0 / lam) * np.eye(d_m, dtype=np.float64)
    chosen = np.zeros(len(Phi_pool), dtype=bool)
    dopt_order: List[int] = []
    for _ in range(max_B):
        scores = np.sum((Phi_pool @ Sigma_inv) * Phi_pool, axis=-1)
        scores[chosen] = -1e18
        best_i = int(np.argmax(scores))
        chosen[best_i] = True
        dopt_order.append(best_i)
        v = Phi_pool[best_i]
        Sv = Sigma_inv @ v
        Sigma_inv = Sigma_inv - np.outer(Sv, Sv) / (1.0 + float(v @ Sv))

    sel_metrics = {}
    for B in (40, 80, 160):
        d_acc, d_cov = eval_subset(np.array(dopt_order[:B], dtype=np.int64))
        u_accs, u_covs = [], []
        for r in range(8):
            idx_r = rng.choice(len(Phi_pool), size=B, replace=False)
            ua, uc = eval_subset(idx_r)
            u_accs.append(ua)
            u_covs.append(uc)
        sel_metrics[f"dopt_B{B}_bacc"] = float(d_acc)
        sel_metrics[f"dopt_B{B}_cov"] = float(d_cov)
        sel_metrics[f"uniform_B{B}_bacc"] = float(np.mean(u_accs))
        sel_metrics[f"uniform_B{B}_cov"] = float(np.mean(u_covs))

    # -------------------------------------------------------------------------
    # Sub-Arm 2B: Zero-Replay Continual Learning on Real 2-Layer Causal Transformer
    # -------------------------------------------------------------------------
    s_keep, s_ft = [0, 1, 2, 3, 4], [5, 6, 7]
    Xk_tr, yk_tr = _sample_dyck_reset_corpus(rng, 1000, seq_len=seq_len, target_classes=s_keep)
    Xk_va, yk_va = _sample_dyck_reset_corpus(rng, 400, seq_len=seq_len, target_classes=s_keep)
    Xf_tr, yf_tr = _sample_dyck_reset_corpus(rng, 600, seq_len=seq_len, target_classes=s_ft)
    Xf_va, yf_va = _sample_dyck_reset_corpus(rng, 300, seq_len=seq_len, target_classes=s_ft)

    def train_phase1_backbone():
        m = RealCausalTransformer(8)
        opt = torch.optim.AdamW(m.parameters(), lr=4e-3, weight_decay=1e-4)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=pretrain_steps)
        m.train()
        for _ in range(pretrain_steps):
            opt.zero_grad()
            # Multitask: Phase-1 supervised classification on Keep {0..4} + 1.5x causal next-token LM
            idx_k = rng.integers(0, len(yk_tr), size=64)
            xb_k = torch.tensor(Xk_tr[idx_k], dtype=torch.long)
            yb_k = torch.tensor(yk_tr[idx_k], dtype=torch.long)
            H_k = m.encode(xb_k)
            loss_ce = F.cross_entropy(m.cls_head(H_k[:, -1, :]), yb_k)
            idx_u = rng.integers(0, len(X_unsup), size=48)
            xb_u = torch.tensor(X_unsup[idx_u], dtype=torch.long)
            H_u = m.encode(xb_u)
            loss_lm = F.cross_entropy(m.lm_head(H_u[:, :-1, :]).reshape(-1, vocab_size), xb_u[:, 1:].reshape(-1))
            (loss_ce + 1.5 * loss_lm).backward()
            opt.step()
            sched.step()
        m.eval()
        return m

    base_tx = train_phase1_backbone()
    # Clone exact Phase-1 weights into standard fine-tune copy and whitened-orth copy
    import copy
    tx_std = copy.deepcopy(base_tx)
    tx_orth = copy.deepcopy(base_tx)

    # 1) Additive-Span Raw Linear Orthogonal Ablation on H ∈ R^{96}
    with torch.no_grad():
        H_unsup = tx_orth.encode(torch.tensor(X_unsup, dtype=torch.long))[:, -1, :].to(torch.float64)
        Hk_tr = tx_orth.encode(torch.tensor(Xk_tr, dtype=torch.long))[:, -1, :].to(torch.float64)
        Hk_va = tx_orth.encode(torch.tensor(Xk_va, dtype=torch.long))[:, -1, :].to(torch.float64)
        Hf_tr = tx_orth.encode(torch.tensor(Xf_tr, dtype=torch.long))[:, -1, :].to(torch.float64)
        Hf_va = tx_orth.encode(torch.tensor(Xf_va, dtype=torch.long))[:, -1, :].to(torch.float64)
        yk_t = torch.tensor(yk_tr, dtype=torch.long)

        Cov_u = (H_unsup.T @ H_unsup) / float(H_unsup.shape[0])
        ev, vec = torch.linalg.eigh(Cov_u)
        reg_u = 0.05 * torch.clamp(ev.mean(), min=1e-12)
        W_white_lin = vec @ torch.diag(1.0 / torch.sqrt(torch.clamp(ev, min=0.0) + reg_u)) @ vec.T
        Zk_tr_lin = Hk_tr @ W_white_lin
        Zk_va_lin = Hk_va @ W_white_lin
        Zf_tr_lin = Hf_tr @ W_white_lin
        Zf_va_lin = Hf_va @ W_white_lin
        Y_oh = F.one_hot(yk_t, num_classes=8).to(torch.float64) * 3.0
        W_lin0 = torch.linalg.solve(Zk_tr_lin.T @ Zk_tr_lin + 1e-2 * torch.eye(d_m, dtype=torch.float64), Zk_tr_lin.T @ Y_oh).T
        cov_zkl = (Zk_tr_lin.T @ Zk_tr_lin) / float(Zk_tr_lin.shape[0])
        ev_kl, vec_kl = torch.linalg.eigh(cov_zkl)
        ord_kl = torch.argsort(ev_kl, descending=True)
        cum_kl = torch.cumsum(ev_kl[ord_kl], dim=0) / torch.clamp(ev_kl.sum(), min=1e-12)
        n_kl = min(int(torch.searchsorted(cum_kl, torch.tensor(0.99, dtype=torch.float64)).item()) + 1, d_m - 12)
        V_kl = vec_kl[:, ord_kl[:n_kl]]
        P_orth_lin = torch.eye(d_m, dtype=torch.float64) - V_kl @ V_kl.T

    dW_lin = nn.Parameter(torch.zeros_like(W_lin0))
    opt_lin = torch.optim.SGD([dW_lin], lr=0.35)
    yf_t = torch.tensor(yf_tr, dtype=torch.long)
    for _ in range(ft_steps):
        opt_lin.zero_grad()
        idx = rng.integers(0, len(yf_tr), size=64)
        logits_l = Zf_tr_lin[idx] @ (W_lin0 + dW_lin @ P_orth_lin).T
        (F.cross_entropy(logits_l, yf_t[idx]) + 5e-3 * (dW_lin ** 2).mean()).backward()
        opt_lin.step()
    with torch.no_grad():
        W_lin_fin = W_lin0 + dW_lin @ P_orth_lin
        lin_orth_keep_after = balanced_accuracy(yk_va, (Zk_va_lin @ W_lin_fin.T).argmax(-1).numpy(), s_keep)
        lin_orth_keep_before = balanced_accuracy(yk_va, (Zk_va_lin @ W_lin0.T).argmax(-1).numpy(), s_keep)
        lin_orth_keep_drop = lin_orth_keep_before - lin_orth_keep_after
        lin_orth_ft_acc = balanced_accuracy(yf_va, (Zf_va_lin @ W_lin_fin.T).argmax(-1).numpy(), s_ft)

    # 2) Unsupervised ERMoE Cluster-Routed Orthogonal ETF Readout on Frozen Causal Transformer
    with torch.no_grad():
        H_unsup_np = H_unsup.numpy()
        H_unsup_norm = H_unsup_np / (np.linalg.norm(H_unsup_np, axis=-1, keepdims=True) + 1e-8)
        # Unsupervised PCA (r_proj = 16) computed purely from unlabeled H_unsup
        Cov_np = (H_unsup_norm.T @ H_unsup_norm) / float(len(H_unsup_norm))
        ev_p, vec_p = np.linalg.eigh(Cov_np)
        U_pca = vec_p[:, np.argsort(ev_p)[::-1][:16]]  # (96, 16)

        # Deterministic unsupervised k-means++ (K = 24, 20 Lloyd iterations) strictly on unlabeled H_unsup_norm
        K_exp = 24
        centers = [H_unsup_norm[int(rng.integers(0, len(H_unsup_norm)))].copy()]
        for _ in range(1, K_exp):
            d2 = np.min(np.sum((H_unsup_norm[:, None, :] - np.stack(centers)[None, :, :]) ** 2, axis=-1), axis=-1)
            probs = d2 / max(1e-12, float(np.sum(d2)))
            centers.append(H_unsup_norm[int(rng.choice(len(H_unsup_norm), p=probs))].copy())
        C_np = np.stack(centers, axis=0)
        for _ in range(20):
            d2 = np.sum((H_unsup_norm[:, None, :] - C_np[None, :, :]) ** 2, axis=-1)
            assign = np.argmin(d2, axis=-1)
            for k_i in range(K_exp):
                m_k = assign == k_i
                if np.any(m_k):
                    c_new = H_unsup_norm[m_k].mean(axis=0)
                    C_np[k_i] = c_new / (np.linalg.norm(c_new) + 1e-8)

        U_pca_t = torch.tensor(U_pca, dtype=torch.float64)
        C_t = torch.tensor(C_np, dtype=torch.float64)
        tau_g = 0.04
        d_ermoe = K_exp * 17  # 408

        def ermoe_feats(H_raw: torch.Tensor) -> torch.Tensor:
            H_n = H_raw / torch.clamp(torch.norm(H_raw, dim=-1, keepdim=True), min=1e-8)
            h_p = torch.cat([H_n @ U_pca_t, torch.ones(H_raw.shape[0], 1, dtype=torch.float64)], dim=-1)  # (N, 17)
            d2 = ((H_n.unsqueeze(1) - C_t.unsqueeze(0)) ** 2).sum(dim=-1)  # (N, 24)
            gates = torch.softmax(-d2 / tau_g, dim=-1)  # (N, 24)
            return torch.einsum("nk,nd->nkd", gates, h_p).reshape(H_raw.shape[0], d_ermoe)

        Phi_u_e = ermoe_feats(H_unsup)
        Phi_k_tr = ermoe_feats(Hk_tr)
        Phi_k_va = ermoe_feats(Hk_va)
        Phi_f_tr = ermoe_feats(Hf_tr)
        Phi_f_va = ermoe_feats(Hf_va)

        Cov_e = (Phi_u_e.T @ Phi_u_e) / float(Phi_u_e.shape[0])
        ev_e, vec_e = torch.linalg.eigh(Cov_e)
        reg_e = 0.1 * torch.clamp(ev_e.mean(), min=1e-12)
        W_white = vec_e @ torch.diag(1.0 / torch.sqrt(torch.clamp(ev_e, min=0.0) + reg_e)) @ vec_e.T

        Zk_tr = Phi_k_tr @ W_white
        Zk_va = Phi_k_va @ W_white
        Zf_tr = Phi_f_tr @ W_white
        Zf_va = Phi_f_va @ W_white

        A_r = Zk_tr.T @ Zk_tr + 1e-2 * torch.eye(d_ermoe, dtype=torch.float64)
        W_0 = torch.linalg.solve(A_r, Zk_tr.T @ Y_oh).T  # (8, 408)

        cov_zk = (Zk_tr.T @ Zk_tr) / float(Zk_tr.shape[0])
        ev_k, vec_k = torch.linalg.eigh(cov_zk)
        order = torch.argsort(ev_k, descending=True)
        ev_sorted = ev_k[order]
        cum_var = torch.cumsum(ev_sorted, dim=0) / torch.clamp(ev_sorted.sum(), min=1e-12)
        n_keep_dims = int(torch.searchsorted(cum_var, torch.tensor(0.995, dtype=torch.float64)).item()) + 1
        n_keep_dims = min(n_keep_dims, d_ermoe - 48)
        V_k = vec_k[:, order[:n_keep_dims]]
        P_keep = V_k @ V_k.T
        P_orth = torch.eye(d_ermoe, dtype=torch.float64) - P_keep
        explained_keep_var = float((ev_sorted[:n_keep_dims].sum() / torch.clamp(ev_sorted.sum(), min=1e-12)).item())

        keep_before_orth = balanced_accuracy(yk_va, (Zk_va @ W_0.T).argmax(-1).numpy(), s_keep)
        keep_logits_before = (Zk_va @ W_0.T).numpy()
        keep_before_std = balanced_accuracy(
            yk_va, tx_std.cls_head(tx_std.encode(torch.tensor(Xk_va, dtype=torch.long))[:, -1, :]).argmax(-1).numpy(), s_keep
        )

    # Zero-replay Phase 2 on FT {5..7} via exact Theorem 21 parameterization W_eff = W_0 + dW @ P_orth
    dW_param = nn.Parameter(torch.zeros_like(W_0))
    orth_steps = max(220, ft_steps)
    opt_orth = torch.optim.SGD([dW_param], lr=0.6)
    sched_orth = torch.optim.lr_scheduler.CosineAnnealingLR(opt_orth, T_max=orth_steps)
    for _ in range(orth_steps):
        opt_orth.zero_grad()
        idx = rng.integers(0, len(yf_tr), size=64)
        W_eff = W_0 + dW_param @ P_orth
        logits = Zf_tr[idx] @ W_eff.T
        loss = F.cross_entropy(logits, yf_t[idx]) + 5e-3 * (dW_param ** 2).mean()
        loss.backward()
        opt_orth.step()
        sched_orth.step()

    with torch.no_grad():
        W_final = W_0 + dW_param @ P_orth
        logits_k_after = (Zk_va @ W_final.T).numpy()
        keep_after_orth = balanced_accuracy(yk_va, logits_k_after.argmax(-1), s_keep)
        ft_acc_orth = balanced_accuracy(yf_va, (Zf_va @ W_final.T).argmax(-1).numpy(), s_ft)
        max_keep_logit_drift = float(np.max(np.abs(logits_k_after - keep_logits_before)))

    # 2) Standard Transformer Phase-2 fine-tuning (AdamW)
    tx_std.train()
    opt_std = torch.optim.AdamW(tx_std.parameters(), lr=2e-3, weight_decay=1e-4)
    for _ in range(ft_steps):
        opt_std.zero_grad()
        idx = rng.integers(0, len(yf_tr), size=64)
        xb = torch.tensor(Xf_tr[idx], dtype=torch.long)
        yb = torch.tensor(yf_tr[idx], dtype=torch.long)
        F.cross_entropy(tx_std.cls_head(tx_std.encode(xb)[:, -1, :]), yb).backward()
        opt_std.step()
    tx_std.eval()
    with torch.no_grad():
        keep_after_std = balanced_accuracy(
            yk_va, tx_std.cls_head(tx_std.encode(torch.tensor(Xk_va, dtype=torch.long))[:, -1, :]).argmax(-1).numpy(), s_keep
        )
        ft_acc_std = balanced_accuracy(
            yf_va, tx_std.cls_head(tx_std.encode(torch.tensor(Xf_va, dtype=torch.long))[:, -1, :]).argmax(-1).numpy(), s_ft
        )

    return {
        "seed": seed,
        "selection": sel_metrics,
        "continual": {
            "rank_P_keep": n_keep_dims,
            "explained_keep_var": explained_keep_var,
            "max_keep_logit_drift": max_keep_logit_drift,
            "orth_keep_before": keep_before_orth,
            "orth_keep_after": keep_after_orth,
            "orth_keep_drop": keep_before_orth - keep_after_orth,
            "orth_ft_acc": ft_acc_orth,
            "lin_orth_keep_after": lin_orth_keep_after,
            "lin_orth_keep_drop": lin_orth_keep_drop,
            "lin_orth_ft_acc": lin_orth_ft_acc,
            "std_keep_before": keep_before_std,
            "std_keep_after": keep_after_std,
            "std_keep_drop": keep_before_std - keep_after_std,
            "std_ft_acc": ft_acc_std,
        },
    }


# =============================================================================
# Arm 3: Continuous-State Noisy 2D Double-Integrator POMDP + Float64/Kan Audit
# =============================================================================

def run_arm3_pomdp_and_kan_audit(n_trials: int = 400) -> dict:
    # Part A: 2D noisy double-integrator x_{t+1} = A x_t + theta * B u_t + w_t, y_t = C x_t + v_t
    dt = 0.2
    A = np.array([[1.0, dt], [0.0, 0.92]], dtype=np.float64)
    B = np.array([0.5 * dt * dt, dt], dtype=np.float64)
    C = np.array([[1.0, 0.0]], dtype=np.float64)
    Q = (0.04 ** 2) * np.eye(2, dtype=np.float64)
    R = np.array([[0.22 ** 2]], dtype=np.float64)

    def kalman_ll(ys: np.ndarray, us: np.ndarray, theta: float) -> float:
        m = np.zeros(2, dtype=np.float64)
        P = (0.1 ** 2) * np.eye(2, dtype=np.float64)
        ll = 0.0
        for t in range(len(ys)):
            m_pred = A @ m + theta * B * us[t]
            P_pred = A @ P @ A.T + Q
            S = float((C @ P_pred @ C.T + R)[0, 0])
            innov = float(ys[t] - (C @ m_pred)[0])
            ll += -0.5 * (math.log(2.0 * math.pi * S) + (innov * innov) / S)
            K = (P_pred @ C.T)[:, 0] / S
            m = m_pred + K * innov
            P = (np.eye(2) - np.outer(K, C[0])) @ P_pred
        return ll

    rng = np.random.default_rng(20261123)
    horizons = [5, 10, 20, 40, 80]
    pomdp_curve = []
    cheb_violations = 0
    for T in horizons:
        u_active = np.array([1.2 * math.sin(0.55 * t) + 0.6 * math.cos(1.15 * t) for t in range(T)], dtype=np.float64)
        u_passive = np.zeros(T, dtype=np.float64)
        act_ok, pas_ok = 0, 0
        llr_margin_samples = []
        for trial in range(n_trials):
            theta_true = 1.0 if (trial % 2 == 0) else -1.0
            for is_act, u_seq in ((True, u_active), (False, u_passive)):
                x = rng.normal(0.0, 0.1, size=2)
                ys = np.zeros(T, dtype=np.float64)
                for t in range(T):
                    x = A @ x + theta_true * B * u_seq[t] + rng.normal(0.0, 0.04, size=2)
                    ys[t] = x[0] + rng.normal(0.0, 0.22)
                ll_pos = kalman_ll(ys, u_seq, +1.0)
                ll_neg = kalman_ll(ys, u_seq, -1.0)
                pred_theta = 1.0 if ll_pos >= ll_neg else -1.0
                if is_act:
                    act_ok += int(pred_theta == theta_true)
                    llr_margin_samples.append(theta_true * (ll_pos - ll_neg))
                else:
                    pas_ok += int(pred_theta == theta_true)
        act_acc = act_ok / float(n_trials)
        pas_acc = pas_ok / float(n_trials)
        emp_err = 1.0 - act_acc
        arr = np.array(llr_margin_samples, dtype=np.float64)
        mean_m = max(1e-12, float(np.mean(arr)))
        var_m = float(np.var(arr, ddof=1))
        cheb_bound = min(1.0, var_m / (mean_m * mean_m))
        if emp_err > cheb_bound + 1e-12:
            cheb_violations += 1
        pomdp_curve.append({
            "T": T,
            "active_acc": act_acc,
            "passive_acc": pas_acc,
            "active_err": emp_err,
            "cheb_bound": cheb_bound,
        })

    # Part B: Float64 U_2 Contraction, Gauge Trace & Horn-Fill Combinatorial Audit
    I2 = np.eye(2, dtype=np.float64)
    r0 = np.array([[1.0, 1.0], [0.0, 0.0]], dtype=np.float64)
    r1 = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float64)
    idem_err = max(float(np.linalg.norm(M @ M - M)) for M in (I2, r0, r1))
    det_reset = max(abs(float(np.linalg.det(r0))), abs(float(np.linalg.det(r1))))
    # Random simplex collapse & O(2) gauge trace invariance
    collapse_err = 0.0
    for _ in range(50):
        p = rng.dirichlet([1.0, 1.0])
        q = rng.dirichlet([1.0, 1.0])
        collapse_err = max(collapse_err, float(np.linalg.norm(r0 @ p - r0 @ q, ord=1)), float(np.linalg.norm(r1 @ p - r1 @ q, ord=1)))
    trace_gauge_err = 0.0
    for _ in range(20):
        ang = float(rng.uniform(0.0, 2.0 * math.pi))
        V = np.array([[math.cos(ang), -math.sin(ang)], [math.sin(ang), math.cos(ang)]], dtype=np.float64)
        for M in (I2, r0, r1):
            trace_gauge_err = max(trace_gauge_err, abs(float(np.trace(V @ M @ V.T) - np.trace(M))))

    # Exhaustive 2-horn fill rates:
    def horn_rates(mul_table: np.ndarray) -> dict:
        n = mul_table.shape[0]
        inner = 0
        outer_l = 0
        outer_r = 0
        for f in range(n):
            row_f = set(mul_table[f, :].tolist())
            col_f = set(mul_table[:, f].tolist())
            for x in range(n):
                if 0 <= int(mul_table[f, x]) < n:
                    inner += 1
                if x in row_f:
                    outer_l += 1
                if x in col_f:
                    outer_r += 1
        tot = float(n * n)
        return {
            "n_elems": n,
            "inner_Lambda2_1_rate": inner / tot,
            "outer_Lambda2_0_rate": outer_l / tot,
            "outer_Lambda2_2_rate": outer_r / tot,
        }

    # U2 mul table (row=left factor): id=0, r0=1, r1=2
    u2_mul = np.array([[0, 1, 2], [1, 1, 1], [2, 2, 2]], dtype=np.int64)
    g_tab = make_a5_group()

    # Exact C5 \wr U2 finite monoid (diagonal pairs (a_0, a_1) in Z5 x Z5 = 25 unitaries + 10 resets = 35 elems)
    c5_u2_elems: List[Tuple[str, Tuple[int, int]]] = [("U", (a, b)) for a in range(5) for b in range(5)] + [
        ("R", (a, b)) for a in range(5) for b in range(2)
    ]
    c5_map = {el: idx for idx, el in enumerate(c5_u2_elems)}
    c5_mul = np.zeros((35, 35), dtype=np.int64)
    for i, ei in enumerate(c5_u2_elems):
        for j, ej in enumerate(c5_u2_elems):
            if ei[0] == "U" and ej[0] == "U":
                prod = ("U", ((ei[1][0] + ej[1][0]) % 5, (ei[1][1] + ej[1][1]) % 5))
            elif ei[0] == "U" and ej[0] == "R":
                a, b = ej[1]
                shift = ei[1][b]
                prod = ("R", ((a + shift) % 5, b))
            else:
                # Reset ei on left wipes prior ej
                prod = ei
            c5_mul[i, j] = c5_map[prod]

    # Sampled A5 \wr U2 exact pair verification (200x200 slice with resets + unitaries)
    a5_u2_u = [("U", (g_tab["s_idx"], g_tab["s1_idx"])), ("U", (g_tab["t_idx"], g_tab["t1_idx"])), ("U", (0, 0))]
    # Include all 60 diagonal unitaries (a, a) + 120 resets (a, b) = 180 closed elements?
    # Note diagonal (a,a) is closed under multiplication and with (a,b) resets is closed under left/right composition!
    a5_u2_elems: List[Tuple[str, Tuple[int, int]]] = [("U", (a, a)) for a in range(60)] + [
        ("R", (a, b)) for a in range(60) for b in range(2)
    ]
    a5_u2_map = {el: idx for idx, el in enumerate(a5_u2_elems)}
    a5_mul = g_tab["mul"]
    a5_u2_table = np.zeros((180, 180), dtype=np.int64)
    for i, ei in enumerate(a5_u2_elems):
        for j, ej in enumerate(a5_u2_elems):
            if ei[0] == "U" and ej[0] == "U":
                prod = ("U", (int(a5_mul[ei[1][0], ej[1][0]]), int(a5_mul[ei[1][1], ej[1][1]])))
            elif ei[0] == "U" and ej[0] == "R":
                a, b = ej[1]
                prod = ("R", (int(a5_mul[ei[1][b], a]), b))
            else:
                prod = ei
            a5_u2_table[i, j] = a5_u2_map[prod]

    return {
        "pomdp_curve": pomdp_curve,
        "chebyshev_violations": cheb_violations,
        "u2_float64_audit": {
            "idem_err": idem_err,
            "det_reset_max": det_reset,
            "simplex_collapse_l1_err": collapse_err,
            "trace_gauge_err": trace_gauge_err,
            "trace_gap": abs(float(np.trace(I2) - np.trace(r0))),
        },
        "simplicial_horn_rates": {
            "U2": horn_rates(u2_mul),
            "A5": horn_rates(g_tab["mul"]),
            "C5_wreath_U2": horn_rates(c5_mul),
            "A5_wreath_U2": horn_rates(a5_u2_table),
        },
    }


def _agg_dict_mean(rows: List[dict]) -> dict:
    out = {}
    for k, v in rows[0].items():
        if isinstance(v, (int, float)) and k != "seed":
            out[k] = float(np.mean([r[k] for r in rows]))
        elif isinstance(v, dict):
            out[k] = _agg_dict_mean([r[k] for r in rows])
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
        kr_p1, kr_p2 = 220, 100
        tx_pre, tx_ft = 240, 100
        pomdp_trials = 150
    else:
        seeds = [0, 1, 2]
        kr_p1, kr_p2 = 280, 150
        tx_pre, tx_ft = 320, 120
        pomdp_trials = 500

    kr_models = ["kr_wreath_ermoe_etf", "unitary_only_ufr_etf", "causal_transformer", "gru_baseline"]
    arm1_raw: Dict[str, List[dict]] = {}
    arm2_raw: List[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        f1 = {ex.submit(run_arm1_kr_task, mn, sd, kr_p1, kr_p2): (mn, sd) for mn in kr_models for sd in seeds}
        f2 = {ex.submit(run_arm2_transformer_task, sd, tx_pre, tx_ft): sd for sd in seeds}
        for f in concurrent.futures.as_completed(f1):
            r = f.result()
            arm1_raw.setdefault(r["model"], []).append(r)
        for f in concurrent.futures.as_completed(f2):
            arm2_raw.append(f.result())

    arm1 = {m: _agg_dict_mean(arm1_raw[m]) for m in kr_models}
    arm2 = _agg_dict_mean(arm2_raw)
    arm3 = run_arm3_pomdp_and_kan_audit(n_trials=pomdp_trials)

    kr = arm1["kr_wreath_ermoe_etf"]
    uni = arm1["unitary_only_ufr_etf"]
    tx1 = arm1["causal_transformer"]
    gru1 = arm1["gru_baseline"]

    hkr1 = (
        kr["L48_bacc"] >= 0.98
        and kr["a5_hom_err"] <= 1e-10
        and kr["reset_contraction_err"] <= 1e-4
        and (kr["L48_bacc"] - uni["L48_bacc"]) >= 0.40
        and (kr["L48_bacc"] - tx1["L48_bacc"]) >= 0.30
        and (kr["L48_bacc"] - gru1["L48_bacc"]) >= 0.30
    )
    hkr2 = (
        kr["forgetting_after_keep"] >= 0.98
        and kr["forgetting_drop"] <= 0.01
        and kr["ft_acc"] >= 0.98
        and tx1["forgetting_drop"] >= 0.30
        and gru1["forgetting_drop"] >= 0.30
    )

    sel = arm2["selection"]
    hkr3 = (
        (sel["dopt_B40_bacc"] - sel["uniform_B40_bacc"]) >= 0.05
        and (sel["dopt_B80_bacc"] - sel["uniform_B80_bacc"]) >= 0.05
        and sel["dopt_B40_cov"] >= sel["uniform_B40_cov"]
        and sel["dopt_B80_cov"] >= sel["uniform_B80_cov"]
    )
    cont = arm2["continual"]
    hkr4 = (
        cont["orth_keep_after"] >= 0.85
        and cont["orth_keep_drop"] <= 0.05
        and cont["orth_ft_acc"] >= 0.80
        and cont["std_keep_drop"] >= 0.40
    )

    t80 = next(row for row in arm3["pomdp_curve"] if row["T"] == 80)
    horns = arm3["simplicial_horn_rates"]
    hkr5 = (
        t80["active_acc"] >= 0.98
        and 0.42 <= t80["passive_acc"] <= 0.58
        and (t80["active_acc"] - t80["passive_acc"]) >= 0.40
        and arm3["chebyshev_violations"] == 0
        and arm3["u2_float64_audit"]["det_reset_max"] < 1e-12
        and horns["A5"]["inner_Lambda2_1_rate"] == 1.0
        and horns["A5"]["outer_Lambda2_0_rate"] == 1.0
        and horns["U2"]["inner_Lambda2_1_rate"] == 1.0
        and horns["U2"]["outer_Lambda2_0_rate"] <= 0.60
        and horns["A5_wreath_U2"]["inner_Lambda2_1_rate"] == 1.0
        and horns["A5_wreath_U2"]["outer_Lambda2_0_rate"] < 0.50
    )

    out = {
        "mode": "smoke" if args.smoke else "full",
        "elapsed_s": round(time.time() - t0, 2),
        "verdicts": {
            "HKR.1": "HELD" if hkr1 else "BROKEN",
            "HKR.2": "HELD" if hkr2 else "BROKEN",
            "HKR.3": "HELD" if hkr3 else "BROKEN",
            "HKR.4": "HELD" if hkr4 else "BROKEN",
            "HKR.5": "HELD" if hkr5 else "BROKEN",
        },
        "Arm1_A5_Wreath_U2": arm1,
        "Arm2_Real_Causal_Transformer": arm2,
        "Arm3_Continuous_POMDP_And_Kan": arm3,
    }
    if not args.smoke:
        OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
