# Spike 30: Why do these nets generalize? The initial-kernel account (C15)

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 4df8933; results below) · **Follows:** Spike 29 (the information tilt *anti*-correlates with held-out accuracy, ρ = −0.69), Spike 16 (function-level symmetry inheritance is mostly the kernel limit)

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

---

## Results

The rerun reproduces Spike 29 exactly: the maximum difference in per-activation held-out accuracy is 0.000. Raw data in `results/spike30_raw/`, analysis in `results/spike30.json`. Over the 24 activations:

| Quantity | Value |
|---|---|
| ρ(kernel held-out accuracy, net held-out accuracy) | **0.81** (looser ridge: 0.92) |
| Mean net–kernel agreement on held-out inputs | **0.763** |
| ρ(λ, net–kernel agreement) | **−0.61** |
| Kernel right where net and kernel disagree (28,994 pooled cases) | **0.449**, i.e. the net is right 55.1% of the time |
| Hamming-1 neighbour vote | 0.545 for every activation (it uses no kernel) |

### Verdicts

| # | Verdict |
|---|---|
| H30.1 | **Held.** ρ = 0.81. |
| H30.2 | **Held.** Agreement 0.763 ≥ 0.75. |
| H30.3 | **Held.** ρ = −0.61. Tilted activations depart further from their kernel. |
| H30.4 | **Broken, in the opposite direction.** Where they disagree, the *net* is right (55.1%); the kernel is right only 44.9%. |

### Exploratory (computed after the verdicts, not pre-registered)

| | Spearman ρ with λ |
|---|---|
| Kernel held-out accuracy | **−0.73** |
| Net held-out accuracy (Spike 29) | −0.69 |
| Net gain over its own kernel | +0.23 |
| Net accuracy after regressing out kernel accuracy | **−0.03** |

The net beats its kernel in 23 of 24 activations, by a mean of +0.024 (range −0.001 to +0.037).

## Findings

**F1. Generalization here has two parts, and both are now measured.**
- **(a) The initial kernel sets the baseline and the ranking.** Kernel regression with the activation's NTK at init, fitted on the 12 seen points, ranks the activations' held-out accuracy at ρ = 0.81–0.92. The trained net agrees with it on 76% of unseen inputs.
- **(b) Training improves on the kernel.** Where the net leaves its kernel, it is right 55% of the time. That adds +2.4 points on average.

**F2. Spike 29's "tilt costs generalization" was a confound, and C14 is refuted as a mechanism.** Activations that produce a strong information tilt also have a *worse initial kernel* for this task (ρ = −0.73). Once the kernel is controlled for, the tilt has no relation to held-out accuracy (ρ = −0.03). Learning gains no less in tilted activations (ρ = +0.23). Feature learning departs further from the kernel *and* those departures are net-positive. So the tilt is not a cost. The indicator-like shape of an activation does two separate things: it makes the tilt, and it makes a worse smoothness prior over Hamming space.

**F3. Revised conjecture C15′.** "Why does it generalize" splits into a prior and an update.
- **The prior** is the activation's initial tangent kernel. For graded activations (ReLU family, |x|, GELU) it is smoother over Hamming space and suits these threshold-like targets better than the kernels of saturating activations.
- **The update** is feature learning. It moves away from the prior, toward crisp, information-tilted threshold mechanisms, and gains a consistent few points.

Open: *why* graded activations give better kernels here. A candidate, untested: their kernels decay more gradually with Hamming distance, so nearby inputs share labels more strongly. A direct test is the kernel's correlation with Hamming distance against its held-out accuracy.

## Addendum (2026-11-13, post hoc, from Spike 31 F3; verdicts above unchanged)

Held-out targets are 39.6% ones, so predicting 0 everywhere scores 0.604. That is higher than every net's held-out accuracy reported here. On balanced accuracy the nets are above chance but weak (0.519–0.561). The Spike 30 conclusions all survive on the balanced measure; see `SPIKE_31_REPORT.md` F3 and `results/spike31_exploratory.json`. Future spikes report balanced accuracy alongside raw accuracy.
