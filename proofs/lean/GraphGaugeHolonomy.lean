import HoTTGaugeBridge

/-!
Graph-generic gauge covariance of path transport.
This is valid for arbitrary vertex types and adjacency relations. The
connection stores labels on ordered vertex pairs; adjacency selects walks.
This proves path covariance, not yet the spanning-tree classification.
-/

namespace Cerp.GraphGaugeHolonomy

universe u v

variable {V : Type u} {G : Type v} {adj : V -> V -> Prop}
variable [Cerp.HoTTGaugeBridge.GroupLike G]

open Cerp.HoTTGaugeBridge

inductive Walk (adj : V -> V -> Prop) : V -> V -> Type u
  | nil (x : V) : Walk adj x x
  | cons {x y z : V} (step : adj x y) (tail : Walk adj y z) :
      Walk adj x z

structure Connection (V : Type u) (G : Type v) where
  edge : V -> V -> G

abbrev VertexGauge (V : Type u) (G : Type v) := V -> G

def gaugeTransform (A : Connection V G) (g : VertexGauge V G) :
    Connection V G where
  edge x y :=
    GroupLike.mul (GroupLike.mul (g y) (A.edge x y)) (GroupLike.inv (g x))

def transport (A : Connection V G) : {x y : V} -> Walk adj x y -> G
  | _, _, Walk.nil _ => GroupLike.one
  | _, _, Walk.cons (x := x) (y := y) _ tail =>
      GroupLike.mul (transport A tail) (A.edge x y)

theorem transport_gauge_covariant
    (A : Connection V G) (g : VertexGauge V G) :
    forall {x y : V} (p : Walk adj x y),
      transport (gaugeTransform A g) p =
        GroupLike.mul (GroupLike.mul (g y) (transport A p))
          (GroupLike.inv (g x)) := by
  intro x y p
  induction p with
  | nil z =>
      simp [transport, GroupLike.one_mul, GroupLike.mul_one,
        GroupLike.mul_inv_cancel]
  | @cons x y z step tail ih =>
      change GroupLike.mul (transport (gaugeTransform A g) tail)
          (GroupLike.mul
            (GroupLike.mul (g y) (A.edge x y)) (GroupLike.inv (g x))) =
        GroupLike.mul (GroupLike.mul (g z)
          (GroupLike.mul (transport A tail) (A.edge x y)))
          (GroupLike.inv (g x))
      rw [ih]
      simp only [GroupLike.mul_assoc]
      rw [inv_mul_left_cancel]

theorem loop_holonomy_gauge_covariant
    (A : Connection V G) (g : VertexGauge V G)
    (x : V) (p : Walk adj x x) :
    transport (gaugeTransform A g) p =
      GroupLike.mul (GroupLike.mul (g x) (transport A p))
        (GroupLike.inv (g x)) :=
  transport_gauge_covariant A g p

theorem loop_holonomy_same_conjugacy_class
    (A : Connection V G) (g : VertexGauge V G)
    (x : V) (p : Walk adj x x) :
    SameConjugacyClass (transport A p)
      (transport (gaugeTransform A g) p) :=
  Exists.intro (g x) (loop_holonomy_gauge_covariant A g x p)

/-- A stabilizing gauge centralizes every based loop holonomy. -/
theorem stabilizer_centralizes_loop_holonomy
    (A : Connection V G) (g : VertexGauge V G)
    (hfix : gaugeTransform A g = A)
    (x : V) (p : Walk adj x x) :
    GroupLike.mul (g x) (transport A p) =
      GroupLike.mul (transport A p) (g x) := by
  have hcov := loop_holonomy_gauge_covariant A g x p
  rw [hfix] at hcov
  have hmul := congrArg (fun t => GroupLike.mul t (g x)) hcov
  have hcancel :
      GroupLike.mul
        (GroupLike.mul
          (GroupLike.mul (g x) (transport A p)) (GroupLike.inv (g x)))
        (g x) = GroupLike.mul (g x) (transport A p) := by
    simp [GroupLike.mul_assoc, GroupLike.inv_mul_cancel, GroupLike.mul_one]
  calc
    GroupLike.mul (g x) (transport A p) =
        GroupLike.mul
          (GroupLike.mul
            (GroupLike.mul (g x) (transport A p)) (GroupLike.inv (g x)))
          (g x) := hcancel.symm
    _ = GroupLike.mul (transport A p) (g x) := hmul.symm
end Cerp.GraphGaugeHolonomy



