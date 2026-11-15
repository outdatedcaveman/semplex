# Spike 48: Does the pull toward the minimum circuit hold at 8 and 10 inputs?

**Date:** 2026-11-15 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 36 (C19′ at n = 5, 6: where trained nets depart from their kernel on held-out inputs, the minimum-circuit completion sides with the net in 73–81% of cases). **Gap:** A6 (scale). **Enabled by:** `netsolve.compile_partial` (Gemini G3, P163), which compiles and certifies care-set tasks at n = 8, 10.

## Question

Everything supporting C19′ is at n ≤ 6. Does the same measurement give the same answer at n = 8 and n = 10?

## Design

The protocol is Spike 36's, with one design decision. Spike 36 showed 48 of 64 inputs at n = 6, which is 8 labelled inputs per input dimension. Showing 75% of the inputs at n = 8 would be 192 labels for a two-unit target, a much easier task on which all predictors may agree. So there are three cells:

| Cell | n | Seen inputs | Held-out inputs | Why |
|---|---|---|---|---|
| `n8_matched` | 8 | 64 (8 per dimension) | 192 | same labels per dimension as Spike 36 |
| `n10_matched` | 10 | 80 (8 per dimension) | 944 | same, one size further |
| `n8_literal` | 8 | 192 (75%) | 64 | Spike 36's fraction, taken literally |

- **Targets.** Per cell, 100 targets from Spike 36's generator (random two-hidden-unit step nets, weights in −3…3, 25–75% ones, with a kernel-checked certificate that the full function is not a threshold function). One random care set per target. Seeds 4,800 (n = 8) and 4,810 (n = 10); the two n = 8 cells share targets and differ in care sets (seeds 4,801 and 4,802).
- **Occam.** `compile_partial` with |w| ≤ 4 gives the minimum cost and, where it exists, a weight-independent certificate of minimality. The completion is the majority vote of 5 nets sampled at that cost with random objectives. The fraction of tasks with a certificate is reported.
- **Nets.** `spike36.train` unchanged: two-layer tanh, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps, 10 seeds per task (5 at n = 10), seed 4,820 + cell index. Only nets that fit every seen input are analysed.
- **Kernel.** `spike36.ntk(n, "tanh")` with ridge on the seen inputs, as in Spike 36.
- **Measures**, on held-out inputs: `sides` (among inputs where the net differs from the kernel, the fraction where the Occam completion equals the net), agreement of the net with each predictor, balanced accuracy of each against the truth.

## Hypotheses and kill criteria

The two matched cells carry the verdicts. `n8_literal` is reported and decides nothing.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H48.1 | The Occam pull holds at scale | `sides` ≥ 0.65 in both matched cells | `sides` ≤ 0.50 in either |
| H48.2 | Occam predicts the net better than the kernel does | agree_occam − agree_ntk ≥ +0.02 in both | ≤ 0 in either |
| H48.3 | Training beats the kernel | bal(net) − bal(kernel) ≥ +0.02 in both | ≤ 0 in either |

Anything else is *neither*.

**Guards.** A cell gives no verdict if fewer than 90% of its nets fit, fewer than 90% of its tasks compile, or it has fewer than 500 net–kernel disagreement points.

**What each outcome would mean.** If H48.1 holds, C19′ is not an artifact of n ≤ 6 and gap A6 closes for two-unit targets. If it breaks, the one surviving result of this line is a small-n effect and the program's centre moves to the compiler and the formal side.

## Commands

```
python -m experiments.spike48 tasks
python -m experiments.spike48 occam CELL
python -m experiments.spike48 nets CELL
python -m experiments.spike48 analyse
```

## Results

(To be filled after the runs.)
