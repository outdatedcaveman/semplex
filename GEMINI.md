# Gemini directive for semplex

[`AGENTS.md`](AGENTS.md) is mandatory. Read it first, then [`STATUS.md`](STATUS.md) (what the theory still lacks). This file is your work queue.

## How the work is split

You have a large token budget. Use it on tasks where **a machine decides whether you are done**: Lean compiles, a test passes, a benchmark meets a number. Volume and persistence win there.

Do not do these; leave them to Claude and the user:
- designing or interpreting experiments on why networks generalize (the `A` gaps in `STATUS.md`);
- editing `THEORY.md` §5, `claims/GAPS.json`, or the status of any existing row in `claims/REGISTER.md`;
- assigning spike numbers or claim numbers.

## Rules that caused problems last time

1. **Work on a branch** named `gemini/<task-id>` cut from `claude/practical-shannon-oqg60y` (or `master` once it is merged). One task per branch. Do not push to `master`.
2. **No numbers.** Do not create `SPIKE_NN_REPORT.md` or `Pnnn` rows. Put proposed claims in `claims/PROPOSED.md` on your branch, one per line: statement, exact evidence (theorem name or `file.json:field`), what it does *not* show. Numbers are assigned at merge.
3. **"PROVED" means the theorem states the claim.** If the Lean statement is weaker than the English claim (a special case, one direction, an arithmetic fact standing in for a probabilistic one), say "lemma toward X" and name what is missing. A one-line theorem is a lemma.
4. **Never change a statement to make a proof go through.** If a given statement is false or unprovable as written, stop and report the counterexample or the obstacle. That is a result.
5. **Any experiment is pre-registered**: the report with numeric held/broken criteria is committed before the run, in its own commit.
6. **Frozen files stay frozen.** `python -m cerp.register check` fails if a file in `experiments/FROZEN.json` changes.
7. **Before every push**, all of these pass:
   ```
   python -m cerp.register check
   python -m cerp.status --check
   python -m pytest -q
   cd proofs/lean && lean Cerp.lean && lean Theory.lean && lean Bounds.lean   # plus the three Audit files; no sorryAx, no ofReduceBool
   ```
8. **Finish with a handoff**: `HANDOFF_<task-id>.md` on the branch with what was done, the exact acceptance check and its output, and what failed.

## Done (merged 2026-11-15)

G1–G7 were verified and merged: Lean compiles (107 audited theorems, standard axioms), 150 Python and 9 Lean-backed tests pass, the G3 benchmark was re-checked on fresh tasks, and the proposals became P160–P165. Two things to keep doing: G4 reported that a lemma was false as stated and proved the corrected version (rule 4), and G7 stated the read level of every source.

One thing to change: when a benchmark I set turns out to be easy (every G3 task had cost ≤ 3), say so at the top of the handoff. It was in the "does not show" section, which is right, but it decides whether the gap closes.

## Queue, in priority order

### G8. Certified minimality at cost 4 for n = 8 (gap B2)

`netsolve.compile_partial` certifies cost-3 nets with the partial not-threshold certificate. Extend it to cost 4: certify that no cost-3 net (two hidden units) fits a partial function.

Benchmark, fixed in advance: n = 8, 100 targets that are random **three**-hidden-unit step nets (weights in −3…3, output weights in −2…2, 25–75% ones, seed 8,820) for which no two-hidden-unit net with |w| ≤ 4 exists on the full table; 75% of inputs in the care set (seed 8,821).

**Done when:** at least 90% compile to a verified cost-4 net *with a kernel-checked certificate that no cost-3 layered net fits the care set*, within 60 s each on 4 cores. If the certificate search is the bottleneck, report the fraction where the solver proves unsat but no checkable certificate is produced; that number is a result. State clearly how many tasks have cost 3 on the care set even though the full target has cost 4.

### G9. Orbit counts of minimum circuits (gap A10)

For every Boolean function on n ≤ 4 inputs (up to the symmetries already used by the atlas), enumerate **all** minimum-cost layered threshold circuits with |w| ≤ 3, quotient them by the function's symmetry group G_f (input permutations and negations that fix f, with output negation where it applies) and by hidden-unit permutation, and tabulate the number of orbits.

**Done when:** `experiments/results/g9_orbits.json` holds, per function class: cost, number of minimum circuits up to weight-equivalence (two circuits are the same if their hidden units compute the same Boolean functions), |G_f|, and the number of G_f-orbits; a test re-derives the table for n = 3 by brute force; and the handoff states the fraction of classes with exactly one orbit. Extend to n = 5 for cost ≤ 3 if it runs in under 2 hours, and report where it stops.

### G10. Multi-layer threshold miters in the Lean kernel at n = 6–8 (follow-up to G2)

**Done when:** a two-hidden-layer net at n = 6 and a one-hidden-layer net at n = 8 are verified against their specifications by kernel `decide` (no `native_decide`), each in under 120 s, with timings in the handoff. If it does not scale, report the size at which it stops and why.

### G11. The Gaussian step of Theorem 15, isolated from the core (gap C1)

The core proofs must stay Mathlib-free. In a **separate** directory `proofs/lean-mathlib/` with its own `lakefile` and toolchain pin, prove that the i.i.d. centred Gaussian product measure on ℝⁿ is invariant under signed permutations, and that an equivariant measurable map pushes an invariant measure to an invariant measure.

**Done when:** it builds with a pinned Mathlib, `#print axioms` shows standard axioms only, the handoff states exactly how the result composes with P160 (which hypotheses of P160 it discharges and which it does not), and nothing under `proofs/lean/` changes. If the Mathlib build is too heavy for the environment, say so and stop; do not vendor Mathlib into the repository.

### G12. Spot-check support for the three unverified literature flags

`HANDOFF_G7.md` raised four critical flags. One (2606.04045) was confirmed against the source at merge. For the other three, 2602.16823 (`lem:blocking_sets_equivalence`), 2507.08802 (`theorem:existing_causalmap_for_any_algorithm`) and 2006.15191 §E (GP 5.80% vs SGD 13.4%), add to `charter/LITERATURE_REVIEW.md` the verbatim statement of the cited theorem or table row with its page or section, so a reader can check each in one step.

**Done when:** each of the three has a verbatim quotation with location. If a quotation does not match what `HANDOFF_G7.md` said, correct the flag and say so first.
