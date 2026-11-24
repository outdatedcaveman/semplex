# Synesism C-20 and Semplex: resource-calculus integration

**Date:** 2026-11-20  
**Status:** architectural reconciliation; no new theorem claimed  
**Purpose:** prevent Semplex Spike 17 from duplicating the substantially more developed resource-sensitive syntax already present in Synesism, and identify a precise bridge between them.

## 1. Executive finding

Synesism already contains a serious occurrence-sensitive, usage-indexed lambda-calculus development. Semplex's current ResourceOccurrence model is a smaller capacity/provenance semantics, not a competing proof calculus.

The projects should therefore be integrated asymmetrically:

- **Synesism C-20** supplies object-language syntax, usage vectors, binders, substitution, reduction, and typing fragments.
- **Semplex CERP/DAP** supplies transformation contracts, protected observations/operations, occurrence provenance, admissibility checks, and certificate-oriented interfaces.

The finite translation/adequacy boundary is already implemented in Semplex as P091, in both Python and Lean. The next step is to review its exact scope, strengthen the mapping where necessary, and test whether it commutes with Synesism's renaming and parallel-substitution operations. Do not build a second linear lambda calculus unless that audit exposes a concrete gap.

## 2. Existing Synesism results (verified status recorded in milestones)

The relevant source modules are in hott-ultimate/formal/agda-experiments/:

| Milestone | Module | Established result | Important limitation |
|---|---|---|---|
| M263 | P0FullTermSyntax | Full recursive term syntax with variables, pairs, lambda and application; usage vectors; weakening and instantiation under nested binders; usage accounting | No typing relation over this syntax; no reduction rule yet |
| M264 | P0BetaIsLinear | Proves beta preserves the usage vector when the bound variable is used exactly once; now also has machine-checked k=0 weakening and k=2 contraction witnesses | Raw usage semantics; not a typed subject-reduction theorem |
| M265 | P0FullTyping | Typing over the full term syntax for variables, tensor/pair introduction, Π/lambda introduction, dependent naming, and usage conversion; telescoped weakening/substitution; types the instantiated beta contractum | The app constructor has no typing rule. betaPreservesTyping is the substitution theorem for the contractum, not subject reduction from a typed redex. piT stores the variable rank but not its multiplicity, so an application rule cannot recover the argument-usage scaling factor |
| M413 | P0FullSubst | Parallel renaming/substitution, identity, four fusion laws, single-substitution lemma, and closure of reduction under substitution/renaming | Standard sigma-calculus infrastructure; explicitly not claimed as new mathematics |
| M414 | P0FINotFunctorial | A concrete DeltaStructure whose FI extension is not functorial | Shows an action of injections is not automatically an FI-module |
| M415 | P0UnivalentFI | For univalent FI-structures over the classifying type, the Delta-plus/Sigma distributive law follows from identity and composition | Converse/unique extension from arbitrary FI-modules remains open |

The C-20 development still lacks a typed application rule. P0FullTyping's betaPreservesTyping theorem types the instantiated contractum from a typed body and argument; it is not subject reduction from a typed redex. The ungraded piT forgets the bound-variable multiplicity needed to scale argument usage, so a graded Π is the natural completion. Tensor elimination as a genuine term former, linearity as a typing premise, and stronger normalization/confluence results also remain open. These limitations must remain attached to any use of the results.

## 3. What Semplex currently contributes

cerp/distinction.py represents resource occurrences by:

- a token identifying an occurrence;
- a formula/proposition label;
- a linear or persistent mode;
- an origin trail recording provenance.

The current model establishes finite semantic facts:

1. A context is well formed only when occurrence tokens are unique.
2. Merging two distinct persistent occurrences of the same formula preserves support for every finite demand and retains both origin trails.
3. Merging two linear occurrences can remove one unit of capacity, when no persistent occurrence supplies the formula.
4. P091 maps an all-linear C-20 usage vector onto Semplex occurrence tokens; Python supports an explicit bijection, while Lean proves the positional special case and an aggregate capacity bound.
5. DAP states preservation obligations relative to declared observations, operations, relations, protocols and permitted loss.

This is useful, but it is **not** yet a derivation calculus, a complete linear logic, a proof of cut admissibility, or an exponential modality.

In particular, ResourceMode.PERSISTENT is currently an external reusable-context classification. It is not yet the object-language !A of linear logic, nor has it been given a comonad/comonoid interpretation.

## 4. The key distinction between the models

Do not identify these objects:

- Synesism's usage vector counts occurrences of variables in a scoped term/context.
- Semplex's token IDs identify evidence/resource occurrences in a finite operational context.
- A formula label in Semplex is not automatically a type in the Synesism syntax.
- Provenance trails are not the same thing as term-variable multiplicity.
- Equality of resource support is weaker than equality of derivations or preservation of substitution.

A valid bridge must state the translation and prove its properties. A suggestive analogy is not enough.

## 5. Implemented finite adapter: P091

The adapter is already implemented in both Python and Lean.

