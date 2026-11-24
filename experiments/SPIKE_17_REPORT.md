# Spike 17: Mechanism of the Curie bias; a prior-symmetry method; where finite networks leave the kernel

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `99b4d1c` before any run or analysis · **Follows:** Spike 16 "what survives"

## Arm 1: where does the circuit-level Curie bias come from?

Two mechanisms make different predictions:
- **(M-pair) Coordination:** the bias lives in *which units are paired*. Training couples units so that the pair keeps the task's symmetry.
- **(M-unit) Unit concentration:** each unit lands, almost independently, on a few G_g-orbits of threshold functions. Units with a large stabilizer are favoured. Symmetric pairs then arise combinatorially, by drawing two units from the same small orbit.

Equivariant bifurcation theory suggests the first ingredient of M-unit. The equivariant branching lemma says symmetry-breaking branches generically carry *maximal* (axial) isotropy subgroups. A unit "remembers" as much symmetry as a generic bifurcation allows.

**Test, on Spike 14's stored cores (A8, G8, A128), using statistics not computed before:**
- *Unit marginals:* m(t) = total credit of unit t across cores.
- *Independent-pairing model:* P(I = {a, b}) ∝ m(a)·m(b), restricted to isomers of g.
- β_ind is that model's orbit-mass exponent, computed exactly as β_obs was in Spike 14.
- *Unit-level exponent β_u:* unit-orbit mass ∝ |unit orbit|^β_u.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.1 | M-unit: pairing is close to independent given unit marginals | \|β_ind − β_obs\| ≤ 0.5·\|β_obs\| in all three runs | β_ind ≥ 0 in any run (coordination is then essential) |
| H17.2 | Units themselves are Curie-biased | β_u ≤ −0.5 in all three runs | β_u ≥ 0 in any |

## Arm 2: a symmetry method that can transfer labels (prior-level, approximate)

The no-transfer lemma (Spike 16) rules out exact data stabilizers. Approximate symmetries are not ruled out. These are transformations σ under which the labelled pairs (x, σx) agree, and which map labelled points to unlabelled ones.

**Method: certified symmetry propagation (CSP).**
- **Candidate generators:** the 28 input transpositions, the cyclic shift, reversal, the 8 single-input negations and global negation.
- **Acceptance:** σ is accepted iff it has at least 10 both-labelled pairs with x ≠ σx and *all* of them agree. Under a null of independent fair labels, the chance probability is ≤ 2⁻¹⁰ per generator, so about 0.04 false accepts per task over 39 candidates.
- **Propagation:** the accepted generators generate a group Ĝ. Each Ĝ-orbit containing labelled points with consistent labels passes that label to its unlabelled points. A conflicting orbit voids Ĝ, and the method falls back to plain training.
- **Model:** the same MLP is trained on the enlarged labelled set.

**Workload:**
- n = 8 inputs (256 points), 128 labelled at random.
- Target families: functions invariant under S8 (symmetric functions), C8 (cyclic shifts), S4×S4 (two blocks), and **none** (random targets). 30 targets each, 3 seeds.
- MLP: tanh, width 64, AdamW. Also reported: an oracle propagation with the true group.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.3 | CSP improves held-out accuracy when the target family is symmetric | mean gain ≥ +0.05 for each of S8, C8, S4×S4 | gain ≤ 0 for any |
| H17.4 | CSP does no harm when there is no symmetry | \|mean gain\| ≤ 0.01 on random targets | loss > 0.02 |

**Prior art (index level):** learned invariances (Augerino, Benton et al. 2020), automatic augmentation search, symmetry-discovery methods. The new element is a *certified* acceptance rule with an explicit false-accept bound and exact propagation. The pre-registered claim is only about the gains above.

## Arm 3: where do finite networks leave the kernel?

**Workload:** fresh seeds on Spike 15's 240 symmetric partial tasks, 5 seeds each. Cells: tanh-AdamW at widths 8, 64 and 512, plus tanh-GD at width 8. The kernel completion is the tanh NTK interpolant, as in Spike 16.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.5 | Feature learning compresses: when the net's completion differs from the kernel's, it is cheaper (atlas cost) more often than costlier | sign test p < 0.01 in every cell | costlier more often in any cell |
| H17.6 | The kernel limit is approached with width | P(learned = kernel) rises from width 8 to 512 by ≥ 0.10 | it falls |
| H17.7 | Symmetry beyond the kernel: when the net departs from the kernel, it stays symmetric | P(symmetric \| learned ≠ kernel) ≥ 2 × the symmetric share q of equally cheap completions | ≤ 1 × q |

## Results (`results/spike17.json`; raw data in `results/spike17_raw/`)

### Arm 1: mechanism (Spike 14 stored cores)

| Run | β observed | β, independent pairing from unit marginals | β_u (unit level) |
|---|---|---|---|
| A8 | −2.28 | −2.31 | −2.70 |
| G8 | −3.60 | −3.67 | −4.44 |
| A128 | −3.22 | −3.31 | −3.39 |

**Exploratory follow-up (post hoc, `experiments/spike17_explore.py`).** Is the unit-level bias a pull toward the target's Chow direction, which is fixed by the whole symmetry group?
- Unit mass vs |cos(unit's ℓ2 max-margin weight vector, target's Chow vector)|: median ρ = −0.03 to −0.05.
- Unit mass vs the unit's stabilizer size: ρ = 0.32 to 0.35.
- Stabilizer size vs cosine: ρ ≈ 0.02.

