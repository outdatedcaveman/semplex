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

### 7.1 Execution & Stopping Outcome (`experiments/results/spike99.json`)

- **Pre-registration & statistical-lock commits prior to final audit execution (`80f8904`):** `ff9445c` (protocol + blocking candidate-agreement audit code), `73c42fc` (Section 8 execution and statistical lock), `8d00806` (unified `D_a`, zero-similarity stub, full grid, PSD enforcement), and `80f8904` (unconditional `aggregate_null_b_test` assertion, uniform `normalize_seed_run_record` / `normalize_seed_eval`, 200-record postconditions, immutable `spike99_selection_lock.json`, Haar QR zero-diag documentation & test log `spike99_test_run.txt`).
- **Status:** **`UNDERPOWERED`** (`verdict: NO VERDICT`)
- **Eligible automata under $\max_B \cos(W_c + W_o, B) \le 0.80$:** **`0 / 312`** fresh irreversible automata with $\min_q \pi_q > 10^{-4}$ (`0 / 323` even without the $\pi_{\min}$ filter; `0 / 600` across the entire Spike 81 pool).
- **Training runs executed:** **`0`** (`python -m experiments.spike99 run` verified `spike99_selection_lock.json` and halted cleanly per Section 8.A without relaxing `<= 0.80`).
- **Selection lock:** `experiments/results/spike99_selection_lock.json` (`selection_sha256`: `23edf1a06862c3b44facaa8bc46030be5b70e04aa9891adfbc4e55ae6bb7d117`, `candidate_audit_commit_sha`: `80f8904f98baa925c81e5bbb8e8bb0df69054343`).
- **Artifacts:** `experiments/results/spike99_candidate_audit.json`, `experiments/results/spike99_predictions.json`, `experiments/results/spike99_selection_lock.json`, `experiments/results/spike99.json`, `experiments/results/spike99_test_run.txt`.

### 7.2 Blocking Candidate-Agreement & Multi-Null Audit on PR #12 (`master_principle_predictions.json`)

Computing the full pairwise Frobenius cosine matrix across the 12 monoids of §11 (`hidden_dim = 64`, `draws = 10,000` per monoid) reveals that $W_c + W_o$, $W_o$, and $G(\lambda_0)$ are **even more collinear than PR #12 inferred** (median $\cos(W_c + W_o, W_o) = \mathbf{0.9718}$, minimum `0.9424`, maximum `0.9993`), while `o o^T` also agrees strongly with both (`0.8437` and `0.8765`), and only `k1_top` (`0.5219`) separates substantially:

| Candidate A \ Candidate B (median [min, max]) | `WcWo` ($W_c + W_o$) | `Wo` ($W_o$) | `G` ($G(\lambda_0)$) | `o` ($o o^\top$) | `k1_top` ($k_{1,w} k_{1,w}^\top$) | `k1_full` ($K_{\mathrm{fut}, t\ge 1}$, aux) |
|---|---|---|---|---|---|---|
| **`WcWo`** | `1.0000` | `0.9718` [`0.9424`, `0.9993`] | `0.9387` [`0.8791`, `0.9673`] | `0.8437` [`0.7186`, `0.8911`] | `0.5219` [`0.2712`, `0.8996`] | `0.7527` [`0.3776`, `0.9542`] |
| **`Wo`** | `0.9718` [`0.9424`, `0.9993`] | `1.0000` | `0.9254` [`0.8676`, `0.9748`] | `0.8765` [`0.8247`, `0.9771`] | `0.5357` [`0.3505`, `0.9199`] | `0.7489` [`0.4534`, `0.9303`] |
| **`G`** | `0.9387` [`0.8791`, `0.9673`] | `0.9254` [`0.8676`, `0.9748`] | `1.0000` | `0.7914` [`0.5903`, `0.9497`] | `0.4838` [`0.2506`, `0.8519`] | `0.7307` [`0.3482`, `0.9115`] |
| **`o`** | `0.8437` [`0.7186`, `0.8911`] | `0.8765` [`0.8247`, `0.9771`] | `0.7914` [`0.5903`, `0.9497`] | `1.0000` | `0.2477` [`0.0049`, `0.8257`] | `0.3790` [`0.0957`, `0.8321`] |
| **`k1_top`** | `0.5219` [`0.2712`, `0.8996`] | `0.5357` [`0.3505`, `0.9199`] | `0.4838` [`0.2506`, `0.8519`] | `0.2477` [`0.0049`, `0.8257`] | `1.0000` | `0.7733` [`0.6466`, `0.9914`] |

