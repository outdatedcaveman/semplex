"""Exact minimum-cost layered threshold circuit enumeration and G_f-orbit quotienting (Gap A10).

For every NPN equivalence class (up to input permutation, input negation, and
optional output negation), enumerates ALL minimum-cost layered threshold circuits
with weights in [-W, W] (default W = 3), under two complementary hidden-unit
circuit-equivalence notions:

1. Hyperplane-partition equivalence (unoriented, matching `cerp/atlas.py` `H`):
   Each hidden unit is identified by its unordered Boolean partition pair
   `h = min(g, ~g)`. Flipping a hidden unit's output `g -> ~g` changes only
   incoming signs in the next layer and preserves cost/architecture; a minimal
   depth-2 width-w circuit is an unordered set `{h_1, ..., h_w}` of w distinct
   partition pairs that admits a weights-bounded output threshold gate computing f.
   Under this quotient, symmetric functions like XOR2 (n=2) and 3 classes at n=3
   have a single G_f-orbit ("the function fixes its mechanism").

2. Literal Boolean-function equivalence (oriented):
   Two circuits are the same iff their hidden units compute the same literal
   Boolean functions `{g_1, ..., g_w}` (`g` and `~g` distinguished). Each
   minimal unoriented width-w circuit lifts to `2^w` distinct oriented circuits.

Mathematical completeness on n <= 4 (all weights |w| <= 3):
- `atlas.build_all(4)` proves `W <= 3` covers 100% of all LTFs (4, 14, 104, 1882)
  and every class achieves minimum cost at depth <= 2 (1, [2], [3], or [4]).
- No depth >= 3 layered circuit can achieve minimum cost:
  - cost 3: [1, 1] reduces to cost 1.
  - cost 4: [2, 1] ends in a 1-input threshold gate, reducing to [2] (cost 3).
  - cost 5 (only `parity4` at n <= 4): any [2, 2], [3, 1], or [1, ...] has <= 3
    first-layer LTFs, impossible by `parity4_not_three_ltf_determined` (Bounds.lean).
"""

from __future__ import annotations

import itertools
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Iterable

import numpy as np

from . import atlas


def ltfs_with_bound(m: int, W: int = 3) -> tuple[dict[int, tuple[tuple[int, ...], int]], list[int]]:
    """Return ({truth_table: (weights, threshold)}, sorted truth tables) for m inputs, |w| <= W."""
    if m <= 4 and W >= 3:
        L, used_w = atlas.ltfs(m)
        if used_w <= W:
            return L, sorted(L)

    X = np.array([[(i >> j) & 1 for j in range(m)] for i in range(1 << m)], dtype=np.int64)
    pow2 = np.array([1 << i for i in range(1 << m)], dtype=np.int64)

    if m >= 5:
        full = (1 << (1 << m)) - 1
        T_m = atlas.transforms(m)
        idx_arr = np.array([idx for _, _, idx in T_m], dtype=np.int64)
        base_w = sorted(itertools.combinations_with_replacement(range(W + 1), m), key=lambda w: (sum(w), w))
        base_map: dict[int, tuple[tuple[int, ...], int]] = {}
        for w_tup in base_w:
            s_row = X @ np.array(w_tup, dtype=np.int64)
            threshs = sorted({int(v) for v in s_row})
            threshs.append(int(s_row.max()) + 1)
            for t in threshs:
                bits = int(((s_row >= t) * pow2).sum())
                if bits not in base_map:
                    base_map[bits] = (w_tup, t)

        base_items = sorted(base_map.items(), key=lambda kv: (sum(kv[1][0]), kv[0]))
        base_bits = np.array([kv[0] for kv in base_items], dtype=np.uint32)
        bit_pos = np.arange(1 << m, dtype=np.uint32)
        out: dict[int, tuple[tuple[int, ...], int]] = {}
        perm_neg = [(perm, neg) for perm, neg, _ in T_m]
        for s in range(0, len(base_bits), 256):
            chunk = base_bits[s:s + 256]
            bmats = ((chunk[:, None] >> bit_pos[None, :]) & np.uint32(1)).astype(np.uint8)
            pbytes = np.ascontiguousarray(np.packbits(bmats[:, idx_arr], axis=2, bitorder="little"))
            trans = pbytes.view(np.uint32).reshape(len(chunk), len(T_m))
            for row_i in range(len(chunk)):
                w_base, t_base = base_items[s + row_i][1]
                row_vals = trans[row_i].tolist()
                for g_i, val in enumerate(row_vals):
                    inv_val = full ^ val
                    if val not in out or inv_val not in out:
                        perm, neg = perm_neg[g_i]
                        wp = [0] * m
                        tp = t_base
                        for j in range(m):
                            wj = w_base[j]
                            if (neg >> j) & 1:
                                wp[perm[j]] = -wj
                                tp -= wj
                            else:
                                wp[perm[j]] = wj
                        if val not in out:
                            out[val] = (tuple(wp), tp)
                        if inv_val not in out:
                            out[inv_val] = (tuple(-x for x in wp), 1 - tp)
        return out, sorted(out)

    w_grid = np.array(list(itertools.product(range(-W, W + 1), repeat=m)), dtype=np.int64)
    s_mat = w_grid @ X.T
    l1 = np.abs(w_grid).sum(axis=1)
    order = np.argsort(l1, kind="mergesort")
    w_grid = w_grid[order]
    s_mat = s_mat[order]

    out = {}
    t_lo = -W * m - 1
    t_hi = W * m + 1
    for idx_row in range(len(w_grid)):
        w_tup = tuple(int(v) for v in w_grid[idx_row])
        s_row = s_mat[idx_row]
        s_min = int(s_row.min())
        s_max = int(s_row.max())
        for t in range(max(t_lo, s_min), min(t_hi, s_max + 1) + 1):
            bits = int(((s_row >= t) * pow2).sum())
            if bits not in out:
                out[bits] = (w_tup, int(t))
    return out, sorted(out)


def _stabilizer_indices(f: int, T_list, m: int) -> tuple[list[int], int]:
    """Return (unique input-transform indices in G_f, np_stabilizer_size).

    Note: for any fixed input transform `idx`, at most one of `outneg in {0, 1}`
    fixes `f` (since `f != ~f`). Thus every element of G_f has a distinct `idx`,
    and the induced action on hidden units depends only on `idx`.
    """
    full = (1 << (1 << m)) - 1
    nf = full ^ f
    gf_idx: list[int] = []
    np_cnt = 0
    for _, _, idx in T_list:
        g = atlas.apply_T(f, idx, 0, m)
        if g == f:
            gf_idx.append(idx)
            np_cnt += 1
        elif g == nf:
            gf_idx.append(idx)
    return gf_idx, np_cnt


def count_orbits(
    circuits: Iterable[tuple[int, ...]],
    gf_idx: list,
    m: int,
    *,
    unoriented: bool = True,
) -> tuple[int, list[int]]:
    """Compute exact G_f-orbits and sorted orbit sizes on a closed set of circuit tuples."""
    c_set = set(circuits)
    if not c_set:
        return 0, []
    full = (1 << (1 << m)) - 1
    used_nodes = {u for c in c_set for u in c}
    act: dict[int, list[int]] = {}
    if unoriented:
        for h in used_nodes:
            act[h] = [min(g2, full ^ g2) for idx in gf_idx for g2 in (atlas.apply_T(h, idx, 0, m),)]
    else:
        for g in used_nodes:
            act[g] = [atlas.apply_T(g, idx, 0, m) for idx in gf_idx]

    k = len(gf_idx)
    seen: set[tuple[int, ...]] = set()
    sizes: list[int] = []
    for c in sorted(c_set):
        if c in seen:
            continue
        orb = {tuple(sorted(act[u][gi] for u in c)) for gi in range(k)}
        if not orb <= c_set:
            raise AssertionError("Circuit set is not closed under G_f")
        seen.update(orb)
        sizes.append(len(orb))
    sizes.sort()
    return len(sizes), sizes


