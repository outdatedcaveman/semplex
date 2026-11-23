# Preliminary prior-art review: resource-sensitive syntax and admissible abstraction

**Date:** 2026-11-21  
**Scope:** Synesism C-20 M263/M264, P0LinearTyping/P0FullTyping, M413, and Semplex P091 / Distinction Admissibility  
**Status:** Preliminary, source-backed triage; not an exhaustive systematic literature review.

## Executive verdict

The current formal ingredients are substantially established mathematics. In particular, quantitative usage accounting in dependent type theory, Agda formalizations of linear metatheory using vectors and semirings, matrix-based resource-aware renaming/substitution environments, de Bruijn substitution calculi, and the universal-property criterion for quotient descent all have close prior art. Wood–Atkey 2022 is a direct predecessor for the proposed matrix-transport semantics, and Wood's 2024 thesis broadens that framework to additional substructural modalities.

Accordingly, neither the C-20 usage calculus nor the elementary quotient/congruence lemmas should be presented as a new logic or foundational result. The potentially distinctive contribution is narrower: a typed, inspectable interface that carries occurrence identity and provenance across representation-changing transformations while checking declared observations and operations, and that can be composed across heterogeneous modules. This must be shown to add guarantees beyond Wood–Atkey's usage-aware environments, QTT, standard representation independence, and abstract interpretation. It remains a research hypothesis, not an established novelty claim.

## 1. Direct prior art

### 1.1 Quantitative Type Theory and type-level use

Atkey's *Syntax and Semantics of Quantitative Type Theory* (LICS 2018, DOI: 10.1145/3209108.3209189) explicitly addresses the conflict between computational use and type formation in dependent type theory. It assigns semiring-valued usage annotations to variables; zero usage permits a variable to remain available for type formation while being erased from runtime computation. Crucially for M265, QTT's dependent function type carries an argument grade π recording how many times the argument may be used. Its application semantics scales the argument context by π and combines it with the function context (Γ₁ + πΓ₂). The dependent tensor product carries the same kind of grade. QTT distinguishes erased and resourced term fragments with σ ∈ {0,1}; this restriction is essential to the admissibility of substitution. Lemma 2.5 gives the exact substitution side conditions and combines the substituted term's context multiplied by the variable grade with the remaining context. Atkey gives quantitative categorical semantics via Quantitative Categories with Families (QCwFs), and realisability models using resource-sensitive combinatory algebras. The paper reformulates McBride's earlier system and repairs a substitution-admissibility problem.

This is directly relevant to the M263/M265 distinction between occurrences in the subject and occurrences in the type. Synesism's stored count and tDep rule are closely aligned with the QTT principle that type-level dependence need not consume computational resources. This correspondence should be treated as prior art, not as an independent discovery. A remaining question is whether C-20 tracks some additional kind of type-level occurrence or identity that QTT does not; the current Usage vector alone does not establish that.

Reference: Robert Atkey, “The Syntax and Semantics of Quantitative Type Theory,” LICS 2018. https://doi.org/10.1145/3209108.3209189

### 1.2 Linear metatheory with vectors, semirings, and Agda

Wood and Atkey's *A Linear Algebra Approach to Linear Metatheory* (EPTCS 353, 2021, pp. 195–212, DOI: 10.4204/EPTCS.353.10) is especially close to M263/M413. It mechanizes a linear typed lambda calculus in Agda, represents context usages as vectors and usage-preserving maps as matrices, and proves admissibility of renaming, subusaging, and substitution using a generalization of McBride's kits-and-traversals method. It explicitly discusses the difficulty of preserving usage under substitution and the use of semirings for quantitative/coeffect calculi.

Consequences:
- Context-indexed usage vectors are established.
- Agda formalization of usage-sensitive renaming and substitution is established.
- Usage preservation under binder-respecting traversals is established in a closely related framework.
- M263/M413 may still contribute a particular syntax, accounting theorem, or integration with Synesism's other modules, but the general method and mathematical ingredients are not novel.

