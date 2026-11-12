# Spike 18: Why do single units prefer symmetric functions? And CSP on standard benchmarks

**Date:** 2026-11-12 · **Status:** pre-registered (no run made) · **Follows:** Spike 17 F1, F2

## Arm A: mechanism of the unit-level Curie bias

**A1, weight-decay ablation (fresh seeds, the 128 elements of Spike 14, 40 seeds each, 3,000 / 10,000 steps).** Weight decay pulls every weight toward the origin, which is fixed by every symmetry. If that pull is what makes units symmetric, removing it should weaken the bias.

| Env | Optimizer | Weight decay |
|---|---|---|
| A8-wd0 / A8-wd0.03 / A8-wd0.1 | AdamW lr 0.03 | 0 / 0.03 / 0.1 |
| G8-wd0 / G8-wd0.003 | GD lr 0.3 | 0 / 0.003 |

The statistics are β (circuit level) and β_u (unit level), with the estimators of Spikes 14 and 17.

**A2, are trained weights exactly symmetric?** For each core unit with threshold function t and stabilizer H_t = {σ ∈ G_g : σt ∈ {t, ¬t}}, the *symmetry defect* is

D(θ) = mean over σ ∈ H_t of ‖σθ ∓ θ‖ / ‖θ‖,

with the sign − when σt = t and + when σt = ¬t. Here θ = (w, b) and σ acts by permuting and sign-flipping input weights. The null is the defect of isotropic Gaussian weight vectors realizing the same t, by rejection sampling. Defects are measured at steps 100, 300, 1,000 and 3,000 in A8-wd0.03 and A8-wd0.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H18.1 | Weight decay causes the unit-level bias | β_u(A8-wd0) − β_u(A8-wd0.1) ≥ +1.0 **and** β_u(G8-wd0) − β_u(G8-wd0.003) ≥ +1.0 | β_u ≤ −2 in both wd = 0 runs (the bias persists without weight decay) |
| H18.2 | Trained units are drawn into the symmetric subspace: final defect far below the null | median final defect ≤ 0.5 × median null defect, in A8-wd0.03 | ≥ 0.9 × null |
| H18.3 | The pull is active during training: defect decreases | median defect at step 3,000 < at step 100, in A8-wd0.03, by ≥ 30% | it increases |
| H18.4 | The pull exists without weight decay | H18.2's ratio ≤ 0.5 in A8-wd0 too | ≥ 0.9 |

## Arm B: certified symmetry propagation on standard benchmarks

Both benchmarks are regenerated exactly, so no download is needed and the generation is checked against the published counts.
- **Tic-tac-toe endgame** (UCI): all legal end-game boards with X moving first. Published: 958 instances, 626 positive ("X wins").
- **MONK's problems 1–3** (Thrun et al., 1991): all 432 attribute combinations, labelled by the three published rules. Random training splits are used, not the original fixed ones, and the original MONK-3 training noise is not added. Both deviations are stated here in advance.

**CSP as in Spike 17**, generalized to finite datasets:
- A candidate σ is a map on input tuples. A pair (x, σx) counts only if both are in the labelled set and x ≠ σx.
- σ is accepted iff it has at least 10 such pairs and all of them agree.
- Labels then propagate along orbits of the generated group. A conflicting orbit voids the method.

Candidates:
- **Tic-tac-toe:** the 7 non-identity board symmetries, plus the 36 cell transpositions and the X↔O swap as decoys.
- **MONK:** the 4 swaps of attributes with equal domains, and all value transpositions within each attribute (17).

**Model:** a one-hot MLP (64 tanh units, AdamW, 2,000 steps), 10 seeds per training fraction. Training fractions: 0.1, 0.2 and 0.3 for tic-tac-toe; 0.15 and 0.3 for MONK.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H18.5 | CSP improves test accuracy on tic-tac-toe | gain ≥ +0.03 at every training fraction | gain ≤ 0 at any |
| H18.6 | CSP improves MONK-1 and MONK-2 | gain ≥ +0.03 at both fractions for both | gain ≤ 0 for either at either fraction |
| H18.7 | CSP never hurts by more than 1 point (all datasets and fractions, MONK-3 included) | every mean gain ≥ −0.01 | any ≤ −0.02 |
| H18.8 | Decoys are rejected | the 36 cell transpositions and the X↔O swap are accepted in ≤ 5% of tic-tac-toe runs | > 20% |
