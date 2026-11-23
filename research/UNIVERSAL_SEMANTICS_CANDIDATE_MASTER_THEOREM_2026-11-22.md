# Candidate Master Theorem for Grounded Universal Semantics
Status: conjectural theorem package; not proved. Version 0.1, 2026-11-22.

## 1. Scope and non-claim

There is no meaningful theorem about “all semantics whatsoever” until the target class is specified. The candidate below is universal relative to a declared class Τ of semantic practices/systems and a preservation signature Σ. It does not claim that every conceivable philosophical use of “meaning” is captured.

The theorem package must establish both:
(i) representation/reconstruction inside a mathematical model; and
(ii) adequacy of that model against independently specified operational and cross-theoretic criteria.

## 2. Data

Fix a sufficiently large universe $\mathcal{U}$ and a smaller universe $\mathcal{U}_0$.

- $\mathcal{C}$: a small category (or ∞-category) of admissible contexts, interventions and resource-bounded experimental situations.
- Τ: a declared class of target semantic systems, each specified by an independently observable operational signature.
- $\mathcal{M}$: an ∞-category of candidate grounded semantic systems, with objects carrying at least a target domain, claim/symbol domain, reference/denotation structure, satisfaction/truth conditions, evidence/warrant structure, update dynamics, and intervention/observation interface.
- Morphisms in $\mathcal{M}$ preserve the declared semantic signature, but must not be defined to preserve unobservable properties merely because the desired theorem needs them.
- $\mathcal{M}_{\mathrm{adm}}$ ⊆ $\mathcal{M}$: the full sub-∞-category of systems satisfying the independently stated operational admissibility tests.
- $\mathcal{P}_B$: admissible probes executable under budget B, with inclusions for B ≤ C.
- $\mathcal{S}$: spaces (∞-groupoids) in $\mathcal{U}$.

The profile functor is
$$
R_B : \mathcal{M}_{\mathrm{adm}} \to \operatorname{Fun}(\mathcal{P}_B^{\mathrm{op}}, \mathcal{S}),
\qquad
R_B(X)(p) = \operatorname{Map}_{\mathcal{M}}(p, X).
$$
The exact variance and whether probes are objects of the same category or a separate test category must be justified in the definitive construction. This is a design choice, not yet settled.

For a profile F, define the moduli space
$$
\operatorname{Mod}_B(F) =
(\mathcal{M}_{\mathrm{adm}})^\simeq
\times_{\operatorname{Fun}(\mathcal{P}_B^{\mathrm{op}}, \mathcal{S})^\simeq}
\{F\},
$$
where ~ denotes maximal subgroupoid/core. The homotopy fibre is a space of candidate systems equipped with profile equivalences, not merely a set of isomorphism classes.

## 3. Candidate theorem package

Assume hypotheses H1–H7 below.

**(T1) Higher reconstruction.** If the probe inclusion is dense in the precise ∞-categorical sense (equivalently, its restricted Yoneda nerve is fully faithful), then R_B is fully faithful: for all X,Y, the induced map of mapping spaces
$$
\operatorname{Map}_{\mathcal{M}_{\mathrm{adm}}}(X, Y) \to
\operatorname{Map}_{\operatorname{Fun}(\mathcal{P}_B^{\mathrm{op}}, \mathcal{S})}(R_B X, R_B Y)
$$
is an equivalence.

**(T2) Moduli rigidity.** For every F in the essential image of R_B, Mod_B(F) is contractible. Outside the essential image it is empty. For a non-dense probe family, non-contractible fibres encode exactly the residual ambiguity up to the equivalence relation represented by the core.

**(T3) Grounding soundness.** An independently defined realization structure assigns operational systems/physical realizers to semantic models. If the realization satisfies the specified intervention-commutation, observation-calibration, counterfactual-stability and correction conditions, then semantic equivalences transport the operationally testable semantic signature. These conditions must not include “the model is true” as a premise.

**(T4) Truth/evidence separation.** Satisfaction/truth, warranted assertion, evidence availability, evidence soundness, evidence completeness and defeasibility are distinct indexed structures. The theory proves exactly which are preserved by each morphism/update; it never infers truth from warrant or completeness from soundness without additional hypotheses.

**(T5) Contextual descent.** If the context-indexed semantic assignment satisfies the stated descent condition (sheaf condition for set-valued truncations; stack/higher descent for space-valued assignments), compatible local semantic data glue to global data, uniquely up to contractible coherent choice. When descent fails, the obstruction is represented, not erased.

