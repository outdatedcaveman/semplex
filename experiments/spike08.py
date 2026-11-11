"""Spike 08: the periodic table of threshold circuits (n <= 4) and compiler v1.

  python -m experiments.spike08        (~2 min)

Writes atlas/PERIODIC_TABLE_n3.md, atlas/table_n4.json and results/spike08.json.
"""

from __future__ import annotations

import json
import pathlib
import random
import time
from collections import Counter

import numpy as np

from cerp import atlas, kernel

ROOT = pathlib.Path(__file__).resolve().parent.parent


def named3():
    v = lambda j: sum(1 << i for i in range(8) if (i >> j) & 1)
    a, b, c, F = v(0), v(1), v(2), 255
    return {
        "constant": 0, "x0 (projection)": a, "AND2": a & b, "XOR2": a ^ b, "AND3": a & b & c,
        "MAJ3 (majority)": (a & b) | (a & c) | (b & c), "XOR3 (parity)": a ^ b ^ c,
        "MUX (x0 ? x1 : x2)": (a & b) | (~a & c & F), "x0 AND (x1 OR x2)": a & (b | c),
        "x0 AND (x1 XOR x2)": a & (b ^ c), "(x0 AND x1) XOR x2": (a & b) ^ c,
        "exactly-one-of-3": sum(1 << i for i in (1, 2, 4)), "all-equal (x0=x1=x2)": 1 | 128,
        "exactly-two-of-3": sum(1 << i for i in (3, 5, 6)),
    }


def verify(tables, m, f):
    art = atlas.artifact(tables, m, f)
    v = kernel.check({"relation": "extensional", "vars": atlas.names(m), "left": art,
                      "right": atlas.table_artifact(m, f)})
    layers = art["body"]["layers"]
    return v.ok and sum(atlas.shape(layers)) == int(tables[m].hi[f]), layers


def main():
    t0 = time.time()
    tables = atlas.build_all(4)
    res = {"build_seconds": round(time.time() - t0, 1), "tables": {}}

    for m in (2, 3, 4):
        tb = tables[m]
        rows, ok_all, maxw = [], True, 0
        for c in tb.classes():
            e = tb.exhibit[c]
            ok, layers = verify(tables, m, e)
            ok_all &= ok
            maxw = max(maxw, max(abs(v) for l in layers for n in l for v in n["w"]))
            rows.append({"class_rep": c, "exhibit": e, "members": int((tb.canon == c).sum()),
                         "neurons_lo": int(tb.lo[e]), "neurons_hi": int(tb.hi[e]), "depth": int(tb.depth[e]),
                         "shape": list(atlas.shape(layers)), "kernel_verified": bool(ok), "net": layers})
        # symmetry transport: random members of every class, not just exhibits
        rng = random.Random(8)
        sample = range(len(tb.hi)) if m < 4 else [rng.randrange(65536) for _ in range(2000)]
        transport_ok = all(verify(tables, m, f)[0] for f in sample)
        res["tables"][m] = {
            "threshold_functions": len(tb.ltf), "weight_magnitude_for_single_neurons": tb.W,
            "classes": len(rows), "all_class_witnesses_kernel_verified": bool(ok_all),
            "transported_witnesses_checked": len(sample), "transported_all_ok": bool(transport_ok),
            "max_abs_weight_in_witnesses": int(maxw),
            "functions_by_neurons": {int(k): int(v) for k, v in zip(*np.unique(tb.hi, return_counts=True))},
            "classes_by_neurons": dict(Counter(r["neurons_hi"] for r in rows)),
            "exact_classes": sum(r["neurons_lo"] == r["neurons_hi"] for r in rows),
            "one_bit_flip_cost_change": atlas.hamming_landscape(tb)}
        print(m, {k: v for k, v in res["tables"][m].items()}, flush=True)
        if m == 4:
            (ROOT / "atlas").mkdir(exist_ok=True)
            (ROOT / "atlas" / "table_n4.json").write_text(json.dumps(rows))
        if m == 3:
            rows3 = rows

    # n = 3 periodic table with Protocol-Frame data (minimal determining layers)
    tb = tables[3]
    nm = {int(tb.canon[b]): k for k, b in named3().items()}
    lines = ["# Periodic table of 3-input threshold circuits", "",
             "Family: strictly layered threshold networks (see `cerp/atlas.py`). One row per NPN class "
             "(14 classes cover all 256 functions). Every witness net is kernel-verified; every neuron "
             "count is exact (all first layers of width <= 3 were enumerated).", "",
             "| Period (neurons) | Element | Truth table | Functions in class | Shape | Min. determining width w* | "
             "Distinct minimal first layers | Witness (weights; threshold per neuron) |",
             "|---|---|---|---|---|---|---|---|"]
    pf = []
    for r in sorted(rows3, key=lambda r: (r["neurons_hi"], r["class_rep"])):
        w, k = atlas.min_determining_layers(tb, r["exhibit"])
        pf.append({"class": r["class_rep"], "neurons": r["neurons_hi"], "wstar": w, "isomers": k})
        net = "; ".join(" ".join(f"{n['w']}>={n['t']}" for n in layer) for layer in r["net"])
        lines.append(f"| {r['neurons_hi']} | {nm.get(r['class_rep'], '(unnamed)')} | 0x{r['exhibit']:02x} | "
                     f"{r['members']} | {tuple(r['shape'])} | {w} | {k} | `{net}` |")
    (ROOT / "atlas" / "PERIODIC_TABLE_n3.md").write_text("\n".join(lines) + "\n")
    res["n3_protocol_frame"] = pf
    res["n3_wstar_plus_one_equals_neurons"] = all(
        p["neurons"] == p["wstar"] + 1 for p in pf if p["neurons"] > 1)
    print("n3 PF", pf, flush=True)

    # compiler v1: random tasks on 4 inputs
    rng = random.Random(88)
    tb = tables[4]
    comp = {}
    for density in (0.9, 0.75, 0.5, 0.25):
        saved, exact_cost, task_cost, optimal, verified, n = 0, 0, 0, 0, 0, 300
        for _ in range(n):
            f = rng.randrange(65536)
            care = sum(1 << i for i in range(16) if rng.random() < density) or 1
            r = atlas.compile_task(tables, 4, f, care)
            v = kernel.check({"relation": "task", "vars": atlas.names(4), "left": r["net"],
                              "right": atlas.table_artifact(4, f), "care": atlas.table_artifact(4, care)})
            verified += v.ok
            optimal += r["optimal"]
            exact_cost += r["exact_neurons"]
            task_cost += r["neurons"]
            saved += r["neurons"] < r["exact_neurons"]
        comp[density] = {"tasks": n, "kernel_verified": verified, "certified_optimal": optimal,
                         "mean_neurons_exact": round(exact_cost / n, 3), "mean_neurons_task": round(task_cost / n, 3),
                         "frac_cheaper_than_exact": round(saved / n, 3)}
        print("compile", density, comp[density], flush=True)
    res["compiler_n4"] = comp
    res["wall_seconds"] = round(time.time() - t0, 1)
    (ROOT / "experiments" / "results" / "spike08.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
