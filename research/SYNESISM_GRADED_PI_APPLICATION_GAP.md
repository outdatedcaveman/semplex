# The missing application rule in P0FullTyping: a graded dependent function type

**Status:** formal diagnosis and proposed repair; not implemented or machine-checked.  
**Source module:** Synesism P0FullTyping.agda (M265), with usage law from M263/M264.

## 1. Exact gap

The current type constructor is:

    piT : (n : Nat) -> FullTy (Γ ▸ n) -> FullTy Γ

The lambda rule receives a body derivation with usage vector u and returns a function whose free-variable usage is popU u:

    (Γ ▸ n) ⊩ b ∈ B ∥ u
    -----------------------------
    Γ ⊩ lam n b ∈ piT n B ∥ popU u

But popU removes the bound-variable coordinate. The type piT n B stores the variable's rank and dependent codomain, not the multiplicity q = headU u with which the body uses the bound variable.

The syntax has an app constructor, but P0FullTyping has no application typing rule. Its betaPreservesTyping theorem is the telescoped substitution theorem applied to the body and argument; it types the contractum instFullAt ε b a. It does not establish subject reduction from a typed application redex, because no application redex is typable in the current relation.

This is not a cosmetic omission. The resource usage of the contractum is:

    dropAt ε u +ᵁ (countAt ε u ·ᵁ ua)

where ua is the argument's usage vector. Since countAt ε u is the multiplicity of the bound variable, an application rule needs that multiplicity. The current piT has erased it.

A naive rule that assigns app f a usage uf +ᵁ ua is correct only when the function uses its argument exactly once. It is wrong for the k=0 and k=2 cases already exhibited in M264.

## 2. Proposed graded Π

Extend the dependent function type with a usage grade q:

    piT : (q : Nat) -> (n : Nat) -> FullTy (Γ ▸ n) -> FullTy Γ

Read piT q n B as a function that uses its argument q times.

A first approximation is to retain the bound-variable coordinate as q and scale argument usage by q. However, this is not yet a faithful QTT rule: Atkey's system distinguishes the *computational relevance* σ ∈ {0,1} of a term from the semiring grade q describing how many times an argument may be used. C-20 currently has no such σ index.

A faithful QTT-style extension should use judgments of the form Γ ⊩ t : A [σ] ∥ u, with σ ∈ {0,1}, and enforce zero usage for erased terms. Its rule shape is:

    (Γ ▸ (σ · q)) ⊩ b ∈ B [σ] ∥ u
    ----------------------------------------------------
    Γ ⊩ lam^q n b ∈ piT q n B [σ] ∥ popU u

    Γ1 ⊩ f ∈ piT q n B [σ] ∥ uf
    Γ2 ⊩ a ∈ base n [σ'] ∥ ua
    0Γ1 = 0Γ2
    σ' = 0  iff  (q = 0 or σ = 0)
    ----------------------------------------------------
    Γ1 +ᵁ (q ·ᵁ Γ2) ⊩ app f a ∈ instTyFull ε B a [σ]
      ∥ (uf +ᵁ (q ·ᵁ ua))

Here q belongs to the usage semiring (choose Nat for the current finite-count model), while σ records whether the term has computational content. The positivity and zero-product conditions on the semiring are part of Atkey's substitution-admissibility argument.

The grade q is not a new resource count. In the computational fragment σ = 1, it is the bound-variable coordinate already computed by M263's usage semantics, now retained in the function type rather than discarded by abstraction. For σ = 0, the body uses the bound variable zero times regardless of the declared Pi grade, so q cannot be inferred from headU u; the lambda syntax must carry q explicitly. Both the σ index and this grade annotation are syntax extensions not present in current C-20.

## 3. Why this gives beta subject reduction

For a computational term (σ = 1), take a body derivation:

    (Γ ▸ n) ⊩ b ∈ B [1] ∥ u

The graded lambda rule assigns q = headU u and yields:

    Γ ⊩ lam^q n b ∈ piT q n B [1] ∥ popU u

If q > 0, the QTT application side condition requires a computational argument (σ' = 1), with usage ua. The redex then has usage:

    popU u +ᵁ (q ·ᵁ ua)

The existing substitution theorem gives the contractum usage:

    dropAt ε u +ᵁ (countAt ε u ·ᵁ ua)

If q = 0, the QTT application side condition instead requires an erased argument (σ' = 0). By the zero-needs-nothing property, its usage is ua = 0, so the redex and contractum both have usage popU u. Thus the k=0 case with a nonzero-resource argument is not a well-typed QTT application; it is a negative test against a naive ungraded rule.

In both admissible cases, the vectors agree by the epsilon-telescope identities:

    popU u = dropAt ε u
    headU u = countAt ε u

Therefore beta subject reduction follows for the graded QTT-style relation, provided the typing and substitution side conditions are proved. This is a real subject-reduction theorem for typable redexes, unlike the current contractum-only theorem.

## 4. How the M264 examples fit

- q = 0: the function ignores the argument; QTT requires the argument to be in the erased fragment (σ' = 0), hence its usage vector is zero. A computational argument with nonzero resources is rejected.
- q = 1: the function uses a computational argument once; beta preserves its usage vector.
- q = 2: the function duplicates a computational argument; the application rule scales its usage by two, matching beta substitution.

The M264 q=0 witness with a nonzero-resource argument is therefore a counterexample to an ungraded application rule, not a well-typed QTT redex. The distinction between a term's computational relevance σ and its resource vector u must be explicit.

## 5. Relation to prior art

This proposed rule is a direct fragment of established Quantitative Type Theory, not a new graded-Pi idea. Atkey (LICS 2018, §2) already defines dependent function types (x π : S) → T whose grade π records argument multiplicity; its application rule scales the argument's usage context by π and adds it to the function's context. The lambda rule constrains the bound-variable usage by the term relevance grade times π. Atkey proves an admissible substitution lemma (Lemma 2.5) under the QTT side conditions and gives quantitative categorical semantics (QCwFs). QTT also includes dependent tensor products and a richer usage discipline. The C-20 proposal is therefore a small mechanized reconstruction of a known QTT fragment, with the specific goal of repairing M265's lost multiplicity and deriving a genuine beta subject-reduction theorem. The q=0/1/2 witnesses should be used as regression cases against the QTT-style rules, not as novelty evidence.

## 6. Minimal implementation and proof sequence

1. Create a separate experimental module first; do not rewrite P0FullTyping until the extension is checked.
2. Define a QTT-style judgment with term relevance σ ∈ {0,1}; prove that σ=0 forces zero computational usage.
3. Extend GradedTy with dependent Π grade q while reusing M263's FullTm and Usage; make q explicit on lambda syntax because it cannot be inferred from an erased body.
4. Define graded type weakening and instantiation.
5. Add lambda and application rules with the QTT side condition σ' = 0 iff (q = 0 or σ = 0).
6. Use the natural-number semiring for the first fragment and record its positivity and zero-product properties.
7. Prove dropAt ε u = popU u and countAt ε u = headU u (or reuse existing identities).
8. Prove substitution preservation for the graded relation, adapting M265's substTyping and QTT Lemma 2.5's side conditions.
9. Derive application typing and a beta subject-reduction theorem with exact usage preservation.
10. Check q=1/2 computational arguments and q=0 erased arguments; explicitly reject the M264 q=0/nonzero-resource argument as ill-typed.
11. Only then decide whether to replace M265's ungraded piT or keep both as a historical fragment and a graded completion.

Do not call the current M265 result full subject reduction until an application typing rule exists.
