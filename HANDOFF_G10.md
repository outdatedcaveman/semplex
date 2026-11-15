# G10 Handoff — Multi-Layer Threshold Network Lean Kernel Miters (`n = 6–8`)

- **Branch:** `gemini/G10` (base commit `cb37616af1f9d2e37eb19c2c169069b745a33863`)
- **Target:** Extend G2's PB Tseitin LRAT Lean kernel verification (`verify_threshold_net_equiv(..., native=False, pb=True)`) to non-degenerate full-fan-in multi-layer networks at `n = 6` (2 hidden layers) and `n = 8` (1 hidden layer) under `< 120s`, map the `> 120s` scaling ceiling across depth, width, and weight axes, and profile the exact Lean kernel bottleneck.
- **Pre-registered Hypothesis (Rule 5 — committed in `79de88e` prior to execution of `experiments/g10_miter_bench.py`):**
  1. Compact full-fan-in multi-layer threshold networks with concise binary-comparator `Expr` specifications (`n6_2hidden_w2_cmp_xor` `[6]->[2]->[2]->1`, `n8_1hidden_w2_eq4` `[8]->[2]->1`) verify via Lean kernel `decide` (`native=False, pb=True`, standard axioms only) in `< 120s`.
  2. Uniform scalar scaling and strictly superincreasing weights keep `pbEncodeLayer` top-down reachable-sum DP states small, whereas wider hidden layers, more LRAT steps/clauses, or non-superincreasing colliding weights push Lean past `120s`.
  3. Kernel `checkLratT` WHNF reduction (and repeated `tseitinTNetMiterPB` evaluation) dominates verification wall time.
- **Files added/changed:**
  - `experiments/g10_miter_bench.py` — reproducible benchmark & Lean stage breakdown harness (`--profile-only` flag added cleanly for `lean-toolchain` stage runs; pre-registered core & sweep benchmarks unchanged).
  - `experiments/results/g10_miter_timings.json` — full `15`-configuration timing dataset (`timeout_sec = 150.0`) + `kernel_breakdown` (`elab_only`, `wf_decide`, `lrat_decide`).
  - `tests/test_lean.py` — added `< 120s` kernel `decide` (`native=False, pb=True`) unit tests `test_tnet_lean_n6_two_hidden_layer_kernel_decide` and `test_tnet_lean_n8_one_hidden_layer_kernel_decide`.
  - `claims/PROPOSED.md` — appended Section 9 documenting verified `n = 6–8` multi-layer miter limits and bottlenecks.
- **Measured Results (`experiments/results/g10_miter_timings.json`, `native=False, pb=True`, axioms `['propext', 'Classical.choice', 'Quot.sound']`):**

| Benchmark | Axis | Shape | Nodes | MaxFanIn | Max\|w\| | Sum\|w\| | Vars | Clauses | LRAT Steps | SAT (s) | Lean Status | Lean (s) | `< 120s` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `baseline_xor4` | baseline | `[4]->[4]->1` | 5 | 4 | 1 | 20 | 42 | 120 | 16 | 0.1525 | `ok` | `16.461` | True |
| `n6_1hidden_w2_eq3` | depth | `[6]->[2]->1` | 3 | 6 | 4 | 30 | 49 | 140 | 19 | 0.1378 | `ok` | `18.848` | True |
| `n6_2hidden_w2_cmp_xor` | **core n=6 2-hidden** | `[6]->[2]->[2]->1` | 5 | 6 | 4 | 34 | 86 | 238 | 30 | 0.4410 | `ok` | **`53.725`** | True |
| `n6_3hidden_w2_d4` | depth | `[6]->[2]->[2]->[2]->1` | 7 | 6 | 4 | 40 | 90 | 248 | 31 | 0.5401 | `ok` | `63.004` | True |
| `n6_4hidden_w2_d5` | depth | `[6]->[2]->[2]->[2]->[2]->1` | 9 | 6 | 4 | 46 | 92 | 252 | 31 | 0.7624 | `ok` | `56.276` | True |
| `n6_2hidden_w4_rot_xor` | width (n=6) | `[6]->[4]->[2]->1` | 7 | 6 | 4 | 70 | 104 | 324 | 47 | 1.2340 | `ok` | `104.442` | True |
| `n8_1hidden_w2_eq4` | **core n=8 1-hidden** | `[8]->[2]->1` | 3 | 8 | 8 | 62 | 98 | 297 | 41 | 1.2757 | `ok` | **`75.414`** | True |
| `n8_factored_parity` | control | `balanced(13)` | 13 | 4 | 1 | 46 | 91 | 256 | 53 | 0.7873 | `ok` | `97.087` | True |
| `n8_1hidden_w3_or` | width (n=8) | `[8]->[3]->1` | 4 | 8 | 8 | 93 | 170 | 515 | 67 | 5.4949 | `timeout_150s` | `150.0` | False |
| `n8_1hidden_w4_rot_or` | width (n=8) | `[8]->[4]->1` | 5 | 8 | 8 | 124 | 206 | 673 | 104 | 12.0553 | `timeout_150s` | `150.0` | False |
| `n8_1hidden_w8_par8` | width (n=8) | `[8]->[8]->1` | 9 | 8 | 1 | 72 | 156 | 512 | 249 | 23.5719 | `timeout_150s` | `150.0` | False |
| `n8_1hidden_w2_scale2` | weight scale 2x | `[8]->[2]->1` | 3 | 8 | 16 | 122 | 98 | 297 | 41 | 1.2723 | `ok` | `73.308` | True |
| `n8_1hidden_w2_super53` | weight superincreasing | `[8]->[2]->1` | 3 | 8 | 53 | 386 | 98 | 297 | 41 | 1.8835 | `ok` | `80.313` | True |
| `n8_1hidden_w2_nonsup_17` | weight nonsup colliding | `[8]->[2]->1` | 3 | 8 | 17 | 194 | 152 | 469 | 64 | 3.4024 | `timeout_150s` | `150.0` | False |
| `n8_1hidden_w2_nonsup_5` | weight nonsup colliding | `[8]->[2]->1` | 3 | 8 | 5 | 58 | 176 | 517 | 61 | 4.8704 | `timeout_150s` | `150.0` | False |

