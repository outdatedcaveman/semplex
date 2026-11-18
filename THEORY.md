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

**Theorem 15, equivariance of mechanism choice [paper proof; a discrete version is proved in Lean, P160].** For the networks of Spikes 09–14 (inputs in {−1,+1}, i.i.d. symmetric Gaussian initialization of first-layer weights and biases, symmetric output weights, cross-entropy, full-batch GD or AdamW with decoupled weight decay), the probability that training on g yields a core whose minimal circuit is I equals the probability that it yields σ·I, for every σ ∈ G_g.
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

- **C1, statistical lift (CONJECTURE, unchanged).** Replace exact ≡_Ω with "not separable at level α from n samples". *Conjecture:* duality and gated soundness survive with error probability controlled by the per-test α summed along the conflict hypergraph's hitting structure; the sample complexity of determining q is governed by the weakest edge of a minimum hitting set. *Status after Gemini's work (P139):* the Lean lemmas filed under C1 do not touch probability. `statistical_gated_sound` is modus ponens and `union_bound_sum` bounds a sum of naturals. They are scaffolding for a future proof, not the lift. Spike 39 (exploratory, not pre-registered) measured 0/48 truth rejections down to `n_per = 200`, which is consistent with the conjecture.
- **C2, limit representations (PROVED for stabilized slices and the metric limit; Lean, P135, P139).** For tail queries (Thm 9), `EpsDetermines` is monotone (`eps_determines_mono`); on `N`-stabilized signals `EventuallyOn` is determined by finite prefixes (`prefix_determines_stabilized`); and a sequence of protocol sets achieving every tolerance determines q in the union limit (`metric_eps_limit_determines`). The general existence of minimal ε-determining sets with a well-behaved limit is still open.
- **C3, adaptivity gap (CONJECTURE, unchanged; a lower bound is PROVED).** *Conjecture:* the gap between adaptive and non-adaptive determining sets is bounded by a function of the conflict hypergraph's rank. *Proved in Lean (P136, P143):* an accurate adaptive `QueryTree` uses a determining protocol set, so it needs at least the minimum hitting-set number of distinct protocols; each hypothesis's trace hits all its local conflicts. The rank bound itself is not addressed.
- **C4, compositional frames (PARTLY PROVED; Lean, P134).** For a product of frames, indistinguishability and determinacy decompose componentwise, and a protocol decisive for a component query is decisive for the product query. This is one inclusion of the conjectured union characterization. The converse inclusion for "separable" queries is not proved. `profile_factor_compile` (P141) is the one-line decode identity behind the Ur-Compiler's factoring, not a proof of C4.
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
- **C19′, feature learning as approximate minimum-circuit search (PARTLY SUPPORTED: holds and replicates on clean targets, fails on real data in Spike 45; Spike 36: departures from the kernel go toward Occam in 73–81% of cases in all 4 fresh cells; partly causal: widening toward the lazy regime raises kernel agreement +0.048, lowers Occam agreement −0.038 and lowers held-out accuracy −0.033).** At n = 6 the init NTK generalizes at 0.79 balanced, trained nets at 0.886–0.894, and the compiler's certified Occam completion at 0.902. Nets agree with Occam on 91% of held-out inputs, against 81–83% with their own NTK. Where nets depart from the NTK, Occam sides with them 80% of the time. Training starts from the kernel prior and moves toward the minimal circuit. This revises C19's n = 4 negative (Spike 34), which was a coarseness artifact. It is consistent with Spike 9 (training picks table-cheapest functions in 88–95% of underspecified runs). *Timing (Spike 43, pre-registered, H-J two-phase core held):* the first ~10 steps change the function along the kernel-smoothed target K f\* (agreement 0.77–0.81). On held-out inputs where K f\* and the Occam completion disagree, the early change sides with K f\* (S = 0.39–0.40 through step 10). S then turns toward Occam from step 30, passes 0.5 by step 100 and ends at 0.72. Plain GD shows the same two phases. This matches Nichani et al.'s first-step feature K f\*. *Depth (Spike 44, pre-registered, H-K REFUTED at this scale):* at matched parameters, three-layer nets agree with Occam slightly less (−0.003, −0.007) and stay closer to their own kernel. The Occam pull is a first-layer feature-learning effect, not a depth effect, for targets that two layers represent exactly. *Scope (Spike 45, pre-registered):* the pull generalizes to other clean target classes (H45.1 held: cost-4 targets 0.72, symmetric functions 0.90, DNF 0.67), weakens with label noise (0.58 with 5 of 48 labels flipped), and **fails on real data** (H45.2 REFUTED: Breast Cancer 0.29, Diabetes 0.45, Digits 0.56; only Wine 0.74). On real tasks the kernel predicts the net better than Occam in 3 of 4 datasets (H45.3 refuted), and the kernel generalizes better than the trained net in 3 of 4 (H45.4 refuted). C19′ is therefore a statement about clean, structured targets. *Scale (Spike 48, pre-registered):* at 8 labelled inputs per dimension the pull is 0.72 at n = 8 and 0.65 at n = 10 (0.80 at n = 6), so it persists and shrinks (H48.1 neither); with 75% of inputs seen at n = 8 it is 0.94. Nets beat their kernel at both sizes (H48.3 held). The pull appears to track how well the seen data determine the minimum circuit. The boundary is label noise (Spike 46, H46.1 held: the pull is 0.83 with no flipped labels, 0.66 with 2 of 48, 0.57 with 5 or 8).
- **C20′, under label noise nets follow a simpler circuit plus memorized exceptions (NOT SUPPORTED, Spike 46; not refuted).** With the exact cost–error frontier computed by the compiler, the frontier point one cost level below the exact fit predicts noisy-label nets no better than the exact-fit circuit (differences −0.004 and +0.006, bars ∓0.02), and beats the kernel on only 1 of 3 real datasets. Noise makes the net less like any circuit: its best circuit agreement falls from 0.89 to 0.75. Exploratory: a two-part-code (MDL) circuit generalizes better than the trained net under noise (0.77 vs 0.70 at 8 flips), so the compiler denoises better than training does here.
- **C21, constrained collapse (REFUTED by Spike 47).** The conjecture was that a hidden layer, unable to collapse to the class for a non-threshold target, collapses onto the cells of a minimum circuit. At 4 inputs over all 128 cost-3 function classes, a width-8 layer is a function of a minimum circuit's cell in 0.08% of nets; the best minimum circuit explains 56% of the representation's variance and the best of all 441,330 two-hyperplane partitions 73%. Minimum circuits are over-represented (the top partition is one in 5.9% of nets, 700 times chance) but not what the layer settles on. So C19′'s function-level agreement does not come from the representation becoming the minimum circuit.
- **C22, consensus law (PARTLY SUPPORTED, Spike 49).** Call a held-out input forced if every minimum circuit consistent with the seen labels gives it the same value. Trained nets output the forced value on 97.9–99.1% of forced inputs, the same at n = 8 and 10 and from 48 to 144 seen inputs (H49.1, H49.2 held), and where they leave their kernel on a forced input they go to the forced value 82–95% of the time (H49.3 held). The decline of the Occam pull with n (Spike 48) is a decline in the fraction of forced inputs (17–81%), not in adherence. Caveat (H49.4 neither): forced inputs are mostly easy ones, where the kernel is also right 87–97% of the time; the net's edge is +2 to +12 points and clears the pre-registered +5 only with more data.
- **C23, graded consensus (PARTLY SUPPORTED, Spike 50).** The share of minimum circuits outputting 1 at a held-out input tracks the share of independently trained nets that do (Spearman 0.76–0.79 at n = 8 and 10; H50.3 held), and inputs on which circuits split evenly are the ones on which seeds split (15–18% vs 1.4–1.9%; H50.4 held). As a predictor of a single net it reaches 0.91–0.93, short of the pre-registered 0.93 in two of three cells (H50.1, H50.2 neither). The majority of minimum circuits generalizes better than one trained net (0.89–0.95 vs 0.88–0.92 balanced accuracy).
- **C24, trained nets reason like a rational nonmonotonic logic (NEITHER, Spike 51).** At n = 4 over 384 tasks, nets' confident conclusions violate Cautious Monotony in 4.3% of instances (H51.1 held), Cut in 5.9% and Rational Monotony in 15.0% (neither). Under counter-evidence they retract 35% of conclusions, in the logic's direction (96% of their retractions are also the minimal-model relation's) but only 48% of what the logic retracts: they are stubborn. The kernel is as cumulative and more rationally monotone, so rationality does not distinguish nets from kernels.
- **C29, symmetry determines concept geometry (PARTLY SUPPORTED; tensor row REFUTED for lexical composition; Spike 53).** In the static embedding weights of 14 open models (24 matrices, rows read directly from the safetensors files), weekday and month vectors form circles: cyclic R² is significant in 85% of cases and the lowest Fourier mode dominates in all of them (H53.1 and H53.2 held). The category block structure appears in all 24 matrices and in THINGS-fMRI object cortex of all 3 subjects (H53.4 and H53.5 held), and brain and model concept geometries correlate in all 63 pairs (median ρ 0.12, H53.6a held).
  - **Refuted:** the prediction that product concepts compose as a tensor product. For month × form and weekday × form, the cycle sits in the additive part (89% of cases), and the interaction carries it in only 13% (H53.3 broken). Composition here is a direct sum, with a weak tensor residue (51% at p < 0.05).
  - **Also broken:** the strong reading that the shared grain is the group skeleton. After removing the 17-category block structure, brain–model agreement remains in 81% of pairs (H53.6b broken), so the shared structure is finer than the labelled taxonomy.
  - **Spike 54 (activations, Neuronpedia sparse codes of 4 models).** Semantic products ("Monday morning", "early January", "last Friday") at their last token are again mainly sums: the last word carries 76–93% of the variance, the other factor enters additively, and the interaction is small (relative interaction 0.05; H54.3 broken; H54.1 and H54.2 neither). The interaction still carries the cycle in 71% of cases at p < 0.05. Where the weekday is not the represented token, it is carried as much by conjunction as additively. The product row stays refuted as a description of composition; a weak structured tensor residue is real.
- **C30, justice as invariance under permuting persons (SUPPORTED, approximately; Spike 56).** Spike 55 could not read a verdict from public sparse codes. Spike 56 used the models' own verdicts (log P("unfair") − log P("fair")) from six small instruct models on CPU, over 12 acts × 30 ordered name pairs. In the three models that judge the cases correctly at ≥ 0.80:
  - names account for 3–5% of the verdict's variance, against 33–40% of the internal state's (H56.2 and H56.3 held);
  - no name moves a verdict by more than 0.21 act-SD (H56.4 held).
  The invariance is approximate: name effects are small but statistically real (permutation p ≤ 0.0002), and they measure residual bias. Weaker models are both less accurate and more name-driven (TinyLlama: 44% name share).

- **C31, economy law for concept geometry (PARTLY SUPPORTED; Spike 57).** Trained recurrent nets on automata built from known Krohn–Rhodes parts represent:
  - a reset as a near-regular simplex (H57.3 held);
  - S₃ mostly in its 2-dimensional standard representation (H57.4 held);
  - cyclic groups as 2-dimensional circles in group order with the lowest Fourier mode, but unevenly spaced (H57.2 broken on spacing).
  A direct product is a near-pure sum (interaction 0.03). A cascade carries 4.3 times more interaction than the matching product in every run, yet far less than a linear (fibred) representation needs (0.14 vs ≥ 0.60; H57.5 neither). The product half of the law holds; the cascade half holds in direction, not magnitude.
- **C32, closure law (registered test BROKEN; exploratory analysis SUPPORTS it; Spike 57).** Nets trained only on outputs do not form tight clusters at the minimal automaton's states (k-means ARI ≥ 0.95 in 21% of runs; H57.1 broken). But a linear probe recovers the minimal state with 100% accuracy in all 29 fitted nets, and the probe-state macro-dynamics are 100% deterministic, i.e. exactly lumpable. The minimal automaton (the Platonic form) is present as an exact closed coarse-graining of a richer microstate that keeps 20–27% within-state variance (Aristotle's macrostate). A confirmatory test must register the probe version.

