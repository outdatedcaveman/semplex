"""Claims ledger with structured warrants (charter §3.2, §10, §13.20; Spike 04).

Spike 01 (F7) and Spike 02 (F8) showed that a single status label cannot
carry the warrant of a claim: the labels are not a chain, and several real
outputs (an exact-but-uncertified enumeration, a numerically checked
existence witness, a result conditional on a declared premise) had no
honest label. So a claim now carries a WARRANT:

    Warrant = (basis, trusted_base, conditions)
      basis         set of Methods the claim ultimately rests on
      trusted_base  what must be correct for the warrant to hold
      conditions    open premises (ids of ASSUMPTION claims) it is conditional on

and, separately, an OUTCOME (asserted / refuted / out-of-scope /
undetermined), which is what the claim says rather than how well it is
backed. A refutation decided by the kernel is a *strongly* warranted
negative claim, not a weak one -- the old chain conflated the two.

Warrants are partially ordered (`stronger_or_equal`). Derived claims get
the JOIN of their dependencies' warrants (union of bases, trusted bases
and conditions), so a derived claim can never look stronger than what it
rests on. Charter §10 labels are a lossy PROJECTION (`Status`), kept for
reporting and backward compatibility.

Enforced invariants (tests):
  1. KERNEL_CHECKED only with an authentic kernel Verdict; no upgrade API.
  2. Effective warrant = own warrant joined with all dependencies'.
  3. Failed checks are recorded (outcome REFUTED), not dropped.
  4. Boundaries and undetermined answers are first-class claims.
  5. Retraction propagates to dependents; history is never deleted.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum

from . import kernel


# ------------------------------------------------------------------ methods

class Method(Enum):
    PROOF_ASSISTANT = "proof-assistant"      # checked by the Lean 4 kernel via cerp.lean_bridge
    KERNEL_CHECKED = "kernel-checked"        # decided or certificate-checked by cerp.kernel
    WITNESS_CHECKED = "witness-checked"      # existence witness re-checked numerically, outside kernel
    EXACT_UNCERTIFIED = "exact-uncertified"  # exact algorithm, unverified code, no certificate
    EMPIRICAL = "empirical"                  # measurement / statistical test under a protocol
    ASSUMPTION = "assumption"                # declared premise; not argued, not tested
    RATIONALE = "rationale"                  # argued conjecture with an open obligation
    HEURISTIC = "heuristic"                  # no guarantee claimed


# Hasse diagram of the method order: a -> b means a is stronger than b.
_ABOVE = {
    Method.PROOF_ASSISTANT: {Method.KERNEL_CHECKED},
    Method.KERNEL_CHECKED: {Method.WITNESS_CHECKED},
    Method.WITNESS_CHECKED: {Method.EXACT_UNCERTIFIED},
    Method.EXACT_UNCERTIFIED: {Method.RATIONALE},
    Method.EMPIRICAL: {Method.RATIONALE},     # incomparable with the deductive chain
    Method.ASSUMPTION: {Method.HEURISTIC},    # incomparable with RATIONALE: premise vs argued guess
    Method.RATIONALE: {Method.HEURISTIC},
    Method.HEURISTIC: set(),
}


def method_geq(a: Method, b: Method) -> bool:
    if a == b:
        return True
    return any(method_geq(x, b) for x in _ABOVE[a])


@dataclass(frozen=True)
class Warrant:
    basis: frozenset
    trusted_base: frozenset = frozenset()
    conditions: frozenset = frozenset()

    def join(self, other: "Warrant") -> "Warrant":
        """Warrant of something resting on both (weakest-link combination)."""
        return Warrant(self.basis | other.basis, self.trusted_base | other.trusted_base,
                       self.conditions | other.conditions)

    def stronger_or_equal(self, other: "Warrant") -> bool:
        """self ⪰ other: no weaker method link, no extra trust, no extra conditions."""
        return (all(any(method_geq(a, b) for b in other.basis) for a in self.basis)
                and self.trusted_base <= other.trusted_base
                and self.conditions <= other.conditions)

    def describe(self) -> str:
        s = "+".join(sorted(m.value for m in self.basis))
        if self.conditions:
            s += f" | conditional on {sorted(self.conditions)}"
        return s


def compare(a: Warrant, b: Warrant) -> str:
    ab, ba = a.stronger_or_equal(b), b.stronger_or_equal(a)
    return "=" if ab and ba else "⪰" if ab else "⪯" if ba else "incomparable"


# ------------------------------------------------------------------ outcomes & labels

class Outcome(Enum):
    ASSERTED = "asserted"
    REFUTED = "refuted"            # the claim as stated was shown false
    OUT_OF_SCOPE = "out-of-scope"  # no result; boundary stated
    UNDETERMINED = "undetermined"  # in scope, but evidence does not decide


class Status(Enum):
    """Charter §10 labels -- now a lossy projection of (warrant, outcome).

    Two labels are new (Spike 04 proposal): COMPUTED-UNCERTIFIED and
    WITNESSED. CERTIFIED-REFINEMENT is not a warrant at all: refinement is
    the claim's *relation*; its warrant is KERNEL_CHECKED like any other.
    """
    PROVED = "PROVED"
    PROVED_IN_FRAGMENT = "PROVED-IN-FRAGMENT"
    WITNESSED = "WITNESSED"
    COMPUTED_UNCERTIFIED = "COMPUTED-UNCERTIFIED"
    EMPIRICALLY_SUPPORTED = "EMPIRICALLY-SUPPORTED"
    CONJECTURE = "CONJECTURE"
    HEURISTIC = "HEURISTIC"
    OUT_OF_SCOPE = "OUT-OF-SCOPE"
    REFUTED = "REFUTED"
    RETRACTED = "RETRACTED"

    @property
    def label(self):
        return self.value


# Projection order: the first matching method (weakest first) names the label.
_PROJECTION = (
    (Method.HEURISTIC, Status.HEURISTIC),
    (Method.RATIONALE, Status.CONJECTURE),
    (Method.ASSUMPTION, Status.CONJECTURE),
    (Method.EMPIRICAL, Status.EMPIRICALLY_SUPPORTED),
    (Method.EXACT_UNCERTIFIED, Status.COMPUTED_UNCERTIFIED),
    (Method.WITNESS_CHECKED, Status.WITNESSED),
    (Method.KERNEL_CHECKED, Status.PROVED_IN_FRAGMENT),
    (Method.PROOF_ASSISTANT, Status.PROVED),
)


def project(w: Warrant, outcome: Outcome, retracted=False) -> Status:
    if retracted:
        return Status.RETRACTED
    if outcome is Outcome.REFUTED:
        return Status.REFUTED
    if outcome in (Outcome.OUT_OF_SCOPE, Outcome.UNDETERMINED):
        return Status.OUT_OF_SCOPE
    for m, s in _PROJECTION:
        if m in w.basis:
            return s
    return Status.HEURISTIC


# ------------------------------------------------------------------ claims

@dataclass
class Claim:
    id: str
    statement: str
    warrant: Warrant
    outcome: Outcome
    category: str
    assumptions: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    notes: str = ""
    retracted_by: str | None = None

    @property
    def status(self) -> Status:
        """Label of the claim's OWN warrant (ignores dependencies and retraction)."""
        return project(self.warrant, self.outcome)

    @property
    def trusted_base(self):
        return sorted(self.warrant.trusted_base)


