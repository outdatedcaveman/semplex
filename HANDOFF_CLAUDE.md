# Claude Code Handoff — `semplex` Honest State, Verified Assets & Next Work Packages

**Updated:** 2026-11-13  
**Purpose:** Grounded, scientifically unvarnished handoff separating what is formally Lean-proved, what works in code, what failed or hit hard bottlenecks empirically, and the highest-leverage next steps toward a unified, publishable theory and scaled Ur-Compiler.

---

## 1. What Is Formally Proved in Lean 4.12 (Standard Axioms Only)

All theorems below were compiled directly with `Lean 4.12.0` (`proofs/lean/Theory.lean`, `proofs/lean/Cerp.lean`, audited by `proofs/lean/AuditTheory.lean` and `proofs/lean/Audit.lean`) under standard axioms at most `{propext, Classical.choice, Quot.sound}` (`0` `sorryAx`):

1. **Quantitative Protocol-Frame Morphisms & Obstruction (`Theory.lean` §17, P071):**
   - `frameHom_indist`, `frameHom_determines_pullback`: Contravariant pullback of observational indistinguishability and exact query determinacy along protocol-preserving morphisms `FrameHom`.
   - `queryApprox_comp`, `frameHom_eps_determines_pullback`, `frameHom_eps_metric_pullback`: Additive `ε₁ + ε₂` composition of quantitative `ε`-determinacy and metric distortion pullback.
   - `lossy_composition_obstruction`: Constructive 3-point finite protocol counterexample proving that lossy coarse abstraction stages create irrecoverable indeterminacy without enriching $\Omega$.
2. **Constructive Finite Markov-Kernel Data-Processing Contraction (`Theory.lean` §18, P072):**
   - `tv_deterministic_dpi`, `markov_kernel_dpi`, `markov_kernel_dpi_comp`: Total-variation contraction $D_{\mathrm{TV}}(K \mu, K \nu) \le D_{\mathrm{TV}}(\mu, \nu)$ across arbitrary finite kernels over `Fin n` and inductive sequential compositions (grounds `stochastic_lts` $T$-step TV guarantees in `ur_compiler.py` without Mathlib).
3. **Peircean Pragmatic Maxim & Discrete Ville Inequality (`Theory.lean` §19, P073):**
   - `indist_implies_pragEquiv`, `peirce_pragmatic_maxim`: Operational equivalence across all `Sign–Object–Interpretant` test contexts coincides with observational determinacy equivalence.
   - `applyStop_preserves_supermartingale`, `optional_stopping_supermartingale`, `ville_anytime_valid_bound`: Arbitrary finite-horizon causal stopping rules preserve discrete nonnegative supermartingales and obey Ville's maximal inequality $\mathbb{P}(\max_{t \le T} M_t \ge \alpha) \le \mathbb{E}[M_0]/\alpha$.
4. **Executable `ThresholdNet` Equivalence & LRAT Certification (`Cerp.lean` Part D, P074):**
   - `decideTNetEquivExpr_correct`: Exhaustive kernel decision procedure verifying any scoped acyclic integer-weight `TNode` DAG (`evalTNet`) against an `Expr` specification.
   - `eval_pbToExpr`, `tseitinTNetGo_complete`, `tseitinTNetMiter_lrat_unsat_implies_equiv`: Arbitrary-depth linear-time hint-indexed LRAT verifier certifying Python-emitted `ThresholdNet`s directly in Lean via pseudo-Boolean Shannon expansion (`pbToExpr`) + Tseitin miter.

---

## 2. What Is Built & Verified in the Ur-Compiler (`cerp/`)

- **Python $\leftrightarrow$ Lean `ThresholdNet` LRAT Bridge ([sat.py](cerp/sat.py), [lean_bridge.py](cerp/lean_bridge.py)):**
  - `_tnet_to_indexed_nodes`, `_pb_to_expr_indexed`, `_lean_tnet_miter`, `prove_tnet_equivalence_lrat`, `tnet_to_lean`, `verify_threshold_net_equiv`.
  - Wired into `ur_compiler._lean_certify_equiv` (`verify_net=True` default when `certify_lean=True`).
