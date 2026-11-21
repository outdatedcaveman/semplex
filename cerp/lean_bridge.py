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


def _enc_bitmask_lit(lit: int) -> int:
    """Encode signed nonzero DIMACS literal to unsigned `Nat` matching `Cerp.encLit`."""
    il = int(lit)
    if il == 0:
        raise ValueError("DIMACS clause literal cannot be 0")
    return 2 * il if il > 0 else 2 * (-il) + 1


def _build_bitmask_lrat(clauses, lrat_steps):
    """Extract per-step bitmasks, used clause IDs, and unit literal sequences."""
    db = [[_enc_bitmask_lit(l) for l in c] for c in clauses]
    out_steps = []
    for cl, hints in lrat_steps:
        u_cl = [_enc_bitmask_lit(l) for l in cl]
        c_mask = 0
        for u in u_cl:
            c_mask |= 1 << u
        f_mask = c_mask
        cids = []
        us = []
        for cid in hints:
            ic = int(cid)
            if ic < 0 or ic >= len(db):
                raise ValueError(f"LRAT hint cid={ic} out of range [0, {len(db)})")
            rem = [u for u in db[ic] if not ((f_mask >> u) & 1)]
            if not rem:
                cids.append(ic)
                break
            elif len(rem) == 1:
                u = rem[0]
                cids.append(ic)
                us.append(u)
                f_mask |= 1 << (u ^ 1)
            else:
                raise ValueError(f"LRAT hint cid={ic} not unit/conflict under trail (rem={rem})")
        if not cids or len(cids) != len(us) + 1:
            raise ValueError("LRAT step hints did not end in conflict")
        out_steps.append((c_mask, cids, us))
        db.append(u_cl)
        if not cl:
            break
    if not out_steps or out_steps[-1][0] != 0:
        raise ValueError("LRAT derivation did not terminate in empty clause")
    return out_steps


def _make_mtree_chunks(cmasks: list[int], chunk_levels: int):
    """Mirror `Cerp.cnfToMTree`'s bottom-up pairing, splitting top `chunk_levels` into named chunks."""
    nodes = [("leaf", i, cmasks[i]) for i in range(len(cmasks))]
    while len(nodes) > 1:
        nxt = []
        for k in range(0, len(nodes), 2):
            if k + 1 < len(nodes):
                nxt.append(("bin", nodes[k], nodes[k + 1]))
            else:
                nxt.append(nodes[k])
        nodes = nxt
    root = nodes[0]

    subtrees = []

    def _cut(node, depth: int, rpath: str) -> str:
        if depth >= chunk_levels or node[0] == "leaf":
            sid = len(subtrees)
            subtrees.append((sid, node, rpath))
            return f"b{sid}"
        return f"(.b {_cut(node[1], depth + 1, rpath + '.1')} {_cut(node[2], depth + 1, rpath + '.2')})"

    top_expr = _cut(root, 0, "")
    cid_loc: dict[int, tuple[int, str]] = {}
    sub_defs: list[tuple[int, str, str]] = []

    def _render_sub(node, spath: str) -> str:
        if node[0] == "leaf":
            cid_loc[node[1]] = (cur_sid, spath)
            return f"(.l {node[2]})"
        return f"(.b {_render_sub(node[1], spath + '.1')} {_render_sub(node[2], spath + '.2')})"

    for cur_sid, node, rpath in subtrees:
        sub_defs.append((cur_sid, _render_sub(node, ""), rpath))
    return top_expr, sub_defs, cid_loc


