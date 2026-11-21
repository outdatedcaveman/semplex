# G13 Handoff — End-to-End Closure of Theorem 15 (`Gap C1`)

- **Branch:** `gemini/G13` (base commit `7be53461c70c14ed261843975fd7428a18e02f31` on `origin/claude/practical-shannon-oqg60y`)
- **Goal:** Connect `P160` (step equivariance in a discrete model) and `P169` (abstract Gaussian invariance for any measurable equivariant step) inside `proofs/lean-mathlib/CerpMathlib.lean`, closing Gap `C1` / Theorem 15 (`THEORY.md` §3.7, `P069`) for a continuous two-layer network over `ℝ`, logistic loss, **true analytic gradient** (`deriv`), GD and AdamW with zero initial moments and time-varying schedules, i.i.d. centered Gaussian first-layer + symmetric output-layer prior, and a concrete Spikes 09–14 unoriented threshold-prefix circuit readout — with zero residual equivariance or measurability hypotheses left.
- **Files added / modified:**
  - `proofs/lean-mathlib/CerpMathlib.lean` — preserves all 9 existing `G11` declarations intact and adds the full `G13` Theorem 15 closure (`section G13`).
  - `proofs/lean-mathlib/AuditMathlib.lean` — `#print axioms` verification for all 9 `G11` declarations and all 27 new `G13` declarations (36 total).
  - `claims/PROPOSED.md` — appended Section 11 (`G13`, no `Pnnn` IDs assigned).
  - `HANDOFF_G13.md` — this handoff.
  - `proofs/lean/` and `proofs/lean-mathlib/lakefile.toml` are completely untouched (`git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/ proofs/lean-mathlib/lakefile.toml` empty).

---

## 1. Summary of Proved Constructions & Theorems (`proofs/lean-mathlib/CerpMathlib.lean`)

1. **Two-Layer Architecture, Binary `{-1, +1}^n` Encoding, Logistic Loss, and Group Action (Item 1):**
   - `paramDim n H := H * n + H + H + 1`, `TwoLayerParams n H := Fin (paramDim n H) → ℝ`, canonical equivalence `paramBlockEquiv` splitting `(W1, b1, W2, b2)`.
   - `actBool σ x := fun i => xor (σ.sgn i) (x (σ.invFun i))`, `IsTargetSymmetry g σ outFlip := ∀ x, g (actBool σ x) = xor outFlip (g x)` (uniformly handles both `g ∘ σ = g` when `outFlip = false` and `g ∘ σ = ¬g` when `outFlip = true`).
   - `liftSignedPerm n H σ outFlip` maps `W1` rows by `σ`, leaves `b1` invariant, and negates `W2, b2` iff `outFlip = true`.
   - `preAct θ h x`, `logit φ θ x`, `logisticSampleLoss y z := Real.log (1 + Real.exp (-(boolToPM1 y * z)))`, normalized full-batch `logisticLoss φ g θ`.

2. **Step (ii) Loss Invariance (Item 2):**
   ```lean
   theorem logisticLoss_invariant {n H : Nat} (φ : ℝ → ℝ)
       (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
       (hSym : IsTargetSymmetry g σ outFlip) (θ : TwoLayerParams n H) :
       logisticLoss φ g (actRealVec (liftSignedPerm n H σ outFlip) θ) = logisticLoss φ g θ

   theorem hiddenFlip_logisticLoss_invariant {n H : Nat} (φ : ℝ → ℝ)
       (hOdd : ∀ z, φ (-z) = -φ z) (g : (Fin n → Bool) → Bool)
       (h0 : Fin H) (θ : TwoLayerParams n H) :
       logisticLoss φ g (actRealVec (hiddenFlipSignedPerm n H h0) θ) = logisticLoss φ g θ
   ```

