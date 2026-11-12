# Spike 25: Certified symmetry propagation at low label counts

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 19 arm 2 (the smoothness-matched null rejects every decoy, but at 10% labelled tic-tac-toe it accepts nothing)

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