**(T6) Resource monotonicity.** For B ≤ C, restriction of richer profiles to poorer profiles induces a comparison between moduli spaces. Under explicit compactness/finite-type or probabilistic assumptions, increasing B cannot increase the set of observationally indistinguishable completions; quantitative rates require additional metric/statistical structure and are not implied by category theory alone.

**(T7) Cross-theory adequacy.** For each independently selected theory T_i in Τ, there is a structure-preserving interpretation J_i into the grounded semantic framework. The family {J_i} is jointly conservative for the declared signature Σ: if a Σ-claim is validated in the common framework, it is validated in each source theory under the interpretation, and source-theoretic distinctions relevant to Σ are not collapsed. Any failure of conservative interpretation is a limitation or no-go result, not to be patched by weakening the source theory silently.

**Conclusion (conditional):** The framework is a universal semantic representation for the declared class Τ and signature Σ, with exact reconstruction where probes are dense, explicit ambiguity where they are not, operationally grounded reference/truth tests, coherent contextual composition, and conservative translations of the included semantic theories.

## 4. Hypotheses and epistemic status

- H1 (formal): $\mathcal{C}$, $\mathcal{M}_{\mathrm{adm}}$, probe functors and size conditions form the required locally small/small ∞-categorical objects in chosen universes.
- H2 (formal): probe inclusion is dense. This is not automatically true and must be proved for a concrete probe-generation scheme.
- H3 (operational): admissibility tests are independently specified and reproducible; their calibration is an empirical/methodological premise, not a theorem of category theory.
- H4 (causal): interventions are well-defined and realization commutes with them to the extent required. This is domain-specific and must be validated.
- H5 (contextual): the assignment satisfies the appropriate descent condition. This is a substantive gluing premise.
- H6 (cross-theoretic): each interpretation exists and is conservative for Σ. This is likely to hold only for a restricted signature and selected theories.
- H7 (resource): finite-budget comparison uses an explicit order/metric/probability model. Mere inclusion of probe classes proves only a qualitative restriction relation.

## 5. Immediate no-go results / falsifiers

1. **Unobservable referent:** two systems have identical outputs under every available probe but refer to distinct external targets. Then the profile cannot identify reference; the framework must report ambiguity.
2. **Truth-predicate stipulation:** two models share syntax/reference but disagree on satisfaction. If the framework selects one without an independent operational test, adequacy is circular.
3. **Non-dense probes:** if there exists a semantic distinction not detected by any probe, full faithfulness fails. Any claimed reconstruction is false or its probe category is underspecified.
4. **Non-gluing contexts:** locally compatible meanings fail to admit a global section. A sheaf-only treatment is inadequate; a stack may retain coherence, but cannot guarantee existence without descent hypotheses.
5. **Incompatible source theories:** a translation that preserves classical model-theoretic truth may fail to preserve inferential warrant or pragmatic success. Joint conservativity may fail for an overstrong signature.
6. **Resource impossibility:** distinct systems may be computationally indistinguishable below B even if distinguishable in principle. Finite-budget semantics must preserve this ambiguity.

## 6. Proof obligations, in dependency order

P0: Fix precise definitions of $\mathcal{C}$, $\mathcal{M}_{\mathrm{adm}}$, probes and the operational signature. Eliminate circularity before proving reconstruction.
P1: State and prove the ∞-categorical restricted Yoneda/density theorem, with mapping-space full faithfulness and universe bookkeeping.
P2: Derive the moduli-fibre result from P1, carefully distinguishing core/homotopy fibre from ordinary categorical fibre.
P3: Define realization as a functor/relation to an operational category and prove intervention/observation commutation results.
P4: Prove finite-budget non-identifiability theorems and quantitative bounds only under explicit assumptions.
P5: Define a context site and prove descent/stackification results, including obstruction examples.
P6: Construct and test conservative translations for selected semantic theories.
P7: Apply the full package to graph-gauge and other non-linguistic cases, preserving isotropy and higher coherence.

## 7. Current status

- Strict 1-groupoid reconstruction/moduli results: formalized in Lean.
- Posetal/resource-envelope shadow: formalized in Lean.
- Grounded model category with reference, satisfaction, evidence and soundness: formalized in Lean at an ordinary categorical level; truth/evidence preservation and countermodels verified.
- Genuine space-valued ∞-categorical theorem: not yet formalized/proved in Lean.
- Independent causal realization and operational density: incomplete.
- Contextual descent/stack theorem: incomplete.
- Joint conservative translations across semantic theories: not established.
- Thus T1/T2 have standard higher-categorical proof routes; T3–T7 are the substantive open frontier. The conditional conclusion is not yet licensed.