Reference: James Wood and Robert Atkey, “A Linear Algebra Approach to Linear Metatheory,” EPTCS 353 (2021), DOI: https://doi.org/10.4204/EPTCS.353.10

### 1.3 Usage-aware environments, matrix actions, and duplicability

Wood and Atkey's *A Framework for Substructural Type Systems* (ESOP 2022, LNCS 13240, pp. 376–402, DOI: 10.1007/978-3-030-99336-8_14) is the most direct comparator for the proposed matrix-transport direction. It defines a resource-aware environment between annotated contexts using a linear map between usage modules. The paper explicitly explains that, for row-vector usage profiles, this map is represented by a matrix and acts by right multiplication. It instantiates the environment construction both for renaming (variables map to variables) and substitution (variables map to terms), and gives an example matrix in which repeated columns encode contraction while zero columns encode weakening. It further states that renamings form a category and that their identity/composition follow from identity/composition of the associated linear maps.

This is not merely adjacent inspiration: it already contains the central mathematical structure of the candidate incidence-matrix account. Its Agda artifact makes the relationship concrete:
- an environment carries a relational linear map Ψ between usage modules and a lookup operation; its resource side condition is P ≤ QΨ;
- the paper explains that, for row-vector profiles, Ψ is represented by a matrix acting by right multiplication; the example matrix explicitly exhibits contraction (repeated columns), weakening (zero columns), and exchange (permuted rows);
- the categorical development defines identity and composition of environments and proves that renamings form a category;
- the generic traversal derives simultaneous renaming and substitution as instances of the same environment machinery;
- a typed duplicability combinator □ is explored, with the paper noting that it requires functional rather than merely relational linear maps.

Therefore:
- the equation “usage transforms by a matrix under renaming/substitution” is not a novelty claim;
- compositionality of these linear maps and resource-aware environments is already established;
- binder-aware simultaneous renaming/substitution and resource-correct environments are already addressed;
- weakening, contraction, exchange, and a typed duplicability construction already have a direct mechanized treatment.

There is, however, a boundary worth recording. The 2022 framework describes simply typed syntaxes: its type universe is a fixed Ty : Set and contexts assign those types to variables. It does not automatically subsume a genuinely dependent syntax in which types vary with term contexts. Synesism C-20's Π fragment is dependent, although its current typing development is incomplete and P091 itself is a finite all-linear adapter. This difference motivates a precise comparison, but it does not by itself establish novelty for the current adapter.

James Wood's 2024 PhD thesis, *A Framework for Semiring-Annotated Type Systems* (DOI: 10.48730/pa0y-ct71), extends this research programme to a broader family of restricted-usage calculi, including an S4-style modality and Linear Logic, with generic simultaneous renaming and substitution mechanized in Agda. It should be consulted before designing any new resource calculus or exponential interface.

References:
- James Wood and Robert Atkey, “A Framework for Substructural Type Systems,” ESOP 2022, DOI: https://doi.org/10.1007/978-3-030-99336-8_14.
- James Wood, *A Framework for Semiring-Annotated Type Systems*, PhD thesis, University of Strathclyde, 2024, DOI: https://doi.org/10.48730/pa0y-ct71.

### 1.4 Explicit substitutions and de Bruijn fusion

Abadi, Cardelli, Curien, and Lévy's *Explicit Substitutions* (Journal of Functional Programming 1(4), 1991, pp. 375–416, DOI: 10.1017/S0956796800000186) develops the lambda-sigma calculus, making substitutions explicit and studying their algebra. It uses de Bruijn notation and treats substitution composition and binder lifting as central infrastructure.

Stark's *Mechanising Syntax with Binders in Coq* (2019 dissertation, 2020) develops pure and scoped de Bruijn algebras, sigma calculi, substitution equations, and automation (Autosubst), including modular and many-sorted syntax.

