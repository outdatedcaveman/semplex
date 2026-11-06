"""Master algorithm v0 (charter §9) -- restricted to fragment F0.

    analyze(source, vars, care=None)

  0. Scope check          -> boundary claim and stop if outside F0
  1. Front end            -> semantics [[source]] (main interpreter, untrusted)
  2. Canonicalize         -> N(source) as ROBDD; kernel checks source == N(source)
  3. Task abstraction     -> minimal sufficient sets (if a care set is given),
                             kernel-checked sufficiency + minimality certificates
  4. Realize              -> untrusted translators produce candidates in 3 substrates
  5. Verify               -> kernel decides each candidate vs source; failures kept
  6. Resource report      -> per-substrate Pareto fronts over VERIFIED candidates only
  7. Improvement claims   -> only when fidelity is kernel-checked and cost dominates
  Every step writes to the ledger with an honest status label.

Partial by design: anything outside F0 returns a boundary claim, not a guess.
"""

from __future__ import annotations

from . import kernel
from .bdd import normal_form
from .ledger import Ledger
from .resources import dominates, pareto_front
from .semantics import TruthTable
from .substrates import cost, expr_vars, semantics
from .sufficiency import (MAX_SUFFICIENCY_VARS, insufficiency_witness,
                          minimal_sufficient_sets, project)
from .sufficiency import report as sufficiency_report
from .translate import (bdd_to_circuit, bdd_to_dfa, bdd_to_expr, circuit_to_expr,
                        expr_to_circuit, restrict_to_care, truthtable_to_bdd)

F0_KINDS = {"expr", "circuit", "dfa", "bdd"}
SUBSTRATE_OF = {"expr": "expr", "circuit": "circuit", "dfa": "dfa", "bdd": "bdd"}


def _free_vars(art):
    k, b = art["kind"], art["body"]
    if k == "expr":
        return expr_vars(b)
    if k == "circuit":
        return set(b["inputs"])
    return set(b["order"])


