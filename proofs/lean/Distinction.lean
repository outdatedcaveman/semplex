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
  iseqv := ⟨fun _ => rfl, fun _ _ h => h.symm, fun _ _ _ h₁ h₂ => h₁.trans h₂⟩

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
  Quotient.map op (by intro a a' haa'; exact h a a' haa')

theorem quotientUnaryOp_mk (R : Setoid X) (op : X → X) (h : UnaryCongruence R op) (a : X) :
    quotientUnaryOp R op h (Quotient.mk R a) = Quotient.mk R (op a) := by rfl

/-- Equality substitution is elimination for the identity type Eq. -/
theorem substitution_of_identity {a b : X} (h : a = b) (P : X → Prop) (ha : P a) : P b := by
  cases h
  exact ha

def Supplies (available required : Nat) : Prop := required ≤ available

theorem linear_contraction_counterexample : Supplies 2 2 ∧ ¬ Supplies 1 2 := by decide

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
