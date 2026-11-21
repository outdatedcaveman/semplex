"""Tests for G15 n = 5 orbit census extensions (fast LTF generation, cost = 4 bitset+sym, brute-force checks)."""

from __future__ import annotations

import numpy as np
import pytest

from cerp import atlas, orbits


@pytest.fixture(scope="module")
def tb4():
    return atlas.build_all(4)[4]


def _canon5_batch(vals: list[int], idx5: np.ndarray) -> np.ndarray:
    arr = np.array(sorted(set(vals)), dtype=np.uint32)
    bit_pos = np.arange(32, dtype=np.uint32)
    full_u32 = np.uint32(0xFFFFFFFF)
    out = np.empty(len(arr), dtype=np.uint32)
    for s in range(0, len(arr), 256):
        chunk = arr[s:s + 256]
        bm = ((chunk[:, None] >> bit_pos[None, :]) & np.uint32(1)).astype(np.uint8)
        pk = np.packbits(bm[:, idx5], axis=2, bitorder="little").view(np.uint32).reshape(len(chunk), len(idx5))
        out[s:s + 256] = np.minimum(pk.min(axis=1), (full_u32 ^ pk).min(axis=1))
    return np.unique(out)


def _closed_l1_le2_n5() -> tuple[list[int], np.ndarray, np.ndarray, list]:
    L1, _ = orbits.ltfs_with_bound(5, W=1)
    # Signed permutations preserve sum(|w_j|), so |w|_1 <= 2 is 100% NPN-closed on n = 5
    keys = sorted(k for k, (w, _) in L1.items() if sum(abs(x) for x in w) <= 2)
    assert len(keys) == 92
    T5 = atlas.transforms(5)
    idx5 = np.array([idx for _, _, idx in T5], dtype=np.int64)
    return keys, np.array(keys, dtype=np.uint32), idx5, T5


def _check_ltf_weights_match_tt(ltf_dict: dict[int, tuple[tuple[int, ...], int]], m: int, W: int, keys: list[int]) -> None:
    X = np.array([[(i >> j) & 1 for j in range(m)] for i in range(1 << m)], dtype=np.int64)
    pow2 = np.array([1 << i for i in range(1 << m)], dtype=np.int64)
    for b in keys:
        w, t = ltf_dict[b]
        assert len(w) == m
        assert max(abs(x) for x in w) <= W
        got = int((((X @ np.array(w, dtype=np.int64)) >= t) * pow2).sum())
        assert got == b, f"Mismatch for {hex(b)}: w={w}, t={t}, got={hex(got)}"


def test_n5_ltfs_with_bound_counts_and_weights() -> None:
    L3, keys3 = orbits.ltfs_with_bound(5, W=3)
    assert len(keys3) == 32812
    L4, keys4 = orbits.ltfs_with_bound(5, W=4)
    assert len(keys4) == 62572
    assert set(keys3) <= set(keys4)

    _check_ltf_weights_match_tt(L3, 5, 3, keys3[::163])
    _check_ltf_weights_match_tt(L4, 5, 4, keys4[::311])


def test_n4_dimension_unchanged(tb4) -> None:
    rows = orbits.enumerate_dimension(4, tb=tb4)
    assert len(rows) == 222
    assert sum(1 for r in rows if r["num_orbits"] == 1) == 65
    assert sum(1 for r in rows if r["oriented_num_orbits"] == 1) == 15


def test_cost4_fast_matches_reference_on_all_78_n4_classes(tb4) -> None:
    L4_keys = sorted(tb4.ltf)
    L4_arr = np.array(L4_keys, dtype=np.int64)
    T4 = atlas.transforms(4)
    idx4 = np.array([idx for _, _, idx in T4], dtype=np.int64)
    full = (1 << 16) - 1
    l_bitsets = orbits._build_l_bitsets(L4_arr.astype(np.uint32), 16)
    l_ints = [int(x) for x in L4_arr]
    h_ints = [min(x, full ^ x) for x in l_ints]

    cost4_reps = sorted({int(c) for f, c in enumerate(tb4.canon) if tb4.hi[f] == 4})
    assert len(cost4_reps) == 78

    for rep in cost4_reps:
        ref = orbits._enumerate_cost4_circuits_for_rep(rep, L4_arr, full, 16)
        fast_nosym = orbits._enumerate_cost4_circuits_for_rep_fast(
            rep, L4_arr, full, 16, l_bitsets=l_bitsets, l_ints=l_ints, h_ints=h_ints
        )
        gf_idx, _ = orbits._stabilizer_indices(rep, T4, 4)
        fast_sym = orbits._enumerate_cost4_circuits_for_rep_fast(
            rep, L4_arr, full, 16,
            l_bitsets=l_bitsets, l_ints=l_ints, h_ints=h_ints, gf_idx=gf_idx, idx_m=idx4,
        )
        assert fast_nosym == ref, f"n=4 fast_nosym mismatch on {hex(rep)}"
        assert fast_sym == ref, f"n=4 fast_sym mismatch on {hex(rep)}"


