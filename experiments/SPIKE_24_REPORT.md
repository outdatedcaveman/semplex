# Spike 24: What about tanh makes the information tilt? Oddness versus saturation

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 22e7329; results below) · **Follows:** Spike 22 (leaky ReLU does not restore the tilt; C10 refuted)

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

---

## Results

Exact fits (`cerp/loglin.py`); raw data in `results/spike24_raw/`, fits in `results/spike24.json`. ReLU is the Spike 22 run.

| Activation | Odd | Saturating | Fit rate | γ₃₀₀₀ | λ₃₀₀₀ |
|---|---|---|---|---|---|
| tanh | yes | yes | 0.999 | 0.66 | 11.59 |
| hardtanh | yes | yes | 0.997 | 0.92 | 10.71 |
| softsign | yes | yes | 1.000 | 0.51 | 12.11 |
| arcsinh | yes | no | 1.000 | 0.70 | 9.09 |
| sigmoid | no | yes | 0.976 | 0.68 | 12.76 |
| clipped ReLU | no | yes | 0.940 | 0.67 | 10.47 |
| ReLU | no | no | 0.991 | 0.53 | 1.19 |

All fit rates are above the 90% flag.

### Verdicts

| # | Verdict |
|---|---|
| H24.1 (oddness) | **Broken.** Sigmoid (12.76) and clipped ReLU (10.47) are not odd and have λ > 5. |
| H24.2 (saturation) | **Broken.** Arcsinh does not saturate and has λ = 9.09 > 5. |
| H24.3 (sigmoid like tanh) | **Held.** λ(sigmoid) = 1.10 × λ(tanh). |

## Findings

**F1. The tilt is generic; ReLU is the exception.** Six activations of very different shapes give λ between 9 and 13. Only the ReLU family is near zero: ReLU 1.2, and leaky ReLU 0.3–1.1 (Spike 22). Neither oddness nor saturation is needed.

**F2. Clipping ReLU restores the tilt.** Clipped ReLU equals ReLU on [0, 1] and is constant above 1. Bounding the active side moves λ from 1.2 to 10.5. Arcsinh is unbounded but grows logarithmically, and it also has the tilt.

**F3. What the ReLU family uniquely shares is positive homogeneity.** φ(cx) = c·φ(x) for c > 0 holds for ReLU and every leaky ReLU, and for none of the six tilted activations. Homogeneity gives each unit a continuous rescaling symmetry, (w₁, b₁, w₂) → (c·w₁, c·b₁, w₂/c). Under gradient flow this conserves w₂² − ‖(w₁, b₁)‖² (balancedness), so a unit's hyperplane can no longer be sharpened independently of its readout. This is post hoc. It is stated as conjecture C12 and tested in Spike 27.

**F4. The function class does not decide; the parametrization does.** Sigmoid and tanh nets compute the same functions and both have the tilt. ReLU and clipped ReLU nets differ only above 1, and only one has it. So the tilt belongs to the training dynamics.
