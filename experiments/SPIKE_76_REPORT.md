# Spike 76: Is predictive energy a variational principle? Width, noise and acquisition-order interventions

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in e352fc3; results below) · **Follows:** Spike 75 (P209, P210: closure and the energy law hold across adaptive substrates) and the unifying picture in `charter/FOUNDATIONS.md` §15.

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

**Bug fix before any verdict (2026-11-18).** `spike76.py` sampled strings through Spike 75's `sample`, which looks automata up in Spike 75's table only. Every Z10_s1_014 and S4_12 run that was not in that table crashed before producing any output. No recorded value changed. The fix routes Spike 75's lookup through this spike's `spec`. The 25 runs completed before the fix (all on Z9_s1_014, which is in both tables) are unaffected.

## Results

`experiments/results/spike76.json`; per-run outputs in `spike76_raw/`. All 76 runs completed (GRU 70, ES 6). Fits: constrained runs fit imperfectly, as expected (width 2: 0.63–0.74; η = 1.0: 0.71–0.92). Unconstrained (η = 0) runs: 14 of 15 fitted.

| Arm | Automaton | Energy prediction | What the learners kept (leader, all runs) |
|---|---|---|---|
| W width 2 | Z9 | r0 | **k = 1 (r1, smoothest faithful) 3/5**, r3 1/5, mixed 1/5 |
| W width 4 | Z9 | {r0, r2} | r2 3/5, k = 1 1/5, r0 1/5 |
| W width 2 | Z10 | r4 | **k = 1 (r0, smoothest) 4/5**, k = 5 1/5 |
| W width 4 | Z10 | {r4, r1} | r4 3/5, r0 1/5, r1 1/5 |
| W width 3 | S4_12 | std | **std 5/5** |
| N η = 0 | Z9 / Z10 / S4_12 | r0 / r4 / std | Z9: r0 3/5 (lottery); Z10: r0 3/5, r4 2/5; S4_12: std 5/5 |
| N η = 0.3 | Z9 / Z10 / S4_12 | — | Z9: r0 4/5; Z10: r4 3/5; S4_12: std 4/5 |
| N η = 1.0 | Z9 / Z10 / S4_12 | — | **Z9: k = 1 5/5; Z10: k = 1 5/5**; S4_12: std 5/5 |
| ES width 2 | Z9 / Z10 | r0 / r4 | Z9: r0 1/3, k = 1 2/3; Z10: r4 1/3, others 2/3 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H76.1 | correct top-k set in 28% of GRU width runs (S4_12 5/5; cyclic 2/20) | ≥ 80% held, < 50% broken | **BROKEN** |
| H76.2 | present set is an energy prefix in 47%; count monotone in η in 40% | prefix ≥ 80% and monotone ≥ 80% held; prefix < 50% broken | **BROKEN** |
| H76.3 | top-energy constituent acquired first in 1/14 fitted runs | ≥ 80% held, < 50% broken | **BROKEN** |
| H76.4 | ES width 2 keeps the top-energy constituent in 2/6 | ≥ 80% held, < 50% broken | **BROKEN** |

**Reading:**
- **Predictive energy is not a variational principle for these learners.** None of the three interventions acts as the truncated-realisation / information-bottleneck picture predicts:
  - squeezing the state does not keep the top-energy constituents;
  - memory noise does not prune from the bottom;
  - the top-energy constituent is not learned first.

  The picture of `charter/FOUNDATIONS.md` §15, where energy is the variational principle, is **refuted** for nonlinear recurrent learners on discrete systems. This is the regime the linear-Gaussian theorems do not cover, and here they do not extend.
- **Under pressure, cyclic learners fall back to the smooth circle.** With width 2 or heavy state noise, ℤ/9 and ℤ/10 networks lead with the k = ±1 character (energy shares only 0.10 and 0.16). That character is the one on which the letter +1 acts as the *smallest rotation*. With η = 1.0 this happens in 10/10 runs.

  In S₄ on 12 cosets the energetic constituent (std) leads under every intervention (width 3: 5/5; η = 1.0: 5/5). The candidate constituents there are equally "smooth": each letter acts with the same character-average.

**Exploratory synthesis (post hoc), conjecture C42: value against implementation cost.** The learned constituent maximises predictive value (energy) minus an implementation cost. The cost grows with how far the letters' actions are from the identity in that representation: the rotation angle per step, for cyclic groups. Constraints such as fewer dimensions or noisier state raise the effective price of rough actions, so learners trade predictive energy for smoothness.

This one trade-off is consistent with:
- the cyclic "circle pull" (Spikes 69, 71, 73);
- the lotteries where value and cost nearly balance (Spike 74);
- the persistence of the energy law where costs are equal (S₄, A₄);
- possibly the double cover (C36). A small rotation acts on degree 1 with a generator of norm 1, and on degree 2 with norm up to 2, so the cover is the cheaper realisation.

It replaces "energy as the variational principle" with "energy as the value term". The cost term is the new and untested part. It must be registered with a quantitative cost (e.g. Σ_a ‖ρ(a) − I‖²) and a stated trade-off before it counts.
