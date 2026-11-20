# Spike 20: Is training selection? A Gibbs temperature, transfer across architectures, and information versus agreement

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commit `a232d4c` before any run or fit · **Follows:** Spike 19 (the universal tilted-volume law); C9 in `THEORY.md`

## Inspirations, read before designing this spike (details in `charter/LITERATURE_REVIEW.md` §5)

- **Deletion Tuning** (Lu, Yang, Lasby, Pote, Ioannou, Ren, arXiv:2611.10866; read in full). Zeroing fewer than 0.05% of gate-projection weights matches full fine-tuning of LLMs: post-training "by selection alone".
  - Suggests **Arm C:** is gradient training of a small network itself mostly *selection* of pre-existing units? If so, a network that may only *select* among frozen random units should follow the same law, with the same parameters.
- **Redundancy maximization** (Blümel, Schneider, Neuhaus et al., Nat. Commun. 17, 11499 (2026); arXiv:2511.02584; read in full). A neuron's local goal of making its recurrent input *redundant* with the target (PID) is necessary and sufficient for associative memory. For a hard threshold it reduces to I(Y : T).
  - Suggests **Arm D:** our tilt term "agreement with the target" may be the wrong information measure. Mutual information between a unit's function and the target is the principled one.
- **LM head as gradient bottleneck** (Godey & Artzi, arXiv:2603.10145; read via the alphaXiv report, not the full text). 95–99% of the logit gradient is lost through a rank-D output layer.
  - In our language, the backward channel is an observational power on the error (`THEORY.md` §3.6). Not tested here.
