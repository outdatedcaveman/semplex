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
| 06 | Kernel in a proof assistant (Lean 4) | Layer A: prove the kernel's decision procedures correct | **blocked**: Lean 4.12 downloads fine, but running a downloaded binary needs your permission (see plan below) |
| **07** | CSIR v0.1 extraction | One schema across fragments; composition along the relation order | **done**, see `experiments/SPIKE_07_REPORT.md` |
| — | Bibliography verification | Charter §13: no unverified citations | **done**, see `charter/BIBLIOGRAPHY.md` (two corroborations, one discrepancy) |

### Spike 06 plan (ready to run once the toolchain is permitted)

Goal: move the PROVED-IN-FRAGMENT trusted base from "220 lines of Python + CPython" toward a proof-assistant kernel. The smallest slice, in Lean 4 core (no Mathlib):

1. Define `Expr` (const, var, not, and, or, xor, ite) and `eval : Expr → (Fin n → Bool) → Bool`.
2. Define `allAssignments n : List (Fin n → Bool)` and prove completeness: every assignment is in the list.
3. Define `decideEquiv e₁ e₂ := allAssignments.all (fun σ => eval e₁ σ == eval e₂ σ)` and prove `decideEquiv e₁ e₂ = true ↔ ∀ σ, eval e₁ σ = eval e₂ σ`. That is soundness and completeness of Spike 01's exhaustive kernel, in a fragment.
4. Stretch goal: a verified RUP checker for Spike 03 (unit propagation soundness), the step that would make large-n proofs proof-assistant-backed.

**Kill criterion:** the proofs need more than core Lean, or the Lean statement cannot be connected to the Python artifacts without a large trusted translation. In that case, record the bridge as the new weakest link.

**What is needed from you:** permission to run the Lean 4 toolchain, downloaded from the official `leanprover/lean4` GitHub releases (a `Bash` permission rule, or approval when prompted).

### Proposed next spikes

| Spike | Focus | Why now |
|---|---|---|
| 08 | Bridge: world-model ↔ executable artifact | CSIR has no link from a causal model to a circuit or program implementing its decision rule. This is the charter's §8 steps 9–10 (distill, then translate and verify) |
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
