# Protocol-Frame Theory: a formal core for canonical epistemology

**Status:** v0.2, 2026-11-11. Every theorem marked **[Lean]** is machine-checked in `proofs/lean/Theory.lean` (Lean 4.12.0, core library, no `sorry`). Its axiom audit is in `proofs/lean/THEORY_CHECK_LOG.txt`: at most propext, Quot.sound and Classical.choice. Theorems marked **[paper]** have informal proofs only.

## 1. Thesis

The charter's layers keep asking the same question with different nouns:

| Layer | Question |
|---|---|
| G | When are two programs "the same"? |
| H | Which features does a task need? |
| §3.4 | Which ontologies can evidence tell apart? |
| §8.7 | Which experiment should we run next? |
| §10 | When may we answer at all? |

Seven spikes produced working instances of each. **This theory claims they are one structure.**

> **Canonical epistemology is the study of the antitone Galois connection between *observational power* (sets of protocols) and *indistinguishability* (equivalence relations on hypotheses).**
>
> - Canonical semantic objects are equivalence classes relative to a declared power.
> - Sufficiency, identifiability, experiment design and test design are the *same* hitting-set problem on one conflict hypergraph.
> - Honest abstention is exactly non-determinacy.
> - Ontological commitments beyond the determinacy frontier can be warranted only *conditionally*.

## 2. Definitions

A **protocol frame** is (H, P, obs) with obs : P → H → O.
- **H** holds hypotheses: worlds, systems, inputs, processes, causal models.
- **P** holds protocols: variables, measurements, interventions, test contexts.
- **obs p h** is what protocol p reveals about h.

An **observational power** is a set Ω ⊆ P. For a candidate set S ⊆ H and a query q : H → A:

| Notion | Definition |
|---|---|
| **Indistinguishable** | h ≡_Ω h′ ⇔ ∀p∈Ω, obs p h = obs p h′ |
| **Ω determines q on S** | ∀h,h′∈S, h ≡_Ω h′ ⇒ q h = q h′ |
| **Conflict set** of a relevant pair (q h ≠ q h′) | D(h,h′) = {p : obs p h ≠ obs p h′} |
| **Decisive protocol** | p alone separates some relevant pair, i.e. D(h,h′) = {p} |
| **Survivors** given truth h⋆ | {h ∈ S : h ≡_Ω h⋆} |

**How each spike instantiates the frame:**

| Spike | H | P | obs | q |
|---|---|---|---|---|
| 01 (sufficiency) | inputs in the care set | variables | the variable's value | the task function |
| 02/02b (inquiry) | candidate causal models | observe/do protocols | predicted distribution | causal or ontological query |
| 05 (testing) | processes | test contexts | "can deadlock with this test?" | which process it is |
| 01/03 (programs) | programs | inputs | output | the program's function |

## 3. Results

### 3.1 The connection

**Theorem 1, antitonicity [Lean `indist_antitone`, `determines_mono`].** If Ω ⊆ Ω′, then ≡_Ω′ ⊆ ≡_Ω, and whatever Ω determines, Ω′ determines.

**Theorem 2, Galois connection [Lean `galois`].** For any relation R on H: R ⊆ ≡_Ω ⇔ Ω ⊆ Blind(R), where Blind(R) is the set of protocols constant on R-related pairs.
- *Reading:* what you can observe and what you cannot distinguish determine each other.
- *Consequence:* each charter "equivalence relation indexed by protocol" (Layer F, §5.2) is the image of an observational power under this connection.
- *Spike 05:* bisimulation, completed-trace and trace equivalence are the images of three test families.

**Theorem 10, canonicity [Lean `canonical_factorization`].** A query is knowable under Ω (determined on all of H) iff it factors through the **Ω-profile** h ↦ (p ↦ obs p h).
- The profile is the canonical semantic object S_Ω = H/≡_Ω that the charter's Layer G asks for, *relative to Ω*.
- Every knowable query is a function of it, and nothing else is knowable.
- This makes precise the charter's claim that canonicity is protocol-relative (Spike 01 F1: the ROBDD is canonical only for a declared variable order, i.e. a declared Ω-encoding).

