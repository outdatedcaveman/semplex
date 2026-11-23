# Probe semantics: separation, faithfulness, and information loss
Date: 2026-11-22
Status: foundational interface proposal; definitions are precise, application to Semplex remains a research programme.

## 1. The central distinction

A probe family can identify objects without identifying transformations between them. These are different mathematical achievements.

Let C be a category and let P_i : C -> D_i be probes. The joint probe is
P : C -> product_i D_i, with P(x) = (P_i(x)) and P(f) = (P_i(f)).

For each x,y, its action on the hom-set is
P_{x,y} : Hom_C(x,y) -> product_i Hom_{D_i}(P_i x, P_i y).

Three properties must not be conflated:

- **Faithful:** every P_{x,y} is injective. Distinct admissible transformations remain distinguishable.
- **Full:** every P_{x,y} is surjective. Every tuple of target transformations is represented by a source transformation.
- **Fully faithful:** every P_{x,y} is bijective. The probe preserves the complete transformation structure between represented objects.
- **Essentially surjective:** every target object is isomorphic to some P(x). This is a separate coverage condition, not a consequence of faithfulness.

A fully faithful and essentially surjective functor is an equivalence of categories. This is the appropriate categorical standard when the intended claim is preservation of structure, rather than merely successful prediction on observed examples.

## 2. Object separation is weaker

The object map x |-> P(x) may be injective (or injective up to isomorphism) while P fails to be faithful. Conversely, a faithful functor need not separate non-isomorphic objects.

For a groupoid C, object separation up to isomorphism means:
P(x) ~= P(y) implies x ~= y.
Faithfulness means:
for every x,y and arrows f,g : x -> y, P(f)=P(g) implies f=g.

The first concerns connected components. The second concerns the paths/morphisms inside a component. Neither implies the other in general.

A probe into a discrete category (in particular, a set regarded as a discrete category) sends every automorphism to an identity. Therefore it cannot be faithful at an object with a nontrivial automorphism group. This is not a technical nuisance: it is a theorem-level obstruction to recovering gauge stabilizers from class labels alone.

## 3. The groupoid quotient and its truncation

For a group G acting on a set X, the action groupoid X//G has:
- objects x in X;
- arrows x -> y given by group elements g with g.x = y;
- automorphisms at x isomorphic to the stabilizer G_x.

Its set of connected components is the orbit set X/G. Passing to this set forgets the automorphism groups. In homotopy-type language, the action groupoid is a 1-type (when G and X are sets), while its 0-truncation records only components.

Thus the information ledger is:

| Level | Retained information | Lost information |
|---|---|---|
| Object representatives | chosen configurations | gauge redundancy |
| Orbit set / pi_0 | gauge-equivalence classes | stabilizers and arrows |
| Action groupoid / 1-type | classes, arrows, isotropy | higher coherence above dimension 1 |
| Higher groupoid / infinity-groupoid | higher paths and coherences | only what the chosen truncation discards |

For the cycle gauge model, the holonomy construction identifies the quotient groupoid with G//G (conjugation action), not merely with the set of conjugacy classes. In particular:
Aut([A]) ~= C_G(H(A)).
The centralizer is exactly the loop-space/isotropy information lost by replacing the groupoid quotient with its orbit set.

## 4. Characters: complete object probes, incomplete groupoid probes

For a finite group G over a splitting field of characteristic zero, irreducible characters form a basis of class functions. Consequently the complete irreducible-character profile separates conjugacy classes.

This establishes object-level completeness for the conjugation action groupoid G//G:
two objects have the same complete character profile iff they lie in the same connected component.

