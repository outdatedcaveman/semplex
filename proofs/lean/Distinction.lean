/-!
Spike 17 — Distinction admissibility, quotienting, and identity.
Lean core only. This file isolates elementary structural lemmas from the
four-system comparison. It does not claim to derive the rules of classical
logic, linear logic, or dependent type theory from one axiom.
-/
namespace Distinction
universe u v w
variable {X : Type u} {Y : Type v} {A : Type w}

/-- A transformation preserves an observable iff equal outputs cannot hide different observable values. -/
def Preserves (T : X → Y) (q : X → A) : Prop :=
  ∀ ⦃x x'⦄, T x = T x' → q x = q x'

/-- The kernel equivalence of a representation/abstraction map. -/
def kernelSetoid (T : X → Y) : Setoid X where
  r x x' := T x = T x'
  iseqv := {
    refl := by intro x; rfl
    symm := by intro x y h; exact h.symm
    trans := by intro x y z hxy hyz; exact hxy.trans hyz
  }

/-- An observable descends to the quotient exactly when it is constant on every fiber. -/
def Descends (R : Setoid X) (q : X → A) : Prop :=
  ∀ x x', R.r x x' → q x = q x'

def inducedObservable (R : Setoid X) (q : X → A) (h : Descends R q) : Quotient R → A :=
  Quotient.lift q (by intro x x' hxx'; exact h x x' hxx')

theorem inducedObservable_mk (R : Setoid X) (q : X → A) (h : Descends R q) (x : X) :
    inducedObservable R q h (Quotient.mk R x) = q x := by rfl

theorem quotient_factorization_criterion (T : X → Y) (q : X → A) :
    Descends (kernelSetoid T) q ↔ Preserves T q := by rfl

/-- A binary operation respects R in both arguments: the congruence obligation. -/
def BinaryCongruence (R : Setoid X) (op : X → X → X) : Prop :=
  ∀ a a' b b', R.r a a' → R.r b b' → R.r (op a b) (op a' b')

