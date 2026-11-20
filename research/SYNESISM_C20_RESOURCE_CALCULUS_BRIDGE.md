# Synesism C-20 and Semplex: resource-calculus integration

**Date:** 2026-11-20  
**Status:** architectural reconciliation; no new theorem claimed  
**Purpose:** prevent Semplex Spike 17 from duplicating the substantially more developed resource-sensitive syntax already present in Synesism, and identify a precise bridge between them.

## 1. Executive finding

Synesism already contains a serious occurrence-sensitive, usage-indexed lambda-calculus development. Semplex's current ResourceOccurrence model is a smaller capacity/provenance semantics, not a competing proof calculus.

The projects should therefore be integrated asymmetrically:

- **Synesism C-20** supplies object-language syntax, usage vectors, binders, substitution, reduction, and typing fragments.
- **Semplex CERP/DAP** supplies transformation contracts, protected observations/operations, occurrence provenance, admissibility checks, and certificate-oriented interfaces.

The next step is not to build a second linear lambda calculus in Semplex. It is to formalize a translation/adequacy boundary between the two representations and determine what additional guarantees DAP contributes.

## 2. Existing Synesism results (verified status recorded in milestones)

The relevant source modules are in hott-ultimate/formal/agda-experiments/:

| Milestone | Module | Established result | Important limitation |
|---|---|---|---|
| M263 | P0FullTermSyntax | Full recursive term syntax with variables, pairs, lambda and application; usage vectors; weakening and instantiation under nested binders; usage accounting | No typing relation over this syntax; no reduction rule yet |
| M264 | P0BetaIsLinear | Beta preserves usage exactly when the bound variable is used once; zero uses and two uses exhibit weakening/contraction failure modes | Raw usage semantics, not yet a typed subject-reduction theorem |
| M265 | P0FullTyping | Typing over the full syntax; weakening, substitution and subject reduction for beta | Application is a constructor without its own typing rule; linearity is a usage property, not a typing premise |
| M413 | P0FullSubst | Parallel renaming/substitution, identity, four fusion laws, single-substitution lemma, and closure of reduction under substitution/renaming | Standard sigma-calculus infrastructure; explicitly not claimed as new mathematics |
| M414 | P0FINotFunctorial | A concrete DeltaStructure whose FI extension is not functorial | Shows an action of injections is not automatically an FI-module |
| M415 | P0UnivalentFI | For univalent FI-structures over the classifying type, the Delta-plus/Sigma distributive law follows from identity and composition | Converse/unique extension from arbitrary FI-modules remains open |

The C-20 development also records remaining gaps: tensor elimination as a genuine term former, typing rules for application, linearity as a typing premise, and stronger normalization/confluence results. These limitations must remain attached to any use of the results.

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
4. DAP states preservation obligations relative to declared observations, operations, relations, protocols and permitted loss.

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

## 5. Candidate bridge: occurrence contexts to usage profiles

A first finite adapter can be specified without claiming a full calculus.

Let a finite resource context be a list of uniquely tokened occurrences. For each proposition/type label A, define:

- linearCount(Gamma,A): number of linear occurrences labelled A;
- persistentPresent(Gamma,A): whether a persistent occurrence labelled A exists;
- support(Gamma,A,k): persistentPresent(Gamma,A) or k <= linearCount(Gamma,A).

A Synesism usage vector is a function-like finite profile over the ordered variable context. The adapter must therefore include an explicit label-to-variable map; it cannot simply identify labels with variables.

The first adequacy theorem should be finite and conditional:

> Given an injective assignment of resource tokens to distinct variables and a label-preserving map from resource formulas to types, the Semplex linear count for each label equals the corresponding Synesism usage count.

Persistent resources require a separate interpretation. Possible choices include a reusable ambient context, a marked duplicability structure, or a future exponential type former. None should be selected silently.

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
- failure witness: a redex using its bound variable zero or at least twice.

The M264 theorem is the appropriate source theorem for this case. Semplex should represent and check its contract, not re-prove the same arithmetic under a new name.

## 7. Research questions and falsifiers

1. **Adequacy:** can a finite token context be translated to a usage-indexed context with exact support/count correspondence?
2. **Persistence:** can the persistent-context rule be represented by a principled exponential/comonoid structure, rather than a Boolean shortcut?
3. **Substitution:** does the adapter commute with Synesism's parallel substitution and its four fusion laws?
4. **Transformation composition:** can DAP certificates compose while tracking both semantic distortion and provenance?
5. **Module indexing:** can the protected observations and resource permissions vary by Synesism module, with coherent reindexing?
6. **Identity:** can evidence-occurrence identity be separated from formula identity and from phenomenal identity without collapsing their distinct roles?

Falsifiers include a failure of the proposed adapter to preserve counts under a binder, a substitution counterexample, or a case where persistent merging preserves present support but breaks a protected operation.

## 8. Next implementation sequence

1. Keep the current Semplex occurrence model as a finite reference semantics.
2. Add an explicit ResourceProfile abstraction and tests for count/support extraction.
3. Formalize the finite adapter and its count-preservation theorem in Lean, with no imported custom axioms.
4. Compare the Lean theorem statement against the Agda definitions in M263/M265/M413; record any mismatch as a failed bridge, not a patch to the target.
5. Only after the adapter is stable, investigate an exponential/persistent extension and module-indexed contracts.
6. Update the claims register with theorem-level evidence only after the Lean audit passes.

## 9. Claim discipline

- **HAVE (Synesism):** the exact M263/M264/M265/M413/M414/M415 fragments, at the scope and limitations recorded in scripts/milestones.json.
- **HAVE (Semplex):** the finite Python and Lean occurrence/resource fragments already recorded in Spike 17.
- **PROPOSED:** the adapter and DAP-certificate bridge.
- **OPEN:** a unified calculus, a genuine exponential semantics, cut admissibility across the proposed interface, and a general module-indexed resource theory.

No claim is made here that Synesism or Semplex has solved linear logic, established a new logic, or derived identity from resources.
