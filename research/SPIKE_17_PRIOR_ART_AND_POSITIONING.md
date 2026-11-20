# Spike 17 — prior-art and contribution boundary

**Status:** preliminary literature map; not a novelty claim.  
**Purpose:** prevent established mathematics from being relabelled as a Semplex discovery.

## 1. Results already established in the literature

### 1.1 Quotients, factorization, and congruence

The quotient universal property says that a function on a carrier descends to a quotient precisely when it is constant on equivalence classes. For algebraic operations, the relevant equivalence must be a congruence. This is standard quotient algebra / universal algebra, not a new DAP result.

The Lean fragment formalizes:
- query factorization through the kernel equivalence of a representation map;
- sufficient congruence conditions for unary and binary operations to descend;
- the converse condition for a binary operation that commutes with the quotient map.

The binary converse is deliberately stated with the commuting square as a hypothesis. It does not claim that an arbitrary operation on the quotient exists without that compatibility.

### 1.2 First-order satisfaction and free-variable support

Tarski semantics defines satisfaction relative to assignments and recursively updates assignments at quantified variables. The theorem that satisfaction depends only on values assigned to free variables is standard. The new Lean file gives a small core-Lean mechanization for a language with equality, constants, unary predicates, falsity, implication, and universal quantification.

The language fragment is intentionally smaller than full first-order logic: no function symbols of positive arity, no relation symbols of arity greater than one, no existential quantifier constructor (existential import is treated separately), and no many-sorted syntax.

The slide's universal-to-existential inference is valid for nonempty domains. The Lean theorem makes the witness explicit. The empty-domain countermodel shows why the nonemptiness assumption matters if empty domains are admitted.

### 1.3 Linear logic and contraction

Girard's linear logic already distinguishes resources that may be used once from formulas that can be reused through exponential modalities. Semplex is not introducing controlled contraction. The initial Lean/Python fragment modeled a small resource semantics with a natural-number count and a Boolean persistent permission. The current branch has refined this into an occurrence-sensitive capacity model:
- individual token IDs and proposition labels;
- linear versus persistent modes;
- explicit provenance trails, concatenated when occurrences are merged;
- a finite-demand support relation.

This is still not a sequent calculus for linear logic or a formalization of its exponential rules.

It proves a minimal counterexample to contraction for linear tokens and sufficient conditions under which contraction is safe in this toy semantics. It is **not** a sequent calculus for linear logic, and the Boolean persistent flag is not a formalization of the full exponential rules, dereliction, promotion, or their cut-elimination metatheory.

### 1.4 Identity types and transport

Dependent type theory has an identity type with reflexivity and an eliminator (path induction), from which substitution/transport is derived. Lean's Eq is the identity type used in the present fragment. The theorem substitution_of_identity formalizes equality elimination for predicates.

This does not derive identity types from DAP. It demonstrates that substitution is structurally dependent on an identity eliminator.

HoTT enriches this picture by interpreting identity proofs as paths and, with univalence, relating identity of types to equivalence of types. Univalence does not identify arbitrary objects just because they are observationally indistinguishable.

### 1.5 Fibrations and indexed categories

The Grothendieck construction relates indexed categories/pseudofunctors to fibrations. The current SmallFibration.lean file is a small split fibration arising from a set-valued contravariant family; its fibers are discrete. This is a standard special case of the category-of-elements/Grothendieck construction. ModuleDescent.lean separately formalizes a finite two-module matching-family example with overlap compatibility and unique gluing; this is a basic finite product/sheaf-style gluing result, not a new descent theorem.

Its value is methodological: it checks that the intended module-indexing story can be represented with an actual base, fibers, reindexing, cartesian lifts, and cleavage coherence. It is not a new fibration construction.

## 2. Relationship to Semplex's existing Protocol-Frame Theory

PFT Theorem 10 already proves that a query determined by observational power factors through the canonical observational profile. Therefore, the first query-preservation component of DAP is an extension of an existing Semplex theorem's pattern, not a new result by itself.

