# Statistical causal anchors, prime decompositions, and GRH connections
## Research note — 2026-11-23

## 1. Repository finding: stochastic grounding already existed

The Lean project already contained `StochasticInterventionGrounding.lean`. It models finite discrete distributions as lists of natural-number weights and defines normalized-distribution equality by cross multiplication. It includes stochastic observation/evolution kernels, intervention traces, deterministic embeddings as Dirac kernels, channel coarsening, and a noisy hidden-bit example.

This changes the next step: do not rebuild stochastic semantics. Extend it toward statistical identifiability and finite-sample reliability.

## 2. New formal result: complementary noisy anchors

Added:
- `proofs/lean/StatisticalCausalAnchorAdequacy.lean`
- `proofs/lean/AuditStatisticalCausalAnchorAdequacy.lean`

A statistical channel maps an external state and affordable probe to a finite weighted outcome distribution. Statistical indistinguishability means equality of the normalized distributions for every affordable probe.

The central criterion is the exact kernel-intersection statement:
joint identification holds iff no distinct pair of external states is statistically indistinguishable to both channels.

Finite example:
- External state is a pair of bits.
- First sensor measures only coordinate 1; second sensor only coordinate 2.
- Each sensor has 3:1 likelihood weights (probability 3/4 of reporting the measured bit correctly).
- Either sensor alone leaves one coordinate invisible.
- The pair of channels identifies the full two-bit state exactly at budget 1 per channel.
- At budget 0 neither channel has an affordable probe, so all states remain observationally equivalent.

The result is distribution-level identifiability, not a finite-sample concentration theorem. The proof audit reports standard `propext` and `Quot.sound` dependencies; no `sorryAx` is reported for the joint-identification theorem. The complete project verification is still to be run after this addition.

## 3. The next statistical theorem

Do not conflate three notions:

1. **Distributional identifiability:** two hypotheses induce different probability distributions.
2. **Finite-sample distinguishability:** a decision rule has error below a chosen threshold after (n) observations.
3. **Resource-bounded identification:** the sample count, intervention cost, and apparatus cost fit a budget.

The new module proves (1). The next target is (2) and (3), ideally using total variation, likelihood ratios, and a finite-sample testing bound. A good first formal target is the binary 3:1 channel: quantify the Bayes-optimal error after (n) independent observations, then prove an exponential upper bound for majority/MAP decoding. Independence must be explicit; repeated interventions in a stateful POMDP are not automatically i.i.d.

Data processing is a key invariant: deterministic post-processing cannot increase statistical distinguishability (e.g. total variation or KL divergence). An independently acquired anchor can add information; a decoder of the same profile cannot.

## 4. Why GRH methods are genuinely relevant

As of 2026-11-23, a Lean proof of classical RH and GRH for Dirichlet L-functions has been announced and extensively checked by independent formal-verification tools; its human-readable exposition and broader expert digestion are still in progress. See §8 below. We should distinguish this formally verified proof claim from proposed strategies for wider families of L-functions, which remain outside the checked scope.

Three structural ideas are relevant:

### 4.1 Prime factorization as a semantic basis problem

The Euler product for the zeta function packages the arithmetic of all positive integers in terms of prime factors. The primes are generators of the multiplicative monoid of positive integers greater than zero, and unique factorization gives a canonical decomposition.

For our theory, this suggests looking for irreducible semantic generators under a precisely specified composition operation. But the analogy must be sharpened:
- *indecomposable/irreducible* means not decomposable into nontrivial factors;
- *prime* is stronger: if it divides a composite, it divides one of the factors;
- *unique factorization* requires additional structural hypotheses.

In a semantic category, the candidate analogue is not automatically a set of primitive concepts. It may be a class of tensor-indecomposable objects, irreducible relations, or generators of a factorization system. We must specify the monoidal/compositional operation, units, equivalence notion, and admissible decompositions. Contextual or higher-order interactions may make factorization non-unique.

### 4.2 Explicit formula: local arithmetic and global spectral structure

The Riemann–Weil explicit formula relates prime-power data (arithmetic side) to zeros of zeta/L-functions (spectral side). This is a particularly attractive analogue for our project: a semantic structure may admit both a generative/decomposition description and a dual spectral/constraint description. The relation between the two may be more fundamental than either representation alone.

This suggests a semantic duality programme:
- generators / irreducible distinctions on one side;
- global spectral or moduli invariants on the other;
- a trace/explicit-formula-like transformation linking them;
- an invariance theorem showing that both sides encode the same grounded structure.

This is a research analogy, not yet a theorem.

### 4.3 Weil positivity and finite local approximations

Weil's positivity criterion reformulates RH as positivity of a quadratic form on a suitable test-function space. For a fixed compact support, only finitely many prime powers contribute to the corresponding explicit-formula calculation; requiring positivity across the relevant supports recovers the global criterion.

This is close in architecture to our resource-indexed probe framework:
- finite prime set / bounded support ↔ finite admissible probe family;
- quadratic form ↔ global consistency/positivity functional;
- increasing support ↔ increasing resource budget;
- positivity at every scale ↔ a global structural condition.

