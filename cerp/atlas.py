"""Atlas of threshold circuits: a verifiable "periodic table" (Spike 08). UNTRUSTED.

Family T (v1): strictly layered networks of threshold neurons on m binary
inputs. A neuron outputs [sum_i w_i * in_i >= t] with integer weights and
reads only the previous layer; the last layer is one neuron.

Elements: Boolean functions up to NPN equivalence (permute / negate inputs,
negate the output). The family is closed under all three, so cost is a
class invariant.

Layer peeling (the recursion everything rests on). A net with first-layer
width w computes  f = Psi(g_1, ..., g_w)  where each g_i is a single
threshold function of the inputs and Psi is computed by the REST of the net,
itself a net of family T on w inputs. Hence

    neurons_m(f) = min over w, g, Psi with f = Psi o g of  w + neurons_w(Psi)

with base case neurons = 1 for threshold functions. In Protocol-Frame terms
(THEORY.md): the first layer is an observational power Omega = {g_1..g_w} on
the hypothesis space of inputs, and f is computable above it iff Omega
DETERMINES f (Theorem 3 / 10). Minimal first-layer width is a minimum hitting
set of f's conflict hypergraph with threshold functions as protocols.

What is exact and what is not. We enumerate every first layer of width
<= wenum (3 for m >= 3), up to symmetry, so for each f:
    hi(f) = best found  (upper bound; witness net is kernel-checkable)
    lo(f) = min(hi(f), wenum + 2)  (anything unseen needs width > wenum)
The entry is exact iff lo == hi. Completeness of the threshold-function
enumeration is anchored to the known counts 4, 14, 104, 1882 (OEIS A000609).

Truth tables are ints: bit number sum(x_j << j) is the value at x.
"""

from __future__ import annotations

import itertools
import os
import pathlib
import pickle
from dataclasses import dataclass

import numpy as np

WMAX = 3
KNOWN_LTF_COUNTS = {1: 4, 2: 14, 3: 104, 4: 1882}
BIG = 255


def names(m):
    return [f"x{j}" for j in range(m)]


# ------------------------------------------------------------ threshold functions

def ltfs(m):
    """All threshold functions of m inputs: {bits: (weights, t)} with small weights."""
    X = np.array([[(i >> j) & 1 for j in range(m)] for i in range(1 << m)], dtype=np.int64)
    pow2 = [1 << i for i in range(1 << m)]
    for W in range(1, 6):
        out = {}
        for w in itertools.product(range(-W, W + 1), repeat=m):
            s = X @ np.array(w, dtype=np.int64)
            for t in range(int(s.min()), int(s.max()) + 2):
                bits = sum(p for p, v in zip(pow2, s) if v >= t)
                cur = out.get(bits)
                if cur is None or sum(map(abs, w)) < sum(map(abs, cur[0])):
                    out[bits] = (tuple(int(v) for v in w), t)
        if len(out) == KNOWN_LTF_COUNTS[m]:
            return out, W
    raise RuntimeError("threshold-function enumeration did not reach the known count")


# ------------------------------------------------------------ symmetries

def transforms(m):
    """[(perm, negmask, index_array)]; (T e)(x) = e(y), y_j = x[perm[j]] ^ neg_j."""
    out = []
    for perm in itertools.permutations(range(m)):
        for neg in range(1 << m):
            idx = np.array([sum((((i >> perm[j]) & 1) ^ ((neg >> j) & 1)) << j for j in range(m))
                            for i in range(1 << m)], dtype=np.int64)
            out.append((perm, neg, idx))
    return out


def apply_T(bits, idx, outneg, m):
    r = sum(((bits >> int(y)) & 1) << i for i, y in enumerate(idx))
    return r ^ ((1 << (1 << m)) - 1) if outneg else r


def _pack(bitmat):
    """(N, 2^m) uint8 0/1 -> (N,) ints."""
    k = bitmat.shape[1]
    b = np.packbits(bitmat, axis=1, bitorder="little")
    if k <= 8:
        return b[:, 0].astype(np.int64)
    return (b[:, 0].astype(np.int64) | (b[:, 1].astype(np.int64) << 8))


