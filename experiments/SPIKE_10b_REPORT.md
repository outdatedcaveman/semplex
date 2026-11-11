# Spike 10b: Learning rules and grokking, scored against exact ground truth

**Date:** 2026-11-11 · **Status:** parts A, B, C complete; meta-learning of rules **did not work** (unsolved, partly diagnosed) · **Follows:** Spike 09 · **Sources:** Nanda23, Perin26, VallePerez18 (levels in `charter/REFERENCES.md`)

## Questions

1. Spike 09 found that backpropagation fills in underspecified tasks with a table-cheapest function. Is that a property of backpropagation, of any learning rule, or of weight space itself?
2. What can a learning rule do as a function of what it is allowed to observe?
3. When a network groks, is the function it ends on a cheapest completion of its training data?

## Setup

- **Networks:** 4 inputs → 8 tanh units → 1 output (parts A, C); 6 inputs → 16 tanh units → 1 output (part B).
- **Ground truth:** the exact 4-input table (Spike 08); the exact solver for 6 inputs.
- **Rules as observational powers** (`cerp/localrules.py`). The first layer's rule may observe:
  - **A:** its own input X, weights W and output Y;
  - **B:** A plus the scalar output error E, broadcast to every unit;
  - **C:** B plus the downstream weights V.
- **Systematic dictionaries.** For a power and a symmetry group on the hidden index, the dictionary is every invariant monomial of those variables up to order 4, enumerated by code. A local loss is a weighted sum; the first layer follows its gradient. The output layer always uses its own delta rule.

| Hidden-index symmetry | Contractions allowed | Sizes at order 4 (A / B / C) |
|---|---|---|
| Orthogonal (trace monomials, as in Perin26) | pairs only | 11 / 16 / 30 |
| Signed permutations (odd activation, e.g. tanh) | even blocks | 14 / 19 / 38 |
| Permutations (generic activation) | any blocks | 52 / 75 / 163 |

The orthogonal sizes at orders 2, 3, 4 for power A (2, 3, 11) coincide with the counts in Perin26's Table 1 for the same variables. We cannot confirm the sets are identical.

## Results

### Part A: the completion bias across rules, and in weight space (`results/spike10b.json`)

Share of fitted runs that chose a table-cheapest completion (Adam inner loop, 4,000 steps):

| Rule | Fits full tasks | 12 of 16 inputs given | 8 of 16 given |
|---|---|---|---|
| Backpropagation | 99.8% | 89% | 95% |
| Feedback alignment | 95.0% | 90% | 96% |
| Error broadcast (no downstream weights) | 94.2% | 90% | 96% |
| Frozen random first layer | 54.6% | 85% | 90% |
| *Chance* | | *55%* | *25%* |
| **Random untrained networks that fit** (8 million sampled, same init scale) | | **90%** | **89%** |
| Same, init scale 4× larger | | 82% | 71% |

### Part C: what each observational power can express (`results/spike10b_rules.json`)

Plain gradient-descent inner loop, 200 steps:

| Rule | Fits full tasks | Cheapest completion (12 / 8 given) |
|---|---|---|
| Backpropagation (reference) | 99.6% | 92% / 96% |
| Power C: the single term E·(V·Y), coefficient 0.5 | 99.6% (identical to backpropagation) | 92% / 96% |
| Power B, permutation symmetry: the single term E·ΣY | 96.1% | 92% / 97% |
| No first-layer learning | 6.9% | (rarely fits) |
| Power A, meta-learned | 15% | (rarely fits) |
| Power B, orthogonal, meta-learned | 16% | |
| Power B, signed permutations, meta-learned | 12% | |
| Power B or C, meta-learned from scratch or from the good single term | under 1% | |

### Part B: grokking on 6 inputs (64 runs per setting)

Target: XOR of two of the six inputs, trained on a random half of the 64 points.

| Initialization, weight decay | Ended on the planted function | Median step: train fit → generalized | Final effective width |
|---|---|---|---|
| Small, 0 | 60 / 64 | 100 → 200 | 2 in 60 runs |
| Small, 0.1 | 64 / 64 | 100 → 200 | 2 in all |
| Large, 0 | 8 / 64 | 300 → 16,350 | more than 4 in 53 runs |
| Large, 0.1 | 64 / 64 | 200 → 1,700 | 2 in all |