def _render_reflected_tnet_body(net, ref_expr, vars_, lrat_steps, name: str) -> str:
    """Render a self-contained reflected bitmask LRAT proof inside standard Lean 4 kernel."""
    from . import sat

    n = len(vars_)
    tns_idx = sat._tnet_to_indexed_nodes(net, vars_)
    _, clauses = sat._lean_tnet_miter_pb(vars_, tns_idx, ref_expr["body"])
    bm_steps = _build_bitmask_lrat(clauses, lrat_steps)
    cmasks = []
    for cl in clauses:
        m = 0
        for l in cl:
            m |= 1 << _enc_bitmask_lit(l)
        cmasks.append(m)

    n_base = len(clauses)
    used_base = sorted({cid for _, cids, _ in bm_steps for cid in cids if cid < n_base})
    chunk_levels = max(1, min(4, len(cmasks).bit_length() - 5))
    top_expr, sub_defs, cid_loc = _make_mtree_chunks(cmasks, chunk_levels)

    max_u = max((u for _, _, us in bm_steps for u in us), default=0)
    ubits = max(10, max_u.bit_length())
    umask = (1 << ubits) - 1

    ns_scope = f"_Refl_{re.sub(r'[^A-Za-z0-9_]', '_', name)}"
    lines = [
        f"def tns : List TNode := {tnet_to_lean(net, vars_)}",
        f"def eSpec : Expr := {expr_to_lean(ref_expr['body'], vars_)}",
        f"namespace {ns_scope}",
    ]
    for sid, expr_s, _ in sub_defs:
        lines.append(f"def b{sid} : MTree := {expr_s}")
    lines.append(f"def baseMT : MTree := {top_expr}")
    lines.append(f"theorem base_eq : cnfToMTree (tseitinTNetMiterPB {n} tns eSpec) = some baseMT := rfl")
    for cid in used_base:
        sid, sp = cid_loc[cid]
        lines.append(f"theorem c{cid} (τ : Nat → Bool) (h : MTreeSat τ b{sid}) : BmSat τ {cmasks[cid]} := h{sp}")

    lines.append("structure HBase (τ : Nat → Bool) : Prop where")
    for sid, _, _ in sub_defs:
        lines.append(f"  h{sid} : MTreeSat τ b{sid}")

    for s_idx, (cm, cids, us) in enumerate(bm_steps):
        cid_new = n_base + s_idx
        upack = 0
        for u in reversed(us):
            upack = (upack << ubits) | u
        chain = "BmList.nil"
        for cid in reversed(cids):
            if cid < n_base:
                sid, _ = cid_loc[cid]
                ref = f"(c{cid} τ hb.h{sid})"
            else:
                ref = f"(c{cid} τ hb)"
            chain = f"BmList.cons {ref} ({chain})"
        lines.append(
            f"theorem c{cid_new} (τ : Nat → Bool) (hb : HBase τ) : BmSat τ {cm} := "
            f"bm_rup_sound {ubits} {umask} {cm} {upack} ({chain}) rfl"
        )
    lines.append(f"end {ns_scope}")

    last_cid = n_base + len(bm_steps) - 1
    hb_fields = ", ".join(f"h{sid} := hmt{rpath}" for sid, _, rpath in sub_defs)
    lines.append("")
    lines.append(f"theorem {name} : ∀ σ, evalTNet {n} tns σ = eval σ eSpec := fun σ =>")
    lines.append(f"  if heq : evalTNet {n} tns σ = eval σ eSpec then heq")
    lines.append(
        f"  else False.elim <| (tseitinTNetMiterPB_sat_of_ne {n} tns eSpec σ (by decide) (by decide) (by decide) heq).elim fun τ hsat =>"
    )
    lines.append(
        f"    have hmt : MTreeSat τ {ns_scope}.baseMT := bm_base_sound τ (tseitinTNetMiterPB {n} tns eSpec) {ns_scope}.baseMT hsat {ns_scope}.base_eq"
    )
    lines.append(f"    have hb : {ns_scope}.HBase τ := {{ {hb_fields} }}")
    lines.append(f"    bm_empty_false ({ns_scope}.c{last_cid} τ hb)")
    return "\n".join(lines) + "\n"


def verify_threshold_net_equiv(net, ref_expr, vars_, lrat_steps=None, name="tnet_equiv", native=False, pb=True, reflected=True):
    """Prove `∀ σ, evalTNet n tns σ = eval σ eSpec` in Lean (exhaustive, reflected bitmask LRAT, or tree LRAT)."""
    n = len(vars_)
    stmt = f"∀ σ, evalTNet {n} tns σ = eval σ eSpec"
    if lrat_steps is not None and pb and reflected and not native:
        try:
            body = _render_reflected_tnet_body(net, ref_expr, vars_, lrat_steps, name)
        except ValueError as exc:
            sha = hashlib.sha256(str(exc).encode()).hexdigest()
            return LeanCheck(False, name, stmt, (), version(), sha, f"error: {exc}", _TOKEN), ""
    else:
        defs = [
            f"def tns : List TNode := {tnet_to_lean(net, vars_)}",
            f"def eSpec : Expr := {expr_to_lean(ref_expr['body'], vars_)}",
        ]
        dec = "native_decide" if native else "decide"
        if lrat_steps is None:
            proof = f"(decideTNetEquivExpr_correct {n} tns eSpec (by decide) (by decide)).mp (by {dec})"
        else:
            fmt_step = lambda c, hs: f"([" + ", ".join(str(l) for l in c) + "], [" + ", ".join(str(h) for h in hs) + "])"
            Ls = "[" + ", ".join(fmt_step(c, hs) for c, hs in lrat_steps) + "]"
            defs.append(f"def Ls : List (Clause × List Nat) := {Ls}")
            thm = "tseitinTNetMiterPB_lrat_unsat_implies_equiv" if pb else "tseitinTNetMiter_lrat_unsat_implies_equiv"
            proof = f"{thm} {n} tns eSpec Ls (by decide) (by decide) (by decide) (by {dec}) (by {dec})"
        body = "\n".join(defs) + f"\n\ntheorem {name} : {stmt} :=\n  {proof}\n"
    ok, ax, log, sha, text = _check(
        body, name, stmt, renders=("eSpec",),
        allowed=NATIVE_AXIOMS if native else ALLOWED_AXIOMS,
    )
    expected = [render_indexed(ref_expr["body"], vars_)]
    printed = [json.loads(line) for line in log.splitlines() if line.startswith("[")]
    ok = ok and printed == expected
    return LeanCheck(ok, name, stmt, ax or (), version(), sha, log, _TOKEN), text
