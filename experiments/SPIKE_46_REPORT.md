# Spike 46: The exact cost–error frontier. Do nets under label noise follow a simpler circuit plus exceptions?

**Date:** 2026-11-14 · **Status:** complete (pre-registered in 147c135; results below) · **Follows:** Spike 45 (the Occam pull holds on clean classes, drops to 0.58 with 5 flipped labels, and fails on real data). **Gap:** A8. **Direction:** R3 in `charter/PRIOR_ART.md`.

**Prior art this is built on.** Harel et al. (arXiv:2410.19092) prove that a minimum-size threshold net fitted to noisy labels can be built as *the teacher circuit plus a part that memorizes the flipped labels*, and that it overfits only mildly. Manoj & Srebro (2302.07263) show the same for minimum description length. Neither compares gradient-trained nets with the exact frontier.

## Idea

For a task with noisy seen labels, the compiler gives the exact **frontier**: for each circuit cost k, the least number e(k) of seen labels a circuit of that cost must misfit. The exact-fit Occam circuit is the cheapest point with e = 0. Call the frontier point one cost level below it the **simpler circuit**: it ignores some labels as exceptions.

**Conjecture C20′.** A net trained to fit noisy labels behaves on held-out inputs like the simpler circuit (the rule), while memorizing the exceptions locally. So as noise grows, the net's held-out outputs agree less with the exact-fit circuit and more with the simpler one.

## Design

- **Synthetic dose arm.** 60 targets from Spike 36's generator (random two-unit step nets, certified not threshold, 25–75% ones), seed 4,600; n = 6; one care set of 48 seen inputs per target. For each target, a fixed random order of 8 seen inputs; dose d ∈ {0, 2, 5, 8} flips the first d of them. Four cells of 60 tasks sharing targets and care sets. Truth on held-out inputs is the clean target.
- **Real arm.** Spike 45's four real datasets, tasks and trained nets, reused read-only (40 splits each).
- **Nets (synthetic).** `spike36.train` unchanged: two-layer tanh, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps, 10 seeds per task, seed 4,610 + cell index. Only nets that fit every seen label, flipped ones included, are analysed.
- **Frontier.** Costs 1, 3, 4, 5, 6 (hidden widths 0, 2, 3, 4, 5; weights |w| ≤ 4). For each cost in order, `netsolve.solve(..., min_errors=True)` gives e(k), with a flag for proved optimality, until e(k) = 0 (cost k\*).
- **Completions.** For each frontier point, 3 nets sampled with `max_errors = e(k)` and random objectives (3 s each); the completion is their majority vote. `exact` is the point k\*. `simpler` is the frontier point at the cost level just below k\*; if k\* = 1 it is `exact` itself (the fraction of such tasks is reported).
- **Secondary predictor, `mdl`.** The frontier point minimizing a two-part code length in bits: circuit bits = 7·log₂9 per first-layer unit plus (h + 1)·log₂9 for the output unit over h hidden units (a single unit costs 7·log₂9); exception bits = log₂C(m, e) + log₂(m + 1) for e exceptions among m seen inputs.
- **Kernel.** `spike36.ntk(6, "tanh")`, ridge on the seen (noisy) labels.
- **Measures**, on held-out inputs, fitted nets only: agreement of the net with each predictor; `sides(P)` = among held-out inputs where the net differs from the kernel, the fraction where predictor P equals the net; balanced accuracy against the clean truth (synthetic) or the held-out labels (real).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H46.1 | Dose–response: the exact-fit Occam pull falls with noise | sides(exact) at d = 0 minus at d = 8 ≥ 0.10 | that difference ≤ 0.02 |
| H46.2 | Crossing: with noise, nets agree more with the simpler circuit than with the exact-fit one, and the reverse without noise | agree(simpler) − agree(exact) ≤ −0.02 at d = 0 **and** ≥ +0.02 at d = 8 | the difference at d = 8 is ≤ 0 |
| H46.3 | Real data: the simpler circuit predicts the net better than the kernel does | agree(simpler) − agree(kernel) > 0 in ≥ 3 of 4 datasets | ≤ 0 in ≥ 3 of 4 |
| H46.4 | The simpler circuit denoises | bal(simpler) − bal(exact) ≥ +0.02 at d = 5 and d = 8 | ≤ 0 at both |

Anything else is *neither*. C20′ is supported if H46.2 holds; it is refuted if H46.2 is broken.

**Guards.** A cell gives no verdict if fewer than 90% of its nets fit, if fewer than 90% of its frontier values are proved optimal, or if `simpler` equals `exact` in more than half of its tasks (then the comparison is empty; this is expected for Breast Cancer, where every task has cost 1).

**Reported without criteria:** the `mdl` predictor; for each cell, the distribution of the frontier point that best matches each net ("where nets land"); the frontier itself.

