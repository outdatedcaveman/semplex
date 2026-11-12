# Spike 23: Does symmetry aim the trajectory, or only proximity? A distance-matched choice test

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 68222d4; results below) · **Follows:** Spike 19 H19.1 and its stated confound

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

---

## Results

Run: fit 99.8%, 331,836 single-point events recorded. 327,586 are analysable: the old and new functions are non-constant and the chosen flip is a valid candidate. On average there are 7.3 candidates per event. 99% intervals come from 200 bootstrap resamples of nets. Data in `results/spike23_raw/events.npz`, fits in `results/spike23.json`.

| Model | κ (−d) | a (log Ω) | β (log \|Stab\|) | μ (I) | bits/event |
|---|---|---|---|---|---|
| d | 40.78 | | | | 0.43712 |
| d + log Ω | 40.79 | −0.04 | | | 0.43697 |
| d + log Ω + log \|Stab\| | 40.72 | −0.12 | **0.49** [0.46, 0.52] | | 0.43375 |
| d + log Ω + I | 40.56 | −0.01 | | 4.15 | 0.42307 |
| full | 40.54 | −0.05 | 0.26 [0.22, 0.29] | **3.90** [3.77, 4.02] | 0.42226 |

### Verdicts

| # | Verdict |
|---|---|
| H23.1 | **Held.** With distance in the model, β = 0.49, 99% interval [0.46, 0.52]. Symmetry aims the trajectory beyond proximity. |
| H23.2 | **Held.** μ = 3.90, 99% interval [3.77, 4.02], above 0 with distance and symmetry in the model. |
| H23.3 | **Neither held nor broken.** Dropping log\|Stab\| costs 0.0032 bits per event: between the 0.001 and 0.01 thresholds. |

## Findings

**F1. Spike 19's confound is resolved: symmetry steers, beyond proximity.** Each single-point flip is compared only against the other flips available at that moment, with each candidate's distance in the model. A unit still prefers to step into the cone with the larger stabilizer, and the effect is far outside sampling error. It survives once information is added (β = 0.26 [0.22, 0.29]), so the Curie preference at the step level is not a relabelled information preference.

**F2. Information steers more strongly.** I(t; g) is the larger effect: a 0.011-bit gain per event against 0.003 for symmetry. Distance dominates everything (κ ≈ 41 per unit of input-space distance): the next flip is nearly always the nearest point. The law's two biases act as small tilts on a proximity-driven walk. That is how they accumulate into Spike 20's strong outcome-level tilt, over the roughly 8 single-point flips each unit makes (331,836 events across 40,960 units).

**F3. Volume plays no part at the step level.** a ≈ 0 in every model. The volume preference of Spikes 19–21 is a property of *where units start* (initialization is exactly the volume measure, Spike 21), not of how they move.
