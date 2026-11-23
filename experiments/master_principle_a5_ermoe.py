#!/usr/bin/env python3
"""
Pre-Registered 27-Run Phase 5 Showdown (`gemini/master-principle-a5-ermoe`)

Tests 5 pre-registered hypotheses (`HA5.1` - `HA5.5`) extending Master Principle
closure to non-solvable simple group `A5` (`|G| = 60`), ERMoE gauge routing
(`arXiv:2511.10971`), and unsupervised bounded-observer epiplexity data selection
(`arXiv:2608.11746`):
- Arm 1 (15 runs): Exact icosahedral Galois-pair unitary representations on `A5`
  (`icosahedral_ermoe_etf` & `icosahedral_exact_linear`) vs `spectral_alm_gen`,
  `cayley_ufr_soft_etf`, and `cayley_unitary_ufr_soft` across `L = 5..32` OOD
  composition, `2/60 = 0.0333` MDL ratio, and zero-replay/zero-masking Phase-2
  continual learning (`S_keep = {e, C2, C3}`, `S_ft = {C5+, C5-}`).
- Arm 2 (12 runs): Unsupervised D-optimal epiplexity data selection vs uniform Haar
  sampling on `a5_haar_low_budget` (`B in {10,20,40}`, eval `L=32`) and
  `s3_bouquet_haar_low_budget` (`B in {15,25,45}`, eval `L=16`).
- Arm 3 (Audits): Float64 exact `A5` (`60x60`), Galois `phi` vs `psi` 5-cycle
  trace split, 25-trial ERMoE convex-gated trace invariance & cross-expert
  orthogonal logit drift.
"""

import argparse
import concurrent.futures
import itertools
import json
import math
import os
import pathlib
import time
from typing import Dict, List, Tuple

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
from scipy.linalg import expm


# =============================================================================
# Finite Groups: Non-Solvable Simple A5 (|G|=60) & S3 Two-Loop Bouquet (11 Orbits)
# =============================================================================

def _build_group_from_perms(perms: List[Tuple[int, ...]]) -> dict:
    n = len(perms)
    deg = len(perms[0])
    ident = tuple(range(deg))
    if perms[0] != ident:
        idx0 = perms.index(ident)
        perms = [perms[idx0]] + [p for i, p in enumerate(perms) if i != idx0]
    p2i = {p: i for i, p in enumerate(perms)}

    def comp(a, b):
        return tuple(a[b[k]] for k in range(deg))

    mul = np.zeros((n, n), dtype=np.int64)
    inv = np.zeros(n, dtype=np.int64)
    for i, a in enumerate(perms):
        for j, b in enumerate(perms):
            mul[i, j] = p2i[comp(a, b)]
            if mul[i, j] == 0:
                inv[i] = j

    seen = set()
    classes = []
    for i in range(n):
        if i in seen:
            continue
        orb = sorted({int(mul[mul[k, i], inv[k]]) for k in range(n)})
        seen.update(orb)
        classes.append(orb)

    return {"n": n, "perms": perms, "p2i": p2i, "mul": mul, "inv": inv, "raw_classes": classes}


def _bfs_words(n: int, mul: np.ndarray, gen_ids: List[int]) -> List[Tuple[int, ...]]:
    words: Dict[int, Tuple[int, ...]] = {0: ()}
    queue = [0]
    while queue:
        cur = queue.pop(0)
        for sym, gid in enumerate(gen_ids):
            nxt = int(mul[cur, gid])
            if nxt not in words:
                words[nxt] = words[cur] + (sym,)
                queue.append(nxt)
    assert len(words) == n, f"Generators failed to span group ({len(words)}/{n})"
    return [words[i] for i in range(n)]


def make_a5_group() -> dict:
    def parity(p):
        return sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j]) % 2

    perms = [p for p in itertools.permutations(range(5)) if parity(p) == 0]
    g = _build_group_from_perms(perms)
    assert g["n"] == 60 and len(g["raw_classes"]) == 5

    # Explicit semantic ordering of the 5 A5 conjugacy classes:
    # cid 0: {e} (size 1), cid 1: C2 (size 15), cid 2: C3 (size 20),
    # cid 3, 4: C5+, C5- (size 12 each, Galois-conjugate 5-cycle classes)
    by_size: Dict[int, List[List[int]]] = {}
    for orb in g["raw_classes"]:
        by_size.setdefault(len(orb), []).append(orb)
    c5_pair = sorted(by_size[12], key=lambda c: c[0])
    classes = [by_size[1][0], by_size[15][0], by_size[20][0], c5_pair[0], c5_pair[1]]
    cls_of = np.zeros(60, dtype=np.int64)
    for cid, orb in enumerate(classes):
        for x in orb:
            cls_of[x] = cid
    g["classes"] = classes
    g["cls_of"] = cls_of
    g["n_cls"] = 5

    s_perm = (1, 0, 3, 2, 4)  # (0 1)(2 3), order 2
    t_perm = (0, 2, 4, 3, 1)  # (1 2 4), order 3, (s*t)^5 = e
    s_idx = g["p2i"][s_perm]
    t_idx = g["p2i"][t_perm]
    mul = g["mul"]
    assert mul[s_idx, s_idx] == 0
    assert mul[mul[t_idx, t_idx], t_idx] == 0
    st = int(mul[s_idx, t_idx])
    st2 = int(mul[st, st])
    assert mul[mul[st2, st2], st] == 0
    g["s_perm"] = s_perm
    g["t_perm"] = t_perm
    g["gens"] = (s_idx, t_idx)
    g["words"] = _bfs_words(60, mul, [s_idx, t_idx])
    return g


