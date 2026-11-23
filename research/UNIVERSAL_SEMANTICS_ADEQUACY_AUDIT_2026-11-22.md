# Universal Semantics: Adequacy Audit and Proof Obligations
Date: 2026-11-22

## Executive verdict

The Grounded Higher Semantic Representation programme has a valid mathematical core, but it is not yet an airtight theory of universal semantics. The current results establish representation and reconstruction theorems *conditional on a chosen semantic category and a sufficiently rich probe family*. They do not prove that the category captures every legitimate semantic phenomenon, that the probes are empirically/physically adequate, or that internal satisfaction is truth about an external world.

This distinction is not cosmetic. Yoneda-style reconstruction is representation-independent only after the category and its morphisms have been fixed. The choice of objects, admissible transformations, reference, satisfaction, and evidence is where substantive semantic commitments enter.

## New formal result in this pass

Added `proofs/lean/GroundedSemanticCategory.lean`.

It defines a category whose objects are grounded models containing:
- a domain of worlds;
- a domain of claims;
- a reference map from claims to worlds;
- a satisfaction relation;
- an evidence type for each claim;
- an evidence-soundness function.

Its morphisms preserve reference, preserve and reflect satisfaction, and transport evidence. Composition and identities are defined, and the category is instantiated as the general category used by the restricted Yoneda development.

The module proves:
1. grounded truth is invariant under every semantic morphism;
2. evidence transported along a semantic morphism remains sound;
3. all-probe profiles are fully faithful for this category;
4. any restricted probe family whose incidence cocone is dense reconstructs semantic morphisms;
5. models with the same bare carrier/reference data but different satisfaction relations cannot be related by a truth-preserving semantic map;
6. soundness does not entail completeness: a true claim may have no evidence object.

The first two reconstruction statements are consequences of the categorical definitions and Yoneda machinery. They are not independent evidence that this is the uniquely correct category of semantics. The countermodels are important: they expose exactly which semantic data cannot be inferred from bare syntax or carriers.

## What the framework currently proves

### A. Formal representation layer
For a fixed category C, the all-probes representable profile is fully faithful. For a selected probe family P, the restricted representation is fully faithful when the canonical incidence cocone is dense in C. This retains transformations, not merely object labels.

### B. Moduli layer
In the strict groupoid development, equivalence of the profile representation yields contractible homotopy fibres in the represented image. The resource-poset development gives lower/upper monotone completion envelopes, identifiability iff envelope collapse, and monotonic improvement under increasing observation budgets.

### C. Grounded-structure layer
Grounded models explicitly carry reference, satisfaction and evidence. Semantic morphisms preserve these fields. This prevents an unstructured isomorphism from silently being treated as semantic equivalence.

## What is not established

1. **Ontology adequacy:** why should every semantic bearer be an object of this category, and why should every semantically legitimate transformation be one of its morphisms?
2. **External reference:** a field called `World` and a map called `reference` do not prove that the map denotes an external physical target. We need a causal/operational realization relation and independent tests for it.
3. **Probe adequacy:** density is a mathematically exact criterion, but for a restricted probe family it is a demanding substantive hypothesis. It must be proved from a principled probe-generation procedure or independently validated; it cannot simply be assumed because reconstruction is desired.
4. **Truth adequacy:** preservation of an internally specified satisfaction predicate proves invariance, not that the predicate is correct. The theory needs bridge principles linking satisfaction to successful reference, counterfactual intervention, prediction, action, and correction.
5. **Evidence completeness and defeasibility:** soundness is formalized, but completeness, graded evidence, defeaters, conflicting evidence, and revision under new observations are not.
6. **Context and descent:** local semantics over contexts may require sheaf/stack conditions. The current strict presheaf layer does not prove descent or coherence for all context changes.
7. **Genuine higher structure:** the strict groupoid results preserve ordinary arrows and automorphism groups. They are not yet a full space-valued (∞,1)-categorical proof with all higher mapping-space coherence.
8. **Universality:** no theorem yet shows that distinct major semantic theories (model-theoretic, inferentialist, pragmatic, informational, causal, computational, embodied) embed into a common category in a way that preserves their own explanatory invariants.

## The decisive theorem we should aim for

