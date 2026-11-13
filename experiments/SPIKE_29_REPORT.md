# Spike 29: Indicator alignment at the trained scale, and does the tilt help generalization?

**Date:** 2026-11-12 · **Status:** complete (pre-registered in bf6a49a; results below) · **Follows:** Spike 28 (C13 held prospectively, but the middle zone was unresolved), Spike 20 (the selection law, so far only *descriptive*)

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

---

## Results

All 24 activations; 1,280 nets per arm per activation. Arm B fit rates ≥ 96.9%. Raw data in `results/spike29_raw/`, analysis in `results/spike29.json`. Chance on a held-out input is 0.5.

| Activation | λ | R²_fixed | R²_trained | Held-out accuracy |
|---|---|---|---|---|
| sigmoid | 12.76 | 0.785 | 0.941 | 0.557 |
| softsign | 12.10 | 0.864 | 0.922 | 0.545 |
| erf | 11.61 | 0.882 | 0.941 | 0.554 |
| tanh | 11.55 | 0.868 | 0.935 | 0.554 |
| sign·√\|x\| | 10.97 | 0.848 | 0.787 | 0.538 |
| hardtanh | 10.71 | 0.875 | 0.934 | 0.555 |
| clip(0, 1) | 10.47 | 0.779 | 0.824 | 0.562 |
| tanh + 0.2x | 10.24 | 0.818 | 0.848 | 0.558 |
| tanh + 0.5x | 9.49 | 0.767 | 0.764 | 0.550 |
| arcsinh | 9.09 | 0.766 | 0.785 | 0.550 |
| clip(0, 2) | 6.69 | 0.631 | 0.637 | 0.560 |
| ELU | 5.95 | 0.627 | 0.470 | 0.568 |
| x·\|x\| | 2.83 | 0.333 | 0.228 | 0.535 |
| GELU | 2.12 | 0.450 | 0.348 | 0.572 |
| SiLU | 2.09 | 0.459 | 0.341 | 0.572 |
| clip(0, 4) | 2.01 | 0.497 | 0.451 | 0.572 |
| softplus | 2.01 | 0.536 | 0.329 | 0.568 |
| ReLU | 1.19 | 0.469 | 0.350 | 0.572 |
| leaky 0.01 | 1.08 | 0.474 | 0.347 | 0.573 |
| leaky 0.1 | 0.98 | 0.514 | 0.375 | 0.571 |
| bent identity | 0.86 | 0.600 | 0.415 | 0.565 |
| ReLU² | 0.43 | 0.201 | 0.143 | 0.558 |
| leaky 0.3 | 0.34 | 0.578 | 0.430 | 0.568 |
| \|x\| | −1.89 | 0.000 | 0.000 | **0.580** |

- ρ(R²_trained, λ) = 0.856 (fixed baseline 0.832).
- ρ(λ, held-out accuracy) = **−0.694**.
- Held-out accuracy, tilted (λ ≥ 7, n = 10) minus untilted (λ ≤ 3, n = 12): **−0.015**.

### Verdicts

| # | Verdict |
|---|---|
| H29.1 | **Neither held nor broken.** ρ = 0.856: above the fixed baseline, below 0.88. |
| H29.2 | **Held.** R²_trained: clip(0, 2) 0.637 > bent identity 0.415. |
| H29.3 | **Broken, with the opposite sign.** ρ(λ, held-out accuracy) = −0.69. |
| H29.4 | **Broken.** Tilted activations are 1.5 points *worse*. |

## Findings

**F1. The trained scale settles C13's middle zone, and helps only a little elsewhere.** Bent identity, never flat, spreads its trained pre-activations across its graded range (R² falls from 0.60 to 0.42). Clip(0, 2) keeps its plateau (0.63 → 0.64). Overall ρ improves from 0.83 to 0.86. C13 stands, now with the measurement taken where units actually operate.

**F2. The information tilt does not buy generalization on this atlas; it costs some.** Across 24 activations, the stronger the tilt, the worse held-out accuracy (ρ = −0.69). Every tilted activation sits between 0.538 and 0.562. Most untilted ones sit between 0.565 and 0.580, the exceptions being ReLU² (0.558) and x·|x| (0.535). The effect is small in absolute terms, because generalizing four unseen bits of a 4-input function from twelve is hard for every activation. It is consistent across shapes, though, and opposite to what the pre-registration expected.

**F3. A reading, stated as a conjecture to test (C14), not a result.** An indicator-like unit commits to a hard partition chosen for its information about the *seen* labels. That makes mechanisms crisp, but it is a bet on the training points. A graded unit keeps distance information, so it behaves more like a similarity kernel, and kernel-like interpolation is what predicts unseen Boolean inputs best here. If so, the tilt trades **generalization for mechanistic crispness**: the same selection that gives clean, readable threshold circuits (Spikes 11–28) costs held-out accuracy. That is a testable *interpretability–generalization trade-off*. The next spike should measure both on the same nets: circuit faithfulness under hardening, and held-out accuracy.

**F4. What this does to the programme's claims.** The selection law (volume × information tilt × symmetry) remains a strong *descriptive* law of which mechanisms training builds. It is not, on this evidence, an account of why training generalizes. Any paper must say so plainly.
