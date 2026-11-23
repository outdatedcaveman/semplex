# Higher Semantic Core: Groupoid Responses, Contexts, and Grounded Semiosis

**Date:** 2026-11-22  
**Status:** Compiling Lean formalization of a 1-groupoid response layer and typed truth/reference/evidence interfaces. This is a foundational prototype, not a completed infinity-categorical semantics or a theory of empirical reference.

## 1. New formal modules

- `proofs/lean/HigherSemanticCore.lean`
- `proofs/lean/SemanticFibrations.lean`

Both are registered in `proofs/lean/lakefile.lean`.

## 2. Why groupoid-valued semantics

The set-valued response core identifies states when their responses are equal. That is useful but can erase structure: responses may be equivalent by an admissible isomorphism without being literally equal, and a response may have nontrivial automorphisms.

A groupoid response object retains:
- response objects;
- isomorphisms between responses;
- automorphisms of an individual response;
- composition and inverse laws.

The module defines a small Groupoid structure, groupoid functors, and equivalences expressed as fully faithful hom-bijections plus essential surjectivity.

`HigherProbeSemantics` assigns a response groupoid to each probe/context and a response object to each target state. `higherSemEq` holds when responses are isomorphic at every probe. Reflexivity, symmetry, and transitivity are machine-checked.

The key example compares:
- a one-object groupoid with automorphism group Z2;
- a one-object groupoid with trivial automorphism group.

Their object shadows are identical, but there is no groupoid equivalence because their automorphism hom-types are not bijective. This formally exhibits information erased by object-only semantics.

Groupoid equivalences transport and reflect isomorphism witnesses, and their hom-bijections preserve automorphism types.

## 3. Contextual coherence

`ContextPreorder` models a refinement order on admissible contexts. `GroupoidPresheaf` assigns a common universe of response objects/arrows together with restriction maps for context refinement. It requires:
- identity restriction on objects and arrows;
- composition coherence on objects and arrows.

The common response universe is a deliberate first-stage encoding: context tags and validity conditions can be represented in the objects themselves. This avoids pretending that dependent reindexing has already been solved.

`ContextualEquivalence` adds objectwise groupoid equivalence and naturality under every context restriction, including arrow-level naturality expressed with heterogeneous equality.

This is a strict groupoid-valued presheaf prototype over a preorder, not yet an arbitrary category-valued pseudofunctor or an infinity-presheaf. The next generalization is to arbitrary small context categories, with explicit pseudofunctorial coherence rather than silently assuming strictness.

## 4. Typed semantic fibrations: reference, truth, evidence

`SemanticFibrations.lean` defines `GroundedSemiosis` with separate domains for:
- World;
- Sign;
- Claim;
- Context.

It separately types:
- `refers : Sign -> World -> Prop` (relational, not forced to be functional);
- `expresses : Sign -> Context -> Claim`;
- `satisfies : Claim -> World -> Prop`;
- `Evidence : Sign -> Context -> World -> Type`.

The soundness bridge is explicit and conditional: evidence for a sign yields satisfaction of its expressed claim at a world only when the sign's reference relation to that world holds.

Two finite countermodels are proved:
1. A claim can be satisfied while no evidence is available. Thus truth does not reduce to current evidential support.
2. A claim can be satisfied while the sign does not refer to the world. Thus satisfaction alone does not establish aboutness.

Reference is relational by design. Unique reference is an optional property, not a built-in assumption; this leaves room for ambiguity, polysemy, partial reference, and context-sensitive reference.

**Interpretive caution:** `AssertionTrue` is a particular grounded-assertion predicate combining reference and satisfaction. It is not proposed as the universal definition of truth for every mathematical, logical, social, or physical claim. The world domain may itself be a mathematical structure, social institution, physical system, or other declared target domain. The theory must not silently assume every claim has a single concrete physical referent.

## 5. Correction from independent adversarial audit

An Antigravity audit event (151825; agent attribution retained as Antigravity) identified several important defects or overstatements:

### 5.1 Evidence completeness quantifier

The previous `CompleteEvidence` predicate combined with universal soundness would have forced every state-dependent truth predicate to be constant across states. It has been corrected to validity-completeness:
`forall c, (forall s, satisfies c s) -> Nonempty (Evidence c)`.

