# Program: learning as minimal symmetry breaking under determination

> **Update after Spike 17.** (1) The circuit-level Curie bias is a *single-unit* law; pairing is independent; the Chow-pull explanation is killed. (2) Symmetries that are approximate and global, rather than exact stabilizers, do transfer labels. Certified symmetry propagation (CSP) takes cyclic targets from chance to 0.98, matches an oracle, and does nothing on random targets. (3) Finite networks depart from the kernel in about 40% of runs, toward cheaper and symmetric completions: the non-kernel part of the function-level bias.
>
> **Revision after Spike 16 (2026-11-12).** T4 is mostly explained by the kernel limit: the NTK interpolant is symmetric on symmetric data, and it matches about two thirds of the networks' symmetric completions. The stabilizer-consistency method (§3) is **refuted**, by an elementary no-transfer lemma (exact data stabilizers never link unlabelled inputs to labelled ones) and by the data (gains within ±0.003). What survives as original: Theorem 15, and the mechanism-level Curie bias in Boolean circuits, which kernels cannot express and which did not transfer to modular addition. The text below is kept as written, with these corrections.

**Status:** research program, 2026-11-12. Every numbered claim carries its warrant: PROVED, EMPIRICAL (with spike), or CONJECTURE (with the test that would decide it). Nothing here is established beyond what its warrant says.

## 1. The question

Why does gradient training of an over-parametrized network generalize, and why does it build the particular mechanisms it builds? Existing answers each cover part of the picture:
- **Simplicity bias / volume:** the function chosen is a high-prior-volume one. Spike 11 shows this does not extend to mechanisms.
- **Implicit margin maximization:** steepest descent maximizes a margin in its own geometry. Spike 13 finds it weak in this regime.
- **Incremental learning:** units are learned one at a time. Spike 13 finds the prediction true but the usual mechanism inapplicable.

The proposal is that one structural principle organizes what these leave unexplained, and that it is stated in terms of the **task's symmetry group alone**.

## 2. The theory in four parts

**T1. Determination (PROVED; THEORY §3.1–3.3).** What a model must compute is fixed by the task's conflict structure: which inputs must be told apart. A first layer is an observational power; a mechanism is a minimal determining set.

**T2. Equivariance (PROVED; THEORY Thm 15).** If initialization, architecture and update rule are invariant under a group G that preserves the task, the *law* of the learned mechanism is G-invariant. Every law of mechanism choice is therefore a law about G-orbits. (Confirmed numerically: Spike 14 H14.1.)

**T3. The Curie bias (EMPIRICAL in Boolean circuits: Spike 14; transfer to modular addition FAILED its pre-registered test: Spike 15 H15.1).** Individual runs do not merely have a symmetric law. They concentrate on mechanisms and functions with a *large stabilizer* in G. Orbit mass ∝ |orbit|^β with β ≈ −2 to −6, the reverse of an entropy or volume law (β ≥ 1). This held on fresh seeds and unseen elements, for circuits and for functions (77% of ties broken toward the more symmetric completion).

