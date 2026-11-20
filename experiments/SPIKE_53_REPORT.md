# Spike 53: Does a concept family's symmetry group fix its geometry, in model weights and in human cortex?

**Date:** 2026-11-16 · **Status:** complete (pre-registered in a754694; results below) · **Follows:** `charter/FOUNDATIONS.md` §8 (conjecture C29, symmetry determines geometry). Third track, concepts outside the Boolean atlas (`experiments/TREE.md`). **Conjecture:** C29.

## Question

C29 says the geometry of a concept family is the representation theory of the family's statistical symmetry group G. For example:
- a cyclic family (ℤ/n) gives a circle;
- a taxonomy (a product of symmetric groups acting within categories) gives block structure;
- a product of independent factors (G₁ × G₂) gives a **tensor product**, so the interaction of the two factors carries each factor's own geometry.

This spike tests the three rows on two substrates, using public data only and without running any model:

- **Weights.** The input-embedding and (where untied) output-embedding matrices of 14 open language models. Only the rows needed are read, directly from the published safetensors files with HTTP range requests (`cerp/hfrows.py`).
- **Brains.** The THINGS-fMRI single-trial responses (Hebart, Contier et al. 2023, eLife; 3 subjects, 720 training concepts × 12 images): ventral and lateral occipito-temporal object cortex.

## Prior art and what is new

- **Circles for weekdays and months** in model activations, found with sparse autoencoders: Engels et al. 2024 (2405.14860), GPT-2 and Mistral-7B. The circle was derived from co-occurrence symmetry by Karkada et al. (2602.15029). It is disputed: "spokes, not a ring" (2610.37796).
- **Category structure in object cortex** is well known (Kriegeskorte et al. 2008, Neuron). Brain–model alignment on THINGS has been reported before.

H53.1, H53.2 and H53.4 are therefore replications on a new substrate (static weights) or a new statistic. The new tests are:
- **H53.3**, the tensor row. I found no prior test.
- **H53.6b**, whether the structure the brain and the models share is exhausted by the group skeleton.

## Data

**Models (14, ungated):**
- openai-community/gpt2
- EleutherAI/pythia-410m
- EleutherAI/pythia-6.9b
- Qwen/Qwen2.5-0.5B
- Qwen/Qwen2.5-7B
- mistralai/Mistral-7B-v0.1
- allenai/OLMo-2-1124-7B
- HuggingFaceTB/SmolLM2-360M
- tiiuae/falcon-7b
- microsoft/phi-2
- bigscience/bloom-560m
- stabilityai/stablelm-2-1_6b
- 01-ai/Yi-6B
- internlm/internlm2_5-7b

Each model contributes its input embedding, and its output embedding when untied: 24 matrices in all. The tensor names were found from the safetensors headers before registration (no values read).

**Token rule.** A word is used only if `" " + word` is a single token in that model's tokenizer (checked before registration). A family enters a matrix's analysis only if every member is a single token.

**Families:**

| Family | Members | Group |
|---|---|---|
| weekdays | Monday … Sunday | ℤ/7 |
| months | January … December | ℤ/12 |
| month abbreviations | Jan … Dec | ℤ/12 |
| month × form (product) | {January … December} × {full, abbreviation} | ℤ/12 × ℤ/2 |
| weekday × form (product) | {Monday … Sunday} × {full, Mon … Sun} | ℤ/7 × ℤ/2 |

"May" and "March" are ambiguous words. They are kept, and that works against the hypotheses.

**Brain:**
- **Voxels.** The union of the localizer ROIs lLOC, rLOC, IT, lFFA, rFFA, lPPA, rPPA, lEBA, rEBA, lOFA, rOFA, restricted to voxels with test-set noise ceiling `nc_testset` > 10 (from `VoxelMetadata.csv`): 3,288, 2,848 and 1,915 voxels for subjects 1–3.
- **Responses.** Each voxel is z-scored over the 8,640 training trials. A concept's pattern is the mean over its 12 training images.

**Concepts for the hierarchy arm:**
- The THINGS training concepts that have exactly one label in `category27_manual.tsv` (THINGS OSF, jum2f), in categories with at least 8 such concepts.
- The model side uses those concepts whose THINGS `Word` is a single token.

## Statistic

**Geometry.** For a family with vectors x₁ … x_n:
1. Subtract the family mean.
2. Normalise each row to unit length.
3. Take the Gram matrix G.

