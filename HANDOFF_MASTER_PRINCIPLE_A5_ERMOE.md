# Handoff: Non-Solvable Simple `A5` Icosahedral Closure, ERMoE Gauge Routing, & Unsupervised Epiplexity Selection (`gemini/master-principle-a5-ermoe`)

**Status:** `[BUILT, AUDITED & EMPIRICALLY VERIFIED — COMMIT 1 3fd2644, 27/27 RUNS PASSED (5/5 HA5 HELD), READY FOR RULE 7]`

**Branch:** `gemini/master-principle-a5-ermoe` (base commit `7be5346`, Commit 1 `3fd2644bc236bebb8e205af7c8679df8562333d6`)

**Scope:** Closes the open non-solvable simple-group frontier beyond solvable `S_3` / `A_4`: proves & benchmarks exact golden-ratio icosahedral Galois-pair presentations for `A_5` (`|G| = 60`), integrates ERMoE (`arXiv:2511.10971`, Tier-2 `#20`) per-expert eigen-reparameterized gauge routing with zero-forgetting orthogonal SGD, and verifies unsupervised D-optimal epiplexity sample selection (`arXiv:2608.11746`, Tier-2 `#27`) under scarce Haar budgets.

---

## 1. Prior Art vs. Semplex Synthesis

- **Prior Art:** Icosahedral group `A_5` representations `ρ_3(φ)` / `ρ_3'(ψ)` and `ρ_4`, Eigen-Reparameterized Mixture of Experts (`ERMoE`, `arXiv:2511.10971`), and epiplexity-guided data selection (`arXiv:2608.11746`) are independent lines of work.
- **Semplex Synthesis & Contribution:** Formalizes `30/30` audited theorems in Mathlib `v4.12.0` (`Semplex.A5ERMoE` in `proofs/lean-mathlib/MasterPrincipleA5ERMoE.lean`) unifying `A_5` Galois representations, simplex-gated ERMoE trace invariance + orthogonal SGD, and bounded-observer `epiplexityCount` splitting (`ρ_4` fails to separate `C_5+` vs `C_5-` while `ρ_3(φ)` strictly splits them), and confirms empirically across `27` runs (`5/5 HA5 HELD`) that:
  1. `icosahedral_ermoe_etf` solves non-solvable `A_5` through `L = 32` (`1.0000`, `hom_err = 2.58e-12`, `30×` MDL ratio `0.0333`, `5.39%` parameters of full Cayley) AND retains `1.0000` (`drop = 0.0000`) on `{e, C_2, C_3}` after zero-replay fine-tuning on `{C_5+, C_5-}` (vs `0.6667` for linear head and `0.0097`–`0.0361` for Cayley);
  2. Dynamic Augmented-Lagrangian (`spectral_alm_gen`) without pre-programmed golden ratios also reaches `L32_bacc = 0.9917` (`hom_err = 0.0225`, `10×` tighter than Cayley `0.2082`), though without whitened orthogonal SGD it drops to `0.2333` in Phase 2;
  3. Unsupervised D-optimal epiplexity selection (reading zero labels during selection) achieves `1.0000` OOD balanced accuracy and `1.0000` class coverage across scarce budgets (`B = 10..45`), outperforming uniform Haar sampling by `+0.1111` (`A_5`) and `+0.2121` (`S_3` bouquet).

---

## 2. Formal Verification (`MasterPrincipleA5ERMoE.lean` — 30/30 Audited Theorems)

Built in isolated Mathlib `v4.12.0` package (`proofs/lean-mathlib/MasterPrincipleA5ERMoE.lean`, `A5_BUILD_RC=0` in `389.45s`; `lake env lean AuditMasterPrincipleA5ERMoE.lean` `A5_AUDIT_RC=0` in `104.81s`, strictly standard axioms `[propext, Classical.choice, Quot.sound]`, `0 sorryAx`):

