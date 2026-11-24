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

## 10. Primes of meaning: semantic, semiotic, algebraic. Their algebra, the syntax–semantics bridge, and Peirce's law (2026-11-16)

Results in Lean are in `proofs/lean/Closure.lean` (audited: standard axioms only; most theorems use none).

Classical results cited **from memory and not re-read** for this section are marked †. Each must be read before it supports a registered claim:
- Barrington 1989 †; Barrington–Thérien 1988 †;
- Schützenberger 1965 † and McNaughton–Papert 1971 † (star-free = aperiodic = FO[<]);
- Straubing 1994, *Finite Automata, Formal Logic, and Circuit Complexity* †;
- Griffin 1990 † (call/cc has the type of Peirce's law);
- Herzberger 1981 † and Burch 1991 † (Peirce's reduction thesis);
- Wierzbicka and Goddard † (Natural Semantic Metalanguage);
- Berardi, Coquand, Hayashi † (limit-computable mathematics).

### 10.1 Three candidate "primes", and what each is

| Candidate | What the primes are | Composition | Status |
|---|---|---|---|
| **Semantic primes** (NSM; Wierzbicka, Goddard †) | About 65 word-meanings claimed to be lexicalised in every language and undefinable: I, YOU, SOMEONE, SOMETHING, THIS, GOOD, BAD, BIG, SMALL, THINK, KNOW, WANT, FEEL, SAY, DO, HAPPEN, BEFORE, AFTER, NOT, MAYBE, CAN, BECAUSE, IF, LIKE… | Reductive paraphrase in a small universal grammar (each prime has a few valency frames). There is no formal algebra: it is a free term language over the primes. | An empirical linguistic hypothesis, contested (universality, undefinability). **Testable in our setting** (Spike 59 plan): do model embeddings of ordinary concepts lie in the sparse span of the primes' embeddings better than of matched random words? |
| **Semiotic primes** (Peirce's categories †) | Firstness, Secondness, Thirdness, i.e. monadic, dyadic and triadic relations. **Peirce's reduction thesis** (proved in algebraic form by Herzberger 1981 †, Burch 1991 †): every relation of any arity is composable from monads, dyads and triads, while triads are not composable from monads and dyads alone. | Relative product plus *teridentity* (the 3-way identity). In category theory: string diagrams in which every wire may split, i.e. special commutative Frobenius algebras (hypergraph categories). Peirce's existential graphs are such diagrams for regular logic. | A theorem, given the operations. **The sign relation is irreducibly triadic**: no composition of dyadic "stands-for" links produces interpretation. |
| **Computational primes** (Krohn–Rhodes) | The flip-flop (resettable memory, irreversible) and the finite simple groups (reversible counting). | Cascade (wreath) product. Decompositions are **not unique** (unlike integers); the invariant is the *group complexity* (minimal number of group levels interleaved with aperiodic ones). Its decidability in general is a long-open problem. | A theorem (§9.2). Spike 57: trained nets build each prime in a recognisable geometry. |

### 10.2 How they connect: logic, circuits, complexity

The algebraic theory of regular languages turns the computational primes into logic and complexity. A language's *syntactic monoid* is the transformation monoid of its minimal automaton, the Myhill–Nerode object of §9.1 (`MN_coarsest`). Then:
- **No group content (aperiodic)** ⇔ star-free ⇔ definable in first-order logic FO[<] (Schützenberger †, McNaughton–Papert †) ⇔ in AC⁰ (constant-depth circuits). Flip-flops only: logic without counting.
- **Solvable groups only** ⇔ FO plus modular-counting quantifiers ⇔ in ACC⁰ (Barrington–Thérien †). Cyclic primes ℤ/p are mod-p counting quantifiers.
- **A non-solvable simple group (A₅)** ⇔ NC¹-complete (Barrington's theorem †: width-5 branching programs over A₅ compute all of NC¹).

So the periodic table is **graded by circuit complexity and by logical expressiveness at once**: flip-flop → FO/AC⁰, cyclic → MOD/ACC⁰, non-solvable simple → NC¹. Two links follow:
- Liu et al. (2210.10749, abstract read) use exactly this split to explain which automata shallow transformers simulate.
- Yang et al. (2608.13433) show the transformer's own elements are counters over ℤ, so the table is substrate-relative.

**Logic coding (Curry–Howard).** Proofs are programs and propositions are types. The construction calculus of a concept (its cascade) is a program; its type is the concept's specification.

**HoTT.** A group G is a pointed connected 1-type BG (§8). A composition series 1 ◁ N ◁ G becomes a fibration BN → BG → B(G/N), and a cascade is an iterated dependent sum (Σ) of such fibres. **Simple groups are exactly the BG admitting no nontrivial such fibration:** the prime types. A flip-flop is *not invertible* and has no place in an ∞-groupoid. HoTT captures the reversible half of the table (symmetry, Plato); the irreversible half (memory, erasure) needs directed or modal/linear structure.

### 10.3 The thermodynamic reading (conjecture C33)

The two kinds of prime split exactly along reversibility:
- groups are bijections;
- the flip-flop's reset erases a bit (Landauer: at least kT ln 2 of heat).

**C33.** The Aristotelian (thermodynamic) side of abstraction is carried by the aperiodic, erasing primes, and the Platonic (symmetric, invariant) side by the group primes. Every abstraction is a cascade of forgetting (resets, which create macrostates by discarding distinctions, at a thermodynamic cost) and of symmetry (groups, which act on what remains without loss).

Spike 57 is consistent with this: the reset's macrostates were tight (2% within-state variance), while group states kept 20–27% micro-detail.

### 10.4 Syntax and semantics: how close is the unification?

For the finite-state fragment it is **already one object**. The syntactic congruence of a language identifies two expressions iff they are interchangeable in every context. That is Frege's and Leibniz's substitutivity and Harris's distributional hypothesis made exact. It is simultaneously:
- its *semantics*: the coarsest closed macrostate deciding meaning (`MN_coarsest`);
- its *syntax*: the syntactic monoid presented by the words;
- its *logic*: the fragment of FO/MSO that defines it (Büchi–Elgot–Trakhtenbrot †, Schützenberger †);
- its *complexity*: the circuit class above;
- its *geometry*: C31's minimal faithful representations of its primes (Spike 57).

**What is not unified:**
1. **Beyond finite state.** Natural language needs at least context-free structure. The algebraic tools (profinite monoids, Eilenberg–Reiterman varieties †) extend only partly.
2. **Approximation.** Real systems are only approximately lumpable. A metric version of closure, with error bounds, is open; Rosas et al. treat the stochastic case.
3. **Grounding.** The monoid is substrate-free. Which observations the outputs o are made of is the grounding problem (C27, meaning in the limit), not solved by algebra.
4. **Scale.** Whether a large model's concepts are the syntactic congruence of its training language is an empirical question that the lexical spikes can begin to answer.

**My assessment:** the unifying structure is identified and theorem-level for finite-state meaning. For natural language it is a research programme, not a result.

### 10.5 Peirce's law in our intuitionistic and linear setting

Lean (`Closure.lean`):
- `peirce_iff_em` (no axioms): over intuitionistic logic, Peirce's law ((P → Q) → P) → P is interderivable with excluded middle.
- `peirce_decidable` (no axioms): it holds constructively for every decidable proposition, hence for every proposition about our finite atlas.
- `not_not_peirce` (no axioms): it is never refutable (Glivenko).

**In linear logic** it fails for a second, independent reason (sequent argument, on paper). In one-sided form, ⊢ ((A⊥ ⅋ B) ⊗ A⊥), A, and the ⊗ rule must split the single A:
- giving A to the right premise leaves ⊢ A⊥ ⅋ B, i.e. ⊢ A⊥, B, which is unprovable;
- giving it to the left leaves ⊢ A⊥ alone, which is unprovable.

A proof exists only if A is first **duplicated** (contraction: ⊢ …, A, A) and then B is **discarded** (weakening: ⊢ A⊥, B, A from ⊢ A⊥, A). So Peirce's law needs a classical multiple-conclusion structure *and both* structural rules. It fails intuitionistically (single conclusion), in linear logic (neither rule), and in affine logic (no contraction).

**Computationally**, Peirce's law is the type of call/cc (Griffin †). call/cc **copies** a continuation (contraction) and later **abandons** the current one (weakening). The abandoning half is the logical form of the reset prime (§10.3): Peirce's law is the law of jumping back, paid for by copying and erasing.

**What it tells us:**
1. **Finite meaning is classical.** On a finite atlas every proposition is decidable, so Peirce's law and excluded middle hold constructively. The classical/intuitionistic gap opens only at infinity.
2. **At infinity, classical principles are realised in the limit.** Excluded middle for Σ⁰₁ statements is realised by limit-computable (learning-in-the-limit) procedures (Berardi, Coquand, Hayashi †). That is our C27 (meaning in the limit, Δ⁰₂).
3. **This is Peirce's own theory of truth.** For Peirce, truth is the opinion inquiry is fated to converge on: truth *in the limit*. **The logical law that bears his name holds exactly where his theory of truth operates.** It holds constructively on finite decidable matters, and is realised by convergent inquiry (learning in the limit) on infinite ones, without a modulus of convergence (fallibilism: you never know you have arrived).
4. **The price is resources.** Linearly, Peirce's law costs copying and erasure. Classical reasoning about the infinite is paid for by duplicating hypotheses and forgetting, as abstraction is paid for by forgetting (C33).

## 11. What Spikes 58–61 mean: stratification, invariants, synonymy, and the reversible/irreversible split (2026-11-17)

### 11.1 The shared core is one level up: stratification, not elements

Spike 61 found that 14 models' lexicons share their shape (linear CKA median 0.59) but no axes: no sparse atom and no principal direction is common to them. Spikes 58 and 60 found the same pattern for group concepts. What is invariant across networks is a **character** (a class function, basis-free), not a set of directions.

Stated exactly:
- each model fixes a basis only up to an orthogonal transformation;
- the meet over models of any basis-dependent object (an axis, an atom) is empty;
- what survives is the orbit under O(d), i.e. the Gram operator or kernel, i.e. the **representation up to isomorphism**.

So the common part of the models is not an element of the type of bases. It is an element of the quotient type, one level up: a point of the type of representations modulo isomorphism. In HoTT that type is a groupoid, and univalence identifies isomorphic structures. The shared meaning is an *identity of structure*, not a shared component.

**Relation to Synesism's Stratification Principle** (P7; negative idealism as its substantive face, `synesism-workshop/_reconciliation/canon-draft-principles.md`). That principle says the supremum of a property is not itself a thing with that property, and the totality lives at a strictly higher type.

Spike 61 is an empirical instance:
- **Stratification:** the "common basis" of all models, sought among bases, is empty;
- **Negative idealism:** the fully realised common element is the absence of an element;
- what is common exists at the next type, as an invariant.

This is an analogy with a precise core, not a proof of P7. The precise core is the representation-theoretic fact that basis-dependent quantities average to zero over the group of changes of basis, while class functions are exactly what survives.

**Correction (Spike 64).** The holonomy of model-to-model alignments is within estimation noise, and the top components glue almost perfectly. The models are rotated copies of one common frame, so the frame bundle is trivial: there is no gluing obstruction. The stratification reading above therefore applies to *raw* coordinates, not to aligned ones. Models share their shape and a recoverable common frame, each up to its own rotation.

**Conjecture C34 (invariance of shared meaning).** What independently trained systems share about a concept is exactly its invariants under their changes of representation (characters, Gram operators, homotopy types), never a component. Testable consequence: any basis-dependent claim of shared concepts (shared neurons, shared atoms, shared directions) fails across models, unless the models are trained so that their bases are tied.

### 11.2 Non-unique decomposition, synonymy and connotation

Krohn–Rhodes decompositions are not unique. For groups, the Jordan–Hölder theorem † says the multiset of composition factors (the simple "atoms") *is* unique, while the composition series (how they are stacked) is not. This is the chemist's isomerism: same atoms, different structure.

For meaning:
- **Denotation** (Frege's reference) is the machine: the minimal automaton, a canonical object.
- **Sense or connotation** is the construction: which cascade realises it.
- Two cascades of the same machine are **synonyms**: same denotation, different sense. Two cascades with the same composition factors but different arrangement are **isomers**: same atoms, different connotation.
- The invariants of a construction are the Jordan–Hölder multiset (for groups) and the group complexity (for semigroups). The free part is the order and the wiring.

Testable: independently trained networks for the same automaton realise the same minimal automaton (Spike 58, 31/31). Do they realise *different cascades*, i.e. synonymous constructions, and does the choice explain their residual differences in geometry? That requires recovering a cascade from a trained net, the retroconstruction aim.

### 11.3 HoTT and irreversibility: correcting §10.2

§10.2 said HoTT captures only the reversible half of the table. That holds for plain HoTT, whose types are ∞-groupoids. It is false for the extended frameworks, which exist precisely to formalise the irreversible half:
- **Directed (simplicial) type theory:** Riehl and Shulman, "A type theory for synthetic ∞-categories" (arXiv:1705.07442, abstract read). A directed interval and Segal and Rezk types give non-invertible arrows inside HoTT. A flip-flop's reset is an arrow without inverse there.
- **Linear HoTT:** Mitchell Riley's thesis †. It adds resource-sensitive (linear) structure to HoTT, the setting where §10.5's copying and erasure live.
- **Categorical optics:** Riley, "Categories of optics" (arXiv:1809.00738, abstract read). These are bidirectional processes (forward computation, backward update); gradient-based learning has been formalised as optics (Cruttwell, Gavranović et al. †).
- **Semicategories:** categories without identities, useful where "doing nothing" is not a process. They are less central here.
- **Baez and collaborators: compositional frameworks for open systems.** These are the most directly relevant:
  - **Open Markov processes** form a dagger compact category with a **black-boxing functor** to the steady-state input–output relation (Baez, Fong and Pollard, arXiv:1508.06448, abstract read). Black-boxing is compositional coarse-graining: the categorical form of §9.1's closure.
  - **Open Petri nets** are morphisms of a symmetric monoidal double category, with operational and reachability semantics as functors (Baez and Master, arXiv:1808.05415). Structured cospans give the general construction (Baez and Courser, arXiv:1911.04630). Open reaction networks have rate-equation dynamics as a functor (Baez and Pollard, arXiv:1704.02051). Petri nets are resource-sensitive: tokens are consumed. That is the linear-logic setting †.
  - **Entropy as functorial information loss.** Shannon entropy is the *only* measure of information loss under measure-preserving maps that is functorial, convex-linear and continuous (Baez, Fritz and Leinster, arXiv:1106.1791, abstract read).

**What this gives the programme: a quantitative Aristotle to pair with the closure Plato.**
- A coarse-graining (abstraction) π has a closure property (it is a congruence: causal power, §9.1, `Closure.lean`).
- It has a *cost*: the information it discards, H(X | π(X)), which by Baez–Fritz–Leinster is the unique functorial measure of that loss.
- Erasure has thermodynamic cost by Landauer †.
- So every abstraction carries two numbers: whether it is closed, and how much it forgets.

C33 (erasure versus symmetry) becomes measurable. Spike 57's reset forgets a lot and keeps tight macrostates; group states forget nothing and keep micro-detail.

**Conjecture C35 (abstractions trade forgetting for closure).** Among the closed coarse-grainings that decide a task, learners settle on the one of least information loss compatible with their readout. That is the Myhill–Nerode congruence, which is maximal among closed task-deciding coarse-grainings (`MN_coarsest`), so it discards the most irrelevant distinctions. The C31″ rule (keep the faithful constituents of the readout representation) is the representation-theoretic face of this.

A test: compute H(state | macrostate) along training and check that it rises to the Myhill–Nerode value (and stays there) exactly when interventions start to succeed.

### 11.4 The readout law is the geometry of a predictive state (derivation), and networks compress it

**Derivation (finite group theory, elementary).** Take a group automaton with states G, right action g ↦ g·w, and output o(g) = the left coset gH (one-hot). For w uniform on G:

  ⟨o(gw), o(hw)⟩ = 1 iff (gw)⁻¹(hw) ∈ H iff w⁻¹(g⁻¹h)w ∈ H,

and the number of such w is |H|·χ_perm(g⁻¹h). So

  E_w ⟨o(gw), o(hw)⟩ = χ_perm(g⁻¹h) / [G : H].

A state that encodes its expected future outputs (a predictive state) therefore has, once the walk mixes, Gram matrix proportional to the readout's permutation character. After centring, that is the permutation character minus the trivial one: exactly C31′.

**Exact computation for the Spike 60 automata** (`experiments/theory/predictive_kernel.py`, horizon 30, no training, `results/theory_predictive_kernel.json`). The predictive kernel's best character is χ₄ (A5_5, 0.97), χ₅ (A5_6, 0.96) and standard (S4_4, 0.97), matching the trained GRUs in all three.

For S4_6 it is the composite: permutation − 1 at 0.97, with χ₂ (0.65) above standard (0.41). The trained GRUs instead keep the standard part alone (χ₂ ≈ 0, P193).

**Reading.**
- C31′ is **derived**, not just fitted: it is the geometry of the predictive state. This is the first first-principles account in the atlas programme of *why* a learned concept has the shape it has (gap E2, "Explains").
- Trained networks **compress** the predictive state. They drop χ₂, the constituent that is not faithful (its kernel is V₄), and keep a faithful one.
- **Conjecture C31‴ (sufficiency).** A network keeps the smallest set of constituents of the predictive state that is (i) faithful, so its macrostates are the minimal automaton's (closure), and (ii) sufficient for its readout: the outputs remain threshold-separable from it.

  This predicts the A₅ results too, provided the minimal faithful 3-dimensional representations fail (ii) for those readouts while χ₄ and χ₅ pass. That is decidable by linear programming, and it is the next step.

**Update (Spike 62): C31‴ refuted prospectively** (0/12). Networks keep unfaithful constituents. The exact predictive kernel matches every fitted case of Spikes 60 and 62 except S4_6. The law is the predictive state itself, without compression, and S4_6 is an open anomaly.

**Lemma (equal energy; 2026-11-17, elementary, used to register Spike 69).** For any complex irreducible χ, the kernel matrix K_χ(g, h) = χ(g⁻¹h) has Frobenius energy Σ_{g,h} |χ(g⁻¹h)|² = |G| Σ_x |χ(x)|² = |G|², *independent of its dimension*. The constituents of χ_perm = Σ m_i χ_i are orthogonal as kernels. So the energy of constituent i in the permutation kernel is m_i²|G|². A real irreducible formed from a conjugate pair ω ⊕ ω̄ has energy 2m²|G|², because Σ_x ω(x)² = 0 when ω² ≠ 1.

Consequences:
- (i) In a permutation readout, all multiplicity-1 real constituents of perm − 1 carry *exactly equal* predictive energy. The predictive-state law alone cannot choose among them. S4_6 (std versus χ₂), S4_6c, S4_8 and A5_10 are all **ties**, and the "best character by Spearman" was a statement about pattern, not about energy. The S4_6 anomaly is therefore a question about how ties are broken.
- (ii) Multiplicity and complex type break ties. S4_12b contains 2χ₂, which carries 4× the energy, and networks chose χ₂. A₄ on pairs contains ω ⊕ ω̄ at 2× the energy of χ₃, which gives the law a unique, unfaithful prediction. Spike 69 tests this, and with it whether the S4_6 preference for the faithful constituent survives against a non-tied kernel.

## 12. Toward the continuous and higher-algebraic side: coalgebra, sheaves, harmonic analysis, higher categories, arithmetic (2026-11-17)

**Working hypothesis (user's).** Semantic space = logical space = mathematical space = phase space.

This section states, for each mathematical thread, (a) the exact known result that bears on the hypothesis, (b) what it means here, and (c) a test.

Marks used:
- † a classical result cited from memory and not re-read;
- **[S]** speculative: an analogy without a theorem behind it yet.

### 12.1 Coalgebra: semantic space is the final coalgebra, and the hypothesis is a theorem in the image-finite case

**(a) Known results.**
- A Moore machine (input alphabet Σ, outputs O) is a coalgebra X → O × X^Σ for the functor F(X) = O × X^Σ.
- Every system has a unique coalgebra morphism into the **final coalgebra** O^(Σ*), the space of all behaviours (Rutten, universal coalgebra †). Its kernel is bisimilarity, which here is Myhill–Nerode, and its image is the minimal machine.
- For image-finite labelled transition systems, two states satisfy the same Hennessy–Milner modal formulas iff they are bisimilar (Hennessy–Milner theorem †; generalised by coalgebraic modal logic, Moss, Pattinson, Schröder †).

**(b) What it means here.**
- *Phase space* (the system's state space with its dynamics) is a coalgebra.
- *Semantic space* is the final coalgebra.
- *Logical space* is the space of modal theories, which coincides with the final coalgebra up to bisimilarity in the image-finite case.

So **"semantic space = logical space = phase space modulo bisimulation" is a theorem for image-finite coalgebras.** The hypothesis is true in this precise form; its extension beyond image-finiteness is open.

Our experiments sit inside this picture:
- §11.4's predictive state is the map into the final coalgebra;
- Spike 58's closure and causal power say trained networks implement that map and factor through its image;
- C31‴ says how the image is linearised: which irreducibles of the behaviour space a network keeps.

**(c) Test.** For stochastic systems the final coalgebra is a space of measures (Giry-type functors †), so the predictive state is a probability-valued behaviour. Extend Spike 58 to probabilistic automata and check that the learned Gram matrix equals the kernel of predictive distributions.

### 12.2 Sheaves: no shared basis is a gluing obstruction; invariants are the global sections

**(a) Known results.**
- Local data on a cover glue to a global section iff the Čech cocycle condition holds. Torsors (bundles of frames) are classified by H¹ with coefficients in the structure group †.
- Contextuality in quantum mechanics is exactly the non-existence of a global section of a presheaf of local distributions (Abramsky and Brandenburger, sheaf-theoretic contextuality †).

**(b) What it means here.**
- **Tested in Spike 64 and refuted as an obstruction: the alignments glue (trivial holonomy within noise).**
- Treat each model as a local chart of semantic space: a frame for the shared shape, determined only up to O(d).
- The pairwise alignments are transition functions. A shared basis would be a global section of the frame bundle.
- Spike 61 says there is none. If alignments around triangles of models do not compose to the identity, the obstruction is a nontrivial "holonomy". What does glue globally is the invariants (Gram, characters): the global sections of the quotient sheaf. That is C34 restated sheaf-theoretically.
- Contextuality has a lexical counterpart. A word whose in-context meanings admit no global section is contextual (polysemy in the strict sense).

**(c) Tests.**
- **Spike 64**, on Spike 61's data: holonomy of orthogonal-Procrustes alignments around model triangles, against bootstrap alignment noise.
- **Later:** contextuality of word meaning across contexts in LLM activations.

### 12.3 Representation theory and harmonic analysis: the continuous version of the sufficiency law

**(a) Known results.** For a compact group K, L²(K) decomposes into irreducibles (Peter–Weyl †). On the sphere S² = SO(3)/SO(2), the irreducibles are the spherical harmonics of degree ℓ. Functions on the real projective plane RP² (unsigned axes) use only **even** ℓ.

**(b) What it means here.** The discrete law C31‴ (smallest faithful, readout-sufficient set of irreducibles) has a continuous analogue for concepts with continuous symmetry, predicted before any test:
- if the readout is a *signed direction*, the learned geometry is ℓ = 1, the 3-dimensional vector representation: the sphere;
- if the readout is an *unsigned axis* (a line, not an arrow), ℓ = 1 cannot separate antipodes as the readout requires, so the geometry is ℓ = 2, the 5-dimensional Veronese embedding of RP².

The same group, with a different readout, gives a different shape, forced by sufficiency.

**(c) Test, Spike 65.** A recurrent network receives a sequence of small 3-D rotations and outputs either the current direction of a body axis (signed) or its unsigned axis. Prediction: the hidden geometry is degree 1 for the signed readout and degree 2 (even harmonics only) for the unsigned one.

### 12.4 Higher categories and group cohomology: cascades as extensions

**(a) Known results.**
- Group extensions 1 → A → E → G → 1 with abelian A are classified by H²(G; A) †. Split extensions are semidirect products; the zero class is the direct product when the action is trivial.
- Crossed modules and 2-groups model "symmetries of symmetries" †.
- Our cascade and product (Spikes 57–58) are a split extension and a direct product of the flip-flop and ℤ/3.

**(b) What it means here.**
- §11.2's synonymy (same composition factors, different stacking) is classified by extension data. Two constructions with the same factors differ by their extension class: isomers.
- Higher-categorically, analogies between concepts are 1-morphisms, and analogies between analogies are 2-morphisms. A concept's higher structure is its 2-group of symmetries.

**(c) Test, Spike 66.** For groups with the same composition factors but different extension classes (ℤ/4 vs ℤ/2 × ℤ/2, a non-split vs a split extension; ℤ/9 vs ℤ/3 × ℤ/3; Q₈ vs D₄), the learned geometries differ as C31‴ predicts. Non-split extensions cannot be represented as sums of the factors' representations and must carry interaction (fibred) structure.

### 12.5 Arithmetic: profinite meaning, p-primary decomposition, and the field with one element

**(a) Known results.**
- Regular languages correspond to the clopen subsets of the free profinite monoid (Stone duality for regular languages; Almeida, Pin, Gehrke †).
- The profinite integers Ẑ = lim ℤ/n = ∏_p ℤ_p collect every cyclic group at once, and ℤ/n ≅ ∏ ℤ/p^k by the Chinese remainder theorem.
- Over 𝔽₁ (the "field with one element"), linear algebra is the combinatorics of finite sets: vector spaces are pointed sets, GL_n(𝔽₁) = S_n, and representations are permutation representations (Tits; Connes–Consani †).

**(b) What it means here.**
- The space of all finite-state meanings is a profinite (Stone) space; the infinitary model of §5 lives there.
- Cyclic concepts split into p-primary parts.
- **Precise link to Synesism's P0 (𝔽₁ + univalence).** By §11.4 the learned geometry starts from the readout's **permutation representation**, which is a representation over 𝔽₁. The network's state space is its base change to ℝ, compressed to the faithful, readout-sufficient constituents (C31‴). So the learned geometry of a group concept is "𝔽₁-representation ⊗ ℝ, minimised". This is an interpretation of established mathematics, not a new theorem, but it puts 𝔽₁ at the root of the observed geometry rather than as an analogy.
- **[S] Perfectoid spaces and tilting.** These relate mixed and positive characteristic via limits. A possible model for the relation between the continuous (real-valued nets) and the discrete (finite automata, profinite meaning) is a limit equivalence of that kind. No theorem is claimed; it is listed so it is not lost.

**(c) Test, Spike 67.** A counter mod n with composite n (n = 6, 12) and a readout that reveals only c mod p. C31‴ and the Chinese remainder theorem predict that the learned geometry is the p-primary circle alone. With a readout of c mod n, it is the faithful circle (k coprime to n), not the product of the prime circles.

### 12.6 Summary of where the threads already touch our data

| Thread | Already supported by our results | Next test |
|---|---|---|
| Final coalgebra | closure and causal power (P188); predictive-state derivation (§11.4) | probabilistic automata |
| Sheaves | shape shared, no basis (P191) | Spike 64: holonomy |
| Harmonic analysis | circles (k = 1), characters (P185, P192) | Spike 65: SO(3), signed vs unsigned |
| Extensions, higher structure | product vs cascade interaction (P185, P188) | Spike 66: extension classes |
| Arithmetic, 𝔽₁ | permutation (𝔽₁) representations at the root of C31‴ | Spike 67: p-primary parts |

## 13. After the prior-art reading: where a breakthrough could still be (2026-11-17)

**Re-scoping, honestly** (`charter/LITERATURE_REVIEW.md`, 2026-11-17).
- Closure for group automata, with causal interventions, is in Zhang & Li (2026).
- Coset readouts living on G/H's permutation character is Stander et al.'s lemma.
- "Features learned in order of spectral energy" is proved for two-layer networks: AGF (Kunin et al. 2025) and Marchetti et al. (2026).
- Shared representational shape is the Platonic hypothesis (Huh et al. 2024).

What is not in that literature is a theory of **which quotient and which constituent a *recurrent* learner selects**:
- with arbitrary readouts;
- with ties, which the equal-energy lemma shows are generic for permutation readouts;
- with continuous groups and covers.

That is the target from here on.

### 13.1 The A₅/SO(3) contrast and conjecture C38 (the encoding decides the cover)

A₅ ⊂ SO(3) is the icosahedral rotation group, and A₅/D₅ is its 6 axes, a finite subset of RP².
- Spike 60 (one-hot letters) built χ₅, the quotient's own representation.
- Spike 70 (ω given in ℝ³) built the double cover S².

The cover was available in the discrete case too: the 12 icosahedral vertices in χ₃, smaller than χ₅. So "smallest linear orbit covering the readout" is already refuted by Spike 60.

C38 instead says that the representation in which the inputs arrive decides it. This is the recurrent analogue of AGF's dependence on encoding statistics. It is tested in both directions in Spike 72: the discrete lift with χ₃-encoded letters, and the continuous descent with degree-2-encoded rotations.

If C38 holds, the picture becomes a **triangle of representations**:
- the input module (encoding);
- the readout module (permutation character on what is distinguished);
- the predictive kernel's energy, which weights the readout constituents by multiplicity.

The learned geometry would be the constituent that is cheapest jointly: present in the readout module, energetic in the predictive kernel, and reachable from the input module by linear maps and gated products. In representation-theoretic terms, the candidate constituents are those ρ with Hom_G(ρ, readout) ≠ 0. Their cost would be set by how ρ sits in tensor powers of the input module, since an RNN builds products of inputs. This **tensor-power reachability** is a definite, computable quantity: the least t such that ρ ⊂ (input)^{⊗t}. That is the classical "depth" of ρ relative to a faithful module (Burnside–Brauer: every irreducible appears in some tensor power of a faithful representation).

**Conjecture C39 (tensor depth).** Among the readout's constituents of comparable predictive energy, a recurrent learner leads with the one of least tensor depth relative to its input module.

For one-hot (regular) inputs every irreducible has depth 1, so energy alone decides. That matches Spikes 62 and 69 outside ties. Check against the known ties:
- **S₄ pair readout with one-hot inputs:** all depths are 1, so the tie remains; C39 is silent there. This is consistent with the generating-set dependence.
- **SO(3) with ω input:** degree 1 has depth 1 and degree 2 has depth 2. C39 predicts the cover, as observed.

C39 is post hoc on these two cases and must be registered on new encodings: for example S₄ letters encoded in std versus std⊗sign, whose tensor depths differ by constituent.

### 13.2 Frontier mathematics that bears on this (inspiration; nothing here is claimed)

- **The Burnside ring and the table of marks.** The learning trajectories of Zhang & Li pass through coset stages G/H₁ → G/H₂ → …. That is a path in the poset of transitive G-sets, and the Burnside ring A(G) is the algebra of those G-sets. A dynamical theory would be a flow on A(G) ⊗ ℝ, with marks φ_K(G/H) = |(G/H)^K| as coordinates.

  Testable consequence: stages should move down the subgroup lattice through subgroups whose permutation modules gain predictive energy fastest. Our predictive kernel restricted to each G/H gives that energy.
- **Mackey and Green functors.** The family of predictive kernels over all subgroups, with restriction and induction, is a Mackey functor. Frobenius reciprocity is what made Stander's lemma and our equal-energy lemma work. A "learned representation functor" from automata to G-modules would have to be a morphism of Mackey functors to respect quotients. That is a strong structural constraint, worth checking on the stage data.
- **Coverings, spin and the Schur multiplier.** The SO(3) cover S² → RP² is the orbit-level shadow of the Lie-group cover SU(2) → SO(3). For finite groups, the analogous lifts are central extensions, classified by the Schur multiplier H²(G; ℂ^×). A₅'s double cover is the binary icosahedral group 2I = SL(2, 5).

  Prediction in the spirit of C38: letters encoded through a *projective* representation (the 2-dimensional spin representation of 2I, given as SU(2) matrices) should make networks build a geometry of the double cover group itself. That is: track a sign that A₅ does not have, giving 120 states instead of 60. If so, the input encoding can *enlarge* the learned state space beyond the Myhill–Nerode automaton. That would be a clean, surprising failure of closure, caused by the encoding.
- **Tannaka–Krein duality.** A group is recoverable from its category of representations with the tensor product. If C39 holds, a network sees "its" group through the tensor category generated by its input module. Then what is learnable at bounded depth is a truncation of that category: a concrete, Tannakian reading of "the network's concept of the group".
- **Perfectoid and profinite threads (§12.5), revisited.** Tilting replaces a characteristic-0 object by a characteristic-p one with the same étale data. The analogue here is replacing a group concept by a quotient or a cover with the same observable (readout) data. The Myhill–Nerode quotient and the encoding-induced cover are the two directions of such a "same observations, different object" equivalence. This is metaphor only until there is a functor to write down.

## 14. Substrate-independent formulation (2026-11-18)

**Directive.** The programme seeks laws for *any* system that computes or learns: gradient-trained networks, spectral algorithms, physical reservoirs, chemical reaction networks, evolving populations, nervous systems. A result found in GRUs is a data point about one substrate. A law must either be stated for an arbitrary computing system, or be explained by a stated property of the substrate.

### 14.1 The three results, restated for an arbitrary system

**(1) Closure.** Myhill–Nerode is a theorem for *any* deterministic system with outputs. Every state space that decides the outputs refines the minimal automaton, and the minimal automaton is the coarsest closed coarse-graining. The same object appears under different names in different fields:

| Field | Name |
|---|---|
| Markov chains | lumpability (Kemeny–Snell) |
| Concurrency | bisimulation (Larsen–Skou; Buchholz: probabilistic bisimulation = ordinary lumpability) |
| Chemical kinetics | exact lumping (Wei–Kuo; Li–Rabitz) |
| Reaction networks | forward/backward bisimulation, with a coarsest-aggregation algorithm (Cardelli, Tribastone, Tschaikowski, Vandin, CONCUR 2015, PNAS 2017; Feret et al. PNAS 2009) |
| Stochastic processes | causal states / ε-machines (Shalizi–Crutchfield 2001) |
| Physics | Mori–Zwanzig projection, and renormalisation; Gordon et al. PRL 2021: relevant operators maximise predictive information |

Pairwise identifications exist. No single framework covering all of them was found in the 2026-11-18 check. A unification is a modest, not a breakthrough, claim.

*The empirical, substrate-dependent question* is which systems actually **reach** the coarsest closed coarse-graining (and discard the rest) and which carry more state. The hypothesis tested in Spike 75: adaptive substrates under a predictive objective reach it; non-adaptive substrates (fixed reservoirs: Tiňo's "Markovian architectural bias") do not even contain it.

**(2) Shape.** For any learner, the predictive kernel K is the Gram matrix of the **Hankel operator** of the system, the map from pasts to futures. For a group automaton the Hankel operator commutes with the group action. By Peter–Weyl it is therefore block-diagonal by irreducible, and its singular subspaces are isotypic components weighted by multiplicity.

So the shape law ("the leading constituent is the top multiplicity-weighted isotypic component of K") is the statement that *the learned state is the top of a Ho–Kalman realisation*. The optimal predictive-state compressors (spectral learning of weighted automata: Hsu–Kakade–Zhang 2009; Balle–Panangaden–Precup on singular value automata) do exactly this by construction. The empirical question is whether *other* learners — gradient networks, evolution and, eventually, biological circuits — converge to the same subspace.

No paper was found that measures whether trained nonlinear RNN states align with the Hankel singular subspace (2026-11-18 check). This is a genuine gap, and Spike 75 measures it across substrates.

**(3) Selection under ties: an equivariant bifurcation.** Learning from small or symmetric initial conditions is a dynamical system with the group's symmetry. Equivariant bifurcation theory (Golubitsky–Stewart–Schaeffer) is the substrate-general theory of such systems, from Rayleigh–Bénard convection and Turing morphogenesis to cortical map development. Ermentrout–Cowan, Swindale, Wolf–Geisel (Nature 1998) and Bressloff et al. 2001 all analysed Hebbian development with isotropy subgroups. It predicts:
- (a) **which irreducible destabilises first:** the one with the largest linear growth rate. In the linear regime that is Saxe et al.'s singular-value order, and for us the predictive energy.
- (b) **which orbit shape appears:** the Equivariant Branching Lemma gives branches for axial isotropy subgroups Σ, those with dim Fix(Σ) = 1. Zhang & Li's A₅ dodecahedron is exactly the orbit of a C₃-fixed (axial) vector in χ₃.
- (c) **what happens at ties:** degenerate or nearly degenerate modes are *mode interactions*. The outcome depends on cubic coefficients and initial conditions: multistability, i.e. a **lottery**. That is our P208, and He et al.'s lottery theorem for two-layer abelian composition.

Prior art for gradient learners: Marchetti–Kunin et al. (2602.03655, irreps learned one at a time by encoding power), He et al. (2606.02993, lottery), and Yang (2605.24057, pitchfork bifurcation of features, not equivariant). Arjevani–Field use isotropy subgroups for spurious minima, not along training time. **Not found:** isotropy and orbit-type predictions, with ties as mode interactions, for learners of sequential or automaton tasks. The template is the Bressloff–Cowan planform enumeration.

### 14.2 Where to draw inspiration next (frameworks whose generalisation to learning machines was not found)

- **Equivariant bifurcation and amplitude equations for learning.** Derive the normal form of training dynamics near the trivial state for a group automaton. The cubic coefficients would predict which tied constituent wins, and with what basin probability, for *any* gradient-like or Hebbian learner. This is the most direct route to a substrate-general selection law.
- **Chemical reaction networks as learners.** CRNs can compute (Soloveichik et al.) and their exact lumping is decidable (Cardelli et al.). A CRN trained to track an automaton, for example by evolutionary search over rate constants, is a chemical substrate for Spike-75-style tests. Deficiency theory (Feinberg) constrains which closures are reachable.
- **Thermodynamic cost of closure.** Discarding the unobservable part is erasure (Landauer). Recent stochastic thermodynamics gives lower bounds on the cost of computing a coarse-graining. Hypothesis: the minimal automaton minimises the dissipation needed to predict, which would make closure a thermodynamic optimum for any physical learner.
- **Morphogenesis and positional information.** Development builds a *readout-determined* geometry: gene expression patterns set by what downstream cells read, much as our geometry is set by the readout. Wolpert's positional information and Turing pattern selection are the biological analogues of the shape law and the lottery.

## 15. One object behind closure and energy: the predictive operator (2026-11-18)

### 15.1 The picture

Let H be a system's **predictive (Hankel) operator**: each past maps to its row of future outputs, over all continuations. Two of our robust results are two properties of this single object.

- **Closure = the row partition of H.** A representation works only if it identifies exactly those pasts whose Hankel rows are equal. That is the Myhill–Nerode partition, or the causal states for stochastic systems. The dynamics descend to it because the set of rows is closed under the letters (shift invariance: Fliess; Ho–Kalman).

  Correction recorded on 2026-11-18: this is the *partition by equal rows*, not the linear kernel of H. For stochastic processes the causal-state partition can be strictly finer than the Hankel rank suggests (Mess3: Hankel rank 3, infinitely many belief states).
- **Energy = the singular structure of H's row space.** Within what is kept, the geometry and the order of acquisition follow the singular values of the centred row Gram, which is our predictive kernel. By Eckart–Young, the best r-dimensional linear predictive representation is the top-r singular subspace.

  With a symmetry, H commutes with the group action. By Schur's lemma it is then block-diagonal by isotypic component, which gives:
  - the multiplicity-weighted isotypic law (P204);
  - the equal-energy ties for permutation readouts (§11.4 lemma);
  - lotteries when singular values coincide (P208).

**Mechanism in learners (hypothesis).** A component of the state receives learning signal in proportion to how much the future depends on it. Nothing the future does not pay for is built, and what is paid for is built in order of how much. A system with no adaptive state gets no such signal and builds neither (P209, P210).

The one anomaly is C36: the unobservable sign is kept in continuous axis tracking. The working conjecture is that the cost being minimised is *realisation complexity* (state dimension of a near-linear realisation: S² in ℝ³ against RP² in ℝ⁵), not information about the past. In discrete automata the two costs coincide.

### 15.2 What is already established (credit; checked 2026-11-18)

| Element | Established by | Scope |
|---|---|---|
| "Keep only what predicts the future" | Bialek, Nemenman, Tishby, *Neural Comput.* 2001 (physics/0007070): predictive information; §6 poses the past→future information bottleneck and names the minimal sufficient statistic | general |
| The IB on futures recovers causal states as the trade-off vanishes, with a hierarchy of approximations | Still, Crutchfield, Ellison, *Chaos* 2010 (0708.1580). **Caveat (their Cor. 1):** prediction alone ties causal states with all prescient rivals; minimality needs a vanishing compression pressure | general |
| Dimensions enter in canonical-correlation (Hankel-SVD) order at critical trade-offs | Chechik et al., *JMLR* 2005; Creutzig, Globerson, Tishby, *PRE* 2009 | **linear-Gaussian only**. Chung & Tiomkin 2611.08426: the unconstrained optimum is not itself a realisable Hankel system |
| Nonpredictive memory costs dissipation | Still, Sivak, Bell, Crooks, *PRL* 2012 (1203.3271) | physical |
| A biological encoder near the predictive-IB bound | Palmer, Marre, Berry, Bialek, *PNAS* 2015 (1307.0225), retina | biological |
| Truncated SVD of the past→future (Koopman/transfer) operator as the optimal linear model; networks trained to find it | Arbabi & Mezić 2017 (1611.06664, Hankel-DMD ↔ ERA/Ho–Kalman); VAMP (Wu & Noé 2020, 1707.04659); VAMPnets (Mardt et al. 2018); Lusch, Kutz, Brunton 2018 (1712.09707) | dynamical systems / molecular kinetics |
| Networks represent belief (causal) states linearly | Shai et al. 2024 (2405.15943) | transformers, HMM data |
| Gradient learners acquire irreducibles one at a time by a spectral score | Marchetti, Kunin et al. 2026 (2602.03655); Kunin et al. 2025 (AGF); Saxe et al. 2014/2019 | two-layer and linear networks |
| Predictive optima favour easy-to-predict modes, not causally relevant ones | Liu 2026 (2605.05029) | general caution |

**So the unifying picture itself (past→future operator; information bottleneck; Hankel/Koopman truncation) is not new.** It is the Bialek–Tishby–Crutchfield–Still line in physics and neuroscience and the Koopman/VAMP line in dynamical systems. Our results are an instance of it.

### 15.3 What may be new, stated modestly

1. **The representation theory of the predictive operator for symmetric systems.**
   - multiplicity-weighted isotypic energy, which beats a dimension-weighted spectral score (AGF) where they disagree (P204);
   - the equal-energy lemma that makes permutation readouts generically tied;
   - lotteries at ties.
   The block structure itself follows from Schur's lemma; the empirical consequences for learners were not found in the literature.
2. **Cross-substrate convergence.** Gradient, gradient-free (evolution strategies) and spectral learners reach the same closure and the same leading constituent, while a fixed reservoir reaches neither (P209, P210). No prior cross-substrate test was found.
3. **Interventions** (Spike 76): if width, memory noise and training time act on the learned constituents exactly as the truncation/bottleneck picture predicts, energy is a *variational principle* for nonlinear, non-Gaussian learners on discrete systems. That would go beyond the linear-Gaussian theorems.
4. **The cover anomaly** (C36, P203, P206): a case where learners keep an unobservable bit. It suggests the effective cost is realisation complexity rather than predictive information. If so, the bottleneck picture needs a geometric (representation-dimension) cost term, which the IB literature lacks.

### 15.4 A candidate general principle (to be tested, not claimed)

*A representation works, for any system and in any substrate, to the extent that it is a low-complexity realisation of the system's predictive operator:*
1. it identifies exactly the pasts with equal futures (closure);
2. it orders what it keeps by predictive energy (spectrum);
3. it breaks ties by symmetry-breaking dynamics (bifurcation);
4. its "complexity" is measured by the dimension of the linear action that realises it, which can favour covers over quotients (the cover anomaly).

Points 1–3 have broad prior support. Point 4 is our conjecture.

### 15.5 Update after Spike 76: energy is the value term, not the whole principle

Spike 76 refuted energy as a variational principle for nonlinear recurrent learners (P211):
- width limits do not keep the top-energy constituents;
- memory noise does not prune from the bottom;
- the top-energy constituent is not learned first.

Under pressure, cyclic learners choose the character on which each letter acts as the smallest rotation. Where all candidates are equally cheap to implement (S₄), energy still decides.

The working replacement is **C42**: *learned constituent = argmax [predictive value − implementation cost]*, where the cost measures how far each letter's action is from the identity in that representation. This unifies the circle pull, the lotteries (value ≈ cost) and, possibly, the cover anomaly (degree 1 is the cheaper action of small rotations). Physically it is the familiar trade-off between information value and thermodynamic or kinetic cost, with the cost carried by the *dynamics* rather than by the memory. That is the term the information-bottleneck literature lacks. C42 is post hoc and must be registered quantitatively.

## 16. Free energy, enaction, relativity and Synesism: what the data allow (2026-11-18)

### 16.1 The Free Energy Principle: checked; what it gives and what it does not

(Prior-art check, `charter/LITERATURE_REVIEW.md` 2026-11-18.)

- **Shared form.** Variational free energy is *complexity − accuracy*. Our refuted "energy only" picture (P211) was the accuracy term alone. The information bottleneck (§15) is accuracy minus an *informational* complexity. FEP's complexity is also informational: KL(q‖p) over states.
- **What FEP does not give.** The data (P211, C42/C43) require a complexity that is a cost of the **dynamics**: how far each input's action is from the identity. FEP produces a preference for slow or smooth dynamics only through a *modeller-chosen prior* on flows (generalized coordinates; Kiebel, Daunizeau & Friston 2008). Explaining our flip that way would be circular.
- **Markov blankets.** The formal critiques matter: Biehl, Pollock & Kanai 2021 (2001.06408); Aguilera et al. 2022 (2105.11203: blankets are non-generic); Bruineberg et al. 2022 ("Pearl" vs "Friston" blankets).

  The defensible statement of our closure result is: **learners recover the *causal blanket*** in the sense of Rosas, Mediano, Biehl, Chandaria & Polani 2020 (2008.12568). That is the minimal *dynamical sufficient statistic* that screens the past off from the future (a Pearl-type blanket in time), and it needs neither a steady state nor FEP's spatial ontology.

  So yes: **a concept is a blanket of a specific kind**, the minimal screening-off variable between an agent's history and its future, i.e. its causal state. FEP's spatial blanket ontology is not needed for that.
- **The patch our data suggest.** Replace (or supplement) FEP's informational complexity with a **kinematic complexity**: the cost of moving the internal state under each input.

  A principled form exists in stochastic thermodynamics. The minimum dissipation to carry out a state transformation in time τ is ∝ W₂²/τ (optimal-transport speed limits: Aurell et al. 2011; Nakazato & Ito). So the cost of an input's action is its *transport distance from the identity*, and our cost index c_ρ is the representation-theoretic version of that distance.

  The nearest existing objective is Vastola & Gershman 2026 (2610.36272): information minus an energetic cost of temporal variation, with phase transitions. Theirs is a linear filter with a stimulus-history information term. Ours is predictive value over group actions with the cost on each input's operator, tested on learners.

### 16.2 Enaction: value is agent-relative, and the cost carries the agent

The selection rule P(ρ) ∝ e_ρ^α · exp(−λ c_ρ) (C43, calibrated post hoc, tested prospectively in Spike 77) splits a concept's representation into two parts:
- **an invariant part**: the predictive operator of the target and its spectrum e_ρ, the same for every observer of the same behaviour;
- **an agent-relative part**: the cost c_ρ of realising each candidate *with that agent's dynamics*, and the exchange rate λ/α set by the agent's resources (width, noise).

Two agents facing the same target X therefore realise it differently, as the user anticipated: no two beings hold exactly the same representation, or obtain the same value from it. The difference is *lawful*, because it is fixed by their cost structure and exchange rate. This is the cybernetic and Peircean point (a representation's value lies in directing action) made quantitative.

The Spike 72–73 refutations (input encoding does not decide) constrain *where* agent-relativity lives. It is in the cost of the internal dynamics and the resource budget, not in how the input is presented.

### 16.3 Relativity: the conversion factor and the proper frame (analogy made precise where it can be)

- **The "c" (conversion factor).** In physics, Landauer's kT ln 2 converts bits into joules, and in Still et al. 2012 the inverse temperature β converts non-predictive bits into dissipated work. In our rule, **λ/α converts log-predictive value into dynamical cost**. If λ/α is universal for a class of learners (fixed by, e.g., their noise temperature), the theory is "relative on the surface, deterministic as a whole": every agent's choice follows from the invariant spectrum plus its own cost structure, through one exchange rate.

  Spike 77, H77.3, tests whether pressure *moves* the rate, as a temperature would. Calibration hint: λ/α ≈ 1.5 at default, ≈ 4.4 under heavy noise.
- **The proper frame ("view from nowhere").** By Kalman's realization theorem, all *minimal* realizations of the same predictive operator are related by a unique invertible change of state coordinates. The basis-free invariants — Hankel singular values, Markov parameters, and for symmetric systems the isotypic decomposition with its multiplicities — are the same for every observer. **The behaviour in the final coalgebra (§12.1) is the frame-independent object.** Each agent's representation is a chart on it, a truncated realization chosen by that agent's exchange rate.

  The "proper time" analogue is thus the agent-independent spectrum of the predictive operator: the *essential spectrum of a concept*, from which every agent's representation is obtained by its own cost-weighted truncation.

### 16.4 Synesism: correspondences, and terms to coin (proposals for the user)

The Synesism canon (`synesism-workshop/canon/lexicon.md`, v1.2) already has close counterparts:

| Our object | Synesism term | Fit |
|---|---|---|
| An agent's truncated realization of a target's behaviour | **Module**: a partial, perspectival reality-slice set by the entity's signature and fitness function; real, not illusion; illusion is misapplication outside its domain | close |
| The invariant behaviour shared by all modules | **module-level unitarity**: the sum of reality shared across entities equals one | close in spirit |
| The learning signal toward the minimal realization | **Tensor**: an imbalance producing a pseudoforce toward equilibrium; from the worldtree's own frame never tipped | suggestive |
| The proper (frame-independent) object | the **worldtree's own frame / Semes** | suggestive |
| A conserved budget split between value and cost | **Molarity**: a conserved measure summing to 1 | speculative |

**Things Synesism does not yet name (proposals; the user coins the terms):**
1. The **exchange rate** λ/α between predictive value and the cost of realising it: the theory's "c".
2. The **essential spectrum of a concept**: the frame-independent spectrum and multiplicities of its predictive operator, from which every module is a cost-weighted truncation.
3. The **cost of an action**: how far an input moves the internal state from where it was, as the dissipation-bounded transport distance.
4. A **lawful perspective**: the specific truncation an agent makes, determined by its own cost structure. This is the quantitative form of a Module.
5. The **causal blanket of a concept**: the minimal screening-off state between an agent's past and its future.
6. A **cover**: a representation that keeps a distinction the target does not need (C36) because it is cheaper to realize. Ontologically, this is a perspectival surplus that is not an illusion.

### 16.5 math-rsi (lisresearchgroup/math-rsi), checked

A workflow-level self-improving harness for mathematical research. Its loop is Prepare → Route → Prove → Verify → Handoff, with a per-problem wiki, Lean 4/DRAT certificates, and a `meta-evolve` skill that turns diagnosed failures into workflow changes. "RSI" is not expanded on the page, and the case-study claims are partly flagged by the authors as pending verification.

**For semplex:** adopt the meta-evolve step. Our failed post-hoc C41 (fitted 46/48, failed prospectively) is exactly the kind of failure such a step should turn into a rule. The rule: "post-hoc fits must be cross-validated across held-out automata before registration", which Spike 77's calibration follows (leave-one-automaton-out).

**For Synesism:** its Lean-certificate verification stage and per-problem wiki fit the workshop's proof-exploration protocol.

## 17. The principle connecting symmetric and irreversible concepts: invariant subspaces of the action on observables (2026-11-19)

### 17.1 The observation that forces it

- The selection rule (C43) holds for group concepts across learners, architectures and samples (P212–P214, P217).
- It fails, as generalised via predictive-kernel eigenvectors, for automata with resets and merges (P216).
- Closure (the minimal automaton, discarding the unobservable) holds for every adaptive learner on every automaton tried (P188, P200, P209).

So the invariant across both cases is closure, and the selection rule must be a special case of something stated in terms of closure.

### 17.2 The statement

Let the inputs act on observables (functions on the minimal states) by (T_a f)(q) = f(δ_a q). This is the Koopman, or pullback, action. Three facts:
1. A coarse-graining is closed (strongly lumpable, a congruence) **iff** the span of its block indicators is an invariant subspace of every T_a (Kemeny–Snell; the linear form of Myhill–Nerode).
2. For a **group**, the T_a are invertible and generate a *semisimple* algebra. Every invariant subspace is a sum of irreducible constituents with a complement, so the candidates are the isotypic blocks, and value against cost picks among them (C43).
3. For a **monoid** (non-invertible inputs: resets, merges, erasures), the algebra is in general *not* semisimple.
   - Invariant subspaces form a lattice without complements.
   - The irreducible composition factors are indexed by the regular J-classes and the irreducible representations of their maximal subgroups. This is Clifford–Munn–Ponizovskii theory: a group-theoretic core at each level, with the levels joined by non-split (radical) extensions.
   - Aperiodic monoids (all maximal subgroups trivial: the flip-flop primes of Krohn–Rhodes) have only 1-dimensional factors stacked in a filtration. Their representations are *triangular*: an ordered, layered geometry, the "erasure" geometry of C33 (Spikes 57–58).

**Conjecture C44 (closure all the way down).** For any automaton, the dominant geometry a learner builds spans an invariant subspace of the input action: *a coarser closed concept*. The candidates selected among are invariant subspaces, not eigenvectors:
- isotypic blocks for groups;
- submodules along the J-filtration for monoids.

The value-minus-cost rule chooses among them.

Krohn–Rhodes then has a representational reading:
- **group primes** contribute semisimple, rotational components (symmetry, "Plato");
- **flip-flop primes** contribute triangular, layered components (erasure, "Aristotle").

### 17.3 Synesism, for the user to name

Synesism's **partition / conjoinment** pair has a precise counterpart here.
- **Reversible inputs (groups) partition without loss.** They split the space of observables into independent, complemented irreducible blocks.
- **Irreversible inputs (merges, resets) conjoin.** They fuse states, creating non-split, layered structure that cannot be undone.

The canon's asymmetry ("there are combinatorially more ways to conjoin than to partition") matches the representation theory: monoid algebras are generically non-semisimple, group algebras never are.

The principle "a concept is a closed (invariant) piece of the action, and its dominant geometry is again closed" would be the formal content of a *synex that preserves itself under action*. A name for this self-preserving closed piece is left for the user to coin.

### 17.4 Tests

- **Spike 83** tests C44's first half: invariance of the dominant learned subspace, for groups and non-groups.
- **If it holds**, the next test is selection among submodules: value and kinetic cost computed on the composition factors of the observable module, using the J-class filtration.
