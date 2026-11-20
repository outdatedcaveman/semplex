# Spike 51: Do trained networks reason like a rational nonmonotonic logic?

**Date:** 2026-11-16 · **Status:** complete (pre-registered in f667769; results below) · **Follows:** Spike 49 (nets output what every minimum circuit agrees on, 98–99%) and `charter/FOUNDATIONS.md` §1–2 (that relation is rational: Theorems 1–2, P175–P176). **Conjecture:** C24.

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

`experiments/results/spike51.json`; raw votes in `spike51_raw/run.json`. All nets fit (99.99%). Literals: 383 CM, 166 RM (tasks with a split input), 383 counter.

**Bug fixed before any verdict was read:** the first analysis run stopped while writing JSON (numpy integers). The only change was the serializer; no measurement changed.

| Rule (violation rate) | Nets, confident (≥ 9/10) | Nets, majority (≥ 6/10) | Kernel | Minimal-model relation |
|---|---|---|---|---|
| Cautious Monotony | 0.043 (93/2159) | 0.052 (137/2637) | 0.051 (137/2681) | 0.000 (0/426) |
| Cut | 0.059 (130/2196) | 0.049 (129/2629) | 0.051 (137/2681) | 0.000 (0/426) |
| Rational Monotony | 0.150 (124/824) | 0.132 (150/1137) | 0.055 (30/546) | 0.000 (0/130) |
| Monotony (retraction under counter-evidence) | 0.349 (753/2159) | 0.251 (663/2637) | 0.197 (529/2681) | 0.995 (432/434) |

Retraction overlap with the minimal-model relation (nets' counter literals, inputs where both draw a conclusion): when a net retracts, the minimal-model relation also retracts in 96% of cases; of the minimal-model relation's retractions, nets make 48%.

### Verdicts

- **H51.1: held.** Cautious Monotony is violated in 4.3% of instances (bar 5%).
- **H51.2: neither.** Cut is violated in 5.9% (bar 5%; broken above 15%).
- **H51.3: neither.** Rational Monotony is violated in 15.0% (bar 10%; broken above 25%).
- **H51.4: neither.** Nets retract 35% of conclusions under counter-evidence (bar 10%), but they make only 48% of the minimal-model relation's retractions (bar 50%).
- **C24: neither supported nor refuted.**

### Reading

1. **Nets are approximately cumulative.** Adding one of their own conclusions to the evidence leaves the others in place about 95% of the time (Cautious Monotony and Cut).
2. **Rational Monotony is where they fall short:** adding a fact they were unsure about changes 15% of their confident conclusions, against 0% for the logic.
3. **They are nonmonotonic in the logic's direction, but stubborn.** When a net drops a conclusion after counter-evidence, the logic drops it too, 96% of the time. But the logic drops nearly everything (counter-evidence against a forced value changes the minimum cost, so the preferred hypotheses are replaced), and the nets drop only half of that.
4. **Rationality does not separate nets from kernels.** The kernel is as cumulative (5.1%) and more rationally monotone (5.5%). What distinguishes the net is *which* conclusions it draws (Spikes 49–50), not that it reasons more lawfully.

**Consequence for the theory.** The nets' consequence relation is close enough to cumulative that the Lehmann–Magidor reconstruction of an implicit ranking is meaningful, but not exact: a ranking elicited from behaviour will need a tolerance. The stubbornness under counter-evidence is a measurable property of gradient training (inertia from the previous solution's basin is the obvious candidate) and a concrete difference from ideal minimal-cost inference.