For empirical/state-relative evidence, use `StateIndexedEvidence` in `SemanticGroundingBridge.lean`, where evidence is indexed by claim and world/state. Soundness and completeness remain distinct.

### 5.2 Quotient factorization direction

The earlier S1 sentence had the direction backwards. For an exact adequate encoder r:S->Z, the kernel of r is contained in semantic equivalence. The correct universal property is that the canonical quotient map q:S->S/≈ factors through the image of r:
`S -> im(r) -> S/≈`.

It is generally false that the encoder itself factors from the semantic quotient, because an implementation may preserve extra distinctions that do not affect protected responses. `ResponseQuotient.factorThrough` has the correct direction. The master architecture's S1 statement has been corrected accordingly.

### 5.3 Graph orientation and backtracking

The existing `EdgeWalk` in `GraphGaugeClassification.lean` traverses only from edge source to target. Consequently, its rooted path certificate models directed out-arborescences, not arbitrary undirected spanning trees with arbitrary edge orientations.

A naive extension with forward and backward steps would make uniqueness among all tree-supported walks false: a path can be extended by an edge and immediately traversed backwards. The proper general solution is a parent/depth certificate:
- every non-root vertex has a parent and parent edge;
- depth strictly decreases toward the root;
- the parent edge may be oriented either parent-to-child or child-to-parent;
- frame transport uses A(e) in the forward case and A(e)^(-1) in the reverse case;
- each tree edge is certified as the parent edge of exactly one endpoint.

This supports well-founded frame recursion without treating backtracking walks as unique paths. It remains a graph work item; the current path-decomposition theorem is conditional on the forward-only out-arborescence model.

### 5.4 Tree/chord disjointness

The current graph structure has a cover condition but no explicit disjointness proof between tree edges and chords. This must be added before identifying chord coordinates with unconstrained generators of a free group.

### 5.5 Attribution and source correction

The audit also noted that `SemanticResponseCore` no longer needs to import `ResponseQuotient`; that import has been removed. Its profile equality theorem is proved by function extensionality, not by a quotient theorem. The master architecture's corresponding description has been corrected.

## 6. HoTT/HIT environment decision

The canonical Lean 4 project remains the right place for ordinary algebra, finite models, response semantics, groupoids, and categorical interfaces. However, Lean's ordinary inductive declarations should not be presented as a full cubical HIT implementation.

The official Cubical Agda documentation explicitly supports interval/path types, Glue types, computational univalence, and higher-inductive types with path constructors. It is therefore the strongest immediate candidate for the genuine cubical/HIT track, with Lean retained as the companion environment for algebraic and theorem-heavy interfaces.

Agda 2.9.0 is now installed locally under %LOCALAPPDATA%/Semplex/Agda/2.9.0 and is not on the global PATH. GHC, Cabal, Stack, and Coq remain absent. The active project uses built-in cubical primitives; the vendored Cubical library v0.9 currently has a Glue/Equiv/Sigma mode incompatibility with Agda 2.9.0.

Official references:
- Agda Cubical language documentation: https://agda.readthedocs.io/en/latest/language/cubical.html
- Cubical Agda library: https://github.com/agda/cubical
- 1lab cubical HoTT reference: https://1lab.dev/

The planned first HIT suite is:
1. interval/path primitives and path induction;
2. circle S1 and its loop;
3. set truncation/propositional truncation;
4. homotopy quotient/classifying space BG for a finite group action;
5. pushouts and a graph realization as a 1-type;
6. univalence and equivalence induction;
7. a semantic quotient whose paths encode admissible transformations and whose higher paths encode coherence between transformations.

The Lean/Agda boundary must be explicit. Lean results can be translated or related through a stated interface; the two kernels are not assumed to share definitional equality or proof trust.

## 7. Immediate next theorem programme

