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

*(Status: Executed, analysed, AND full Rule 7 verified.)*

## Measured Results (`experiments/results/master_principle_transformer.json`, `64/64` runs completed)

### Pre-Registered Verdicts

| Hypothesis | Verdict | Exact Quantitative Evidence |
| :--- | :---: | :--- |
| **`HTF.1`** (Zero recurrent stiffness class shift) | **`HELD`** | **`9 / 12` (`0.750`)** non-group automata have BOTH `kin_norm(CausalTF) > kin_norm(RNN-MLP)` AND `lam_emp(CausalTF) < lam_emp(RNN-MLP)` (`7/8` `free` monoids; `non_group` `med_kin = 0.8721` vs `0.6403`, `med_lam = 0.136` vs `0.581`; and `4/4` groups `med_lam = 0.703` vs `4.411`) |
| **`HTF.2`** (`G(λ_emp)` vs raw observable `o` on `CausalTF`) | **`BROKEN`** | Only **`1 / 12` (`0.0833`)** discriminating non-group automata beat `o`! Mean `CausalTF` final residual stream aligns closest to instantaneous `o` (`0.9460` non-group, `0.9779` `k_definite`) > `Wo` (`0.8590`) > `G(λ_emp)` (`0.7763`) > `G(0)` (`0.7596`) > `Wc` (`0.4622`), whereas `GRU-MLP` (`cos_o = 0.5774 < G_emp = 0.9124`) and `RNN-MLP` (`cos_o = 0.4413 < G_emp = 0.8541`) store rich mixed-predictive + past-reachability structure |
| **`HTF.3`** (`k`-definite vs periodic-group fit at `T = 16`) | **`NEITHER`** | `mean_fit(k_definite) = 1.0000` (`4/4` exact `1.0`), `mean_fit(group) = 0.9999` (`Z11_s1_04a = 0.9998`, `Z12_s1_015 = 0.9998`, `Z7_s2_016 = 1.0`, `Z8_s3_023 = 1.0`), diff `+0.00008 < 0.05`: fixed `T = 16` full self-attention suffices for 2L 4-head Pre-LN CausalTF to learn cyclic sums without length extrapolation |
| **`HTF.4`** (`G(0)` vs `G(LAM0)` boundary on `CausalTF`) | **`HELD`** | **`11 / 12` (`0.9167`)** fitted non-group automata obey `cos(G_tf, G(0)) > cos(G_tf, G(LAM0))` (`0.7596` vs `0.6577` overall; `0.6446` vs `0.5018` on `k_definite`), whereas `GRU-MLP` and `RNN-MLP` align closer to `G(LAM0)` than `G(0)` on `free` and `group` classes |

### Cross-Architecture Geometry Comparison (`T = 16, burn = 4`, `fit >= 0.90`)

| Arch | Family (`n_fitted`) | `mean(fit)` | `med(kin)` | `med(λ_emp)` | `cos_o` | `cos_Wo` | `cos_Wc` | `cos_G0` | `cos_G_lam0` | `cos_G_emp` |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `causal_tf` | `free (8/8)` | `0.9660` | `0.7402` | `0.401` | **`0.9300`** | `0.8487` | `0.4789` | `0.8170` | `0.7356` | `0.8393` |
| `gru_mlp` | `free (8/8)` | `1.0000` | `0.6489` | `1.122` | `0.6324` | `0.7700` | `0.7907` | `0.8556` | `0.8831` | **`0.9139`** |
| `rnn_mlp` | `free (8/8)` | `1.0000` | `0.5568` | `1.200` | `0.4598` | `0.6294` | **`0.8794`** | `0.7612` | `0.8466` | `0.8774` |
| `spec` | `free (8/8)` | `1.0000` | `0.6873` | `-0.174` | `0.7275` | **`0.9593`** | `0.5962` | `0.9495` | `0.8721` | `0.9625` |
| `causal_tf` | `k_def (4/4)` | `1.0000` | `1.0160` | `-0.129` | **`0.9779`** | `0.8796` | `0.4288` | `0.6446` | `0.5018` | `0.6503` |
| `gru_mlp` | `k_def (4/4)` | `1.0000` | `0.8678` | `0.784` | `0.4675` | `0.7446` | `0.8096` | `0.8606` | `0.8741` | **`0.9093`** |
| `rnn_mlp` | `k_def (4/4)` | `1.0000` | `1.0214` | `-0.118` | `0.4042` | `0.5847` | `0.8002` | `0.7923` | `0.7261` | **`0.8077`** |
| `spec` | `k_def (4/4)` | `1.0000` | `1.0419` | `-0.208` | `0.7626` | **`0.9754`** | `0.7108` | `0.8797` | `0.7173` | `0.8816` |
| `causal_tf` | `group (4/4)` | `0.9999` | `0.4604` | `0.703` | **`0.9365`** | `0.8112` | `0.2474` | `0.8062` | `0.7743` | `0.8147` |
| `gru_mlp` | `group (4/4)` | `1.0000` | `0.2133` | `3.763` | `0.3731` | `0.5620` | `0.3587` | `0.5909` | `0.6968` | **`0.7692`** |
| `rnn_mlp` | `group (4/4)` | `0.9998` | `0.2014` | `4.411` | `0.3532` | `0.5400` | `0.4693` | `0.5821` | `0.7282` | **`0.8367`** |
| `spec` | `group (4/4)` | `1.0000` | `0.5259` | `-0.153` | `0.5832` | **`0.8990`** | `0.2030` | `0.8897` | `0.8401` | `0.8895` |