The solver found no single neuron fitting the training half in 16 of 16 splits checked, so the planted 3-neuron function is a cheapest completion there.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H10.1 | The completion bias is specific to backpropagation | **Broke**: three different rules give the same bias (89–90% and 95–96%) |
| H10.2 | The bias is the volume of weight space | **Mostly held**: random fitting networks give 90% and 89%; training matches the first and exceeds the second. It depends on initialization scale |
| H10.3 | A rule that sees only its own layer cannot learn the task | **Held, proved** (`task_blind`, Lean) and observed |
| H10.4 | The trace-monomial dictionary is comprehensive for a tanh layer | **Broke**: the working error-broadcast rule is not a trace monomial of any order (F3) |
| H10.5 | Meta-learning finds good rules in each dictionary | **Failed** in four attempts, including when started from a rule that works (F5) |
| H10.6 | A grokked network ends on a cheapest completion | **Held** in this setup: 64 / 64 with weight decay, at the minimum effective width |

## Findings

**F1. The simplicity bias belongs to the network, not the learning rule.** Backpropagation, feedback alignment and error broadcast reach the same completions at the same rates. Even a frozen random first layer, when it fits, mostly lands on a cheapest function.

**F2. Weight-space volume explains most of it.** Conditioning random untrained networks on fitting the task already gives 90% (12 inputs given) and 89% (8 given). Training adds nothing in the first case and about 6 points in the second. The volume figure falls with a larger initialization scale, so "the bias" is a joint property of architecture and initialization. This is an exact small-scale test of the volume hypothesis (VallePerez18, recalled from memory; not re-read).

**F3. The right dictionary is fixed by the layer's symmetry group.** Trace monomials are the invariants when hidden space has full orthogonal symmetry. An elementwise tanh has only signed-permutation symmetry, and a generic activation only permutation symmetry, so more monomials are invariant.
- The error-broadcast term E·ΣY changes sign when one hidden unit is flipped, while every monomial in which each hidden index appears an even number of times does not. So it lies outside the orthogonal and signed-permutation dictionaries at **every** order.
- It is a single order-2 term in the permutation dictionary, and it fits 96% of tasks.
- Consequence: a dictionary built only from trace monomials cannot express this simple, working local rule at the "broadcast error" level.

**F4. Observational power sets what is learnable, with one proved boundary.**
- Power A is task-blind (Lean theorem): whatever the coefficients, the first layer ends the same for every task.
- Power C contains backpropagation as one order-3 term (checked numerically to 10⁻⁵).
- Power B with permutation symmetry already reaches 96%. Whether power B with only orthogonal or signed-permutation symmetry can do well is **open**: meta-learning found 12–16%, which is a floor, not a ceiling.

**F5. Meta-learning rule coefficients failed, and the cause is only partly understood.** Four attempts, all by differentiating the final loss through training:
- With horizons growing from 10 to 200 steps, a run started from backpropagation drove its coefficient from 0.5 to about 6. At 10 steps the best rule takes very large steps (loss 0.13); at longer horizons the loss sat near 0.5.
- With long horizons only (100 and 200 steps) and a smaller step size, the backpropagation coefficient stayed near 0.6, but other terms drifted to comparable size (for example −0.45 on E²·(V·Y)) and the rule still fit under 1% (`results/spike10b_rules_long_horizon.json`).
- So short horizons are one problem, and drift of the other coefficients under noisy meta-gradients is another. We have not found a configuration that even *keeps* a working rule working.

Perin26 report related fragility ("numerically delicate"; their global rules did not recover backpropagation). This part of the experiment therefore says nothing about the dictionaries' ceilings.

**F6. Grokking, seen against ground truth.** With a large initialization and weight decay, the network fits its training half by step 200 and generalizes at a median step of 1,700, ending in every run on the planted function, which the solver confirms is a cheapest completion, using exactly the minimum two distinguishing units. Without weight decay it mostly stays in a memorizing solution that uses more than four. With a small initialization there is no delay. This matches the account in Nanda23 (read as a report, not the paper) at a scale where "the simple solution" is defined exactly rather than by inspection.

## Gaps

- Rule dictionaries were evaluated on one small architecture; the inner loop for part C is plain gradient descent for 200 steps.
- The meta-optimizer is the unsolved part. Fixes to try: a fixed long horizon, a penalty on update size, or the adjoint approach Perin26 mention.
- The volume comparison uses 8 million samples; for 49 of the 666 twelve-point tasks no fitting random network was sampled.
- Grokking was shown for one planted function on 6 inputs.
- Invariant-theory statements behind F3 (contractions generate the invariants) are recalled, not verified.
