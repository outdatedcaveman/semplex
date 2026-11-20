# Distinction Admissibility: a formal core

**Status:** initial formal core verified in Lean 4.12.0 CI; 9 finite Python tests pass. The universal DAP remains a research schema, not a theorem.
**Program:** Semplex / CERP, Spike 17.
**Synesism status:** interpretation proposal only; no canon change.

## 1. Scope

Can identity, substitution, contraction, quotienting, and context-sensitive equivalence be understood through one account of admissible structural transformations?

**Answer: partly.** A common preservation calculus can state when a transformation is safe relative to declared observations and operations. It does not, without further structure, derive every logic's identity type, substitution rule, or structural rules. Those are distinct mathematical structures; some are primitive in their respective foundations.

## 2. Basic semantic setting

Let X be a source domain, Y a target domain, T : X → Y a representation or abstraction map, and q : X → A a protected observable.

Define:

    Preserves(T,q) iff for all x,x' in X,
    T(x)=T(x') implies q(x)=q(x').

This says q is constant on every fiber of T. Equivalently, there is a unique function q-bar on im(T) such that q=q-bar∘T. The codomain must be restricted to im(T), or a default value supplied, to avoid extra assumptions.

For a family Q of protected observables, require this condition for every q in Q.

### Quotients

For an equivalence relation R on X, the quotient map is π : X → X/R. An observable descends iff R is contained in ker(q): x R y implies q(x)=q(y). This is task-/protocol-relative distinction loss, not a claim that discarded distinctions are irrelevant for every future purpose.

### Operations

For an n-ary operation f : X^n → X, an induced quotient operation is well-defined iff R is a congruence:

    (x_i R y_i for every i) implies
    f(x_1,...,x_n) R f(y_1,...,y_n).

Preserving current queries is weaker than preserving operations that may be applied later. A quotient can pass the first test and fail the second.

### Translations

For source operation f and target operation g, exact preservation may be expressed by the homomorphism law:

    T(f(x_1,...,x_n)) = g(Tx_1,...,Tx_n).

Compiler correctness may instead require simulation, trace relations, refinement, or approximate preservation. The relation must be selected from the semantics, not assumed universally.

## 3. Distinction Admissibility Principle (DAP)

**DAP is a schema, not a single theorem.** A transformation is admissible relative to a declared contract C=(Q,F,Rsrc,Rtgt,epsilon,Pi) only if it satisfies every preservation obligation in that contract.

- Q: protected observations/queries.
- F: protected operations and their arities.
- Rsrc and Rtgt: source and target semantic relations.
- epsilon: permitted quantitative distortion, if any.
- Pi: protocols/contexts under which obligations are evaluated.

For exact quotienting, DAP reduces to observable factorization plus congruence for every protected operation. For approximate or probabilistic transformations, replace equality by a declared metric/divergence bound and prove its composition law.

**Loss accounting:** distinctions outside the contract may be discarded, but the certificate must name the scope of the guarantee and the distinctions/operations not protected. It must not call the transformation globally lossless.

Without a declared task, interface, operation family, and resource model, there is no determinate answer to whether information loss is admissible.

## 4. Identity, substitution, contraction: what follows?

### Identity

- In classical first-order logic with equality, equality is a logical primitive (or explicitly axiomatized); substitutivity is part of its governing theory.
- In intensional dependent type theory, Id_A(x,y) is a primitive type former with reflexivity and an eliminator J/path induction. Transport along an identity proof is derived by that eliminator.
- In a setoid/observational foundation, one can define identity relative to a chosen equivalence and work with equivalence classes. This gives quotient identity, not automatically literal equality of original representatives.
- In category theory, objects remain objects with identity morphisms; many constructions are invariant up to isomorphism/equivalence. Invariance under isomorphism does not erase identity morphisms.

Thus identity can be weakened, relativized, or reconstructed at a chosen abstraction level, but DAP alone does not derive every identity notion. DAP itself uses equality in its metatheory, or must be formulated in an ambient logic with its own identity structure.

### Substitution

- First-order substitution of equals is licensed by equality's congruence across function and predicate symbols.
- Dependent substitution is reindexing/pullback of types and terms along context morphisms; in fibrational semantics it is structural data of the fibration/indexed category.
- A generic preservation map yields substitution only for protected operations/contexts for which congruence or naturality has been proved.