## What This Does NOT Show (Architectural Boundary Discovery)

- **Self-attention residual stream is NOT governed by `G(λ)`:** `HTF.2` broke cleanly (`1/12 = 8.3%`). Because `CausalTF` reads bounded past inputs directly in attention heads and maps its final layer through a single `Linear` projection, its final residual centroids sit overwhelmingly along instantaneous output `o` (`0.93–0.98`) + weak `Wo` (`0.81–0.88`), dropping past-reachability `Wc` (`0.25–0.48`) and predicting the exact sign shift (`HTF.1`: higher `kin_norm` / lower `λ_emp`, `HTF.4`: `G(0) > G(LAM0)` `11/12`), marking the sharp scope boundary of `G(λ)` (recurrent bottlenecks `GRU`/`LSTM`/`RNN`, not final-layer Pre-LN attention residuals).
- **Length extrapolation beyond `T_train = 16`:** In-distribution at fixed `T = 16` with `pos_emb(16)`, 2L 4-head attention fits periodic cyclic groups to `0.9999`; `MasterPrincipleWindow.periodic_group_not_definite` predicts breakdown under out-of-distribution `T > T_train` or depth/head caps, not fixed `T = 16` capacity.
- **Hidden-layer / attention-key internal states:** Only the final transformer block's residual stream was measured; intermediate block-1 or concatenated `(Q, K)` attention representations were not tested.
- **`proofs/lean/` unchanged:** Core Cerp Lean proofs remain untouched; Mathlib proofs live strictly in `proofs/lean-mathlib/`.

## Rule 7 Verification (Observed Outputs)

- `python -m cerp.register check`: `exit=0` (`0 problem(s), 46 status note(s)`).
- `python -m cerp.status --check`: `exit=0`.
- `git diff origin/claude/practical-shannon-oqg60y -- proofs/lean/`: empty (`LEAN_DIFF_LEN=0`).
- Lean 4.12.0 audits against `proofs/lean/` core `.olean`s: `Audit.lean`, `AuditTheory.lean`, `AuditBounds.lean`, `AuditInference.lean`, `AuditClosure.lean` all `exit=0`, standard axioms only, `leftover_oleans=0`.
- Lean Mathlib `v4.12.0`: `lake build MasterPrincipleWindow` `exit=0` (`17.83s`), `AuditMasterPrincipleWindow.lean` `exit=0` (`7/7` theorems strictly `[]`, `[propext]`, `[propext, Quot.sound]`, or `[propext, Classical.choice, Quot.sound]`); `proofs/lean-mathlib/.lake` removed cleanly (`DOT_LAKE_PRESENT=False`).
- `SEMPLEX_LEAN_TIMEOUT=900 pytest -q`: **`167 passed in 713.07s (0:11:53)`** (`exit=0`).