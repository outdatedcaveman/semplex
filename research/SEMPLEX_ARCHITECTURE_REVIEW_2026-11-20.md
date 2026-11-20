# Semplex architecture review — 2026-11-20

**Scope:** architecture-level review based on the current README, charter, THEORY.md, AUDIT.md (2026-11-17), ROADMAP.md, CSIR Spike 07 report, literature review, claims register, and selected core files/tests. This is not a fresh line-by-line audit of every Python module or a rerun of the full test suite.

## Executive assessment

Semplex is already a substantial research platform with a coherent methodological core: untrusted discovery/translation, independent checkers, explicit warrants, protocol-relative semantics, and machine-checkable claims. Its strongest asset is not any single theorem or compiler; it is the discipline of making scope, assumptions, trust base, and failure modes explicit.

Its principal risk is breadth outrunning semantic integration. The project now spans epistemology, causal discovery, circuit synthesis, neural learning, compilation, resource optimization, and Peircean interpretation. Those can belong together, but the common semantic interface must be demonstrated rather than inferred from shared vocabulary.

The 2026-11-17 audit is unusually valuable: it documents 135 passing tests after repairs, 81 audited Lean theorems, and a detailed set of previously reproduced defects. It also explicitly records remaining gaps. Do not let the impressive spike count obscure the distinction between a verified finite fragment and the universal program.

## What is strongest

1. **Trust architecture.** Searchers/solvers/translators are untrusted; small checkers validate certificates. The claims register and warrant discipline are the right basis for high-assurance research.
2. **Protocol-Frame Theory.** The antitone relationship between observational power and indistinguishability, and factorization of determined queries through observational profiles, provide a genuine common language for many fragments.
3. **Adversarial methodology.** The roadmap's prior-art gate, kill criteria, mutation tests, and negative-result acceptance are sound research practices.
4. **CSIR restraint.** Spike 07 tested one schema across fragments and explicitly distinguishes kernel-checkable from empirical links. Its rule of three should remain in force.
5. **Epistemic honesty.** The literature review retracts several premature novelty claims and identifies classical antecedents. Preserve this standard.

## Main architectural risks

### A. Theoretical over-unification

PFT's observational equivalence is powerful, but it is not automatically a theory of all identity, meaning, reference, causal dependence, or ontology. A common interface is not proof that the represented notions are one mathematical object. Each fragment needs an interpretation theorem and a clear boundary.

### B. CSIR trust boundary

AUDIT.md identifies a key issue: CSIR links and the claims register are plain data; validation and rechecking do not automatically guarantee every declared warrant is authentic. Continue moving strong claims behind certificate verifiers, and make unsupported warrant labels fail closed.

### C. Translation correctness and semantic alignment

The audit records earlier cases where Lean checked a translation of the compiled output rather than the original specification, and a Python threshold-net rendering gap. Those were partly fixed; the remaining TNode round-trip gap is explicitly open. Treat end-to-end source-to-target semantic alignment as a priority, not a documentation detail.

### D. Trusted-base growth

The Python kernels have grown, and the audit notes the 300-line trigger in ADR-0002 has passed. More importantly, every additional trusted checker increases the assurance burden. Prefer small composable verifiers, proof-producing untrusted search, and a clearly enumerated trusted base.

### E. Evidence and theorem provenance

The README/ROADMAP/claims register have previously drifted. The current audit fixed several mismatches, but manual status propagation remains fragile. Add a machine-readable theorem/experiment manifest from which the README, audit tables, and claim statuses can be checked or generated.

### F. Resource semantics

The project has resource reports and lower bounds, but the meaning of a cost remains model-dependent. Treat resources as typed quantities with declared units, scope, composition law, and uncertainty. Do not combine gate count, latency, memory, energy, and proof-checking cost into a single scalar without an explicit objective and exchange rates.

### G. Ontology/epistemology boundary

The epistemic sandbox's results are conditional on candidate spaces, interventions, statistical assumptions, and closed-world premises. A formal determinacy theorem does not establish that the hypothesis set is complete or that the ontology is true. The audit and literature review already recognize this; keep it explicit in CSIR and published claims.