**T4. Generalization as symmetry inheritance (EMPIRICAL, pre-registered: Spike 15 H15.3–H15.4, six architecture cells, six groups; learned completions keep the data's symmetry 81–93% of the time vs 18% for equally cheap completions. The kernel-limit explanation is not yet excluded).** On an underspecified task, the completion chosen is a cheap one that keeps the stabilizer of the *observed data*. Hence:
- **Prediction T4a:** generalization succeeds when the world's target shares the stabilizer of the training data, and fails in proportion to the target's *symmetry deficit* relative to that stabilizer.
- **Prediction T4b:** a model's out-of-sample errors concentrate on inputs where the true target breaks a symmetry the training data happened to have.

This is a structural escape from "no free lunch": training does not assume smoothness or low norm; it assumes the world is no less symmetric than what it has seen. T4 is falsifiable with planted targets (Spike 16).

## 3. A method that follows if T3–T4 hold: stabilizer-consistency training

If training already prefers to keep the data's symmetries, a learner can be helped by making that preference explicit and exact.

1. **Compute G_data**, the exact stabilizer of the labelled training set: the largest group of input transformations (from a declared family, such as input permutations and negations for tabular binary data, or translations and reflections for grids) that maps the labelled set to itself and preserves labels. This is a finite computation; no symmetry is assumed in advance.
2. **Train with a consistency penalty** λ·E_x E_{σ∈G_data} ‖f(σx) − f(x)‖² on *unlabelled* inputs. Equivalently, average the model over G_data at test time.
3. **Claim (CONJECTURE, test in Spike 16):**
   - It improves held-out accuracy exactly when T4a's symmetry deficit is zero.
   - It hurts in proportion to the deficit when it is not.
   - Its gain is largest where the plain network's Curie bias is weakest (wide GD networks, Spike 13 F5).

What is new relative to data augmentation and equivariant architectures is that the group is **derived from the data as an exact stabilizer**, not chosen by the designer, and a theory says when it should help.

A further step, if this works, is an **architecture whose symmetry group is inferred**: layers made G_data-equivariant on the fly, with G_data re-estimated as data arrive. This is a programme, not a claim.

## 4. Correspondences with Synesism (inspiration, not premises)

Synesism (`outdatedcaveman/synesism-workshop`, `canon/principles.md`) is a structuralist-monist system. Several of its principles have exact or near-exact counterparts in the results above. They are listed because they suggested hypotheses; the hypotheses stand or fall on the tests.

| Synesism | Counterpart here | Status of the counterpart |
|---|---|---|
| **P0/P1, univocity and univalence:** equivalent beings are identical; difference is internal articulation of the One | T2: circuits related by a task symmetry are one mechanism; the right object is the orbit, not the circuit | PROVED (Thm 15) |
| **P8, modularity:** each being accesses a partial, perspectival slice; the total is conserved and sums to one | The ensemble over seeds is exactly symmetric; each run is a symmetry-breaking "module" of it; probabilities over the orbit sum to one | PROVED (ensemble), EMPIRICAL (individual breaking is small) |
| **P9, universal attractor:** a structural pull toward the Absolute, the most unified configuration | T3: a pull toward the mechanism with the largest stabilizer | EMPIRICAL (Spike 14); Spike 15 tests transfer |
| **P6, differentiation:** trajectories tend to increasing variation | The opposing pull: finite capacity forces symmetry breaking (arXiv:2610.36138). T3 says training breaks as little as capacity requires | CONJECTURE: the balance of P6 and P9 sets β |
| **P2, coherence (Yoneda):** to be is to stand in relations | About two thirds of learned circuits contain a unit that exists only together with its partner; no single-unit network reaches it | EMPIRICAL (Spike 14 F3, post hoc) |
| **P5, partition and conjoinment:** two co-equal operations; more ways to conjoin than to partition | The first layer partitions the input space into cells; the output conjoins cells. Training reaches minimal circuits more reliably when there are more of them (abundance, Spike 14 H14.9) | EMPIRICAL (abundance); the mapping itself is an analogy |

**One sharpened prediction suggested by P6 and P9 together:** β should become *less* negative (weaker Curie bias) as capacity becomes scarcer relative to the task, and more negative as width grows. Spike 14 already hints at this: A128 β ≈ −3.2 vs A8 β ≈ −2.3. To be pre-registered.

## 5. What would refute the program

- Spike 15 arm A or arm B fails. The Curie bias is then a fact about Boolean threshold circuits, not a principle.
- T4a fails: generalization does not track the symmetry deficit.
- The stabilizer-consistency method gives no gain where the theory says it should.

## 6. What would make it publishable

A single paper needs:
1. Theorem 15 machine-checked in Lean, for a general equivariant training map.
2. The Curie law in at least two unrelated domains with pre-registered tests (Spike 14, Spike 15).
3. T4 confirmed with planted targets, plus the method's gain on at least one standard benchmark with a known or derivable symmetry: permuted tabular data, or images with partial translation symmetry.
4. Code, seeds and raw counts released (already in `experiments/results/`).
