# semplex: Canonical Epistemology Research Program (CERP)

A working implementation track for the research charter **"Canonical Epistemology, Natural Semantics, Ontology, and Verified Computational Translation"** (`charter/CHARTER_v0.1.md`).

The charter describes a discipline that studies what exists, how it can be known, how representations get meaning and are tested against reality, and how computational content can be compared, translated and optimized across substrates, all with independently checkable guarantees.

We build toward it **agilely**. Each step is a thin end-to-end *spike* that tests specific charter assumptions against running code. Each spike reports which assumptions held, broke or sharpened, and that verdict feeds back into the charter. See `ROADMAP.md` and `decisions/ADR-0001`.

## Status

**Spike 01 is done**: a formal vertical slice on finite Boolean functions, with three substrates (functional expressions, circuits, DFAs), canonical forms, task-relative minimal sufficient representations, untrusted translators, an independent trusted kernel, Pareto resource reports and an enforced claims ledger. Findings are in `experiments/SPIKE_01_REPORT.md`.

**Spike 02 is done**: a world-facing sandbox. A hidden world is reachable only through observation and intervention protocols, and an agent holds four rival ontologies, chooses experiments by information gain, tests predictions on fresh data, records typed ontology revisions, and abstains where evidence underdetermines. Across 900 answers it gave **no wrong answer labeled EMPIRICALLY-SUPPORTED**, including when the true ontology was missing from its candidates. Findings are in `experiments/SPIKE_02_REPORT.md`.

**Proposed next: Spike 02b**, ontology *generation* when the candidate set is refuted (see `ROADMAP.md`).

## Run it

```bash
pip install pytest
python -m pytest -q                                   # 49 tests
python -m cerp.demo                                   # spike 01: redundant-sensor alarm, full ledger
python -m cerp.epistemics.demo latent_confounded all  # spike 02: watch an inquiry into a hidden world
python -m experiments.spike01                         # -> experiments/results/spike01.json
python -m experiments.spike02                         # -> experiments/results/spike02.json (~3 min)
```

## Layout

| Path | Contents |
|---|---|
| `charter/` | The foundational brief (original .docx and markdown conversion) |
| `cerp/kernel.py` | **Trusted** verification kernel: stdlib only, independent interpreters |
| `cerp/` (rest) | Untrusted machinery: semantics, substrates, BDD canonicalization, translators, sufficiency, resources, ledger, pipeline |
| `cerp/epistemics/` | Spike 02: causal Bayes nets with latents, sandbox worlds (ground truth, agent may not import), rival ontologies, the inquiry loop |
| `tests/` | Correctness and adversarial tests, including charter §12.1 criteria |
| `experiments/` | Spike experiments, reports and raw results |
| `claims/REGISTER.md` | Program-level claims, with honest status |
| `decisions/` | Architecture decision records |
| `ROADMAP.md` | Spike protocol and sequence |

## The one rule

Nothing is called *proved*, *canonical*, *optimal*, *verified* or *grounded* without a stated scope and a warrant of the right kind. In code, the ledger refuses to record proof status without a kernel-minted verdict, and a derived claim can never be stronger than its weakest dependency.
