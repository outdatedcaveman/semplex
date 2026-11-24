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
    """Convert a RUP proof (list of clauses) into cone-of-influence trimmed LRAT steps [(clause, [cid, ...]), ...]."""
    base_len = len(clauses)
    db = [list(c) for c in clauses]
    raw_lrat = []
    for C in lemmas:
        # `false_lits` are literals falsified by the current trail.
        # Initial trail is [-l for l in C], which falsifies every l in C.
        c_set = set(C)
        false_lits = set(c_set)
        prop_records = []
        conflict_cid = None
        while True:
            unit_cid = None
            unit_lit = None
            unit_clause = None
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
                        unit_clause = cl
            if conflict_cid is not None:
                break
            if unit_cid is None:
                raise ValueError(f"RUP lemma {C} failed unit propagation during LRAT conversion")
            prop_records.append((unit_cid, unit_lit, unit_clause))
            false_lits.add(-unit_lit)

        # Backward cone-of-influence trimming of unit-propagation hints (preserving forward order).
        needed_false = set(db[conflict_cid]) - c_set
        kept_rev = []
        for cid, u, cl in reversed(prop_records):
            if (-u) in needed_false:
                needed_false.remove(-u)
                kept_rev.append(cid)
                for lit in cl:
                    if lit != u and lit not in c_set:
                        needed_false.add(lit)
        hints = kept_rev[::-1] + [conflict_cid]

        raw_lrat.append((list(C), hints))
        db.append(list(C))
        if not C:
            break

    if not raw_lrat or raw_lrat[-1][0]:
        return raw_lrat

    # Backward cone-of-influence pruning of unused intermediate lemmas.
    k = len(raw_lrat)
    used = [False] * k
    used[-1] = True
    needed_cids = set(raw_lrat[-1][1])
    for idx in range(k - 2, -1, -1):
        if (base_len + idx) in needed_cids:
            used[idx] = True
            needed_cids.update(raw_lrat[idx][1])
    remap = {}
    nxt_cid = base_len
    for idx, flag in enumerate(used):
        if flag:
            remap[base_len + idx] = nxt_cid
            nxt_cid += 1
    return [
        (c, [h if h < base_len else remap[h] for h in hs])
        for idx, (c, hs) in enumerate(raw_lrat)
        if used[idx]
    ]


def _lean_tseitin_encode(body, var_idx, nxt):
    op = body[0]
    if op == "const":
        return nxt, [[nxt if int(body[1]) else -nxt]], nxt + 1
    if op == "var":
        idx = body[1] if var_idx is None else var_idx[body[1]]
        return idx + 1, [], nxt
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


def _tnet_to_indexed_nodes(net, vars_list):
    """Normalize a ThresholdNet dict to Lean-indexed `TNode`s whose last node is `net['output']`."""
    wire_idx = {v: i for i, v in enumerate(vars_list)}
    tns = []
    for nd in net["nodes"]:
        ins = [wire_idx[src] for src in nd["in"]]
        ws = [int(w) for w in nd["w"]]
        t = int(nd["t"])
        wire_idx[nd["id"]] = len(vars_list) + len(tns)
        tns.append({"ins": ins, "ws": ws, "t": t})
    out_idx = wire_idx[net["output"]]
    if not tns or out_idx != len(vars_list) + len(tns) - 1:
        tns.append({"ins": [out_idx], "ws": [1], "t": 1})
    return tns


def _pb_to_expr_indexed(ins, ws, t):
    """Mirror Lean `Cerp.pbToExpr` pseudo-Boolean Shannon expansion over wire indices."""
    if not ins or not ws:
        return ("const", 1 if t <= 0 else 0)
    return (
        "ite",
        ("var", ins[0]),
        _pb_to_expr_indexed(ins[1:], ws[1:], t - ws[0]),
        _pb_to_expr_indexed(ins[1:], ws[1:], t),
    )


def _pb_bounds(ins, ws):
    """Mirror Lean `Cerp.pbBounds` sum range `[min_sum, max_sum]`."""
    lo, hi = 0, 0
    for _, w in zip(ins, ws):
        lo += min(w, 0)
        hi += max(w, 0)
    return lo, hi


def _add_bound(lo, hi, u, acc):
    if lo < u <= hi and u not in acc:
        return [u] + acc
    return acc


def _next_layer_ts(lo, hi, w, ts):
    acc = []
    for u in ts:
        acc = _add_bound(lo, hi, u - w, acc)
        acc = _add_bound(lo, hi, u, acc)
    return acc


def _mk_sym_ite(c_lit, th, el, nxt):
    if th[0] == "const" and el[0] == "const":
        if th[1] and el[1]:
            return ("const", True), [], nxt
        if not th[1] and not el[1]:
            return ("const", False), [], nxt
        if th[1] and not el[1]:
            return ("lit", c_lit), [], nxt
        return ("lit", -c_lit), [], nxt
    if th[0] == "const" and el[0] == "lit":
        e = el[1]
        if th[1]:
            return ("lit", nxt), [[nxt, -c_lit], [nxt, -e], [-nxt, c_lit, e]], nxt + 1
        return ("lit", nxt), [[-nxt, -c_lit], [-nxt, e], [nxt, c_lit, -e]], nxt + 1
    if th[0] == "lit" and el[0] == "const":
        t = th[1]
        if el[1]:
            return ("lit", nxt), [[nxt, c_lit], [nxt, -t], [-nxt, -c_lit, t]], nxt + 1
        return ("lit", nxt), [[-nxt, c_lit], [-nxt, t], [nxt, -c_lit, -t]], nxt + 1
    t, e = th[1], el[1]
    if t == e:
        return ("lit", t), [], nxt
    return ("lit", nxt), [[-c_lit, -nxt, t], [-c_lit, nxt, -t], [c_lit, -nxt, e], [c_lit, nxt, -e]], nxt + 1


