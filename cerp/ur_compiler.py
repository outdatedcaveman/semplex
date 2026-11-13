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

import numpy as np

from . import atlas, csir, kernel
from .semantics import TruthTable
from .substrates import CircuitBuilder, cost as circuit_cost
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


def _expr_key(body: Any) -> Any:
    if isinstance(body, list):
        return tuple(_expr_key(x) for x in body)
    return body


def _expr_to_dag_circuit(body: Any, inputs: list[str]) -> dict[str, Any]:
    """Compile an F0 expr AST into a hash-consed DAG Circuit artifact."""
    cb = CircuitBuilder(inputs)
    memo: dict[Any, str] = {}

    def _emit(node: Any) -> str:
        k = _expr_key(node)
        if k in memo:
            return memo[k]
        op = node[0]
        if op == "const":
            res = cb.gate("const1" if int(node[1]) else "const0")
        elif op == "var":
            res = str(node[1])
        elif op == "not":
            res = cb.gate("not", _emit(node[1]))
        elif op in ("and", "or", "xor"):
            res = cb.gate(op, _emit(node[1]), _emit(node[2]))
        elif op == "ite":
            cv = _emit(node[1])
            tv = _emit(node[2])
            ev = _emit(node[3])
            res = cb.gate("or", cb.gate("and", cv, tv), cb.gate("and", cb.gate("not", cv), ev))
        else:
            raise ValueError(f"Unsupported expr op for DAG circuit: {op!r}")
        memo[k] = res
        return res

    out = _emit(body)
    return cb.build(out)


def _table_from_fn(vars_list: list[str], fn: Callable[[dict[str, int]], int]) -> np.ndarray:
    """Evaluate `fn` into a flat uint8 array of length 2^n in TruthTable (MSB-first) order."""
    n = len(vars_list)
    size = 1 << n
    out = np.empty(size, dtype=np.uint8)
    env: dict[str, int] = {}
    for i in range(size):
        for j in range(n):
            env[vars_list[j]] = (i >> (n - 1 - j)) & 1
        out[i] = 1 if fn(env) else 0
    return out


def _truthtable_from_array(vars_list: list[str], table_arr: np.ndarray) -> TruthTable:
    bits = 0
    for i in np.flatnonzero(table_arr):
        bits |= 1 << int(i)
    return TruthTable(tuple(vars_list), bits)


_ATLAS_CACHE: dict[int, Any] = {}


def _get_atlas_tables(m_max: int = 4):
    if m_max not in _ATLAS_CACHE:
        _ATLAS_CACHE[m_max] = atlas.build_all(m_max)
    return _ATLAS_CACHE[m_max]


def _atlas_min_for_table(n: int, table_arr: np.ndarray, atlas_tables=None) -> tuple[int | None, int | None]:
    if n > 4 or n < 1:
        return None, None
    tb = (atlas_tables or _get_atlas_tables(4))[n]
    # Atlas indexes assignments with var[0] as LSB (Fortran order), TruthTable uses MSB-first (C order)
    arr_f = table_arr.reshape((2,) * n).ravel(order="F")
    bits = 0
    for i in np.flatnonzero(arr_f):
        bits |= 1 << int(i)
    return int(tb.hi[bits]), bits


def _leaf_threshold_net(vars_list: list[str], bits: int | None, atlas_tables=None) -> dict[str, Any] | None:
    n = len(vars_list)
    if bits is None or n < 1 or n > 4:
        return None
    tables = atlas_tables or _get_atlas_tables(4)
    layers = atlas.net_layers(tables, n, bits)
    if layers is None:
        return None
    nodes = []
    cur_inputs = list(vars_list)
    for li, layer in enumerate(layers):
        next_inputs = []
        for ni, neu in enumerate(layer):
            nid = f"n_{li}_{ni}"
            nodes.append({"id": nid, "in": list(cur_inputs), "w": [int(w) for w in neu["w"]], "t": int(neu["t"])})
            next_inputs.append(nid)
        cur_inputs = next_inputs
    return {"inputs": list(vars_list), "nodes": nodes, "output": cur_inputs[0]}


