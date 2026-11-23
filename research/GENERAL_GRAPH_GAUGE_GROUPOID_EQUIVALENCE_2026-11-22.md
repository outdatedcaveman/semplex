# General connected-graph gauge groupoid theorem
Date: 2026-11-22
Status: mathematical theorem and proof plan; graph-generic path covariance is Lean-verified, full groupoid equivalence remains to be formalized.

## 1. Setting

Let Gamma be a connected graph regarded as a 1-dimensional CW complex. Fix a base vertex r, a spanning tree T, and an orientation convention for every geometric edge. Let G be any group.

A connection A assigns an element A(e) in G to each oriented edge, with A(e-bar) = A(e)^(-1). A vertex gauge is a function g : V(Gamma) -> G, acting by
A^g(e : u -> v) = g(v) A(e) g(u)^(-1).

Let Conn(Gamma,G) be the set of connections. Its gauge action groupoid has connections as objects and gauges g with A^g = B as arrows A -> B.

The fundamental group Pi_1(Gamma,r) is free for a graph. Holonomy defines a representation
rho_A : Pi_1(Gamma,r) -> G.
A gauge transformation changes it by basepoint conjugation:
rho_(A^g)(ell) = g(r) rho_A(ell) g(r)^(-1).

The target groupoid is the conjugation action groupoid
Hom(Pi_1(Gamma,r),G) // G.

## 2. Theorem

**Spanning-tree gauge groupoid equivalence.**
For every connected graph Gamma, every group G, and every choice of base vertex and spanning tree T, the holonomy functor is an equivalence of groupoids:
Conn(Gamma,G) // G^V  ~=  Hom(Pi_1(Gamma,r),G) // G.

This is stronger than a bijection between gauge-equivalence classes. It preserves arrows and isotropy groups.

