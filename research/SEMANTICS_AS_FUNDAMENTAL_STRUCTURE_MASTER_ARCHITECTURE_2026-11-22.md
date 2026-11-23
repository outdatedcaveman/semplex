# Semantics as a Fundamental Structure: Master Research Architecture

**Date:** 2026-11-22  
**Status:** research architecture and theorem programme; not a completed theory, canon amendment, or novelty claim.

## 0. Governing objective

Semplex seeks a mathematically explicit account of semantics as a fundamental structure. It must explain, rather than assume:

1. how a structure can be about another structure;
2. how signs, states, symbols, proofs, programs, and models acquire content;
3. what makes an interpretation correct rather than merely internally coherent;
4. how truth is grounded, including relations among truth, evidence, realization, and the world;
5. how meaning survives changes of notation, encoding, implementation, and mathematical presentation;
6. how semantic structure appears in physical, biological, cognitive, social, mathematical, and computational systems;
7. how these domains can be related without reducing all of them to human language, passive correlation, or one favored architecture.

The ambition is not to rename existing theories with a common vocabulary. It is to identify a common mathematical core, establish its limits, and prove bridges among domains.

**Guiding criterion:** every claimed unity must be expressed as a structure-preserving construction or theorem; every claim of grounding must identify the non-formal input connecting the construction to its target.

## 1. Syntax, semantics, and grounding

A formal syntax supplies expressions and rules of manipulation. A formal semantics supplies an interpretation, model, realization, or satisfaction relation. Merely defining a map from syntax to a semantic domain does not eliminate the divide: it relocates the divide to the choice and justification of the domain and map.

Distinguish three questions:

- **Internal interpretation:** given a formal system and a model, what does an expression denote, and when is it satisfied?
- **External grounding:** why is this model or interpretation relevant to the system represented?
- **Semantic adequacy:** which distinctions and transformations must an interpretation preserve to count as meaning-preserving?

The target is not to collapse these questions. It is to derive their relations and identify irreducible grounding conditions.

### 1.1 Candidate common interface

For a system X, admissible context/probe category P, and response object V, define response semantics as a functor or profunctor:

\[
\mathsf R_X:\mathcal P^{op}\to\mathcal V,
\qquad
\mathbf H_X:\mathcal H^{op}\times\mathcal P\to\mathcal V.
\]

Objects of P may be experimental interventions, proof contexts, computational contexts, or communicative protocols. Morphisms encode valid refinement, composition, substitution, or context change. Responses may be truth values, observations, distributions, state transformations, proof objects, or higher spaces.

A representation is semantically adequate relative to P when it preserves the protected response structure. Exact semantic identity is equivalence of complete response profiles; approximate semantics requires a declared metric or enriched distortion.

This is a candidate interface, not yet a universal definition of all meaning. It must be tested against referential, inferential, normative, mathematical, causal, and socially instituted meaning.

### 1.2 Three levels

1. **World structure:** target system and its actual lawful/counterfactual organization.
2. **Representational structure:** physical or abstract sign system purporting to encode aspects of the target.
3. **Interpretive structure:** relations by which the representation is evaluated, decoded, used, corrected, or understood.

The semantic relation connects these levels. It is not automatically identical to any one of them.

A formal model proves conditional theorems. Without an interpretation/realization argument, it does not establish that its symbols refer to the intended world. A causal relation alone is also insufficient: arbitrary correlations, trivial encodings, and pancomputational mappings must be excluded by organizational and counterfactual criteria.

## 2. Five coupled research layers

### A. Mathematical foundations and higher identity

Question: what is the mathematical nature of identity, equivalence, transformation, and structure when higher coherence is retained?

Tools: dependent type theory; identity types; HoTT; univalence and universes; higher inductive types (HITs); (∞,1)-categories and ∞-groupoids; fibrations; modalities; ∞-toposes and their internal logic.

HoTT provides a disciplined language in which equality is structured by paths, paths between paths, and higher coherence. Univalence identifies equivalence of types with identity in a universe under the univalence axiom. HITs construct spaces/types by generators and higher relations: quotients, suspensions, pushouts, classifying spaces, and more.

