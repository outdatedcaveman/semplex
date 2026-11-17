# Spike 66: Formally pre-registered test of the predictive-state law; extension pairs, a p-primary readout, the S₄ anomaly

**Date:** 2026-11-17 · **Status:** pre-registered (no run) · **Follows:** Spikes 60 and 62 (P196: the exact predictive-state kernel matched every fitted case but one, without formal pre-registration). This spike also covers two of `charter/FOUNDATIONS.md` §12's threads: extension classes (§12.4) and p-primary decomposition (§12.5).

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

(Not run.)
