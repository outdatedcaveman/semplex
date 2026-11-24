# Spike 75: Are closure and the predictive-energy shape law substrate-independent?

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in 015d439; results below) · **Follows:** the user's directive of 2026-11-18 to state laws for any computing system, not for one network architecture; P200 (closure discards the unobservable part); P201 and P204 (the shape law); `charter/FOUNDATIONS.md` §14.

## Question

Every result in Spikes 57–74 comes from networks trained by gradient descent. A law about *concepts* should hold for any system that learns to predict, or fail in a principled way. Here the same automata are learned by four substrates that share nothing but the task:

| Substrate | What it is | Adapts its state? | Gradients? |
|---|---|---|---|
| **GRU** | Recurrent network trained by Adam, as in Spikes 69–71 | yes | yes |
| **SPEC** | Exact spectral learner. The state of a history is its row of the Hankel matrix (future outputs over 300 random suffixes of length ≤ 8), projected onto the nonzero singular subspace. This is predictive-state compression in the sense of Ho–Kalman realisation, Fliess's theorem for weighted automata, and the spectral learning of Hsu, Kakade and Zhang. | yes (by construction) | no |
| **RES** | Fixed random echo-state reservoir: 200 tanh units, spectral radius 0.9, random input weights. Only a linear readout is trained (ridge). A physical-style system with fading memory. | **no** | no (closed-form readout) |
| **ES** | The same GRU, trained by evolution strategies: antithetic Gaussian perturbations (population 64, σ = 0.05), rank-weighted updates with Adam, 4,000 iterations | yes | **no** |

## Automata (letters: generators plus identity) and predictive-kernel predictions (computed before training)

| Automaton | Readout | Minimal automaton | Energy prediction |
|---|---|---|---|
| Z6_mod3 | [c ≡ 0 mod 3] | ℤ/3 (3 states) | k = ±2 (the mod-3 character; share 1.0) |
| A4_4 | one-hot g(0) | A₄ | χ₃ (1.0) |
| A4_6 | one-hot pair {g(0), g(1)} | A₄ | ω-pair (0.67, unfaithful) |
| S4_12 | cosets of ⟨(01)⟩ | S₄ | std (m = 2, 0.67) |
| Z9_s1_014 | [c ∈ {0, 1, 4}] | ℤ/9 | r0 (0.55); a seed lottery in Spike 74 |

ES is run on Z6_mod3, A4_4 and A4_6 only, because of cost.

**Seeds:**
- GRU 5, RES 5 and ES 3 per automaton;
- SPEC 3: it is deterministic up to the suffix sample.

**Fit guards:**
- GRU and ES: ≥ 0.99 at length 100.
- SPEC is exact by construction.
- RES is not guarded: it is a fixed physical system, and its failure to fit is part of the question.

**Measured on 400 strings of length 30, steps 5–29:**
- the macrostate probe;
- the group-element probe;
- for Z6_mod3, the probe for c mod 2;
- each irreducible's isotypic share of the centred centroid Gram, and the leader.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H75.1 | **Closure discards the unobservable part in every adaptive substrate** (Z6_mod3: c mod 2 not linearly decodable) | median probe for c mod 2 ≤ 0.6 in each adaptive substrate with fitted runs (GRU, SPEC, ES; at least 2 substrates) | any adaptive substrate has median ≥ 0.9 |
| H75.2 | **The energy law holds across adaptive substrates** (A4_6, S4_12) | leader = energy prediction in ≥ 80% of fitted runs pooled over GRU, SPEC and ES (≥ 2 substrates) | < 50% |
| H75.3 | **Readout-shaped geometry needs an adaptive state.** The reservoir's leading constituent does not depend on the readout (same leader for A4_4 and A4_6 with the same reservoir), while the GRU's does (χ₃ vs ω-pair) | same leader for RES in ≥ 80% of seed pairs **and** for GRU in ≤ 20% | RES same-leader fraction ≤ GRU's |
| H75.4 | **A fixed reservoir does not build the minimal automaton** | macrostate probe ≤ 0.9 in ≥ 80% of RES runs | < 50% |

Anything else is *neither*.

**Note on design history.** A smoke test, run before registration on the throwaway seed 1, showed the reservoir cannot even count mod 3 (probe 0.35). So a pre-drafted hypothesis that "the reservoir keeps the unobservable 2-part" was replaced, before any registered run, by H75.4.

**Reported without criteria:** Z9_s1_014 leaders per substrate (lottery or not), probes, and fits.

## What this cannot show

- Four substrates, all simulated on a digital computer.
- SPEC realises the predictive kernel by construction (its Gram is the Hankel Gram), so for SPEC, H75.2 is a check of the measurement pipeline, not a discovery. The informative substrates are ES (no gradients) and RES (no adaptation).
- One reservoir size and spectral radius.

