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
