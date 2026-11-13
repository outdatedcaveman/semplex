"""Bridge to the Lean 4 proofs in proofs/lean/Cerp.lean (Spike 06).

Turns concrete claims into Lean theorems, checked by the Lean kernel using
deciders that are PROVED correct in Cerp.lean:

  equivalence / task-equivalence of two F0 expressions
      theorem : ∀ σ, eval σ e₁ = eval σ e₂          (via decideEquiv_correct)
  unsatisfiability of a CNF (e.g. a circuit miter) from a RUP certificate
      theorem : ∀ σ, cnfSat σ F = false              (via unsat_of_certificate)

Acceptance requires ALL of:
  * lean exits 0 with no errors;
  * `#print axioms` lists only {propext, Quot.sound, Classical.choice}
    -- in particular no sorryAx and no Lean.ofReduceBool (native_decide);
  * round trip: Lean renders the expressions it checked, and they must equal
    the bridge's own rendering of the source artifacts (translation faithfulness).

Remaining trust, recorded in each warrant: the Lean 4 kernel; for the CNF
route, the Python Tseitin encoder (cerp.kernel.miter_cnf) is NOT verified,
so "unsat CNF" -> "equivalent circuits" is a bridge assumption.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass

LEAN_DIR = pathlib.Path(__file__).resolve().parent.parent / "proofs" / "lean"
ALLOWED_AXIOMS = {"propext", "Quot.sound", "Classical.choice"}
# native mode: the PROVED checker runs as compiled code; the Lean compiler and
# runtime join the trusted base (axiom Lean.ofReduceBool). Recorded separately.
NATIVE_AXIOMS = ALLOWED_AXIOMS | {"Lean.ofReduceBool"}
_TOKEN = object()


class LeanUnavailable(Exception):
    pass


@dataclass(frozen=True)
class LeanCheck:
    ok: bool
    theorem: str
    statement: str
    axioms: tuple
    lean_version: str
    source_sha256: str
    log: str
    _token: object = None

    def __post_init__(self):
        if self._token is not _TOKEN:
            raise ValueError("LeanCheck can only be produced by cerp.lean_bridge")

    @property
    def authentic(self):
        return self._token is _TOKEN


def lean_binary():
    b = os.environ.get("CERP_LEAN") or shutil.which("lean")
    if not b or not pathlib.Path(b).exists():
        raise LeanUnavailable("set CERP_LEAN to a Lean 4 binary (tested with 4.12.0)")
    return b


def _run(args, cwd, env=None, timeout=900):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                       env={**os.environ, **(env or {})})
    return p.returncode, p.stdout + p.stderr


def _library(build_dir: pathlib.Path):
    """Compile Cerp.lean to an .olean once per source hash."""
    src = (LEAN_DIR / "Cerp.lean").read_text()
    h = hashlib.sha256(src.encode()).hexdigest()[:16]
    out = build_dir / h
    olean = out / "Cerp.olean"
    if not olean.exists():
        out.mkdir(parents=True, exist_ok=True)
        code, log = _run([lean_binary(), f"--root={LEAN_DIR}", "-o", str(olean),
                          str(LEAN_DIR / "Cerp.lean")], cwd=LEAN_DIR)
        if code != 0:
            raise RuntimeError("Cerp.lean failed to compile:\n" + log)
    return out


def version():
    return _run([lean_binary(), "--version"], cwd=".")[1].strip()


# ------------------------------------------------------------ translation

def expr_to_lean(e, vars_):
    op = e[0]
    if op == "const":
        return f"(Expr.const {'true' if e[1] else 'false'})"
    if op == "var":
        return f"(Expr.var {vars_.index(e[1])})"
    return f"(Expr.{op} " + " ".join(expr_to_lean(x, vars_) for x in e[1:]) + ")"


def render_indexed(e, vars_):
    """The rendering Lean's Expr.render must reproduce (indices instead of names)."""
    op = e[0]
    if op == "const":
        return ["const", 1 if e[1] else 0]
    if op == "var":
        return ["var", vars_.index(e[1])]
    return [op] + [render_indexed(x, vars_) for x in e[1:]]


def _axioms(log, theorem):
    m = re.search(rf"'{re.escape(theorem)}' depends on axioms: \[([^\]]*)\]", log)
    if m:
        return tuple(a.strip() for a in m.group(1).split(",") if a.strip())
    if f"'{theorem}' does not depend on any axioms" in log:
        return ()
    return None


