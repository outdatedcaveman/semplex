# Spike 47: Does the hidden layer collapse onto the cells of a minimum circuit?

**Date:** 2026-11-15 · **Status:** complete (pre-registered in the merge commit before training; results below) · **Follows:** Spike 36 (C19′ on clean targets) and Gemini's census G9 (all minimum circuits of every 4-input function, with their symmetry orbits). **Gaps:** A9 (what the hidden layer represents), A3 (mechanism), A10 (identifiability). **Direction:** R1 in `charter/PRIOR_ART.md`, restricted to what prior work does not cover.

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

`experiments/results/spike47.json`; per-net rows in `spike47_raw/rows.json`. All 1,280 nets fit. My independent enumeration of minimum circuits agrees with G9's count for all 128 targets, so both guards pass.

| Measure (step 3,000, contribution-weighted representation) | Value |
|---|---|
| Nets with CR_min ≥ 0.90 | 0.08% (1 of 1,280) |
| Median CR_min (best minimum circuit) | 0.555 |
| Median CR_best (best of all 441,330 two-hyperplane partitions) | 0.732 |
| Median CR_class (two cells by f) | 0.242 |
| Top-ranked partition is a minimum circuit of the target | 5.9% of nets (chance 0.0086%) |
| Median rank of the best minimum circuit among all partitions | 1302 of 441,330 |
| Median CR_min at steps 30 / 100 / 300 / 1,000 / 3,000 | 0.509 / 0.520 / 0.524 / 0.537 / 0.555 |

### Verdicts

- **H47.1: broken.** The hidden layer is a function of a minimum circuit's cell (CR_min ≥ 0.90) in 0.08% of nets; the bar for "broken" was below 40%.
- **H47.2: broken.** The best two-hyperplane partition is a minimum circuit of the target in 5.9% of nets (bar for "broken": below 30%). That is about 700 times chance, so minimum circuits are over-represented, but they are not what the layer settles on.
- **H47.3: neither.** CR_min rises by +0.035 from step 100 to step 3,000 (bars: ≥ +0.10 held, ≤ +0.02 broken).
- **C21: refuted.**

### Reading

1. **A width-8 hidden layer does not reduce to a minimum circuit.** The best minimum circuit explains 56% of the representation's variance. Even the best of all two-hyperplane partitions explains only 73%: the layer uses more than two directions.
2. **It does not collapse to the class either** (24%), as the argument in the Idea section requires.
3. **Minimum circuits are present but not dominant.** Their median rank is about 1,300 of 441,330 (top 0.3%). This agrees with Spikes 9 and 12: a minimum circuit sits inside the net as a core, and the remaining units do not vanish under this training recipe.
4. **Exploratory.** Targets with a single orbit of minimum circuits show *less* collapse (median 0.41) than targets with several (0.63), and the top partition is never a minimum circuit for them (0 of 500 nets, against 9.7%). More minimum circuits to choose from means a better best match, so this split mostly reflects the number of candidates, not identifiability.
5. Raw activations give the same picture (median 0.52; 6.0% top-is-minimum).

**What this rules out.** "The hidden layer represents the coarsest realizable sufficient partition" is false for over-wide nets under weight decay 0.03 and 3,000 steps. Function-level agreement with the minimum circuit on held-out inputs (C19′) therefore does not come from the representation becoming that circuit.

**Next.** The open question for gap A9 is the opposite one: how many hyperplanes does the layer effectively use, and does that number fall toward the minimum as weight decay, training time or width change? That is a dose–response, not a yes/no collapse.
