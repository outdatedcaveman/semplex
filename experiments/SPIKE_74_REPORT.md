# Spike 74: Gated smoothness (C41), prospective

**Date:** 2026-11-18 · **Status:** pre-registered (predictions in `results/spike74_predictions.json`, committed with this report before any run) · **Follows:** Spike 73's exploratory finding (`experiments/theory/gated_smoothness.py`). Gated smoothness fits 46/48 fitted cyclic runs across Spikes 69, 71 and 73 post hoc, with θ ∈ [0.05, 0.10].

## Conjecture C41 (gated smoothness)

Take the constituents whose share of the predictive kernel's isotypic energy is ≥ θ: the *gate*, i.e. the representations present in what must be predicted. Among them, the learned geometry leads with the one that is **smoothest along the letters**: mean P(e, a)/P(e, e) over the non-identity letters a. Ties in smoothness are broken by energy.

θ = 0.08, fixed here before any run. The rival is pure predictive energy (C37): the top share, if ≥ 1.5× the second.

## Automata (all new), with predictions computed before training

Letters are the generator(s) plus the identity letter. The readout is [c ∈ S], or the one-hot of the image of point 0 for the dihedral groups.

| Automaton | Letter(s) | Readout | Energy (C37) | Gated smoothness (C41) | Role |
|---|---|---|---|---|---|
| Z9_s1_014 | +1 | {0, 1, 4} | r0 (0.55, smooth 0.17) | **r1** (0.10, smooth 0.77) | discriminating; gate share near θ |
| Z9_s2_014 | +2 | {0, 1, 4} | r0 (0.55, −0.94) | **r1** (0.10, 0.17) | discriminating |
| Z10_s1_014 | +1 | {0, 1, 4} | r4 (0.61, −0.31) | **r0** (0.16, 0.81) | discriminating |
| Z10_s1_024 | +1 | {0, 2, 4} | k = 5, r2 (0.73, −1.0) | **r0** (0.12, 0.81) | discriminating |
| Z10_s3_026 | +3 | {0, 2, 6} | k = 5, r2 (0.73, −1.0) | **r4** (0.12, 0.81) | discriminating |
| Z7_s1_01 | +1 | {0, 1} | r2 | r2 | agreement |
| Z7_s2_01 | +2 | {0, 1} | r2 (−0.22) | r2: the smoother r1 is absent from the gate | agreement; the gate matters |
| D5_pt | rotation, reflection | one-hot g(0) | tie (0.50 / 0.50) | **r1** (smooth 0.15 vs −0.40) | tie-break |
| D6_pt | rotation, reflection | one-hot g(0) | three-way tie (0.33 each) | **r2** (0.25 vs 0.00, −0.25) | tie-break |

## Training and measurement

As in Spike 71:
- GRU 64, Adam lr 0.003 cosine, 6,000 steps, length 30, batch 64;
- 5 seeds, seed 7,400 + 10·index + seed;
- fit guard ≥ 0.99 at length 100;
- the final leader is the top isotypic share of the centred centroid Gram, with the whitened version reported.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H74.1 | Gated smoothness predicts the final leader (all automata) | ≥ 80% of fitted runs | < 50% |
| H74.2 | **Gated smoothness beats pure energy where they disagree** (the five discriminating cyclic automata) | gated prediction leads in ≥ 80% | energy prediction leads in ≥ 50% |
| H74.3 | Gated smoothness breaks dihedral energy ties | ≥ 80% of fitted D5/D6 runs | < 50% |

Anything else is *neither*.

**Guards.**
- An automaton counts only with ≥ 3 fitted seeds.
- H74.1 needs ≥ 5 qualifying automata, H74.2 ≥ 3, and H74.3 ≥ 1.

## What this cannot show

- Smoothness is defined from the letters' matrix coefficients, an index chosen post hoc in Spike 73. A held verdict supports this index, not a mechanism.
- Cyclic and dihedral groups only.

## Commands

```
python -m experiments.spike74 predict
python -m experiments.spike74 run
python -m experiments.spike74 analyse
```
