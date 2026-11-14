"""Untrusted search for lower-bound certificates (checked by cerp.kernel_bounds)."""

from __future__ import annotations

from itertools import combinations_with_replacement


def _vec(n, pts):
    return tuple(sum((p >> j) & 1 for p in pts) for j in range(n))


def not_threshold_cert(n, f, kmax=4):
    T = [p for p in range(1 << n) if (f >> p) & 1]
    F = [p for p in range(1 << n) if not (f >> p) & 1]
    if not T or not F:
        return None
    if n <= 6:
        for k in range(2, kmax + 1):
            sums = {}
            for a in combinations_with_replacement(T, k):
                sums.setdefault(_vec(n, a), a)
            for b in combinations_with_replacement(F, k):
                a = sums.get(_vec(n, b))
                if a is not None:
                    return {"pos": list(a), "neg": list(b)}
        return None
    if kmax >= 2 and len(T) <= 600 and len(F) <= 600:
        sums = {}
        for a in combinations_with_replacement(T, 2):
            sums.setdefault(_vec(n, a), a)
        for b in combinations_with_replacement(F, 2):
            a = sums.get(_vec(n, b))
            if a is not None:
                return {"pos": list(a), "neg": list(b)}
    if kmax >= 3:
        return _lp_farkas_witness(n, T, F)
    return None


def not_two_halfspaces_cert(n, f, kmax=3):
    """Bad sets of false points (supports of summability witnesses), returned only
    if they already force a monochromatic bad set under every 2-colouring."""
    T = [p for p in range(1 << n) if (f >> p) & 1]
    F = [p for p in range(1 << n) if not (f >> p) & 1]
    if not T or not F:
        return None
    best = {}
    for k in range(1, kmax + 1):
        sums = {}
        for a in combinations_with_replacement(T, k):
            sums.setdefault(_vec(n, a), a)
        for b in combinations_with_replacement(F, k):
            a = sums.get(_vec(n, b))
            if a is not None:
                S = frozenset(b)
                if not any(s <= S for s in best):
                    for s in [s for s in best if S < s]:
                        del best[s]
                    best[S] = {"set": sorted(S), "pos": list(a), "neg": list(b)}
        bad = list(best.values())
        if bad and _forces(bad):
            return bad
    return None


def _forces(bad):
    uni = sorted({q for b in bad for q in b["set"]})
    if len(uni) > 20:
        return False
    masks = [sum(1 << uni.index(q) for q in b["set"]) for b in bad]
    return all(any((s & c) == s or (s & c) == 0 for s in masks) for c in range(1 << len(uni)))


