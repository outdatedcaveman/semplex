"""Trusted kernel extension: certificates for LOWER bounds on threshold circuits.

Stdlib only; imports only the core kernel. Points are ints (bit j = x_j);
truth tables are ints (bit number = point).

1. check_not_threshold(n, f, pos, neg)
   pos: k points where f = 1, neg: k points where f = 0 (repeats allowed),
   with equal coordinate-wise sums. Then f is NOT a threshold function:
   a neuron [w.x >= t] would give  sum_pos w.p >= k t > sum_neg w.q,  but the
   two sides are equal because the point sums are equal.

2. check_not_two_halfspaces(n, f, bad)
   bad: list of {"set": S, "pos": [...], "neg": [...]} where S is a set of
   false points, neg is drawn from S, pos from true points, equal sums.
   By (1) no single neuron is true on all true points and false on all of S.
   If f = g1 AND g2 with both threshold, colour each false point by a g_i that
   rejects it: no bad set can be monochromatic. So if EVERY 2-colouring of the
   false points makes some bad set monochromatic, f is not an intersection of
   two halfspaces. The kernel checks all colourings itself.

With both f and NOT f certified by (2), and f certified by (1), f needs at
least 4 neurons in a strictly layered threshold net: 1 or 2 neurons compute
threshold functions only, and 3 neurons compute g1 AND g2 or g1 OR g2.
"""

from __future__ import annotations

from .kernel import KERNEL_VERSION, KernelError, Verdict, _TOKEN


def _val(f, p):
    return (f >> p) & 1


def _sums_equal(n, pos, neg):
    return len(pos) == len(neg) > 0 and all(
        sum((p >> j) & 1 for p in pos) == sum((q >> j) & 1 for q in neg) for j in range(n))


def _valid(n, f, pts):
    if type(f) is not int or not 0 <= f < (1 << (1 << n)):
        raise KernelError("bad table")
    for p in pts:
        if type(p) is not int or not 0 <= p < (1 << n):
            raise KernelError("bad point")


def check_not_threshold(n, f, pos, neg) -> Verdict:
    _valid(n, f, list(pos) + list(neg))
    ok = (all(_val(f, p) == 1 for p in pos) and all(_val(f, q) == 0 for q in neg)
          and _sums_equal(n, pos, neg))
    return Verdict(ok, "not-threshold", (), len(pos), None, KERNEL_VERSION, _TOKEN)


def check_not_two_halfspaces(n, f, bad) -> Verdict:
    masks, universe = [], []
    for b in bad:
        S, pos, neg = list(b["set"]), list(b["pos"]), list(b["neg"])
        _valid(n, f, S + pos + neg)
        if not (all(_val(f, q) == 0 for q in S) and all(q in S for q in neg)
                and all(_val(f, p) == 1 for p in pos) and _sums_equal(n, pos, neg)):
            return Verdict(False, "not-two-halfspaces", (), 0, None, KERNEL_VERSION, _TOKEN)
        for q in S:
            if q not in universe:
                universe.append(q)
        masks.append(sum(1 << universe.index(q) for q in S))
    if len(universe) > 20:
        raise KernelError("too many points to colour exhaustively")
    for colouring in range(1 << len(universe)):
        if not any((s & colouring) == s or (s & colouring) == 0 for s in masks):
            return Verdict(False, "not-two-halfspaces", (), colouring, None, KERNEL_VERSION, _TOKEN)
    return Verdict(True, "not-two-halfspaces", (), 1 << len(universe), None, KERNEL_VERSION, _TOKEN)
