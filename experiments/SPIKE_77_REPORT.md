# Spike 77: Is there one exchange rate between predictive value and dynamical cost? (C43, prospective)

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in 8550e70; results below) · **Follows:** Spike 76 (P211: energy is not a variational principle; under pressure, learners choose the smoothest letter action). Also follows the post-hoc calibration `experiments/theory/exchange_rate.py` (`results/theory_exchange_rate.json`) and `charter/FOUNDATIONS.md` §15.5 and §16.

## Conjecture C43 (Gibbs selection with one exchange rate)

A learner's leading constituent ρ is drawn with probability

  P(ρ) ∝ e_ρ^α · exp(−λ·c_ρ),

where:
- e_ρ is the constituent's predictive-energy share (value);
- c_ρ = 1 − mean_a P(e, a)/P(e, e) is the mean distance of the letters' actions from the identity in ρ (cost; equal to ‖ρ(a) − I‖²_F/2d averaged over letters);
- **λ/α is the exchange rate** between log-value and cost for a given learner and resource budget.

**Calibration (post hoc, on Spikes 71, 73–76; default GRU condition).** 24 automata, 135 fitted runs. α = 2.49 and λ = 3.68 give:

| Model | Negative log-likelihood |
|---|---|
| Gibbs rule (in sample) | 55 |
| Gibbs rule, leave-one-automaton-out | 58 |
| energy-only | 112 |
| smoothness-only | 161 |
| chance | 184 |

Leave-one-automaton-out, the rule's top pick matches 86% of runs.

**Here α and λ are frozen**, as are the energy-only and smoothness-only rivals' fitted parameters, and the rule is tested on new automata.

## Automata (selected by a fixed rule before any run)

Pool: 282 new automata:
- cyclic ℤ/7, ℤ/8, ℤ/11 and ℤ/12 with letter +s (s ∈ {1, 2, 3} coprime to n) and readouts [c ∈ {0, a, b}];
- dihedral D₅ and D₇ (point and two-point readouts);
- A₄ and S₃ variants.

Names run in Spikes 69–76 are excluded. Selection rule:
1. keep candidates where the Gibbs prediction is confident (p_max ≥ 0.6) and differs from at least one rival's;
2. sample up to 2 per family with seed 77.

This gave **11 automata**:
- Z7_s1_015, Z7_s3_023
- Z8_s3_037, Z8_s3_015
- Z11_s3_045, Z11_s2_012
- Z12_s1_037, Z12_s1_035
- D7_pt
- A4_sub012
- S3_pt

The per-automaton predictions of all three rules are in the predictions file.

## Training

**Default condition.** Spike 71's trainer: GRU 64, Adam lr 0.003 cosine, 6,000 steps, length 30, identity letter, 5 seeds. Fit guard ≥ 0.99 at length 100. The leader is the top isotypic share of the centroid Gram.

