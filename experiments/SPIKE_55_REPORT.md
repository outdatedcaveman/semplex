# Spike 55: Does a model's fairness verdict factor through the quotient by persons?

**Date:** 2026-11-16 · **Status:** pre-registered (no analysis run) · **Follows:** `charter/FOUNDATIONS.md` §8, conjecture C30; Spike 52 (moral concept pilot, no verdict); Spike 54 (same data source). **Conjecture:** C30.

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

(Not run.)
