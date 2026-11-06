# Spike 01: Formal vertical slice on fragment F0

**Date:** 2026-11-06 · **Charter refs:** §5, §6, §7, §10, §11.1, §12.1 · **Status:** complete

## Question

Can the charter's core loop (semantics → canonicalize → task-relative abstraction → untrusted translation → independent verification → resource report → honest ledger) run end to end on the smallest fragment that is still mathematically complete? Which of its assumptions hold, which break, and which turn out to have no content?

**Fragment F0:** total Boolean functions over a declared, finite, ordered set of variables (≤16). There are three substrates (the charter's §11.1 demonstrator): a small functional language (`expr`), Boolean circuits, and DFAs. ROBDDs serve as the canonical semantic objects. A task is a target function plus a *care set*, the task's admissible input domain.

## What was built (≈1,400 lines, stdlib only; kernel 220)

| Module | Charter layer | Role | Trust |
|---|---|---|---|
| `cerp/kernel.py` | §7.5 | Independent evaluators and an exhaustive decision procedure (220 lines); insufficiency-certificate checker | **trusted** (the whole trusted base, by design) |
| `cerp/semantics.py`, `substrates.py` | E | Main interpreters, cost models | untrusted, cross-checked against the kernel |
| `cerp/bdd.py` | G | ROBDD normal form, task normal form, `restrict` | untrusted |
| `cerp/translate.py` | J | 7 translators between substrates | untrusted |
| `cerp/sufficiency.py` | H | Minimal sufficient sets (minimal transversals of the conflict hypergraph) | untrusted |
| `cerp/resources.py` | I | Pareto dominance | untrusted |
| `cerp/ledger.py` | §3.2, §10 | Claims ledger. Proof status requires a kernel-minted `Verdict`; status is capped by dependencies | enforced in code |
| `cerp/pipeline.py` | §9 | Master algorithm v0, partial by design | |

There are 35 tests. Five deliberately injected mutants (kernel, BDD, translator, sufficiency, ledger) were each caught.

## Hypotheses and verdicts

| # | Hypothesis (from the charter) | Verdict | Evidence |
|---|---|---|---|
| H1 | One semantic domain can serve as the meeting point for three substrates | **Held** in F0 | All translations kernel-verified on 150 random 6-var functions; two independent interpreter stacks agree pointwise |
| H2 | A normal form N with N(N(C))=N(C) and N(C₁)=N(C₂) ⇔ C₁≡C₂ exists in a decidable fragment | **Held, with a parameter** | Tested on 7,140 random pairs (>50 equivalent). Canonicity is relative to the variable order (F1) |
| H3 | Untrusted translators plus a small independent verifier give real assurance | **Held in F0; doesn't scale yet** | An unsound translator was caught with a counterexample and recorded as REFUTED. Exhaustive checking hits a wall (F3) |
| H4 | Task-relative minimal sufficient representations can be computed and may be non-unique | **Held, and sharpened** | Non-uniqueness occurs *only* under restricted task domains (F4) |
| H5 | Task-relative abstraction yields resource improvement | **Broke, then repaired** | The naive version was worse than doing nothing in 55% of mild-restriction cases (F6) |
| H6 | The status taxonomy (§10) suffices to label every output honestly | **Partially broke** | One output type has no honest label; the labels aren't a chain (F7) |
| H7 | Contracts compose only when they match (§7.3) | **Held** | Explicit counterexample for task relations with different care sets |

## Findings

All numbers are **EMPIRICALLY-SUPPORTED** only. They describe our seeded random workload (`experiments/spike01.py`, seed 20261106: 300 random depth-6 expressions over 6 vars with support ≥ 3) and say nothing about natural workloads. Raw data: `results/spike01.json`.

**F1. Canonical objects carry their protocol.** The ROBDD is canonical only for a *fixed* variable order. The textbook function (x₁∧y₁)∨(x₂∧y₂)∨(x₃∧y₃) has 6 nodes under one order and 14 under another, and both are "the" canonical form. On the workload, the ratio of largest to smallest canonical object across 20 random orders had median 1.53 and max 3.0.
→ *Charter amendment proposal:* Layer G should state that canonical forms are indexed by a declared parameter set, and that parameter set belongs inside Ω.

**F2. Canonical is a good normalizer and not an optimizer.** Routing through the canonical form gave smaller circuits than direct translation in 94.7% of cases (median 0.41×), but larger in 5% (max 3×). The workload generator produces redundant expressions, so the 94.7% figure says more about the generator than about canonical forms. The structural point stands: never treat "canonical" as "optimal realization". They are different objects with different jobs.

**F3. Proof by exhaustive decision hits a wall at n≈16–20.** Kernel time: 2.3 s at n=16. Extrapolated: ≈10 min at n=24, ≈2 days at n=32, ≈10⁷ years at n=64. (The timings are noisy because each n uses a different random expression; treat the extrapolation as order of magnitude only.) The way out is the charter's own §7.2: *certificates cheaper to check than to find*. We have one: the insufficiency witness, which takes 2 evaluations at any n. Equivalence needs the analogue, for example SAT miters with DRAT/LRAT unsatisfiability proofs and an independent checker. → **Spike 03.**

**F4. Multiple minimal sufficient representations come from domain restriction.** *Proposition (proof sketch in `cerp/sufficiency.py`, tested on random functions):* with the full input domain, the minimal sufficient variable set is unique and equals the function's support. Multiplicity appears only when the task domain is restricted:

| Task domain | Fraction with >1 minimal sufficient set |
|---|---|
| random 90% of inputs | 0.7% |
| random 60% | 8.7% |
| random 30% | 51% |
| one equality constraint (two redundant sensors) | 92% |
| two equality constraints | 90% (mean 3.0 minimal sets) |

*Interpretive conjecture (bridge to ontology):* substitutable variables (in some minimal sets but not all) are a computational signature of **redundant measurement channels of a shared latent quantity**. That is an ontological hypothesis ("a and b measure one thing") inferred from task structure. → **Spike 02 tests this.**

**F5. Fidelity relation must be a Pareto dimension.** The first run put exact (≡_ext) and task-relative (≡_T) realizations on one front, so task-only realizations appeared to "dominate" exact ones. That conflates contracts. Fronts are now indexed by (substrate, relation).
→ *Charter §5.7/Layer I amendment:* the fidelity relation is a coordinate of the resource-fidelity front, not a pass/fail filter.

**F6. Naive task abstraction made things worse. Equivalence inclusion fixes it.** Projecting onto a minimal sufficient set and filling don't-cares with 0 destroyed structure:

| Task domain | Naive: worse than exact | `restrict`: worse than exact | Best-of-all: strictly better than exact |
|---|---|---|---|
| 90% | 55% | 10% | 23% |
| 60% | 51% | 6% | 65% |
| 30% | 9% | 2% | 92% |
| 2 correlations | 0% | 0% | 94% (median 0.32× gates) |

Two repairs:
1. Use a don't-care-aware operator (Coudert–Madre `restrict`, an existing tool).
2. A structural principle: **≡_ext ⊆ ≡_T, so every exact realization is automatically a task realization.** The ledger records this as a *derived* claim, and the task front then provably never loses to the exact front (tested).

Generalization worth pursuing: the equivalence relations of Layer F form a **refinement order**, and candidates, certificates and claims should flow along its inclusion maps. This is a concrete design constraint for the CSIR.

**F7. The status taxonomy has a gap and isn't a chain.**
- (a) The output "these are *all* the minimal sufficient sets" comes from an exact but uncertified algorithm. It is not HEURISTIC (the algorithm is exact), not EMPIRICAL, and not PROVED. We labeled it CONJECTURE, which undersells it.
- (b) To cap derived claims by their weakest dependency we had to impose a total order on the labels. But CERTIFIED-REFINEMENT and PROVED-IN-FRAGMENT differ in *kind*, not strength.

→ *Proposal (Q-L1):* make status a structured record (warrant method × trusted base × scope × relation) with a partial order, rather than one enum. → **Spike 04.**

**F8. The trusted base includes the toolchain's caches.** During mutation testing, CPython reused a stale `.pyc` of a mutant: same file size, same mtime second. The restored, correct kernel then *failed* tests. This is a small, concrete instance of charter §14's last question (residual assumptions in the pipeline). Verification runs should disable bytecode caching or hash-check sources.

**F9. Existing parts that slot in.** Several layers already have mature theory in F0, and recognizing them saved invention:
- ROBDD canonicity (Bryant, 1986)
- Generalized cofactor / `restrict` (Coudert & Madre, 1990)
- Minimal sufficient sets = **rough-set reducts** via discernibility matrices (Pawlak; Skowron & Rauszer, 1992); finding a minimum one is NP-hard
- Quasi-reduced BDD ≅ DFA for fixed-length languages

*Verification status of each reference: `charter/BIBLIOGRAPHY.md`.*

## What did not get tested (honest gaps)

- **No world contact.** F0 is purely formal. Natural semantics, measurement and ontology revision (the charter's most novel part) are untouched. **That is the biggest risk, and the reason Spike 02 comes next.**
- **No proof assistant.** "PROVED-IN-FRAGMENT" here means decided by a 220-line Python kernel. The charter's Layer A asks for more.
- **No state.** F0 is functions only. The charter's warning not to "collapse all semantics into input-output functions" is not yet exercised.
- **No CSIR schema.** Artifacts are plain tagged JSON. Extracting a CSIR from one fragment would be premature; we will extract it after 2–3 fragments.

## Next smallest falsifiable milestones

See `ROADMAP.md`. Spike 02 (world-facing sandbox) is the priority because it attacks the riskiest assumption.
