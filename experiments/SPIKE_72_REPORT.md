# Spike 72: Does the input encoding decide whether a network lifts to a cover?

**Date:** 2026-11-17 · **Status:** pre-registered (predictions in `results/spike72_predictions.json`, committed with this report before any run) · **Follows:** Spike 70 (C36: axis-trackers build the double cover S² → RP², P203) and Spike 60 (A₅ read through 6 points builds χ₅, P192). The comparison of the two was made on 2026-11-17 and is recorded in `charter/FOUNDATIONS.md` §13. **Related prior work:** Marchetti, Kunin et al. (arXiv:2602.03655) prove that the *encoding's* Fourier statistics set which irreps a two-layer network learns.

## The observation that motivates it

A₅ is the rotation group of the icosahedron. Its 6 cosets of D₅ are the icosahedron's 6 axes: 6 points of RP². So A₅ read through 6 points (Spike 60) is the discrete version of tracking an unsigned axis (Spike 70). Yet the two experiments went opposite ways:

| Experiment | Input encoding | What the network built |
|---|---|---|
| Spike 60, A₅ on 6 axes | one-hot letters (regular representation, no preferred irrep) | χ₅: the readout's own representation, the *quotient* |
| Spike 70, axis tracking under SO(3) | ω ∈ ℝ³ (the vector representation) | the signed direction: the *double cover* S² |

The icosahedral double cover of the 6 axes exists: 12 vertices in χ₃, a 3-dimensional representation, against 5 dimensions for χ₅. So "the network builds the smallest linear representation whose orbit covers the readout" would predict χ₃ in Spike 60, and it was not built.

**Conjecture C38 (the encoding decides the cover).** A recurrent network builds the orbit geometry in the representation that its *input encoding* makes cheapest. Given that representation as input, it lifts to the cover that representation provides. Given no preferred representation (one-hot), it builds the readout's own representation.

## Design

**Discrete part.** A₅ with letters (0 1 2), (0 1 2 3 4) and identity; the readout is the one-hot of the D₅ coset (6 axes); the minimal automaton is all of A₅. There are three input encodings, each feeding a GRU (hidden size 64) through a 16-unit input layer:
- **ONEHOT:** a learned embedding, as in Spike 60.
- **RHO3:** each letter given as its 3×3 icosahedral rotation matrix, flattened to 9 numbers. The representation is constructed and verified as a homomorphism on all 60 elements. Its character matches the real irreducible r1_tr9_ker1 exactly (correlation 1.00), so it is one of the two χ₃.
- **RHO5:** each letter given as its 5×5 matrix in the 6-axis representation minus trivial (χ₅, r3_tr25_ker1).

**Continuous part.** The Spike 70 AXIS task (σ = 0.15, output uuᵀ − I/3), with rotations given in three encodings:
- **OMEGA:** ω, 3 numbers, as in Spike 70.
- **D1:** R = exp([ω]×), 9 numbers (degree 1).
- **D2:** the 5×5 matrix of R acting on traceless symmetric matrices, 25 numbers (degree 2, the representation in which RP² sits).

**Training.** As Spikes 69–70: Adam with lr 0.003 cosine to 0, 6,000 steps, length 30, batch 64. Five seeds per encoding, seed 7,200 + 10·index + seed.

**Fit guards.**
- Discrete: accuracy ≥ 0.99 at length 100.
- Continuous: R² ≥ 0.90 at length 30.

**Measurements.**
- Discrete: each irreducible's isotypic share of the centred centroid Gram, both cosine and whitened (as in Spike 71); the leader is the top share.
- Continuous (as in Spike 70): harmonic regression R²_ℓ and a *class-balanced* sign probe on states with |u_z| ≥ 0.3. This fixes Spike 70's unbalanced probe.

## Predictions (C38)

| Encoding | Predicted leader | Alternative |
|---|---|---|
| ONEHOT | χ₅ (r3), replicating Spike 60 | — |
| **RHO3** | **χ₃ (r1)**, the icosahedral cover | χ₅ (the readout's own representation) |
| RHO5 | χ₅ (r3) | — |
| OMEGA | cover (sign kept), replicating Spike 70 | — |
| D1 | cover (sign kept) | — |
| **D2** | **RP²: no sign, weak degree-1 geometry** | cover |

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H72.1 | **Discrete lift:** RHO3 networks lead with the χ₃ their input realises | leader = r1 in ≥ 80% of fitted RHO3 runs | < 50% |
| H72.2 | Controls: ONEHOT and RHO5 lead with χ₅ | ≥ 80% of fitted runs of both | < 50% |
| H72.3 | **Continuous descent:** with D2 input, axis-trackers build RP², not the cover | R²₁ < 0.5 × the median OMEGA R²₁ **and** balanced sign probe ≤ 0.75, in ≥ 80% of fitted D2 runs | balanced sign probe ≥ 0.95 in ≥ 50% |
| H72.4 | Continuous control: with D1 input the cover is kept | balanced sign probe ≥ 0.95 in ≥ 80% of fitted D1 runs | < 50% |

Anything else is *neither*.

**Guard.** Each encoding counts only with ≥ 3 fitted seeds. H72.3 also needs ≥ 1 fitted OMEGA run.

**Reported without criteria:** the whitened leader, all shares, R²₂ and R²₃.

## What this cannot show

- One architecture and one group pair.
- If D2 networks fail the fit guard, H72.3 gives no verdict. Recovering R from D2(R) is possible (SO(3) has trivial centre) but nonlinear.
- The sphere is unevenly covered (Spike 70), which inflates R²₂ for every encoding equally.

## Commands

```
python -m experiments.spike72 predict
python -m experiments.spike72 run
python -m experiments.spike72 analyse
```
