# Spike 31: Why do graded activations have better priors? Spectral bias over Walsh degrees (C16)

**Date:** 2026-11-13 · **Status:** complete (pre-registered in 5cb7ea6; results below) · **Follows:** Spike 30 F3 (the initial kernel is the generalization prior; graded activations have better kernels here, for an unexplained reason)

## Conjecture C16

On the hypercube {−1, +1}⁴, each activation's initial NTK depends only on Hamming distance, because the init is i.i.d. Gaussian and |x| is constant. Such a kernel is diagonalized by the 16 Walsh characters χ_S(x) = Π_{i∈S} x_i. All characters of the same degree |S| = k share one eigenvalue μ_k. Kernel regression's inductive bias is then exactly its **degree spectrum** (μ₀, …, μ₄).

C16 has two parts:
- **(a)** The atlas targets are threshold-like, so most of their non-constant energy is at degree 1.
- **(b)** A kernel generalizes on them in proportion to how much of its non-constant mass sits on degree 1. Graded activations put more there than saturating ones.

This is the "decays more gradually with Hamming distance" candidate of Spike 30 F3, stated exactly.

## Measures

- **Degree-1 share** of a kernel: F1 = 4μ₁ / Σ_{k≥1} C(4, k) μ_k. Here μ_k = χᵀKχ / 16 for any χ of degree k, averaged over the characters of that degree.
- **Target spectrum:** for each element g (as ±1), its Walsh energy by degree, averaged over the 128 elements, with each target's non-constant energy normalized to 1.
- **Kernel held-out accuracy:** reused unchanged from Spike 30 (`results/spike30.json`; ridge ε = 10⁻³·tr/12; same masks and targets).

## Arms

- **A (observational).** All 24 activation kernels: compute F1 and relate it to kernel and net held-out accuracy.
- **B (intervention).** Synthetic distance kernels K_r = Σ_S r^{|S|} χ_S χ_Sᵀ, with μ₀ = 1, for r ∈ {0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2}. Small r puts weight on low degrees; r = 1 is flat, the "memorizing" kernel. Also a **matched kernel**, whose μ_k for k ≥ 1 is the mean target energy per character at degree k. Every kernel uses Spike 30's kernel ridge on the same 1,280 tasks.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H31.1 | Sanity: activation NTKs are distance-only, so the Walsh characters diagonalize them | max over activations of the off-diagonal energy share of K in the Walsh basis ≤ 0.02 | > 0.1 |
| H31.2 | F1 ranks kernel held-out accuracy across the 24 activations | Spearman ρ ≥ 0.7 | ρ ≤ 0.3 |
| H31.3 | F1 ranks trained-net held-out accuracy (Spike 29) | ρ ≥ 0.6 | ρ ≤ 0.2 |
| H31.4 | Graded activations put more mass on degree 1 | mean F1 of untilted activations (λ ≤ 3) > mean F1 of tilted ones (λ ≥ 7) | < |
| H31.5 | Intervention: accuracy follows degree-1 weight | in arm B, accuracy decreases monotonically in r over r ≥ 0.3, with at most one inversion | accuracy is higher at r = 1.0 than at r = 0.3 |
| H31.6 | Matching the target spectrum gives the best prior | matched-kernel accuracy ≥ the best activation kernel's | < the best activation kernel's − 0.01 |

---

## Results

`results/spike31.json` (pre-registered analysis) and `results/spike31_exploratory.json` (balanced-accuracy re-analysis, post hoc).

**The premise of C16(a) is false.** The atlas targets' non-constant Walsh energy by degree, averaged over the 128 elements:

| Degree 1 | Degree 2 | Degree 3 | Degree 4 |
|---|---|---|---|
| 0.283 | **0.438** | 0.200 | 0.079 |

Most target energy is at degree 2, not degree 1.

**Activations, degree-1 share (F1) against accuracy.** Over the 24 activations, ρ(F1, kernel accuracy) = −0.46 and ρ(F1, net accuracy) = −0.38. The untilted activations have *less* degree-1 share than the tilted ones (difference −0.087). |x| has the lowest F1 (0.36) and the best nets.

**Synthetic kernels K_r** (μ_k = r^k):

| r | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.7 | 1.0 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|---|
| Accuracy (pre-registered) | 0.544 | 0.537 | 0.534 | 0.537 | 0.539 | 0.542 | 0.604* | 0.451 | 0.452 |
| Balanced accuracy (post hoc) | 0.536 | 0.527 | 0.522 | 0.523 | 0.518 | 0.520 | 0.500 | 0.486 | 0.488 |

\* r = 1 makes K the identity. Its held-out prediction is then 0 everywhere, so 0.604 is just the share of 0s among held-out targets (see the caveat below).

**Matched kernel** (spectrum equal to the targets'): accuracy 0.563 against 0.551 for the best activation kernel; balanced 0.557 against at most 0.541.

### Verdicts

| # | Verdict |
|---|---|
| H31.1 | **Held.** Maximum off-diagonal energy share in the Walsh basis is 0.00013: the NTKs are distance-only. |
| H31.2 | **Broken, opposite sign.** ρ = −0.46. |
| H31.3 | **Broken.** ρ = −0.38. |
| H31.4 | **Broken.** Graded activations have *less* degree-1 share. |
| H31.5 | **Broken as stated**, but for an artifact: the r = 1 "memorizing" kernel scores 0.604 because it always predicts 0. On balanced accuracy (post hoc), accuracy falls with r from 0.536 to 0.488, with two small inversions. |
| H31.6 | **Held.** The matched kernel beats every activation kernel (+0.012 accuracy, +0.016 balanced). |

## Findings

**F1. C16 is refuted.** "Graded activations are better because they weight degree 1" is wrong twice over. The targets are mostly degree-2. Among activations, more degree-1 weight goes with *worse* priors.

**F2. Spectrum matching is what works.** A kernel whose degree spectrum equals the targets' beats all 24 activation kernels. This is the *spectral bias / task–model alignment* account of kernel generalization (Bordelon, Canatar & Pehlevan 2020; Canatar et al. 2021, *Nat. Commun.*). It is **prior art**, not new: our atlas confirms it exactly. Over the activations, cosine alignment to the target spectrum is only weakly predictive (ρ = 0.28 with kernel balanced accuracy, 0.37 with net), so degree-level spectra do not explain the activation ranking. The rest must lie in what the degree spectrum ignores, chiefly μ₀, the constant mode that sets how strongly predictions lean toward the seen majority.

**F3. Caveat found in this spike, affecting Spikes 29–30: label imbalance.** Only 39.6% of target outputs are 1, so predicting 0 everywhere scores 0.604, *above every net* (0.535–0.580). On balanced accuracy (0.5 = chance):
- saturating-activation kernels are at chance (0.497–0.513);
- graded kernels reach 0.53–0.54;
- nets reach 0.519–0.561 (mean 0.546).

Generalization on this atlas is therefore real but weak. Re-run on the balanced measure (`spike31_exploratory.json`), every Spike 30 conclusion survives:
- the kernel ranks the nets (ρ = 0.79);
- the tilt's apparent cost is inherited from the kernel (residual ρ = 0.09);
- learning improves on the kernel in **24 of 24** activations, by +2.6 balanced points, and *more* for tilted activations (ρ = +0.55).
