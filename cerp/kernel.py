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

KERNEL_VERSION = "0.1.0"
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


_EVAL = {"expr": _eval_expr, "circuit": _eval_circuit, "dfa": _eval_dfa, "bdd": _eval_bdd}


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
