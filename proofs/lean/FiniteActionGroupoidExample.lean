import HigherSemanticCore

namespace Cerp.FiniteActionGroupoidExample

open Cerp.HoTTGaugeBridge
open Cerp.HigherSemanticCore

universe u

private theorem bxor_comm_local (a b : Bool) : bxor a b = bxor b a := by
  cases a <;> cases b <;> rfl

instance boolXorGroupLike : GroupLike Bool where
  mul := bxor
  inv := fun b => b
  one := false
  mul_assoc := bxor_assoc
  one_mul := bxor_false_left
  mul_one := bxor_false_right
  inv_mul_cancel := bxor_self
  mul_inv_cancel := bxor_self
  inv_mul := by intro a b; exact bxor_comm_local a b
  inv_inv := by intro a; rfl

/-- C2 acts trivially on none and freely on the two-element orbit some false/some true. -/
def boolOptionAction : GroupAction Bool (Option Bool) where
  act := fun g x =>
    match x with
    | none => none
    | some b => some (bxor g b)
  one_act := by
    intro x
    cases x <;> rfl
  mul_act := by
    intro g h x
    cases x with
    | none => rfl
    | some b => exact congrArg some (bxor_assoc g h b)

abbrev Q := actionGroupoid Bool (Option Bool) boolOptionAction

def fixedNoneFalse : Q.Hom none none := ⟨false, rfl⟩
def fixedNoneTrue : Q.Hom none none := ⟨true, rfl⟩

theorem fixed_object_has_two_distinct_loops : fixedNoneFalse ≠ fixedNoneTrue := by
  intro h
  have hval : false = true := congrArg Subtype.val h
  cases hval

theorem moving_object_stabilizer_is_trivial
    (g : Stabilizer boolOptionAction (some false)) : g.1 = false := by
  have h := g.2
  change some (bxor g.1 false) = some false at h
  cases hval : g.1 with
  | false => rfl
  | true =>
      rw [hval] at h
      simp [bxor] at h

theorem two_moving_states_are_in_same_orbit :
    OrbitRelated boolOptionAction (some false) (some true) := by
  exact ⟨true, rfl⟩

theorem fixed_and_moving_states_are_not_in_same_orbit :
    Not (OrbitRelated boolOptionAction none (some false)) := by
  intro h
  rcases h with ⟨g, hg⟩
  cases g <;> simp [boolOptionAction] at hg

end Cerp.FiniteActionGroupoidExample
