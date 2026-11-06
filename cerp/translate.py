"""Translators between substrates (Layer J).

Translators are UNTRUSTED. They may be clever, heuristic or (later)
AI-generated. Nothing they output is accepted until cerp.kernel checks a
claim relating it to its source. See cerp/pipeline.py.
"""

from __future__ import annotations

from .bdd import BDD
from .semantics import TruthTable
from .substrates import CircuitBuilder

# ------------------------------------------------------------ expr -> circuit

def expr_to_circuit(expr_art, inputs) -> dict:
    cb = CircuitBuilder(inputs)

    def go(e):
        op = e[0]
        if op == "var":
            return e[1]
        if op == "const":
            return cb.gate("const1" if e[1] else "const0")
        if op == "not":
            return cb.gate("not", go(e[1]))
        if op == "ite":
            c, t, f = go(e[1]), go(e[2]), go(e[3])
            return cb.gate("or", cb.gate("and", c, t), cb.gate("and", cb.gate("not", c), f))
        return cb.gate(op, go(e[1]), go(e[2]))

    return cb.build(go(expr_art["body"]))


# ------------------------------------------------------------ bdd -> circuit

def bdd_to_circuit(bdd_art, inputs) -> dict:
    """Multiplexer realization: node(x, lo, hi) -> (x & hi) | (~x & lo)."""
    b = bdd_art["body"]
    cb = CircuitBuilder(inputs)
    memo = {}

    def go(i):
        if i == 0:
            return cb.gate("const0")
        if i == 1:
            return cb.gate("const1")
        if i in memo:
            return memo[i]
        lvl, lo, hi = b["nodes"][i]
        x = b["order"][lvl]
        if (lo, hi) == (0, 1):
            r = x
        elif (lo, hi) == (1, 0):
            r = cb.gate("not", x)
        elif lo == 0:
            r = cb.gate("and", x, go(hi))
        elif hi == 0:
            r = cb.gate("and", cb.gate("not", x), go(lo))
        elif lo == 1:
            r = cb.gate("or", cb.gate("not", x), go(hi))
        elif hi == 1:
            r = cb.gate("or", x, go(lo))
        else:
            r = cb.gate("or", cb.gate("and", x, go(hi)), cb.gate("and", cb.gate("not", x), go(lo)))
        memo[i] = r
        return r

    return cb.build(go(b["root"]))


# ------------------------------------------------------------ bdd -> dfa

def bdd_to_dfa(bdd_art) -> dict:
    """Quasi-reduced layering of an ordered BDD is a DFA over the fixed order.

    State (level, node). If the node does not test `level`, both edges
    pass through. For a fixed reading order this is the minimal DFA for
    the function's fixed-length language, up to the merged sink (known
    correspondence; our code is tested, not proved).
    """
    b = bdd_art["body"]
    nodes, n = b["nodes"], len(b["order"])
    start = (0, b["root"])
    delta, accept, frontier, seen = {}, [], [start], {start}

    def name(s):
        return f"L{s[0]}N{s[1]}"

    while frontier:
        lvl, u = s = frontier.pop()
        if lvl == n:
            if u == 1:
                accept.append(name(s))
            continue
        if u > 1 and nodes[u][0] == lvl:
            nxt = [(lvl + 1, nodes[u][1]), (lvl + 1, nodes[u][2])]
        else:
            nxt = [(lvl + 1, u), (lvl + 1, u)]
        delta[name(s)] = [name(t) for t in nxt]
        for t in nxt:
            if t not in seen:
                seen.add(t)
                frontier.append(t)
    return {"kind": "dfa", "body": {"order": list(b["order"]), "start": name(start),
                                    "delta": dict(sorted(delta.items())), "accept": sorted(accept)}}


# ------------------------------------------------------------ bdd -> expr

def bdd_to_expr(bdd_art) -> dict:
    """Shannon expansion as nested ite (a tree: sharing is lost -> may blow up)."""
    b = bdd_art["body"]

    def go(i):
        if i in (0, 1):
            return ["const", i]
        lvl, lo, hi = b["nodes"][i]
        x = ["var", b["order"][lvl]]
        if (lo, hi) == (0, 1):
            return x
        if (lo, hi) == (1, 0):
            return ["not", x]
        if lo == 0:
            return ["and", x, go(hi)]
        if hi == 0:
            return ["and", ["not", x], go(lo)]
        return ["ite", x, go(hi), go(lo)]

    return {"kind": "expr", "body": go(b["root"])}


# ------------------------------------------------------------ circuit -> expr

def circuit_to_expr(circ_art) -> dict:
    """Unfold the DAG into a tree. Exposes the cost of losing sharing."""
    c = circ_art["body"]
    by_id = {g["id"]: g for g in c["gates"]}
    memo = {}

    def go(r):
        if r not in by_id:
            return ["var", r]
        if r in memo:
            return memo[r]
        g = by_id[r]
        op = g["op"]
        if op == "const0":
            e = ["const", 0]
        elif op == "const1":
            e = ["const", 1]
        else:
            e = [op] + [go(x) for x in g["in"]]
        memo[r] = e
        return e

    import copy
    return {"kind": "expr", "body": copy.deepcopy(go(c["output"]))}


# ------------------------------------------------------------ truth table -> *

def truthtable_to_bdd(tt: TruthTable) -> dict:
    m = BDD(tt.vars)
    return m.export(m.from_truthtable(tt))


def restrict_to_care(f: TruthTable, care: TruthTable) -> dict:
    """Don't-care-aware simplification over the full variable order."""
    m = BDD(f.vars)
    return m.export(m.restrict(m.from_truthtable(f), m.from_truthtable(care)))


def truthtable_to_artifact(tt: TruthTable) -> dict:
    """Used for care sets: a canonical BDD artifact of the predicate."""
    return truthtable_to_bdd(tt)
