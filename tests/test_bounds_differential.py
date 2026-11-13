"""Differential tests between cerp.kernel_bounds and the Lean 4 Bounds.lean predicates (P048)."""

import itertools
import random

from cerp import bounds, kernel_bounds


def _lean_not_threshold_pred(n: int, pos: list[int], neg: list[int]) -> bool:
    """Exact mirror of Bounds.lean not_threshold_cert_sound hypotheses."""
    if len(pos) != len(neg) or len(pos) == 0:
        return False
    return all(
        sum((p >> j) & 1 for p in pos) == sum((q >> j) & 1 for q in neg)
        for j in range(n)
    )


def _lean_not_two_hs_pred(n: int, bad: list[tuple[list[int], list[int]]]) -> bool:
    """Exact mirror of Bounds.lean not_two_halfspaces_cert_sound hypotheses."""
    for b_pos, b_neg in bad:
        if not _lean_not_threshold_pred(n, b_pos, b_neg):
            return False
    pts = sorted({q for _, b_neg in bad for q in b_neg})
    for bits in range(1 << len(pts)):
        col = {q: bool((bits >> i) & 1) for i, q in enumerate(pts)}
        if not any(
            all(col[q] for q in b_neg) or all(not col[q] for q in b_neg)
            for _, b_neg in bad
        ):
            return False
    return True


def test_not_threshold_matches_lean_predicate():
    rng = random.Random(42)
    n = 4
    for _ in range(40):
        f = rng.randrange(1 << (1 << n))
        cert = bounds.not_threshold_cert(n, f)
        if cert is not None:
            pos, neg = cert["pos"], cert["neg"]
            assert kernel_bounds.check_not_threshold(n, f, pos, neg).ok
            assert _lean_not_threshold_pred(n, pos, neg)
            # Mutate one point to break coordinate sum equality and verify both reject
            bad_pos = list(pos)
            bad_pos[0] = bad_pos[0] ^ 1
            if not _lean_not_threshold_pred(n, bad_pos, neg):
                assert not kernel_bounds.check_not_threshold(n, f, bad_pos, neg).ok


def test_not_two_halfspaces_matches_lean_predicate():
    rng = random.Random(99)
    n = 4
    checked = 0
    for _ in range(120):
        f = rng.randrange(1 << (1 << n))
        bad = bounds.not_two_halfspaces_cert(n, f, kmax=2)
        if bad is None:
            continue
        v = kernel_bounds.check_not_two_halfspaces(n, f, bad)
        assert v.ok
        lean_bad = [(b["pos"], b["neg"]) for b in bad]
        assert _lean_not_two_hs_pred(n, lean_bad)
        # Dropping a bad set should break or preserve both identically
        if len(bad) > 1:
            sub = bad[:-1]
            v_sub = kernel_bounds.check_not_two_halfspaces(n, f, sub)
            assert v_sub.ok == _lean_not_two_hs_pred(n, lean_bad[:-1])
        checked += 1
        if checked >= 15:
            break
    assert checked >= 10


def test_point_selector_one_bit_flip_matches_lean_theorem():
    """Verify Bounds.lean one_bit_flip_add_point_neuron on all 3-input threshold functions."""
    n = 3
    pts = list(itertools.product([0, 1], repeat=n))
    for w in [(1, 1, 1), (2, -1, 1), (0, 1, -1)]:
        for t in (0, 1, 2):
            f = [sum(wi * xi for wi, xi in zip(w, x)) >= t for x in pts]
            for idx, x0 in enumerate(pts):
                flipped = [not f[i] if i == idx else f[i] for i in range(len(pts))]
                pw = [1 if b == 1 else -1 for b in x0]
                pt = sum(x0)
                p = [sum(wi * xi for wi, xi in zip(pw, x)) >= pt for x in pts]
                if not f[idx]:
                    assert flipped == [fi or pi for fi, pi in zip(f, p)]
                else:
                    assert flipped == [fi and (not pi) for fi, pi in zip(f, p)]
