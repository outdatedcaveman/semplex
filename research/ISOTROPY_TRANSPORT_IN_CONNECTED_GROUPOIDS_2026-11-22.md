# Isotropy transport in groupoids

**Date:** 2026-11-22  
**Status:** generic Lean theorem compiled.

Let C be a groupoid and f : a → b an isomorphism. Conjugation by f transports automorphisms:
\[
\operatorname{Aut}(a)\to\operatorname{Aut}(b),\qquad
h\mapsto f^{-1}\,h\,f
\]
under the convention that composition is written in traversal order. The inverse map is
\[
k\mapsto f\,k\,f^{-1}.
\]

The Lean module `proofs/lean/ConnectedIsotropy.lean` defines this bijection on hom-types and proves both inverse laws directly from the groupoid associativity, identity, and inverse laws. It also derives involutivity of inversion from the groupoid axioms rather than assuming an extra field. Therefore isomorphic objects have bijective automorphism/loop types.

This theorem is the local algebraic ingredient needed for the componentwise classification of a connected groupoid by the one-object groupoid on a chosen representative's automorphism group. The full equivalence still requires choosing connecting arrows coherently and proving the functoriality/fully-faithful statements. The current theorem does not itself construct that equivalence.

Semantic consequence: object equivalence must preserve isotropy up to group isomorphism. A 0-truncated quotient forgets this structure, while the groupoid retains it as the loop type at each object.


**Scope caveat:** the current Lean result establishes a bijection of automorphism hom-types, proves that it preserves the identity automorphism, and proves that inverse-arrow transport is inverse. Preservation of automorphism composition (the final step to a group isomorphism) remains an explicit open formalization item; an initial proof attempt was discarded rather than retained as an unverified claim.