It does **not** establish full faithfulness as a functor to a discrete vector space. Such a target has only identity arrows, so every nontrivial centralizer is collapsed. The character profile classifies pi_0(G//G), not the entire 1-type.

A categorical probe architecture therefore needs at least two channels:
1. a class-function channel separating components;
2. an isotropy/transport channel preserving automorphism groups and arrows.

The channels need not be independent in the final theory, but the second cannot be silently inferred from the first.

## 5. Multi-loop holonomy and joint rather than coordinatewise quotienting

For a connected graph with first Betti number b, choose a base frame and a free basis of its fundamental group. Flat holonomy data is a tuple in Hom(F_b,G) ~= G^b. Change of base frame acts by simultaneous conjugation:
(g_1,...,g_b) |-> (k g_1 k^-1,...,k g_b k^-1).

The moduli groupoid is therefore Hom(F_b,G)//G. Coordinatewise conjugacy classes are not a complete invariant of simultaneous conjugacy. The S3 two-loop witness already found in Spike 27 demonstrates this: (s01,s01) and (s01,s12) have identical coordinatewise transposition classes, but the first pair has equal entries and the second does not; simultaneous conjugation preserves equality.

This is a general warning: quotienting each coordinate independently replaces a joint orbit problem by a strictly coarser product quotient.

## 6. Resource-indexed probe semantics

Let R be a preorder of resource budgets and let P_r be the family of probes executable at budget r. Define object indistinguishability:
x ~^0_r y iff every probe in P_r gives equivalent outputs on x,y.

Define arrow indistinguishability for parallel arrows f,g:
f ~^1_r g iff every probe in P_r maps f and g to the same arrow (or to equivalent arrows under a specified target equivalence).

If r <= s and P_r is included in P_s, then:
~^0_s is contained in ~^0_r, and ~^1_s is contained in ~^1_r.
This monotonicity is a direct consequence of quantifying over a larger probe family; it does not imply eventual separation.

A resource-relative adequacy claim should report at least:
- object-kernel: which configurations remain indistinguishable;
- arrow-kernel: which transformations remain indistinguishable;
- isotropy retention: the induced maps on automorphism groups/loop spaces;
- coverage: which target objects and arrows are representable;
- cost: resources required to reach each separation/faithfulness threshold.

This yields a resolution profile rather than one scalar score.

## 7. Candidate theorem schema

**Joint-probe equivalence criterion.** Let C be a groupoid and let P : C -> D be a functor into a groupoid D. If P is fully faithful and essentially surjective, then P is an equivalence; hence it induces equivalences on all hom-sets and automorphism groups, and a bijection on connected components.

**Set-valued obstruction.** If P factors through a discrete category, then for every x, the induced map Aut_C(x) -> Aut_D(Px) is trivial. Therefore P can be faithful only where Aut_C(x) is trivial.

**Truncation warning.** A bijection pi_0(C) -> pi_0(D) does not imply C ~= D. It gives no control over isotropy groups, and in higher groupoids gives no control over higher homotopy groups or coherence data.

The first statement is the standard fully-faithful/essentially-surjective equivalence criterion; the second follows because discrete categories have only identity arrows; the third follows because pi_0 is a truncation invariant and is not conservative on groupoids.

## 8. Proof and experiment obligations

1. Formalize the action groupoid and its 0-truncation in Lean/Mathlib, keeping the distinction between a set quotient and a quotient groupoid explicit.
2. Formalize the cycle holonomy functor on objects and arrows; prove full faithfulness by the spanning-tree reconstruction and essential surjectivity by the normal form (e,e,h).
3. Derive the induced isomorphism Aut(A) ~= C_G(H(A)), not merely an injection.
4. Generalize to a connected graph using a spanning tree and a free basis of pi_1; make basepoint dependence and simultaneous conjugation explicit.
5. Build finite counterexample suites where object separation succeeds but arrow faithfulness fails, and where coordinatewise invariants fail to separate joint orbits.
6. For resource-indexed probes, measure object and arrow kernels separately. Never call object-level injectivity “full abstraction” without specifying the semantic category and the morphism-level criterion.

## 9. Relation to the variational programme

The variational objective may select a preferred metric or factorization on a minimal predictive support. It cannot by itself restore arrows or isotropy already erased by an earlier quotient. The order of operations matters:

(1) define the semantic groupoid and admissible transformations;
(2) identify the observable subcategory and its probe functor;
(3) determine object and arrow kernels;
(4) reduce to minimal support only after stating what structure the reduction preserves;
(5) optimize a realization within that preserved structure.

This is a proposed interface constraint, not a theorem that the current variational objective satisfies it. In particular, rank reduction, centering, and quotienting must each state whether they preserve connected components, automorphism groups, and mapping spaces.

## 9. Independent audit refinements (2026-11-22)

An Antigravity-channel adversarial audit (event 151820; not yet a direct Gemini response) identified two important precision points:

1. For a joint probe P=(P_i):C -> product_i D_i, fullness is relative to the full product hom-set. Arbitrary tuples of component morphisms need not be jointly realizable by one source morphism. Thus the product functor is not generically full. A full-faithfulness/equivalence claim may require restricting the codomain to the essential image or to a compatibility subcategory/limit, or else specifying a single canonical target category. The definitions in Sections 1 and 7 remain correct; this is a warning against assuming their hypotheses for an unconstrained product target.
2. For the action groupoid X//G, the homotopy fiber of the 0-truncation map |-|_0 : X//G -> pi_0(X//G) over the component [x] is the delooping B(G_x), a connected 1-type whose loop space is G_x. The stabilizer is the loop space, not the homotopy fiber itself. In the gauge-cycle case, this loop group is C_G(H).

These refinements are now part of the canonical interpretation. Direct Gemini review is still pending; event 151820 is attributed to Antigravity.