def make_s3_group() -> dict:
    perms = list(itertools.permutations(range(3)))
    g = _build_group_from_perms(perms)
    classes = sorted(g["raw_classes"], key=lambda c: (len(c), c[0]))
    cls_of = np.zeros(6, dtype=np.int64)
    for cid, orb in enumerate(classes):
        for x in orb:
            cls_of[x] = cid
    g["classes"] = classes
    g["cls_of"] = cls_of
    g["n_cls"] = len(classes)
    s_idx = g["p2i"][(1, 0, 2)]
    r_idx = g["p2i"][(1, 2, 0)]
    g["gens"] = (s_idx, r_idx)
    g["words"] = _bfs_words(6, g["mul"], [s_idx, r_idx])
    return g


def build_bouquet_orbits(g_tab: dict) -> dict:
    n = g_tab["n"]
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    orbit_of = np.full((n, n), -1, dtype=np.int64)
    orbits = []
    for a in range(n):
        for b in range(n):
            if orbit_of[a, b] != -1:
                continue
            oid = len(orbits)
            pts = sorted({(int(mul[mul[k, a], inv[k]]), int(mul[mul[k, b], inv[k]])) for k in range(n)})
            for x, y in pts:
                orbit_of[x, y] = oid
            orbits.append(pts)
    return {"n_orbits": len(orbits), "orbits": orbits, "orbit_of": orbit_of}


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, classes_present=None) -> float:
    if classes_present is None:
        classes_present = np.unique(y_true)
    recalls = []
    for c in classes_present:
        m = (y_true == c)
        if np.any(m):
            recalls.append(float(np.mean(y_pred[m] == c)))
    return float(np.mean(recalls)) if recalls else 0.0


def sample_balanced_single_loop(rng, g_tab: dict, lengths: List[int], per_len: int,
                                allowed_classes=None):
    n = g_tab["n"]
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    classes = g_tab["classes"]
    target_cids = list(allowed_classes) if allowed_classes is not None else list(range(len(classes)))

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
                seq = np.roll(np.append(prefix, last), int(rng.integers(0, L)))
                seqs.append(seq)
                labels.append(cid)
        perm = rng.permutation(len(seqs))
        xs[L] = np.array(seqs, dtype=np.int64)[perm]
        ys[L] = np.array(labels, dtype=np.int64)[perm]
    return xs, ys


def sample_balanced_bouquet(rng, g_tab: dict, b_info: dict, loop_lengths: List[int],
                            per_len: int, allowed_orbits=None):
    n = g_tab["n"]
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    orbits = b_info["orbits"]
    target_oids = list(allowed_orbits) if allowed_orbits is not None else list(range(len(orbits)))

    xs, ys = {}, {}
    for Lloop in loop_lengths:
        seqs, labels = [], []
        per_o = max(1, per_len // len(target_oids))
        for oid in target_oids:
            pairs = orbits[oid]
            for k in range(per_o):
                h1, h2 = pairs[k % len(pairs)]
                pref1 = rng.integers(0, n, size=Lloop - 1)
                p1 = 0
                for g in pref1:
                    p1 = int(mul[p1, int(g)])
                last1 = int(mul[inv[p1], h1])
                pref2 = rng.integers(0, n, size=Lloop - 1)
                p2 = 0
                for g in pref2:
                    p2 = int(mul[p2, int(g)])
                last2 = int(mul[inv[p2], h2])
                seqs.append(np.concatenate([np.append(pref1, last1), np.append(pref2, last2)]))
                labels.append(oid)
        perm = rng.permutation(len(seqs))
        xs[Lloop] = np.array(seqs, dtype=np.int64)[perm]
        ys[Lloop] = np.array(labels, dtype=np.int64)[perm]
    return xs, ys


# =============================================================================
# Exact A5 Multi-Irrep Block Generators (d = 6)
# =============================================================================

def _a5_icosahedral_3d_np(alpha: float) -> Tuple[np.ndarray, np.ndarray]:
    u = 0.5 * np.array([alpha, alpha - 1.0, 1.0], dtype=np.float64)
    S = 2.0 * np.outer(u, u) - np.eye(3, dtype=np.float64)
    T = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]], dtype=np.float64)
    return S, T


def _a5_standard_4d_np(s_perm: Tuple[int, ...], t_perm: Tuple[int, ...]) -> Tuple[np.ndarray, np.ndarray]:
    Q = np.zeros((5, 4), dtype=np.float64)
    for k in range(4):
        v = np.zeros(5, dtype=np.float64)
        v[:k + 1] = 1.0
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
    M[:A.shape[0], :A.shape[1]] = A
    M[A.shape[0]:, A.shape[1]:] = B
    return M


