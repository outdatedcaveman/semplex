# Spike 02: World-facing sandbox (rival ontologies, evidence, revision)

**Date:** 2026-11-06 · **Charter refs:** §3 (whole), §5.7, §5.8, §8, §10, §11.1 · **Status:** complete

## Question

Can the charter's ontology-epistemology loop (§8) run against a world the agent cannot see directly, and do so without a truth oracle? Specifically, can the agent:
- hold rival ontologies,
- test them only through measurement and intervention protocols,
- revise them with a typed record,
- abstain where the evidence underdetermines the answer,
- and stay honest when the truth isn't among its candidates?

## The sandbox

**Observables:** A (an action), S1 and S2 (two sensors), Y (an outcome). The worlds are hidden behind an `Interface` that exposes protocols (observe, do(A=a), do(S1=s)) and returns counts. The agent module may not import the world module, and a test enforces this. The synthetic world is a calibration sandbox, *not* evidence that natural-world grounding is solved (charter §11.1).

| World (truth) | Structure | Note |
|---|---|---|
| `latent_causal` | A → Z → {S1, S2, Y} | Z hidden |
| `latent_confounded` | Z → {A, S1, S2, Y} | **Observationally identical** to `latent_causal` (difference 3·10⁻¹⁷); differs only under do(A) |
| `copy_chain` | A → S1 → {S2, Y} | No hidden variable; S2 is a noisy copy of S1 |

**Candidate ontologies:** O1 latent-causal, O2 independent-channels, O3 latent-confounded, O4 copy-chain. These are typed structures with explicit commitments such as ("exists-latent", Z) and ("causes", A, Z).

**Agent loop** (`cerp/epistemics/inquiry.py`):
- Fit every surviving ontology with EM.
- Pick the protocol with maximal expected information gain about *which* ontology is right.
- Use the fresh batch as a **prediction test** of fits that never saw it.
- Eliminate an ontology only on failed adequacy.
- Record a typed revision.
- Answer four queries, with the status discipline described below.
- When nothing discriminates the survivors, attach equivalence witnesses and stop.

Bonferroni control covers every test the run may perform.

## Hypotheses and verdicts

| # | Hypothesis | Kill criterion | Verdict |
|---|---|---|---|
| H2.1 | The ledger can type an ontology revision: what changed, why, what's invalidated, what follows (§3.4) | Revisions need information the ledger can't type | **Held**, after adding retraction with dependency propagation |
| H2.2 | From observation alone, the agent abstains between observationally equivalent ontologies; interventions separate them | The agent confidently picks the wrong ontology from observational data | **Held**: abstained 30/30, resolved 30/30 after do(A), 0 confident errors |
| H2.3 | Spike 01's conjecture P006: substitutable variables signal a shared latent quantity | Substitutability fails to track latent sharing | **Broke, then refined**: with noisy channels nothing is substitutable; the informative signature is complementarity vs screening-off (F6) |
| H2.4 | Adequacy can be stated as a checkable, protocol-indexed claim without a truth oracle (§5.8) | Every formulation smuggles in ground truth | **Held, but only after a calibration fix**: the naive version rejects the true ontology (F2) |

## Results

Measured on 15 seeds per cell, 1,500 samples per batch, seeds fixed (raw data: `results/spike02.json`). These are EMPIRICAL results about this sandbox, not general results.

**Truth among the candidates** (540 answers):

