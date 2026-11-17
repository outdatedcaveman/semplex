# Spike 63: Can a deeper transformer learn group automata, and does it obey the Barrington split and the sufficiency law?

**Date:** 2026-11-17 · **Status:** complete (pre-registered in this file's first commit; results below) · **Follows:** Spike 60 (P194: a 2-layer transformer learned neither S₄ nor A₅). **Conjectures:** substrate-relative periodic table (`charter/FOUNDATIONS.md` §9.2), Barrington grading (§10.2), C31‴ (§11.4).

## Design

- **Automata:** S4_4 and A5_5 of Spike 60 (identical definitions).
- **Model:** causal pre-LayerNorm transformer, **4 layers**, width 64, 4 heads, feed-forward 256, learned positions up to 30.
- **Optimiser:** AdamW, lr 0.001 cosine to 0 after 500 warm-up steps, 15,000 steps, batch 64.
- **Length curriculum:** training string length rises linearly from 6 to 30 over the first 7,500 steps, then stays at 30. Loss is on every position.
- **Seeds:** 3 per automaton (6,300 + 10·index + seed).
- **Fit guard:** output accuracy ≥ 0.99 on 500 strings of length 30.
- **Measurements:** as Spike 60 (probe accuracy, best irreducible, readout and minimal-faithful scores, steps to 0.99), from the final-layer residual.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H63.1 | A 4-layer transformer with curriculum learns the solvable group | S4_4 fits in ≥ 2 of 3 seeds | 0 of 3 |
| H63.2 | **Barrington split:** the solvable group is learned more readily than the non-solvable one | S₄ fit rate − A₅ fit rate ≥ 2/3 | A₅ fit rate ≥ S₄ fit rate |
| H63.3 | **C31‴ is substrate-independent** | in fitted runs (≥ 2 needed), the best irreducible is the C31‴ prediction (S4_4: standard; A5_5: χ₄) in all | in none |

Anything else is *neither*.

## What this cannot show

- Fixed length (30): Barrington's separation is asymptotic in length, so failure on A₅ here is suggestive, not a lower bound.
- One width and one budget.

## Commands

```
python -m experiments.spike63 run
python -m experiments.spike63 analyse
```

## Results

`experiments/results/spike63.json`.

| Automaton | Seed | Fit | Steps to 0.99 | Probe | Best irreducible | Readout ρ |
|---|---|---|---|---|---|---|
| S4_4 | 6300 | 0.994 | 10475 | 0.48 | std | 0.34 |
| S4_4 | 6301 | 0.972 | -1 | 0.38 | std | 0.33 |
| S4_4 | 6302 | 0.987 | 13225 | 0.41 | std | 0.34 |
| A5_5 | 6310 | 0.991 | 11150 | 0.13 | chi4 | 0.30 |
| A5_5 | 6311 | 0.976 | -1 | 0.14 | chi4 | 0.30 |
| A5_5 | 6312 | 0.978 | -1 | 0.11 | chi4 | 0.30 |

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H63.1 | S4_4 fit in 1/3 (the other two reached 0.972 and 0.987) | ≥ 2 held, 0 broken | **NEITHER** |
| H63.2 | fit rate S₄ 1/3 = A₅ 1/3 | difference ≥ 2/3 held; A₅ ≥ S₄ broken | **BROKEN** |
| H63.3 | both fitted runs: best irreducible as predicted (standard; χ₄); all 6 runs show it | all held | **HELD** |

**Reading:**
- **A deeper transformer with a length curriculum learns both groups** at length 30, barely (1/3 each). No solvable/non-solvable gap appears at this length, consistent with Barrington's separation being asymptotic.
- **Its state geometry is the same as the recurrent networks':** standard for S₄, χ₄ for A₅, i.e. the readout/predictive-state character.
- **Yet the full group element is decodable only partly** (probe 0.11–0.48, against 1.0 for GRUs). The transformer realises the predictive geometry without an explicit closed macrostate. Its outputs are computed by other routes (shortcuts, in Liu et al.'s sense).
- **So the geometry law is substrate-independent across these two architectures, while closure is not:** the recurrent net builds the minimal automaton; the transformer builds its predictive shadow.
