# Spike 17 — Distinction admissibility, identity, and controlled contraction

**Status:** initial finite demonstrator complete; Lean proof source committed for verification; not yet fully proof-assistant verified.
**Date:** 2026-11-20
**Branch:** research/distinction-calculus

## Question

Can identity, substitution, contraction, quotienting, and context-sensitive equivalence be compared through one preservation calculus without erasing the differences among classical first-order logic, linear logic, dependent type theory, and Synesism-inspired contextual semantics?

## Prior-art gate

The relevant mathematics is established: quotient factorization and congruence for induced operations; classical equality and substitutivity; linear logic's restriction of weakening/contraction and exponential modalities; Martin-Löf identity types and path induction; fibrations/indexed categories as categorical semantics of substitution.

The proposed contribution is an integration into Semplex's protocol-relative preservation and CSIR/certificate architecture. No claim of new mathematics is made.

## Formal core

For T : X → Y and protected query q : X → A:

    Preserves(T,q) := for all x,x', T(x)=T(x') implies q(x)=q(x').

This is equivalent to q factoring through the image of T. For quotient relation R, a query descends iff constant on R-classes. An operation descends only if R is a congruence for that operation. The distinction-admissibility contract must list both protected observations and protected operations; query preservation alone is insufficient.

## Four-system demonstrator

| System | Instance | Result |
|---|---|---|
| Classical FOL | Tarski satisfaction depends only on assignments to free variables | Forgetting a non-free variable preserves satisfaction for that formula; the same quotient can fail for another formula |
| Linear logic | Finite multiset resource semantics | Two linear tokens satisfy a two-token demand; one does not. General contraction is unsound. An unrestricted resource is duplicable by stipulation |
| Dependent type theory | Lean identity type Eq, reflexivity and equality elimination | Substitution of equals follows by identity elimination; this does not prove identity types arise from DAP |
| Contextual/module-indexed | Finite observation families | Two states may be equivalent in a module observing one coordinate and distinguishable in a richer module |

**Scope:** the fourth model is an indexed observational family, not yet a full Grothendieck fibration. A genuine fibration requires a base category of contexts, fibers, cartesian liftings/reindexing, and coherence laws.

## Tests run

Command: PYTHONPATH=. python -m pytest -q against the isolated demonstrator.
Result: **5 passed**.

The Lean source proofs/lean/Distinction.lean and axiom audit proofs/lean/AuditDistinction.lean were added. The current execution environment has no lean/lake executable and no network access, so these files have **not been compiled here**. They must not be represented as Lean-verified until Lean 4.12.0 compiles them and the axiom audit is reviewed.

## Findings

1. DAP is a schema, not a universal axiom. It needs a declared interface: protected observations, operations, protocols/contexts, error tolerance, and resource model.
2. Identity, substitution, and contraction do not collapse into one rule. A common preservation calculus can specify admissibility conditions, but cannot derive them all without assumptions encoding the relevant structure.
3. The Tarski slide is a clean first example. A formula's satisfaction factors through restriction of assignments to its free variables. The quotient is formula-relative.
4. Operation preservation is stronger than query preservation. A finite counterexample demonstrates a quotient that preserves one observable but cannot support a non-congruent operation.
5. Linear logic confirms the resource point. Contraction is controlled by duplicability, not by identity of formula content.
6. Synesism's phenomenal identity has a candidate model: module-indexed equivalence plus continuity/coherence across transitions and overlap compatibility. This is a proposal, not a derivation from P8.

## Kill criteria / unresolved work

- If DAP cannot distinguish a safe quotient from one that breaks a protected operation, revise or reject it.
- If the contextual model is only ordinary observational equivalence with renamed terminology, do not claim a new fibration or new mathematics.
- If P1's true/phenomenological distinction cannot be made precise without contradiction, record the conflict for reconciliation rather than changing canon.
- Before novelty claims, compare against setoids, quotient algebras, linear logic, categorical logic, contextual equivalence, fibrations, and descent.

## Next work

1. Compile Distinction.lean with Lean 4.12.0; audit axioms and add it to tests/test_lean.py.
2. Add explicit finite first-order syntax/semantics and prove the free-variable satisfaction lemma.
3. Replace the fourth toy model with a small split fibration/indexed category and verify reindexing functoriality.
4. Formalize linear resource contexts and the !-like duplicability interface without claiming a full linear-logic proof system.
5. Extend CSIR only after at least three fragments need the same transformation/certificate fields.
6. Build a literature comparison table with precise citations and novelty verdicts before any paper-level claim.