def _expand_oriented(pair_circuits: Iterable[tuple[int, ...]], full: int) -> list[tuple[int, ...]]:
    """Expand unoriented hyperplane tuples into all 2^w oriented hidden-function tuples."""
    out: list[tuple[int, ...]] = []
    for c in pair_circuits:
        w = len(c)
        for signs in range(1 << w):
            tup = tuple(sorted((full ^ c[j]) if ((signs >> j) & 1) else c[j] for j in range(w)))
            out.append(tup)
    return out


def _subcube_ltf_lookup(w: int) -> np.ndarray:
    """Return all w-input LTFs (`|v| <= 3`) as integer truth-table bitmasks."""
    _, L_list = ltfs_with_bound(w, W=3)
    return np.array(L_list, dtype=np.uint32)


def enumerate_class_bruteforce(
    rep: int,
    cost: int,
    m: int,
    ltf_keys: list[int],
    T_list,
) -> dict:
    """Independent brute-force enumerator for small m (tests every C(|H|, w) and C(|L|, w))."""
    full = (1 << (1 << m)) - 1
    gf_idx, gf_np = _stabilizer_indices(rep, T_list, m)
    if cost == 1:
        return {
            "rep": rep,
            "cost": 1,
            "gf_order": len(gf_idx),
            "gf_np_order": gf_np,
            "num_circuits": 1,
            "num_orbits": 1,
            "orbit_sizes": [1],
            "oriented_num_circuits": 1,
            "oriented_num_orbits": 1,
            "oriented_orbit_sizes": [1],
        }

    w = cost - 1
    H = sorted(b for b in ltf_keys if b <= (full ^ b))
    L_w = _subcube_ltf_lookup(w)
    K = 1 << m

    def admits_psi(tup: tuple[int, ...]) -> bool:
        pm, nm = 0, 0
        for x in range(K):
            code = 0
            for j, u in enumerate(tup):
                if (u >> x) & 1:
                    code |= 1 << j
            if (rep >> x) & 1:
                pm |= 1 << code
            else:
                nm |= 1 << code
        if pm & nm:
            return False
        return bool(np.any(((L_w & pm) == pm) & ((L_w & nm) == 0)))

    unoriented = [comb for comb in itertools.combinations(H, w) if admits_psi(comb)]
    oriented = [comb for comb in itertools.combinations(sorted(ltf_keys), w) if admits_psi(comb)]
    # Verify non-redundant (no pair g, ~g both present in minimal oriented circuit)
    for comb in oriented:
        pairs = {min(u, full ^ u) for u in comb}
        if len(pairs) != w:
            raise AssertionError(f"Degenerate complementary pair found in minimal circuit for rep={rep}")

    n_orb_u, sizes_u = count_orbits(unoriented, gf_idx, m, unoriented=True)
    n_orb_o, sizes_o = count_orbits(oriented, gf_idx, m, unoriented=False)
    return {
        "rep": rep,
        "cost": cost,
        "gf_order": len(gf_idx),
        "gf_np_order": gf_np,
        "num_circuits": len(unoriented),
        "num_orbits": n_orb_u,
        "orbit_sizes": sizes_u,
        "oriented_num_circuits": len(oriented),
        "oriented_num_orbits": n_orb_o,
        "oriented_orbit_sizes": sizes_o,
    }


def _enumerate_cost3_circuits_for_rep(rep: int, L_arr: np.ndarray, full: int) -> list[tuple[int, int]]:
    """Exact width-2 unoriented hyperplane-pair circuits computing rep via any 2-input threshold gate."""
    found: set[tuple[int, int]] = set()
    for target in (rep, full ^ rep):
        sup = L_arr[(L_arr & target) == target]
        sup = sup[sup != target]
        exc = sup ^ target
        n_sup = len(sup)
        for i in range(n_sup):
            si = int(sup[i])
            hi = min(si, full ^ si)
            m = (exc[i + 1:] & exc[i]) == 0
            for j_off in np.nonzero(m)[0]:
                sj = int(sup[i + 1 + j_off])
                hj = min(sj, full ^ sj)
                if hi < hj:
                    found.add((hi, hj))
                elif hj < hi:
                    found.add((hj, hi))
    return sorted(found)


def _enumerate_cost4_circuits_for_rep(rep: int, L_arr: np.ndarray, full: int, K: int) -> list[tuple[int, int, int]]:
    """Exact width-3 unoriented hyperplane-triple circuits using canonical {AND3, AND_OR, MAJ3}."""
    found: set[tuple[int, int, int]] = set()
    # 1) AND3 and AND_OR over (rep, ~rep)
    for target in (rep, full ^ rep):
        ntarget = full ^ target
        supA = L_arr[(L_arr & target) == target]
        excA = supA ^ target
        nA = len(supA)
        for i in range(nA):
            a = int(supA[i])
            ha = min(a, full ^ a)
            ea = int(excA[i])
            # AND3: a & b & c == target
            for j in range(i + 1, nA):
                hb = min(int(supA[j]), full ^ int(supA[j]))
                if hb == ha:
                    continue
                eab = ea & int(excA[j])
                for ko in np.nonzero((excA[j + 1:] & eab) == 0)[0]:
                    hc = min(int(supA[j + 1 + ko]), full ^ int(supA[j + 1 + ko]))
                    if hc != ha and hc != hb:
                        found.add(tuple(sorted((ha, hb, hc))))
            # AND_OR: a & (b | c) == target
            bad = a & ntarget
            cands = L_arr[(L_arr & bad) == 0]
            sub = cands & target
            for j in range(len(cands)):
                hb = min(int(cands[j]), full ^ int(cands[j]))
                if hb == ha:
                    continue
                rem_t = target ^ int(sub[j])
                for ko in np.nonzero((sub[j + 1:] & rem_t) == rem_t)[0]:
                    hc = min(int(cands[j + 1 + ko]), full ^ int(cands[j + 1 + ko]))
                    if hc != ha and hc != hb:
                        found.add(tuple(sorted((ha, hb, hc))))

    # 2) MAJ3(a, b, c) == rep iff pairwise disjoint error masks E = g ^ rep
    E = L_arr ^ rep
    pc = np.array([int(x).bit_count() for x in E], dtype=np.int32)
    max_small = K // 3
    small_idx = np.nonzero(pc <= max_small)[0]
    for i in small_idx:
        ea = int(E[i])
        ha = min(int(L_arr[i]), full ^ int(L_arr[i]))
        b_idx = np.nonzero((E & ea) == 0)[0]
        for bi_pos, j in enumerate(b_idx):
            if pc[j] <= max_small and j <= i:
                continue
            eb = int(E[j])
            hb = min(int(L_arr[j]), full ^ int(L_arr[j]))
            if hb == ha:
                continue
            eab = ea | eb
            for ko in np.nonzero((E[b_idx[bi_pos + 1:]] & eab) == 0)[0]:
                k = int(b_idx[bi_pos + 1 + ko])
                if pc[k] <= max_small and k <= i:
                    continue
                hc = min(int(L_arr[k]), full ^ int(L_arr[k]))
                if hc != ha and hc != hb:
                    found.add(tuple(sorted((ha, hb, hc))))
    return sorted(found)


