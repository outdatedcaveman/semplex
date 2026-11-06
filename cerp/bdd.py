"""Reduced ordered BDDs as the canonical form for fragment F0 (Layer G).

Established result (Bryant 1986): for a FIXED variable order, the reduced
ordered BDD of a Boolean function is unique. So, with the order as a
declared parameter, `normal_form` below is a normal form N with
    N(N(C)) = N(C)   and   N(C1) = N(C2)  <=>  [[C1]] = [[C2]].
Our *implementation* of that theorem is tested, not proved (status:
EMPIRICALLY-SUPPORTED for the code; the theorem itself is literature).

Note the parameter: canonicity is relative to the order. Different orders
give different (and differently sized) canonical objects for the same
function -- canonical form is itself protocol-indexed.
"""

from __future__ import annotations

from .semantics import TruthTable


class BDD:
    def __init__(self, order):
        self.order = tuple(order)
        self.level = {v: i for i, v in enumerate(self.order)}
        self.nodes = [None, None]  # 0 = FALSE, 1 = TRUE
        self.unique = {}
        self._ite_memo = {}

    # node = (level, lo, hi)
    def mk(self, level, lo, hi):
        if lo == hi:
            return lo
        key = (level, lo, hi)
        if key not in self.unique:
            self.unique[key] = len(self.nodes)
            self.nodes.append(key)
        return self.unique[key]

    def var(self, name):
        return self.mk(self.level[name], 0, 1)

    def _top(self, u):
        return self.nodes[u][0] if u > 1 else len(self.order)

    def _cof(self, u, lvl, b):
        if u <= 1 or self.nodes[u][0] != lvl:
            return u
        return self.nodes[u][2] if b else self.nodes[u][1]

    def ite(self, f, g, h):
        if f == 1:
            return g
        if f == 0:
            return h
        if g == h:
            return g
        if g == 1 and h == 0:
            return f
        key = (f, g, h)
        if key in self._ite_memo:
            return self._ite_memo[key]
        lvl = min(self._top(f), self._top(g), self._top(h))
        hi = self.ite(self._cof(f, lvl, 1), self._cof(g, lvl, 1), self._cof(h, lvl, 1))
        lo = self.ite(self._cof(f, lvl, 0), self._cof(g, lvl, 0), self._cof(h, lvl, 0))
        r = self.mk(lvl, lo, hi)
        self._ite_memo[key] = r
        return r

    def NOT(self, f): return self.ite(f, 0, 1)
    def AND(self, f, g): return self.ite(f, g, 0)
    def OR(self, f, g): return self.ite(f, 1, g)
    def XOR(self, f, g): return self.ite(f, self.NOT(g), g)

    # ----------------------------------------------------------- builders
    def from_expr(self, e):
        op = e[0]
        if op == "const":
            return e[1]
        if op == "var":
            return self.var(e[1])
        if op == "not":
            return self.NOT(self.from_expr(e[1]))
        a = self.from_expr(e[1])
        if op == "ite":
            return self.ite(a, self.from_expr(e[2]), self.from_expr(e[3]))
        b = self.from_expr(e[2])
        return {"and": self.AND, "or": self.OR, "xor": self.XOR}[op](a, b)

    def from_truthtable(self, tt: TruthTable):
        if tt.vars != self.order:
            raise ValueError("truth table order must equal BDD order")
        n = tt.n
        memo = {}

        def build(level, prefix):
            # prefix: integer of the first `level` bits
            if level == n:
                return tt.at(prefix)
            key = (level, prefix)
            if key not in memo:
                lo = build(level + 1, prefix << 1)
                hi = build(level + 1, (prefix << 1) | 1)
                memo[key] = self.mk(level, lo, hi)
            return memo[key]

        return build(0, 0)

    def from_artifact(self, body):
        if tuple(body["order"]) != self.order:
            raise ValueError("order mismatch")
        memo = {0: 0, 1: 1}

        def go(i):
            if i not in memo:
                lvl, lo, hi = body["nodes"][i]
                memo[i] = self.mk(lvl, go(lo), go(hi))
            return memo[i]

        return go(body["root"])

    def restrict(self, f, c):
        """Coudert-Madre 'restrict' generalized cofactor: a BDD that agrees
        with f wherever c = 1 and uses the don't-cares to simplify.
        Heuristic w.r.t. size (not guaranteed smaller); exact w.r.t. care."""
        memo = {}

        def go(f, c):
            if c == 0:
                raise ValueError("empty care set")
            if c == 1 or f <= 1:
                return f
            key = (f, c)
            if key in memo:
                return memo[key]
            lf, lc = self._top(f), self._top(c)
            if lc < lf:  # c tests a var f does not depend on here: existentially merge
                r = go(f, self.OR(self.nodes[c][1], self.nodes[c][2]))
            else:
                lvl = lf
                c0, c1 = self._cof(c, lvl, 0), self._cof(c, lvl, 1)
                f0, f1 = self._cof(f, lvl, 0), self._cof(f, lvl, 1)
                if c0 == 0:
                    r = go(f1, c1)
                elif c1 == 0:
                    r = go(f0, c0)
                else:
                    r = self.mk(lvl, go(f0, c0), go(f1, c1))
            memo[key] = r
            return r

        return go(f, c)

    # ----------------------------------------------------------- export
    def export(self, u) -> dict:
        """Deterministic renumbering => canonical serialized form."""
        ids, out = {0: 0, 1: 1}, [[-1, 0, 0], [-1, 1, 1]]

        def go(v):
            if v in ids:
                return ids[v]
            lvl, lo, hi = self.nodes[v]
            a, b = go(lo), go(hi)
            ids[v] = len(out)
            out.append([lvl, a, b])
            return ids[v]

        root = go(u)
        return {"kind": "bdd", "body": {"order": list(self.order), "nodes": out, "root": root}}


def evaluate_bdd(body, env):
    i = body["root"]
    while i > 1:
        lvl, lo, hi = body["nodes"][i]
        i = hi if env[body["order"][lvl]] else lo
    return i


def normal_form(artifact, order) -> dict:
    """N(C): canonical BDD artifact for any F0 artifact, under `order`."""
    from .substrates import semantics

    m = BDD(order)
    if artifact["kind"] == "expr":
        u = m.from_expr(artifact["body"])
    elif artifact["kind"] == "bdd" and tuple(artifact["body"]["order"]) == tuple(order):
        u = m.from_artifact(artifact["body"])
    else:
        u = m.from_truthtable(semantics(artifact, order))
    return m.export(u)


def task_normal_form(artifact, care_artifact, order) -> dict:
    """Canonical object of the quotient by task-equivalence (Layer G + H).

    Two artifacts are T-equivalent (agree on every care point) iff they
    have equal (care, f AND care) pairs. The pair is canonical even though
    the *cheapest realization* of the class is not unique.
    """
    from .substrates import semantics

    m = BDD(order)
    f = m.from_truthtable(semantics(artifact, order))
    c = m.from_truthtable(semantics(care_artifact, order))
    return {"care": m.export(c), "on": m.export(m.AND(f, c))}
