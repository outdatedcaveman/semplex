# Handoff: Exact Variational Geodesic Master Principle & Arbitrary Finite-Group Gauge Realization (`gemini/master-principle-variational`)

**Status:** `[PRE-REGISTERED COMMIT 1 — PENDING EMPIRICAL RUN]`  
**Branch:** `gemini/master-principle-variational` (local in isolated worktree; base `origin/claude/practical-shannon-oqg60y` @ `7be5346`)  
**Complementary Coordination:** Closes ChatGPT's Spike 25/26/27 §Next open formal & neural obligations in an isolated scratch worktree without duplicating canonical runs or altering the canonical checkout.

---

## 1. The Variational Resolution of Spike 26 §10.4 (`W_c + W_o` vs `X*(lam)`)

In Spike 26 (`S_3` gauge-ring controlled HMM), ChatGPT rightly noted that while the balanced realization Gramian $W_c^{1/2} W_o W_c^{1/2}$ captures the squared singular spectrum of $H = R O$, neither $W_c + W_o$ nor its ad-hoc two-sided heat sandwich $e^{-\lambda L_{\mathrm{kin}}/2}(W_c + W_o)e^{-\lambda L_{\mathrm{kin}}/2}$ had been derived from first principles—and empirically on centered Spike 26 matrices, $\mathrm{rank}(W_{c,\perp} + W_{o,\perp}) = (1, 2, 2)$ across $(B=2,\eta=1/6), (B=3,\eta=1/6), (B=3,\eta=1/3)$, falsely retaining unobservable modes where $\mathrm{rank}(H_c) = (0, 2, 0)$.

Consider an internal state representation $H_{\mathrm{state}}$ with state-centroid metric $X = H_{\mathrm{state}} H_{\mathrm{state}}^\top > 0$ factoring past-history features into future responses, plus physical step kinetic cost $\lambda \operatorname{Tr}(L_{\mathrm{kin}} X)$:
$$\mathcal{J}_\lambda(X) \;=\; \operatorname{Tr}\!\big((A + \lambda L_{\mathrm{kin}})\, X\big) + \operatorname{Tr}\!\big(B X^{-1}\big)$$
- **Global Minimum & Unique Riccati Solution (Arbitrary Non-Commuting SPD $A, B$):** By Frobenius square completion $\|R_A R_X^\top - U^\top R_B R_X^{-1}\|_F^2 \ge 0$, $\inf_{X > 0} \mathcal{J}_\lambda(X) = 2\operatorname{Tr}\!\big(((A + \lambda L_{\mathrm{kin}})^{1/2} B (A + \lambda L_{\mathrm{kin}})^{1/2})^{1/2}\big)$, uniquely attained by solving $X (A + \lambda L_{\mathrm{kin}}) X = B$:
  $$X^*(\lambda) \;=\; (A + \lambda L_{\mathrm{kin}})^{-1} \,\#\, B$$
- **Exact Unification of Empirical Regimes:**
  1. **Dual Belief Coordinates ($A = W_c$, $B = W_o$):** Encoder $\|R E\|_F^2 = \operatorname{Tr}(W_c X)$, decoder $\|E^{-1} O\|_F^2 = \operatorname{Tr}(W_o X^{-1})$. At $\lambda = 0$, $X^*_{\mathrm{dual}}(0) = W_c^{-1} \,\#\, W_o$ (exact `W_bal_dual`), which transforms $GL(m)$-covariantly ($X' = S X S^\top$) and lifts via $R$ to $(R X^*_{\mathrm{dual}}(0) R^\top)^2 = H H^\top$, recovering the exact Hankel realization $(H H^\top)^{1/2}$ with $\operatorname{Tr} = \|H\|_*$ and exact zero collapse when $H = 0$.
  2. **Primal State-Feature Coordinates ($A = W_c^{-1}$, $B = W_o$):** At $\lambda = 0$, $X^*_{\mathrm{primal}}(0) = W_c \,\#\, W_o$ (exact Kubo–Ando geometric mean `W_gm` that outperformed `W_sum` and `W_bal` on monoids in `HHK.2`).