Substitution is not one rule: it is a family of transport/naturality principles indexed by syntax, type families, and contexts.

### Contraction

Contraction is not identity. It changes the multiplicity of assumption occurrences. Classical structural logic admits unrestricted contraction; linear logic does not admit it for arbitrary formulas and recovers controlled contraction for exponential resources such as !A. In categorical semantics, unrestricted duplication corresponds to diagonal/comonoid structure; a general symmetric monoidal category does not supply such a diagonal for every object.

A resource-sensitive account can characterize contraction by a duplicability structure, but cannot derive unrestricted contraction without assuming enough structure to duplicate resources.

## 5. Four comparison fragments

| Fragment | Identity | Substitution/transport | Contraction | DAP contribution |
|---|---|---|---|---|
| Classical FOL with equality | Primitive logical equality | Congruence/substitutivity | Unrestricted structural rule | States the protected language/interpretation preserved by quotient or renaming |
| Linear logic | Formula/proof equality is metatheoretic; resource occurrences matter | Substitution under linear context discipline | Not general; controlled by !/? | Makes duplicability an explicit resource permission |
| Dependent type theory / HoTT | Identity type with refl and J | Transport by path induction; substitution by context reindexing | Depends on the type theory; ordinary MLTT contexts are structural, linear dependent theories differ | Distinguishes path identity, definitional equality, equivalence, and transport |
| Context-/module-indexed model | Equivalence relative to a declared module/interface | Reindexing along context changes | Permission indexed by module/resource class | Formalizes local identity and cross-context compatibility; a full fibration requires more than an indexed relation |

## 6. Tarski's satisfaction slide

For a first-order formula phi, satisfaction M,s models phi depends only on the values assigned to its free variables FV(phi). Define s ~phi s' iff s and s' agree on FV(phi).

Satisfaction is constant on ~phi-classes and factors through the restricted assignment/profile. For a closed formula, FV(phi) is empty, so satisfaction is assignment-independent.

This is a clean instance of admissible distinction loss: assignment coordinates not free in phi may be forgotten **for evaluating phi**. They may not be forgotten for another formula that uses them. The quotient is formula-indexed, not absolute.

## 7. Names, assignments, and existential import

Keep variables, constant symbols, and fresh eigenparameters distinct. In standard first-order semantics, domains are nonempty and every constant symbol denotes an element. Thus ∃x(x=c) follows from equality reflexivity and existential introduction. The existential import inference ∀x φ(x) ⊢ ∃x φ(x) uses nonemptiness: choose an element, instantiate the universal, and introduce the existential. If empty domains are permitted, the universal is vacuously true while the existential is false. The written name does not create this inference by itself; it is the combined effect of signature, interpretation, nonempty-domain convention, and proof rules.

Tarski's free-variable theorem concerns assignments, not constant names: satisfaction depends only on the assignment restricted to FV(φ). A constant is interpreted by the structure; a variable is interpreted by the assignment. See research/NAMES_AND_EXISTENTIAL_IMPORT.md for the full analysis.

## 8. Minimal countermodels

### Query preservation does not imply operation preservation

Let X={0,1,2,3} and xRy iff x,y have the same parity. q(x)=x mod 2 descends. Addition modulo 4 is compatible with parity and descends. But g(0)=0 and g(x)=1 for x≠0 is not compatible: 0R2, while g(0)=0 is not related to g(2)=1. The quotient cannot define g unambiguously.

### Contraction fails for linear resources

In a simple resource semantics, n tokens satisfy demand m iff m≤n. Two A-tokens satisfy a two-token demand; one does not. General contraction from two A occurrences to one is unsound. An unrestricted/exponential resource is modeled separately as duplicable.

### Contextual identity is not global identity

Let states be pairs (a,b). Module M1 observes only a; M2 observes both coordinates. Then (0,0) and (0,1) are indistinguishable in M1 but distinguishable in M2. Local equivalence is real relative to the module, but cannot be silently promoted to global identity.

## 8. Synesism source reconciliation

The currently connected source material does **not** support reducing ordinary identity to module-relative observational equivalence.

