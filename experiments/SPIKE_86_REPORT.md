# Spike 86: The growth-rate race: is the Gibbs selection rule the outcome of a race between linearly growing representations?

**Date:** 2026-11-19 · **Status:** pre-registered (automata, features and the near-tie sample in `results/spike86_predictions.json`, committed with this report before any run) · **Follows:** Spikes 77–80 (C43, P212–P214, P217) and the bifurcation-theory reading of 2026-11-19 (`charter/LITERATURE_REVIEW.md`: Yang 2605.24057, He et al. 2606.02993 and 2602.16849, Kunin et al. AGF, Cross–Hohenberg).

## The mechanism under test

**Starting point.** From a small initialisation the hidden geometry starts near zero, and each isotypic block ρ grows at its own early rate σ_ρ.

**The race.** If the block that wins the race leads at the end, then three things follow:
- The leader is argmax_ρ [σ_ρ T + log A_ρ(0)].
- Across seeds this becomes a softmax in σ. That would *explain* the Gibbs form, P(ρ) ∝ exp(−βΔ), and the seed lottery.
- The rule's two terms should appear in the growth rate itself:
  - energy (value) speeds a block's growth;
  - kinetic cost (the Swift–Hohenberg-like "diffusion" term) slows it.

**Derived predictions:**
- The lottery should sharpen as the initialisation shrinks, because the race is longer.
- Weight decay should raise the exchange rate. Like a resource cost, it penalises the larger weights a costlier (faster-rotating) representation needs.

## Design

**Learner.** GRU (64 units) + AdamW, lr 0.003, cosine schedule, 6,000 steps, length 30, batch 64. This is the learner (α, λ) were frozen on.
- SGD was piloted first on a calibration automaton outside both test sets (D5_pt). At initialisation scale 0.1 or 0.3 it stayed on its plateau (fit 0.81). Adam at scale 0.1 fitted (1.0), and AdamW with weight decay 0.05 fitted (1.0).
- No other choice was tuned on the pilot.

| Arm | Initialisation scale (all parameters multiplied) | Weight decay |
|---|---|---|
| R (race) | 0.1 | 0 |
| D (default) | 1.0 | 0 |
| W (pressure) | 1.0 | 0.05 |

**Automata:**
- **Set A:** the 11 decisive automata of Spike 77 (arm R, 5 seeds).
- **Set B:** 8 *near-tie* automata. They come from the 17 unused pool automata whose frozen-rule probability of the top block is 0.35–0.6, whose top two blocks differ in cost by > 0.05, and which were drawn with seed 86. All 8 happen to be ℤ/11 automata; in every one the top two blocks have probabilities 0.54 / 0.40. Set B is run in arms R, D and W with 8 seeds each.
- 247 runs in total. The fit guard is ≥ 0.99 at length 100.

**Growth rate.**
- Absolute isotypic energy of the centred centroid Gram, tr(P_ρ G P_ρ), at checkpoints every 10 steps up to step 500, then every 250.
- The window runs from step 10 to the first checkpoint where total energy reaches 10% of its final value, with at least 3 checkpoints.
- σ_ρ is the least-squares slope of log energy over that window.
- The leader is the top block of the final normalised shares (as in Spikes 69–80).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H86.1 | **The race decides the winner:** in arm R the final leader is the block with the largest early growth rate | ≥ 75% of fitted runs (≥ 20 runs) | < 50% |
| H86.2 | **The rule is the growth rate:** σ_ρ (z-scored within run) regressed on log e_ρ and c_ρ over arm R has a positive energy coefficient and a negative cost coefficient | both 95% bootstrap CIs (resampling automata, 2,000 draws) exclude 0 with the right sign | either CI excludes 0 with the wrong sign |
| H86.3 | **Not a dimension artefact** (He et al.): with log(block dimension) added as a covariate, the energy coefficient stays positive | CI > 0 | CI < 0 |
| H86.4 | **The lottery sharpens at small initialisation:** on set B, the mean frequency of the modal leader in arm R exceeds arm D | by ≥ 0.10 | R < D |
| H86.5 | **Weight decay raises the exchange rate:** on set B, the fraction of runs led by the cheaper of the two top blocks in arm W exceeds arm D | by ≥ 0.10 | W < D |
| H86.6 | **Form:** a linear-in-energy law (a·e − b·c) fits the leaders of arms R and D better than the log-linear rule (α log e − λ c), both with two parameters fitted by maximum likelihood | NLL_linear < NLL_log | NLL_linear ≥ NLL_log |