## 8. Research discipline

Do not call the theorem “proved” until all component statements have exact definitions and verified proofs. Do not call the framework “universal” until Τ and Σ are explicit and the conservativity claim is demonstrated. If no-go results show that a broad universality claim is impossible, narrow the scope transparently rather than redefine semantics to evade the counterexample.

## 9. Prior-art correction and architectural revision

Institution theory already supplies a mature framework for signatures, sentences, models, satisfaction, invariance under notation changes, and truth-preserving translations between logics (Goguen & Burstall 1992, DOI 10.1145/147508.147524). Sheaf-theoretic contextuality already models local empirical assignments and global-section obstructions (Abramsky & Brandenburger 2011, arXiv:1102.0264). Lawvere hyperdoctrines already formalize indexed propositions, substitution and quantification.

Therefore T5 and T7 cannot be presented as novel merely because we add descent or cross-theory translations. They should be treated as foundations/constraints. The target contribution, if any, is a compatibility and adequacy theorem that joins:

1. institution-like indexed syntax/model/satisfaction structures;
2. an operational context site with empirical presheaves and possible contextuality obstructions;
3. a causal realization relation whose tests are independently specified;
4. evidence and warrant structures distinct from truth;
5. resource-indexed higher probe profiles and moduli of candidate realizers;
6. higher equivalence and isotropy data.

The central compatibility square must say precisely when satisfaction is invariant under theory translations, when realization commutes with interventions, and how local empirical evidence lifts to or obstructs global semantic realizations. The framework must permit nonexistence of global sections; sheafification cannot be used to erase empirical contextuality.

Revised T7: construct interpretations from selected institutions/semantic theories into the proposed higher operational framework and prove conservativity only for a declared signature. Institution morphisms/comorphisms already provide the basic truth-preserving translation concept. The new burden is to show that the translations also preserve operational realization, resource-indexed moduli, evidence/warrant distinctions and relevant higher automorphisms. If these additional invariants cannot be jointly preserved, report the incompatibility.

Revised T5: use sheaf/stack descent only when the empirical/contextual system satisfies the relevant gluing condition. Otherwise represent the obstruction (e.g. via contextuality witnesses or cohomological classes) as semantic data.

This revision is mandatory for any novelty or universality claim.

## 10. Peircean adequacy constraint

The minimal triadic model added to Lean is not yet a sufficient Peircean semantic object. Alrøe (2025), “The six types of sign action,” *Semiotica* 2025(266), DOI 10.1515/sem-2024-0112, distinguishes representation from temporal mediation; separates immediate and dynamical objects; distinguishes immediate, dynamical and final interpretants; and proposes six sign-action directions. The paper also identifies the non-homuncular interpreter problem in biosemiotics as unresolved.

Accordingly, a defensible candidate semantics should not identify a ternary representation relation with its causal process. It should contain both, coupled by explicit compatibility laws. It should keep the dynamical object operationally independent from the immediate object represented in the sign, and should not reduce the final interpretant to an ordinary next-state transition. The present Lean triadic model is a first formal placeholder only.

## 11. Revised strict categorical core

The more appropriate base is the existing relational `GroundedSemiosis` schema, not the simpler functional-reference prototype. The new `GroundedSemiosisCategory.lean` defines structure-preserving maps that separately preserve/reflect aboutness (`refers`), context-indexed claim expression, satisfaction, and transport evidence. It proves content truth, reference, grounded assertion truth, and evidence soundness transfer.

The new `TriadicRelationalSemiosis.lean` extends this exact schema with a ternary sign–world–interpretant relation and interpretant-to-next-sign continuation. Its morphisms preserve/reflect the ternary relation and commute with continuation. The transport theorems are axiom-free; the all-probe reconstruction uses only standard `Quot.sound`.

This is the strongest current strict categorical base because it does not force reference to be a function or collapse content satisfaction into grounded assertion truth. It remains a formal structure, not an independently validated empirical theory. In particular, its triadic relation still needs sign-establishment/memory dynamics and immediate/dynamical/final interpretant distinctions before it can claim Peircean adequacy.

## 12. Operational reference construction now formalized