1. Add a 2-groupoid layer: 1-morphisms are response isomorphisms; 2-morphisms are coherent transformations between them. Determine whether strict 2-groupoids suffice for finite gauge examples or whether bicategorical coherence is needed.
2. Generalize context preorders to small categories and groupoid-valued pseudofunctors.
3. Define a semantic quotient as a homotopy quotient/localization, retaining stabilizers and higher automorphisms.
4. Connect groupoid-valued response semantics to the graph-gauge action groupoid and prove the cycle/bouquet cases as a worked example.
5. Formalize a Cubical Agda HIT for the classifying space of a finite action groupoid.
6. Relate internal type-theoretic truth, satisfaction in a model, constructive evidence, and grounded target truth through explicit comparison maps/modalities; do not identify them.
7. Only after these interfaces are stable, attempt an infinity-topos semantics for a selected HoTT fragment.

No custom axioms or `sorryAx` are intended in the new Lean modules. Fresh full-project builds and targeted axiom audits are required before treating the additions as verified.


## 8. Follow-up graph formalization attempt

A separate parent/depth formalization was attempted in `GraphGaugeParentFrames.lean` to handle arbitrary edge orientations without path uniqueness. The intended construction is mathematically clear: define each non-root vertex's frame recursively from its parent; use A(e) when the parent edge points toward the child and A(e)^(-1) when it points toward the parent; use strict depth decrease for termination; derive the usual frame recursion for every tree edge.

The Lean recursive definition itself was accepted, but the equation-rewrite proof obligations did not compile cleanly because the generated dependent match equation was recursively unfolded by simplification. The draft and its Lake registration were removed rather than leaving an unverified module in the canonical build.

**Status:** parent/depth is the preferred mathematical design for the general-orientation case, but no machine-checked theorem is claimed yet. The previously verified `GraphGaugePathDecomposition` remains intact and conditional on forward-only out-arborescence paths. The next implementation should use an explicit `WellFounded.fix` plus a separately proved recursion equation, or a non-dependent parent-frame encoding, rather than relying on broad simplification of the recursive equation.


### 4.1 Content truth versus grounded assertion truth

The formal interface now distinguishes `ContentTrue` (satisfaction of a contextually expressed claim in a target model) from `GroundedAssertionTrue` (content truth together with the independently specified sign-to-world reference relation). This avoids defining all truth as reference: mathematical or abstract claims can be evaluated in their declared model domain, while the additional aboutness relation is required only when asserting that a particular sign is grounded in a particular target. The Boolean countermodel proves content satisfaction need not imply reference.


## 9. Action groupoids and gauge semantics

Added and registered:
- `proofs/lean/GraphGaugeActionGroupoid.lean`
- the generic action-groupoid construction in `proofs/lean/HigherSemanticCore.lean`.

For a group action G ↷ X, `actionGroupoid` has:
- objects x in X;
- arrows x -> y given by group elements g with g·x=y;
- composition induced by group multiplication;
- inverses induced by group inverses.

The theorem `orbit_quotient_eq_iff_action_arrow` proves that equality in the ordinary orbit quotient is equivalent to existence of an arrow in the action groupoid. Thus the orbit set is its 0-truncated connected-component quotient.

The theorem `actionGroupoid_loops_are_stabilizer` identifies the loop type at x with the stabilizer subgroup/type. This is the crucial information lost by replacing a homotopy quotient with an orbit set.

The graph-specific module defines the pointwise group structure on vertex gauge transformations and proves that they act on edge connections. `GaugeHomotopyQuotient` is the resulting action groupoid Conn(D,G)//G^V. The theorem `gauge_loop_space_is_stabilizer` identifies automorphisms of a connection in this groupoid with gauge transformations fixing that connection.

This is the direct categorical bridge between the semantic programme and graph-gauge work: gauge transformations are admissible presentation changes; the action groupoid is the homotopy quotient; stabilizers are semantic automorphisms. It is still a 1-groupoid construction. Higher cells between gauge transformations and their coherence remain future work.

**Precision note:** `SemanticFibrations` currently uses indexed families and relations inspired by fibrations; it does not yet construct Grothendieck fibrations or modalities in an infinity-topos. Likewise, `GroupoidPresheaf` is a strict preorder-indexed prototype over a shared response universe, not a general dependent pseudofunctor.


## 10. Finite action-groupoid witness

Added and registered `proofs/lean/FiniteActionGroupoidExample.lean`.

The group C2 represented by Boolean xor acts on Option Bool:
- the point none is fixed by both group elements, so its loop/stabilizer type has two distinct arrows;
- the two points some false and some true lie in one orbit;
- the stabilizer at some false is trivial;
- none and some false are in distinct orbits.

