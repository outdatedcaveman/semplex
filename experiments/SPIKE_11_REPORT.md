# Spike 11: Does weight-space volume predict which circuit training finds? (H-B)

**Date:** 2026-11-11 · **Status:** complete. Hypotheses and kill criteria were committed before any run (commit `cc839c6`); the diagnostics in F3–F4 are post hoc and labeled as such · **Follows:** Spike 09 F2 (6–7 distinct circuits per 10 seeds) · **Prior-art check:** see `charter/LITERATURE_REVIEW.md` (H-B) and `charter/REFERENCES.md` (Zhong23, ConvEvo26)

## Question

Spike 09 found that the *function* training learns is predictable and the *circuit* is not: ten seeds give six or seven different minimal first layers ("isomers"). The volume hypothesis says training samples functions roughly in proportion to their prior volume in parameter space. Does the same law hold one level down, for *which isomer* of a fixed function training lands on?

## Setup

- **Elements:** the 128 four-input elements with minimum determining width w\* = 2 that a single output neuron can combine (cost 3). For these, an isomer is an unordered pair {t1, t2} of threshold functions, up to complement, that determines g. All isomers are enumerated exactly.
- **Predictor (no fitted parameters):** V(I) = Ω(t1)·Ω(t2), where Ω(t) is the probability that one hidden unit with isotropic Gaussian weights and bias computes t or its complement (a solid angle in R^5, by Monte Carlo). Under an isotropic Gaussian prior on a width-2 network, the probability of computing g *through I* factors as V(I) times an output term. That term is the same for every isomer of g: every isomer needs a 3:1 output gate, and those gates have equal prior mass by symmetry. So the volume law predicts P(I | g learned) = V(I) / Σ V.
- **Baseline:** uniform over the isomers of g.
- **Runs:** (A) width 2, the minimal circuit itself, 200 seeds per element; (B) width 8 as in Spike 09, 100 seeds per element. Spike 09's optimizer and initialization. At width 8, every minimal pair present among the units gets equal fractional credit.
- **Scores:** log-likelihood gain over uniform (bits per run), the share of elements where the gain is positive, Spearman correlation per element, and the pooled log–log slope of observed frequency against predicted share.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H11.1 | At width 2, volume predicts the isomer better than uniform | gain ≥ 0.25 bits/run and positive in ≥ 75% of elements | gain ≤ 0.05 bits/run |
| H11.2 | Same at width 8 | same thresholds | same |
| H11.3 | The relation is proportional (a law, not just a ranking) | pooled log–log slope in [0.7, 1.3] | slope outside [0.4, 1.6] → "monotone but not proportional" |
| H11.4 | The width-2 result is not just training keeping its initial units | share of runs whose final units equal their initial units < 80% | ≥ 80% → the test only re-measures the initialization, so no content beyond sampling |

## Results (`results/spike11.json`; seeded; about 9 minutes on 4 CPUs)

Setup facts: Ω was estimated from 4·10⁷ samples, and all 941 threshold functions (up to complement, plus the constant) were seen. Elements have 5–1,457 isomers (mean 55). On average the predicted favourite gets 29% of an element's predicted mass.

| | Width 2 | Width 8 |
|---|---|---|
| Nets / fit / fit with a minimal pair | 25,600 / 6,376 / 6,316 | 12,800 / 12,783 / 6,584 |
| Elements scored | 123 | 126 |
| **Gain over uniform (bits/run)** | **+0.245** | **−0.024** |
| Elements with positive gain | 43% | 46% |
| Median Spearman within an element | 0.19 | 0.19 |
| Most-observed isomer = predicted favourite | 15% (uniform chance 6%) | 10% (6%) |
| Pooled log–log slope (as registered) | 0.89 | 1.13 |
| Same slope, normalized per element (post hoc) | | 0.74 |
| Runs whose final units equal their initial units | 0% | |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H11.1 | **Not held, not broken.** The gain of 0.245 bits/run is just below the 0.25 threshold, and it is positive in only 43% of elements (75% needed). It is above the 0.05 kill line. |
| H11.2 | **Broken.** At width 8 the volume predictor is no better than uniform (−0.02 bits/run). |
| H11.3 | **The registered test had no content; sharpened** (F2). The registered slope was in range at both widths, but that metric is confounded. Normalized per element, the relation is monotone only at the extremes. |
| H11.4 | **Held, but weak.** No run kept its initial units. That was nearly guaranteed: two random units almost never determine g at initialization, so this rules out only the most trivial reading. |

## Findings

**F1. Prior volume does not tell us which circuit training builds, even though it tells us which function training picks.** Spike 09 found volume-style simplicity bias at the level of functions (94–95% cheapest completions). One level down, among the minimal circuits of one function, the same kind of predictor carries almost no information. At width 2 it gains about a quarter of a bit per run. At the architecture Spike 09 used (width 8) it gains nothing. The extension of the volume hypothesis from functions to mechanisms proposed as H-B does not hold in this setting.

**F2. The registered calibration metric was confounded, and the corrected one shows where the signal is.** Pooling isomers across elements mixes elements with 5 isomers and elements with 1,457. Every isomer of a small element has a large predicted *and* observed share, so the pooled slope looks proportional even without a law. Normalizing each element by its uniform share (post hoc) gives slope 0.74 at width 8. The bins are non-monotone in the middle. The only clear effect is at the top: when the predictor puts more than 4× the uniform share on an isomer, training does too (4.6× predicted, 4.3× observed). The pre-registration should have specified the normalized metric; this is recorded as a protocol lesson.

**F3. Exploratory (post hoc): training prefers unbalanced units, against the volume.** Within an element, the observed frequency correlates with *imbalance* of the two units (how far each unit's number of true inputs is from 8): median Spearman 0.47, against 0.19 for log volume. The units with the largest solid angles are the balanced ones, such as single variables. So the dominant preference of training runs partly against the prior volume. This is a single diagnostic chosen after seeing the data; it becomes a hypothesis (H-B′ below), not a finding.

**F4. Small elements are where the predictor fails worst.** For elements with at most 20 isomers, the mean gain is −0.5 to −0.6 bits/run at both widths: the predictor is confidently wrong. The positive part of the width-2 gain comes from elements with many isomers. (Post hoc.)

## Proposed next step

- **H-B′ (to pre-register in a later spike):** among minimal circuits of one function, gradient training prefers circuits whose units split the inputs unevenly. A predictor based on imbalance (or a margin-based quantity) beats both volume and uniform on a *fresh* seed set and on 5-input elements.
- Also test whether F3 is about the optimizer: repeat with plain gradient descent and with a different initialization scale. Volume is scale-free; the training dynamics are not.

## Gaps

- One optimizer (AdamW), one horizon, one initialization distribution. The prior used for V is isotropic Gaussian; the network's own initialization has zero output bias, which does not matter for V (the output factor is constant per element) but does matter for training.
- The width-2 fit rate is 25%, so its isomer frequencies are conditioned on a selected subset of runs.
- At width 8, every minimal pair present gets equal credit. A net holding several minimal pairs is counted fractionally, which flattens the observed distribution.
- The in-sample "ceiling" is inflated: there are about 50 runs per element over about 55 isomers. It is reported only as an upper reference.
