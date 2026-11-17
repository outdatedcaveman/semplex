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

**Proposition 14, the symmetry gap [paper proof; its core lemma is Lean `even_span_excludes_odd`].** Let the hidden index have signed-permutation symmetry (flip unit j: Y_j, row j of W and V_j change sign). Every monomial in which each hidden index occurs an even number of times is invariant under such a flip. The error-broadcast term E·Σ_j Y_j is not. Hence it lies outside the orthogonal (trace-monomial) and signed-permutation dictionaries at every order, and inside the permutation dictionary at order 2.
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

- **C1, statistical lift.** Replace exact ≡_Ω with "not separable at level α from n samples". *Lean (`Theory.lean` §14):* `statistical_gated_sound`, `union_bound_sum`, `err_le_sumBudget`, and `uniform_budget_bound` prove cross-multiplied finite-candidate error-budget additivity and gated soundness; Spike 13 measured 0/48 truth rejections down to `n_per=200`.
- **C2, limit representations.** For tail queries (Thm 9), `EpsDetermines` is monotone (`eps_determines_mono`), on `N`-stabilized signals `EventuallyOn` is determined by finite prefixes (`prefix_determines_stabilized`), and `metric_eps_limit` / `metric_eps_limit_determines` prove that any sequence of protocol sets achieving $\text{dist}(q(h_1), q(h_2)) \le \text{tol}$ for all $\text{tol}$ determines $q$ in the union limit.
- **C3, adaptivity gap.** `adaptive_uses_determining`, `adaptive_min_protocols_lb`, `adaptive_trace_discriminates`, and `adaptive_local_hitting_lb` (Lean) prove any accurate `QueryTree` must use a determining protocol set whose distinct protocol count is at least the minimum global hitting-set size, while each hypothesis's adaptive trace hits all local conflicts (separating local certificate complexity from global hitting number).
- **C4, compositional frames.** *PROVED in Lean (`prod_indist`, `prod_determines`, `prod_decisive_left`, `profile_factor_compile`):* for a product of frames, indistinguishability, determinacy, decisive protocols, and observational-profile factorization decompose cleanly across components (`cerp/ur_compiler.py`).
- **C6, reach vs choice (withdrawn in its strong form, Spike 10c F3).** The conjecture was that any two rules that fit a task choose the same completions. Hand-written error-driven rules do (Spike 10b), but meta-learned rules with terms acting directly on the weights fit equally well and choose a cheapest completion far less often (72–84% against 96%). Revised form: the completion distribution is fixed by the architecture and initialization only for rules whose first-layer update is driven by the error alone.
- **C7, minimal observational power for learning.** For each element of the atlas there is a least observational power (and symmetry group) whose dictionary contains a rule that learns it. Power A is excluded by Theorem 12. Spike 10c: a broadcast error with permutation symmetry suffices for all 222 four-input elements (order 2, 7 terms). Whether the orthogonal or signed-permutation dictionaries suffice is open; search found 41 and 24 elements, which are lower bounds.
- **C5, trust-indexed escalation.** *PROVED in Lean (`Theory.lean` §15: `threshold_escalation_optimal`, `threshold_escalation_unique_strict`):* given per-claim cost and impact, the threshold policy `0 < impact - ratio * cost` maximizes total net benefit over all escalation policies on any finite claim list and is unique on all non-tie claims.

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
- The frame does not capture every epistemic situation. Probabilistic protocols, costs and partial observation are only partly covered: C1 and C3 have partial Lean results (§5) but remain open in general.
- The formalized theorems say nothing about the real world beyond their hypotheses. Whether an empirical setup is a protocol frame with exact observations is an empirical claim with its own warrant.


---

## 7. Quantitative Morphisms, Markov Contraction, Interpretant & Ville Bounds, and Verified Networks (2026-11-13 Update)

The Lean 4 formalization (`proofs/lean/Theory.lean` §§17–19 and `proofs/lean/Cerp.lean` Part D, checked cleanly in `Lean 4.12.0` under standard axioms `{propext, Classical.choice, Quot.sound}`) and Spike 16 experiments extend Sections 2–5 in four directions while clarifying hard combinatorial and empirical barriers:

### 7.1 Indexed Protocol-Frame Morphisms & Lossy-Composition Obstruction (`Theory.lean` §17, P071)
For indexed protocol frames `(Φ₁, Φ₂)` and morphisms `FrameHom`:
- **`frameHom_indist`, `frameHom_determines_pullback`**: Exact query determinacy pulls back contravariantly along protocol-preserving morphisms.
- **`queryApprox_comp`, `frameHom_eps_determines_pullback`, `frameHom_eps_metric_pullback`**: Quantitative `ε`-determinacy (`EpsDetermines`) composes additively (`ε₁ + ε₂`) across stacked abstractions/metrics and pulls back along `FrameHom`.
- **`lossy_composition_obstruction`**: An explicit 3-point finite protocol system witnesses that exact query loss across coarse abstraction stages creates non-trivial indeterminacy that cannot be recovered locally without enriching $\Omega$ (motivating sheaf/cohomological obstruction invariants as future work).

