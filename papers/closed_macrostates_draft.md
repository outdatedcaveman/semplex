# Learned abstractions are closed macrostates with causal power; their shape is the leading component of a predictive state

*Draft for outside review, 2026-11-17. The semplex project (outdatedcaveman/semplex). Every number is from a pre-registered experiment whose report, code and frozen results are in the repository (`experiments/SPIKE_57`–`SPIKE_70_REPORT.md`), unless marked exploratory. Refuted predictions are reported as refuted.*

## Abstract

Is an abstraction a coarse description of a system's states (a macrostate), or a thing with causal power of its own? For deterministic systems the two coincide exactly when the coarse-graining is closed under the dynamics. The coarsest closed coarse-graining that still decides the outputs is the Myhill–Nerode congruence, the states of the minimal automaton (machine-checked in Lean). We ask whether neural networks trained only on outputs build this object, and what shape they give it.

**Closure and causal power.** In recurrent networks trained on automata with known algebraic building blocks (cyclic groups, a reset, S₃, A₄, A₅, a product and a cascade):
- in all 31 fitted networks, a linear probe recovers the minimal-automaton state exactly;
- writing another macrostate into the network makes all later outputs follow the automaton from it, in 100% of trials;
- swapping in micro-detail from another history with the same macrostate changes nothing;
- a mod-3 readout of a mod-6 counter leaves no decodable trace of the unobserved 2-part.

Learning cost follows the algebraic grading of the target, up to the non-solvable A₅.

**Shape.** The geometry of the learned states is not the group's smallest faithful representation (refuted for A₅ under two readouts). A state that encodes its expected future outputs has a Gram matrix given by the readout's permutation character; we derive this exactly. We also prove that all multiplicity-1 constituents of that character carry *equal* predictive energy.

Across 17 pre-registered automata, with the predictive kernel computed before training:
- networks build the kernel's top isotypic component as their leading constituent in 29/34 runs, including unfaithful predictions against smoother faithful alternatives;
- the full Gram is not the kernel;
- the predictive state does not decide the geometry when it is degenerate (identity readouts) or tied, and ties are broken by the generating set.

**A continuous case.** Networks asked to track only an unsigned axis under 3-D rotation do not build the minimal state space RP². They build its double cover S², where the rotation acts linearly.

## 1. Closure: abstraction as a macrostate with its own dynamics

Let T_a : X → X be the action of letter a and o : X → O the output. A coarse-graining π : X → B has macro-dynamics (π ∘ T_a = T̄_a ∘ π) iff it is a congruence. The Myhill–Nerode relation x ≈ y ⟺ ∀w. o(run w x) = o(run w y) is a congruence that decides o, and every congruence deciding o refines it.

All three facts are proved in Lean 4 (`proofs/lean/Closure.lean`). One uses classical choice; the others use no axioms. This is the deterministic case of Rosas et al. (arXiv:2402.09090): causal closure ⇔ strong lumpability. Coalgebraically, the Myhill–Nerode quotient is the image of the system in the final coalgebra of behaviours.

## 2. Setup

**Automata.** States are group elements, or the automaton's states. Letters act on the right, and an identity letter is included from Spike 66 on. Outputs are 0/1 vectors.
- Spikes 57–58: counters, a reset, S₃/A₄/A₅ with the image of point 0 as output, a product and a cascade.
- Spikes 60–69: coset readouts G/H of S₄ and A₅, identity readouts, subset readouts of abelian groups and Q₈, and pair readouts.

Minimality is checked by Moore minimisation.

**Networks.** GRUs (width 64, embedding 16) trained with Adam (lr 0.003, cosine schedule; the schedule is constant in Spikes 57–58). Training uses random strings of length 30 and binary cross-entropy on the outputs only. Fit guard: ≥ 0.99 accuracy at length 100. Five seeds per automaton (three in Spike 66).

## 3. Closure, causal power, inertness, cost (Spike 58)