**Python implementation**
- ResourceUse records a token, formula label, variable index, usage count, and provenance.
- ResourceProfile aggregates usage by formula and exposes unused tokens, duplicated tokens, at-most-once capacity, and exact-once usage.
- resource_profile_from_usage accepts an explicit token-to-variable bijection and a formula-to-C-20-rank map; it rejects duplicate tokens, missing or non-bijective mappings, rank mismatches, negative counts, and persistent contexts.
- resource_profile_fits_context checks token/formula correspondence, per-token linearity, and aggregate demand against the context's linear capacity.
- tests/test_distinction.py has 22 passing tests in the latest recorded focused run; adapter-specific cases cover successful alignment, weakening (zero use), contraction (multiple use), invalid maps, persistent rejection, negative counts, noncontiguous variable positions, and forged provenance.

**Lean implementation**
- Namespace C20Adapter defines an ordered context/usage profile by zipping the resource context with the usage vector.
- usage_for_formula_le_linear_capacity proves that, for an all-linear context and a usage vector with every coordinate at most one, aggregate per-formula demand is bounded by the context's linear capacity.
- adapter_rank_aligned and adapter_profile_length certify the rank alignment and length correspondence.
- AuditDistinction.lean includes explicit axiom-audit commands. The latest compile confirms: `usage_for_formula_le_linear_capacity` and its adapter wrapper use `propext`, `Classical.choice`, and `Quot.sound`; `adapter_rank_aligned` has no axioms; `adapter_profile_length` and `profile_length` use `propext`; `linearCount_cons` and the new `linearCount_perm` use `propext` and `Quot.sound`; `usageForFormula_perm` uses `propext`; and `adapter_capacity_bound_invariant_under_permutation` uses `propext` and `Quot.sound`. These are reported dependencies, not hidden assumptions.

**Exact scope and mismatch**
- The Lean adapter uses context order as its canonical token-to-variable bijection; Python supports an arbitrary explicit bijection. Lean now proves `usageForFormula_perm`, `linearCount_perm`, and `adapter_capacity_bound_invariant_under_permutation`. The last theorem is deliberately conditional on an explicit paired permutation of `(occurrence, usage)` profiles as well as a context permutation. It does not derive the paired profile permutation from a token bijection or from an arbitrary permutation of contexts alone. This closes aggregate-demand invariance under a supplied alignment, not the general equivalence to Python's arbitrary-bijection implementation.
- **Direct prior art:** Wood and Atkey's ESOP 2022 Agda framework (`laMudri/generic-lr`, artifact DOI `10.5281/zenodo.6146236`) defines usage-aware environments with a relational linear map Ψ, a resource inequality P ≤ QΨ, and a lookup operation. It proves identity/composition of environments and derives resource-correct renaming and simultaneous substitution. For finite free usage modules, Ψ is represented by a matrix acting on row vectors. The P091 all-linear token/variable alignment is a candidate restricted instance of this environment structure, not a new resource-environment calculus. The generic framework is for simply typed syntaxes with fixed Ty : Set; C-20's dependent Π fragment is not automatically covered. A checked translation remains OPEN.
- **Direct dependent-type prior art:** Atkey's QTT (LICS 2018, DOI `10.1145/3209108.3209189`) already has semiring-annotated contexts in dependent type theory, dependent Π types graded by argument multiplicity π, an application rule that scales argument usage by π, and an admissible substitution lemma (Lemma 2.5). A candidate correspondence is: C-20's `Usage Γ` ↔ QTT's semiring usage context; `headU u` ↔ Π grade π; `popU u` ↔ the free-variable usage after abstraction; `uf + q · ua` ↔ QTT application usage; and M265's substitution theorem ↔ QTT substitution admissibility. This is a comparison map to prove, not an established equivalence. QTT is substantially richer than current M265, which has no application typing rule.
- The Lean theorem proves an upper bound, not a full isomorphism between Semplex profiles and Agda's indexed Usage type.
- The adapter is all-linear only. Persistent resources are rejected because C-20's current LCtx/Usage fragment has no exponential or reusable-context semantics.
- No theorem yet shows the adapter commutes with renaming or M413's parallel substitution/fusion laws.

This is a meaningful finite adequacy result, not a full resource calculus or a cross-language equivalence theorem. The adapter must reject persistent occurrences rather than silently treating them as linear or duplicable.

## 6. How DAP can add something beyond C-20

C-20 explains when beta reduction conserves a usage vector. DAP can generalize the question from one reduction rule to arbitrary representation-changing transformations.

For a transformation T, protected observations Q and protected operations F, the certificate should report:

- which usage/provenance observables factor through T;
- which operations descend or commute with T;
- which occurrence identities are merged;
- whether multiplicity is conserved, consumed, duplicated, or abstracted;
- the exact contexts in which the guarantee holds.

This suggests a DAP certificate for beta reduction:

- protected observable: the usage profile of free variables;
- protected operation: substitution/reduction;
- contract: exact usage preservation for linear redexes;
- failure witness: a redex using its bound variable zero or at least twice, provided the argument carries nonzero usage; usage-empty arguments are the exception.

The M264 theorem is the appropriate source theorem for this case. Semplex should represent and check its contract, not re-prove the same arithmetic under a new name.