- **C32 confirmed with causal power (HELD; Spike 58).** In all 31 fitted recurrent nets on seven automata (reset, ℤ/5, S₃, A₄, A₅, product, cascade):
  - the minimal automaton is an exactly lumpable linear coarse-graining (H58.1);
  - overwriting the macrostate makes the future follow the automaton from the new macrostate in 100% of trials (H58.2);
  - swapping micro-detail within a macrostate changes nothing (H58.3).

  The Plato–Aristotle synthesis (§9.1) holds as an experiment: abstractions are macrostates, and closed macrostates are causes. Learning cost follows the periodic table exactly (aperiodic < cyclic < solvable < non-solvable A₅; cascade > product; H58.6 held).
- **C31 revised to C31′ (minimal-faithful clause REFUTED where it is distinguishable; Spike 58, exploratory).** The learned Gram is the predicted minimal faithful character for ℤ/5, S₃ and A₄. For A₅ it is χ₄ in 5/5 runs, not the 3-dimensional icosahedral representation. All 15 non-abelian runs fit the permutation representation on the points the output reports. C31′: the geometry is the group's permutation representation on the cosets the readout distinguishes. To be tested prospectively (A₅ on 6 points predicts χ₅).

- **C31′ tested prospectively; refined to C31″ (Spike 60).**
  - **Held:** A₅ read out through 6 points gives χ₅, the readout's representation, in 3/3 fitted GRUs; the minimal faithful 3-dimensional characters are anti-correlated (H60.2 held).
  - **Broken:** S₄ read out through 6 points uses the standard representation alone, not the readout's standard ⊕ χ₂ (H60.1 broken).
  - **C31″ (post hoc, fits 18/18 fitted runs):** a trained recurrent net represents a group concept by the *faithful constituents of the group's permutation representation on what its readout distinguishes*.
  - **Transformers:** 2 layers fitted neither S₄ nor A₅ (H60.5 broken, both fail), so the substrate comparison and the Barrington grading remain untested.