The plausible extension is to make the preservation interface richer:
1. not only current observations/queries, but protected operations;
2. not only a quotient induced by an observational profile, but arbitrary source-to-target transformations;
3. not only extensional outputs, but occurrence identity, provenance, and resource permissions;
4. not only a theorem, but an independently checkable transformation certificate integrated with CSIR.

Even these points may have close precedents in abstract interpretation, compiler correctness, data refinement, algebraic specification, resource semantics, and categorical semantics. Each must be compared against the appropriate literature before any novelty statement.

## 3. What the current code does and does not establish

| Component | Current result | Not established |
|---|---|---|
| Query preservation | Quotient factorization criterion in Lean | A new universal abstraction theory |
| Typed DAP contract | A Lean interface/contract for protected observations and total unary/binary operations, with quotient descent | General transformations, loss certificates, or higher-order/effectful operations |
| Operation preservation | Unary/binary quotient-operation descent and binary converse | General higher-order, partial, stochastic, stateful, or effectful operations |
| FOL | Satisfaction invariance over free variables in a small syntax | Full FOL metatheory or completeness |
| Existential import | Nonempty witness theorem and empty-domain countermodel | A metaphysical existence principle |
| Equality substitution | Lean Eq elimination | Derivation of identity from admissibility |
| Contraction | Finite resource countermodel and safe cases | Full linear logic or a general theory of evidence duplication |
| Contextual identity | Module-indexed observational equivalence in Python | Ontological identity of phenomenal beings |
| Fibration | Small split fibration with discrete fibers | A nontrivial category of modules with rich morphisms or Synesism P8 |
| Module gluing | Finite two-module overlap: compatibility iff a unique global profile exists | General sheaf condition, arbitrary covers, or ontology of phenomenal beings |

## 4. Primary references

1. Jean-Yves Girard, “Linear Logic,” Theoretical Computer Science 50(1), 1987, 1–102. DOI: https://doi.org/10.1016/0304-3975(87)90045-4. This is the foundational reference for the distinction between linear use and exponential/reusable formulas.
2. Bart Jacobs, Categorical Logic and Type Theory, Studies in Logic and the Foundations of Mathematics 141, North-Holland/Elsevier, 1999. Author's book page and contents: https://www.cs.ru.nl/B.Jacobs/CLT/bookinfo.html. Chapters 1 and 4 cover fibrations, split fibrations, indexed categories, and first-order predicate logic; the book explicitly uses fibrations as a unifying concept.
3. The Univalent Foundations Program, Homotopy Type Theory: Univalent Foundations of Mathematics, Institute for Advanced Study, 2013. arXiv: https://arxiv.org/abs/1308.0729 ; book site: https://homotopytypetheory.org/book/. Relevant for identity types, path induction, higher structure, and univalence.
4. “Tarski's Truth Definitions,” Stanford Encyclopedia of Philosophy. https://plato.stanford.edu/entries/tarski-truth/. Relevant for satisfaction relative to assignments, recursive clauses, and the relationship between satisfaction and free variables.
5. Stanford CS257, “First-order Logic: Semantics,” lecture slides, 2023. https://web.stanford.edu/class/cs257/slides/Lecture_7.pdf. States and proves the standard free-variable assignment-invariance theorem by induction.
6. Lean 4 core API, Init.Core: https://lean-lang.org/doc/api/Init/Core.html ; Lean reference: Quotients: https://lean-lang.org/doc/reference/latest/The-Type-System/Quotients/. These specify the kernel quotient primitives and Quotient.lift, Quotient.sound, and related constructions used by the mechanization.

## 5. Novelty gate

No paper or public description should claim that Semplex has invented:
- quotient factorization;
- congruence as the condition for induced quotient operations;
- free-variable invariance in Tarski semantics;
- linear logic's controlled contraction/weakening;
- identity types or substitution by path induction;
- the Grothendieck construction or split fibrations;
- univalence.

A defensible future contribution would need a theorem or tool that materially strengthens the combination above—for example, a general certificate calculus for typed transformations that composes query preservation, operation compatibility, occurrence/provenance preservation, and resource accounting, with mechanically checkable loss bounds. That is a research target, not a result of this spike yet.
