# Spike 78: Closing the loopholes of the selection rule (C43)

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in 0f3143e; results below) · **Follows:** Spike 77 (P212). There, the Gibbs rule P(ρ) ∝ e_ρ^α·exp(−λ c_ρ), with α = 2.49 and λ = 3.68 frozen, predicted 50/51 fitted GRU runs on 11 new automata. **α and λ stay frozen here.**

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

## Results

`experiments/results/spike78.json`; per-run outputs in `spike78_raw/`. All 168 runs completed. Fitted (≥ 0.99 at length 100):

| Learner | Fitted runs | Automata qualifying |
|---|---|---|
| GRU + Adam | 31/36 | 12 |
| LSTM + Adam | 33/36 | 12 |
| tanh RNN + Adam | 20/36 | 10 |
| GRU + SGD | 13/36 | 7 |
| frequency arm (GRU + Adam) | 24/24 | — |

**Frozen rule, per learner** (random, unselected automata):

| Learner | Argmax accuracy | On discriminating cases | NLL Gibbs / energy / smooth | LOO accuracy (refitted) | Exchange rate λ/α (refitted) |
|---|---|---|---|---|---|
| GRU + Adam | **93.5%** | 91.3% | **5.5** / 20.5 / 42.3 | 87% | 1.89 |
| LSTM + Adam | **93.9%** | 91.7% | **4.5** / 21.3 / 46.1 | 100% | 1.90 |
| tanh RNN + Adam | **85.0%** | 78.6% | **12.5** / 14.6 / 26.5 | 85% | 2.24 |
| GRU + SGD | **76.9%** | 70.0% | **9.6** / 15.3 / 12.5 | 77% | 3.30 |

**Frequency arm** (predicted leader under +1-heavy / +s-heavy letters; observed in 4 runs each):

| Automaton | Predicted | Observed +1-heavy | Observed +s-heavy | Flip? |
|---|---|---|---|---|
| F7_2_013 | r2 → r1 | r2 4/4 ✓ | r2 3/4, r1 1/4 | no (1/4) |
| F7_3_013 | r2 → r0 | **r1 4/4** ✗ | r0 3/4 ✓ | partly |
| F11_2_024 | r0 → r3 | r0 4/4 ✓ | **r0 4/4** ✗ | no |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H78.1 | GRU + Adam on unselected automata: accuracy 93.5%; NLL 5.5 < 20.5, 42.3 | ≥ 75% and below both rivals | **HELD** |
| H78.2 | frozen rule beats both rivals' NLL for LSTM, tanh RNN and GRU + SGD (3/3) | all | **HELD** |
| H78.3 | per-learner LOO accuracy: 87%, 100%, 85%, 77% (minimum 77%) | ≥ 70% for every learner | **HELD** |
| H78.4 | frequency arm: observed = predicted leader in 12/24 (50%) | ≥ 80% held, < 50% broken | **NEITHER** |
| H78.5 | adding log dimension and faithfulness *worsens* calibration LOO NLL (−9.6%) | improvement < 10% | **HELD** |
| H78.6 | frozen rule on whitened leaders: 93.8% | ≥ 70% | **HELD** |

**Reading:**
- **The rule survives five of the six loophole tests.**
  - It predicts **randomly drawn** automata (93.5%) as well as the selected ones of Spike 77, including the cases where the rules disagree (91%).
  - With its parameters frozen from GRU + Adam, it beats both rivals for **LSTMs, tanh RNNs and GRUs trained by SGD**.
  - Refitted per learner, its form predicts held-out automata at 77–100%.
  - No missing variable: dimension and faithfulness add nothing (they make out-of-sample prediction worse).
  - It holds on the reparametrisation-invariant geometry (94%).
- **Each learner has its own exchange rate:** GRU and LSTM with Adam ≈ 1.9, tanh RNN 2.2, GRU with plain SGD 3.3. Learners that are harder to train (no adaptive optimiser, no gating) weigh dynamical cost more. This matches Spike 77, where noise raised the rate. **The exchange rate is a property of the learner, i.e. of the agent, and the rule's form is shared.** This is the measurable part of the "agent-relative value" picture.
- **The cost is not usage-weighted as modelled** (H78.4 neither, 50%).
  - Re-weighting input frequencies changed the leader in only one of three automata as predicted (F7_3_013, +s-heavy).
  - F11_2_024 kept its +1-smooth character even when +2 letters were 8× more frequent.
  - F7_3_013 under +1-heavy input led with a constituent no rule predicted.

  So the cost term depends on *which actions the agent has* more than on *how often it uses them*, at least over this range of frequencies. The agent-relativity of cost is therefore structural (the repertoire of actions), not experiential (their usage statistics). That is a substantive constraint on the enactive reading, and this part of C43 must be revised. A frequency-independent cost (mean over the letter set) is what Spikes 77–78 support.

**Status of C43 after the loophole tests:**
- **Supported:** the form value^α·exp(−λ·cost), with predictive energy as value and the action-distance of the letter set as cost:
  - across four recurrent learners and two optimisers;
  - on unselected automata;
  - in an invariant geometry;
  - with per-learner exchange rates that order sensibly.
- **Not supported:** usage-weighting of the cost.
- **Still open:**
  - non-recurrent and non-gradient substrates;
  - non-abelian groups in an unselected sample;
  - a derivation of the cost from first principles.
