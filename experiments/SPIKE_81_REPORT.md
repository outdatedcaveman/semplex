# Spike 81: The selection rule beyond groups: arbitrary automata with resets and merges

**Date:** 2026-11-19 · **Status:** complete (pre-registered with predictions in 63b3236; results below) · **Follows:** Spikes 77–80 (the Gibbs selection rule C43, P212–P214). So far it has been tested only on group automata, where symmetry supplies the candidate representations. A law about concepts must say what happens without symmetry.

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

## Results

`experiments/results/spike81.json`; per-run outputs in `spike81_raw/`. All 72 runs fitted (≥ 0.99). A container restart interrupted the runs once; the seeded runner resumed.

| Set | Fitted runs | Gibbs accuracy | NLL Gibbs / energy-only / smoothness-only |
|---|---|---|---|
| Random (12 automata) | 36 | **22%** | 49.5 / **48.7** / 60.9 |
| Discriminating (12) | 36 | **39%** | 78.0 / **61.0** / 66.4 |
| Non-permutation (mixed + free; 15) | 45 | **29%** | 73.9 / **62.3** / 69.6 |

**Pooled argmax accuracy over all 72 fitted runs** (exploratory comparison): Gibbs 31%, energy-only 35%, smoothness-only 32%, chance (1/number of modes) 20%.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H81.1 | random: 22%, NLL not below energy-only | ≥ 60% and below both held; < 50% broken | **BROKEN** |
| H81.2 | discriminating: 39% | same | **BROKEN** |
| H81.3 | non-permutation: 29% | same | **BROKEN** |

**Reading:**
- **The rule does not extend to automata without symmetry, in this generalised form.** On random automata with merges and resets, no rule predicts which predictive mode a trained GRU's leading geometric direction aligns with: all three sit at 31–35%, against 20% chance. Energy alone is marginally best, so the cost term adds nothing here.
- **Two explanations, not yet separated:**
  1. **Symmetry is what makes the law work.** In group automata the candidate representations are irreducible blocks: rigid, mutually orthogonal and invariant under every input. Learners must pick among a few clean options, and value and cost are well defined per block.

     Without symmetry, the predictive kernel's eigenvectors are not invariant under the inputs. The learned geometry need not align with any single one, and "the leading mode" is ill-defined.
  2. **The generalisation is wrong.** The right modes for non-invertible dynamics may not be eigenvectors of the predictive kernel at all, but, e.g., the singular vectors of the Hankel operator in a realisation adapted to the inputs (Ho–Kalman), or invariant subspaces of the letter actions.
- **What survives.** The selection rule C43 is a law about *symmetric* systems: groups, where it holds across learners, optimisers, architectures and samples (Spikes 77–80). Its extension to arbitrary machines fails as formulated here.

  For an "atlas of concepts" this is a substantive boundary. The rule predicts how a concept is represented when the concept has a symmetry, i.e. when its actions are invertible and compose into a group. It does not yet predict representations of irreversible, reset-like concepts. Those were the aperiodic "flip-flop" primes of the periodic table, and their geometry was erasure, not symmetry (C33, Spikes 57–58).