**Pressure arm.** State noise η = 1.0 (Spike 76's GRU-cell trainer) on every second automaton, 3 seeds each, with no fit guard.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H77.1 | **The frozen Gibbs rule predicts new automata better than either rival** | predictive negative log-likelihood (fitted default runs) is lower than energy-only's and smoothness-only's | otherwise |
| H77.2 | Its argmax is the observed leader | ≥ 75% of fitted default runs | < 50% |
| H77.3 | **Pressure raises the exchange rate** | λ/α refitted on the η = 1.0 runs exceeds λ/α refitted on the default runs of the same automata | otherwise |

Anything else is *neither*.

**Guards.**
- H77.1 and H77.2 need ≥ 5 automata with ≥ 1 fitted run.
- H77.3 needs ≥ 9 η = 1.0 runs.

## What this cannot show

- One learner family (GRU).
- The cost index is one choice among several. A dissipation-derived cost (Wasserstein speed limits; `charter/FOUNDATIONS.md` §16) would be the principled form.
- α and λ were calibrated on data from the same learner and training recipe, so a held verdict supports C43 for this learner only.

## Commands

```
python -m experiments.spike77 predict
python -m experiments.spike77 run
python -m experiments.spike77 analyse
```

**Bug fix before the H77.3 verdict (2026-11-18).** The pressure arm calls Spike 76's trainer, which looked automata up in Spike 76's own table. All 18 η = 1.0 runs therefore crashed before producing output. The fix also patches `spike76.spec`. The default-condition runs used a different trainer and are unaffected.

## Results

`experiments/results/spike77.json`; per-run outputs in `spike77_raw/`.

**Fits.** Default condition: 51 of 55 runs fitted. All 11 automata qualify. η = 1.0: 18 runs, not fit-guarded (fit 0.6–0.9).

| Automaton | Gibbs (frozen) | Energy | Smooth | Default leaders (fitted) | η = 1.0 leaders |
|---|---|---|---|---|---|
| Z7_s1_015 | r2 | r1 | r2 | **r2 5/5** | r2 3/3 |
| Z7_s3_023 | r0 | r2 | r0 | **r0 5/5** | — |
| Z8_s3_037 | r0 | r0 | r2 | **r0 4/4** | smooth r2 2/3, r3 1/3 |
| Z8_s3_015 | r0 | r0 | r2 | **r0 5/5** | — |
| Z11_s3_045 | r1 | r4 | r2 | **r1 4/4** (neither rival) | smooth r2 3/3 |
| Z11_s2_012 | r0 | r0 | r3 | **r0 5/5** | — |
| Z12_s1_037 | r0 | r0 | r1 | **r0 5/5** | r0 2/3, smooth r1 1/3 |
| Z12_s1_035 | r1 | r4 | r1 | **r1 4/5**, r4 1/5 | — |
| D7_pt | r3 | r1 | r3 | **r3 5/5** | r1 2/3, r3 1/3 |
| A4_sub012 | χ₃ | χ₃ | ω-pair | **χ₃ 5/5** | — |
| S3_pt | std | std | sign | **std 5/5** | std 3/3 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H77.1 | predictive negative log-likelihood: Gibbs **4.4**, energy-only 35.5, smoothness-only 56.7 | Gibbs below both rivals | **HELD** |
| H77.2 | Gibbs argmax = observed leader in **50/51** fitted runs (98%) | ≥ 75% | **HELD** |
| H77.3 | refitted exchange rate λ/α: default 2.8 → η = 1.0 **9.2** | η = 1.0 rate > default rate | **HELD** |

**Reading:**
- **One exchange rate between predictive value and dynamical cost predicts which representation a recurrent learner builds**, prospectively, on automata it was not fitted on. The two parameters were frozen before any run.
  - The rule gets both directions right: the cheap, smooth representation beating the energetic one (ℤ/7, ℤ/12, D₇) and the energetic one beating the smooth one (ℤ/8, ℤ/11 with letter +2, A₄, S₃).
  - In Z11_s3_045 it predicts a constituent that *neither* rival predicts (r1), and the networks build it in 4/4 runs.
  - Its error is 8× lower than energy alone and 13× lower than smoothness alone.
- **Pressure moves the exchange rate, as a temperature would.** Under heavy state noise the refitted rate rises from 2.8 to 9.2: dynamical cost weighs more. Two automata flip to the smooth constituent: Z8 2/3, Z11 3/3.

  One automaton moves the other way (D7: from the smooth r3 toward r1 2/3), so the shift is not uniform. With 3 seeds per automaton this is a weak, directional result.
- **Limits:**
  - One learner family (GRU), whose parameters were calibrated on the same recipe.
  - The cost index is a representation-theoretic proxy; a dissipation-derived cost (Wasserstein speed limit, `charter/FOUNDATIONS.md` §16.1) is the principled form, still to be derived.
  - The other substrates (evolution strategies, spectral, reservoir) have not been tested against the rule.
