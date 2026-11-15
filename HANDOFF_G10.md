# G10 Handoff — Multi-Layer Threshold Network Lean Kernel Miters (`n = 6–8`)

- **Branch:** `gemini/G10` (base commit `cb37616af1f9d2e37eb19c2c169069b745a33863`)
- **Target:** Extend G2's PB Tseitin LRAT Lean kernel verification (`verify_threshold_net_equiv(..., native=False, pb=True)`) to non-degenerate full-fan-in multi-layer networks at `n = 6` (2 hidden layers) and `n = 8` (1 hidden layer) under `< 120s`, map the `> 120s` scaling ceiling across depth, width, and weight axes, and profile the exact Lean kernel bottleneck.
- **Pre-registered Hypothesis (Rule 5 — committed prior to execution of `experiments/g10_miter_bench.py`):**
  1. Compact full-fan-in multi-layer threshold networks with concise binary-comparator `Expr` specifications (`n6_2hidden_w2_cmp_xor` `[6]->[2]->[2]->1`, `n8_1hidden_w2_eq4` `[8]->[2]->1`) will verify cleanly via Lean kernel `decide` (`native=False, pb=True`, axioms $\subseteq \{\text{propext}, \text{Classical.choice}, \text{Quot.sound}\}$) in `< 120s`.
  2. Uniform scalar weight scaling (`(w, t) -> (k*w, k*t)`) and strictly superincreasing weights keep `pbEncodeLayer` top-down reachable-sum states small (`O(n)`), whereas increasing hidden width (`w >= 3..8`), LRAT step/clause counts, or colliding non-superincreasing weights will push Lean kernel `decide` past `120s`.
  3. Inside `tseitinTNetMiterPB_lrat_unsat_implies_equiv`, `checkLratT` (which re-evaluates `tseitinTNetMiterPB` twice to construct `bOfListAux` and its length, then interprets LRAT unit propagation via Lean kernel WHNF reduction) dominates wall time over `wellFormed` and `.olean` load/elaboration.
- **Per-case timeout cap:** `150.0s` per Lean verification call (`> 120s` ceiling test).
- **Results & Rule 7 checks:**
  - Pending execution of `experiments/g10_miter_bench.py`.
