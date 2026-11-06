"""Spike 02 measurements.  python -m experiments.spike02

The harness (this file) may look at ground truth; the agent may not.
All numbers are EMPIRICAL statements about this sandbox and these seeds.
"""

from __future__ import annotations

import json
import pathlib
import random
import time
from collections import Counter, defaultdict

from cerp.epistemics.approx_sufficiency import minimal_eps_sufficient
from cerp.epistemics.bayesnet import distribution, em_fit
from cerp.epistemics.inquiry import DEFAULT_QUERIES, adequacy_test, inquire, query_text
from cerp.epistemics.ontologies import (CANDIDATES, O1_LATENT_CAUSAL, O2_INDEPENDENT,
                                        O3_LATENT_CONFOUNDED, O4_COPY_CHAIN)
from cerp.epistemics.stats import g_test
from cerp.epistemics.world import ALL_ACTIONS, WORLDS, Interface, true_effect

SEEDS = range(15)
TRUE_MODEL = {"latent_causal": O1_LATENT_CAUSAL.name, "latent_confounded": O3_LATENT_CONFOUNDED.name,
              "copy_chain": O4_COPY_CHAIN.name}
INTERFACES = {"observe-only": ALL_ACTIONS[:1], "observe+do(A)": ALL_ACTIONS[:3], "all": ALL_ACTIONS}


def truth_answer(world, q):
    if q[0] == "effect":
        return true_effect(world, q[1], q[2])
    s, _ = WORLDS[world]
    return any(z in s.parents[q[1]] and z in s.parents[q[2]] for z in s.latents)


def classify(world, rep):
    out = {}
    for q in DEFAULT_QUERIES:
        a = rep["answers"].get(query_text(q))
        if a is None:
            out[q] = "no-answer"
            continue
        st, head = a["status"], a["statement"].split(":")[0]
        if head == "UNDETERMINED":
            out[q] = "undetermined"
        elif st == "RETRACTED":
            out[q] = "retracted"
        else:
            correct = (head == "YES") == truth_answer(world, q)
            out[q] = f"{st}/{'correct' if correct else 'WRONG'}"
    return out


def run_grid(candidates, worlds, label):
    rows, tally = [], defaultdict(Counter)
    for world in worlds:
        for iname, acts in INTERFACES.items():
            for seed in SEEDS:
                t0 = time.perf_counter()
                rep = inquire(Interface(world, acts, seed=1000 + seed), candidates, seed=seed)
                cls = classify(world, rep)
                for q, c in cls.items():
                    tally[(world, iname, query_text(q))][c] += 1
                    tally[("ALL", "ALL", "ALL")][c] += 1
                rows.append({"world": world, "interface": iname, "seed": seed,
                             "survivors": rep["survivors"], "spent": rep["spent"],
                             "protocols": [r["protocol"] for r in rep["rounds"]],
                             "true_model_survived": TRUE_MODEL[world] in rep["survivors"],
                             "true_model_in_candidates": TRUE_MODEL[world] in [c.name for c in candidates],
                             "secs": round(time.perf_counter() - t0, 2)})
    summary = {" | ".join(k): dict(v) for k, v in sorted(tally.items())}
    return {"label": label, "rows": rows, "summary": summary}


def calibration_study(n_seeds=40):
    """False rejection of the TRUE model by naive vs calibrated adequacy."""
    a_each = 0.05 / (8 * 10)
    out = {}
    for world, model, do in (("latent_causal", O1_LATENT_CAUSAL, {"S1": 1}),
                             ("latent_causal", O1_LATENT_CAUSAL, {"A": 1}),
                             ("latent_confounded", O3_LATENT_CONFOUNDED, {"S1": 0})):
        naive, calib = [], []
        for seed in range(n_seeds):
            rng = random.Random(seed)
            iface = Interface(world, seed=5000 + seed)
            train = {(): iface.run({}, 1500)}
            params = em_fit(model, train, rng)[0]
            batch = iface.run(do, 1500)
            naive.append(g_test(batch, distribution(model, params, do))[2])
            calib.append(adequacy_test(model, params, train, do, batch, rng)[2])
        key = f"{world} / {model.name} / do{do}"
        out[key] = {"alpha_per_test": a_each,
                    "naive_false_rejection_rate": sum(p < a_each for p in naive) / n_seeds,
                    "calibrated_false_rejection_rate": sum(p < a_each for p in calib) / n_seeds,
                    "naive_p_below_0.05": sum(p < 0.05 for p in naive) / n_seeds,
                    "calibrated_p_below_0.05": sum(p < 0.05 for p in calib) / n_seeds}
    return out


def sufficiency_signature(n=3000):
    obs = ("A", "S1", "S2", "Y")
    out = {}
    for world in WORLDS:
        pats = Counter()
        for seed in SEEDS:
            r = minimal_eps_sufficient(Interface(world, seed=9000 + seed).run({}, n),
                                       obs, ("A", "S1", "S2"), "Y", 0.0)
            pats[" / ".join("{" + ",".join(s) + "}" for s in r["sets"])] += 1
        out[world] = dict(pats)
    return out


def main():
    t0 = time.time()
    res = {"seeds": len(SEEDS), "batch": 1500, "initial_obs": 1500}
    res["main"] = run_grid(CANDIDATES, list(WORLDS), "truth among candidates")
    res["truth_missing"] = {
        "copy_chain without O4": run_grid((O1_LATENT_CAUSAL, O2_INDEPENDENT, O3_LATENT_CONFOUNDED),
                                          ["copy_chain"], "O4 removed"),
        "latent_causal without O1": run_grid((O2_INDEPENDENT, O3_LATENT_CONFOUNDED, O4_COPY_CHAIN),
                                             ["latent_causal"], "O1 removed"),
    }
    res["calibration"] = calibration_study()
    res["sufficiency_signature"] = sufficiency_signature()
    res["wall_seconds"] = round(time.time() - t0, 1)
    out = pathlib.Path(__file__).parent / "results" / "spike02.json"
    out.write_text(json.dumps(res, indent=1, default=str))

    def show(block):
        print(f"\n## {block['label']}")
        for k, v in block["summary"].items():
            print(f"  {k}: {v}")
        rows = block["rows"]
        tm = [r for r in rows if r["true_model_in_candidates"]]
        if tm:
            print(f"  true model survived: {sum(r['true_model_survived'] for r in tm)}/{len(tm)}")
        print(f"  mean samples spent: {sum(r['spent'] for r in rows) / len(rows):.0f}")

    show(res["main"])
    for b in res["truth_missing"].values():
        show(b)
    print("\n## calibration"); print(json.dumps(res["calibration"], indent=1))
    print("\n## sufficiency signature"); print(json.dumps(res["sufficiency_signature"], indent=1))
    print("wall", res["wall_seconds"], "s")


if __name__ == "__main__":
    main()
