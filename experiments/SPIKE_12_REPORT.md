# Spike 12: Is the learned circuit invariant when the environment changes?

**Date:** 2026-11-11 · **Status:** complete. Pre-registered in commit `8df15a6` before any run. The pre-registration did not say which readout H12.3–H12.5 use, so both are reported · **Follows:** Spike 11 (volume does not predict the circuit; post-hoc conjecture H-B′)

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

## Results (`results/spike12.json`, raw counts in `results/spike12_raw/`; about 47 minutes wall time on 4 CPUs)

**Fit and size of the output-carrying core**

| Env | Fit | Mean R2 prefix (units carrying the output) | Fitted nets whose R2 prefix holds no minimal pair |
|---|---|---|---|
| W8 | 99.9% | 3.2 | 62% |
| W32 | 100% | 3.8 | 57% |
| W128 | 100% | 4.3 | 53% |
| W512 | 100% | 5.4 | 51% |
| W1024 | 100% | 6.6 | 50% |
| W8-s0.1 | 96.8% | 3.2 | 59% |
| W8-s2 | 100% | 3.2 | 67% |
| W8-GD | **37%** | 2.8 | 46% |

**Invariance: JS divergence between environments divided by the within-environment noise floor (1 = indistinguishable from reseeding)**

| Pair | R2 ratio | R2 modal agreement | R1 ratio |
|---|---|---|---|
| W8 → W32 | 1.21 | 62% | 1.32 |
| W32 → W128 | 0.97 | 58% | 1.54 |
| W128 → W512 | 1.13 | 54% | 2.02 |
| W512 → W1024 | 1.23 | 59% | 1.36 |
| **W8 → W1024** | **1.62** | 57% | **3.82** |
| W8 → W8-GD (12 elements) | 3.89 | 67% | 9.65 |
| W8 → W8-s0.1 | 1.57 | 58% | 2.01 |
| W8 → W8-s2 | 1.25 | 58% | 0.95 |

**Predictors: median within-element Spearman, R2 (R1 in brackets)**

| Env | S_vol | S_imb | S_agree |
|---|---|---|---|
| W8 | 0.14 (0.17) | 0.28 (0.31) | **0.36 (0.48)** |
| W32 | 0.13 (0.18) | **0.40** (0.39) | 0.38 **(0.49)** |
| W128 | 0.16 (0.20) | 0.32 (0.37) | **0.40 (0.45)** |
| W512 | 0.17 **(0.32)** | 0.28 (0.08) | **0.35** (0.22) |
| W1024 | 0.15 **(0.34)** | 0.29 (0.09) | **0.36** (0.28) |
| W8-s0.1 | 0.09 (0.08) | 0.32 (0.34) | **0.38 (0.40)** |
| W8-s2 | 0.13 (0.14) | 0.29 (0.31) | **0.40 (0.49)** |
| W8-GD | 0.12 (0.16) | **0.28 (0.28)** | 0.19 (0.24) |

## Hypotheses and verdicts

| # | Verdict |
|---|---|
| H12.1 | **Held.** Every adjacent width pair has an R2 ratio ≤ 1.23. End to end (8 → 1024, a 128× change) the ratio is 1.62, well under the kill line of 3. There is slow drift, not a jump. |
| H12.2 | **Broken as registered (ratio 3.89), but confounded.** Plain GD at lr 1.0 fit only 37% of nets. Only 12 elements had runs in both halves, and the comparison conditions on a very selected subset. The learning rate was chosen from a smoke test on one easy function; that was a mistake. |
| H12.3 | **Broken.** S_agree is not higher at small initialization (0.38 at s0.1 vs 0.40 at s2, R2; 0.40 vs 0.49, R1). The derivation's specific prediction failed, so the linear-regime argument is not, or not only, why S_agree works. |
| H12.4 | **Mixed.** Under R1, S_imb = 0.31 ≥ 0.3 and is above S_vol: held. Under R2, 0.28: just under the bar, still above S_vol. The H-B′ direction replicates on fresh seeds; its strength is borderline. |
| H12.5 | **Held.** S_agree ≥ S_imb at W8 under both readouts (0.36 vs 0.28; 0.48 vs 0.31). |

## Findings

**F1. The circuit that carries the output is a stable object across a 128× change in width.** Under R2, going from 8 to 1024 units changes the isomer distribution about as much as reseeding does at each step, with a mild cumulative drift (ratio 1.62 end to end). This answers the question that motivated the spike: at this scale, "which circuit" is a property of the task and the training rule, not of the network size. That makes it a legitimate target for a general law. It does not show such a law exists beyond this setting.

**F2. Bulk versus core: the units that carry no load follow the prior; the units that carry the output do not.** Under R1 (all units present), wide networks look different from narrow ones (ratio 3.82), and the predictor that wins in the bulk at width 512–1024 is *volume* (0.32–0.34). Under R2, volume stays at 0.15 at every width. Most units of a wide network stay close to their random initialization, so their population reflects the prior. The functional core is selected by something else. This reconciles Spike 11's negative result with the volume literature: volume describes the bulk, not the mechanism.

**F3. Target agreement is the best single predictor and is invariant across environments, but its derivation is wrong or incomplete.** S_agree, "the circuit contains the unit that agrees most with g", leads in 6 of 8 environments under R2. Its Spearman is flat across width (0.35–0.40) and initialization scale. The proposed mechanism predicted it would fade at large initialization, and it did not (H12.3 broken). One unverified explanation: AdamW normalizes update sizes, which removes most of the dependence on initialization scale. The one non-Adam environment is exactly where S_agree loses (0.19), but that environment is confounded (H12.2).

**F4. Wider networks build redundant cores.** The output-carrying prefix grows from 3.2 units at width 8 to 6.6 at width 1024, while the minimal circuit inside it stays the same (F1). Training duplicates the circuit rather than changing it.

**F5. About half of the fitted nets compute g with an output-carrying core that contains no minimal pair (it needs three or more of its units).** This holds at every width (50–67%). These nets are excluded from the isomer statistics, so all R2 numbers describe the other half.

## What this says about "deterministic or inductive"

Everything here is still inductive: seeded, reproducible measurements over a finite set of environments. What changed is that the object is now known to be stable under the environment changes tested (F1). The best predictor explains a moderate share of the variation (rank correlation about 0.4), so the choice of circuit is neither deterministic given the task nor explained by any one heuristic tested. The one attempt to *derive* a predictor from the dynamics failed its own test (H12.3). The next step is to derive the selection from the optimizer's dynamics, with GD done properly so that Adam's normalization can be separated out.

## Gaps

- GD needs a learning rate and a number of steps that fit, chosen on a calibration set of elements disjoint from the 48 scored.
- 40 seeds per element: the noise floor is large (within-environment JS of 0.10–0.17), so small real changes cannot be seen. A ratio near 1 means "no change detectable at this sample size".
- One task family (4-input, w\* = 2), tanh, full batch. "Across domains" is not tested at all.
- The output-scale rule (√(8/H)) is one parametrization; mean-field scaling (1/H) could change F2.
