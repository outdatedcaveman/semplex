# Toward a Causally Grounded Full-Abstraction Principle

**Date:** 2026-11-21
**Status:** research hypothesis and formal work plan; not a theorem, not a canon amendment, and not a novelty claim
**Change:** semantic-grounding-principle
**Coordination:** maintainer-approved joint ChatGPT / Antigravity-Gemini investigation. Gemini's isolated worktree supplies experiments; this canonical research note records the shared synthesis. Canonical Semplex edits by ChatGPT remain uncommitted; Gemini's separate `gemini/G15` branch is on `origin` and has not been merged.

## 0. The question

Can one mathematical principle explain, without conflating them:

1. how distinctions in the physical world acquire objective significance;
2. how an agent builds an internal representation that is about those distinctions and guides action;
3. how mathematical structures capture invariant relations that are independent of any one notation or realization?

The target is stronger than a common vocabulary. We need a structure that admits:
- a physical interpretation with counterfactual/interventional content;
- an internal/mental realization with a causal role in inference and action;
- an abstract mathematical formulation whose invariants survive changes of representation;
- exact theorems for finite cases, explicit hypotheses for stochastic/continuous cases, and falsifiable empirical predictions.

A formal proof relative to a chosen model does not establish that the model is the right model of reality. A physical implementation map must be independently grounded; a mathematical universal property does not select the empirically relevant observations by itself.

## 1. Working candidate

> **Contextual-Behavior / Distinction-Admissibility Principle:** the semantic content of an object is its complete response profile under all admissible contexts; semantic identity is equality of these profiles. In physics the contexts are physically realizable interventions; coalgebraically the profile is final behaviour; algebraically it is the invariant observable algebra; linearly it is the interventional Hankel operator. A representation is grounded when it is a physically implemented, causally efficacious, resource-bounded morphism preserving or quantitatively approximating that profile. Any transformation that merges, duplicates, abstracts, or removes distinctions is admissible only if it preserves protected contextual responses and resource/provenance invariants, or explicitly accounts for their loss.

Short form: **meaning is invariant behaviour under admissible contexts; representation is its causal realization.**

This is deliberately not stated as “meaning is information”, “meaning is prediction”, or “meaning is causal correlation”. It requires a structured family of interventions, responses, and admissible continuations. Passive correlation alone is insufficient; a representation must support counterfactual generalization and must participate in the mechanism by which the user succeeds or fails.

The hypothesis has three layers, not three substances:

- **Physical layer:** the world supplies a controlled dynamical structure and its lawful response to interventions.
- **Mental layer:** an agent constructs a finite, resource-bounded realization of the relevant response structure; the realization shapes its own predictions, inferences, and actions.
- **Mathematical layer:** abstract structures encode the relational invariants of such systems under structure-preserving maps. A physical interpretation is a model/realization map, not an identity between a mathematical object and a physical object.

The intended unity is a common theory of relations, transformations, and invariants. It does not yet prove substance monism, panpsychism, or that every mathematical object is physically instantiated.

## 2. Formal base: controlled dynamical systems

Let a system be a controlled stochastic process

\[
\mathcal S=(X,A,Y,K,O),
\]

