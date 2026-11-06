# Spike 07: CSIR v0.1, extracted rather than designed

**Date:** 2026-11-06 · **Charter refs:** §6 (CSIR), §7.3 (composition), §12.3 (independently inspectable artifacts) · **Status:** complete

## Question

The charter calls the CSIR "the pivotal artifact" but rightly defers its schema "until its adequacy is demonstrated". With three fragments now working (F0 Boolean functions, F1 transition systems, causal world-models), can one schema carry all of them? Can it encode the relation order the spikes discovered, and can a bundle be re-verified from its own contents?

## The schema (`cerp/csir.py`, examples in `csir/examples/`)

A bundle is plain JSON made of **nodes** and **links**.

- **Node:** an artifact (any kind), its interface (the Ω domain), optional ontological commitments, optional resources *with their cost model*, and provenance.
- **Link:** a claimed relation between two nodes, *relative to a protocol*, carrying a **certificate** sufficient to re-check it and a **warrant** (Spike 04).
- **Relations** come from a registry ordered by inclusion:
  - extensional ⊆ task[care]
  - bisimulation ⊆ completed-trace ⊆ trace
  - adequate-to and interventional (empirical, never transitive)

Every top-level field came from a concrete need in an earlier spike:

| Field | Needed by |
|---|---|
| link.protocol | S01 (care sets), S02 (Ω-indexed adequacy), S05 (equivalence depends on observer) |
| relation registry + order | S01 F6 (ext ⊆ task), S05 F1 (bisim ⊆ ctrace ⊆ trace) |
| link.certificate | S03 (RUP lemmas), S05 (bisimulation relations, closed state-set pairs) |
| link.warrant | S04 (basis × trusted base × conditions) |
| node.ontology | S02/02b (typed commitments, generated or hand-written) |
| node.resources.cost_model | S01 F5 (costs only comparable within a declared model) |
| node.provenance | S02b (generated vs researcher-supplied), S01 (translator) |

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H7.1 | One schema represents the real outputs of all three fragments with no fragment-specific top-level fields | **Held**: Spike 01 pipeline (25 nodes, 24 links), Spike 05 LTS pairs, Spike 03 RUP-certified circuits, and Spike 02 inquiries all export and validate |
| H7.2 | Composition follows the relation order and refuses mismatched contracts | **Held**: ext∘task → task; bisim∘trace → trace; task[c1]∘task[c2] refused; adequacy∘adequacy refused ("adequacy is not transitive") |
| H7.3 | A bundle can be re-verified from its contents alone, and tampering is detected | **Held**: every kernel-checked link re-verifies after a JSON round trip; altering one artifact fails its link |

## Findings

**F1. The CSIR's core is the link, not the node.** The charter's §6 list is mostly about what goes *inside* a representation. What the spikes needed most was a typed, protocol-relative, *certified relation between* representations. That fits the charter's own commitment to "plurality with typed interfaces … connect them through declared mappings, not forced identity" (§2). Canonical forms (ROBDD, bisimulation quotient) appear as ordinary nodes linked by certified relations, with no privileged status.

**F2. Empirical links are first-class but do not compose.** "Model M is adequate to the world under protocols Π" is a link with an empirical warrant and its evidence attached. `compose` refuses to chain such links, because adequacy is not transitive: M₁ adequate to M₂ and M₂ adequate to W does not make M₁ adequate to W at any useful tolerance. This is §7.3 for the empirical side, which the charter only states for the formal side.

**F3. Re-verification has two tiers, and the bundle says which.** Kernel-checked links are re-checked from the bundle alone. Empirical links can be audited (protocol, data and uncertainty are present) but not re-derived without new data. `recheck` reports "not kernel-checkable: empirical" rather than pretending to verify them. This matches charter §12.2: "No test-suite result is presented as universal proof."

**F4. The validator enforces honesty at the schema level.** It rejects:
- a kernel-checked warrant without a certificate;
- costs without a cost model;
- a relation applied to the wrong kind of artifact;
- a task relation without a care set;
- links without warrants.

Each of these was a mistake the spikes either made or explicitly guarded against.

## Gaps

- No migration machinery yet (charter §13.19 asks for versioned migrations); this is v0.1.
- There is no relation between a causal model and an executable artifact (e.g. "this circuit implements this model's decision rule"). That bridge, from Layer J translation to world-models, is the obvious next integration step.
- The relation registry is closed (code). An extensible registry with declared inclusion axioms, each axiom itself a ledger claim, would make the order auditable.