## Commands

```
python -m experiments.spike46 tasks
python -m experiments.spike46 frontier CELL     # d0 d2 d5 d8 breast_cancer wine digits diabetes
python -m experiments.spike46 nets CELL         # synthetic cells only
python -m experiments.spike46 analyse
```

## Results

`experiments/results/spike46.json`; raw outputs in `spike46_raw/`. Every task has an exact-fit point; 98–100% of frontier values are proved optimal. Net fit 97–100%. Breast Cancer gives no verdict, as expected (every task has cost 1, so `simpler` = `exact`).

| Cell | sides(exact) | agree exact | agree simpler | agree mdl | agree kernel | bal. net | bal. exact | bal. simpler | bal. mdl | bal. kernel | mean exact cost | guard |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| d0 | 0.832 | 0.887 | 0.883 | 0.883 | 0.792 | 0.886 | 0.887 | 0.843 | 0.843 | 0.750 | 2.87 | yes |
| d2 | 0.655 | 0.811 | 0.800 | 0.824 | 0.785 | 0.788 | 0.812 | 0.856 | 0.829 | 0.726 | 3.63 | yes |
| d5 | 0.569 | 0.743 | 0.759 | 0.772 | 0.744 | 0.728 | 0.718 | 0.760 | 0.775 | 0.710 | 3.92 | yes |
| d8 | 0.567 | 0.739 | 0.745 | 0.745 | 0.724 | 0.701 | 0.704 | 0.718 | 0.766 | 0.663 | 4.10 | yes |
| breast_cancer | 0.291 | 0.742 | 0.742 | 0.742 | 0.844 | 0.744 | 0.653 | 0.653 | 0.653 | 0.674 | 1.00 | no |
| wine | 0.741 | 0.927 | 0.943 | 0.943 | 0.891 | 0.814 | 0.776 | 0.799 | 0.799 | 0.887 | 2.05 | yes |
| digits | 0.557 | 0.738 | 0.747 | 0.799 | 0.767 | 0.687 | 0.655 | 0.652 | 0.708 | 0.712 | 3.90 | yes |
| diabetes | 0.480 | 0.746 | 0.787 | 0.798 | 0.798 | 0.707 | 0.660 | 0.685 | 0.767 | 0.750 | 3.83 | yes |

### Verdicts

- **H46.1: held.** The exact-fit Occam pull falls with noise: 0.83 with no flips, 0.66 with 2, 0.57 with 5, 0.57 with 8 (a drop of 0.27 from 0 to 8). Most of the drop happens by 2 flipped labels out of 48.
- **H46.2: neither.** The crossing has the predicted sign but is far too small: agree(simpler) − agree(exact) = −0.004 at d = 0 and +0.006 at d = 8, against bars of ∓0.02.
- **H46.3: neither.** The simpler circuit beats the kernel on Wine (+0.05) and loses on Digits (−0.02) and Diabetes (−0.01).
- **H46.4: neither.** The simpler circuit is more accurate than the exact-fit one by +0.042 at d = 5 and +0.014 at d = 8 (the bar was +0.02 at both).
- **C20′: not supported.** "One cost level simpler, plus exceptions" does not describe what noisy-label nets do on held-out inputs any better than the exact-fit circuit does.

### Reading

1. **Noise does not move the net to another point on the frontier. It makes the net less like any circuit.** The net's agreement with its best circuit predictor falls from 0.89 (no noise) to 0.75 (8 flips), while its agreement with the kernel stays at 0.72–0.79. Under noise the net sits about as far from the circuits as from the kernel.
2. **Two flipped labels in 48 are enough** to take the pull from 0.83 to 0.66. The exact-fit circuit's cost rises from 2.9 to 3.6 units to absorb them.
3. **Exploratory (no criterion was set for `mdl`).** The two-part-code circuit is the best or joint-best predictor of the net in 5 of the 7 cells with a verdict, and it generalizes better than the trained net under noise: 0.775 vs 0.728 at d = 5, 0.766 vs 0.701 at d = 8, 0.767 vs 0.707 on Diabetes, 0.708 vs 0.687 on Digits. On real data it beats the kernel on Diabetes only. This says the compiler can *denoise better than training does* here; it does not say nets follow it.

**Limit of the landing statistic.** "Where nets land" picks the best-matching frontier point with ties going to the cheaper point, so it over-counts cheaper points (62% even with no noise). It is reported in the JSON and should not be read as evidence.

**Next.** The pull toward the minimum circuit is a clean-data phenomenon that label noise removes quickly. Two open routes: (a) nets that are *not* forced to fit every label (early stopping, stronger weight decay), where prior work predicts a return to the clean rule; (b) leave noise and pursue the canonical-quotient line (gap A9), which asks what the hidden layer represents and does not depend on exact fitting.