| Quantity | Value |
|---|---|
| fitted networks | 31 (36 of 40 fitted; ℤ/7 excluded, with 2 fitted seeds) |
| probe accuracy (minimal state), held-out | 1.000 in 31/31 |
| macro-determinism of probe states | 1.000 in 31/31 |
| intervention to another macrostate: all 20 later outputs follow the automaton from it | 100% of 2,000 trials, 31/31 networks |
| swap of within-macrostate micro-detail: outputs unchanged | 100%, 31/31 |
| within-state variance (exploratory) | 20–27% for group states; 2% for the reset |

**Learning cost** (median steps to 0.99): reset 50 < ℤ/5 100 < ℤ/7 125 < S₃ 175 < A₄ 425 < A₅ 650. The Spearman correlation with the predicted order is 1.0, and the cascade costs more than the product (300 vs 250). The order is confounded with group size.

**Arithmetic closure** (Spike 66, H66.3 held). ℤ/6 read out mod 3: the c mod 2 probe is at 0.54 (chance 0.50), while the macrostate probe is at 1.0.

**Interpretation.** The networks keep substantial micro-detail (the "thermodynamic" view of a macrostate). The abstraction is nonetheless exactly the minimal automaton, and it is causally efficacious while the micro-detail is causally inert. Both readings of abstraction, as macrostate and as cause, are true of the same object.

## 4. Geometry: the predictive state

We use the cosine Gram G of centred, normalised state centroids, scored against kernels by Spearman correlation over off-diagonal entries. Irreducibles are computed as isotypic projectors of the regular representation; conjugate pairs and quaternionic types are merged into real irreducibles.

**Derivation.** For output = left coset gH and w uniform on G:

  E_w ⟨o(gw), o(hw)⟩ = χ_perm(g⁻¹h) / [G : H].

A predictive state's Gram is therefore the readout's permutation character. The exact finite-horizon kernel is K = Σ_{t ≤ 30} E_w⟨o(gw), o(hw)⟩, computed from the automaton alone (`experiments/spike69.py`, `predict`).

**Lemma (equal energy).** For a complex irreducible χ, the kernel χ(g⁻¹h) has Frobenius energy |G|², whatever its dimension. A constituent of multiplicity m therefore carries m²|G|², and a merged conjugate pair carries 2m²|G|². So in a permutation readout every multiplicity-1 real constituent of perm − 1 carries *the same* predictive energy. The predictive state cannot choose among them, and when the readout has several such constituents the prediction is a tie.

**Sequence of tests:**
1. **Minimal faithful (C31): refuted for A₅.** A₅ read out through 5 points gives χ₄ in 5/5 runs, with the 3-dimensional characters at ≈ 0 (Spike 58). Prospectively, A₅ read out through 6 points gives χ₅ in 3/3 fitted runs, with the minimal faithful characters at −0.16 to −0.25 (Spike 60).
2. **Compression to a smallest faithful, readout-sufficient set (C31‴): refuted prospectively**, 0/12 (Spike 62). Networks keep unfaithful constituents.
3. **Predictive state as a universal law: refuted** (Spike 66). For identity readouts the kernel is exactly diagonal, and networks still build structured geometry. That degeneracy was not checked before registration and is recorded as a design flaw.
4. **Formal two-regime test (Spike 69).** Seventeen automata were classified *before training* by τ, the total-variation distance of the kernel's isotypic energy from the degenerate (identity) kernel. Kernels with τ ≥ 0.15 count as structured. A structured kernel has a unique prediction if its top share is ≥ 1.5× the second, and is a tie otherwise.

| Result | Measured | Verdict |
|---|---|---|
| **Leading constituent = top isotypic component** (7 automata with a unique prediction) | 29/34 fitted runs (85%) | **held** |
| Full Gram = kernel (ρ ≥ 0.6) | 36% | broken |
| Predictive beats one-step output kernel | 31% | broken |
| Degenerate regime gives the minimal faithful representation | 9/23 | broken |
| Ties broken toward the faithful constituent | 55% | neither |
| Ties broken toward the lowest dimension | 45% | broken |

