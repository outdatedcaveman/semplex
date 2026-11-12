# Spike 24: What about tanh makes the information tilt? Oddness versus saturation

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 22 (leaky ReLU does not restore the tilt; C10 refuted)

## Question

Unit-level law: P(unit computes t | g) ∝ Ω(t)^γ · exp(λ·I(t; g)). Tanh gives λ ≈ 11.5; ReLU and leaky ReLU give λ ≈ 0.3–1.2 (Spikes 21–22). Two features distinguish tanh from (leaky) ReLU:

- **Oddness (C11a).** φ(−x) = −φ(x). A unit and its complement give the same feature up to sign, so the unit is a centred ±1 *vote*, and the readout can use either side of the hyperplane.
- **Saturation (C11b).** φ is bounded. In the saturated regime units become indicator functions, so only the function t (not the distance from the hyperplane) reaches the output.

## Design (as Spike 22: 128 elements × 40 seeds, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps; fresh seeds)

| Activation | Odd | Saturating |
|---|---|---|
| tanh | yes | yes |
| hardtanh, clip(x, −1, 1) | yes | yes |
| softsign, x / (1 + \|x\|) | yes | yes (slowly) |
| arcsinh | yes | no |
| sigmoid | no | yes |
| clipped ReLU, clip(x, 0, 1) | no | yes |
| ReLU (Spike 22 run reused) | no | no |

Fit (γ, λ) at step 3,000 with the exact fitter (`cerp/loglin.py`). Fit rates reported; a run fitting < 90% of nets is flagged.

Note: sigmoid(x) = (1 + tanh(x/2))/2, so a sigmoid net computes the same function class as a tanh net, with a different parametrization. If sigmoid lacks the tilt, the tilt belongs to the training dynamics in a given parametrization, not to the function class.

## Hypotheses and kill criteria (C11a and C11b are rivals)

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H24.1 (C11a) | **Oddness makes the tilt** | every odd activation has λ ≥ 5 and every non-odd one λ ≤ 3 | any odd activation has λ < 3, or any non-odd one λ > 5 |
| H24.2 (C11b) | **Saturation makes the tilt** | every saturating activation has λ ≥ 5 and every non-saturating one λ ≤ 3 | any saturating activation has λ < 3, or any non-saturating one λ > 5 |
| H24.3 | Sigmoid behaves like tanh (the tilt is a property of the function class) | λ(sigmoid) ≥ 0.7 × λ(tanh) | λ(sigmoid) ≤ 0.3 × λ(tanh) |
