# Master Principle Transformer Handoff (`gemini/master-principle-transformer`)

**Branch:** `gemini/master-principle-transformer` (cut from `origin/claude/practical-shannon-oqg60y` @ `7be5346`)
**Targets:**
1. Formalize in Lean 4 + Mathlib `v4.12.0` (`proofs/lean-mathlib/MasterPrincipleWindow.lean`) the exact finite-window `k`-definite equivalence vs periodic-group obstruction (`IsDefinite δ k` collapses every `>= k`-word to an exact bounded suffix map `windowState δ q₀ k` and collapses initial distribution pushforwards to a point mass, whereas every nontrivial bijective/group automaton violates `IsDefinite δ k` for all `k : ℕ`).
2. Pre-register and execute a horizon `T = 16` (`burn = 4`) architectural comparison of 2-layer Pre-LN Causal Transformer (`causal_tf`, zero recurrent hidden carry-over) vs `gru_mlp` vs `rnn_mlp` vs non-learned `spec` across `16` disjoint automata (`8` fresh `free` monoids, `4` verified `k`-definite reset monoids `k ∈ {2, 3, 4}`, `4` fresh cyclic groups).

## Lean 4 Mathlib Verification (`MasterPrincipleWindow.lean` & `AuditMasterPrincipleWindow.lean`)

- `lake build MasterPrincipleWindow`: `exit=0` (`17.83s`)
- `lake env lean AuditMasterPrincipleWindow.lean`: `exit=0`
- Audited theorems (all strictly `[]`, `[propext]`, `[propext, Quot.sound]`, or `[propext, Classical.choice, Quot.sound]`):
  - `MasterPrincipleWindow.run_append`
  - `MasterPrincipleWindow.definite_monotone`
  - `MasterPrincipleWindow.definite_depends_only_on_suffix`
  - `MasterPrincipleWindow.definite_window_map_exact`
  - `MasterPrincipleWindow.run_bijective_of_bijective`
  - `MasterPrincipleWindow.periodic_group_not_definite`
  - `MasterPrincipleWindow.definite_reset_pushforward_const`

## Pre-Registered Scope, Hyperparameters, & Verdict Criteria (Rule 5 — Committed Prior to Execution)

- **Horizon & Operators (`T_SEQ = 16`, `BURN = 4`, `T_OP = 16`, `GAMMA_C = 0.6`, `GAMMA_O = 0.7`, `LAM0 = 1.476410...`)**
- **Disjoint 16-automaton panel (`experiments/results/master_principle_transformer_predictions.json`):**
  - `8` fresh `free` monoids (exact reserved set from `master-principle-mech`): `['M_11', 'M_35', 'M_68', 'M_140', 'M_146', 'M_317', 'M_380', 'M_599']`
  - `4` programmatically verified `k`-definite reset monoids (`m ∈ {6, 8}`, exact `k ∈ {2, 3, 4}`, zero stay-identity letter): `['def_k2_m6', 'def_k3_m8_par', 'def_k3_m8_rst', 'def_k4_m8']`
  - `4` fresh discriminating cyclic groups (disjoint from Spikes `77/78`, `master-principle`, and `master-principle-mech`): `['Z11_s1_04a', 'Z12_s1_015', 'Z7_s2_016', 'Z8_s3_023']`
- **Architectures (`d_model = 64`):**
  - `causal_tf`: 2L Pre-LN Causal Transformer (`nhead = 4`, `d_ff = 128`, GELU, causal mask, learned token + pos embeddings, linear readout, `lr = 3e-3`, `steps = 2000`; sanity-checked on separate non-eval `2`-definite 4-state toy automaton -> `fit = 1.0000` in `64.3s`).
  - `gru_mlp`: GRU(64) + 3-layer tanh MLP (`lr = 4e-3`, `steps = 1200`).
  - `rnn_mlp`: orthogonal-init Elman tanh RNN(64) + 3-layer tanh MLP (`lr = 4e-3`, `clip_norm = 1.0`, `steps = 1500`).
  - `spec`: exact Hankel-SVD baseline (`T = 16`).

**Pre-Registered Hypotheses (`HELD` / `NEITHER` / `BROKEN`):**
- **`HTF.1` (Zero recurrent stiffness class prediction):** Across matched `fit >= 0.90` `free + k_definite` automata (`>= 8` pairs), `kin_norm(CausalTF) > kin_norm(RNN-MLP)` AND `lam_emp(CausalTF) < lam_emp(RNN-MLP)` on `>= 75%` of pairs (`< 50%` `BROKEN`).
- **`HTF.2` (`G(λ_emp)` vs raw observable `o` on `CausalTF`):** On `>= 6` discriminating `fit >= 0.90` `free + k_definite` automata where `cos(G(λ_emp), o) < 0.95`, `cos(G_tf, G(λ_emp)) > cos(G_tf, o)` on `>= 75%` (`< 50%` `BROKEN`).
- **`HTF.3` (`k`-definite vs periodic-group fit dichotomy):** `mean_fit(CausalTF, k_definite) >= 0.95` AND `mean_fit(CausalTF, k_definite) > mean_fit(CausalTF, group) + 0.05` (`HELD`, `<= group` `BROKEN`).
- **`HTF.4` (`G(0)` vs `G(LAM0)` boundary test for zero-inertia attention):** Across `>= 8` `fit >= 0.90` `free + k_definite` automata, un-smoothed `G(0) = P_perp(W_c + W_o)P_perp` beats high-inertia `G(LAM0)` in Gram cosine on `CausalTF` on `>= 75%` of automata (`< 50%` `BROKEN`).

*(Status: Pre-registered; training arms pending execution.)*