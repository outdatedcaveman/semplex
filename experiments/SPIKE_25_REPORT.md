# Spike 25: Certified symmetry propagation at low label counts

**Date:** 2026-11-12 · **Status:** complete (pre-registered in 5f8640c; results below) · **Follows:** Spike 19 arm 2 (the smoothness-matched null rejects every decoy, but at 10% labelled tic-tac-toe it accepts nothing)

## Why it failed at 10%

A candidate σ is tested on pairs (x, σx) with *both* labels known. At a labelled fraction f, there are about f²·N such pairs: ≈ 10 on tic-tac-toe at 10%. With a smoothness-matched null p₀(d) ≈ 0.6–0.7 at small distances, ten agreeing pairs give p ≈ 10⁻², far above the Bonferroni threshold 0.001/44. The test is starved of pairs, not wrong.

## Two less strict variants (everything else as Spike 19 arm 2: same datasets, splits, seeds, model, candidates)

- **V1, FDR.** Spike 19's statistic (all both-labelled pairs agree; p = Π p₀(dᵢ)), accepted by Benjamini–Hochberg at q = 0.05 over the candidates instead of Bonferroni at 0.001.
- **V2, pseudo-label evidence.** First train the plain model on the labelled points (Spike 19's baseline). Give every point an *observed value*: its label if labelled, otherwise the plain model's prediction. Test σ on all pairs (x, σx) in which at least one point is labelled, about 2f·N pairs (≈ 190 at 10%). Disagreements are allowed: the p-value is the upper tail of the number of agreeing pairs under independent Bernoulli(p₀(dᵢ)) draws (exact Poisson-binomial). The null p₀(d) is the agreement rate among random pairs at Hamming distance d with at least one labelled point, using the same observed values, so the plain model's own smoothness is in the null. Accept at Bonferroni 0.001/m. **Only true labels are propagated**, through the orbits of the accepted candidates, with Spike 19's conflict check.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H25.1 | V2 finds the board symmetries at 10% | a board symmetry is accepted in ≥ 8/10 tic-tac-toe runs at 0.1 | ≤ 5/10 |
| H25.2 | Both variants stay safe | a decoy is accepted in ≤ 1/10 runs at every tic-tac-toe fraction, for V1 and for V2 | > 3/10 at any fraction, for either |
| H25.3 | V2 helps at 10% | tic-tac-toe gain at 0.1 ≥ +0.03 | ≤ 0 |
| H25.4 | V2 does no harm anywhere | every mean gain (tic-tac-toe 0.1/0.2/0.3; MONK-1/2/3 at 0.15/0.3) ≥ −0.01 | any ≤ −0.02 |

---

## Results

Same splits as Spikes 18 and 19, 10 runs per cell. Results in `results/spike25.json`. A "decoy" is a cell transposition or the X↔O swap; a "sym" is one of the 7 board symmetries. MONK candidates are attribute and value swaps, counted in neither class.

| Dataset @ fraction | Plain | V1 (FDR) gain | V1 decoy / sym runs, voided | V2 (pseudo-label) gain | V2 decoy / sym runs, voided |
|---|---|---|---|---|---|
| tic-tac-toe @ 0.1 | 0.912 | **+0.036** | 0 / 7, 0 | +0.010 | 10 / 10, 8 |
| tic-tac-toe @ 0.2 | 0.976 | +0.007 | 5 / 10, 5 | 0.000 | 10 / 10, 10 |
| tic-tac-toe @ 0.3 | 0.980 | 0.000 | 10 / 10, 10 | 0.000 | 10 / 10, 10 |
| MONK-1 @ 0.15 / 0.3 | 0.922 / 1.000 | +0.005 / 0 | | **+0.053** / 0 | |
| MONK-2 @ 0.15 / 0.3 | 0.768 / 0.998 | **+0.121** / +0.002 | | **+0.119** / +0.002 | |
| MONK-3 @ 0.15 / 0.3 | 0.983 / 0.998 | +0.000 / 0 | | 0 / 0 | |

### Verdicts

| # | Verdict |
|---|---|
| H25.1 | **Held.** V2 accepts a board symmetry in 10/10 runs at 0.1. |
| H25.2 | **Broken.** V2 accepts a decoy in 10/10 runs at every tic-tac-toe fraction. V1 does so in 5/10 at 0.2 and 10/10 at 0.3. |
| H25.3 | **Neither held nor broken.** V2's gain at 0.1 is +0.010: above 0, below +0.03. |
| H25.4 | **Held.** No mean gain is below 0 for V2 (all ≥ 0). |

## Findings

**F1. Matching the null on distance is not enough once the test has enough power.** Spike 19's null rejected every decoy only because Bonferroni at 0.001 left it with little power. With FDR at 0.05 (V1), or with the many extra pairs that pseudo-labels supply (V2), decoys pass again. A cell transposition moves an input by Hamming distance 2 yet preserves far more of the label than a random distance-2 move: it keeps the multiset of marks, and tic-tac-toe outcomes depend on the marks' arrangement only through lines. Label smoothness is *anisotropic*, and a null matched on distance alone cannot see that. A calibrated test needs a null matched on the transformation's own structure, e.g. random permutations of the same cycle type.

**F2. Pseudo-labels inherit the model's own invariances.** V2 measures agreement between labels and the plain model's predictions. A trained MLP is itself nearly invariant under many decoys, so its predictions "confirm" them. The conflict check then voided most runs, which is why there was no harm (H25.4) and also no gain.

**F3. The useful result is a narrow one.** At 10% labelled tic-tac-toe, the FDR variant gained +3.6 points with no decoy and a true symmetry in 7/10 runs. On MONK-2 at 15%, both variants gained about +12 points through value and attribute swaps. Safety still rests on the conflict check, not on the certificate. CSP remains a useful heuristic with a fallback, not yet a certified method.
