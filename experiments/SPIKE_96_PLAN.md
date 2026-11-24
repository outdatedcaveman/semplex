> Renumbered from canonical distinction-calculus `SPIKE_26_PLAN` to `SPIKE_96_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Experiment plan — non-Abelian causal realization

**Date:** 2026-11-22  
**Status:** implemented; exact finite benchmark  
**Code:** `experiments/nonabelian_causal_realization.py`  
**Tests:** `tests/test_nonabelian_causal_realization.py`  
**Artifact:** `artifacts/nonabelian-causal-realization-20261122.json`

## Questions

1. Does a finite non-Abelian gauge system reduce exactly to conjugacy classes of its Wilson-loop holonomy?
2. Can a gauge-covariant, action-conditioned hidden Markov process be built on those classes?
3. Does the history-to-future response operator factor through Bayesian beliefs, and when is that belief representation fully abstract?
4. How do intervention cost and observation noise change the minimal predictive quotient?
5. What information is lost by local, unordered, or frame-dependent representations?

## Preregistered finite model

- Gauge group: (S_3), acting at the three vertices of a directed 3-cycle.
- Edge connection: (A=(A_0,A_1,A_2)in S_3^3).
- Gauge action: (A_imapsto g_{i+1}A_i g_i^{-1}).
- Holonomy: (H(A)=A_2A_1A_0), with the stated permutation-composition convention.
- Gauge-invariant sector: conjugacy class ([H(A)]), giving identity, transposition, and 3-cycle sectors.
- Hidden dynamics: two exact rational transition kernels on the three conjugacy classes. Both are invertible and they do not commute.
- The class-level kernels are lifted uniformly to (S_3); the lift must be row-stochastic and conjugation-equivariant.
- Actions: `wait` costs 1 and has a uniform observation; `probe` costs 3 and has a symmetric three-outcome observation channel (K_\eta).
- The hidden state transitions before the observation is emitted.

## Definitions

For action (a) and outcome (y), define the substochastic matrix
[
M_{a,y}(i,j)=P_a(i,j)O_a(ymid j).
]
For history (h=(a_1,y_1,ldots,a_n,y_n)), the unnormalized forward row is
[
\alpha_h=\pi M_{a_1,y_1}\cdots M_{a_n,y_n},
\qquad
\mu_h=\frac{\alpha_h}{\alpha_h\mathbf 1}.
]
For a future test (\tau=(a'_1,y'_1,ldots,a'_m,y'_m)), its likelihood vector is
[
f_\tau=M_{a'_1,y'_1}\cdots M_{a'_m,y'_m}\mathbf 1.
]
The finite history-future Hankel matrix is
[
H_{h,\tau}=P(\tau\mid h)=\mu_h f_\tau= (RO)_{h,\tau}.
]

At budget (B), histories and future tests are restricted to action words whose total cost is at most (B). The predictive quotient identifies histories with equal rows of (H). On the full belief simplex, posterior full abstraction holds exactly when the future-test matrix (O) has rank 3.

## Predicted exact thresholds

- (B<3): only wait actions are affordable; all affordable emissions are uniform. The future-response rank and quotient size are 1, even though reachable posterior beliefs can differ.
- (B\ge3): a single probe is affordable. Since (det P_{probe}=1/4) and (det K_\eta=(1-3\eta)^2), the probe separates every belief iff (\eta\ne1/3).
- (\eta=1/3): every emission is uniform; all histories remain predictively equivalent at every budget.

## Verification requirements

- Exhaustively enumerate all (S_3^3) connections and vertex gauge transformations.
- Verify holonomy transforms by conjugation and gauge orbits are classified by conjugacy class.
- Verify the group-level Markov lifts are stochastic and conjugation-equivariant.
- Compute (R,O,H) with exact rational arithmetic and check (H=RO).
- Compute exact ranks and weighted Gramians.
- Include a counterexample showing an unordered local edge-class multiset can miss ordered holonomy.
- Keep gauge-invariant, gauge-covariant, and gauge-fixed baselines explicitly distinct.

## Scope limits

This is an exact finite mathematical model. It is not a hardware experiment, a new gauge-theory result, a learned-model benchmark, or evidence that the Master Operator is already derived from the Hankel operator. Those require separate work.
