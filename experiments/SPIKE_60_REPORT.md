# Spike 60: Is a learned group concept shaped by what its readout distinguishes? (C31′ prospective, with a transformer arm)

**Date:** 2026-11-16 · **Status:** pre-registered (no run) · **Follows:** Spike 58 (P190). There, A₅ read out through 5 points gave χ₄ in 5/5 runs, not the minimal faithful 3-dimensional characters. The post-hoc reformulation C31′ is tested here on new readouts. **Conjectures:** C31 versus C31′; the substrate-relative table (§9.2); the Barrington grading (§10.2).

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

(Not run.)
