"""Structured circuit families for Spike 03 (equivalence beyond n = 16).

Each pair computes the same function by structurally different means,
so equivalence is not syntactic. A deliberately buggy variant gives
non-equivalent pairs.
"""

from __future__ import annotations

from .substrates import CircuitBuilder


def _ab(k):
    return [f"a{i}" for i in range(k)], [f"b{i}" for i in range(k)]


def carry_ripple(k):
    """Carry-out of a + b (k bits), ripple chain."""
    a, b = _ab(k)
    cb = CircuitBuilder(a + b)
    c = cb.gate("const0")
    for i in range(k):
        g = cb.gate("and", a[i], b[i])
        p = cb.gate("xor", a[i], b[i])
        c = cb.gate("or", g, cb.gate("and", c, p))
    return cb.build(c), a + b


def carry_prefix(k, bug=False):
    """Carry-out via a recursive (Sklansky-style) generate/propagate tree."""
    a, b = _ab(k)
    cb = CircuitBuilder(a + b)

    def gp(lo, hi):  # (G, P) for bit range [lo, hi)
        if hi - lo == 1:
            g = cb.gate("and", a[lo], b[lo])
            p = cb.gate("or", a[lo], b[lo])
            return g, p
        mid = (lo + hi) // 2
        gl, pl = gp(lo, mid)
        gh, ph = gp(mid, hi)
        if bug and lo == 0 and hi == k:
            return gh, cb.gate("and", ph, pl)  # drops the carry from the low half
        return cb.gate("or", gh, cb.gate("and", ph, gl)), cb.gate("and", ph, pl)

    g, _ = gp(0, k)
    return cb.build(g), a + b


def less_than_msb(k):
    """a < b (unsigned), scanning from the most significant bit."""
    a, b = _ab(k)
    cb = CircuitBuilder(a + b)
    lt = cb.gate("const0")
    eq = cb.gate("const1")
    for i in reversed(range(k)):
        bit_lt = cb.gate("and", cb.gate("not", a[i]), b[i])
        lt = cb.gate("or", lt, cb.gate("and", eq, bit_lt))
        eq = cb.gate("and", eq, cb.gate("not", cb.gate("xor", a[i], b[i])))
    return cb.build(lt), a + b


def less_than_borrow(k):
    """a < b as the final borrow of a - b, scanning from the LSB."""
    a, b = _ab(k)
    cb = CircuitBuilder(a + b)
    br = cb.gate("const0")
    for i in range(k):
        na = cb.gate("not", a[i])
        t1 = cb.gate("and", na, b[i])
        t2 = cb.gate("and", cb.gate("not", cb.gate("xor", a[i], b[i])), br)
        br = cb.gate("or", t1, t2)
    return cb.build(br), a + b


FAMILIES = {
    "carry: ripple vs prefix": lambda k: (carry_ripple(k), carry_prefix(k), True),
    "carry: ripple vs BUGGY prefix": lambda k: (carry_ripple(k), carry_prefix(k, bug=True), False),
    "a<b: msb-scan vs borrow-chain": lambda k: (less_than_msb(k), less_than_borrow(k), True),
}