- **Weight-Space Programming** (Takehi, Teoh, Zhang, Khattab, blog, Nov 2026; Beaker's follow-up post not reachable from this session). Frontier LLMs read and write raw weights.
  - Not tested here. The atlas could serve as an exactly verifiable benchmark for it (proposal in the literature review).

## Arm A: is the tilt a temperature set by training? (C9)

Fit the two-parameter law log w(t|g) = γ·log Ω(t) + λ·agree(t, g) by maximum likelihood on all 128 elements, separately for each stored run, with 100 bootstrap resamples over elements.

Runs:
- Spike 18: A8-wd0, A8-wd0.03, A8-wd0.1, G8-wd0, G8-wd0.003.
- Spike 14: A8, G8, A128.
- Spike 19: arm1.
- Spikes 12 and 13 (48 elements): W8 at 3,000 steps vs A8-10k at 10,000 steps.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H20.1 | Weight decay sharpens the tilt | λ(A8-wd0.1) > λ(A8-wd0.03) > λ(A8-wd0) **and** λ(G8-wd0.003) > λ(G8-wd0), each ordering in ≥ 90% of bootstrap resamples | any ordering reversed in point estimates |
| H20.2 | Longer training sharpens the tilt | λ(S13 A8-10k) > λ(S12 W8) in ≥ 90% of resamples | reversed |
| H20.3 | The law's form is stable across runs: γ stays positive | γ > 0 in every run | γ ≤ 0 in any run |

## Arm B: does the law transfer across architectures?

- **Fresh runs:** ReLU width 8 and tanh width 32 (output scale √(8/H)), AdamW, wd 0.03, 3,000 steps, 128 elements × 40 seeds.
- **Scoring:** the Spike 19 parameters, fitted on tanh width 8 (log w = 0.131·log|Stab| + 9.92·agree + 0.88·log Ω), on Spike 19's 64 held-out elements.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H20.4 | The universal law transfers to ReLU and to width 32 without refitting | gain ≥ 1.3 bits/run and ≥ Curie + 0.2 in both | below Curie in either |

## Arm C: is training selection? (after Deletion Tuning)

- **Selection-only network:** first layer frozen at its random initialization (width 512, the same law as before). Only the output layer is trained, with an L1 penalty (1e-3) so that a few units are selected. AdamW, 3,000 steps, 128 elements × 40 seeds. The core is read with R2, as before.
- **Fits:** the two-parameter law (γ_sel, λ_sel), compared with (γ_train, λ_train) from Spike 19 arm 1 (full training, same initialization law, width 8).

A pure selection process picks among units present at initialization, so its volume exponent should be near 1. Gradient training that actively *builds* agreeing units should have a stronger tilt than selection.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H20.5 | Full training is mostly selection: its tilt is close to that of selection | λ_train / λ_sel ∈ [0.7, 1.43] | λ_train / λ_sel ≥ 2 (training builds) |
| H20.6 | Selection follows prior volume | γ_sel ∈ [0.6, 1.4] | γ_sel ≤ 0.3 |

## Arm D: information or agreement? (after redundancy maximization)

Replace agree(t, g) by I(t; g), the mutual information between the unit's function and the target under uniform inputs. Fit (γ, λ) on the 64 training elements of Spike 14 A8, as in Spike 19. Test on the 64 held-out elements (Spike 14 A8, and Spike 19 fresh).

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H20.7 | Information is the better tilt variable | held-out gain(MI + Ω) ≥ gain(agree + Ω) + 0.05 bits on both test sets | lower than agree + Ω by more than 0.05 on both |

## Results (`results/spike20.json`; raw data in `results/spike20_raw/`)

Fit rates: ReLU-8 99.1%; tanh-32 100%; selection-only 100% (on average 14 of 512 units keep |w₂| > 0.05).

### Arm A: per-run fit of log w = γ·log Ω + λ·agree (bootstrap 95% intervals)

| Run | Elements | γ | λ |
|---|---|---|---|
| S14:A8 | 128 | 0.89 [0.69, 1.06] | 10.83 [9.54, 12.50] |
| S14:G8 | 128 | 0.95 [0.75, 1.13] | 9.84 [8.84, 11.03] |
| S14:A128 | 128 | 0.77 [0.58, 0.97] | 9.21 [8.09, 10.37] |
| S18:A8-wd0.03 | 128 | 0.88 [0.76, 1.07] | 10.73 [9.81, 12.20] |
| S18:A8-wd0.1 | 128 | 0.84 [0.67, 1.03] | 10.93 [9.76, 12.10] |
| S18:A8-wd0 | 128 | 0.92 [0.73, 1.08] | 10.65 [9.53, 11.99] |
| S18:G8-wd0.003 | 128 | 0.99 [0.79, 1.21] | 10.31 [8.85, 11.72] |
| S18:G8-wd0 | 128 | 0.98 [0.81, 1.17] | 11.04 [9.94, 12.01] |
| S19:arm1 | 128 | 0.87 [0.72, 1.03] | 10.57 [9.66, 11.67] |
| S12:W8 | 48 | 0.73 [0.46, 1.02] | 10.93 [8.98, 13.24] |
| S13:A8-10k | 48 | 0.68 [0.39, 0.94] | 10.84 [9.30, 12.58] |
| S20:relu8 | 128 | 0.98 [0.74, 1.17] | -1.32 [-5.11, 2.94] |
| S20:tanh32 | 128 | 0.84 [0.67, 0.99] | 10.37 [9.32, 11.66] |
| S20:selection | 128 | 1.08 [0.93, 1.27] | 2.68 [-0.21, 5.06] |

Bootstrap P(ordering): A8 wd 0.1 > 0.03: 0.54; A8 wd 0.03 > 0: 0.61; G8 wd 0.003 > 0: 0.22; A8 10k > 3k steps: 0.41.

### Arm B: Spike 19 parameters, unchanged, on the held-out 64 elements

| Architecture | Universal law (S19 params) | Curie |
|---|---|---|
| ReLU, width 8 | **−0.80** bits/run | 0.82 |
| tanh, width 32 | **1.57** | 1.35 |

### Arm C: selection-only vs full training

| | γ | λ |
|---|---|---|
| Selection only (frozen random first layer, width 512) | 1.08 [0.93, 1.27] | 2.68 [−0.21, 5.06] |
| Full training (Spike 19 arm 1, width 8) | 0.87 [0.72, 1.03] | 10.57 [9.66, 11.67] |

λ_train / λ_sel = 3.94. The bootstrap interval of the ratio is unbounded, because λ_sel's interval includes 0.

### Arm D: information or agreement (fit on 64 elements; tested on the other 64)

| Tilt variable | Fitted (γ, λ) | Held-out Spike 14 | Held-out fresh (Spike 19) |
|---|---|---|---|
| agreement | (0.94, 10.27) | 1.67 | 1.58 |
| **mutual information I(t; g)** | (1.06, 8.90) | **1.95** | **1.93** |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H20.1 | **Broken.** Weight decay does not sharpen the tilt. The A8 point estimates are ordered as predicted but indistinguishable (10.65 / 10.73 / 10.93), and the GD ordering is reversed (11.04 at wd 0 vs 10.31 at wd 0.003). |
| H20.2 | **Broken.** 10,000 steps give λ = 10.84, against 10.93 at 3,000. |
| H20.3 | **Held.** γ > 0 in every run (0.68–1.08). |
| H20.4 | **Broken.** The law transfers to tanh width 32 (1.57 bits, +0.22 over Curie), but fails completely for ReLU (−0.80, worse than uniform). |
| H20.5 | **Broken.** Full training's tilt is about 4× that of selection: training *builds* agreeing units; it does not merely select them. |
| H20.6 | **Held.** Selection follows prior volume (γ_sel = 1.08). |
| H20.7 | **Held.** Mutual information beats agreement by +0.28 and +0.35 bits/run on held-out elements. |

## Findings

**F1. The tilt is a constant, not a temperature.** Across every tanh run, λ ≈ 10.5 (interval about 9–12.5): AdamW and GD, weight decay 0–0.1, 3,000 or 10,000 steps, widths 8, 32 and 128. Conjecture C9, a Gibbs factor whose temperature is set by optimizer and horizon, is refuted. Whatever sets λ, it is not those knobs.

**F2. The activation function decides whether there is a tilt at all.** ReLU networks show *no* tilt: λ = −1.3, interval [−5.1, 2.9]. Their circuit choice follows prior volume alone (γ ≈ 1). So the tanh-fitted law gives worse than uniform predictions for ReLU. A ReLU unit whose pre-activation is negative on an input gets no gradient there, so units move little and the circuit is closer to what initialization offered.

**F3. Training = selection × building.** A network allowed only to *select* among frozen random units follows prior volume (γ ≈ 1) with a weak tilt (λ ≈ 2.7, interval includes 0). Full tanh training has the same volume term but a 4× stronger tilt (λ ≈ 10.6). The law therefore decomposes: **prior volume says which units are available; the tilt says how strongly gradient training reshapes them toward the target.** ReLU training behaves like selection (F2). This connects to Deletion Tuning's "post-training by selection": in our setting selection explains the volume factor, but tanh training does more than select.

**F4. Information beats agreement, as the redundancy-maximization paper suggests.** Replacing agreement with mutual information I(t; g) raises held-out prediction from about 1.6 to about 1.93 bits/run: about 70% of the per-element ceiling (2.75, Spike 19), up from 59%. The law is now

w(t | g) ∝ Ω(t)^1.06 · exp(8.9 · I(t; g)),

the prior solid angle times an exponential in the unit's information about the target. For a hard threshold, Blümel et al. show redundancy reduces to I(Y : T). Our tilt is that quantity, measured on what training *chose* rather than on a goal that was imposed.

## Updated statement of the law (supersedes the Spike 19 form)

For tanh networks trained by gradient descent (AdamW or GD, any weight decay and horizon tested, widths 8–128): restrict first to minimum cost, then

P(circuit I | g) ∝ product over the units t of I of Ω(t)^γ · exp(λ·I(t; g)), with γ ≈ 1 and λ ≈ 9 (per bit of mutual information).

For ReLU networks and for selection-only training, the tilt vanishes, and what remains is the prior volume.