| World | Protocols available | Answers by status | Mean samples |
|---|---|---|---|
| latent_causal | observe | 45 CONJECTURE ✓, 15 UNDETERMINED | 3,000 |
| latent_causal | + do(A) | 15 EMPIRICAL ✓, 45 CONJECTURE ✓ | 4,500 |
| latent_causal | all | 45 EMPIRICAL ✓, 15 CONJECTURE ✓ | 12,000 |
| latent_confounded | observe | 45 CONJECTURE ✓, 15 UNDETERMINED | 3,000 |
| latent_confounded | + do(A) | 15 EMPIRICAL ✓, 45 CONJECTURE ✓ | 8,200 |
| latent_confounded | all | 45 EMPIRICAL ✓, 15 CONJECTURE ✓ | 15,200 |
| copy_chain | observe | 60 UNDETERMINED | 3,000 |
| copy_chain | + do(A) | 15 EMPIRICAL ✓, 45 UNDETERMINED | 4,500 |
| copy_chain | all | 45 EMPIRICAL ✓, 15 CONJECTURE ✓ | 7,500 |

- **Zero wrong answers at any status.**
- The true ontology survived in 135/135 runs.

**Truth removed from the candidates** (360 answers):
- **Zero wrong EMPIRICALLY-SUPPORTED answers.** All 105 wrong answers carried the CONJECTURE label, which meant "conditional on the closed-world assumption", and that assumption was false.
- When the protocols could expose the gap, they did: the closed world was refuted, dependent answers were retracted automatically, and directly measured facts survived.

## Findings

**F1. Underdetermination is detected, not guessed.** The two latent worlds have identical observational distributions. In every observe-only run the agent:
- kept both O1 and O3,
- answered UNDETERMINED to "does A change Y?",
- and attached mutual **equivalence witnesses**: each ontology was fitted to reproduce the other's predictions, max KL ≈ 3·10⁻⁸.

Expected information gain then *selected* do(A) as the discriminating experiment on its own. Observing more had EIG ≈ 0, which is the correct value. This is the charter's §10 "observational equivalence can hide causal differences", turned into executable behavior. It is also Layer F's protocol-indexed equivalence (≡_Ω) from Spike 01, now applied to ontologies: O1 ≡_Ω O3 for Ω = observe, and not for Ω = do(A).

**F2. A naive prediction test rejects the true ontology.** Testing a *fitted* model's prediction with a G-test treats estimated parameters as exact. Estimation error (from 1,500 training samples) has the same order of magnitude as test sampling noise, so the true model fails at an inflated rate.

| Setting | Naive false rejection at α=6.25·10⁻⁴ | Calibrated |
|---|---|---|
| O1 under do(S1=1) | 5% | 0% |
| O1 under do(A=1) | 10% | 0% |
| O3 under do(S1=0) | 7.5% | 0% |

(At α=0.05 the naive rejection rate was 27–35%.) The fix is a parametric bootstrap of the null (refit on simulated training data) with a Satterthwaite scaled-χ² tail. This is the general lesson of charter §5.7 in concrete form: *a test of a fitted predictor must account for how the predictor was fitted.*

**F3. Rejection and preference are different epistemic acts.** Eliminating ontologies because a rival "predicts better" (paired log score) would reject overparameterized-but-true models, and it conflates a better-fitted *predictor* with a truer *ontology*. Only failed adequacy eliminates. Predictive superiority is recorded as `preference`. Parsimony is likewise a declared policy and never evidence (charter §3.4).

**F4. Ontological commitments stay conditional; interventional facts do not.** Even in fully resolved runs, "S1 and S2 measure a shared hidden quantity" never rose above CONJECTURE. That was not hand-coded: it depends on the closed-world assumption, and the ledger's dependency cap does the rest. Interventional effects measured on both arms reached EMPIRICALLY-SUPPORTED independently of any ontology.

