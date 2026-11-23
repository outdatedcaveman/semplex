import HigherSemanticCore
import GraphGaugeClassification

namespace Cerp.GraphGaugeActionGroupoid

open Cerp.HoTTGaugeBridge
open Cerp.GraphGaugeClassification
open Cerp.HigherSemanticCore

universe u v w
variable {V : Type u} {E : Type v} {G : Type w} [GroupLike G]

instance pointwiseGroupLike : GroupLike (V -> G) where
  mul f g := fun v => GroupLike.mul (f v) (g v)
  inv f := fun v => GroupLike.inv (f v)
  one := fun _ => GroupLike.one
  mul_assoc := by
    intro f g h
    funext v
    exact GroupLike.mul_assoc (f v) (g v) (h v)
  one_mul := by
    intro f
    funext v
    exact GroupLike.one_mul (f v)
  mul_one := by
    intro f
    funext v
    exact GroupLike.mul_one (f v)
  inv_mul_cancel := by
    intro f
    funext v
    exact GroupLike.inv_mul_cancel (f v)
  mul_inv_cancel := by
    intro f
    funext v
    exact GroupLike.mul_inv_cancel (f v)
  inv_mul := by
    intro f g
    funext v
    exact GroupLike.inv_mul (f v) (g v)
  inv_inv := by
    intro f
    funext v
    exact GroupLike.inv_inv (f v)

/-- Vertex gauge transformations act on edge connections. -/
def gaugeAction (D : Graph (V := V) (E := E)) :
    Cerp.HigherSemanticCore.GroupAction (V -> G) (Connection (E := E) (G := G)) where
  act := fun g A => Cerp.GraphGaugeClassification.act D A g
  one_act := by
    intro A
    have hone : GroupLike.inv (GroupLike.one : G) = GroupLike.one := by
      calc
        GroupLike.inv (GroupLike.one : G) =
            GroupLike.mul (GroupLike.inv (GroupLike.one : G)) GroupLike.one := by
              rw [GroupLike.mul_one]
        _ = GroupLike.one := GroupLike.inv_mul_cancel GroupLike.one
    funext e
    simp [Cerp.GraphGaugeClassification.act, pointwiseGroupLike, hone,
      GroupLike.one_mul, GroupLike.mul_one]
  mul_act := by
    intro g h A
    funext e
    simp [Cerp.GraphGaugeClassification.act, pointwiseGroupLike,
      GroupLike.mul_assoc, GroupLike.inv_mul]

/-- The gauge action groupoid is the homotopy quotient Conn(D,G) // G^V. -/
abbrev GaugeHomotopyQuotient (D : Graph (V := V) (E := E)) :=
  Cerp.HigherSemanticCore.actionGroupoid (V -> G) (Connection (E := E) (G := G)) (gaugeAction D)

/-- Automorphisms of a connection in the gauge groupoid are exactly the
    gauge transformations fixing that connection. -/
def GaugeStabilizer (D : Graph (V := V) (E := E))
    (A : Connection (E := E) (G := G)) :=
  {g : V -> G // Cerp.GraphGaugeClassification.act D A g = A}

theorem gauge_loop_space_is_stabilizer
    (D : Graph (V := V) (E := E))
    (A : Connection (E := E) (G := G)) :
    (GaugeHomotopyQuotient D).Hom A A = GaugeStabilizer D A := rfl

end Cerp.GraphGaugeActionGroupoid
