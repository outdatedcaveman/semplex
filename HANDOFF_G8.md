# Handoff: G8 (Gap B2 — Certified Minimal Cost-4 at n = 8)

**Branch:** `gemini/G8` (cut from `origin/claude/practical-shannon-oqg60y` at `cb37616`)

## Pre-Registered Benchmark Protocol & Success Criteria (Committed Before Execution)

- **Script:** `experiments/g8_cost4_benchmark.py`
- **Output artifact:** `experiments/results/g8_cost4_benchmark.json`
- **Target generator:** `n = 8`, `100` distinct Boolean functions generated via `numpy.random.default_rng(8820)` using random 3-hidden-unit step nets (`w_hidden in [-3, 3]`, `b_hidden in [-6, 6]`, `w_out in [-2, 2]`, `b_out in [-3, 3]`, `25%-75%` ones, i.e., `64..192 / 256`), accepting only targets where `netsolve.solve(f, 8, layered(8, [2]), W=4)` returns `"unsat"` on the full 256-row truth table.
- **Care-set sampling:** For each target in generation order, sample `192 / 256` (`75%`) care points using `numpy.random.default_rng(8821)`.
- **Compiler invocation:** `cerp.netsolve.compile_partial(f, 8, care, W=4, max_width=4, time_limit=60.0, workers=4)`.
- **Numeric HELD criteria:**
  1. Among all non-collapsing targets (`cost > 3` on the 192-point care set), `>= 90%` return a verified cost-4 network (`cerp.kernel.evaluate` agrees on all `192` care points) AND a kernel-verified minimal cost-4 certificate (`cerp.kernel_bounds.check_not_two_halfspaces_partial` passes on both `pos` and `neg`) within `60.0s` on 4 cores.
  2. Every reported `sat` network passes `cerp.kernel.evaluate` on all care points, and every certified lower bound passes `cerp.kernel_bounds`.
- **Mandatory secondary metrics to report at top upon completion:**
  - Exact count of full-table cost-4 targets (`|w| <= 4` width-2 UNSAT) that collapse to `cost <= 3` (`cost == 3` and `cost == 1`) on the `75%` care set.
  - Exact count and fraction of targets where the CP-SAT solver proves width-2 `W=4` `"unsat"` on the care set without a kernel-checkable `not-two-halfspaces` certificate (`cost3_solver_unsat == True`).
- **Numeric BROKEN criteria:**
  - Any `kernel.evaluate` or `kernel_bounds` verification mismatch, OR `< 90%` verified + certified-minimal cost-4 among non-collapsing targets within `60s`.

## Implementation Summary (Pre-Benchmark)

1. **`cerp/netsolve.py`**:
   - Added decoupled exact 3-halfspace solver `_solve_three_halfspaces_gate` and `_solve_three_halfspaces` dispatching `layered(n, [3])` across all 5 canonical 3-input threshold P-classes (`or_and`, `and_or`, `maj3`, `and3`, `or3`, filtering `[2,1,1]` gates when `W == 1`).
   - Updated `compile_partial(...)` to record `cost3_status` (`"skipped" | "sat" | "certified_impossible" | "unsat" | "unknown"`) and `cost3_solver_unsat`.
2. **`tests/test_bounds_partial.py`**:
   - Added `test_solve_three_halfspaces_all_gates_and_w1` and `test_compile_partial_cost4_certification_and_fields` (`10 passed in 8.19s`).
