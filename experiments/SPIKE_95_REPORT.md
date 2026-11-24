> Renumbered from canonical distinction-calculus `SPIKE_25_REPORT` to `SPIKE_95_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 25 — The Wilson loop is the first affordable semantic discriminator

**Status:** PASS — 13/13 focused tests; exact rational model.  
**Date:** 2026-11-22  
**Plan:** experiments/SPIKE_25_PLAN.md  
**Code:** experiments/finite_holonomy_pomdp.py  
**Tests:** tests/test_finite_holonomy_pomdp.py  
**Full model note:** research/FINITE_HOLONOMY_POMDP_REALIZATION.md  
**Artifact:** artifacts/finite-holonomy-pomdp-20261122.json

## Result

A three-vertex Z3 gauge ring yields a compact controlled partially observed system whose semantic distinctions appear at an exact resource threshold.

The 27 connection configurations split into exactly three gauge orbits, each of size 9. The additive Wilson-loop holonomy
\[
\theta=a_0+a_1+a_2\pmod 3
\]
is invariant under all 27 vertex gauge transformations and classifies those orbits.

The controller moves clockwise or counterclockwise one edge at a time. Open paths have no gauge-invariant scalar readout. Closed backtracking paths of length two have zero winding and reveal nothing. The first noncontractible paths, +++ and ---, cost three edge operations and reveal theta or -theta, respectively.

The hidden state is theta in Z3; the agent's state is its posterior belief b in the two-simplex. A clockwise loop is observed through
\[
K_\eta(y\mid\theta)=
\begin{cases}
1-2\eta,&y=\theta,\\
\eta,&y\ne\theta.
\end{cases}
\]
The channel matrix has exact determinant
\[
\det K_\eta=(1-3\eta)^2.
\]

## Theorem-level result for this model

1. For every resource budget B<3, all affordable closed paths have winding zero. All posterior beliefs induce the same response profile; the resource-relative semantic quotient is a singleton.
2. For B>=3, the clockwise-loop response map is b -> b K_eta. It is injective exactly when eta != 1/3. Thus the posterior representation is fully abstract for the declared response family exactly in that regime.
3. At eta=1/3, the observation channel is uniform. Every finite loop-outcome sequence has a prior-independent distribution, so no amount of repeated probing recovers the hidden sector.
4. Bayesian updating gives the sufficient predictive state for all future loop observations.

This is a direct physical-model instantiation of the response-quotient and predictive-state bridge. It makes the resource threshold and the information-loss threshold explicit.

## Exact machine checks

The executable report confirms 27 connection configurations, 27 gauge transformations, 3 gauge orbits of size 9, gauge invariance and exact orbit classification, gauge-invariant phase for all closed control paths through length six, no nontrivial winding before cost 3, one-loop full abstraction for non-uniform noise, total information erasure at uniform noise, exact Bayesian posterior and predictive sufficiency, and dependence between repeated observations caused by the shared static hidden sector.

Focused tests: **13 passed**.

## Connection to earlier spikes

- Spike 23: posterior beliefs factor the history-future response matrix. This model supplies a gauge-theoretic hidden state and explicit control costs.
- Spike 24: a three-state partial-observation system has a two-dimensional centered predictive realization. This model adds a topological/global invariant whose observability has a sharp intervention threshold.
- CausalRealization.lean: the model gives a concrete candidate instantiation of its abstract History, Test, cost, and response fields. The current Lean bridge has not yet been instantiated with this model or compiled against a new adapter.

## What is established and what is not

Established for this finite model: exact gauge-orbit classification, closed-path invariance, resource threshold, channel-rank threshold, and posterior predictive sufficiency.

Not established: new gauge theory, a general physical probe-density theorem, superiority of higher-category models, a new law of nature, or a universal semantic currency. These remain separate research obligations.

## Next experiment

Compare four predictors on held-out gauge-ring tasks: local-statistics-only; flat embedding of observed edge snippets; path-compositional model preserving ordered action composition; explicit gauge-invariant holonomy/belief-state model.

Vary ring length, group size, noise, hidden-sector prior, and intervention budget. Match parameter count and observation/compute budgets. Measure held-out response error, calibration, sample efficiency, memory, and compute. The key falsifier is that path composition offers no advantage once baselines receive equivalent global information and capacity.


## CausalRealization interface

For the generic causal-realization signature, take histories H, costed tests Test_B equal to closed primitive-control words of length at most B, Outcome equal to distributions on Z3, and encode(h)=mu_h, the posterior over holonomy. The response decoder maps a posterior to the outcome distribution of each closed path.

For B<3, the history quotient is a singleton. For B>=3 and eta != 1/3, full abstraction holds:
\[
h\sim_B h' \iff \mu_h=\mu_{h'}.
\]
The quotient is the image of the reachable posterior map (the full two-simplex if all beliefs are admitted as states). At eta=1/3 it is a singleton at every budget. The Python model verifies the finite response calculations; the abstract Lean theorem has not yet been instantiated with this specific model.


## 7. Exact posterior-Hankel factorization and balanced spectrum

For the uniform prior and one-loop observation histories y in Z3, the posterior-history matrix is R=K_eta because the channel is symmetric and its columns sum to one. The future-test matrix is O=K_eta. Hence the history-future Hankel matrix factors exactly:
\[
H=RO=K_\eta^2.
\]
Let P_perp=I-(1/3)11^T and lambda=1-3 eta. Since
\[
K_\eta=P_0+\lambda P_\perp,\qquad P_0=(1/3)11^T,
\]
we obtain
\[
P_\perp H P_\perp=\lambda^2P_\perp.
\]
The posterior-history and future-test Gramians are both
\[
W_c=W_o=\lambda^2P_\perp,
\]
so the balanced Gram product is
\[
W_c^{1/2}W_oW_c^{1/2}=\lambda^4P_\perp.
\]
The two nonzero squared singular values of the centered Hankel matrix are exactly lambda^4, matching the two nonzero eigenvalues of the balanced Gram product.

At eta=1/6, lambda=1/2:
- centered Hankel = (1/4) P_perp;
- Wc = Wo = (1/4) P_perp;
- balanced Gram = (1/16) P_perp.

At eta=1/3, all centered quantities vanish. This gives a gauge-theoretic counterpart to the posterior-Hankel results in Spikes 23 and 24. The exact matrices are included in the JSON artifact.
