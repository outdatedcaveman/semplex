# Handoff: Exact Semidirect Generator Locking, Orthogonal Bias-Free Retention, Stochastic Interventional DPI, & Variational MDL Closure (`gemini/master-principle-closure`)

**Status:** `[BUILT, AUDITED & EMPIRICALLY VERIFIED — COMMIT 1 61db985, 39/39 RUNS PASSED (5/5 HMC HELD), READY FOR RULE 7]`

**Branch:** `gemini/master-principle-closure` (base commit `7be5346`, Commit 1 `61db985721b10489eb339f0f08eeff1781c7f284`)

**Scope:** Closes the residual gaps from `gemini/master-principle-lie-lyapunov` (`ee14372`): (1) replacing soft mixed-word relation penalties (`0.0178` `A4` homomorphism drift) with exact semidirect-product generator locking (`S_3 = C_3 ⋊ C_2`, `A_4 = V_4 ⋊ C_3`) plus comparing Augmented-Lagrangian (`spectral_alm_gen`) dynamic constraint enforcement, (2) eliminating Phase-2 catastrophic forgetting without replay or kept-label masking via Moore–Penrose spectral whitening of Phase-1 invariants + bias-free plain SGD (`semidirect_exact_etf`), and (3) unifying stochastic channel TV data-processing bounds (`StochasticInterventionalDPI`) with variational MDL parameter compression (`2d < |G|d`).

---

## 1. Prior Art vs. Semplex Synthesis

- **Prior Art:** Semidirect group presentations (`C_3 ⋊ C_2`, `V_4 ⋊ C_3`), orthogonal subspace continual learning / feature whitening, total-variation data-processing inequality (`tvDist`), and amortized variational optimization (`arXiv:2202.00665`, `arXiv:2605.10878`, `arXiv:2611.10501`, `arXiv:1609.07152`, `arXiv:2602.15029`, Levin–Friston–Chis-Ciure Markov-blanket screening) are established components.
- **Semplex Synthesis & Contribution:** Unifies all five mechanisms inside `34/34` audited Mathlib `v4.12.0` theorems (`Semplex.Closure` in `proofs/lean-mathlib/MasterPrincipleClosure.lean`) AND proves in a controlled 2×2 ablation (`experiments/master_principle_closure.py`, `39` runs) that **neither** exact semidirect algebra alone (`semidirect_exact_linear`: `L32 = 1.0000`, `forgetting_after_keep = 0.5000` on `A4`) **nor** whitened bias-free SGD alone over softly regularized Cayley matrices (`cayley_ufr_soft_etf`: `L32 = 0.2807`, `forgetting_after_keep = 0.0386` on `A4`) closes both OOD composition and zero-replay continual retention — whereas uniting exact semidirect presentation invariants with Moore–Penrose whitened bias-free SGD (`semidirect_exact_etf`) achieves `L4..L32 = 1.0000`, `forgetting_after_keep = 1.0000` (`forgetting_drop = 0.0000`), and `85.9%` parameter compression (`2,160` vs `15,356` parameters on `A4`).

---

## 2. Formal Verification (`MasterPrincipleClosure.lean` — 34/34 Audited Theorems)

Built in isolated Mathlib `v4.12.0` package (`proofs/lean-mathlib/MasterPrincipleClosure.lean`, `CLOSURE_BUILD_RC=0` in `284.74s`, `0` errors, `0` warnings; `lake env lean AuditMasterPrincipleClosure.lean` `CLOSURE_AUDIT_RC=0` in `76.46s`, strictly standard axioms `[propext, Classical.choice, Quot.sound]`, `0 sorryAx`):

1. **`SemidirectExactUnitary` (10 theorems):** Exact unitary generator families `s3GenS(φ)`/`s3GenR` and `a4GenS`/`a4GenT(φ₁, φ₂)` satisfy `s^2 = 1`, `r^3 = 1` / `t^3 = 1`, and mixed relations `(s*r)^2 = 1` / `(s*t)^3 = 1` identically across arbitrary continuous torus phases `φ, φ₁, φ₂ : ℝ` and arbitrary `U(d)` gauge conjugations `gaugeConj V M = V * M * Vᴴ`, while preserving unitarity and `trace`.
2. **`OrthogonalReadoutRetention` (6 theorems):** Exact zero-forgetting conservation under arbitrary-length bias-free SGD folds (`foldOrthSGD`) orthogonal to kept features (`orth_batch_sgd_logit_invariant`, `orth_sgd_preserves_margin`, `orth_sgd_preserves_argmax`), paired with a concrete `bias_drift_flips_prediction_witness` counterexample showing additive bias flips argmax even with frozen weights.
3. **`StochasticInterventionalDPI` (7 theorems):** Non-negativity, symmetry, reflexivity, triangle inequality, general column-stochastic channel TV data-processing inequality (`stochastic_channel_tv_dpi`: `tvDist (K *ᵥ p) (K *ᵥ q) ≤ tvDist p q`), strict 3:1 noisy hidden-bit POMDP separation (`passive tv = 0` vs `active tv = 1/2`), and Markov-blanket screening (`markov_blanket_screened_kernel`).
4. **`VariationalDescriptionClosure` (6 theorems):** Exact `d × d` unitary Frobenius norm squared (`unitary_frobNormSq`: `frobNormSq M = d`), gauge invariance, generator MDL compression (`semidirect_generator_mdl_compression`: `2d < |G|d` for `|G| > 2`), amortized quadratic free-energy optimality (`amortized_quad_ge_opt`, `amortized_quad_eq_iff_zero_gap`), and midpoint convexity (`quadEnergy_midpoint_convex`).
5. **`MasterPrincipleSynthesis` (5 theorems):** Unified `MasterPrincipleClosureBundle` instances for `S_3` (`|G| = 6`, `d = 2`) and non-ambivalent `A_4` (`|G| = 12`, `d = 3`), combined gauge-trace + orthogonal-SGD invariance (`orth_whitened_exact_representation_zero_forgetting`), joint DPI + active witness separation, and joint MDL + variational + Markov-blanket closure summary.

