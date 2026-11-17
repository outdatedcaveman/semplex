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

### Done (chronological)

| Spike | Fragment / focus | Main assumptions under test | Report |
|---|---|---|---|
| **01** | F0: finite Boolean functions, 3 substrates | Canonical forms; untrusted translation + small verifier; task sufficiency; resource gain; status taxonomy | `experiments/SPIKE_01_REPORT.md` |
| **02** | World-facing sandbox with known latent structure | Natural semantics (§3.3); rival ontologies; evidence ledger; revision (§3.4) | `experiments/SPIKE_02_REPORT.md` |
| **02b** | Ontology *generation* when the closed world is refuted | Revision beyond elimination, without relativism (§1.3) | `experiments/SPIKE_02b_REPORT.md` |
| **03** | Succinct equivalence certificates (RUP) | Proof-carrying translation past the exhaustive wall | `experiments/SPIKE_03_REPORT.md` |
| **04** | Status as structured warrant | §10 taxonomy as a partial order | `experiments/SPIKE_04_REPORT.md`, ADR-0004 |
| **05** | F1: stateful systems (LTS) | Trace vs completed-trace vs bisimulation | `experiments/SPIKE_05_REPORT.md` |
| **06** | Kernel in Lean 4 | Prove the kernel's decision procedures correct | `experiments/SPIKE_06_REPORT.md` |
| **07** | CSIR v0.1 | One schema across fragments; composition along the relation order | `experiments/SPIKE_07_REPORT.md` |
| **T** | Protocol-Frame Theory | Unify the spikes formally | `THEORY.md`, `proofs/lean/Theory.lean` |
| — | Bibliography verification, literature review | No unverified citations; novelty audit | `charter/BIBLIOGRAPHY.md`, `charter/REFERENCES.md`, `charter/LITERATURE_REVIEW.md` |
| **08** | Periodic table of threshold circuits (n ≤ 4) + compiler v1 | Exact optimal circuits per function class | `experiments/SPIKE_08_REPORT.md`, `atlas/` |
| **08b** | Atlas hardening | Certified lower bounds, skip/ReLU families, weight-space geometry, n=5 hunt | `experiments/SPIKE_08b_REPORT.md` |
| **09** | Train small real networks against the atlas | Do learned circuits land on table optima | `experiments/SPIKE_09_REPORT.md` |
| **10b** | Learning rules as observational powers | Task-blindness (Thm 12); volume prior | `experiments/SPIKE_10b_REPORT.md` |
| **10c** | Rule search; learnability per rule dictionary | C6, C7 (H-A) | `experiments/SPIKE_10c_REPORT.md` |
| **11** | H-B (volume law for mechanisms), H-D (coarser, not folded) | | `experiments/SPIKE_11_REPORT.md` |
| **12** | Bridge: causal model → verified circuit (`csir.distill_causal_rule`) | Charter §8 steps 9–10 | no report; P060, `tests/test_csir.py` |
| **13, 13b** | C1 statistical lift, H-C (grokking XOR6), H-E (depth separation) | | `experiments/SPIKE_13_REPORT.md` (13b: JSON only, `experiments/results/spike13b_hc_long.json`) |
| **14, 14b** | First real case studies (PlayTennis, UCI breast cancer) | Charter §11.1 | `experiments/SPIKE_14_REPORT.md` (14b: JSON only, `experiments/results/spike14b_breast_cancer.json`) |
| **15** | Ur-Compiler (profile factorization; F0/LTS/stochastic/continuous/causal) | H-G, H-H | no report; P068–P069, `experiments/results/spike15_ur_compiler.json` |
| **16** | Lean §§17–19, `ThresholdNet` LRAT bridge, n=16 SAT-CEGAR, H-A/H-D/H-C/H-E scaling | | `experiments/SPIKE_16_REPORT.md`, `HANDOFF_CLAUDE.md` |
| — | Project audit (2026-11-17) | Everything: broken, inconsistent, inefficient, unneeded | `AUDIT.md` |

### Open

| Item | Focus | Why |
|---|---|---|
| WP-A | Linear-size pseudo-Boolean → CNF in `Cerp.lean` | `pbToExpr` is O(2^fan-in); pure-kernel LRAT stops at ~4 inputs (`HANDOFF_CLAUDE.md`) |
| WP-B | Connect `ville_anytime_valid_bound` to a concrete sequential test in `cerp/epistemics/` | The Lean bound has no instance in running code |
| WP-C | `parity4 ≥ 5` neurons for unbounded weights; depth-3 separation | Bounded-weight CP-SAT is evidence only |
| WP-D | Symbolic (BDD/AIG) Ur-Compiler for n > 14 without dense tables | Current large-n path is sampled or SAT-CEGAR on given ASTs |
| C7 | Least observational power per atlas element | Spike 10c search results are lower bounds |
| — | Stress the epistemic agent | Non-parsimonious truth, cancelling paths (faithfulness), noisy interventions, more latents |
| — | Reports for Spikes 12, 13b, 14b and 15 | Register cites them; only code, tests and JSON exist |

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
- **Q-OptStop-Connect** (Spike 16): instantiate `Theory.ville_anytime_valid_bound` directly on concrete sequential `QueryTree` / `cerp/epistemics/` e-value processes and lift finite Markov-kernel DPI (`Fin n`) toward continuous state spaces.
- **Q-HD-Theory** (Spike 16): formalize why width coarsening shifts canonical profile representations from isolated units (`max_unit_corr`) to distributed linear subspaces (`R^2 = 0.9850`), and test SAT-CEGAR compiler scaling on ASTs beyond `n = 16` without dense tables.
