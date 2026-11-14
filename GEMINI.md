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

## Queue, in priority order

Each task names the gap in `STATUS.md` it closes and the check that decides it.

### G1. Theorem 15 in Lean (gap C1; lifts 20 flagged claims)

`THEORY.md` "Theorem 15, equivariance of mechanism choice" has a paper proof in four steps. Mechanize it in `proofs/lean/Theory.lean` without Mathlib, in this shape:

- A group `G` acts on a parameter type `Θ` and on a circuit type `C`.
- `step : Θ → Θ` commutes with the action (prove this *concretely* for: gradient descent on a loss invariant under the action, where the action is by coordinate permutations and sign flips; then for the AdamW update with elementwise moments and decoupled weight decay).
- `readout : Θ → C` is equivariant.
- Conclusion 1 (deterministic): `readout (step^[t] (σ • θ)) = σ • readout (step^[t] θ)`.
- Conclusion 2 (distributional, finite): for a finite weighted list of initial parameters whose weights are invariant under the action, the total weight landing on circuit `I` equals the total weight landing on `σ • I`.

**Done when:** both conclusions compile with standard axioms only; the permutation-and-sign-flip action and the AdamW step are defined concretely, not assumed as hypotheses; `HANDOFF_G1.md` lists every hypothesis of the final theorem next to the sentence of the paper proof it corresponds to. If Gaussian initialization cannot be handled without measure theory, say so: the finite version is a lemma toward Theorem 15, and the claim stays "paper proof + finite case in Lean".

### G2. Linear pseudo-Boolean encoding in Lean (gap B1)

`Cerp.pbToExpr` expands a fan-in-`d` threshold neuron as an `O(2^d)` Shannon tree. Replace it (or add a second path) with an `O(d·w)` encoding, e.g. a binary adder or sorting network, with a soundness proof against `evalTNet`.

**Done when:** the `xor4` net (5 nodes) is verified against its `Expr` spec by pure kernel `decide` (no `native_decide`) in under 60 s, and `xor3` still passes. Report both timings.

### G3. Care-set compilation at 8–10 inputs (gap B2; unblocks gap A6)

`cerp/netsolve.py` finds minimum layered threshold nets for partial functions (a care mask) up to n = 6. Make it work at n = 8 and n = 10: symmetry breaking on hidden units, incremental solving over hidden width, lower-bound certificates via `bounds.not_threshold_cert_partial` and its two-halfspace analogue.

Benchmark, fixed in advance: for each n in {8, 10}, 100 targets from `experiments/spike36.py`'s generator (seeds 8,800 and 8,810) with 75% of inputs in the care set.

**Done when:** at n = 8, at least 90% of tasks return a verified net with a certificate that no cheaper layered net exists, within 60 s each on 4 cores. Report the n = 10 numbers whatever they are. Every returned net is checked with `kernel.evaluate` on all care points.

### G4. No-transfer lemma in Lean (gap C2)

The lemma named "No-transfer lemma" in `THEORY.md` / claim P077: symmetrizing a predictor over the exact stabilizer of the labelled data cannot change expected accuracy on unlabelled points. Finite version, standard axioms.

**Done when:** it compiles and the handoff maps each hypothesis to the paper statement.

### G5. `parity4` needs 5 neurons (gap B3)

Certify that 4-input parity has no layered threshold net with 4 neurons. The enumeration is about 1.1 × 10⁹ cases; reduce it with the signed-permutation symmetry `B₄`, and check the reduced certificate in Lean or with `cerp/kernel_bounds.py`.

**Done when:** a kernel-checked certificate exists and its checker runs in under 30 min. A proof that the reduction is sound must be part of it.

### G6. Make the intermittent test deterministic (gap D2)

`tests/test_localrules.py::test_search_keeps_a_working_rule_working` fails on some runs (score 0.875 against 0.9). Do not lower the bar and do not skip the test. Fix the seeds so the run is reproducible, or change the test to average over a fixed set of seeds with the bar justified from the measured distribution (mean 0.95, min 0.875 over 20 seeds).

**Done when:** 20 consecutive `pytest -q` runs pass.

### G7. Work through the prior-art reading queue (gap D3)

`charter/PRIOR_ART.md` §4 lists about 20 papers found on 2026-11-14 and not yet read, with the reason each matters. Read each **in full** and add a row to `charter/LITERATURE_REVIEW.md` §5. Start with 2606.04045 (it may already state our sufficiency result), then 1805.08522, 2302.07263, the proofs of 2410.19092, 2512.20607, 2507.19680.

Then extend the sweep to what one arXiv-centred pass could not reach: computational mechanics (Crutchfield, Shalizi), formal concept analysis (Ganter & Wille), rough sets (Pawlak; Skowron & Rauszer), Myhill–Nerode and exact automata learning (Angluin), symbol grounding (Harnad; Mollo & Millière), identifiability in nonlinear ICA and causal representation learning (Hyvärinen; Schölkopf et al.), causal abstraction (Geiger et al.; Beckers & Halpern), Occam learning and minimum circuit size (Blumer et al.; Kearns & Vazirani).

**Searching.** Use `python -m cerp.litsearch "<query>"` (Crossref and the arXiv API; free, no account). A hit is a lead, not a reading.

**Done when:** every queued paper has a row with what was read (full text / abstract only), its main claim, and one of {anticipates, contradicts, orthogonal} for a named claim of ours, with the sentence that shows it. Then update the verdict table in `PRIOR_ART.md` §1 where a verdict changes. Abstract-only rows must say so. No row for a paper that was not opened. If a paper already contains one of our results, say so at the top of the handoff.
