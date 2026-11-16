# Spike 60: Is a learned group concept shaped by what its readout distinguishes? (C31′ prospective, with a transformer arm)

**Date:** 2026-11-16 · **Status:** complete (pre-registered in 5b097d0; results below) · **Follows:** Spike 58 (P190). There, A₅ read out through 5 points gave χ₄ in 5/5 runs, not the minimal faithful 3-dimensional characters. The post-hoc reformulation C31′ is tested here on new readouts. **Conjectures:** C31 versus C31′; the substrate-relative table (§9.2); the Barrington grading (§10.2).

## Hypotheses being contrasted

- **C31 (economy).** The learned state geometry is a minimal faithful irreducible representation of the group.
- **C31′ (readout).** The geometry is the permutation representation of the group on the cosets G/H that the output distinguishes, minus the trivial part. Its predicted Gram is K(g, h) = χ_perm(g⁻¹h) − 1, where χ_perm(x) is the number of cosets fixed by x.

## Automata (states = group elements; letter p acts on the right, g ↦ g∘p; output = one-hot of the left coset gH)

| Name | Group, generators | H (readout) | Cosets | C31′ predicts (perm − 1) | C31 predicts |
|---|---|---|---|---|---|
| A5_5 | A₅; (0 1 2), (0 1 2 3 4) | stabiliser of 0 (A₄) | 5 | χ₄ | χ₃ or χ₃′ |
| A5_6 | A₅; same | normaliser of ⟨(0 1 2 3 4)⟩ (D₅, order 10) | 6 | **χ₅** | χ₃ or χ₃′ |
| S4_4 | S₄; (0 1), (0 1 2 3) | stabiliser of 0 (S₃) | 4 | standard (3-dim) | standard or standard ⊗ sign |
| S4_6 | S₄; same | stabiliser of the pair {0, 1} (order 4) | 6 | standard + χ₂ (composite) | standard or standard ⊗ sign |

A5_6 and S4_6 are new readouts, where the two conjectures disagree. A5_5 replicates Spike 58. S4_4 is a control where they agree. In every case H is core-free, so the minimal automaton is the whole group (checked by Moore minimisation in code).

## Architectures

**GRU (recurrent).**
- Hidden size 64, embedding 16.
- Adam with lr 0.003, **cosine-decayed to 0** over 6,000 steps. This is changed from Spike 58 to remove the late-training collapse seen there.
- Fit guard: accuracy ≥ 0.99 on 500 strings of length 100.

**Transformer (constant depth).**
- Causal, pre-LayerNorm, 2 layers, model width 64, 4 heads, feed-forward 128, learned positions up to 30.
- AdamW with lr 0.001, cosine to 0, 6,000 steps.
- The hidden state is the final-layer residual at each position.
- Fit guard: accuracy ≥ 0.99 on 500 strings of length 30 (the training length).

**Shared.**
- Random strings of length 30, batch 64, binary cross-entropy on the output bits.
- Seeds: 5 per (automaton, architecture), 6,000 + 10·index + seed (+ 500 for the transformer).

## Measurements

These use 400 strings of length 30 for both architectures, steps 5–29.

**Centroids and Gram.** For each group element, the centroid hidden state, centred and normalised; G is their cosine Gram matrix. Each candidate is scored by the Spearman correlation of the off-diagonal entries of G with its predicted kernel:
- ρ_readout, for C31′'s K;
- ρ_minfaith, the larger over C31's minimal faithful irreducibles;
- each single nontrivial irreducible (reported).

**Closure (GRU only, replicating P188).**
- Linear-probe accuracy and determinism.
- Interchange-intervention success: the donor hidden state comes from another string in a different state, and the remaining 20 outputs must follow the automaton from that state.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H60.1 | **C31′ beats C31 where they disagree** (GRU; A5_6 and S4_6) | ρ_readout > ρ_minfaith in ≥ 80% of fitted runs | < 50% |
| H60.2 | **Sharp prediction:** GRU A5_6 has the character of χ₅ | χ₅ is the best single irreducible in ≥ 80% of fitted runs | χ₃ or χ₃′ best in ≥ 50% |
| H60.3 | C31′ fits strongly (GRU, all four automata) | ρ_readout ≥ 0.50 in ≥ 80% of fitted runs | < 50% |
| H60.4 | C31′ is substrate-independent (transformer; A5_6 and S4_6) | ρ_readout > ρ_minfaith in ≥ 80% of fitted transformer runs (needs ≥ 3, else no verdict) | < 50% |
| H60.5 | **Barrington grading:** a constant-depth transformer fits the solvable group, not the non-solvable one | transformer fit rate S₄ (10 runs) ≥ 0.6 **and** A₅ (10 runs) ≤ 0.2 | A₅ fit rate ≥ S₄ fit rate |
| H60.6 | Closure and causal power replicate (GRU) | probe ≥ 0.99, determinism ≥ 0.99 and intervention ≥ 0.98 in ≥ 80% of fitted runs | < 50% |