def UnaryCongruence (R : Setoid X) (op : X → X) : Prop :=
  ∀ a a', R.r a a' → R.r (op a) (op a')

def quotientUnaryOp (R : Setoid X) (op : X → X) (h : UnaryCongruence R op) : Quotient R → Quotient R :=
  Quotient.lift (fun a => Quotient.mk R (op a))
    (by
      intro a a' haa'
      exact Quotient.sound (h a a' haa'))

theorem quotientUnaryOp_mk (R : Setoid X) (op : X → X) (h : UnaryCongruence R op) (a : X) :
    quotientUnaryOp R op h (Quotient.mk R a) = Quotient.mk R (op a) := by rfl

/-- Equality substitution is elimination for the identity type Eq. -/
theorem substitution_of_identity {a b : X} (h : a = b) (P : X → Prop) (ha : P a) : P b := by
  cases h
  exact ha

def Supplies (available required : Nat) : Prop := required ≤ available

theorem linear_contraction_counterexample : Supplies 2 2 ∧ ¬ Supplies 1 2 := by
  change 2 ≤ 2 ∧ ¬ 2 ≤ 1
  decide

theorem unrestricted_resource_can_supply (n : Nat) : Supplies n n := Nat.le_refl n

/-- Module-indexed indistinguishability under a declared observation family. -/
def ModuleIndist (P : Type u) (O : Type v) (obs : P → X → O)
    (module : P → Prop) (x y : X) : Prop :=
  ∀ p, module p → obs p x = obs p y

theorem moduleIndist_equivalence (P : Type u) (O : Type v) (obs : P → X → O) (module : P → Prop) :
    (∀ x, ModuleIndist P O obs module x x) ∧
    (∀ x y, ModuleIndist P O obs module x y → ModuleIndist P O obs module y x) ∧
    (∀ x y z, ModuleIndist P O obs module x y → ModuleIndist P O obs module y z →
      ModuleIndist P O obs module x z) := by
  constructor
  · intro x p hp; rfl
  constructor
  · intro x y h p hp; exact (h p hp).symm
  · intro x y z hxy hyz p hp; exact (hxy p hp).trans (hyz p hp)

/-- Adding observations refines indistinguishability. -/
theorem module_refinement (P : Type u) (O : Type v) (obs : P → X → O)
    {M N : P → Prop} (hMN : ∀ p, M p → N p) (x y : X) :
    ModuleIndist P O obs N x y → ModuleIndist P O obs M x y := by
  intro h p hp
  exact h p (hMN p hp)
end Distinction


/-! ## First-order syntax and Tarski satisfaction invariance

A deliberately small first-order language with variables, constants, equality,
unary predicates, falsity, implication, and universal quantification. The
satisfaction theorem is proved from the recursive semantics, not tested by
enumerating selected assignments.
-/
namespace FirstOrder

universe u

inductive Term where
  | var : Nat → Term
  | const : Nat → Term
  deriving DecidableEq

def Term.free : Term → Nat → Prop
  | .var n, v => n = v
  | .const _, _ => False

def Term.eval {α : Type u} (constants : Nat → α) (s : Nat → α) : Term → α
  | .var n => s n
  | .const c => constants c

def AgreeOn {α : Type u} (P : Nat → Prop) (s s' : Nat → α) : Prop :=
  ∀ v, P v → s v = s' v

theorem Term.eval_agree {α : Type u} (constants : Nat → α) (t : Term)
    {s s' : Nat → α} (h : ∀ v, Term.free t v → s v = s' v) :
    Term.eval constants s t = Term.eval constants s' t := by
  cases t with
  | var n => exact h n rfl
  | const c => rfl

def update {α : Type u} (s : Nat → α) (x : Nat) (a : α) : Nat → α :=
  fun y => if y = x then a else s y

theorem agreeOn_update {α : Type u} (P : Nat → Prop) (s s' : Nat → α)
    (x : Nat) (a : α)
    (h : AgreeOn (fun v => v ≠ x ∧ P v) s s') :
    AgreeOn P (update s x a) (update s' x a) := by
  intro v hv
  by_cases hvx : v = x
  · subst v
    simp [update]
  · simp [update, hvx]
    exact h v ⟨hvx, hv⟩

inductive Formula where
  | equal : Term → Term → Formula
  | pred : Nat → Term → Formula
  | falsum : Formula
  | imp : Formula → Formula → Formula
  | all : Nat → Formula → Formula
  | ex : Nat → Formula → Formula

def Formula.free : Formula → Nat → Prop
  | .equal t u, v => Term.free t v ∨ Term.free u v
  | .pred _ t, v => Term.free t v
  | .falsum, _ => False
  | .imp φ ψ, v => Formula.free φ v ∨ Formula.free ψ v
  | .all x φ, v => v ≠ x ∧ Formula.free φ v
  | .ex x φ, v => v ≠ x ∧ Formula.free φ v

structure Interpretation (α : Type u) where
  constants : Nat → α
  predicates : Nat → α → Prop

def Formula.sat {α : Type u} (I : Interpretation α) (s : Nat → α) :
    Formula → Prop
  | .equal t u => Term.eval I.constants s t = Term.eval I.constants s u
  | .pred p t => I.predicates p (Term.eval I.constants s t)
  | .falsum => False
  | .imp φ ψ => Formula.sat I s φ → Formula.sat I s ψ
  | .all x φ => ∀ a, Formula.sat I (update s x a) φ
  | .ex x φ => ∃ a, Formula.sat I (update s x a) φ

theorem satisfaction_depends_only_on_free_variables
    {α : Type u} (I : Interpretation α) (φ : Formula) :
    ∀ s s', AgreeOn (Formula.free φ) s s' →
      (Formula.sat I s φ ↔ Formula.sat I s' φ) := by
  induction φ with
  | equal t u =>
      intro s s' h
      change
        (Term.eval I.constants s t = Term.eval I.constants s u) ↔
        (Term.eval I.constants s' t = Term.eval I.constants s' u)
      have ht : Term.eval I.constants s t = Term.eval I.constants s' t :=
        Term.eval_agree I.constants t (fun v hv => h v (Or.inl hv))
      have hu : Term.eval I.constants s u = Term.eval I.constants s' u :=
        Term.eval_agree I.constants u (fun v hv => h v (Or.inr hv))
      rw [ht, hu]
  | pred p t =>
      intro s s' h
      change
        I.predicates p (Term.eval I.constants s t) ↔
        I.predicates p (Term.eval I.constants s' t)
      have ht : Term.eval I.constants s t = Term.eval I.constants s' t :=
        Term.eval_agree I.constants t h
      rw [ht]
  | falsum =>
      intro s s' h
      rfl
  | imp φ ψ ihφ ihψ =>
      intro s s' h
      change
        (Formula.sat I s φ → Formula.sat I s ψ) ↔
        (Formula.sat I s' φ → Formula.sat I s' ψ)
      have hφ : AgreeOn (Formula.free φ) s s' :=
        fun v hv => h v (Or.inl hv)
      have hψ : AgreeOn (Formula.free ψ) s s' :=
        fun v hv => h v (Or.inr hv)
      have eφ := ihφ s s' hφ
      have eψ := ihψ s s' hψ
      constructor
      · intro hImp hSat
        exact eψ.mp (hImp (eφ.mpr hSat))
      · intro hImp hSat
        exact eψ.mpr (hImp (eφ.mp hSat))
  | all x φ ih =>
      intro s s' h
      change
        (∀ a, Formula.sat I (update s x a) φ) ↔
        (∀ a, Formula.sat I (update s' x a) φ)
      constructor
      · intro hSat a
        apply (ih (update s x a) (update s' x a)
          (agreeOn_update (Formula.free φ) s s' x a h)).mp
        exact hSat a
      · intro hSat a
        apply (ih (update s x a) (update s' x a)
          (agreeOn_update (Formula.free φ) s s' x a h)).mpr
        exact hSat a


  | ex x φ ih =>
      intro s s' h
      change
        (∃ a, Formula.sat I (update s x a) φ) ↔
        (∃ a, Formula.sat I (update s' x a) φ)
      constructor
      · rintro ⟨a, ha⟩
        refine ⟨a, ?_⟩
        exact (ih (update s x a) (update s' x a)
          (agreeOn_update (Formula.free φ) s s' x a h)).mp ha
      · rintro ⟨a, ha⟩
        refine ⟨a, ?_⟩
        exact (ih (update s x a) (update s' x a)
          (agreeOn_update (Formula.free φ) s s' x a h)).mpr ha

/-- A finite list of assumptions is satisfied by an assignment. -/
def ContextSat {α : Type u} (I : Interpretation α)
    (s : Nat → α) (Γ : List Formula) : Prop :=
  ∀ ψ, ψ ∈ Γ → Formula.sat I s ψ

/-- A context not mentioning x remains satisfied when x's assignment is changed. -/
theorem contextSat_update_fresh {α : Type u} (I : Interpretation α)
    (Γ : List Formula) (s : Nat → α) (x : Nat) (a : α)
    (hFresh : ∀ ψ, ψ ∈ Γ → ¬ Formula.free ψ x)
    (hΓ : ContextSat I s Γ) :
    ContextSat I (update s x a) Γ := by
  intro ψ hψ
  have hAgree : AgreeOn (Formula.free ψ) s (update s x a) := by
    intro v hv
    by_cases hvx : v = x
    · subst v
      exact False.elim (hFresh ψ hψ hv)
    · simp [update, hvx]
  have hInvariant :=
    satisfaction_depends_only_on_free_variables I ψ s (update s x a) hAgree
  exact hInvariant.mp (hΓ ψ hψ)

/-- Semantic soundness of universal introduction with its eigenvariable side condition. -/
theorem forall_intro_fresh_sound {α : Type u} (I : Interpretation α)
    (Γ : List Formula) (φ : Formula) (x : Nat)
    (hFresh : ∀ ψ, ψ ∈ Γ → ¬ Formula.free ψ x)
    (hDerive : ∀ s, ContextSat I s Γ → Formula.sat I s φ) :
    ∀ s, ContextSat I s Γ → Formula.sat I s (.all x φ) := by
  intro s hΓ
  change ∀ a, Formula.sat I (update s x a) φ
  intro a
  apply hDerive (update s x a)
  exact contextSat_update_fresh I Γ s x a hFresh hΓ


/-- Semantic soundness of existential elimination with a fresh eigenvariable.

The eigenvariable may occur in the temporary witness assumption, but must not
occur free in the persistent context or the conclusion. -/
theorem exists_elim_fresh_sound {α : Type u} (I : Interpretation α)
    (Γ : List Formula) (φ ψ : Formula) (x : Nat)
    (hFreshContext : ∀ χ, χ ∈ Γ → ¬ Formula.free χ x)
    (hFreshConclusion : ¬ Formula.free ψ x)
    (hMinor : ∀ s, ContextSat I s (φ :: Γ) → Formula.sat I s ψ) :
    ∀ s, ContextSat I s Γ → Formula.sat I s (.ex x φ) →
      Formula.sat I s ψ := by
  intro s hΓ hExists
  rcases hExists with ⟨witness, hWitness⟩
  have hΓ' := contextSat_update_fresh I Γ s x witness hFreshContext hΓ
  have hMinorContext : ContextSat I (update s x witness) (φ :: Γ) := by
    intro χ hχ
    rcases List.mem_cons.mp hχ with hEq | hIn
    · cases hEq
      exact hWitness
    · exact hΓ' χ hIn
  have hConclusion := hMinor (update s x witness) hMinorContext
  have hAgree : AgreeOn (Formula.free ψ) (update s x witness) s := by
    intro v hv
    by_cases hvx : v = x
    · subst v
      exact False.elim (hFreshConclusion hv)
    · simp [update, hvx]
  have hInvariant :=
    satisfaction_depends_only_on_free_variables I ψ
      (update s x witness) s hAgree
  exact hInvariant.mp hConclusion

/-- Existential introduction is witnessed by an element of the interpreted domain. -/
theorem exists_intro_semantic {α : Type u} (I : Interpretation α)
    (s : Nat → α) (x : Nat) (φ : Formula) (witness : α)
    (h : Formula.sat I (update s x witness) φ) :
    Formula.sat I s (.ex x φ) :=
  ⟨witness, h⟩

/-- A nonempty domain supplies a witness for universal-to-existential import. -/
theorem forall_implies_exists {α : Type u} (P : α → Prop) (witness : α)
    (h : ∀ x, P x) : ∃ x, P x :=
  ⟨witness, h witness⟩

/-- A constant symbol has an existential witness because its interpretation is an element. -/
theorem constant_has_existential_denotation {α : Type u}
    (constants : Nat → α) (c : Nat) : ∃ x, x = constants c :=
  ⟨constants c, rfl⟩

/-- Empty-domain countermodel: the universal is vacuously true, the existential false. -/
theorem empty_domain_existential_import_failure :
    (∀ x : Empty, False) ∧ ¬ (∃ x : Empty, False) := by
  constructor
  · intro x
    cases x
  · intro h
    rcases h with ⟨x, _⟩
    cases x

end FirstOrder

/-! ## Resource-sensitive contraction fragment

The Boolean persistent flag is a minimal model of an unrestricted/! resource.
It is intentionally not presented as a complete linear-logic calculus.
-/
namespace Resources

structure Context where
  linear : Nat
  persistent : Bool
  deriving DecidableEq

def CanSupply (Γ : Context) (required : Nat) : Prop :=
  Γ.persistent = true ∨ required ≤ Γ.linear

def contractLinear (Γ : Context) : Context :=
  { Γ with linear := Γ.linear - 1 }

theorem linear_contraction_counterexample :
    CanSupply ⟨2, false⟩ 2 ∧ ¬ CanSupply (contractLinear ⟨2, false⟩) 2 := by
  simp [CanSupply, contractLinear]

theorem persistent_context_survives_contraction (n required : Nat) :
    CanSupply (contractLinear ⟨n, true⟩) required := by
  simp [CanSupply, contractLinear]

theorem linear_contraction_safe_with_surplus (n required : Nat)
    (h : required ≤ n - 1) :
    CanSupply (contractLinear ⟨n, false⟩) required := by
  exact Or.inr h


/-! ### Occurrence-sensitive resources

Unlike the earlier Boolean context flag, this model records individual token
identities, proposition labels, resource modes, and provenance. It remains a
small capacity semantics, not a sequent calculus for linear logic.
-/

inductive ResourceMode where
  | linear
  | persistent
  deriving DecidableEq, BEq, Repr

structure ResourceOccurrence where
  token : Nat
  formula : Nat
  mode : ResourceMode
  origins : List Nat
  deriving DecidableEq, Repr

def linearCount (Γ : List ResourceOccurrence) (A : Nat) : Nat :=
  (Γ.filter fun o => o.formula == A && o.mode == .linear).length

def hasPersistent (Γ : List ResourceOccurrence) (A : Nat) : Bool :=
  Γ.any fun o => o.formula == A && o.mode == .persistent

def supports (Γ : List ResourceOccurrence) (A demand : Nat) : Prop :=
  hasPersistent Γ A = true ∨ demand ≤ linearCount Γ A

def mergePersistent (a b : ResourceOccurrence) : ResourceOccurrence :=
  { token := a.token
    formula := a.formula
    mode := .persistent
    origins := a.origins ++ b.origins }

def mergeLinear (a b : ResourceOccurrence) : ResourceOccurrence :=
  { token := a.token
    formula := a.formula
    mode := .linear
    origins := a.origins ++ b.origins }

/-- Contracting two persistent occurrences of the same formula preserves
support for every formula and every finite demand. -/
theorem persistent_contraction_preserves_support
    (Γ : List ResourceOccurrence) (a b : ResourceOccurrence)
    (hFormula : a.formula = b.formula)
    (ha : a.mode = .persistent) (hb : b.mode = .persistent)
    (A demand : Nat) :
    supports (Γ ++ [a, b]) A demand ↔
      supports (Γ ++ [mergePersistent a b]) A demand := by
  cases a with
  | mk aToken aFormula aMode aOrigins =>
    cases b with
    | mk bToken bFormula bMode bOrigins =>
      simp_all [supports, hasPersistent, linearCount, mergePersistent, ResourceMode]

/-- Persistent contraction preserves the complete recorded provenance list. -/
theorem mergePersistent_preserves_origin_count
    (a b : ResourceOccurrence) :
    (mergePersistent a b).origins.length =
      a.origins.length + b.origins.length := by
  simp [mergePersistent]

/-- Two distinct linear occurrences can jointly satisfy a two-use demand,
but their one-token contraction cannot. -/
theorem linear_contraction_counterexample_occurrences (A : Nat) :
    let a : ResourceOccurrence := ⟨1, A, .linear, [1]⟩
    let b : ResourceOccurrence := ⟨2, A, .linear, [2]⟩
    a.token ≠ b.token ∧
      supports [a, b] A 2 ∧
      ¬ supports [mergeLinear a b] A 2 := by
  change 1 ≠ 2 ∧ (false = true ∨ 2 ≤ 2) ∧ ¬ (false = true ∨ 2 ≤ 1)
  decide


end Resources


/-! ## Binary quotient operations: sufficiency and necessity of congruence -/
namespace QuotientOperations

universe u

variable {X : Type u} (R : Setoid X)

def BinaryCongruence (op : X → X → X) : Prop :=
  ∀ a a' b b', R.r a a' → R.r b b' → R.r (op a b) (op a' b')

def inducedBinary (op : X → X → X) (h : BinaryCongruence R op) :
    Quotient R → Quotient R → Quotient R :=
  Quotient.lift₂
    (fun a b => Quotient.mk R (op a b))
    (by
      intro a b a' b' haa' hbb'
      exact Quotient.sound (h a a' b b' haa' hbb'))

theorem inducedBinary_mk (op : X → X → X) (h : BinaryCongruence R op)
    (a b : X) :
    inducedBinary R op h (Quotient.mk R a) (Quotient.mk R b) =
      Quotient.mk R (op a b) := by
  rfl

/-- Any operation on the quotient commuting with the quotient map forces congruence. -/
theorem congruence_necessary
    (op : X → X → X)
    (opbar : Quotient R → Quotient R → Quotient R)
    (commutes : ∀ a b,
      opbar (Quotient.mk R a) (Quotient.mk R b) =
        Quotient.mk R (op a b)) :
    BinaryCongruence R op := by
  intro a a' b b' haa' hbb'
  apply Quotient.exact
  calc
    Quotient.mk R (op a b) =
        opbar (Quotient.mk R a) (Quotient.mk R b) :=
      (commutes a b).symm
    _ = opbar (Quotient.mk R a') (Quotient.mk R b') := by
      rw [Quotient.sound haa', Quotient.sound hbb']
    _ = Quotient.mk R (op a' b') := commutes a' b'

end QuotientOperations


/-! ## A typed Distinction Admissibility contract

The contract protects a declared family of observations and total unary/binary
operations. It is intentionally scoped: it does not yet cover partial,
higher-order, stochastic, stateful, or effectful operations.
-/
namespace Admissibility

universe u v w

structure Interface (X : Type u) where
  Observation : Type v
  ObservationValue : Observation → Type w
  observe : (i : Observation) → X → ObservationValue i
  UnaryOperation : Type v
  unary : UnaryOperation → X → X
  BinaryOperation : Type v
  binary : BinaryOperation → X → X → X

structure Contract {X : Type u} (I : Interface X) (R : Setoid X) : Prop where
  observation_preservation :
    ∀ i x y, R.r x y → I.observe i x = I.observe i y
  unary_compatibility :
    ∀ f, Distinction.UnaryCongruence R (I.unary f)
  binary_compatibility :
    ∀ f, QuotientOperations.BinaryCongruence R (I.binary f)

/-- Every protected observation descends to the quotient. -/
def descendObservation {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (i : I.Observation) : Quotient R → I.ObservationValue i :=
  Quotient.lift (I.observe i)
    (by
      intro x y hxy
      exact h.observation_preservation i x y hxy)

/-- Every protected unary operation descends to the quotient. -/
def descendUnary {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (f : I.UnaryOperation) : Quotient R → Quotient R :=
  Quotient.lift (fun x => Quotient.mk R (I.unary f x))
    (by
      intro x y hxy
      exact Quotient.sound (h.unary_compatibility f x y hxy))

/-- Every protected binary operation descends to the quotient. -/
def descendBinary {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (f : I.BinaryOperation) :
    Quotient R → Quotient R → Quotient R :=
  Quotient.lift₂ (fun x y => Quotient.mk R (I.binary f x y))
    (by
      intro x y x' y' hxx' hyy'
      exact Quotient.sound (h.binary_compatibility f x x' y y' hxx' hyy'))

theorem descendObservation_mk {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (i : I.Observation) (x : X) :
    descendObservation I R h i (Quotient.mk R x) = I.observe i x := by
  rfl

theorem descendUnary_mk {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (f : I.UnaryOperation) (x : X) :
    descendUnary I R h f (Quotient.mk R x) =
      Quotient.mk R (I.unary f x) := by
  rfl

theorem descendBinary_mk {X : Type u} (I : Interface X) (R : Setoid X)
    (h : Contract I R) (f : I.BinaryOperation) (x y : X) :
    descendBinary I R h f (Quotient.mk R x) (Quotient.mk R y) =
      Quotient.mk R (I.binary f x y) := by
  rfl

end Admissibility
