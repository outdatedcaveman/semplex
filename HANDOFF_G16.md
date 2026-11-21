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

*(Status: Pre-registered; full benchmark pending execution.)*
