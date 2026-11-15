# Handoff: G9 (Gap A10 — Symmetry Orbits of Minimum Threshold Circuits)

**Branch:** `gemini/G9` (cut from `origin/claude/practical-shannon-oqg60y` at `cb37616`, pre-registered at `d1ca9b4`)

## Headline Outcome (Fraction of 1-Orbit Classes)

- **Under unoriented hyperplane-partition equivalence (hidden units identified up to sign flip `g <-> ~g`, matching `cerp/atlas.py`'s `H` and Gap A10 "the function fixes its mechanism"):**
  - **`n <= 4` combined (`242` NPN classes, 100% exact over ALL LTFs):** **`80 / 242` (`33.0579%`)** have `num_orbits == 1` (`54 / 216 = 25.0%` among non-threshold `cost >= 3` classes):
    - `n = 1`: **`2 / 2` (`100.0%`)**
    - `n = 2`: **`4 / 4` (`100.0%`)** (`1 / 1` at `cost = 3`)
    - `n = 3`: **`9 / 14` (`64.2857%`)** (`6 / 6` at `cost = 1`, `3 / 7` at `cost = 3`, `0 / 1` at `cost = 4`)
    - `n = 4`: **`65 / 222` (`29.2793%`)** (`15 / 15` at `cost = 1`, **`50 / 128 = 39.06%` at `cost = 3`**, `0 / 78` at `cost = 4`, `0 / 1` at `cost = 5`)
  - **`n = 5`, `cost <= 3` with `|w| <= 3` (100% completed in `188.98s`, `7,295` classes):** **`3,725 / 7,295` (`51.0624%`)** have `num_orbits == 1` (`42 / 42` at `cost = 1`, **`3,683 / 7,253 = 50.779%` at `cost = 3`**).
- **Under strict oriented hidden-function equivalence (distinguishing `g` from `~g`):**
  - **`n <= 4` combined:** **`26 / 242` (`10.7438%`)** (`2 / 2` at `n=1`, `3 / 4` at `n=2`, `6 / 14` at `n=3`, `15 / 222` at `n=4`), and **`0 / 216` (`0.0%`)** for every `cost >= 3` class (each minimal unoriented width-`w` circuit splits into `2^w` distinct oriented sign variants).
  - **`n = 5`, `cost <= 3` (`|w| <= 3`):** **`42 / 7,295` (`0.5757%`)** (`42 / 42` at `cost = 1`, `0 / 7,253` at `cost = 3`).
- **`n = 5` stopping point & weight-bound scope:**
  - `enumerate_n5_cost_le3(W=3, time_limit=5400.0)` **completed all `42` `cost = 1` + `7,253` `cost = 3` NPN classes (`stopped_reason = "completed"` in `188.98s`)**. Scope excludes the `61,760` additional 5-variable LTFs (`94,572 - 32,812`) requiring `|w| >= 4` and all `cost >= 4` NPN classes at `n = 5`.
  - For `n <= 4`, `|w| <= 3` already exhausts `100%` of all LTFs (`4, 14, 104, 1882`), and depth >= 3 circuits cannot achieve minimum cost (`cost 3`: `[1,1]` collapses to `cost 1`; `cost 4`: `[2,1]` collapses to `cost 3`; `cost 5 parity4`: blocked by `Bounds.lean: parity4_not_three_ltf_determined`), so `n <= 4` counts are globally exact across arbitrary weights and layered depths.

## Summary of Changes

1. **`cerp/orbits.py`**
   - Implemented `ltfs_with_bound`, `_stabilizer_indices` (`G_f` with output negation where it fixes `f`), `count_orbits`, `enumerate_class_bruteforce`, `enumerate_dimension` (`1 <= m <= 4` via `AND2`, canonical `AND3`/`AND_OR`/`MAJ3`, and `parity4` `G_f`-orbit + 64-pair conflict cover), and `enumerate_n5_cost_le3`.

2. **`tests/test_g9_orbits.py`**
   - Verified `ltfs_with_bound` matches `atlas.KNOWN_LTF_COUNTS` for `n <= 4` with `|w| <= 3`.
   - Re-derived **all `20` NPN classes (`2 + 4 + 14`) on `n <= 3`** by independent brute force (`C(|H|, w)` and `C(|L|, w)`), verifying exact agreement on every field (`cost`, `gf_order`, `num_circuits`, `num_orbits`, `orbit_sizes`, and oriented counts).
   - Verified all `128` `cost = 3` classes on `n = 4` and Orbit-Stabilizer invariants.

3. **`experiments/g9_orbits.py` and `experiments/results/g9_orbits.json`**
   - Generated complete orbit tables across `n = 1, 2, 3, 4` (`242` classes, `118.7s` total) and `n = 5 (cost <= 3, |w| <= 3)` (`7,295` classes, `188.98s`).

4. **`claims/PROPOSED.md`**
   - Added `gemini/G9` proposed claims (no `Pnnn` IDs assigned; `THEORY.md` §5, `claims/GAPS.json`, `claims/REGISTER.md`, and `experiments/FROZEN.json` untouched).

## Exact Acceptance Check & Verification Outputs

- **`experiments/g9_orbits.py`** (`experiments/results/g9_orbits.json`):
  - `n = 1`: `2` classes, unoriented 1-orbit `2/2`, oriented 1-orbit `2/2`, `0.001s`
  - `n = 2`: `4` classes, unoriented 1-orbit `4/4`, oriented 1-orbit `3/4`, `0.003s`
  - `n = 3`: `14` classes, unoriented 1-orbit `9/14` (`6` cost-1 + `3` cost-3; `cost=4 parity3`: `62` circuits, `5` orbits), oriented 1-orbit `6/14`, `0.094s`
  - `n = 4`: `222` classes, unoriented 1-orbit `65/222` (`15` cost-1 + `50` cost-3; `cost=4` `78` classes -> `238,245` circuits / `101,211` orbits, min orbits > 1; `cost=5 parity4` -> `12,404` circuits / `52` orbits under `|G_f|=384`), oriented 1-orbit `15/222`, `118.646s`
  - `n = 5 (cost <= 3, |w| <= 3)`: `7,295` classes (`42` cost-1, `7,253` cost-3; `325,915` cost-3 unoriented circuits in `114,817` orbits; `3,725/7,295` 1-orbit unoriented), `188.98s`, `stopped_reason = "completed"`
  - Every row verified: `sum(orbit_sizes) == num_circuits` and all orbit sizes divide `gf_order`.

- **Rule 7 checks (verified on final code/data state):**
  - `python -m cerp.register check` -> exit `0` (`0 problem(s), 33 status note(s)`); `git diff -w claims/LEDGER_CHECK.md` empty.
  - `python -m cerp.status --check` -> exit `0`.
  - `pytest -q` -> `161 passed, 1 failed in 1022.04s (0:17:02)` (sole failure: `tests/test_lean.py::test_proof_files_compile_and_use_only_standard_axioms` `TimeoutExpired` at `600s` compiling `Bounds.lean` on this 8 GB RAM host).
  - Standalone Lean `v4.12.0` (`C:\Users\bruno\.elan\toolchains\leanprover--lean4---v4.12.0\bin\lean.exe`) full compile + audit (`.olean` built into `$env:TEMP` and removed, `LEFTOVER_OLEAN=0`): `Cerp.lean` exit `0` (`54.32s`), `Theory.lean` exit `0` (`26.46s`), `Bounds.lean` exit `0` (`650.43s`), `Audit.lean` exit `0` (`2.48s`), `AuditTheory.lean` exit `0` (`2.82s`), `AuditBounds.lean` exit `0` (`2.00s`), `bad_axioms=False` (standard axioms `[propext, Classical.choice, Quot.sound]` only).
