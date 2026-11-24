#!/usr/bin/env python3
"""
Pre-Registered 39-Run Master Principle Closure Showdown (`gemini/master-principle-closure`)

Tests 5 pre-registered hypotheses (`HMC.1` - `HMC.5`):
- Arm 1 (27 runs): Exact semidirect unitary presentations (`semidirect_exact_etf` &
  `semidirect_exact_linear`, `A4 = V4 x| C3` up to OOD `L = 32`, `S3 = C3 x| C2`
  bouquet up to OOD `L = 16`) vs `spectral_alm_gen` (Augmented Lagrangian on mixed
  relation), `cayley_ufr_soft_etf`, and `cayley_unitary_ufr_soft`, evaluating both
  OOD length stability and unmodified Phase-2 continual retention (`*_etf` = Phase-1
  feature whitening + bias-free plain SGD, zero replay, zero kept-label masking).
- Arm 2 (12 runs): Stochastic interventional POMDPs (`noisy_hidden_bit_pomdp` and
  `stochastic_s3_holonomy_pomdp`) comparing `passive_sampling_probe` vs
  `active_interventional_probe` across noise levels `{0.0, 0.15, 0.30}` with exact
  kernel TV distance vs empirical finite-sample estimates.
- Arm 3 (Audits): float64 `S3`/`A4` semidirect algebra & trace invariance, exact
  unitary Frobenius MDL ratio (`2d / (|G|d)`), 50-channel random TV DPI contractivity,
  and 50-trial amortized Matrix-KL variational optimality.
"""

import argparse
import concurrent.futures
import itertools
import json
import math
import os
import pathlib
import sys
import time
from typing import Dict, List, Tuple

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
from scipy.linalg import eigh, expm, logm


# =============================================================================
# Finite Groups (S3, A4) + Bouquet Orbits + Sampling
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
    cls_of = np.zeros(n, dtype=np.int64)
    for i in range(n):
        if i in seen:
            continue
        orb = sorted({int(mul[mul[k, i], inv[k]]) for k in range(n)})
        cid = len(classes)
        for x in orb:
            seen.add(x)
            cls_of[x] = cid
        classes.append(orb)

    return {
        "n": n,
        "perms": perms,
        "p2i": p2i,
        "mul": mul,
        "inv": inv,
        "classes": classes,
        "cls_of": cls_of,
        "n_cls": len(classes),
    }


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


def make_s3_group() -> dict:
    perms = list(itertools.permutations(range(3)))
    g = _build_group_from_perms(perms)
    # Generators: s = (1, 0, 2) (order 2), r = (1, 2, 0) (order 3), (s*r)^2 = e
    s_idx = g["p2i"][(1, 0, 2)]
    r_idx = g["p2i"][(1, 2, 0)]
    g["gens"] = (s_idx, r_idx)
    g["words"] = _bfs_words(g["n"], g["mul"], [s_idx, r_idx])
    return g


