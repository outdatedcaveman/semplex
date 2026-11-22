# Handoff: `gemini/master-principle-hankel` — Non-Commuting FD, Interface vs Hankel Balancing, & Partial-Observation HMMs

**Branch:** `gemini/master-principle-hankel` (cut cleanly from `origin/claude/practical-shannon-oqg60y`)
**Status:** PRE-REGISTERED (Commit 1); training run pending.

## 1. Formal Mathlib Verification (`proofs/lean-mathlib/MasterPrincipleHankel.lean`)

Compiled under Lean v4.12.0 (`lake build MasterPrincipleHankel`, `62.70s`) and audited via `proofs/lean-mathlib/AuditMasterPrincipleHankel.lean` (`AUDIT_RC=0`). All 13 theorems depend strictly on `[propext, Classical.choice, Quot.sound]`, zero `sorryAx`:

1. **General Non-Commuting Matrix Fluctuation-Dissipation** (no `[L, W] = 0` assumed):
   - `trace_matG_eq_dirichletFlow`: Exact eigenbasis trace reduction `Tr(exp(-λ/2 L) W exp(-λ/2 L)) = ∑_i (Uᵀ W U)_{ii} exp(-λ μ_i)`.
   - `trace_mul_matG_eq_moment1`: Exact first-moment identity `Tr(L G(λ)) = ∑_i (Uᵀ W U)_{ii} μ_i exp(-λ μ_i)`.
   - `matNormDirichlet_hasDerivAt_neg_var`: Exact non-commuting fluctuation-dissipation theorem `d/dλ [Tr(L G(λ)) / Tr(G(λ))] = -Var_λ(L)`.
   - `matNormDirichlet_strictAnti` and `matLambda_unique_of_dirichlet`: Strict monotonicity and unique identifiability of `λ` from observed empirical roughness `kin_norm` whenever at least two `L`-eigenmodes with distinct eigenvalues carry positive weight.
2. **Concatenated Interface Gram, Hankel Collapse, and Variational Balancing**:
   - `concat_interface_gram`: Proves `Φ Φᵀ = Aᵀ A + B Bᵀ = W_c + W_o` for the concatenated past-plus-future feature matrix `Φ = [Aᵀ | B]`.
   - `interface_sum_quadForm_eq_zero_iff`: Exact nullspace characterization `vᵀ(W_c + W_o)v = 0 ↔ A v = 0 ∧ Bᵀ v = 0`.
   - `hankel_collapse_of_wc_zero`: Formalizes the uniform-prior group action collapse (`W_c = 0 → A = 0 ∧ H = A B = 0 ∧ W_c W_o = 0`, while `W_c + W_o = W_o` remains non-zero).
   - `trace_hankel_eq_trace_wc_wo`: `Tr(Hᵀ H) = Tr(W_c W_o)`.
   - `trace_wc_wo_am_gm`: `2 Tr(W_c W_o) ≤ Tr(W_c²) + Tr(W_o²)`, with equality iff `W_c = W_o`.
   - `variational_nuclear_norm_bound`: For arbitrary orthogonal frames `U, V` (`U Uᵀ = 1`, `V Vᵀ = 1`) and injective index pairings `(e, g)`, proves `∑_t (Uᵀ H V)_{e(t), g(t)} ≤ (1/2) Tr(W_c + W_o)`, showing `(1/2) Tr(W_c + W_o)` upper-bounds the Hankel nuclear norm `‖H‖_*` and attains equality under balanced coordinates `W_c = W_o`.
3. **Contractive Linear Recurrence (`LRU`/`SSM`) Past Decay Law**:
   - `contractive_ssm_lag_weight`, `contractive_ssm_geom_sum`: Exact `(ρ^t)² = (ρ²)^t` and finite-horizon geometric series identity deriving `γ_c = ρ²` from first principles.

## 2. Pre-Registered Empirical Design (`experiments/master_principle_hankel.py`)

