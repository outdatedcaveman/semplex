# Spike 83: The invariance principle: is a learned concept's dominant geometry itself closed under the inputs?

**Date:** 2026-11-19 · **Status:** pre-registered (automata fixed in `results/spike83_predictions.json`, committed with this report before any run) · **Follows:**
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