M413's Ren, Sub, ext, exts, ren, sub, identity, four fusion laws, and the bridges from telescope weakening/instantiation are therefore standard sigma-calculus/de Bruijn infrastructure. The M413 module itself correctly disclaims novelty. Its value is that it supplies the exact interface needed by the C-20 development.

References:
- M. Abadi, L. Cardelli, P.-L. Curien, and J.-J. Lévy, “Explicit Substitutions,” JFP 1(4) (1991). https://doi.org/10.1017/S0956796800000186
- Kathrin Stark, *Mechanising Syntax with Binders in Coq* (2019/2020). https://www.ps.uni-saarland.de/Publications/documents/Stark_2020_Mechanising.pdf

### 1.5 Recent linear lambda calculus in de Bruijn notation

De Groote and Tourneur's 2026 preprint, *A Typing System for the Linear Lambda-Calculus in de Bruijn Notation* (arXiv:2607.20181), introduces fragmentary environments that make multiplicative linear typing work with de Bruijn indices, and proves subject reduction. It is a close comparator for the lambda/beta part of M264: de Bruijn linearity, resource-sensitive application, and reduction are already studied in a modern formal system. It is not identical to C-20's untyped usage-vector accounting, and it does not establish C-20's stored/type-level distinction or the Semplex provenance adapter. The correct conclusion is narrower: M264's basic beta/resource law is not itself a novelty claim.

Reference: Philippe de Groote and Vincent Tourneur, 2026. https://arxiv.org/abs/2607.20181

### 1.6 Representation independence and abstraction

Mitchell's *Representation Independence and Data Abstraction* (POPL 1986, DOI: 10.1145/512644.512669) formalizes when two implementations are equivalent because their operations behave correspondingly. Reynolds's *Types, Abstraction and Parametric Polymorphism* (1983) develops the abstraction theorem by generalizing homomorphisms to relations; it explicitly connects type abstraction, representation independence, information hiding, and parametricity. These are close precedents for the DAP requirement that protected observations and operations survive a representation change.

Abstract interpretation is another relevant comparator. Its Galois-connection framework formalizes sound, potentially lossy abstraction and supports compositional soundness theorems. DAP must explain what its certificate tracks beyond an abstraction/concretization pair and a soundness condition—especially if occurrence provenance and resource budgets are intended to be essential.

References:
- John C. Mitchell, “Representation Independence and Data Abstraction,” POPL 1986, DOI: https://doi.org/10.1145/512644.512669
- John C. Reynolds, “Types, Abstraction and Parametric Polymorphism,” 1983. https://people.mpi-sws.org/~dreyer/ats/papers/reynolds.pdf
- Patrick and Radhia Cousot, “Abstract Interpretation: A Unified Lattice Model for Static Analysis of Programs by Construction or Approximation of Fixpoints,” POPL 1977.

### 1.7 Provenance semirings and transformation lineage

Green, Karvounarakis, and Tannen's *Provenance Semirings* (PODS 2007, DOI: 10.1145/1265530.1265535) gives a compositional algebra for tracking how source facts contribute to query results. Input facts are annotated with indeterminates; alternative derivations combine by addition and joint dependencies by multiplication. The resulting provenance polynomials retain more information than a flat list of source identifiers, and many other provenance interpretations arise by semiring homomorphisms.

This is direct prior art for propagating origin information through transformations. Semplex's current origins tuple is substantially weaker: it concatenates origin IDs but does not encode alternative derivations, joint dependency structure, or transformation operators. If DAP needs compositional lineage, it must compare against provenance semirings rather than presenting origin-trail concatenation as a new provenance theory.

Grädel and Tannen's *Provenance Analysis and Semiring Semantics for First-Order Logic* (2024, arXiv:2412.07986) extends this line to full first-order logic with negation using quotient semirings and dual indeterminates. This broadens the logical scope beyond positive relational transformations.

