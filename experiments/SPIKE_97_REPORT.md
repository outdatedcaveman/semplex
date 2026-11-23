> Renumbered from canonical distinction-calculus `SPIKE_27_REPORT` to `SPIKE_97_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 27 — Character probes and the HoTT gauge-groupoid bridge

**Date:** 2026-11-22  
**Status:** finite character optimization implemented; S3/D4 action-groupoid hom-set comparisons exhaustive; multi-loop simultaneous-conjugation counterexample added; Lean algebraic kernel compiled successfully.

## 1. Research question

Can the gauge-invariant sector semantics from Spike 26 be reconstructed by a resource-bounded family of representation-theoretic probes, while retaining the gauge transformations discarded by an ordinary orbit-set quotient?

Two distinct mathematical objects are required:

1. A *character profile* of a conjugacy class, which is a decategorified observable.
2. The *gauge action groupoid*, which remembers arrows and stabilizers between configurations.

They answer different questions. The first determines which conjugacy sectors can be distinguished by trace-valued probes. The second preserves the symmetry structure of the underlying physical configuration space.

## 2. Character-theoretic separation

For a finite group (G), the irreducible complex characters form an orthonormal basis of the vector space of class functions. Consequently the complete character vector
[
Clongmapsto (chi_
ho(C))_{
hoinwidehat G}
]
separates conjugacy classes: if two classes agree on every irreducible character, they agree on every class function, including the indicator function of either class.

A resource-limited probe family (Ssubseteqwidehat G) induces
[
Xi_S(C)=(chi_
ho(C))_{
hoin S}.
]
It is fully abstract for the conjugacy-class task exactly when (Xi_S) is injective. Finding the smallest such (S) is a finite set-cover problem over unordered pairs of distinct conjugacy classes: character (
ho) covers pair ({C_i,C_j}) iff (chi_
ho(C_i)
echi_
ho(C_j)).

The implementation exhaustively solves this optimization for the S3 and D4 character tables and permits nonnegative measurement costs.

### S3

With classes identity, transposition, 3-cycle, the character table is
[
egin{array}{c|rrr}
 & 1 & (12) & (123)\hline
1 & 1&1&1\
mathrm{sgn}&1&-1&1\
mathrm{std}_2&2&0&-1
end{array}
]
The standard two-dimensional irreducible character alone separates all three conjugacy classes. Thus the minimum cardinality is **one**.

This is a useful correction to the naive expectation that all irreducible characters are always needed. The full character table guarantees separation, but a task-specific subfamily may suffice.

### D4

For classes (1,r^2,{r,r^3},{s,r^2s},{rs,r^3s}), the table is
[
egin{array}{c|rrrrr}
 &1&r^2&r^{pm1}&s	ext{-axis}&rs	ext{-axis}\hline
1&1&1&1&1&1\
alpha&1&1&1&-1&-1\
eta&1&1&-1&1&-1\
alphaeta&1&1&-1&-1&1\

ho_2&2&-2&0&0&0
end{array}
]
The minimum separating family has cardinality **three**. The three minimum subsets (using zero-based row indices) are ((1,2,4)), ((1,3,4)), and ((2,3,4)). With illustrative costs ((1,2,3,4,5)), the minimum weighted solution costs 10 and is ((1,2,4)).

The costs are placeholders, not measured physical implementation costs. They define a well-posed resource-optimization interface that later needs calibration against actual probe construction, energy, precision, and readout costs.

The character rows pass weighted row-orthogonality checks using the conjugacy-class sizes. This checks the supplied S3 and D4 tables internally; it is not a general character-table generator.

## 3. The groupoid, not merely the orbit set

Let (G) be a group and let (mathrm{Conn}(G)=G^3) be the connection space of the three-edge cycle. The vertex gauge group is (G^3), acting by
[
A_imapsto g_{i+1}A_i g_i^{-1}.
]
The action groupoid (mathrm{Conn}(G)//G^3) has connections as objects and vertex gauge transformations as arrows.

There is a functor
[
F:mathrm{Conn}(G)//G^3longrightarrow G//G
]
to the conjugation action groupoid. On objects it sends (A) to ordered holonomy
[
H(A)=A_2A_1A_0.
]
On arrows it sends (g=(g_0,g_1,g_2)) to its base-vertex component (g_0). Holonomy covariance proves this is well-defined.

### Full faithfulness by spanning-tree reconstruction

Fix connections (A,A'). A conjugation arrow (k:H(A)	o H(A')) satisfies
[
H(A')=kH(A)k^{-1}.
]
There is a unique possible vertex gauge extending (g_0=k):
[
g_1=A'_0g_0A_0^{-1},qquad
g_2=A'_1g_1A_1^{-1}.
]
The holonomy-conjugacy equation is exactly the remaining edge equation
[
A'_2=g_0A_2g_2^{-1}.
]
Therefore the map on every hom-set is bijective: (F) is fully faithful.

### Essential surjectivity

Every (hin G) is the holonomy of the connection ((1,1,h)). Thus (F) is essentially surjective.

Hence, for a connected three-cycle,
[
oxed{mathrm{Conn}(G)//G^3simeq G//G.}
]

This is an equivalence of groupoids, not merely a bijection on isomorphism classes.

The isotropy group at a connection with holonomy (H) is isomorphic to the centralizer
[
C_G(H)={kin Gmid kH=Hk}.
]
The orbit set, equivalently the 0-truncation of this groupoid, is the set of conjugacy classes. Passing to that set forgets stabilizer groups. The action groupoid retains them.

## 4. HoTT interpretation

In univalent foundations, a group (G) regarded as a set-level group is a 0-type. A group action on a set (X) yields a homotopy quotient (X//G), a 1-type/action groupoid. Its identity types retain the action witnesses; its 0-truncation (|X//G|_0) is the ordinary orbit set.

For the cycle:
- (mathrm{Conn}(G)=G^3) is a set;
- the vertex gauge group (G^3) acts on it;
- (mathrm{Conn}(G)//G^3) is the 1-truncated semantic object;
- (|,mathrm{Conn}(G)//G^3,|_0) is the conjugacy-class quotient;
- the loop space at (A) is its gauge stabilizer, equivalent to (C_G(H(A))).

The groupoid equivalence above is therefore a concrete 1-type equivalence. It explains precisely what is lost when the model collapses a homotopy quotient to a set quotient.

### Relation to higher gauge theory

This is only the 1-groupoid layer. In higher gauge theory, fields, gauge transformations, gauge-of-gauge transformations, and higher coherences require a higher groupoid or moduli stack. The same methodological distinction persists: truncating too early destroys higher automorphism/coherence data. A later (infty)-categorical extension should replace the action groupoid by an appropriate homotopy quotient in an (infty)-topos and replace scalar characters by higher-categorical traces/characters where defined. This is a research programme, not a theorem established by this finite benchmark.

## 5. Restricted Yoneda and the meaning of characters

The character map is a decategorified shadow of representation-theoretic evaluation. Each representation is a probe; its trace is a class function. A selected family of irreducible representations defines a finite response profile on conjugacy classes.

This resembles restricted Yoneda semantics, but it is not literally the full mapping-space-valued Yoneda embedding:
- ordinary Yoneda retains morphism sets (or mapping spaces);
- characters retain traces, hence discard most morphism-level information;
- the character profile separates conjugacy classes when the chosen family is sufficient;
- it does not recover centralizers or the full action groupoid.

This distinction is foundational: character separation proves observational completeness for a specific set-level task, not categorical equivalence of the gauge moduli object.

## 6. Lean kernel and verification boundary

Added `proofs/lean/HoTTGaugeBridge.lean` with a self-contained abstract group interface and theorem statements for:
- base-frame covariance of ordered holonomy;
- gauge invariance of the induced conjugacy class;
- mapping gauge stabilizers into the holonomy centralizer.

The file is registered in `proofs/lean/lakefile.lean`. `lake env lean HoTTGaugeBridge.lean` completed successfully. The compiled fragment proves abstract-group holonomy covariance, conjugacy-class invariance, and that a gauge stabilizer maps into the holonomy centralizer. It does not yet prove the full action-groupoid equivalence in Lean. The Python implementation exhaustively checks the action-groupoid hom-set bijection for every pair of S3 connections and every pair of D4 connections; it also checks centralizer sizes.

No claim is made that the Lean file formalizes univalence, higher inductive quotients, or the complete groupoid equivalence. That remains the next formalization step.

## 7. Prior-art and novelty discipline

The finite-group character theorem is classical. The action-groupoid/homotopy-quotient construction and its relation to gauge symmetry are also standard. The spanning-tree reduction of graph connections to holonomy data is a standard gauge-theoretic idea.

The project-specific contribution here is an executable bridge between:
1. the exact S3/D4 gauge-cycle fixture;
2. minimum resource-costed character families for class separation;
3. the groupoid-level gauge quotient with stabilizers;
4. the Causal-Realization distinction between set-level observational full abstraction and richer morphism-preserving equivalence.

This is a synthesis and test harness, not a claim to have discovered character theory, homotopy quotients, or a new theorem of gauge theory.

## 8. Next proof targets

1. Prove the action-groupoid equivalence in Lean using explicit hom-set equivalences and verify identity/composition preservation.
2. Encode the action groupoid as a 1-type in a HoTT/Agda development; show its 0-truncation is the conjugacy-class quotient and identify loop spaces with centralizers.
3. Generalize from a cycle to a connected graph: choose a spanning tree, gauge-fix tree edges, and identify residual holonomy data with representations of the fundamental groupoid up to conjugation.
4. Replace character-only readouts by full representation-valued probes; compare trace decategorification with categorical traces and mapping-space data.
5. Define a resource-enriched probe category and prove that a cost-bounded character family yields the corresponding response quotient. Distinguish the minimum set-cover problem from the physically calibrated cost problem.
6. Ask Gemini to independently audit the character tables, minimum set-cover results, groupoid functor, stabilizer identification, and HoTT truncation claims before treating the synthesis as independently validated.


## 9. Multi-loop graphs: simultaneous conjugation

For a connected graph with first Betti number (b_1), a spanning tree leaves (b_1) based holonomies. The residual base-point gauge acts on the entire tuple simultaneously:
[
(g_1,ldots,g_{b_1})mapsto
(k g_1 k^{-1},ldots,k g_{b_1}k^{-1}).
]
The groupoid-level moduli object is
[
mathrm{Hom}(F_{b_1},G)//G,
]
not a product of independent conjugation groupoids ((G//G)^{b_1}). The corresponding set quotient is (mathrm{Hom}(F_{b_1},G)/G), not (mathrm{Cl}(G)^{b_1}).

The S3 executable counterexample uses ((s_{01},s_{01})) and ((s_{01},s_{12})). Their coordinate-wise conjugacy classes agree, but they are not simultaneously conjugate; their ordered products are the identity and a 3-cycle. This is a direct test that loop composition and joint gauge action cannot be discarded independently.

## 10. Verification

- Focused suite: **8 tests passed** for character separation, weighted minima, action-groupoid hom-sets, identity/composition, centralizers, and the two-loop counterexample.
- Combined Spike 26/27 finite regression: **31 tests passed in 68.19 seconds**.
- Exhaustive action-groupoid hom-set comparisons: **46,656** source/target pairs for S3 and **262,144** for D4.
- Character tables pass weighted row orthogonality; minimum separating family sizes are 1 for S3 and 3 for D4.
- Symmetric channel full stochastic domain and anti-identity endpoint checked in the combined suite.
- Exact centered-Gram and stationary-prior diagnostics checked in the combined suite.
- Python compilation, artifact regeneration, git diff check, and focused Lean compilation all passed.
- No full repository suite, Mathlib higher-category development, Agda build, or physical experiment was run.
- No commits, pushes, or merges were made.
- Direct Gemini audit task 141 remains pending. The independent adversarial feedback received so far is attributed to Antigravity/Gemini coordination event 151805, not misrepresented as a completed direct Gemini review.