3. **True Analytic Gradient Equivariance, Backpropagation Equivalence, Measurability, and Concrete `tanh` (Item 3a):**
   ```lean
   def trueGrad {d : Nat} (L : (Fin d → ℝ) → ℝ) (θ : Fin d → ℝ) : Fin d → ℝ :=
     fun i => deriv (fun t : ℝ => L (Function.update θ i t)) (θ i)

   theorem trueGrad_equivariant {d : Nat} (L : (Fin d → ℝ) → ℝ) (σ : SignedPerm d)
       (hLinv : ∀ θ, L (actRealVec σ θ) = L θ) (θ : Fin d → ℝ) :
       trueGrad L (actRealVec σ θ) = actRealVec σ (trueGrad L θ)

   theorem trueGrad_logisticLoss_eq_explicitGrad {n H : Nat} (φ φ' : ℝ → ℝ)
       (hφd : ∀ z, HasDerivAt φ (φ' z) z) (g : (Fin n → Bool) → Bool) :
       trueGrad (@logisticLoss n H φ g) = explicitGrad φ φ' g

   theorem measurable_trueGrad_logisticLoss {n H : Nat} {φ φ' : ℝ → ℝ}
       (hφd : ∀ z, HasDerivAt φ (φ' z) z) (hφm : Measurable φ) (hφ'm : Measurable φ')
       (g : (Fin n → Bool) → Bool) :
       Measurable (trueGrad (@logisticLoss n H φ g) : TwoLayerParams n H → TwoLayerParams n H)

   def tanhReal (x : ℝ) : ℝ := Real.sinh x / Real.cosh x
   theorem tanhReal_odd (x : ℝ) : tanhReal (-x) = -tanhReal x
   theorem hasDerivAt_tanhReal (x : ℝ) : HasDerivAt tanhReal (tanhRealDeriv x) x
   theorem measurable_tanhReal : Measurable tanhReal
   theorem measurable_tanhRealDeriv : Measurable tanhRealDeriv
   ```

4. **GD & AdamW with Zero Initial Moments and Arbitrary Schedules (Item 3b):**
   - `gdStepReal`, `runGDSchedule` (arbitrary `(lr, wd)` schedule `sched : Nat → ℝ × ℝ`).
   - `adamwStepReal`, `runAdamWSchedule` (arbitrary `sched : Nat → AdamWCfgReal` starting from zero initial moments `(θ, 0, 0)`).
   - Proved `gdStepReal_equivariant`, `measurable_gdStepReal`, `runGDSchedule_equivariant`, `measurable_runGDSchedule`, `adamwStepReal_equivariant`, `measurable_adamwStepReal`, `runAdamWSchedule_equivariant`, `measurable_runAdamWSchedule`.

5. **Block-Product Symmetric Initialization & Concrete Spikes 09–14 Readout (Item 4):**
   - `twoLayerInitMeasure n H vW1 vB1 μW2 μb2`: i.i.d. `N(0, vW1)` on `W1`, `N(0, vB1)` on `b1`, and arbitrary symmetric probability laws `μW2`, `μb2` on `W2`, `b2` (covering centered Gaussians via `gaussianReal_map_neg` and zero-bias point mass via `dirac_zero_map_neg`); proved `twoLayerInitMeasure_invariant`.
   - `concreteCircuitReadout g : TwoLayerParams n H → CircuitOut n`: extracts Boolean hidden halfspaces `decide (0 ≤ preAct θ h x)`, sorts `Fin H` by decreasing `|w2 θ h|` (breaking ties deterministically by `h.val`), selects the shortest prefix determining `g`, and returns `some` of the canonical unoriented halfspace `Finset` in `Sym2 ((Fin n → Bool) → Bool)` (or `none`). Proved `concreteCircuitReadout_equivariant` and `measurable_concreteCircuitReadout` (via finite discrete factorization `ReadoutSig n H`).

