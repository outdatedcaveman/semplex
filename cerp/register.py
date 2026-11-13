"""The program claims register (claims/REGISTER.md) as a ledger (charter §13.20; THEORY C5).

  python -m cerp.register check            validate, project effective status, write claims/LEDGER_CHECK.md
  python -m cerp.register affected P110    every claim that transitively depends on P110

Why: the register has been corrected by hand three times (P099 fitter, P113 confound,
P117 label imbalance). Each correction must reach every claim built on the corrected
one. The ledger already joins warrants along dependencies and computes the
invalidation set; this module loads the register into it.

Mapping from the register's free-text status to a ledger warrant, weakest reading wins:
  REFUTED                      -> outcome REFUTED
  METHOD NOTE                  -> category "method-note" (no strength claim)
  EXPLORATORY                  -> HEURISTIC
  CONJECTURE                   -> RATIONALE
  EMPIRICALLY-SUPPORTED/-CONFIRMED -> EMPIRICAL
  COMPUTED-UNCERTIFIED         -> EXACT_UNCERTIFIED
  kernel-checked / PROVED-IN-FRAGMENT -> KERNEL_CHECKED
  PROVED with Lean in the evidence    -> PROOF_ASSISTANT
  PROVED (literature)          -> ASSUMPTION   (rests on a cited source)
  PROVED (informal / sketch)   -> RATIONALE    (argued, not mechanized)
A status combining several (e.g. "PROVED + EMPIRICALLY-SUPPORTED") gets every
matching method; the projection then reports the weakest.
"""

from __future__ import annotations

import pathlib
import re
import sys
from dataclasses import dataclass

from .ledger import PY_TB, Claim, Ledger, LedgerError, Method, Outcome, Status, Warrant, project

ROOT = pathlib.Path(__file__).resolve().parent.parent
REGISTER = ROOT / "claims" / "REGISTER.md"
REPORT = ROOT / "claims" / "LEDGER_CHECK.md"
COLS = ("id", "statement", "status", "scope", "evidence", "depends", "caveats", "next")
SPLIT = re.compile(r"(?<!\\)\|")
PID = re.compile(r"P(\d{3})")
RANGE = re.compile(r"P(\d{3})\s*[–-]\s*P(\d{3})")


@dataclass
class Row:
    id: str
    statement: str
    status: str
    scope: str
    evidence: str
    depends: list
    caveats: str
    next: str


def parse(path=REGISTER):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| P"):
            continue
        cells = [c.strip() for c in SPLIT.split(line.strip().strip("|"))]
        cells = (cells + [""] * len(COLS))[: len(COLS)]
        d = dict(zip(COLS, cells))
        deps = set()
        for a, b in RANGE.findall(d["depends"]):
            deps |= {f"P{i:03d}" for i in range(int(a), int(b) + 1)}
        deps |= {f"P{m}" for m in PID.findall(RANGE.sub("", d["depends"]))}
        deps.discard(d["id"])
        rows.append(Row(depends=sorted(deps), **{k: d[k] for k in COLS if k != "depends"}))
    return rows


def methods_for(row):
    s = row.status.upper()
    m = set()
    if "EXPLORATORY" in s:
        m.add(Method.HEURISTIC)
    if "CONJECTURE" in s:
        m.add(Method.RATIONALE)
    if "EMPIRICAL" in s:
        m.add(Method.EMPIRICAL)
    if "COMPUTED-UNCERTIFIED" in s:
        m.add(Method.EXACT_UNCERTIFIED)
    if "KERNEL-CHECKED" in s or "PROVED-IN-FRAGMENT" in s:
        m.add(Method.KERNEL_CHECKED)
    if re.search(r"\bPROVED\b(?!-IN)", s):
        if "LEAN" in (row.evidence + row.status).upper():
            m.add(Method.PROOF_ASSISTANT)
        elif "LITERATURE" in s:
            m.add(Method.ASSUMPTION)
        else:
            m.add(Method.RATIONALE)
    return m or {Method.HEURISTIC}


