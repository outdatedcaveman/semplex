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


def check_not_threshold_partial(n, f, care, pos, neg) -> Verdict:
    """Partially specified f: only points in `care` carry labels. Certifies that NO
    completion of f is a threshold function. Same argument as check_not_threshold,
    but every pos/neg point must be a care point, so the certificate never relies on
    a don't-care value (Spike 35: the total-function search wrongly used don't-cares)."""
    _valid(n, f, list(pos) + list(neg))
    if type(care) is not int or not 0 <= care < (1 << (1 << n)):
        raise KernelError("bad care mask")
    ok = (all((care >> p) & 1 for p in list(pos) + list(neg))
          and all(_val(f, p) == 1 for p in pos) and all(_val(f, q) == 0 for q in neg)
          and _sums_equal(n, pos, neg))
    return Verdict(ok, "not-threshold-partial", (), len(pos), None, KERNEL_VERSION, _TOKEN)


def check_not_two_halfspaces_partial(n, f, care, bad) -> Verdict:
    """Partial-function analogue of check_not_two_halfspaces: every point in every
    bad set and witness (S, pos, neg) must lie in `care`."""
    if type(care) is not int or not 0 <= care < (1 << (1 << n)):
        raise KernelError("bad care mask")
    masks, universe = [], []
    for b in bad:
        S, pos, neg = list(b["set"]), list(b["pos"]), list(b["neg"])
        pts = S + pos + neg
        _valid(n, f, pts)
        if not (all((care >> q) & 1 for q in pts)
                and all(_val(f, q) == 0 for q in S) and all(q in S for q in neg)
                and all(_val(f, p) == 1 for p in pos) and _sums_equal(n, pos, neg)):
            return Verdict(False, "not-two-halfspaces-partial", (), 0, None, KERNEL_VERSION, _TOKEN)
        for q in S:
            if q not in universe:
                universe.append(q)
        masks.append(sum(1 << universe.index(q) for q in S))
    if len(universe) > 20:
        raise KernelError("too many points to colour exhaustively")
    for colouring in range(1 << len(universe)):
        if not any((s & colouring) == s or (s & colouring) == 0 for s in masks):
            return Verdict(False, "not-two-halfspaces-partial", (), colouring, None, KERNEL_VERSION, _TOKEN)
    return Verdict(True, "not-two-halfspaces-partial", (), 1 << len(universe), None, KERNEL_VERSION, _TOKEN)
_B4_PERMS = None


def _get_b4_perms():
    global _B4_PERMS
    if _B4_PERMS is None:
        from itertools import permutations
        _B4_PERMS = list(permutations(range(4)))
    return _B4_PERMS


def _canon16(f):
    return (0xFFFF ^ f) if (f & 1) else f


_REG_EDGES16 = (
    (0, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15),
    (1, 2), (5, 6), (9, 10), (13, 14),
    (2, 4), (3, 5), (10, 12), (11, 13),
    (4, 8), (5, 9), (6, 10), (7, 11),
)


def _is_regular16(g):
    return all(((g >> u) & 1) <= ((g >> v) & 1) for u, v in _REG_EDGES16)


def _apply_b4(f, perm_idx, neg_mask):
    p = _get_b4_perms()[perm_idx]
    r = 0
    for x in range(16):
        y = (
            (((x >> p[0]) & 1) ^ (neg_mask & 1))
            | ((((x >> p[1]) & 1) ^ ((neg_mask >> 1) & 1)) << 1)
            | ((((x >> p[2]) & 1) ^ ((neg_mask >> 2) & 1)) << 2)
            | ((((x >> p[3]) & 1) ^ ((neg_mask >> 3) & 1)) << 3)
        )
        if (f >> y) & 1:
            r |= 1 << x
    return r


def _elem_op16(f, kind):
    if kind == "neg0":
        return sum((((f >> (x ^ 1)) & 1) << x) for x in range(16))
    if kind == "sw01":
        return sum((((f >> ((x & ~3) | ((x & 1) << 1) | ((x >> 1) & 1))) & 1) << x) for x in range(16))
    if kind == "sw12":
        return sum((((f >> ((x & ~6) | ((x & 2) << 1) | ((x >> 1) & 2))) & 1) << x) for x in range(16))
    return sum((((f >> ((x & ~12) | ((x & 4) << 1) | ((x >> 1) & 4))) & 1) << x) for x in range(16))


