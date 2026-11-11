# Spike 11: Does weight-space volume predict which circuit training finds? (H-B)

**Date:** 2026-11-11 · **Status:** pre-registered (hypotheses and kill criteria written before any run) · **Follows:** Spike 09 F2 (6–7 distinct circuits per 10 seeds) · **Prior-art check:** see `charter/LITERATURE_REVIEW.md` (H-B) and `charter/REFERENCES.md` (Zhong23, ConvEvo26)

## Question

Spike 09 found that the *function* training learns is predictable and the *circuit* is not: ten seeds give six or seven different minimal first layers ("isomers"). The volume hypothesis says training samples functions roughly in proportion to their prior volume in parameter space. Does the same law hold one level down, for *which isomer* of a fixed function training lands on?

## Setup (planned)

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
