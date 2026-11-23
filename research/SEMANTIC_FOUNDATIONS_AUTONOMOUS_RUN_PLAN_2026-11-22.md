# Semantic Foundations: Autonomous Research Run Plan

**Prepared:** 2026-11-22  
**Canonical repository:** semplex\  
**Primary objective:** construct a mathematically explicit, representation-independent account of semantics that unifies reference/aboutness, truth, evidence, computational correctness, admissible transformations, and higher identity without conflating their domains.

This is a dependency-ordered programme, not a claim that the whole theory can be completed in one run. Each stage has a concrete artifact and a stopping criterion. Work should proceed autonomously within the current repository, with no commits, pushes, merges, external paid actions, or destructive changes.

## 1. Current verified foundation

### 1.1 Set-valued response semantics
- SemanticResponseCore.lean: target states, probes, responses, response profiles, semantic equivalence, exact realization, injectivity under separating probes, finite-sequence dynamic commutation.
- SemanticGroundingBridge.lean: probe restriction, underdetermination, truth preservation/reflection/adequacy, state-indexed evidence, dynamic grounding interface.
- ResponseQuotient.lean: the correct factorization direction is from the image of any exact adequate encoder to the semantic quotient.

### 1.2 Groupoid-valued semantics
- HigherSemanticCore.lean: groupoids, groupoid functors/equivalences, hom-bijections, response isomorphism equivalence, contextual groupoid presheaf over a preorder, action groupoids.
- The action groupoid's orbit set is its 0-truncation/connected-components quotient.
- The loop type at an object is its stabilizer.
- Object-only equivalence can erase automorphism groups; a one-object counterexample is machine-checked.

### 1.3 Grounding and truth interfaces
- SemanticFibrations.lean: separate world/sign/claim/context types; relational reference; context-sensitive expression; model satisfaction; indexed evidence.
- ContentTrue is satisfaction of expressed content in a declared model.
- GroundedAssertionTrue adds the independent sign-to-world reference relation.
- Evidence soundness is conditional on reference; truth is not identified with evidence.

### 1.4 Gauge case study
- GraphGaugeActionGroupoid.lean: vertex gauge transformations act on edge connections; their action groupoid is the homotopy quotient; connection automorphisms are exactly stabilizing gauge transformations.
- GraphGaugePathDecomposition.lean: transport concatenation and tree-edge recursion are derived from unique forward tree paths.
- The latter is restricted to directed out-arborescence paths. The general orientation case remains open.

## 2. Research stages and dependencies

### Stage A — Finish the 1-groupoid semantic interface
**Goal:** turn the current structures into a compositional theory of semantics-preserving translations.

Tasks:
1. Generalize the context preorder to a small category.
2. Replace strict restriction equations with explicit pseudofunctorial coherence where strictness is not justified.
3. Define natural transformations between groupoid-valued semantics and natural equivalences.
4. Prove a full-abstraction theorem for a finite context category and finite response groupoids.
5. Connect the Yoneda embedding to the response-profile principle: state exactly which category of probes is dense/separating and what object it reconstructs.

Deliverables:
- ContextCategorySemanticPresheaf.lean
- finite full-abstraction example and counterexample;
- a note stating when object-level response equivalence is sufficient and when mapping-groupoid data is required.

Stop if a proof requires an unrecorded choice of contexts or a non-faithful probe category; record the obstruction instead of assuming density.

### Stage B — Higher morphisms and coherence
**Goal:** move beyond 1-groupoids without pretending that a groupoid is already an infinity-groupoid.

Tasks:
1. Specify a strict 2-groupoid or bicategory for the finite gauge/action examples.
2. Define 2-cells between admissible transformations and prove vertical/horizontal composition laws.
3. State interchange and associativity/unitor coherence explicitly.
4. Determine which results are invariant under strictification and which require weak bicategorical coherence.
5. Define higher response equivalence as a coherent equivalence of mapping objects, not merely an equality of object sets.

