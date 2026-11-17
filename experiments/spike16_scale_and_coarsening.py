"""Spike 16: Neural width-coarsening (H-D), n=8 alignment (H-A), longer XOR6 grokking (H-C),
depth-3 vs depth-2 separation + parity4>=5 CP-SAT check (H-E / Bounds), and multi-output
ur_compiler benchmark. Uses JAX + OR-Tools via isolated extras venv; UNTRUSTED empirics."""

from __future__ import annotations

import json
import math
import pathlib
import sys
import time
from typing import Any

import jax
import jax.numpy as jnp
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import netsolve, ur_compiler  # noqa: E402


def _all_bits(n: int) -> np.ndarray:
    idx = np.arange(1 << n, dtype=np.int32)[:, None]
    shifts = np.arange(n, dtype=np.int32)[None, :]
    return ((idx >> shifts) & 1).astype(np.float32)


def _r2_linear_probe(H: np.ndarray, target: np.ndarray) -> float:
    """Least-squares R^2 of predicting binary `target` from hidden activations `H`."""
    y = target.astype(np.float64)
    var_y = float(np.var(y))
    if var_y < 1e-12:
        return 1.0
    X = np.concatenate([H.astype(np.float64), np.ones((H.shape[0], 1), dtype=np.float64)], axis=1)
    coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ coef
    mse = float(np.mean((y - pred) ** 2))
    return max(0.0, 1.0 - mse / var_y)


def _max_unit_corr(H: np.ndarray, target: np.ndarray) -> float:
    y = target.astype(np.float64)
    y = y - y.mean()
    yn = np.linalg.norm(y)
    if yn < 1e-12:
        return 0.0
    best = 0.0
    for j in range(H.shape[1]):
        h = H[:, j].astype(np.float64)
        h = h - h.mean()
        hn = np.linalg.norm(h)
        if hn > 1e-12:
            c = abs(float(np.dot(h, y) / (hn * yn)))
            if c > best:
                best = c
    return best


def run_part_a_hd_n8() -> dict[str, Any]:
    """H-D & H-A at n=8: low-rank factored function compiled vs JAX MLPs of width 4..32."""
    vars8 = [f"x{i}" for i in range(8)]

    def enc_bit(e: dict[str, int]) -> int:
        return int(e["x0"] ^ e["x1"] ^ e["x2"] ^ e["x3"])

    def fn8(e: dict[str, int]) -> int:
        c = enc_bit(e)
        g = (e["x4"] | e["x5"]) ^ (e["x6"] & e["x7"])
        return int(c & g)

    t0 = time.perf_counter()
    comp = ur_compiler.compile_profile_factored(vars8, fn8)
    ur_dt = time.perf_counter() - t0
    X_np = _all_bits(8)
    y_np = np.array([fn8({vars8[j]: int(row[j]) for j in range(8)}) for row in X_np], dtype=np.float32)
    c_np = np.array([enc_bit({vars8[j]: int(row[j]) for j in range(8)}) for row in X_np], dtype=np.float32)

    X_j = jnp.array(X_np * 2.0 - 1.0)
    y_j = jnp.array(y_np)

    widths = [4, 8, 16, 32]
    seeds = [0, 1, 2, 3, 4]
    width_stats: dict[str, Any] = {}

    for W in widths:
        accs = []
        unit_corrs = []
        probe_r2s = []

        def _loss(p):
            h = jnp.tanh(X_j @ p["W1"] + p["b1"])
            logits = (h @ p["W2"] + p["b2"]).squeeze(-1)
            bce = jnp.mean(jnp.maximum(logits, 0.0) - logits * y_j + jnp.log1p(jnp.exp(-jnp.abs(logits))))
            reg = 1e-4 * (jnp.sum(p["W1"] ** 2) + jnp.sum(p["W2"] ** 2))
            return bce + reg

        val_grad = jax.value_and_grad(_loss)

        @jax.jit
        def run_800(params):
            lr, b1_c, b2_c, eps = 0.03, 0.9, 0.999, 1e-8
            m0 = jax.tree.map(jnp.zeros_like, params)
            v0 = jax.tree.map(jnp.zeros_like, params)

            def body(step_0, carry):
                p, m, v = carry
                step = step_0 + 1
                _, g = val_grad(p)
                m = jax.tree.map(lambda mi, gi: b1_c * mi + (1.0 - b1_c) * gi, m, g)
                v = jax.tree.map(lambda vi, gi: b2_c * vi + (1.0 - b2_c) * (gi * gi), v, g)
                m_hat = jax.tree.map(lambda mi: mi / (1.0 - b1_c ** step), m)
                v_hat = jax.tree.map(lambda vi: vi / (1.0 - b2_c ** step), v)
                p = jax.tree.map(lambda pi, mh, vh: pi - lr * mh / (jnp.sqrt(vh) + eps), p, m_hat, v_hat)
                return (p, m, v)

            p_f, _, _ = jax.lax.fori_loop(0, 800, body, (params, m0, v0))
            h = jnp.tanh(X_j @ p_f["W1"] + p_f["b1"])
            logits = (h @ p_f["W2"] + p_f["b2"]).squeeze(-1)
            return h, logits

        for seed in seeds:
            key = jax.random.PRNGKey(100 * W + seed)
            k1, k2 = jax.random.split(key)
            params = {
                "W1": jax.random.normal(k1, (8, W)) * (1.0 / math.sqrt(8)),
                "b1": jnp.zeros((W,)),
                "W2": jax.random.normal(k2, (W, 1)) * (1.0 / math.sqrt(W)),
                "b2": jnp.zeros((1,)),
            }
            h_j, logits_j = run_800(params)
            h_np = np.array(h_j)
            pred_np = (np.array(logits_j) >= 0.0).astype(np.float32)
            accs.append(float(np.mean(pred_np == y_np)))
            unit_corrs.append(_max_unit_corr(h_np, c_np))
            probe_r2s.append(_r2_linear_probe(h_np, c_np))

        width_stats[str(W)] = {
            "acc_mean": float(np.mean(accs)),
            "acc_min": float(np.min(accs)),
            "acc_max": float(np.max(accs)),
            "max_unit_corr_mean": float(np.mean(unit_corrs)),
            "subspace_probe_r2_mean": float(np.mean(probe_r2s)),
        }

    return {
        "ur_compiler": {
            "decomposed": comp["decomposed"],
            "profile_rank": comp["profile_rank"],
            "circuit_cost": comp["circuit_cost"],
            "atlas_min_neurons": comp["atlas_min_neurons"],
            "tnet_nodes": len(comp["threshold_net"]["nodes"]) if comp["threshold_net"] else None,
            "time_s": round(ur_dt, 4),
        },
        "mlp_widths": width_stats,
    }