### 3.2 The duality: representation = inquiry = testing

**Theorem 3, discernibility duality [Lean `duality`].** Ω determines q on S iff Ω hits every conflict set D(h,h′) of a relevant pair.

*Contribution.* For P = variables this is the rough-set discernibility characterization of reducts (Skowron & Rauszer 1992; `charter/BIBLIOGRAPHY.md`). The frame-level statement says **the same theorem** governs:
- choosing features (what to *look at*),
- choosing experiments (what to *do*),
- choosing test suites (how to *probe*).

So Spike 01's sufficiency machinery and Spike 02's experiment selection are one algorithm on one hypergraph. We are not aware of this three-way identification in the literature; it should be checked against the experimental-design and testing-equivalence literatures before any formal claim of priority.

**Theorem 5, realizability [Lean `realizable`].** Every family of sets is the conflict hypergraph of some frame and query. Choosing a minimum determining set, whether of features, experiments or tests, is therefore **exactly** the minimum hitting-set problem in full generality. It inherits that problem's NP-hardness (Karp; *to verify*) and its approximation theory. No method can do better in general: any efficient general planner would solve hitting set.

### 3.3 Existence and uniqueness of minimal representations

**Theorem 4, least determining set [Lean `least_iff`, `decisive_necessary`].** A least determining set exists iff the decisive protocols determine q, and then it *equals* the set of decisive protocols. Every determining set contains every decisive protocol.
- *Precedent:* in rough-set theory, "the reduct is unique iff the core is a reduct", with the core given by the singleton entries of the discernibility matrix. Theorem 4 generalizes this to arbitrary frames, answer types and infinite protocol sets.
- *Reading:* a canonical minimal representation, experiment plan or test suite exists exactly when every relevant distinction can be made by some individually indispensable protocol.

**Theorem 11, finitary uniqueness [Lean `finitary_least`].** If q depends on only finitely many coordinates (binary signals observed coordinate-wise), every relevant pair is separated by a decisive coordinate. By Theorem 4, the decisive coordinates form the unique minimal sufficient set. This is Spike 01's full-domain proposition, now proved for any answer type.

**Theorem 9, non-existence [Lean `no_minimal_representation`].** For infinite binary signals and the tail query "the signal is eventually always on":
- full observational power determines the query;
- no coordinate is decisive;
- *every* determining set remains determining after removing any one protocol.

**No minimal sufficient representation exists.**
- *Reading:* Theorems 9 and 11 form a **dichotomy**. Finite dependence yields a canonical minimal representation; asymptotic (tail) properties can have none.
- *Charter impact:* Layer H ("multiple incomparable minimal representations may exist; the theory must allow them") understated the situation. **Existence itself can fail**, and it does so for exactly the long-run properties (limits, stability, eventual behavior) that empirical science often cares about. A theory of task-relative abstraction needs a notion of *approximately* minimal or *limit* representation for such queries. → Conjecture C2.

### 3.4 Inquiry and abstention

**Theorem 6, gated inquiry [Lean `gated_sound`, `gated_complete`, `no_flip`, `closed_world_necessary`].** For an agent that answers q only when all survivors agree:
- **(a) sound:** if the truth is among the candidates, every answer is true;
- **(b) complete:** if Ω determines q, it always answers;
- **(c) no flip:** with exact observations, gaining protocols never changes a given answer; it only resolves abstentions;
- **(d) necessity:** without the closed-world premise, (a) fails. There is an explicit counterexample.

*Relation to the experiments.* Spike 02's zero wrong answers among 540 (truth among candidates) is the empirical shadow of (a). Its 105 wrong-but-labeled answers when the truth was removed are the shadow of (d). By (c), every retraction the Spike 02 ledger ever performs must be caused by a failed closed world or by statistical error, never by learning *more* in the exact regime. **This gives a diagnostic: a retraction is evidence against a premise.**

