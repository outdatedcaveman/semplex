# Spike 02b: Ontology generation after refutation

**Date:** 2026-11-06 · **Charter refs:** §1.3 (revisable ontology, not relativism), §3.4, §8.11 · **Status:** complete · **Motivated by:** Spike 02's biggest gap

## Question

Spike 02's agent could *refute* its candidate set but not *repair* it. Can it propose new ontologies in a way that is constrained by what it has already established, records its own provenance, and is still held to fresh-data testing?

## Design (`cerp/epistemics/generate.py`, hooked into `inquire(..., generate_on_refutation=True)`)

1. After every candidate fails, the agent first **finishes model-free measurement**: it runs every intervention arm it can and records the direct two-arm effect estimates.
2. It **enumerates every DAG** over the observables plus at most one latent: 29,824 structures, which matches the known counts of 543 + 29,281 labelled DAGs.
3. It **prunes** by:
   - *hygiene*: a latent needs at least 2 children;
   - *measured facts*: a measured effect requires a directed path, and a measured absence forbids one, under a **declared faithfulness assumption**;
   - *already-refuted structures*.
4. It orders survivors by parameter count, a **declared parsimony policy**, and screens them on the data already seen.
5. The top 3 become candidates under a **new, named closed-world assumption**, with a generation claim that cites the measured facts and the faithfulness premise.
6. **Generated ontologies must be re-tested on fresh data for every available protocol.** They were proposed after seeing the data, so the old data cannot validate them.

## Hypotheses and verdicts

| # | Hypothesis | Kill criterion | Verdict |
|---|---|---|---|
| H2b.1 | After refutation, constrained generation recovers an adequate ontology within a bounded number of candidates | Space blows up, or survivors are mostly artifacts | **Held**: the truth was proposed in the top 3 and survived validation in 40/40 runs |
| H2b.2 | Settled interventional facts prune the space by a large factor | Negligible pruning | **Held**: 11,156 → 476–856 after hygiene (13–23×). Screening then fitted only 7–54 candidates |
| H2b.3 | Generated ontologies carry provenance and stay conditional | The ledger can't express it | **Held**: each answer from a generated ontology is conditional, *by name*, on the generation's closed-world premise; the generation claim depends on the measured facts and the faithfulness premise (tested) |

## Results (`results/spike02b.json`; 10 seeds per scenario; the truth is never among the given candidates)

| Scenario | Truth proposed | Truth survived | Answers (status: correct/wrong) | Mean samples |
|---|---|---|---|---|
| copy_chain, O4 removed | 10/10 | 10/10 | 50 EMPIRICAL ✓, 10 CONJECTURE ✓ | 15,000 |
| latent_causal, O1 removed | 10/10 | 10/10 | 50 EMPIRICAL ✓, 10 CONJECTURE ✓ | 19,200 |
| direct_and_latent (outside all 4) | 10/10 | 10/10 | 50 EMPIRICAL ✓, 10 UNDETERMINED | 19,500 |
| direct_and_latent + do(S2) | 10/10 | 10/10 | 70 EMPIRICAL ✓, 10 CONJECTURE ✓ | 30,000 |

**0 wrong answers at any status in 220 answers.**

## Findings

**F1. Refutation plus measurement is enough to repair the candidate set in this sandbox.** The facts the agent measured *without any ontology* (Spike 02 F5's model-free route) are exactly what makes generation tractable and non-arbitrary. Theory-light measurement turns out to be the foundation for theory *construction*, not just a fallback.

**F2. Generation surfaces the real underdetermination.** In the direct_and_latent world, the generator proposed both "a hidden Z drives S1 and S2" (the truth) and "S2 directly drives S1". Both pass every available test, so the agent says UNDETERMINED and attaches the disagreement. Adding a do(S2) protocol resolves it in 10/10 runs. **What can be known about the ontology is a function of the available interventions**, and the agent can say which intervention it lacks.

**F3. Post-hoc candidates need fresh validation.** The first implementation let generated ontologies inherit the earlier tests, and since they were near-equivalent on old protocols, information gain was ~0, so they were never tested at all. Requiring fresh data on every protocol for generated sets closed that loophole. This is the general rule that hypotheses formed after seeing data can't be confirmed by that data (charter §5.7 on adaptive evaluation).

**F4. Faithfulness is now an explicit, retractable premise.** Turning "measured no effect" into "no causal path" requires assuming that effects don't cancel and aren't below the resolution. The ledger records this premise per generation, and every generated answer depends on it. If the premise is ever refuted, everything resting on it will be retracted automatically.

## Gaps and threats to validity

- **The parsimony policy favored the truth** because the sandbox worlds are simple. A world whose truth is *less* parsimonious than an adequate rival would expose the policy: the agent would accept the simpler rival, labeled CONJECTURE, until a protocol separates them. That is untested.
- **Enumeration does not scale.** 5 nodes means 29,824 DAGs; 7 nodes is about 1.1 billion. Scaling needs search or structure learning, which reintroduces heuristics whose outputs must still be validated on fresh data. The validation discipline is what makes heuristic generation safe.
- Only one latent and binary variables.
- No cancelling paths in the worlds, so the faithfulness premise was never stressed.