**Limit:** HoTT does not by itself ground reference or empirical truth. It provides a foundational language and internal semantics. Grounding remains a question about models, realizations, probes, and relations to targets.

### B. Semantic structure and invariance

Question: what is preserved when a representation changes while its meaning remains the same?

Tools: response functors/profunctors; contextual equivalence and full abstraction; natural transformations and equivalences; Yoneda and density with justified probe categories; observational quotients; invariants under admissible transformations; fibrations of contexts; compositionality and substitution.

The theory must say which transformations are admissible and what they preserve. It must also account for semantic surplus: implementations may retain distinctions irrelevant to target content but useful for memory, robustness, or computational efficiency.

### C. Grounding, reference, and truth

Question: what makes an interpretation true of its target, and what is truth beyond derivability inside a formal calculus?

Keep distinct:
- syntactic derivability;
- model-theoretic satisfaction;
- truth in a specified structure;
- evidence or proof;
- successful realization;
- causal/interventional correctness;
- reference and aboutness;
- normative correctness.

Candidate grounding conditions:
- **Adequacy:** decoded response profile matches protected target responses.
- **Commutation:** representational updates track target updates.
- **Counterfactual robustness:** adequacy survives held-out admissible interventions/contexts.
- **Causal efficacy:** representational changes affect downstream inference/action as predicted.
- **Organizational grounding:** implementation is constrained by its own mechanism, not arbitrary external encoding.
- **Provenance and correction:** principled mismatch detection and repair.

These are candidate criteria, not a completed solution. Normative and social truth may require structures not reducible to physical prediction.

### D. Computational and logical semantics

Question: when does a computational state, program, proof, or latent representation encode something, and when is a computation correct?

Domains: operational and denotational semantics; realizability and proof interpretations; Curry–Howard; compiler correctness; program/contextual equivalence; abstract interpretation; algorithmic information and complexity; causal models; neural representations and circuit/algorithm distillation; resource-bounded and approximate realization.

The theory must cover symbolic and subsymbolic systems. It must not assume a neural network is the universal semantic substrate, or that proof objects and physical processes are identical merely because a formal correspondence exists.

### E. Natural and social semiosis

Question: how do physical, biological, cognitive, linguistic, and institutional systems participate in sign processes?

Peirce's object/sign/interpretant triad is a research guide, but must be mathematically typed:
- object: target structure or constraint source;
- sign: physically realized or formally specified representation;
- interpretant: resulting transformation in dispositions, expectations, inference, or action.

Distinguish objective causal structure from representation-for-an-agent, and individual interpretation from socially stabilized meaning. Norms, testimony, institutions, and collective correction may require game-theoretic, deontic, and institutional semantics beyond causal response semantics.

## 3. HoTT as a semantic foundation: concrete obligations

### 3.1 Core interpretation

For a chosen type theory T and an ∞-topos (or suitable higher-categorical model) E, define semantics assigning:
- each context Γ to an object/context in E;
- each type A over Γ to an object in the slice E/Γ;
- each term to a section;
- each substitution to pullback/reindexing;
- each identity type to a path object/diagonal factorization;
- each universe to a suitable univalent fibration;
- each HIT to its corresponding homotopy-colimit or higher-inductive universal construction.

The interpretation must be stable under substitution and preserve specified computation rules, strictly or propositionally as appropriate. State exactly which rules and coherence levels are validated.

### 3.2 HITs as semantic constructors

Priority cases:
- set quotients: observational equivalence and semantic identification;
- coequalizers/pushouts: gluing interpretations and compositional interfaces;
- suspensions/spheres: generators of higher homotopy;
- truncations: controlled loss of higher information;
- classifying spaces BG: action groupoids and symmetry;
- homotopy quotients: quotienting by transformations while retaining stabilizers and higher isotropy.

The action groupoid quotient X//G is central: its 0-truncation remembers orbits; its full homotopy type retains stabilizers as loop spaces and higher coherence. Quotienting by symmetry must not automatically erase symmetry data.

### 3.3 Truth in an ∞-topos

