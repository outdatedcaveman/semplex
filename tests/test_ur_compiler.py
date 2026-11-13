"""Tests for cerp.ur_compiler (compositional C4 profile-factorization + unified F0/LTS/Causal)."""

import math
import random

from cerp import kernel, ur_compiler
from cerp.epistemics.bayesnet import Structure, em_fit
from cerp.substrates import evaluate_circuit


def test_compositional_parity_n8():
    vars8 = [f"x{i}" for i in range(8)]
    parity = lambda env: sum(env[v] for v in vars8) & 1
    res = ur_compiler.compile_profile_factored(vars8, parity, max_leaf=4)
    assert res["decomposed"] is True
    assert res["profile_rank"] == 1
    assert res["atlas_min_neurons"] is not None
    assert res["circuit"] is not None
    assert res["threshold_net"] is not None
    assert len(res["threshold_net"]["nodes"]) <= res["atlas_min_neurons"]
    assert "gates" in res["circuit_cost"] and "depth" in res["circuit_cost"]
    # Verify exact extensional agreement on all 256 inputs for expr, DAG circuit, and threshold_net
    body = res["expr"]["body"]
    circ = res["circuit"]["body"]
    tnet = res["threshold_net"]
    for m in range(256):
        env = {vars8[j]: (m >> j) & 1 for j in range(8)}
        benv = {k: bool(v) for k, v in env.items()}
        expected = parity(env)
        assert int(bool(kernel._eval_expr(body, benv))) == expected
        assert evaluate_circuit(circ, env) == expected
        assert ur_compiler.eval_threshold_net(tnet, env) == expected


def test_compositional_hierarchical_threshold_n8():
    vars8 = [f"x{i}" for i in range(8)]
    # (x0+x1+x2+x3 >= 2) XOR (x4+x5+x6+x7 >= 3) -> rank 1 across (x0..x3, x4..x7)
    fn = lambda env: int((sum(env[f"x{i}"] for i in range(4)) >= 2) ^ (sum(env[f"x{i}"] for i in range(4, 8)) >= 3))
    out = ur_compiler.compile_unified({"kind": "f0", "vars": vars8, "fn": fn, "name": "hier_n8"})
    assert out["validation_errors"] == []
    res = out["compiled"]
    assert res["decomposed"] is True
    assert res["profile_rank"] == 1
    body = res["expr"]["body"]
    for m in range(256):
        env = {vars8[j]: (m >> j) & 1 for j in range(8)}
        benv = {k: bool(v) for k, v in env.items()}
        assert int(bool(kernel._eval_expr(body, benv))) == fn(env)


def test_unified_lts_compilation():
    # 3-state mod-3 counter with action 0=stay, 1=inc, output=1 iff next_state == 0
    states = ["S0", "S1", "S2"]
    actions = ["stay", "inc"]
    transitions = {
        ("S0", "stay"): ("S0", 1), ("S0", "inc"): ("S1", 0),
        ("S1", "stay"): ("S1", 0), ("S1", "inc"): ("S2", 0),
        ("S2", "stay"): ("S2", 0), ("S2", "inc"): ("S0", 1),
    }
    out = ur_compiler.compile_unified({"kind": "lts", "states": states, "actions": actions, "transitions": transitions})
    assert out["validation_errors"] == []
    assert set(out["compiled_outputs"].keys()) == {"next_s0", "next_s1", "out"}
    # Check compiled step-circuit matches transition table
    for si, s in enumerate(states):
        for ai, a in enumerate(actions):
            ns, ob = transitions[(s, a)]
            ns_i = states.index(ns)
            benv = {"s0": bool(si & 1), "s1": bool((si >> 1) & 1), "a0": bool(ai & 1)}
            got_ns0 = int(bool(kernel._eval_expr(out["compiled_outputs"]["next_s0"]["expr"]["body"], benv)))
            got_ns1 = int(bool(kernel._eval_expr(out["compiled_outputs"]["next_s1"]["expr"]["body"], benv)))
            got_out = int(bool(kernel._eval_expr(out["compiled_outputs"]["out"]["expr"]["body"], benv)))
            assert (got_ns0 + 2 * got_ns1) == ns_i
            assert got_out == ob


