# Spike 33: What in training beats the init-prior posterior? Feature learning vs the information tilt (C18)

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spike 32 (trained nets beat the exact init-prior Bayes posterior in 24/24 activations; C18: the step-level information tilt carries the gain)

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
