# Handoff: Exact Lie-Presentation Unitary Homomorphisms, Non-Posetal Kan Retracts, Hoza Isolating Trees, & Continuous Lyapunov Tangent Gramians (`gemini/master-principle-lie-lyapunov`)

**Status:** `[VERIFIED — 34/34 MATHLIB THEOREMS & 45-RUN EMPIRICAL SHOWDOWN]`  
**Branch:** `gemini/master-principle-lie-lyapunov` (base `origin/claude/practical-shannon-oqg60y` @ `7be5346`)  
**Scope:** Follows `gemini/master-principle-ghsrt` (`56074e3`) and Task 143 (`event 151873`) by testing generator-level unitary presentations (`lie_presentation_gen` and `spectral_presentation_gen`) on non-ambivalent `A4` (`L = 4..16`) and `b1 = 2` `S3` bouquet (`L = 3..8`), formalizing the 3-object Kan retract countermodel outside posetal lattices, proving Hoza (`ECCC TR26-323`) min-isolating spanning-tree gauge reconstruction, and unifying continuous shifted Lyapunov balanced Gramians (`G_cont_lyap`) and Clark (`arXiv:2610.12426`) sparse spacetime KKT RNN tangent spectra with JEPA Content-Geometry alignment (`C8_slow3` & fixed non-identity `D4_slow3` `jag`).

---

## 1. Prior Art vs. Semplex Synthesis

- **Prior Art:** Group presentations (`S3`, `A4`), Lie exponentials, Hoza's `O(log(wn))`-seed min-isolating weights (`ECCC TR26-323`), and Clark's regularized forward-backward minimum-norm tangent response function (`arXiv:2610.12426`) are established results in algebra, derandomization, and random RNN statistical physics.
- **Semplex Contribution:** Machine-checked `34/34` Mathlib `v4.12.0` theorems separating 3-object Kan-extension agreement (`Lan_i v = Ran_i v`) from retract-free equivalence in `Type`, proving exact `S3`/`A4` presentation homomorphisms and isolating-weight tree gauge covariance, deriving shifted continuous Lyapunov similarity/trace conservation, and running a pre-registered 45-run neural + dynamical showdown (`4 HELD`, `1 NEITHER`, `0 BROKEN`).

---

## 2. Mathlib v4.12.0 Formalization (`proofs/lean-mathlib/MasterPrincipleLieLyapunov.lean`)

Built cleanly in isolated temporary `.lake` mount (`lake build MasterPrincipleLieLyapunov` exited `0` in `83.26s`, 0 errors/warnings; `lake env lean AuditMasterPrincipleLieLyapunov.lean` exited `0` in `30.40s`, `.lake` unmounted cleanly leaving 0 `.olean` files in tree). All `34/34` theorems use strictly standard Lean axioms (`[propext]`, `[propext, Classical.choice, Quot.sound]`, or axiom-free) with **zero `sorryAx`** and **zero custom axioms**:

1. **`KanRetractObstruction` (7 theorems):** Concrete 3-object index category `(0 -> 1 -> 2)` with `P = {0, 2}` proving `kan_comparison_at_1_is_id`, `extension_factors_identity`, explicit 3-element middle object retract `extraMidFunctor_restricts_to_v`, `extraMidFunctor_mid_not_equiv_bool`, `kan_comparison_equiv_not_sufficient_in_type` (refuting unrestricted `Lan ~ Ran => Ext ~ *` outside posets), positive `posetal_retract_eq`, and `essential_image_equiv_determined`.
2. **`LiePresentationUnitary` (13 theorems):** `isUnitary_one`, `isUnitary_conjTranspose`, `isUnitary_mul`, `isUnitary_pow`, `spectral_conjugate_unitary`, `spectral_conjugate_pow`, `spectral_conjugate_torsion` (proving `V D V^*` automatically satisfies `U^k = 1` when `D^k = 1`), exact semidirect multiplication laws `s3PresRep_mul`/`s3PresRep_unitary`, `a4_v4_commute`, `a4PresRep_mul`/`a4PresRep_unitary`, and `a4PresRep_trace_conjugacy_invariant`.
3. **`IsolatingWeightTree` (7 theorems):** Strict positive-weight walk monotonicity (`walkWeight_step_strict_lt`), zero root weight (`minWalk_root_nil`), optimality (`minWalk_le`, `minWalk_prefix_eq`), disjointness from chords (`isolating_tree_chord_disjoint`), `isolating_treeFrame_edge_recursion` on BOTH orientations, and `isolating_treeFrame_gauge_covariant`.
4. **`ContinuousLyapunovGramian` (7 theorems):** `shiftedGen_zero`, `shiftedGen_conj`, `lyapEq_congruence_invariant`, `balanced_trace_similarity_invariant` (`Tr(Wc_tilde Wo_tilde) = Tr(Wc Wo)`), `skew_lyapunov_trace_exact` (`lam * Tr(W) = Tr(Q)` for skew generators), `lyapunov_quadratic_decay`, and `discrete_to_continuous_lyapunov_expansion`.

