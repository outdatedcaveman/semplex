# Handoff — Task G5 (Gap B3: Lean 4 Proof & Kernel Verifier for `parity4` >= 5 Neurons)

- **Branch:** `gemini/G5` (cut from `claude/practical-shannon-oqg60y` at `262281e`)

## What Was Built

1. **Lean 4.12.0 Formalization ([`proofs/lean/Bounds.lean`](proofs/lean/Bounds.lean), [`proofs/lean/AuditBounds.lean`](proofs/lean/AuditBounds.lean)):**
   - Added `CerpBounds.parity4_not_three_ltf_determined` and `CerpBounds.parity4_not_four_neurons` in `proofs/lean/Bounds.lean`.
   - Regularizes arbitrary integer-weighted 4-input LTFs into non-negative non-decreasing weights via elementary $B_4$ operations (`regularize_ltf`, `monotone_isRegular`), classifies all regular canonical functions (`regExhaust`, `t_reg_exhaust`) into constant `0` and 14 $B_4$-closed orbits totaling 940 canonical non-constant LTFs, reduces pairs modulo orbit symmetry and stabilizers (`stabTrie_*`, `witTrie_*_*`), and refutes every pair with single- or multi-bucket coordinate-sum Farkas certificates (`checkPairCertB`, `checkPairCertB_sound`).
   - Added `#print axioms parity4_not_three_ltf_determined` and `#print axioms parity4_not_four_neurons` to `proofs/lean/AuditBounds.lean`.

2. **Trusted Python Kernel Extension & Untrusted Certificate Generator:**
   - [`cerp/kernel_bounds.py`](cerp/kernel_bounds.py): added `check_parity4_needs_5_neurons(cert) -> Verdict` (keeping imports strictly `from .kernel import KERNEL_VERSION, KernelError, Verdict, _TOKEN`), checking monotone weight witnesses for all 15 representatives, `neg0`/`sw01`/`sw12`/`sw23` closure, exhaustive $2^{16}$ regular-poset coverage matching `isRegularB16` (`_REG_EDGES16`), stabilizer fixation, and single/multi-bucket Farkas witnesses.
   - [`cerp/bounds.py`](cerp/bounds.py): added `parity4_five_neuron_cert()`.

3. **Tests & Proposed Claims:**
   - [`tests/test_atlas_bounds.py`](tests/test_atlas_bounds.py): `test_parity4_needs_5_neurons_certificate_and_forgeries` (positive verdict + negative mutation tests on target, monotonicity, threshold, orbit completeness, const-const, const-rep, pair cert, witness cover).
   - [`tests/test_bounds_differential.py`](tests/test_bounds_differential.py): `test_parity4_five_neuron_matches_atlas_and_lean` (exact agreement with `atlas.ltfs(4)` 940 canonical non-constant LTFs and 14 orbit sizes, plus `_lean_not_threshold_pred` checks).
   - [`claims/PROPOSED.md`](claims/PROPOSED.md): proposed claim entry.

## Verification Results (Rule 7 — Run Sequentially)

1. `python -m cerp.register check` & `git diff -w claims/LEDGER_CHECK.md` & `python -m cerp.status --check`:
   - `0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md`
   - `git diff -w claims/LEDGER_CHECK.md` empty (cleaned with `git checkout -- claims/LEDGER_CHECK.md`)
   - `REG_RC=0 STATUS_RC=0`
2. `pytest -q -k "not test_search_keeps_a_working_rule_working" --tb=short`:
   - `155 passed, 1 deselected in 1135.83s (0:18:55)` (exit code 0).
   - Excluded pre-existing `262281e` failure `tests/test_localrules.py::test_search_keeps_a_working_rule_working` (already fixed on `gemini/G6`, per Rule 7 baseline instruction).
3. Lean 4.12.0 compilation into `$env:TEMP\semplex_lean_olean` and audits (zero `.olean` left in `proofs/lean/`):
   - `lean -o Cerp.olean Cerp.lean` -> exit 0
   - `lean -o Theory.olean Theory.lean` -> exit 0
   - `lean -o Bounds.olean Bounds.lean` -> exit 0
   - `lean Audit.lean` -> exit 0 (`[propext, Quot.sound]` / `[propext, Classical.choice, Quot.sound]`)
   - `lean AuditTheory.lean` -> exit 0 (`[propext, Classical.choice, Quot.sound]` subset)
   - `lean AuditBounds.lean` -> exit 0:
     - `'CerpBounds.parity4_not_three_ltf_determined' depends on axioms: [propext, Classical.choice, Quot.sound]`
     - `'CerpBounds.parity4_not_four_neurons' depends on axioms: [propext, Classical.choice, Quot.sound]`
   - `LEAN_ALL_OK DT=788.78s leftover_olean=0` (zero `sorryAx`, zero `Lean.ofReduceBool`).
