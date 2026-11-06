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
| **02b** | Ontology *generation*: propose new candidates when the closed world is refuted | Can revision go beyond elimination without becoming unconstrained (§1.3 last bullet)? | **proposed next** |
| 03 | Succinct equivalence certificates | Proof-carrying translation that scales past the exhaustive wall (F3) | planned |
| 04 | Status as structured warrant | Redesign of the §10 taxonomy into a partial order (F7) | planned |
| 05 | F1: stateful systems (Mealy machines, LTS) | Trace equivalence vs bisimulation vs I/O; "don't collapse into functions" | planned |
| 06 | Kernel in a proof assistant | Layer A: restate F0 kernel judgments in Lean 4 and prove the decision procedure correct | planned |
| 07 | CSIR v0 extraction | First schema, after 01, 02 and 05 have shown what is actually shared | planned |

### Spike 02b (proposed next): ontology generation

Spike 02's agent can *refute* its candidate set but cannot *repair* it. The charter's revision story (§3.4, §8.11) needs both.

- **Smallest slice:** a generator that enumerates small DAGs over the observables plus at most one or two latents, constrained by everything already settled (directly measured interventional facts, refuted structures, the screening-off/complementarity signatures from F6). Generated candidates enter the same adequacy loop.
- **H2b.1:** after closed-world refutation, a constrained generator recovers an adequate ontology within a bounded number of candidates. *Kill:* the space blows up, or adequacy-passing candidates are mostly artifacts.
- **H2b.2:** settled interventional facts prune the generated space by a large factor. *Kill:* pruning is negligible.
- **H2b.3:** generated-then-accepted ontologies carry their provenance (which constraints produced them) and remain CONJECTURE-capped. *Kill:* the ledger can't express generation provenance.

Alternative next steps, if you prefer: **Spike 04** (status as a structured warrant, now with two independent motivations, F7/S01 and F8/S02), or **Spike 03** (scaling verification past n≈16).

## Open questions carried forward

- **Q-L1** (F7): status labels form a partial order, not a chain. What structure is it?
- **Q-G1** (F1): should canonical-form parameters (like variable order) live in Ω or in the CSIR node?
- **Q-F1** (F6): do the equivalence relations of Layer F form a lattice with useful meets and joins, and does candidate and certificate transport along inclusions generalize beyond F0?
- ~~**Q-H1**~~: answered by Spike 02 F6. With noise, the signature is complementarity vs screening-off, not substitutability.
- **Q-B1** (S02 F4): identity criteria for latent entities across rival ontologies (currently by name).
- **Q-E1** (S02 F7): task-relative stopping. When does an agent need absence claims at all?
- **Q-A1** (S02 F2): a general recipe for calibrating adequacy tests of fitted predictors (bootstrap, e-values, or held-out refits).
