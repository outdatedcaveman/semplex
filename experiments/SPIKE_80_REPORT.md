# Spike 80: Three targeted tests of the selection rule: cost form, gradient-free convergence, non-abelian disagreement

**Date:** 2026-11-19 · **Status:** pre-registered (predictions in `results/spike80_predictions.json`, committed with this report before any run) · **Follows:** Spike 79 (P214). That spike left three open items:
- the cost's form (H79.4: chord and geodesic tied, 28.4 vs 28.3);
- gradient-free learners did not converge (H79.2: no verdict);
- the unselected non-abelian sample never separated cost from energy (H79.1: neither).

## (a) Cost form: kinetic (chord²) vs geodesic (angle²)

**Calibration (before any run).** Both forms were fitted on the 112 fitted GRU runs of Spikes 77–79 (default condition):

| Form | α | λ | In-sample NLL |
|---|---|---|---|
| chord (kinetic) | 3.03 | 5.14 | **10.7** |
| geodesic | 2.79 | 1.07 | 19.2 |

On the larger data set the kinetic form already fits much better. That is in-sample, so it calibrates the test here but does not count as one.

**Test automata.** ℤ/n with two letters +a, +b (plus identity) and readouts [c ∈ {0, x, y}]. With two letters, averaging chord² and angle² over the letters can rank characters differently.

Candidates are automata where the two calibrated forms predict different leaders, each with probability ≥ 0.45. The threshold was lowered from 0.6 before any run, because 0.6 gave no candidates. 18 qualified; 8 were sampled with seed 80:

**T9_13_014, T9_23_017, T9_23_023, T9_23_028, T9_23_067, T9_34_026, T9_34_037, T9_34_047.**

In every one, the kinetic form predicts the unfaithful k = ±3 constituent (r2, kernel ℤ/3) and the geodesic form a faithful character.

**Learner.** GRU + Adam (Spike 79 trainer), 5 seeds.

## (b) A gradient-free learner at convergence

Evolution strategies on the same GRU:
- 12,000 iterations (3× Spike 79);
- σ = 0.03, cosine-decayed step size, antithetic population 64, length-30 batches.

Automata: Z7_s1_015 and Z7_s3_023 (Spike 77; Gibbs = smooth ≠ energy) and Z8_s3_015 (Gibbs = energy ≠ smooth). 3 seeds each. The rule's α and λ are frozen from Spike 77.

## (c) Non-abelian automata where the frozen rule and energy disagree

The pool is the dihedral groups D₅–D₈ (rotation + reflection, two reflections, rotation-by-2 + reflection) and the Spike 79 non-dihedral generating sets, with point and subset readouts. Of these, 18 automata have a frozen-rule prediction that differs from the energy-only prediction. **8 were sampled at random (seed 80) from that subpopulation**, with no selection on confidence:

**N_D5r2f_pt, N_D5rf_pt, N_D6ff_pt, N_D7r2f_s026, N_D7r2f_s045, N_D7rf_pt, N_D7rf_s023, N_D7rf_s045.**

GRU + Adam, 3 seeds.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H80.1 | **The kinetic (minimum-dissipation) cost is the right form** | NLL of the calibrated chord rule < NLL of the calibrated geodesic rule on fitted arm-(a) runs (≥ 4 automata) | otherwise |
| H80.2 | A gradient-free learner at convergence follows the frozen rule | argmax accuracy ≥ 75% of fitted ES runs (≥ 2 automata) | < 50% |
| H80.3 | **Cost beats energy in non-abelian groups when they disagree** | frozen-rule argmax accuracy ≥ 70% **and** NLL below energy-only and smoothness-only (≥ 4 automata) | accuracy < 50% |

Anything else is *neither*.

**Fit guard:** ≥ 0.99 at length 100.

## What this cannot show

- Arm (a) uses only ℤ/9 (the only group with confident disagreements).
- Arm (c) is dihedral-dominated.
- ES may still not converge (no verdict).

## Commands

```
python -m experiments.spike80 predict
python -m experiments.spike80 run
python -m experiments.spike80 analyse
```
