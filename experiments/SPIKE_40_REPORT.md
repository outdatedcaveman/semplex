# Spike 40: Non-synthetic case study (Quinlan 1986 PlayTennis)

> **Provenance (added at merge, 2026-11-13).** Written and run by Gemini on `master` as *Spike 14*; renumbered to Spike 40 because Spikes 11–16 were already taken on the research branch. Its script and result file names keep the original number (code frozen; not renamed). **Not pre-registered:** this report and its results were committed together (AGENTS.md rule 1), so every verdict below is exploratory. Claim numbers P058–P078 in the original were renumbered to P131–P151.


**Date:** 2026-11-13 · **Status:** complete · **Script:** `experiments/spike14_real_case_study.py` · **Results:** `experiments/results/spike14_real_case_study.json`

## Method
- Fit a causal Bayes net (`cerp/epistemics/bayesnet.py`) on the 14 real observations of Quinlan (1986) PlayTennis binarized to 4 features (`Sunny`, `Hot`, `HighHum`, `Windy` $\to$ `Play`).
- Distilled the Bayes-optimal decision rule to a canonical F0 expression + gate-level circuit via `csir.distill_causal_rule`, validated and re-checked the CSIR bundle, and looked up the exact minimum threshold-neuron count in `atlas.build_all(4)[4]`.

## Results
- **Log-likelihood:** `-42.2141`
- **CSIR validation:** `[]` (0 structural errors)
- **CSIR recheck:** link 0 (`distills`) `not kernel-checkable: empirical`; link 1 (`extensional`) **`verified`**
- **Distilled gate circuit cost:** `8 gates`, `depth 5` (truth table `32607`)
- **Atlas minimum threshold neurons:** **`1`** (the distilled rule is a single threshold function)