where:
- \(X\) is the physical state space;
- \(A\) is the set of admissible interventions or controls;
- \(Y\) is the observation space;
- \(K(dx'\mid x,a)\) is the state-transition kernel;
- \(O(dy\mid x,a)\) is the observation kernel.

For deterministic systems, replace the kernels with functions. For histories \(h\in H\), let \(\mathcal U\) be a declared class of finite or infinite future intervention protocols. Define the counterfactual response profile

\[
\Phi_{\mathcal S}(h)(u,B)
  :=\Pr_{\mathcal S}(Y_{\mathrm{future}}\in B\mid h,\operatorname{do}(u)),
\]

for every admissible protocol \(u\in\mathcal U\) and measurable future-observation event \(B\).

The controlled predictive equivalence relation is

\[
h\sim_{\mathcal S,\mathcal U}h'
\quad\Longleftrightarrow\quad
\forall u\in\mathcal U,\ \forall B,\
\Phi_{\mathcal S}(h)(u,B)=\Phi_{\mathcal S}(h')(u,B).
\]

In a deterministic automaton with output behavior, this specializes to equality of all future input/output behavior (the Myhill–Nerode style relation). In stochastic processes it is related to predictive equivalence and causal states. With actions, it is closer to controlled predictive-state representations / epsilon-transducers than to passive prediction from an uncontrolled time series.

Let

\[
Q_{\mathcal S}:=H/{\sim_{\mathcal S,\mathcal U}}.
\]

This quotient is the candidate **causal-semantic state space** relative to the chosen intervention and observation protocol. It identifies exactly those histories that no permitted future test can distinguish.

### 2.1 Closure condition

For the quotient to carry induced dynamics, appending an admissible action/observation must respect equivalence:

\[
h\sim h'\implies h\cdot(a,y)\sim h'\cdot(a,y)
\]

whenever the update is defined (or the corresponding almost-sure / kernel-level condition in stochastic settings).

This is the closure / congruence obligation. It is not automatic for an arbitrary coarse-graining. For deterministic automata it is the familiar right-congruence condition. For stochastic systems it must be stated using the appropriate lumpability or predictive-state condition.

### 2.2 First theorem target: universal minimality of the causal quotient

**Target theorem A (finite exact form).** Given a finite controlled transition/output system and a fixed admissible test language closed under concatenation and residualization:

1. \(\sim\) is an equivalence relation;
2. the quotient \(Q_{\mathcal S}\) has well-defined induced transitions and outputs;
3. it preserves every declared test response;
4. for every other state representation \(r:H\to Z\) that is sufficient for all tests (equal representations imply equal response profiles), there exists a unique map \(\bar r: r(H)\to Q_{\mathcal S}\) or the appropriate factor map, with the direction fixed by the chosen convention.

The exact factorization direction and uniqueness statement must be checked carefully: the quotient is the coarsest sufficient partition, while any sufficient representation refines it. This is the universal property we want, not a slogan about “minimality”.

**Target theorem B (stochastic form).** Extend the construction to regular conditional distributions / controlled kernels, stating measurability, support, and almost-sure qualifications. Do not silently assume finite-state results generalize to arbitrary measurable spaces.

## 3. Grounded representation: the internal model must preserve counterfactual structure

Let an agent have internal state space \(Z\), update mechanism \(U:Z\times A\times Y\to Z\), and a representation map \(r:H\to Z\).

A weak data-predictive representation merely correlates with past observations. The stronger candidate grounding conditions are:

**(G1) Predictive adequacy.** There is a decoder \(\widehat\Phi:Z\to\mathsf{Resp}\) such that

\[
\Phi_{\mathcal S}=\widehat\Phi\circ r
\]

on the declared domain, exactly or within an explicit divergence bound.

**(G2) Dynamic commutation.** Updating the physical history and updating the internal representation commute:

\[
r(h\cdot(a,y))=U(r(h),a,y)
\]

for all admissible transitions (or a specified probabilistic coupling / naturality condition).

**(G3) Interventional robustness.** G1–G2 hold not only on the observed trajectory but across a declared family of interventions, including held-out compositions of interventions. This blocks accidental correlations and overfitting to the actual path.

**(G4) Causal efficacy in the user.** The internal state is a causal mediator in the mechanism producing inference/action. Interventions that alter the representational structure, while controlling relevant alternatives, change the system's downstream success in the predicted direction. A passive detector or a correlated by-product is not thereby a representation with the relevant content.

**(G5) Locality / nontrivial implementation.** The physical-to-internal mapping must be constrained by actual causal mechanisms, component organization, and counterfactual transitions. An arbitrary lookup mapping from a sufficiently complex physical trajectory is not enough. This is essential to avoid trivializing pancomputationalism.

**G1–G5 are proposed criteria, not jointly proved.** G1–G3 give a formal adequacy interface; G4–G5 address the grounding gap that purely formal semantics cannot close.

### 3.1 Meaning is not just correlation

Two histories can have the same passive observational statistics but different intervention responses. If the agent's internal state does not preserve the difference, it may predict the observed distribution while failing under intervention. Such a system is statistically calibrated on the training distribution but not grounded in the stronger counterfactual sense.

Conversely, an internal code can preserve the relevant response profile while differing radically in physical realization. Its content is then invariant across the allowed change of realization, not identical to the substrate.

### 3.2 Agent-relative realization and cost

The causal-semantic quotient specifies what distinctions are relevant relative to \((\mathcal U,\mathcal O)\). It does not determine which implementation an agent can afford.

For an agent \(A\), let \(\mathcal R_A\) be its available realizations. A candidate selection rule is

\[
r_A^*\in\arg\min_{r\in\mathcal R_A}
\bigl[\mathcal L_{\mathrm{pred}}(r)
      +\mathcal L_{\mathrm{action}}(r)
      +\lambda_A C_A(r)\bigr],
\]

subject to explicit resource constraints. Here:
- predictive loss measures mismatch of response profiles;
- action loss measures failure to preserve action-relevant consequences;
- \(C_A\) is a vector of implementation costs (state dimension, memory, latency, energy/dissipation, update cost, robustness);
- \(\lambda_A\) is an explicit exchange-rate vector or scalarization, not a hidden universal constant.

Do not combine incomparable costs into one number without specifying units, constraints, and exchange rates. Exact semantics is the zero-distortion case; approximate semantics requires a declared distortion budget.

This is where C42/C43 (predictive value minus kinematic/implementation cost) may fit. The cost should be derived from the agent's actual dynamics or thermodynamic constraints, not chosen post hoc to fit a preferred representation.

## 4. Mathematical form: response profiles, invariants, and Yoneda

A candidate categorical presentation begins with a category \(\mathcal C\) of controlled systems and structure-preserving maps. A test/probe object represents an admissible intervention-and-observation protocol. A system is interpreted by its response to every probe.

The Yoneda perspective is suggestive: an object is characterized, up to isomorphism, by its natural profile of relations to all probes in the category. But this is not yet the desired grounding theorem. The key open work is to define a **causal test category** whose morphisms encode admissible interventions and whose semantics records the corresponding response kernels, then show:

1. the response-profile construction is functorial;
2. physically implemented representations induce structure-preserving maps;
3. two representations are semantically equivalent exactly when their profiles are naturally isomorphic on the protected test category;
4. the construction is compositional under compatible translations;
5. the finite quotient of §2 is recovered as a special case.

**Important boundary:** Yoneda does not by itself tell us which probes are physically meaningful, which observations are normatively important, or which model describes the actual world. It tells us that an object is determined by its relations to all objects in a chosen category. The grounding burden is in constructing and justifying that category and its physical interpretation.

For formal mathematical structures, semantics is model-relative satisfaction plus invariant relational role. A physical system can instantiate a mathematical structure when a physically grounded interpretation map preserves the relevant operations and relations. This is a bridge between abstract and concrete structures, not a proof that abstract mathematics reduces to physical states.

## 5. Where C44 fits: invariant subspaces of the action on observables

For a deterministic automaton with states \(Q\), input alphabet \(A\), and transition \(\delta\), let \(V=\mathbb R^Q\) be the observable functions on states. Each input acts by a Koopman/pullback operator

\[
(T_a f)(q)=f(\delta(q,a)).
\]

For a partition \(\pi\) of \(Q\), let \(W_\pi\subseteq V\) be the span of its block-indicator functions.

**Known finite fact to formalize locally:** \(\pi\) is a transition congruence / closed deterministic coarse-graining iff \(W_\pi\) is invariant under every \(T_a\). The stochastic analogue is expressed through lumpability / invariant subspaces of the appropriate Markov operators.

This gives a bridge from behavioral closure to linear representation theory.

- For group actions, the generated algebra is semisimple under the usual characteristic-zero finite-group hypotheses; invariant representations decompose into irreducible constituents / isotypic components.
- For non-invertible monoid actions, semisimplicity can fail; invariant submodules may form non-split filtrations and extensions.
- The empirical C44 claim is that adaptive learners' dominant learned geometry lies in an invariant subspace, with selection among candidates governed by predictive value and implementation/kinematic cost.

**Critical caveat:** an arbitrary invariant *linear subspace* need not be the span of a partition's block indicators. C44's linear invariant-subspace statement is therefore not automatically the same as a semantic quotient or a closed coarse-graining. To recover quotient semantics, one may need a unital subalgebra / Boolean subalgebra / idempotent-closed condition, or a separate theorem relating the learned subspace to a partition. This is a central proof obligation, not a detail.

C44 may explain the geometry and construction of representations; it does not by itself define semantic content. The causal response profile in §2 is the candidate content; C44 explains which internal realizations can remain stable under the system's actions.

## 6. Peircean bridge (provisional)

A possible triadic interpretation is:

- **Object:** the external or target structure whose counterfactual constraints determine the response profile;
- **Sign:** the physically realized internal state / representation;
- **Interpretant:** the induced change in expectations, inferences, habits, or action dispositions when the sign is processed.

Semiosis is then not a static symbol-to-object correlation. It is an iterated, physically realized transformation in which the interpretant updates the agent's future response profile.

This mapping is interpretive until the object/sign/interpretant roles are typed and the relevant commuting diagrams are proved. It should be compared with Peirce's own definitions and contemporary biosemiotics rather than treated as an automatic consequence of predictive-state theory.

## 7. Minimal counterexamples and kill tests

The principle must survive all of the following. Each is a test, not an illustration.

1. **Passive-correlation trap:** construct two environments with the same observational distribution but different interventional response profiles. A representation trained only on passive data should be judged ungrounded if it fails the held-out intervention.
2. **Spurious physical implementation:** reproduce the warming-rock / alternating-bit mapping. The proposed criterion must reject the arbitrary mapping because the required counterfactual transitions are not supported by the rock's own causal organization.
3. **Readout blindness:** two physical states agree on current readout but a permitted future intervention distinguishes them. The quotient must keep them separate.
4. **Over-refinement:** two internal states have identical response profiles under all protected tests. The canonical semantic quotient must identify them even if the agent's hardware keeps both for cheaper dynamics or fault tolerance; this distinguishes semantic identity from implementation identity.
5. **Cover anomaly:** an implementation may retain a distinction not needed by the target if that cover is cheaper or dynamically more stable. The principle must allow representational surplus without falsely treating it as target content.
6. **Non-semantic invariant subspace:** produce an invariant subspace that is not an algebra of observables and does not define a quotient. This should refute any claim that C44 alone yields semantic closure.
7. **Goal/protocol dependence:** change the allowed interventions or protected observations. The semantic quotient should change in a predictable, explicit way. The theory must not conceal this relativity.
8. **No agent / no user:** a physical system can have objective causal structure without representing anything for an agent. The theory must distinguish worldly causal structure from representational content rather than declaring every causal state a mental representation.
9. **Mathematical non-instantiation:** formal structures can be studied without a known physical realization. The framework must preserve their formal semantics while leaving physical grounding as an additional interpretation question.
10. **Unidentifiable interventions:** where the intervention class cannot distinguish two causal models, the semantics is only identified up to that equivalence class. Do not claim recovery of the unique ontology from observational data alone.

## 8. Prior-art boundary: what is already known

The present candidate is surrounded by substantial prior art. At minimum, compare directly with:

- **Predictive-state representations:** Littman & Sutton (NeurIPS 2001) formulate state as action-conditional predictions of future observations and show a linear predictive representation bounded by the minimal POMDP state count.
- **Computational mechanics / causal states:** predictive equivalence of pasts by their future distributions gives minimal predictive partitions (Crutchfield–Shalizi and successors).
- **Causal closure / lumpability:** Rosas et al., *Software in the Natural World* (2024), connect causal closure to strong lumpability and coarse-graining.
- **Hankel / realization theory:** minimal input-output realizations and predictive operators already characterize state dimension and past-to-future behavior.
- **Interventionist causal semantics:** Pearl/Woodward-style interventions define counterfactual response structure, with well-known limits on identifiability and the admissible intervention language.
- **Physical implementation of computation:** counterfactual, causal, and mechanistic accounts explicitly reject arbitrary state mappings that satisfy only actual-transition matching.
- **Structural mental representation:** mechanistic-interventionist accounts argue that structural similarity can be causally relevant to success and distinguish internal models from mere detectors.
- **Categorical causal models:** Otsuka & Saigo (2022) define causal models as functors into stochastic matrices and compare them via natural transformations / equivalences; Mahadevan (NeurIPS 2025) develops topos causal models with a universal property.
- **Free-energy / information bottleneck / rate-distortion:** these already connect predictive accuracy and representational complexity; any new kinematic-cost term must be distinguished and derived.

The likely novelty, if any, is **not** “prediction grounds meaning”, “causal states are minimal”, “causal models are functors”, or “Yoneda determines objects by relations”. It may lie in a theorem-level integration of:
1. interventionally grounded response-profile semantics;
2. a typed internal representation map with causal efficacy;
3. resource- and dynamics-sensitive selection among realizations;
4. quotient/submodule coherence across reversible and irreversible actions;
5. compositional certificates that preserve the semantic profile through transformations.

Even that may be an integration or a new formal interface rather than new foundational mathematics. The prior-art review must decide.

## 9. Research plan for the joint 12-hour window

### ChatGPT: formal synthesis and adversarial theory
1. Fix the definitions of histories, tests, response profiles, equivalence, and the factorization direction.
2. Prove the finite quotient theorem and the equivalence between partition closure and invariant block-indicator subspaces.
3. Construct the counterexample showing invariant subspace does not imply quotient semantics.
4. State a representation-grounding theorem with explicit causal and intervention assumptions.
5. Compare with PFT, DAP, C-20/P091, categorical causal models, structural representation theory, and Peircean semiosis.
6. Draft the smallest defensible theorem package and a list of what remains metaphysical / empirical.

### Antigravity/Gemini: mechanistic derivation and experiments
1. Finish the already-running G15 verification; do not start additional heavy jobs until it completes and memory is safe.
2. Reconcile C42/C43, C44, predictive-kernel/Hankel results, and G18's predictive-kernel identity.
3. Derive whether the learned invariant subspace can be predicted from the observable action algebra, input module, readout module, and explicit kinematic cost.
4. Design one pre-registered held-out test distinguishing:
   - predictive-information-only selection;
   - invariant-subspace / causal-closure selection;
   - predictive-value-minus-kinematic-cost selection.
5. Use groups and non-invertible monoids, with unseen automata and held-out intervention sequences. Include fixed-reservoir and matched-random controls.
6. Test finite examples analytically / exactly before training. Report held, broken, or inconclusive without moving thresholds post hoc.

### Joint coordination
- Shared evidence and decisions go to Egon Mind; do not duplicate experiments.
- Gemini works only in its isolated worktree; canonical edits are coordinated through this shared note.
- No commits, pushes, merges, or changes to frozen experiments without explicit authorization.
- Respect the two-side-session limit, sequential WSL/Agda rule, resource gates, and existing runner controls.
- A 12-hour window is an allocation of research priority, not a claim that an autonomous process will run unattended after the chat ends.

## 10. Acceptance gates

The candidate advances only if all six gates are addressed:

1. **Mathematical well-posedness:** definitions and domains are precise; no hidden quantification over an unspecified set of tests.
2. **Nontriviality:** the theory rejects spurious mappings and passive correlations while allowing legitimate multiple realizations.
3. **Compositionality:** response-profile preservation composes under explicit compatibility conditions.
4. **Cross-domain adequacy:** the same formal interface can be instantiated in physical dynamics, internal agent models, and abstract mathematical structures without conflating their ontologies.
5. **Prior-art honesty:** each component is classified as known, derived, integrated, or potentially novel.
6. **Falsifiability:** at least one prospective test can break the central selection law, not merely fit it post hoc.

If the candidate fails, preserve the failure and narrow the claim. The goal is not to force a grand unification but to discover the strongest principle the evidence actually supports.

## 11. Initial source dossier

- Littman, M. L. & Sutton, R. S. (2001), “Predictive Representations of State”, NeurIPS 14. https://proceedings.neurips.cc/paper/2001/hash/1e4d36177d71bbb3558e43af9577d70e-Abstract.html
- Otsuka, J. & Saigo, H. (2022), “On the Equivalence of Causal Models: A Category-Theoretic Approach”, PMLR 177, 634–646. https://proceedings.mlr.press/v177/otsuka22a.html
- Mahadevan, S. (2025), “Universal Causal Inference in a Topos”, NeurIPS 38. https://proceedings.nips.cc/paper_files/paper/2025/hash/b62038599eb650d601ffac6e0e77b437-Abstract-Conference.html
- Stanford Encyclopedia of Philosophy, “Computation in Physical Systems”, Winter 2025 archive, especially §§2.1–2.2 on simple mappings and counterfactual/causal restrictions. https://plato.stanford.edu/archives/win2025/entries/computation-physicalsystems/
- “Structural representations: causally relevant and different from detectors” (2017), *Biology & Philosophy* 32, 337–355. DOI: 10.1007/s10539-017-9562-6.
- Rosas et al. (2024), “Software in the natural world: A computational approach to hierarchical emergence”, arXiv:2402.09090.
- Crutchfield & Shalizi (2001), computational mechanics / causal states; exact citation and theorem scope to be verified in the full prior-art pass.
- Woodward (2003), *Making Things Happen*; Pearl (2009), *Causality*, for interventionist causal structure.
- Peirce, *Collected Papers*, sign/object/interpretant passages; exact edition/paragraph references to be verified before citation.



## 12. A concrete theorem already within reach: partition closure iff invariant indicators

Let \(Q\) be finite, \(A\) a finite alphabet, and \(\delta:Q\times A\to Q\) a deterministic transition function. For each \(a\in A\), define \(T_a:\mathbb R^Q\to\mathbb R^Q\) by \((T_af)(q)=f(\delta(q,a))\).

For a partition \(\pi\) of \(Q\), let \(W_\pi\) be the span of \(\mathbf 1_B\) for blocks \(B\in\pi\).

**Proposition (indicator-subspace characterization).** The following are equivalent:

1. \(\pi\) is a transition congruence: if \(q\sim_\pi q'\), then \(\delta(q,a)\sim_\pi\delta(q',a)\) for every \(a\in A\).
2. \(W_\pi\) is invariant under every Koopman operator \(T_a\).

**Proof.**

(1 ⇒ 2) It suffices to show \(T_a\mathbf 1_B\in W_\pi\) for each block \(B\). Its value at \(q\) is \(1\) exactly when \(\delta(q,a)\in B\). By congruence, this predicate is constant on each block of \(\pi\); therefore it is a linear combination of block indicators.

(2 ⇒ 1) Suppose \(W_\pi\) is invariant. Then \(T_a\mathbf 1_B\) belongs to \(W_\pi\), hence is constant on each block. For \(q,q'\) in the same block and every block \(B\), we have \(\delta(q,a)\in B\) iff \(\delta(q',a)\in B\). Since the blocks partition \(Q\), the two successors belong to the same block. Thus \(\pi\) is a congruence. ∎

This is the finite deterministic bridge from Myhill–Nerode-style closure to Koopman invariance. It is not claimed as new mathematics; the contribution would be its role in the larger grounding calculus and its extension to the resource-/intervention-indexed settings.

### 12.1 Why arbitrary invariant subspaces are not enough

Take \(Q=\{0,1,2\}\) and one constant-reset transition \(\delta(q,a)=0\) for all \(q\). Let \(f(q)=q\), and \(W=\operatorname{span}\{\mathbf 1,f\}\). Then \(T_a\mathbf 1=\mathbf 1\) and \(T_af=f(0)\mathbf 1=0\), so \(W\) is invariant. But \(W\) is not closed under pointwise multiplication because \(f^2=(0,1,4)\) is not in \(\operatorname{span}\{(1,1,1),(0,1,2)\}\). Hence \(W\) is not the algebra of all functions constant on a partition.

This is a decisive warning: **invariant linear geometry does not automatically define a semantic quotient.** If C44 is intended to describe semantic coarse-grainings, the candidate learned subspace must additionally satisfy a suitable algebra/idempotent condition, or a different interpretation theorem must be supplied. If it does not, C44 may describe representational geometry without being the content semantics itself.

### 12.2 Group versus monoid: exact hypotheses

For a finite group \(G\) over a field of characteristic zero, Maschke's theorem gives semisimplicity of the group algebra; finite-dimensional representations decompose into irreducibles. For a finite monoid \(M\), the monoid algebra need not be semisimple. The presence of non-invertible actions can yield non-split extensions and invariant-subspace filtrations.

Do not infer that every monoid representation has only triangular one-dimensional factors: that requires additional aperiodicity / algebraic hypotheses and a precise field. Likewise, the maximal-subgroup / regular-J-class description must be stated using the exact Clifford–Munn–Ponizovskii hypotheses. C44's representation-theoretic story must be audited at this level before it is promoted to a general theorem.

## 13. Immediate proof obligations

1. Prove Proposition §12 in Lean for finite types and finite partitions, with no classical axioms beyond those required for finite decidability.
2. Prove that the response-profile equivalence of §2 is a right congruence under the chosen test-language closure assumptions.
3. Prove the quotient's universal property with the factorization direction made explicit.
4. Formalize the finite stochastic analogue: identify the exact lumpability condition and its operator-theoretic statement.
5. Prove / refute the claim that the relevant learned subspaces in C44 are subalgebras or are otherwise sufficient to determine a quotient.
6. Derive the relationship between the predictive Hankel operator, the response-profile map, and the Koopman action; do not identify their kernels or row partitions without a theorem.


## 14. A more general interface: probe-response semantics

The response-profile construction can be abstracted without prematurely identifying every domain with a stochastic process.

Let \(\mathcal P\) be a category of admissible probes:
- objects are test protocols / contexts;
- morphisms are lawful extensions, reparameterizations, or compositions of tests;
- composition records how one test can be continued or transformed into another.

For a system-state \(x\), define a response assignment

\[
R_x:\mathcal P\longrightarrow\mathcal O,
\]

where \(\mathcal O\) is an appropriate response category (sets, distributions, stochastic kernels, traces, or a typed observation category). Functoriality says that transforming a probe transforms its predicted/actual response coherently.

**Probe-response semantic equivalence** is equality (or a specified natural equivalence) of the response assignments over every protected probe. The exact choice matters:
- pointwise equality is appropriate when observation labels and probabilities are fixed;
- natural isomorphism is appropriate when only structure, not the names of response coordinates, is protected;
- a divergence bound is appropriate for approximate or noisy realizations.

This is a reusable schema, not a new theorem. Its value is that the physical, mental, and mathematical cases can instantiate different probe and response categories while sharing the same preservation calculus.

### 14.1 Three instantiations

**Physical:** probes are interventions and measurement protocols; responses are distributions over subsequent observations and physical outcomes. The response assignment is the controlled counterfactual profile of §2.

**Mental:** probes are admissible cognitive contexts, questions, action options, or sensory perturbations; responses are inferential transitions, expectations, and action dispositions. An internal state has content only to the extent that its response profile is grounded in the external causal profile and is causally used by the agent.

**Mathematical:** probes are structure-preserving maps, contexts, or constructions; responses are the resulting morphisms, truth values, or induced structures. A mathematical object is characterized by its relational profile within a specified category. Yoneda is the canonical theorem showing that the representable profile \(\operatorname{Hom}_{\mathcal C}(-,x)\) determines \(x\) up to isomorphism.

The mathematical instantiation is not identical to the physical one: a morphism in a mathematical category need not be a physically executable intervention. The bridge is a semantics/realization functor that maps a selected mathematical probe language to physical interventions and preserves their responses.

### 14.2 The bridge theorem to aim for

Let \(\mathcal P_S\) be a protected probe category for a source system and \(\mathcal P_T\) one for a target representation. Let \(F:\mathcal P_S\to\mathcal P_T\) translate probes, and let \(R_S,R_T\) be their response functors.

A transformation is semantically adequate when there is a natural isomorphism (or a declared approximate natural transformation)

\[
R_S\ \cong\ R_T\circ F
\]

on the protected probe subcategory, together with a causal implementation condition ensuring that \(F\) corresponds to physically supported interventions rather than arbitrary relabeling.

If two such translations compose and their intermediate probe/response interfaces match, naturality composes. This gives a candidate mathematical spine for DAP's compositional certificates. The difficult theorem is not that natural transformations compose; it is that the resource, causal, provenance, and loss side conditions are preserved by the composite.

**Do not call this “the Yoneda semantics of everything”.** Yoneda supplies the representation theorem for one mathematical instantiation. The general response-functor schema needs its own definitions, adequacy theorem, and physical grounding conditions.


## 15. Machine-checking status

A first Lean 4 core-only module has been drafted at:

- `proofs/lean/CausalClosure.lean`

It states the equivalence between transition congruence and stability of all block indicators under the Koopman pullback maps. **It has not yet been compiled or axiom-audited.** Do not cite it as a checked theorem until the local Lean 4.12.0 compile succeeds and an audit confirms the expected axiom base. The full span/subalgebra statement, stochastic version, predictive quotient theorem, and grounded-representation theorem remain open.


## 16. Integration with Gemini's already-formalized Master Principle

This section records an important result already present in the isolated branch `gemini/master-principle`; it is not new work in the canonical branch. Source files were inspected directly:

- `proofs/lean-mathlib/MasterPrinciple.lean`
- `proofs/lean-mathlib/AuditMasterPrinciple.lean`
- `HANDOFF_MASTER_PRINCIPLE.md`
- G18: `proofs/lean-mathlib/PredictiveKernel.lean` and `HANDOFF_G18.md`

### 16.1 The operator

For a finite automaton with positive state weighting \(\pi\), input transitions \(\delta_a\), and readout \(o\), Gemini's candidate realization operator is

\[
\mathcal G_{\mathcal A}(\lambda)
=
P_\perp\,
e^{-\frac{\lambda}{2}\mathcal L_{\mathrm{kin}}}
\bigl(W_c(\gamma_c)+W_o(\gamma_o)\bigr)
e^{-\frac{\lambda}{2}\mathcal L_{\mathrm{kin}}}
P_\perp.
\]

Its components have distinct roles:

- \(W_c\): past-reachability / input-conditioned distinguishability, propagated by the Perron–Frobenius adjoints of the Koopman actions;
- \(W_o\): future observability / output consequence, propagated by the forward Koopman actions and the readout;
- \(\mathcal L_{\mathrm{kin}}\): a nonnegative Dirichlet operator measuring the average squared change of an observable under the input transitions;
- \(P_\perp\): removal of the constant mode.

The two-sided heat factors penalize modes that are expensive under the system's own transition dynamics. This is not merely the predictive information bottleneck: the candidate cost is an operator derived from the kinematics of the input actions, not just a KL penalty on a chosen latent distribution.

### 16.2 What is formally established on Gemini's branch

The handoff records a successful Mathlib build and axiom audit for 18 exported declarations (Lean 4.12.0 + Mathlib 4.12.0; zero `sorryAx`; audited dependencies limited to `propext`, `Classical.choice`, and `Quot.sound`). The inspected declarations establish, among other things:

- the exact \(L^2(\pi)\) adjoint identity between the Koopman pullback and the past-step operator;
- self-adjointness and nonnegativity of the Dirichlet kinetic operator, plus its exact quadratic-form identity;
- vanishing of \(W_c\) on every bijective, \(\pi\)-preserving input automaton (in particular, finite group actions with uniform \(\pi\));
- reduction on joint eigenmodes to the Gibbs-style weight \(e\,e^{-\lambda c}\), recovering C43 in the group case;
- the Boolean-hypercube identity connecting the kinetic form to normalized total Boolean influence.

This gives a mathematically explicit bridge from input dynamics to representation geometry. It does **not** yet prove that \(\mathcal G\) is the unique or universally optimal semantic representation, nor that the heat-damping mechanism is derived from a general learning dynamics.

### 16.3 What the pre-registered experiment actually says

The master-principle handoff reports 180/180 runs completed, with 5 HELD, 2 NEITHER, and 1 BROKEN:

- **Held:** linear-readout GRU alignment (HM.2); LSTM and tanh-RNN alignment (HM.3a); group-case leading-irrep prediction (HM.4); initialization-to-training shift from reachability-dominated toward observability-dominated geometry (HM.5b).
- **Broken:** the frozen universal \(\lambda_0\) did not beat the unheated \(W_c+W_o\) median for GRU-MLP (HM.1b).
- **Neither:** GRU-MLP's primary alignment threshold narrowly missed (HM.1a); isotropic state noise did not reliably lower kinetic energy (HM.5a).

The exploratory optimum \(\lambda^*\) varied by architecture: spectral/no-recurrence near zero; GRU around 0.75–1.0; LSTM/RNN around 1.0–1.5. The correct interpretation is therefore **architecture-/resource-dependent exchange rate**, not one fixed universal constant. The fixed \(\lambda_0=1.476410\) was calibrated on Spike 77 and must not be advertised as substrate-independent.

The mechanistic observation HM.5b is particularly useful: at initialization the GRU-MLP geometry was much closer to \(W_c\); after training it became more aligned with \(W_o\). This suggests a learning process that starts with what the recurrent substrate can reach and progressively organizes it around what the readout makes consequential. It is evidence for a mechanism in this experiment, not yet a derivation from general learning laws.

G18's Lean proof is narrower still: it proves the counting and expectation identities for one-hot left-coset readouts of finite group actions, connecting their predictive kernel to the permutation character. It is not a proof of the full Hankel/predictive-kernel identity for arbitrary controlled systems.

### 16.4 The stronger synthesis: content versus realization

The evidence suggests that the sought principle should be typed into two inseparable but non-identical clauses:

**(C) Causal-response content.** The content of a distinction is its profile of differences in future observations and action consequences across admissible interventions. Histories with identical profiles are semantically equivalent relative to the protected probe category; histories with different profiles must not be collapsed.

**(R) Causal-kinetic realization.** An adaptive physical agent realizes that content in a finite internal state space. Its representational geometry is selected from the available dynamically closed / action-invariant structures by a trade-off among past reachability, future observability, and the actual cost of implementing the input dynamics. \(\mathcal G_{\mathcal A}(\lambda)\) is a concrete finite-automaton candidate for the operator governing that trade-off; \(\lambda\) is determined by the architecture, substrate, and resource regime, not assumed universal.

The mathematical layer expresses both clauses invariantly: (C) as equivalence of response functors on a probe category; (R) as the spectral / module structure of operators induced by the system's action on observables. A physical realization functor must preserve the protected response structure; an agent's internal functor is an approximate, resource-bounded realization of it.

This gives a more defensible unifying statement than “everything is prediction”:

> **A semantic distinction is an invariant counterfactual difference; a representation is a physically realized, cost-sensitive model of those differences.**

### 16.5 New proof obligations created by the synthesis

1. Show that the causal-response quotient of §2 is the correct content object for the same controlled automata on which \(W_c,W_o,\mathcal L_{\mathrm{kin}}\) are defined.
2. Show that the protected response quotient is stable under all input transitions (the closure theorem), and state when its observable algebra is represented by invariant subspaces.
3. Prove that the top spectral modes of \(\mathcal G_{\mathcal A}(\lambda)\) live in / approximate the admissible semantic observable algebra, rather than merely being invariant vectors with no quotient interpretation.
4. Derive the architecture-dependent \(\lambda^*\) from measurable physical/algorithmic parameters (state stiffness, gate dynamics, noise, update rule, energy budget) instead of post-hoc calibration.
5. Explain why the reachability-to-observability shift appears during training, and derive or falsify it for non-gradient learners and physical/chemical substrates.
6. Show that the same response-preserving maps compose across physical, cognitive, and mathematical levels, with explicit distortion and resource budgets.
7. Separate objective content from normative relevance: a response profile says what changes under interventions; it does not, alone, determine which outcomes matter to an agent or why a biological system should care.

**Current assessment:** the two-clause synthesis is the strongest candidate so far. Its components are largely known or already formalized; the possible contribution is the exact connection between causal-semantic quotients, action-invariant observable algebras, and the resource-dependent operator selecting internal realizations. That connection remains open.


## 17. The quotient theorem in its exact universal-property form

Bundle all protected test responses into one map

\[
\Phi:H\longrightarrow \mathsf{Resp}
:=\prod_{u\in\mathcal U}\mathsf{Dist}(Y^{*}),
\qquad
\Phi(h)(u)=\Pr(Y_{\mathrm{future}}\mid h,\operatorname{do}(u)).
\]

Define \(h\sim h'\) iff \(\Phi(h)=\Phi(h')\), and let \(q:H\to H/{\sim}\) be the quotient map. Then \(\Phi\) factors uniquely as

