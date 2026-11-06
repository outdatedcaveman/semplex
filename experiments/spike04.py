"""Spike 04 measurements: how much structure did single labels hide?

  python -m experiments.spike04

Builds the real ledgers produced by Spike 01 (demo pipeline) and Spike 02
(one inquiry per world, all protocols) and reports, per ledger:
  * how many DISTINCT warrants collapse onto each charter label
  * the fraction of asserted claim pairs whose warrants are INCOMPARABLE
    (pairs a total order would have been forced to rank)
"""

from __future__ import annotations

import itertools
import json
import pathlib
from collections import defaultdict

from cerp.demo import ALARM, SENSORS_AGREE
from cerp.epistemics.inquiry import inquire
from cerp.epistemics.ontologies import CANDIDATES
from cerp.epistemics.world import ALL_ACTIONS, Interface
from cerp.ledger import Outcome, compare
from cerp.pipeline import analyze


def profile(L):
    per_label = defaultdict(set)
    ws = []
    for c in L.claims.values():
        w = L.effective_warrant(c.id)
        per_label[L.effective_status(c.id).label].add(w.describe())
        if c.outcome is Outcome.ASSERTED and not L.is_retracted(c.id):
            ws.append(w)
    pairs = list(itertools.combinations(ws, 2))
    inc = sum(compare(a, b) == "incomparable" for a, b in pairs)
    return {"claims": len(L.claims),
            "distinct_warrants_per_label": {k: sorted(v) for k, v in sorted(per_label.items())},
            "asserted_pairs": len(pairs),
            "incomparable_fraction": round(inc / len(pairs), 3) if pairs else 0.0}


def main():
    res = {"spike01_alarm": profile(analyze(ALARM, ["a", "b", "c", "d"], care=SENSORS_AGREE)["ledger"])}
    for w in ("latent_causal", "latent_confounded", "copy_chain"):
        res[f"spike02_{w}"] = profile(inquire(Interface(w, ALL_ACTIONS, seed=1), CANDIDATES, seed=1)["ledger"])
    out = pathlib.Path(__file__).parent / "results" / "spike04.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
