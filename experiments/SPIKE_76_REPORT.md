# Spike 76: Is predictive energy a variational principle? Width, noise and acquisition-order interventions

**Date:** 2026-11-18 · **Status:** pre-registered (predictions in `results/spike76_predictions.json`, committed with this report before any run) · **Follows:** Spike 75 (P209, P210: closure and the energy law hold across adaptive substrates) and the unifying picture in `charter/FOUNDATIONS.md` §15.

## The picture under test

A working representation is a truncated realisation of the system's predictive (Hankel) operator H:
- it discards ker H (closure);
- it keeps H's singular directions in order of singular value (energy).

Equivalently, it is a point on the solution path of a predictive information bottleneck. The theory predicts the effect of *interventions*, not just correlations:

1. **Width (Eckart–Young).** Limit the state to r dimensions: the learner keeps the top-energy constituents that fit.
2. **Noise (a cost on memory).** Inject Gaussian noise into the state at every step. That is a cost on retained information, the bottleneck trade-off parameter. Constituents should be pruned from the lowest energy up, so the surviving set is always a top-k prefix of the energy order.
3. **Acquisition order.** Unconstrained learners acquire the top-energy constituent first, as in the linear theory, where the time to learn a mode is ∝ 1/singular value (Saxe et al.).

## Automata and energy orders (computed before training)

| Automaton | Energy order (share of the predictive kernel) |
|---|---|
| Z9_s1_014 | r0 0.55 > r2 (k = 3) 0.33 > r1 0.10 > r3 0.01 |
| Z10_s1_014 | r4 0.61 > r1 0.19 ≈ r0 0.16 > others |
| S4_12 | std 0.67 > std⊗sign 0.17 = χ₂ 0.17 |

The second and third Z10 constituents (0.19, 0.16) are nearly tied, so the width-4 prediction for Z10 is fragile; it is registered anyway.

## Design

**Learners.**
- GRU-cell recurrent network (embedding 16), Adam with lr 0.003 cosine to 0, 6,000 steps, length 30, batch 64.
- The ES arm uses the same network trained by evolution strategies, as in Spike 75.

| Arm | Configurations | Prediction |
|---|---|---|
| **W** (width) | Z9 width 2 and 4; Z10 width 2 and 4; S4_12 width 3 (GRU, 5 seeds); Z9 and Z10 width 2 (ES, 3 seeds) | the k largest learned shares are the k top-energy constituents: k = width/2 for the cyclic cases (2-dim real irreducibles), k = 1 for S4_12 width 3 |
| **N** (noise) | all three automata, width 64, state noise η ∈ {0, 0.3, 1.0} (GRU, 5 seeds) | the present set (share ≥ 0.15) is a top-k prefix of the energy order at every η, and shrinks as η grows |
| **T** (acquisition) | the η = 0 runs, with geometry recorded every 100 steps to step 3,000, then every 500 | the top-energy constituent reaches half its final share first |

**Measure.** Isotypic shares of the double-centred, normalised centroid Gram on 400 strings, steps 5–29, as in Spikes 71–75.

**Fit guards.** No fit guard for arms W and N: a constrained learner is expected to fit imperfectly, and the theory concerns which subspace it keeps. Fit is reported. Arm T uses fitted runs only (≥ 0.99 at length 100).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H76.1 | **Width keeps the top of the energy order** (GRU) | correct top-k set in ≥ 80% of runs | < 50% |
| H76.2 | **Noise prunes from the bottom** (GRU) | present set is an energy prefix in ≥ 80% of runs **and** the count present is non-increasing in η in ≥ 80% of seed sweeps | prefix in < 50% |
| H76.3 | **The top-energy constituent is acquired first** (GRU, η = 0, fitted) | ≥ 80% of runs (needs ≥ 5) | < 50% |
| H76.4 | Width keeps the top constituent without gradients (ES, width 2) | ≥ 80% of runs | < 50% |

Anything else is *neither*.

## What this cannot show

- One family of recurrent learners.
- Noise in the state is one implementation of a memory cost. Weight decay or an explicit information penalty may behave differently.
- "Present" uses a fixed share threshold (0.15).

## Commands

```
python -m experiments.spike76 predict
python -m experiments.spike76 run
python -m experiments.spike76 analyse
```
