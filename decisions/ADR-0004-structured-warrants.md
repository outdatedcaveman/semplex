# ADR-0004: Replace single status labels with structured warrants

**Status:** accepted · **Date:** 2026-11-06 · **Amends:** charter §10 (with migration rules, per §13.19)

## Context

Spikes 01 (F7) and 02 (F8) found outputs with no honest §10 label. Both also found that the labels don't form a total order, yet the v0 ledger treated them as one.

## Decision

A claim stores:
- a **warrant**: a set of methods, plus a trusted base, plus the named premises it is conditional on;
- an **outcome**: asserted, refuted, out of scope, or undetermined.

Derived claims receive the join of their dependencies' warrants. §10 labels are computed as a projection for reporting, and two labels are added: WITNESSED and COMPUTED-UNCERTIFIED. Migration rules are in `experiments/SPIKE_04_REPORT.md`.

## Consequences

- Existing recorder APIs keep their names, so callers needed only three edits.
- Any future warrant kind (e.g. "proof-assistant checked") is one enum member plus one edge in the order.
- Reports must say which premise a conditional claim rests on, and they now can.
