"""Spike 01 measurements.  python -m experiments.spike01

Every number here is EMPIRICAL: it describes our generators and our
(untrusted) translators on a seeded random workload, nothing more. The
workload is described in the output so the results are reproducible.
"""

from __future__ import annotations

import json
import pathlib
import random
import statistics
import time

from cerp import kernel
from cerp.bdd import normal_form
from cerp.semantics import TruthTable
from cerp.substrates import cost, random_expr, semantics
from cerp.sufficiency import minimal_sufficient_sets, project
from cerp.translate import (bdd_to_circuit, circuit_to_expr, expr_to_circuit, restrict_to_care,
                            truthtable_to_bdd)

SEED = 20261106
N = 6
VARS = [f"x{i}" for i in range(N)]
TRIALS = 300
DEPTH = 6


def q(xs):
    xs = sorted(xs)
    if not xs:
        return {}
    return {"n": len(xs), "mean": round(statistics.fmean(xs), 3), "median": xs[len(xs) // 2],
            "p10": xs[len(xs) // 10], "p90": xs[(9 * len(xs)) // 10], "min": xs[0], "max": xs[-1]}


def nontrivial_exprs(rng, k):
    out = []
    while len(out) < k:
        e = {"kind": "expr", "body": random_expr(VARS, DEPTH, rng)}
        tt = semantics(e, VARS)
        if len(tt.support()) >= 3:
            out.append(e)
    return out


def random_care(rng, kind):
    if kind.startswith("density"):
        p = float(kind.split("=")[1])
        return TruthTable.from_function(VARS, lambda env: rng.random() < p)
    # "correlated=k": k random pairwise equality constraints (redundant sensors)
    k = int(kind.split("=")[1])
    pairs = [tuple(rng.sample(VARS, 2)) for _ in range(k)]
    return TruthTable.from_function(VARS, lambda env: all(env[a] == env[b] for a, b in pairs))


def gates(art):
    return cost(art)["gates"]


def main():
    rng = random.Random(SEED)
    exprs = nontrivial_exprs(rng, TRIALS)
    res = {"workload": {"seed": SEED, "vars": N, "trials": TRIALS, "expr_depth": DEPTH,
                        "filter": "support >= 3"}}

    # E3: is the canonical form a good realization?  nf->circuit vs direct expr->circuit
    direct, canon, blow = [], [], []
    for e in exprs:
        nf = normal_form(e, VARS)
        c_direct = expr_to_circuit(e, VARS)
        direct.append(gates(c_direct))
        canon.append(gates(bdd_to_circuit(nf, VARS)))
        # E6: losing sharing: circuit -> expr tree size vs source expr
        blow.append(cost(circuit_to_expr(c_direct))["ast_nodes"] / cost(e)["ast_nodes"])
    ratio = [c / d for c, d in zip(canon, direct) if d]
    res["E3_canonical_vs_direct_circuit_gates"] = {
        "direct": q(direct), "canonical": q(canon), "canonical_over_direct": q(ratio),
        "canonical_strictly_smaller_frac": round(sum(c < d for c, d in zip(canon, direct)) / len(exprs), 3),
        "canonical_strictly_larger_frac": round(sum(c > d for c, d in zip(canon, direct)) / len(exprs), 3)}
    res["E6_circuit_to_expr_size_ratio"] = q(blow)

    # E4: order sensitivity of the canonical object
    spread = []
    for e in exprs[:100]:
        sizes = []
        for _ in range(20):
            order = VARS[:]
            rng.shuffle(order)
            sizes.append(len(normal_form(e, order)["body"]["nodes"]) - 2)
        spread.append(max(sizes) / max(1, min(sizes)))
    res["E4_bdd_size_max_over_min_across_20_orders"] = q(spread)

    # E1 + E2: task restriction -> multiplicity of minimal sets, and resource gain
    e12 = {}
    for kind in ["density=0.9", "density=0.6", "density=0.3", "correlated=1", "correlated=2"]:
        multi, gain, gain_restrict, gain_best, minsize, fullsupp, verified = [], [], [], [], [], [], 0
        for e in exprs[:150]:
            f = semantics(e, VARS)
            care = random_care(rng, kind)
            if care.count() == 0:
                continue
            sets = minimal_sufficient_sets(f, care)
            multi.append(len(sets))
            minsize.append(min(len(s) for s in sets))
            fullsupp.append(len(f.support()))
            best_ext = min(gates(expr_to_circuit(e, VARS)), gates(bdd_to_circuit(normal_form(e, VARS), VARS)))
            care_art = truthtable_to_bdd(care)
            proj_best = None
            for s in sets[:4]:
                g = truthtable_to_bdd(project(f, care, s))
                c = bdd_to_circuit(g, [v for v in VARS if v in s])
                v = kernel.check({"relation": "task", "vars": VARS, "left": e, "right": c, "care": care_art})
                assert v.ok, "task realization failed kernel check"  # would be a real bug
                verified += 1
                proj_best = gates(c) if proj_best is None else min(proj_best, gates(c))
            rc = bdd_to_circuit(restrict_to_care(f, care), VARS)
            assert kernel.check({"relation": "task", "vars": VARS, "left": e, "right": rc, "care": care_art}).ok
            verified += 1
            denom = best_ext or 1
            gain.append(proj_best / denom)
            gain_restrict.append(gates(rc) / denom)
            gain_best.append(min(proj_best, gates(rc), best_ext) / denom)
        e12[kind] = {
            "tasks": len(multi),
            "frac_with_multiple_minimal_sets": round(sum(m > 1 for m in multi) / len(multi), 3),
            "num_minimal_sets": q(multi),
            "min_sufficient_size": q(minsize), "full_support_size": q(fullsupp),
            "gate_ratio_vs_best_exact": {"naive_projection": q(gain), "restrict": q(gain_restrict),
                                         "best_of_all_incl_exact": q(gain_best)},
            "frac_strict_improvement": {
                "naive_projection": round(sum(g < 1 for g in gain) / len(gain), 3),
                "restrict": round(sum(g < 1 for g in gain_restrict) / len(gain), 3),
                "best_of_all_incl_exact": round(sum(g < 1 for g in gain_best) / len(gain), 3)},
            "frac_worse_than_exact": {
                "naive_projection": round(sum(g > 1 for g in gain) / len(gain), 3),
                "restrict": round(sum(g > 1 for g in gain_restrict) / len(gain), 3)},
            "kernel_verified_task_realizations": verified}
    res["E1_E2_task_restriction"] = e12

    # E5: exhaustive kernel scaling
    scale = {}
    for n in range(8, 17, 2):
        vs = [f"y{i}" for i in range(n)]
        e = {"kind": "expr", "body": random_expr(vs, 8, random.Random(n))}
        c = expr_to_circuit(e, vs)
        t0 = time.perf_counter()
        kernel.check({"relation": "extensional", "vars": vs, "left": e, "right": c})
        scale[n] = round(time.perf_counter() - t0, 4)
    res["E5_kernel_seconds_by_n"] = scale
    t16 = scale[16]
    res["E5_extrapolated_seconds"] = {"n=24": round(t16 * 2 ** 8), "n=32": round(t16 * 2 ** 16),
                                      "n=64 (years)": f"{t16 * 2 ** 48 / 3.15e7:.1e}"}

    out = pathlib.Path(__file__).parent / "results" / "spike01.json"
    out.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
