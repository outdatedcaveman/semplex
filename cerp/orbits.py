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
    w_grid = np.array(list(itertools.product(range(-W, W + 1), repeat=m)), dtype=np.int64)
    s_mat = w_grid @ X.T
    l1 = np.abs(w_grid).sum(axis=1)
    order = np.argsort(l1, kind="mergesort")
    w_grid = w_grid[order]
    s_mat = s_mat[order]

    out: dict[int, tuple[tuple[int, ...], int]] = {}
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
