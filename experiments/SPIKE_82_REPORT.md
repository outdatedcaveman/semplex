# Spike 82: The selection rule in pretrained language models: number concepts

**Date:** 2026-11-19 · **Status:** pre-registered (predictions in `results/spike82_predictions.json`, computed from model *outputs only* and committed with this report before any hidden state was read) · **Follows:** Spikes 77–81 (the Gibbs selection rule C43). This is the first test outside trained-from-scratch toy automata. Related: Engels et al. 2024 (2405.14860, circular features); Kantamneni & Tegmark 2025 and Zhou et al. 2024 (Fourier features of numbers in LLMs, periods 2, 5, 10, 100).

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