An ∞-topos has an internal language and subobject classifier Ω, classifying propositions/subobjects in the relevant internal sense. This provides internal truth relative to an object of the topos.

But distinguish:
1. internal truth in E;
2. truth in an external mathematical model of E;
3. truth of claims about an intended physical/computational target.

An internal subobject classifier is not, by itself, a metaphysical grounding of truth.

### 3.4 Modalities and semantic information

Investigate modalities (including truncation, sheafification/localization, and reflective subuniverses) as operators specifying which distinctions are retained or discarded:
- truncation forgets higher identity information above a level;
- localization identifies structures under a declared class of equivalences;
- sheafification enforces local-to-global coherence relative to a coverage;
- modalities encode principled changes of semantic resolution/context.

Derive when information loss is legitimate, what it costs, and which downstream truths remain invariant.

### 3.5 HoTT and grounding

A formal interpretation of HoTT in an ∞-topos establishes validity relative to that model and its assumptions. It does not establish that the model is the unique ontology of reality. The stronger programme relates formal types/paths, physically realizable state spaces/transformations, computational representations, and evidence/proofs through explicit realization structures.

## 4. Truth: a layered programme

Avoid both formalism-only (truth equals provability) and an unexplained correspondence slogan.

1. **Formal truth:** for language L and structure M, satisfaction M ⊨ φ is recursively defined. Tarski-style truth definitions and undefinability constrain what a sufficiently expressive language can define internally.
2. **Constructive/evidential truth:** propositions-as-types interprets propositions as types and evidence as terms under a chosen type-theoretic discipline. Constructive proof is evidence under specified rules; it does not identify all truth with proof in every semantics.
3. **Empirical/counterfactual truth:** claims about a physical/computational system require a grounded target model and probes/interventions that distinguish the claim from alternatives. Insufficient probes identify truth only up to observational equivalence.
4. **Referential truth:** reference requires an account of how a sign/internal state is anchored to a target. Candidate constraints include causal history, intervention-sensitive covariance, structural correspondence, and social calibration.
5. **Normative/social truth:** mathematical validity, empirical accuracy, and social/normative correctness must not be conflated. Institutions and practices help constitute some facts, but can themselves be evaluated for coherence, evidence, and fit to the world.

Long-range target: represent distinct truth regimes as structured fibrations over a common semantic base, with explicit comparison maps and compatibility conditions. State what is shared, what differs, which translations preserve truth, and how contradiction, uncertainty, and underdetermination are represented. This is conjectural.

## 5. Graph-gauge classification as a controlled semantic case study

For a connected graph:
- raw edge labels are presentations;
- vertex gauge transformations are admissible changes of local frame;
- loop holonomies are invariant response data;
- a spanning tree chooses a normal form;
- chord holonomies provide independent generators;
- the action groupoid retains symmetries and stabilizers;
- orbit sets alone lose isotropy information.

The target
\[
\operatorname{Conn}(\Gamma,G)//G^V
\simeq
\operatorname{Hom}(\pi_1(\Gamma,r),G)//G
\]
is a theorem about when two presentations represent the same global holonomy semantics.

This is a laboratory for defining syntax/presentation, admissible transformations, semantic invariants, full abstraction, higher symmetry, and generalization from groups to groupoids and higher gauge structures. It does **not** by itself solve reference to the physical world.

## 6. Existing work to integrate, not duplicate

Existing canonical research:
- SEMANTIC_GROUNDING_PRINCIPLE_2026-11-21.md: contextual-behavior/distinction-admissibility, response quotients, grounding criteria, causal Yoneda, resource bounds, architecture optimization, prior-art caveats.
- HIGHER_CATEGORICAL_CAUSAL_SEMANTICS_2026-11-21.md: response presheaves/profunctors, higher causal semantics, resource enrichment.
- MASTER_PRINCIPLE_SYNTHESIS_2026-11-21.md: variational/spectral and resource-sensitive realization.
- ULTIMATE_COMPILER_ARCHITECTURE.md: architecture and representation selection.
- Lean ResponseQuotient, ObservableCongruence, ResourceRelativeProbes, BeliefStateHankel, GraphGaugeHolonomy, GraphGaugeClassification, HigherGaugeCohomology.