def analyze(source: dict, vars, care: dict | None = None, *, name="source",
            translators: dict | None = None, max_task_sets: int = 3) -> dict:
    vars = tuple(vars)
    L = Ledger()
    rep = {"name": name, "vars": list(vars), "ledger": L, "candidates": [], "rejected": []}

    # 0. scope ------------------------------------------------------------
    if not isinstance(source, dict) or source.get("kind") not in F0_KINDS:
        L.boundary(f"{name}: not an F0 artifact", reason="F0 covers expr/circuit/dfa/bdd only")
        rep["status"] = "OUT-OF-SCOPE"
        return rep
    if len(vars) > kernel.MAX_VARS:
        L.boundary(f"{name}: {len(vars)} variables exceeds exhaustive-kernel limit {kernel.MAX_VARS}",
                   reason="no succinct equivalence certificates yet (spike-01 finding F3)")
        rep["status"] = "OUT-OF-SCOPE"
        return rep
    if not _free_vars(source) <= set(vars):
        L.boundary(f"{name}: free variables {sorted(_free_vars(source) - set(vars))} undeclared",
                   reason="semantics is only defined relative to a declared domain (protocol Omega)")
        rep["status"] = "OUT-OF-SCOPE"
        return rep

    # 1-2. semantics + canonical form ---------------------------------------
    tt = semantics(source, vars)
    nf = normal_form(source, vars)
    v = kernel.check({"relation": "extensional", "vars": vars, "left": source, "right": nf})
    c_nf = L.kernel_result(f"{name} ≡_ext N({name}) (ROBDD, order {list(vars)})", v,
                           category="canonicalization",
                           assumptions=["variable order is a declared parameter of N"])
    rep["truth_table"] = tt
    rep["normal_form"] = nf
    if not v.ok:  # main interpreter / canonicalizer bug: stop, do not build on it
        rep["status"] = "INTERNAL-INCONSISTENCY"
        return rep

    # 4-5. extensional realizations ---------------------------------------
    tr = translators or default_translators()
    produced = []
    for tname, fn in tr.items():
        try:
            art = fn(source, nf, vars)
        except Exception as exc:  # untrusted translator crashed
            L.heuristic(f"translator {tname} failed on {name}: {exc!r}", procedure=tname)
            continue
        if art is not None:
            produced.append((tname, art))
    produced.append(("identity", source))

    ext_ok = {}
    for tname, art in produced:
        v = kernel.check({"relation": "extensional", "vars": vars, "left": source, "right": art})
        c = L.kernel_result(f"{tname}({name}) ≡_ext {name}", v, category="translation",
                            depends_on=[c_nf.id] if tname.startswith("nf") else [])
        entry = {"translator": tname, "artifact": art, "cost": cost(art), "claim": c.id,
                 "substrate": SUBSTRATE_OF[art["kind"]], "relation": "extensional"}
        if v.ok:
            rep["candidates"].append(entry)
            ext_ok.setdefault(entry["substrate"], []).append(entry)
        else:
            entry["counterexample"] = v.counterexample
            rep["rejected"].append(entry)

    # 3. task abstraction ---------------------------------------------------
    if care is not None:
        _task_stage(rep, L, source, care, tt, vars, name, max_task_sets)

    # 6. Pareto fronts per (substrate, fidelity relation) --------------------
    # Fidelity is a dimension, not a filter: a task-only realization must not
    # silently "dominate" exact ones (spike-01 finding F5).
    fronts = {}
    for key in {(c["substrate"], c["relation"]) for c in rep["candidates"]}:
        cands = [c for c in rep["candidates"] if (c["substrate"], c["relation"]) == key]
        fronts[key] = pareto_front(cands)
    rep["pareto"] = fronts

    # 7. verified improvements over the incumbent (the source itself) ----
    inc = next(c for c in rep["candidates"] if c["translator"] == "identity")
    for c in rep["candidates"]:
        if c is inc or c["substrate"] != inc["substrate"]:
            continue
        if dominates(c["cost"], inc["cost"]):
            L.derived(f"{c['translator']} improves on incumbent {name}: "
                      f"{c['cost']} dominates {inc['cost']} under {c['relation']} fidelity",
                      depends_on=[c["claim"]], category="improvement",
                      rule="charter §5.7: kernel-checked fidelity + Pareto cost dominance",
                      assumptions=["cost = exact count on the artifact under the F0 cost model"],
                      evidence={"incumbent": inc["cost"], "candidate": c["cost"]})
    rep["status"] = "OK"
    return rep


