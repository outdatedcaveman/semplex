# Spike 16 Report — Width-Coarsening (`H-D`), XOR6 Grokking (`H-C`), Depth-3 Separation (`H-E`), and Scaled `ur_compiler` Benchmarks

**Date:** 2026-11-13  
**Script:** [spike16_scale_and_coarsening.py](file:///C:/Users/bruno/Claude%20Code/semplex/experiments/spike16_scale_and_coarsening.py)  
**Raw output:** [spike16_results.json](file:///C:/Users/bruno/Claude%20Code/semplex/experiments/spike16_results.json)  
**Trust status:** Untrusted empirical runs (JAX 0.12.0.1 + OR-Tools CP-SAT 9.15.6755 in `%TEMP%\semplex_extras_venv`), except where noted as Lean-certified.

---

## 1. Local Learning Rules Diagnostic (`test_localrules.py`)

Diagnosed the intermittent `0.875 < 0.9` failure in `tests/test_localrules.py::test_search_keeps_a_working_rule_working` (without relaxing the `0.9` assertion):
- Observed CEM run: `hist: [[0.0419, 0.917], [0.0326, 1.0], [0.035, 0.917], [0.0395, 0.875]]`, `a[bp]: 1.0`.
- Pure backpropagation (`warm`) across 20 random initialization batches achieved `mean = 0.9521`, `min = 0.875` (`21/24`), `max = 1.0`.
- **Conclusion:** `cem_search` did not drop backprop (`a[bp] == 1.0`); the failure is Monte-Carlo initialization variance on `rng(1)` generation 3.

---

## 2. `H-A` & `H-D` (Cammarata Width-Coarsening) at $n = 8$

Target: $f(x_0..x_7) = (x_0 \oplus x_1 \oplus x_2 \oplus x_3) \land ((x_4 \lor x_5) \oplus (x_6 \land x_7))$, canonical encoder code bit $c(x_0..x_3) = x_0 \oplus x_1 \oplus x_2 \oplus x_3$.

- **`ur_compiler.compile_profile_factored`:** `decomposed=True`, `profile_rank=1`, `circuit_cost={"gates": 36, "depth": 10}`, `atlas_min_neurons=9`, `tnet_nodes=9`, runtime `0.0524s`.
- **JAX `tanh` MLPs (5 seeds each, 800 Adam steps, L2 `1e-4`):**

| Width | Mean Acc (Min–Max) | Max Single-Unit `|corr(h_j, c)|` | Subspace Linear Probe $R^2(H \to c)$ |
|---:|---:|---:|---:|
| 4 | 0.8289 (0.6875–0.9453) | 0.1972 | 0.2805 |
| 8 | 0.9945 (0.9883–1.0000) | 0.3713 | 0.6912 |
| 16 | 1.0000 (1.0000–1.0000) | 0.3463 | 0.9034 |
| 32 | 1.0000 (1.0000–1.0000) | 0.3062 | 0.9850 |

- **Finding:** Once accuracy saturates (`width 8 -> 16 -> 32`), **single-unit monosemanticity (`H-A`) degrades steadily (`0.3713 -> 0.3463 -> 0.3062`) while linear-subspace recovery (`R^2`) rises sharply to `0.9850`** (`H-D`). Overparameterization recovers the Ur-Compiler's canonical `profile_rank=1` bit in a distributed linear subspace rather than in isolated neurons.

---

## 3. `H-C` (Longer-Horizon XOR6 Grokking)

Trained 64-wide `tanh` MLPs on `XOR6` ($n = 6$, 64 total points) for 3,000 Adam steps across weight decays `wd in {0.0, 0.01, 0.05}` (3 seeds each):

| `n_train` | `wd` | Train Acc Mean | Test Acc Mean (Max) | Grokking Steps (`>=0.95`) |
|---:|---:|---:|---:|---|
| 32 | 0.00 | 1.0000 | 0.5833 (0.6563) | `[None, None, None]` |
| 32 | 0.01 | 1.0000 | 0.4479 (0.5313) | `[None, None, None]` |
| 32 | 0.05 | 0.7083 | 0.2917 (0.3125) | `[None, None, None]` |
| 48 | 0.00 | 1.0000 | **0.9375 (1.0000)** | `[None, None, 250]` |
| 48 | 0.01 | 1.0000 | **0.2292 (0.3125)** | `[None, None, None]` |
| 48 | 0.05 | 0.5764 | 0.2708 (0.3125) | `[None, None, None]` |

- **Findings:**
  1. `32/64` remains a genuine **sample-complexity barrier** across all weight decays and 3,000-step budgets (`0/9` seeds grok).
  2. At `48/64`, unregularized Adam (`wd = 0.0`) achieves `0.9375` mean test accuracy (`max = 1.0000`), whereas even moderate L2 decay (`wd = 0.01`) suppresses `tanh` hidden gain and produces **anti-parity test collapse** (`0.2292` < chance, despite `1.0000` train fit), while `wd = 0.05` underfits train (`0.5764`).

---

## 4. `H-E` (Depth-3 vs Depth-2 Separation) & `parity4 >= 5` CP-SAT Check

Using `cerp.netsolve.solve` (OR-Tools CP-SAT, bounded integer weights `|w| <= 4`):
- `parity4` in depth-2 `[3, 1]` (4 neurons total): **`unsat`** in `13.985s` (supports tightness of `Bounds.lean` `parity4_not_two_halfspaces`; unbounded $\mathbb{R}^4$ Lean mechanization still faces the $\binom{1882}{3} \approx 1.1\times 10^9$ canonical-LTF enumeration barrier without $B_4$ symmetry reduction or a hyperplane-slicing theorem).
- `parity5` in **depth-3 chain `chain(5, 3)`** (**3 total neurons**): **`sat`** in `0.596s` (explicit witness saved in [spike16_results.json](file:///C:/Users/bruno/Claude%20Code/semplex/experiments/spike16_results.json)).
- `parity5` in `layered(5, [2, 2, 1], skip=True)` (depth-3, width-2 with skip): **`sat`** in `0.766s`.
- `parity5` in depth-2 `[3, 1]` (4 neurons, `W=4`): **`unsat`** in `17.539s`.
- `parity5` in depth-2 `[4, 1]` (5 neurons, `W=4`): **`unknown`** at `25.038s` timeout.
- **Finding:** Clean concrete **`H-E` separation at $n = 5$** for bounded weights (`|w| <= 4`): a **3-neuron** chained depth-3 circuit computes `parity5`, whereas depth-2 `[3, 1]` (**4 neurons**) is provably **`unsat`**.

---

## 5. Scaled Multi-Output & $n = 16$ `ur_compiler` Benchmark

- **`n = 10` 3-output coupled LTS policy** (`out_brake`, `out_left`, `out_right`):
  - Independent `compile_profile_factored`: `37` `TNode`s, `118` circuit gates (max depth `13`), `0.027s`.
  - Joint `compile_multi_profile_factored` (`profile_rank=1`): **`27` deduplicated `TNode`s** (`5` shared encoder + `22` decoder, **-27.0% neurons**), `118` per-output circuit gates (max depth `13`), `0.031s`.
- **`n = 16` symbolic AST CEGAR** (`compile_profile_factored(..., expr_ast=expr16)`):
  - `decomposed=True`, `profile_rank=1`, **`soundness="cegar-sat"`**, `circuit_cost={"gates": 53, "depth": 9}`, `atlas_min_neurons=17`, **`0.132s`**.
- **Lean 4.12 LRAT scaling benchmark (measured via `prove_tnet_equivalence_lrat` + `verify_threshold_net_equiv`):**
  - `xor3` (4 nodes, 73 vars, 173 clauses, 8 LRAT steps): `ok=True` under pure kernel `by decide` (`('propext', 'Classical.choice', 'Quot.sound')`) in **`219.37s`**.
  - `xor4` (5 nodes, 176 vars, 431 clauses, 16 LRAT steps): timed out at **`>900s`** under kernel `by decide`, succeeded in **`14.78s`** under `native_decide` (`NATIVE_AXIOMS` including `'Lean.ofReduceBool'`).
  - **Bottleneck diagnosed:** `Cerp.pbToExpr` expands each neuron's pseudo-Boolean condition via a naive `O(2^d)` Shannon `ite` tree; replacing `pbToExpr` with linear-size $O(d \cdot w)$ binary-adder arithmetic PB->CNF in Lean is the highest-leverage next step for scaling kernel-checked `ThresholdNet` LRAT proofs.
