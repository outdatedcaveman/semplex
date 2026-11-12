# Abductive hypotheses: what rule decides which mechanism training builds?

**Status:** working document, started 2026-11-12. Each candidate is an *inference to the best explanation* of the observations below. None is established. Each must make a prediction that the others do not, and is retired when that prediction fails.

## 1. The observations to explain

| # | Observation | Source | Status |
|---|---|---|---|
| O1 | On underspecified tasks, training picks a table-cheapest completion 88–96% of the time (chance 25–55%) | S09 F1, S10c | EMPIRICAL, strong |
| O2 | Among the minimal circuits of one function, prior weight-space volume barely predicts which one training builds | S11 (pre-registered) | EMPIRICAL |
| O3 | The output-carrying core is invariant, up to reseeding noise, across widths 8 → 1024 | S12 F1 (pre-registered) | EMPIRICAL |
| O4 | In wide networks the *bulk* of units follows the prior volume; the *core* does not | S12 F2 | EMPIRICAL (post hoc contrast) |
| O5 | "The core contains the unit that agrees most with the target" is the best predictor tested (ρ ≈ 0.4), flat across width and initialization scale under AdamW | S12 F3 | EMPIRICAL |
| O6 | That predictor's linear-regime derivation fails: no dependence on initialization scale | S12 H12.3 | REFUTED derivation |
| O7 | Training prefers units that split the inputs unevenly | S11 F3, S12 H12.4 | EMPIRICAL, borderline |
| O8 | Learning rules that fit equally well differ in completion bias | S10c F3 | EMPIRICAL |
| O9 | Wider networks duplicate the core instead of changing it | S12 F4 | EMPIRICAL |
| O10 | About half of the nets use a core with no minimal pair inside | S12 F5 | EMPIRICAL |

A good explanation must cover O1–O3 together: why the *function* follows simplicity, why the *circuit* does not follow volume, and why the circuit does not depend on size.

## 2. Candidate principles

### A1. Greedy residual fitting (incremental, "matching pursuit")
Training builds the circuit one unit at a time. The first unit to specialize is the threshold function that best fits the target on its own; later units fit what is left.
- **Explains:** O5 directly. O3, because the order of specialization depends on the task, not on width. O7, if the best single-unit fits of these functions are unbalanced (for an AND-like target, the best single threshold is itself AND-like).
- **Distinct prediction:** the core contains the *globally* best-agreeing threshold function t\* far more often than the share of isomers that contain it. t\* also appears first in time.
- **Prior art:** saddle-to-saddle and incremental learning (arXiv:2512.20607, 2302.11055, 2605.27097). Known at the level of rank or features; not tested against an exact list of circuit isomers.
- **Tension:** O6. The usual derivation needs small initialization, and the effect does not fade at large initialization under AdamW.

### A2. Optimizer-geometry margin maximization
Steepest descent with respect to a norm converges, in direction, to a maximum-margin solution *in that norm*. GD maximizes an ℓ2 margin; Adam, which behaves like sign descent, maximizes an ℓ∞ margin. The circuit chosen is the isomer whose units can be realized with the largest margin in the optimizer's own geometry.
- **Explains:** O3, because mean-field and wide-network limits of margin maximization are width-independent once width ≥ w\*. O8, because a learning rule is a geometry, so different rules imply different margins and different choices. O1, if cheap completions have larger margins. O6, because under Adam the ℓ∞ geometry makes the selection scale-free, so no dependence on initialization is expected.
- **Distinct prediction:** the ℓ∞ margin predictor wins under AdamW; the ℓ2 margin predictor wins under GD. The ordering *flips* with the optimizer. No other candidate predicts a flip.
- **Prior art:** "Flavors of Margin" (arXiv:2410.22069); Adam on separable data (arXiv:2406.10650; per-sample departure 2510.26303; learning-rate schedule dependence 2611.01929); smooth homogeneous nets under Adam and Muon (2602.16340). Our networks are not homogeneous (tanh, biases) and use weight decay, so the theorems do not apply directly. That is part of what is tested.

### A3. Lazy bulk, rich core
Only units with large output weight move far; the rest stay near initialization. The core is chosen by the dynamics (A1 or A2); the bulk is a sample of the prior.
- **Explains:** O4 and O9, and why volume works only for the bulk (O2 vs. the volume literature).
- **Distinct prediction:** distance moved from initialization is strongly bimodal and tracks |output weight|. The bulk's unit distribution matches the solid-angle prior even at the end of training.

### A4. Description length of the circuit
Training finds the circuit with the shortest description: smallest total integer weight.
- **Explains:** O1 (it is the atlas's own cost, refined), possibly O7.
- **Distinct prediction:** the isomer with the smallest summed minimal-integer-weight representation wins, independent of the optimizer. This contradicts A2's flip.
- **Note:** minimal integer weights and ℓ1/ℓ∞ margins are closely related, so A4 and A2 under Adam may be hard to separate. The GD arm separates them.

### A5. Basin accessibility (dynamical volume, not prior volume)
What matters is the volume of the *basin of attraction* of each isomer under the dynamics, not the volume of the region that computes it.
- **Explains:** O2, since basins and regions differ.
- **Weakness:** as stated, it re-describes the data. It becomes testable only with an independent way to estimate basins, for example short-horizon rollouts from the prior, scored before the long run.

### A6. Symmetry breaking by the target's own statistics
The target's correlation structure (Chow parameters, Fourier spectrum) breaks the permutation symmetry among units at a rate set by the spectrum, and the units that break first form the core.
- **Relation:** a mechanistic version of A1 that does not need small initialization; the rate argument concerns relative, not absolute, scales. Overlaps with A1 in its predictions until timing is measured.

## 3. What would count as finding "the" rule

A determinant rule here means a predictor with no fitted parameters that meets all four tests:
1. it is stated before the data;
2. it predicts the core's isomer distribution as well as reseeding allows: the JS ratio between prediction and data is close to 1, not just ρ > 0;
3. it stays correct across width, initialization and optimizer, *changing its prediction exactly where the optimizer changes* if it is geometry-dependent;
4. it transfers to 5-input functions and to a second task family without modification.

No candidate meets these yet. The ceiling observed so far is ρ ≈ 0.4.

## 4. Discriminating test (Spike 13)

| Candidate | Prediction tested | Pass | Fail |
|---|---|---|---|
| A1 | The core contains t\* more often than the share of isomers containing t\* | ≥ 1.5× in every main environment | ≤ 1× in any |
| A2 | ℓ2-margin predictor beats ℓ∞ under GD; the order flips under AdamW | both orderings | both reversed |
| A4 | Minimal-integer-weight predictor wins under both optimizers | best in both | worst of the three in either |
| O6 under GD | Without Adam, S_agree depends on initialization scale | difference ≥ 0.1 | reversed |

A3 and A6 need measurements over time and of distance moved; they are deferred to Spike 14.