def _build_l_bitsets(L_arr: np.ndarray, K: int) -> tuple[int, list[int], list[int]]:
    """Precompute per-input-point Python-int membership bitsets over L_arr indices."""
    all_mask = (1 << len(L_arr)) - 1
    one_l: list[int] = []
    zero_l: list[int] = []
    u = L_arr.astype(np.uint64)
    for p in range(K):
        bits = ((u >> np.uint64(p)) & np.uint64(1)).astype(np.uint8)
        m_int = int.from_bytes(np.packbits(bits, bitorder="little").tobytes(), "little")
        one_l.append(m_int)
        zero_l.append(all_mask ^ m_int)
    return all_mask, one_l, zero_l


def _intersect_bitsets(start_mask: int, masks: list[int], pat: int) -> int:
    m_int = start_mask
    while pat:
        lsb = pat & -pat
        m_int &= masks[lsb.bit_length() - 1]
        if not m_int:
            return 0
        pat ^= lsb
    return m_int


def _apply_transforms_batch(vals: np.ndarray, idx_sub: np.ndarray, K: int) -> np.ndarray:
    bmats = ((vals[:, None].astype(np.uint64) >> np.arange(K, dtype=np.uint64)[None, :]) & 1).astype(np.uint8)
    pbytes = np.ascontiguousarray(np.packbits(bmats[:, idx_sub], axis=2, bitorder="little"))
    if K == 32:
        return pbytes.view(np.uint32).reshape(len(vals), len(idx_sub))
    if K == 16:
        return pbytes.view(np.uint16).reshape(len(vals), len(idx_sub)).astype(np.uint32)
    return pbytes[:, :, 0].astype(np.uint32)


def _orbit_rep_positions(
    vals: np.ndarray,
    idx_sub: np.ndarray,
    K: int,
    outneg_cols: np.ndarray | None = None,
    full: int = 0,
) -> list[int]:
    if len(vals) == 0 or len(idx_sub) <= 1:
        return list(range(len(vals)))
    trans = _apply_transforms_batch(vals, idx_sub, K)
    if outneg_cols is not None and np.any(outneg_cols):
        mask = outneg_cols[None, :]
        trans = np.where(mask, np.uint32(full) ^ trans, trans)
    seen: set[int] = set()
    reps: list[int] = []
    v_list = vals.tolist()
    for pos, v in enumerate(v_list):
        if v in seen:
            continue
        reps.append(pos)
        seen.update(trans[pos].tolist())
    return reps


def _enumerate_cost4_circuits_for_rep_fast(
    rep: int,
    L_arr: np.ndarray,
    full: int,
    K: int,
    *,
    l_bitsets: tuple[int, list[int], list[int]] | None = None,
    l_ints: list[int] | None = None,
    h_ints: list[int] | None = None,
    gf_idx: list[int] | None = None,
    idx_m: np.ndarray | None = None,
) -> list[tuple[int, int, int]]:
    """Exact bitset + G_f-symmetry cost-4 enumerator over L_arr (equals _enumerate_cost4_circuits_for_rep)."""
    if l_bitsets is None:
        l_bitsets = _build_l_bitsets(L_arr, K)
    all_mask, one_l, zero_l = l_bitsets
    if l_ints is None:
        l_ints = [int(x) for x in L_arr]
    if h_ints is None:
        h_ints = [min(x, full ^ x) for x in l_ints]

    use_sym = gf_idx is not None and len(gf_idx) > 1
    if use_sym:
        assert gf_idx is not None
        if isinstance(gf_idx[0], (int, np.integer)):
            assert idx_m is not None
            idx_gf = idx_m[gf_idx]
        else:
            idx_gf = np.asarray(gf_idx, dtype=np.int64)
        rep_trans = _apply_transforms_batch(np.array([rep], dtype=np.uint32), idx_gf, K)[0]
        g_is_neg = (rep_trans != np.uint32(rep))
        idx_np = idx_gf[~g_is_neg]
        has_outneg = bool(np.any(g_is_neg))
    else:
        idx_gf = np.empty((0, K), dtype=np.int64)
        idx_np = np.empty((0, K), dtype=np.int64)
        g_is_neg = np.empty(0, dtype=bool)
        has_outneg = False

    seed_found: set[tuple[int, int, int]] = set()
    targets = (rep,) if (use_sym and has_outneg) else (rep, full ^ rep)

    # 1) AND3 and AND_OR over target(s)
    for target in targets:
        ntarget = full ^ target
        sup_mask = _intersect_bitsets(all_mask, one_l, target)
        sup_indices: list[int] = []
        m_tmp = sup_mask
        while m_tmp:
            lsb = m_tmp & -m_tmp
            sup_indices.append(lsb.bit_length() - 1)
            m_tmp ^= lsb
        if not sup_indices:
            continue

        if len(idx_np) > 1:
            sup_arr = L_arr[sup_indices]
            a_pos_list = _orbit_rep_positions(sup_arr, idx_np, K)
            sym_np = True
        else:
            a_pos_list = list(range(len(sup_indices)))
            sym_np = False

        n_sup = len(sup_indices)
        for pos_a in a_pos_list:
            i = sup_indices[pos_a]
            a = l_ints[i]
            ha = h_ints[i]
            ea = a ^ target

            # AND3: a & b & c == target
            b_start = 0 if sym_np else pos_a + 1
            for pos_b in range(b_start, n_sup):
                j = sup_indices[pos_b]
                if j == i:
                    continue
                hb = h_ints[j]
                if hb == ha:
                    continue
                eab = ea & (l_ints[j] ^ target)
                k_mask = _intersect_bitsets(sup_mask, zero_l, eab) & (~((1 << (j + 1)) - 1))
                while k_mask:
                    lsb = k_mask & -k_mask
                    k = lsb.bit_length() - 1
                    k_mask ^= lsb
                    hc = h_ints[k]
                    if hc != ha and hc != hb:
                        t = (ha, hb, hc) if ha < hb < hc else tuple(sorted((ha, hb, hc)))
                        seed_found.add(t)

            # AND_OR: a & (b | c) == target
            bad = a & ntarget
            cands_mask = _intersect_bitsets(all_mask, zero_l, bad)
            if not cands_mask:
                continue
            sup_cands = cands_mask & sup_mask
            jm = cands_mask
            while jm:
                j_lsb = jm & -jm
                j = j_lsb.bit_length() - 1
                jm ^= j_lsb
                hb = h_ints[j]
                if hb == ha:
                    continue
                tail_mask = ~((1 << (j + 1)) - 1)
                rem_t = target & ~l_ints[j]
                if rem_t == 0:
                    k_mask = cands_mask & tail_mask
                elif rem_t == target:
                    k_mask = sup_cands & tail_mask
                else:
                    k_mask = _intersect_bitsets(cands_mask, one_l, rem_t) & tail_mask
                while k_mask:
                    k_lsb = k_mask & -k_mask
                    k = k_lsb.bit_length() - 1
                    k_mask ^= k_lsb
                    hc = h_ints[k]
                    if hc != ha and hc != hb:
                        t = (ha, hb, hc) if ha < hb < hc else tuple(sorted((ha, hb, hc)))
                        seed_found.add(t)

    # 2) MAJ3(a, b, c) == rep
    zero_E = [one_l[p] if ((rep >> p) & 1) else zero_l[p] for p in range(K)]
    E_ints = [v ^ rep for v in l_ints]
    max_small = K // 3
    small_indices = [idx for idx, e in enumerate(E_ints) if e.bit_count() <= max_small]
    small_mask = 0
    for idx in small_indices:
        small_mask |= 1 << idx

    if use_sym and small_indices:
        s_pos_list = _orbit_rep_positions(L_arr[small_indices], idx_gf, K, g_is_neg, full)
        i_list = [small_indices[pos] for pos in s_pos_list]
    else:
        i_list = small_indices

    for i in i_list:
        ha = h_ints[i]
        b_mask = _intersect_bitsets(all_mask, zero_E, E_ints[i])
        if not use_sym:
            b_mask &= ~(small_mask & ((1 << (i + 1)) - 1))
        jm = b_mask
        while jm:
            j_lsb = jm & -jm
            j = j_lsb.bit_length() - 1
            jm ^= j_lsb
            hb = h_ints[j]
            if hb == ha:
                continue
            k_mask = _intersect_bitsets(b_mask, zero_E, E_ints[j]) & (~((1 << (j + 1)) - 1))
            while k_mask:
                k_lsb = k_mask & -k_mask
                k = k_lsb.bit_length() - 1
                k_mask ^= k_lsb
                hc = h_ints[k]
                if hc != ha and hc != hb:
                    t = (ha, hb, hc) if ha < hb < hc else tuple(sorted((ha, hb, hc)))
                    seed_found.add(t)

    if not use_sym or not seed_found:
        return sorted(seed_found)

    # Expand seed_found under full G_f so the output matches exact unpruned set
    nodes = sorted({u for c in seed_found for u in c})
    node_idx = {u: idx for idx, u in enumerate(nodes)}
    trans_u = _apply_transforms_batch(np.array(nodes, dtype=np.uint32), idx_gf, K)
    trans_u = np.minimum(trans_u, np.uint32(full) ^ trans_u)
    t_rows = trans_u.tolist()
    n_gf = len(idx_gf)
    expanded: set[tuple[int, int, int]] = set()
    for h0, h1, h2 in seed_found:
        r0 = t_rows[node_idx[h0]]
        r1 = t_rows[node_idx[h1]]
        r2 = t_rows[node_idx[h2]]
        for gi in range(n_gf):
            x, y, z = r0[gi], r1[gi], r2[gi]
            if x > y:
                x, y = y, x
            if y > z:
                y, z = z, y
            if x > y:
                x, y = y, x
            expanded.add((x, y, z))
    return sorted(expanded)


