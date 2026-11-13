# Spike 34: The compiler as the prior. Does minimum circuit cost explain generalization?

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spikes 30–33 (the initial kernel and the exact init-prior posterior each explain most of *what* trained nets predict, but nets generalize better than both, and only when features learn). This is the first spike since 11 to use the compiler (`atlas.compile_task`, Spike 08) as an object of study.

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