The intervention-grounding development supplies a concrete operational referent space. For an operational scaffold S, intervention protocol P and budget B, define world equivalence by equality of all affordable intervention-response traces:
$$
w \sim_B w' \iff \forall a\,(\operatorname{cost}_P(a) \le B \Rightarrow \operatorname{trace}_S(w, a) = \operatorname{trace}_S(w', a)).
$$
The referent space is the quotient (W/{sim_B}). A sign s operationally refers to a quotient class q when some representative world w in q produces s. This reference relation is intentionally not assumed functional: one observed sign can be compatible with multiple referent classes.

Lean modules `InterventionGrounding.lean` and `OperationalReference.lean` prove a finite example in which two hidden worlds are one referent class at budget 0 but split into distinct classes at budget 1; the same current sign is related to both classes at the richer budget. They also prove monotone forgetting from a richer referent space to a coarser one and preservation of the operational-reference relation under that map.

This provides a non-truth-conditional and non-functional operational notion of reference. It is a candidate semantics for *identifiability under a declared intervention language*, not a metaphysical identity criterion. Its adequacy depends on independent calibration of the sensor/intervention protocol and on whether the selected interventions are appropriate for the target domain.

The definitive theorem should combine this operational quotient with the grounded institution/triadic category and its higher profile moduli. In particular, the operational referent quotient is only the object-level 0-truncation of the richer moduli of systems; it does not preserve all transformations, automorphisms or higher paths.


## 8. Adequacy obstruction now formalized (2026-11-23)

The first anti-circularity theorem package is machine-checked in `GroundingAdequacy.lean`.

For each budget B, observational equivalence is the kernel of the complete affordable response profile. The external referent map descends to the observational quotient exactly when it is constant on those equivalence classes; an external truth predicate descends exactly when it is invariant there. Conversely, if two observationally equivalent histories have distinct external referents, every profile-only decoder necessarily gives them the same output and therefore cannot recover both.

This yields a necessary adequacy condition for any proposed universal semantic reconstruction: **the operational probe signature must separate every externally meaningful distinction that the theory claims to reconstruct**. If it does not, the moduli object must retain multiple possible referents/truth assignments rather than collapse them.

The result does not prove the probes adequate, nor does it identify the correct external target. It makes those premises independently falsifiable. The finite Boolean intervention example verifies the predicted budget transition: ambiguity at B=0, separation at B=1.

Formal verification: focused Lake builds pass. Axiom audit reports only standard `Quot.sound` and `propext`; no project-specific axioms or `sorryAx`.


## 9. Operational calibration interface

The external grounding premise is now given a typed form in `OperationalGroundingAdequacy.lean`. An operational system and an external target are distinct types. A realization relation links them; an internal response function and external response function are separately specified; calibration states that realized systems reproduce external probe responses. A budget-indexed separation hypothesis requires every pair of distinct external targets to be distinguished by some affordable probe.

Under calibration and separation, equal internal response profiles force equality of external referents. If separation fails, a pair of distinct external targets agreeing on all affordable probes exists. The theorem therefore gives both a sufficient condition for grounded reference and an explicit failure witness. It is conditional on independent calibration/separation and does not derive them from syntax or from the target category.


## 10. Object-level embedding versus full faithfulness

The external profile map `ExternalProfileAt_B` is now formally injective exactly when affordable external probes separate distinct targets. Calibration identifies internal system profiles with external profiles, yielding unique external reference from profile equality. This is an object-level embedding criterion only. It must not be advertised as full faithfulness: morphism-level reflection and preservation (and, in the higher case, mapping-space equivalence) remain separate proof obligations.


## 11. Grounded relative-density equivalence (strict 1-category)

The strict categorical core now has a machine-checked adequacy equivalence. Let E be the external category, C the operational category, R : E → C the realization functor, and P the operational probes. If the probe-incidence cocone is a colimit for each pair of realized objects, then R is fully faithful exactly when the induced response-profile representation is fully faithful. This is a relative-density condition on the realized image, not global density of every operational object.

The reverse implication matters: with relatively dense probes, a profile-level full-faithfulness claim cannot conceal a non-faithful realization functor. The empty-probe Bool counterexample demonstrates the failure when relative density is absent. This closes the strict 1-categorical morphism-level criterion, but it does not yet supply bicategorical pseudonaturality or `(∞,1)`-categorical mapping-space equivalences.


## 12. Higher-categorical target and moduli-fiber qualification

For locally small `(∞,1)`-categories E and C, a realization functor R:E→C, and a small full probe subcategory i:P↪C, define `N_P(c)(p)=Map_C(i(p),c)` in spaces. If each realized object R(x) is the weighted colimit of its canonical probe-incidence diagram,

`∫^{p∈P} Map_C(i(p),R(x)) ⊗ i(p) ≃ R(x)`,

