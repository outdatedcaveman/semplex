# Spike 15: The definitive transfer test of the Curie principle

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `eadda15` before any run on p = 61. The pilots used primes 23 and 59, whose quotient groups Z_p^*/±1 are cyclic of prime order (11 and 29), so they carry **no** information about subgroup structure; only training mechanics and sparsity were inspected. The test prime is 61, so the quotient has order 30 and subgroups of orders 2, 3, 5, 6, 10 and 15. No run on it has been made.

## Why this is the definitive test

Spike 14 found the Curie bias in one task family (4-input Boolean functions) with one architecture family. A principle stated purely in terms of a task's symmetry group should hold wherever the training map is equivariant under that group, in a different domain and a different architecture, and it should predict something that nothing else does.

### Arm A: modular addition (a different domain and architecture)

- **Model:** one-hot tokens, logits(a, b) = U·relu(E1[a] + E2[b]) with 128 hidden units, full data, AdamW (lr 0.01, weight decay 1), 2,000 steps, 96 models.
- **Symmetry:** tokens are unstructured, so every permutation of Z_61 applied jointly to inputs and outputs preserves the initialization law and the architecture. The automorphisms a ↦ ua of addition preserve the task. Theorem 15's argument carries over unchanged: the *law* of the learned mechanism is invariant under multiplication by units. These act on Fourier frequencies by k ↦ u⁻¹k, so the group acting on frequency profiles is Z_61^*/±1 (cyclic, order 30).
- **Mechanism readout:** the Fourier power profile of the first-layer weights over the 30 frequencies (pilots show networks spread power over most frequencies, so a profile is used rather than a sparse set).
- **The risky prediction:** nothing about *addition* singles out multiplicative structure. Additive features, not multiplicative ones, solve the task. Yet the Curie principle says each individual run should break the task's symmetry as little as possible. So its power profile should be closer to *constant on cosets of multiplicative subgroups* than its own values arranged at random.
- **Statistic:** for subgroup H, R_H = within-coset variance / total variance of the profile. Its percentile is taken against 2,000 random permutations of the same profile. With no structure the percentile is uniform with mean 0.5.
- **Calibration control (adversarial):** the same statistic on *fake* cosets, fixed random partitions of the frequencies into blocks of the same sizes. It must give a mean of 0.5. If it does not, the statistic is broken and arm A is void.

### Arm B: generalization as symmetry inheritance (other architectures)

- **Tasks:** 240 partial 4-input tasks, 40 for each of six symmetry groups H (swap two inputs, cyclic shift, reversal, all permutations, global negation, two disjoint swaps). Each task is H-invariant by construction: the target and the care set are unions of H-orbits of inputs.
- **Cells:** tanh and ReLU, width 8 and 64, AdamW and GD. Five seeds per task.
- **The question that separates symmetry from simplicity:** among runs that learn a *cheapest* completion, on tasks where some but not all cheapest completions are H-invariant, how often is the learned completion H-invariant? Compare with q, the share of cheapest completions that are invariant. Equally cheap means the simplicity bias cannot be the explanation.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H15.0 | (Validity) The statistic is calibrated: fake partitions give mean percentile 0.5 | every fake partition in [0.45, 0.55] | any outside [0.4, 0.6] → arm A void |
| H15.1 | **Curie in modular addition:** profiles are closer to coset-constant for real multiplicative subgroups | mean percentile ≤ 0.40 for the subgroups of order 2 and 3, one-sided p < 0.01 | mean percentile ≥ 0.50 for every subgroup |
| H15.2 | Equivariance analogue: the *mean* profile over models is flat, much flatter than individual profiles | mean-profile CV ≤ 0.25 × mean per-model CV | ≥ 0.5 × |
| H15.3 | **Symmetry inheritance across architectures:** on equally cheap completions, the learned one is H-invariant more often than its share q | observed − expected ≥ 0.10 and p < 0.01 (all groups pooled) in every one of the six cells | observed ≤ expected in 3 or more cells |
| H15.4 | Inheritance holds for each symmetry group separately (pooled over cells) | observed > expected for all six groups | observed < expected for 2 or more groups |

Between thresholds, the verdict is "neither". Runs on the same task are not independent, so z-values are optimistic; arm B also reports per-group results to show the effect is not carried by one group.

## Results (`results/spike15.json`, raw data in `results/spike15_raw/`)

### Arm A: modular addition, p = 61, 96 models (all at 100% accuracy)

| Subgroup order | 2 | 3 | 5 | 6 | 10 | 15 |
|---|---|---|---|---|---|---|
| Real multiplicative cosets: mean percentile (one-sided p) | 0.439 (0.018) | 0.509 (0.62) | 0.450 (0.036) | 0.515 (0.68) | 0.431 (0.008) | 0.483 (0.28) |
| Fake partitions, same block sizes (calibration) | 0.521 | 0.515 | 0.543 | 0.550 | 0.514 | 0.481 |

Mean-profile coefficient of variation: 0.059. Per-model: 0.503.