1. **`A5IcosahedralUnitary` (10 theorems):** Golden-ratio roots `phiGolden`, `psiGolden` satisfy `α² = α + 1` and `φ ≠ ψ`; unitary Hermitian `a5GenS α` (`s^2 = 1`) and 3-cycle `a5GenT` (`t^3 = 1`) satisfy `(s*t)^5 = 1` via exact 5-step algebraic factorization; preserved under arbitrary `U(d)` `gaugeConj` and trace; Galois 5-cycle traces satisfy `Tr(s(φ)t) = φ ≠ ψ = Tr(s(ψ)t)`; exact `30×` Frobenius MDL gap (`6 < 180`).
2. **`ERMoEGaugeRouting` (8 theorems):** Any simplex-gated mixture `routedOp g V M = ∑ e, g e • gaugeConj (V e) M` across arbitrary unitary expert eigen-bases preserves `M.trace` and `1`; orthogonal rank-1 / batch bias-free SGD updates annihilate `x_keep` perturbations and preserve kept logits & argmax.
3. **`EpiplexityBoundedObserver` (7 theorems):** Monotonicity of distinguishing relations and `epiplexityCount`, strict `epiplexityCount` gain upon splitting a confounded pair, zero gain from degenerate probes, and concrete witness `a5_rho4_degenerate_rho3_splits` (`0 < 2`).
4. **`Phase5Synthesis` (5 theorems):** Joint Galois presentations, ERMoE trace + zero-forgetting, `30×` MDL + Galois split, epiplexity + ERMoE closure, and inhabited `NonSolvableMasterBundle`.

---

## 3. Empirical Campaign (`27/27` Runs, `813.35s`, All `5/5` Hypotheses `HELD`)

Pre-registered in `experiments/results/master_principle_a5_ermoe_predictions.json` and executed in `experiments/master_principle_a5_ermoe.py` (`--workers 2`, 3 seeds per arm, saved in `experiments/results/master_principle_a5_ermoe.json`).

### Pre-Registered Verdicts (`HA5.1`–`HA5.5`)

| Hypothesis | Verdict | Key Measured Values vs Criterion |
|---|---|---|
| `HA5.1` | **HELD** | `icosahedral_ermoe_etf` (`2.58e-12`) & `icosahedral_exact_linear` (`3.20e-12`) achieve `1.0000` across all `L=5..32` (`+0.7892 >= +0.55` over Cayley `0.2108`); `spectral_alm_gen` cuts `hom_err` (`0.0225 < 0.2082`) and reaches `L32 = 0.9917`. |
| `HA5.2` | **HELD** | Zero-replay Phase-2 `forgetting_after_keep = 1.0000` (`drop = 0.0000`) on `icosahedral_ermoe_etf`, vs `0.6667` (`icosahedral_exact_linear`, `+0.3333 >= +0.25`) and `0.0097` / `L32 = 0.2033` (`cayley_ufr_soft_etf`). |
| `HA5.3` | **HELD** | Unsupervised D-optimal epiplexity achieves `1.0000` mean OOD bacc & `1.0000` coverage on BOTH worlds, vs `0.8889` (`A5`, `+0.1111 >= +0.10`) and `0.7879` (`S3_bouquet`, `+0.2121 >= +0.10`). |
| `HA5.4` | **HELD** | Generator Frobenius MDL ratio `0.03333 < 0.05` (`30×`) and parameter ratio `1,840 / 34,149 = 0.0539 <= 0.10`. |
| `HA5.5` | **HELD** | Float64 `f64_a5_hom_err = 1.48e-14 < 1e-13`, `f64_a5_unitary_err = 1.55e-14 < 1e-13`, `f64_galois_split_err = 1.30e-15 < 1e-14`, 25-trial ERMoE `trace_err = 1.79e-15`, `orth_logit_drift = 1.78e-15`, neural max unitary err `2.67e-5 < 1e-4`. |

### Arm 1: Non-Solvable `A5` (`|G| = 60`, Train `L ∈ {2..5}`, Eval `L = 5..32`, Keep `{e, C2, C3}`, Fine-Tune `{C5+, C5-}`)

