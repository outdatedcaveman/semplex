# Roadmap: hypothesis-driven spikes

The charter (`charter/CHARTER_v0.1.md`) describes *what* the discipline should eventually be. This file describes *how we get there*: in thin, end-to-end slices. Each slice tests specific assumptions of the charter against running code and real measurements before anything is built out exhaustively.

## The spike protocol

Every spike is a small experiment on the charter itself:

0. **Prior-art gate.** Before building: search for the result, record what was found and at what verification level in `charter/REFERENCES.md`, and state what would be new. (Added after the 2026-11-11 review found prior work for most of the theory core.)
1. **Question.** Which charter assumption(s) are we testing?
2. **Hypotheses with kill criteria.** What would count as the assumption *failing*? We write this down before building.
3. **Smallest slice.** The minimum code that runs the whole loop (front end → semantics → verification → ledger) on the fragment. No layer gets built beyond what the slice needs.
4. **Adversarial checks.** An intentionally wrong component must be caught (charter §12.1). Mutation-test the tests.
5. **Measure.** Seeded and reproducible, with the workload described. All numbers are EMPIRICAL and labeled as such.
6. **Report.** Verdict per hypothesis (held / broke / sharpened / no content), numbered findings, proposed charter amendments, honest gaps.
7. **Feed back.** Charter amendments go through `decisions/` (ADR) with an impact analysis (charter §13.19).

Rules of thumb:
- **Rule of three for the CSIR.** No general schema until three fragments have needed the same thing.
- **Riskiest assumption first.** Order spikes by "if this is false, how much of the charter dies?"
- **Every spike ships a ledger.** Claims about the system get the same status discipline as claims made by the system.

## Spike sequence

| Spike | Fragment / focus | Main assumptions under test | Status |
|---|---|---|---|
| **01** | F0: finite Boolean functions, 3 substrates | Canonical forms; untrusted translation + small verifier; task sufficiency; resource gain; status taxonomy | **done**, see `experiments/SPIKE_01_REPORT.md` |
| **02** | World-facing sandbox: synthetic world with known latent structure | Natural semantics (§3.3); measurement maps; rival ontologies; evidence ledger; ontology revision (§3.4); "observation can hide causal difference" (§10) | **done**, see `experiments/SPIKE_02_REPORT.md` |
| **02b** | Ontology *generation* when the closed world is refuted | Revision beyond elimination, without relativism (§1.3) | **done**, see `experiments/SPIKE_02b_REPORT.md` |
| **03** | Succinct equivalence certificates (RUP) | Proof-carrying translation past the exhaustive wall (S01 F3) | **done**, see `experiments/SPIKE_03_REPORT.md` |
| **04** | Status as structured warrant | §10 taxonomy as a partial order (S01 F7, S02 F8) | **done**, see `experiments/SPIKE_04_REPORT.md`, ADR-0004 |
| **05** | F1: stateful systems (LTS) | Trace vs completed-trace vs bisimulation; "don't collapse into I/O functions" | **done**, see `experiments/SPIKE_05_REPORT.md` |
| **06** | Kernel in a proof assistant (Lean 4) | Layer A: prove the kernel's decision procedures correct | **done**, see `experiments/SPIKE_06_REPORT.md` |
| **T** | Protocol-Frame Theory | Unify the spikes formally | **v0.1 done**: `THEORY.md`, 11 theorems in `proofs/lean/Theory.lean` |
| **08** | Periodic table of threshold circuits (n ≤ 4) + compiler v1 | Exhaustive, verifiable optimal circuits per function class; first layer as observational power | **done**, see `experiments/SPIKE_08_REPORT.md`, `atlas/` |
| **07** | CSIR v0.1 extraction | One schema across fragments; composition along the relation order | **done**, see `experiments/SPIKE_07_REPORT.md` |
| — | Bibliography verification | Charter §13: no unverified citations | **done**, see `charter/BIBLIOGRAPHY.md` (two corroborations, one discrepancy) |

### Proposed next spikes

