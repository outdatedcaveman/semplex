# Spike 71: Which constituent does a recurrent learner select? Predictive energy versus AGF versus orbit size, with emergence order

**Date:** 2026-11-17 · **Status:** complete (pre-registered with predictions in 1b5a15d; results below) · **Follows:** Spike 69 (P201, P202) and the prior-art reading of 2026-11-17 (`charter/LITERATURE_REVIEW.md`).

That reading fixes the competitors:
- Kunin et al. (AGF, arXiv:2506.06489) and Marchetti et al. (arXiv:2602.03655): in feedforward networks, irreps are learned one at a time in order of the utility ‖x̂[ρ]‖^{k+1}/(C_ρ n_ρ)^{(k−1)/2}.
- Wu et al. (arXiv:2410.07476): irrep usage follows the minimum ρ-set (orbit) size.
- arXiv:2610.05292: the centroid geometry is not invariant under reparametrisation.

## Three predictors, all computed from the automaton before training (`python -m experiments.spike71 predict`)

1. **Predictive energy (C37, ours).** The top isotypic share of the predictive kernel K (horizon 30), as in Spike 69. It counts as a unique prediction only if it is ≥ 1.5× the second; otherwise it is a tie.

   For coset readouts the share of a constituent is ∝ m²C, where m is its multiplicity in the permutation module and C = 2 for a merged conjugate pair (equal-energy lemma, `charter/FOUNDATIONS.md` §11.4). **Multiplicity decides.**
2. **AGF utility (extrapolated).** The output functions generate a left-invariant module, whose ρ-part has dimension m n C. We take ‖x̂[ρ]‖²_op ∝ share/(m²C), and use the k = 2 utility (‖x̂‖_op²)^{3/2}/(C n)^{1/2}.

   For coset readouts the operator norms are equal for every constituent, so **AGF predicts the lowest C·n**. The prediction is the set of constituents within 2% of the maximum.
3. **Minimum orbit size (Wu et al.).** For each constituent present, the minimum over subgroups K with a nonzero K-fixed vector of the index [G : K]. The prediction is the set of minimisers.

