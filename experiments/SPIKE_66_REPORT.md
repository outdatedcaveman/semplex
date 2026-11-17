# Spike 66: Formally pre-registered test of the predictive-state law; extension pairs, a p-primary readout, the S₄ anomaly

**Date:** 2026-11-17 · **Status:** complete (pre-registered in 52a41f6; results below) · **Follows:** Spikes 60 and 62 (P196: the exact predictive-state kernel matched every fitted case but one, without formal pre-registration). This spike also covers two of `charter/FOUNDATIONS.md` §12's threads: extension classes (§12.4) and p-primary decomposition (§12.5).

## Law under test

The learned macrostate geometry (cosine Gram of macrostate centroids) equals the geometry of the **predictive state**, K = Σ_{t=1..30} E_w⟨o(gw), o(hw)⟩, centred and computed exactly from the automaton (`experiments/spike66.py`, `predictive_kernel`). The predictions are fixed by the code, committed before any run.

**Baseline.** The one-step output kernel ⟨o(g), o(h)⟩ (current output similarity only).

## Automata

Letters are the generators plus an identity ("no-op") letter.

| Name | Group | Output | Minimal states | Thread |
|---|---|---|---|---|
| Z4 / V4 | ℤ/4 / ℤ/2×ℤ/2 | [g = e] | 4 / 4 | same factors, non-split vs split |
| Z9 / Z3xZ3 | ℤ/9 / ℤ/3×ℤ/3 | [g = e] | 9 / 9 | same factors, non-split vs split |
| Q8 / D4 | quaternion / dihedral (order 8) | [g = e] | 8 / 8 | same order and factors, different extensions |
| Z6_mod3 | ℤ/6 | [c ≡ 0 mod 3] | **3** | p-primary: the 2-part is unobservable |
| S4_6 | S₄ | one-hot of the image of {0, 1} (6 pairs) | 24 | the Spike 60 anomaly, repeated |

## Training

GRU recipe of Spike 60 (width 64, Adam lr 0.003 cosine, 6,000 steps, length 30, batch 64). 3 seeds per automaton (6,600 + 10·index + seed). Fit guard: ≥ 0.99 at length 100.

## Hypotheses and kill criteria

H66.1 and H66.2 pool the fitted runs of every automaton except S4_6, with more than 2 macrostates.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H66.1 | **Predictive-state law:** Spearman(learned Gram, predictive kernel) ≥ 0.6 | in ≥ 80% of runs | < 50% |
| H66.2 | It beats the one-step output kernel | ρ_predictive > ρ_onestep in ≥ 80% | < 50% |
| H66.3 | **Closure discards the unobservable p-part** (Z6_mod3): c mod 2 is not decodable | median probe accuracy for c mod 2 ≤ 0.60 (chance 0.5) | ≥ 0.90 |

Anything else is *neither*. **Reported without criteria:** S4_6's best irreducible, i.e. whether the anomaly (standard rather than the predicted χ₂) repeats.

## What this cannot show

- Small groups; one architecture.
- Spearman correlation on Gram entries, not a full kernel fit.

## Commands

```
python -m experiments.spike66 predict
python -m experiments.spike66 run
python -m experiments.spike66 analyse
```

## Results

`experiments/results/spike66.json`. 23 of 24 runs fit (one Z9 run reached 0.886).