Anything else is *neither*. H86.6 is a two-way model comparison: "broken" means the current log-linear form is preferred.

## What this cannot show

- One architecture and one optimiser family.
- With Adam, "small initialisation" is only partly a lazy-to-rich switch, because Adam's step size does not scale with the weights.
- Set B is all ℤ/11, with one tie structure.
- A growth rate measured in the hidden geometry is not the linearised Jacobian eigenvalue. It is its observable consequence.
- The independence-of-irrelevant-alternatives test and a sharp noise threshold (quasispecies) are deferred.

## Commands

```
python -m experiments.spike86 predict
python -m experiments.spike86 run 0/4      # parts 0/4 .. 3/4 in parallel
python -m experiments.spike86 analyse
```

## Results

`experiments/results/spike86.json`; per-run trajectories in `spike86_raw/`. All 247 runs completed.

**Fit:** the guard is ≥ 0.99.
- Arm R: 60/119 fitted. Set A: 37/55. Set B: 23/64.
- Arm D: 59/64. Arm W: 49/64.

Small initialisation fitted reliably on the pilot automaton but not on the ℤ/11 near-tie set. Filtering by fit may bias arm R, so this is a caveat on H86.1 and H86.2.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H86.1 | the block with the largest early growth rate leads at the end in 35/60 (58%) | ≥ 75% held, < 50% broken | **NEITHER** |
| H86.2 | energy coefficient +0.079, CI [0.035, 0.119]; cost coefficient −0.019, CI [−0.62, 0.70] | both CIs exclude 0 with the right sign | **NEITHER** |
| H86.3 | with log(dimension) as a covariate the energy coefficient is +0.069, CI [0.020, 0.154] | CI > 0 | **HELD** |
| H86.4 | too few set-B automata with ≥ 4 fitted arm-R runs | ≥ 5 automata per arm | **NO VERDICT** |
| H86.5 | led by the cheaper block: W 0.65 vs D 0.69 | W − D ≥ 0.10 | **BROKEN** |
| H86.6 | NLL linear-in-energy 66.0 vs log-linear 59.1 | NLL_linear < NLL_log | **BROKEN** (the log-linear rule is preferred) |

Modal-leader frequency (descriptive, for H86.4): R 0.92, D 0.93, W 0.85.

**Reading:**
- **The race mechanism explains the value term, not the cost term.**
  - Early growth rates rise with predictive energy share. This survives a block-dimension covariate, so the He et al. (2606.02993) worry that "dimension through initialisation geometry, not energy" drives selection does not hold here.
  - Kinetic cost has no detectable effect on *early* growth, and the race winner predicts the final leader only 58% of the time.
  - So cost acts after the linear phase, during consolidation or competition, not as a diffusion term in the growth rate. The Swift–Hohenberg reading (cost = −Dk² in the dispersion relation) is not supported.
- **Weight decay does not raise the exchange rate.** It slightly lowers the share of the cheaper block. The resource-pressure effect of Spike 77, where state noise raised λ/α, is therefore not a generic "pressure" effect: noise on the state works, decay on the weights does not.
- **The log-linear form stands against the linear softmax-in-σ form.** That is one more strike against reading the rule as a pure growth-rate race.
- **Next:** the input-diffusion test of the heat-kernel reading of λ (`charter/LITERATURE_REVIEW.md`, 2026-11-19), and measuring the cost term's effect in the post-race phase, e.g. which block's share grows after the total energy saturates.