def test_unified_causal_compilation():
    from collections import Counter
    s = Structure(name="toy", observables=("X", "Y"), latents=(), parents={"X": (), "Y": ("X",)})
    data = {(): Counter([(0, 0), (0, 0), (1, 1), (1, 1)])}
    params, _ = em_fit(s, data, random.Random(0), restarts=1, iters=20)
    out = ur_compiler.compile_unified({"kind": "causal", "structure": s, "params": params, "target": "Y"})
    assert out["validation_errors"] == []
    assert out["recheck"][1][1] == "verified"


def test_unified_stochastic_lts_compilation():
    states = ["S0", "S1"]
    actions = ["a0", "a1"]
    transitions = {
        ("S0", "a0"): {("S0", 0): 0.9, ("S1", 1): 0.1},
        ("S0", "a1"): {("S1", 1): 0.85, ("S0", 0): 0.15},
        ("S1", "a0"): {("S1", 1): 0.95, ("S0", 0): 0.05},
        ("S1", "a1"): {("S0", 0): 0.8, ("S1", 1): 0.2},
    }
    out = ur_compiler.compile_unified({
        "kind": "stochastic_lts",
        "states": states,
        "actions": actions,
        "transitions": transitions,
        "horizon": 3,
    })
    assert out["validation_errors"] == []
    assert abs(out["eps_bound"] - 0.2) < 1e-9
    assert abs(out["horizon_eps_bound"] - 0.6) < 1e-9
    benv_01 = {"s0": False, "a0": True}
    assert int(bool(kernel._eval_expr(out["compiled_outputs"]["next_s0"]["expr"]["body"], benv_01))) == 1
    assert int(bool(kernel._eval_expr(out["compiled_outputs"]["out"]["expr"]["body"], benv_01))) == 1


def test_unified_continuous_compilation():
    # 2D continuous indicator: x0 + x1 >= 1.0, quantized at 3 bits per coord (6 Boolean vars)
    out = ur_compiler.compile_unified({
        "kind": "continuous",
        "dim": 2,
        "bits_per_coord": 3,
        "fn": lambda xs: xs[0] + xs[1],
        "threshold": 1.0,
        "lipschitz": 1.0,
        "name": "halfspace_2d",
    })
    assert out["validation_errors"] == []
    assert out["coord_eps"] == 0.125
    assert out["eps_bound"] > 0.125
    comp = out["compiled"]
    assert comp["circuit"] is not None
    # Check origin (0, 0) -> 0 and (1, 1) -> 1
    zeros = {v: 0 for v in comp["vars"]}
    ones = {v: 1 for v in comp["vars"]}
    assert evaluate_circuit(comp["circuit"]["body"], zeros) == 0
    assert evaluate_circuit(comp["circuit"]["body"], ones) == 1

    # Adaptive Lipschitz subdivision should agree with uniform and use fewer than 64 fn evals
    out_ad = ur_compiler.compile_unified({
        "kind": "continuous",
        "dim": 2,
        "bits_per_coord": 3,
        "fn": lambda xs: xs[0] + xs[1],
        "threshold": 1.0,
        "lipschitz": math.sqrt(2.0),
        "adaptive": True,
        "name": "halfspace_2d_ad",
    })
    assert out_ad["validation_errors"] == []
    assert out_ad["adaptive"] is True
    assert out_ad["fn_evals"] < 64
    assert evaluate_circuit(out_ad["compiled"]["circuit"]["body"], zeros) == 0
    assert evaluate_circuit(out_ad["compiled"]["circuit"]["body"], ones) == 1
