# ADR-0003: Epistemic rules of the inquiry agent

**Status:** accepted (Spike 02) · **Date:** 2026-11-06

## Decisions

1. **Truth/agent separation is structural.** Ground truth lives in `cerp/epistemics/world.py`. The agent receives only an `Interface` (protocols in, counts out). A test forbids the agent module from importing the world module.
2. **Only failed adequacy eliminates an ontology.** Comparative predictive fit is recorded as *preference*, and parsimony as *policy*. Neither is grounds for rejection.
3. **Adequacy tests are calibrated for estimation.** A fitted model's prediction is tested against a bootstrap null that includes refitting. The naive test rejects true models (Spike 02, F2).
4. **Every test is a prediction on fresh data**, never on data the fit has seen. Bonferroni control spans the maximum number of tests in a run.
5. **Two routes to answers, kept apart:**
   - Directly measured intervention effects are recorded with no ontology dependency, and they outlive ontology collapse.
   - Model-derived answers depend on the closed-world assumption, so the ledger caps them at CONJECTURE.
6. **Abstention is a first-class outcome.** When survivors disagree and no available protocol discriminates them, the answer is UNDETERMINED, with equivalence witnesses attached.

## Consequences

The agent is slower: absence claims cost about 2× the samples of presence claims (Spike 02, F7). It is also more often undecided. In exchange, across 900 answers it gave no wrong answer labeled EMPIRICALLY-SUPPORTED.
