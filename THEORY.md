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

This is a precise, checkable form of a structural-realist intuition: **the empirically secure part of an ontology is its Ω-profile.** The rest is model-relative, and the theory says exactly which premise each further commitment rests on.

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
- **C6, reach vs choice.** For a fixed architecture and initialization, any two learning rules that both fit a task induce (approximately) the same distribution over completions, namely the weight-space volume conditioned on fitting. Evidence: Spike 10b F1–F2. Known to be scale-dependent; the exact statement needs the initialization as a parameter.
- **C7, minimal observational power for learning.** For each element of the atlas there is a least observational power (and symmetry group) whose dictionary contains a rule that learns it. Power A is excluded by Theorem 12; whether broadcast error with only signed-permutation symmetry suffices is open.
- **C5, trust-indexed escalation.** Given warrant costs per trust tier (Spike 06 F1), there is an optimal escalation policy: re-check at a higher tier exactly those claims whose `affected_by` set exceeds a threshold proportional to the cost ratio.

## 6. What this does *not* claim

- That the frame captures every epistemic situation. Probabilistic protocols, costs and partial observation of outcomes are only partly covered: C1 and C3 are open.
- That the formalized theorems say anything about the *real* world beyond their hypotheses. The Lean proofs establish the logic; whether a given empirical setup *is* a protocol frame with exact observations is an empirical claim with its own warrant, which Spike 02 treats statistically.
- Priority for ingredients with precedents: discernibility and reducts, testing equivalences, causal observational equivalence, Galois connections between attributes and objects, hitting-set hardness. The contribution claimed is the unification, the transport across domains, Theorems 6, 9, 10 and 11 in this generality, the warrant calculus with its optimality result, and the end-to-end machine-checked development tied to working spikes.
