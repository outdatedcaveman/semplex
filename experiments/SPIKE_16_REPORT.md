# Spike 16: Is symmetry inheritance the kernel limit? Does generalization track the symmetry deficit? Does stabilizer symmetrization help where predicted?

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `b661527` before any run · **Follows:** Spike 15 F1 and F3; program `charter/PROGRAM_SYMMETRY.md` T4

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

## Results (`results/spike16.json`)

| Cell | Kernel completion symmetric | Kernel completion cheapest | P(learned = kernel \| learned symmetric) | Held-out acc.: f\* keeps / breaks G_data | Error rate on orbits where f\* breaks / keeps | Symmetrization gain: keeps / breaks |
|---|---|---|---|---|---|---|
| tanh-W8-AdamW | 0.97 | 0.93 | 0.64 | 0.520 / 0.523 | 0.50 / 0.47 | +0.003 / +0.002 |
| ReLU-W8-AdamW | 0.94 | 0.92 | 0.67 | 0.513 / 0.516 | 0.50 / 0.48 | 0.000 / 0.000 |
| tanh-W8-GD | 0.97 | 0.93 | 0.68 | 0.523 / 0.522 | 0.50 / 0.47 | −0.001 / −0.002 |
| tanh-W64-AdamW | 0.97 | 0.93 | 0.66 | 0.518 / 0.525 | 0.50 / 0.47 | +0.001 / +0.003 |

Mean atlas cost: 3.08 (keeping targets) vs 3.29 (breaking), a difference of 0.20, below the 0.3 confound threshold.

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H16.1 | **Neither.** Learned symmetric completions equal the kernel's 64–68% of the time: the kernel limit explains most, not all, of symmetry inheritance. |
| H16.2 | **Broken in 2 of 4 cells, neither in 2.** The kernel completion is cheapest 92–93% of the time, about as often as trained nets. The kernel limit accounts for the simplicity bias on these tasks as well. |
| H16.3 | **Broken.** Held-out accuracy is at chance (≈0.52) and does not depend on whether f\* keeps the data's stabilizer. |
| H16.4 | **Neither** (ratio 1.04–1.07). |
| H16.5 | **Broken.** Symmetrizing over G_data changes nothing (|gain| ≤ 0.003). |

## Findings

**F1. The function-level "Curie" result of Spikes 14–15 is mostly the kernel limit.** Kernel interpolation with the network's own NTK is symmetric on symmetric data (94–97%) and cheap (92–93%). It predicts the trained network's completion in about two thirds of the cases where that completion is symmetric. Kernel methods inheriting the invariances of their kernel is known (for example, work on learning with invariances in random-features and kernel models). Spike 15 F1 should therefore not be presented as a new principle. What remains unexplained by the kernel is the third of symmetric completions that differ from the kernel's choice, and the finite-network deviation from it.

**F2. A no-transfer lemma kills the stabilizer method, and the data agree.** *Lemma (elementary).* If G maps the labelled set to itself, every G-orbit lies entirely inside the labelled set or entirely outside it. So G-invariance relates unlabelled inputs only to other unlabelled inputs and carries no label information to them. Symmetrizing a predictor over the exact data stabilizer can make its unseen predictions mutually consistent, but cannot make them more accurate on average. This is exactly what was measured (all gains within ±0.003). T4a and the method in `charter/PROGRAM_SYMMETRY.md` §3 are refuted as stated. Any useful symmetry-based generalization must use symmetries that are *not* exact stabilizers of the data: symmetries of a prior over targets, or approximate ones.

**F3. With 8 random labels on random 4-input targets, nothing generalizes.** Held-out accuracy is ≈ 0.52 in every cell. These tasks carry too little information for any inductive bias to show; the planted design was uninformative about T4a, independently of F2.

## What survives, after Spikes 11–16

- **Theorem 15** (equivariance of mechanism choice) and its confirmation, in two domains.
- **The mechanism-level Curie bias in Boolean threshold circuits** (Spike 14). Kernel arguments cannot explain it, because the kernel limit has no circuits. A parameter-free predictor gains about 1.3–1.7 bits per run. It did **not** transfer to modular-addition frequency profiles (Spike 15 arm A). It is a real, original, *domain-limited* finding.
- **Symmetry inheritance of functions** is real and robust across architectures, but mostly predicted by the kernel limit (F1).
