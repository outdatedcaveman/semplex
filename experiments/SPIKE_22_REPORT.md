# Spike 22: Does moving units create the tilt? Leaky ReLU and a movement dose–response (C10)

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 4b4ea69; results below) · **Follows:** Spike 20 (ReLU and selection-only training show no information tilt), Spike 21, conjecture C10

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

---

## Results

Fits with the exact Newton solver (`cerp/loglin.py`). Raw data in `results/spike22_raw/`, fits in `results/spike22.json`.

| Activation | Fit rate | Movement | γ₀ | λ₀ | γ₃₀₀₀ | λ₃₀₀₀ |
|---|---|---|---|---|---|---|
| ReLU (α = 0) | 0.991 | 0.978 | 0.99 | 0.01 | 0.53 | 1.19 |
| leaky, α = 0.01 | 0.999 | 0.992 | 1.00 | −0.05 | 0.51 | 1.08 |
| leaky, α = 0.1 | 1.000 | 0.994 | 1.00 | −0.01 | 0.51 | 0.98 |
| leaky, α = 0.3 | 1.000 | 0.993 | 0.99 | −0.11 | 0.48 | 0.34 |
| tanh | 0.999 | 0.994 | 1.00 | 0.01 | 0.66 | 11.55 |

Spearman ρ(movement, λ₃₀₀₀) = 0.10.

### Verdicts

| # | Verdict |
|---|---|
| H22.1 | **Broken.** λ(α = 0.3) = 0.34 < 2. Leakiness does not restore the tilt; λ *falls* as α grows. |
| H22.2 | **Broken.** ρ = 0.10 ≤ 0.3. |
| H22.3 | **Neither held nor broken**, and the premise fails: 97.8% of ReLU units and 99.4% of tanh units end with a different threshold function than they started with. Every activation moves its units almost completely. |

## Findings

**F1. C10 is refuted.** The tilt is not caused by gradient being able to move units: ReLU units move as much as tanh units, and giving ReLU a gradient on its dead side makes the tilt *smaller*. The tanh tilt (λ ≈ 11.5) is an order of magnitude above every piecewise-linear member of the ReLU family (λ ≤ 1.2).

**F2. The tilt is a property of the activation's shape.** Moving from ReLU toward the identity (α → 1) removes what little tilt there is. Tanh differs from leaky ReLU in two ways: it is odd and it saturates. Spike 24 separates the two.
