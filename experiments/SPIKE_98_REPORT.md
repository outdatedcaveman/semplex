> Renumbered from canonical distinction-calculus `SPIKE_28_REPORT` to `SPIKE_98_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 28 — Conjugation Semantics and S3 Isotropy

**Date:** 2026-11-22  
**Status:** finite exhaustive experiment + generic Lean theorem; not a completed higher-semantic theory.

## Question

What information is retained when presentations are identified up to conjugation, and what does the corresponding action groupoid retain that the orbit set forgets?

## Generic theorem formalized in Lean

`proofs/lean/ConjugationSemanticGroupoid.lean` defines conjugation
\[
\operatorname{conj}_g(x)=gxg^{-1}
\]
from the project's abstract `GroupLike` interface, proves that this is a group action, and establishes
\[
gxg^{-1}=x \quad\Longleftrightarrow\quad gx=xg.
\]
Thus the stabilizer predicate at x is exactly the centralizer predicate
\[
C_G(x)=\{g\in G\mid gx=xg\}.
\]
The file also proves that nonempty conjugation-arrow witnesses are equivalent to the existence of a conjugating element. A focused `#print axioms` audit found no custom axioms or `sorryAx`; the displayed dependencies are standard Lean `propext` and, for predicate extensionality, `Quot.sound`.

This is a generic theorem over the project's group interface. It is not yet a formalized finite S3 instance, nor a proof of the full action-groupoid equivalence in HoTT.

## Exhaustive S3 calculation

`experiments/s3_conjugation_groupoid.py` enumerates all six permutations, all conjugation orbits, centralizers, and all 36 ordered object pairs. The regression test is `tests/test_s3_conjugation_groupoid.py`.

| Conjugacy class | Class size | Centralizer size | Product |
|---|---:|---:|---:|
| Identity | 1 | 6 | 6 |
| Transpositions | 3 | 2 | 6 |
| 3-cycles | 2 | 3 | 6 |

Verified finite invariants:

- Three connected components/orbits, of sizes 1, 3, and 2.
- Centralizer orders are 6, 2, and 3, respectively.
- Orbit–stabilizer holds in every class: \(|[x]|\,|C_G(x)|=6\).
- There are 14 ordered object-pairs with nonempty hom-sets: \(1^2+3^2+2^2=14\).
- The total number of groupoid arrows is 36: each of the six objects has six outgoing arrows, one for each group element.
- The total number of loops is 18: \(6+3\cdot2+2\cdot3=18\).
- The groupoid cardinality is \(1/6+1/2+1/3=1\).

The artifact is written to `artifacts/s3-conjugation-groupoid-20261122.json` by the experiment.

## Semantic interpretation

The orbit set records only three conjugacy classes. It identifies all presentations within each class and forgets the automorphism groups.

The action groupoid retains the isotropy:
- identity presentation: automorphism group S3;
- transposition presentation: automorphism group C2;
- 3-cycle presentation: automorphism group C3.

This is not cosmetic metadata. Isotropy determines the loop space of the corresponding 1-groupoid and changes the structure of maps, descent data, and any higher quotient built from it. Two objects in the same orbit are equivalent, but their automorphism groups are only guaranteed to be isomorphic by conjugation; across different orbits the isotropy types can differ.

The finite example also gives a useful correction to a tempting count: 18 is the number of loops, not the total number of arrows. The total arrow count is 36.

## What this establishes — and what it does not

**Established:** a generic Lean proof that conjugation stabilizers are centralizers; an exhaustive, independent finite S3 calculation; and a concrete demonstration that the 0-truncated orbit set loses isotropy.

**Not established:** a formal Lean construction of the S3 permutation group; a full categorical equivalence between the conjugation action groupoid and a disjoint union of one-object centralizer groupoids; a univalent or complete HoTT classifying-space construction; or a general account of semantic reference/grounding.

## Next mathematical step

Prove, for any group action, that each connected component of its action groupoid is equivalent to the one-object groupoid on the stabilizer of a chosen representative. Specialize to conjugation to obtain
\[
G//G\simeq \coprod_{[x]\in G/\!\sim_{\mathrm{conj}}} B C_G(x).
\]
Then construct the corresponding finite S3 equivalence and relate its classifying-space loop types to the Agda HIT work. This is the precise bridge from orbit classification to higher semantic identity.

## Final verification

- Full Lean `lake build`: passed, including `ConjugationSemanticGroupoid` and `ConnectedIsotropy`.
- Full Python suite: 239 passed, 2 skipped in 360.68 seconds.
- Focused S3 regression test: passed after centralizer structure classification was added to the artifact.
- Cubical Agda verification: passed.
- `git diff --check`: passed.
- No commits, pushes, or merges.