| Spike | Focus | Why now |
|---|---|---|
| T2 | Theory conjectures C1–C5 (`THEORY.md` §5) | C1 (statistical lift) and C2 (limit representations) first: they decide whether the theory survives contact with finite data and with the long-run properties science cares about |
| **08b** | Atlas hardening: certified lower bounds, skip/ReLU families, weight-space geometry, bit-flip theorem, n=5 hunt | See `experiments/SPIKE_08b_REPORT.md` | **done** (no depth-sensitive element among 100,000 five-input candidates) |
| **09** | Train small real networks against the atlas | Do learned circuits land on table optima, and which isomer | **done**, see `experiments/SPIKE_09_REPORT.md` |
| **10b** | Learning rules as observational powers; volume prior; grokking against ground truth | See `experiments/SPIKE_10b_REPORT.md`, `THEORY.md` §3.6 | **done**, except meta-learning of rules (failed four times; cause partly understood) |
| — | Literature review and novelty audit | `charter/LITERATURE_REVIEW.md` | **done (first pass)**; redo against the Codex dossier and Cammarata's essay once accessible |
| 11+ | New hypotheses H-B (volume law for mechanisms), H-D (clean vs superposed), H-C, H-E, H-F | Chosen because no prior work was found; each still needs its own prior-art gate |
| **10c** | Rule search fixed; learnability per rule dictionary (H-A) | See `experiments/SPIKE_10c_REPORT.md` | **done**; results are lower bounds |
| **16** | Prior-art closure (`charter/LITERATURE_REVIEW.md` §3c), Lean §§17–19 (`FrameHom`/DPI/Peirce/Ville), `ThresholdNet` LRAT bridge (`Cerp.lean` Part D), $n=16$ SAT-CEGAR + shared-encoder `ur_compiler`, `H-A`/`H-D`/`H-C`/`H-E` scaling | See `experiments/SPIKE_16_REPORT.md`, `HANDOFF_CLAUDE.md`, `proofs/lean/Theory.lean`, `proofs/lean/Cerp.lean` | **done** (empirics falsified wide `H-A` in favor of subspace `H-D`, found `wd=0.01` XOR6 collapse, isolated `O(2^d)` `pbToExpr` Lean kernel wall) |
| (old 10c) | Fix rule meta-learning; settle C7 (= H-A) | Fixed long horizon or adjoint method; then find the least observational power per element |
| (old 10b) | Grokking against ground truth | 5–6 inputs with a real held-out set: does the post-grokking function equal the table/solver optimum; score local learning rules (arXiv:2611.12248) the same way |
| 08c | Periodic table, remaining parameters | In order: (1) certify lower bounds; (2) n=5 by class-level search, hunting the first depth-sensitive element; (3) skip connections and ReLU; (4) weight-space geometry (the manifold proper); (5) prove the one-bit-flip ≤ 2 conjecture |
| 12 | Bridge: world-model ↔ executable artifact | CSIR has no link from a causal model to a circuit or program implementing its decision rule. This is the charter's §8 steps 9–10 (distill, then translate and verify) |
| 09 | LRAT certificates | S03 F3: hint-carrying proofs should make checking linear (literature agrees, see `charter/BIBLIOGRAPHY.md`) |
| 10 | Stress the epistemic agent | A non-parsimonious truth (S02b gap), cancelling paths (faithfulness premise), noisy interventions, more latents |
| 11 | First non-synthetic case study | Charter §11.1: only after the measurement-adequacy protocol is clear, which S02/02b now make concrete |

## Open questions carried forward