**Theorem 7, underdetermination [Lean `underdetermination`].** If two candidates are Ω-indistinguishable but disagree on q, then every procedure using only Ω-observations is wrong on one of them.

*The ontological conditionality principle.* Spike 02 F4 observed that "a hidden entity exists" never rose above CONJECTURE. Theorems 6d and 7 explain why. Any ontological commitment that is not Ω-determined on the candidate set can be warranted only conditionally on a premise that selects among indistinguishable candidates (closed world, parsimony, faithfulness), and the warrant must name that premise. What *is* Ω-determined, such as the directly measured effects in Spike 02 F5, holds for every survivor and needs no such premise.

**The empirically secure part of an ontology is its Ω-profile.** The rest is model-relative, and the theory says exactly which premise each further commitment rests on.

*Correction (2026-11-11).* An earlier version called this a structural-realist reading. It is weaker than that. By Newman's objection to structural realism (see the Stanford Encyclopedia entry, in the charter's own reference list), a purely structural claim about unobservables reduces to its observational consequences plus a cardinality claim. Our statement is therefore empirical adequacy relative to Ω, which is Theorem 7 restated; it gives no support to realism about structure. Likewise, when a prediction fails, the data do not determine which named premise to retract (Duhem); our retraction rules encode a policy.

### 3.5 The warrant calculus

**Theorem 8, weakest-link is optimal [Lean `join_is_greatest_lower_bound`, `stronger_refl`, `stronger_trans`].**
- *Setup:* warrants are (method basis, trusted base, conditions). Methods and trusted components each carry their own preorder (strength, trustworthiness). Warrants are ordered "each link of the stronger dominates some link of the weaker; no extra conditions".
- *Result:* the combination rule the ledger uses (union of everything) is the **greatest lower bound** of the supports.
- *Reading:* no rule that avoids overstating can give a derived claim a stronger warrant. The ledger's rule is safe and also the most generous safe rule.
- *Generalization:* the theorem is stated over arbitrary component preorders, so it also answers Spike 06 F3. Lean-kernel trust and Python-kernel trust can now be *ordered* by declaring a trust preorder; set inclusion is just the degenerate case.

### 3.6 Learning rules as observational powers

A learning rule is also an observer. For one layer, fix what its update may depend on (a set Ω of variables) and the symmetry group G the layer's units have. The **dictionary** D(Ω, G, K) is the set of G-invariant monomials of the variables in Ω up to order K; a rule is a weighted sum of them, followed by gradient. Spike 10b enumerates these dictionaries by code.

**Theorem 12, task-blindness [Lean `task_blind`].** If a block of parameters is updated by a rule that observes only that block (and task-independent inputs), then after any number of steps the block is the same for every task.
- *Reading:* a layer whose rule cannot observe the task carries no information about the task. Everything task-specific must be done downstream. This is the learning-rule analogue of Theorem 7: no procedure can depend on what it cannot observe.
- *Instance:* power A = {own input, weights, output}. Confirmed numerically for the full order-4 dictionary.

**Proposition 13, backpropagation is one monomial [numerical check to 10⁻⁵; exact by the chain rule].** With Ω = {X, W, Y, E, V} (own layer, broadcast error, downstream weights), the order-3 monomial E·(V·Y) has first-layer gradient E·V·(1−Y²)·Xᵀ, the backpropagated gradient. It is absent from every dictionary that omits V.

**Proposition 14, the symmetry gap [paper proof].** Let the hidden index have signed-permutation symmetry (flip unit j: Y_j, row j of W and V_j change sign). Every monomial in which each hidden index occurs an even number of times is invariant under such a flip. The error-broadcast term E·Σ_j Y_j is not. Hence it lies outside the orthogonal (trace-monomial) and signed-permutation dictionaries at every order, and inside the permutation dictionary at order 2.
- *Reading:* which rules are expressible depends on the symmetry group assumed, and trace monomials assume more symmetry than a network with an elementwise activation has. A comprehensive dictionary must be built from the layer's actual symmetry group.
- *Evidence:* that single term fits 96% of the 4-input tasks (Spike 10b).

