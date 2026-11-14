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


def not_threshold_cert_partial(n, f, care, kmax=4):
    """Untrusted search for a check_not_threshold_partial certificate: uses care points only."""
    T = [p for p in range(1 << n) if (care >> p) & 1 and (f >> p) & 1]
    F = [p for p in range(1 << n) if (care >> p) & 1 and not (f >> p) & 1]
    for k in range(2, kmax + 1):
        sums = {}
        for a in combinations_with_replacement(T, k):
            sums.setdefault(_vec(n, a), a)
        for b in combinations_with_replacement(F, k):
            a = sums.get(_vec(n, b))
            if a is not None:
                return {"pos": list(a), "neg": list(b)}
    return None


def _canon16(f):
    return (0xFFFF ^ f) if (f & 1) else f


def _apply_b4(f, perm, neg_mask):
    r = 0
    for x in range(16):
        y = (
            (((x >> perm[0]) & 1) ^ (neg_mask & 1))
            | ((((x >> perm[1]) & 1) ^ ((neg_mask >> 1) & 1)) << 1)
            | ((((x >> perm[2]) & 1) ^ ((neg_mask >> 2) & 1)) << 2)
            | ((((x >> perm[3]) & 1) ^ ((neg_mask >> 3) & 1)) << 3)
        )
        if (f >> y) & 1:
            r |= 1 << x
    return r


def _find_sum4(T, F, kmax=4):
    for k in range(2, kmax + 1):
        sums = {}
        for a in combinations_with_replacement(T, k):
            sums.setdefault(_vec(4, a), a)
        for b in combinations_with_replacement(F, k):
            a = sums.get(_vec(4, b))
            if a is not None:
                return list(a), list(b)
    return None


def _certify_pair_b4(g1, g2, target):
    bks = []
    for c1 in (0, 1):
        for c2 in (0, 1):
            A = [x for x in range(16)
                 if ((g1 >> x) & 1) == c1 and ((g2 >> x) & 1) == c2 and ((target >> x) & 1) == 1]
            B = [x for x in range(16)
                 if ((g1 >> x) & 1) == c1 and ((g2 >> x) & 1) == c2 and ((target >> x) & 1) == 0]
            if A and B:
                bks.append((c1, c2, A, B))
    for c1, c2, A, B in bks:
        w = _find_sum4(A, B)
        if w is not None:
            return {"kind": "single", "g2": g2, "c1": c1, "c2": c2, "pos": w[0], "neg": w[1]}
    m = len(bks)
    wits = []
    for mask in range(1 << (m - 1)):
        T, F = list(bks[0][2]), list(bks[0][3])
        for ci in range(1, m):
            if (mask >> (ci - 1)) & 1:
                T.extend(bks[ci][3])
                F.extend(bks[ci][2])
            else:
                T.extend(bks[ci][2])
                F.extend(bks[ci][3])
        w = _find_sum4(T, F)
        assert w is not None
        wits.append({"pos": w[0], "neg": w[1]})
    tags = [[c1, c2, A[0], B[0]] for c1, c2, A, B in bks]
    return {"kind": "multi", "g2": g2, "tags": tags, "wits": wits}


def parity4_five_neuron_cert():
    """Untrusted search constructing the full B_4-reduced 5-neuron lower-bound
    certificate for 4-input parity (verified by kernel_bounds.check_parity4_needs_5_neurons)."""
    from itertools import permutations

    target = sum((1 << x) for x in range(16) if bin(x).count("1") & 1)
    reg_wt = {}
    for w0 in range(5):
        for w1 in range(w0, 5):
            for w2 in range(w1, 5):
                for w3 in range(w2, 5):
                    w = (w0, w1, w2, w3)
                    vals = [sum(w[j] * ((x >> j) & 1) for j in range(4)) for x in range(16)]
                    for t in range(1, sum(w) + 1):
                        tbl = sum((1 << x) for x in range(16) if vals[x] >= t)
                        if 0 < tbl < 0xFFFF and (tbl & 1) == 0:
                            cur = reg_wt.get(tbl)
                            if cur is None or sum(w) < sum(cur[0]):
                                reg_wt[tbl] = ([w0, w1, w2, w3], t)

    b4 = [(pi, perm, neg) for pi, perm in enumerate(permutations(range(4))) for neg in range(16)]
    orbits_raw = {}
    seen = set()
    for rtbl in sorted(reg_wt):
        if rtbl in seen:
            continue
        omap = {}
        for pi, perm, neg in b4:
            f = _canon16(_apply_b4(rtbl, perm, neg))
            if f not in seen:
                seen.add(f)
        for pi, perm, neg in b4:
            f = _canon16(_apply_b4(rtbl, perm, neg))
            if f not in omap:
                inv = next((pi2, neg2) for pi2, p2, neg2 in b4 if _canon16(_apply_b4(f, p2, neg2)) == rtbl)
                omap[f] = inv
        orbits_raw[rtbl] = omap

    assert len(orbits_raw) == 14 and sum(len(o) for o in orbits_raw.values()) == 940
    ordered_reps = sorted(orbits_raw, key=lambda r: (-len(orbits_raw[r]), r))

    reps = [{"table": 0, "weights": [0, 0, 0, 0], "threshold": 1}]
    orbits = []
    for rtbl in ordered_reps:
        w, t = reg_wt[rtbl]
        reps.append({"table": rtbl, "weights": w, "threshold": t})
        orbits.append([[f, p, neg] for f, (p, neg) in sorted(orbits_raw[rtbl].items())])

    stabilizers = []
    pair_certs = []
    pair_witnesses = []
    for i1, rep1 in enumerate(ordered_reps):
        stab = [(pi, perm, neg) for pi, perm, neg in b4 if _canon16(_apply_b4(rep1, perm, neg)) == rep1]
        stabilizers.append([[pi, neg] for pi, _, neg in stab])
        certs1 = []
        witness_map = {}
        wrow = []
        for i2 in range(i1, 14):
            rep2 = ordered_reps[i2]
            wlist = []
            for f2 in sorted(orbits_raw[rep2]):
                if f2 not in witness_map:
                    cid = len(certs1)
                    certs1.append(_certify_pair_b4(rep1, f2, target))
                    for pi, perm, neg in stab:
                        g2 = _canon16(_apply_b4(f2, perm, neg))
                        if g2 not in witness_map:
                            si = next(sidx for sidx, (_, sp, sneg) in enumerate(stab)
                                      if _canon16(_apply_b4(g2, sp, sneg)) == f2)
                            witness_map[g2] = (si, cid)
                si, cid = witness_map[f2]
                wlist.append([f2, si, cid])
            wrow.append(wlist)
        pair_certs.append(certs1)
        pair_witnesses.append(wrow)

    return {
        "target": target,
        "reps": reps,
        "orbits": orbits,
        "stabilizers": stabilizers,
        "const_const": _certify_pair_b4(0, 0, target),
        "const_reps": [_certify_pair_b4(0, r, target) for r in ordered_reps],
        "pair_certs": pair_certs,
        "pair_witnesses": pair_witnesses,
    }
