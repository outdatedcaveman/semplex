# Spike 26: Do trained networks complete algebra lawfully? Associativity and the Curie bias on a 3-element carrier

**Date:** 2026-11-12 · **Status:** pre-registered (no run made; amended once before any run, see below) · **Inspired by:** McDermott, Piróg & Uustalu, "Counting Monads on Lists" (CLA 2023). That paper counts the lawful structures on a fixed carrier and asks how one structure is singled out from a finite seed (closure under associativity). Here we ask which lawful structure *training* singles out. **Follows:** C8(c) (does the Curie bias transfer to non-Boolean domains?), Spike 20 (selection versus building)

## Setting

- **Carrier and laws.** Carrier {0, 1, 2}. Of the 3⁹ binary operations, enumerate the associative ones (the labelled semigroups of order 3).
- **Tasks.** With rng seed 2600, draw a semigroup S uniformly and reveal k ∈ {4, 5, 6} of its 9 cells (k uniform). Keep the task if the revealed cells have at least 2 associative completions. Take 300 such *general* tasks. Random tasks rarely have symmetry (a dry run of the generator gave 11 of 300), so add a *symmetric pool*: 150 further tasks, drawn the same way with seed 2603, kept only if |G| > 1. Lawfulness rates (H26.1–H26.2) use the general pool; the Curie test (H26.3) uses every task with |G| > 1.
- **Symmetry of a task.** G is the set of permutations π of the carrier that map the revealed cell set to itself and satisfy π(T(a, b)) = T(πa, πb) on it.
  - The encoding is one-hot(a) ⊕ one-hot(b) in, 3 logits out, with i.i.d. Gaussian initialization.
  - Relabelling the carrier permutes input and output coordinates, so the distribution of completions is G-equivariant (Theorem 15 analogue).
- **Training (40 seeds per task).**
  - *Full:* tanh MLP, width 16, AdamW (lr 0.03, wd 0.01), 2,000 full-batch steps, cross-entropy on the revealed cells.
  - *Selection only:* first layer frozen at width 256, readout trained the same way (Spike 20's selection control).
- **Completion.** The argmax on the hidden cells. Only nets that fit every revealed cell are counted.

## Measures

- **Lawfulness rate.** The fraction of fitted nets whose completed table is associative, against the fraction of all completions that are associative (the uniform rate, 3^(9−k) completions per task).
- **Curie β.** Restricted to associative completions in tasks with |G| > 1: the orbits of associative completions under G, and the mass that trained nets put on each. β is computed with Spike 14's pooled estimator (`spike17.orbit_beta`); β < 0 means smaller orbits (more symmetric completions) get more mass than their size predicts. 95% interval from 1,000 bootstrap resamples of tasks.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H26.1 | **Training is biased toward lawful completions.** Full training's lawfulness rate exceeds the uniform rate | ratio ≥ 2, pooled over tasks | ratio ≤ 1 |
| H26.2 | **The law bias is built, not selected.** Full training is more lawful than selection-only | rate(full) ≥ 1.3 × rate(selection) | rate(full) ≤ rate(selection) |
| H26.3 | **The Curie bias transfers (C8(c)).** β < 0 for full training | 95% interval below 0 | point estimate ≥ 0 |

Reported as well: whether the completion training picks is the source semigroup S, as a rate against 1 / (number of associative completions).

## Amendment before any run (2026-11-12)

The generator ran for 30 minutes without filling the symmetric pool. Exhaustive count: only **114** distinct revealed tables have ≥ 2 associative completions and a nontrivial G. By k: 48 at 4 cells, 45 at 5, 21 at 6. The target of 150 was therefore unreachable. Amendment: the symmetric pool is *all 114*, enumerated exhaustively and deterministically. A symmetric task that is also drawn into the general pool appears in both pools. Hypotheses, criteria, training and estimators are unchanged. No network had been trained when this was changed.