The proofs are machine-checked. This is a deliberately minimal example, not yet the S3 conjugation/gauge instance. It demonstrates that isotropy is object-dependent and that the 0-truncated orbit set omits information carried by the homotopy quotient.


## 11. Genuine cubical HIT setup and first constructions

A local Cubical Agda project now exists under `proofs/cubical/`:
- `%LOCALAPPDATA%/Semplex/Agda/2.9.0/agda.exe` is the verified official Windows x64 binary (archive SHA-256 recorded in the cubical README);
- no global PATH changes were made and no GHC/Cabal installation was needed;
- `proofs/cubical/semplex-cubical.agda-lib` and `verify.ps1` provide reproducible local builds.

Machine-checked Agda modules:
1. `Semplex.Cubical.Primitives`: a minimal path/refl/path-concatenation layer over Agda's cubical interval and path primitives.
2. `Semplex.Cubical.S1`: an actual higher-inductive circle with a base point and a loop path constructor.
3. `Semplex.Cubical.BGroup2Skeleton`: a higher-inductive 2-dimensional presentation skeleton for a group, with a point, one loop per group element, and 2-cells for unit, multiplication, and inverse relations.

The local project build via `agda --build-library` passes.

**Crucial limitation:** BGroup2Skeleton is not yet the full classifying space BG. Its 2-cells present the group relations, but associativity/unit/inverse coherence at the next dimension and the required 1-truncation are not yet formalized. No claim about its higher homotopy groups is made.

Toolchain investigation:
- Agda 2.8.0.2 official Windows binary crashes internally on this machine even on a simple module; the 2.8.0 binary exits with a missing-runtime status.
- Agda 2.9.0 works for the custom minimal cubical layer.
- The official Cubical Agda library v0.9 was downloaded and hash-verified, but its Prelude currently fails under Agda 2.9.0 because the Glue/Equiv import chain conflicts with the built-in Sigma cubical mode. The tested v0.9 archive was removed from the repository after the compatibility failure; the active project has no dependency on it.
- The active HIT work therefore uses the built-in cubical primitives directly. Computational univalence/Glue remains blocked pending a compatible library/toolchain combination.

This is the first actual HIT formalization in the project, but not yet the full higher-inductive semantics required by the ultimate programme.


## 12. Final verification record

- Lean full build after the action-groupoid, gauge-action, and finite C2 example modules: passed.
- Focused builds for HigherSemanticCore, GraphGaugeActionGroupoid, SemanticFibrations, SemanticGroundingBridge, FiniteActionGroupoidExample, and GraphGaugePathDecomposition: passed.
- Axiom audit over the semantic, groupoid, gauge, and finite-action theorems: no custom axioms and no sorryAx. The quotient/identity results use standard propext and Quot.sound; the classical non-separation existence result additionally uses standard classical reasoning.
- Python regression: 238 passed, 2 skipped (336 seconds). No Python source was changed in the later Agda setup.
- Cubical Agda local project: verify.ps1 / --build-library passed for the three active modules.
- git diff --check: passed.
- Temporary Lean audit files and failed Agda 2.8 toolchain copies were removed. The Agda 2.9.0 executable is outside the repository under %LOCALAPPDATA%; no global PATH changes.
- No commits, pushes, or merges.


## 13. Circle induction and the first higher-coherence obstruction

Added `Semplex.Cubical.S1Recursor`. It defines:
- a nondependent circle recursor into a carrier equipped with a point and a loop;
- a dependent circle eliminator from a family P : S1 -> Set, a base case, and a dependent path over the loop;
- explicit base and loop computation equalities, both proved by cubical path reflexivity.

The full Agda project build passes with this module included. This is stronger than merely declaring the S1 HIT: its dependent elimination interface and computation behavior are now machine-checked.

A naive nondependent recursor for BGroup2Skeleton was attempted and rejected by Agda with transport (primTransp) boundary mismatches. The draft was removed. The obstruction is substantive: 2-dimensional constructors require coherent transport over their boundaries; a record of path-valued cells with pointwise clauses is not enough. The next version must specify the dependent boundary/coherence data in the eliminator, or use the generated dependent eliminator with its exact boundary types.