The crucial lesson is not that finite checks prove the infinite theorem. It is that a global property can sometimes be characterized by a directed family of finite, locally computable constraints, provided the limiting/extension theorem is proved.

Connes' 2026 survey describes a promising programme connecting Weil positivity, time-frequency concentration, prolate spheroidal operators, and information theory. It explicitly says the convergence step needed to turn the numerical approximants into the actual zeta zeros remains unproved. This is a useful methodological precedent, not a proof of RH.

## 5. Candidate semantic-prime programme

Define a grounded symmetric monoidal (or otherwise compositional) category ((\mathcal C,\otimes,\mathbb 1)). Then distinguish:

- **Atomicity:** every non-unit object admits a finite decomposition into irreducibles.
- **Irreducibility:** an object cannot be expressed as a tensor product of two non-units.
- **Primality:** divisibility of a product forces divisibility of one factor.
- **Unique factorization:** decompositions agree up to permutation and equivalence of factors.
- **Operational atomicity:** no admissible lower-cost substructure preserves the same complete grounded response profile.
- **Semantic adequacy:** the factorization preserves reference, truth, inferential role, and higher coherence.

Operational atomicity is budget-relative and therefore not absolute: a structure can be irreducible at budget (B) but decomposable when richer probes or transformations become available. The theory should distinguish intrinsic atoms from resource-relative atoms.

A plausible goal is a canonical *semantic factorization system*, not a naïve universal bag of primitive symbols. Factorization systems may be more robust than prime elements when decomposition is non-unique or order-sensitive.

## 6. Open obligations

1. Prove finite-sample error bounds for repeated stochastic probes.
2. Formalize adaptive intervention policies and their resource accounting.
3. Establish a statistical data-processing theorem for a suitable divergence.
4. Define compositional semantic divisibility and distinguish irreducible from prime.
5. Determine conditions for atomic decomposition and uniqueness (or characterize the obstruction).
6. Connect decomposition invariants to the resource-indexed grounded moduli space.
7. Prove that the semantic/spectral duality is faithful and adequately grounded, rather than merely a change of representation.
8. Compare the proposed architecture with existing categorical factorization systems, trace formulae, Weil positivity, and causal homotopy literature before making novelty claims.


## 7. Additional statistical infrastructure already present in the project

A second repository inspection found substantial prior work in `proofs/lean/Theory.lean` that should be reused rather than duplicated:

- `PFT.Dist`: finite weighted distributions, event masses, pushforward and Markov-kernel bind.
- `PFT.tv_deterministic_dpi`: deterministic post-processing cannot increase event total-variation distinguishability.
- `PFT.markov_kernel_dpi` and `markov_kernel_dpi_comp`: stochastic channels and compositions have explicit TV contraction/scaling bounds.
- `PFT.union_bound_sum` and `err_le_sumBudget`: finite candidate-family error aggregation.
- The finite probability-tree / supermartingale development includes optional-stopping preservation and `PFT.ville_anytime_valid_bound`, an anytime-valid maximal inequality for adaptive peeking/stopping.

Thus the repository already has much of the statistical machinery conceptually required. The main missing bridge is to connect the stochastic intervention channels and their exact normalized `FinDist` equality to the `PFT.Dist` event-TV / Markov-kernel framework, then instantiate the existing bounds for concrete noisy semantic probes. The two distribution aliases are structurally the same list-of-weighted-outcomes representation but currently live in separate namespaces and use different interfaces. We should prove a representation bridge or consolidate them, not maintain parallel probability theories.

The finite-sample research target is therefore more precise than stated above: construct an i.i.d. or explicitly adaptive experiment from the existing stochastic intervention model; represent its hypotheses and decision rule; derive an event-TV or likelihood-ratio separation; and apply the existing Ville / union-bound results with correct normalization, and add a concentration theorem if the chosen experiment requires one. The present new module establishes exact complementary-channel identifiability only.


## 8. Critical update: the November 2026 Alpöge–Claude RH/Dirichlet-GRH proof

The initial version of this note described GRH as simply unproved. That is now incomplete. On 20 November 2026 Levent Alpöge announced a Lean formal proof, developed with Claude, of the classical Riemann Hypothesis and GRH for Dirichlet (L)-functions. The 22 November MIT verification page reports that all 175,187 modules compile; all five headline theorems use only Lean's standard `propext`, `Classical.choice`, and `Quot.sound`; every compiled module passes Lean-kernel replay; independent kernels nanoda and con-leche accept the export; con-leche and con-ron statement comparison accept all five theorems; and lean4lean accepts all modules. MIT's page still lists the full-export Lean default/paranoid kernel replay and end-to-end `lake comparator` as running at its 22 November update. Michael Rubinstein's Waterloo page separately reports the four principal checks (compile, axiom audit, module kernel replay, nanoda) all completed successfully on 21 November.

