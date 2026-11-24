# Semplex–Synesism: culmination research campaign

**Started:** 2026-11-21  
**Status:** research programme and verification plan; proposed laws are not theorem claims  
**Repositories:** Semplex and Synesism  
**Execution policy:** sequential, BelowNormal priority, resource-gated; no commits or pushes

## 1. Objective

Advance toward a representation-independent account of admissible transformations: a system in which distinctions, occurrence identity, resource usage, semantic observations, and transformation permissions are explicit, and in which preservation claims are accompanied by machine-checkable certificates.

The immediate target has been sharpened by prior-art review. Wood and Atkey (2021, 2022) already establish semiring-vector/matrix usage transport, resource-aware renaming and substitution environments, and compositional linear maps; Wood's 2024 thesis broadens the framework to additional modalities. Therefore the matrix transport law is not our novelty target.

> Formalize the precise relationship between Synesism C-20/P091 and the established usage-aware environment framework, then determine whether Semplex can add a genuinely stronger, compositional certificate interface for occurrence identity, provenance, protected observations/operations, and heterogeneous module transformations.

This is not yet a universal ontology/epistemology, a complete logic, or a proof that every meaningful transformation is resource-conserving. The project must preserve that distinction.

## 2. Existing verified foundations

### Synesism
- M263: recursive scoped term syntax, binders, usage accounting, and instantiation law.
- M264: beta usage preservation for the exact-one-use case, plus explicit zero-use and two-use witnesses.
- M265: partial typing system; no typed application rule and no full subject-reduction theorem.
- M413: parallel renaming/substitution, identity, four fusion laws, and reduction closure.
- P0C20UsageVectorBridge: finite-vector/list serialization in de Bruijn order, coordinate/rank and length correspondence, instantiation usage law, and vector images of M413 fusion equations.

### Semplex
- P091: finite all-linear adapter from C-20 usage vectors to resource occurrence tokens.
- Python accepts an explicit token-to-variable bijection and validates provenance, rank alignment, nonnegative counts, and capacity.
- Lean proves a positional aggregate capacity bound and permutation-invariance results for explicitly aligned context/profile permutations.
- The adapter intentionally rejects persistent occurrences. It is not a full linear logic, a derivation calculus, or a cross-language equivalence.

## 3. Known algebra of transport and the actual gap

The matrix semantics is established prior art, not a proposed new theorem. Wood–Atkey 2022 defines resource-aware environments through linear maps between usage modules and explains their matrix representation. For row-vector profiles, renaming/substitution acts by right multiplication; composition follows from composition of linear maps. Their examples explicitly represent duplication, weakening, and exchange. The present work should treat that framework as a baseline and seek a checked translation or a demonstrable extension.

Let a finite source context have positions I and a target context have positions J. A usage profile is a vector u : I → ℕ.

### Renaming

For a renaming r : I → J, define its incidence matrix:

R_r(i,j) = 1 if r(i)=j, and 0 otherwise.

The candidate transport is:

(u · R_r)(j) = Σ_{i∈I, r(i)=j} u(i).

This is intentionally defined for non-injective renamings: when several source variables are identified, their usage counts add. Bijective renaming is the permutation-matrix special case. The current Lean paired-permutation theorem covers only that special case.

### Parallel substitution

For a substitution σ : I → Tm(J), define:

M_σ(i,j) = number of occurrences of variable j in σ(i).

The candidate usage law is:

usage(sub σ t) = usage(t) · M_σ.

For composable substitutions σ : I → Tm(J) and τ : J → Tm(K), the expected composition law is:

M_(sub τ ∘ σ) = M_σ · M_τ.

The identity substitution should yield the identity matrix. Renaming should be the special case of substitution by variables.

These equations are standard consequences of the usage-aware environment perspective and must not be claimed as novel. The local research task is to prove that the concrete C-20 vector/list serialization and P091 occurrence-token adapter instantiate the same structure, or to find the precise mismatch. A useful local proof would establish a checked representation correspondence, not rediscover matrix composition. Particular care is needed for C-20's context-indexed de Bruijn coordinates, the Lean positional adapter, and Python's arbitrary explicit bijection.

### Binder condition

A top-level usage equation is insufficient unless it is stable under lambda abstraction. The required commuting square is:

usage(ren/sub (lam b)) = popU(usage(ren/sub (body b)))

with the appropriate lifted map on the body context. The proof must show that the newest bound coordinate is discharged while all older coordinates are transported consistently.

## 4. Occurrence provenance and the P091 boundary

A usage matrix aggregates counts. P091 additionally identifies resource occurrences by stable tokens and provenance trails. These are not interchangeable data.

The desired bridge must distinguish:
- a source occurrence token;
- its source variable position;
- target variable positions reached by substitution;
- multiplicity of each target occurrence;
- provenance of the transformed occurrence(s);
- resource mode and admissibility contract.

A bijection is valid only for the all-linear positional adapter. Under non-injective renaming, multiple source positions may contribute to one target coordinate. Under substitution, a source occurrence may disappear (zero count) or contribute multiple times. A future adapter must represent this as a relation or weighted incidence map, not falsely force it into a bijection.

