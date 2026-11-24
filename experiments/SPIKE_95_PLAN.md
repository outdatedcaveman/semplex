> Renumbered from canonical distinction-calculus `SPIKE_25_PLAN` to `SPIKE_95_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 25 — Resource-bounded Wilson-loop realization in a finite POMDP

**Date:** 2026-11-22  
**Status:** PASS — 13/13 focused tests; exact rational model  
**Code:** experiments/finite_holonomy_pomdp.py  
**Tests:** tests/test_finite_holonomy_pomdp.py  
**Report:** research/FINITE_HOLONOMY_POMDP_REALIZATION.md  
**Artifact:** artifacts/finite-holonomy-pomdp-20261122.json

## Question

Can the resource-indexed response quotient and posterior predictive-state construction be instantiated in one controlled partially observed physical model where local probes provably miss a global gauge invariant?

## Prior-art gate

Gauge holonomy, Wilson loops, finite POMDP belief states, Bayesian predictive sufficiency, and matrix identifiability are established. This spike does not claim any of those as new. The narrow contribution is an executable bridge fixture combining primitive physically interpretable edge controls, gauge-invariant closed-path readouts, explicit intervention costs, a hidden holonomy sector and agent posterior, and an exact resource threshold and observation-noise threshold for full abstraction.

## Model

- Physical configuration: Z3 connection on a three-cycle.
- Hidden gauge-invariant sector: additive Wilson-loop holonomy theta in Z3.
- Primitive controls: clockwise/counterclockwise edge traversal, each cost 1.
- Physical path state: current vertex and accumulated parallel-transport phase.
- Readout: only gauge-invariant closed-path phase, passed through a symmetric Z3 observation channel.
- Agent state: a probability belief over the three holonomy sectors.

## Hypotheses and kill criteria

- H25.1: holonomy is invariant under every vertex gauge transformation and classifies the 27 finite connection configurations into exactly three orbits. Kill if exhaustive enumeration finds a counterexample.
- H25.2: every closed control word of length below 3 has zero winding; the first informative path costs 3. Kill if any shorter closed word has nonzero holonomy response.
- H25.3: all beliefs are response-equivalent below budget 3. Kill if any affordable closed path distinguishes beliefs.
- H25.4: at budget at least 3, the posterior-belief representation is fully abstract iff eta != 1/3. Kill if the channel determinant or exact response enumeration disagrees.
- H25.5: eta=1/3 erases all information, including under repeated loop observations. Kill if any finite outcome sequence depends on the prior.

## Verification

All arithmetic is exact over integers and fractions. Thirteen focused tests pass. The script exhaustively checks all 27 connections, all 27 gauge transformations, and every closed control word up to length six.

## Limits

This is a finite gauge-theoretic POMDP benchmark, not an experiment on a physical ring, not a new result in gauge theory or POMDP theory, and not evidence that higher-categorical representations outperform conventional models. The next empirical test must compare compositional path-aware and local-only predictors at matched observation and compute budgets.