def _compose_threshold_nets(
    vars_list: list[str],
    enc_vars: list[str],
    enc_nets: list[dict[str, Any] | None],
    dec_net: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if dec_net is None or any(e is None for e in enc_nets):
        return None
    nodes = []
    wire_map: dict[str, str] = {}
    for k, (ev, enet) in enumerate(zip(enc_vars, enc_nets)):
        prefix = f"e{k}_"
        local_map: dict[str, str] = {}
        for nd in enet["nodes"]:
            new_id = prefix + nd["id"]
            local_map[nd["id"]] = new_id
            nodes.append({
                "id": new_id,
                "in": [local_map.get(src, src) for src in nd["in"]],
                "w": list(nd["w"]),
                "t": int(nd["t"]),
            })
        wire_map[ev] = local_map.get(enet["output"], enet["output"])

    d_prefix = "d_"
    d_map: dict[str, str] = dict(wire_map)
    for nd in dec_net["nodes"]:
        new_id = d_prefix + nd["id"]
        d_map[nd["id"]] = new_id
        nodes.append({
            "id": new_id,
            "in": [d_map.get(src, src) for src in nd["in"]],
            "w": list(nd["w"]),
            "t": int(nd["t"]),
        })
    return {
        "inputs": list(vars_list),
        "nodes": nodes,
        "output": d_map.get(dec_net["output"], dec_net["output"]),
    }


def eval_threshold_net(net: dict[str, Any], env: dict[str, int]) -> int:
    """Evaluate a DAG threshold-neuron network emitted by the Ur-Compiler."""
    vals = {v: int(env[v]) for v in net["inputs"]}
    for nd in net["nodes"]:
        s = sum(int(w) * vals[src] for w, src in zip(nd["w"], nd["in"]))
        vals[nd["id"]] = 1 if s >= int(nd["t"]) else 0
    return vals[net["output"]]


def _leaf_compile_table(vars_list: list[str], table_arr: np.ndarray, atlas_tables=None) -> dict[str, Any]:
    tt = _truthtable_from_array(vars_list, table_arr)
    bdd_art = truthtable_to_bdd(tt)
    expr_art = bdd_to_expr(bdd_art)
    circ_art = bdd_to_circuit(bdd_art, vars_list)
    atlas_neurons, bits = _atlas_min_for_table(len(vars_list), table_arr, atlas_tables=atlas_tables)
    tnet = _leaf_threshold_net(vars_list, bits, atlas_tables=atlas_tables)
    return {
        "vars": list(vars_list),
        "expr": expr_art,
        "circuit": circ_art,
        "threshold_net": tnet,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": atlas_neurons,
        "decomposed": False,
        "profile_rank": None,
        "children": [],
    }


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


def _best_profile_split_table(
    vars_list: list[str], table_arr: np.ndarray, max_s1: int = 4, max_s2_sample: int = 64
) -> tuple[list[str], list[str], int, np.ndarray, np.ndarray] | None:
    """NumPy-vectorized C4 profile rank search over truth-table array."""
    n = len(vars_list)
    k = min(max_s1, max(2, n // 2))
    candidates: list[list[int]] = []
    for start in range(0, n - k + 1):
        candidates.append(list(range(start, start + k)))
    if n >= 2 * k:
        candidates.append(list(range(0, n, 2))[:k])

    arr_nd = table_arr.reshape((2,) * n)
    best = None
    for s1_pos in candidates:
        s1_set = set(s1_pos)
        s2_pos = [i for i in range(n) if i not in s1_set]
        n1, n2 = len(s1_pos), len(s2_pos)
        mat = np.transpose(arr_nd, s1_pos + s2_pos).reshape(1 << n1, 1 << n2)

        # Fast pre-filter on sampled S2 columns if S2 is large
        if (1 << n2) > max_s2_sample:
            cols = np.linspace(0, (1 << n2) - 1, max_s2_sample, dtype=int)
            uniq_sample = np.unique(mat[:, cols], axis=0)
            sample_rank = 0 if len(uniq_sample) <= 1 else math.ceil(math.log2(len(uniq_sample)))
            if sample_rank >= n1:
                continue

        # Exact profile equivalence classes across all S2
        _, first_idx, inverse = np.unique(mat, axis=0, return_index=True, return_inverse=True)
        num_classes = len(first_idx)
        rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
        if rank >= n1:
            continue

        s1 = [vars_list[i] for i in s1_pos]
        s2 = [vars_list[i] for i in s2_pos]
        # rep_rows[c] = mat[first_idx[c], :] gives the exact decoder slice for code c
        rep_rows = mat[first_idx, :]
        if best is None or rank < best[2]:
            best = (s1, s2, rank, inverse, rep_rows)
            if rank <= 1:
                break
    return best


def _compile_table_factored(
    vars_list: list[str],
    table_arr: np.ndarray,
    *,
    max_leaf: int = 4,
    atlas_tables=None,
    _depth: int = 0,
) -> dict[str, Any]:
    if atlas_tables is None:
        atlas_tables = _get_atlas_tables(4)
    n = len(vars_list)
    if n <= max_leaf:
        return _leaf_compile_table(vars_list, table_arr, atlas_tables=atlas_tables)

    split = _best_profile_split_table(vars_list, table_arr, max_s1=max_leaf)
    if split is None:
        return _leaf_compile_table(vars_list, table_arr, atlas_tables=atlas_tables)

    s1, s2, rank, row_to_code, rep_rows = split
    enc_vars = [f"_c_{_depth}_{j}" for j in range(rank)]
    encoders = []
    enc_map: dict[str, Any] = {}
    for bit_idx in range(rank):
        enc_table = ((row_to_code >> bit_idx) & 1).astype(np.uint8)
        enc_res = _compile_table_factored(
            s1, enc_table, max_leaf=max_leaf, atlas_tables=atlas_tables, _depth=_depth + 1
        )
        encoders.append(enc_res)
        enc_map[enc_vars[bit_idx]] = enc_res["expr"]["body"]

    # Build decoder table over enc_vars + s2 (MSB-first: enc_vars then s2)
    n2 = len(s2)
    num_codes = rep_rows.shape[0]
    dec_table = np.zeros((1 << rank, 1 << n2), dtype=np.uint8)
    for c in range(num_codes):
        # enc_vars[j] is bit (rank - 1 - j) of row index in dec_table, while row_to_code uses bit j = enc_vars[j]
        rev_c = sum((((c >> j) & 1) << (rank - 1 - j)) for j in range(rank))
        dec_table[rev_c, :] = rep_rows[c, :]
    # Unreachable codes fallback to rep_rows[0]
    used_rev = {sum((((c >> j) & 1) << (rank - 1 - j)) for j in range(rank)) for c in range(num_codes)}
    for r in range(1 << rank):
        if r not in used_rev:
            dec_table[r, :] = rep_rows[0, :]

    dec_vars = enc_vars + s2
    dec_res = _compile_table_factored(
        dec_vars, dec_table.ravel(), max_leaf=max_leaf, atlas_tables=atlas_tables, _depth=_depth + 1
    )
    composed_body = subst_expr(dec_res["expr"]["body"], enc_map)
    composed_expr = {"kind": "expr", "body": composed_body}
    circ_art = _expr_to_dag_circuit(composed_body, vars_list)

    neuron_ub = None
    if dec_res["atlas_min_neurons"] is not None and all(e["atlas_min_neurons"] is not None for e in encoders):
        neuron_ub = dec_res["atlas_min_neurons"] + sum(e["atlas_min_neurons"] for e in encoders)
    tnet = _compose_threshold_nets(
        vars_list, enc_vars, [e.get("threshold_net") for e in encoders], dec_res.get("threshold_net")
    )

    return {
        "vars": list(vars_list),
        "expr": composed_expr,
        "circuit": circ_art,
        "threshold_net": tnet,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": neuron_ub,
        "decomposed": True,
        "profile_rank": rank,
        "split": {"s1": s1, "s2": s2},
        "children": encoders + [dec_res],
    }


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
        atlas_tables = _get_atlas_tables(4)
    n = len(vars_list)
    if n <= 14:
        table_arr = _table_from_fn(vars_list, fn)
        return _compile_table_factored(
            vars_list, table_arr, max_leaf=max_leaf, atlas_tables=atlas_tables, _depth=_depth
        )
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
    circ_art = _expr_to_dag_circuit(composed_body, vars_list)

    neuron_ub = None
    if dec_res["atlas_min_neurons"] is not None and all(e["atlas_min_neurons"] is not None for e in encoders):
        neuron_ub = dec_res["atlas_min_neurons"] + sum(e["atlas_min_neurons"] for e in encoders)
    tnet = _compose_threshold_nets(
        vars_list, enc_vars, [e.get("threshold_net") for e in encoders], dec_res.get("threshold_net")
    )

    return {
        "vars": list(vars_list),
        "expr": composed_expr,
        "circuit": circ_art,
        "threshold_net": tnet,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": neuron_ub,
        "decomposed": True,
        "profile_rank": rank,
        "split": {"s1": s1, "s2": s2},
        "children": encoders + [dec_res],
    }


def _lean_certify_equiv(vars_list: list[str], expr_art: dict[str, Any], ref_expr: dict[str, Any] | None = None, name: str = "ur_cert") -> dict[str, Any]:
    """Certify `expr_art ≡ ref_expr` (or vs BDD canonical form) via LRAT + Lean 4.12."""
    from . import lean_bridge, sat

    if ref_expr is None:
        tt = TruthTable.from_function(vars_list, _fn_from_expr(vars_list, expr_art))
        ref_expr = bdd_to_expr(truthtable_to_bdd(tt))
    status, lrat_steps, _ = sat.prove_equivalence_lrat({"vars": vars_list, "left": expr_art, "right": ref_expr})
    if status != "unsat":
        return {"ok": False, "status": status, "axioms": (), "theorem": name}
    chk, _ = lean_bridge.verify_expr_equiv_lrat(expr_art, ref_expr, vars_list, lrat_steps, name=name)
    return {"ok": chk.ok, "status": "unsat", "axioms": list(chk.axioms), "theorem": chk.theorem, "source_sha256": chk.source_sha256}


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
        lean_cert = None
        if spec.get("certify_lean"):
            lean_cert = _lean_certify_equiv(vars_list, res["expr"], spec.get("reference_expr"), name=f"{n_id}_lean")
        prov = {"produced_by": "ur_compiler.compile_profile_factored",
                "decomposed": res["decomposed"], "profile_rank": res["profile_rank"]}
        if lean_cert is not None:
            prov["lean_cert"] = lean_cert
        expr_node = csir.node(
            n_id,
            res["expr"],
            {"vars": vars_list},
            resources={"cost": res["circuit_cost"], "atlas_neuron_ub": res["atlas_min_neurons"],
                       "cost_model": "F0/compositional"},
            provenance=prov,
        )
        b = csir.bundle([expr_node], [])
        return {
            "kind": "f0",
            "compiled": res,
            "lean_cert": lean_cert,
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

    if kind == "stochastic_lts":
        states = list(spec["states"])
        actions = list(spec["actions"])
        transitions = spec["transitions"]  # (s, a) -> dict[(ns, ob), prob] or list[(ns, ob, prob)]
        s_bits = max(1, math.ceil(math.log2(max(2, len(states)))))
        a_bits = max(1, math.ceil(math.log2(max(2, len(actions)))))
        s_vars = [f"s{i}" for i in range(s_bits)]
        a_vars = [f"a{i}" for i in range(a_bits)]
        step_vars = s_vars + a_vars
        s_index = {s: i for i, s in enumerate(states)}

        det_trans: dict[tuple[Any, Any], tuple[Any, int]] = {}
        eps_bound = 0.0
        for s in states:
            for a in actions:
                dist = transitions[(s, a)]
                items = list(dist.items()) if isinstance(dist, dict) else [((ns, ob), p) for ns, ob, p in dist]
                best_pair, best_p = max(items, key=lambda kv: kv[1])
                det_trans[(s, a)] = (best_pair[0], int(bool(best_pair[1])))
                eps_bound = max(eps_bound, max(0.0, 1.0 - float(best_p)))

        horizon = max(1, int(spec.get("horizon", 1)))
        horizon_eps_bound = min(1.0, horizon * eps_bound)

        nodes = [
            csir.node(
                "stochastic_lts_spec",
                {"kind": "lts", "body": {"states": states, "actions": actions, "stochastic": True,
                                         "eps_bound": eps_bound, "horizon": horizon,
                                         "horizon_eps_bound": horizon_eps_bound}},
                {"actions": actions},
                resources={"eps_bound": eps_bound, "horizon": horizon,
                           "horizon_eps_bound": horizon_eps_bound, "cost_model": "T-step-TV"},
                provenance={"produced_by": "stochastic_lts_spec"},
            )
        ]
        links = []
        compiled_outputs = {}
        for out_name, getter in (
            [(f"next_s{b}", lambda ns, ob, bit=b: (s_index[ns] >> bit) & 1) for b in range(s_bits)]
            + [("out", lambda ns, ob: int(bool(ob)))]
        ):
            def _make_sstep_fn(g=getter):
                def _step(env: dict[str, int]) -> int:
                    si = sum((env[s_vars[j]] << j) for j in range(s_bits))
                    ai = sum((env[a_vars[j]] << j) for j in range(a_bits))
                    if si >= len(states) or ai >= len(actions):
                        return 0
                    ns, ob = det_trans[(states[si], actions[ai])]
                    return g(ns, ob)
                return _step

            comp = compile_profile_factored(step_vars, _make_sstep_fn())
            compiled_outputs[out_name] = comp
            nodes.append(
                csir.node(
                    out_name,
                    comp["expr"],
                    {"vars": step_vars},
                    resources={"cost": comp["circuit_cost"], "atlas_neuron_ub": comp["atlas_min_neurons"],
                               "eps_bound": eps_bound, "cost_model": "F0/compositional"},
                    provenance={"produced_by": "ur_compiler.stochastic_lts_step", "parents": ["stochastic_lts_spec"],
                                "eps_bound": eps_bound},
                )
            )
            links.append(
                csir.link(
                    "stochastic_lts_spec", out_name, "distills",
                    {"vars": step_vars, "target": out_name},
                    certificate={"method": "argmax-determinization", "eps_bound": eps_bound},
                    warrant={"basis": ["kernel-checked", "1-step-TV-bound"],
                             "trusted_base": ["cerp/ur_compiler.py"],
                             "conditions": [f"1-step TV error <= {eps_bound:.6g}"]},
                )
            )
        b = csir.bundle(nodes, links)
        return {
            "kind": "stochastic_lts",
            "eps_bound": eps_bound,
            "horizon": horizon,
            "horizon_eps_bound": horizon_eps_bound,
            "compiled_outputs": compiled_outputs,
            "csir": b,
            "validation_errors": csir.validate(b),
        }

    if kind == "continuous":
        # Quantized continuous function f: [0, 1]^d -> {0, 1} (or R -> bool via threshold)
        dim = int(spec["dim"])
        bits = int(spec.get("bits_per_coord", 3))
        fn_cont = spec["fn"]  # Callable[[list[float]], int|bool|float]
        threshold = float(spec.get("threshold", 0.5))
        lipschitz = spec.get("lipschitz")
        adaptive = bool(spec.get("adaptive", False)) and (lipschitz is not None)
        coord_eps = 2.0 ** (-bits)
        eps_bound = float(lipschitz) * math.sqrt(dim) * coord_eps if lipschitz is not None else coord_eps

        vars_list = [f"x{d}_b{b}" for d in range(dim) for b in range(bits)]
        denom = float((1 << bits) - 1) if bits > 0 else 1.0

        eval_count = 0
        if adaptive:
            # Lipschitz-certified adaptive dyadic box subdivision over [0, 1]^d grid
            grid_n = 1 << bits
            table_grid = np.zeros((grid_n,) * dim, dtype=np.uint8)
            L_val = float(lipschitz)

            def _subdivide(bounds: list[tuple[int, int]]) -> None:
                nonlocal eval_count
                if all(hi - lo == 1 for lo, hi in bounds):
                    idx = tuple(lo for lo, _ in bounds)
                    xs = [i / denom if denom > 0 else 0.0 for i in idx]
                    val = fn_cont(xs)
                    eval_count += 1
                    table_grid[idx] = int(val) if isinstance(val, bool) else (1 if float(val) >= threshold else 0)
                    return
                center_idx = [((lo + hi - 1) / 2.0) for lo, hi in bounds]
                xs_c = [c / denom if denom > 0 else 0.0 for c in center_idx]
                f_c = float(fn_cont(xs_c))
                eval_count += 1
                rad = math.sqrt(sum((((hi - lo - 1) / 2.0) / denom) ** 2 for lo, hi in bounds)) if denom > 0 else 0.0
                if abs(f_c - threshold) > L_val * rad:
                    sl = tuple(slice(lo, hi) for lo, hi in bounds)
                    table_grid[sl] = 1 if f_c >= threshold else 0
                    return
                # Split along widest coordinate
                split_d = max(range(dim), key=lambda d: bounds[d][1] - bounds[d][0])
                lo, hi = bounds[split_d]
                mid = (lo + hi) // 2
                left_b = list(bounds)
                left_b[split_d] = (lo, mid)
                right_b = list(bounds)
                right_b[split_d] = (mid, hi)
                _subdivide(left_b)
                _subdivide(right_b)

            _subdivide([(0, grid_n)] * dim)

            def _quantized_fn(env: dict[str, int]) -> int:
                idx = tuple(sum((int(env[f"x{d}_b{b}"]) << b) for b in range(bits)) for d in range(dim))
                return int(table_grid[idx])
        else:
            def _quantized_fn(env: dict[str, int]) -> int:
                nonlocal eval_count
                xs = []
                for d in range(dim):
                    q = sum((int(env[f"x{d}_b{b}"]) << b) for b in range(bits))
                    xs.append(q / denom if denom > 0 else 0.0)
                val = fn_cont(xs)
                eval_count += 1
                if isinstance(val, bool):
                    return int(val)
                return 1 if float(val) >= threshold else 0

        comp = compile_profile_factored(vars_list, _quantized_fn)
        n_id = spec.get("name", "continuous_compiled")
        c_id = f"{n_id}_circuit"
        lean_cert = None
        if spec.get("certify_lean"):
            lean_cert = _lean_certify_equiv(vars_list, comp["expr"], name=f"{n_id}_lean")
        expr_node = csir.node(
            n_id,
            comp["expr"],
            {"vars": vars_list},
            resources={"cost": comp["circuit_cost"], "atlas_neuron_ub": comp["atlas_min_neurons"],
                       "coord_eps": coord_eps, "eps_bound": eps_bound, "fn_evals": eval_count,
                       "cost_model": "F0/quantized"},
            provenance={"produced_by": "ur_compiler.continuous_quantized",
                        "dim": dim, "bits_per_coord": bits, "eps_bound": eps_bound,
                        "adaptive": adaptive, "fn_evals": eval_count,
                        "decomposed": comp["decomposed"], "profile_rank": comp["profile_rank"]},
        )
        circ_node = csir.node(
            c_id,
            comp["circuit"],
            {"vars": vars_list},
            resources={"cost": comp["circuit_cost"], "coord_eps": coord_eps, "eps_bound": eps_bound,
                       "cost_model": "circuit/DAG"},
            provenance={"produced_by": "ur_compiler.continuous_quantized", "parents": [n_id]},
        )
        warrant = {"basis": ["structural-sharing"], "trusted_base": ["cerp/ur_compiler.py"],
                   "conditions": [f"quantization resolution <= {coord_eps:.6g}"]}
        if lean_cert is not None:
            warrant["lean_cert"] = lean_cert
        link = csir.link(
            n_id, c_id, "extensional",
            {"vars": vars_list},
            certificate={"method": "hash-consed-dag-translation"},
            warrant=warrant,
        )
        b = csir.bundle([expr_node, circ_node], [link])
        return {
            "kind": "continuous",
            "eps_bound": eps_bound,
            "coord_eps": coord_eps,
            "adaptive": adaptive,
            "fn_evals": eval_count,
            "lean_cert": lean_cert,
            "compiled": comp,
            "csir": b,
            "validation_errors": csir.validate(b),
        }

    raise ValueError(f"Unsupported spec kind: {kind!r}")