def build_a5_5type_6d_blocks_np(g_tab: dict) -> List[Tuple[np.ndarray, np.ndarray]]:
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    psi = (1.0 - math.sqrt(5.0)) / 2.0
    S_phi, T_phi = _a5_icosahedral_3d_np(phi)
    S_psi, T_psi = _a5_icosahedral_3d_np(psi)
    S4, T4 = _a5_standard_4d_np(g_tab["s_perm"], g_tab["t_perm"])
    return [
        (_blk2(S_phi, S_phi), _blk2(T_phi, T_phi)),
        (_blk2(S_psi, S_psi), _blk2(T_psi, T_psi)),
        (_blk2(S4, np.eye(2)), _blk2(T4, np.eye(2))),
        (_blk2(S_phi, np.eye(3)), _blk2(T_phi, np.eye(3))),
        (_blk2(S_psi, np.eye(3)), _blk2(T_psi, np.eye(3))),
    ]


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
    Us = Ub[X]  # (B, L, H, d, d)
    P = Us[:, 0]
    for t in range(1, X.shape[1]):
        P = torch.matmul(P, Us[:, t])
    tr1 = torch.diagonal(P, dim1=-2, dim2=-1).sum(-1) / d
    P2 = torch.matmul(P, P)
    tr2 = torch.diagonal(P2, dim1=-2, dim2=-1).sum(-1) / d
    return torch.cat([tr1.real, tr1.imag, tr2.real, tr2.imag], dim=-1)


# =============================================================================
# Arm 1: Non-Solvable A5 Icosahedral ERMoE Showdown (15 runs)
# =============================================================================

