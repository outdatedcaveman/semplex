# Spike 51: Do trained networks reason like a rational nonmonotonic logic?

**Date:** 2026-11-16 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 49 (nets output what every minimum circuit agrees on, 98–99%) and `charter/FOUNDATIONS.md` §1–2 (that relation is rational: Theorems 1–2, P175–P176). **Conjecture:** C24.

## Question

Theorem 2 says inference by minimal cost satisfies Cut, Cautious Monotony and Rational Monotony, and is nonmonotonic. Spike 49 says nets approximate that inference on single inputs. Here the nets' *own* consequence relation is tested directly, as logic: conclusions are retrained on and checked for what survives.

## The nets' consequence relation

A task is a target f on n = 4 inputs and a set D of 8 seen inputs with their labels. Ten nets are trained on D (Spike 36's recipe: tanh, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps).

- **Definition.** D |~ (x := v) when at least 9 of 10 seeds output v at the unseen input x ("confident").
- **Variant (reported).** At least 6 of 10 seeds, a majority.

## Design

- **Tasks.** The 128 representatives of the cost-3 function classes at n = 4, each with 3 random care sets of 8 inputs: 384 tasks, seed 5,100.
- **Literals added to the evidence**, per task (seed 5,101), each giving a new training set D + a with 10 fresh seeds:
  - **CM literal:** a random confident conclusion (x_a := v_a) of D;
  - **RM literal:** a random unseen input on which seeds split (2 to 8 of 10 say 1), with a random value;
  - **counter literal:** a random confident conclusion with its value flipped.
- **Instances**, over every other unseen input b:

| Rule | Instance | Violation |
|---|---|---|
| Cautious Monotony | D \|~ a (CM literal) and D \|~ b | not D + a \|~ b |
| Cut | D \|~ a (CM literal) and D + a \|~ b | not D \|~ b |
| Rational Monotony | not D \|~ ¬a (RM literal) and D \|~ b | not D + a \|~ b |
| Monotony | counter literal added, D \|~ b | not D + a \|~ b (a retraction) |

- **Controls, on the same instances:** the exact minimal-model relation (atlas costs at n = 4; violates nothing by Theorem 1), and the kernel-ridge predictor (`spike36.ntk`, deterministic, so "confident" means its sign), each with its own conclusions as literals.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H51.1 | Nets satisfy Cautious Monotony | violation rate ≤ 0.05 | > 0.15 |
| H51.2 | Nets satisfy Cut | violation rate ≤ 0.05 | > 0.15 |
| H51.3 | Nets satisfy Rational Monotony | violation rate ≤ 0.10 | > 0.25 |
| H51.4 | Nets are nonmonotonic in the logic's way | retraction rate under counter-evidence ≥ 0.10, **and** among conclusions the minimal-model relation retracts, nets retract ≥ 50% | retraction rate < 0.03 |

Anything else is *neither*. C24 is supported if H51.1–H51.3 hold, and refuted if H51.1 or H51.3 is broken.

**Guards.** No verdict if fewer than 90% of nets fit, or a rule has fewer than 300 instances.

**Reported without criteria:** the majority variant; the kernel's rates; the fraction of net retractions that the minimal-model relation also makes (precision of retraction).

## Commands

```
python -m experiments.spike51 run
python -m experiments.spike51 analyse
```

## Results

(To be filled after the runs.)
