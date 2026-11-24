# Six-hour universal-semantics proof campaign
Started: 2026-11-22
Status: active; elapsed time is not inferred from the mandate.

## Mission
Determine what can actually be proved about a universal theory of semantics, separating formal reconstruction from semantic adequacy, external grounding, and universality across theories.

## Operating rules
- Correctness before apparent progress.
- Every theorem states its assumptions and their epistemic status: definition, formal hypothesis, independently justified operational principle, or empirical claim.
- Counterexamples are first-class outputs.
- No novelty claim for established Yoneda, density, Kan extension, presheaf, causal-category, or homotopy-fibre machinery by itself.
- No git commits, pushes, merges, paid APIs, purchases, or external side effects.
- Gemini/Codex contributions are reported only if actual outputs arrive.
- Work remains in the canonical Semplex repository.

## Workstreams
1. Higher reconstruction: genuine space-valued restricted Yoneda, essential image, homotopy fibres, universe/size constraints, coherent mapping spaces.
2. Grounding: independently specified operational systems, causal interventions, counterfactual predictions, realization and correction.
3. Probe adequacy: density criteria, resource-bounded indistinguishability, separating families, no-go results.
4. Truth and evidence: reference, satisfaction, truth, warrant, evidence soundness/completeness, defeasibility.
5. Contextuality: sites, sheaves/stacks, descent, gluing obstructions and higher coherence.
6. Cross-theory adequacy: model-theoretic, proof-theoretic, pragmatic, informational, causal and computational interpretations.
7. Applications: graph gauge, holonomy, isotropy and higher symmetries.
8. Prior art: verified sources, scope and novelty boundaries.

## Timeline / evidence log

### T+0 — campaign opened
- Created orchestrated meta-project `universal-semantics-six-hour-proof-campaign`.
- Assigned independent adversarial review to peer analysis tracks. Assignment is not evidence of completion.
- Enabled orchestrator autonomy in `supervise_only` mode: stale tasks may be requeued; it does not invent work.
- Started local regression process (PID 11164): full Lean build, full Python pytest suite, then `git diff --check`. Awaiting final output.

### T+0 — initial research constraints
The current GRBHR results are conditional reconstruction results. They do not by themselves establish:
- that the selected category contains all semantic phenomena;
- that its reference relation reaches an external target;
- that its satisfaction relation is correct;
- that the operational probe family is dense;
- that competing semantic theories embed conservatively;
- that strict groupoid results extend to all higher mapping spaces.

### T+0 — immediate theorem-design decision
Do not formulate “universal semantics” as the unrestricted category of all structures with a truth predicate. That is trivially broad and semantically empty. Require independent operational admissibility conditions and a declared scope of systems/theories. Universality is always relative to a specified class and preservation signature; an unrestricted absolute claim risks being undefinable or false.

## Decision register
- D1: Separate representational completeness from semantic adequacy.
- D2: Treat density as a substantive condition to prove/test, not as a convenient premise hidden in the definition of “adequate probes.”
- D3: A realization map must be specified independently of the correctness predicate it is later used to validate.
- D4: Truth, warrant, evidence and successful action are distinct notions; no one may be substituted for another without a theorem.
- D5: Preserve automorphisms/isotropy and higher paths; quotienting to object-level equivalence may erase semantic structure.
- D6: Any universality theorem must name its domain of theories and its conservative signature.

## Open questions
- What minimal operational signature suffices to characterize reference without circularly defining it as “whatever makes the claim true”?
- Can operationally generated probes be shown dense, or is density only an ideal limit? What is the finite-budget residual ambiguity?
- Which semantic theories can be embedded conservatively into one institution/category, and which are irreducibly incompatible?
- What descent conditions are empirically/mathematically warranted rather than imposed?
- Can the higher moduli construction support defeasible evidence and updates as morphisms in a fibration or indexed category?

## Completion criteria
A campaign result counts only when supported by checked proofs, explicit countermodels, or traceable literature. A plan or theorem sketch is not a proof. The final report must include what failed, what remains conditional, and what would falsify the framework.

