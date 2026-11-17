# Spike 69: The two-regime law (C37), registered with the predictive kernel's structure computed beforehand

**Date:** 2026-11-17 · **Status:** pre-registered (predictions in `results/spike69_predictions.json`, committed with this report before any run) · **Follows:** Spike 66 (P199–P200), where the identity readout made the predictive kernel exactly diagonal and that degeneracy was not checked before registration. Also follows Spike 62 (the predictive-state law) and the S4_6 anomaly (Spikes 60, 66). **Conjectures:** C37; the predictive-state law; the S4_6 anomaly.

## What changed since Spike 66

The predictive kernel is computed exactly before training (`python -m experiments.spike69 predict`), and each automaton is classified by a structure index fixed in advance.

**Predictive kernel.** K(g, h) = Σ_{t=1..30} E_w ⟨o(g w), o(h w)⟩ over uniform random words w of length t, then double-centred.

**Irreducibles.** These are computed numerically for any group, as isotypic projectors P_i of the regular representation. Complex-conjugate and quaternionic types are merged into real irreducibles. Each is labelled `r<k>_tr<d²>_ker<|kernel|>`; ker1 means faithful.

**Isotypic share.** The share of the kernel's Frobenius energy in component i is ‖P_i K P_i‖² / ‖K‖².

**Structure index τ.** τ is the total-variation distance between the kernel's isotypic shares and those of the degenerate kernel, the centring matrix, whose shares are tr P_i / (n − 1). τ = 0 exactly for an identity-like predictive state.
- **Degenerate regime:** τ < 0.15.
- **Structured regime:** τ ≥ 0.15.
- **Unique prediction:** a structured kernel whose top share is ≥ 1.5 × the second.
- **Tie:** any other structured kernel.

A tie arises structurally. In a permutation readout, every multiplicity-1 constituent of perm − 1 carries the same energy, m_i² |G|². This explains why a tie-break rule is needed (S4_6).

**Smoothness of a constituent.** The mean over the generating letters a of P(e, a)/P(e, e). For cyclic groups this is cos(2πk/n), so the smoothest faithful character is the k = ±1 circle.

## Automata

The letters are the generators plus an identity letter (as in Spike 66). States are group elements and the output is given per element. In every case the minimal automaton is the whole group, checked by Moore minimisation.

| Name | Group, generators | Readout | τ | Class | Prediction (C37) | Architectural-bias alternative |
|---|---|---|---|---|---|---|
| Z8_id | ℤ/8, +1 | [g = e] | 0.000 | degenerate | minimal faithful: k = ±1 or ±3 | same |
| S3_id | S₃, (01), (012) | [g = e] | 0.000 | degenerate | std (r0_tr4) | same |
| A4_id | A₄, (012), (01)(23) | [g = e] | 0.003 | degenerate | χ₃ (r1_tr9) | same |
| D4_id | D₄, (0123), (13) | [g = e] | 0.000 | degenerate | 2-dim (r2_tr4) | same |
| Q8_id | Q₈, i, j | [g = e] | 0.000 | degenerate | quaternionic 2-dim (r2_tr4) | same |
| D4_4 | D₄ | one-hot g(0) | 0.357 | tie | {2-dim faithful r2, 1-dim r0} | r2 |
| **A4_6** | A₄ | one-hot pair {g(0), g(1)} | 0.484 | unique | **ω-pair r0_tr2_ker4 (unfaithful; share 0.67 against χ₃ 0.33)** | χ₃ |
| **Z7_02** | ℤ/7 | [g(0) ∈ {0, 2}] | 0.478 | unique | **k = ±3 (r1; share 0.81)** | k = ±1 (r2) |
| Z9_013 | ℤ/9 | [g(0) ∈ {0, 1, 3}] | 0.390 | unique | k = ±1 (r1; 0.55) | same |
| **Z8_014** | ℤ/8 | [g(0) ∈ {0, 1, 4}] | 0.623 | unique | **k = ±2 (r0, unfaithful; 0.90)** | k = ±1 (r3) |
| Z4xZ2 | ℤ/4 × ℤ/2 | one subset bit | 0.623 | unique | r2_tr2_ker2 (0.91) | none faithful |
| V4_01 | V₄ | [g = e], [first factor trivial] | 0.593 | unique | r0_tr1_ker2 (0.93) | none faithful |
| Z33_sub | ℤ/3 × ℤ/3 | one subset bit | 0.250 | tie (three-way) | {r1, r2, r3} | none faithful |
| Q8_sub | Q₈ | [g ∈ {1, i, j}] | 0.352 | unique | quaternionic r2 (0.92) | same |
| S4_6 | S₄, (01), (0123) | one-hot pair | 0.435 | tie | {std r2, χ₂ r0} | std |
| S4_6cox | S₄, (01), (12), (23) | one-hot pair | 0.435 | tie | {std r2, χ₂ r0} | std |
| S4_6c3 | S₄, (012), (0123) | one-hot pair | 0.435 | tie | {std r2, χ₂ r0} | std |

