# Module-indexed resource and admissibility semantics

**Status:** design proposal, not formalized or validated.  
**Purpose:** define the next semantic layer without changing the current P091 all-linear contract prematurely.

## 1. Problem

P091 currently describes one ordered resource context and one formula-rank map. Synesism's module idea is richer: distinct modules may expose different observations, protect different operations, and retain different subsets of distinctions. A transformation can therefore be admissible in one module and inadmissible in another.

A global resource profile that forgets module visibility can conceal exactly the distinctions the module architecture is supposed to preserve. The extension should make module scope explicit rather than adding an informal label to existing tokens.

## 2. Proposed data

Let M be a set of module identifiers and O a finite set of resource-occurrence tokens.

For each occurrence o:
- token(o): stable occurrence identity;
- rank(o): formula/resource rank;
- mode(o): linear or persistent;
- origin(o): finite provenance set of source tokens;
- visible(o,m): whether module m can observe or use o.

Each module m has a contract:
- Obs(m): protected observations;
- Ops(m): protected operations and relations;
- Loss(m): explicitly permitted distinctions to discard;
- Cap(m,A): capacity for formula/rank A;
- Eq(m): the equivalence relation that the module itself treats as indistinguishable.

The module-local context is Γ_m = {o ∈ O | visible(o,m)}. Its aggregate usage is:

    U_m(A) = Σ { usage_m(o) | o ∈ Γ_m and rank(o) = A }

For the current P091 adapter, all occurrences in Γ_m must be linear and each coordinate must have usage at most one. Persistent resources remain outside this adapter.

## 3. Module-local admissibility

A transformation q : X → Y is admissible in module m only relative to the declared contract.

1. **Observation descent.** Every protected observation obs ∈ Obs(m) factors through q: there is an obs' such that obs = obs' ∘ q.
2. **Operation descent.** Every protected operation op ∈ Ops(m) has a corresponding op' satisfying q ∘ op = op' ∘ q^k. Equivalently, the kernel equivalence of q must be a congruence for the protected operations.
3. **Resource capacity.** The transformed module profile remains within Cap(m,A), or the exact excess/loss is explicitly permitted by Loss(m).
4. **Provenance accounting.** If q identifies or merges occurrences, the result retains the union or multiset of their source tokens. Provenance is not silently erased merely because the semantic quotient is valid.
5. **Declared loss only.** Any distinction removed by q must be in the module's declared Loss(m), or be provably irrelevant to every protected observation and operation.

This is not yet a new logical principle. Observation descent and operation descent are standard quotient/congruence conditions. The candidate extension is their explicit composition with occurrence-level provenance and resource budgets.

## 4. Cross-module compatibility

A module morphism F_mn : X_m → X_n expresses how one module's representation is interpreted by another. A family of transformations q_m is compatible when the following square commutes:

    X_m  --F_mn-->  X_n
     |               |
    q_m             q_n
     |               |
     v               v
    Y_m  --F'_mn--> Y_n

That is, q_n ∘ F_mn = F'_mn ∘ q_m, and the induced maps preserve the protected observations and operations on both sides.

Global admissibility requires admissibility in every module in scope plus compatibility for every declared inter-module map. A quotient that is safe in module m but destroys a distinction protected by module n is not globally admissible.

For modules over a shared underlying object, a conservative global indistinguishability relation is the intersection of the local relations:

    x ≈_global y  iff  for every m in scope, x ≈_m y.

This prevents local indistinguishability in one perspective from being mistaken for identity across all perspectives. The exact construction may need a fibration or indexed category if modules have different carriers rather than a common underlying object.

## 5. Composition theorem to target

Suppose q : X → Y and r : Y → Z are admissible in every module in scope, and both families commute with the declared inter-module maps. Then the composite r ∘ q should be admissible provided:
- protected observations and operations are closed under the induced descent;
- provenance maps compose without losing source identities;
- resource budgets are monotone under the declared loss policy;
- any intermediate distinction discarded by r was already either preserved by q or explicitly licensed by the relevant module contract.

The observation/operation part follows standard quotient descent. The provenance and resource-budget clauses are the substantive additions to test. This theorem must be proved, not assumed.

## 6. Structural boundaries already exposed by C-20/P091

### Renaming

M413's Ren permits arbitrary variable maps, not only bijections. A non-injective renaming can identify two source variables and aggregate their usage counts at one target coordinate. It is therefore not a mere permutation and need not preserve a linear capacity bound.

The P091 permutation theorem should assume an explicit permutation of aligned token/usage pairs. Python's explicit token-to-variable bijection is the appropriate witness; Lean's ordered zip is a canonical convention only when both lists share the same order.

### Substitution

M263's instUsageFull law makes substitution usage depend on how many times the substituted variable occurs in the body. M264's k=0 and k=2 examples witness weakening and contraction when the argument carries resources. A substitution that is not linear in the substituted variable can erase or duplicate resource usage.

The vector bridge should state the exact transformation law. It must not claim unconditional preservation of a linear profile.

### Persistent resources

Semplex already has a minimal persistent-capacity semantics: a persistent occurrence can supply any finite demand, persistent contraction preserves support and provenance, and linear contraction can lose one unit of capacity. This is stronger than a bare ResourceMode enum, but it is still not a full object-language exponential modality. There is no typing/sequent rule for promotion or dereliction, no explicit two-zone substitution theorem, and no categorical comonoid semantics for !. P091 therefore continues to reject persistent contexts rather than silently treating this minimal capacity model as a full exponential.

## 7. Relation to established frameworks

- **Representation independence and data abstraction:** Mitchell (POPL 1986) already relates implementation equivalence to correspondence between observable operations. DAP cannot claim that requirement as new.
- **Relational parametricity:** Reynolds (1983) generalizes homomorphisms to relations to capture abstraction and representation independence. Module contracts should be compared with logical relations and parametricity.
- **Abstract interpretation:** Galois connections already provide a compositional framework for sound, lossy abstraction. DAP must identify what provenance/resource certificates add beyond abstraction and concretization maps.
- **Indexed/fibred semantics:** if modules have genuinely different carriers and local views, a family of semantic categories/fibres with reindexing functors may be more faithful than a flat product of module labels.

The potential contribution is not “modules preserve their own observations.” That is established. It is the possibility of a mechanically checked, compositional certificate that combines module-local observational descent, operation congruence, occurrence provenance, and resource-capacity accounting across representation changes.

## 8. Minimal implementation sequence

1. Add a module identifier and visibility relation without changing the existing ResourceOccurrence contract.
2. Define ModuleContract and module-local profile aggregation as a separate layer.
3. Add a two-module counterexample: a merge admissible in one module but rejected in the other.
4. Prove module-local admissibility and cross-module square commutation in Lean.
5. Prove composition of module-indexed certificates.
6. Add property-based Python tests for module visibility, provenance unions, and local/global equivalence.
7. Only then consider persistent resources, backed by a formal ! semantics.

**Do not** extend the current P091 adapter to persistent or module-indexed contexts by silently relaxing its all-linear assumptions. Preserve the finite all-linear result as a clearly delimited base case.
