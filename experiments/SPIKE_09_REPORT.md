# Spike 09: Do trained networks land on the atlas's optimal circuits?

**Date:** 2026-11-11 · **Status:** complete · **Follows:** Spike 08/08b; motivated by Nanda et al. (arXiv:2301.05217), see `charter/LITERATURE_ATLAS.md`

## Question

The atlas knows the optimal circuit for every 4-input task. When a real-valued network is trained by gradient descent on the same tasks, does it find those optima? Does every run find the same circuit? And when the task leaves some inputs unspecified, does training fill them in the way the table-driven compiler would?

## Setup (`cerp/train.py`, `experiments/spike09.py`)

- **Network:** 4 inputs → 8 tanh units → 1 logit. Full-batch AdamW, cross-entropy, weight decay 0, 0.03 or 0.1. About 27,000 networks, trained in batches.
- **Reading a circuit off a trained net:** each hidden unit induces a threshold function, "pre-activation ≥ 0". The learned layer is then a set of observations in the Protocol-Frame sense.
  - **Effective width** is the smallest number of learned units whose threshold functions determine the computed function.
  - It is compared with **w\***, the minimum over all threshold functions, which the atlas gives exactly.
- **E1:** all 222 elements, fully specified, 10 seeds each.
- **E2:** 1,332 partial tasks (12 or 8 of the 16 inputs specified), 5 seeds each.

## Results (`results/spike09.json`)

**E1, fully specified tasks:**

| Weight decay | Fit | Hard-step version computes the same function | Minimal effective width at step 100 → 6,000 | Mean distinct circuits per task (10 seeds) |
|---|---|---|---|---|
| 0 | 99.8% | 100% | 42% → 53% | 7.1 |
| 0.03 | 100% | 100% | 43% → 56% | 6.6 |
| 0.1 | 100% | 100% | 42% → 59% | 6.2 |

Minimality by how hard the function is (weight decay 0.1):

| w* (threshold functions needed) | Networks | Found a minimal layer |
|---|---|---|
| 1 | 140 | 100% |
| 2 | 1,590 | 46% |
| 3 | 470 | 91% |
| 4 (parity) | 10 | 50% |

**E2, partial tasks:**

| Inputs specified | Learned completion is the table's cheapest | Chance level | Mean neurons: learned / cheapest / random completion |
|---|---|---|---|
| 12 of 16 | 88% | 55% | 2.76 / 2.65 / 3.29 |
| 8 of 16 | 94–95% | 25% | 1.84 / 1.78 / 3.30 |

Weight decay made no measurable difference in E2.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H9.1 | Trained nets realize a threshold circuit (the atlas's family is a faithful description) | **Held**: replacing every tanh by a hard step never changed the computed function |
| H9.2 | Training finds a minimal first layer | **Partly**: 53–59% overall; always for single-neuron functions, often not for w* = 2 |
| H9.3 | Weight decay drives circuits toward the minimum | **Weak**: +6 points at the strongest setting; no sharp "cleanup" phase |
| H9.4 | Different seeds find the same circuit | **Broke**: about 6–7 distinct circuits per 10 seeds; only 17–21 of 222 tasks were unanimous |
| H9.5 | Training completes partial tasks with the table's cheapest function | **Held strongly**: 88–95%, far above chance |

## Findings

**F1. Gradient descent behaves like the table-driven compiler on underspecified tasks.** With half the inputs unspecified, the function a trained network settles on is one of the cheapest completions in 94–95% of runs (chance: 25%). The atlas's neuron count is therefore a good predictor of *which generalization* training picks. This is the simplicity bias, measured against exact ground truth instead of a proxy. It also connects to Spike 08b's geometry result: cheap functions occupy almost all of weight space.

**F2. The function is predictable; the circuit is not.** For the same task, ten seeds produce six or seven different minimal-or-near-minimal first layers. This is what the atlas's isomer counts predicted (up to 201 minimal layers for one element). For this setting, "universality" holds at the level of the element and fails at the level of the circuit.

**F3. Training approaches minimal circuits gradually, and only partway.** The share of minimal layers rises smoothly from 42% to 53–59% over training. There is no memorize-then-clean-up transition here, and weight decay helps only a little. Two caveats on comparing this with Nanda et al.: all 16 inputs are in the training set, so there is nothing to grok; and "minimal" here means fewest *distinguishing* units, not smallest weights.

**F4. Functions needing two threshold units are where training is wasteful.** Networks found a minimal layer for 91% of the w* = 3 tasks but only 38–46% of the w* = 2 tasks. A likely reason: these have many near-minimal 3-unit solutions that are easier to reach. Unverified.

**F5. A theory link from Spike 08 fails at 4 inputs.** "Neurons = w* + 1" held for every 3-input function. At 4 inputs, **31 of the 78 four-neuron elements are the XOR of two single neurons**: two threshold functions determine them (w* = 2), but combining those two takes more than one output neuron, so they still cost 4. The minimum determining width is a lower bound on cost, not the cost. The correct statement needs the cost of the combining function as well, which is what the layer-peeling recursion already computes.

## Gaps

- One architecture (8 tanh units), one optimizer, 4 inputs. Nothing here is evidence about large networks.
- Effective width counts distinguishing units; it ignores weight magnitudes, so it cannot see weight decay shrinking a circuit without changing its logic.
- F4's explanation is a guess.
- No task with a held-out set large enough to show grokking; that needs more inputs.
