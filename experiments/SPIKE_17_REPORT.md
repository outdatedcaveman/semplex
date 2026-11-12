# Spike 17: Mechanism of the Curie bias; a prior-symmetry method; where finite networks leave the kernel

**Date:** 2026-11-12 · **Status:** pre-registered (no run, and no analysis of the statistics below, has been made) · **Follows:** Spike 16 "what survives"

## Arm 1: where does the circuit-level Curie bias come from?

Two mechanisms make different predictions:
- **(M-pair) Coordination:** the bias lives in *which units are paired*. Training couples units so that the pair keeps the task's symmetry.
- **(M-unit) Unit concentration:** each unit lands, almost independently, on a few G_g-orbits of threshold functions. Units with a large stabilizer are favoured. Symmetric pairs then arise combinatorially, by drawing two units from the same small orbit.

Equivariant bifurcation theory suggests the first ingredient of M-unit. The equivariant branching lemma says symmetry-breaking branches generically carry *maximal* (axial) isotropy subgroups. A unit "remembers" as much symmetry as a generic bifurcation allows.

**Test, on Spike 14's stored cores (A8, G8, A128), using statistics not computed before:**
- *Unit marginals:* m(t) = total credit of unit t across cores.
- *Independent-pairing model:* P(I = {a, b}) ∝ m(a)·m(b), restricted to isomers of g.
- β_ind is that model's orbit-mass exponent, computed exactly as β_obs was in Spike 14.
- *Unit-level exponent β_u:* unit-orbit mass ∝ |unit orbit|^β_u.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.1 | M-unit: pairing is close to independent given unit marginals | \|β_ind − β_obs\| ≤ 0.5·\|β_obs\| in all three runs | β_ind ≥ 0 in any run (coordination is then essential) |
| H17.2 | Units themselves are Curie-biased | β_u ≤ −0.5 in all three runs | β_u ≥ 0 in any |

## Arm 2: a symmetry method that can transfer labels (prior-level, approximate)

The no-transfer lemma (Spike 16) rules out exact data stabilizers. Approximate symmetries are not ruled out. These are transformations σ under which the labelled pairs (x, σx) agree, and which map labelled points to unlabelled ones.

**Method: certified symmetry propagation (CSP).**
- **Candidate generators:** the 28 input transpositions, the cyclic shift, reversal, the 8 single-input negations and global negation.
- **Acceptance:** σ is accepted iff it has at least 10 both-labelled pairs with x ≠ σx and *all* of them agree. Under a null of independent fair labels, the chance probability is ≤ 2⁻¹⁰ per generator, so about 0.04 false accepts per task over 39 candidates.
- **Propagation:** the accepted generators generate a group Ĝ. Each Ĝ-orbit containing labelled points with consistent labels passes that label to its unlabelled points. A conflicting orbit voids Ĝ, and the method falls back to plain training.
- **Model:** the same MLP is trained on the enlarged labelled set.

**Workload:**
- n = 8 inputs (256 points), 128 labelled at random.
- Target families: functions invariant under S8 (symmetric functions), C8 (cyclic shifts), S4×S4 (two blocks), and **none** (random targets). 30 targets each, 3 seeds.
- MLP: tanh, width 64, AdamW. Also reported: an oracle propagation with the true group.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.3 | CSP improves held-out accuracy when the target family is symmetric | mean gain ≥ +0.05 for each of S8, C8, S4×S4 | gain ≤ 0 for any |
| H17.4 | CSP does no harm when there is no symmetry | \|mean gain\| ≤ 0.01 on random targets | loss > 0.02 |

**Prior art (index level):** learned invariances (Augerino, Benton et al. 2020), automatic augmentation search, symmetry-discovery methods. The new element is a *certified* acceptance rule with an explicit false-accept bound and exact propagation. The pre-registered claim is only about the gains above.

## Arm 3: where do finite networks leave the kernel?

**Workload:** fresh seeds on Spike 15's 240 symmetric partial tasks, 5 seeds each. Cells: tanh-AdamW at widths 8, 64 and 512, plus tanh-GD at width 8. The kernel completion is the tanh NTK interpolant, as in Spike 16.

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H17.5 | Feature learning compresses: when the net's completion differs from the kernel's, it is cheaper (atlas cost) more often than costlier | sign test p < 0.01 in every cell | costlier more often in any cell |
| H17.6 | The kernel limit is approached with width | P(learned = kernel) rises from width 8 to 512 by ≥ 0.10 | it falls |
| H17.7 | Symmetry beyond the kernel: when the net departs from the kernel, it stays symmetric | P(symmetric \| learned ≠ kernel) ≥ 2 × the symmetric share q of equally cheap completions | ≤ 1 × q |
