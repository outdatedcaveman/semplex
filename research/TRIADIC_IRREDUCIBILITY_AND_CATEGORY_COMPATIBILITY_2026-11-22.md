# Triadic irreducibility and category-theoretic compatibility
Date: 2026-11-22

## 1. Adversarial issue

Peirce's genuine triadic relation is not a mere conjunction of three dyadic relations. A common formal mistake is to model a sign triad as three independent arrows (sign→object, sign→interpretant, object→interpretant). That may destroy precisely the Thirdness/mediation one is trying to represent.

Mogens Kilstrup (2015), “Naturalizing semiotics: The triadic sign of Charles Sanders Peirce as a systems property,” *Progress in Biophysics and Molecular Biology* 119(3), 563–575, DOI 10.1016/j.pbiomolbio.2015.08.013, explicitly discusses a Ψ(O,R,I) linkage-space model and a section titled “... its incompatibility with category theory.” His argument, as available in the full-text search extract, is that composing two sign mappings does not have an intrinsic semiotic meaning; the change of an element's role (e.g. representamen in one sign, object in another) requires a new sign-establishment event. He allows that category theory might help construct a semiotic category if its mappings obey appropriate associativity/commutativity constraints, but does not provide a general categorical solution.

This is not a proof that category theory cannot model semiosis. It is a specific warning against identifying the triadic sign relation itself with ordinary composable arrows.

## 2. A formal irreducibility witness

Added `proofs/lean/IrreducibleTriadicRelations.lean`.

Let S=O=I=Bool and define the even-parity relation:
[
R(s,o,i)iff (s=o)leftrightarrow(i=mathrm{false}).
]
It contains exactly the four triples of even parity: 000, 011, 101, 110.

Every assignment to any two coordinates extends to a triple satisfying R. Suppose R factored as
[
R(s,o,i)iff R_{SO}(s,o)land R_{SI}(s,i)land R_{OI}(o,i).
]
Because every pair extends to a valid triple, each binary factor would have to hold for every pair. Their conjunction would therefore hold for all eight triples. But R rejects 001, contradiction.

Lean proves:
- all three pairwise extension lemmas;
- `evenParity_not_pairwise_factorable`.

The module is included in Lake and the full `lake build` passed. The axiom audit reports only standard `propext` for the parity/equivalence propositions; no custom axioms or `sorryAx`.

This is a rigorous finite witness that genuine ternary relations can carry information irreducible to pairwise constraints. It does not prove that every Peircean sign relation has this property, nor that this parity relation is a model of semiosis. It establishes the formal distinction needed to avoid silently reducing Thirdness to dyadic links.

## 3. What this means for our categorical architecture

The category-theoretic layer should be placed at the level of **whole structured semantic systems and their structure-preserving transformations**, not at the level of pretending that each sign triad is a three-arrow category.

The Lean `TriadicGroundedSemiosis` module is compatible with this caution: it treats semiosis as a ternary relation on signs, objects and interpretants, and defines morphisms between entire models that preserve/reflect that relation. It does not factor the relation into pairwise arrows.

But two major additions remain:
1. **Role-change/establishment:** if an interpretant becomes a sign or an object enters a new representational role, the transition may require a new establishment event and new scaffold state, not merely reuse of an existing arrow.
2. **Two-phase semiosis:** model sign establishment (learning/coding, creating a persistent linkage/memory) separately from sign interpretation (activating that established linkage when a novel representamen is encountered).

A suitable mathematical object may therefore be a relational/hypergraph-like triadic structure internal to a category of semiotic scaffolds, equipped with a stateful transition system. The category's morphisms preserve whole scaffolds; coalgebraic transitions model temporal evolution; the triadic relation remains primitive. The category must not impose a composition law on sign-level transitions unless empirical/semiotic laws justify it.

## 4. Connection to Alrøe (2025)

Hugo F. Alrøe, “The six types of sign action,” *Semiotica* 2025(266), 1–30, DOI 10.1515/sem-2024-0112, further separates representation from mediation and proposes six mediation directions. This reinforces the need to model:
- representation as a triadic relation;
- mediation as a distinct source–mediator–outcome process;
- immediate and dynamical correlates separately;
- temporal establishment/interpretation and the interpreter/scaffold.

Kilstrup and Alrøe are not simply interchangeable accounts. Their differences are an adversarial comparison target, not a consensus theory.

## 5. Sources

- Kilstrup (2015), PubMed: https://pubmed.ncbi.nlm.nih.gov/26276466/
- Kilstrup (2015), DTU author record: https://orbit.dtu.dk/en/publications/naturalizing-semiotics-the-triadic-sign-of-charles-sanders-peirce/
- Kilstrup (2015), publisher page: https://www.sciencedirect.com/science/article/pii/S0079610715001261
- Alrøe (2025), DOI: https://doi.org/10.1515/sem-2024-0112
