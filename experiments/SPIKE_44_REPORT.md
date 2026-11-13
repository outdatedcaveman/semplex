# Spike 44: Does depth raise Occam agreement? (H-K)

**Date:** 2026-11-13 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 36 (C19′, two-layer nets).
**Source of the hypothesis:** Nichani, Damian & Lee, arXiv:2305.06986. Three-layer nets learn nonlinear features that two-layer nets cannot learn efficiently. In our setting, the Occam completion is a two-hidden-unit threshold circuit, a composition of features.

## Question

At matched parameter count, do three-layer nets side with the minimum-circuit completion more often than two-layer nets, and generalize better?

## Design

- **Tasks:** Spike 36's n = 5 and n = 6 tasks (300 each) and its Occam completions, reused read-only.
- **L2 (baseline):** Spike 36's two-layer width-8 tanh nets. Their recorded outputs `nets_n{5,6}_tanh.json` are reused, not retrained. n = 6: 65 parameters.
- **L3 (new):** three-layer tanh nets with hidden widths [5, 5] (n = 6: 71 parameters; n = 5: 65). Same recipe as L2: AdamW lr 0.03, wd 0.03, 3,000 steps, 10 seeds per task, logistic loss on the care set.
  - Initialization: weights and hidden biases N(0, 0.5²); output weights N(0, 0.5²); output bias 0.
  - Training seed 4,400 + n.
- **Kernels:** each architecture's own init NTK, as the empirical mean of J Jᵀ over 4,000 random initializations (closed form per net). The L2 kernel computed this way is compared against Spike 36's analytic kernel as a check.
- **Measures**, on held-out inputs of fitted nets, as in Spike 36's `compare`:
  - agreement with the Occam completion;
  - on held-out inputs where the net departs from its own NTK ridge prediction, the fraction where Occam sides with the net;
  - balanced accuracy.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H44.1 | Depth raises agreement with Occam | agree_occam(L3) − agree_occam(L2) ≥ +0.02 at both n | the difference is ≤ 0 at either n |
| H44.2 | Departures from the kernel go toward Occam more often with depth | sides(L3) − sides(L2) ≥ +0.03 at both n | the difference is < 0 at both n |
| H44.3 | Depth does not cost held-out accuracy | bal(L3) − bal(L2) ≥ 0 at both n | bal(L3) − bal(L2) ≤ −0.01 at both n |

Other values are *neither*. H-K holds if H44.1 and H44.2 hold, and is broken if H44.1 is broken.

**Fit guard:** if fewer than 95% of L3 nets fit their care set at some n, that n's verdicts are reported as *neither (fit)*.

## Commands

```
python -m experiments.spike44 run 5
python -m experiments.spike44 run 6
python -m experiments.spike44 analyse
```

## Results

(To be filled after the runs.)
