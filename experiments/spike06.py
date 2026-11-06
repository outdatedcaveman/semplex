"""Spike 06 measurements: what does proof-assistant-grade trust cost?

  CERP_LEAN=/path/to/lean python -m experiments.spike06

Three tiers of trust for the SAME claims:
  python   cerp/kernel.py (stdlib Python, unverified)
  lean     Lean kernel evaluates the PROVED decider (`decide`)
  native   compiled PROVED decider (`native_decide`; compiler trusted)
"""

from __future__ import annotations

import json
import pathlib
import random
import time

from cerp import kernel
from cerp.bdd import normal_form
from cerp.benchmarks import carry_prefix, carry_ripple
from cerp.lean_bridge import prove_cnf_unsat, prove_expr_claim
from cerp.sat import prove_equivalence
from cerp.substrates import random_expr
from cerp.translate import bdd_to_expr


def timed(f, *a, **k):
    t = time.perf_counter()
    r = f(*a, **k)
    return r, round(time.perf_counter() - t, 3)


def main():
    res = {"exhaustive_expr": [], "rup_carry": []}
    rng = random.Random(6)
    for n in (4, 6, 8, 10):
        vs = [f"x{i}" for i in range(n)]
        e = {"kind": "expr", "body": random_expr(vs, 6, rng)}
        nf = bdd_to_expr(normal_form(e, vs))
        v, tp = timed(kernel.check, {"relation": "extensional", "vars": vs, "left": e, "right": nf})
        (r, _), tl = timed(prove_expr_claim, e, nf, vs, name=f"rand{n}")
        row = {"n": n, "python_ok": v.ok, "python_s": tp, "lean_ok": r.ok, "lean_s": tl}
        res["exhaustive_expr"].append(row)
        print("exhaustive", row, flush=True)
    for k in (2, 3, 4, 8, 16, 32):
        (l, vs), (rr, _) = carry_ripple(k), carry_prefix(k)
        c = {"vars": vs, "left": l, "right": rr}
        _, F = kernel.miter_cnf(c)
        _, lemmas, _ = prove_equivalence(c)
        v, tp = timed(kernel.check_rup, {**c, "certificate": lemmas})
        row = {"inputs": 2 * k, "clauses": len(F), "lemmas": len(lemmas), "python_ok": v.ok, "python_s": tp}
        if k <= 4:
            (r, _), tl = timed(prove_cnf_unsat, F, lemmas, name=f"c{k}")
            row.update(lean_ok=r.ok, lean_s=tl)
        (r, _), tn = timed(prove_cnf_unsat, F, lemmas, name=f"n{k}", native=True)
        row.update(native_ok=r.ok, native_s=tn)
        res["rup_carry"].append(row)
        print("rup", row, flush=True)
    out = pathlib.Path(__file__).parent / "results" / "spike06.json"
    out.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