def run_part_b_hc_xor6() -> dict[str, Any]:
    """H-C longer-horizon check on XOR6 (n=6, 64 inputs): 32 vs 48 train split, 3000 steps."""
    X_np = _all_bits(6)
    y_np = (np.sum(X_np, axis=1).astype(np.int32) % 2).astype(np.float32)
    X_full = jnp.array(X_np * 2.0 - 1.0)
    y_full = jnp.array(y_np)

    def _loss_b(p, X_b, y_b, wd):
        h = jnp.tanh(X_b @ p["W1"] + p["b1"])
        logits = (h @ p["W2"] + p["b2"]).squeeze(-1)
        bce = jnp.mean(jnp.maximum(logits, 0.0) - logits * y_b + jnp.log1p(jnp.exp(-jnp.abs(logits))))
        return bce + 0.5 * wd * (jnp.sum(p["W1"] ** 2) + jnp.sum(p["W2"] ** 2))

    val_grad_b = jax.value_and_grad(_loss_b)

    @jax.jit
    def run_250(params, m, v, start_step, X_b, y_b, wd):
        lr, b1_c, b2_c, eps = 0.02, 0.9, 0.999, 1e-8

        def body(offset, carry):
            p, mi_c, vi_c = carry
            step = start_step + offset + 1
            _, g = val_grad_b(p, X_b, y_b, wd)
            mi_c = jax.tree.map(lambda a, b: b1_c * a + (1.0 - b1_c) * b, mi_c, g)
            vi_c = jax.tree.map(lambda a, b: b2_c * a + (1.0 - b2_c) * (b * b), vi_c, g)
            m_hat = jax.tree.map(lambda a: a / (1.0 - b1_c ** step), mi_c)
            v_hat = jax.tree.map(lambda a: a / (1.0 - b2_c ** step), vi_c)
            p = jax.tree.map(lambda a, mh, vh: a - lr * mh / (jnp.sqrt(vh) + eps), p, m_hat, v_hat)
            return (p, mi_c, vi_c)

        return jax.lax.fori_loop(0, 250, body, (params, m, v))

    eval_fn = jax.jit(lambda p, X: ((jnp.tanh(X @ p["W1"] + p["b1"]) @ p["W2"] + p["b2"]).squeeze(-1) >= 0.0).astype(jnp.float32))

    results = {}
    for n_train in (32, 48):
        for wd in (0.0, 0.01, 0.05):
            test_accs = []
            train_accs = []
            grok_steps = []
            for seed in (0, 1, 2):
                rng = np.random.default_rng(1000 * n_train + seed)
                perm = rng.permutation(64)
                tr_idx, te_idx = perm[:n_train], perm[n_train:]
                X_tr, y_tr = X_full[tr_idx], y_full[tr_idx]
                X_te, y_te = X_full[te_idx], y_full[te_idx]

                key = jax.random.PRNGKey(500 + seed)
                k1, k2 = jax.random.split(key)
                W = 64
                params = {
                    "W1": jax.random.normal(k1, (6, W)) * 0.5,
                    "b1": jnp.zeros((W,)),
                    "W2": jax.random.normal(k2, (W, 1)) * (1.0 / math.sqrt(W)),
                    "b2": jnp.zeros((1,)),
                }
                m = jax.tree.map(jnp.zeros_like, params)
                v = jax.tree.map(jnp.zeros_like, params)
                first_grok = None
                for chunk in range(12):
                    params, m, v = run_250(params, m, v, chunk * 250, X_tr, y_tr, wd)
                    te_a = float(jnp.mean(eval_fn(params, X_te) == y_te))
                    if te_a >= 0.95 and first_grok is None:
                        first_grok = (chunk + 1) * 250
                tr_a = float(jnp.mean(eval_fn(params, X_tr) == y_tr))
                te_a = float(jnp.mean(eval_fn(params, X_te) == y_te))
                train_accs.append(tr_a)
                test_accs.append(te_a)
                grok_steps.append(first_grok)

            results[f"n{n_train}_wd{wd}"] = {
                "train_acc_mean": float(np.mean(train_accs)),
                "test_acc_mean": float(np.mean(test_accs)),
                "test_acc_max": float(np.max(test_accs)),
                "grok_steps": grok_steps,
            }
    return results


