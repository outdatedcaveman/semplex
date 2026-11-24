# Toward a triadic, coalgebraic, institutional semantics
Date: 2026-11-22
Status: architectural conjecture and proof programme, not a theorem.

## 1. Motivation

The current grounded-model Lean structure has a claim-to-world reference map and a satisfaction predicate. It is deliberately explicit, but it is still too static and dyadic to capture the Peircean idea that semiosis is an irreducible relation among sign, object and interpretant, and that interpretants can themselves enter further semiosis.

A static category of semantic models is also not enough for ongoing computation, inquiry, learning, biological regulation or social interpretation. These are state-transition processes. Coalgebra provides a mature mathematical language for such dynamics, while institutions provide a mature language for syntax/model/satisfaction and translations among logics. Sheaf theory handles local empirical contexts and global-section obstructions.

A possible unifying architecture is therefore an **institution-enriched coalgebra of triadic semiosis**, with causal realization and resource-indexed probes.

## 2. Proposed layers

### 2.1 Triadic semantic event

A semantic event should have three irreducible roles:
- sign/representamen S;
- object O;
- interpretant I.

The primitive relation is ternary:
[
mathsf{Sem}(s,o,i)subseteq S	imes O	imes I.
]
Do not replace it by three independent binary edges unless a theorem establishes that the factorization preserves the relevant semantics.

A continuation map or transition relation allows an interpretant to become a sign in a later semiosis:
[
mathsf{next}:I	o S
]
(or, more generally, a relation/distribution over next signs and contexts). This is a formal interface for semiosis as a process, not a claim that Peirce's entire theory is captured by one function.

### 2.2 Coalgebraic dynamics

Let ᵎ be a category of triadic semantic configurations, and F:ᵎ→ᵎ (or a suitable endofunctor on a category of state carriers) describe admissible next-step semiosis, interventions, observations and updates.

A semantic process is an F-coalgebra:
[
c:X	o F(X).
]
Coalgebra morphisms preserve the chosen dynamics. Bisimulation/behavioral equivalence identifies states with the same behavior relative to F. If a final coalgebra ν F exists, the unique map into it supplies final behavioral semantics.

**Critical qualification:** final-coalgebra semantics is fully abstract only relative to the behavior functor and the chosen behavioral equivalence. It does not independently establish that the observation functor tracks the intended external object or that the chosen F includes all semantically relevant actions.

### 2.3 Institution layer

An institution I has signatures, sentences, models and satisfaction, with the satisfaction condition ensuring invariance under signature translation. Use this to host logical and computational theories without privileging one syntax.

A higher/enriched extension may replace Set/Cat by spaces/∞-categories where appropriate, but that extension must be defined and its coherence proved; it must not be assumed for free.

The desired combined object is not merely a product of an institution and a coalgebra. The transition dynamics should act on institution models, sentences, and evidence in a coherent way. Candidate formulation: a coalgebra internal to an appropriate category (or ∞-category) of institutions/structured models, or an institution-valued coalgebra. Which is correct depends on the intended morphisms and must be settled by universal properties.

### 2.4 Contextual empirical layer

Let Ctx be a site/category of experimental contexts. Assign local empirical data to each context and restriction maps to overlaps. A compatible family may or may not extend to a global section. Failure to extend is not automatically a defect: contextuality may be a genuine physical/computational property.

For higher-valued data, use a stack or higher sheaf only when the descent conditions are satisfied. Retain obstruction data when they fail.

### 2.5 Causal realization

Define an operational category Op whose objects are systems with independently specified intervention and observation protocols. A realization is a structure-preserving map/anafunctor/representation from a semantic coalgebra to Op, commuting with the chosen interventions and predicting outcomes within declared error bounds.

Do not define realization as “the semantic object that makes the proposition true.” Instead, calibrate it through:
- intervention response;
- out-of-sample prediction;
- counterfactual invariance;
- transport across independently measured contexts;
- correction when predictions fail.

These conditions are empirical and domain-specific. Their validity is not a theorem of category theory.

### 2.6 Resource-indexed probes and moduli

For budget B, let P_B be the category of admissible probes/tests. A restricted higher profile functor sends a grounded triadic coalgebraic institution to its space-valued profile. The moduli space of a profile is the homotopy fibre of this functor on maximal subgroupoids/cores.

If P_B is dense, the restricted nerve is fully faithful and profile fibres are contractible. If not, the fibre records indistinguishable realizers and their automorphisms/higher symmetries. Increasing B refines the profile, but quantitative rates require additional metric/probabilistic assumptions.

## 3. Candidate unifying theorem

**Grounded Triadic Coalgebraic-Institution Reconstruction (GTCIR) — conjectural.**

