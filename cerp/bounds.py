"""Untrusted search for lower-bound certificates (checked by cerp.kernel_bounds)."""

from __future__ import annotations

from itertools import combinations_with_replacement


def _vec(n, pts):
    return tuple(sum((p >> j) & 1 for p in pts) for j in range(n))


def not_threshold_cert(n, f, kmax=4):
    T = [p for p in range(1 << n) if (f >> p) & 1]
    F = [p for p in range(1 << n) if not (f >> p) & 1]
    for k in range(2, kmax + 1):
        sums = {}
        for a in combinations_with_replacement(T, k):
            sums.setdefault(_vec(n, a), a)
        for b in combinations_with_replacement(F, k):
            a = sums.get(_vec(n, b))
            if a is not None:
                return {"pos": list(a), "neg": list(b)}
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
    masks = [sum(1 << uni.index(q) for q in b["set"]) for b in bad]
    return all(any((s & c) == s or (s & c) == 0 for s in masks) for c in range(1 << len(uni)))
