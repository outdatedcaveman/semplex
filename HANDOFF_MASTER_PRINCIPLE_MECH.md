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

*(Status: Executed, analysed, AND full Rule 7 verified.)*

## Measured Results (`experiments/results/master_principle_mech.json`)

### Pre-Registered Verdicts (`108` runs total, `100%` finished, `BelowNormal` single-threaded)

| Hypothesis | Verdict | Exact Quantitative Evidence |
| :--- | :---: | :--- |
| **`HMM.1a`** (`LAM_KIN` beats `LAM0`) | **`HELD`** | **`4 / 4` (`100%`)** architectures beat `LAM0` in mean `cos_G` purely out-of-sample (`gru_lin`: `0.9487 -> 0.9543`, `gru_mlp`: `0.8520 -> 0.8537`, `lstm_mlp`: `0.8884 -> 0.8886`, `rnn_mlp`: `0.8092 -> 0.8132`) |
| **`HMM.1b`** (`rnn_mlp` & `lstm_mlp` beat all rivals) | **`HELD`** | **`4 / 4`** architectures (including `rnn_mlp` `n=9` and `lstm_mlp` `n=12`) beat ALL 6 rivals (`Wo`, `Wc`, `WcWo_noheat`, `o`, `k1`, `Wo_heat_kin`) in BOTH mean & median `cos_G`; **`100%` (`8/8` `rnn_mlp`, `10/10` others)** beat `o` where `cos(G, o) < 0.95` |
| **`HMM.2`** (Zero-cosine `LAM_KIN` vs `LAM_CAL` gap) | **`HELD`** | Max mean `cos_G` gap across all 4 architectures is **`0.0036`** (`|0.81323 - 0.80961|` on `rnn_mlp`, far below `0.02` gate) |
| **`HMM.3`** (Causal inertia `α = 1.0 -> 0.5 -> 0.25`) | **`NO VERDICT`** | **`4 / 4` (`100%`)** converged pairs (`fit >= 0.90`, `M_110`, `M_308`, `G_Z7_s3_046`, `G_Z7_s2_056`) drop `kin_norm` AND raise `lam_emp` strictly (`α=0.5` is `5 / 5`), below the pre-registered `n >= 8` converged-pairs floor |
| **`HMM.4`** (Dirichlet penalty `μ = 0.20`) | **`NO VERDICT`** | **`2 / 2` (`100%`)** converged pairs (`M_110`: `0.8449 -> 0.7321`; `M_308`: `0.4951 -> 0.4765`) drop `kin_norm`, below `n >= 8` because step-0 `dh/var_h` collapsed fit (`0.56–0.84`) on `10 / 12` automata |
| **`HMM.5`** (Weight decay `wd = 3e-2` dissociation) | **`HELD`** *(underpowered comparator)* | `4 / 8` (`0.500`) converged pairs lower `kin_norm` (`M_583`, `M_110`, `M_358`, `G_Z7_s1_025`), strictly `< min(1.0, 1.0)` — effect is symmetric noise (`±0.006`), caveated by `n=4` in `HMM.3` and `n=2` in `HMM.4` |

### Arm 1: Out-of-Sample Calibration (`12` fresh monoids, `fit >= 0.99`)

