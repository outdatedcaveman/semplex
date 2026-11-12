# Spike 22: Does moving units create the tilt? Leaky ReLU and a movement dose–response (C10)

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 20 (ReLU and selection-only training show no information tilt), Spike 21, conjecture C10

## Question

Spike 20 found that tanh nets choose units with P(t | g) ∝ Ω(t)^γ · exp(λ·I(t; g)), λ ≈ 9–10, while ReLU nets and frozen-first-layer nets show λ ≈ 0. C10 says the tilt exists because gradient *moves* units' hyperplanes toward informative directions, and ReLU blocks this with its dead side. If so, giving ReLU a leaky slope α should restore the tilt, in proportion to how much the units move.

## Design (fresh seeds; 128 elements × 40 seeds; width 8; AdamW lr 0.03, wd 0.03; 3,000 steps)

Activations: ReLU (α = 0), leaky ReLU with α ∈ {0.01, 0.1, 0.3}, and tanh. Five runs.

For each run:
- **Tilt.** Fit (γ, λ) of the unit-level law at step 0 and step 3,000, over all 940 non-constant threshold functions up to complement, by maximum likelihood (the Spike 21 fit).
- **Movement.** The fraction of all units (net × unit index) whose threshold function, up to complement, differs between step 0 and step 3,000.
- **Fit rate.** Fraction of nets that compute their target.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H22.1 | **Leakiness restores the tilt.** λ₃₀₀₀ rises with α | λ(α=0.3) ≥ 4 and λ(0.3) > λ(0.1) > λ(0.01) | λ(0.3) < 2 |
| H22.2 | **Tilt follows movement (C10 core).** Across the five runs, λ₃₀₀₀ increases with movement | Spearman ρ(movement, λ₃₀₀₀) ≥ 0.9 (i.e. same order, at most one swap) | ρ ≤ 0.3 |
| H22.3 | ReLU's units move less than tanh's | movement(ReLU) < 0.5 × movement(tanh) | movement(ReLU) ≥ movement(tanh) |

If any leaky run fits fewer than 90% of nets, its λ is reported but flagged. Spearman over five points is coarse; it is used only for ordering.
