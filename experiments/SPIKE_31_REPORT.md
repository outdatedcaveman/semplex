# Spike 31: Why do graded activations have better priors? Spectral bias over Walsh degrees (C16)

**Date:** 2026-11-13 · **Status:** pre-registered (no run made) · **Follows:** Spike 30 F3 (the initial kernel is the generalization prior; graded activations have better kernels here, for an unexplained reason)

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
