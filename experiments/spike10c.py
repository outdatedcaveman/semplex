"""Spike 10c: the least a learning rule must observe, per element.

  python -m experiments.spike10c       (needs jax; ~1 hour on 4 CPUs; resumable)

For each (observational power, hidden symmetry group, order) the best rule is
searched with a derivative-free method at a fixed 200-step horizon, on half of
the 4-input elements, then scored on all 222. Results are checkpointed per
configuration in experiments/results/spike10c.json.
"""

from __future__ import annotations

import json
import pathlib
import random
import time

import numpy as np

from cerp import atlas, localrules as L

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike10c.json"
H, N, T_EVAL, SEEDS = 8, 4, 200, 5
CONFIGS = [("C", "O", 3), ("B", "S", 2), ("B", "S", 3), ("B", "O", 4), ("B", "B", 4), ("A", "O", 4),
           ("C", "O", 4), ("A", "S", 3), ("B", "S", 4)]


def tgt(fs):
    return np.array([[(int(f) >> x) & 1 for x in range(16)] for f in fs], dtype=np.float32)


def main():
    import jax.numpy as jnp
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    tb = atlas.build_all(4)[4]
    X = jnp.asarray(L.inputs_aug(N))
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    cost = [int(tb.hi[e]) for e in ex]
    rnd = random.Random(101)
    train_cls = sorted(rnd.sample(range(len(ex)), len(ex) // 2))
    held = [i for i in range(len(ex)) if i not in set(train_cls)]
    Ttr = tgt([ex[i] for i in train_cls] * 2)
    Ctr = np.ones_like(Ttr)
    rnd2 = random.Random(92)
    tasks = []
    for e in ex:
        for size in (12, 8):
            for _ in range(3):
                care = sum(1 << x for x in rnd2.sample(range(16), size))
                comps = [e & care]
                for x in range(16):
                    if not (care >> x) & 1:
                        comps += [c | (1 << x) for c in comps]
                tasks.append({"f": e, "care": care, "size": size, "min": int(tb.hi[np.array(comps)].min())})

    def evaluate(tr, coef):
        run = tr["run"](T_EVAL)
        fs = np.array(ex * SEEDS)
        st = L.init_states(len(fs), H, N, np.random.default_rng(40))
        g, _ = L.read_states(run(jnp.asarray(coef), tuple(map(jnp.asarray, st)), X, tgt(fs),
                                 np.ones((len(fs), 16), dtype=np.float32)), N)
        fit = (g == fs).reshape(SEEDS, len(ex))
        per = fit.sum(0)
        out = {"fit": round(float(fit.mean()), 4), "fit_held_out": round(float(fit[:, held].mean()), 4),
               "fit_by_min_neurons": {k: round(float(fit[:, [i for i, c in enumerate(cost) if c == k]].mean()), 3)
                                      for k in (1, 3, 4, 5)},
               "elements_learned_4_of_5_seeds": int((per >= 4).sum()),
               "elements_learned_by_min_neurons": {k: int(sum(per[i] >= 4 for i, c in enumerate(cost) if c == k))
                                                   for k in (1, 3, 4, 5)},
               "seeds_fit_per_element": per.tolist()}
        fs = np.array([t["f"] for t in tasks] * 3)
        cs = np.array([t["care"] for t in tasks] * 3)
        st = L.init_states(len(fs), H, N, np.random.default_rng(41))
        g, _ = L.read_states(run(jnp.asarray(coef), tuple(map(jnp.asarray, st)), X, tgt(fs), tgt(cs)), N)
        ok = (g & cs) == (fs & cs)
        for size in (12, 8):
            idx = [i for i in np.nonzero(ok)[0] if tasks[i % len(tasks)]["size"] == size]
            tot = sum(1 for i in range(len(fs)) if tasks[i % len(tasks)]["size"] == size)
            out[f"partial_{size}"] = {"fit": round(len(idx) / tot, 4), "frac_cheapest_when_fit": round(float(np.mean(
                tb.hi[g[idx]] == [tasks[i % len(tasks)]["min"] for i in idx])), 3) if idx else None}
        return out

    if "backprop" not in res:
        res["backprop"] = evaluate(L.make_trainer([], N, backprop=True), np.zeros(0, dtype=np.float32))
        mA = L.enumerate_monomials("A", 2, "O")
        res["no first-layer learning"] = evaluate(L.make_trainer(mA, N), np.zeros(len(mA), dtype=np.float32))
        OUT.write_text(json.dumps(res, indent=1))
        print("backprop", res["backprop"]["fit"], "frozen", res["no first-layer learning"]["fit"], flush=True)

    for P, G, K in CONFIGS:
        key = f"{P},{G},{K}"
        if key in res:
            continue
        t0 = time.time()
        monos = L.enumerate_monomials(P, K, G)
        labels = [m["label"] for m in monos]
        tr = L.make_trainer(monos, N)
        rng = np.random.default_rng(1000 + len(monos))
        units = L.natural_units(monos, tr, X, H, N, rng)
        gens = 40 if len(monos) <= 30 else 60
        a, hist = L.cem_search(tr, units, X, Ttr, Ctr, H, N, rng, gens=gens, pop=32 if len(monos) <= 30 else 48,
                               log=lambda s: print(key, s, flush=True))
        ev = evaluate(tr, a * units)
        order = np.argsort(-np.abs(a))
        ev.update({"power": P, "symmetry": G, "order": K, "dictionary_size": len(monos),
                   "search_history_loss_fit": hist[::5] + [hist[-1]], "seconds": round(time.time() - t0),
                   "coefficients_natural_units": {labels[i]: round(float(a[i]), 3) for i in order if abs(a[i]) > 0.05}})
        res[key] = ev
        OUT.write_text(json.dumps(res, indent=1))
        print("DONE", key, {k: ev[k] for k in ("fit", "fit_held_out", "fit_by_min_neurons", "elements_learned_4_of_5_seeds",
                                                "dictionary_size", "seconds")}, flush=True)


if __name__ == "__main__":
    main()
