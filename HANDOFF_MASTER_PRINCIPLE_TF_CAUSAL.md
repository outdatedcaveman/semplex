# Handoff: `gemini/master-principle-tf-causal` — Transformer Head/Layer Resolution, OOD Length Extrapolation, & Powered Causal Inertia

**Branch:** `gemini/master-principle-tf-causal` (cut cleanly from `origin/claude/practical-shannon-oqg60y`)
**Status:** PRE-REGISTERED (Commit 1); training run pending.

## 1. Pre-Registered Scope (`experiments/master_principle_tf_causal.py`)

This branch resolves the four open empirical diagnostics from `gemini/master-principle-transformer` (`HTF.2`, `HTF.3`) and `gemini/master-principle-mech` (`HMM.3`, `HMM.4`) across 140 training runs:

- **Arm 1 (`16` automata × `5` archs = `80` runs, `T_train = 16`, `burn = 4`, `steps = 1200`, `lr = 3e-3` AdamW + cosine decay):**
  - Exact 16-automata diagnostic panel (`8` free monoids `M_11..M_599`, `4` verified `k`-definite `def_k2_m6..def_k4_m8`, `4` cyclic groups `Z11_s1_04a..Z8_s3_023`).
  - Architectures: `tf_lin` (2L Pre-LN CausalTF + Linear head), `tf_mlp` (2L Pre-LN CausalTF + 3L tanh MLP head), `tf_rope_mlp` (2L Pre-LN RoPE CausalTF + 3L tanh MLP), `tf_sw4_mlp` (2L Pre-LN RoPE Sliding-Window `W_1=2, W_2=3`, exact mathematical receptive field `RF=4` verified by zero-difference perturbation check), and `gru_mlp`.
  - Probes BOTH Layer-1 (`L1`) and Layer-2 (`L2`) residuals against `G_sum(λ_kin)`, `W_gm(λ_kin)`, `G(0)`, `G(LAM0)`, `W_o`, `W_c`, and `o`; tests OOD length extrapolation at `T_test ∈ {16, 32, 64}`.
- **Arm 2 (`12` monoids × `5` arms = `60` runs, `T = 16`, `burn = 4`, `steps = 2500`, `lr = 3e-3 -> 3e-4` cosine + `clip_grad_norm_(1.0)`):**
  - Exact 12 `master-principle-mech` monoids (`[467, 583, 110, 358, 308, 532, 350, 535, 578, 352, 449, 52]`).
  - Arms: `leaky_a100` (`α=1.0`), `leaky_a050` (`α=0.50`), `leaky_a025` (`α=0.25`), `vel_warmup` (`α=1.0`, normalized post-burn step-velocity penalty ramped `0 -> 0.05` over steps `1000..1500` then constant `0.05`), and `wd_3e2` (`weight_decay = 3e-2` control).

## 2. Pre-Registered Verdict Rules (`HTC.1`–`HTC.5`)

- **`HTC.1` (Head Confound vs Attention Law):** Among converged (`fit >= 0.90`, `n >= 8`) non-group `tf_mlp` runs at Layer 2 (`L2`), **`HEAD_CONFOUND`** if `>= 9/12` beat `o` (`cos_Gsum_kin > cos_o`), **`ATTENTION_LAW`** if `<= 4/12` beat `o`, else `NEITHER` (also reporting `L1` and `tf_lin` comparisons).
- **`HTC.2` (Strict Finite-Window Dichotomy — `MasterPrincipleWindow.lean`):** On `tf_sw4_mlp` (`RF = 4`), `HELD` if `4/4` `k`-definite monoids (`k <= 4`) achieve `fit >= 0.95` across ALL `T ∈ {16, 32, 64}` AND `4/4` cyclic groups fail (`fit <= 0.50` across ALL `T ∈ {16, 32, 64}`).
- **`HTC.3` (OOD Length Extrapolation `T=16 -> T=64`):** `HELD` if `gru_mlp` achieves `fit_T64 >= 0.90` on `4/4` cyclic groups while `tf_rope_mlp` degrades (`fit_T64 < 0.70`) on `>= 3/4` cyclic groups yet holds `fit_T64 >= 0.90` on `>= 3/4` `k`-definite monoids.
- **`HTC.4` (Powered `HMM.3` — `LeakyRNN` Inertia):** Requiring `>= 8/12` converged triplets (`fit >= 0.90` across all `α ∈ {1.0, 0.50, 0.25}`), `HELD` if `kin_norm` strictly decreases (`1.0 > 0.50 > 0.25`) and `λ_emp` strictly increases on `>= 80%` AND `cos(G_net(0.25), G(λ_kin(0.25))) > cos(G_net(0.25), G(λ_kin(1.0)))` on `>= 75%`.
- **`HTC.5` (Powered `HMM.4` — Warmup Velocity Penalty):** Requiring `>= 8/12` converged pairs (`vel_warmup` & `leaky_a100` `fit >= 0.90`), `HELD` if `vel_warmup` lowers `kin_norm` & raises `λ_emp` on `>= 75%` AND `cos(G_net(vel), G(λ_kin(vel))) >= cos(G_net(vel), G(λ_kin(base)))` on `>= 75%`.
