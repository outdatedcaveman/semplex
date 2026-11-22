# Handoff: Exponential Heat-Filtered Kubo–Ando vs Matrix-KL Free-Energy Master Principle & Bidirectional/Multi-Loop Gauge Classification (`gemini/master-principle-free-energy`)

**Status:** `[COMPLETE & RULE-7 VERIFIED — LOCAL BRANCH ONLY, NO PUSH]`  
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

## 4. Measured Verdicts & Empirical Results (`92/92` Runs in `1578.2s`)

| Hypothesis | Verdict | Summary Measurement |
|---|---|---|
| `HFE.1` | **`NEITHER`** | At `K_norm`-matched `lam`, **`G_gm_heat`** held a narrow `~0.004–0.006` edge over **`X_kl_gm`** across `4/4` archs (`0.876, 0.832, 0.769, 0.827` vs `0.872, 0.827, 0.764, 0.821`); BOTH decisively beat `G_sum_heat` (`0.868, 0.792, 0.721, 0.802`) and algebraic `X_primal_var` (`0.824, 0.734, 0.568, 0.686`). Under strict **leave-one-monoid-out CV (`loocv`)**, **`X_kl_gm`** edged out `G_gm_heat` on `gru_mlp` (`0.8505` vs `0.8490`) & `vel_warmup` (`0.7906` vs `0.7891`). |
| `HFE.2` | **`BROKEN`** | Only `2/16` HMM runs saw dual exponential (`G_dual_heat`/`X_kl_dual`) beat both `W_bal_dual` and primal `G_gm_heat` on BOTH state & hist: on `gru_mlp`, `G_gm_heat` led state (`0.815` vs `0.774`), while on `vel_warmup` `nonrev_hmm` `G_dual_heat` led state (`0.497` vs `0.263`), though `vel_warmup` again collapsed HMM hist-kernel `cos` (`0.009`). |
| `HFE.3` | **`HELD`** | Both transitions passed ALL 6 thresholds: `rnn_mlp -> leaky_a025` dropped `kin_norm` on `9/12` (`mean dk = -0.0721`) and raised `lam(G_gm_heat)` `9/12` (`1.68 -> 2.90`) and `lam(X_kl_gm)` `9/12` (`1.77 -> 3.19`); `rnn_mlp -> vel_warmup` shifted **`12/12` (`mean dk = -0.0544`, `lam(G_gm_heat)` `1.68 -> 2.45`, `lam(X_kl_gm)` `1.77 -> 2.63`)**. |
| `HFE.4` | **`NEITHER`** | Class-balanced training completely unlocked `D_4` (`palindromic_gru` `0.996` `bacc` & `0.969` OOD `L=6`; `cayley_unitary` `0.997` `bacc` & **`1.000` coll sep**). On non-ambivalent `A_4`, **`palindromic_gru` collapsed to `0.000` chiral separation** (`C3+ vs C3-`), while **`cayley_unitary_equivariant` ($U(d)$) hit `0.897` `L=4 bacc`, `1.000` chiral sep, `0.797` coll sep, `0.691` OOD `L=5` (`0.009` shy of `0.70`), and `0.534` OOD `L=6`**. |
| `HFE.5` | **`HELD`** | On the $b_1 = 2$ `S_3` bouquet (`11` joint orbits vs `9` per-loop pairs), **`per_loop_gauge_pooled_gru` hit EXACT `0.000` on BOTH split pairs** (`0.806` `bacc` vs Bayes `0.818`); **`cayley_unitary_bouquet` achieved `0.99995` held-out `bacc` & `1.000` on BOTH split pairs** (`unitary_err = 7.15e-7`); and **`joint_bouquet_gru`** exhibited **deferred base-frame collapse**, preserving `0.954` within-`[H_1]` variance after loop 1 before collapsing to `0.181` penultimate (`drop = 0.773`). |
| `HFE.6` | **`BROKEN`** | All `12/12` monoids passed `gm_raw_mono`, `gm_norm_mono`, `gm_log_convex`, `kl_raw_mono`, `kl_trace_convex`, strict Golden–Thompson gaps (`gt_min_gap = -1.33e-15`, `gt_gap_lam1 >= 6.32e-4`), and all `U(d)` layers kept `max_unitary_err = 7.15e-7 < 1e-5`. **HOWEVER**, explicit congruence Riccati check `||G_lam A_lam G_lam - B_lam|| / ||B_lam||` failed our `< 1e-8` uniform threshold at extreme `lam = 50.0` (`max = 1.95e+8`, `med = 1.47e+2`) due to float64 condition-number overflow ($e^{\pm 25 \mu_{\max}} \sim 10^{13}$), even while holding at **`med <= 5.46e-15` (`max <= 5.35e-12`) for `lam <= 4.0`** and **`med = 6.10e-12` (`max = 2.72e-8`) at `lam = 15.0`**. |

### Arm 1A Summary (`12` Non-Commuting Monoids, `mean / loocv / oracle_best`)