## Commands

```
python -m experiments.spike75 predict
python -m experiments.spike75 run
python -m experiments.spike75 analyse
```

## Results

`experiments/results/spike75.json`; per-run outputs in `spike75_raw/`. A container restart interrupted the runs. Because they are seeded and the runner skips completed runs, the restart changed nothing.

**Fits:**
- GRU: 23 of 25 fitted (two S4_12 runs reached 0.93 and 0.98).
- SPEC: exact by construction.
- ES: Z6_mod3 fitted 3/3; **A4_4 did not fit (0.77–0.78) and A4_6 did not (0.85–0.90)**, so ES counts only for H75.1.
- RES: fit 0.65–0.92 (not guarded).

| Substrate | Z6_mod3: macro probe / c mod 2 | A4_4 leader | A4_6 leader | S4_12 leader | Z9_s1_014 leader | Macro probe (A₄, S₄) |
|---|---|---|---|---|---|---|
| GRU (gradients) | 1.00 / **0.52–0.57** | χ₃ 5/5 | **ω-pair 5/5** | **std 5/5** | r0 5/5 | 0.70–1.00 |
| SPEC (Hankel SVD) | 1.00 / **0.50–0.52** | χ₃ 3/3 | **ω-pair 3/3** | **std 3/3** | r0 3/3 | 1.00 |
| ES (no gradients) | 1.00 / **0.52–0.54** | χ₃ 3/3 (unfitted) | ω-pair 3/3 (unfitted) | — | — | 0.24–0.59 (unfitted) |
| RES (fixed reservoir) | **0.33–0.35** / 0.50 | χ₃ 5/5 | **χ₃ 5/5** | std⊗sign 5/5 | r1 5/5 | **0.05–0.16** |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H75.1 | median c mod 2 probe: GRU 0.56, SPEC 0.52, ES 0.53 | all ≤ 0.6 | **HELD** |
| H75.2 | energy prediction = leader in 100% of fitted A4_6/S4_12 runs (GRU 9/9, SPEC 6/6; ES unfitted) | ≥ 80%, ≥ 2 substrates | **HELD** |
| H75.3 | reservoir: same leader for both A₄ readouts in 5/5 seed pairs; GRU in 0/5 | RES ≥ 80% and GRU ≤ 20% | **HELD** |
| H75.4 | reservoir macrostate probe ≤ 0.9 in 25/25 runs (0.05–0.35) | ≥ 80% | **HELD** |

**Reading:**
- **Closure is a property of adaptive predictive compression, not of gradient descent or of one architecture.**
  - Three learners that share nothing but a predictive objective and an adaptive state each build exactly the 3-state minimal automaton of ℤ/6 read out mod 3. Each keeps no linearly decodable trace of the unobserved 2-part:
    - a gradient-trained GRU;
    - an exact SVD of the Hankel matrix;
    - a GRU trained by evolution strategies, with no gradients at all.
  - A fixed random reservoir with a trained linear readout builds no minimal automaton at all. Its state is a fading memory of recent letters (Tiňo's Markovian bias), and probes recover the macrostate at near-chance levels for every automaton.
- **The predictive-energy shape law holds identically in a substrate with no neurons and no gradients.** Wherever the gradient-trained network fits, its leading constituent is the one the exact spectral learner selects: the unfaithful ω-pair for A₄ on pairs, std (multiplicity 2) for S₄ on 12 cosets. In the ℤ/9 automaton that was a seed lottery in Spike 74, this spike's GRUs (5/5) and the spectral learner (3/3) both chose the energy prediction.

  The evolution-strategies networks, not fitted on A₄, already led with the readout's predicted constituent: ω-pair for the pair readout, χ₃ for the point readout.
- **Readout-shaped geometry requires an adaptive state.** The reservoir's leading constituent is the same whatever the readout (χ₃ for both A₄ readouts), because its geometry is set by its fixed dynamics and the letters. Adaptive learners switch with the readout.

**What this establishes, honestly.** For the spectral learner the shape law holds by construction: its Gram is the Hankel Gram. The content of H75.2 is that a gradient-trained nonlinear network converges to the same subspace, and the content of H75.1 that a gradient-free one discards the same information. So the laws describe a *target* that different adaptive learners reach, the top of the Hankel (Ho–Kalman) realisation. They are not a property of one learning rule.

In the 2026-11-18 literature check, no prior measurement of recurrent-network states against the Hankel singular subspace, and no cross-substrate test of minimal-automaton recovery, was found.

**Limits:**
- ES failed to fit A₄.
- One reservoir configuration.
- All four substrates are simulated digitally.
- The next substrates in `charter/FOUNDATIONS.md` §14.2 are chemical reaction networks and Hebbian/local learners.