- **Kernel Stage Breakdown (`kernel_breakdown`, Lean `v4.12.0`):**
  - `baseline_xor4` (`16` steps / `120` clauses): `elab_only = 2.181s`, `wf_decide = 2.962s`, `lrat_decide = 11.45s` (full `16.461s`).
  - `n6_2hidden_w2_cmp_xor` (`30` steps / `238` clauses): `elab_only = 3.535s`, `wf_decide = 6.917s`, `lrat_decide = 52.609s` (full `53.725s`). Here `checkLratT` kernel WHNF reduction dominates (`97.9%` of total runtime).
  - `n8_1hidden_w2_eq4` (`41` steps / `297` clauses): `elab_only = 24.71s`, `wf_decide = 30.602s`, `lrat_decide = 72.138s` (full `75.414s`). Front-end Lean elaboration of `tns`/`eSpec`/`Ls` jumps `7x` from `30 -> 41` steps while kernel reduction adds `~47.4s`.
  - `n8_1hidden_w4_rot_or` (`104` steps / `673` clauses): **`elab_only = timeout (150.0s)`**, `wf_decide = timeout (150.0s)`, `lrat_decide = timeout (150.0s)`. At `>= 104` LRAT steps / `206` vars / `673` clauses, Lean 4 front-end elaboration alone exceeds `150s` before `by decide` even runs.
- **Bottleneck Conclusions:**
  1. **Dual Lean bottleneck past `120s`:** (a) at medium sizes (`~30` steps), `checkLratT` WHNF evaluation plus `3x` recomputation of `tseitinTNetMiterPB` (once in `hw`, twice in `hchk`) dominates (`52.6s` vs `3.5s` elab); (b) at larger LRAT proofs (`41 -> 104` steps), Lean 4 elaboration of nested `List (Clause × List Nat)` signed-integer literals (`elab_only`: `3.535s -> 24.71s -> >150.0s`) becomes a co-dominant hard wall.
  2. **Weight structure vs magnitude:** `pbEncodeLayer`'s sparse top-down DP is invariant to uniform scaling (`w2_scale2`: `73.308s`) and stays bounded for strictly superincreasing weights (`w2_super53`: `max|w|=53`, `80.313s`), whereas non-superincreasing colliding weights (`[17,13,11,7]`, `[5,4,3,2]`) expand reachable DP states into `469–517` clauses and `61–64` LRAT steps, pushing verification past `150s`.
- **Rule 7 checks (verified on final code/data state):**
  - Targeted unit tests (`pytest -q tests/test_lean.py -k "two_hidden_layer or one_hidden_layer"`): `2 passed, 9 deselected in 142.09s (0:02:22)`.
  - Full `pytest -q`: `1 failed, 160 passed in 1117.78s (0:18:37)` (sole failure: `tests/test_lean.py::test_proof_files_compile_and_use_only_standard_axioms` `TimeoutExpired` at `600s` compiling `Bounds.lean`).
  - Standalone Lean `v4.12.0` (`Cerp` `57.61s`, `Theory` `24.37s`, `Bounds` `620.87s`, `Audit` `3.80s`, `AuditTheory` `2.69s`, `AuditBounds` `2.53s`), all exit `0`, `bad_axioms=False` (`[propext, Classical.choice, Quot.sound]` only), `LEFTOVER_OLEAN=0`.
  - `python -m cerp.register check` -> exit `0` (`0 problem(s), 33 status note(s)`); `git diff -w claims/LEDGER_CHECK.md` empty.
  - `python -m cerp.status --check` -> exit `0`.