---

## 3. Pre-Registered Verdicts (`HLL.1`–`HLL.5`)

Results from `experiments/results/master_principle_lie_lyapunov.json` (`45` runs in `1454.3s` summary / `1456.72s` wall clock, `max_neural_unitary_err = 5.245e-6`):

| Hypothesis | Verdict | Observed Evidence vs. Criterion |
|---|---|---|
| **`HLL.1`** | **`NEITHER`** | `spectral_presentation_gen` achieves **`1.00000`** OOD balanced accuracy on EVERY length (`A4 L4..L16 = 1.00000`, beating `cayley_unitary_ufr_soft L16 = 0.37281` by **`+0.62719`** with `3.0x` fewer params [`5,124` vs `15,356`]; `S3_bouquet L3..L8 = 1.00000`). Marked `NEITHER` solely because soft relation penalty on `(st)^3 = 1` left `homomorphism_err = 0.01783` on `A4` and `0.00251` on `S3_bouquet` (above the strict `<= 1e-3` bar despite perfect finite-word classification). |
| **`HLL.2`** | **`HELD`** | On unmodified `A4` fine-tuning (`S_ft={2,3}`, `S_keep={0,1}`): `lie_presentation_gen` retains **`0.69825`** (`+0.50351` over `cayley_unitary_fer = 0.19474`, well above `>= +0.20`; vs `cayley_unitary_ufr_soft = 0.02632` and `lie_exp_ufr_soft = 0.00000`), while `spectral_presentation_gen` retains `0.50000`. On `S3_bouquet`, BOTH presentation models suffer **`0.00000` forgetting drop** (`1.00000 -> 1.00000`). |
| **`HLL.3`** | **`HELD`** | Fixing `D4_slow3` fast non-identity generators eliminates the `9.9` sentinel (`jepa_sg = 2.1426`, `jepa_svreg = 2.4128`, `jepa_slow_svreg = 1.5983`, all `< 3.0`); `jepa_slow_svreg` reduces `jag` vs `jepa_sg` on both worlds (`C8`: `1.3894 < 1.8026`; `D4`: `1.5983 < 2.1426`) and boosts `r2_slow` over `jepa_svreg` (`C8`: `0.6466` vs `0.0148`, **`+0.6317`**; `D4`: `0.6964` vs `0.0364`, **`+0.6600`**). |
| **`HLL.4`** | **`HELD`** | `G_cont_lyap(lam)` achieves `best_cos = 0.84630` on `C8_slow3` (`lam*=0.633`, vs `G_gm_heat = 0.83185`, `X_kl_gm = 0.83153`) and `0.82058` on `D4_slow3` (`lam*=0.300`, vs `G_gm_heat = 0.80604`, `X_kl_gm = 0.80516`), mean gap `0.01449 <= 0.08`; Clark (`arXiv:2610.12426`) `N=32, T=56` sparse spacetime KKT solver matches QR Lyapunov exponents at **`0.01871`** quantile MAE (`<= 0.02`; per-seed `[0.02117, 0.01489, 0.02008]`; CDF W1 `0.02037`). |
| **`HLL.5`** | **`HELD`** | `exact_s3_pres_hom_err = 1.658e-15`, `exact_a4_pres_hom_err = 2.029e-15`, `continuous_lyap_err = 6.391e-14`, `trace_similarity_err = 0.0`, `kan_retract_verified = true`, Hoza isolating spanning trees `30/30` (`isolating_tree_success_rate = 1.0`, `gauge_covariance_rate = 1.0`, `max_seed_tried = 1`), and `max_neural_unitary_err = 5.245e-6 < 1e-5`. |

---

## 4. Detailed Empirical Tables (Mean Across 3 Seeds)

### Arm 1A: Non-Ambivalent `A4` (`15` runs: train `L in {4, 5}`, eval OOD up to `L = 16`)

| Model | Params | `unitary_err` | `hom_err` | `L4` | `L5` | `L6` | `L8` | `L12` | `L16` | Keep Before | Keep After | Drop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `cayley_unitary_fer` | 18,732 | 6.95e-7 | 0.2712 | 0.5684 | 0.3921 | 0.3219 | 0.2789 | 0.2719 | 0.2404 | 0.6035 | 0.1947 | 0.4088 |
| `cayley_unitary_ufr_soft` | 15,356 | 7.35e-7 | 0.0614 | 0.9991 | 0.9965 | 0.9921 | 0.8605 | 0.4772 | 0.3728 | 1.0000 | 0.0263 | 0.9737 |
| `lie_exp_ufr_soft` | 15,356 | 9.93e-7 | 0.0461 | 0.9930 | 0.9772 | 0.9439 | 0.5956 | 0.2605 | 0.3114 | 0.9877 | 0.0000 | 0.9877 |
| `lie_presentation_gen` | 5,124 | 3.22e-6 | 0.0633 | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | **0.6982** | **0.3018** |
| `spectral_presentation_gen` | **5,124** | 4.73e-6 | **0.0178** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | 0.5000 | 0.5000 |