class LedgerError(Exception):
    pass


KERNEL_TB = frozenset({f"cerp/kernel.py v{kernel.KERNEL_VERSION}", "CPython", "hardware"})
PY_TB = frozenset({"CPython", "hardware"})


class Ledger:
    def __init__(self, prefix="C"):
        self.prefix = prefix
        self.claims: dict[str, Claim] = {}

    def _add(self, *, warrant, outcome=Outcome.ASSERTED, depends_on=(), **kw) -> Claim:
        for d in depends_on:
            if d not in self.claims:
                raise LedgerError(f"unknown dependency {d}")
        cid = f"{self.prefix}{len(self.claims) + 1:03d}"
        c = Claim(id=cid, warrant=warrant, outcome=outcome, depends_on=list(depends_on), **kw)
        self.claims[cid] = c
        return c

    # ------------------------------------------------------------ recorders
    def kernel_result(self, statement, verdict, *, category, assumptions=(), depends_on=(), notes=""):
        """A kernel verdict: an asserted claim if ok, a (strongly warranted) refutation if not."""
        if not isinstance(verdict, kernel.Verdict) or not verdict.authentic:
            raise LedgerError("only authentic kernel verdicts can back a kernel-checked claim")
        how = {"insufficient": "certificate check (2 evaluations)",
               "rup": f"RUP refutation certificate ({verdict.points_checked} lemmas checked)"}.get(
            verdict.relation,
            f"domain = {{0,1}}^{list(verdict.vars)} (exhaustive, {verdict.points_checked} points)")
        return self._add(
            statement=statement, category=category,
            warrant=Warrant(frozenset({Method.KERNEL_CHECKED}), KERNEL_TB),
            outcome=Outcome.ASSERTED if verdict.ok else Outcome.REFUTED,
            assumptions=list(assumptions) + [how],
            evidence={"kernel_version": verdict.kernel_version, "relation": verdict.relation,
                      "points_checked": verdict.points_checked, "counterexample": verdict.counterexample},
            depends_on=depends_on, notes=notes)

    def proof_assistant(self, statement, check, *, category, bridge=(), depends_on=(), notes=""):
        """A theorem checked by Lean (cerp.lean_bridge). The trusted base names the
        Lean kernel, the compiler if native evaluation was used, and every
        unverified bridge step (e.g. the Python Tseitin encoder)."""
        from . import lean_bridge
        if not isinstance(check, lean_bridge.LeanCheck) or not check.authentic or not check.ok:
            raise LedgerError("only an authentic, successful LeanCheck can back a proof-assistant claim")
        tb = {f"Lean kernel ({check.lean_version.split(',')[0]})"} | set(bridge)
        if "Lean.ofReduceBool" in check.axioms:
            tb.add("Lean compiler + runtime (native_decide)")
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.PROOF_ASSISTANT}), frozenset(tb)),
                         evidence={"theorem": check.theorem, "lean_statement": check.statement,
                                   "axioms": list(check.axioms), "source_sha256": check.source_sha256},
                         depends_on=depends_on, notes=notes)

    def empirical(self, statement, *, protocol, data, uncertainty, category="empirical",
                  assumptions=(), depends_on=(), trusted_base=("analysis code",), notes=""):
        if not protocol or data is None or not uncertainty:
            raise LedgerError("empirical claims need protocol, data and an uncertainty statement")
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.EMPIRICAL}), PY_TB | frozenset(trusted_base)),
                         assumptions=list(assumptions),
                         evidence={"protocol": protocol, "data": data, "uncertainty": uncertainty},
                         depends_on=depends_on, notes=notes)

    def computed(self, statement, *, algorithm, category="computed", depends_on=(), notes=""):
        """Output of an exact algorithm whose code is not verified and emits no certificate."""
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.EXACT_UNCERTIFIED}), PY_TB | {algorithm}),
                         evidence={"algorithm": algorithm}, depends_on=depends_on, notes=notes)

    def witnessed(self, statement, *, witness_check, category="witness", depends_on=(), notes=""):
        """An existence claim backed by a witness re-checked numerically outside the kernel."""
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.WITNESS_CHECKED}), PY_TB | {witness_check}),
                         evidence={"witness_check": witness_check}, depends_on=depends_on, notes=notes)

    def assumption(self, statement, *, why, category="assumption", notes=""):
        """A declared premise. Everything depending on it becomes conditional on it."""
        c = self._add(statement=statement, category=category,
                      warrant=Warrant(frozenset({Method.ASSUMPTION})), evidence={"why": why}, notes=notes)
        c.warrant = Warrant(c.warrant.basis, c.warrant.trusted_base, frozenset({c.id}))
        return c

    def conjecture(self, statement, *, rationale, open_obligation, category="conjecture",
                   depends_on=(), notes=""):
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.RATIONALE})),
                         evidence={"rationale": rationale, "open_obligation": open_obligation},
                         depends_on=depends_on, notes=notes)

    def heuristic(self, statement, *, procedure, category="heuristic", depends_on=(), notes=""):
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.HEURISTIC})),
                         evidence={"procedure": procedure}, depends_on=depends_on, notes=notes)

    def derived(self, statement, *, depends_on, rule, category, assumptions=(), evidence=None, notes=""):
        """Follows from its dependencies by a stated rule. Its warrant is the
        join of theirs; there is no way to pass a stronger one in."""
        if not depends_on:
            raise LedgerError("a derived claim needs dependencies")
        for d in depends_on:
            if d not in self.claims:
                raise LedgerError(f"unknown dependency {d}")
        w = Warrant(frozenset())
        for d in depends_on:
            w = w.join(self.effective_warrant(d))
        ev = dict(evidence or {})
        ev["rule"] = rule
        return self._add(statement=statement, category=category, warrant=w,
                         assumptions=list(assumptions), evidence=ev, depends_on=depends_on, notes=notes)

    def boundary(self, statement, *, reason, category="boundary", undetermined=False, notes=""):
        return self._add(statement=statement, category=category,
                         warrant=Warrant(frozenset({Method.HEURISTIC})),
                         outcome=Outcome.UNDETERMINED if undetermined else Outcome.OUT_OF_SCOPE,
                         evidence={"reason": reason}, notes=notes)

    def retract(self, cid, *, by):
        """Withdraw a claim because of revision claim `by`. Nothing is deleted;
        every claim depending on it becomes effectively RETRACTED too."""
        if by not in self.claims or cid not in self.claims:
            raise LedgerError("unknown claim")
        self.claims[cid].retracted_by = by

    def affected_by(self, cid):
        """All claims that (transitively) depend on cid -- the invalidation set."""
        out, frontier = set(), {cid}
        while frontier:
            nxt = {c.id for c in self.claims.values() if set(c.depends_on) & frontier} - out
            out |= nxt
            frontier = nxt
        return sorted(out)

    # ------------------------------------------------------------ queries
    def effective_warrant(self, cid, _seen=frozenset()) -> Warrant:
        if cid in _seen:
            raise LedgerError(f"dependency cycle through {cid}")
        c = self.claims[cid]
        w = c.warrant
        for d in c.depends_on:
            w = w.join(self.effective_warrant(d, _seen | {cid}))
        return w

    def is_retracted(self, cid, _seen=frozenset()) -> bool:
        c = self.claims[cid]
        return bool(c.retracted_by) or any(self.is_retracted(d, _seen | {cid}) for d in c.depends_on)

    def effective_status(self, cid) -> Status:
        c = self.claims[cid]
        return project(self.effective_warrant(cid), c.outcome, self.is_retracted(cid))

    def by_status(self, status: Status):
        return [c for c in self.claims.values() if self.effective_status(c.id) == status]

    def to_json(self) -> str:
        def enc(c):
            d = asdict(c)
            w = self.effective_warrant(c.id)
            d["warrant"] = {"basis": sorted(m.value for m in c.warrant.basis),
                            "trusted_base": sorted(c.warrant.trusted_base),
                            "conditions": sorted(c.warrant.conditions)}
            d["effective_warrant"] = w.describe()
            d["outcome"] = c.outcome.value
            d["status"] = c.status.label
            d["effective_status"] = self.effective_status(c.id).label
            return d
        return json.dumps([enc(c) for c in self.claims.values()], indent=2, default=str)

    def to_markdown(self) -> str:
        rows = ["| ID | Effective status | Warrant | Category | Statement | Depends on |",
                "|---|---|---|---|---|---|"]
        for c in self.claims.values():
            eff = self.effective_status(c.id)
            st = eff.label + ("" if eff == c.status else f" (own: {c.status.label})")
            rows.append(f"| {c.id} | {st} | {self.effective_warrant(c.id).describe()} | {c.category} "
                        f"| {c.statement} | {', '.join(c.depends_on)} |")
        return "\n".join(rows)
