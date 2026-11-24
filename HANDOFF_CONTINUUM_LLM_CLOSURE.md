# Handoff: Continuum Kernel Covariance, Gate-3 Groupoid Bridge, Arbitrary-n Cubical Stabilization & Real Pretrained HuggingFace Probes (`gemini/master-principle-continuum-llm-closure`)

## 1. PR Stack Lock & Branch Context

- Merged stacked PRs `#2 -> #5 -> #7 -> #8` cleanly (`--merge`, zero `--squash`, preserving all SHAs/refs) into `master` (`ebdb3ced0ac146923925daa39a515b4323200239`), leaving PR #3 (`ccr-a50507aa-kgdlx2`) and active Draft PR #4 (`research/distinction-calculus-2026-11-20`) untouched and open.
- Cut fresh branch `gemini/master-principle-continuum-llm-closure` directly off locked `origin/master`.

---

## 2. Formal Track Closure Matrix

| Track | Deliverables | Verified Status | Axiom / Safety Notes |
| --- | --- | --- | --- |
| **Pure Lean 4 (Gate-3 Bridge + Spike 31 Reconciliation)** | `proofs/lean/CausalCovarianceGroupoidBridge.lean`, `proofs/lean/AuditCausalCovarianceGroupoidBridge.lean`, `proofs/lean/lakefile.lean`, `proofs/lean/check_all.ps1` | `BUILD_BRIDGE_RC=0`, `AUDIT_BRIDGE_RC=0`, `17/17` declarations audited | Strictly `[]`, `[propext]`, or `[propext, Quot.sound]`; **zero `Classical.choice`**, `0 sorryAx` |
| **Mathlib v4.12.0 (17th Library: Continuum Kernels)** | `proofs/lean-mathlib/ContinuumKernelCovariance.lean`, `proofs/lean-mathlib/AuditContinuumKernelCovariance.lean`, `proofs/lean-mathlib/lakefile.toml` | `MATHLIB_BUILD_ALL17_RC=0`, `MATHLIB_AUDIT_RC=0`, `19/19` new theorems (`370/370` total across `17` libs) | Zero warnings on `ContinuumKernelCovariance.lean`, `0 sorryAx`; covers general measurable, `[PolishSpace] [T2Space]` & `[StandardBorelSpace]` |
| **Cubical Agda `2.9.0 --cubical=full` (9th Module: `n ≥ 4` Stabilization)** | `proofs/cubical/src/Semplex/Cubical/InductiveHigherHorn.agda` | `ALL9_CUBICAL_PASS`, `CUBICAL_RC=0` across `9` modules | **Zero warnings** (`Fin zero = ⊥`, `Fin (suc n) = ⊤ ⊎ Fin n`), proves contractible horn filling for all `n ≥ 4` (`Cosk2-filler-contr-ge-4`) for `BG G` & `U2Monoid` |

### Exact Pure Lean 4 Audited Declarations (`17/17`, Zero `Classical.choice`)
`exact_experimentCost_transport`, `exact_experimentTrace_transport`, `exact_profileEquality_preserved`, `exact_profileEquality_reflected_constructive`, `exact_profileEquality_iff_constructive`, `groupoidEquivalenceComp`, `representation_induces_profileGroupoidEquivalence`, `representation_preserves_contractible_fibers`, `groundedProfileGroupoid_transport_equivalence`, `groundedProfileGroupoid_transport_fibers_contractible`, `groundedModuliToTransportedProfileEquiv`, `groundedModuliToTransportedProfile_fiber_contractible`, `stochasticTrace_totalWeight_pos`, `distEq_trans_of_pos`, `validStochasticExp_target`, `stochastic_induces_profileGroupoidEquivalence`, `stochastic_preserves_contractible_fibers`.

### Exact Mathlib Continuum Theorems (`19/19` in `Semplex.ContinuumKernelCovariance`)
`traceMap_measurable`, `traceMap_measurableEmbedding`, `measure_map_injective_of_measurableEmbedding`, `traceMap_measure_injective`, `traceKernel_isMarkov`, `kernel_map_comp_of_comm`, `kernel_map_prod_of_comm`, `continuum_experimentCost_le_of_monotone`, `continuum_traceKernel_transport`, `continuum_externalTraceMeasure_transport`, `continuum_profile_preserved_scaled`, `continuum_profile_reflected_embedding`, `continuum_profile_iff_affordable_embedding`, `continuum_profile_reflected_polish`, `continuum_profile_iff_polish`, `continuum_profile_reflected_standardBorel`, `continuum_profile_iff_standardBorel`, `continuum_event_variation_pushforward_eq`, `continuum_noninjective_real_counterexample`.

---

## 3. Empirical Pretrained HuggingFace & Continuum Polish Kernel Findings (`811.70s`)