Deliverables:
- a finite strict 2-groupoid module;
- an explicit counterexample to any claim that object and arrow sets alone encode all 2-dimensional semantics;
- a bridge from 2-groupoid automorphisms to higher response identity.

Do not use a strict 2-groupoid if the target example requires genuinely weak coherence; record the exact obstruction.

### Stage C — Genuine HoTT/HIT semantics
**Goal:** construct real higher-inductive types with path constructors and computational rules.

Toolchain decision:
- Keep Lean 4 for ordinary algebra, finite structures, category theory, and response semantics.
- Use Cubical Agda as the candidate environment for cubical paths, computational univalence, and HITs.
- Agda 2.9.0 is installed locally under %LOCALAPPDATA%/Semplex/Agda/2.9.0; no global PATH changes and no GHC/Cabal installation. Do not claim cubical HIT support in the Lean project: the active Cubical Agda project is separate. The Cubical library v0.9 import chain is currently incompatible with Agda 2.9.0 Glue mode, so the first HITs use built-in primitives.

Formal sequence:
1. Cubical interval/path primitives and path induction.
2. Circle S1, loop constructor, and recursion/induction principles.
3. Propositional truncation and set truncation.
4. Classifying space BG for a finite group/action groupoid.
5. Pushouts and a graph realization as a 1-type.
6. Univalence and equivalence induction.
7. Semantic homotopy quotient whose paths represent admissible transformations and whose higher paths encode coherence.

Deliverables:
- a Cubical Agda project under proofs/cubical/;
- explicit Agda library/toolchain versions and commands;
- Lean/Agda translation interfaces with no claim of shared definitional equality or shared kernel trust.

### Stage D — Truth, reference, and evidence as separate indexed structures
**Goal:** develop the current indexed interfaces into genuine categorical fibrations/modalities and model comparisons.

Tasks:
1. Model satisfaction as a predicate/fibration over claims and target structures.
2. Model evidence as a separate family over claims, states, contexts, and provenance.
3. Model reference/aboutness as a relation or span, not automatically as a function.
4. Distinguish internal truth in a type-theoretic universe, model satisfaction, proof/evidence, and empirical truth about a target.
5. Define comparison maps/modalities between these layers and state preservation/reflection conditions.
6. Prove soundness and completeness only relative to explicit assumptions; do not make empirical completeness a default.
7. Add partial reference, ambiguity, polysemy, error, and misrepresentation examples.

Deliverables:
- categorical fibration definitions and pullback/reindexing;
- a truth/evidence/reference comparison diagram;
- countermodels showing which implications fail absent grounding premises.

### Stage E — Computational/logical semantics
**Goal:** show how programs, proofs, compilers, and learned representations participate in the same framework.

Tasks:
1. Treat operational, denotational, and contextual semantics as different probe categories.
2. Define a compiler translation and prove response preservation/reflection.
3. Distinguish proof objects as evidence from truth in a model.
4. Formalize a resource-indexed semantic equivalence and approximate adequacy.
5. Connect implementation update commutation to finite and eventually infinite interaction traces.
6. Relate circuit/algorithm distillation to semantic quotienting without assuming the quotient is the smallest implementation.

Deliverables:
- compiler-correctness example;
- proof/evidence model with explicit soundness assumptions;
- resource-enriched response semantics.

### Stage F — General graph-gauge equivalence
**Goal:** finish the graph case without the current orientation restriction.

Tasks:
1. Add explicit tree/chord disjointness.
2. Use a parent/depth certificate for arbitrary edge orientations; define frame recursion with inverse labels for reversed parent edges.
3. Implement the recursion using explicit WellFounded.fix and a separately proved equation, avoiding broad simplification of recursive definitions.
4. Define reduced walks or a path category where immediate backtracking is handled correctly.
5. Identify chord coordinates with a free-group representation object.
6. Prove full faithfulness, essential surjectivity, and isotropy/stabilizer correspondence.
7. Generalize from groups to groupoids only after the group case is complete.