The ultimate result should not merely say that Yoneda reconstructs objects from all probes. It should be a **Grounded Semantic Adequacy and Reconstruction Theorem** with independent premises and explicit failure conditions.

A candidate formulation:

Let Σ be a class of semantic systems specified independently by operational/causal criteria; let C_Σ be their category with admissible semantic transformations; let P_B be the probe category available at resource budget B; let R_B be the space-valued restricted semantic profile functor.

Prove, under explicit hypotheses:
- (Representation) R_B is fully faithful exactly when P_B is dense in the appropriate higher-categorical sense.
- (Moduli) for profiles in the essential image, the homotopy fibre of R_B is contractible; otherwise it measures residual ambiguity.
- (Grounding) a causal realization map selects a point in that fibre and commutes with admissible interventions/updates.
- (Truth transport) satisfaction, reference, and evidence are invariant under the induced equivalences, with evidence soundness and completeness separately characterized.
- (Resource monotonicity) increasing B induces a comparison map that can only reduce the admissible completion/moduli space, with a quantitative bound when a metric/probability structure is supplied.
- (Cross-theory adequacy) each target semantic theory T_i admits a structure-preserving interpretation into C_Σ, and the interpretation preserves its independently validated semantic observables; ideally the family is jointly conservative.

Crucially, the definition of Σ and its adequacy tests must not be derived from the theorem itself. Otherwise the theorem is circular.

## Adversarial tests / possible falsifiers

- **Syntax collision:** construct two systems with identical syntax and all currently available program-level probes but different external referents or truth conditions. If no admissible causal probe separates them, the framework must report non-identifiability rather than declare them semantically identical.
- **False density:** exhibit a probe family whose observed profiles appear rich but whose incidence cocone is not dense. The theory must detect the missing distinctions.
- **Automorphism collapse:** compare orbit/quotient semantics with action-groupoid semantics. If isotropy or higher automorphisms affect meaning, a quotient-only reconstruction is inadequate.
- **Context failure:** construct compatible local interpretations that fail to glue; determine whether stackification repairs them or whether the semantics is genuinely contextual.
- **Evidence gap:** distinguish truth without evidence, evidence without truth (which soundness should rule out), incomplete evidence, and defeasible evidence.
- **Computational irreducibility:** determine which semantic distinctions are in principle unresolvable under a finite resource budget, not merely currently unobserved.
- **Theory comparison:** test model-theoretic truth, proof-theoretic provability, inferential role, pragmatic success, and causal reference on common examples and counterexamples. Do not assume they coincide.

## Prior-art boundary

The Yoneda/density and higher-categorical causal ingredients are not novel in isolation:
- Sridhar Mahadevan, “Universal Causality,” *Entropy* 25(4), 574 (2023), DOI: 10.3390/e25040574. This already combines higher categorical causal interventions, presheaf representations, Yoneda, category-of-elements constructions, fibrations/lifting, and homotopy constructions.
- Emily Riehl and Dominic Verity, “The comprehension construction,” *Higher Structures* 2(1) (2018), pp. 116–190, DOI: 10.21136/HS.2018.05. This develops higher-categorical comprehension and Yoneda embeddings, including full-faithfulness and coherent nerve machinery.
- Resource monotone lower/upper extensions via Kan extensions are developed by Cockett, Geng, Scandolo & Srinivasan, “Extending Resource Monotones using Kan Extensions,” EPTCS 380 (2023), DOI: 10.4204/EPTCS.380.12.

Any novelty claim must therefore concern the integrated adequacy architecture: resource-indexed moduli of grounded semantic completions, a non-circular causal realization criterion, truth/evidence structure over those moduli, and conservative bridges among distinct semantic theories. This remains a research hypothesis until compared systematically against the literature.

## Next technical sequence

1. Formalize the space-valued (∞,1)-categorical restricted Yoneda nerve and its homotopy fibres.
2. Replace the informal grounding field with a causal realization structure: interventions, observations, counterfactual predictions, and a realization functor/section.
3. State and prove a non-circular density criterion for operationally generated probes; derive finite-budget non-identifiability bounds.
4. Add a context site and prove the precise descent/stack conditions required for local semantic profiles to glue.
5. Build conservative interpretations of at least four semantic theories (model-theoretic, inferentialist/proof-theoretic, pragmatic, causal/informational) and test where they agree and diverge.
6. Apply the theory to the existing graph-gauge case, preserving isotropy and higher coherence.

