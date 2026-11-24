# Spike 26: Do trained networks complete algebra lawfully? Associativity and the Curie bias on a 3-element carrier

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 2e5afe3, amended before any run in 361da8d; results below) · **Inspired by:** McDermott, Piróg & Uustalu, "Counting Monads on Lists" (CLA 2023). That paper counts the lawful structures on a fixed carrier and asks how one structure is singled out from a finite seed (closure under associativity). Here we ask which lawful structure *training* singles out. **Follows:** C8(c) (does the Curie bias transfer to non-Boolean domains?), Spike 20 (selection versus building)

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

---

## Results

300 general tasks plus all 114 symmetric tasks, 40 seeds each. Every net fit its revealed cells (fit rate 1.000 for both training modes). Raw data in `results/spike26_raw/runs.json`, analysis in `results/spike26.json`. There are 125 tasks with |G| > 1: the 114 of the symmetric pool plus 11 that the general draw also hit.

| | Full training (tanh, width 16) | Selection only (frozen width-256 first layer) |
|---|---|---|
| Lawful (associative) completion rate, general pool | **0.669** | 0.612 |
| … against the uniform rate over completions (0.070) | **9.6×** | 8.7× |
| Completion equals the source semigroup S (chance 0.251) | 0.288 | 0.289 |
| Curie β (95% interval) | **−1.85** [−2.72, −1.08] | −1.29 [−2.20, −0.57] |

### Verdicts

| # | Verdict |
|---|---|
| H26.1 | **Held.** Full training completes tables associatively 9.6 times as often as a uniform completion would (66.9% against 7.0%). |
| H26.2 | **Neither held nor broken.** Full / selection = 1.09: above 1.0, below 1.3. |
| H26.3 | **Held.** β = −1.85, 95% interval entirely below 0. |

## Findings

**F1. The Curie bias transfers to algebra.** On a non-Boolean domain, partial operation tables on a 3-element carrier, completions with a larger symmetry group get more than their orbit-size share of training's mass. β = −1.85 sits in the range Spike 14 found for Boolean mechanisms (β ≈ −2 to −6). This is the first transfer of the bias outside threshold-circuit atlases. C8(c) moves from open to supported on one non-Boolean domain.

**F2. Training is strongly biased toward lawful structure, and the bias is mostly already present before features are learned.** Two-thirds of trained completions are associative, against 7% by chance. Freezing the first layer at random and training only the readout already gives 61%. Learning the features adds about 6 points of lawfulness and makes the Curie bias stronger (−1.85 against −1.29). Spike 20's division between selection and building, measured on circuits, reappears here for algebraic laws: most of the effect comes from selection, and a smaller part from building.

**F3. Training does not recover the source table.** It picks the source semigroup only slightly above chance (0.29 against 0.25). It prefers lawful and symmetric completions, but has no special access to the table the data came from. This is what an inductive bias should do. It is also why the bias is useful only when the true structure is itself lawful and symmetric.

**Caution.** Associativity on a 3-element carrier is common among "simple" tables: constant, projection and min/max-like operations are all associative. Part of F2 may be a simplicity bias that associativity happens to track. Separating the two needs a law that simple tables do *not* tend to satisfy, which is a candidate follow-up.