### Arm B: symmetric partial tasks; learned completion H-invariant vs share q of equally cheap completions that are

| Cell | Fit | Learned a cheapest completion | Runs scored | Expected (q) | Observed | z |
|---|---|---|---|---|---|---|
| tanh-W8-adam | 1.000 | 0.949 | 972 | 0.18 | **0.81** | 57 |
| tanh-W64-adam | 1.000 | 0.963 | 975 | 0.18 | **0.82** | 57 |
| relu-W8-adam | 0.996 | 0.945 | 976 | 0.19 | **0.82** | 57 |
| relu-W64-adam | 1.000 | 0.939 | 973 | 0.18 | **0.83** | 58 |
| tanh-W8-gd | 1.000 | 0.980 | 987 | 0.18 | **0.93** | 68 |
| relu-W8-gd | 0.998 | 0.976 | 996 | 0.19 | **0.92** | 67 |

Pooled over cells, by symmetry group:

| Group | Runs | Expected | Observed |
|---|---|---|---|
| swap01 | 864 | 0.40 | **0.92** |
| cyclic4 | 1070 | 0.08 | **0.76** |
| reverse | 1055 | 0.22 | **0.88** |
| S4 | 833 | 0.08 | **0.86** |
| global_negation | 1182 | 0.08 | **0.84** |
| swap01_x_swap23 | 875 | 0.30 | **0.90** |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H15.0 | **Neither (statistic usable, marginally calibrated).** Fake partitions give 0.481–0.550; one value (0.5501) is just outside the "held" band but well inside the "void" limits. |
| H15.1 | **Neither: no detectable Curie bias in modular addition.** The order-2 subgroup gives 0.439 (bar: ≤ 0.40 with p < 0.01) and order 3 gives 0.509. Three subgroups lean the predicted way (p = 0.008–0.04), but none survives correction for six tests, and the fake partitions lean the other way by a similar amount. The pre-registered transfer to a new domain **did not succeed.** |
| H15.2 | **Held.** The mean profile over models is 8.6× flatter than individual profiles (ratio 0.12 ≤ 0.25), as the equivariance analogue requires. |
| H15.3 | **Held, decisively.** In every one of six cells (tanh and ReLU, widths 8 and 64, AdamW and GD), the learned completion keeps the task's symmetry 81–93% of the time, against 18% for equally cheap completions (z ≈ 57–68, optimistic because runs share tasks). |
| H15.4 | **Held.** Every symmetry group separately: observed far above expected. |

## Findings

**F1. Generalization as symmetry inheritance holds across architectures, activations, widths and optimizers.** When a partial task has a symmetry, trained networks fill in the missing inputs symmetrically 4–5 times more often than simplicity alone predicts. This is T4 of `charter/PROGRAM_SYMMETRY.md`, now with a pre-registered test in six cells and six groups. GD inherits more than AdamW (0.92–0.93 vs 0.81–0.83); width does not matter (8 vs 64).

**F2. The Curie bias at the level of mechanisms did not transfer to modular addition, at least not in the form tested.** Individual frequency profiles are no more constant on multiplicative cosets than chance allows, although the ensemble is flat (equivariance holds). Three readings, not decided here:
1. The principle is about *what is computed* (functions, F1), not about internal mechanisms in general. The Boolean circuit result (Spike 14) would then reflect that, in that family, symmetric circuits compute symmetric functions.
2. The statistic was wrong for this domain. Networks here use nearly all frequencies, and a near-flat profile is already almost invariant, so departures from flatness may be noise.
3. The relevant symmetry here (multiplication) does not act on the training data in a way the network can "see". In arm B the symmetry is a stabilizer of the observed data; in arm A it is a symmetry of the full task that every finite network must break to compute anything.

Reading 3 makes a testable distinction: **the Curie bias acts on symmetries of the data the network is fitting, not on abstract symmetries of the task.** It is the sharpest next hypothesis.

**F3. The kernel-limit alternative must be ruled out before F1 is called a new principle.** A network at infinite width trained by GD behaves like kernel regression with a symmetric kernel, and kernel interpolation of symmetric data is exactly symmetric. That would explain symmetry inheritance without any new principle. Two observations argue against it being the whole story: inheritance does not grow from width 8 to 64, and it is strongest at width 8 under GD, far from the kernel regime. Neither is a test. Spike 16 will compare the learned completion with the kernel-regime prediction directly.

## What this changes in the program

- **T4 (symmetry inheritance) is upgraded:** EMPIRICAL across six architecture cells, pre-registered.
- **T3 (Curie bias for mechanisms) is restricted:** EMPIRICAL in Boolean circuits only, with a failed transfer to modular addition. It should be restated as a statement about data symmetries (F2, reading 3) and re-tested.
- **Next (Spike 16):**
  1. Kernel-regime prediction vs learned completion (F3).
  2. Planted targets with a symmetry deficit relative to the data (T4a): generalization error should track the deficit.
  3. The stabilizer-consistency method: does it help exactly where T4a says?
