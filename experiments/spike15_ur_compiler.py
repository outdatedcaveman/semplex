"""Spike 15: Ur-Compiler compositional C4 profile-factorization benchmark (H-G, H-H)."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cerp import ur_compiler
from cerp.semantics import TruthTable
from cerp.translate import bdd_to_expr, truthtable_to_bdd

OUT = ROOT / "experiments" / "results" / "spike15_ur_compiler.json"


def bench_fn(name: str, vars_list: list[str], fn):
    t0 = time.time()
    comp = ur_compiler.compile_profile_factored(vars_list, fn, max_leaf=4)
    comp_time = time.time() - t0
    comp_gates = comp["circuit_cost"]["gates"]

    t1 = time.time()
    tt = TruthTable.from_function(vars_list, fn)
    flat_expr = bdd_to_expr(truthtable_to_bdd(tt))
    flat_time = time.time() - t1
    flat_gates = ur_compiler.expr_gate_count(flat_expr["body"])

    return {
        "name": name,
        "n_vars": len(vars_list),
        "decomposed": comp["decomposed"],
        "profile_rank": comp["profile_rank"],
        "compositional_gates": comp_gates,
        "flat_bdd_gates": flat_gates,
        "gate_ratio_comp_over_flat": round(comp_gates / max(1, flat_gates), 3),
        "atlas_neuron_ub": comp["atlas_min_neurons"],
        "comp_time_s": round(comp_time, 4),
        "flat_time_s": round(flat_time, 4),
    }


def main():
    v6 = [f"x{i}" for i in range(6)]
    v8 = [f"x{i}" for i in range(8)]
    v10 = [f"x{i}" for i in range(10)]

    benchmarks = [
        bench_fn("parity_6", v6, lambda e: sum(e[v] for v in v6) & 1),
        bench_fn("parity_8", v8, lambda e: sum(e[v] for v in v8) & 1),
        bench_fn("hier_thresh_8", v8, lambda e: int((sum(e[f"x{i}"] for i in range(4)) >= 2) ^ (sum(e[f"x{i}"] for i in range(4, 8)) >= 3))),
        bench_fn("block_maj_10", v10, lambda e: int(
            ((sum(e[f"x{i}"] for i in range(4)) >= 2) + (sum(e[f"x{i}"] for i in range(4, 8)) >= 2) + (e["x8"] & e["x9"])) >= 2
        )),
    ]
    res = {"benchmarks": benchmarks}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
