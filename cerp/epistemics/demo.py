"""Watch the inquiry loop:  python -m cerp.epistemics.demo [world] [observe|doA|all]

worlds: latent_causal (default), latent_confounded, copy_chain
"""

import sys

from ..ledger import Status
from .inquiry import inquire
from .ontologies import CANDIDATES
from .world import ALL_ACTIONS, Interface

LEVELS = {"observe": ALL_ACTIONS[:1], "doA": ALL_ACTIONS[:3], "all": ALL_ACTIONS}


def main(argv):
    world = argv[1] if len(argv) > 1 else "latent_causal"
    level = argv[2] if len(argv) > 2 else "all"
    print(f"# Inquiry into a hidden world through protocols: {level}\n")
    print("Candidate ontologies:")
    for c in CANDIDATES:
        print(f"  - {c.name}: {c.description}")
    rep = inquire(Interface(world, LEVELS[level], seed=1), CANDIDATES, seed=1)
    L = rep["ledger"]
    print("\n## Rounds")
    for r in rep["rounds"]:
        drop = f"  -> dropped {r['dropped']} (revision {r['revision']})" if r["dropped"] else ""
        print(f"  {r['round']}: {r['protocol']:10s} because {r['why']}{drop}")
    print("\n## Ontology revisions")
    for c in L.claims.values():
        if c.category == "ontology-revision":
            ev = c.evidence
            print(f"  [{c.id}] {c.statement}")
            if "commitments_newly_settled" in ev:
                print(f"       newly settled: {ev['commitments_newly_settled']}")
                print(f"       still open:    {ev['commitments_still_open']}")
    print(f"\n## Answers (survivors: {rep['survivors']}; samples used: {rep['spent']})")
    for q, a in rep["answers"].items():
        print(f"  {a['status']:22s} {a['statement']}")
    if rep.get("equivalence"):
        print("\n## Why some questions stay open: equivalence witnesses")
        for k, v in rep["equivalence"].items():
            print(f"  {k}: max KL {v['max_kl']:.1e} ({'witnessed' if v['witnessed'] else 'not witnessed'})")
    n_ret = sum(L.effective_status(c) is Status.RETRACTED for c in L.claims)
    print(f"\nLedger: {len(L.claims)} claims, {n_ret} retracted (kept for history).")


if __name__ == "__main__":
    main(sys.argv)
