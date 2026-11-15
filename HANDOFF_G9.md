# Handoff: G9 (Gap A10 — Symmetry Orbits of Minimum Threshold Circuits)

**Branch:** `gemini/G9` (cut from `origin/claude/practical-shannon-oqg60y` at `cb37616`)

## Pre-Registered Protocol & Verification Criteria (Committed Before Execution)

- **Modules & Script:** `cerp/orbits.py`, `experiments/g9_orbits.py` -> `experiments/results/g9_orbits.json`
- **Scope (`|w| <= 3`):**
  1. Complete NPN class enumeration on `n <= 4` (`2, 4, 14, 222` classes; `242` total across `n = 1..4`).
  2. Extension to `n = 5` for `cost <= 3` (`|w| <= 3`), bounded by `N5_TIME_LIMIT = 5400.0s` (`1.5h < 2h`), reporting the exact completion / stopping point.
- **Equivalence Conventions Tabulated:**
  - **Unoriented hyperplane-partition equivalence (`num_circuits`, `num_orbits`):** Each hidden unit is identified by its unordered Boolean partition pair `h = min(g, ~g)` (matching `cerp/atlas.py`'s `H` basis and Gap A9/A10 mechanism-partition semantics, since flipping `g <-> ~g` is absorbed by output weight negation).
  - **Oriented hidden-function equivalence (`oriented_num_circuits`, `oriented_num_orbits`):** Each hidden unit is treated as a literal Boolean function `g in L_n` without quotienting `g <-> ~g`.
  - **`G_f` symmetry group (`gf_order`, `gf_np_order`):** Full NPN stabilizer of class representative `rep` (`perm`, `neg`, and `outneg in {0, 1}` where `apply_T(rep, idx, outneg, n) == rep`), alongside input-only NP stabilizer size.
- **Numeric HELD criteria:**
  1. `tests/test_g9_orbits.py` re-derives `n = 1, 2, 3` (`2 + 4 + 14 = 20` classes) completely by independent brute force (`C(|H|, w)` and `C(|L|, w)` against `L_w`), with `100%` exact equality on every field (`cost`, `gf_order`, `num_circuits`, `num_orbits`, `orbit_sizes`, and oriented twins).
  2. Orbit-Stabilizer invariants (`sum(orbit_sizes) == num_circuits`, every orbit size divides `|G_f|`, and `|G_f| * |NPN_class| == 2^(n+1) * n!`) hold for every tabulated class on `n <= 4` and `n = 5` (`cost <= 3`).

## Pre-Execution Implementation & Test Status

- **`cerp/orbits.py`:** Implemented exact enumerators for `cost = 1, 3, 4, 5` (`n <= 4`) and fast `n = 5 (cost <= 3)` orbit-sieving + chunked `np.packbits` group actions.
- **`tests/test_g9_orbits.py`:** Ran `pytest -q tests/test_g9_orbits.py` -> **`3 passed in 15.65s`**.