| Automaton | Readout (H) | Energy (C37) | AGF | Orbit | Discriminates |
|---|---|---|---|---|---|
| S4_12 | ⟨(01)⟩, 12 cosets: 1 + χ₂ + 2 std + std⊗sign | **std (m = 2)** | χ₂ | χ₂ | energy vs AGF/orbit |
| S4_12b | ⟨(01)(23)⟩: sign + 2χ₂ + std + std⊗sign | **χ₂ (m = 2)** | sign | sign | energy vs AGF/orbit |
| A5_20 | C₃, 20 cosets (Zhang and Li's stage): χ₃ + χ₃′ + 2χ₄ + χ₅ | **χ₄ (m = 2)** | χ₃ or χ₃′ | χ₄ | energy/orbit vs AGF |
| S4_8 | ⟨(012)⟩: sign + std + std⊗sign | tie | sign | sign | tie-break |
| A5_10 | S₃: χ₄ + χ₅ | tie | χ₄ | χ₄ | tie-break |
| D4_4r | vertex stabiliser | tie | 1-dim r0 | r0 | tie-break |
| D4_4e | edge reflection | tie | 1-dim r3 | r3 | tie-break |
| A4_4 | point stabiliser: χ₃ | χ₃ | χ₃ | χ₃ | control (all agree) |
| Z11_03 | [c ∈ {0, 3}] | k = ±4 (share 0.53) | same | all | energy vs smooth circle k = ±1 |
| Z10_05 | [c ∈ {0, 1, 5}] | k = ±2 (unfaithful, 0.86) | same | k = 5 | energy vs smooth circle |
| Z12_06 | [c ∈ {0, 4, 6}] | k = 6 (unfaithful, 0.65) | same | same | energy vs smooth circle |

S4_8, A5_10 and S4_12b replicate Spike 62 readouts, now with an identity letter added. Their earlier outcomes were S4_8 → sign 5/5, A5_10 → χ₄ (2 fitted runs) and S4_12b → χ₂ 4/5. So those three predictions are partly informed by data. The other eight automata are new.

## Training and measurement

As Spike 69:
- GRU with hidden size 64, Adam with lr 0.003 cosine to 0, 6,000 steps, length 30, batch 64;
- the letters are the generators plus an identity letter;
- 5 seeds per automaton, seed 7,100 + 10·index + seed;
- fit guard: ≥ 0.99 at length 100.

**Geometry is recorded during training**, at steps 50–2,000 every 50 and then every 500. It is measured on a fixed set of 400 strings, steps 5–29, as each constituent's isotypic share of the double-centred centroid Gram, in two forms:
- **cosine:** centroids centred and normalised;
- **whitened:** centroids multiplied by the inverse square root of the pooled within-element covariance. This is invariant under any invertible linear reparametrisation of the hidden state, which answers arXiv:2610.05292, Prop. 1.

**Leaders:**
- **final leader:** the largest share at step 6,000;
- **first leader:** the largest share at the first checkpoint where the shares depart from the regular (identity-like) shares by τ ≥ 0.15.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H71.1 | Predictive energy predicts the final leader (unique cases) | ≥ 80% of fitted runs | < 50% |
| H71.2 | AGF predicts the **first** leader (all automata) | ≥ 80% | < 50% |
| H71.3 | Minimum orbit size predicts the final leader | ≥ 80% | < 50% |
| H71.4 | **Where energy and AGF disagree** (S4_12, S4_12b, A5_20), energy wins | final leader = energy prediction in ≥ 80% | final leader in the AGF set in ≥ 50% |
| H71.5 | The first leader persists (first = final) | ≥ 80% | < 50% |
| H71.6 | The leader is reparametrisation-robust (whitened = cosine) | ≥ 80% | < 50% |
| H71.7 | Energy ties are broken toward the lowest C·n (the AGF set) | ≥ 80% of fitted tie runs | < 50% |
| H71.8 | **Cyclic:** predictive energy beats the smooth k = ±1 circle (Z11, Z10, Z12) | energy prediction is the final leader in ≥ 80% | the smoothest faithful character leads in ≥ 50% |

Anything else is *neither*.

**Guards.**
- An automaton counts only with ≥ 3 fitted seeds.
- H71.1–H71.3 need ≥ 4 qualifying automata; H71.4, H71.7 and H71.8 need ≥ 2.

**Reported without criteria:** full share trajectories, the step of first structure, and per-automaton tables.

## What this cannot show

- One recurrent architecture.
- The AGF extrapolation is ours: AGF is proved for two-layer feedforward networks from small initialisation, and a GRU at default initialisation is outside its assumptions. A failure of H71.2 refutes our extrapolation, not their theorem.
- The leader is a one-constituent summary of a mixture.

## Commands

```
python -m experiments.spike71 predict
python -m experiments.spike71 run
python -m experiments.spike71 analyse
```

## Results

`experiments/results/spike71.json`; per-run trajectories in `spike71_raw/`.

**Fitted runs.**
- **A₅ did not fit:** A5_10 reached 0.91–0.92 and A5_20 0.95–0.96, so both are excluded.
- S4_12: 3/5 fitted. S4_8: 4/5. Z11_03: 4/5. All others: 5/5.
- Nine automata qualify.

| Automaton | Energy | AGF | Orbit | Final leader (fitted runs) | First leader |
|---|---|---|---|---|---|
| **S4_12** | std (m = 2) | χ₂ | χ₂ | **std 3/3** | std⊗sign 3/3 |
| **S4_12b** | χ₂ (m = 2) | sign | sign | **χ₂ 5/5** | std⊗sign 5/5 |
| S4_8 | tie | sign | sign | std 3/4, std⊗sign 1/4 | std⊗sign 4/4 |
| D4_4r | tie | r0 (1-dim) | r0 | r0 4/5, 2-dim 1/5 | mixed |
| D4_4e | tie | r3 (1-dim) | r3 | 2-dim 4/5, r3 1/5 | 2-dim 5/5 |
| A4_4 | χ₃ | χ₃ | χ₃ | χ₃ 5/5 | χ₃ 5/5 |
| Z11_03 | k = ±4 | k = ±4 | all | **k = ±1 3/4**, k = ±3 1/4 | k = ±1 4/4 |
| Z10_05 | k = ±2 (unfaithful) | same | k = 5 | **k = ±2 5/5** | k = ±1 5/5 |
| Z12_06 | k = 6 | same | same | **k = ±2 5/5** (third by energy) | k = ±1 4/5 |
| A5_10 (unfitted) | tie | χ₄ | χ₄ | χ₄ 5/5 (unfitted) | — |
| A5_20 (unfitted) | χ₄ (m = 2) | χ₃ / χ₃′ | χ₄ | χ₄ 3/5, χ₃ 2/5 (unfitted) | — |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H71.1 | energy prediction = final leader in 67% of fitted unique runs | ≥ 80% held, < 50% broken | **NEITHER** |
| H71.2 | AGF prediction = first leader in 15% | ≥ 80% held, < 50% broken | **BROKEN** |
| H71.3 | minimum orbit predicts the final leader in 34% | ≥ 80% held, < 50% broken | **BROKEN** |
| H71.4 | **energy vs AGF where they disagree** (S4_12, S4_12b): energy wins 8/8 (100%), AGF 0% | ≥ 80% held | **HELD** |
| H71.5 | first leader = final leader in 39% | ≥ 80% held, < 50% broken | **BROKEN** |
| H71.6 | whitened leader = cosine leader in 80% | ≥ 80% | **HELD** |
| H71.7 | energy ties broken to the lowest C·n in 36% | ≥ 80% held, < 50% broken | **BROKEN** |
| H71.8 | cyclic: energy 36%, smooth k = ±1 circle 21% | energy ≥ 80% held; smooth ≥ 50% broken | **NEITHER** |

**Reading:**
- **Multiplicity decides, and dimension does not.** These are the decisive cases. When a readout's permutation module contains a constituent twice, networks lead with it in 8/8 runs: std in S₄ on 12 cosets, χ₂ in S₄ on cosets of ⟨(01)(23)⟩. This happens against both the low-dimension preference of AGF and the minimum-orbit predictor of Wu et al. Energy ∝ m² (the equal-energy lemma) is the right currency, and dimension discounts are not. In the two A₅ cases that did not fit, the same holds in the majority of runs (χ₄, m = 2, 3/5), but they do not count.
- **The geometry is not an artefact of the metric.** The leader is the same under a whitening that removes any invertible linear reparametrisation in 80% of runs, which answers arXiv:2610.05292's objection.
- **Learning passes through stages.** The first structured geometry is usually *not* the final one (39% persist). S₄ networks start with std⊗sign and end with the energetic constituent. Cyclic networks start with the smooth k = ±1 circle and, in Z10 and Z12, leave it later. This is the recurrent counterpart of Zhang & Li's coset stages. AGF's ordering does not describe the first stage either (15%).
- **Ties are not broken toward low dimension.** S4_8 now leads with std, where Spike 62, *without* an identity letter, gave sign 5/5. D4's two coset readouts break oppositely: vertex stabiliser → 1-dim, edge reflection → 2-dim. Ties remain decided by the letters, as in Spike 69, and no registered rule predicts them.
- **Cyclic counters keep returning to the circle.**
  - Z11 (all characters faithful) ends at k = ±1 against an energy prediction of k = ±4, as Z7 did in Spike 69.
  - Z10 follows energy to the unfaithful k = ±2.
  - Z12 ends at k = ±2, which is neither the energy prediction (k = 6) nor the circle.

  A post-hoc pattern: when the energetic character is faithful but rough (prime n), the smooth circle wins. When an unfaithful character carries most of the energy, a coarse low-frequency character wins. A "smooth, energetic, coarse" trade-off is not yet a law.

**Status of the shape law after Spike 71.** The leading constituent tracks multiplicity-weighted predictive energy in all non-abelian cases with a unique prediction: A4_4, S4_12 and S4_12b here, A4_6 in Spike 69. Ties and cyclic counters are decided by something else: the letters, with a pull toward smooth low-frequency characters.
