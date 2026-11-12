# Spike 13: GD done properly; a discriminating test of abductive candidates A1, A2, A4

**Date:** 2026-11-12 · **Status:** pre-registered (written after calibration on disjoint elements, before any main run) · **Follows:** Spike 12; candidates in `charter/ABDUCTION.md` · **Prior-art check:** margin implicit bias (arXiv:2410.22069, 2406.10650, 2602.16340, 2611.01929) and incremental learning (2512.20607, 2302.11055) are known at the level of parameters and functions; we found no test of them against an exact list of circuit isomers.

## Root cause of Spike 12's GD failure (found during calibration)

Weight decay is applied as θ ← θ − lr·wd·θ. With lr = 1 and wd = 0.03, GD shrank the weights by 3% per step, against 0.09% per step for AdamW at lr 0.03. That pinned the network near zero: the loss stayed flat at 0.248 from step 3,000 to step 30,000, and fit stayed at 48% at widths 8 and 32. With wd = 0 or 0.003, the same runs fit 100%. **Spike 12's H12.2 verdict is withdrawn as uninformative: it compared AdamW with an over-regularized GD, not with GD.**

**Rule adopted here:** GD uses wd = 0.0009 / lr, so its per-step shrink equals AdamW's.

**Calibration** (`results/spike13_calibration.json`): 16 elements disjoint from the 48 scored, 10 seeds, 10,000 steps. Fit was 100% at every lr in {0.3, 1, 3, 10}. The rule fixed beforehand (largest fit, ties to the smaller lr) gives **lr = 0.3**.

## Environments (same 48 elements as Spike 12, 40 fresh seeds, 10,000 steps)

| Env | Width | Init | Optimizer |
|---|---|---|---|
| A8-10k | 8 | 0.5 | AdamW lr 0.03, wd 0.03 (Spike 12's W8 at matched steps) |
| G8-s0.1, G8-s0.5, G8-s2 | 8 | 0.1, 0.5, 2 | GD lr 0.3, wd 0.003 |
| G128-s0.5 | 128 | 0.5 | GD lr 0.3, wd 0.003 |

The readouts (R1, R2) and the invariance ratio are as in Spike 12. **Primary readout for every hypothesis: R2.**

## New predictors (fixed in advance, no fitted parameters; `cerp/unitgeom.py`)

- **S_m2** = log m₂(t1) + log m₂(t2), where m₂ is the ℓ2 max-margin of the unit over the 16 inputs (bias included in the norm).
- **S_minf**: the same with the ℓ∞ margin.
- **S_int** = −(minimal integer |w| + |T| of t1 + the same for t2), exact by MILP.
- **t\***: the threshold function(s) agreeing most with g, over *all* threshold functions.

## Hypotheses and kill criteria

| # | Candidate | Hypothesis | Held if | Broken if |
|---|---|---|---|---|
| H13.1 | — | With GD done properly, the core does not depend on the optimizer: ratio(A8-10k, G8-s0.5) | ≤ 1.5 | ≥ 3 |
| H13.2 | O6 | Under GD, S_agree's Spearman is higher at init 0.1 than at 2 | difference ≥ 0.1 | reversed |
| H13.3 | A2 | S_m2 > S_minf in G8-s0.5 **and** S_minf > S_m2 in A8-10k | both | both reversed |
| H13.4 | A2 | In each environment, the margin predictor matching the optimizer is ≥ S_agree | in A8-10k and G8-s0.5 | below S_agree − 0.1 in both |
| H13.5 | A1 | Share of runs whose core contains t\*, divided by the share of isomers containing t\* | ≥ 1.5 in every Spike 13 environment | ≤ 1 in any |
| H13.6 | A4 | S_int is the best of {S_m2, S_minf, S_int} in both A8-10k and G8-s0.5 | best in both | worst of the three in either |

Between thresholds, the verdict is "neither". Spike 12's AdamW environments are re-scored with the new predictors as a secondary, already-seen data set; those results do not decide any verdict.