## Verification and agent status

The new `GroundedSemanticCategory.lean` module has been added to the Lake project. Its focused build and the full project `lake build` both passed. `git diff --check` passed. A focused axiom audit found no axioms for truth preservation, evidence soundness transfer, the semantic countermodel, or the soundness/completeness separation; the two reconstruction definitions depend only on standard `Quot.sound` through the existing extensionality infrastructure. No custom axioms or `sorryAx` were introduced.

Gemini review remains pending in the local orchestrator; no Gemini output has been received. Do not attribute any result in this dossier to Gemini.


## 9. Formal adequacy result: observational descent and no-go (2026-11-23)

Added and registered `proofs/lean/GroundingAdequacy.lean`, with finite witness in `GroundingAdequacyExample.lean`.

For a history space H, costed probe family F, and budget B, let h ≈_B h' mean equality of every affordable response. Then:

1. **Profile invariance:** h ≈_B h' iff their complete response profiles agree (the forward direction is proved here; the reverse follows by evaluation).
2. **Reference no-go:** if h ≈_B h' but their independently specified external referents differ, no decoder whose only input is the affordable response profile can recover both referents exactly.
3. **Reference descent criterion:** a referent map factors through H/≈_B iff it is constant on ≈_B classes.
4. **Truth descent criterion:** a truth predicate factors through H/≈_B iff it is invariant (logically equivalent) across ≈_B classes.

The finite Boolean witness instantiates the obstruction: at budget 0, passive observations cannot recover the hidden referent or hidden-bit truth; at budget 1, the intervention-sensitive probe separates the two states and both become observable.

**Axiom audit:** the general no-go theorem and reference descent depend only on Lean's standard `Quot.sound`; truth descent additionally uses standard `propext`. No custom axioms or `sorryAx` were introduced.

**Interpretation:** this is an exact adequacy boundary, not a proof that a particular empirical probe family is adequate. It shows what must be independently validated: every distinction that matters to external reference/truth must be separated by the operational signature, or else the theory must preserve that ambiguity. The quotient is therefore a semantics relative to a probe regime, not an ontological identity relation simpliciter.


## 10. Prior-art boundary for the new adequacy lemma

The abstract mathematical ingredients are established elsewhere and must not be claimed as novel:

- **Predictive-state / causal-state equivalence:** histories are grouped when they induce the same predictions for all future tests. Crutchfield–Young computational mechanics and predictive-state representations are direct precedents. Singh, James & Rudary define controlled-system states through predictions of observable test outcomes and organize history/test predictions in a system-dynamics matrix (UAI 2004; source: `Predictive State Representations: A New Theory for Modeling Dynamical Systems`).
- **Causal identifiability:** a target quantity is identifiable from observations under assumptions when equality of observed distributions across admissible models forces equality of the target quantity. This is the same logical shape as the reference no-go theorem.
- **Interventional/counterfactual model equivalence:** causal models can be compared by agreement on observational, interventional, and counterfactual predictions. More informative interventions refine the equivalence relation.

Accordingly, `GroundingAdequacy` is not a new general theorem of quotient theory, predictive-state theory, or causal identifiability. Its contribution to this programme is to make the adequacy boundary explicit in the same typed interface as external reference, truth, resource-indexed probes, and the higher semantic reconstruction pipeline. The next novelty-bearing problem is to derive a principled, non-circular operational probe-generation/validation procedure and connect its separation structure to the higher moduli of grounded semantic systems.

Relevant sources:
- Singh, James & Rudary (2004), *Predictive State Representations: A New Theory for Modeling Dynamical Systems*: https://faculty.cc.gatech.edu/~isbell/reading/papers/uai2004psr.pdf
- Stanford Encyclopedia of Philosophy, *Causal Models*, especially identifiability and interventions: https://plato.stanford.edu/entries/causal-models/
- Pearl-style identifiability definition: https://pmc.ncbi.nlm.nih.gov/articles/PMC2836213/


## 11. External-target calibration and resource-indexed separation (2026-11-23)