**Per-monoid PR #12 audit (`10,000` draws, actual `hidden_dim = 64`):**

| ID | Kind | `m` | `cos(WcWo, Wo)` | `cos(WcWo, G)` | `cos(WcWo, o)` | `cos(WcWo, k1_top)` | `cos(Wo, G)` | `cos(Wo, o)` | Null A(`G`) med / p95 | Null A(`WcWo`) med / p95 | Null B self(`WcWo`) p95* | Null C self(`WcWo`) p95* |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 65 | free | 5 | 0.9529 | 0.9302 | 0.8911 | 0.8996 | 0.9228 | 0.9771 | 0.9038 / 0.9537 | 0.9787 / 0.9908 | 0.8542 | 0.8323 |
| 127 | mixed | 6 | 0.9625 | 0.9421 | 0.8342 | 0.6582 | 0.9748 | 0.9295 | 0.7206 / 0.8179 | 0.8563 / 0.9214 | 0.7610 | 0.8041 |
| 515 | free | 6 | 0.9699 | 0.9363 | 0.7186 | 0.4059 | 0.8676 | 0.8247 | 0.7841 / 0.8448 | 0.7431 / 0.8054 | 0.8947 | 0.9107 |
| 103 | mixed | 9 | 0.9887 | 0.9646 | 0.8840 | 0.4381 | 0.9646 | 0.8818 | 0.6690 / 0.7399 | 0.6509 / 0.7275 | 0.6072 | 0.5198 |
| 512 | free | 6 | 0.9551 | 0.9544 | 0.8332 | 0.4488 | 0.9574 | 0.8815 | 0.6690 / 0.7679 | 0.7476 / 0.8336 | 0.8250 | 0.7493 |
| 409 | mixed | 7 | 0.9991 | 0.8791 | 0.8485 | 0.3797 | 0.8775 | 0.8587 | 0.7812 / 0.8471 | 0.7177 / 0.7896 | 0.7229 | 0.7551 |
| 584 | free | 7 | 0.9424 | 0.8819 | 0.7794 | 0.6243 | 0.8754 | 0.8492 | 0.7248 / 0.8198 | 0.9190 / 0.9602 | 0.6869 | 0.6605 |
| 70 | mixed | 9 | 0.9809 | 0.9254 | 0.8406 | 0.5657 | 0.9281 | 0.8787 | 0.7533 / 0.8275 | 0.7344 / 0.8067 | 0.6256 | 0.6106 |
| 281 | free | 4 | 0.9993 | 0.9142 | 0.8500 | 0.6466 | 0.9205 | 0.8581 | 0.9203 / 0.9496 | 0.8523 / 0.9143 | 0.9128 | 0.9294 |
| 193 | mixed | 7 | 0.9512 | 0.9673 | 0.8467 | 0.2712 | 0.9334 | 0.8811 | 0.6457 / 0.7351 | 0.7358 / 0.8140 | 0.7383 | 0.7358 |
| 368 | free | 8 | 0.9737 | 0.9453 | 0.8363 | 0.4781 | 0.9213 | 0.8743 | 0.7996 / 0.8689 | 0.8016 / 0.8628 | 0.6761 | 0.6872 |
| 76 | mixed | 9 | 0.9873 | 0.9412 | 0.8572 | 0.5661 | 0.9558 | 0.8682 | 0.6617 / 0.7358 | 0.7399 / 0.8090 | 0.6005 | 0.5947 |

