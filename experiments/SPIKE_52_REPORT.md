# Spike 52: The canonical form of a moral concept (pilot on the Moral Machine)

**Date:** 2026-11-16 · **Status:** complete — no verdict (guard failed; pre-registered in 5b8624d) · **Follows:** `charter/FOUNDATIONS.md` §6 (canonical forms, forced cores, meaning as enactive power) and Spikes 45, 49, 50. **First step of** the "justice" programme (§6.5).

## Question

Take a moral verdict concept, "whose lives should the car spare", as millions of people applied it. Treated as a function from situations to verdicts:

1. What is its minimal form: a single weighted rule (a threshold function, the simplest kind of form), or something more complex?
2. Given part of the evidence, does inference by minimal form predict the verdicts on the rest?
3. Is the forced core shared across cultures?

## Data

Moral Machine, `SharedResponsesSurvey.csv` (Awad et al., *Nature* 563, 2018; OSF project 3hvt2), plus the cultural clusters in `country_cluster_map.csv`. Only the codebook (`MMdata_ReadMe.txt`) has been read; no response has been looked at.

**Unit.** One dilemma (one `ResponseID`, two rows). The *stay side* S is the outcome whose characters die if the car stays (`Intervention = 0`).
- **Label:** S's `Saved`, that is, whether the respondent chose to swerve to save S.
- **Features** (binary, describing S relative to the other side):

| Bit | Feature | Definition |
|---|---|---|
| x0 | S is crossing lawfully | S `CrossingSignal` = 1 |
| x1 | S is crossing unlawfully | S `CrossingSignal` = 2 |
| x2 | S are the car's passengers | S `Barrier` = 1 |
| x3 | S has more characters | S `NumberOfCharacters` > other side's |
| x4 | S has fewer characters | S `NumberOfCharacters` < other side's |
| x5 | S is younger | `ScenarioType` = Age and S `AttributeLevel` = Young |
| x6 | S is older | `ScenarioType` = Age and S `AttributeLevel` = Old |
| x7 | S is pets | `ScenarioType` = Species and S `AttributeLevel` = Pets |

- **Cells.** A cell is a feature pattern. Its **verdict** is the majority label over its dilemmas, and it counts as observed if it has at least 30 dilemmas and the majority is not a tie.
- Dilemmas with missing values in these columns are dropped.
- **Cultural clusters** are as defined in `country_cluster_map.csv` (Western, Eastern, Southern; Awad et al.).

## Analyses (all fixed here)

1. **Minimal form.** `netsolve.compile_partial` (n = 8, |w| ≤ 4) on the observed cells gives the minimum cost of the aggregate verdict function. Also reported: the fewest cells a single threshold unit must misfit (`min_errors`).
2. **Inference from partial evidence.** 40 random splits (seed 5,200), each showing 60% of observed cells. On the hidden cells:
   - **forced cells:** a hidden cell is forced if every minimum-cost circuit consistent with the shown cells (|w| ≤ 4) gives it the same value, decided exactly as in Spike 49;
   - **accuracy of the forced values** against the human verdict;
   - **baselines:** logistic regression on the 8 bits (fitted to the shown cells weighted by dilemma counts), the additive model behind the paper's effect sizes, and the minimal-form majority vote over 10 sampled circuits on all hidden cells.
3. **Cultures.** The verdict function per cluster, on cells observed in all three:
   - the fraction of cells where all three clusters agree;
   - the minimum cost for each cluster;
   - the fraction of cells forced in every cluster under the same splits.

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H52.1 | **Moral calculus.** The aggregate verdict is a single weighted rule | one threshold unit fits all observed cells | it must misfit > 10% of observed cells |
| H52.2 | **Forced verdicts are right.** From 60% of situations, the verdicts forced by every minimal form match human verdicts on the rest | accuracy of forced values ≥ 0.90, with ≥ 20% of hidden cells forced | accuracy < 0.75 |
| H52.3 | **Minimal form is at least as good as the additive model** on hidden cells | majority-of-minimal-forms accuracy ≥ logistic accuracy − 0.02 | < logistic − 0.05 |
| H52.4 | **Shared core across cultures** | all three clusters agree on ≥ 85% of commonly observed cells | < 70% |

Anything else is *neither*.

**Guards.** No verdict if fewer than 40 cells are observed overall, or fewer than 25 in all three clusters (H52.4 only).

**What this pilot cannot show.** The Moral Machine measures quick choices in stylized dilemmas, not considered judgments of justice. Its features are the experimenters' choices. Aggregating over millions of people gives the verdict function of a population, not of anyone's concept. The pilot tests whether the machinery yields a definite, checkable answer on real moral data; it does not settle what justice is.

**Deviation recorded before any outcome was read.** The first build paired the two outcomes of a dilemma within streamed chunks and found none, because the file is sorted by `Intervention`. The build now loads the needed columns whole and joins on `ResponseID`. No definition or criterion changed.

## Commands

```
python -m experiments.spike52 build
python -m experiments.spike52 analyse
```

## Results

`experiments/results/spike52.json`; aggregated counts in `spike52_raw/cells.json`. 5,449,620 dilemmas from 11,286,141 rows.

### Verdicts

**All four: no verdict.** The guard needed at least 40 observed cells; there are **24**. The cause is the Moral Machine's design: each dilemma varies one attribute type (age, species, number, …), so most combinations of my eight features never occur together. I should have checked the design's reachable cells before setting the guard. Everything below is exploratory.

### Exploratory observations

1. **The aggregate verdict is a single weighted rule on the 24 cells.** It has minimum cost 1, certified, and a single threshold unit fits all 24 cells with no error. This is consistent with the additive effect-size model of Awad et al., but 24 cells across 8 features is weak evidence of linearity, since many functions fit few points.
2. **Inference from partial evidence.** With 60% of cells shown (about 14), only 6.5% of hidden cells are forced. Those forced values are always right (100%), but they are few. The majority of minimal forms is right on 82.5% of hidden cells, against 95.8% for weighted logistic regression. With this little structure, a threshold rule fitted to counts beats one fitted to binary verdicts, as expected, since the logistic model uses the vote shares and the circuits only their signs.
3. **Cultures.** All three clusters (Western, Eastern, Southern) observe the same 24 cells, each verdict function has cost 1, and they agree on 87.5% of cells (the bar for H52.4 would have been 85%). The three disagreements are cells near a 50% split: passengers (saved shares 0.51 / 0.47 / 0.51); lawful+fewer (saved shares 0.39 / 0.51 / 0.42); unlawful+younger (saved shares 0.55 / 0.50 / 0.58).

### What this does and does not show

- It shows that the machinery runs on real moral data and gives definite, checkable answers: a minimal form, a certificate, a forced core, cultural agreement.
- It does not test the hypotheses. The Moral Machine is too sparse in feature combinations for the forcing analysis to bite: few cells means few forced cells.

**Next.** Two designs would work:
- choose features along the axes the experiment actually crosses (structural bits × one attribute at a time, analysed per scenario type);
- use a dataset designed as a full factorial over justice-relevant features (desert, need, equality, procedure), which would need to be found or collected.