| Arch | Fitted | `med(kin_norm)` | `med(λ_emp)` | `pred(λ_KIN)` | `mean(G_λ0)` | `mean(G_CAL)` | `mean(G_KIN)` | Beat All 6 Rivals? | Beat `o` (`<0.95`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `gru_lin` | `12 / 12` | `0.6524` | `1.094` | `0.857` | `0.9487` | `0.9543` | **`0.9543`** | **True** (mean & med) | `10 / 10` (`1.00`) |
| `gru_mlp` | `12 / 12` | `0.6424` | `1.284` | `1.085` | `0.8520` | `0.8523` | **`0.8537`** | **True** (mean & med) | `10 / 10` (`1.00`) |
| `lstm_mlp` | `12 / 12` | `0.6028` | `1.239` | `1.137` | `0.8884` | `0.8889` | **`0.8886`** | **True** (mean & med) | `10 / 10` (`1.00`) |
| `rnn_mlp` | `9 / 12` | `0.5953` | **`2.376`** | `1.782` | `0.8092` | `0.8096` | **`0.8132`** | **True** (mean & med) | `8 / 8` (`1.00`) |

*(Note: `rnn_mlp` `med cos_G_kin = 0.8334` > `Wc = 0.8196` > `WcWo_noheat = 0.7817` > `Wo_heat_kin = 0.7098` > `k1 = 0.6987` > `Wo = 0.5728` > `o = 0.4252`; `mean cos_G_kin = 0.8132` > `Wc = 0.8048` > all others.)*

### Arm 2/3: Causal Interventions (`LeakyRNN`, `1000` steps, all `12` units shown unconditionally)

- **Strictly converged pairs (`fit >= 0.90`):** `alpha_0.5`: `5/5` (`1.0`), `alpha_0.25`: `4/4` (`1.0`), `monotone_chain`: `4/4` (`1.0`), `dirichlet_0.20`: `2/2` (`1.0`), `wd_3e-2`: `4/8` (`0.50`).
- **Unconditional directional pattern across all `12` automata (`6` monoids + `6` groups):**
  - `kin_norm(α = 0.25) < kin_norm(α = 1.0)` holds on **`12 / 12` (`100%`)** of automata (`kin(0.5) < kin(1.0)` also `12 / 12`), and strict monotone `kin(1.0) > kin(0.5) > kin(0.25)` holds on **`11 / 12` (`91.7%`)** (the sole non-strict tail is `G_Z7_s1_025`: `0.8702 -> 0.2050 -> 0.2099` where `α = 0.25` stopped at `fit = 0.6311`).
  - Conversely, two periodic groups that failed baseline `α = 1.0` (`G_Z11_s2_039`: `fit=0.7055`, `G_Z12_s1_029`: `fit=0.8153`) **solved to `fit >= 0.995` ONLY when leaky inertia `α = 0.5` was enabled** (`0.9995`, `0.9953`), with lower `kin_norm` and higher `lam_emp`.

| Unit | `α=1.0` (`fit`, `kin`, `λ`) | `α=0.5` (`fit`, `kin`, `λ`) | `α=0.25` (`fit`, `kin`, `λ`) | `dir_0.20` (`fit`, `kin`, `λ`) | `wd_3e-2` (`fit`, `kin`, `λ`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `M_467` | `(0.6086, 0.1787, 9.56)` | `(0.6250, 0.1280, 12.0)` | `(0.6064, 0.1213, 12.0)` | `(0.5592, 0.2005, 8.93)` | `(0.6024, 0.1693, 9.88)` |
| `M_583` | `(0.9900, 0.4872, 2.50)` | `(0.8782, 0.4507, 2.87)` | `(0.6874, 0.3956, 3.53)` | `(0.5938, 0.5802, 1.67)` | `(0.9904, 0.4808, 2.56)` |
| `M_110` | **`(1.0000, 0.8449, -0.54)`** | **`(1.0000, 0.7969, 0.57)`** | **`(0.9455, 0.6520, 3.75)`** | **`(0.9991, 0.7321, 2.01)`** | `(1.0000, 0.8445, -0.53)` |
| `M_358` | `(1.0000, 0.5660, 2.79)` | `(0.8830, 0.4971, 3.52)` | `(0.8612, 0.4674, 3.88)` | `(0.8050, 0.6006, 2.46)` | `(1.0000, 0.5602, 2.85)` |
| `M_308` | **`(1.0000, 0.4951, 4.31)`** | **`(0.9943, 0.4789, 5.98)`** | **`(0.9779, 0.4716, 7.76)`** | **`(0.9723, 0.4765, 6.41)`** | `(1.0000, 0.4972, 4.17)` |
| `M_532` | `(0.7912, 0.2743, 12.0)` | `(0.7851, 0.2029, 12.0)` | `(0.7835, 0.1878, 12.0)` | `(0.7852, 0.2056, 12.0)` | `(0.7984, 0.3086, 11.97)` |
| `G_Z11_s2_039` | `(0.7055, 0.1201, 7.37)` | `(0.9995, 0.0914, 11.52)` | `(0.9656, 0.0877, 12.0)` | `(0.8075, 0.1156, 7.74)` | `(0.7028, 0.1203, 7.36)` |
| `G_Z12_s1_029` | `(0.8153, 0.0921, 8.27)` | `(0.9953, 0.0798, 10.83)` | `(0.9729, 0.0749, 12.0)` | `(0.8366, 0.0875, 8.97)` | `(0.7682, 0.1196, 6.18)` |
| `G_Z7_s1_025` | `(1.0000, 0.8702, 0.13)` | `(1.0000, 0.2050, 10.17)` | `(0.6311, 0.2099, 9.67)` | `(0.6345, 0.4565, 4.71)` | `(0.9990, 0.8366, 0.85)` |
| `G_Z8_s1_036` | `(0.9988, 0.7430, 1.60)` | `(0.7052, 0.1808, 11.79)` | `(0.7176, 0.1690, 12.0)` | `(0.6670, 0.2403, 9.13)` | `(0.9925, 0.7469, 1.52)` |
| `G_Z7_s3_046` | **`(1.0000, 0.2182, 6.53)`** | **`(0.9997, 0.2012, 8.41)`** | **`(0.9910, 0.1933, 10.57)`** | `(0.6713, 0.2350, 5.53)` | `(0.9998, 0.2196, 6.42)` |
| `G_Z7_s2_056` | **`(0.9981, 0.5810, 0.09)`** | **`(0.9997, 0.1983, 12.0)`** | **`(0.9989, 0.1942, 12.0)`** | `(0.5946, 0.3307, 6.51)` | `(0.9981, 0.5827, 0.03)` |

## What This Does NOT Show

- **Powered causal `fit >= 0.90` sample on `HMM.3` / `HMM.4`:** At `steps = 1000`, `LeakyRNN(α = 0.25)` only converged to `fit >= 0.90` on `4 / 12` tasks (`M_467` and `M_532` failed even at `α = 1.0`), and un-annealed `dirichlet_0.20` collapsed fit on `10 / 12` tasks, leaving `HMM.3` and `HMM.4` strictly **`NO VERDICT`** (`n < 8` pairs) despite `12 / 12` unconditional directional agreement for `α = 0.25` and `0.5`. Larger step budgets (`>= 2000`) or warmup-annealed Dirichlet penalties are needed to bring converged sample size above `n = 8`.
- **Full non-diagonal / non-commuting matrix trace identity in Lean:** `MasterPrincipleMech.lean` proves `normDirichlet_hasDerivAt_neg_var` and `lambda_unique_of_dirichlet` over finite weighted eigenspectra `(w, μ)`, NOT general finite-dimensional non-commuting `Matrix` exponentials in Mathlib (`tr(L exp(-λ L) W) / tr(exp(-λ L) W)`).
- **`proofs/lean/` unchanged:** Core Cerp Lean proofs remain untouched; Mathlib proofs are isolated in `proofs/lean-mathlib/`.

## Rule 7 Verification (Observed Outputs)

- `python -m cerp.register check`: `exit=0` (`0 problem(s), 46 status note(s)`).
- `python -m cerp.status --check`: `exit=0`.
- `git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/`: empty (`LEAN_DIFF_LEN=0`).
- Lean 4.12.0 audits against `proofs/lean/` core `.olean`s: `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`, `AuditInference.lean`, `AuditClosure.lean` all `exit=0`, standard axioms only, `leftover_oleans=0`.
- Lean Mathlib `v4.12.0`: `lake build MasterPrincipleMech` `exit=0` (`841.05s`), `AuditMasterPrincipleMech.lean` `exit=0` (`8/8` theorems strictly `[propext, Classical.choice, Quot.sound]`); `proofs/lean-mathlib/.lake` removed from worktree (`DOT_LAKE_PRESENT=False`).
- `SEMPLEX_LEAN_TIMEOUT=900 pytest -q`: **`167 passed in 731.38s (0:12:11)`** (`exit=0`).