The older *2. Definitions and Premises* and *5. Sema* chapters distinguish equal semonic value from structural identity: a zeroth-order semon and two first-order sema can have equal aggregate value while differing in order, mappings, and properties. *7. Systems* identifies the synod as the system's invariant/identity element and requires coherent transformations to preserve semonic value. *6. Syneces* treats syneces as relations/conversion factors and describes logic as semonic-preserving entailment.

The newer *Module* topic note describes modules as partial, contingent reality-slices generated through interactions involving signatures and fitness functions. It distinguishes internal semonic value from external/contextual fitness. These are not merely arbitrary observer opinions.

The connected workspace did not surface an explicit P8 page or the exact current P1 wording referenced in earlier conversations. Those earlier paraphrases are not treated as canonical until matched to their source. See:
- `research/SYNESISM_IDENTITY_MODULE_RECONCILIATION.md`
- `research/SYNESISM_MODULE_SEMANTICS_DESIGN.md`

### Formal consequence

Keep at least these notions separate:
1. semonic-value equivalence;
2. structural/configurational identity;
3. signature-based individuation;
4. system continuity anchored by a synod;
5. module-relative accessibility/fitness;
6. Markov-blanket/boundary identity (a proposed formal analogy, not yet defined).

The binary dyadic example is now formalized in `SynesismConservation.lean`: value is preserved under partition while configuration changes. It does not prove the general molarity theory. The resource fragment now records occurrence IDs, formula labels, linear/persistent modes, and provenance. It proves that merging two persistent occurrences of the same formula preserves support for every finite demand, while merging two distinct linear occurrences can destroy a two-use entailment. The merged provenance trail is explicitly concatenated; this remains a capacity semantics, not a linear-logic sequent calculus.

The generic fibration and finite gluing fragments are mathematical scaffolds only. They do not yet formalize Synesism modules as fitness-indexed partial reality-slices or prove that the module family satisfies descent.

## 9. Verification status

**CI passed:** https://github.com/outdatedcaveman/semplex/actions/runs/44693971714

- Lean 4.12.0 compiled and axiom-audited `Distinction.lean`, `SmallFibration.lean`, `ModuleDescent.lean`, and `SynesismConservation.lean`.
- The finite Python reference suite now passes **11/11** tests.
- Audited theorem dependencies are limited to `propext` and `Quot.sound`; no `sorryAx`, `Classical.choice`, or custom axiom dependency appears.
- The FOL syntax is a fragment (equality, unary predicates, falsity, implication, ∀ and ∃); the resource semantics is not full linear logic, the dependent-type fragment is not full HoTT, and the fibration/gluing examples are finite standard constructions.
- No Synesism canon or CSIR v0.1 schema was changed.

## 10. Remaining proof obligations

1. Define relative molarity and prove its algebraic laws beyond the binary dyadic example.
2. Formalize the synod invariant and the Principle of Coherence for nontrivial system transformations.
3. Define contextual fitness and modules as interaction-generated partial reality-slices.
4. Resolve the unitarity accounting law, especially how overlapping modules share/count reality-content.
5. Formalize the relation between modules and Markov blankets without identifying them by analogy alone.
6. Extend the four-system comparison beyond the now-verified FOL eigenvariable soundness fragment; formalize occurrence-sensitive linear contexts and compare actual structural rules.
7. Compare all candidate results with existing quotient algebra, linear logic, categorical logic, HoTT, fibrations, sheaf theory, and active inference before claiming novelty.

## 11. Literature anchors

- Girard (1987), *Linear Logic*; SEP, “Linear Logic”: https://plato.stanford.edu/entries/logic-linear/
- SEP, “Intuitionistic Type Theory”: https://plato.stanford.edu/entries/type-theory-intuitionistic/
- Jacobs (1999), *Categorical Logic and Type Theory*; Hermida (1993), *Fibrations, Logical Predicates and Indeterminates*.
- Tarski (1933/1956), “The Concept of Truth in Formalized Languages”; standard satisfaction lemmas concerning free variables.
- Semplex THEORY.md Theorem 10 already proves factorization through protocol profiles. Spike 17 generalizes the intended interface; it does not yet establish novelty.
