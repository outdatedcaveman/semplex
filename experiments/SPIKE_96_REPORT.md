> Renumbered from canonical distinction-calculus `SPIKE_26_REPORT` to `SPIKE_96_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 26 — Non-Abelian causal realization with controlled hidden dynamics

**Date:** 2026-11-22  
**Status:** exact finite model implemented; focused regression currently 13 tests  
**Plan:** `experiments/SPIKE_26_PLAN.md`  
**Code:** `experiments/nonabelian_causal_realization.py`  
**Tests:** `tests/test_nonabelian_causal_realization.py`  
**Artifact:** `artifacts/nonabelian-causal-realization-20261122.json`

## 1. Executive result

The (S_3) three-edge gauge ring gives an exact non-Abelian test of the Causal-Realization Principle. The gauge-invariant static sector is the conjugacy class of the ordered Wilson-loop product. A conjugation-equivariant controlled Markov process on those sectors then supplies a finite partially observed dynamical system.

The complete finite history-to-future response matrix factors exactly as
[
H_B=R_B O_B,
]
where (R_B) maps histories to posterior beliefs and (O_B) maps hidden sectors to future-test likelihoods. Its minimal predictive quotient is determined by (O_B), not by the posterior map alone.

The decisive distinction is now explicit:

- At budget (B=2), posterior histories span a two-dimensional linear space under the chosen uniform initial prior, but all affordable future responses are identical: (rank R=2), (rank O=rank H=1). This rank-R increase is caused by known wait-transition drift of a nonstationary prior, not by informative observation updates.
- At budget (B=3), an informative Wilson-loop probe becomes affordable. At (eta=1/6), all three ranks become 3 and posterior beliefs are fully abstract.
- At (eta=1/3), the observation channel is uniform. Even with the probe affordable, (operatorname{rank}O=operatorname{rank}H=1); no finite future experiment distinguishes the hidden sector.

This is a concrete example where an agent's internal state contains more distinctions than its current physical test interface can semantically justify.

## 2. Non-Abelian gauge calculation

Use (G=S_3) and a directed cycle with vertices (0,1,2). An edge connection is
[
A=(A_0,A_1,A_2)in G^3.
]
For vertex gauge elements (g=(g_0,g_1,g_2)), the oriented edge action is
[
A_ilongmapsto A_i'=g_{i+1}A_i g_i^{-1},
]
with indices modulo 3. With permutation composition interpreted as “rightmost first”, define
[
H(A)=A_2A_1A_0.
]
The intermediate gauge elements cancel:
[
H(A')=g_0H(A)g_0^{-1}.
]
Thus the group element is base-frame covariant, while its conjugacy class ([H(A)]) is gauge invariant.

The three conjugacy classes of (S_3) are:
- identity: size 1;
- transpositions: size 3;
- 3-cycles: size 2.

Exhaustive enumeration gives 216 connection configurations and 216 vertex-gauge transformations, with exactly three gauge orbits. Their sizes are:
[
36,quad108,quad72.
]
More generally, the orbit associated with (H) has size
[
rac{|G|^3}{|C_G(H)|}=|G|^2,|[H]|,
]
so the three observed sizes agree exactly with the centralizer-stabilizer formula.

## 3. Local, compositional, and gauge-invariant representations

The benchmark distinguishes four objects that must not be conflated.

1. **Strictly local gauge-invariant scalar.** A single open edge transforms by independent left and right endpoint gauges. The (G\times G) action is transitive on its label, so any scalar invariant of one open edge is constant. No such probe can distinguish the three sectors.
2. **Naive unordered edge-class multiset.** This is a gauge-fixed statistic, not a gauge invariant: an individual edge's conjugacy class is not preserved by independent endpoint gauges. It also loses composition order. The exact search found 10 such signatures, four of which occur with more than one holonomy class. One witness is
   [
   (e,s_{12},s_{12})quad\text{versus}\quad(e,s_{12},s_{01}),
   ]
   whose local conjugacy-class multisets agree but whose loop holonomies lie in the identity and 3-cycle classes, respectively.
3. **Ordered path product.** The full (H\in S_3) retains the order-sensitive composition, but carries six possible base-frame values and transforms by conjugation.
4. **Conjugacy-class quotient.** Passing from (H\in S_3) to ([H]) removes the base-frame redundancy. There are three gauge-invariant sectors, exactly the orbits of the connection space.

The group-valued representation therefore has a factor-of-two frame redundancy relative to the conjugacy-class quotient. The dynamic predictive state is a belief (b\in\Delta^2), with two affine degrees of freedom.

## 4. Controlled hidden dynamics

Let the hidden state (x_t\in\{e,\tau,c}) denote the identity, transposition, or 3-cycle conjugacy class. There are two actions:

[
P_{wait}=
\begin{pmatrix}
3/4&1/4&0\\
1/8&3/4&1/8\\
0&1/4&3/4
\end{pmatrix},
\qquad
P_{probe}=
\begin{pmatrix}
1/2&1/2&0\\
0&1/2&1/2\\
1/4&0&3/4
\end{pmatrix}.
]

Both are row-stochastic and invertible:
[
\det P_{wait}=3/8,\qquad \det P_{probe}=1/4.
]
They do not commute. The induced class dynamics have also been lifted to Markov kernels on (S_3) by distributing each target-class probability uniformly over that conjugacy class. The exact lift is row-stochastic and conjugation-equivariant, so the dynamics respect the gauge quotient.

The action costs are
[
c(wait)=1,\qquad c(probe)=3.
]
After the transition, `wait` emits a uniform observation in ({0,1,2}). The `probe` action emits through
[
K_\eta(y\mid x)=
\begin{cases}
1-2\eta,&y=x,\\
\eta,&y\ne x.
\end{cases}
]
Its determinant is
[
\det K_\eta=(1-3\eta)^2.
]
At (eta=1/6), this determinant is (1/4); at (eta=1/3), the channel is exactly uniform and singular.

The transition-before-emission convention is part of the model definition. The matrices are exact rational choices for a controlled finite benchmark, not estimates of a physical process.

## 5. History-to-future Hankel operator

For action (a) and observed outcome (y), define the substochastic matrix
[
M_{a,y}(i,j)=P_a(i,j)O_a(y\mid j).
]
For a history
[
h=(a_1,y_1,\ldots,a_n,y_n),
]
let
[
\alpha_h=\pi M_{a_1,y_1}\cdots M_{a_n,y_n},
\qquad
\mu_h=\frac{\alpha_h}{\alpha_h\mathbf1}.
]
For a future test
[
\tau=(a'_1,y'_1,\ldots,a'_m,y'_m),
]
let its likelihood vector be
[
f_\tau=M_{a'_1,y'_1}\cdots M_{a'_m,y'_m}\mathbf1.
]
The conditional future response is
[
H_{h,\tau}=P(\tau\mid h)=\mu_h f_\tau.
]
Collecting posterior rows into (R_B) and future likelihood columns into (O_B) yields the exact factorization
[
\boxed{H_B=R_BO_B.}
]

The finite resource family includes all action words with total action cost at most (B), both for histories and future tests. The experiment enumerates every observation string for each such word. The initial prior is uniform over the three conjugacy classes.

The predictive equivalence relation is
[
h\sim_B h'
\iff
\forall\tau\in\mathcal T_B, H_{h,\tau}=H_{h',\tau}.
]
On beliefs, this is
[
b\sim_B b'
\iff
(b-b')O_B=0.
]
Since the empty test contributes the constant vector, full abstraction on the whole simplex is equivalent here to (operatorname{rank}O_B=3). Posterior equality is sufficient at every budget; it is necessary only when the affordable future tests separate all beliefs.

## 6. Exact resource/noise full-abstraction theorem

**Proposition.** For the declared (S_3) controlled HMM:

1. If (B<3), all affordable action words contain only `wait`. Every wait emission is uniform, so every future-test likelihood vector is constant across hidden states. Therefore (operatorname{rank}O_B=1), all beliefs are response-equivalent, and the predictive quotient is a singleton.
2. If (B\ge3), the one-step `probe` test is affordable. Its outcome distribution from belief (b) is
   [
   bP_{probe}K_\eta.
   ]
   Because (P_{probe}) is invertible and
   [
   \det(P_{probe}K_\eta)=\frac14(1-3\eta)^2,
   ]
   the probe separates every pair of beliefs exactly when (eta\ne1/3). In this regime the posterior representation is fully abstract for the declared test family.
3. If (eta=1/3), all emissions are uniform for both actions. Every finite action-observation response is independent of the initial belief at every budget, so the predictive quotient remains a singleton.

**Proof.** The first and third cases follow because each affordable outcome likelihood vector is proportional to \(\mathbf1\). In the second case, the single-probe response is an invertible linear map on the belief simplex precisely when its determinant is nonzero. Equal posterior beliefs always give equal future responses by the Markov property and Bayesian filtering. The single-probe test supplies the converse when the matrix is invertible. \(\square\)

## 7. Exact ranks and weighted Gramians

The exact finite enumeration produces:

| Budget / channel | Histories | Tests | rank (R) | rank (O) | rank (H) | Full abstraction? |
|---|---:|---:|---:|---:|---:|---|
| (B=2,\eta=1/6) | 13 | 13 | 2 | 1 | 1 | No |
| (B=3,\eta=1/6) | 43 | 43 | 3 | 3 | 3 | Yes |
| (B=3,\eta=1/3) | 43 | 43 | 3 | 1 | 1 | No |

For uniform finite history/test weights, set
[
D_H=|H_B|^{-1}I,\qquad D_T=|T_B|^{-1}I,
]
and define
[
W_c=R_B^TD_HR_B,\qquad W_o=O_BD_TO_B^T.
]
The exact ranks are:
- (B=2,\eta=1/6): ((\operatorname{rank}W_c,\operatorname{rank}W_o,\operatorname{rank}(W_cW_o))=(2,1,1));
- (B=3,\eta=1/6): ((3,3,3));
- (B=3,\eta=1/3): ((3,1,1)).

The general balanced-spectrum identity follows directly from the factorization. Write
[
\widetilde H=D_H^{1/2}H D_T^{1/2}=R_wO_w.
]
Then (W_c=R_w^TR_w) and (W_o=O_wO_w^T). The nonzero squared singular values of (\widetilde H) are the nonzero eigenvalues of
[
W_c^{1/2}W_oW_c^{1/2},
]
equivalently the nonzero eigenvalues of (W_cW_o). The executable model verifies the exact factorizations, Gram matrices, and ranks; it does not numerically diagonalize the full weighted Hankel spectrum. The spectral equality above is the general linear-algebra theorem, not a new discovery.

The key diagnostic is the difference between action-conditioned past state and future distinguishability. At (B=2), (W_c) has rank 2 under the uniform initial prior, but (W_o) has rank 1. This does not show that observations taught the agent: every affordable wait observation is uniform. The rank increase comes from applying the known transition P_wait to a nonstationary prior. The stationary distribution (1/4,1/2,1/4) is fixed by P_wait and reduces rank(R) and rank(W_c) to 1 at B=2.

## 8. What this contributes to the master principle

This benchmark supplies a non-Abelian, dynamically controlled, exactly rational instance of the two-clause Causal-Realization Principle:

- **Content:** the resource-indexed future-response profile; semantic identity is equality of all protected future responses.
- **Realization:** the Bayesian belief is a causally sufficient internal state; it is fully abstract exactly when the affordable future tests separate the belief simplex.
- **Higher/gauge structure:** the physical connection is not itself the semantic state. Gauge-equivalent configurations collapse to conjugacy classes, while ordered path composition is needed to expose the global invariant.
- **Resource dependence:** semantic distinctions appear only when a noncontractible probe is affordable and its observation channel is informative.

It strengthens the derivation of a concrete past/future Hankel factorization and shows exactly why a posterior Gramian can contain modes absent from the future-response quotient.

It does **not** yet derive the Master Operator (G_\lambda=e^{-\lambda L_{kin}/2}(W_c+W_o)e^{-\lambda L_{kin}/2}) from the Hankel operator, nor establish that the action cost is a calibrated physical energy or thermodynamic quantity. The connection between the exact response object and the proposed resource-penalized realization selector remains open.

## 9. Verification and limitations

- Original Spike26-specific regression: 13 tests; post-audit combined Spike26/27 finite regression: 31 tests passed.
- Exact arithmetic: Python `Fraction`; no floating-point probability calculations.
- Gauge orbit and group-lift checks are exhaustive over the finite (S_3) model.
- The JSON artifact contains the finite (R,O,H,W_c,W_o,W_cW_o) matrices.
- No full repository suite or Agda build was run. The focused core-Lean HoTTGaugeBridge module has since compiled and `lake build HoTTGaugeBridge` passed; this is not a formalization of the full groupoid equivalence or the Mathlib variational development.
- No hardware experiment, neural training, or matched-capacity learned-model comparison was run.
- An independent adversarial audit arrived through the Antigravity/Gemini coordination channel (event 151805). The direct Gemini task 141 remains pending; the audit is attributed to Antigravity/Gemini, not represented as a completed direct Gemini review.
- The model is a finite mathematical benchmark, not new gauge theory or a new physical law.

## 10. Next discriminating work

1. Generalize the theorem from three conjugacy classes to arbitrary finite (G), with class-covariant controlled kernels and arbitrary finite observation channels.
2. Replace the fixed three-outcome channel with irreducible-character readouts and determine when characters separate conjugacy classes (and when a selected character family fails).
3. Compare gauge-invariant local probes, ordered path products, conjugacy-class quotients, and posterior-state models at matched test/action/compute budgets on held-out graph sizes.
4. Derive or refute a theorem connecting the exact (W_c,W_o) obtained from the Hankel factorization to the Master Operator's proposed (W_c+W_o) and kinetic penalty. Do not assume the sum is a balanced-realization Gramian.
5. Formalize the finite theorem in Lean only after memory is available and the mathematical interface is stable.


### Cardinality clarification

The ratio 6 group elements to 3 conjugacy classes is a 2:1 reduction in total state-count only. The quotient fibers are not uniform: their sizes are 1, 3, and 2. The phrase “frame redundancy factor” in the JSON artifact denotes this aggregate cardinality ratio, not a constant two-to-one fiber size.


## 11. Generalization beyond S3: arbitrary finite groups and D4

The implementation now has a generic finite-group interface in `experiments/finite_group_gauge_orbits.py`. It accepts a finite group multiplication/inverse table and checks the gauge-ring orbit formula without assuming commutativity.

A second exhaustive instance uses (D_4), the order-8 dihedral group of the square:
- 512 connection configurations and 512 vertex-gauge transformations;
- five conjugacy classes of sizes (1,1,2,2,2);
- five gauge orbits of sizes (64,64,128,128,128);
- each orbit size agrees with (|G|^2|[H]|).

The generic class-kernel lift is
[
Q(g,g')=\frac{P([g],[g'])}{|[g']|}.
]
For any row-stochastic class transition matrix (P), this lift is row-stochastic and conjugation-equivariant. A nontrivial 5-state cyclic transition on the (D_4) classes was lifted and both properties were checked exactly.

The symmetric observation channel also generalizes to (n) conjugacy sectors:
[
K_n(\eta)=\eta\mathbf1\mathbf1^T+(1-n\eta)I,
\qquad
\det K_n(\eta)=(1-n\eta)^{n-1}.
]
Thus, for any invertible class transition (P), the one-step predictive map (b\mapsto bPK_n(\eta)) separates the full (n)-simplex iff (\eta\ne1/n). Exact checks include:
- (n=3,\eta=1/6): determinant (1/4);
- (n=5,\eta=1/10): determinant (1/16);
- (n=5,\eta=1/5): determinant (0), the uniform channel.

This extends the finite group-orbit and observation-rank calculations beyond the original (S_3) example. It is still not a Lean proof of the arbitrary-group theorem; the code exhaustively checks the (S_3) and (D_4) instances, while the displayed formulas are supported by the general algebraic arguments.


### Verification count update

The original S3-specific suite has 13 tests; the generic S3/D4 finite-group suite adds 6. The combined Spike 26 focused regression therefore contains 19 tests. The broader cross-spike integration run is recorded separately after the final validation pass.


### Final validation update (2026-11-22)

The S3-specific tests (13) plus generic finite-group tests (7) give **20 focused tests**. The combined cross-spike integration suite covering Spike 25, belief-state Hankel factorization, partial-observation Hankel, resource-relative probes, restricted Yoneda, semantic grounding, and both new modules passed **61 tests in 13.98 seconds**. Both experiment scripts regenerated their JSON artifacts successfully; `py_compile` and `git diff --check` passed. Free physical RAM after the run was approximately 1.27 GB. No Lean/Agda build or full repository suite was run.


## 12. Independent adversarial audit and corrections (2026-11-22)

An independent audit was delivered through the Antigravity/Gemini coordination channel (orchestrator event 151805). The following corrections are incorporated; the audit is not being treated as a completed direct Gemini review because task 141 remains pending.

### 12.1 The class-level Markov lift is not unique

The lift
[
Q(g,g')=P([g],[g'])/|[g']|
]
is stochastic and conjugation-equivariant, but it is only one possible lift. It uniformly redistributes mass within each target conjugacy class and erases exact within-class state in one step. The identity kernel is also conjugation-equivariant and lumpable over conjugacy classes, while preserving the exact group element. Thus the lift is a maximal-symmetry/reset choice, not a canonical consequence of the quotient. Future models must state whether intra-class memory is physically meaningful and which lift is justified.

### 12.2 Correct probability range for the symmetric channel

For
[
K_n(\eta)=\eta\mathbf1\mathbf1^T+(1-n\eta)I,
]
the diagonal is (1-(n-1)\eta) and the off-diagonal entries are (\eta). The stochastic domain is
[
0\le\eta\le\frac1{n-1},
]
not (0\le\eta\le1/n). The determinant remains
[
\det K_n(\eta)=(1-n\eta)^{n-1}.
]
At (\eta=1/n), the channel is uniform and singular. At the valid endpoint (\eta=1/(n-1)), the diagonal is zero, but the channel is still invertible for (n\ge2). For (n=5,\eta=1/4), the determinant is (1/256): an anti-identity-style channel still separates all beliefs. Code and tests now cover this full stochastic range.

### 12.3 One-step invertibility versus multi-step observability

The determinant condition on (P_{probe}K_\eta) characterizes separation by the **single probe**. It is sufficient for full abstraction once that probe is affordable. It is not a necessary condition for separation by an entire multi-step test family: a singular one-step transition can still be observable through a sequence of different controlled transitions. The general theorem must be stated in terms of the rank/observability of the complete future-test operator (O_B), not the determinant of one transition.

### 12.4 Posterior rank and prior drift

The (B=2) rank-(R=2) result under the uniform initial prior is caused by known open-loop evolution under (P_{wait}), not by informative observations: all wait emissions are uniform. The stationary distribution
[
\pi_*=(1/4,1/2,1/4)
]
satisfies (\pi_*P_{wait}=\pi_*), and using it reduces (rank(R)) to 1 at (B=2). The artifact and regression suite now include this prior-sensitivity control. The original rank result remains correct for its declared uniform prior, but it must not be described as evidence acquisition.

### 12.5 The centered Gram sum is not the centered Hankel operator

For the three Spike 26 regimes, exact centering gives
[
rank(H_c)=(0,2,0),
\qquad
rank((W_c)_c+(W_o)_c)=(1,2,2)
]
for ((B,\eta)=(2,1/6),(3,1/6),(3,1/3)), respectively. Thus the centered sum retains a spurious mode below the probe threshold and under total observation erasure. This is a direct counterexample to identifying the sum with the predictive/balanced Hankel object. The executable diagnostic and tests now calculate these ranks exactly.

The audit also proposed a variational alternative,
[
J_\lambda(X)=\mathrm{Tr}((A+\lambda L_{kin})X)+\mathrm{Tr}(BX^{-1}),
\]
with candidate minimizer (X_*(\lambda)=(A+\lambda L_{kin})^{-1}\#B), where (#) is the operator geometric mean. This is not yet adopted as the Semplex Master Principle. It is a promising candidate requiring a careful domain/positivity/uniqueness proof, derivation from the operational Hankel features, and a comparison against the existing heat-sandwich selector. Antigravity reports that it is formalizing this in an isolated worktree; do not duplicate its 100-run empirical campaign or copy unreviewed files into the canonical tree.

### 12.6 Multi-loop graphs require simultaneous conjugation

For a bouquet with two loops, componentwise conjugacy classes are not sufficient. In (S_3), the pairs ((s_{01},s_{01})) and ((s_{01},s_{12})) have the same individual transposition classes, but are not simultaneously conjugate: one has equal components and the other does not. Their ordered products also differ (identity versus a 3-cycle). For (b_1) loops the correct set-level data is not (mathrm{Cl}(G)^{b_1}), but
[
\mathrm{Hom}(F_{b_1},G)/G,
]
and the correct groupoid-level object is
[
\mathrm{Hom}(F_{b_1},G)//G
]
under simultaneous conjugation. The connected-graph statement in the research note is updated accordingly.
