> Renumbered from canonical distinction-calculus `SPIKE_18_REPORT` to `SPIKE_88_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 18 — Higher-gauge moduli, local probe insufficiency, and truncation

**Status:** PASS — exact finite computation, Lean-checked cochain core, and explicit axiom audit.  
**Date:** 2026-11-21  
**Plan:** experiments/SPIKE_18_PLAN.md  
**Primary report/theory:** research/HIGHER_CATEGORICAL_CAUSAL_SEMANTICS_2026-11-21.md  
**Machine result:** artifacts/higher-gauge-surface-holonomy-20261121.json

## Result

The tetrahedral \(S^2\) with a \(\mathbb Z_2\)-valued 2-form gauge field realizes exactly the predicted 2-type:

\[
(\lvert\pi_0\rvert,\lvert\pi_1\rvert,\lvert\pi_2\rvert)=(2,1,2).
\]

The two \(\pi_0\) sectors have identical distributions on every proper subset of faces, while the global surface holonomy distinguishes them. The 2-groupoid has a nontrivial \(\pi_2\) represented by the constant nonzero 0-form gauge transformation; its 1-truncation erases this higher automorphism.

## Exact computation

| Quantity | Result |
|---|---:|
| Vertices / edges / faces | 4 / 6 / 4 |
| \(|\operatorname{im}d_0|\) | 8 |
| \(|\ker d_0|\) | 2 |
| \(|\operatorname{im}d_1|\) | 8 |
| \(|\ker d_1|\) | 8 |
| Gauge-orbit sizes | 8 and 8 |
| Proper face-subset marginals checked | 15 |
| Horizontal-composition instances | 1,048,576 |
| Interchange-law instances | 65,536 |
| Nontrivial 2-automorphisms of identity | 2 |

All assertions passed. The exact result is stored in the JSON artifact.

### Structural proof

Each edge of the tetrahedron belongs to exactly two faces, so its coboundary has even total face parity. Conversely, every pair of faces shares an edge, and the corresponding edge coboundary is the sum of that pair of face basis vectors. These pair-vectors generate the even-parity subspace. Hence \(\operatorname{im}d_1\) is exactly the even-parity subspace, so \(H^2(S^2;\mathbb Z_2)\cong\mathbb Z_2\).

For any proper subset of \(k<4\) faces and any fixed assignment on those faces, exactly \(2^{3-k}\) completions have either prescribed total parity. Thus every proper-subset marginal is uniform and sector-independent. The full parity/surface holonomy remains different.

The gauge-of-gauge cochain complex gives \(\ker d_1=\operatorname{im}d_0\) and \(\ker d_0\cong\mathbb Z_2\), hence \(H^1=0\), \(H^0=\mathbb Z_2\), and the claimed 2-type.

## Strict 2-groupoid checks

- 1-morphism identity, inverse, composition, associativity, and unit laws: PASS.
- 2-morphism identity, inverse, and vertical composition: PASS.
- Horizontal composition: 1,048,576 instances PASS.
- Interchange: 65,536 instances PASS.
- Coherence \(d_1d_0=0\): PASS.

## Lean verification

The file proofs/lean/HigherGaugeCohomology.lean compiles under Lean 4.12.0.

The formalized results include:
- \(d_1d_0=0\);
- exact 2-cochains have zero surface holonomy;
- surface holonomy is invariant under 1-form gauge transformations;
- \(\ker d_0\) consists exactly of constant 0-cochains;
- every closed 1-cochain is exact on the tetrahedral sphere;
- zero surface holonomy iff the 2-cochain is exact.

The separate axiom audit reports:
- no axioms for the three central cochain/holonomy identities;
- only standard Lean propext for the kernel/image and iff characterizations;
- no sorry, admit, unsafe declaration, or classical choice.

The exhaustive strict 2-groupoid composition/interchange checks are Python finite proofs by enumeration; they are not claimed to be Lean formalized.

## Interpretation and limits

**Established in this spike:** a finite 2-form gauge model has two global sectors, identical proper-local marginals, and a nontrivial 2-automorphism. The ordinary \(\pi_0\) classifies sectors but is not the full moduli 2-groupoid.

**Not established:** a new physical field, experimental detectability of the gauge-of-gauge automorphism, superiority of higher-categorical machine-learning representations, or a universal semantic theory. The example is a discrete mathematical model, not a physical experiment.

The result supports a narrower methodological claim: where the target domain has nontrivial higher moduli, a 0-truncated invariant or 1-truncated representation cannot be fully faithful. Whether the higher structure is protected for a particular task must be decided by its admissible probes.

## Next work

1. Extend the probe-density benchmark to calculate the restricted nerve on objects, 1-morphisms, and 2-morphisms.
2. Compare the finite mapping 2-type with the cohesive/differential refinement \(B^2U(1)_{\mathrm{conn}}\), keeping discrete topology separate from connection/curvature data.
3. Build a matched-capacity learning benchmark only after the exact probe hierarchy is specified.
4. Keep the general Causal-Hankel Full-Abstraction theorem conditional on density, representability, and realization hypotheses.


## Repository regression check

The full Semplex test suite was run on the authorized PC after the new finite experiment and Lean formalization were in place:

\`\`\`text
pytest -q
152 passed, 2 skipped in 269.88s (0:04:29)
\`\`\`

Exit code: 0. The suite is a repository regression check; the higher-gauge script and Lean module were also run/compiled independently as described above.
