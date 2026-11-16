# Spike 58: Does the learned abstraction have causal power, and is its geometry the character of the minimal faithful representation?

**Date:** 2026-11-16 · **Status:** pre-registered (no run) · **Follows:** Spike 57. That spike's registered closure test (clusters) broke, while an exploratory linear probe found the minimal automaton exactly (P186); this spike confirms that prospectively. Also follows `charter/FOUNDATIONS.md` §9–§10. **Conjectures:** C31, C32; Plato and Aristotle (§9.1) as an experiment.

**Tools applied** (shared by the user and evaluated in `charter/LITERATURE_REVIEW.md`):
- **Interchange interventions on hidden states:** the reading/writing idea of weight-space programming (2611.18114, AHA, auto-WSP) applied to activations. This tests causal power directly.
- **Persistent homology** (`ripser`; Postol, *Algebraic Topology for Data Scientists*): the loop topology of cyclic concepts.
- **Character theory:** an exact, parameter-free form of the economy law.
- **A non-solvable group (A₅)** next to solvable ones: the Barrington grading of the periodic table (§10.2).

## Automata

| Name | Letters | States | Output each step | Group content |
|---|---|---|---|---|
| Z5, Z7 | inc, noop | ℤ/n | [c = 0] | cyclic (solvable) |
| RESET3 | r0, r1, r2, noop | 3 | ([s = 0], [s = 1]) | none (aperiodic) |
| S3 | (0 1), (0 1 2) | S₃ (6) | one-hot of g(0) (3) | solvable |
| A4 | (0 1 2), (0 1)(2 3) | A₄ (12) | one-hot of g(0) (4) | solvable |
| A5 | (0 1 2), (0 1 2 3 4) | A₅ (60) | one-hot of g(0) (5) | **non-solvable simple** |
| PROD, CASC | as Spike 57 | 6 | as Spike 57 | flip-flop × ℤ/3, flip-flop ≀ ℤ/3 |

For S3, A4 and A5 the output reveals only g(0), so the state is not observable: the network must build the group from outputs. Minimality of every automaton is checked by Moore minimization in code.

## Training

- **Model.** GRU, hidden size 64, letter embedding 16, linear readout, binary cross-entropy on all output bits.
- **Data and optimiser.** Random strings of length 30; Adam, lr 0.003, batch 64, 8,000 steps.
- **Seeds.** 5 per automaton (seed 5,800 + 10·index + seed).
- **Fit guard.** Output accuracy ≥ 0.99 on 500 strings of length 100.
- **Learning-cost record.** Steps to first reach training accuracy ≥ 0.99, checked every 25 steps; −1 if never.

## Measurements (hidden states of 400 strings of length 60, steps 5–59)

**Closure (probe form).**
- Multinomial logistic probe from hidden state to minimal state, trained on half the strings and tested on the other half.
- Probe-state macro-determinism, as in Spike 57's exploratory analysis.

**Causal power (interchange intervention).** For 2,000 trials:
- take a test string; at a random step t ∈ [10, 39] its state is s;
- replace the hidden state by the hidden state of another string at a step where its state is s′ ≠ s (random);
- run the remaining 20 letters of the original string from there;
- *success* if every output bit on the remaining steps equals the automaton's output when run from s′.

**Micro-inertness control:** the same, but with a donor in the *same* state s. Success if the outputs equal the run from s.

**Characters.** Groups only (Z5, Z7, S3, A4, A5).
- Take the centroid per group element, centred and normalised to unit length; G is the cosine Gram matrix.
- For each nontrivial real irreducible character χ (complex-conjugate pairs merged by taking real parts), the predicted similarity is K_χ(g, h) = Re χ(g⁻¹h) (the expected Gram of a random vector's orbit under that representation).
- Score each χ by the Spearman correlation between the off-diagonal entries of G and K_χ.

The economy law predicts the best-scoring character is a minimal faithful irreducible:
- Z_n: χ_k with k = ±1 (the lowest frequency, a circle);
- S₃: the 2-dimensional standard;
- A₄: the 3-dimensional irreducible (its only faithful one);
- A₅: one of the two 3-dimensional icosahedral irreducibles (not the faithful 4- or 5-dimensional ones).

**Topology.** Z5 and Z7: persistent homology (Vietoris–Rips, ripser) of 1,500 sampled hidden states; ratio of the largest to the second-largest H₁ persistence.

**Interaction.** PROD and CASC: relative interaction as in Spike 57.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H58.1 | **Closure (C32), probe form:** the minimal automaton is a closed, lumpable, linearly readable coarse-graining | probe accuracy ≥ 0.99 and determinism ≥ 0.99 in ≥ 80% of fitted runs | < 50% |
| H58.2 | **The abstraction has causal power** (Plato): setting the macrostate sets the future | intervention success ≥ 0.98 in ≥ 80% of fitted runs | < 50% |
| H58.3 | **Micro-detail is causally inert** (Aristotle: only the macrostate matters) | same-state swap success ≥ 0.99 in ≥ 80% of fitted runs | < 50% |
| H58.4 | **Economy as characters (C31):** the learned Gram is the character of a minimal faithful irreducible | best character is the predicted one in ≥ 80% of fitted group runs | < 50% |
| H58.5 | Cyclic concepts have one loop | Z5, Z7: largest H₁ persistence ≥ 3× the second in ≥ 80% of fitted runs | < 50% |
| H58.6 | **Construction cost grows along the table** | Spearman between the predicted order RESET3 < Z5 < Z7 < S3 < A4 < A5 and median steps-to-0.99 (never-reached counts as ∞) ≥ 0.90, **and** CASC median > PROD median | Spearman ≤ 0.50 |

Anything else is *neither*.

**Guard.** An automaton contributes to H58.1–H58.5 only with ≥ 3 fitted seeds. No verdict on H58.4 if fewer than 3 group automata qualify.

**Reported without criteria:**
- the character scores per irreducible;
- PROD and CASC relative interaction (replication of H57.5's direction);
- the persistence diagrams;
- whether A₅ (non-solvable) costs more than size alone predicts (steps per log |G|).

## What this cannot show

- One recurrent architecture (the table is substrate-relative: transformers next).
- Probes and interventions read the representation linearly and locally.
- Characters predict the expected Gram of a random orbit, not a particular one.

## Commands

```
python -m experiments.spike58 run
python -m experiments.spike58 analyse
```

## Results

(Not run.)
