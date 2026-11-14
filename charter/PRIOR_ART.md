# Prior-art map (sweep of 2026-11-14)

What is already known on each front of the project, what that does to our claims, and what is still unread. This file is the index; reading notes go in `LITERATURE_REVIEW.md` §5.

**Coverage, stated plainly.** Eight topical searches (alphaXiv index, about 130 candidate papers returned) and one Consensus search. This is a structured sweep, not an exhaustive one: non-arXiv literature (books, older journals, logic and semantics) was reached only through one search. Each entry carries its read status:

- **R** = main text or a full structured report read;
- **P** = abstract, introduction and theorem statements read;
- **A** = abstract or listing only;
- **M** = known from memory, not opened in this sweep. An **M** entry must be opened before it is cited as support (AGENTS.md rule 7).

## 1. Verdict per claim of ours

| Our claim | Closest prior work | Verdict |
|---|---|---|
| C19′: trained nets move from the kernel prior toward the minimum-circuit completion (P127–P129, P152, P154) | Simplicity bias of the parameter–function map (Valle-Pérez et al. 1805.08522, A); Mingard et al. 2505.24060 (P): Boolean data, a network–DNF correspondence, generalization tracks prior probability and DNF complexity; Harel et al. 2410.19092 (P): minimum-size threshold nets that fit noisy data overfit only mildly, and random interpolating nets generalize about as well as minimum-size ones | **Anticipated in general form.** "Nets prefer low-complexity functions" and "minimum-size interpolators generalize" are established. What we add: (i) gradient-trained nets compared input by input with a *certified* minimum threshold circuit; (ii) the measure "where the net leaves its own kernel, which way does it go"; (iii) the lazy-regime arm; (iv) the timing; (v) the failure on real data. Present it as a measurement inside this literature, not as a new principle. |
| Timing: kernel-like first, Occam later (P152) | Leap complexity and saddle-to-saddle (Abbe et al. 2302.11055, A); saddle-to-saddle explains simplicity bias (2512.20607, A); increasing complexity over training (2211.11567, A; Nakkiran et al., M); Nichani et al. 2305.06986 (R) | **Partly anticipated.** "Simple first, complex later" is known. The kernel-smoothed-target phase followed by a turn toward the minimum circuit, measured on conflict points, was not found. |
| Occam pull weakens with label noise; kernel beats the interpolating net on noisy real tasks (P155, P156) | Early learning then memorization (Arpit et al. 1706.05394, A; Liu et al. 2007.00151, A; Li et al. 2019, A); taxonomy of overfitting (Mallinar et al. 2207.06569, A); early stopping under label noise for kernel flow (2610.33846, A); MDL interpolation is tempered (Manoj & Srebro 2302.07263, A); Harel et al. (P) | **Expected from prior work.** Nets forced to fit noisy labels generalize worse than early-stopped or kernel predictors, and exact minimum-size interpolators pay a known price for noise. Our real-data protocol forced interpolation of noisy majority labels. H45.4's outcome is a replication of this, not a discovery. |
| Theorem 15: mechanism choice is equivariant under the task's symmetry group (P069) | Equivariance of gradient methods under symmetric losses is a standard tool (equivariance toolbox 2512.21447, A; Ziyin et al. 2502.05300, A; Yang et al. 2510.02670, R, for hidden-unit permutations; Abbe & Boix-Adserà on GD equivariance, M) | **An instance of a known principle.** Ours is the input-symmetry version applied to *which circuit is found*. Mechanizing it (Gemini G1) is still worth doing for the ledger; it is not a novelty claim. |
| Curie bias: orbit mass ∝ \|orbit\|^β with β < 0 (P07x) | Symmetric solutions are attracting (Ziyin et al., A); symmetry breaking in learning (2611.06718, A; 2609.01768, A) | **Open as a quantitative law.** Attraction to symmetric solutions is known qualitatively. The exponent law over orbits of exact minimal circuits was not found. |
| Unit-level selection law, tilt and activation dependence (C13) | Neural redshift (2403.02241, A): the prior over functions depends on the activation | **Partly anticipated** at the level "activation shapes the prior". The indicator-alignment account (R² predicts λ) was not found. |
| Protocol frames: determining sets ↔ hitting sets; minimal sufficient observation sets (THEORY §2) | Rough-set reducts and formal concept analysis (acknowledged in P004); computational mechanics: causal states are the minimal sufficient statistic of prediction (Shai et al. 2405.15943, R; Crutchfield, M); Bayes-sufficient representations in supervised learning (2606.04045, A) | **The core idea has a long history.** Our contribution is the exact, finite, kernel-checked version with compilation. 2606.04045 must be read: it may state our supervised sufficiency result. |
| Verified compilation of functions to threshold nets with a Lean checker (P147, P141) | Tracr (2301.05062, A), ALTA (2410.18077, A), decompiling transformers to RASP (2602.08857, A), synthesis and verification of C-RASP programs (2602.16473, A), circuit discovery with provable guarantees (2602.16823, A), Elser: learning with Boolean threshold functions by constraint projection (Consensus, A) | **Crowded.** Compile-to-weights and verify-a-circuit both exist for transformers. Not found: *minimum-size* certificates (lower bounds) and a proof-assistant kernel in the loop. That is our niche; say so narrowly. |

## 2. What the map says to do

1. **Stop presenting C19′ as a new principle.** It is a sharp, certified measurement of a known bias, with two additions that look new (the direction-of-departure measure and the real-data boundary).
2. **The noise result needs the exact frontier, not another dose–response alone.** Prior theory covers exact interpolators. What nobody seems to have is the *exact, certified* cost-versus-errors frontier for a task and the point on it where gradient training lands (Spike 46 design).
3. **The most original ground is deterministic semantics**, see §3. Simplicity bias is crowded; exact canonical structure with certificates is not.