def _check_pair_cert_b4(g1, crt, target):
    if not isinstance(crt, dict):
        return False
    g2 = crt.get("g2")
    if type(g2) is not int or not 0 <= g2 < 65536 or crt.get("kind") not in ("single", "multi"):
        return False
    if crt["kind"] == "single":
        c1, c2 = crt.get("c1"), crt.get("c2")
        pos, neg = crt.get("pos"), crt.get("neg")
        if (c1 not in (0, 1) or c2 not in (0, 1)
                or not isinstance(pos, list) or not isinstance(neg, list)):
            return False
        _valid(4, g1, pos + neg)
        return (
            _sums_equal(4, pos, neg)
            and all(_val(g1, p) == c1 and _val(g2, p) == c2 and _val(target, p) == 1 for p in pos)
            and all(_val(g1, q) == c1 and _val(g2, q) == c2 and _val(target, q) == 0 for q in neg)
        )
    tags, wits = crt.get("tags"), crt.get("wits")
    if (not isinstance(tags, list) or not isinstance(wits, list)
            or not 1 <= len(tags) <= 4 or len(wits) != (1 << (len(tags) - 1))):
        return False
    for entry in tags:
        if not isinstance(entry, (list, tuple)) or len(entry) != 4:
            return False
        c1, c2, a0, b0 = entry
        _valid(4, target, [a0, b0])
        if c1 not in (0, 1) or c2 not in (0, 1):
            return False
        if not (_val(g1, a0) == c1 and _val(g2, a0) == c2 and _val(target, a0) == 1
                and _val(g1, b0) == c1 and _val(g2, b0) == c2 and _val(target, b0) == 0):
            return False
    m = len(tags)
    for mask in range(1 << (m - 1)):
        signs = [1] + [0 if ((mask >> (ci - 1)) & 1) else 1 for ci in range(1, m)]
        wit = wits[mask]
        if not isinstance(wit, dict) or not isinstance(wit.get("pos"), list) or not isinstance(wit.get("neg"), list):
            return False
        pos, neg = wit["pos"], wit["neg"]
        _valid(4, target, pos + neg)
        if not _sums_equal(4, pos, neg):
            return False
        if not all(any(_val(g1, p) == c1 and _val(g2, p) == c2 and _val(target, p) == s
                       for (c1, c2, _, _), s in zip(tags, signs)) for p in pos):
            return False
        if not all(any(_val(g1, q) == c1 and _val(g2, q) == c2 and _val(target, q) == (1 - s)
                       for (c1, c2, _, _), s in zip(tags, signs)) for q in neg):
            return False
    return True