Added and registered `proofs/lean/OperationalGroundingAdequacy.lean`.

The structure `OperationalGrounding` deliberately distinguishes:
- internal operational systems;
- external targets/referents;
- probes and their execution costs;
- internal system responses;
- independently specified external responses;
- a realization relation between systems and targets;
- calibration: realized systems return the externally specified response for every probe.

For each budget B, `SeparatesAt G B` says every pair of distinct external targets is distinguished by at least one probe of cost ≤ B.

Machine-checked consequences:
1. **Grounded referent uniqueness:** calibrated systems with equal affordable profiles must realize the same external target, provided the external probe family separates at B.
2. **Underdetermination witness:** failure of separation yields two distinct external targets agreeing on every affordable external probe.
3. **Resource monotonicity:** separation at B implies separation at every C ≥ B.
4. **Finite hidden-bit calibration:** the passive probe does not separate at B=0; the active reveal probe separates at B=1; calibrated realized systems with equal B=1 profiles have the same external referent.

This is the first explicit formal bridge from internal response profiles to an independently typed external target. It still does not prove calibration or separation for any real physical/computational domain. Those are exposed as independently testable premises, not hidden in a category definition.

**Axiom audit:** referent uniqueness and the non-separation witness use standard classical choice/propositional extensionality and quotient principles; resource monotonicity is axiom-free. No custom axioms or `sorryAx`.


### 11.1 Profile embedding characterization

The operational interface now also defines the external profile map
`ExternalProfileAt_B : External -> (AffordableProbe_B -> Outcome)`
and proves that it is injective **if and only if** the external probes separate targets at budget B. Calibration is proved to be equality of internal and external profile functions. Thus the grounded-reference theorem factors cleanly into:

`calibration` + `external-profile injectivity` (equivalently, `SeparatesAt B`) + `internal-profile equality` ⇒ `external referent equality`.

This is the precise bridge from an independently specified external target space into the space of operational response profiles. It is not yet a higher-categorical full-faithfulness theorem: it establishes injectivity on objects only. To obtain full faithfulness, the next step must include admissible transformations and prove that response-profile equivalence both preserves and reflects the relevant mapping spaces/morphism sets.


## 12. Grounded relative-density theorem: exact strict 1-category criterion (2026-11-23)

Added `proofs/lean/GroundedRelativeDensity.lean` and finite counterexample `GroundedRelativeDensityExample.lean`.

Let E be an external semantic category, C an operational category, R : E → C a realization functor, and P a family of operational probes. `RelativeProbeDensity` requires the canonical probe-incidence cocone to have the colimit universal property only for pairs of objects in the realized image of R. It is not required to be dense on all of C.

The formal result is an equivalence of adequacy conditions:

`R is fully faithful` iff `the composite external-to-operational response-profile representation is fully faithful`,

provided P is relatively dense on the realized image. The forward direction composes the hom-equivalence for R with the restricted-Yoneda hom-equivalence. The reverse direction reconstructs an operational arrow uniquely from its probe profile, then uses profile-level full faithfulness to recover the external arrow. All hom-sets, including non-invertible program/compiler/state-transition maps, are preserved and reflected.

A finite counterexample shows why relative density is necessary: the empty probe family admits a natural profile transformation from false to true in the discrete Bool category even though there is no category morphism false → true. Hence the relative colimit universal property fails.

**Axiom audit:** the relative-density theorem and its full-faithfulness equivalence depend only on standard `Quot.sound`; no classical choice, custom axiom, or `sorryAx`. The empty-probe counterexample is also included in the audit.

**Prior-art boundary:** this is a strict categorical packaging of standard dense restricted Yoneda plus composition/reflection of fully faithful functors, not a new theorem of category theory. Predictive-state representations already encode dynamical states as predictions of executable tests/experiments (Singh, James & Rudary 2004, pp. 1–3). The Semplex synthesis is the explicit separation of external semantics, realization, resource-bounded operational probes, relative density on the realized image, reference/truth descent, and the higher moduli programme. No novelty claim should be made for the individual categorical ingredients.

Source: Singh, James & Rudary, *Predictive State Representations: A New Theory for Modeling Dynamical Systems* (UAI 2004), https://faculty.cc.gatech.edu/~isbell/reading/papers/uai2004psr.pdf


