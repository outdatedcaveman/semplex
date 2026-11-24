# G11 Handoff — Continuous Gaussian Product & Pushforward Invariance (`Gap C1`)

- **Branch:** `gemini/G11` (base commit `cb37616af1f9d2e37eb19c2c169069b745a33863`)
- **Target:** Isolate Mathlib measure-theoretic formalization of continuous i.i.d. centered Gaussian product invariance and equivariant pushforward invariance under signed permutations in `proofs/lean-mathlib/`, leaving `proofs/lean/` untouched (`git diff proofs/lean/` empty).
- **Files added/changed:**
  - `.gitignore` — ignore `proofs/lean-mathlib/.lake/`.
  - `proofs/lean-mathlib/lean-toolchain` — pinned to `leanprover/lean4:v4.12.0`.
  - `proofs/lean-mathlib/lakefile.toml` & `proofs/lean-mathlib/lake-manifest.json` — isolated package `CerpMathlib` pinned to `mathlib4` `rev = "v4.12.0"` (`809c3fb3b5c8f5d7dace56e200b426187516535a`); prebuilt cache tested without compiling Mathlib from source, and `.lake/` deleted before commit.
  - `proofs/lean-mathlib/CerpMathlib.lean` — targeted imports (`Mathlib.Probability.Distributions.Gaussian`, `Mathlib.MeasureTheory.Constructions.Pi`) proving:
    - `gaussianReal_map_neg`: `(gaussianReal 0 v).map Neg.neg = gaussianReal 0 v`.
    - `iid_symmetric_pi_map_actRealVec`: invariance of any symmetric i.i.d. product probability measure `(Measure.pi fun _ : Fin n => μ₀)` under `actRealVec σ` (`SignedPerm n`).
    - `gaussianProd_map_actRealVec`: signed-permutation invariance of `(gaussianProd n v) = Measure.pi fun _ : Fin n => gaussianReal 0 v` on `Fin n → ℝ`.
    - `gaussianProd_pushforward_equivariant`: `((gaussianProd n v).map T).map (actRealVec σ) = (gaussianProd n v).map T` for any measurable equivariant `T : (Fin n → ℝ) → (Fin n → ℝ)`.
    - `gaussianProd_readout_map_invariant`: `((gaussianProd n v).map F).map actC = (gaussianProd n v).map F` for any measurable `F : (Fin n → ℝ) → C` equivariant into `(actC : C → C)`.
    - `theorem15_gaussian_circuit_mass_eq` & `theorem15_gaussian_iter_circuit_mass_eq`: continuous Gaussian probability mass equality `(gaussianProd n v).map (fun θ => readout (Nat.iterate step t θ)) {actC tgt} = ... {tgt}` matching `P160`'s finite `theorem15_finite_distribution_invariant`.
  - `proofs/lean-mathlib/AuditMathlib.lean` — `#print axioms` audit script for every proved theorem.
  - `claims/PROPOSED.md` — appended Gap C1 continuous Gaussian invariance proposal.
- **Exact Mathlib Build & Axiom Verification (`lake` `5.0.0`, `mathlib4` `v4.12.0`, host `7.88 GB` RAM / `27.4 GB` commit):**
  - Prebuilt `.olean` cache unpacked cleanly (`5134/5134` files, zero Mathlib source compilation).
  - `lake build CerpMathlib` -> `exit=0` in `195.23s` (`✔ [2024/2025] Built CerpMathlib`).
  - `lake env lean AuditMathlib.lean` -> `exit=0` in `163.42s`; every theorem depends only on standard axioms `[propext, Classical.choice, Quot.sound]` (`measurable_iterate` zero axioms, `iterate_equivariant` `[propext, Quot.sound]`, zero `sorryAx` / `Lean.ofReduceBool` / `Lean.trustCompiler`).
- **Exact Bridge & Remaining Gap vs `P160` (`proofs/lean/Theory.lean` `Theorem15`, L1594–2324):**
  1. **Cross-package boundary:** `proofs/lean/Theory.lean` remains Mathlib-free (`~24–29s` compile), so `CerpMathlib.SignedPerm` / `actRealVec` mirrors `PFT.SignedPerm` / `PFT.actVec` structurally rather than importing `PFT`.
  2. **Optimizer scalar & moment instantiation:** `P160` proves `theorem15_gd_trajectory_equivariant` and `theorem15_adamw_trajectory_equivariant` for any `AdamScalar S` (instantiated in `Theory.lean` on `Int`), whereas `CerpMathlib` treats any measurable equivariant `step : (Fin n → ℝ) → (Fin n → ℝ)`. Supplying an `AdamScalar ℝ` instance (`sqrt := Real.sqrt`, continuous stabilized division `x / (√v + ε)` for AdamW's second moment, and embedding `θ₀ ↦ (θ₀, 0, 0)` in `AdamWState ℝ n`) plus proving `Measurable step` and `Measurable readout` (finite-threshold circuit partition measurability on `ℝ^n`) remains if both layers are unified into a single Mathlib module.
- **Rule 7 checks (verified on final code/data state):**
  - `pytest -q` -> `159 passed in 964.92s (0:16:04)` (`PYTEST_EXIT=0`, including `tests/test_lean.py::test_proof_files_compile_and_use_only_standard_axioms`).
  - Standalone Lean `v4.12.0` (`Cerp` `51.00s`, `Theory` `21.84s`, `Bounds` `569.21s`, `Audit` `3.50s`, `AuditTheory` `2.45s`, `AuditBounds` `1.94s`), all exit `0`, `bad_axioms=False` (`[propext, Classical.choice, Quot.sound]` only), `LEFTOVER_OLEAN=0`.
  - `git diff proofs/lean/` empty (`PROOFS_LEAN_DIFF_EMPTY=True`); `proofs/lean-mathlib/.lake/` absent before commit.
  - `python -m cerp.register check` -> exit `0` (`0 problem(s), 33 status note(s)`); `git diff -w claims/LEDGER_CHECK.md` empty.
  - `python -m cerp.status --check` -> exit `0`.