\[
H\xrightarrow{q}H/{\sim}\xrightarrow{\bar\Phi}\operatorname{im}(\Phi),
\]

where \(\bar\Phi([h])=\Phi(h)\) is a bijection.

Now let \(r:H\to Z\) be any other representation that is sufficient for these tests: there exists \(d:Z\to\mathsf{Resp}\) such that \(\Phi=d\circ r\). Restricting to \(\operatorname{im}(r)\), there is a unique surjection

\[
u_r:\operatorname{im}(r)\twoheadrightarrow H/{\sim}
\quad\text{such that}\quad
q=u_r\circ r.
\]

It is well-defined because \(r(h)=r(h')\) implies \(\Phi(h)=d(r(h))=d(r(h'))=\Phi(h')\), hence \([h]=[h']\). It is unique because every element of \(\operatorname{im}(r)\) is \(r(h)\) for some history.

This is the exact universal property intended in Target Theorem A: **every sufficient representation refines the causal-semantic quotient**. The quotient is the coarsest state that preserves every protected response. It is not necessarily the cheapest physical realization; an implementation can retain redundant distinctions for robustness or lower transition cost.

### 17.1 Probe hierarchy and lawful perspective

Let \(\mathcal U_{\mathrm{task}}\subseteq\mathcal U_{\mathrm{agent}}\subseteq\mathcal U_{\mathrm{phys}}\), where:
- \(\mathcal U_{\mathrm{phys}}\) contains all interventions physically admissible in the model;
- \(\mathcal U_{\mathrm{agent}}\) contains those the agent can sense, perform, or reliably model;
- \(\mathcal U_{\mathrm{task}}\) contains the protected tests relevant to a particular task.

Then more tests can only refine the quotient:

\[
\mathcal U_1\subseteq\mathcal U_2
\quad\Longrightarrow\quad
\sim_{\mathcal U_2}\ \subseteq\ \sim_{\mathcal U_1}.
\]

Thus an agent's perspective is not arbitrary subjectivity: it is a lawful coarse-graining induced by its physically accessible probe set and resource limits. Two agents can have different modules because their probe categories and realization costs differ, while both are constrained by the same underlying physical response structure.

This gives a precise place for Synesism's Module concept, but it also makes the relativity explicit: content is invariant *relative to a protected probe category*. There is no unique task-independent finite quotient unless a maximal physically meaningful probe class is specified.


## 18. Stronger central object: the interventional Hankel operator

The two-clause synthesis becomes more coherent if the common object is not merely a quotient or a Gramian, but the **interventional past-to-future response operator**.

Let \(\mathcal H^-\) be admissible past histories, \(\mathcal U^+\) future intervention protocols, and \(\mathcal Y^+\) future observation events. Define

\[
H_{\mathcal S}(h,u)(B)
:=
\Pr_{\mathcal S}(Y^+\in B\mid h,\operatorname{do}(u)).
\]

In finite deterministic transducers this is a (possibly weighted) Hankel matrix whose rows are future response profiles and whose columns are future tests. In stochastic controlled systems it is an operator/kernel valued in probability distributions. This is the causal/interventional strengthening of the ordinary observational Hankel construction.

### 18.1 Three objects that must not be conflated

1. **Row equivalence / semantic content:** histories \(h,h'\) are equivalent iff \(H(h,-)=H(h',-)\) over every protected future intervention. The quotient is the minimal deterministic/predictive state partition relative to that test class.
2. **Linear Hankel rank / realization dimension:** in finite-dimensional weighted linear systems, the rank of \(H\) gives the minimal linear realization dimension under the relevant controllability/observability assumptions. It is not generally the number of causal states. A stochastic process can have finite Hankel rank and infinitely many predictive/causal states.
3. **Cost-sensitive learned geometry:** \(W_c\), \(W_o\), and \(\mathcal L_{\mathrm{kin}}\) describe reachability, observability, and transition cost in a chosen Hilbert realization. \(\mathcal G_{\mathcal A}(\lambda)\) is a candidate operator for selecting an internal geometry; it is not itself the semantic quotient or the Hankel operator.

This distinction is essential. The quotient is the content-level object; the Hankel operator records the full past-to-future response relation; a realization is a factorization of that operator; and \(\mathcal G\) is a proposed cost-sensitive selection rule among realizations.

### 18.2 The realization picture

In a finite linear system, the Hankel operator admits a reachability/observability factorization

\[
H=\mathcal O\,\mathcal R,
\]

where \(\mathcal R\) maps past input histories into a state realization and \(\mathcal O\) maps that state into future output responses. Minimal realizations are controllable and observable; under standard hypotheses they are unique up to invertible change of state coordinates.

This supplies the physical/mental/mathematical bridge:

- **Physical:** the process implements the causal input-to-output map and its counterfactual response to interventions.
- **Mental:** an internal state is a realization/factorization of that map, learned under the agent's finite memory, action, and energy constraints.
- **Mathematical:** the operator and its realization invariants are independent of the arbitrary coordinates used by a particular implementation.

A mental representation is therefore not required to resemble the world point-for-point. It must preserve the relevant causal response structure well enough for the agent's inferences and actions. Different agents may use non-isomorphic coordinates or different approximate realizations while tracking the same protected response operator.

### 18.3 Relationship to the Master Operator — and a necessary warning

The classical Hankel/SVD realization theory does not automatically imply Gemini's \(\mathcal G\). In standard balanced truncation, Hankel singular values are related to the controllability/observability Gramians through the spectrum of \(W_cW_o\) (or a symmetric equivalent such as \(W_c^{1/2}W_oW_c^{1/2}\)). Gemini's candidate instead uses a two-sided heat-damped sum \(W_c+W_o\).

Therefore:

- the reachability/observability ingredients have a clear system-identification interpretation;
- the kinematic heat regularizer is a plausible additional physical cost;
- **no theorem yet shows that the spectrum of \(\mathcal G\) is the optimal truncation of the interventional Hankel operator**;
- the empirical results support some alignments, but the broken fixed-\(\lambda\) hypothesis and architecture dependence prevent a universal-operator claim.

The next mathematical question is whether \(\mathcal G\) can be derived as the optimizer of a well-posed variational problem for approximate causal realizations, and under what assumptions that optimizer is equivalent to, or differs from, balanced Hankel truncation.

### 18.4 What is genuinely stronger than ordinary predictive equivalence

Classical computational mechanics defines causal states by equality of conditional future distributions given observed pasts. That is a powerful, established theory, but it is observational unless the process model includes controlled interventions. Our proposed extension indexes the response profile by future interventions \(\operatorname{do}(u)\), and requires the internal realization to preserve the intervention calculus and to be causally efficacious in its user.

This extension is close to controlled predictive-state representations and epsilon-transducers; it must be compared with those directly. It is not enough to rename predictive equivalence as “semantic grounding”. The grounding claim requires G2–G5, and the representation-selection claim requires a prospective derivation of the cost term and exchange rate.


## 19. A concrete obstruction: forward semantic closure need not survive past reachability

The distinction between content and realization is not merely philosophical. The current Master Principle's past-reachability term can leave the forward predictive quotient even in a tiny finite stationary system.

Take four states \(Q=\{A_0,A_1,B_0,B_1\}\), three equally likely input letters \(a,b,c\), and transitions:

| State | \(a\) | \(b\) | \(c\) |
|---|---|---|---|
| \(A_0\) | \(A_0\) | \(B_0\) | \(A_1\) |
| \(A_1\) | \(A_0\) | \(B_1\) | \(A_0\) |
| \(B_0\) | \(A_0\) | \(B_0\) | \(B_1\) |
| \(B_1\) | \(A_1\) | \(B_1\) | \(B_0\) |

The full-support stationary distribution for the uniform random input is

\[
\pi=(7,4,6,5)/22.
\]

The partition \(\Pi=\{\{A_0,A_1\},\{B_0,B_1\}\}\) is a forward transition congruence:
- \(a\) sends every state to block A;
- \(b\) sends every state to block B;
- \(c\) preserves the A/B block.

Thus every block-constant observable remains block-constant under each Koopman pullback \(T_a f=f\circ\delta_a\). The two-block quotient is an exact deterministic predictive quotient for any output depending only on the A/B block.

Now take the centered block-constant observable

\[
f=\mathbf 1_A-\tfrac12\mathbf 1=(\tfrac12,\tfrac12,-\tfrac12,-\tfrac12).
\]

For the past-step adjoint in \(L^2(\pi)\),

\[
(T_a^*g)(r)=\frac{1}{\pi(r)}
\sum_{q:\delta_a(q)=r}\pi(q)g(q),
\]

the scalar \(\langle\mathbf 1,T_a f\rangle_\pi\) is \(+1/2\) for input a, \(-1/2\) for b, and 0 for c. Substituting into the exact MasterPrinciple recursion for \(W_c\) at horizon \(T=1\) gives

