#!/usr/bin/env python3
"""
Pre-Registered 48-Run Master Principle GHSRT Showdown (`gemini/master-principle-ghsrt`)

Tests 5 pre-registered hypotheses (`HGH.1` - `HGH.5`):
- Arm 1 (24 runs): UFR Homomorphic U(d) vs FER vs Test-Time Symmetrization (`arXiv:2611.24032`)
  & Catastrophic Forgetting (`arXiv:2611.11020`, `arXiv:2611.11862`) on non-ambivalent `A4`
  and `b1 = 2` `S3` two-loop bouquets (`OOD` length generalization through `L = 8` / `L = 6`).
- Arm 2 (24 runs): JEPA Content-Geometry Tradeoff (`Ren & LeCun 2026` SVReg / Slow SVReg +
  `arXiv:2611.21596` SADL) vs `G_gm_heat(lam)` & `X_kl_gm(lam)` on dual-timescale monoids.
- HGH.5 Audit: Exact numerical verification of group-algebra Frobenius monoid laws,
  finite concept-quantale residuation (`arXiv:2608.26631`), U(d) homomorphism word-length
  invariance, and neural unitarity (< 1e-5).
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
from scipy.linalg import expm, logm, eigh, fractional_matrix_power, solve_discrete_lyapunov


# =============================================================================
# Finite Groups (A4, D4, S3, C8) with exact multiplication tables (id = index 0)
# =============================================================================

def _build_group_from_perms(perms: List[Tuple[int, ...]]) -> dict:
    n = len(perms)
    deg = len(perms[0])
    ident = tuple(range(deg))
    # Place identity strictly at index 0
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

    # Conjugacy classes
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
        "mul": mul,
        "inv": inv,
        "classes": classes,
        "cls_of": cls_of,
        "n_cls": len(classes),
    }


def make_s3_group() -> dict:
    perms = list(itertools.permutations(range(3)))
    return _build_group_from_perms(perms)


def make_d4_group() -> dict:
    # Dihedral group D4 on vertices 0,1,2,3
    r = (1, 2, 3, 0)
    s = (0, 3, 2, 1)

    def comp(a, b):
        return tuple(a[b[k]] for k in range(4))

    gens = [r, s]
    closure = {(0, 1, 2, 3)}
    q = [(0, 1, 2, 3)]
    while q:
        cur = q.pop()
        for g in gens:
            nxt = comp(g, cur)
            if nxt not in closure:
                closure.add(nxt)
                q.append(nxt)
    return _build_group_from_perms(sorted(closure))


def make_a4_group() -> dict:
    def parity(p):
        inv_cnt = sum(1 for i in range(len(p)) for j in range(i + 1, len(p)) if p[i] > p[j])
        return inv_cnt % 2

    perms = [p for p in itertools.permutations(range(4)) if parity(p) == 0]
    g = _build_group_from_perms(perms)
    assert g["n"] == 12 and g["n_cls"] == 4
    return g


def make_c8_group() -> dict:
    perms = [tuple((k + r) % 8 for k in range(8)) for r in range(8)]
    return _build_group_from_perms(perms)


def build_bouquet_orbits(g_tab: dict) -> dict:
    """Simultaneous conjugation orbits (g1, g2) ~ (k g1 k^-1, k g2 k^-1) on G x G."""
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
    return {"orbit_of": orbit_of, "orbits": orbits, "n_orbits": len(orbits)}


# =============================================================================
# Sampling Class-Balanced Loop Words & Gauge Rewritings (Arm 1)
# =============================================================================

def _words_for_group_elements(rng: np.random.Generator, mul: np.ndarray, G: int, L: int, count: np.ndarray) -> np.ndarray:
    """Generate exact uniform random sequences of length L whose left-product is h, balanced by count[h]."""
    out = []
    # Precompute inverse-lookup: for fixed product h, sample x_0..x_{L-2} uniformly, then solve x_{L-1} * p = h
    # => x_{L-1} = h * p^-1. Wait: if G has exact inv table: x_{L-1} = mul[h, inv[p]].
    return np.empty((0, L), dtype=np.int64)


def sample_balanced_single_loop(
    rng: np.random.Generator, g_tab: dict, lengths: List[int], total_per_class: int,
    allowed_classes: List[int] = None
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """Return dict L -> (X_L, y_L) with uniform sampling across conjugacy classes (and group elements inside each class)."""
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    classes = g_tab["classes"]
    n_cls = g_tab["n_cls"]
    G = g_tab["n"]
    if allowed_classes is None:
        allowed_classes = list(range(n_cls))

    X_by_L = {}
    y_by_L = {}
    per_L_cls = max(1, total_per_class // len(lengths))
    for L in lengths:
        xs = []
        ys = []
        for cid in allowed_classes:
            elts = classes[cid]
            for m in range(per_L_cls):
                h = elts[m % len(elts)]
                prefix = rng.integers(0, G, size=L - 1, dtype=np.int64)
                p = 0
                for t in range(L - 1):
                    p = int(mul[prefix[t], p])
                last = int(mul[h, inv[p]])
                word = np.append(prefix, last)
                # Random cyclic shift? Word product changes by conjugation ONLY, keeping conjugacy class invariant!
                shift = int(rng.integers(0, L))
                word = np.roll(word, shift)
                xs.append(word)
                ys.append(cid)
        X = np.array(xs, dtype=np.int64)
        y = np.array(ys, dtype=np.int64)
        perm = rng.permutation(len(y))
        X_by_L[L] = X[perm]
        y_by_L[L] = y[perm]
    return X_by_L, y_by_L


def sample_balanced_bouquet(
    rng: np.random.Generator, g_tab: dict, b_info: dict, lengths: List[int],
    total_per_orbit: int, allowed_orbits: List[int] = None
) -> Tuple[Dict[int, np.ndarray], Dict[int, np.ndarray]]:
    """Generate two-loop bouquet sequences [loop1(L), loop2(L)] balanced across joint simultaneous orbits."""
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    G = g_tab["n"]
    orbits = b_info["orbits"]
    n_orb = b_info["n_orbits"]
    if allowed_orbits is None:
        allowed_orbits = list(range(n_orb))

    X_by_L = {}
    y_by_L = {}
    per_L_orb = max(1, total_per_orbit // len(lengths))
    for L in lengths:
        xs = []
        ys = []
        for oid in allowed_orbits:
            pts = orbits[oid]
            for m in range(per_L_orb):
                h1, h2 = pts[m % len(pts)]
                # Loop 1
                pref1 = rng.integers(0, G, size=L - 1, dtype=np.int64)
                p1 = 0
                for t in range(L - 1):
                    p1 = int(mul[pref1[t], p1])
                w1 = np.append(pref1, int(mul[h1, inv[p1]]))
                # Loop 2
                pref2 = rng.integers(0, G, size=L - 1, dtype=np.int64)
                p2 = 0
                for t in range(L - 1):
                    p2 = int(mul[pref2[t], p2])
                w2 = np.append(pref2, int(mul[h2, inv[p2]]))
                # Note: simultaneous gauge conjugation preserves joint orbit, cyclic shift on individual loop
                # preserves loop conjugacy, NOT always simultaneous conjugation if shifted independently when base changes!
                # Keep unshifted or shift inside exact base-pinned representative: wait -- to test true bouquet holonomy at basepoint,
                # cyclic shift of w1 relative to w2 changes h1 by conjugation with prefix of w1, changing joint orbit unless k=1!
                xs.append(np.concatenate([w1, w2]))
                ys.append(oid)
        X = np.array(xs, dtype=np.int64)
        y = np.array(ys, dtype=np.int64)
        perm = rng.permutation(len(y))
        X_by_L[L] = X[perm]
        y_by_L[L] = y[perm]
    return X_by_L, y_by_L


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray, classes_present: List[int] = None) -> float:
    if classes_present is None:
        classes_present = sorted(set(y_true.tolist()))
    accs = []
    for c in classes_present:
        mask = (y_true == c)
        if np.any(mask):
            accs.append(float(np.mean(y_pred[mask] == y_true[mask])))
    return float(np.mean(accs)) if accs else 0.0


# =============================================================================
# Cayley Unitary Helper & Arm 1 Architectures (Parameter-Matched 16k +- 5%)
# =============================================================================

def run_arm1_single_task(group_name: str, model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(1000 + seed * 97 + (0 if group_name == "A4" else 13))

    g_tab = make_a4_group() if group_name == "A4" else make_s3_group()
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    G = g_tab["n"]
    n_cls = g_tab["n_cls"]

    def make_cayley(P_re, P_im, eye_c):
        # Z = P + i Q ; A = Z - Z^* (skew-Hermitian)
        Z = torch.complex(P_re, P_im)
        A = Z - Z.conj().transpose(-1, -2)
        eye = eye_c.unsqueeze(0).expand_as(A)
        U_nt = torch.linalg.solve(eye + A, eye - A)
        U_0 = eye_c.unsqueeze(0)  # identity element strictly I
        return torch.cat([U_0, U_nt], dim=0)  # (G, H, d, d)

    def _trace_feats(P, d):
        feats = []
        Pk = P
        for k in range(4):
            if k > 0:
                Pk = torch.matmul(Pk, P)
            tr = torch.diagonal(Pk, dim1=-2, dim2=-1).sum(-1) / d
            feats.append(tr.real)
            feats.append(tr.imag)
        return torch.cat(feats, dim=-1)

    if model_name == "cayley_unitary_fer":
        n_heads, d = 8, 6
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads, self.d = n_heads, d
                scale = 0.45 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.trunk = nn.Sequential(nn.Linear(n_heads * 8, 96), nn.Tanh(), nn.Linear(96, 32), nn.Tanh())
                self.head = nn.Linear(32, n_cls)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley(self.P_re, self.P_im, self.eye_c)
            def extract_with_bank(self, Ub, X):
                Us = Ub[X]
                P = Us[:, 0]
                for t in range(1, X.shape[1]):
                    P = torch.matmul(Us[:, t], P)
                inv_f = _trace_feats(P, self.d)
                pen = self.trunk(inv_f)
                return inv_f, pen, self.head(pen)
            def extract(self, X):
                return self.extract_with_bank(self.unitary_bank(), X)
            def forward(self, X):
                return self.extract(X)[2]
        m = Model()
        train_lengths = [3, 4]

    elif model_name in ("cayley_unitary_varlen_linear", "cayley_unitary_ufr_grounded"):
        n_heads, d = 19, 6
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads, self.d = n_heads, d
                scale = 0.55 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.head = nn.Linear(n_heads * 8, n_cls)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley(self.P_re, self.P_im, self.eye_c)
            def extract_with_bank(self, Ub, X):
                Us = Ub[X]
                P = Us[:, 0]
                for t in range(1, X.shape[1]):
                    P = torch.matmul(Us[:, t], P)
                inv_f = _trace_feats(P, self.d)
                return inv_f, inv_f, self.head(inv_f)
            def extract(self, X):
                return self.extract_with_bank(self.unitary_bank(), X)
            def forward(self, X):
                return self.extract(X)[2]
        m = Model()
        train_lengths = [2, 3, 4]

    elif model_name == "ordered_gru":
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G, 28)
                self.rnn = nn.GRU(28, 56, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(56, 20), nn.Tanh())
                self.head = nn.Linear(20, n_cls)
            def extract(self, X):
                seq = self.rnn(self.emb(X))[0]
                h_last = seq[:, -1, :]
                pen = self.trunk(h_last)
                return h_last, pen, self.head(pen)
            def forward(self, X):
                return self.extract(X)[2]
        m = Model()
        train_lengths = [2, 3, 4]
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    assert 15200 <= n_params <= 16800, f"Arm1 A4 {model_name} params={n_params}"

    # Precompute Cayley pair tables for counterfactual composition grounding (DynamicRealization)
    a_idx_np, b_idx_np = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
    a_idx_t = torch.tensor(a_idx_np.ravel(), dtype=torch.long)
    b_idx_t = torch.tensor(b_idx_np.ravel(), dtype=torch.long)
    ab_idx_t = torch.tensor(mul[a_idx_np, b_idx_np].ravel(), dtype=torch.long)

    # Generate balanced Phase-1 train/val datasets across train_lengths and OOD test lengths
    X_tr, y_tr = sample_balanced_single_loop(rng, g_tab, train_lengths, 960)
    X_val, y_val = sample_balanced_single_loop(rng, g_tab, [4, 5, 6, 8], 1024)

    opt = torch.optim.AdamW(m.parameters(), lr=8e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, steps_p1), eta_min=5e-4)
    hom_loss_val = 0.0
    for step in range(steps_p1):
        opt.zero_grad()
        L = train_lengths[step % len(train_lengths)]
        idx = rng.integers(0, len(y_tr[L]), size=80)
        xb = torch.tensor(X_tr[L][idx], dtype=torch.long)
        yb = torch.tensor(y_tr[L][idx], dtype=torch.long)
        if hasattr(m, "extract_with_bank"):
            Ub = m.unitary_bank()
            logits = m.extract_with_bank(Ub, xb)[2]
        else:
            Ub = None
            logits = m(xb)
        loss = F.cross_entropy(logits, yb)
        if model_name == "cayley_unitary_ufr_grounded":
            ramp = min(1.0, step / max(1.0, 0.25 * steps_p1))
            lam_hom = 8.0 * ramp
            diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
            hom_l = (diff.abs() ** 2).mean()
            hom_loss_val = float(hom_l.detach().item())
            loss = loss + lam_hom * hom_l
        loss.backward()
        opt.step()
        sched.step()

    m.eval()
    unitary_err = 0.0
    if hasattr(m, "unitary_bank"):
        with torch.no_grad():
            Ub = m.unitary_bank()
            eye = torch.eye(m.d, dtype=torch.complex64).view(1, 1, m.d, m.d)
            err = torch.matmul(Ub, Ub.conj().transpose(-1, -2)) - eye
            unitary_err = float(err.abs().max().item())
            diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
            hom_loss_val = float((diff.abs() ** 2).mean().item())

    def eval_single(X_np, y_np, k_tts: int = 1) -> Tuple[float, float]:
        with torch.no_grad():
            if k_tts == 1:
                logits = m(torch.tensor(X_np, dtype=torch.long))
                probs = F.softmax(logits, dim=-1).numpy()
            else:
                N, L = X_np.shape
                probs = np.zeros((N, n_cls), dtype=np.float64)
                for k_i in range(k_tts):
                    if k_i == 0:
                        Xk = X_np
                    else:
                        ks = rng.integers(0, G, size=(N, 1))
                        # Conjugate each element g -> k * g * k^-1 and randomly roll
                        Xk = mul[mul[ks, X_np], inv[ks]]
                        shift = int(rng.integers(0, L))
                        Xk = np.roll(Xk, shift, axis=1)
                    lg = m(torch.tensor(Xk, dtype=torch.long))
                    probs += F.softmax(lg, dim=-1).numpy()
                probs /= k_tts
        pred = probs.argmax(axis=-1)
        return balanced_accuracy(y_np, pred), float(np.mean(pred == y_np))

    eval_res = {}
    for L in [4, 5, 6, 8]:
        bacc, acc = eval_single(X_val[L], y_val[L], k_tts=1)
        eval_res[f"L{L}_bacc"] = bacc
        eval_res[f"L{L}_acc"] = acc

    tts_res = {}
    if model_name == "ordered_gru":
        for L in [4, 5, 6, 8]:
            tts_res[f"L{L}"] = {}
            for K in [1, 2, 4, 8, 16]:
                bacc_k, acc_k = eval_single(X_val[L], y_val[L], k_tts=K)
                tts_res[f"L{L}"][f"K{K}"] = bacc_k

    # Phase 2 Catastrophic Forgetting Probe (2611.11020 UFR vs FER):
    # Fine-tune strictly on S_ft = {2, 3} with unmodified CE optimizer; test retention on S_keep = {0, 1}
    S_keep = [0, 1]
    S_ft = [2, 3]
    keep_mask = np.isin(y_val[4], S_keep)
    X_keep_eval, y_keep_eval = X_val[4][keep_mask], y_val[4][keep_mask]
    before_keep = balanced_accuracy(
        y_keep_eval,
        m(torch.tensor(X_keep_eval, dtype=torch.long)).detach().argmax(-1).numpy(),
        classes_present=S_keep,
    )
    X_ft, y_ft = sample_balanced_single_loop(rng, g_tab, [4], 400, allowed_classes=S_ft)
    m.train()
    opt_ft = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=0.0)
    for _ in range(steps_p2):
        opt_ft.zero_grad()
        idx = rng.integers(0, len(y_ft[4]), size=64)
        xb = torch.tensor(X_ft[4][idx], dtype=torch.long)
        yb = torch.tensor(y_ft[4][idx], dtype=torch.long)
        loss_ft = F.cross_entropy(m(xb), yb)
        loss_ft.backward()
        opt_ft.step()
    m.eval()
    with torch.no_grad():
        after_pred = m(torch.tensor(X_keep_eval, dtype=torch.long)).argmax(-1).numpy()
    after_keep = balanced_accuracy(y_keep_eval, after_pred, classes_present=S_keep)

    return {
        "arm": "Arm1_A4",
        "group": group_name,
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "homomorphism_err": hom_loss_val,
        **eval_res,
        "tts": tts_res,
        "forgetting_before_keep": before_keep,
        "forgetting_after_keep": after_keep,
        "forgetting_drop": float(before_keep - after_keep),
    }


def run_arm1_bouquet_task(model_name: str, seed: int, steps_p1: int, steps_p2: int) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(3000 + seed * 101)

    g_tab = make_s3_group()
    b_info = build_bouquet_orbits(g_tab)
    mul = g_tab["mul"]
    inv = g_tab["inv"]
    G = g_tab["n"]
    n_orb = b_info["n_orbits"]  # 11

    def make_cayley(P_re, P_im, eye_c):
        Z = torch.complex(P_re, P_im)
        A = Z - Z.conj().transpose(-1, -2)
        eye = eye_c.unsqueeze(0).expand_as(A)
        U_nt = torch.linalg.solve(eye + A, eye - A)
        return torch.cat([eye_c.unsqueeze(0), U_nt], dim=0)

    def bouquet_feats(Ub, X, d):
        Lloop = X.shape[1] // 2
        def prod_seq(Xs):
            Us = Ub[Xs]
            P = Us[:, 0]
            for t in range(1, Xs.shape[1]):
                P = torch.matmul(Us[:, t], P)
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
            torch.matmul(H12, H1dH2d),
            torch.matmul(H12, H12),
        ]
        feats = []
        for W in words:
            tr = torch.diagonal(W, dim1=-2, dim2=-1).sum(-1) / d
            feats.append(tr.real)
            feats.append(tr.imag)
        return torch.cat(feats, dim=-1)

    if model_name == "cayley_unitary_fer":
        n_heads, d = 8, 6
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads, self.d = n_heads, d
                scale = 0.45 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.trunk = nn.Sequential(nn.Linear(n_heads * 20, 72), nn.Tanh(), nn.Linear(72, 18), nn.Tanh())
                self.head = nn.Linear(18, n_orb)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley(self.P_re, self.P_im, self.eye_c)
            def forward_with_bank(self, Ub, X):
                inv_f = bouquet_feats(Ub, X, self.d)
                return self.head(self.trunk(inv_f))
            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)
        m = Model()
        train_lengths = [3]

    elif model_name in ("cayley_unitary_varlen_linear", "cayley_unitary_ufr_grounded"):
        n_heads, d = 27, 6
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.n_heads, self.d = n_heads, d
                scale = 0.55 / math.sqrt(d)
                self.P_re = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.P_im = nn.Parameter(torch.randn(G - 1, n_heads, d, d) * scale)
                self.head = nn.Linear(n_heads * 20, n_orb)
                self.register_buffer("eye_c", torch.eye(d, dtype=torch.complex64).unsqueeze(0).expand(n_heads, d, d).clone())
            def unitary_bank(self):
                return make_cayley(self.P_re, self.P_im, self.eye_c)
            def forward_with_bank(self, Ub, X):
                inv_f = bouquet_feats(Ub, X, self.d)
                return self.head(inv_f)
            def forward(self, X):
                return self.forward_with_bank(self.unitary_bank(), X)
        m = Model()
        train_lengths = [2, 3]

    elif model_name == "joint_bouquet_gru":
        class Model(nn.Module):
            def __init__(self):
                super().__init__()
                self.emb = nn.Embedding(G, 32)
                self.loop_emb = nn.Embedding(2, 32)
                self.rnn = nn.GRU(32, 54, batch_first=True)
                self.trunk = nn.Sequential(nn.Linear(54, 22), nn.Tanh())
                self.head = nn.Linear(22, n_orb)
            def forward(self, X):
                B, tot = X.shape
                Lloop = tot // 2
                lidx = torch.cat([
                    torch.zeros(Lloop, dtype=torch.long, device=X.device),
                    torch.ones(Lloop, dtype=torch.long, device=X.device),
                ]).unsqueeze(0).expand(B, tot)
                seq = self.rnn(self.emb(X) + self.loop_emb(lidx))[0]
                return self.head(self.trunk(seq[:, -1, :]))
        m = Model()
        train_lengths = [2, 3]
    else:
        raise ValueError(model_name)

    n_params = sum(p.numel() for p in m.parameters())
    assert 15200 <= n_params <= 16800, f"Arm1 Bouquet {model_name} params={n_params}"

    a_idx_np, b_idx_np = np.meshgrid(np.arange(G), np.arange(G), indexing="ij")
    a_idx_t = torch.tensor(a_idx_np.ravel(), dtype=torch.long)
    b_idx_t = torch.tensor(b_idx_np.ravel(), dtype=torch.long)
    ab_idx_t = torch.tensor(mul[a_idx_np, b_idx_np].ravel(), dtype=torch.long)

    X_tr, y_tr = sample_balanced_bouquet(rng, g_tab, b_info, train_lengths, 1100)
    X_val, y_val = sample_balanced_bouquet(rng, g_tab, b_info, [3, 4, 6], 1100)

    opt = torch.optim.AdamW(m.parameters(), lr=8e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, steps_p1), eta_min=5e-4)
    hom_loss_val = 0.0
    for step in range(steps_p1):
        opt.zero_grad()
        L = train_lengths[step % len(train_lengths)]
        idx = rng.integers(0, len(y_tr[L]), size=80)
        xb = torch.tensor(X_tr[L][idx], dtype=torch.long)
        yb = torch.tensor(y_tr[L][idx], dtype=torch.long)
        if hasattr(m, "forward_with_bank"):
            Ub = m.unitary_bank()
            logits = m.forward_with_bank(Ub, xb)
        else:
            Ub = None
            logits = m(xb)
        loss = F.cross_entropy(logits, yb)
        if model_name == "cayley_unitary_ufr_grounded":
            ramp = min(1.0, step / max(1.0, 0.25 * steps_p1))
            diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
            hom_l = (diff.abs() ** 2).mean()
            hom_loss_val = float(hom_l.detach().item())
            loss = loss + (8.0 * ramp) * hom_l
        loss.backward()
        opt.step()
        sched.step()

    m.eval()
    unitary_err = 0.0
    if hasattr(m, "unitary_bank"):
        with torch.no_grad():
            Ub = m.unitary_bank()
            eye = torch.eye(m.d, dtype=torch.complex64).view(1, 1, m.d, m.d)
            unitary_err = float((torch.matmul(Ub, Ub.conj().transpose(-1, -2)) - eye).abs().max().item())
            diff = torch.matmul(Ub[a_idx_t], Ub[b_idx_t]) - Ub[ab_idx_t]
            hom_loss_val = float((diff.abs() ** 2).mean().item())

    def eval_bouquet(X_np, y_np, k_tts: int = 1) -> Tuple[float, float]:
        with torch.no_grad():
            if k_tts == 1:
                probs = F.softmax(m(torch.tensor(X_np, dtype=torch.long)), dim=-1).numpy()
            else:
                N, tot = X_np.shape
                probs = np.zeros((N, n_orb), dtype=np.float64)
                for k_i in range(k_tts):
                    if k_i == 0:
                        Xk = X_np
                    else:
                        ks = rng.integers(0, G, size=(N, 1))
                        # Simultaneous conjugation k w1 k^-1, k w2 k^-1 preserves exact joint base-orbit!
                        Xk = mul[mul[ks, X_np], inv[ks]]
                    probs += F.softmax(m(torch.tensor(Xk, dtype=torch.long)), dim=-1).numpy()
                probs /= k_tts
        pred = probs.argmax(axis=-1)
        return balanced_accuracy(y_np, pred), float(np.mean(pred == y_np))

    eval_res = {}
    for L in [3, 4, 6]:
        bacc, acc = eval_bouquet(X_val[L], y_val[L], k_tts=1)
        eval_res[f"L{L}_bacc"] = bacc
        eval_res[f"L{L}_acc"] = acc

    tts_res = {}
    if model_name == "joint_bouquet_gru":
        for L in [3, 4, 6]:
            tts_res[f"L{L}"] = {}
            for K in [1, 2, 4, 8, 16]:
                bacc_k, _ = eval_bouquet(X_val[L], y_val[L], k_tts=K)
                tts_res[f"L{L}"][f"K{K}"] = bacc_k

    # Phase 2 Forgetting Probe: split 11 orbits into {0..4} keep and {5..10} fine-tune
    S_keep = list(range(5))
    S_ft = list(range(5, n_orb))
    keep_mask = np.isin(y_val[3], S_keep)
    X_keep_eval, y_keep_eval = X_val[3][keep_mask], y_val[3][keep_mask]
    before_keep = balanced_accuracy(
        y_keep_eval,
        m(torch.tensor(X_keep_eval, dtype=torch.long)).detach().argmax(-1).numpy(),
        classes_present=S_keep,
    )
    X_ft, y_ft = sample_balanced_bouquet(rng, g_tab, b_info, [3], 440, allowed_orbits=S_ft)
    m.train()
    opt_ft = torch.optim.AdamW(m.parameters(), lr=2e-3, weight_decay=0.0)
    for _ in range(steps_p2):
        opt_ft.zero_grad()
        idx = rng.integers(0, len(y_ft[3]), size=64)
        xb = torch.tensor(X_ft[3][idx], dtype=torch.long)
        yb = torch.tensor(y_ft[3][idx], dtype=torch.long)
        F.cross_entropy(m(xb), yb).backward()
        opt_ft.step()
    m.eval()
    with torch.no_grad():
        after_pred = m(torch.tensor(X_keep_eval, dtype=torch.long)).argmax(-1).numpy()
    after_keep = balanced_accuracy(y_keep_eval, after_pred, classes_present=S_keep)

    return {
        "arm": "Arm1_S3_bouquet",
        "group": "S3_bouquet",
        "model": model_name,
        "seed": seed,
        "n_params": n_params,
        "unitary_max_err": unitary_err,
        "homomorphism_err": hom_loss_val,
        **eval_res,
        "tts": tts_res,
        "forgetting_before_keep": before_keep,
        "forgetting_after_keep": after_keep,
        "forgetting_drop": float(before_keep - after_keep),
    }


# =============================================================================
# Arm 2: Content-Geometry Tradeoff (Ren & LeCun 2026 + SADL) vs Free-Energy Ops
# =============================================================================

def build_dual_timescale_world(world_name: str, seed: int = 0) -> dict:
    """
    24-state dual-timescale monoid world: (fast_state in [0..7], slow_state in [0..2]).
    Actions a in {0, 1, 2, 3} act strongly on fast state and couple to slow state only on
    sparse contact events (mixing slow factor ~8x slower than fast geometry).
    """
    rng = np.random.default_rng(700 + seed + (0 if "C8" in world_name else 31))
    n_fast, n_slow = 8, 3
    n_states = n_fast * n_slow  # 24

    if world_name == "C8_slow3":
        # Actions: +1 mod 8, -1 mod 8, +2 mod 8, stay
        shifts = [1, 7, 2, 0]
        def fast_step(f, a):
            return (f + shifts[a]) % 8
        # Shortest path graph distance on C8 ring
        dist_fast = np.zeros((n_fast, n_fast), dtype=np.float64)
        for i in range(n_fast):
            for j in range(n_fast):
                d = abs(i - j)
                dist_fast[i, j] = min(d, n_fast - d)
    else:  # D4_slow3
        d4 = make_d4_group()
        mul4 = d4["mul"]
        # Pick 4 generators/actions including rotation r (idx != 0), flip s, r^-1, id
        # Find two elements of order 4 and order 2 cleanly:
        acts = [0]
        for g in range(1, 8):
            if int(mul4[g, g]) != 0:
                acts.append(g)
                acts.append(int(d4["inv"][g]))
                break
        for g in range(1, 8):
            if int(mul4[g, g]) == 0 and g not in acts:
                acts.append(g)
                break
        acts = (acts + [0, 1, 2, 3])[:4]
        def fast_step(f, a):
            return int(mul4[f, acts[a]])
        # Shortest BFS path distance on Cayley graph
        dist_fast = np.full((n_fast, n_fast), 99.0)
        for src in range(n_fast):
            dist_fast[src, src] = 0
            q = [src]
            for u in q:
                for a in range(4):
                    v = fast_step(u, a)
                    if dist_fast[src, v] > dist_fast[src, u] + 1:
                        dist_fast[src, v] = dist_fast[src, u] + 1
                        q.append(v)

    n_acts = 4
    trans = np.zeros((n_states, n_acts), dtype=np.int64)
    P = np.zeros((n_states, n_states), dtype=np.float64)
    for f in range(n_fast):
        for s in range(n_slow):
            sid = f * n_slow + s
            for a in range(n_acts):
                fn = fast_step(f, a)
                # Sparse contact event advances slow state ONLY when fast state hits 0 via nontrivial action
                sn = (s + 1) % n_slow if (f == 0 and a != 0 and fn != 0) else s
                nid = fn * n_slow + sn
                trans[sid, a] = nid
                P[sid, nid] += 1.0 / n_acts

    # Observation map in R^32: orthogonal factor codes + slow-state subspace + nonlinear mix + fixed sensory nuisance
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
            # Modest SNR slow factor (Ren & LeCun 2026: hard-to-predict / lower-variance than fast factor)
            v[8:14] = slow_code[s] * 0.45
            v[14:] = rng.normal(scale=0.18, size=obs_dim - 14)  # irreducible nuisance dims
            base_feats[f * n_slow + s] = (Q @ v).astype(np.float32)

    return {
        "name": world_name,
        "n_fast": n_fast,
        "n_slow": n_slow,
        "n_states": n_states,
        "n_acts": n_acts,
        "obs_dim": obs_dim,
        "trans": trans,
        "P": P,
        "dist_fast": dist_fast,
        "base_feats": base_feats,
    }


def _centered_cos(K1: np.ndarray, K2: np.ndarray) -> float:
    n = K1.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    C1 = H @ K1 @ H
    C2 = H @ K2 @ H
    denom = float(np.linalg.norm(C1) * np.linalg.norm(C2))
    return float(np.sum(C1 * C2) / denom) if denom > 1e-12 else 0.0


def compute_free_energy_operators(w: dict, lam_grid: np.ndarray) -> dict:
    """Compute exact heat-filtered Kubo-Ando G_gm_heat(lam) and Matrix-KL X_kl_gm(lam) on the 24-state graph."""
    P = w["P"]
    n = w["n_states"]
    X = w["base_feats"].astype(np.float64)
    X = X - X.mean(axis=0, keepdims=True)
    # Discrete-time discounted Controllability/Observability balanced Gramians (rho < 1 guaranteed SPD!)
    rho = 0.85
    A = rho * P.T
    Wc = solve_discrete_lyapunov(A, np.eye(n))
    Wc = 0.5 * (Wc + Wc.T)
    Wo = solve_discrete_lyapunov(A.T, X @ X.T)
    Wo = 0.5 * (Wo + Wo.T)
    # Symmetrize SPD floor cleanly
    def _floor_spd(M):
        vals, vecs = eigh(0.5 * (M + M.T))
        vals = np.maximum(vals, 1e-6)
        return (vecs * vals) @ vecs.T

    Wc = _floor_spd(Wc)
    Wo = _floor_spd(Wo)
    Wc_half = fractional_matrix_power(Wc, 0.5).real
    Wc_nhalf = fractional_matrix_power(Wc, -0.5).real
    mid = _floor_spd(Wc_nhalf @ Wo @ Wc_nhalf)
    G0 = _floor_spd(Wc_half @ fractional_matrix_power(mid, 0.5).real @ Wc_half)

    # Normalized graph Laplacian of transition graph
    Psym = 0.5 * (P + P.T)
    Dinv2 = np.diag(1.0 / np.sqrt(np.maximum(Psym.sum(axis=1), 1e-8)))
    L_kin = np.eye(n) - Dinv2 @ Psym @ Dinv2
    L_kin = 0.5 * (L_kin + L_kin.T)

    vals0, vecs0 = eigh(G0)
    logG0 = (vecs0 * np.log(np.maximum(vals0, 1e-8))) @ vecs0.T

    G_gm_ops = []
    X_kl_ops = []
    for lam in lam_grid:
        E = expm(-0.5 * lam * L_kin)
        G_gm_ops.append(E @ G0 @ E)
        X_kl_ops.append(expm(logG0 - lam * L_kin))
    return {"G_gm_heat": G_gm_ops, "X_kl_gm": X_kl_ops, "lam_grid": lam_grid}


def run_arm2_jepa_task(world_name: str, obj_name: str, seed: int, steps: int = 1200) -> dict:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    torch.set_num_threads(1)
    torch.manual_seed(seed)
    rng = np.random.default_rng(5000 + seed * 89 + (0 if "C8" in world_name else 41))

    w = build_dual_timescale_world(world_name, seed=0)
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

    params = list(enc.parameters()) + list(pred.parameters())
    opt = torch.optim.AdamW(params, lr=2e-3, weight_decay=1e-4)

    # Pre-generate training transitions (t, t+1, t+2) for slowness + predictor loss
    def sample_batch(B: int):
        s0 = rng.integers(0, n_states, size=B)
        a0 = rng.integers(0, n_acts, size=B)
        s1 = trans[s0, a0]
        a1 = rng.integers(0, n_acts, size=B)
        s2 = trans[s1, a1]
        x0 = base_feats[s0] + rng.normal(scale=0.18, size=(B, obs_dim)).astype(np.float32)
        x1 = base_feats[s1] + rng.normal(scale=0.18, size=(B, obs_dim)).astype(np.float32)
        x2 = base_feats[s2] + rng.normal(scale=0.18, size=(B, obs_dim)).astype(np.float32)
        a0_oh = np.eye(n_acts, dtype=np.float32)[a0]
        return (
            torch.from_numpy(x0), torch.from_numpy(x1), torch.from_numpy(x2),
            torch.from_numpy(a0_oh),
        )

    for step in range(steps):
        opt.zero_grad()
        x0, x1, x2, a0_oh = sample_batch(128)
        z0 = enc(x0)
        z1 = enc(x1)
        z_hat, gate = pred(z0, a0_oh)

        if obj_name == "jepa_sg":
            with torch.no_grad():
                zt = target_enc(x1)
            l_pred = F.mse_loss(z_hat, zt)
            # Mild variance collapse prevention matching VicReg/SG baseline
            std_z = torch.sqrt(z0.var(dim=0) + 1e-4)
            loss = l_pred + 0.1 * F.relu(1.0 - std_z).mean()

        elif obj_name == "jepa_svreg":
            # End-to-end predictor + Sliced Variance Regularization (Ren & LeCun 2026) along random directions
            l_pred = F.mse_loss(z_hat, z1)
            dirs = torch.randn(lat_dim, 64)
            dirs = dirs / (dirs.norm(dim=0, keepdim=True) + 1e-8)
            proj = z0 @ dirs  # (B, 64)
            std_proj = torch.sqrt(proj.var(dim=0) + 1e-4)
            l_sv = (F.relu(1.0 - std_proj) ** 2).mean()
            loss = l_pred + 4.0 * l_sv

        elif obj_name == "jepa_slow_svreg":
            # Slow SVReg (Ren & LeCun 2026): SVReg + explicit slowness term + gated residual predictor
            l_pred = F.mse_loss(z_hat, z1)
            dirs = torch.randn(lat_dim, 64)
            dirs = dirs / (dirs.norm(dim=0, keepdim=True) + 1e-8)
            proj = z0 @ dirs
            std_proj = torch.sqrt(proj.var(dim=0) + 1e-4)
            l_sv = (F.relu(1.0 - std_proj) ** 2).mean()
            # Slowness preserves slowly varying features while preventing fast-step distortion
            l_slow = 0.45 * F.mse_loss(z1, z0) + 0.05 * gate.mean()
            loss = l_pred + 4.0 * l_sv + l_slow

        elif obj_name == "jepa_sadl":
            # SADL (arXiv:2611.21596): Demand-Supply pairwise distance constraint on encoder directly
            l_pred = F.mse_loss(z_hat, z1)
            dirs = torch.randn(lat_dim, 64)
            dirs = dirs / (dirs.norm(dim=0, keepdim=True) + 1e-8)
            proj = z0 @ dirs
            std_proj = torch.sqrt(proj.var(dim=0) + 1e-4)
            l_sv = (F.relu(1.0 - std_proj) ** 2).mean()
            # Supply pairwise diff in encoder vs demanded spread
            zc = z0 - z0.mean(dim=0, keepdim=True)
            pdist = torch.cdist(zc, zc, p=2) / math.sqrt(lat_dim)
            target_spread = 1.25
            eye_mask = 1.0 - torch.eye(zc.shape[0])
            l_sadl = (F.relu(target_spread - pdist) * eye_mask).mean()
            loss = l_pred + 2.5 * l_sv + 2.0 * l_sadl
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

    # 1. Geometry metrics: route jaggedness over 2-step random action walks + shortest-path distance correlation
    Zc = Z - Z.mean(axis=0, keepdims=True)
    # Walk jaggedness along fast ring steps (holding slow fixed so we measure geometric smoothness of map)
    jags = []
    for f in range(w["n_fast"]):
        for s in range(w["n_slow"]):
            s0 = f * w["n_slow"] + s
            s1 = trans[s0, 0]
            s2 = trans[s1, 0]
            # If slow changed at step, skip to measure pure navigation map geometry or include all
            if s1 % w["n_slow"] == s and s2 % w["n_slow"] == s:
                d01 = np.linalg.norm(Z[s1] - Z[s0])
                d12 = np.linalg.norm(Z[s2] - Z[s1])
                d02 = np.linalg.norm(Z[s2] - Z[s0])
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

    # 2. Content metrics: held-out noisy evaluation Ridge R^2 for fast cos/sin and slow one-hot
    eval_rng = np.random.default_rng(9001 + seed)
    B_eval = 512
    s_tr = eval_rng.integers(0, n_states, size=B_eval)
    s_te = eval_rng.integers(0, n_states, size=B_eval)
    x_etr = base_feats[s_tr] + eval_rng.normal(scale=0.18, size=(B_eval, obs_dim)).astype(np.float32)
    x_ete = base_feats[s_te] + eval_rng.normal(scale=0.18, size=(B_eval, obs_dim)).astype(np.float32)
    with torch.no_grad():
        Ztr = enc(torch.from_numpy(x_etr)).numpy().astype(np.float64)
        Zte = enc(torch.from_numpy(x_ete)).numpy().astype(np.float64)

    def ridge_r2(Z_a, Y_a, Z_b, Y_b, reg=1e-2):
        # Center targets
        Za = np.column_stack([Z_a, np.ones(len(Z_a))])
        Zb = np.column_stack([Z_b, np.ones(len(Z_b))])
        W = np.linalg.solve(Za.T @ Za + reg * np.eye(Za.shape[1]), Za.T @ Y_a)
        pred = Zb @ W
        ss_res = np.sum((Y_b - pred) ** 2)
        ss_tot = np.sum((Y_b - Y_b.mean(axis=0, keepdims=True)) ** 2)
        return float(1.0 - ss_res / max(ss_tot, 1e-12))

    Yf_tr = np.eye(w["n_fast"])[s_tr // 3]
    Yf_te = np.eye(w["n_fast"])[s_te // 3]
    Ys_tr = np.eye(w["n_slow"])[s_tr % 3]
    Ys_te = np.eye(w["n_slow"])[s_te % 3]
    r2_fast = ridge_r2(Ztr, Yf_tr, Zte, Yf_te)
    r2_slow = ridge_r2(Ztr, Ys_tr, Zte, Ys_te)

    # Effective rank
    sv = np.linalg.svd(Zc, compute_uv=False)
    sv = sv[sv > 1e-10]
    p_sv = (sv ** 2) / np.sum(sv ** 2)
    eff_rank = float(np.exp(-np.sum(p_sv * np.log(p_sv + 1e-12))))

    # 3. Free-energy operator alignment (best lambda & centered cosine vs G_gm_heat & X_kl_gm)
    lam_grid = np.linspace(0.0, 4.0, 41)
    ops = compute_free_energy_operators(w, lam_grid)
    K_z = Zc @ Zc.T

    best_cos_gm, best_lam_gm = -1.0, 0.0
    best_cos_kl, best_lam_kl = -1.0, 0.0
    for lam, G_op, X_op in zip(lam_grid, ops["G_gm_heat"], ops["X_kl_gm"]):
        cg = _centered_cos(K_z, G_op)
        ck = _centered_cos(K_z, X_op)
        if cg > best_cos_gm:
            best_cos_gm, best_lam_gm = cg, float(lam)
        if ck > best_cos_kl:
            best_cos_kl, best_lam_kl = ck, float(lam)

    return {
        "arm": "Arm2_ContentGeometry",
        "world": world_name,
        "objective": obj_name,
        "seed": seed,
        "jag": jag,
        "r_geom": r_geom,
        "r2_fast": r2_fast,
        "r2_slow": r2_slow,
        "eff_rank": eff_rank,
        "best_cos_G_gm_heat": best_cos_gm,
        "best_lam_G_gm_heat": best_lam_gm,
        "best_cos_X_kl_gm": best_cos_kl,
        "best_lam_X_kl_gm": best_lam_kl,
    }


# =============================================================================
# Algebraic Laws Audit (Frobenius + Concept Quantale + U(d) Word Invariance)
# =============================================================================

def run_algebraic_audit() -> dict:
    rng = np.random.default_rng(2026)

    # 1. Group-Algebra Frobenius Monoid & Separability Laws on S3, D4, A4
    frob_results = {}
    for gname, gfn in [("S3", make_s3_group), ("D4", make_d4_group), ("A4", make_a4_group)]:
        gt = gfn()
        G = gt["n"]
        mul = gt["mul"]
        inv = gt["inv"]
        f = rng.normal(size=G)
        h = rng.normal(size=G)

        def frob_mul(u, v):
            out = np.zeros(G)
            for x in range(G):
                s = 0.0
                for a in range(G):
                    s += u[a] * v[mul[inv[a], x]]
                out[x] = s
            return out

        def frob_comul(u):
            return np.array([[u[mul[x, y]] for y in range(G)] for x in range(G)])

        def mul_left_tensor(u, M):
            out = np.zeros((G, G))
            for x in range(G):
                for y in range(G):
                    out[x, y] = sum(u[a] * M[mul[inv[a], x], y] for a in range(G))
            return out

        def mul_right_tensor(M, v):
            out = np.zeros((G, G))
            for x in range(G):
                for y in range(G):
                    out[x, y] = sum(M[x, b] * v[mul[inv[b], y]] for b in range(G))
            return out

        def contract_mul(M):
            return np.array([sum(M[a, mul[inv[a], x]] for a in range(G)) for x in range(G)])

        lhs_f = frob_comul(frob_mul(f, h))
        rhs_l = mul_left_tensor(f, frob_comul(h))
        rhs_r = mul_right_tensor(frob_comul(f), h)
        spec_l = contract_mul(frob_comul(f))
        spec_r = G * f
        frob_results[gname] = {
            "frob_left_err": float(np.max(np.abs(lhs_f - rhs_l))),
            "frob_right_err": float(np.max(np.abs(lhs_f - rhs_r))),
            "frob_special_err": float(np.max(np.abs(spec_l - spec_r))),
        }

    # 2. Finite Residuated Concept Quantale check on C3 and S3 left-ideal / Cayley context
    # A clean residuated relation: S = monoid, T = S x P, R(s, (t, p)) := (s * t in U_p)
    # Wait: symmetric two-sided nuclear relation: R(s, t) := True iff s belongs to normal/central conjugation kernel?
    # Even simpler exact test: Cayley left-ideal relation on S = C4 where T = subsets closed under shift?
    # Use a bi-invariant partition/normal subgroup K of S3 (K = A3, index 2):
    # R(s, (u, v, target_coset)) := ((u * s * v) mod K == target_coset). Wait: this gives exact IsResiduatedRel!
    s3 = make_s3_group()
    mul3 = s3["mul"]
    # Exact parity coset on S3: class ids from make_s3_group(): 1-element id + two 3-cycles belong to A3; 3 transpositions odd!
    # Check element-wise cycle order: mul[g, mul[g, g]] == 0 => even (A3)
    even = np.array([1 if int(mul3[g, mul3[g, g]]) == 0 else 0 for g in range(6)], dtype=np.int64)
    # R(s, (u, v, c)) := (even[mul[mul[u, s], v]] == c)
    T_pts = [(u, v, c) for u in range(6) for v in range(6) for c in (0, 1)]

    def R_fn(s, tp):
        u, v, c = tp
        return int(even[mul3[mul3[u, s], v]]) == c

    def gamma_set(A_mask: int) -> int:
        # polarUp
        ups = [tp for tp in T_pts if all(R_fn(s, tp) for s in range(6) if (A_mask >> s) & 1)]
        out = 0
        for s in range(6):
            if all(R_fn(s, tp) for tp in ups):
                out |= (1 << s)
        return out

    # Check residuated stability (IsResiduatedRel) & closed concept monoid + residuation laws on all 2^6 subsets
    res_viol = 0
    for s in range(6):
        for tp in T_pts:
            mL = sum((1 << x) for x in range(6) if R_fn(int(mul3[x, s]), tp))
            mR = sum((1 << x) for x in range(6) if R_fn(int(mul3[s, x]), tp))
            if gamma_set(mL) != mL:
                res_viol += 1
            if gamma_set(mR) != mR:
                res_viol += 1

    closed_masks = sorted({gamma_set(m) for m in range(64)})
    def c_mul(A, B):
        raw = 0
        for a in range(6):
            if (A >> a) & 1:
                for b in range(6):
                    if (B >> b) & 1:
                        raw |= (1 << int(mul3[a, b]))
        return gamma_set(raw)

    c_one = gamma_set(1 << 0)
    quantale_assoc_viol = 0
    quantale_res_viol = 0
    for A in closed_masks:
        if c_mul(A, c_one) != A or c_mul(c_one, A) != A:
            quantale_res_viol += 1
        for B in closed_masks:
            for C in closed_masks:
                if c_mul(c_mul(A, B), C) != c_mul(A, c_mul(B, C)):
                    quantale_assoc_viol += 1
                resR = sum((1 << x) for x in range(6) if all(((C >> int(mul3[a, x])) & 1) for a in range(6) if (A >> a) & 1))
                lhs = ((c_mul(A, B) & C) == c_mul(A, B))
                rhs = ((B & resR) == B)
                if lhs != rhs:
                    quantale_res_viol += 1

    # 3. Exact U(d) A4 Homomorphism word-length trace invariance (L = 4 vs 8 vs 16)
    a4 = make_a4_group()
    mul4 = a4["mul"]
    inv4 = a4["inv"]
    # Regular unitary permutation matrices U_g in U(12) give an exact faithful unitary homomorphism!
    U_reg = np.zeros((12, 12, 12), dtype=np.complex128)
    for g in range(12):
        for h in range(12):
            U_reg[g, mul4[g, h], h] = 1.0
    # Add random global unitary gauge Q in U(12) and skew phases
    Z = rng.normal(size=(12, 12)) + 1j * rng.normal(size=(12, 12))
    Qg, _ = np.linalg.qr(Z)
    U_gauged = np.array([Qg @ U_reg[g] @ Qg.conj().T for g in range(12)])
    # Compare product along words of L=4, 8, 16 with equal group product vs conjugate
    w4 = [1, 2, 5, 7]
    p_tot = 0
    for x in w4:
        p_tot = int(mul4[x, p_tot])
    w8 = w4 + [0, 3, int(inv4[3]), 0]
    k = 9
    w16 = [int(mul4[mul4[k, x], inv4[k]]) for x in w8] + [4, int(inv4[4])] * 4

    def eval_w(w):
        P = np.eye(12, dtype=np.complex128)
        for x in w:
            P = U_gauged[x] @ P
        return np.trace(P)

    t4, t8, t16 = eval_w(w4), eval_w(w8), eval_w(w16)
    hom_len_err = float(max(abs(t4 - t8), abs(t4 - t16)))

    return {
        "frob_laws": frob_results,
        "quantale_n_closed": len(closed_masks),
        "quantale_res_rel_violations": res_viol,
        "quantale_assoc_violations": quantale_assoc_viol,
        "quantale_residuation_violations": quantale_res_viol,
        "homomorphism_word_length_trace_err": hom_len_err,
    }


def _worker_run(job: dict) -> dict:
    t0 = time.time()
    kind = job["kind"]
    if kind == "arm1_a4":
        res = run_arm1_single_task("A4", job["model"], job["seed"], job["steps_p1"], job["steps_p2"])
    elif kind == "arm1_bouquet":
        res = run_arm1_bouquet_task(job["model"], job["seed"], job["steps_p1"], job["steps_p2"])
    elif kind == "arm2":
        res = run_arm2_jepa_task(job["world"], job["objective"], job["seed"], job["steps"])
    else:
        raise ValueError(kind)
    res["elapsed_s"] = round(time.time() - t0, 2)
    return res


def compute_verdicts(arm1_runs: List[dict], arm2_runs: List[dict], audit: dict) -> dict:
    def filt(runs, **kw):
        return [r for r in runs if all(r.get(k) == v for k, v in kw.items())]

    def mean_key(runs, key):
        return float(np.mean([r[key] for r in runs])) if runs else 0.0

    # HGH.1: UFR Homomorphic U(d) OOD Length Invariance
    a4_ufr = filt(arm1_runs, arm="Arm1_A4", model="cayley_unitary_ufr_grounded")
    a4_fer = filt(arm1_runs, arm="Arm1_A4", model="cayley_unitary_fer")
    a4_lin = filt(arm1_runs, arm="Arm1_A4", model="cayley_unitary_varlen_linear")
    bq_ufr = filt(arm1_runs, arm="Arm1_S3_bouquet", model="cayley_unitary_ufr_grounded")
    bq_fer = filt(arm1_runs, arm="Arm1_S3_bouquet", model="cayley_unitary_fer")
    bq_lin = filt(arm1_runs, arm="Arm1_S3_bouquet", model="cayley_unitary_varlen_linear")

    a4_ufr_ood = [mean_key(a4_ufr, f"L{L}_bacc") for L in (4, 5, 6, 8)]
    bq_ufr_ood = [mean_key(bq_ufr, f"L{L}_bacc") for L in (3, 4, 6)]
    hgh1_pass = (
        min(a4_ufr_ood) >= 0.98
        and min(bq_ufr_ood) >= 0.98
        and mean_key(a4_ufr, "L8_bacc") - max(mean_key(a4_fer, "L8_bacc"), mean_key(a4_lin, "L8_bacc")) >= 0.15
        and mean_key(bq_ufr, "L6_bacc") - max(mean_key(bq_fer, "L6_bacc"), mean_key(bq_lin, "L6_bacc")) >= 0.15
    )

    # HGH.2: TTS scaling vs UFR & UFR forgetting resistance
    a4_gru = filt(arm1_runs, arm="Arm1_A4", model="ordered_gru")
    bq_gru = filt(arm1_runs, arm="Arm1_S3_bouquet", model="joint_bouquet_gru")
    a4_tts_k1 = float(np.mean([r["tts"]["L4"]["K1"] for r in a4_gru]))
    a4_tts_k16 = float(np.mean([r["tts"]["L4"]["K16"] for r in a4_gru]))
    a4_tts_l8_k16 = float(np.mean([r["tts"]["L8"]["K16"] for r in a4_gru]))
    bq_tts_k1 = float(np.mean([r["tts"]["L3"]["K1"] for r in bq_gru]))
    bq_tts_k16 = float(np.mean([r["tts"]["L3"]["K16"] for r in bq_gru]))
    bq_tts_l6_k16 = float(np.mean([r["tts"]["L6"]["K16"] for r in bq_gru]))

    a4_ret_diff = mean_key(a4_ufr, "forgetting_after_keep") - mean_key(a4_fer, "forgetting_after_keep")
    bq_ret_diff = mean_key(bq_ufr, "forgetting_after_keep") - mean_key(bq_fer, "forgetting_after_keep")
    tts_helps = ((a4_tts_k16 - a4_tts_k1 >= 0.02) or (bq_tts_k16 - bq_tts_k1 >= 0.02))
    ufr_beats_tts_ood = (mean_key(a4_ufr, "L8_bacc") > a4_tts_l8_k16 + 0.15) and (mean_key(bq_ufr, "L6_bacc") > bq_tts_l6_k16 + 0.15)
    forgetting_res = (a4_ret_diff >= 0.05) and (bq_ret_diff >= 0.05)
    hgh2_verdict = "HELD" if (tts_helps and ufr_beats_tts_ood and forgetting_res) else (
        "BROKEN" if (not ufr_beats_tts_ood and not forgetting_res) else "NEITHER"
    )

    # HGH.3: Content-Geometry Tradeoff (Ren & LeCun 2026 + SADL)
    sg = filt(arm2_runs, objective="jepa_sg")
    sv = filt(arm2_runs, objective="jepa_svreg")
    sl = filt(arm2_runs, objective="jepa_slow_svreg")
    sa = filt(arm2_runs, objective="jepa_sadl")
    geom_gain = mean_key(sv, "jag") < mean_key(sg, "jag") and mean_key(sv, "r_geom") > mean_key(sg, "r_geom")
    slow_drop = mean_key(sl, "r2_slow") - mean_key(sv, "r2_slow") >= 0.05
    slow_geom = mean_key(sl, "jag") < mean_key(sg, "jag")
    sadl_ok = mean_key(sa, "eff_rank") >= 3.0 and mean_key(sa, "r2_fast") >= 0.80
    hgh3_verdict = "HELD" if (geom_gain and slow_drop and slow_geom and sadl_ok) else (
        "BROKEN" if (not geom_gain and not slow_drop) else "NEITHER"
    )

    # HGH.4: Temperature Alignment G_gm_heat / X_kl_gm vs JEPA
    cos_all = float(np.mean([max(r["best_cos_G_gm_heat"], r["best_cos_X_kl_gm"]) for r in arm2_runs]))
    lam_sv = mean_key(sv, "best_lam_G_gm_heat")
    lam_sl = mean_key(sl, "best_lam_G_gm_heat")
    lam_sg = mean_key(sg, "best_lam_G_gm_heat")
    hgh4_verdict = "HELD" if (cos_all >= 0.60 and lam_sv > lam_sg) else (
        "BROKEN" if cos_all < 0.45 else "NEITHER"
    )

    # HGH.5: Exact Algebraic Laws + Neural Unitarity
    max_frob = max(max(v.values()) for v in audit["frob_laws"].values())
    max_u_err = max([r["unitary_max_err"] for r in arm1_runs], default=0.0)
    hgh5_pass = (
        max_frob < 1e-10
        and audit["quantale_res_rel_violations"] == 0
        and audit["quantale_assoc_violations"] == 0
        and audit["quantale_residuation_violations"] == 0
        and audit["homomorphism_word_length_trace_err"] < 1e-10
        and max_u_err < 1e-5
    )

    return {
        "HGH.1": "HELD" if hgh1_pass else "BROKEN",
        "HGH.2": hgh2_verdict,
        "HGH.3": hgh3_verdict,
        "HGH.4": hgh4_verdict,
        "HGH.5": "HELD" if hgh5_pass else "BROKEN",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--raw-dir", type=str, default=None)
    args = parser.parse_args()

    t_start = time.time()
    audit = run_algebraic_audit()
    print(f"ALGEBRAIC_AUDIT: max_frob={max(max(v.values()) for v in audit['frob_laws'].values()):.2e}, "
          f"quantale_viol=({audit['quantale_res_rel_violations']},{audit['quantale_assoc_violations']},{audit['quantale_residuation_violations']}), "
          f"hom_len_err={audit['homomorphism_word_length_trace_err']:.2e}")

    jobs = []
    if args.smoke:
        for model in ["cayley_unitary_fer", "cayley_unitary_varlen_linear", "cayley_unitary_ufr_grounded", "ordered_gru"]:
            jobs.append({"kind": "arm1_a4", "model": model, "seed": 0, "steps_p1": 250, "steps_p2": 50})
        for model in ["cayley_unitary_ufr_grounded", "joint_bouquet_gru"]:
            jobs.append({"kind": "arm1_bouquet", "model": model, "seed": 0, "steps_p1": 250, "steps_p2": 50})
        for obj in ["jepa_sg", "jepa_svreg", "jepa_slow_svreg", "jepa_sadl"]:
            jobs.append({"kind": "arm2", "world": "C8_slow3", "objective": obj, "seed": 0, "steps": 250})
    else:
        for seed in [0, 1, 2]:
            for model in ["cayley_unitary_fer", "cayley_unitary_varlen_linear", "cayley_unitary_ufr_grounded", "ordered_gru"]:
                jobs.append({"kind": "arm1_a4", "model": model, "seed": seed, "steps_p1": 900, "steps_p2": 200})
            for model in ["cayley_unitary_fer", "cayley_unitary_varlen_linear", "cayley_unitary_ufr_grounded", "joint_bouquet_gru"]:
                jobs.append({"kind": "arm1_bouquet", "model": model, "seed": seed, "steps_p1": 900, "steps_p2": 200})
            for world in ["C8_slow3", "D4_slow3"]:
                for obj in ["jepa_sg", "jepa_svreg", "jepa_slow_svreg", "jepa_sadl"]:
                    jobs.append({"kind": "arm2", "world": world, "objective": obj, "seed": seed, "steps": 1200})

    print(f"Launching {len(jobs)} jobs with workers={args.workers}...")
    raw_dir = pathlib.Path(args.raw_dir) if args.raw_dir else None
    if raw_dir:
        raw_dir.mkdir(parents=True, exist_ok=True)

    results = []
    if args.workers <= 1:
        for idx, job in enumerate(jobs, 1):
            r = _worker_run(job)
            results.append(r)
            if raw_dir:
                (raw_dir / f"run_{idx:03d}.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
            print(f"[{idx}/{len(jobs)}] {r.get('arm')} | {r.get('model', r.get('objective'))} | {r['elapsed_s']}s")
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as ex:
            for idx, r in enumerate(ex.map(_worker_run, jobs), 1):
                results.append(r)
                if raw_dir:
                    (raw_dir / f"run_{idx:03d}.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
                if idx % 6 == 0 or idx == len(jobs) or args.smoke:
                    print(f"[{idx}/{len(jobs)}] {r.get('arm')} | {r.get('model', r.get('objective'))} | {r['elapsed_s']}s")

    arm1_runs = [r for r in results if r["arm"].startswith("Arm1")]
    arm2_runs = [r for r in results if r["arm"] == "Arm2_ContentGeometry"]
    verdicts = compute_verdicts(arm1_runs, arm2_runs, audit)

    # Aggregate summaries cleanly
    arm1_agg = {}
    for arm in sorted({r["arm"] for r in arm1_runs}):
        arm1_agg[arm] = {}
        for model in sorted({r["model"] for r in arm1_runs if r["arm"] == arm}):
            sub = [r for r in arm1_runs if r["arm"] == arm and r["model"] == model]
            keys = [k for k in sub[0] if k.endswith("_bacc") or k.endswith("_acc") or k.startswith("forgetting_") or k in ("unitary_max_err", "homomorphism_err")]
            entry = {"n_runs": len(sub), "n_params": sub[0]["n_params"]}
            for k in keys:
                entry[k] = round(float(np.mean([r[k] for r in sub])), 5)
            if sub[0]["tts"]:
                tts_mean = {}
                for Lkey, kdict in sub[0]["tts"].items():
                    tts_mean[Lkey] = {K: round(float(np.mean([r["tts"][Lkey][K] for r in sub])), 5) for K in kdict}
                entry["tts"] = tts_mean
            arm1_agg[arm][model] = entry

    arm2_agg = {}
    for world in sorted({r["world"] for r in arm2_runs}):
        arm2_agg[world] = {}
        for obj in sorted({r["objective"] for r in arm2_runs if r["world"] == world}):
            sub = [r for r in arm2_runs if r["world"] == world and r["objective"] == obj]
            keys = ["jag", "r_geom", "r2_fast", "r2_slow", "eff_rank",
                    "best_cos_G_gm_heat", "best_lam_G_gm_heat", "best_cos_X_kl_gm", "best_lam_X_kl_gm"]
            arm2_agg[world][obj] = {k: round(float(np.mean([r[k] for r in sub])), 5) for k in keys}
    arm2_agg["overall_by_objective"] = {}
    for obj in sorted({r["objective"] for r in arm2_runs}):
        sub = [r for r in arm2_runs if r["objective"] == obj]
        keys = ["jag", "r_geom", "r2_fast", "r2_slow", "eff_rank",
                "best_cos_G_gm_heat", "best_lam_G_gm_heat", "best_cos_X_kl_gm", "best_lam_X_kl_gm"]
        arm2_agg["overall_by_objective"][obj] = {k: round(float(np.mean([r[k] for r in sub])), 5) for k in keys}

    summary = {
        "verdicts": verdicts,
        "total_runs": len(results),
        "total_elapsed_s": round(time.time() - t_start, 2),
        "algebraic_audit": audit,
        "arm1_summary": arm1_agg,
        "arm2_summary": arm2_agg,
    }

    if args.out:
        out_p = pathlib.Path(args.out)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("VERDICTS:", json.dumps(verdicts))
    print(f"COMPLETED {len(results)} runs in {summary['total_elapsed_s']}s")


if __name__ == "__main__":
    main()
