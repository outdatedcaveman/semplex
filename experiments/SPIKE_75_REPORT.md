# Spike 75: Are closure and the predictive-energy shape law substrate-independent?

**Date:** 2026-11-18 · **Status:** pre-registered (predictions in `results/spike75_predictions.json`, committed with this report before any run) · **Follows:** the user's directive of 2026-11-18 to state laws for any computing system, not for one network architecture; P200 (closure discards the unobservable part); P201 and P204 (the shape law); `charter/FOUNDATIONS.md` §14.

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
