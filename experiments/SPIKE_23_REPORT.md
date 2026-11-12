# Spike 23: Does symmetry aim the trajectory, or only proximity? A distance-matched choice test

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 19 H19.1 and its stated confound

## Question

Spike 19 found that, before a unit's threshold function settles, its weights already lie closer to the symmetric subspace of its *eventual* stabilizer (p = 1.5 × 10⁻⁶⁰). Its stated confound: a unit near t's cone is near Fix(Stab(t)) simply because the cone is centred there. This spike removes the confound by looking at *choices*.

## Design

Train 128 elements × 40 seeds, width 8, tanh, AdamW (lr 0.03, wd 0.03), 3,000 steps, fresh seed 23,000. Read every unit's threshold function after **every** step.

- **Event.** A unit's function changes from f to f′ by flipping exactly one input point x, and neither f nor f′ is constant.
- **Choice set.** All points x′ whose flip turns f into a non-constant threshold function: the cones adjacent to the unit's current cone.
- **Covariates per candidate, all measured the step before the event:**
  - d = |w·x′ + b| / ‖w‖, the Euclidean distance from x′ to the unit's hyperplane (static proximity);
  - log Ω(f′), the volume of the cone entered;
  - log |Stab_{G_g}(f′)|, the size of its stabilizer in the task's symmetry group (as in Spike 19);
  - I(f′; g), the mutual information of the new function with the target.
- **Model.** Conditional logit: P(x | event) ∝ exp(−κ·d + a·log Ω + β·log|Stab| + μ·I).
- **Fitting and uncertainty.** Maximum likelihood; 99% intervals from 200 bootstrap resamples of *nets*.

If symmetry only looks predictive because of proximity, β is ≈ 0 once d is in the model.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H23.1 | **Symmetry aims, beyond proximity.** In the model (d, log Ω, log\|Stab\|), β > 0 | 99% interval above 0 | point estimate ≤ 0 |
| H23.2 | **Information aims, beyond proximity and symmetry.** In the full model, μ > 0 | 99% interval above 0 | point estimate ≤ 0 |
| H23.3 | **The symmetry effect is not negligible.** Dropping log\|Stab\| from the (d, log Ω, log\|Stab\|) model costs at least 0.01 bits per event | ≥ 0.01 | < 0.001 |

Reported as well, not pre-registered: whether β survives once I is in the model (i.e. whether the Curie preference at the choice level is distinct from the information preference), and the number of events.