Executed single-threaded (`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, `torch.set_num_threads(1)`) against pre-registered predictions in `experiments/results/pretrained_checkpoint_gauge_predictions.json` (never edited after running; results saved in `experiments/results/pretrained_checkpoint_gauge_results.json`).

| Hypothesis | Checkpoint / Domain | Verdict | Key Observed Numbers & Honest Root Cause |
| --- | --- | --- | --- |
| **`HP.1`** | `cross-encoder/ms-marco-MiniLM-L-6-v2` (22.7M params, 6 layers) | **`BROKEN`** | `temp_recal_flips = 0`, `flip_per_tv_int4 = 1.0689 > flip_per_tv_layer_deletion = 0.3810`, `margin_auroc_int4 = 0.9968` **held**, **but** `fp32_infam_acc = 0.6375 < 0.85` at a fixed `0.0` cutoff (ranking margins for borderline paraphrases sit near `-0.3`), so matching a `63.75%`-accurate teacher at `T = 0.7017` increased raw ECE (`0.3055 -> 0.3789`); also `oof_flip_rate_int4 = 0.0125 == infam_flip_rate_int4` (`2` total flips). |
| **`HP.2`** | `HuggingFaceTB/SmolLM2-135M-Instruct` (135M params, 30 layers) | **`BROKEN`** | Deletion temperature recalibration gave `temp_recal_flips = 0` and cut ECE by `51.82%` (`0.4623 -> 0.2228`), and `flip_per_tv_int4 = 2.0542 > 0.4384`. **However**, raw `Yes/No` exhibited strong `Yes`-sycophancy (`fp32_infam_acc = 0.5208`), full per-channel `int4` collapsed predictions (`87.5%` total flips, `84/96`), inverting margin prediction (`AUROC = 0.1558`). **Striking Sirius-Tiamat replication:** keeping ONLY `mlp.down_proj` in `fp32` cut `int4` flips ~4.5x (`0.8958 -> 0.2292` In-Family, `0.8542 -> 0.1667` OOF). |
| **`HP.3`** | `ms-marco-MiniLM-L-6-v2` ZeroVLN Prop. 1–2 (`22,713,216` params) | **`BROKEN`** | Exact `float64` Prop. 2 held to machine precision (`prop2_pyth_rel_err = 1.367e-16`, `prop2_orth_cos_abs = 9.499e-17`, `orthogonal_waste_fraction = 0.9634`), `frozen_taskA_drop = 0.0`, and SFT caused `sft_taskA_logit_l2_drift = 10.5807` (`sft_taskB_acc = 1.0`), **but** frozen `[CLS]` only scored `0.60 < 0.90` on standalone topic routing because `ms-marco` `[CLS]` is trained specifically for cross-attention pair matching rather than single-text clustering. |
| **`HP.4`** | `SmolLM2-135M-Instruct` ZeroVLN Prop. 1–2 (`7,080,192` top-2-block params) | **`HELD`** | `frozen_taskA_drop = 0.0`, `frozen_taskB_acc = 0.8750 >= 0.85`, `sft_taskA_logit_l2_drift = 2.2131`, `prop2_pyth_rel_err = 1.283e-16`, `prop2_orth_cos_abs = 9.823e-18`, `orthogonal_waste_fraction = 0.9988` (`sft_taskB_acc = 0.78125`). |
| **`HP.5`** | Polish `ℝ²` Ornstein-Uhlenbeck Markov Kernel (`seeds [101, 202, 303]`) | **`HELD`** | `jacobian_log_density_max_err = 7.105e-15`, `mc_energy_dist_err_max = 0.001010`, `projection_collapse_ratio_max = 0.0` under cubic shear diffeomorphism `φ` vs projection `ψ`. |

---

## 3b. Scope Clarifications (`G_prof` vs `G_rep` & Empirical Interpretation)

- **Profile Groupoids (`G_prof`) vs Representation Automorphism Groupoids (`G_rep`):** `CausalCovarianceGroupoidBridge.profileKernelGroupoid`, `stochasticProfileKernelGroupoid`, and `ContinuumKernelCovariance`'s profile-equivalence theorems characterize **observational profile equivalence** (`PLift (profile(e) = profile(e'))`, thin groupoids with trivial automorphism groups). Contractible fibers between thin profile groupoids establish representation-invariant observational covariance, **not** triviality of the underlying representation-gauge automorphism groupoid `G_rep` when sensors hide internal coordinates without an independent separating anchor.
- **`HP.3`–`HP.5` Statistical Limits:** In `HP.3` and `HP.4`, `sft_taskA_acc` increased (`0.6375 -> 0.65` and `0.5208 -> 0.625` respectively), so `sft_taskA_logit_l2_drift` reflects logit/gauge shift rather than Task-A accuracy loss, and `frozen_taskA_drop = 0.0` holds directly by keeping the backbone frozen. `orthogonal_waste_fraction` is a local inner-product statistic comparing the multi-step AdamW update against the initial Task-B gradient `g` rather than a matched-return global comparison. `HP.5` checks a unit-Jacobian volume-preserving cubic shear (`|det J| = 1`) and does not yet stress non-constant Jacobian determinants or arbitrary measurable embeddings.

---

## 4. Verification & Reproducibility

```powershell
python -m cerp.register check
python -m cerp.status --check
powershell -ExecutionPolicy Bypass -File proofs/lean/check_all.ps1
cd proofs/lean-mathlib && lake build && lake env lean AuditContinuumKernelCovariance.lean
# WSL Agda 2.9.0:
# /opt/Agda-nightly/bin/agda -v0 --cubical=full -i proofs/cubical/src proofs/cubical/src/Semplex/Cubical/InductiveHigherHorn.agda
$env:OMP_NUM_THREADS="1"; $env:MKL_NUM_THREADS="1"
python experiments/pretrained_checkpoint_gauge_probe.py
python -m pytest -q
```
