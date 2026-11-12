# Spike 19: Does symmetry attraction select the function? A calibrated CSP. Is the selection law a universal semiring measure?

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `42db2e4` before any run · **Follows:** Spike 18 F1, F3; Spike 17 F1 · **Theory source:** Baril, Couceiro & Lagerkvist, "New Perspectives on Semiring Applications to Dynamic Programming", arXiv:2512.03916 (Discrete Applied Mathematics 383, 2026). Read in full.

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

## Results (`results/spike19.json`; raw data in `results/spike19_raw/`)

### Arm 1 (fit 99.8%; 353 core units with a nontrivial stabilizer and a conjugate comparison subgroup)

| | Value |
|---|---|
| Pre-settling observations | 1,631 |
| Median D_H′ − D_H (closer to own subgroup ⇒ positive) | **+0.162** |
| Positive / negative | 1,142 / 489, sign test p = 1.5 × 10⁻⁶⁰ |
| Share of units closer to their own H at the last pre-settling checkpoint | **0.89** |
| Settling checkpoint (number of units) | 3: 3 · 10: 10 · 30: 71 · 100: 112 · 300: 52 · 1,000: 48 · 3,000: 57 |

### Arm 2 (same splits as Spike 18)

| Dataset @ fraction | Plain | Calibrated CSP | Gain | Runs accepting a decoy | Runs accepting a board symmetry |
|---|---|---|---|---|---|
| tic-tac-toe @ 0.1 | 0.911 | 0.910 | −0.001 | 0/10 | 0/10 |
| tic-tac-toe @ 0.2 | 0.974 | **0.992** | +0.017 | 0/10 | 10/10 |
| tic-tac-toe @ 0.3 | 0.982 | **0.995** | +0.013 | 0/10 | 10/10 |
| MONK-1 @ 0.15 / 0.3 | 0.916 / 1.000 | 0.932 / 1.000 | +0.016 / 0 | — | — |
| MONK-2 @ 0.15 / 0.3 | 0.775 / 0.996 | 0.770 / 1.000 | −0.005 / +0.004 | — | — |
| MONK-3 @ 0.15 / 0.3 | 0.983 / 0.998 | 0.984 / 0.994 | +0.001 / −0.004 | — | — |

### Arm 3 (fit on 64 elements of Spike 14 A8; tested on the other 64)

Fitted universal law: log w(t|g) = 0.13·log|Stab(t)| + 9.92·agree(t, g) + 0.88·log Ω(t). Bootstrap 95% interval for the stabilizer coefficient: [−0.18, 0.60].

| Bits/run over uniform, held-out elements | Universal product measure | Curie (β = −2) | Oracle per-element product measure |
|---|---|---|---|
| Spike 14 A8 (seen seeds, unseen elements) | **1.69** | 1.36 | — |
| Fresh arm-1 runs | **1.60** | 1.23 | — |
| Fresh, seeds 20–39 | **1.63** | 1.19 | 2.75 |

**Exploratory (post hoc, `experiments/spike19_explore.py`): nested models, same split**

| Unit-weight terms | Fitted coefficients | Held-out S14 | Fresh |
|---|---|---|---|
| agreement only | 9.08 | 1.36 | 1.27 |
| stabilizer + solid angle | 1.19, 0.08 | 0.83 | 0.79 |
| stabilizer + agreement | 1.07, 6.71 | 1.61 | 1.52 |
| **agreement + solid angle** | **10.27, 0.94** | **1.67** | **1.58** |
| all three | 0.13, 9.92, 0.88 | 1.69 | 1.61 |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H19.1 | **Held.** Before a unit's function settles, its weights are already closer to the symmetric subspace of its *eventual* stabilizer than to that of an equally symmetric conjugate (p = 1.5 × 10⁻⁶⁰). |
| H19.2 | **Held.** 89% of units are closer to their own H at the last checkpoint before settling. |
| H19.3 | **Held.** No decoy accepted in any run. |
| H19.4 | **Held.** A board symmetry was accepted in 10/10 runs at 20% and 30%. |
| H19.5 | **Broken.** At 10% labelled the calibrated test accepts nothing (gain −0.001). At 20% and 30% it gains +0.017 and +0.013, where Spike 18's uncalibrated version gained ≈ 0. |
| H19.6 | **Held.** The worst change is −0.005. |
| H19.7 | **Held.** The universal unit-weight law beats the Curie predictor by +0.33 and +0.37 bits/run on unseen elements. |
| H19.8 | **Neither.** It reaches 0.59 of the per-element oracle (1.63 vs 2.75). |
| H19.9 | **Neither.** The stabilizer coefficient is positive (0.13), but its interval includes 0. |

