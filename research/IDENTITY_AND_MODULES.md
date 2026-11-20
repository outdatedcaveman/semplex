# Phenomenological identity and Synesism modules: formalization note

**Status:** research interpretation, not canon amendment.

## What P1 currently says

The canonical text makes two claims that must be kept distinct:

- True identity is oneness/indiscernibility and is fully possessed only by Semes.
- Phenomenological identity is the modular, transient, fluid, approximate identity of ordinary beings, which are described as quasiobjects.

P8 says modules are real partial, perspectival reality-slices. A module is not merely an observer's arbitrary opinion; it is a fragment of manifest reality with a domain of validity. Illusion is the misapplication of a module outside that domain.

Therefore the answer to “is Semes' identity the only real one?” depends on “real.” Under the canon, it is the only full/true identity. It does not follow that ordinary identity is unreal or arbitrary. Ordinary beings have real but derivative, approximate and module-indexed identity.

## Candidate operational account

For each module M, specify:

- a domain D_M of states/presentations it covers;
- protected observables Q_M;
- protected relations and transitions F_M;
- an admissible distortion/tolerance ε_M;
- a validity boundary and evidence/provenance.

Define x ≈_M y iff all protected observables agree within ε_M and all protected transitions respect the relation. Exact equivalence is the ε=0 case. If the relation is not transitive under a proposed tolerance, do not call it an equivalence relation; use a metric or pseudometric and define a threshold relation separately.

Persistence of a quasiobject across time is not bare equality of snapshots. It is a path/chain of admissible transitions whose composed relation preserves the selected invariants. Composition requires a theorem: tolerances may accumulate, relations may fail to compose, and a module change may expose previously hidden distinctions.

## Cross-module identity

If M and N overlap, require their identity claims to agree on the overlap or provide an explicit translation/refinement between their interfaces. A global identity claim should be constructed by descent/gluing only when the overlap compatibility conditions hold. Local equivalence in M alone never implies global identity.

This is where fibrations or indexed categories may be useful:
- base objects: modules/contexts and their refinements;
- fibers: entities, states, evidence, and admissible transformations available in each module;
- reindexing: restriction/change of module along a context morphism;
- cartesian lifting: transport of a local object/claim into a refined context;
- descent: compatible local descriptions glue to a global description.

The current Spike 17 Python model implements only the observation-indexed equivalence part. It is not yet a fibration.

## The P1 ambiguity

P1's headline says identical signature and semonic value imply identity. Its clarification says only Semes has full true identity and ordinary beings have phenomenological identity. Before formalization, determine whether the headline means:
1. equality of loci/positions in the worldtree;
2. identity of one being across multiple descriptions;
3. identity simpliciter between distinct presentations;
4. a criterion for true identity, or only for phenomenological identity.

These are not equivalent. The formalization must not silently choose one.

## Semes and formal equality

The claim that Semes alone has full true identity is a metaphysical commitment of Synesism, not a theorem of ordinary first-order logic, HoTT, or category theory. HoTT's univalence identifies equivalent types with equal types (under the univalence axiom); it does not establish that one metaphysical entity is the only genuinely self-identical being.

The formal program should treat the Semes claim as an interpretation to be made precise and tested for consistency with the mathematical structures, not as something already proven by univalence.

## Immediate research tests

1. Define module refinement and reindexing; prove observational indistinguishability becomes finer as protected observations increase.
2. Construct an overlap example where two modules agree locally but fail to glue globally.
3. Specify a transition semantics for ordinary-object persistence and test composition of approximate identity.
4. Compare the result with setoids, contextual equivalence, bisimulation, sheaves/descent, and fibrations.
5. Only then propose a precise formal reading of P1/P8 for reconciliation.
