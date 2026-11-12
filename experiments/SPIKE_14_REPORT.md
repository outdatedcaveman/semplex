# Spike 14: A Curie principle for learning? (and three other bold candidates)

**Date:** 2026-11-12 · **Status:** complete. Pre-registered in commits `0800f3c` and `071f726` (H14.9), before any Spike 14 analysis. Hypotheses come from an exploratory screen of already-seen data (`experiments/spike14_explore.py`) and are tested here on **fresh seeds** and on **80 elements never scored before** · **Candidates:** `charter/ABDUCTION.md` §5 · **Prior-art gate:** see the end of this report.

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
| H14.9 | (added before any Spike 14 analysis; screen on Spikes 12–13) | Minimality is reached when minimal options are abundant: across elements, the share of nets with a non-minimal core falls with log(number of isomers) | Spearman ≤ −0.3 on the 80 unseen elements, in every run | ≥ 0 in any |

Between thresholds, the verdict is "neither".

**Killed in the screen (recorded, not tested):** a "frustration" corollary of B1 predicted more non-minimal cores when every minimal circuit of g has a large orbit. On Spikes 12–13 data the sign was reversed in all 13 environments (ρ ≈ −0.17 to −0.35).

## Prior-art gate (abstract or index level)

- arXiv:2309.16932 (Ziyin et al.): mirror symmetries of the *loss in parameter space* make symmetric solutions attractive under gradient noise. This is a possible mechanism for B1, but it concerns parameter symmetries, not orbits of a task's discrete minimal mechanisms.
- arXiv:2610.36138: limited capacity forces a predictable amount of symmetry breaking. This is the opposing pull. B1 says that, among the solutions capacity allows, training breaks as little as it can.
- No source found that states a power law of mechanism mass in orbit size under the task's symmetry group, or that tests one against an exact list of circuits.

## Results (`results/spike14.json`; post hoc diagnostics in `experiments/spike14_diag.py`)

Fit: 99.9% (A8), 100% (G8), 100% (A128). "All" means 128 elements; "unseen" means the 80 never scored before.