- **The predictive-state law (SUPPORTED; C31‴ REFUTED; Spike 62).** Compression to the smallest faithful, readout-sufficient set (C31‴) is refuted on five new readouts (H62.1–H62.3 broken): networks keep unfaithful constituents (χ₂, sign) as their dominant geometry. The exact predictive-state kernel, the Gram matrix of expected future outputs computed from the automaton alone (FOUNDATIONS §11.4), predicts the observed best character in every fitted case of Spikes 60 and 62 except one (S₄ via 6 points in Spike 60). Three of its predictions (S4_12b, A5_10, A5_15) were made before those runs finished, though not formally registered. **Learned geometry = predictive-state geometry** is the current law, to be confirmed by a formally pre-registered test.

- **The predictive-state law refuted as universal (Spike 66; H66.1–H66.2 broken).** For identity-only readouts the predictive kernel is diagonal (equidistant states), but networks build compact structured geometry. Its successes are confined to coset readouts of moderate size. The S₄ 6-point anomaly replicated (standard, 3/3). **Closure discards the unobservable p-part** (ℤ/6 read mod 3: c mod 2 undecodable, probe 0.54; H66.3 held). Post-hoc synthesis C37: predictive structure decides the geometry when it is low-rank and structured; architectural bias (compact, low-frequency, faithful) decides it when the predictive state is degenerate.

