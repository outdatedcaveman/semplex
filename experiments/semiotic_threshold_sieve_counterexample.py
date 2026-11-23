"""Counterexample to thresholded multiplicative confidence being a sieve.

Thiopoulos (1992), Definitions 2.20-2.21 and Theorem 2.1, assigns
conf(f o g) = conf(f) * conf(g) and proposes arrows with conf >= B
as a sieve/topological interpretation. This script tests sieve closure
directly in the smallest nontrivial compositional category.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.costed_executable_sieves import ChainProbeCategory, sieve_closure, is_sieve


def threshold_family(c, target, weights, threshold):
    return {
        a for a in c.arrows
        if c.target[a] == target and weights[a] >= threshold
    }


def run():
    c = ChainProbeCategory()
    c.validate()
    weights = {"iQ": 1.0, "iP": 1.0, "iX": 1.0, "u": 0.5, "g": 0.9, "h": 0.45}
    assert abs(weights["h"] - weights["g"] * weights["u"]) < 1e-12
    rows = []
    for threshold in (0.4, 0.45, 0.5, 0.8, 0.9):
        raw = threshold_family(c, "X", weights, threshold)
        closure = sieve_closure(c, "X", raw)
        rows.append({
            "threshold": threshold,
            "threshold_arrows": sorted(raw),
            "is_sieve": is_sieve(c, "X", raw),
            "sieve_closure": sorted(closure),
            "extra_arrows_added": sorted(closure - raw),
        })
    return {
        "source": "Thiopoulos (1992), Towards a Logic of Semiotic Systems, Definitions 2.20-2.21 and Theorem 2.1",
        "category": "Q --u--> P --g--> X, h = g∘u",
        "weights": weights,
        "composition_rule": "w(g∘u)=w(g)w(u)",
        "threshold_test": "R_B(X) = {f:Y→X | w(f)≥B}",
        "counterexample_at_B_0_8": {
            "g_is_in_threshold": weights["g"] >= 0.8,
            "composite_h_is_in_threshold": weights["h"] >= 0.8,
            "threshold_family_is_sieve": is_sieve(c, "X", threshold_family(c, "X", weights, 0.8)),
        },
        "rows": rows,
        "criterion": "For each B, threshold arrows form a sieve iff w(f)≥B implies w(f∘u)≥B for every composable u; multiplicativity alone does not imply this.",
        "scope": "finite counterexample to a general closure implication; it does not assess every possible interpretation of the 1992 paper's notation or intended weight domain",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2, sort_keys=True))
