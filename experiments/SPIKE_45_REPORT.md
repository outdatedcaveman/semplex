# Spike 45: Does "feature learning moves toward the minimum circuit" hold outside its home setting?

**Date:** 2026-11-14 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 36 (C19′ replicated, but only for random two-unit threshold targets at n = 5, 6). **Gaps addressed:** A1 (other target classes), A2 (real data), part of D1.

## Question

C19′ says: where a trained net departs from its kernel's prediction on held-out inputs, it goes toward the minimum-circuit (Occam) completion. Spike 36 measured 73–81%. Does this hold for other kinds of target and for real data?

## Common protocol (as Spike 36, n = 6)

- **Nets:** two-layer tanh, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps, 10 seeds per task, logistic loss on the seen inputs. `spike36.train` is reused unchanged.
- **Kernel:** `spike36.ntk(6, "tanh")` with `spike36.kpred` (ridge on the seen inputs).
- **Occam:** minimum-cost layered threshold net (weights |w| ≤ 4) matching the seen labels. Costs tried in order: 1, then hidden widths 2, 3, 4, 5 (cost = width + 1), 10 s per solve. The completion is the majority vote of 3 nets sampled with random objectives at the minimum cost found. A task with no net found is *uncompiled* and excluded.
- **Measures**, on held-out inputs, over nets that fit their seen inputs:
  - `sides`: among held-out inputs where the net differs from the kernel prediction, the fraction where the Occam completion equals the net;
  - `agree_occam`, `agree_ntk`: agreement of the net with each predictor;
  - balanced accuracy of net, kernel and Occam against the truth.

## Arm S: four synthetic target classes

100 tasks per class; 48 of 64 inputs seen (one random care set per target); targets have 25–75% ones. Seeds 4,500 + class index.

| Class | Targets |
|---|---|
| S1 `cost4` | Random 3-hidden-unit step nets (weights in −3…3) that no 2-hidden-unit net with \|w\| ≤ 4 computes (solver returns unsat on the total function). |
| S2 `symmetric` | Functions of the Hamming weight, f(x) = g(\|x\|) with random g, that are not threshold functions. |
| S3 `noisy` | Spike 36's generator with a fresh seed; 5 of the 48 seen labels are flipped. Nets and Occam see the flipped labels. Truth on held-out inputs is the clean target. |
| S4 `dnf` | OR of 3 random terms, each an AND of 2–3 literals of random sign; not threshold functions. |

## Arm R: four real datasets

Datasets bundled with scikit-learn (no download): Breast Cancer (malignant vs benign), Wine (class 1 vs rest), Digits (digit ≥ 5), Diabetes (target above its median).

- **Task construction.** The 6 features with the largest absolute correlation with the label are binarized at their medians. Each observed 6-bit pattern is a cell, and its label is the majority label of its rows (tied cells are dropped). This defines a partial Boolean function on the observed cells. The feature choice uses all rows; it defines the task and is shared by all three predictors.
- **Splits.** 40 random splits per dataset: 75% of observed cells seen, 25% held out. Splits whose seen or held-out part has only one class are redrawn. Seed 4,550 + dataset index.
- Unobserved cells are neither trained on nor scored.
- **Task sizes, checked before any run (no outcomes seen):** observed cells / cells labelled 1: Breast Cancer 28 / 3, Wine 44 / 15, Digits 51 / 30, Diabetes 52 / 29. Breast Cancer is small and unbalanced; the disagreement guard below decides whether it yields a verdict.

## Hypotheses and kill criteria

Per class or dataset, `sides` is **held** at ≥ 0.65 (synthetic) or ≥ 0.60 (real), **broken** at ≤ 0.50, otherwise neither.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H45.1 | The Occam pull generalizes across synthetic classes | `sides` held in ≥ 3 of 4 classes | `sides` broken in ≥ 2 of 4 classes |
| H45.2 | The Occam pull holds on real data | `sides` held in ≥ 3 of 4 datasets | `sides` broken in ≥ 2 of 4 datasets |
| H45.3 | Occam predicts the net better than the kernel does | agree_occam − agree_ntk ≥ +0.02 in ≥ 6 of the 8 cells | the difference is ≤ 0 in ≥ 4 of the 8 cells |
| H45.4 | Training beats the kernel on real data | bal(net) − bal(kernel) ≥ +0.01 in ≥ 3 of 4 datasets | the difference is ≤ 0 in ≥ 3 of 4 datasets |

Anything else is *neither*.

**Guards.** A cell counts as *no verdict* (and counts against "held", not toward "broken") if fewer than 70% of its tasks compile, fewer than 90% of its nets fit, or it has fewer than 200 net–kernel disagreement points.

**What each outcome would mean.** If H45.1 and H45.2 hold, C19′ is a general statement and gap A3 (mechanism) is the next target. If the pull fails on a class, that class bounds the claim, and its features (cost, noise, symmetry) say where to look for the mechanism. If it fails on real data but holds on synthetic classes, the theory is a statement about clean low-cost targets only.

## Commands

```
python -m experiments.spike45 tasks
python -m experiments.spike45 occam CELL      # CELL in cost4 symmetric noisy dnf breast_cancer wine digits diabetes
python -m experiments.spike45 nets CELL
python -m experiments.spike45 analyse
```

## Results

(To be filled after the runs.)
