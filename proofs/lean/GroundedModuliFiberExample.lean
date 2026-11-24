import GroundedModuliFiber

namespace Cerp.GroundedModuliFiberExample

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.GroundedRelativeDensity
open Cerp.GroundedModuliFiber
open Cerp.SemanticModuliFiber

/-- External category with one object and only its identity. -/
def terminalGroupoid : Groupoid where
  Obj := Unit
  Hom := fun _ _ => Unit
  id := fun _ => ()
  comp := fun _ _ => ()
  inv := fun _ => ()
  id_comp := by intro a b f; cases f; rfl
  comp_id := by intro a b f; cases f; rfl
  assoc := by intro a b c d f g h; cases f; cases g; cases h; rfl
  inv_left := by intro a b f; cases f; rfl
  inv_right := by intro a b f; cases f; rfl

/-- Operational category with two objects and no arrows between them. -/
def discreteBoolCategory : SemCategory where
  Obj := Bool
  Hom := fun x y => PLift (x = y)
  id := fun x => ⟨rfl⟩
  comp := fun f g => ⟨f.down.trans g.down⟩
  id_comp := by intro x y f; cases f; rfl
  comp_id := by intro x y f; cases f; rfl
  assoc := by intro w x y z f g h; cases f; cases g; cases h; rfl

def falseOnlyProbes : ProbeFamily discreteBoolCategory where
  isProbe := fun x => x = false

def identityLikeRealization :
    SemFunctor (asSemCategory terminalGroupoid) discreteBoolCategory where
  obj := fun _ => false
  map := fun _ => ⟨rfl⟩
  map_id := by intro x; rfl
  map_comp := by intro x y z f g; rfl

def realizationFullyFaithful :
    FullyFaithfulRealization (asSemCategory terminalGroupoid)
      discreteBoolCategory identityLikeRealization where
  homEquiv := fun x y =>
    { toFun := fun _ => ⟨rfl⟩
      invFun := fun _ => ()
      left_inv := by intro f; cases f; rfl
      right_inv := by intro f; cases f; rfl }
  toFun_eq_map := by intro x y f; rfl

/-- Every realized object is false, and the false probe is sufficient
    to reconstruct all morphisms between realized objects. -/
def relativeDensityOnImage :
    RelativeProbeDensity (asSemCategory terminalGroupoid)
      discreteBoolCategory identityLikeRealization falseOnlyProbes where
  lift := fun {x y} eta => eta.app false rfl ⟨rfl⟩
  lift_spec := by
    intro x y eta p hp alpha
    cases p with
    | false => cases alpha; rfl
    | true => cases hp
  lift_unique := by
    intro x y eta m hm
    cases m
    rfl

/-- The probe family is not globally dense in the operational category:
    there is a natural transformation from the empty profile of true to
    the nonempty profile of false, but no arrow true → false. -/
def spuriousProfileTrueFalse :
    RestrictedProfileNat discreteBoolCategory falseOnlyProbes true false where
  app := by
    intro p hp alpha
    cases hp
    cases alpha.down
  natural := by
    intro p q hp hq u f
    cases hq
    cases f.down

theorem falseOnlyProbes_not_globally_dense :
    ¬ Nonempty (ProbeDensity discreteBoolCategory falseOnlyProbes) := by
  intro h
  rcases h with ⟨D⟩
  have f : discreteBoolCategory.Hom true false :=
    D.lift (x := true) (y := false) spuriousProfileTrueFalse
  exact Bool.noConfusion f.down

/-- Despite not being globally dense, the single probe is relatively dense
    on the realized image, so the grounded profile groupoid is equivalent
    to the external terminal groupoid and its moduli fiber is contractible. -/
theorem finite_grounded_moduli_contractible :
    FiberContractible
      (groundedProfileEquivalence terminalGroupoid discreteBoolCategory
        identityLikeRealization falseOnlyProbes realizationFullyFaithful
        relativeDensityOnImage) () :=
  grounded_moduli_fiber_contractible terminalGroupoid discreteBoolCategory
    identityLikeRealization falseOnlyProbes realizationFullyFaithful
    relativeDensityOnImage ()

end Cerp.GroundedModuliFiberExample
