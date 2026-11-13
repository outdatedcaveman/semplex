# Spike 11: Volume law for mechanisms (H-B) and width compression (H-D)

**Date:** 2026-11-13 · **Status:** complete · **Script:** `experiments/spike11_hb_hd.py` · **Results:** `experiments/results/spike11_hb_hd.json`

## Questions

1. **H-B (Volume law for mechanisms):** Among the minimal determining first-layer circuits ("isomers") of the *same* Boolean function $f$, does AdamW land on each isomer with frequency correlated with its weight-space volume?
2. **H-D ("Coarser, not folded", Cammarata):** When hidden width $H$ is reduced below a function's minimum width $w^*(f)$, do trained hidden units become *clean* members or *coarsenings* (cell unions) of a minimal determining set $\Omega^*$, or *folded* mixtures that split cells of every $\Omega^*$?

## Method

- **H-B on 3 inputs:** Exact integer weight-grid volume (`cerp/geometry.py`, $W=1$, $h=2$, 177,147 points) compared against 200 AdamW seeds ($H=4$, 300 steps) across all multi-isomer $w^*=2$ elements (5 elements with $\ge 2$ isomers).
- **H-B on 4 inputs:** Gaussian initialization prior volume (100,000 random `cerp/train.py` nets at $H=8$, `scale=0.5`) against 10 representative $w^*=2$ elements.
- **H-D on 4 inputs:** 10 elements ($4$ with $w^*=2$, $6$ with $w^*=3$) trained at widths $H \in \{1, 2, 3, 4, 6, 8, 12, 16\}$ (20 seeds each). Each non-constant hidden unit $u$ is classified as:
  - **clean:** $u$ (up to complement) belongs to some minimal determining set $\Omega^*$ of $f$;
  - **coarsening:** $u$ is not clean, but some $\Omega^*$ determines $u$ (exact union of $\Omega^*$-cells);
  - **folded:** $u$ splits at least one cell of every known $\Omega^*$.

## Results (`experiments/results/spike11_hb_hd.json`)

### H-B: Isomer frequency vs weight-space volume

| Setting | Elements | Pooled Spearman $\rho$ | Pooled Pearson $r$ | Top-isomer match |
|---|---|---|---|---|
| $n=3$ exact grid ($W=1$) vs AdamW | 5 | **0.391** | **0.666** | 3 / 5 (**60.0%**) |
| $n=4$ Gaussian prior (100k samples, `scale=0.5`) | 0 | — | — | 0 hits on the 10 sampled exhibits |

### H-D: Unit classification by width regime

| Regime | Fit rate | Active units | Clean | Coarsening | Folded | Constant |
|---|---|---|---|---|---|---|
| `below` ($H < w^*$) | 0.9% | 440 | 79.3% | 9.3% | **11.4%** | 0.0% |
| `at` ($H = w^*$) | 37.5% | 520 | 75.4% | 10.4% | **14.2%** | 0.0% |
| `above` ($H > w^*$) | 94.1% | 9,388 | 58.6% | 7.9% | **33.6%** | 0.6% |

## Verdicts

- **H-B partially supported (moderate, not strong):** On 3 inputs with exact $W=1$ grid volume, isomer frequency correlates positively with grid volume ($r = 0.666$, $\rho = 0.391$, top-isomer match 3/5). On 4 inputs, 100k unconditioned Gaussian samples at `scale=0.5` yielded 0 hits on the 10 target exhibits, so $n=4$ mechanism volume requires larger sampling or NPN-class pooling.
- **H-D held (sharpened):** When width is squeezed ($H < w^*$ and $H = w^*$), **88.6%** and **85.8%** of active units remain clean members or exact coarsenings of a minimal determining set (only 11.4% / 14.2% folded). Counter-intuitively, folded units *increase* to **33.6%** at $H > w^*$, where excess capacity allows redundant units to take mixed orientations alongside clean ones.

## Gaps

- $n=3$ grid used $W=1$; larger $W$ or NPN-pooled $n=4$ sampling is needed to settle H-B at $n=4$.
- For $w^*=3$ in H-D, $\Omega^*$ is collected from the atlas witness plus $H \ge 8$ runs rather than exhaustive $\binom{940}{3}$ search.
