import GroundedSemanticCategory

/-!
# Triadic grounded semiosis

A formal extension of the grounded model with an explicit ternary
sign-object-interpretant relation and an interpretant-to-next-sign map.
This is a structural interface inspired by Peircean semeiotic, not a
claim that the whole Peircean theory has been captured.
-/

namespace Cerp.TriadicGroundedSemiosis

open Cerp.GroundedSemanticTransfer
open Cerp.GroundedSemanticCategory
open Cerp.SemanticYoneda.GeneralCategory

universe u v w z

/-- A grounded semantic model enriched with triadic semiosis and continuation. -/
structure TriadicModel where
  base : GroundedModel.{u,v,w}
  Interpretant : Type z
  semiosis : base.Claim -> base.World -> Interpretant -> Prop
  interpretantSign : Interpretant -> base.Claim

/-- A morphism preserves the grounded base, the ternary sign relation,
    and the interpretant-to-sign continuation. -/
structure TriadicHom (M N : TriadicModel.{u,v,w,z}) where
  base : GroundedHom M.base N.base
  interpretantMap : M.Interpretant -> N.Interpretant
  semiosis_iff : forall s o i,
    M.semiosis s o i <->
      N.semiosis (base.claimMap s) (base.worldMap o)
        (interpretantMap i)
  interpretant_sign_commutes : forall i,
    base.claimMap (M.interpretantSign i) =
      N.interpretantSign (interpretantMap i)

namespace TriadicHom

def id (M : TriadicModel.{u,v,w,z}) : TriadicHom M M where
  base := GroundedHom.id M.base
  interpretantMap := fun i => i
  semiosis_iff := by intro s o i; rfl
  interpretant_sign_commutes := by intro i; rfl

def comp {M N K : TriadicModel.{u,v,w,z}}
    (f : TriadicHom M N) (g : TriadicHom N K) : TriadicHom M K where
  base := GroundedHom.comp f.base g.base
  interpretantMap := g.interpretantMap ∘ f.interpretantMap
  semiosis_iff := by
    intro s o i
    exact (f.semiosis_iff s o i).trans
      (g.semiosis_iff (f.base.claimMap s) (f.base.worldMap o)
        (f.interpretantMap i))
  interpretant_sign_commutes := by
    intro i
    change g.base.claimMap (f.base.claimMap (M.interpretantSign i)) =
      K.interpretantSign (g.interpretantMap (f.interpretantMap i))
    rw [f.interpretant_sign_commutes, g.interpretant_sign_commutes]

end TriadicHom

/-- The ordinary category of triadic grounded semantic models. -/
def triadicCategory :
    SemCategory.{max (u + 1) (max (v + 1) (max (w + 1) (z + 1))),
      max u (max v (max w z))} where
  Obj := TriadicModel.{u,v,w,z}
  Hom := TriadicHom
  id := TriadicHom.id
  comp := TriadicHom.comp
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

/-- Truth in the grounded base is invariant under a triadic semantic map. -/
theorem triadic_truth_preserved {M N : triadicCategory.Obj}
    (f : TriadicHom M N) (s : M.base.Claim) :
    GroundedTrue M.base s <->
      GroundedTrue N.base (f.base.claimMap s) :=
  grounded_truth_preserved f.base s

/-- Triadic semiosis itself is preserved and reflected by every morphism. -/
theorem triadic_relation_preserved {M N : triadicCategory.Obj}
    (f : TriadicHom M N) (s : M.base.Claim)
    (o : M.base.World) (i : M.Interpretant) :
    M.semiosis s o i <->
      N.semiosis (f.base.claimMap s) (f.base.worldMap o)
        (f.interpretantMap i) :=
  f.semiosis_iff s o i

/-- An interpretant's continuation into a subsequent sign commutes with
    semantic transport. -/
theorem interpretant_continuation_preserved
    {M N : triadicCategory.Obj} (f : TriadicHom M N)
    (i : M.Interpretant) :
    f.base.claimMap (M.interpretantSign i) =
      N.interpretantSign (f.interpretantMap i) :=
  f.interpretant_sign_commutes i

/-- The all-probes Yoneda representation is fully faithful on this
    explicitly triadic category. This is a representation theorem only:
    it does not prove operational adequacy or irreducibility of semiosis. -/
def triadic_all_probe_reconstruction (M N : triadicCategory.Obj) :
    Cerp.HigherSemanticCore.HomBijection
      (triadicCategory.Hom M N)
      (ProfileNat triadicCategory M N) :=
  homEquiv triadicCategory M N

end Cerp.TriadicGroundedSemiosis
