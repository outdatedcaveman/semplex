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

## Done

- **G1–G7** (merged 2026-11-15): claims P160–P165.
- **G8–G12** (merged 2026-11-15): claims P166–P169, corrections under P165. All verified here: 155 Python tests, 11 Lean-backed tests, and the Mathlib project built and audited from a fresh cache.

What worked and should continue: pre-registering your own benchmarks, reporting a broken criterion as broken (G8), correcting your own earlier handoff (G12), and keeping Mathlib out of the core proofs (G11).

## Queue, in priority order

### G13. Close Theorem 15: bridge the two Lean packages (gap C1)

P160 proves step equivariance in a discrete model; P169 proves Gaussian invariance for any measurable equivariant step. Nothing connects them, so the claim is still "partly mechanized" and 20 dependent claims stay flagged. Work only in `proofs/lean-mathlib/`.

1. Define the two-layer network of Spikes 09–14 on ℝ (inputs in {−1, +1}ⁿ, first-layer weights and biases, output weights and bias, an odd activation such as tanh), its logistic loss on a Boolean target g, and the action of an input symmetry σ (a permutation of inputs with sign flips, and output negation when g∘σ = ¬g) on the parameters.
2. Prove the loss is invariant under that action whenever σ is a symmetry of g. This is step (ii) of the paper proof and is not mechanized anywhere yet.
3. Prove equivariance and measurability of the gradient-descent step and of the AdamW step with its moment state (initial moments zero), for the true gradient if Mathlib's calculus makes that practical, otherwise for the central-difference gradient used in P160, stated as such.
4. Conclude: for i.i.d. centred Gaussian first-layer parameters and a symmetric law on the output weights, the probability that training yields circuit I equals the probability that it yields σ·I.

**Done when:** one theorem states item 4 with no hypothesis of equivariance or measurability left (only: σ is a symmetry of g, the activation is odd and measurable, the readout is a stated concrete function or a stated equivariant measurable one); `#print axioms` shows standard axioms only; the handoff lists every remaining hypothesis and whether it is an assumption about the world or a gap. If the readout cannot be made concrete, say exactly why.

### G14. Prior art on what over-wide hidden layers represent (gap A9) — lowest priority

**Update:** Spike 47 refuted C21 (0.08% of nets). Do this task last. Its question is now: is the *negative* result known, and what does prior work say about how many directions an over-wide hidden layer keeps under weight decay?

Claim under review, C21: for a non-threshold Boolean target and one hidden layer, the hidden representation cannot collapse to the class (the Bayes quotient) and instead collapses onto the cell partition of a minimum circuit, the coarsest sufficient partition the architecture can realize.

Read in full: neural collapse and its review (Papyan, Han & Donoho; 2206.04041), intermediate-layer collapse (2308.02760; 2201.08924), collapse in shallow ReLU nets (2510.21078), the persistence of collapse under low-rank bias (2410.23169), and work on linear regions or activation patterns of trained shallow nets on Boolean or discrete data. Search with `python -m cerp.litsearch`.

**Done when:** rows in `charter/LITERATURE_REVIEW.md` §5 with read level, main claim, and one of {anticipates, contradicts, orthogonal} for C21 with the sentence that shows it; and a short statement at the top of the handoff: is "collapse onto a minimum-size sufficient partition when class collapse is unrealizable" already stated anywhere?

### G15. Census at 5 inputs beyond cost 3 (follow-up to G9, gap A10)

Extend `cerp/orbits.py` to n = 5 with |w| ≤ 4 for cost 3, and to cost 4 at n = 5 for as many classes as complete in 6 hours on 4 cores.

**Done when:** the table reports, per cost, classes completed, one-orbit fraction, and where and why it stopped; the n = 4 results are unchanged; a test covers a sample of n = 5 classes by brute force.

### G16. Pass the kernel wall (follow-up to G10)

G10 found that kernel `decide` stops scaling at about 41–60 LRAT steps. Find a certificate representation the kernel checks faster (packed or reflected clauses, a checker written for kernel reduction) without `native_decide`.

**Done when:** `[8]→[4]→1` (104 LRAT steps in G10's table) verifies in under 120 s with standard axioms only; or a handoff shows, with measurements, which stage is the irreducible cost.

### G17. (done by Claude) The Lean test timeout is read from `SEMPLEX_LEAN_TIMEOUT` (default 600 s); see `proofs/lean/README.md`.
