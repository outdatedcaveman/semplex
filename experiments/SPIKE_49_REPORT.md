# Spike 49: Do trained nets realize the consensus of minimum circuits?

**Date:** 2026-11-15 · **Status:** complete (pre-registered in 2d6130e; one deviation recorded before any verdict; results below) · **Follows:** Spike 48 (the Occam pull is 0.72 at n = 8 and 0.65 at n = 10 with 8 labels per dimension, 0.94 with 75% of inputs seen). **Gaps:** A6 (scale), A3 (mechanism), A4 (one predictor).

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

`experiments/results/spike49.json`; raw outputs in `spike49_raw/`. Every task compiled; 99.7–100% of nets fit; at most 0.4% of forcing queries timed out. All cells pass the guards.

| Cell | n | seen | fraction forced | net adherence | kernel adherence | `sides_forced` | net vs majority on unforced | forced value = true label | net accuracy on unforced | forced pairs |
|---|---|---|---|---|---|---|---|---|---|---|
| n8_s48 | 8 | 48 | 0.172 | 0.981 | 0.952 | 0.827 | 0.848 | 0.973 | 0.818 | 20602 |
| n8_s96 | 8 | 96 | 0.570 | 0.979 | 0.920 | 0.875 | 0.850 | 0.997 | 0.836 | 68210 |
| n8_s144 | 8 | 144 | 0.807 | 0.986 | 0.867 | 0.947 | 0.861 | 0.999 | 0.871 | 90107 |
| n10_s80 | 10 | 80 | 0.276 | 0.991 | 0.971 | 0.816 | 0.860 | 0.988 | 0.842 | 16530 |

### Verdicts

- **H49.1: held.** On forced inputs, nets output the forced value 97.9–99.1% of the time in every cell (bar 0.95).
- **H49.2: held.** That rate varies by 0.011 across input sizes and sample sizes (bar 0.04), while the fraction of forced inputs varies from 17% to 81%.
- **H49.3: held.** Where a net leaves its kernel on a forced input, it goes to the forced value 82–95% of the time (bar 0.80).
- **H49.4: neither.** The net adheres more than the kernel in every cell, by +0.029, +0.059, +0.119 and +0.020. The bar was +0.05 in every cell; two cells miss it.
- **C22: not fully supported under the pre-registered rule,** which required H49.4. Its first two parts (adherence, and independence of n and sample size) held.

### Reading

1. **The consensus law holds as a description.** A trained net almost never contradicts what every minimum circuit agrees on: 2% of the time, the same at 8 and 10 inputs and from 48 to 144 seen inputs.
2. **It explains Spike 48's trend.** The pull shrinks with n at fixed labels per dimension because fewer inputs are forced (17–28% in the sparse cells against 81% with 144 seen), not because nets follow forced values less.
3. **But forced inputs are also the easy ones.** The forced value is the true label 97–99.9% of the time, and the kernel gets 87–97% of them right too. In the sparse cells the net's edge over the kernel on forced inputs is only 2–3 points. So "nets follow the consensus" is partly "nets and kernels both get determined inputs right". The law distinguishes the net from the kernel clearly only when data are plentiful (+12 points at 144 seen).
4. **Unforced inputs are not noise.** Nets agree with the majority of sampled minimum circuits on 85–86% of them and are right on 82–87%. Minimum circuits still carry information there, which the law as stated does not capture.

**Limits.** Forcing is relative to |w| ≤ 4 and to layered nets of the minimum cost. Two-unit targets only. 120 sampled held-out inputs per task (112 in `n8_s144`).

**Next.** A graded version: replace "forced or not" by the fraction of minimum circuits giving each value at an input, and test whether the net's output probability tracks it. That would cover point 4 and give a single predictor (gap A4).
