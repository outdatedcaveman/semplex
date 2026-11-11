"""Trusted verification kernel, v0.

This is the only module whose correctness the PROVED-IN-FRAGMENT label
depends on. Design rules (enforced by tests/test_kernel_independence.py):

  * stdlib only; it must NOT import anything from the rest of `cerp`;
  * it re-implements its own tiny interpreters for every serialized
    artifact kind, so a bug in a translator or in the main interpreters
    cannot silently agree with itself;
  * it decides claims by exhaustive enumeration over a finite Boolean
    domain (n <= MAX_VARS), so for this fragment the decision procedure
    *is* the proof. It does not check succinct certificates yet (see
    experiments/SPIKE_01_REPORT.md, finding F3).

Trusted base for a PROVED-IN-FRAGMENT verdict: this file + the CPython
interpreter + the hardware. That is weaker than a proof-assistant kernel
and is recorded as such in the claims ledger.

Serialized artifact kinds (plain JSON-compatible data):

  expr     {"kind": "expr", "body": E}
           E = ["const", 0|1] | ["var", name] | ["not", E]
             | ["and"|"or"|"xor", E, E] | ["ite", E, E, E]
  circuit  {"kind": "circuit", "body": {"inputs": [names],
            "gates": [{"id": str, "op": op, "in": [refs]}...], "output": ref}}
           op in and/or/xor (2 inputs), not (1), const0/const1 (0).
           Gates must be topologically ordered; refs are inputs or earlier ids.
  dfa      {"kind": "dfa", "body": {"order": [names], "start": s,
            "delta": {s: [s_on_0, s_on_1]}, "accept": [states]}}
           Reads exactly len(order) bits in `order`; accepts -> 1.
  bdd      {"kind": "bdd", "body": {"order": [names],
            "nodes": [[level, lo, hi], ...], "root": int}}
           Node 0 is FALSE, node 1 is TRUE (their entries are ignored).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

KERNEL_VERSION = "0.4.0"
MAX_VARS = 16

_TOKEN = object()  # only this module can mint verdicts


class KernelError(Exception):
    """Malformed artifact or claim. Never a verdict."""


@dataclass(frozen=True)
class Verdict:
    ok: bool
    relation: str
    vars: tuple
    points_checked: int
    counterexample: dict | None
    kernel_version: str
    _token: object = None

    def __post_init__(self):
        if self._token is not _TOKEN:
            raise KernelError("Verdicts can only be issued by the kernel")

    @property
    def authentic(self) -> bool:
        return self._token is _TOKEN


# ---------------------------------------------------------------- evaluators

def _bit(v):
    if v not in (0, 1):
        raise KernelError(f"non-Boolean value {v!r}")
    return v


def _eval_expr(e, env):
    op = e[0]
    if op == "const":
        return _bit(e[1])
    if op == "var":
        return env[e[1]]
    if op == "not":
        return 1 - _eval_expr(e[1], env)
    if op == "and":
        return _eval_expr(e[1], env) & _eval_expr(e[2], env)
    if op == "or":
        return _eval_expr(e[1], env) | _eval_expr(e[2], env)
    if op == "xor":
        return _eval_expr(e[1], env) ^ _eval_expr(e[2], env)
    if op == "ite":
        return _eval_expr(e[2], env) if _eval_expr(e[1], env) else _eval_expr(e[3], env)
    raise KernelError(f"unknown expr op {op!r}")


_ARITY = {"and": 2, "or": 2, "xor": 2, "not": 1, "const0": 0, "const1": 0}


def _eval_circuit(c, env):
    val = {}
    for name in c["inputs"]:
        val[name] = env[name]
    for g in c["gates"]:
        op, ins = g["op"], g["in"]
        if op not in _ARITY or len(ins) != _ARITY[op]:
            raise KernelError(f"bad gate {g!r}")
        if g["id"] in val:
            raise KernelError(f"duplicate id {g['id']!r}")
        a = [val[r] for r in ins]  # KeyError => not topologically ordered
        val[g["id"]] = {
            "and": lambda: a[0] & a[1],
            "or": lambda: a[0] | a[1],
            "xor": lambda: a[0] ^ a[1],
            "not": lambda: 1 - a[0],
            "const0": lambda: 0,
            "const1": lambda: 1,
        }[op]()
    return val[c["output"]]


def _eval_dfa(d, env):
    s = d["start"]
    for name in d["order"]:
        s = d["delta"][s][env[name]]
    return 1 if s in set(d["accept"]) else 0


def _eval_bdd(b, env):
    nodes, order = b["nodes"], b["order"]
    i = b["root"]
    steps = 0
    while i not in (0, 1):
        level, lo, hi = nodes[i]
        i = hi if env[order[level]] else lo
        steps += 1
        if steps > len(nodes):
            raise KernelError("cyclic BDD")
    return i


def _eval_tnet(b, env):
    """Strictly layered threshold network (spike 08):
    {"inputs": [names], "layers": [[{"w": [ints], "t": int}, ...], ...]}
    A neuron outputs 1 iff sum(w_i * in_i) >= t; it reads only the previous
    layer; the last layer must hold exactly one neuron."""
    vals = [env[n] for n in b["inputs"]]
    layers = b["layers"]
    if not layers or len(layers[-1]) != 1:
        raise KernelError("tnet needs a final layer with exactly one neuron")
    for layer in layers:
        nxt = []
        for nrn in layer:
            w, t = nrn["w"], nrn["t"]
            if len(w) != len(vals) or not all(type(v) is int for v in w) or type(t) is not int:
                raise KernelError("bad neuron")
            nxt.append(1 if sum(a * v for a, v in zip(w, vals)) >= t else 0)
        vals = nxt
    return vals[0]


def _eval_table(b, env):
    """Explicit truth table: {"order": [names], "bits": int}; the value at
    assignment x is bit number sum(x_j << j) of `bits`."""
    order, bits = b["order"], b["bits"]
    if type(bits) is not int or not 0 <= bits < (1 << (1 << len(order))):
        raise KernelError("bad table")
    return (bits >> sum(env[n] << j for j, n in enumerate(order))) & 1


def _eval_dnet(b, env):
    """General feedforward net (spike 08b): skip connections and ReLU allowed.
    {"inputs": [names], "neurons": [{"in": [refs], "w": [ints], "b": int, "act": "step"|"relu"}]}
    Values are indexed inputs first, then neurons in order; a neuron may read
    any EARLIER value. pre = sum(w * value) + b; step -> [pre >= 0];
    relu -> max(0, pre). The output is the last neuron, which must be a step."""
    vals = [env[n] for n in b["inputs"]]
    ns = b["neurons"]
    if not ns or ns[-1]["act"] != "step":
        raise KernelError("dnet must end in a step neuron")
    for nrn in ns:
        refs, w, bias, act = nrn["in"], nrn["w"], nrn["b"], nrn["act"]
        if (len(refs) != len(w) or type(bias) is not int or not all(type(v) is int for v in w)
                or not all(type(r) is int and 0 <= r < len(vals) for r in refs)):
            raise KernelError("bad neuron")
        pre = sum(a * vals[r] for a, r in zip(w, refs)) + bias
        if act == "step":
            vals.append(1 if pre >= 0 else 0)
        elif act == "relu":
            vals.append(pre if pre > 0 else 0)
        else:
            raise KernelError(f"unknown activation {act!r}")
    return vals[-1]


_EVAL = {"expr": _eval_expr, "circuit": _eval_circuit, "dfa": _eval_dfa, "bdd": _eval_bdd,
         "tnet": _eval_tnet, "table": _eval_table, "dnet": _eval_dnet}


def evaluate(artifact, env):
    try:
        return _EVAL[artifact["kind"]](artifact["body"], env)
    except KernelError:
        raise
    except (KeyError, IndexError, TypeError) as exc:
        raise KernelError(f"malformed {artifact.get('kind')!r} artifact: {exc!r}") from exc


# ---------------------------------------------------------------- deciding

RELATIONS = ("extensional", "task")


def check(claim) -> Verdict:
    """Decide a claim by exhaustive enumeration.

    claim = {"relation": "extensional" | "task",
             "vars": [names],             # the declared finite domain {0,1}^vars
             "left": artifact, "right": artifact,
             "care": artifact}            # required iff relation == "task"

    extensional: for all x in {0,1}^vars: left(x) == right(x)
    task:        for all x with care(x) == 1: left(x) == right(x)
    """
    rel = claim.get("relation")
    if rel not in RELATIONS:
        raise KernelError(f"unknown relation {rel!r}")
    names = tuple(claim["vars"])
    if len(set(names)) != len(names):
        raise KernelError("duplicate variable names")
    if len(names) > MAX_VARS:
        raise KernelError(f"domain too large for exhaustive kernel: {len(names)} > {MAX_VARS}")
    care = claim.get("care")
    if (rel == "task") != (care is not None):
        raise KernelError("'care' is required for, and only for, relation 'task'")

    checked = 0
    for bits in product((0, 1), repeat=len(names)):
        env = dict(zip(names, bits))
        if care is not None and evaluate(care, env) == 0:
            continue
        checked += 1
        lv, rv = evaluate(claim["left"], env), evaluate(claim["right"], env)
        if lv != rv:
            return Verdict(False, rel, names, checked, dict(env), KERNEL_VERSION, _TOKEN)
    return Verdict(True, rel, names, checked, None, KERNEL_VERSION, _TOKEN)


def check_insufficiency(claim) -> Verdict:
    """Check a succinct certificate that a variable subset is NOT sufficient.

    claim = {"vars": [names], "f": artifact, "care": artifact,
             "subset": [names], "x": {name: bit}, "y": {name: bit}}

    ok iff x and y are total assignments over vars, both in care, agree on
    every variable of subset, and f(x) != f(y). Cost: two evaluations,
    independent of domain size -- unlike `check`, this scales.
    """
    names = tuple(claim["vars"])
    x, y = claim["x"], claim["y"]
    subset = set(claim["subset"])
    if not subset <= set(names):
        raise KernelError("subset not within vars")
    for a in (x, y):
        if set(a) != set(names):
            raise KernelError("witness must assign exactly the declared vars")
        for v in a.values():
            _bit(v)
    ok = (
        evaluate(claim["care"], x) == 1
        and evaluate(claim["care"], y) == 1
        and all(x[v] == y[v] for v in subset)
        and evaluate(claim["f"], x) != evaluate(claim["f"], y)
    )
    return Verdict(ok, "insufficient", names, 2, None, KERNEL_VERSION, _TOKEN)


# ---------------------------------------------------------------- spike 03
# Proof-carrying equivalence beyond the exhaustive wall.
#
# The kernel itself builds the miter CNF from the claim (Tseitin encoding
# below), so an untrusted encoder cannot substitute a different formula.
# An untrusted SAT solver may then supply a RUP certificate: a list of
# lemmas, each of which must follow from the formula plus earlier lemmas by
# unit propagation alone, ending with the empty clause. Checking needs only
# unit propagation -- far simpler than the search that found the lemmas.

MAX_RUP_VARS = 200_000


def _tseitin(art, var_of, fresh, out):
    """Encode artifact (expr or circuit); return the literal of its output."""
    kind, body = art["kind"], art["body"]

    def gate(op, ins):
        z = fresh()
        if op == "and":
            a, b = ins
            out.extend([[-z, a], [-z, b], [z, -a, -b]])
        elif op == "or":
            a, b = ins
            out.extend([[z, -a], [z, -b], [-z, a, b]])
        elif op == "xor":
            a, b = ins
            out.extend([[-z, a, b], [-z, -a, -b], [z, -a, b], [z, a, -b]])
        elif op == "not":
            (a,) = ins
            out.extend([[z, a], [-z, -a]])
        elif op == "ite":
            c, t, e = ins
            out.extend([[-c, -t, z], [-c, t, -z], [c, -e, z], [c, e, -z]])
        elif op in ("const0", "const1"):
            out.append([z] if op == "const1" else [-z])
        else:
            raise KernelError(f"unknown op {op!r}")
        return z

    if kind == "expr":
        def go(e):
            op = e[0]
            if op == "var":
                return var_of[e[1]]
            if op == "const":
                return gate("const1" if _bit(e[1]) else "const0", [])
            return gate(op, [go(x) for x in e[1:]])
        return go(body)
    if kind == "circuit":
        lit = {name: var_of[name] for name in body["inputs"]}
        for g in body["gates"]:
            if g["op"] not in _ARITY or len(g["in"]) != _ARITY[g["op"]]:
                raise KernelError(f"bad gate {g!r}")
            if g["id"] in lit:
                raise KernelError(f"duplicate id {g['id']!r}")
            lit[g["id"]] = gate(g["op"], [lit[r] for r in g["in"]])
        return lit[body["output"]]
    raise KernelError(f"RUP route supports expr and circuit artifacts, not {kind!r}")


def miter_cnf(claim):
    """(n_vars, clauses) satisfiable  <=>  left and right differ somewhere in care.
    Inputs are variables 1..n in the declared order. Public so untrusted
    solvers can work on exactly the formula the kernel will check."""
    names = tuple(claim["vars"])
    if len(set(names)) != len(names):
        raise KernelError("duplicate variable names")
    var_of = {v: i + 1 for i, v in enumerate(names)}
    counter = [len(names)]
    clauses = []

    def fresh():
        counter[0] += 1
        if counter[0] > MAX_RUP_VARS:
            raise KernelError("formula too large for the RUP kernel")
        return counter[0]

    try:
        lo = _tseitin(claim["left"], var_of, fresh, clauses)
        ro = _tseitin(claim["right"], var_of, fresh, clauses)
        m = fresh()
        clauses += [[-m, lo, ro], [-m, -lo, -ro], [m, -lo, ro], [m, lo, -ro], [m]]
        if claim.get("care") is not None:
            clauses.append([_tseitin(claim["care"], var_of, fresh, clauses)])
    except KeyError as exc:
        raise KernelError(f"undeclared variable or dangling reference {exc}") from exc
    return counter[0], clauses


def _rup_refutes(clauses, lemmas):
    db, watches, units = [], {}, []

    def add(c):
        c = list(dict.fromkeys(c))
        if any(-l in c for l in c):
            return  # tautology: always satisfied, adds nothing
        if not c:
            db.append(c)
        elif len(c) == 1:
            units.append(c[0])
        else:
            idx = len(db)
            db.append(c)
            watches.setdefault(c[0], []).append(idx)
            watches.setdefault(c[1], []).append(idx)

    def conflict_under(assumptions):
        if any(not c for c in db):
            return True
        val = {}

        def value(l):  # True / False / None
            v = val.get(abs(l))
            return None if v is None else (v if l > 0 else not v)

        trail = []
        for l in list(assumptions) + units:
            x = value(l)
            if x is False:
                return True
            if x is None:
                val[abs(l)] = l > 0
                trail.append(l)
        i = 0
        while i < len(trail):
            false_lit = -trail[i]
            i += 1
            ws = watches.get(false_lit, [])
            j = 0
            while j < len(ws):
                c = db[ws[j]]
                if c[0] == false_lit:
                    c[0], c[1] = c[1], c[0]
                if value(c[0]) is True:
                    j += 1
                    continue
                for k in range(2, len(c)):
                    if value(c[k]) is not False:
                        c[1], c[k] = c[k], c[1]
                        watches.setdefault(c[1], []).append(ws[j])
                        ws[j] = ws[-1]
                        ws.pop()
                        break
                else:
                    first = value(c[0])
                    if first is False:
                        return True
                    if first is None:
                        val[abs(c[0])] = c[0] > 0
                        trail.append(c[0])
                    j += 1
        return False

    for c in clauses:
        add(c)
    for n, lemma in enumerate(lemmas):
        if not conflict_under([-l for l in lemma]):
            return False, n
        add(lemma)
        if not lemma:
            return True, n + 1
    return False, len(lemmas)


def check_rup(claim) -> Verdict:
    """Equivalence (or task-equivalence, with 'care') of two expr/circuit
    artifacts, certified by claim['certificate'] = list of RUP lemmas.
    ok => the miter is unsatisfiable => left == right on every care point."""
    n, clauses = miter_cnf(claim)
    lemmas = claim["certificate"]
    for lem in lemmas:
        for l in lem:
            if not isinstance(l, int) or l == 0 or abs(l) > n:
                raise KernelError("certificate literal out of range")
    ok, checked = _rup_refutes(clauses, lemmas)
    return Verdict(ok, "rup", tuple(claim["vars"]), checked, None, KERNEL_VERSION, _TOKEN)


def check_counterexample(claim) -> Verdict:
    """ok iff the given total assignment is in care and left != right there.
    Two evaluations at any domain size: a succinct certificate of NON-equivalence."""
    names = tuple(claim["vars"])
    x = claim["x"]
    if set(x) != set(names):
        raise KernelError("witness must assign exactly the declared vars")
    for v in x.values():
        _bit(v)
    care = claim.get("care")
    ok = (care is None or evaluate(care, x) == 1) and evaluate(claim["left"], x) != evaluate(claim["right"], x)
    return Verdict(ok, "counterexample", names, 2, dict(x) if ok else None, KERNEL_VERSION, _TOKEN)
