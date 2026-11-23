# Handoff: Exact Semidirect Generator Locking, Orthogonal Bias-Free Retention, Stochastic Interventional DPI, & Variational MDL Closure (`gemini/master-principle-closure`)

**Status:** `[PRE-REGISTERED — PENDING SMOKE, 39-RUN EXECUTION & RULE 7]`  
**Branch:** `gemini/master-principle-closure` (base `origin/claude/practical-shannon-oqg60y` @ `7be5346`)  
**Scope:** Closes the two residual gaps from `gemini/master-principle-lie-lyapunov` (`ee14372`): (1) replacing soft mixed-word relation penalties (`0.0178` `A4` homomorphism drift) with exact semidirect-product generator locking (`S_3 = C_3 ⋊ C_2`, `A_4 = V_4 ⋊ C_3`) plus comparing Augmented-Lagrangian (`spectral_alm_gen`) dynamic constraint enforcement, (2) eliminating Phase-2 catastrophic forgetting via Phase-1 whitened bias-free SGD (`semidirect_exact_etf`, zero replay, zero kept-label access), and (3) unifying stochastic channel TV data-processing bounds (`StochasticInterventionalDPI`) with variational MDL parameter compression (`2d < |G|d`).

---

## 1. Prior Art vs. Semplex Synthesis

- **Prior Art:** Semidirect group presentations (`C_3 ⋊ C_2`, `V_4 ⋊ C_3`), neural feature whitening / orthogonal gradient updates, total-variation data-processing inequality (`tvDist`), and amortized optimization (`arXiv:2202.00665`, `arXiv:2605.10878`, `arXiv:2611.10501`) are established building blocks.
- **Semplex Contribution:** Unifies all five pillars in `34/34` audited Mathlib `v4.12.0` theorems (`MasterPrincipleClosure.lean`, `CLOSURE_BUILD_RC=0` `284.74s`, `CLOSURE_AUDIT_RC=0` `76.46s`, strictly standard axioms, `0 sorryAx`) and tests them in a pre-registered 39-run campaign pushing OOD group composition to `A4 L = 32` (`8x` training length) and `S3 L = 16`, Phase-2 orthogonal retention, and noisy POMDP active-vs-passive intervention separation.

---

## 2. Pre-Registered Hypotheses (`HMC.1`–`HMC.5`)

Pre-registered in `experiments/results/master_principle_closure_predictions.json` (`27` Arm-1 neural runs + `12` Arm-2 stochastic POMDP runs + Arm-3 float64 closure audits).
