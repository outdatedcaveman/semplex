# Spike 62: The sufficiency law (C31‴), prospective: learned geometry = smallest faithful, readout-sufficient set of irreducibles

**Date:** 2026-11-17 · **Status:** complete (pre-registered in d8a9728; results below) · **Follows:** Spike 60 (P192, P193) and the theory in `charter/FOUNDATIONS.md` §11.4. The LP check (`experiments/theory/sufficiency_lp.py`, `results/theory_sufficiency_lp.json`) found C31‴ matches all four Spike 60 cases; that match was post hoc. **Conjecture:** C31‴.

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

`experiments/results/spike62.json`; per-run outputs in `spike62_raw/`. Fitted runs: S4_6c 5, S4_8 5, S4_12b 5, A5_10 2 (3 runs reached 0.91–0.93), A5_15 0 (all 0.936–0.939). A5_10 counts for H62.1 only in pooled form; A5_15 is excluded by the guard.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H62.1 | predicted single irreducible best in **0/12** fitted runs (S4_6c: χ₂ 5/5; S4_8: sign 5/5; A5_10: χ₄ 2/2, but A5_10 has < 3 fitted seeds and is excluded) | ≥ 80% held, < 50% broken | **BROKEN** |
| H62.2 | S4_12b predicted set above all singles and the readout module in 0/5 | ≥ 80% | **BROKEN** |
| H62.3 | predicted set above the readout module in 1/15 | ≥ 80% | **BROKEN** |

**The sufficiency law C31‴ is refused.** In S₄, networks do not compress to a smallest faithful, readout-sufficient set. They keep unfaithful constituents (χ₂, sign) as their dominant geometry. For A5_10 the observed χ₄ coincides with the prediction, but too few seeds fitted for a verdict.

**What the data do follow: the predictive-state law.** The exact finite-horizon predictive kernel (`experiments/theory/predictive_kernel.py`; no fitting) predicts:
- S4_6c → χ₂, S4_8 → sign: computed after the first runs of these two automata had been seen;
- S4_12b → χ₂, A5_10 → χ₄, A5_15 → χ₅: computed and shown before any of their runs finished, but not committed as a formal pre-registration.

Observed best irreducibles:
- S4_6c: χ₂ 5/5; S4_8: sign 5/5; S4_12b: χ₂ 4/5 (one run sign);
- A5_10: χ₄ 5/5, including the 3 unfitted runs;
- A5_15 (unfitted): χ₅ 4/5.

With Spike 60, the predictive-state law matches every fitted case except Spike 60's S4_6, where networks used the standard representation and the predictive kernel prefers χ₂ (0.65 against 0.41).

**Conclusion.** The learned geometry of a group concept is the geometry of the network's **predictive state**: the Gram matrix of expected future outputs, i.e. the readout's permutation character weighted by how fast each constituent decorrelates under the random walk. There is one unexplained anomaly (S4_6). The compression refinement C31‴ is refuted.
