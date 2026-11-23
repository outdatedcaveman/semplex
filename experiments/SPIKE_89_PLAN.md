> Renumbered from canonical distinction-calculus `SPIKE_19_PLAN` to `SPIKE_89_PLAN` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 19 — Resource-indexed restricted Yoneda: finite exact benchmark

**Date:** 2026-11-21  
**Status:** finite benchmark implemented; exact checks pass  
**Code:** `experiments/restricted_yoneda_probe_benchmark.py`  
**Tests:** `tests/test_restricted_yoneda.py`  
**Results:** `artifacts/restricted-yoneda-probe-benchmark-20261121.json`

## Research question

What is lost when a representation is built from a restricted family of probes rather than all representables? In particular, does separating objects suffice to reconstruct the morphisms and their composition?

## Formal setup

For a small category \(\mathcal C\) and a full subcategory \(\mathcal P\hookrightarrow\mathcal C\), define the restricted Yoneda functor

\[
y_{\mathcal P}:\mathcal C\to[\mathcal P^{op},\mathbf{Set}],
\qquad
y_{\mathcal P}(X)(P)=\operatorname{Hom}_{\mathcal C}(P,X).
\]

For \(X,Y\), the canonical map is

\[
\Phi_{X,Y}:\operatorname{Hom}_{\mathcal C}(X,Y)
\longrightarrow
\operatorname{Nat}(y_{\mathcal P}(X),y_{\mathcal P}(Y)),
\]

sending \(f:X\to Y\) to postcomposition \(g\mapsto f\circ g\).

The benchmark distinguishes:
- **object separation:** \(y_{\mathcal P}(X)\not\cong y_{\mathcal P}(Y)\) for distinct objects;
- **faithfulness:** \(\Phi_{X,Y}\) injective;
- **fullness:** \(\Phi_{X,Y}\) surjective;
- **full faithfulness:** both, for every pair \(X,Y\).

For a finite category, the script enumerates all natural transformations exactly, compares them with the image of \(\Phi\), and reports separate faithfulness/fullness defects.

## Test categories

1. **Walking arrow:** \(0\to1\). The singleton probe subcategory \(\mathcal P=\{1\}\) is fully faithful/dense; \(\mathcal P=\{0\}\) is not.
2. **Parallel-pair category:** two objects \(A,B\), two distinct arrows \(f,g:A\rightrightarrows B\), and identities. A single probe \(A\) or \(B\) separates the objects but does not yield a fully faithful restricted Yoneda functor. Both probes together recover full faithfulness.
3. **Discrete pair:** two unrelated objects. The probe \(A\) separates the objects but introduces an extra natural transformation \(y(B)\to y(A)\), so the functor is not full.

The parallel-pair probe costs are declared as \(c(A)=1,c(B)=3\). These are synthetic bookkeeping weights, not measured physical costs.

## Hypotheses and falsifiers

| ID | Hypothesis | Falsifier |
|---|---|---|
| H19.1 | Object separation is strictly weaker than full faithfulness | A general theorem or the exact enumerations show no distinction in the test categories |
| H19.2 | The parallel-pair category has minimum full-faithfulness probe cost 4 under the declared weights | Any probe subset of cost below 4 is fully faithful |
| H19.3 | A proper dense probe subcategory can suffice | The walking-arrow \(\{1\}\) restriction fails a full-faithfulness check |
| H19.4 | Natural transformations, not only componentwise profile cardinalities, are necessary to test reconstruction | The script's naturality constraints do not affect the results |

## Methods and verification

- Validate identity, source/target, composition, and associativity in each finite category.
- Enumerate all functions between the finite hom-sets.
- Enumerate all natural transformations satisfying every probe-arrow naturality square.
- Compute the canonical image of every original morphism.
- Compare object-profile isomorphism, faithfulness, and fullness.
- Exhaustively enumerate every probe subset and its total declared cost.
- Test the results in pytest.

No stochastic sampling, floating-point arithmetic, external solver, or third-party library is used.

## Acceptance criteria

- All three categories validate.
- All natural transformations are enumerated, not sampled.
- All expected finite examples pass.
- The report clearly states that finite ordinary-category enumeration is not a theorem about arbitrary \(\infty\)-categories or physical realizability.
- No commit, push, or merge is made.
