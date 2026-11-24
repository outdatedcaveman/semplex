> Renumbered from canonical distinction-calculus `SPIKE_23_REPORT` to `SPIKE_93_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 23 — The missing past feature is the observer's posterior

**Status:** PASS — finite Z2 model; 6/6 tests.  
**Date:** 2026-11-21  
**Plan:** experiments/SPIKE_23_PLAN.md  
**Code:** experiments/belief_state_hankel_factorization.py  
**Tests:** tests/test_belief_state_hankel_factorization.py

## Result

The same physical system has different predictive quotients for two agents with different information access.

- An action-only observer with a uniform prior sees only actions that permute the hidden states. Its posterior remains uniform. All action-only histories have the same predictive response profile, and the centered past Gramian is zero.
- An observer receiving a one-hot measurement has posterior \(\mu_y=\delta_y\). The two observation histories have different future response profiles. The whitened posterior covariance is exactly \(P_\perp\), the nonzero centered projector.

For the finite model:
\[
W_c^{action}=0,\qquad W_c^{obs}=P_\perp,\qquad W_o=P_\perp.
\]
The history-future response matrix factors:
\[
H=RO,
\]
where R maps observation histories to posterior beliefs and O maps hidden states to future-test response vectors.

Thus:
\[
(W_c^{action})^{1/2}W_o(W_c^{action})^{1/2}=0,
\]
but:
\[
(W_c^{obs})^{1/2}W_o(W_c^{obs})^{1/2}=P_\perp\ne0.
\]

## Interpretation

This sharpens Spike 22. The current Wc is not necessarily wrong: it is the past-information Gramian for the restricted action-only history model with an invariant prior. It is incomplete if the intended agent history includes observations and Bayesian updates.

The correct past feature map for a physically grounded agent is generally built from its posterior beliefs:
\[
\mu_h(x)=P(X_t=x\mid h).
\]
The future response map sends a state to predictions of future tests. Their composition gives the action-observation Hankel matrix. In this finite HMM, the factorization is exact.

This is a promising bridge between:
- physical reality: hidden states, transitions, and actual observation channels;
- mental representation: the agent's posterior predictive state;
- mathematics: the Hankel factorization and the minimal predictive quotient.

The semantic quotient is agent-relative only through physically specified access to observations and interventions. It is not arbitrary subjectivity.

## What this does not establish

- It does not prove that Wc_obs is the correct general Wc for all systems.
- It does not prove the Master Operator should use a balanced product rather than Wc+Wo.
- It does not establish a universal resource-cost law.
- It does not make the finite HMM factorization novel; it is standard predictive-state/observable-operator structure.

The next theorem must derive posterior-history and future-test feature maps for a declared physical protocol, then establish the exact Hankel factorization and its resource-bounded realization.


## Verification

\`\`\`text
pytest -q tests/test_belief_state_hankel_factorization.py
6 passed
\`\`\`

The machine artifact is artifacts/belief-state-hankel-factorization-20261121.json. All eight exact assertions pass, including the distinction between action-only and observation-conditioned predictive quotients.


## Lean companion

The generic belief-to-response factorization is formalized in proofs/lean/BeliefStateHankel.lean. It proves that the history-future response factors through the belief state, that belief equality implies predictive equivalence, that test separation gives the converse, and that an exact internal response decoder cannot merge predictively distinct histories. The module compiles under Lean 4.12 core; the posterior factorization and representation-kernel theorem are axiom-free. The audit is in proofs/lean/AuditSemanticGrounding_20261121.txt.