Use this architecture as a map and dependency graph. Reconcile existing claims and identify missing theorems; do not duplicate the long notes.

## 7. Core conjectures and theorem targets

**S1 — Contextual semantic quotient.** For declared probe category P, equality of complete response profiles defines the coarsest equivalence preserving all P-responses. For every exact P-adequate encoder r:S→Z, the canonical quotient map q:S→S/≈ factors through the image of r: there is a unique map from im(r) to S/≈ whose composite with r is q. The converse direction is generally false: an encoder may retain semantically irrelevant implementation distinctions. The decoded response profile, not necessarily the encoder itself, factors through the semantic quotient.

**S2 — Semantic full abstraction.** A translation is fully abstract relative to P iff it preserves and reflects contextual equivalence, retaining higher mapping-space data at the required truncation level.

**S3 — Grounded realization.** A representation is grounded relative to a target when a physically/computationally realized interpretation map satisfies response adequacy, dynamic commutation, counterfactual robustness, and organizational constraints. The theorem is conditional on independently justified physical premises.

**S4 — Higher semantic quotient.** For a groupoid/higher-groupoid of presentations and admissible transformations, semantic quotient is a homotopy quotient or suitable localization, not merely a set quotient. Loop spaces encode stabilizers; higher loop spaces encode higher automorphisms/coherence.

**S5 — HoTT semantic interpretation.** A chosen HoTT fragment has a sound interpretation in a specified ∞-topos/model, including contexts, types, terms, identity types, universes, and selected HITs. Universe/resizing assumptions are explicit.

**S6 — Truth compatibility.** Explicit comparison maps relate internal logical truth, model satisfaction, constructive evidence, and grounded empirical truth, with domains and failure conditions stated.

**S7 — Resource-bounded realization.** Minimal implementation cost is characterized by outer architecture search and inner representation optimization. Lower bounds arise from response-profile packing, information, computational complexity, and physical resource constraints.

**S8 — Semiosis.** Object/sign/interpretant is a structured, iterated realization of target constraints, sign transformations, and interpretant updates. The triad is typed and its stability/correction conditions proved.

S3, S5 as a full model programme, S6, and S8 are not established by current work.

## 8. Work packages and order

**WP0 — Canonical ontology.** Define common interfaces for target systems, presentations, contexts/probes, responses, admissible transformations, semantic equivalence, realization/grounding, truth/evidence, and resource grades. Deliverable: typed glossary and dependency graph. Avoid a monolithic definition that assumes the answer.

**WP1 — Finish graph-gauge classification.** Formalize rooted spanning-tree certificates and unique root paths; construct chord-generator free groups and representation types; prove connection/gauge action-groupoid equivalence; retain stabilizer/higher coherence data.

**WP2 — HoTT/HIT semantic core.** Select precise type-theory fragment and model target. Formalize set quotients, homotopy quotients/classifying spaces, pushouts, truncations, and one representative HIT. Prove universal properties and distinguish semantic equivalence from 0-truncated equality. State univalence/universe assumptions.

**WP3 — Truth and grounding.** Separate internal satisfaction, proof evidence, and empirical target truth. Define interpretation/realization maps and adequacy diagrams. Formalize a finite causal example with passive-correlation counterexample and intervention-sensitive grounding. Prove underdetermination for non-separating probes.

**WP4 — Higher response semantics.** Lift response functors from Set/Prop to groupoids/spaces. Define equivalence via natural equivalence of response presheaves. Prove higher full abstraction for a tractable finite groupoid case; connect to graph-gauge homotopy quotient.

**WP5 — Computational/logical semantics.** Formalize compiler correctness as response-preserving translation. Compare operational, denotational, and contextual semantics. Add resource-enriched correctness and distortion. Examine proof/program semantics and proofs as evidence versus truthmakers.

**WP6 — Peircean/social extension.** Type object/sign/interpretant and transformations. Distinguish agent-relative from objective response structure. Add social stabilization, testimony, correction, and normative constraints without reducing them to prediction.

