# Spike 03: Proof-carrying equivalence beyond the exhaustive wall

**Date:** 2026-11-06 · **Charter refs:** §7.2, §7.5, §10 · **Status:** complete · **Motivated by:** Spike 01 F3

## Question

Spike 01's kernel decides equivalence by checking every input, which is infeasible past n≈16–20. The charter's §7.2 answer is proof-carrying translation: an untrusted search produces a certificate, and a small trusted checker validates it. Does that work here, and what does it actually buy?

## What was built

- **`cerp/kernel.py` v0.2 (trusted):**
  - The kernel **builds the miter formula itself** from the two artifacts with its own Tseitin encoding, so an untrusted encoder can't substitute a different formula.
  - `check_rup` replays a RUP certificate. Each lemma must follow from the formula plus earlier lemmas by unit propagation alone, ending in the empty clause.
  - `check_counterexample` certifies *non*-equivalence with 2 evaluations.
  - Care sets give task-relative equivalence by the same route.
- **`cerp/sat.py` (untrusted):** a CDCL solver (two watched literals, first-UIP learning, VSIDS, phase saving, restarts) that emits its learned clauses as the certificate.
- **`cerp/benchmarks.py`:** structurally different circuits for the same function (ripple vs prefix-tree carry; MSB-scan vs borrow-chain comparison), plus a deliberately buggy variant.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H3.1 | Proof-carrying equivalence passes the n≈16 wall | **Held for structured circuits**: n=64 certified in ≤ 0.1 s. **Not for random functions** (F2) |
| H3.2 | Checking a certificate is much cheaper than finding it | **Broke**: check/search ratio 0.4–1.4 (F3). The gain is in *trust*, not speed |
| H3.3 | Corrupted, truncated or borrowed certificates are rejected | **Held** (tests: truncation, random lemma corruption, a valid certificate replayed against a same-size false claim) |
| H3.4 | Non-equivalence has a succinct certificate | **Held**: a counterexample is checked in about 0.1 ms at n=64 |

## Results (`results/spike03.json`)

| Pair | n | Search | Kernel check | Lemmas | Exhaustive kernel |
|---|---|---|---|---|---|
| carry ripple vs prefix | 16 | 1 ms | 1 ms | 45 | 2.5 s |
| carry ripple vs prefix | 64 | 30 ms | 10 ms | 250 | ~10⁷ years (extrap.) |
| a<b msb-scan vs borrow | 64 | 83 ms | 37 ms | 370 | — |
| carry vs BUGGY prefix | 64 | 8 ms | 0.15 ms (counterexample) | — | — |
| random expr vs its BDD circuit | 16 (BDD 4,515 nodes) | 80 s | 117 s | 14,050 | 371 s |
| random expr vs its BDD circuit | 16 (BDD 1,987 nodes) | 11 s | 15 s | 5,727 | 151 s |
| random expr vs its BDD circuit | 20 (BDD 1,040 nodes) | 1.5 s | 2.1 s | 1,870 | — |

Rows where the random expression collapsed to a constant (BDD size 1) are omitted as degenerate.

## Findings

**F1. The wall moves from "number of inputs" to "structure of the proof".** For arithmetic-like circuits, certificate size grows roughly linearly with width: 250 lemmas at n=64. The exhaustive wall at n≈16–20 simply disappears for them.

**F2. For unstructured functions, there is no free lunch.** Cost tracks the function's intrinsic complexity (BDD size), not n. A random 16-input function with a 4,515-node BDD needed 14,050 lemmas and was only about 2× faster than exhaustive checking end to end. This is consistent with equivalence being coNP-complete. The charter's "universality disciplined by explicit domain boundaries" applies here: proof-carrying works where the domain has structure, which is exactly where engineered artifacts live.

**F3. Certificates buy trust, not speed.** Kernel checking took 0.4–1.4× the solver's search time, because RUP replay redoes unit propagation for every lemma. What the certificate buys is that the 230-line search heuristics (VSIDS, restarts, learning) are **out of the trusted base**. Only Tseitin encoding plus unit propagation, about 170 kernel lines, must be right. Charter §7.5's "acceptance mediated by a smaller, trusted verifier" is achieved; "cheaper to check" is not, for this certificate format. Formats with hints (LRAT) would make checking linear-time. → Q-C1.

**F4. The kernel must own the formula.** If the encoder were untrusted, a certificate could prove the unsatisfiability of *some other* formula. A test demonstrates this: a valid certificate is replayed against a same-size false claim and rejected. This is the general shape of proof-carrying code: the checker must derive the *statement* from the claim, not accept it from the prover.

**F5. The trusted base grew, and the warrant model records it.** The kernel went from 220 to about 410 lines. That is past ADR-0002's "revisit at 300" threshold, so the threshold was revisited: the growth is the RUP checker and the encoder, both still stdlib-only and independence-tested. The Spike 04 warrant names the trusted base per claim, so this growth is visible rather than silent. Moving the kernel into a proof assistant (Spike 06) is now better motivated.

## Gaps

- No clause deletion (RUP, not DRUP/LRAT), so certificates are larger and checking is slower than necessary.
- The solver is a teaching-grade CDCL. Industrial solvers would push F2's boundary further, but would not remove it.
- Only expr and circuit artifacts take the RUP route. BDD and DFA artifacts would need an encoding or a conversion step.
