# Spike 54: Do semantic product concepts compose as tensor products in model activations?

**Date:** 2026-11-16 · **Status:** pre-registered (no analysis run) · **Follows:** Spike 53, which refuted C29's tensor row for *lexical* composition (P180: in static embeddings, month × form and weekday × form are additive). **Conjecture:** C29, product row.

## Question

Spike 53 tested products of a meaning and a spelling (January / Jan). Those live in the lexicon, where a direct sum is the natural encoding. The product row of C29 is about *semantic* products, built in context: "Monday morning", "early January", "last Friday". Is a semantic product a tensor product of its factors' representations, or again a sum?

## Data: public sparse-autoencoder maps (Neuronpedia)

No model is run here. Neuronpedia's public endpoint `POST /api/search-topk-by-token` returns, for any text, the 20 most active features of a published sparse autoencoder at every token. Defaults are used: `numResults` 20, `densityThreshold` 0.01 (features active on more than 1% of tokens are dropped), and beginning-of-sequence tokens are ignored.

**Sources (7; all answered a test call before registration):**
- gpt2-small 4-res-jb, 8-res-jb, 10-res-jb
- gemma-2-2b 12-gemmascope-res-16k, 20-gemmascope-res-16k
- gemma-3-1b 13-gemmascope-2-res-16k
- llama3.1-8b 16-llamascope-res-32k

**Representation of a phrase.** Take the sparse vector of feature activations at the phrase's last token. The phrase is the last word of a sentence. Sum over two sentence templates, then normalise to unit length.

**Families (products; the first factor is cyclic):**

| Family | Factors | Templates (last token in bold) |
|---|---|---|
| weekday × time of day | {Monday … Sunday} × {morning, afternoon, evening, night} (7 × 4) | "It happened on Monday **morning**", "We met on Monday **morning**" |
| month × part | {January … December} × {early, late} (12 × 2) | "It happened in early **January**", "We met in early **January**" |
| weekday × direction | {Monday … Sunday} × {last, next} (7 × 2) | "It happened last **Monday**", "We met last **Monday**" |

The same two templates are used for every cell; only the factor words change.

**Token rule.** A case (source × family) is used only if, for every phrase, the last token is the whole last word (token string equal to " " + word).

## Statistics (as in Spike 53)

1. **Decomposition.** x_ij = μ + a_i + b_j + r_ij, where i is the cyclic factor.
2. **Additive cycle.** The cyclic R² of the rows a_i, against 10,000 relabellings of i (seed 5,400).
3. **Tensor cycle.** The cyclic R² of the interaction rows r_i = (r_i1, …, r_im) concatenated over j, against the same null. The tensor product predicts that the interaction carries the first factor's cycle. A direct sum predicts that it does not.
4. **Relative interaction.** ‖r‖² / ‖x − μ‖², divided by its no-structure value (n−1)(m−1)/(nm−1). In Spike 53 (lexical) the median was **0.543**.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H54.1 | The cyclic factor is a circle in context too (additive part) | p < 0.01 in ≥ 75% of cases | < 50% |
| H54.2 | **Semantic products are tensor products** (interaction carries the cycle) | p < 0.01 in ≥ 50% of cases | ≤ 20% |
| H54.3 | Contextual composition is more interactive than lexical | median relative interaction ≥ 0.643 (Spike 53 + 0.1) | ≤ 0.543 |

Anything else is *neither*.

**Reading.**
- If H54.2 holds, C29's product row stands for semantic products, and Spike 53's refutation is confined to lexical forms.
- If H54.2 is broken, composition is a sum in context too. The row is then refuted for these families, and the theory needs a different account of composition.

**Guard.** No verdict with fewer than 12 usable cases.

**Reported without criteria:** results by source and family, and the cyclic R² of the second factor where it has 4 levels (times of day).

## What this cannot show

- Top-20 sparse features are a truncated view of the residual stream. A tensor component spread over many weak features would be missed.
- A sparse autoencoder may learn conjunction features ("Monday-morning") by design, and that would favour an interaction.
- Three families, seven sources.

## Commands

```
python -m experiments.spike54 run
python -m experiments.spike54 analyse
```

## Results

(Not run.)
