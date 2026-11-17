# Spike 62: The sufficiency law (C31‴), prospective: learned geometry = smallest faithful, readout-sufficient set of irreducibles

**Date:** 2026-11-17 · **Status:** pre-registered (no run) · **Follows:** Spike 60 (P192, P193) and the theory in `charter/FOUNDATIONS.md` §11.4. The LP check (`experiments/theory/sufficiency_lp.py`, `results/theory_sufficiency_lp.json`) found C31‴ matches all four Spike 60 cases; that match was post hoc. **Conjecture:** C31‴.

## Conjecture

A trained recurrent network represents a group automaton by the **smallest set of irreducible representations that is**:
- **(i) faithful**: its matrix coefficients separate all group elements (closure);
- **(ii) readout-sufficient**: every output coset is linearly threshold-separable from the set's matrix coefficients (decided by linear programming).

Predictions are computed before training by enumerating all sets of irreducibles (`experiments/spike62.py`, `predict`).

## Automata (new readouts; letters and dynamics as in Spike 60; output = one-hot left coset gH)

| Name | Group | H (readout) | Cosets | Readout module (perm − 1) | **C31‴ prediction** | C31 (minimal faithful) |
|---|---|---|---|---|---|---|
| S4_6c | S₄ | ⟨(0 1 2 3)⟩ | 6 | χ₂ + std⊗sign | **std⊗sign** | std or std⊗sign |
| S4_8 | S₄ | ⟨(0 1 2)⟩ | 8 | sign + std + std⊗sign | **std⊗sign** | std or std⊗sign |
| S4_12b | S₄ | ⟨(0 1)(2 3)⟩ | 12 | sign + 2χ₂ + std + std⊗sign | **sign + std, or sign + std⊗sign** | std or std⊗sign |
| A5_10 | A₅ | ⟨(0 1 2), (0 1)(3 4)⟩ ≅ S₃ | 10 | χ₄ + χ₅ | **χ₄** | χ₃ or χ₃′ |
| A5_15 | A₅ | V₄ = ⟨(0 1)(2 3), (0 2)(1 3)⟩ | 15 | χ₄ + 2χ₅ | **χ₅** | χ₃ or χ₃′ |

**Training.** GRU exactly as Spike 60 (width 64, Adam lr 0.003 cosine to 0, 6,000 steps, length 30, batch 64). 5 seeds per automaton (seed 6,200 + 10·index + seed). Fit guard: ≥ 0.99 at length 100.

**Statistic.** As Spike 60: the Spearman correlation between the off-diagonal centroid cosine Gram and Re χ(g⁻¹h) for each irreducible. For a set of irreducibles, the kernel is the sum of their characters.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H62.1 | **Single-constituent predictions** (S4_6c, S4_8, A5_10, A5_15): the best single irreducible is the predicted one | ≥ 80% of fitted runs (pooled) | < 50% |
| H62.2 | **The two-part prediction** (S4_12b): the best predicted set (sign + std or sign + std⊗sign) scores above every single irreducible and above the full readout module | ≥ 80% of fitted runs | < 50% |
| H62.3 | **C31‴ beats C31′:** the predicted set scores above the readout module (perm − 1) | ≥ 80% of fitted runs, all five automata | < 50% |

Anything else is *neither*. **Guard:** an automaton counts only with ≥ 3 fitted seeds.

## What this cannot show

One architecture; two groups; sufficiency is tested on matrix-coefficient features, not on the network's own nonlinear readout.

## Commands

```
python -m experiments.spike62 predict
python -m experiments.spike62 run
python -m experiments.spike62 analyse
```

## Results

(Not run.)