- ~~**Q-L1**~~: answered by Spike 04. Warrants = (method basis, trusted base, conditions), partially ordered; labels are a projection.
- **Q-W1** (S04): quantitative strength inside empirical warrants (p-values, effect sizes) is not yet ordered.
- **Q-C1** (S03 F3): certificate formats that are cheaper to check than to find (LRAT).
- **Q-G1** (F1): should canonical-form parameters (like variable order) live in Ω or in the CSIR node?
- **Q-F1** (F6): partially answered by Spikes 05 and 07. The inclusion order (ext ⊆ task; bisim ⊆ ctrace ⊆ trace) generalizes and drives CSIR composition. Meets and joins remain open.
- **Q-O1** (S05 F2): which equivalence is "right" is the coarsest one that the declared Ω can still observe. Needs a formal Ω → relation mapping.
- ~~**Q-H1**~~: answered by Spike 02 F6. With noise, the signature is complementarity vs screening-off, not substitutability.
- **Q-B1** (S02 F4): identity criteria for latent entities across rival ontologies (currently by name).
- **Q-E1** (S02 F7): task-relative stopping. When does an agent need absence claims at all?
- **Q-A1** (S02 F2): a general recipe for calibrating adequacy tests of fitted predictors (bootstrap, e-values, or held-out refits).
- **Q-LRAT-PB** (Spike 16): replace `O(2^d)` `Cerp.pbToExpr` Shannon trees with linear `O(d * w)` binary-adder PB->CNF in Lean so pure-kernel `by decide` LRAT scales past fan-in 4 (`xor4` >900s).
- **Q-Bounds-Sym** (Spike 16): break the $\binom{1882}{3} \approx 1.1\times 10^9$ `parity4 >= 5` enumeration barrier in `Bounds.lean` via $B_4$ signed-permutation symmetry reduction or an algebraic hyperplane-slicing theorem.
- **Q-OptStop-Connect** (Spike 16): instantiate `Theory.ville_anytime_valid_bound` directly on concrete sequential `QueryTree` / `cerp/epistemics.py` e-value processes and lift finite Markov-kernel DPI (`Fin n`) toward continuous state spaces.
- **Q-HD-Theory** (Spike 16): formalize why width coarsening shifts canonical profile representations from isolated units (`max_unit_corr`) to distributed linear subspaces (`R^2 = 0.9850`), and test SAT-CEGAR compiler scaling on ASTs beyond `n = 16` without dense tables.

## Spike 17 — Distinction admissibility (initial formal core verified, 2026-11-20)

Research branch: `research/distinction-calculus-2026-11-20`  
Draft PR: https://github.com/outdatedcaveman/semplex/pull/4

Implemented:
- typed DAP contract for protected observations and total unary/binary operations, with quotient descent;
- quotient factorization, binary congruence necessity, and unary/binary operation descent;
- recursive first-order syntax/semantics with equality, unary predicates, falsity, implication, ∀ and ∃; Lean proofs of Tarski free-variable invariance and semantic soundness of ∀-introduction / ∃-elimination under eigenvariable freshness;
- explicit nonempty-domain existential witness and empty-domain countermodel; variables and constants have separate semantic clauses;
- Lean identity-type substitution fragment;
- occurrence-sensitive resource fragment with token IDs, linear/persistent modes, provenance, a verified persistent-contraction preservation theorem, and a verified linear-contraction counterexample;
- small split fibration with discrete Boolean fibers, reindexing, cartesian factorization, and cleavage coherence;
- finite two-module overlap model proving compatible local sections glue uniquely and incompatible sections do not glue;
- dyadic Synesism molarity model: the value relation is a proved equivalence, but order/multiplicity do not descend through its quotient; binary partition conserves value while changing configuration, with synod-anchor preservation;
- finite Python reference model with **9 adversarial tests**;
- prior-art/novelty analysis, updated claim register, and architecture review.

**Verification:** GitHub Actions passed with Lean 4.12.0 compilation and axiom audits for Distinction, SmallFibration, ModuleDescent, and SynesismConservation, plus 11/11 Python tests. The audited theorem dependencies are limited to `propext` and `Quot.sound`; no `sorryAx`, custom axioms, or `Classical.choice` dependency appears. See https://github.com/outdatedcaveman/semplex/actions/runs/44693971714. Source reconciliation and module semantics design are in `research/SYNESISM_IDENTITY_MODULE_RECONCILIATION.md` and `research/SYNESISM_MODULE_SEMANTICS_DESIGN.md`.

**Scope:** these are small formal fragments and standard constructions, not full FOL, full linear logic, full HoTT, a new fibration theorem, a general sheaf theorem, or a proof of Synesism's ontology. No Synesism canon or CSIR v0.1 schema changes.

Next gates:
1. Generalize the protected interface to additional operation classes only where existing Semplex fragments require them.
2. Generalize the finite overlap model to multiple modules/covers and test descent conditions against the available Synesism module definitions; match the exact P8 source before claiming alignment.
3. Replace the Boolean persistent flag with occurrence-sensitive resources, copy permissions, and provenance-aware judgments.
4. Complete the four-system comparison, including eigenparameter side conditions and the exact structural rules each system requires.
5. Integrate typed transformation/loss certificates into CSIR only after multiple existing fragments require the same fields.
6. Continue prior-art comparison before any novelty claim.
