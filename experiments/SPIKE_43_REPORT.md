# Spike 43: Kernel-smoothed target first, Occam later? (H-J)

**Date:** 2026-11-13 · **Status:** complete (pre-registered in e244824; results below) · **Follows:** Spike 36 (C19′ replicated: on held-out inputs where trained nets depart from their NTK prediction, the minimum-circuit (Occam) completion sides with the net in 73–81% of cases).
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

`experiments/results/spike43.json`; raw checkpoints in `spike43_raw/`.

**Sanity check passed.** Arm A's final outputs equal Spike 36's `nets_n6_tanh.json` on 100% of bits, so this is Spike 36's run with checkpoints. Fit: 99.97% (arm A) and 100% (arm G). 9,085 held-out (net, input) points have Occam ≠ k.

| t | A_K (A) | S (A) | agree Occam, sign z (A) | agree ridge NTK (A) | bal. acc. (A) | A_K (G) | S (G) |
|---|---|---|---|---|---|---|---|
| 1 | 0.767 | 0.395 | 0.544 | 0.542 | 0.543 | 0.783 | 0.328 |
| 3 | 0.775 | 0.393 | 0.627 | 0.625 | 0.626 | 0.830 | 0.363 |
| 10 | 0.807 | 0.395 | 0.785 | 0.776 | 0.777 | 0.854 | 0.449 |
| 30 | 0.854 | 0.465 | 0.855 | 0.830 | 0.839 | 0.851 | 0.543 |
| 100 | 0.841 | 0.623 | 0.893 | 0.820 | 0.873 | 0.839 | 0.634 |
| 300 | 0.829 | 0.681 | 0.901 | 0.809 | 0.881 | 0.832 | 0.668 |
| 3000 | 0.818 | 0.721 | 0.903 | 0.799 | 0.882 | 0.827 | 0.699 |

### Verdicts

- **H43.1: neither.** A_K(1) = 0.767, between the kill line 0.65 and the bar 0.80. The first Adam step agrees with the kernel-smoothed target on 77% of held-out inputs; plain GD gives 78%. Adam's sign step is therefore not the reason it falls short of 0.80. A_K peaks at 0.85 around step 30, then declines.
- **H43.2: held.** S(1) = 0.395. Where the Occam completion and the kernel-smoothed target disagree, the early change sides with the kernel 60% of the time. S stays at 0.39–0.40 through step 10.
- **H43.3: held.** S(3000) − S(1) = +0.326. S first reaches 0.5 between step 30 and step 100 and ends at 0.72.
- **H-J overall: neither.** It needed all three to hold. Its two-phase core held (H43.2 and H43.3), and arm G shows the same shape: S goes 0.33 → 0.70 and crosses 0.5 by step 30.

### Reading

The order predicted from Nichani et al. holds in our atlas. Training first moves along the kernel-smoothed target; on the inputs where that target and the minimum circuit disagree, the net turns toward the circuit only after about 10–30 steps. Held-out balanced accuracy is 0.78 at step 10, when the change is kernel-like, and rises to 0.88 as S rises. This puts a time on C19′: the move toward Occam is a *later* phase, not present from the first step.
