# Distinction Calculus: identity, contraction, and admissible loss

**Status:** research proposal / not yet a theorem / not a Synesism canon amendment  
**Target:** Semplex (CERP), extending CSIR and Protocol-Frame Theory  
**Branch:** `research/distinction-calculus`  
**Synesism relation:** candidate formal bridge to P0–P2, P5, P7, P8; any metaphysical promotion remains subject to Bruno's explicit approval.

## 1. Research question

Can identity, reference, inference, abstraction, and computation be described as typed operations over distinctions, with explicit conditions governing when distinctions may be introduced, preserved, reused, identified, duplicated, or eliminated?

The proposal is not that every distinction is a physical resource, nor that all identity is reducible to information. It is that formal systems should expose the commitments and preservation conditions hidden inside operations such as naming, substitution, contraction, quotienting, and abstraction.

**Working thesis (conjectural):** a transformation that identifies or removes distinctions is admissible relative to a protected family of observations, queries, and operations exactly when the semantic content those observers can access is preserved (or is preserved up to an explicitly declared refinement/approximation). Where future operations are not known, no task-relative quotient can be called globally lossless.

## 2. Why this belongs in Semplex

Semplex already has:
- Protocol-Frame Theory (PFT): a frame `(H, P, obs)`, observational powers `Ω`, and protocol-indexed indistinguishability.
- The Galois connection between observational power and indistinguishability.
- Canonical factorization: an `Ω`-determined query factors through the `Ω`-profile.
- Task-relative sufficiency, equivalence, proof certificates, and a structured warrant ledger.
- CSIR v0.1: bundles of artifact nodes and protocol-relative, warranted, certifiable links.

The proposed calculus should be a theory layer over these existing results, not a competing ontology or a replacement for PFT. The key bridge is:

> A quotient is not simply a declaration that two things are identical. It is a representation change that forgets distinctions. Its legitimacy is relative to what must remain observable, answerable, executable, or reconstructible.

This makes the CSIR link—not a globally privileged canonical node—the natural place to record the result.

## 3. Typed distinctions: do not conflate these

The formalization must keep at least the following types separate.

1. **Entity:** an element of a domain/model.
2. **Occurrence:** a particular use or token of an entity, proposition, assumption, or evidence item.
3. **Name/reference:** a syntactic handle with a denotation or interpretation, possibly partial or context-dependent.
4. **Observation profile:** the outputs available under a declared protocol family.
5. **Equivalence:** a relation between entities or artifacts, indexed by protocol/task/context.
6. **Identification/quotient:** a map that replaces multiple representatives with one abstract representative.
7. **Inferential permission:** a rule licensing substitution, instantiation, generalization, duplication, discharge, or reuse.
8. **Resource:** a typed, measured or logical quantity (evidence multiplicity, assumptions, time, memory, energy, communication, etc.).
9. **Operation:** a transformation on entities, occurrences, contexts, or artifacts.

An equality between entities does not automatically identify their occurrences. Two occurrences of the same proposition need not be one evidence token. Two names may co-refer without being interchangeable in every intensional or opaque context. A quotient equivalence need not be a congruence for every operation.

## 4. Core mathematical objects

### 4.1 Protocol-relative indistinguishability

Retain PFT's definition. For frame `F = (H, P, obs)` and observational power `Ω ⊆ P`:

```
h ≡_Ω h'  iff  for every p ∈ Ω, obs(p,h) = obs(p,h').
```

This is an equivalence relation. Increasing observational power refines indistinguishability.

### 4.2 Protected signature

Let `Q` be a declared family of queries/observables that a transformation promises to preserve. Let `≈` be the equivalence used for quotienting.

A query `q : H → A` is preserved by the quotient iff it is constant on equivalence classes:

```
Preserved(q, ≈) := ∀ x y, x ≈ y → q(x) = q(y).
```

