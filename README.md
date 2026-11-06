# semplex: Canonical Epistemology Research Program (CERP)

A working implementation track for the research charter **"Canonical Epistemology, Natural Semantics, Ontology, and Verified Computational Translation"** (`charter/CHARTER_v0.1.md`).

The charter describes a discipline that studies what exists, how it can be known, how representations get meaning and are tested against reality, and how computational content can be compared, translated and optimized across substrates, all with independently checkable guarantees.

We build toward it **agilely**. Each step is a thin end-to-end *spike* that tests specific charter assumptions against running code. Each spike reports which assumptions held, broke or sharpened, and that verdict feeds back into the charter. See `ROADMAP.md` and `decisions/ADR-0001`.

## Status

**Spike 01 is done**: a formal vertical slice on finite Boolean functions, with three substrates (functional expressions, circuits, DFAs), canonical forms, task-relative minimal sufficient representations, untrusted translators, an independent trusted kernel, Pareto resource reports and an enforced claims ledger. Findings are in `experiments/SPIKE_01_REPORT.md`.

**Next: Spike 02**, a world-facing sandbox with rival ontologies, measurement and ontology revision.

## Run it

```bash
pip install pytest
python -m pytest -q             # 35 tests
python -m cerp.demo             # worked example: redundant-sensor alarm, full ledger
python -m experiments.spike01   # reproducible measurements -> experiments/results/spike01.json
```

## Layout

| Path | Contents |
|---|---|
| `charter/` | The foundational brief (original .docx and markdown conversion) |
| `cerp/kernel.py` | **Trusted** verification kernel: stdlib only, independent interpreters |
| `cerp/` (rest) | Untrusted machinery: semantics, substrates, BDD canonicalization, translators, sufficiency, resources, ledger, pipeline |
| `tests/` | Correctness and adversarial tests, including charter §12.1 criteria |
| `experiments/` | Spike experiments, reports and raw results |
| `claims/REGISTER.md` | Program-level claims, with honest status |
| `decisions/` | Architecture decision records |
| `ROADMAP.md` | Spike protocol and sequence |

## The one rule

Nothing is called *proved*, *canonical*, *optimal*, *verified* or *grounded* without a stated scope and a warrant of the right kind. In code, the ledger refuses to record proof status without a kernel-minted verdict, and a derived claim can never be stronger than its weakest dependency.