- **Scaled Factored Ur-Compiler ([ur_compiler.py](cerp/ur_compiler.py)):**
  - Replaced the broken strided `S2` sampler (which froze low-order bits at `0` for `n > 14`) with unbiased structured + SplitMix64 probes (`_sample_s2_envs`) and optional symbolic SAT-CEGAR equivalence checking (`_sat_cegar_refine_split`), tracked explicitly via `soundness` (`"exact" | "cegar-sat" | "sampled(k)"`).
  - Added joint multi-output factored compiler `compile_multi_profile_factored` and wired it (`shared_encoder=True` default) into `compile_unified` for `"lts"` and `"stochastic_lts"`.
  - Measured on `n = 16` (`expr_ast` SAT-CEGAR): `0.132s`, `profile_rank=1`, `soundness="cegar-sat"`.
  - Measured on `n = 10` 3-output coupled LTS: `-27.0%` deduplicated `TNode`s (`37 -> 27`).

---

## 3. Honest Empirical Findings, Negative Results & Bottlenecks

Do **not** overclaim around these measured limits:

1. **Kernel `by decide` LRAT bottleneck on `ThresholdNet` (`P074`):**
   - `Cerp.pbToExpr` expands each neuron's pseudo-Boolean condition into a `O(2^d)` binary `ite` tree.
   - `xor3` (4 nodes, 173 Tseitin clauses, 8 LRAT steps) passes pure kernel `by decide` in **`219.37s`**.
   - `xor4` (5 nodes, 431 Tseitin clauses, 16 LRAT steps) times out at **`>900s`** under `by decide`, whereas `native_decide` verifies it in **`14.78s`** (`NATIVE_AXIOMS`, trusting Lean compiler runtime).
2. **`Bounds.lean` `parity4 >= 5` Combinatorial Barrier (`Q-Bounds-Sym`):**
   - OR-Tools CP-SAT confirms `[3, 1]` (`|w| <= 4`) is `unsat` for `parity4` (`13.985s`), and `Bounds.lean` proves `parity4_not_two_halfspaces`.
   - Proving `parity4 >= 5` in Lean for **unbounded** weights via finite canonical-LTF enumeration faces $\binom{1882}{3} \approx 1.1\times 10^9$ triples, infeasible in `by decide` without either $B_4$ symmetry reduction or an algebraic hyperplane-slicing proof.
3. **Single-Unit Monosemanticity (`H-A`) Fails at Wide Width While Subspace `H-D` Succeeds (`experiments/SPIKE_16_REPORT.md`):**
   - On the $n = 8$ low-rank factored function (`profile_rank=1`, 5 seeds each, `tanh` Adam), accuracy saturates at width 16–32 (`1.000`), but `max_unit_corr_mean` drops (`0.3713` at $W=8 \to 0.3062$ at $W=32$) while linear subspace probe $R^2$ rises (`0.6912 -> 0.9850`). Overparameterized nets encode canonical Ur-Compiler variables in distributed linear subspaces, not isolated natural neurons.
4. **`XOR6` (`H-C`) Sample Barrier & L2 Anti-Parity Collapse (`experiments/SPIKE_16_REPORT.md`):**
   - `32/64` train split never groks (`0/9` seeds up to 3,000 steps).
   - At `48/64`, unregularized Adam (`wd = 0.0`) achieves `0.9375` mean test accuracy (`max = 1.0`), whereas `wd = 0.01` collapses test accuracy to **`0.2292`** (anti-parity overfitting despite `1.000` train fit), and `wd = 0.05` underfits train (`0.5764`).
5. **`tests/test_localrules.py::test_search_keeps_a_working_rule_working` Flakiness (`P076`):**
   - Strict `0.9` threshold was **preserved** (not relaxed). Across 20 random batches on the same setup, pure backprop itself has `min = 0.875`, `mean = 0.9521`; CEM kept backprop (`a[bp] = 1.0`) and failed solely due to Monte-Carlo initialization variance on gen 3.