Equivalently, there exists a factor `q̄ : H/≈ → A` such that `q = q̄ ∘ quotient`, subject to the chosen quotient construction.

For a family `Q`, preservation is pointwise for every `q ∈ Q`.

This is the first formal meaning of **admissible distinction loss**. PFT Theorem 10 already supplies the factorization pattern for the Ω-profile. The new work is to generalize it from observational profiles to arbitrary declared protected interfaces and to transformations/operations.

### 4.3 Operation congruence

Preserving current observations is not enough if later operations must remain well-defined.

For an n-ary operation `f : H^n → H`, an equivalence `≈` is a congruence iff:

```
x₁ ≈ y₁ ∧ ... ∧ xₙ ≈ yₙ  ⇒  f(x₁,...,xₙ) ≈ f(y₁,...,yₙ).
```

A quotient supports a well-defined induced operation only when the relevant congruence condition holds. This is a crucial test: a quotient may preserve present answers but fail to preserve future computation.

For partial, stochastic, causal, stateful, or higher-order operations, define the corresponding typed preservation condition rather than forcing this simple deterministic schema.

### 4.4 Distinction-loss certificate

A proposed identification/abstraction should carry:
- source domain/artifact and target quotient/abstraction;
- equivalence relation and its scope;
- protected protocol/query/operation family;
- preservation proof or certificate;
- declared non-preserved distinctions;
- resource and cost model, where relevant;
- warrant, trusted base, assumptions, and limitations;
- reversibility/reconstruction status.

A certificate must not claim global losslessness when it proves only task- or protocol-relative preservation.

## 5. Controlled contraction: a separate operation

Do not define contraction as equality.

In sequent calculus, contraction changes the multiplicity of assumption occurrences. For example:

```
Γ, A, A ⊢ B
----------------  contraction
Γ, A ⊢ B
```

This does not identify two objects denoted by A. It licenses treating two occurrences of an assumption as one for a derivation.

The calculus must distinguish:
- **propositional identity:** both occurrences have the same content;
- **token identity:** both occurrences are literally the same resource token;
- **duplicability:** a token may be copied without changing the modeled resource state;
- **contractibility:** multiple occurrences may be merged without invalidating the target judgment;
- **discardability/weakening:** an occurrence may be unused;
- **substitution:** one term/reference may replace another in a specified context.

Linear logic is a key comparator because it separates unrestricted assumptions from resources whose multiplicity matters. The exponential modality `!` is a candidate formal mechanism for controlled duplicability, but it must not be assumed to solve all forms of contraction.

For evidence, observations, measurements, and causal samples, equal content does not imply duplicate provenance or statistical independence. The resource model must preserve token multiplicity and provenance when they affect warrant.

## 6. Identity: working answer and levels

The question "is identity fundamental?" is ill-posed until the kind and level of identity are specified.

Distinguish:
- **Metalogical identity:** the equality relation used by the chosen foundation.
- **Object identity:** sameness of an entity within an ontology.
- **Type identity:** equality/paths between types or structures.
- **Structural equivalence:** isomorphism, equivalence, bisimulation, or another declared relation.
- **Observational identity:** indistinguishability under a protocol family.
- **Occurrence identity:** sameness of a token/use/evidence item.
- **Phenomenological identity:** persistence of an ordinary object across changing modules and contexts.

Preliminary philosophical position: identity need not be a single, context-free metaphysical primitive for every level. But no formal foundation gets to eliminate identity-like structure for free. If primitive equality is removed, its work reappears in equivalence, congruence, substitution rules, transport, or invariance conditions.

For Synesism specifically, do not rewrite the canon. P0 is Univocity, not the equation that all beings are equal. P1 distinguishes true identity/indiscernibility (fully realized only in Semes) from phenomenological, modular, approximate identity of ordinary quasiobjects. The extension should test whether the latter can be modeled as stable, context-indexed profiles/relations, while P0 remains the metaphysical premise and P1's exact formal reading remains an obligation.

