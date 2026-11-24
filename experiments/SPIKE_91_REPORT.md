> Renumbered from canonical distinction-calculus `SPIKE_21_REPORT` to `SPIKE_91_REPORT` to avoid filename collision with existing `SPIKE_18..87` on base `7be5346`.

# Spike 21 — Resource-relative probe presheaves

**Status:** PASS — exact finite model and 7 tests; general Lean proof drafted but not compiled.  
**Date:** 2026-11-21  
**Plan:** experiments/SPIKE_21_PLAN.md  
**Code:** experiments/resource_relative_probe_sieves.py  
**Tests:** tests/test_resource_relative_probe_sieves.py  
**Artifact:** artifacts/resource-relative-probe-sieves-20261121.json

## 1. Result

A budget-bounded family of probes need not be a sieve in the full physical category. But it can be a valid presheaf when indexed only by a wide subcategory of zero-cost refinements.

This is the cleanest repair so far to the conflict between resource budgets and compositional probe semantics.

Let \(\mathcal C\) be a category and \(\mathcal F\subseteq\mathcal C\) a wide subcategory of free/zero-cost refinements. Let arrow cost \(c\) be subadditive under composition:
\[
c(g\circ f)\le c(g)+c(f),
\]
with identities and all arrows in \(\mathcal F\) having cost zero.

For each target \(X\) and budget \(B\), define:
\[
M_B(X)(P)=\{f:P\to X\mid c(f)\le B\},\quad P\in\mathcal F.
\]

If \(u:Q\to P\) is free, then:
\[
c(f\circ u)\le c(f)+c(u)=c(f)\le B.
\]
Therefore precomposition restricts to \(M_B(X)(P)\to M_B(X)(Q)\). This makes \(M_B(X)\) a presheaf on \(\mathcal F\), i.e. a sieve relative to free refinements.

For a possibly costly target transformation \(h:X\to Y\), postcomposition shifts the budget:
\[
M_B(X)\longrightarrow M_{c(h)+B}(Y),\quad f\mapsto h\circ f.
\]
This is natural under free precomposition by associativity.

The same argument works for vector-valued costs in an ordered commutative monoid.

## 2. Exact finite model

The tested category has objects \(R,Q,P,X,Y\). Its key arrows are:
\[
Q\xrightarrow{u}P\xrightarrow{g}X,\qquad
h=g\circ u,
\]
and
\[
R\xrightarrow{v}Q,\quad
w=u\circ v,\quad
k=h\circ v=g\circ w.
\]

Costs:
- \(u\): 0 (free);
- \(g\): 1;
- \(h\): 1;
- \(v\): 2 (paid);
- \(w\): 2;
- \(k\): 3;
- \(t:X\to Y\): 2;
- \(tg,th,tk\): 3,3,5.

At budget 1, affordable arrows into X are:
\[
M_1(X)=\{id_X,g,h\}.
\]
This is closed under the free refinement \(u\): \(g\mapsto h\). It is not closed under paid \(v\): \(h\mapsto k\), whose cost is 3.

At budget 3, \(k\) becomes affordable and the family is closed under all incoming arrows in this finite category.

Postcomposition by \(t\), of cost 2, shifts the budget from 1 to 3:
\[
id_X\mapsto t,\quad g\mapsto tg,\quad h\mapsto th.
\]
The map commutes with the free refinement \(u\).

## 3. Verification

\`\`\`text
pytest -q tests/test_restricted_yoneda.py tests/test_costed_executable_sieves.py tests/test_semiotic_threshold_sieve.py tests/test_resource_relative_probe_sieves.py
23 passed in 0.29s
exit code 0
\`\`\`

The finite model exhaustively checks:
- identities and associativity;
- cost subadditivity for every composable arrow pair;
- closure of the zero-cost arrows under composition;
- relative sieve closure for budgets 0, 1, 2, 3, 5;
- failure of full-category sieve closure at budgets 1 and 2;
- grade-shift postcomposition and naturality under free refinements.

The general Lean proof has been drafted in proofs/lean/ResourceRelativeProbes.lean but has **not yet been compiled**. The PC currently has approximately 1.4 GB free RAM, below the previously established safe threshold for Lean/Agda builds; no build was started. No WSL/Agda process was terminated.

## 4. Prior art: the machinery already exists

Marsden & Zwart, “Quantitative Foundations for Resource Theories,” CSL 2018, DOI 10.4230/LIPIcs.CSL.2018.32, is a direct mathematical antecedent:
- §2: quantale-enriched categories with Boolean, interval, Lawvere-cost, and multiplicative-probability quantales;
- §3: quantale-valued presheaves and profunctors, with composition laws enforcing compatibility under free conversions;
- §3's separation-of-concerns remark: the domain/codomain model freely available resources, while profunctor values model additional costly conversions;
- §6: bimodules are closed under precomposition and postcomposition by freely available multi-conversions;
- §7: canonical reflexive-transitive closure of conversions.

Thus neither resource-enriched categories, quantale-valued profunctors, nor the free/costly distinction is novel. The present finite model instantiates those ideas for probe protocols and makes the budget-preserving presheaf condition explicit.

## 5. Candidate Semplex bridge, still unproved

The relevant next object is likely not a bare restricted Yoneda embedding but a resource-enriched causal response profunctor:
\[
\mathsf R:\mathcal F_{\mathrm{probe}}^{op}\times\mathcal C_{\mathrm{system}}\to\mathcal Q,
\]
or a higher-valued refinement when response data include spaces/groupoids.

The open theorem would connect:
1. physical executability of probes;
2. free-refinement closure;
3. quantale/vector-valued cost and probability;
4. full abstraction of the response semantics on a protected system class;
5. higher moduli preservation and explicit truncation distortion.

The current spike proves only the elementary finite presheaf/grade-shift behavior. It does not establish this full theorem or novelty.
