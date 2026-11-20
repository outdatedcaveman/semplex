"""Tests for exact minimum-circuit enumeration and G_f-orbit quotienting (Gap A10)."""

from __future__ import annotations

import itertools
import math

import pytest

from cerp import atlas, orbits


def test_ltf_weight_bound_matches_known_counts():
    for m in (1, 2, 3, 4):
        L, keys = orbits.ltfs_with_bound(m, W=3)
        assert len(keys) == atlas.KNOWN_LTF_COUNTS[m]
        for b in keys:
            w, _t = L[b]
            assert max(abs(v) for v in w) <= 3


def test_n1_to_n3_matches_bruteforce_exactly():
    tables = atlas.build_all(3)
    for m in (1, 2, 3):
        tb = tables[m]
        L_keys = sorted(tb.ltf.keys())
        fast_rows = orbits.enumerate_dimension(m, tb=tb)
        assert len(fast_rows) == {1: 2, 2: 4, 3: 14}[m]

        for row in fast_rows:
            bf = orbits.enumerate_class_bruteforce(row["rep"], row["cost"], m, L_keys, tb.T)
            for k in (
                "rep",
                "cost",
                "gf_order",
                "gf_np_order",
                "num_circuits",
                "num_orbits",
                "orbit_sizes",
                "oriented_num_circuits",
                "oriented_num_orbits",
                "oriented_orbit_sizes",
            ):
                assert row[k] == bf[k], f"Mismatch at m={m} rep={row['rep']} key={k}: {row[k]} vs {bf[k]}"

            # Group-theoretic sanity checks
            assert sum(row["orbit_sizes"]) == row["num_circuits"]
            assert sum(row["oriented_orbit_sizes"]) == row["oriented_num_circuits"]
            for s in row["orbit_sizes"]:
                assert row["gf_order"] % s == 0
            for s in row["oriented_orbit_sizes"]:
                assert row["gf_order"] % s == 0


def test_n4_spot_checks_and_group_laws():
    tables = atlas.build_all(4)
    tb4 = tables[4]
    L4_keys = sorted(tb4.ltf.keys())
    L4_arr = orbits.np.array(L4_keys, dtype=orbits.np.uint32)
    full4 = 65535
    npn_order = 2 * math.factorial(4) * (1 << 4)
    class_counts = {}
    for c in tb4.canon.tolist():
        class_counts[c] = class_counts.get(c, 0) + 1

    # Check ALL 128 cost=3 classes (fast ~0.3s) and verify one against full brute force
    cost3_reps = [r for r in tb4.classes() if int(tb4.hi[r]) == 3]
    assert len(cost3_reps) == 128
    for rep in cost3_reps:
        unoriented = orbits._enumerate_cost3_circuits_for_rep(rep, L4_arr, full4)
        gf_idx, _ = orbits._stabilizer_indices(rep, tb4.T, 4)
        assert len(gf_idx) * class_counts[rep] == npn_order
        n_orb, sizes = orbits.count_orbits(unoriented, gf_idx, 4, unoriented=True)
        assert sum(sizes) == len(unoriented)
        assert all(len(gf_idx) % s == 0 for s in sizes)
        assert n_orb >= 1

    # Spot-check 1 cost=3 class via full C(H4, 2) enumeration against L2
    rep0 = cost3_reps[0]
    H4 = sorted(b for b in L4_keys if b <= (full4 ^ b))
    L2_arr = orbits._subcube_ltf_lookup(2)
    bf_u = set()
    for a, b in itertools.combinations(H4, 2):
        pm, nm = 0, 0
        for x in range(16):
            code = ((a >> x) & 1) | (((b >> x) & 1) << 1)
            if (rep0 >> x) & 1:
                pm |= 1 << code
            else:
                nm |= 1 << code
        if not (pm & nm) and orbits.np.any(((L2_arr & pm) == pm) & ((L2_arr & nm) == 0)):
            bf_u.add((a, b))
    assert sorted(bf_u) == orbits._enumerate_cost3_circuits_for_rep(rep0, L4_arr, full4)

    # Spot-check 2 cost=4 classes on n=4 for exact Orbit-Stabilizer closure
    cost4_reps = [r for r in tb4.classes() if int(tb4.hi[r]) == 4][:2]
    for rep in cost4_reps:
        unoriented = orbits._enumerate_cost4_circuits_for_rep(rep, L4_arr, full4, 16)
        gf_idx, _ = orbits._stabilizer_indices(rep, tb4.T, 4)
        n_orb, sizes = orbits.count_orbits(unoriented, gf_idx, 4, unoriented=True)
        assert sum(sizes) == len(unoriented)
        assert all(len(gf_idx) % s == 0 for s in sizes)
        assert n_orb >= 1