*\*Note: Raw per-seed `G_learned` centroid matrices from `master_principle_raw/` are not tracked on `master`, so Null B/C above report the spectrum-preserving self-orientation benchmark $\cos(W_c+W_o,\, Q(W_c+W_o)Q^\top)$ in $\operatorname{im}(P_\perp)$ (`pr12_null_summary`: Null A(`G`) median-of-medians `0.7390`, median-of-p95s `0.8237`; Null A(`WcWo`) median-of-medians `0.7453`, median-of-p95s `0.8238`; Null B self(`WcWo`) median-of-p95s `0.7306`; Null C self(`WcWo`) median-of-p95s `0.7426`).*

### 7.3 Spike 81 Pool Eligibility & Rejection Audit (`600` Automata)

Full pool breakdown (`experiments/results/spike99_candidate_audit.json:spike81_pool_audit`):
- **Total pool (`S81.build_pool()`):** `600` (`200` `perm`, `200` `mixed`, `200` `free`).
- **Excluded as previously used (`used_in_prior_spike`):** `85` across `spike81`, `spike83`, `spike84`, `spike87`, `master_principle`, `master_principle_mech`, `master_principle_transformer`, `master_principle_tf_causal`.
- **Bijective automata (`bijective_not_irreversible`):** `201` (`200` `perm` + `1` `free` automaton `id = 251`, `m = 5`, whose minimized action letters are all bijective).
- **Isomorphic duplicates (`canonical_aut_sig`):** **`0`** (both under letter-permutation equivalence and fixed-letter order).
- **Effect of $\min_q \pi_q > 10^{-4}$ filter (`low_pi_threshold_effect`):** excludes `24` automata total (`11` fresh irreversible automata: IDs `104, 152, 176, 200, 206, 242, 341, 392, 437, 479, 491`, each with $\min_q \pi_q = 8.2305 \times 10^{-5}$). None of those `11` pass the candidate disagreement filter (`min max_B = 0.9351`, `0 / 11` eligible). No automaton has $\min_q \pi_q \le 10^{-12}$.
- **Fresh irreversible automata with $\min_q \pi_q > 10^{-4}$:** `312` (`323` total fresh irreversible).
- **Candidate collinearity filter ($\max_B \cos(W_c + W_o, B) \le 0.80$):**
  - **Eligible:** **`0 / 312`** (`0 / 323` without $\pi_{\min}$ filter; **`0 / 600`** across the entire pool!).
  - **Rejected:** **`600 / 600`** (`candidate_collinearity_max_cos_gt_0.80`: `600`, `used_in_prior_spike`: `85`, `bijective_not_irreversible`: `201`, `low_stationary_mass_pi_le_1e-4`: `24`).
  - **Observed minimum $\max_B \cos(W_c + W_o, B)$ among fresh $\pi > 10^{-4}$:** **`0.9037`** (`id = 542`).
  - **Observed minimum $\cos(W_c + W_o, W_o)$ among fresh $\pi > 10^{-4}$:** **`0.8822`** (`id = 518`).
  - **Diagnostic sensitivity (never used to relax threshold):**
    - Excluding $G(\lambda_0)$ from $B$ still gives **`0 / 312`** at $\le 0.80$ (`min = 0.8822`).
    - Even across all `399` non-dead irreversible automata including already-used ones, minimum $\max_B = 0.8910$ (`id = 359`) and minimum $\cos(W_c + W_o, W_o) = 0.8684$ (`id = 449`).
    - Even under non-pre-registered unit normalization $\hat{W}_c + \hat{W}_o = W_c/\|W_c\|_F + W_o/\|W_o\|_F$, only `14 / 312` (`< 20`) achieve $\max_B \le 0.80$.

**Stratified summary across all `312` fresh irreversible automata ($\min_q \pi_q > 10^{-4}$):**