def test_cost4_fast_matches_reference_on_n5_sample() -> None:
    L_keys, L_arr, idx5, _ = _closed_l1_le2_n5()
    full = 0xFFFFFFFF
    bit_pos = np.arange(32, dtype=np.uint32)

    # Full W = 3 check on parity3 (|G_f| = 3840)
    _, L3_keys = orbits.ltfs_with_bound(5, W=3)
    L3_arr = np.array(L3_keys, dtype=np.uint32)
    par3_rep = int(_canon5_batch([0x0FF0F00F], idx5)[0])
    bmat = ((np.uint32(par3_rep) >> bit_pos) & np.uint32(1)).astype(np.uint8)
    packed = np.packbits(bmat[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
    gf_par3 = sorted(set(np.nonzero(packed == np.uint32(par3_rep))[0].tolist())
                     | set(np.nonzero(packed == np.uint32(full ^ par3_rep))[0].tolist()))

    ref_par3 = orbits._enumerate_cost4_circuits_for_rep(par3_rep, L3_arr, full, 32)
    fast_par3 = orbits._enumerate_cost4_circuits_for_rep_fast(
        par3_rep, L3_arr, full, 32, gf_idx=gf_par3, idx_m=idx5
    )
    assert len(ref_par3) > 0
    assert fast_par3 == ref_par3

    # Additional closed |w|_1 <= 2 cost=4 reps compared against reference enumerator
    l_bs = orbits._build_l_bitsets(L_arr, 32)
    l_set = set(L_keys)
    pair_vals = [a & b for a in L_keys for b in L_keys if (a & b) not in l_set]
    cost3_set = set(_canon5_batch(pair_vals, idx5).tolist())
    triple_cands = []
    for a in L_keys[::7]:
        for b in L_keys[::11]:
            for c in L_keys[::13]:
                triple_cands.extend((a & b & c, a & (b | c), (a & b) | (a & c) | (b & c)))
    c4_reps: list[int] = []
    for rc in _canon5_batch(triple_cands, idx5).tolist():
        if rc not in l_set and rc not in cost3_set and not orbits._enumerate_cost3_circuits_for_rep(rc, L_arr, full):
            c4_reps.append(rc)
            if len(c4_reps) >= 4:
                break
    assert len(c4_reps) >= 3

    for rep in c4_reps:
        ref = orbits._enumerate_cost4_circuits_for_rep(rep, L_arr, full, 32)
        fast_ns = orbits._enumerate_cost4_circuits_for_rep_fast(rep, L_arr, full, 32, l_bitsets=l_bs)
        bm = ((np.uint32(rep) >> bit_pos) & np.uint32(1)).astype(np.uint8)
        pk = np.packbits(bm[idx5], axis=1, bitorder="little").view(np.uint32).ravel()
        gf_i = sorted(set(np.nonzero(pk == np.uint32(rep))[0].tolist())
                      | set(np.nonzero(pk == np.uint32(full ^ rep))[0].tolist()))
        fast_s = orbits._enumerate_cost4_circuits_for_rep_fast(
            rep, L_arr, full, 32, l_bitsets=l_bs, gf_idx=gf_i, idx_m=idx5
        )
        assert len(ref) > 0
        assert fast_ns == ref
        assert fast_s == ref


def test_n5_bruteforce_matches_fast_enumerators_on_closed_l1_le2_family() -> None:
    L_keys, L_arr, idx5, T5 = _closed_l1_le2_n5()
    full = 0xFFFFFFFF
    l_set = set(L_keys)

    pair_vals = [a & b for a in L_keys[::3] for b in L_keys[::5] if (a & b) not in l_set]
    cost3_reps = [r for r in _canon5_batch(pair_vals, idx5).tolist() if r not in l_set][:5]
    assert len(cost3_reps) == 5

    orbits._init_n5_worker(L_arr, idx5, full, True)
    for rep in cost3_reps:
        fast_row = orbits._n5_cost3_worker(rep)
        bf_row = orbits.enumerate_class_bruteforce(rep, 3, 5, L_keys, T5)
        for key in (
            "num_circuits", "num_orbits", "orbit_sizes",
            "oriented_num_circuits", "oriented_num_orbits", "oriented_orbit_sizes",
            "gf_order", "gf_np_order",
        ):
            assert fast_row[key] == bf_row[key], f"cost=3 mismatch on {hex(rep)} key={key}"

    all_pair_vals = [a & b for a in L_keys for b in L_keys if (a & b) not in l_set]
    cost3_all = set(_canon5_batch(all_pair_vals, idx5).tolist())
    triple_cands = []
    for a in L_keys[::5]:
        for b in L_keys[::7]:
            for c in L_keys[::13]:
                triple_cands.extend((a & b & c, (a & b) | (a & c) | (b & c)))
    cost4_reps = [
        r for r in _canon5_batch(triple_cands, idx5).tolist()
        if r not in l_set and r not in cost3_all and not orbits._enumerate_cost3_circuits_for_rep(r, L_arr, full)
    ][:3]
    assert len(cost4_reps) == 3

    for rep in cost4_reps:
        fast_row = orbits._n5_cost4_worker((rep, False))
        bf_row = orbits.enumerate_class_bruteforce(rep, 4, 5, L_keys, T5)
        assert fast_row["cost3_circuits_at_W"] == 0
        for key in (
            "num_circuits", "num_orbits", "orbit_sizes",
            "oriented_num_circuits", "oriented_num_orbits", "oriented_orbit_sizes",
            "gf_order", "gf_np_order",
        ):
            assert fast_row[key] == bf_row[key], f"cost=4 mismatch on {hex(rep)} key={key}"
