"""The project status board: what the theory still lacks to be effective.

  python -m cerp.status            regenerate STATUS.md and claims/status/*.json
  python -m cerp.status --check    fail if STATUS.md is out of date or a source is inconsistent

Sources (edit these, never STATUS.md):
  claims/GAPS.json    the gap register: each missing piece, what closes it, the next action
  claims/RUNS.json    one entry per finished spike: verdicts, what was learned, which gaps moved
  claims/REGISTER.md  the claims (via cerp.register), THEORY.md §5 (conjectures)

AGENTS.md rule 8: after every run, append to RUNS.json, update GAPS.json, regenerate.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

from . import register as R

ROOT = R.ROOT
GAPS = ROOT / "claims" / "GAPS.json"
RUNS = ROOT / "claims" / "RUNS.json"
OUT = ROOT / "STATUS.md"
CSVDIR = ROOT / "claims" / "status"
STATES = ("OPEN", "PARTIAL", "CLOSED")
MOVES = STATES + ("new",)
LEVER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
VERDICTS = ("HELD", "BROKEN", "NEITHER", "NO VERDICT")
CONJ = re.compile(r"^- \*\*(C\d+′?), (.+?)\*\*", re.M)


def claim_class(row):
    s = row.status.upper()
    if "REFUTED" in s: return "Refuted"
    if "METHOD NOTE" in s: return "Method note"
    if "EXPLORATORY" in s: return "Exploratory"
    if "CONJECTURE" in s: return "Conjecture"
    if "PARTLY MECHANIZED" in s: return "Proved on paper"
    if "PROVED" in s and "LEAN" in (s + row.evidence.upper()): return "Proved in Lean"
    if "KERNEL-CHECKED" in s or "PROVED-IN-FRAGMENT" in s: return "Kernel-checked"
    if "PROVED" in s: return "Proved on paper"
    if "EMPIRICAL" in s: return "Empirical"
    if "COMPUTED" in s: return "Computed"
    return "Other"


def conjectures(text):
    out = []
    for cid, rest in CONJ.findall(text):
        m = re.match(r"(.*)\s\(([^()]*(?:\([^()]*\)[^()]*)*)\)\.?$", rest.rstrip("."), re.S)
        title, note = (m.group(1), m.group(2)) if m else (rest.rstrip("."), "")
        u = note.upper()
        state = ("Open" if "CONJECTURE" in u else "Not supported" if "NOT SUPPORTED" in u
                 else "Refuted" if "REFUTED" in u else "Partly" if ("PARTLY SUPPORTED" in u or "PARTLY PROVED" in u)
                 else "Supported" if "SUPPORTED" in u else "Proved" if "PROVED" in u
                 else "Withdrawn" if "WITHDRAWN" in u else "Open")
        out.append({"id": cid, "title": title, "state": state, "note": note})
    return sorted(out, key=lambda c: int(re.sub(r"\D", "", c["id"])))


def collect():
    g = json.loads(GAPS.read_text(encoding="utf-8")); runs = json.loads(RUNS.read_text(encoding="utf-8"))["runs"]
    rows = R.parse(); ids = {r.id for r in rows}
    problems, notes, led = R.check()
    report = (ROOT / "claims" / "LEDGER_CHECK.md").read_text(encoding="utf-8")
    weak = re.findall(r"^- (P\d{3}) \((\d+) note\(s\)\): (.*?) \| (.*)$", report.split("## Weakest links")[1].split("## Corrections")[0], re.M)
    errs = [f"ledger: {p}" for p in problems]
    gid = {x["id"] for x in g["gaps"]}; eid = {e["id"] for e in g["effective_when"]}
    for x in g["gaps"]:
        if x["status"] not in STATES: errs.append(f"{x['id']}: status {x['status']}")
        if x["leverage"] not in LEVER: errs.append(f"{x['id']}: leverage {x['leverage']}")
        if x["serves"] not in eid: errs.append(f"{x['id']}: serves unknown {x['serves']}")
        errs += [f"{x['id']}: cites unknown claim {c}" for c in x.get("claims", []) if c not in ids]
        errs += [f"{x['id']}: blocked by unknown gap {b}" for b in x.get("blocked_by", []) if b not in gid]
    for r in runs:
        if not (ROOT / "experiments" / f"SPIKE_{r['spike']}_REPORT.md").exists(): errs.append(f"run {r['spike']}: no report")
        errs += [f"run {r['spike']}: verdict {v['verdict']}" for v in r["verdicts"] if v["verdict"] not in VERDICTS]
        errs += [f"run {r['spike']}: unknown gap {m['gap']}" for m in r.get("gaps_moved", []) if m["gap"] not in gid]
        errs += [f"run {r['spike']}: unknown claim {c}" for c in r.get("claims", []) if c not in ids]
    classes = {}
    for r in rows:
        classes[claim_class(r)] = classes.get(claim_class(r), 0) + 1
    frozen = json.loads(R.FROZEN.read_text(encoding="utf-8")) if R.FROZEN.exists() else {}
    return {"g": g, "runs": runs, "rows": rows, "notes": notes, "weak": weak, "errs": errs, "classes": classes,
            "conj": conjectures((ROOT / "THEORY.md").read_text(encoding="utf-8")), "frozen": len(frozen)}


def criteria(d):
    """Per effectiveness criterion: gaps open / partial / closed and a 0-1 progress score (closed 1, partial 0.5)."""
    out = []
    for e in d["g"]["effective_when"]:
        gs = [x for x in d["g"]["gaps"] if x["serves"] == e["id"]]
        n = {s: sum(x["status"] == s for x in gs) for s in STATES}
        out.append({**e, **n, "gaps": len(gs), "progress": round((n["CLOSED"] + 0.5 * n["PARTIAL"]) / len(gs), 2) if gs else 0.0})
    return out


def render(d):
    g = d["g"]; L = ["# semplex status board", "",
        "Generated by `python -m cerp.status` from `claims/GAPS.json`, `claims/RUNS.json`, `claims/REGISTER.md` and `THEORY.md`. Do not edit by hand.", "",
        f"**Goal.** {g['goal']}", "", "## 1. Is the theory effective yet?", "",
        "| Criterion | The test it must pass | Gaps open | Partial | Closed | Progress |", "|---|---|---|---|---|---|"]
    for c in criteria(d):
        L.append(f"| **{c['id']} {c['name']}** | {c['test']} | {c['OPEN']} | {c['PARTIAL']} | {c['CLOSED']} | {int(100 * c['progress'])}% |")
    L += ["", "Progress counts a closed gap as 1 and a partial one as ½. It measures the gap list, not truth: a new finding can add gaps.", "",
          "## 2. Next actions, by leverage", "", "| Gap | Leverage | State | What is missing | Closes when | Next |", "|---|---|---|---|---|---|"]
    order = sorted([x for x in g["gaps"] if x["status"] != "CLOSED"], key=lambda x: (LEVER[x["leverage"]], bool(x.get("blocked_by")), x["id"]))
    for x in order:
        blk = f" (blocked by {', '.join(x['blocked_by'])})" if x.get("blocked_by") else ""
        L.append(f"| **{x['id']}** {x['title']} | {x['leverage']} | {x['status']}{blk} | {x['missing']} | {x['closes_when']} | {x['next']} |")
    L += ["", "## 3. The gap register, by pillar", ""]
    for p in dict.fromkeys(x["pillar"] for x in g["gaps"]):
        L += [f"### {p}", "", "| Gap | Serves | State | What we have | Claims |", "|---|---|---|---|---|"]
        L += [f"| **{x['id']}** {x['title']} | {x['serves']} | {x['status']} | {x['have']} | {', '.join(x.get('claims', []))} |" for x in g["gaps"] if x["pillar"] == p]
        L.append("")
    L += ["## 4. Run reports, newest first", ""]
    for r in reversed(d["runs"]):
        L += [f"### Spike {r['spike']}: {r['question']}", "",
              f"{r['date']} · commit `{r['commit']}` · overall **{r['overall']}** · report `experiments/SPIKE_{r['spike']}_REPORT.md` · claims {', '.join(r.get('claims', [])) or 'none'}", "",
              "| Hypothesis | Verdict | Measured | Criterion |", "|---|---|---|---|"]
        L += [f"| {v['id']} | **{v['verdict']}** | {v['measured']} | {v['bar']} |" for v in r["verdicts"]]
        L += ["", f"**Learned.** {r['learned']}", ""]
        L += [f"- Gap {m['gap']}: {m['from']} → {m['to']}. {m['why']}." for m in r.get("gaps_moved", [])] + [""]
    L += ["## 5. Conjectures", "", "| ID | Conjecture | State | Detail |", "|---|---|---|---|"]
    L += [f"| {c['id']} | {c['title']} | {c['state']} | {c['note']} |" for c in d["conj"]]
    L += ["", "## 6. Ledger health", "",
          f"- Claims: {len(d['rows'])}. " + "; ".join(f"{k}: {v}" for k, v in sorted(d["classes"].items(), key=lambda kv: -kv[1])) + ".",
          f"- Problems: {len([e for e in d['errs'] if e.startswith('ledger')])}. Claims stated stronger than their support: {len(d['notes'])}.",
          f"- Frozen spike files (rule 2): {d['frozen']}.", "", "Weakest links (fixing one lifts every note that rests on it):", "",
          "| Claim | Notes resting on it | Its status | Statement |", "|---|---|---|---|"]
    L += [f"| {a} | {b} | {c} | {s[:140]} |" for a, b, c, s in d["weak"][:6]]
    return "\n".join(L) + "\n"


def tables(d):
    """Flat tables for the dashboard page, as JSON rows."""
    g = d["g"]
    t = {"criteria": [{k: c[k] for k in ("id", "name", "test", "gaps", "OPEN", "PARTIAL", "CLOSED")} | {"progress_pct": int(round(100 * c["progress"]))} for c in criteria(d)],
         "gaps": [{"id": x["id"], "pillar": x["pillar"], "serves": x["serves"], "title": x["title"], "status": x["status"], "leverage": x["leverage"],
                   "have": x["have"], "missing": x["missing"], "closes_when": x["closes_when"], "next": x["next"],
                   "blocked_by": " ".join(x.get("blocked_by", [])), "claims": " ".join(x.get("claims", []))} for x in g["gaps"]],
         "runs": [{"spike": r["spike"], "date": r["date"], "commit": r["commit"], "question": r["question"], "overall": r["overall"], "learned": r["learned"],
                   "moved": "; ".join(f"{m['gap']}: {m['from']} → {m['to']} ({m['why']})" for m in r.get("gaps_moved", [])),
                   "claims": " ".join(r.get("claims", []))} for r in d["runs"]],
         "verdicts": [{"key": f"{r['spike']}:{v['id']}", "spike": r["spike"], "id": v["id"], "verdict": v["verdict"], "measured": v["measured"], "bar": v["bar"]}
                      for r in d["runs"] for v in r["verdicts"]],
         "conjectures": d["conj"],
         "claim_classes": [{"class": k, "claims": v} for k, v in sorted(d["classes"].items(), key=lambda kv: -kv[1])],
         "weak_links": [{"claim": a, "notes": int(b), "status": c, "statement": s[:200]} for a, b, c, s in d["weak"][:8]],
         "ledger": [{"metric": "Claims", "value": len(d["rows"])}, {"metric": "Ledger problems", "value": len([e for e in d["errs"] if e.startswith("ledger")])},
                    {"metric": "Claims stated stronger than their support", "value": len(d["notes"])}, {"metric": "Frozen spike files", "value": d["frozen"]}]}
    return {name: json.dumps(rows, indent=1, ensure_ascii=False) + "\n" for name, rows in t.items()}


def main(argv):
    d = collect(); text = render(d); tb = tables(d)
    for e in d["errs"]:
        print("  PROBLEM", e)
    if "--check" in argv:
        stale = (not OUT.exists() or OUT.read_text(encoding="utf-8") != text
                 or any(not (CSVDIR / f"{k}.json").exists() or (CSVDIR / f"{k}.json").read_text(encoding="utf-8") != v for k, v in tb.items()))
        if stale:
            print("STATUS.md or claims/status/ is out of date: run python -m cerp.status")
        return 1 if (stale or d["errs"]) else 0
    OUT.write_text(text, encoding="utf-8"); CSVDIR.mkdir(exist_ok=True)
    for k, v in tb.items():
        (CSVDIR / f"{k}.json").write_text(v, encoding="utf-8")
    c = criteria(d)
    print(f"STATUS.md written: {len(d['g']['gaps'])} gaps, " + ", ".join(f"{x['id']} {int(100 * x['progress'])}%" for x in c) + f"; {len(d['errs'])} problem(s)")
    return 1 if d["errs"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