def _enumerate_cost5_parity4(rep: int, L_arr: np.ndarray, H: list[int], T_list, m: int) -> list[tuple[int, int, int, int]]:
    """Exact width-4 unoriented hyperplane-quadruple enumeration using G_f orbits and conflict-pair cover."""
    full = (1 << (1 << m)) - 1
    gf_idx, _ = _stabilizer_indices(rep, T_list, m)
    even_pts = [x for x in range(1 << m) if ((rep >> x) & 1) == 0]
    odd_pts = [x for x in range(1 << m) if ((rep >> x) & 1) == 1]
    pairs = [(x, y) for x in even_pts for y in odd_pts]
    n_pairs = len(pairs)
    if n_pairs > 64:
        raise ValueError("Conflict pair bitmask supports up to 64 pairs")

    h_to_idx = {h: i for i, h in enumerate(H)}
    seen = [False] * len(H)
    orb_id = [-1] * len(H)
    orb_reps: list[int] = []
    for hi, h in enumerate(H):
        if seen[hi]:
            continue
        oid = len(orb_reps)
        orb_reps.append(hi)
        for idx in gf_idx:
            g2 = atlas.apply_T(h, idx, 0, m)
            hj = h_to_idx[min(g2, full ^ g2)]
            seen[hj] = True
            orb_id[hj] = oid

    h_u64 = np.array(H, dtype=np.uint64)
    cov64 = np.zeros(len(H), dtype=np.uint64)
    H_covers = [0] * n_pairs
    for e, (x, y) in enumerate(pairs):
        diff = ((h_u64 >> x) & 1) ^ ((h_u64 >> y) & 1)
        cov64 |= diff << np.uint64(e)
        mask = 0
        for hi in np.nonzero(diff)[0]:
            mask |= 1 << int(hi)
        H_covers[e] = mask

    max_cov = max(int(v).bit_count() for v in cov64)
    pop8 = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
    all_mask = np.uint64((1 << n_pairs) - 1 if n_pairs < 64 else 0xFFFFFFFFFFFFFFFF)
    orb_id_arr = np.array(orb_id, dtype=np.int32)
    h_indices = np.arange(len(H), dtype=np.int32)
    L_u16 = L_arr.astype(np.uint32)

    seed_quads: list[tuple[int, int, int, int]] = []
    for o1, i1 in enumerate(orb_reps):
        c1 = cov64[i1]
        valid_mask = (orb_id_arr > o1) | ((orb_id_arr == o1) & (h_indices > i1))
        valid_js = np.nonzero(valid_mask)[0]
        for pos2, i2_np in enumerate(valid_js):
            i2 = int(i2_np)
            c12 = c1 | cov64[i2]
            js3 = valid_js[pos2 + 1:]
            if len(js3) == 0:
                continue
            rem123 = all_mask ^ (c12 | cov64[js3])
            cnts = pop8[rem123.view(np.uint8).reshape(-1, 8)].sum(axis=1)
            for pos3 in np.nonzero(cnts <= max_cov)[0]:
                i3 = int(js3[pos3])
                rem = int(rem123[pos3])
                if rem == 0:
                    continue
                cands = ((1 << len(H)) - (1 << (i3 + 1)))
                tmp = rem
                while tmp and cands:
                    lsb = tmp & -tmp
                    cands &= H_covers[lsb.bit_length() - 1]
                    tmp ^= lsb
                while cands:
                    lsb = cands & -cands
                    i4 = lsb.bit_length() - 1
                    cands ^= lsb
                    if not valid_mask[i4]:
                        continue
                    h1, h2, h3, h4 = H[i1], H[i2], H[i3], H[i4]
                    pm, nm = 0, 0
                    for x in range(1 << m):
                        code = (
                            ((h1 >> x) & 1)
                            | (((h2 >> x) & 1) << 1)
                            | (((h3 >> x) & 1) << 2)
                            | (((h4 >> x) & 1) << 3)
                        )
                        if (rep >> x) & 1:
                            pm |= 1 << code
                        else:
                            nm |= 1 << code
                    if np.any(((L_u16 & pm) == pm) & ((L_u16 & nm) == 0)):
                        seed_quads.append((h1, h2, h3, h4))

    all_circuits: set[tuple[int, int, int, int]] = set()
    for q in seed_quads:
        if q in all_circuits:
            continue
        for idx in gf_idx:
            q2 = tuple(sorted(min(g2, full ^ g2) for h in q for g2 in (atlas.apply_T(h, idx, 0, m),)))
            all_circuits.add(q2)
    return sorted(all_circuits)