What becomes empirically secure here is **causal-interventional structure among observables**, while the existence and identity of hidden entities stays model-relative. This resembles a structural-realist reading (see the charter's SEP references), and it is a property of the formal setup we chose, not a philosophical conclusion we imposed.

A related open problem: latent identity across ontologies is currently **by name** ("Z" in O1 and "Z" in O3 are treated as the same commitment). The charter's Layer B identity criteria are needed here. → Q-B1.

**F5. Measured facts must not be held hostage by theory.** Initially every answer was routed through surviving ontologies. When all ontologies failed, the agent reported *nothing*, even though it had run both do(A) arms and the effect was plainly in the data. The fix:
- Effect queries whose interventions were run are answered by a **model-free two-arm measurement** with an interval.
- Ontologies answer only untested questions, and those answers are labeled CONJECTURE.
- After the closed world is refuted, inquiry continues in measurement-only mode.

**F6. H2.3 refined: complementarity vs screening-off, not substitutability.** With noisy sensors of unequal quality, minimal ε-sufficient sets (plug-in Bayes risk, ε=0) are unique in all 45 runs. Substitutability was a knife-edge artifact of Spike 01's *exact* redundancy. But sufficiency structure still discriminates the worlds:

| World | Minimal sufficient set for predicting Y from {A, S1, S2} | Reading |
|---|---|---|
| latent_causal | {A, S1, S2} (15/15) | Channels are *complementary*: independent noisy readings of one hidden quantity |
| latent_confounded | {A, S1, S2} (15/15) | Same; identical observationally, as it must be |
| copy_chain | {S1} (15/15) | S1 *screens off* S2 and A: S2 carries nothing beyond S1 |

P006 is refuted as stated. In its place is P012 (CONJECTURE): complementarity of redundant channels is the noisy-regime signature of a shared latent cause, and screening-off is the signature of a chain. This is still only observational and cannot separate O1 from O3, so it is a cheap pre-screen for candidate ontologies, not a substitute for intervention.

**F7. Absence is expensive.** In the fully resolved latent_causal run, the ontology was settled after 2 rounds (6,000 samples). The agent then spent 7,500 more establishing that do(S1) changes *nothing*. Confirming "no effect > 0.05" needs the interval to sit inside ±0.05, which takes about 2× the data per arm that confirming presence does. Measured costs: latent_confounded with all protocols averaged 15,200 samples vs 12,000 for latent_causal. An agent that only needs to *act* may not need absence claims at all. That is a task-relative stopping rule, and it ties to Layer H. → open question Q-E1.

**F8. Status-taxonomy gap, again.** Equivalence witnesses are numerically checkable existence proofs ("these parameters reproduce those predictions within KL 3·10⁻⁸"). That is stronger than CONJECTURE and weaker than a kernel proof. This is the same gap as Spike 01's F7, a second independent instance, and it strengthens the case for Spike 04.

## What did not get tested (honest gaps)

- **A finite, hand-written candidate set.** Real ontology *generation* (proposing O5 after O1–O4 all fail) is untouched. The agent can refute the closed world but cannot repair it. This is the biggest gap and an obvious next frontier.
- **Binary variables, 4 observables, 1 latent.** Scaling and continuous variables are untested.
- **Perfect interventions only.** Fat-hand or noisy interventions, and measurement error *in* the intervention, are untested.
- **Calibration is approximate.** The bootstrap uses fitted parameters as the truth proxy, the Satterthwaite tail is an approximation, and B=30.
- **No sequential-testing guarantee** beyond Bonferroni with a fixed maximum number of tests and fresh data each round. That is conservative but valid; alpha-spending or e-values would be more efficient.
- **No real-world data.** That comes only after the protocol for measurement adequacy is clear (charter §11.1).

## Proposed charter amendments

1. **§5.8 (adequacy):** a test of adequacy must account for how the prediction was obtained (F2). Add "calibrated for estimation" as an explicit requirement.
2. **§3.4 (revision):** distinguish *rejection* (failed adequacy) from *preference* (comparative fit) from *policy* (parsimony) (F3).
3. **§3.3 (grounding):** add the theory-light route. Direct measurements of intervention effects are recorded independently of any ontology and outlive ontology collapse (F5).
4. **§10 (labels):** CONJECTURE currently covers both "unproven idea" and "conditional on the closed-world assumption". These differ in kind (F4, F8). → Spike 04.
