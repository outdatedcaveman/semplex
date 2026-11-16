# Foundations: learning as nonmonotonic logic

*Status: program document, 2026-11-16. Every statement is marked **theorem** (proved here), **checked** (computed here), **known** (prior literature, read), or **conjecture**.*

## 0. What we are after, stated so it can fail

The aim is a computational theory of meaning: an account, in natural law, of how a system comes to assign meaning to what it has not seen, precise enough to prove theorems about and to test against learners.

Stated that way, the theory must say:

1. what the meaning of a new input *is*, given the evidence;
2. how a learner *computes* it;
3. why it is the *right* assignment;
4. which parts are *necessary* (derivable from minimal assumptions) and which are *contingent* (a property of one architecture or optimizer).

Two limits are stated in advance, so that the program is not mistaken for something it cannot be:

- **Rice's theorem is not overcome; it is sidestepped.** Every non-trivial semantic property of programs in a Turing-complete language is undecidable, and nothing here changes that. This theory works over finite domains with a cost ranking, where every question is decidable. The real question there is not *whether* meaning is computable but *how hard* it is. §3 makes that the target.
- **The theory covers inductive meaning-assignment: what follows from evidence.** It says nothing yet about experience, valuation or consciousness. Showing that one capacity of mind is lawful does not show that nothing else is. Any claim beyond inductive meaning-assignment would need its own evidence.

## 1. The bridge we found (Spikes 49–50 read as logic)

Spike 49 measured that trained nets output the value that *every minimum-cost circuit consistent with the data* gives, 98–99% of the time, independently of input size and sample size. Spike 50 showed that where minimum circuits disagree, training seeds disagree.

That relation, "forced by every minimal explanation of the evidence", is a classical object of logic: the **preferential (minimal-model) consequence relation** of Shoham (1987) and Kraus, Lehmann & Magidor (1990), and the **circumscription** of McCarthy (1980). Write it as

> D |~ φ  ⟺  every function of least circuit cost that agrees with the data D satisfies φ.

**Theorem 1 (rationality).** For any finite set of hypotheses with a ranking (here: functions ranked by minimum circuit cost), |~ satisfies Reflexivity, Left Logical Equivalence, Right Weakening, Cut, Cautious Monotony, Or and **Rational Monotony**. It is a *rational consequence relation* (Lehmann & Magidor 1992).

*Proof* (the steps that matter). Let min(D) be the least-cost functions agreeing with D, all of rank r.
- Cautious Monotony: if every f in min(D) satisfies a, every such f agrees with D + a, so the least rank under D + a is still r and min(D + a) = min(D). Whatever followed from D still follows.
- Cut: if min(D) ⊨ a and min(D + a) ⊨ b, then min(D + a) = min(D) by the same argument, so min(D) ⊨ b.
- Rational Monotony: if D |~ b and not D |~ ¬a, then some f in min(D) satisfies a. The least rank under D + a is still r, and min(D + a) = min(D) ∩ [a] ⊆ min(D) ⊨ b.

This is an instance of Lehmann and Magidor's representation theorem, not a new theorem; finiteness guarantees smoothness. ∎

**Checked.** Exhaustively, over all 6,561 partial labellings of the 3-input cube with atlas costs (`experiments/foundations/klm_check.py`):

