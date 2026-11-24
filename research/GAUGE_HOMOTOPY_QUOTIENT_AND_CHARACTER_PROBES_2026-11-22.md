# Gauge semantics as a homotopy quotient: character probes and higher structure

## 1. The two quotients

The finite gauge-cycle model makes two different quotient operations visible.

Let (G) be a group, let (V) be the vertices of a connected graph, and let (E) be its oriented edges. A discrete connection is an element of
[
mathrm{Conn}_Gamma(G)=G^E.
]
The vertex gauge group (G^V) acts by
[
(gcdot A)_e=g_{t(e)}A_eg_{s(e)}^{-1}.
]

The **orbit set**
[
mathrm{Conn}_Gamma(G)/G^V
]
forgets the gauge transformation relating two configurations and forgets stabilizers.

The **action groupoid**
[
mathrm{Conn}_Gamma(G)//G^V
]
retains configurations as objects, gauge transformations as arrows, and gauge stabilizers as automorphism groups. When (G) is a set-level group, this is a groupoid/1-type.

In HoTT language, its 0-truncation is the ordinary orbit set:
[
ig|mathrm{Conn}_Gamma(G)//G^Vig|_0
simeq mathrm{Conn}_Gamma(G)/G^V.
]
The truncation map is not an innocuous notation change: it discards the path witnesses and automorphism groups.

## 2. The cycle equivalence

For the three-edge cycle, write (A=(A_0,A_1,A_2)) and
[
H(A)=A_2A_1A_0.
]
The gauge transformation
[
A_imapsto g_{i+1}A_ig_i^{-1}
]
gives
[
H(gcdot A)=g_0H(A)g_0^{-1}.
]

Define the functor
[
F:mathrm{Conn}(G)//G^3longrightarrow G//G
]
by (F(A)=H(A)) on objects and (F(g_0,g_1,g_2)=g_0) on arrows.