def _to_bitmask(fn, n: int) -> int:
    mask = 0
    for m in range(1 << n):
        x = [(m >> j) & 1 for j in range(n)]
        if fn(x):
            mask |= 1 << m
    return mask


def run_part_c_he_and_bounds() -> dict[str, Any]:
    """H-E depth-3 vs depth-2 separation via OR-Tools CP-SAT + parity4>=5 CP-SAT check."""
    p4_mask = _to_bitmask(lambda x: x[0] ^ x[1] ^ x[2] ^ x[3], 4)

    t0 = time.perf_counter()
    p4_d2_w3 = netsolve.solve(p4_mask, 4, netsolve.layered(4, [3, 1]), W=4, time_limit=25.0, workers=2)
    p4_dt = time.perf_counter() - t0

    # H-E test on parity5: binary carry-subtract cascade computes parity5 in 3 chained neurons (depth-3),
    # whereas depth-2 [3, 1] (4 neurons) and [4, 1] (5 neurons) are tested with CP-SAT!
    p5_mask = _to_bitmask(lambda x: x[0] ^ x[1] ^ x[2] ^ x[3] ^ x[4], 5)

    t1 = time.perf_counter()
    p5_chain3 = netsolve.solve(p5_mask, 5, netsolve.chain(5, 3), W=4, time_limit=20.0, workers=2)
    p5_c3_dt = time.perf_counter() - t1

    t2 = time.perf_counter()
    p5_d3_w2 = netsolve.solve(p5_mask, 5, netsolve.layered(5, [2, 2, 1], skip=True), W=4, time_limit=20.0, workers=2)
    p5_d3_dt = time.perf_counter() - t2

    t3 = time.perf_counter()
    p5_d2_w3 = netsolve.solve(p5_mask, 5, netsolve.layered(5, [3, 1]), W=4, time_limit=25.0, workers=2)
    p5_d2_w3_dt = time.perf_counter() - t3

    t4 = time.perf_counter()
    p5_d2_w4 = netsolve.solve(p5_mask, 5, netsolve.layered(5, [4, 1]), W=4, time_limit=25.0, workers=2)
    p5_d2_w4_dt = time.perf_counter() - t4

    return {
        "parity4_depth2_3_1_W4": {"status": p4_d2_w3[0], "dt_s": round(p4_dt, 3)},
        "parity5_chain3_W4": {"status": p5_chain3[0], "dt_s": round(p5_c3_dt, 3), "witness": p5_chain3[1]},
        "parity5_depth3_2_2_1_skip_W4": {"status": p5_d3_w2[0], "dt_s": round(p5_d3_dt, 3)},
        "parity5_depth2_3_1_W4": {"status": p5_d2_w3[0], "dt_s": round(p5_d2_w3_dt, 3)},
        "parity5_depth2_4_1_W4": {"status": p5_d2_w4[0], "dt_s": round(p5_d2_w4_dt, 3)},
    }