6. **End-to-End Theorem 15 Closures (Zero Residual Equivariance or Measurability Hypotheses):**
   ```lean
   theorem theorem15_twoLayer_adamw_concrete {n H : Nat}
       (φ φ' : ℝ → ℝ) (hφd : ∀ z, HasDerivAt φ (φ' z) z)
       (hφm : Measurable φ) (hφ'm : Measurable φ')
       (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
       (hSym : IsTargetSymmetry g σ outFlip)
       (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
       (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
       (sched : Nat → AdamWCfgReal) (t : Nat) (tgt : CircuitOut n) :
       (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
           (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
           {actCircuitOut σ tgt} =
         (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
           (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H φ g)) sched t θ))
           {tgt}

   theorem theorem15_twoLayer_tanh_adamw_concrete {n H : Nat}
       (g : (Fin n → Bool) → Bool) (σ : SignedPerm n) (outFlip : Bool)
       (hSym : IsTargetSymmetry g σ outFlip)
       (vW1 vB1 : ℝ≥0) (μW2 μb2 : Measure ℝ) [IsProbabilityMeasure μW2] [IsProbabilityMeasure μb2]
       (hW2 : μW2.map Neg.neg = μW2) (hb2 : μb2.map Neg.neg = μb2)
       (sched : Nat → AdamWCfgReal) (t : Nat) (tgt : CircuitOut n) :
       (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
           (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
           {actCircuitOut σ tgt} =
         (twoLayerInitMeasure n H vW1 vB1 μW2 μb2).map
           (fun θ => concreteCircuitReadout g (runAdamWSchedule (trueGrad (@logisticLoss n H tanhReal g)) sched t θ))
           {tgt}
   ```
   (Plus `theorem15_twoLayer_gd_concrete`, `theorem15_twoLayer_tanh_gd_concrete`, and `theorem15_twoLayer_adamw_general_readout`.)

---

## 2. Classification of Every Remaining Hypothesis (`World Assumption` vs `Remaining Gap`)

| Hypothesis / Modeling Detail | Classification | Exact Explanation |
|---|---|---|
| `IsTargetSymmetry g σ outFlip` | **World assumption** | Defining premise of Theorem 15: `σ` (with optional output bit negation `outFlip`) is an actual symmetry of Boolean target `g`. |
| `twoLayerInitMeasure` (`W1, b1 ~ N(0, v)` and symmetric `μW2, μb2`) | **World assumption** | Matches task-symmetric Gaussian/zero-bias initialization (symmetric centered Gaussians via `gaussianReal_map_neg`; zero `b2` via `dirac_zero_map_neg`). |
| Differentiability `(HasDerivAt φ φ')` & measurability of `φ, φ'` | **Discharged for `tanh`** / **World assumption for general `φ`** | Discharged unconditionally in `theorem15_twoLayer_tanh_*` via `tanhReal`; oddness is **not** needed for input symmetries `σ` (`logisticLoss_invariant` holds for any `φ`), and enters separately for hidden-unit negation (`hiddenFlip_logisticLoss_invariant`). Excludes activations non-differentiable at 0 (e.g. exact kink ReLU). |
| Deterministic full-batch loss over all `2^n` inputs; zero initial AdamW moments `(0, 0)`; deterministic schedule `sched` | **World assumption** | Matches Spikes 09–14 full-batch Boolean training from standard zero-moment AdamW init; stochastic mini-batch sampling would require an extra assumption that batch order/noise is `σ`-invariant in distribution. |
| Exact `ℝ` real arithmetic & exact `deriv` | **Remaining gap (numerical)** | Continuous `ℝ` semantics ignore IEEE-754 float32 rounding and non-associative summation order in CPU/GPU kernels (`proofs/lean/Theory.lean` models discrete integer fixed-point rounding separately). |
| `concreteCircuitReadout g` (`0 ≤ preAct` threshold + `\|w2\|`-ordered shortest prefix determining `g` with `h1.val ≤ h2.val` tie-break) | **Remaining gap (modeling detail)** | Exact `\|w2\|` invariance holds under `liftSignedPerm`, making the `h1.val ≤ h2.val` tie-break exactly equivariant everywhere; Spikes 09–14's exact Python/CP-SAT post-processing is covered only via `theorem15_twoLayer_adamw_general_readout` provided the post-processor itself is equivariant (PyTorch/Python `sort` with non-deterministic float ties on measure-zero sets would match only a.e.). |

