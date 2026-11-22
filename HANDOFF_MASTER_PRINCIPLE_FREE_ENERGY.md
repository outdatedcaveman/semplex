# Handoff: Exponential Heat-Filtered Kubo–Ando vs Matrix-KL Free-Energy Master Principle & Bidirectional/Multi-Loop Gauge Classification (`gemini/master-principle-free-energy`)

**Status:** `[PRE-REGISTERED — EXPERIMENT PENDING FULL 92-RUN EXECUTION]`  
**Branch:** `gemini/master-principle-free-energy` (base `origin/claude/practical-shannon-oqg60y` @ `7be5346`)  
**Complementary Coordination:** Advances the Master Principle discovery from `gemini/master-principle-variational` (where exponential `G_gm_heat(lam)` refuted algebraic `X_primal_var(lam)` across 4/4 architectures) while closing all formal graph-gauge & non-ambivalent/multi-loop obligations identified in our Task 141 audits without modifying the canonical checkout.

---

## 1. Theoretical Motivation & Prior-Art Boundaries

In `gemini/master-principle-variational`, pre-registered runs (`HVR.1 = BROKEN`, `HVR.3 = BROKEN`) empirically **refuted** the algebraic ridge $(W_c^{-1} + \lambda L_{\mathrm{kin}})^{-1} \,\#\, W_o$ in favor of the exponentially damped geometric mean:
$$G_{\mathrm{gm\_heat}}(\lambda) \;=\; e^{-\lambda L_{\mathrm{kin}}/2}\,\big(W_c \,\#\, W_o\big)\,e^{-\lambda L_{\mathrm{kin}}/2}.$$
Two competing non-commuting first-principles derivations generate the exponential factor:
1. **Heat-Filtered Kubo–Ando Principle ($G_{\mathrm{gm\_heat}}(\lambda)$):** Applying heat smoothing $E_\lambda = e^{-\lambda L_{\mathrm{kin}}/2}$ symmetrically to the causal controllability/observability Gramians ($W_c(\lambda) = E_\lambda W_c E_\lambda$, $W_o(\lambda) = E_\lambda W_o E_\lambda$) preserves the exact Kubo–Ando geodesic midpoint $W_c(\lambda) \,\#\, W_o(\lambda) = E_\lambda (W_c \# W_o) E_\lambda$.
2. **Quantum Relative-Entropy / Matrix-KL Free Energy ($X_{\mathrm{kl\_gm}}(\lambda)$):** Minimizing the Umegaki relative-entropy free energy $D_{\mathrm{KL}}(X \,\|\, G_0) + \lambda \operatorname{Tr}(L_{\mathrm{kin}} X)$ (by Klein's inequality) yields the unique global minimizer $X_{\mathrm{kl\_gm}}(\lambda) = \exp(\log G_0 - \lambda L_{\mathrm{kin}})$. Whenever $[G_0, L_{\mathrm{kin}}] = 0$, $X_{\mathrm{kl\_gm}}(\lambda) = G_{\mathrm{gm\_heat}}(\lambda)$ identically; when $[G_0, L_{\mathrm{kin}}] \neq 0$, their Baker–Campbell–Hausdorff divergence tests which physical variational principle governs neural representations!

Simultaneously, on the gauge-symmetry frontier, we extend cycle-only formalizations to **arbitrary oriented graphs** (fixing forward-only `EdgeWalk` and backtracking traps via acyclic depth recursion), **non-ambivalent groups (`A_4`)** requiring complex unitary $U(d)$ phases over real/palindromic character probes, and **$b_1 = 2$ two-loop `S_3` bouquets** requiring deferred joint base-frame quotienting.

---

## 2. Mathlib v4.12.0 Formalization (`45/45` Theorems, Standard Axioms Only)

Isolated in `proofs/lean-mathlib/` (`MasterPrincipleFreeEnergy.lean` `31/31`, `MasterPrincipleBouquet.lean` `14/14`):

- **`MasterPrincipleFreeEnergy.lean` (`31` audited theorems):**
  - Basis-independent spectral functional calculus (`spectral_apply_eq_of_eq`), symmetric `symmExp`/`symmLog` inverse pair (`symmExp_symmLog`, `symmLog_symmExp`), SPD square-root uniqueness (`posDef_sq_eq_iff`), semigroup laws (`heatOp_add`, `heatOp_mul_neg`).
  - **Heat-Filtered Kubo–Ando Variational Theorem (`heat_filtered_kubo_ando_riccati`):** $G_{\mathrm{gm\_heat}}(\lambda)$ is strictly SPD and the unique global minimizer of $\operatorname{Tr}(W_c(\lambda)^{-1} X) + \operatorname{Tr}(W_o(\lambda) X^{-1})$.
  - **Exponential Fluctuation–Dissipation & Log-Partition Convexity:** `gm_heat_raw_kinetic_antitone`, `gm_heat_raw_kinetic_strictAnti`, `gm_heat_norm_kinetic_antitone`, `gm_heat_norm_kinetic_strictAnti`, `gm_heat_partition_midpoint_log_convex`.
  - **Quantum Relative-Entropy Free Energy:** `kl_scalar_nonneg`, `kl_scalar_eq_zero_iff`, **Klein's Inequality (`klein_inequality_nonneg`, `klein_inequality_eq_iff`)**, `kl_free_energy_identity`, global unique minimizer `kl_free_energy_unique_minimizer`, `kl_free_energy_kinetic_antitone`, `kl_free_energy_kinetic_strictAnti`, `kl_free_energy_trace_convex`, and commuting limit coincidence `commuting_kl_eq_gm_heat`.
- **`MasterPrincipleBouquet.lean` (`14` audited theorems):**
  - Disjointly partitioned `OrientedGraph`, bidirectional `SignedWalk` (`fwd`/`bwd`) with `signedTransport_gauge_covariant`, depth-ranked `AcyclicSpanningTree` with well-founded `treeFrame`, automatic bidirectional `treeFrame_edge_recursion`, `spanningTree_gaugeHomEquiv` (full faithfulness), `spanningTree_autEquiv_commonCentralizer`, and `spanningTree_chordRep_essential_surj`.
  - Arbitrary $b$-loop `(L+1)`-edge bouquet full faithfulness (`bouquet_homEquiv`), explicit proof of non-ambivalence of $A_4$ (`a4_non_ambivalent`), and both `S_3` two-loop simultaneous-conjugacy split pairs (`s3_bouquet_both_split_pairs`).

---

## 3. Pre-Registered Empirical Protocol (`92` Runs across 4 Arms)

1. **Arm 1A (`48` runs):** `12` fresh non-commuting monoids (`NCM_FE00..11`) $\times$ `4` archs (`gru_mlp`, `rnn_mlp`, `leaky_a025`, `vel_warmup`) comparing `G_gm_heat`, `X_kl_gm`, `G_sum_heat`, `X_kl_sum`, `X_primal_var` under $K_{\mathrm{norm}}$-matched $\lambda$, LOOCV $\lambda$, and 41-point oracle grid, plus exact Riccati, Golden–Thompson gap, monotonicity, and convexity audits.
2. **Arm 1B (`16` runs):** `8` HMMs (`4` cyclic + `4` non-reversible) $\times$ `2` archs (`gru_mlp`, `vel_warmup`) testing dual exponential `G_dual_heat`/`X_kl_dual` vs `W_bal_dual` and primal `G_gm_heat`/`X_kl_gm`.
3. **Arm 2A (`16` runs):** Class-balanced `D_4` & non-ambivalent `A_4` gauge rings (`L_train in {3,4}`, held-out `L=4`, OOD `L=5,6`, `16k +- 5%` params) testing `multiset_deepsets`, `palindromic_gru` (ambivalent real-character proxy), `ordered_gru`, and Complex Unitary `cayley_unitary_equivariant` ($U(d)$, $M(e)=I$).
4. **Arm 2B (`12` runs):** $b_1 = 2$ `S_3` two-loop bouquet (`11` simultaneous orbits vs `9` per-loop pairs, `L=3`/loop train/held-out + OOD `L=4`/loop, `16k +- 5%` params) testing `multiset_deepsets`, `per_loop_gauge_pooled_gru`, `joint_bouquet_gru` (tracking deferred mid-vs-penultimate base-frame collapse), and `cayley_unitary_bouquet`.

---

## 4. Measured Verdicts (`[PENDING EXECUTION]`)

*(Populated automatically after the 92-run empirical showdown completes.)*

---

## 5. Rule 7 Verification Ledger (`[PRE-COMMIT 1 — MATHLIB AUDITED]`)

- Isolated Mathlib build (`MasterPrincipleFreeEnergy`, `MasterPrincipleBouquet`): pending final ledger update post-run.
- Protected paths (`claims/LEDGER.md`, `claims/LEDGER_CHECK.md`, `proofs/lean/*`, `cerp/*`, `tests/*`): untouched.
