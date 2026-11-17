# Spike 64: Is there a global frame for semantic space? Holonomy of model-to-model alignments

**Date:** 2026-11-17 · **Status:** pre-registered (no run) · **Follows:** Spike 61 (P191: lexicons share shape but not axes), `charter/FOUNDATIONS.md` §12.2 (sheaf reading), C34.

## Question

Each model is a local chart of a shared semantic shape, defined up to rotation. Pairwise alignments act as transition functions.
- If composing alignments around a triangle of models returns the identity (up to estimation noise), the models fit one **global frame**: a shared basis exists in principle, and Spike 61's failure to find shared atoms was about dictionaries.
- If it does not, the frame bundle has nontrivial **holonomy**: there is no global frame, and only invariants glue.

## Data and method

**Data.** Spike 61's rows: 14 models' input embeddings for 6,163 shared words, centred and normalised; each reduced to its top 128 principal components.

**Alignment.** For each ordered pair (a, b), the orthogonal Procrustes rotation R_ab (128 × 128) minimises ‖X_a R − X_b‖_F over a fixed random 80% of words (seed 6,400).

**Holonomy** of a triangle (a, b, c): h = ‖R_ab R_bc R_ca − I‖_F / √(2·128). A random rotation gives about 1.

**Noise baseline.**
- For each pair, fit R_ab separately on two disjoint random halves of the fit words. The alignment noise is δ_ab = ‖R⁽¹⁾ − R⁽²⁾‖_F / √(2·128).
- For a triangle, the noise scale is ν = √(δ_ab² + δ_bc² + δ_ca²), and the ratio is ρ = h / ν.

**Fit quality.** R² = 1 − ‖X_a R_ab − X_b‖² / ‖X_b‖² on the held-out 20% of words.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H64.1 | **No global frame:** holonomy exceeds alignment noise | ρ ≥ 2 in ≥ 80% of the 364 triangles | ρ ≤ 1.2 in ≥ 50% |
| H64.2 | **Shape shared nonetheless:** rotations transfer substantial structure | median held-out R² ≥ 0.30 over the 182 ordered pairs | median < 0.10 |

Anything else is *neither*.

**Reported without criteria:**
- holonomy as a function of the models' CKA;
- whether holonomy concentrates in low- or high-variance components (per-component diagonal of R_ab R_bc R_ca).

## What this cannot show

- Procrustes alignment is linear and global. A nonlinear frame might glue where the linear one does not.
- Static input embeddings only.

## Commands

```
python -m experiments.spike64 run
```

## Results

(Not run.)