A candidate occurrence transport can record a finite multigraph from source tokens to target occurrence tokens, with edge multiplicities and inherited origin trails. Whether such expansion is permitted depends on the resource mode and protected operations. The graph model is proposed, not implemented.

## 5. DAP as resource-indexed observational congruence and certificate

The first formal design is recorded in `research/DAP_RESOURCE_INDEXED_OBSERVATIONAL_CONGRUENCE.md`. Its core proposal is contextual: two representations are equivalent only if no well-typed, resource-admissible context can distinguish them through a protected observation. This is a resource-indexed instance of the established observational-congruence idea, not a novelty claim by itself.

For a transformation T : X → Y, declare:
- protected observations Q;
- protected operations F and the admissible one-hole contexts they generate;
- resource permissions/capacities and a usage-aware environment map;
- data lineage (source dependencies and alternative/joint derivations);
- action lineage (observable transformation events, including fusion/splitting);
- permitted loss or abstraction.

A certificate should establish, where applicable:
1. which observations factor through T or are preserved up to a declared relation;
2. which operations commute with T or are simulated/bisimulated;
3. which source distinctions are identified or erased;
4. whether usage is conserved, consumed, expanded, or abstracted;
5. how source-data provenance and transformation-action provenance are transported;
6. the precise domain and side conditions of the guarantee;
7. a counterexample or explicit loss report when preservation fails.

The first benchmark remains beta reduction, using M264's exact-one-use theorem and its zero-use / two-use counterexamples. Semplex should encode the contract and its witnesses, not duplicate the underlying Agda arithmetic. The eventual checker must compose certificates only when their intermediate observation, resource, provenance, and operation interfaces are compatible. The system-level architecture and implementation map are recorded in `research/ULTIMATE_COMPILER_ARCHITECTURE.md`; the next practical vertical slice is a finite resource-aware LTS quotient checked by the existing `kernel_lts` plus a new independent resource kernel.

## 6. Persistence: compare before extending

ResourceMode.PERSISTENT is currently an external reusable-context classification, not an object-language exponential !A. Wood–Atkey 2022 already experiments with a duplicability combinator that captures discardability and unbounded duplication; Wood's 2024 thesis develops a broader semiring-annotated framework including S4-style modality and Linear Logic.

A future extension must therefore identify a gap relative to that work, not merely add a comonoid or exponential label. Investigate whether P091's token provenance and DAP's protected-operation contracts can be integrated with graded modalities and promotion side conditions without losing the source identity of reused resources.

Do not implement persistence as a Boolean switch or claim a linear-logic semantics before the comparison and laws are explicit.

## 7. Verification campaign

Run sequentially:
1. focused Semplex distinction tests;
2. fast Semplex test suite;
3. complete Semplex suite with verbose per-test output;
4. Lean compilation of all core formal modules and all corresponding axiom audits;
5. targeted Agda checks for M264, M263 vector bridge, M265 typing, and M413 substitution;
6. incremental Agda experiment sweep, including pinned negative probes;
7. Agda C-3 sweep;
8. Synesism preflight, milestone, bibliography, citation, register, atlas, vacuity, specification, frontier, dead-end, pinned, and local-verification checks;
9. both repositories' diff and JSON integrity checks.

Every check is sequential. Agda must never be run concurrently inside the WSL VM. The resource gate delays the next step while CPU is high or available memory is below 25%. This gate does not throttle a running process; per-step timeouts and BelowNormal scheduling are separate safeguards.

## 8. Research integrity and stopping rules

- No sorry, postulate, unsafe escape hatch, or hidden axiom may be introduced to make a theorem compile.
- Every theorem must be checked from its actual source module and dependencies.
- A successful compile is not a claim of novelty, soundness of the intended interpretation, or axiom-freedom.
- A failed expected-negative probe is a result only when its diagnostic matches the pinned reason.
- Do not rewrite milestones, claims registers, or progress summaries merely to make them green. Update them only after independently verified evidence.
- No commit, push, destructive cleanup, process termination outside the research runner, or modification of unrelated user files without separate authorization.
- If resource checks remain unsafe, wait rather than forcing execution.
- If the full sweep is too long, preserve its exact progress and report checked/unchecked scope rather than marking a partial sweep green.

## 9. Success criteria for this campaign

A strong outcome is not “everything passes.” It is:
- a trustworthy baseline of what currently compiles and what does not;
- a localized diagnosis of the previous slow-suite failure;
- no silent loss of provenance or false bijection assumptions;
- a checked translation between C-20/P091 and Wood–Atkey's usage-aware environment semantics, or a precise counterexample delimiting the translation;
- a compositional DAP certificate interface that demonstrably adds provenance/observation guarantees beyond existing usage-aware environments and representation-independence methods;
- explicit counterexamples and narrowed contracts where it does not;
- an updated, evidence-backed research roadmap distinguishing HAVE, PROPOSED, and OPEN.

The culmination sought is a compositional, proof-carrying theory of admissible transformations. This campaign can move toward it; it cannot assume it has already been achieved.