def _check(body, theorem, statement, renders=(), build_dir=None, allowed=ALLOWED_AXIOMS):
    build = pathlib.Path(build_dir or tempfile.gettempdir()) / "cerp_lean_build"
    lib = _library(build)
    text = "import Cerp\nopen Cerp\nset_option maxRecDepth 200000\nset_option maxHeartbeats 0\n\n" + body + f"\n#print axioms {theorem}\n"
    for name in renders:
        text += f"#eval IO.println ({name}.render)\n"
    sha = hashlib.sha256(text.encode()).hexdigest()
    tc_file = LEAN_DIR / "lean-toolchain"
    env = {"LEAN_PATH": str(lib)}
    if tc_file.exists() and "ELAN_TOOLCHAIN" not in os.environ:
        env["ELAN_TOOLCHAIN"] = tc_file.read_text().strip()
    with tempfile.TemporaryDirectory() as d:
        f = pathlib.Path(d) / "Claim.lean"
        f.write_text(text)
        code, log = _run([lean_binary(), str(f)], cwd=d, env=env)
    ax = _axioms(log, theorem)
    ok = (code == 0 and "error" not in log.lower() and ax is not None and set(ax) <= allowed
          and "sorryAx" not in ax)
    return ok, ax, log, sha, text


def prove_expr_claim(left, right, vars_, care=None, name="claim"):
    """Prove ∀σ, eval σ L = eval σ R (or the task version under `care`) in Lean."""
    n = len(vars_)
    defs = [f"def eL : Expr := {expr_to_lean(left['body'], vars_)}",
            f"def eR : Expr := {expr_to_lean(right['body'], vars_)}"]
    if care is None:
        stmt = "∀ σ, eval σ eL = eval σ eR"
        proof = f"(decideEquiv_correct {n} eL eR (by decide) (by decide)).mp (by decide)"
        renders = ("eL", "eR")
    else:
        defs.append(f"def eC : Expr := {expr_to_lean(care['body'], vars_)}")
        stmt = "∀ σ, eval σ eC = true → eval σ eL = eval σ eR"
        proof = f"(decideTask_correct {n} eC eL eR (by decide) (by decide) (by decide)).mp (by decide)"
        renders = ("eL", "eR", "eC")
    thm = f"{name}"
    body = "\n".join(defs) + f"\n\ntheorem {thm} : {stmt} :=\n  {proof}\n"
    ok, ax, log, sha, text = _check(body, thm, stmt, renders)
    # round-trip faithfulness: the terms Lean checked are the artifacts we meant
    expected = [render_indexed(a["body"], vars_) for a in (left, right) + ((care,) if care else ())]
    printed = [json.loads(line) for line in log.splitlines() if line.startswith("[")]
    ok = ok and printed == expected
    return LeanCheck(ok, thm, stmt, ax or (), version(), sha, log, _TOKEN), text


def prove_cnf_unsat(clauses, lemmas, name="miter_unsat", native=False):
    """Prove ∀σ, cnfSat σ F = false in Lean from a RUP certificate.
    native=True evaluates the proved checker as compiled code (compiler trusted)."""
    F = "[" + ", ".join("[" + ", ".join(str(l) for l in c) + "]" for c in clauses) + "]"
    Ls = "[" + ", ".join("[" + ", ".join(str(l) for l in c) + "]" for c in lemmas) + "]"
    stmt = "∀ σ, cnfSat σ F = false"
    body = (f"def F : CNF := {F}\ndef Ls : List Clause := {Ls}\n\n"
            f"theorem {name} : {stmt} :=\n  unsat_of_certificate F Ls (by decide) "
            f"(by {'native_decide' if native else 'decide'})\n")
    ok, ax, log, sha, text = _check(body, name, stmt, allowed=NATIVE_AXIOMS if native else ALLOWED_AXIOMS)
    return LeanCheck(ok, name, stmt, ax or (), version(), sha, log, _TOKEN), text


def verify_expr_equiv_tseitin(left, right, vars_, lemmas, name="tseitin_equiv", native=False):
    """Prove ∀σ, eval σ L = eval σ R in Lean via Tseitin miter + RUP certificate."""
    n = len(vars_)
    Ls = "[" + ", ".join("[" + ", ".join(str(l) for l in c) + "]" for c in lemmas) + "]"
    defs = [
        f"def eL : Expr := {expr_to_lean(left['body'], vars_)}",
        f"def eR : Expr := {expr_to_lean(right['body'], vars_)}",
        f"def Ls : List Clause := {Ls}",
    ]
    stmt = "∀ σ, eval σ eL = eval σ eR"
    dec = "native_decide" if native else "decide"
    proof = f"tseitinMiter_unsat_implies_equiv {n} eL eR Ls (by decide) (by decide) (by {dec}) (by {dec})"
    body = "\n".join(defs) + f"\n\ntheorem {name} : {stmt} :=\n  {proof}\n"
    ok, ax, log, sha, text = _check(
        body, name, stmt, renders=("eL", "eR"),
        allowed=NATIVE_AXIOMS if native else ALLOWED_AXIOMS,
    )
    expected = [render_indexed(a["body"], vars_) for a in (left, right)]
    printed = [json.loads(line) for line in log.splitlines() if line.startswith("[")]
    ok = ok and printed == expected
    return LeanCheck(ok, name, stmt, ax or (), version(), sha, log, _TOKEN), text


