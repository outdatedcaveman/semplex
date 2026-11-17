# Learned abstractions are closed macrostates with causal power, shaped by what they predict

*Draft for outside review, 2026-11-17. The semplex project (outdatedcaveman/semplex). Every number below is from a pre-registered experiment whose report, code and frozen results are in the repository (`experiments/SPIKE_57`–`SPIKE_62_REPORT.md`), unless marked exploratory.*

## Abstract

Is an abstraction a coarse description of a system's states (a macrostate), or a thing with causal power of its own? For deterministic systems the two coincide exactly when the coarse-graining is closed under the dynamics, so that the macrostates have a dynamics of their own. The coarsest closed coarse-graining that still decides the system's outputs is the Myhill–Nerode congruence, the states of the minimal automaton (machine-checked in Lean). We ask whether neural networks trained only on outputs build this object.

In recurrent networks trained on automata whose algebraic building blocks are known (cyclic groups, a reset, S₃, A₄, A₅, a direct product and a cascade):
- in every one of 31 fitted networks, a linear probe recovers the minimal-automaton state exactly, and its macro-dynamics are exactly deterministic;
- writing another macrostate into the network makes the whole subsequent output follow the automaton from that macrostate in 100% of 2,000 trials per network;
- swapping in micro-detail from another history with the same macrostate changes nothing.

Learning cost follows the algebraic grading of the target, from the aperiodic reset to the non-solvable simple group A₅.

The geometry of the learned states is not the group's smallest faithful representation. It is predicted by what the network must read out. A state that encodes its expected future outputs has a Gram matrix equal to the permutation character of the readout, which we derive exactly. A prospective test confirmed this: A₅ read out through its 6-point action gives the 5-dimensional character, with the minimal faithful 3-dimensional characters anti-correlated. A proposed compression refinement was refuted prospectively (§5). The predictive-state kernel matches every fitted case but one.

## 1. Closure: abstraction as a macrostate with its own dynamics

Let T_a : X → X be the action of letter a on states, and let o : X → O be the output. A coarse-graining π : X → B has macro-dynamics (T̄ with π ∘ T_a = T̄_a ∘ π) iff it is a congruence (π x = π y ⇒ π T_a x = π T_a y).

The Myhill–Nerode relation x ≈ y ⟺ ∀w. o(run w x) = o(run w y) is a congruence. It decides o, and every congruence deciding o refines it. All three facts are proved in Lean 4 (`proofs/lean/Closure.lean`; standard axioms, most proofs axiom-free).

This is the deterministic case of the closure results of Rosas, Geiger, Luppi, Seth, Polani, Gastpar and Mediano (arXiv:2402.09090), who prove that causal closure of a coarse-grained process is equivalent to strong lumpability of its causal states. In coalgebraic terms, the Myhill–Nerode quotient is the image of the system in the final coalgebra of behaviours.

## 2. Setup

**Automata.**
- ℤ/5 and ℤ/7 counters with output [c = 0];
- a 3-value reset;
- S₃, A₄ and A₅ acting on their natural points, with output the image of point 0 (a left coset of a point stabiliser);
- a flip-flop × ℤ/3 product and a flip-flop ≀ ℤ/3 cascade (same states and outputs; in the cascade the count direction depends on the mode).

All are minimal (Moore minimisation).

**Networks.** GRUs (width 32 or 64) trained by Adam on random strings of length 30, with binary cross-entropy on the outputs only. Fit guard: ≥ 0.99 accuracy at length 100. Five seeds per automaton.

## 3. Results: closure, causal power, inertness, cost

From Spike 58 (pre-registered; all hypotheses below held):

| Quantity | Value |
|---|---|
| fitted networks | 31 (36/40 fitted; ℤ/7 excluded, with 2 seeds) |
| probe accuracy (minimal state), held-out | 1.000 in 31/31 |
| macro-determinism of probe states | 1.000 in 31/31 |
| intervention to another macrostate: all 20 later outputs follow the automaton from it | 100% of 2,000 trials, 31/31 networks |
| swap of within-macrostate micro-detail: outputs unchanged | 100%, 31/31 |
| within-state variance (Spike 57, exploratory) | 20–27% for group states; 2% for the reset |

