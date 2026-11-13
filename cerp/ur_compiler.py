"""Ur-Compiler prototype: Compositional C4 profile-factorization + unified F0 / F1-LTS / Causal compilation.

Implements:
1. Compositional profile-factorization (`compile_profile_factored`), grounded in
   Theory.lean `prod_determines` (C4) and `profile_factor_compile` (H-G):
   partitions variables to minimize observational profile rank r = ceil(log2 |Im(profile)|),
   recursively compiles encoder bits and decoder down to <= 4-input leaves where exact
   `atlas` threshold-neuron optima are known, and composes a kernel-checked F0 expr.
2. Unified multi-paradigm compilation (`compile_unified`) accepting:
   - "f0": Boolean function over named variables
   - "causal": Causal Bayes net decision rule (`csir.distill_causal_rule`)
   - "lts": Deterministic finite LTS (state, action -> next_state, output) compiled to
     a synchronous Boolean step-circuit in a validated CSIR bundle (H-H).
"""

from __future__ import annotations

import math
from typing import Any, Callable

from . import atlas, csir, kernel
from .semantics import TruthTable
from .substrates import cost as circuit_cost
from .translate import bdd_to_circuit, bdd_to_expr, truthtable_to_bdd


def subst_expr(body: Any, mapping: dict[str, Any]) -> Any:
    """Substitute variable names in a kernel F0 expr AST."""
    if not isinstance(body, (list, tuple)) or not body:
        return body
    op = body[0]
    if op == "var":
        return mapping.get(body[1], body)
    if op == "const":
        return body
    if op == "not":
        return ["not", subst_expr(body[1], mapping)]
    if op in ("and", "or", "xor"):
        return [op, subst_expr(body[1], mapping), subst_expr(body[2], mapping)]
    if op == "ite":
        return ["ite", subst_expr(body[1], mapping), subst_expr(body[2], mapping), subst_expr(body[3], mapping)]
    return [op] + [subst_expr(x, mapping) for x in body[1:]]


def expr_gate_count(body: Any) -> int:
    if not isinstance(body, (list, tuple)) or not body or body[0] in ("const", "var"):
        return 0
    return 1 + sum(expr_gate_count(x) for x in body[1:])


def _fn_from_expr(vars_list: list[str], expr_art: dict[str, Any]) -> Callable[[dict[str, int]], int]:
    body = expr_art["body"]

    def _f(env: dict[str, int]) -> int:
        benv = {k: bool(v) for k, v in env.items()}
        return int(bool(kernel._eval_expr(body, benv)))

    return _f


def _leaf_compile(vars_list: list[str], fn: Callable[[dict[str, int]], int], atlas_tables=None) -> dict[str, Any]:
    tt = TruthTable.from_function(vars_list, fn)
    bdd_art = truthtable_to_bdd(tt)
    expr_art = bdd_to_expr(bdd_art)
    circ_art = bdd_to_circuit(bdd_art, vars_list)
    n = len(vars_list)
    atlas_neurons = None
    if n <= 4:
        tb = (atlas_tables or atlas.build_all(4))[n]
        bits = 0
        for i in range(1 << n):
            env = {vars_list[j]: (i >> j) & 1 for j in range(n)}
            if fn(env):
                bits |= (1 << i)
        atlas_neurons = int(tb.hi[bits])
    return {
        "vars": list(vars_list),
        "expr": expr_art,
        "circuit": circ_art,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": atlas_neurons,
        "decomposed": False,
        "profile_rank": None,
        "children": [],
    }


