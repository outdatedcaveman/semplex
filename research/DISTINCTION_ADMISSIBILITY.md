# Distinction Admissibility: a formal core

**Status:** formal specification; finite instance tested; Lean source added, compiler verification pending.
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

## 7. Minimal countermodels

### Query preservation does not imply operation preservation

Let X={0,1,2,3} and xRy iff x,y have the same parity. q(x)=x mod 2 descends. Addition modulo 4 is compatible with parity and descends. But g(0)=0 and g(x)=1 for x≠0 is not compatible: 0R2, while g(0)=0 is not related to g(2)=1. The quotient cannot define g unambiguously.

### Contraction fails for linear resources

In a simple resource semantics, n tokens satisfy demand m iff m≤n. Two A-tokens satisfy a two-token demand; one does not. General contraction from two A occurrences to one is unsound. An unrestricted/exponential resource is modeled separately as duplicable.

### Contextual identity is not global identity

Let states be pairs (a,b). Module M1 observes only a; M2 observes both coordinates. Then (0,0) and (0,1) are indistinguishable in M1 but distinguishable in M2. Local equivalence is real relative to the module, but cannot be silently promoted to global identity.

## 8. Synesism: identity of ordinary beings in practice

Canon P1 distinguishes **true identity** from **phenomenological identity**. Its lexicon says only Semes possesses full true identity; ordinary beings are quasiobjects with modular, transient, approximate phenomenological identity. P8 defines modules as real partial reality-slices, not illusions.

A candidate formal reading:

1. A module M supplies a protected interface of observations/relations Q_M.
2. Two presentations or states of an ordinary quasiobject are M-equivalent when Q_M-observables agree within a declared tolerance and protected transitions are respected.
3. Persistence through time is a coherent family of such local equivalences along admissible transitions.
4. Cross-module identity requires compatibility on overlaps and a specified gluing/descent condition.

This is **not yet the canonical meaning of P8**. The finite model in Spike 17 is an operational observer/module abstraction. Synesism's modules are ontological/epistemic reality-slices; the bridge remains a proof obligation.

Nor does P0/P1 formally prove that Semes is the only entity with metaphysically real identity. That is a canon commitment. Distinguish: (i) identity primitive in a formal language, (ii) equality in a model, (iii) structural/observational equivalence, (iv) persistence of a quasiobject, and (v) P1's metaphysical true identity.

**Canon ambiguity to resolve:** P1's headline says identical signature and semonic value imply identity, while its clarification says ordinary beings lack true self-identity but possess approximate phenomenological identity. Does the antecedent concern identity between loci, identity of an entity across descriptions, or identity simpliciter? No implementation should silently choose.

## 9. Verification status

1. **Lean source added; compiler check pending:** quotient factorization criterion in kernel-setoid form.
2. **Lean source added; compiler check pending:** unary operation descends to quotient under congruence.
3. **Lean source added; compiler check pending:** equality substitution by identity elimination.
4. **Lean source added; compiler check pending:** module-indistinguishability is an equivalence and refines with added observations.
5. **Finite Python tests pass:** Tarski free-variable example, congruence counterexample, resource contraction counterexample, context-dependent identity.
6. **Known mathematics:** quotient factorization/congruence, linear-logic exponential control of contraction, identity-type elimination, fibrational substitution. No priority claim.
7. **Open:** full fibrational model of Synesism modules, bridge to P0/P1, and any genuinely novel theorem beyond existing literature.

## 10. Literature anchors

- Girard (1987), *Linear Logic*; SEP, “Linear Logic”: https://plato.stanford.edu/entries/logic-linear/
- SEP, “Intuitionistic Type Theory”: https://plato.stanford.edu/entries/type-theory-intuitionistic/
- Jacobs (1999), *Categorical Logic and Type Theory*; Hermida (1993), *Fibrations, Logical Predicates and Indeterminates*.
- Tarski (1933/1956), “The Concept of Truth in Formalized Languages”; standard satisfaction lemmas concerning free variables.
- Semplex THEORY.md Theorem 10 already proves factorization through protocol profiles. Spike 17 generalizes the intended interface; it does not yet establish novelty.