The bolded rows are the discriminating cases, where the predictive kernel and the architectural bias (the smoothest minimal faithful irreducible) disagree.

**A4_6 is the S4_6 anomaly transplanted.** A₄ acting on pairs has perm − 1 = χ₃ + (ω ⊕ ω̄). There the merged ω-pair carries twice the energy of χ₃, so the predictive law makes a *unique*, unfaithful prediction. If networks build χ₃ here as they built std in S4_6, the anomaly is a general preference for the faithful constituent over the predictive kernel's choice.

## Training and measurement

As Spike 66:
- GRU with hidden size 64 and embedding 16;
- Adam with lr 0.003, cosine to 0 over 6,000 steps;
- strings of length 30, batch 64, binary cross-entropy;
- 5 seeds per automaton: seed 6,900 + 10·index + seed;
- fit guard: accuracy ≥ 0.99 on 500 strings of length 100.

**Measured on 400 strings of length 30, steps 5–29:**
- the centred, normalised centroid per element, giving the cosine Gram;
- ρ_predictive: the Spearman correlation of the off-diagonal Gram with K;
- ρ_onestep: the same against the one-step output kernel;
- the best irreducible: the highest Spearman correlation of the Gram with P_i;
- the macrostate probe.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H69.1 | Structured regime: geometry = predictive kernel | ρ_predictive ≥ 0.6 in ≥ 80% of fitted structured runs | < 50% |
| H69.2 | Structured regime: predictive beats one-step | ρ_predictive > ρ_onestep in ≥ 80% | < 50% |
| H69.3 | Unique predictions: best irreducible = the kernel's top isotypic component | ≥ 80% of fitted unique runs | < 50% |
| H69.4 | Degenerate regime: best irreducible is a minimal faithful one (architectural bias) | ≥ 80% of fitted degenerate runs | < 50% |
| H69.5 | Ties are broken toward the faithful constituent (D4_4, S4_6 ×3) | best irreducible is the faithful tied one in ≥ 80% | < 50% |
| H69.6 | Ties are broken toward the lowest-dimensional constituent (same cases) | ≥ 80% | < 50% |
| H69.7 | **Discriminating cases** (A4_6, Z7_02, Z8_014): the predictive law beats the architectural bias | the predicted irreducible is best in ≥ 80% | the smoothest minimal faithful irreducible is best in ≥ 50% |

H69.5 and H69.6 are incompatible on these cases: at most one can hold. Anything else is *neither*.

**Guards.**
- An automaton counts only with ≥ 3 fitted seeds.
- H69.1–H69.3 need ≥ 4 qualifying automata, H69.4 needs ≥ 3, and H69.5–H69.7 need ≥ 2.
- Z33_sub, a tie with no faithful constituent, is reported only.

**Reported without criteria:**
- all irreducible scores;
- in Z8_id, whether the circle is k = ±1 or ±3;
- the macrostate probe.

## What this cannot show

- One architecture.
- Groups of order ≤ 24.
- The Spearman correlation against one irreducible's kernel is a coarse summary of a Gram that can mix several constituents.
- τ and the 1.5 tie margin are thresholds chosen with the predictions, before any run, not derived.

## Commands

```
python -m experiments.spike69 predict
python -m experiments.spike69 run
python -m experiments.spike69 analyse
```