Deliverables:
- a general-orientation rooted-tree frame theorem;
- a Lean equivalence between connection/gauge action groupoid and representation/conjugation action groupoid;
- explicit finite S3 and multi-loop tests.

## 3. Verification protocol

For every meaningful change:
1. Focused lake build <Module>.
2. Axiom audit with #print axioms for the principal theorems.
3. Full lake build.
4. python -m pytest -q when Python code/artifacts or cross-module interfaces change.
5. git diff --check.
6. Inspect changed files and ensure temporary audit files are removed.
7. Record exactly which claims are machine-checked, conditional, or still design-level.

Axiom policy:
- standard Lean principles such as propext and Quot.sound may appear when their use is understood and documented;
- no custom axioms or sorryAx in verified results;
- never describe a theorem as axiom-free if its audit shows otherwise.

## 4. Operating constraints

- Work directly in the canonical repository; do not delegate local coding to Codex.
- Treat Antigravity/Gemini outputs as external reviews, not as proof. Reproduce findings locally.
- Do not edit or merge isolated Antigravity worktrees without explicit review.
- No commits, pushes, merges, package installations, paid actions, or destructive cleanup without explicit approval.
- Use long-running shell processes for deterministic builds/tests and inspect their outputs before claiming completion.
- The remote terminal exposes bounded waits and background process handles; a shell process can continue while work proceeds, but this does not mean a reasoning agent continues independently after the conversation turn ends. Never claim unattended research progress that has not actually occurred.

## 5. Next concrete execution order

1. Finish audit and full build for the newly added action-groupoid/gauge bridge.
2. Create a finite S3 action-groupoid example and explicitly compute orbit representatives and stabilizers.
3. Prove the first finite full-abstraction theorem for groupoid-valued responses.
4. Specify a strict 2-groupoid for the same finite action and test the coherence laws.
5. Prepare Cubical Agda environment specification; only install after confirming system/package conditions.
6. Formalize the first HIT, BG, and connect its loop space to the stabilizer theorem.
7. Return to general-orientation graph gauge classification.

The programme's success criterion is not the number of files or definitions. It is a chain of explicit constructions and theorems in which reference, truth, evidence, computational realization, and higher identity are related without being conflated.


## 6. Status at end of this run

### Completed/verified
- Set-valued probe/response semantics and exact realization interfaces.
- Truth preservation, reflection, and adequacy; reference/content truth/evidence separation prototypes.
- Groupoid-valued response semantics, action groupoids, orbit-set 0-truncation, and stabilizer loop identification.
- Graph gauge action groupoid and its stabilizer correspondence.
- Finite C2 action example with distinct isotropy at fixed and free-orbit objects.
- Genuine cubical S1 HIT, its dependent eliminator with base/loop computation equalities, and the group classifying-space 2-skeleton typechecked in Agda 2.9.0.

### Partially completed / conditional
- Contextual groupoid presheaf remains a strict preorder-indexed prototype.
- SemanticFibrations is indexed-family structure, not yet actual Grothendieck fibrations/modalities.
- BGroup2Skeleton lacks higher coherence and 1-truncation; it is not yet BG.
- Graph path classification still relies on a forward rooted-tree certificate; arbitrary edge orientations and full equivalence remain open.
- Cubical library Glue/univalence is blocked by Agda 2.9.0 compatibility with Cubical library v0.9.

### Next execution order
1. Finite S3 conjugation/action-groupoid example and compute centralizers/stabilizers.
2. Finite full-abstraction theorem for groupoid-valued response semantics.
3. Strict 2-groupoid or bicategory with explicit interchange/coherence for the same finite example.
4. Add 3-dimensional associativity coherence to the classifying-space HIT and establish the 1-truncation; first derive the exact dependent eliminator boundary conditions exposed by the failed naive recursor.
5. Resolve Glue/univalence library compatibility.
6. Return to arbitrary-orientation graph-gauge classification.