## Findings

**F1. The weights head for the eventual symmetric subspace before the function is decided, but a confound remains.** In 89% of cases, a unit's weights are closer to the fixed subspace of its *final* stabilizer than to that of an equally symmetric alternative, before its threshold function has settled.
- *Confound, stated plainly:* a unit that has nearly reached t's cone is naturally closer to Fix(Stab(t)), because t's cone is centred on that subspace. So H19.1 shows that the trajectory is *aimed* at t early. It does not yet show that symmetry, rather than proximity to t's cone, does the aiming.
- *The discriminating test:* compare units whose pre-settling function is equally far from t and from σt.

**F2. A universal, three-parameter product measure predicts which circuit training builds on tasks it never saw.** It gains about 1.6–1.7 bits per run over uniform on held-out elements and fresh seeds, 0.33–0.37 bits more than the Curie predictor. It reaches about 60% of what a per-element product measure fitted on the same element's own data can do. This is the first fitted law in this program that **transfers across tasks**.

**F3. The Curie bias is largely derived, not fundamental. The underlying law is "volume tilted by fit".** Once agreement with the target is in the unit weight, the stabilizer term is not needed (95% interval includes 0). Exploratory nested models show that two terms nearly match all three:

w(t | g) ∝ Ω(t)^0.94 · exp(10.3 · agree(t, g)).

Each unit is weighted by its prior solid angle, tilted exponentially by how many inputs it gets right. Stabilizer size and solid angle are largely interchangeable because symmetric threshold functions occupy larger solid angles. Spike 11's negative result for volume, and Spike 14's positive result for symmetry, are two partial views of this one tilted-volume weight.

**F4. Calibration fixed safety, and cost power.** The smoothness-matched null removed every decoy and every harmful change, and recovered gains on tic-tac-toe at 20–30% (to 0.99+). It is too strict at very low label counts: it accepts nothing at 10% on tic-tac-toe, and loses Spike 18's MONK gains, which came partly from genuine value symmetries that the stricter test now rejects.

## The selection law, stated in the language of Baril et al.

For a task g, let SOL be its set of minimal circuits (the minimum-cost solutions of the determination problem). The empirical law is the normalized (R_min ∆ R≥0)-measure: the dioid of circuit cost, ∆-composed with the probability semiring, with unit matrix

M[unit, t] = Ω(t)^γ · exp(λ · agree(t, g)), with γ ≈ 0.9 and λ ≈ 10 (agreement as a fraction of 16).

- **Lexicographically,** training first restricts to minimum cost (Spike 09: about 94% cheapest completions). Among minimal solutions it then follows this product measure (Spike 17: pairing independent; F2–F3 here).
- **Equivariance (Theorem 15)** holds automatically, because Ω and agreement are G_g-invariant.
- **The Curie bias** follows because symmetric units have larger Ω and, for symmetric targets, higher agreement.

What is *not* explained: the remaining 40% to the per-element oracle, and why the tilt is exponential with λ ≈ 10. A Gibbs-like reading, with energy equal to the number of misclassified inputs and inverse temperature ≈ 0.62 per input, is a conjecture to test.
