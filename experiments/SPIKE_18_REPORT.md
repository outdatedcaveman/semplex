# Spike 18: Why do single units prefer symmetric functions? And CSP on standard benchmarks

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `5787cb9` before any run. One bookkeeping fix after the run: defect records lacked their task element, which the null needs. Training is deterministic, so A8-wd0 and A8-wd0.03 were rerun with identical outcomes; nothing else changed. · **Follows:** Spike 17 F1, F2

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

## Results (`results/spike18.json`, raw data in `results/spike18_raw/`)

### Arm A

| Env | Fit | β (circuits) | β_u (units) |
|---|---|---|---|
| A8-wd0 | 99.7% | −2.40 | **−2.73** |
| A8-wd0.03 | 99.9% | −2.50 | −2.95 |
| A8-wd0.1 | 100% | −3.17 | −3.27 |
| G8-wd0 | 100% | −2.24 | **−2.81** |
| G8-wd0.003 | 100% | −4.00 | −4.49 |

**Symmetry defect of core units with a nontrivial stabilizer** (median; isotropic-Gaussian null for the same function: 0.186)

| Env | Units | Step 100 | 300 | 1,000 | 3,000 | Final / null |
|---|---|---|---|---|---|---|
| A8-wd0.03 | 3,641 | 0.078 | 0.058 | 0.046 | **0.035** | **0.19** |
| A8-wd0 | 3,441 | 0.070 | 0.058 | 0.053 | 0.050 | 0.27 |

### Arm B

Regeneration checks: tic-tac-toe 958 instances, 626 positive (UCI: 958 / 626). MONK: 432 instances.

| Dataset @ labelled fraction | Plain MLP | MLP + CSP | Gain | Runs voided by conflict | Runs accepting a decoy |
|---|---|---|---|---|---|
| tic-tac-toe @ 0.1 | 0.911 | 0.964 | **+0.053** | 2/10 | 7/10 |
| tic-tac-toe @ 0.2 | 0.974 | 0.975 | +0.001 | 10/10 | 10/10 |
| tic-tac-toe @ 0.3 | 0.982 | 0.982 | +0.000 | 10/10 | 10/10 |
| MONK-1 @ 0.15 | 0.916 | 0.981 | **+0.065** | 0 | — |
| MONK-1 @ 0.3 | 1.000 | 1.000 | 0.000 | 0 | — |
| MONK-2 @ 0.15 | 0.775 | 0.877 | **+0.101** | 0 | — |
| MONK-2 @ 0.3 | 0.996 | 1.000 | +0.004 | 0 | — |
| MONK-3 @ 0.15 | 0.983 | 0.977 | −0.006 | 5/10 | — |
| MONK-3 @ 0.3 | 0.998 | 0.998 | 0.000 | 8/10 | — |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H18.1 | **Broken.** Without weight decay the unit-level bias persists (β_u = −2.73 under AdamW, −2.81 under GD). Weight decay strengthens it (GD: −2.81 → −4.49; AdamW: −2.73 → −3.27) but is not its cause. |
| H18.2 | **Held.** Trained core units are nearly exactly symmetric in weight space: median defect 0.035 vs 0.186 for random weights computing the same function (ratio 0.19). |
| H18.3 | **Held.** The defect falls by 55% from step 100 to step 3,000. Most of the symmetrization happens before step 100: the step-100 value is already 0.4 × null. |
| H18.4 | **Held.** Without weight decay the ratio is 0.27; the defect still falls (−29%). |
| H18.5 | **Neither.** +0.053 at 10% labelled; ≈ 0 at 20% and 30%, where every run was voided by a conflict. |
| H18.6 | **Broken as registered, because of a ceiling.** Gains of +0.065 (MONK-1) and +0.101 (MONK-2) at 15%. At 30% the plain MLP is already at 1.000 on MONK-1, so the gain is exactly 0, which meets the "≤ 0" kill condition. |
| H18.7 | **Held.** The worst mean change is −0.006 (MONK-3 at 15%). |
| H18.8 | **Broken.** Decoy cell swaps were accepted in 7/10, 10/10 and 10/10 tic-tac-toe runs. |

## Findings

**F1. Symmetric subspaces are attracting.** Every core unit whose threshold function has a nontrivial stabilizer ends with weights that are nearly *exactly* invariant under that stabilizer: 5 times closer to the symmetric subspace than random weights computing the same function. Most of this happens in the first 100 steps, and it continues more slowly afterwards. It happens without weight decay, which only strengthens it. This is the first direct evidence for the mechanism proposed in Spike 17: transverse attraction of weight vectors into fixed-point subspaces of the task's symmetry group.
- *An alternative not yet separated:* the ℓ2 max-margin weight vector of a threshold function is unique and therefore invariant under the function's stabilizer. Convergence toward a max-margin "centre" of the cone would also produce low defect. That explains *why weights are symmetric given t*. It does not explain *why symmetric t are chosen*, which is the Curie bias itself. The next test must measure attraction *before* the threshold function settles.

**F2. Weight decay is an amplifier, not the source.** β_u is about −2.7 to −2.8 without weight decay under both optimizers. Weight decay deepens it, most strongly under GD.

**F3. CSP gives large gains with little data, and never hurt by more than a point. But its certificate is wrong on real data.** At small labelled fractions CSP adds 5–10 points on tic-tac-toe, MONK-1 and MONK-2. The acceptance rule's false-accept bound assumed independent labels. On structured data, inputs differing in two cells often share a label for reasons unrelated to symmetry, so decoy swaps pass the test, and with more labelled data they pass more often. Harm was prevented by the conflict check (the run voids), not by the certificate. That also removed the benefit at 20–30% labelled. **A calibrated test is needed:** compare a candidate's label agreement with that of random transformations that move inputs by the same amount (a permutation null that keeps label smoothness).

## Status

- **Mechanism:** the bias is a unit-level law (Spike 17); symmetric weight subspaces are attracting (F1); weight decay amplifies (F2). Open: whether attraction *selects* t, or only symmetrizes weights once t is fixed.
- **Method:** useful in the low-data regime; the certificate must be recalibrated before CSP can be called certified.