def enumerate_dimension(m: int, tb: atlas.Table | None = None) -> list[dict]:
    """Enumerate all NPN classes, exact min-circuit counts, and G_f-orbits for m <= 4."""
    if m < 1 or m > 4:
        raise ValueError(f"Exact full-table atlas orbit enumeration supports 1 <= m <= 4, got {m}")
    if tb is None:
        tb = atlas.build_all(m)[m]

    full = (1 << (1 << m)) - 1
    K = 1 << m
    L_keys = sorted(tb.ltf.keys())
    L_arr = np.array(L_keys, dtype=np.uint32)
    H = sorted(b for b in L_keys if b <= (full ^ b))
    L_sub4 = _subcube_ltf_lookup(4) if m == 4 else np.array([], dtype=np.uint32)

    rows: list[dict] = []
    for rep in tb.classes():
        cost = int(tb.hi[rep])
        if not tb.exact(rep) or int(tb.d2[rep]) != cost:
            raise AssertionError(f"Expected depth <= 2 exact cost at m={m}, rep={rep}")
        gf_idx, gf_np = _stabilizer_indices(rep, tb.T, m)
        if cost == 1:
            rows.append({
                "rep": rep,
                "rep_hex": hex(rep),
                "cost": 1,
                "gf_order": len(gf_idx),
                "gf_np_order": gf_np,
                "num_circuits": 1,
                "num_orbits": 1,
                "orbit_sizes": [1],
                "oriented_num_circuits": 1,
                "oriented_num_orbits": 1,
                "oriented_orbit_sizes": [1],
            })
            continue

        if cost == 3:
            unoriented = _enumerate_cost3_circuits_for_rep(rep, L_arr, full)
        elif cost == 4:
            unoriented = _enumerate_cost4_circuits_for_rep(rep, L_arr, full, K)
        elif cost == 5 and m == 4:
            unoriented = _enumerate_cost5_parity4(rep, L_sub4, H, tb.T, m)
        else:
            raise NotImplementedError(f"Unsupported cost={cost} at m={m}")

        oriented = sorted(_expand_oriented(unoriented, full))
        n_orb_u, sizes_u = count_orbits(unoriented, gf_idx, m, unoriented=True)
        n_orb_o, sizes_o = count_orbits(oriented, gf_idx, m, unoriented=False)
        rows.append({
            "rep": rep,
            "rep_hex": hex(rep),
            "cost": cost,
            "gf_order": len(gf_idx),
            "gf_np_order": gf_np,
            "num_circuits": len(unoriented),
            "num_orbits": n_orb_u,
            "orbit_sizes": sizes_u,
            "oriented_num_circuits": len(oriented),
            "oriented_num_orbits": n_orb_o,
            "oriented_orbit_sizes": sizes_o,
        })
    return rows


def enumerate_n5_cost_le3(W: int = 3, time_limit: float = 3600.0) -> dict:
    """Extend to n = 5 for cost <= 3 with weights |w| <= W using fast orbit sieving."""
    t0 = time.perf_counter()
    m = 5
    full = 0xFFFFFFFF
    L5_dict, L5_keys = ltfs_with_bound(m, W=W)
    L5_arr = np.array(L5_keys, dtype=np.uint32)
    L5_set = set(L5_keys)

    T5 = atlas.transforms(m)
    idx5 = np.array([idx for _, _, idx in T5], dtype=np.int64)
    full_u32 = np.uint32(full)
    bit_pos = np.arange(32, dtype=np.uint32)

    def orbit_of(f: int) -> tuple[int, list[int], list[int]]:
        bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        inv = full_u32 ^ packed
        rep = int(min(packed.min(), inv.min()))
        return rep, packed.tolist(), inv.tolist()

    # 1. Cost-1 NPN classes (among |w| <= W LTFs)
    seen1: set[int] = set()
    cost1_reps: list[int] = []
    for f in L5_keys:
        if f in seen1:
            continue
        rep, fwd, inv = orbit_of(f)
        cost1_reps.append(rep)
        seen1.update(fwd)
        seen1.update(inv)

    # 2. Discover all cost-3 NPN classes via oriented cost1_rep & L5
    oriented_reps: list[int] = []
    for r in cost1_reps:
        if r not in (0, full):
            oriented_reps.append(r)
            nr = full ^ r
            if nr != r:
                oriented_reps.append(nr)

    raw_cands: set[int] = set()
    for r in oriented_reps:
        vals = L5_arr & np.uint32(r)
        for x in vals.tolist():
            if x not in L5_set:
                raw_cands.add(x)

    seen3: set[int] = set()
    cost3_reps: list[int] = []
    for f in sorted(raw_cands):
        if f in seen3:
            continue
        rep, fwd, inv = orbit_of(f)
        cost3_reps.append(rep)
        for v in fwd:
            if v in raw_cands:
                seen3.add(v)
        for v in inv:
            if v in raw_cands:
                seen3.add(v)
    cost3_reps.sort()
    disc_sec = round(time.perf_counter() - t0, 3)

    # Fast stabilizer + circuit enumeration for each class
    # Fast vectorized transform for small sets of truth tables:
    def apply_gf_pairs(pairs_list: list[tuple[int, int]], gf_i: list[int], *, unoriented: bool) -> tuple[int, list[int]]:
        if not pairs_list:
            return 0, []
        nodes = sorted({u for c in pairs_list for u in c})
        node_u32 = np.array(nodes, dtype=np.uint32)
        node_idx = {u: k for k, u in enumerate(nodes)}
        idx_gf = idx5[gf_i]
        act_rows: list[list[int]] = []
        for s in range(0, len(node_u32), 256):
            chunk = node_u32[s:s + 256]
            bmats = ((chunk[:, None] >> bit_pos[None, :]) & np.uint32(1)).astype(np.uint8)
            p_bytes = np.ascontiguousarray(np.packbits(bmats[:, idx_gf], axis=2, bitorder="little"))
            trans = p_bytes.view(np.uint32).reshape(len(chunk), len(gf_i))
            if unoriented:
                trans = np.minimum(trans, full_u32 ^ trans)
            act_rows.extend(trans.tolist())
        c_set = set(pairs_list)
        seen_c: set[tuple[int, int]] = set()
        sizes: list[int] = []
        k = len(gf_i)
        for c in pairs_list:
            if c in seen_c:
                continue
            r0 = act_rows[node_idx[c[0]]]
            r1 = act_rows[node_idx[c[1]]]
            orb = {(r0[gi], r1[gi]) if r0[gi] <= r1[gi] else (r1[gi], r0[gi]) for gi in range(k)}
            if not orb <= c_set:
                raise AssertionError("n=5 circuit set not closed under G_f")
            seen_c.update(orb)
            sizes.append(len(orb))
        sizes.sort()
        return len(sizes), sizes

    def gf_for_rep(f: int) -> tuple[list[int], int]:
        bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        nf = np.uint32(full ^ f)
        eq = np.nonzero(packed == np.uint32(f))[0]
        neq = np.nonzero(packed == nf)[0]
        gf_i = sorted(set(eq.tolist()) | set(neq.tolist()))
        return gf_i, int(len(eq))

    rows: list[dict] = []
    for rep in cost1_reps:
        gf_i, gf_np = gf_for_rep(rep)
        rows.append({
            "rep": rep,
            "rep_hex": hex(rep),
            "cost": 1,
            "gf_order": len(gf_i),
            "gf_np_order": gf_np,
            "num_circuits": 1,
            "num_orbits": 1,
            "orbit_sizes": [1],
            "oriented_num_circuits": 1,
            "oriented_num_orbits": 1,
            "oriented_orbit_sizes": [1],
        })

    completed_cost3 = 0
    stopped_reason = "completed"
    for rep in cost3_reps:
        if time.perf_counter() - t0 > time_limit:
            stopped_reason = f"time_limit_{time_limit}s_at_cost3_idx_{completed_cost3}_of_{len(cost3_reps)}"
            break
        gf_i, gf_np = gf_for_rep(rep)
        unoriented = _enumerate_cost3_circuits_for_rep(rep, L5_arr, full)
        n_orb_u, sizes_u = apply_gf_pairs(unoriented, gf_i, unoriented=True)
        oriented = sorted(_expand_oriented(unoriented, full))
        n_orb_o, sizes_o = apply_gf_pairs(oriented, gf_i, unoriented=False)
        rows.append({
            "rep": rep,
            "rep_hex": hex(rep),
            "cost": 3,
            "gf_order": len(gf_i),
            "gf_np_order": gf_np,
            "num_circuits": len(unoriented),
            "num_orbits": n_orb_u,
            "orbit_sizes": sizes_u,
            "oriented_num_circuits": len(oriented),
            "oriented_num_orbits": n_orb_o,
            "oriented_orbit_sizes": sizes_o,
        })
        completed_cost3 += 1
        if completed_cost3 == 50 or completed_cost3 % 500 == 0:
            print(f"[n=5 cost=3] {completed_cost3}/{len(cost3_reps)} elapsed={time.perf_counter()-t0:.1f}s", flush=True)

    return {
        "n": 5,
        "W": W,
        "ltf_count": len(L5_keys),
        "hyperplane_pairs": len(L5_keys) // 2,
        "cost1_classes": len(cost1_reps),
        "cost3_classes_total": len(cost3_reps),
        "cost3_classes_completed": completed_cost3,
        "stopped_reason": stopped_reason,
        "discovery_seconds": disc_sec,
        "total_seconds": round(time.perf_counter() - t0, 3),
        "classes": rows,
    }


