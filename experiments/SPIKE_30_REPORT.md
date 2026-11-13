# Spike 30: Why do these nets generalize? The initial-kernel account (C15)

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spike 29 (the information tilt *anti*-correlates with held-out accuracy, ρ = −0.69), Spike 16 (function-level symmetry inheritance is mostly the kernel limit)

## Conjecture C15

On this atlas, a trained net's predictions on *unseen* inputs come mainly from its activation's **initial neural tangent kernel** (NTK). The NTK is the similarity over the 16 inputs that the activation and the initialization fix before any training. Gradient descent near init behaves like kernel regression with it, so the kernel is the generalization prior. Feature learning moves the net away from that kernel. That movement is what builds crisp, information-tilted threshold mechanisms (Spikes 19–28), and here it costs held-out accuracy.

Literature bearing, read 2026-11-13. These are analogies, not evidence:
- **WikiTrace** (arXiv 2611.14320): lessons compressed from outcome labels mislead unless the raw evidence is kept.
- **LeapQuant** (arXiv 2609.38166): committing to quantized values at every step accumulates correlated error.
- **The continuous diffusion and flow language model survey** (Tang et al. 2026): committing to discrete tokens early incurs factorization error.

Each matches the reading that an indicator unit commits early to a hard partition and discards graded distance information.

## Design

- **Nets.** The same 24 activations, masks and seeds as Spike 29 arm B: 128 elements × 10 seeds, width 8, 12 of 16 inputs seen. Arm B is rerun deterministically, this time storing each net's prediction on its 4 held-out inputs.
- **Kernel.** For each activation, the expected empirical NTK of the width-8 net at `train.init`, estimated by Monte Carlo over 400,000 hidden units:
  Θ(x, x′) = 8·( E[φ(z)φ(z′)] + 0.25·E[φ′(z)φ′(z′)]·(x·x′ + 1) ) + 1,
  where z = w·x + b and w, b ~ N(0, 0.5²). The constant 0.25 = E[w₂²].
- **Kernel prediction.** Kernel ridge regression on the 12 seen points, with targets ±1 and ridge ε = 10⁻³·tr(K)/12. The prediction on a held-out input is the sign. A sensitivity check uses ε = 10⁻¹·tr(K)/12 (reported, not pre-registered).
- **Reproduction check.** Each activation's net held-out accuracy must match Spike 29's to within 0.001. Otherwise the rerun is not the same experiment, and this is reported before any verdict.
- **Baselines (reported).** A Hamming-1 neighbour vote over seen points; the constant majority label.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H30.1 | **The kernel tracks generalization across activations** | Spearman ρ(kernel held-out accuracy, trained-net held-out accuracy) ≥ 0.6 over the 24 activations | ρ ≤ 0.2 |
| H30.2 | **Trained nets mostly inherit the kernel's predictions** | mean agreement between net and kernel on held-out inputs ≥ 0.75 | ≤ 0.6 |
| H30.3 | **Feature learning is departure from the kernel** | ρ(λ, net–kernel agreement) ≤ −0.5 | ≥ 0 |
| H30.4 | **Departure costs accuracy** | on held-out inputs where net and kernel disagree, pooled over activations, the kernel is right ≥ 55% of the time | ≤ 50% |

If H30.1–H30.4 hold, the answer to "why does it generalize" here is that **gradient descent inherits the initial kernel's smoothness prior, and the parts that generalize are the parts that did not learn features**. If H30.2 or H30.4 break, the kernel is not the explanation, and the other priors must be tested: the minimal-circuit (Occam) prior, and the volume prior of Spike 19 over completions.
