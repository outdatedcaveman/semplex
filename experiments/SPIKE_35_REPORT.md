# Spike 35: The compiler at six inputs. Certified Occam completion, and do the priors separate?

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 07e7533; results below) · **Follows:** Spike 34 (at n = 4 the compiler's Occam prior is too coarse: ≈10 of 16 completions tie). This is front 2 (scale) and front 1 (compiler as prior) together. It is the first use of the compiler past the exhaustive atlas.

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

---

## Results

`results/spike35.json`; exploratory analysis in `results/spike35_exploratory.json`. 400 tasks, 16 held-out inputs each. Net fit rates: tanh 0.999, ReLU 0.999.

| Predictor | Balanced accuracy | Raw accuracy |
|---|---|---|
| **Occam (compiler, 5-sample vote)** | **0.902** | 0.902 |
| Trained nets, tanh | 0.894 | 0.894 |
| Trained nets, ReLU | 0.886 | 0.886 |
| NTK, ReLU | 0.796 | 0.796 |
| NTK, tanh | 0.788 | 0.788 |

**Compiler.**
- A kernel-verified minimum-cost net was found for **100%** of tasks, at a mean of 1.6 s per task including 5 tie samples.
- **96.2%** of the cost-3 answers are *certified* Occam-optimal by a kernel-checked partial not-threshold certificate.
- In 7.75% of tasks the 48 seen labels fit a single threshold function, so Occam (correctly, by its own lights) picks cost 1, while the target is cost 3.
- All 5 sampled minimal nets agree on every held-out input in 9.5% of tasks.

### Verdicts

| # | Verdict |
|---|---|
| H35.1 | **Held.** 100% found and verified. |
| H35.2 | **Held.** 96.2% certified optimal. |
| H35.3 | **Broken (narrowly).** 9.5% < 10%. The criterion demanded agreement on *all 16* held-out inputs across 5 samples. Ties remain, but the 5-sample vote is accurate (0.902). |
| H35.4 | **Neither held nor broken.** Occam − nets = +0.012 (between 0 and +0.03). |
| H35.5 | **Held.** Occam − NTK = **+0.110**. |

### Exploratory (post hoc): where does feature learning move?

| | tanh | ReLU |
|---|---|---|
| Net agrees with Occam on held-out inputs | **0.910** | **0.905** |
| Net agrees with its NTK | 0.808 | 0.834 |
| Where net ≠ NTK (12,277 / 10,625 cases): Occam sides with the net | **0.802** | **0.799** |
| … and the net is right | 0.776 | 0.771 |

## Findings

**F1. The compiler works past the atlas, with certificates.** At n = 6 (2⁶⁴ functions, far beyond exhaustive tables), partial-task Occam compilation takes 1.6 s per task and is certified optimal in 96% of cost-3 cases. This is front 2's first deliverable. The soundness bug found on the way (total-function certificates on masked tables) is fixed in the kernel and tested.

**F2. The n = 4 platform was pathological.** At n = 6 every predictor generalizes far above chance (0.79–0.90 balanced, against 0.50–0.56 at n = 4). Spikes 29–34's small effects were a ceiling of the platform, not a property of learning. Their *directions* stand; their magnitudes do not transfer.

**F3. The answer to "why does it generalize" sharpens to two parts.**
- **(a) The init kernel is a good but limited prior:** 0.79 balanced, and nets agree with it on 81–83% of held-out inputs.
- **(b) Feature learning moves the net from that prior toward the minimum-circuit (Occam) completion.** Nets agree with Occam on 91% of held-out inputs. Where they leave the kernel, Occam sides with them 80% of the time, and they are right 77% of the time.

Occam alone generalizes at least as well as training (+0.012). This is the opposite of Spike 34's n = 4 reading (45%), where Occam was too coarse to show it. **It is exploratory and needs a pre-registered replication:** Spike 36, fresh targets and seeds, plus a 5th input count (n = 5) and other target costs.

**F4. Revised conjecture C19′.** Gradient descent on threshold-like tasks generalizes because:
1. it starts from the NTK prior;
2. feature learning then performs an approximate **minimum-description-length search over circuits**, landing on or near the compiler's minimal completion.

This would unify Spikes 9–14 (training picks table-cheapest functions in 88–95% of runs on underspecified tasks) with Spikes 30–35. The Spike 9 result was the first hint of it, at full data.
