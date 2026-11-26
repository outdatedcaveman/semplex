# Spike 100: Discriminating Test of the Two-Sided Gramian ($W_c + W_o$) on Operator-Separable `NO_id` Irreversible Automata

**Date:** 2026-11-26 · **Branch:** `gemini/spike-100` · **Status:** pre-registered protocol (`Commit 1`, before `predict()` execution and before any training run) · **Follows:** Spike 99 (`experiments/SPIKE_99_REPORT.md`, frozen at `22b0cf5` / merged PR #14 `904b4a9`).

## 1. Research Question, System Change from Spike 99, and Claim Scope

**Why Spike 100 is a new experimental system (`NO_id` Option A):**
Spike 99 (`UNDERPOWERED / NO VERDICT`) proved that Spike 81's 600-automaton pool contains `0 / 312` fresh irreversible automata satisfying $\max_B \cos(W_c + W_o, B) \le 0.80$ (minimum `0.9037`, minimum $\cos(W_c + W_o, W_o) = 0.8822$). Mathematically, appending an artificial stay-identity letter (`L = k + 1`, `T_id = I`) dilutes $L_{\mathrm{kin}} = \frac{1}{2(k+1)} \sum_a (T_a - I)^\top (T_a - I)$ and shifts both $W_c$ and $W_o$. Spike 100 therefore moves to **ordinary irreversible deterministic finite automata without an artificial stay-identity letter (`NO_id`, `Dl = D`)**, constructed by a frozen, independent-trial operator search conditioned on operator identifiability. This is a substantive change in the experimental system rather than a sampling tweak, and is documented here prior to `predict()`.

**Question:** On operator-separable `NO_id` irreversible DFAs where $W_c + W_o$ disagrees quantitatively ($\max_B \cos \le 0.80$) with every competitor:
1. $W_o$ alone (future observability Gramian),
2. $G(\lambda_0)$ (kinetic heat-kernel filtered two-sided operator, $\lambda_0 = 1.476410$),
3. $o o^\top$ (instantaneous $\sqrt{\pi_{\mathrm{occ}}}$-centered output Gram), and
4. $k_{1,\mathrm{top}} = k_{1,w} k_{1,w}^\top$ (rank-1 outer product of the $t \ge 1$ predictive-kernel top mode),

does a trained GRU's learned state Gramian follow $W_c + W_o$ above null alignments (**H1**) and discriminate $W_c + W_o$ from all four competitors (**H2**)?

**Claim Scope & External-Validity Boundary (Pre-Registered):**
- Conditional inference: Spike 100 evaluates H1 and H2 on a deliberately constructed population of `NO_id` irreversible DFAs conditioned on operator identifiability ($\max_B \cos \le 0.80$, $\min \pi_{\mathrm{occ}} \ge 0.01$, $\|K_1\|_F \ge 10^{-3}$, $\mathrm{eigengap}(K_1) \ge 10^{-3}$). Even a `HELD` result does **not** estimate prevalence across random irreversible DFAs and does **not** establish a universal representation theorem.
- **H1**, **H2**, and **H3** are reported separately. Spike 100 does **not** test **H3** (causal necessity of $W_c + W_o$ during training or intervention).

## 2. Reference Measure ($\pi_{\mathrm{occ}}$) and Trajectory Alignment

Throughout Spike 100, $\pi_{\mathrm{occ}}$ denotes the **finite-horizon post-burn occupancy measure** induced by starting at minimal state `s0`, drawing independent uniform letters over `L` action symbols for `T = 30` steps, and averaging over post-burn indices `t in {5, ..., 29}`:
$$\pi_{\mathrm{occ}} = \frac{1}{T - \mathrm{burn}} \sum_{t=\mathrm{burn}}^{T-1} \delta_{s_0}^\top P^{t+1} = \frac{1}{25} \sum_{t=5}^{29} \delta_{s_0}^\top P^{t+1}, \qquad P = \frac{1}{L}\sum_{a=0}^{L-1} P_a.$$
Because `MP.fast_sample()` advances `q = Dl[X[:, t], q]` before writing `ST[:, t] = q`, `ST[:, 5:]` matches `S81.visit_dist(..., T=30, burn=5)` 1-to-1. Spike 100 does **not** claim $\pi_{\mathrm{occ}} P = \pi_{\mathrm{occ}}$ invariance and logs `stat_l1_defect` $= \|\pi_{\mathrm{occ}}^\top P - \pi_{\mathrm{occ}}\|_1$ plus `markov_spectral_gap` on every automaton.

## 3. Pre-Registered Independent-Trial `NO_id` Pool Search (`predict()`)

Before any neural training:
- **Automaton class (`NO_id`):** no stay-identity letter (`Dl = D`), `L in {3, 4, 5}`, initial states `n_init in {7, 8, 9, 10, 11, 12}`, Moore-minimized (`S81.minimize`) minimal states `m >= 6`, non-constant binary output `O`, at least one non-bijective action letter.
- **Independent-trial search budget:** `N_TRIALS = 200` completely independent deterministic trials `trial_idx = 0..199`, each seeded by `np.random.default_rng(100_500_000 + trial_idx)`. Each trial draws one random `(n_init, L, d, o)` and executes `N_MUT_STEPS = 250` local single-entry mutations (`80%` transition entry, `20%` output bit, sequential `rng` draws) minimizing the lexicographic objective `(n_hard_fails, -min(pi_min, 0.01), max_comp_cos)` and tracking the single lowest-`max_comp_cos` candidate satisfying **all hard eligibility gates**:
  1. Irreversible (`>= 1` non-bijective letter), minimal `m >= 6`, non-constant `O`;
  2. Finite-horizon post-burn occupancy support `min(pi_occ) >= 0.01`;
  3. Non-degenerate predictive kernel `||K_1||_F >= 1e-3` **and** leading eigenvalue gap $\lambda_1(K_1) - \lambda_2(K_1) \ge 10^{-3}$;
  4. Candidate separation $\max_{B \in \{W_o, G(\lambda_0), o o^\top, k_{1,\mathrm{top}}\}} \cos(W_c + W_o, B) \le 0.80$ (never relaxed).
- **1-per-trial emission & deduplication:** Each trial emits at most **1** eligible winner (`None` if no step passed all 4 gates), eliminating shared evolutionary lineage across units. Cross-trial deduplication uses `canonical_aut_sig_guarded(D, O, s0)` (`L <= 6` guard) invoked once per emitted winner. Every trial (initial, best/final, rejection reasons, duplicate flags) is recorded in `experiments/results/spike100_pool_audit.json`.
- **Descriptive `dimH` logging (not gated):** `dimH`, `dimR`, and `dimO` from `S84.head_structure` are logged for stratification rather than gated, avoiding silent exclusion of strongly irreversible synchronizing DFAs (`dimH = 0`).
- **Deterministic stratified selection:** If `N_elig >= 20`, select `N = 20` automata over `(L, m)` strata (`selection_seed = 20261126`) and persist `experiments/results/spike100_predictions.json` + `experiments/results/spike100_selection_lock.json`. If `N_elig < 20`, halt as `UNDERPOWERED / NO VERDICT` without threshold relaxation.
- **Explicit stage denominators:** Reports must separately state `n_search_trials` (`200`), `n_trial_winners_eligible`, `n_unique_eligible`, `n_selected_for_training` (`20`), `n_runs_expected` (`200`), `n_runs_present`, `n_fit_ok`, and `n_gram_valid`.

## 4. Learners, Trajectory Generation, Nulls, and Statistical Criteria

Retains the locked Spike 99 §4–§5 & §8 architecture verbatim on the `NO_id` `20 x 2 x 5 = 200` seed grid:
- **Learners:** `gru_mlp` (primary, `nn.GRU(16, 64)` + 3-layer `Tanh` MLP) and `gru_lin` (secondary, linear readout) + `untrained_gru` step-0 control; `5` seeds per arm (`batch=64, seq_len=30, burn=5, steps=2000, lr=0.004, AdamW(weight_decay=0.0), CosineAnnealingLR(2000), fit_guard=0.99` on `500` trajectories of length `100`).
- **Frozen training & evaluation seeds:** `seed = 100_000 + (0 if arch == "gru_mlp" else 10_000) + 100 * aid + seed_idx` and `eval_seed = 100_000_000 + 100 * aid + seed_idx` (`seed_idx in {0..4}`). Held-out Gram extraction uses `400` trajectories (`eval_seed + 1_000_000` after `500_000` step-0 / `1_000_000` trained fit offsets) of length `30`, discarding `t in {0..4}`, verifying centring `||1_pi^T X||_2 < 1e-8`.
- **Nulls (`10,000` draws each):** Null A (Gaussian $\pi_{\mathrm{occ}}$-weighted, `hidden_dim=64`), Null B (spectrum-preserving Haar orthogonal rotations $U \in O(m-1)$ via sign-corrected QR `sign(0) = +1` with PSD & eigenvalue preservation checks `< 1e-7`), Null C (secondary diagonal in centred subspace).
- **Intention-to-train primary analysis & verdict rules:** All `200` grid slots retained via canonical `normalize_seed_run_record` / `validate_and_complete_seed_grid` (`gram_valid=False, fit_ok=False` -> zero cosine stub). Individual HELD requires `med_target > Null A p95 + 0.05`, `>= 4/5` above Null A `p95`, `D_a >= 0.05`, `>= 4/5` Null B `p <= 0.05`, and `>= 4/5` fit `>= 0.99`. Aggregate `HELD` (`gru_mlp`) requires `>= 14/20` individual HELD, `median_a(D_a) >= 0.05`, 10,000-rep hierarchical bootstrap `ci95_low >= 0.05`, and 10,000-rep aggregate Null B `p_aggregate <= 0.05` on `T = median_a(D_a)` computed via `compute_automaton_D_batch`. Holm–Bonferroni Wilcoxon tests (`alpha = 0.05`) are reported separately.

## 5. Strengthened Provenance & Clean-Tree Lock

1. **Strict native `int` & `arch` validation (`validate_raw_record_provenance`):** Every raw file loaded during `run()` resume (before skipping existing files) and `analyse()` must carry `selection_lock_sha256 == lock["selection_sha256"]`, `candidate_audit_commit_sha == lock["candidate_audit_commit_sha"]`, `arch in ("gru_mlp", "gru_lin")`, and exact native `int` (`type(v) is int`, rejecting `bool`/`float`/`None`) `id`, `seed_idx`, `seed == expected_train_seed(...)`, and `eval_seed == expected_eval_seed(...)`.
2. **Pre-write clean-tree check & dependency source hashes:** In production `predict()`, `verify_clean_working_tree()` checks `git status --porcelain == ""` **before** writing any `spike100_*.json` artifacts. `spike100_selection_lock.json` binds `source_file_sha256s` across `experiments/spike100.py`, `experiments/spike99.py`, `experiments/master_principle.py`, `experiments/spike81.py`, `experiments/spike84.py`, and `experiments/audits/spike99_candidate_audit.py` inside `canonical_selection_lock_hash()`, and `verify_selection_lock()` re-verifies all live source digests on disk at both `run()` and `analyse()`.

## 6. Commands

```powershell
python -m experiments.spike100 predict
python -m experiments.spike100 run
python -m experiments.spike100 analyse
```

## 7. Results & Deviation Log

*(Pre-registered — `predict()`, `run()`, and `analyse()` have not yet been executed.)*
