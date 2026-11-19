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

## Measurement bug fixed before any run produced a result

- `predict()` merged the module structure into each automaton record. Its key `"O"` (observable-module basis) overwrote the automaton's output vector `"O"`, so `run` crashed on the first training step and no result was produced.
- Fix: `train` reads the output vector from Spike 81's seeded pool by automaton id, asserting the transition table matches; all 16 match. `measure` keeps using `"O"` as the module basis, as intended.
- No hypothesis, criterion or automaton changed.

## Results

`experiments/results/spike84.json`; per-run outputs and centroids in `spike84_raw/`.
- 48 runs; 37 fitted with a valid measurement (15 automata).
- Automaton 356: its 3 runs did not fit at ≥ 0.99.
- Automaton 461: 1 of 3 at 0.99.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H84.1 | head share above its dimension share in 29/37 (78.4%) | ≥ 80% held, < 50% broken | **NEITHER** |
| H84.2 | top learned direction more in H than in R in 27/37 (73.0%) | ≥ 70% | **HELD** |
| H84.3 | share in O ≥ 0.8 in 37/37 | ≥ 80% | **HELD, but vacuous** (see below) |

Medians: share in H 0.90 against a dimension fraction of 0.29; top direction 0.98 in H, 0.02 in R.

**H84.3 is true by construction.** The automata are minimal, so every pair of states is distinguishable by the output. That makes O the whole constants-removed space (dim O = m − 1 in all 16), and share_obs = 1 identically. This should have been seen at pre-registration. The verdict is recorded as it came out and carries no evidence.

**The failures are whole automata, not seeds.** 178, 581, 82 (3/3 runs each) and 461 all have a one-dimensional head and put most of their geometry in R. Two other automata with dim H = 1 (257, 527) do not fail in the same way.

## Exploratory (after the verdicts, not pre-registered): the learner leads with the output generator, not the π-orthogonal head

Two quantities per automaton:
- the fraction of the centred, π-weighted output vector o lying in H;
- the squared alignment of the top learned direction with o.

| Automaton | dim H / dim O | o in H | Share in H (runs) | (top · o)² (runs) |
|---|---|---|---|---|
| 178 | 1/4 | 0.19 | 0.15, 0.14, 0.12 | 0.98, 0.99, 0.98 |
| 82 | 1/4 | 0.15 | 0.23, 0.22, 0.25 | 0.97, 0.97, 0.96 |
| 581 | 1/4 | 0.50 | 0.20, 0.21, 0.23 | 0.85, 0.85, 0.89 |
| 257 | 1/4 | 0.63 | 0.46, 0.46, 0.49 | 0.98, 0.99, 0.94 |
| 461 | 1/5 | 0.83 | 0.45, 0.38 | 0.88, 0.84 |
| 293 | 2/7 | 0.91 | 0.76–0.79 | 0.98 |
| 527 | 1/4 | 0.95 | 0.88–0.91 | 0.98–0.99 |
| the other 8 | ≥ 3/4 | ≥ 0.98 | 0.96–1.00 | 0.73–1.00 |

- **In every automaton the dominant learned direction is the output vector itself** (median alignment ≈ 0.96).
- The share in the π-orthogonal head follows how much of o lies in that complement. When o lies mostly in R (178, 82), so does the geometry.

**Interpretation.** The head of a module is a *quotient*, O / rad(A)·O. Since O = A·o is cyclic, the head is spanned by the image of the generator o. The π-orthogonal complement is one arbitrary lift of that quotient, and it is the wrong one. The learner picks the lift through o. This was flagged under "What this cannot show" ("different inner products give different complements of R").

So the corrected conjecture is **C45′: the learner leads with the generator of its observable module.** It is a candidate connecting principle with the group case:
- for groups, o splits over complemented isotypic blocks and value against cost picks among them;
- for monoids there is no complement, and the only canonical piece is the generator.

This is post hoc and needs its own pre-registered test with a non-trivial rival. A readout-trained network may favour o for architectural reasons alone, so a learner without a linear readout is the control.
