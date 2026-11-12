# Spike 29: Indicator alignment at the trained scale, and does the tilt help generalization?

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 28 (C13 held prospectively, but the middle zone was unresolved), Spike 20 (the selection law, so far only *descriptive*)

## Two questions

**A. Refining C13.** Spike 28's indicator score R² = corr(φ(x), 1[x > 0])² used a fixed scale, x ~ N(0, 2²). Units actually see their *trained* pre-activations, whose scale grows with the weight norm. Spike 28 F3 suggested that this scale decides the middle zone: clip(0, 2) at R² 0.63 had λ = 6.7, while bent identity at 0.60 had λ = 0.9. Arm A measures R² on the trained pre-activation distribution itself.

**B. Usefulness.** Everything so far says *which* mechanism training picks. It does not yet say whether the information tilt makes networks better. Arm B asks whether activations with a stronger tilt generalize better from partial data on the same atlas.

## Design (all 24 activations of Spikes 22, 24, 27 and 28; width 8; AdamW lr 0.03, wd 0.03; 3,000 steps; fresh seeds 29,000 + i)

- **Arm A.** 128 elements × 10 seeds, full truth tables. At step 3,000, compute
  R²_trained = corr(φ(pre), 1[pre > 0])²,
  pooled over every unit and every input of every net. λ for each activation is taken from Spikes 22, 24, 27 and 28, already measured.
- **Arm B.** 128 elements × 10 seeds. Each net sees 12 of its 16 inputs, a random subset per net (rng seed 29,999). Report accuracy on the 4 held-out inputs, averaged over nets that fit all 12 seen inputs.

**Fixed baseline, computed before any run** (`results/spike29_baseline.json`): over the 24 activations, Spearman ρ(R²_fixed, λ) = **0.832**. ReLU-sphere is excluded because it is the same activation as ReLU.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H29.1 | Trained-scale R² ranks λ better than fixed-scale R² | ρ(R²_trained, λ) ≥ 0.88 | ρ(R²_trained, λ) < 0.832 |
| H29.2 | It orders the middle zone correctly | R²_trained(clip2) > R²_trained(bentid) | R²_trained(clip2) < R²_trained(bentid) |
| H29.3 | The tilt helps generalization: activations with a stronger tilt predict held-out inputs better | ρ(λ, held-out accuracy) ≥ 0.5 | ρ(λ, held-out accuracy) ≤ 0 |
| H29.4 | The effect is large enough to matter | mean held-out accuracy of tilted activations (λ ≥ 7) − untilted (λ ≤ 3) ≥ +0.02 | difference ≤ 0 |

H29.3 and H29.4 are the step from *describing* what training selects to a claim about *performance*. If they are broken, the tilt is a fact about mechanisms that does not translate into better generalization on this atlas. That is a result in its own right.