### T+1 — first adversarial theorem and literature findings
- Added `proofs/lean/SemanticAdequacyCounterexamples.lean` with finite Boolean examples.
- Proved sufficiency alone does not imply full abstraction: a predictive representation can preserve every observed response while distinguishing states that the available probes cannot distinguish.
- Proved a constant representation can be fully abstract for a deliberately weak probe family, showing that “fully abstract” is always relative to a specified observational language and does not guarantee rich semantics.
- Proved an observation pair is indistinguishable at budget 0 but separated at budget 1. This is a minimal executable witness that semantic identity under probes is budget-relative.
- Focused Lean build passed; one unused-variable warning was cleaned up. Full build and axiom audit still to be rerun.
- Literature review found a major prior-art correction: institution theory (Goguen–Burstall 1992, DOI 10.1145/147508.147524) already formalizes signatures, sentences, models, satisfaction invariance and truth-preserving translations between logics. Sheaf-theoretic contextuality (Abramsky–Brandenburger 2011, arXiv:1102.0264) already models empirical contexts and global-section obstructions. Lawvere hyperdoctrines already organize indexed propositions, substitution and quantifiers.
- Consequence: T7 as currently phrased is not novel. The promising frontier is the compatibility of higher/resource-indexed moduli, institution-style satisfaction, operational causal realization, and evidence/warrant structures. Contextuality must be represented as a possible obstruction, not erased by forcing a global sheaf.

### T+2 — formal verification and conceptual revision
- Added `proofs/lean/SemanticAdequacyCounterexamples.lean` to Lake. Full `lake build` passed after inclusion; `git diff --check` passed.
- Axiom audit: sufficiency-not-full-abstraction, coarse-representation full abstraction, and high-budget separation have no axiomatic dependencies. The low-budget indistinguishability theorem depends on standard `propext` and `Quot.sound` through quotient/setoid infrastructure. No custom axiom or `sorryAx` was introduced.
- The full Python regression suite remains in progress in PID 11164; initial Lean build passed, and pytest output is progressing. Do not report Python suite as complete until final process output.
- Added `research/INSTITUTIONAL_AND_CONTEXTUAL_SEMANTICS_PRIOR_ART_2026-11-22.md`: institution theory already handles cross-logic translations and satisfaction invariance; sheaf-theoretic contextuality already handles local empirical models and obstructions to global sections; hyperdoctrines handle indexed propositions/substitution/quantification.
- Added `research/TRIADIC_COALGEBRAIC_INSTITUTIONAL_SEMANTICS_FRONTIER_2026-11-22.md`: proposed a more ambitious integration of Peircean triadic semiosis, coalgebraic process semantics, institution-style logic, contextual empirical sheaves, causal realization, and resource-indexed higher moduli. This is a conjectural architecture, not a proved theorem. Coalgebraic final semantics is itself mature prior art; it only gives behavior relative to the chosen endofunctor and does not solve external reference.
- The existing grounded Lean model remains a static dyadic structure (claim -> world plus satisfaction). It is not yet a formalization of irreducible triadic semiosis or interpretant dynamics. This limitation is now explicit.

### T+3 — triadic formalization
- Added `proofs/lean/TriadicGroundedSemiosis.lean`. It extends the grounded model with a genuine ternary relation `semiosis(sign, object, interpretant)` and an interpretant-to-next-sign continuation map.
- Defined structure-preserving morphisms that preserve/reflect the ternary relation and commute with continuation, in addition to preserving reference, satisfaction and evidence in the grounded base. Constructed the resulting ordinary category and proved truth transport, triadic-relation transport, and continuation commutation.
- The focused build and full Lean `lake build` passed; `git diff --check` passed. Axiom audit: the three semantic transport theorems are axiom-free; all-probe Yoneda reconstruction depends only on standard `Quot.sound`.
- Important limitation: a ternary predicate plus continuation is only a formal interface inspired by Peirce. It does not yet prove irreducibility of the triad, model all six directions of sign action, or ground the relation operationally. The category-level Yoneda result remains conditional on the chosen structure and is not a universal-semantics theorem.
- Full Python regression process PID 11164 is still running after approximately eight minutes; it has emitted continued progress but no final summary. Treat as pending.

### T+4 — regression baseline completed
- The full baseline command completed successfully: Lean `lake build`, Python `pytest -q`, and `git diff --check` all exited 0.
- Python result: **239 passed, 2 skipped in 593.31s**. This includes the new tests already present in the working tree at the time of the run; the newly added Lean-only modules do not change Python sources.
- A second full Lean build after adding the triadic module also passed. Focused axiom audits were completed for the new semantic counterexamples and triadic transport results.

