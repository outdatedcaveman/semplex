"""Spike 03 measurements: proof-carrying equivalence past the exhaustive wall.

  python -m experiments.spike03

For each circuit family and width k (n = 2k inputs) we time:
  search  untrusted CDCL solver finding the RUP certificate / counterexample
  check   trusted kernel replaying the certificate (or evaluating the counterexample)
and, where n <= 16, the exhaustive kernel for comparison.
"""

from __future__ import annotations

import json
import pathlib
import random
import time

from cerp import kernel
from cerp.bdd import normal_form
from cerp.benchmarks import FAMILIES
from cerp.sat import prove_equivalence
from cerp.substrates import random_expr
from cerp.translate import bdd_to_circuit


def timed(f, *a, **k):
    t = time.perf_counter()
    r = f(*a, **k)
    return r, time.perf_counter() - t


def run_pair(left, right, vars_, expect_equal, time_limit=120):
    claim = {"vars": vars_, "left": left, "right": right}
    try:
        (status, payload, solver), t_search = timed(prove_equivalence, claim, time_limit)
    except kernel.KernelError as exc:
        return {"n": len(vars_), "status": "out-of-scope", "reason": str(exc)}
    row = {"n": len(vars_), "status": status, "search_s": round(t_search, 3), "conflicts": solver.conflicts}
    if status == "unsat":
        claim["certificate"] = payload
        v, t_check = timed(kernel.check_rup, claim)
        row.update(certified=v.ok, lemmas=len(payload), check_s=round(t_check, 3),
                   lemma_literals=sum(len(l) for l in payload))
    elif status == "sat":
        v, t_check = timed(kernel.check_counterexample, {**claim, "x": payload})
        row.update(certified=v.ok, check_s=round(t_check, 5))
    row["correct"] = (status == "unsat") == expect_equal if status != "timeout" else None
    if len(vars_) <= kernel.MAX_VARS:
        v, t_ex = timed(kernel.check, {"relation": "extensional", "vars": vars_, "left": left, "right": right})
        row.update(exhaustive_s=round(t_ex, 3), exhaustive_agrees=v.ok == expect_equal)
    return row


def main():
    res = {"families": {}, "random_expr_vs_canonical": []}
    for fam, make in FAMILIES.items():
        rows = []
        for k in (4, 8, 12, 16, 24, 32):
            (l, vs), (r, _), eq = make(k)
            row = run_pair(l, r, vs, eq)
            rows.append(row)
            print(fam, row, flush=True)
            if row["status"] == "timeout":
                break
        res["families"][fam] = rows
    rng = random.Random(3)
    for n in (12, 16, 20, 24):
        vs = [f"x{i}" for i in range(n)]
        for _ in range(3):
            e = {"kind": "expr", "body": random_expr(vs, 9, rng)}
            nf = normal_form(e, vs)
            row = run_pair(e, bdd_to_circuit(nf, vs), vs, True)
            row["bdd_nodes"] = len(nf["body"]["nodes"]) - 2
            res["random_expr_vs_canonical"].append(row)
            print("random", row, flush=True)
    out = pathlib.Path(__file__).parent / "results" / "spike03.json"
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
