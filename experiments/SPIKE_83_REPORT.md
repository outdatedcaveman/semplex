# Spike 83: The invariance principle: is a learned concept's dominant geometry itself closed under the inputs?

**Date:** 2026-11-19 · **Status:** complete (pre-registered in bf8b42c; results below) · **Follows:**
- Spikes 77–80: the selection rule holds for group, i.e. symmetric, concepts (P212–P214, P217).
- Spike 81: it fails as generalised to automata with resets and merges (P216).
- The request to find the principle connecting the two cases. Theory: `charter/FOUNDATIONS.md` §17.

## The principle under test

A coarse-graining of a dynamical system is closed (strongly lumpable) exactly when the span of its block-indicator functions is **invariant** under every input's action on observables, (T_a f)(q) = f(δ_a q) (Kemeny–Snell; the linear form of Myhill–Nerode closure).

- **Groups.** The T_a are invertible. The minimal invariant subspaces are the irreducible representations, and isotypic components are invariant. That is why the selection rule had clean candidates.
- **Monoids** (resets, merges). The T_a generate a non-semisimple algebra. Invariant subspaces exist (submodules) but do not split into independent irreducible pieces: the Clifford–Munn–Ponizovskii / Steinberg representation theory of finite monoids is layered.

  The predictive kernel's eigenvectors, used as "modes" in Spike 81, are not invariant in general. That may be why Spike 81 failed.

**Conjecture C44 (closure all the way down).** For any automaton, a trained learner's *dominant* geometry spans an approximately **invariant subspace** of the input actions, i.e. a coarser closed concept:
- an isotypic component for groups;
- a submodule for monoids.

Value against cost then selects *among invariant subspaces*. This is the unifying principle; the selection rule is its group case.

## Design

- **Automata.**
  - **Groups:** the 11 automata of Spike 77 (states = group elements, letters = generators + identity).
  - **Non-groups:** the 15 non-permutation (mixed and free, i.e. merge/reset) automata of Spike 81.
- **Learner.** GRU + Adam (6,000 steps, length 30), 2 seeds. Fit guard ≥ 0.99 at length 100.
- **Learned dominant subspace.** Take the visit-weighted (π) centroid Gram over minimal states and its top r eigenvectors, as functions on states. r is the smallest number reaching 70% of the variance, capped at m − 2 so it is never the whole space. The constant function is always included.
- **Invariance defect.** δ(U) = mean_a ‖(I − P_U) T_a P_U‖² / ‖T_a P_U‖² in the π-weighted inner product. δ = 0 for an exactly invariant subspace; sanity check: an isotypic component gives 2·10⁻³¹.
- **Baselines:**
  - 300 random r-dimensional subspaces (with the constant), giving a percentile;
  - for non-groups, the top-r predictive-kernel eigenvectors of Spike 81.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H83.1 | Groups: the learned dominant subspace is invariant | defect in the lowest 20% of random subspaces in ≥ 80% of fitted runs (≥ 5 runs) | < 50% |
| H83.2 | **Non-groups (resets/merges): the learned dominant subspace is invariant**, i.e. closure all the way down | same | same |
| H83.3 | Non-groups: the learned subspace is more invariant than the predictive-kernel eigenvectors used in Spike 81 | δ(learned) < δ(kernel) in ≥ 70% | < 50% |

Anything else is *neither*.

## What this cannot show

- Invariance of the dominant subspace does not by itself say *which* invariant subspace is chosen. A selection rule over submodules (value against cost on the composition factors) is the next step.
- The 70% variance cut is a fixed choice.
- One learner.

## Commands

```
python -m experiments.spike83 predict
python -m experiments.spike83 run
python -m experiments.spike83 analyse
```

## Results

`experiments/results/spike83.json`; per-run outputs in `spike83_raw/`. All 52 runs completed. Groups: 20/22 fitted. Non-groups: 30/30 fitted.

**Measurement bug, found before the verdicts were recorded.**
- In two non-group automata (ids 335 and 422), one minimal state was never visited in the sampled strings. Its visit weight was 0, the defect computation divided by √0, and all defects for those 4 runs became NaN.
- The script's percentile then counted NaN ≤ threshold as false and reported percentile 0, so these runs were wrongly counted as "invariant".
- The hidden states were not saved, so the 4 runs cannot be recomputed. They are excluded.

Both values are kept:

| Fraction | Script output (with the 4 NaN runs) | Corrected (26 valid runs) |
|---|---|---|
| non-groups invariant | 70% | 65% |
| learned beats kernel | 17% | 19% |

The verdicts are the same under both.

| Measure | Groups (20 fitted) | Non-groups (26 valid) |
|---|---|---|
| Median defect of the learned dominant subspace | **0.095** | **0.158** |
| Median defect of random subspaces of equal dimension | 0.271 | 0.229 |
| Median percentile of learned vs random | **0.0** | 0.05 |
| Median defect of the top predictive-kernel eigenvectors | — | **0.120** |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H83.1 | groups: learned subspace in the lowest 20% of random subspaces in 16/20 (80%) | ≥ 80% | **HELD** |
| H83.2 | non-groups: in the lowest 20% in 17/26 (65%) | ≥ 80% held, < 50% broken | **NEITHER** |
| H83.3 | non-groups: learned defect < kernel-eigenvector defect in 5/26 (19%) | ≥ 70% held, < 50% broken | **BROKEN** |

**Reading:**
- **For symmetric concepts, closure goes all the way down** (H83.1 held). The dominant geometry a GRU builds for a group automaton spans an invariant subspace of the input actions: a closed sub-concept, an isotypic block. Its defect is below every random subspace in the median run.
- **For irreversible concepts, only partly** (H83.2 neither).
  - The dominant learned geometry is more closed than chance in most runs (65%, median percentile 0.05), but far from exactly closed (median defect 0.16 against 0.23 for random).
  - In about a third of the runs it is no more closed than a random subspace.
- **The explanation offered for Spike 81's failure is refuted** (H83.3 broken). The predictive-kernel eigenvectors used in Spike 81 are *more* invariant than the learned subspace (median 0.12 vs 0.16, in 21/26 runs). So Spike 81 did not fail because its candidates were not closed.

  Rather, learners on irreversible automata do not organise their dominant geometry around a closed sub-concept as cleanly as they do for groups. Their geometry is less constrained. That agrees with the layered, non-semisimple representation theory: monoids have no complemented blocks to settle into.

**Status of C44.** Holds for groups. Partly holds for monoids. The principle connecting the two cases is still open:
- invariance is shared, but only approximately for monoids;
- what the dominant geometry is in the irreversible case is not yet determined.

A next candidate, in line with §17: the *head* of the observable module (its top composition factor along the J-filtration) rather than any closed subspace, since the learner sees outputs first and the layers beneath are reached only through erasure.
