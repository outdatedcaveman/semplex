# Handoff: `gemini/master-principle-hankel` — Non-Commuting FD, Interface vs Hankel Balancing, & Partial-Observation HMMs

**Branch:** `gemini/master-principle-hankel` (cut cleanly from `origin/claude/practical-shannon-oqg60y`)
**Status:** COMPLETE & VERIFIED (Commit 1 pre-registration: `67239f7`).

## 1. Formal Mathlib Verification (`proofs/lean-mathlib/MasterPrincipleHankel.lean`)

Compiled under Lean v4.12.0 (`lake build MasterPrincipleHankel`, `62.70s`) and audited via `proofs/lean-mathlib/AuditMasterPrincipleHankel.lean` (`AUDIT_RC=0`). All 13 theorems depend strictly on `[propext, Classical.choice, Quot.sound]`, zero `sorryAx`:

1. **General Non-Commuting Matrix Fluctuation-Dissipation** (no `[L, W] = 0` assumed):
   - `trace_matG_eq_dirichletFlow`, `trace_mul_matG_eq_moment1`: Exact eigenbasis trace expansions without assuming commutativity `[L, W] = 0`.
   - `matNormDirichlet_hasDerivAt_neg_var`: Exact non-commuting fluctuation-dissipation theorem `d/dλ [Tr(L G(λ)) / Tr(G(λ))] = -Var_λ(L)`.
   - `matNormDirichlet_strictAnti` & `matLambda_unique_of_dirichlet`: Strict monotonicity and unique identifiability of `λ` from empirical roughness `kin_norm`.
2. **Concatenated Interface Gram, Hankel Collapse, and Variational Balancing**:
   - `concat_interface_gram`, `interface_sum_quadForm_eq_zero_iff`: `Φ Φᵀ = W_c + W_o` for `Φ = [Aᵀ | B]`.
   - `hankel_collapse_of_wc_zero`: Formalizes the uniform-prior group action collapse (`W_c = 0 → A = 0 ∧ H = A B = 0 ∧ W_c W_o = 0`, while `W_c + W_o = W_o`).
   - `trace_hankel_eq_trace_wc_wo`, `trace_wc_wo_am_gm`, `variational_nuclear_norm_bound`: Proves `Tr(Hᵀ H) = Tr(W_c W_o)` and `∑_t (Uᵀ H V)_{e(t), g(t)} ≤ (1 / 2) Tr(W_c + W_o)` for all orthogonal frames `U, V`, attaining equality under balanced coordinates `W_c = W_o`.
3. **Contractive Linear Recurrence (`LRU`/`SSM`) Past Decay Law**:
   - `contractive_ssm_lag_weight`, `contractive_ssm_geom_sum`: Exact `(ρ^t)² = (ρ²)ᵗ` and finite-horizon geometric series identity.

## 2. Measured Verdicts (`HHK.1`–`HHK.5`)

Machine artifact: `experiments/results/master_principle_hankel.json` (`64 / 64` runs completed, `505.4s`, max Hankel SVD vs `W_bal` eigval discrepancy `4.72e-16` across all 8 HMMs).

