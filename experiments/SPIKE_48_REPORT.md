# Spike 48: Does the pull toward the minimum circuit hold at 8 and 10 inputs?

**Date:** 2026-11-15 · **Status:** complete (pre-registered in 911c34d; results below) · **Follows:** Spike 36 (C19′ at n = 5, 6: where trained nets depart from their kernel on held-out inputs, the minimum-circuit completion sides with the net in 73–81% of cases). **Gap:** A6 (scale). **Enabled by:** `netsolve.compile_partial` (Gemini G3, P163), which compiles and certifies care-set tasks at n = 8, 10.

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

`experiments/results/spike48.json`; raw outputs in `spike48_raw/`. Every task compiled and every sampled net was verified on its seen inputs. All cells pass the guards. Tasks have cost 1 (20–25 per matched cell, where the seen inputs happen to be linearly separable) or cost 3.

| Cell | n | seen | `sides` | agree Occam | agree kernel | bal. net | bal. kernel | bal. Occam | certified | fit | disagreements |
|---|---|---|---|---|---|---|---|---|---|---|---|
| n8_matched | 8 | 64 | 0.716 | 0.895 | 0.857 | 0.879 | 0.819 | 0.891 | 0.92 | 0.998 | 27451 |
| n10_matched | 10 | 80 | 0.649 | 0.897 | 0.887 | 0.886 | 0.849 | 0.881 | 0.85 | 1.000 | 53144 |
| n8_literal | 8 | 192 | 0.941 | 0.977 | 0.834 | 0.977 | 0.829 | 0.987 | 0.98 | 1.000 | 10634 |

For reference, Spike 36 at n = 6 (48 seen): `sides` 0.79–0.81, agree Occam 0.89–0.90, agree kernel 0.80–0.83.

### Verdicts

- **H48.1: neither.** `sides` is 0.716 at n = 8 (above the 0.65 bar) and 0.649 at n = 10 (below it by 0.001). The pull is present at both sizes and well above 0.50, but it does not clear the bar at n = 10.
- **H48.2: neither.** Occam predicts the net better than the kernel by +0.039 at n = 8 (above +0.02) and by +0.010 at n = 10 (below it).
- **H48.3: held.** Trained nets beat their kernel by +0.060 (n = 8) and +0.037 (n = 10) in balanced accuracy.

### Reading

1. **The effect survives scale but shrinks at a fixed number of labels per dimension:** 0.80 (n = 6), 0.72 (n = 8), 0.65 (n = 10). It is not an artifact of n ≤ 6, and it is not constant either.
2. **With more data it is very strong.** In the literal cell (75% of inputs seen at n = 8) Occam sides with the net on 94% of its departures from the kernel, and agrees with the net on 97.7% of held-out inputs against the kernel's 83.4%.
3. **So the pull tracks how well the seen data pin down the circuit.** With 8 labels per dimension the minimum-cost completion is itself uncertain (its accuracy is 0.88–0.89, about the net's), and 20–25% of tasks look linearly separable on the seen inputs. With 192 labels the minimum circuit is nearly determined (accuracy 0.987) and nets follow it.
4. **Occam and the net generalize about equally** in the matched cells (0.89 vs 0.88), both ahead of the kernel (0.82–0.85).

**Limits.** One care set per target; two-unit targets only; width 8; 5 seeds at n = 10. The dependence on sample size is read off three cells, not measured as a curve.

**Next.** Measure the pull as a function of the number of seen inputs at fixed n. The prediction from this reading: `sides` rises with the fraction of tasks whose minimum circuit is unique on the seen inputs.