def make_a4_group() -> dict:
    def parity(p):
        inv_cnt = sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
        return inv_cnt % 2

    perms = [p for p in itertools.permutations(range(4)) if parity(p) == 0]
    g = _build_group_from_perms(perms)
    assert g["n"] == 12 and g["n_cls"] == 4
    # Generators: s = (1, 0, 3, 2) (order 2), t = (1, 2, 0, 3) (order 3), (s*t)^3 = e
    s_idx = g["p2i"][(1, 0, 3, 2)]
    t_idx = g["p2i"][(1, 2, 0, 3)]
    mul = g["mul"]
    assert mul[s_idx, s_idx] == 0
    assert mul[mul[t_idx, t_idx], t_idx] == 0
    st = int(mul[s_idx, t_idx])
    assert mul[mul[st, st], st] == 0
    g["gens"] = (s_idx, t_idx)
    g["words"] = _bfs_words(g["n"], mul, [s_idx, t_idx])
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
    cls_of = g_tab["cls_of"]
    classes = g_tab["classes"]
    target_cids = list(allowed_classes) if allowed_classes is not None else list(range(len(classes)))

    xs, ys = {}, {}
    for L in lengths:
        seqs = []
        labels = []
        per_c = max(1, per_len // len(target_cids))
        for cid in target_cids:
            members = classes[cid]
            for k in range(per_c):
                h_target = int(members[k % len(members)])
                prefix = rng.integers(0, n, size=L - 1)
                prod = 0
                for g in prefix:
                    prod = int(mul[prod, int(g)])
                last = int(mul[g_tab["inv"][prod], h_target])
                seq = np.append(prefix, last)
                shift = int(rng.integers(0, L))
                seq = np.roll(seq, shift)
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
        seqs = []
        labels = []
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
                seq = np.concatenate([np.append(pref1, last1), np.append(pref2, last2)])
                seqs.append(seq)
                labels.append(oid)
        perm = rng.permutation(len(seqs))
        xs[Lloop] = np.array(seqs, dtype=np.int64)[perm]
        ys[Lloop] = np.array(labels, dtype=np.int64)[perm]
    return xs, ys


# =============================================================================
# Arm 1: Exact Semidirect Closure vs Spectral-ALM & Whitened Orthogonal SGD
# =============================================================================

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


def _bouquet_trace_feats(torch, Ub, X, d: int):
    Lloop = X.shape[1] // 2

    def prod_seq(Xs):
        Us = Ub[Xs]
        P = Us[:, 0]
        for t in range(1, Xs.shape[1]):
            P = torch.matmul(P, Us[:, t])
        return P

    H1 = prod_seq(X[:, :Lloop])
    H2 = prod_seq(X[:, Lloop:])
    H1d = H1.conj().transpose(-1, -2)
    H2d = H2.conj().transpose(-1, -2)
    H1_2 = torch.matmul(H1, H1)
    H2_2 = torch.matmul(H2, H2)
    H12 = torch.matmul(H1, H2)
    H1dH2d = torch.matmul(H1d, H2d)
    words = [
        H1, H2, H1_2, H2_2,
        H12, torch.matmul(H1, H2d),
        torch.matmul(H1_2, H2), torch.matmul(H1, H2_2),
        torch.matmul(H12, H1dH2d), torch.matmul(H12, H12),
    ]
    feats = []
    for W in words:
        tr = torch.diagonal(W, dim1=-2, dim2=-1).sum(-1) / d
        feats.append(tr.real)
        feats.append(tr.imag)
    return torch.cat(feats, dim=-1)


def run_arm1_task(group_name: str, model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng((1500 if group_name == "A4" else 3500) + seed * 101)

    if group_name == "A4":
        g_tab = make_a4_group()
        n_classes = g_tab["n_cls"]  # 4
        train_lengths = [2, 3, 4]
        eval_lengths = [4, 5, 6, 8, 12, 16, 24, 32]
        s_keep, s_ft = [0, 1], [2, 3]
        p2_len = 4
        is_bouquet = False
        b_info = None
    else:
        g_tab = make_s3_group()
        b_info = build_bouquet_orbits(g_tab)
        n_classes = b_info["n_orbits"]  # 11
        train_lengths = [2, 3]
        eval_lengths = [3, 4, 6, 8, 12, 16]
        s_keep, s_ft = list(range(6)), list(range(6, 11))
        p2_len = 3
        is_bouquet = True

    G = g_tab["n"]
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
    feat_mult = 4 if not is_bouquet else 20
    use_etf = model_name.endswith("_etf")
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))

    if model_name in ("cayley_unitary_ufr_soft", "cayley_ufr_soft_etf"):
        n_heads = 19 if not is_bouquet else 27

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
                return _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)

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
        n_heads = 32 if not is_bouquet else 24
        half_h = n_heads // 2
        if group_name == "A4":
            ds_row = torch.diag(torch.tensor([1, -1, -1, 1, 1, 1], dtype=torch.complex64))
            diag_s_bank = ds_row.unsqueeze(0).expand(n_heads, d, d).clone()
            dt_pos = torch.diag(torch.tensor([1, omega, omega2, omega, omega, 1], dtype=torch.complex64))
            dt_neg = torch.diag(torch.tensor([1, omega, omega2, omega2, omega2, 1], dtype=torch.complex64))
            diag_t_bank = torch.cat([
                dt_pos.unsqueeze(0).expand(half_h, d, d),
                dt_neg.unsqueeze(0).expand(n_heads - half_h, d, d),
            ], dim=0).clone()
        else:
            ds_row = torch.diag(torch.tensor([1, -1, 1, -1, 1, -1], dtype=torch.complex64))
            diag_s_bank = ds_row.unsqueeze(0).expand(n_heads, d, d).clone()
            dt_row = torch.diag(torch.tensor([1, 1, omega, omega2, omega, omega2], dtype=torch.complex64))
            diag_t_bank = dt_row.unsqueeze(0).expand(n_heads, d, d).clone()

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
                self.alm_rho = 12.0

            def generators(self):
                V0 = make_exp_skew(self.X0_re, self.X0_im)
                V1 = make_exp_skew(self.X1_re, self.X1_im)
                U0 = torch.matmul(torch.matmul(V0, self.diag_s), V0.conj().transpose(-1, -2))
                U1 = torch.matmul(torch.matmul(V1, self.diag_t), V1.conj().transpose(-1, -2))
                return U0, U1

            def relation_residual(self):
                U0, U1 = self.generators()
                U01 = torch.matmul(U0, U1)
                U01_2 = torch.matmul(U01, U01)
                if group_name == "A4":
                    return torch.matmul(U01_2, U01) - self.eye_h
                return U01_2 - self.eye_h

            def alm_loss(self):
                R = self.relation_residual()
                quad = 0.5 * self.alm_rho * (R.abs() ** 2).mean()
                lin = (self.alm_lam.conj() * R).real.mean()
                return quad + lin

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)

            def forward_with_bank(self, Ub, X):
                return self.head(self.features_with_bank(Ub, X))

            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)

        m = Model()
        comp_w = 0.0
        alm_mode = True
        lr = 8e-3 if group_name == "A4" else 6e-3

    elif model_name in ("semidirect_exact_linear", "semidirect_exact_etf"):
        # Exact semidirect generator parameterization:
        #   A4 = V4 x| C3 (`a4GenS`, `a4GenT(phi1, phi2)` on 3D + 4 chiral 1D head types)
        #   S3 = C3 x| C2 (`s3GenS(phi)`, `s3GenR` across 3 irrep-multiplicity head types)
        n_heads = 24 if not is_bouquet else 18

        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.65 / math.sqrt(d)
                self.X_re = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.X_im = nn.Parameter(torch.randn(n_heads, d, d) * scale)
                self.phi1 = nn.Parameter(torch.randn(n_heads) * 0.5)
                self.phi2 = nn.Parameter(torch.randn(n_heads) * 0.5)
                feat_dim = n_heads * feat_mult
                self.head = nn.Linear(feat_dim, n_classes, bias=(not use_etf))
                self.register_buffer("W_white", torch.eye(feat_dim, dtype=torch.float32))

            def _gauge_unitary(self):
                return make_exp_skew(self.X_re, self.X_im)

            def _local_gens(self):
                H = n_heads
                Gs = torch.zeros(H, d, d, dtype=torch.complex64)
                Gt = torch.zeros(H, d, d, dtype=torch.complex64)
                e1 = torch.complex(torch.cos(self.phi1), torch.sin(self.phi1))
                e2 = torch.complex(torch.cos(self.phi2), torch.sin(self.phi2))
                om_c = torch.tensor(omega, dtype=torch.complex64)
                om2_c = torch.tensor(omega2, dtype=torch.complex64)
                if group_name == "A4":
                    em = torch.complex(torch.cos(-(self.phi1 + self.phi2)), torch.sin(-(self.phi1 + self.phi2)))
                    # 3D V4 x| C3 block (indices 0,1,2) + identity on 1D blocks
                    Gs[:, 0, 0] = 1.0
                    Gs[:, 1, 1] = -1.0
                    Gs[:, 2, 2] = -1.0
                    Gs[:, 3, 3] = 1.0
                    Gs[:, 4, 4] = 1.0
                    Gs[:, 5, 5] = 1.0

                    Gt[:, 0, 1] = e1
                    Gt[:, 1, 2] = e2
                    Gt[:, 2, 0] = em
                    # 4 chiral 1D irrep-spectrum head types spanning exact conjugacy-class rank 4
                    q = H // 4
                    Gt[0:q, 3, 3] = om_c
                    Gt[0:q, 4, 4] = om_c
                    Gt[0:q, 5, 5] = 1.0

                    Gt[q:2*q, 3, 3] = om2_c
                    Gt[q:2*q, 4, 4] = om2_c
                    Gt[q:2*q, 5, 5] = 1.0

                    Gt[2*q:3*q, 3, 3] = om_c
                    Gt[2*q:3*q, 4, 4] = 1.0
                    Gt[2*q:3*q, 5, 5] = 1.0

                    Gt[3*q:, 3, 3] = om2_c
                    Gt[3*q:, 4, 4] = 1.0
                    Gt[3*q:, 5, 5] = 1.0
                else:
                    # S3 = C3 x| C2 on 2D irrep block + 3 irrep-multiplicity head types
                    e1c = e1.conj()
                    e2c = e2.conj()
                    Gs[:, 0, 1] = e1
                    Gs[:, 1, 0] = e1c
                    Gt[:, 0, 0] = om_c
                    Gt[:, 1, 1] = om2_c

                    q = H // 3
                    # Type 0: 2*rho_2 + sgn + 1
                    Gs[0:q, 2, 3] = e2[0:q]
                    Gs[0:q, 3, 2] = e2c[0:q]
                    Gt[0:q, 2, 2] = om_c
                    Gt[0:q, 3, 3] = om2_c
                    Gs[0:q, 4, 4] = -1.0
                    Gt[0:q, 4, 4] = 1.0
                    Gs[0:q, 5, 5] = 1.0
                    Gt[0:q, 5, 5] = 1.0

                    # Type 1: rho_2 + 2*sgn + 2*1
                    Gs[q:2*q, 2, 2] = -1.0
                    Gt[q:2*q, 2, 2] = 1.0
                    Gs[q:2*q, 3, 3] = -1.0
                    Gt[q:2*q, 3, 3] = 1.0
                    Gs[q:2*q, 4, 4] = 1.0
                    Gt[q:2*q, 4, 4] = 1.0
                    Gs[q:2*q, 5, 5] = 1.0
                    Gt[q:2*q, 5, 5] = 1.0

                    # Type 2: rho_2 + 3*sgn + 1
                    Gs[2*q:, 2, 2] = -1.0
                    Gt[2*q:, 2, 2] = 1.0
                    Gs[2*q:, 3, 3] = -1.0
                    Gt[2*q:, 3, 3] = 1.0
                    Gs[2*q:, 4, 4] = -1.0
                    Gt[2*q:, 4, 4] = 1.0
                    Gs[2*q:, 5, 5] = 1.0
                    Gt[2*q:, 5, 5] = 1.0
                return Gs, Gt

            def generators(self):
                V = self._gauge_unitary()
                Vh = V.conj().transpose(-1, -2)
                Gs, Gt = self._local_gens()
                U0 = torch.matmul(torch.matmul(V, Gs), Vh)
                U1 = torch.matmul(torch.matmul(V, Gt), Vh)
                return U0, U1

            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)

            def features_with_bank(self, Ub, X):
                return _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)

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
        lr = 8e-3 if group_name == "A4" else 6e-3
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())

    if is_bouquet:
        X_tr, y_tr = sample_balanced_bouquet(rng, g_tab, b_info, train_lengths, 560)
        X_val, y_val = sample_balanced_bouquet(rng, g_tab, b_info, eval_lengths, 440)
    else:
        X_tr, y_tr = sample_balanced_single_loop(rng, g_tab, train_lengths, 480)
        X_val, y_val = sample_balanced_single_loop(rng, g_tab, eval_lengths, 380)

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
            diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
            loss = loss + comp_w * (diff.abs() ** 2).mean()
        if alm_mode:
            loss = loss + m.alm_loss()
        loss.backward()
        opt.step()
        sched.step()
        if alm_mode and ((step + 1) % max(20, steps_p1 // 8) == 0):
            with torch.no_grad():
                R = m.relation_residual()
                m.alm_lam.add_(m.alm_rho * R)
                m.alm_rho = min(1536.0, m.alm_rho * 1.8)

    # For *_etf models: compute Phase-1 feature whitening W_white from Phase-1 training
    # distribution ONLY (no Phase-2 data, no replay stored), fit closed-form ridge init on
    # bias-free head H(bias=False) over whitened features Z = Phi @ W_white, then freeze W_white!
    m.eval()
    if use_etf:
        with torch.no_grad():
            Ub1 = m.unitary_bank()
            phi_list, y_list = [], []
            for L in train_lengths:
                phi_list.append(m.features_with_bank(Ub1, torch.tensor(X_tr[L], dtype=torch.long)))
                y_list.append(torch.tensor(y_tr[L], dtype=torch.long))
            Phi1 = torch.cat(phi_list, dim=0).to(torch.float64)
            Y1 = torch.cat(y_list, dim=0)
            Cov = (Phi1.T @ Phi1) / float(Phi1.shape[0])
            evals, evecs = torch.linalg.eigh(Cov)
            keep = evals > (1e-4 * evals.max())
            inv_sqrt = evecs[:, keep] @ torch.diag(1.0 / torch.sqrt(evals[keep])) @ evecs[:, keep].T
            m.W_white.copy_(inv_sqrt.to(torch.float32))
            Z1 = (Phi1 @ inv_sqrt).to(torch.float32)
            Y_oh = F.one_hot(Y1, num_classes=n_classes).to(torch.float32) * 3.0
            A_r = Z1.T @ Z1 + 1e-3 * torch.eye(Z1.shape[1], dtype=torch.float32)
            W_closed = torch.linalg.solve(A_r, Z1.T @ Y_oh).T  # (C, F)
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
            pred = logits.argmax(-1).numpy()
            eval_res[f"L{L}_bacc"] = balanced_accuracy(y_val[L], pred)

    # Phase-2 Unmodified Continual Learning on S_ft ONLY (NO replay, NO S_keep masking)
    keep_mask = np.isin(y_val[p2_len], s_keep)
    X_keep, y_keep = X_val[p2_len][keep_mask], y_val[p2_len][keep_mask]
    with torch.no_grad():
        before_keep = balanced_accuracy(
            y_keep,
            m(torch.tensor(X_keep, dtype=torch.long)).argmax(-1).numpy(),
            classes_present=s_keep,
        )
    if is_bouquet:
        X_ft, y_ft = sample_balanced_bouquet(rng, g_tab, b_info, [p2_len], 440, allowed_orbits=s_ft)
    else:
        X_ft, y_ft = sample_balanced_single_loop(rng, g_tab, [p2_len], 400, allowed_classes=s_ft)

    m.train()
    if use_etf:
        opt_ft = torch.optim.SGD(m.parameters(), lr=2e-2, momentum=0.0, weight_decay=0.0)
    else:
        opt_ft = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=0.0)

    for _ in range(steps_p2):
        opt_ft.zero_grad()
        idx = rng.integers(0, len(y_ft[p2_len]), size=64)
        xb = torch.tensor(X_ft[p2_len][idx], dtype=torch.long)
        yb = torch.tensor(y_ft[p2_len][idx], dtype=torch.long)
        loss_ft = F.cross_entropy(m(xb), yb)
        loss_ft.backward()
        opt_ft.step()

    m.eval()
    with torch.no_grad():
        Ub_after = m.unitary_bank()
        after_keep = balanced_accuracy(
            y_keep,
            m.forward_with_bank(Ub_after, torch.tensor(X_keep, dtype=torch.long)).argmax(-1).numpy(),
            classes_present=s_keep,
        )
        # Fresh post-Phase-2 probe on frozen backbone representations
        Phi_all = m.features_with_bank(Ub_after, torch.tensor(X_val[p2_len], dtype=torch.long))
        y_all = y_val[p2_len]
        split = len(y_all) // 2
        P_tr, Y_tr_p = Phi_all[:split], y_all[:split]
        P_te, Y_te_p = Phi_all[split:], y_all[split:]
        Y_oh_p = F.one_hot(torch.tensor(Y_tr_p, dtype=torch.long), num_classes=n_classes).to(torch.float32)
        A_pr = P_tr.T @ P_tr + 1e-3 * torch.eye(P_tr.shape[1], dtype=torch.float32)
        W_pr = torch.linalg.solve(A_pr, P_tr.T @ Y_oh_p)
        pred_pr = (P_te @ W_pr).argmax(-1).numpy()
        km_te = np.isin(Y_te_p, s_keep)
        probe_after_keep = balanced_accuracy(Y_te_p[km_te], pred_pr[km_te], classes_present=s_keep)

    return {
        "arm": f"Arm1_{group_name}",
        "group": group_name,
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
        "probe_after_keep": probe_after_keep,
    }


# =============================================================================
# Arm 2: Stochastic Interventional vs Passive POMDPs (`arXiv:2611.10501` + DPI)
# =============================================================================

def _tv_dist(p: np.ndarray, q: np.ndarray) -> float:
    return 0.5 * float(np.sum(np.abs(p - q)))


def run_arm2_pomdp_task(world_name: str, mode: str, seed: int, n_samples: int) -> dict:
    rng = np.random.default_rng((7100 if "hidden" in world_name else 8100) + seed * 37 + (0 if mode == "passive_sampling_probe" else 5))
    noises = [0.0, 0.15, 0.30]
    tv_ana_list, tv_emp_list, acc_list = [], [], []
    dpi_violations = 0

    for eta in noises:
        if world_name == "noisy_hidden_bit_pomdp":
            # Latent world (h, v) with visible bit v fixed to 0 so hidden bit h in {0, 1} controls transition
            if mode == "passive_sampling_probe":
                # Budget 0: can only read s0 = v = 0 (kernel collapses BOTH latent h=0,1 onto sign 0)
                K = np.array([[1.0, 1.0], [0.0, 0.0]], dtype=np.float64)
            else:
                # Budget 1: executes reveal action () -> noisy bit with slip eta: P(obs = h) = 1 - eta
                K = np.array([[1.0 - eta, eta], [eta, 1.0 - eta]], dtype=np.float64)
            p0 = np.array([1.0, 0.0])
            p1 = np.array([0.0, 1.0])
            q0 = K @ p0
            q1 = K @ p1
            tv_ana = _tv_dist(q0, q1)
            tv_prior = _tv_dist(p0, p1)
            if tv_ana > tv_prior + 1e-12:
                dpi_violations += 1
            # Draw finite Monte Carlo trajectories
            obs0 = rng.choice(2, size=n_samples, p=q0)
            obs1 = rng.choice(2, size=n_samples, p=q1)
            emp0 = np.bincount(obs0, minlength=2) / float(n_samples)
            emp1 = np.bincount(obs1, minlength=2) / float(n_samples)
            tv_emp = _tv_dist(emp0, emp1)
            # Bayes-optimal held-out accuracy predicting latent h from fresh test obs
            test0 = rng.choice(2, size=n_samples, p=q0)
            test1 = rng.choice(2, size=n_samples, p=q1)
            rule = (q1 >= q0).astype(np.int64)  # predict 1 if q1[o] >= q0[o] else 0 (ties -> first or unbiased)
            if np.allclose(q0, q1):
                # Tie-breaking constant predictor -> 0.50 balanced accuracy
                rule = np.zeros(2, dtype=np.int64)
            pred0 = rule[test0]
            pred1 = rule[test1]
            acc = 0.5 * (float(np.mean(pred0 == 0)) + float(np.mean(pred1 == 1)))
        else:
            # stochastic_s3_holonomy_pomdp: 3 conjugacy classes of S3 ({e}, {r, r^2}, {s, sr, sr^2})
            # Passive probe only observes parity sign chi_sgn in {+1 (even: e, r, r^2), -1 (odd: s..)}:
            # collapses classes 0 and 1 identically!
            # Active probe executes ordered test pair (s, r) under transition slip eta -> 3D outcome space
            p_classes = [np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0])]
            if mode == "passive_sampling_probe":
                # Outcomes 0: even parity, 1: odd parity, 2: unused -> K shape (3, 3)
                K = np.array([
                    [1.0 - eta, 1.0 - eta, eta],
                    [eta, eta, 1.0 - eta],
                    [0.0, 0.0, 0.0],
                ], dtype=np.float64)
            else:
                # Active distinguishing probe: class k stays at k with prob (1 - eta), slips uniformly to others with eta/2
                K = np.array([
                    [1.0 - eta, 0.5 * eta, 0.5 * eta],
                    [0.5 * eta, 1.0 - eta, 0.5 * eta],
                    [0.5 * eta, 0.5 * eta, 1.0 - eta],
                ], dtype=np.float64)
            qs = [K @ p for p in p_classes]
            # Mean pairwise TV between conjugacy classes (focusing also on hard unseparated pair 0 vs 1!)
            tv_ana = _tv_dist(qs[0], qs[1])
            if tv_ana > _tv_dist(p_classes[0], p_classes[1]) + 1e-12:
                dpi_violations += 1
            emps = []
            tests = []
            for k in range(3):
                tr = rng.choice(3, size=n_samples, p=qs[k])
                emps.append(np.bincount(tr, minlength=3) / float(n_samples))
                tests.append(rng.choice(3, size=n_samples, p=qs[k]))
            tv_emp = _tv_dist(emps[0], emps[1])
            Q_mat = np.stack(qs, axis=0)  # (3 classes, 3 obs)
            rule = np.argmax(Q_mat, axis=0)  # MAP Bayes classifier across 3 classes
            recs = [float(np.mean(rule[tests[k]] == k)) for k in range(3)]
            acc = float(np.mean(recs))

        tv_ana_list.append(tv_ana)
        tv_emp_list.append(tv_emp)
        acc_list.append(acc)

    return {
        "arm": "Arm2_POMDP",
        "world": world_name,
        "mode": mode,
        "seed": seed,
        "mean_tv_analytical": float(np.mean(tv_ana_list)),
        "mean_tv_empirical": float(np.mean(tv_emp_list)),
        "mean_acc": float(np.mean(acc_list)),
        "tv_eta000": float(tv_ana_list[0]),
        "tv_eta015": float(tv_ana_list[1]),
        "tv_eta030": float(tv_ana_list[2]),
        "acc_eta000": float(acc_list[0]),
        "acc_eta015": float(acc_list[1]),
        "acc_eta030": float(acc_list[2]),
        "dpi_violations": int(dpi_violations),
    }