Fix:
- a declared class Τ of operational semantic systems;
- a semantic preservation signature Σ;
- a small context site Ctx;
- an institution-valued category of triadic semantic configurations;
- an accessible endofunctor F encoding admissible semiosis transitions and interventions;
- an operational realization functor R into a category of measured systems;
- a resource-indexed probe family P_B.

Suppose:
H1. The category and endofunctor satisfy the relevant size/accessibility conditions, and the required final coalgebra (or a specified replacement) exists.
H2. The semantic coalgebras satisfy the specified transition and triadic coherence laws.
H3. The institution satisfaction condition holds for all admissible theory translations.
H4. Realization commutes with the declared interventions and is independently calibrated by empirical tests.
H5. The context-indexed empirical assignment satisfies descent exactly where global realizations are claimed; elsewhere its obstruction is retained.
H6. P_B is dense in the category of grounded semantic coalgebras for the declared signature.
H7. The interpretations of the selected source theories are conservative for Σ.

Then:
1. final behavioral semantics is fully abstract for the F-behavioral equivalence;
2. the resource-indexed restricted profile is fully faithful on the declared grounded semantic category;
3. profile homotopy fibres in the essential image are contractible, with all higher equivalences/coherences preserved;
4. operational realization and institution satisfaction are invariant under the induced semantic equivalences;
5. contextual obstructions and finite-budget non-identifiability remain explicit in the moduli/obstruction data;
6. the included semantic theories embed conservatively for Σ.

The conclusion is **relative universality** for Τ and Σ, not absolute universality over every possible use of “meaning.”

## 4. Why this may unify more than the current theorem

- **Logic:** institutions and hyperdoctrines encode signatures, propositions, models, substitution, quantification and satisfaction.
- **Computation:** coalgebraic behavior models state transitions, automata, protocols and interactive processes.
- **Peircean semiosis:** the primitive semantic event is triadic and temporally extensible through interpretant-to-sign continuation.
- **Causality/physics:** realization is constrained by intervention and observation, not merely by formal interpretation.
- **Contextuality:** sheaves encode local empirical data and global-section obstructions.
- **Higher mathematics:** ∞-categorical profiles and moduli retain paths, automorphisms and higher coherence.
- **Resource-bounded cognition/computation:** probe budgets determine what can actually be distinguished.

## 5. What could make this proposal fail

1. No appropriate category of institution-enriched triadic coalgebras may exist with the desired morphisms and compositional laws.
2. A final coalgebra may not exist for the required functor; accessible endofunctors are a sufficient route in many locally presentable settings, but not a universal guarantee.
3. Behavioral equivalence may be too coarse or too fine relative to semantic identity; finality only solves the equivalence problem after F is chosen.
4. A causal realization may be many-to-many, non-functorial, context-dependent, or non-identifiable. A single realization functor may be too restrictive.
5. The Peircean triadic relation may not admit a faithful reduction to a simple ternary predicate plus continuation function. We may need a relation-valued/higher structure.
6. Institution satisfaction can preserve truth under translation while leaving truth's external correctness ungrounded.
7. Contextual empirical models may lack global sections. The framework must not force them to glue.
8. Conservative translations among model-theoretic, proof-theoretic, pragmatic and informational semantics may exist only on a narrow common signature or may be impossible.
9. The entire structure may be a sophisticated synthesis of known institution, coalgebra, sheaf and higher-category theories without a genuinely new theorem. Novelty must be demonstrated by a theorem not already subsumed by these frameworks.

## 6. Proof strategy and dependency graph

A. Define the triadic institution category and its morphisms; prove identities/composition and satisfaction transport.
B. Define F and prove it is an endofunctor (or accessible polynomial/power functor) on that category.
C. Establish final-coalgebra existence under explicit conditions; prove the standard final semantics/bisimulation result for the chosen F.
D. Define operational realization independently and prove intervention-commutation and calibration transfer.
E. Define context-site empirical assignments; prove descent for a restricted class and exhibit non-gluing countermodels.
F. Define resource-indexed higher probe functor and prove density/full-faithfulness/homotopy-fibre contractibility.
G. Prove the compatibility theorem joining A–F; show that the squares commute and that obstruction data is retained.
H. Establish conservative interpretations from selected theories, or record no-go results.

## 7. Prior-art and conceptual sources

- Goguen & Burstall (1992), “Institutions: Abstract Model Theory for Specification and Programming,” JACM 39(1), 95–146, DOI 10.1145/147508.147524.
- Abramsky & Brandenburger (2011), “The Sheaf-Theoretic Structure of Non-Locality and Contextuality,” New Journal of Physics 13, 113036; arXiv:1102.0264.
- Rutten (2000), “Universal Coalgebra: A Theory of Systems,” Theoretical Computer Science 249, 3–80. Coalgebraic behavioral equivalence and final semantics are established foundations.
- Power & Turi (1999), “A Coalgebraic Foundation for Linear Time Semantics,” ENTCS 29, 259–274, DOI 10.1016/S1571-0661(05)80319-6.
- Kilstrup (2015), “Naturalizing semiotics: The triadic sign of Charles Sanders Peirce as a systems property,” Progress in Biophysics and Molecular Biology 119(3), 563–575, DOI 10.1016/j.pbiomolbio.2015.08.013.
- Stanford Encyclopedia of Philosophy, “Charles Sanders Peirce,” section on semeiotic; and “Proof-Theoretic Semantics,” revised 2023.

