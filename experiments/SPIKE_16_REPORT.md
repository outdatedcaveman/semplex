# Spike 16: Is symmetry inheritance the kernel limit? Does generalization track the symmetry deficit? Does stabilizer symmetrization help where predicted?

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 15 F1 and F3; program `charter/PROGRAM_SYMMETRY.md` T4

## Setup

- **Cells:** four, from Spike 15: tanh-W8-AdamW, ReLU-W8-AdamW, tanh-W8-GD, tanh-W64-AdamW. Fresh seeds (base 16 000).
- **Part 1:** Spike 15's 240 symmetric partial tasks, 5 seeds each. **Kernel prediction:** the completion given by ridgeless regression with the network's Monte Carlo NTK (200,000 units, the same initialization law) on ±1 targets.
- **Parts 2–3:** 600 *planted* tasks. A random 4-input target f\* (a random member of a random class) and a random set of 8 labelled inputs. Only tasks are kept whose labelled data have a nontrivial stabilizer G_data: the input permutations and negations mapping the labelled set to itself with labels preserved. G_data is computed exactly from the data; nothing about f\* is used. f\* either keeps G_data (38% of tasks) or breaks it (62%). Three seeds each.
- **Method (part 3):** average the trained network's logits over G_data at test time. This is the simplest form of the stabilizer-consistency method in the program, §3.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H16.1 | **Inheritance is not the kernel limit:** when the learned completion is symmetric, it often differs from the kernel completion | P(learned = kernel \| learned symmetric) ≤ 0.5 in every cell | ≥ 0.8 in every cell (then inheritance ≈ kernel proximity) |
| H16.2 | The kernel completion is a worse model of training than the Curie+simplicity description: it is cheapest less often than the nets (93–98%, Spike 15) | kernel cheapest share ≤ 0.8 | ≥ 0.93 |
| H16.3 | **T4a, symmetry deficit:** held-out accuracy is higher when f\* keeps G_data than when it breaks it | difference ≥ 0.10 in every cell | ≤ 0 in any |
| H16.4 | **T4b, error localization:** errors concentrate on free inputs lying in G_data-orbits where f\* is not constant | error rate there ≥ 2× the rate on orbits where f\* is constant, every cell | ≤ 1× in any |
| H16.5 | **Method, where predicted:** symmetrizing over G_data helps when f\* keeps G_data and hurts when it breaks it | gain > 0 for keeping targets **and** < 0 for breaking targets, every cell | gain ≤ 0 for keeping targets in any cell |

Caveat stated in advance: H16.3 is confounded if keeping targets are simpler than breaking ones. The mean atlas cost of each group is reported; if they differ by more than 0.3 neurons, H16.3 is downgraded to "neither" whatever the accuracy difference.