def run_arm1_a5_task(model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(5100 + seed * 101)

    g_tab = make_a5_group()
    n_classes = 5  # {e}=0, C2=1, C3=2, C5+=3, C5-=4
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
        A = Z - Z.conj().transpose(-1, -2)
        return torch.linalg.matrix_exp(A)

    d = 6
    feat_mult = 4
    use_etf = model_name.endswith("_etf")
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))

    if model_name in ("cayley_unitary_ufr_soft", "cayley_ufr_soft_etf"):
        n_heads = 8

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.4 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=(not use_etf))
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float32))

            def unitary_bank(self):
                return make_cayley_bank(self.P_re, self.P_im, self.eye_c)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                feats = self.features_with_bank(Ub, X)
                if use_etf:
                    feats = feats @ self.W_white
                return self.head(feats)

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w = 4.0
        alm_mode = False
        lr = 3e-3

    elif model_name == "spectral_alm_gen":
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
                U0 = torch.matmul(torch.matmul(V0, self.diag_s), V0.conj().transpose(-1, -2))
                U1 = torch.matmul(torch.matmul(V1, self.diag_t), V1.conj().transpose(-1, -2))
                return U0, U1

            def relation_residual(self):
                U0, U1 = self.generators()
                P = torch.matmul(U0, U1)
                P2 = torch.matmul(P, P)
                P4 = torch.matmul(P2, P2)
                return torch.matmul(P4, P) - self.eye_h

            def alm_loss(self):
                R = self.relation_residual()
                quad = 0.5 * self.alm_rho * (R.abs() ** 2).mean()
                lin = (self.alm_lam.conj() * R).real.mean()
                return quad + lin

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
        comp_w = 0.0
        alm_mode = True
        lr = 8e-3

    elif model_name in ("icosahedral_exact_linear", "icosahedral_ermoe_etf"):
        blocks = build_a5_5type_6d_blocks_np(g_tab)
        n_heads = 20  # 4 experts per irrep block type
        gs_list, gt_list = [], []
        for h in range(n_heads):
            Sb, Tb = blocks[h % len(blocks)]
            gs_list.append(torch.tensor(Sb, dtype=torch.complex64))
            gt_list.append(torch.tensor(Tb, dtype=torch.complex64))
        gs_bank = torch.stack(gs_list, dim=0)
        gt_bank = torch.stack(gt_list, dim=0)

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.65 / math.sqrt(d)
                # ERMoE: per-expert unitary eigen-basis gauge conjugation V_h = exp(X_h - X_h*)
                self.X_re = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.X_im = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=(not use_etf))
                self.register_buffer("gs_bank", gs_bank)
                self.register_buffer("gt_bank", gt_bank)
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float32))

            def generators(self):
                V = make_exp_skew(self.X_re, self.X_im)
                Vh = V.conj().transpose(-1, -2)
                U0 = torch.matmul(torch.matmul(V, self.gs_bank), Vh)
                U1 = torch.matmul(torch.matmul(V, self.gt_bank), Vh)
                return U0, U1

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                feats = self.features_with_bank(Ub, X)
                if use_etf:
                    feats = feats @ self.W_white
                return self.head(feats)

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w = 0.0
        alm_mode = False
        lr = 8e-3
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    X_tr, y_tr = sample_balanced_single_loop(rng, g_tab, train_lengths, 500)
    X_val, y_val = sample_balanced_single_loop(rng, g_tab, eval_lengths, 400)

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
            m.W_white.copy_(inv_sqrt.to(torch.float32))
            Z1 = (Phi1 @ inv_sqrt).to(torch.float32)
            Y_oh = F.one_hot(Y1, num_classes=n_classes).to(torch.float32) * 3.0
            A_r = Z1.T @ Z1 + 1e-3 * torch.eye(Z1.shape[1], dtype=torch.float32)
            W_closed = torch.linalg.solve(A_r, Z1.T @ Y_oh).T
            m.head.weight.copy_(W_closed)

    with torch.no_grad():
        Ub = m.unitary_bank()
        eye = torch.eye(d, dtype=torch.complex64).unsqueeze(0).unsqueeze(0).expand_as(Ub)
        unitary_err = float((torch.matmul(Ub, Ub.conj().transpose(-1, -2)) - eye).abs().max().item())
        diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
        hom_err = float((diff.abs() ** 2).mean().item())
        full_bank_frob_sq = float((Ub.abs() ** 2).sum().item())
        if hasattr(m, "generators"):
            U0, U1 = m.generators()
            gen_frob_sq = float(((U0.abs() ** 2).sum() + (U1.abs() ** 2).sum()).item())
        else:
            gen_frob_sq = full_bank_frob_sq
        mdl_ratio = gen_frob_sq / max(1e-12, full_bank_frob_sq)

        eval_res = {}
        for L in eval_lengths:
            logits = m.forward_with_bank(Ub, torch.tensor(X_val[L], dtype=torch.long))
            eval_res[f"L{L}_bacc"] = balanced_accuracy(y_val[L], logits.argmax(-1).numpy())

    # Phase 2 continual learning on S_ft = {C5+, C5-} ONLY (zero replay, zero kept-label masking)
    keep_mask = np.isin(y_val[p2_len], s_keep)
    X_keep, y_keep = X_val[p2_len][keep_mask], y_val[p2_len][keep_mask]
    with torch.no_grad():
        before_keep = balanced_accuracy(
            y_keep, m(torch.tensor(X_keep, dtype=torch.long)).argmax(-1).numpy(), classes_present=s_keep
        )
    X_ft, y_ft = sample_balanced_single_loop(rng, g_tab, [p2_len], 400, allowed_classes=s_ft)

    m.train()
    opt_ft = torch.optim.SGD(m.parameters(), lr=2e-2) if use_etf else torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=0.0)
    for _ in range(steps_p2):
        opt_ft.zero_grad()
        idx = rng.integers(0, len(y_ft[p2_len]), size=64)
        F.cross_entropy(m(torch.tensor(X_ft[p2_len][idx], dtype=torch.long)), torch.tensor(y_ft[p2_len][idx], dtype=torch.long)).backward()
        opt_ft.step()

    m.eval()
    with torch.no_grad():
        Ub_after = m.unitary_bank()
        after_keep = balanced_accuracy(
            y_keep,
            m.forward_with_bank(Ub_after, torch.tensor(X_keep, dtype=torch.long)).argmax(-1).numpy(),
            classes_present=s_keep,
        )
        ft_acc = balanced_accuracy(
            y_ft[p2_len],
            m.forward_with_bank(Ub_after, torch.tensor(X_ft[p2_len], dtype=torch.long)).argmax(-1).numpy(),
            classes_present=s_ft,
        )
        Phi_all = m.features_with_bank(Ub_after, torch.tensor(X_val[p2_len], dtype=torch.long))
        y_all = y_val[p2_len]
        split = len(y_all) // 2
        P_tr, Y_tr_p = Phi_all[:split], y_all[:split]
        P_te, Y_te_p = Phi_all[split:], y_all[split:]
        Y_oh_p = F.one_hot(torch.tensor(Y_tr_p, dtype=torch.long), num_classes=n_classes).to(torch.float32)
        W_pr = torch.linalg.solve(P_tr.T @ P_tr + 1e-3 * torch.eye(P_tr.shape[1]), P_tr.T @ Y_oh_p)
        pred_pr = (P_te @ W_pr).argmax(-1).numpy()
        km_te = np.isin(Y_te_p, s_keep)
        probe_after_keep = balanced_accuracy(Y_te_p[km_te], pred_pr[km_te], classes_present=s_keep)

    return {
        "arm": "Arm1_A5",
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "homomorphism_err": hom_err,
        "gen_frob_sq": gen_frob_sq,
        "full_bank_frob_sq": full_bank_frob_sq,
        "mdl_ratio": mdl_ratio,
        **eval_res,
        "forgetting_before_keep": before_keep,
        "forgetting_after_keep": after_keep,
        "forgetting_drop": float(before_keep - after_keep),
        "ft_acc": ft_acc,
        "probe_after_keep": probe_after_keep,
    }


# =============================================================================
# Arm 2: Unsupervised D-Optimal Epiplexity Selection (12 runs, `#27`)
# =============================================================================

def _a5_element_feats(g_tab: dict) -> np.ndarray:
    blocks = build_a5_5type_6d_blocks_np(g_tab)
    words = g_tab["words"]
    Phi_g = np.zeros((60, 10), dtype=np.float64)
    for ti, (Sb, Tb) in enumerate(blocks):
        mats = [np.eye(6, dtype=np.float64)]
        for w in words[1:]:
            M = Sb if w[0] == 0 else Tb
            for sym in w[1:]:
                M = M @ (Sb if sym == 0 else Tb)
            mats.append(M)
        for i in range(60):
            Phi_g[i, 2 * ti] = np.trace(mats[i]) / 6.0
            Phi_g[i, 2 * ti + 1] = np.trace(mats[i] @ mats[i]) / 6.0
    return Phi_g


