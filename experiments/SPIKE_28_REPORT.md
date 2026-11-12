# Spike 28: Does indicator-alignment predict the information tilt? (C13, on activations not yet run)

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 27 F3. The post-hoc observation: across 15 activations, the tilt λ ranks with R²(φ(x), 1[x > 0]), x ~ N(0, 2²), Spearman 0.84. That correlation was found after seeing the data. This spike tests it only on activations that have not been run.

## Conjecture C13

A unit's information tilt is strong when its output is mostly *which side* of its hyperplane the input lies on, i.e. when the indicator score R² = corr(φ(x), 1[x > 0])², x ~ N(0, 4), is high. Then the readout sees the threshold function t and selection follows I(t; g). When the output is graded with distance, the tilt is weak.

## Design

As Spikes 24 and 27: 128 elements × 40 seeds, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps; fresh seeds 28,000 + i; exact fits at step 3,000. R² was computed with 400,000 samples (rng seed 0) **before** any run. It is fixed here:

| Activation | R² | Group |
|---|---|---|
| erf(x) | 0.882 | high |
| sign(x)·√\|x\| | 0.848 | high |
| tanh(x) + 0.2x | 0.818 | high |
| tanh(x) + 0.5x | 0.767 | high |
| clip(x, 0, 2) | 0.631 | middle |
| bent identity, (√(x²+1) − 1)/2 + x | 0.600 | middle |
| clip(x, 0, 4) | 0.497 | low |
| SiLU, x·σ(x) | 0.459 | low |
| GELU, x·Φ(x) | 0.450 | low |

The clip family is a within-shape dose test: clip(x, 0, 1) already gave λ = 10.47 (Spike 24).

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H28.1 | High-R² activations have the tilt | every high-group λ ≥ 7 | any high-group λ < 4 |
| H28.2 | Low-R² activations lack it | every low-group λ ≤ 3 | any low-group λ > 5 |
| H28.3 | R² ranks λ across all nine new runs | Spearman ρ ≥ 0.7 | ρ ≤ 0.3 |

Runs fitting < 90% of nets are flagged and reported.
