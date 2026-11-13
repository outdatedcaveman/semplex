# Spike 32: Is training a Bayesian posterior under the init prior? The volume account of generalization (after singular learning theory)

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 0b4e14b; results below) · **Follows:** Spikes 30–31 (the initial NTK is the generalization prior, ρ = 0.79 balanced, 76% agreement; learning improves on it). **Inspired by:** Resolution (Snikkers, Newgas, Hoogland, Elliott), "Formalizing Hironaka's Resolution of Singularities" (6 Oct 2026), read in full. Its motive is Watanabe's singular learning theory (SLT), in which Bayes generalization error is set by the volume geometry (RLCT) of the zero-loss set.

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

---

## Results

16 million init samples per activation; the same 1,280 tasks per activation as Spikes 29–31 (fitted nets only). Raw data in `results/spike32_raw/`, analysis in `results/spike32.json`.

| | Init-prior posterior | NTK (Spike 30) |
|---|---|---|
| Mean agreement with trained nets on held-out inputs | **0.800** | 0.763 |
| ρ(balanced accuracy, net balanced accuracy) over 24 activations | 0.72 | 0.79 |
| Balanced accuracy ≥ the nets' | **0 of 24** activations | 0 of 24 |

On the 28,994 inputs where net and NTK disagree, the posterior sides with the net 43.6% of the time.

Per activation: the posterior's balanced accuracy is 0.499–0.553; the nets' is 0.519–0.561. The posterior agrees with the nets more than the NTK does in 24 of 24 activations.

### Verdicts

| # | Verdict |
|---|---|
| H32.1 | **Held.** Agreement 0.800, +0.037 over the NTK. |
| H32.2 | **Neither held nor broken.** ρ = 0.72: below the NTK's 0.79, above 0.5. |
| H32.3 | **Broken.** Where the net departs from the kernel, the posterior sides with the net only 43.6% of the time. |
| H32.4 | **Broken.** The posterior never generalizes as well as the trained nets (0 of 24). |

## Findings

**F1. Trained nets are closer to Bayes-under-the-init-prior than to the NTK.** The full weight-space-volume posterior predicts what a trained net outputs on an unseen input 80% of the time, against 76% for the kernel, and does so in every activation. As a *description* of the function training picks, the volume account (Mingard et al.; SLT's finite-n object) beats the kernel.

**F2. But the nets generalize better than the posterior, every time.** In all 24 activations the trained nets' balanced accuracy exceeds that of the exact init-prior posterior predictive. That is notable, because a Bayes posterior *predictive* normally beats a single draw from the posterior. The part of learning that improves on the kernel (Spike 30, +2.6 balanced points) is *not* explained by the volume prior either: where the net leaves the kernel, the posterior mostly sides with the kernel.

**F3. Where this leaves "why does it generalize".** On this atlas there are three layers:
1. The init prior, whether as NTK or exact volume, accounts for most of *what* the net predicts (76–80% agreement) and for much of the ranking across activations (ρ ≈ 0.7–0.8).
2. Neither prior generalizes as well as the trained nets.
3. The remainder is a consistent, positive effect of the training *dynamics* that is not in the initial measure, i.e. not Bayesian under the init prior. Spike 23 identified candidate forces acting step by step: information tilt (μ = 3.9) and symmetry (β = 0.26), beyond distance.

**Conjecture C18 (next).** The step-level information tilt is what carries generalization beyond the init prior. The test: a training rule with the tilt removed (Spike 20's selection-only readout training, or a rule that steps by distance alone) should fall to the posterior's accuracy, not stay at the net's.

**Caveats.**
- Rare completions rely on add-half smoothing.
- The posterior is zero-temperature: exact consistency with the 12 seen labels.
- Balanced accuracies are weak overall (≤ 0.56), so absolute effects are small, though consistent in sign across all 24 activations.
- SLT's asymptotic RLCT claims are untested at n = 12.