| Axis | Bin | Count | Eligible | Min $\max_B \cos$ | Median $\max_B \cos$ | Median $\cos(W_c+W_o, W_o)$ | Median $\|W_c\|/\|W_o\|$ |
|---|---|---:|---:|---:|---:|---:|---:|
| `#states` | `m=4` | 22 | 0 | 0.9388 | 0.9886 | 0.9886 | 0.3089 |
| `#states` | `m=5` | 73 | 0 | 0.9334 | 0.9848 | 0.9791 | 0.3419 |
| `#states` | `m=6` | 59 | 0 | 0.9194 | 0.9754 | 0.9725 | 0.3668 |
| `#states` | `m=7` | 58 | 0 | 0.9092 | 0.9768 | 0.9768 | 0.3124 |
| `#states` | `m=8` | 61 | 0 | 0.9037 | 0.9725 | 0.9725 | 0.3668 |
| `#states` | `m=9` | 39 | 0 | 0.9312 | 0.9712 | 0.9712 | 0.3314 |
| `H(pi)` bits | `[0, 1.5)` | 8 | 0 | 0.9984 | 0.9998 | 0.9998 | 0.0222 |
| `H(pi)` bits | `[1.5, 2.2)` | 59 | 0 | 0.9336 | 0.9831 | 0.9815 | 0.3751 |
| `H(pi)` bits | `[2.2, 2.8)` | 174 | 0 | 0.9037 | 0.9750 | 0.9712 | 0.3480 |
| `H(pi)` bits | `[2.8, inf)` | 71 | 0 | 0.9312 | 0.9759 | 0.9759 | 0.2979 |
| `spectral_gap` | `[0, 0.25)` | 44 | 0 | 0.9256 | 0.9811 | 0.9811 | 0.2647 |
| `spectral_gap` | `[0.25, 0.50)` | 207 | 0 | 0.9037 | 0.9771 | 0.9755 | 0.3463 |
| `spectral_gap` | `[0.50, 1.1)` | 61 | 0 | 0.9312 | 0.9786 | 0.9754 | 0.3677 |
| `\|Wc\|/\|Wo\|` | `[0, 0.25)` | 93 | 0 | 0.9762 | 0.9909 | 0.9909 | 0.1762 |
| `\|Wc\|/\|Wo\|` | `[0.25, 0.50)` | 147 | 0 | 0.9320 | 0.9739 | 0.9721 | 0.3568 |
| `\|Wc\|/\|Wo\|` | `[0.50, 1.0)` | 72 | 0 | 0.9037 | 0.9521 | 0.9414 | 0.6198 |
| `rank(WcWo)` | `rank=3` | 22 | 0 | 0.9388 | 0.9886 | 0.9886 | 0.3089 |
| `rank(WcWo)` | `rank=4` | 73 | 0 | 0.9334 | 0.9848 | 0.9791 | 0.3419 |
| `rank(WcWo)` | `rank=5` | 59 | 0 | 0.9194 | 0.9754 | 0.9725 | 0.3668 |
| `rank(WcWo)` | `rank=6` | 58 | 0 | 0.9092 | 0.9768 | 0.9768 | 0.3124 |
| `rank(WcWo)` | `rank=7` | 61 | 0 | 0.9037 | 0.9725 | 0.9725 | 0.3668 |
| `rank(WcWo)` | `rank=8` | 39 | 0 | 0.9312 | 0.9712 | 0.9712 | 0.3314 |
| `H(out)` bits | `[0, 0.5)` | 23 | 0 | 0.9092 | 0.9823 | 0.9823 | 0.2772 |
| `H(out)` bits | `[0.5, 0.85)` | 90 | 0 | 0.9037 | 0.9774 | 0.9760 | 0.3405 |
| `H(out)` bits | `[0.85, 1.01)` | 199 | 0 | 0.9312 | 0.9780 | 0.9755 | 0.3463 |

**Top 20 lowest-collinearity (all still rejected) fresh irreversible automata (`max_B > 0.80`):**

