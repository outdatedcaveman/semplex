# Spike 49: Do trained nets realize the consensus of minimum circuits?

**Date:** 2026-11-15 · **Status:** pre-registered (no runs yet) · **Follows:** Spike 48 (the Occam pull is 0.72 at n = 8 and 0.65 at n = 10 with 8 labels per dimension, 0.94 with 75% of inputs seen). **Gaps:** A6 (scale), A3 (mechanism), A4 (one predictor).

## Where the hypothesis comes from (exploratory, on Spike 48's data)

After Spike 48's verdicts, I split its held-out inputs by whether the 5 sampled minimum-cost completions agree. Where they agree, the net outputs the agreed value on 96.1% (n = 8, 64 seen), 96.5% (n = 10) and 98.8% (n = 8, 192 seen) of inputs. Where they split, the net agrees with their majority on only 71–72%. Per task, the mean unanimity of the completions correlates with the pull at Spearman 0.78 (pooled). This is post hoc and uses 5 samples as a stand-in for "all minimum circuits". It is the source of the conjecture, not evidence for it.

## Conjecture C22 (consensus law)

Call a held-out input **forced** if every minimum-cost circuit consistent with the seen labels gives it the same value. Then:

1. On forced inputs, a trained net outputs the forced value, at a rate that does not depend on the input size or on how many inputs were seen.
2. On unforced inputs, minimum circuits do not predict the net.
3. The decline of the Occam pull with n in Spike 48 is a decline in the fraction of forced inputs, not in the net's adherence to them.

## Design

- **Cells** (fresh targets and care sets; seeds 4,900 + cell index for targets, 4,950 + cell index for care sets):

| Cell | n | Seen | Seeds per task |
|---|---|---|---|
| `n8_s48` | 8 | 48 | 10 |
| `n8_s96` | 8 | 96 | 10 |
| `n8_s144` | 8 | 144 | 10 |
| `n10_s80` | 10 | 80 | 5 |

- **Targets, nets, kernel:** as Spike 48 (two-unit targets certified not threshold; `spike36.train`, tanh width 8; `spike36.ntk` ridge). 100 targets per cell.
- **Minimum cost:** `compile_partial` with |w| ≤ 4.
- **Forced inputs, computed exactly for the stated weight bound.** For each task, 120 held-out inputs are drawn at random (seed 4,990 + cell index). 5 minimum-cost nets are sampled. An input on which they disagree is unforced. For an input on which they agree, the solver is asked for a minimum-cost net (same shape, |w| ≤ 4) that fits the seen labels and gives the *opposite* value there: `unsat` means forced, `sat` means unforced, and a timeout (5 s) is recorded as unknown and excluded.
- **Measures**, over fitted nets and the sampled held-out inputs:
  - `adherence` = fraction of forced inputs on which the net outputs the forced value;
  - `kernel_adherence` = the same for the kernel prediction;
  - `sides_forced` = among forced inputs where net ≠ kernel, the fraction where the net has the forced value;
  - `majority_agreement` = on unforced inputs, agreement of the net with the majority of the 5 samples;
  - the fraction of inputs that are forced.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H49.1 | Nets output the forced value | `adherence` ≥ 0.95 in every cell | < 0.90 in any cell |
| H49.2 | The rate does not depend on n or sample size | max − min of `adherence` across cells ≤ 0.04 | > 0.08 |
| H49.3 | Where the net leaves the kernel on a forced input, it goes to the forced value | `sides_forced` ≥ 0.80 in every cell | < 0.65 in any cell |
| H49.4 | This is not just the kernel agreeing too | `adherence` − `kernel_adherence` ≥ 0.05 in every cell | ≤ 0 in any cell |

Anything else is *neither*. C22 is supported if H49.1, H49.3 and H49.4 hold; refuted if H49.1 or H49.3 is broken.

**Guards.** A cell gives no verdict if fewer than 90% of nets fit, fewer than 90% of tasks compile, more than 10% of the forcing queries are unknown, or it has fewer than 2,000 forced (net, input) pairs.

**Scope stated in advance.** "Every minimum circuit" means every layered threshold net of the minimum cost with |w| ≤ 4. P170 found that raising the cap to 16 changes the minimum cost in about 2% of such tasks.

**Deviation recorded before any verdict (2026-11-15).** The cell `n8_s144` has only 112 held-out inputs, fewer than the 120 the design samples, and its forcing run stopped with an error before producing any output. The code now samples min(120, number held out), so that cell uses all 112. No other cell is affected and no criterion changed.

## Commands

```
python -m experiments.spike49 tasks
python -m experiments.spike49 forced CELL
python -m experiments.spike49 nets CELL
python -m experiments.spike49 analyse
```

## Results

(To be filled after the runs.)
