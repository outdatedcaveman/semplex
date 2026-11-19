# Spike 81: The selection rule beyond groups: arbitrary automata with resets and merges

**Date:** 2026-11-19 · **Status:** pre-registered (predictions in `results/spike81_predictions.json`, committed with this report before any run) · **Follows:** Spikes 77–80 (the Gibbs selection rule C43, P212–P214). So far it has been tested only on group automata, where symmetry supplies the candidate representations. A law about concepts must say what happens without symmetry.

## The rule, generalised (no group needed)

For any deterministic automaton, on its minimal (Myhill–Nerode) states Q with visit distribution π:

| Quantity | Definition |
|---|---|
| **Modes** v_i | eigenvectors of the π-weighted, π-centred predictive kernel K(q, r) = Σ_{t ≤ 30} E_w[o(qw)·o(rw)] |
| **Value** e_i | the mode's eigenvalue share |
| **Cost** c_i | ½·mean_a E_π[(v_i(δ_a q) − v_i(q))²] / E_π[v_i²]: the mean squared jump of the mode's coordinate when a letter acts, i.e. the kinetic displacement cost of §16.1 and Spike 79 |

For a group automaton and v in an isotypic component, c_i is exactly the c_ρ of Spikes 77–80. Letters are not required to be invertible, so resets and merges are included.

**Rule (α = 2.49, λ = 3.68 frozen from Spike 77):** P(mode i) ∝ e_i^α · exp(−λ c_i).

**Rivals:**
- energy-only: the top eigenvector of K;
- smoothness-only: the minimum-cost mode, with λ = 3.

## Automata

A pool of 600 random automata (seed 81):
- 5–9 states, 2–3 letters plus an identity letter, random binary output;
- three kinds in rotation:
  - **perm:** all letters are permutations;
  - **mixed:** one letter is a non-injective map (a merge);
  - **free:** arbitrary maps, including resets;
- minimised; kept if they have ≥ 4 states and a non-constant output.

**Random set.** 12 automata drawn uniformly from the pool (seed 810): 6 mixed, 4 free, 2 perm.

**Discriminating set.** 12 drawn from the 225 automata whose Gibbs and energy predictions differ: 7 perm, 3 free, 2 mixed.

## Training and measurement

- GRU + Adam (Spike 77 recipe: width 64, 6,000 steps, length 30), 3 seeds.
- Fit guard: ≥ 0.99 at length 100.
- **Learned leader:** take the top eigenvector u of the learned π-weighted centroid Gram (centroids of hidden states per minimal state). The leader is the mode v_i with the largest |⟨u, v_i⟩_π|.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H81.1 | **Random automata:** the frozen rule predicts the learned leading mode | argmax accuracy ≥ 60% **and** NLL below both rivals (≥ 5 fitted automata) | accuracy < 50% |
| H81.2 | **Discriminating automata:** same | same | same |
| H81.3 | **Without symmetry:** the rule holds on the non-permutation automata (mixed + free) of both sets | same | same |

The 60% threshold is lower than for groups because modes are single vectors. Near-equal eigenvalues make individual modes, and hence alignment, less well defined.

## What this cannot show

- **Near-degenerate permutation automata.** Mode values are near-equal there, so the "leader" can be ill-conditioned; this may lower accuracy for reasons unrelated to the rule.
- Binary output only; one learner.
- α and λ were calibrated on groups. A different normalisation of value (eigenvalue share vs isotypic share) may shift the effective exchange rate.

## Commands

```
python -m experiments.spike81 predict
python -m experiments.spike81 run
python -m experiments.spike81 analyse
```