def _exact_fraction_witness(n, T_sub, F_sub):
    """Exact rational BFS witness via Fraction RREF over [T_sub | -F_sub]."""
    from fractions import Fraction
    from math import lcm

    cols = len(T_sub) + len(F_sub)
    if cols == 0 or not T_sub or not F_sub:
        return None
    # Equations: coords 0..n-1 sum to 0; sum(T) - sum(F) = 0; normalized via positive cp_model or Fraction
    # Solve homogeneous system [A; sum_T - sum_F] = 0 with a >= 0, b >= 0, sum_T > 0 via vertex/nullspace
    mat = []
    for j in range(n):
        row = [Fraction((p >> j) & 1) for p in T_sub] + [Fraction(-((q >> j) & 1)) for q in F_sub]
        mat.append(row)
    mat.append([Fraction(1)] * len(T_sub) + [Fraction(-1)] * len(F_sub))

    # Build RREF and find minimal non-negative null vector? Simpler: solve exact LP equality
    # with sum(T) == 1 by RREF on rows 0..n plus row sum(T) = 1:
    eqs = [r + [Fraction(0)] for r in mat]
    eqs.append([Fraction(1)] * len(T_sub) + [Fraction(0)] * len(F_sub) + [Fraction(1)])

    rows_n = len(eqs)
    piv_cols = []
    r = 0
    for c in range(cols):
        if r >= rows_n:
            break
        piv = next((rr for rr in range(r, rows_n) if eqs[rr][c] != 0), None)
        if piv is None:
            continue
        eqs[r], eqs[piv] = eqs[piv], eqs[r]
        pv = eqs[r][c]
        eqs[r] = [v / pv for v in eqs[r]]
        for rr in range(rows_n):
            if rr != r and eqs[rr][c] != 0:
                fac = eqs[rr][c]
                eqs[rr] = [eqs[rr][cc] - fac * eqs[r][cc] for cc in range(cols + 1)]
        piv_cols.append((r, c))
        r += 1
    for rr in range(r, rows_n):
        if eqs[rr][cols] != 0:
            return None
    sol = [Fraction(0)] * cols
    for pr, pc in piv_cols:
        sol[pc] = eqs[pr][cols]
    if any(v < 0 for v in sol):
        return None
    if sum(sol[:len(T_sub)]) <= 0:
        return None
    scale = 1
    for v in sol:
        scale = lcm(scale, v.denominator)
    ints = [int(v * scale) for v in sol]
    pos = [p for p, cnt in zip(T_sub, ints[:len(T_sub)]) for _ in range(cnt)]
    neg = [q for q, cnt in zip(F_sub, ints[len(T_sub):]) for _ in range(cnt)]
    if pos and len(pos) == len(neg) and _vec(n, pos) == _vec(n, neg):
        return {"pos": pos, "neg": neg}
    return None