- **C34, invariance of shared meaning (SUPPORTED; Spikes 64, 68).** Static lexicons of 14 models are rotated copies of a common frame in their leading dimensions (no gluing obstruction; P195). For concepts in context in 5 small models, unrelated models share shape (CKA 0.84) and a common frame up to rotation (Procrustes R² 0.46), but not raw coordinates (axis excess ≤ 0.20). A model and its own fine-tune share coordinates (0.97). What independent learners share is the concept's invariant shape and a frame defined up to one rotation each, never their coordinates.

- **C36, linearising cover (SUPPORTED; Spike 70, pre-registered; H70.1, H70.2, H70.4 held, H70.3 neither).** With a guard the networks pass (R² ≥ 0.99), GRUs trained to output only the axis uuᵀ represent the signed direction: the double cover S² → RP², not the minimal quotient. Their degree-1 geometry matches sign-trained networks, the sign is perfectly decodable, and antipodes stay apart (P203). Continuous closure keeps a bit the readout cannot see when dropping it would break the linearity of the dynamics. The candidate reconciliation with discrete closure (the coarsest quotient on which the dynamics act linearly at small dimension) is untested. **Spike 72:** the cover persists when rotations are input in the degree-2 representation, so C38 (input encoding decides the cover) is **refuted** (P206). Candidate C40 (untested): when letters are near-identity, a smoothness pull selects the lowest-frequency faithful representation. **Spike 73:** C38 refuted on the discrete side too (A₅ fed χ₃ letters still builds χ₅, P207). **C41, gated smoothness (post hoc):** the leader is the smoothest constituent (along the letters) among those with predictive share ≥ θ; it fits 46/48 cyclic runs over Spikes 69–73 and must be tested prospectively. **Spike 74:** C41 (gated smoothness) **refuted** as a deterministic law prospectively (68%; P208): when several constituents carry predictive energy, the leader is a seed lottery. The robust shape law: geometry lies in the readout's energetic constituents, and a clearly dominant multiplicity-weighted one leads.