def _task_stage(rep, L, source, care, tt, vars, name, max_task_sets):
    care_tt = semantics(care, vars)
    if len(vars) > MAX_SUFFICIENCY_VARS:
        L.boundary(f"{name}: sufficiency enumeration skipped ({len(vars)} > {MAX_SUFFICIENCY_VARS} vars)",
                   reason="minimal-transversal enumeration is exponential")
        return
    sets = minimal_sufficient_sets(tt, care_tt)
    srep = sufficiency_report(tt, care_tt)
    rep["sufficiency"] = srep
    c_enum = L.conjecture(
        f"{name}: minimal sufficient sets under care = {srep['minimal_sufficient_sets']}",
        rationale="exact minimal-transversal enumeration (cerp/sufficiency.py), untrusted code",
        open_obligation="completeness of the enumeration is not certified; "
                        "each listed set's sufficiency and minimality IS kernel-checked below",
        category="task-sufficiency")

    task_realizations = []
    for s in sets[:max_task_sets]:
        g = project(tt, care_tt, s)
        g_bdd = truthtable_to_bdd(g)
        # sufficiency of s: g depends only on s and agrees with source on care
        v = kernel.check({"relation": "task", "vars": vars, "left": source, "right": g_bdd, "care": care})
        c_suf = L.kernel_result(f"{sorted(s)} is sufficient for task({name}): projection ≡_T {name}", v,
                                category="task-sufficiency")
        # minimality of s: every v in s has a checkable insufficiency witness for s - {v}
        mins = []
        for x in sorted(s):
            w = insufficiency_witness(tt, care_tt, s - {x})
            if w is None:
                mins = None
                break
            vv = kernel.check_insufficiency({"vars": vars, "f": source, "care": care,
                                             "subset": sorted(s - {x}), "x": w[0], "y": w[1]})
            mins.append(L.kernel_result(f"{sorted(s - {x})} is NOT sufficient for task({name})", vv,
                                        category="task-sufficiency").id)
        if mins is not None:
            L.derived(f"{sorted(s)} is a MINIMAL sufficient set for task({name})",
                      depends_on=[c_suf.id] + mins, category="task-sufficiency",
                      rule="sufficiency is monotone, so minimality = sufficient and every "
                           "one-smaller subset insufficient")
        task_realizations.append((f"proj[{','.join(sorted(s))}]", g_bdd, sorted(s, key=vars.index)))

    # don't-care-aware simplification (Coudert-Madre restrict) -- spike-01 finding F6
    task_realizations.append(("restrict", restrict_to_care(tt, care_tt), list(vars)))

    for label, g_bdd, inputs in task_realizations:
        for tname, art in ((f"task:{label}:bdd", g_bdd),
                           (f"task:{label}:circuit", bdd_to_circuit(g_bdd, inputs)),
                           (f"task:{label}:dfa", bdd_to_dfa(g_bdd)),
                           (f"task:{label}:expr", bdd_to_expr(g_bdd))):
            v = kernel.check({"relation": "task", "vars": vars, "left": source, "right": art, "care": care})
            c = L.kernel_result(f"{tname}({name}) ≡_T {name}", v, category="translation")
            entry = {"translator": tname, "artifact": art, "cost": cost(art),
                     "claim": c.id, "substrate": art["kind"], "relation": "task"}
            if v.ok:
                rep["candidates"].append(entry)
            else:
                entry["counterexample"] = v.counterexample
                rep["rejected"].append(entry)

    # ≡_ext ⊆ ≡_T: every exact realization is also a task realization, so the
    # task front must include them (otherwise "task-optimal" can be worse than exact).
    for c in [c for c in rep["candidates"] if c["relation"] == "extensional"]:
        d = L.derived(f"{c['translator']}({name}) ≡_T {name}", depends_on=[c["claim"]],
                      category="translation", rule="≡_ext implies ≡_T for every care set")
        rep["candidates"].append(dict(c, relation="task", claim=d.id))


def default_translators():
    def only(kind, f):
        return lambda src, nf, vars: f(src, nf, vars) if src["kind"] == kind else None

    return {
        "expr->circuit": only("expr", lambda s, nf, v: expr_to_circuit(s, list(v))),
        "circuit->expr": only("circuit", lambda s, nf, v: circuit_to_expr(s)),
        "nf->bdd": lambda s, nf, v: nf,
        "nf->circuit": lambda s, nf, v: bdd_to_circuit(nf, list(v)),
        "nf->dfa": lambda s, nf, v: bdd_to_dfa(nf),
        "nf->expr": lambda s, nf, v: bdd_to_expr(nf),
        "nf->expr->circuit": lambda s, nf, v: expr_to_circuit(bdd_to_expr(nf), list(v)),
    }


def summarize(rep) -> str:
    L = rep["ledger"]
    lines = [f"# Analysis: {rep['name']}  (status: {rep['status']})", ""]
    if "sufficiency" in rep:
        s = rep["sufficiency"]
        lines += ["## Task sufficiency",
                  f"- minimal sufficient sets: {s['minimal_sufficient_sets']}",
                  f"- necessary: {s['necessary']}  substitutable: {s['substitutable']}  "
                  f"dispensable: {s['dispensable']}", ""]
    if rep.get("pareto"):
        lines.append("## Verified Pareto fronts, per (substrate, fidelity relation)")
        for (sub, rel), front in sorted(rep["pareto"].items()):
            for c in front:
                lines.append(f"- [{sub} / ≡_{'ext' if rel == 'extensional' else 'T'}] "
                             f"{c['translator']}: {c['cost']}  ({c['claim']})")
        lines.append("")
    if rep["rejected"]:
        lines.append("## Rejected by kernel")
        for c in rep["rejected"]:
            lines.append(f"- {c['translator']}: counterexample {c.get('counterexample')}")
        lines.append("")
    lines += ["## Ledger", "", L.to_markdown()]
    return "\n".join(lines)