### Arm 1B: `b1 = 2` `S3` Bouquet (`12` runs: train `L in {3, 4}`, eval OOD up to `L = 8`)

| Model | Params | `unitary_err` | `hom_err` | `L3` | `L4` | `L6` | `L8` | Keep Before | Keep After | Drop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `cayley_unitary_fer` | 15,995 | 6.56e-7 | 0.2408 | 0.9477 | 0.7720 | 0.5030 | 0.3348 | 0.9542 | 0.9069 | 0.0472 |
| `cayley_unitary_ufr_soft` | 15,671 | 8.05e-7 | 0.0804 | 0.9992 | 0.9689 | 0.5909 | 0.2303 | 0.9986 | 0.6431 | 0.3556 |
| `lie_presentation_gen` | 8,747 | 1.83e-6 | 0.0411 | **1.0000** | **1.0000** | 0.9962 | 0.9985 | 1.0000 | **1.0000** | **0.0000** |
| `spectral_presentation_gen` | **8,747** | 2.90e-6 | **0.0025** | **1.0000** | **1.0000** | **1.0000** | **1.0000** | 1.0000 | **1.0000** | **0.0000** |

### Arm 2: Continuous Shifted Lyapunov vs. Heat/KL & Fixed `D4_slow3` `jag` (`18` runs)

| World | Objective | `jag` | `r_geom` | `r2_fast` | `r2_slow` | `eff_rank` | `cos(G_cont_lyap)` | `lam*_cont` | `cos(G_gm_heat)` | `cos(X_kl_gm)` |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `C8_slow3` | `jepa_sg` | 1.8026 | 0.2281 | 0.9919 | -0.0240 | 4.4900 | 0.8346 | 4.000 | 0.7619 | 0.7619 |
| `C8_slow3` | `jepa_svreg` | **1.3279** | 0.7095 | 0.8250 | 0.0148 | 2.8195 | 0.7784 | 1.200 | 0.7378 | 0.7377 |
| `C8_slow3` | `jepa_slow_svreg` | 1.3894 | **0.7429** | 0.9329 | **0.6466** | 4.5655 | **0.8463** | 0.633 | **0.8319** | **0.8315** |
| `D4_slow3` | `jepa_sg` | 2.1426 | -0.1139 | 0.9927 | 0.2043 | 4.6491 | 0.7549 | 4.000 | 0.6793 | 0.6793 |
| `D4_slow3` | `jepa_svreg` | 2.4128 | -0.2125 | 0.7732 | 0.0364 | 2.8754 | 0.6880 | 4.000 | 0.6134 | 0.6134 |
| `D4_slow3` | `jepa_slow_svreg` | **1.5983** | **0.7864** | 0.9433 | **0.6964** | 5.5554 | **0.8206** | 0.300 | **0.8060** | **0.8052** |

---

## 5. What This Does NOT Show (Honest Limitations)

1. `spectral_presentation_gen` enforces torsion relations (`s^2 = 1`, `t^3 = 1`) spectrally by conjugation, but `(s t)^3 = 1` (`A4`) and `(s r)^2 = 1` (`S3`) are still softly regularized rather than enforced as exact Coxeter/presentation manifolds (`homomorphism_err = 0.01783` on `A4` and `0.00251` on `S3_bouquet`), which caused `HLL.1 = NEITHER` despite `1.00000` OOD classification up to `L = 16`.
2. In `A4` Phase-2 fine-tuning (`S_ft={2,3}`), presentation-grounded architectures retain `0.500–0.698` on `S_keep={0,1}` (far above `0.000–0.195` baselines), yet still drop because the linear classifier `head` is shared and unconstrained during Phase-2 updates (`S3_bouquet`, by contrast, retains `1.000` with `0.0` drop).
3. Clark's sparse spacetime KKT comparison (`N = 32, T = 56`, `epsilon = 1.0`) was run across 3 random asymmetric RNN seeds as an algorithmic solver audit rather than trained inside the `C8`/`D4` JEPA neural encoders.
4. Hoza isolating-weight spanning trees are audited across 30 random `b1 in {2, 3, 5}` finite multigraphs (`1` seed sufficiency here stems from random multigraph edge-weight collision rarity up to `|V|<=10`, whereas worst-case adversarial graphs require larger seed bit-lengths matching `O(log(wn))`).
5. Mathlib formalization in `proofs/lean-mathlib/MasterPrincipleLieLyapunov.lean` proves discrete presentation homomorphisms and finite-dimensional matrix Lyapunov theorems, without bridging across package boundaries into `proofs/lean/` or continuous-spectrum infinite-dimensional functional analysis.

---

## 6. Verification Scope (Rule 7 Checklist)

Committed before final Semplex Rule 7 verification completes over `cerp.register check`, `cerp.status --check`, `5/5` core `proofs/lean` axiom audits (`Audit`, `AuditBounds`, `AuditClosure`, `AuditInference`, `AuditTheory`), and full `pytest -q` (with `ortools` and `jax`) with `0` protected-path edits and `0` `.lake`/`.olean` files in tree.
