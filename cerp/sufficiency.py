"""Task-relative sufficiency for fragment F0 (charter Layer H, §5.5).

Task T = (f, care): a target Boolean function f and a care set (the task's
admissible input domain D_T; points outside are don't-cares). A variable
set S is SUFFICIENT for T iff
    for all x, y in care:  x|S == y|S  =>  f(x) == f(y).

Reformulation used here (finite case): call {v : x_v != y_v} the conflict
set of a pair (x, y) in care with f(x) != f(y). Then S is sufficient iff S
hits every conflict set, so the minimal sufficient sets are exactly the
minimal transversals of the conflict hypergraph. This is the rough-set
"reduct" / discernibility-matrix construction (Pawlak; Skowron & Rauszer
1992 -- bibliographic details to be verified per charter §13).

Proposition (full care => uniqueness). If care is the whole domain, the
unique minimal sufficient set is support(f): every v in support(f) yields
a singleton conflict {v}. Multiplicity of minimal representations is
therefore a property of RESTRICTED task domains (correlated inputs).
"""

from __future__ import annotations

from itertools import combinations

from .semantics import TruthTable

MAX_SUFFICIENCY_VARS = 12


def _mask_to_vars(mask, vars):
    n = len(vars)
    return frozenset(v for j, v in enumerate(vars) if mask >> (n - 1 - j) & 1)


def conflict_sets(f: TruthTable, care: TruthTable) -> list:
    """Minimal (under inclusion) conflict sets, as bitmasks."""
    on = [i for i in care.ones() if f.at(i)]
    off = [i for i in care.ones() if not f.at(i)]
    masks = {x ^ y for x in on for y in off}
    # absorption: keep only inclusion-minimal masks
    minimal = []
    for m in sorted(masks, key=lambda m: bin(m).count("1")):
        if not any(k & m == k for k in minimal):
            minimal.append(m)
    return minimal


def minimal_sufficient_sets(f: TruthTable, care: TruthTable | None = None) -> list:
    if care is None:
        care = TruthTable.const(f.vars, 1)
    n = f.n
    if n > MAX_SUFFICIENCY_VARS:
        raise ValueError(f"sufficiency enumeration limited to {MAX_SUFFICIENCY_VARS} vars")
    conflicts = conflict_sets(f, care)
    found = []
    for k in range(n + 1):
        for combo in combinations(range(n), k):
            s = sum(1 << (n - 1 - j) for j in combo)
            if any(m & s == m for m in found):
                continue  # superset of a known minimal set
            if all(c & s for c in conflicts):
                found.append(s)
    return [_mask_to_vars(s, f.vars) for s in found]


def insufficiency_witness(f: TruthTable, care: TruthTable, s: frozenset):
    """A pair (x, y) in care, agreeing on s, with f(x) != f(y); or None."""
    seen = {}
    for i in care.ones():
        env = f.env(i)
        key = tuple(env[v] for v in f.vars if v in s)
        if key in seen and f.at(seen[key]) != f.at(i):
            return f.env(seen[key]), env
        seen.setdefault(key, i)
    return None


def project(f: TruthTable, care: TruthTable, s: frozenset, fill: int = 0) -> TruthTable:
    """The function of S alone that agrees with f on care (don't-cares := fill)."""
    sub = tuple(v for v in f.vars if v in s)
    table = {}
    for i in care.ones():
        env = f.env(i)
        key = tuple(env[v] for v in sub)
        table[key] = f.at(i)
    return TruthTable.from_function(sub, lambda env: table.get(tuple(env[v] for v in sub), fill))


def report(f: TruthTable, care: TruthTable | None = None) -> dict:
    sets = minimal_sufficient_sets(f, care)
    allv = set(f.vars)
    necessary = frozenset.intersection(*sets) if sets else frozenset()
    used = frozenset().union(*sets) if sets else frozenset()
    return {
        "minimal_sufficient_sets": [sorted(s) for s in sets],
        "necessary": sorted(necessary),               # in every minimal set
        "substitutable": sorted(used - necessary),     # in some, not all
        "dispensable": sorted(allv - used),            # in none
        "unique": len(sets) == 1,
    }
