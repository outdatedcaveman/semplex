# Spike 13: GD done properly; a discriminating test of abductive candidates A1, A2, A4

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `587eb22`, after calibration on disjoint elements and before any main run · **Follows:** Spike 12; candidates in `charter/ABDUCTION.md` · **Prior-art check:** margin implicit bias (arXiv:2410.22069, 2406.10650, 2602.16340, 2611.01929) and incremental learning (2512.20607, 2302.11055) are known at the level of parameters and functions; we found no test of them against an exact list of circuit isomers.

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

## Results (`results/spike13.json`, raw counts in `results/spike13_raw/`; about 15 minutes wall time)

**Fit and faithfulness**

| Env | Fit | Still computes g with hard steps | Mean core size (R2 prefix) |
|---|---|---|---|
| A8-10k | 100% | 100% | 3.1 |
| G8-s0.1 / s0.5 / s2 | 99.9 / 100 / 100% | 94 / 92 / 93% | 3.8 |
| G128-s0.5 | 100% | **63%** | **10.4** |

**Predictors (median within-element Spearman, R2)**

| Env | S_vol | S_imb | S_agree | S_m2 | S_minf | S_int |
|---|---|---|---|---|---|---|
| A8-10k | 0.10 | 0.39 | **0.44** | 0.13 | 0.07 | 0.15 |
| G8-s0.1 | 0.17 | **0.27** | 0.25 | 0.17 | 0.15 | 0.17 |
| G8-s0.5 | 0.12 | **0.28** | 0.27 | 0.16 | 0.14 | 0.16 |
| G8-s2 | 0.10 | **0.30** | 0.28 | 0.16 | 0.15 | 0.18 |
| G128-s0.5 | 0.12 | **0.25** | 0.13 | 0.15 | 0.21 | 0.22 |

**A1: share of credited runs whose core contains t\*, against the share of isomers containing t\* (R2)**

| A8-10k | G8-s0.1 | G8-s0.5 | G8-s2 | G128-s0.5 | Spike 12 environments (re-scored) |
|---|---|---|---|---|---|
| 39% vs 10% (**3.8×**) | 31% vs 10% (3.1×) | 35% vs 10% (3.5×) | 36% vs 10% (3.6×) | 22% vs 12% (1.8×) | 3.2–3.9× (W8-GD: 4.7×) |

**Invariance (R2 ratio; 1 = indistinguishable from reseeding)**

| Pair | Ratio | Elements |
|---|---|---|
| A8-10k vs G8-s0.5 (optimizer) | 2.21 | 32 |
| Spike 12 W8 (3,000 steps) vs A8-10k (10,000 steps) | 1.16 | 37 |
| G8-s0.1 vs G8-s2 (init scale, GD) | 1.20 | 30 |
| G8-s0.5 vs G128-s0.5 (width, GD) | 3.76 | 17 |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H13.1 | **Neither** (ratio 2.21). The optimizer changes the core measurably; reseeding alone does not explain the difference. It is not a wholesale change either. |
| H13.2 | **Broken.** Under GD too, S_agree is not higher at small initialization (0.25 at 0.1 vs 0.28 at 2). The circuit is also invariant to initialization scale under GD (ratio 1.20). The linear-regime derivation is refuted without Adam, so O6 was not caused by Adam's normalization. |
| H13.3 | **Neither.** Under GD, ℓ2 beats ℓ∞ (0.16 vs 0.14) as A2 predicts. Under AdamW it does too (0.13 vs 0.07), against A2. No flip. Both margins are weak, and they are correlated 0.92 across units, so this test had low power. |
| H13.4 | **Broken.** The matching margin predictor is far below S_agree in both environments (AdamW: 0.07 vs 0.44; GD: 0.16 vs 0.27). |
| H13.5 | **Held.** The core contains the single best-agreeing threshold function 1.8–3.8× more often than chance over isomers, in every Spike 13 environment and in all 8 re-scored Spike 12 environments. |
| H13.6 | **Neither.** S_int is best under AdamW (0.15) and second under GD (0.158 vs 0.164). Both values are small. |

## Findings

**F1. The first step of greedy residual fitting (A1) is the one regularity that has survived every environment so far.** Across 13 environments (two optimizers, widths 8–1024, initialization scales 0.1–2), the learned core contains t\*, the threshold function that alone best approximates the target, about 3.5 times more often than a random minimal circuit would. This is the most stable effect found in Spikes 11–13. It is what A1 predicts, and none of A2, A4 or volume predicts it.

**F2. Margin and description-length explanations (A2, A4) fail as principal explanations here.** Their predictors carry rank correlations of 0.07–0.23, below agreement and imbalance everywhere at width 8. The optimizer flip that would have singled out A2 did not occur. Caveat: the theorems behind A2 concern the long-time limit of homogeneous networks without weight decay. 10,000 steps with tanh, biases and weight decay may be outside their reach, so A2 is not refuted in its own regime.

**F3. Initialization scale is irrelevant under both optimizers.** GD ratios across a 20× change in scale are 1.0–1.4, and AdamW's were 1.25–1.57 in Spike 12. Whatever selects the circuit is scale-free over this range. That rules out explanations that depend on a small-initialization (saddle) regime, including the standard derivation of A1. A1's prediction holds; its usual mechanism does not apply.

**F4. The optimizer matters; which predictor works best depends on it.** Under AdamW, agreement (0.44) beats imbalance (0.39). Under GD, imbalance is best (0.27–0.30) and agreement is close behind. GD's cores are larger (3.8 vs 3.1 units) and less threshold-like (92–94% faithful vs 100%).

**F5. Under GD, width is not innocuous.** At width 128, GD with this parametrization builds large cores (10.4 units) and only 63% of nets still compute g with hard steps. The comparison with width 8 (ratio 3.76) covers only 17 elements and uses a readout that fails for a third of the nets. Spike 12's width invariance (O3) was measured under AdamW and should be stated as AdamW-specific until GD is run in a regime where the circuit readout is faithful.

**F6. Spike 12's GD result is withdrawn** (root cause above). Spike 12's report and P061 stand for AdamW only.

## Update to the abductive picture (`charter/ABDUCTION.md`)

- **A1 survives**, sharpened: "the core contains the best single-unit approximation of the target" holds everywhere tested, but the textbook mechanism (small-initialization saddle escape) cannot be the reason (F3). A1 needs a scale-free mechanism; A6 (symmetry breaking at a rate set by the target's own statistics, which depends only on ratios) is the natural candidate.
- **A2 and A4 are demoted:** weak everywhere, and no flip.
- **Open:** what picks the *second* unit? t\* is in the core in about 35% of runs, so in most runs it is not, and agreement explains only part of the ranking.

## Proposed Spike 14 (to pre-register)

- **Full greedy A1:** given t\*, predict the second unit as the threshold function that best fits the residual (the inputs t\* gets wrong, weighted by the loss gradient), with no fitted parameters. Test whether it predicts the full isomer, not just t\*'s presence.
- **Timing (A1/A6):** record which units become threshold-stable first. A1 predicts t\* first; A6 predicts an order set by the target's Chow and Fourier spectrum, independent of scale.
- **Lazy bulk / rich core (A3):** distance moved against |output weight| at widths 128–1024.
- **Transfer:** run the surviving predictor on 5-input elements without changing it.

## Gaps

- 40 seeds per element; noise floor as in Spike 12.
- The ℓ2 and ℓ∞ margins are 0.92-correlated across units. The pre-registration did not quantify this power problem.
- G128's readout is unreliable (63% faithful).
