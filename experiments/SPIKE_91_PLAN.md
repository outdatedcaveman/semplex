> Renumbered from canonical distinction-calculus `SPIKE_21_PLAN` to `SPIKE_91_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 21 — Resource-relative probe presheaves

**Date:** 2026-11-21  
**Status:** finite exact model passes; general Lean proof drafted but not yet compiled (resource gate)  
**Prior art:** Marsden & Zwart (2018), *Quantitative Foundations for Resource Theories*, DOI 10.4230/LIPIcs.CSL.2018.32  
**Code:** experiments/resource_relative_probe_sieves.py  
**Tests:** tests/test_resource_relative_probe_sieves.py  
**Results:** artifacts/resource-relative-probe-sieves-20261121.json

## Research question

Can resource-bounded executable probes be made compositionally coherent without requiring closure under every physical transformation, including costly refinements?

## Candidate theorem

Let \(\mathcal C\) be a category, and let \(\mathcal F\subseteq\mathcal C\) be a wide subcategory of zero-cost/free refinements. Let \(c:\mathrm{Mor}(\mathcal C)\to Q\) take values in an ordered commutative monoid \((Q,\oplus,0,\le)\), satisfying:
- \(c(id_X)=0\);
- \(c(g\circ f)\le c(g)\oplus c(f)\);
- \(c(u)=0\) for \(u\in\mathcal F\).

For target \(X\) and budget \(B\), define
\[
M_B(X)(P)=\{f:P\to X\mid c(f)\le B\},\qquad P\in\mathcal F.
\]

Then precomposition by \(u:Q\to P\) in \(\mathcal F\) preserves the budget:
\[
c(f\circ u)\le c(f)\oplus 0=c(f)\le B.
\]
Thus \(M_B(X)\) is a subpresheaf of the restriction \(\mathcal C(-,X)|_{\mathcal F^{op}}\).

For any target arrow \(h:X\to Y\) of cost \(K\), postcomposition induces a grade-shifting map:
\[
M_B(X)\longrightarrow M_{K\oplus B}(Y),\qquad f\mapsto h\circ f.
\]
Associativity makes this map natural with respect to free refinements.

The result generalizes immediately to vector-valued costs in ordered commutative monoids.

## Finite test model

Objects \(R,Q,P,X,Y\), with:
- \(u:Q\to P\) free, cost 0;
- \(g:P\to X\), cost 1;
- \(h=g\circ u:Q\to X\), cost 1;
- \(v:R\to Q\), paid, cost 2;
- \(w=u\circ v:R\to P\), cost 2;
- \(k=h\circ v=g\circ w:R\to X\), cost 3;
- \(t:X\to Y\), cost 2;
- \(tg=t\circ g\), \(th=t\circ h\), \(tk=t\circ k\), with costs 3,3,5.

The free subcategory contains identities and \(u\), but not \(v\) or \(w\).

At budget 1:
- the affordable arrows into \(X\) are \(\{id_X,g,h\}\);
- this family is a sieve relative to free refinements;
- it is not a sieve in the full category, because precomposition of \(h\) by paid \(v\) produces \(k\), cost 3.

The costly target transformation \(t\), cost 2, maps the budget-1 profile into the budget-3 profile on \(Y\): \(id_X\mapsto t\), \(g\mapsto tg\), \(h\mapsto th\).

## Falsifiers

- A free arrow has nonzero cost.
- Cost subadditivity fails.
- A free precomposition takes an affordable arrow outside the same budget.
- Grade-shift postcomposition fails its \(B+K\) bound.
- Naturality under free refinements fails.

## Prior-art guardrail

Marsden & Zwart (2018) already provide quantale-enriched resource categories, cost/probability quantales, presheaves, profunctors, a separation of free and costly conversions, and bimodules closed under pre/postcomposition by free multi-conversions. This candidate theorem is an application/specialization of that established machinery, not a claim to invent resource-enriched categories or free/costly categorical semantics.

The potential Semplex contribution, if any, lies in connecting these resource-relative probe presheaves to causal response semantics, higher mapping-space reconstruction/full abstraction, and a physically calibrated distortion certificate. This needs further theorem-by-theorem prior-art review.

## Acceptance criteria

- Finite category identities, associativity, and cost subadditivity pass.
- Affordable probes are closed under free precomposition at every tested budget.
- Budget-1 probes fail closure under the paid refinement, as expected.
- Costly postcomposition shifts budget correctly and is natural.
- All tests pass.
- General Lean module is not reported as verified until compilation and axiom audit complete.
