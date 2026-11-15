# Spike 47: Does the hidden layer collapse onto the cells of a minimum circuit?

**Date:** 2026-11-15 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 36 (C19′ on clean targets) and Gemini's census G9 (all minimum circuits of every 4-input function, with their symmetry orbits). **Gaps:** A9 (what the hidden layer represents), A3 (mechanism), A10 (identifiability). **Direction:** R1 in `charter/PRIOR_ART.md`, restricted to what prior work does not cover.

## Idea

Neural collapse says the last hidden layer of a trained classifier becomes a function of the class alone: the coarsest partition of inputs that determines the answer (the Bayes quotient; Sevetlidis 2606.04045). For a non-threshold Boolean function and one hidden layer, that is impossible: if every hidden unit were constant on each class, the function would be a threshold function. The coarsest partitions a single hidden layer *can* realize while still determining the answer are the cell partitions of **minimum circuits** (two hyperplanes, at most four cells, for cost-3 functions).

**Conjecture C21 (constrained collapse).** After training, the hidden layer of an over-wide net is, to a good approximation, a function of the cell of one minimum circuit of the target. The collapse continues after the net has fitted the data.

**Prior art checked (titles and abstracts only):** neural collapse in intermediate layers (2308.02760), in shallow ReLU nets for separable data (2510.21078), reviews (2206.04041). None states collapse onto a minimum-circuit partition when class collapse is impossible.

## Design

- **Targets.** All 128 symmetry classes of 4-input functions with minimum cost 3 (one representative each, from the atlas / G9). The full truth table is the training set (16 inputs): this is a question about representation, not about held-out prediction.
- **Nets.** Two-layer tanh, width 8, the Spike 36 recipe (AdamW lr 0.03, wd 0.03, logistic loss, initialization N(0, 0.5²)), 10 seeds per target, seed 4,700. Weights are saved at steps 30, 100, 300, 1,000, 3,000. Only nets that fit all 16 inputs at step 3,000 are analysed.
- **Representation.** Z = hidden activations times outgoing weights (each unit's contribution to the logit), a 16 × 8 matrix. Secondary: raw activations H.
- **Collapse ratio.** For a partition π of the 16 inputs, CR(π) = the fraction of the variance of Z (around its mean) explained by cell means.
- **Partitions.**
  - `min`: for each minimum circuit of the target (a pair of threshold functions, taken up to complement, whose two-bit cell pattern determines f through a threshold gate), its cell partition. Enumerated independently here and checked against G9's counts. CR_min = the largest CR over the target's minimum circuits.
  - `all`: every pair of distinct non-constant 4-input threshold functions up to complement (about 441,000 partitions). CR_best = the largest CR over all of them.
  - `class`: the two-cell partition by f (for reference; C21 says this cannot be reached).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H47.1 | The hidden layer is nearly a function of a minimum circuit's cell | CR_min ≥ 0.90 in ≥ 70% of nets at step 3,000 | in < 40% of nets |
| H47.2 | Specificity: among all two-hyperplane partitions, the best one is a minimum circuit of the target | the top-ranked partition is a minimum circuit of f in ≥ 60% of nets | in < 30% of nets |
| H47.3 | Collapse continues after fitting | median CR_min at step 3,000 minus at step 100 ≥ +0.10 | ≤ +0.02 |

Anything else is *neither*. C21 is supported if H47.1 and H47.2 hold, and refuted if either is broken.

**Guards.** No verdict if fewer than 90% of nets fit, or if the independent enumeration of minimum circuits disagrees with G9's count for any target (the disagreement is then the result).

**Chance level for H47.2.** A target has between about 150 and 1,400 minimum circuits among the 441,000 partitions, so a random partition is a minimum circuit well under 1% of the time; the exact rate is reported.

**Design check before any training (no outcomes seen):** my enumeration of minimum circuits matches G9's count on the first 12 targets, and the collapse measure returns 1.0 on a planted partition.

**Reported without criteria:** the same measures on raw activations H; CR_class; CR_min split by whether the target has one symmetry orbit of minimum circuits or several (G9: 50 vs 78 classes); the number of cells of the chosen partition.

## Commands

```
python -m experiments.spike47 run
python -m experiments.spike47 analyse
```

## Results

(To be filled after the runs.)
