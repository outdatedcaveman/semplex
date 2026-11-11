# Roadmap: hypothesis-driven spikes

The charter (`charter/CHARTER_v0.1.md`) describes *what* the discipline should eventually be. This file describes *how we get there*: in thin, end-to-end slices. Each slice tests specific assumptions of the charter against running code and real measurements before anything is built out exhaustively.

## The spike protocol

Every spike is a small experiment on the charter itself:

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
| 10b | Grokking against ground truth | 5–6 inputs with a real held-out set: does the post-grokking function equal the table/solver optimum; score local learning rules (arXiv:2611.12248) the same way |
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
