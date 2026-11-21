# Pre-Registered Master Principle Protocol & Handoff (`gemini/master-principle`)

**Date:** 2026-11-20 · **Branch:** `gemini/master-principle` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`) · **Status:** COMPLETE — 180/180 runs executed (0 errors), pre-registered verdicts: 5 HELD / 2 NEITHER / 1 BROKEN.

## 1. Candidate Master Principle

For any finite deterministic automaton $(Q, A, \delta, \pi)$ with stationary state distribution $\pi > 0$ ($\sum_q \pi_q = 1$) and output map $o : Q \to \mathbb{R}^d$, define in the $\sqrt{\pi}$-weighted, constant-centered Hilbert space $L^2_0(\pi) = P_\perp L^2(\pi)$:

- Standardized forward Koopman observables $\hat{o}$ (zero mean, unit variance per coordinate under $\pi$),
- Forward observability Gramian $W_o(\gamma_o) = P_\perp \left(\sum_{t=0}^{T-1} \gamma_o^t A_t\right) P_\perp$ with $A_0 = \hat{o}\hat{o}^\top$ and $A_{t+1} = \frac{1}{|A|} \sum_a \tilde{T}_a A_t \tilde{T}_a^\top$,
- Past-reachability $\chi^2$ Gramian $W_c(\gamma_c) = \sum_{t=1}^{T-1} \gamma_c^t P_\perp B_t P_\perp$ with $B_0 = \mathbf{1}_\pi \mathbf{1}_\pi^\top$ and $B_{t+1} = \frac{1}{|A|} \sum_a \tilde{T}_a^\top B_t \tilde{T}_a$,
- Dirichlet kinetic operator $\mathcal{L}_{\text{kin}} = \frac{1}{2|A|} \sum_a P_\perp (\tilde{T}_a - I)^\top (\tilde{T}_a - I) P_\perp$,

where $\tilde{T}_a = D_\pi^{1/2} P_a D_\pi^{-1/2}$ ($P_a$ is the Koopman pull-back $(P_a f)(q) = f(\delta_a q)$). The predicted state-representation Gram operator at exchange rate $\lambda$ is the non-commutative two-sided causal-kinetic operator:

$$\mathcal{G}(\lambda) = P_\perp\, e^{-\frac{\lambda}{2}\mathcal{L}_{\text{kin}}}\,\bigl(W_c(\gamma_c) + W_o(\gamma_o)\bigr)\, e^{-\frac{\lambda}{2}\mathcal{L}_{\text{kin}}}\, P_\perp.$$

**Frozen constants (zero tuning on any test automaton):**
$\gamma_c = 0.6$, $\gamma_o = 0.7$, $T_{\text{op}} = 30$, and $\lambda_0 = \lambda_{\text{S77}} / \alpha_{\text{S77}} = 3.6753248 / 2.4893651 = 1.476410$ (from frozen Spike 77 calibration `experiments/results/theory_exchange_rate.json:default`).

## 2. Mechanized Lean 4 + Mathlib Theorems (`proofs/lean-mathlib/MasterPrinciple.lean`)

Verified with `lake build MasterPrinciple` (`BUILD EXIT: 0` in `113.46s`, Lean `v4.12.0` + Mathlib `v4.12.0`) and `lake env lean AuditMasterPrinciple.lean` (`AUDIT EXIT: 0` in `82.22s`, all 18 audited declarations depend only on `[propext, Classical.choice, Quot.sound]`, zero `sorryAx`):

- `pastStep_adjoint`: exact $L^2(\pi)$ duality $\langle T_a^* f, g \rangle_\pi = \langle f, T_a g \rangle_\pi$.
- `wcOp_eq_zero_of_bijective`, `pastForm_eq_zero_of_bijective`: $W_c \equiv 0$ identically whenever every input transition $\delta_a$ is bijective and $\pi$-preserving (including every finite group automaton under uniform $\pi$).
- `kineticOp_inner_eq_dirichlet`, `kineticOp_selfAdjoint`, `kineticForm_nonneg`, `kineticOp_const`, `piInner_constOne_kineticOp`: self-adjointness and Dirichlet energy identity for $\mathcal{L}_{\text{kin}}$.
- `heatApply_eigenmode`, `masterOperator_eigenvalue_on_commuting_mode`, `group_master_reduces_to_gibbs`: on any bijective $\pi$-preserving automaton, the Master Operator reduces identically (with zero linearity hypotheses left) on commuting eigenmodes $(e, c)$ to the Gibbs spectral weight $e \cdot e^{-\lambda c}$ (`C43`).
- `hypercube_kineticForm_eq_totalInfluence`: on the Boolean $n$-cube with single-bit flips, `kineticForm` of a Boolean function $g$ equals $(2/n) \cdot I(g)$ (normalized total Boolean influence), linking $\mathcal{L}_{\text{kin}}$ directly to the Boolean-circuit sensitivity axis.

## 3. Prospective Pre-Registered Experimental Design (`experiments/master_principle.py`)

### Fresh Test Automata (`experiments/results/master_principle_predictions.json`, seed `20261120`)
- **12 fresh irreversible monoids** (6 `free`, 6 `mixed`) drawn from `S81.build_pool()`, strictly excluding all 53 automaton IDs previously used in Spikes 81, 84, and 87 (`(pi > 1e-4).all()`, `dimR >= 1`, `dimH >= 1`):
  - Interleaved IDs: `65` (free), `127` (mixed), `515` (free), `103` (mixed), `512` (free), `409` (mixed), `584` (free), `70` (mixed), `281` (free), `193` (mixed), `368` (free), `76` (mixed).
- **6 fresh discriminating group automata** drawn from `S77.POOL` (186 eligible after excluding `S77.USED`, `spike77_predictions.json`, and `spike78_predictions.json`), where `lead_G != energy` or `lead_G != smooth` and `pmax >= 0.6`:
  - `Z11_s1_048`, `Z12_s1_045`, `Z7_s3_015`, `Z8_s3_047`, `Z7_s2_013`, `Z11_s2_035`.

### Training Arms (`batch=64`, `T=30`, `burn=5`, fit guard `>= 0.99` at length 100 except `HM.5a` `>= 0.90`)
1. `gru_mlp`: GRU (`dim=64`) + 3-layer tanh MLP readout (`steps=2000, lr=0.004`, 3 seeds × 12 monoids = 36 runs; saves step-0 and final centroids).
2. `gru_lin`: GRU (`dim=64`) + linear readout (`steps=2000, lr=0.004`, 2 seeds × 12 monoids = 24 runs).
3. `lstm_mlp`: LSTM (`steps=1500, lr=0.008`, 2 seeds × 12 monoids = 24 runs).
4. `rnn_mlp`: ungated tanh `nn.RNN` with orthogonal `W_hh` init & gradient clipping `1.0` (`steps=2500, lr=0.004`, 2 seeds × 12 monoids = 24 runs).
5. `spec`: exact Hankel-SVD spectral realization (400 random suffixes len 0..8, 12 monoids).
6. `grp`: `gru_lin` + `gru_mlp` (`steps=2500, lr=0.004`, 3 seeds each × 6 fresh groups = 36 runs).
7. `noise`: `GRUCell`-based `gru_mlp` with state noise $\eta = 0.20$ during training (`steps=2500, lr=0.004`, 2 seeds × [first 6 monoids + 6 groups] = 24 runs).
- Execution infra note (committed before any completed run in `master_principle_raw/`): switched `torch.set_num_threads(4)` -> `1` (1.73x faster on CPU for `batch=64, T=30`) and added deterministic `part="k/K"` job sharding matching `experiments/spike87.py`; zero changes to seeds, hyperparameters, automata, operators, or criteria.

### Pre-Registered Hypotheses and Numeric Kill Criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| **HM.1a** | Nonlinear-readout `GRU-MLP` state Gram aligns closely with zero-parameter $\mathcal{G}(\lambda_0)$ | Median $\cos(G_{\text{learned}}, \mathcal{G}(\lambda_0)) \ge 0.85$ ($\ge 8$ fitted monoids) | Median $< 0.70$ |
| **HM.1b** | $\mathcal{G}(\lambda_0)$ beats all ablations (`Wo_heat`, `WcWo_noheat`, `Wo`, `o`, `k1`) | Beats all 5 rivals in median cosine, beats `o` pairwise on $\ge 70\%$ of runs with $\cos(G,o) < 0.95$ ($\ge 4$ monoids), AND beats `Wo_heat` pairwise on $\ge 70\%$ of runs with $\|W_c\|/\|W_o\| \ge 0.25$ (8/12 monoids, $\ge 4$ fitted) | Fails median lead OR drops $< 50\%$ on either pairwise test |
| **HM.2** | Linear-readout `GRU-LIN` state Gram follows $\mathcal{G}(\lambda_0)$ and beats generator $o$ | Median $\cos(G_{\text{learned}}, \mathcal{G}(\lambda_0)) \ge 0.90$ ($\ge 8$ monoids) AND beats $o$ in $\ge 70\%$ of fitted runs | Median $< 0.75$ or beats $o$ in $< 50\%$ |
| **HM.3a** | Multi-substrate recurrence: `LSTM-MLP` and `RNN-MLP` follow $\mathcal{G}(\lambda_0)$ | BOTH achieve median $\cos(G_{\text{learned}}, \mathcal{G}(\lambda_0)) \ge 0.80$ ($\ge 6$ fitted monoids each) | Either median $< 0.65$ |
| **HM.3b** | Non-recurrent boundary control: Hankel-SVD (`SPEC`) lacks kinetic/past filtering | `SPEC` aligns closer to $W_o$ than $\mathcal{G}(\lambda_0)$ on $\ge 75\%$ of the 12 monoids ($\ge 8$ monoids) | $< 50\%$ |
| **HM.4** | Exact group unification (zero parameter change) | On 6 fresh groups (`GRU-LIN` + `GRU-MLP`), $\mathcal{G}(\lambda_0)$ top eigenspace matches learned leading irrep in $\ge 75\%$ of runs ($\ge 4$ groups) and beats energy-only and smooth-only | $< 50\%$ |
| **HM.5a** | Causal kinetic-diffusion test: training noise $\eta=0.20$ lowers normalized Dirichlet energy $\bar{c}$ | $\bar{c}(\eta=0.20) < \bar{c}(\eta=0)$ on $\ge 75\%$ of tested automata (6 monoids + 6 groups, `fit >= 0.90`, $\ge 8$ automata) | $< 50\%$ |
| **HM.5b** | Mechanistic decomposition (Step 0 vs trained): reservoir initialization is $W_c$-dominated, gradient learning builds $W_o$ | At step 0, $\cos(G_0, W_c) > \cos(G_0, W_o)$ in $\ge 75\%$ of fitted runs AND final $\cos(G, W_o) > \cos(G_0, W_o)$ in $\ge 80\%$ ($\ge 12$ runs) | $< 50\%$ on either |

Anything in between is **NEITHER** (`NO VERDICT` if fewer than the minimum automata/runs satisfy the fit guard).

## 4. What this cannot show

- Whether continuous-state Transformer architectures (depth-bounded, non-recurrent) obey the same operator or occupy a distinct bounded-window universality class.
- Whether optimal global constants $(\gamma_c, \gamma_o)$ or nonlinear spectral transformations of $W_c + W_o$ improve on $(\gamma_c=0.6, \gamma_o=0.7)$ without tuning.
- Why finite-width gradient dynamics concretely induce the $\approx e^{-\frac{\lambda_0}{2}\mathcal{L}}$ damping factor from initialization to convergence.

## 5. Results (`experiments/results/master_principle.json`, `master_principle_raw/`: 384 files / 180 JSON / 0.479 MB)

### 5.1 Pre-Registered Verdicts (`5 HELD / 2 NEITHER / 1 BROKEN`)

| ID | Pre-Registered Verdict | Observed Result | Thresholds (Held / Broken) |
|---|---|---|---|
| **HM.1a** | **NEITHER** | `gru_mlp` median $\cos(G, \mathcal{G}(\lambda_0)) = 0.840$ (mean $0.835$; `36/36` fitted across `12/12` monoids; `u1_G = 0.700` vs `u1_o = 0.451`, `u1_k1 = 0.392`) | Held $\ge 0.85$ / Broken $< 0.70$ ($\ge 8$ monoids) |
| **HM.1b** | **BROKEN** | Fails `all_rivals_beaten_median` strictly because `WcWo_noheat` ($\lambda=0$) achieved median `0.870 > 0.840` (pairwise $\mathcal{G} > W_c+W_o = 50.0\%$, though mean `0.835 > 0.822`). Meanwhile $\mathcal{G}(\lambda_0)$ beat `Wo_heat` `36/36 = 100%` (`21/21 = 100%` across 7 monoids with $\|W_c\|/\|W_o\|\ge 0.25$), beat `o` `36/36 = 100%`, beat `Wo` `30/36 = 83.3%`, beat `k1` `25/36 = 69.4%` | Beats all 5 medians & $\ge 70\%$ both pairwise tests / Any median loss or $< 50\%$ pairwise |
| **HM.2** | **HELD** | `gru_lin` median $\cos(G, \mathcal{G}(\lambda_0)) = 0.936$, beat `o` in `19/22 = 86.4%` (`22/24` fitted across `11/12` monoids; `u1_G = 0.927`; note `WcWo_noheat` median `0.942`, mean `0.922 < 0.935`) | Held $\ge 0.90$ & $\ge 70\%$ / Broken $< 0.75$ or $< 50\%$ |
| **HM.3a** | **HELD** | `lstm_mlp` median $\cos_G = 0.877$ (`24/24` fitted, `12/12` monoids; beats all 5 rivals in median & mean) AND `rnn_mlp` median $\cos_G = 0.821$ (`22/24` fitted, `11/12` monoids; beats all 5 rivals in median & mean) | Held both $\ge 0.80$ / Broken either $< 0.65$ ($\ge 6$ monoids each) |
| **HM.3b** | **HELD** | `spec` (Hankel-SVD) closer to $W_o$ than $\mathcal{G}(\lambda_0)$ on `10/12 = 83.3%` of monoids (median $\cos_{W_o} = 0.930$ vs $\cos_G = 0.893$) | Held $\ge 75\%$ / Broken $< 50\%$ ($\ge 8$ monoids) |
| **HM.4** | **HELD** | Across `25/36` fitted group runs (`6/6` fresh groups), `lead_G` matched learned leading irrep in `88.0%` (`gru_lin = 93.3%`, `gru_mlp = 80.0%`) vs energy-only `16.0%` and smooth-only `72.0%`; `3/3` fitted (`6/6` total) on 3-way discriminator `Z12_s1_045` | Held $\ge 75\%$ & beats E,S / Broken $< 50\%$ ($\ge 4$ groups) |
| **HM.5a** | **NEITHER** | Noise ($\eta=0.20$) lowered `kin_norm` in `5/10 = 50.0%` fitted pairs (`4/6` monoids lowered [`515, 103, 512, 409`], `2/6` slightly raised [`65, 127`]; `1/4` groups lowered [`Z11_s2_035`], `3/4` groups raised [`Z7_s3_015, Z8_s3_047, Z7_s2_013`]) | Held $\ge 75\%$ / Broken $< 50\%$ ($\ge 8$ pairs) |
| **HM.5b** | **HELD** | `36/36` `gru_mlp` runs: at step 0, $\cos(G_0, W_c) > \cos(G_0, W_o)$ in `97.2%` (`35/36`; median `0.860` vs `0.243`), and training raises $\cos_{W_o}$ in `100.0%` (`36/36`) | Held $\ge 75\%$ & $\ge 80\%$ / Broken $< 50\%$ either |

### 5.2 Full Arm-by-Arm Summary (`fit >= 0.99`, except `noise` `fit >= 0.90`)

| Arm | Fitted / Total (Automata) | `cos_G` med (mean) | `cos_Wo_heat` med (mean) | `cos_WcWo_noheat` med (mean) | `cos_Wo` med (mean) | `cos_Wc` med (mean) | `cos_o` med (mean) | `cos_k1` med (mean) | `u1_G` med (mean) | `u1_o` med | `u1_k1` med |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `gru_mlp` | `36/36` (`12/12`) | `0.840` (`0.835`) | `0.761` (`0.779`) | `0.870` (`0.822`) | `0.768` (`0.761`) | `0.708` (`0.655`) | `0.605` (`0.568`) | `0.810` (`0.708`) | `0.700` (`0.637`) | `0.451` | `0.392` |
| `gru_lin` | `22/24` (`11/12`) | `0.936` (`0.935`) | `0.906` (`0.904`) | `0.942` (`0.922`) | `0.924` (`0.900`) | `0.486` (`0.570`) | `0.855` (`0.817`) | `0.689` (`0.644`) | `0.927` (`0.883`) | `0.925` | `0.342` |
| `lstm_mlp` | `24/24` (`12/12`) | `0.877` (`0.867`) | `0.839` (`0.817`) | `0.844` (`0.832`) | `0.781` (`0.779`) | `0.641` (`0.624`) | `0.591` (`0.573`) | `0.808` (`0.742`) | `0.800` (`0.738`) | `0.598` | `0.456` |
| `rnn_mlp` | `22/24` (`11/12`) | `0.821` (`0.796`) | `0.707` (`0.707`) | `0.778` (`0.749`) | `0.672` (`0.647`) | `0.774` (`0.730`) | `0.461` (`0.468`) | `0.725` (`0.643`) | `0.561` (`0.489`) | `0.276` | `0.289` |
| `spec` | `12/12` (`12/12`) | `0.893` (`0.881`) | `0.894` (`0.882`) | `0.927` (`0.924`) | `0.930` (`0.932`) | `0.490` (`0.492`) | `0.656` (`0.678`) | `0.922` (`0.910`) | `0.858` (`0.784`) | `0.744` | `0.745` |

- `grp`: `25/36` fitted across `6/6` groups (`gru_lin`: `15/18` across `6` groups, median `cos_G = 0.906`, mean `0.871`; `gru_mlp`: `10/18` across `4` groups, median `cos_G = 0.684`, mean `0.622`). Runs below `0.99`: `gru_lin` (`Z11_s1_048`: `0.9899, 0.9749`; `Z11_s2_035`: `0.8146`); `gru_mlp` (`Z11_s1_048`: `0.8848, 0.9279, 0.8957`; `Z11_s2_035`: `0.9314, 0.8715`; `Z12_s1_045`: `0.9720, 0.9815, 0.8534`).
- `noise`: `19/24` fitted at `>= 0.90` (`monoid`: `12/12` across `6/6`; `group`: `7/12` across `4/6`; below `0.90`: `Z11_s1_048`: `0.7009, 0.7037`; `Z11_s2_035`: `0.7988`; `Z12_s1_045`: `0.6963, 0.8547`).
- `gru_lin` below `0.99`: `mixed id=409` (`0.9738, 0.9516`). `rnn_mlp` below `0.99`: `mixed id=76` (`0.9446, 0.7784`). Zero NaN crashes in any arm.

### 5.3 Post-Hoc Exploratory Diagnostics (Explicitly NOT Pre-Registered)

1. **Architecture-ordered kinetic exchange rate $\lambda^* > 0$:** An exploratory sweep $\lambda \in \{0, 0.25, 0.5, 0.75, 1.0, 1.48, 2.0, 3.0\}$ on saved fitted centroids reveals a strictly positive kinetic optimum ordered monotonically by recurrent state stiffness/gating:
   - `SPEC` (no recurrence): peaks at $\lambda = 0$ ($W_o$: median `0.930`, mean `0.932` vs $\lambda_0$: `0.893` / `0.881`).
   - `GRU-LIN`: MED `0.00:0.942, 0.25:0.945, 0.50:0.946, 0.75:0.945, 1.00:0.944, 1.48:0.936`; MN `0.00:0.922, 0.25:0.934, 0.50:0.941, 0.75:0.944, 1.00:0.944, 1.48:0.935` (`+0.022` mean at $\lambda \approx 0.75\text{--}1.0$).
   - `GRU-MLP`: MED `0.00:0.870, 0.25:0.867, 0.50:0.863, 0.75:0.855, 1.00:0.852, 1.48:0.840`; MN `0.00:0.822, 0.25:0.832, 0.50:0.838, 0.75:0.841, 1.00:0.841, 1.48:0.835` (`+0.019` mean at $\lambda \approx 0.75\text{--}1.0$, while median peaks at `0.00`).
   - `LSTM-MLP`: MED `0.00:0.844, 0.50:0.877, 0.75:0.884, 1.00:0.885, 1.48:0.877`; MN `0.00:0.832, 0.75:0.864, 1.00:0.867, 1.48:0.867` (`+0.041` median / `+0.035` mean over $\lambda = 0$).
   - `RNN-MLP`: MED `0.00:0.778, 0.50:0.796, 1.00:0.821, 1.48:0.821`; MN `0.00:0.749, 1.00:0.792, 1.48:0.796` (`+0.043` median / `+0.047` mean over $\lambda = 0$).
   - **Scientific conclusion:** On irreversible monoids, $W_c + W_o$ already captures the dominant transition geometry (explaining why $\mathcal{G}(\lambda_0)$ beat `Wo_heat` `36/36`), and **the kinetic damping rate $\lambda^*$ is substrate-dependent rather than one fixed universal constant $\lambda_0 = 1.476$**—frozen $\lambda_0$ over-damped `GRU-MLP` relative to $\lambda = 0$ (`HM.1b` BROKEN), while accurately matching `LSTM-MLP` and `RNN-MLP` (`HM.3a` HELD).

2. **Why `HM.5a` failed on group automata (mechanism test of noise):** Inspecting irrep variance shares ($\operatorname{Tr}(P_\rho G)/\operatorname{Tr}(G)$) explains why isotropic state noise $\eta = 0.20$ raised `kin_norm` on `3/4` fitted groups: noiseless `GRU-MLP` already placed `>90%` variance in the lowest-Dirichlet-energy irrep (`r0` on `Z7_s3_015`: `0.905–0.929`; `r1` on `Z7_s2_013`: `0.907–0.926`; `r2` on `Z8_s3_047` s=0,1: `0.907–0.919`), whereas adding $\eta = 0.20$ forced the network to amplify higher-frequency output-carrying modes (`r2` on `Z7_s3_015`: `0.024 -> 0.072`; `r0` on `Z7_s2_013`: `0.023 -> 0.078`; `r0_tr2_ker2` on `Z8_s3_047`: `0.663–0.865`) to preserve readout SNR under additive state perturbation. Thus **isotropic state noise is NOT the physical mechanism that lowers Dirichlet energy in noiseless training**.

### 5.4 What Broke and What This Does NOT Show

- **Pre-registered failures:** `HM.1b` is **BROKEN** (frozen $\lambda_0$ lost on median to unsmoothed `Wc + Wo` on `GRU-MLP`), `HM.1a` is **NEITHER** (`0.840 < 0.85`), and `HM.5a` is **NEITHER** (`5/10`, refuted on 3/4 fitted groups).
- Does **not** yield an architecture-free constant $\lambda_0$: $\lambda^*$ varies monotonically with recurrent architecture (`0` in SPEC, `~0.75` in GRU, `~1.0–1.5` in LSTM/RNN).
- Does **not** test non-recurrent bounded-window sequence architectures (e.g., Causal Transformers) at parity `>= 0.99` fit, nor derive $\mathcal{G}(\lambda)$ or $\lambda^*(\text{arch})$ analytically from SGD/AdamW training dynamics.

## 6. Verification & Rule 7 Acceptance Output

- **Mathlib build & axiom audit (`proofs/lean-mathlib/`):**
  - `lake build MasterPrinciple` -> `exit 0` in `113.46s`.
  - `lake env lean AuditMasterPrinciple.lean` -> `exit 0` in `82.22s`; all 18 audited declarations depend only on `[propext, Classical.choice, Quot.sound]` (zero `sorryAx`).
  - `proofs/lean-mathlib/.lake` removed prior to commit; `git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/` empty.
- **Rule 7 checks:**
  - `python -m cerp.register check` -> `0 problem(s), 46 status note(s)` (`exit 0`; `claims/LEDGER_CHECK.md` reverted after LF/CRLF-only check).
  - `python -m cerp.status --check` -> `exit 0`.
  - `SEMPLEX_LEAN_TIMEOUT=900` (`%TEMP%\semplex_extras_venv\Scripts\python.exe -m pytest -q`) -> `167 passed in 1111.59s (0:18:31)` (`exit 0`).
  - Standalone Lean `v4.12.0` (`Cerp.lean`, `Theory.lean`, `Bounds.lean`, `Closure.lean`, `Inference.lean` + `Audit*.lean`, `.olean` compiled to `%TEMP%`, `leftover .olean in proofs/lean: 0`) -> `leanOk: True`, standard axioms only (`[propext, Classical.choice, Quot.sound]` max, zero `sorryAx`, zero `Lean.ofReduceBool`).