- **Variational Fluctuation-Dissipation Theorem:** Raising $\lambda_1 < \lambda_2$ strictly decreases kinetic energy $\operatorname{Tr}(L_{\mathrm{kin}} X^*(\lambda_2)) \le \operatorname{Tr}(L_{\mathrm{kin}} X^*(\lambda_1))$ and preserves concavity of $\Phi(\lambda) = \inf_X \mathcal{J}_\lambda(X)$.

*Prior-Art Honesty:* The operator geometric mean `#` on positive cones is classical (Pusz–Woronowicz 1975; Kubo–Ando 1980), variational nuclear-norm trace infima are standard (Srebro et al. 2005), and unweighted balancing originates with Moore 1981. What is project-specific is deriving $X^*(\lambda) = (A + \lambda L_{\mathrm{kin}})^{-1} \# B$ from the Semplex encoder/decoder + kinetic Lagrangian to replace the ad-hoc additive heat sandwich, proving the non-commuting SPD/polar/GL(m)/Hankel-support package in Lean 4/Mathlib, and testing all regimes on controlled gauge rings and non-commuting dynamical systems.

---

## 2. Mathlib v4.12.0 Formalization Record (`BUILD_RC=0`, `0` warnings)

Both isolated modules in `proofs/lean-mathlib/` compiled cleanly (`66.33s`) and passed strict axiom audits (`AUDIT_VAR_RC=0`, `AUDIT_GAUGE_RC=0`), depending strictly on `[propext, Classical.choice, Quot.sound]` with zero `sorryAx`:

- **`MasterPrincipleVariational.lean` (`26/26` audited theorems):**
  `frobNormSq_eq_sum_sq`, `frobNormSq_nonneg`, `frobNormSq_eq_zero_iff`, `variational_trace_identity`, `variational_trace_lower_bound`, `variational_trace_eq_iff_factor`, `variational_eq_implies_riccati` (`X A X = B`), `variational_minimizer_unique`, `riccati_geodesic_attains_bound`, `hankel_induced_history_gram_sq` (`(R X R^T)^2 = H H^T`), `gl_covariant_riccati_and_history_invariance`, `dual_and_primal_enc_dec_costs`, `variational_kinetic_antitone`, `variational_kinetic_strictAnti`, `variational_envelope_sandwich`, `variational_envelope_concave`, `posDef_congruence`, `riccati_geodesic_posDef`, `exists_posDef_sqrt`, `exists_posDef_sqrt_and_polar` (full spectral + polar construction directly from `A.PosDef, B.PosDef`), `hankel_support_reduction` (singular `r`-dim minimal realization), `hankel_zero_collapse`, `weighted_hankel_induced_history_gram_sq` (policy/test weights), `posDef_add_smul_posSemidef`, `matrix_variational_kinetic_antitone`, `matrix_variational_kinetic_strictAnti`.
- **`MasterPrincipleGauge.lean` (`16/16` audited theorems):**
  `pathProd_gaugeAct`, `wilsonLoop_gauge_covariant`, `gaugeAct_mul`, `gaugeAct_one`, `gaugeHomEquiv` (full faithfulness `{g // g • A = A'} ≃ {k // k H(A) k^{-1} = H(A')}` for arbitrary group `G` and ring length `L+1`), `gaugeStabilizer_bijective_centralizer`, `gaugeOrbit_iff_isConj`, `gaugeOrbit_card_eq` (`|G|^L * |[H(A)]|`), `classKernelLift_nonneg`, `classKernelLift_conj_equivariant`, `classKernelLift_row_stochastic`, `symChannel_row_sum`, `symChannel_vecMul_centered`, `symChannel_uniform_erasure`, `symChannel_separates_simplex_iff` (full stochastic `[0, 1/(n-1)]` iff `eta != 1/n`), `twoLoop_s3_simultaneous_conj_counterexample`.

---

## 3. Pre-Registered Falsifiers (`HVR.1`–`HVR.6`, `100` Empirical Runs)

1. **`HVR.1` (Primal Variational `X_primal_var` vs Heat-Sandwiches on 12 Fresh Monoids × 4 Archs = 48 runs):**
   - `HELD` if `X_primal_var(lam_var)` beats BOTH `G_sum_heat(lam_heat)` and `G_gm_heat(lam_heat)` in mean AND median cosine similarity by `>= +0.01` on `>= 3/4` converged architectures (`fit >= 0.90`); `BROKEN` if either heat sandwich beats `X_primal_var` in mean & median on `>= 3/4` archs; else `NEITHER`.