## 9. Methodological constraints

1. No semantic inflation: specify target, probes, responses, and adequacy.
2. No truth inflation: theoremhood relative to axioms is not automatically truth about the world.
3. No HoTT overclaim: univalence and HITs are powerful foundations, not a completed grounding theory.
4. No reduction by fiat: domains may share structure while differing in realization and norms.
5. No unearned universality: state counterexamples and assumptions.
6. No architecture lock-in: neural, symbolic, categorical, dynamical, and hybrid realizations remain candidates.
7. No hidden resource scalar: preserve vector costs and Pareto trade-offs absent justified scalarization.
8. No erased symmetry: use homotopy quotients when stabilizers/higher automorphisms matter.
9. No unsupported novelty claim: map prior art.
10. No proof theater: formalize only claims actually represented in the model and document abstraction gaps.

## 10. Success criterion

The programme succeeds only if it yields a coherent stack in which formal semantics is precise; semantic equivalence and meaning-preserving transformations are characterized; higher identity and quotient structure are retained where necessary; truth and evidence are related without conflation; grounding connects interpretations to organized targets; computational representations are evaluated by fidelity and resource cost; natural/social semiosis is accommodated without flattening it into prediction; and every bridge is supported by theorems, assumptions, counterexamples, or empirical tests.

The ultimate object is not a single equation. It is a foundational theory whose interfaces make it possible to prove when two things mean the same, when a representation is about its target, when an inference is valid, when a claim is true, and what resources are required to realize that semantic competence.


## 11. Typed semantic-response core (2026-11-22)

Added and registered proofs/lean/SemanticResponseCore.lean. It makes the probe/response interface explicit rather than treating the response map as an untyped black box.

Machine-checked results:
- ProbeSemantics defines a target state type, probe/context type, and response type.
- semEq defines equality of complete response profiles across all declared probes; reflexivity, symmetry, transitivity, and the induced setoid are proved.
- responseProfile and semEq_iff_responseProfile_eq identify semantic equivalence with equality of the function-valued response profile. This module does not import or directly invoke ResponseQuotient.
- ExactRealization specifies an encoder and probe decoder with exact response adequacy.
- encoding_collision_implies_semEq proves that an implementation collision can occur only between semantically equivalent target states.
- exact_realization_injective proves that if probes separate target states, every exact realization must encode them injectively.
- Dynamics and DynamicRealization specify target and implementation updates; commutes_list proves that one-step update commutation extends to every finite action sequence.
- SatisfactionModel and EvidenceSystem keep model satisfaction and proof/evidence objects distinct; SoundEvidence is an explicit bridge, and evidence_soundness is proved. Completeness is separately defined and is not assumed.

**Verification:** fresh full lake build passed after initial module registration; focused module build passed after linking responseProfile to ResponseQuotient. Axiom audit: semEq reflexivity, collision-to-semantic-equivalence, exact-realization injectivity, finite-sequence dynamic commutation, and evidence soundness all report no axioms.

**Interpretive boundary:** these are exact model-relative interface theorems. They do not prove that the chosen probes exhaust physical reality, that an arbitrary encoder is physically grounded, or that formal evidence is identical to truth. Those are deliberately separate obligations in the master architecture.


### Typed response-core integration correction

The typed response-profile equivalence is stated as equality of the function-valued profile, not as a direct theorem about the legacy ResponseQuotient relation. This avoids an elaboration mismatch between the two modules while preserving the intended mathematical equivalence. The axiom audit reports the profile-equality theorem depends on Lean's standard Quot.sound; the collision, injectivity, finite-update-commutation, and evidence-soundness theorems report no axioms. There are no custom axioms or sorryAx.


### Naming and dependency clarification
The current theorem is named semEq_iff_responseProfile_eq: pointwise equality of all probe responses is equivalent to equality of the function-valued response profile. This is the same defining relation used by the existing ResponseQuotient module, but the theorem does not directly invoke its responseRel constant. The audit dependency on Quot.sound is a standard Lean quotient axiom surfaced through the imported response-quotient environment; the core collision, injectivity, dynamic-commutation, and evidence-soundness results themselves have no axiom dependencies.


