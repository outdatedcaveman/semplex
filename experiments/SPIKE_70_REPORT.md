# Spike 70: Direction versus axis, with a passable guard: does a network lift to the double cover? (C36)

**Date:** 2026-11-17 · **Status:** complete (pre-registered in 9f126ec; results below) · **Follows:** Spike 65, which gave no verdict because its fit guard (R² ≥ 0.95 at length 100, with σ = 0.3) could not be met. Its exploratory finding was that axis-trackers kept the signed direction, the double cover S² → RP², instead of the minimal quotient RP². **Conjecture:** C36 (linearising cover): a network represents the simplest *linear* representation of the dynamics from which the output can be computed, even when a smaller quotient would suffice.

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

## Results

`experiments/results/spike70.json`; per-run outputs in `spike70_raw/`. All 10 runs pass the guard: SIGN 0.998–0.999 and AXIS 0.992–0.994 at length 30; at length 40, ≥ 0.985.

| Readout | Seed | Fit R² (30) | Fit R² (40) | R²₁ | R²₂ | R²₃ | Sign probe | Antipodal ratio | Swap = no-swap |
|---|---|---|---|---|---|---|---|---|---|
| SIGN | 7000 | 0.999 | 0.997 | 0.74 | 0.35 | 0.09 | 1.000 | 1.54 | 0.00 |
| SIGN | 7001 | 0.999 | 0.998 | 0.73 | 0.33 | 0.07 | 1.000 | 1.57 | 0.00 |
| SIGN | 7002 | 0.999 | 0.997 | 0.70 | 0.29 | 0.07 | 1.000 | 1.49 | 0.00 |
| SIGN | 7003 | 0.999 | 0.998 | 0.72 | 0.38 | 0.09 | 1.000 | 1.55 | 0.00 |
| SIGN | 7004 | 0.998 | 0.998 | 0.73 | 0.38 | 0.08 | 1.000 | 1.63 | 0.00 |
| AXIS | 7010 | 0.994 | 0.988 | 0.73 | 0.39 | 0.11 | 1.000 | 1.50 | 0.03 |
| AXIS | 7011 | 0.993 | 0.985 | 0.73 | 0.38 | 0.09 | 1.000 | 1.50 | 0.05 |
| AXIS | 7012 | 0.992 | 0.987 | 0.74 | 0.40 | 0.11 | 1.000 | 1.54 | 0.04 |
| AXIS | 7013 | 0.992 | 0.987 | 0.75 | 0.40 | 0.11 | 1.000 | 1.48 | 0.04 |
| AXIS | 7014 | 0.994 | 0.988 | 0.74 | 0.44 | 0.12 | 1.000 | 1.54 | 0.04 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H70.1 | AXIS: R²₁ ≥ 0.2 and R²₁ > R²₂ in 5/5 (R²₁ 0.73–0.75, R²₂ 0.38–0.44) | ≥ 80% | **HELD** |
| H70.2 | AXIS sign probe ≥ 0.9 in 5/5 (all 1.000) | ≥ 80% | **HELD** (see the design flaw below) |
| H70.3 | median swap = no-swap: AXIS 0.04, SIGN 0.00 | AXIS ≥ 0.9 and SIGN ≤ 0.1 held; AXIS ≤ SIGN broken | **NEITHER** (the criterion is uninformative here; see below) |
| H70.4 | SIGN: R²₁ ≥ 0.3 and R²₁ > R²₂ in 5/5 | ≥ 80% | **HELD** |

**Two design flaws, recorded.**

1. **The sign probe was not class-balanced.** With σ = 0.15 and start at e_z, only about 4% of the states with |u_z| ≥ 0.3 are southern, so majority-class chance is about 0.96 and the threshold of 0.9 is below chance. In the exploratory control below, the *balanced* accuracy is 1.000 in all 4 retrained runs, so the conclusion stands. But H70.2's criterion did not test it.
2. **The H70.3 criterion is uninformative at low noise.** It requires R² ≥ 0.9 over the 20-step window, but the outputs vary little across that window (about 0.67 rad of rotation). So even a 0.1 rad donor mismatch fails it.

A related limitation: the states cover the sphere unevenly (median 43° from e_z, 99th percentile 124°). So the harmonic features are not orthogonal, which is why R²₂ ≈ 0.35 even for SIGN. The *comparison* between AXIS and SIGN is unaffected. Their geometries are indistinguishable.

**Exploratory control, after the verdicts** (`experiments/spike70_control.py`, `results/spike70_control.json`). Seeds 0–1 of each readout were retrained with the same seeds. The output MSE against the no-swap truth was compared after an antipodal swap and after a same-state swap (donor within 0.1 rad of u):

| Readout | Seed | MSE antipodal swap | MSE same-state swap | Ratio | Balanced sign probe |
|---|---|---|---|---|---|
| SIGN | 7000 | 1.27 | 0.0010 | 1,303 | 1.000 |
| SIGN | 7001 | 1.27 | 0.0008 | 1,587 | 1.000 |
| AXIS | 7010 | 0.055 | 0.0011 | 50 | 1.000 |
| AXIS | 7011 | 0.065 | 0.0012 | 57 | 1.000 |

**Reading:**
- **C36 (linearising cover) is supported, now with a fit guard the networks pass.** Networks trained to output only the axis uuᵀ represent the *signed direction*:
  - the degree-1 geometry is identical to the networks trained on the sign itself (R²₁ 0.74 vs 0.73);
  - the sign is perfectly decodable (balanced accuracy 1.0);
  - antipodal states are as far apart as random pairs (ratio 1.50 vs 1.55).

  They do not build the minimal quotient RP². The Myhill–Nerode state of the task is RP², and the networks build its double cover S², where SO(3) acts by its smallest faithful linear representation.
- **The extra bit is mostly but not fully inert.** Writing the antipodal state into an AXIS network costs 20× less output error than in a SIGN network, but 50× more than a same-state swap. The confound is that antipodal donors come from rarely visited, far-diffused regions. So the residual may be tracking error there, not causal use of the sign. This is unresolved.
- **The discrete and continuous results disagree in kind.** In discrete automata, closure discards what the readout cannot see: the 2-part of ℤ/6 read mod 3 (Spike 66) and the unobservable group parts (Spikes 57–58). Here a continuous network keeps a bit the readout cannot see, because dropping it would make the dynamics non-linear.

  A candidate reconciliation, not tested: networks build the *coarsest quotient on which the dynamics act linearly at small dimension*. For ℤ/6 mod 3, ℤ/3 acts linearly on its own circle, so the 2-part can go. For the axis, RP² admits no 3-dimensional linear SO(3) action (its smallest equivariant linear embedding is 5-dimensional), so the network keeps S² ⊂ ℝ³.