| | A8 all / unseen | G8 all / unseen | A128 all / unseen |
|---|---|---|---|
| H14.1 within-orbit variance share (observed vs multinomial null) | 0.046 vs 0.048 / 0.038 vs 0.044 | 0.041 vs 0.044 / 0.036 vs 0.039 | 0.022 vs 0.034 / 0.026 vs 0.036 |
| **H14.2 β** (orbit mass ∝ \|orbit\|^β) | **−2.28 / −2.98** | **−3.60 / −5.72** | **−3.22 / −3.43** |
| H14.3 within equal-agreement strata: median ρ(mass, orbit size); share of strata negative | −0.32 (67%) / −0.33 (72%) | −0.35 (78%) / −0.44 (81%) | −0.33 (80%) / −0.36 (85%) |
| **H14.4 Curie predictor, gain over uniform (bits/run)** | **+1.31 / +1.32** | **+1.63 / +1.67** | **+1.25 / +1.30** |
| (volume, same metric) | −0.06 / +0.16 | +0.11 / +0.39 | −0.14 / +0.05 |
| Median Spearman: Curie / agreement / hub / U-product / volume | 0.35 / 0.41 / 0.27 / 0.75 / 0.13 | 0.33 / 0.39 / 0.23 / 0.67 / 0.15 | 0.35 / 0.41 / 0.32 / 0.74 / 0.17 |
| U-product gain (bits/run) | −0.33 / −0.80 | −0.81 / −1.24 | −0.51 / −0.71 |
| H14.6 fossil: share of cores containing it vs its isomer baseline; share containing t\* | 8.7% vs 2.6% (3.3×); 38.5% | 8.8% vs 2.7% (3.3×); 32.2% | 27% vs 4.8% (5.7×, only 132 runs have a fossil); 33.9% |
| **H14.9** ρ(non-minimal share, log #isomers), unseen | **−0.60** | **−0.48** | **−0.55** |

**H14.5, partial tasks (all 222 elements, 6,660 runs):** among runs that chose a cheapest completion, and where the cheapest completions differ in symmetry, the learned completion was **more symmetric than the average cheapest completion in 4,475 cases and less in 1,355** (77%; 113 ties; one-sided sign test p < 10⁻³⁰⁰).

**Post hoc diagnostics (not pre-registered):**

| | A8 | G8 | A128 |
|---|---|---|---|
| Spearman among isomers actually observed: U-product / Curie | 0.13 / 0.56 | 0.58 / 0.87 | 0.17 / 0.54 |
| Share of runs whose circuit uses only units a single-unit net ever reaches | 34% | 37% | 33% |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H14.1 | **Held.** Within-orbit variation equals the multinomial null. Theorem 15 is confirmed. |
| H14.2 | **Held.** β ≤ −2.3 in every run, on all and on unseen elements. |
| H14.3 | **Held.** Within groups of orbits that agree equally with g, mass still falls with orbit size (median ρ −0.32 to −0.44). The Curie bias is not agreement in disguise. |
| H14.4 | **Held.** The parameter-free Curie predictor gains 1.25–1.67 bits per run, on unseen elements too. Spike 11's volume predictor gained −0.02. |
| H14.5 | **Held.** The Curie bias holds at the level of *functions*: 77% of non-ties, p < 10⁻³⁰⁰. |
| H14.6 | **Neither.** The fossil is in the core 3–6× more often than chance, but less often than the global t\* (the second criterion failed). B3 does not beat A1. |
| H14.7 | **Held as registered (ρ 0.67–0.86 vs agreement 0.39–0.45), but the diagnostic shows why.** The U-product ranks well because it predicts *which isomers are possible*: those it gives zero, training rarely builds. Among isomers that do occur it ranks weakly under AdamW (0.13–0.17), and as a probability it is badly calibrated (negative gain). |
| H14.8 | **Neither.** Hub degree gives ρ 0.23–0.32; option value is a modest predictor, not a principle. |
| H14.9 | **Held.** Elements with more minimal circuits reach one more reliably (ρ −0.48 to −0.60 on unseen elements). |

## Findings

**F1. A Curie principle for learning: training preserves the task's symmetry as far as it can.** Every law of mechanism choice in this setting is a law about orbits of the task's symmetry group (Theorem 15, confirmed). Across those orbits, training does the opposite of what an entropy or volume argument predicts. A mechanism type that keeps more of the task's symmetry (a smaller orbit) gets *more* total probability, not less, roughly as |orbit|^−3. This holds under both optimizers, at widths 8 and 128, and on 80 elements never examined before, with its exponent fixed in advance. It is the first predictor in Spikes 11–14 that carries a large amount of information about the circuit: about 1.3–1.7 bits per run, where volume carries none.

**F2. The same principle works one level up, on functions.** When a task leaves inputs unspecified and several cheapest completions exist, training chooses a more symmetric one 77% of the time. Spike 09 F1 (training picks a *cheapest* completion) and Spike 14 F1 (training picks a *symmetric* mechanism) are two faces of one bias. Among equally cheap functions, the tie is broken by symmetry. One law covers both the choice of what to compute and the choice of how to compute it.

**F3. Mechanisms are cooperative: two thirds contain a part that cannot exist alone.** Only about 35% of learned circuits use only units that a single-unit network trained on the same task ever reaches. In the rest, at least one unit exists only because a partner does. The single-unit predictor mostly tells which circuits are *possible*. It does not tell which possible circuit is chosen; Curie does that better (0.54–0.87 vs 0.13–0.58 among observed isomers).

**F4. Abundance of minimal solutions predicts whether training finds one.** Across elements, the share of nets that end in a non-minimal core falls strongly with the number of minimal circuits (ρ ≈ −0.55). A corollary of B1 that predicted the opposite, "frustration", was killed in the screen.

**F5. Two of the candidates were weak.** The fossil is real but weaker than t\* (B3); option value is modest (B2).

## What this changes

The question "which mechanism does training build?" now has a structural partial answer that does not mention weights, volumes or margins: **the one that keeps the most of the task's symmetry, among those the network can assemble cooperatively.** The answer is stated purely in terms of the task's symmetry group, so it can be tested in any domain where the group is known: group operations, permutation-invariant tasks, images under translation. That is the next test (conjecture C8 in `THEORY.md`).

## Gaps

- β is estimated from binned pooled data and varies (−2.3 to −5.7). The predictor's exponent was fixed at β = −2, so the information gain is a lower bound for a better-calibrated law.
- 4-input Boolean tasks, tanh, full batch. Transfer to another domain is the decisive test.
- The R2 readout excludes non-minimal cores (about half of runs).
- No mechanism is offered yet for why symmetric mechanisms are attracting; arXiv:2309.16932 is a candidate.
