# Spike 79: The last loopholes: non-abelian groups unselected, non-recurrent and gradient-free learners, and a derived cost

**Date:** 2026-11-18 · **Status:** complete (pre-registered with predictions in 26bdec6; results below) · **Follows:** Spike 78 (P213). The Gibbs rule P(ρ) ∝ e_ρ^α·exp(−λ c_ρ) survived five of six loophole tests there. Three gaps remained:
- the random sample was all cyclic;
- only recurrent, gradient-trained learners were tested;
- the cost was a proxy.

**α = 2.49 and λ = 3.68 stay frozen.**

## (A) Unselected non-abelian automata

Pool: 11 non-abelian generating sets:
- S₃ ((01), (012)) and S₃ ((01), (12));
- D₄, D₅ with rotation + reflection and with two reflections; D₆ with rotation + reflection;
- A₄ ((012), (01)(23)) and A₄ ((012), (123));
- S₄ ((01), (0123)) and S₄ Coxeter;
- Q₈.

Readouts: point (one-hot of g(0)), two-point and three-point subsets. A random sample of 10 (seed 79), excluding the construction already run in Spike 77 (S3_pt):

**A4a_sub013, A4a_sub023, A4b_pt, A4b_sub01, D4rf_sub023, D6rf_sub012, S3t_sub01, S3t_sub02, S4c_sub013, S4x_pt.**

The Gibbs prediction differs from the smoothness rule in A4a_sub013, A4a_sub023, D4rf_sub023 and S4c_sub013. It coincides with the energy rule in all 10, so this arm tests generality, not energy against cost.

Learner: GRU + Adam (Spike 77 recipe without the identity-letter change: the generators plus identity), 3 seeds.

## (B) Other substrates on unselected cyclic automata

The first 6 automata of Spike 78's random sample:

**Z11_s1_019, Z11_s1_038, Z11_s2_015, Z11_s2_016, Z11_s3_023, Z11_s3_035.**

Three discriminate between rules: Z11_s1_038 and Z11_s2_015/016 (Gibbs = energy ≠ smooth); Z11_s3_023 (Gibbs = smooth ≠ energy).