---

## 3. Empirical Campaign (`39/39` Runs, `1444.05s`, All `5/5` Pre-Registered `HMC` Hypotheses `HELD`)

Pre-registered in `experiments/results/master_principle_closure_predictions.json` and executed in `experiments/master_principle_closure.py` (`--workers 2`, 3 seeds per configuration, summary saved in `experiments/results/master_principle_closure.json`).

### Pre-Registered Verdicts (`HMC.1`–`HMC.5`)

| Hypothesis | Verdict | Key Measured Values vs Criterion |
|---|---|---|
| `HMC.1` | **HELD** | `semidirect_exact_etf` `hom_err = 3.55e-13` (`A4`) & `1.15e-13` (`S3`), `1.0000` OOD balanced accuracy across ALL lengths through `A4 L=32` (`8x` max train len `4`) & `S3 L=16`; `spectral_alm_gen` cuts `A4` `hom_err` to `7.70e-8 < 0.0178` (`1.0000` at `L=32`). |
| `HMC.2` | **HELD** | Zero-replay, zero-masking Phase-2 `forgetting_after_keep = 1.0000` (`drop = 0.0000`) on BOTH `A4` and `S3_bouquet` (`semidirect_exact_etf`), vs `0.5000` (`semidirect_exact_linear`, gap `+0.5000 >= +0.25`) and `L32_bacc = 0.2807` / `after_keep = 0.0386` (`cayley_ufr_soft_etf`, `L32` gap `+0.7193 >= +0.55`). |
| `HMC.3` | **HELD** | `active_interventional_probe` vs `passive_sampling_probe`: `noisy_hidden_bit_pomdp` mean analytical TV `0.7000` vs `0.0000` (acc `0.8492` vs `0.5000`); `stochastic_s3_holonomy_pomdp` mean TV `0.7750` vs `0.0000` (acc `0.8504` vs `0.5678`); `0` TV DPI violations. |
| `HMC.4` | **HELD** | Generator Frobenius MDL ratio `0.1667 < 0.25` (`A4`) and `0.3333 < 0.40` (`S3_bouquet`), with `A4` parameter ratio `2,160 / 15,356 = 0.1407 <= 0.50`. |
| `HMC.5` | **HELD** | Float64 `f64_pres_hom_err = 5.46e-15`, `f64_trace_err = 1.11e-15`, 50-channel TV DPI `max_excess = -1.12e-2` (`0` violations), 50-trial Matrix-KL `min_gap = 0.1341 >= -1e-12`, and `max_neural_unitary_err = 8.34e-6 < 1e-5`. |

### Arm 1: `A4 = V4 ⋊ C3` (`|G| = 12`, Train `L ∈ {2,3,4}`, Eval through `L = 32`, Keep `c ∈ {0,1}`, Fine-Tune `c ∈ {2,3}`)

| Model | Params | `hom_err` | `mdl_ratio` | `L4` | `L12` | `L24` | `L32` | Keep Before | Keep After | Drop | Post-P2 Probe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `semidirect_exact_etf` | **2,160** | `3.55e-13` | `0.1667` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | **1.0000** | **0.0000** | 1.0000 |
| `semidirect_exact_linear` | 2,164 | `3.28e-13` | `0.1667` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 0.5000 | 0.5000 | 1.0000 |
| `spectral_alm_gen` | 5,124 | `7.70e-8` | `0.1667` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 0.5000 | 0.5000 | 1.0000 |
| `cayley_ufr_soft_etf` | 15,352 | `0.0619` | `1.0000` | 0.9991 | 0.5816 | 0.3158 | 0.2807 | 1.0000 | 0.0386 | 0.9614 | 1.0000 |
| `cayley_unitary_ufr_soft` | 15,356 | `0.0602` | `1.0000` | 0.9965 | 0.5167 | 0.3079 | 0.3491 | 0.9982 | 0.0596 | 0.9386 | 0.9963 |