## 7. Research questions and falsifiers

### Candidate transport semantics (proposed; not yet proved)

The next bridge should not treat every renaming or substitution as a permutation. A permutation merely reorders coordinates; general substitutions can erase, identify, or duplicate them. The natural finite representation is a matrix action on usage vectors.

Let I be the source-variable positions and J the target-variable positions. For a renaming r : I → J, define its incidence matrix R by R(i,j)=1 exactly when r(i)=j, and 0 otherwise. A source usage row-vector u is transported by:

`u' = u R`, equivalently `u'(j) = Σ_{i : r(i)=j} u(i)`.

This handles non-injective renaming by summing the usages of all source variables identified at a target variable. Bijective renaming is the special case where R is a permutation matrix; that is precisely the case covered by the current paired-permutation Lean theorem.

For a substitution σ assigning a target term to each source variable, define Mσ(i,j) as the number of occurrences of target variable j in σ(i). The candidate law is:

`usage(sub σ t) = usage(t) Mσ`.

For composable substitutions σ : Γ → Tm(Δ) and τ : Δ → Tm(Θ), the expected matrix law is:

`M(sub τ ∘ σ) = Mσ Mτ`.

These equations are a proposed finite abstraction of the usage accounting, not current theorems. M263's instantiation law and the Agda vector bridge establish an important single-variable/telescope case; M413 establishes syntax-level fusion. The missing proof is that the usage-vector interpretation is functorial for arbitrary renaming and parallel substitution, including binder extension.

This matrix view also exposes the token issue. Under non-injective renaming, distinct source tokens may point to one target variable, so the token-to-variable map is no longer a bijection. Under substitution, a source token's provenance may be erased (zero use) or expanded into multiple target occurrences (multiple use). The adapter must preserve token identity/provenance while allowing a many-to-one or weighted incidence relation; it must not silently coerce that relation back into a bijection. Whether such expansion is admissible depends on the declared resource mode and capacity contract.

1. **Permutation naturality (partially closed):** Lean proves aggregate invariance given an explicit paired profile permutation. Can the Python token-to-variable bijection be compiled into that paired permutation, with a checked correspondence to the positional Lean representation?
2. **Stronger adequacy:** the Agda-side finite-vector/list representation of M263 Usage and its coordinate/length correspondence are now machine-checked. The remaining question is a cross-language theorem connecting that serialization to the Lean/Python adapter.
3. **Substitution:** Agda proves vector-level corollaries of all four M413 fusion laws and the instantiation-to-substitution identity. The remaining question is whether the Lean/Python adapter's profile transformation commutes with those operations, or whether a precise counterexample narrows the interface.
4. **Persistence:** can the persistent-context rule be represented by a principled exponential/comonoid structure, rather than a Boolean shortcut?
5. **Transformation composition:** can DAP certificates compose while tracking both semantic distortion and provenance?
6. **Module indexing and identity:** can protected observations, resource permissions, and occurrence identity vary coherently across Synesism modules without conflating evidence identity, formula identity, and phenomenal identity?

Falsifiers include a failure of permutation naturality, a binder/substitution counterexample, or a case where persistent merging preserves present support but breaks a protected operation.

## 8. Next implementation sequence

1. Treat P091 as the current baseline; do not reimplement the adapter.
2. DONE: formalize the Agda M263 Usage-to-vector/list representation, coordinate/rank correspondence, and stored-occurrence convention. The Agda module compiles with --safe; no cross-language theorem is claimed.
3. DONE (conditional Lean result): prove invariance of aggregate formula demand and linear capacity under a supplied paired permutation. OPEN: derive that paired permutation from Python's explicit token-to-variable bijection and prove representation correspondence.
4. M264's explicit k=2 beta-contraction witness is now added and Agda-checked; keep it distinct from the k=0 weakening witness, and do not claim a universal iff theorem.
5. DONE (Agda-side): vector extraction respects renRen, renSub, subRen, subSub, renIsSub, betaIsSingle, and the instantiation usage law. OPEN (adapter-side): prove the Lean/Python profile action commutes with these transformations, or produce a counterexample that narrows the contract.
6. Only after those steps, investigate an exponential/persistent extension and module-indexed contracts. Keep P091 scoped to an all-linear finite fragment and update the claims register only when a new theorem or counterexample is independently checked.

## 9. Claim discipline

- **HAVE (Synesism):** the exact M263/M264/M265/M413/M414/M415 fragments, at the scope and limitations recorded in scripts/milestones.json.
- **HAVE (Semplex):** the finite Python and Lean occurrence/resource fragments already recorded in Spike 17.
- **HAVE (Agda):** finite-vector/list representation of M263 Usage, instantiation usage law, and vector-level M413 fusion corollaries.
- **PROPOSED:** cross-language permutation/substitution naturality and DAP-certificate integration around P091.
- **OPEN:** a unified calculus, a genuine exponential semantics, cut admissibility across the proposed interface, and a general module-indexed resource theory.

No claim is made here that Synesism or Semplex has solved linear logic, established a new logic, or derived identity from resources.