## 3. Research directions for deterministic (analytic) semantic grounding

Each direction states the principle, what is already known, what would be new, and a first experiment that fits the atlas.

### R1. Meaning as the canonical quotient (query-relative causal states)

- **Principle.** The meaning of an input, for a task, is its class in the coarsest partition of inputs that still determines the answer. This partition is unique and computable. It is the supervised, finite analogue of causal states (minimal sufficient statistics of prediction) and of Myhill–Nerode classes.
- **Known.** Causal states and their linear representation in transformers trained on hidden-Markov data (Shai et al., R). Sufficiency in supervised learning (2606.04045, A). Our frames give the exact lattice of sufficient partitions (THEORY §2).
- **New.** A learning statement with certificates: a trained net's hidden layer factors through a partition that lies between the canonical quotient and the partition induced by a minimum circuit's first layer, and the theory says *which one* and *when*. Gemini's exploratory Spike 37 (86–89% of units are members or coarsenings of minimal determining sets) points this way and is not pre-registered.
- **First experiment.** For each atlas target, compute the canonical quotient and the first-layer partitions of all minimum circuits. Measure, over training, whether hidden activations are a function of the quotient class (decodability) and which minimum-circuit partition they converge to.

### R2. Identifiability of mechanisms (how much the function fixes the circuit)

- **Principle.** Grounding is deterministic exactly when the mechanism is identifiable: the function plus a cost bound determine the circuit up to a computable symmetry group.
- **Known.** Identifiability theory for latent variables (nonlinear ICA, causal representation learning; 2610.18155, A). Causal abstraction as the definition of "implements" (Geiger et al. 2301.04709, A) and its non-uniqueness problem (2507.08802, A).
- **New.** An exact count: for every function in the atlas, the number of orbits of minimum circuits under the task's symmetry group. One orbit means the mechanism is identifiable; more than one measures the semantic indeterminacy. Conjecture: training's choice among orbits follows the Curie law, so the indeterminacy is resolved predictably.
- **First experiment.** Enumerate minimum circuits per function at n ≤ 5 (the atlas has them), quotient by the symmetry group, and tabulate the indeterminacy. Lean target: uniqueness up to symmetry for threshold functions (cost 1).

### R3. The exact cost–error frontier (noise-tolerant Occam)

- **Principle.** With noisy labels the right object is the Pareto frontier of circuit cost against misfit labels, a two-part code. It is computable with the compiler.
- **Known.** MDL; tempered overfitting of exact minimum-size interpolators (Harel et al., P; Manoj & Srebro, A; Chatterjee & Sudijono, A).
- **New.** Computing the certified frontier per task and locating trained nets on it as a function of weight decay and training time.
- **First experiment.** Spike 46.

### R4. Semantics that composes (quantitative frame morphisms)

- **Principle.** A structuring of meaning is useful only if it survives composition with a stated loss. Gemini's Lean §17 has pull-back of ε-determinacy along frame morphisms and an obstruction example.
- **Known.** Compositional and causal abstraction (2602.16612, A); trace-relating compilation (Abate et al., per Gemini's §3c).
- **New.** A loss budget that adds along a compiled pipeline and is checked by the kernel at each stage, so that a composed circuit carries a certified bound on how much meaning it lost.
- **First experiment.** Compile a factored function through the Ur-Compiler with a per-stage budget and check the end-to-end bound.

**Suggested order:** R3 (next spike, repairs the real-data failure), then R1 (the main original line), with R2 in parallel because it needs only enumeration and Lean.

## 4. Reading queue (found, not yet read)

These must be read before any claim leans on them. Marked with the reason.

| Paper | Why it matters |
|---|---|
| Bayes-Sufficient Representations in Supervised Learning, 2606.04045 | May state our supervised sufficiency result (R1) |
| Valle-Pérez, Camargo, Louis, 1805.08522; Mingard et al., "Is SGD a Bayesian sampler?" (M) | The baseline for C17 and C19′ |
| Manoj & Srebro, 2302.07263; Chatterjee & Sudijono (Annals of Statistics 2026) | MDL interpolators and noise (R3) |
| Harel et al., 2410.19092: proofs and the partial-function circuit-size bound | Their bound may give our compiler a lower-bound tool (gap B2) |
| Saddle-to-saddle explains simplicity bias, 2512.20607; Abbe et al., 2302.11055 | Timing (P152) and the mechanism gap A3 |
| Feature learning is decoupled from generalization, 2507.19680 | Bears directly on C18 and H45.4 |
| Simplicity bias and optimization threshold in two-layer ReLU nets, 2410.02348 | Nets that do not interpolate noise: our forced-fit protocol |
| Ziyin et al., 2502.05300; equivariance toolbox, 2512.21447 | Theorem 15 and the Curie bias |
| Geiger et al., 2301.04709; 2507.08802; 2610.18155 | R2 |
| Approximate homomorphisms and convergent representations in transducers, 2608.20428 | Stability of minimal representations (R1, R4) |
| Decompiling transformers to RASP, 2602.08857; 2602.16823; 2602.16473 | Compiler front |
| Do deep networks forget initialization?, 2605.29152 | The "init prior survives training" premise of C15′ |
| When is early stopping beneficial under label noise?, 2610.33846 | H45.4 |
| Crutchfield & Shalizi on causal states; Ganter & Wille on formal concept analysis; Harnad on symbol grounding (all M) | Foundations for R1 |