# ------------------------------------------------------------ G15: n = 5 parallel & cost = 4

_W5_STATE: dict = {}


def _init_n5_worker(L5_arr: np.ndarray, idx5: np.ndarray, full: int, build_bitsets: bool = False) -> None:
    l_ints = [int(x) for x in L5_arr]
    h_ints = [min(x, full ^ x) for x in l_ints]
    _W5_STATE.clear()
    _W5_STATE["L5_arr"] = L5_arr
    _W5_STATE["l_ints"] = l_ints
    _W5_STATE["h_ints"] = h_ints
    _W5_STATE["idx5"] = idx5
    _W5_STATE["full"] = full
    _W5_STATE["bit_pos"] = np.arange(32, dtype=np.uint32)
    if build_bitsets:
        _W5_STATE["l_bitsets"] = _build_l_bitsets(L5_arr, 32)


def _n5_gf_and_orbits(
    f: int,
    circuits: list[tuple[int, ...]],
    idx5: np.ndarray,
    full: int,
    bit_pos: np.ndarray,
    *,
    unoriented: bool,
) -> tuple[list[int], int, int, list[int]]:
    bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
    packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
    nf = np.uint32(full ^ f)
    eq = np.nonzero(packed == np.uint32(f))[0]
    neq = np.nonzero(packed == nf)[0]
    gf_i = sorted(set(eq.tolist()) | set(neq.tolist()))
    gf_np = int(len(eq))
    if not circuits:
        return gf_i, gf_np, 0, []
    if len(gf_i) == 1:
        n_c = len(circuits)
        return gf_i, gf_np, n_c, [1] * n_c

    nodes = sorted({u for c in circuits for u in c})
    node_u32 = np.array(nodes, dtype=np.uint32)
    node_idx = {u: k for k, u in enumerate(nodes)}
    idx_gf = idx5[gf_i]
    act_rows: list[list[int]] = []
    full_u32 = np.uint32(full)
    for s in range(0, len(node_u32), 256):
        chunk = node_u32[s:s + 256]
        bm = ((chunk[:, None] >> bit_pos[None, :]) & np.uint32(1)).astype(np.uint8)
        pb = np.ascontiguousarray(np.packbits(bm[:, idx_gf], axis=2, bitorder="little"))
        tr = pb.view(np.uint32).reshape(len(chunk), len(gf_i))
        if unoriented:
            tr = np.minimum(tr, full_u32 ^ tr)
        act_rows.extend(tr.tolist())

    c_set = set(circuits)
    seen_c: set[tuple[int, ...]] = set()
    sizes: list[int] = []
    k_gf = len(gf_i)
    w = len(circuits[0])
    for c in circuits:
        if c in seen_c:
            continue
        rows_c = [act_rows[node_idx[u]] for u in c]
        if w == 2:
            r0, r1 = rows_c
            orb = {(r0[gi], r1[gi]) if r0[gi] <= r1[gi] else (r1[gi], r0[gi]) for gi in range(k_gf)}
        else:
            r0, r1, r2 = rows_c
            orb = {tuple(sorted((r0[gi], r1[gi], r2[gi]))) for gi in range(k_gf)}
        if not orb <= c_set:
            raise AssertionError("n=5 circuit set not closed under G_f")
        seen_c.update(orb)
        sizes.append(len(orb))
    sizes.sort()
    return gf_i, gf_np, len(sizes), sizes


def _n5_cost3_worker(rep: int) -> dict:
    L5_arr = _W5_STATE["L5_arr"]
    idx5 = _W5_STATE["idx5"]
    full = _W5_STATE["full"]
    bit_pos = _W5_STATE["bit_pos"]
    unoriented = _enumerate_cost3_circuits_for_rep(rep, L5_arr, full)
    gf_i, gf_np, n_orb_u, sizes_u = _n5_gf_and_orbits(rep, unoriented, idx5, full, bit_pos, unoriented=True)
    oriented = sorted(_expand_oriented(unoriented, full))
    if len(gf_i) == 1:
        n_orb_o, sizes_o = len(oriented), [1] * len(oriented)
    else:
        _, _, n_orb_o, sizes_o = _n5_gf_and_orbits(rep, oriented, idx5, full, bit_pos, unoriented=False)
    return {
        "rep": rep,
        "rep_hex": hex(rep),
        "cost": 3,
        "gf_order": len(gf_i),
        "gf_np_order": gf_np,
        "num_circuits": len(unoriented),
        "num_orbits": n_orb_u,
        "orbit_sizes": sizes_u,
        "oriented_num_circuits": len(oriented),
        "oriented_num_orbits": n_orb_o,
        "oriented_orbit_sizes": sizes_o,
    }