| Arch | `fit >= 0.90` | `G_gm_heat` | `X_kl_gm` | `G_sum_heat` | `X_kl_sum` | `X_primal_var` | `W_gm` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `gru_mlp` | `12/12` | `0.876 / 0.849 / 0.880` | `0.872 / 0.850 / 0.875` | `0.868 / 0.838 / 0.878` | `0.867 / 0.840 / 0.877` | `0.824 / 0.821 / 0.841` | `0.829` |
| `rnn_mlp` | `12/12` | `0.832 / 0.801 / 0.843` | `0.827 / 0.797 / 0.839` | `0.792 / 0.757 / 0.816` | `0.789 / 0.754 / 0.814` | `0.734 / 0.749 / 0.757` | `0.755` |
| `leaky_a025` | `10/12` | `0.769 / 0.680 / 0.803` | `0.764 / 0.677 / 0.797` | `0.721 / 0.581 / 0.780` | `0.722 / 0.555 / 0.776` | `0.568 / 0.594 / 0.611` | `0.605` |
| `vel_warmup` | `12/12` | `0.827 / 0.789 / 0.847` | `0.821 / 0.791 / 0.842` | `0.802 / 0.765 / 0.838` | `0.796 / 0.760 / 0.833` | `0.686 / 0.648 / 0.704` | `0.686` |

### Arm 2A Summary (`D_4` Class-Balanced & Non-Ambivalent `A_4`, `16k +- 0.4%` params)

| Group | Model | Params | `L=4` `bacc` (`acc`) | `L=5` OOD `bacc` | `L=6` OOD `bacc` | Coll Sep | Chiral Sep (`C3+ vs C3-`) | `within_orbit` (`raw -> pen`) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `D4` | `multiset_deepsets` | `16,047` | `0.349` (`0.367`) | `0.086` | `0.165` | `0.000` | — | `1.000 -> 0.667` |
| `D4` | **`palindromic_gru`** | `15,957` | `0.996` (`0.998`) | **`0.985`** | **`0.969`** | `0.988` | — | `0.430 -> 0.035` |
| `D4` | `ordered_gru` | `15,957` | `0.748` (`0.732`) | `0.651` | `0.435` | `0.756` | — | `0.824 -> 0.164` |
| `D4` | **`cayley_unitary`** | `16,001` | **`0.997`** (`0.997`) | `0.764` | `0.509` | **`1.000`** | — | `0.751 -> 0.100` |
| `A4` | `multiset_deepsets` | `16,053` | `0.630` (`0.669`) | `0.323` | `0.197` | `0.000` | `0.617` | `1.000 -> 0.776` |
| `A4` | `palindromic_gru` | `16,060` | `0.539` (`0.533`) | `0.343` | `0.297` | `0.773` | **`0.000`** | `0.961 -> 0.210` |
| `A4` | `ordered_gru` | `16,060` | `0.795` (`0.906`) | `0.574` | `0.339` | `0.758` | **`1.000`** | `0.908 -> 0.129` |
| `A4` | **`cayley_unitary`** | `16,036` | **`0.897`** (`0.940`) | **`0.691`** | **`0.534`** | **`0.797`** | **`1.000`** | `0.800 -> 0.146` |

### Arm 2B Summary ($b_1 = 2$ `S_3` Two-Loop Bouquet, `11` Joint Orbits vs `9` Per-Loop Pairs)

| Model | Params | Held `bacc` (`acc`) | `L=4`/loop OOD `bacc` | `tau_split` Sep | `cyc_split` Sep | `mid_[H1]` | `raw -> pen` |
|---|---:|---:|---:|---:|---:|---:|---:|
| `multiset_deepsets` | `16,047` | `0.083` (`0.066`) | `0.096` | `0.000` | `0.000` | — | `0.999 -> 0.999` |
| `per_loop_gauge_pooled_gru` | `15,899` | `0.806` (`0.806`) | `0.241` | **`0.000`** | **`0.000`** | — | `0.600 -> 0.006` |
| `joint_bouquet_gru` | `15,975` | `0.790` (`0.803`) | `0.078` | `0.701` | `0.625` | **`0.954`** | `0.713 -> 0.181` |
| **`cayley_unitary_bouquet`** | `15,923` | **`1.000`** (`0.9999`) | **`0.381`** | **`1.000`** | **`1.000`** | — | `0.876 -> 0.079` |

---

## 5. Rule 7 Verification Ledger

- `python -m cerp.register check`: `exit=0` (`0 problem(s), 46 status note(s)`).
- `python -m cerp.status --check`: `exit=0`.
- Core Lean audits (`Audit.lean`, `AuditBounds.lean`, `AuditClosure.lean`, `AuditInference.lean`, `AuditTheory.lean` against base `7be5346` `.olean`s): `exit=0`, `CORE_AUDIT_FAILS=0`, `LEFTOVER_OLEANS=0`.
- Isolated Mathlib audits (`MasterPrincipleFreeEnergy.lean` `31/31`, `MasterPrincipleBouquet.lean` `14/14` = `45/45` theorems): `BUILD_RC=0` (`0` errors, `0` warnings), `AUDIT_FE_RC=0`, `AUDIT_BQ_RC=0`, strictly standard axioms (`[propext]`, `[propext, Quot.sound]`, `[propext, Classical.choice, Quot.sound]`), zero `sorryAx`.
- Full test suite (`pytest -q`): **`167 passed in 738.05s`**, `exit=0`.
- Hygiene: `proofs/lean-mathlib/.lake` removed from worktree (`LAKE_PRESENT=False`), raw per-run artifacts archived cleanly outside git in temporary storage, zero protected files touched, zero PII/local paths in diff.