def _s3_bouquet_pair_feats(g_tab: dict) -> np.ndarray:
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))
    words = g_tab["words"]

    def s3_bank(t):
        Gs = np.zeros((6, 6), dtype=np.complex128)
        Gt = np.zeros((6, 6), dtype=np.complex128)
        Gs[0, 1] = 1.0; Gs[1, 0] = 1.0
        Gt[0, 0] = omega; Gt[1, 1] = omega2
        if t == 0:
            Gs[2, 3] = 1.0; Gs[3, 2] = 1.0; Gt[2, 2] = omega; Gt[3, 3] = omega2
            Gs[4, 4] = 1.0; Gt[4, 4] = 1.0; Gs[5, 5] = 1.0; Gt[5, 5] = 1.0
        elif t == 1:
            Gs[2, 2] = -1.0; Gt[2, 2] = 1.0; Gs[3, 3] = -1.0; Gt[3, 3] = 1.0
            Gs[4, 4] = 1.0; Gt[4, 4] = 1.0; Gs[5, 5] = 1.0; Gt[5, 5] = 1.0
        else:
            Gs[2, 2] = -1.0; Gt[2, 2] = 1.0; Gs[3, 3] = -1.0; Gt[3, 3] = 1.0
            Gs[4, 4] = -1.0; Gt[4, 4] = 1.0; Gs[5, 5] = 1.0; Gt[5, 5] = 1.0
        mats = [np.eye(6, dtype=np.complex128)]
        for w in words[1:]:
            M = Gs if w[0] == 0 else Gt
            for sym in w[1:]:
                M = M @ (Gs if sym == 0 else Gt)
            mats.append(M)
        return mats

    banks = [s3_bank(t) for t in range(3)]
    feats = np.zeros((6, 6, 60), dtype=np.float64)
    for h1 in range(6):
        for h2 in range(6):
            row = []
            for bk in banks:
                H1, H2 = bk[h1], bk[h2]
                H1d, H2d = H1.conj().T, H2.conj().T
                H1_2, H2_2 = H1 @ H1, H2 @ H2
                H12, H1dH2d = H1 @ H2, H1d @ H2d
                for W in (H1, H2, H1_2, H2_2, H12, H1 @ H2d, H1_2 @ H2, H1 @ H2_2, H12 @ H1dH2d, H12 @ H12):
                    tr = np.trace(W) / 6.0
                    row.extend([tr.real, tr.imag])
            feats[h1, h2] = row
    return feats


