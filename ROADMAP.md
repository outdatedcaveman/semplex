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
| **02** | World-facing sandbox: synthetic world with known latent structure | Natural semantics (§3.3); measurement maps; rival ontologies; evidence ledger; ontology revision (§3.4); "observation can hide causal difference" (§10) | **next** |
| 03 | Succinct equivalence certificates | Proof-carrying translation that scales past the exhaustive wall (F3) | planned |
| 04 | Status as structured warrant | Redesign of the §10 taxonomy into a partial order (F7) | planned |
| 05 | F1: stateful systems (Mealy machines, LTS) | Trace equivalence vs bisimulation vs I/O; "don't collapse into functions" | planned |
| 06 | Kernel in a proof assistant | Layer A: restate F0 kernel judgments in Lean 4 and prove the decision procedure correct | planned |
| 07 | CSIR v0 extraction | First schema, after 01, 02 and 05 have shown what is actually shared | planned |

### Spike 02 (next): sketch

**World:** a simulator with a known latent structure. For example, a hidden quantity Z drives two noisy sensors S₁ and S₂, and an actuator A affects an outcome Y through Z. The data-generating process is known *to us* but not to the system.

**Rival ontologies:**
- O₁: S₁ and S₂ measure one latent Z
- O₂: S₁ and S₂ are independent causes of Y
- O₃: a confounded variant that is observationally equivalent to O₁ but differs under intervention

**Hypotheses and kill criteria:**
- H2.1: The ledger can represent an ontology revision, i.e. which commitments changed, why, what is invalidated, and what new predictions follow (§3.4). *Kill:* revisions need information the ledger can't type.
- H2.2: From observation alone, O₁ and O₃ are not distinguished, and the system **abstains** rather than picking one. Interventions on A distinguish them. *Kill:* the system confidently picks the wrong ontology from observational data.
- H2.3: Spike 01's F4 conjecture holds: substitutable variables in task sufficiency predict "shared latent cause". *Kill:* substitutability fails to track latent sharing in the simulator's known ground truth.
- H2.4: Measurement adequacy (§5.8) can be stated as a checkable claim indexed to protocol and evidence, without a truth oracle. *Kill:* every formulation smuggles in the simulator's ground truth.

**Smallest slice:** discrete variables, so F0's machinery can reuse care sets and sufficiency; Bayesian model comparison over 3 hand-written ontologies; experiment selection by expected information gain; a calibration check against held-out simulated data.

**Explicit non-claim:** the synthetic world is a calibration sandbox, not evidence that natural-world grounding is solved (charter §11.1).

## Open questions carried forward

- **Q-L1** (F7): status labels form a partial order, not a chain. What structure is it?
- **Q-G1** (F1): should canonical-form parameters (like variable order) live in Ω or in the CSIR node?
- **Q-F1** (F6): do the equivalence relations of Layer F form a lattice with useful meets and joins, and does candidate and certificate transport along inclusions generalize beyond F0?
- **Q-H1** (F4): does "substitutable ⇒ shared latent" hold beyond equality constraints, for example with noisy redundancy?
