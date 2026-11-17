# Spike 70: Direction versus axis, with a passable guard: does a network lift to the double cover? (C36)

**Date:** 2026-11-17 · **Status:** pre-registered (this report committed before any registered run) · **Follows:** Spike 65, which gave no verdict because its fit guard (R² ≥ 0.95 at length 100, with σ = 0.3) could not be met. Its exploratory finding was that axis-trackers kept the signed direction, the double cover S² → RP², instead of the minimal quotient RP². **Conjecture:** C36 (linearising cover): a network represents the simplest *linear* representation of the dynamics from which the output can be computed, even when a smaller quotient would suffice.

## Changes from Spike 65 (fixed before any registered run)

- Rotation noise is σ = 0.15, down from 0.3.
- The fit guard is R² ≥ 0.90 on 500 sequences at the **training length 30**. Length-40 R² is also reported.
- Measurements use 500 sequences of length 40, steps 5–39.
- The swap intervention is at t ∈ [5, 18], followed by 20 continued inputs.
- A **sign probe** is added: a logistic probe for the sign of u_z, on states with |u_z| ≥ 0.3, trained on half and tested on the other half. It reads directly whether the hidden state carries the bit that RP² forgets.

**Guard calibration.** One pilot per readout was run at seed 99, outside the registered range, for 2,000 steps. Only the fits were inspected: SIGN 0.993, AXIS 0.971 at length 30 (0.987 and 0.952 at length 40). So the guard is passable. No geometry values from the pilot were looked at.

Everything else is as in Spike 65:
- **Task:** a body axis is rotated by random small rotations, which are the network's input.
- **Readouts:**
  - SIGN outputs u (S², degree-1 harmonics);
  - AXIS outputs the traceless projector uuᵀ − I/3 (RP², degree 2).
- **Model:** GRU with hidden size 64 and a linear head, trained with MSE.
- **Optimiser:** Adam, lr 0.003, cosine schedule over 6,000 steps, batch 64.
- **Seeds:** 5 per readout, seed 7,000 + 10·readout + seed.
- **Measurements:** the harmonic regression R²_ℓ (ℓ = 1, 2, 3), the antipodal ratio, and the antipodal swap.

**Predictions.**
- Minimal quotient for AXIS: RP², with degree-2 geometry and no sign information.
- C36: the double cover, with degree-1 geometry and the sign present, as for SIGN.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H70.1 | **C36, geometry:** AXIS networks are degree-1 (the cover), not degree-2 (the quotient) | R²₁ ≥ 0.2 and R²₁ > R²₂ in ≥ 80% of fitted AXIS runs | R²₂ > R²₁ in ≥ 50% |
| H70.2 | **C36, information:** AXIS networks carry the sign the output forgets | sign probe ≥ 0.9 in ≥ 80% of fitted AXIS runs | sign probe ≤ 0.6 in ≥ 50% |
| H70.3 | **The extra sign is causally inert for AXIS and causal for SIGN** (closure at the level of outputs) | median swap-matches-no-swap: AXIS ≥ 0.9 and SIGN ≤ 0.1 | AXIS ≤ SIGN |
| H70.4 | SIGN control: degree-1 geometry | R²₁ ≥ 0.3 and R²₁ > R²₂ in ≥ 80% of fitted SIGN runs | < 50% |

Anything else is *neither*.

**Guard.** A readout counts only with ≥ 3 fitted seeds. H70.3 needs both readouts.

**Reported without criteria:** the antipodal ratio, R²₃, and fit at length 40.

H70.1 and H70.2 are C36's two signatures. Their negations together would be the minimal quotient (RP²), as Spike 65 originally predicted.

## What this cannot show

- One architecture.
- The harmonic regression is linear: a degree-2 code computed nonlinearly from a degree-1 state shows up as degree 1.
- The sign probe is linear.

## Commands

```
python -m experiments.spike70 run
python -m experiments.spike70 analyse
```
