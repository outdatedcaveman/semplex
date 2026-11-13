"""Untrusted CDCL SAT solver that emits RUP certificates (Spike 03).

Nothing here is trusted. On UNSAT it returns the sequence of learned
clauses ending with the empty clause; cerp.kernel.check_rup re-derives the
formula and replays each lemma by unit propagation. On SAT it returns a
model, which cerp.kernel.check_counterexample checks by evaluation.

Standard design: two watched literals, first-UIP learning, VSIDS-style
activities with decay, phase saving, geometric restarts. No clause
deletion, so the certificate is pure additions (RUP, not DRUP).
"""

from __future__ import annotations

import time


class Solver:
    def __init__(self, n_vars, clauses):
        self.n = n_vars
        self.clauses = []
        self.watches = {}
        self.val = [0] * (n_vars + 1)        # 0 unassigned, 1 true, -1 false
        self.level = [0] * (n_vars + 1)
        self.reason = [None] * (n_vars + 1)
        self.act = [0.0] * (n_vars + 1)
        self.phase = [-1] * (n_vars + 1)
        self.trail, self.lim, self.qhead = [], [], 0
        self.inc = 1.0
        self.proof = []
        self.conflicts = 0
        self.unsat_at_root = False
        for c in clauses:
            self._add(list(dict.fromkeys(c)), learned=False)

    def _v(self, l):
        x = self.val[abs(l)]
        return x if l > 0 else -x

    def _assign(self, l, reason):
        v = abs(l)
        self.val[v] = 1 if l > 0 else -1
        self.level[v] = len(self.lim)
        self.reason[v] = reason
        self.trail.append(l)

    def _add(self, c, learned):
        if any(-l in c for l in c):
            return None
        if learned:
            self.proof.append(list(c))
        if not c:
            self.unsat_at_root = True
            return None
        if len(c) == 1:
            if self._v(c[0]) == -1 and self.level[abs(c[0])] == 0:
                self.unsat_at_root = True
            elif self._v(c[0]) == 0:
                self._assign(c[0], None)
            return None
        idx = len(self.clauses)
        self.clauses.append(c)
        self.watches.setdefault(c[0], []).append(idx)
        self.watches.setdefault(c[1], []).append(idx)
        return idx

    def _propagate(self):
        while self.qhead < len(self.trail):
            fl = -self.trail[self.qhead]
            self.qhead += 1
            ws = self.watches.get(fl, [])
            j = 0
            while j < len(ws):
                ci = ws[j]
                c = self.clauses[ci]
                if c[0] == fl:
                    c[0], c[1] = c[1], c[0]
                if self._v(c[0]) == 1:
                    j += 1
                    continue
                for k in range(2, len(c)):
                    if self._v(c[k]) != -1:
                        c[1], c[k] = c[k], c[1]
                        self.watches.setdefault(c[1], []).append(ci)
                        ws[j] = ws[-1]
                        ws.pop()
                        break
                else:
                    if self._v(c[0]) == -1:
                        return ci
                    self._assign(c[0], ci)
                    j += 1
        return None

    def _bump(self, v):
        self.act[v] += self.inc
        if self.act[v] > 1e100:
            self.act = [a * 1e-100 for a in self.act]
            self.inc *= 1e-100

    def _analyze(self, ci):
        seen, learnt, counter = set(), [], 0
        lvl = len(self.lim)
        p, idx = None, len(self.trail) - 1
        clause = self.clauses[ci]
        while True:
            for q in clause:
                if p is not None and q == p:
                    continue
                v = abs(q)
                if v not in seen and self.level[v] > 0:
                    seen.add(v)
                    self._bump(v)
                    if self.level[v] == lvl:
                        counter += 1
                    else:
                        learnt.append(q)
            while abs(self.trail[idx]) not in seen:
                idx -= 1
            p = self.trail[idx]
            idx -= 1
            counter -= 1
            if counter == 0:
                break
            clause = self.clauses[self.reason[abs(p)]]
        learnt.insert(0, -p)
        back = max((self.level[abs(l)] for l in learnt[1:]), default=0)
        if len(learnt) > 1:  # second watch must be the deepest remaining literal
            k = max(range(1, len(learnt)), key=lambda i: self.level[abs(learnt[i])])
            learnt[1], learnt[k] = learnt[k], learnt[1]
        self.inc /= 0.95
        return learnt, back

    def _backtrack(self, lvl):
        while len(self.lim) > lvl:
            start = self.lim.pop()
            for l in self.trail[start:]:
                v = abs(l)
                self.phase[v] = self.val[v]
                self.val[v] = 0
                self.reason[v] = None
            del self.trail[start:]
        self.qhead = min(self.qhead, len(self.trail))

    def _decide(self):
        best, bv = -1.0, 0
        for v in range(1, self.n + 1):
            if self.val[v] == 0 and self.act[v] > best:
                best, bv = self.act[v], v
        return bv

    def solve(self, time_limit=60.0):
        t0 = time.perf_counter()
        if self.unsat_at_root or self._propagate() is not None:
            self.proof.append([])
            return False
        restart_at, budget = 100, 100
        while True:
            ci = self._propagate()
            if ci is not None:
                self.conflicts += 1
                if not self.lim:
                    self.proof.append([])
                    return False
                learnt, back = self._analyze(ci)
                self._backtrack(back)
                idx = self._add(learnt, learned=True)
                if self.unsat_at_root:
                    self.proof.append([])
                    return False
                if idx is not None:
                    self._assign(learnt[0], idx)
                if self.conflicts >= restart_at:
                    budget = int(budget * 1.5)
                    restart_at = self.conflicts + budget
                    self._backtrack(0)
                if time.perf_counter() - t0 > time_limit:
                    return None
                continue
            v = self._decide()
            if v == 0:
                return True
            self.lim.append(len(self.trail))
            self._assign(v if self.phase[v] > 0 else -v, None)

    def model(self):
        return {v: (1 if self.val[v] > 0 else 0) for v in range(1, self.n + 1)}


