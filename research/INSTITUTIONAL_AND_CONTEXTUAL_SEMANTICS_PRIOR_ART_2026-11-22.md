# Institutional and contextual semantics: prior-art correction
Date: 2026-11-22

## Why this changes the programme

The cross-theory and contextual parts of the candidate master theorem are not blank territory. Two bodies of work already formalize much of what we had described as future architecture:

1. **Institution theory** (Goguen–Burstall) abstracts logical systems as signatures, sentences, models, and satisfaction, with a satisfaction condition enforcing truth invariance under change of notation. Institution morphisms/comorphisms already formalize truth-preserving translations among logics.
2. **Sheaf-theoretic contextuality** (Abramsky–Brandenburger) models local empirical data over measurement contexts and characterizes the existence of global non-contextual realizations by global-section obstructions. This is a concrete operationally grounded use of contextual descent, including cases where no global section exists.

Therefore, “we will add context categories, satisfaction, and translations between semantic theories” is not a sufficiently distinctive research claim. We should use these theories as foundations and ask what remains absent: a higher/resource-indexed moduli theory of *operationally grounded semantic systems* that connects institutional satisfaction and empirical realizability without conflating them.

## 1. Institution theory

Canonical source:
- Joseph A. Goguen and Rod M. Burstall, “Institutions: Abstract Model Theory for Specification and Programming,” *Journal of the ACM* 39(1), 95–146 (1992), DOI: 10.1145/147508.147524.
- Author-hosted overview and technical exposition: https://cseweb.ucsd.edu/~goguen/projs/inst.html
- Original LFCS report: https://publish.lfcs.inf.ed.ac.uk/reports/90/ECS-LFCS-90-106/

An institution comprises:
- a category Sign of signatures and signature morphisms;
- Sen: Sign → Set, sentences over signatures;
- Mod: Signᵒᵖ → Cat, models and reducts;
- satisfaction relations ⊨_Σ between Σ-models and Σ-sentences;
- the satisfaction condition: for σ:Σ→Σ′, M′ a Σ′-model, and φ a Σ-sentence,
  M′ ⊨_{Σ′} Sen(σ)(φ) iff Mod(σ)(M′) ⊨_Σ φ.

This explicitly handles truth-preserving change of notation. Institution morphisms/comorphisms provide structured translations among logical systems. The framework has applications to programming/specification languages, databases, ontologies, and natural-language semantics.

Implication: our T7 (“cross-theory adequacy”) overlaps strongly with institution theory. The research question should be whether we can define an *operationally grounded higher institution* whose model fibres carry causal realization, evidence/warrant, and resource-indexed probes, and whose institutional translations are conservative for a declared semantic signature.

Important limitation: the institution satisfaction condition is an invariance axiom for a formal satisfaction relation. It does not, by itself, ground the model's reference to an external physical world, justify the satisfaction relation empirically, or prove that a chosen institution captures all meaning.

## 2. Sheaf-theoretic contextuality

Canonical sources:
- Samson Abramsky and Adam Brandenburger, “The Sheaf-Theoretic Structure of Non-Locality and Contextuality,” *New Journal of Physics* 13 (2011), 113036; arXiv:1102.0264.
  https://arxiv.org/abs/1102.0264
- Samson Abramsky, Shane Mansfield and Rui Soares Barbosa, “The Cohomology of Non-Locality and Contextuality,” arXiv:1111.3620 (2011).
  https://arxiv.org/abs/1111.3620

The first paper organizes measurement contexts into a cover, local outcome assignments into a presheaf, and empirical models into compatible local data. Non-contextuality corresponds to the existence of a global section; contextuality is an obstruction to such a section. The cohomological extension supplies obstruction witnesses in important examples.

Implication: our descent programme must not assume that all local semantics glue. In physical and computational settings, failure to glue may be the phenomenon to be explained. The right object is often a moduli/obstruction space of compatible local realizations, not a sheafification that silently forces a global object.