def canon_all(m, T):
    n = 1 << (1 << m)
    F = np.arange(n, dtype=np.int64)
    B = ((F[:, None] >> np.arange(1 << m)) & 1).astype(np.uint8)
    best = np.full(n, n, dtype=np.int64)
    for _, _, idx in T:
        v = _pack(B[:, idx])
        best = np.minimum(best, np.minimum(v, (n - 1) ^ v))
    return best


# ------------------------------------------------------------ the table

@dataclass
class Table:
    m: int
    ltf: dict            # bits -> (w, t)
    W: int               # weight magnitude that sufficed
    T: list
    canon: np.ndarray    # class representative of every function
    hi: np.ndarray       # best known neuron count
    depth: np.ndarray    # depth of that best net
    d2: np.ndarray       # best known neuron count among depth <= 2 nets (BIG if none found)
    exhibit: dict        # class rep -> member carrying a stored witness
    wit: dict            # exhibit -> (w, [g bits], psi bits)
    wenum: int           # every first layer of width <= wenum was enumerated

    @property
    def bound(self):
        """Anything not found needs first-layer width > wenum, hence >= wenum + 2 neurons."""
        return self.wenum + 2

    @property
    def lo(self):
        return np.minimum(self.hi, self.bound)

    def exact(self, f):
        return int(self.hi[f]) <= self.bound

    def classes(self):
        return sorted(self.exhibit)


