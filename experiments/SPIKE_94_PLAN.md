> Renumbered from canonical distinction-calculus `SPIKE_24_PLAN` to `SPIKE_94_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 24 — Three-state partial-observation Hankel realization

**Date:** 2026-11-21  
**Status:** PASS — 4/4 tests; all 10 machine assertions pass  
**Code:** experiments/partial_observation_hankel_z3.py  
**Tests:** tests/test_partial_observation_hankel_z3.py  
**Artifact:** artifacts/partial-observation-hankel-z3-20261121.json

## Question

Can we verify, beyond the two-state fully revealing example, that observation-conditioned posterior histories generate the correct past Gramian and that the balanced product reproduces the weighted Hankel singular spectrum?

## Model

- Hidden states \(X=\mathbb Z_3\), uniform prior.
- Actions are the three cyclic shifts.
- Observations \(Y=\{0,1\}\) have likelihoods:
  \(P(1\mid x)=(0.9,0.5,0.1)\),
  \(P(0\mid x)=(0.1,0.5,0.9)\).
- Histories consist of one observation followed by one cyclic action.
- Future tests consist of one cyclic action followed by one observation.

There are six histories and six future tests. The posterior map R has six distinct rows; the future response map O is state-indexed. The probability Hankel matrix is \(H=RO\). After centering and prior whitening, the weighted matrix is \(\widetilde H=D_h^{1/2}R_{\rm feat}O_{\rm feat}D_\tau^{1/2}\).

## Acceptance criteria

- Action-only histories preserve the uniform prior and give \(W_c^{action}=0\).
- Observation-conditioned histories give nonzero \(W_c^{hist}\).
- Six distinct posterior beliefs and six distinct future profiles.
- Centered weighted Hankel rank equals 2.
- Nonzero squared singular values of \(\widetilde H\) equal the eigenvalues of \(W_c^{1/2}W_oW_c^{1/2}\).