### Arm 1: `S3 = C3 ⋊ C2` Two-Loop Bouquet (`|G| = 6`, `11` Orbits, Train `Lloop ∈ {2,3}`, Eval through `Lloop = 16`, Keep `0..5`, Fine-Tune `6..10`)

| Model | Params | `hom_err` | `mdl_ratio` | `L3` | `L6` | `L12` | `L16` | Keep Before | Keep After | Drop | Post-P2 Probe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `semidirect_exact_etf` | **5,292** | `1.15e-13` | `0.3333` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | **1.0000** | **0.0000** | 1.0000 |
| `semidirect_exact_linear` | 5,303 | `1.01e-13` | `0.3333` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 0.6667 | 0.3333 | 1.0000 |
| `spectral_alm_gen` | 8,747 | `0.0050` | `0.3333` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 1.0000 | 0.0000 | 1.0000 |
| `cayley_unitary_ufr_soft` | 15,671 | `0.0772` | `1.0000` | 1.0000 | 0.7417 | 0.0712 | 0.0765 | 1.0000 | 0.5625 | 0.4375 | 0.9914 |

### Arm 2: Stochastic Interventional vs. Passive POMDPs (`η ∈ {0.0, 0.15, 0.30}`, `n = 2000` / seed)

| World | Mode | Mean TV (Exact) | Mean TV (Emp) | Mean Acc | `η=0.00` Acc | `η=0.15` Acc | `η=0.30` Acc | DPI Viols |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `noisy_hidden_bit_pomdp` | `active_interventional_probe` | **0.7000** | 0.7036 | **0.8492** | 1.0000 | 0.8541 | 0.6935 | 0 |
| `noisy_hidden_bit_pomdp` | `passive_sampling_probe` | 0.0000 | 0.0000 | 0.5000 | 0.5000 | 0.5000 | 0.5000 | 0 |
| `stochastic_s3_holonomy_pomdp` | `active_interventional_probe` | **0.7750** | 0.7769 | **0.8504** | 1.0000 | 0.8487 | 0.7025 | 0 |
| `stochastic_s3_holonomy_pomdp` | `passive_sampling_probe` | 0.0000 | 0.0058 | 0.5678 | 0.6667 | 0.5675 | 0.4693 | 0 |

### Arm 3: Exact Float64 Closure, 50-Channel DPI, & 50-Trial Matrix-KL Audits

- `S3` float64 presentation max `hom_err = 2.71e-15`, `unitary_err = 2.74e-15`
- `A4` float64 presentation max `hom_err = 5.46e-15`, `unitary_err = 5.63e-15`
- Gauge-trace invariance max error `= 1.11e-15`
- 50 random column-stochastic channel TV DPI max excess `= -0.01116` (`0` violations)
- 50-trial amortized Matrix-KL variational optimality min gap `= 0.13410 >= -1e-12`
- Max neural unitary constraint violation across all 27 runs `= 8.34e-6 < 1e-5`

---

## 4. Tier-2 Source Integration Status

See `research/TIER2_MASTER_PRINCIPLE_INTEGRATION_2026-11-22.md` for full accounting of all 14 Tier-2 sources (`#4, #6, #15, #16, #20, #27, #29, #31, #32, #34, #39, #40, #45, #49`): `#15, #31` integrated in `gemini/master-principle-lie-lyapunov`; `#6, #16, #34, #39, #40` formalized and tested here alongside `#4` alignment; `#20, #27` scoped for next-cycle MoE/epiplexity coupling; `#29, #32, #45, #49` routed cleanly to companion foundational work.

---

## 5. Honest Limitations & Scope Boundaries

1. **Explicit solvable generator templates:** `semidirect_exact_etf` encodes exact semidirect generator parametrizations for solvable finite groups `S_3 = C_3 ⋊ C_2` and `A_4 = V_4 ⋊ C_3` (with diverse irrep-multiplicity / chiral head spectra spanning full conjugacy/orbit rank). Non-solvable simple groups such as `A_5` require explicit icosahedral/projective generator templates or `spectral_alm_gen` constrained optimization (`7.70e-8` on `A4`, `0.0050` on `S3`).
2. **Moore–Penrose whitening assumptions:** Exact Phase-2 orthogonal retention relies on Phase-1 features approximately spanning the kept classes' invariant subspace with kept vs fine-tuned invariant traces separated inside the whitened spectral cone; novel unseen invariant subspaces introduced during Phase 2 whose support overlaps previously kept class traces are not protected against interference by readout orthogonality alone.
3. **Rule 7 Gate Discipline:** Required Rule 7 checks on commit (`cerp.register check`, `cerp.status --check`, 5/5 core Lean audits `Audit`, `AuditBounds`, `AuditClosure`, `AuditInference`, `AuditTheory`, and `pytest -q`); exact post-final-edit test counts and runtimes are recorded in the Commit 2 message after passing.
