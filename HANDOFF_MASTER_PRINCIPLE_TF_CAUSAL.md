# Handoff: `gemini/master-principle-tf-causal` — Transformer Head/Layer Resolution, OOD Length Extrapolation, & Powered Causal Inertia

**Branch:** `gemini/master-principle-tf-causal` (cut cleanly from `origin/claude/practical-shannon-oqg60y`)
**Status:** COMPLETE & VERIFIED (Commit 1 pre-registration: `3e62628`).

## 1. Measured Verdicts (`HTC.1`–`HTC.5`)

Machine artifact: `experiments/results/master_principle_tf_causal.json` (`140 / 140` runs completed, `2681.3s`, strict `RF=4` mask verified via zero-difference perturbation check before `run`).

| Hypothesis | Verdict | Exact Quantitative Summary |
|---|---|---|
| **`HTC.1`** | **NEITHER** | Head & Layer resolution of `HTF.2` on converged non-group automata (`T=16`): on `tf_lin` (`n=10`), Layer 1 beats `o` on **`10/10` (`100%`)** (`free`: `cos_Gsum_kin = 0.815`, `cos_Wc = 0.885` vs `cos_o = 0.435`) while Layer 2 drops to **`2/10` (`20%`)** (`cos_o = 0.919–0.975`); replacing ONLY the linear head with a 3-layer tanh MLP (`tf_mlp`, `n=11`) keeps Layer 1 at **`11/11` (`100%`)** beating `o` and raises Layer 2 beating `o` from `20%` (`2/10`) to **`63.6%` (`7/11`)** (`free` `Gsum = 0.850 > o = 0.715`, `k_def` `0.762 > o = 0.585`, `group` `0.859 > o = 0.410`), below the `>= 9/12` `HEAD_CONFOUND` threshold. |
| **`HTC.2`** | **BROKEN** | Strict `RF = 4` sliding-window (`tf_sw4_mlp`, `W_1=2, W_2=3`): `def_k2_m6`, `def_k3_m8_par`, and `def_k3_m8_rst` held exact **`1.000`** across `T ∈ {16, 32, 64}` (`def_k4_m8` `0.941 -> 0.936`), missing `>= 0.95` on `def_k4_m8`; meanwhile `0/4` cyclic groups converged (`0.564–0.811` at `T=16`, `0.569–0.762` at `T=64`, vs `0.999–1.000` for `tf_mlp`/`tf_rope_mlp`), above the strict `<= 0.50` coin-flip floor due to 4-token partial statistical correlations on correlated output bits. |
| **`HTC.3`** | **NEITHER** | OOD length extrapolation (`T_train=16 -> T_test=32, 64`): `gru_mlp` held `0.9998` (`free`) and `1.0000` (`k_def`) at `T=64`, and `0.946` (`T=32`) -> `0.850` (`T=64`) on cyclic groups (`1/4 >= 0.90` at `T=64`). `tf_rope_mlp` dropped to `0.670` mean on cyclic groups (`2/4 < 0.70`) AND also degraded from `1.000` to `0.812` on `k_def` (`0/4 >= 0.90` at `T=64`) due to RoPE OOD phase shift — whereas sliding-window `tf_sw4_mlp` stayed length-invariant on `k_def` (`0.985 -> 0.984`). |
| **`HTC.4`** | **HELD** | **Powered `HMM.3` settlement (`12/12` triplets converged `fit >= 0.90` across all `α ∈ {1.0, 0.50, 0.25}`!):** `mean_fit`: `0.9997 -> 0.9951 -> 0.9763`; `mean_kin_norm`: `0.5249 -> 0.4498 -> 0.4124`; `mean_λ_emp`: `2.899 -> 4.124 -> 4.980`. **`10 / 12` (`83.3%`)** showed strictly monotone `kin_norm` drop & `λ_emp` rise, and **`9 / 12` (`75.0%`)** aligned `G_net(0.25)` closer to `G(λ_kin(0.25))` than to `G(λ_kin(1.0))` (failing only on `MM_350`, `MM_52`, and `MM_535`). |
| **`HTC.5`** | **HELD** | **Powered `HMM.4` settlement (`12/12` converged pairs `fit >= 0.998`, `mean_fit = 0.9992` vs `0.9997`):** Warmup-annealed step-velocity regularization (`μ: 0 -> 0.05`) lowered `kin_norm` and raised `λ_emp` on **`12 / 12` (`100%`)** (`mean_kin`: `0.5249 -> 0.4284`, `mean_λ`: `2.899 -> 4.290`), and **`11 / 12` (`91.7%`)** aligned `G_net(vel)` closer to `G(λ_kin(vel))` than to `G(λ_kin(base))` (preserving `mean cos_G = 0.823` vs `0.841`). By contrast `wd_3e2` control left `kin_norm` (`0.520`) and `λ` (`3.022`) nearly unchanged (`12/12` `mean_fit = 0.9995`). |

## 2. Key Scientific Takeaways

1. **Resolution of the `HTF.2` Transformer Puzzle (`L1` vs `L2` Depth Decomposition):** Prior `HTF.2 = BROKEN` reflected output-layer geometry at Layer 2 under a `Linear` head (`2/10` beat `o`), NOT absence of causal automaton state inside self-attention: Layer 1 of BOTH `tf_lin` (`10/10`) and `tf_mlp` (`11/11`) builds spectral state representations (`cos_Gsum_kin = 0.73–0.85`, `cos_Wc = 0.64–0.89`, `cos_o = 0.12–0.45`), and switching to a 3L MLP head lifts Layer 2 alignment with `G(λ_kin)` over `o` from `20%` (`2/10`) to `63.6%` (`7/11`).
2. **Causal Inertia (`α`) and Post-Warmup Velocity Penalty Cause Direct Travel Along `G(λ)`:** Increasing `steps` from `1000` (`HMM.3`/`HMM.4 = NO VERDICT` in `master-principle-mech`) to `2500` with warmup velocity annealing yields `12/12` convergence on every intervention arm, proving BOTH structural leakiness (`10/12` monotone, `9/12` shifted Gramian) and post-warmup smoothness pressure (`12/12` `λ` increase, `11/12` shifted Gramian) causally shift learned states along the predicted `G(λ)` curve, whereas `weight_decay = 3e-2` does not.
3. **Strict Finite-Window vs RoPE OOD Extrapolation (`MasterPrincipleWindow.lean`):** Local windowed self-attention (`RF = 4`) is length-invariant up to `T = 64` on `k`-definite automata (`k <= 3` holds `1.000`), collapses on `4/4` periodic groups (`0.57–0.76`), while global RoPE degrades at `T = 64` even on `k`-definite automata (`0.812`) unless constrained to finite local relative windows.

## 3. Verification Summary

- `cerp.register check`, `cerp.status --check`, 5 core Lean audits against clean base `7be5346`, `leftover_oleans=0`, and `pytest -q` executed in full Rule-7 check before Commit 2.