| Rank | ID | Kind | `m` | `L` | `max_B` | `cos(WcWo, Wo)` | `cos(WcWo, G)` | `cos(WcWo, o)` | `cos(WcWo, k1_top)` | `\|Wc\|/\|Wo\|` | `cos(Wc, Wo)` | Reason |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 542 | free | 8 | 4 | 0.9037 | 0.9005 | 0.9037 | 0.7682 | 0.3784 | 0.7769 | 0.5029 | `max_B > 0.80` |
| 2 | 47 | free | 7 | 4 | 0.9092 | 0.9016 | 0.9092 | 0.6449 | 0.3906 | 0.6710 | 0.4105 | `max_B > 0.80` |
| 3 | 248 | free | 6 | 4 | 0.9194 | 0.9194 | 0.9152 | 0.7656 | 0.4195 | 0.6203 | 0.4613 | `max_B > 0.80` |
| 4 | 482 | free | 6 | 4 | 0.9205 | 0.9205 | 0.8979 | 0.7305 | 0.4287 | 0.6532 | 0.5036 | `max_B > 0.80` |
| 5 | 395 | free | 6 | 4 | 0.9256 | 0.9256 | 0.9037 | 0.7071 | 0.4465 | 0.6479 | 0.5302 | `max_B > 0.80` |
| 6 | 311 | free | 7 | 4 | 0.9270 | 0.9270 | 0.8696 | 0.7405 | 0.6564 | 0.5932 | 0.4808 | `max_B > 0.80` |
| 7 | 500 | free | 9 | 4 | 0.9312 | 0.9041 | 0.9312 | 0.6883 | 0.3835 | 0.6772 | 0.4318 | `max_B > 0.80` |
| 8 | 44 | free | 6 | 4 | 0.9320 | 0.9320 | 0.9042 | 0.8027 | 0.7310 | 0.4803 | 0.3382 | `max_B > 0.80` |
| 9 | 86 | free | 8 | 4 | 0.9323 | 0.9323 | 0.9063 | 0.7741 | 0.7675 | 0.6930 | 0.6067 | `max_B > 0.80` |
| 10 | 179 | free | 5 | 4 | 0.9334 | 0.9163 | 0.9334 | 0.8178 | 0.6961 | 0.5195 | 0.2751 | `max_B > 0.80` |
| 11 | 134 | free | 5 | 3 | 0.9336 | 0.9336 | 0.9208 | 0.7346 | 0.7845 | 0.7862 | 0.6676 | `max_B > 0.80` |
| 12 | 434 | free | 6 | 4 | 0.9342 | 0.9342 | 0.9323 | 0.6995 | 0.5389 | 0.7625 | 0.6586 | `max_B > 0.80` |
| 13 | 272 | free | 6 | 3 | 0.9344 | 0.9082 | 0.9344 | 0.7213 | 0.4498 | 0.7166 | 0.4930 | `max_B > 0.80` |
| 14 | 239 | free | 8 | 4 | 0.9368 | 0.9368 | 0.9253 | 0.7549 | 0.5545 | 0.6770 | 0.6214 | `max_B > 0.80` |
| 15 | 56 | free | 6 | 3 | 0.9372 | 0.9372 | 0.8758 | 0.7390 | 0.4130 | 0.5204 | 0.4619 | `max_B > 0.80` |
| 16 | 2 | free | 6 | 4 | 0.9373 | 0.9373 | 0.9276 | 0.8044 | 0.7689 | 0.8501 | 0.7121 | `max_B > 0.80` |
| 17 | 143 | free | 9 | 4 | 0.9376 | 0.9353 | 0.9376 | 0.7544 | 0.5050 | 0.4628 | 0.3325 | `max_B > 0.80` |
| 18 | 173 | free | 9 | 4 | 0.9379 | 0.9379 | 0.9339 | 0.7589 | 0.3464 | 0.5021 | 0.4386 | `max_B > 0.80` |
| 19 | 29 | free | 7 | 4 | 0.9383 | 0.9094 | 0.9383 | 0.7200 | 0.4055 | 0.6666 | 0.4510 | `max_B > 0.80` |
| 20 | 329 | free | 4 | 3 | 0.9388 | 0.9291 | 0.9388 | 0.7759 | 0.6572 | 0.6044 | 0.5086 | `max_B > 0.80` |

*(Every one of the 600 automata with full `5 x 5` candidate cosines and explicit rejection reason list is stored in `experiments/results/spike99_candidate_audit.json:spike81_pool_audit.all_pool_records`.)*

