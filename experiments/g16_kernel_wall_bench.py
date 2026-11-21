"""G16 benchmark: reflected opaque-theorem bitmask LRAT in Lean 4 kernel (`native=False`).

Pre-registered benchmark comparing G16's reflected bitmask LRAT proof engine
(`bm_base_sound` + `bm_rup_sound` + `bm_empty_false` in `proofs/lean/Cerp.lean`,
standard axioms only, zero `Lean.ofReduceBool`) against G10 across all 15
`experiments/g10_miter_bench.py` configurations.
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

from cerp import lean_bridge, sat
from experiments import g10_miter_bench as G10

TIMEOUT_SEC = 150.0


def _profile_reflected_stages(net, expr_d, vs, lrat_steps, lib_dir, timeout_s=TIMEOUT_SEC):
    """Break down Lean check time into base MTree `rfl` vs full reflected LRAT verification."""
    body = lean_bridge._render_reflected_tnet_body(net, expr_d, vs, lrat_steps, "g16_stage")
    lines = body.splitlines()
    # Keep header + baseMT + base_eq for `base_rfl` check
    base_eq_idx = next(i for i, ln in enumerate(lines) if ln.startswith("theorem base_eq"))
    ns_line = next(ln for ln in lines if ln.startswith("namespace "))
    ns_name = ns_line.split()[1]
    base_only_src = (
        "import Cerp\nopen Cerp\nset_option maxRecDepth 200000\nset_option maxHeartbeats 0\n"
        + "\n".join(lines[: base_eq_idx + 1])
        + f"\nend {ns_name}\n"
    )
    full_src = (
        "import Cerp\nopen Cerp\nset_option maxRecDepth 200000\nset_option maxHeartbeats 0\n"
        + body
        + "\n#print axioms g16_stage\n"
    )
    lean_bin = lean_bridge.lean_binary()
    env = {**os.environ, "LEAN_PATH": str(lib_dir)}
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        for sname, src in (("base_eq_rfl", base_only_src), ("full_verify", full_src)):
            f = d / f"{sname}.lean"
            f.write_text(src, encoding="utf-8")
            t0 = time.perf_counter()
            try:
                code, _ = lean_bridge._run([lean_bin, str(f)], cwd=d, timeout=timeout_s, env=env)
                out[sname] = {"status": "ok" if code == 0 else f"exit_{code}", "seconds": round(time.perf_counter() - t0, 3)}
            except subprocess.TimeoutExpired:
                out[sname] = {"status": "timeout", "seconds": round(timeout_s, 3)}
    return out


def main():
    orig_run = lean_bridge._run

    def _capped_run(args, cwd=None, timeout=TIMEOUT_SEC, env=None):
        return orig_run(args, cwd=cwd, timeout=TIMEOUT_SEC, env=env)

    lean_bridge._run = _capped_run

    t_warm = time.perf_counter()
    build_dir = pathlib.Path(tempfile.gettempdir()) / "cerp_lean_build"
    lib_dir = lean_bridge._library(build_dir)
    cerp_compile_sec = round(time.perf_counter() - t_warm, 3)
    print(f"Cerp.olean ready in {cerp_compile_sec}s", flush=True)

    g10_path = ROOT / "experiments" / "results" / "g10_miter_timings.json"
    g10_by_name = {}
    if g10_path.exists():
        g10_by_name = {r["name"]: r for r in json.loads(g10_path.read_text(encoding="utf-8"))["results"]}

    benchmarks = G10._build_benchmarks()
    stage_targets = {"baseline_xor4", "n6_2hidden_w2_cmp_xor", "n8_1hidden_w2_eq4", "n8_1hidden_w4_rot_or", "n8_1hidden_w8_par8"}
    results = []

    for item in benchmarks:
        name = item["name"]
        vs = item["vars"]
        net = item["net"]
        expr_d = item["expr"]
        G10._verify_truth_table(net, expr_d, vs)

        idx = sat._tnet_to_indexed_nodes(net, vs)
        mv, clauses = sat._lean_tnet_miter_pb(vs, idx, expr_d["body"])
        t0 = time.perf_counter()
        sat_status, lrat_steps, _ = sat.prove_tnet_equivalence_lrat(net, expr_d, vs, pb=True)
        sat_t = round(time.perf_counter() - t0, 4)
        assert sat_status == "unsat", f"{name} unexpected sat_status={sat_status}"
        n_hints = sum(len(h) for _, h in lrat_steps)

        t1 = time.perf_counter()
        try:
            chk, _ = lean_bridge.verify_threshold_net_equiv(
                net, expr_d, vs, lrat_steps=lrat_steps, name=f"g16_{name}", native=False, pb=True, reflected=True
            )
            lean_t = round(time.perf_counter() - t1, 3)
            lean_status = "ok" if chk.ok else "failed"
            axioms = list(chk.axioms)
        except subprocess.TimeoutExpired:
            lean_t = round(TIMEOUT_SEC, 3)
            lean_status = f"timeout_{int(TIMEOUT_SEC)}s"
            axioms = []

        g10_row = g10_by_name.get(name, {})
        rec = {
            "name": name,
            "axis": item["axis"],
            "shape": item["shape"],
            "n_inputs": len(vs),
            "nodes": len(net["nodes"]),
            "miter_vars": mv,
            "miter_clauses": len(clauses),
            "lrat_steps": len(lrat_steps),
            "lrat_hints": n_hints,
            "sat_seconds": sat_t,
            "lean_status": lean_status,
            "lean_seconds": lean_t,
            "under_120s": lean_status == "ok" and lean_t < 120.0,
            "axioms": axioms,
            "g10_lean_status": g10_row.get("lean_status"),
            "g10_lean_seconds": g10_row.get("lean_seconds"),
        }
        if name in stage_targets:
            rec["stage_breakdown"] = _profile_reflected_stages(net, expr_d, vs, lrat_steps, lib_dir)
        results.append(rec)
        print(
            f"{name:24s} steps={len(lrat_steps):3d} hints={n_hints:4d} "
            f"lean={lean_status} ({lean_t}s) [g10={g10_row.get('lean_seconds')}s] under_120s={rec['under_120s']}",
            flush=True,
        )

    by_name = {r["name"]: r for r in results}
    allowed = set(lean_bridge.ALLOWED_AXIOMS)
    all_std = all(r["lean_status"] == "ok" and set(r["axioms"]) <= allowed for r in results)
    n_under_120 = sum(1 for r in results if r["under_120s"])
    w4 = by_name["n8_1hidden_w4_rot_or"]
    par8 = by_name["n8_1hidden_w8_par8"]
    g10_timeouts = ["n8_1hidden_w3_or", "n8_1hidden_w4_rot_or", "n8_1hidden_w8_par8", "n8_1hidden_w2_nonsup_17", "n8_1hidden_w2_nonsup_5"]

    verdicts = {
        "H16.1_w4_rot_or_under_120s": bool(w4["lean_status"] == "ok" and w4["lean_seconds"] < 120.0 and set(w4["axioms"]) <= allowed),
        "H16.2_all_5_g10_timeouts_under_120s": all(
            by_name[k]["lean_status"] == "ok" and by_name[k]["lean_seconds"] < 120.0 and set(by_name[k]["axioms"]) <= allowed
            for k in g10_timeouts
        ),
        "H16.3_all_15_under_120s_std_axioms": bool(all_std and n_under_120 == len(results)),
        "H16.4_w8_par8_249_steps_under_120s": bool(par8["lean_status"] == "ok" and par8["lean_seconds"] < 120.0 and set(par8["axioms"]) <= allowed),
    }

    payload = {
        "timeout_sec": TIMEOUT_SEC,
        "cerp_compile_seconds": cerp_compile_sec,
        "n_benchmarks": len(results),
        "n_under_120s": n_under_120,
        "all_standard_axioms": all_std,
        "verdicts": verdicts,
        "results": results,
    }
    out_path = ROOT / "experiments" / "results" / "g16_kernel_wall.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Summary: {n_under_120}/{len(results)} < 120s, all_std={all_std}, verdicts={verdicts}")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
