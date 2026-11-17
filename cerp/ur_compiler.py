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


def _leaf_compile(vars_list: list[str], fn: Callable[[dict[str, int]], int], atlas_tables=None) -> dict[str, Any]:
    tt = TruthTable.from_function(vars_list, fn)
    bdd_art = truthtable_to_bdd(tt)
    expr_art = bdd_to_expr(bdd_art)
    circ_art = bdd_to_circuit(bdd_art, vars_list)
    if len(vars_list) <= 4:
        return _leaf_compile_table(vars_list, _table_from_fn(vars_list, fn), atlas_tables=atlas_tables)
    return {
        "vars": list(vars_list),
        "expr": expr_art,
        "circuit": circ_art,
        "threshold_net": None,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": None,
        "decomposed": False,
        "profile_rank": None,
        "children": [],
    }


def _combine_soundness(labels) -> str:
    """Weakest label wins: any sampled(k) < cegar-sat < exact."""
    labels = [str(x) for x in labels]
    sampled = [x for x in labels if x.startswith("sampled")]
    if sampled:
        return sampled[0]
    return "cegar-sat" if "cegar-sat" in labels else "exact"


def _sample_s2_envs(s2: list[str], max_s2_sample: int) -> tuple[list[dict[str, int]], bool]:
    """Return assignments over `s2`: exact if `2^|s2| <= max_s2_sample`, else
    unbiased structured (0, 1, 1-hot, compl-1-hot, 2-hot) + SplitMix64 pseudorandom probes.
    Avoids strided `range(0, 2^n2, step)` which freezes all low-order bits at 0."""
    n2 = len(s2)
    if (1 << n2) <= max_s2_sample:
        return [{s2[j]: (m >> j) & 1 for j in range(n2)} for m in range(1 << n2)], True

    seen: set[tuple[int, ...]] = set()
    envs: list[dict[str, int]] = []

    def _add(bits: tuple[int, ...]) -> None:
        if bits not in seen and len(envs) < max_s2_sample:
            seen.add(bits)
            envs.append({s2[j]: bits[j] for j in range(n2)})

    _add((0,) * n2)
    _add((1,) * n2)
    for j in range(n2):
        _add(tuple(1 if i == j else 0 for i in range(n2)))
        _add(tuple(0 if i == j else 1 for i in range(n2)))
    for j in range(max(0, n2 - 1)):
        _add(tuple(1 if i in (j, j + 1) else 0 for i in range(n2)))

    state = 0x9E3779B97F4A7C15
    attempts = 0
    while len(envs) < max_s2_sample and attempts < max_s2_sample * 8:
        attempts += 1
        bits = []
        for j in range(n2):
            state = (state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
            z = state
            z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
            z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
            z = z ^ (z >> 31)
            bits.append(z & 1)
        _add(tuple(bits))
    return envs, False


def _sat_cegar_refine_split(
    vars_list: list[str],
    s1: list[str],
    s2: list[str],
    x1_to_code: dict[tuple[int, ...], int],
    expr_ast: dict[str, Any],
) -> dict[str, int] | None:
    """Use SAT to check if two `s1` inputs in the same equivalence class behave
    differently under `expr_ast` for some `s2`. Returns a counterexample `s2` env,
    None when every class is PROVED uniform (all SAT calls unsat), or the string
    "unknown" when any SAT call timed out (no claim may then be made)."""
    from . import sat

    body = expr_ast["body"]
    rep_of: dict[int, tuple[int, ...]] = {}
    for x1, code in x1_to_code.items():
        if code not in rep_of:
            rep_of[code] = x1
    for x1, code in x1_to_code.items():
        rep = rep_of[code]
        if x1 == rep:
            continue
        m1 = {s1[j]: ["const", int(x1[j])] for j in range(len(s1))}
        m2 = {s1[j]: ["const", int(rep[j])] for j in range(len(s1))}
        lhs = {"kind": "expr", "body": subst_expr(body, m1)}
        rhs = {"kind": "expr", "body": subst_expr(body, m2)}
        status, model, _ = sat.prove_equivalence({"vars": s2, "left": lhs, "right": rhs})
        if status == "sat" and isinstance(model, dict):
            return {v: int(bool(model.get(v, False))) for v in s2}
        if status != "unsat":
            return "unknown"
    return None


def _best_profile_split(
    vars_list: list[str],
    fn: Callable[[dict[str, int]], int],
    max_s1: int = 4,
    max_s2_sample: int = 128,
    expr_ast: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], int, dict[tuple[int, ...], int], str] | None:
    """Find a split (S1, S2) with |S1| <= max_s1 where the observational profile of S1
    has rank r = ceil(log2 |Im(profile)|) < |S1|. Returns (s1, s2, rank, x1_to_code, soundness)."""
    n = len(vars_list)
    k = min(max_s1, max(2, n // 2))
    candidates: list[list[str]] = []
    for start in range(0, n - k + 1):
        candidates.append(vars_list[start:start + k])
    if n >= 2 * k:
        candidates.append([vars_list[i] for i in range(0, n, 2)][:k])

    best = None
    for s1 in candidates:
        s1_set = set(s1)
        s2 = [v for v in vars_list if v not in s1_set]
        n1 = len(s1)
        eff_samples = max(max_s2_sample, 8 * n)
        s2_envs, exact_s2 = _sample_s2_envs(s2, eff_samples)
        soundness = "exact" if exact_s2 else f"sampled({len(s2_envs)})"

        for _cegar_round in range(8):
            profiles: dict[tuple[int, ...], int] = {}
            x1_to_code: dict[tuple[int, ...], int] = {}
            for m1 in range(1 << n1):
                x1 = tuple((m1 >> j) & 1 for j in range(n1))
                env1 = {s1[j]: x1[j] for j in range(n1)}
                sig = tuple(fn({**env1, **e2}) for e2 in s2_envs)
                if sig not in profiles:
                    profiles[sig] = len(profiles)
                x1_to_code[x1] = profiles[sig]
                if len(profiles) > (1 << (n1 - 1)):
                    break

            num_classes = len(profiles)
            rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
            if rank >= n1:
                break

            if not exact_s2 and expr_ast is not None:
                cex = _sat_cegar_refine_split(vars_list, s1, s2, x1_to_code, expr_ast)
                if isinstance(cex, dict):
                    s2_envs.append(cex)
                    continue
                if cex is None:
                    soundness = "cegar-sat"
            break
        else:
            rank = n1

        if rank >= n1:
            continue

        if best is None or rank < best[2]:
            best = (s1, s2, rank, x1_to_code, soundness)
            if rank <= 1 and soundness in ("exact", "cegar-sat"):
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
        "soundness": "exact",
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
    expr_ast: dict[str, Any] | None = None,
    _depth: int = 0,
) -> dict[str, Any]:
    """Recursively compile `fn` via C4 profile factorization down to `max_leaf` leaves.
    Supports `n <= 14` via vectorized NumPy exact truth-table slicing, and `n > 14` via
    unbiased probing + optional SAT-CEGAR refinement (`expr_ast`) without 2^n table blowup."""
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

    split = _best_profile_split(vars_list, fn, max_s1=max_leaf, expr_ast=expr_ast)
    if split is None:
        return _leaf_compile(vars_list, fn, atlas_tables=atlas_tables)

    s1, s2, rank, x1_to_code, split_soundness = split
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
    dec_expr_ast: dict[str, Any] | None = None
    if expr_ast is not None and rank > 0:
        # Symbolic substitution for CEGAR over dec_vars (ITE tree on enc_vars selecting rep_x1)
        def _mux_rep(bit: int, code_prefix: int) -> Any:
            if bit >= rank:
                rep = code_to_rep.get(code_prefix, code_to_rep[0])
                return subst_expr(expr_ast["body"], {s1[j]: ["const", int(rep[j])] for j in range(len(s1))})
            lo = _mux_rep(bit + 1, code_prefix)
            hi = _mux_rep(bit + 1, code_prefix | (1 << bit))
            return ["ite", ["var", enc_vars[bit]], hi, lo]

        dec_expr_ast = {"kind": "expr", "body": _mux_rep(0, 0)}
    elif expr_ast is not None and rank == 0:
        rep0 = code_to_rep[0]
        dec_expr_ast = {"kind": "expr", "body": subst_expr(expr_ast["body"], {s1[j]: ["const", int(rep0[j])] for j in range(len(s1))})}

    def _dec_fn(env: dict[str, int]) -> int:
        code = sum((int(env[ev]) << j) for j, ev in enumerate(enc_vars))
        if code not in code_to_rep:
            code = 0
        rep_x1 = code_to_rep[code]
        full_env = {**{s1[j]: rep_x1[j] for j in range(len(s1))}, **{v: env[v] for v in s2}}
        return fn(full_env)

    dec_res = compile_profile_factored(
        dec_vars, _dec_fn, max_leaf=max_leaf, atlas_tables=atlas_tables, expr_ast=dec_expr_ast, _depth=_depth + 1
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

    overall_sound = _combine_soundness(
        [split_soundness, dec_res.get("soundness", "exact")] + [e.get("soundness", "exact") for e in encoders])

    return {
        "vars": list(vars_list),
        "expr": composed_expr,
        "circuit": circ_art,
        "threshold_net": tnet,
        "circuit_cost": circuit_cost(circ_art),
        "atlas_min_neurons": neuron_ub,
        "decomposed": True,
        "soundness": overall_sound,
        "profile_rank": rank,
        "split": {"s1": s1, "s2": s2},
        "children": encoders + [dec_res],
    }


def compile_multi_profile_factored(
    vars_list: list[str],
    fns: dict[str, Callable[[dict[str, int]], int]],
    *,
    max_leaf: int = 4,
    atlas_tables=None,
) -> dict[str, Any]:
    """Joint multi-output C4 profile factorization sharing ONE latent encoder across outputs."""
    if atlas_tables is None:
        atlas_tables = _get_atlas_tables(4)
    n = len(vars_list)
    names = list(fns.keys())
    if len(names) <= 1 or n <= max_leaf:
        outputs = {nm: compile_profile_factored(vars_list, fns[nm], max_leaf=max_leaf, atlas_tables=atlas_tables) for nm in names}
        return {"shared_encoder": False, "profile_rank": None, "outputs": outputs, "encoders": []}

    k = min(max_leaf, max(2, n // 2))
    best = None
    if n <= 12:
        tables = {nm: _table_from_fn(vars_list, fns[nm]).reshape((2,) * n) for nm in names}
        for s1_pos in [list(range(start, start + k)) for start in range(0, n - k + 1)] + (
            [list(range(0, n, 2))[:k]] if n >= 2 * k else []
        ):
            s1_set = set(s1_pos)
            s2_pos = [i for i in range(n) if i not in s1_set]
            n1 = len(s1_pos)
            mats = [np.transpose(tables[nm], s1_pos + s2_pos).reshape(1 << n1, -1) for nm in names]
            joint_mat = np.concatenate(mats, axis=1)
            _, first_idx, inverse = np.unique(joint_mat, axis=0, return_index=True, return_inverse=True)
            num_classes = len(first_idx)
            rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
            if rank >= n1:
                continue
            s1 = [vars_list[i] for i in s1_pos]
            s2 = [vars_list[i] for i in s2_pos]
            # rows of joint_mat are in C order over s1_pos (s1[0] is the most significant bit)
            x1_to_code = {
                tuple((m1 >> (n1 - 1 - j)) & 1 for j in range(n1)): int(inverse[m1])
                for m1 in range(1 << n1)
            }
            if best is None or rank < best[2]:
                best = (s1, s2, rank, x1_to_code, "exact")
                if rank <= 1:
                    break
    else:
        candidates = [vars_list[start:start + k] for start in range(0, n - k + 1)]
        if n >= 2 * k:
            candidates.append([vars_list[i] for i in range(0, n, 2)][:k])
        for s1 in candidates:
            s1_set = set(s1)
            s2 = [v for v in vars_list if v not in s1_set]
            s2_envs, exact_s2 = _sample_s2_envs(s2, max(128, 8 * n))
            n1 = len(s1)
            profiles: dict[tuple[int, ...], int] = {}
            x1_to_code = {}
            for m1 in range(1 << n1):
                x1 = tuple((m1 >> j) & 1 for j in range(n1))
                env1 = {s1[j]: x1[j] for j in range(n1)}
                sig = tuple(fns[nm]({**env1, **e2}) for nm in names for e2 in s2_envs)
                if sig not in profiles:
                    profiles[sig] = len(profiles)
                x1_to_code[x1] = profiles[sig]
                if len(profiles) > (1 << (n1 - 1)):
                    break
            num_classes = len(profiles)
            rank = 0 if num_classes <= 1 else math.ceil(math.log2(num_classes))
            if rank < n1 and (best is None or rank < best[2]):
                sound_label = "exact" if exact_s2 else f"sampled({len(s2_envs)})"
                best = (s1, s2, rank, x1_to_code, sound_label)
                if rank <= 1:
                    break

    if best is None:
        outputs = {nm: compile_profile_factored(vars_list, fns[nm], max_leaf=max_leaf, atlas_tables=atlas_tables) for nm in names}
        return {"shared_encoder": False, "profile_rank": None, "outputs": outputs, "encoders": []}

    s1, s2, rank, x1_to_code, sound_str = best
    code_to_rep: dict[int, tuple[int, ...]] = {}
    for x1, code in x1_to_code.items():
        if code not in code_to_rep:
            code_to_rep[code] = x1

    enc_vars = [f"_mc_{j}" for j in range(rank)]
    encoders = []
    enc_map: dict[str, Any] = {}
    for bit_idx in range(rank):
        def _make_menc(bi: int) -> Callable[[dict[str, int]], int]:
            return lambda env: (x1_to_code[tuple(env[v] for v in s1)] >> bi) & 1

        enc_res = compile_profile_factored(s1, _make_menc(bit_idx), max_leaf=max_leaf, atlas_tables=atlas_tables)
        encoders.append(enc_res)
        enc_map[enc_vars[bit_idx]] = enc_res["expr"]["body"]

    dec_vars = enc_vars + s2
    outputs: dict[str, dict[str, Any]] = {}
    for nm in names:
        fn = fns[nm]

        def _dec_fn(env: dict[str, int], _f=fn) -> int:
            code = sum((int(env[ev]) << j) for j, ev in enumerate(enc_vars))
            rep_x1 = code_to_rep.get(code, code_to_rep[0])
            full_env = {**{s1[j]: rep_x1[j] for j in range(len(s1))}, **{v: env[v] for v in s2}}
            return _f(full_env)

        dec_res = compile_profile_factored(dec_vars, _dec_fn, max_leaf=max_leaf, atlas_tables=atlas_tables)
        composed_body = subst_expr(dec_res["expr"]["body"], enc_map)
        composed_expr = {"kind": "expr", "body": composed_body}
        circ_art = _expr_to_dag_circuit(composed_body, vars_list)
        tnet = _compose_threshold_nets(vars_list, enc_vars, [e.get("threshold_net") for e in encoders], dec_res.get("threshold_net"))
        neuron_ub = None
        if dec_res["atlas_min_neurons"] is not None and all(e["atlas_min_neurons"] is not None for e in encoders):
            neuron_ub = dec_res["atlas_min_neurons"] + sum(e["atlas_min_neurons"] for e in encoders)
        outputs[nm] = {
            "vars": list(vars_list),
            "expr": composed_expr,
            "circuit": circ_art,
            "threshold_net": tnet,
            "circuit_cost": circuit_cost(circ_art),
            "atlas_min_neurons": neuron_ub,
            "decomposed": True,
            "shared_encoder": True,
            "soundness": _combine_soundness(
                [sound_str, dec_res.get("soundness", "exact")] + [e.get("soundness", "exact") for e in encoders]),
            "profile_rank": rank,
            "split": {"s1": s1, "s2": s2},
            "children": encoders + [dec_res],
        }
    return {
        "shared_encoder": True,
        "profile_rank": rank,
        "split": {"s1": s1, "s2": s2},
        "soundness": sound_str,
        "encoders": encoders,
        "outputs": outputs,
    }


def _lean_certify_equiv(
    vars_list: list[str],
    expr_art: dict[str, Any],
    ref_expr: dict[str, Any] | None = None,
    name: str = "ur_cert",
    threshold_net: dict[str, Any] | None = None,
    verify_net: bool = True,
    spec_fn: Callable[[dict[str, int]], int] | None = None,
) -> dict[str, Any]:
    """Certify `expr_art ≡ spec` (and optional `threshold_net ≡ expr_art`) via LRAT + Lean 4.12.

    The specification is `ref_expr` if given, else the canonical BDD expression of
    `spec_fn` (only for n <= 12). The reference is never derived from `expr_art`
    itself: that would certify the compiled expression against its own normal form.
    Without a specification the result is `ok: False, status: "no-reference"`; the
    net check (if requested) still runs and is reported separately."""
    from . import lean_bridge, sat

    if ref_expr is None and spec_fn is not None and len(vars_list) <= 12:
        tt = TruthTable.from_function(vars_list, spec_fn)
        ref_expr = bdd_to_expr(truthtable_to_bdd(tt))

    if ref_expr is None:
        res: dict[str, Any] = {"ok": False, "status": "no-reference", "axioms": (), "theorem": name}
    else:
        status, lrat_steps, _ = sat.prove_equivalence_lrat({"vars": vars_list, "left": expr_art, "right": ref_expr})
        if status != "unsat":
            return {"ok": False, "status": status, "axioms": (), "theorem": name}
        chk, _ = lean_bridge.verify_expr_equiv_lrat(expr_art, ref_expr, vars_list, lrat_steps, name=name)
        res = {"ok": chk.ok, "status": "unsat", "axioms": list(chk.axioms), "theorem": chk.theorem, "source_sha256": chk.source_sha256}
        if not chk.ok:
            return res

    if verify_net and threshold_net is not None:
        n_status, n_lrat, _ = sat.prove_tnet_equivalence_lrat(threshold_net, expr_art, vars_list)
        if n_status != "unsat":
            res.update({"ok": False, "net_ok": False, "net_status": n_status, "net_theorem": f"{name}_net"})
            return res
        n_chk, _ = lean_bridge.verify_threshold_net_equiv(
            threshold_net, expr_art, vars_list, lrat_steps=n_lrat, name=f"{name}_net"
        )
        res.update({
            "ok": bool(res["ok"] and n_chk.ok),
            "net_ok": n_chk.ok,
            "net_status": "unsat",
            "net_axioms": list(n_chk.axioms),
            "net_theorem": n_chk.theorem,
            "net_source_sha256": n_chk.source_sha256,
        })
    return res


def threshold_net_to_dnet(net: dict[str, Any]) -> dict[str, Any]:
    """Re-express an Ur-Compiler threshold net as a kernel `dnet` artifact
    (step neurons, integer weights, bias = -t), so the trusted Python kernel can
    check it. Raises KeyError if a node reads a wire that is not defined earlier."""
    idx = {v: i for i, v in enumerate(net["inputs"])}
    neurons = []
    for nd in net["nodes"]:
        neurons.append({"in": [idx[src] for src in nd["in"]], "w": [int(w) for w in nd["w"]],
                        "b": -int(nd["t"]), "act": "step"})
        idx[nd["id"]] = len(idx)
    if not neurons or idx[net["output"]] != len(idx) - 1:
        neurons.append({"in": [idx[net["output"]]], "w": [1], "b": -1, "act": "step"})
    return {"kind": "dnet", "body": {"inputs": list(net["inputs"]), "neurons": neurons}}


def _table_artifact(vars_list: list[str], fn: Callable[[dict[str, int]], int]) -> dict[str, Any]:
    """Kernel `table` artifact: bit number sum(x_j << j) (order = vars_list) is fn(x)."""
    bits = 0
    n = len(vars_list)
    for m in range(1 << n):
        if fn({vars_list[j]: (m >> j) & 1 for j in range(n)}):
            bits |= 1 << m
    return {"kind": "table", "body": {"order": list(vars_list), "bits": bits}}


def _kernel_link(frm: str, to: str, left: dict, right: dict, vars_list: list[str]) -> dict[str, Any]:
    """Run the trusted kernel NOW and emit an extensional link that csir.recheck can
    re-verify from the bundle alone. Raises if the kernel refutes the claim."""
    if len(vars_list) > kernel.MAX_VARS:
        return csir.link(frm, to, "extensional", {"vars": vars_list},
                         warrant={"basis": ["exact-uncertified"], "trusted_base": ["cerp/ur_compiler.py"],
                                  "conditions": [f"not kernel-checked: {len(vars_list)} > {kernel.MAX_VARS} vars"]})
    v = kernel.check({"relation": "extensional", "vars": list(vars_list), "left": left, "right": right})
    if not v.ok:
        raise ValueError(f"kernel refuted {frm} ≡ {to}: {v}")
    return csir.link(frm, to, "extensional", {"vars": list(vars_list)}, certificate={"method": "exhaustive"},
                     warrant={"basis": ["kernel-checked"], "trusted_base": ["cerp/kernel.py"], "conditions": []})


def _compile_lts_steps(states, actions, det_trans, *, spec_id, spec_art, spec_resources, produced_by,
                       shared, distill_cert, distill_conditions, extra_res):
    """Shared back end for `lts` and `stochastic_lts`: compile every next-state bit and
    the output bit of the (determinized) step function, and export a CSIR bundle in
    which each claim is backed by what was actually checked:

      spec --distills (exact-uncertified: binary encoding)--> <out>_table
      <out>_table --extensional (kernel-checked)--> <out>              (compiled expr)
      <out> --extensional (kernel-checked)--> <out>_net                (threshold net as dnet)
    """
    s_bits = max(1, math.ceil(math.log2(max(2, len(states)))))
    a_bits = max(1, math.ceil(math.log2(max(2, len(actions)))))
    s_vars = [f"s{i}" for i in range(s_bits)]
    a_vars = [f"a{i}" for i in range(a_bits)]
    step_vars = s_vars + a_vars
    s_index = {st: i for i, st in enumerate(states)}

    getters = ([(f"next_s{b}", lambda ns, ob, bit=b: (s_index[ns] >> bit) & 1) for b in range(s_bits)]
               + [("out", lambda ns, ob: int(bool(ob)))])

    def _make_step_fn(g):
        def _step(env: dict[str, int]) -> int:
            si = sum((env[s_vars[j]] << j) for j in range(s_bits))
            ai = sum((env[a_vars[j]] << j) for j in range(a_bits))
            if si >= len(states) or ai >= len(actions):
                return 0  # unused codes: fixed to 0
            ns, ob = det_trans[(states[si], actions[ai])]
            return g(ns, ob)
        return _step

    step_fns = {name: _make_step_fn(g) for name, g in getters}
    if shared and len(step_vars) >= 2 and len(step_fns) >= 2:
        multi = compile_multi_profile_factored(step_vars, step_fns)
        compiled = multi["outputs"]
        shared_used, shared_rank = bool(multi.get("shared_encoder", False)), multi.get("profile_rank")
    else:
        compiled = {name: compile_profile_factored(step_vars, fn) for name, fn in step_fns.items()}
        shared_used, shared_rank = False, None

    nodes = [csir.node(spec_id, spec_art, {"actions": actions}, resources=spec_resources,
                       provenance={"produced_by": spec_id})]
    links = []
    encoding = (f"state i -> bits {s_vars} (LSB first), action i -> bits {a_vars}; "
                "unused codes map to 0")
    for name, _ in getters:
        comp = compiled[name]
        t_id = f"{name}_table"
        table = _table_artifact(step_vars, step_fns[name])
        nodes.append(csir.node(t_id, table, {"vars": step_vars}, provenance={"produced_by": produced_by,
                                                                            "parents": [spec_id]}))
        nodes.append(csir.node(
            name, comp["expr"], {"vars": step_vars},
            resources={"cost": comp["circuit_cost"], "atlas_neuron_ub": comp["atlas_min_neurons"],
                       "cost_model": "F0/compositional", **extra_res},
            provenance={"produced_by": produced_by, "parents": [t_id], "shared_encoder": shared_used,
                        "profile_rank": shared_rank, "soundness": comp.get("soundness", "exact")}))
        links.append(csir.link(spec_id, t_id, "distills", {"vars": step_vars, "target": name},
                               certificate=distill_cert,
                               warrant={"basis": ["exact-uncertified"], "trusted_base": ["cerp/ur_compiler.py"],
                                        "conditions": [encoding] + list(distill_conditions)}))
        links.append(_kernel_link(t_id, name, table, comp["expr"], step_vars))
        if comp.get("threshold_net") is not None:
            n_id = f"{name}_net"
            nodes.append(csir.node(n_id, threshold_net_to_dnet(comp["threshold_net"]), {"vars": step_vars},
                                   provenance={"produced_by": produced_by, "parents": [name]}))
            links.append(_kernel_link(name, n_id, comp["expr"], nodes[-1]["artifact"], step_vars))
    b = csir.bundle(nodes, links)
    return {"shared_encoder": shared_used, "profile_rank": shared_rank, "compiled_outputs": compiled,
            "csir": b, "validation_errors": csir.validate(b)}


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
        res = compile_profile_factored(vars_list, fn, expr_ast=spec.get("expr_ast"))
        n_id = spec.get("name", "f0_compiled")
        lean_cert = None
        if spec.get("certify_lean"):
            lean_cert = _lean_certify_equiv(
                vars_list,
                res["expr"],
                spec.get("reference_expr"),
                name=f"{n_id}_lean",
                threshold_net=res.get("threshold_net"),
                verify_net=bool(spec.get("verify_net", True)),
                spec_fn=fn,
            )
        prov = {"produced_by": "ur_compiler.compile_profile_factored",
                "decomposed": res["decomposed"], "profile_rank": res["profile_rank"],
                "soundness": res.get("soundness", "exact")}
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
        states, actions = list(spec["states"]), list(spec["actions"])
        det_trans = {(st, a): (spec["transitions"][(st, a)][0], int(bool(spec["transitions"][(st, a)][1])))
                     for st in states for a in actions}
        spec_art = {"kind": "lts", "body": {
            "states": states, "actions": actions,
            "transitions": [[st, a, ns, ob] for (st, a), (ns, ob) in det_trans.items()]}}
        out = _compile_lts_steps(
            states, actions, det_trans, spec_id="lts_spec", spec_art=spec_art, spec_resources=None,
            produced_by="ur_compiler.lts_step", shared=bool(spec.get("shared_encoder", True)),
            distill_cert={"method": "binary-encoding"}, distill_conditions=[], extra_res={})
        return {"kind": "lts", **out}

    if kind == "stochastic_lts":
        states, actions = list(spec["states"]), list(spec["actions"])
        transitions = spec["transitions"]  # (s, a) -> dict[(ns, ob), prob] or list[(ns, ob, prob)]
        det_trans: dict[tuple[Any, Any], tuple[Any, int]] = {}
        dist_rows = []
        eps_bound = 0.0
        for st in states:
            for a in actions:
                dist = transitions[(st, a)]
                items = list(dist.items()) if isinstance(dist, dict) else [((ns, ob), p) for ns, ob, p in dist]
                dist_rows.extend([st, a, ns, ob, float(pr)] for (ns, ob), pr in items)
                best_pair, best_p = max(items, key=lambda kv: kv[1])
                det_trans[(st, a)] = (best_pair[0], int(bool(best_pair[1])))
                # TV distance between the point mass at the argmax and the true distribution
                eps_bound = max(eps_bound, max(0.0, 1.0 - float(best_p)))
        horizon = max(1, int(spec.get("horizon", 1)))
        horizon_eps_bound = min(1.0, horizon * eps_bound)  # union bound over T steps
        spec_art = {"kind": "lts", "body": {"states": states, "actions": actions, "stochastic": True,
                                            "transitions": dist_rows, "eps_bound": eps_bound,
                                            "horizon": horizon, "horizon_eps_bound": horizon_eps_bound}}
        out = _compile_lts_steps(
            states, actions, det_trans, spec_id="stochastic_lts_spec", spec_art=spec_art,
            spec_resources={"eps_bound": eps_bound, "horizon": horizon,
                            "horizon_eps_bound": horizon_eps_bound, "cost_model": "T-step-TV"},
            produced_by="ur_compiler.stochastic_lts_step", shared=bool(spec.get("shared_encoder", True)),
            distill_cert={"method": "argmax-determinization", "eps_bound": eps_bound},
            distill_conditions=[f"1-step TV error <= {eps_bound:.6g}"], extra_res={"eps_bound": eps_bound})
        return {"kind": "stochastic_lts", "eps_bound": eps_bound, "horizon": horizon,
                "horizon_eps_bound": horizon_eps_bound, **out}

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
        fn_evals = eval_count
        n_id = spec.get("name", "continuous_compiled")
        c_id = f"{n_id}_circuit"
        lean_cert = None
        if spec.get("certify_lean"):
            lean_cert = _lean_certify_equiv(
                vars_list,
                comp["expr"],
                name=f"{n_id}_lean",
                threshold_net=comp.get("threshold_net"),
                verify_net=bool(spec.get("verify_net", True)),
                spec_fn=_quantized_fn,
            )
        eval_count = fn_evals
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
        link = _kernel_link(n_id, c_id, comp["expr"], comp["circuit"], vars_list)
        if lean_cert is not None:
            link["warrant"]["lean_cert"] = lean_cert
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
