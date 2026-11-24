# Non-Abelian causal realization: gauge quotient, predictive state, and resource threshold

**Date:** 2026-11-22  
**Status:** exact finite result for one (S_3) model; not a universal theorem.

This note integrates Spike 26 into the Causal-Realization research line. The full derivation, matrices, and verification record are in `experiments/SPIKE_26_REPORT.md`; the executable source and exact JSON artifact are linked there.

## 1. Ontic gauge configurations are not semantic states

For a three-edge directed cycle and finite gauge group (G), let
[
A=(A_0,A_1,A_2)\in G^3,
\qquad
A_i\mapsto g_{i+1}A_ig_i^{-1}.
]
With (H(A)=A_2A_1A_0), one obtains
[
H(A^g)=g_0H(A)g_0^{-1}.
]
Thus the loop product is a base-frame-covariant quantity; its conjugacy class is gauge invariant. In the (S_3) instance, exhaustive orbit enumeration shows that the gauge quotient of connection configurations has exactly three elements, represented by the identity, transposition, and 3-cycle classes.

This illustrates a general distinction needed in the theory:
- a coordinate representation may retain gauge/frame distinctions;
- a physical invariant quotient removes distinctions that no gauge-invariant probe can protect;
- a further task-relative predictive quotient can collapse even some gauge-invariant sectors if the available future tests cannot distinguish them.

The first quotient is an ontological/gauge constraint. The second is an epistemic/resource constraint. They should not be identified.

## 2. Dynamic realization and the predictive quotient

Let (X) be the three conjugacy classes. For each action (a), let (P_a) be a transition kernel on (X), and let (O_a(y\mid x)) be the observation channel emitted after the transition. Define
[
M_{a,y}(x,x')=P_a(x,x')O_a(y\mid x').
]
For a history (h), the Bayesian posterior (mu_h\in\Delta(X)) is the normalized forward state. For a future test (	au), let (f_\tau(x)) be its likelihood from hidden state (x). Then
[
\Phi_B(h)(\tau)=P(\tau\mid h)=\mu_h f_\tau.
]
The history-future Hankel operator factors:
[
H_B=R_BO_B.
]
The minimal resource-relative predictive equivalence is
[
h\sim_B h'
\iff
\mu_hO_B=\mu_{h'}O_B.
]
The posterior is always sufficient, but it is fully abstract only when (O_B) separates the relevant beliefs. In this finite simplex model, the empty test is included, so full abstraction on all beliefs is equivalent to (operatorname{rank}(O_B)=|X|=3).

This is the precise bridge between the Causal-Realization content clause and the internal-state realization clause: the content is the future-response row; the posterior is one causal realization of that row; and the test family determines whether the realization has redundant distinctions.

## 3. Exact threshold result

The (S_3) fixture uses an action `wait` of cost 1 with uniform emissions and an action `probe` of cost 3 with transition determinant (1/4). Its three-outcome channel satisfies
[
\det K_\eta=(1-3\eta)^2.
]
Consequently:
- for (B<3), all future tests use only uniform-emission waits and the predictive quotient is a singleton;
- for (B\ge3), the one-step probe map (b\mapsto bP_{probe}K_\eta) is injective iff (\eta\ne1/3);
- at (\eta=1/3), all emissions are uniform and no finite future test separates beliefs at any budget.

The most instructive exact counterexample is (B=2): the history-posterior matrix has rank 2, while the future-test matrix and Hankel matrix both have rank 1. The agent has learned/updated an internal belief, but the declared physical test interface cannot read the distinction out. The semantic quotient is therefore strictly coarser than the posterior representation.

## 4. Hankel Gramians and the Master Operator

For finite history and test weights (D_H,D_T), define
[
W_c=R^TD_HR,\qquad W_o=OD_TO^T.
]
The nonzero squared singular values of the weighted Hankel matrix are the nonzero eigenvalues of
[
W_c^{1/2}W_oW_c^{1/2}.
]
This is the standard balanced-realization identity for a factorized finite Hankel operator. Spike 26 verifies exact (H=RO), exact Gram matrices, and the predicted ranks in all three resource/noise regimes.

It does **not** prove that the Semplex Master Operator's current (W_c+W_o) is the balanced Hankel Gram, nor that its kinetic penalty is the physically correct resource cost. The two objects must be derived from the same operationally defined past/future maps before such an identification is licensed.

## 5. Limits and open theorem

The result is a finite (S_3) construction with rational kernels. It does not establish a theorem for arbitrary finite or compact groups, general gauge theories, stochastic/quantum higher categories, neural systems, or physical hardware. The next theorem target is to characterize, for arbitrary finite (G), which families of representation characters separate the conjugacy classes relevant to the protected readout, and how the rank of the resource-bounded future-test operator controls the predictive quotient.

The central research lesson is not “meaning is holonomy.” It is narrower and more general: physical symmetries determine which distinctions are gauge artifacts; admissible future tests determine which remaining distinctions are semantically real for the declared task; and a causal realization is fully abstract exactly when its internal kernel coincides with that response equivalence.


## 6. Beyond S3

The companion generic finite-group module now checks the gauge-ring orbit law for both (S_3) and (D_4). For (D_4), the five conjugacy classes have sizes (1,1,2,2,2), and the 512 connection configurations split into five gauge orbits of sizes (64,64,128,128,128). A generic class Markov kernel lifts to a group-level kernel by (Q(g,g')=P([g],[g'])/|[g']|); the D4 lift was checked to be row-stochastic and conjugation-equivariant.

For (n) conjugacy sectors, the symmetric channel is (K_n(\eta)=\eta\mathbf1\mathbf1^T+(1-n\eta)I), with determinant ((1-n\eta)^{n-1}). Thus an invertible class transition followed by this channel separates the full belief simplex exactly when (\eta\ne1/n). This is an algebraic generalization; exhaustive machine checks cover S3 and D4, not every finite group, and no arbitrary-group Lean proof has yet been added.