## 12. Semantic grounding bridge: formalization update (2026-11-22)

Added `proofs/lean/SemanticGroundingBridge.lean` and the companion research note `research/SEMANTIC_GROUNDING_BRIDGE_AND_GRAPH_PATH_DECOMPOSITION_2026-11-22.md`.

The new module sharpens WP3:
- probe restrictions make explicit that a narrower observation regime cannot recover distinctions absent from its probes;
- non-separation yields an explicit pair of distinct but observationally equivalent target states;
- translation truth adequacy is preservation **and** reflection of satisfaction, not merely one-way soundness;
- state-indexed evidence separates evidence for a claim at a particular target state from evidence that would have to establish the claim in every state;
- exact response adequacy plus update commutation proves finite-sequence intervention adequacy.

A two-state Boolean witness shows passive constant observations are non-separating while an intervention-sensitive probe separates the states. This is a formal counterexample illustrating the logic of interventions, not an empirical causal result.

**Boundary:** the new GroundedRealization is grounded only relative to its declared target dynamics and probe family. It does not establish that the chosen target model is the intended external world, that interventions are physically valid, or that all relevant counterfactuals have been covered. Those remain empirical and organizational grounding obligations.

The state-indexed evidence interface is preferred for state-dependent empirical claims. The earlier EvidenceSystem in SemanticResponseCore is a coarser interface and should not be mistaken for a complete account of evidence.


## 13. Higher semantic response layer (2026-11-22)

Added and registered:
- `proofs/lean/HigherSemanticCore.lean`
- `proofs/lean/SemanticFibrations.lean`

The first lifts probe responses from sets to groupoids. Responses can be related by isomorphisms; automorphism types are retained. It proves that higher response equivalence (isomorphism at every probe) is an equivalence relation, and that groupoid equivalences preserve and reflect isomorphism witnesses and preserve automorphism hom-types.

A one-object counterexample proves that object-only shadows are insufficient: a groupoid with Z2 automorphisms and a groupoid with trivial automorphisms have identical object types but are not equivalent. Thus orbit/object-level collapse can erase semantic symmetry.

A strict groupoid-valued presheaf prototype over a context preorder adds restriction maps and identity/composition coherence. A contextual equivalence is objectwise fully faithful/essentially surjective and natural on objects and arrows. This is a first-stage strict 1-groupoid model, not yet a general category-indexed pseudofunctor or an infinity-presheaf.

`SemanticFibrations` gives separate types for World, Sign, Claim, Context, relational reference, context-sensitive expression, model satisfaction, and state-indexed evidence. Evidence soundness is conditional on reference. Finite countermodels show:
- a claim can be satisfied without current evidence;
- a claim can be satisfied without the sign referring to the evaluated world.

This blocks the conflations truth=evidence and satisfaction=aboutness. It does not claim that reference must always be a unique physical denotation; unique reference is an optional property.

**Formal boundary:** groupoids retain 1-dimensional invertible symmetry. They do not yet provide arbitrary higher morphisms. The next layer must model 2-cells/coherence and then a cubical HIT semantics. Ordinary Lean inductives are not being described as a full cubical HIT implementation.

## 14. Adversarial corrections and HoTT environment

An independent Antigravity audit event (151825) exposed a quantifier bug in the older `CompleteEvidence` predicate. It has been corrected: the unindexed EvidenceSystem now expresses completeness only for claims true at every state. State-relative empirical evidence belongs in `StateIndexedEvidence` in SemanticGroundingBridge. The distinction and rationale are recorded in `research/HIGHER_SEMANTIC_CORE_GROUPoid_AND_GROUNDING_2026-11-22.md`.

The same audit corrected S1's universal-property direction. For an exact adequate encoder, the semantic quotient map factors through the encoder's image, not generally the reverse. This correction is reflected in §7 above and in the ResponseQuotient theorem.

