# Spike 63: Can a deeper transformer learn group automata, and does it obey the Barrington split and the sufficiency law?

**Date:** 2026-11-17 · **Status:** pre-registered (no run) · **Follows:** Spike 60 (P194: a 2-layer transformer learned neither S₄ nor A₅). **Conjectures:** substrate-relative periodic table (`charter/FOUNDATIONS.md` §9.2), Barrington grading (§10.2), C31‴ (§11.4).

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

(Not run.)