def prove_equivalence(claim, time_limit=60.0):
    """Untrusted search. Returns ("unsat", lemmas) | ("sat", assignment) | ("timeout", None)."""
    from .kernel import miter_cnf

    n, clauses = miter_cnf(claim)
    s = Solver(n, clauses)
    r = s.solve(time_limit)
    if r is None:
        return "timeout", None, s
    if r is False:
        return "unsat", s.proof, s
    m = s.model()
    return "sat", {name: m[i + 1] for i, name in enumerate(claim["vars"])}, s


def rup_to_lrat(clauses, lemmas):
    """Convert a RUP proof (list of clauses) into hint-indexed LRAT steps [(clause, [cid, ...]), ...]."""
    db = [list(c) for c in clauses]
    lrat = []
    for C in lemmas:
        # `false_lits` are literals falsified by the current trail.
        # Initial trail is [-l for l in C], which falsifies every l in C.
        false_lits = set(C)
        hints = []
        while True:
            conflict_cid = None
            unit_cid = None
            unit_lit = None
            for cid, cl in enumerate(db):
                rem = [l for l in cl if l not in false_lits]
                if not rem:
                    conflict_cid = cid
                    break
                if len(rem) == 1 and unit_cid is None:
                    u = rem[0]
                    # Only propagate if -u is not already falsified (i.e. u not already true)
                    if (-u) not in false_lits:
                        unit_cid = cid
                        unit_lit = u
            if conflict_cid is not None:
                hints.append(conflict_cid)
                break
            if unit_cid is None:
                raise ValueError(f"RUP lemma {C} failed unit propagation during LRAT conversion")
            hints.append(unit_cid)
            false_lits.add(-unit_lit)
        lrat.append((list(C), hints))
        db.append(list(C))
        if not C:
            break
    return lrat


def _lean_tseitin_encode(body, var_idx, nxt):
    op = body[0]
    if op == "const":
        return nxt, [[nxt if int(body[1]) else -nxt]], nxt + 1
    if op == "var":
        return var_idx[body[1]] + 1, [], nxt
    if op == "not":
        oa, ca, n1 = _lean_tseitin_encode(body[1], var_idx, nxt)
        out = n1
        return out, ca + [[out, oa], [-out, -oa]], n1 + 1
    if op == "and":
        oa, ca, n1 = _lean_tseitin_encode(body[1], var_idx, nxt)
        ob, cb, n2 = _lean_tseitin_encode(body[2], var_idx, n1)
        out = n2
        return out, ca + cb + [[-out, oa], [-out, ob], [out, -oa, -ob]], n2 + 1
    if op == "or":
        oa, ca, n1 = _lean_tseitin_encode(body[1], var_idx, nxt)
        ob, cb, n2 = _lean_tseitin_encode(body[2], var_idx, n1)
        out = n2
        return out, ca + cb + [[out, -oa], [out, -ob], [-out, oa, ob]], n2 + 1
    if op == "xor":
        oa, ca, n1 = _lean_tseitin_encode(body[1], var_idx, nxt)
        ob, cb, n2 = _lean_tseitin_encode(body[2], var_idx, n1)
        out = n2
        return out, ca + cb + [[-out, -oa, -ob], [-out, oa, ob], [out, -oa, ob], [out, oa, -ob]], n2 + 1
    if op == "ite":
        oc, cc, n1 = _lean_tseitin_encode(body[1], var_idx, nxt)
        ot, ct, n2 = _lean_tseitin_encode(body[2], var_idx, n1)
        oe, ce, n3 = _lean_tseitin_encode(body[3], var_idx, n2)
        out = n3
        return out, cc + ct + ce + [[-oc, -out, ot], [-oc, out, -ot], [oc, -out, oe], [oc, out, -oe]], n3 + 1
    raise ValueError(f"Unsupported op for Lean Tseitin miter: {op!r}")


def _lean_tseitin_miter(vars_list, left_body, right_body):
    var_idx = {v: i for i, v in enumerate(vars_list)}
    n = len(vars_list)
    o1, c1, n1 = _lean_tseitin_encode(left_body, var_idx, n + 1)
    o2, c2, n2 = _lean_tseitin_encode(right_body, var_idx, n1)
    clauses = c1 + c2 + [[-n2, -o1, -o2], [-n2, o1, o2], [n2, -o1, o2], [n2, o1, -o2], [n2]]
    return n2, clauses


def prove_equivalence_lrat(claim, time_limit=60.0):
    """Untrusted search returning hint-indexed LRAT proof matching Cerp.tseitinMiter."""
    n, clauses = _lean_tseitin_miter(claim["vars"], claim["left"]["body"], claim["right"]["body"])
    s = Solver(n, clauses)
    r = s.solve(time_limit)
    if r is None:
        return "timeout", None, s
    if r is False:
        return "unsat", rup_to_lrat(clauses, s.proof), s
    m = s.model()
    return "sat", {name: m[i + 1] for i, name in enumerate(claim["vars"])}, s
