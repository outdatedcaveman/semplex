"""Claims ledger with enforced status discipline (charter §3.2, §10, §13.20).

Enforced invariants (tests/test_ledger.py):
  1. PROVED-IN-FRAGMENT can only be recorded with an authentic, positive
     kernel Verdict. There is no API to "upgrade" a claim's status.
  2. A claim's EFFECTIVE status is capped by its weakest dependency.
  3. Failed checks are recorded (REFUTED, with counterexample), not dropped.
  4. Boundaries (out-of-scope, undecidable, too large) are first-class claims.

v0 simplification, flagged as open question Q-L1: statuses are treated as
a total order for the "weakest dependency" rule. The charter's labels are
not really a chain (CERTIFIED-REFINEMENT vs PROVED-IN-FRAGMENT differ in
*kind*, not strength), so a product/lattice structure is likely needed.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum

from . import kernel


class Status(Enum):
    # value = rank in the v0 total order (higher = stronger warrant)
    PROVED = 8
    PROVED_IN_FRAGMENT = 7
    CERTIFIED_REFINEMENT = 6
    EMPIRICALLY_SUPPORTED = 5
    CALIBRATED_PROBABILISTIC = 4
    CONJECTURE = 3
    HEURISTIC = 2
    OUT_OF_SCOPE = 1
    REFUTED = 0

    @property
    def label(self):
        return self.name.replace("_", "-")


@dataclass
class Claim:
    id: str
    statement: str
    status: Status
    category: str
    assumptions: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    trusted_base: list = field(default_factory=list)
    notes: str = ""


class LedgerError(Exception):
    pass


class Ledger:
    def __init__(self, prefix="C"):
        self.prefix = prefix
        self.claims: dict[str, Claim] = {}

    def _add(self, **kw) -> Claim:
        for d in kw.get("depends_on", []):
            if d not in self.claims:
                raise LedgerError(f"unknown dependency {d}")
        cid = f"{self.prefix}{len(self.claims) + 1:03d}"
        c = Claim(id=cid, **kw)
        self.claims[cid] = c
        return c

    # ------------------------------------------------------------ recorders
    def kernel_result(self, statement, verdict, *, category, assumptions=(), depends_on=(), notes=""):
        """Record a kernel verdict: PROVED-IN-FRAGMENT if ok, else REFUTED."""
        if not isinstance(verdict, kernel.Verdict) or not verdict.authentic:
            raise LedgerError("only authentic kernel verdicts can back a proof-status claim")
        return self._add(
            statement=statement,
            status=Status.PROVED_IN_FRAGMENT if verdict.ok else Status.REFUTED,
            category=category,
            assumptions=list(assumptions) + [
                f"domain = {{0,1}}^{list(verdict.vars)} (exhaustive, {verdict.points_checked} points)"
                if verdict.relation != "insufficient" else "certificate check (2 evaluations)",
            ],
            evidence={"kernel_version": verdict.kernel_version, "relation": verdict.relation,
                      "points_checked": verdict.points_checked,
                      "counterexample": verdict.counterexample},
            depends_on=list(depends_on),
            trusted_base=[f"cerp/kernel.py v{verdict.kernel_version}", "CPython", "hardware"],
            notes=notes,
        )

    def empirical(self, statement, *, protocol, data, uncertainty, category="empirical",
                  assumptions=(), depends_on=(), notes=""):
        if not protocol or data is None or not uncertainty:
            raise LedgerError("empirical claims need protocol, data and an uncertainty statement")
        return self._add(statement=statement, status=Status.EMPIRICALLY_SUPPORTED, category=category,
                         assumptions=list(assumptions),
                         evidence={"protocol": protocol, "data": data, "uncertainty": uncertainty},
                         depends_on=list(depends_on), notes=notes)

    def conjecture(self, statement, *, rationale, open_obligation, category="conjecture",
                   depends_on=(), notes=""):
        return self._add(statement=statement, status=Status.CONJECTURE, category=category,
                         evidence={"rationale": rationale, "open_obligation": open_obligation},
                         depends_on=list(depends_on), notes=notes)

    def heuristic(self, statement, *, procedure, category="heuristic", depends_on=(), notes=""):
        return self._add(statement=statement, status=Status.HEURISTIC, category=category,
                         evidence={"procedure": procedure}, depends_on=list(depends_on), notes=notes)

    def derived(self, statement, *, depends_on, rule, category, assumptions=(), evidence=None, notes=""):
        """A claim that follows from its dependencies by a stated rule.

        Its own status is the weakest effective status of its dependencies;
        there is no way to pass a stronger one in.
        """
        if not depends_on:
            raise LedgerError("a derived claim needs dependencies")
        for d in depends_on:
            if d not in self.claims:
                raise LedgerError(f"unknown dependency {d}")
        status = min((self.effective_status(d) for d in depends_on), key=lambda s: s.value)
        ev = dict(evidence or {})
        ev["rule"] = rule
        return self._add(statement=statement, status=status, category=category,
                         assumptions=list(assumptions), evidence=ev,
                         depends_on=list(depends_on), notes=notes)

    def boundary(self, statement, *, reason, category="boundary", notes=""):
        return self._add(statement=statement, status=Status.OUT_OF_SCOPE, category=category,
                         evidence={"reason": reason}, notes=notes)

    # ------------------------------------------------------------ queries
    def effective_status(self, cid, _seen=None) -> Status:
        _seen = _seen or set()
        if cid in _seen:
            raise LedgerError(f"dependency cycle through {cid}")
        c = self.claims[cid]
        s = c.status
        for d in c.depends_on:
            ds = self.effective_status(d, _seen | {cid})
            if ds.value < s.value:
                s = ds
        return s

    def by_status(self, status: Status):
        return [c for c in self.claims.values() if self.effective_status(c.id) == status]

    def to_json(self) -> str:
        def enc(c):
            d = asdict(c)
            d["status"] = c.status.label
            d["effective_status"] = self.effective_status(c.id).label
            return d
        return json.dumps([enc(c) for c in self.claims.values()], indent=2, default=str)

    def to_markdown(self) -> str:
        rows = ["| ID | Effective status | Category | Statement | Depends on |",
                "|---|---|---|---|---|"]
        for c in self.claims.values():
            eff = self.effective_status(c.id)
            st = eff.label + ("" if eff == c.status else f" (own: {c.status.label})")
            rows.append(f"| {c.id} | {st} | {c.category} | {c.statement} | {', '.join(c.depends_on)} |")
        return "\n".join(rows)
