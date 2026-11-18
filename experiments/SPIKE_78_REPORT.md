# Spike 78: Closing the loopholes of the selection rule (C43)

**Date:** 2026-11-18 · **Status:** pre-registered (predictions in `results/spike78_predictions.json`, committed with this report before any run) · **Follows:** Spike 77 (P212). There, the Gibbs rule P(ρ) ∝ e_ρ^α·exp(−λ c_ρ), with α = 2.49 and λ = 3.68 frozen, predicted 50/51 fitted GRU runs on 11 new automata. **α and λ stay frozen here.**

## Loopholes and how each is closed

| # | Loophole in Spike 77 | Test here |
|---|---|---|
| L1 | One learner family (GRU + Adam) | The same frozen rule on **LSTM + Adam**, **tanh RNN + Adam** and **GRU + SGD** (momentum 0.9, lr 0.1), plus GRU + Adam as control |
| L2 | Automata were *selected* where the rule was confident and disagreed with a rival | A **random sample** of 12 automata from the unused pool (seed 78), with no selection on predictions |
| L3 | Easy cases (all rules agree) inflate accuracy | Accuracy reported separately on the discriminating subset |
| L4 | The cost could be a fixed property of the group, not of the agent's experience | **Letter-frequency arm:** ℤ/n with letters +1, +s and identity, the same readout, only the frequencies changed (0.8/0.1/0.1 vs 0.1/0.8/0.1). Cost and kernel are usage-weighted, so the rule predicts that the leader **flips** in each of 3 automata: F7_2_013, F7_3_013, F11_2_024 |
| L5 | A missing variable (dimension, faithfulness) might be doing the work | On the calibration data (Spikes 71–76), compare leave-one-automaton-out predictive NLL of the 2-parameter rule against a 4-parameter model adding log dimension and faithfulness |
| L6 | The leader depends on a basis-dependent (cosine) geometry | Accuracy of the frozen rule on **whitened** leaders, which are invariant to invertible reparametrisation |

## Predictions (computed before training; full probabilities in the predictions file)

**Random sample.** The pool happens to be mostly cyclic, so all 12 are cyclic:

| Automata | Gibbs vs rivals |
|---|---|
| Z11_s1_019, Z11_s3_035, Z11_s3_039 | all three rules agree |
| Z11_s1_038, Z11_s2_015, Z11_s2_016, Z7_s1_014, Z7_s3_025, Z8_s1_026 | Gibbs = energy ≠ smooth |
| Z11_s3_023, Z12_s1_014, Z12_s1_034 | Gibbs = smooth ≠ energy |

**Frequency arm.** The predicted leader flips:

| Automaton | +1-heavy | +s-heavy |
|---|---|---|
| F7_2_013 | r2 (0.95) | r1 (0.89) |
| F7_3_013 | r2 (0.89) | r0 (0.95) |
| F11_2_024 | r0 (0.87) | r3 (0.99) |

## Training and measurement

- Embedding 16, recurrent width 64, linear head, BCE.
- 6,000 steps, cosine schedule, length 30, batch 64; gradient-norm clip 5.
- 3 seeds per (automaton, learner); 4 seeds per frequency condition (GRU + Adam).
- Fit guard: ≥ 0.99 at length 100.
- The leader is the top isotypic share of the centred, normalised centroid Gram (cosine), with a whitened version.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H78.1 | Unselected automata (GRU + Adam) | argmax accuracy ≥ 75% **and** NLL below both rivals | accuracy < 50% |
| H78.2 | Learner generality with the parameters frozen | NLL(Gibbs) below both rivals for every other learner with ≥ 6 fitted automata | Gibbs worse than a rival for ≥ 2 learners |
| H78.3 | The rule's *form* holds per learner (refitted α, λ; leave-one-automaton-out) | LOO argmax accuracy ≥ 70% for every learner with ≥ 6 fitted automata (at least 3 learners) | any < 50% |
| H78.4 | **Usage-weighted cost: the leader flips with input frequencies** | observed leader = predicted leader in ≥ 80% of frequency-arm runs | < 50% |
| H78.5 | No missing variable | adding log dimension and faithfulness improves calibration LOO NLL by < 10% | ≥ 25% |
| H78.6 | Robust to reparametrisation | frozen-rule accuracy on whitened leaders ≥ 70% (all fitted runs) | < 50% |

Anything else is *neither*. Per-learner exchange rates λ/α are reported.

## What this cannot show

- **Group diversity:** the random sample is all cyclic, because the pool was. Non-abelian generality rests on Spikes 69–77 (A₄, S₃, S₄, D₅–D₇).
- Recurrent learners only. Spike 75's spectral and evolution-strategies substrates are not re-tested against the Gibbs rule.
- The cost index is still a proxy, not derived from dissipation.

## Commands

```
python -m experiments.spike78 predict
python -m experiments.spike78 run
python -m experiments.spike78 analyse
```
