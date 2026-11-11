# Spike 12: Is the learned circuit invariant when the environment changes?

**Date:** 2026-11-11 · **Status:** pre-registered (hypotheses, metrics and kill criteria written before any run) · **Follows:** Spike 11 (volume does not predict the circuit; post-hoc conjecture H-B′)

## Question

Spike 11's conclusion is inductive: one width, one optimizer, one initialization. Before looking for a general heuristic for *which circuit training builds*, we need to know whether there is a stable object to explain at all. If the network gets 128× wider, or the initialization or optimizer changes, does training still build the same minimal circuits, at the same frequencies? And is there a predictor whose success can be **derived** from the dynamics instead of found in the data?

## Environments

48 elements, drawn with a fixed seed from Spike 11's 128 (w\* = 2, cost 3) and stratified by isomer count. 40 fresh seeds per element and environment. 3,000 full-batch steps; weight decay 0.03; float32.

| Env | Width | Init scale | Optimizer |
|---|---|---|---|
| W8 (baseline) | 8 | 0.5 | AdamW, lr 0.03 |
| W32, W128, W512, W1024 | 32 … 1024 | 0.5 | AdamW, lr 0.03 |
| W8-s0.1, W8-s2 | 8 | 0.1, 2.0 | AdamW, lr 0.03 |
| W8-GD | 8 | 0.5 | plain gradient descent, lr 1.0 |

The output weights are initialized at scale·√(8/H), so the logit stays O(1) as width grows, and W8 reproduces Spike 09/11 exactly.

## Reading the circuit

- **R1 (presence):** every isomer of g whose two units both occur among the hidden units gets equal fractional credit (Spike 11's readout). At large width this credits isomers that are present but unused.
- **R2 (importance):** units are sorted by |output weight|. Take the shortest prefix whose threshold functions determine g, then credit the isomers inside that prefix fractionally. This is the circuit that carries the output.

## Predictors (all fixed in advance, no fitted parameters; scored by rank)

- **S_vol** = log Ω(t1)Ω(t2) (Spike 11).
- **S_imb** = |#t1 − 8| + |#t2 − 8|, where #t is the number of true inputs of t (H-B′, post hoc in Spike 11; now tested on fresh seeds).
- **S_agree** = max over the two units of the agreement of that unit (or its complement) with g on the 16 inputs. **Derivation:** at small initialization tanh is linear. The first-layer gradient of every unit is then proportional to its output weight times the residual-weighted input sum, Σ_x (y_x − ½)·x̃, which is the same direction (g's Chow vector) for all units. So early training pulls every unit toward g's best linear threshold approximation, and the circuit should contain the unit that agrees most with g. The derivation predicts the effect **weakens as initialization grows**, because units then start far from the linear regime.

## Hypotheses and kill criteria

Invariance is measured with the Jensen–Shannon divergence (JS) between the per-element isomer distributions of two environments, computed on disjoint 20-seed halves. The ratio is JS between environments divided by JS between the two halves of the same environment (the noise floor), averaged over elements.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H12.1 | Under R2, the circuit distribution is invariant to width from 8 to 1024 | JS ratio ≤ 1.5 for every adjacent width pair | JS ratio(W8, W1024) ≥ 3 |
| H12.2 | Under R2, it is invariant to the optimizer (W8 vs W8-GD) | ratio ≤ 1.5 | ratio ≥ 3 |
| H12.3 | The init regime moves the predictors as derived: S_agree's within-element Spearman is higher at s0.1 than at s2 | difference ≥ 0.1 | reversed (s2 higher) |
| H12.4 | H-B′ replicates on fresh seeds: at W8, the median within-element Spearman of S_imb is ≥ 0.3 and above S_vol | both | S_imb ≤ S_vol |
| H12.5 | The derived predictor is at least as good as the post-hoc one at W8: S_agree ≥ S_imb | ≥ | S_agree < S_imb − 0.1 |

Between thresholds, the verdict is "neither" and is reported as such.
