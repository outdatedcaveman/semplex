import GroundedSemiosisCategory

/-!
# Triadic semiosis over relationally grounded, contextual semantics

This is the richer triadic category: reference remains relational, claims
are expressed in contexts, satisfaction and evidence remain separate, and
a ternary sign-object-interpretant relation is added.
-/

namespace Cerp.TriadicRelationalSemiosis

open Cerp.SemanticFibrations
open Cerp.GroundedSemiosisCategory
open Cerp.SemanticYoneda.GeneralCategory

universe u v w x z

structure TriadicGroundedModel where
  base : GroundedSemiosis.{u,v,w,x}
  Interpretant : Type z
  semiosis : base.Sign -> base.World -> Interpretant -> Prop
  interpretantSign : Interpretant -> base.Sign

structure TriadicGroundedHom
    (M N : TriadicGroundedModel.{u,v,w,x,z}) where
  base : GroundedSemiosisHom M.base N.base
  interpretantMap : M.Interpretant -> N.Interpretant
  semiosis_iff : forall s world i,
    M.semiosis s world i <->
      N.semiosis (base.signMap s) (base.worldMap world)
        (interpretantMap i)
  interpretant_sign_commutes : forall i,
    base.signMap (M.interpretantSign i) =
      N.interpretantSign (interpretantMap i)

namespace TriadicGroundedHom

def id (M : TriadicGroundedModel.{u,v,w,x,z}) :
    TriadicGroundedHom M M where
  base := GroundedSemiosisHom.id M.base
  interpretantMap := fun i => i
  semiosis_iff := by intro s w i; rfl
  interpretant_sign_commutes := by intro i; rfl

def comp {M N K : TriadicGroundedModel.{u,v,w,x,z}}
    (f : TriadicGroundedHom M N)
    (g : TriadicGroundedHom N K) : TriadicGroundedHom M K where
  base := GroundedSemiosisHom.comp f.base g.base
  interpretantMap := g.interpretantMap ∘ f.interpretantMap
  semiosis_iff := by
    intro s w i
    exact (f.semiosis_iff s w i).trans
      (g.semiosis_iff (f.base.signMap s) (f.base.worldMap w)
        (f.interpretantMap i))
  interpretant_sign_commutes := by
    intro i
    change g.base.signMap (f.base.signMap (M.interpretantSign i)) =
      K.interpretantSign (g.interpretantMap (f.interpretantMap i))
    rw [f.interpretant_sign_commutes, g.interpretant_sign_commutes]

end TriadicGroundedHom

def triadicRelationalCategory :
    SemCategory.{max (u + 1) (max (v + 1)
      (max (w + 1) (max (x + 1) (z + 1)))),
      max u (max v (max w (max x z)))} where
  Obj := TriadicGroundedModel.{u,v,w,x,z}
  Hom := TriadicGroundedHom
  id := TriadicGroundedHom.id
  comp := TriadicGroundedHom.comp
  id_comp := by
    intro M N f
    cases f
    rfl
  comp_id := by
    intro M N f
    cases f
    rfl
  assoc := by
    intro A B C D f g h
    cases f
    cases g
    cases h
    rfl

theorem grounded_assertion_truth_preserved
    {M N : triadicRelationalCategory.Obj}
    (f : TriadicGroundedHom M N) (s : M.base.Sign)
    (c : M.base.Context) (world : M.base.World) :
    GroundedAssertionTrue M.base s c world <->
      GroundedAssertionTrue N.base (f.base.signMap s)
        (f.base.contextMap c) (f.base.worldMap world) :=
  assertion_truth_iff f.base s c world

theorem triadic_relation_preserved
    {M N : triadicRelationalCategory.Obj}
    (f : TriadicGroundedHom M N) (s : M.base.Sign)
    (world : M.base.World) (i : M.Interpretant) :
    M.semiosis s world i <->
      N.semiosis (f.base.signMap s) (f.base.worldMap world)
        (f.interpretantMap i) :=
  f.semiosis_iff s world i

theorem interpretant_becomes_sign_coherently
    {M N : triadicRelationalCategory.Obj}
    (f : TriadicGroundedHom M N) (i : M.Interpretant) :
    f.base.signMap (M.interpretantSign i) =
      N.interpretantSign (f.interpretantMap i) :=
  f.interpretant_sign_commutes i

theorem evidence_remains_sound
    {M N : triadicRelationalCategory.Obj}
    (f : TriadicGroundedHom M N) (s : M.base.Sign)
    (c : M.base.Context) (world : M.base.World)
    (href : M.base.refers s world)
    (ev : M.base.Evidence s c world) :
    N.base.satisfies
      (N.base.expresses (f.base.signMap s) (f.base.contextMap c))
      (f.base.worldMap world) :=
  evidence_transport_sound f.base s c world href ev

/-- Yoneda reconstruction now applies to the richer contextual, relational,
    evidential and triadic semantic structures as whole objects. -/
def all_probe_reconstruction
    (M N : triadicRelationalCategory.Obj) :
    Cerp.HigherSemanticCore.HomBijection
      (triadicRelationalCategory.Hom M N)
      (ProfileNat triadicRelationalCategory M N) :=
  homEquiv triadicRelationalCategory M N

end Cerp.TriadicRelationalSemiosis
