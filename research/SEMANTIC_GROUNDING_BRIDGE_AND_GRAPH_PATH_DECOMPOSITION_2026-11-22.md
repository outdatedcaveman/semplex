# Semantic Grounding Bridge and Graph Path Decomposition

**Date:** 2026-11-22  
**Status:** Lean-formalized interfaces and conditional theorems; not a completed theory of truth or a general graph theorem from connectivity alone.

## 1. Semantic grounding bridge

Added `proofs/lean/SemanticGroundingBridge.lean`, importing the typed response core.

### 1.1 Probe restriction and underdetermination

A `ProbeRestriction P` consists of a probe type Q and an embedding Q -> P. Agreement on all P-probes implies agreement on any restricted Q-family. Conversely, if a restricted family separates all target states, then the full family separates them.

The theorem `underdetermination_of_nonseparation` makes the negative case explicit: if the declared probes do not separate states, there exist distinct target states with identical complete response profiles. The theory therefore cannot infer unique target identity from a non-separating observation regime.

This is a model-relative result. It does not say which probes are physically available or normatively appropriate.

### 1.2 Truth preservation and reflection

`ClaimInterpretation` separates source satisfaction, target satisfaction, and a claim translation. `TruthPreserving` and `TruthReflecting` are distinct. `TruthAdequate` is equivalent to their conjunction.

This captures an important distinction:
- preservation/soundness: source truth is not translated into target falsity;
- reflection: target truth of the translation does not overstate what the source claim says;
- adequacy: both directions hold.

The construction is relative to a shared target-state domain. It does not solve reference to an external world, nor does it identify truth with derivability.

### 1.3 Counterfactual robustness from dynamics

`GroundedRealization` packages:
- exact probe-response adequacy of an encoder/decoder;
- a target transition system and an implementation update;
- equality of the two state encoders;
- one-step update commutation.

The theorem `finite_intervention_adequacy` derives response adequacy after every finite action/intervention sequence from these premises. Thus finite-horizon counterfactual robustness is a theorem of the interface, not an extra axiom.

The word *grounded* here is deliberately qualified: this is grounding relative to a declared target dynamics and probe family. Empirical identification of the target, causal validity of the interventions, organizational autonomy, and open-world robustness remain external obligations.

### 1.4 Passive observation versus intervention: finite witness

The module includes a two-state Boolean example:
- passive probes return a constant and therefore fail to distinguish false from true;
- an intervention-sensitive probe exposes the state and separates them.

This is a deliberately minimal formal witness for the logic of intervention-sensitive identification, not an empirical causal model. It demonstrates that increasing the probe family can remove an underdetermination that passive observation cannot.

### 1.5 Evidence and satisfaction

The bridge adds `StateIndexedEvidence`, whose evidence type depends on both claim and target state. Soundness and completeness are stated separately. This is more appropriate for state-dependent claims than a single evidence type per claim that would need to establish satisfaction across every possible state.

The older `EvidenceSystem` in `SemanticResponseCore` remains a coarse interface; use the state-indexed version when formalizing empirical claims with state-relative satisfaction.

## 2. Graph-gauge path decomposition

Added `proofs/lean/GraphGaugePathDecomposition.lean`.

### 2.1 Concatenation law

The module defines concatenation of edge-indexed walks and proves:
`transport(p ++ q) = transport(q) * transport(p)`,
matching the project's convention that later traversed edges multiply on the left.

It also proves that concatenating tree-supported paths preserves tree support.

### 2.2 Deriving the tree transport recursion

The earlier `RootedSpanningTree` certificate stored the transport recursion as an explicit field. The new `RootedTreePaths` certificate requires only:
- a root and one root-to-vertex path for every vertex;
- normalization at the root;
- tree support of those paths;
- uniqueness among tree-supported root paths.

For any selected tree edge e:u->v, the concatenation of the certified root-to-u path with e is itself tree-supported. By uniqueness it must equal the certified root-to-v path. The transport concatenation theorem then derives:
`P(v) = A(e) * P(u)`.

The theorem `tree_transport_recursion` proves this derivation. The constructor `toRootedSpanningTree` converts the weaker path certificate into the earlier reconstruction certificate, supplying its recursion field from the theorem rather than assuming it.

### 2.3 Remaining graph gap

This does **not** yet construct `RootedTreePaths` from a finite connected acyclic graph. The existence of root-to-vertex paths, tree support, and uniqueness still needs a graph-theoretic construction from explicit connectedness/acyclicity assumptions. Reverse-edge consistency and identification of chord coordinates with `Hom(pi_1,G)` also remain open. The full action-groupoid equivalence is not yet packaged as a Lean equivalence.

## 3. Verification and interpretation

Focused Lean builds passed for `SemanticGroundingBridge` and `GraphGaugePathDecomposition`. A fresh full `lake build` and repository diff checks should be rerun after the current documentation/registration updates.

No commits, pushes, or merges were made. No direct Gemini completion is claimed.


## 4. Final verification addendum

- Fresh full `lake build`: passed after both new modules and their lakefile registrations.
- `git diff --check`: passed.
- Temporary axiom audit file was removed after execution.
- Axiom audit: the restriction, truth-adequacy, finite-intervention, state-indexed evidence, passive-witness, and tree-path uniqueness/decomposition results have no axiom dependencies. The classical underdetermination theorem uses standard `Classical.choice` (and Lean's standard `propext`/`Quot.sound`); the intervention-separation and transport-recursion proofs show only standard `propext`/`Quot.sound` dependencies. No custom axioms or `sorryAx` were reported.
