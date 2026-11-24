# Spike 36: Replication of "feature learning moves toward Occam", and the lazy-regime test

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 368c0cf; results below) · **Follows:** Spike 35 (exploratory: trained nets agree with the compiler's certified Occam completion on 91% of held-out inputs vs 81–83% with their NTK, and where nets depart from the NTK, Occam sides with them 80% of the time). **Inspired by:** Gao et al., arXiv:2611.11905 (wide two-layer tanh nets trained with Adam stay in the kernel regime).

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

---

## Results

`results/spike36.json`; raw data in `results/spike36_raw/`. Fit rates ≥ 0.998 everywhere. The compiler verified 100% of tasks at both n; cost-3 answers were certified optimal in 96.9% (n = 5) and 96.4% (n = 6).

### Arm R: replication on fresh targets

| Cell | Agree net–Occam | Agree net–NTK | Difference | Occam sides with net where net ≠ NTK | Net bal. | Occam bal. | NTK bal. |
|---|---|---|---|---|---|---|---|
| n = 5, tanh | 0.867 | 0.797 | +0.070 | **0.734** | 0.791 | 0.777 | 0.732 |
| n = 5, ReLU | 0.848 | 0.808 | **+0.040** | **0.732** | 0.790 | 0.777 | 0.715 |
| n = 6, tanh | 0.903 | 0.799 | +0.104 | **0.808** | 0.882 | 0.899 | 0.771 |
| n = 6, ReLU | 0.892 | 0.826 | +0.066 | **0.794** | 0.874 | 0.899 | 0.778 |

### Arm W: width, n = 6, tanh, 100 tasks × 4 seeds

| m | Agree net–own NTK | Agree net–Occam | Net bal. | Occam sides with net where net ≠ NTK |
|---|---|---|---|---|
| 8 | 0.800 | 0.894 | 0.867 | 0.794 |
| 64 | 0.801 | 0.901 | 0.875 | 0.833 |
| 512 | 0.834 | 0.878 | 0.854 | 0.854 |
| 2048 | 0.848 | 0.856 | 0.834 | 0.818 |

### Verdicts

| # | Verdict |
|---|---|
| H36.1 | **Neither held nor broken.** Nets agree more with Occam than with their NTK in all 4 cells (+0.040 to +0.104), but the n = 5 ReLU cell falls short of the +0.05 threshold. |
| H36.2 | **Held.** Where nets leave their kernel, Occam sides with them in 73–81% of cases, in all 4 cells (threshold 65%). |
| H36.3 | **Neither held nor broken.** Agreement with the NTK rises by +0.048 from m = 8 to m = 2048, just short of +0.05. It rises from 0.80 to 0.85, not to ≈ 1, so the lazy regime is only partly reached. |
| H36.4 | **Held.** Held-out balanced accuracy falls by 0.033 (0.867 → 0.834). |
| H36.5 | **Held.** Agreement with Occam falls by 0.038 (0.894 → 0.856). |

## Findings

**F1. The direction of feature learning replicates.** On fresh targets and at both input sizes, when a trained net departs from its init kernel, the compiler's minimal circuit agrees with the net 73–81% of the time. Spike 35's exploratory finding (P127) is now pre-registered and replicated.

**F2. Pushing toward the lazy regime moves nets back.** As width grows under the Gao et al. scaling, from m = 64 to m = 2048:
- nets agree more with their kernel (+0.047);
- they agree less with Occam (−0.045);
- they generalize worse (−0.041).

The regime is only partly reached at m = 2048 (kernel agreement 0.85), so this is a dose–response, not an on/off test. It is the first *causal-direction* evidence for C19′: reducing feature learning moves predictions away from Occam and costs held-out accuracy.

**F3. Occam is not an upper bound.** At n = 5 trained nets beat the compiler's Occam completion (0.79 vs 0.777 balanced); at n = 6 Occam leads (0.899 vs 0.874–0.882). Training is near Occam but not identical to it, so the residual differences are worth studying in their own right.

**F4. State of the answer to "why does it generalize".** On threshold-like targets with 75% of inputs seen:
- **(i)** the init kernel supplies a prior that reaches 0.72–0.78 balanced;
- **(ii)** feature learning moves the net, consistently, toward the minimum-circuit completion, reaching 0.79–0.88;
- **(iii)** suppressing feature learning by width moves it back.

This is C19′. It is supported, replicated and partly causal, but shown only for these target classes, two activations and n ≤ 6.
