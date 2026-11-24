> Renumbered from canonical distinction-calculus `SPIKE_22_PLAN` to `SPIKE_92_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 22 — Orbit-response kernel versus prior-belief reachability

**Date:** 2026-11-21  
**Status:** exact Z2 counterexample passes; 9 tests  
**Prior artifact:** Gemini G18 group coset-readout kernel theorem  
**Code:** experiments/orbit_kernel_vs_belief_gramian.py  
**Tests:** tests/test_orbit_kernel_vs_belief_gramian.py  
**Artifact:** artifacts/orbit-kernel-vs-belief-gramian-20261121.json

## Question

Is the current past Gramian Wc the reachability factor of the group orbit-response kernel used in G18? Does the standard balanced product \(W_c^{1/2}W_oW_c^{1/2}\) reproduce the orbit kernel when Wc is defined from a uniform prior?

## Exact model

Take \(G=\mathbb Z_2\) acting regularly on \(X=\mathbb Z_2\) by XOR, with uniform prior \(\pi=(1/2,1/2)\) and one-hot readout \(o(x)=e_x\).

The G18-style orbit kernel is:
\[
K(g,h)=\mathbb E_{w\sim\mathrm{Unif}(G)}
\langle o(gw),o(hw)\rangle.
\]
For one-hot readout, \(K=I_2\), hence its centered restriction is \(P_\perp\neq0\).

The current Master Principle past Gramian starts from the uniform-prior rank-one matrix \(B_0=\mathbf1_\pi\mathbf1_\pi^\top\), propagates it by \(B\mapsto |A|^{-1}\sum_aT_a^\top BT_a\), then centers. Every group permutation preserves the uniform prior, so \(W_c=0\).

The future observability Gramian \(W_o\) is nonzero. Thus \(W_c+W_o=W_o\neq0\), while the standard balanced product built from this Wc is:
\[
W_c^{1/2}W_oW_c^{1/2}=0.
\]

If instead the past-feature map includes all centered initial-state perturbations, \(W_c^{state}=P_\perp\), then:
\[
(W_c^{state})^{1/2}W_o(W_c^{state})^{1/2}=W_o.
\]
The result depends on what the past input/history feature map represents.

## General orbit-kernel identity

For a finite group acting on a finite state space with invariant prior \(\mu\), and vector-valued readout \(o\), define:
\[
K(g,h)=\mathbb E_{x\sim\mu}\langle o(gx),o(hx)\rangle.
\]
Then K is positive semidefinite because:
\[
\sum_{g,h}a_ga_hK(g,h)
=\mathbb E_x\left\|\sum_g a_go(gx)\right\|^2\ge0.
\]
For a left action and invariant prior, \(K(gs,hs)=K(g,h)\), so \(K(g,h)=\kappa(hg^{-1})\) with \(\kappa(s)=\mathbb E_x\langle o(x),o(sx)\rangle\). The G18 coset one-hot identity is a central special case; arbitrary readouts need not produce a class function.

## Acceptance criteria

- Z2 orbit kernel equals identity for one-hot readout.
- Current uniform-prior Wc vanishes exactly up to floating-point tolerance.
- Wo remains nonzero.
- Current balanced product collapses to zero.
- Centered-state baseline product recovers Wo.
- Arbitrary vector readout yields a PSD orbit Gram.
- Interpret the result as a mismatch of feature maps, not as a refutation of balanced realization theory.


## Additional algebraic witness

Use diagonal positive Gramians \(W_c=\operatorname{diag}(100,60)\) and \(W_o=\operatorname{diag}(1,40)\). Then the sum ranks mode 1 first (101 vs 100), while the balanced product ranks mode 2 first (100 vs 2400). This exact example demonstrates that sum-based and balanced joint controllability/observability objectives can select opposite modes, even when both Gramians are nonzero.
