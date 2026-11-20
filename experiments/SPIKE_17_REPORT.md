# Spike 17 — Distinction admissibility, identity, and controlled contraction

**Status:** initial formal core passes Lean 4.12.0 CI and axiom audit; finite Python demonstrator passes.  
**Date:** 2026-11-20  
**Branch:** `research/distinction-calculus-2026-11-20`  
**Pull request:** https://github.com/outdatedcaveman/semplex/pull/4

## Question

Can identity, substitution, contraction, quotienting, and context-sensitive equivalence be compared through one preservation calculus without erasing the differences among classical first-order logic, linear logic, dependent type theory, and Synesism-inspired contextual semantics?

## Prior-art gate

The relevant mathematics is established: quotient factorization and congruence for induced operations; classical equality and substitutivity; linear logic's restriction of weakening/contraction and exponential modalities; Martin-Löf identity types and path induction; fibrations/indexed categories as categorical semantics of substitution; and matching-family/descent ideas for gluing local data.

The proposed Semplex contribution is an integration into protocol-relative preservation and CSIR/certificate architecture. No claim of new mathematics is made. See `research/SPIKE_17_PRIOR_ART_AND_POSITIONING.md`.

## Formal core

For T : X -> Y and protected query q : X -> A:

    Preserves(T,q) := for all x,x', T(x)=T(x') implies q(x)=q(x').

This is equivalent to q factoring through the image of T. For quotient relation R, a query descends iff constant on R-classes. An operation descends only if R is a congruence for that operation.

The Lean development now packages this as a typed protected-interface contract:
- a declared family of observations, with potentially different result types;
- declared total unary operations;
- declared total binary operations;
- a setoid relation R;
- proof obligations that observations are constant and operations are congruent on R.

Under that contract, every protected observation and operation descends to the quotient. The binary quotient-operation fragment also proves the converse: any quotient operation commuting with the quotient map forces congruence.

This is a scoped schema for exact quotients and total deterministic operations, not a universal axiom for arbitrary transformations.

## Four-system demonstrator

| System | Formal fragment | Result and boundary |
|---|---|---|
| Classical FOL | Recursive syntax/semantics with variables, constants, equality, unary predicates, falsity, implication, and universal quantification | Lean proves satisfaction depends only on the assignment restricted to free variables. The syntax is a small fragment, not full FOL. |
| Linear/resource logic | Natural-number linear resource count plus a Boolean persistent-use permission | Lean proves a contraction counterexample and safe cases. This is a resource semantics fragment, not a complete linear-logic sequent calculus or full exponential modality. |
| Dependent type theory | Lean identity type Eq, reflexivity, and equality elimination | Substitution follows by identity elimination. This is not a full Martin-Löf type theory or HoTT development. |
| Contextual/fibrational semantics | Two-object context preorder; discrete fibers Bool and Bool × Bool; Grothendieck total category | Lean proves reindexing laws, category laws, cartesian factorization, and cleavage coherence. This is a standard small set-valued fibration, not a new construction. |

## Synesism source reconciliation and dyadic conservation

The connected Synesism sources sharpen the theory materially. The older Definitions and Premises explicitly distinguishes equal semonic value from structural equality: one zeroth-order semon and two first-order sema can have the same aggregate value while differing in mappings and properties. The Systems chapter identifies the synod as a system's invariant/identity element and requires semonic value preservation under coherent transformations. The Syneces chapter describes syneces as relations/morphisms and logic as semonic-preserving entailment. Newer topic notes define modules as partial, contingent reality-slices arising from interactions and fitness functions, and distinguish internal semonic value from external contextual fitness.

`SynesismConservation.lean` now formalizes the binary dyadic example: one parent profile and two first-order offspring profiles have equal aggregate molarity; each child has half the parent's value; binary partition preserves value while changing order/configuration; and a system state can evolve coherently while retaining its synod anchor. The cross-multiplication relation is proved reflexive, symmetric, and transitive on dyadic profiles. Crucially, order and multiplicity are not constant on its equivalence classes, so quotienting by molarity alone cannot preserve those structural observables. This is an explicit toy model of the source's example, not a general definition of molarity. The 2025 *On identity* note also questions numerical identity for differentiated beings and emphasizes relational individuation, creating a tension with the older synod-as-system-identity formulation. The source also uses “module” in two different senses across the older Definitions and newer topic note; these meanings are kept separate in `research/SYNESISM_IDENTITY_MODULE_RECONCILIATION.md`. The connected workspace did not surface an explicit P8 page; the earlier P8 paraphrase remains unverified.

The generic `SmallFibration.lean` and `ModuleDescent.lean` remain scaffolds only. They do not yet formalize modules as fitness-indexed partial reality-slices or prove that Synesism's module family satisfies descent. See `research/SYNESISM_IDENTITY_MODULE_RECONCILIATION.md` and `research/SYNESISM_MODULE_SEMANTICS_DESIGN.md` for the source-grounded correction and candidate semantics.

## Tarski, names, and existential import

The slide's assignment-invariance result is mechanized: satisfaction depends only on values assigned to free variables. A formula-relative quotient of assignments therefore preserves satisfaction for that formula, but may fail to preserve another formula that reads a discarded coordinate.

The syntax distinguishes variables (interpreted by assignments) from constants (interpreted by the structure). A constant's denotation supplies a witness for an existential statement. The universal-to-existential inference is proved with an explicit nonempty-domain witness; an empty-domain countermodel shows why nonemptiness is required if empty domains are admitted. This does not make a name token an ontological generator: the inference depends on signature, interpretation, domain convention, and proof rules.

Fresh eigenparameters and full natural-deduction side conditions are not yet formalized.

## Module identity and gluing

`SmallFibration.lean` is a two-context indexed family: a coarse context sees one Boolean coordinate; a refined context sees two. Reindexing forgets the second coordinate. Its Grothendieck construction has discrete fibers and cartesian lifts with a unique factorization property.

`ModuleDescent.lean` adds a separate finite overlap example:
- Module A sees (x,z);
- Module B sees (y,z);
- the overlap sees z;
- local sections glue iff their overlap coordinates agree;
- the resulting global (x,y,z) profile is unique;
- incompatible local profiles have no global amalgamation.

This is a finite matching-family/sheaf-style example, not a general sheaf theorem and not a proof that Synesism's P8 modules satisfy descent. It gives us a concrete mathematical test for what cross-module coherence would have to mean.

## Verification

**CI passed.** Lean 4.12.0 compile and axiom-audit jobs both passed, and the finite Python test suite passed **9/9**.

CI run: https://github.com/outdatedcaveman/semplex/actions/runs/44693971714

The axiom audit reports only:
- `propext` for some extensionality/equality-of-propositions results;
- `Quot.sound` for quotient construction/descent results.

No audited theorem depends on `sorryAx`, `Classical.choice`, or an unapproved custom axiom. The use of `Quot.sound` is expected for Lean's quotient primitive; it is not an extra research axiom.

The verification covers:
- `Distinction.lean` and `AuditDistinction.lean`;
- `SynesismConservation.lean` and `AuditSynesismConservation.lean` (dyadic partition/value conservation, non-identity, and synod-anchored coherent evolution);
- `SmallFibration.lean` and `AuditFibration.lean`;
- `ModuleDescent.lean` and `AuditModuleDescent.lean`;
- the finite Python reference model and nine adversarial tests.

The repository test harness `tests/test_lean.py` also compiles these modules and checks their axiom outputs when Lean 4.12.0 is available.

## Findings

1. **DAP is a typed contract schema, not a universal axiom.** It must declare the observations and operations to be protected. For quotienting, the observation condition is constancy on equivalence classes; the operation condition is congruence.
2. **Identity, substitution, and contraction remain distinct.** The shared preservation calculus can state admissibility obligations, but does not derive all three without assumptions encoding identity, congruence, or resource permissions.
3. **Names carry inferential commitments through their semantics.** Variables, interpreted constants, and fresh proof parameters have different roles. The slide's existential import uses nonempty-domain semantics or a witness term/parameter. Lean now proves semantic soundness of ∀-introduction and ∃-elimination under explicit eigenvariable freshness conditions.
4. **Molarity-equivalence is not identity.** Even when the dyadic value relation is a genuine equivalence relation, order and multiplicity do not descend through its quotient. This is a direct DAP counterexample to treating equal semonic value as structural identity.
5. **Module-relative descriptions have a concrete gluing test.** Local profiles can be assembled only when overlap restrictions agree. This is a generic matching-family example, not yet a derivation from Synesism's module ontology.
6. **Occurrence-sensitive contraction is more precise than the original Boolean flag.** Two persistent occurrences of the same formula can be merged without changing resource support at any finite demand, while merging two distinct linear occurrences destroys support for a two-use demand. The merged token records both provenance trails. This is still a small capacity semantics, not full linear logic.\n7. **No novelty claim is warranted.** Quotient descent, congruence, free-variable invariance, linear contraction control, identity types, Grothendieck fibrations, and finite gluing are established mathematics. The possible value is the typed integration with PFT and CSIR, which still needs comparative evaluation.

## Kill criteria / unresolved work

- If DAP cannot distinguish a safe quotient from one that breaks a protected operation, revise or reject it.
- If the contextual/fibrational model is only ordinary observational equivalence with renamed terminology, do not claim a new fibration or new mathematics.
- If P1's true/phenomenological distinction cannot be made precise without contradiction, record the conflict for reconciliation rather than changing canon.
- If the P8 module structure does not supply the base morphisms, restrictions, and overlap data required for descent, do not impose sheaf language on it.
- Before novelty claims, compare against setoids, quotient algebras, linear logic, categorical logic, contextual equivalence, fibrations, and descent.

## Next work

1. Formalize the source's relative molarity beyond the binary dyadic example, including its algebraic laws and relation to configuration/scheme.
2. Formalize system identity through a synod invariant and the Principle of Coherence, distinguishing full logics from quasilogics.
3. Extend modules to fitness-indexed partial reality-slices with an explicit reality-share/overlap measure; do not assume the generic fibration is already that semantics.
4. Extend the protected interface from total unary/binary operations to typed partial, stateful, effectful, stochastic, and higher-order operations only where Semplex fragments require them.
5. Generalize the finite overlap model to multiple modules/covers and explicit transition maps; derive the exact descent conditions and test them against the available Synesism module definitions.
6. Replace the toy Boolean persistent flag with occurrence-sensitive resource contexts, explicit copy permissions, and provenance-aware judgments; compare directly with linear logic's exponential rules.
8. The FOL fragment now includes ∃ and machine-checked eigenvariable soundness for ∀-introduction and ∃-elimination. Complete a syntax-directed comparison of all four systems, with occurrence-sensitive linear contexts and explicit structural rules.
8. Design a CSIR transformation/certificate representation only after at least three existing fragments need the same typed preservation and loss-accounting fields.
9. Continue the literature and novelty audit before any paper-level claim.