| Rule | Instances | Violations |
|---|---|---|
| Cautious Monotony | 3,904 | 0 |
| Cut | 3,904 | 0 |
| Rational Monotony | 10,912 | 0 |
| Monotony (classical logic's rule) | 14,816 | 3,888 |

So the relation is **nonmonotonic** (new evidence retracts conclusions in 26% of cases) and still **rational**.

**What is new here is not Theorem 1 but the bridge.** A gradient-trained network, with no logic built in, empirically implements the minimal-model consequence relation of its own architecture's cost ranking at 98–99% (Spike 49). If that holds up, generalization *is* a form of nonmonotonic inference whose preference order is circuit cost.

## 2. What the bridge buys: four problems restated so they can be attacked

### 2.1 Implicit bias becomes a recoverable object

The Lehmann–Magidor representation theorem is constructive: from any rational consequence relation one can rebuild a **ranking** of hypotheses that generates it. So if trained nets satisfy the rationality postulates, their implicit bias stops being a vague tendency. It becomes a definite total preorder over functions that can be **elicited from behaviour alone** and compared with circuit cost, weight norm, kernel norm or description length.

- **Conjecture C24.** Trained nets satisfy Cautious Monotony and Cut at rates close to their consensus adherence (≥ 95%), and violate Monotony at a rate close to the minimal-model relation's.
- **Conjecture C24′.** The ranking elicited from net behaviour agrees with minimum circuit cost on most pairs of functions, and its disagreements identify the net's own contingent bias.

This turns "why does it generalize" into "which ranking does it implement", which is answerable exactly.

### 2.2 Training is belief revision

Rational consequence relations correspond to AGM belief revision (Gärdenfors & Makinson 1994): adding a datum to D is revising a belief state.

- **Conjecture C25.** Successive training on growing data satisfies the Darwiche–Pearl postulates for *iterated* revision, or it violates a specific one. Either answer says which kind of reasoner gradient descent is.

### 2.3 Holism and compositionality, reconciled precisely

The meaning of one input depends on *all* the evidence, and adding one datum can retract conclusions elsewhere: the consequence relation is holistic. Yet it is generated by a single ranking, and circuit cost is compositional (the cost of a composed circuit is bounded by its parts).

- **Thesis (to formalize).** *Meaning is holistic at the level of consequence and compositional at the level of its generator.* Precisely: a rational consequence relation whose ranking is a subadditive cost on a syntax with composition. The ranking is the point where syntax (circuits) and semantics (functions) meet, a Galois connection ordered by cost.

### 2.4 The complexity of meaning (the honest successor of Rice)

Deciding D |~ φ asks: for every minimum-cost circuit consistent with D, does φ hold? Two known results suggest this is hard:

- **Known.** Circumscriptive inference is Π₂ᵖ-complete (Eiter & Gottlob 1993).
- **Known.** The partial minimum circuit size problem is NP-hard (Hirahara 2022; Ilango 2020 for related forms).

- **Conjecture C26 (hardness of meaning).** For threshold circuits of unbounded size, deciding D |~ (x := v) is coNP-hard, and plausibly complete for a class at the second level of the polynomial hierarchy.

**Constraint from October 2026.** The Exponential Time Hypothesis has been refuted, independently by an internal Claude research model (Anthropic) and by an OpenAI model. Both papers have a Lean formalization and were not yet peer reviewed as of the reports read. Any hardness claim here must therefore rest on NP-hardness or the polynomial hierarchy, never on ETH or SETH; fine-grained lower bounds from those hypotheses are not available. C26 is stated accordingly.

If true, gradient descent at 98–99% adherence is an efficient approximate solver for a provably hard inference problem. Hardness also *predicts where it must fail*: instances built from the hardness reduction should break the consensus law. That makes it a falsifiable prediction, not a slogan.

### 2.5 Grounding

Here the grounding problem takes a precise form. A symbol (an input) is grounded to the extent that the evidence forces its value. Forced inputs are grounded by the data alone, and unforced ones are grounded only by the ranking, that is, by the learner's prior. Spike 49 measures exactly this split: 17–81% of inputs were forced, depending on data. Grounding then becomes a quantity with a law, not an all-or-nothing metaphysical question.

## 3. The mathematical toolkit and what each part is for

| Area | Use here | First concrete step |
|---|---|---|
| Nonmonotonic logic (KLM, Lehmann–Magidor) | The consequence relation of learning; the representation theorem to elicit implicit rankings | Spike 51 |
| Belief revision (AGM, Darwiche–Pearl) | Training on growing data as iterated revision | After Spike 51 |
| Complexity (polynomial hierarchy, MCSP) | Hardness of meaning; predicted failure families | Attempt the reduction for C26 |
| Category theory | The cost-ordered Galois connection between syntax and semantics; composition of frames (Gemini's Lean §17 already has frame morphisms) | State the adjunction and check subadditivity |
| Model theory | Minimal models and circumscription; definability of forced sets | Characterize which forced sets are definable by small formulas |
| Proof theory and Lean | Mechanize Theorem 1 and the representation theorem on finite rankings | Small; suitable for Gemini |

## 4. Next step

**Spike 51: do trained networks reason like a rational nonmonotonic logic?** At n = 4, train nets on D and on D + a, where a is a label the net itself predicted on D. Count Cautious Monotony, Cut and Rational Monotony against Monotony. Run the same tests on the kernel predictor as a control, then elicit the ranking from net behaviour and compare it with circuit cost (C24, C24′).

It is pre-registerable now, cheap, and decisive in either direction. If nets are rational in this sense, the program has its spine. If they are not, the bridge in §1 is only an approximation, and we learn exactly where it breaks.

## References (to be read in full before citation in a result; AGENTS.md rule 7)

- Kraus, Lehmann & Magidor, "Nonmonotonic reasoning, preferential models and cumulative logics", *Artificial Intelligence* 44 (1990).
- Lehmann & Magidor, "What does a conditional knowledge base entail?", *Artificial Intelligence* 55 (1992).
- Shoham, "A semantical approach to nonmonotonic logics", LICS 1987.
- McCarthy, "Circumscription — a form of non-monotonic reasoning", *Artificial Intelligence* 13 (1980).
- Gärdenfors & Makinson, "Nonmonotonic inference based on expectations", *Artificial Intelligence* 65 (1994).
- Darwiche & Pearl, "On the logic of iterated belief revision", *Artificial Intelligence* 89 (1997).
- Eiter & Gottlob, "Propositional circumscription and extended closed-world reasoning are Π₂ᵖ-complete", *Theoretical Computer Science* 114 (1993).
- Hirahara, "NP-hardness of learning programs and partial MCSP", FOCS 2022.
- Claude (Anthropic), "A 2^o(n) Time Algorithm for 3-SAT" (October 2026; Lean formalization; not yet peer reviewed): refutes ETH. Known only from press reports so far.

## 5. The infinitary model, and what higher-order logic can and cannot do about Rice

**Theorem 2 (rationality without finiteness; proved in Lean, `proofs/lean/Inference.lean`).** Let H be *any* type of hypotheses (all programs, all concepts, all functions on an infinite domain) and rank : H → ℕ any cost. The relation "D |~ φ iff every least-cost hypothesis consistent with D satisfies φ" satisfies Reflexivity, Right Weakening, Cut, Cautious Monotony and Rational Monotony, and fails Monotony. Standard axioms only; core Lean, no Mathlib.

The only property used is that ℕ is well-founded, which guarantees a least-cost hypothesis whenever any exists (the proof is `exists_pref`). This is exactly where infinitary versions can break: with a ranking that is not well-founded, as with real-valued scores that can decrease forever, Cautious Monotony can fail. So the infinitary model is: **any hypothesis space, any discrete cost**.

**Rice's theorem, precisely.** Higher-order logic does not escape it. Validity in full higher-order logic is not even arithmetically definable. Any formal system that reasons about all programs inherits undecidability, and with it incompleteness. A higher-order language changes what can be *said*, not what can be *decided*.

What it does buy us is three exact ways around Rice. Each is a theorem-level fact, not a hope:

1. **Certify instead of decide.** Rice forbids one procedure that decides a semantic property for *every* program. It does not forbid proving the property for *particular* programs. The compiler plus Lean kernel is this route: every artifact carries a checked proof of its meaning.
2. **Restrict the language.** In total typed languages or bounded circuits, many semantic properties become decidable. This is how the atlas works.
3. **Learn in the limit.** Some undecidable properties are *limit-computable*. They are not decided at any finite time, but a learner's guess converges to the truth and stays there, with no signal of having converged (Gold 1967; Putnam; Shoenfield's limit lemma: limit-computable equals Δ⁰₂).

- **Conjecture C27 (meaning in the limit).** Take rank to be description length in a fixed universal language, with hypotheses that halt on every input by construction (time-bounded, as in Levin's Kt). Then the minimal-model consequence relation of Theorems 1–2 is limit-computable but not decidable: **meaning cannot be decided, but it can be learned in the limit.** Where it stops: properties that quantify over all inputs, such as totality, are Π⁰₂ and are not limit-computable. Rice's barrier is lowered by one level of the arithmetical hierarchy, not removed.

That is the honest form of "a workaround to Rice": not a decider, but a convergence theorem with a precisely located ceiling.

## 6. Canonical forms of concepts: Platonism, family resemblance, and meaning as enactive power

The question is what the canonical form of a concept like justice or grief is. The theory gives that question three precise parts.

**6.1 Reference and sense.** A concept, taken as a verdict on situations, has an *extension*: the function from situations to verdicts. It also has *realizations*: circuits that compute that function. Their minimal realizations, taken up to the concept's own symmetry group, are its candidate canonical forms.

**Proposal.** This is Frege's distinction made exact: the *reference* is the function, and a *sense* is a symmetry orbit of minimal realizations. One reference can have several senses exactly when there is more than one orbit.

**6.2 Does a concept have a Platonic form?** In the strict sense, a concept has a unique canonical form when its minimal realization is unique up to symmetry, that is, one orbit. This is *computable*, and the census has computed it (P167, Gemini G9, re-derived in Spike 47):

| Concept complexity (minimum circuit cost) | Concepts with a unique canonical form |
|---|---|
| cost 1 (threshold concepts), 4 inputs | 15 of 15 (100%) |
| cost 3, 4 inputs | 50 of 128 (39%) |
| cost ≥ 4, 4 inputs | 0 of 79 (0%) |
| cost 3, 5 inputs (weights ≤ 3) | 3,683 of 7,253 (51%) |

In this model, **simple concepts have Platonic forms and complex ones do not.** A complex concept is a *family* of inequivalent minimal forms. That is Wittgenstein's family resemblance, given a definition and a count.

- **Conjecture C28 (no essence for complex concepts).** The fraction of concepts with a unique canonical form tends to zero as minimum cost grows. It is testable at 5 inputs, where the census can be extended to cost 4.

**6.3 What the family shares, and why learners agree.** The forms in a family disagree on some situations and agree on others. The situations where all forms agree are the forced core. Spikes 49–50 measured what learners do with this:

- they reproduce the forced core 98–99% of the time;
- they split, seed by seed, exactly where the forms split.

So the shared meaning of a complex concept is its forced core, and the rest is where individual learners, like individual people, legitimately differ.

**6.4 Meaning as enactive power.** What a concept lets an agent *do* is decide cases from partial evidence. That is its consequence relation: given these facts, which verdicts are forced. This is inferentialism (Brandom; Collinson, Eckhardt & Pym 2605.05368, read in §5 of the literature review) and Peirce's pragmatic maxim, which Gemini's Lean §19 already formalizes as determinacy equivalence.

The theory adds a sharp distinction:
- On *complete* evidence, every realization of a concept enacts the same verdicts, so the canonical form is idle.
- On *partial* evidence, different forms license different conclusions, so the form *is* the enactive power.

**Thesis.** The canonical form of a concept matters exactly in the space between what the evidence settles and what it does not. Meaning-as-enactive-power is the consequence relation on partial evidence, and its generator is the ranking of forms.

**6.5 Justice and grief.** The framework says what to compute, not yet the answer, because those concepts need data.
- **Justice** as a concept of verdicts fits directly. Take judgments of situations described by a few features, compute the minimal forms, their orbits and the forced core, and ask whether "justice" has one form or a family, and which verdicts every form agrees on. This is a concrete experiment that needs a judgment dataset.
- **Grief** is not a verdict-function. Its *dispositional* role (what it inclines an agent to do and infer) fits the same machinery; its felt quality does not, and the theory makes no claim about it.

## 7. Updated next steps

1. **Spike 51.** Do trained nets satisfy the rationality postulates, and what ranking do they implement? (§2.1)
2. **Census at cost 4, 5 inputs.** Test C28. Gemini task G15 already covers this.
3. **A concept-judgment pilot.** One verdict concept with real human judgments over a few features: its forms, orbits and forced core (§6.5).
4. **Theory.** Attempt C27 (meaning in the limit) and C26 (hardness of meaning) as paper proofs.

## 8. The grain of a concept: its symmetry group (atlas programme)

**Prior art (checked 2026-11-16).** Concept geometry in language models is now well mapped:
- **Circles for cyclic concepts** (months, weekdays) are established (Engels et al.; many replications) and *derived*. Karkada, Korchinski, Nava, Wyart & Bahri (2602.15029, structured report read) show that translation symmetry in pairwise co-occurrence statistics makes the co-occurrence matrix circulant, so representations are its Fourier modes: closed loops for periodic concepts, rippled open curves for sequences, linear decodability of coordinates.
- **Categorical concepts form simplices and hierarchies are orthogonal** (Park et al. 2406.01506, abstract only).
- **Emotion geometry mirrors human affect psychology** (Sofroniew et al. 2604.07729, Anthropic, on Claude Sonnet 4.5; replicated across 19 open models; abstracts only).
- **Not settled:** cross-model convergence (the "Platonic representation hypothesis", Huh et al. 2405.07987) is disputed on its metrics (2602.14486, 2609.27252), and the weekday "ring" is disputed (2610.37796, "spokes, not a ring").
- **Karkada et al. name the open problem themselves:** categorical and hierarchical structure lack a unifying account.

**Conjecture C29 (symmetry determines geometry).** The geometry of a family of concepts is the *representation theory of its statistical symmetry group*. The data's co-occurrence statistics are invariant under a group G acting on the family, so the co-occurrence matrix commutes with G and its eigenspaces are G's irreducible representations. Hence:

| Symmetry of the family | Group | Predicted geometry |
|---|---|---|
| cyclic (months, hours, hues) | ℤ/n | circle and higher Fourier modes (Karkada et al., derived) |
| exchangeable (unordered categories) | Sₙ | regular simplex: Gram matrix aI + b11ᵀ (matches Park et al.) |
| hierarchy (taxonomy) | wreath products Sₙ ≀ Sₘ | nested simplices in orthogonal subspaces (matches Park et al.) |
| **product of independent factors** ("Monday morning") | G₁ × G₂ | **tensor product**: Gram matrix ≈ Kronecker product of the factors' Gram matrices; for two cycles, a torus |
| reflection plus rotation (compass with mirror symmetry) | dihedral Dₙ | Dₙ's irreps: paired Fourier modes, mirror-symmetric |

Only the first row is derived. The others are predictions. The product row is the sharpest, and I found no prior test of it. It says that **compositional meaning is the tensor product of the parts' representations**: compositionality as a theorem of representation theory, not a design choice.

**The topological reading.** In homotopy type theory the circle is the delooping of ℤ (S¹ ≃ Bℤ), and a type whose loops form a group G is BG. On C29, the grain of a concept family is its type of symmetries, BG. Its observed shape is what the shape modality ʃ of cohesive HoTT extracts from a continuous representation. Concretely:
- a circle for ℤ/n;
- contractible clusters (a simplex) for Sₙ, whose delooping is not a circle;
- a torus for ℤ/n × ℤ/m.

Persistent homology of the representations measures this shape. This is where modal HoTT enters as the right language: the theory is stated as a statement about BG, and the measurement as one about its shape.

**Justice as symmetry (conjecture C30).** A fairness verdict is impartial exactly when it is invariant under permuting the persons involved, the symmetric group on agents (Rawls's veil; Harsanyi). On C29, an impartial concept's representation should factor through the quotient by that permutation group: verdict representations invariant to swapping who is who. This is testable in models by swapping names and roles in otherwise identical cases. It also gives a definition: the canonical form of justice is the verdict function modulo the group of person-permutations.

**Spike 53 (run; see `experiments/SPIKE_53_REPORT.md`, P179–P181).** Outcome: the cyclic and taxonomic rows hold in 14 models' static weights and in object cortex. The product row is refuted for lexical composition, which is additive (a direct sum). The geometry brains and models share is finer than the labelled taxonomy. The original proposal follows.

**Spike 53 (as proposed).** Test the product row on small open models runnable here (GPT-2, Pythia-410M, Qwen2.5-0.5B, SmolLM2-360M; CPU):
- phrases "<weekday> <time of day>" (7 × 4) and "<month> <year>" (12 × several);
- measure whether the family's Gram matrix is better fitted by a Kronecker product of the factor Gram matrices than by unconstrained low-rank or additive models;
- measure whether persistent homology shows two independent loops (torus) for weekday × hour.

## 9. An atlas and a periodic table of concepts (programme, 2026-11-16)

**Aim.** Two objects:
- an *atlas*: every concept on a substrate, placed in a geometry that says how it relates to every other;
- a *calculus*: an exact account of how a concept is built from elementary parts. The calculus should predict a concept's construction and recover it from a trained system, the way a program reduces to branches and loops and those to bits.

The aim also includes testing at every scale which laws govern both.

### 9.1 Plato and Aristotle are both right, and this is a theorem (not ours)

"Abstractions have causal power" and "abstractions are macrostates" are compatible. Exactly the macrostates that are **closed under the dynamics** carry causal power.

- Every abstraction is a coarse-graining, a partition of microstates (Aristotle; the thermodynamic reading).
- A coarse-graining has causal power of its own (interventions on the macro level have well-defined macro effects, and micro detail adds no predictive power) iff it is *closed*.
- For a stochastic process, closure holds iff the coarse-graining of its causal states is *strongly lumpable*. The closed coarse-grainings form a lattice.

This is proved by Rosas, Geiger, Luppi, Seth, Polani et al., "Software in the natural world" (arXiv:2402.09090; Theorems 1–3, read in the parts cited). In the deterministic case it is classical: the Myhill–Nerode congruence of a language is the coarsest closed macrostate that still decides the language, and its classes are the states of the unique minimal automaton.

So the *Platonic form* of a behaviour is its minimal closed coarse-graining: canonical, unique up to isomorphism, and causally efficacious. Its *Aristotelian* status is that it is a macrostate of some substrate. The form is substrate-independent because many micro-dynamics share it.

For a static concept (no dynamics), the closed coarse-grainings that decide a target f are the partitions refining the level sets of f. The coarsest is the minimal sufficient partition of our atlas (P003, P004). Our Boolean atlas is the static slice of this picture.

### 9.2 The periodic table: Krohn–Rhodes primes

The **Krohn–Rhodes theorem** gives the elementary parts of any finite deterministic process: every finite automaton divides a cascade (wreath product) of
- **flip-flops**: resettable memory, the "if/assign" element;
- **finite simple groups** dividing its semigroup: the reversible "loop/count" elements, of which cyclic groups of prime order are the simplest.

This is the user's analogy made exact. A program is a cascade of branches and loops, and the cascade is the construction calculus. The table's elements are the simple groups together with the flip-flop, with the classification of finite simple groups as the literal periodic table of the reversible part.

Prior use for neural networks: Liu et al., "Transformers learn shortcuts to automata" (arXiv:2210.10749, abstract read), use Krohn–Rhodes theory to explain shallow transformer solutions.

**Caveat: the table is substrate-relative.** Yang et al. (arXiv:2608.13433, abstract read) show that the length-generalizing fragment of transformers is built from unbounded counting (ℤ) and its iterated wreath products, not from flip-flops and finite simple groups. What counts as an element depends on the substrate's primitive operations, as in chemistry versus nuclear physics.

### 9.3 Conjecture C31: the economy law for concept geometry

C29 said a concept family's geometry is set by its symmetry group. Spikes 53–54 refuted its tensor-product row. Composition is mainly a direct sum with a structured residue.

Representation theory explains that refutation:
- the smallest faithful linear representation of a product G₁ × G₂ is ρ₁ ⊕ ρ₂ (dimension d₁ + d₂), not ρ₁ ⊗ ρ₂ (d₁·d₂);
- the tensor (interaction) part is needed only when the task reads out a function of the factors that does not separate.

**C31 (economy law).** A trained system represents a concept by a near-minimal faithful representation of the transformation semigroup of its closed macrostate, built cascade by cascade from its Krohn–Rhodes elements:

| Element or composition | Predicted geometry |
|---|---|
| cyclic group ℤ/n | a circle, with one Fourier mode coprime to n |
| flip-flop / reset on k values | k points in general position (a simplex) |
| non-abelian simple group, or S₃ | its smallest faithful irreducible (for S₃, the 2-dimensional standard representation: states on a circle with dihedral symmetry) |
| direct product | direct sum, small interaction |
| cascade (the second component's action depends on the first's state) | fibred geometry, carried by the interaction term |

Spikes 53–54 fit the product row, but post hoc. The prospective test is the contrast between a direct product and a cascade on the same factors.

**C32 (closure law).** A system trained only on a behaviour's outputs settles on the behaviour's Myhill–Nerode congruence. Its internal macrostates are the minimal automaton's states, and its macro-transitions are deterministic (lumpable). Learning builds the Platonic form as an Aristotelian macrostate.

### 9.4 Programme by scale

| Scale | Atlas | Construction | First test |
|---|---|---|---|
| Exact, static | Boolean functions and minimal threshold circuits (existing atlas, n ≤ 4 complete) | circuit composition | done (Spikes 01–52) |
| Exact, dynamic | small automata: minimal DFAs and their Krohn–Rhodes cascades | cascade products | **Spike 57**: trained recurrent nets on prime and composite automata (C31, C32) |
| Model lexicon | concept embeddings of open models (weights) | sparse composition from candidate primitives (Wierzbicka's semantic primes; WordNet genus + differentia) | Spike 58 (planned): reconstruct concepts from primitives, predict and recover their definitional construction |
| Brain | THINGS-fMRI concept geometry | as above | after Spike 58 |

**Laws to test across scales:**
- C31 (economy) and C32 (closure);
- a construction-cost law: learning time and data grow with the Krohn–Rhodes complexity of the target, as minimum circuit cost governs it in the static atlas;
- retroconstruction: the cascade is recoverable from a trained system's macro-dynamics.