---

## 3. Exact Build & Axiom Audit Output (`proofs/lean-mathlib/`)

- `lake build CerpMathlib` -> `✔ [2024/2025] Built CerpMathlib`, `Build completed successfully.` (`exit 0` in `282.47s`, zero errors, zero warnings).
- `lake env lean AuditMathlib.lean` -> `exit 0` in `211s`, all **36** audited declarations depend ONLY on `[propext, Classical.choice, Quot.sound]` (no `sorryAx`):
  - `CerpMathlib.gaussianReal_map_neg`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.iid_symmetric_pi_map_actRealVec`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.gaussianProd_map_actRealVec`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.gaussianProd_pushforward_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.gaussianProd_readout_map_invariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_gaussian_circuit_mass_eq`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_iterate`: `no axioms`
  - `CerpMathlib.iterate_equivariant`: `[propext, Quot.sound]`
  - `CerpMathlib.theorem15_gaussian_iter_circuit_mass_eq`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.logisticLoss_invariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.hiddenFlip_logisticLoss_invariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.trueGrad_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.trueGrad_logisticLoss_eq_explicitGrad`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_trueGrad_logisticLoss`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.tanhReal_odd`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.hasDerivAt_tanhReal`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_tanhReal`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_tanhRealDeriv`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.gdStepReal_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_gdStepReal`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.runGDSchedule_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_runGDSchedule`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.adamwStepReal_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_adamwStepReal`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.runAdamWSchedule_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_runAdamWSchedule`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.blockSymmetricPi_map_actRealVec`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.dirac_zero_map_neg`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.twoLayerInitMeasure_invariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.concreteCircuitReadout_equivariant`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.measurable_concreteCircuitReadout`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_twoLayer_adamw_concrete`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_twoLayer_tanh_adamw_concrete`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_twoLayer_gd_concrete`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_twoLayer_tanh_gd_concrete`: `[propext, Classical.choice, Quot.sound]`
  - `CerpMathlib.theorem15_twoLayer_adamw_general_readout`: `[propext, Classical.choice, Quot.sound]`

---

## 4. Rule 7 Acceptance Output

- `python -m cerp.register check` -> `0 problem(s), 46 status note(s)` (`exit 0`; CRLF-only diff on `claims/LEDGER_CHECK.md` reverted).
- `python -m cerp.status --check` -> `exit 0`.
- `SEMPLEX_LEAN_TIMEOUT=900` (`%TEMP%\semplex_extras_venv\Scripts\python.exe -m pytest -q`) -> `167 passed in 1338.11s (0:22:18)` (`exit 0`).
- Standalone Lean `v4.12.0` compile & audit (`.olean` compiled to `%TEMP%`, `LEAN_OK=True`, `LEFTOVER_OLEAN=0`, zero `sorryAx`, zero `Lean.ofReduceBool`):
  - `Cerp.lean` (`80.34s`), `Audit.lean` (`2.51s`) — `exit 0`
  - `Theory.lean` (`34s`), `AuditTheory.lean` (`3.61s`) — `exit 0`
  - `Bounds.lean` (`666.08s`), `AuditBounds.lean` (`2.8s`) — `exit 0`
  - `Closure.lean` (`2.51s`), `AuditClosure.lean` (`1.04s`) — `exit 0`
  - `Inference.lean` (`1.85s`), `AuditInference.lean` (`1.01s`) — `exit 0`
- `git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/ proofs/lean-mathlib/lakefile.toml` empty; `proofs/lean-mathlib/.lake/` absent before commit.
