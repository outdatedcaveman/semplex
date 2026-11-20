# Spike 33: What in training beats the init-prior posterior? Feature learning vs the information tilt (C18)

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 2baa6c2; results below) · **Follows:** Spike 32 (trained nets beat the exact init-prior Bayes posterior in 24/24 activations; C18: the step-level information tilt carries the gain)

## Disclosure before registration

The Spike 32 rows, already reported, show the *untilted* ReLU family also beating the posterior: ReLU balanced 0.557 against posterior 0.533. C18 in its simple form ("no tilt ⇒ no gain") is therefore already strained by data I have seen. I do not register a hypothesis on those numbers. This spike is a fresh **intervention**. Tasks, masks, seeds and the posterior stay fixed, and only the training dynamics change. It separates two candidates:
- **(i) the information tilt** (C18);
- **(ii) feature learning as such**: the first layer moving at all, whatever its tilt.

## Design

Six activations: tanh, sigmoid and erf (tilted, λ ≈ 11.5–12.8), and ReLU, GELU and |x| (untilted, λ ≤ 2.1). The 1,280 tasks per activation are those of Spikes 29–32: same elements, masks and seeds. The posterior predictions are Spike 32's, unchanged.

| Arm | Training |
|---|---|
| C, reference | Spike 29 arm B (AdamW lr 0.03, wd 0.03, width 8, 3,000 steps), rerun deterministically to record units and movement. The analysis aborts unless its held-out predictions equal Spike 30's exactly |
| D, slowed features | as C, but the first layer's (W₁, b₁) AdamW step is multiplied by 0.1 |
| G, plain GD | full-batch GD, lr 0.3, wd 0.003, no momentum (as Spike 21) |
| A, no feature learning | first layer frozen at init, width 64; only (W₂, b₂) trained (AdamW lr 0.03, wd 0.03); out-scale 0.5·√(8/64) |

For every (activation, arm) cell, measured on fitted nets only:
- **gain over the posterior** = net balanced accuracy − posterior balanced accuracy;
- **λ**, fitted with the Spike 22 law on each cell's own trained units (this task setting: 12 seen inputs), using I(t; target). For arm C this replaces the full-data λ of Spike 29;
- **feature movement** = the fraction of units whose threshold function changed from init.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H33.1 | **Without feature learning there is no gain over the posterior.** Arm A | mean gain over the 6 activations ≤ +0.005 | mean gain ≥ arm C's mean gain − 0.005 |
| H33.2 | **C18: the gain follows the tilt.** Across the 18 trained-feature cells (arms C, D, G) | Spearman ρ(λ, gain) ≥ 0.5 | ρ ≤ 0 |
| H33.3 | **Rival: the gain follows feature movement, whatever the tilt** | ρ(movement, gain) ≥ 0.5 over the same 18 cells | ρ ≤ 0 |
| H33.4 | **Untilted activations gain as much as tilted ones** in arm C | mean gain (ReLU, GELU, \|x\|) ≥ 0.8 × mean gain (tanh, sigmoid, erf) | ≤ 0.5 × |

H33.2 and H33.3 are rivals. If H33.3 holds and H33.2 does not, C18 is refuted: what beats Bayes-under-init is feature learning, not its information tilt.

---

## Results

Raw data in `results/spike33_raw/`, analysis in `results/spike33.json`. Every cell fits ≥ 98.9% of nets.

**Deviation from the pre-registration (recorded before verdicts).** The pre-registered check required the arm C rerun to reproduce Spike 30's held-out predictions *exactly*. It reproduced 4 of 6 activations exactly. The other two differ by 1 bit (ReLU) and 2 bits (|x|) out of 5,120. The cause is float32 rounding order in the update: the rerun computes p − (a + b), the original p − a − b, and that can flip a net sitting at a ReLU kink. The analysis was changed to tolerate ≤ 5 differing bits and to use arm C's own predictions, so its λ, movement and accuracy come from the same nets. A 3-bit difference cannot move any statistic below.

| Activation | Arm C gain (λ) | D, slowed features | G, plain GD | A, frozen features |
|---|---|---|---|---|
| tanh | +0.030 (10.6) | +0.022 (8.8) | +0.028 (10.2) | −0.017 (−0.1) |
| sigmoid | +0.042 (11.2) | +0.042 (9.9) | +0.038 (10.0) | −0.004 (0.0) |
| erf | +0.024 (10.4) | +0.018 (8.8) | +0.022 (10.1) | −0.021 (0.0) |
| ReLU | +0.023 (1.2) | +0.018 (0.9) | +0.029 (1.0) | −0.005 (0.0) |
| GELU | +0.023 (2.2) | +0.013 (1.6) | +0.026 (2.1) | +0.002 (0.0) |
| \|x\| | +0.008 (−1.1) | +0.004 (−1.3) | +0.021 (−2.0) | −0.016 (−0.1) |

Gain = balanced held-out accuracy minus that of the exact init-prior posterior (Spike 32), on identical tasks.

### Verdicts

| # | Verdict |
|---|---|
| H33.1 | **Held.** Frozen features give a mean gain of −0.010: *below* the posterior. Arm C's mean is +0.025. |
| H33.2 | **Held.** ρ(λ, gain) = 0.67 over the 18 trained-feature cells. |
| H33.3 | **Held.** ρ(movement, gain) = 0.59 over the same cells. |
| H33.4 | **Neither held nor broken.** Untilted / tilted gain ratio = 0.57. |

The rivals H33.2 and H33.3 both held, because across cells λ and movement are themselves correlated (ρ = 0.77). The pre-registered test does not separate them.

### Exploratory (post hoc): within each activation

Demeaning per activation, so that the arms vary the training while the activation is fixed: ρ(movement, gain) = **0.58** and ρ(λ, gain) = **0.27**. Slowing feature learning (D) lowers the gain in 5 of 6 activations, while λ barely changes. |x| has a *negative* tilt in every arm, yet plain GD gives it its largest gain (+0.021).

## Findings

**F1. Feature learning is necessary for the gain over Bayes-under-init.** With the first layer frozen, nets do *worse* than the exact init-prior posterior. With it trained, they do better in all 18 cells. The +2.5 points that beat the posterior come from the first layer moving.

**F2. The tilt does not obviously carry the gain.** Across activations, tilt and gain go together. But within an activation, the gain follows how much the features move more than how tilted they become, and the negative-tilt |x| gains under plain GD. C18 as stated ("the information tilt carries generalization beyond the init prior") is not supported, though it is not refuted either: the pre-registered test could not separate the two. The leading reading: *feature movement as such* improves on the init prior; the tilt is a by-product, in saturating activations, of that same movement.

**F3. Next test (Spike 34, proposed).** A within-activation dose–response separates the two cleanly. Scale the first layer's learning rate (0, 0.03, 0.1, 0.3, 1, 3) for each of the 6 activations. Pre-register that the gain tracks movement after partialling out λ, and not the reverse.
