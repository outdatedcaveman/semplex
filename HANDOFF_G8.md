# Handoff: G8 (Gap B2 — Certified Minimal Cost-4 at n = 8)

**Branch:** `gemini/G8` (cut from `origin/claude/practical-shannon-oqg60y` at `cb37616`, pre-registered at `0ce31fa`)

## Headline Outcome (Care-Set Collapse & Solver-UNSAT Breakdown)

- **Targets tested (`n = 8`, `192 / 256` care set, `seed = 8820` / `8821`, `W = 4`, `time_limit = 60.0s`, `workers = 4`):** `100 / 100` verified (`100%`) by `cerp.kernel.evaluate`, max time `14.1109s` (`median = 1.6616s`, `mean = 2.7312s`, `wall = 274.257s`).
- **Full-`W<=4`-cost-4 targets that collapsed on the `75%` care set:**
  - Collapsed to `cost = 3` within `|w| <= 4`: **`6 / 100` (`6.0%`; `5` certified minimal via `not_threshold_cert_partial`, `1` [`idx=56`] uncertified because it admits a `cost = 1` linear separator on the care set at `|w| <= 16`)**.
  - Collapsed to `cost = 3` at higher weights `5 <= |w| <= 16` (`|w| <= 4` width-2 UNSAT, but width-2 SAT on care at `|w| <= 16`): **`13 / 100` (`13.0%`; `11` at `|w| <= 8`, `2` more at `|w| <= 16`)**. Notably, `11` of those `13` (`9` at `|w| <= 8`, `2` more at `|w| <= 16`) already had a width-2 circuit on the **full 256-row table** once `|w| > 4` is permitted (they were only `W = 4` width-2 UNSAT on the full table, per the generator spec); only `2` (`idx = 73, 91`) were full-table `W = 16` width-2 UNSAT and genuinely collapsed on the `75%` care set at `|w| <= 16`.
  - Total targets whose care-set restriction collapses below unconstrained `cost = 4`: **`19 / 100` (`6` at `|w| <= 4` + `13` at `5 <= |w| <= 16`)**, leaving **`81 / 100`** genuinely unconstrained `cost = 4` partial functions.
- **Fraction where solver proves `W = 4` width-2 `"unsat"` without a checkable `not-two-halfspaces` certificate (`cost3_solver_unsat`):**
  - **`13 / 100` (`13.0%` of all targets; `13 / 94 = 13.83%` of `W = 4` cost-4 targets)**.
  - **Root cause:** For **13 / 13 (100%)** of these cases, no weight-independent `not-two-halfspaces` certificate mathematically *can* exist because a 2-hidden-unit (`cost = 3`) net fits the care set at `|w| <= 16`. Among the `81` targets that truly lack any width-2 representation, `bounds.not_two_halfspaces_cert_partial` + `kernel_bounds.check_not_two_halfspaces_partial` certified **`81 / 81` (`100.0%`)** within `60s`.
- **Pre-registered `>= 90%` (`compile_partial(..., W=4)`) threshold assessment:**
  - Literal fixed-`W=4` non-collapsing cohort: **`81 / 94` (`86.17%`)** compiled to verified cost-4 with kernel-checked `not-two-halfspaces` minimality certificates (`BROKEN` relative to `>= 90%` on `W=4`-only non-collapsing cohort, by 4 targets — **not** because of certificate search failure, but because all `13` remaining targets have `W in 5..16` width-2 solutions on the care set).
  - Unbounded-weight non-collapsing cohort (targets not admitting width-2 at `|w| <= 16` on care): **`81 / 81` (`100.0%`)** compiled and kernel-certified at `cost = 4` within `14.11s` max.

## Summary of Changes

1. **`cerp/netsolve.py`**
   - Added canonical 3-input threshold P-class gate table `_THREE_HALFSPACE_GATES` (`or_and`, `and_or`, `maj3`, `and3`, `or3`), `_solve_three_halfspaces_gate(...)`, and `_solve_three_halfspaces(...)` (two-round budget schedule across canonical gates with lossless symmetry breaking and `W == 1` filtering of `[2,1,1]` gates).
   - Wired fast decoupled dispatch for `layered(n, [3])` (`B is None and max_errors is None and not min_errors and W >= 1`) into `solve(...)`.
   - Extended `compile_partial(...)` return dicts with `cost3_status` (`"skipped" | "sat" | "certified_impossible" | "unsat" | "unknown"`) and `cost3_solver_unsat` (`lower_bound < 4 and cost3_status == "unsat"`).

