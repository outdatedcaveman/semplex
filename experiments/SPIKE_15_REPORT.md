# Spike 15: The definitive transfer test of the Curie principle

**Date:** 2026-11-12 · **Status:** pre-registered. The pilots used primes 23 and 59, whose quotient groups Z_p^*/±1 are cyclic of prime order (11 and 29), so they carry **no** information about subgroup structure; only training mechanics and sparsity were inspected. The test prime is 61, so the quotient has order 30 and subgroups of orders 2, 3, 5, 6, 10 and 15. No run on it has been made.

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