### 7.2 Constructive Finite Markov-Kernel Data-Processing Contraction (`Theory.lean` §18, P072)
Using explicit finite rational/real discrete distributions over `Fin n`:
- **`tv_deterministic_dpi`**: Deterministic pushforward maps never increase total-variation distance.
- **`markov_kernel_dpi`, `markov_kernel_dpi_comp`**: Finite stochastic Markov kernels satisfy $D_{\mathrm{TV}}(K \mu, K \nu) \le D_{\mathrm{TV}}(\mu, \nu)$ and compose inductively across multi-step transitions (`T-step-TV` grounding the Ur-Compiler's `stochastic_lts` approximation bounds without Mathlib measure theory).

### 7.3 Peircean Triadic Semiosis & Anytime-Valid Ville/Optional Stopping (`Theory.lean` §19, P073)
- **`indist_implies_pragEquiv`, `peirce_pragmatic_maxim`**: With signs `rep : P → H → S` and an interpretant `interp : P → S → Act`, objects indistinguishable by their signs are indistinguishable in practical consequence, and a query determined through the interpretant is determined by the signs. Only this direction is proved: the converse needs `interp` to be injective on the relevant signs. Both facts follow from Theorem 3 and congruence; the Peircean reading is an interpretation, not extra mathematics (corrected by the 2026-11-17 audit).
- **`applyStop_preserves_supermartingale`, `optional_stopping_supermartingale`, `ville_anytime_valid_bound`**: Over finite horizons `T`, any adapted causal stopping policy preserves the discrete nonnegative supermartingale property and obeys Ville's anytime-valid inequality ($\mathbb{P}(\max_{t \le T} M_t \ge \alpha) \le \mathbb{E}[M_0]/\alpha$). Connecting concrete `cerp/epistemics/` empirical tests directly to instances of `ville_anytime_valid_bound` remains an open bridge.

### 7.4 Verified Integer-Weight `ThresholdNet` Emission (`Cerp.lean` Part D, P074–P075)
- `Cerp.lean` Part D defines executable integer-weight linear-threshold DAGs (`TNode`, `evalTNet`, `tnetScoped`) and verifies compiler outputs against canonical `Expr` specs via both exhaustive kernel checking (`decideTNetEquivExpr_correct`) and linear-time LRAT hint-indexed Tseitin miters (`tseitinTNetMiter_lrat_unsat_implies_equiv`, Python bridge `prove_tnet_equivalence_lrat` + `verify_threshold_net_equiv`).
- **Measured scaling bottleneck:** `pbToExpr` expands a fan-in-`d` threshold neuron using an exponential $O(2^d)$ Shannon `ite` tree. Consequently, pure-kernel `by decide` passes `xor3` (4 `TNode`s, 173 clauses, 8 LRAT steps) in `219.37s` but times out (`>900s`) on `xor4` (5 `TNode`s, 431 clauses, 16 LRAT steps), where `native_decide` succeeds in `14.78s`. A linear $O(d \cdot w)$ binary-adder pseudo-Boolean encoding in `Cerp.lean` is required before kernel LRAT net verification scales to high-fan-in multi-layer networks.

### 7.5 Spike 16 Empirical Corrections & Negative Results (P076–P078)
- **Local rule variance (`test_localrules.py`):** The `0.875 < 0.9` score on `rng(1)` gen 3 (deterministic on Linux, not intermittent) reflects initialization variance of pure backprop (`mean=0.9521`, `min=0.875` over 20 seeds), not CEM dropping backprop (`a[bp]=1.0`). The test now compares the returned rule with backprop on the same fresh networks (audit B1).
- **Width coarsening (`H-A` vs `H-D`, $n=8$):** Single-unit alignment fades with width (`0.3713` at $W=8 \to 0.3062$ at $W=32$) while linear subspace $R^2$ climbs to `0.9850` (`SPIKE_16_REPORT.md` §2).
- **`XOR6` (`H-C`) & `parity5` (`H-E`):** `32/64` fails to grok (`0/9` seeds up to 3,000 steps); at `48/64`, unregularized Adam reaches `0.9375` while `wd=0.01` exhibits anti-parity collapse (`0.2292`). Bounded-weight CP-SAT (`|w| <= 4`) verifies `chain(5,3)` (`3` neurons, `sat` `0.596s`) vs depth-2 `[3,1]` (`4` neurons, `unsat` `17.539s`), and `[3,1]` `unsat` for `parity4` (`13.985s`), leaving unbounded $\mathbb{R}^4$ Lean mechanization of `parity4 >= 5` open past the $\binom{1882}{3}$ enumeration barrier.