| Automaton | Seed | Fit | ρ predictive | ρ one-step | Macrostates | Probe (macro) | Probe c mod 2 | Best irreducible |
|---|---|---|---|---|---|---|---|---|
| Z4 | 6600 | 1.000 | -0.12 | 0.49 | 4 | 1.00 |  |  |
| Z4 | 6601 | 1.000 | 0.12 | 0.49 | 4 | 1.00 |  |  |
| Z4 | 6602 | 1.000 | -0.12 | 0.49 | 4 | 1.00 |  |  |
| V4 | 6610 | 1.000 | 0.44 | 0.49 | 4 | 1.00 |  |  |
| V4 | 6611 | 1.000 | 0.44 | 0.49 | 4 | 1.00 |  |  |
| V4 | 6612 | 1.000 | 0.29 | 0.49 | 4 | 1.00 |  |  |
| Z9 | 6620 | 0.886 | -0.22 | 0.30 | 9 | 0.97 |  |  |
| Z9 | 6621 | 1.000 | -0.05 | 0.38 | 9 | 1.00 |  |  |
| Z9 | 6622 | 1.000 | 0.02 | 0.29 | 9 | 1.00 |  |  |
| Z3xZ3 | 6630 | 1.000 | 0.18 | 0.23 | 9 | 1.00 |  |  |
| Z3xZ3 | 6631 | 1.000 | 0.15 | 0.21 | 9 | 1.00 |  |  |
| Z3xZ3 | 6632 | 1.000 | 0.23 | 0.28 | 9 | 1.00 |  |  |
| Q8 | 6640 | 1.000 | -0.01 | 0.09 | 8 | 1.00 |  |  |
| Q8 | 6641 | 1.000 | -0.14 | 0.02 | 8 | 1.00 |  |  |
| Q8 | 6642 | 1.000 | -0.04 | 0.25 | 8 | 1.00 |  |  |
| D4 | 6650 | 1.000 | 0.19 | 0.25 | 8 | 1.00 |  |  |
| D4 | 6651 | 1.000 | 0.13 | 0.16 | 8 | 1.00 |  |  |
| D4 | 6652 | 1.000 | 0.14 | 0.23 | 8 | 1.00 |  |  |
| Z6_mod3 | 6660 | 1.000 | -0.50 | 0.87 | 3 | 1.00 | 0.5592 |  |
| Z6_mod3 | 6661 | 1.000 | -0.50 | 0.87 | 3 | 1.00 | 0.5354 |  |
| Z6_mod3 | 6662 | 1.000 | -0.50 | 0.87 | 3 | 1.00 | 0.5342 |  |
| S4_6 | 6670 | 1.000 | 0.47 | 0.58 | 24 | 1.00 |  | std |
| S4_6 | 6671 | 1.000 | 0.50 | 0.58 | 24 | 1.00 |  | std |
| S4_6 | 6672 | 1.000 | 0.43 | 0.58 | 24 | 1.00 |  | std |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H66.1 | ρ_predictive ≥ 0.6 in 0% of pooled fitted runs | ≥ 80% held, < 50% broken | **BROKEN** |
| H66.2 | ρ_predictive > ρ_onestep in 0% | ≥ 80% held, < 50% broken | **BROKEN** |
| H66.3 | Z6_mod3 median probe for c mod 2 = 0.54 (chance 0.50) | ≤ 0.60 held | **HELD** |

Reported without criteria: the S4_6 anomaly repeats, with best irreducible std in 3/3 runs (the predictive kernel prefers χ₂).

**Design flaw, recorded.** For the identity readout [g = e] used for Z4, V4, Z9, Z3xZ3, Q8 and D4, two distinct states never give the same output under the same future word. So the predictive kernel is **exactly diagonal**: it predicts a regular simplex, with all states equidistant, and its off-diagonal ranking is noise from the finite horizon. This was computable before registration and was not checked. The test is still a valid refutation of the law as stated, since the law makes a definite prediction (equidistance) and the networks violate it: they build structured geometries (the one-step kernel, which singles out the identity, fits better). But it tests a degenerate case of the law rather than a typical one. Z6_mod3 has only 3 macrostates, so its Spearman correlations over 3 pairs are not informative.

**Reading:**
- **Closure discards what cannot be observed.** For ℤ/6 read out mod 3, the networks' hidden states carry no linearly decodable trace of the unobservable 2-part (0.53–0.56, chance 0.5). The macrostate is the 3-part only: the p-primary part the readout sees (`charter/FOUNDATIONS.md` §12.5). This is the Myhill–Nerode quotient made literal in arithmetic.
- **The predictive-state law is refuted as a universal law.** It predicted the best character for coset readouts of moderate size (Spikes 60 and 62, 11 of 12 automata). It fails for regular, identity-only readouts, where it predicts equidistance and networks build compact geometry instead (circles for cyclic groups, as already seen in Spikes 57–58). It also fails for S₄'s 6-point readout, now replicated.
- **Candidate synthesis, post hoc (C37, two regimes).**
  - Where the predictive state is low-rank and structured, networks realise its geometry.
  - Where it is degenerate (identity-like, full rank), the predictive structure does not constrain the geometry. The architecture's inductive bias decides it: compact, low-frequency, faithful (circles).