**Empirical law (Spike 10b, not a theorem).** Among rules that fit, the function chosen on an underspecified task does not depend on the rule: backpropagation, feedback alignment and error broadcast pick a table-cheapest completion at the same rates, and random fitting networks do so at nearly the same rate.

This suggests a division of labour, stated as conjecture C6 below: **observational power decides which tasks a rule can learn; the parameter-to-function map decides which function it learns.**

### 3.7 Task symmetry and the choice of mechanism

Let G_g be the group of input permutations and input negations σ with g∘σ ∈ {g, ¬g}.

**Theorem 15, equivariance of mechanism choice [paper proof].** For the networks of Spikes 09–14 (inputs in {−1,+1}, i.i.d. symmetric Gaussian initialization of first-layer weights and biases, symmetric output weights, cross-entropy, full-batch GD or AdamW with decoupled weight decay), the probability that training on g yields a core whose minimal circuit is I equals the probability that it yields σ·I, for every σ ∈ G_g.
- *Proof.* σ acts on parameters linearly: an input permutation permutes the columns of W1, an input negation flips the sign of one column, and output negation (when g∘σ = ¬g) flips W2 and b2. (i) The initialization law is invariant under this action. (ii) The loss on g at θ equals the loss on g at σθ. (iii) GD, AdamW's moment estimates, the elementwise normalization and weight decay all commute with coordinate permutations and sign flips. So the trajectory from σθ₀ is σ applied to the trajectory from θ₀. (iv) The readout (threshold functions up to complement, units ordered by |output weight|) is equivariant. ∎
- *Reading:* every law of mechanism selection is a law about G_g-orbits. Spike 14 H14.1 confirms it numerically: within-orbit variance equals a multinomial null.

**Empirical law: the Curie bias (Spikes 12–14; pre-registered and replicated in Spike 14 on fresh seeds and unseen elements).** Orbit mass ∝ |orbit|^β with β between −2.3 and −5.7, under both optimizers and at widths 8 and 128. Training concentrates on mechanisms that keep a large subgroup of the task's symmetry. The bias is not explained by agreement with the target, and a parameter-free predictor based on it gains 1.25–1.67 bits per run. It also holds one level up: among the cheapest completions of a partial task, training picks a more symmetric function in 77% of cases.

This is the opposite of what an entropy or volume argument predicts (β ≥ 1). The ensemble is exactly symmetric (Theorem 15), and each run breaks the symmetry as little as it can.

### 3.8 The selection law as a semiring measure (empirical; after Baril, Couceiro & Lagerkvist 2026)

Baril et al. (arXiv:2512.03916) give a calculus for solution sets: join/union expressions, measures μ_M(F) = Σ_{f∈F} Π_s M[s, f(s)], and the ∆-product D∆A, which evaluates an A-measure on the *minimum-cost* solutions of a cost dioid D. In this language the empirical mechanism-selection law of Spikes 09–19 reads:

> **P(circuit I | task g) = normalized (R_min ∆ R≥0)-measure over the task's solution set,** with unit matrix M[u, t] = Ω(t)^γ · exp(λ·agree(t, g)).

- The *cost* coordinate (R_min) is the atlas's neuron count; training first selects minimum cost.
- The *weight* coordinate is a product over units; pairing is independent (Spike 17).
- The two parameters are *universal* across tasks: fitted on 64 elements, the law gains 1.6–1.7 bits/run on 64 unseen ones (Spike 19).

Status: EMPIRICAL (pre-registered transfer test H19.7 held; the two-parameter form is post hoc). The Curie bias (§3.7) is a consequence, since Ω and agreement are larger for symmetric units. The law reaches about 60% of the per-element ceiling.

