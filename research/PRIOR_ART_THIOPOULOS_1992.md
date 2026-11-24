# Prior-art note: Thiopoulos (1992), “Towards a Logic of Semiotic Systems”

**Source:** Constantin Thiopoulos, “Towards a Logic of Semiotic Systems,” *Mathématiques et sciences humaines* 117 (1992), 49–60. Numdam stable record: https://www.numdam.org/article/MSH_1992__117__49_0.pdf

## 1. Why this source matters

This is a direct antecedent to the broad structural-semantics thesis in Semplex/Synesism. It explicitly argues that meaning is not adequately modeled as a denotational map alone; meaning is an entity's position and interlinking in a network. It proposes a category-theoretic formalization of semiotic systems, weighted morphisms, context-generated subcategories, and structural invariants between interacting systems.

The source must be included in the canonical literature review before any claim about the novelty of relational meaning, categorical semiotics, weighted semantic networks, or contextual meaning.

## 2. Source-grounded overlap

| Thiopoulos construction | Source location | Relation to Semplex/Synesism |
|---|---|---|
| Meaning as structural interlinking/positional value rather than only denotation | Abstract; §1.2, pp. 49–52 | Direct conceptual antecedent to meaning as relational role |
| Semiotic systems as weighted networks of terms | §2.2, Definition 2.18, p. 56 | Direct antecedent to weighted semantic networks |
| Semiotic category with objects, morphisms and multiplicative morphism confidence | §2.2, Definitions 2.19–2.20, p. 56 | Direct formal antecedent to weighted categorical representations |
| Thresholded incoming arrows as an intensional interpretation | §2.2, Definition 2.21, p. 56 | Direct antecedent to probe/profile semantics, but see formal audit below |
| Context/situation as a generated full subcategory | §2.2, Definition 2.24, pp. 57–58 | Direct antecedent to context-indexed semantic profiles |
| Situational category of possible interactions | §2.2, Definition 2.25, p. 58 | Related to context categories and relational semantics |
| Hypercategory of semiotic categories over a common alphabet | §2.2, Definition 2.26, p. 58 | Related to a category of representational systems and translations |
| Communication category and invariant morphisms between situational categories | §2.2, Definition 2.27, p. 58 | Direct antecedent to cross-system structural invariants |
| Connectionist interpretation and information-retrieval semantics | §§3.1–3.2, p. 59 | Direct application to network-based meaning and retrieval |

## 3. Philosophical differences

The article explicitly grounds its account in phenomenology and autopoietic cybernetics, citing Heidegger, Merleau-Ponty, Maturana and Varela. It describes reality as an intersubjectively constituted domain emerging through structural coupling.

That is not automatically the same as the intended Semplex/Synesism programme:
- Semplex seeks a physically grounded, operationally testable semantics.
- It should not assume the article's phenomenological/autopoietic ontology.
- The intended naturalized thesis treats relational meaning as potentially objective and constrained by physical counterfactual structure, not merely as a cultural/subjective construct.
- Category-theoretic overlap does not entail metaphysical equivalence.

The correct relation is: major conceptual/formal antecedent, with a distinct philosophical grounding.

## 4. Formal audit: multiplicative threshold sets need not be sieves

Thiopoulos defines:
\[
\operatorname{conf}(f\circ g)=\operatorname{conf}(f)\operatorname{conf}(g)
\]
and proposes:
\[
R_B(X)=\{f:Y\to X\mid\operatorname{conf}(f)\ge B\}
\]
as a sieve/topological interpretation (Definitions 2.20–2.21, Theorem 2.1).

A sieve on \(X\) must be closed under precomposition:
\[
f:Y\to X\in R,\quad u:Z\to Y
\implies f\circ u:Z\to X\in R.
\]

Counterexample:
\[
Q\xrightarrow{u}P\xrightarrow{g}X,\qquad h=g\circ u,
\]
with
\[
\operatorname{conf}(u)=0.5,\quad
\operatorname{conf}(g)=0.9,\quad
\operatorname{conf}(h)=0.45.
\]
At \(B=0.8\), \(g\in R_B(X)\) but \(h\notin R_B(X)\). Hence \(R_B(X)\) is not a sieve. With identity weights 1, \(id_X\) is also in the threshold set; a sieve containing \(id_X\) must be maximal, which this threshold set is not.

The paper's displayed proof of Theorem 2.1 appears to use the reverse implication (a composite above threshold implies a factor is above threshold) rather than sieve closure (a factor above threshold implies every precomposition remains above threshold). The proof therefore does not establish the sieve axiom under nontrivial multiplicative weights in \((0,1]\).

There is also a type/notation ambiguity in Definition 2.17: a Grothendieck topology assigns a collection of covering sieves to each object, while Definition 2.21 appears to return one threshold sieve. This may be an omission or notational compression. The sieve-closure counterexample is independent of that ambiguity.

This is a narrow mathematical critique of the threshold-sieve claim, not a rejection of the broader semiotic formalism.

## 5. Correct closure condition

For fixed \(B\), threshold arrows form a sieve iff
\[
\forall f,u,\quad
\operatorname{conf}(f)\ge B
\implies
\operatorname{conf}(f\circ u)\ge B.
\]

Under multiplicativity:
\[
\operatorname{conf}(f)\ge B
\implies
\operatorname{conf}(f)\operatorname{conf}(u)\ge B.
\]

If this must hold for every \(B>0\), then choosing \(B=\operatorname{conf}(f)>0\) forces \(\operatorname{conf}(u)\ge1\) for every admissible precomposition. Therefore nontrivial normalized weights in \((0,1]\) do not generally induce sieves by thresholding.

Possible repairs, not yet established as novel:
1. Restrict to an admissible-refinement subcategory where the closure condition holds.
2. Use a different composition law and prove its threshold cuts are sieves.
3. Separate raw executable experiments from the sieve generated by them, attaching a closure-cost certificate.
4. Define resource-graded coverages whose pullback/refinement laws explicitly account for additional cost.

## 6. Semplex research consequences

The article rules out broad novelty claims for:
- relational/structural meaning as network position;
- weighted semiotic categories;
- contextual situation subcategories;
- cross-system invariants of semiotic structures.

The more precise open target is to derive a physically grounded, resource-indexed semantics whose admissible probe structure is compositionally coherent and whose reconstruction guarantees are explicit. This should be compared against categorical realization theory, causal active experimental design, presheaf/sieve semantics, and resource-sensitive logic.

## 7. Reproducible artifacts

- experiments/SPIKE_20_REPORT.md
- experiments/semiotic_threshold_sieve_counterexample.py
- experiments/costed_executable_sieves.py
- tests/test_semiotic_threshold_sieve.py
- tests/test_costed_executable_sieves.py
- artifacts/semiotic-threshold-sieve-counterexample-20261121.json
