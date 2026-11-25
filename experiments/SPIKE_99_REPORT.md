# Spike 99: Discriminating Test of the Two-Sided Gramian ($W_c + W_o$) on Irreversible Automata

**Date:** 2026-11-25 · **Branch:** `gemini/spike-99` · **Status:** pre-registered protocol (Commit 1, before pool eligibility audit execution and before any training run) · **Follows:** Spike 81 (`experiments/spike81.py`), Master Principle §11 (`experiments/master_principle.py`), PR #12 Triage (`claims/PROPOSED_TRIAGE_2026-11-25.md`), and Independent Reviewer Protocol Specification (`Task 150 / 2026-11-25`).

## 1. Research Question and Claim Scope

**Question:** On irreversible finite deterministic automata where the two-sided Gramian $W_c + W_o$ disagrees quantitatively with all competing candidate operators, does a trained GRU's learned state Gramian follow $W_c + W_o$ (past reachability plus future observability) better than:
1. $W_o$ alone (future observability Gramian),
2. $G(\lambda_0)$ (kinetic heat-kernel filtered two-sided operator, $\lambda_0 = 1.476410$),
3. $o o^\top$ (instantaneous $\sqrt{\pi}$-centered output Gram), and
4. $k_{1,\mathrm{top}} = k_{1,w} k_{1,w}^\top$ (rank-1 outer product of the $t \ge 1$ predictive-kernel top mode)?

**Claim Scope (Pre-Registered Boundary):**
- Applies strictly to **discriminating irreversible automata** satisfying the candidate-disagreement filter below.
- Tests **H1 (alignment above null)** and **H2 (discrimination against competing candidate operators)** only; it does **not** test H3 (causal necessity of $W_c + W_o$ during training or intervention).

## 2. Terminology Corrections from PR #12 Audit (`master_principle_null.py`)

In `claims/PROPOSED_TRIAGE_2026-11-25.md` and `experiments/results/audit_master_principle_null.json`, the summary values reported on the 12 monoids of §11 (`master_principle_predictions.json`) must be stated precisely:
- **`0.74` (`0.7391`)** is the **median across monoids of the per-monoid median under the stationary-weighted Gaussian null** (`64`-d), **not** an absolute "chance level".
- **`0.82` (`0.8229`)** is the **median across monoids of the per-monoid 95th percentiles** under that Gaussian null, **not** a pooled 95th percentile.
- Furthermore, `master_principle_null.py` computed only $\cos(G, B)$ for $B \in \{o o^\top, W_c + W_o, W_o\}$; it did **not** compute candidate-vs-candidate cosines (e.g., $\cos(W_c + W_o, W_o)$), leaving candidate agreement unestablished until the blocking audit in `experiments/audits/spike99_candidate_audit.py` runs.

## 3. Pre-Registered Blocking Candidate-Agreement & Eligibility Audit

