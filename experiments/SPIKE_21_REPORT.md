# Spike 21: Where does the information tilt come from? A ratchet test, after "Stuck in a Loop"

**Date:** 2026-11-12 · **Status:** complete (pre-registered in b8d8bed; results below) · **Follows:** Spike 20 (tilt constant across optimizer, weight decay and horizon; absent for ReLU and for selection-only training); C10

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

---

## Results

**Run.** All four variants, 5,120 nets each. Fit rates: tanh-AdamW 1.000, tanh-GD 1.000, tanh-GD-democratized 0.999, ReLU-AdamW 0.990. Raw counts are in `results/spike21_raw/`, fits in `results/spike21.json`.

**A measurement error, found and fixed before any verdict.** The first analysis used Nelder-Mead, started at λ = 0. On 7 of the 28 checkpoints it stalled at a spurious point (λ = 0.075 or 0.002), with negative log-likelihood worse than the optimum by 167 to 40,237 nats. The law is log-linear, so its likelihood is convex. I replaced the fit with an exact Newton solver (`cerp/loglin.py`); both values are stored. The 21 checkpoints where Nelder-Mead had converged agree to three decimals. I also refitted every Spike 20 law fit with the Newton solver (`experiments/refit20_exact.py`, `results/spike20_refit_exact.json`). All 28 agree with the reported values to ±0.001, so Spike 20 stands as published.

### λ (information tilt) and γ (volume exponent) over training

| Step | tanh-AdamW | tanh-GD | tanh-GD-democratized | ReLU-AdamW |
|---|---|---|---|---|
| 0 | −0.08 (γ 1.01) | −0.08 (1.00) | −0.02 (1.00) | −0.06 (1.00) |
| 10 | 4.42 | 2.27 | 3.97 | 0.73 |
| 30 | 8.99 | 5.66 | 7.78 | 2.80 |
| 100 | 10.68 | 8.34 | 9.74 | 1.65 |
| 300 | 11.27 | 9.19 | 10.18 | 1.16 |
| 1,000 | 11.53 | 9.91 | 10.42 | 0.99 |
| 3,000 | 11.56 (γ 0.67) | 10.62 (0.83) | 10.61 (0.85) | 1.13 (0.53) |

### Verdicts

| # | Verdict |
|---|---|
| H21.1 | **Held.** At step 0, \|λ\| ≤ 0.08 and γ ∈ [0.998, 1.006] in every variant. Random initialization is exactly the volume measure. |
| H21.2 | **Held.** λ₁₀₀ / λ₃₀₀₀ = 0.92 (AdamW) and 0.78 (GD). Most of the tilt forms in the first 100 steps. |
| H21.3 | **Broken.** Democratized GD reaches λ₃₀₀₀ = 10.61 against 10.62 for plain GD (ratio 1.00). It is *faster* early (3.97 against 2.27 at step 10). Fit rate 99.9%, so not confounded. |
| H21.4 | **Neither held nor broken.** ReLU's λ peaks at 2.80 at step 30 (above 2, below 4) and settles at 1.13. |

## Findings

**F1. Training starts from pure volume and adds the tilt fast.** At initialization the units follow Ω(t) exactly (γ = 1, λ = 0). That is the "selection" measure of Spike 20 made literal. The information tilt is then *built*: λ rises to 80–90% of its final value within 100 steps, while γ falls (volume matters less as training proceeds). The early lock-in matches the "Stuck in a Loop" picture.

**F2. The early lock-in is not a credit ratchet.** Removing the output-weight factor from every unit's gradient leaves the final tilt unchanged and speeds its onset. So the tilt is not produced by units with large w₂ getting more gradient. The analogy with attention-credit ratcheting fails at this level. Whatever builds the tilt lives in the per-point error signal and the activation, not in the credit multiplier.

**F3. ReLU has a weak, transient tilt.** At the level of all units (not just the determining core of Spike 20), ReLU shows λ ≈ 1–3, peaking early, against 10–12 for tanh. Its volume exponent also falls further (γ ≈ 0.53). Spike 20's "ReLU has no tilt" was measured on cores and holds there; at the unit level the honest statement is "an order of magnitude weaker".