The careful status is therefore: **a major, extensively independently machine-checked formal proof claim exists, and the Lean/Mathlib community has certified the formal result; the human-readable mathematical explanation and broader expert digestion are still in progress.** This is much stronger than a numerical or heuristic claim. It is not accurate to say there is no proof attempt or that the conjecture is simply untouched. The checked GRH scope is Dirichlet (L)-functions; Dedekind zeta, Hecke, and general automorphic (L)-functions are not included in the five checked statements.

The current human-readable guide by Rubinstein (version 2, 22 November, 265-page working draft) is especially relevant to the prime-atom question. It explicitly warns that its main inequality (M), the arithmetic heart of the argument, is still quoted from the Lean development rather than fully proved in the exposition. The guide reduces (M) to thirteen classical hypotheses, none all proved outright in that document. This is a gap in human exposition, not evidence that the Lean proof lacks a proof term; it means the mathematical mechanism has not yet been fully distilled into a conventional argument.

### 8.1 The actual prime mechanism is richer than unique factorization

The proof's eight-step outline contains a structural pattern worth studying:

1. A zero off the critical line would force a large value of a smoothed prime-power statistic (G(x)), via a Mellin transform and explicit formula.
2. Chebyshev's principle bounds how many distinct primes can divide an object by comparing divisibility with its size.
3. The object is no longer a single integer: it is a high-rank lattice map.
4. Special derivatives and theta kernels acquire controlled prime-power divisibility, especially at inert primes.
5. A chain of theta lifts between unitary groups supplies a map whose norm, covolume, and rank can be estimated.
6. Lattice slope inequalities turn local divisibility data into a global size constraint; many maps and rank bounds control the average slope.
7. The chain length (m) balances endpoint loss (x/m) against accumulated per-step loss (m), yielding (m\asymp\sqrt{x}) and the critical exponent (1/2).
8. Auxiliary Dirichlet characters and residue-class averaging transfer the inert-prime estimate to all prime powers in the required weighted sum.

The prime role is therefore not merely “unique factorization into atoms.” Distinct primes provide independent local divisibility constraints, while a global height/covolume/slope invariant limits their cumulative strength. This is much closer to a local-to-global resource theorem.

### 8.2 A candidate semantic translation

For a compositional semantic category, investigate a family of irreducible semantic probes/atoms \(\pi\) and a valuation-like profile
\[
  v_\pi(X)\in\mathbb N\cup\{\infty\},
\]
where (v_\pi(X)) measures the multiplicity with which the semantic structure (X) contains or is divisible by the atom (pi). If the composition is monoidal, the desired law is
\[
  v_\pi(X\otimes Y)=v_\pi(X)+v_\pi(Y).
\]
A global semantic height (H(X)) would then constrain a finite family of local valuations, schematically
\[
  \sum_{\pi\in P} w(\pi)\,v_\pi(X)\le H(X)+\mathrm{loss}(P),
\]
for finite (P). This is only a proposed architecture; the category, divisibility relation, valuations, and height must be defined and the inequality proved. In a non-UFD category, valuations may not be canonical, so they may need to be defined by prime ideals, subobject lattices, or a factorization system rather than by chosen decompositions.

The promising bridge to our work is:
- semantic atoms/local valuations ↔ prime-power divisibility constraints;
- grounded probes ↔ tests detecting local factors;
- resource-indexed finite probe families ↔ finite sets of primes/scales;
- global semantic complexity/height ↔ lattice covolume or slope;
- a local-to-global inequality ↔ a theorem bounding the total semantic content visible across all atoms;
- directed passage to all probes ↔ the global limit needed for full semantic adequacy.

This is a substantive research analogy, not a theorem already established in our repository. The most useful next formal target is a general abstract local-to-global divisibility/height theorem in a monoidal category or an ordered divisibility structure, with a finite arithmetic model first. It should explicitly distinguish atomicity, primality, unique factorization, and resource-relative irreducibility.


## 9. Existing semantic irreducibility result: atoms need not be unary

A further repository inspection found `IrreducibleTriadicRelations.lean` and its research dossier. It proves that a finite ternary even-parity relation on three Boolean roles cannot be expressed as the conjunction of three pairwise binary relations: every assignment to any two coordinates extends to a valid triple, which forces every proposed binary factor to be universal, while the ternary relation still excludes some triples.

This matters for the prime analogy. A naïve theory that searches only for primitive *concepts* or independent unary features is too weak. The irreducible semantic units may be relations/hyperedges involving several roles, or higher coherent structures. We must distinguish:
- irreducibility against pairwise relational factorization (already witnessed in Lean);
- indecomposability under a chosen monoidal composition;
- primality under a divisibility relation;
- uniqueness of global factorization.

These are not equivalent. The parity witness establishes only the first. A semantic prime theory should permit relational atoms of arity (k\ge 2), and potentially higher-categorical coherence data, rather than force every atom into a node-like primitive. This also fits the local-to-global lesson from the RH proof: the relevant local divisibility data may live in structured maps/lattices, not in isolated scalar symbols.