**The Chow-pull explanation is killed.**

### Arm 2: certified symmetry propagation (n = 8; 128 of 256 points labelled; 90 runs per family)

| Target family | Plain MLP | MLP + CSP | MLP + oracle group | Gain (CSP) | Generators accepted (mean) | Tasks voided |
|---|---|---|---|---|---|---|
| S8 (symmetric functions) | 0.951 | 0.996 | 0.997 | +0.045 | 29.1 | 1/30 |
| C8 (cyclic) | 0.508 | **0.982** | 0.982 | **+0.474** | 1.0 | 0/30 |
| S4×S4 | 0.861 | 0.978 | 0.982 | +0.117 | 11.6 | 1/30 |
| none (random) | 0.507 | 0.507 | 0.507 | 0.000 | 0.0 | 0/30 |

### Arm 3: departures from the kernel (fresh seeds, 1,200 runs per cell)

| Cell | P(learned = kernel) | Departures | Cheaper / costlier than kernel | Sign test p | P(symmetric \| departure) | Symmetric share of equal-cost completions |
|---|---|---|---|---|---|---|
| tanh-W8-AdamW | 0.546 | 545 | 64 / 42 | 0.020 | 0.60 | 0.21 |
| tanh-W64-AdamW | 0.600 | 480 | 61 / 22 | 1.1e-5 | 0.63 | 0.21 |
| tanh-W512-AdamW | 0.612 | 466 | 68 / 15 | 1.6e-9 | 0.69 | 0.21 |
| tanh-W8-GD | 0.670 | 396 | 66 / 13 | 5.4e-10 | 0.83 | 0.22 |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H17.1 | **Held.** Independent pairing from unit marginals reproduces β to within 0.1 in all three runs. |
| H17.2 | **Held.** Units themselves are Curie-biased, with β_u from −2.7 to −4.4. |
| H17.3 | **Neither, because of a ceiling.** Gains are +0.474 (C8) and +0.117 (S4×S4), but only +0.045 for S8, where the plain MLP already reaches 0.951 and the oracle gains only +0.045. CSP matches the oracle group in every family. |
| H17.4 | **Held.** On random targets CSP accepts no generator and changes nothing. |
| H17.5 | **Neither (3 of 4 cells pass).** Departures from the kernel are cheaper far more often than costlier everywhere, but at width 8 with AdamW p = 0.020 misses the 0.01 bar. Most departures (about 80%) are to completions of *equal* cost. |
| H17.6 | **Neither.** Agreement with the kernel rises with width (0.546 → 0.600 → 0.612), but by 0.066, short of 0.10. At width 512, 39% of runs still depart from the kernel. |
| H17.7 | **Held.** When networks depart from the kernel, they stay symmetric 2.8–3.7 times more often than equal-cost completions (0.60–0.83 vs 0.21–0.22). |

## Findings

**F1. The Curie bias is a property of single units.** Pairing is statistically independent given the unit marginals (β_ind ≈ β_obs), and units individually favour threshold functions with a large stabilizer in the task's symmetry group. The circuit-level law of Spike 14 is inherited from a unit-level law plus combinatorics. The obvious unit-level explanation, a pull toward the target's Chow direction, is killed: alignment with it predicts nothing (ρ ≈ −0.04). The unit-level mechanism is still unknown. The next candidate is transverse attraction of weight vectors into the symmetric subspaces Fix(H), measurable from weight trajectories.

**F2. Symmetry that *can* transfer labels does, and a certified rule finds it without harm.** CSP accepts transformations that agree on at least 10 labelled pairs. These are approximate, global symmetries, not stabilizers of the labelled set, so they connect labelled to unlabelled inputs, which the Spike 16 lemma showed exact stabilizers never do. Results:
- **cyclic targets:** accuracy goes from chance (0.51) to 0.98;
- **block-symmetric targets:** it gains 12 points;
- **every symmetric family:** it matches an oracle that knows the true group;
- **random targets:** it accepts nothing and changes nothing.

Learned-invariance methods exist (Augerino; augmentation search). What is specific here is an explicit false-accept bound, exact propagation, and the theoretical account (Spikes 15–16) of why *these* symmetries help when stabilizers cannot.

**F3. Where finite networks leave the kernel, they move toward cheaper and toward symmetric.** About 40–45% of runs depart from the infinite-width kernel's completion, even at width 512, with the standard parametrization and AdamW or GD. The departures:
- go to cheaper completions 3–5 times more often than to costlier ones;
- stay symmetric about 3 times more often than equally cheap alternatives.

This is the part of the function-level Curie bias that the kernel limit does *not* explain. Finite networks add a symmetry and simplicity preference on top of the kernel's.

## Status after Spike 17

- **Curie bias, mechanisms:** now localized to single units (F1). Its cause is open, and one candidate is killed.
- **Curie bias, functions:** mostly the kernel (Spike 16), plus a genuine finite-network excess of symmetry and simplicity (F3).
- **Method:** CSP works where theory says it can (F2), and is honest about its prior art.
