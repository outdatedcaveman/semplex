# Lorenz & Tull (2026) Prior Art Review and Exact Originality Boundary

## 1. Primary Reference Analyzed in Full

- **Citation:** Robin Lorenz and Sean Tull, *Causal Abstractions, Categorically* (`arXiv:2602.16612v1`, `cs.LO`, February 18, 2026; `https://arxiv.org/abs/2602.16612`).
- **Scope:** A 71-page systematic categorical unification of causal abstraction notions inside deterministic/stochastic Markov categories (`FStoch`, `FinStoch`, `Det`, `FRel`, `QC`) using strict causal models over DAGs `(S, <=)`.

## 2. What Lorenz & Tull (2026) Already Establish

1. **Categorical Type Alignments and Downward/Upward Abstractions (Def. 14–16, Prop. 18):**
   - A downward abstraction between causal models consists of an order-preserving functor `pi` paired with **epic** deterministic transition/projection natural transformations `tau_X : pi(X) -> X` commuting with interventions and outcome mechanisms.
   - Upward abstractions are formulated via partial surjective inverse maps `omega` (`Def. 16`) and shown in `Prop. 18` to be recoverable directly from downward abstractions via right-inverses / sections on the epic projections.
2. **Unification of Exact, Strong, Constructive, and Iso-Constructive Abstractions (Sec. 5):**
   - Unifies exact transformations (`Def. 21`), strong causal abstraction (`Def. 23`), constructive abstraction (`Def. 24`), interchange/counterfactual intervention consistency, and iso-constructive equivalences (`Prop. 45`), complementing prior categorical/Markov-category causal formalisms including Geiger et al. (2025) and Mahadevan (2023/2025) tracked in `research/PRIOR_ART_REVIEW_RESOURCE_SEMANTICS_2026-11-21.md` and `research/HIGHER_CATEGORICAL_CAUSAL_SEMANTICS_2026-11-21.md`.
3. **Mechanism-Level Screening-Off & Markov/Cartesian Categories (Sec. 6, Def. 46, Thm. 51):**
   - Introduces mechanism-level abstractions parameterized by simple, extra-simple, and full abstraction maps `alpha(X)` defining screening-off equivalence partitions across `CD(S)`, `Markov(S)`, and `Cart(S)`, proving compatibility/characterization theorems (`Thm. 51`) when mechanisms commute with deterministic projections `tau`.
4. **Quantum-to-Classical Instantiation (Sec. 7):**
   - Applies the downward framework inside `QC` (quantum circuits / instruments) to characterize classical causal abstractions of quantum processes.
5. **Explicit Future-Work Boundaries Stated by the Authors (Sec. 8 Discussion, pp. 49–52):**
   - Works strictly with **exact commuting squares in finite discrete Markov categories (`FStoch`) over acyclic causal structures (`<=`)**;
   - Explicitly leaves open:
     - **Cyclic / feedback causal structures** beyond DAGs;
     - **Approximate causal abstractions** and distance/divergence stability bounds (`[BEH20, GWP+24, GIZ+23]`);
     - **Continuous domains** (`Hyb`, parameterized quantum circuits in `R^n`, Standard Borel / Polish measure spaces);
     - **Structured model/representation groupoids (`Model(C)`)** tracking latent equivalences and automorphisms as first-class objects rather than external commuting squares.

## 3. Exact Demarcation: Strictly Outside Lorenz & Tull (2026)

Every component formalized on this branch targets an exact structural regime left absent or explicitly deferred by Lorenz & Tull (2026) and prior non-contextual/epic abstraction frameworks (cf. Abramsky & Brandenburger 2011 sheaf contextuality reviewed in `research/INSTITUTIONAL_AND_CONTEXTUAL_SEMANTICS_PRIOR_ART_2026-11-22.md`):

### A. Homotopy-Fiber Isotropy Exact Sequence & Anchor-Induced `Cech H^1` Obstructions (`proofs/lean/ObstructionExactSequence.lean`, `proofs/cubical/src/Semplex/Cubical/FiberObstructionSequence.agda`)

