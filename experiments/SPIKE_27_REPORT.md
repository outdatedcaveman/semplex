# Spike 27: Is positive homogeneity what removes the tilt? (C12)

**Date:** 2026-11-12 · **Status:** complete (pre-registered in cd09ec0; results below) · **Follows:** Spike 24 F3 (post hoc: the only activations without the information tilt, ReLU and leaky ReLU, are exactly the positively homogeneous ones)

## Conjecture C12

The information tilt λ (unit-level law P(t | g) ∝ Ω(t)^γ · exp(λ·I(t; g))) is suppressed when the activation is positively homogeneous, φ(cx) = c^k·φ(x) for c > 0. The proposed cause is the per-unit rescaling symmetry (w₁, b₁, w₂) → (c·w₁, c·b₁, c^(−k)·w₂). It lets gradient trade hyperplane sharpness against readout weight, and it couples the two through a conserved balance.

## Design (as Spikes 22 and 24: 128 elements × 40 seeds, width 8, AdamW lr 0.03, wd 0.03, 3,000 steps; fresh seeds)

| Run | Activation | Homogeneous? |
|---|---|---|
| abs | \|x\| (even, degree 1) | yes |
| relu² | max(x, 0)² (degree 2) | yes |
| signed square | x·\|x\| (odd, degree 2) | yes |
| softplus | log(1 + eˣ) (grows linearly) | no |
| ELU | x for x > 0, eˣ − 1 otherwise (linear on the positive side) | no |
| **ReLU-sphere** (intervention) | ReLU, but after every step each unit's (w₁, b₁) is rescaled to its initial norm. This removes the rescaling freedom without changing the function class | ReLU, symmetry removed |

Fit (γ, λ) at step 3,000 with the exact fitter. Runs fitting < 90% of nets are flagged.

## Hypotheses and kill criteria

| # | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H27.1 | Homogeneous activations lack the tilt | λ ≤ 3 for abs, relu² and signed square | any > 5 |
| H27.2 | Non-homogeneous activations have it, even with linear growth | λ ≥ 5 for softplus and ELU | any < 3 |
| H27.3 | **Removing ReLU's rescaling symmetry restores the tilt (causal test)** | λ(ReLU-sphere) ≥ 5 | ≤ 3 |

---

## Results

Exact fits (`cerp/loglin.py`); raw data in `results/spike27_raw/`, fits in `results/spike27.json`. All runs fit ≥ 98% of nets.

| Run | Homogeneous | Fit rate | γ₃₀₀₀ | λ₃₀₀₀ |
|---|---|---|---|---|
| \|x\| | yes | 1.000 | 0.50 | −1.89 |
| ReLU² | yes | 0.982 | 0.81 | 0.43 |
| signed square x·\|x\| | yes | 1.000 | 0.78 | 2.83 |
| softplus | no | 1.000 | 0.85 | 2.02 |
| ELU | no | 1.000 | 0.85 | 5.95 |
| ReLU-sphere | ReLU with rescaling removed | 0.992 | 0.49 | 1.24 |

### Verdicts

| # | Verdict |
|---|---|
| H27.1 | **Held.** All three homogeneous activations have λ ≤ 3 (−1.89, 0.43, 2.83). |
| H27.2 | **Broken.** Softplus is not homogeneous and has λ = 2.02 < 3. ELU has the tilt (5.95). |
| H27.3 | **Broken.** Fixing each ReLU unit's input norm leaves λ at 1.24, the same as plain ReLU (1.19). |

## Findings

**F1. C12 is refuted.** Homogeneity is sufficient to lose the tilt in every case tested, but it is not the cause. A non-homogeneous activation (softplus) also lacks it, and removing ReLU's rescaling symmetry directly does not restore it.

**F2. Running tally of the activation question (Spikes 22, 24, 27).** Fifteen activations so far. Three named mechanisms are refuted: unit movement (C10), oddness or saturation (C11), and homogeneity (C12). The tilt is present for tanh, hardtanh, softsign, arcsinh, sigmoid, clipped ReLU and ELU. It is absent for ReLU, three leaky ReLUs, |x|, ReLU², x·|x| and softplus.

**F3. Exploratory, not pre-registered (computed after seeing these results).** One scalar ranks all 15 activations' tilts with Spearman ρ = 0.84: the share of φ(x)'s variance explained by the side of the hyperplane, R²(φ(x), 1[x > 0]) for x ~ N(0, 2²). Scales 1, 2 and 4 give 0.84, 0.84 and 0.81; 0.5 gives 0.74; s = 2 was picked after looking. At s = 2:
- every activation with the tilt has R² ≥ 0.77, except ELU (0.62, λ 5.95);
- every activation without it has R² ≤ 0.57.

Proposed reading, C13: when a unit's output is mostly *which side* of its hyperplane the input lies on, the readout sees the threshold function t itself, and selection follows t's information about the target. When the output is graded with distance, as for ReLU, what gets selected is the usefulness of the ramp, not t. Spike 28 tests C13 on activations not yet run, with predictions fixed in advance.