Anything else is *neither*.

**Guard.** For GRU hypotheses, an automaton contributes only with ≥ 3 fitted seeds.

**Reported without criteria:**
- all single-irreducible scores;
- steps to 0.99 by automaton and architecture;
- transformer probe accuracy.

## What this cannot show

- Two groups and four readouts.
- Spearman correlation against predicted kernels, not a full decomposition of the Gram into isotypic components.
- One transformer size. The Barrington prediction is asymptotic in sequence length, and here the length is fixed at 30.

## Commands

```
python -m experiments.spike60 run gru
python -m experiments.spike60 run tf
python -m experiments.spike60 analyse
```

## Results

`experiments/results/spike60.json`; per-run outputs in `spike60_raw/`.

**Fitted runs.**
- GRU: A5_5 5/5, A5_6 3/5 (the other two reached 0.885 and 0.98), S4_4 5/5, S4_6 5/5. The cosine schedule removed Spike 58's late-training collapse.
- Transformer: **0/20** fit at the training length (0.87–0.91 accuracy for both groups); its probes decode the group element at only 0.08–0.27.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H60.1 | ρ_readout > ρ_minfaith in 3/8 runs on the discriminating cases (A5_6: 3/3; S4_6: 0/5) | ≥ 80% held, < 50% broken | **BROKEN** |
| H60.2 | A5_6: χ₅ best in 3/3 fitted runs (and in 5/5 including unfitted); χ₃ and χ₃′ best in 0 | ≥ 80% held | **HELD** |
| H60.3 | ρ_readout ≥ 0.50 in 10/18 fitted GRU runs | ≥ 80% held, < 50% broken | **NEITHER** |
| H60.4 | no fitted transformer runs | guard | **NO VERDICT** |
| H60.5 | transformer fit rate S₄ 0.0, A₅ 0.0 | S₄ ≥ 0.6 and A₅ ≤ 0.2 held; A₅ ≥ S₄ broken | **BROKEN** |
| H60.6 | probe, determinism and intervention criteria met in 17/18 fitted GRU runs | ≥ 80% | **HELD** |

**Median Spearman, readout vs minimal faithful (GRU):**

| Case | Readout | Minimal faithful |
|---|---|---|
| A5_5 | 0.58 | -0.02 |
| A5_6 | 0.35 | -0.21 |
| S4_4 | 0.63 | 0.63 (identical by construction) |
| S4_6 | 0.38 | **0.54** |

**Reading:**
- **The sharp prospective prediction of C31′ held.** A₅ read out through 6 points gives χ₅, the readout's representation. The minimal faithful 3-dimensional characters are *anti*-correlated (−0.16 to −0.25). Together with A5_5 (χ₄, 5/5 here and 5/5 in Spike 58), the minimal-faithful economy law (C31) is refuted for A₅ under two independent readouts.
- **C31′ as stated is also refuted, by S4_6.** There the readout's representation is standard ⊕ χ₂, but every network uses the standard representation alone: standard 0.47–0.59, χ₂ ≈ 0, composite 0.36–0.41.
- **χ₂ is the unfaithful constituent:** its kernel is the Klein group V₄, so it cannot distinguish elements of V₄.
- **Synthesis, exploratory and post hoc (conjecture C31″).** The learned geometry is the *faithful part of the readout's permutation representation*: the irreducible constituents of G's permutation action on what the output distinguishes, keeping those that are faithful. It fits all 18 fitted GRU runs:
  - A5_5: χ₄;
  - A5_6: χ₅;
  - S4_4 and S4_6: standard (χ₂ dropped).

  Both earlier laws are special cases. It must be tested prospectively on readouts whose permutation representation contains several faithful constituents.
- **Transformers.** A 2-layer transformer learned neither group within 6,000 steps at length 30, so the Barrington contrast (solvable versus non-solvable) did not appear: both failed. This agrees with Liu et al. that constant-depth shortcuts are hard to *find* by training even when they exist for solvable groups. It is not evidence for the grading.
- **Construction cost** (GRU median steps to 0.99): S4_4 300 < S4_6 500 < A5_5 700 < A5_6 3150. The non-solvable group costs more under both readouts, and the 6-point readouts cost more than the point-stabiliser ones. Exploratory.