def run_part_d_ur_benchmark() -> dict[str, Any]:
    """Multi-output shared-encoder LTS (n=10..12 exact) & n=16 CEGAR policy benchmark."""
    # Exact 10-var (64 states, 16 actions) multi-output coupled Markov/LTS step
    # State transitions & 3 outputs share 1-bit state class parity(s0..s5) & parity(a0..a3)
    vars10 = [f"s{i}" for i in range(6)] + [f"a{i}" for i in range(4)]

    def s_cls(e):
        return e["s0"] ^ e["s1"] ^ e["s2"] ^ e["s3"] ^ e["s4"] ^ e["s5"]

    def a_cls(e):
        return (e["a0"] & e["a1"]) ^ (e["a2"] | e["a3"])

    fns10 = {
        "out_brake": lambda e: s_cls(e) & a_cls(e),
        "out_left": lambda e: s_cls(e) ^ e["a0"],
        "out_right": lambda e: (1 - s_cls(e)) & (e["a1"] | e["a2"]),
    }

    t0 = time.perf_counter()
    indep = {nm: ur_compiler.compile_profile_factored(vars10, fn) for nm, fn in fns10.items()}
    indep_dt = time.perf_counter() - t0
    indep_cost = sum(v["circuit_cost"]["gates"] for v in indep.values())
    indep_depth = max(v["circuit_cost"]["depth"] for v in indep.values())
    indep_tnet_nodes = sum(len(v["threshold_net"]["nodes"]) for v in indep.values() if v.get("threshold_net"))

    t1 = time.perf_counter()
    shared = ur_compiler.compile_multi_profile_factored(vars10, fns10)
    shared_dt = time.perf_counter() - t1
    shared_out_cost = sum(v["circuit_cost"]["gates"] for v in shared["outputs"].values())
    shared_depth = max(v["circuit_cost"]["depth"] for v in shared["outputs"].values())
    enc_nodes = sum(len(e["threshold_net"]["nodes"]) for e in shared["encoders"] if e.get("threshold_net")) if shared["encoders"] else 0
    dec_nodes = sum(
        len(v["children"][-1]["threshold_net"]["nodes"])
        for v in shared["outputs"].values()
        if v.get("children") and v["children"][-1].get("threshold_net")
    )

    # n=16 AST CEGAR benchmark
    vars16 = [f"x{i}" for i in range(16)]
    p_l = ["xor", ["xor", ["var", "x0"], ["var", "x1"]], ["xor", ["var", "x2"], ["var", "x3"]]]
    p_r = ["xor", ["xor", ["var", "x8"], ["var", "x9"]], ["xor", ["var", "x10"], ["var", "x11"]]]
    expr16 = {"kind": "expr", "body": ["and", ["and", p_l, ["or", ["var", "x4"], ["var", "x5"]]], ["xor", p_r, ["and", ["var", "x12"], ["var", "x13"]]]]}

    def fn16(e):
        l = (e["x0"] ^ e["x1"] ^ e["x2"] ^ e["x3"]) & (e["x4"] | e["x5"])
        r = (e["x8"] ^ e["x9"] ^ e["x10"] ^ e["x11"]) ^ (e["x12"] & e["x13"])
        return int(l & r)

    t2 = time.perf_counter()
    c16 = ur_compiler.compile_profile_factored(vars16, fn16, expr_ast=expr16)
    c16_dt = time.perf_counter() - t2

    return {
        "n10_multi_output": {
            "indep_dt_s": round(indep_dt, 3),
            "indep_total_circuit_gates": indep_cost,
            "indep_max_depth": indep_depth,
            "indep_total_tnet_nodes": indep_tnet_nodes,
            "shared_encoder": shared["shared_encoder"],
            "shared_rank": shared["profile_rank"],
            "shared_dt_s": round(shared_dt, 3),
            "shared_total_circuit_gates": shared_out_cost,
            "shared_max_depth": shared_depth,
            "shared_encoder_neurons": enc_nodes,
            "shared_decoder_neurons": dec_nodes,
            "shared_dedup_neurons": enc_nodes + dec_nodes,
        },
        "n16_cegar": {
            "decomposed": c16["decomposed"],
            "profile_rank": c16["profile_rank"],
            "soundness": c16["soundness"],
            "circuit_cost": c16["circuit_cost"],
            "atlas_min_neurons": c16["atlas_min_neurons"],
            "dt_s": round(c16_dt, 3),
        },
    }


def main() -> None:
    out_path = ROOT / "experiments" / "results" / "spike16_scale_and_coarsening.json"
    report: dict[str, Any] = {}
    for key, fn in [
        ("part_a_hd_n8", run_part_a_hd_n8),
        ("part_b_hc_xor6", run_part_b_hc_xor6),
        ("part_c_he_and_bounds", run_part_c_he_and_bounds),
        ("part_d_ur_benchmark", run_part_d_ur_benchmark),
    ]:
        report[key] = fn()
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
