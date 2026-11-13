# Spike 41: Ur-Compiler benchmarks (Gemini's "Spike 15")

> **Provenance (added at merge, 2026-11-13).** Gemini named this work "Spike 15" on `master`. It wrote no report; the results are in `experiments/results/spike15_ur_compiler.json` and the script is `experiments/spike15_ur_compiler.py` (file names unchanged). **Not pre-registered**, so it is exploratory.

- **Claim:** P141. Profile-factor compilation reduces gate counts relative to a flat BDD.
- **What the results file shows:** the compositional circuit needs 0.23–0.66× the gates of a flat BDD on the listed benchmarks (e.g. parity_8: 43 vs 191 gates). The first compile (parity_6) took 290 s, before the persistent atlas cache; the others took milliseconds.
- **Caveat:** the baseline is a BDD-to-gates translation, not a minimum circuit. The ratios show that composition helps against that baseline, not that the output is near-optimal.
