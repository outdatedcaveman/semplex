> Renumbered from canonical distinction-calculus `SPIKE_22_REPORT` to `SPIKE_92_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 22 — The group orbit kernel is not the current uniform-prior Hankel factorization

**Status:** PASS — exact finite Z2 model; 9/9 tests.  
**Date:** 2026-11-21  
**Plan:** experiments/SPIKE_22_PLAN.md  
**Code:** experiments/orbit_kernel_vs_belief_gramian.py  
**Tests:** tests/test_orbit_kernel_vs_belief_gramian.py  
**Artifact:** artifacts/orbit-kernel-vs-belief-gramian-20261121.json

## 1. Main result

A small exact group model exposes a distinction that the current Semplex terminology must preserve.

For \(G=\mathbb Z_2\) acting on itself by left translation, uniform prior, and one-hot readout:
\[
K(g,h)=\mathbb E_w\langle o(gw),o(hw)\rangle=I_2.
\]
Thus the group orbit-response kernel is nonzero and distinguishes the two group elements.

But the current Master Principle past Gramian \(W_c\) begins from the uniform-prior rank-one form and propagates it by the adjoint transition action. Since every group action is a permutation preserving the uniform prior:
\[
W_c=0
\]
after centering. The future observability Gramian remains nonzero:
\[
W_o=2(1+0.8+0.8^2)P_\perp=4.88P_\perp
\]
for horizon 3 and \(\gamma_o=0.8\).

Therefore:
- the current sum \(W_c+W_o\) remains nonzero and selects the centered state direction;
- the balanced product \(W_c^{1/2}W_oW_c^{1/2}\) collapses to zero;
- replacing the past Gramian with the centered full-state baseline \(W_c^{state}=P_\perp\) makes the balanced product recover \(W_o\).

This is not a counterexample to balanced truncation. It shows that the current \(W_c\) is not the state-orbit controllability Gramian corresponding to the G18 orbit kernel. It measures *change of the chosen uniform prior under past action*, a belief/prior-sensitivity quantity. The orbit kernel indexes transformations acting on state-specific readouts. These are different past-feature maps.

## 2. Why this matters

The current Master Operator uses:
\[
G_\lambda=e^{-\lambda L_{\rm kin}/2}(W_c+W_o)e^{-\lambda L_{\rm kin}/2}.
\]
The sum is a valid positive-semidefinite joint feature Gram if Wc and Wo are separately Gram matrices. It combines prior-sensitivity and future-observability information. It is not, without a further factorization theorem, the standard Hankel singular-value operator.

In standard linear realization, if \(H=OR\), with controllability and observability Gramians \(W_c=RR^*\) and \(W_o=O^*O\), the balanced/Hankel spectrum is governed by:
\[
W_c^{1/2}W_oW_c^{1/2},
\]
not \(W_c+W_o\). But the current Wc is generated from a particular uniform-prior input feature; it cannot simply be substituted into that formula for every semantic kernel.

The exact missing specification is: **what are the past histories, initial-state features, and prior distribution that define the Hankel factor R?** Until this is fixed, calling Wc+Wo a Hankel Gram is too strong. A safer name is a *two-sided causal-interface Gram* or *sum-of-past-and-future response Gramians*.

## 3. General arbitrary-readout group kernel

For a finite group G acting on a finite state set X with invariant prior μ and vector readout o, define:
\[
K(g,h)=\mathbb E_{x\sim\mu}\langle o(gx),o(hx)\rangle.
\]
It is PSD for any readout:
\[
\sum_{g,h}a_ga_hK(g,h)=
\mathbb E_x\left\|\sum_g a_go(gx)\right\|^2\ge0.
\]
For a left action and invariant prior, the kernel is right-invariant under simultaneous right multiplication of its group labels:
\[
K(gs,hs)=K(g,h),
\]
so it is a positive-definite function of \(hg^{-1}\). The G18 coset one-hot theorem gives the special central case \(\kappa(s)=\chi_{\rm perm}(s)/[G:H]\). For arbitrary readouts, \(\kappa\) need not be conjugation-invariant; the Fourier transform is then matrix-valued on irreducible representations rather than one scalar per irrep.

This supplies a clean mathematical extension of the G18 formula, but the general positive-definite-kernel fact is standard harmonic analysis. Its value here is to identify the exact hypotheses needed for the scalar Gibbs reduction.

## 4. Exact finite verification

\`\`\`text
pytest -q tests/test_orbit_kernel_vs_belief_gramian.py
7 passed in 0.45s
exit code 0
\`\`\`

All six machine assertions passed:
- current Wc is zero;
- Wo is nonzero;
- orbit kernel is identity;
- current balanced product is zero;
- state-baseline balanced product recovers Wo;
- arbitrary-readout orbit kernel is PSD.

The tiny residual norm in Wc (\(\sim 7.1\times10^{-32}\)) is floating-point roundoff from eigendecomposition; the exact symbolic argument is permutation invariance of the uniform prior.

## 5. Consequence for the foundational principle

Keep the two-clause Causal-Realization Principle, but sharpen the content clause:

1. **Semantic content:** equality of complete response profiles under a declared family of admissible histories, interventions, and observations; the quotient is the coarsest exact predictive state.
2. **Physical/mental realization:** an internal dynamical system factors through or approximates that quotient under explicit causal and resource constraints.

The Master Operator is a candidate selector for the second clause. Its sum \(W_c+W_o\) must be interpreted as a joint causal-interface Gram until a past/future factorization theorem identifies it with a Hankel object. The prior \(\pi\) and the choice of past-feature map are part of the semantics, not harmless implementation details.

This also clarifies the physical/mental/mathematical bridge: physical systems supply actual intervention-response channels; agents build resource-bounded internal realizations of their task-relative response quotients; mathematics studies the invariants and morphisms preserving those response structures. The claim that every mathematical structure is physically instantiated remains an additional metaphysical hypothesis, not a consequence of this formalism.


## 6. Independent diagonal ranking counterexample

Even when both Gramians are nonzero, the sum and balanced product can select opposite modes. Take:
\[
W_c=\operatorname{diag}(100,60),\qquad
W_o=\operatorname{diag}(1,40).
\]
Then:
\[
W_c+W_o=\operatorname{diag}(101,100),
\]
so the sum selects mode 1, whereas:
\[
W_c^{1/2}W_oW_c^{1/2}
=\operatorname{diag}(100,2400),
\]
so the balanced product selects mode 2. The first mode is highly reachable but weakly observable; the second is jointly strong. This is the standard reason balanced realization uses a joint product rather than an additive score when the target is minimal input-output realization.

This example does not establish that the balanced product is the right Semplex operator: that depends on whether the current Wc and Wo arise from the same past/future factorization. It establishes that Wc+Wo and the balanced product are different objectives, not interchangeable notations.


## 7. Kinematic Dirichlet cost is not thermodynamic entropy production

In the same Z2 example, take the random-action transition matrix \(P=(I+S)/2\) with uniform stationary distribution. It satisfies detailed balance, so its stationary entropy production is exactly zero. Yet the action-averaged Dirichlet operator is:
\[
L_{\rm kin}=P_\perp\ne0.
\]
Thus \(L_{\rm kin}\) measures variation of state features under the available transitions; it is a kinematic/smoothness cost, not thermodynamic dissipation. A physical energy interpretation requires a separate calibration to transition rates, local detailed balance, work, and heat. This distinction is reinforced by Still et al. (2012, 2020) and the 2026 Dobrynin–Stroujkova preprint on thermodynamic costs of predictive memory.