## 13. Higher lift: precise conjectural theorem boundary

The expected `(∞,1)`-categorical theorem is now specified in the master dossier: weighted probe-colimit presentations of each realized object imply that restricted higher-Yoneda induces equivalences of mapping spaces on the realized image. Composing with R gives `N_P∘R` fully faithful iff R is fully faithful. The homotopy fiber over an in-image profile is then contractible on maximal subgroupoids.

This is the appropriate higher moduli statement. It is distinct from, and does not imply, contractibility of the core of the unrestricted category of all diagram extensions. The latter inference is false in general because Kan-envelope comparison equivalence can leave nontrivial retracts (Section 13.2 of the GHSRT dossier).

Status: theorem statement and weighted-colimit hypothesis specified; no higher-categorical proof or Lean formalization yet. The only machine-checked version currently established is the strict 1-category result in `GroundedRelativeDensity.lean`.


## 14. Strict 1-groupoid moduli theorem (2026-11-23)

Added `GroundedModuliFiber.lean` and `GroundedModuliFiberExample.lean`.

Given an external groupoid E, operational category C, fully faithful realization functor R : E → C, and a probe family relatively dense on the realized image, the module constructs:
1. the groupoid whose objects are external systems and whose arrows are natural transformations between their restricted operational response profiles;
2. a groupoid equivalence from E to that grounded profile groupoid;
3. contractibility of the homotopy fiber over every in-image profile, in the precise strict 1-groupoid sense already formalized by `SemanticModuliFiber`: inhabited fiber objects and exactly one compatible arrow between any two.

The finite example is deliberately nontrivial: the external groupoid has one object; the operational category has two disconnected objects (false and true); the realization lands only at false; and the probe family contains only false. This probe family is **not globally dense** in the operational category, but it is relatively dense on the realized image. The grounded profile groupoid is nevertheless equivalent to the external groupoid and its moduli fiber is contractible. This demonstrates why the relative, rather than global, density condition is the right one.

**Axiom audit:** `groundedProfileEquivalence` and `grounded_moduli_fiber_contractible` depend only on standard `Quot.sound`; the finite non-global-density counterexample is axiom-free. No classical choice, custom axioms, or `sorryAx` in this package.

**Scope:** this is a strict 1-groupoid result. It preserves ordinary hom-sets/automorphism groups and proves a contractible 1-groupoid fiber. It is not yet the full `(∞,1)`-categorical theorem, where mapping spaces, higher paths, and coherence cells must be retained.


## 15. Lossless semiosis transport to the profile quotient (2026-11-23)

Added `GroundedSemiosisTransport.lean`. The kernel of the external profile map defines a quotient of external targets by equal affordable response profiles. Under `SeparatesAt B`, the quotient is equivalent to the external target type; its inverse is defined by quotient recursion, not by selecting an arbitrary representative.

A general `GroundedSemiosis` structure now transports to this profile quotient without changing:
- signs or contexts;
- the expression map from signs/contexts to claims;
- relational reference (not forced to be a function);
- satisfaction/content truth;
- evidence types;
- the evidence-soundness implication.

The preservation theorems show content truth, grounded-assertion truth, and evidential support are invariant under the transport. The construction preserves the distinction between truth and evidence: evidence soundness is transported, but truth is not made equivalent to having evidence.

**Axiom audit:** the quotient equivalence and all transport/preservation theorems depend on standard `propext`, `Classical.choice`, and `Quot.sound`; no custom axioms or `sorryAx`. The use of classical choice is standard and explicit in the audit.


## 16. Quotient-based semiosis transport and finite truth/evidence witness

The transport layer was sharpened to avoid selecting representatives: `ProfileWorld` is the quotient of external targets by equality of affordable external response profiles. Under `SeparatesAt B`, the quotient is equivalent to the external target type via quotient recursion. This avoids a representative-choice construction.

`GroundedSemiosisTransportExample.lean` instantiates the transport with the hidden-bit system. At budget 1, the true bit yields a true grounded assertion in profile space, while the evidence type remains empty. This machine-checks that the representation change does not collapse truth into evidential support.

The proof uses standard quotient and classical principles, no custom axioms or `sorryAx`.