**Refinement (Spike 20, pre-registered).**
1. The tilt variable is better stated as *mutual information* I(t; g) than agreement: 1.93 bits/run held out, about 70% of the ceiling.
2. λ is a constant (≈ 10.5 in agreement units) across optimizer, weight decay, horizon and width for tanh networks; C9's "temperature" reading is refuted.
3. ReLU networks and selection-only training have no tilt; their choice follows prior volume (γ ≈ 1).

So: **volume decides what is available; tanh gradient training adds an information tilt.**

## 4. Map: charter ↔ theory ↔ evidence

| Charter | Theory | Machine-checked | Empirical instance |
|---|---|---|---|
| Layer F (protocol-indexed equivalence) | Thm 1, 2 | yes | S05 hierarchy; S01 care sets |
| Layer G (canonical objects) | Thm 10 | yes | S01 ROBDD (order = Ω-encoding); S05 quotient |
| Layer H (task sufficiency) | Thm 3, 4, 9, 11 | yes | S01 F4; S02 F6 |
| §3.4 ontology revision, identifiability | Thm 7 | yes | S02 F1, F4; S02b F2 |
| §8.7 experiment selection | Thm 3, 5 | yes | S02 EIG chose do(A); S02b do(S2) |
| §10 honest labels | Thm 6, 8 | yes | S02 zero confident errors; S04 warrants |
| §7.5 small trusted checker | Cerp.lean `decideEquiv_correct`, `checkAll_sound`; Bounds.lean | yes | S03, S06, S08b |
| Layer K (how methods improve) | Thm 12, Prop 13–14 | Thm 12 yes | S10b |

## 5. Conjectures and open problems (the bold part)