Learning cost (median steps to 0.99): reset 50 < ℤ/5 100 < ℤ/7 125 < S₃ 175 < A₄ 425 < A₅ 650. Spearman with the predicted order is 1.0, and a cascade costs more than the matching product (300 vs 250). This order also tracks group size; separating size from solvability needs groups of equal order.

**Interpretation.** The networks keep substantial micro-state detail (the "thermodynamic" macrostate view). The abstraction they build is nonetheless exactly the minimal automaton, and it is causally efficacious while the micro-detail is causally inert. The two readings of abstraction (macrostate, cause) are both true of the same object.

## 4. Geometry: the readout determines the shape

For group automata, compute the cosine Gram matrix G of state centroids and score candidate kernels K(g, h) = χ(g⁻¹h) by Spearman correlation.

**Derivation.** For a group automaton with output the left coset gH, and w uniform on G,

  E_w ⟨o(gw), o(hw)⟩ = |H| χ_perm(g⁻¹h) / |G|,

where χ_perm is the permutation character on G/H. A predictive state's Gram matrix is therefore the readout's permutation character. An exact finite-horizon computation (horizon 30) reproduces the best character observed in trained networks in 3 of 4 Spike 60 automata (`experiments/theory/predictive_kernel.py`).

**Tests:**
- **Spike 58:** A₅ via 5 points gives χ₄ in 5/5 runs; the minimal faithful 3-dimensional characters are ≈ 0.
- **Spike 60, prospective:** A₅ via 6 points gives χ₅ in 3/3 fitted runs (5/5 overall), with the minimal faithful characters at −0.16 to −0.25.
- **Spike 60:** S₄ via 6 points (readout module standard ⊕ χ₂) uses the standard representation alone, contradicting the pure predictive-state form.

## 5. No compression: the predictive state is the law (Spike 62)

**C31‴** (keep the smallest faithful set of irreducibles from which every output coset is linearly separable) matched all four Spike 60 cases post hoc. It was tested prospectively on five new readouts and **refuted**: the predicted set was best in 0/12 fitted runs. Networks keep unfaithful constituents as their dominant geometry (S₄ via ⟨(0 1 2 3)⟩: χ₂ 5/5; via ⟨(0 1 2)⟩: sign 5/5; 12-point readout: χ₂ 4/5).

The **exact predictive-state kernel** (the Gram of expected future outputs over the training horizon, computed from the automaton alone) predicts the best character in every fitted case of Spikes 60 and 62 except one: S₄ via its 6-point pair action, where networks use the standard representation. Three of these predictions were computed before the corresponding runs finished, though they were not formally pre-registered.

The current law is therefore: **a trained recurrent network represents a group concept by the geometry of its predictive state.** A formally pre-registered test, including the anomaly, is the next step.

## 6. Related work

- **Closure and emergence:** Rosas et al. 2024 (arXiv:2402.09090).
- **Transformers and Krohn–Rhodes shortcuts:** Liu et al. 2022 (arXiv:2210.10749); the length-generalisation algebra of Yang et al. (arXiv:2608.13433).
- **Circular features in language models:** Engels et al. 2024 (arXiv:2405.14860).
- **Trained RNNs recovering a theoretical construction:** Jensen et al., eLife (planning).
- **Causal abstraction via interchange interventions:** Geiger et al. † (not re-read for this draft).
- **Compositional open systems and black-boxing:** Baez, Fong, Pollard (arXiv:1508.06448).

## 7. Limitations

- A single recurrent architecture for the closure results. A 2-layer transformer failed to learn S₄ and A₅ at all (Spike 60); Spike 63 tests a deeper one.
- Small automata (up to 60 states).
- Characters are compared by rank correlation, not by a full isotypic decomposition.
- The cost order is confounded with group size.
- The predictive-kernel identity is proved on paper; its Lean formalisation is pending.

## Reproducibility

Every experiment has a pre-registered report committed before its run, frozen code and results, and is listed in `claims/REGISTER.md` (claims P185–P194) and `claims/RUNS.json`.