## Recommended architecture changes

### 1. Add a transformation contract before expanding CSIR

For every abstraction/translation/quotient, specify:
- source and target semantic domains;
- protected observations/queries;
- protected operations and contexts;
- exact, approximate, probabilistic, or trace-based preservation relation;
- resource model and permitted loss;
- certificate and independent verifier;
- explicit non-guarantees.

This is the DAP contract. Keep it as a research-level schema first; do not mutate CSIR v0.1 until at least three fragments need the same fields.

### 2. Separate identity notions in the core vocabulary

Do not use “equivalent,” “identical,” “same,” and “interchangeable” synonymously. At minimum distinguish:
- syntactic/definitional equality;
- logical equality with substitutivity;
- identity types/paths;
- isomorphism/equivalence;
- observational/contextual equivalence;
- bisimulation/trace equivalence;
- task equivalence;
- occurrence/provenance identity;
- persistence identity across time.

Each relation needs its own type, scope, and admissible composition rules.

### 3. Build the indexed-context layer before claiming a fibration

Represent modules as contexts with fibers of states/entities/claims and reindexing maps. Prove identity/reindexing coherence, then construct the Grothendieck total category and cartesian liftings. Add descent/gluing only after the overlap conditions are explicit.

### 4. Make CSIR transformation-aware, not merely relation-aware

The current link-centered schema is valuable. The next extension may require transformation artifacts carrying source/target maps, semantics, certificates, and reconstruction/loss information. Derive this from at least three real use cases; do not pre-design a universal schema.

### 5. Preserve the proof/empirical split

A theorem about finite models, an exact finite search result, a randomized experiment, a statistical estimate, and a real-world causal claim are not interchangeable. Keep each status tied to its assumptions and trusted base.

### 6. Narrow the active research portfolio

Maintain one foundational workstream and a small number of vertical spikes. For the current work, prioritize:
- DAP and identity/occurrence/contraction distinctions;
- Tarski satisfaction as a canonical finite semantic example;
- the four-system comparison;
- source-to-target certificate integrity;
- one genuine world-facing validation case.

Pause new neural/circuit subprojects unless they directly test a declared foundational claim or close an existing proof obligation.

## Specific gaps to close from the existing audit

1. Finish the TNode source-render round-trip and make Lean verify the exact Python-emitted net.
2. Resolve the remaining quantitative error-bound semantics for continuous compilation.
3. Connect the Markov-kernel data-processing result to the actual stochastic-LTS bound, or narrow the claim.
4. Finish the missing reports for Spikes 12, 13b, 14b, and 15.
5. Revisit ADR-0002's trusted-kernel size trigger.
6. Correct/qualify the novelty language in Literature Review §3c as the audit recommends.
7. Keep the roadmap and claim register generated or cross-checked against test/proof manifests.

## Research strategy for novelty

For every candidate new theorem:
1. State exact definitions and hypotheses.
2. Search the nearest literatures before implementation.
3. Identify whether it is a theorem, a re-expression, a finite generalization, a mechanization, or an empirical finding.
4. Produce a minimal counterexample to the strongest plausible false generalization.
5. Mechanize the theorem and audit axioms.
6. Independently test the implementation against the formal semantics.
7. Only then write the novelty claim.

A new mathematical result is welcome, but it must survive comparison with model theory, proof theory, set theory, categorical logic, HoTT, programming-language semantics, and information theory. The aim is not to make Semplex sound unprecedented; it is to make its actual contributions difficult to dismiss.

## Overall verdict

Semplex has a strong and unusually disciplined research infrastructure. It is not yet a universal epistemology, a complete ontology, or a new foundation of mathematics. Its most defensible present contribution is a verified, protocol-relative framework that connects representation, observation, task sufficiency, testing, and evidence status across several finite computational fragments.

The next leap should be depth, not breadth: prove the preservation calculus, formalize contextual identity with actual indexed/fibrational structure, and show exactly what this adds beyond established quotient, linear-logic, type-theoretic, and categorical machinery.
