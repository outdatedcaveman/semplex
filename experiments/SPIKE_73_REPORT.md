# Spike 73: The smoothness pull (C40): do near-identity letters override the predictive kernel?

**Date:** 2026-11-18 · **Status:** pre-registered (predictions in `results/spike73_predictions.json`, committed with this report before any run) · **Follows:**
- Spike 69 (ℤ/7 exception), Spike 71 (ℤ/11 returns to the k = ±1 circle; P205): the cyclic evidence for C40.
- Spike 72 (the cover survives degree-2 input, so C38 is refuted, P206; the A₅ part did not fit).

## Conjecture C40 (smoothness pull)

A recurrent learner leads with the faithful irreducible that varies most slowly along its letters, i.e. the one maximising mean P(e, a)/P(e, e) over the letters a. It does so even against the predictive kernel's energy, when letters are near the identity.

For ℤ/n with letter +s, the smoothest character is the k with ks ≡ ±1 (mod n). Changing s at a fixed readout moves the smooth character while the readout's spectrum stays put. That separates C40 from the predictive-energy law (C37) in both directions.

## Part A: cyclic groups, letter step versus readout spectrum (n prime, so every nontrivial character is faithful)

The letters are +s and the identity. The output is [c ∈ S]. The energy prediction (top isotypic share of the predictive kernel, ≥ 1.5 × the second) and the smooth prediction are both computed below.

| Automaton | Letter | Readout S | Energy (C37) | Smooth (C40) | Role |
|---|---|---|---|---|---|
| Z11_s1_03 | +1 | {0, 3} | k = ±4 (0.53) | k = ±1 | discriminating (replicates Spike 71 without new knobs) |
| Z11_s3_03 | +3 | {0, 3} | k = ±4 | k = ±4 | agreement |
| **Z11_s3_012** | +3 | {0, 1, 2} | **k = ±1 (0.80)** | **k = ±4** | discriminating, the *opposite* direction |
| Z13_s1_05 | +1 | {0, 5} | tie (k = 5: 0.45; k = 3: 0.31) | k = ±1 | smooth only |
| **Z13_s5_012** | +5 | {0, 1, 2} | **k = ±1 (0.70)** | **k = ±5** | discriminating, opposite direction |
| Z13_s5_05 | +5 | {0, 5} | tie | k = ±5 | smooth only |

## Part B: A₅ on its 6 axes with icosahedral letters, fit repaired

Spike 72's discrete test failed the guard, which we attribute to the identity letter. Here the letters are (0 1 2) and (0 1 2 3 4) only, as in Spike 60 (3/5 fitted there), and training runs 12,000 steps. Encodings:
- **A5_ONEHOT:** a learned embedding;
- **A5_RHO3:** the icosahedral 3×3 matrices (Spike 72's construction).

Predictions are from Spike 72's file:
- C38 (refuted on the continuous side) predicted χ₃ (r1) for RHO3.
- The energy law predicts χ₅ (r3) for both.

## Part C: axis tracking with large rotation steps

This is Spike 70's AXIS task with ω input, but with σ = 0.5 and σ = 1.0 rad instead of 0.15. **C40 predicts** that far-from-identity steps remove the smoothness pull. The predictive kernel of the AXIS readout lives in degree 2, so the network should then build RP² and carry no sign.

## Training and measurement

- **Part A:** Spike 71's trainer (GRU 64, Adam lr 0.003 cosine, 6,000 steps, length 30). The final leader is the top isotypic share of the centroid Gram (cosine), with the whitened version reported.
- **Part B:** Spike 72's discrete trainer without the identity letter, 12,000 steps; the leader is defined as in Spike 72.
- **Part C:** Spike 72's continuous trainer (ω input). Measured: R²_ℓ and the balanced sign probe.

**Seeds:** 5 per job, seed 7,300 + 10·job + seed.

**Fit guards:**
- Parts A and B: accuracy ≥ 0.99 at length 100.
- Part C: R² ≥ 0.90 at length 30.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H73.1 | C40: cyclic leader = smoothest faithful character (all six automata) | ≥ 80% of fitted runs | < 50% |
| H73.2 | **C40 against C37 where they disagree** (Z11_s1_03, Z11_s3_012, Z13_s5_012) | smooth prediction leads in ≥ 80% | energy prediction leads in ≥ 50% |
| H73.3 | A₅ with icosahedral letters leads with χ₃ (C38, discrete side) | ≥ 80% of fitted RHO3 runs | < 50% |
| H73.4 | A₅ with one-hot letters leads with χ₅ (energy law; Spike 60 replication) | ≥ 80% of fitted ONEHOT runs | < 50% |
| H73.5 | C40, continuous: with σ = 1.0, axis-trackers drop the sign (RP²) | balanced sign probe ≤ 0.75 in ≥ 80% of fitted runs | ≥ 0.95 in ≥ 50% |

Anything else is *neither*.

**Guards.**
- Each automaton or setting counts only with ≥ 3 fitted seeds.
- H73.1 needs ≥ 4 qualifying automata, and H73.2 needs ≥ 2.

**Reported without criteria:** σ = 0.5, all shares, and the whitened leaders.

## What this cannot show

- For prime n, changing the letter is equivalent to relabelling the readout by an automorphism. So Part A tests "letters versus readout spectrum", not anything beyond that.
- Large-σ tracking may fail the guard (no verdict).
- One architecture.

## Commands

```
python -m experiments.spike73 predict
python -m experiments.spike73 run
python -m experiments.spike73 analyse
```
