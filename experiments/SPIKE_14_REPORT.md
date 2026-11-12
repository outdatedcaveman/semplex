# Spike 14: A Curie principle for learning? (and three other bold candidates)

**Date:** 2026-11-12 · **Status:** pre-registered. Hypotheses come from an exploratory screen of already-seen data (`experiments/spike14_explore.py`) and are tested here on **fresh seeds** and on **80 elements never scored before** · **Candidates:** `charter/ABDUCTION.md` §5 · **Prior-art gate:** see the end of this report.

## The idea

**B0 (theorem).** Initialization and loss are invariant under the task's symmetry group G_g: input permutations and negations that map g to g or ¬g. The training map is equivariant. So the probability of each minimal circuit is constant on G_g-orbits, and any law of mechanism selection is a law about orbits.

**B1 (Curie principle for learning).** Training favours circuits that keep a large part of the task's symmetry: small orbits get far more total mass than large ones. Exploratory screen: orbit mass ∝ |orbit|^β with β between −1.8 and −2.9 in all 13 earlier environments. β = 1 would be "every circuit equally likely" (entropy, volume); β = 0 would be "every symmetry type equally likely".

**B2 (option value):** units with many minimal completions are preferred. **B3 (fossil):** the last single-threshold function computed before fitting stays in the core. **B4 (independent parts):** P(I) ∝ U(t1)·U(t2), where U is measured on single-unit networks.

## Runs (fresh seed bases 14 000+)

| Run | What | Scale |
|---|---|---|
| A8 | AdamW, width 8, 3,000 steps, checkpoints at 10…2,000 | 128 elements × 40 seeds |
| G8 | GD lr 0.3, wd 0.003, width 8, 10,000 steps | 128 × 40 |
| A128 | AdamW, width 128, 3,000 steps | 128 × 40 |
| U1 | single hidden unit, AdamW, 3,000 steps (for B4) | 128 × 200 |
| PART | partial tasks: 8 of 16 inputs given, 6 care sets per element, 5 seeds, AdamW width 8, 4,000 steps | all 222 elements |

The readout is R2 throughout. The Curie predictor's exponent is **fixed now** at per-isomer mass ∝ |orbit|^(β−1) with β = −2, the conservative end of the exploratory range. It is not refitted.

## Hypotheses and kill criteria

Each is checked on all 128 elements; "unseen" means the 80 new elements only.

| # | Candidate | Hypothesis | Held if | Broken if |
|---|---|---|---|---|
| H14.1 | B0 | Counts are uniform within orbits | observed within-orbit variance share ≤ 1.5 × multinomial null | ≥ 3 × null |
| H14.2 | B1 | Symmetric circuits win: β < 0 | β ≤ −1 in every run, all and unseen | β ≥ 0 in any run |
| H14.3 | B1 | Not agreement in disguise: within groups of orbits with equal agreement, mass falls with orbit size | median Spearman(mass, orbit size) ≤ −0.2 in every run | ≥ 0 in any run |
| H14.4 | B1 | The Curie predictor (no free parameter) gains information over uniform | ≥ 0.5 bits/run in every run (volume: −0.02 in Spike 11) | ≤ 0.1 in any |
| H14.5 | B1, functions | Among the cheapest completions of a partial task, training picks a more symmetric one (larger stabilizer) than average | share "more" ≥ 0.6 of non-ties, sign test p < 0.01 | share ≤ 0.5 |
| H14.6 | B3 | The run's last single-threshold function is in the core much more than chance and more than the global t\* | ratio to its isomer baseline ≥ 2 **and** share > share containing t\* | ratio ≤ 1 |
| H14.7 | B4 | Independent parts: the U-product predictor's Spearman is ≥ agreement's | in A8 and G8 | below agreement − 0.1 in both |
| H14.8 | B2 | Option value replicates: median Spearman of hub degree ≥ 0.3 | in every run | < 0.15 in any |

Between thresholds, the verdict is "neither".

## Prior-art gate (abstract or index level)

- arXiv:2309.16932 (Ziyin et al.): mirror symmetries of the *loss in parameter space* make symmetric solutions attractive under gradient noise. This is a possible mechanism for B1, but it concerns parameter symmetries, not orbits of a task's discrete minimal mechanisms.
- arXiv:2610.36138: limited capacity forces a predictable amount of symmetry breaking. This is the opposing pull. B1 says that, among the solutions capacity allows, training breaks as little as it can.
- No source found that states a power law of mechanism mass in orbit size under the task's symmetry group, or that tests one against an exact list of circuits.
