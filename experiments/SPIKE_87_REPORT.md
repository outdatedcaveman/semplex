# Spike 87: The generator principle: on irreversible automata, does a learner lead with the output vector, the generator of its observable module?

**Date:** 2026-11-19 · **Status:** pre-registered (automata, output vectors, kernel modes and heads in `results/spike87_predictions.json`, committed with this report before any run) · **Follows:**
- Spike 84 (P220). The π-orthogonal head was mixed. Post hoc, the top learned direction was the output vector o in all 15 automata (median squared alignment 0.96).
- The homological-algebra and non-normal-operator reading of 2026-11-19 (`charter/LITERATURE_REVIEW.md`).

## The conjecture

**C45′ (the generator principle).** The observable module O = A·o is cyclic. Its head O / rad(A)·O is a quotient, and the canonical lift of that quotient is the generator o, not the π-orthogonal complement Spike 84 used. A learner on an irreversible automaton leads with o.

This is the candidate bridge to the group case:
- in groups, o splits over complemented isotypic blocks, and value against cost chooses among them;
- in monoids no complements exist, and o is the only canonical piece.

**The obvious deflation:** a network that reads its output linearly from its hidden state may favour o for architectural reasons alone. Hence the control learner.

## Design

**Automata.** 16 *fresh* automata, drawn with seed 87 from Spike 81's pool. The criteria are the same as in Spike 84: all states visited, a non-trivial radical layer and head. Spike 84's 16 automata are excluded, leaving 60 eligible.
- 14 of the 16 have (o · k₁)² < 0.9, where k₁ is the predictive kernel's top mode.
- 15 have (o · g)² < 0.9, where g is the Gibbs-selected mode.
- In 5 automata (223, 254, 194, 359, 20), less than half of o lies in the π-head.

**Learners**, 3 seeds each, 96 runs in total:
- (lin) the Spike 84 recipe: GRU-64 + Adam, linear readout;
- (mlp) the same, with a *trained nonlinear readout* (64 → 64 → 64 → 1, tanh). This is the control.

Fit guard: ≥ 0.99 at length 100.

**Measurement.** u₁ is the top left singular vector of the π-weighted, centred minimal-state centroids, constants removed (as in Spike 84). Its squared alignment is computed with each of:
- ô, the output vector in the same frame, normalised;
- k₁, the top eigenvector of the predictive kernel (sum over t ≥ 1, so it excludes the trivial oo^T term; Spike 81);
- g, the kernel mode the frozen Gibbs rule selects (Spike 81);
- the π-head subspace H (Spike 84), as squared projection.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H87.1 | **Generator lead** (lin): (u₁·ô)² ≥ 0.8 | ≥ 75% of fitted runs (≥ 8 automata) | < 50% |
| H87.2 | The generator beats the kernel's top mode where they differ ((ô·k₁)² < 0.9): (u₁·ô)² > (u₁·k₁)² | ≥ 70% (≥ 4 automata) | < 50% |
| H87.3 | **Not the readout** (mlp control): (u₁·ô)² ≥ 0.8 | ≥ 75% (≥ 8 automata) | < 50% |
| H87.4 | The generator beats the Gibbs-selected kernel mode where they differ: (u₁·ô)² > (u₁·g)² | ≥ 70% (≥ 4 automata) | < 50% |
| H87.5 | **Generator, not π-head**: where o lies mostly outside H (o-in-head < 0.5), (u₁·ô)² > ‖P_H u₁‖². Conservative, since a subspace is compared with a single vector | ≥ 70% (≥ 3 automata) | < 50% |

Anything else is *neither*.

## What this cannot show

- One recurrent architecture; the MLP readout is one kind of nonlinearity.
- **The Harder–Narasimhan rival is deferred.** Computing an HN filtration of O needs:
  - a slope defined on submodules, where the energy share is instance-dependent and not additive;
  - a search over a submodule lattice that is infinite for non-semisimple modules.
  
  That needs theory before it can be pre-registered (candidate Spike 88).
- Leading with o is consistent with, but does not prove, the module-theoretic reading. o is also the target of the loss.
- Extending C45′ to groups (the leader as the dominant isotypic projection of o) is not tested here.

## Commands

```
python -m experiments.spike87 predict
python -m experiments.spike87 run 0/2      # and 1/2
python -m experiments.spike87 analyse
```

## Results

`experiments/results/spike87.json`; per-run centroids in `spike87_raw/`. 96 runs. Fitted at ≥ 0.99: 33 linear-readout runs (13 automata) and 30 MLP-readout runs (12 automata).

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H87.1 | (u₁·ô)² ≥ 0.8 in 28/33 linear-readout runs (85%); median 0.95 | ≥ 75% | **HELD** |
| H87.2 | beats the kernel's top mode in 26/27 runs where they differ (96%) | ≥ 70% | **HELD** |
| H87.3 | trained nonlinear readout: (u₁·ô)² ≥ 0.8 in 8/30 runs (27%); median 0.61 | ≥ 75% held, < 50% broken | **BROKEN** |
| H87.4 | beats the Gibbs-selected kernel mode in 29/30 runs (97%) | ≥ 70% | **HELD** |
| H87.5 | where o lies mostly outside the π-head, the generator beats the head subspace in 12/12 runs (4 automata) | ≥ 70% | **HELD** |

Median squared alignment of u₁, linear vs MLP readout:

| Rival | Linear readout | MLP readout |
|---|---|---|
| o | 0.95 | 0.61 |
| k₁ | 0.48 | 0.51 |
| Gibbs mode | 0.15 | 0.15 |
| π-head (subspace) | 0.84 | 0.72 |

**Reading:**
- **Prospectively, on fresh automata, the dominant direction of a linearly read-out learner is the output vector.** It beats every structural rival: the kernel's top mode, the Gibbs-selected mode, and the π-orthogonal head even where o lies outside the head.
- **That is mostly the readout.** With a trained nonlinear readout the alignment falls to a median of 0.61. Only 27% of runs pass the bar, though o still ranks above k₁ and the Gibbs mode.
- **C45′ as a substrate-general principle is refuted.** The irreversible case's "generator lead" is the architectural fact that a linear readout pulls the top direction onto what it reads, not a property of the observable module.
- What remains for irreversible concepts is weaker. The leading direction is still more aligned with o than with any kernel-derived mode, and no candidate predicts it strongly once the readout is nonlinear. The principle connecting groups and monoids stays open. The Harder–Narasimhan rival (Spike 88) is the next candidate, and it must be tested with a nonlinear readout from the start.