# =============================================================================
# Arm 3: Exact Float64 Closure, Random-Channel TV DPI & Amortized KL Audits
# =============================================================================

def run_closure_audits() -> dict:
    rng = np.random.default_rng(20261123)
    s3 = make_s3_group()
    a4 = make_a4_group()
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))

    def rand_unitary(d):
        Z = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
        A = 0.5 * (Z - Z.conj().T)
        return expm(A)

    s3_hom_max, s3_u_max, trace_err_max = 0.0, 0.0, 0.0
    for _ in range(25):
        phi = float(rng.uniform(-math.pi, math.pi))
        V = rand_unitary(2)
        Gs = np.array([[0.0, np.exp(1j * phi)], [np.exp(-1j * phi), 0.0]], dtype=np.complex128)
        Gr = np.array([[omega, 0.0], [0.0, omega2]], dtype=np.complex128)
        Us = V @ Gs @ V.conj().T
        Ur = V @ Gr @ V.conj().T
        mats = [np.eye(2, dtype=np.complex128)]
        for w in s3["words"][1:]:
            M = Us if w[0] == 0 else Ur
            for sym in w[1:]:
                M = M @ (Us if sym == 0 else Ur)
            mats.append(M)
        for M in mats:
            s3_u_max = max(s3_u_max, float(np.linalg.norm(M @ M.conj().T - np.eye(2))))
        trace_err_max = max(trace_err_max, abs(complex(np.trace(Us) - np.trace(Gs))), abs(complex(np.trace(Ur) - np.trace(Gr))))
        for a in range(6):
            for b in range(6):
                s3_hom_max = max(s3_hom_max, float(np.linalg.norm(mats[a] @ mats[b] - mats[int(s3["mul"][a, b])])))

    a4_hom_max, a4_u_max = 0.0, 0.0
    for _ in range(25):
        phi1 = float(rng.uniform(-math.pi, math.pi))
        phi2 = float(rng.uniform(-math.pi, math.pi))
        V = rand_unitary(3)
        Gs = np.diag([1.0, -1.0, -1.0]).astype(np.complex128)
        Gt = np.array([
            [0.0, np.exp(1j * phi1), 0.0],
            [0.0, 0.0, np.exp(1j * phi2)],
            [np.exp(-1j * (phi1 + phi2)), 0.0, 0.0],
        ], dtype=np.complex128)
        Us = V @ Gs @ V.conj().T
        Ut = V @ Gt @ V.conj().T
        mats = [np.eye(3, dtype=np.complex128)]
        for w in a4["words"][1:]:
            M = Us if w[0] == 0 else Ut
            for sym in w[1:]:
                M = M @ (Us if sym == 0 else Ut)
            mats.append(M)
        for M in mats:
            a4_u_max = max(a4_u_max, float(np.linalg.norm(M @ M.conj().T - np.eye(3))))
        trace_err_max = max(trace_err_max, abs(complex(np.trace(Us) - np.trace(Gs))), abs(complex(np.trace(Ut) - np.trace(Gt))))
        for a in range(12):
            for b in range(12):
                a4_hom_max = max(a4_hom_max, float(np.linalg.norm(mats[a] @ mats[b] - mats[int(a4["mul"][a, b])])))

    # 50 random column-stochastic TV DPI checks
    dpi_excess_max = -1.0
    dpi_viols = 0
    for _ in range(50):
        n = int(rng.integers(2, 10))
        m = int(rng.integers(2, 10))
        K = rng.uniform(0.0, 1.0, size=(m, n))
        K = K / np.sum(K, axis=0, keepdims=True)
        p = rng.uniform(0.0, 1.0, size=n); p /= np.sum(p)
        q = rng.uniform(0.0, 1.0, size=n); q /= np.sum(q)
        ex = _tv_dist(K @ p, K @ q) - _tv_dist(p, q)
        dpi_excess_max = max(dpi_excess_max, ex)
        if ex > 1e-13:
            dpi_viols += 1

    # 50-trial amortized Matrix-KL variational gap: Tr(X (log X - log G0 + lam L)) - Tr(X) >= Opt
    kl_min_gap = float("inf")
    for _ in range(50):
        n = 6
        M0 = rng.normal(size=(n, n))
        G0 = expm(0.5 * (M0 + M0.T) * 0.3)
        ML = rng.normal(size=(n, n))
        L = 0.5 * (ML + ML.T) * 0.25
        L = L - np.trace(L) / n * np.eye(n)
        lam = float(rng.uniform(0.2, 2.0))
        Kmat = logm(G0).real - lam * L
        X_star = expm(Kmat)

        def free_e(X):
            vals, vecs = eigh(X)
            vals = np.clip(vals, 1e-12, None)
            logX = vecs @ np.diag(np.log(vals)) @ vecs.T
            return float(np.trace(X @ (logX - Kmat) - X))

        f_star = free_e(X_star)
        P_pert = rng.normal(size=(n, n)) * 0.15
        X_alt = expm(Kmat + 0.5 * (P_pert + P_pert.T))
        gap = free_e(X_alt) - f_star
        kl_min_gap = min(kl_min_gap, gap)

    return {
        "f64_s3_hom_err": s3_hom_max,
        "f64_s3_unitary_err": s3_u_max,
        "f64_a4_hom_err": a4_hom_max,
        "f64_a4_unitary_err": a4_u_max,
        "f64_pres_hom_err": max(s3_hom_max, a4_hom_max),
        "f64_trace_err": float(trace_err_max),
        "dpi_50channel_max_excess": float(dpi_excess_max),
        "dpi_50channel_violations": int(dpi_viols),
        "amortized_kl_50trial_min_gap": float(kl_min_gap),
        "algebraic_mdl_ratio_S3": 2.0 / 6.0,
        "algebraic_mdl_ratio_A4": 2.0 / 12.0,
    }