### T+4 — agent orchestration status
- The meta-project dispatch response assigned a review task to Gemini, but no Gemini review output or execution evidence has been received in this campaign.
- The native wake bridge reports local runners for peer analysis runners only; Antigravity is listed as an interactive surface, and Gemini has no confirmed local runner in the wake response. The orchestration database intermittently returns `database is locked` / `mind_slow`; subsequent event reads show the pre-existing Gemini task 143, not a completed response to this new campaign.
- Therefore Gemini must be reported as requested/queued but unverified, not as having contributed. No Codex delegation was used for the mathematical work in this campaign.

### T+5 — irreducible triadic relation and category-theory challenge
- Prior-art audit uncovered Mogens Kilstrup (2015), DOI 10.1016/j.pbiomolbio.2015.08.013, whose article explicitly discusses the incompatibility of a Ψ(O,R,I) sign-linkage model with naïve category-theoretic composition. His point: composing sign-level mappings may have no intrinsic semiotic meaning; role changes may require new sign-establishment events. This is a serious challenge, not a proof that all category theory is incompatible with semiosis.
- Added `proofs/lean/IrreducibleTriadicRelations.lean`: an even-parity relation on Bool³ that cannot be expressed as a conjunction of three pairwise binary relations. Proof: every pair of coordinates extends to a satisfying triple, forcing each binary factor to be universal, while the ternary relation rejects 001. This is a concrete formal witness of irreducible ternary structure.
- Focused build and full Lean build passed; axiom audit reports only standard `propext` for propositional equivalences. No custom axioms or `sorryAx`.
- Architectural decision: keep triadic semiosis primitive as a relation inside whole semantic-system objects. Category theory should model structure-preserving transformations between whole systems, not replace the triad with three composable arrows. Add explicit sign-establishment/memory and sign-interpretation phases; do not assume an interpretant-to-sign transition is just an ordinary arrow composition.
- Added `research/TRIADIC_IRREDUCIBILITY_AND_CATEGORY_COMPATIBILITY_2026-11-22.md` documenting the challenge, proof, limitations and sources.

### T+6 — integration with the pre-existing relational grounding fibration
- Inspection of `SemanticFibrations.lean` and `SemanticResponseCore.lean` revealed a richer pre-existing foundation than the simpler `GroundedModel` category added earlier: relational reference `refers : Sign → World → Prop`, context-indexed claim expression, satisfaction, evidence indexed by sign/context/world, and explicit separation of content truth from grounded assertion truth. The simpler category is therefore only a prototype and should not replace this richer schema.
- Added `proofs/lean/GroundedSemiosisCategory.lean`: a category of the existing `GroundedSemiosis` models. Morphisms preserve/reflect relational reference and satisfaction, commute with context-indexed claim expression, and transport evidence. Proved content-truth invariance, reference invariance, grounded-assertion-truth invariance, and evidence soundness transfer.
- Added `proofs/lean/TriadicRelationalSemiosis.lean`: extends those relational/contextual/evidential models with a ternary sign–world–interpretant relation and interpretant-to-next-sign continuation. Morphisms preserve/reflect the triad and commute with continuation.
- Focused and full Lean builds passed. Axiom audit: assertion-truth, triadic-relation, continuation and evidence-soundness transport are axiom-free; all-probe Yoneda reconstruction depends only on standard `Quot.sound`. `git diff --check` passed.
- This is the most coherent current strict-category core: a relationally grounded semantic institution-like model with an irreducible triadic relation. It still does not model sign establishment/learning, separate immediate/dynamical/final interpretants, independent dynamical-object calibration, or a true ∞-category. Those are the next gaps.

### T+6 — semantic continuation distinguished from temporal dynamics
- Renamed the triadic-model field `nextSign` to `interpretantSign` (and its naturality field accordingly) in both triadic modules. This avoids conflating the Peircean point that an interpretant can itself function as a further sign with an ordinary temporal next-state transition.
- Focused and full Lean builds passed after the rename. Architectural distinction now explicit: interpretant-as-sign (representational continuation), dynamical mediation (temporal causal transition), and final interpretant (normative/ideal limit) are three different structures.

