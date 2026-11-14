# Proposed Claims — G3 (Gap B2: Care-Set Compilation at n = 8, 10)

## Proposed Claim B2-G3: Certified Partial-Care Threshold Compilation at n = 8 and n = 10

- **Statement:** Using decoupled 2-halfspace CP-SAT compilation (`_solve_two_halfspaces`), linear-size lexicographic chain symmetry breaking across interchangeable hidden neurons (`netsolve.solve`), and exact LP Farkas + Carathéodory/Fraction lower-bound search (`bounds.not_threshold_cert_partial`, `bounds.not_two_halfspaces_cert_partial`), the incremental compiler `netsolve.compile_partial(..., W=4, max_width=4, time_limit=60.0, workers=4)` compiles and certifies minimality for 100/100 non-threshold `spike36`-family targets at `n = 8` (75% care set, `192/256` points) and 100/100 at `n = 10` (75% care set, `768/1024` points), with every compiled network verified against `cerp.kernel.evaluate` on all care inputs and every lower bound verified by `cerp.kernel_bounds`.
- **Exact Evidence:**
  - Benchmark script: `experiments/g3_care_benchmark.py`; raw results: `experiments/results/g3_care_benchmark.json`.
  - **`n = 8`** (100 distinct non-threshold targets, generator seed `8800`, care seed `8801`, `192/256` care inputs, `time_limit = 60.0s`, `workers = 4`):
    - Verified SAT networks: **100 / 100** (`100%` within 60s)
    - Certified minimal networks: **100 / 100** (`100%` within 60s; `99` cost-3 via `not-threshold-partial`, `1` cost-1 `trivial`)
    - Compile time: median `0.2789s`, mean `0.3034s`, max `0.9845s`, wall `31.097s`
  - **`n = 10`** (100 distinct non-threshold targets, generator seed `8810`, care seed `8811`, `768/1024` care inputs, `time_limit = 60.0s`, `workers = 4`):
    - Verified SAT networks: **100 / 100** (`100%` within 60s)
    - Certified minimal networks: **100 / 100** (`100%` within 60s; `100` cost-3 via `not-threshold-partial`)
    - Compile time: median `2.2451s`, mean `2.2657s`, max `4.6495s`, wall `229.892s`
  - Kernel-checked unit tests in `tests/test_bounds_partial.py`:
    - `test_not_two_halfspaces_partial_and_forgeries`: checks `parity3` partial/full lower-bound certificates via `kernel_bounds.check_not_two_halfspaces_partial` and rejection of forged/incomplete masks and empty bad-set lists.
    - `test_not_threshold_partial_lp_n8`: verifies LP Farkas witness discovery on `n = 8` partial non-threshold (`x0 ^ x1`) and `None` on linearly separable threshold functions.
    - `test_compile_partial_n4_and_n8`: verifies `cost == 1` (`trivial`), `cost == 4` (`lower_bound == 4`, `not-two-halfspaces-partial` on lifted `parity3` at `n = 4`), and `n = 8` partial 2-halfspace compilation against `kernel.evaluate`.
- **What It Does Not Show:**
  - The `spike36` generator samples width-2 threshold nets (`cost <= 3`), so the `n = 8, 10` benchmark validates cost-1 and cost-3 compilation and `not-threshold-partial` certificates at scale, not random `cost >= 4` hardness at `n = 8, 10`.
  - `check_not_two_halfspaces_partial` is bounded to bad-set universes of at most 20 points (`len(universe) <= 20`) and certifies non-representability as a single `AND` or `OR` of two real halfspaces (ruling out width-2 1-hidden-layer threshold nets), not arbitrary deeper DAG topologies.
  - Lower bounds from `not_threshold_cert_partial` and `not_two_halfspaces_cert_partial` apply to 1-hidden-layer `step` networks (`layered(n, [w])`) and do not establish optimality over general DAG or ReLU circuits.
