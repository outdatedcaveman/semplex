# Handoff G4: No-transfer lemma in Lean (Gap C2)

**Branch:** `gemini/G4` (cut cleanly from `origin/claude/practical-shannon-oqg60y` at `262281e`)  
**Gap targeted:** `C2` (`P077`, `experiments/SPIKE_16_REPORT.md` F2)

## What was done

Added `section NoTransfer` (§20) to [`proofs/lean/Theory.lean`](proofs/lean/Theory.lean) and corresponding `#print axioms` checks to [`proofs/lean/AuditTheory.lean`](proofs/lean/AuditTheory.lean). All proofs use Lean 4.12 core only (no Mathlib, zero `sorry`, zero `ofReduceBool`).

### Hypothesis-to-paper mapping (`experiments/SPIKE_16_REPORT.md` F2 / `P077`)

| Paper hypothesis / claim (`SPIKE_16_REPORT.md` F2) | Lean identifier in `Theory.lean` (§20 `NoTransfer`) | Axioms |
|---|---|---|
| Exact group `G` acting reversibly on input space `X` | `FiniteGroupAction Gp X` (`elems`, `act`, `inv`, `inv_mem`, `act_left_inv`, `act_right_inv`) | — |
| `G` maps labelled set `L` to itself / preserves `(L, y|_L)` | `StabilizesSet ga L`, `StabilizesLabelled ga L yL`, `stabilizesLabelled_to_set` | `[]` |
| "every G-orbit lies entirely inside the labelled set or entirely outside it" | `no_transfer_orbit_preserves_labelled`, `no_transfer_orbit_preserves_unlabelled` | `[]` |
| "G-invariance relates unlabelled inputs only to other unlabelled inputs and carries no label information to them" | `no_transfer_sym_list_independent_of_labelled`, `no_transfer_sym_predictor_independent_of_labelled` (any `agg` over `G`-orbits on `x ∉ L` depends strictly on `f|_{¬L}`) | `[]` |
| Flipping unlabelled labels preserves `(L, y|_L)` and its exact stabilizer `G` | `flipUnlabelled`, `flipUnlabelled_preserves_labelled`, `flipUnlabelled_preserves_stabilizer` | `[propext]` |
| Deterministic symmetrization (e.g. logit averaging / majority vote) cannot change expected unlabelled accuracy under any unlabelled-flip-invariant completion distribution | `no_transfer_flip_pair_constant`, `no_transfer_flip_invariant_dist_eq` | `[propext, Quot.sound]` |
| Random-`G` (Reynolds) symmetrization cannot change expected unlabelled accuracy on any `G`-invariant target over a `G`-closed unlabelled set `U` | `no_transfer_reynolds_fixed_invariant_target` | `[propext, Quot.sound]` |
| Random-`G` (Reynolds) symmetrization cannot change expected unlabelled accuracy under any `G`-invariant finite prior over targets | `no_transfer_reynolds_invariant_prior` (via self-contained `sumNat_map_bijection`) | `[propext, Quot.sound]` |
| Honest scope boundary (Rule 4): without label-flip invariance, deterministic majority vote *can* strictly change expected accuracy if the target prior is `G`-invariant yet skewed (e.g. 4:1 toward constant-true on `Fin 3`) | `sym_majority_can_improve_without_flip_symmetry` (`accRaw = 9 < 12 = accSym`) | `[]` |

## Exact acceptance check and verbatim output

1. Lean 4.12 compilation & axiom audit (`lean --root=. -o ... Cerp.lean/Theory.lean/Bounds.lean` + `lean Audit.lean && lean AuditTheory.lean && lean AuditBounds.lean`): exited `0`. Verbatim §20 lines from `AuditTheory.lean`:
```text
'PFT.sumNat_map_bijection' depends on axioms: [propext, Quot.sound]
'PFT.stabilizesLabelled_to_set' does not depend on any axioms
'PFT.no_transfer_orbit_preserves_labelled' does not depend on any axioms
'PFT.no_transfer_orbit_preserves_unlabelled' does not depend on any axioms
'PFT.no_transfer_sym_list_independent_of_labelled' does not depend on any axioms
'PFT.no_transfer_sym_predictor_independent_of_labelled' does not depend on any axioms
'PFT.flipUnlabelled_preserves_labelled' depends on axioms: [propext]
'PFT.flipUnlabelled_preserves_stabilizer' depends on axioms: [propext]
'PFT.no_transfer_flip_pair_constant' depends on axioms: [propext, Quot.sound]
'PFT.no_transfer_flip_invariant_dist_eq' depends on axioms: [propext, Quot.sound]
'PFT.no_transfer_reynolds_fixed_invariant_target' depends on axioms: [propext, Quot.sound]
'PFT.no_transfer_reynolds_invariant_prior' depends on axioms: [propext, Quot.sound]
'PFT.sym_majority_can_improve_without_flip_symmetry' does not depend on any axioms
```

2. `python -m cerp.register check`: exited `0` (`0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md`). `git diff -w claims/LEDGER_CHECK.md` empty; restored via `git checkout -- claims/LEDGER_CHECK.md`.

3. `python -m cerp.status --check`: exited `0`.

4. Full `& "$env:TEMP\semplex_extras_venv\Scripts\python.exe" -m pytest -q`:
```text
........................................................................ [ 46%]
.................F...................................................... [ 93%]
..........                                                               [100%]
FAILED tests/test_localrules.py::test_search_keeps_a_working_rule_working - assert 0.875 >= 0.9
1 failed, 153 passed in 518.17s (0:08:38)
```

## What failed / open

- The 1 failure (`tests/test_localrules.py::test_search_keeps_a_working_rule_working`, `0.875 < 0.9`) is the pre-existing Monte-Carlo seed-1 bug on base commit `262281e`, already isolated and fixed on branch `origin/gemini/G6` (`4b0f36a`). Keeping `gemini/G4` cleanly isolated ("one task per branch"), all 153 other tests (including `tests/test_lean.py`) passed with 0 skips.
- Continuous Gaussian/Lebesgue measure-theoretic versions are not mechanized (finite weighted lists only; continuous measure theory requires Mathlib).
