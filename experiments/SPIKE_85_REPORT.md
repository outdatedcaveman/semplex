# Spike 85: Does the selection rule predict a language model's whole number spectrum from the model's own repertoire?

**Date:** 2026-11-19 · **Status:** pre-registered (repertoires, costs and predicted spectra in `results/spike85_predictions.json`, committed with this report before `analyse` is run) · **Follows:**
- Spike 82 (LM number geometry leads with k = 1: held, but not discriminating).
- Spike 77 (Gibbs rule, frozen α = 2.489, λ = 3.675).
- Spike 78 (cost is repertoire-based, not usage-weighted).

## Why

Spike 82 tested only the *leading* Fourier mode, and every rival predicted k = 1. This spike asks the whole spectrum. With the frozen parameters, does P(k) ∝ e_k^α · exp(−λ c_k) rank the learned Fourier modes of the hidden states? The value e_k is the energy share of the predictive kernel, and the cost c_k comes from the transitions the model itself treats as its actions.

## Construction (done before analysis)

**Repertoire.** Five transition templates: "from {n} to", "{n}, then", "counting: {n},", "between {n} and", "after {n} comes". For each, pool the model's next-number probability mass over differences d = m − n (mod 100). The repertoire is every d with ≥ 5% of the pooled mass, each weighted equally (Spike 78).

**Cost.** c_k = mean over the repertoire of 1 − cos(2πkd/100), the kinetic (chord²) cost of Spike 80.

**Predicted spectra over k = 1..50:**
- gibbs: (α, λ) frozen;
- energy-only: Spike 77's energy-only α;
- cost-only: Spike 77's smooth λ.

| Model | Repertoire d (pooled mass) | Top-5 gibbs k |
|---|---|---|
| GPT-2 | 0 (.066), 1 (.084), 2 (.069), 3 (.052), 5 (.050) | 1, 40, 2, 3, 20 |
| Pythia-410m | **empty** (no difference reaches 5%) | 1, 40, 50, 2, 20 |
| GPT-2-medium | 1 (.054), 2 (.059), 5 (.051) | 1, 2, 40, 3, 20 |

**Known weakness, stated before the test.** For Pythia the repertoire is empty, so the cost is 0. Then gibbs = energy up to α, and the Spearman ranks are identical: gibbs cannot *beat* energy for that model. H85.1 therefore counts Pythia as a non-win. This is a pre-registered handicap, not a post hoc exclusion.

## Measurement

The learned spectrum is the Fourier energy shares of the centred, normalised cosine Gram of the Spike 82 hidden states (layer ≈ 60%). The comparison is the Spearman ρ between log predicted P(k) and the learned shares.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H85.1 | The gibbs spectrum ranks the learned modes better than both energy-only and cost-only | gibbs ρ > max(rivals) in ≥ 2/3 of models | < 1/3 |
| H85.2 | The gibbs spectrum predicts the whole learned spectrum | median gibbs ρ ≥ 0.5 | < 0.2 |

Anything else is *neither*. At least 3 models are needed for a verdict.

## What this cannot show

- Three models, one number range, one layer.
- The 5% repertoire cut is a fixed choice.
- "Repertoire" here is the model's *predicted* transitions, a proxy for its action set.
- Fourier modes are the irreducibles of ℤ/100 only if the model treats numbers cyclically; it does not exactly.

## Commands

```
python -m experiments.spike85 predict
python -m experiments.spike85 analyse
```
