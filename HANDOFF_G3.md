# Handoff: G3 (Gap B2 — Care-Set Compilation at n = 8, 10)

**Branch:** `gemini/G3` (cut from `origin/claude/practical-shannon-oqg60y` at `262281e`)

## Summary of Changes

1. **`cerp/kernel_bounds.py`**
   - Added `check_not_two_halfspaces_partial(n, f, care, bad) -> Verdict`: partial-function analogue of `check_not_two_halfspaces` requiring every witness point in `S`, `pos`, `neg` to lie in `care`, verifying `_sums_equal(n, pos, neg)`, and exhaustively checking all 2-colourings on the bad-set universe (`len(universe) <= 20`).

2. **`cerp/bounds.py`**
   - Added `_exact_fraction_witness` and `_lp_farkas_witness`: solves exact Farkas feasibility over all real halfspaces via `scipy.optimize.linprog(..., method="highs")`, followed by sparse Carathéodory CP-SAT / exact `Fraction` RREF extraction and full CP-SAT fallback.
   - Upgraded `not_threshold_cert` (for `n > 6`) and `not_threshold_cert_partial` (using `k = 2` deduplication plus `_lp_farkas_witness` for `n > 6` or large care sets) while preserving exact `k = 2..kmax` combinatorial loop behavior for `n <= 6`.
   - Added `not_two_halfspaces_cert_partial(n, f, care, kmax=3, max_iters=64)` using fast 4-bit packed `k = 2` pair conflict graph + short odd cycle BFS (`_find_short_odd_cycle`) and CEGAR with `_lp_farkas_witness` cuts + minimal UNSAT core extraction (`_minimize_bad`).

3. **`cerp/netsolve.py`**
   - Replaced exponential `(2 * W + 1) ** i` symmetry-breaking weights with linear-size lexicographic chain symmetry breaking across interchangeable neurons.
   - Added `_solve_two_halfspaces(...)` fast decoupled AND/OR CP-SAT path inside `solve(...)` when solving unslacked 1-hidden-layer width-2 `step` specifications (`B is None and max_errors is None and not min_errors and W >= 1`).
   - Added `compile_partial(f, n, care, W=4, max_width=4, time_limit=60.0, workers=4)`: incremental compiler combining Farkas 1-threshold checking, width-2 compilation, partial 2-halfspace lower-bound certificates (`not_two_halfspaces_cert_partial` on `f & care` and `(~f) & care`), and incremental search over `w = 3 .. max_width`.

4. **`tests/test_bounds_partial.py`**
   - Added `test_not_two_halfspaces_partial_and_forgeries`, `test_not_threshold_partial_lp_n8`, and `test_compile_partial_n4_and_n8` covering partial lower-bound checks, forgery rejection, LP witness search at `n = 8`, and `compile_partial` verification against `cerp.kernel.evaluate`.

5. **`experiments/g3_care_benchmark.py` and `experiments/results/g3_care_benchmark.json`**
   - Fixed benchmark matching `experiments/spike36.py`'s generator at `n = 8` (seed `8800`, 100 distinct non-threshold targets, 192/256 = 75% care set) and `n = 10` (seed `8810`, 100 distinct non-threshold targets, 768/1024 = 75% care set), with every returned network checked against `cerp.kernel.evaluate` on all care inputs.

6. **`claims/PROPOSED.md`**
   - Recorded proposed claim `B2-G3` with exact numbers, evidence, and scope limitations (no edits to `THEORY.md` §5, `claims/GAPS.json`, `claims/REGISTER.md`, or frozen files in `experiments/FROZEN.json`).

## Benchmark & Verification Results

- **Fixed G3 benchmark (`experiments/g3_care_benchmark.py`):**
  - **`n = 8` (`seed = 8800`, `192/256` care):**
    - `verified_within_60s`: **100 / 100 (100%)**
    - `certified_minimal_within_60s`: **100 / 100 (100%)** (`99` cost-3 via `not-threshold-partial`, `1` cost-1 `trivial`)
    - Timing: median `0.2789s`, mean `0.3034s`, max `0.9845s`, wall `31.097s`
  - **`n = 10` (`seed = 8810`, `768/1024` care):**
    - `verified_within_60s`: **100 / 100 (100%)**
    - `certified_minimal_within_60s`: **100 / 100 (100%)** (`100` cost-3 via `not-threshold-partial`)
    - Timing: median `2.2451s`, mean `2.2657s`, max `4.6495s`, wall `229.892s`

- **Rule 7 Sequential Checks:**
  1. `python -m cerp.register check` -> `0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md` (`git diff -w claims/LEDGER_CHECK.md` empty; restored cleanly).
  2. `python -m cerp.status --check` -> exit code `0`.
  3. `python -m pytest -q -k "not test_search_keeps_a_working_rule_working" --tb=short` -> `156 passed, 1 deselected in 539.88s (0:08:59)`.
     - *Excluded test note:* `test_search_keeps_a_working_rule_working` is deselected per Rule 7 because of the pre-existing `262281e` baseline failure already resolved independently on `gemini/G6`.
  4. Lean 4.12.0 audits (`Cerp.lean`, `Theory.lean`, `Bounds.lean` built into `$env:TEMP\semplex_lean_olean`, then `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`) -> `LEAN_ALL_OK leftover_olean=0` (only `[propext, Classical.choice, Quot.sound]`, zero `sorryAx`, zero `Lean.ofReduceBool`).
