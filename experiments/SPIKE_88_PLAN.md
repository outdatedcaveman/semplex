> Renumbered from canonical distinction-calculus `SPIKE_18_PLAN` to `SPIKE_88_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 18 — Higher-gauge moduli, local probe insufficiency, and truncation

**Status:** exact finite model implemented; all assertions pass; Lean core formalization compiles and axiom audit is recorded.  
**Date:** 2026-11-21  
**Companion:** `experiments/higher_gauge_surface_holonomy.py`  
**Theory:** `research/HIGHER_CATEGORICAL_CAUSAL_SEMANTICS_2026-11-21.md`

## Question

Can a minimal finite higher-gauge model exhibit, in one controlled construction:

1. globally distinct semantic sectors that every proper local face-subset marginal fails to distinguish;
2. nontrivial higher automorphism data that disappears under 1-truncation;
3. a strict 2-groupoid whose composition/coherence laws can be checked exhaustively;
4. a corresponding cochain/holonomy theorem package formalized in Lean?

This is a finite mathematical test of the claim that relational semantics may require global composition and higher coherence, not just local labels or ordinary equivalence classes.

## Model

Use the boundary complex of a tetrahedron, a triangulation of \(S^2\), with coefficients \(A=\mathbb Z_2\):

\[
C^0\cong\mathbb Z_2^4
\xrightarrow{d_0}
C^1\cong\mathbb Z_2^6
\xrightarrow{d_1}
C^2\cong\mathbb Z_2^4.
\]

- Objects: face 2-cochains \(B\in C^2\).
- 1-morphisms: edge gauge parameters \(\Lambda\in C^1\), with \(B'=B+d_1\Lambda\).
- 2-morphisms: vertex gauge-of-gauge parameters \(\eta\in C^0\), with \(\Lambda'=\Lambda+d_0\eta\).
- Composition at each level is addition over \(\mathbb Z_2\).
- Surface holonomy is \(W(B)=(-1)^{\sum_f B_f}\).

The model is the standard finite cochain presentation of the 2-form gauge mapping 2-type \(\operatorname{Map}(S^2,K(\mathbb Z_2,2))\).

## Hypotheses and falsifiers

| ID | Hypothesis | Falsifier |
|---|---|---|
| H18.1 | \(\operatorname{im}d_1\) is exactly the even-parity face subspace, giving two gauge sectors | A face field of even parity is not a coboundary, or an odd one is |
| H18.2 | Every proper face-subset marginal is uniform and identical in the two sectors; full surface holonomy separates them | Any proper subset has sector-dependent marginal, or surface holonomy is not gauge-invariant |
| H18.3 | \((\pi_0,\pi_1,\pi_2)\) has cardinalities \((2,1,2)\) | Any computed kernel/image quotient differs |
| H18.4 | The gauge data form a strict 2-groupoid under the specified compositions | Identity, inverse, composition, horizontal composition, or interchange fails |
| H18.5 | The cochain identity and holonomy claims are Lean-provable with disclosed axiom dependencies | Compilation failure or an unreported/custom axiom is required |

## Methods

1. Exhaustively enumerate all \(2^6\) edge gauge parameters and all \(2^4\) face fields.
2. Enumerate all \(2^4\) vertex gauge-of-gauge parameters.
3. Compute \(\operatorname{im}d_0\), \(\ker d_0\), \(\operatorname{im}d_1\), and \(\ker d_1\).
4. Check all proper face-subset marginals, all gauge orbits, surface holonomy, and the finite strict 2-groupoid laws.
5. Formalize the cochain identities, kernel/image characterizations, and holonomy invariance in Lean 4.12 core.
6. Audit theorem axioms explicitly.

No stochastic sampling, floating-point arithmetic, learned model, or external solver is used.

## Acceptance criteria

- All exact assertions pass.
- The report separates the finite theorem from claims about physical observability or universal semantics.
- Lean compilation and axiom audit are recorded separately from exhaustive Python checks.
- No commits, pushes, or merges are made without explicit authorization.
