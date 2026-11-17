"""Spike 02b measurements: ontology generation after refutation.

  python -m experiments.spike02b

Scenarios (truth always OUTSIDE the given candidates):
  copy_chain without O4, latent_causal without O1,
  direct_and_latent (outside all four), with and without do(S2).
Harness-only ground truth decides whether the truth was proposed, whether
it survived fresh-data validation, and whether answers are correct.
"""

from __future__ import annotations

import json
import pathlib
import time
from collections import Counter

from cerp.epistemics.generate import canon_of_structure
from cerp.epistemics.inquiry import EXTENDED_QUERIES, inquire, query_text
from cerp.epistemics.ontologies import (CANDIDATES, O1_LATENT_CAUSAL, O2_INDEPENDENT,
                                        O3_LATENT_CONFOUNDED, O4_COPY_CHAIN)
from cerp.epistemics.world import ALL_ACTIONS, Interface, true_effect, truth

SEEDS = range(10)
WITH_S2 = ALL_ACTIONS + ({"S2": 0}, {"S2": 1})
Q_S2 = EXTENDED_QUERIES + (("effect", "S2", "S1"), ("effect", "S2", "Y"))

SCENARIOS = {
    "copy_chain, O4 removed": ("copy_chain", (O1_LATENT_CAUSAL, O2_INDEPENDENT, O3_LATENT_CONFOUNDED),
                               ALL_ACTIONS, EXTENDED_QUERIES),
    "latent_causal, O1 removed": ("latent_causal", (O2_INDEPENDENT, O3_LATENT_CONFOUNDED, O4_COPY_CHAIN),
                                  ALL_ACTIONS, EXTENDED_QUERIES),
    "direct_and_latent (outside all)": ("direct_and_latent", CANDIDATES, ALL_ACTIONS, EXTENDED_QUERIES),
    "direct_and_latent + do(S2)": ("direct_and_latent", CANDIDATES, WITH_S2, Q_S2),
}


def truth_answer(world, q):
    if q[0] == "effect":
        return true_effect(world, q[1], q[2])
    s, _ = truth(world)
    return any(z in s.parents[q[1]] and z in s.parents[q[2]] for z in s.latents)


def main():
    res = {}
    t0 = time.time()
    for label, (world, cands, acts, queries) in SCENARIOS.items():
        true_canon = canon_of_structure(truth(world)[0])
        agg = Counter()
        rows = []
        for seed in SEEDS:
            rep = inquire(Interface(world, acts, seed=700 + seed), cands, seed=seed, queries=queries,
                          generate_on_refutation=True, max_rounds=40)
            proposed = [p for g in rep["generations"] for p in g["proposed"]]
            gen_structs = rep.get("generated_structures", {})
            true_proposed = any(canon_of_structure(gen_structs[n]) == true_canon for n in proposed)
            true_survived = any(canon_of_structure(gen_structs[n]) == true_canon
                                for n in rep["survivors"] if n in gen_structs)
            agg["truth proposed"] += true_proposed
            agg["truth survived validation"] += true_survived
            agg["generated set fully refuted"] += bool(rep["generations"]) and not rep["survivors"]
            for q in queries:
                a = rep["answers"].get(query_text(q))
                if a is None:
                    agg["answer: none"] += 1
                    continue
                head = a["statement"].split(":")[0]
                if head == "UNDETERMINED" or a["status"] in ("OUT-OF-SCOPE", "RETRACTED"):
                    agg["answer: undetermined/retracted"] += 1
                else:
                    ok = (head == "YES") == truth_answer(world, q)
                    agg[f"answer: {a['status']} {'correct' if ok else 'WRONG'}"] += 1
            rows.append({"seed": seed, "spent": rep["spent"], "survivors": rep["survivors"],
                         "generations": rep["generations"]})
        res[label] = {"runs": len(SEEDS), "summary": dict(agg), "mean_spent": sum(r["spent"] for r in rows) / len(rows),
                      "pruning_example": rows[0]["generations"][0]["counts"] if rows[0]["generations"] else None,
                      "rows": rows}
        print(label, dict(agg), "mean spent", res[label]["mean_spent"], flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    out = pathlib.Path(__file__).parent / "results" / "spike02b.json"
    out.write_text(json.dumps(res, indent=1, default=str))


if __name__ == "__main__":
    main()
