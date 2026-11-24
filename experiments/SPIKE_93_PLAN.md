> Renumbered from canonical distinction-calculus `SPIKE_23_PLAN` to `SPIKE_93_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 23 — Observation-conditioned past Gramian and the finite HMM Hankel factorization

**Date:** 2026-11-21  
**Status:** PASS — finite exact model; 6/6 tests  
**Code:** experiments/belief_state_hankel_factorization.py  
**Tests:** tests/test_belief_state_hankel_factorization.py  
**Artifact:** artifacts/belief-state-hankel-factorization-20261121.json

## Question

Does the current Wc vanish because it models only action-induced changes of a uniform prior, and does adding the agent's observation history produce the correct past predictive feature map and a nonzero balanced/Hankel operator?

## Model

- Hidden state X = Z2.
- Actions A = Z2 acting by identity and swap.
- Prior pi = (1/2,1/2).
- Observation y is one-hot and reveals the current hidden state.
- Future tests consist of observing now and after each group action.

For action-only histories, every action preserves the uniform prior, so the posterior remains pi and the centered past Gramian is zero.

For an observation history y, the posterior is mu_y=delta_y. Define whitened posterior feature:
\[
r_y=D_\pi^{-1/2}(\mu_y-\pi).
\]
Then the posterior-history covariance is:
\[
W_c^{obs}=E_y[r_y r_y^\top]=P_\perp.
\]

The future-test response matrix O has rows indexed by hidden states and columns by future tests. The history-future response matrix is:
\[
H_{h,\tau}=P(\tau\mid h)=\langle\mu_h,f_\tau\rangle,
\qquad H=R O.
\]

## Hypotheses

- H23.1: action-only histories yield one predictive profile and Wc=0.
- H23.2: one-hot observation histories yield two predictive profiles and Wc_obs=P_perp.
- H23.3: the history-future response matrix factors exactly through posterior beliefs.
- H23.4: the balanced product using Wc_obs and Wo is nonzero, while the action-only product is zero.
- H23.5: the distinction is an information-access difference for two agents interacting with the same physical system, not a change in physical ontology.

## Limits

This is a finite HMM/PSR example. It does not prove that the current Master Operator is universally optimal, nor that its kinematic cost is a thermodynamic cost. It isolates the correct role of observation-conditioned posterior histories in the past Gramian.