References:
- Todd J. Green, Grigoris Karvounarakis, and Val Tannen, “Provenance Semirings,” PODS 2007. https://doi.org/10.1145/1265530.1265535
- Erich Grädel and Val Tannen, “Provenance Analysis and Semiring Semantics for First-Order Logic,” 2024. https://arxiv.org/abs/2412.07986

### 1.8 Coalgebraic observational provenance across non-injective rewrites

Tian and Liu's 2026 preprint, *Provenance Tracking in AI Compilers through the Lens of Coalgebra* (arXiv:2606.10937), is a particularly close comparator for the identity/provenance problem. It argues that value-preserving compiler rewrites can erase intermediate graph nodes and thereby destroy syntactic identity. Its proposed solution enriches coalgebraic semantics with explicit action states, relates fused and unfused action traces through an abstraction relation, and uses bisimulation to express observational correctness. The prototype applies this to AI compiler graph fusion, splitting, and elimination.

This overlaps directly with DAP's proposed requirement that transformations preserve declared observations even when internal representation and node identity change. It is a 2026 preprint, and its demonstrated scope is AI compiler graphs rather than a general typed calculus of arbitrary module transformations. Nevertheless, the conceptual overlap is too close to ignore. A DAP claim about provenance under non-injective transformations must compare against action-reflective coalgebra and bisimulation, not just database lineage or quotient descent.

Reference: Zilu Tian and Liying Liu, “Provenance Tracking in AI Compilers through the Lens of Coalgebra,” 2026. https://arxiv.org/abs/2606.10937

### 1.9 Proof-carrying and compositional transformation certificates

Quentin Garchery's *A Framework for Proof-carrying Logical Transformations* (2021, arXiv:2107.02352) instruments logical transformations to emit certificates that are checked independently by a third-party checker. Its skeptical architecture reduces trust in the transformation implementation; certificates with holes support incremental construction and composition of transformations.

This is direct prior art for the certificate/checker architecture proposed for DAP. DAP cannot claim novelty merely for having transformations emit certificates or for composing those certificates. The potential gap is the semantic content of the certificates: whether they can uniformly combine resource-aware environment maps, occurrence provenance, observational/bisimulation obligations, and module-indexed protected operations, while supporting lossy transformations with explicit, compositional loss reports.

Reference: Quentin Garchery, “A Framework for Proof-carrying Logical Transformations,” 2021. https://arxiv.org/abs/2107.02352

### 1.10 Resource transition systems and full abstraction

Dal Lago and Gavazzo's *Resource Transition Systems and Full Abstraction for Linear Higher-Order Effectful Programs* (FSCD 2021, DOI: 10.4230/LIPIcs.FSCD.2021.23) is a direct comparator for the proposed resource-indexed observational semantics. It introduces resource transition systems whose states explicitly carry tuples of reusable programs and linear values, so the operational semantics accounts for both ordinary effects and the intensional availability/consumption/copying of resources. Its main theorem proves that trace equivalence over these resource transition systems is sound and complete for contextual equivalence in its linear higher-order calculus with algebraic effects and explicit copying.

This establishes that resource-sensitive operational equivalence, contextual testing under linearity, and explicit-copying modalities are already developed in a rigorous setting. The calculus is simply typed (with recursive types) and effectful; it is not a general module-indexed representation-transformation calculus, nor does it integrate P091-style occurrence tokens with proof-carrying transformation certificates. Still, DAP's resource-indexed contextual-equivalence proposal must be compared directly against this result. Semplex's existing LTS and kernel_lts components may be closer to this line of work than the new design note initially recognized.

Reference: Ugo Dal Lago and Francesco Gavazzo, “Resource Transition Systems and Full Abstraction for Linear Higher-Order Effectful Programs,” FSCD 2021. https://doi.org/10.4230/LIPIcs.FSCD.2021.23.