| Model | Params | `hom_err` | `mdl_ratio` | `L5` | `L12` | `L24` | `L32` | Keep Before | Keep After | Drop | Post-P2 Probe |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `icosahedral_ermoe_etf` | **1,840** | `2.58e-12` | `0.0333` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | **1.0000** | **0.0000** | 1.0000 |
| `icosahedral_exact_linear` | 1,845 | `3.20e-12` | `0.0333` | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 0.6667 | 0.3333 | 1.0000 |
| `spectral_alm_gen` | 3,285 | `0.0225` | `0.0333` | 0.9958 | 0.9900 | 0.9892 | 0.9917 | 1.0000 | 0.2333 | 0.7667 | 1.0000 |
| `cayley_ufr_soft_etf` | 34,144 | `0.2091` | `1.0000` | 0.2017 | 0.1900 | 0.1892 | 0.2033 | 0.2153 | 0.0097 | 0.2056 | 0.1721 |
| `cayley_unitary_ufr_soft` | 34,149 | `0.2082` | `1.0000` | 0.1917 | 0.1933 | 0.1875 | 0.2108 | 0.2139 | 0.0361 | 0.1778 | 0.1695 |

### Arm 2: Unsupervised D-Optimal Epiplexity Data Selection (`pool = 600` words, zero labels during selection)

| World | Mode | Mean OOD BAcc | Mean Coverage | `B_0` BAcc | `B_1` BAcc | `B_2` BAcc |
|---|---|---:|---:|---:|---:|---:|
| `a5_haar_low_budget` (`B = 10, 20, 40`, `L=32`) | `epiplexity_d_optimal_selection` | **1.0000** | **1.0000** | 1.0000 | 1.0000 | 1.0000 |
| `a5_haar_low_budget` | `uniform_random_sampling` | 0.8889 | 0.8889 | 0.8667 | 0.9333 | 0.8667 |
| `s3_bouquet_haar_low_budget` (`B = 15, 25, 45`, `L=16`) | `epiplexity_d_optimal_selection` | **1.0000** | **1.0000** | 1.0000 | 1.0000 | 1.0000 |
| `s3_bouquet_haar_low_budget` | `uniform_random_sampling` | 0.7879 | 0.7879 | 0.6364 | 0.8485 | 0.8788 |

### Arm 3: Float64 Closure & ERMoE Routing Audits

- Float64 `A5` (`60 × 60`) max `hom_err = 1.48e-14`, `unitary_err = 1.55e-14`, trace invariance `= 8.99e-16`, Galois `Tr(s t) - α` error `= 1.30e-15`
- 25-trial ERMoE convex-gated trace invariance max error `= 1.79e-15`; cross-expert orthogonal SGD max logit drift `= 1.78e-15`

---

## 4. Honest Limitations & Rule 7

1. **Known `A_5` template vs arbitrary black-box discovery:** `icosahedral_ermoe_etf` supplies exact algebraic 3D icosahedral and 4D standard block forms; when no template is supplied, `spectral_alm_gen` still learns `A_5` to `L32_bacc = 0.9917` from spectrum + mixed relation penalty `(U_0 U_1)^5 - I = 0`, though its `hom_err = 0.0225` needs further dual refinement before matching `1e-12` continual subspace rigidity.
2. **Epiplexity feature dependence:** Unsupervised D-optimal selection operates on conjugated unitary trace descriptors `Phi(x)` whose conjugation invariance already factors out nuisance gauge degrees of freedom; raw word-token selection without invariant embeddings would not recover class orbits efficiently.
3. **Rule 7 Gate:** Required post-final-edit checks (`cerp.register check`, `cerp.status --check`, 5/5 core Lean audits `Audit`, `AuditBounds`, `AuditClosure`, `AuditInference`, `AuditTheory`, and `pytest -q`) are recorded verbatim in Commit 2.
