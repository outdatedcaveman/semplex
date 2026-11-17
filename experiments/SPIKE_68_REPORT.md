# Spike 68: Shared shape and shared axes for concepts in context, with a tied-basis control (C34)

**Date:** 2026-11-17 · **Status:** pre-registered (no run) · **Follows:** Spikes 61 and 64 (P191, P195: lexicons share shape and a common frame up to one rotation per model, but not raw axes); `charter/FOUNDATIONS.md` §11.1 (C34). Numbered 68 because §12 reserved 65–67 for the continuous and arithmetic tests.

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

## Commands

```
python -m experiments.spike68 run
python -m experiments.spike68 analyse
```

## Results

(Not run.)