6. **Hardware Constraint (Windows 8 GB RAM Box):**
   - Never run multiple heavy commands (Lean + JAX/PyTorch/OR-Tools) concurrently; commit exhaustion causes BSOD `0x113`.

---

## 4. Prioritized Next Work Packages for Claude Code

### Work Package A (Highest Proof-Engineering ROI): Linear-Size $O(d \cdot w)$ PB $\to$ CNF in `Cerp.lean` (`Q-LRAT-PB`)
- **Problem:** `pbToExpr` blows up `TNode` Tseitin CNF as $O(2^d)$, capping pure-kernel `by decide` LRAT checks at ~3–4 input neurons.
- **Target:** Replace `pbToExpr` in `proofs/lean/Cerp.lean` + `_pb_to_expr_indexed` in `cerp/sat.py` with a verified linear-size sequential binary-adder or totalizer PB->CNF encoding (or proved equivalence `pbSumCnf_complete` directly for bounded sums) so `xor4` (4–5 neurons) replays in `<10s` under pure kernel `by decide` (`ALLOWED_AXIOMS`).
- **Acceptance:** `test_tnet_lean_exhaustive_and_lrat_equiv` passes on `xor4` with `native=False` (`'Lean.ofReduceBool'` absent) under 30s.

### Work Package B (Formal Theory Unification): Connect Sequential Epistemics & Continuous DPI (`Q-OptStop-Connect`)
- **Problem:** `Theory.lean` §§18–19 proves `markov_kernel_dpi` (`Fin n`) and `ville_anytime_valid_bound` cleanly, and `cerp/epistemics/` runs empirical tests, but the sequential `cerp/epistemics/` / `QueryTree` estimators are not yet instantiated as verified `Nat`/`Fin` supermartingales nor bridged to Mathlib measure theory.
- **Targets:**
  1. Instantiate a concrete sequential likelihood-ratio / e-value test process (`cerp/epistemics/` $\leftrightarrow$ `proofs/lean/Theory.lean`) proving its rejection rule satisfies `ville_anytime_valid_bound` at finite horizon `T`.
  2. Explore Mathlib `MeasureTheory.Kernel` optional sub-package or finite-refinement projective limit for `Theory.lean` §18 DPI.
  3. Formalize `lossy_composition_obstruction` into an algebraic **obstruction invariant** (e.g., conditional profile entropy / sheaf gluing defect across overlapping $\Omega$-covers).

### Work Package C (Circuit Complexity Lower Bounds): $B_4$-Symmetrized `parity4 >= 5` & Depth-3 Separation (`Q-Bounds-Sym`)
- **Problem:** `parity4_not_two_halfspaces` is proved in `proofs/lean/Bounds.lean`, and Spike 16 gave bounded-weight `|w| <= 4` CP-SAT `unsat` for `[3, 1]` on `parity4`/`parity5` + 3-neuron `chain(5, 3)` witness on `parity5`. Unbounded `parity4 >= 5` and general `depth-3` separation are still unformalized in Lean.
- **Target:** Quotients under the hyperoctahedral symmetry $B_4$ (`2^4 * 4! = 384`) or a hyperplane-orthant counting lemma in `proofs/lean/Bounds.lean` to close `parity4 >= 5`, plus formalize `parity5_chain3` (`3`-neuron upper bound verified directly against `evalTNet`).

### Work Package D (Neural & Ur-Compiler Scaling): Symbolic AST Compilation Without Dense Tables (`Q-HD-Theory`)
- **Problem:** `cerp/ur_compiler.py` (`n > 14`) can compile large factored functions if given `expr_ast`, but its encoder-partition search is still greedy (`C(n, <=4)` + enumerates `2^n1` slices) and fails to decompose general unfactored deep ASTs directly (still builds a dense `table_arr` once `dec_vars <= 14`).
- **Target:** Add symbolic BDD/AIG cofactor decomposition directly on `expr_ast` for `n > 14`, benchmark on multi-feature continuous control (`CartPole` / quantized MDP benchmarks) with end-to-end Lean LRAT net checks, and test whether `H-D` subspace emergence (`R^2 -> 0.985`) stabilizes or collapses across multi-layer ReLU vs `tanh` depth.
