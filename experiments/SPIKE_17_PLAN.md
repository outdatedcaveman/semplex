# Spike 17 — Identity, controlled contraction, and admissible distinction loss

**Status:** proposed; no experiment results yet  
**Parent:** Protocol-Frame Theory / CSIR v0.1  
**Design principle:** smallest end-to-end spike, prior-art gate, explicit kill criteria, independent verification.

## Question

Can we extend Protocol-Frame Theory from protocol-relative indistinguishability and query factorization to a verified account of (i) admissible quotienting, (ii) operation-preserving abstraction, and (iii) controlled contraction of assumption/evidence occurrences?

## Hypotheses and kill criteria

| ID | Hypothesis | Kill criterion |
|---|---|---|
| H17.1 | Query-preserving quotienting is exactly factorization through the quotient in the finite fragment | A counterexample under the stated definitions |
| H17.2 | Preserving present observations does not guarantee preserving future operations | No finite counterexample can be constructed, or the proposed operation condition is redundant |
| H17.3 | Contraction cannot be inferred from equality of proposition content alone when token multiplicity is semantically relevant | Every plausible resource semantics makes the distinction irrelevant; narrow the claim |
| H17.4 | A nontrivial sufficient condition for safe contraction can be stated and independently checked | Only circular or vacuous conditions are found |
| H17.5 | The extension can be represented in CSIR without breaking existing v0.1 bundles | Existing examples/tests cannot be migrated or validated without semantic regression |
| H17.6 | A contextual/fibrational model captures a real distinction between strict and context-relative identity | The model collapses to ordinary equivalence with no explanatory gain |

## Shared test matrix

| Case | Classical FOL | Linear logic | Dependent type theory | Contextual/fibrational model |
|---|---|---|---|---|
| Nonempty-domain existential import | Standard semantics; witness term | Resource assumptions separately tracked | Witness as term of Σ/type | Witness availability indexed by context |
| Empty domain | Universal vacuity vs existential failure | Not primarily a contraction case | Empty type / no inhabitant | No local witness in empty fiber |
| Duplicate assumption | Contraction admissible | Linear vs exponential assumptions | Context discipline / structural rules | Occurrence tokens and local permissions |
| Same proposition, distinct evidence | Provenance/multiplicity external to bare FOL | Resource tokens | Distinct terms/proofs, proof irrelevance only if assumed | Distinct evidence objects over same observation |
| Quotient then future operation | Congruence required | Quotient of resource semantics | Setoid quotient / higher quotient | Fiberwise equivalence and descent |
| Context shift | Interpretation may change | Modality/resource context | Dependent transport | Pullback/reindexing along context morphism |
| Co-reference under opacity | Extensional equality vs opaque contexts | Context-sensitive permissions | Identity/path transport | Reference indexed by module |

## Formal core

### Definitions to mechanize

- `Frame`: hypotheses, protocols, observations.
- `Indist Ω x y`: existing PFT definition.
- `Protected Q`: family of queries.
- `Preserves q R`: q constant on R-classes.
- `Congruent R f`: R compatible with operation f.
- `Occurrence A`: a token distinct from its proposition/content.
- `Context`: a multiset/list of occurrences with resource annotations.
- `Contractible Γ A`: merging two A-occurrences preserves the declared judgments.
- `DistinctionLoss`: source/target relation plus declared preservation scope and certificate.

### Required proof/counterexample set

1. Factorization iff constancy on equivalence classes, for a finite quotient construction.
2. Congruence implies the induced operation on quotient is well-defined.
3. Counterexample: query-preserving quotient that does not preserve a non-congruent future operation.
4. Counterexample: two equal proposition labels but distinct linear tokens; merging changes what can be derived.
5. Safe contraction for an explicitly unrestricted/exponential resource class.
6. Context-indexed equivalence: same pair equivalent under Ω₁ but distinguishable under Ω₂.

Do not assume that a quotient exists constructively for every arbitrary relation; state setoid/quotient assumptions and constructive boundaries.

## Implementation sequence

1. Read current Semplex branch state, Lean conventions, CSIR schema and audit.
2. Add isolated `proofs/lean/Distinction.lean`; do not modify `Theory.lean` until the core is reviewed.
3. Add finite Python reference model and adversarial tests.
4. Add `experiments/SPIKE_17_REPORT.md` only after running results; never pre-fill findings.
5. Add CSIR exporter/schema proposal after three real fragments demonstrate common fields.
6. Update claims register and roadmap only after proof/test status is known.

## Acceptance gate

The spike is successful if it produces:
- one nontrivial theorem about admissible quotienting;
- one minimal counterexample to "current observational equivalence is enough";
- one explicit safe-contraction condition and one unsafe-contraction counterexample;
- a machine-checkable certificate route;
- a clear separation of established mathematics, Synesism interpretation, and novel conjecture.

A negative result is a valid outcome if it locates a precise obstruction.