The graph audit also establishes a serious limitation: current forward-only EdgeWalk certificates describe out-arborescences. Simply adding backward steps would make uniqueness over all tree-supported walks false due to backtracking. The general solution should use parent/depth recursion with inverse edge labels when a parent edge is oppositely oriented. The current path-decomposition theorem remains conditional on its forward-only model. Explicit tree/chord disjointness is also required.

For genuine cubical paths, computational univalence, and HITs, Cubical Agda is now installed locally alongside Lean. The current Agda 2.9.0 project compiles genuine HITs using built-in cubical primitives; the official Cubical library v0.9 still has a Glue/Equiv/Sigma mode incompatibility. GHC/Cabal are not installed and no global PATH changes were made.


### Truth/reference refinement

The typed semiosis layer distinguishes `ContentTrue` (model satisfaction of expressed content) from `GroundedAssertionTrue` (content satisfaction together with a sign-to-world reference relation). This is not a universal reduction of truth to reference: the semantic target domain may be mathematical, physical, social, or computational. The additional reference condition is an aboutness/grounding condition for a particular sign and target.


## 15. Action-groupoid semantics and the gauge case

The generic `actionGroupoid` construction in `HigherSemanticCore.lean` forms the homotopy quotient X//G of a group action. It proves:
- orbit relation iff there is an action-groupoid arrow;
- equality in the ordinary orbit quotient iff there is such an arrow (the orbit set is the 0-truncation/connected-components quotient);
- the loop type at x is exactly the stabilizer of x.

`GraphGaugeActionGroupoid.lean` instantiates this with vertex gauge transformations acting on edge connections. Its `gauge_loop_space_is_stabilizer` theorem identifies connection automorphisms with gauge transformations fixing the connection. This is a direct bridge from admissible presentation changes to semantic automorphisms. The construction is 1-groupoidal; higher cells are still outstanding.

Terminology boundary: SemanticFibrations currently consists of indexed families/relations inspired by fibrations, not yet Grothendieck fibrations or an infinity-topos modality. GroupoidPresheaf is a strict preorder-indexed prototype over a common response universe, not a general dependent pseudofunctor.


### Finite isotropy witness

`FiniteActionGroupoidExample.lean` gives a C2 action on Option Bool. The fixed point has two distinct automorphisms; the non-fixed two-point orbit has trivial stabilizer. The points in that orbit are connected by an action-groupoid arrow, while the fixed point is in a different orbit. This is a small machine-checked witness that the homotopy quotient carries object-dependent isotropy absent from the orbit set.


## 16. Cubical Agda and first genuine HITs

A local Cubical Agda project is now present under `proofs/cubical/`, using the official Agda 2.9.0 Windows x64 binary verified by SHA-256 and kept local to the repository (no global PATH changes, no GHC/Cabal installation).

The modules `Semplex.Cubical.Primitives`, `Semplex.Cubical.S1`, and `Semplex.Cubical.BGroup2Skeleton` typecheck:
- minimal path primitives and path composition;
- the circle S1 as an actual HIT with a loop path constructor;
- a group classifying-space 2-skeleton with unit, multiplication, and inverse 2-cells.

This is genuine cubical/HIT work, not an ordinary Lean inductive pretending to be a HIT.

**Boundary:** BGroup2Skeleton is not yet a full BG: associativity and unit/inverse coherence cells at higher dimensions and 1-truncation remain. The official Cubical Agda library v0.9 currently fails under Agda 2.9.0 due to a Glue/Equiv/Sigma cubical-mode conflict. The active project therefore uses built-in cubical primitives directly; Glue/univalence remains a toolchain/library compatibility blocker.


### Circle induction and computation

`Semplex.Cubical.S1Recursor` now defines both the nondependent circle recursor and its dependent eliminator, including explicit base and loop computation equalities. The full Cubical Agda build passes. This is a genuine HIT eliminator, not merely a declaration of a path constructor.

A naive recursor for the group 2-skeleton was rejected due to `primTransp` boundary mismatches. The failed draft was removed. This confirms that higher HIT elimination needs carefully typed dependent boundary/coherence data; it is not enough to list target 2-cells.