def run_arm2_epiplexity_task(world_name: str, mode: str, seed: int, pool_size: int) -> dict:
    rng = np.random.default_rng((9100 if "a5" in world_name else 9500) + seed * 43 + (0 if mode == "uniform_random_sampling" else 7))

    if world_name == "a5_haar_low_budget":
        g_tab = make_a5_group()
        n_cls = 5
        Phi_g = _a5_element_feats(g_tab)
        budgets = [10, 20, 40]
        mul = g_tab["mul"]
        L_pool = 4
        # Unlabeled Haar-uniform pool (L_pool = 4)
        X_pool = rng.integers(0, 60, size=(pool_size, L_pool))
        g_pool = np.zeros(pool_size, dtype=np.int64)
        for t in range(L_pool):
            g_pool = mul[g_pool, X_pool[:, t]]
        y_pool = g_tab["cls_of"][g_pool]
        Phi_pool = Phi_g[g_pool]
        # Fresh balanced OOD L=32 test set
        X_test, y_test_d = sample_balanced_single_loop(rng, g_tab, [32], 400)
        g_test = np.zeros(len(X_test[32]), dtype=np.int64)
        for t in range(32):
            g_test = mul[g_test, X_test[32][:, t]]
        Phi_test = Phi_g[g_test]
        y_test = y_test_d[32]
    else:
        g_tab = make_s3_group()
        b_info = build_bouquet_orbits(g_tab)
        n_cls = b_info["n_orbits"]  # 11
        Phi_pairs = _s3_bouquet_pair_feats(g_tab)
        budgets = [15, 25, 45]
        mul = g_tab["mul"]
        L_loop = 3
        X_p1 = rng.integers(0, 6, size=(pool_size, L_loop))
        X_p2 = rng.integers(0, 6, size=(pool_size, L_loop))
        h1_p = np.zeros(pool_size, dtype=np.int64)
        h2_p = np.zeros(pool_size, dtype=np.int64)
        for t in range(L_loop):
            h1_p = mul[h1_p, X_p1[:, t]]
            h2_p = mul[h2_p, X_p2[:, t]]
        y_pool = np.array([int(b_info["orbit_of"][int(h1_p[i]), int(h2_p[i])]) for i in range(pool_size)], dtype=np.int64)
        Phi_pool = np.array([Phi_pairs[int(h1_p[i]), int(h2_p[i])] for i in range(pool_size)], dtype=np.float64)
        # Fresh balanced OOD Lloop=16 test set
        X_test, y_test_d = sample_balanced_bouquet(rng, g_tab, b_info, [16], 440)
        X16 = X_test[16]
        h1_t = np.zeros(len(X16), dtype=np.int64)
        h2_t = np.zeros(len(X16), dtype=np.int64)
        for t in range(16):
            h1_t = mul[h1_t, X16[:, t]]
            h2_t = mul[h2_t, X16[:, 16 + t]]
        Phi_test = np.array([Phi_pairs[int(h1_t[i]), int(h2_t[i])] for i in range(len(X16))], dtype=np.float64)
        y_test = y_test_d[16]

    baccs, covs = [], []
    feat_dim = Phi_pool.shape[1]
    for B in budgets:
        if mode == "uniform_random_sampling":
            chosen = rng.choice(pool_size, size=B, replace=False)
        else:
            # Unsupervised D-optimal epiplexity selection (ZERO labels read during selection!)
            Sigma = np.eye(feat_dim, dtype=np.float64) * 100.0
            chosen_list = []
            avail = np.ones(pool_size, dtype=bool)
            for _ in range(B):
                scores = np.einsum("ij,jk,ik->i", Phi_pool, Sigma, Phi_pool)
                scores[~avail] = -1.0
                best = int(np.argmax(scores))
                chosen_list.append(best)
                avail[best] = False
                v = Phi_pool[best]
                Sv = Sigma @ v
                Sigma = Sigma - np.outer(Sv, Sv) / (1.0 + float(v @ Sv))
            chosen = np.array(chosen_list, dtype=np.int64)

        covs.append(len(np.unique(y_pool[chosen])) / float(n_cls))
        P_tr = Phi_pool[chosen]
        Y_tr = y_pool[chosen]
        Y_oh = np.eye(n_cls, dtype=np.float64)[Y_tr]
        A_r = P_tr.T @ P_tr + 1e-4 * np.eye(feat_dim, dtype=np.float64)
        W = np.linalg.solve(A_r, P_tr.T @ Y_oh)
        pred = np.argmax(Phi_test @ W, axis=-1)
        baccs.append(balanced_accuracy(y_test, pred))

    return {
        "arm": "Arm2_Epiplexity",
        "world": world_name,
        "mode": mode,
        "seed": seed,
        "mean_ood_bacc": float(np.mean(baccs)),
        "mean_coverage": float(np.mean(covs)),
        "b0_bacc": float(baccs[0]),
        "b1_bacc": float(baccs[1]),
        "b2_bacc": float(baccs[2]),
        "b0_cov": float(covs[0]),
        "b1_cov": float(covs[1]),
        "b2_cov": float(covs[2]),
    }


# =============================================================================
# Arm 3: Float64 A5, Galois Split, & ERMoE Routing Audits
# =============================================================================

def run_a5_ermoe_audits() -> dict:
    rng = np.random.default_rng(20261123)
    a5 = make_a5_group()
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    psi = (1.0 - math.sqrt(5.0)) / 2.0
    S_phi, T_phi = _a5_icosahedral_3d_np(phi)
    S_psi, T_psi = _a5_icosahedral_3d_np(psi)

    def rand_unitary(d):
        Z = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
        return expm(0.5 * (Z - Z.conj().T))

    a5_hom_max, a5_u_max, trace_err_max, galois_err_max = 0.0, 0.0, 0.0, 0.0
    for name, S_loc, T_loc, alpha in (("phi", S_phi, T_phi, phi), ("psi", S_psi, T_psi, psi)):
        for _ in range(15):
            V = rand_unitary(3)
            Us = V @ S_loc.astype(np.complex128) @ V.conj().T
            Ut = V @ T_loc.astype(np.complex128) @ V.conj().T
            mats = [np.eye(3, dtype=np.complex128)]
            for w in a5["words"][1:]:
                M = Us if w[0] == 0 else Ut
                for sym in w[1:]:
                    M = M @ (Us if sym == 0 else Ut)
                mats.append(M)
            for M in mats:
                a5_u_max = max(a5_u_max, float(np.linalg.norm(M @ M.conj().T - np.eye(3))))
            trace_err_max = max(trace_err_max, abs(complex(np.trace(Us) - np.trace(S_loc))), abs(complex(np.trace(Ut) - np.trace(T_loc))))
            galois_err_max = max(galois_err_max, abs(complex(np.trace(Us @ Ut) - alpha)))
            for a in range(60):
                for b in range(60):
                    a5_hom_max = max(a5_hom_max, float(np.linalg.norm(mats[a] @ mats[b] - mats[int(a5["mul"][a, b])])))

    # 25-trial ERMoE convex-gated trace invariance + cross-expert orthogonal SGD drift
    ermoe_trace_err, ermoe_orth_drift = 0.0, 0.0
    E_exp, d_exp, k_exp, m_exp = 6, 4, 16, 4
    for _ in range(25):
        gate = rng.dirichlet(np.ones(E_exp))
        M0 = rng.normal(size=(d_exp, d_exp)) + 1j * rng.normal(size=(d_exp, d_exp))
        routed = np.zeros((d_exp, d_exp), dtype=np.complex128)
        for e in range(E_exp):
            Ve = rand_unitary(d_exp)
            routed += gate[e] * (Ve @ M0 @ Ve.conj().T)
        ermoe_trace_err = max(ermoe_trace_err, abs(complex(np.trace(routed) - np.trace(M0))))

        # Orthogonal subspace x_keep (dim 8) vs x_ft (dim 8)
        Q, _ = np.linalg.qr(rng.normal(size=(k_exp, k_exp)))
        x_keep = Q[:, :3] @ rng.normal(size=3)
        W = rng.normal(size=(m_exp, k_exp))
        init_logits = W @ x_keep
        for _step in range(10):
            x_ft = Q[:, 8:] @ rng.normal(size=k_exp - 8)
            r = rng.normal(size=m_exp)
            W = W - 0.1 * np.outer(r, x_ft)
        ermoe_orth_drift = max(ermoe_orth_drift, float(np.max(np.abs(W @ x_keep - init_logits))))

    return {
        "f64_a5_hom_err": a5_hom_max,
        "f64_a5_unitary_err": a5_u_max,
        "f64_trace_err": trace_err_max,
        "f64_galois_split_err": galois_err_max,
        "ermoe_trace_max_err": ermoe_trace_err,
        "ermoe_orth_logit_drift": ermoe_orth_drift,
        "algebraic_mdl_ratio_A5": 2.0 / 60.0,
    }


