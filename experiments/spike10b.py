"""Spike 10b: other learning rules and grokking, scored against exact ground truth.

  python -m experiments.spike10b        (~20 min on 4 CPUs)

Part A (4 inputs, exact table): do learning rules other than backpropagation share
its simplicity bias? Is that bias just the volume of weight space?
Part B (6 inputs, held-out half): when a network groks a planted simple function,
is that function a cheapest completion of its training data?
"""

from __future__ import annotations

import json
import pathlib
import random
import time

import numpy as np

from cerp import atlas, learnrules as lr, netsolve

ROOT = pathlib.Path(__file__).resolve().parent.parent
H = 8


def tgt(fs, npts=16):
    return np.array([[(int(f) >> x) & 1 for x in range(npts)] for f in fs], dtype=np.float64)


def part_a(res):
    tables = atlas.build_all(4)
    tb = tables[4]
    L = np.array(sorted(tb.ltf), dtype=np.int64)
    x2 = np.zeros(65536, dtype=bool)
    x2[(L[:, None] ^ L[None, :]).reshape(-1)] = True
    wstar = np.where(tb.hi == 1, 1, np.where((tb.hi == 3) | x2, 2, np.where(tb.hi == 5, 4, 3)))
    wstar[0] = wstar[65535] = 0
    XS = lr.inputs(4)
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    rnd = random.Random(101)
    train_cls = set(rnd.sample(range(len(ex)), len(ex) // 2))

    # partial tasks, generated exactly as in Spike 09
    rnd2 = random.Random(92)
    tasks = []
    for ci, e in enumerate(ex):
        for size in (12, 8):
            for _ in range(3):
                care = sum(1 << x for x in rnd2.sample(range(16), size))
                comps = [e & care]
                for x in range(16):
                    if not (care >> x) & 1:
                        comps += [c | (1 << x) for c in comps]
                comps = np.array(comps)
                costs = tb.hi[comps]
                tasks.append({"f": e, "care": care, "size": size, "min": int(costs.min()), "held_out": ci not in train_cls,
                              "comps": comps, "chance": float((costs == costs.min()).mean())})

    # meta-learn the local rule on the training half (full tasks + their partial tasks)
    t0 = time.time()
    mt_f = [ex[i] for i in sorted(train_cls)] + [t["f"] for t in tasks if not t["held_out"]][::3]
    mt_c = [65535] * len(train_cls) + [t["care"] for t in tasks if not t["held_out"]][::3]
    alpha, score, hist = lr.meta_learn_local(XS, tgt(mt_f), tgt(mt_c), H, np.random.default_rng(7))
    res["local_rule"] = {"coefficients": [round(float(a), 3) for a in alpha], "meta_loss": round(score, 4),
                         "best_loss_per_generation": hist, "seconds": round(time.time() - t0, 1),
                         "terms": ["error broadcast * own slope", "error-modulated Hebbian", "Hebbian",
                                   "Oja-style decay", "weight decay"]}
    print("meta-learned", res["local_rule"], flush=True)

    rules = {"backprop": {}, "feedback alignment": {"rule": "fa"}, "error broadcast (unlearned)":
             {"rule": "local", "alpha": np.array([1.0, 0, 0, 0, 0])},
             "meta-learned local rule": {"rule": "local", "alpha": alpha}, "frozen first layer": {"rule": "frozen"}}
    out = {}
    for name, kw in rules.items():
        rule = kw.get("rule", "backprop")
        r = {}
        # E1: full tasks
        fs = np.array(ex * 10)
        rng = np.random.default_rng(31)
        p = lr.init(len(fs), H, 4, rng)
        p, _ = lr.train(p, XS, tgt(fs), np.ones((len(fs), 16)), 4000, rule=rule, alpha=kw.get("alpha"),
                        fb=rng.normal(0, 0.5, (len(fs), H)))
        g, units = lr.read(p, XS)
        fit = g == fs
        exc = [lr.effective_width(units[i], int(g[i]), 16) - int(wstar[g[i]]) for i in np.nonzero(fit)[0]]
        held = np.array([(i % len(ex)) not in train_cls for i in range(len(fs))])
        r["full_tasks"] = {"fit": round(float(fit.mean()), 4), "fit_held_out_classes": round(float(fit[held].mean()), 4),
                           "frac_minimal_width": round(float(np.mean(np.array(exc) == 0)), 3)}
        # E2: partial tasks
        fs = np.array([t["f"] for t in tasks] * 5)
        cs = np.array([t["care"] for t in tasks] * 5)
        rng = np.random.default_rng(32)
        p = lr.init(len(fs), H, 4, rng)
        p, _ = lr.train(p, XS, tgt(fs), tgt(cs), 4000, rule=rule, alpha=kw.get("alpha"),
                        fb=rng.normal(0, 0.5, (len(fs), H)))
        g, _ = lr.read(p, XS)
        fit = (g & cs) == (fs & cs)
        for size in (12, 8):
            for label, want in (("all", None), ("held_out_classes", True)):
                idx = [i for i in np.nonzero(fit)[0] if tasks[i % len(tasks)]["size"] == size
                       and (want is None or tasks[i % len(tasks)]["held_out"])]
                tot = sum(1 for i in range(len(fs)) if tasks[i % len(tasks)]["size"] == size
                          and (want is None or tasks[i % len(tasks)]["held_out"]))
                learned = tb.hi[g[idx]]
                r[f"partial_{size}_{label}"] = {
                    "fit": round(len(idx) / tot, 4),
                    "frac_cheapest": round(float(np.mean(learned == [tasks[i % len(tasks)]["min"] for i in idx])), 3),
                    "mean_neurons": round(float(learned.mean()), 3)}
        out[name] = r
        print(name, json.dumps(r), flush=True)
    res["A_rules"] = out

    # volume prior: functions of random-weight networks, then exact conditioning on each task
    prior = {}
    for scale in (0.5, 2.0):
        hist = np.zeros(65536, dtype=np.int64)
        rng = np.random.default_rng(55)
        for _ in range(40):
            p = lr.init(200_000, H, 4, rng, scale=scale)
            g, _ = lr.read(p, XS)
            hist += np.bincount(g, minlength=65536)
        o = {"samples": int(hist.sum()), "functions_seen": int((hist > 0).sum()),
             "mass_on_single_neuron_functions": round(float(hist[tb.hi == 1].sum() / hist.sum()), 4)}
        for size in (12, 8):
            fr, covered, chance = [], 0, []
            for t in tasks:
                if t["size"] != size:
                    continue
                m = hist[t["comps"]]
                if m.sum() == 0:
                    continue
                covered += 1
                fr.append(float(m[tb.hi[t["comps"]] == t["min"]].sum() / m.sum()))
                chance.append(t["chance"])
            o[f"partial_{size}"] = {"tasks_with_any_sample": covered, "of": sum(t["size"] == size for t in tasks),
                                    "frac_cheapest_under_volume": round(float(np.mean(fr)), 3),
                                    "chance": round(float(np.mean(chance)), 3)}
        prior[str(scale)] = o
        print("volume prior, init scale", scale, json.dumps(o), flush=True)
    res["A_volume_prior"] = prior


def part_b(res):
    n, npts, Hb, B = 6, 64, 16, 64
    XS = lr.inputs(n)
    target = sum(1 << x for x in range(npts) if ((x >> 0) ^ (x >> 1)) & 1)        # x0 XOR x1
    tb_row = np.array([[(target >> x) & 1 for x in range(npts)]], dtype=np.float64)
    # is the planted function a cheapest completion? (no single neuron fits the training half)
    rnd = random.Random(66)
    splits = [sum(1 << x for x in rnd.sample(range(npts), 32)) for _ in range(B)]
    single = [netsolve.solve(target, n, netsolve.chain(n, 1), W=10, time_limit=60, workers=4, care=s)[0]
              for s in splits[:16]]
    res["B_setup"] = {"inputs": n, "hidden": Hb, "target": "x0 XOR x1 (3 neurons in the layered family)",
                      "train_points": 32, "single_neuron_fits_training_half": single.count("sat"),
                      "splits_checked": len(single), "solver_unknown": single.count("unknown")}
    print(res["B_setup"], flush=True)
    care = np.array([[(s >> x) & 1 for x in range(npts)] for s in splits], dtype=np.float64)
    T = np.repeat(tb_row, B, axis=0)
    out = {}
    for scale in (0.5, 3.0):
        for wd in (0.0, 0.1):
            rng = np.random.default_rng(600)
            p = lr.init(B, Hb, n, rng, scale=scale)
            first_fit = np.full(B, -1)
            first_gen = np.full(B, -1)
            curve = {}

            def cb(t, p, first_fit=first_fit, first_gen=first_gen, curve=curve):
                if t % 100:
                    return
                _, _, z = lr.forward(p, XS)
                correct = (z >= 0) == (T > 0.5)
                tr = (correct * care).sum(1) / 32
                te = (correct * (1 - care)).sum(1) / 32
                first_fit[(first_fit < 0) & (tr == 1)] = t
                first_gen[(first_gen < 0) & (te == 1) & (tr == 1)] = t
                if t in (100, 300, 1000, 3000, 10000, 30000):
                    curve[t] = [round(float(tr.mean()), 3), round(float(te.mean()), 3)]

            p, _ = lr.train(p, XS, T, care, 30000, lr=0.01, wd=wd, on_step=cb)
            g, units = lr.read(p, XS)
            exact = np.array([int(x) == target for x in g])
            widths = [lr.effective_width(units[i], int(g[i]), npts, kmax=4) for i in range(B)]
            both = (first_fit > 0) & (first_gen > 0)
            out[f"init_scale={scale}, weight_decay={wd}"] = {
                "runs": B, "fit_training_half": int((first_fit > 0).sum()),
                "ended_on_planted_function": int(exact.sum()),
                "median_step_train_fit": int(np.median(first_fit[first_fit > 0])) if (first_fit > 0).any() else None,
                "median_step_generalized": int(np.median(first_gen[first_gen > 0])) if (first_gen > 0).any() else None,
                "median_delay_ratio": round(float(np.median(first_gen[both] / first_fit[both])), 1) if both.any() else None,
                "runs_with_delay_over_10x": int((first_gen[both] > 10 * first_fit[both]).sum()),
                "final_effective_width": {str(k): int(v) for k, v in zip(*np.unique(widths, return_counts=True))},
                "train_test_accuracy_by_step": curve}
            print(f"B scale={scale} wd={wd}", json.dumps(out[f"init_scale={scale}, weight_decay={wd}"]), flush=True)
    res["B_grokking"] = out


def main():
    t0 = time.time()
    res = {}
    part_a(res)
    part_b(res)
    res["wall_seconds"] = round(time.time() - t0, 1)
    (ROOT / "experiments" / "results" / "spike10b.json").write_text(json.dumps(res, indent=1))
    print("done", res["wall_seconds"])


if __name__ == "__main__":
    main()
