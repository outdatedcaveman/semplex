# Spike 06: The kernel's judgments, proved in Lean 4

**Date:** 2026-11-06 · **Charter refs:** Layer A, §7.5, §10, §14 (last question) · **Status:** complete

## Question

Up to now, "PROVED-IN-FRAGMENT" has meant *decided by about 220 lines of Python*. Can the kernel's two central judgments be restated and **proved correct** in a proof assistant? Can concrete claims about our artifacts then be checked by that assistant's kernel? And what does that grade of trust cost?

## What was proved (`proofs/lean/Cerp.lean`, Lean 4.12.0, core library only)

| Theorem | Statement (informal) | Axioms |
|---|---|---|
| `decideEquiv_correct` | For scoped expressions: `decideEquiv n e₁ e₂ = true ↔ ∀ σ : ℕ → Bool, eval σ e₁ = eval σ e₂`. Spike 01's exhaustive kernel is **sound and complete** over *all* assignments, not just the 2ⁿ it enumerates | propext, Quot.sound |
| `decideTask_correct` | Same for task-relative equivalence: agreement on every σ in the care set | propext, Quot.sound |
| `allEnvs_complete`, `eval_congr` | The 2ⁿ enumerated environments represent every assignment on the relevant variables | propext (+ Quot.sound) |
| `propagate_sound`, `rup_sound` | Unit propagation from a consistent state never fabricates a conflict, so a RUP lemma holds in every model of the formula | propext, Quot.sound |
| `checkAll_sound` / `unsat_of_certificate` | **If the checker accepts a certificate, no assignment satisfies the formula** | propext, Quot.sound |

There is no `sorry` and no `native_decide` in the library. The axiom audit is in `proofs/lean/CHECK_LOG.txt`.

## The bridge (`cerp/lean_bridge.py`)

Concrete claims become Lean files. Lean's kernel checks them by evaluating the *proved* deciders (`decide`). A result is accepted only if all three hold:
1. Lean exits cleanly.
2. `#print axioms` lists only standard axioms (no `sorryAx`; `Lean.ofReduceBool` only in the explicitly labeled native tier).
3. **Round trip:** Lean prints back the terms it checked, and they must equal the bridge's rendering of the source artifacts, so a translation error cannot pass unnoticed.

The ledger gains a `proof_assistant` recorder that names the Lean kernel, the compiler (native tier only), and every unverified bridge step in the warrant's trusted base.

## Hypotheses and verdicts

| # | Hypothesis | Verdict |
|---|---|---|
| H6.1 | The decision procedures can be proved correct in core Lean without heavy libraries | **Held**: about 330 lines, standard axioms only |
| H6.2 | Concrete artifact claims can be proof-assistant-checked end to end | **Held** for expression equivalence up to n=10 and for RUP certificates up to 8 inputs (kernel tier) and 64 inputs (native tier). False claims are rejected and truncated certificates fail |
| H6.3 | Proof-assistant trust is affordable | **Broke, informatively**: 10³–10⁵× slower than the Python kernel (F1) |

## Results (`results/spike06.json`)

**Exhaustive expression equivalence:**

| n | Python kernel | Lean kernel (`decide`) |
|---|---|---|
| 4 | <1 ms | 0.18 s |
| 8 | 1 ms | 1.4 s |
| 10 | 5 ms | 7.2 s |

**RUP certificate (ripple vs prefix carry):**

| Inputs | Lemmas | Python kernel | Lean kernel | Lean native (compiler trusted) |
|---|---|---|---|---|
| 4 | 8 | <1 ms | 5.4 s | 0.4 s |
| 8 | 25 | 1 ms | 46.6 s | 1.4 s |
| 32 | 117 | 3 ms | — | 26 s |
| 64 | 250 | 15 ms | — | 146 s |

## Findings

**F1. Trust has a price curve, and now we have it measured.** The same certificate can be checked at three trust tiers:

| Tier | Trusted base | Cost |
|---|---|---|
| Python kernel | ~400 unverified lines + CPython | 1× |
| Lean kernel | Small, audited, but evaluates by reduction | ~10⁴–10⁵× |
| Lean native | Proved algorithm + Lean compiler | ~10²–10⁴× |

This makes charter §14's last question ("system-level reliability when foundation, proof assistant, hardware … have residual assumptions") quantitative: **each step down in trusted base cost about two orders of magnitude in time** here.

A rational policy, which we propose:
- Check everything at the cheap tier.
- Escalate to the expensive tiers only for claims that other claims depend on heavily.

The ledger already knows those dependencies, via `affected_by`.

**F2. Proved deciders turn "decided" into "proved".** `decideEquiv_correct` closes the gap between "the kernel enumerated 2ⁿ points" and "the functions are equal for *every* σ : ℕ → Bool". This is a semantic statement the Python kernel could only assume. `allEnvs_complete` and `eval_congr` (only scoped variables matter) do the work.

**F3. Trusted bases are not ordered by set inclusion.** With the Spike 04 warrant order, a Lean-proved claim and a Python-kernel claim come out **incomparable**: the trusted bases differ and neither contains the other. That is correct as far as it goes, but it cannot say that *the Lean kernel deserves more trust than 220 lines of Python*. The warrant theory needs a **trust preorder over components**, which is itself a claim with a warrant (audits, independent implementations, usage history). → Q-W2, and an input to the theory document.

**F4. The weakest link moved, and is now named.** For circuit claims, Lean proves that the *CNF* is unsatisfiable. The step "CNF unsat ⇒ circuits equivalent" rests on the Python Tseitin encoder, which is not yet verified. It appears explicitly in the trusted base ("bridge"). Verifying Tseitin in Lean is a well-scoped next step.

## How to reproduce

```bash
export CERP_LEAN=/path/to/lean-4.12.0/bin/lean
cd proofs/lean && $CERP_LEAN Cerp.lean              # library: proofs
python -m pytest -q tests/test_lean.py              # bridge (skipped if CERP_LEAN unset)
python -m experiments.spike06                       # tier measurements
```
