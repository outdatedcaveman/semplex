# Conjugation groupoids, centralizers, and semantic isotropy

**Date:** 2026-11-22  
**Status:** generic stabilizer theorem formalized; finite S3 enumeration checked.

For a group G acting on itself by conjugation, the action groupoid has objects x∈G and arrows x→y given by group elements g satisfying gxg⁻¹=y. Its connected components are conjugacy classes. The loop group at x is the stabilizer
\[
\operatorname{Stab}(x)=\{g\in G:gxg^{-1}=x\}=C_G(x).
\]

The Lean module `proofs/lean/ConjugationSemanticGroupoid.lean` proves the stabilizer-centralizer equivalence for every `GroupLike` group. The accompanying S3 experiment exhaustively verifies the finite decomposition: three components with representative centralizers S3, C2, and C3. The orbit set has three points; the action groupoid has nontrivial and nonuniform isotropy.

The key structural target is the general componentwise equivalence
\[
X//G\simeq\coprod_{[x]\in X/G} B\operatorname{Stab}(x),
\]
for a group action, with the conjugation specialization above. This equivalence is a standard groupoid-level classification pattern; the project's contribution is to integrate it as a verified semantic interface, not to claim the theorem itself as novel.

For S3, class sizes and stabilizer orders are (1,6), (3,2), and (2,3). There are 14 nonempty ordered hom-sets, 36 arrows, and 18 loops. The groupoid cardinality is 1. These counts distinguish the arrow total from the loop total and make the isotropy loss under 0-truncation explicit.

This case study supports the semantic architecture: admissible transformations generate a groupoid; observational/orbit quotienting keeps connected components; higher identity retains automorphism structure. It does not yet supply grounding to an external physical target.