| Hypothesis | Verdict | Exact Quantitative Summary |
|---|---|---|
| **`HHK.1`** | **BROKEN** | Step-0 `16`-draw isotropic LRU: `lru_lo` (`ρ=0.50 -> γ_c=0.25`) matched `W_c(0.25) > W_c(0.7225)` on `12/12` (`mean cos = 0.9405`), whereas `lru_hi` (`ρ=0.85 -> γ_c=0.7225`) matched `W_c(0.7225) > W_c(0.25)` on only `1/12` (`mean cos = 0.7535`); additionally `0/12` linear diagonal LRU runs converged to `fit >= 0.90` on non-abelian monoids (`lo [0.649, 0.844]`, `hi [0.600, 0.838]`). |
| **`HHK.2`** | **NEITHER** | Only `2/4` archs reached `fit >= 0.90` (`gru_mlp` `12/12`, `rnn_mlp` `12/12`; LRUs `0/12`). On BOTH converged archs, **Kubo–Ando geometric mean `W_gm = W_c # W_o` outperformed `W_sum = W_c + W_o` and `W_bal = W_c^{1/2} W_o W_c^{1/2}`**: `gru_mlp` mean/median **`W_gm 0.9199 / 0.9201`** > `W_sum 0.8657 / 0.8571` > `W_bal 0.8138 / 0.8135` > `W_c 0.7787` > `W_o 0.7380` > `W_bal_dual 0.7185` > `o 0.4957`; `rnn_mlp` mean/median **`W_gm 0.8882 / 0.8928`**, `W_c 0.8805 / 0.8973`, `W_bal 0.8749 / 0.8570` > `W_sum 0.7855 / 0.7712`. |
| **`HHK.3`** | **NEITHER** | `9/16` HMM runs satisfied both `kl_gap <= 0.03` AND `belief_r2 >= 0.85` (below `12/16`): **ALL `16/16` achieved near-Bayes prediction (`kl_gap = 0.0001–0.0103`, mean `0.0036` nats)**, splitting sharply by family on *linear* belief readout: `8/8` non-reversible HMMs had `belief_r2 ∈ [0.946, 0.992]` (mean `0.9766`, `kl_gap = 0.00036`), vs `1/8` cyclic-group HMMs (`belief_r2 ∈ [0.577, 0.873]`, mean `0.7380`, `kl_gap = 0.0069`). |
| **`HHK.4`** | **HELD** | On all 8 converged cyclic-group HMMs (`hmm_Z4..Z7`, where `W_c^{action} = 0` identically: `<= 3.4e-32`), **`7/8` runs achieved `> 0.50` cosine for all three observation-conditioned operators `W_sum, W_bal, W_gm` in both history-kernel and state-basis spaces** (`hmm_Z5 rnn_mlp` had `hist W_sum = 0.449`, while `7/8` scored `0.56–0.87` hist and `0.89–0.96` state). Across the 8 strongly non-commuting non-reversible HMMs (`comm ∈ [0.354, 0.639]`, `‖Wc_obs‖/‖Wo_obs‖ = 13×–24×`), **`W_bal_dual` dominated** (`mean hist = 0.8654`, `mean state = 0.8239`) vs `W_o` (`0.8260 / 0.6270`), `W_gm` (`0.7769 / 0.5658`), `W_bal` (`0.7488 / 0.3532`), and unnormalized `W_sum` (`0.7321 / 0.2926`, swamped by `Wc_obs`). |
| **`HHK.5`** | **BROKEN** | Across all `16/16` converged HMM runs (`kl_gap <= 0.03`), while `pca95_dim` (`3–22`) stayed far below `n_distinct_beliefs` (`278–363`) on `16/16`, cyclic-group HMMs expanded nonlinearly to `pca95_dim = 13–22` (`median pca95/(m-1) = 2.5`), whereas non-reversible HMMs stayed compressed at `pca95_dim = 3` (`4/4` `gru_mlp`, `<= m - 1`) and `5–7` (`rnn_mlp`). |

## 3. Key Scientific Takeaways

1. **Operator Selection Depends on Commutator & Past/Future Conditioning Scale:** On deterministic non-commuting monoids (`comm ∈ [0.124, 0.445]`) where `W_c` and `W_o` sit at matched energy scales, the **Kubo–Ando matrix geometric mean `W_gm = W_c # W_o`** beats both `W_sum = W_c + W_o` (`0.920` vs `0.866` on GRU; `0.888` vs `0.786` on RNN) and `W_bal` (`0.814` / `0.875`). On strongly non-reversible partial-observation HMMs where `‖Wc_obs‖` is `13×–24×` larger than `‖Wo_obs‖`, raw additive `W_sum` collapses toward `W_c` (`0.293` state cosine) while **balanced-coordinate pullback `W_bal_dual = W_c^{+1/2} (W_c^{1/2} W_o W_c^{1/2})^{1/2} W_c^{+1/2}`** (`0.865` hist, `0.824` state) best recovers learned structure.
2. **Cyclic vs Non-Reversible HMM Posterior Geometry (Synthesizing Spike 24):** All 16 HMM runs achieve Bayes-optimal next-observation filtering (`<= 0.010` nats), yet linear PCA/belief decoding splits cleanly: non-reversible localized HMMs embed into `m - 1` linear directions (`gru_mlp` `pca95 = 3`, `belief_r2 = 0.977`), while cyclic-group noisy Bayes filtering spreads nonlinear log-likelihood ratios across `13–22` PCA dimensions (`belief_r2 = 0.738`), directly illustrating why linear Hankel rank bounds *linear* realizations rather than nonlinear RNN dimension.
3. **Why Contractive LRU Broke at `ρ = 0.85`:** For slow decay (`ρ = 0.85`) over `T = 16`, transient zero-init truncation (`0.85^4 = 0.522`) plus cross-time word-correlation terms `ρ^{k+j} E[e_{x_{t-k}} e_{x_{t-j}}^T | q]` break the diagonal sum approximation `W_c(ρ²)`, whereas fast decay (`ρ = 0.50`) matches `W_c(0.25)` at `0.941` (`12/12`). Linear diagonal recurrences also lack multiplicative transition gating needed to learn non-abelian automaton multiplication (`fit <= 0.844`).

## 4. Verification Summary

- Mathlib: `lake build MasterPrincipleHankel` (`BUILD_RC=0`, `62.70s`) & `AuditMasterPrincipleHankel.lean` (`AUDIT_RC=0`, `[propext, Classical.choice, Quot.sound]`, `proofs/lean-mathlib/.lake` moved back out of workspace).
- `cerp.register check`, `cerp.status --check`, 5 core Lean audits against clean base `7be5346`, and `pytest -q` run in final Rule-7 verification pass before Commit 2.
