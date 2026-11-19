# Spike 84: Do learners concentrate on the head of the observable module? (The irreversible case)

**Date:** 2026-11-19 · **Status:** pre-registered (automata and their exact module structure in `results/spike84_predictions.json`, committed with this report before any run) · **Follows:** Spike 83 (P218). There, symmetric concepts were closed all the way down, irreversible ones only partly, and the explanation for Spike 81 was refuted. Theory: `charter/FOUNDATIONS.md` §17.

## The object

The inputs act on observables by (T_a f)(q) = f(δ_a q). They generate a finite-dimensional matrix algebra A.

| Object | Definition |
|---|---|
| **Radical** rad(A) | the irreversible, nilpotent part. Computed exactly with Dickson's criterion: in characteristic 0, x ∈ rad(A) iff tr(xy) = 0 for all y ∈ A |
| **Observable module** O | span of T_w·o over all words w: everything the output can distinguish through future inputs (Kalman observability) |
| **Radical layer** R | rad(A)·O: the part of O reachable only through erasures |
| **Head** H | the π-orthogonal complement of R in O: the top layer |

All are taken with constants removed and in the visit-weighted (π) inner product.

**Checks:**
- a group automaton (ℤ/7) has rad(A) = 0, so H = O;
- an automaton with a reset letter has a 2-dimensional radical.

**Conjecture C45 (the head).** In irreversible automata, the learner concentrates its geometry on the head: the layer the output reads directly. The radical layer is under-represented relative to its dimension. For groups this is vacuous (H = O), so C45 extends the group picture without changing it.

## Automata

From Spike 81's 600-automaton pool, 76 have every state visited, a non-trivial radical layer and a non-trivial head. 16 were sampled with seed 84: 13 free, 3 mixed. Head fractions dim H / dim O range from 0.2 to 0.88.

## Training and measurement

- GRU + Adam (Spike 81 recipe), 3 seeds. Fit guard ≥ 0.99 at length 100.
- Centroids per minimal state, π-weighted and centred.
- **Shares:** the fraction of learned variance lying in H, in R and in O.
- **Top direction:** the top learned direction's squared projection on H and on R.
- Centroids are saved this time.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H84.1 | **Learned geometry concentrates on the head beyond its dimension:** share in H / share in O > dim H / dim O | ≥ 80% of fitted runs (≥ 6 automata) | < 50% |
| H84.2 | The top learned direction lies more in H than in R | ≥ 70% | < 50% |
| H84.3 | The learned geometry lies in the observable module (closure in its linear form) | share in O ≥ 0.8 in ≥ 80% | < 50% |

Anything else is *neither*.

## What this cannot show

- Concentration on the head is a geometric statement. Which composition factor *within* the head leads (value against cost) is the next step.
- One learner.
- The head is defined via a π-orthogonal complement. Different inner products give different complements of R.

## Commands

```
python -m experiments.spike84 predict
python -m experiments.spike84 run
python -m experiments.spike84 analyse
```