**Symmetry projection.** For a group G acting on the members, Ĝ averages G over the orbits of off-diagonal index pairs:
- **cyclic:** pairs at the same cyclic distance;
- **hierarchy:** pairs in the same block (category c, category c′). This is the projection onto matrices invariant under permuting concepts within categories.

**R²_G** is the share of the off-diagonal variance of G that Ĝ explains.

**Null.** Members are relabelled at random (10,000 permutations for the families, 2,000 for the hierarchy, seed 5,300), and the p-value is (1 + #{null ≥ observed}) / (1 + N).

**Fourier order.** The eigenvalues of the circulant Ĝ are λ_m for m = 1 … ⌊n/2⌋. A "circle" means λ₁ is the largest.

**Tensor test (product families).**
1. Each token vector is normalised.
2. The vectors are decomposed two-way: x_ij = μ + a_i + b_j + r_ij.
3. Additivity (a direct sum, a "Monday + plural vector" picture) predicts that the interaction r carries no structure from the first factor.
4. The tensor product predicts r_{i,·} = (first-factor representation) ⊗ (centred second factor), so r's Gram over the first factor reproduces the factor's circle.

With two levels r_{i,2} = −r_{i,1}, so the test is the cyclic R² of the rows r_{i,1}, against the same permutation null.

**Cross-substrate agreement (Mantel).** For each (subject, matrix) pair on their common concepts, take the Spearman correlation of the off-diagonal entries of the two Gram matrices. The null permutes concepts on one side (2,000 permutations).
- **Full:** G as is.
- **Residual:** G − Ĝ on both sides, which is the structure beyond the 27-category skeleton.

## Hypotheses and kill criteria

Here a *case* is one (matrix, family) pair that passes the token rule.

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H53.1 | Cyclic families have cyclic geometry in static weights | R²_cyc has p < 0.01 in ≥ 75% of cases (weekdays, months, month abbreviations) | < 50% |
| H53.2 | …and it is a circle (lowest Fourier mode), not "spokes" | λ₁ is the largest in ≥ 75% of cases | < 50% |
| H53.3 | **Product families are tensor products** | the interaction rows r_{i,1} have cyclic R² with p < 0.01 in ≥ 50% of product cases | ≤ 20% |
| H53.4 | Object cortex has the taxonomy's block geometry | R²_block p < 0.001 in every available subject | p ≥ 0.01 in ≥ 2 subjects |
| H53.5 | Static weights have the taxonomy's block geometry | R²_block p < 0.001 in ≥ 75% of matrices | < 50% |
| H53.6a | Brain and weights share geometry | full Mantel p < 0.01, ρ > 0, in ≥ 75% of (subject, matrix) pairs | < 50% |
| H53.6b | The shared grain is exhausted by the group skeleton | residual Mantel p ≥ 0.01 in ≥ 50% of pairs | residual p < 0.01, ρ > 0, in ≥ 75% of pairs |

Anything else is *neither*.

**Reading for C29:**
- C29's derived row (cyclic) is supported if H53.1 and H53.2 hold.
- Its sharpest prediction (tensor) is supported if H53.3 holds, and refuted if H53.3 is broken. A broken H53.3 would mean composition in weights is additive (direct sum), not tensor.
- H53.6b broken means the "grain" shared by brains and models is finer than the labelled taxonomy, so the symmetry group that C29 needs is not the one the labels give.

**Guards:**
- No verdict on H53.1–H53.2 with fewer than 30 cases, or on H53.3 with fewer than 15.
- No verdict on a (subject, matrix) pair with fewer than 100 common concepts.
- A subject whose data cannot be downloaded is reported missing; H53.4 is then judged on the available subjects (at least 2, else no verdict).

**Reported without criteria:**
- the interaction share ‖r‖² / ‖x − μ‖² against its null value (m−1)(n−1)/(mn−1);
- the cyclic R² of the additive part a_i;
- input versus output embeddings;
- R² by model size.

## What this cannot show

Static embeddings are the model's lexicon, not its contextual representations. The circles Engels et al. found are in activations. A failure here is a failure in weights only. Brain patterns are from images, not words. The cross-substrate test compares visual-object cortex with lexical weights.

## Procedure change before any brain analysis (recorded)

Storing a 15 GB file per subject would use the whole disk. The brain data are therefore streamed instead.

1. Two metadata-only passes over subject 1's file located its HDF5 layout (pandas fixed format):
   - `block0_values` is one contiguous row-major float32 array, 211,339 voxels × 9,840 trials, at byte 7,392,223,744;
   - it ends 2,568 bytes before the end of the file;
   - rows are in `voxel_id` order (checked equal to row number).
2. One pass per subject then keeps only the selected voxels' rows (about 130 MB). The file is never written to disk.
   - Subjects 2 and 3 are assumed to share the layout, with the offset computed from file size and voxel count.
   - Trial columns are assumed to be in `StimulusMetadata` order, because the column labels are pickled and not readable from the metadata alone.

**New guard (applies to every subject).** Before any analysis, odd and even repeats of the 100 test images must correlate more with the same image than with different images by at least 0.05. Otherwise the subject is excluded as misaligned.

**Second fix, also before any analysis.** Subject 2 failed the guard: same 0.396 against different 0.395. The guessed offset was wrong; subject 2's array does not end at the same distance from the end of the file.
- The extractor now reads each subject's own offset during the stream. The root symbol table in the first MB gives the address of the dataset's object header, and that window is captured before the array begins.
- On subject 1 this gives the same offset, so subject 1's extraction (guard: same 0.360, different 0.239) stands.

No hypothesis or criterion changed.

## Commands

```
python -m experiments.spike53 fetch-brain 01   # likewise 02, 03; streams, about 130 MB of disk per subject
python -m experiments.spike53 run
python -m experiments.spike53 analyse
```

## Results

`experiments/results/spike53.json`; raw `spike53_raw/run.json`.

**Cases:**
- 72 family cases and 45 product cases over 24 matrices;
- 3 subjects, 370 concepts in 17 categories each;
- 63 (subject, matrix) pairs with ≥ 100 common concepts (62–158).

All three subjects passed the alignment guard (same versus different image: 0.360/0.239, 0.426/0.321, 0.332/0.240).

**Execution error, recorded.** The first run read only subjects 1 and 2: subject 3's patterns had been written to the default data folder, because the shell's `export` applied to only one of two parallel jobs. Its outputs are kept as `spike53_2subjects.json` and `spike53_raw/run_2subjects.json`. The run was repeated on all three subjects as registered. **Every verdict is the same in both runs.** The figures below are from the three-subject run.

| ID | Measured | Criterion | Verdict |
|---|---|---|---|
| H53.1 | cyclic R² significant in 84.7% of cases (weekdays 96%, months 100%, abbreviations 62%) | ≥ 75% | **HELD** |
| H53.2 | lowest Fourier mode largest in 100% of cases | ≥ 75% | **HELD** |
| H53.3 | interaction carries the cycle (p < 0.01) in 13.3% of product cases | ≥ 50% held, ≤ 20% broken | **BROKEN** |
| H53.4 | block R² 0.125, 0.259, 0.091, all p = 0.0005 (the floor) | p < 0.001 in all subjects | **HELD** |
| H53.5 | block R² p < 0.001 in 100% of matrices (median R² 0.31) | ≥ 75% | **HELD** |
| H53.6a | brain–model Mantel ρ > 0, p < 0.01 in 100% of pairs (median ρ 0.122) | ≥ 75% | **HELD** |
| H53.6b | residual (beyond the 17-category skeleton) still significant in 81.0% of pairs (median ρ 0.040) | ≥ 75% breaks | **BROKEN** |

**Reading:**
- **Cyclic geometry (C29's derived row) holds in static weights of 14 models.** Weekday and month embeddings are circles: the lowest Fourier mode dominates in every case, so there are no "spokes" here. This is a replication on a new substrate. Engels et al. found it in activations; here it is already in the lexicon.
- **The tensor row is refuted for lexical composition.** In month × form and weekday × form, the additive part carries the cycle (significant in 89% of cases, median cyclic R² 0.76). The interaction share is 0.25 against a no-structure value of 0.46–0.48, and the interaction carries the cycle in only 13%. Composition of these factors in embedding space is mainly a **direct sum** (x ≈ a_month + b_form), not a tensor product.
  - **Exploratory:** 51% of product cases have interaction p < 0.05, against 5% expected by chance. So a weak tensor component is present but secondary.
  - Output embeddings show it less than input embeddings (0% against 23% at p < 0.01).
- **Taxonomy geometry is shared by cortex and weights.**
  - Ventral object cortex (from images) and the lexical embeddings of 14 models both have the category block structure.
  - Their concept geometries correlate in every pair (median ρ 0.12).
  - **The shared geometry is not exhausted by the category skeleton:** after removing each side's 17-category block structure, 81% of pairs still correlate. The residual is about 31% of the full correlation (median ratio).
  - So the "grain" that brains and models share is finer than the labelled taxonomy. In C29's terms, the symmetry group that would fix it is not the one the category labels give.