For fixed (A,A'), a conjugation arrow (k:H(A)	o H(A')) determines at most one gauge arrow:
[
g_0=k,quad
g_1=A'_0g_0A_0^{-1},quad
g_2=A'_1g_1A_1^{-1}.
]
The conjugacy equation (H(A')=g_0H(A)g_0^{-1}) is precisely the remaining third-edge equation. Thus (F) is fully faithful. It is essentially surjective because (hin G) is the holonomy of ((1,1,h)). Hence
[
mathrm{Conn}(G)//G^3simeq G//G.
]

The loop group at (A) is therefore
[
Omega_A(mathrm{Conn}(G)//G^3)
simeq mathrm{Aut}(A)
simeq C_G(H(A)).
]
This identifies the stabilizer, not just its cardinality.

For finite (G), orbit-stabilizer gives
[
|mathcal O_A|=rac{|G|^3}{|C_G(H(A))|}
=|G|^2,|[H(A)]|.
]
This recovers the exact S3 and D4 orbit-size law from Spike 26.

## 3. Representation characters as decategorified probes

Let (mathrm{Rep}_{mathbb C}(G)) be the semisimple category of finite-dimensional complex representations. Each representation (ho) defines a trace-valued class function
[
chi_ho(g)=mathrm{Tr}(ho(g)).
]
For irreducible (ho), the character is constant on conjugacy classes. For finite (G), irreducible characters form an orthonormal basis of class functions.

Therefore the complete character profile separates conjugacy classes. A restricted family (S) defines
[
Xi_S([g])=(chi_ho(g))_{hoin S}.
]
Its full-abstraction condition is simply injectivity of (Xi_S).

The finite optimization problem is:
[
min_{Ssubseteqwidehat G}sum_{hoin S}c_ho
quad	ext{subject to}quad
[g]
e[h]Rightarrow
existshoin S:chi_ho(g)
echi_ho(h).
]
This is a weighted set-cover problem over class pairs. It is exact as a combinatorial optimization, but its cost coefficients become physical only after calibration.

### Why characters do not reconstruct the groupoid

A character is a trace. Trace is invariant under conjugation and additive over direct sums; this is precisely why it is useful as a class function. But the trace has forgotten intertwiner spaces and the automorphism structure of the representation. A character profile can classify the orbit-set points while failing to recover their stabilizer groups.

Thus:
- character probes can be complete for the 0-truncated quotient;
- the action groupoid is richer and retains isotropy;
- a higher-categorical Yoneda profile should retain mapping spaces, not only traces.

This is a concrete example of a general distinction between **observational completeness after truncation** and **equivalence before truncation**.

## 4. S3 and D4 exact probe minima

The S3 standard two-dimensional character ((2,0,-1)) separates all three classes by itself. Minimum cardinality: one.

For D4, no pair of irreducible characters separates all five classes; minimum cardinality: three. Under illustrative row costs ((1,2,3,4,5)), the minimum-cost family has total cost 10. The exact minimizing families are listed in `experiments/SPIKE_27_REPORT.md`.

The complete tables pass weighted row orthogonality with class-size weights. The benchmark computes minimum families by exhaustive subset search and computes which class-pairs each character distinguishes.

## 5. Higher-categorical extension

For a graph (Gamma) with a chosen spanning tree (T), gauge fixing along (T) leaves residual holonomies on non-tree edges. The number of independent cycles is the rank of the graph's fundamental group. For a connected graph, the resulting groupoid is expected to be equivalent to a conjugation action groupoid on
[
mathrm{Hom}(pi_1(Gamma),G)//G.
]
This is the discrete finite-group model of flat connections modulo gauge, with the groupoid retaining automorphisms.

For higher gauge theory, replace (G) by a higher group/(infty)-group and ordinary connections by higher cocycles. Gauge transformations, gauge-of-gauge transformations, and their coherences form higher mapping data. The natural home is an (infty)-topos or cohesive (infty)-topos, where homotopy quotients and moduli stacks preserve this structure.

A candidate semantics should therefore be organized as a hierarchy:
1. raw configurations and transformations;
2. action groupoid / homotopy quotient;
3. (0)-truncation to orbit classes;
4. resource-bounded response presheaf on admissible probes;
5. higher Yoneda reconstruction when the probe family is dense;
6. physical realization and cost.

A character family lives at step 3/4: it can test class-level separation. It is not a substitute for the full higher response object at step 5.

## 6. Foundational theorem obligations

The next formal development should establish:
- functoriality of the holonomy map on the action groupoids (identity and composition);
- full faithfulness by the unique spanning-tree gauge extension;
- essential surjectivity;
- equivalence of isotropy groups with centralizers;
- identification of 0-truncation with the orbit set;
- character-basis completeness for finite groups over (mathbb C);
- resource-relative full abstraction iff the selected character profile is injective;
- comparison between trace probes and mapping-space-valued probes.

The Lean fragment `proofs/lean/HoTTGaugeBridge.lean` currently targets only the elementary group-algebra covariance/stabilizer kernel. The Python action-groupoid model exhaustively checks all connection pairs for S3 and D4. Neither should be described as a complete formalization of HoTT or an (infty)-categorical theorem.

## 7. Prior art

The underlying ingredients are established:
- classical finite-group character theory;
- action groupoids and homotopy quotients;
- gauge groupoids and moduli stacks;
- HoTT set truncation and higher quotients;
- Yoneda reconstruction.

The research opportunity is the explicit integration of these structures with resource-bounded physical probe semantics and the distinction between set-level character separation and higher groupoid reconstruction. That is a synthesis target, not a novelty claim for any ingredient in isolation.


## 8. Multi-loop correction: simultaneous conjugation is essential

The cycle is the one-generator case. For a connected graph with first Betti number (b_1), spanning-tree gauge fixing leaves a tuple of (b_1) based holonomies, not (b_1) independently gauge-invariant conjugacy classes. The residual base-vertex gauge acts by **simultaneous** conjugation:
[
(g_1,ldots,g_{b_1})longmapsto
(k g_1 k^{-1},ldots,k g_{b_1}k^{-1}).
]
Thus the correct moduli groupoid is
[
mathrm{Hom}(F_{b_1},G)//G,
]
and its orbit-set truncation is (mathrm{Hom}(F_{b_1},G)/G). It is generally not (mathrm{Cl}(G)^{b_1}).

For (S_3), choose transpositions (s_{01}
e s_{12}). The pairs
[
(s_{01},s_{01}),qquad(s_{01},s_{12})
]
have the same conjugacy class in each coordinate. But they are not simultaneously conjugate: any simultaneous conjugator fixing the first coordinate (s_{01}) would have to fix the second (s_{01}), and therefore could not send it to (s_{12}). Equivalently, the ordered products are (e) and a 3-cycle. This is now encoded and tested in experiments/character_hott_gauge_bridge.py.

The lesson for higher categorical semantics is important: the gauge quotient acts on the *whole representation of the fundamental group*, not separately on each loop. Relations and joint composition are part of the semantic object.


## 9. Operational cautions from the adversarial audit

The uniform class-kernel lift is not canonical. It redistributes every target-class transition uniformly across elements of that class, erasing intra-class state. The identity kernel is also conjugation-equivariant and lumpable over classes, but preserves exact group elements. A physical model must justify which lift is appropriate; symmetry alone does not select the uniform lift.

For the symmetric n-sector channel, the true stochastic parameter domain is (0\le\eta\le1/(n-1)), since the diagonal entry is (1-(n-1)\eta). The singular point remains (eta=1/n). At the valid endpoint (eta=1/(n-1)), the diagonal vanishes but the channel is still invertible. The exact five-sector endpoint example (eta=1/4) has determinant (1/256).

The Spike26 posterior-rank effect at budget 2 is due to open-loop prior drift under the nonstationary uniform prior, not observation learning. The stationary wait prior ((1/4,1/2,1/4)) removes this rank increase.

Finally, the centered Hankel operator and the centered Gram sum are different objects. Exact ranks across the three Spike26 regimes are:
[
\operatorname{rank}(H_c)=(0,2,0),\qquad
\operatorname{rank}((W_c)_c+(W_o)_c)=(1,2,2).
]
The sum therefore retains modes absent from the centered response operator in the unobservable regimes. Any proposed master selector must be derived from the minimal predictive realization, not identified with (W_c+W_o) by notation.
