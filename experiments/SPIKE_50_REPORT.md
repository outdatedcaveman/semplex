# Spike 50: A graded consensus law. Does the share of minimum circuits predict the net everywhere?

**Date:** 2026-11-16 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 49 (on inputs forced by every minimum circuit, nets output the forced value 98–99% of the time; on unforced inputs they agree with the majority of 5 sampled minimum circuits 85–86% of the time). **Gap:** A4 (one predictor for the net's held-out outputs).

## Conjecture C23 (graded consensus)

For a held-out input x, let p(x) be the share of minimum-cost circuits consistent with the seen labels that output 1 at x, and q(x) the share of independently trained nets that output 1. Then q tracks p: inputs on which minimum circuits split evenly are the inputs on which training seeds split, and the majority of minimum circuits predicts the net on all held-out inputs better than the kernel does.

## Design

- **Cells** (fresh targets and care sets, as Spike 48's generator; targets seed 5,000 + cell index, care sets 5,050 + cell index):

| Cell | n | Seen | Seeds per task |
|---|---|---|---|
| `n8_s64` | 8 | 64 | 10 |
| `n8_s96` | 8 | 96 | 10 |
| `n10_s80` | 10 | 80 | 10 |

- **Nets, kernel:** `spike36.train` (tanh, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps), seed 5,070 + cell index; `spike36.ntk` ridge. 100 targets per cell; only fitted nets count.
- **p(x), estimated.** `compile_partial` (|w| ≤ 4) gives the minimum cost; 20 minimum-cost nets are sampled with random linear objectives (`rand_obj` 0–19, 3 s each) and p̂(x) is the share outputting 1. **This is not a uniform sample of minimum circuits**: random objectives favour extreme weight vectors. The estimate is stated as such.
- **q(x)** = share of fitted seeds outputting 1.
- **Predictors of each net's output on held-out inputs:** `graded` = [p̂ > 0.5] (ties broken by the kernel); `kernel` = ridge NTK prediction.
- **Measures:**
  - `agree_graded`, `agree_kernel`: per (net, held-out input) agreement;
  - `rho`: Spearman correlation of p̂ and q over held-out inputs with 0 < p̂ < 1, pooled per cell;
  - `split_seed_rate`: among inputs with 0.4 ≤ p̂ ≤ 0.6, the mean of min(q, 1 − q), against the same quantity among inputs with p̂ ∈ {0, 1}.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H50.1 | The graded consensus predicts the net on all held-out inputs | `agree_graded` ≥ 0.93 in every cell | < 0.88 in any cell |
| H50.2 | It beats the kernel | `agree_graded` − `agree_kernel` ≥ +0.03 in every cell | ≤ 0 in any cell |
| H50.3 | Seed disagreement follows circuit disagreement | `rho` ≥ 0.40 in every cell | ≤ 0.10 in any cell |
| H50.4 | Evenly split inputs are where seeds split | `split_seed_rate`(0.4–0.6) − `split_seed_rate`({0,1}) ≥ +0.10 in every cell | ≤ 0 in any cell |

Anything else is *neither*. H50.1 and H50.2 together are gap A4's closing test at n = 8. C23 is supported if H50.1–H50.3 hold, refuted if H50.1 or H50.3 is broken.

**Guards.** No verdict for a cell if fewer than 90% of nets fit, fewer than 90% of tasks compile, or fewer than 500 held-out inputs have 0 < p̂ < 1.

## Commands

```
python -m experiments.spike50 tasks
python -m experiments.spike50 occam CELL
python -m experiments.spike50 nets CELL
python -m experiments.spike50 analyse
```

## Results

(To be filled after the runs.)