then the restricted higher-Yoneda map on mapping spaces between realized objects is an equivalence. Hence `N_P∘R` is fully faithful iff R is fully faithful. The resulting homotopy fiber over an in-image profile is contractible on maximal subgroupoids.

This is the intended higher lift of the Lean-verified strict 1-category theorem. It is **not yet proved or formalized** here. It requires homotopy-coherent natural transformations, mapping spaces, weighted colimits, and universe/size control. Do not conflate this fiber with the core of the unrestricted category of all extensions: the Kan-envelope retract counterexample in the GHSRT dossier refutes that stronger claim.


## 13. Strict groupoid moduli fiber is now Lean-verified

`GroundedModuliFiber.lean` upgrades the relative-density result to a groupoid-level construction. Under a fully faithful external realization and relative probe density on the realized image, the external groupoid is equivalent to the groupoid of operational response profiles. Every fiber over an in-image profile is contractible in the strict 1-groupoid sense: it has an object, and every pair of fiber points has exactly one compatible arrow.

A finite example proves that relative density is genuinely weaker than global density: one probe is insufficient for the entire two-object operational category, yet sufficient on the realized one-object subcategory. Its grounded profile moduli fiber is contractible. The groupoid theorem's axiom audit uses only `Quot.sound`; the finite non-global-density counterexample is axiom-free.

The `(∞,1)`-categorical extension remains open. In particular, this theorem does not establish contractibility of arbitrary extension categories or their cores.


## 14. Reference, syntax, truth, and evidence now transport together

`GroundedSemiosisTransport.lean` forms the quotient of external targets by equality of affordable operational profiles. When the probes separate external targets, this quotient is equivalent to the original target type. A full `GroundedSemiosis` structure can then be transported to profile space while preserving relational reference, expression, satisfaction, evidence, and evidence soundness. This is a structural transport theorem, not an assertion that evidence is complete: truth and evidential support remain distinct predicates.


## 15. Quotient semantics avoids arbitrary representative choice

The profile-world semantics is now defined as the quotient of external targets by equality of their affordable response profiles. Under probe separation, quotient recursion recovers the unique external target. This makes the semiosis transport independent of a chosen representative and carries reference, expression, satisfaction, evidence, and evidence soundness into profile space. A finite hidden-bit example verifies that a true grounded assertion remains true while evidence remains absent.


### 13.1 Canonical composition check

The grounded profile groupoid's composition is now formally shown to equal pointwise composition of natural transformations (`profileCompose_is_pointwise`). The groupoid is therefore the canonical profile groupoid transported through the reconstruction equivalence, not a groupoid with an ad hoc operation. Its axiom audit uses only `Quot.sound`.

## 16. External observational gauge freedom and independent anchors

A new no-go result closes an important circularity gap. Any external relabelling that preserves all probe responses leaves the complete profile unchanged at every budget. Calibration is invariant under reindexing the realization relation by that relabelling. Thus no internal reconstruction theorem can determine which member of an observationally indistinguishable external class is the intended referent.

The hidden-coordinate countermodel makes the obstruction concrete: a perfectly calibrated system probes only coordinate one of a two-coordinate external target; coordinate two, and any truth predicate depending on it, remain unidentifiable at every budget. Increasing resources cannot repair a missing probe direction.

An independent anchor need only separate the residual ambiguities left by the operational profile. The combined profile-plus-anchor is injective iff the anchor separates every pair with equal operational profiles. This is a necessary-and-sufficient criterion, not a claim that a valid anchor has already been empirically supplied.


A further no-go theorem rules out profile-derived pseudo-anchors: any anchor computed solely as a function of the operational response profile is constant on each profile-equivalence class and cannot resolve a pre-existing ambiguity. Independent grounding must add genuinely new information, not merely transform existing observations.

## 17. Causal anchor fusion

A second operational channel resolves an ambiguity left by the first precisely when the intersection of their profile kernels becomes trivial. This is formalized as a necessary-and-sufficient criterion, with a complementary two-coordinate example where neither channel alone identifies the target but the joint profile does.

The stronger causal construction defines experiments by an initialisation map, apparatus state, observation function, intervention transition, and resource cost. Response profiles are generated by intervention traces. A two-stage apparatus initially reads one coordinate and, after one intervention, exposes the other. The target is not identifiable at budget zero but is identifiable at budget one.

This is not yet empirical grounding: the physical validity and independent calibration of the apparatus transition/observation model remain assumptions to be established. The formal result isolates exactly where that empirical bridge enters.