## 2. Implications for M263/M264, P0LinearTyping/P0FullTyping, and M413

The M263 stored-usage accounting, P0LinearTyping's restricted typing/substitution fragment, M264 beta conservation at a linear redex, P0FullTyping's full-syntax typing fragment, and M413 fusion laws should be described as a formalized, project-specific assembly of known techniques unless a sharper difference is identified.

A mathematical precision point matters for M264: beta usage equality depends on both the multiplicity of the bound variable and the argument's usage vector. Multiplicity one is sufficient for every argument. It is necessary only when the argument has at least one nonzero usage coordinate; a usage-empty argument contributes zero on both sides for every multiplicity. The current theorem proves the sufficient case and the concrete weakening/contraction counterexamples, not a universal iff theorem. The explicit k=2 witness now compiles in Agda; it remains a local example, not a general iff theorem.

P0FullTyping is more developed than the earlier binder-free typing fragment: it defines types over the full M263 term syntax and proves telescoped substitution. However, its app constructor has no typing rule. Its betaPreservesTyping theorem types the instantiated contractum from a typed body and argument; it is not subject reduction from a typed application redex. The current Π type forgets the bound-variable usage coordinate when lambda discharges the binder. A graded Π carrying q = headU(bodyUsage) is the natural way to recover the argument-usage multiplier in an application rule. This is a real completion gap, but graded/quantitative function types are established QTT territory, not a novelty claim. See the separate graded-Π design note.

The C-20/Semplex adapter is not yet a cross-language equivalence:
- Agda's Usage is indexed by LCtx and built by snoc; its coordinates correspond to de Bruijn variable positions.
- Lean's P091 adapter zips an ordered List ResourceOccurrence with a List Nat.
- Python additionally supports an explicit token-to-variable bijection.
- The Lean result is an aggregate capacity upper bound for all-linear contexts with per-coordinate usage at most one.
- Agda's new P0C20UsageVectorBridge now compiles and proves an internal finite-vector/list serialization, coordinate/rank correspondence, length correspondence, the instUsageFull vector law, and vector-level corollaries of all four M413 fusion equalities. No theorem yet identifies that Agda list serialization with Lean's P091 profile function or proves the adapter commutes with arbitrary renaming/substitution.
- Semplex has a minimal persistent-capacity model (arbitrary finite demand, support-preserving contraction, provenance concatenation), but P091 excludes it and it is not an object-language exponential modality with promotion/dereliction or a two-zone substitution theorem.

## 3. Implications for Distinction Admissibility

The elementary condition that an observable descends through a quotient iff it is constant on equivalence classes, and that operations descend iff they respect the equivalence (congruence), is a standard universal-property result. It is not by itself a new logical principle.

A further close precedent is **observational congruence** in programming-language semantics: contextual equivalence is constructed by quantifying over all program contexts, and is the largest congruence contained in observational equivalence. This is precisely why immediate agreement on a chosen observation set is not enough; the permitted contexts/operations determine whether the equivalence is stable under composition. The resource-indexed version proposed in this project must be compared with this established contextual-equivalence construction, rather than presented as a new principle.

Reference: Stanford Encyclopedia of Philosophy, “Games, Full Abstraction and Full Completeness,” discussion of contextual equivalence and the largest congruence contained in observational equivalence: https://plato.stanford.edu/entries/games-abstraction/.

The potentially useful extension in DAP is not the certificate architecture alone (Garchery 2021), lineage propagation alone (Green–Karvounarakis–Tannen 2007), or observation-preserving provenance alone (Tian–Liu 2026). The candidate contribution would be a common typed interface in which a concrete transformation carries: (i) its induced identifications/kernel, (ii) protected observations and operations, (iii) resource-aware environment maps, (iv) provenance of occurrences and transformation actions, and (v) explicitly permitted losses. Composition would have to preserve these structures and expose exactly which obligations are weakened or discharged. Even this synthesis is only a hypothesis until its formal content is shown to exceed an assembly of the cited frameworks.