- **Why not in Lorenz & Tull (2026):** Lorenz–Tull maps are epic abstractions `tau : M_low -> M_high` verifying *when* two causal models satisfy commuting interventional diagrams. They do not examine the **internal automorphism groupoid `G_rep`** of representations preserving an observed profile `G_prof`, nor the exact sequence relating full gauge isotropy `pi_1(BG_rep)`, profile-kernel isotropy `ker(Obs_P : G_rep -> G_prof)`, and **local-to-global anchor gluing obstructions in `Cech H^1`**.
- **What is new here:**
  1. **Constructive exactness & connecting coset homomorphism (Core Lean 4, `22/22`, `0 Classical.choice`, `0 sorryAx` + Cubical Agda `2.9.0`, `10/10`, `0` warnings):** Forms the pointed exact sequence connecting kernel isotropy `H = ker(Obs_P)` through total gauge `G`, quotient cosets `G / H` (`BHom`), and `H^1` transition cocycles (`globalRealization_iff_coboundary`, `gluesByGauge_iff_transition_coboundary`, `connecting_trivial_iff_lift`, `exactness_at_H1_H`), and lifts the pointed exact sequence natively into Cubical HoTT via square-cell `Deloop`, `Deloop->BG`, `Fib`, `kerLoop`, `connecting-coset-path`, and `im-trivializes-connecting` (plus concrete `C4 -> C2` witness `c4-mod2-coset1-trivializes`).
  2. **Anchor-induced Specker contextual obstruction (`speckerCoset0Local_not_gluesByGauge`, `c4_triangle_coset0_anchor_no_global_realization`):** Proves that a compatible global realization (`(1, 1, 1)` or `(3, 3, 3)` mod 4) exists *before* anchoring, yet imposing a partial anchor in the `0/2` coset kills all global sections while preserving full local consistency on every edge (`speckerCoset0Local_valid_edges`), realizing nontrivial cycle monodromy `2 != 0 mod 4`.
  3. **Monolith Partial-Anchor Impossibility (`hasMonolith_not_partialAnchorAdequate`, `q8_not_partialAnchorAdequate`, `c4_not_partialAnchorAdequate` vs `c2cubed_partialAnchorAdequate`):** Proves a structural dichotomy between factorizable elementary abelian gauges (`C2^3`, identifiable via 3 hyperplane anchors) and **monolithic** gauge groups whose proper nontrivial subgroups share a non-trivial intersection (`M = {0, 2} <= C4`, `M = {1, -1} <= Q8`), making partial state identification provably impossible unless an anchor breaks the monolith itself.

### B. Continuum `mu`-a.e. Gauge Quotienting, `ker W` Gauge-Tube Escape Bounds & Geometric Contraction Horizons (`proofs/lean-mathlib/QuantitativeGaugeStability.lean`)

- **Why not in Lorenz & Tull (2026):** Lorenz & Tull explicitly note continuous domains (`Hyb`) and approximate abstractions (`[BEH20, GWP+24, GIZ+23]`) as future work and require exact commutative equality in `FStoch`.
- **What is new here (`17/17` Mathlib v4.12.0 theorems, `0` warnings, `0 sorryAx`):**
  1. **Standard Borel / `mu`-a.e. Gauge Quotienting (`aeGaugeRel_equivalence`, `ae_null_perturbation_trivial`, `ae_anchor_kills_isotropy_iff`):** Weakens strict everywhere-injective representation equivalence on `ContinuumKernelCovariance` to **`mu`-almost-everywhere** equality, proving measure-zero latent perturbations leave every kernel law invariant and characterizing anchor identifiability up to `mu`-null sets.
  2. **Quantitative `eps`-Gauge Composition & Geometric Contraction Horizons (`epsGauge_refl/symm/comp/pow`, `contraction_horizon_bound`, `nonexpansive_horizon_bound`):** Replaces qualitative `epsilon = 0` commutation with a weighted/metric pseudogroup of `eps`-gauge morphisms and proves closed-form multi-step error propagation: under contractivity `rho < 1`, total discrepancy saturates geometrically at `rho^T * d_0 + eps * (1 - rho^T) / (1 - rho)`, strictly tightening the naive linear `d_0 + T * eps` bound (`nonexpansive_horizon_bound`).
  3. **`ker W` Gauge-Tube Decision Rigidity (`gauge_perturbation_invisible`, `no_flip_within_gauge_tube_pos/neg`, `gauge_escape_lower_bound`, `eps_orbit_rigidity`):** Relates hidden-state gauge perturbations decomposed into `ker W` (`null`) + orthogonal readout component to exact classifier margin stability: flips are impossible inside the `|m|` gauge tube (`no_flip_within_gauge_tube_*`), yielding the sharp necessary escape bound `|m| <= delta_orth` (`gauge_escape_lower_bound`).
  4. **Variable-Jacobian Continuum Pushforward (`variable_jacobian_density_pushforward`, `exp_jacobian_nonunit`, `exp_density_change_of_variables`):** Extends `ContinuumKernelCovariance`'s volume-preserving check to arbitrary strictly positive spatially varying Jacobians (`|det Dphi(x)| != 1`), illustrated explicitly by `exp(x)`.

## 4. What Remains Open (Intellectual Honesty)

1. **Infinitary `n`-Truncated / `(infty, 1)` Fibrations:** Cubical Agda currently models `1`-truncated `BG`/`Deloop` classifying spaces for group-homomorphism fibers `BHom` alongside `2`-coskeletal simplicial stabilization (`InductiveHigherHorn.agda`), rather than general non-coskeletal `(infty, n)` cohesive toposes.
2. **Support-Relative Variable-Signature Grothendieck Fibration:** In Pure Lean 4, connecting `ObstructionExactSequence` across distinct variable causal signatures `(G_rep -> G_prof)` requires gluing fixed-signature Markov profile groupoids (`StochasticResponseProfileGroupoid`, `AnchoredResponseKernel`) via a strict Grothendieck fibration restricted to reachable supports `Reach(mu_0) = U_w supp(mu_w)`.
3. **Full Metric Markov-Dobrushin Tightness & Frontier Scale:** `QuantitativeGaugeStability` derives closed-form contraction bounds abstractly over pseudometric/Lipschitz step laws (`d_t`); unifying these directly with Mathlib's `MeasureTheory.Measure.tv` / `Wasserstein` Dobrushin coefficients and validating `Gamma_mod` on calibration-split frontier checkpoints remains future empirical and formal work.