def check_parity4_needs_5_neurons(cert) -> Verdict:
    """Verify the certificate that 4-input parity cannot be computed by <= 4 threshold neurons."""
    fail = lambda reason=None: Verdict(False, "parity4-needs-5-neurons", (), 0, reason, KERNEL_VERSION, _TOKEN)
    if not isinstance(cert, dict):
        return fail("bad-cert-type")
    target = sum((1 << x) for x in range(16) if bin(x).count("1") & 1)
    if cert.get("target") != target:
        return fail("bad-target")
    reps = cert.get("reps")
    orbits = cert.get("orbits")
    stabilizers = cert.get("stabilizers")
    const_const = cert.get("const_const")
    const_reps = cert.get("const_reps")
    pair_certs = cert.get("pair_certs")
    pair_witnesses = cert.get("pair_witnesses")
    if (not isinstance(reps, list) or len(reps) != 15
            or not isinstance(orbits, list) or len(orbits) != 14
            or not isinstance(stabilizers, list) or len(stabilizers) != 14
            or not isinstance(const_reps, list) or len(const_reps) != 14
            or not isinstance(pair_certs, list) or len(pair_certs) != 14
            or not isinstance(pair_witnesses, list) or len(pair_witnesses) != 14):
        return fail("bad-lengths")

    rep_tables = []
    for idx, r in enumerate(reps):
        if not isinstance(r, dict):
            return fail(f"rep-{idx}")
        tbl, w, t = r.get("table"), r.get("weights"), r.get("threshold")
        if (type(tbl) is not int or not 0 <= tbl < 65536 or (tbl & 1) != 0
                or not isinstance(w, (list, tuple)) or len(w) != 4
                or any(type(wi) is not int for wi in w) or type(t) is not int):
            return fail(f"rep-type-{idx}")
        if not (0 <= w[0] <= w[1] <= w[2] <= w[3]):
            return fail(f"rep-not-monotone-{idx}")
        realized = sum(
            (1 << x) for x in range(16)
            if sum(w[j] * ((x >> j) & 1) for j in range(4)) >= t
        )
        if realized != tbl or not _is_regular16(tbl):
            return fail(f"rep-not-regular-ltf-{idx}")
        rep_tables.append(tbl)
    if rep_tables[0] != 0 or len(set(rep_tables)) != 15:
        return fail("rep-distinct")

    orb_sets = []
    classified = {0}
    for k in range(14):
        rep_k = rep_tables[k + 1]
        members = orbits[k]
        if not isinstance(members, list) or not members:
            return fail(f"orbit-empty-{k}")
        oset = set()
        for entry in members:
            if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                return fail(f"orbit-entry-{k}")
            f, p_idx, neg = entry
            if (type(f) is not int or not 0 <= f < 65536 or (f & 1) != 0
                    or type(p_idx) is not int or not 0 <= p_idx < 24
                    or type(neg) is not int or not 0 <= neg < 16):
                return fail(f"orbit-bounds-{k}")
            if _canon16(_apply_b4(f, p_idx, neg)) != rep_k:
                return fail(f"orbit-map-{k}")
            oset.add(f)
        if rep_k not in oset:
            return fail(f"orbit-missing-rep-{k}")
        for f in oset:
            for op in ("neg0", "sw01", "sw12", "sw23"):
                if _canon16(_elem_op16(f, op)) not in oset:
                    return fail(f"orbit-unclosed-{k}")
        orb_sets.append(oset)
        classified |= oset

    for g in range(65536):
        if _is_regular16(g) and _canon16(g) not in classified:
            return fail(f"unclassified-regular-{g}")

    if not _check_pair_cert_b4(0, const_const, target):
        return fail("const-const")
    for k in range(14):
        if not _check_pair_cert_b4(0, const_reps[k], target) or const_reps[k].get("g2") != rep_tables[k + 1]:
            return fail(f"const-rep-{k}")

    total_checked = 1 + 14 + 15
    for i1 in range(14):
        rep1 = rep_tables[i1 + 1]
        stab = stabilizers[i1]
        if not isinstance(stab, list) or not stab:
            return fail(f"stab-{i1}")
        for s_entry in stab:
            if not isinstance(s_entry, (list, tuple)) or len(s_entry) != 2:
                return fail(f"stab-entry-{i1}")
            sp, sneg = s_entry
            if type(sp) is not int or not 0 <= sp < 24 or type(sneg) is not int or not 0 <= sneg < 16:
                return fail(f"stab-bounds-{i1}")
            if _canon16(_apply_b4(rep1, sp, sneg)) != rep1:
                return fail(f"stab-not-fixing-{i1}")

        certs1 = pair_certs[i1]
        if not isinstance(certs1, list) or not certs1:
            return fail(f"certs-{i1}")
        for crt in certs1:
            if not _check_pair_cert_b4(rep1, crt, target):
                return fail(f"cert-invalid-{i1}")
        total_checked += len(certs1)

        wrow = pair_witnesses[i1]
        if not isinstance(wrow, list) or len(wrow) != 14 - i1:
            return fail(f"wrow-{i1}")
        for off, i2 in enumerate(range(i1, 14)):
            wlist = wrow[off]
            if not isinstance(wlist, list):
                return fail(f"wlist-{i1}-{i2}")
            seen_f2 = set()
            for w_entry in wlist:
                if not isinstance(w_entry, (list, tuple)) or len(w_entry) != 3:
                    return fail(f"wentry-{i1}-{i2}")
                f2, si, cid = w_entry
                if (type(f2) is not int or type(si) is not int or type(cid) is not int
                        or not 0 <= si < len(stab) or not 0 <= cid < len(certs1)):
                    return fail(f"wbounds-{i1}-{i2}")
                sp, sneg = stab[si]
                if _canon16(_apply_b4(f2, sp, sneg)) != certs1[cid]["g2"]:
                    return fail(f"wmap-{i1}-{i2}")
                seen_f2.add(f2)
            if seen_f2 != orb_sets[i2]:
                return fail(f"wcover-{i1}-{i2}")
            total_checked += len(seen_f2)

    return Verdict(True, "parity4-needs-5-neurons", (), total_checked, None, KERNEL_VERSION, _TOKEN)