**Structural Root Cause of Zero Eligibility:**
Because $W_c \succeq 0$ and $W_o \succeq 0$ are both positive semidefinite operators on $\operatorname{im}(P_\perp)$ (dimension $m - 1 \in \{3,\dots,8\}$), their Frobenius inner product is strictly non-negative ($\operatorname{Tr}(W_c W_o) \ge 0$; observed median $\cos(W_c, W_o) \approx 0.52$). Meanwhile, under `master_operators`, $\|W_o\|_F$ dominates $\|W_c\|_F$ on Spike 81's pool (median $\|W_c\|_F / \|W_o\|_F \approx 0.34$, max `0.8702` across fresh $\pi > 10^{-4}$). With $r = \|W_c\|/\|W_o\| < 0.87$ and $c = \cos(W_c, W_o) \ge 0$, $\cos(W_c + W_o, W_o) = \frac{1 + r c}{\sqrt{1 + r^2 + 2 r c}}$ mathematically exceeds `0.88` across the entire pool.

### 7.4 Mandatory Outcome Table (H1 / H2 / H3 / Readout / Reliability Separation)

| Axis | Status | Interpretation |
|---|---|---|
| **H1 (alignment above Null A & Null B)** | **NOT TESTED** (`0` training runs) | Halted pre-training (`N_elig = 0 < 20`). Does NOT support $W_c + W_o$. |
| **H2 (discrimination vs $W_o, G(\lambda_0), o o^\top, k_{1,\mathrm{top}}$)** | **NOT TESTED** (`0` training runs) | Spike 81's pool contains `0` automata where $W_c + W_o$ differs from all competitors by $\cos \le 0.80$. |
| **H3 (causal necessity)** | **NOT TESTED** (out of scope) | Spike 99 does not test causal intervention/necessity. |
| **Readout dependence (`gru_mlp` vs `gru_lin`)** | **NOT TESTED** | No training executed. |
| **Training reliability (fit $\ge 0.99$)** | **NOT TESTED** | No training executed. |
| **Overall Spike 99 Verdict** | **`NO VERDICT` (`UNDERPOWERED`)** | Never promoted; Spike 81's pool lacks discriminating instances for $\max_B \cos(W_c + W_o, B) \le 0.80$. |

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

*(Frozen selection parameters: strata = `(kind, m)`, algorithm = deterministic round-robin over shuffled within-stratum IDs sorted ascending, `selection_seed = 20261125`. `predict()` also persists the immutable cryptographic selection lock `experiments/results/spike99_selection_lock.json` containing the ordered 20 `selected_ids`, canonical automaton signatures, `candidate_audit_commit_sha`, `selection_algorithm`, `selection_seed`, `eligible_strata_inputs`, and `selection_sha256`; `run()` and `analyse()` verify the lock against `spike99_predictions.json` and the rebuilt pool and stamp `selection_lock_sha256` and `candidate_audit_commit_sha` onto every training record and summary output. Also audit and report the exact exclusion count and `pi_min` distribution of the `min(pi_q) > 1e-4` filter.)*

### B. Training Seeds and Failed Runs

- Publish exactly 5 training seeds per condition.
- No replacement seeds.
- Retain every seed in the primary intention-to-train
  analysis.
- Report every fit failure.
- Fit-qualified analysis is secondary only.
- At least 4/5 seeds must achieve accuracy >= 0.99
  for individual HELD eligibility.

*(Frozen training seeds: `seed = 99000 + arch_offset + 100 * aid + seed_idx` for `seed_idx in {0, 1, 2, 3, 4}`, with `arch_offset = 0` for `gru_mlp` and `10000` for `gru_lin`; PyTorch `torch.manual_seed(seed)` and NumPy `np.random.default_rng(seed)`. Every training/missing/invalid record passes through one canonical normalizer `normalize_seed_run_record` that enforces unified `gram_valid=False, fit_ok=False` metadata on all invalid/failed/missing seeds, and `analyse()` enforces the exact 200-record `20 x 2 x 5` postcondition via `validate_and_complete_seed_grid`.)*

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

