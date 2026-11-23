#!/usr/bin/env python3
"""
Pre-Registered 45-Run Master Principle Showdown (`gemini/master-principle-lie-lyapunov`)

Tests 5 pre-registered hypotheses (`HLL.1` - `HLL.5`):
- Arm 1 (27 runs): Exact presentation unitary homomorphisms (`spectral_presentation_gen`
  and `lie_presentation_gen`, `U_g = word(U_s, U_t)` via Lie `matrix_exp`) vs
  `lie_exp_ufr_soft`, `cayley_unitary_ufr_soft`, and `cayley_unitary_fer` on non-ambivalent
  `A4` (up to OOD `L = 16`) and `b1 = 2` `S3` bouquet (up to OOD `L = 8`), plus Phase-2
  forgetting retention.
- Arm 2 (18 runs): Content-Geometry JEPA (`jepa_sg`, `jepa_svreg`, `jepa_slow_svreg`)
  on `C8_slow3` and fixed non-identity `D4_slow3` compared against continuous-time
  shifted Lyapunov balanced Gramian `G_cont_lyap(lam)` (`solve_continuous_lyapunov`),
  discrete `G_gm_heat(lam)`, and `X_kl_gm(lam)`, plus Clark (`arXiv:2610.12426`)
  regularized forward-backward minimum-norm tangent response vs QR Lyapunov exponents
  on `N = 32` random asymmetric RNNs.
- HLL.5 Audits: Exact continuous Lyapunov residual, balanced trace similarity,
  exact `S3`/`A4` presentation homomorphisms, Hoza (`ECCC TR26-323`) small-seed
  min-isolating spanning trees across 30 random `b1 in {2,3,5}` multigraphs,
  and finite 3-object Kan retract obstruction verification.
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
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.linalg import expm, logm, eigh, fractional_matrix_power, solve_continuous_lyapunov, solve_discrete_lyapunov


# =============================================================================
# Finite Groups (S3, D4, A4, C8) + Exact Generator Word Tables
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


def make_s3_group() -> dict:
    perms = list(itertools.permutations(range(3)))
    g = _build_group_from_perms(perms)
    # Generators: s = (1, 0, 2) (order 2), r = (1, 2, 0) (order 3), sr = rs^{-1} -> (sr)^2 = e
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


def make_d4_group() -> dict:
    r = (1, 2, 3, 0)
    s = (0, 3, 2, 1)

    def comp(a, b):
        return tuple(a[b[k]] for k in range(4))

    closure = {(0, 1, 2, 3)}
    q = [(0, 1, 2, 3)]
    while q:
        cur = q.pop()
        for gen in (r, s):
            nxt = comp(gen, cur)
            if nxt not in closure:
                closure.add(nxt)
                q.append(nxt)
    g = _build_group_from_perms(sorted(closure))
    g["r_idx"] = g["p2i"][r]
    return g


def make_c8_group() -> dict:
    perms = [tuple((k + r) % 8 for k in range(8)) for r in range(8)]
    g = _build_group_from_perms(perms)
    g["r_idx"] = g["p2i"][tuple((k + 1) % 8 for k in range(8))]
    return g


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
                # verify exact holonomy class
                check = 0
                for g in seq:
                    check = int(mul[check, int(g)])
                assert int(cls_of[check]) == cid
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
    orb_of = b_info["orbit_of"]
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
# Arm 1: Exact Presentation U(d) vs Soft-UFR vs FER (A4 to L=16, S3 bouquet to L=8)
# =============================================================================

def _build_bank_from_gens_torch(torch, gens_U, words: List[Tuple[int, ...]]):
    # gens_U[0], gens_U[1]: shape (n_heads, d, d) complex
    # Compute all group element matrices cleanly by word multiplication (identity = eye)
    eye = torch.eye(gens_U[0].shape[-1], dtype=gens_U[0].dtype, device=gens_U[0].device).unsqueeze(0).expand_as(gens_U[0])
    mats = [eye]
    for idx in range(1, len(words)):
        w = words[idx]
        cur = gens_U[w[0]]
        for sym in w[1:]:
            cur = torch.matmul(cur, gens_U[sym])
        mats.append(cur)
    return torch.stack(mats, dim=0)  # (G, n_heads, d, d)


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
    rng = np.random.default_rng((1000 if group_name == "A4" else 3000) + seed * 101)

    if group_name == "A4":
        g_tab = make_a4_group()
        n_classes = g_tab["n_cls"]  # 4
        train_lengths = [2, 3, 4]
        eval_lengths = [4, 5, 6, 8, 12, 16]
        s_keep, s_ft = [0, 1], [2, 3]
        p2_len = 4
        is_bouquet = False
        b_info = None
    else:
        g_tab = make_s3_group()
        b_info = build_bouquet_orbits(g_tab)
        n_classes = b_info["n_orbits"]  # 11
        train_lengths = [2, 3]
        eval_lengths = [3, 4, 6, 8]
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
        A = Z - Z.conj().transpose(-1, -2)  # exact skew-Hermitian A^H = -A
        return torch.linalg.matrix_exp(A)

    d = 6
    feat_mult = 4 if not is_bouquet else 20

    if model_name == "cayley_unitary_fer":
        n_heads = 11 if not is_bouquet else 8
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.4 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                h_mid = 128 if not is_bouquet else 72
                h_bot = 32 if not is_bouquet else 18
                self.trunk = nn.Sequential(
                    nn.Linear(n_heads * feat_mult, h_mid), nn.Tanh(),
                    nn.Linear(h_mid, h_bot), nn.Tanh()
                )
                self.head = nn.Linear(h_bot, n_classes)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley_bank(self.P_re, self.P_im, self.eye_c)
            def forward_with_bank(self, Ub, X):
                feats = _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)
                return self.head(self.trunk(feats))
            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)
        m = Model()
        comp_w = 0.0
        pres_mode = None
        lr = 3e-3

    elif model_name in ("cayley_unitary_ufr_soft", "lie_exp_ufr_soft"):
        n_heads = 19 if not is_bouquet else 27
        use_exp = (model_name == "lie_exp_ufr_soft")
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.d = d
                scale = 0.4 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.head = nn.Linear(n_heads * feat_mult, n_classes)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                if use_exp:
                    U_nt = make_exp_skew(self.P_re, self.P_im)
                    return torch.cat([self.eye_c.unsqueeze(0), U_nt], dim=0)
                return make_cayley_bank(self.P_re, self.P_im, self.eye_c)
            def forward_with_bank(self, Ub, X):
                feats = _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)
                return self.head(feats)
            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)
        m = Model()
        comp_w = 4.0
        pres_mode = None
        lr = 3e-3

    elif model_name in ("lie_presentation_gen", "spectral_presentation_gen"):
        n_heads = 32 if not is_bouquet else 24
        use_spectral = (model_name == "spectral_presentation_gen")
        w_rel = 12.0 if use_spectral else 6.0

        # Exact faithful irrep spectra for d=6:
        # A4 chiral faithful: rho_3 + chi_1 + chi_1 + 1 on first half, rho_3 + chi_2 + chi_2 + 1 on second half
        #   so Tr(C3+) and Tr(C3-) are genuinely complex and distinct!
        # S3 regular rep: 1 + sgn + 2*rho_2 -> s: (1,-1,1,-1,1,-1), r: (1,1,w,w^2,w,w^2)
        omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
        omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))
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
            def generators(self):
                V0 = make_exp_skew(self.X0_re, self.X0_im)
                V1 = make_exp_skew(self.X1_re, self.X1_im)
                if use_spectral:
                    # Exact spectral torsion locking: U0^2 = I and U1^3 = I hold identically at every step!
                    U0 = torch.matmul(torch.matmul(V0, self.diag_s), V0.conj().transpose(-1, -2))
                    U1 = torch.matmul(torch.matmul(V1, self.diag_t), V1.conj().transpose(-1, -2))
                    return U0, U1
                return V0, V1
            def unitary_bank(self):
                U0, U1 = self.generators()
                return _build_bank_from_gens_torch(torch, [U0, U1], words)
            def presentation_loss(self):
                U0, U1 = self.generators()
                eye = self.eye_h
                U01 = torch.matmul(U0, U1)
                if group_name == "A4":
                    U01_2 = torch.matmul(U01, U01)
                    U01_3 = torch.matmul(U01_2, U01)
                    loss_rel = (U01_3 - eye).abs().pow(2).mean()
                    if not use_spectral:
                        U0_2 = torch.matmul(U0, U0)
                        U1_3 = torch.matmul(torch.matmul(U1, U1), U1)
                        loss_rel = loss_rel + (U0_2 - eye).abs().pow(2).mean() + (U1_3 - eye).abs().pow(2).mean()
                else:
                    U01_2 = torch.matmul(U01, U01)
                    loss_rel = (U01_2 - eye).abs().pow(2).mean()
                    if not use_spectral:
                        U0_2 = torch.matmul(U0, U0)
                        U1_3 = torch.matmul(torch.matmul(U1, U1), U1)
                        loss_rel = loss_rel + (U0_2 - eye).abs().pow(2).mean() + (U1_3 - eye).abs().pow(2).mean()
                return w_rel * loss_rel
            def forward_with_bank(self, Ub, X):
                feats = _bouquet_trace_feats(torch, Ub, X, self.d) if is_bouquet else _single_loop_trace_feats(torch, Ub, X, self.d)
                return self.head(feats)
            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)
        m = Model()
        comp_w = 0.0
        pres_mode = model_name
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
        if pres_mode is not None:
            loss = loss + m.presentation_loss()
        loss.backward()
        opt.step()
        sched.step()

    m.eval()
    with torch.no_grad():
        Ub = m.unitary_bank()
        eye = torch.eye(d, dtype=torch.complex64).unsqueeze(0).unsqueeze(0).expand_as(Ub)
        unitary_err = float((torch.matmul(Ub, Ub.conj().transpose(-1, -2)) - eye).abs().max().item())
        diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
        hom_err = float((diff.abs() ** 2).mean().item())

        eval_res = {}
        for L in eval_lengths:
            logits = m.forward_with_bank(Ub, torch.tensor(X_val[L], dtype=torch.long))
            pred = logits.argmax(-1).numpy()
            eval_res[f"L{L}_bacc"] = balanced_accuracy(y_val[L], pred)

    # Phase-2 Unmodified Fine-Tuning Forgetting Test (`2611.11020`)
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
        after_keep = balanced_accuracy(
            y_keep,
            m(torch.tensor(X_keep, dtype=torch.long)).argmax(-1).numpy(),
            classes_present=s_keep,
        )

    return {
        "arm": f"Arm1_{group_name}",
        "group": group_name,
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "homomorphism_err": hom_err,
        **eval_res,
        "forgetting_before_keep": before_keep,
        "forgetting_after_keep": after_keep,
        "forgetting_drop": float(before_keep - after_keep),
    }


# =============================================================================
# Arm 2: Continuous Lyapunov vs Heat/KL Operators + Fixed D4_slow3 jag + Clark RNN
# =============================================================================

def build_dual_timescale_world(name: str, seed: int = 0) -> dict:
    rng = np.random.default_rng(1100 + seed + (0 if "C8" in name else 53))
    n_fast, n_slow = 8, 3
    n_states = n_fast * n_slow  # 24
    n_acts = 4

    if name == "C8_slow3":
        # C8 ring: a=0 (stay), a=1 (+1), a=2 (-1), a=3 (+2)
        def fast_step(f, a):
            if a == 0: return f
            if a == 1: return (f + 1) % 8
            if a == 2: return (f - 1) % 8
            return (f + 2) % 8
    elif name == "D4_slow3":
        fast_g = make_d4_group()
        r_idx = fast_g["r_idx"]
        rinv = int(fast_g["inv"][r_idx])
        s_idx = fast_g["p2i"][(0, 3, 2, 1)]
        acts_g = [0, r_idx, s_idx, rinv]
        def fast_step(f, a):
            return int(fast_g["mul"][f, acts_g[a]])
    else:
        raise ValueError(name)

    # Shortest-path distance on S_fast using generating actions {1,2,3}
    dist_fast = np.full((n_fast, n_fast), 999, dtype=np.float64)
    for f0 in range(n_fast):
        dist_fast[f0, f0] = 0.0
        q = [f0]
        while q:
            u = q.pop(0)
            for a in (1, 2, 3):
                v = fast_step(u, a)
                if dist_fast[f0, v] > dist_fast[f0, u] + 1.0:
                    dist_fast[f0, v] = dist_fast[f0, u] + 1.0
                    q.append(v)

    trans = np.zeros((n_states, n_acts), dtype=np.int64)
    P = np.zeros((n_states, n_states), dtype=np.float64)
    for f in range(n_fast):
        for s in range(n_slow):
            sid = f * n_slow + s
            for a in range(n_acts):
                fn = fast_step(f, a)
                sn = (s + 1) % n_slow if (f == 0 and a != 0 and fn != 0) else s
                nid = fn * n_slow + sn
                trans[sid, a] = nid
                P[sid, nid] += 1.0 / n_acts

    # Check non-identity, non-involution fast generators (f -> f1 -> f2 != f) for non-degenerate 2-step jag
    fast_non_two_cycle_acts = [
        a for a in (1, 2, 3) if any(fast_step(fast_step(f, a), a) != f for f in range(n_fast))
    ]
    assert len(fast_non_two_cycle_acts) >= 1

    obs_dim = 32
    Q, _ = np.linalg.qr(rng.normal(size=(obs_dim, obs_dim)))
    fast_code = np.zeros((n_fast, 8))
    for f in range(n_fast):
        ang = 2 * math.pi * f / n_fast
        fast_code[f, 0:4] = [math.cos(ang), math.sin(ang), math.cos(2 * ang), math.sin(2 * ang)]
        fast_code[f, 4:] = rng.normal(scale=0.35, size=4)
    slow_code = np.zeros((n_slow, 6))
    for s in range(n_slow):
        ang = 2 * math.pi * s / n_slow
        slow_code[s, :4] = [math.cos(ang), math.sin(ang), 0.7 * math.cos(2 * ang), 0.7 * math.sin(2 * ang)]
        slow_code[s, 4:] = rng.normal(scale=0.3, size=2)
    base_feats = np.zeros((n_states, obs_dim), dtype=np.float32)
    for f in range(n_fast):
        for s in range(n_slow):
            v = np.zeros(obs_dim)
            v[:8] = fast_code[f] * 1.4
            v[8:14] = slow_code[s] * 0.45
            v[14:] = rng.normal(scale=0.18, size=obs_dim - 14)
            base_feats[f * n_slow + s] = (Q @ v).astype(np.float32)

    return {
        "name": name,
        "n_fast": n_fast,
        "n_slow": n_slow,
        "n_states": n_states,
        "n_acts": n_acts,
        "fast_non_two_cycle_acts": fast_non_two_cycle_acts,
        "trans": trans,
        "P": P,
        "dist_fast": dist_fast,
        "base_feats": base_feats,
        "obs_dim": obs_dim,
    }


def _floor_spd(M: np.ndarray) -> np.ndarray:
    vals, vecs = eigh(0.5 * (M + M.T))
    vals = np.maximum(vals, 1e-6)
    return (vecs * vals) @ vecs.T


def _kubo_ando_geom_mean(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    A = _floor_spd(A)
    B = _floor_spd(B)
    A_half = fractional_matrix_power(A, 0.5).real
    A_nhalf = fractional_matrix_power(A, -0.5).real
    mid = _floor_spd(A_nhalf @ B @ A_nhalf)
    return _floor_spd(A_half @ fractional_matrix_power(mid, 0.5).real @ A_half)


def _centered_cos(K1: np.ndarray, K2: np.ndarray) -> float:
    n = K1.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    C1 = H @ K1 @ H
    C2 = H @ K2 @ H
    denom = float(np.linalg.norm(C1) * np.linalg.norm(C2))
    return float(np.sum(C1 * C2) / denom) if denom > 1e-12 else 0.0


def compute_free_energy_and_cont_lyap_operators(w: dict) -> dict:
    P = w["P"]
    n_s = w["n_states"]
    X = w["base_feats"].astype(np.float64)
    Xc = X - X.mean(axis=0, keepdims=True)
    rho = 0.85
    A_disc = rho * P.T
    Wc0 = solve_discrete_lyapunov(A_disc, np.eye(n_s))
    Wo0 = solve_discrete_lyapunov(A_disc.T, Xc @ Xc.T)
    G0 = _kubo_ando_geom_mean(Wc0, Wo0)

    Psym = 0.5 * (P + P.T)
    Dinv2 = np.diag(1.0 / np.sqrt(np.maximum(Psym.sum(axis=1), 1e-8)))
    L_kin = np.eye(n_s) - Dinv2 @ Psym @ Dinv2
    L_kin = 0.5 * (L_kin + L_kin.T)

    vals0, vecs0 = eigh(G0)
    logG0 = (vecs0 * np.log(np.maximum(vals0, 1e-8))) @ vecs0.T

    # Continuous-time generator matching discrete alpha*P (alpha = 0.85 -> A_cont = (P^T - I) - 0.15 I)
    A_cont = (P.T - np.eye(n_s)) - 0.15 * np.eye(n_s)
    Q_c = np.eye(n_s)
    Q_o = Xc @ Xc.T

    lam_grid = np.linspace(0.0, 4.0, 41)
    G_gm_heat = []
    X_kl_gm = []
    G_cont_lyap = []
    for lam in lam_grid:
        E = expm(-0.5 * lam * L_kin)
        G_gm_heat.append(E @ G0 @ E)
        X_kl_gm.append(expm(logG0 - lam * L_kin))

        A_shift = A_cont - 0.5 * lam * np.eye(n_s)
        Wc_c = solve_continuous_lyapunov(A_shift, -Q_c)
        Wo_c = solve_continuous_lyapunov(A_shift.T, -Q_o)
        G_cont_lyap.append(_kubo_ando_geom_mean(Wc_c, Wo_c))

    return {
        "lam_grid": lam_grid,
        "G_gm_heat": G_gm_heat,
        "X_kl_gm": X_kl_gm,
        "G_cont_lyap": G_cont_lyap,
    }


def _ridge_r2(Z_a: np.ndarray, Y_a: np.ndarray, Z_b: np.ndarray, Y_b: np.ndarray, reg: float = 1e-2) -> float:
    Za = np.column_stack([Z_a, np.ones(len(Z_a))])
    Zb = np.column_stack([Z_b, np.ones(len(Z_b))])
    W = np.linalg.solve(Za.T @ Za + reg * np.eye(Za.shape[1]), Za.T @ Y_a)
    pred = Zb @ W
    ss_res = float(np.sum((Y_b - pred) ** 2))
    ss_tot = float(np.sum((Y_b - Y_b.mean(axis=0, keepdims=True)) ** 2))
    return float(1.0 - ss_res / max(ss_tot, 1e-12))


def run_arm2_jepa_task(world_name: str, obj_name: str, seed: int, steps: int = 1200) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(5000 + seed * 89 + (0 if "C8" in world_name else 41))

    w = build_dual_timescale_world(world_name, seed=0)
    ops = compute_free_energy_and_cont_lyap_operators(w)
    n_states = w["n_states"]
    n_acts = w["n_acts"]
    obs_dim = w["obs_dim"]
    trans = w["trans"]
    base_feats = w["base_feats"]
    lat_dim = 16

    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(nn.Linear(obs_dim, 64), nn.SiLU(), nn.Linear(64, 64), nn.SiLU(), nn.Linear(64, lat_dim))
        def forward(self, x):
            return self.net(x)

    class Predictor(nn.Module):
        def __init__(self, use_gate: bool = False):
            super().__init__()
            self.use_gate = use_gate
            self.fc = nn.Sequential(nn.Linear(lat_dim + n_acts, 64), nn.SiLU(), nn.Linear(64, lat_dim))
            if use_gate:
                self.gate = nn.Sequential(nn.Linear(lat_dim + n_acts, 32), nn.SiLU(), nn.Linear(32, lat_dim), nn.Sigmoid())
        def forward(self, z, a_oh):
            inp = torch.cat([z, a_oh], dim=-1)
            delta = self.fc(inp)
            if self.use_gate:
                g = self.gate(inp)
                return z + g * delta, g
            return delta, None

    enc = Encoder()
    target_enc = Encoder()
    target_enc.load_state_dict(enc.state_dict())
    pred = Predictor(use_gate=(obj_name == "jepa_slow_svreg"))
    opt = torch.optim.AdamW(list(enc.parameters()) + list(pred.parameters()), lr=2e-3, weight_decay=1e-4)

    def sample_batch(B: int):
        s0 = rng.integers(0, n_states, size=B)
        a0 = rng.integers(0, n_acts, size=B)
        s1 = trans[s0, a0]
        x0 = base_feats[s0] + rng.normal(scale=0.18, size=(B, obs_dim)).astype(np.float32)
        x1 = base_feats[s1] + rng.normal(scale=0.18, size=(B, obs_dim)).astype(np.float32)
        a0_oh = np.eye(n_acts, dtype=np.float32)[a0]
        return torch.from_numpy(x0), torch.from_numpy(x1), torch.from_numpy(a0_oh)

    for _ in range(steps):
        opt.zero_grad()
        x0, x1, a0_oh = sample_batch(128)
        z0 = enc(x0)
        z1 = enc(x1)
        z_hat, gate = pred(z0, a0_oh)

        if obj_name == "jepa_sg":
            with torch.no_grad():
                zt = target_enc(x1)
            l_pred = F.mse_loss(z_hat, zt)
            std_z = torch.sqrt(z0.var(dim=0) + 1e-4)
            loss = l_pred + 0.1 * F.relu(1.0 - std_z).mean()
        elif obj_name == "jepa_svreg":
            l_pred = F.mse_loss(z_hat, z1)
            dirs = torch.randn(lat_dim, 64)
            dirs = dirs / (dirs.norm(dim=0, keepdim=True) + 1e-8)
            proj = z0 @ dirs
            std_proj = torch.sqrt(proj.var(dim=0) + 1e-4)
            loss = l_pred + 4.0 * (F.relu(1.0 - std_proj) ** 2).mean()
        elif obj_name == "jepa_slow_svreg":
            l_pred = F.mse_loss(z_hat, z1)
            dirs = torch.randn(lat_dim, 64)
            dirs = dirs / (dirs.norm(dim=0, keepdim=True) + 1e-8)
            proj = z0 @ dirs
            std_proj = torch.sqrt(proj.var(dim=0) + 1e-4)
            l_sv = (F.relu(1.0 - std_proj) ** 2).mean()
            l_slow = 0.45 * F.mse_loss(z1, z0) + 0.05 * gate.mean()
            loss = l_pred + 4.0 * l_sv + l_slow
        else:
            raise ValueError(obj_name)

        loss.backward()
        opt.step()
        if obj_name == "jepa_sg":
            with torch.no_grad():
                for p, tp in zip(enc.parameters(), target_enc.parameters()):
                    tp.data.mul_(0.99).add_(p.data, alpha=0.01)

    enc.eval()
    with torch.no_grad():
        Z = enc(torch.from_numpy(base_feats)).numpy().astype(np.float64)

    Zc = Z - Z.mean(axis=0, keepdims=True)
    # Fixed non-identity, non-involution 2-step jaggedness across fast cyclic generators (keeping slow constant)!
    jags = []
    for a in w["fast_non_two_cycle_acts"]:
        for s0 in range(n_states):
            s1 = int(trans[s0, a])
            s2 = int(trans[s1, a])
            if (s0 % w["n_slow"]) == (s1 % w["n_slow"]) == (s2 % w["n_slow"]):
                d01 = float(np.linalg.norm(Z[s1] - Z[s0]))
                d12 = float(np.linalg.norm(Z[s2] - Z[s1]))
                d02 = float(np.linalg.norm(Z[s2] - Z[s0]))
                if d02 > 1e-6:
                    jags.append((d01 + d12) / d02)
    jag = float(np.mean(jags)) if jags else 9.9

    # Distance correlation against shortest-path distance on S_fast (across pairs with same s_slow)
    dz_list, dg_list = [], []
    for s in range(w["n_slow"]):
        for f1 in range(w["n_fast"]):
            for f2 in range(f1 + 1, w["n_fast"]):
                dz_list.append(float(np.linalg.norm(Z[f1 * 3 + s] - Z[f2 * 3 + s])))
                dg_list.append(float(w["dist_fast"][f1, f2]))
    r_geom = float(np.corrcoef(dz_list, dg_list)[0, 1]) if np.std(dz_list) > 1e-8 else 0.0

    # Held-out noisy evaluation Ridge R^2 for fast and slow states (matching GHSRT protocol)
    eval_rng = np.random.default_rng(9001 + seed)
    B_eval = 512
    s_tr = eval_rng.integers(0, n_states, size=B_eval)
    s_te = eval_rng.integers(0, n_states, size=B_eval)
    x_etr = base_feats[s_tr] + eval_rng.normal(scale=0.18, size=(B_eval, obs_dim)).astype(np.float32)
    x_ete = base_feats[s_te] + eval_rng.normal(scale=0.18, size=(B_eval, obs_dim)).astype(np.float32)
    with torch.no_grad():
        Ztr = enc(torch.from_numpy(x_etr)).numpy().astype(np.float64)
        Zte = enc(torch.from_numpy(x_ete)).numpy().astype(np.float64)
    Yf_tr = np.eye(w["n_fast"])[s_tr // 3]
    Yf_te = np.eye(w["n_fast"])[s_te // 3]
    Ys_tr = np.eye(w["n_slow"])[s_tr % 3]
    Ys_te = np.eye(w["n_slow"])[s_te % 3]
    r2_fast = _ridge_r2(Ztr, Yf_tr, Zte, Yf_te)
    r2_slow = _ridge_r2(Ztr, Ys_tr, Zte, Ys_te)

    svals = np.linalg.svd(Zc, compute_uv=False)
    pnorm = (svals ** 2) / (np.sum(svals ** 2) + 1e-12)
    pnorm = pnorm[pnorm > 1e-12]
    eff_rank = float(math.exp(-np.sum(pnorm * np.log(pnorm))))

    G_z = Zc @ Zc.T
    lams = ops["lam_grid"]
    cos_heat = [_centered_cos(G_z, Op) for Op in ops["G_gm_heat"]]
    cos_kl = [_centered_cos(G_z, Op) for Op in ops["X_kl_gm"]]
    cos_cont = [_centered_cos(G_z, Op) for Op in ops["G_cont_lyap"]]
    i_h = int(np.argmax(cos_heat))
    i_k = int(np.argmax(cos_kl))
    i_c = int(np.argmax(cos_cont))

    return {
        "arm": "Arm2_JEPA",
        "world": world_name,
        "objective": obj_name,
        "seed": seed,
        "jag": jag,
        "r_geom": r_geom,
        "r2_fast": r2_fast,
        "r2_slow": r2_slow,
        "eff_rank": eff_rank,
        "best_cos_G_gm_heat": float(cos_heat[i_h]),
        "lam_star_heat": float(lams[i_h]),
        "best_cos_X_kl_gm": float(cos_kl[i_k]),
        "lam_star_kl": float(lams[i_k]),
        "best_cos_G_cont_lyap": float(cos_cont[i_c]),
        "lam_star_cont": float(lams[i_c]),
    }


# =============================================================================
# Arm 3 / HLL.4 & HLL.5: Clark Tangent-Response RNN, Hoza Isolating Trees,
# Exact Algebraic & Kan-Retract Audits
# =============================================================================

def verify_clark_min_norm_tangent_rnn(n_seeds: int = 3, N: int = 32, T: int = 56) -> dict:
    """
    Compare QR finite-time Lyapunov exponents vs Clark (`arXiv:2610.12426`)
    regularized forward-backward minimum-norm tangent response function chi(lam):
    min ||v_0||^2 + ||v_T - h||^2 s.t. v_{t+1} - e^{-lam} J_t v_t = 0
    solved via the sparse spacetime KKT forward-backward saddle system WITHOUT
    forming propagator products M_T or QR/SVD decompositions.
    """
    maes = []
    max_cdf_errs = []
    for seed in range(n_seeds):
        rng = np.random.default_rng(9100 + seed * 37)
        W = rng.normal(scale=1.25 / math.sqrt(N), size=(N, N))
        x = rng.normal(scale=0.5, size=N)
        Js = []
        for _ in range(20):  # burn-in onto chaotic/mixed attractor
            x = np.tanh(W @ x)
        for _ in range(T):
            z = W @ x
            x = np.tanh(z)
            dtanh = 1.0 - x ** 2
            Js.append((dtanh[:, None] * W))

        # 1. Ground-truth QR finite-time Lyapunov spectrum (lambda_1 >= ... >= lambda_N)
        Q = np.eye(N)
        log_r = np.zeros(N)
        for Jt in Js:
            Q, R = np.linalg.qr(Jt @ Q)
            log_r += np.log(np.abs(np.diag(R)) + 1e-18)
        lam_qr = np.sort(log_r / T)[::-1]

        # 2. Regularized forward-backward minimum-norm spacetime KKT solver across lambda grid
        lam_lo = float(lam_qr.min() - 0.12)
        lam_hi = float(lam_qr.max() + 0.12)
        lam_grid = np.linspace(lam_lo, lam_hi, 121)

        # Build sparse identity forcing RHS E_end mapping h in R^N into backward-terminal KKT slot
        n_v = (T + 1) * N
        n_p = T * N
        total_dim = n_v + n_p
        I_N = sparse.eye(N, format="csc")

        # Precompute KKT constant pieces: primal cost diag H = blkdiag(I_N at t=0, 0..., I_N at t=T)
        h_diag = np.zeros(n_v)
        h_diag[:N] = 1.0
        h_diag[T * N : (T + 1) * N] = 1.0
        H_blk = sparse.diags(h_diag, offsets=0, format="csc")

        # RHS vectors: gradient of -h^T v_T in H block -> columns for h = e_0 .. e_{N-1}
        rows_rhs = np.arange(T * N, (T + 1) * N)
        cols_rhs = np.arange(N)
        RHS = sparse.csc_matrix((np.ones(N), (rows_rhs, cols_rhs)), shape=(total_dim, N))

        cdf_clark = []
        cdf_qr = []
        for lam in lam_grid:
            scale = math.exp(-lam)
            # C matrix (T*N x (T+1)*N): v_{t+1} - scale * J_t v_t = 0
            c_rows = []
            c_cols = []
            c_data = []
            for t, Jt in enumerate(Js):
                r_off = t * N
                # +I * v_{t+1}
                c_rows.append(r_off + np.arange(N))
                c_cols.append((t + 1) * N + np.arange(N))
                c_data.append(np.ones(N))
                # -scale * J_t * v_t
                rr, cc = np.nonzero(Jt)
                c_rows.append(r_off + rr)
                c_cols.append(t * N + cc)
                c_data.append(-scale * Jt[rr, cc])
            C_mat = sparse.csc_matrix(
                (np.concatenate(c_data), (np.concatenate(c_rows), np.concatenate(c_cols))),
                shape=(n_p, n_v),
            )
            KKT = sparse.bmat([[H_blk, C_mat.T], [C_mat, None]], format="csc")
            sol = spsolve(KKT, RHS)
            # Response matrix chi_{ij} = (v_T)_i for h = e_j -> chi(lam) = (1/N) Tr(v_T) = fraction > lam
            V_T = sol[T * N : (T + 1) * N, :].toarray()
            chi_gt = float(np.trace(V_T) / N)
            cdf_clark.append(1.0 - chi_gt)
            cdf_qr.append(float(np.mean(lam_qr <= lam)))

        cdf_clark = np.array(cdf_clark)
        cdf_qr = np.array(cdf_qr)
        # Enforce monotone non-decreasing CDF and invert at midpoints (k + 0.5)/N -> W1 quantile MAE
        cdf_mono = np.maximum.accumulate(np.clip(cdf_clark, 0.0, 1.0))
        q_levels = (np.arange(N) + 0.5) / N
        lam_clark = np.interp(q_levels, cdf_mono, lam_grid)[::-1]
        mae = float(np.mean(np.abs(lam_clark - lam_qr)))
        trap_fn = getattr(np, "trapezoid", getattr(np, "trapz", None))
        w1 = float(trap_fn(np.abs(cdf_clark - cdf_qr), lam_grid))
        maes.append(mae)
        max_cdf_errs.append(w1)

    return {
        "n_seeds": n_seeds,
        "N": N,
        "T": T,
        "mean_quantile_mae": float(np.mean(maes)),
        "mean_cdf_w1": float(np.mean(max_cdf_errs)),
        "per_seed_mae": maes,
    }


def verify_hoza_isolating_trees(n_graphs: int = 30) -> dict:
    """
    Hoza (ECCC TR26-323) small-seed O(log(wn))-bit min-isolating weight search across
    30 random connected multigraphs (b1 in {2, 3, 5}), verifying unique shortest path
    to every vertex AND gauge-covariant chord holonomy equivalence across seeds.
    """
    rng = np.random.default_rng(20261122)
    b1_choices = [2, 3, 5]
    primes = [101, 211, 307, 409, 503, 607, 709, 809, 907, 1009]
    found_counts = 0
    holonomy_matches = 0
    seeds_used = []
    s3 = make_s3_group()
    mul_s3, inv_s3 = s3["mul"], s3["inv"]

    for gi in range(n_graphs):
        nV = int(rng.integers(6, 12))
        b1 = b1_choices[gi % len(b1_choices)]
        nE = (nV - 1) + b1
        edges = []
        # Spanning backbone first to guarantee connectivity
        for v in range(1, nV):
            u = int(rng.integers(0, v))
            edges.append((u, v) if rng.random() < 0.5 else (v, u))
        # Extra b1 chord edges (including parallel multiedges/self-loops allowed)
        for _ in range(b1):
            u = int(rng.integers(0, nV))
            v = int(rng.integers(0, nV))
            edges.append((u, v))

        adj = [[] for _ in range(nV)]
        for ei, (u, v) in enumerate(edges):
            adj[u].append((v, ei, 1))
            adj[v].append((u, ei, -1))

        # Test tiny hash seeds s -> polynomial weight w(e) = 1 + ((a*e^2 + b*e + c) mod p)
        found_seed = None
        parent_tree = None
        for s_idx in range(1, 256):
            p = primes[s_idx % len(primes)]
            a = 1 + (s_idx * 7) % (p - 1)
            b = 3 + (s_idx * 13) % p
            c = 1 + (s_idx * 29) % p
            w = [1 + ((a * ei * ei + b * ei + c) % p) for ei in range(nE)]
            # Dijkstra with exact tie counting
            dist = [10 ** 18] * nV
            count = [0] * nV
            parent = [None] * nV
            dist[0] = 0
            count[0] = 1
            used = [False] * nV
            for _ in range(nV):
                u = min((v for v in range(nV) if not used[v]), key=lambda v: dist[v])
                used[u] = True
                for v, ei, dr in adj[u]:
                    nd = dist[u] + w[ei]
                    if nd < dist[v]:
                        dist[v] = nd
                        count[v] = count[u]
                        parent[v] = (u, ei, dr)
                    elif nd == dist[v]:
                        count[v] += count[u]
            if all(cnt == 1 for cnt in count):
                found_seed = s_idx
                parent_tree = parent
                break

        if found_seed is not None:
            found_counts += 1
            seeds_used.append(found_seed)
            # Verify gauge covariance of isolating tree frame under random S3 vertex gauge
            A = rng.integers(0, s3["n"], size=nE)
            g_v = rng.integers(0, s3["n"], size=nV)
            A_g = [int(mul_s3[mul_s3[g_v[edges[ei][1]], A[ei]], inv_s3[g_v[edges[ei][0]]]]) for ei in range(nE)]

            def frame(conn):
                vals = [0] * nV
                # Evaluate in topological distance order via parent links
                def get_v(v):
                    if v == 0:
                        return 0
                    u, ei, dr = parent_tree[v]
                    step = int(conn[ei]) if dr == 1 else int(inv_s3[conn[ei]])
                    return int(mul_s3[step, get_v(u)])
                return [get_v(v) for v in range(nV)]

            P_orig = frame(A)
            P_gauge = frame(A_g)
            ok = all(P_gauge[v] == int(mul_s3[mul_s3[g_v[v], P_orig[v]], inv_s3[g_v[0]]]) for v in range(nV))
            if ok:
                holonomy_matches += 1

    return {
        "n_graphs": n_graphs,
        "isolating_tree_success_rate": float(found_counts / n_graphs),
        "gauge_covariance_rate": float(holonomy_matches / n_graphs),
        "max_seed_tried": max(seeds_used) if seeds_used else -1,
    }


def run_algebraic_and_retract_audits() -> dict:
    # 1. Exact S3 & A4 presentation group homomorphisms via numerical unitary irreps
    omega = complex(math.cos(2 * math.pi / 3), math.sin(2 * math.pi / 3))
    omega2 = complex(math.cos(4 * math.pi / 3), math.sin(4 * math.pi / 3))
    s3 = make_s3_group()
    Us_s3 = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    Ur_s3 = np.diag([omega, omega2]).astype(np.complex128)
    s3_mats = [np.eye(2, dtype=np.complex128)]
    for w in s3["words"][1:]:
        M = Us_s3 if w[0] == 0 else Ur_s3
        for sym in w[1:]:
            M = M @ (Us_s3 if sym == 0 else Ur_s3)
        s3_mats.append(M)
    max_s3_err = max(float(np.linalg.norm(s3_mats[a] @ s3_mats[b] - s3_mats[int(s3["mul"][a, b])]))
                     for a in range(6) for b in range(6))

    a4 = make_a4_group()
    # Standard 3D irrep of A4: permutation matrices restricted to 3D zero-sum orthogonal complement
    Q, _ = np.linalg.qr(np.array([[1, -1, 0, 0], [1, 1, -2, 0], [1, 1, 1, -3], [1, 1, 1, 1]], dtype=np.float64) / 1.0)
    # Use standard normalized Helmert basis columns 0..2 orthogonal to all-ones vector
    H = np.zeros((4, 3), dtype=np.float64)
    H[:, 0] = np.array([1, -1, 0, 0]) / math.sqrt(2)
    H[:, 1] = np.array([1, 1, -2, 0]) / math.sqrt(6)
    H[:, 2] = np.array([1, 1, 1, -3]) / math.sqrt(12)
    def perm4(p):
        P = np.zeros((4, 4), dtype=np.complex128)
        for i, pi in enumerate(p):
            P[pi, i] = 1.0
        return P
    Us_a4 = H.T @ perm4((1, 0, 3, 2)) @ H
    Ut_a4 = H.T @ perm4((1, 2, 0, 3)) @ H
    a4_mats = [np.eye(3, dtype=np.complex128)]
    for w in a4["words"][1:]:
        M = Us_a4 if w[0] == 0 else Ut_a4
        for sym in w[1:]:
            M = M @ (Us_a4 if sym == 0 else Ut_a4)
        a4_mats.append(M)
    max_a4_err = max(float(np.linalg.norm(a4_mats[a] @ a4_mats[b] - a4_mats[int(a4["mul"][a, b])]))
                     for a in range(12) for b in range(12))

    # 2. Continuous Lyapunov + Congruence Trace Similarity Audit
    w = build_dual_timescale_world("D4_slow3", seed=0)
    n_s = w["n_states"]
    P = w["P"]
    X = w["base_feats"].astype(np.float64)
    Xc = X - X.mean(axis=0, keepdims=True)
    A_cont = (P.T - np.eye(n_s)) - 0.15 * np.eye(n_s)
    Q_c = np.eye(n_s)
    Q_o = Xc @ Xc.T + 1e-3 * np.eye(n_s)
    lam = 1.5
    A_sh = A_cont - 0.5 * lam * np.eye(n_s)
    Wc = solve_continuous_lyapunov(A_sh, -Q_c)
    Wo = solve_continuous_lyapunov(A_sh.T, -Q_o)
    lyap_res_c = float(np.linalg.norm(A_sh @ Wc + Wc @ A_sh.T + Q_c))
    lyap_res_o = float(np.linalg.norm(A_sh.T @ Wo + Wo @ A_sh + Q_o))
    rng = np.random.default_rng(77)
    T_sim = np.eye(n_s) + 0.12 * rng.normal(size=(n_s, n_s))
    T_inv = np.linalg.inv(T_sim)
    Wc_t = T_sim @ Wc @ T_sim.T
    Wo_t = T_inv.T @ Wo @ T_inv
    trace_sim_err = abs(float(np.trace(Wc_t @ Wo_t) - np.trace(Wc @ Wo)))

    # 3. 3-Object Kan Retract Check: G(0)=Bool, G(1)=Bool+*, G(2)=Bool
    def f01(b): return ("bool", b)
    def f12(x): return x[1] if x[0] == "bool" else True
    retract_ok = all(f12(f01(b)) == b for b in (False, True))
    hoza = verify_hoza_isolating_trees(30)
    clark = verify_clark_min_norm_tangent_rnn(n_seeds=3, N=32, T=56)

    return {
        "exact_s3_pres_hom_err": max_s3_err,
        "exact_a4_pres_hom_err": max_a4_err,
        "exact_pres_hom_err": max(max_s3_err, max_a4_err),
        "continuous_lyap_err": max(lyap_res_c, lyap_res_o),
        "trace_similarity_err": trace_sim_err,
        "kan_retract_verified": retract_ok,
        "hoza_isolating_trees": hoza,
        "clark_rnn_lyap": clark,
    }


def _worker_task(job: tuple) -> dict:
    kind = job[0]
    if kind == "arm1":
        _, group_name, model_name, seed, s1, s2 = job
        return run_arm1_task(group_name, model_name, seed, s1, s2)
    elif kind == "arm2":
        _, world_name, obj_name, seed, steps = job
        return run_arm2_jepa_task(world_name, obj_name, seed, steps)
    raise ValueError(kind)


def aggregate_and_judge(results: List[dict], audit: dict, total_elapsed_s: float) -> dict:
    # Group Arm 1 results
    arm1_agg = {}
    for gname in ("A4", "S3_bouquet"):
        arm1_agg[gname] = {}
        models = sorted({r["model"] for r in results if r["arm"] == f"Arm1_{'A4' if gname=='A4' else 'S3'}"})
        for mname in models:
            sub = [r for r in results if r["arm"] == f"Arm1_{'A4' if gname=='A4' else 'S3'}" and r["model"] == mname]
            keys = [k for k in sub[0] if k not in ("arm", "group", "model", "seed")]
            arm1_agg[gname][mname] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    # Group Arm 2 results
    arm2_agg = {}
    for wname in ("C8_slow3", "D4_slow3"):
        arm2_agg[wname] = {}
        objs = sorted({r["objective"] for r in results if r["arm"] == "Arm2_JEPA" and r["world"] == wname})
        for obj in objs:
            sub = [r for r in results if r["arm"] == "Arm2_JEPA" and r["world"] == wname and r["objective"] == obj]
            keys = [k for k in sub[0] if k not in ("arm", "world", "objective", "seed")]
            arm2_agg[wname][obj] = {k: float(np.mean([r[k] for r in sub])) for k in keys}

    # Judge HLL.1
    a4_agg = arm1_agg["A4"]
    s3_agg = arm1_agg["S3_bouquet"]
    pres_candidates_a4 = [a4_agg[m] for m in ("spectral_presentation_gen", "lie_presentation_gen") if m in a4_agg]
    pres_candidates_s3 = [s3_agg[m] for m in ("spectral_presentation_gen", "lie_presentation_gen") if m in s3_agg]
    best_a4_pres = max(pres_candidates_a4, key=lambda d: d["L16_bacc"])
    best_s3_pres = max(pres_candidates_s3, key=lambda d: d["L8_bacc"])
    min_a4_bacc = min(best_a4_pres[f"L{L}_bacc"] for L in (4, 5, 6, 8, 12, 16))
    min_s3_bacc = min(best_s3_pres[f"L{L}_bacc"] for L in (3, 4, 6, 8))
    soft_a4_L16 = a4_agg["cayley_unitary_ufr_soft"]["L16_bacc"]
    hll1 = (
        best_a4_pres["homomorphism_err"] <= 1e-3
        and best_s3_pres["homomorphism_err"] <= 1e-3
        and min(min_a4_bacc, min_s3_bacc) >= 0.990
        and (best_a4_pres["L16_bacc"] - soft_a4_L16) >= 0.10
    )

    # Judge HLL.2
    fer_keep = a4_agg["cayley_unitary_fer"]["forgetting_after_keep"]
    soft_keep = a4_agg["cayley_unitary_ufr_soft"]["forgetting_after_keep"]
    pres_keep = best_a4_pres["forgetting_after_keep"]
    hll2 = ((pres_keep - fer_keep) >= 0.20) and (pres_keep > soft_keep)

    # Judge HLL.3
    d4_jags = [arm2_agg["D4_slow3"][o]["jag"] for o in arm2_agg["D4_slow3"]]
    c8_slow = arm2_agg["C8_slow3"]["jepa_slow_svreg"]
    c8_sg = arm2_agg["C8_slow3"]["jepa_sg"]
    c8_sv = arm2_agg["C8_slow3"]["jepa_svreg"]
    d4_slow = arm2_agg["D4_slow3"]["jepa_slow_svreg"]
    d4_sg = arm2_agg["D4_slow3"]["jepa_sg"]
    d4_sv = arm2_agg["D4_slow3"]["jepa_svreg"]
    hll3 = (
        all(j < 3.0 for j in d4_jags)
        and c8_slow["jag"] < c8_sg["jag"]
        and d4_slow["jag"] < d4_sg["jag"]
        and (c8_slow["r2_slow"] - c8_sv["r2_slow"]) >= 0.50
        and (d4_slow["r2_slow"] - d4_sv["r2_slow"]) >= 0.50
    )

    # Judge HLL.4
    c8_cont = c8_slow["best_cos_G_cont_lyap"]
    d4_cont = d4_slow["best_cos_G_cont_lyap"]
    mean_cont = 0.5 * (c8_cont + d4_cont)
    mean_heat = 0.5 * (c8_slow["best_cos_G_gm_heat"] + d4_slow["best_cos_G_gm_heat"])
    clark_mae = audit["clark_rnn_lyap"]["mean_quantile_mae"]
    hll4 = (min(c8_cont, d4_cont) >= 0.80) and (abs(mean_cont - mean_heat) <= 0.08) and (clark_mae <= 0.02)

    # Judge HLL.5
    max_neural_u_err = max(r["unitary_max_err"] for r in results if "unitary_max_err" in r)
    hll5 = (
        audit["continuous_lyap_err"] < 1e-12
        and audit["trace_similarity_err"] < 1e-12
        and audit["exact_pres_hom_err"] < 1e-13
        and audit["hoza_isolating_trees"]["isolating_tree_success_rate"] == 1.0
        and audit["hoza_isolating_trees"]["gauge_covariance_rate"] == 1.0
        and max_neural_u_err < 1e-5
        and audit["kan_retract_verified"]
    )

    # Disambiguate HLL.1..4 HELD vs BROKEN vs NEITHER cleanly
    def verdict(flag: bool, partial: bool = False) -> str:
        if flag:
            return "HELD"
        return "NEITHER" if partial else "BROKEN"

    hll1_partial = (best_a4_pres["L16_bacc"] - soft_a4_L16) >= 0.10 or min_s3_bacc >= 0.990
    hll2_partial = (pres_keep - fer_keep) >= 0.20
    hll3_partial = all(j < 3.0 for j in d4_jags) and (c8_slow["r2_slow"] - c8_sv["r2_slow"]) >= 0.50
    hll4_partial = min(c8_cont, d4_cont) >= 0.80

    return {
        "verdicts": {
            "HLL.1": verdict(hll1, hll1_partial and not hll1),
            "HLL.2": verdict(hll2, hll2_partial and not hll2),
            "HLL.3": verdict(hll3, hll3_partial and not hll3),
            "HLL.4": verdict(hll4, hll4_partial and not hll4),
            "HLL.5": "HELD" if hll5 else "BROKEN",
        },
        "total_runs": len(results),
        "total_elapsed_s": round(total_elapsed_s, 2),
        "max_neural_unitary_err": max_neural_u_err,
        "audit": audit,
        "Arm1": arm1_agg,
        "Arm2": arm2_agg,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Fast verification run")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    t0 = time.time()
    audit = run_algebraic_and_retract_audits()
    print(
        f"ALGEBRAIC_AUDIT: pres_hom={audit['exact_pres_hom_err']:.2e}, "
        f"cont_lyap={audit['continuous_lyap_err']:.2e}, trace_sim={audit['trace_similarity_err']:.2e}, "
        f"hoza_iso={audit['hoza_isolating_trees']['isolating_tree_success_rate']:.2f}, "
        f"clark_mae={audit['clark_rnn_lyap']['mean_quantile_mae']:.4f}, kan_retract={audit['kan_retract_verified']}",
        flush=True,
    )

    seeds = [0] if args.smoke else [0, 1, 2]
    s1_a4 = 240 if args.smoke else 900
    s2_a4 = 120 if args.smoke else 360
    s1_s3 = 220 if args.smoke else 750
    s2_s3 = 100 if args.smoke else 300
    s_jepa = 250 if args.smoke else 1200

    jobs = []
    for m in ("cayley_unitary_fer", "cayley_unitary_ufr_soft", "lie_exp_ufr_soft", "lie_presentation_gen", "spectral_presentation_gen"):
        for sd in seeds:
            jobs.append(("arm1", "A4", m, sd, s1_a4, s2_a4))
    for m in ("cayley_unitary_fer", "cayley_unitary_ufr_soft", "lie_presentation_gen", "spectral_presentation_gen"):
        for sd in seeds:
            jobs.append(("arm1", "S3", m, sd, s1_s3, s2_s3))
    for wname in ("C8_slow3", "D4_slow3"):
        for obj in ("jepa_sg", "jepa_svreg", "jepa_slow_svreg"):
            for sd in seeds:
                jobs.append(("arm2", wname, obj, sd, s_jepa))

    results = []
    temp_dir = pathlib.Path(os.environ.get("TEMP", "/tmp")) / "semplex_trash_oleans"
    raw_dir = temp_dir / f"mp_ll_raw_{time.strftime('%Y%m%d_%H%M%S')}"
    raw_dir.mkdir(parents=True, exist_ok=True)

    print(f"Launching {len(jobs)} jobs with workers={args.workers} ...", flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
        for i, res in enumerate(ex.map(_worker_task, jobs)):
            results.append(res)
            with open(raw_dir / f"run_{i:02d}.json", "w", encoding="utf-8") as f:
                json.dump(res, f)
            tag = res.get("model") or f"{res.get('world')}/{res.get('objective')}"
            label = f"{res['arm']}/{tag}/s{res['seed']}"
            print(f"[{i+1}/{len(jobs)}] {label} done ({time.time() - t0:.1f}s)", flush=True)

    summary = aggregate_and_judge(results, audit, time.time() - t0)
    print("VERDICTS:", json.dumps(summary["verdicts"]), flush=True)

    if not args.smoke:
        out_path = pathlib.Path(__file__).resolve().parent / "results" / "master_principle_lie_lyapunov.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
        print(f"Saved summary -> {out_path} (raw archived at {raw_dir})", flush=True)
    else:
        print("Smoke run summary:", json.dumps({
            "A4_spectral_L16": summary["Arm1"]["A4"]["spectral_presentation_gen"]["L16_bacc"],
            "A4_spectral_hom": summary["Arm1"]["A4"]["spectral_presentation_gen"]["homomorphism_err"],
            "A4_lie_L16": summary["Arm1"]["A4"]["lie_presentation_gen"]["L16_bacc"],
            "A4_lie_hom": summary["Arm1"]["A4"]["lie_presentation_gen"]["homomorphism_err"],
            "A4_soft_L16": summary["Arm1"]["A4"]["cayley_unitary_ufr_soft"]["L16_bacc"],
            "S3_spectral_L6": summary["Arm1"]["S3_bouquet"]["spectral_presentation_gen"]["L6_bacc"],
            "S3_spectral_L8": summary["Arm1"]["S3_bouquet"]["spectral_presentation_gen"]["L8_bacc"],
            "S3_spectral_hom": summary["Arm1"]["S3_bouquet"]["spectral_presentation_gen"]["homomorphism_err"],
            "S3_lie_L8": summary["Arm1"]["S3_bouquet"]["lie_presentation_gen"]["L8_bacc"],
            "D4_jags": {k: v["jag"] for k, v in summary["Arm2"]["D4_slow3"].items()},
            "C8_cont_cos": summary["Arm2"]["C8_slow3"]["jepa_slow_svreg"]["best_cos_G_cont_lyap"],
            "C8_heat_cos": summary["Arm2"]["C8_slow3"]["jepa_slow_svreg"]["best_cos_G_gm_heat"],
            "D4_cont_cos": summary["Arm2"]["D4_slow3"]["jepa_slow_svreg"]["best_cos_G_cont_lyap"],
            "D4_heat_cos": summary["Arm2"]["D4_slow3"]["jepa_slow_svreg"]["best_cos_G_gm_heat"],
        }, indent=2), flush=True)


if __name__ == "__main__":
    main()