The strongest current Semplex contribution is therefore a candidate interface and executable/formal demonstrator, not a new foundation for logic.

## 4. Tests that could establish a stronger contribution

1. **Agda-to-vector representation — DONE:** P0C20UsageVectorBridge defines the finite vector/list serialization in de Bruijn order and proves length, rank-coordinate, and usage-coordinate correspondence with LCtx.
2. **Token/rank alignment — PARTIAL:** the Agda rank and usage vectors share the same indexed coordinates; Python's explicit token-to-variable map is tested under permutation. The Lean permutation theorem is being checked separately; a cross-language theorem remains open.
3. **Usage-aware environment correspondence — OPEN:** Wood–Atkey already provides matrix/linear-map semantics for resource-aware renaming and substitution. Prove that C-20's de Bruijn-indexed Usage serialization and P091's ordered Lean/Python adapter instantiate that framework, or identify a precise obstruction. Do not re-prove matrix composition as a novelty result.
4. **Substitution correspondence — PARTIAL:** P0C20UsageVectorBridge derives the vector form of instUsageFull, connects it to M413's instIsSub, and maps all four fusion equalities to vector equalities. The remaining work is a checked representation correspondence to the Wood–Atkey environment and P091, with exact all-linear side conditions.
5. **Provenance semantics — OPEN:** compare Semplex's flat origins tuple with provenance semirings (alternative/joint derivations) and with Tian–Liu's action-reflective coalgebra/bisimulation for non-injective graph rewrites. Determine whether DAP requires both data lineage and action lineage, and define their composition.
6. **Certificate composition — OPEN:** Garchery already establishes modular proof-carrying logical transformations and certificates with holes. Determine what extra semantic payload is needed to compose resource, provenance, and observation obligations, and formalize the checker independently.
7. **Module-indexed integration — OPEN:** formalize how protected observations, operations, identities, and resource contracts vary across Synesism modules; show that restriction, extension, and module composition preserve certificates. Compare this directly with usage-aware environments, provenance semantics, coalgebraic observational correctness, and representation independence.
8. **Comparative falsification:** build small countermodels where one component alone succeeds but the integrated certificate must reject or report loss. Only a concrete advantage over the separate prior-art frameworks can support a novelty claim.

## 5. Current novelty assessment

| Claim | Assessment |
|---|---|
| Usage vectors for binders and resource-sensitive substitution | Established prior art |
| Type-level use separated from runtime/computational use | Established prior art in QTT |
| De Bruijn renaming/substitution fusion | Established sigma-calculus infrastructure |
| Beta preserves usage for a linearly used bound variable | Standard consequence of quantitative substitution accounting |
| Quotient descent iff observable invariance; operations require congruence | Standard universal-property mathematics |
| Provenance-aware, token-indexed adapter from C-20 usage to Semplex resources | Potentially useful integration; currently finite and incomplete |
| Semiring provenance for transformation lineage | Established for broad classes of data/query transformations |
| Coalgebraic observational provenance across non-injective AI graph rewrites | Close 2026 preprint comparator; narrow compiler scope |
| Proof-carrying logical transformations and modular certificate composition | Established prior art |
| DAP as a unified resource/provenance/observation certificate calculus across heterogeneous modules | Open research hypothesis; novelty unestablished |

**Recommendation:** do not design another usage calculus or generic certificate language before comparing the concrete P091/DAP interface against Wood–Atkey, provenance semirings, Tian–Liu's action-reflective coalgebra, and Garchery's proof-carrying transformations. The most valuable possible result is a machine-checked composition theorem for a certificate that combines resource admissibility, data/action provenance, protected observations and operations, and explicit loss across heterogeneous modules—together with countermodels showing exactly why each component is necessary. If that theorem reduces to a straightforward product of existing structures, report that honestly rather than claiming a new foundation.
