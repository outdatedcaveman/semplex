# Spike 27: Is positive homogeneity what removes the tilt? (C12)

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 24 F3 (post hoc: the only activations without the information tilt, ReLU and leaky ReLU, are exactly the positively homogeneous ones)

## Conjecture C12

The information tilt λ (unit-level law P(t | g) ∝ Ω(t)^γ · exp(λ·I(t; g))) is suppressed when the activation is positively homogeneous, φ(cx) = c^k·φ(x) for c > 0. The proposed cause is the per-unit rescaling symmetry (w₁, b₁, w₂) → (c·w₁, c·b₁, c^(−k)·w₂). It lets gradient trade hyperplane sharpness against readout weight, and it couples the two through a conserved balance.

## Design (as Spikes 22 and 24: 128 elements × 40 seeds, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps; fresh seeds)

| Run | Activation | Homogeneous? |
|---|---|---|
| abs | \|x\| (even, degree 1) | yes |
| relu² | max(x, 0)² (degree 2) | yes |
| signed square | x·\|x\| (odd, degree 2) | yes |
| softplus | log(1 + eˣ) (grows linearly) | no |
| ELU | x for x > 0, eˣ − 1 otherwise (linear on the positive side) | no |
| **ReLU-sphere** (intervention) | ReLU, but after every step each unit's (w₁, b₁) is rescaled to its initial norm. This removes the rescaling freedom without changing the function class | ReLU, symmetry removed |

Fit (γ, λ) at step 3,000 with the exact fitter. Runs fitting < 90% of nets are flagged.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H27.1 | Homogeneous activations lack the tilt | λ ≤ 3 for abs, relu² and signed square | any > 5 |
| H27.2 | Non-homogeneous activations have it, even with linear growth | λ ≥ 5 for softplus and ELU | any < 3 |
| H27.3 | **Removing ReLU's rescaling symmetry restores the tilt (causal test)** | λ(ReLU-sphere) ≥ 5 | ≤ 3 |