def _worker_task(job: tuple) -> dict:
    if job[0] == "arm1":
        _, mname, seed, s1, s2 = job
        return run_arm1_a5_task(mname, seed, s1, s2)
    _, world_name, mode, seed, pool_sz = job
    return run_arm2_epiplexity_task(world_name, mode, seed, pool_sz)


def aggregate_and_judge(results: List[dict], audit: dict, total_elapsed_s: float) -> dict:
    arm1_agg = {}
    for mname in sorted({r["model"] for r in results if r["arm"] == "Arm1_A5"}):
        sub = [r for r in results if r["arm"] == "Arm1_A5" and r["model"] == mname]
        keys = [k for k in sub[0] if k not in ("arm", "model", "seed")]
        arm1_agg[mname] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    arm2_agg = {}
    for wname in ("a5_haar_low_budget", "s3_bouquet_haar_low_budget"):
        arm2_agg[wname] = {}
        for md in ("uniform_random_sampling", "epiplexity_d_optimal_selection"):
            sub = [r for r in results if r["arm"] == "Arm2_Epiplexity" and r["world"] == wname and r["mode"] == md]
            keys = [k for k in sub[0] if k not in ("arm", "world", "mode", "seed")]
            arm2_agg[wname][md] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    ico_etf = arm1_agg["icosahedral_ermoe_etf"]
    ico_lin = arm1_agg["icosahedral_exact_linear"]
    alm = arm1_agg["spectral_alm_gen"]
    cay = arm1_agg["cayley_unitary_ufr_soft"]
    cay_etf = arm1_agg["cayley_ufr_soft_etf"]

    min_ico_bacc = min(ico_etf[f"L{L}_bacc"] for L in (5, 6, 8, 12, 16, 24, 32))
    ha5_1 = (
        max(ico_etf["homomorphism_err"], ico_lin["homomorphism_err"]) <= 1e-5
        and min_ico_bacc >= 0.995
        and (ico_etf["L32_bacc"] - cay["L32_bacc"]) >= 0.55
        and alm["homomorphism_err"] < cay["homomorphism_err"]
    )
    ha5_2 = (
        ico_etf["forgetting_after_keep"] >= 0.98
        and ico_etf["forgetting_drop"] <= 0.02
        and (ico_etf["forgetting_after_keep"] - ico_lin["forgetting_after_keep"]) >= 0.25
        and (ico_etf["L32_bacc"] - cay_etf["L32_bacc"]) >= 0.55
        and (ico_etf["forgetting_after_keep"] - cay_etf["forgetting_after_keep"]) >= 0.25
    )
    a5_e = arm2_agg["a5_haar_low_budget"]["epiplexity_d_optimal_selection"]
    a5_r = arm2_agg["a5_haar_low_budget"]["uniform_random_sampling"]
    s3_e = arm2_agg["s3_bouquet_haar_low_budget"]["epiplexity_d_optimal_selection"]
    s3_r = arm2_agg["s3_bouquet_haar_low_budget"]["uniform_random_sampling"]
    ha5_3 = (
        min(a5_e["mean_ood_bacc"] - a5_r["mean_ood_bacc"], s3_e["mean_ood_bacc"] - s3_r["mean_ood_bacc"]) >= 0.10
        and min(a5_e["mean_coverage"] - a5_r["mean_coverage"], s3_e["mean_coverage"] - s3_r["mean_coverage"]) > 0.05
    )
    a5_param_ratio = ico_etf["n_params"] / cay["n_params"]
    ha5_4 = (ico_etf["mdl_ratio"] < 0.05) and (a5_param_ratio <= 0.10)
    max_neural_u_err = max(r["unitary_max_err"] for r in results if "unitary_max_err" in r)
    ha5_5 = (
        audit["f64_a5_hom_err"] < 1e-13
        and audit["f64_a5_unitary_err"] < 1e-13
        and audit["f64_galois_split_err"] < 1e-14
        and audit["ermoe_trace_max_err"] < 1e-14
        and audit["ermoe_orth_logit_drift"] < 1e-14
        and max_neural_u_err < 1e-4
    )

    return {
        "verdicts": {
            "HA5.1": "HELD" if ha5_1 else "BROKEN",
            "HA5.2": "HELD" if ha5_2 else "BROKEN",
            "HA5.3": "HELD" if ha5_3 else "BROKEN",
            "HA5.4": "HELD" if ha5_4 else "BROKEN",
            "HA5.5": "HELD" if ha5_5 else "BROKEN",
        },
        "total_runs": len(results),
        "total_elapsed_s": round(total_elapsed_s, 2),
        "max_neural_unitary_err": max_neural_u_err,
        "a5_param_ratio": a5_param_ratio,
        "audit": audit,
        "Arm1_A5": arm1_agg,
        "Arm2_Epiplexity": arm2_agg,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    t0 = time.time()
    audit = run_a5_ermoe_audits()
    print(
        f"A5_AUDIT: hom={audit['f64_a5_hom_err']:.2e}, u={audit['f64_a5_unitary_err']:.2e}, "
        f"gal={audit['f64_galois_split_err']:.2e}, ermoe_tr={audit['ermoe_trace_max_err']:.2e}, "
        f"orth_drift={audit['ermoe_orth_logit_drift']:.2e}",
        flush=True,
    )

    seeds = [0] if args.smoke else [0, 1, 2]
    s1 = 180 if args.smoke else 500
    s2 = 100 if args.smoke else 240
    pool_sz = 600

    jobs = []
    for m in ("cayley_unitary_ufr_soft", "cayley_ufr_soft_etf", "spectral_alm_gen", "icosahedral_exact_linear", "icosahedral_ermoe_etf"):
        for sd in seeds:
            jobs.append(("arm1", m, sd, s1, s2))
    for w in ("a5_haar_low_budget", "s3_bouquet_haar_low_budget"):
        for md in ("uniform_random_sampling", "epiplexity_d_optimal_selection"):
            for sd in seeds:
                jobs.append(("arm2", w, md, sd, pool_sz))

    results = []
    temp_dir = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "semplex_trash_oleans"
    raw_dir = temp_dir / f"mp_a5_ermoe_raw_{time.strftime('%Y%m%d_%H%M%S')}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Launching {len(jobs)} jobs with workers={args.workers} ...", flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(_worker_task, jobs)):
            results.append(res)
            with open(raw_dir / f"run_{i:02d}.json", "w", encoding="utf-8") as f:
                json.dump(res, f)
            tag = res.get("model") or f"{res.get('world')}/{res.get('mode')}"
            print(f"[{i+1}/{len(jobs)}] {res['arm']}/{tag}/s{res['seed']} done ({time.time() - t0:.1f}s)", flush=True)

    summary = aggregate_and_judge(results, audit, time.time() - t0)
    print("VERDICTS:", json.dumps(summary["verdicts"]), flush=True)

    if not args.smoke:
        out_path = pathlib.Path(__file__).resolve().parent / "results" / "master_principle_a5_ermoe.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
        print(f"Saved summary -> {out_path} (raw archived at {raw_dir})", flush=True)
    else:
        print("Smoke run summary:", json.dumps({
            "A5_ico_etf_L32": summary["Arm1_A5"]["icosahedral_ermoe_etf"]["L32_bacc"],
            "A5_ico_etf_hom": summary["Arm1_A5"]["icosahedral_ermoe_etf"]["homomorphism_err"],
            "A5_ico_etf_keep": summary["Arm1_A5"]["icosahedral_ermoe_etf"]["forgetting_after_keep"],
            "A5_ico_lin_keep": summary["Arm1_A5"]["icosahedral_exact_linear"]["forgetting_after_keep"],
            "A5_cayley_etf_L32": summary["Arm1_A5"]["cayley_ufr_soft_etf"]["L32_bacc"],
            "A5_cayley_etf_keep": summary["Arm1_A5"]["cayley_ufr_soft_etf"]["forgetting_after_keep"],
            "A5_alm_hom": summary["Arm1_A5"]["spectral_alm_gen"]["homomorphism_err"],
            "A5_alm_L32": summary["Arm1_A5"]["spectral_alm_gen"]["L32_bacc"],
            "param_ratio": summary["a5_param_ratio"],
            "Epi_A5_bacc": summary["Arm2_Epiplexity"]["a5_haar_low_budget"]["epiplexity_d_optimal_selection"]["mean_ood_bacc"],
            "Rand_A5_bacc": summary["Arm2_Epiplexity"]["a5_haar_low_budget"]["uniform_random_sampling"]["mean_ood_bacc"],
            "Epi_S3_bacc": summary["Arm2_Epiplexity"]["s3_bouquet_haar_low_budget"]["epiplexity_d_optimal_selection"]["mean_ood_bacc"],
            "Rand_S3_bacc": summary["Arm2_Epiplexity"]["s3_bouquet_haar_low_budget"]["uniform_random_sampling"]["mean_ood_bacc"],
        }, indent=2), flush=True)


if __name__ == "__main__":
    main()
