"""Spike 10b, part C: systematic local learning rules scored against the atlas.

  python -m experiments.spike10b_rules      (needs jax; ~15 min on 4 CPUs)

For each observational power (A: own layer; B: + broadcast error; C: + downstream
weights) the dictionary is every trace monomial up to order 4. Coefficients are
meta-learned on half of the 4-input elements and evaluated on all of them.
"""

from __future__ import annotations

import json
import pathlib
import random
import time

import numpy as np

from cerp import atlas, learnrules as lr, localrules as L

ROOT = pathlib.Path(__file__).resolve().parent.parent
H, N, T_EVAL = 8, 4, 200


def tgt(fs):
    return np.array([[(int(f) >> x) & 1 for x in range(16)] for f in fs], dtype=np.float32)


def main():
    import jax.numpy as jnp
    t0 = time.time()
    tb = atlas.build_all(4)[4]
    Lt = np.array(sorted(tb.ltf), dtype=np.int64)
    x2 = np.zeros(65536, dtype=bool)
    x2[(Lt[:, None] ^ Lt[None, :]).reshape(-1)] = True
    wstar = np.where(tb.hi == 1, 1, np.where((tb.hi == 3) | x2, 2, np.where(tb.hi == 5, 4, 3)))
    wstar[0] = wstar[65535] = 0
    X = jnp.asarray(L.inputs_aug(N))
    ex = [int(tb.exhibit[c]) for c in tb.classes()]
    rnd = random.Random(101)
    train_cls = set(rnd.sample(range(len(ex)), len(ex) // 2))
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
                costs = tb.hi[np.array(comps)]
                tasks.append({"f": e, "care": care, "size": size, "min": int(costs.min()), "held": ci not in train_cls})
    mt_f = tgt([ex[i] for i in sorted(train_cls)] + [t["f"] for t in tasks if not t["held"]])
    mt_c = tgt([65535] * len(train_cls) + [t["care"] for t in tasks if not t["held"]])

    def evaluate(trainer, coef, seed):
        out = {}
        run = trainer["run"](T_EVAL)
        fs = np.array(ex * 5)
        st = L.init_states(len(fs), H, N, np.random.default_rng(seed))
        fin = run(jnp.asarray(coef), tuple(map(jnp.asarray, st)), X, tgt(fs), np.ones((len(fs), 16), dtype=np.float32))
        g, units = L.read_states(fin, N)
        fit = g == fs
        held = np.array([(i % len(ex)) not in train_cls for i in range(len(fs))])
        exc = [lr.effective_width(units[i], int(g[i]), 16) - int(wstar[g[i]]) for i in np.nonzero(fit)[0]]
        out["full_fit"] = round(float(fit.mean()), 4)
        out["full_fit_held_out_elements"] = round(float(fit[held].mean()), 4)
        out["full_fit_by_min_neurons"] = {int(k): round(float(fit[tb.hi[fs] == k].mean()), 3) for k in (1, 3, 4, 5)}
        out["frac_minimal_width_when_fit"] = round(float(np.mean(np.array(exc) == 0)), 3) if exc else None
        fs = np.array([t["f"] for t in tasks] * 3)
        cs = np.array([t["care"] for t in tasks] * 3)
        st = L.init_states(len(fs), H, N, np.random.default_rng(seed + 1))
        fin = run(jnp.asarray(coef), tuple(map(jnp.asarray, st)), X, tgt(fs), tgt(cs))
        g, _ = L.read_states(fin, N)
        fit = (g & cs) == (fs & cs)
        for size in (12, 8):
            idx = [i for i in np.nonzero(fit)[0] if tasks[i % len(tasks)]["size"] == size]
            tot = sum(1 for i in range(len(fs)) if tasks[i % len(tasks)]["size"] == size)
            learned = tb.hi[g[idx]]
            out[f"partial_{size}"] = {"fit": round(len(idx) / tot, 4),
                                      "frac_cheapest_when_fit": round(float(np.mean(
                                          learned == [tasks[i % len(tasks)]["min"] for i in idx])), 3) if idx else None,
                                      "mean_neurons": round(float(learned.mean()), 3) if idx else None}
        return out

    res = {"hidden": H, "eval_steps": T_EVAL, "order": 4}
    bp = L.make_trainer([], N, backprop=True)
    res["backprop (same inner loop)"] = evaluate(bp, np.zeros(0, dtype=np.float32), 40)
    print("backprop", json.dumps(res["backprop (same inner loop)"]), flush=True)

    configs = [("A", "O", None), ("B", "O", None), ("B", "B", None), ("B", "S", None), ("B", "S", "Y[a]*E"),
               ("C", "O", None), ("C", "O", "Y[a]*E*V[a]")]
    for P, G, warm in configs:
        monos = L.enumerate_monomials(P, 4, G)
        labels = [m["label"] for m in monos]
        tr = L.make_trainer(monos, N)
        rng = np.random.default_rng(70)
        scales = L.normalisation(monos, tr, X, H, N, rng)
        name = f"power {P}, hidden symmetry {G}"
        if P == "A":
            res["no first-layer learning"] = evaluate(tr, np.zeros(len(monos), dtype=np.float32), 40)
            print("frozen", json.dumps(res["no first-layer learning"]), flush=True)
        start = None
        if warm:
            fixed = np.zeros(len(monos), dtype=np.float32)
            fixed[labels.index(warm)] = 0.5
            ev = evaluate(tr, fixed, 40)
            res[f"{name}: the single term {warm} with coefficient 0.5 (not learned)"] = ev
            print("fixed", warm, json.dumps(ev), flush=True)
            start = np.where(scales > 0, fixed / np.maximum(scales, 1e-12), 0.0)
            name += f", started from {warm}"
        t1 = time.time()
        a, hist = L.meta_learn(monos, tr, scales, X, mt_f, mt_c, H, N, rng, iters=250, lr=0.002, l1=1e-5, start=start,
                               log=lambda s_: print(P, G, s_, flush=True))
        ev = evaluate(tr, a * scales, 40)
        order = np.argsort(-np.abs(a * scales))
        ev.update({"dictionary_size": len(monos), "meta_loss_by_horizon": hist, "meta_seconds": round(time.time() - t1, 1),
                   "largest_terms_by_effective_coefficient": [[labels[i], round(float(a[i] * scales[i]), 4)] for i in order[:6]]})
        res[name + " (meta-learned)"] = ev
        print(name, json.dumps(ev), flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    (ROOT / "experiments" / "results" / "spike10b_rules.json").write_text(json.dumps(res, indent=1))
    print("done", res["wall_seconds"])


if __name__ == "__main__":
    main()