def _lookup_sym(lo, hi, m, u):
    if u <= lo:
        return ("const", True)
    if hi < u:
        return ("const", False)
    for k, s in m:
        if k == u:
            return s
    return ("const", False)


def _build_layer(c_lit, s_lo, s_hi, w, sub_map, ts, nxt):
    my_map = []
    clauses = []
    cur = nxt
    for u in ts:
        th = _lookup_sym(s_lo, s_hi, sub_map, u - w)
        el = _lookup_sym(s_lo, s_hi, sub_map, u)
        s, c1, cur = _mk_sym_ite(c_lit, th, el, cur)
        my_map.append((u, s))
        clauses.extend(c1)
    return my_map, clauses, cur


def _pb_encode_layer(ins, ws, ts, nxt):
    if not ins or not ws:
        return [], [], nxt
    i, is_ = ins[0], ins[1:]
    w, ws_ = ws[0], ws[1:]
    s_lo, s_hi = _pb_bounds(is_, ws_)
    ts_next = _next_layer_ts(s_lo, s_hi, w, ts)
    sub_map, sub_cnf, n1 = _pb_encode_layer(is_, ws_, ts_next, nxt)
    my_map, my_cnf, n2 = _build_layer(i + 1, s_lo, s_hi, w, sub_map, ts, n1)
    return my_map, sub_cnf + my_cnf, n2


def _pb_encode_sym(ins, ws, t, nxt):
    lo, hi = _pb_bounds(ins, ws)
    if t <= lo:
        return ("const", True), [], nxt
    if hi < t:
        return ("const", False), [], nxt
    m, cnf, n1 = _pb_encode_layer(ins, ws, [t], nxt)
    return _lookup_sym(lo, hi, m, t), cnf, n1


def _wire_eq_sym(w, s):
    if s[0] == "const":
        return [[w]] if s[1] else [[-w]]
    o = s[1]
    return [[-w, o], [w, -o]]


def _lean_tnet_miter_pb(vars_list, tns, ref_body):
    """Produce the exact CNF emitted by Lean's `Cerp.tseitinTNetMiterPB`."""
    n = len(vars_list)
    m = len(tns)
    nxt = n + m + 1
    c_net = []
    o_net = 0
    for k, nd in enumerate(tns):
        s, c, nxt = _pb_encode_sym(nd["ins"], nd["ws"], nd["t"], nxt)
        w = n + k + 1
        c_net.extend(c)
        c_net.extend(_wire_eq_sym(w, s))
        o_net = w
    var_idx = {v: i for i, v in enumerate(vars_list)}
    o_spec, c_spec, nxt2 = _lean_tseitin_encode(ref_body, var_idx, nxt)
    clauses = (
        c_net
        + c_spec
        + [[-nxt2, -o_net, -o_spec], [-nxt2, o_net, o_spec], [nxt2, -o_net, o_spec], [nxt2, o_net, -o_spec], [nxt2]]
    )
    return nxt2, clauses


def _lean_tnet_miter(vars_list, tns, ref_body):
    """Produce the exact CNF emitted by Lean's `Cerp.tseitinTNetMiter`."""
    n = len(vars_list)
    m = len(tns)
    nxt = n + m + 1
    c_net = []
    o_net = 0
    for k, nd in enumerate(tns):
        pb_e = _pb_to_expr_indexed(nd["ins"], nd["ws"], nd["t"])
        o, c, nxt = _lean_tseitin_encode(pb_e, None, nxt)
        w = n + k + 1
        c_net.extend(c)
        c_net.append([-w, o])
        c_net.append([w, -o])
        o_net = w
    var_idx = {v: i for i, v in enumerate(vars_list)}
    o_spec, c_spec, nxt2 = _lean_tseitin_encode(ref_body, var_idx, nxt)
    clauses = (
        c_net
        + c_spec
        + [[-nxt2, -o_net, -o_spec], [-nxt2, o_net, o_spec], [nxt2, -o_net, o_spec], [nxt2, o_net, -o_spec], [nxt2]]
    )
    return nxt2, clauses


def prove_tnet_equivalence_lrat(net, ref_expr, vars_list, time_limit=60.0, pb=True):
    """Untrusted SAT search returning hint-indexed LRAT proof matching `Cerp.tseitinTNetMiterPB` (or `tseitinTNetMiter` when `pb=False`)."""
    tns = _tnet_to_indexed_nodes(net, vars_list)
    miter_fn = _lean_tnet_miter_pb if pb else _lean_tnet_miter
    n_vars, clauses = miter_fn(vars_list, tns, ref_expr["body"])
    s = Solver(n_vars, clauses)
    r = s.solve(time_limit)
    if r is None:
        return "timeout", None, s
    if r is False:
        return "unsat", rup_to_lrat(clauses, s.proof), s
    m = s.model()
    return "sat", {name: m[i + 1] for i, name in enumerate(vars_list)}, s