- **C1, statistical lift.** Replace exact ≡_Ω with "not separable at level α from n samples". *Conjecture:* duality and gated soundness survive with error probability controlled by the per-test α summed along the conflict hypergraph's hitting structure. The sample complexity of determining q is governed by the *weakest* edge of a minimum hitting set, i.e. the hardest-to-separate relevant pair. Spike 02's measurements (absence ≈ 2× the cost of presence) are a data point.
- **C2, limit representations.** For tail queries (Thm 9), define ε-determining sets and show minimal ones exist for every ε > 0, with a well-behaved limit.
- **C3, adaptivity gap.** Adaptive inquiry (choose the next protocol after seeing results) is a decision tree over the frame. *Conjecture:* the adaptivity gap between adaptive and non-adaptive determining sets is bounded by a function of the conflict hypergraph's rank. Spike 02's EIG agent is a greedy adaptive policy, and its performance relative to the optimum is unmeasured.
- **C4, compositional frames.** For a product of independent frames, the decisive set of a composite query is the union of the component decisive sets whenever the query is "separable". This would give compositional canonicity, the charter's §14 open question.
- **C6, reach vs choice (withdrawn in its strong form, Spike 10c F3).** The conjecture was that any two rules that fit a task choose the same completions. Hand-written error-driven rules do (Spike 10b), but meta-learned rules with terms acting directly on the weights fit equally well and choose a cheapest completion far less often (72–84% against 96%). Revised form: the completion distribution is fixed by the architecture and initialization only for rules whose first-layer update is driven by the error alone.
- **C7, minimal observational power for learning.** For each element of the atlas there is a least observational power (and symmetry group) whose dictionary contains a rule that learns it. Power A is excluded by Theorem 12. Spike 10c: a broadcast error with permutation symmetry suffices for all 222 four-input elements (order 2, 7 terms). Whether the orthogonal or signed-permutation dictionaries suffice is open; search found 41 and 24 elements, which are lower bounds.
- **C8, Curie principle for learning.** For any architecture and training rule that are equivariant under a task's symmetry group G, the mass that training assigns to an orbit O of minimal mechanisms decreases with |O|. Equivalently, it increases with the size of the subgroup of G that fixes the mechanism. Open: (a) a mechanism (candidate: symmetric configurations are attracting under the averaged dynamics, cf. arXiv:2309.16932); (b) whether β is universal or depends on architecture; (c) transfer to non-Boolean domains, such as group-operation tasks, where G is large and known. **Update (Spike 26):** (c) is supported on one non-Boolean domain. When trained nets complete partial operation tables on a 3-element carrier, β = −1.85 [−2.72, −1.08], and the completions are associative 9.6× as often as chance.
- **C9, tilted-volume law (temperature form REFUTED by Spike 20).** λ does not depend on optimizer, weight decay or horizon. It does depend on the activation: ReLU gives no tilt.
- **C10, origin of the tilt (REFUTED by Spike 22).** The conjecture was that the tilt arises because gradient *moves* units, which ReLU's dead side prevents, so leaky slopes would restore it. Leaky ReLU does not restore it (λ falls from 1.2 to 0.3 as the slope grows to 0.3, against 11.5 for tanh), and nearly every unit changes function under every activation (≥ 97.8%). Spike 21 also rules out the output-weight credit ratchet: removing the w₂ factor from the gradient leaves λ unchanged. What Spike 21 does establish: at initialization the unit distribution is exactly the volume measure (γ = 1.00, λ = 0.0), and the tilt forms within ~100 steps.
- **C11, oddness or saturation (REFUTED by Spike 24).** Sigmoid and clipped ReLU have the tilt without being odd. Arcsinh has it without saturating.
- **C12, positive homogeneity (REFUTED by Spike 27).** Homogeneous activations do lack the tilt. But softplus, which is not homogeneous, lacks it too (λ = 2.0). Removing ReLU's rescaling symmetry does not restore it (λ = 1.2).
- **C13, indicator alignment (SUPPORTED, prospectively, by Spike 28).** The information tilt λ is strong when a unit's output mostly records *which side* of its hyperplane an input lies on. The measure is R² = corr(φ(x), 1[x > 0])², with x ~ N(0, 4). The rule was found after the fact on 15 activations. It was then tested on 9 new ones with predictions fixed in advance, and all three hypotheses held:
  - R² ≥ 0.77 gave λ 9.5–11.6;
  - R² ≤ 0.50 gave λ 2.0–2.1;
  - Spearman ρ was 0.83;
  - clipping ReLU at c = 1, 2, 4 gave λ = 10.5, 6.7, 2.0.

  Proposed mechanism: an indicator-like unit hands the readout its threshold function t, so the loss gradient that moves the unit depends on t's information about the target. A graded unit hands over distance, so what is selected is the usefulness of a ramp. Open: the middle zone (R² ≈ 0.6) is not decided by this R², which uses a fixed pre-activation scale rather than the trained one. Spike 23 shows the tilt acting at the level of single steps: of the available neighbouring cones, units step into the more informative one (μ = 3.9) and, separately, the more symmetric one (β = 0.26), beyond distance.
