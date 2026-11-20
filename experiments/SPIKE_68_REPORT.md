# Spike 68: Shared shape and shared axes for concepts in context, with a tied-basis control (C34)

**Date:** 2026-11-17 · **Status:** complete (pre-registered in 56a3fc1; results below) · **Follows:** Spikes 61 and 64 (P191, P195: lexicons share shape and a common frame up to one rotation per model, but not raw axes); `charter/FOUNDATIONS.md` §11.1 (C34). Numbered 68 because §12 reserved 65–67 for the continuous and arithmetic tests.

## Question

C34 says independently trained models share a concept's invariants, but not their raw coordinates, unless their bases are tied by training. Tested on in-context representations:
- **unrelated models** should share shape (CKA), and share a common frame after rotation (Procrustes), but not raw axes;
- **a model and its own fine-tune** share raw axes too.

## Models (run on CPU)

- Qwen/Qwen2.5-0.5B (base) and Qwen/Qwen2.5-0.5B-Instruct: tied, because the instruct model is fine-tuned from the base.
- HuggingFaceTB/SmolLM2-360M.
- EleutherAI/pythia-410m.
- openai-community/gpt2.

Each is downloaded, used and deleted.

## Concepts and representation

- **Concepts.** THINGS concept words (Spike 53 metadata) that are single tokens in all five tokenizers, in sorted order, at most 300.
- **Contexts.** Five fixed templates:
  - "I saw a {w} yesterday."
  - "There is a {w} on the table."
  - "She talked about the {w}."
  - "A picture of a {w}."
  - "We need a {w} now."
- **Representation.** The residual stream at the concept's token, at the layer nearest 60% of depth (following arXiv:2611.11531), averaged over the five templates, then centred and normalised across concepts.

## Measures (per model pair; 10 pairs)

- **Shape:** linear CKA.
- **Common frame:** held-out R² of an orthogonal Procrustes map, fitted on 80% of concepts and evaluated on 20%, after reducing both to their top 64 principal components.
- **Raw axes:**
  - for each coordinate (neuron) of model A, the largest |Pearson r| with any coordinate of model B, over concepts;
  - the mean over A's coordinates, symmetrised;
  - this is compared with the same statistic after shuffling concepts in B (*axis excess* = observed − shuffled).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H68.1 | Shape is shared across unrelated models | median CKA ≥ 0.5 over the 9 unrelated pairs | < 0.25 |
| H68.2 | **Raw axes are tied only by training:** the tied pair's axis excess far exceeds every unrelated pair's | tied excess ≥ 3× the largest unrelated excess | tied excess ≤ the median unrelated excess |
| H68.3 | A common frame exists after rotation for unrelated models | median Procrustes held-out R² ≥ 0.3 over unrelated pairs | < 0.1 |

Anything else is *neither*.

## What this cannot show

- Five models, one layer choice, five templates.
- Neuron-level matching is one notion of axis; others (sparse atoms) were tested in Spike 61.

**Procedure change before any result (recorded).** The first run computed one sentence at a time and took over 50 minutes for its first model, with CPU threads oversubscribed by a parallel spike. It was stopped, no representation saved, and replaced by batched forward passes (100 sentences per batch, right padding, attention mask). The representation (the residual at the concept token) is unchanged.

## Commands

```
python -m experiments.spike68 run
python -m experiments.spike68 analyse
```

## Results

`experiments/results/spike68.json`; representations in `spike68_raw/`. 300 concepts. Layers used (nearest 60% of depth): Qwen 14, SmolLM2 19, Pythia 14, GPT-2 7.

| Pair | Tied | CKA | Procrustes R² | Axis | Axis (shuffled) | Axis excess |
|---|---|---|---|---|---|---|
| Qwen2.5-0.5B – Qwen2.5-0.5B-Instruct | yes | 0.99 | 0.98 | 0.97 | 0.19 | 0.78 |
| Qwen2.5-0.5B – SmolLM2-360M |  | 0.85 | 0.48 | 0.39 | 0.19 | 0.20 |
| Qwen2.5-0.5B – pythia-410m |  | 0.84 | 0.46 | 0.36 | 0.19 | 0.17 |
| Qwen2.5-0.5B – gpt2 |  | 0.79 | 0.29 | 0.35 | 0.19 | 0.16 |
| Qwen2.5-0.5B-Instruct – SmolLM2-360M |  | 0.85 | 0.47 | 0.39 | 0.19 | 0.20 |
| Qwen2.5-0.5B-Instruct – pythia-410m |  | 0.83 | 0.46 | 0.36 | 0.19 | 0.17 |
| Qwen2.5-0.5B-Instruct – gpt2 |  | 0.79 | 0.32 | 0.35 | 0.19 | 0.15 |
| SmolLM2-360M – pythia-410m |  | 0.84 | 0.43 | 0.36 | 0.19 | 0.17 |
| SmolLM2-360M – gpt2 |  | 0.80 | 0.32 | 0.35 | 0.19 | 0.15 |
| pythia-410m – gpt2 |  | 0.85 | 0.47 | 0.35 | 0.19 | 0.15 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H68.1 | median CKA over unrelated pairs 0.84 | ≥ 0.5 | **HELD** |
| H68.2 | tied axis excess 0.78 against a largest unrelated excess of 0.20 (3.9×) | ≥ 3× | **HELD** |
| H68.3 | median Procrustes held-out R² over unrelated pairs 0.46 | ≥ 0.3 | **HELD** |

**Reading.** For concepts in context, independently trained models share:
- the **shape** of the concept space (CKA 0.84, higher than for static embeddings);
- a **common frame up to rotation** (Procrustes R² 0.46).

They do **not** share raw coordinates: the best neuron-to-neuron correlation barely exceeds a shuffle (excess ≤ 0.20).

A model and its own fine-tune share coordinates almost perfectly (axis 0.97, CKA 0.99). Shared axes are an artefact of shared training history; shared shape is a property of the concepts. This is C34, as amended after Spike 64, now confirmed in context.
