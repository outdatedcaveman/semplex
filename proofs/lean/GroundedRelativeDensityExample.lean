import GroundedRelativeDensity

/-!
Finite witness for the relative-density hypothesis:
the all-probes family is dense, while the empty family cannot be dense
even on the image of the identity realization of the discrete Bool category.
-/

namespace Cerp.GroundedRelativeDensityExample

open Cerp.HigherSemanticCore
open Cerp.SemanticYoneda.GeneralCategory
open Cerp.GroundedRelativeDensity

def identityRealization :
    SemFunctor discreteBoolCategory discreteBoolCategory where
  obj := id
  map := fun f => f
  map_id := by intro x; rfl
  map_comp := by intro x y z f g; rfl

def allProbeRelativeDensity :
    RelativeProbeDensity discreteBoolCategory discreteBoolCategory
      identityRealization (allProbes discreteBoolCategory) where
  lift := fun {x y} eta => (allProbesDense discreteBoolCategory).lift eta
  lift_spec := by
    intro x y eta p hp alpha
    exact (allProbesDense discreteBoolCategory).lift_spec eta p hp alpha
  lift_unique := by
    intro x y eta m hm
    exact (allProbesDense discreteBoolCategory).lift_unique eta m hm

/-- The empty probe family admits a natural profile transformation from
    false to true, despite there being no corresponding category morphism.
    Therefore it cannot satisfy the relative colimit universal property. -/
theorem empty_probes_not_relatively_dense :
    ¬ Nonempty (RelativeProbeDensity discreteBoolCategory discreteBoolCategory
      identityRealization emptyProbeFamily) := by
  intro h
  rcases h with ⟨D⟩
  have f : discreteBoolCategory.Hom false true :=
    D.lift (x := false) (y := true) emptyProbeProfileNat
  exact Bool.noConfusion f.down

end Cerp.GroundedRelativeDensityExample