- **C37, two regimes (STRUCTURED HALF SUPPORTED as a leading-component law; DEGENERATE HALF REFUTED; Spike 69, pre-registered with predictions).**
  - *Spike 71 (pre-registered head-to-head):* the leading constituent follows **multiplicity-weighted** predictive energy (share ∝ m²C). It beats the dimension-discounted AGF utility (Kunin et al. 2025, extrapolated) and the minimum-orbit predictor (Wu et al. 2025) in 8/8 runs where they disagree (P204), and it is robust to reparametrisation.
  - *Refuted:* low-dimension tie-breaking and persistence of the first-emerging geometry, since learning passes through stages (P205).
  - *Open:* ties and cyclic counters depend on the letters, with a pull toward the smooth k = ±1 circle.
  - *Supported:* where the predictive kernel has a unique top isotypic component, GRUs build it as the leading constituent in 29/34 runs, including unfaithful ones (P201).
  - *Refuted:* the full Gram is not the kernel (H69.1–H69.2 broken).
  - *Refuted:* with identity readouts, networks do not build the minimal faithful representation (H69.4 broken). In Q₈, A₄ and S₃, abelian letter counts lead.
  - *Ties:* in permutation readouts, multiplicity-1 constituents carry equal predictive energy (lemma, FOUNDATIONS §11.4), and ties are broken by the generating set. The S₄ pair "anomaly" is dynamical and does not generalise: A₄ on pairs follows the kernel to its unfaithful constituent (P202).

