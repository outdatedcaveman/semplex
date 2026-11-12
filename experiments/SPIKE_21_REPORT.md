# Spike 21: Where does the information tilt come from? A ratchet test, after "Stuck in a Loop"

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 20 (tilt constant across optimizer, weight decay and horizon; absent for ReLU and for selection-only training); C10

## Inspiration

Eyler et al., "Stuck in a Loop: Runaway credit ratcheting in attention matrices" (Hyperstition, 9 Sept 2026; read in full):
- In attention, every key's gradient carries a factor of its current attention weight, so attention shapes credit, and credit shapes attention: a positive feedback loop.
- Early differences lock in. Within a run, patterns at step 1,000 already resemble step 10,000 more than two runs resemble each other.
- A natural-gradient "democratized" query update (NATQ) widens attention but *worsens* validation loss.

The analogue here is a tanh unit. Its first-layer gradient carries a factor of its output weight w₂ and of its activation slope. A unit whose function already carries information about the target gets a larger w₂, hence more gradient, hence moves further toward informative directions: a ratchet. That would produce an *exponential* tilt in information, fixed early.

## Measurement: the unit-level law over training

For each net, at steps 0, 10, 30, 100, 300, 1,000 and 3,000, take the threshold functions of *all* its units. Fit, per checkpoint and over all 128 elements, the unit-level law

P(unit computes t | g) ∝ Ω(t)^γ · exp(λ·I(t; g)),

over all 940 non-constant threshold functions (up to complement), by maximum likelihood. At step 0 the units are random, so the expected fit is γ ≈ 1, λ ≈ 0.

## Variants (fresh seeds; 128 elements × 40 seeds; width 8; 3,000 steps)

| Variant | Description |
|---|---|
| tanh-AdamW | as in Spike 19 (lr 0.03, wd 0.03) |
| tanh-GD | plain GD, lr 0.3, wd 0.003 |
| **tanh-GD-democratized** | GD in which each unit's first-layer gradient (weights and bias) is divided by \|w₂ₖ\| + 0.05. This removes the output-weight credit factor: the ratchet's multiplier |
| ReLU-AdamW | as Spike 20 |

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H21.1 | The tilt starts at zero: initialization is pure volume | at step 0, \|λ\| < 1 and γ ∈ [0.8, 1.2] in all variants | \|λ\| > 2 in any |
| H21.2 | The tilt locks in early, as a ratchet would: in tanh-AdamW and tanh-GD, λ at step 100 is ≥ 70% of λ at step 3,000 | both | < 40% in both |
| H21.3 | **The credit ratchet drives the tilt:** removing the w₂ factor weakens it | λ₃₀₀₀(democratized) ≤ 0.7 × λ₃₀₀₀(tanh-GD) | ≥ 0.9 × |
| H21.4 | ReLU never develops the tilt | λ(ReLU) < 2 at every checkpoint | > 4 at any checkpoint |

Fit rate is reported for each variant. If democratized GD fits less than 90% of nets, H21.3 is reported as confounded.