def _worker_task(job: tuple) -> dict:
    kind = job[0]
    if kind == "arm1":
        _, group_name, model_name, seed, s1, s2 = job
        return run_arm1_task(group_name, model_name, seed, s1, s2)
    elif kind == "arm2":
        _, world_name, mode, seed, n_samp = job
        return run_arm2_pomdp_task(world_name, mode, seed, n_samp)
    raise ValueError(kind)


def aggregate_and_judge(results: List[dict], audit: dict, total_elapsed_s: float) -> dict:
    arm1_agg = {}
    for gname in ("A4", "S3_bouquet"):
        arm1_agg[gname] = {}
        arm_tag = f"Arm1_{'A4' if gname == 'A4' else 'S3'}"
        models = sorted({r["model"] for r in results if r["arm"] == arm_tag})
        for mname in models:
            sub = [r for r in results if r["arm"] == arm_tag and r["model"] == mname]
            keys = [k for k in sub[0] if k not in ("arm", "group", "model", "seed")]
            arm1_agg[gname][mname] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    arm2_agg = {}
    for wname in ("noisy_hidden_bit_pomdp", "stochastic_s3_holonomy_pomdp"):
        arm2_agg[wname] = {}
        modes = sorted({r["mode"] for r in results if r["arm"] == "Arm2_POMDP" and r["world"] == wname})
        for md in modes:
            sub = [r for r in results if r["arm"] == "Arm2_POMDP" and r["world"] == wname and r["mode"] == md]
            keys = [k for k in sub[0] if k not in ("arm", "world", "mode", "seed")]
            arm2_agg[wname][md] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    # HMC.1
    a4_sd_etf = arm1_agg["A4"]["semidirect_exact_etf"]
    a4_sd_lin = arm1_agg["A4"]["semidirect_exact_linear"]
    s3_sd_etf = arm1_agg["S3_bouquet"]["semidirect_exact_etf"]
    s3_sd_lin = arm1_agg["S3_bouquet"]["semidirect_exact_linear"]
    a4_alm = arm1_agg["A4"]["spectral_alm_gen"]
    min_a4_sd = min(a4_sd_etf[f"L{L}_bacc"] for L in (4, 5, 6, 8, 12, 16, 24, 32))
    min_s3_sd = min(s3_sd_etf[f"L{L}_bacc"] for L in (3, 4, 6, 8, 12, 16))
    hmc1_exact = (
        max(a4_sd_etf["homomorphism_err"], a4_sd_lin["homomorphism_err"],
            s3_sd_etf["homomorphism_err"], s3_sd_lin["homomorphism_err"]) <= 1e-5
        and min(min_a4_sd, min_s3_sd) >= 0.995
        and a4_alm["homomorphism_err"] < 0.0178
    )
    hmc1_partial = (
        max(a4_sd_etf["homomorphism_err"], s3_sd_etf["homomorphism_err"]) <= 1e-5
        and min(min_a4_sd, min_s3_sd) >= 0.995
    )

    # HMC.2
    etf_a4_keep = a4_sd_etf["forgetting_after_keep"]
    etf_s3_keep = s3_sd_etf["forgetting_after_keep"]
    etf_a4_drop = a4_sd_etf["forgetting_drop"]
    etf_s3_drop = s3_sd_etf["forgetting_drop"]
    lin_a4_keep = a4_sd_lin["forgetting_after_keep"]
    cay_etf_a4_L32 = arm1_agg["A4"]["cayley_ufr_soft_etf"]["L32_bacc"]
    hmc2_exact = (
        min(etf_a4_keep, etf_s3_keep) >= 0.98
        and max(etf_a4_drop, etf_s3_drop) <= 0.02
        and (etf_a4_keep - lin_a4_keep) >= 0.25
        and (a4_sd_etf["L32_bacc"] - cay_etf_a4_L32) >= 0.55
    )
    hmc2_partial = (etf_a4_keep - lin_a4_keep) >= 0.25 or (a4_sd_etf["L32_bacc"] - cay_etf_a4_L32) >= 0.55

    # HMC.3
    tv_gaps = []
    acc_gaps = []
    total_pomdp_dpi_viols = 0
    for wname in ("noisy_hidden_bit_pomdp", "stochastic_s3_holonomy_pomdp"):
        act = arm2_agg[wname]["active_interventional_probe"]
        pas = arm2_agg[wname]["passive_sampling_probe"]
        tv_gaps.append(act["mean_tv_analytical"] - pas["mean_tv_analytical"])
        acc_gaps.append(act["mean_acc"] - pas["mean_acc"])
        total_pomdp_dpi_viols += int(act["dpi_violations"] + pas["dpi_violations"])
    hmc3 = min(tv_gaps) >= 0.30 and min(acc_gaps) >= 0.25 and total_pomdp_dpi_viols == 0

    # HMC.4
    a4_param_ratio = a4_sd_etf["n_params"] / arm1_agg["A4"]["cayley_unitary_ufr_soft"]["n_params"]
    hmc4 = (a4_sd_etf["mdl_ratio"] < 0.25) and (s3_sd_etf["mdl_ratio"] < 0.40) and (a4_param_ratio <= 0.50)

    # HMC.5
    max_neural_u_err = max(r["unitary_max_err"] for r in results if "unitary_max_err" in r)
    hmc5 = (
        audit["f64_pres_hom_err"] < 1e-14
        and audit["f64_trace_err"] < 1e-14
        and audit["dpi_50channel_max_excess"] <= 1e-14
        and audit["dpi_50channel_violations"] == 0
        and audit["amortized_kl_50trial_min_gap"] >= -1e-12
        and max_neural_u_err < 1e-5
    )

    def _v(exact: bool, partial: bool = False) -> str:
        if exact:
            return "HELD"
        return "NEITHER" if partial else "BROKEN"

    return {
        "verdicts": {
            "HMC.1": _v(hmc1_exact, hmc1_partial and not hmc1_exact),
            "HMC.2": _v(hmc2_exact, hmc2_partial and not hmc2_exact),
            "HMC.3": "HELD" if hmc3 else "BROKEN",
            "HMC.4": "HELD" if hmc4 else "BROKEN",
            "HMC.5": "HELD" if hmc5 else "BROKEN",
        },
        "total_runs": len(results),
        "total_elapsed_s": round(total_elapsed_s, 2),
        "max_neural_unitary_err": max_neural_u_err,
        "a4_param_ratio": a4_param_ratio,
        "audit": audit,
        "Arm1": arm1_agg,
        "Arm2": arm2_agg,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Fast smoke verification")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    t0 = time.time()
    audit = run_closure_audits()
    print(
        f"CLOSURE_AUDIT: f64_hom={audit['f64_pres_hom_err']:.2e}, "
        f"f64_tr={audit['f64_trace_err']:.2e}, "
        f"dpi50_ex={audit['dpi_50channel_max_excess']:.2e}, "
        f"kl_min={audit['amortized_kl_50trial_min_gap']:.2e}",
        flush=True,
    )

    seeds = [0] if args.smoke else [0, 1, 2]
    s1_a4 = 240 if args.smoke else 900
    s2_a4 = 120 if args.smoke else 360
    s1_s3 = 220 if args.smoke else 750
    s2_s3 = 100 if args.smoke else 300
    n_pomdp = 400 if args.smoke else 2000

    jobs = []
    for m in ("cayley_unitary_ufr_soft", "cayley_ufr_soft_etf", "spectral_alm_gen", "semidirect_exact_linear", "semidirect_exact_etf"):
        for sd in seeds:
            jobs.append(("arm1", "A4", m, sd, s1_a4, s2_a4))
    for m in ("cayley_unitary_ufr_soft", "spectral_alm_gen", "semidirect_exact_linear", "semidirect_exact_etf"):
        for sd in seeds:
            jobs.append(("arm1", "S3", m, sd, s1_s3, s2_s3))
    for wname in ("noisy_hidden_bit_pomdp", "stochastic_s3_holonomy_pomdp"):
        for md in ("passive_sampling_probe", "active_interventional_probe"):
            for sd in seeds:
                jobs.append(("arm2", wname, md, sd, n_pomdp))

    results = []
    temp_dir = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "semplex_trash_oleans"
    raw_dir = temp_dir / f"mp_closure_raw_{time.strftime('%Y%m%d_%H%M%S')}"
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
        out_path = pathlib.Path(__file__).resolve().parent / "results" / "master_principle_closure.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
        print(f"Saved summary -> {out_path} (raw archived at {raw_dir})", flush=True)
    else:
        print("Smoke run summary:", json.dumps({
            "A4_sd_etf_L32": summary["Arm1"]["A4"]["semidirect_exact_etf"]["L32_bacc"],
            "A4_sd_etf_hom": summary["Arm1"]["A4"]["semidirect_exact_etf"]["homomorphism_err"],
            "A4_sd_etf_keep_after": summary["Arm1"]["A4"]["semidirect_exact_etf"]["forgetting_after_keep"],
            "A4_sd_lin_keep_after": summary["Arm1"]["A4"]["semidirect_exact_linear"]["forgetting_after_keep"],
            "A4_cayley_etf_L32": summary["Arm1"]["A4"]["cayley_ufr_soft_etf"]["L32_bacc"],
            "A4_cayley_etf_keep_after": summary["Arm1"]["A4"]["cayley_ufr_soft_etf"]["forgetting_after_keep"],
            "A4_alm_hom": summary["Arm1"]["A4"]["spectral_alm_gen"]["homomorphism_err"],
            "A4_alm_L32": summary["Arm1"]["A4"]["spectral_alm_gen"]["L32_bacc"],
            "S3_sd_etf_L16": summary["Arm1"]["S3_bouquet"]["semidirect_exact_etf"]["L16_bacc"],
            "S3_sd_etf_hom": summary["Arm1"]["S3_bouquet"]["semidirect_exact_etf"]["homomorphism_err"],
            "S3_sd_etf_keep_after": summary["Arm1"]["S3_bouquet"]["semidirect_exact_etf"]["forgetting_after_keep"],
            "POMDP_hidden_active_tv": summary["Arm2"]["noisy_hidden_bit_pomdp"]["active_interventional_probe"]["mean_tv_analytical"],
            "POMDP_hidden_passive_tv": summary["Arm2"]["noisy_hidden_bit_pomdp"]["passive_sampling_probe"]["mean_tv_analytical"],
            "POMDP_s3_active_acc": summary["Arm2"]["stochastic_s3_holonomy_pomdp"]["active_interventional_probe"]["mean_acc"],
            "POMDP_s3_passive_acc": summary["Arm2"]["stochastic_s3_holonomy_pomdp"]["passive_sampling_probe"]["mean_acc"],
        }, indent=2), flush=True)


if __name__ == "__main__":
    main()