- **Semantic primes as the lexicon's elements (REFUTED in model lexicons; Spike 59).** In 24 embedding matrices of 14 open models, Wierzbicka's 67 single-word prime exponents reconstruct concrete nouns *worse* than frequency-matched real words in every matrix (H59.1 broken; median z −3.8), and abstract words no better (H59.2 broken). Prime decompositions agree across models beyond chance (H59.3 held), but an exploratory control shows random frequency-matched dictionaries agree as much or more (concrete 2.07–2.18 vs primes 1.84 shared atoms; abstract 2.95–3.15 vs 2.93): the agreement is shared model geometry, not a property of the primes. The lexical periodic table is not made of these words in these spaces; its elements must be found from data.

- **Data-driven lexical elements (NONE FOUND at the word-embedding level; Spike 61).** Sparse dictionaries (256 atoms, 5 per word) learned independently in 14 models' input embeddings over 6,163 shared words do not match across models better than principal directions (median matched correlation 0.148 vs 0.146; H61.1 neither), and no atom is universal (0/256; H61.2 broken). Rotation-invariant geometry is strongly shared (linear CKA median 0.59; exploratory). So lexicons share a shape without a basis. The table's elements, if any, are operations on representations (as with automata), not a set of word-level directions.

- **C5, trust-indexed escalation (PROVED in an assumed linear-gain model; Lean, P139).** Given per-claim cost and impact, the threshold policy `0 < impact − ratio·cost` maximizes total net benefit over all escalation policies on any finite claim list and is unique on non-tie claims (`threshold_escalation_optimal`). The proof is pointwise maximization summed. The open part is whether escalation gains are additive across claims that share dependencies (the ledger's `affected_by` sets overlap).

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


---

## 7. Quantitative Morphisms, Markov Contraction, Interpretant & Ville Bounds, and Verified Networks (2026-11-13, Gemini; merged with corrections)


> **Merge note.** Written by Gemini on `master`. Spike and claim numbers were renumbered at the merge (Spikes 11–16 → 37–42, P058–P078 → P131–P151). The Lean results compile with standard axioms only. Two readings were corrected: §7.3's `peirce_pragmatic_maxim` is duality (Thm 1) applied to the composed observation map, and the Peirce interpretation adds no mathematical content. The empirical items in §7.5 come from a spike that was not pre-registered, so they are exploratory.

The Lean 4 formalization (`proofs/lean/Theory.lean` §§17–19 and `proofs/lean/Cerp.lean` Part D, checked cleanly in `Lean 4.12.0` under standard axioms `{propext, Classical.choice, Quot.sound}`) and Spike 42 experiments extend Sections 2–5 in four directions while clarifying hard combinatorial and empirical barriers:

### 7.1 Indexed Protocol-Frame Morphisms & Lossy-Composition Obstruction (`Theory.lean` §17, P144)
For indexed protocol frames `(Φ₁, Φ₂)` and morphisms `FrameHom`:
- **`frameHom_indist`, `frameHom_determines_pullback`**: Exact query determinacy pulls back contravariantly along protocol-preserving morphisms.
- **`queryApprox_comp`, `frameHom_eps_determines_pullback`, `frameHom_eps_metric_pullback`**: Quantitative `ε`-determinacy (`EpsDetermines`) composes additively (`ε₁ + ε₂`) across stacked abstractions/metrics and pulls back along `FrameHom`.
- **`lossy_composition_obstruction`**: An explicit 3-point finite protocol system witnesses that exact query loss across coarse abstraction stages creates non-trivial indeterminacy that cannot be recovered locally without enriching $\Omega$ (motivating sheaf/cohomological obstruction invariants as future work).

### 7.2 Constructive Finite Markov-Kernel Data-Processing Contraction (`Theory.lean` §18, P145)
Using explicit finite rational/real discrete distributions over `Fin n`:
- **`tv_deterministic_dpi`**: Deterministic pushforward maps never increase total-variation distance.
- **`markov_kernel_dpi`, `markov_kernel_dpi_comp`**: Finite stochastic Markov kernels satisfy $D_{\mathrm{TV}}(K \mu, K \nu) \le D_{\mathrm{TV}}(\mu, \nu)$ and compose inductively across multi-step transitions (`T-step-TV` grounding the Ur-Compiler's `stochastic_lts` approximation bounds without Mathlib measure theory).

### 7.3 Peircean Triadic Semiosis & Anytime-Valid Ville/Optional Stopping (`Theory.lean` §19, P146)
- **`indist_implies_pragEquiv`, `peirce_pragmatic_maxim`**: Formalizing Peirce's `Sign–Object–Interpretant` triad over action-observation frames, two signs yield indistinguishable practical consequences across all admissible Interpretant contexts if and only if they fall in the same observational determinacy equivalence class.
- **`applyStop_preserves_supermartingale`, `optional_stopping_supermartingale`, `ville_anytime_valid_bound`**: Over finite horizons `T`, any adapted causal stopping policy preserves the discrete nonnegative supermartingale property and obeys Ville's anytime-valid inequality ($\mathbb{P}(\max_{t \le T} M_t \ge \alpha) \le \mathbb{E}[M_0]/\alpha$). Connecting concrete `cerp/epistemics.py` empirical tests directly to instances of `ville_anytime_valid_bound` remains an open bridge.

### 7.4 Verified Integer-Weight `ThresholdNet` Emission (`Cerp.lean` Part D, P147–P148)
- `Cerp.lean` Part D defines executable integer-weight linear-threshold DAGs (`TNode`, `evalTNet`, `tnetScoped`) and verifies compiler outputs against canonical `Expr` specs via both exhaustive kernel checking (`decideTNetEquivExpr_correct`) and linear-time LRAT hint-indexed Tseitin miters (`tseitinTNetMiter_lrat_unsat_implies_equiv`, Python bridge `prove_tnet_equivalence_lrat` + `verify_threshold_net_equiv`).
- **Measured scaling bottleneck:** `pbToExpr` expands a fan-in-`d` threshold neuron using an exponential $O(2^d)$ Shannon `ite` tree. Consequently, pure-kernel `by decide` passes `xor3` (4 `TNode`s, 173 clauses, 8 LRAT steps) in `219.37s` but times out (`>900s`) on `xor4` (5 `TNode`s, 431 clauses, 16 LRAT steps), where `native_decide` succeeds in `14.78s`. A linear $O(d \cdot w)$ binary-adder pseudo-Boolean encoding in `Cerp.lean` is required before kernel LRAT net verification scales to high-fan-in multi-layer networks.

### 7.5 Spike 42 Empirical Corrections & Negative Results (P149–P151)
- **Local rule variance (`test_localrules.py`):** The intermittent `0.875 < 0.9` score on `rng(1)` gen 3 reflects Monte-Carlo initialization variance of pure backprop (`mean=0.9521`, `min=0.875` over 20 seeds), not CEM dropping backprop (`a[bp]=1.0`).
- **Width coarsening (`H-A` vs `H-D`, $n=8$):** Single-unit alignment fades with width (`0.3713` at $W=8 \to 0.3062$ at $W=32$) while linear subspace $R^2$ climbs to `0.9850` (`SPIKE_42_REPORT.md` §2).
- **`XOR6` (`H-C`) & `parity5` (`H-E`):** `32/64` fails to grok (`0/9` seeds up to 3,000 steps); at `48/64`, unregularized Adam reaches `0.9375` while `wd=0.01` exhibits anti-parity collapse (`0.2292`). Bounded-weight CP-SAT (`|w| <= 4`) verifies `chain(5,3)` (`3` neurons, `sat` `0.596s`) vs depth-2 `[3,1]` (`4` neurons, `unsat` `17.539s`), and `[3,1]` `unsat` for `parity4` (`13.985s`), leaving unbounded $\mathbb{R}^4$ Lean mechanization of `parity4 >= 5` open past the $\binom{1882}{3}$ enumeration barrier.