These references establish that the ingredients are mature. The research target is the nontrivial compatibility and adequacy theorem, if it exists.

## 8. Critical Peircean refinement: triadic relation is not yet enough

A direct examination of Hugo F. Alrøe, “The six types of sign action,” *Semiotica* 2025(266), 1–30, DOI 10.1515/sem-2024-0112 (published 13 June 2025), forces a substantial refinement.

The paper distinguishes **representation** (the sign–object–interpretant relation) from **mediation** (a temporally directed source–mediator–outcome process). It argues that Peircean sign action requires their integration, and proposes six directions/types of sign action: perceiving, acting, interpreting, expressing, sensing and reacting. It also distinguishes a dynamical object from an immediate object, and immediate, dynamical and final interpretants. It explicitly discusses the unresolved problem of defining semiosis in living systems without assuming a homuncular interpreter.

This has direct consequences for our formalization:

1. The current `TriadicGroundedSemiosis.lean` structure (a ternary relation plus `nextSign`) is only a minimal interface. It is not a faithful formalization of the richer Peircean architecture.
2. We need at least two linked structures: (a) a representation relation and (b) a causal/temporal mediation relation. They should not be identified by definition.
3. The dynamical object must be independently embodied/causally effective, while the immediate object is the object as represented by the sign. This gives a principled route to avoid circularly defining reference as “the object the sign refers to.”
4. The interpretant should be stratified (immediate, dynamical, final) where the application requires it. The final interpretant is not simply the next state in a temporal transition; it is a normative/ideal limit concept and must not be collapsed into coalgebraic iteration.
5. A complete sign-action architecture should account for the six directions, or justify a restricted subset for a specified domain. A single `nextSign : Interpretant → Sign` map cannot do this.
6. Operational adequacy requires a non-homuncular interpreter condition: specify the physical/functional organization that realizes interpretive effects, not an unexplained external observer.

The paper also explicitly warns that Peirce's standard model has unresolved gaps and that the broader semiotic field is divided over how to extend semiosis to cells and non-human systems. This is not a settled foundation; it is an active theoretical problem. We should treat Alrøe's sixfold architecture as a serious candidate and adversarial comparison, not as established consensus.

The revised target should be a **two-layer triadic mediation model**: a representation institution (sign, immediate/dynamical object, immediate/dynamical/final interpretant) coupled to a mediation coalgebra (source, mediator, outcome and intervention-sensitive transitions). The coupling itself is a theorem/structure to be justified, not a definitional collapse.

Source: https://doi.org/10.1515/sem-2024-0112 ; publisher page https://www.degruyterbrill.com/document/doi/10.1515/sem-2024-0112/html (see especially sections 2–4).

## 9. Terminological correction: interpretant-as-sign is not temporal next-state

The Lean field previously named `nextSign` has been renamed `interpretantSign` in both triadic modules. This is deliberate: Peirce's claim that an interpretant is itself capable of functioning as a further sign is a representational/logical continuation, not automatically a temporal transition in the physical system.

Actual temporal evolution belongs in a separate mediation/dynamics structure (e.g. a coalgebra or open-system transition), with its own state, input, output and update maps. The final interpretant is a third, normative/ideal-limit notion and must not be identified with either the interpretant-as-sign map or an ordinary coalgebraic next state.

This three-way separation is now an explicit design constraint:
- **Interpretant-as-sign:** semiotic continuation of representation.
- **Dynamical mediation:** temporally realized causal transition.
- **Final interpretant:** ideal/normative limiting interpretation under specified inquiry conditions.

The rename was followed by successful focused and full Lean builds.

## 10. Operational semiotic scaffold formalized

Added `proofs/lean/OperationalSemioticScaffold.lean` as a minimal closed-loop, non-homuncular process interface. A scaffold has:
- an environment/world state;
- an internal memory state;
- a sensor mapping world states to signs;
- an interpretation operation from memory and sign to interpretant;
- an action-selection operation;
- a learning/update operation on memory;
- an environment transition driven by action.

One step performs: sense → interpret → choose action → update memory and world. A structure-preserving map between scaffolds must commute with every component. The module proves that such a map commutes with one full cycle and preserves every finite output trace.

This is an operational systems model that does not posit an external homuncular interpreter: the interpreting mechanism is part of the system's internal state and transition structure. It is not yet a theory of semantic correctness. Trace preservation is relative to the chosen sensors, actions, state and transition laws; it does not prove that the sensor tracks the intended dynamical object or that the interpretant is true.