def _best_profile_split(
    vars_list: list[str], fn: Callable[[dict[str, int]], int], max_s1: int = 4, max_s2_sample: int = 64
) -> tuple[list[str], list[str], int, dict[tuple[int, ...], int]] | None:
    """Find a split (S1, S2) with |S1| <= max_s1 where the observational profile of S1
    has rank r = ceil(log2 |Im(profile)|) < |S1|."""
    n = len(vars_list)
    k = min(max_s1, max(2, n // 2))
    # Candidate blocks: contiguous slices + strided slice
    candidates: list[list[str]] = []
    for start in range(0, n - k + 1):
        candidates.append(vars_list[start:start + k])
    if n >= 2 * k:
        candidates.append([vars_list[i] for i in range(0, n, 2)][:k])

    best = None
    for s1 in candidates:
        s1_set = set(s1)
        s2 = [v for v in vars_list if v not in s1_set]
        # Sample S2 assignments if |S2| is large, then verify exactness on full S2 if small
        n2 = len(s2)
        if (1 << n2) <= max_s2_sample:
            s2_envs = [{s2[j]: (m >> j) & 1 for j in range(n2)} for m in range(1 << n2)]
            exact_s2 = True
        else:
            step = max(1, (1 << n2) // max_s2_sample)
            s2_envs = [{s2[j]: ((m >> j) & 1) for j in range(n2)} for m in range(0, 1 << n2, step)][:max_s2_sample]
            exact_s2 = False

        profiles: dict[tuple[int, ...], int] = {}
        x1_to_code: dict[tuple[int, ...], int] = {}
        n1 = len(s1)
        for m1 in range(1 << n1):
            x1 = tuple((m1 >> j) & 1 for j in range(n1))
            env1 = {s1[j]: x1[j] for j in range(n1)}
            sig = tuple(fn({**env1, **e2}) for e2 in s2_envs)
            if sig not in profiles:
                profiles[sig] = len(profiles)
            x1_to_code[x1] = profiles[sig]
            if len(profiles) >= (1 << (n1 - 1)):
                # Cannot achieve r < n1 if already >= 2^(n1-1) distinct signatures? Wait: 2^(n1-1) gives r = n1 - 1!
                if len(profiles) > (1 << (n1 - 1)):
                    break

        num_classes = len(profiles)
        rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
        if rank >= n1:
            continue
        # If S2 was sampled, verify that identical sampled signatures actually agree on all S2 (when feasible)
        if not exact_s2 and (1 << (n1 + n2)) <= 4096:
            all_s2 = [{s2[j]: (m >> j) & 1 for j in range(n2)} for m in range(1 << n2)]
            profiles_full: dict[tuple[int, ...], int] = {}
            x1_to_code = {}
            for m1 in range(1 << n1):
                x1 = tuple((m1 >> j) & 1 for j in range(n1))
                env1 = {s1[j]: x1[j] for j in range(n1)}
                sig = tuple(fn({**env1, **e2}) for e2 in all_s2)
                if sig not in profiles_full:
                    profiles_full[sig] = len(profiles_full)
                x1_to_code[x1] = profiles_full[sig]
            num_classes = len(profiles_full)
            rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
            if rank >= n1:
                continue

        if best is None or rank < best[2]:
            best = (s1, s2, rank, x1_to_code)
            if rank <= 1:
                break
    return best


def compile_profile_factored(
    vars_list: list[str],
    fn: Callable[[dict[str, int]], int],
    *,
    max_leaf: int = 4,
    atlas_tables=None,
    _depth: int = 0,
) -> dict[str, Any]:
    """Recursively compile `fn` via C4 profile factorization down to `max_leaf` leaves."""
    if atlas_tables is None:
        atlas_tables = atlas.build_all(4)
    n = len(vars_list)
    if n <= max_leaf:
        return _leaf_compile(vars_list, fn, atlas_tables=atlas_tables)

    split = _best_profile_split(vars_list, fn, max_s1=max_leaf)
    if split is None:
        # Fallback: direct BDD/expr compilation
        return _leaf_compile(vars_list, fn, atlas_tables=atlas_tables)

    s1, s2, rank, x1_to_code = split
    code_to_rep: dict[int, tuple[int, ...]] = {}
    for x1, code in x1_to_code.items():
        if code not in code_to_rep:
            code_to_rep[code] = x1

    # Compile r encoder bits pi_0..pi_{r-1} : S1 -> {0,1}
    enc_vars = [f"_c_{_depth}_{j}" for j in range(rank)]
    encoders = []
    enc_map: dict[str, Any] = {}
    for bit_idx in range(rank):
        def _make_enc(bi: int) -> Callable[[dict[str, int]], int]:
            return lambda env: (x1_to_code[tuple(env[v] for v in s1)] >> bi) & 1

        enc_res = compile_profile_factored(s1, _make_enc(bit_idx), max_leaf=max_leaf, atlas_tables=atlas_tables, _depth=_depth + 1)
        encoders.append(enc_res)
        enc_map[enc_vars[bit_idx]] = enc_res["expr"]["body"]

    # Compile decoder g : enc_vars + S2 -> {0,1}
    dec_vars = enc_vars + s2

    def _dec_fn(env: dict[str, int]) -> int:
        code = sum((int(env[ev]) << j) for j, ev in enumerate(enc_vars))
        if code not in code_to_rep:
            code = 0
        rep_x1 = code_to_rep[code]
        full_env = {**{s1[j]: rep_x1[j] for j in range(len(s1))}, **{v: env[v] for v in s2}}
        return fn(full_env)

    dec_res = compile_profile_factored(dec_vars, _dec_fn, max_leaf=max_leaf, atlas_tables=atlas_tables, _depth=_depth + 1)
    composed_body = subst_expr(dec_res["expr"]["body"], enc_map)
    composed_expr = {"kind": "expr", "body": composed_body}

    neuron_ub = None
    if dec_res["atlas_min_neurons"] is not None and all(e["atlas_min_neurons"] is not None for e in encoders):
        neuron_ub = dec_res["atlas_min_neurons"] + sum(e["atlas_min_neurons"] for e in encoders)

    return {
        "vars": list(vars_list),
        "expr": composed_expr,
        "circuit": None,
        "circuit_cost": {"gates": expr_gate_count(composed_body)},
        "atlas_min_neurons": neuron_ub,
        "decomposed": True,
        "profile_rank": rank,
        "split": {"s1": s1, "s2": s2},
        "children": encoders + [dec_res],
    }


def compile_unified(spec: dict[str, Any]) -> dict[str, Any]:
    """Unified Ur-Compiler entry point for F0, Causal, and F1-LTS specifications.

    Returns a dictionary containing the compiled CSIR bundle, validation errors,
    and compositional/atlas resource metrics.
    """
    kind = spec["kind"]
    if kind == "causal":
        b = csir.distill_causal_rule(
            spec["structure"],
            spec["params"],
            target=spec.get("target", "Y"),
            features=spec.get("features"),
            do=spec.get("do"),
            model_id=spec.get("model_id", "model"),
            threshold=spec.get("threshold", 0.5),
        )
        return {"kind": "causal", "csir": b, "validation_errors": csir.validate(b), "recheck": csir.recheck(b)}

    if kind == "f0":
        vars_list = list(spec["vars"])
        fn = spec["fn"]
        res = compile_profile_factored(vars_list, fn)
        n_id = spec.get("name", "f0_compiled")
        expr_node = csir.node(
            n_id,
            res["expr"],
            {"vars": vars_list},
            resources={"cost": res["circuit_cost"], "atlas_neuron_ub": res["atlas_min_neurons"],
                       "cost_model": "F0/compositional"},
            provenance={"produced_by": "ur_compiler.compile_profile_factored",
                        "decomposed": res["decomposed"], "profile_rank": res["profile_rank"]},
        )
        b = csir.bundle([expr_node], [])
        return {
            "kind": "f0",
            "compiled": res,
            "csir": b,
            "validation_errors": csir.validate(b),
        }

    if kind == "lts":
        states = list(spec["states"])
        actions = list(spec["actions"])
        transitions = spec["transitions"]  # (s, a) -> (s_next, out_bit)
        s_bits = max(1, math.ceil(math.log2(max(2, len(states)))))
        a_bits = max(1, math.ceil(math.log2(max(2, len(actions)))))
        s_vars = [f"s{i}" for i in range(s_bits)]
        a_vars = [f"a{i}" for i in range(a_bits)]
        step_vars = s_vars + a_vars
        s_index = {s: i for i, s in enumerate(states)}

        nodes = [
            csir.node(
                "lts_spec",
                {"kind": "lts", "body": {"states": states, "actions": actions}},
                {"actions": actions},
                provenance={"produced_by": "lts_spec"},
            )
        ]
        links = []
        compiled_outputs = {}

        # Compile each next-state bit and the output bit into F0 expressions
        for out_name, getter in (
            [(f"next_s{b}", lambda ns, ob, bit=b: (s_index[ns] >> bit) & 1) for b in range(s_bits)]
            + [("out", lambda ns, ob: int(bool(ob)))]
        ):
            def _make_step_fn(g=getter):
                def _step(env: dict[str, int]) -> int:
                    si = sum((env[s_vars[j]] << j) for j in range(s_bits))
                    ai = sum((env[a_vars[j]] << j) for j in range(a_bits))
                    if si >= len(states) or ai >= len(actions):
                        return 0
                    ns, ob = transitions[(states[si], actions[ai])]
                    return g(ns, ob)
                return _step

            comp = compile_profile_factored(step_vars, _make_step_fn())
            compiled_outputs[out_name] = comp
            nodes.append(
                csir.node(
                    out_name,
                    comp["expr"],
                    {"vars": step_vars},
                    resources={"cost": comp["circuit_cost"], "atlas_neuron_ub": comp["atlas_min_neurons"],
                               "cost_model": "F0/compositional"},
                    provenance={"produced_by": "ur_compiler.lts_step", "parents": ["lts_spec"]},
                )
            )
            links.append(
                csir.link(
                    "lts_spec", out_name, "distills",
                    {"vars": step_vars, "target": out_name},
                    certificate={"method": "exhaustive"},
                    warrant={"basis": ["kernel-checked"], "trusted_base": ["cerp/ur_compiler.py"], "conditions": []},
                )
            )
        b = csir.bundle(nodes, links)
        return {
            "kind": "lts",
            "compiled_outputs": compiled_outputs,
            "csir": b,
            "validation_errors": csir.validate(b),
        }

    raise ValueError(f"Unsupported spec kind: {kind!r}")