def _lp_farkas_witness(n, T, F):
    """Find a small Farkas witness (pos, neg) showing conv(T) and conv(F) intersect,
    or return None if strictly separable."""
    if not T or not F:
        return None
    import numpy as np
    from scipy.optimize import linprog
    from ortools.sat.python import cp_model

    mT, mF = len(T), len(F)
    A = np.zeros((n + 2, mT + mF), dtype=float)
    for j in range(n):
        A[j, :mT] = [(p >> j) & 1 for p in T]
        A[j, mT:] = [-((q >> j) & 1) for q in F]
    A[n, :mT] = 1.0
    A[n + 1, mT:] = 1.0
    b = np.zeros(n + 2, dtype=float)
    b[n] = 1.0
    b[n + 1] = 1.0
    res = linprog(np.zeros(mT + mF), A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    if not res.success:
        return None

    x = res.x
    T_sub = [T[i] for i in range(mT) if x[i] > 1e-8]
    F_sub = [F[j] for j in range(mF) if x[mT + j] > 1e-8]
    if T_sub and F_sub:
        cm = cp_model.CpModel()
        av = [cm.NewIntVar(0, 1000, "") for _ in T_sub]
        bv = [cm.NewIntVar(0, 1000, "") for _ in F_sub]
        cm.Add(sum(av) >= 1)
        cm.Add(sum(av) == sum(bv))
        for j in range(n):
            cm.Add(sum(av[i] for i, p in enumerate(T_sub) if (p >> j) & 1)
                   == sum(bv[k] for k, q in enumerate(F_sub) if (q >> j) & 1))
        cm.Minimize(sum(av))
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 1.0
        if s.Solve(cm) in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            pos = [p for p, var in zip(T_sub, av) for _ in range(int(s.Value(var)))]
            neg = [q for q, var in zip(F_sub, bv) for _ in range(int(s.Value(var)))]
            if pos and len(pos) == len(neg) and _vec(n, pos) == _vec(n, neg):
                return {"pos": pos, "neg": neg}
        exact = _exact_fraction_witness(n, T_sub, F_sub)
        if exact is not None:
            return exact

    # Fallback: exact integer search on full (T, F) in case HiGHS picked a degenerate face
    cm = cp_model.CpModel()
    av = [cm.NewIntVar(0, 100, "") for _ in T]
    bv = [cm.NewIntVar(0, 100, "") for _ in F]
    cm.Add(sum(av) >= 1)
    cm.Add(sum(av) == sum(bv))
    for j in range(n):
        cm.Add(sum(av[i] for i, p in enumerate(T) if (p >> j) & 1)
               == sum(bv[k] for k, q in enumerate(F) if (q >> j) & 1))
    cm.Minimize(sum(av))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 2.0
    if s.Solve(cm) in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        pos = [p for p, var in zip(T, av) for _ in range(int(s.Value(var)))]
        neg = [q for q, var in zip(F, bv) for _ in range(int(s.Value(var)))]
        if pos and len(pos) == len(neg) and _vec(n, pos) == _vec(n, neg):
            return {"pos": pos, "neg": neg}
    return None


def not_threshold_cert_partial(n, f, care, kmax=4):
    """Untrusted search for a check_not_threshold_partial certificate: uses care points only."""
    T = [p for p in range(1 << n) if (care >> p) & 1 and (f >> p) & 1]
    F = [p for p in range(1 << n) if (care >> p) & 1 and not (f >> p) & 1]
    if not T or not F:
        return None
    if len(T) <= 600 and len(F) <= 600:
        sums = {}
        for a in combinations_with_replacement(T, 2):
            sums.setdefault(_vec(n, a), a)
        for b in combinations_with_replacement(F, 2):
            a = sums.get(_vec(n, b))
            if a is not None:
                return {"pos": list(a), "neg": list(b)}
    if n <= 6 and kmax >= 3 and len(T) <= 40 and len(F) <= 40:
        for k in range(3, kmax + 1):
            sums = {}
            for a in combinations_with_replacement(T, k):
                sums.setdefault(_vec(n, a), a)
            for b in combinations_with_replacement(F, k):
                a = sums.get(_vec(n, b))
                if a is not None:
                    return {"pos": list(a), "neg": list(b)}
    return _lp_farkas_witness(n, T, F)


def _find_short_odd_cycle(edges, F_pts):
    """Given edge pairs (q1, q2) over F_pts, return a short odd cycle list of pairs if any."""
    from collections import deque
    adj = {q: [] for q in F_pts}
    edge_map = {}
    for q1, q2, wit in edges:
        adj[q1].append(q2)
        adj[q2].append(q1)
        edge_map[(min(q1, q2), max(q1, q2))] = wit
    best_cycle = None
    for start in F_pts:
        if not adj[start]:
            continue
        dist = {start: 0}
        parent = {start: None}
        q = deque([start])
        while q:
            u = q.popleft()
            du = dist[u]
            if best_cycle is not None and 2 * du + 1 >= len(best_cycle):
                break
            for v in adj[u]:
                if v not in dist:
                    dist[v] = du + 1
                    parent[v] = u
                    q.append(v)
                elif (dist[u] - dist[v]) % 2 == 0:
                    # Reconstruct cycle between u and v back to LCA
                    pu, pv = [], []
                    cu, cv = u, v
                    while dist[cu] > dist[cv]:
                        pu.append(cu); cu = parent[cu]
                    while dist[cv] > dist[cu]:
                        pv.append(cv); cv = parent[cv]
                    while cu != cv:
                        pu.append(cu); cu = parent[cu]
                        pv.append(cv); cv = parent[cv]
                    nodes = [cu] + list(reversed(pu)) + pv
                    if len(nodes) % 2 == 1 and len(nodes) <= 19:
                        if best_cycle is None or len(nodes) < len(best_cycle):
                            best_cycle = nodes
                        if len(best_cycle) == 3:
                            break
            if best_cycle is not None and len(best_cycle) == 3:
                break
        if best_cycle is not None and len(best_cycle) == 3:
            break
    if best_cycle is None:
        return None
    bad = []
    L = len(best_cycle)
    for i in range(L):
        a, b = best_cycle[i], best_cycle[(i + 1) % L]
        wit = edge_map[(min(a, b), max(a, b))]
        bad.append(wit)
    return bad


def _minimize_bad(F, bad):
    """Shrink bad to an inclusion-minimal UNSAT core whose universe has <= 20 points."""
    from ortools.sat.python import cp_model

    def is_unsat(subset):
        uni = sorted({q for b in subset for q in b["set"]})
        if not uni:
            return False
        cm = cp_model.CpModel()
        col = {q: cm.NewBoolVar("") for q in uni}
        for b in subset:
            S = b["set"]
            cm.Add(sum(col[q] for q in S) >= 1)
            cm.Add(sum(col[q] for q in S) <= len(S) - 1)
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 1.0
        return s.Solve(cm) == cp_model.INFEASIBLE

    # Prefer keeping smaller sets first (remove largest redundant sets first)
    kept = sorted(bad, key=lambda b: len(b["set"]))
    for idx in range(len(kept) - 1, -1, -1):
        cand = kept[:idx] + kept[idx + 1:]
        if cand and is_unsat(cand):
            kept = cand
    return kept if _forces(kept) else None


def not_two_halfspaces_cert_partial(n, f, care, kmax=3, max_iters=64):
    """Untrusted search for check_not_two_halfspaces_partial: certifies that NO
    completion of f on `care` is an intersection of two halfspaces."""
    T = [p for p in range(1 << n) if (care >> p) & 1 and (f >> p) & 1]
    F = [p for p in range(1 << n) if (care >> p) & 1 and not (f >> p) & 1]
    if not T or not F:
        return None
    # 1. Fast k=2 bad pair graph (4-bit packed ints for speed on n <= 12)
    edges = []
    if len(T) <= 600 and len(F) <= 600:
        shift = 4
        t_pack = [sum(((p >> j) & 1) << (shift * j) for j in range(n)) for p in T]
        t_pair = {}
        for i in range(len(T)):
            pi = T[i]; ti = t_pack[i]
            for j in range(i, len(T)):
                t_pair.setdefault(ti + t_pack[j], (pi, T[j]))
        f_pack = [sum(((q >> j) & 1) << (shift * j) for j in range(n)) for q in F]
        for i in range(len(F)):
            qi = F[i]; fi = f_pack[i]
            for j in range(i + 1, len(F)):
                hit = t_pair.get(fi + f_pack[j])
                if hit is not None:
                    qj = F[j]
                    edges.append((qi, qj, {"set": [qi, qj], "pos": list(hit), "neg": [qi, qj]}))
        cyc = _find_short_odd_cycle(edges, F)
        if cyc is not None:
            return cyc

    # 2. CEGAR over 2-colourings of F using CP-SAT + LP Farkas cuts
    from ortools.sat.python import cp_model
    bad = [w for _, _, w in edges]
    seen_sets = {frozenset(w["set"]) for w in bad}
    cm = cp_model.CpModel()
    col = {q: cm.NewBoolVar(f"c_{q}") for q in F}
    cm.Add(col[F[0]] == 0)
    for w in bad:
        S = w["set"]
        cm.Add(col[S[0]] != col[S[1]])

    for _ in range(max_iters):
        s = cp_model.CpSolver()
        s.parameters.max_time_in_seconds = 2.0
        st = s.Solve(cm)
        if st == cp_model.INFEASIBLE:
            return _minimize_bad(F, bad)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        F0 = [q for q in F if not s.Value(col[q])]
        F1 = [q for q in F if s.Value(col[q])]
        w0 = _lp_farkas_witness(n, T, F0) if F0 else None
        w1 = _lp_farkas_witness(n, T, F1) if F1 else None
        if w0 is None and w1 is None:
            return None
        progressed = False
        for w in (w0, w1):
            if w is None:
                continue
            S = sorted(set(w["neg"]))
            fs = frozenset(S)
            if fs not in seen_sets and len(S) >= 2:
                seen_sets.add(fs)
                entry = {"set": S, "pos": w["pos"], "neg": w["neg"]}
                bad.append(entry)
                cm.Add(sum(col[q] for q in S) >= 1)
                cm.Add(sum(col[q] for q in S) <= len(S) - 1)
                progressed = True
        if not progressed:
            return None
    return None
