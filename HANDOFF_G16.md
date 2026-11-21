# G16 Handoff — Pass the Lean 4 Kernel `decide` Wall (`gemini/G16`)

**Branch:** `gemini/G16` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`)
**Target:** Break G10's Lean 4 kernel verification wall (`> 150s` at `>= 61` LRAT steps, `[8]->[4]->1` at `104` steps timing out in `elab_only` alone) WITHOUT `native_decide` (`Lean.ofReduceBool`), keeping strictly standard axioms `{propext, Classical.choice, Quot.sound}`.

## Pre-Registered Hypotheses & Acceptance Criteria (Rule 5 — Committed Prior to Full 15-Target Run)

G10 established two distinct kernel bottlenecks on dense PB Tseitin miters:
1. Front-end elaboration explosion of large `List (Clause × List Nat)` signed-integer literals (`elab_only > 150s` at `104` LRAT steps).
2. Kernel WHNF call-by-name slowdown in random-access binary-tree (`BTree Clause`) clause database lookups and assignment-trail traversals.

**Design (G16):** Replace interpreted clause-DB traversal with a **Reflected Bitmask LRAT Engine** proved in core Lean 4.12 (`proofs/lean/Cerp.lean`, zero Mathlib):
- CNF clauses are reflected once as GMP `Nat` literal bitmasks inside a chunked binary tree `MTree` (`bm_base_sound`), checked against `tseitinTNetMiterPB n tns eSpec` by one `rfl`.
- Each LRAT derivation step is checked as an opaque top-level theorem (`bm_rup_sound`) running GMP `Nat.lor` / `Nat.shiftLeft` / `Nat.land` propagation (`bmStepOk`) over packed unit hints (`BmList`), ending in conflict (`bm_empty_false`).

**Numeric Pre-Registered Criteria (`experiments/g16_kernel_wall_bench.py` -> `experiments/results/g16_kernel_wall.json`):**
- **`H16.1` (Primary G16 gate):** `[8]->[4]->1` (`n8_1hidden_w4_rot_or`, `104` LRAT steps) verifies in `< 120.0s` (`native=False`, axioms subset of `{propext, Classical.choice, Quot.sound}`).
- **`H16.2` (Timeout elimination):** All `5` G10 timeout targets (`n8_1hidden_w3_or`, `n8_1hidden_w4_rot_or`, `n8_1hidden_w8_par8`, `n8_1hidden_w2_nonsup_17`, `n8_1hidden_w2_nonsup_5`) verify in `< 120.0s` (`native=False`, standard axioms only).
- **`H16.3` (Full suite sweep):** All `15 / 15` G10 benchmark configurations verify in `< 120.0s` (vs G10 `10 / 15`).
- **`H16.4` (249-step scaling):** `[8]->[8]->1` (`n8_1hidden_w8_par8`, `249` LRAT steps / `7,955` hints) verifies in `< 120.0s`.

*(Status: Benchmark executed AND full Rule 7 verified.)*

## Measured Results (`experiments/results/g16_kernel_wall.json`)

- **Pre-compiled `Cerp.olean` timing:** `0.012s` (already warm from prior build; standalone clean rebuild verified separately in Rule 7)
- **Completion:** `15 / 15` benchmarks finished with `lean_status == "ok"` and `under_120s == True` (`all_standard_axioms == True`, strictly `["propext", "Classical.choice", "Quot.sound"]`, zero `sorryAx`, zero `Lean.ofReduceBool`).

### Acceptance Verdicts

| Criterion | Outcome | Exact Witness |
| :--- | :---: | :--- |
| `H16.1_w4_rot_or_under_120s` | **`True`** | `n8_1hidden_w4_rot_or`: **`48.558s`** (`104` steps, `3,451` hints) vs G10 `timeout_150s` (`elab_only > 150s`) |
| `H16.2_all_5_g10_timeouts_under_120s` | **`True`** | All 5 G10 timeouts pass in `33.341s–63.080s` (`w3_or`, `w4_rot_or`, `w8_par8`, `nonsup_17`, `nonsup_5`) |
| `H16.3_all_15_under_120s_std_axioms` | **`True`** | `15 / 15` `< 120s`, axioms `['propext', 'Classical.choice', 'Quot.sound']` |
| `H16.4_w8_par8_249_steps_under_120s` | **`True`** | `n8_1hidden_w8_par8`: **`63.080s`** (`249` steps, `7,955` hints) vs G10 `timeout_150s` |

### Full 15-Target Comparison (`G10` Interpreted `BTree` vs `G16` Reflected Bitmask, `native=False`, `pb=True`)

| Benchmark | Shape | Clauses | LRAT Steps | Hints | G10 Lean (`s`) | G16 Lean (`s`) | Speedup | Stage Breakdown (`base_eq_rfl` / `full_verify`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `baseline_xor4` | `[4]->[4]->1` | 120 | 16 | 317 | 16.461 | 8.968 | 1.8x | 3.559s / 7.770s |
| `n6_1hidden_w2_eq3` | `[6]->[2]->1` | 140 | 19 | 435 | 18.848 | 11.613 | 1.6x | — |
| `n6_2hidden_w2_cmp_xor` | `[6]->[2]->[2]->1` | 238 | 30 | 966 | 53.725 | 13.737 | 3.9x | 5.171s / 14.281s |
| `n6_3hidden_w2_d4` | `[6]->[2]->[2]->[2]->1` | 248 | 31 | 1049 | 63.004 | 14.215 | 4.4x | — |
| `n6_4hidden_w2_d5` | `[6]->[2]->[2]->[2]->[2]->1` | 252 | 31 | 1058 | 56.276 | 18.159 | 3.1x | — |
| `n6_2hidden_w4_rot_xor` | `[6]->[4]->[2]->1` | 324 | 47 | 1412 | 104.442 | 21.362 | 4.9x | — |
| `n8_1hidden_w2_eq4` | `[8]->[2]->1` | 297 | 41 | 1160 | 75.414 | 18.238 | 4.1x | 6.897s / 20.092s |
| `n8_factored_parity` | `balanced(13)` | 256 | 53 | 1088 | 97.087 | 17.014 | 5.7x | — |
| `n8_1hidden_w3_or` | `[8]->[3]->1` | 515 | 67 | 2217 | `timeout_150s` | **35.328** | >4.2x | — |
| `n8_1hidden_w4_rot_or` | `[8]->[4]->1` | 673 | 104 | 3451 | `timeout_150s` | **48.558** | >3.1x | 16.394s / 46.087s |
| `n8_1hidden_w8_par8` | `[8]->[8]->1` | 512 | 249 | 7955 | `timeout_150s` | **63.080** | >2.4x | 10.954s / 63.108s |
| `n8_1hidden_w2_scale2` | `[8]->[2]->1` | 297 | 41 | 1160 | 73.308 | 22.770 | 3.2x | — |
| `n8_1hidden_w2_super53` | `[8]->[2]->1` | 297 | 41 | 1160 | 80.313 | 22.053 | 3.6x | — |
| `n8_1hidden_w2_nonsup_17` | `[8]->[2]->1` | 469 | 64 | 1768 | `timeout_150s` | **35.712** | >4.2x | — |
| `n8_1hidden_w2_nonsup_5` | `[8]->[2]->1` | 517 | 61 | 2335 | `timeout_150s` | **33.341** | >4.5x | — |

## What This Does NOT Show

- **Linear file size growth in emitted proof certificates:** Every LRAT derivation step emits one opaque top-level theorem (`bm_rup_sound`) referencing pre-resolved literal bitmasks rather than running dynamic trail-lookup inside kernel WHNF, so generated `.lean` certificate body text scales linearly with `lrat_hints` (`291,174` bytes / `775` lines at `104` steps / `3,451` hints for `n8_1hidden_w4_rot_or`; `432,745` bytes / `774` lines at `249` steps / `7,955` hints for `n8_1hidden_w8_par8`). Still checked end-to-end by Lean 4 kernel without `Lean.ofReduceBool` or custom axioms.
- **Unrestricted `n >= 16` scaling or arbitrary SAT solvers:** Tested up to `n = 8`, `673` clauses, `249` LRAT steps, and `7,955` hints. Beyond ~`10^4`–`10^5` LRAT hints, generating and elaborating one Lean theorem per step will eventually hit front-end file size / memory limits unless packed into byte-stream / reflected binary arrays or batched lemmas.
- **Standalone Python PB/SAT soundness:** Python computes the Tseitin CNF & LRAT hint stream untrusted; kernel trust depends ONLY on `Cerp.tseitinTNetMiterPB_sat_of_ne`, `Cerp.bm_base_sound`, `Cerp.bm_rup_sound`, and `Cerp.bm_empty_false` checked against `tseitinTNetMiterPB n tns eSpec`.

## Rule 7 Verification (Observed Outputs)

- `python -m cerp.register check`: `exit=0` (`0 problem(s), 46 status note(s)`).
- `python -m cerp.status --check`: `exit=0`.
- `SEMPLEX_LEAN_TIMEOUT=900 pytest -q`: **`168 passed in 1058.46s (0:17:38)`** (`exit=0`).
- Standalone Lean `v4.12.0` (`proofs/lean/` -> `%TEMP%\semplex_trash_oleans\g16_rule7`):
  - `Cerp.lean` (`51.97s`), `Theory.lean` (`24.45s`), `Bounds.lean` (`540s`), `Inference.lean` (`1.41s`), `Closure.lean` (`1.19s`) -> all `exit=0`.
  - `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`, `AuditInference.lean`, `AuditClosure.lean` -> all `exit=0`; strictly `[]`, `[propext]`, `[propext, Quot.sound]`, or `[propext, Classical.choice, Quot.sound]` (zero `sorryAx`, zero `Lean.ofReduceBool`).
  - `leftover_oleans=0` inside `proofs/lean/`.
