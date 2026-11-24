import OperationalReference

/-!
# Resource-relative syntax and satisfaction on operational referents

A claim is admissible at budget B exactly when it is invariant under
the intervention-response equivalence induced by that budget. Such claims
descend uniquely to predicates on the quotient referent space.
-/

namespace Cerp.OperationalSatisfaction

open Cerp.InterventionGrounding
open Cerp.OperationalReference

universe u v w x y

variable {S : Cerp.OperationalSemioticScaffold.OperationalScaffold.{u,v,w,x,y}}

/-- Claims expressible/evaluable at budget B must be invariant under all
    world distinctions that the available interventions cannot resolve. -/
structure ObservableClaim (P : InterventionProtocol S) (budget : Nat) where
  holds : S.World -> Prop
  invariant : forall w1 w2,
    experimentEquivalent P budget w1 w2 ->
      (holds w1 <-> holds w2)

/-- The semantics of an observable claim descends to the operational
    referent quotient. -/
def satisfaction (P : InterventionProtocol S) (budget : Nat)
    (claim : ObservableClaim P budget) :
    ReferentSpace P budget -> Prop :=
  Quotient.lift claim.holds (by
    intro w1 w2 h
    exact propext (claim.invariant w1 w2 h))

@[simp] theorem satisfaction_mk (P : InterventionProtocol S)
    (budget : Nat) (claim : ObservableClaim P budget) (world : S.World) :
    satisfaction P budget claim
      (Quotient.mk (worldSetoid P budget) world) = claim.holds world := rfl

/-- More interventions refine observational equivalence, so every
    low-budget observable claim remains observable at a higher budget. -/
def refineClaim (P : InterventionProtocol S) {b1 b2 : Nat}
    (hle : b1 <= b2) (claim : ObservableClaim P b1) :
    ObservableClaim P b2 where
  holds := claim.holds
  invariant := by
    intro w1 w2 h
    exact claim.invariant w1 w2
      (experimentEquivalent_antitone P hle h)

/-- Satisfaction commutes with forgetting a richer referent space to a
    poorer one. This is the central resource-relative syntax/semantics law. -/
theorem satisfaction_forget (P : InterventionProtocol S)
    {b1 b2 : Nat} (hle : b1 <= b2)
    (claim : ObservableClaim P b1)
    (q : ReferentSpace P b2) :
    satisfaction P b2 (refineClaim P hle claim) q <->
      satisfaction P b1 claim (forgetReferent P hle q) := by
  refine Quotient.inductionOn q ?_
  intro world
  rfl

/-- The descended satisfaction predicate is unique: any predicate on
    referent classes that agrees with the claim on every representative
    must equal the quotient semantics. -/
theorem satisfaction_unique (P : InterventionProtocol S)
    (budget : Nat) (claim : ObservableClaim P budget)
    (other : ReferentSpace P budget -> Prop)
    (hother : forall world,
      other (Quotient.mk (worldSetoid P budget) world) <-> claim.holds world) :
    forall q, other q <-> satisfaction P budget claim q := by
  intro q
  refine Quotient.inductionOn q ?_
  intro world
  rw [satisfaction_mk]
  exact hother world

/-- The hidden-bit claim is not observable before the reveal intervention. -/
def hiddenBitClaim : (Bool × Bool) -> Prop :=
  fun world => world.1 = true

theorem hiddenBit_not_observable_at_zero :
    ¬ exists c : ObservableClaim revealProtocol 0,
      c.holds = hiddenBitClaim := by
  rintro ⟨c, hc⟩
  have hinv := c.invariant (false, false) (true, false)
    hidden_worlds_indistinguishable_at_zero
  rw [hc] at hinv
  simp [hiddenBitClaim] at hinv

/-- After the reveal intervention is affordable, the hidden-bit claim
    becomes observable and therefore has a well-defined truth value on
    every operational referent class. -/
def hiddenBitObservableAtOne : ObservableClaim revealProtocol 1 where
  holds := hiddenBitClaim
  invariant := by
    intro w1 w2 h
    have hw := revealProtocol_separating_at_one w1 w2 h
    rw [hw]

end Cerp.OperationalSatisfaction
