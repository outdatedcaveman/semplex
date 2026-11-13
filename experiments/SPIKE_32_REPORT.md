# Spike 32: Is training a Bayesian posterior under the init prior? The volume account of generalization (after singular learning theory)

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spikes 30–31 (the initial NTK is the generalization prior, ρ = 0.79 balanced, 76% agreement; learning improves on it). **Inspired by:** Resolution (Snikkers, Newgas, Hoogland, Elliott), "Formalizing Hironaka's Resolution of Singularities" (6 Oct 2026), read in full. Its motive is Watanabe's singular learning theory (SLT), in which Bayes generalization error is set by the volume geometry (RLCT) of the zero-loss set.

## Conjecture C17

A trained net's held-out prediction is the **zero-temperature Bayesian posterior under the initialization prior**. Among the 16 completions of the 4 unseen outputs, training picks in proportion to the init-probability (weight-space volume) of nets computing each completion. The NTK of Spikes 30–31 is the linearized (Gaussian-process) shadow of this prior. The full volume prior should match trained nets better, and should account for the part of learning that "improves on the kernel".

**Prior art.** Mingard, Valle-Pérez, Skalse & Louis, "Is SGD a Bayesian sampler? Well, almost" (JMLR 2021) proposes that the probability SGD finds a function tracks its Bayesian posterior under the init prior. They test it with Gaussian-process (NNGP) approximations of that posterior on MNIST and CIFAR. What the atlas adds is an *exact* finite-width posterior, with no Gaussian-process approximation, and a head-to-head comparison with the NTK on the same 24 activations, masks and seeds. SLT's asymptotic RLCT statements (n → ∞) are not tested here: n = 12 is far from asymptotic.

## Design

- **Function frequency table.** For each of the 24 activations, sample 16,000,000 width-8 nets from `train.init`'s distribution (seed 32,000 + i). Record the 16-bit function each computes as sign(z) ≥ 0 at the 16 inputs, giving freq(g) over all 65,536 g.
- **Posterior predictive** for each Spike 29/30 task, i.e. each net's seen set and target. The 16 completions g consistent with the 12 seen labels get weight ∝ freq(g) + 0.5 (add-half smoothing). The predicted held-out bit is 1 iff its posterior probability exceeds 0.5. Ties (all weights equal) predict the majority of the seen labels.
- **Comparison.** Agreement with the trained nets' held-out predictions (Spike 30 raw, fitted nets only) and balanced accuracy, against the NTK kernel on identical tasks. Raw accuracy is reported too.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H32.1 | The volume posterior matches trained nets better than the NTK | mean agreement (over 24 activations) exceeds the NTK's 0.763 by ≥ 0.03 | it is lower than the NTK's |
| H32.2 | It ranks the activations' generalization at least as well | Spearman ρ(posterior balanced accuracy, net balanced accuracy) ≥ 0.79 (the NTK's) | ρ ≤ 0.5 |
| H32.3 | It accounts for the improvement over the kernel: where net and NTK disagree, the posterior sides with the net | ≥ 60% of pooled disagreements | ≤ 50% |
| H32.4 | It generalizes at least as well as the trained nets | posterior balanced accuracy ≥ net balanced accuracy in ≥ 18 of 24 activations | in ≤ 6 of 24 |
