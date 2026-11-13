"""Spike 14: First non-synthetic case study (UCI PlayTennis / Quinlan 1986).

  python -m experiments.spike14_real_case_study

Fits a causal Bayes net on the 14 real PlayTennis observations (discretized to
4 binary features: OutlookSunny, TempHot, HumidityHigh, WindStrong -> Play),
distills the Bayes-optimal decision rule to an F0 expr + circuit via
`csir.distill_causal_rule`, verifies the CSIR bundle, and compares circuit cost
against the exact 4-input atlas (`cerp/atlas.py`).
"""

from __future__ import annotations

import json
import pathlib
import random
from collections import Counter

from cerp import atlas, csir, substrates
from cerp.epistemics.bayesnet import Structure, em_fit, loglik

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "results" / "spike14_real_case_study.json"

# Quinlan (1986) PlayTennis dataset (14 real observations), binarized:
#   Sunny = (Outlook == Sunny), Hot = (Temp == Hot), HighHum = (Humidity == High), Windy = (Wind == Strong)
PLAY_TENNIS = [
    (1, 1, 1, 0, 0), (1, 1, 1, 1, 0), (0, 1, 1, 0, 1), (0, 0, 1, 0, 1),
    (0, 0, 0, 0, 1), (0, 0, 0, 1, 0), (0, 0, 0, 1, 1), (1, 0, 1, 0, 0),
    (1, 0, 0, 0, 1), (0, 0, 0, 0, 1), (1, 0, 0, 1, 1), (0, 0, 1, 1, 1),
    (0, 1, 0, 0, 1), (0, 0, 1, 1, 0),
]


def main():
    s = Structure(
        name="play_tennis",
        observables=("Sunny", "Hot", "HighHum", "Windy", "Play"),
        latents=(),
        parents={"Sunny": (), "Hot": (), "HighHum": (), "Windy": (),
                 "Play": ("Sunny", "Hot", "HighHum", "Windy")},
    )
    data = {(): Counter(PLAY_TENNIS)}
    params, ll = em_fit(s, data, random.Random(0), restarts=2, iters=50)
    b = csir.distill_causal_rule(s, params, target="Play", model_id="play_tennis")
    errs = csir.validate(b)
    recheck = csir.recheck(b)

    circ_node = [n for n in b["nodes"] if n["artifact"]["kind"] == "circuit"][0]
    expr_node = [n for n in b["nodes"] if n["artifact"]["kind"] == "expr"][0]
    tb = atlas.build_all(4)[4]
    # Evaluate distilled rule on all 16 inputs to look up exact atlas minimum neurons
    from cerp.kernel import _eval_expr
    feats = ["Sunny", "Hot", "HighHum", "Windy"]
    tt_bits = 0
    for i in range(16):
        env = {feats[j]: bool((i >> j) & 1) for j in range(4)}
        if _eval_expr(expr_node["artifact"]["body"], env):
            tt_bits |= (1 << i)
    atlas_min_neurons = int(tb.hi[tt_bits])

    res = {
        "dataset": "Quinlan 1986 PlayTennis (14 rows, 4 binary features)",
        "loglik": round(float(ll), 4),
        "csir_validation_errors": errs,
        "csir_recheck": recheck,
        "distilled_circuit_cost": circ_node["resources"]["cost"],
        "atlas_min_threshold_neurons": atlas_min_neurons,
        "truth_table_bits": tt_bits,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