## 7. Synesism interface (candidate mapping, not canon)

- **P0 Univocity:** all distinctions are internal articulations of the One; no external ontological domain. This does not collapse the Many into featureless sameness.
- **P1 Unicity:** identity/indiscernibility must be formalized with the canon's distinction between true and phenomenological identity.
- **P2 Coherence:** relations/syneces are constitutive; candidate structures should be relation-first where appropriate, not assume independently self-sufficient relata.
- **P5 Multiplicity:** partition and conjoinment are co-equal operations. The calculus must model both differentiation and fusion; they are not inverse functions.
- **P7 Stratification:** totalities and their elements may inhabit different levels. Quotients, universes, and self-reference need explicit level discipline.
- **P8 Modularity:** an ordinary being accesses a partial reality-slice. Identity and equivalence may therefore be module-/protocol-relative without making every perspective equally adequate.

No result in Semplex by itself proves P0 or any metaphysical claim. Formal results can establish conditional consequences of explicit structures and assumptions.

## 8. Relationship to the CSIR

Do not immediately break CSIR v0.1 or silently mutate its schema. First test an extension in a separate module and export it as ordinary CSIR artifacts/links.

Candidate new link relations:
- `identifies-under`: a declared identification under a protocol/context;
- `quotient-of`: a quotient map with its equivalence and certificate;
- `preserves-query`: a query/interface factors through a transformation;
- `congruence-for`: an equivalence is compatible with a declared operation;
- `contracts`: a proof-context transformation with occurrence-level provenance;
- `refines` / `reconstructs`: explicit relations between coarser and finer representations.

These are proposals. Their relation order and composition rules must be derived and tested, not guessed. Some are not equivalence relations and should not be inserted into the existing equivalence inclusion registry.

A future CSIR version should represent **transformations as first-class artifacts**, not merely links, if certificates need executable source/target maps, kernels, or reconstruction procedures.

## 9. Candidate formal propositions

P1. **Factorization criterion.** A query is preserved by a quotient iff it is constant on the quotient's equivalence classes.

P2. **Congruence criterion.** An operation descends to a quotient iff the quotient equivalence is a congruence for that operation (state exact assumptions and proof).

P3. **No free contraction.** Equality of proposition content alone does not entail admissible contraction when occurrence multiplicity/provenance is semantically relevant. Construct a countermodel.

P4. **Contextual contractibility.** Contraction is admissible relative to a judgment family iff merging occurrences preserves every protected judgment under the declared semantics. Determine useful sufficient conditions and decidable fragments.

P5. **Information monotonicity.** A coarsening of observational power cannot increase the set of queries determined. This is already a PFT consequence; use it as a baseline, not a novelty claim.

P6. **Future-operation obstruction.** A quotient may preserve a current query family but fail to preserve a later operation that is not congruent with the quotient. Produce a minimal counterexample and a certificate of failure.

P7. **No universal canonical representative.** Distinction-preserving quotients can have multiple representatives/normal forms, or no computable canonical syntax in the general case. Keep this separate from existence of an abstract quotient object.

## 10. Identity and the foundations question

The project should compare three positions, without presupposing the winner:

1. **Identity primitive:** equality is part of the logical/metalogical foundation. This is common in first-order semantics and type theories.
2. **Identity structural/derived:** identity is characterized by all admissible predicates, relations, or structural roles (Leibniz-style), with explicit restrictions on the language's expressive strength.
3. **Identity level-relative:** equality, equivalence, isomorphism, observational indistinguishability, and occurrence identity are distinct relations whose admissibility depends on type, context, and task.

Important caution: a second-order Leibniz definition does not automatically define equality in a weak first-order language; type-theoretic identity types are not merely ordinary observational equivalence; univalence identifies equivalence of types with identity of types, not arbitrary equivalence of all objects. Category theory's invariance under isomorphism does not eliminate identity morphisms.

