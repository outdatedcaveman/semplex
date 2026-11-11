"""Spike 09: do trained networks land on the atlas's optimal circuits?

  python -m experiments.spike09        (~15 min on 4 CPUs)

E1  every 4-input element, fully specified: which circuit does training find?
E2  partially specified tasks: which COMPLETION does training choose, and is it
    the cheapest one in the table (the compiler's choice)?
"""

from __future__ import annotations

import json
import pathlib
import random
import time
from collections import Counter, defaultdict

import numpy as np

from cerp import atlas, train

ROOT = pathlib.Path(__file__).resolve().parent.parent
H = 8
WDS = (0.0, 0.03, 0.1)
CHECKPOINTS = (100, 300, 1000, 3000, 6000)
SEEDS_E1, SEEDS_E2 = 10, 5


def tgt(fs):
    return np.array([[(int(f) >> x) & 1 for x in range(16)] for f in fs], dtype=np.float64)


def wstar_table(tb):
    """Minimum number of threshold functions that determine g, for every 4-input g."""
    L = np.array(sorted(tb.ltf), dtype=np.int64)
    x2 = np.zeros(65536, dtype=bool)
    x2[(L[:, None] ^ L[None, :]).reshape(-1)] = True
    w = np.where(tb.hi == 1, 1, np.where((tb.hi == 3) | x2, 2, np.where(tb.hi == 5, 4, 3)))
    w[0] = w[65535] = 0
    return w, x2


def main():
    t0 = time.time()
    tables = atlas.build_all(4)
    tb = tables[4]
    wstar, x2 = wstar_table(tb)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    res = {"hidden_units": H, "weight_decays": list(WDS)}

    # theory check left open by Spike 08: is neurons = w* + 1 at 4 inputs?
    four = [e for e in ex if tb.hi[e] == 4]
    res["n4_classes_at_4_neurons"] = len(four)
    res["n4_classes_at_4_neurons_that_are_xor_of_two_neurons"] = int(sum(bool(x2[e]) for e in four))

    # ---------------- E1
    e1 = {}
    for wd in WDS:
        fs = np.array(ex * SEEDS_E1)
        rng = np.random.default_rng(900 + int(wd * 1000))
        p = train.init(len(fs), H, rng)
        T, C = tgt(fs), np.ones((len(fs), 16))
        state, done, traj = None, 0, {}
        for cp in CHECKPOINTS:
            p, state = train.train(p, T, C, cp - done, wd=wd, state=state)
            done = cp
            g, faithful, units = train.read_circuits(p)
            fit = g == fs
            exc = [train.effective_width(units[i], int(g[i]))[0] - int(wstar[g[i]]) for i in np.nonzero(fit)[0]]
            traj[cp] = {"fit": round(float(fit.mean()), 4), "mean_excess_width": round(float(np.mean(exc)), 3),
                        "frac_minimal": round(float(np.mean(np.array(exc) == 0)), 3)}
        by_w, isomers, uniq_units = defaultdict(list), defaultdict(list), []
        for i in np.nonzero(fit)[0]:
            k, iso = train.effective_width(units[i], int(g[i]))
            by_w[int(wstar[g[i]])].append(k - int(wstar[g[i]]))
            isomers[int(fs[i])].append(iso)
            uniq_units.append(len({min(int(u), 65535 ^ int(u)) for u in units[i]} - {0}))
        distinct = [len(set(v)) for v in isomers.values() if len(v) == SEEDS_E1]
        e1[str(wd)] = {
            "trajectory": traj, "faithful_when_fit": round(float(faithful[fit].mean()), 4),
            "mean_distinct_hidden_functions": round(float(np.mean(uniq_units)), 2),
            "by_minimum_width": {k: {"nets": len(v), "frac_minimal": round(float(np.mean(np.array(v) == 0)), 3),
                                     "mean_excess": round(float(np.mean(v)), 3)} for k, v in sorted(by_w.items())},
            "tasks_with_all_seeds_fit": len(distinct),
            "mean_distinct_circuits_per_task": round(float(np.mean(distinct)), 2),
            "tasks_where_every_seed_found_the_same_circuit": int(sum(d == 1 for d in distinct)),
            "tasks_where_every_seed_found_a_different_circuit": int(sum(d == SEEDS_E1 for d in distinct))}
        print("E1", wd, json.dumps(e1[str(wd)]), flush=True)
    res["E1_full_tasks"] = e1

    # ---------------- E2
    rnd = random.Random(92)
    tasks = []
    for e in ex:
        for size in (12, 8):
            for _ in range(3):
                care = sum(1 << x for x in rnd.sample(range(16), size))
                comps = [e & care]
                for x in range(16):
                    if not (care >> x) & 1:
                        comps += [c | (1 << x) for c in comps]
                costs = tb.hi[np.array(comps)]
                tasks.append({"f": e, "care": care, "size": size, "min": int(costs.min()),
                              "chance_optimal": float((costs == costs.min()).mean()), "random_mean": float(costs.mean())})
    e2 = {}
    for wd in WDS:
        fs = np.array([t["f"] for t in tasks] * SEEDS_E2)
        cs = np.array([t["care"] for t in tasks] * SEEDS_E2)
        rng = np.random.default_rng(1900 + int(wd * 1000))
        p = train.init(len(fs), H, rng)
        p, _ = train.train(p, tgt(fs), tgt(cs), 4000, wd=wd)
        g, _, _ = train.read_circuits(p)
        fit = (g & cs) == (fs & cs)
        out = {}
        for size in (12, 8):
            idx = [i for i in np.nonzero(fit)[0] if tasks[i % len(tasks)]["size"] == size]
            tk = [tasks[i % len(tasks)] for i in idx]
            learned = tb.hi[g[idx]]
            out[size] = {"nets_fit": len(idx),
                         "fit_rate": round(len(idx) / (len(fs) // 2), 4),
                         "frac_learned_completion_is_cheapest": round(float(np.mean(learned == [t["min"] for t in tk])), 3),
                         "chance_level": round(float(np.mean([t["chance_optimal"] for t in tk])), 3),
                         "mean_neurons_learned": round(float(learned.mean()), 3),
                         "mean_neurons_cheapest": round(float(np.mean([t["min"] for t in tk])), 3),
                         "mean_neurons_random_completion": round(float(np.mean([t["random_mean"] for t in tk])), 3)}
        e2[str(wd)] = out
        print("E2", wd, json.dumps(out), flush=True)
    res["E2_partial_tasks"] = e2
    res["wall_seconds"] = round(time.time() - t0, 1)
    (ROOT / "experiments" / "results" / "spike09.json").write_text(json.dumps(res, indent=1))
    print("done", res["wall_seconds"], "s; 4-neuron classes that are XOR of two neurons:",
          res["n4_classes_at_4_neurons_that_are_xor_of_two_neurons"], "of", res["n4_classes_at_4_neurons"])


if __name__ == "__main__":
    main()
