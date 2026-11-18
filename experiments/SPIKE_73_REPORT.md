# Spike 73: The smoothness pull (C40): do near-identity letters override the predictive kernel?

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in 4bca70d; results below) · **Follows:**
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

## Results

`experiments/results/spike73.json`; per-run outputs in `spike73_raw/`.

**Fitted runs:**
- Z11_s1_03 5/5, Z11_s3_03 3/5, Z11_s3_012 3/5.
- Z13 automata: 0, 0 and 1 of 5. The ℤ/13 subset readouts did not fit at length 100 (0.80–0.99).
- A5_ONEHOT 5/5 and A5_RHO3 4/5: **the fit repair worked**.
- AX σ = 0.5: 0/5 (R² 0.71–0.74). AX σ = 1.0: 0/5 (R² ≈ 0.005, not learned at all).

| Automaton | Energy | Smooth | Final leader (all runs; fitted runs in bold) |
|---|---|---|---|
| Z11_s1_03 | k = 4 | k = 1 | **k = 1 4/5**, k = 3 1/5 |
| Z11_s3_03 | k = 4 | k = 4 | **k = 4 3/3** (5/5 overall) |
| Z11_s3_012 | **k = 1** | k = 4 | **k = 1 3/3** (5/5 overall) |
| Z13_s1_05 (unfitted) | tie | k = 1 | k = 2 3/5, k = 3 2/5 |
| Z13_s5_012 (unfitted) | k = 1 | k = 5 | k = 2 5/5 |
| Z13_s5_05 (1 fitted) | tie | k = 5 | k = 5 5/5 |
| A5_ONEHOT | χ₅ | — | **χ₅ 5/5** |
| A5_RHO3 (icosahedral letters) | χ₅ | — | **χ₅ 4/4** (5/5 overall) |
| AX σ = 0.5 (unfitted) | RP² under C40 | — | sign kept: balanced probe 0.99 in 5/5; R²₁ 0.30–0.32 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H73.1 | only 3 automata qualify (needs 4); among them the smooth prediction leads in 64% | guard | **NO VERDICT** |
| H73.2 | discriminating cases: smooth leads 50%, energy 38% | smooth ≥ 80% held; energy ≥ 50% broken | **NEITHER** |
| H73.3 | A₅ with icosahedral χ₃ letters leads with χ₃ in 0/4 | ≥ 80% held, < 50% broken | **BROKEN** |
| H73.4 | A₅ with one-hot letters leads with χ₅ in 5/5 | ≥ 80% | **HELD** |
| H73.5 | no fitted σ = 1.0 runs | guard | **NO VERDICT** |

**Reading:**
- **C38 is now refuted on both sides.** Fed the icosahedral 3×3 matrices as letters, fitted A₅ networks still lead with χ₅, the readout's own representation (4/4). Their input carries the χ₃ representation, but the learned geometry ignores it. Together with Spike 72 (continuous), the input encoding decides neither the cover nor the leading constituent in these tasks.
- **The energy law replicates for A₅ on its 6 axes** (H73.4, 5/5). This is Spike 60's prospective result, now with a different trainer and twice the steps.
- **Neither pure smoothness nor pure energy decides cyclic geometry** (H73.2 neither).
  - **Z11_s1_03:** smoothness wins (k = 1 against energetic k = 4).
  - **Z11_s3_012:** energy wins (k = 1 against smooth k = 4).

  The difference is that in Z11_s3_012 the smooth character has **zero** predictive energy: it does not occur in the readout at all.
- **Large rotation steps could not be learned.** At σ = 0.5 the fit was 0.72, and the sign was still kept (0.99, unfitted). At σ = 1.0 nothing was learned. The continuous half of C40 is untested.

**Exploratory, after the verdicts: gated smoothness** (`experiments/theory/gated_smoothness.py`, `results/theory_gated_smoothness.json`). Among the constituents whose predictive-kernel share is ≥ θ, take the smoothest along the letters, with energy breaking smoothness ties. This rule fits:
- **46 of 48 fitted runs on cyclic groups** across Spikes 69, 71 and 73 (ℤ/7, ℤ/8 twice, ℤ/9, ℤ/10, ℤ/11 four ways, ℤ/12, ℤ/13, plus ℤ/4 × ℤ/2), for any θ between 0.05 and 0.10. This includes every case where pure energy failed: ℤ/7, ℤ/11, ℤ/12.
- The non-cyclic abelian ℤ/3 × ℤ/3 in only 1/5 runs.
- Over all 135 fitted runs of the three spikes, 106 (79%). The misses are concentrated in Q₈ with the identity readout, D₄ on 4 points, and S₄ pairs with Coxeter letters.

**C41 (gated smoothness)** is fitted after the fact, and θ was chosen on these data. It is a candidate law and must be tested prospectively (Spike 74).
