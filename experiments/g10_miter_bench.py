"""G10 benchmark: multi-layer threshold network equivalence via Lean kernel `decide`.

Pre-registered benchmark measuring:
1. Core non-degenerate full-fan-in targets under 120s:
   - n=6 two-hidden-layer (`[6] -> [2] -> [2] -> 1`) vs explicit `Expr`
   - n=8 one-hidden-layer (`[8] -> [2] -> 1`) vs explicit `Expr`
2. Scaling ceiling (> 120s) across depth, width, and weight/DP-state axes.
3. Sub-obligation Lean kernel breakdown (`import/elaborate`, `wellFormed`, `checkLratT`).
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import kernel, lean_bridge, sat, ur_compiler


TIMEOUT_SEC = 150.0


def _and(a, b):
    return ["and", a, b]


def _or(a, b):
    return ["or", a, b]


def _not(a):
    return ["not", a]


def _xor(a, b):
    return ["xor", a, b]


def _iff(a, b):
    return _not(_xor(a, b))


def _gt3(as_, bs_):
    a0, a1, a2 = as_
    b0, b1, b2 = bs_
    eq0 = _iff(a0, b0)
    eq1 = _iff(a1, b1)
    return _or(
        _and(a0, _not(b0)),
        _or(_and(eq0, _and(a1, _not(b1))), _and(eq0, _and(eq1, _and(a2, _not(b2))))),
    )


def _gt4(as_, bs_):
    return _or(
        _and(as_[0], _not(bs_[0])),
        _and(_iff(as_[0], bs_[0]), _gt3(as_[1:], bs_[1:])),
    )


def _bits_expr(vs, mask):
    res = ["var", vs[0]] if ((mask >> (len(vs) - 1)) & 1) else _not(["var", vs[0]])
    for i, v in enumerate(vs[1:], 1):
        lit = ["var", v] if ((mask >> (len(vs) - 1 - i)) & 1) else _not(["var", v])
        res = _and(res, lit)
    return res


def _dense_eq4_expr(vs, w4):
    a_vars, b_vars = vs[:4], vs[4:]
    by_sum = {}
    for m in range(16):
        s = sum(w4[i] * ((m >> (3 - i)) & 1) for i in range(4))
        by_sum.setdefault(s, []).append(m)
    eq_id = _and(
        _and(_iff(["var", a_vars[0]], ["var", b_vars[0]]), _iff(["var", a_vars[1]], ["var", b_vars[1]])),
        _and(_iff(["var", a_vars[2]], ["var", b_vars[2]]), _iff(["var", a_vars[3]], ["var", b_vars[3]])),
    )
    body = eq_id
    for ms in by_sum.values():
        if len(ms) > 1:
            for m1 in ms:
                for m2 in ms:
                    if m1 != m2:
                        body = _or(body, _and(_bits_expr(a_vars, m1), _bits_expr(b_vars, m2)))
    return {"kind": "expr", "body": body}


def _eval_net(net, env):
    vals = dict(env)
    for nd in net["nodes"]:
        s = sum(int(w) * (1 if vals[i] else 0) for i, w in zip(nd["in"], nd["w"]))
        vals[nd["id"]] = 1 if s >= int(nd["t"]) else 0
    return vals[net["output"]]


def _verify_truth_table(net, expr_d, vs):
    n = len(vs)
    for mask in range(1 << n):
        env = {vs[i]: (mask >> i) & 1 for i in range(n)}
        assert _eval_net(net, env) == (1 if kernel.evaluate(expr_d, env) else 0)
    return True


def _build_benchmarks():
    vs4 = [f"x{i}" for i in range(4)]
    comp4 = ur_compiler.compile_profile_factored(vs4, lambda e: e["x0"] ^ e["x1"] ^ e["x2"] ^ e["x3"])

    vs6 = [f"x{i}" for i in range(6)]
    A3 = [["var", "x0"], ["var", "x1"], ["var", "x2"]]
    B3 = [["var", "x3"], ["var", "x4"], ["var", "x5"]]
    nB3 = [_not(x) for x in B3]
    C3 = [["var", "x4"], ["var", "x5"], ["var", "x3"]]
    n6_eq3_expr = {"kind": "expr", "body": _and(_iff(A3[0], B3[0]), _and(_iff(A3[1], B3[1]), _iff(A3[2], B3[2])))}
    n6_eq_ac_expr = _and(_iff(A3[0], C3[0]), _and(_iff(A3[1], C3[1]), _iff(A3[2], C3[2])))
    n6_cmp_xor_expr = {"kind": "expr", "body": _xor(_gt3(A3, B3), _gt3(A3, nB3))}

    n6_1h_eq3 = {
        "inputs": vs6,
        "nodes": [
            {"id": "h0", "in": vs6, "w": [4, 2, 1, -4, -2, -1], "t": 0},
            {"id": "h1", "in": vs6, "w": [4, 2, 1, -4, -2, -1], "t": 1},
            {"id": "out", "in": ["h0", "h1"], "w": [1, -1], "t": 1},
        ],
        "output": "out",
    }
    n6_2h_w2_cmp_xor = {
        "inputs": vs6,
        "nodes": [
            {"id": "h0", "in": vs6, "w": [4, 2, 1, -4, -2, -1], "t": 1},
            {"id": "h1", "in": vs6, "w": [4, 2, 1, 4, 2, 1], "t": 8},
            {"id": "g0", "in": ["h0", "h1"], "w": [1, 1], "t": 1},
            {"id": "g1", "in": ["h0", "h1"], "w": [1, 1], "t": 2},
            {"id": "out", "in": ["g0", "g1"], "w": [1, -1], "t": 1},
        ],
        "output": "out",
    }
    n6_2h_w4_rot_xor = {
        "inputs": vs6,
        "nodes": [
            {"id": "h0", "in": vs6, "w": [4, 2, 1, -4, -2, -1], "t": 0},
            {"id": "h1", "in": vs6, "w": [4, 2, 1, -4, -2, -1], "t": 1},
            {"id": "h2", "in": vs6, "w": [4, 2, 1, -1, -4, -2], "t": 0},
            {"id": "h3", "in": vs6, "w": [4, 2, 1, -1, -4, -2], "t": 1},
            {"id": "g0", "in": ["h0", "h1", "h2", "h3"], "w": [2, -2, -1, 1], "t": 2},
            {"id": "g1", "in": ["h0", "h1", "h2", "h3"], "w": [-1, 1, 2, -2], "t": 2},
            {"id": "out", "in": ["g0", "g1"], "w": [1, 1], "t": 1},
        ],
        "output": "out",
    }
    n6_3h_d4 = {
        "inputs": vs6,
        "nodes": n6_2h_w2_cmp_xor["nodes"][:-1] + [
            {"id": "m0", "in": ["g0", "g1"], "w": [-2, 1], "t": -1},
            {"id": "m1", "in": ["g0", "g1"], "w": [1, -2], "t": 1},
            {"id": "out", "in": ["m0", "m1"], "w": [-1, 1], "t": 1},
        ],
        "output": "out",
    }
    n6_4h_d5 = {
        "inputs": vs6,
        "nodes": n6_3h_d4["nodes"][:-1] + [
            {"id": "q0", "in": ["m0", "m1"], "w": [-2, 1], "t": 0},
            {"id": "q1", "in": ["m0", "m1"], "w": [2, -1], "t": 1},
            {"id": "out", "in": ["q0", "q1"], "w": [1, -1], "t": 1},
        ],
        "output": "out",
    }

    vs8 = [f"x{i}" for i in range(8)]
    A4 = [["var", f"x{i}"] for i in range(4)]
    B4 = [["var", f"x{i}"] for i in range(4, 8)]
    nB4 = [_not(x) for x in B4]
    eq4_ab = _and(_and(_iff(A4[0], B4[0]), _iff(A4[1], B4[1])), _and(_iff(A4[2], B4[2]), _iff(A4[3], B4[3])))
    eq4_ac = _and(_and(_iff(A4[0], B4[1]), _iff(A4[1], B4[2])), _and(_iff(A4[2], B4[3]), _iff(A4[3], B4[0])))
    par8_body = ["var", "x0"]
    for v in vs8[1:]:
        par8_body = _xor(par8_body, ["var", v])
    comp8 = ur_compiler.compile_profile_factored(vs8, lambda e: sum(e[v] for v in vs8) % 2)

    def _eq4_net(w4, scale=1):
        w = [scale * x for x in w4] + [-scale * x for x in w4]
        return {
            "inputs": vs8,
            "nodes": [
                {"id": "h0", "in": vs8, "w": w, "t": 0},
                {"id": "h1", "in": vs8, "w": w, "t": scale},
                {"id": "out", "in": ["h0", "h1"], "w": [1, -1], "t": 1},
            ],
            "output": "out",
        }

    n8_w3_or = {
        "inputs": vs8,
        "nodes": [
            {"id": "h0", "in": vs8, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 0},
            {"id": "h1", "in": vs8, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 1},
            {"id": "h2", "in": vs8, "w": [8, 4, 2, 1, 8, 4, 2, 1], "t": 16},
            {"id": "out", "in": ["h0", "h1", "h2"], "w": [1, -1, 1], "t": 1},
        ],
        "output": "out",
    }
    n8_w4_or = {
        "inputs": vs8,
        "nodes": [
            {"id": "h0", "in": vs8, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 0},
            {"id": "h1", "in": vs8, "w": [8, 4, 2, 1, -8, -4, -2, -1], "t": 1},
            {"id": "h2", "in": vs8, "w": [8, 4, 2, 1, -1, -8, -4, -2], "t": 0},
            {"id": "h3", "in": vs8, "w": [8, 4, 2, 1, -1, -8, -4, -2], "t": 1},
            {"id": "out", "in": ["h0", "h1", "h2", "h3"], "w": [1, -1, 1, -1], "t": 1},
        ],
        "output": "out",
    }
    n8_par8_1h = {
        "inputs": vs8,
        "nodes": [{"id": f"h{k}", "in": vs8, "w": [1] * 8, "t": k + 1} for k in range(8)]
        + [{"id": "out", "in": [f"h{k}" for k in range(8)], "w": [1 if k % 2 == 0 else -1 for k in range(8)], "t": 1}],
        "output": "out",
    }

    return [
        {"name": "baseline_xor4", "axis": "baseline", "shape": "[4]->[4]->1", "vars": vs4, "net": comp4["threshold_net"], "expr": comp4["expr"], "profile": True},
        {"name": "n6_1hidden_w2_eq3", "axis": "depth", "shape": "[6]->[2]->1", "vars": vs6, "net": n6_1h_eq3, "expr": n6_eq3_expr, "profile": False},
        {"name": "n6_2hidden_w2_cmp_xor", "axis": "core_n6_2h", "shape": "[6]->[2]->[2]->1", "vars": vs6, "net": n6_2h_w2_cmp_xor, "expr": n6_cmp_xor_expr, "profile": True},
        {"name": "n6_3hidden_w2_d4", "axis": "depth", "shape": "[6]->[2]->[2]->[2]->1", "vars": vs6, "net": n6_3h_d4, "expr": n6_cmp_xor_expr, "profile": False},
        {"name": "n6_4hidden_w2_d5", "axis": "depth", "shape": "[6]->[2]->[2]->[2]->[2]->1", "vars": vs6, "net": n6_4h_d5, "expr": n6_cmp_xor_expr, "profile": False},
        {"name": "n6_2hidden_w4_rot_xor", "axis": "width", "shape": "[6]->[4]->[2]->1", "vars": vs6, "net": n6_2h_w4_rot_xor, "expr": {"kind": "expr", "body": _xor(n6_eq3_expr["body"], n6_eq_ac_expr)}, "profile": False},
        {"name": "n8_1hidden_w2_eq4", "axis": "core_n8_1h", "shape": "[8]->[2]->1", "vars": vs8, "net": _eq4_net([8, 4, 2, 1]), "expr": {"kind": "expr", "body": eq4_ab}, "profile": True},
        {"name": "n8_factored_parity", "axis": "control", "shape": "balanced(13)", "vars": vs8, "net": comp8["threshold_net"], "expr": comp8["expr"], "profile": False},
        {"name": "n8_1hidden_w3_or", "axis": "width", "shape": "[8]->[3]->1", "vars": vs8, "net": n8_w3_or, "expr": {"kind": "expr", "body": _or(eq4_ab, _gt4(A4, nB4))}, "profile": False},
        {"name": "n8_1hidden_w4_rot_or", "axis": "width", "shape": "[8]->[4]->1", "vars": vs8, "net": n8_w4_or, "expr": {"kind": "expr", "body": _or(eq4_ab, eq4_ac)}, "profile": True},
        {"name": "n8_1hidden_w8_par8", "axis": "width", "shape": "[8]->[8]->1", "vars": vs8, "net": n8_par8_1h, "expr": {"kind": "expr", "body": par8_body}, "profile": False},
        {"name": "n8_1hidden_w2_scale2", "axis": "weight_scale", "shape": "[8]->[2]->1", "vars": vs8, "net": _eq4_net([8, 4, 2, 1], scale=2), "expr": {"kind": "expr", "body": eq4_ab}, "profile": False},
        {"name": "n8_1hidden_w2_super53", "axis": "weight_super53", "shape": "[8]->[2]->1", "vars": vs8, "net": _eq4_net([53, 26, 12, 5]), "expr": {"kind": "expr", "body": eq4_ab}, "profile": False},
        {"name": "n8_1hidden_w2_nonsup_17", "axis": "weight_nonsup", "shape": "[8]->[2]->1", "vars": vs8, "net": _eq4_net([17, 13, 11, 7]), "expr": _dense_eq4_expr(vs8, [17, 13, 11, 7]), "profile": False},
        {"name": "n8_1hidden_w2_nonsup_5", "axis": "weight_nonsup_colliding", "shape": "[8]->[2]->1", "vars": vs8, "net": _eq4_net([5, 4, 3, 2]), "expr": _dense_eq4_expr(vs8, [5, 4, 3, 2]), "profile": False},
    ]


def _profile_lean_stages(net, expr_d, vs, lrat_steps, timeout_s=TIMEOUT_SEC):
    n = len(vs)
    fmt_step = lambda c, hs: f"([" + ", ".join(str(l) for l in c) + "], [" + ", ".join(str(h) for h in hs) + "])"
    Ls = "[" + ", ".join(fmt_step(c, hs) for c, hs in lrat_steps) + "]"
    tns_s = lean_bridge.tnet_to_lean(net, vs)
    expr_s = lean_bridge.expr_to_lean(expr_d["body"], vs)
    header = "\n".join([
        "import Cerp",
        "open Cerp",
        f"def tns : List TNode := {tns_s}",
        f"def eSpec : Expr := {expr_s}",
        f"def Ls : List (Clause × List Nat) := {Ls}",
        "",
    ])
    stages = {
        "elab_only": header + f"#check @tseitinTNetMiterPB_lrat_unsat_implies_equiv {n} tns eSpec Ls\n",
        "wf_decide": header + f"theorem chk_wf : wellFormed (tseitinTNetMiterPB {n} tns eSpec) = true := by decide\n",
        "lrat_decide": header + f"theorem chk_lrat : checkLratT (bOfListAux (tseitinTNetMiterPB {n} tns eSpec) 0 .leaf) (tseitinTNetMiterPB {n} tns eSpec).length Ls = true := by decide\n",
    }
    timings = {}
    lean_bin = lean_bridge.lean_binary()
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        env = {**os.environ, "LEAN_PATH": str(lean_bridge._library(d))}
        for sname, src in stages.items():
            f = d / f"{sname}.lean"
            f.write_text(src, encoding="utf-8")
            t0 = time.perf_counter()
            try:
                code, _ = lean_bridge._run([lean_bin, str(f)], cwd=d, timeout=timeout_s, env=env)
                dt = round(time.perf_counter() - t0, 3)
                timings[sname] = {"status": "ok" if code == 0 else f"exit_{code}", "seconds": dt}
            except subprocess.TimeoutExpired:
                timings[sname] = {"status": "timeout", "seconds": round(timeout_s, 3)}
    return timings


def main():
    orig_run = lean_bridge._run

    def _capped_run(args, cwd=None, timeout=TIMEOUT_SEC, env=None):
        return orig_run(args, cwd=cwd, timeout=TIMEOUT_SEC, env=env)

    lean_bridge._run = _capped_run

    benchmarks = _build_benchmarks()
    results = []
    for item in benchmarks:
        name = item["name"]
        vs = item["vars"]
        net = item["net"]
        expr_d = item["expr"]
        _verify_truth_table(net, expr_d, vs)

        idx = sat._tnet_to_indexed_nodes(net, vs)
        mv, clauses = sat._lean_tnet_miter_pb(vs, idx, expr_d["body"])
        t0 = time.perf_counter()
        sat_status, lrat_steps, _ = sat.prove_tnet_equivalence_lrat(net, expr_d, vs, pb=True)
        sat_t = round(time.perf_counter() - t0, 4)
        assert sat_status == "unsat", f"{name} unexpected sat_status={sat_status}"

        total_abs_w = sum(abs(int(w)) for nd in net["nodes"] for w in nd["w"])
        max_abs_w = max(abs(int(w)) for nd in net["nodes"] for w in nd["w"])
        max_fan_in = max(len(nd["in"]) for nd in net["nodes"])

        t1 = time.perf_counter()
        try:
            chk, _ = lean_bridge.verify_threshold_net_equiv(
                net, expr_d, vs, lrat_steps=lrat_steps, name=f"g10_{name}", native=False, pb=True
            )
            lean_t = round(time.perf_counter() - t1, 3)
            lean_status = "ok" if chk.ok else "failed"
            axioms = list(chk.axioms)
        except subprocess.TimeoutExpired:
            lean_t = round(TIMEOUT_SEC, 3)
            lean_status = f"timeout_{int(TIMEOUT_SEC)}s"
            axioms = []

        rec = {
            "name": name,
            "axis": item["axis"],
            "shape": item["shape"],
            "n_inputs": len(vs),
            "nodes": len(net["nodes"]),
            "max_fan_in": max_fan_in,
            "max_abs_w": max_abs_w,
            "sum_abs_w": total_abs_w,
            "miter_vars": mv,
            "miter_clauses": len(clauses),
            "lrat_steps": len(lrat_steps),
            "sat_seconds": sat_t,
            "lean_status": lean_status,
            "lean_seconds": lean_t,
            "under_120s": lean_status == "ok" and lean_t < 120.0,
            "axioms": axioms,
        }
        if item["profile"]:
            rec["kernel_breakdown"] = _profile_lean_stages(net, expr_d, vs, lrat_steps)
        results.append(rec)
        print(
            f"{name}: shape={item['shape']} vars={mv} clauses={len(clauses)} steps={len(lrat_steps)} "
            f"lean={lean_status} ({lean_t}s) under_120s={rec['under_120s']}",
            flush=True,
        )

    out_path = ROOT / "experiments" / "results" / "g10_miter_timings.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"timeout_sec": TIMEOUT_SEC, "results": results}, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