The sheaf-theoretic model is already operational: contexts are measurement choices, local sections are outcome assignments, and empirical distributions are observed. This is a strong testbed for the proposed framework.

## 3. Categorical logic and indexed semantics

Lawvere hyperdoctrines organize predicates/propositions over contexts and model quantifiers through adjoints to substitution/reindexing, subject to Beck–Chevalley-style coherence. This is another mature foundation for syntax/logic/semantics integration.

Reference overview:
- Stanford Encyclopedia of Philosophy, “Intuitionistic Type Theory,” section on categorical models and hyperdoctrines:
  https://plato.stanford.edu/entries/type-theory-intuitionistic/

Implication: semantic propositions should likely form an indexed doctrine/fibration over contexts/worlds, rather than merely be a field on each isolated model. This would represent substitution, quantification, and contextual transport structurally.

## 4. Inferentialism is not just another encoding of truth conditions

The proof-theoretic semantics literature treats inferential role/proof as conceptually prior to truth-conditional denotation in important approaches. The contrast is not simply two equivalent notations; it concerns explanatory priority and what counts as meaning.

Reference:
- Peter Schroeder-Heister, “Proof-Theoretic Semantics,” Stanford Encyclopedia of Philosophy, revised 2023:
  https://plato.stanford.edu/entries/proof-theoretic-semantics/
- “Theories of Meaning,” Sydney Encyclopedia of Philosophy, discussion of inferentialism:
  https://plato.sydney.edu.au/entries/meaning/

Implication: a joint conservative signature must not impose truth-conditional primacy. It should preserve inferential consequence/warrant as a separate invariant and identify conditions under which inferential and model-theoretic semantics agree.

## 5. Revised synthesis

A promising base architecture is not a single ordinary category of structures with a truth predicate. It is a layered object:

- an institution-like indexed syntax/model/satisfaction structure;
- a context site (or higher category) of admissible experiments and interventions;
- an operational empirical model/presheaf recording observations;
- a causal realization relation connecting semantic models to operational systems;
- an evidence/warrant doctrine indexed over claims and contexts;
- a resource-indexed category of admissible probes;
- a space-valued moduli construction retaining equivalences, automorphisms and higher coherence.

The central challenge is to prove a compatibility theorem among these layers: institutional satisfaction transport, operational realization, evidence/warrant updates, and higher moduli reconstruction must commute where the theory says they should, while contextuality and non-identifiability remain explicit obstructions.

This is a better research frontier than rediscovering institution theory or sheaf contextuality. It may still overlap with existing work on categorical causal models, higher institutions, sheaf semantics and homotopy type theory; systematic literature review remains necessary.

## Verified source records

- Goguen & Burstall 1992 DOI confirmed by ACM/DBLP/LFCS records: 10.1145/147508.147524.
- Abramsky & Brandenburger arXiv record: 1102.0264.
- Abramsky, Mansfield & Barbosa arXiv record: 1111.3620.
- Institution overview explicitly states the signature/sentence/model/satisfaction structure and institution morphisms.
- SEP proof-theoretic semantics entry revised 2023 explicitly distinguishes proof/inference-based meaning from truth-condition semantics.

## 6. Lean interface added

Added `proofs/lean/InstitutionalSemantics.lean`, a minimal ordinary institution structure with:
- a signature category;
- covariant sentence translation;
- contravariant model reduct;
- functorial identity/composition laws;
- satisfaction condition.

The module proves satisfaction transport and its compositionality along signature morphisms. Focused and full Lean builds pass; the two theorems have no axiomatic dependencies.

This formalization is deliberately a baseline, not a novelty claim. It makes the institutional satisfaction condition explicit in the proof corpus so the later grounded/triadic/higher extension can be compared against a known logical interface. It does not prove external reference, empirical truth, or that the chosen institution covers all semantic phenomena.
