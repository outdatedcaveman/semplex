import HigherSemanticCore

namespace Cerp.ConjugationSemanticGroupoid

open Cerp.HoTTGaugeBridge
open Cerp.HigherSemanticCore

universe u
variable {G : Type u} [GroupLike G]

theorem inv_one : GroupLike.inv (GroupLike.one : G) = GroupLike.one := by
  calc
    GroupLike.inv (GroupLike.one : G) =
        GroupLike.mul GroupLike.one (GroupLike.inv GroupLike.one) :=
          (GroupLike.one_mul _).symm
    _ = GroupLike.one := GroupLike.mul_inv_cancel _

/-- Conjugation is the canonical action of a group on itself. -/
def conjugate (g x : G) : G :=
  GroupLike.mul (GroupLike.mul g x) (GroupLike.inv g)

theorem conjugate_one (x : G) : conjugate GroupLike.one x = x := by
  simp [conjugate, inv_one, GroupLike.one_mul, GroupLike.mul_one]

theorem conjugate_mul (g h x : G) :
    conjugate (GroupLike.mul g h) x =
      conjugate g (conjugate h x) := by
  simp [conjugate, GroupLike.mul_assoc, GroupLike.inv_mul]

def conjugationAction : GroupAction G G where
  act := conjugate
  one_act := conjugate_one
  mul_act := conjugate_mul

/-- The isotropy condition under conjugation is exactly commutation:
    the stabilizer of x is the centralizer C_G(x). -/
theorem conjugation_stabilizer_iff_commutes (g x : G) :
    conjugate g x = x ↔
      GroupLike.mul g x = GroupLike.mul x g := by
  constructor
  · intro h
    have h' := congrArg (fun z => GroupLike.mul z g) h
    dsimp [conjugate] at h'
    calc
      GroupLike.mul g x =
          GroupLike.mul (GroupLike.mul (GroupLike.mul g x) (GroupLike.inv g)) g := by
            simp [GroupLike.mul_assoc, GroupLike.inv_mul_cancel, GroupLike.mul_one]
      _ = GroupLike.mul x g := by
            simpa [GroupLike.mul_assoc, GroupLike.inv_mul_cancel,
              GroupLike.mul_one] using h'
  · intro h
    calc
      conjugate g x =
          GroupLike.mul (GroupLike.mul x g) (GroupLike.inv g) := by
            simp [conjugate, h]
      _ = x := by
        simp [GroupLike.mul_assoc, GroupLike.mul_inv_cancel, GroupLike.mul_one]

/-- Conjugation arrows are precisely conjugating witnesses. -/
def ConjugationArrow (x y : G) :=
  {g : G // conjugate g x = y}

theorem conjugacy_iff_arrow_nonempty (x y : G) :
    (∃ g : G, conjugate g x = y) ↔ Nonempty (ConjugationArrow x y) := by
  constructor
  · rintro ⟨g, h⟩
    exact ⟨⟨g, h⟩⟩
  · rintro ⟨⟨g, h⟩⟩
    exact ⟨g, h⟩

/-- The loop witnesses at x are exactly its centralizer elements. -/
theorem loop_witness_iff_centralizer (x g : G) :
    (conjugate g x = x) ↔
      GroupLike.mul g x = GroupLike.mul x g := by
  exact conjugation_stabilizer_iff_commutes g x

/-- Equality of the two centralizer predicates, extensionally. -/
theorem stabilizer_predicate_eq_centralizer (x : G) :
    (fun g => conjugate g x = x) =
      (fun g => GroupLike.mul g x = GroupLike.mul x g) := by
  funext g
  exact propext (conjugation_stabilizer_iff_commutes g x)

end Cerp.ConjugationSemanticGroupoid
