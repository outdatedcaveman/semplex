# Program-level claims register

These are claims *about the research program and its artifacts*, held to the same discipline the system applies to its own outputs (charter §13.20). Per-run, machine-generated ledgers come from `cerp.ledger.Ledger` (see `python -m cerp.demo`).

| ID | Statement | Status | Scope / assumptions | Evidence | Depends on | Counterarguments / caveats | Next action |
|---|---|---|---|---|---|---|---|
| P001 | ROBDD under a fixed order is a normal form for F0 (idempotent; equal iff extensionally equivalent) | PROVED (literature) | Fixed variable order | Bryant 1986 (*to verify*) | | Our *implementation* is only tested (P002) | Verify citation |
| P002 | `cerp/bdd.normal_form` implements P001 correctly | EMPIRICALLY-SUPPORTED | Seeded random exprs, ≤6 vars | `tests/test_canonical.py` (7,140 pairs) | P001 | Not proved; Python and toolchain trusted | Spike 06 |
| P003 | With full care, the minimal sufficient variable set is unique and equals support(f) | PROVED (informal sketch) | Finite Boolean f | Sketch in `cerp/sufficiency.py`; random tests | | Informal proof, not mechanized | Mechanize in Spike 06 |
| P004 | Minimal sufficient sets = minimal transversals of the conflict hypergraph (= rough-set reducts) | PROVED (informal) + literature | Finite tasks | Definition unfolding; Skowron & Rauszer 1992 (*to verify*) | | | Verify citation |
| P005 | Multiplicity of minimal sufficient sets rises sharply with domain restriction and correlation | EMPIRICALLY-SUPPORTED | Spike 01 workload only | `experiments/results/spike01.json` E1 | P003 | Random care sets are not natural task domains | Spike 02 with a structured world |
| P006 | Substitutable variables signal redundant channels of a shared latent quantity | CONJECTURE | | Spike 01 F4 (suggestive) | P005 | May fail under noise, or for non-equality correlations | Test in Spike 02 (H2.3) |
| P007 | Naive don't-care filling often makes task realizations *worse* than exact ones | EMPIRICALLY-SUPPORTED | Spike 01 workload, gate count | E1_E2 (55% worse at 90% density) | | Cost model is gate count only | |
| P008 | Including exact realizations in task fronts guarantees task fronts never lose to exact fronts | PROVED (trivial: ≡_ext ⊆ ≡_T) + tested | Any care set | `test_task_front_never_worse_than_exact_front` | | | |
| P009 | Exhaustive verification is infeasible beyond n≈20–24 on this kernel | EMPIRICALLY-SUPPORTED | Single machine, CPython | E5 timings (noisy) | | Order-of-magnitude only | Spike 03 |
| P010 | The charter §10 status labels do not form a total order | CONJECTURE (strong) | | F7 analysis | | Could be repaired by a convention | Spike 04 |
| P011 | The §9 pseudocode is absent from the source .docx v0.1 | EMPIRICALLY-SUPPORTED | | Inspected `word/document.xml` | | | Ask authors whether a draft exists |
