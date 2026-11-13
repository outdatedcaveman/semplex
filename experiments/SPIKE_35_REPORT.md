# Spike 35: The compiler at six inputs. Certified Occam completion, and do the priors separate?

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spike 34 (at n = 4 the compiler's Occam prior is too coarse: ≈10 of 16 completions tie). This is front 2 (scale) and front 1 (compiler as prior) together. It is the first use of the compiler past the exhaustive atlas.

## Compiler extension (built and tested before this registration)

- **Partial-function lower-bound certificates.** `kernel_bounds.check_not_threshold_partial` (trusted) and `bounds.not_threshold_cert_partial` (untrusted search), tested in `tests/test_bounds_partial.py`. The total-function search, applied to a masked table, is *unsound*: it treats don't-cares as 0 and certifies false lower bounds. A probe found this, and a test documents it. Before this spike the total search was only ever called on total functions, so no past result is affected.
- **Tie sampling.** `netsolve.solve(..., rand_obj=seed)` minimizes a random linear objective over weights, so repeated calls return different satisfying networks of the same wiring. Feasibility is unchanged.

**Occam compilation of a partial task** (care = 48 of 64 points):
1. Try 1 neuron, a single threshold function: CP-SAT, weights in [−4, 4], 20 s.
2. If infeasible, try a certificate that *no completion* is threshold; it is kernel-checked.
3. Otherwise try 3 neurons (2 hidden + output), then 4 (3 hidden + output).

Two neurons in a strictly layered net compute only threshold functions, so cost 3 is the next level. A 3-neuron result is **certified Occam-optimal** when step 2's certificate holds. Every returned net is kernel-evaluated on all 48 care points.

## Design

- **Targets.** 200 six-input functions computed by random 2-hidden-unit step nets: integer weights in [−3, 3], hidden biases in [−6, 6], output weights in [−2, 2]; rng seed 3,500. Kept only if the *total* function carries a kernel-checked not-threshold certificate (so the target has cost exactly 3) and has 16–48 ones.
- **Tasks.** Two random care sets of 48 points per target (seed 3,501): 400 tasks, 16 held-out inputs each.
- **Occam prediction.** Compile as above, then sample 5 minimal-cost nets (`rand_obj` = 0…4) and take the majority vote per held-out input; a 2–2 split would go to the seen majority, but with 5 votes ties cannot occur.
- **NTK.** Kernel ridge (ε = 10⁻³·tr/48) with the width-8 NTK at init, for tanh and ReLU (Monte Carlo, 400,000 units, as Spike 30).
- **Trained nets.** Width 8, tanh and ReLU, 10 seeds per task, AdamW lr 0.03, wd 0.03, 3,000 steps, logistic loss on care points; fitted nets only.
- **Metric.** Balanced held-out accuracy (primary), raw accuracy reported.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H35.1 | The compiler works at n = 6 on partial tasks | a kernel-verified min-cost net is found within the limits for ≥ 95% of tasks | < 80% |
| H35.2 | Its optimality is certified | ≥ 80% of tasks whose Occam cost is 3 are certified Occam-optimal (the not-threshold certificate is found) | < 50% |
| H35.3 | Occam's ties shrink at n = 6 | all 5 sampled minimal nets agree on every held-out input in ≥ 30% of tasks | < 10% |
| H35.4 | **Occam generalizes better than training at n = 6** | Occam balanced − mean(tanh net, ReLU net) balanced ≥ +0.03 | ≤ 0 |
| H35.5 | Occam beats the NTK | Occam balanced − mean(tanh NTK, ReLU NTK) balanced ≥ +0.03 | ≤ 0 |

Reported: the fraction of tasks whose 48 seen labels are consistent with a single threshold function (there Occam picks cost 1 and the target is cost 3); per-method raw accuracy; time per task.
