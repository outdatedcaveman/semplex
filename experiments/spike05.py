"""Spike 05 measurements: how often do the equivalences come apart?

  python -m experiments.spike05

Random small LTS pairs (2-3 states, actions a/b), nondeterministic and
deterministic. For every pair, every verdict is certified by kernel_lts.
For pairs that are trace-equivalent but not bisimilar we search small
random test processes for a context in which deadlock behaviour differs.
"""

from __future__ import annotations

import json
import pathlib
import random
from collections import Counter

from cerp import kernel_lts as K
from cerp.lts import bisimulation, random_lts, trace_equivalence

N_PAIRS = 3000
N_TESTS = 300


def classify(A, B):
    b = bisimulation(A, B)
    c = trace_equivalence(A, B, completed=True)
    t = trace_equivalence(A, B)
    # every verdict certified by the trusted kernel
    assert (K.check_bisimulation(A, B, b[1]) if b[0] == "bisimilar"
            else K.check_distinguishing_formula(A, B, b[1])).ok
    for res, comp in ((c, True), (t, False)):
        if res[0] == "equivalent":
            assert K.check_trace_cert(A, B, res[1], completed=comp).ok
        else:
            X, Y = (A, B) if res[2] == "P" else (B, A)
            assert K.check_trace_witness(X, Y, res[1], completed=res[3] == "completed").ok
    return (t[0] == "equivalent", c[0] == "equivalent", b[0] == "bisimilar")


def distinguishing_context(A, B, rng):
    for _ in range(N_TESTS):
        T = random_lts(rng, rng.randint(1, 3), actions=("a", "b", "ok"), p=0.45)
        if K.check_context_deadlock(A, T, {"a", "b"}).ok != K.check_context_deadlock(B, T, {"a", "b"}).ok:
            return T
    return None


def main():
    rng = random.Random(5)
    res = {}
    for label, det in (("nondeterministic", False), ("deterministic", True)):
        cats, ctx = Counter(), Counter()
        for _ in range(N_PAIRS):
            A = random_lts(rng, rng.randint(2, 3), det=det)
            B = random_lts(rng, rng.randint(2, 3), det=det)
            t, c, b = classify(A, B)
            key = "bisimilar" if b else "completed-trace-eq only" if c else "trace-eq only" if t else "different traces"
            cats[key] += 1
            if t and not b:
                ctx["distinguished by some tested context" if distinguishing_context(A, B, rng)
                    else "no context found"] += 1
        res[label] = {"pairs": N_PAIRS, "categories": dict(cats), "trace_eq_not_bisimilar_contexts": dict(ctx)}
        print(label, res[label], flush=True)
    out = pathlib.Path(__file__).parent / "results" / "spike05.json"
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
