"""Three computational substrates for fragment F0 (charter §11.1):

  expr     a restricted functional language (nested lists, see kernel docs)
  circuit  a Boolean gate netlist (DAG)
  dfa      a deterministic finite automaton reading the inputs serially

All artifacts are plain JSON-compatible dicts {"kind", "body"} so the same
object can be handed to the independent kernel. This module provides the
main interpreters, cost models and random generators.
"""

from __future__ import annotations

import random

from .semantics import TruthTable

# ---------------------------------------------------------------- expr

def evaluate_expr(e, env):
    op = e[0]
    if op == "const":
        return e[1]
    if op == "var":
        return env[e[1]]
    if op == "not":
        return 1 ^ evaluate_expr(e[1], env)
    a = evaluate_expr(e[1], env)
    if op == "and":
        return a and evaluate_expr(e[2], env)
    if op == "or":
        return a or evaluate_expr(e[2], env)
    if op == "xor":
        return a ^ evaluate_expr(e[2], env)
    if op == "ite":
        return evaluate_expr(e[2], env) if a else evaluate_expr(e[3], env)
    raise ValueError(op)


def expr_size(e) -> int:
    if e[0] in ("const", "var"):
        return 1
    return 1 + sum(expr_size(c) for c in e[1:])


def expr_depth(e) -> int:
    if e[0] in ("const", "var"):
        return 0
    return 1 + max(expr_depth(c) for c in e[1:])


def expr_vars(e) -> set:
    if e[0] == "var":
        return {e[1]}
    if e[0] == "const":
        return set()
    return set().union(*(expr_vars(c) for c in e[1:]))


def pretty(e) -> str:
    op = e[0]
    if op == "const":
        return str(e[1])
    if op == "var":
        return e[1]
    if op == "not":
        return "~" + pretty(e[1])
    if op == "ite":
        return f"({pretty(e[1])} ? {pretty(e[2])} : {pretty(e[3])})"
    sym = {"and": "&", "or": "|", "xor": "^"}[op]
    return f"({pretty(e[1])} {sym} {pretty(e[2])})"


def random_expr(vars, depth: int, rng: random.Random):
    if depth == 0 or rng.random() < 0.15:
        if rng.random() < 0.05:
            return ["const", rng.randint(0, 1)]
        return ["var", rng.choice(vars)]
    op = rng.choice(["and", "or", "xor", "not", "and", "or", "ite"])
    if op == "not":
        return ["not", random_expr(vars, depth - 1, rng)]
    if op == "ite":
        return ["ite"] + [random_expr(vars, depth - 1, rng) for _ in range(3)]
    return [op, random_expr(vars, depth - 1, rng), random_expr(vars, depth - 1, rng)]


# ---------------------------------------------------------------- circuit

def evaluate_circuit(c, env):
    val = dict((k, env[k]) for k in c["inputs"])
    for g in c["gates"]:
        a = [val[r] for r in g["in"]]
        op = g["op"]
        val[g["id"]] = (
            a[0] & a[1] if op == "and" else
            a[0] | a[1] if op == "or" else
            a[0] ^ a[1] if op == "xor" else
            1 - a[0] if op == "not" else
            0 if op == "const0" else 1
        )
    return val[c["output"]]


def circuit_cost(c) -> dict:
    depth = {k: 0 for k in c["inputs"]}
    for g in c["gates"]:
        depth[g["id"]] = 1 + max((depth[r] for r in g["in"]), default=0) if g["op"] not in ("const0", "const1") else 0
    live = _live_gates(c)
    return {"gates": len(live), "depth": depth.get(c["output"], 0)}


def _live_gates(c):
    by_id = {g["id"]: g for g in c["gates"]}
    seen, stack = set(), [c["output"]]
    while stack:
        r = stack.pop()
        if r in by_id and r not in seen:
            seen.add(r)
            stack.extend(by_id[r]["in"])
    return seen


class CircuitBuilder:
    """Hash-consing netlist builder (structural sharing = CSE)."""

    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.gates = []
        self._memo = {}

    def gate(self, op, *ins):
        if op in ("and", "or", "xor"):
            ins = tuple(sorted(ins))  # commutative
        key = (op, ins)
        if key not in self._memo:
            gid = f"g{len(self.gates)}"
            self.gates.append({"id": gid, "op": op, "in": list(ins)})
            self._memo[key] = gid
        return self._memo[key]

    def build(self, output):
        c = {"inputs": self.inputs, "gates": self.gates, "output": output}
        # drop dead gates for a tidy artifact
        live = _live_gates(c)
        c["gates"] = [g for g in self.gates if g["id"] in live]
        return {"kind": "circuit", "body": c}


# ---------------------------------------------------------------- dfa

def evaluate_dfa(d, env):
    s = d["start"]
    for name in d["order"]:
        s = d["delta"][s][env[name]]
    return 1 if s in d["accept"] else 0


def dfa_cost(d) -> dict:
    states = set(d["delta"]) | {t for ts in d["delta"].values() for t in ts} | {d["start"]}
    return {"states": len(states), "transitions": 2 * len(d["delta"])}


# ---------------------------------------------------------------- dispatch

def evaluate(artifact, env):
    kind, body = artifact["kind"], artifact["body"]
    if kind == "expr":
        return evaluate_expr(body, env)
    if kind == "circuit":
        return evaluate_circuit(body, env)
    if kind == "dfa":
        return evaluate_dfa(body, env)
    if kind == "bdd":
        from .bdd import evaluate_bdd
        return evaluate_bdd(body, env)
    raise ValueError(kind)


def semantics(artifact, vars) -> TruthTable:
    """[[artifact]] over the declared variable order (main interpreter)."""
    return TruthTable.from_function(vars, lambda env: evaluate(artifact, env))


def cost(artifact) -> dict:
    kind, body = artifact["kind"], artifact["body"]
    if kind == "expr":
        return {"ast_nodes": expr_size(body), "depth": expr_depth(body)}
    if kind == "circuit":
        return circuit_cost(body)
    if kind == "dfa":
        return dfa_cost(body)
    if kind == "bdd":
        return {"bdd_nodes": len(body["nodes"]) - 2}
    raise ValueError(kind)
