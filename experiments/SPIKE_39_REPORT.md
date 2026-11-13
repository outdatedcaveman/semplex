# Spike 39: Statistical lift (C1), grokking delay (H-C), and n=5 depth-3 certificates (H-E)

> **Provenance (added at merge, 2026-11-13).** Written and run by Gemini on `master` as *Spike 13*; renumbered to Spike 39 because Spikes 11–16 were already taken on the research branch. Its script and result file names keep the original number (code frozen; not renamed). **Not pre-registered:** this report and its results were committed together (AGENTS.md rule 1), so every verdict below is exploratory. Claim numbers P058–P078 in the original were renumbered to P131–P151.


**Date:** 2026-11-13 · **Status:** complete · **Script:** `experiments/spike13_c1_hc_he.py` · **Results:** `experiments/results/spike13_c1_hc_he.json`

## Results

### C1: Statistical lift on noisy worlds (`cerp/epistemics`)
- Swept `n_per` $\in \{200, 600, 1200\}$ and $\alpha \in \{0.005, 0.05\}$ across `latent_causal` and `latent_confounded` (4 seeds each = 8 runs per cell, 48 runs total).
- Across all 48 runs: **0 truth rejections** (`truth_rejection_rate = 0.0`) and **24 `EMPIRICALLY-SUPPORTED` answers per cell**, confirming that calibrated adequacy preserves `EmpSurvivors hstar` even at `n_per = 200`.

### H-C: Grokking delay at 6 inputs
- Planted 6-input XOR-of-halfspaces on 32/64 care points (`H=12`, `wd=0.05`, `steps=600`, 8 seeds per scale).
- `n_fit = 8/8` at every scale (`mean_t_fit`: `37.5` at `0.5`, `47.5` at `1.0`, `60.0` at `1.5`, `85.0` at `2.0`), but **`n_grokked = 0/8`** within 600 steps (budget too short for the grokking transition on this 6-input target).

### H-E: 5-input depth-3 candidates vs two-halfspace lower bound
- Sampled 300 random 5-input depth-3 circuits (`(h1_0 & h1_1) ^ h1_2`), yielding **289 distinct functions**.
- **92 of 289** were **certified not realizable by 2 halfspaces** (`bounds.not_two_halfspaces_cert(5, f, kmax=2)`).