def _n5_cost4_worker(item: tuple[int, bool]) -> dict:
    rep, is_sym = item
    L5_arr = _W5_STATE["L5_arr"]
    l_ints = _W5_STATE["l_ints"]
    h_ints = _W5_STATE["h_ints"]
    l_bitsets = _W5_STATE["l_bitsets"]
    idx5 = _W5_STATE["idx5"]
    full = _W5_STATE["full"]
    bit_pos = _W5_STATE["bit_pos"]

    bmat = ((np.uint32(rep) >> bit_pos) & np.uint32(1)).astype(np.uint8)
    packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
    nf = np.uint32(full ^ rep)
    eq = np.nonzero(packed == np.uint32(rep))[0]
    neq = np.nonzero(packed == nf)[0]
    gf_i = sorted(set(eq.tolist()) | set(neq.tolist()))
    gf_np = int(len(eq))

    c3_check = len(_enumerate_cost3_circuits_for_rep(rep, L5_arr, full))
    unoriented = _enumerate_cost4_circuits_for_rep_fast(
        rep, L5_arr, full, 32,
        l_bitsets=l_bitsets, l_ints=l_ints, h_ints=h_ints, gf_idx=gf_i, idx_m=idx5,
    )
    if len(gf_i) == 1:
        n_orb_u, sizes_u = len(unoriented), [1] * len(unoriented)
    else:
        _, _, n_orb_u, sizes_u = _n5_gf_and_orbits(rep, unoriented, idx5, full, bit_pos, unoriented=True)
    oriented = sorted(_expand_oriented(unoriented, full))
    if len(gf_i) == 1:
        n_orb_o, sizes_o = len(oriented), [1] * len(oriented)
    else:
        _, _, n_orb_o, sizes_o = _n5_gf_and_orbits(rep, oriented, idx5, full, bit_pos, unoriented=False)
    return {
        "rep": rep,
        "rep_hex": hex(rep),
        "cost": 4,
        "is_symmetric": is_sym,
        "cost3_circuits_at_W": c3_check,
        "gf_order": len(gf_i),
        "gf_np_order": gf_np,
        "num_circuits": len(unoriented),
        "num_orbits": n_orb_u,
        "orbit_sizes": sizes_u,
        "oriented_num_circuits": len(oriented),
        "oriented_num_orbits": n_orb_o,
        "oriented_orbit_sizes": sizes_o,
    }


def _discover_n5_cost_le3_data(W: int) -> tuple[dict, list[int], np.ndarray, np.ndarray, list[int], list[int]]:
    m = 5
    full = 0xFFFFFFFF
    L5_dict, L5_keys = ltfs_with_bound(m, W=W)
    L5_arr = np.array(L5_keys, dtype=np.uint32)
    L5_set = set(L5_keys)
    T5 = atlas.transforms(m)
    idx5 = np.array([idx for _, _, idx in T5], dtype=np.int64)
    full_u32 = np.uint32(full)
    bit_pos = np.arange(32, dtype=np.uint32)

    def orbit_of(f: int) -> tuple[int, list[int], list[int]]:
        bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        inv = full_u32 ^ packed
        rep = int(min(packed.min(), inv.min()))
        return rep, packed.tolist(), inv.tolist()

    seen1: set[int] = set()
    cost1_reps: list[int] = []
    for f in L5_keys:
        if f in seen1:
            continue
        rep, fwd, inv = orbit_of(f)
        cost1_reps.append(rep)
        seen1.update(fwd)
        seen1.update(inv)

    oriented_reps: list[int] = []
    for r in cost1_reps:
        if r not in (0, full):
            oriented_reps.append(r)
            nr = full ^ r
            if nr != r:
                oriented_reps.append(nr)

    raw_cands: set[int] = set()
    for r in oriented_reps:
        vals = L5_arr & np.uint32(r)
        for x in vals.tolist():
            if x not in L5_set:
                raw_cands.add(x)

    seen3: set[int] = set()
    cost3_reps: list[int] = []
    for f in sorted(raw_cands):
        if f in seen3:
            continue
        rep, fwd, inv = orbit_of(f)
        cost3_reps.append(rep)
        for v in fwd:
            if v in raw_cands:
                seen3.add(v)
        for v in inv:
            if v in raw_cands:
                seen3.add(v)
    cost3_reps.sort()
    return L5_dict, L5_keys, L5_arr, idx5, cost1_reps, cost3_reps


