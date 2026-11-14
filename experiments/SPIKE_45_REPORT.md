# Spike 45: Does "feature learning moves toward the minimum circuit" hold outside its home setting?

**Date:** 2026-11-14 · **Status:** complete (pre-registered in 9a78ce0; results below) · **Follows:** Spike 36 (C19′ replicated, but only for random two-unit threshold targets at n = 5, 6). **Gaps addressed:** A1 (other target classes), A2 (real data), part of D1.

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

`experiments/results/spike45.json`; raw outputs in `spike45_raw/`. Every task compiled and every compiled net was verified on its seen inputs. All eight cells pass the guards.

**Deviation recorded.** A worker restart killed the Diabetes compilation part-way. It was rerun from scratch with the same code and tasks; no other cell was touched.

| Cell | `sides` | verdict | agree Occam | agree kernel | bal. net | bal. kernel | bal. Occam | mean cost | disagreements | fit |
|---|---|---|---|---|---|---|---|---|---|---|
| cost4 | 0.716 | **held** | 0.846 | 0.772 | 0.782 | 0.732 | 0.805 | 3.57 | 3621 | 0.993 |
| symmetric | 0.897 | **held** | 0.828 | 0.441 | 0.832 | 0.319 | 0.899 | 3.95 | 8492 | 0.949 |
| noisy | 0.582 | **neither** | 0.756 | 0.740 | 0.737 | 0.697 | 0.723 | 3.98 | 4099 | 0.984 |
| dnf | 0.668 | **held** | 0.900 | 0.904 | 0.933 | 0.926 | 0.890 | 3.10 | 1540 | 1.000 |
| breast_cancer | 0.291 | **broken** | 0.742 | 0.844 | 0.744 | 0.674 | 0.653 | 1.00 | 437 | 1.000 |
| wine | 0.741 | **held** | 0.930 | 0.891 | 0.814 | 0.887 | 0.782 | 2.05 | 478 | 1.000 |
| digits | 0.556 | **neither** | 0.734 | 0.767 | 0.687 | 0.712 | 0.667 | 3.90 | 1209 | 1.000 |
| diabetes | 0.450 | **broken** | 0.742 | 0.798 | 0.707 | 0.750 | 0.671 | 3.83 | 1030 | 0.983 |

### Verdicts

- **H45.1: held.** The Occam pull holds in 3 of 4 synthetic classes: cost-4 targets 0.72, symmetric 0.90, DNF 0.67. With 5 flipped labels it drops to 0.58 (neither).
- **H45.2: broken.** On real data the pull holds only for Wine (0.74). It is broken for Breast Cancer (0.29) and Diabetes (0.45), and neither for Digits (0.56).
- **H45.3: broken.** Occam predicts the net better than the kernel in only 4 of 8 cells (cost4 +0.07, symmetric +0.39, noisy +0.02, wine +0.04). The kernel is the better predictor for DNF (−0.004), Breast Cancer (−0.10), Digits (−0.03) and Diabetes (−0.06).
- **H45.4: broken.** Trained nets beat their kernel on held-out real cells only for Breast Cancer (+0.07). They are worse on Wine (−0.07), Digits (−0.03) and Diabetes (−0.04).

### Reading

1. **C19′ is a statement about clean, structured targets.** It extends beyond its home class (costlier circuits, symmetric functions, DNF). It does not extend to real data in this protocol.
2. **Label noise is the likely boundary.** The one synthetic class with noise is the weakest (0.58), and the real tasks are noisy by construction: a cell's label is a majority vote over overlapping classes. The exact-fit Occam completion has to spend circuit cost on the noise (mean cost 3.8–4.0 for noisy, Digits and Diabetes), and it generalizes worst of the three predictors in all four real cells.
3. **Symmetric targets are where the kernel fails outright** (balanced accuracy 0.32, below chance) and nets follow Occam almost entirely (0.90). This is the strongest single piece of evidence for the pull.
4. **On real data here, training does not help.** The kernel generalizes better than the trained net in 3 of 4 datasets. The +2–10 point gain from feature learning seen on synthetic targets is absent.
5. **Breast Cancer's cost is 1.0**: every task is fitted by a single threshold unit, so "minimum circuit" picks among many single units and is not a sharp prediction there.

**Limits.** Real tasks are six median-binarized features with majority labels per cell; 28–52 cells per dataset; splits of one dataset share a target. Noise was not varied as a dose. The conclusion "noise is the boundary" is a hypothesis from this pattern, not a tested result.

**Next.** A noise dose–response on synthetic targets, and a noise-tolerant Occam (minimum cost allowing errors, a two-part code) as the revised predictor.