Focused and full Lean builds pass. Axiom audit reports only standard `propext` for equality of propositional outputs. No custom axioms or `sorryAx`.

## 11. Intervention-relative identification theorem formalized

Added `proofs/lean/InterventionGrounding.lean`. It defines a resource-costed family of intervention sequences, the observation trace induced by an intervention sequence, and observational equivalence of world states at budget B:
[
w sim_B w' iff orall a ; (cost(a)le B Rightarrow trace(w,a)=trace(w',a)).
]

The module proves this is an equivalence relation, that it is antitone in budget (indistinguishability at a larger budget implies indistinguishability at a smaller one), and that a protocol is separating when no distinct world states remain equivalent.

A finite example has a hidden Boolean component and a visible sensor component. At budget zero, two worlds with different hidden bits are indistinguishable. A single intervention reveals the hidden bit; at budget one, the protocol separates all world states. Both the positive and negative separating results are machine-checked.

This is a concrete operational grounding principle: referential identity is identifiable only up to the equivalence induced by admissible interventions. It does not claim metaphysical identity; if two external states remain indistinguishable under every admissible intervention, the correct output is residual ambiguity, not an invented distinction.

Full Lean build and `git diff --check` pass. Axiom audit: the new observational-equivalence and separating results depend only on standard `propext`; the equivalence-relation and budget-monotonicity lemmas are axiom-free. No custom axioms or `sorryAx`.

## 12. Operational reference as a relation into a resource-relative moduli space

Added `proofs/lean/OperationalReference.lean`. It defines the referent space at budget B as the quotient of world states by the intervention-response equivalence relation from `InterventionGrounding.lean`. A sign operationally refers to a referent class when some representative of that class produces the sign.

The module proves:
- richer-budget referent classes map canonically to coarser-budget classes;
- operational reference is preserved under this forgetting map;
- two worlds with different hidden states occupy the same referent class at budget 0;
- those same worlds occupy distinct referent classes at budget 1;
- the same observed sign can refer to two distinct referent classes at budget 1.

The last result is important: reference is not forced to be a function from signs to unique worlds. Under partial observation, a sign can be compatible with several distinct operational referents. Additional interventions refine the moduli space and can disambiguate them. If no admissible intervention separates two targets, the theory must preserve that ambiguity.

This is an explicit, non-truth-conditional operational account of referential identifiability. It is not yet a complete theory of reference: the choice of sensor and intervention protocol must be independently justified, and the relation between immediate object and dynamical object remains to be modeled.

Full Lean build and diff check pass. Axiom audit: reference transport uses standard `Quot.sound`; low-budget class coincidence uses `propext` and `Quot.sound`; separation and the two-referent theorem use only standard `propext`. No custom axioms or `sorryAx`.
## 13. Syntax–satisfaction descent theorem formalized

Added `proofs/lean/OperationalSatisfaction.lean`. For a declared intervention protocol P and budget B, an `ObservableClaim` is a predicate on world states invariant under the observational equivalence relation `~_B`. The module constructs its unique descended satisfaction predicate on the quotient referent space `W/~_B`.

Machine-checked results:
- every B-observable claim descends to a predicate on operational referent classes;
- the descended predicate is unique among predicates agreeing on every representative;
- a claim observable at a lower budget remains observable at a higher budget;
- satisfaction commutes with the canonical map forgetting higher-budget referent distinctions;
- in the finite hidden-bit model, the hidden-bit proposition cannot be represented as an observable claim at budget 0, but is observable at budget 1 after a reveal intervention.

This gives a precise local bridge between a syntax of admissible claims and semantics as satisfaction over operationally identified referents. It is not a proof that all meaningful claims are observable, nor that the chosen interventions are complete for a domain. The invariance condition is a necessary admissibility condition relative to the selected observational language. Whether it is sufficient for semantic legitimacy in physical, mathematical, computational and human domains remains an adequacy question.

Full Lean build and `git diff --check` pass. The axiom audit reports only standard `propext` and `Quot.sound`; no custom axioms or `sorryAx` occur in these results.## 14. Representative invariance of operational reference

Extended `proofs/lean/OperationalReference.lean` with a proof that every budgeted observational equivalence preserves the current sensor output, because the empty intervention is always affordable. From this, proved that all representatives of a given operational referent class have the same current sensor output. Consequently, once a sign is related to a quotient class by the existential operational-reference relation, every representative of that class produces that sign.

This closes a small but essential well-definedness obligation: reference is not allowed to depend on an arbitrary representative chosen after quotienting. The result is still protocol-relative; it does not establish that the sensor is calibrated to an external referent.

Focused build of `OperationalReference` passes. The full Lean build is being rerun after this addition.