def verify_expr_equiv_lrat(left, right, vars_, lrat_steps, name="lrat_equiv", native=False):
    """Prove ∀σ, eval σ L = eval σ R in Lean via linear-time hint-indexed LRAT checker."""
    n = len(vars_)
    fmt_step = lambda c, hs: f"([" + ", ".join(str(l) for l in c) + "], [" + ", ".join(str(h) for h in hs) + "])"
    Ls = "[" + ", ".join(fmt_step(c, hs) for c, hs in lrat_steps) + "]"
    defs = [
        f"def eL : Expr := {expr_to_lean(left['body'], vars_)}",
        f"def eR : Expr := {expr_to_lean(right['body'], vars_)}",
        f"def Ls : List (Clause × List Nat) := {Ls}",
    ]
    stmt = "∀ σ, eval σ eL = eval σ eR"
    dec = "native_decide" if native else "decide"
    proof = f"tseitinMiter_lrat_unsat_implies_equiv {n} eL eR Ls (by decide) (by decide) (by {dec}) (by {dec})"
    body = "\n".join(defs) + f"\n\ntheorem {name} : {stmt} :=\n  {proof}\n"
    ok, ax, log, sha, text = _check(
        body, name, stmt, renders=("eL", "eR"),
        allowed=NATIVE_AXIOMS if native else ALLOWED_AXIOMS,
    )
    expected = [render_indexed(a["body"], vars_) for a in (left, right)]
    printed = [json.loads(line) for line in log.splitlines() if line.startswith("[")]
    ok = ok and printed == expected
    return LeanCheck(ok, name, stmt, ax or (), version(), sha, log, _TOKEN), text


def tnet_to_lean(net, vars_):
    """Render a normalized ThresholdNet dict as a Lean `List TNode` term."""
    from .sat import _tnet_to_indexed_nodes

    tns = _tnet_to_indexed_nodes(net, vars_)
    fmt_int = lambda x: f"({int(x)})" if int(x) < 0 else str(int(x))
    items = []
    for nd in tns:
        ins_s = "[" + ", ".join(str(int(i)) for i in nd["ins"]) + "]"
        ws_s = "[" + ", ".join(fmt_int(w) for w in nd["ws"]) + "]"
        items.append(f"{{ ins := {ins_s}, ws := {ws_s}, t := {fmt_int(nd['t'])} }}")
    return "[" + ", ".join(items) + "]"


def verify_threshold_net_equiv(net, ref_expr, vars_, lrat_steps=None, name="tnet_equiv", native=False):
    """Prove `∀ σ, evalTNet n tns σ = eval σ eSpec` in Lean (exhaustive or LRAT)."""
    n = len(vars_)
    defs = [
        f"def tns : List TNode := {tnet_to_lean(net, vars_)}",
        f"def eSpec : Expr := {expr_to_lean(ref_expr['body'], vars_)}",
    ]
    stmt = f"∀ σ, evalTNet {n} tns σ = eval σ eSpec"
    dec = "native_decide" if native else "decide"
    if lrat_steps is None:
        proof = f"(decideTNetEquivExpr_correct {n} tns eSpec (by decide) (by decide)).mp (by {dec})"
    else:
        fmt_step = lambda c, hs: f"([" + ", ".join(str(l) for l in c) + "], [" + ", ".join(str(h) for h in hs) + "])"
        Ls = "[" + ", ".join(fmt_step(c, hs) for c, hs in lrat_steps) + "]"
        defs.append(f"def Ls : List (Clause × List Nat) := {Ls}")
        proof = f"tseitinTNetMiter_lrat_unsat_implies_equiv {n} tns eSpec Ls (by decide) (by decide) (by decide) (by {dec}) (by {dec})"
    body = "\n".join(defs) + f"\n\ntheorem {name} : {stmt} :=\n  {proof}\n"
    ok, ax, log, sha, text = _check(
        body, name, stmt, renders=("eSpec",),
        allowed=NATIVE_AXIOMS if native else ALLOWED_AXIOMS,
    )
    expected = [render_indexed(ref_expr["body"], vars_)]
    printed = [json.loads(line) for line in log.splitlines() if line.startswith("[")]
    ok = ok and printed == expected
    return LeanCheck(ok, name, stmt, ax or (), version(), sha, log, _TOKEN), text
