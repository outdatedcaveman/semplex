# Spike 43: Kernel-smoothed target first, Occam later? (H-J)

**Date:** 2026-11-13 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 36 (C19′ replicated: on held-out inputs where trained nets depart from their NTK prediction, the minimum-circuit (Occam) completion sides with the net in 73–81% of cases).
**Source of the hypothesis:** Nichani, Damian & Lee, arXiv:2305.06986 (`charter/LITERATURE_REVIEW.md` §5, H-J). In their layer-wise analysis the first gradient step learns a feature ≈ K f\*, the target smoothed by the initial kernel.

## Question

C19′ says that feature learning moves nets from the kernel prior toward Occam. *When* does that happen? H-J predicts two phases:
1. The first steps change the function along the kernel-smoothed target K f\*.
2. Agreement with Occam, where it conflicts with K f\*, appears only later.

The alternative is that the departures toward Occam are present from the first steps. That would mean the Occam pull is not a later feature-learning phase.

## Design

- **Tasks:** Spike 36's n = 6 tasks: 300 tasks (150 targets × 2 care sets of 48 seen inputs). Its Occam completions (5-sample vote) are reused read-only from `experiments/results/spike36_raw/`.
- **Arm A (primary).** The exact Spike 36 training recipe: width 8, tanh, AdamW lr 0.03, wd 0.03, 3,000 steps, 10 seeds per task, training seed 3,720 (= Spike 36's). Function outputs z_t on all 64 inputs are recorded at t ∈ {0, 1, 2, 3, 5, 10, 30, 100, 300, 1000, 3000}.
  - **Sanity check:** the final outputs must match Spike 36's `nets_n6_tanh.json` on ≥ 99.9% of bits. If they do not, the run is a re-run with the recorded difference, not a replication.
- **Arm G (secondary, descriptive only).** Plain full-batch gradient descent, which is the setting of the theory. Same nets and seeds, lr = 2.0, no weight decay, same checkpoints and 3,000 steps. Adam's first step is a sign step, so it is only approximately a kernel step; arm G checks whether that matters.
- **Kernel-smoothed target:** k(x) = sign( Σ_{s seen} Θ(x, s)·(y_s − ½) ) on held-out x, with Θ the width-8 tanh NTK of Spike 36 (`spike36.ntk(6, "tanh")`). Up to scale, this is the function change of one infinitesimal gradient step from z = 0 under the logistic loss.
- **Measures**, on held-out inputs of nets that fit their care set at step 3,000 (fixed set):
  - A_K(t) = agreement of sign(z_t − z_0) with k.
  - S(t) = on held-out inputs where the Occam completion and k disagree, the fraction where sign(z_t − z_0) agrees with Occam.
  - Also reported: agreement of sign(z_t) with Occam and with the ridge NTK prediction (Spike 36's `kpred`), and balanced accuracy of sign(z_t).

## Hypotheses and kill criteria (arm A)

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H43.1 | The first update follows the kernel-smoothed target | A_K(1) ≥ 0.80 | A_K(1) < 0.65 |
| H43.2 | Early, where Occam and k conflict, the change sides with k | S(1) ≤ 0.40 | S(1) ≥ 0.55 |
| H43.3 | Occam agreement on those conflicts rises later | S(3000) − S(1) ≥ +0.15 | S(3000) − S(1) ≤ +0.05 |

Values in between are reported as *neither*. H-J holds if H43.1–H43.3 all hold. H-J is broken if H43.2 or H43.3 is broken. Exploratory, no criterion: the first checkpoint at which S(t) ≥ 0.5, and arm G's curves.

## Commands

```
python -m experiments.spike43 run A
python -m experiments.spike43 run G
python -m experiments.spike43 analyse
```

## Results

(To be filled after the runs.)
