# Spike 19: Does symmetry attraction select the function? A calibrated CSP. Is the selection law a universal semiring measure?

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 18 F1, F3; Spike 17 F1 · **Theory source:** Baril, Couceiro & Lagerkvist, "New Perspectives on Semiring Applications to Dynamic Programming", arXiv:2512.03916 (Discrete Applied Mathematics 383, 2026). Read in full.

## Why the semiring paper matters here

Baril et al. represent the solution set of any problem with certificates as a join/union expression. Join combines partial solutions with disjoint domains; disjoint union merges sets of solutions. A *measure* sends these to the × and + of a semiring and is determined by a matrix of per-element weights M[s, t]:

μ_M(F) = Σ_{f∈F} Π_s M[s, f(s)].

Their **∆-product** D∆A combines a totally ordered cost dioid D with a semiring A. It evaluates μ_A only on the *minimum-cost* solutions: lexicographically, cost first, then the A-measure.

Our results fit this language exactly:
- Minimal circuits are the minimum-cost solutions of a hitting-set problem; isomer counts are their #Cost (R_min∆ℕ).
- Spike 09 F1: training first picks a cheapest completion.
- Spike 17 F1: the distribution over minimal circuits is reproduced by independent pairing of units, i.e. it is a product measure with unit-level weights.

**Conjecture (S19, stated before testing):** the mechanism-selection law of gradient training is a normalized (R_min ∆ R≥0)-measure over the task's solution set. Its unit weight matrix M[unit, t] = w(t | g) depends only on intrinsic, symmetry-invariant properties of the unit relative to the task, and is **universal across tasks**.

## Arm 1: does attraction to the symmetric subspace precede the choice of function?

- **Runs:** 128 elements × 40 fresh seeds, AdamW, wd = 0.03, width 8. Weights at steps 1, 3, 10, 30, 100, 300, 1,000 and 3,000.
- **Settling:** for each core unit whose final function t has a nontrivial stabilizer H ⊂ G_g, the settling time is the first checkpoint from which its threshold function stays equal to t.
- **Test:** before settling, compare its weight-space defect relative to H with its defect relative to a *conjugate* subgroup H′ = σHσ⁻¹ ≠ H, for σ ∈ G_g. H′ has the same order and fixes a different, equally symmetric function σt.
- **What a selecting attraction predicts:** if attraction selects the function, the unit is already closer to Fix(H) than to Fix(H′) before its function settles. If weights only symmetrize after the function is fixed, the two defects agree before settling.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H19.1 | Attraction precedes settling | median over pre-settling observations of D_H′ − D_H > 0, sign test p < 0.01, with at least 300 observations | median ≤ 0 |
| H19.2 | Pre-settling defect predicts the final stabilizer | among units with a nontrivial final stabilizer, the share with D_H < D_H′ at the last pre-settling checkpoint is ≥ 0.6 | ≤ 0.5 |

## Arm 2: CSP with a smoothness-matched null

Spike 18 showed that the independence-based bound fails because nearby inputs share labels. The new acceptance test:
- For a candidate σ with n both-labelled pairs (x, σx) at Hamming distances d_i, all agreeing, the p-value is Π_i p₀(d_i). Here p₀(d) is the label-agreement rate among *random* labelled pairs at Hamming distance d (in the one-hot encoding), estimated from the training labels only.
- σ is accepted iff p < 0.001 / (number of candidates), i.e. Bonferroni over candidates.

Everything else is as in Spike 18: the same datasets, fractions, seeds, model and candidates.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H19.3 | Decoys are now rejected | any decoy accepted in ≤ 1/10 runs at every tic-tac-toe fraction | > 3/10 at any fraction |
| H19.4 | True symmetries are still found | at least one board symmetry accepted in ≥ 8/10 tic-tac-toe runs at fractions 0.2 and 0.3 | ≤ 5/10 |
| H19.5 | Calibrated CSP improves tic-tac-toe at every fraction | gain ≥ +0.01 at 0.2 and 0.3, and ≥ +0.03 at 0.1 | gain ≤ 0 at any |
| H19.6 | No harm anywhere | every mean gain ≥ −0.01 | any ≤ −0.02 |

## Arm 3: is the selection law a universal product measure?

- **Model:** P(I = {t1, t2} | g) ∝ w(t1|g)·w(t2|g), with

  log w(t|g) = a·log|Stab_{G_g}(t)| + b·agree(t, g) + c·log Ω(t).

  Three parameters, shared across all tasks.
- **Fitting:** by maximum likelihood on the Spike 14 A8 cores of a *fixed random half* of the 128 elements, chosen by seed 1901 before fitting.
- **Evaluation:** bits gained over uniform per run on (i) the other half of Spike 14 A8 and (ii) the fresh arm-1 runs on the held-out half.
- **Comparisons:**
  - the parameter-free Curie predictor of Spike 14 (β = −2);
  - an *oracle* per-element product measure, whose unit weights are fitted on each held-out element's own arm-1 cores from seeds 0–19 and scored on seeds 20–39. It is the ceiling for any product measure.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H19.7 | Universal unit weights transfer to unseen tasks | held-out gain ≥ Curie's gain + 0.2 bits/run on both test sets | below Curie's gain on either |
| H19.8 | A universal product measure captures most of what any product measure can | universal gain ≥ 0.7 × oracle gain on the fresh test set | ≤ 0.4 × |
| H19.9 | The fitted law is Curie-like | a > 0 (units with larger stabilizer weigh more), with a bootstrap 95% interval excluding 0 | a ≤ 0 |