The question is therefore not simply "identity or no identity?" It is: which identity notion is primitive at which level, what work does it do, and which rules make it substitutive, transportable, contractible, or observable?

## 11. Adversarial test suite

Use one shared family of examples across four formal settings:
- classical first-order logic (with and without equality; nonempty vs empty domains);
- linear logic (linear assumptions vs `!`-assumptions);
- dependent type theory (identity types, transport, path induction; distinguish type identity from term identity);
- a contextual/fibrational model motivated by Synesism (identity and equivalence indexed by module/protocol; strict vs fibrant interpretation).

Pathology/edge cases:
1. Existential import: `∀x φ ⊢ ∃x φ` depends on nonempty-domain semantics or an explicit witness.
2. Empty domain: vacuous universal truth does not imply existential truth.
3. Russell/comprehension: unrestricted construction is a formation-rule issue; do not falsely attribute it to names alone.
4. Curry/self-reference: test typing/diagonalization and contraction/implication assumptions separately.
5. Quotient collapse: current queries factor, but a future operation is not congruent.
6. Evidence duplication: two identical data values with distinct provenance versus one duplicated record.
7. Co-reference under opacity: names co-refer extensionally but are not substitutable in an intensional/opaque context.
8. Resource duplication: two linear tokens versus one token; unrestricted `!` case.
9. Context shift: equivalence in module Ω₁ but not Ω₂.
10. Refinement/reconstruction: a quotient plus a section/provenance map versus quotient alone.

## 12. Minimal implementation plan

### Spike 17a — formal core
- Add an isolated Lean module with protocol-indexed indistinguishability, protected query families, quotient factorization, congruence, occurrence tokens, and a minimal contraction judgment.
- Prove only the general lemmas whose assumptions are explicit.
- Include counterexamples demonstrating that entity identity, occurrence identity, and contraction differ.

### Spike 17b — cross-logic comparison
- Formalize finite fragments for classical FOL, linear assumptions, and a small dependent identity-type fragment.
- Use a common test matrix; report what is definable, what is primitive, and what is not preserved.

### Spike 17c — CSIR extension
- Encode source/target nodes, transformation artifacts, equivalence/context, protected interfaces, preservation certificates, resource/provenance data, and warrants.
- Verify certificates independently.
- Add schema migration only after at least three fragments need the same fields.

### Spike 17d — Synesism bridge
- Build a small contextual/fibrational model; compare strict quotient with context-indexed/fibrant equivalence.
- Test P1's true/phenomenological identity distinction and P2 relational constitution without changing canon.
- Submit a reconciliation note with exact formal results, counterexamples, and unresolved gaps.

## 13. Prior-art and novelty discipline

This project must not claim to invent:
- linear logic's control of contraction/weakening;
- quotient universal properties or congruence criteria;
- Leibniz equality;
- identity types or univalence;
- observational equivalence and contextual equivalence;
- fibrations or descent.

The possible contribution is a tested integration of these notions with PFT's protocol/query factorization, evidence provenance, resource accounting, and CSIR's independently verifiable transformation certificates. Novelty requires a separate literature review.

## 14. Acceptance criteria

A first milestone is complete only when:
1. The four identity/occurrence/contraction notions are formally distinct.
2. The factorization criterion is proved in the chosen fragment.
3. A quotient that preserves current queries but fails future congruence is exhibited.
4. A contraction counterexample shows identical content is insufficient when multiplicity matters.
5. At least one safe contraction condition is proved.
6. The same examples are represented in all four comparison settings or explicit blockers are recorded.
7. Claims enter the Semplex ledger with status, assumptions, dependencies, and counterarguments.
8. No Synesism canon file is changed without explicit approval.

## 15. The central question

**What is the minimal structure that makes distinction, reference, identity, inference, and admissible abstraction possible—and which of these structures can be derived from the others without circularity or loss of the phenomena they are meant to explain?**

That is the foundational problem. The rest of the work package operationalizes it.