Consequently, for every connection A,
Aut_(Conn//G^V)(A) ~= C_G(rho_A(Pi_1(Gamma,r))),
the centralizer of the entire holonomy image, not merely the centralizer of one loop.

## 3. Constructive proof

For every vertex v, let p_v be the unique tree path from r to v. Let P_A(v) be its ordered parallel transport. For every non-tree edge e:u->v, the path
ell_e = p_u Â· e Â· reverse(p_v)
is a fundamental loop. The loops ell_e, one per chord, form a free basis of Pi_1(Gamma,r).

**Functoriality.** For any path p:u->v, path transport satisfies
P_(A^g)(p) = g(v) P_A(p) g(u)^(-1).
For loops at r this is conjugation by g(r), so holonomy defines a functor to the conjugation action groupoid.

**Full faithfulness.** Fix A,B and a conjugation arrow k such that
rho_B(ell) = k rho_A(ell) k^(-1) for every based loop ell.
There is exactly one gauge transformation inducing k. It is
g(v) = P_B(v) k P_A(v)^(-1).

For a tree edge u->v, the unique-path recursion for P_A and P_B gives
P_A(v) = A(e) P_A(u) (because later edges multiply on the left), and similarly for B. Substituting the formula for g proves
B(e) = g(v) A(e) g(u)^(-1).
For a chord e:u->v, this edge equation is equivalent, after multiplying by the tree transports, to the conjugacy equation for the fundamental loop ell_e. Since the chord loops freely generate Pi_1, the assumed representation conjugacy supplies every chord equation. Thus g is a gauge arrow A->B.

Uniqueness follows because any such gauge arrow must satisfy the tree-path transport equation
P_B(v) = g(v) P_A(v) k^(-1),
which forces the displayed formula at every vertex.

Hence the map on each hom-set is bijective: full and faithful.

**Essential surjectivity.** Given any representation rho:Pi_1(Gamma,r)->G, define a connection A_rho by setting every tree-edge label to the identity and assigning to each chord the value of rho on its corresponding fundamental loop (or its inverse, depending on the fixed orientation convention). Since Pi_1 of a graph is free on the chord loops, this defines a connection with holonomy rho. Thus every target object is in the image, not merely isomorphic to one.

This proves equivalence.

## 4. Isotropy consequence

Set A=B in the full-faithfulness construction. A gauge automorphism is uniquely determined by k=g(r), and the chord conditions say exactly that k commutes with every rho_A(ell). Therefore
Aut(A) ~= {k in G | forall ell, k rho_A(ell) = rho_A(ell) k}
= C_G(im rho_A).

For a single cycle, Pi_1 ~= Z and a representation is determined by one holonomy h; this reduces to C_G(h), matching Spike 27. For a graph with b independent cycles, the stabilizer is the common centralizer of the b holonomies. This is generally smaller than the centralizer of any one coordinate.

## 5. Formalization status and next Lean targets

The new Lean module proofs/lean/GraphGaugeHolonomy.lean proves, for arbitrary vertex types and arbitrary admissible-walk relations:
1. gauge covariance of transport along every finite walk;
2. conjugacy covariance of every closed-walk holonomy;
3. every gauge stabilizer centralizes every based loop holonomy.

The formal model currently stores labels on all ordered vertex pairs and uses adjacency only to select admissible walks. This is a deliberate core-Lean simplification; it is not yet the edge-indexed graph structure with reverse-edge involution and inverse-label law.

Remaining formal obligations:
1. Replace pair-indexed labels with an oriented-edge type and reverse-edge involution.
2. Define a spanning-tree structure with a root and unique tree paths.
3. Prove the tree-path recursion and the unique reconstruction formula for a gauge arrow.
4. Prove the chord equations equivalent to conjugacy of the free-generator holonomies.
5. Package the hom-set bijections as full faithfulness and construct the identity-on-tree-edge representative for essential surjectivity.
6. Derive the automorphism-group isomorphism to the common centralizer of all holonomies.

No sorry, axioms, or Mathlib dependency were added to the current Lean path-covariance module. The groupoid equivalence itself is not yet a Lean theorem.

## 6. Important scope limits

- The theorem concerns ordinary G-valued connections on a graph (a 1-complex). Adding 2-cells imposes flatness relations; the fundamental group presentation changes and the chord generators are no longer freely independent.
- For higher gauge theory, edge labels and vertex gauges are not enough: 2-morphisms and coherence data enter. The correct target is a higher representation/moduli object, not merely a 1-groupoid.
- The theorem is independent of finiteness of G. Finiteness is needed for the character-basis results, not for spanning-tree gauge fixing.
- The chosen spanning tree gives coordinates, not intrinsic structure. Changing the tree changes the free basis of pi_1 but not the equivalence class of the resulting groupoid.



## 7. Updated Lean formalization status (2026-11-22)

The formalization has advanced beyond the earlier path-covariance-only status. New module:
`proofs/lean/GraphGaugeClassification.lean` (registered as `GraphGaugeClassification` in `proofs/lean/lakefile.lean`).

Machine-checked results now include:

1. **Edge-indexed path covariance.** `EdgeWalk` uses an actual edge type with source/target maps. `edgeTransport_gauge_covariant` proves transport covariance for every finite edge walk under the vertex-gauge action.
2. **Frame covariance.** `treeFrames_covariant` derives
   `P_B(v) = g(v) P_A(v) g(root)^(-1)`
   from an arrow `A^g=B), provided both frames are transports along the same selected root-to-vertex paths.
3. **Chord holonomy covariance.** `chordHolonomy_gauge_covariant` proves simultaneous conjugation by the root component.
4. **Gauge reconstruction.** `canonicalGauge_chord`, `canonicalGauge_tree`, and `canonicalGauge_isArrow` prove that the explicit formula `g(v)=P_B(v) k P_A(v)^(-1)` satisfies the edge equation on every edge, assuming tree-frame recursion and conjugacy on all chord holonomies.
5. **Uniqueness.** `canonicalGauge_unique` proves uniqueness among gauges satisfying the frame-transport relation for a fixed basepoint conjugator.
6. **Free-generator representative.** `ChordRep` and `treeGaugeRepresentative` formalize the tree-gauge object construction in chord-generator coordinates: tree edges are identity and each chord carries its chosen generator value.

The abstract group interface in `HoTTGaugeBridge.lean` now includes the inverse-of-product and double-inverse laws, plus left/right cancellation lemmas, to support these proofs without Mathlib.

**Verification:** `lake build GraphGaugeClassification` passed after the final additions; the complete `lake build` passed before the last edge-walk/frame-covariance and chord-coordinate additions. The current focused build recompiles the classification module and its dependencies successfully. A fresh full build is still required after these latest additions.

**Precise remaining gap:** this is not yet a single Lean theorem asserting
`Conn(Γ,G)//G^V ≃ Hom(π₁(Γ,r),G)//G`.
The remaining bridge is to formalize a connected graph with a genuine spanning-tree certificate (including uniqueness/existence of tree paths), identify the chord-generator assignment with the actual free-group representation type, and package the hom-set bijections plus essential surjectivity into an equivalence of action groupoids. The present `ChordRep` is an explicit free-generator coordinate model, not yet a Lean construction of `Hom(π₁,G)`. Reverse-edge involution/inverse-label consistency also remains to be encoded. No `sorry`, custom axiom, or unverified theorem was introduced.


### Verification addendum (2026-11-22, after the edge-walk extension)

A fresh full `lake build` of the canonical `proofs/lean` project passed after all current graph-classification additions. The focused Python character/HoTT bridge suite passed **8/8** in 59.45 seconds. `git diff --check` passed.

A temporary `#print axioms` audit was run and the temporary file removed. The new graph theorems depend only on Lean's standard `propext` and, for subtype/function-extensionality packaging, `Quot.sound`; **no `sorryAx`, custom axiom, or admitted theorem** appears in the audited theorem dependencies.

The edge-indexed formalization now includes actual `EdgeWalk` paths and `edgeTransport_gauge_covariant`, plus `treeFrames_covariant`. The chord-coordinate representative theorem gives the tree-gauge construction for a function of chord generators. The remaining formal gap remains the genuine connected spanning-tree/path certificate and a Lean definition of the free group `π₁` and its representation type, followed by the single packaged action-groupoid equivalence.


### 8. Rooted spanning-tree certificate formalization (2026-11-22)

The canonical Lean module now contains an explicit structure RootedSpanningTree with:
- a root vertex;
- a selected edge-indexed root-to-vertex walk for every vertex;
- a proof that each selected walk uses only edges marked as tree edges;
- uniqueness of the selected walk among all tree-supported walks;
- a transport-recursion law for each tree edge, with the chosen orientation convention.

The associated treeFrame is defined as parallel transport along the selected path. Lean proves:
- treeFrame_root: the frame is identity at the root;
- treeFrame_recursion: the frame obeys the tree-edge recursion;
- spanningTree_reconstruct_gauge: the tree frames and simultaneous chord-holonomy conjugacy reconstruct a gauge arrow on every edge;
- spanningTree_reconstruct_basepoint: the reconstructed gauge has the prescribed basepoint component.

**Verification:** focused lake build GraphGaugeClassification and a fresh full lake build passed. The axiom audit reports no axioms for the two frame lemmas; reconstruction depends only on standard propext and Quot.sound. No sorryAx or custom axioms.

**Important formal boundary:** this is a certificate interface, not yet a theorem constructing a certificate from connectedness and acyclicity. In addition, the certificate currently carries transport recursion explicitly. The next strengthening is to derive that recursion from a structural decomposition of each selected tree path into the path to its parent plus its final edge, rather than accepting it as certificate data. Then prove existence of such a certificate for a finite connected acyclic graph (or a suitable constructive variant). Only after those steps should we claim the full graph classification theorem.
