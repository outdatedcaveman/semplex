# Triage of `claims/PROPOSED.md` (2026-11-25)

**Scope.** This reviews the Gemini Master Principle work merged into `master` (PR #11 and its predecessors, 2026-11-22 to 2026-11-24): about 89k lines, Spikes 88–98, 118 Lean modules and one Cubical Agda module.

**Rule until a section is promoted:** nothing in `PROPOSED.md` enters `claims/REGISTER.md` without the promotion checklist at the end of this file.

## What was checked, and what passed

| Check | Result |
|---|---|
| `python -m cerp.register check`, `python -m cerp.status --check` on `master` | 0 problems |
| Frozen files touched | none. The diff from `7be5346` deletes one line and touches no frozen file |
| Pre-registration order, on four branches checked (closure, a5-ermoe, lie-lyapunov, variational) | predictions committed 30–45 min before results. On `master` everything lands in one consolidation commit (`9666061`), so order can be verified only on the branches |
| Lean hygiene, 118 new modules | no `sorry`/`admit`/`axiom`/`native_decide`/`unsafe` (the only `sorry` hits are docstrings saying "no sorry") |
| `lake build`, core Lean (`proofs/lean`) | PASS |
| `lake build`, Lean + Mathlib (`proofs/lean-mathlib`, 22 libraries) | PASS (4.5 min, cached Mathlib) |

The formal layer is sound as code. What it proves is a separate question; see the verdict classes below.

## The central empirical claim (§11): G(λ) on irreversible monoids

§11 tests a zero-parameter operator **G(λ)** on 12 fresh irreversible monoids: past-reachability Gramian W_c plus observability Gramian W_o, filtered by a kinetic heat kernel. This is the right question; it is the open problem left by Spikes 84–87.

The reported medians of cos(learned Gram, G(λ₀)):

| Arm | Median |
|---|---|
| GRU-MLP | 0.84 |
| GRU-linear | 0.94 |
| LSTM-MLP | 0.88 |
| tanh-RNN-MLP | 0.82 |

**The audit adds a null and finds the evidence much weaker than the verdicts suggest** (`experiments/audits/master_principle_null.py` → `experiments/results/audit_master_principle_null.json`):

| Quantity (median over the 12 monoids) | Value |
|---|---|
| cos(G, random centred π-weighted Gram), the chance level | **0.74** (95th percentile **0.82**) |
| cos(G, W_c + W_o), i.e. without the heat factor | 0.94 |
| cos(G, W_o) | 0.93 |
| cos(G, o oᵀ), the output-vector rank-1 Gram | 0.79 |

Reading:
- **Nonlinear readout (GRU-MLP):** 0.84 sits just above the null's 95th percentile. It is weak evidence, not "near-held".
- **Linear readout (GRU-linear):** 0.94 is clearly above chance.
- **The candidates cannot be told apart.** G, W_c + W_o and W_o agree with each other at 0.93–0.94, so a learned Gram near 0.84–0.94 cannot discriminate among them. That is why HM.1b broke: W_c + W_o without heat scored *higher*, 0.870 against 0.840.
- **What survives:** a two-sided Gramian (past reachability and future observability) is a promising candidate for the irreversible case. It reduces to the group rule because W_c = 0 for bijective automata (`wcOp_eq_zero_of_bijective`, proved). The kinetic heat factor is not supported on monoids, and the test used cannot separate the candidates.
- **What is needed:** a pre-registered test on *discriminating* monoids, where cos(G, W_c + W_o) and cos(G, W_o) fall below 0.8, scored against a per-automaton null. This becomes semplex Spike 99, in the work order.

## Verdict classes, section by section

- **Class A, substantive and correctly scoped; promotable after the checklist.**
  - §11 formal identities: Koopman / Perron–Frobenius adjointness, W_c = 0 for bijective automata, and the reduction to the Gibbs weight under commuting eigenmodes.
  - §1–§10 and G12: narrowing and caveat sections from earlier rounds. They downgrade claims and need only a citation check.
- **Class B, real but overstated; promote only with the overstated part removed.**
  - §11 empirical (see above).
  - §12–§17: honest BROKEN and NEITHER verdicts, kept. The titles claim more than the verdicts show.
- **Class C, results that hold by construction; record as engineering, not as evidence for the principle.**
  - §19–§21 and the semidirect and A₅ parts of §22: architectures that build the group presentation into the parameterisation ("exact semidirect generator locking", "icosahedral" templates).
  - Their "5/5 HELD" runs (homomorphism error ≈ 1e-13, accuracy 1.000) show the hard-coded structure works. They do not show that learners *find* it.
- **Class D, packaging; no new content.**
  - The capstone `master_principle_universal_closure` was four independent results with disjoint hypotheses joined by ∧. It is renamed `four_results_bundle`, with a deprecated alias.
  - Titles such as "Grand Closure", "Complete Unification" and "Final Synthesis" (§22–§27) should be read as "collection".
- **Not triaged in depth:** §18 (GHSRT), §22–§27 beyond the points above, and the Cubical Agda `SemanticUnivalence` module, which is a standard derivation of `ua` from Glue. Each still needs a reader before promotion.

## Promotion checklist (for any agent)

1. State exactly what is proved, and say where it is standard (cite it). A proof of a textbook result is formalisation work, not a finding.
2. For any empirical alignment metric, report the null: chance level and 95th percentile for the same automata. Report how much the candidates agree with each other, and test only where they disagree.
3. If the hypothesised structure is built into the architecture, the result is an engineering result.
4. Pre-registration: predictions committed before results *on the branch that ran them*. Link the commits.
5. Then add the `P###` row to `claims/REGISTER.md` with its dependencies, and run `python -m cerp.register check` (0 problems).