- **C14, interpretability–generalization trade-off (REFUTED as a mechanism by Spike 30).** Spike 29's anti-correlation between tilt and held-out accuracy is inherited from the activations' initial kernels (ρ(λ, kernel accuracy) = −0.73). With the kernel controlled for, the tilt is unrelated to held-out accuracy (ρ = −0.03).
- **C15′, why these nets generalize: kernel prior plus a positive feature-learning update (SUPPORTED by Spike 30).** The activation's initial NTK fixes the generalization prior. It ranks held-out accuracy across 24 activations at ρ = 0.81–0.92, and nets agree with it on 76% of unseen inputs. Feature learning departs from the kernel, more so in tilted activations (ρ = −0.61), and where it does it is right 55% of the time (+2.4 points, in 23 of 24 activations). Open: why graded activations have better kernels on this atlas (candidate: smoother decay with Hamming distance).
- **C16, degree-1 spectral bias (REFUTED by Spike 31).** The targets' Walsh energy is mostly at degree 2 (0.44), and activations with more degree-1 weight have worse priors (ρ = −0.46). What holds instead is known theory: a kernel whose degree spectrum matches the targets' beats every activation kernel (spectral bias / task–model alignment; Bordelon, Canatar & Pehlevan). Degree spectra explain the activation ranking only weakly (ρ ≈ 0.3). Next candidate: the constant mode μ₀ (pull toward the seen majority). Caveat for all generalization claims here: targets are 39.6% ones, so balanced accuracy must be reported; on it, nets are at 0.52–0.56.
- **C17, training as the init-prior Bayes posterior (PARTLY SUPPORTED, Spike 32).** The exact weight-space-volume posterior predicts trained nets' held-out outputs better than the NTK (agreement 0.800 vs 0.763, in all 24 activations). But the nets generalize better than this posterior in 24 of 24 activations, and their improvement over the kernel is not in it. So generalization here = init prior (most of *what* is predicted) + a positive effect of the training dynamics that is not Bayesian under the init prior.
- **C18, the tilt carries the gain beyond the init prior (NOT SUPPORTED, Spike 33; not refuted).** Feature learning is necessary: frozen-feature nets fall *below* the init-prior posterior (−0.010), and trained-feature nets beat it in 18 of 18 cells (+0.025). Across cells, gain tracks both λ (ρ = 0.67) and feature movement (ρ = 0.59), which are confounded (ρ = 0.77). Within an activation (post hoc), gain tracks movement (0.58) more than λ (0.27), and the negative-tilt |x| gains most under plain GD. Leading reading: feature *movement* improves on the init prior, and the tilt is a by-product in saturating activations. Separating test: Spike 34 dose–response.
- **C19, Occam (minimum circuit cost) as the missing prior (NOT SUPPORTED at n = 4, Spike 34).** The compiler's cheapest completion reaches 0.552 balanced, beating 15 of 24 activations' nets without training. But where training departs from Bayes-under-init it does not move toward Occam (45.2%), and volume tie-breaking hurts. Cause: at n = 4 about 10 of 16 completions tie at the minimum cost, so the prior is too coarse. Untested at n ≥ 5, where it predicts sharper separation.
- **C5, trust-indexed escalation.** Given warrant costs per trust tier (Spike 06 F1), there is an optimal escalation policy: re-check at a higher tier exactly those claims whose `affected_by` set exceeds a threshold proportional to the cost ratio.

## 6. What this does *not* claim, and what is already known

A literature review (`charter/LITERATURE_REVIEW.md`, 2026-11-11) found prior work for most of the core. **The theory is a synthesis of known results in one machine-checked framework, not new mathematics.**

| Part | Already known as |
|---|---|
| Thm 1–2 (Galois connection) | Formal Concept Analysis (Wille; Ganter & Wille) |
| Thm 3 (duality) | Rough-set discernibility for features; separating systems for experiments (Hyttinen et al. 2013; Shanmugam et al. 2015); teaching sets for examples |
| Thm 4 | Core and unique reduct in rough sets |
| Thm 6–7 | Version spaces; causal identifiability |
| Thm 8 | Assumption-based truth maintenance tracks the premises; the ordered warrant and its optimality were not found |
| Thm 12 | Necessity of a backward channel (Baldi & Sadowski, as cited by Perin et al.) |
| Atlas method | Minimal threshold networks by integer programming, including partially specified functions (Cameron 1964; Hopcroft & Mattson 1965) |
| Spike 10b volume and grokking results | Volume hypothesis literature; Omnigrok |

What remains ours: the integration, the Lean development, kernel-checked certificates on running code, and exact small-scale measurements. The open hypotheses most likely to be new are H-A to H-F in the review.

Further limits:
- The frame does not capture every epistemic situation. Probabilistic protocols, costs and partial observation are only partly covered: C1 and C3 are open.
- The formalized theorems say nothing about the real world beyond their hypotheses. Whether an empirical setup is a protocol frame with exact observations is an empirical claim with its own warrant.
