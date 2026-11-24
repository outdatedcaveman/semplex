# Spike 61: Do language models share a discrete set of lexical elements? Data-driven atoms across 14 models

**Date:** 2026-11-16 · **Status:** complete (pre-registered in 5a79341; results below) · **Follows:** Spike 59, where Wierzbicka's primes were not a privileged basis (P187) and the next step named was to learn universal atoms from data. Also follows Spike 53 (models share concept geometry, P181). Part of the lexical scale of the atlas programme (`charter/FOUNDATIONS.md` §9.4). **Gap:** A12.

## Question

Models share lexical geometry (P181), but shared geometry can be continuous: the same subspace, with no preferred axes. A periodic table needs more: a **discrete set of elements**, sparse directions that each model finds independently and that combine to make words.

The test compares two decompositions learned separately in each model, by how well their components match across models:
- **sparse atoms:** dictionary learning with each word built from 5 atoms;
- **dense principal directions** with the same number of components.

If models share discrete elements, the sparse atoms should match across models better than the principal directions.

## Data

- **Models:** the 14 models of Spike 53, **input** embeddings only. Falcon's output matrix is tied, and one matrix per model keeps the models independent.
- **Words:** entries of the Google 10,000 English words list (`experiments/data/google-10000-english-no-swears.txt`) that are alphabetic, at least 2 letters long, and single tokens in all 14 tokenizers. The same word list is used in every model.
- **Preprocessing:** rows are centred over the words and normalised to unit length.

## Method (per model, independently)

**Sparse atoms.**
- `sklearn.decomposition.MiniBatchDictionaryLearning` with 256 atoms, alpha 1.0, batch 256, `max_iter` 30, `random_state` 0.
- Each word is coded by orthogonal matching pursuit with exactly 5 nonzero atoms.
- The code matrix A_m is words × 256.

**Dense baseline.** The scores of each word on the top 256 principal components (PCA).

**Matching.**
- For each pair of models, take the absolute Pearson correlation between every atom's code column in one model and every atom's code column in the other, over words.
- Match the 256 atoms one-to-one (Hungarian algorithm) to maximise total correlation.
- Record the mean matched correlation.
- The same is done for PCA score columns.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H61.1 | **Models share discrete elements:** sparse atoms match across models better than dense directions | sparse mean matched correlation exceeds PCA's by ≥ 0.05 in ≥ 75% of the 91 model pairs | sparse ≤ PCA in ≥ 50% of pairs |
| H61.2 | **A substantial set of universal atoms exists** | ≥ 25% of a reference model's atoms (GPT-2, the oldest and smallest) match an atom with correlation ≥ 0.5 in ≥ 10 of the other 13 models | < 5% |

Anything else is *neither*.

**Guard.** No verdict with fewer than 2,000 shared words.

**Reported without criteria:**
- the universal atoms (top 10 words by loading), for inspection: are they semantic fields, primes-like operators, morphology, frequency?
- each word's 5-atom code as its "formula";
- atom co-activation and whether universal atoms form a hierarchy;
- a word-shuffle null for the matching statistic, which should be near the floor.

## What this cannot show

- Static embeddings; English; one dictionary size.
- Universality of sparse atoms could still reflect sparse structure in word co-occurrence statistics shared by all training corpora. That would itself be the "element" claim at the level of data, not of models.
- Interpreting atoms from top words is judgment and is reported as such.

## Commands

```
python -m experiments.spike61 run
python -m experiments.spike61 analyse
```

## Results

`experiments/results/spike61.json`; embedding rows in `spike61_raw/` (495 MB, git-ignored; `run` regenerates them). 6,163 shared words.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H61.1 | sparse beats dense by ≥ 0.05 in 12.1% of 91 pairs; sparse ≤ dense in 34.1%; median matched correlation sparse 0.148, dense 0.146 (shuffle floor 0.078) | ≥ 75% held; ≤ in ≥ 50% broken | **NEITHER** |
| H61.2 | 0 of 256 GPT-2 atoms match at r ≥ 0.5 in ≥ 10 other models | ≥ 25% held; < 5% broken | **BROKEN** |

**Exploratory control, after the verdicts** (`experiments/spike61_control.py`, `results/spike61_control.json`):
- **Shape is shared.** Rotation-invariant geometry is strongly shared: linear CKA between models is 0.42–0.79 (median 0.59), against 0.06 with words shuffled.
- **Axes are not.** Between GPT-2 and Qwen2.5-7B, the best atom matches are: maximum 0.65, 90th percentile 0.25, median 0.11. Only 2 atoms reach 0.5 and 15 reach 0.3.

**Reading.** The models' lexicons share their *shape* strongly but share *no preferred axes*, neither sparse atoms nor principal directions. At the level of word embeddings there is no discrete, model-independent set of elements: the shared structure is a continuous geometry, defined up to rotation.

This fits the automaton results (Spikes 57–58). There the invariant is not a basis but the *representation* (characters are basis-free), and the elements are operations (Krohn–Rhodes primes), not directions. **The lexical periodic table, if it exists, should be sought in the operations models apply to word representations, not in a basis for the words.**

**Sample formulas** (GPT-2 codes; atoms by index, none universal): "three" ≈ atom 7 (0.71) + small terms; "justice" = a single atom (102, weight 1.0), so the dictionary spends an atom on one word. Codes are idiosyncratic. Other examples are in the results file.
