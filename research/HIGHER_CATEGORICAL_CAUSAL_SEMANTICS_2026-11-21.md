# Higher-Categorical Causal Semantics: a precise extension and an exact obstruction

**Date:** 2026-11-21  
**Status:** research supplement; definitions and finite test are proposed; no claim of a new theorem in higher category theory  
**Parent:** \`SEMANTIC_GROUNDING_PRINCIPLE_2026-11-21.md\`  
**Execution:** ChatGPT direct work on the canonical Semplex working tree; no commit, push, merge, or edits to Gemini's isolated worktree.

## 1. Why the ordinary relational account is not yet enough

The current probe-response and coalgebraic constructions characterize a state by its responses to admissible interventions. They already retain the composition of interventions when the action monoid is used correctly. What they do not yet make explicit is the hierarchy of *relations between transformations*.

This matters in gauge systems, topology, and higher geometry. Two protocols may have the same endpoints but differ by a deformation; two deformations may themselves be equivalent; and these equivalences can satisfy coherence laws. Replacing this structure by a set of labels, or even by a graph of pairwise relations, can discard global transport and higher holonomy.

The appropriate hierarchy is:

- a **category** when transformations compose and need not be invertible;
- a **groupoid** when all transformations being represented are invertible;
- an **\(\infty\)-category** when transformations between transformations and all higher coherences matter;
- an **\(\infty\)-groupoid** when every morphism at every level is invertible.

A physical intervention is not generally invertible. Therefore the physical action category must not be replaced wholesale by a groupoid. Invertible gauge equivalences, reversible protocol deformations, and higher equivalences form distinguished substructures inside the larger category of admissible processes.

## 2. The proposed semantic object: a response functor, not a label

Let \(\mathcal U\) be an \(\infty\)-category of admissible experimental contexts. Its objects are protocols or intervention contexts. Its 1-morphisms are lawful protocol transformations, extensions, or refinements. Its 2-morphisms are specified equivalences/deformations between such transformations; higher morphisms encode coherence among those equivalences.

For a physical system \(S\), define a response assignment

\[
\mathsf R_S:\mathcal U^{op}\longrightarrow \mathcal V,
\]

where \(\mathcal V\) is a response \(\infty\)-category appropriate to the experiment: sets, spaces of traces, probability spaces, Markov kernels in a suitable enriched setting, or a typed category of outcomes. The variance is a convention: here a morphism \(u\to v\) means that \(v\) is a lawful refinement/continuation of \(u\), and restriction along it forgets the extra detail. A covariant convention is equally possible if the protocol morphisms are oriented oppositely; the choice must be fixed once and used consistently.

The semantic content of \(S\), relative to \(\mathcal U\), is the *entire functor* \(\mathsf R_S\), including its action on morphisms and higher morphisms. Two systems are contextually equivalent when their response functors are naturally equivalent:

\[
S\simeq_{\mathcal U}T
\quad\Longleftrightarrow\quad
\mathsf R_S\simeq \mathsf R_T
\quad\text{in }\operatorname{Fun}(\mathcal U^{op},\mathcal V).
\]

This is stronger than equality of a table of one-step responses. It preserves which response transformations compose, which paths are equivalent, and whether two apparently identical local descriptions glue coherently.

The equation is a definition relative to a declared context category, not a context-free definition of meaning. If the intervention language omits a physically possible discriminator, the resulting equivalence is only interface-relative.

## 3. Restricted Yoneda: what is theorem and what is still conjectural

For an \(\infty\)-category \(\mathcal C\) and a full subcategory of probes \(\mathcal P\subseteq\mathcal C\), the restricted Yoneda profile of \(X\) is

\[
N_{\mathcal P}(X):=\operatorname{Map}_{\mathcal C}(-,X)|_{\mathcal P}
:\mathcal P^{op}\to\mathcal S.
\]

Here \(\mathcal S\) is the \(\infty\)-category of spaces. Mapping *spaces*, rather than mere hom-sets, retain automorphisms and higher homotopies between probe-to-object maps.

**Established mathematics.** The Yoneda embedding is fully faithful. If \(\mathcal P\) is dense in \(\mathcal C\), the restricted nerve \(N_{\mathcal P}\) is fully faithful. Consequently,

\[
\operatorname{Map}_{\mathcal C}(X,Y)
\simeq
\operatorname{Nat}(N_{\mathcal P}(X),N_{\mathcal P}(Y)).
\]

Density is essential. Without it, restricted profiles may fail to distinguish objects or transformations.

**Research hypothesis.** The physically realizable intervention/probe family for a specified class of systems may be dense in a suitably chosen category of physically meaningful structures. If so, all structure-preserving maps and equivalences in that domain could be reconstructed from physically available probe relations.

This is not proved by Yoneda. It requires:
1. a defensible category \(\mathcal C_{\mathrm{phys}}\) of systems and admissible transformations;
2. a physically justified probe subcategory \(\mathcal P_{\mathrm{phys}}\);
3. a proof or counterexample for density;
4. a demonstration that the probes are causally executable, not merely mathematically definable.

If density fails, the correct result is not “semantics is subjective”; it is a precise quotient or localization relative to the probes, plus an explicit account of the information lost.

## 4. The causal realization layer

A higher-categorical response functor does not itself establish physical reference. For a candidate internal representation \(r:S\to Z\), require separately:

- **causal acquisition:** the representation is generated by a physical channel coupled to the target system;
- **counterfactual adequacy:** its responses agree with the source on held-out admissible contexts, up to a declared error;
- **causal use:** interventions on the representation alter downstream inference/action as its claimed model predicts;
- **history/provenance:** acquisition history is retained whenever it changes reference, transfer, or future response;
- **resource accounting:** implementation costs and losses compose with the semantic certificates.

The mathematical certificate should therefore have two layers: a natural equivalence of response functors, and an implementation witness establishing that the functorial translation is physically realized. Neither layer implies the other.

## 5. Cohesion and differential refinement

A cohesive \(\infty\)-topos is a candidate ambient setting because it can distinguish discrete structure, homotopy structure, and cohesive/geometric structure without forcing them into one level.

The roles should be kept separate:

- homotopy types record paths, equivalences, and higher automorphisms;
- cohesive structure records the relation to geometric/continuous realization;
- differential refinement records connections, curvature, and transport data.

For gauge theory, configuration spaces are naturally groupoids or higher groupoids; higher gauge fields are represented by higher cocycles, and gauge transformations by higher morphisms. Differential cohomology refines topological characteristic data by connection/curvature information. This gives a disciplined mathematical bridge from relational semantics to physical geometry.

K-theory and generalized cohomology belong here as *invariants of selected geometric data*, not as universal semantic currencies. Stable K-classes forget some unstable information; differential K-theory restores differential refinement but remains theory-specific. The M-theory-related use of unstable cohomotopy in the Sati–Schreiber programme must not be conflated with the K-theoretic classification of D-brane charges.

## 6. Exact finite obstruction: local marginals do not determine global surface holonomy

A compact exact example demonstrates why semantic profiles must retain composition/global coherence, not only local response statistics.

Take the boundary complex of a tetrahedron, a triangulation of \(S^2\), with four triangular faces \(f_0,\ldots,f_3\), six edges, and four vertices. Put a \(\mathbb Z_2\)-valued 2-form gauge field on faces:

\[
B\in C^2(S^2;\mathbb Z_2)\cong\mathbb Z_2^4.
\]

A 1-form gauge parameter is \(\Lambda\in C^1(S^2;\mathbb Z_2)\). It acts by

\[
B\longmapsto B+\delta\Lambda.
\]

Every edge belongs to exactly two faces, so \(\sum_f(\delta\Lambda)_f=0\pmod 2\). For this triangulated sphere, the image of \(\delta:C^1\to C^2\) is exactly the even-parity subspace. Thus the gauge orbits are precisely the two parity sectors

\[
\mathcal O_h=\{B\in\mathbb Z_2^4:\sum_f B_f=h\},\qquad h\in\{0,1\}.
\]

The gauge-invariant surface holonomy is

\[
W(B)=(-1)^{\langle B,[S^2]\rangle}
=(-1)^{\sum_f B_f}.
\]

Now place the uniform distribution on each gauge orbit. For any proper subset \(J\subsetneq\{0,1,2,3\}\) of faces, the marginal distribution \(B|_J\) is uniform on \(\mathbb Z_2^{|J|}\), in *both* sectors. Proof: for each assignment on \(J\), exactly \(2^{3-|J|}\) completions have the prescribed total parity. Hence every local marginal on fewer than all four faces is identical between \(h=0\) and \(h=1\), while the global surface holonomy differs deterministically.

This is an exact obstruction to any purported semantics that retains only proper-subcomplex marginals: it necessarily identifies two globally distinct gauge sectors. A semantic model retaining the coherent surface observable separates them.

The higher-gauge hierarchy is also explicit. Objects are 2-form fields \(B\); 1-morphisms are 1-form gauge transformations \(\Lambda\) relating fields; 2-morphisms are 0-form gauge transformations \(\eta\) between 1-form gauge parameters, with \(\Lambda\mapsto\Lambda+\delta\eta\). The cochain identity \(\delta^2=0\) is the coherence law ensuring that a 2-morphism does not change the induced transformation of \(B\).

**Interpretation boundary:** this is a finite mathematical model of higher gauge structure. It is not evidence for a new physical field, a new M-theory prediction, or an experimentally observed phenomenon. Its value is methodological: it supplies a controlled case in which local statistics are insufficient and a higher/global invariant is necessary.

## 7. Reproducible exact test and acceptance criteria

The companion script \`experiments/higher_gauge_surface_holonomy.py\` enumerates the tetrahedral cochain complex exactly over \(\mathbb Z_2\). It checks:

1. the image of the edge-to-face coboundary has size 8 and equals the even-parity subspace;
2. the two gauge orbits are exactly the two parity sectors;
3. all proper face-subset marginals coincide between sectors;
4. the global surface holonomy separates the sectors;
5. vertex-to-edge gauge-of-gauge transformations lie in the kernel of the edge-to-face coboundary.

All computations are finite enumeration; there is no floating-point tolerance, sampling, or learned model.

**Pass condition:** every assertion in the script succeeds.  
**Failure meaning:** either the chosen cell-complex incidence convention or the claimed exact orbit/marginal statement is wrong; revise the mathematics, do not weaken the assertions.  
**What it establishes:** the stated finite counterexample and its exact coherence relation.  
**What it does not establish:** that higher categorical representations outperform ordinary models in all domains. That requires a prospective held-out comparison.

## 8. Differential experimental programme

The finite example suggests a hierarchy of prospective tests:

**Test A — 1-holonomy.** On a cycle graph with a \(\mathbb Z_2\) connection, compare systems sampled uniformly from the two gauge orbits. Every proper edge-subset marginal agrees; the Wilson loop around the full cycle differs. Compare local-statistics baselines with a model that preserves path composition.

**Test B — 2-holonomy.** Use the tetrahedral \(S^2\) model above. Train/select representations using only proper-face observations, then evaluate the global surface holonomy. A representation that does not retain the 2-coherent gauge structure should fail unless it has independently encoded an equivalent global invariant.

**Test C — noisy/approximate version.** Add observation noise and compare:
- local marginal embeddings;
- ordinary graph/message-passing models with matched capacity;
- path/surface-compositional representations;
- a higher-categorical representation with explicit gauge-equivalence and coherence data.

Measure held-out holonomy classification, calibration, sample complexity, memory, and compute. The higher-categorical model earns its complexity only if it improves generalization or calibration at matched resources.

**Falsifier:** once the baseline is given the same global information and capacity, the compositional/higher-categorical representation provides no reproducible predictive or sample-efficiency advantage. In that case the higher structure remains a useful language for invariance, not a demonstrated computational advantage.

## 9. The candidate theorem package

The following is the proper theorem ladder; do not collapse the conjectural steps.

**T1 — finite gauge-orbit obstruction (proved by enumeration plus a short cochain argument).** On the tetrahedral sphere, proper-face marginals do not distinguish the two \(\mathbb Z_2\) 2-form gauge sectors, whereas surface holonomy does.

**T2 — restricted Yoneda reconstruction (established theorem under density).** A dense probe subcategory reconstructs objects and mapping spaces by the restricted Yoneda nerve.

**T3 — physical probe-density theorem (open).** For a declared class of physical systems, characterize conditions under which physically executable probes are dense in the category of systems/transformations relevant to the target semantics.

**T4 — causal higher-realization theorem (open).** Give necessary and sufficient conditions for a physically implemented internal higher-categorical model to preserve the source response functor, including causal efficacy, history, and resource costs.

**T5 — approximate higher-semantic compression theorem (open).** Bound held-out response distortion as a function of truncation level, omitted higher morphisms, probe coverage, and realization resources.

A plausible novelty target is T3–T5 or a nontrivial, compositional certificate connecting them to Semplex's distinction-admissibility/resource semantics. T1 and T2 are foundations/benchmarks, not novelty claims.

## 10. Immediate next actions

1. Run the exact companion script and preserve its stdout/result as an artifact.
2. Add the tetrahedral gauge example to the controlled experiment registry only after checking existing experiment IDs and naming conventions.
3. Define the physical context \(\infty\)-category for one concrete platform (initially a finite controlled automaton or a gauge lattice model).
4. Specify the response \(\infty\)-functor and its natural transformations explicitly; avoid informal talk of “higher meaning”.
5. Prove the finite quotient/full-abstraction theorem in Lean, then add the response-functor preservation layer.
6. Obtain Gemini's independent G15/G16/G18 report and reconcile it; do not duplicate its already-running computations.
7. Only after a resource-safe compile window, run the new Lean module and the existing regression suite sequentially.

## 11. Source anchors and scope

- Schreiber, U. & Shulman, M., *Quantum Gauge Field Theory in Cohesive Homotopy Type Theory* — higher groupoids, cohesive homotopy theory, and gauge-field configuration spaces.
- Schreiber, U., *Differential Cohomology in a Cohesive \(\infty\)-Topos* — differential cohomology and higher geometric structures in cohesive homotopy theory.
- Sati, H. & Schreiber, U., *Higher Gauge Theory via Differential Nonabelian Cohomology in Cohesive Homotopy Theory* (2026 draft) — higher gauge structures and generalized cohomological charge/flux descriptions; treat as a research draft, not experimental confirmation.
- Yoneda lemma and density theorem for \(\infty\)-categories — the established reconstruction result underlying §3.
- Standard cellular/simplicial cohomology: the tetrahedral sphere has \(H^2(S^2;\mathbb Z_2)\cong\mathbb Z_2\); the two sectors above are its two cohomology classes.



## 12. Execution record

**2026-11-21 — exact finite test PASS.** The companion script was executed on the authorized PC with Python 3.13:

```powershell
python experiments\higher_gauge_surface_holonomy.py
```

The script completed with all exact assertions passing. It enumerated 64 edge gauge parameters, found an 8-element coboundary image equal to the even-parity face fields, recovered two gauge orbits of size 8, checked all 15 proper face-subset marginals (all identical across the two sectors), and verified that the global surface holonomy is 0 in one sector and 1 in the other. It also verified `d_1 d_0=0` for all vertex gauge parameters.

Machine-readable output is preserved at `artifacts/higher-gauge-surface-holonomy-20261121.json`. This is a finite exact mathematical validation, not a physical experiment and not a learned-model benchmark. The next empirical step is to compare representations on held-out surface holonomy at matched information and resource budgets.


**Second exact run — strict 2-groupoid laws PASS.** The script was strengthened to check the full finite composition structure. It verified identity, inverses, and composition for all enumerated 1-morphisms; identity, inverses, and vertical composition for 2-morphisms; 1,048,576 horizontal-composition instances; and 65,536 interchange-law instances. Every assertion passed. The test therefore checks more than the cohomology-sector count: it verifies the explicit strict 2-groupoid coherence operations in this finite model. Updated machine-readable results are in `artifacts/higher-gauge-surface-holonomy-20261121.json`.


## 13. Lean formal verification

The core cochain identities were formalized in `proofs/lean/HigherGaugeCohomology.lean` using Lean 4.12.0 and only the core `Lean` import. Direct compilation completed with exit code 0. A self-contained axiom-audit source, `proofs/lean/AuditHigherGaugeCohomology.lean`, was compiled separately; Lean reported that each of the following depends on no axioms:

- `d1_d0_zero`: the cochain identity (d_1d_0=0);
- `surfaceHolonomy_d1_zero): every exact 2-cochain has zero total surface holonomy;
- `surfaceHolonomy_gauge_invariant): total surface holonomy is invariant under every 1-form gauge transformation.

This is a checked theorem package for the algebraic core of the finite example. The exhaustive Python enumeration independently checks the finite orbit sizes, all proper-subset marginals, and strict 2-groupoid composition/interchange laws. It does not yet formalize the entire 2-groupoid in Lean, nor does it establish density of physical probes or the general semantic theorem.


## 14. Hand proof of the finite cohomology and marginal claims

The finite enumeration is an independent check; the orbit classification also has a short structural proof.

For each edge (e) of the tetrahedron, (delta e) has value 1 on exactly the two triangular faces incident to (e). Hence its total face parity is zero. Conversely, every pair of distinct triangular faces shares exactly one edge, and the coboundary of that edge is precisely the sum of the two corresponding face basis vectors. These pair-vectors generate the even-parity subspace of (mathbb Z_2^4). Therefore

[
operatorname{im}(delta:C^1	o C^2)
={binmathbb Z_2^4:	extstylesum_f b_f=0}.
]

The gauge orbits are the two cosets of this image. The quotient (C^2/operatorname{im}delta) is (mathbb Z_2), represented by total surface parity; this is the concrete cochain realization of (H^2(S^2;mathbb Z_2)congmathbb Z_2).

For a selected proper face set (J) of cardinality (kleq3), fix any assignment (ainmathbb Z_2^J). The remaining (4-k) bits must have one prescribed parity, so exactly (2^{4-k-1}=2^{3-k}) completions exist. This number is independent of the chosen sector (h) and of (a). Thus the normalized marginal is exactly uniform for every proper (J), not merely approximately close.

The strict 2-groupoid operations are:
- objects: (Bin C^2);
- 1-morphisms: (Lambda:B	o B+deltaLambda), composed by addition of edge cochains;
- 2-morphisms: (eta:LambdaRightarrowLambda+deltaeta), vertically composed by addition of vertex cochains;
- horizontal composition of 2-morphisms: addition of their vertex cochains.

Identities are zero cochains and every morphism is its own inverse. The equation (delta^2=0) guarantees that a 2-morphism does not change the source or target object. The interchange law is the commutativity of addition in (mathbb Z_2). The Python campaign exhaustively checks these laws in the finite instance; the Lean module proves the central (delta^2=0) and holonomy-invariance identities without axioms.


## 15. The deeper synthesis: causal Hankel semantics as a higher profunctor

The previous sections suggest a more precise common object than either a quotient, a coalgebra, or a Gramian alone: a **past-to-future response profunctor**. This makes the connection between relational meaning, categorical semantics, and system realization explicit.

Let:
- \(\mathcal H\) be a category (or \(\infty\)-category) of admissible past histories;
- \(\mathcal U\) be a category (or \(\infty\)-category) of future interventions and observation protocols;
- \(\mathcal V\) be a suitable response category, preferably symmetric monoidal if we want enriched composition.

Define the interventional Hankel object as a \(\mathcal V\)-valued profunctor

\[
\mathbf H:\mathcal H^{op}\times\mathcal U\longrightarrow\mathcal V.
\]

At an object pair \((h,u)\), \(\mathbf H(h,u)\) is the response object for applying future protocol \(u\) after past history \(h\). In a finite deterministic transducer, it is a matrix entry. In a stochastic system, it is a conditional distribution or kernel, with the precise measurable/enriched category fixed by the model. In a higher-gauge system, it can be a space of response traces with nontrivial homotopy and automorphism data.

For each past history \(h\), the row profile is the functor

\[
\mathsf S(h):=\mathbf H(h,-)\in\operatorname{Fun}(\mathcal U,\mathcal V).
\]

The semantic equivalence of histories is equivalence of these entire response functors:

\[
h\simeq_{\mathbf H}h'
\quad\Longleftrightarrow\quad
\mathsf S(h)\simeq\mathsf S(h').
\]

This is not merely equality of scalar outputs. It is equivalence of all future responses, natural with respect to protocol composition and refinement, and homotopy-coherent when \(\mathcal U,\mathcal V\) are higher categories.

### 15.1 Realizations are profunctor factorizations

An internal state category \(\mathcal Z\) gives a realization when \(\mathbf H\) factors through it. In a \(\mathcal V\)-enriched setting, take profunctors

\[
\mathbf R:\mathcal H^{op}\times\mathcal Z\to\mathcal V,
\qquad
\mathbf O:\mathcal Z^{op}\times\mathcal U\to\mathcal V.
\]

Their composite is the coend

\[
(\mathbf O\odot\mathbf R)(h,u)
=
\int^{z\in\mathcal Z}
\mathbf R(h,z)\otimes\mathbf O(z,u).
\]

A realization certificate is an equivalence

\[
\mathbf H\simeq\mathbf O\odot\mathbf R.
\]

When \(\mathbf R\) is representable by a functor \(r:\mathcal H\to\mathcal Z\), so that \(\mathbf R(h,z)\simeq\operatorname{Map}_{\mathcal Z}(r(h),z)\), the co-Yoneda lemma reduces the coend factorization to evaluation of \(\mathbf O\) at \(r(h)\). This recovers the response-nerve factorization \(\mathsf S\simeq\mathsf O\circ r^{op}\) in §15.2.

Interpretation:
- \(\mathbf R\) encodes how histories reach/instantiate internal states;
- \(\mathbf O\) encodes how internal states generate future responses;
- the coend identifies descriptions related by lawful internal-state transformations.

In finite-dimensional linear systems, this reduces to the familiar Hankel factorization \(H=OR\), with the coend/tensor composition becoming matrix multiplication. For ordinary deterministic automata, the internal state is a sufficient statistic of the past and the output map supplies future behaviour. For higher categorical semantics, the coend is a homotopy-coherent quotient: it retains equivalences among internal realizations rather than simply summing over labels.

This is a promising categorical generalization of the past-reachability/future-observability split. It does not yet prove that a minimum-cost factorization exists or is unique. Those require hypotheses on \(\mathcal V\), the system, and the allowed state categories.

### 15.2 Full abstraction becomes a property of the realization nerve

Let \(r:\mathcal H\to\mathcal Z\) be a proposed internal realization, and let \(\mathsf O:\mathcal Z^{op}\to\operatorname{Fun}(\mathcal U,\mathcal V)\) be the functor obtained by currying the observation profunctor \(\mathbf O:\mathcal Z^{op}\times\mathcal U\to\mathcal V\). Since \(\mathbf H\) is contravariant in its history variable, the response nerve has type \(\mathsf S:\mathcal H^{op}\to\operatorname{Fun}(\mathcal U,\mathcal V)\), and adequacy is a natural equivalence

\[
\mathsf S\simeq\mathsf O\circ r^{op}.
\]

The realization is fully abstract at the object level when

\[
r(h)\simeq r(h')
\quad\Longleftrightarrow\quad
\mathsf S(h)\simeq\mathsf S(h').
\]

At the full higher-categorical level, the stronger condition is that the induced map on mapping spaces is an equivalence:

\[
\operatorname{Map}_{\mathcal H}(h,h')
\simeq
\operatorname{Map}_{\operatorname{Fun}(\mathcal U,\mathcal V)}
(\mathsf S(h),\mathsf S(h')).
\]

The right-hand side is the space of natural transformations and all higher homotopies between response profiles. This condition is not automatic from object-level behavioural equivalence. It is exactly the kind of reconstruction guaranteed by a fully faithful nerve; restricted Yoneda gives it when the probe subcategory is dense.

This exposes three distinct levels that must not be conflated:

1. **Response sufficiency:** every protected response factors through the representation.
2. **Object-level full abstraction:** the representation identifies exactly the histories with equivalent response profiles.
3. **Higher full faithfulness:** all morphisms and higher coherences between histories are reconstructed by natural transformations between their profiles.

A system can satisfy (1) while retaining redundant states; satisfy (2) while failing to represent all higher transformations; and satisfy (3) only relative to the chosen context/probe category.

### 15.3 Why this is more than renaming the Hankel matrix

The ordinary Hankel matrix is a scalar- or vector-valued table indexed by pasts and futures. The profunctor generalization adds:
- lawful morphisms between histories and future protocols;
- naturality under composition and refinement;
- response objects that may themselves be spaces, distributions, or structured categories;
- higher automorphisms and homotopies between response transformations;
- a compositional realization interface through a coend.

The linear Hankel operator is recovered by applying a linearization functor to this richer object. K-theory, differential cohomology, and other generalized invariants can then be applied to suitable families/moduli of realizations, but they are not the profunctor itself and do not replace its response data.

### 15.4 The candidate Causal-Hankel Full-Abstraction Theorem

A defensible theorem target is:

> Let \(\mathbf H:\mathcal H^{op}\times\mathcal U\to\mathcal V\) be a response profunctor in an appropriate enriched or \(\infty\)-categorical setting. Suppose an internal realization \(r:\mathcal H\to\mathcal Z\) and observation functor \(\mathsf O:\mathcal Z^{op}\to\operatorname{Fun}(\mathcal U,\mathcal V)\) satisfy a homotopy-coherent factorization \(\mathsf S\simeq\mathsf O r^{op}\). Then:
> 1. object-level adequacy gives \(\ker(r)\subseteq\ker(\mathsf S)\): the representation cannot merge histories with inequivalent protected response profiles;
> 2. object-level full abstraction additionally requires the reverse inclusion, so \(r(h)\simeq r(h')\) iff \(\mathsf S(h)\simeq\mathsf S(h')\);
> 3. higher full faithfulness of \(r^{op}\) (equivalently \(r\)) follows if \(\mathsf S\) is fully faithful **and** \(\mathsf O\) is fully faithful on the essential image of \(r^{op}\). Without the latter hypothesis, full faithfulness of \(\mathsf S=\mathsf O\circ r^{op}\) does not by itself imply full faithfulness of \(r\).
>
> Every response-sufficient realization factors through the semantic quotient/localization when the kernel of its realization map is a congruence and the relevant quotient exists. In the \(\infty\)-categorical setting, the quotient must be specified as an effective quotient, localization, or suitable essential-image factorization; it cannot be assumed to exist merely because an object-level equivalence relation has been written down.

The theorem's nontrivial work is not the formal statement that a fully faithful functor reflects equivalences. It is to establish:
1. a physically grounded response profunctor \(\mathbf H\);
2. the appropriate enrichment and coend composition for the chosen physical domain;
3. density/full faithfulness of the actual probe family;
4. existence and stability of the realization factorization;
5. causal efficacy and resource bounds for the physical implementation.

### 15.5 A crucial obstruction: object profiles need not reconstruct morphisms

A family of probes may distinguish all objects and still fail to detect some morphisms. Thus a proof that two physical states are distinguishable by measurements does not yet prove that all transformations between physical states are represented. The relevant hierarchy is:

\[
\text{object separation}
\;\not\Rightarrow\;
\text{full faithfulness}
\;\Longleftrightarrow_{\text{dense probes}}\;
\text{mapping-space reconstruction}.
\]

This is one reason the \(\infty\)-categorical formulation matters. A model that records only connected components \(\pi_0\operatorname{Map}(P,X)\) can miss automorphisms and higher homotopies even when it distinguishes the underlying objects. Truncation is a controlled information loss and must be declared as such.

### 15.6 Connection to the Master Operator

The causal Hankel profunctor \(\mathbf H\) is the content-level object. A factorization \(\mathbf H\simeq\mathbf O\odot\mathbf R\) is a realization. The Master Operator \(\mathcal G_\lambda\) may be used to choose a geometry or finite-dimensional approximation for \(\mathbf Z\), but it cannot be identified with \(\mathbf H\) without a theorem.

The most coherent architecture is therefore:

\[
\boxed{
\text{physical interventions}
\to
\mathbf H
\to
\text{response nerve / semantic quotient}
\to
\text{profunctor factorization}
\to
\text{cost-sensitive realization}
}
\]

This is a more exact integration of the existing Causal-Realization Principle, the interventional Hankel operator, higher-categorical semantics, and the Master Operator than treating any one of them as the whole theory.


## 16. The exact logical-type / behavioural-quotient theorem already known

There is a precise classical theorem that should serve as the first logical bridge, rather than reinventing a vague “logical type equals behaviour” principle.

Let \(L=(S,\{\xrightarrow{a}\}_{a\in A},\models)\) be a labelled transition system with action labels \(A\) and protected atomic observations \(P\). Let \(\mathcal L_{\mathrm{HM}}\) be polymodal Hennessy–Milner logic:

\[
\varphi ::= \top\mid p\mid\neg\varphi\mid
(\varphi\wedge\psi)\mid\langle a\rangle\varphi,
\quad p\in P,\ a\in A.
\]

The type of a state is its complete theory in this language,

\[
\operatorname{tp}_{\mathrm{HM}}(s)
:=\{\varphi\in\mathcal L_{\mathrm{HM}}:s\models\varphi\}.
\]

Write \(s\equiv_{\mathrm{HM}}t\) when their theories agree, and \(s\sim_{\mathrm{bis}}t\) when they are bisimilar.

**Hennessy–Milner theorem.** For image-finite labelled transition systems,

\[
s\sim_{\mathrm{bis}}t
\quad\Longleftrightarrow\quad
\operatorname{tp}_{\mathrm{HM}}(s)
=
\operatorname{tp}_{\mathrm{HM}}(t).
\]

The forward implication holds generally (bisimulation preserves modal formulas). Image-finiteness is used for the converse: if a successor of \(s\) has no bisimilar matching successor of \(t\), finitely many successor states of \(t\) can each be separated by a formula; a finite conjunction then constructs a diamond formula separating \(s\) and \(t\). Without image-finiteness, finitary modal equivalence can be strictly coarser than bisimilarity. If infinitary conjunctions are admitted, bisimulation is characterized without the image-finite restriction.

Thus, for image-finite systems, the quotient by logical-type equality is exactly the bisimulation quotient. This is a rigorous instance of the desired equation:

\[
\text{logical type over the admissible action language}
=
\text{behavioural equivalence class}.
\]

**Physical reading (conditional).** If \(A\) is the complete set of physically admissible interventions in the model, \(P\) is the protected measurement vocabulary, and the LTS correctly models the system's transition possibilities, then the Hennessy–Milner type is an exact representation of its interventionally observable behaviour. The theorem does not establish that the selected actions are physically realizable, that the transition model is complete, or that the observations are causally grounded. Those remain independent empirical premises.

**Higher-categorical limitation.** Ordinary Hennessy–Milner types characterize object-level bisimulation. They do not reconstruct mapping spaces between systems, gauge automorphisms, 2-morphisms, or higher coherence. In the higher-categorical proposal, this theorem is the \(\pi_0\)/1-dimensional baseline. A higher logical language would need modalities whose semantics are spaces (or other higher objects), together with coherence-sensitive transformations; its expressivity theorem is open.

**Prior-art boundary.** The Hennessy–Milner theorem and bisimulation quotient are established results, not a novelty claim. The research target is to identify physically justified intervention languages and determine whether an enriched/higher analogue gives full mapping-space reconstruction, and how that interacts with causal efficacy and resource-bounded realization.




**Additional modal-semantics sources**
- Hennessy, M. & Milner, R. (1985), “Algebraic laws for nondeterminism and concurrency,” *Journal of the ACM* 32(1), 137–161.
- van Glabbeek, R. J. (2011), “Bisimulation,” in *Encyclopedia of Parallel Computing*. The survey states the LTS/bisimulation definitions, Hennessy–Milner logic, the general infinitary characterization, and the image-finite finitary theorem.
- Huth, M. (2005), “Labelled transition systems as a Stone space,” *Logical Methods in Computer Science* 1(1:1), 1–28, DOI: 10.2168/LMCS-1(1:1)2005. This connects the bisimulation quotient to a fully abstract domain model and a Stone topology.


## 17. Physical probe density: the exact missing hypothesis

The restricted Yoneda theorem gives a clean way to state what must be proved about physically available tests. Three notions should be separated.

Let \(\mathcal P\hookrightarrow\mathcal C\) be a full subcategory of probes and

\[
N_{\mathcal P}:\mathcal C\to\operatorname{Fun}(\mathcal P^{op},\mathcal S),
\qquad
N_{\mathcal P}(X)=\operatorname{Map}_{\mathcal C}(-,X)|_{\mathcal P}.
\]

**Object-separating / conservative probes.** The family separates objects up to equivalence if

\[
N_{\mathcal P}(X)\simeq N_{\mathcal P}(Y)
\Longrightarrow X\simeq Y.
\]

This says that no two inequivalent systems have the same probe profile. It is enough for object-level semantic identification, but not for reconstruction of transformations.

**Dense probes.** The family is dense if the restricted Yoneda nerve is fully faithful:

\[
\operatorname{Map}_{\mathcal C}(X,Y)
\simeq
\operatorname{Nat}(N_{\mathcal P}(X),N_{\mathcal P}(Y))
\]

for all \(X,Y\), including the higher homotopies in these mapping spaces. Density therefore reconstructs not only objects but all morphisms and higher equivalences between them.

**Colimit generation.** In the standard density presentation, each \(X\) is recovered as a canonical colimit of probes weighted by its mapping spaces:

\[
X\simeq
\operatorname*{colim}_{(P\to X)\in\mathcal P_{/X}} P,
\]

with the appropriate \(\infty\)-categorical/coend formulation. This is a useful constructive way to verify density, not a claim that every physical system is literally assembled from laboratory apparatuses.

The implications and non-implications matter:

\[
\text{density}\Rightarrow\text{object separation},
\qquad
\text{object separation}\not\Rightarrow\text{density}.
\]

A collection of measurements can distinguish every pair of states yet fail to detect some morphism between systems, or some nontrivial automorphism/higher homotopy. Therefore “all states are distinguishable” is not enough to claim that the logical language reconstructs the whole higher-categorical world.

### 17.1 Operational criteria for physical density

For a proposed physical probe subcategory \(\mathcal P_{\mathrm{phys}}\), the following are separate empirical/mathematical obligations:

1. **Realizability:** every probe object and probe morphism corresponds to a physically implementable apparatus/protocol, within declared tolerances.
2. **Compositional closure:** serial composition, parallel composition, refinement, and lawful coupling of probes remain represented.
3. **Object separation:** inequivalent target systems/states have distinguishable probe profiles.
4. **Morphism separation:** distinct physical transformations induce distinguishable natural transformations on probe profiles.
5. **Higher-coherence detection:** nontrivial loops, automorphisms, and higher homotopies are detected at the relevant truncation level.
6. **Descent:** local probe data glue to global response data, with gauge equivalences and obstruction classes handled explicitly.

Conditions 3–5 can be tested on a finite synthetic world with known ground-truth category. Condition 6 is a separate local-to-global theorem; it does not follow from object separation.

### 17.2 A finite density benchmark

Construct a finite category or finite 2-groupoid \(\mathcal C\) whose objects, morphisms, and 2-morphisms are explicitly enumerable. Define nested probe subcategories

\[
\mathcal P_0\subseteq\mathcal P_1\subseteq\cdots\subseteq\mathcal C
\]

by adding, in order, local observations, composite path probes, global loop probes, surface probes, and higher gauge-equivalence probes.

For each stage, compute:
- the partition of objects induced by \(N_{\mathcal P_n}\);
- the number of distinct morphisms identified by the restricted nerve;
- the induced maps on automorphism groups and higher homotopy sets;
- whether the restricted nerve is fully faithful on the chosen finite category.

This separates three outcomes (the “1-dense/2-dense” labels here are experimental shorthand for truncation levels, not standard terminology):
- **only separating:** object semantics is complete, but transformation semantics is not;
- **1-truncated fully faithful but not 2-truncated fully faithful:** objects and ordinary morphisms are reconstructed, but 2-morphisms/coherence are lost;
- **fully faithful at the tested truncation:** the probe nerve reconstructs all data in the finite model.

The tetrahedral \(S^2\) example is the first nontrivial test fixture: local face marginals do not separate its two surface-holonomy sectors, while the global surface probe does. The next extension should explicitly enumerate its 1- and 2-morphism mapping groupoids and calculate the restricted nerve for nested probe families.

**Falsifier for a proposed physical density claim:** find a nontrivial physical morphism or higher homotopy that remains invisible to every probe in the claimed complete family. The correct response is to narrow the reconstructed category or add the missing probe, not to declare the invisible structure meaningless.


## 18. The nontrivial \(\pi_2\): why the 2-groupoid is not reducible to its 1-truncation

The same finite model yields a stronger higher-categorical result than the surface-holonomy separation alone.

For the tetrahedral cochain complex

\[
C^0(S^2;\mathbb Z_2)
\xrightarrow{d_0}
C^1(S^2;\mathbb Z_2)
\xrightarrow{d_1}
C^2(S^2;\mathbb Z_2),
\]

the exact enumerations give

\[
|\operatorname{im}d_0|=8,\quad
|\ker d_1|=8,\quad
|\ker d_0|=2,\quad
|\operatorname{im}d_1|=8.
\]

Moreover, \(\ker d_1=\operatorname{im}d_0\), and \(\ker d_0\) consists precisely of the two constant vertex gauge parameters. Therefore the homotopy groups of the finite 2-groupoid at any object are

\[
\pi_0\simeq H^2(S^2;\mathbb Z_2)\simeq\mathbb Z_2,
\]
\[
\pi_1\simeq H^1(S^2;\mathbb Z_2)=0,
\]
\[
\pi_2\simeq H^0(S^2;\mathbb Z_2)\simeq\mathbb Z_2.
\]

Interpretation:
- \(\pi_0\) gives the two inequivalent surface-holonomy sectors;
- \(\pi_1=0\) says every 1-automorphism of a fixed 2-form field is 2-isomorphic to the identity;
- \(\pi_2=\mathbb Z_2\) says the identity 1-morphism has a nontrivial 2-automorphism, represented by the constant nonzero 0-form gauge transformation.

A 1-truncation retains the connected components and ordinary equivalence classes but erases this nontrivial \(\pi_2\). Thus an ordinary groupoid of gauge-equivalence classes is not equivalent to the full moduli 2-groupoid. It forgets genuine higher automorphism data.

This is the clearest finite demonstration in the current campaign of why higher categorical structure is not merely decorative. The higher morphisms encode gauge-of-gauge symmetry and the stacky automorphism structure of the moduli problem. Whether a particular physical semantics must preserve this data depends on its protected probes; the mathematical model establishes that the data exist and are erased by 1-truncation, not that every observable experiment can measure them.

The script now checks \((|\pi_0|,|\pi_1|,|\pi_2|)=(2,1,2)\) explicitly. The result is included in the machine-readable artifact. The finite homotopy-group computation is exact and exhaustive.


## 19. Expanded Lean proof package and exact axiom boundary

The Lean module now also proves:
- the kernel of \(d_0\) consists exactly of the two constant 0-cochains;
- every closed 1-cochain is exact on the tetrahedral sphere (\(\ker d_1=\operatorname{im}d_0\));
- a 2-cochain has zero surface holonomy iff it is exact;
- the canonical face-preimage construction for every zero-holonomy 2-cochain.

The expanded module compiles with Lean 4.12.0. The self-contained axiom audit reports:
- **no axioms** for \(d_1d_0=0\), exact-cochain holonomy zero, and gauge invariance of surface holonomy;
- dependency only on Lean's standard proposition-extensionality axiom \(\texttt{propext}\) for the four kernel/image and iff characterizations above.

No sorry, admit, unsafe declaration, or classical choice is used in these proofs. The exact axiom dependencies are recorded in the JSON artifact; the distinction matters and should not be collapsed into the blanket phrase “axiom-free.”


## 20. The finite model as a mapping 2-type: the direct bridge to higher gauge stacks

The cochain calculation has a standard homotopy-theoretic interpretation. The Eilenberg–Mac Lane space \(K(A,2)\) classifies degree-2 cohomology with coefficients in \(A\). The moduli space of unpointed 2-form \(A\)-gauge fields on a space \(X\), including gauge transformations and gauge-of-gauge transformations, is modeled by

\[
\operatorname{Map}(X,K(A,2)).
\]

For \(i\geq0\) in the relevant range, its homotopy groups at a component are

\[
\pi_i\operatorname{Map}(X,K(A,2))
\cong H^{2-i}(X;A).
\]

For \(X=S^2\) and \(A=\mathbb Z_2\), this gives exactly

\[
\pi_0=H^2(S^2;\mathbb Z_2)=\mathbb Z_2,\qquad
\pi_1=H^1(S^2;\mathbb Z_2)=0,\qquad
\pi_2=H^0(S^2;\mathbb Z_2)=\mathbb Z_2.
\]

This is the homotopy type independently recovered by the finite cochain/2-groupoid enumeration. The unpointed qualification matters: the nontrivial \(H^0\) term is precisely the constant gauge-of-gauge automorphism. A pointed mapping-space model would remove that global degree of freedom.

The finite construction can therefore be read as an explicit combinatorial model of the 2-truncated mapping space \(\operatorname{Map}(S^2,K(\mathbb Z_2,2))\). It is not just an arbitrary 2-category assembled to illustrate a point.

### 20.1 From the discrete model to cohesive higher gauge theory

In higher gauge theory, a higher gauge field is represented by a map into a higher classifying object; its mapping space is the moduli \(\infty\)-groupoid of fields, gauge transformations, gauge-of-gauge transformations, and their higher coherences. Cohesive homotopy type theory adds geometric/differential structure to this homotopy-theoretic picture. In the Schreiber–Shulman framework, cohesive structure is used to formulate gauge fields, higher bundles, and connections in cohesive \(\infty\)-toposes.

The finite \(\mathbb Z_2\) 2-form model is the discrete topological analogue of this architecture:
- \(K(\mathbb Z_2,2)\) is the classifying 2-type;
- maps \(S^2\to K(\mathbb Z_2,2)\) are 2-form gauge fields;
- paths in the mapping space are 1-form gauge transformations;
- homotopies between paths are 0-form gauge-of-gauge transformations;
- the homotopy groups measure sectors and higher automorphisms.

The differential refinement replaces the purely topological classifying object with a higher classifying stack carrying connection/curvature data (schematically, \(B^2U(1)_{\mathrm{conn}}\) for \(U(1)\) 2-gerbe data). It retains the higher moduli structure while adding differential observables and flux quantization.

### 20.2 A semantic character map must not silently truncate the moduli stack

The map from the full moduli 2-groupoid to its topological cohomology class records only \(\pi_0\). In this example it retains the two sectors but forgets the nontrivial \(\pi_2\). More generally, a generalized character map from a higher moduli stack to differential forms/cohomology may be informative without being fully faithful.

This suggests a precise audit for any proposed semantic invariant \(\chi:\mathcal M\to\mathcal I\):

1. compute its effect on \(\pi_0\): which physically distinct sectors does it separate?
2. compute its effect on \(\pi_1\): which gauge transformations/automorphisms survive?
3. compute its effect on \(\pi_2\) and higher groups: which gauge-of-gauge coherences are erased?
4. characterize its homotopy fibers: what distinctions remain invisible to the invariant?
5. determine whether those fibers are physically irrelevant gauge redundancy or protected structure for the intended task.

This is a better-defined candidate for a **semantic character map** than a universal scalar representation weight. It is a map of structured moduli objects, and its information loss is measured by its homotopy fibers/truncation rather than hidden inside one number.

### 20.3 K-theory and M-theory: exact scope

Differential K-theory is a differential refinement of topological K-theory: it retains a K-class together with connection/curvature-level data and associated differential-character information. The Chern character is a natural map from K-theory to cohomology, but it is not generally a fully faithful encoding of the full higher moduli stack.

The 2026 Sati–Schreiber draft *Higher Gauge Theory via Differential Nonabelian Cohomology in Cohesive Homotopy Theory* explicitly treats D/NS brane charges in unstable K-theory and M-brane charges in unstable cohomotopy. These are distinct generalized cohomology frameworks. The correct connection is not “M-theory is K-theory”; rather, higher gauge/flux data in different brane sectors are modeled by different generalized cohomological structures.

For this programme, the useful research question is whether a general semantic character construction can map a causally grounded realization stack into suitable differential/generalized cohomology invariants while explicitly recording the kernel, homotopy fibers, and lost higher automorphism data. The finite \(K(\mathbb Z_2,2)\) example gives a minimal test: the \(\pi_0\) character alone is not fully faithful because it discards \(\pi_2\).

**Sources:** Schreiber & Shulman, *Quantum Gauge Field Theory in Cohesive Homotopy Type Theory*, arXiv:1408.0054; Schreiber, *Differential Cohomology in a Cohesive \(\infty\)-Topos*, arXiv:1310.7930; Sati & Schreiber, *Higher Gauge Theory via Differential Nonabelian Cohomology in Cohesive Homotopy Theory*, arXiv:2606.12534 (2026 draft).


## 21. A general no-go theorem for scalar semantic characters

The finite example exposes a simple general obstruction.

**Truncation no-go.** Let \(\mathcal M\) be an \(\infty\)-groupoid and let \(\mathcal I\) be an \(n\)-truncated \(\infty\)-groupoid. If there is an object \(x\in\mathcal M\) with

\[
\pi_k(\mathcal M,x)\neq 0
\quad\text{for some }k>n,
\]

then no functor \(\chi:\mathcal M\to\mathcal I\) can be fully faithful.

**Proof.** Full faithfulness would require equivalences on all mapping spaces, in particular on the iterated loop spaces at \(x\). But an \(n\)-truncated target has vanishing homotopy groups above degree \(n\), while the source has a nonzero \(\pi_k\). This is a contradiction.

Special cases:
- a scalar or set-valued invariant is 0-truncated and cannot be fully faithful on a moduli space with nontrivial automorphisms;
- an ordinary groupoid/1-type cannot fully faithfully encode a 2-groupoid with nontrivial \(\pi_2\);
- a cohomology class in \(H^n(X;A)\), viewed only as a set of sectors, is the \(\pi_0\) of a higher mapping space and does not encode its higher automorphism groups.

For the tetrahedral example, the map

\[
\operatorname{Map}(S^2,K(\mathbb Z_2,2))
\longrightarrow
H^2(S^2;\mathbb Z_2)
\]

retains the two connected components but discards \(\pi_2\cong\mathbb Z_2\). It is a useful sector classifier, not a fully faithful semantic representation.

**Consequence for a universal representation currency.** A single scalar cannot be a fully faithful currency for arbitrary higher semantic structures. At best it is a task-specific projection of a richer invariant. A universal candidate must preserve the relevant mapping spaces (or carry an explicit truncation/error certificate). Differential cohomology, K-theory, and generalized character maps can be highly informative, but their \(\pi_0\)-valued classifications should not be mistaken for the full moduli \(\infty\)-groupoid unless their stack-level refinements are retained.

This no-go theorem is elementary homotopy theory. The research contribution would be to identify which higher homotopy groups are physically protected, construct the appropriate higher-valued semantic character, and quantify the task/resource cost of retaining or truncating them.


## 22. Verification record after the homotopy-group extension

The strengthened Python script was rerun after adding the \(\pi_0,\pi_1,\pi_2\) calculations. It passed all exact assertions:
- \((|\pi_0|,|\pi_1|,|\pi_2|)=(2,1,2)\);
- \(|\operatorname{im}d_0|=|\ker d_1|=8\), \(|\ker d_0|=2\), and \(|\operatorname{im}d_1|=8\);
- all 15 proper-face-subset marginals agree between the two sectors;
- 1,048,576 horizontal-composition instances and 65,536 interchange-law instances pass;
- surface holonomy separates the two components.

The expanded Lean module was compiled after the kernel/image additions. Its separate axiom audit completed with exit code 0 and the exact dependencies listed in §19 and the JSON artifact. No canonical file has been committed, pushed, or merged.


## 24. Consolidated candidate architecture for Semplex/Synesism

The current synthesis can now be stated as a layered architecture with explicit mathematical obligations.

### Layer 0 — Physical ontology

A declared class of physical systems and admissible transformations forms an \(\infty\)-category \(\mathcal C_{\mathrm{phys}}\) (or a lower truncation when justified). Irreversible processes remain non-invertible morphisms; gauge equivalences and protocol homotopies occupy their appropriate higher groupoids. No blanket replacement of physical dynamics by a group action is permitted.

### Layer 1 — Causal epistemology

A physically realizable probe subcategory \(\mathcal P_{\mathrm{phys}}\) and intervention category \(\mathcal U_{\mathrm{phys}}\) are declared. The interventional Hankel response profunctor \(\mathbf H\) records what each past history predicts under every future intervention, with the appropriate response enrichment (deterministic, stochastic, quantum, or higher-space-valued).

### Layer 2 — Semantic identity

The response nerve \(\mathsf S\) assigns each history its complete future response functor. Semantic equivalence is natural equivalence of these profiles. Object-level completeness requires probe separation; full higher completeness requires density/full faithfulness, which reconstructs mapping spaces and higher coherence.

### Layer 3 — Representation and compilation

An internal representation is a factorization

\[
\mathbf H\simeq\mathbf O\odot\mathbf R
\]

through a state category \(\mathcal Z\). In the representable case this induces \(\mathsf S\simeq\mathsf O r^{op}\). A translation between representations is admissible when it preserves the response profunctor up to a declared equivalence (or a quantified distortion). The semantic object is not the implementation: it is the invariant response structure the implementation must realize.

### Layer 4 — Physical realization and resource optimization

A representation must have a causal acquisition channel, counterfactual calibration, causal use, provenance where relevant, and a resource certificate. Among semantically adequate realizations, optimize a declared cost/distortion order. The order may be partial or vector-valued; forcing every task into one scalar currency would erase incomparable trade-offs.

The Master Operator can be a candidate approximation/selection mechanism for a finite-dimensional realization, but it becomes semantic only after a theorem connects its modes to the response profunctor and establishes the relevant preservation bounds.

### Layer 5 — Higher invariants and differential refinement

A semantic character map sends a higher realization/moduli object to selected topological, differential, or generalized-cohomological invariants. Its homotopy fibers explicitly record what it forgets. A \(\pi_0\)-only character is not fully faithful when higher automorphisms are present; differential/generalized cohomology should be used as structured invariant layers, not silently promoted to the whole semantics.

### Synesism interpretation (conditional, not a derivation)

This architecture offers a mathematically disciplined reading of Synesism:
- continuity is represented by coherent transformation and gluing, not by erasure of distinctions;
- identity is the stable relational role/invariant under admissible transformations;
- a distinction is a difference in protected response structure under some admissible probe;
- a system's identity can remain invariant while its configuration changes;
- gauge redundancy is not automatically a physical distinction, but its automorphism structure may still matter to the moduli semantics;
- local descriptions form a global system only when their overlap data satisfy descent.

These are candidate formal correspondences, not proofs that category theory entails Synesism or that Tegmark's Level IV hypothesis is true.

### The actual theorem frontier

The highest-value open result is now clearer:

> For a specified physically grounded class of systems, characterize when the interventional response profunctor admits a dense probe nerve and a resource-bounded, causally realized factorization that is fully abstract up to the protected higher structure.

This decomposes into independently falsifiable subclaims: physical probe realizability, density, coend factorization, causal realization, and resource bounds. A failure in any one layer narrows the theorem rather than being hidden by a global philosophical slogan.


## 25. Prior-art audit: the broad synthesis is not novel by itself

A targeted literature search found substantial direct antecedents. This materially narrows the novelty claim. The present architecture must not be presented as the first categorical/higher-categorical theory of causality, as the first Yoneda-based physical semantics, as the first categorical realization theory, or as the first K-theoretic treatment of causal equivalence.

| Prior work | Established overlap | What remains to be compared |
|---|---|---|
| J. A. Goguen, *Discrete-time machines in closed monoidal categories* (1975); J. Adámek, *Realization theory for automata in categories* (1976); Adámek, Ehrig & Trnková, *On an equivalence of system-theoretical and categorical concepts* (1980) | Categorical system theories, reductions, universal/minimal realizations, and categorical conditions for minimal reductions | Whether a higher, physically grounded response-probe nerve yields new density and resource-bounded full-abstraction theorems |
| Arbib & Manes, *Generalized Hankel Matrices and System Realization* (1980) | Generalized Hankel matrices for adjoint systems, including linear/bilinear systems, automata, and group systems; realization criteria and canonical/partial realization | Whether the interventional response profunctor contributes anything beyond a categorified presentation of known Hankel realization |
| Rosebrugh, Sabadini & Walters, *Minimal realization in bicategories of automata* (1998) | Minimal realization and behaviour categories in bicategories, including serial composition and (co)lax (co)monads | Whether the proposed higher-gauge/causal realization has new structure beyond bicategorical automata realization |
| Kissinger & Uijlen, *A categorical semantics for causal structure* (2019) | Categorical process semantics for causal structure, including classical probabilistic and quantum processes, quantum \(n\)-combs, and indefinite causal order | Whether the target is a different semantic problem (grounded system identity and representation translation) rather than another causal-process semantics |
| Mahadevan, *Universal Causality* (2023) | Higher-order categories/simplicial objects for interventions; categorical causal models; presheaves, Yoneda, universal arrows, Grothendieck categories of elements, and homotopy colimits | Whether physical probe density and causal realization are proved in a stronger sense than the paper's representable/presheaf architecture |
| Hefford & Wilson, *A Profunctorial Semantics for Quantum Supermaps* (LICS 2024) | Strong profunctors, profunctor optics, Yoneda/representability, and factorization of higher-order quantum processes into concrete networks | Whether a past-to-future causal Hankel profunctor with physical grounding and resource-sensitive minimal realization adds a distinct theorem |
| Mahadevan, *Higher Algebraic K-Theory of Causality* (2025) | cPROP causal models, natural transformations, observational equivalence, classifying spaces, simplicial nerves, and Grayson–Quillen group completion | This is algebraic K-theory of causal cPROP categories, distinct from topological/differential K-theory of bundles; compare exact constructions before proposing any new causal K-theory |
| Mahadevan, *Topos Causal Models* (2025 draft) | Topos-based causal models, interventions via subobject classifiers, limits/colimits, natural transformations, internal logic and Kripke–Joyal semantics | Whether the proposed physical ontology/epistemology split or density criterion yields additional universal properties |
| Hefford & Wilson, *A BV-Category of Spacetime Interventions* (2025 preprint); Wilson, Hefford & Hoffreumon, *Supermaps on Generalised Theories* (2026 preprint) | BV-categories of spacetime/intervention-context pairs; categorical supermaps and Yoneda representation for general circuit theories | Whether our contexts are more general than intervention-context pairs, and whether our target is state/meaning reconstruction rather than higher-order process semantics |

### 25.1 Immediate novelty corrections

1. **Profunctor composition by coends is standard.** It is a useful representation of the Hankel factorization, not a novelty claim by itself.
2. **Categorical and bicategorical minimal realization is established.** Any new realization theorem must identify the exact new hypotheses/conclusion.
3. **Yoneda-based causal representation is established prior art.** Universal Causality explicitly uses presheaves, Yoneda, representables, and homotopy colimits.
4. **Higher categorical causal equivalence and K-theoretic constructions already exist.** Mahadevan's 2025 work uses cPROPs, classifying spaces, and algebraic K-theory. Do not conflate this with Schreiber's topological/differential K-theory.
5. **Profunctorial semantics for higher-order quantum processes already exists.** The new framework must not claim to invent profunctorial causal semantics.

### 25.2 Plausible novelty frontier (not yet established)

The best remaining target is not a broad categorical synthesis. It is a *specific theorem* connecting all of the following in one declared physical domain:

- an intervention category whose morphisms are physically executable and whose causal direction is explicit;
- a response profunctor whose enrichment retains the relevant stochastic/quantum/higher-gauge data;
- a physically realizable probe subcategory with a proved density or quantified failure of density;
- a full-abstraction/minimal-realization theorem for representations of that response object;
- a resource-bounded approximate version with explicit distortion and complexity bounds;
- a causal realization witness (acquisition, counterfactual calibration, use, and provenance);
- a higher character map whose homotopy fibers quantify information lost by topological/differential invariants.

Even this combination may have close antecedents in categorical systems theory, causal process theories, or higher gauge theory. It must be compared theorem-by-theorem, not declared novel from its vocabulary.

### 25.3 What this spike contributes, honestly

The tetrahedral \(S^2\) model and Lean/Python verification are a new *Semplex research artifact*, but the underlying cohomology, mapping-space homotopy groups, and gauge 2-groupoid are standard mathematics. The artifact is useful as an exact benchmark and formalization fixture; it is not a new theorem in higher gauge theory.

**Required next literature task:** read the full Mahadevan 2023/2025 papers, Hefford–Wilson 2024/2025/2026 papers, and the categorical realization references. Produce a claim-by-claim overlap matrix before writing a novelty statement or submission abstract.


### 25.4 Bibliographic anchors for the prior-art matrix

- Goguen, J. A. (1975). “Discrete-time machines in closed monoidal categories. I.” *Journal of Computer and System Sciences*, 10(1), 1–43. DOI: 10.1016/S0022-0000(75)80012-2.
- Adámek, J. (1976). “Realization theory for automata in categories.” *Journal of Pure and Applied Algebra*, 9(3), 281–296.
- Adámek, J., Ehrig, H. & Trnková, V. (1980). “On an equivalence of system-theoretical and categorical concepts.” *Kybernetika*, 16(5), 389–410.
- Arbib, M. A. & Manes, E. G. (1980). “Generalized Hankel Matrices and System Realization.” *SIAM Journal on Mathematical Analysis*, 11(3), 405–424. DOI: 10.1137/0511038.
- Rosebrugh, R., Sabadini, N. & Walters, R. F. C. (1998). “Minimal realization in bicategories of automata.” *Mathematical Structures in Computer Science*, 8(2), 93–116. DOI: 10.1017/S0960129597002454.
- Kissinger, A. & Uijlen, S. (2019). “A categorical semantics for causal structure.” *Logical Methods in Computer Science*, 15(3:15). DOI: 10.23638/LMCS-15(3:15)2019.
- Mahadevan, S. (2023). “Universal Causality.” *Entropy*, 25(4), 574. DOI: 10.3390/e25040574.
- Hefford, J. & Wilson, M. (2024). “A Profunctorial Semantics for Quantum Supermaps.” *Proceedings of LICS 2024*, 43:1–43:15. DOI: 10.1145/3661814.3662123; arXiv:2402.02997.
- Mahadevan, S. (2025). “Higher Algebraic K-Theory of Causality.” *Entropy*, 27(5), 531. DOI: 10.3390/e27050531.
- Mahadevan, S. (2025 draft). “Topos Causal Models.” arXiv:2508.08295.
- Hefford, J. & Wilson, M. (2025 preprint). “A BV-Category of Spacetime Interventions.” arXiv:2502.19022.
- Wilson, M., Hefford, J. & Hoffreumon, T. (2026 preprint). “Supermaps on Generalised Theories.” arXiv:2602.23865.

The matrix is a targeted initial audit, not an exhaustive systematic review. Full-text comparison is still required before asserting a novelty gap.


**Repository regression:** after the new experiment and Lean module were in place, the full Semplex suite completed with **152 passed, 2 skipped** in 269.88 seconds (exit code 0). This validates the existing repository test suite; it does not by itself prove the new theoretical claims.


## 26. Resource-indexed restricted Yoneda: finite benchmark and corrected research frontier

### 26.1 Exact finite result (Spike 19)

For a small category \(\mathcal C\) and full subcategory \(\mathcal P\hookrightarrow\mathcal C\), the restricted Yoneda functor is

\[
y_{\mathcal P}(X)(P)=\operatorname{Hom}_{\mathcal C}(P,X),
\qquad
y_{\mathcal P}:\mathcal C\to[\mathcal P^{op},\mathbf{Set}].
\]

For every \(X,Y\), the canonical comparison is

\[
\Phi_{X,Y}:\operatorname{Hom}_{\mathcal C}(X,Y)
\to\operatorname{Nat}(y_{\mathcal P}(X),y_{\mathcal P}(Y)).
\]

Spike 19 exhaustively enumerates these natural transformations in three finite categories. The result separates four properties which must not be conflated:
- object separation (non-isomorphic restricted profiles);
- faithfulness (no original morphisms collapsed);
- fullness (no spurious natural transformations);
- full faithfulness (both).

The parallel-pair category \(A \overset{f,g}{\rightrightarrows} B\) is decisive. Either singleton probe \(\{A\}\) or \(\{B\}\) separates the objects, but neither is fully faithful. With \(\{A\}\), there are four extra natural transformations in total; with \(\{B\}\), the distinct arrows \(f,g\) collapse. The full probe category \(\{A,B\}\) is fully faithful. Under the synthetic costs \(c(A)=1,c(B)=3\), the minimum fully faithful probe cost is exactly 4.

Conversely, in the walking-arrow category \(0\to1\), the proper full subcategory \(\{1\}\) is fully faithful. Thus the correct condition is density/full faithfulness, not "probe every object".

The discrete two-object category with probe \(\{A\}\) gives a second object-separating but non-full example: a spurious natural transformation appears in the \(B\to A\) direction.

**Verification:** `pytest -q tests/test_restricted_yoneda.py` reports 7 passed in 0.11s. The script validates category laws, enumerates all component functions, imposes naturality for every probe arrow, and compares the exact canonical image with every natural transformation.

Artifacts:
- `experiments/SPIKE_19_PLAN.md`
- `experiments/SPIKE_19_REPORT.md`
- `experiments/restricted_yoneda_probe_benchmark.py`
- `tests/test_restricted_yoneda.py`
- `artifacts/restricted-yoneda-probe-benchmark-20261121.json`

This is a finite ordinary-category benchmark, not a new theorem, not an \(\infty\)-categorical result, and not yet a physical experiment. Probe costs are declared synthetic weights.

### 26.2 The executable-probe bridge: a useful categorical identification

For each object \(X\), the representable presheaf is \(yX=\operatorname{Hom}_{\mathcal C}(-,X)\). A subpresheaf

\[
M_X\hookrightarrow yX
\]

is exactly a sieve on \(X\): a collection of arrows into \(X\) closed under precomposition. Therefore, if the physically executable probes into \(X\) are to form a functorial family under refinement/precomposition, they must form a sieve.

This is not a new categorical construction. It identifies the correct place where physical admissibility enters the existing mathematics:

- the abstract representable \(yX\) contains all categorical probes;
- the physically executable family is a subpresheaf \(M_X\);
- its closure condition is sieve closure;
- the family of sieves regarded as jointly sufficient probes leads to coverage/Grothendieck-topology questions;
- sheaf/stack descent then concerns gluing local response data over those covers.

The condition is substantive. An arbitrary hand-picked set of physically feasible experiments need not be closed under precomposition. If it is not, it cannot be used as a subpresheaf without either changing the probe semantics or taking a closure that may introduce operations that are not physically executable.

### 26.3 Direct prior art discovered: the novelty frontier narrows again

The earlier §25 matrix needs the following corrections.

**Mahadevan, *Universal Causality* (2023):**
- Explicitly states the Causal Reproducing Property as the Yoneda isomorphism between causal morphisms and natural transformations of representables.
- Uses presheaf categories and the canonical colimit representation by representables (density).
- Models sequences of interventions as a higher-order category over simplicial objects.
- Uses category-of-elements/Grothendieck constructions and homotopy colimits.
- Its own future-work section leaves sheaf-based causal inference/Grothendieck topologies for subsequent work and says the use of simplicial sets suggests higher-order causal models as future work.

This means the ordinary restricted-Yoneda benchmark is an executable illustration of standard theory, while the broad use of Yoneda/density for causal reconstruction is already explicitly in prior work.

**Mahadevan, *Topos Causal Models* (2025 draft; later NeurIPS 2025 paper *Universal Causal Inference in a Topos*):**
- Explicitly constructs causal models using Yoneda presheaves and Grothendieck topologies/sieves.
- Uses sheaves to collate local autonomous mechanisms into a global model.
- Models interventions as subobjects/monomorphisms and develops an internal logic.
- States a universal factorization property for causal functors mapping decomposable structure to probabilistic semantics.

Therefore, neither the identification of executable probes with sieves nor the use of sheaves for causal local-to-global assembly can be claimed as novel in itself.

**Hefford, Wilson & Hoffreumon, *Supermaps on Generalised Theories* (2026):**
- Proves a Yoneda lemma for categorical supermaps on physical theories with channel-state duality.
- Shows categorical supermaps coincide with concrete Choi–Jamiołkowski supermaps under its hypotheses.
- Extends the analysis to concrete profunctors and general circuit theories.

Thus a physical interpretation of probes, a higher-order process category, and Yoneda-based reconstruction have close and direct physical-theory antecedents.

**Budgeted causal experimental design:**
- Hyttinen, Eberhardt & Hoyer (2013) give constructive optimal experiment selection for identifying causal structures.
- Lindgren, Kocaoglu, Dimakis & Vishwanath (2018) study minimum-cost intervention design and approximation algorithms.
- Agrawal et al. (2019) give ABCD-Strategy for budgeted targeted causal discovery, with approximation/optimization guarantees.
- Later work studies active learning and intervention design under finite samples and cost constraints.

Hence "choose the most informative interventions under a budget" is also established. Any new claim must be more precise than generic cost-sensitive probe selection.

### 26.4 The narrowed problem worth pursuing

The potentially nontrivial intersection is now:

1. A physical system category \(\mathcal C_{\mathrm{phys}}\) with explicit operational semantics.
2. A physically executable **subpresheaf/sieve** \(M_X\hookrightarrow yX\) for each target system, not merely a freely chosen abstract probe subcategory.
3. A cost/resource structure on executable arrows and their refinements, potentially vector-valued and context-dependent.
4. A task-protected higher response object (spaces, groupoids, stochastic/quantum channels), not just a set-valued presheaf.
5. A criterion for when the executable subpresheaf family is dense/full-faithful on the relevant protected subcategory, and a quantitative obstruction when it is not.
6. A compiler/realization theorem translating between implementations while preserving the protected response structure with explicit resource and distortion certificates.

Even this is a candidate synthesis, not a novelty claim. The key issue is whether the physical executable-probe constraint creates a genuinely new theorem or merely instantiates known sieve/coverage, active experimental design, and categorical realization theory.

### 26.5 Next exact experiment (Spike 20)

Construct finite categories with an explicitly designated set of executable arrows into each target. Test whether:
- executable arrows form sieves under precomposition;
- non-closed executable sets fail to define a presheaf;
- sieve closure may add physically infeasible arrows;
- budget truncation breaks sieve closure or coverage axioms;
- a coverage can be generated from admissible families without assuming pullbacks exist;
- the resulting restricted response functor is faithful/full/dense;
- the minimal budget needed for full faithfulness differs from the minimum budget needed only for object separation.

The next report must compare these constructions against standard sieves, coverages, Grothendieck topologies, and budgeted experimental design. It must not rename those constructions and claim novelty.


## 27. Direct semiotic-category antecedent: Thiopoulos (1992)

A major prior-art source has now been identified:

**Constantin Thiopoulos (1992), “Towards a Logic of Semiotic Systems,” *Mathématiques et sciences humaines* 117, 49–60.**

The paper is unusually close to the broad conceptual foundations of this programme:
- meaning is treated as an entity's position/interlinking in a network, not merely a denotational label;
- a semiotic system is a weighted directed graph of terms;
- it is formalized as a category with weighted morphisms;
- the interpretation/meaning of a term is defined through its incoming weighted relations;
- a “situation” is a context-generated full subcategory representing relevant interactions;
- a situational category collects such contexts;
- a hypercategory has semiotic categories over a shared alphabet as objects and functors as morphisms;
- invariant morphisms between situational categories are used to model consensual domains between structurally coupled systems.

This is a direct conceptual and formal antecedent to structural/relational semantics, contextual meaning, weighted categorical representations, and cross-system invariants. It must be acknowledged in any future statement of the programme's foundations. Its explicit philosophical basis is phenomenology/autopoiesis (Heidegger, Merleau-Ponty, Maturana and Varela); that is not automatically the same as the intended naturalized, physically grounded, non-spiritualist Semplex/Synesism programme.

### 27.1 Formal audit of the multiplicative threshold-sieve construction

Thiopoulos Definitions 2.20–2.21 assign
\[
w(f\circ g)=w(f)w(g)
\]
and propose thresholded incoming arrows
\[
R_B(X)=\{f:Y\to X\mid w(f)\ge B\}
\]
as a sieve/topological interpretation (Theorem 2.1).

A sieve must be closed under precomposition. A finite counterexample is
\[
Q\xrightarrow{u}P\xrightarrow{g}X,\qquad h=g\circ u,
\]
with \(w(u)=0.5,w(g)=0.9,w(h)=0.45\), identity weights 1. At \(B=0.8\), \(g\) and \(id_X\) belong to the threshold family but \(h\) does not. Since \(g\in R_B(X)\) and \(u:Q\to P\), sieve closure requires \(h=g\circ u\in R_B(X)\). It follows that \(R_B(X)\) is not a sieve.

The displayed proof of Theorem 2.1 appears to reason in the reverse direction (a composite meeting the threshold implies its factor has sufficient weight), whereas sieve closure requires a threshold-qualified arrow to remain qualified after precomposition. The article's printed type for its “Grothendieck topology” also appears underspecified: a Grothendieck topology assigns a collection of covering sieves to each object, while Definition 2.21 appears to return a single threshold sieve. This may be a notation/omission issue, but it does not repair the counterexample to sieve closure.

For fixed \(B\), the exact criterion is
\[
w(f)\ge B\Longrightarrow w(f\circ u)\ge B
\]
for every composable \(f,u\). Under multiplicativity, if this is required for every \(B>0\), then positive-weight arrows force \(w(u)\ge1\) for all admissible precompositions. Hence nontrivial normalized weights in \((0,1]\) do not generally yield sieves by simple thresholding.

This is a narrow formal critique, not a rejection of the paper's overall semiotic programme. The paper's broader intuition and constructions of situational/hypercategories remain relevant antecedents.

### 27.2 Resource-cost counterpart

Spike 20 gives the additive-cost analogue. If \(c(g)=1\) and \(c(h)=3\), the budget sublevel at 1 contains \(g\) but not its precomposition \(h\). Its sieve closure adds \(h\) and has cost 3. Thus budget truncation and categorical refinement closure conflict unless the resource model explicitly accounts for the cost of refinements or restricts the admissible refinement category.

### 27.3 Consequences and open repair strategies

Do not claim novelty for:
- meaning as network position/relational role;
- weighted semiotic categories;
- contextual/situational subcategories for meaning;
- category-theoretic modelling of intersubjective/structural invariants.

Potentially useful, but not yet novel, repair directions:
1. restrict the probe category to physically admissible refinements and test closure there;
2. define resource-graded coverages with explicit pullback/refinement cost laws;
3. use a different weight-composition law or a quantale-enriched semantics whose threshold cuts are provably sieves;
4. keep raw executable experiments separate from their categorical closure and attach an explicit closure-cost certificate.

**Spike 20:** `experiments/SPIKE_20_REPORT.md` and the exact counterexample artifacts record the result. The combined restricted-Yoneda/sieve test suite reports 16 passed. No general Lean theorem or physical experiment is claimed.

**Primary source:** Thiopoulos, C. (1992). “Towards a Logic of Semiotic Systems.” *Mathématiques et sciences humaines*, 117, 49–60. Numdam PDF: https://www.numdam.org/article/MSH_1992__117__49_0.pdf.


## 28. Resource-relative probe presheaves and the free/costly split

Spike 21 develops a precise repair to the sieve obstruction.

### 28.1 Candidate lemma

Let \(\mathcal C\) be a category, \(\mathcal F\subseteq\mathcal C\) a wide subcategory of free refinements, and let
\[
c:\operatorname{Mor}(\mathcal C)\to(Q,\oplus,0,\le)
\]
take values in an ordered commutative monoid, with:
\[
c(id_X)=0,\qquad c(g\circ f)\le c(g)\oplus c(f),
\qquad c(u)=0\text{ for }u\in\mathcal F.
\]

For a target \(X\) and budget \(B\), define
\[
M_B(X)(P)=\{f:P\to X\mid c(f)\le B\},\qquad P\in\mathcal F.
\]

Then if \(u:Q\to P\) is free,
\[
c(f\circ u)\le c(f)\oplus c(u)=c(f)\le B.
\]
So precomposition restricts to a map \(M_B(X)(P)\to M_B(X)(Q)\). The identity and associativity laws make \(M_B(X)\) a presheaf on \(\mathcal F\), i.e. a sieve relative to free refinements.

For any target arrow \(h:X\to Y\) of cost \(K\), postcomposition induces a grade-shifting map
\[
M_B(X)\to M_{K\oplus B}(Y),\qquad f\mapsto h\circ f.
\]
Associativity makes this map natural with respect to free refinements. If \(h\) is itself free, the grade is unchanged.

This works with vector-valued costs in a partially ordered commutative monoid; no universal scalarization is needed.

### 28.2 Exact finite witness

The Spike 21 finite category has free \(u:Q\to P\) of cost 0, \(g:P\to X\) of cost 1, \(h=g\circ u:Q\to X\) of cost 1, and paid \(v:R\to Q\) of cost 2, with \(k=h\circ v:R\to X\) of cost 3.

At budget 1:
\[
M_1(X)=\{id_X,g,h\}.
\]
It is a sieve relative to the free subcategory (because \(g\mapsto h\) under \(u\)), but not a sieve in the full category (because the paid refinement \(v\) maps \(h\mapsto k\), which exceeds budget).

A paid target transformation \(t:X\to Y\) of cost 2 induces
\[
M_1(X)\to M_3(Y)
\]
by postcomposition, naturally with respect to \(u\).

### 28.3 Direct prior art: Marsden & Zwart (2018)

Marsden & Zwart, “Quantitative Foundations for Resource Theories,” CSL 2018, DOI 10.4230/LIPIcs.CSL.2018.32, already supply the broad machinery:
- quantale-enriched categories for costs, probabilities, and connection strengths;
- quantale-valued presheaves and profunctors;
- explicit separation of freely available conversions from costly conversions;
- bimodules closed under pre/postcomposition by free conversions;
- canonical reflexive-transitive closure of conversions.

Therefore the free/costly categorical split, resource-enriched presheaves/profunctors, and closure under free conversions are not new. Spike 21 is a finite operational specialization and a useful proof fixture, not a novelty claim.

### 28.4 Remaining theorem frontier

A possible Semplex-specific theorem must add more than resource enrichment:
1. physical executability and provenance of causal probes;
2. a protected higher response object (spaces/groupoids/channels) with explicit truncation control;
3. a full-abstraction/minimal-realization condition for causal response semantics;
4. a resource-graded comparison of translations/compilers with explicit distortion;
5. a theorem that identifies when a given physically realizable probe family is sufficiently dense for the protected semantics.

This must be compared against resource theories, causal experimental design, categorical realization, and higher causal-process semantics. No novelty is claimed yet.

### 28.5 Formal verification status

A core-Lean draft exists at `proofs/lean/ResourceRelativeProbes.lean`. It states the costed-category structure and proves the intended presheaf action and grade-shift laws in draft form. **It has not been compiled or axiom-audited.** The PC had approximately 1.4 GB free RAM at the time; the established >=2 GB build safety gate was respected. The finite Python model and 23-test suite pass.

Artifacts: `experiments/SPIKE_21_REPORT.md`, `experiments/resource_relative_probe_sieves.py`, `tests/test_resource_relative_probe_sieves.py`, `artifacts/resource-relative-probe-sieves-20261121.json`.


## 29. Stronger Universal Causality antecedent: the 2022 UCM already has interventions, observations, enrichment and resource profunctors

A full-text read of Mahadevan's 2022 preprint, *On the Universality of Diagrams for Causal Inference and the Causal Reproducing Property* (arXiv:2207.02917v1), shows a closer overlap than the abstract-level audit suggested.

The Universal Causal Model is explicitly a tuple
\[
\langle\mathcal C,\mathcal X,\mathcal I,\mathcal O,\mathcal E\rangle.
\]
In the paper's Definition 4:
- \(\mathcal C\) is a category of causal objects and morphisms, and may be \(\mathcal V\)-enriched to capture additional structure in hom-objects;
- \(\mathcal X\) contains construction objects, explicitly including profunctors between posets to represent resource models;
- \(\mathcal I\) is an intervention category whose intervention objects map from an experimental-design category \(\mathcal E\) into \(\mathcal C\);
- \(\mathcal O\) is a functor category of observation objects, including partial/noisy views of causal objects;
- \(\mathcal E\) is an evaluation category for intervention outcomes.

The paper also:
- states the Causal Reproducing Property \( \operatorname{Hom}_{\mathcal C}(X,Y)\cong\operatorname{Nat}(\operatorname{Hom}_{\mathcal C}(-,X),\operatorname{Hom}_{\mathcal C}(-,Y))\);
- discusses unobservable confounders by approximating the full presheaf \(\operatorname{Hom}_{\mathcal C}(-,X)\) from an observable subcategory \(\mathcal D\) using Kan extensions;
- explicitly warns that practical scaling requires representation-specific and application-specific constraints;
- cites almost-optimal intervention sets and active causal experimental design.

This is a direct antecedent to the combination of intervention categories, experimental designs, observation functors, enriched causal categories, resource profunctors, and observable-subcategory approximation. Therefore the following are not novel by themselves:
- treating experiments as a category of interventions;
- distinguishing intervention protocols from observations;
- using a \(\mathcal V\)-enriched causal category;
- using profunctors for resource models;
- using Kan extensions to approximate causal semantics from observable subcategories.

Combined with Marsden–Zwart (2018), the resource-relative probe presheaf of §28 is an expected specialization of established machinery.

### 29.1 Refined remaining question

The most defensible target is now more specific than a resource-aware Yoneda construction:

> Given a physically executable/observable intervention subcategory, a resource-enriched causal response semantics, and a protected higher response structure, derive computable lower/upper Kan-extension bounds on the global semantics, prove when those bounds collapse (exact reconstruction/full abstraction), and give optimal resource-cost lower bounds for shrinking the residual gap.

The 2022 UC paper uses Kan extensions to approximate from observable objects, but the retrieved treatment does not establish a quantitative resource-costed *gap* between lower and upper semantic extensions, a full-abstraction criterion for heterogeneous representation translations, or higher-moduli preservation with explicit truncation distortion. These are candidate gaps only; they require a more complete comparison with enriched Kan extensions, active experimental design, and categorical realization theory.

A useful finite prototype is to take a poset-valued response presheaf and compute the interval between its left and right Kan extensions from an observable subposet. The interval width is an identifiability certificate: zero width means the response is determined at that object by the available probes; positive width means multiple completions remain. A costed probe-selection problem can then seek to reduce this gap. This is a proposed experiment, not yet a theorem about arbitrary causal categories.

**Primary source:** Mahadevan, S. (2022). *On the Universality of Diagrams for Causal Inference and the Causal Reproducing Property*, arXiv:2207.02917v1. In particular §1, Definition 4, §7.3, and Summary/Future Work.


## 30. Resource-bounded Wilson-loop POMDP: concrete realization fixture (Spike 25)

The abstract response quotient and posterior predictive-state interface is now instantiated in a finite controlled gauge model. A three-vertex ring carries a Z3 connection. Vertex gauge transformations act on edge labels by a_i -> a_i + g_(i+1)-g_i; the gauge-invariant hidden state is the Wilson-loop holonomy theta=sum_i a_i mod 3. Exhaustive enumeration verifies 27 connections, 27 gauge transformations, and exactly three gauge orbits of size nine.

The controller uses primitive clockwise/counterclockwise edge actions of unit cost. Its physical path state consists of current vertex and accumulated parallel-transport phase. Open paths have no gauge-invariant scalar readout. Backtracking loops have zero winding. The first noncontractible loops (+++ and ---) cost three and reveal theta or -theta through a noisy Z3 observation channel.

The agent's information state is a belief b over theta. The clockwise-loop channel is
\[
K_\eta=\eta\mathbf1\mathbf1^\top+(1-3\eta)I,\qquad
\det K_\eta=(1-3\eta)^2.
\]
This gives an exact pair of thresholds:
- intervention budget below three collapses all beliefs into one response-equivalence class;
- at budget three or more, the belief representation is fully abstract exactly when eta is not 1/3;
- at eta=1/3, the observation channel is uniform and all finite repeated-loop response distributions are prior-independent.

The implementation uses rational arithmetic. It checks gauge invariance of all closed control paths through length six, Bayesian updating, predictive sufficiency, repeated-observation dependence, and the exact resource/noise thresholds. Thirteen focused tests pass. See Spike 25 and the standalone model note for the complete derivation and prospective falsification design.

This is a finite exact realization, not a new result in gauge theory, POMDP theory, or higher category theory. It is a bridge fixture for connecting the generic causal-realization interface to a physical hidden-state model. In particular, the current Lean bridge has not yet been instantiated with this concrete model.


**Full-abstraction interface:** the physical history space maps to posterior beliefs. Costed tests are closed primitive-control words; each response is a distribution on Z3. Below cost three, the history quotient is a singleton. At cost three or more and eta != 1/3, histories are equivalent exactly when their posteriors agree. The quotient is the reachable-posterior image (or the full two-simplex if all beliefs are admitted). This is a concrete instance of the generic causal-realization sufficiency/separation conditions, but the specialized adapter remains to be formalized in Lean.


**Posterior-Hankel connection:** with uniform prior and one-loop observation histories, the posterior-history matrix and future-test matrix both equal K_eta. Thus H=RO=K_eta^2. Writing P_perp=I-(1/3)11^T and lambda=1-3 eta gives centered H=lambda^2 P_perp, Wc=Wo=lambda^2 P_perp, and balanced Gram Wc^(1/2)WoWc^(1/2)=lambda^4 P_perp. At eta=1/6 these are respectively (1/4)P_perp and (1/16)P_perp. The two nonzero squared singular values of centered H match the two nonzero balanced-Gram eigenvalues exactly. This connects the Wilson-loop model to the posterior-history Hankel constructions of Spikes 23 and 24. Exact matrices are in the artifact JSON.
