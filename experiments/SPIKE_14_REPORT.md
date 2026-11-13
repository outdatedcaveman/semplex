# Spike 14: Non-synthetic case study (Quinlan 1986 PlayTennis)

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
