# Master Principle Mechanism Handoff (`gemini/master-principle-mech`)

**Branch:** `gemini/master-principle-mech` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`)
**Targets:**
1. Formalize in Mathlib `v4.12.0` (`proofs/lean-mathlib/MasterPrincipleMech.lean`) the fluctuation-dissipation theorem `d/dlam ⟨μ⟩_lam = - Var_lam(μ)`, strict monotonicity & uniqueness of Boltzmann temperature `lam` from normalized Dirichlet energy `normDirichlet`, and `α²` scaling of step-inertia `LeakyRNN` displacement.
2. Pre-register and execute 100% out-of-sample tests across `12` fresh monoids (`6 free + 6 mixed`) and `6` fresh discriminating group automata, strictly disjoint from Spikes `77/78/81/84/87` and `origin/gemini/master-principle` (`65` excluded monoids; preserving `8` free monoids for `master-principle-transformer`).

## Lean 4 Mathlib Verification (`MasterPrincipleMech.lean` & `AuditMasterPrincipleMech.lean`)

- `lake build MasterPrincipleMech`: `exit=0` (`841.05s`)
- `lake env lean AuditMasterPrincipleMech.lean`: `exit=0`
- Audited theorems (all strictly `[propext, Classical.choice, Quot.sound]`, zero `sorryAx`, zero `MasterPrinciple*` custom axioms):
  - `MasterPrincipleMech.dirichletFlow_hasDerivAt`
  - `MasterPrincipleMech.dirichletFlow_gram_eq_sandwich`
  - `MasterPrincipleMech.dirichletVar_nonneg`
  - `MasterPrincipleMech.dirichletVar_pos_of_two_modes`
  - `MasterPrincipleMech.normDirichlet_hasDerivAt_neg_var`
  - `MasterPrincipleMech.normDirichlet_strictAnti`
  - `MasterPrincipleMech.lambda_unique_of_dirichlet`
  - `MasterPrincipleMech.leaky_step_displacement_sq`

## Pre-Registered Scope, Frozen Parameters, & Verdict Criteria (Rule 5 — Committed Prior to Execution)

- **Frozen operators & temperatures (zero test tuning):**
  - `GAMMA_C = 0.6`, `GAMMA_O = 0.7`, `T_OP = 30`, `LAM0 = 1.476410...`
  - `LAM_CAL = {"gru_lin": 0.85, "gru_mlp": 0.85, "lstm_mlp": 1.20, "rnn_mlp": 1.50}`
  - `LAM_KIN = {"gru_lin": 0.857, "gru_mlp": 1.085, "lstm_mlp": 1.137, "rnn_mlp": 1.782}` (thermodynamic inversion via `normDirichlet` from prior run's `med_kin_norm` ONLY)
- **Disjoint fresh evaluation panel (`experiments/results/master_principle_mech_predictions.json`):**
  - `12` monoids (`6 free + 6 mixed`): `[467, 583, 110, 358, 308, 532, 350, 535, 578, 352, 449, 52]`
  - `8` fresh `free` monoids explicitly reserved for `master-principle-transformer`: `[11, 35, 68, 140, 146, 317, 380, 599]`
  - `6` discriminating groups: `['Z11_s2_039', 'Z12_s1_029', 'Z7_s1_025', 'Z8_s1_036', 'Z7_s3_046', 'Z7_s2_056']`

**Pre-Registered Hypotheses (`HELD` / `NEITHER` / `BROKEN`):**
- **`HMM.1a` (Out-of-sample `LAM_KIN` improvement over `LAM0`):** `cos(G_learned, G(LAM_KIN[arch])) >= cos(G_learned, G(LAM0))` in mean Gram cosine across `>= 3/4` (`75%`) architectures (`>= 1` `fit >= 0.99` each).
- **`HMM.1b` (Resolving `HM.1b` miss on `rnn_mlp` and `lstm_mlp`):** Under `LAM_KIN`, BOTH `rnn_mlp` and `lstm_mlp` (`>= 8` fitted monoids each) beat all 5 rivals (`Wo`, `Wc`, `WcWo_noheat`, `o`, `k1`, and `Wo_heat_kin`) in mean Gram cosine AND `rnn_mlp` beats `o` on `>= 70%` of discriminating runs (`cos(G_kin, o) < 0.95`).
- **`HMM.2` (Zero-cosine `LAM_KIN` vs calibrated `LAM_CAL` transfer gap):** `max_{arch} |mean_cos(G_kin) - mean_cos(G_cal)| <= 0.02` (`HELD`, `> 0.05` `BROKEN`).
- **`HMM.3` (Causal inertia `LeakyRNN` `α = 1.0 -> 0.5 -> 0.25`):** Across `12` automata (`monoids[:6] + 6 groups`, `fit >= 0.90`), `α = 0.25` lowers `kin_norm` relative to `α = 1.0` on `>= 75%` of fitted pairs (`>= 8` pairs; `< 50%` `BROKEN`), and correspondingly raises `lam_emp`.
- **`HMM.4` (Explicit Dirichlet penalty `μ = 0.20` on `LeakyRNN α = 1.0`):** Lowers `kin_norm` relative to `α = 1.0` baseline on `>= 75%` of fitted pairs (`>= 8` pairs; `< 50%` `BROKEN`).
- **`HMM.5` (Weight-decay dissociation control `wd = 3e-2` on `LeakyRNN α = 1.0`):** Fraction lowering `kin_norm` is strictly below both `α = 0.25` (`HMM.3`) and `dirichlet_0.20` (`HMM.4`) (`HELD` iff `frac(wd) < min(frac(0.25), frac(dirichlet))`, else `BROKEN`).

*(Status: Pre-registered; training arms pending execution.)*