def load(path=REGISTER):
    rows = parse(path)
    led = Ledger(prefix="P")
    for r in rows:
        refuted = "REFUTED" in r.status.upper()
        note = "METHOD NOTE" in r.status.upper()
        c = Claim(id=r.id, statement=r.statement,
                  warrant=Warrant(frozenset(methods_for(r)), PY_TB | {"analysis code"}),
                  outcome=Outcome.REFUTED if refuted else Outcome.ASSERTED,
                  category="method-note" if note else "program", depends_on=[],
                  evidence={"register_status": r.status, "evidence": r.evidence})
        led.claims[r.id] = c
    unknown = {}
    for r in rows:
        ok = [d for d in r.depends if d in led.claims]
        bad = [d for d in r.depends if d not in led.claims]
        led.claims[r.id].depends_on = ok
        if bad:
            unknown[r.id] = bad
    return rows, led, unknown


def check(path=REGISTER):
    rows, led, unknown = load(path)
    problems, notes = [], []
    for cid, bad in unknown.items():
        problems.append(f"{cid}: depends on unknown claim(s) {', '.join(bad)}")
    for r in rows:
        try:
            eff = led.effective_warrant(r.id)
        except LedgerError as e:
            problems.append(str(e)); continue
        c = led.claims[r.id]
        if c.category == "method-note" or c.outcome is Outcome.REFUTED:
            continue
        own, effective = project(c.warrant, c.outcome), project(eff, c.outcome)
        if own is not effective:
            notes.append(f"{r.id}: stated {own.label}, but rests on weaker support -> effectively {effective.label}")
        refuted_deps = [d for d in c.depends_on if led.claims[d].outcome is Outcome.REFUTED]
        if refuted_deps and not re.search(r"supersed|refut|replac|correct", r.caveats + r.next + r.statement, re.I):
            problems.append(f"{r.id}: depends on refuted {', '.join(refuted_deps)} without saying how it survives")
    weak = {Method.RATIONALE, Method.ASSUMPTION, Method.HEURISTIC}

    def weak_roots(cid, seen):
        out = set()
        for d in led.claims[cid].depends_on:
            if d in seen:
                continue
            seen.add(d)
            if led.claims[d].warrant.basis & weak:
                out.add(d)
            out |= weak_roots(d, seen)
        return out
    root_count = {}
    for n in notes:
        for x in weak_roots(n.split(":")[0], set()):
            root_count[x] = root_count.get(x, 0) + 1
    corrections = [r.id for r in rows if "METHOD NOTE" in r.status.upper() or "corrects" in (r.caveats + r.evidence).lower()]
    lines = ["# Ledger check of the claims register", "",
             "Generated by `python -m cerp.register check` from `claims/REGISTER.md`. Do not edit by hand.", "",
             f"- Claims: {len(rows)}; dependency links: {sum(len(c.depends_on) for c in led.claims.values())}",
             f"- Problems (must fix): {len(problems)}",
             f"- Status notes (a claim stated stronger than what it rests on): {len(notes)}", ""]
    lines += ["## Problems", ""] + ([f"- {p}" for p in problems] or ["None."]) + [""]
    lines += ["## Status notes", ""] + ([f"- {n}" for n in notes] or ["None."]) + [""]
    byid = {r.id: r for r in rows}
    lines += ["## Weakest links behind the status notes", "",
              "Upgrading these (e.g. mechanizing a paper proof in Lean) lifts every note that rests on them.", ""]
    lines += [f"- {k} ({v} note(s)): {byid[k].status} | {byid[k].statement[:120]}"
              for k, v in sorted(root_count.items(), key=lambda kv: -kv[1])] or ["None."]
    lines += ["", "## Corrections: claims to re-review", "",
              "A correction depends on the claim it corrects. Every other claim built on the corrected one must be re-read in its light.", ""]
    for cid in corrections:
        for target in led.claims[cid].depends_on:
            others = [x for x in led.affected_by(target) if x != cid]
            lines.append(f"- {cid} corrects {target}; also built on {target}: {', '.join(others) if others else '(none)'}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return problems, notes, led


def main(argv):
    if len(argv) >= 2 and argv[0] == "affected":
        _, led, _ = load()
        for cid in argv[1:]:
            print(cid, "->", ", ".join(led.affected_by(cid)) or "(nothing depends on it)")
        return 0
    problems, notes, _ = check()
    print(f"{len(problems)} problem(s), {len(notes)} status note(s); report: {REPORT.relative_to(ROOT)}")
    for p in problems:
        print("  PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
