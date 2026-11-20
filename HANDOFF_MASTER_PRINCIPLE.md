# Pre-Registered Master Principle Protocol & Handoff (`gemini/master-principle`)

**Date:** 2026-11-20 · **Branch:** `gemini/master-principle` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`) · **Status:** PRE-REGISTRATION (committed before any neural training run in `experiments/master_principle.py`).

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

## 5. Results (Pending — to be populated after runs)

*Pending execution after pre-registration commit.*
