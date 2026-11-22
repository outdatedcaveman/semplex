> **Reconciled at merge (2026-11-15).** These proposals from `gemini/G1`–`G7` were verified and entered in `claims/REGISTER.md` as P160 (G1), P161 with a correction to P077 (G4), P162 (G2), P163 (G3), P164 (G5) and P165 (G7's eight boundary proposals); G6 is recorded under P149. Kept below as filed. New proposals go under a new heading.
>
> **Second reconciliation (2026-11-15).** `gemini/G8`–`G12` were verified and entered as P166 (G8), P167 (G9), P168 (G10), P169 (G11); G12's corrections are recorded under P165.

# Proposed Claims (`claims/PROPOSED.md` — `gemini/G6`)

No new empirical or formal claims proposed on `gemini/G6` (engineering / test-determinism fix for Gap D2 only).
# Proposed claims from branch gemini/G1 (Gap C1: Theorem 15 in Lean)

- Statement: Lemma toward Theorem 15 (`THEORY.md` §3.7, `P069`): under concrete coordinate permutations and sign flips (`SignedPerm n` acting on parameter/gradient/1st-moment vectors and permuting non-negative 2nd-moment vectors), a `σ`-invariant scalar loss `L` induces an equivariant gradient (`fdGrad_equivariant`), both concrete full-batch GD (`gdStep_equivariant`) and concrete AdamW with elementwise 1st/2nd moments, sqrt normalization, and decoupled weight decay (`adamwStep_equivariant`) commute with `σ` over any time-varying schedule, any equivariant circuit readout commutes along trajectories (`theorem15_gd_trajectory_equivariant`, `theorem15_adamw_trajectory_equivariant`), and any finite `σ`-invariant weighted parameter ensemble assigns equal weight to circuit `I` and `σ • I` (`theorem15_finite_distribution_invariant`, `theorem15_adamw_finite_distribution_invariant`, discharged for finite duplicate-free orbit pools by `ensembleInvariant_of_nodup_support`), with concrete fixed-point `Int` arithmetic proved in Lean core (`intFixedScalar`). Evidence: `proofs/lean/Theory.lean` (§20 `Theorem15`), audited in `proofs/lean/AuditTheory.lean` (`[propext]` / `[propext, Quot.sound]` only, zero `sorryAx`). What it does NOT show: continuous Gaussian initialization $\mathcal{N}(0, \sigma_w^2 I)$ (requires measure theory / Mathlib; keep `P069` as "paper proof + finite case in Lean") and continuous Fréchet derivatives (formalized via finite-difference `fdGrad` or assumed analytical `grad` equivariance in `*_of_grad`).
# Proposed claims from branch gemini/G4 (Gap C2: No-transfer lemma)

- Statement: If a finite group `G` stabilizes the labelled dataset `(L, y|_L)` (in particular sets `L` to `L`), every `G`-orbit lies wholly inside `L` or wholly outside `L`, so any `G`-symmetrized predictor evaluated on an unlabelled input depends strictly on the base predictor's values on unlabelled inputs (zero label information transfers from `L`); moreover, under unlabelled-flip invariance (`y ↦ flipUnlabelled L y`), deterministic symmetrization and raw prediction have identical expected unlabelled hit count, while under any `G`-invariant target prior (or fixed `G`-invariant target) on a `G`-closed unlabelled set `U`, random-`G` (Reynolds) symmetrization preserves expected unlabelled hit count identically. Evidence: `proofs/lean/Theory.lean` (`PFT.no_transfer_orbit_preserves_labelled`, `PFT.no_transfer_orbit_preserves_unlabelled`, `PFT.no_transfer_sym_list_independent_of_labelled`, `PFT.no_transfer_sym_predictor_independent_of_labelled`, `PFT.flipUnlabelled_preserves_labelled`, `PFT.flipUnlabelled_preserves_stabilizer`, `PFT.no_transfer_flip_pair_constant`, `PFT.no_transfer_flip_invariant_dist_eq`, `PFT.no_transfer_reynolds_fixed_invariant_target`, `PFT.no_transfer_reynolds_invariant_prior`); audited in `proofs/lean/AuditTheory.lean` (axioms `{propext, Quot.sound}` only, zero `sorryAx`). What it does NOT show: (1) Infinite domains/continuous Gaussian measures (finite discrete sums over lists `U`, `G`, and `targets`); (2) As proved in `PFT.sym_majority_can_improve_without_flip_symmetry`, *deterministic* majority-vote / logit-average symmetrization over a `G`-orbit CAN strictly change (and improve) expected accuracy if the target prior is `G`-invariant yet skewed (lacking unlabelled flip symmetry, e.g., 4:1 toward constant-true on a 3-point cyclic unlabelled orbit).
# Proposed Claims — Branch `gemini/G2` (Gap B1)

Do not assign `Pnnn` IDs or modify `claims/REGISTER.md` on this branch; Claude merges and assigns IDs.

- **Proposed claim (BTree LRAT checker soundness in Lean 4 kernel):**
  `Cerp.checkLratT_unsat` establishes that if the structural-recursion binary-tree LRAT checker `Cerp.checkLratT` accepts a well-formed CNF `cs` and hint-indexed trace `Ls`, then `cs` has no satisfying Boolean assignment (`∀ σ, cnfSat σ cs = false`), proved in `proofs/lean/Cerp.lean` under axioms `[propext, Quot.sound]` (`0` `sorryAx`).

- **Proposed claim (Direct PB BDD Tseitin miter soundness & kernel `by decide` equivalence for `xor4`):**
  `Cerp.tseitinTNetMiterPB_lrat_unsat_implies_equiv` proves that direct pseudo-Boolean BDD Tseitin encoding (`pbEncodeSym`, without exponential `O(2^d)` `pbToExpr` Shannon expansion) plus `checkLratT` LRAT refutation implies `∀ σ, evalTNet n ns σ = eval σ e` under axioms `[propext, Classical.choice, Quot.sound]` (`0` `sorryAx`, `0` `Lean.ofReduceBool`). Together with backward cone-of-influence hint trimming and lemma pruning in `cerp/sat.py::rup_to_lrat`, kernel `by decide` certification now succeeds in `5.25 s` on `xor3` (57 clauses vs 173, 22 vars vs 73) and `15.68 s` on `xor4` (120 clauses vs 431, 42 vars vs 176), down from `245.30 s` (`xor3`) and timeout (`xor4`).
# Proposed Claims — G3 (Gap B2: Care-Set Compilation at n = 8, 10)

## Proposed Claim B2-G3: Certified Partial-Care Threshold Compilation at n = 8 and n = 10

- **Statement:** Using decoupled 2-halfspace CP-SAT compilation (`_solve_two_halfspaces`), linear-size lexicographic chain symmetry breaking across interchangeable hidden neurons (`netsolve.solve`), and exact LP Farkas + Carathéodory/Fraction lower-bound search (`bounds.not_threshold_cert_partial`, `bounds.not_two_halfspaces_cert_partial`), the incremental compiler `netsolve.compile_partial(..., W=4, max_width=4, time_limit=60.0, workers=4)` compiles and certifies minimality for 100/100 non-threshold `spike36`-family targets at `n = 8` (75% care set, `192/256` points) and 100/100 at `n = 10` (75% care set, `768/1024` points), with every compiled network verified against `cerp.kernel.evaluate` on all care inputs and every lower bound verified by `cerp.kernel_bounds`.
- **Exact Evidence:**
  - Benchmark script: `experiments/g3_care_benchmark.py`; raw results: `experiments/results/g3_care_benchmark.json`.
  - **`n = 8`** (100 distinct non-threshold targets, generator seed `8800`, care seed `8801`, `192/256` care inputs, `time_limit = 60.0s`, `workers = 4`):
    - Verified SAT networks: **100 / 100** (`100%` within 60s)
    - Certified minimal networks: **100 / 100** (`100%` within 60s; `99` cost-3 via `not-threshold-partial`, `1` cost-1 `trivial`)
    - Compile time: median `0.2789s`, mean `0.3034s`, max `0.9845s`, wall `31.097s`
  - **`n = 10`** (100 distinct non-threshold targets, generator seed `8810`, care seed `8811`, `768/1024` care inputs, `time_limit = 60.0s`, `workers = 4`):
    - Verified SAT networks: **100 / 100** (`100%` within 60s)
    - Certified minimal networks: **100 / 100** (`100%` within 60s; `100` cost-3 via `not-threshold-partial`)
    - Compile time: median `2.2451s`, mean `2.2657s`, max `4.6495s`, wall `229.892s`
  - Kernel-checked unit tests in `tests/test_bounds_partial.py`:
    - `test_not_two_halfspaces_partial_and_forgeries`: checks `parity3` partial/full lower-bound certificates via `kernel_bounds.check_not_two_halfspaces_partial` and rejection of forged/incomplete masks and empty bad-set lists.
    - `test_not_threshold_partial_lp_n8`: verifies LP Farkas witness discovery on `n = 8` partial non-threshold (`x0 ^ x1`) and `None` on linearly separable threshold functions.
    - `test_compile_partial_n4_and_n8`: verifies `cost == 1` (`trivial`), `cost == 4` (`lower_bound == 4`, `not-two-halfspaces-partial` on lifted `parity3` at `n = 4`), and `n = 8` partial 2-halfspace compilation against `kernel.evaluate`.
- **What It Does Not Show:**
  - The `spike36` generator samples width-2 threshold nets (`cost <= 3`), so the `n = 8, 10` benchmark validates cost-1 and cost-3 compilation and `not-threshold-partial` certificates at scale, not random `cost >= 4` hardness at `n = 8, 10`.
  - `check_not_two_halfspaces_partial` is bounded to bad-set universes of at most 20 points (`len(universe) <= 20`) and certifies non-representability as a single `AND` or `OR` of two real halfspaces (ruling out width-2 1-hidden-layer threshold nets), not arbitrary deeper DAG topologies.
  - Lower bounds from `not_threshold_cert_partial` and `not_two_halfspaces_cert_partial` apply to 1-hidden-layer `step` networks (`layered(n, [w])`) and do not establish optimality over general DAG or ReLU circuits.
# Proposed Claims (Branch `gemini/G5`)

## Proposed Claim: 4-Input Parity Requires at Least 5 Strictly Layered Threshold Neurons (Gap B3)

- **Statement:** No strictly layered threshold network (Family T / `evalLayered`) with at most 4 total neurons (hidden layers plus 1 output neuron) can compute 4-input parity (`parity4`, truth table `0x6996`), nor can any 3 linear threshold functions on 4 binary inputs determine `parity4`. Combined with a valid 5-neuron strictly layered parity construction, `parity4` has exact minimum size 5 in Family T.
- **Exact Evidence:**
  - Formal Lean 4.12.0 proofs in [`proofs/lean/Bounds.lean`](proofs/lean/Bounds.lean):
    - `CerpBounds.parity4_not_three_ltf_determined`
    - `CerpBounds.parity4_not_four_neurons`
    - Audited in [`proofs/lean/AuditBounds.lean`](proofs/lean/AuditBounds.lean): both theorems depend only on `[propext, Classical.choice, Quot.sound]` (zero `sorryAx`, zero `Lean.ofReduceBool`).
    - Method: weight regularization (`regularize_ltf`, `monotone_isRegular`), exhaustive regular canonical enumeration (`regExhaust`, `t_reg_exhaust`), $B_4$ orbit closure across 14 canonical orbits of sizes `[192, 192, 96, 96, 96, 64, 64, 32, 32, 24, 16, 16, 16, 4]` (940 non-constant canonical 4-bit LTFs plus constant `0`), stabilizer quotienting, and single/multi-bucket coordinate-sum Farkas certificates.
  - Python kernel verifier & certificate builder:
    - [`cerp/kernel_bounds.py`](cerp/kernel_bounds.py): `check_parity4_needs_5_neurons(cert) -> Verdict` (stdlib-only imports from `.kernel`), verifying monotone weight witnesses for all 15 representatives, generator closure (`neg0`, `sw01`, `sw12`, `sw23`), exhaustive $2^{16}$ 20-edge regular-poset coverage (`_REG_EDGES16`), stabilizer fixation, and all single/multi Farkas certificates.
    - [`cerp/bounds.py`](cerp/bounds.py): `parity4_five_neuron_cert()`.
    - Tested in [`tests/test_atlas_bounds.py`](tests/test_atlas_bounds.py) (`test_parity4_needs_5_neurons_certificate_and_forgeries`) and [`tests/test_bounds_differential.py`](tests/test_bounds_differential.py) (`test_parity4_five_neuron_matches_atlas_and_lean`, cross-checked against `atlas.ltfs(4)` and `_lean_not_threshold_pred`).
- **What it does NOT show:**
  - Does not lower-bound threshold circuits with skip connections or arbitrary DAG wiring (which are not modeled by `evalLayered`).
  - Does not independently re-prove the 5-neuron upper bound construction inside `Bounds.lean`.
  - Does not establish Lean-verified $\ge 5$ bounds for $n \ge 5$ parity functions.
# Proposed Claim & Boundary Refinements — Gap D3 (`gemini/G7`)

Note: Per `GEMINI.md`, this file proposes boundary restrictions, anticipation flags, and barrier notes from the `gemini/G7` literature audit (`charter/LITERATURE_REVIEW.md` §5 lines 142–192, `charter/PRIOR_ART.md`). No `Pnnn` IDs are assigned here, and no existing `REGISTER.md` statuses, `THEORY.md` §5 text, or `claims/GAPS.json` rows are modified.

---

## 1. Narrow `R1` (`THEORY §2`, `P028`, `P031`) to Finite Conflict-Hypergraph Duality & Certified Compilation

- **Proposed statement:** Restrict novelty claims around `R1` (`THEORY §2`, `P028`, `P031` canonical quotient / minimal sufficient representation) strictly to: (i) finite deterministic determining-set / conflict-hypergraph duality on Boolean care sets (`P004`, `P027`), (ii) certified minimum threshold circuit synthesis, and (iii) Lean 4 kernel checking (`Theory.lean`, `Cerp.lean`, `Bounds.lean`). General statistical and sequential minimal-sufficiency uniqueness theorems are **prior art**.
- **Exact evidence:**
  - **Sevetlidis (`arXiv:2606.04045`, Full text):** `templateArxiv.tex` Abstract L74 states `"In the almost-surely unique Bayes-action case, the relevant object is a Bayes quotient, which identifies inputs that require the same Bayes-optimal action. A representation is sufficient when it refines this quotient, and Bayes-minimal when it is informationally equivalent to it"`; `thm:bayes-quotient-main` (L205–223, L222) proves `"Bayes-sufficient representations are exactly refinements of the Bayes quotient"`; `cor:minimal-unique-app` (L841–849) proves `$\sigma(H_1)=\sigma(H_2)\text{ mod }P_X$`.
  - **Shalizi & Crutchfield (`arXiv:cond-mat/9907176`, Full text):** `cmppss-arxiv.tex` Abstract L80–83 (`"the causal-state representation---an \epsilon-machine---is the minimal one consistent with accurate prediction"`), L1579 (`\Cmu(\PrescientStateSet) \ge \Cmu(\CausalStateSet)`), L1646 (`Causal States Are Unique`).
  - **Barnett & Crutchfield (`arXiv:1412.2690`, Full text):** `et1.tex` L1924 (`"causal states have the minimal conditional statistical complexity among all prescient rival partitions \PS"`) and L1962 (`"The \eT\ is the unique prescient, minimal partition of pasts"`).
  - **Rosas, Boyd & Baltieri (`arXiv:2504.04608`, Full text):** `main.tex` `theo:Predictive Transducer Coarse-Graining` L803 proves `"If R_t is a predictive world model of a transducer, then its minimal bisimulation is isomorphic to the \epsilon-transducer"`.
- **What this does NOT show:** None of the above construct exact finite Boolean conflict-hypergraph minimal hitting sets or produce solver-certified threshold circuits verified by a proof-assistant kernel. Moreover, Rosas et al. (`2504.04608` Abstract L148) show generic (non-predictive) minimal world-model transducers need not be unique, paralleling `P029` / `P144`.

---

## 2. Document Independent Co-Discovery of Blocking-Set / MHS Duality on `P004` & `P027`

- **Proposed statement:** Cite `Hadad, Katz & Bassan (arXiv:2602.16823, ICLR 2026)` alongside `P004` and `P027` as an independent publication of monotone blocking-set / minimum-hitting-set (MHS) duality for minimal faithful circuits, while differentiating semplex's finite Boolean care-set domain and Lean 4 formal proofs.
- **Exact evidence:**
  - **Hadad, Katz & Bassan (`arXiv:2602.16823`, Full text):** `iclr2026_conference.tex` `lem:blocking_sets_equivalence` (L2786–2791) proves `"Under a monotone predicate \Phi, the set of circuit blocking sets with respect to G coincides exactly with the sets whose removal breaks faithfulness of the full model, i.e., C' \subseteq G is a blocking set if and only if \neg \Phi(G \setminus C', G)"`; `mhs_main_theorem_appendix` (L2806–2829) proves the MHS of blocking sets gives a cardinally minimal faithful circuit, with `mhs_algorithm_convergence_prop` (L1392–1395).
- **What this does NOT show:** `2602.16823` prunes existing continuous neural network graphs under empirical faithfulness predicates `\Phi`; it does not synthesize globally minimum-neuron Boolean threshold nets from scratch or check lower-bound / SAT-LRAT / BDD proofs inside Lean 4 (`Cerp.lean`, `Bounds.lean`).

---

## 3. Constrain `R2` (`Gap A9`, `Gap A10`, `P133`, `P134`, `P144`) Against Nonlinear Alignment Triviality

- **Proposed statement:** Abandon any unconstrained formulation of `R2` allowing arbitrary nonlinear alignment maps `\tau` between neural layers and symbolic algorithms. Restrict `R2` to structurally constrained alignment families (such as compatible block permutations × block-diagonal invertible maps, unit-aligned cells, or bounded-distortion approximate abstractions `\varepsilon`) anchored by constructive causal abstraction.
- **Exact evidence:**
  - **Sutter, Minder, Hofmann & Pimentel (`arXiv:2507.08802`, Full text):** `main.tex` Abstract L207 states `"under reasonable assumptions, \emph{any} neural network can be mapped to \emph{any} algorithm, rendering this unrestricted notion of causal abstraction trivial and uninformative"`; `theorem:existing_causalmap_for_any_algorithm` (L579–581) formalizes this triviality for layer-injective, output-surjective task-solving networks.
  - **Geiger, Harding & Icard (`arXiv:2508.11214`, Abstract + sections):** `sprevak-arxiv.tex` L93 warns `"Laxer mapping constraints for implementation may thereby admit an excess of representational claims"`.
  - **Zaghw, Brendel & Reizinger (`arXiv:2610.18155`, Full text):** `theory.tex` `thm:maximality` (L115–121) proves universal preservation of constructive causal abstractions under reparameterization holds iff `"T=\sigma\circ D\text{ for some }D\in\mathcal D"` (compatible block permutation and block-diagonal invertible transformation).
  - **Cifuentes (`arXiv:2608.20428`, Full text):** `approximate_homomorphism.tex` `prop:compose_approx_homo` (L125–127) proves additive `\varepsilon`-reduction composition (`\varepsilon_1+\varepsilon_2`) parallel to `P144` (`queryApprox_comp`), alongside `thm:predictive-residual-stability` (`bayesian_representation.tex` L51–68).
- **What this does NOT show:** `2507.08802` does *not* refute constructive abstractions restricted to fixed structural/basis families (`2610.18155`, `2301.04709`, `2211.12270`), nor does `2610.18155` prove whether gradient descent converges to block-identifiable modules in finite threshold nets (`Gap A10`). Also see `Hyvärinen et al. 1805.08651` (`Th1` L329): i.i.d. unmodulated Boolean tasks lack auxiliary-variable variability, explaining non-unique threshold isomers (`P045`).

---

## 4. Reclassify `H45.4` / `P155`–`P159` (`R3`) as Prior-Art Replication Under Forced Interpolation (`Gap A8`)

- **Proposed statement:** Do not claim priority on either (i) exact MDL / minimal threshold-net degradation under label noise, or (ii) GP/kernel outperforming SGD under label noise. Restrict remaining empirical questions in `R3` / `Gap A8` to unforced, early-stopped, and weight-decayed training compared against exact kernel-angle thresholds `\gamma_c(\varepsilon)`.
- **Exact evidence:**
  - **Mingard, Valle-Pérez, Skalse & Louis (`arXiv:2006.15191`, Full text):** `appendices.tex` §E L724–726 already shows on 20% label noise that `"\varepsilon_{G,SGD}=13.4\% and \varepsilon_{G,GP}=5.80\%"` with `"\sum_{f\in F} P_B(f\|S)=99.3\%"` vs `"\sum_{f\in F} P_{SGD}(f\|S)=24.3\%"` (§G L762–768 on 7-bit Boolean networks).
  - **Manoj & Srebro (`arXiv:2302.07263`, Full text):** `paper_results.tex` `thm:agnostic_main` (L41–49: `1-2^{-H(\alpha)}`) and `thm:random_label_noise_main` (L53–65: `2\Lstar(1-\Lstar)`).
  - **Harel et al. (`arXiv:2410.19092`, Full text):** `01_main.tex` `thm: minsize interpolator bound` (L606–639: `1-2^{-H(\errorRate)}+o(1)`, `2\errorRate(1-\errorRate)`) and `thm: posterior sampling bound` (L685–698).
  - **Chatterjee & Sudijono (`arXiv:2409.12446` / *AoS* 2026, Full text):** `main.tex` `thm:generalization with noise` (L1278–1288: `C\rho + O(1/n)`), while §7 Limitations (L1390) explicitly notes `"Our theorem also does not say anything about neural networks trained with gradient-based methods"`.
  - **Boursier & Flammarion (`arXiv:2410.02348`, Full text):** `main.tex` `thm:noconvergence` (L397–405) proves unforced small-init 2-layer ReLU gradient flow above `n \ge \Theta(d^3\log d)` does not interpolate label noise.
  - **Boncoraglio & Zdeborová (`arXiv:2610.33846`, Full text):** `main_arxiv.tex` L255 & L288 define the exact critical kernel angle `\gamma_c(\varepsilon)` governing when kernel gradient flow benefits from early stopping under noise.
- **What this does NOT show:** Prior bounds on forced interpolators (`2302.07263`, `2410.19092`, `2409.12446`) do *not* settle whether regularizing or early-stopping small threshold networks on finite Boolean tasks recovers the solver-certified minimum circuit before memorizing minority noise (`Gap A8`), nor do they provide the fine-grained per-conflict-input trajectory (`P152`) on clean Boolean data.

---

## 5. Bound `C15'` (`P094`, `P111`), `C18` (`P121`), and `C19'` (`P127`–`P129`, `P152`, `P154`) by Optimizer & Feature-Quality Caveats

- **Proposed statement:**
  1. Restrict `C15'` ("initialization prior survives training") to low-regularization / low-LR SGD or lazy regimes; adaptive optimizers (Adam) and tuned weight decay erase initialization-scale sensitivity.
  2. Do not infer feature/circuit quality in `C18` from scalar kernel-alignment or NTK-departure magnitude alone; pair kernel metrics with functional generalization and causal intervention checks.
  3. Frame `P152` timing inside saddle-to-saddle / leap dynamics (`2512.20607`, `2302.11055`), limiting novelty to the conflict-point trajectory against solver-certified minimum threshold circuits.
- **Exact evidence:**
  - **Das et al. (`arXiv:2605.29152`, Full text):** `arxiv.tex` Abstract L106 (`"Low-learning-rate SGD can interpolate while still remembering its initialization: on ResNet-9 with batch size b=128, test accuracy varies by 26.5 percentage points across initialization scales despite \ge99.5\% training accuracy... In contrast, Adam-family methods largely erase the dependence"`) and L1232 (`"|\Delta|=0.0 pp at b=128"`).
  - **Göring et al. (`arXiv:2507.19680`, Full text):** `sample.tex` Abstract L155 & Claim box L217 (`"FL strength is decoupled from feature quality, measured by the FL gap \Delta_{\operatorname{NT}}"`) and L283–286, L318–319 (`S_{NT}`, `S_{CK}` fail to distinguish true vs shuffled labels at `\gamma=0.01`).
  - **Zhang, Saxe & Latham (`arXiv:2512.20607`, Full text):** `all.tex` Abstract L48 (`"linear networks learn solutions of increasing rank, ReLU networks learn solutions with an increasing number of kinks..."`) and `main.tex` `thm:fixed-point` / `thm:narrow-manifold`.
  - **Abbe, Boix-Adserà & Misiakiewicz (`arXiv:2302.11055`, Full text):** `main.tex` Abstract L648–654 (`"\Tilde \Theta (d^{\max(\mathrm{Leap}(f),2)})"`, sequential support learning via saddle-to-saddle jumps).
- **What this does NOT show:** `2605.29152` studies ResNet-9 image classification rather than small Boolean threshold MLPs (`C15'`); `2507.19680` shows metric decoupling at `\gamma=0.01`, not that exact conflict-point agreement with a solver-certified minimum circuit is spurious; and `2512.20607` / `2302.11055` do not measure conflict-input trajectories against exact minimum Boolean threshold circuits.

---

## 6. Frame `Theorem 15` (`P069`) as an Input-Symmetry Instantiation & Keep Curie Exponent (`Gap A3`) Open

- **Proposed statement:** Present `Theorem 15` (`P069`, mechanized in Lean on `gemini/G1`) solely as semplex's input-symmetry instantiation of general gradient-equivariance theorems already established in the literature. Treat only the quantitative Curie orbit-exponent law (`P070` / `Gap A3`) as open relative to prior art.
- **Exact evidence:**
  - **Yang & Ziyin (`arXiv:2512.21447`, Full text):** `main.tex` `thm:main-discrete` (L321–342) proves `$\nabla L({\boldsymbol{\theta}})\circ \widehat X({\boldsymbol{\theta}},{\boldsymbol{\lambda}}_0) = \nabla L({\boldsymbol{\theta}})$` and discrete Hessian conservation on `\mathrm{Fix}(H,\lambda_0)` (`thm:main` L258–305 for continuous symmetries).
  - **Ziyin, Xu, Poggio & Chuang (`arXiv:2502.05300`, Full text):** `arxiv.tex` `theo: complexity` (L363–365) establishes parameter-reduced symmetry dynamics and qualitative attraction/merging (`conjecture` L377–381, `theo: alignment` L458–466).
- **What this does NOT show:** Neither `2512.21447` nor `2502.05300` derives an orbit-cardinality power law over solver-certified minimum Boolean circuits (`|\mathrm{orbit}|^\beta` with `\beta < 0`), nor do they mechanize SGD/AdamW training invariance in Lean 4 (`gemini/G1`).

---

## 7. Clarify `Gap B2` (`P124`, `P148`, `P040`) Barriers: `2410.19092` Is Upper-Bound Only & SoS Fails Without Structure

- **Proposed statement:** Record two structural updates on `Gap B2` (certifying partial-function minimum threshold circuit lower bounds):
  1. `Harel et al. (2410.19092)` does **not** solve `Gap B2` because `thm: partial fctn net cxty` proves an upper bound (existence), not a lower bound.
  2. Generic Sum-of-Squares / SDP relaxations cannot efficiently certify super-polynomial-circuit lower bounds because of `Austrin & Risse (2311.12994)`; practical lower-bound certification in `cerp` must rely on symmetry quotienting, branch-and-bound / SAT+LRAT proofs, and domain structure (`gemini/G3`, `gemini/G5`).
- **Exact evidence:**
  - **Harel et al. (`arXiv:2410.19092`, Full text):** `01_main.tex` `thm: partial fctn net cxty` (L410–431) constructs a depth-14 threshold network with weight bounded by `$\log\binom{N}{N_1} + (\log\binom{N}{\Ncorrupt})^{3/4}\polylog N + O(d_0^2 \log N)$` — an *upper bound* on size/weight.
  - **Austrin & Risse (`arXiv:2311.12994`, Abstract + sections):** `abstract.tex` L3–6 proves `"for every Boolean function f: \{0,1\}^n \rightarrow \{0,1\}, SoS requires degree \Omega(s^{1-\epsilon}) to prove that f does not have circuits of size s (for any s > \poly(n))"`.
  - **Related hardness baselines:** `Hirahara, Ilango & Loff (arXiv:2507.10426, Partial LaTeX source)` `main.tex` L197 proves exact deterministic communication complexity `\CC(f)` is NP-hard; `Ilango (FOCS 2020, Metadata only)` and `Hirahara & Ilango (FOCS 2025, Metadata only)` flag NP-hardness around partial-function MCSP (details paywalled).
- **What this does NOT show:** Asymptotic SoS and MCSP worst-case barriers do *not* preclude fast certified lower bounds for structured small-`n` partial functions or symmetric classes (`gemini/G3` `n=8,10`; `gemini/G5` `parity4 >= 5`), which avoid generic dense algebraic relaxations.

---

## 8. Statistical Quotient Coarsening (`Gap C1`) & Extrinsic Symbol Grounding Limits (`P146`)

- **Proposed statement:**
  1. In `Gap C1` (`P135`, `P139`), treat finite-sample Myhill–Nerode quotient coarsening via kernel MMD (`Pow 2026`) as partial prior art for sample-dependent equivalence-class merging; restrict semplex's contribution to certified finite-domain query trees / neural state extraction (`P136`).
  2. Restrict philosophical claims around `P146` (`Peircean semiosis` / `THEORY §3.4`) strictly to *intra-systemic* distinguishability on protocol frames, explicitly excluding extrinsic referential world-grounding (`2304.01481`).
- **Exact evidence:**
  - **Pow (`10.68852/pf-261114.000002`, 2026, Abstract only):** Crossref abstract reports an `"alphabet-free trajectory bound N = O (B\log (B/\delta)/\varepsilon_(MMD)^2 + B^2\log (1/\delta))"` with finite-sample behavior `"as a resolution effect: distinctions below the test's detection scale are merged"`.
  - **Coelho Mollo & Millière (`arXiv:2304.01481`, Abstract + sections + Crossref abstract):** Crossref abstract specifies `"referential grounding is achieved when a system's internal states satisfy two conditions... (1) they stand in appropriate causal-informational relations to the world, and (2) they have a history of selection"` (`main.tex` L143: `"hook onto the world"`).
- **What this does NOT show:** `Pow 2026` was inspected at `Abstract only` level (full proofs and applicability to finite neural threshold representations remain unverified), and `2304.01481` does not invalidate finite-frame syntactic/operational equivalence as a formal engineering invariant.

---

# Proposed Claims & Literature Corrections — Branch `gemini/G12`

## G12-1. Location & Scope Clarifications for `HANDOFF_G7.md` Spot-Checks (`2006.15191`, `2507.08802`, `2602.16823`)

- **Proposed statement:** Update the section/hypothesis metadata on `P165` (from G7's spot-check flags) after primary-source verification: (1) `2006.15191` 20% label-corruption MNIST figures appear in **Section 5** (`sample.tex` `fig:random` L731–732) and **Appendix D** (`appendices.tex` `fig:appendix_corrupted_mnist` L723–726, NOT Appendix E `app:CSR` — `%\section{...app:rand_label}` at L683 is commented out; 7-bit Boolean nets are in **Appendix F** `app:bool_func` L762–768), with `\eg = \langle \epsilon_G \rangle` (`\eg=13.4\% for SGD` vs `\eg_{GP}=5.80\%`); (2) `2507.08802` `theorem:existing_causalmap_for_any_algorithm` appears in **Section 4** (`sec:main_theorem`, `main.tex` L579–581) and explicitly assumes countable input-space (`assumption:Countable_infinite`) and matchable partial-orderings (`assumption:minimalrequirements`) in addition to layer injectivity, strict output-surjectivity, and task solving; (3) `2602.16823` `lem:blocking_sets_equivalence` and `mhs_main_theorem_appendix` are confirmed verbatim in **Appendix B, Subsection B.7** (`app:proof_of_prop_mhs_duality`, `iclr2026_conference.tex` L2769–2791).
- **Exact evidence:** `charter/LITERATURE_REVIEW.md` §5 rows for `2006.15191`, `2507.08802`, and `2602.16823`, plus verbatim quotes and LaTeX line citations in `HANDOFF_G12.md`.
- **What this does NOT show:** Does not alter the substantive prior-art conclusions of `P165` (`R3` label noise, unconstrained `R2`, or blocking-set/MHS duality).

---

## G12-2. Automata Shortcut Isomers (`2210.10749`), Energy-Descent Baselines (`2611.17309`), Weight-Space Controls (`WSP-Gym`, `2611.14418`, `2611.14413`), and Infinite-Frame Effective Stone Duality (`Downey & Melnikov 2026`, `Montalbán 2019`)

- **Proposed statement:**
  1. Treat Krohn–Rhodes $O(1)$-depth shortcut circuits (`arXiv:2210.10749`) as a formal mechanism explaining finite-horizon equivalence vs interventional/OOD divergence (`P045`, `R2`, `Gap A9`/`A10`): training should be tested on causal state interventions and OOD horizon generalization, and paired with published symmetry-emergence dual beliefs (`10.1126/sciadv.aeh0773`).
  2. Adopt mean-field Potts energy descent (`CRAM`, `arXiv:2611.17309`) as an experimental baseline for pairwise exclusion constraint learning (`cerp/localrules.py`), and enforce matched-SNR / random-edit controls (`WSP-Gym`) whenever evaluating direct weight-space circuit edits.
  3. Cite `2611.14418` and `2611.14413` as hardware-costed inference parallels to `P137` (`threshold_escalation_optimal`) and `P077`/`G4` ($C_4$ Reynolds orbit averaging), respectively, and scope infinite observation-frame generalizations of `P008`/`P009` (`THEORY §2`) by the Feiner / Downey–Jockusch / Downey–Melnikov effective Stone duality boundary (`Theorem A` $\to$ `Theorem B`).
- **Exact evidence:**
  - **Liu et al. (`arXiv:2210.10749`, Full text):** `arxiv_files/3-theory.tex` `thm:shortcut-log-depth` ($O(\log T)$ depth), `thm:shortcut-const-depth` ($O(|Q|^2\log|Q|)$ constant depth for solvable semiautomata), and `thm:barrington-lower-bound` ($\mathsf{TC}^0 \neq \mathsf{NC}^1$ barrier for non-solvable semiautomata).
  - **Rosas (`10.1126/sciadv.aeh0773`, *Science Advances* 2026, Crossref/OpenAlex abstract):** `"dynamical processes that are equivariant with respect to a symmetry group give rise to multiple emergent macroscopic levels arranged according to the algebraic structure of the symmetry. The same symmetries shape the Bayesian beliefs of an observer with only partial access to the system"`.
  - **Hoover, Blayney & Whittington (`arXiv:2611.17309`, Full text):** `arxiv_main.tex` `eq:core` & `eq:flow` (`E_{\theta}(p) = \beta^{-1}\sum_i p_i^\top \log p_i + \frac{1}{2}\sum_{i\neq j} p_i^\top W_{ij} p_j + \sum_i b_i^\top p_i`), solving `99.996%` of Sudoku-Extreme in `42 ms` (`>=1,000x` faster and `>=282x` fewer FLOPs than looped models).
  - **emeraldant (`WSP-Gym`, Full text `README.md`):** SFT+RL (`Inkling 2 Small`) repairs `82.9% [79.4, 86.5]` of faulty small ReLU nets in `~38` tokens, whereas on `Qwen3.5-0.8B` (`MATH-500`) `"a random edit to the same table reaches 37.6%, and across eight layers none of the trained models beat random edits"` (`38%`).
  - **Khan, L & Misri (`arXiv:2611.14418` & `arXiv:2611.14413`, Full text PDFs):** `2611.14418` reports entropy AUC `0.93` and `94%` margin-gate flip recall at `15%` escalation budget over `36,724` steps, with `0.874x` live bytes bounded by `bf16` head reads (`311.2 MB`); `2611.14413` p. 5 states `"the average over a full orbit is invariant to cyclic reordering, so only the difference between orbits is left"` (`+12.6` points at 4 bits on `0.6B`).
  - **Downey & Melnikov (Springer 2026, ToC + pp. 8, 11) & Montalbán (`CSTpart1.pdf`, Ch. I–X):** `Theorem A` (p. 8) separates c.e.-presented Boolean algebras (not necessarily computable) from low Boolean algebras; `Theorem B` (p. 11) transfers this via effective Stone duality to separate computable Polish spaces from right-c.e. Stone spaces and computably compact spaces.
- **What this does NOT show:** `2210.10749` analyzes Transformers over sequences rather than 2-layer Boolean threshold MLPs (`C19'`); `2611.17309` (`CRAM`) does not give minimum-circuit proofs; `2611.14418` live GSM8K paired CIs (`p=0.080`) do not separate the entropy gate from endpoints; `2601.06002` (*Effective Semantic Isomers*), `2609.12303`, and `2611.16267` (`Causals`) contain no formal bridge to `cerp` minimal-circuit theory; and Downey–Melnikov / Montalbán address infinite computable structures rather than finite truth-table synthesis.

# Proposed claims from `gemini/G8` (`Gap B2` — cost-4 at `n = 8`)

1. **`compile_partial` decoupled width-3 solver (`layered(n, [3])`):** Replacing generic indicator/ReLU-style `solve(..., layered(n, [3]))` with an exact case split `_solve_three_halfspaces` over the 5 canonical 3-input threshold P-classes (`or_and`, `and_or`, `maj3`, `and3`, `or3`, with `W=1` filtering of `[2,1,1]`) solves 100 / 100 partial `n = 8` (`192/256` care) benchmarks to kernel-verified `W <= 4` circuits in `1.66s` median (`14.11s` max), verified by `tests/test_bounds_partial.py::test_solve_three_halfspaces_all_gates_and_w1` and `experiments/results/g8_cost4_benchmark.json`. **Does NOT show:** completeness for non-layered/skip topologies or `W > 4` unless invoked with larger `W`.

2. **Fixed `W = 4` vs unbounded-weight cost-4 minimality separation (`experiments/results/g8_cost4_benchmark.json`):** On 100 random `n = 8` 3-hidden-unit step nets (seed `8820`, full-table `layered(8, [2])` `W = 4` UNSAT) evaluated on `192/256` care points (seed `8821`), `compile_partial(f, 8, care, W=4, max_width=4, time_limit=60.0, workers=4)` verified `100 / 100`, with `6` collapsing to `cost = 3` (`W <= 4`), `81 / 94` (`86.17%`) certified `cost = 4` minimal via `kernel_bounds.check_not_two_halfspaces_partial`, and `13 / 94` (`13.83%`) `cost3_solver_unsat` (below the pre-registered `90%` threshold for the fixed-`W=4` cohort). Weight-bound auditing shows `13 / 13` (`100%`) of those uncertified `cost = 4` targets admit a kernel-verified width-2 (`cost = 3`) circuit on the care set at `|w| <= 16` (`11` at `|w| <= 8`, and `11` already had width-2 `|w| <= 16` solutions on the full 256-row table), and the single uncertified `cost = 3` target (`idx = 56`) admits a `cost = 1` separator at `|w| <= 16`; thus `not_two_halfspaces_cert_partial` certified `81 / 81` (`100%`) of all genuinely unbounded-weight cost-4 care instances (`g8_cost4_benchmark.json:weight_bound_audit`). **Does NOT show:** certificate scalability beyond `n = 8` or `len(universe) <= 20` inside `kernel_bounds.check_not_two_halfspaces_partial`, nor minimality against width-3 non-layered nets.

# Proposed claims from `gemini/G9` (`Gap A10` — symmetry orbits of minimum circuits)

1. **Exact `G_f`-orbit census of minimum layered threshold circuits on `n <= 4` (`experiments/results/g9_orbits.json`):** Across all `242` NPN classes on `n <= 4` (`2, 4, 14, 222`, where `|w| <= 3` covers 100% of all LTFs and minimum cost is always achieved at depth `<= 2`), under unoriented hyperplane-partition equivalence (`g <-> ~g`), **`80 / 242` (`33.06%`)** have `num_orbits == 1` (`2/2` at `n=1`, `4/4` at `n=2`, `9/14` at `n=3`, `65/222` at `n=4`: `15/15` cost-1, `50/128` cost-3, `0/78` cost-4, `0/1` cost-5 `parity4` [`12,404` circuits, `52` orbits]), verified against full brute force on `n <= 3` (`tests/test_g9_orbits.py`) and Orbit-Stabilizer invariants across all `242` classes (`g9_orbits.json:aggregate_n_le_4`). Under strict oriented hidden-function equivalence (distinguishing `g` and `~g`), **`26 / 242` (`10.74%`)** have `1` orbit (`26 / 26` cost-1, `0 / 216` non-threshold). **Does NOT show:** behavior for continuous/unbounded weights at depth >= 3 when non-minimal circuits are included, nor `n >= 5` functions of cost >= 4.

2. **`n = 5, cost <= 3 (|w| <= 3)` orbit extension (`experiments/results/g9_orbits.json:dims.5_cost_le_3`):** With hidden and output weights bounded by `|w| <= 3`, `32,812` 5-input LTFs split into `42` `cost = 1` and `7,253` `cost = 3` NPN classes (`7,295` total, 100% completed in `188.98s`). Under unoriented hyperplane equivalence, **`3,725 / 7,295` (`51.06%`)** have `1` `G_f`-orbit (`42 / 42` at `cost = 1`, `3,683 / 7,253` = `50.78%` at `cost = 3`); under oriented equivalence, `42 / 7,295` (`0.58%`) have `1` orbit. **Does NOT show:** orbit counts for `n = 5` LTFs requiring `|w| >= 4` (beyond the `32,812` out of `94,572` LTFs covered by `|w| <= 3`) or any `n = 5` classes with `cost >= 4`.

## 9. Multi-Layer Threshold Miter Scaling in Lean Kernel `decide` at `n = 6–8` (`G10`)

- **Proposed statement:** Using the verified PB Tseitin LRAT checker (`Cerp.tseitinTNetMiterPB_lrat_unsat_implies_equiv`, `native=False`, `pb=True`, standard axioms `[propext, Classical.choice, Quot.sound]` only), Lean 4 kernel `decide` verifies non-degenerate full-fan-in multi-layer threshold networks against `Expr` specifications in `< 120s` at `n = 6` (2 hidden layers `[6]->[2]->[2]->1`, `53.725s`; `[6]->[4]->[2]->1`, `104.442s`; up to 4 hidden layers `[6]->[2]->[2]->[2]->[2]->1`, `56.276s`) and `n = 8` (1 hidden layer `[8]->[2]->1`, `75.414s`). Scaling past `120s` is governed by two empirically distinct Lean bottlenecks: (1) kernel `checkLratT` WHNF reduction and repeated `tseitinTNetMiterPB` evaluation (`3.535s` elaboration -> `52.609s` `checkLratT` at 30 steps / 238 clauses), and (2) superlinear Lean front-end elaboration explosion of the `Ls` / `tns` / `eSpec` terms (`2.181s` at 16 steps -> `24.71s` at 41 steps -> `> 150.0s` timeout in `elab_only` even before `by decide` at 104 steps / 673 clauses). On `[8]->[2]->1`, `pbEncodeLayer` top-down reachable-sum DP is invariant to uniform scaling (`max|w|=16`, `73.308s`) and remains fast for strictly superincreasing weights (`[53,26,12,5]`, `80.313s`), whereas non-superincreasing colliding weights (`[17,13,11,7]`, 469 clauses, 64 steps; `[5,4,3,2]`, 517 clauses, 61 steps) cross `> 150s`.
- **Exact evidence:** `experiments/g10_miter_bench.py`, `experiments/results/g10_miter_timings.json`, `tests/test_lean.py` (`test_tnet_lean_n6_two_hidden_layer_kernel_decide`, `test_tnet_lean_n8_one_hidden_layer_kernel_decide`), and `HANDOFF_G10.md`.
- **What this does NOT show:** Kernel `decide` does not scale to arbitrary wide/dense `n = 8` hidden layers (`[8]->[3]->1`, `[8]->[4]->1`, `[8]->[8]->1` all hit `> 150s`) or large LRAT step counts (`>= 61` steps / `>= 469` clauses) without moving to pre-computed / binary-encoded / reflected certificates (`bv_decide`-style reflection or external proof-producing compilation).

## 10. Continuous Gaussian Prior Signed-Permutation Invariance (`Gap C1` / `G11`)

- **Proposed statement:** Close the continuous measure-theoretic hypothesis of `P160` (`Theorem 15`, previously limited in `proofs/lean/Theory.lean` to discrete weighted lists via `EnsembleInvariant`): in an isolated Mathlib `v4.12.0` package (`proofs/lean-mathlib/CerpMathlib.lean`, leaving `proofs/lean/` untouched), the i.i.d. centered Gaussian product measure `gaussianProd n v := Measure.pi (fun _ : Fin n => gaussianReal 0 v)` on `Fin n → ℝ` is invariant under every signed coordinate permutation `actRealVec σ` (`gaussianProd_map_actRealVec`), its pushforward under any measurable equivariant trajectory `step^[t]` preserves `actRealVec σ` invariance (`gaussianProd_pushforward_equivariant`), and for any measurable equivariant readout `readout : (Fin n → ℝ) → C` into a measurable-singleton circuit space `C`, pushed-forward probability mass on `{actC tgt}` equals `{tgt}` (`theorem15_gaussian_iter_circuit_mass_eq`), using only standard axioms `[propext, Classical.choice, Quot.sound]`.
- **Exact evidence:** `proofs/lean-mathlib/CerpMathlib.lean`, `proofs/lean-mathlib/AuditMathlib.lean` (`lake build CerpMathlib` `exit=0` in `195.23s`; `lake env lean AuditMathlib.lean` `exit=0` in `163.42s`, standard axioms only), and `HANDOFF_G11.md`.
- **What this does NOT show:** `proofs/lean/Theory.lean` (`PFT.AdamScalar`, `PFT.gdStep`, `PFT.adamwStep`) is not imported across package boundaries; instantiating `AdamScalar ℝ` with stabilized continuous `ℝ` arithmetic and proving Borel measurability of continuous `gdStep`/`adamwStep` and piecewise-constant threshold `readout` remain unformalized integration glue.

## 11. Mechanistic Thermodynamics & Causal Inertia of `G(λ)` (`master-principle-mech`)

- **Proposed statement:** (1) Formalized in `proofs/lean-mathlib/MasterPrincipleMech.lean` (Mathlib `v4.12.0`, standard axioms `[propext, Classical.choice, Quot.sound]` only): over any finite spectrum `(w, μ)` with `w >= 0` and two distinct active modes, the normalized Dirichlet energy `normDirichlet w μ lam` satisfies the fluctuation-dissipation theorem `d/dlam ⟨μ⟩_λ = - Var_λ(μ) < 0` (`normDirichlet_hasDerivAt_neg_var`, `normDirichlet_strictAnti`), uniquely identifying `lam` (`lambda_unique_of_dirichlet`), and `LeakyRNN` step inertia `(1 - α) h + α u` scales squared displacement by `α^2` (`leaky_step_displacement_sq`). (2) Empirically, on `12` fresh disjoint monoids (`6 free + 6 mixed`) using strictly out-of-sample `LAM_KIN = {"gru_lin": 0.857, "gru_mlp": 1.085, "lstm_mlp": 1.137, "rnn_mlp": 1.782}` (`HMM.1a = HELD`, `HMM.1b = HELD`, `HMM.2 = HELD`): all `4/4` architectures beat frozen `LAM0` in mean `cos_G` (`0.8132–0.9543` vs `0.8092–0.9487`), ALL `4/4` architectures including `rnn_mlp` (`n = 9`, `0.8132 > 0.8048 [Wc]`) and `lstm_mlp` (`n = 12`, `0.8886 > 0.8567 [WcWo]`) beat all 6 rivals in both mean and median Gram cosine (`100%` beat `o` where `cos(G, o) < 0.95`), with max `|mean_cos(G_KIN) - mean_cos(G_CAL)| = 0.0036 <= 0.02`.
- **Exact evidence:** `proofs/lean-mathlib/MasterPrincipleMech.lean`, `proofs/lean-mathlib/AuditMasterPrincipleMech.lean` (`lake build MasterPrincipleMech` `exit=0` in `841.05s`, `AUDIT_RC=0`), `experiments/master_principle_mech.py`, `experiments/results/master_principle_mech_predictions.json`, `experiments/results/master_principle_mech.json`, and `HANDOFF_MASTER_PRINCIPLE_MECH.md`.
- **What this does NOT show:** Under the strict pre-registered `fit >= 0.90` gate at `1,000` training steps, causal `LeakyRNN` step-inertia `α = 0.25` (`HMM.3`: `4/4` = `100%` lower `kin_norm` & higher `λ_emp`) and explicit step-0 Dirichlet regularization `μ = 0.20` (`HMM.4`: `2/2` = `100%` lower `kin_norm`, collapsed fit on `10/12` tasks) returned **`NO VERDICT`** (`< 8` converged pairs; consequently `HMM.5 = HELD` [`wd_3e-2` lowered `kin_norm` on `4/8 = 50%`] is underpowered against `n=4`/`n=2`), although unconditionally `12/12` units lowered `kin_norm` for `α = 0.25` and `α = 0.5`. Lean proofs operate over finite eigenspectra `(w, μ)` rather than general non-commuting matrix exponentials.
