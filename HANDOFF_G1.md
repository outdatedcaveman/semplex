# Handoff G1: Theorem 15 in Lean (Gap C1 / P069)

**Branch:** `gemini/G1` (cut cleanly from `origin/claude/practical-shannon-oqg60y` at `262281e`)  
**Gap targeted:** `C1` (`P069`, `THEORY.md` §3.7 Theorem 15)  
**Scope status:** **Lemma toward Theorem 15** (`paper proof + finite case in Lean`). Conclusion 1 (deterministic trajectory equivariance for concrete GD and concrete AdamW) and Conclusion 2 (distributional invariance over any finite `σ`-invariant weighted initial ensemble) compile in Lean 4.12 core with standard axioms (`[propext]` / `[propext, Quot.sound]`, zero `sorry`, zero `ofReduceBool`). What remains unmechanized without Mathlib is the continuous Gaussian measure $\mathcal{N}(0, \sigma_w^2 I)$ over $\mathbb{R}^n$ and continuous Fréchet differentiation (modeled via finite-difference `fdGrad` or assumed gradient equivariance in `*_of_grad`).

## What was done

Added `section Theorem15` (§20) to [`proofs/lean/Theory.lean`](proofs/lean/Theory.lean) and `#print axioms` checks to [`proofs/lean/AuditTheory.lean`](proofs/lean/AuditTheory.lean). Both `SignedPerm n` (the coordinate permutation + sign-flip group action) and `gdStep` / `adamwStep` (elementwise 1st & 2nd moments with $g^2$ sign-evenness, bias corrections, $\sqrt{\hat{v}} + \varepsilon$ normalization, and decoupled weight decay) are defined **concretely**, along with concrete fixed-point `Int` scalar arithmetic (`intFixedScalar`) whose algebraic laws (`symIntDiv_neg_left`, `-(-a)=a`, etc.) are all proved in Lean core.

### Hypothesis-to-paper mapping (`THEORY.md` §3.7 Theorem 15)

| Paper sentence / proof step (`THEORY.md` §3.7) | Lean identifier / hypothesis in `Theory.lean` (§20 `Theorem15`) | Notes |
|---|---|---|
| "σ acts on parameters linearly: input permutation permutes columns of `W1`, input negation flips sign of one column, output negation flips `W2, b2`" | `SignedPerm n` (`toFun`, `invFun`, `left_inv`, `right_inv`, `sgn`), `actVec F σ v`, `permVec σ v`, `actAdamWState F σ s`, proved invertible via `actVec_left_inv`, `actVec_right_inv`, `actVec_comp`, `actAdamWState_left_inv` | `θ` and 1st moment `m` transform via `actVec`; 2nd moment `v` transforms via unsigned coordinate permutation `permVec`. |
| "(i) The initialization law is invariant under this action." | `init : List (Nat × Θ)`, `hinit : EnsembleInvariant actΘ init` (pushforward invariance), discharged for duplicate-free orbit pools by `ensembleInvariant_of_nodup_support` | Finite weighted ensemble in Lean core; continuous i.i.d. $\mathcal{N}(0, \sigma_w^2 I)$ requires Mathlib measure theory. |
| "(ii) The loss on g at θ equals the loss on g at σθ." | `hL_inv : ∀ θ, L (actVec F σ θ) = L θ` | Derived concretely into gradient equivariance `fdGrad_equivariant` (`fdGrad F L stepScale δ`) with zero assumed gradient axiom (`*_of_grad` also supports analytic gradients). |
| "(iii) GD, AdamW's moment estimates, the elementwise normalization and weight decay all commute with coordinate permutations and sign flips." | `gdStep`, `gdStep_equivariant`, `adamwStep`, `adamwStep_equivariant` (concrete elementwise `m`, `v` via `signedVal_sq_invariant` proving `(-g)*(-g) = g*g`, `div_neg_left`, decoupled `oneSubLrWd`) | Abstracted over `AdamScalar S` + concretely instantiated by `intFixedScalar : AdamScalar Int` (zeros/quotients/square roots verified without external axioms). |
| "So the trajectory from σθ₀ is σ applied to the trajectory from θ₀." | `iterStep_equivariant`, `runSchedule_equivariant` (supporting time-varying AdamW $(1-\beta_1^t), (1-\beta_2^t)$ bias-correction schedules) | Applies directly at arbitrary step horizon `t`. |
| "(iv) The readout ... is equivariant." | `readout : Θ → C`, `hreadout : ∀ θ, readout (actΘ θ) = actC (readout θ)`, plus left inverse `hC_left : ∀ c, invC (actC c) = c` on circuits | `hC_left` expresses injectivity of circuit action `actC` (without redundant right-inverse). |
| Conclusion 1 (deterministic equivariance) | `theorem15_trajectory_equivariant`, `theorem15_gd_trajectory_equivariant`, `theorem15_adamw_trajectory_equivariant` | `readout (step^[t] (σ • s)) = actC σ (readout (step^[t] s))` |
| Conclusion 2 (probability/weight landing on `I` equals `σ • I`) | `circuitMass`, `theorem15_finite_distribution_invariant`, `theorem15_adamw_finite_distribution_invariant` | Equal total weight over `init` on `tgt` and `actC tgt`. |

