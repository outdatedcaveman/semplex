> Renumbered from canonical distinction-calculus `SPIKE_20_PLAN` to `SPIKE_90_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 20 — Weighted semiotic categories, executable sieves, and threshold closure

**Date:** 2026-11-21  
**Status:** finite counterexample and tests pass  
**Primary antecedent:** Constantin Thiopoulos (1992), “Towards a Logic of Semiotic Systems,” *Mathématiques et sciences humaines* 117, 49–60.  
**Code:** experiments/costed_executable_sieves.py; experiments/semiotic_threshold_sieve_counterexample.py  
**Tests:** tests/test_costed_executable_sieves.py; tests/test_semiotic_threshold_sieve.py

## Question

Can a multiplicative confidence/weight on morphisms be thresholded to produce a sieve (and therefore a presheaf of admissible probes), as proposed in Thiopoulos's 1992 semiotic-category formalism? What changes when arrow costs are positive and resource-bounded?

## Source claim under examination

Thiopoulos defines:
\[
w(f\circ g)=w(f)w(g)
\]
and proposes the threshold family
\[
R_B(X)=\{f:Y\to X\mid w(f)\ge B\}
\]
as a sieve/topological interpretation (Definitions 2.20–2.21; Theorem 2.1).

A sieve on \(X\) must satisfy:
\[
f:Y\to X\in R,\ u:Z\to Y
\quad\Longrightarrow\quad
f\circ u:Z\to X\in R.
\]

## Finite counterexample

Use the category \(Q\xrightarrow{u}P\xrightarrow{g}X\), with \(h=g\circ u:Q\to X\). Assign:
\[
w(u)=0.5,\quad w(g)=0.9,\quad w(h)=w(g)w(u)=0.45,
\]
and identity weights 1.

At threshold \(B=0.8\), \(g\) and \(id_X\) lie in \(R_B(X)\), but \(h\) does not. Therefore \(R_B(X)\) is not a sieve. Its sieve closure adds the lower-confidence composite \(h\).

## General criterion to prove

For fixed \(B\), \(R_B(X)\) is a sieve exactly when:
\[
w(f)\ge B \Longrightarrow w(f\circ u)\ge B
\]
for every composable \(f,u\).

If \(w(f\circ u)=w(f)w(u)\) and this is required for every threshold \(B>0\), then for every positive-weight \(f\), all admissible precompositions must satisfy \(w(u)\ge1\). Thus multiplicative weights in \((0,1]\) do not generally yield sieve-closed threshold families. This criterion is elementary; the finite script is an executable counterexample, not a general Lean proof.

## Resource-cost analogue

In the same category, let implementation costs be \(c(g)=1,c(h)=3\). The budget sublevel \(\{g\}\) at budget 1 is not a sieve; its sieve closure adds \(h\) and costs 3. Therefore a budget cutoff on arrow costs is not automatically a physically executable subpresheaf.

## Acceptance criteria

- Category identities and associativity validate.
- Multiplicative weights satisfy the declared composite equation.
- The threshold family at 0.8 fails sieve closure.
- Its sieve closure adds h.
- The cost-budget family at 1 fails sieve closure and its closure exceeds budget.
- All tests pass.
- The paper is treated as a direct conceptual antecedent but its theorem is evaluated narrowly and charitably; no blanket dismissal of the paper is permitted.
