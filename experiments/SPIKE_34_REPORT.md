# Spike 34: The compiler as the prior. Does minimum circuit cost explain generalization?

**Date:** 2026-11-13 · **Status:** complete (pre-registered in a45f946; results below) · **Follows:** Spikes 30–33 (the initial kernel and the exact init-prior posterior each explain most of *what* trained nets predict, but nets generalize better than both, and only when features learn). This is the first spike since 11 to use the compiler (`atlas.compile_task`, Spike 08) as an object of study.

## Conjecture C19

The part of generalization that neither the kernel nor the init-prior posterior explains is an **Occam prior over circuits**. Among the 16 completions of the 4 unseen outputs, training moves toward the one with the fewest threshold neurons. Spike 33 showed feature learning is required for the gain; C19 says what feature learning moves *toward*.

**Not rigged in its favour.** The targets are 3-neuron circuits (w* = 2). When a cheaper completion exists (a single threshold function, cost 1), the Occam prior picks it and is wrong on that task. The test is whether minimum cost generalizes better than the priors already measured.

## Design

The same 1,280 tasks per activation as Spikes 29–33: same elements, masks and seeds. Each task is a target g, 12 seen inputs and 4 held-out inputs.

**Predictors.** Neither depends on the activation.
- **Occam.** Among the 16 completions, take those with the minimum neuron count `tb.hi`, breaking ties by minimum depth. Each held-out bit is the majority over the tied minimal completions; a tie goes to the majority of the seen labels.
- **Occam→volume.** The same, but ties among minimal completions are broken by the Spike 32 init-prior posterior restricted to them, separately per activation.

**Exactness check.** The fraction of all completions whose neuron count is exact (`tb.exact`) is reported. If it is below 0.99, the verdicts are flagged.

**Compared against** (identical tasks): trained nets (Spike 30 raw, fitted nets only), the NTK (Spike 30) and the init-prior posterior (Spike 32). Balanced accuracy is primary; raw accuracy is reported.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H34.1 | The Occam prior generalizes better than training | Occam balanced accuracy ≥ 0.60 (the best net was 0.561) | ≤ 0.55 |
| H34.2 | Nets that agree more with Occam generalize better | Spearman ρ(agreement with Occam, net balanced accuracy) over 24 activations ≥ 0.5 | ρ ≤ 0 |
| H34.3 | **What training adds beyond Bayes-under-init points toward Occam** | on held-out inputs where net and posterior disagree, pooled over activations, Occam sides with the net ≥ 60% | ≤ 50% |
| H34.4 | Volume refines Occam's ties | mean Occam→volume balanced accuracy ≥ Occam's | < Occam's − 0.01 |

---

## Results

`results/spike34.json`. All completions' neuron counts are exact (`tb.exact` holds for 100%).

| Quantity | Value |
|---|---|
| Occam balanced accuracy (raw accuracy) | **0.552** (0.590) |
| Mean number of completions tied at the minimum cost, of 16 | **9.86** |
| Tasks with a completion cheaper than the target | 20.9% |
| Trained nets below / above Occam (balanced) | 15 below / 9 above (the ReLU family, GELU, SiLU, softplus, ELU, \|x\|, clip4) |
| ρ(net–Occam agreement, net balanced accuracy) | 0.46 |
| Occam sides with the net where net and init-prior posterior disagree (24,471 pooled) | 45.2% |
| Occam→volume minus Occam, mean balanced | −0.015 |

Net–Occam agreement (0.70–0.76) is *lower* than net–posterior agreement (0.73–0.83) in 23 of 24 activations.

### Verdicts

| # | Verdict |
|---|---|
| H34.1 | **Neither held nor broken.** 0.552: just above the 0.55 kill line, below 0.60. Occam beats 15 of 24 activations' nets, but not the best ones. |
| H34.2 | **Neither held nor broken.** ρ = 0.46. |
| H34.3 | **Broken.** Where training departs from Bayes-under-init, it does *not* move toward the cheapest circuit (45.2% < 50%). |
| H34.4 | **Broken.** Breaking Occam's ties by init volume *hurts* (−0.015). |

## Findings

**F1. C19 is not supported. The gain training makes beyond the init prior is not an Occam move toward minimum circuit cost.** Four priors have now been tested on the same tasks: the NTK, the exact init-prior posterior, Occam, and Occam→volume. None reproduces the extra generalization that feature learning adds (Spikes 32–33).

**F2. At n = 4 the compiler's cost is too coarse to be a sharp prior.** About 10 of 16 completions tie at the minimum neuron count, and in 21% of tasks a cheaper completion than the target exists. Occam is still competitive: it matches or beats the trained nets of 15 activations, with no training at all. But it cannot rank completions finely enough to explain the residual.

**F3. What this says about the experimental platform.** Every prior tested sits between 0.50 and 0.56 balanced. At 12 seen points of 16, every task has exactly 16 completions and only coarse cost levels, so priors cannot be told apart. This is the strongest argument yet for **front 2** (certified composition to n = 5–6): with more inputs, costs spread out, completions multiply, and the four priors make different predictions. The prediction to carry forward: at n ≥ 5, Occam's ties shrink, and its advantage over the init-prior posterior, if C19 has any truth, should grow.
