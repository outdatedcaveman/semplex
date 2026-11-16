# Spike 59: Are semantic primes the elements of the lexicon? A lexical periodic-table test in model weights

**Date:** 2026-11-16 · **Status:** pre-registered (no run) · **Follows:** `charter/FOUNDATIONS.md` §9.4 (the lexical scale of the atlas) and §10.1 (semantic primes). The weight-reading method is Spike 53's (`cerp/hfrows.py`): rows read from published safetensors files, no model run.

## Question

The Natural Semantic Metalanguage (NSM; Wierzbicka, Goddard †, list cited from memory and to be checked against Goddard & Wierzbicka 2014 before any claim rests on it) holds that about 65 universal, undefinable meanings explicate every other word meaning.

If the primes are the elements of the lexicon, two things should hold:
1. **Spanning.** Ordinary concepts should be reconstructible from the primes' representations better than from equally many comparable words.
2. **Universality.** The primes a concept decomposes into should agree across independently trained models.

## Data

**Models.** The 14 models of Spike 53, input and (where untied) output embeddings: 24 matrices.

**Prime dictionary.** 67 single-word English exponents of the primes (lower-case, `" " + word` must be a single token; words that are not are dropped for that model):

> i, you, someone, something, thing, people, body, kind, part, this, same, other, one, two, some, all, much, many, little, few, good, bad, big, small, think, know, want, feel, see, hear, say, words, true, do, happen, move, be, mine, live, die, when, time, now, before, after, long, short, moment, where, place, here, above, below, far, near, side, inside, touch, not, maybe, can, because, if, very, more, like, way

**Targets** (words in either dictionary are excluded):
- **Concrete:** THINGS concept words (Hebart et al. 2019; the metadata Spike 53 used) that are single lower-case tokens.
- **Abstract** (fixed now): justice, freedom, anger, fear, love, hate, hope, shame, pride, guilt, joy, grief, envy, trust, idea, belief, promise, lie, truth, gift, friend, enemy, help, harm, power, rule, law, right, duty, fault, blame, praise, reason, cause, chance, risk, danger, safety, peace, war, beauty, health, wealth, poverty, success, failure, mistake, secret, memory, dream, plan, choice, goal, need, value, price, debt, loss, victory, rest.

**Matched random dictionaries.**
- For each prime, draw a random real English word from the same frequency band: within ±100 ranks of the prime in the Google 10,000 most-frequent English words list (`experiments/data/google-10000-english-no-swears.txt`, from github.com/first20hours/google-10000-english; all 67 primes are in it).
- The word must be alphabetic, at least 2 letters, a single token in that model, and not a prime or a target.
- 20 such dictionaries per matrix (seed 5,900).

(A token-id proxy for frequency was drafted first and replaced before any run, because it admitted subword fragments.)

## Statistic

**Preprocessing.** Rows are centred by the mean of all rows read for that matrix (primes, targets, random words), then normalised.

**Spanning.** Each target is reconstructed by orthogonal matching pursuit with k = 8 atoms from a dictionary. R² = 1 − ‖x − x̂‖² / ‖x‖². Per matrix and target set, the mean R² is compared:
- p = the share of the 20 random dictionaries whose mean R² is at least the primes';
- *z* = (primes − random mean) / random SD.

**Universality.** For each target (in every usable matrix's target list), take its set of 8 primes chosen by OMP in each matrix. The statistic is the mean, over targets and over pairs of matrices, of the number of primes the two sets share. All sets have 8 atoms, so this is monotone in Jaccard overlap. The null shuffles prime identities within each matrix (a random relabelling among the prime atoms that matrix uses, applied consistently to all targets of that matrix; 1,000 shuffles).

## Hypotheses and kill criteria

| ID | Hypothesis | Held if | Broken if |
|---|---|---|---|
| H59.1 | **Primes span the concrete lexicon** better than matched words | p ≤ 0.05 in ≥ 75% of matrices (concrete targets) | primes below the random median in ≥ 50% of matrices |
| H59.2 | **Primes span the abstract lexicon** better than matched words | the same, abstract targets | the same |
| H59.3 | **Prime decompositions are universal across models** | observed mean overlap above all 1,000 shuffles (p < 0.001), concrete and abstract each | p ≥ 0.05 for both |

Anything else is *neither*.

**Guard.** No verdict for a matrix with fewer than 50 primes as single tokens, or fewer than 100 concrete or 40 abstract targets.

**Reported without criteria:**
- the primes used most often per target set;
- R² as a function of k (4, 8, 16);
- the difference between concrete and abstract targets.

## What this cannot show

- Static embeddings encode distributional similarity, not explication. NSM claims a paraphrase relation, which linear reconstruction only approximates.
- Primes are high-frequency, often function-like words. Token-id matching controls frequency only roughly.
- English exponents only; NSM's claim is cross-linguistic.

## Commands

```
python -m experiments.spike59 run
python -m experiments.spike59 analyse
```

## Results

(Not run.)
