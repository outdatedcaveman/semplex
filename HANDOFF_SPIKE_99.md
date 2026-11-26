# Handoff: Spike 99 (`gemini/spike-99`, Task G-A)

**Date:** 2026-11-25 · **Branch:** `gemini/spike-99` (cut from `origin/master` @ `b503dad`) · **Status:** `UNDERPOWERED` / `NO VERDICT` (`0` training runs executed per pre-registered Section 8.A halting rule).

## What Was Done

1. **Pre-registration & Statistical Lock (Committed BEFORE final audit execution `80f8904`):**
   - Commit `ff9445c`: Pre-registered `experiments/SPIKE_99_REPORT.md` plus `experiments/audits/spike99_candidate_audit.py`, `experiments/spike99.py`, and `tests/test_spike99.py`, incorporating all 11 initial ChatGPT review changes (exact null terminology, empirical upper-tail $p = (1 + \#\{\text{null} \ge \text{obs}\})/(B+1)$, Nulls A/B/C with 10,000 draws and actual GRU `hidden_dim = 64`, strict $\max_B \cos(W_c + W_o, B) \le 0.80$ eligibility without relaxation, 5 seeds $\times$ 2 readouts + untrained control, $\mu_s$ learned Gram with within/between variance / $R^2_{\text{state}}$ / split-half stability, hierarchical bootstrap, Holm–Bonferroni $\alpha = 0.05$, and H1/H2 vs H3 scope separation).
   - Commit `73c42fc`: Folded in all Commit-2 Section 8 amendments from ChatGPT's pre-registration review (intention-to-train 5-seed retention, $\ge 4/5$ fit & Null B $p \le 0.05$, 10,000 aggregate Null B replicates for $T = \operatorname{med}_a D_a$, strengthened `ci95_low >= 0.05`, `||Q0^T Q0 - I||_F < 1e-8`, `||Q0 Q0^T - P_perp||_F < 1e-8`, eigenvalue-preservation checks, `||1_pi^T X||_2 < 1e-8`, deterministic stratified sampling, shared held-out evaluation seed, and `min(pi) > 1e-4` sensitivity tracking).
   - Commit `8d00806`: Unified `compute_automaton_D_batch` / `compute_automaton_D_from_cos_matrix`, unified zero-similarity stub, enforced `selected_ids x arm x 5-seed` grid, enforced strict PSD checks, and expanded unit tests.
   - Commit `80f8904`: Added unconditional `|observed_T - obs_T_computed| < 1e-12` assertion and per-rotation PSD checks/diagnostics in `aggregate_null_b_test`, unified canonical failed-seed normalization (`normalize_seed_run_record` & `normalize_seed_eval` setting `gram_valid=False, fit_ok=False`), explicit 200-record (`20 x 2 x 5`) postconditions, immutable selection lock (`experiments/results/spike99_selection_lock.json`), explicit Haar QR sign-correction convention (`Q * sign(diag(R)), sign(0)=+1`) + verification, and complete test evidence (`experiments/results/spike99_test_run.txt`).

2. **Blocking Candidate-Agreement & Spike 81 Pool Eligibility Audit:**
   - **PR #12 (`master_principle_predictions.json`, 12 monoids):** Computed the omitted $5 \times 5$ pairwise cosine matrix (plus `k1_full` auxiliary). Median $\cos(W_c + W_o, W_o) = \mathbf{0.9718}$ (range `0.9424`–`0.9993`), $\cos(W_c + W_o, G(\lambda_0)) = 0.9387$, $\cos(W_o, G(\lambda_0)) = 0.9254$, $\cos(W_c + W_o, o o^\top) = 0.8437$, $\cos(W_c + W_o, k_{1,\mathrm{top}}) = 0.5219$. Null A (`10,000` draws, `hidden_dim = 64`) median-of-medians = `0.7390` (`WcWo`: `0.7453`), median-of-p95s = `0.8237` (`WcWo`: `0.8238`).
   - **Spike 81 Pool (`600` automata):** Excluded `85` previously used IDs, `201` bijective automata (`200` `perm` + `1` `free` `id = 251`), `0` isomorphic duplicates, and `24` with $\min_q \pi_q \le 10^{-4}$ (`11` fresh irreversible, all with `max_B >= 0.9351`, `0` eligible). Out of the `312` fresh irreversible automata with $\min_q \pi_q > 10^{-4}$ (`323` total fresh irreversible), **`0 / 312` satisfy $\max_B \cos(W_c + W_o, B) \le 0.80$** (minimum observed `0.9037` on `id = 542`; minimum $\cos(W_c + W_o, W_o) = 0.8822$ on `id = 518`).
   - **Outcome:** Halted per Section 8.A without relaxing the `0.80` bar (`0` training runs executed; `status = UNDERPOWERED`, `verdict = NO VERDICT`).

3. **Artifact Freezing & Proposed Claim:**
   - Frozen in `experiments/FROZEN.json`: `experiments/spike99.py`, `experiments/audits/spike99_candidate_audit.py`, `experiments/results/spike99.json`, `experiments/results/spike99_predictions.json`, `experiments/results/spike99_selection_lock.json`, `experiments/results/spike99_candidate_audit.json`, `experiments/results/spike99_test_run.txt`.
   - Added §29 to `claims/PROPOSED.md` per the `claims/PROPOSED_TRIAGE_2026-11-25.md` promotion checklist.

## Acceptance Checks

- `python -m pytest -v --tb=short tests/test_spike99.py` -> `11 passed in 25.98s` (`EXIT_STATUS=0`)
- `python -m pytest -v --tb=short tests/test_spike99.py tests/test_register.py tests/test_status.py tests/test_kernel.py tests/test_ledger_and_pipeline.py tests/test_master_principle_final_synthesis.py tests/test_master_principle_grand_closure.py tests/test_warrants.py` -> `59 passed in 68.89s` (`EXIT_STATUS=0`)
- `python -m cerp.register check` -> `0 problem(s), 46 status note(s)` (`EXIT_STATUS=0`)
- `python -m cerp.status --check` -> exit `0`
- `python -m experiments.spike99 predict && python -m experiments.spike99 run && python -m experiments.spike99 analyse` -> `status=UNDERPOWERED, n_eligible=0, n_training_runs_executed=0, lock_sha=23edf1a06862`
- `git diff --check` -> exit `0`
- *Scope note:* Unfiltered `tests/test_bounds_partial.py` fails `7/10` (`ModuleNotFoundError: No module named 'ortools'`), and unfiltered repo-wide pytest reached 15% at 300s (`0.35 GB` free RAM on this 8 GB host).

## What Failed / Remaining Blockers

- **Pool obstruction (no failure in code):** Spike 81's 4–9 state random automaton pool cannot produce discriminating instances where $\max_B \cos(W_c + W_o, B) \le 0.80$ because both $W_c, W_o \succeq 0$ (`cos(W_c, W_o) >= 0`) and $\|W_o\|_F$ exceeds $\|W_c\|_F$ across all 323 fresh irreversible automata. Testing $W_c + W_o$ vs $W_o$ requires synthesizing an out-of-pool family (where $\|W_c\|_F \gtrsim \|W_o\|_F$ and $W_c \perp W_o$) under a fresh pre-registered spike.
