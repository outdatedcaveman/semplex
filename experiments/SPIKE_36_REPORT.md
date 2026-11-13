# Spike 36: Replication of "feature learning moves toward Occam", and the lazy-regime test

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spike 35 (exploratory: trained nets agree with the compiler's certified Occam completion on 91% of held-out inputs vs 81–83% with their NTK, and where nets depart from the NTK, Occam sides with them 80% of the time). **Inspired by:** Gao et al., arXiv:2611.11905 (wide two-layer tanh nets trained with Adam stay in the kernel regime).

## Conjecture under test, C19′

Gradient training starts from the init-kernel prior. *Feature learning* then moves the net toward the minimum-circuit (Occam) completion.

Two predictions follow:
1. The Spike 35 pattern replicates on fresh targets and at another input size.
2. Removing feature learning by going to the lazy regime (large width, η ∝ 1/√m, per Gao et al.) moves nets back toward their kernel and costs held-out accuracy.

## Arm R: replication (fresh data)

- **Settings.** n = 6 (48 of 64 seen) and n = 5 (24 of 32 seen).
- **Targets.** For each n, 150 new targets from Spike 35's generator: random 2-hidden-unit step nets with a kernel-checked total not-threshold certificate and 25–75% ones. Seeds 3,600 (n = 6) and 3,650 (n = 5).
- **Tasks.** Two random care sets per target: 300 tasks per n.
- **Methods.** Occam compilation with partial certificates and a 5-sample vote. Width-8 NTK kernel ridge for tanh and ReLU. Trained width-8 nets, tanh and ReLU, 10 seeds per task, AdamW lr 0.03, wd 0.03, 3,000 steps. Fresh seeds throughout.

## Arm W: width (lazy regime)

- **Tasks.** n = 6, the first 100 tasks of arm R; tanh; 4 seeds per task.
- **Widths.** m ∈ {8, 64, 512, 2048}.
- **Training.** AdamW with lr = 0.03·√(8/m), wd 0.03, output-weight init scale 0.5·√(8/m), 3,000 steps.
- **Kernel.** Each width is compared with its own init NTK, Θ_m = m·E[φφ′] + 2·E[φ̇φ̇′](x·x′ + 1) + 1, by Monte Carlo.

Metrics are balanced accuracy and agreement on held-out inputs, using fitted nets only.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H36.1 | **Nets agree more with Occam than with their NTK** | agree(net, Occam) − agree(net, NTK) ≥ +0.05 for tanh and ReLU at both n (4 cells) | ≤ 0 in any cell |
| H36.2 | **Departures from the kernel go toward Occam** | where net ≠ NTK, Occam sides with the net ≥ 65% in all 4 cells | ≤ 50% in any cell |
| H36.3 | **Laziness restores the kernel** | agree(net, own NTK) at m = 2048 minus at m = 8 ≥ +0.05 | ≤ 0 |
| H36.4 | **Laziness costs generalization** | held-out balanced accuracy at m = 2048 ≤ that at m = 8 − 0.03 | ≥ that at m = 8 |
| H36.5 | **Laziness moves nets away from Occam** | agree(net, Occam) at m = 2048 ≤ that at m = 8 − 0.03 | ≥ that at m = 8 |

H36.3–H36.5 are the causal half. If the width arm shows no laziness effect (H36.3 broken), the regime was not reached, and H36.4–H36.5 are uninformative rather than refuting.
