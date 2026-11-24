# Handoff: Homotopy-Fiber Obstruction Exactness, Monolith Impossibility & Quantitative Gauge Stability

## 1. Branch and Deliverables

- **Branch:** `gemini/master-principle-obstruction-stability` (stacked on `gemini/master-principle-continuum-llm-closure` at `21b0eb3ae1a94661d99e459c20c47be4a2e6f12e` / PR #9)
- **Prior-Art & Originality Analysis:**
  - `research/LORENZ_TULL_2026_PRIOR_ART_AND_ORIGINALITY.md` — full analysis of Lorenz & Tull (`arXiv:2602.16612v1`) showing why internal isotropy `ker(Obs_P : G_rep -> G_prof)`, anchor-induced `Cech H^1` gluing obstructions, monolith subgroup impossibility, `mu`-a.e. quotienting, `ker W` gauge-tube bounds, and geometric contraction horizons sit strictly outside Lorenz & Tull (2026).
- **Pure Lean 4 Formalization (`proofs/lean/ObstructionExactSequence.lean`, `proofs/lean/AuditObstructionExactSequence.lean`):**
  - Registered in `proofs/lean/lakefile.lean` and `proofs/lean/check_all.ps1`.
  - `22/22` audited declarations (`14` axiom-free `[]`, `7` `[propext]`, `1` `[propext, Quot.sound]`, `0` `Classical.choice`, `0` `sorryAx`):
    - Exact sequence of pointed sets & cocycle/coboundary characterization (`globalRealization_iff_coboundary`, `gluesByGauge_iff_transition_coboundary`, `connecting_trivial_iff_lift`, `exactness_at_H1_H`);
    - Anchor-induced `C4` Specker contextual obstruction (`unanchored_triangle_has_two_realizations`, `c2InC4_acts_on_realizations`, `speckerCoset0Local_valid_edges`, `speckerCoset0Local_not_transition_coboundary`, `speckerCoset0Local_not_gluesByGauge`, `c4_triangle_coset0_anchor_no_global_realization`, `speckerC2Cocycle_nontrivial`, `speckerCoset1Local_gluesByGauge`);
    - Monolith subgroup impossibility (`hasMonolith_not_partialAnchorAdequate`, `c4_hasMonolith`, `c4_not_partialAnchorAdequate`, `q8_nonabelian`, `q8_hasMonolith`, `q8_not_partialAnchorAdequate` vs `c2cubed_partialAnchorAdequate`).
- **Cubical Agda HoTT Formalization (`proofs/cubical/src/Semplex/Cubical/FiberObstructionSequence.agda`):**
  - `10th` Cubical module checked under Agda `2.9.0 --cubical=full` with `0` warnings across all `10` modules.
  - Implements square-cell `Deloop` + `Deloop->BG` equivalence (avoiding constructor-`hcomp` boundary transport mismatch), `BHom`, `Fib`, `kerLoop` (`kerLoop-fst`), connecting coset path (`connectingPoint`, `connecting-coset-path`), exactness (`im-trivializes-connecting`), and the concrete `C4Group -> C2Group` mod-2 witness (`mod2Hom`, `c4-mod2-ker-loop`, `c4-mod2-ker-loop-proj`, `c4-mod2-coset1-trivializes`).
- **Mathlib Formalization (`proofs/lean-mathlib/QuantitativeGaugeStability.lean`, `proofs/lean-mathlib/AuditQuantitativeGaugeStability.lean`):**
  - Registered as the `18th` default library in `proofs/lean-mathlib/lakefile.toml`.
  - `17/17` audited theorems (`[propext, Classical.choice, Quot.sound]`, `0` warnings, `0` `sorryAx`):
    - `mu`-a.e. equivalence & anchor identifiability (`aeGaugeRel_equivalence`, `ae_null_perturbation_trivial`, `ae_anchor_kills_isotropy_iff`);
    - `eps`-gauge closure & geometric vs linear contraction bounds (`epsGauge_refl`, `epsGauge_symm`, `epsGauge_comp`, `epsGauge_pow`, `contraction_horizon_bound`, `nonexpansive_horizon_bound`);
    - `ker W` gauge-tube decision stability (`gauge_perturbation_invisible`, `no_flip_within_gauge_tube_pos`, `no_flip_within_gauge_tube_neg`, `gauge_escape_lower_bound`, `eps_orbit_rigidity`);
    - Variable-Jacobian density pushforward (`variable_jacobian_density_pushforward`, `exp_jacobian_nonunit`, `exp_density_change_of_variables`).
- **Empirical Probes & Tests:**
  - `experiments/quantitative_gauge_stability_probe.py`
  - `experiments/results/quantitative_gauge_stability_predictions.json` (pre-registered unchanged)
  - `experiments/results/quantitative_gauge_stability_results.json`
  - `tests/test_quantitative_gauge_stability_probe.py`
  - `claims/PROPOSED.md` (`## 26.`)

## 2. Empirical Results (`HQS.1`–`HQS.5`, `1547.40s` total)

- `HQS.1` (**`HELD`**, `0.0076s`): Non-Dirac `16`-state `Q8` and `C2^3` HMMs (`max_row_prob = 0.85`, `profile_tv_max = 7.633e-17`); all `4` proper nontrivial subgroups of `Q8` intersect in `["1", "-1"]` (`kernel_size = 2`), whereas `C2^3`'s `14` subgroups clear to `["000"]` in `3` hyperplane anchors.
- `HQS.2` (**`HELD`**, `0.00007s`): `C4 -> C2` Specker triangle yields `2` unanchored global sections (`[1,1,1]`, `[3,3,3]`), `2` solutions per edge in coset `{0,2}` with `0` global sections and constant cycle monodromy `2 != 0 mod 4`, vs `2` global sections and `8` trivial monodromies in coset `{1,3}`.
- `HQS.3` (**`BROKEN`**, `1418.73s`): Pretrained `HuggingFaceTB/SmolLM2-135M-Instruct` achieved `cal_fp32_acc = 1.0` and `fp32_eval_acc = 0.9583` on clean factual completion pairs, but `per_family_int4_flip_rates` and `all_int4_flip_rate` stayed `0.0` (`all_int4_acc = 0.9583`), falsifying `all_int4_flip_rate >= 0.15` and leaving `spearman_gamma_vs_flip = null` / `spearman_frob_vs_flip = null`. Continuous `per_family_int4_mean_abs_margin_shift` still varied cleanly across modules (`down_proj = 1.4380`, `up_proj = 1.0852`, `gate_proj = 0.6740`, `k_proj = 0.5976`, `o_proj = 0.5748`, `v_proj = 0.5395`, `q_proj = 0.4701`) in broad agreement with `gamma_mod` (`down_proj = 1.6533`, `up_proj = 1.1708`, `v_proj = 0.9499`, `gate_proj = 0.8746`, `o_proj = 0.6943`, `q_proj = 0.6366`, `k_proj = 0.6328`).
- `HQS.4` (**`HELD`**, `127.29s`): On `BAAI/bge-base-en-v1.5` (`14,175,744` top-2-block params), `fp32_taskA_acc = 1.0`, `frozen_taskA_drop = 0.0`, `frozen_taskB_acc = 1.0`, `prop2_pyth_rel_err = 7.039e-13`, `prop2_orth_cos_abs = 1.912e-14`, `orthogonal_waste_fraction = 0.9238`; return-only SGD matching SFT Task-B eval loss (`matched_taskB_acc_gap = 0.0`, both `1.0` Task-B acc) reduced update norm `0.2845 -> 0.03578` and Task-A logit L2 drift `0.09019 -> 0.08173`.
- `HQS.5` (**`HELD`**, `0.70s`): Triangular `C^infty` map across seeds `[101, 202, 303]` achieved `jacobian_ratio_max_min = 14.0457`, `jacobian_log_density_max_err = 7.105e-15`, `mc_energy_dist_err_max = 0.002888`, and satisfied the `T=1..8` contraction bound (`contraction_vs_linear_ratio_at_T8 = 0.1969`).

## 3. Reproducible Verification Commands

- Core Lean: `powershell -ExecutionPolicy Bypass -File proofs/lean/check_all.ps1`
- Mathlib Lean: `cd proofs/lean-mathlib && lake build && lake env lean AuditQuantitativeGaugeStability.lean`
- Cubical Agda: `/opt/Agda-nightly/bin/agda -v0 --cubical=full` over all `10` modules in `proofs/cubical/src/Semplex/Cubical/`
- Ledger & Tests: `python -m cerp.register check`, `python -m cerp.status --check`, `pytest -q`