def enumerate_n5_cost_le3_parallel(W: int = 4, workers: int = 3, time_limit: float = 3600.0) -> dict:
    """Complete parallel n = 5, cost <= 3 enumeration with |w| <= W."""
    t0 = time.perf_counter()
    full = 0xFFFFFFFF
    bit_pos = np.arange(32, dtype=np.uint32)
    _, L5_keys, L5_arr, idx5, cost1_reps, cost3_reps = _discover_n5_cost_le3_data(W)
    disc_sec = round(time.perf_counter() - t0, 3)

    rows: list[dict] = []
    for rep in cost1_reps:
        bmat = ((np.uint32(rep) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        nf = np.uint32(full ^ rep)
        eq = np.nonzero(packed == np.uint32(rep))[0]
        neq = np.nonzero(packed == nf)[0]
        gf_i = sorted(set(eq.tolist()) | set(neq.tolist()))
        rows.append({
            "rep": rep,
            "rep_hex": hex(rep),
            "cost": 1,
            "gf_order": len(gf_i),
            "gf_np_order": int(len(eq)),
            "num_circuits": 1,
            "num_orbits": 1,
            "orbit_sizes": [1],
            "oriented_num_circuits": 1,
            "oriented_num_orbits": 1,
            "oriented_orbit_sizes": [1],
        })

    completed_cost3 = 0
    stopped_reason = "completed"
    stopped_at_rep: str | None = None
    chunk_sz = max(32, workers * 16)
    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_n5_worker,
        initargs=(L5_arr, idx5, full, False),
    ) as pool:
        for start in range(0, len(cost3_reps), chunk_sz):
            if time.perf_counter() - t0 > time_limit:
                stopped_reason = f"time_limit_{time_limit}s_at_cost3_idx_{completed_cost3}_of_{len(cost3_reps)}"
                stopped_at_rep = hex(cost3_reps[start])
                break
            chunk = cost3_reps[start:start + chunk_sz]
            for row in pool.map(_n5_cost3_worker, chunk, chunksize=8):
                rows.append(row)
                completed_cost3 += 1
            if completed_cost3 <= chunk_sz or completed_cost3 % 512 < chunk_sz or completed_cost3 == len(cost3_reps):
                print(f"[n=5 W={W} cost=3] {completed_cost3}/{len(cost3_reps)} elapsed={time.perf_counter()-t0:.1f}s", flush=True)

    return {
        "n": 5,
        "W": W,
        "workers": workers,
        "ltf_count": len(L5_keys),
        "hyperplane_pairs": len(L5_keys) // 2,
        "cost1_reps": cost1_reps,
        "cost3_reps": cost3_reps,
        "cost1_classes": len(cost1_reps),
        "cost3_classes_total": len(cost3_reps),
        "cost3_classes_completed": completed_cost3,
        "stopped_at_rep": stopped_at_rep,
        "stopped_reason": stopped_reason,
        "discovery_seconds": disc_sec,
        "total_seconds": round(time.perf_counter() - t0, 3),
        "classes": rows,
    }


def _symmetric_n5_reps() -> list[int]:
    """Canonical NPN representatives for all 64 symmetric 5-variable Boolean functions."""
    T5 = atlas.transforms(5)
    idx5 = np.array([idx for _, _, idx in T5], dtype=np.int64)
    bit_pos = np.arange(32, dtype=np.uint32)
    full = 0xFFFFFFFF
    hw = [x.bit_count() for x in range(32)]
    seen: set[int] = set()
    reps: list[int] = []
    for mask in range(64):
        f = 0
        for x in range(32):
            if (mask >> hw[x]) & 1:
                f |= 1 << x
        bmat = ((np.uint32(f) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        rep = int(min(packed.min(), (np.uint32(full) ^ packed).min()))
        if rep not in seen:
            seen.add(rep)
            reps.append(rep)
    return sorted(reps)


def enumerate_n5_cost4(
    W: int = 3,
    *,
    cost_le3_W3_set: set[int] | None = None,
    cost_le3_W4_set: set[int] | None = None,
    workers: int = 3,
    time_limit: float = 1500.0,
    max_general_discover: int = 2500,
) -> dict:
    """Enumerate n=5 cost=4 (W=3) classes across exhaustive symmetric slice + deterministic general stream."""
    t0 = time.perf_counter()
    full = 0xFFFFFFFF
    bit_pos = np.arange(32, dtype=np.uint32)

    _, L5_keys, L5_arr, idx5, cost1_W3, cost3_W3 = _discover_n5_cost_le3_data(W)
    if cost_le3_W3_set is None:
        cost_le3_W3_set = set(cost1_W3) | set(cost3_W3)

    T5 = atlas.transforms(5)
    # 1) Exhaustive symmetric slice (all 64 symmetric Boolean functions -> NPN classes)
    sym_all_reps = _symmetric_n5_reps()
    sym_non_le3 = [r for r in sym_all_reps if r not in cost_le3_W3_set]

    sym_cost4_rows: list[dict] = []
    sym_cost_ge5_reps: list[int] = []
    _init_n5_worker(L5_arr, idx5, full, True)
    for rep in sym_non_le3:
        row = _n5_cost4_worker((rep, True))
        if row["cost3_circuits_at_W"] != 0:
            raise AssertionError(f"Symmetric rep {hex(rep)} had cost3 circuits")
        if row["num_circuits"] == 0:
            sym_cost_ge5_reps.append(rep)
            continue
        if cost_le3_W4_set is not None:
            row["drops_to_cost3_at_W4"] = rep in cost_le3_W4_set
        sym_cost4_rows.append(row)

    # 2) Deterministic balanced general catalog via AND3/AND_OR/MAJ3 from cost1_W3 & strided L5
    def canon_batch(vals: list[int]) -> list[int]:
        if not vals:
            return []
        arr = np.array(vals, dtype=np.uint32)
        out: list[int] = []
        full_u32 = np.uint32(full)
        for s in range(0, len(arr), 256):
            chunk = arr[s:s + 256]
            bm = ((chunk[:, None] >> bit_pos[None, :]) & np.uint32(1)).astype(np.uint8)
            pk = np.packbits(bm[:, idx5], axis=2, bitorder="little").view(np.uint32).reshape(len(chunk), len(idx5))
            mins = np.minimum(pk.min(axis=1), (full_u32 ^ pk).min(axis=1))
            out.extend(mins.tolist())
        return out

    general_reps_set: set[int] = set()
    sym_cost4_set = {r["rep"] for r in sym_cost4_rows}
    oriented_c1: list[int] = []
    for r in cost1_W3:
        if r not in (0, full):
            oriented_c1.append(r)
            nr = full ^ r
            if nr != r:
                oriented_c1.append(nr)

    # Round-robin / capped sampling across ALL oriented cost1 templates and {AND3, AND_OR, MAJ3}
    step_a = max(1, len(L5_keys) // 31)
    step_b = max(1, len(L5_keys) // 29)
    sample_b = L5_arr[::step_b].astype(np.uint32)
    per_r_cap = max(1, (max_general_discover + len(oriented_c1) - 1) // len(oriented_c1))
    spill_cands: list[int] = []
    for r in oriented_c1:
        if len(general_reps_set) >= max_general_discover:
            break
        ru = np.uint32(r)
        raw_r: list[int] = []
        for u in L5_keys[::step_a]:
            uu = np.uint32(u)
            for batch in (
                (ru & uu & sample_b),
                (ru & (uu | sample_b)),
                ((ru & uu) | (ru & sample_b) | (uu & sample_b)),
            ):
                raw_r.extend(batch.tolist())
        added_r = 0
        for rep in canon_batch(list(dict.fromkeys(raw_r))):
            if rep in cost_le3_W3_set or rep in sym_cost4_set or rep in general_reps_set:
                continue
            if added_r < per_r_cap and len(general_reps_set) < max_general_discover:
                general_reps_set.add(rep)
                added_r += 1
            else:
                spill_cands.append(rep)

    for rep in spill_cands:
        if len(general_reps_set) >= max_general_discover:
            break
        if rep not in cost_le3_W3_set and rep not in sym_cost4_set:
            general_reps_set.add(rep)

    # Process balanced Hamming weights first (w=16..12) to avoid stalling on degenerate tiny-weight reps
    general_reps = sorted(
        general_reps_set,
        key=lambda r: (-min(r.bit_count(), 32 - r.bit_count()), r),
    )
    disc_sec = round(time.perf_counter() - t0, 3)

    general_rows: list[dict] = []
    completed_general = 0
    stopped_reason = "completed"
    stopped_at_rep: str | None = None
    chunk_sz = max(2, workers)

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_n5_worker,
        initargs=(L5_arr, idx5, full, True),
    ) as pool:
        for start in range(0, len(general_reps), chunk_sz):
            if time.perf_counter() - t0 > time_limit:
                stopped_reason = f"time_limit_{time_limit}s_at_general_idx_{completed_general}_of_{len(general_reps)}"
                stopped_at_rep = hex(general_reps[start])
                break
            chunk = [(rep, False) for rep in general_reps[start:start + chunk_sz]]
            for row in pool.map(_n5_cost4_worker, chunk, chunksize=1):
                if row["cost3_circuits_at_W"] != 0:
                    raise AssertionError(f"General rep {row['rep_hex']} had cost3 circuits")
                if row["num_circuits"] == 0:
                    raise AssertionError(f"General rep {row['rep_hex']} had 0 cost4 circuits")
                if cost_le3_W4_set is not None:
                    row["drops_to_cost3_at_W4"] = row["rep"] in cost_le3_W4_set
                general_rows.append(row)
                completed_general += 1
            print(
                f"[n=5 W={W} cost=4 general] {completed_general}/{len(general_reps)} "
                f"last={general_rows[-1]['rep_hex']}(w={general_rows[-1]['rep'].bit_count()},c4={general_rows[-1]['num_circuits']}) "
                f"elapsed={time.perf_counter()-t0:.1f}s",
                flush=True,
            )

    return {
        "n": 5,
        "W": W,
        "workers": workers,
        "symmetric_total_classes": len(sym_all_reps),
        "symmetric_cost4_classes": len(sym_cost4_rows),
        "symmetric_cost_ge5_reps": [hex(r) for r in sym_cost_ge5_reps],
        "symmetric_classes": sym_cost4_rows,
        "general_classes_discovered": len(general_reps),
        "general_classes_completed": completed_general,
        "stopped_at_rep": stopped_at_rep,
        "stopped_reason": stopped_reason,
        "discovery_seconds": disc_sec,
        "total_seconds": round(time.perf_counter() - t0, 3),
        "general_classes": general_rows,
    }
