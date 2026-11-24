> Renumbered from canonical distinction-calculus `SPIKE_19_REPORT` to `SPIKE_89_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 19 — Resource-indexed restricted Yoneda: finite exact benchmark

**Status:** PASS — exact finite enumeration; 7/7 tests pass.  
**Date:** 2026-11-21  
**Plan:** experiments/SPIKE_19_PLAN.md  
**Implementation:** experiments/restricted_yoneda_probe_benchmark.py  
**Tests:** tests/test_restricted_yoneda.py  
**Result:** artifacts/restricted-yoneda-probe-benchmark-20261121.json

## 1. Main result

The finite experiment establishes a distinction that matters for the Semplex programme:

> Separating objects by their probe profiles does not suffice to reconstruct the category. Full abstraction requires reconstruction of every hom-set through natural transformations, not merely distinguishability of objects.

This is not a new theorem in category theory. It is an exact executable benchmark illustrating the difference between a conservative/faithful representation and a fully faithful one.

## 2. Exact results

### 2.1 Walking arrow

For the category \(0\to1\), the singleton full subcategory \(\mathcal P=\{1\}\) is fully faithful under restricted Yoneda. Thus a proper probe subcategory can be dense; all objects need not be probed.

The alternative \(\mathcal P=\{0\}\) fails: both restricted profiles are singleton-valued and the reverse hom-set is spuriously represented by a natural transformation.

### 2.2 Parallel-pair category

Let \(\mathcal C\) have two objects \(A,B\), two distinct arrows \(f,g:A\to B\), and identities.

| Probe family | Object separating? | Faithfulness defect | Fullness defect | Fully faithful? |
|---|---:|---:|---:|---:|
| \(\varnothing\) | no | 1 | 1 | no |
| \(\{A\}\) | yes | 0 | 4 | no |
| \(\{B\}\) | yes | 1 | 0 | no |
| \(\{A,B\}\) | yes | 0 | 0 | yes |

With declared costs \(c(A)=1,c(B)=3\), the minimum cost of a fully faithful probe family is exactly 4. Both singleton choices separate the objects, but neither reconstructs all morphisms:
- probing \(A\) yields extra natural transformations, including spurious endomorphism-like transformations of the profile of \(B\);
- probing \(B\) collapses the two distinct arrows \(f\) and \(g\).

This is a concrete demonstration that object classification, faithful encoding, and full reconstruction are distinct requirements.

### 2.3 Discrete pair

For a discrete two-object category and \(\mathcal P=\{A\}\), the two profiles are non-isomorphic, so objects are separated. Nevertheless, there is one extra natural transformation in a hom direction where the original category has no morphism. The restricted functor is not full.

## 3. Mathematical interpretation

The canonical comparison is

\[
\Phi_{X,Y}:
\operatorname{Hom}_{\mathcal C}(X,Y)
\to
\operatorname{Nat}(y_{\mathcal P}(X),y_{\mathcal P}(Y)).
\]

Its kernel measures morphisms collapsed by the representation; its cokernel here is represented by extra natural transformations not induced by any original morphism. For finite hom-sets, the code reports the corresponding cardinality defects:
\[
d_{\mathrm{faith}}(X,Y)=|\operatorname{Hom}(X,Y)|-|\operatorname{im}\Phi_{X,Y}|,
\]
\[
d_{\mathrm{full}}(X,Y)=|\operatorname{Nat}(y_{\mathcal P}X,y_{\mathcal P}Y)|-|\operatorname{im}\Phi_{X,Y}|.
\]

These are exact finite diagnostics, not general metrics for enriched or higher categories.

The walking-arrow example also prevents an overcorrection: the required probe family need not contain every object. The correct condition is density/full faithfulness, not maximal probe coverage.

## 4. Verification

\`\`\`text
pytest -q tests/test_restricted_yoneda.py
7 passed in 0.11s
exit code 0
\`\`\`

The script independently validates category identities and associativity, enumerates all component functions, imposes naturality for every arrow in the probe subcategory, and checks the canonical Yoneda map for every ordered pair of objects.

## 5. Limits

- These are finite ordinary categories and set-valued presheaves.
- Probe costs are arbitrary synthetic weights, not empirically calibrated costs.
- The model assumes all morphisms from a probe object to a target are available. It does not yet represent a physically executable subset of those morphisms.
- No stochastic, quantum, differential, or higher-homotopy mapping spaces are included.
- The finite cardinality defects are not stable under arbitrary equivalences or enrichment changes.
- The result does not establish a new category-theoretic theorem or a new physical theory.

## 6. Next mathematical step: executable subpresheaves

The next version must distinguish the abstract restricted Yoneda profile from the physically executable part of it.

For each target \(X\), define a subfunctor

\[
M_X\hookrightarrow \operatorname{Hom}_{\mathcal C}(P(-),X)
\]

whose elements are the probe maps that can actually be implemented under a specified physical and resource regime. Closure under precomposition by probe morphisms is required for \(M_X\) to be a presheaf. This is a nontrivial admissibility condition: an arbitrary list of executable probes need not be compositionally closed.

The research target becomes:

1. characterize when the executable subpresheaves \(M_X\) separate objects;
2. characterize when they induce full faithfulness on the protected subcategory;
3. quantify the obstruction when exact reconstruction fails;
4. optimize probe acquisition under costs without assuming scalar costs are universally comparable;
5. compare with existing active experimental design, causal identification, and categorical realization theorems.

The likely challenge is not the restricted Yoneda construction itself. It is a physically grounded criterion for executable subpresheaf closure, plus a resource-sensitive reconstruction/approximation theorem.

