# Spike 82: The selection rule in pretrained language models: number concepts

**Date:** 2026-11-19 · **Status:** complete (pre-registered with output-only predictions in ad98065; results below) · **Follows:** Spikes 77–81 (the Gibbs selection rule C43). This is the first test outside trained-from-scratch toy automata. Related: Engels et al. 2024 (2405.14860, circular features); Kantamneni & Tegmark 2025 and Zhou et al. 2024 (Fourier features of numbers in LLMs, periods 2, 5, 10, 100).

## Design

- **Concept.** The integers 0–99, treated as the cycle ℤ/100 under the counting action +1.
- **Value: from the model's own predictions.** For each of 16 templates ("I counted up to {n}", "There were {n}", "Turn to page {n}", …), take the model's next-token distribution after the number.
  - K(n, m) is the mean Hellinger inner product of those distributions over templates, double-centred.
  - Value e_k is the Fourier energy share of K at frequency k = 1…50.
  - Templates are used only where every number 0–99 is a single token.
- **Cost:** c_k = 1 − cos(2πk/100), the kinetic cost of the counting action +1.
- **Rule** (α, λ frozen from Spike 77): P(k) ∝ e_k^α·exp(−λ c_k). Rivals are energy-only and smoothness-only (with Spike 77's parameters).
- **Test.** Hidden states at ~60% depth at the number token, averaged over templates, centred and normalised. The leading Fourier mode of their Gram over ℤ/100 is the observation.
- **Models:**
  - GPT-2: 16 templates; layer 7 of 12.
  - Pythia-410m: 16 templates; layer 14 of 24.
  - GPT-2-medium: 16 templates; layer 14 of 24.
  - SmolLM2-360M was skipped: its tokenizer splits numbers into digits.

## Predictions (from outputs only)

| Model | Top value modes (k) | Gibbs | Energy-only | Smooth-only |
|---|---|---|---|---|
| GPT-2 | 1, 40, 20, 50, 2, 3 | k = 1 | k = 1 | k = 1 |
| Pythia-410m | 1, 40, 50, 2, 20, 10 | k = 1 | k = 1 | k = 1 |
| GPT-2-medium | 1, 40, 2, 50, 3, 20 | k = 1 | k = 1 | k = 1 |

**Limitation, stated before running.** All three rules predict k = 1 in every model, so this spike cannot separate the rule from its rivals. It tests only the shared prediction that a period-100 counting circle leads the geometry.

The models' *predictive* spectra do contain the known high-frequency structure:
- k = 40 (period 2.5);
- k = 20 (period 5);
- k = 50 (period 2);
- k = 10 (period 10).

So the test can fail if the hidden geometry is led by one of those modes, as the published "periods 2, 5, 10" findings would suggest.

## Hypothesis and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H82.1 | The frozen rule predicts the leading Fourier mode of LM number geometry | rule argmax = observed leading k in ≥ 2/3 of models **and** pooled NLL below both rivals | matches in < 1/3 of models |

The NLL comparison is weak here because the rules agree. A held verdict can come mainly from the accuracy term.

Reported without criteria: the top learned Fourier modes per model.

## What this cannot show

- Three small models, one layer each, one concept.
- A one-step predictive kernel; the toy automata used a 30-step horizon.
- Non-discriminating predictions (above).
- Numbers are also *linearly* ordered. A monotone magnitude code also loads mostly on k = 1, so "k = 1 leads" does not distinguish a circle from a line.

## Commands

```
python -m experiments.spike82 predict
python -m experiments.spike82 run
python -m experiments.spike82 analyse
```

## Results

`experiments/results/spike82.json`; hidden states in `spike82_raw/` (git-ignored if large).

| Model | Learned leading k | Top learned modes (share) | Predicted (all rules) |
|---|---|---|---|
| GPT-2 | **1** | 1 (0.45), **50 (0.35)**, 40 (0.17), 30, 10, 2 | k = 1 |
| Pythia-410m | **1** | 1 (0.48), **50 (0.34)**, 40 (0.08), 2, 20 | k = 1 |
| GPT-2-medium | **1** | 1 (0.52), **50 (0.30)**, 40 (0.14), 2, 20 | k = 1 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H82.1 | rule argmax = observed leading k in 3/3 models; pooled NLL: Gibbs 0.08, energy-only 2.73, smoothness-only 9.19 | ≥ 2/3 and NLL below both rivals | **HELD** |

**Reading:**
- **The leading mode is predicted**, in all three pretrained LMs: the period-100 counting circle (k = 1). As stated before running, every rule predicted k = 1, so this confirms the shared prediction, not the rule against its rivals. The NLL margin reflects the rule's confidence, not discrimination. A monotone magnitude code would also load on k = 1.
- **The second mode is the instructive part.** In every model, parity (k = 50, period 2) carries 30–35% of the number geometry, and k = 40 (period 2.5) another 8–17%. These are the modes with the *highest* predictive value after k = 1 in the model's own next-token behaviour. But they are the *most expensive* under the counting action: k = 50 flips sign at every step, cost 2, the maximum. A cost-only account would suppress them.

  So in LMs the leading constituent follows the rule, while the *secondary* structure follows value despite maximal cost. Two readings are possible:
  - LM numbers are not learned through the +1 counting action alone. Other actions in text (+2, ×10, parity-dependent agreement) are cheap for the k = 50 mode. That would fit the repertoire-dependence found in Spike 78.
  - The single-leader summary is too coarse for a multi-constituent geometry.

  This is exploratory and post hoc. It points to the next test: specify the LM's action repertoire (which numerical operations appear in text) and predict the *whole* spectrum, not only its leader.