Pre-registered predictions saved in `experiments/results/master_principle_hankel_predictions.json` (committed BEFORE executing `run`):

- **Arm 1 — 12 Fresh Strongly Non-Commuting Monoids (`NCM_00`..`NCM_11`, `seed = 2026112201`, `415/500` qualified):**
  - Selected for strong non-commutativity `comm_ratio ∈ [0.124, 0.445]`, nontrivial discrimination from instantaneous `o` (`cos < 0.90`), and maximal operator separation `1 - min(cos(G_sum, G_bal), cos(G_sum, G_gm)) ∈ [0.173, 0.287]`.
  - Architectures (`4 × 12 = 48` runs, `steps = 1200`): `gru_mlp`, `rnn_mlp`, `lru_lo_mlp` (`ρ = 0.50`, `γ_c = 0.25`), `lru_hi_mlp` (`ρ = 0.85`, `γ_c = 0.7225`).
  - Candidate operators evaluated fairly at each operator's exact FD zero-cosine `λ_kin`: `W_sum = W_c + W_o`, `W_bal = W_c^{1/2} W_o W_c^{1/2}`, `W_gm = W_c # W_o`, `W_bal_dual = W_c^{+1/2} W_bal^{1/2} W_c^{+1/2}`, `W_c`, `W_o`, and `o`.
- **Arm 2 — 8 Fresh Partially-Observed Controlled HMMs (`2 × 8 = 16` runs, `steps = 1500`):**
  - 4 reversible cyclic-group HMMs (`hmm_Z4`..`hmm_Z7`) with `W_c^{action} = 0` identically, plus 4 non-reversible strongly non-commuting controlled HMMs (`hmm_nr_0`..`hmm_nr_3`, `comm_ratio ∈ [0.354, 0.639]`).
  - Verified exact Hankel factorization `H = R_feat @ O_feat` and `eigvals(W_bal) = s(H)²` to `max_hankel_err = 4.72e-16`.

## 3. Pre-Registered Verdict Rules (`HHK.1`–`HHK.5`)

- **`HHK.1` (Contractive SSM `γ_c = ρ²`):** Step-0 `16`-draw isotropic Gram of `lru_lo` (`ρ=0.50`) matches `W_c(0.25) > W_c(0.7225)` on `>= 10/12` monoids, `lru_hi` (`ρ=0.85`) matches `W_c(0.7225) > W_c(0.25)` on `>= 10/12` monoids (`mean cos >= 0.90`), and among converged pairs (`>= 6`), post-training optimal `γ_c^*` is strictly higher for `lru_hi_mlp` than `lru_lo_mlp` in `>= 75%`.
- **`HHK.2` (Non-Commuting Operator Showdown):** `W_sum` is `HELD` if it beats all 6 rivals on both mean and median `cos_G` at matched `λ_kin` in `>= 3/4` qualifying (`n >= 6`, `fit >= 0.90`) architectures; `BROKEN` if `W_bal` or `W_gm` beats `W_sum` on mean and median in `>= 3/4` architectures; otherwise `NEITHER`.
- **`HHK.3` (Partial-Observation Bayes Filtering):** `HELD` if `>= 12/16` HMM runs achieve `kl_gap <= 0.03` nats and held-out linear belief decoding `belief_r2 >= 0.85`.
- **`HHK.4` (Reversible-Group HMM Observation Recovery):** Among converged cyclic-group HMM runs (`kl_gap <= 0.05`, requiring `>= 6`), `HELD` if observation-derived `W_sum`, `W_bal`, and `W_gm` all achieve `> 0.50` cosine in both held-out history-kernel and state-basis space on `>= len-1` (and `>= 6`) runs (whereas `W_c^{action} = 0` identically).
- **`HHK.5` (Hankel Rank Compression vs Distinct Belief Quotient):** Across converged HMM runs (`kl_gap <= 0.03`, `>= 10`), `HELD` if `pca95_dim <= m + 1` and `pca95_dim < n_distinct_beliefs` on every converged run.