def build(m, tables):
    """Build the table for m inputs from the tables for fewer inputs."""
    L, W = ltfs(m)
    T = transforms(m)
    canon = canon_all(m, T)
    n = 1 << (1 << m)
    full = n - 1
    key = np.full(n, BIG * 8, dtype=np.int64)       # neurons * 8 + depth, lexicographic
    d2 = np.full(n, BIG, dtype=np.int64)
    wit_w = np.zeros(n, dtype=np.int64)
    wit_g = np.zeros((n, WMAX), dtype=np.int64)
    wit_psi = np.zeros(n, dtype=np.int64)
    for b in L:
        key[b] = 1 * 8 + 1
        d2[b] = 1

    H = sorted(b for b in L if b <= (full ^ b))      # one of each complement pair
    Hbits = np.array([[(b >> i) & 1 for i in range(1 << m)] for b in H], dtype=np.int64)
    reps = sorted({int(canon[b]) for b in L})
    rep_idx = [H.index(r) for r in reps]

    def closed():
        ck = np.full(n, BIG * 8, dtype=np.int64)
        np.minimum.at(ck, canon, key)
        return ck[canon]

    def sweep(w, psi_key):
        """Try every first layer of width w with every known rest-of-net Psi."""
        nw = 1 << (1 << w)
        psis = sorted((int(psi_key[p]), p) for p in range(nw)
                      if p <= ((nw - 1) ^ p) and psi_key[p] < BIG * 8)
        rest = np.array(list(itertools.combinations_with_replacement(range(len(H)), w - 1)), dtype=np.int64)
        changed = False
        for r in rep_idx:
            cells = Hbits[r][None, :].repeat(len(rest), axis=0)
            for i in range(w - 1):
                cells = cells | (Hbits[rest[:, i]] << (i + 1))
            for pk, psi in psis:
                cost, dep = pk // 8, pk % 8
                table = np.array([(psi >> c) & 1 for c in range(1 << w)], dtype=np.uint8)
                fb = _pack(table[cells])
                k = (w + cost) * 8 + (1 + dep)
                sel = key[fb] > k
                if sel.any():
                    changed = True
                    tgt = fb[sel]
                    key[tgt] = k
                    wit_w[tgt] = w
                    wit_psi[tgt] = psi
                    wit_g[tgt, 0] = r
                    wit_g[tgt, 1:w] = rest[sel]
                if dep == 1:
                    s2 = d2[fb] > w + 1
                    d2[fb[s2]] = w + 1
        return changed

    # Widths below m use the finished smaller tables. Width m refers to this
    # very table (the rest-of-net is a net on m inputs), so iterate to a fixpoint;
    # it is well founded because the rest is always strictly cheaper.
    wenum = 1
    for w in range(2, WMAX + 1):
        if w < m:
            tw = tables[w]
            sweep(w, tw.hi * 8 + tw.depth)
            wenum = w
        elif w == m:
            while sweep(w, closed()):
                pass
            wenum = w
    if m == 1:
        wenum = WMAX

    # Seeded upper bound: parity via m counting neurons [sum x >= k] and an
    # alternating output. Only used where enumeration found nothing; the kernel
    # checks it like any other witness.
    seeded = {}
    par = sum(1 << i for i in range(1 << m) if bin(i).count("1") % 2)
    if key[par] > (m + 1) * 8 + 2:
        key[par] = (m + 1) * 8 + 2
        d2[par] = min(int(d2[par]), m + 1)
        seeded[par] = [[{"w": [1] * m, "t": k} for k in range(1, m + 1)],
                       [{"w": [(-1) ** k for k in range(m)], "t": 1}]]

    # exhibits: per class, a directly found member with the best key
    order = np.lexsort((key, canon))
    exhibit, wit = {}, {}
    seen = set()
    for f in order:
        c = int(canon[f])
        if c in seen:
            continue
        seen.add(c)
        f = int(f)
        exhibit[c] = f
        if f in seeded:
            wit[f] = ("seed", seeded[f])
        elif f not in L and key[f] < BIG * 8:
            w = int(wit_w[f])
            wit[f] = (w, [H[int(g)] for g in wit_g[f, :w]], int(wit_psi[f]))
    # close under NPN: cost is a class invariant
    ck = np.full(n, BIG * 8, dtype=np.int64)
    np.minimum.at(ck, canon, key)
    key = ck[canon]
    c2 = np.full(n, BIG, dtype=np.int64)
    np.minimum.at(c2, canon, d2)
    return Table(m, L, W, T, canon, key // 8, key % 8, c2[canon], exhibit, wit, wenum)


_CACHE_DIR = pathlib.Path(__file__).resolve().parent.parent / "atlas" / ".cache"


def _source_tag():
    """Hash of this file: the cache is valid only for the code that built it."""
    import hashlib
    return hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()[:12]


def build_all(m_max=4, *, use_cache=True):
    """Exact tables for 1..m_max inputs. Cached under atlas/.cache, keyed by m_max AND
    by the hash of atlas.py, so editing the builder can never serve stale tables."""
    cache_path = _CACHE_DIR / f"tables_m{m_max}_{_source_tag()}.pkl"
    if use_cache and cache_path.exists():
        try:
            with cache_path.open("rb") as fh:
                return pickle.load(fh)
        except Exception:
            pass
    tables = {}
    for m in range(1, m_max + 1):
        tables[m] = build(m, tables)
    if use_cache:
        try:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp_path = cache_path.with_suffix(f".tmp.{os.getpid()}")
            with tmp_path.open("wb") as fh:
                pickle.dump(tables, fh, protocol=pickle.HIGHEST_PROTOCOL)
            tmp_path.replace(cache_path)
            for old in _CACHE_DIR.glob(f"tables_m{m_max}*.pkl"):
                if old != cache_path:
                    old.unlink()
        except Exception:
            pass
    return tables


# ------------------------------------------------------------ witnesses

def _neuron(wt):
    return {"w": list(wt[0]), "t": int(wt[1])}


def net_layers(tables, m, f):
    """Layers of a best-known net for ANY function f of m inputs (None if unknown)."""
    tb = tables[m]
    if f in tb.ltf:
        return [[_neuron(tb.ltf[f])]]
    e = tb.exhibit[int(tb.canon[f])]
    if e not in tb.wit:
        return None
    if tb.wit[e][0] == "seed":
        layers = tb.wit[e][1]
    else:
        w, gs, psi = tb.wit[e]
        layers = [[_neuron(tb.ltf[g]) for g in gs]] + net_layers(tables, w, psi)
    if e == f:
        return layers
    for perm, neg, idx in tb.T:
        for o in (0, 1):
            if apply_T(e, idx, o, m) == f:
                return _transform(layers, perm, neg, o, m)
    raise AssertionError("no symmetry maps the exhibit to f")


def _transform(layers, perm, neg, outneg, m):
    first = []
    for nrn in layers[0]:
        w2, t2 = [0] * m, nrn["t"]
        for j in range(m):
            if (neg >> j) & 1:
                w2[perm[j]] = -nrn["w"][j]
                t2 -= nrn["w"][j]
            else:
                w2[perm[j]] = nrn["w"][j]
        first.append({"w": w2, "t": t2})
    out = [first] + [[dict(n) for n in layer] for layer in layers[1:]]
    if outneg:
        last = out[-1][0]
        out[-1] = [{"w": [-v for v in last["w"]], "t": 1 - last["t"]}]
    return out


def artifact(tables, m, f):
    layers = net_layers(tables, m, f)
    return None if layers is None else {"kind": "tnet", "body": {"inputs": names(m), "layers": layers}}


def table_artifact(m, bits):
    return {"kind": "table", "body": {"order": names(m), "bits": int(bits)}}


def shape(layers):
    return tuple(len(l) for l in layers)


# ------------------------------------------------------------ compiler v1

def compile_task(tables, m, f, care):
    """Cheapest known net agreeing with f on every care point.

    Searches every completion of the don't-cares. `optimal` is True when the
    choice is provably optimal within family T: its neuron count is <= the
    lower bound of every completion (i.e. <= tb.bound)."""
    tb = tables[m]
    full = (1 << (1 << m)) - 1
    care &= full
    cands = np.array([f & care], dtype=np.int64)
    for p in range(1 << m):
        if not (care >> p) & 1:
            cands = np.concatenate([cands, cands | (1 << p)])
    keys = tb.hi[cands] * 8 + tb.depth[cands]
    g = int(cands[int(np.argmin(keys))])
    return {"function": g, "neurons": int(tb.hi[g]), "depth": int(tb.depth[g]),
            "exact_neurons": int(tb.hi[f]), "completions": len(cands),
            "optimal": int(tb.hi[g]) <= tb.bound, "net": artifact(tables, m, g)}


# ------------------------------------------------------------ structure

def min_determining_layers(tb, f, wmax=3):
    """Protocol-Frame view: the smallest w such that some w threshold functions
    DETERMINE f, and how many such first layers there are ("isomers")."""
    m = tb.m
    full = (1 << (1 << m)) - 1
    if f in (0, full):
        return 0, 1
    H = sorted(b for b in tb.ltf if b <= (full ^ b) and b not in (0, full))
    Hbits = np.array([[(b >> i) & 1 for i in range(1 << m)] for b in H], dtype=np.int64)
    fb = np.array([(f >> i) & 1 for i in range(1 << m)], dtype=bool)
    for w in range(1, wmax + 1):
        combos = np.array(list(itertools.combinations(range(len(H)), w)), dtype=np.int64)
        cells = np.zeros((len(combos), 1 << m), dtype=np.int64)
        for i in range(w):
            cells |= Hbits[combos[:, i]] << i
        onehot = np.int64(1) << cells
        m1 = np.bitwise_or.reduce(np.where(fb[None, :], onehot, 0), axis=1)
        m0 = np.bitwise_or.reduce(np.where(~fb[None, :], onehot, 0), axis=1)
        k = int(((m1 & m0) == 0).sum())
        if k:
            return w, k
    return None, 0


def hamming_landscape(tb):
    """How much can the neuron count change when ONE truth-table bit flips?"""
    n = len(tb.hi)
    F = np.arange(n, dtype=np.int64)
    out = {}
    for j in range(1 << tb.m):
        d = np.abs(tb.hi[F] - tb.hi[F ^ (1 << j)])
        for v, c in zip(*np.unique(d, return_counts=True)):
            out[int(v)] = out.get(int(v), 0) + int(c)
    return out


# ------------------------------------------------------------ one-bit flips (Spike 08b, step 5)

def flip_bit_layers(layers, n, f, p):
    """Net for f XOR (indicator of point p), built from a depth <= 2 net for f.

    Depth 2: add ONE hidden neuron that fires only at p, with an output weight
    large enough to override everything else there (+1 neuron).
    Depth 1 (f is a single neuron g): hidden layer {g, indicator}, output
    g OR ind (if f(p) = 0) or g AND NOT ind (if f(p) = 1)  (+2 neurons)."""
    ind = {"w": [1 if (p >> j) & 1 else -1 for j in range(n)], "t": bin(p).count("1")}
    fp = (f >> p) & 1
    if len(layers) == 1:
        return [[dict(layers[0][0]), ind], [{"w": [1, -1 if fp else 1], "t": 1}]]
    if len(layers) != 2:
        raise ValueError("construction is for depth <= 2")
    out = layers[1][0]
    big = sum(abs(v) for v in out["w"]) + abs(out["t"]) + 1
    return [[dict(x) for x in layers[0]] + [ind],
            [{"w": list(out["w"]) + [-big if fp else big], "t": out["t"]}]]