## Exact acceptance check and verbatim output

1. Lean 4.12 compilation & axiom audit (`Cerp`, `Theory`, `Bounds`, `Audit`, `AuditTheory`, `AuditBounds`): exited `0`. Verbatim §20 lines from `AuditTheory.lean`:
```text
'PFT.symIntDiv_neg_left' depends on axioms: [propext, Quot.sound]
'PFT.intFixedScalar' depends on axioms: [propext, Quot.sound]
'PFT.actVec_left_inv' depends on axioms: [propext, Quot.sound]
'PFT.actVec_right_inv' depends on axioms: [propext, Quot.sound]
'PFT.actVec_comp' depends on axioms: [propext, Quot.sound]
'PFT.fdGrad_equivariant' depends on axioms: [propext, Quot.sound]
'PFT.gdStep_equivariant' depends on axioms: [propext, Quot.sound]
'PFT.adamwStep_equivariant' depends on axioms: [propext, Quot.sound]
'PFT.theorem15_trajectory_equivariant' depends on axioms: [propext]
'PFT.theorem15_gd_trajectory_equivariant' depends on axioms: [propext, Quot.sound]
'PFT.theorem15_adamw_trajectory_equivariant' depends on axioms: [propext, Quot.sound]
'PFT.theorem15_finite_distribution_invariant' depends on axioms: [propext]
'PFT.ensembleInvariant_of_nodup_support' depends on axioms: [propext, Quot.sound]
'PFT.theorem15_adamw_finite_distribution_invariant' depends on axioms: [propext, Quot.sound]
```

2. `python -m cerp.register check`: exited `0` (`0 problem(s), 37 status note(s); report: claims\LEDGER_CHECK.md`). `git diff -w claims/LEDGER_CHECK.md` empty; restored via `git checkout -- claims/LEDGER_CHECK.md`.

3. `python -m cerp.status --check`: exited `0`.

4. Filtered `& "$env:TEMP\semplex_extras_venv\Scripts\python.exe" -m pytest -q -k "not test_search_keeps_a_working_rule_working"`:
```text
........................................................................ [ 47%]
........................................................................ [ 94%]
.........                                                                [100%]
153 passed, 1 deselected in 525.61s (0:08:45)
```

## What failed / open

- Continuous Gaussian measure $\mathcal{N}(0, \sigma_w^2 I)$ and continuous Fréchet gradients remain informal paper proof (require Mathlib measure theory and calculus); therefore `P069` stays `"paper proof + finite case in Lean"`.
- Base test `tests/test_localrules.py::test_search_keeps_a_working_rule_working` (deselected above) fails on `262281e` (`0.875 < 0.9`) and is fixed separately on branch `origin/gemini/G6` (`4b0f36a`).