### 14.1 Canonical profile composition verified

A potential gap in the groupoid construction was checked explicitly: its transported composition was not merely assumed to coincide with pointwise composition of natural transformations. Added `profileCompose_is_pointwise` to `GroundedModuliFiber.lean`, proving that the composition recovered through the external category is exactly the canonical componentwise composition of profile natural transformations. The proof uses realization functoriality, associativity in C, and the profile reconstruction equivalence. Its axiom audit reports only `Quot.sound`.

## 18. The response-invisible relabelling no-go and anchor criterion (2026-11-23)

Added to OperationalGroundingAdequacy.lean:

1. **Invisible relabelling theorem.** If an external relabelling sigma preserves every external response for every probe, then its complete response profile is unchanged at every resource budget. If it moves any target, global separation fails at every budget.
2. **Calibration invariance.** The same internal response remains calibrated after reindexing the realization relation by sigma. Hence calibration alone cannot fix external labels that are invisible to the probe language.
3. **Finite permanent-blindness countermodel.** hiddenCoordinateGrounding is perfectly calibrated but probes only the first coordinate of a two-bit external target. The second coordinate remains unidentifiable at every budget. A truth predicate depending on that coordinate is not profile-observable.
4. **Independent-anchor criterion.** An anchor need not encode all external targets. It need only separate pairs that remain indistinguishable under the operational profile. anchoredProfile_injective_iff_anchor_separates_residual proves this condition necessary and sufficient for the combined profile-plus-anchor to be injective. anchor_breaks_invisible_symmetry proves that any symmetry it resolves must change the anchor value.

This is an anti-circularity result, not a magical grounding theorem. It proves that internal predictive consistency and calibration cannot resolve observational gauge freedom. To identify external semantics, the framework needs independently validated anchors/interventions. If the anchor is itself defined by the target semantics, circularity has merely been relocated.

Axiom audit: the no-go, calibration-invariance, reindexing, and anchor-injectivity theorems are axiom-free or use only standard Quot.sound; the finite profile/truth counterexample uses standard propext and Quot.sound. No custom axioms or sorryAx.


### 18.1 Profile-derived anchors cannot solve profile ambiguity

Added axiom-free theorem profile_derived_anchor_cannot_break_ambiguity. If two external targets have equal operational profiles, every anchor computed as a function of that same profile assigns them equal anchor values. Therefore no post-processing, decoder, compression, or re-encoding of the original observations can break their ambiguity. A genuine anchor must contribute information not functionally determined by the original operational profile.

## 19. Causal anchor fusion and intervention-generated identification (2026-11-23)

Added CausalAnchorAdequacy.lean.

### 19.1 Independent channel fusion

For two operational channels A and B over the same external domain, the joint profile is the ordered pair of their affordable response profiles. The theorem joint_identification_iff_kernel_intersection_trivial proves that joint identification holds iff the intersection of their observational equivalence relations is the diagonal. In plain terms: every pair of distinct targets must be distinguished by at least one channel.

The finite complementary-coordinate model exhibits why independent channels can help: channel A sees only coordinate one; channel B sees only coordinate two; neither alone identifies the full two-bit target, but their joint profile does. The profile-derived-channel theorem separately establishes that deterministic post-processing of an existing channel cannot refine its observational kernel.

### 19.2 A genuinely dynamical intervention model

CausalExperiment explicitly separates:
- an external target and apparatus initialisation map;
- apparatus state;
- an observation function;
- an intervention/state-transition function;
- intervention costs.

The experiment response is not assigned arbitrarily per probe: it is generated as the observation trace of the transition dynamics. The two-stage measurement example initially observes the first bit. One intervention changes the apparatus observation phase, exposing the second bit. At budget zero, two targets differing only in the second bit are indistinguishable; at budget one, the complete response profile identifies the two-bit target.

This establishes a formal causal route by which an additional measurement can resolve an ambiguity. It does **not** yet prove that any chosen physical apparatus actually implements the stipulated transition/observation functions, nor that those functions are independently calibrated against nature. That empirical bridge remains an open obligation. The theorem is therefore a conditional causal-identification result, not a completed universal grounding theorem.

The new Lean target and axiom audit are registered in lakefile.lean and check_all.ps1.