2. **`HVR.2` (Dual Variational `X_dual_var` vs Heat-Sandwiches on 8 Fresh HMMs × 2 Archs = 16 runs):**
   - `HELD` if `X_dual_var(lam_var)` beats `G_sum_heat`, `G_gm_heat`, and `W_sum` simultaneously in BOTH history-kernel and state spaces on `>= 12/16` converged runs (`kl_gap <= 0.05`); `BROKEN` if heat dominates in both spaces on `>= 12/16` runs; else `NEITHER`.
3. **`HVR.3` (Variational Causal Shift Under `leaky_a025` & `vel_warmup` Interventions, Arm 1A + 1B):**
   - `HELD` if reducing step velocity lowers `kin_norm` and raises `lam_var` on `>= 75%` of converged pairs AND moves `G_net(intervened)` strictly closer to `X_var(lam_intervened)` than `X_var(lam_base)` on `>= 75%` (`n >= 16`); `BROKEN` if `<= 25%`; else `NEITHER`.
4. **`HVR.4` (Matched-Capacity `~16k ± 5%` Non-Abelian Gauge-Ring Separation, `Z_3, S_3, D_4`, `L_train ∈ {3, 4}` -> held-out `L=4` & OOD `L=5`, 24 runs):**
   - `HELD` if all 3 hold: (i) `local_edge_mlp` stays near chance (`<= 0.45` `Z_3`/`S_3`, `<= 0.35` `D_4`); (ii) `multiset_deepsets` clears `bacc >= 0.90` on `Z_3` held-out `L=4`, YET scores exact `collision_pair_sep = 0.000` on non-Abelian `S_3` & `D_4` collision pairs with `ordered_gru` clearing `collision_pair_sep >= 0.70` and beating `multiset_deepsets` in `bacc_L4` by `> +0.05` on both; (iii) `ordered_gru` achieves `bacc >= 0.85` on all 3 at held-out `L=4` and `>= 0.80` on OOD `L=5`. `BROKEN` if `multiset_deepsets` beats `0.0` collision separation or matches `ordered_gru` within `0.02` on `S_3` & `D_4`, or `ordered_gru` fails `Z_3` held-out (`< 0.85`); else `NEITHER`.
5. **`HVR.5` (Gauge-Orbit Variance Collapse in Non-Abelian Learned Compositional Models, 24 runs):**
   - `HELD` if `within_orbit_var / total_var <= 0.15` in penultimate representation (`pen`) on both `S_3` and `D_4` for `>= 1` converged compositional model AND `<= 0.25` for `ordered_gru` `pen`; `BROKEN` if `> 0.50` for `ordered_gru`; else `NEITHER`.
6. **`HVR.6` (Dynamic Controlled `S_3` & `D_4` Gauge-Ring POMDP Full-Abstraction Phase Transition, 12 runs):**
   - `HELD` if in `(B=3, eta_inf)` trained GRUs hit `kl_gap <= 0.03` and `belief_r2 >= 0.85` on both `S_3` and `D_4`, while unobservable regimes `(B=2, eta_inf)` and `(B=3, eta_unif)` achieve `kl_gap <= 0.03` AND collapse predictive state variance (`var_ratio <= 0.25` or `eff_rank <= 0.5 * eff_rank_full` or `belief_r2 <= 0.30`); `BROKEN` if `(B=3, eta_inf)` fails `belief_r2 >= 0.60`; else `NEITHER`.

---

## 4. Measured Verdicts & Results

**Verdict Table:** `[PENDING RUN]`

| Hypothesis | Verdict | Summary Measurement |
|---|---|---|
| `HVR.1` | `[PENDING RUN]` | — |
| `HVR.2` | `[PENDING RUN]` | — |
| `HVR.3` | `[PENDING RUN]` | — |
| `HVR.4` | `[PENDING RUN]` | — |
| `HVR.5` | `[PENDING RUN]` | — |
| `HVR.6` | `[PENDING RUN]` | — |

---

## 5. Rule 7 Verification Ledger

- `python -m cerp.register check`: `[PENDING RUN]`
- `python -m cerp.status --check`: `[PENDING RUN]`
- Core Lean audits (`Audit*.lean`): `[PENDING RUN]`
- Full `pytest -q`: `[PENDING RUN]`
