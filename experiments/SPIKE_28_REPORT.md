# Spike 28: Does indicator-alignment predict the information tilt? (C13, on activations not yet run)

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 361da8d; results below) · **Follows:** Spike 27 F3. The post-hoc observation: across 15 activations, the tilt λ ranks with R²(φ(x), 1[x > 0]), x ~ N(0, 2²), Spearman 0.84. That correlation was found after seeing the data. This spike tests it only on activations that have not been run.

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

---

## Results

Exact fits; raw data in `results/spike28_raw/`, fits in `results/spike28.json`. All runs fit ≥ 97.7% of nets.

| Activation | R² (fixed in advance) | Group | γ₃₀₀₀ | λ₃₀₀₀ |
|---|---|---|---|---|
| erf | 0.882 | high | 0.67 | **11.62** |
| sign·√\|x\| | 0.848 | high | 0.41 | **10.97** |
| tanh(x) + 0.2x | 0.818 | high | 0.67 | **10.24** |
| tanh(x) + 0.5x | 0.767 | high | 0.66 | **9.49** |
| clip(x, 0, 2) | 0.631 | middle | 0.64 | 6.69 |
| bent identity | 0.600 | middle | 0.81 | 0.86 |
| clip(x, 0, 4) | 0.497 | low | 0.56 | **2.01** |
| SiLU | 0.459 | low | 0.82 | **2.09** |
| GELU | 0.450 | low | 0.77 | **2.12** |

Spearman ρ(R², λ) over the nine runs = 0.83.

### Verdicts

| # | Verdict |
|---|---|
| H28.1 | **Held.** Every high-group λ ≥ 7, in the range 9.49–11.62. |
| H28.2 | **Held.** Every low-group λ ≤ 3, in the range 2.01–2.12. |
| H28.3 | **Held.** ρ = 0.83 ≥ 0.7. |

## Findings

**F1. C13 survives a test it could have failed.** It made predictions for nine activations it had never seen, and all three pre-registered hypotheses held. Inside the high group, λ falls in exactly the order of R² (erf > sign·√|x| > tanh + 0.2x > tanh + 0.5x). Adding a linear ramp to tanh lowers the tilt as the indicator score falls.

**F2. A dose–response inside one shape.** Clipping ReLU at height c: c = 1 gives λ = 10.47 (Spike 24), c = 2 gives 6.69, c = 4 gives 2.01. The function class and the threshold are the same in all three; only how far the unit's output tracks *distance* rather than *side* changes. This is the cleanest single piece of evidence for C13.

**F3. Where C13 is weakest.** The middle zone (R² 0.6–0.65) is not decided by R² alone. Clip(0, 2) at 0.63 has λ = 6.7, while bent identity at 0.60 has λ = 0.9. Bent identity is never flat: it is graded on both sides, while clip is flat above c. A sharper predictor probably needs the distribution of pre-activations *after* training, which grows with weight norm, rather than the fixed N(0, 4) used here. That is the next refinement; no claim is made about it yet.

**F4. Tally across the activation programme (24 activations, Spikes 22, 24, 27, 28).** Refuted: unit movement (C10), oddness, saturation (C11), homogeneity (C12). Surviving, now including a prospective test: indicator alignment (C13).