Before any training run:
1. **Blocking Candidate-Agreement Audit:** Compute and publish the full $5 \times 5$ pairwise Frobenius cosine matrix among $\{W_c + W_o,\, W_o,\, G(\lambda_0),\, o o^\top,\, k_{1,\mathrm{top}}\}$ (plus full $K_{\mathrm{fut},t\ge 1}$ as auxiliary diagnostic) for:
   - All 12 monoids in `experiments/results/master_principle_predictions.json` (PR #12 audit), and
   - Every automaton in Spike 81's 600-automaton pool (`experiments/spike81.py:build_pool()`).
2. **Exclusion & Deduplication Rules:**
   - Exclude every automaton ID used in prior spikes or experiments (`spike81`, `spike83`, `spike84`, `spike87`, `master_principle`, `master_principle_mech`, `master_principle_transformer`, `master_principle_tf_causal`).
   - Exclude non-irreversible automata (every automaton where all non-identity action letters are bijections).
   - Exclude isomorphic duplicates via canonical `(D, O, s_0)` signature (BFS state relabeling from $s_0$ minimized across all action-letter permutations).
   - Require positive stationary visit support $\min_q \pi_q > 10^{-4}$ under the Spike 81 uniform-letter transition kernel ($T = 30$, burn $= 5$, stay-identity letter included).
3. **Eligibility Filter (Unconditional — Never Relaxed):**
   An automaton is eligible **iff** target $A = W_c + W_o$ satisfies:
   $$\max_{B \in \{W_o,\, G(\lambda_0),\, o o^\top,\, k_{1,\mathrm{top}}\}} \cos(W_c + W_o,\, B) \le 0.80.$$
4. **Full Audit Reporting & Stratification:** Publish every eligible **and** rejected automaton with explicit rejection reasons (`experiments/results/spike99_candidate_audit.json`), stratified by:
   - number of minimal states $m$,
   - stationary entropy $H(\pi)$ (bits),
   - Markov spectral gap $1 - |\lambda_2(M)|$ (and Dirichlet gap $\lambda_1(L_{\mathrm{kin}})$),
   - irreversibility ($\|W_c\|_F / \|W_o\|_F$, non-bijective letter count, min image fraction, non-reversibility defect),
   - Gramian ranks ($\operatorname{rank}(W_c+W_o)$, $\operatorname{rank}(W_o)$, $\operatorname{rank}(W_c)$, $\operatorname{rank}(G)$), and
   - output complexity ($H(o)$ under $\pi$, Krylov observable dimension $\dim \mathcal{O}$, output kinetic norm).
5. **Sample-Size Stopping Rule:** Select $N = 20$ eligible automata (or all eligible if $N_{\mathrm{elig}} \ge 20$). **If fewer than 20 automata qualify ($N_{\mathrm{elig}} < 20$), do NOT relax the $\le 0.80$ threshold and do NOT run training: halt and report `UNDERPOWERED` (`NO VERDICT`).**

## 4. Pre-Registered Learners, Controls, and Learned Gram Definition

If $N_{\mathrm{elig}} \ge 20$:
- **Learners (identical budgets: `hidden_dim = 64`, `emb_dim = 16`, `batch = 64`, `seq_len = 30`, `burn = 5`, `steps = 2000`, `lr = 0.004`, `AdamW(weight_decay = 0.0)` + `CosineAnnealingLR(2000)`, single-threaded torch `OMP_NUM_THREADS = 1`, fit guard $\ge 0.99$ on 500 rollouts of length 100):**
  - **Primary arm (`gru_mlp`):** `nn.GRU(16, d_h)` + 3-layer `Tanh` MLP readout, **5 seeds** per automaton.
  - **Secondary arm (`gru_lin`):** `nn.GRU(16, d_h)` + linear readout, **5 seeds** per automaton.
  - **Control (`untrained_gru`):** step-0 evaluation prior to any optimizer step on all 5 seeds per arm.
  - **No best-seed selection:** all seeds meeting the fit guard are retained; fit pass rates are reported verbatim.
- **Exact Learned State Gram Definition:**
  - Held-out trajectories: $N_{\mathrm{traj}} = 400$, length $T = 30$, post-burn steps $t \in \{5, \dots, 29\}$.
  - State centroids: $\hat{\mu}_s = \mathbb{E}[h_t \mid s_t = s] = \frac{1}{|I_s|} \sum_{(b,t) \in I_s} h_{b,t}$ for each minimal state $s \in Q$.
  - Stationary weighting & centering: with $W = \sqrt{\pi}$, $\mathbf{1}_\pi = W / \|W\|_2$, and $P_\perp = I_m - \mathbf{1}_\pi \mathbf{1}_\pi^\top$, set $\bar{\mu} = \sum_s \pi_s \hat{\mu}_s$, $X = \operatorname{diag}(W)(\hat{M} - \mathbf{1}\bar{\mu}^\top)$, $X_\perp = P_\perp X$, and
    $$G_{\mathrm{learned}} = X_\perp X_\perp^\top.$$
  - Similarity normalization: Frobenius cosine $\cos(G_{\mathrm{learned}}, C) = \langle G_{\mathrm{learned}}, C \rangle_F / (\|G_{\mathrm{learned}}\|_F \|C\|_F)$.
  - **Required state-geometry diagnostics per run:** within-state variance $\mathrm{Var}_{\mathrm{within}}$, between-state variance $\mathrm{Var}_{\mathrm{between}} = \operatorname{Tr}(G_{\mathrm{learned}})$, minimum pairwise centroid distance, state-explained variance fraction $R^2_{\mathrm{state}} = \mathrm{Var}_{\mathrm{between}} / (\mathrm{Var}_{\mathrm{between}} + \mathrm{Var}_{\mathrm{within}})$, and split-half held-out stability $\cos(G_{\mathrm{learned}}^{(1)}, G_{\mathrm{learned}}^{(2)})$ across independent 200-trajectory halves.

## 5. Pre-Registered Null Families and Statistical Criteria

For each automaton and run, compute per-automaton empirical upper-tail $p$-values using $B = 10{,}000$ draws:
$$p = \frac{1 + \#\{\text{null} \ge \text{observed}\}}{B + 1}.$$
Automata are the independent statistical unit; the 5 seeds are nested within each automaton.

- **Null A (Gaussian stationary-weighted, $B = 10{,}000$, primary calibration):** $Z \sim \mathcal{N}(0, 1)^{m \times d_{\mathrm{actual}}}$ using the GRU's **actual** hidden dimension `mdl.hidden_dim` (`64`), $X = P_\perp (\sqrt{\pi} \odot Z)$, $G_{\mathrm{null}} = X X^\top$.
- **Null B (Spectrum-preserving random orientations, $B = 10{,}000$, mandatory robustness):** Haar-random orthogonal $U \in O(m-1)$ applied to $G_{\mathrm{learned}}$ inside the $(m-1)$-dimensional centred subspace $\operatorname{im}(P_\perp)$: $G_{\mathrm{null}} = Q_0 (U (Q_0^\top G_{\mathrm{learned}} Q_0) U^\top) Q_0^\top$.
- **Null C (Diagonal / spectrum-matched in centred subspace, $B = 10{,}000$, secondary):** random permutations of the centred eigenvalues along the canonical centred basis of $\operatorname{im}(P_\perp)$.

### Individual Automaton HELD Criterion (All 4 Required)
1. Per-automaton seed-median $\cos(G_{\mathrm{learned}}, W_c + W_o) > \text{Null A } p_{95} + 0.05$;
2. At least $4/5$ seeds strictly exceed $\text{Null A } p_{95}$;
3. Target $W_c + W_o$ beats **every** competitor $B \in \{W_o, G(\lambda_0), o o^\top, k_{1,\mathrm{top}}\}$ by $\ge 0.05$ on seed median:
   $$D_a = \operatorname{med}_s \cos(G_{a,s}, W_c + W_o) - \max_B \operatorname{med}_s \cos(G_{a,s}, B) \ge 0.05;$$
4. Median per-seed empirical upper-tail $p$ under spectrum-preserving **Null B** satisfies $p_B \le 0.05$.

### Aggregate Verdict Rules (`gru_mlp` Primary Arm, `N >= 20`)
- **HELD** iff **all** of:
  1. $\ge 14 / 20$ (or $\ge \lceil 0.70 N \rceil$) automata individually **HELD**;
  2. Median over automata of $D_a$ satisfies $\operatorname{med}_a D_a \ge 0.05$;
  3. 10,000-rep **hierarchical bootstrap** (resample automata with replacement, then 5 seeds with replacement within each sampled automaton) 95% CI lower bound for $\operatorname{med}_a D_a$ is strictly $> 0$;
  4. Aggregate Null B passes (median per-automaton Null B $p \le 0.05$).
- **BROKEN** if **either**:
  1. Hierarchical bootstrap 95% CI upper bound for $\operatorname{med}_a D_a < 0.05$, **or**
  2. $\le 6 / 20$ automata individually **HELD** **and** aggregate alignment fails the null ($\operatorname{med}_a p_A > 0.05$ or $\operatorname{med}_a p_B > 0.05$).
- **NEITHER:** all other outcomes when $N_{\mathrm{elig}} \ge 20$ (never promoted).
- **UNDERPOWERED / NO VERDICT:** whenever $N_{\mathrm{elig}} < 20$ under $\max_B \cos(W_c + W_o, B) \le 0.80$.
- **Pairwise competitor tests:** paired Wilcoxon signed-rank tests across automata ($W_c + W_o$ vs each of the 4 competitors) with Holm–Bonferroni correction at $\alpha = 0.05$.

## 6. Commands

```powershell
python -m experiments.audits.spike99_candidate_audit
python -m experiments.spike99 predict
python -m experiments.spike99 run
python -m experiments.spike99 analyse
```

## 7. Results

*Pending execution after pre-registration and Commit-2 statistical lock.*

## 8. Commit-2 Amendments: Execution and Statistical Lock

### A. Automaton Selection

If N_elig >= 20:

- Select exactly 20 automata.
- Use deterministic stratified sampling.
- Freeze strata, selection algorithm, and RNG seed
  before selection.
- Publish all selected IDs before training.
- Publish all eligible but unselected IDs.
- No manual substitutions.

If N_elig < 20:
- Halt.
- Report UNDERPOWERED / NO VERDICT.
- No threshold relaxation.

*(Frozen selection parameters: strata = `(kind, m)`, algorithm = deterministic round-robin over shuffled within-stratum IDs sorted ascending, `selection_seed = 20261125`. Also audit and report the exact exclusion count and `pi_min` distribution of the `min(pi_q) > 1e-4` filter.)*

### B. Training Seeds and Failed Runs

- Publish exactly 5 training seeds per condition.
- No replacement seeds.
- Retain every seed in the primary intention-to-train
  analysis.
- Report every fit failure.
- Fit-qualified analysis is secondary only.
- At least 4/5 seeds must achieve accuracy >= 0.99
  for individual HELD eligibility.

*(Frozen training seeds: `seed = 99000 + arch_offset + 100 * aid + seed_idx` for `seed_idx in {0, 1, 2, 3, 4}`, with `arch_offset = 0` for `gru_mlp` and `10000` for `gru_lin`; PyTorch `torch.manual_seed(seed)` and NumPy `np.random.default_rng(seed)`. Analysis enforces the full `selected_ids x arm x 5-seed` grid via `validate_and_complete_seed_grid`, synthesizing explicit failed-run stubs if any grid record is absent.)*

### C. Trajectory Generation

Freeze and publish:

- Initial-state distribution.
- Transition sampling procedure.
- Evaluation RNG seed.
- Burn-in handling.
- Held-out trajectory IDs or reproducible
  trajectory-generation seed.

All competing candidates use identical evaluation
trajectories.

*(Frozen trajectory generator: deterministic initial state fixed at `s0`, independent uniform letter draws over `L` action symbols (including stay-identity letter), training batches `B=64, T=30`, held-out fit check `500` trajectories of length `100` (`eval_seed + 1_000_000`), held-out Gram extraction `400` trajectories of length `30` (`eval_seed + 2_000_000`, `eval_seed = 99_000_000 + 100 * aid + seed_idx`, shared across arms), burn-in `t in {0..4}` discarded and `t in {5..29}` retained. Verify centring invariant `||1_pi^T X||_2 < 1e-8`.)*

### D. Null B Implementation

Construct Q0 as an orthonormal basis of im(P_perp).

Verify:

||Q0.T @ Q0 - I||_F < 1e-8
||Q0 @ Q0.T - P_perp||_F < 1e-8

For each draw:

- Generate an independent Haar-random U in O(m-1).
- Randomize the centred learned Gram.
- Verify PSD and eigenvalue preservation.
- Record maximum numerical eigenvalue error.

Use 10,000 independent draws per run.

Individual Null B robustness:
At least 4/5 seeds must have p_B <= 0.05.

*(Canonical basis for Null C: standard orthonormal basis `Q0` of `im(P_perp)` constructed by symmetric eigendecomposition of `P_perp`. Zero-norm / missing-centroid / missing-grid runs are flagged `gram_valid = False` and retained as failed runs with unified zero similarity (`cosines = 0.0` across all 5 candidates, `margin_D = 0.0`, `p_upper = 1.0`) identically across observed statistics, hierarchical bootstrap, and aggregate Null B in the intention-to-train primary analysis. `null_b_rotation_draws` enforces both eigenvalue preservation (`max_eig_err < 1e-7`) and PSD (`min_eig >= -1e-8 * scale`).)*

### E. Aggregate Statistical Test

Primary discrimination statistic:

T = median_a(D_a), where D_a = median_s(cos_{a,s,target}) - max_c median_s(cos_{a,s,c})

computed via a single shared canonical helper (`compute_automaton_D_batch`) across observed summaries, hierarchical bootstrap replicates, and aggregate Null B replicates.

Construct 10,000 aggregate Null B replicates.

For every replicate:
- Independently randomize each automaton/seed Gram.
- Recompute seed-level candidate similarities.
- Recompute D_a.
- Recompute T using the identical aggregation procedure.

Aggregate empirical p-value:

p_aggregate =
(1 + count(T_null >= T_observed)) / 10001

Do not use the median of individual p-values
as an aggregate significance test.

### F. Strengthened Aggregate HELD

In addition to all existing requirements:

The lower bound of the 95% hierarchical bootstrap
confidence interval for median_a(D_a) must be >= 0.05.

Bootstrap:
- 10,000 replicates.
- Resample automata first.
- Resample their 5 seeds second.
- Percentile 95% confidence interval.
- Preserve candidate pairing within seeds and recompute `D_a = median_s(cos_{a,s,target}) - max_c median_s(cos_{a,s,c})` per replicate using the identical shared statistic function.

### G. Mandatory Interpretation

Report H1, H2, and H3 separately.

- H1: alignment above the specified null.
- H2: discrimination against every competitor.
- H3: causal necessity (not tested by Spike 99).

H1 passing without H2 does NOT confirm
the two-sided Gramian hypothesis.

Null B passing without Null A does NOT
confirm the hypothesis.

Fit-qualified results cannot replace
the intention-to-train primary analysis.

NEITHER and UNDERPOWERED are never
described as confirmation.

### H. Reproducibility

Publish:
- RNG seeds and implementations.
- Candidate construction formulas.
- Normalization and centering conventions.
- Zero-norm and missing-value policies.
- Every excluded and failed run.
- Complete deviation log.

No changes to primary thresholds,
selection rules, or statistical procedures
after the first training run.