- **ES:** the GRU trained by evolution strategies (Spike 75's recipe, 4,000 iterations). No gradients.
- **TF:** a 2-layer causal transformer, as in Spike 60. No recurrence. The hidden state is the final residual per position. Fit is measured at the training length 30.

3 seeds each.

## (C) The cost from first principles

Moving a *labelled* state x to ρ(a)x within the representation costs, at minimum, the kinetic action of the straight path, ∝ ‖ρ(a)x − x‖². For x uniform on the representation's unit sphere:

  E‖ρ(a)x − x‖² = 2(1 − Re χ_ρ(a)/d_ρ) = 2·c_ρ(a).

So **the cost index used since Spike 77 is exactly the mean minimum (Euclidean) kinetic cost of carrying out each input's action**, up to a factor of 2. This is the representation-theoretic form of a minimum-dissipation (speed-limit) bound for a transformation with fixed particle identities.

The registered alternative is the *geodesic* cost E[angle(x, ρ(a)x)²], motion confined to the orbit sphere. It is computed by sampling 400 points of the isotypic sphere.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H79.1 | Unselected non-abelian automata, frozen rule (GRU) | argmax accuracy ≥ 75% **and** NLL below both rivals (≥ 5 automata fitted) | accuracy < 50% |
| H79.2 | Gradient-free learner (ES), frozen rule | NLL below both rivals (≥ 4 automata fitted) | otherwise |
| H79.3 | Non-recurrent learner (transformer), frozen rule | NLL below both rivals (≥ 4 automata fitted) | otherwise |
| H79.4 | **The kinetic (chord²) cost is the right form** | leave-one-(learner, automaton)-out NLL with refitted α, λ is lower for chord than for geodesic, over all fitted Spike 79 runs (≥ 6 groups) | otherwise |

Anything else is *neither*.

## What this cannot show

- ES and transformers may fail to fit; the guards then give no verdict.
- The non-abelian sample agrees with the energy rule everywhere, so it cannot separate energy from cost.
- The kinetic derivation treats the representation space as the arena of motion. A network's hidden space is larger and nonlinear.

## Commands

```
python -m experiments.spike79 predict
python -m experiments.spike79 run
python -m experiments.spike79 analyse
```

## Results

`experiments/results/spike79.json`; per-run outputs in `spike79_raw/`. All 66 runs completed; a container restart interrupted them once, and the seeded runner resumed without changing anything.

**Fits:**
- GRU on non-abelian automata: 30/30.
- Transformer: 18/18 at the training length.
- **ES: 0/18 fitted (0.61–0.82)**, so H79.2 has no verdict.

| Arm | Accuracy of frozen rule (argmax) | NLL Gibbs / energy-only / smoothness-only |
|---|---|---|
| GRU, 10 unselected non-abelian automata | **29/30 (96.7%)** | 2.22 / **2.08** / 23.5 |
| Transformer, 6 unselected cyclic automata | **15/18 (83%)** | **6.63** / 8.07 / 33.2 |
| ES, the same 6 cyclic automata (unfitted, exploratory) | 15/18; the misses are Z11_s2_015, where ES led with the smooth r3 | — |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H79.1 | accuracy 96.7%; NLL 2.22, not below energy-only's 2.08 | accuracy ≥ 75% **and** NLL below both rivals | **NEITHER** |
| H79.2 | no fitted ES runs | guard | **NO VERDICT** |
| H79.3 | transformer: Gibbs NLL 6.63 < 8.07, 33.2 | below both rivals | **HELD** |
| H79.4 | LOO NLL chord 28.44 vs geodesic 28.33 | chord < geodesic | **BROKEN** (by 0.4%) |

**Reading:**
- **Non-abelian groups, unselected (H79.1 neither).** The frozen rule names the leading representation in 29 of 30 runs on randomly drawn non-abelian automata: S₃, D₄, D₆, A₄ and S₄ with varied generators and readouts. As stated in advance, in this sample the Gibbs and energy predictions coincide everywhere. The cost term therefore only slightly lowers the rule's confidence, and energy-only wins narrowly on likelihood. This confirms generality without separating cost from energy. The separating non-abelian evidence remains the selected cases of Spike 77 (D₇) and Spike 69 (A₄ on pairs).
- **A non-recurrent learner follows the same rule (H79.3 held).** Transformers trained on unselected cyclic automata lead with the rule's prediction in 83% of runs and beat both rivals. The law is not specific to recurrence.
- **Gradient-free learning (H79.2 no verdict).** Evolution strategies did not fit within 4,000 iterations. Unfitted, they already lead with the rule's prediction in 15/18 runs, deviating once toward smoothness.
- **The cost's form is not resolved (H79.4 broken, by 0.4%).**
  - The kinetic (straight-line, minimum-dissipation) cost and the geodesic (on-orbit) cost fit these data equally well (28.4 vs 28.3).
  - The kinetic derivation stands as mathematics: the index *is* the mean minimum kinetic cost of each input's action.
  - The data do not single it out. On these automata the two forms are nearly monotone transforms of each other.
  - Separating them needs large-angle actions, where chord² and angle² diverge.

**Where C43 stands after all loophole tests (Spikes 77–79):**
- **Supported:**
  - holds prospectively and on unselected samples;
  - across GRU, LSTM, tanh RNN and transformer, and two optimisers;
  - on cyclic, dihedral and non-abelian groups;
  - on reparametrisation-invariant geometry;
  - with learner-specific exchange rates;
  - with no missing variable.
- **Not supported:** usage-weighting of the cost (Spike 78).
- **Untested or unresolved:**
  - gradient-free learners at convergence;
  - the cost's exact functional form (chord vs geodesic);
  - energy against cost in an *unselected* non-abelian sample.