*(Canonical basis for Null C: standard orthonormal basis `Q0` of `im(P_perp)` constructed by symmetric eigendecomposition of `P_perp`. Both `null_b_rotation_draws` and `aggregate_null_b_test` use `_haar_orthogonal_batch` (`Q * sign(diag(R))` with explicit `sign(0) = +1` convention and `||U^T U - I||_max < 1e-10`), check every source and rotated Gram for PSD (`min_eig >= -1e-8 * scale`) and eigenvalue preservation (`max_eig_err < 1e-7`), and report PSD diagnostics in the outputs. Zero-norm / missing-centroid / non-PSD / malformed / missing-grid runs are normalized through `normalize_seed_run_record` and `normalize_seed_eval` with unified `gram_valid = False, fit_ok = False`, zero similarity (`cosines = 0.0` across all 5 candidates, `margin_D = 0.0`, `p_upper = 1.0`), identically across observed statistics, hierarchical bootstrap, and aggregate Null B in the intention-to-train primary analysis. `aggregate_null_b_test` unconditionally asserts `|observed_T - obs_T_computed| < 1e-12`.)*

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

## 9. Deviation Log & Next Steps

- **Protocol deviations:** None (`0` training runs executed; Section 8.A halted execution deterministically at `N_elig = 0 < 20` without relaxing `max_B <= 0.80`).
- **Post-`22b0cf5` provenance hardening (Collab Thread 2 / PR #14 review):** Hardened `experiments/spike99.py` (`validate_raw_record_provenance` enforced in both `run()` prior to skipping existing raw files and `analyse()` on all raw JSON records, plus non-empty lock/audit hash checks in `verify_selection_lock()`) and added regression tests in `tests/test_spike99.py` (`test_raw_record_provenance_enforcement_on_analyse_and_resume`). Re-recorded only `experiments/spike99.py` in `experiments/FROZEN.json`; `experiments/audits/spike99_candidate_audit.py` and all frozen result/lock/test-log files (`spike99.json`, `spike99_predictions.json`, `spike99_selection_lock.json`, `spike99_candidate_audit.json`, `spike99_test_run.txt`) remain byte-identical to `22b0cf5`, and the `UNDERPOWERED / NO VERDICT` outcome is unchanged.
- **Audit implementation notes:**
  1. `canonical_aut_sig` checks state isomorphism up to action-letter permutations; since `0` duplicates were found even under letter permutations, `0` duplicates exist under fixed-letter order as well.
  2. For PR #12's 12 monoids, `master_principle_raw/` centroid arrays are not committed on `master`, so Null B/C in Section 7.2 measure the spectrum-preserving self-orientation distribution of $W_c + W_o$ inside $\operatorname{im}(P_\perp)$ (verifying strict PSD preservation).
- **Test suite scope note (`experiments/results/spike99_test_run.txt`):** All `11` tests in `tests/test_spike99.py` passed (`EXIT_STATUS=0`), and all `59` tests across the `8` Spike 99 / CERP / master-principle suites plus `cerp.register check` and `cerp.status --check` exited `0`; unfiltered `tests/test_bounds_partial.py` fails `7/10` on this host solely because optional dependency `ortools` is not installed, and unfiltered repo-wide pytest reached 15% at 300s (`0.35 GB` free RAM on this 8 GB host).
- **Why Spike 99 cannot be powered on Spike 81's pool & next step:** Spike 81's 600-automaton pool (with scalar binary outputs and stay-identity letter) cannot separate $W_c + W_o$ from $W_o$ at $\max_B \cos \le 0.80$ because $\|W_c\|_F < \|W_o\|_F$ and $\cos(W_c, W_o) \ge 0$. Any future discriminating test must construct a **new automaton family** outside Spike 81's pool (e.g., reset/merge-heavy non-stationary-dominated or higher-state automata with engineered $\|W_c\|_F \gtrsim \|W_o\|_F$ and $\cos(W_c, W_o) \approx 0$, or relative-scale / Kubo–Ando candidates) under a new pre-registered spike (`Spike 100+`).

