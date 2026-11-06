# ADR-0002: Spike 01 stack (Python, stdlib-only kernel, exhaustive decision)

**Status:** accepted for Spike 01 only · **Date:** 2026-11-06

## Decision

- **Language:** Python 3, stdlib only (pytest for tests). It is the fastest way to iterate on what the objects even are.
- **Trusted kernel:** `cerp/kernel.py`. It imports nothing from the rest of the package (enforced by a test) and has its own interpreters. It decides claims by exhaustive enumeration (n ≤ 16), and it is the only code that can mint the `Verdict` objects the ledger requires for proof status.
- **Label scope:** "PROVED-IN-FRAGMENT" in this spike means *decided by the kernel*. The trusted base is the kernel, CPython and the hardware, and every such claim records this.

## Rejected alternatives for now

- **Proof assistant first (Lean 4 / Coq / Isabelle).** Correct long-term (charter Layer A), but too slow for finding out what the objects are. Scheduled as Spike 06, once F0's judgments have stabilized.
- **SAT/SMT-based equivalence.** Needed to pass the n≈16 wall, but only with checkable proofs (DRAT/LRAT) and an independent checker. Otherwise it adds a large trusted base. Scheduled as Spike 03.

## Revisit when

Any of the following happens: a fragment needs n > 16, a claim needs a guarantee stronger than "decided by a Python kernel", or the kernel grows past roughly 300 lines (it is 220 now).
