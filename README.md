# semplex: Canonical Epistemology Research Program (CERP)

A working implementation track for the research charter **"Canonical Epistemology, Natural Semantics, Ontology, and Verified Computational Translation"** (`charter/CHARTER_v0.1.md`).

The charter describes a discipline that studies what exists, how it can be known, how representations get meaning and are tested against reality, and how computational content can be compared, translated and optimized across substrates, all with independently checkable guarantees.

We build toward it **agilely**. Each step is a thin end-to-end *spike* that tests specific charter assumptions against running code. Each spike reports which assumptions held, broke or sharpened, and that verdict feeds back into the charter. See `ROADMAP.md` and `decisions/ADR-0001`.

## Status

**Spike 01 is done**: a formal vertical slice on finite Boolean functions, with three substrates (functional expressions, circuits, DFAs), canonical forms, task-relative minimal sufficient representations, untrusted translators, an independent trusted kernel, Pareto resource reports and an enforced claims ledger. Findings are in `experiments/SPIKE_01_REPORT.md`.

**Spike 02 is done**: a world-facing sandbox. A hidden world is reachable only through observation and intervention protocols, and an agent holds four rival ontologies, chooses experiments by information gain, tests predictions on fresh data, records typed ontology revisions, and abstains where evidence underdetermines. Across 900 answers it gave **no wrong answer labeled EMPIRICALLY-SUPPORTED**, including when the true ontology was missing from its candidates. Findings are in `experiments/SPIKE_02_REPORT.md`.

**Spikes 02b, 03, 04, 05 and 07 are done:**
- **02b, ontology generation:** after refuting its candidates, the agent proposes new ontologies constrained by its own measurements and validates them on fresh data. The truth was recovered in 40/40 runs.
- **03, proof-carrying equivalence:** RUP certificates certify n=64 circuit equivalences in milliseconds, past the exhaustive wall.
- **04, structured warrants:** status is a partial order, and labels are a projection of it.
- **05, stateful systems:** equivalence is protocol-indexed; trace ≠ bisimulation, and the difference is observable in a context.
- **07, CSIR v0.1:** one schema across all fragments, with certified links re-verifiable from the bundle alone.

**Spike 06 is done**: the kernel's deciders are *proved* correct in Lean 4, and concrete claims are checked by Lean's kernel through an audited bridge.

**The theory: [`THEORY.md`](THEORY.md).** Protocol-Frame Theory unifies the spikes. Its 11 theorems are machine-checked in `proofs/lean/Theory.lean`:
- representation, inquiry and testing are one hitting-set problem;
- canonical objects are relative to observational power;
- minimal representations are unique exactly when every distinction has a decisive protocol, and can fail to exist at all for tail properties;
- honest abstention is sound and never flips;
- the ledger's weakest-link rule is the optimal safe rule.

**Spike 08 is done: a verifiable periodic table of circuits** (`atlas/`, `experiments/SPIKE_08_REPORT.md`). For strictly layered threshold networks on up to 4 inputs, every function class has an exact minimum neuron count with a kernel-verified witness circuit, and a table-driven compiler returns provably optimal task circuits.

**Spike 08b** hardens it: kernel-checked lower-bound certificates, tables for skip-connection and ReLU families, weight-space geometry, and resumable overnight jobs (`python -m cerp.crunch`). Literature notes: `charter/LITERATURE_ATLAS.md`.

**Spike 09** trains about 27,000 small real-valued networks against the table: on underspecified tasks, gradient descent picks a table-cheapest function in 88–95% of runs, but different seeds find different circuits (`experiments/SPIKE_09_REPORT.md`).

Citations are verified in `charter/BIBLIOGRAPHY.md`.

## Run it

```bash
pip install pytest numpy ortools
python -m pytest -q                                   # 86 tests (Lean tests need CERP_LEAN=/path/to/lean)
python -m cerp.demo                                   # spike 01: redundant-sensor alarm, full ledger
python -m cerp.epistemics.demo latent_confounded all  # spike 02: watch an inquiry into a hidden world
python -m experiments.spike01                         # -> experiments/results/spike01.json
python -m experiments.spike02                         # -> experiments/results/spike02.json (~3 min)
python -m experiments.spike02b                        # ontology generation (~3 min)
python -m experiments.spike03                         # proof-carrying equivalence (~15 min)
python -m experiments.spike04                         # warrant structure in real ledgers
python -m experiments.spike05                         # LTS equivalence hierarchy
python -m experiments.spike08                         # periodic table of circuits + compiler v1 (~2 min, needs numpy)
```

## Layout

| Path | Contents |
|---|---|
| `charter/` | The foundational brief (original .docx and markdown conversion) |
| `cerp/kernel.py`, `cerp/kernel_lts.py` | **Trusted** kernels: stdlib only, independent interpreters, exhaustive decision, RUP checking, LTS certificate checks |
| `cerp/` (rest) | Untrusted machinery: semantics, substrates, BDD canonicalization, translators, sufficiency, resources, ledger, pipeline |
| `cerp/epistemics/` | Spikes 02/02b: causal Bayes nets with latents, sandbox worlds (ground truth, agent may not import), rival ontologies, the inquiry loop, ontology generation |
| `cerp/sat.py`, `cerp/lts.py`, `cerp/csir.py` | Spikes 03, 05, 07: untrusted CDCL solver, LTS algorithms, CSIR schema |
| `cerp/atlas.py`, `atlas/` | Spike 08: circuit atlas builder and compiler; the generated tables |
| `csir/examples/` | Example CSIR bundles from three fragments |
| `proofs/lean/` | Lean 4 proofs: kernel deciders (`Cerp.lean`) and the theory (`Theory.lean`), with axiom audits |
| `THEORY.md` | Protocol-Frame Theory: definitions, theorems, conjectures |
| `tests/` | Correctness and adversarial tests, including charter §12.1 criteria |
| `experiments/` | Spike experiments, reports and raw results |
| `claims/REGISTER.md` | Program-level claims, with honest status |
| `decisions/` | Architecture decision records |
| `ROADMAP.md` | Spike protocol and sequence |

## The one rule

Nothing is called *proved*, *canonical*, *optimal*, *verified* or *grounded* without a stated scope and a warrant of the right kind. In code, the ledger refuses to record kernel-checked status without a kernel-minted verdict, and every claim carries a structured warrant (methods, trusted base, named premises). A derived claim can never be stronger than what it rests on.