\[
W_c(\gamma_c,1)f
=\gamma_c\,(17/42,\ 5/24,\ -13/36,\ -3/10).
\]

This vector is still centered under \(\pi\), but it is **not** block-constant: its A coordinates differ, and its B coordinates differ. Therefore the past-reachability Gramian does not, in general, preserve the forward predictive quotient algebra—even though the partition is a transition congruence and \(\pi\) is stationary for the random input process.

Consequences:

1. We must not claim that \(W_c\), or \(\mathcal G\), automatically acts on the minimal forward semantic quotient.
2. \(W_c\) may encode implementation/history-access structure that refines the forward content quotient. Such refinement may be useful for realizing the process, but it is not automatically additional semantic content.
3. A theorem connecting \(\mathcal G\) to semantic content needs an extra condition (e.g. reverse lumpability / adjoint-invariance), a projection onto the semantic observable algebra, or an explicit split between content modes and implementation modes.
4. This is a decisive small test for Gemini: verify the exact calculation independently and determine whether the correct general condition is two-sided lumpability, a balanced quotient, or a constrained realization objective.

This is a substantive restriction on the unification hypothesis, not a refutation of the Master Principle. It sharpens the proposed division: **the response quotient specifies what is to be preserved; reachability and kinematic cost specify how a physical agent can realize it, possibly with extra implementation state.**


## 20. The deepest common form: the present as a causal interface

The response–realization principle can be stated even more compactly in the language of causal mediation.

At a temporal cut, let \(H^-\) denote the past context, \(Z\) a candidate present state/interface, \(U^+\) a future intervention protocol, and \(Y^+\) a future observation/outcome. A sufficient causal interface satisfies

\[
\Pr(Y^+\mid H^-=h,\operatorname{do}(U^+=u))
=
\Pr(Y^+\mid Z=r(h),\operatorname{do}(U^+=u))
\]

for every protected past \(h\), future intervention \(u\), and outcome event. In the stochastic case, \(Z\) may be a distribution over internal states rather than a deterministic code.

Equivalently, the interventional past-to-future response kernel factors through the interface:

\[
H_{\mathcal S}=\mathcal O\circ\mathcal R,
\]

where \(\mathcal R\) maps past contexts to present states and \(\mathcal O\) maps present states to future response profiles. This is the causal-interface form of the reachability/observability factorization.

The **Causal Interface Principle (CIP)** is the strongest current compact formulation:

> At any chosen causal cut, semantic content is the invariant past-to-future response structure that can pass through the present interface. A representation is grounded when it is a physically implemented, interventionally adequate, causally efficacious factorization of that structure. Its internal geometry is selected under the reachability, observability, and physical cost constraints of the realizing system.

This makes the distinction between content and implementation precise:
- the response kernel \(H\) is what must be preserved;
- the minimal response quotient is the coarsest sufficient semantic interface;
- a physical or mental implementation may refine that quotient to make the interface reachable, robust, or cheap;
- \(W_c\) measures aspects of reachability, \(W_o\) aspects of observability, and \(\mathcal L_{\mathrm{kin}}\) the transition cost of the realization;
- \(\mathcal G_{\mathcal A}(\lambda)\) is a candidate selector of internal geometry, not the content kernel itself.

### 20.1 Why this is a better bridge across the three domains

- **Physical world:** every causal process mediates between preparation/history and possible later outcomes. The response kernel is fixed by the physical transition and intervention structure.
- **Mental world:** a mental state is an internal causal interface. It compresses past sensory/action history while preserving the distinctions needed for future inference and action. It is not grounded merely by correlation; it must be a working mediator in the agent's causal organization.
- **Mathematical world:** the response kernel and its factorizations form an abstract relational object. Different coordinate systems / realizations are equivalent when they preserve the same protected response structure. Universal properties characterize the interface independently of its notation.

This is a common *structural role*, not a claim that a neuron, a physical state, and a mathematical object are literally the same kind of substance.

### 20.2 Connection to Peirce (still provisional)

The interface picture suggests a disciplined triadic reading:
- the **object** constrains which past-to-future response relations are physically possible;
- the **sign** is the present, physically realized mediator carrying a compressed state of those relations;
- the **interpretant** is the induced future disposition: an inference, expectation, action, or habit that changes what the system does next.

The interpretant is not merely another symbol; it is a change in the system's dispositions. Semiosis is the iterated construction and revision of causal interfaces. This is compatible with a pragmatic reading of Peirce, but a historical claim about Peirce requires exact textual scholarship and is not established by this formal analogy.

### 20.3 Relation to Markov blankets and predictive states

CIP is close to several established ideas and must not be advertised as a new discovery without comparison:
- a Markov blanket / sufficient mediator separates a system's past from its future conditional on the present;
- computational mechanics defines minimal predictive states by equivalence of pasts with identical future distributions;
- predictive-state representations and \(\epsilon\)-transducers represent state through action-conditioned future predictions;
- control theory factors input/output behavior through controllable and observable state;
- causal models express intervention-indexed response kernels.

The potentially substantive extension is the joint requirement that the interface be (i) interventionally grounded in physical causal dynamics, (ii) causally efficacious in an agent's inference/action loop, and (iii) selected as a resource-/kinematic-cost-sensitive realization with a compositional, representation-independent semantic certificate.

The central theorem target is now: **characterize the universal minimal causal interface for an interventional response kernel, then characterize exactly which physical realizations preserve it and how the cost-sensitive Master Operator selects among those realizations.**


## 21. Exact condition for the Master Operator to descend to a semantic quotient

Let \(\Pi\) be a finite partition of \(Q\), and let \(\mathcal A_\Pi\subseteq\mathbb R^Q\) be the algebra of functions constant on its blocks. Assume \(\pi(q)>0\) for every state. For action \(a\), define the weighted reverse-preimage coefficient

\[
\kappa_a(r,D)
:=
\frac{1}{\pi(r)}
\sum_{q\in D:\,\delta_a(q)=r}\pi(q),
\qquad D\in\Pi.
\]

For a block-constant function \(f=\sum_{D\in\Pi}c_D\mathbf 1_D\),

\[
(T_a^*f)(r)=\sum_{D\in\Pi}c_D\,\kappa_a(r,D).
\]

Therefore:

