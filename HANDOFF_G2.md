# Handoff — `gemini/G2` (Gap B1: Lean kernel LRAT for `xor4` via `decide`)

## What was done

1. **Root-cause diagnosis of `xor4` / `xor3` Lean kernel timeout:**
   - Legacy `Cerp.pbToExpr` expanded each $d$-input `TNode` into an $O(2^d)$ decision-tree `Expr`, bloating `xor3` (73 vars / 173 clauses) and `xor4` (176 vars / 431 clauses).
   - Legacy `cerp/sat.py::rup_to_lrat` recorded all propagated literals instead of cone-of-influence (COI) trimmed hints (71–74 hints per step on `xor3`, up to 177 on `xor4`).
   - Legacy `Cerp.checkLrat` stored the clause DB as an `Array` queried/appended inside `by decide`, forcing kernel WHNF $O(N)$ linear scans over `Array.toList` on every hint lookup and clause push.

2. **Lean 4 binary-tree LRAT checker & direct pseudo-Boolean BDD miter (`proofs/lean/Cerp.lean`, `proofs/lean/Audit.lean`):**
   - Added structural-recursion binary tree DB (`BTree`, `bgetAux`, `bsetAux`, `bOfListAux`) and `checkLratT` / `rupCheckT`, proving `checkLratT_unsat` under `[propext, Quot.sound]`. (`WellFounded.fix` recursion is avoided so kernel WHNF reduces `by decide` cleanly.)
   - Added direct layered pseudo-Boolean BDD encoder `pbEncodeSym` (`pbBounds`, `nextLayerTs`, `mkSymIte`, `buildLayer`, `pbEncodeLayer`), `wireEqSym`, `tseitinTNetGoPB`, and `tseitinTNetMiterPB`, avoiding exponential `pbToExpr` expansion.
   - Proved `Cerp.tseitinTNetMiterPB_lrat_unsat_implies_equiv` under `[propext, Classical.choice, Quot.sound]` (0 `sorryAx`, 0 `Lean.ofReduceBool`), and added it to `proofs/lean/Audit.lean`.

3. **Matching Python COI-trimmed LRAT + PB encoder (`cerp/sat.py`, `cerp/lean_bridge.py`, `tests/test_lean.py`):**
   - Updated `cerp/sat.py::rup_to_lrat` with backward cone-of-influence trimming of unit-propagation hints (preserving forward propagation order) and backward pruning of unused intermediate lemmas.
   - Added exact Python twin `_pb_bounds`, `_add_bound`, `_next_layer_ts`, `_mk_sym_ite`, `_lookup_sym`, `_build_layer`, `_pb_encode_layer`, `_pb_encode_sym`, `_wire_eq_sym`, and `_lean_tnet_miter_pb`, and defaulted `prove_tnet_equivalence_lrat(..., pb=True)` and `lean_bridge.verify_threshold_net_equiv(..., pb=True)` to the PB + `BTree` path.
   - Updated `tests/test_lean.py::test_tnet_lean_exhaustive_and_lrat_equiv` to verify `xor4` with `native=False` and `set(r_lrat.axioms) <= set(lean_bridge.ALLOWED_AXIOMS)`.
   - Added proposed claim notes in `claims/PROPOSED.md` (no `Pnnn` IDs assigned; `claims/REGISTER.md`, `claims/GAPS.json`, `THEORY.md` §5, and all `experiments/FROZEN.json` files untouched).

## Exact acceptance check and verbatim output

### End-to-end `xor3` / `xor4` PB vs non-PB benchmark (`native=False`)
```text
=== xor3 ===
old_pbFalse: vars=73 clauses=173 status=unsat steps=8 hints_min_max=(24,28) hints_sum=207
new_pbTrue : vars=22 clauses=57 status=unsat steps=8 hints_min_max=(9,18) hints_sum=115
lean_decide: ok=True wall_s=5.25 axioms=['propext', 'Classical.choice', 'Quot.sound']
=== xor4 ===
old_pbFalse: vars=176 clauses=431 status=unsat steps=16 hints_min_max=(35,40) hints_sum=594
new_pbTrue : vars=42 clauses=120 status=unsat steps=16 hints_min_max=(11,27) hints_sum=317
lean_decide: ok=True wall_s=15.68 axioms=['propext', 'Classical.choice', 'Quot.sound']
```
(`xor3` before this branch was `245.30 s` without PB/COI/BTree; after: `5.25 s`. `xor4` is now `15.68 s` with kernel `by decide`, `native=False`.)

### `tests/test_lean.py`
```text
.........                                                                [100%]
9 passed in 197.67s (0:03:17)
```

### Rule 7 checks on final branch state
- `python -m cerp.register check`:
```text
0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md
LEDGER_DIFF_W_LEN=0
```
- `python -m cerp.status --check`: exited `0` (empty stdout).
- `& "$env:TEMP\semplex_extras_venv\Scripts\python.exe" -m pytest -q -k "not test_search_keeps_a_working_rule_working"`:
```text
........................................................................ [ 47%]
........................................................................ [ 94%]
.........                                                                [100%]
153 passed, 1 deselected in 269.16s (0:04:29)
```
  (Note: `tests/test_localrules.py::test_search_keeps_a_working_rule_working` is the pre-existing `262281e` failure fixed on isolated sibling branch `origin/gemini/G6` commit `4b0f36a`.)
- Lean compilation to `$env:TEMP\semplex_lean_olean` and audit (`Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`): exited `0` with zero `.olean` files in `proofs/lean/` (`LEFTOVER_OLEAN=0`):
```text
'Cerp.tseitinTNetMiterPB_lrat_unsat_implies_equiv' depends on axioms: [propext, Classical.choice, Quot.sound]
```
(All other theorems in `Audit.lean`, `AuditTheory.lean`, and `AuditBounds.lean` printed with `{}` or `<= {propext, Classical.choice, Quot.sound}` and zero `sorryAx` / zero `Lean.ofReduceBool`.)

## What failed / open

- Pre-existing `test_search_keeps_a_working_rule_working` remains excluded here per isolated-branch plan (`gemini/G6` fixes it independently).
- No open issues remain inside Gap B1 (`G2`).
