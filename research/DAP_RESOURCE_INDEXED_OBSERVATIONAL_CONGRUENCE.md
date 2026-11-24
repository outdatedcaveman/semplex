# DAP: resource-indexed observational congruence and transformation certificates

**Date:** 2026-11-21  
**Status:** formal design proposal; no new theorem or novelty claim  
**Depends on:** Semplex DAP / P091; Synesism C-20 M263/M264/M413

## 1. Why this is the next target

The earlier proposal to define usage transport by matrices is already covered by Wood–Atkey's semiring-annotated environment framework. Provenance semirings, coalgebraic action provenance, and proof-carrying transformation certificates also have direct prior art.

The more precise open question is whether these structures can be integrated into a single *resource-indexed observational congruence* and a compositional certificate calculus. The goal is not merely to say that an observable is preserved by a transformation. It is to specify which contexts are permitted to test the representation, what resources those contexts may consume, which data and actions must remain traceable, and what losses are explicitly allowed.

This note gives a formal target for that integration. Every construction below is proposed until formalized and checked.

## 2. Signatures, observations, and contexts

Let a representation be a many-sorted algebraic structure:

- S is a family of carriers, one for each sort;
- Σ is a typed signature of operations, with specified arities and source/target sorts;
- O is a family of protected observations, each a typed map from a carrier to an observation domain;
- R is a resource annotation structure, initially a partially ordered semiring or posemiring;
- P is a provenance domain for source identities and transformation actions.

A one-hole context is a well-typed expression built from Σ with exactly one distinguished hole of a specified sort. Context composition is substitution into that hole. The identity context is the hole itself.

A resource-indexed context additionally carries an annotation describing its demand on free inputs. The admissibility relation is supplied by an environment or linear map in the sense of Wood–Atkey: a source budget must be sufficient for the target context's demand. The exact orientation of vectors and matrices must be fixed once and reused consistently.

Let observational equivalence be:

x ≈O y  iff  o(x) = o(y) for every protected observation o in O.

This is generally not guaranteed to be a congruence: an operation context may distinguish two objects that the immediate observations do not.

### 2.1 Existing Semplex components to reuse

The repository already contains several relevant components, but they are not yet one DAP certificate system:
- cerp/distinction.py defines finite resource occurrences, modes, provenance trails, capacity checks, and the P091 Python adapter. Its resource checks are ordinary Python functions, not yet an independent trusted-kernel judgment.
- cerp/lts.py performs untrusted search for trace equivalence, completed-trace equivalence, bisimulation, distinguishing formulas, parallel contexts, deadlock paths, and bisimulation quotients.
- cerp/kernel_lts.py independently checks finite bisimulation relations, HML distinguishing formulas, trace certificates/witnesses, context deadlock, and reachable-deadlock paths.
- cerp/ledger.py records claims, warrants, assumptions, evidence dependencies, and weakening of derived warrants.
- cerp/pipeline.py demonstrates a bounded master pipeline for F0 Boolean artifacts, with explicit scope boundaries and kernel-checked translations.

The immediate implementation strategy should connect these existing components, not create a competing LTS, ledger, or resource calculus. The missing seam is a typed certificate envelope whose checker validates the resource, observation/context, provenance, and ledger dependencies together. In particular, resource-profile checking must be moved behind an independent kernel boundary before it is treated as proof-carrying evidence.

## 3. Resource-indexed contextual equivalence

Define:

x ≈O,Σ,R y

iff for every well-typed, resource-admissible one-hole context C and every protected observation o whose domain accepts C[x] and C[y],

o(C[x]) = o(C[y]).

This definition is intentionally contextual. It asks whether any permitted continuation can distinguish x and y, not merely whether the current observation set distinguishes them.

### Expected elementary properties

Subject to the context class containing the identity context and being closed under composition:
1. ≈O,Σ,R is reflexive, symmetric, and transitive.
2. It is compatible with every operation whose argument contexts are admitted by the resource discipline.
3. It is contained in immediate observational equivalence, because the identity context is allowed.
4. It is the largest congruence, among congruences compatible with the admitted context class, that is contained in ≈O.

The fourth item is the familiar observational-congruence construction from programming-language semantics. It is not claimed as new. The resource-indexed restriction is a parameterization that must be compared carefully with quantitative and substructural contextual equivalence.

### Important qualification

If the admissible context class is not closed under composition, or if resource budgets are context-sensitive in a way that breaks closure, the expected congruence property may fail. That failure is a useful falsifier: the system must either strengthen its admissibility rules or weaken the congruence claim.

### Direct prior art: resource transition systems

Dal Lago and Gavazzo (FSCD 2021) already construct resource transition systems whose states carry reusable programs and linear values, and prove trace equivalence sound and complete for contextual equivalence in a linear higher-order calculus with algebraic effects and explicit copying. This is a much more developed instance of resource-sensitive contextual equivalence than the abstract definition above. The current proposal must be treated as a possible generalization/integration with P091 provenance and module-indexed transformation certificates, not as a new contextual-equivalence principle. Semplex's existing LTS and kernel_lts modules should be compared directly with their resource transition systems.

## 4. Transformation admissibility

Let T : S → S' be a typed representation transformation. A certificate should declare at least:

