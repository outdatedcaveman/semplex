# Spike 20: Is training selection? A Gibbs temperature, transfer across architectures, and information versus agreement

**Date:** 2026-11-12 · **Status:** pre-registered (no run, and no fit of the statistics below, has been made) · **Follows:** Spike 19 (the universal tilted-volume law); C9 in `THEORY.md`

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
