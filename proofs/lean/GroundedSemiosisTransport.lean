import OperationalGroundingAdequacy
import SemanticFibrations

/-!
# Lossless transport of grounded semiosis to operational profile space

The kernel of the external response-profile map defines a quotient of
external targets by observational indistinguishability. If affordable
probes separate targets, this quotient is equivalent to the external
target type. Any grounded semiosis structure (relational reference,
expression, satisfaction, evidence, and evidence soundness) therefore
transports losslessly to the operational profile quotient.
-/

namespace Cerp.GroundedSemiosisTransport

open Cerp.OperationalGroundingAdequacy
open Cerp.SemanticFibrations
open Cerp.HigherSemanticCore

universe u v w x

def profileSetoid
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) : Setoid External where
  r := fun e e' => ExternalProfileAt G budget e = ExternalProfileAt G budget e'
  iseqv := {
    refl := by intro e; rfl
    symm := by intro e e' h; exact h.symm
    trans := by intro e e' e'' h₁ h₂; exact h₁.trans h₂
  }

def ProfileWorld
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) :=
  Quotient (profileSetoid G budget)

/-- Injectivity of the external profile yields a strictly constructive quotient
    inverse using only quotient soundness (without `Classical.choice`). -/
def profileToExternalOfInjective
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hinj : ExternalProfileInjective G budget) :
    ProfileWorld G budget -> External :=
  Quotient.lift id (fun _ _ hprof => hinj hprof)

@[simp] theorem profileToExternalOfInjective_mk
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hinj : ExternalProfileInjective G budget) (e : External) :
    profileToExternalOfInjective G budget hinj
      (Quotient.mk (profileSetoid G budget) e) = e := rfl

/-- Under explicit profile injectivity, the profile quotient and external
    target type are equivalent using only quotient recursion (`[Quot.sound]`). -/
def externalProfileQuotientEquivOfInjective
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hinj : ExternalProfileInjective G budget) :
    HomBijection External (ProfileWorld G budget) where
  toFun := fun e => Quotient.mk (profileSetoid G budget) e
  invFun := profileToExternalOfInjective G budget hinj
  left_inv := by intro e; rfl
  right_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro e
    rfl

/-- Separation makes the external referent a well-defined function of its
    operational profile class. -/
def profileToExternal
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget) :
    ProfileWorld G budget -> External :=
  Quotient.lift id (by
    intro e e' hprof
    exact (externalProfile_injective_iff_separatesAt G budget).2 hsep hprof)

@[simp] theorem profileToExternal_mk
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget) (e : External) :
    profileToExternal G budget hsep
      (Quotient.mk (profileSetoid G budget) e) = e := rfl

/-- Under probe separation, the profile quotient and the external target
    type are equivalent. The quotient lift itself avoids choice, while
    converting `SeparatesAt` to `ExternalProfileInjective` uses classical
    contradiction (`externalProfile_injective_iff_separatesAt`); see
    `externalProfileQuotientEquivOfInjective` for the choice-free variant. -/
def externalProfileQuotientEquiv
    {System : Type u} {External : Type v} {Probe : Type w} {Outcome : Type x}
    (G : OperationalGrounding System External Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget) :
    HomBijection External (ProfileWorld G budget) where
  toFun := fun e => Quotient.mk (profileSetoid G budget) e
  invFun := profileToExternal G budget hsep
  left_inv := by intro e; rfl
  right_inv := by
    intro q
    refine Quotient.inductionOn q ?_
    intro e
    rfl

/-- Transport a fully grounded semiosis structure from external targets
    to their resource-bounded operational profile quotient. -/
def transportGroundedSemiosis
    (M : GroundedSemiosis)
    {System : Type u} {Probe : Type v} {Outcome : Type w}
    (G : OperationalGrounding System M.World Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget) :
    GroundedSemiosis where
  World := ProfileWorld G budget
  Sign := M.Sign
  Claim := M.Claim
  Context := M.Context
  refers := fun s p => M.refers s (profileToExternal G budget hsep p)
  expresses := M.expresses
  satisfies := fun claim p => M.satisfies claim (profileToExternal G budget hsep p)
  Evidence := fun s c p => M.Evidence s c (profileToExternal G budget hsep p)
  evidence_sound := by
    intro s c p href hev
    exact M.evidence_sound s c (profileToExternal G budget hsep p) href hev

theorem content_truth_preserved
    (M : GroundedSemiosis)
    {System : Type u} {Probe : Type v} {Outcome : Type w}
    (G : OperationalGrounding System M.World Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget)
    (s : M.Sign) (c : M.Context) (p : ProfileWorld G budget) :
    ContentTrue (transportGroundedSemiosis M G budget hsep) s c p ↔
      ContentTrue M s c (profileToExternal G budget hsep p) :=
  Iff.rfl

theorem grounded_assertion_truth_preserved
    (M : GroundedSemiosis)
    {System : Type u} {Probe : Type v} {Outcome : Type w}
    (G : OperationalGrounding System M.World Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget)
    (s : M.Sign) (c : M.Context) (p : ProfileWorld G budget) :
    GroundedAssertionTrue (transportGroundedSemiosis M G budget hsep) s c p ↔
      GroundedAssertionTrue M s c (profileToExternal G budget hsep p) :=
  Iff.rfl

theorem evidential_support_preserved
    (M : GroundedSemiosis)
    {System : Type u} {Probe : Type v} {Outcome : Type w}
    (G : OperationalGrounding System M.World Probe Outcome)
    (budget : Nat) (hsep : SeparatesAt G budget)
    (s : M.Sign) (c : M.Context) (p : ProfileWorld G budget) :
    EvidentiallySupported (transportGroundedSemiosis M G budget hsep) s c p ↔
      EvidentiallySupported M s c (profileToExternal G budget hsep p) :=
  Iff.rfl

end Cerp.GroundedSemiosisTransport