2. **`tests/test_bounds_partial.py`**
   - Added `test_solve_three_halfspaces_all_gates_and_w1` and `test_compile_partial_cost4_certification_and_fields` (`n=3 parity3` and `n=6` partial care disjoint 3-OR).

3. **`experiments/g8_cost4_benchmark.py` and `experiments/results/g8_cost4_benchmark.json`**
   - Pre-registered fixed benchmark (`seed 8820` targets, `seed 8821` `192/256` care sets) + `audit_weight_bounds(...)` verifying care/full `W <= 8` and `W <= 16` solutions across every uncertified `W <= 4` row with `cerp.kernel.evaluate` and `cerp.kernel_bounds`.

4. **`claims/PROPOSED.md`**
   - Added proposed claims under branch heading `gemini/G8` (no `Pnnn` IDs assigned; frozen files, `THEORY.md` §5, `claims/GAPS.json`, and existing `claims/REGISTER.md` statuses untouched).

## Exact Acceptance Check & Verification Outputs

- **`experiments/g8_cost4_benchmark.py`** (pre-registered at `0ce31fa`, run on `gemini/G8`, then `--audit` run after adding `audit_weight_bounds`):
  - Generation: `4040` attempts (`rejected_balance=3567`, `rejected_cost1_or_w1=144`, `rejected_width2_w4=229`, `rejected_width2_unknown=0`) in `168.037s`.
  - Compile + verify (`W=4, max_width=4, time_limit=60.0s, workers=4`):
    - `sat_count`: `100 / 100`
    - `verified_within_60s`: `100 / 100`
    - `cost_histogram`: `{"4": 94, "3": 6}`
    - `collapsed_to_cost1_on_care`: `0`, `collapsed_to_cost3_on_care`: `6` (`5` certified minimal, `1` `idx=56` solvable at `cost=1, W<=16`)
    - `certified_cost4_within_60s`: `81` (`81 / 94 = 86.17%` of `W=4` cost-4 targets; `81 / 81 = 100.0%` of targets without `W<=16` width-2 care collapse)
    - `solver_unsat_without_cert_count`: `13` (`13.0%` of all targets, `13.83%` of `W=4` cost-4 targets)
    - `certified_minimal_within_60s`: `86 / 100` (`5` cost-3 + `81` cost-4)
    - Timing: `median_seconds = 1.6616`, `mean_seconds = 2.7312`, `max_seconds = 14.1109`, `wall_seconds = 274.257`.
  - Weight-bound audit (`weight_bound_audit` in `experiments/results/g8_cost4_benchmark.json`):
    - `uncertified_cost4_total`: `13`
    - `uncertified_cost4_care_width2_w8_sat`: `11`
    - `uncertified_cost4_care_width2_w16_sat`: `13`
    - `uncertified_cost4_full_width2_w8_sat`: `9`
    - `uncertified_cost4_full_width2_w16_sat`: `11`
    - `uncertified_cost3_total`: `1` (`idx=56`), `uncertified_cost3_care_cost1_w16_sat`: `1`

- **Rule 7 checks (verified on final code/data state):**
  1. `python -m cerp.register check` -> `0 problem(s), 33 status note(s); report: claims\LEDGER_CHECK.md` (`git diff -w claims/LEDGER_CHECK.md` empty; `claims/LEDGER_CHECK.md` restored cleanly).
  2. `python -m cerp.status --check` -> exited `0`.
  3. `python -m pytest -q` -> `160 passed, 1 failed in 1002.35s (0:16:42)`:
     - Only failure is `tests/test_lean.py::test_proof_files_compile_and_use_only_standard_axioms`, which hit its hardcoded `600s` per-file subprocess timeout (`tests/test_lean.py:75`) while compiling `Bounds.lean` (`proofs/lean/` was not modified on this branch).
  4. Standalone Lean `v4.12.0` compile (into `$env:TEMP\semplex_lean_olean\G8`) & axiom audit (`LEFTOVER_OLEAN=0`, zero `sorryAx`, zero `Lean.ofReduceBool`):
     - `Cerp.lean`: exit `0` (`72.75s`), `Audit.lean`: exit `0` (`2.74s`)
     - `Theory.lean`: exit `0` (`29.39s`), `AuditTheory.lean`: exit `0` (`2.39s`)
     - `Bounds.lean`: exit `0` (`646.65s`), `AuditBounds.lean`: exit `0` (`2.44s`)