1. **Observation contract.** Which protected observations factor through T, commute with T, or are preserved only up to a stated relation?
2. **Operation contract.** Which operations are preserved as homomorphisms, simulations, or bisimulations?
3. **Resource contract.** Which environment/linear map relates source budgets to target demands, and which inequality or relation proves capacity sufficiency?
4. **Data provenance.** Which source occurrences jointly or alternatively contribute to each target occurrence?
5. **Action provenance.** Which transformation actions were applied, fused, split, reordered, or abstracted?
6. **Loss declaration.** Which distinctions, observations, operation laws, or provenance details are intentionally discarded?
7. **Proof evidence.** Machine-checkable witnesses for the obligations above, with explicit assumptions and axioms.

A quotient transformation is admissible for an observation family only if the observations factor through the quotient. To preserve operations, its kernel must be a congruence for the protected signature. The contextual relation above is the candidate criterion when immediate observational equivalence is too coarse.

For non-quotient transformations, use typed relations or simulations rather than pretending every transformation is a quotient map.

## 5. Two provenance layers

A flat list of origin IDs is insufficient for general compositional provenance.

### 5.1 Data lineage

Use a provenance-semiring-style annotation where:
- addition records alternative derivations;
- multiplication records joint dependencies;
- source tokens are indeterminates;
- semiring homomorphisms project the full lineage to coarser views such as Boolean support, derivation counts, or cost.

This follows the established Green–Karvounarakis–Tannen framework. The existing Semplex origins tuple is not equivalent to such a polynomial.

### 5.2 Action lineage

For transformations that fuse, split, eliminate, or reorder internal nodes, source-data lineage alone does not say which computational actions were performed. Use an action trace or coalgebraic observation layer, with a relation/bisimulation connecting source and target action sequences under an explicit abstraction map.

Tian–Liu (2026) provides a close comparator for action-reflective coalgebra and non-injective AI-compiler rewrites. DAP must identify a broader or more general requirement before claiming an extension.

The certificate must relate the two layers: data lineage explains which source inputs contribute; action lineage explains which transformations and operations produced the target representation.

## 6. Certificate composition

For composable transformations S0 --T1--> S1 --T2--> S2, a certificate composition operation is only defined when the intermediate contracts are compatible.

A candidate certificate record is:

C(T) = (E, Q, F, D, A, L, W)

where:
- E is the resource-aware environment map/relation;
- Q is the observation contract;
- F is the protected-operation contract;
- D is data-lineage evidence;
- A is action-lineage evidence;
- L is the declared loss profile;
- W is the collection of proof witnesses and assumptions.

Composition should:
- compose E using the established linear-map/environment composition law;
- compose Q only where the intermediate observation interfaces match;
- compose F using homomorphism/simulation compatibility;
- compose D through provenance-semiring substitution/homomorphisms;
- compose A through a valid action-abstraction/bisimulation composition theorem;
- accumulate L without hiding a loss at an intermediate stage;
- combine W into a certificate checked independently of the transformation implementation.

This is a design sketch, not a proved operation. In particular, weak bisimulations do not compose automatically in every setting; the chosen relation and abstraction notion must be stated precisely.

Garchery's proof-carrying logical transformations already provide modular certificates and certificates with holes. DAP must reuse that insight and show that its resource, data/action provenance, and observational contracts add a substantive semantic guarantee.

## 7. Minimal countermodels that the formalization must pass

1. **Immediate observation is insufficient.** Two values have equal immediate observations but an admitted operation context distinguishes them. The contextual congruence must keep them separate.
2. **Resource insufficiency.** Two representations are observationally equivalent, but a target context demands more linear capacity than the source budget permits. The certificate must reject the transformation.
3. **Lineage collapse.** Two derivations produce the same target value. Boolean support says only that the value exists; the protected provenance polynomial must distinguish the derivations.
4. **Action erasure.** A graph rewrite preserves final values but erases an intermediate action that a protected postprocessor needs. Value-only correctness must pass while the action-provenance contract fails.
5. **Incompatible composition.** T1 preserves one observation interface, but T2 assumes another that T1 did not provide. The checker must refuse to compose the certificates.
6. **Declared loss.** A transformation intentionally discards a distinction not used by any protected observation or operation. The certificate may accept it only if that loss is explicitly authorized.
7. **Persistent misuse.** A persistent occurrence is duplicated by the transformation while the current all-linear P091 contract is active. The adapter must reject it rather than silently upgrading the resource mode.

## 8. Research sequence

1. Formalize finite many-sorted signatures, observations, and typed one-hole contexts.
2. Define a finite resource-indexed context class and prove closure under composition for the chosen resource semantics.
3. Prove the elementary resource-indexed observational-congruence theorem, explicitly labeling it as a standard contextual-equivalence result.
4. Formalize a quotient/admissibility checker and the countermodels above.
5. Define data-lineage annotations and action-lineage traces as distinct types.
6. Define certificate compatibility and composition; prove soundness and associativity up to certificate equivalence.
7. Connect the resource component to Wood–Atkey environments and P091.
8. Compare the full result against provenance semirings, Tian–Liu coalgebraic provenance, Garchery proof certificates, representation independence, abstract interpretation, and contextual equivalence.
9. Make a novelty decision only after the comparison: new theorem, useful integration, or known combination.

## 9. Novelty and scope discipline

The following are not novelty claims:
- matrix/semiring usage transport;
- generic simultaneous renaming and substitution;
- semiring provenance for data transformations;
- observational congruence as the largest congruence below contextual equivalence;
- bisimulation/action traces for preserving observations through graph fusion;
- independent checking and composition of proof certificates.

The only possible contribution under investigation is a formally specified integration of these structures into a resource-indexed, provenance-aware, module-indexed admissibility interface with a sound compositional checker. It may turn out to be a useful engineering synthesis rather than new mathematics. That outcome is acceptable if the guarantees and limits are precise.
