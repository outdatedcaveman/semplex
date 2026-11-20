# Spike 55: Does a model's fairness verdict factor through the quotient by persons?

**Date:** 2026-11-16 · **Status:** complete (pre-registered in 17b75ab; results below) · **Follows:** `charter/FOUNDATIONS.md` §8, conjecture C30; Spike 52 (moral concept pilot, no verdict); Spike 54 (same data source). **Conjecture:** C30.

## Question

C30 says a fairness verdict is impartial exactly when it is invariant under permuting the persons involved (the veil of ignorance as a symmetry). On C29, an impartial concept's representation should factor through the quotient by that group: the verdict depends on *what was done to whom, by role*, not on *who*.

A model's whole internal state cannot be name-invariant: it must carry the names to continue the text. The prediction is therefore about the **verdict read out of the state**. It should be far more name-invariant than the state itself.

## Data (Neuronpedia, as in Spike 54; no model run here)

The sources are the same 7 published sparse-autoencoder layers as in Spike 54, gpt2-small 4/8/10-res-jb through llama3.1-8b 16-llamascope-res-32k, and the endpoint is the same `search-topk-by-token` (top 20 features, density threshold 0.01).

**Cases.** Sentence: "{A} {act} {B}. That was". The representation is the top-20 feature vector at the last token, " was", normalised.

- **12 acts** (labelled before any run):
  - **unfair:** "stole money from", "lied to", "cheated", "broke a promise to", "took credit for the work of", "insulted";
  - **fair:** "returned the money to", "told the truth to", "paid back", "kept a promise to", "gave credit to", "thanked".
- **12 name assignments.** Every ordered pair of distinct names from {Emily, Jamal, Mei, Carlos}. A transposition of the pair is one element of the person-permutation group acting on the case.

That gives 144 sentences per source.

## Statistics

**Verdict readout.** For each held-out act k:
1. Take the 11 other acts.
2. Set w = mean representation of their unfair cells − mean of their fair cells.
3. Score each of act k's 12 cells as v = ⟨x, w⟩ − c, where c is the midpoint of the two training means projected on w.

The readout never sees the held-out act.

**Name shares.**
- **Verdict:** s_v = (variance of v within acts, across name assignments) / (total variance of v).
- **State:** s_x = Σ‖x − x̄_act‖² / Σ‖x − μ‖², the share of the representation's variance that depends on names.

## Hypotheses and kill criteria

A *source* is one of the 7 SAE layers.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H55.1 | The verdict is readable from the state | held-out accuracy (a cell counts as correct when v > 0 exactly for unfair acts) ≥ 0.80 in ≥ 5 of 7 sources | ≥ 0.80 in ≤ 2 sources |
| H55.2 | **The verdict is impartial** (C30) | s_v ≤ 0.10 in ≥ 75% of usable sources | s_v ≥ 0.25 in ≥ 50% of usable sources |
| H55.3 | **The verdict factors through the quotient** (more invariant than the state) | s_v < s_x in ≥ 75% of usable sources | in < 50% |

Anything else is *neither*. "Usable" means held-out accuracy ≥ 0.70: no verdict on H55.2 and H55.3 if fewer than 4 sources are usable.

**Reported without criteria:**
- **Directional name effects:** the mean verdict score by agent name and by victim name, and their spread relative to the act effect. This is the face of bias, for example a harsher verdict when Jamal is the agent.
- **Role asymmetry:** the mean v(A, B) − v(B, A) over acts.

## What this cannot show

- The readout is a mean-difference direction in a top-20 sparse code. The models' own verdicts (their next-token probabilities) are not available from this endpoint.
- Four names, one sentence frame, twelve acts.
- Invariance in a representation is not impartiality in behaviour. This is a first measurement of whether the structure C30 names is present.

## Commands

```
python -m experiments.spike55 run
python -m experiments.spike55 analyse
```

## Results

`experiments/results/spike55.json`; raw responses in `spike54_raw/` (cache shared with Spike 54). The token rule held in all 7 sources.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H55.1 | held-out accuracy ≥ 0.80 in 2 of 7 sources (median 0.69) | ≥ 5 held, ≤ 2 broken | **BROKEN** |
| H55.2 | 3 usable sources (< 4) | guard | **NO VERDICT** |
| H55.3 | 3 usable sources (< 4) | guard | **NO VERDICT** |

**Per source:**

| Source | Accuracy | s_v (verdict's name share) | s_x (state's name share) |
|---|---|---|---|
| gpt2-small 4-res-jb | 0.44 | 0.197 | 0.580 |
| gpt2-small 8-res-jb | 0.42 | 0.295 | 0.357 |
| gpt2-small 10-res-jb | 0.58 | 0.207 | 0.305 |
| gemma-2-2b 12-gemmascope | 0.71 | 0.177 | 0.292 |
| gemma-2-2b 20-gemmascope | 0.89 | 0.112 | 0.256 |
| gemma-3-1b 13-gemmascope-2 | 0.86 | 0.068 | 0.223 |
| llama3.1-8b 16-llamascope | 0.69 | 0.103 | 0.228 |

**Reading:**
- At the token " was", right after the case is stated, a fairness verdict is readable by a held-out mean-difference direction in the later Gemma layers but not in GPT-2. GPT-2 is at or below chance, so its sparse code at that point does not separate fair from unfair acts along a shared direction.
- C30 could not be tested as registered.
- **Descriptively, below the registered bar:**
  - where a verdict is readable at ≥ 0.70 (three sources), its dependence on names is 0.07–0.18 of its variance, against 0.22–0.29 for the state as a whole. That is the direction C30 predicts in all three.
  - In every source the verdict depends on names less than the state does (7 of 7).
- **Exploratory name effects.** No name shifts the verdict by more than the act effect's standard deviation in the readable sources: agent spread 0.08–0.30, victim spread 0.14–0.36 of the act SD. The mean role asymmetry v(A, B) − v(B, A) is 0 to four decimals, which is forced by the design, because every ordered pair appears.
- **What the next test needs:** the models' own verdicts (next-token probabilities of "fair"/"unfair"), which this endpoint does not give, or a later token where the verdict is stated.
