# Spike 57: Do trained networks build the minimal automaton, in the geometry of its Krohn–Rhodes parts?

**Date:** 2026-11-16 · **Status:** pre-registered (no run) · **Follows:** `charter/FOUNDATIONS.md` §9. This is the first test of the dynamic, exact scale of the atlas programme. It follows Spikes 53–54, whose refutation of C29's tensor row C31 explains post hoc; here the prediction is prospective. **Conjectures:** C31 (economy law), C32 (closure law).

## Question

A small recurrent network is trained only on the *outputs* of a finite automaton. Two questions:
- **Closure (C32).** Does it build the automaton's Myhill–Nerode congruence: internal macrostates equal to the minimal automaton's states, with deterministic (lumpable) macro-transitions?
- **Economy (C31).** Is the geometry of those macrostates the predicted near-minimal faithful representation of the automaton's Krohn–Rhodes parts?
  - a circle for a cyclic group;
  - a simplex for a reset;
  - a 2-dimensional representation for S₃;
  - a direct sum for a direct product;
  - a fibred (interaction-carrying) geometry for a cascade.

## Automata (each with its output map; states are those of the minimal Moore machine, checked by minimization in code)

| Name | Letters | State | Output | Krohn–Rhodes parts |
|---|---|---|---|---|
| Z5 | inc, noop | c ∈ ℤ/5 | [c = 0] | ℤ/5 |
| Z7 | inc, noop | c ∈ ℤ/7 | [c = 0] | ℤ/7 |
| RESET3 | r0, r1, r2, noop | s ∈ {0, 1, 2} | ([s = 0], [s = 1]) | flip-flop on 3 values |
| S3 | swap(0 1), cycle(0 1 2) | permutation of 3 | [identity] | S₃ (ℤ/3 and ℤ/2) |
| PROD | set0, set1, t, noop | (m ∈ {0, 1}, c ∈ ℤ/3); t: c += 1 | ([c = 0], m) | flip-flop × ℤ/3 (direct product) |
| CASC | set0, set1, t, noop | (m, c); t: c += +1 if m = 0, −1 if m = 1 | ([c = 0], m) | flip-flop ≀ ℤ/3 (cascade: the count's direction depends on the mode) |

PROD and CASC have the same states, outputs and letters. They differ only in whether the counter's action depends on the mode. A linear representation of PROD's transformations exists on a direct sum (mode ⊕ circle). CASC's needs mode ⊗ circle: two circles turning in opposite directions.

## Training

- **Model.** GRU, hidden size 32, linear sigmoid readout at every step, binary cross-entropy on outputs only.
- **Data.** Random strings of length 30, letters uniform.
- **Optimiser.** Adam, lr 0.003, 3,000 steps, batch 64.
- **Seeds.** 5 per automaton (seed 5,700 + index).
- **Fit guard.** Output accuracy ≥ 0.99 on 500 random strings of length 100 (length generalization).

## Measurements

These use hidden states from 400 random strings of length 60, skipping the first 5 steps.

- **Centroids:** the mean hidden state per minimal-automaton state.
- **Closure:**
  - k-means with k = number of minimal states (10 restarts); adjusted Rand index (ARI) between clusters and true minimal states;
  - macro-determinism: for each (cluster, letter), the share of transitions that land in the modal next cluster, weighted by count.
- **Circle (Z5, Z7):**
  - share of centroid variance in the top 2 principal components;
  - angle step uniformity: the standard deviation of θ(c + 1) − θ(c) (mod 2π, taken in (−π, π]) over c.
- **Simplex (RESET3):** coefficient of variation of the 3 pairwise centroid distances.
- **S₃:** share of centred centroid variance in the top 2 principal components.
- **Interaction (PROD, CASC):** two-way decomposition of the centroids over (m, c), as in Spike 53. The interaction share ‖r‖² / ‖x − μ‖² is divided by its no-structure value (n − 1)(m − 1)/(nm − 1) = 0.4 to give the relative interaction.

## Hypotheses and kill criteria

"Runs" are fitted (automaton, seed) runs.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H57.1 | **Closure (C32):** the net's macrostates are the minimal automaton's, with lumpable dynamics | ARI ≥ 0.95 and determinism ≥ 0.99 in ≥ 80% of runs (all automata) | in < 50% |
| H57.2 | Cyclic groups are circles | Z5 and Z7: top-2 share ≥ 0.80 and step SD ≤ 0.35 rad in ≥ 80% of runs | < 50% |
| H57.3 | A reset is a simplex | RESET3: distance CV ≤ 0.15 in ≥ 80% of runs | < 50% |
| H57.4 | S₃ uses its 2-dimensional representation | S3: top-2 share ≥ 0.80 in ≥ 80% of runs | < 50% |
| H57.5 | **Economy: products are sums, cascades are fibred (C31)** | PROD relative interaction ≤ 0.30 in ≥ 80% of runs **and** CASC ≥ 0.60 in ≥ 80% | CASC's median ≤ PROD's median |

Anything else is *neither*.

**Guard.** An automaton's hypotheses get a verdict only if at least 3 of its 5 seeds fit. H57.1 is judged over all fitted runs.

**Reported without criteria:**
- the Fourier step of each circle;
- the dimension holding 90% of centroid variance;
- training steps to first reach 0.99 training accuracy, by automaton (construction-cost law, exploratory).

## What this cannot show

- One architecture (GRU), one width and one training recipe.
- Linear-representation predictions are tested on a nonlinear network's hidden states.
- Six automata, chosen to separate the predictions, not sampled from all automata.

## Commands

```
python -m experiments.spike57 run
python -m experiments.spike57 analyse
```

## Results

(Not run.)
