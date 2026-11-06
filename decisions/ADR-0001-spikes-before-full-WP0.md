# ADR-0001: Run hypothesis-driven spikes before completing WP0

**Status:** accepted · **Date:** 2026-11-06

## Context

Charter §11 says WP0 (glossary, foundation comparison, threat model) should be "approved before coding". Read literally, that sequences the program waterfall-style: foundations are decided before any component is tried. The project owners want an agile approach instead. Each goal is tackled modularly, and the assumptions behind it are checked against working code before effort is invested in breadth.

## Decision

We deviate from the literal §11 ordering in a bounded way:

- **Spikes may write code before WP0 is complete**, provided each spike declares its hypotheses and kill criteria up front, ships a ledger, and reports findings back as proposed charter amendments.
- **The non-negotiable parts of the charter still apply from day one.** These are proof/evidence separation, honest status labels, an independent verifier for anything labeled proved, recorded failures, and partiality on out-of-scope inputs. They are cheap to honor in small code and costly to retrofit.
- **WP0 deliverables are grown from spike evidence**, not written in advance. Example: the foundation comparison (Layer A) will be informed by what Spikes 01, 05 and 06 actually needed.

## Consequences

- Positive: assumptions get tested early. Spike 01 already broke two (F5, F6) and found a gap in the status taxonomy (F7). A document-first process would likely have frozen these.
- Negative: early code is disposable. The kernel, artifact formats and ledger shape will change. Mitigation: keep the kernel tiny and stdlib-only, and keep artifacts as plain data.
- Risk: spikes can drift into "building because it's fun". Mitigation: every spike must name the charter assumption it tests. A spike that can't is not started.