### T+7 — institutional syntax/semantics interface formalized
- Added `proofs/lean/InstitutionalSemantics.lean`: ordinary institution structure with signature category, covariant sentence translation, contravariant model reduct, functorial laws, and satisfaction condition.
- Proved satisfaction transport and compositionality along signature translations. Both theorems are axiom-free. Focused/full Lean builds and `git diff --check` passed.
- This is an explicit formal baseline for the syntax/semantics bridge, not a novelty claim: it instantiates known institution theory. The frontier is to enrich the model fibres with relational reference, triadic semiosis, causal realization, resource-indexed probes and higher moduli while preserving the institutional satisfaction condition.

### T+8 — operational, non-homuncular scaffold
- Added `proofs/lean/OperationalSemioticScaffold.lean`: an environment/agent closed-loop system with sensor-to-sign, memory-conditioned interpretation, action selection, memory learning and environment evolution.
- Proved structure-preserving maps commute with one full sense→interpret→act→update cycle and preserve every finite output trace. Focused/full Lean builds and diff check passed. Axiom audit reports only standard `propext`; no custom axioms or `sorryAx`.
- This provides a concrete non-homuncular operational architecture for semiosis. It does not by itself ground reference or guarantee truth: observational trace preservation is relative to the sensor/action interface. We need independent calibration and intervention tests against the dynamical object.

### T+9 — operational identification under interventions
- Added `proofs/lean/InterventionGrounding.lean`: defines costed intervention sequences, observation traces, and resource-relative observational equivalence of world states.
- Proved equivalence relation laws and monotonicity with budget. In a finite hidden-state model, budget 0 cannot distinguish two different external states, while a one-step reveal intervention makes the protocol separating at budget 1.
- Focused/full Lean builds and `git diff --check` passed. Axiom audit: equivalence and monotonicity lemmas are axiom-free; finite observational indistinguishability/separation theorems depend only on standard `propext`. No custom axioms or `sorryAx`.
- This is the strongest new operational grounding result so far: the framework can define referential identifiability through intervention-response equivalence, and must preserve residual ambiguity where the intervention family cannot separate targets. It is an operational equivalence notion, not metaphysical identity.

### T+10 — operational reference as a resource-indexed moduli relation
- Added `proofs/lean/OperationalReference.lean`: referent spaces are quotient spaces of world states modulo intervention-response equivalence at budget B. A sign refers to a class when some representative produces it.
- Proved canonical forgetting from higher-budget to lower-budget referent spaces and transport of reference along it. In the finite hidden-state model, two distinct worlds occupy one referent class at budget 0 but distinct classes at budget 1; at budget 1, the same observed sign is related to two distinct referent classes.
- This formalizes referential ambiguity rather than forcing unique denotation: under partial observation, reference is a relation into a moduli space of candidate targets. More interventions refine the space; unresolvable distinctions remain ambiguous.
- Full Lean build and diff check pass. Axiom audit: only standard `Quot.sound`/`propext` dependencies in quotient/equivalence constructions; no custom axioms or `sorryAx`.
### T+11 — syntax/satisfaction descent to operational referents
- Added `proofs/lean/OperationalSatisfaction.lean`. Defines claims admissible at budget B as predicates invariant under B-bounded intervention-response equivalence, then descends them to predicates on the quotient referent space.
- Proved existence (by construction), uniqueness, preservation under budget refinement, and commutation of satisfaction with forgetting richer referent distinctions. Finite hidden-bit witness: hidden-bit proposition is not observable at budget 0 but becomes observable after a reveal intervention at budget 1.
- Focused and full Lean builds pass; `git diff --check` passes. Axiom audit: only standard `propext` and `Quot.sound`, no custom axioms or `sorryAx`.
- Scope warning: this is a rigorous syntax–satisfaction interface relative to a declared intervention language. It does not establish that the intervention language is complete or appropriate for every domain, and it does not settle the full higher-categorical semantics theorem.### T+12 — representative invariance of reference
- Extended `OperationalReference.lean`: proved budgeted observational equivalence preserves the current sensor output (the empty intervention is affordable), and hence every representative of a referent quotient class produces the same current sign.
- This establishes that the existential operational-reference relation is independent of the representative chosen after quotienting. It does not independently calibrate the sensor against an external referent.
- Focused Lean build passes.