**Discriminating cases (where the kernel's prediction is not the smoothest faithful irreducible):**
- **A₄ on pairs** builds the unfaithful ω-pair, which carries 2× the energy of χ₃ by the lemma: 5/5 runs.
- **ℤ/8 read through {0, 1, 4}** builds frequency k = ±2, which identifies c and c + 4, rather than the k = 1 circle: 5/5 runs.
- **Exception: ℤ/7 read through {0, 2}.** The kernel put 81% of its energy on k = ±3, and every network built the k = ±1 circle.

**Ties are broken by the generating set.** For S₄ read through its 6 pairs, std is used with generators (01), (0123) and with (012), (0123) (5/5 each). With the Coxeter transpositions (01), (12), (23), χ₂ is used (4/5). The earlier "S₄ anomaly" is a dynamical tie-break, not a preference for faithful constituents, as A₄ on pairs shows.

**Degenerate regime.** With identity readouts, ℤ/8 builds its circle and D₄ its 2-dimensional faithful representation. Q₈, A₄ and S₃ instead lead with a character of the abelianisation, a letter-counting quotient (Q₈: word-length parity 5/5; A₄: the ω-pair 5/5; S₃: sign 3/5). This pattern is post hoc.

**What the shape law now is.** The leading constituent of a learned group concept is the top isotypic component of its predictive state, with one cyclic exception in seven. The rest of the geometry, the degenerate case and ties are not decided by the predictive state, and depend on the letters.

## 5. A continuous case: the network builds the double cover (Spike 70)

A direction u ∈ S² is rotated by random small rotations, which are the network's input (σ = 0.15).
- **SIGN** networks output u.
- **AXIS** networks output only uuᵀ − I/3. The axis dynamics close on RP², so RP² is the minimal state space.

All 10 networks pass the guard (R² ≥ 0.99 at the training length).

| | SIGN | AXIS |
|---|---|---|
| R² of hidden states on degree-1 harmonics | 0.73 | 0.74 |
| R² on degree-2 harmonics | 0.35 | 0.40 |
| sign of u decodable (balanced accuracy, exploratory) | 1.00 | 1.00 |
| antipodal/random centroid distance | 1.55 | 1.50 |

AXIS networks represent the signed direction, the double cover S² → RP², where SO(3) acts by its 3-dimensional representation. The quotient's smallest equivariant linear embedding is 5-dimensional. The extra bit is largely, but not completely, inert. Writing in the antipodal state raises AXIS output error 50× over a same-state swap, against 1,300× for SIGN. Antipodal donors come from rarely visited states, so this residual is unresolved.

Discrete closure discards what the readout cannot see (§3). Continuous closure kept a bit the readout cannot see. A reconciliation we have not tested: networks build the coarsest quotient on which the dynamics act linearly at small dimension.

## 6. Related work

- **Closure and emergence:** Rosas et al. 2024 (arXiv:2402.09090).
- **Transformers and Krohn–Rhodes shortcuts:** Liu et al. 2022 (arXiv:2210.10749); length-generalisation algebra (arXiv:2608.13433).
- **Circular features in language models:** Engels et al. 2024 (arXiv:2405.14860).
- **Trained RNNs recovering a theoretical construction:** Jensen et al., eLife.
- **Causal abstraction via interchange interventions:** Geiger et al. † (not re-read for this draft).
- **Compositional open systems and black-boxing:** Baez, Fong and Pollard (arXiv:1508.06448).
- **Representation-theoretic analyses of learned group operations:** e.g. Chughtai et al. on group composition †. This must be read and compared before submission: their setting (a group operation given as a binary input, not an automaton over words) differs, but their claim that networks learn particular irreducibles is directly related.

## 7. Limitations

- One recurrent architecture for the closure and shape results. A 2-layer transformer failed to learn S₄ or A₅. A 4-layer transformer trained with a curriculum learned them in 1 of 3 seeds, with the same geometry.
- Small groups (order ≤ 60).
- Constituents are scored by rank correlation of the Gram with each irreducible's kernel, a coarse summary of a mixture.
- The structure threshold τ ≥ 0.15 and the tie margin of 1.5× were chosen with the predictions, before training, not derived.
- The cost order is confounded with group size.
- The predictive-kernel identity and the equal-energy lemma are proved on paper; Lean formalisation is pending.

## Reproducibility

Each experiment has:
- a pre-registered report committed before its run;
- frozen code and results, hash-checked;
- claims in `claims/REGISTER.md` (P185–P203);
- run entries in `claims/RUNS.json`.

Commands are listed in each report.