**Proposition (two-sided partition invariance).** For each action \(a\):
1. \(T_a\mathcal A_\Pi\subseteq\mathcal A_\Pi\) iff \(\Pi\) is a forward transition congruence.
2. \(T_a^*\mathcal A_\Pi\subseteq\mathcal A_\Pi\) iff, for every target block \(C\), every \(r,r'\in C\), and every source block \(D\),
   \[
   \kappa_a(r,D)=\kappa_a(r',D).
   \]
   This is the weighted reverse-lumpability condition for the individual action.

If both conditions hold for every action, then the block-constant algebra is invariant under all compositions, sums, and scalar multiples of \(T_a\) and \(T_a^*\). If the readout \(o\) is block-constant, this is a sufficient condition for \(W_c\), \(W_o\), and \(\mathcal L_{\mathrm{kin}}\) to preserve \(\mathcal A_\Pi\); centering and the finite-dimensional heat operator preserve it as well. Consequently \(\mathcal G_{\mathcal A}(\lambda)\) descends to an operator on the quotient.

The four-state counterexample in §19 satisfies forward congruence but violates the reverse condition, exactly explaining why \(W_c\) leaks out of the predictive quotient.

This gives a concrete research fork:

- If semantics is *forward predictive content*, then either impose reverse lumpability, project the realization operator onto the forward semantic algebra, or accept that \(\mathcal G\) also selects implementation refinements.
- If semantics is *two-sided causal identity*, define the protected response profile to include both future consequences and past/reachability contexts. The quotient is then finer and may support the full Master Operator.

Which fork is right is a substantive philosophical and empirical question. The general principle should allow both as different probe categories, not silently identify them.


## 22. Prior-art correction: the causal-interface idea has close precedents

The literature search materially narrows any novelty claim. The present synthesis is **not** the first proposal of a causal interface between past and future, nor the first account of mental representation as a causally efficacious structural model.

1. **Causal blankets.** Rosas, Mediano, Biehl, Chandaria & Polani (2020), “Causal blankets: Theory and algorithmic framework”, arXiv:2008.12568, already define a causal blanket as sensory/active dynamical sufficient statistics—“differences that make a difference”—and use it to identify perception-action loops from data. Their construction is designed to work without assuming stationarity or Markovian dynamics and proves that every bipartite stochastic process has a causal blanket. This is extremely close to the causal-interface language of §20. Any claim of novelty must identify a theorem or constraint beyond their framework, not merely rename a blanket.

2. **Forward and reverse causal states.** James, Mahoney & Crutchfield (2017), “Information trimming: Sufficient statistics, mutual information, and predictability from effective channel states”, *Physical Review E* 95, 060102(R), DOI 10.1103/PhysRevE.95.060102, prove that minimal sufficient statistics can be taken on both sides of a channel while preserving mutual information. For a stochastic process, excess entropy is the mutual information between forward-time and reverse-time causal states. Thus the two-sided past/future structure in §20 is also established prior art.

3. **Causally efficacious structural representations.** Gładziejewski and colleagues' interventionist/mechanistic account (2017) already argues that structural similarity can be causally relevant to a representation-using system and distinguishes structural representations from mere detectors. “Situated Neural Representations” (2022) argues that embodied, embedded, dynamically interacting systems can form causally efficacious, determinate, misrepresentable content. These works directly constrain G4 and the mental layer.

4. **Predictive processing and teleosemantics.** Recent work on teleosemantics, structural resemblance, and predictive processing already combines causal-probabilistic structural similarity with function/consumer-based content. Our account must explain whether its response kernel improves on these accounts, not simply restate them.

5. **Markov blankets and memory.** Parr, Da Costa, Heins, Ramstead & Friston (2021), “Memory and Markov Blankets”, *Entropy* 23(9), 1105, DOI 10.3390/e23091105, explicitly analyze how a present blanket can mediate internal/external dynamics while retaining dependence on past blanket states. This cautions against treating a static conditional-independence blanket as a complete theory of memory or semantic content.

### Revised novelty hypothesis

The possible contribution is now much narrower and more demanding:

- define an **interventionally indexed** response/blanket structure with explicit counterfactual guarantees, rather than only observational or process-statistical sufficiency;
- characterize its universal quotient/factorization and its relation to categorical causal semantics;
- derive a physically grounded realization objective that combines the exact past/future interface with the system's own kinematic cost;
- prove when the Master Operator \(\mathcal G_{\mathcal A}(\lambda)\) preserves the semantic interface (e.g. under two-sided lumpability), and characterize its leakage when it does not;
- derive architecture-dependent \(\lambda^*\) from update/energy constraints, rather than fit it;
- show how the same certified response-preserving transformations apply to physical systems, internal representations, and abstract mathematical structures.

The causal blanket / forward-reverse causal-state literature means the broad interface principle is established in important forms. The research question is whether the **interventional, cost-sensitive, compositional realization theorem** adds a precise and useful result.


## 23. Deterministic core, stochastic extension, and correctness conditions

The physical grounding claim should be formulated first in the deterministic case, then generalized.

For a deterministic controlled system,

\[
x_{t+1}=F_a(x_t),\qquad y_t=G(x_t),
\]

and an intervention word \(u=a_1\cdots a_n\), define

\[
\Phi(x)(u)=G(F_{a_n}\circ\cdots\circ F_{a_1}(x)).
\]

This is an exact response function: no probability or information-theoretic approximation is required. Two states are semantically equivalent relative to the probe language iff every admissible future intervention sequence produces the same protected readouts. The finite quotient is then a deterministic congruence.

The stochastic kernel in §§2 and 18 is the extension for noisy, partially observed, or quantum/open-system descriptions. It should not be taken to imply ontic indeterminism: probabilities may represent objective stochasticity, unresolved degrees of freedom, or an observer's epistemic uncertainty. These interpretations must be kept separate.

### 23.1 Truth, error, and misrepresentation

Let \(e:H\to Z\) be the agent's encoder and \(\widehat\Phi:Z\to\mathsf{Resp}\) its internal response model. For an actual history \(h\), the descriptive correctness condition is

\[
\widehat\Phi(e(h))=\Phi_{\mathcal S}(h)
\]

in the exact case, or \(D(\widehat\Phi(e(h)),\Phi_{\mathcal S}(h))\leq\varepsilon\) for a declared divergence / test metric in the approximate case.

A representation misrepresents when it predicts a counterfactual response that the target system does not support, even if the actual observed trajectory happens to match by luck. This provides an intervention-sensitive truth condition. A directive/action representation additionally needs a policy/effect criterion: whether using the internal state causes the system to select actions that achieve its declared objective. Descriptive truth and directive success are related but not identical.

This still does not derive which outcomes ought to matter. The protected readout set and the agent's objective must be declared; biological function, value, and normativity require additional theory. Do not hide those choices inside the response kernel.


### Bibliographic additions verified in the prior-art pass

- Rosas, F. E., Mediano, P. A. M., Biehl, M., Chandaria, S. & Polani, D. (2020), “Causal blankets: Theory and algorithmic framework”, arXiv:2008.12568. https://arxiv.org/abs/2008.12568
- James, R. G., Mahoney, J. R. & Crutchfield, J. P. (2017), “Information trimming: Sufficient statistics, mutual information, and predictability from effective channel states”, *Physical Review E* 95, 060102(R). DOI: 10.1103/PhysRevE.95.060102.
- Gładziejewski, P. & Miłkowski, M. (2017), “Structural representations: causally relevant and different from detectors”, *Biology & Philosophy* 32, 337–355. DOI: 10.1007/s10539-017-9562-6.
- Piccinini, G. (2022), “Situated Neural Representations: Solving the Problems of Content”, *Frontiers in Neurorobotics* 16, 846979. DOI: 10.3389/fnbot.2022.846979.
- Parr, T., Da Costa, L., Heins, C., Ramstead, M. J. D. & Friston, K. (2021), “Memory and Markov Blankets”, *Entropy* 23(9), 1105. DOI: 10.3390/e23091105.

**Nontriviality warning:** because causal blankets can be constructed for every bipartite stochastic process, mere existence of a blanket/interface cannot ground semantics. The relevant conditions are nontrivial predictive/interventional sufficiency, physically realizable and causally efficacious use, protected counterfactual generalization, and a principled criterion for which partition/probe category is not vacuous.


### 22.1 Exact limitations in the causal-blanket predecessor

The full Rosas et al. paper sharpens the comparison:

- Their minimal dynamical Bayesian sufficient statistic (D-BaSS) groups past trajectories by equality of conditional future distributions; the causal blanket is a *minimal reciprocal* D-BaSS, unique up to isomorphism. It decomposes into a sensory statistic and an active statistic.
- They explicitly state that computational-mechanics causal states guarantee counterfactual relationships only when the system is fully observed. Under partial observation, the states are only Granger-style maximally non-mediated predictive states.
- A causal blanket exists for every bipartite stochastic process, but its existence does not mean the process is well-described as a perception-action loop. The authors quantify mismatch using integrated information: a synergistic component \(I(X_{t+1};Y_{t+1}\mid X_t,Y_t)\) is not mediated by the blanket when the joint dynamics are non-factorisable.
- The blanket construction captures directed influences between the two parts but can leave higher-order synchronous synergy outside the interface. It is an informational boundary, not a complete causal ontology.

This is exactly why the proposed principle must not use observational sufficiency alone. It needs an explicit causal model / intervention family, a treatment of hidden variables and synergistic interactions, and a criterion for when the interface is an adequate description of the whole process rather than only a useful coarse-graining.


### 6.1 A more exact Peircean alignment

The strongest Peircean connection is not simply “object = world, sign = representation, interpretant = action”. It is the distinction among interpretants:

- the **dynamic interpretant** is the actual effect/interpretation produced on a particular occasion;
- the **final interpretant** is the general conditional disposition or habit that would govern interpretation under the relevant conditions.

The response profile \(\Phi\) is closer to the latter: it describes what the system would predict, infer, or do across a family of counterfactual probes, not merely what it happened to do on the observed trajectory. A single observed response is only one dynamic manifestation of that disposition.

Peirce's sign relation is triadic: the object determines the sign, and the sign determines an interpretant, with the interpretant itself capable of becoming a further sign. This makes the causal-interface model a possible formalization of one part of semiosis: an object constrains the response structure; a sign is a physically realized mediator; an interpretant is the induced change in inferential/action disposition. The response operator could model the conditional habit carried through the sign, while semiosis corresponds to iterated updates of that operator and its realizations.

Two cautions:
1. Peirce's final interpretant is not reducible to an empirical conditional probability or a fixed policy; it has a normative/logical and communal dimension tied to inquiry and habit formation.
2. The interpretant need not be overt motor action. It may be a further sign, inference, expectation, or acquired habit. The action channel is one observable consequence, not the whole interpretant.

Thus the proposed formalism may be Peircean in structure, but its identification with Peirce's full semiotics remains a philosophical thesis requiring textual and conceptual argument.


The formalization draft now has three files:
- `proofs/lean/CausalClosure.lean` — block-indicator/transition-congruence equivalence;
- `proofs/lean/ResponseQuotient.lean` — response quotient injectivity and factorization of any sufficient representation;
- `proofs/lean/AuditSemanticGrounding.lean` — axiom audit entry point.

All three are uncompiled drafts pending resource recovery. The expected use of classical choice in the factorization theorem is explicit in its noncomputable representative selection; no result is to be reported as machine-checked until the compile and audit succeed.


## 24. Candidate unifying law: invariant-observable-algebra semantics

The most compact mathematical candidate so far is:

> **Invariant-Observable-Algebra Principle (IOAP):** the semantic distinctions of a system, relative to a declared family of admissible transformations and protected readouts, are exactly the distinctions generated by the smallest observable algebra closed under those transformations. A representation is semantically adequate when its physically realized dynamics preserve a realization of that algebra.

This is the algebraic form of the response-profile principle. It is also the missing condition between C44's invariant linear geometry and a genuine semantic quotient.

### 24.1 Deterministic statement

Let \(X\) be a state space, \(M\) a monoid acting on \(X\) by maps \(m:X\to X\), and \(\mathcal O\subseteq\mathbb R^X\) a declared set of protected observables. For each \(m\in M\), the Koopman pullback is

\[
U_m f := f\circ m.
\]

Define the semantic observable algebra as the smallest unital pointwise subalgebra

\[
\mathcal A_{\mathcal S}
:=
\operatorname{Alg}_{\mathbb R}
\{U_m o\mid m\in M,\ o\in\mathcal O\}
\subseteq\mathbb R^X.
\]

Equivalently, \(\mathcal A_{\mathcal S}\) is the intersection of all unital subalgebras containing the protected readouts and invariant under every \(U_m\).

Define

\[
x\sim_{\mathcal A}y
\quad\Longleftrightarrow\quad
\forall f\in\mathcal A_{\mathcal S},\ f(x)=f(y).
\]

Then:

1. **Invariance:** \(\mathcal A_{\mathcal S}\) is invariant under every Koopman action by construction.
2. **Congruence:** if \(x\sim_{\mathcal A}y\), then \(m(x)\sim_{\mathcal A}m(y)\) for every \(m\in M\), because \(f\circ m\in\mathcal A_{\mathcal S}\).
3. **Readout preservation:** every protected observable and every finite continuation of it is constant on equivalence classes.
4. **Coarsest semantic quotient:** \(X/\sim_{\mathcal A}\) is the coarsest quotient on which all protected readouts after all admissible transformations remain well-defined.
5. **Finite representation theorem:** if \(X\) is finite, every unital subalgebra of \(\mathbb R^X\) is exactly the algebra of functions constant on the blocks of a unique partition. Thus the algebra and the semantic quotient determine one another.

The last point is the key correction to C44. An invariant *linear subspace* need not be a quotient. An invariant *unital observable algebra* does determine a quotient. The four-state counterexample in §19 is excluded because \(\operatorname{span}\{1,f\}\) is not closed under pointwise multiplication.

### 24.2 Stochastic statement: strong lumpability

For a controlled Markov system with kernels \(K_a(x,dx')\), define the Markov operator

\[
(P_a f)(x)=\int_X f(x')K_a(x,dx').
\]

For a finite partition \(\Pi\), the block-constant functions form a unital algebra \(\mathcal A_\Pi\). Then

\[
P_a\mathcal A_\Pi\subseteq\mathcal A_\Pi
\]

iff the partition is strongly lumpable for action \(a\):

\[
K_a(x,D)=K_a(y,D)
\quad
\text{for all }x\sim_\Pi y\text{ and all }D\in\Pi.
\]

For deterministic kernels this reduces to transition congruence. This is an exact stochastic counterpart, not an appeal to approximate prediction. For non-Markovian processes, enlarge the state to histories or a sufficient predictive state before applying the result.

### 24.3 Representation as an algebra homomorphism

Let \(r:X\to Z\) be an internal representation map. Pullback gives an algebra homomorphism

\[
r^*:\mathbb R^Z\to\mathbb R^X,
\qquad
r^*(g)=g\circ r.
\]

Its image is the algebra of observables constant on the fibres of \(r\). If \(r\) is equivariant with respect to the source and internal dynamics, this image is invariant under the source Koopman action.

The representation is adequate when its pullback algebra contains the protected semantic algebra (exactly or within a declared approximation bound). If it is minimal and exact, its fibres are precisely the semantic equivalence classes. If it retains more distinctions, it is a refinement/cover of the semantic quotient, potentially useful for robustness or cheaper implementation.

This recovers the factorization result of §17 as an algebraic statement: every sufficient representation maps onto the coarsest semantic quotient.

### 24.4 How this connects all three domains

- **Physical:** the transformation monoid is generated by physically admissible dynamics/interventions; observables are measurable physical outcomes. The invariant algebra defines which state distinctions survive every permitted causal continuation.
- **Mental:** an agent's internal representational algebra is a physically implemented, resource-bounded realization of selected environmental observables. A representation is not merely correlated with the world; its algebraic structure is used by its own inferential/action mechanism.
- **Mathematical:** algebra homomorphisms, invariant subalgebras, quotient objects, and universal properties express the same preservation law without reference to a particular coordinate system. Yoneda gives a categorical version: objects are determined by their relations to all probes in the chosen category.

The common structure is not that a brain, a rock, and a number are the same substance. It is that each can be studied as an object equipped with admissible transformations and observable relations, and semantic identity is induced by the invariant algebra of those relations.

### 24.5 Relation to the Master Operator

C44 searches for invariant *linear* subspaces of the action on observables. IOAP says that semantic content requires a stronger object: an invariant *algebra*. The Master Operator \(\mathcal G_{\mathcal A}(\lambda)\) can still be useful for discovering high-value modes, but its leading eigenspace is not automatically a semantic algebra.

A possible two-stage construction is:

1. use \(\mathcal G_{\mathcal A}(\lambda)\) to identify predictive/reachable/low-cost candidate modes;
2. close those modes under pointwise products, constants, and all admissible Koopman actions, then compute the induced quotient.

The algebra closure may increase dimension or erase the apparent compression advantage. That cost is measurable and must be included in the objective. If no small invariant algebra approximates the selected modes, then C44 may be describing useful geometry without describing semantic content.

### 24.6 Novelty boundary and open risks

Invariant subalgebras of Koopman operators, strong lumpability, finite quotient algebras, and behavioural equivalence are established mathematics. IOAP is not claimed as a new theorem in those areas. The possible contribution is their typed integration with:
- interventional rather than merely observational probes;
- a physical implementation/equivariance certificate;
- agent-specific resource and kinematic cost;
- a derivation connecting \(\mathcal G\)'s spectral modes to an approximately invariant semantic algebra;
- compositional certificates that preserve the algebra across physical, cognitive, and mathematical interpretations.

The principle remains relative to the chosen monoid and observable set. It does not decide which observables are important, supply an agent's values, or solve the hard problem of consciousness. Those are separate obligations, not hidden assumptions.


### 24.7 Prior art on invariant observable algebras

The algebraic core is established in dynamical systems and stochastic-process theory:

- Koopman operators turn nonlinear state dynamics into linear pullback operators on observables; the operator acts multiplicatively for deterministic maps. Invariant observable subspaces are widely used in nonlinear control, but a general invariant *subspace* need not reconstruct the state.
- In topological dynamics, quotient systems correspond to invariant closed subalgebras of continuous observables (with the appropriate compact/Hausdorff and continuity assumptions). This is a direct precedent for the algebra-to-quotient step.
- For finite Markov chains, strong lumpability is equivalent to invariance of the block-constant function space / kernel of the lumping map under the transition operator. This is the stochastic version of the same quotient condition.
- The finite theorem that a unital subalgebra of \(\mathbb R^X\) corresponds to a partition is a finite-dimensional commutative-algebra fact; in continuous settings it leads toward Gelfand/Stone duality, but topological closure and separation hypotheses matter.

Relevant sources:
- Mauroy, Mezić & Susuki (eds.) / Koopman-operator survey literature; see the AMS Notices overview of Koopman operators and their role in dynamical systems.
- Korda & Mezić (2018), “On convergence of extended dynamic mode decomposition to the Koopman operator”, *Journal of Nonlinear Science*; DOI 10.1007/s00332-017-9423-0 (operator approximation context).
- “Koopman Invariant Subspaces and Finite Linear Representations of Nonlinear Dynamical Systems for Control” (2016), *PLOS ONE* / PMC4769143.
- Gurvits & Ledoux, “Markov property for a function of a Markov chain: a linear algebra approach” (2013 preprint), for invariant-subspace criteria and strong lumpability.
- Geiger & Temmel (2014), “Lumpings of Markov Chains, Entropy Rate Preservation, and Higher-Order Lumpability”, *Journal of Applied Probability* 51, 1114–1132.
- Kümmerer / standard topological dynamics references on invariant subalgebras and quotient systems; a modern exposition is the thesis “Topological Dynamics via Koopman Operators” (2021).

Therefore IOAP's algebra/quotient theorem is a synthesis of established mathematics. Its possible contribution lies in the *semantic interpretation and cross-domain certificate*: protected intervention algebras, physical realization maps, agent-specific resource costs, and a theorem that the learned Master Operator yields or approximates a valid invariant algebra.


### 24.8 A further operator-theoretic gap

Even if \(\mathcal G_{\mathcal A}(\lambda)\) is self-adjoint and positive, its eigenspaces are invariant under \(\mathcal G\), not automatically under every Koopman operator \(U_m\). Nor does a \(\mathcal G\)-invariant subspace automatically close under pointwise multiplication.

The required chain is therefore:

\[
\text{high-value spectral modes}
\ \not\Rightarrow\
\text{action-invariant subspace}
\ \not\Rightarrow\
\text{invariant observable algebra}
\ \Rightarrow\
\text{semantic quotient}.
\]

Each arrow needs a theorem or a measured approximation bound. A useful diagnostic is to measure both commutators \([\mathcal G,U_a]\) and algebra-closure residuals for the selected subspace. In symmetric group cases, representation-theoretic symmetry may force commutation under additional hypotheses; in general non-invertible monoids, it must not be assumed.


## 25. Categorical core: the universal probe-response quotient

The invariant-algebra construction has a simpler categorical core that works before choosing real-valued observables.

Let a monoid \(M\) act on a set \(X\), and let \(\mathcal O\) be a family of protected probes/readouts \(o_i:X\to Y_i\). Define the universal response-profile map

\[
\Phi:X\longrightarrow\prod_{(m,i)\in M\times I}Y_i,
\qquad
\Phi(x)_{(m,i)}:=o_i(m\cdot x).
\]

Define \(x\approx y\) iff \(\Phi(x)=\Phi(y)\).

**Theorem (universal observable congruence).**
1. \(\approx\) is an equivalence relation.
2. It is an \(M\)-congruence: \(x\approx y\Rightarrow n\cdot x\approx n\cdot y\) for every \(n\in M\).
3. The quotient \(q:X\to X/{\approx}\) inherits an \(M\)-action and every protected readout \(o_i\) factors through \(q\).
4. If \(r:X\to Z\) is any equivariant representation through which every protected readout factors, then there is a unique map \(u:\operatorname{im}(r)\to X/{\approx}\) with \(q=u\circ r\). Thus every sufficient equivariant representation refines the universal observable quotient.

**Proof sketch.** Equality in a product is coordinatewise. Reflexivity, symmetry, and transitivity follow from equality. If \(x\approx y\), then for every \(m,i\), \(o_i(m\cdot(n\cdot x))=o_i((m n)\cdot x)=o_i((m n)\cdot y)=o_i(m\cdot(n\cdot y))\), so the relation is stable under the action. The quotient action is therefore well-defined. If \(r(x)=r(y)\), equivariance gives \(r(m\cdot x)=r(m\cdot y)\); since each \(o_i\) factors through \(r\), all coordinates of \(\Phi(x)\) and \(\Phi(y)\) agree. The unique factor map follows by the quotient universal property.

This is a generalized Myhill–Nerode / behavioural-equivalence theorem for a declared probe family. In the finite deterministic case, the invariant observable algebra of §24 is the algebraic dual of this quotient. In a stochastic controlled system, the transformations are Markov kernels (morphisms in the Kleisli category of the probability monad), and the response profile is kernel-valued; quotient congruence must be stated as strong lumpability or its history-dependent analogue. In a linear system, choosing coordinates turns the same map into a Hankel operator.

### 25.1 Why this may be the actual metatheoretic spine

The same construction can be instantiated at each level:

- **World:** \(X\) is a physical state/process space; \(M\) is the monoid of physically admissible interventions and evolutions; \(\mathcal O\) is the protected measurement/action readout family.
- **Mind:** \(Z\) is an internal state space; an equivariant representation map \(r\) is a physically realized compression of the world profile. Its adequacy is testable by interventionally held-out probes; its cost is determined by the agent's actual dynamics.
- **Mathematics:** \(X\) is an object in a category of structures; probes are structure-preserving maps/contexts; the response profile is a functor of relations. Yoneda is the special case where the probe profile is representable and determines the object up to isomorphism.

The physical, mental, and mathematical domains are not identified as the same kind of entity. They are related by equivariant/structure-preserving maps that preserve the same response profile. This is a precise sense in which they form a continuum of realizations of one relational structure.

### 25.2 The unresolved physical-grounding condition

The theorem only guarantees preservation *relative to the declared monoid and probes*. It does not select the physically correct monoid, guarantee that interventions are realizable, or show that the internal representation causally participates in the agent's success. Those are the independent grounding obligations G3–G5.

This is where the full theory must go beyond abstract behavioural equivalence:
- admissible transformations must correspond to physically supported interventions;
- the representation map must be implemented by a real causal mechanism;
- interventions on the internal state must have the predicted effects on the agent's inferences/actions;
- hidden variables and synergistic interactions must be included or bounded;
- the resource-sensitive realization must preserve the universal quotient, or its loss must be quantified.

The theorem is a necessary mathematical spine, not a complete metaphysics.


A third formal core module has been added:
- `proofs/lean/ObservableCongruence.lean` — monoid-action probe-response equivalence, its action congruence, maximality among stable readout-preserving relations, induced quotient action, and descended readouts.

The audit entry point now imports all three modules. It remains uncompiled pending resource recovery.


## 26. Coalgebraic formulation: final behaviour as canonical semantics

The universal probe-response quotient is a special case of **coalgebraic behavioural semantics**, which may be the most general mathematical language for the proposed metatheory.

Fix an endofunctor \(F:\mathcal C\to\mathcal C\) describing the permitted one-step observations and transitions of a system. An \(F\)-coalgebra is

\[
\gamma:X\to F X.
\]

If a final coalgebra \((\nu F,\zeta)\) exists, every coalgebra has a unique coalgebra morphism

\[
\llbracket-\rrbracket_\gamma:X\to\nu F,
\]

and this map sends each state to its canonical behaviour. Two states have the same semantics exactly when their images in \(\nu F\) agree. The kernel is the coarsest behaviour-preserving congruence; quotienting by it gives the minimal observable behaviour of the system.

For a deterministic Moore-style system with action alphabet \(A\) and readout space \(Y\), one can take \(F(X)=Y\times X^A\). Its final coalgebra is the space of all \(Y\)-valued behaviours over finite action words. This recovers the response-profile construction. Probabilistic systems use distribution-valued functors in an appropriate measurable/metric category; the probabilistic coalgebra literature studies final semantics and behavioural equivalence in both discrete and continuous settings.

### 26.1 The proposed grounding principle in coalgebraic form

1. **Physical system:** a coalgebra whose transition/observation functor is fixed by physically admissible interventions and readouts.
2. **Semantic content:** the final behaviour of a state under all those interventions, or the greatest behavioural equivalence when a final coalgebra is unavailable.
3. **Mental representation:** an internal coalgebra equipped with an exact or approximate coalgebra morphism into the physical behaviour object. The morphism must be physically implemented and causally used by the agent.
4. **Mathematical structure:** the final coalgebra and its universal property provide a coordinate-free semantic object; algebraic, categorical, and linear representations are different presentations of the same behaviour.
5. **Resource selection:** the Master Operator is a candidate mechanism for selecting a finite, low-cost internal realization of the required behaviour, subject to the invariant-algebra and commutation conditions above.

This yields a concise thesis:

> **Meaning is the invariant behaviour of a system under its physically admissible interactions; understanding is the construction of a causally effective internal realization of that behaviour.**

### 26.2 Important limitations

- Final-coalgebra semantics is already established in universal coalgebra; this is not a new mathematical discovery.
- The choice of \(F\) is decisive. If it encodes only passive observations, the semantics is only observational. To ground meaning physically, \(F\) must encode genuine intervention possibilities, protected measurements, and relevant causal dependencies.
- A final behaviour object captures what a system does under the chosen interface; it does not by itself decide what the system ought to care about, whether a state is conscious, or why a particular internal state is about a particular external object.
- A coalgebra morphism can preserve formal behaviour without being a physically realized causal mechanism. The implementation and efficacy requirements G4–G5 remain independent.
- In approximate/resource-bounded settings, exact behavioural equivalence is too strict. We need a quantitative coalgebraic distance / approximate bisimulation, and a theorem relating that distance to the predictive/action loss and the physical cost of the realization.

### 26.3 Relation among the candidate formalisms

The current synthesis is best understood as a hierarchy of presentations:

- **Coalgebraic semantics:** the general behavioural object and universal map.
- **Probe-response quotient:** the kernel congruence of the map for a specified intervention/readout family.
- **Invariant observable algebra:** the finite deterministic algebraic dual of that quotient; strong lumpability is its stochastic analogue.
- **Interventional Hankel operator:** the linear past-to-future representation of the same response structure.
- **Master Operator \(\mathcal G_{\mathcal A}(\lambda)\):** a proposed cost-sensitive selector of internal realization geometry, not the semantic object itself.

The hard theorem is to connect the last item to the first four under explicit assumptions. This is the research frontier; the other arrows are largely standard categorical, automata, and operator theory.


### Coalgebraic prior-art dossier

- Rutten, J. J. M. M. (2000), “Universal coalgebra: a theory of systems”, *Theoretical Computer Science* 249, 3–80. DOI: 10.1016/S0304-3975(00)00056-6.
- de Vink, E. P. & Rutten, J. J. M. M. (1999), “Bisimulation for probabilistic transition systems: a coalgebraic approach”, *Theoretical Computer Science* 221, 271–293. DOI: 10.1016/S0304-3975(99)00035-3.
- Sokolova, A. (2011), “Probabilistic systems coalgebraically: A survey”, *Theoretical Computer Science* 412, 5095–5110. DOI: 10.1016/j.tcs.2011.05.008.
- Bonsangue, M. M., Milius, S. & Silva, A., work on final semantics and behavioural equivalence for coalgebras; see their survey/lecture notes on coalgebraic semantics and final coalgebras.
- “The Theory of Traces for Systems with Nondeterminism, Probability, and Termination” (LMCS 2022) gives final-coalgebra semantics as the kernel of the unique semantic map and treats deterministic automata as coalgebras for \(F(X)=2\times X^A\).

These references confirm that final-coalgebra behaviour is an established universal semantics for state-based systems, including probabilistic ones. The proposed work must therefore not claim the final-coalgebra idea itself as novel.


## 27. Explicit functors for the first physical models

The abstract functor \(F\) must be fixed by the actual intervention/observation interface. Two baseline instances are:

### 27.1 Deterministic controlled dynamics

Let \(A\) be the set of physically admissible controls/interventions, \(Y\) the protected readout space, and

\[
\delta:X\times A\to X,
\qquad o:X\to Y.
\]

Define

\[
F_{\mathrm{det}}(X)=Y\times X^A,
\qquad
\gamma(x)=\bigl(o(x),\ a\mapsto\delta(x,a)\bigr).
\]

The final behaviour can be identified with the space of functions \(Y^{A^*}\). Its unique semantic map satisfies

\[
\llbracket x\rrbracket(\epsilon)=o(x),
\qquad
\llbracket x\rrbracket(a w)=
\llbracket\delta(x,a)\rrbracket(w).
\]

Thus two physical states are semantically equivalent iff every finite admissible intervention word produces the same readout. This is precisely the deterministic probe-response quotient.

### 27.2 Controlled stochastic dynamics

Let \(K_a(x,dy,dx')\) be the joint kernel for the next readout and next state under intervention \(a\). A natural coalgebra type is

\[
F_{\mathrm{stoch}}(X)=\bigl(\mathcal D(Y\times X)\bigr)^A,
\qquad
\gamma(x)(a)=K_a(x,-),
\]

where \(\mathcal D\) is an appropriate probability-distribution / probability-measure functor. The final behaviour maps each state to its family of output-stream distributions under every future action word. The correct category may be measurable spaces, Polish spaces, or a metric category; existence of the final coalgebra and measurability of the semantic map must be checked rather than assumed.

### 27.3 Why this is the right starting point

These two functors let us begin with a deterministic theorem and then generalize:
- prove the deterministic finite case exactly;
- identify the quotient and its invariant observable algebra;
- define the Hankel matrix from past histories to future intervention/output tests;
- establish the physical realization map;
- then extend to stochastic kernels and partial observation with explicit assumptions.

The deterministic case is not a claim that the world is known to be deterministic. It is the strongest clean theorem available before introducing uncertainty. If the stochastic extension is required, it should preserve the deterministic result as a special case.


## 28. Exact variational meaning of the Master Operator's heat sandwich

There is a useful exact interpretation of the Master Operator that sharpens the role of \(\lambda\). Restrict to the centered finite-dimensional space \(H_0=\mathbf 1^\perp\), and write

\[
W:=P_\perp(W_c+W_o)P_\perp,
\qquad
L:=P_\perp\mathcal L_{\mathrm{kin}}P_\perp,
\qquad
S_\lambda:=e^{-\lambda L/2}.
\]

Then \(\mathcal G_\lambda=S_\lambda W S_\lambda\). Since \(L\) is finite-dimensional and nonnegative, \(S_\lambda\) is invertible on \(H_0\). For any nonzero \(f\), set \(g=S_\lambda f\). The Rayleigh quotient gives the exact identity

\[
\lambda_{\max}(\mathcal G_\lambda)
=
\sup_{g\ne0}
\frac{\langle g,Wg\rangle}
     {\langle g,e^{\lambda L}g\rangle}.
\]

Equivalently, the top mode solves the generalized eigenproblem

\[
Wg=\mu\,e^{\lambda L}g.
\]

Thus the heat sandwich is not merely a visual smoothing heuristic: it selects the direction with maximal reachability-plus-observability energy per **exponentially weighted kinematic norm**. If \(W\) and \(L\) commute, a common eigenmode with values \((w,\ell)\) receives score \(w e^{-\lambda\ell}\), recovering the Gibbs-style C43 weighting. In the noncommutative case, the generalized eigenproblem mixes modes.

### 28.1 What this does and does not derive

- It gives an exact variational characterization of \(\mathcal G_\lambda\) in the finite model.
- It shows precisely how \(\lambda\) prices high-kinetic-cost modes: a mode of kinetic eigenvalue \(\ell\) is weighted by \(e^{-\lambda\ell}\) in the commuting case.
- It does **not** yet derive the value of \(\lambda\) from physics. The denominator is an exponential moment of \(L\), not simply the mean Dirichlet energy \(\langle g,Lg\rangle\). A physical resource interpretation must explain why this exponential norm is the correct budget/cost.
- The fixed \(\lambda_0\) failure on GRU-MLP and the architecture-dependent exploratory optima support treating \(\lambda\) as substrate-/resource-dependent. The next step is to derive \(\lambda^*(\mathcal A,B)\) from a declared physical or computational budget \(B\), not fit it after observing the desired representation.

A decisive test is whether the architecture-specific empirical optima collapse when expressed in a physically justified normalized exponential-cost budget, or whether the heat-sandwich objective itself must be revised.


### 6.2 Primary-text anchor

The alignment is not merely an analogy invented from the triad. In CP 8.315 (1909), Peirce characterizes the Final Interpretant as a conditional about how every interpreter *would* act under specified circumstances. In CP 5.491–5.492, he treats habit as the living logical interpretant and explicitly denies that habit is exclusively mental, using natural processes as examples. This is strikingly close to a naturalized counterfactual-disposition semantics.

The formal response profile is therefore a plausible mathematical analogue of Peirce's generalized conditional habit. But it is not identical to the Final Interpretant: Peirce's account includes the norm of inquiry, the ideal limit of interpretation, and self-control; an empirical response kernel alone does not supply those. The primary-text convergence is a research lead, not a proof that IOAP or coalgebraic semantics exhausts Peircean semiosis.


## 29. The metatheoretic bridge to logic: contextual equivalence and distinction admissibility

The same principle can be stated without privileging physical interventions. Replace “intervention” with **admissible context**.

Let \(X\) be a class of semantic objects, \(\mathcal C\) a category/monoid of admissible contexts or transformations, and \(\operatorname{Obs}\) a family of protected observations. Define contextual equivalence:

\[
x\equiv_{\mathcal C}y
\quad\Longleftrightarrow\quad
\forall c\in\mathcal C,\ 
\operatorname{Obs}(c[x])=\operatorname{Obs}(c[y]).
\]

The quotient by \(\equiv_{\mathcal C}\) is the coarsest abstraction that preserves every protected contextual response. A transformation is admissible when it preserves this equivalence and accounts for any protected resource/provenance structure.

This recovers the same architecture in different domains:

- **Physics:** contexts are physically realizable interventions; observations are subsequent measurements and action consequences.
- **Cognition:** contexts are questions, sensory perturbations, internal computations, and available actions; observations are inferences, expectations, and dispositions.
- **Mathematics:** contexts are morphisms, constructions, and structure-preserving maps; observations are invariant relations or truth values.
- **Logic:** contexts are inference environments / proof contexts; observations are derivability, normal forms, semantic truth, and resource usage.

In logic, two formulas or names are contextually equivalent when no admissible inference context distinguishes them. A name's inferential charge is its response profile across those contexts. A quotient that identifies two names is legitimate only if it preserves the protected inferential consequences.

### 29.1 Distinction Admissibility as the common rule

This gives a precise interpretation of the Distinction Admissibility Conjecture already used in the Synesism/Semplex work:

> Every transformation that identifies, abstracts, duplicates, or eliminates distinctions must be justified relative to the protected contexts, observables, and resources. It is admissible only when it preserves the required semantic/inferential invariants, or explicitly accounts for the loss.

The universal probe-response quotient is the maximal identification licensed by the selected contexts. The invariant observable algebra is its algebraic presentation. The final coalgebra is its universal behavioural semantics. Resource-sensitive logic adds a further constraint: a transformation must also preserve or explicitly debit the usage/provenance profile (the C-20/P091 side).

This is the strongest candidate for a single metatheoretic principle because it applies to:
- physical causal transformations;
- mental inference/action transformations;
- mathematical structure-preserving transformations;
- logical inference and resource transformations.

It does **not** imply that every domain has the same contexts, observations, or resource laws. The common law governs how distinctions may be identified; each domain supplies its own physically or formally justified context category.

### 29.2 What would make this more than contextual equivalence

Contextual equivalence and behavioural equivalence are established concepts in logic, programming-language semantics, process algebra, and coalgebra. The research contribution must therefore be the stronger package:
1. the context category is grounded in physically admissible interventions, not chosen arbitrarily;
2. the representation is a causal mediator in the system that uses it;
3. the quotient is compatible with an invariant observable algebra and resource accounting;
4. the Master Operator selects an implementation whose induced contextual equivalence matches or approximates the target's;
5. the translations between physical, cognitive, mathematical, and logical contexts compose with explicit certificates.

This may be the correct way to bind the causal-interface project to C-20/P091 and the broader Synesism metatheory.


## 30. Approximate grounding: from behavioural equivalence to a physical representation theorem

Exact behavioural equivalence is too strict for finite agents and noisy substrates. The missing physical theorem should therefore be quantitative.

Let \(\Phi_{\mathcal S}(h)\) be the physical system's interventional response profile for history \(h\), and let \(\widehat\Phi_{\mathcal A}(z)\) be the internal model's response profile for agent state \(z\). Choose a metric \(D\) on response profiles. Examples:
- deterministic finite outputs: a discounted Hamming / supremum metric over intervention words;
- continuous deterministic outputs: a discounted supremum metric using a metric on \(Y\);
- stochastic outputs: total variation, Wasserstein, or another declared divergence on future-outcome distributions.

An encoder \(e:H\to Z\) is \(\varepsilon\)-response-adequate when

\[
\sup_{h\in H_{\mathrm{protected}}}
D\bigl(\Phi_{\mathcal S}(h),\widehat\Phi_{\mathcal A}(e(h))\bigr)
\leq\varepsilon.
\]

This is a counterfactual guarantee: the bound ranges over the protected intervention family, not merely the observed training trajectories.

### 30.1 Causal efficacy is an independent condition

Response adequacy alone can be satisfied by a passive detector or a lookup table. A representation must also be causally used by the agent. A minimal operational condition is:

- intervening on the internal state (or on the physical mechanism that sets it) changes the agent's downstream inferences/actions in the way predicted by the internal transition/readout model;
- ablating or scrambling the representation degrades the protected response performance;
- the representation's causal influence is mediated through the agent's actual inference/action loop, not only correlated with its output.

This is the formal role of G4–G5 and the distinction between structural representation and detector. In practice, interventions may target neural populations, computational state, or a physically manipulable internal mechanism; the available intervention family must be stated.

### 30.2 Resource-sensitive realization objective

A candidate learning objective is

\[
\min_{e,\widehat{\gamma}}
\quad
\mathbb E_{h}\!
\left[
D\bigl(\Phi_{\mathcal S}(h),
\widehat\Phi_{\widehat{\gamma}}(e(h))\bigr)
\right]
+
\lambda\,C_{\mathcal A}(e,\widehat{\gamma})
\]

subject to:
- the internal dynamics \(\widehat\gamma\) are physically implementable on the agent's substrate;
- the representation is causally efficacious;
- protected observable algebra / resource constraints are preserved or the loss is explicitly bounded;
- the memory, energy, latency, and update budgets are respected.

The Master Operator \(\mathcal G_{\mathcal A}(\lambda)\) is a candidate spectral approximation to this optimization in finite linearized systems. The central open theorem is to derive the objective's quadratic form from the actual learning and physical update dynamics, and then prove when its optimizer is represented by \(\mathcal G\)'s top modes. The exact variational identity in §28 is a useful intermediate step, not that theorem.

### 30.3 Compositional error certificates

Suppose \(f\) and \(g\) are two approximate representation translations, with response distortions at most \(\varepsilon_f\) and \(\varepsilon_g\). If the intermediate response map is non-expansive (or has known Lipschitz constant \(L_g\)), then

\[
\varepsilon_{g\circ f}
\leq
L_g\varepsilon_f+\varepsilon_g.
\]

This gives a compositional grounding certificate across levels:
physical process \(\to\) sensory/internal state \(\to\) cognitive model \(\to\) mathematical abstraction / logical representation.

The resource certificate composes separately: memory/energy/latency costs must be summed or bounded under the actual composition model. A semantically accurate composite can still be physically unrealizable if its costs exceed the agent's budget.

### 30.4 Minimal theorem package

The next formal and experimental programme should target, in order:

1. **Exact quotient theorem:** final-behaviour kernel is the coarsest stable contextual equivalence (the deterministic core is now drafted in Lean).
2. **Algebra theorem:** finite deterministic quotient iff the protected observable algebra is invariant; stochastic analogue via strong lumpability.
3. **Realization theorem:** every exact sufficient representation factors through the quotient; every approximate representation has a measurable response distortion.
4. **Causal efficacy theorem/test:** intervention on the internal representation changes downstream action/inference as predicted, ruling out mere detection.
5. **Master-operator theorem:** under explicit commutation, reverse-lumpability, and algebra-closure assumptions, \(\mathcal G\)'s selected modes yield an invariant semantic algebra; otherwise quantify the implementation refinement/leakage.
6. **Resource derivation:** derive \(\lambda^*(\mathcal A,B)\) from substrate dynamics and budget, or falsify the heat-sandwich cost model.
7. **Composition theorem:** exact/approximate semantic certificates and physical cost bounds compose across domains.

This package is ambitious but falsifiable. It is also much more precise than claiming that all meaning is prediction or that one universal neural geometry must exist.


The probe-response formalization also now includes `representation_kernel_le_probeEq`: any equivariant internal representation through which the protected readouts factor has a kernel contained in the universal behavioural equivalence. This is the direct exact theorem connecting a sufficient representation to the canonical semantic quotient; it remains uncompiled.


## 31. Execution status and handoff (2026-11-21, evening)

| Workstream | Current state | Evidence / caveat |
|---|---|---|
| Contextual-Behavior / DAP synthesis | Research hypothesis drafted; prior-art boundary explicit | §§1–30 of this note; not a new theorem claim |
| Universal probe-response core | Three Lean modules drafted | `CausalClosure.lean`, `ResponseQuotient.lean`, `ObservableCongruence.lean`; **not yet compiled** |
| Axiom audit | Drafted | `AuditSemanticGrounding.lean`; **not yet run** |
| Master Operator variational identity | Derived analytically | §28; Gemini asked to independently verify against implementation |
| Four-state \(W_c\) counterexample | Exact rational calculation independently checked in Python | §19; Gemini asked to verify definitions and reverse-lumpability condition |
| G15 experiment | Validation complete | Gemini reports 172 pytest passes, register/status checks pass, five Lean audits pass; orbit enumerations are Python/NumPy empirical, not Lean-kernel proofs |
| G15 H15.3 general cost-4 slice | Partial | 12/1500 discovered classes completed; 6/12 drop to cost 3 at width 4, 6/12 remain at least cost 4; no complete general cost-4 census |
| Agda campaign runner | Paused after in-flight slice | Run `20261121-200357`: first five steps PASS; current Agda slice 1–25 must finish; follow-on steps paused; **do not kill WSL/Agda** |
| Ledger measurement | Added, not yet validated | New metrics in `ai-ensemble/ledger/metrics.py`; change cards `semantic-grounding-principle` and `semantic-grounding-measurement`; compile report not yet generated |
| Version control | No ChatGPT commits/pushes | Canonical Semplex and ai-ensemble edits remain uncommitted; Gemini's G15 work exists on isolated `origin/gemini/G15`, not merged to canonical |

### Immediate sequence

1. Let the in-flight Agda slice finish; do not stop it.
2. Keep the campaign runner paused after that slice.
3. Wait for free RAM to recover to at least 2 GB and CPU to remain below 75%.
4. Compile the three semantic-grounding Lean modules sequentially with Lean 4.12.0; run the axiom audit; write `artifacts/verification/semantic-grounding/verification.json`.
5. Run the ledger collector and its CI tests; confirm both new metrics are populated.
6. Incorporate Gemini's independent review of §19, §21, §28, and the full contextual-behavior theorem package.
7. Design one held-out counterfactual experiment that distinguishes semantic quotient preservation from mere spectral/representation alignment.

No further commits, pushes, merges, or PRs without maintainer approval.


The exact rational calculation is now encoded as `tests/test_semantic_grounding.py` (four tests: stationary distribution, forward congruence, exact \(W_c\) leakage, reverse-lumpability failure). The test file has been written but **not run** because the active Agda proof currently leaves insufficient free RAM.


## 32. Identity, the One, and local modules (metaphysical interpretation — conjectural)

The contextual-behaviour construction offers a precise *analogue* of the Synesism distinction between identity at the level of the One and identity at the level of differentiated existence.

- A local module chooses a restricted category \(\mathcal C_i\) of contexts/probes. It induces a local equivalence \(\equiv_i\): two states are identical relative to that module when no context in \(\mathcal C_i\) distinguishes them.
- Enlarging the context category can only refine the quotient: if \(\mathcal C_i\subseteq\mathcal C_j\), then \(\equiv_j\subseteq\equiv_i\). More admissible probes reveal more distinctions.
- A global or “One-level” behavioural profile would use the union/coherent closure of all physically admissible contexts. Equality of complete profiles is the strongest identity available to the theory.
- A local mathematical, cognitive, or physical description is a quotient/realization relative to a smaller context family. Its identities are therefore real relative to that interface without being assumed absolutely fundamental.

This resembles the identity-of-indiscernibles principle, but with a crucial restriction: indiscernibility is relative to a specified category of admissible contexts. Only if that category is complete for the target ontology can behavioural identity be promoted to ontological identity.

The “One” may therefore be modeled *formally* by a universal behaviour object / final coalgebra, while differentiated beings are its local realizations and quotients. This is a mathematical interpretation of the metaphysical thesis, not a proof that the final coalgebra is literally the One.

A possible module-gluing theorem would say: local semantic quotients can be assembled into a global realization iff their overlap translations preserve the shared contextual response algebra and resource/provenance invariants. This would connect the contextual principle to the Synesism module semantics and to the C-20 resource calculus. It remains a separate formalization target.


## 33. Fluctuation–dissipation calibration of \(\lambda\) (Gemini formalization, pending compile)

Gemini has drafted an isolated Mathlib formalization, `proofs/lean-mathlib/MasterPrincipleMech.lean`, with a useful mechanistic result. It is **not yet compiled**, because the canonical Agda slice is still consuming nearly all available RAM.

Let \(L\) have kinetic eigenvalues \(\mu_i\), and let \(w_i\geq0\) be predictive weights in that eigenbasis. Define

\[
Z(\lambda)=\sum_i w_i e^{-\lambda\mu_i},
\qquad
C(\lambda)=
\frac{\sum_i w_i\mu_i e^{-\lambda\mu_i}}
     {\sum_i w_i e^{-\lambda\mu_i}}.
\]

Then

\[
\boxed{\frac{dC}{d\lambda}
=-\operatorname{Var}_{\lambda}(\mu)\leq0.}
\]

The derivative is strictly negative whenever at least two distinct kinetic eigenvalues carry positive predictive weight. Therefore \(C(\lambda)\) is strictly decreasing and any target mean kinetic budget in its range identifies **at most one** \(\lambda\). With continuity and the endpoint limits, one obtains existence and uniqueness for budgets in the interior of the attainable range. For \(\lambda\geq0\), the range runs from \(C(0)\) down toward the smallest positively weighted kinetic eigenvalue.

This is a genuine fluctuation–dissipation identity: increasing the inverse-temperature/regularization parameter reduces the normalized kinetic energy at a rate equal to minus its weighted variance. It gives a principled calibration rule:

\[
\lambda^*(\mathcal A,B)
\text{ is the unique value satisfying }
C_{\mathcal A}(\lambda)=B,
\]

provided the architecture's spectrum and the physical/computational budget \(B\) put the target in the attainable range.

### 33.1 Noncommuting case: what the result actually controls

For general self-adjoint \(L\) and positive semidefinite \(W\), choose an eigenbasis \(e_i\) of \(L\) and set \(w_i=\langle e_i,W e_i\rangle\geq0\). The trace-level normalized cost

\[
C_{\mathrm{tr}}(\lambda)
=
\frac{\operatorname{Tr}(L e^{-\lambda L}W)}
     {\operatorname{Tr}(e^{-\lambda L}W)}
\]

has exactly the same weighted-expectation form and therefore the same variance derivative, even when \(W\) and \(L\) do not commute. This calibrates a **global trace-level budget**. It does not by itself prove that the kinetic cost of the top eigenvector of \(G_\lambda\) is monotone; that stronger claim needs commutation or additional hypotheses.

### 33.2 Architecture-specific inertia

The same Lean draft proves the exact leaky-update identity

\[
\sum_d \pi(d)
\left(
((1-\alpha)h_d+\alpha u_d)-h_d
\right)^2
=
\alpha^2
\sum_d\pi(d)(u_d-h_d)^2.
\]

Thus a leaky update scales squared per-step displacement by \(\alpha^2\). This is a concrete mechanism-specific contribution to kinematic cost. It does not yet prove the full \(\mathcal L_{\mathrm{kin}}\) spectrum scales by \(\alpha^2\), nor does it account for the accompanying latency/memory tradeoff; those require the actual recurrent dynamics.

### 33.3 Proof status and next obligation

The isolated file claims formal proofs of the derivative, nonnegative variance, strict monotonicity, uniqueness of \(\lambda\) for a target normalized Dirichlet cost, and the leaky-step identity. It also includes the exact diagonal heat-sandwich identity. These claims must be checked by compiling the Mathlib file and auditing its axioms.

The remaining physical question is now sharply stated: derive the target budget \(B\) from the actual substrate's energy, latency, memory, and update constraints. The theorem then turns that budget into a unique \(\lambda\) (under the spectral assumptions), rather than fitting \(\lambda\) after observing a preferred representation.


### 33.4 Exact target range for nonnegative \(\lambda\)

Assume \(\mu_i\geq0\), \(w_i\geq0\), and at least one positive weight. Let

\[
\mu_{\min}:=\min\{\mu_i:w_i>0\},
\qquad
C(0)=\frac{\sum_iw_i\mu_i}{\sum_iw_i}.
\]

If at least two distinct \(\mu_i\) have positive weight, then \(C\) is continuous and strictly decreasing on \([0,\infty)\), with

\[
C(0)=\frac{\sum_iw_i\mu_i}{\sum_iw_i},
\qquad
\lim_{\lambda\to\infty}C(\lambda)=\mu_{\min}.
\]

Consequently, every target budget \(B\) satisfying

\[
\mu_{\min}<B\leq C(0)
\]

has exactly one finite solution \(\lambda\geq0\) to \(C(\lambda)=B\). At \(B=C(0)\), the solution is \(\lambda=0\); the endpoint \(B=\mu_{\min}\) is reached only as \(\lambda\to\infty\), unless all positively weighted modes already share that eigenvalue (the degenerate, unidentifiable case). Budgets outside this interval cannot be achieved by nonnegative \(\lambda\).

This is the precise calibration theorem to add to the Lean file after its first compile succeeds.


### 33.5 Operator-level noncommutative fluctuation–dissipation identity

The diagonal weighted formula has a direct finite-dimensional operator version that does **not** require \(W\) and \(L\) to commute.

Assume \(L=L^*\succeq0\), \(W=W^*\succeq0\), and \(W\neq0\). Let

\[
S_\lambda=e^{-\lambda L/2},
\qquad
G_\lambda=S_\lambda W S_\lambda,
\qquad
Z_\lambda=\operatorname{Tr}(G_\lambda)>0,
\qquad
\rho_\lambda=G_\lambda/Z_\lambda.
\]

Then \(\rho_\lambda\) is a density operator and

\[
C_\lambda:=\operatorname{Tr}(L\rho_\lambda)
\]

is its mean kinetic cost. Since \(L\) commutes with \(S_\lambda\),

\[
G_\lambda'=-\tfrac12(LG_\lambda+G_\lambda L).
\]

Cyclicity of trace gives

\[
Z_\lambda'=-\operatorname{Tr}(LG_\lambda),
\qquad
\frac{d}{d\lambda}\operatorname{Tr}(LG_\lambda)
=-\operatorname{Tr}(L^2G_\lambda).
\]

The quotient rule therefore yields

\[
\boxed{
C_\lambda'
=
-\left[
\operatorname{Tr}(L^2\rho_\lambda)
-
\operatorname{Tr}(L\rho_\lambda)^2
\right]
=
-\operatorname{Var}_{\rho_\lambda}(L)
\leq0.
}
\]

This is a noncommutative fluctuation–dissipation identity for the actual heat-sandwiched Master Operator. It applies even when \(W\) and \(L\) do not commute. Strict decrease holds exactly when \(\rho_\lambda\) has support across at least two distinct eigenspaces of \(L\); because \(S_\lambda\) is invertible, this support condition is inherited from \(W\).

**Scope:** this controls the *global trace-normalized mean kinetic cost* of \(G_\lambda\). It does not imply monotonicity of the kinetic cost of the single top eigenvector of \(G_\lambda\). That stronger claim remains open without extra commutation/spectral assumptions.

This operator proof is the next formalization target for Gemini's Mathlib file. It is a stronger result than the current diagonal-weight theorem and directly addresses the noncommuting Master Operator.


**Additional status update:** Gemini has written `proofs/lean-mathlib/MasterPrincipleMech.lean` and `AuditMasterPrincipleMech.lean` in its isolated `gemini/master-principle-mech` worktree. The file contains the diagonal fluctuation–dissipation theorem, strict \(\lambda\)-uniqueness for a target normalized Dirichlet cost, and the leaky-update \(\alpha^2\) displacement identity. A `lake build MasterPrincipleMech` + audit task is currently in flight; no compile/audit result has yet been confirmed. The stronger noncommutative trace-level identity in §33.5 is a separate derivation and has not yet been added to that Lean file.


### 33.6 Multiple physical budgets (extension)

A single \(\lambda\) presumes that energy, latency, memory, and update effort have already been scalarized into one positive cost operator. A more physical model may use commuting self-adjoint cost operators \(L_1,\ldots,L_k\) and a vector of shadow prices \(\boldsymbol\lambda\):

\[
H_{\boldsymbol\lambda}=\sum_j\lambda_jL_j,
\qquad
S_{\boldsymbol\lambda}=e^{-H_{\boldsymbol\lambda}/2},
\qquad
G_{\boldsymbol\lambda}=S_{\boldsymbol\lambda}WS_{\boldsymbol\lambda},
\qquad
\rho_{\boldsymbol\lambda}=G_{\boldsymbol\lambda}/\operatorname{Tr}G_{\boldsymbol\lambda}.
\]

When the \(L_j\) commute with one another, the same trace calculation gives

\[
\frac{\partial}{\partial\lambda_j}
\operatorname{Tr}(L_i\rho_{\boldsymbol\lambda})
=
-\operatorname{Cov}_{\rho_{\boldsymbol\lambda}}(L_i,L_j).
\]

The covariance matrix is positive semidefinite, so the Jacobian of mean resource costs with respect to their prices is negative semidefinite. In principle, a vector budget can determine a vector \(\boldsymbol\lambda^*\), provided the costs are not redundant and the target lies in the attainable interior.

For noncommuting cost operators, the derivative involves a noncommutative/Kubo–Mori covariance and generally does not reduce to the simple classical covariance formula. This is an extension target, not an established result in the current Lean draft.


## 34. Full abstraction: the exact criterion for a grounded representation

The central representation criterion can now be stated in the language of full abstraction.

Let \(\equiv_{\mathcal C}\) be contextual equivalence for the declared contexts and protected observations. A representation map \(r:X\to Z\) is **fully abstract** exactly when

\[
r(x)=r(y)
\quad\Longleftrightarrow\quad
x\equiv_{\mathcal C}y.
\]

This separates two obligations:

- **Soundness / no false merges:** \(r(x)=r(y)\Rightarrow x\equiv_{\mathcal C}y\). The representation never identifies states that a protected context can distinguish.
- **Completeness / no false splits:** \(x\equiv_{\mathcal C}y\Rightarrow r(x)=r(y)\). It does not preserve distinctions that have no consequence under any protected context.

The universal quotient \(q:X\to X/{\equiv_{\mathcal C}}\) is fully abstract by construction. The Lean theorem `representation_kernel_le_probeEq` proves the soundness half for any equivariant representation through which all protected readouts factor: its kernel is contained in contextual equivalence. A minimal representation must additionally satisfy completeness; then it is isomorphic to the universal quotient, up to the relevant notion of representation equivalence.

This is the exact bridge to logic and semantics: fully abstract denotational semantics identifies two expressions iff no admissible program/proof context distinguishes them. In physics, replace program contexts with physically realizable interventions. In cognition, use the agent's accessible questions, sensory perturbations, and actions. In mathematics, use structure-preserving probes. The same criterion applies, but the context category differs by domain.

Full abstraction is established prior art in programming-language semantics. The research contribution would be to establish **physically grounded full abstraction**: the context category is justified by actual physical possibility, the representation is causally efficacious, and the realization is resource-bounded. In approximate systems, soundness/completeness become quantitative distortion and false-merge/false-split bounds.


## 35. Conditional expectation and invariant-algebra closure: the bridge from \(\mathcal G_\lambda\) to semantics

The main unresolved gap is that \(\mathcal G_\lambda\)'s spectral modes need not form an invariant observable algebra. The correct object is not merely a high-scoring subspace but a **unital algebra of observables closed under the admissible dynamics**.

For a finite state space with stationary measure \(\pi\), let \(\mathcal A\subseteq L^2(\pi)\) be the subspace of functions constant on the classes of a partition. It is also a unital pointwise subalgebra of \(L^\infty\). Let \(E_\mathcal A\) be the orthogonal projection / conditional expectation onto that algebra:

\[
(E_\mathcal A f)(x)
=
\mathbb E_\pi[f\mid B(x)].
\]

For a deterministic Koopman operator \(U_a f=f\circ\delta_a\), exact quotient dynamics require

\[
U_a(\mathcal A)\subseteq\mathcal A
\quad\Longleftrightarrow\quad
(I-E_\mathcal A)U_aE_\mathcal A=0.
\]

The operator norm

\[
\ell_a(\mathcal A)
:=
\|(I-E_\mathcal A)U_aE_\mathcal A\|
\]

is an exact leakage diagnostic: zero iff the algebra is invariant; positive values quantify how much an action sends block-constant observables outside the candidate semantic algebra. This is safer than using the full commutator \([E_\mathcal A,U_a]\), which may be nonzero even when \(\mathcal A\) is forward-invariant.

### 35.1 Algebraic closure of spectral candidates

Given a top-\(k\) spectral subspace \(V_\lambda\) of \(\mathcal G_\lambda\), form:

\[
\mathcal A_0=\operatorname{Alg}(1,V_\lambda),
\qquad
\mathcal A_{n+1}
=
\operatorname{Alg}\left(
\mathcal A_n\cup\bigcup_{a\in A}U_a(\mathcal A_n)
\right).
\]

In deterministic systems, Koopman pullbacks are algebra homomorphisms, so the fixed point is an invariant unital algebra. In stochastic systems, Markov operators are linear/positive but not multiplicative; the closure must be iterated and may expand to the full function algebra. That expansion is itself informative: the proposed spectral features may not support a compact exact semantic quotient.

The experiment should report:
- dimension growth \(\dim\mathcal A_n\) until stabilization (or a declared approximation threshold);
- leakage \(\ell_a(\mathcal A_n)\) for each action;
- held-out interventional response distortion;
- resource cost of storing/updating the closed algebra;
- false merges and false splits relative to the exact response quotient.

### 35.2 Revised role for the Master Operator

The most defensible current interpretation is:

1. \(\mathcal G_\lambda\) proposes high-value generators/features under a kinetic budget.
2. Algebraic and dynamical closure tests whether those features define a valid semantic object.
3. Conditional expectation projects observations onto a candidate quotient and quantifies leakage.
4. The accepted representation must preserve protected contextual responses and resource/provenance invariants.

A future objective may optimize directly over invariant subalgebras:

\[
\max_{\mathcal A\in\mathrm{InvSubAlg}(M)}
\quad
\mathrm{PredictiveValue}(\mathcal A)
-
\lambda\,\mathrm{PhysicalCost}(\mathcal A),
\]

or use \(\mathcal G_\lambda\) to propose generators before closure. This is a research target, not an established theorem. It is the clearest route currently identified for connecting the Master Operator to the contextual-behaviour quotient.


### 34.1 When does optimality imply completeness?

Completeness does not follow from predictive sufficiency alone. A representation can preserve all current protected responses while retaining extra latent distinctions. To derive full abstraction from optimality, additional assumptions are needed.

A sufficient finite-state condition is:
1. \(r:X\to Z\) is an exact equivariant representation and its kernel is contained in contextual equivalence (the soundness theorem).
2. The contextual quotient of \(Z\)'s image is itself realizable as an equivariant quotient representation.
3. Quotienting does not increase the declared physical resource cost (state count is the simplest case; for energy/latency this must be proved).
4. The context category already includes all future tasks/interventions whose distinctions must be retained.

If \(\ker r\) is strictly finer than contextual equivalence, the quotient of \(Z\) by the induced contextual relation is then a strictly smaller sufficient representation at no greater cost, contradicting minimality. Therefore a minimum-cost exact representation is fully abstract under these assumptions.

Without condition 3, a smaller abstract state space might require a more expensive physical code. Without condition 4, “extra” distinctions may be valuable for future learning or unanticipated tasks. In those cases, retaining them is not irrational over-refinement; it signals that the protected context category or resource model is incomplete.

Thus the correct theorem is not “optimality always implies full abstraction,” but:

> **Optimality implies full abstraction only relative to a context-complete task family and a quotient-monotone physical cost model.**


### 34.2 Prior-art anchors

The full-abstraction terminology is standard in programming-language semantics. The Stanford Encyclopedia of Philosophy's entry “Games, Full Abstraction and Full Completeness” defines full abstraction as coincidence of denotational and operational equivalence and explains how program contexts induce congruence. The PLS Lab's “Observational Equivalence” entry gives the standard all-observable-context formulation. These sources establish the formal precedent; the proposed extension is to make the contexts physically admissible interventions and to require causal efficacy/resource-bounded implementation.


**Numerical sanity check (not a proof):** a random \(3\times3\) positive-semidefinite pair with \(\|[L,W]\|_F\approx1.9563\) gave finite-difference \(C'(0.37)\approx-4.7113893618\) and \(-\operatorname{Var}_{\rho}(L)\approx-4.7113893610\), discrepancy \(8.1\times10^{-10}\). This supports the noncommuting derivation; the trace proof above remains the actual justification.


The same `Fraction` recurrence was independently re-evaluated in the analysis environment and returned the exact expected vector and zero mean. This validates the arithmetic transcription, but it is not a substitute for running the repository's pytest file on the target machine.


## 36. Historical causal grounding and reference

Contextual equivalence supplies a behavioural criterion, but it does not by itself settle reference or aboutness. Two internal states may have identical present response profiles while differing in how they were acquired, which physical object caused them, or which learning history they encode. If that history matters to the target semantics, it must be included among the protected distinctions.

A grounded representation should therefore satisfy four independent conditions:

1. **Causal acquisition:** the internal state is produced through a physical information channel causally coupled to the relevant object/system, not merely assigned by coincidence.
2. **Counterfactual calibration:** its predictions remain accurate under held-out, physically admissible interventions on that object/system.
3. **Causal use:** intervening on or ablating the representation changes the agent's downstream inferences/actions in the way its internal model predicts.
4. **Historical/provenance integrity:** the causal path by which the representation was acquired is preserved whenever it affects reference, learning, or transfer.

A fifth condition is needed for normative or goal-directed content:

5. **Success criterion:** specify which outcomes count as successful inquiry/action. Predictive accuracy, task reward, survival, truth-tracking, and social usefulness are not interchangeable objectives.

This separates three cases:
- a **detector** correlates with an object but is not used as an internal causal model;
- a **misrepresentation** is causally acquired and used, but its counterfactual response profile is wrong;
- a **grounded representation** has the relevant causal history, preserves the protected counterfactual behaviour within a declared error bound, and is causally used in the agent's control/inference loop.

The provenance condition also explains why a purely extensional quotient can be insufficient for some semantics: if two states have identical current behaviour but different histories that matter to future transfer or reference, the context category must include history-sensitive probes. This is compatible with the Distinction Admissibility Principle: provenance is protected whenever its removal would alter a required inference or future response.


## 37. Explicit limits: what this principle does not yet solve

To prevent the framework from becoming an unfalsifiable “theory of everything,” its limits must remain explicit.

1. **It does not derive the laws of physics.** The physically admissible context category and transition functor must be grounded in empirical physics; the semantic principle organizes their consequences.
2. **It does not guarantee that the chosen contexts are complete.** If an omitted intervention distinguishes two states, the quotient is only interface-relative.
3. **It does not solve consciousness or phenomenal character.** Causal efficacy and full abstraction may explain functional/structural content without explaining why experience feels as it does.
4. **It does not automatically solve reference or intentionality.** Causal acquisition, provenance, historical learning, and success conditions remain necessary; even then, a complete theory of aboutness is open.
5. **It does not derive mathematical ontology from physics.** It provides structure-preserving correspondences between mathematical models and physical/cognitive systems, not a proof that every abstract object is physically instantiated.
6. **It does not guarantee a unique optimal representation.** Multiobjective costs, nonconvexity, changing task families, and future-learning value can produce Pareto frontiers rather than a single optimum.
7. **It does not establish novelty by unification alone.** Contextual equivalence, full abstraction, coalgebraic final semantics, invariant algebras, causal representation, and resource-sensitive logic all have substantial prior art. The new contribution must be a precise theorem or reproducible result connecting them under physical grounding and resource constraints.

The ambition is a common, compositional metatheory—not a claim that one equation replaces physics, mathematics, logic, and cognitive science.


## Higher-categorical extension (2026-11-21)

The next-level categorical synthesis and its exact finite higher-gauge test are developed in `research/HIGHER_CATEGORICAL_CAUSAL_SEMANTICS_2026-11-21.md`. The key refinement is to treat the interventional Hankel object as a response profunctor and internal realizations as profunctor factorizations; the restricted Yoneda/density theorem controls higher mapping-space reconstruction, while Hennessy–Milner gives the image-finite 1-dimensional logical-type/bisimulation baseline. The companion tetrahedral (S^2), (mathbb Z_2) 2-form gauge model has a Lean-checked cochain/holonomy core and an exhaustive finite strict-2-groupoid test. This supplement is a research proposal plus verified finite mathematics, not a general physical grounding theorem.


The higher-gauge supplement now also computes the homotopy groups of the tetrahedral 2-groupoid: (pi_0=H^2(S^2;mathbb Z_2)congmathbb Z_2), (pi_1=H^1=0), and (pi_2=H^0congmathbb Z_2). Thus its 1-truncation erases a nontrivial 2-automorphism; see §18 of the supplement and the exact enumeration artifact.


The discrete higher-gauge model is now identified with the 2-truncated mapping space (mathrm{Map}(S^2,K(mathbb Z_2,2))): (pi_i=H^{2-i}(S^2;mathbb Z_2)) for (i=0,1,2). This makes the (pi_2) loss under 1-truncation directly comparable to the higher moduli-stack structure in cohesive gauge theory; see §20 of the higher-categorical supplement.
