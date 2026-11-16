# Spike 52: The canonical form of a moral concept (pilot on the Moral Machine)

**Date:** 2026-11-16 · **Status:** pre-registered (no outcome data read) · **Follows:** `charter/FOUNDATIONS.md` §6 (canonical forms, forced cores, meaning as enactive power) and Spikes 45, 49, 50. **First step of** the "justice" programme (§6.5).

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

## Commands

```
python -m experiments.spike52 build
python -m experiments.spike52 analyse
```

## Results

(To be filled after the runs.)
